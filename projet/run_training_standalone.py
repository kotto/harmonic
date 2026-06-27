"""
Entraînement autonome du modèle harmonic-tiny
===============================================
Version standalone : ne nécessite ni datasets HF ni tokenizer externe.
Utilise un petit dataset réel (TinyShakespeare ou texte synthétique).

Usage:
    python run_training_standalone.py --steps 50 --seq_len 128
"""

import os
import sys
import math
import time
import json
import argparse
import logging
import urllib.request
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
# Tiny Shakespeare Dataset
# ============================================================================

TINY_SHAKESPEARE_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"

class TinyShakespeareDataset(Dataset):
    """
    Dataset basé sur TinyShakespeare.
    Tokenisation simple au niveau mot avec vocabulaire limité.
    """
    
    def __init__(self, seq_len=128, max_samples=500, min_freq=2):
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
        # Mathématiques
        for _ in range(50):
            a, b = torch.randint(1, 100, (2,)).tolist()
            texts.append(f"What is {a} plus {b}? The answer is {a+b}.")
            texts.append(f"Calculate {a} times {b}. Result: {a*b}.")
        # Science
        texts.append("The Earth orbits the Sun at a distance of 150 million kilometers.")
        texts.append("Water boils at 100 degrees Celsius at sea level pressure.")
        texts.append("Light travels at approximately 300000 kilometers per second.")
        texts.append("DNA contains the genetic instructions for all living organisms.")
        # Code
        texts.append("def fibonacci(n): return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)")
        texts.append("for i in range(10): print(i) class Animal: pass")
        texts.append("import numpy as np array = np.zeros((10, 10))")
        # Général
        texts.append("The quick brown fox jumps over the lazy dog near the bank of the river.")
        texts.append("Artificial intelligence is transforming how we interact with technology.")
        texts.append("The history of mathematics spans thousands of years of human discovery.")
        texts.append("Machine learning algorithms can recognize patterns in complex data.")
        return "\n".join(texts * 10)
    
    def _build_vocab(self, min_freq=2):
        """Construit un vocabulaire à partir du texte."""
        words = self.data.split()
        freq = {}
        for w in words:
            w_clean = w.strip('.,!?;:"\'()-[]{}<>').lower()
            if w_clean:
                freq[w_clean] = freq.get(w_clean, 0) + 1
        
        # Tokenizer simple
        vocab = {'<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3}
        for w, f in sorted(freq.items(), key=lambda x: -x[1]):
            if f >= min_freq and len(vocab) < 5000:
                vocab[w] = len(vocab)
        
        # Convertir le texte en IDs
        ids = []
        for w in words:
            w_clean = w.strip('.,!?;:"\'()-[]{}<>').lower()
            ids.append(vocab.get(w_clean, vocab['<UNK>']))
        
        logger.info(f"  Vocabulaire: {len(vocab)} mots (min_freq={min_freq})")
        return vocab, torch.tensor(ids, dtype=torch.long)
    
    def _create_samples(self, max_samples):
        """Crée des échantillons de séquences."""
        samples = []
        step = self.seq_len // 2  # chevauchement de 50%
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
# Entraînement
# ============================================================================

def train():
    parser = argparse.ArgumentParser(description='Entraînement harmonique standalone')
    parser.add_argument('--steps', type=int, default=100, help='Nombre de steps')
    parser.add_argument('--seq_len', type=int, default=128, help='Longueur de séquence')
    parser.add_argument('--batch_size', type=int, default=2, help='Batch size')
    parser.add_argument('--grad_acc', type=int, default=2, help='Gradient accumulation')
    parser.add_argument('--lr', type=float, default=3e-4, help='Learning rate')
    parser.add_argument('--samples', type=int, default=500, help='Échantillons dataset')
    parser.add_argument('--output', type=str, default='./training_output', help='Dossier sortie')
    args = parser.parse_args()
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Device: {device}")
    
    # Modèle harmonic-tiny
    config = HARMONIC_CONFIGS['harmonic-tiny'].copy()
    config['max_len'] = args.seq_len
    config['dropout'] = 0.1
    config['vocab_size'] = 5000  # vocabulaire limité
    
    model = HarmonicForCausalLM(config)
    model.to(device)
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Modèle: harmonic-tiny")
    logger.info(f"  Paramètres: {total_params:,} (trainable: {trainable_params:,})")
    logger.info(f"  Configuration: seq_len={args.seq_len}, batch={args.batch_size}, "
                f"grad_acc={args.grad_acc}, lr={args.lr}")
    
    # Optimizer
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    
    # Dataset
    logger.info("Chargement du dataset...")
    dataset = TinyShakespeareDataset(
        seq_len=args.seq_len,
        max_samples=args.samples
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    
    # Output dir
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Entraînement
    model.train()
    data_iter = iter(loader)
    global_step = 0
    best_loss = float('inf')
    train_losses = []
    start_time = time.time()
    
    logger.info("=" * 60)
    logger.info("DÉBUT DE L'ENTRAÎNEMENT")
    logger.info("=" * 60)
    
    while global_step < args.steps:
        optimizer.zero_grad()
        accumulated_loss = 0.0
        
        for _ in range(args.grad_acc):
            try:
                batch = next(data_iter)
            except StopIteration:
                data_iter = iter(loader)
                batch = next(data_iter)
            
            input_ids = batch['input_ids'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids, labels=labels)
            logits = outputs[0]
            loss = outputs[1]
            
            loss.backward()
            accumulated_loss += loss.item()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        
        optimizer.step()
        global_step += 1
        
        # Learning rate scheduling (cosine avec warmup)
        if global_step < 10:
            lr_scale = min(1.0, global_step / 10)
            for pg in optimizer.param_groups:
                pg['lr'] = args.lr * lr_scale
        else:
            progress = (global_step - 10) / (args.steps - 10)
            lr_scale = 0.5 * (1.0 + math.cos(math.pi * progress))
            for pg in optimizer.param_groups:
                pg['lr'] = args.lr * lr_scale
        
        # Logging
        if global_step % 5 == 0 or global_step == args.steps:
            avg_loss = accumulated_loss / args.grad_acc
            elapsed = time.time() - start_time
            tokens_per_sec = (
                global_step * args.batch_size * args.seq_len * args.grad_acc / elapsed
            ) if elapsed > 0 else 0
            
            logger.info(
                f"Step {global_step:4d}/{args.steps} | "
                f"Loss: {avg_loss:.4f} | "
                f"LR: {optimizer.param_groups[0]['lr']:.2e} | "
                f"Tokens/s: {tokens_per_sec:.0f} | "
                f"Temps: {elapsed:.0f}s"
            )
            
            train_losses.append({
                'step': global_step,
                'loss': avg_loss,
                'lr': optimizer.param_groups[0]['lr'],
                'tokens_per_sec': tokens_per_sec
            })
            
            # Mise à jour best_loss
            if avg_loss < best_loss:
                best_loss = avg_loss
        
        # Checkpoint périodique
        if global_step % 25 == 0:
            ckpt_path = output_dir / f'checkpoint_step_{global_step}.pt'
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'global_step': global_step,
                'best_loss': best_loss,
                'config': config,
            }, ckpt_path)
            logger.info(f"  Checkpoint: {ckpt_path}")
    
    # Fin
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"ENTRAÎNEMENT TERMINÉ en {elapsed:.0f}s")
    logger.info(f"Steps: {global_step}, Best loss: {best_loss:.4f}")
    logger.info("=" * 60)
    
    # Sauvegarder les métriques
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
        },
        'train_losses': train_losses,
        'best_loss': best_loss,
        'total_time': elapsed,
        'total_params': total_params,
        'trainable_params': trainable_params,
        'timestamp': datetime.now().isoformat(),
    }
    
    metrics_path = output_dir / 'training_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Métriques: {metrics_path}")
    
    # Checkpoint final
    final_path = output_dir / 'checkpoint_final.pt'
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
        'optimizer_state_dict': optimizer.state_dict(),
        'metrics': metrics,
    }, final_path)
    logger.info(f"Modèle final: {final_path}")
    
    # Test de génération rapide
    logger.info("\nTest de génération rapide...")
    model.eval()
    prompt = torch.tensor([[dataset.vocab.get('the', dataset.vocab['<UNK>'])]], 
                          dtype=torch.long).to(device)
    with torch.no_grad():
        generated = model.generate(
            prompt, 
            max_new_tokens=30,
            temperature=0.8,
            top_k=50
        )
    logger.info(f"  Prompt: 'the'")
    logger.info(f"  Généré: {generated[0].cpu().tolist()}")
    
    return metrics


if __name__ == '__main__':
    train()
