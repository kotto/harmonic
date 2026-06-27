"""
Script d'entrainement simplifie pour le modele harmonique
==========================================================
Version CPU-friendly avec :
- Dataset FineWeb-edu sample-10BT en streaming (tres peu d'echantillons)
- Sequence length reduite (128 tokens)
- Batch size reduit (1)
- Gradient accumulation
- Suivi des signatures harmoniques 7D
- Checkpointing

Usage:
    python run_training.py --steps 50 --seq_len 128
"""

import os
import sys
import math
import time
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, IterableDataset
from torch.optim import AdamW

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
from model.tokenizer import HarmonicTokenizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SimpleTextDataset(IterableDataset):
    """
    Dataset iterable simple qui utilise un petit echantillon de FineWeb-edu.
    Version CPU-friendly : charge peu de donnees, sequence courte.
    """
    
    def __init__(self, max_samples=100, seq_len=128, vocab_size=50304):
        self.max_samples = max_samples
        self.seq_len = seq_len
        self.tokenizer = HarmonicTokenizer(vocab_size=vocab_size)
        self._tokenizer_trained = False
    
    def _train_tokenizer(self, texts):
        """Entraine le tokenizer BPE sur les textes."""
        logger.info(f"Entrainement du tokenizer BPE sur {len(texts)} echantillons...")
        self.tokenizer.train(texts, verbose=True)
        self._tokenizer_trained = True
        logger.info(f"Tokenizer pret: {self.tokenizer.vocab_size} tokens")
    
    def __iter__(self):
        from datasets import load_dataset
        
        # Charger un petit echantillon de FineWeb-edu
        dataset = load_dataset(
            'HuggingFaceFW/fineweb-edu',
            'sample-10BT',
            split='train',
            streaming=True
        )
        dataset = dataset.take(self.max_samples + 50)  # un peu plus pour le tokenizer
        
        # Collecter les textes
        texts = []
        for i, example in enumerate(dataset):
            text = example.get('text', '')
            if len(text) < 20:
                continue
            texts.append(text)
            
            if len(texts) >= self.max_samples + 10:
                break
        
        # Entrainer le tokenizer sur les premiers textes
        train_texts = texts[:10]
        self._train_tokenizer(train_texts)
        
        # Generer les echantillons
        count = 0
        for text in texts[10:]:
            if count >= self.max_samples:
                break
            
            # Tokenizer
            tokens = self.tokenizer.encode(
                text[:self.seq_len * 3],
                add_special_tokens=True,
                max_length=self.seq_len
            )
            
            # Padding
            if len(tokens) < self.seq_len:
                tokens = tokens + [self.tokenizer.pad_token_id] * (
                    self.seq_len - len(tokens))
            
            yield {
                'input_ids': torch.tensor(tokens[:self.seq_len], dtype=torch.long),
                'labels': torch.tensor(tokens[:self.seq_len], dtype=torch.long),
            }
            count += 1


def train():
    parser = argparse.ArgumentParser(description='Entrainement harmonique simplifie')
    parser.add_argument('--steps', type=int, default=50, help='Nombre de steps')
    parser.add_argument('--seq_len', type=int, default=128, help='Longueur de sequence')
    parser.add_argument('--batch_size', type=int, default=1, help='Batch size')
    parser.add_argument('--grad_acc', type=int, default=4, help='Gradient accumulation')
    parser.add_argument('--lr', type=float, default=3e-4, help='Learning rate')
    parser.add_argument('--samples', type=int, default=100, help='Echantillons dataset')
    parser.add_argument('--output', type=str, default='./checkpoints', help='Dossier sortie')
    args = parser.parse_args()
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Device: {device}")
    
    # Modele
    config = HARMONIC_CONFIGS['harmonic-tiny'].copy()
    config['max_len'] = args.seq_len
    config['dropout'] = 0.1
    
    model = HarmonicForCausalLM(config)
    model.to(device)
    
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Modele: harmonic-tiny ({total_params:,} parametres)")
    logger.info(f"Configuration: seq_len={args.seq_len}, batch={args.batch_size}, "
                f"grad_acc={args.grad_acc}, lr={args.lr}")
    
    # Optimizer
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    
    # Dataset
    dataset = SimpleTextDataset(
        max_samples=args.samples,
        seq_len=args.seq_len,
        vocab_size=config['vocab_size']
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, num_workers=0)
    
    # Output dir
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Entrainement
    model.train()
    data_iter = iter(loader)
    global_step = 0
    best_loss = float('inf')
    train_losses = []
    signature_history = []
    start_time = time.time()
    
    logger.info("=" * 60)
    logger.info("DEBUT DE L'ENTRAINEMENT")
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
            
            logits, loss, signatures = model(input_ids, labels=labels)
            loss.backward()
            accumulated_loss += loss.item()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        
        optimizer.step()
        global_step += 1
        
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
                f"Tokens/s: {tokens_per_sec:.0f} | "
                f"Elapsed: {elapsed:.0f}s"
            )
            
            train_losses.append({
                'step': global_step,
                'loss': avg_loss,
                'tokens_per_sec': tokens_per_sec
            })
            
            # Signatures harmoniques
            if signatures is not None:
                sig_profile = signatures.mean(dim=(1, 2))  # [L, 7]
                signature_history.append({
                    'step': global_step,
                    'signatures': sig_profile.cpu().tolist()
                })
                
                dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']
                logger.info("  Profil harmonique moyen:")
                for i in range(min(4, sig_profile.shape[0])):
                    vals = sig_profile[i]
                    logger.info(f"    Couche {i}: " + " | ".join(
                        f"{d}={v.item():.3f}" for d, v in zip(dims, vals)
                    ))
        
        # Checkpoint
        if global_step % 25 == 0 or global_step == args.steps:
            checkpoint_path = output_dir / f'checkpoint_step_{global_step}.pt'
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'global_step': global_step,
                'best_loss': best_loss,
                'config': config,
            }, checkpoint_path)
            logger.info(f"Checkpoint: {checkpoint_path}")
    
    # Fin
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"ENTRAINEMENT TERMINE en {elapsed:.0f}s")
    logger.info(f"Steps: {global_step}, Best loss: {best_loss:.4f}")
    logger.info("=" * 60)
    
    # Sauvegarder les metriques
    metrics = {
        'config': {
            'model': 'harmonic-tiny',
            'steps': args.steps,
            'seq_len': args.seq_len,
            'batch_size': args.batch_size,
            'grad_acc': args.grad_acc,
            'lr': args.lr,
        },
        'train_losses': train_losses,
        'signature_history': signature_history,
        'best_loss': best_loss,
        'total_time': elapsed,
        'total_params': total_params,
    }
    
    metrics_path = output_dir / 'training_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metriques: {metrics_path}")
    
    # Checkpoint final
    final_path = output_dir / 'checkpoint_final.pt'
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
        'metrics': metrics,
    }, final_path)
    logger.info(f"Modele final: {final_path}")
    
    return metrics


if __name__ == '__main__':
    train()
