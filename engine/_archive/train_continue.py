"""
Script d'entrainement continu + calibration + extension vocabulaire
====================================================================
Charge le checkpoint step 10, etend le tokenizer, continue l'entrainement
sur le corpus local, et calibre le PhiInverseDecoder.

Usage:
    python train_continue.py --steps 500 --batch_size 2 --seq_len 128

Etapes:
  1. Charger le checkpoint HarmonicForCausalLM (59M params, step 10)
  2. Entrainer le tokenizer BPE sur le corpus local → 50304 tokens
  3. Continuer l'entrainement sur corpus_all.txt (~20k lignes)
  4. Calibrer le ConditionEncoder (11D→512D) sur paires (signature, texte)
  5. Sauvegarder checkpoints + tokenizer + encoder
"""

import os
import sys
import math
import time
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW

# Chemins
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_HARMONIC_TRAINING = _PROJECT_ROOT / "harmonic_training"
_CORPUS_DIR = _PROJECT_ROOT / "data" / "corpus"
_OUTPUT_DIR = _PROJECT_ROOT / "data" / "training_output"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_HARMONIC_TRAINING))

from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
from model.tokenizer import HarmonicTokenizer
from engine.harmonic_engine import HarmonicResonanceEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-5s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==============================================================================
# 1. TOKENIZER ETENDU
# ==============================================================================

def build_extended_tokenizer(corpus_paths: List[Path], vocab_size: int = 50304) -> HarmonicTokenizer:
    """Construit un tokenizer avec vocabulaire etendu."""
    logger.info(f"Building tokenizer ({vocab_size} target)...")

    tokenizer = HarmonicTokenizer(vocab_size=vocab_size)
    base_size = tokenizer.get_vocab_size()

    # Collecter les mots frequents du corpus
    from collections import Counter
    import re

    all_texts = []
    for path in corpus_paths:
        if path.exists() and path.stat().st_size > 100:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                texts = [line.strip() for line in f if len(line.strip()) > 20]
                all_texts.extend(texts)

    logger.info(f"  Corpus: {len(all_texts)} texts")

    # Extraire les mots frequents
    word_counter = Counter()
    for text in all_texts[:5000]:
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{2,}\b', text.lower())
        word_counter.update(words)

    # Ajouter les tops mots au tokenizer
    existing = set(tokenizer.token_to_id.keys())
    new_count = 0
    for word, _ in word_counter.most_common(8000):
        if word not in existing and len(word) >= 2:
            new_id = len(tokenizer.id_to_token)
            tokenizer.token_to_id[word] = new_id
            tokenizer.id_to_token[new_id] = word
            new_count += 1

    logger.info(f"  Tokenizer: {tokenizer.get_vocab_size()} tokens "
                f"({new_count} new words from corpus, base={base_size})")

    # Sauvegarder
    try:
        tokenizer.save(str(_OUTPUT_DIR / "tokenizer_extended.json"))
    except Exception:
        import json
        data = {
            'token_to_id': tokenizer.token_to_id,
            'id_to_token': {str(k): v for k, v in tokenizer.id_to_token.items()},
        }
        with open(str(_OUTPUT_DIR / "tokenizer_extended.json"), 'w') as f:
            json.dump(data, f, ensure_ascii=False)

    return tokenizer


# ==============================================================================
# 2. DATASET LOCAL
# ==============================================================================

