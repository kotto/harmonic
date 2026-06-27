"""
Script d'entrainement du modele harmonique
============================================
Entraine HarmonicForCausalLM sur FineWeb-edu avec :
- Dataset streaming (pas de telechargement complet)
- Precision mixte (bf16)
- Cosine learning rate scheduler
- Gradient accumulation
- Checkpointing periodique
- Evaluation sur validation set
- Suivi des signatures harmoniques 7D

Usage:
    python training/train.py --model harmonic-tiny --max_steps 1000
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
from torch.cuda.amp import autocast, GradScaler

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
from config.training_config import TrainingConfig
from model.tokenizer import HarmonicTokenizer


# =========================================================================
# LOGGING
# =========================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =========================================================================
# DATASET STREAMING (FineWeb-edu)
# =========================================================================

class FineWebDataset(IterableDataset):
    """
    Dataset iterable pour FineWeb-edu en streaming.
    
    Ne telecharge pas le dataset complet, lit les donnees
    a la volee depuis HuggingFace Datasets.
    Utilise le vrai tokenizer BPE harmonique.
    """
    
    def __init__(self, config: TrainingConfig, split: str = 'train'):
        self.config = config
        self.split = split
        # Initialiser le tokenizer BPE harmonique
        self.tokenizer = HarmonicTokenizer(vocab_size=config.vocab_size)
        self._tokenizer_trained = False
        
    def _ensure_tokenizer_trained(self, sample_texts):
        """Entraine le tokenizer sur un echantillon si pas deja fait."""
        if not self._tokenizer_trained:
            logger.info(f"Entrainement du tokenizer BPE sur {len(sample_texts)} echantillons...")
            self.tokenizer.train(sample_texts, verbose=False)
            self._tokenizer_trained = True
            logger.info(f"Tokenizer pret: {self.tokenizer.vocab_size} tokens")
        
    def __iter__(self):
        from datasets import load_dataset
        
        # Charger le dataset en streaming
        dataset = load_dataset(
            self.config.dataset_name,
            self.config.dataset_config,
            split=self.config.dataset_split if split == 'train' else 'validation',
            streaming=True
        )
        
        # Limiter le nombre d'echantillons si demande
        if self.config.max_samples is not None:
            dataset = dataset.take(self.config.max_samples)
        
        # Collecter d'abord quelques textes pour entrainer le tokenizer
        buffer_texts = []
        buffer_size = 100  # 100 textes suffisent pour un tokenizer basique
        
        for i, example in enumerate(dataset):
            text = example.get('text', '')
            if len(text) < 10:
                continue
            
            # Stocker pour l'entrainement du tokenizer
            if not self._tokenizer_trained and i < buffer_size:
                buffer_texts.append(text[:1000])  # Limiter a 1000 chars
            
            # Tokenization avec le vrai tokenizer BPE
            if self._tokenizer_trained or i >= buffer_size - 1:
                if not self._tokenizer_trained:
                    self._ensure_tokenizer_trained(buffer_texts)
                
                # Encoder avec le tokenizer BPE
                tokens = self.tokenizer.encode(
                    text[:self.config.sequence_length * 2],  # un peu plus pour compenser
                    add_special_tokens=True,
                    max_length=self.config.sequence_length
                )
                
                # Padding si necessaire
                if len(tokens) < self.config.sequence_length:
                    tokens = tokens + [self.tokenizer.pad_token_id] * (
                        self.config.sequence_length - len(tokens))
                
                yield {
                    'input_ids': torch.tensor(tokens[:self.config.sequence_length]),
                    'labels': torch.tensor(tokens[:self.config.sequence_length]),
                }
            
            # Si on a assez de textes pour entrainer le tokenizer
            if i == buffer_size - 1 and not self._tokenizer_trained:
                self._ensure_tokenizer_trained(buffer_texts)


# =========================================================================
# LEARNING RATE SCHEDULER
# =========================================================================

def get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps, min_lr_ratio=0.1):
    """
    Cosine learning rate scheduler avec warmup.
    
    LR augmente lineairement pendant warmup_steps,
    puis decroit en cosinus jusqu'a min_lr_ratio * max_lr.
    """
    def lr_lambda(current_step):
        if current_step < warmup_steps:
            return float(current_step) / float(max(1, warmup_steps))
        progress = float(current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        cosine_decay = 0.5 * (1.0 + math.cos(math.pi * progress))
        return min_lr_ratio + (1.0 - min_lr_ratio) * cosine_decay
    
    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


# =========================================================================
# ENTRAINEMENT
# =========================================================================

class HarmonicTrainer:
    """
    Entraineur pour le modele harmonique.
    
    Gere :
    - L'entrainement avec precision mixte
    - Le checkpointing
    - L'evaluation periodique
    - Le suivi des signatures harmoniques
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        
        # Device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Device: {self.device}")
        
        # Modele
        model_config = HARMONIC_CONFIGS[config.model_name]
        model_config['dropout'] = config.dropout
        model_config['max_len'] = config.sequence_length
        
        self.model = HarmonicForCausalLM(model_config)
        self.model.to(self.device)
        
        total_params = sum(p.numel() for p in self.model.parameters())
        logger.info(f"Modele: {config.model_name} ({total_params:,} parametres)")
        
        # Optimizer
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
            betas=(config.beta1, config.beta2),
            eps=config.epsilon
        )
        
        # Scheduler
        self.scheduler = get_cosine_schedule_with_warmup(
            self.optimizer,
            warmup_steps=config.warmup_steps,
            total_steps=config.max_steps,
            min_lr_ratio=config.min_lr_ratio
        )
        
        # Mixed precision
        self.use_amp = config.mixed_precision in ['fp16', 'bf16']
        self.amp_dtype = torch.bfloat16 if config.mixed_precision == 'bf16' else torch.float16
        self.scaler = GradScaler(enabled=(config.mixed_precision == 'fp16'))
        
        # Dataset
        self.train_dataset = FineWebDataset(config, split='train')
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=config.batch_size,
            num_workers=0,
            pin_memory=True
        )
        
        # Checkpoint directory
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tracking
        self.global_step = 0
        self.best_loss = float('inf')
        self.train_losses = []
        self.signature_history = []
    
    def train_step(self, batch):
        """Une etape d'entrainement."""
        input_ids = batch['input_ids'].to(self.device)
        labels = batch['labels'].to(self.device)
        
        # Forward avec precision mixte
        with autocast(device_type=self.device.type, dtype=self.amp_dtype, enabled=self.use_amp):
            logits, loss, signatures = self.model(input_ids, labels=labels)
        
        # Backward
        if self.config.mixed_precision == 'fp16':
            self.scaler.scale(loss).backward()
        else:
            loss.backward()
        
        return loss.item(), signatures
    
    def train(self):
        """Boucle d'entrainement principale."""
        logger.info("=" * 60)
        logger.info("DEBUT DE L'ENTRAINEMENT")
        logger.info("=" * 60)
        
        self.model.train()
        data_iter = iter(self.train_loader)
        
        start_time = time.time()
        accumulated_loss = 0.0
        
        while self.global_step < self.config.max_steps:
            # Gradient accumulation
            self.optimizer.zero_grad()
            
            for _ in range(self.config.gradient_accumulation_steps):
                try:
                    batch = next(data_iter)
                except StopIteration:
                    data_iter = iter(self.train_loader)
                    batch = next(data_iter)
                
                loss_val, signatures = self.train_step(batch)
                accumulated_loss += loss_val
            
            # Gradient clipping
            if self.config.mixed_precision == 'fp16':
                self.scaler.unscale_(self.optimizer)
            
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.config.gradient_clip_val
            )
            
            # Optimizer step
            if self.config.mixed_precision == 'fp16':
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                self.optimizer.step()
            
            self.scheduler.step()
            self.global_step += 1
            
            # Logging
            if self.global_step % self.config.logging_steps == 0:
                avg_loss = accumulated_loss / self.config.logging_steps
                lr = self.scheduler.get_last_lr()[0]
                elapsed = time.time() - start_time
                tokens_per_sec = (
                    self.global_step * self.config.batch_size * 
                    self.config.sequence_length * self.config.gradient_accumulation_steps / elapsed
                )
                
                logger.info(
                    f"Step {self.global_step:6d}/{self.config.max_steps} | "
                    f"Loss: {avg_loss:.4f} | "
                    f"LR: {lr:.2e} | "
                    f"Tokens/s: {tokens_per_sec:.0f} | "
                    f"Elapsed: {elapsed:.0f}s"
                )
                
                self.train_losses.append({
                    'step': self.global_step,
                    'loss': avg_loss,
                    'lr': lr,
                    'tokens_per_sec': tokens_per_sec
                })
                
                accumulated_loss = 0.0
            
            # Suivi des signatures harmoniques
            if self.global_step % (self.config.logging_steps * 10) == 0:
                sig_profile = signatures.mean(dim=(1, 2))  # [L, 7]
                self.signature_history.append({
                    'step': self.global_step,
                    'signatures': sig_profile.cpu().tolist()
                })
                
                # Afficher le profil
                dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']
                logger.info("  Profil harmonique moyen:")
                for i in range(min(4, sig_profile.shape[0])):
                    vals = sig_profile[i]
                    logger.info(f"    Couche {i}: " + " | ".join(
                        f"{d}={v.item():.3f}" for d, v in zip(dims, vals)
                    ))
            
            # Checkpoint
            if self.global_step % self.config.save_steps == 0:
                self.save_checkpoint()
            
            # Evaluation
            if self.global_step % self.config.eval_steps == 0:
                self.evaluate()
        
        # Fin de l'entrainement
        self.save_checkpoint(final=True)
        self.save_metrics()
        
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"ENTRAINEMENT TERMINE en {elapsed:.0f}s")
        logger.info(f"Steps: {self.global_step}, Best loss: {self.best_loss:.4f}")
        logger.info("=" * 60)
    
    def evaluate(self):
        """Evaluation sur le jeu de validation."""
        self.model.eval()
        
        # Creer un petit dataset de validation
        eval_dataset = FineWebDataset(self.config, split='validation')
        eval_loader = DataLoader(
            eval_dataset,
            batch_size=self.config.eval_batch_size,
            num_workers=0
        )
        
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for i, batch in enumerate(eval_loader):
                if i >= 10:  # Limiter a 10 batches
                    break
                
                input_ids = batch['input_ids'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                logits, loss, _ = self.model(input_ids, labels=labels)
                total_loss += loss.item()
                num_batches += 1
        
        avg_loss = total_loss / num_batches
        
        if avg_loss < self.best_loss:
            self.best_loss = avg_loss
            logger.info(f"  [Nouveau record] Validation loss: {avg_loss:.4f}")
        
        logger.info(f"  Validation loss: {avg_loss:.4f} (best: {self.best_loss:.4f})")
        
        self.model.train()
    
    def save_checkpoint(self, final=False):
        """Sauvegarde un checkpoint."""
        suffix = 'final' if final else f'step_{self.global_step}'
        checkpoint_path = self.output_dir / f'checkpoint_{suffix}.pt'
        
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'global_step': self.global_step,
            'best_loss': self.best_loss,
            'config': self.config.__dict__,
            'model_config': HARMONIC_CONFIGS[self.config.model_name],
        }
        
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Checkpoint sauvegarde: {checkpoint_path}")
    
    def save_metrics(self):
        """Sauvegarde les metriques d'entrainement."""
        metrics = {
            'config': self.config.__dict__,
            'train_losses': self.train_losses,
            'signature_history': self.signature_history,
            'best_loss': self.best_loss,
            'total_steps': self.global_step,
        }
        
        metrics_path = self.output_dir / 'training_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metriques sauvegardees: {metrics_path}")


