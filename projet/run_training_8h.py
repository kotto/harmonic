"""
Entraînement longue durée (8h) du modèle harmonic-tiny
=======================================================
Optimisé pour CPU AMD Ryzen 5 3500U, 6GB RAM.
Checkpoints espacés, reprise possible, logging léger.

Usage:
    python run_training_8h.py                    # lance l'entraînement 8h
    python run_training_8h.py --resume           # reprend depuis dernier checkpoint
    python run_training_8h.py --dry-run          # estime le temps sans entraîner
"""

import os
import sys
import math
import time
import json
import argparse
import logging
import urllib.request
import traceback
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW

# Ajouter harmonic_training au path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'harmonic_training'))

from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration par défaut pour 8h
# ============================================================================
DEFAULT_CONFIG = {
    'steps': 4000,
    'seq_len': 128,
    'batch_size': 4,
    'grad_acc': 1,
    'lr': 3e-4,
    'weight_decay': 0.01,
    'samples': 1000,
    'warmup_steps': 50,
    'save_every': 250,
    'log_every': 20,
    'max_time_hours': 8.0,
    'output': './training_output_8h',
}

TINY_SHAKESPEARE_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"


# ============================================================================
# Dataset TinyShakespeare
# ============================================================================
class TinyShakespeareDataset(Dataset):
    """Dataset TinyShakespeare avec vocabulaire enrichi."""

    def __init__(self, seq_len=128, max_samples=1000, min_freq=2):
        self.seq_len = seq_len
        self.data = self._load_text()
        self.vocab, self.ids = self._build_vocab(min_freq)
        self.samples = self._create_samples(max_samples)
        logger.info(f"Dataset: {len(self.samples)} sequences, "
                    f"vocab={len(self.vocab)}, seq_len={seq_len}")

    def _load_text(self):
        """Charge TinyShakespeare depuis GitHub ou utilise un fallback."""
        try:
            logger.info("Téléchargement de TinyShakespeare...")
            with urllib.request.urlopen(TINY_SHAKESPEARE_URL, timeout=10) as f:
                text = f.read().decode('utf-8')
            logger.info(f"  {len(text)} caractères chargés")
            return text
        except Exception as e:
            logger.warning(f"  Échec du téléchargement: {e}")
            logger.info("  Utilisation d'un texte de fallback...")
            return self._generate_fallback_text()

    def _generate_fallback_text(self):
        """Génère un texte d'entraînement réaliste en cas d'absence de réseau."""
        texts = []
        for _ in range(80):
            a, b = torch.randint(1, 1000, (2,)).tolist()
            texts.append(f"Calculate {a} plus {b} equals {a+b}.")
            texts.append(f"What is {a} times {b}? The product is {a*b}.")
            texts.append(f"Subtract {b} from {a}: result is {a-b}.")
        for _ in range(40):
            texts.append("The fundamental theorem of calculus states that differentiation and integration are inverse operations.")
            texts.append("Quantum mechanics describes the behavior of matter and energy at atomic and subatomic scales.")
            texts.append("Evolution by natural selection is the primary mechanism driving the diversity of life on Earth.")
        for _ in range(30):
            texts.append("def quicksort(arr): return arr if len(arr) <= 1 else quicksort([x for x in arr[1:] if x <= arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x > arr[0]])")
            texts.append("class NeuralNetwork: def __init__(self, layers): self.layers = layers; self.weights = [torch.randn(m, n) * 0.01 for m, n in zip(layers[:-1], layers[1:])]")
        for _ in range(30):
            texts.append("The Roman Empire spanned over 500 years and covered three continents at its height.")
            texts.append("Shakespeare wrote 37 plays and 154 sonnets during the Elizabethan era.")
            texts.append("The Renaissance period marked a rebirth of art, science, and classical knowledge in Europe.")
        return "\n".join(texts)

    def _build_vocab(self, min_freq=2):
        """Construit un vocabulaire à partir du texte."""
        words = self.data.split()
        freq = {}
        for w in words:
            w_clean = w.strip('.,!?;:"\'()-[]{}<>').lower()
            if w_clean:
                freq[w_clean] = freq.get(w_clean, 0) + 1

        vocab = {'<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3}
        for w, f in sorted(freq.items(), key=lambda x: -x[1]):
            if f >= min_freq and len(vocab) < 5000:
                vocab[w] = len(vocab)

        ids = []
        for w in words:
            w_clean = w.strip('.,!?;:"\'()-[]{}<>').lower()
            ids.append(vocab.get(w_clean, vocab['<UNK>']))

        logger.info(f"  Vocabulaire: {len(vocab)} mots (min_freq={min_freq})")
        return vocab, torch.tensor(ids, dtype=torch.long)

    def _create_samples(self, max_samples):
        """Crée des échantillons avec chevauchement 50%."""
        samples = []
        step = max(1, self.seq_len // 2)
        for i in range(0, len(self.ids) - self.seq_len, step):
            if len(samples) >= max_samples:
                break
            samples.append(self.ids[i:i + self.seq_len])
        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x = self.samples[idx]
        return {'input_ids': x, 'labels': x}


# ============================================================================
# Fonctions utilitaires
# ============================================================================
def get_cosine_schedule(optimizer, current_step, warmup_steps, total_steps, min_lr_ratio=0.05):
    """Calcule le LR selon un schedule cosine avec warmup."""
    if current_step < warmup_steps:
        return DEFAULT_CONFIG['lr'] * (current_step / max(1, warmup_steps))
    else:
        progress = (current_step - warmup_steps) / max(1, total_steps - warmup_steps)
        cosine_decay = 0.5 * (1.0 + math.cos(math.pi * progress))
        return DEFAULT_CONFIG['lr'] * (min_lr_ratio + (1.0 - min_lr_ratio) * cosine_decay)


def estimate_time(config):
    """Estime le temps total d'entraînement basé sur le benchmark précédent."""
    # Benchmark: 100 steps en 453s avec batch=2, seq=128
    base_steps = 100
    base_time = 453.0
    base_batch = 2
    base_seq = 128

    # Facteurs d'échelle
    scale = (config['batch_size'] / base_batch) * (config['seq_len'] / base_seq)
    # Overhead fixe (~15%) réduit avec batch plus grand
    overhead = 1.0 + 0.15 * (base_batch / config['batch_size'])

    est_time_per_step = (base_time / base_steps) * scale * overhead
    est_total = est_time_per_step * config['steps']

    return est_time_per_step, est_total


# ============================================================================
# Entraînement principal
# ============================================================================
def train():
    parser = argparse.ArgumentParser(description='Entraînement harmonique 8h')
    parser.add_argument('--steps', type=int, default=DEFAULT_CONFIG['steps'])
    parser.add_argument('--seq_len', type=int, default=DEFAULT_CONFIG['seq_len'])
    parser.add_argument('--batch_size', type=int, default=DEFAULT_CONFIG['batch_size'])
    parser.add_argument('--grad_acc', type=int, default=DEFAULT_CONFIG['grad_acc'])
    parser.add_argument('--lr', type=float, default=DEFAULT_CONFIG['lr'])
    parser.add_argument('--samples', type=int, default=DEFAULT_CONFIG['samples'])
    parser.add_argument('--output', type=str, default=DEFAULT_CONFIG['output'])
    parser.add_argument('--save_every', type=int, default=DEFAULT_CONFIG['save_every'])
    parser.add_argument('--log_every', type=int, default=DEFAULT_CONFIG['log_every'])
    parser.add_argument('--resume', action='store_true', help='Reprendre depuis checkpoint')
    parser.add_argument('--dry-run', action='store_true', help='Estimer le temps sans entraîner')
    parser.add_argument('--max-time', type=float, default=DEFAULT_CONFIG['max_time_hours'],
                        help='Temps maximum en heures')
    args = parser.parse_args()

    # ── Estimation ──
    config_vars = {
        'steps': args.steps,
        'seq_len': args.seq_len,
        'batch_size': args.batch_size,
        'grad_acc': args.grad_acc,
        'lr': args.lr,
        'samples': args.samples,
    }
    time_per_step, est_total = estimate_time(config_vars)
    max_time_sec = args.max_time * 3600

    logger.info("=" * 60)
    logger.info("PLAN D'ENTRAÎNEMENT 8H")
    logger.info("=" * 60)
    logger.info(f"  Steps:     {args.steps}")
    logger.info(f"  Seq len:   {args.seq_len}")
    logger.info(f"  Batch:     {args.batch_size}")
    logger.info(f"  Grad acc:  {args.grad_acc}")
    logger.info(f"  LR:        {args.lr:.0e}")
    logger.info(f"  Samples:   {args.samples}")
    logger.info(f"  Save:      tous les {args.save_every} steps")
    logger.info(f"  Log:       tous les {args.log_every} steps")
    logger.info(f"── Estimation ──")
    logger.info(f"  Temps/step estimé: {time_per_step:.1f}s")
    logger.info(f"  Temps total estimé: {est_total:.0f}s ({est_total/3600:.1f}h)")
    logger.info(f"  Temps max autorisé: {max_time_sec:.0f}s ({args.max_time:.1f}h)")
    logger.info(f"  Steps max dans ce temps: {int(max_time_sec / max(time_per_step, 0.1))}")

    if args.dry_run:
        logger.info("Dry-run terminé.")
        return

    # Ajuster steps si dépasse le temps max
    max_steps_by_time = int(max_time_sec / max(time_per_step, 0.1))
    if max_steps_by_time < args.steps:
        logger.warning(f"  ⚠ Réduction à {max_steps_by_time} steps pour respecter le temps max")
        args.steps = max_steps_by_time

    # ── Device ──
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Device: {device}")

    # ── Dataset ──
    logger.info("Chargement du dataset...")
    dataset = TinyShakespeareDataset(
        seq_len=args.seq_len,
        max_samples=args.samples
    )
    loader = DataLoader(
        dataset, batch_size=args.batch_size,
        shuffle=True, num_workers=0,
        drop_last=True
    )

    # ── Modèle ──
    config = HARMONIC_CONFIGS['harmonic-tiny'].copy()
    config['max_len'] = args.seq_len
    config['dropout'] = 0.1
    config['vocab_size'] = len(dataset.vocab)

    model = HarmonicForCausalLM(config)
    model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Modèle: harmonic-tiny ({total_params:,} params)")

    # ── Optimizer ──
    optimizer = AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=DEFAULT_CONFIG['weight_decay'],
        betas=(0.9, 0.95)
    )

    # ── Output dir ──
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Reprise ──
    start_step = 0
    best_loss = float('inf')
    train_losses = []
    start_time = time.time()

    if args.resume:
        ckpt_files = sorted(output_dir.glob('checkpoint_step_*.pt'))
        if ckpt_files:
            latest = ckpt_files[-1]
            logger.info(f"Reprise depuis {latest}")
            ckpt = torch.load(latest, map_location=device, weights_only=False)
            model.load_state_dict(ckpt['model_state_dict'])
            optimizer.load_state_dict(ckpt['optimizer_state_dict'])
            start_step = ckpt['global_step']
            best_loss = ckpt.get('best_loss', float('inf'))
            logger.info(f"  Step de reprise: {start_step}, best_loss: {best_loss:.4f}")

            # Charger les métriques existantes (ignorer fichier corrompu)
            metrics_path = output_dir / 'training_metrics.json'
            if metrics_path.exists():
                try:
                    with open(metrics_path) as f:
                        old_metrics = json.load(f)
                    train_losses = old_metrics.get('train_losses', [])
                    logger.info(f"  {len(train_losses)} entrées de métriques chargées")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"  Métriques corrompues ({e}), démarrage à zéro")
                    train_losses = []

    # ── Entraînement ──
    model.train()
    data_iter = iter(loader)
    global_step = start_step
    warmup_steps = DEFAULT_CONFIG['warmup_steps']
    tokens_per_step = args.batch_size * args.seq_len
    max_time_abs = start_time + max_time_sec

    logger.info("=" * 60)
    logger.info("DÉBUT DE L'ENTRAÎNEMENT")
    logger.info(f"  Steps: {start_step} → {args.steps}")
    logger.info(f"  Durée max: {args.max_time:.1f}h (jusqu'à {datetime.fromtimestamp(max_time_abs).strftime('%H:%M:%S')})")
    logger.info("=" * 60)

    while global_step < args.steps:
        # Vérification du temps restant
        if time.time() >= max_time_abs:
            logger.warning(f"Temps maximum atteint ({args.max_time:.1f}h). Arrêt.")
            break

        optimizer.zero_grad()
        accumulated_loss = 0.0
        actual_batches = 0

        for _ in range(args.grad_acc):
            try:
                batch = next(data_iter)
            except StopIteration:
                data_iter = iter(loader)
                batch = next(data_iter)

            input_ids = batch['input_ids'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(input_ids, labels=labels)
            loss = outputs[1]  # (logits, loss)
            loss.backward()
            accumulated_loss += loss.item()
            actual_batches += 1

        # Gradient clipping
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()
        global_step += 1

        # LR scheduling (cosine avec warmup)
        current_lr = get_cosine_schedule(
            optimizer, global_step,
            warmup_steps, args.steps
        )
        for pg in optimizer.param_groups:
            pg['lr'] = current_lr

        # Logging périodique
        if global_step % args.log_every == 0 or global_step == args.steps or global_step == start_step + 1:
            avg_loss = accumulated_loss / max(actual_batches, 1)
            elapsed = time.time() - start_time
            tokens_per_sec = (global_step - start_step) * tokens_per_step / max(elapsed, 1)
            time_remaining = max_time_sec - elapsed
            progress_pct = (global_step - start_step) / max(1, args.steps - start_step) * 100

            logger.info(
                f"[{global_step:4d}/{args.steps}] "
                f"Loss: {avg_loss:.4f} | "
                f"Best: {best_loss:.4f} | "
                f"LR: {current_lr:.2e} | "
                f"Grad: {grad_norm:.2f} | "
                f"Tok/s: {tokens_per_sec:.0f} | "
                f"T: {elapsed:.0f}s "
                f"({elapsed/3600:.1f}h) "
                f"R: {time_remaining/3600:.1f}h | "
                f"{progress_pct:.0f}%"
            )

            train_losses.append({
                'step': global_step,
                'loss': avg_loss,
                'best_loss': best_loss,
                'lr': current_lr,
                'grad_norm': float(grad_norm),
                'tokens_per_sec': tokens_per_sec,
                'elapsed': elapsed,
                'time_remaining': time_remaining,
            })

            if avg_loss < best_loss:
                best_loss = avg_loss

        # Checkpoint périodique
        if global_step % args.save_every == 0:
            ckpt_path = output_dir / f'checkpoint_step_{global_step}.pt'
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'global_step': global_step,
                'best_loss': best_loss,
                'config': config,
                'args': vars(args),
                'timestamp': datetime.now().isoformat(),
            }, ckpt_path)
            logger.info(f"  ✅ Checkpoint: {ckpt_path} ({ckpt_path.stat().st_size / 1e6:.1f} MB)")

            # Sauvegarder les métriques à chaque checkpoint
            metrics = {
                'config': {
                    'model': 'harmonic-tiny',
                    'steps': args.steps,
                    'seq_len': args.seq_len,
                    'batch_size': args.batch_size,
                    'grad_acc': args.grad_acc,
                    'lr': args.lr,
                    'vocab_size': len(dataset.vocab),
                    'dataset_samples': len(dataset),
                    'total_params': total_params,
                    'trainable_params': trainable_params,
                },
                'train_losses': train_losses,
                'best_loss': best_loss,
                'total_time': time.time() - start_time,
                'total_params': total_params,
                'trainable_params': trainable_params,
                'timestamp': datetime.now().isoformat(),
            }
            with open(output_dir / 'training_metrics.json', 'w') as f:
                json.dump(metrics, f, indent=2)

    # ══════════════════════════════════════════════════
    # FIN DE L'ENTRAÎNEMENT
    # ══════════════════════════════════════════════════
    elapsed = time.time() - start_time

    logger.info("=" * 60)
    logger.info(f"{'ENTRAÎNEMENT TERMINÉ':^58}")
    logger.info("=" * 60)
    logger.info(f"  Steps:       {start_step} → {global_step} ({global_step - start_step} steps)")
    logger.info(f"  Durée:       {elapsed:.0f}s ({elapsed/3600:.2f}h)")
    logger.info(f"  Best loss:   {best_loss:.4f}")
    logger.info(f"  Final loss:  {train_losses[-1]['loss']:.4f}" if train_losses else "  Final loss:  N/A")
    logger.info(f"  Tokens vus:  {(global_step - start_step) * tokens_per_step:,}")
    logger.info(f"  Tokens/s:    {(global_step - start_step) * tokens_per_step / max(elapsed, 1):.0f}")
    logger.info("=" * 60)

    # Sauvegarder checkpoint final
    final_path = output_dir / 'checkpoint_final.pt'
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
        'optimizer_state_dict': optimizer.state_dict(),
        'metrics': {
            'steps': global_step,
            'best_loss': best_loss,
            'total_time': elapsed,
        },
    }, final_path)
    logger.info(f"Modèle final: {final_path} ({final_path.stat().st_size / 1e6:.1f} MB)")

    # Sauvegarder métriques finales
    metrics = {
        'config': {
            'model': 'harmonic-tiny',
            'steps': args.steps,
            'seq_len': args.seq_len,
            'batch_size': args.batch_size,
            'grad_acc': args.grad_acc,
            'lr': args.lr,
            'vocab_size': len(dataset.vocab),
            'dataset_samples': len(dataset),
            'total_params': total_params,
            'trainable_params': trainable_params,
        },
        'train_losses': train_losses,
        'best_loss': best_loss,
        'total_time': elapsed,
        'total_params': total_params,
        'trainable_params': trainable_params,
        'timestamp': datetime.now().isoformat(),
        'tokens_processed': (global_step - start_step) * tokens_per_step,
    }
    with open(output_dir / 'training_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Métriques: {output_dir / 'training_metrics.json'}")

    # Test de génération rapide
    logger.info("\nTest de génération rapide...")
    model.eval()
    test_tokens = ['the', 'what', 'i', 'you', 'king']
    for token_str in test_tokens:
        token_id = dataset.vocab.get(token_str, dataset.vocab.get('the', 1))
        prompt = torch.tensor([[token_id]], dtype=torch.long).to(device)
        with torch.no_grad():
            generated = model.generate(
                prompt,
                max_new_tokens=20,
                temperature=0.8,
                top_k=50
            )
        # Tentative de décodage simple
        id_to_word = {v: k for k, v in dataset.vocab.items()}
        decoded = ' '.join([id_to_word.get(i, '<?>') for i in generated[0].cpu().tolist()])
        logger.info(f"  [{token_str:6s}] → {decoded[:80]}")

    logger.info(f"\n✅ Entraînement terminé en {elapsed/3600:.2f}h")
    return metrics


if __name__ == '__main__':
    try:
        train()
    except KeyboardInterrupt:
        logger.warning("\nInterruption détectée. Checkpoint de sauvegarde...")
        # Le dernier checkpoint est déjà sauvegardé
        logger.info("Pour reprendre: python run_training_8h.py --resume")
    except Exception as e:
        logger.error(f"ERREUR: {e}")
        traceback.print_exc()
        sys.exit(1)