class LocalCorpusDataset(torch.utils.data.IterableDataset):
    """Dataset iterable a partir du corpus local."""

    def __init__(self, texts: List[str], tokenizer: HarmonicTokenizer,
                 seq_len: int = 128):
        self.texts = texts
        self.tokenizer = tokenizer
        self.seq_len = seq_len

    def __iter__(self):
        for text in self.texts:
            if len(text) < 10:
                continue
            tokens = self.tokenizer.encode(text)
            if len(tokens) < 5:
                continue
            # Créer des chunks de seq_len+1 (pour le shift labels)
            for i in range(0, max(1, len(tokens) - self.seq_len), self.seq_len // 2):
                chunk = tokens[i:i + self.seq_len + 1]
                if len(chunk) < 5:
                    continue
                # Pad si nécessaire
                if len(chunk) < self.seq_len + 1:
                    chunk = chunk + [0] * (self.seq_len + 1 - len(chunk))
                input_ids = torch.tensor(chunk[:-1], dtype=torch.long)
                labels = torch.tensor(chunk[1:], dtype=torch.long)
                yield input_ids, labels

    def __len__(self):
        return len(self.texts) * 2  # estimation


def load_corpus(corpus_dir: Path) -> List[str]:
    """Charge tous les fichiers texte du corpus."""
    all_texts = []
    corpus_files = sorted(corpus_dir.glob("*.txt"))
    for path in corpus_files:
        if path.stat().st_size < 100:
            continue
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            texts = [line.strip() for line in f if len(line.strip()) > 15]
            all_texts.extend(texts)
    logger.info(f"Corpus loaded: {len(all_texts)} texts from {len(corpus_files)} files")
    return all_texts


# ==============================================================================
# 3. BOUCLE D'ENTRAINEMENT
# ==============================================================================

def train_continue(
    model: nn.Module,
    train_texts: List[str],
    tokenizer: HarmonicTokenizer,
    checkpoint_path: Path,
    output_dir: Path,
    num_steps: int = 500,
    batch_size: int = 2,
    seq_len: int = 128,
    lr: float = 3e-4,
    grad_accum_steps: int = 4,
    save_every: int = 100,
    max_time_minutes: int = 0,
    use_amp: bool = False,
):
    """Continue l'entrainement du modele."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.train()

    # Dataset + DataLoader
    dataset = LocalCorpusDataset(train_texts, tokenizer, seq_len)
    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=False, num_workers=0
    )

    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_steps)

    # Charger l'état de l'optimizer si présent dans le checkpoint
    ckpt = torch.load(str(checkpoint_path), map_location='cpu', weights_only=False)
    if 'optimizer_state_dict' in ckpt:
        try:
            optimizer.load_state_dict(ckpt['optimizer_state_dict'])
            logger.info("Optimizer state restored")
        except Exception:
            logger.info("Optimizer state not restored (fresh start)")

    scaler = torch.amp.GradScaler() if use_amp else None

    logger.info(f"Training on {device} | {num_steps} steps | batch={batch_size} | "
                f"seq_len={seq_len} | grad_accum={grad_accum_steps}")
    logger.info(f"Corpus: {len(train_texts)} texts | Model: {sum(p.numel() for p in model.parameters()):,} params")

    best_loss = float('inf')
    global_step = 0
    total_loss = 0.0
    tokens_seen = 0
    t0 = time.time()

    optimizer.zero_grad()

    for epoch in range(10):  # max 10 epochs sur le corpus
        for batch_idx, (input_ids, labels) in enumerate(dataloader):
            if global_step >= num_steps:
                logger.info(f"Reached target steps ({num_steps})")
                break

            # Time-based stopping
            if max_time_minutes > 0 and (time.time() - t0) > max_time_minutes * 60:
                logger.info(f"Reached time limit ({max_time_minutes} min)")
                break

            input_ids = input_ids.to(device)
            labels = labels.to(device)

            # Forward
            if use_amp and device.type == 'cuda':
                with torch.amp.autocast('cuda'):
                    logits, loss, _ = model(input_ids, labels=labels)
            else:
                logits, loss, _ = model(input_ids, labels=labels)

            if loss is None:
                continue

            loss = loss / grad_accum_steps

            # Backward
            if use_amp and scaler is not None:
                scaler.scale(loss).backward()
            else:
                loss.backward()

            tokens_seen += input_ids.numel()

            if (batch_idx + 1) % grad_accum_steps == 0:
                if use_amp and scaler is not None:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()

                optimizer.zero_grad()
                scheduler.step()
                global_step += 1

                total_loss += loss.item() * grad_accum_steps

                # Logging
                if global_step % 20 == 0:
                    avg_loss = total_loss / max(global_step, 1)
                    elapsed = time.time() - t0
                    tk_s = tokens_seen / max(elapsed, 1)
                    logger.info(
                        f"  Step {global_step}/{num_steps} | "
                        f"loss={loss.item()*grad_accum_steps:.4f} | "
                        f"avg_loss={avg_loss:.4f} | "
                        f"lr={scheduler.get_last_lr()[0]:.2e} | "
                        f"{tk_s:.0f} tok/s"
                    )

                # Sauvegarde
                if global_step % save_every == 0:
                    ckpt_path = output_dir / f"checkpoint_step_{global_step}.pt"
                    torch.save({
                        'model_state_dict': {k.replace('model.', ''): v
                                           for k, v in model.state_dict().items()},
                        'optimizer_state_dict': optimizer.state_dict(),
                        'scheduler_state_dict': scheduler.state_dict(),
                        'global_step': global_step,
                        'best_loss': best_loss,
                        'avg_loss': total_loss / global_step,
                        'config': model.config if hasattr(model, 'config') else {},
                    }, str(ckpt_path))
                    logger.info(f"  Checkpoint saved: {ckpt_path.name}")

                if loss.item() * grad_accum_steps < best_loss:
                    best_loss = loss.item() * grad_accum_steps

        if global_step >= num_steps:
            break

    elapsed = time.time() - t0
    final_loss = total_loss / max(global_step, 1)
    logger.info(f"Training complete: {global_step} steps in {elapsed:.0f}s")
    logger.info(f"  Final avg_loss={final_loss:.4f}, best_loss={best_loss:.4f}")

    # Sauvegarde finale
    final_ckpt = output_dir / "checkpoint_final.pt"
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'global_step': global_step,
        'best_loss': best_loss,
        'avg_loss': final_loss,
        'total_time': elapsed,
        'config': model.config if hasattr(model, 'config') else {},
    }, str(final_ckpt))
    logger.info(f"Final checkpoint: {final_ckpt}")

    return final_loss


# ==============================================================================
# 4. CALIBRATION DU CONDITION ENCODER
# ==============================================================================

def calibrate_condition_encoder(
    texts: List[str],
    engine: HarmonicResonanceEngine,
    encoder,  # ConditionEncoder
    n_samples: int = 200,
    n_steps_per_sample: int = 10,
    lr: float = 0.005,
) -> float:
    """
    Calibre le ConditionEncoder sur des paires (signature 9D, embedding du texte).

    Pour chaque texte echantillonne :
      1. engine.analyze(texte) → signature 9D
      2. Modele entraine → embedding du texte
      3. ConditionEncoder.train_step(sig_9d → embedding) → MSE loss
    """
    logger.info(f"Calibrating ConditionEncoder on {n_samples} samples...")

    np.random.seed(42)
    indices = np.random.choice(len(texts), min(n_samples, len(texts)), replace=False)
    total_loss = 0.0

    for i, idx in enumerate(indices):
        text = texts[idx]
        if len(text) < 20:
            continue

        # Signature 9D du moteur
        try:
            sig = engine.analyze(text)
            sig_dict = sig.to_dict()
            sig_9d = np.array([
                sig_dict.get("phi", 0.5), sig_dict.get("alpha", 0.5),
                sig_dict.get("reasoning", 0.5), sig_dict.get("creativity", 0.5),
                sig_dict.get("math", 0.5), sig_dict.get("factual", 0.5),
                sig_dict.get("code", 0.5), sig_dict.get("emotion", 0.5),
                sig_dict.get("temporal", 0.5),
            ], dtype=np.float32)
        except Exception:
            sig_9d = np.full(9, 0.5, dtype=np.float32)

        # Étendre à 11D
        sig_11d = np.pad(sig_9d, (0, 2), mode='constant', constant_values=0.5)

        # Embedding cible : embedding de caractères simple
        # (en production, utiliserait le modèle entraîné pour obtenir l'embedding)
        char_embed = np.zeros(512, dtype=np.float32)
        for j, ch in enumerate(text[:512]):
            char_embed[j % 512] += (ord(ch) % 100) / 100.0
        char_embed = char_embed / (np.linalg.norm(char_embed) + 1e-8)

        for _ in range(n_steps_per_sample):
            loss = encoder.train_step(
                sig_11d.reshape(1, 11),
                char_embed.reshape(1, 512),
                lr=lr,
            )
        total_loss += loss

        if (i + 1) % 50 == 0:
            logger.info(f"  Calibration: {i+1}/{n_samples} samples, loss={loss:.6f}")

    avg_loss = total_loss / max(n_samples, 1)
    logger.info(f"Calibration complete: avg_loss={avg_loss:.6f}")

    # Sauvegarder
    encoder_path = str(_OUTPUT_DIR / "condition_encoder_calibrated.npz")
    encoder.save(encoder_path)
    logger.info(f"Encoder saved: {encoder_path}")

    return avg_loss


# ==============================================================================
# 5. MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Harmonic Training Continuation")
    parser.add_argument('--steps', type=int, default=500, help='Training steps')
    parser.add_argument('--batch_size', type=int, default=2)
    parser.add_argument('--seq_len', type=int, default=128)
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--save_every', type=int, default=100)
    parser.add_argument('--max_time', type=int, default=0,
                       help='Max training time in minutes (0=unlimited)')
    parser.add_argument('--skip_training', action='store_true')
    parser.add_argument('--skip_calibration', action='store_true')
    parser.add_argument('--model_type', default='harmonic-tiny',
                       choices=['harmonic-tiny', 'harmonic-small'])
    args = parser.parse_args()

    print("=" * 60)
    print("HARMONIC TRAINING — Continuation + Calibration + Vocab Extend")
    print("=" * 60)
    print()

    # --- 1. Charger le checkpoint le plus recent ---
    # Priorite: data/training_output/checkpoint_final.pt > harmonic_training/checkpoints_test/
    ckpt_candidates = [
        _OUTPUT_DIR / "checkpoint_final.pt",
        _HARMONIC_TRAINING / "checkpoints_test" / "checkpoint_final.pt",
    ]
    ckpt_path = None
    for c in ckpt_candidates:
        if c.exists():
            ckpt_path = c
            break

    if ckpt_path is None:
        logger.error("No checkpoint found")
        sys.exit(1)

    logger.info(f"Loading checkpoint: {ckpt_path}")
    ckpt = torch.load(str(ckpt_path), map_location='cpu', weights_only=False)
    config_data = ckpt.get('config', {})
    logger.info(f"  Checkpoint config: hidden={config_data.get('hidden_size')}, "
                f"layers={config_data.get('num_layers')}, "
                f"max_len={config_data.get('max_len')}")

    # --- 2. Construire le tokenizer étendu ---
    corpus_paths = sorted(_CORPUS_DIR.glob("*.txt"))
    tokenizer = build_extended_tokenizer(corpus_paths, vocab_size=50304)

    # --- 3. Charger le modèle ---
    model_config = dict(HARMONIC_CONFIGS.get(args.model_type, HARMONIC_CONFIGS['harmonic-tiny']))
    model_config['vocab_size'] = 50304
    model_config['max_len'] = args.seq_len

    logger.info(f"Creating model ({args.model_type}): {model_config['hidden_size']} hidden, "
                f"{model_config['num_layers']} layers, {model_config['num_heads']} heads")

    model = HarmonicForCausalLM(model_config)

    # Charger les poids
    state = ckpt['model_state_dict']
    state = {k.replace('model.', ''): v for k, v in state.items()}
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing:
        logger.info(f"  Missing keys: {len(missing)} (token_embedding, lm_head resize for new max_len)")
    logger.info(f"  Model loaded: {sum(p.numel() for p in model.parameters()):,} params")

    # --- 4. Continuer l'entraînement ---
    if not args.skip_training:
        logger.info("=" * 40)
        logger.info("PHASE 1: Training continuation")
        logger.info("=" * 40)

        train_texts = load_corpus(_CORPUS_DIR)
        if len(train_texts) < 10:
            logger.error("Not enough training texts")
            sys.exit(1)

        final_loss = train_continue(
            model=model,
            train_texts=train_texts,
            tokenizer=tokenizer,
            checkpoint_path=ckpt_path,
            output_dir=_OUTPUT_DIR,
            num_steps=args.steps,
            batch_size=args.batch_size,
            seq_len=args.seq_len,
            lr=args.lr,
            save_every=args.save_every,
            max_time_minutes=args.max_time,
        )

        logger.info(f"Training done! Final loss: {final_loss:.4f}")
    else:
        logger.info("Training skipped (--skip_training)")

    # --- 5. Calibrer le ConditionEncoder ---
    if not args.skip_calibration:
        logger.info("=" * 40)
        logger.info("PHASE 2: ConditionEncoder calibration")
        logger.info("=" * 40)

        try:
            from engine.phi_diffusion_engine import ConditionEncoder
        except ImportError:
            logger.error("ConditionEncoder not available, skipping calibration")
        else:
            engine = HarmonicResonanceEngine(use_hologram='light')
            encoder = ConditionEncoder()
            train_texts = load_corpus(_CORPUS_DIR)

            cal_loss = calibrate_condition_encoder(
                texts=train_texts,
                engine=engine,
                encoder=encoder,
                n_samples=min(200, len(train_texts)),
            )
            logger.info(f"Calibration done! Final loss: {cal_loss:.6f}")

    # --- Résumé ---
    print()
    print("=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Output: {_OUTPUT_DIR}")
    print(f"  Tokenizer: {_OUTPUT_DIR / 'tokenizer_extended.json'}")
    print(f"  Model checkpoint: {_OUTPUT_DIR / 'checkpoint_final.pt'}")
    print(f"  Encoder: {_OUTPUT_DIR / 'condition_encoder_calibrated.npz'}")
    print()
    print("To use the trained model:")
    print("  from engine.harmonic_decoder_bridge import HarmonicDecoderBridge")
    print("  bridge = HarmonicDecoderBridge(model_type='trained')")
    print("  # bridge uses the checkpoint in data/training_output/")
    print("=" * 60)


if __name__ == '__main__':
    main()