# =========================================================================
# POINT D'ENTREE
# =========================================================================

def main():
    parser = argparse.ArgumentParser(description='Entrainement du modele harmonique')
    
    # Modele
    parser.add_argument('--model', type=str, default='harmonic-tiny',
                        choices=['harmonic-tiny', 'harmonic-small', 'harmonic-base',
                                'harmonic-large', 'harmonic-xl'])
    
    # Entrainement
    parser.add_argument('--max_steps', type=int, default=1000)
    parser.add_argument('--batch_size', type=int, default=2)
    parser.add_argument('--gradient_accumulation_steps', type=int, default=4)
    parser.add_argument('--learning_rate', type=float, default=3e-4)
    parser.add_argument('--sequence_length', type=int, default=512)
    
    # Checkpoint
    parser.add_argument('--output_dir', type=str, default='./checkpoints')
    parser.add_argument('--resume', type=str, default=None)
    
    # Precision
    parser.add_argument('--precision', type=str, default='bf16',
                        choices=['fp16', 'bf16', 'no'])
    
    args = parser.parse_args()
    
    # Configuration
    config = TrainingConfig(
        model_name=args.model,
        max_steps=args.max_steps,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        sequence_length=args.sequence_length,
        output_dir=args.output_dir,
        resume_from_checkpoint=args.resume,
        mixed_precision=args.precision,
    )
    
    # Entrainement
    trainer = HarmonicTrainer(config)
    
    # Resume from checkpoint
    if args.resume:
        checkpoint = torch.load(args.resume, map_location=trainer.device)
        trainer.model.load_state_dict(checkpoint['model_state_dict'])
        trainer.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        trainer.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        trainer.global_step = checkpoint['global_step']
        trainer.best_loss = checkpoint['best_loss']
        logger.info(f"Reprise depuis le checkpoint: {args.resume} (step {trainer.global_step})")
    
    trainer.train()


if __name__ == '__main__':
    main()
