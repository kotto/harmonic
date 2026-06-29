"""
Calibration du ConditionEncoder (11D → 512D)
=============================================
Entraine le ConditionEncoder sur des paires (signature 9D moteur, texte corpus).
Ameliore le mapping signature → embedding, ce qui ameliore le PhiInverseDecoder.

Usage rapide (30s-2min selon le nombre d'echantillons):
    python calibrate_encoder.py --samples 200 --steps 20
"""

import sys
import os
import math
import time
import argparse
from pathlib import Path
from typing import List
import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_HARMONIC_TRAINING = _PROJECT_ROOT / "harmonic_training"
_CORPUS_DIR = _PROJECT_ROOT / "data" / "corpus"
_OUTPUT_DIR = _PROJECT_ROOT / "data" / "training_output"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_HARMONIC_TRAINING))

from engine.phi_diffusion_engine import ConditionEncoder
from engine.harmonic_engine import HarmonicResonanceEngine


def load_corpus_texts(corpus_dir: Path, max_texts: int = 2000) -> List[str]:
    """Charge les textes du corpus."""
    texts = []
    for path in sorted(corpus_dir.glob("*.txt")):
        if path.stat().st_size < 100:
            continue
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if len(line) > 30:
                    texts.append(line)
                    if len(texts) >= max_texts:
                        return texts
    return texts


def calibrate_encoder(
    texts: List[str],
    encoder: ConditionEncoder,
    engine: HarmonicResonanceEngine,
    n_samples: int = 200,
    n_steps_per_sample: int = 10,
    lr: float = 0.01,
) -> float:
    """Calibre le ConditionEncoder sur le corpus."""

    np.random.seed(42)
    indices = np.random.choice(len(texts), min(n_samples, len(texts)), replace=False)

    total_loss = 0.0
    n_processed = 0

    t0 = time.time()
    for i, idx in enumerate(indices):
        text = texts[idx]

        # 1. Signature 9D du moteur
        try:
            sig = engine.analyze(text)
            sig_dict = sig.to_dict()
            sig_9d = np.array([
                sig_dict.get("phi", sig.phi_ratio),
                sig_dict.get("alpha", sig.alpha_complexity),
                sig_dict.get("reasoning", sig.k_reasoning),
                sig_dict.get("creativity", sig.k_creative),
                sig_dict.get("math", sig.k_mathematical),
                sig_dict.get("factual", sig.k_factual),
                sig_dict.get("code", sig.k_code),
                sig_dict.get("emotion", sig.k_emotional),
                sig_dict.get("temporal", sig.k_temporal),
            ], dtype=np.float32)
        except Exception:
            continue

        # 2. Embedding cible: distribution de caracteres du texte
        # Chaque caractere est encode comme un vecteur de 512 dimensions
        # via des sinusoides de frequences harmoniques
        target = np.zeros(512, dtype=np.float32)
        chars = text[:512]
        for j, ch in enumerate(chars):
            # Encodage positionnel harmonique
            freq = (j + 1) / 512.0
            phase = ord(ch) * math.pi / 256.0
            pos = j % 512
            target[pos] += math.sin(freq * 2 * math.pi + phase) * 0.1

        # Normaliser
        norm = np.linalg.norm(target)
        if norm > 0:
            target /= norm

        # 3. Etendre a 11D
        sig_11d = np.pad(sig_9d, (0, 2), mode='constant', constant_values=0.5)

        # 4. Train step
        for _ in range(n_steps_per_sample):
            loss = encoder.train_step(
                sig_11d.reshape(1, 11),
                target.reshape(1, 512),
                lr=lr,
            )

        total_loss += loss
        n_processed += 1

        if (i + 1) % 50 == 0:
            elapsed = time.time() - t0
            print(f"  [{i+1}/{n_samples}] loss={loss:.6f}  "
                  f"avg_loss={total_loss/n_processed:.6f}  "
                  f"{elapsed:.0f}s")

    final_loss = total_loss / max(n_processed, 1)
    elapsed = time.time() - t0
    print(f"Calibration complete: {n_processed} samples in {elapsed:.0f}s")
    print(f"  Final avg_loss: {final_loss:.6f}")

    return final_loss


def main():
    parser = argparse.ArgumentParser(description="ConditionEncoder Calibration")
    parser.add_argument('--samples', type=int, default=200)
    parser.add_argument('--steps', type=int, default=10,
                       help='Training steps per sample')
    parser.add_argument('--lr', type=float, default=0.01)
    args = parser.parse_args()

    print("=" * 60)
    print("CONDITION ENCODER CALIBRATION")
    print(f"  Samples: {args.samples} | Steps/sample: {args.steps} | LR: {args.lr}")
    print("=" * 60)
    print()

    # Charger les textes
    print("Loading corpus...")
    texts = load_corpus_texts(_CORPUS_DIR, max_texts=max(2000, args.samples * 3))
    print(f"  {len(texts)} texts loaded")
    print()

    # Initialiser le moteur (light = sans fasttext pour la vitesse)
    print("Initializing harmonic engine (light mode)...")
    engine = HarmonicResonanceEngine(use_hologram='light')
    print()

    # Initialiser l'encoder
    encoder = ConditionEncoder()
    print(f"ConditionEncoder: {sum(p.size for p in [encoder.W1, encoder.W2]):,} params")
    print()

    # Calibrer
    print("Calibrating...")
    loss = calibrate_encoder(
        texts=texts,
        encoder=encoder,
        engine=engine,
        n_samples=args.samples,
        n_steps_per_sample=args.steps,
        lr=args.lr,
    )

    # Sauvegarder
    encoder_path = str(_OUTPUT_DIR / "condition_encoder_calibrated.npz")
    encoder.save(encoder_path)
    print(f"\nEncoder saved: {encoder_path}")

    # Metriques de validation
    print("\nValidation (5 echantillons):")
    for i in range(min(5, len(texts))):
        text = texts[i * 100 % len(texts)]
        try:
            sig = engine.analyze(text)
            sig_9d = np.array([sig.phi_ratio, sig.alpha_complexity] +
                             [getattr(sig, f'k_{d}', 0.5)
                              for d in ['reasoning','creative','mathematical','factual','code',
                                        'emotional','temporal']], dtype=np.float32)
            sig_11d = np.pad(sig_9d, (0, 2), mode='constant', constant_values=0.5)
            emb = encoder.encode(sig_11d)
            print(f"  [{text[:50]:.50s}...] → emb norm={np.linalg.norm(emb):.2f}")
        except Exception as e:
            print(f"  [error: {e}]")

    print()
    print("=" * 60)
    print("CALIBRATION COMPLETE")
    print(f"  Output: {encoder_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
