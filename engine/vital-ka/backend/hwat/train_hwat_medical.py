"""
🏥 train_hwat_medical.py — Entraînement HWAT-Med-125M
=====================================================
Continued pre-training + SFT sur corpus médical.

Architecture cible: 125M params (dim=1024, 12 layers, 16 heads, seq=512)
Phase 1: Continued pre-training (100k steps)
Phase 2: SFT médical (50k paires Q/A)
Phase 3: LoRA spécialités (12 adapters)

Note: Sans GPU, entraînement CPU très lent. Script optimisé pour validation.
"""

import sys, math, time, json, random, os
from pathlib import Path
from typing import List, Iterator

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

from hwat_torch import OptimizedHWAT, create_125m_model, phase_attention_fast, mlp_fast, layernorm_amp_fast
from tokenizers import Tokenizer

# ════════════════════════════════════════════════════════════════════════════════
# CONFIG (adaptatif CPU/GPU)
# ════════════════════════════════════════════════════════════════════════════════

# Détecter device pour adapter la config
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
IS_CPU = DEVICE.type == 'cpu'

if IS_CPU:
    # Config MINI pour CPU (validation pipeline seulement)
    CONFIG = {
        'vocab_size': 50000,
        'dim': 256,
        'n_layers': 4,
        'n_heads': 4,
        'max_seq_len': 256,
        'hidden_mult': 4,
        'batch_size': 2,
        'seq_len': 128,
        'lr': 2e-4,
        'min_lr': 2e-5,
        'warmup_steps': 100,
        'max_steps': 100,
        'grad_accum': 4,
        'grad_clip': 1.0,
        'weight_decay': 0.1,
        'train_file': 'data/medical_corpus/train.txt',
        'val_file': 'data/medical_corpus/val.txt',
        'tokenizer_path': 'tokenizer_medical_50k/tokenizer.json',
        'save_every': 50,
        'eval_every': 25,
        'output_dir': 'checkpoints/hwat_med_125m',
        'resume_from': None,
    }
else:
    # Config 125M pour GPU
    CONFIG = {
        'vocab_size': 50000,
        'dim': 1024,
        'n_layers': 12,
        'n_heads': 16,
        'max_seq_len': 512,
        'hidden_mult': 4,
        'batch_size': 4,
        'seq_len': 256,
        'lr': 2e-4,
        'min_lr': 2e-5,
        'warmup_steps': 1000,
        'max_steps': 10000,
        'grad_accum': 8,
        'grad_clip': 1.0,
        'weight_decay': 0.1,
        'train_file': 'data/medical_corpus/train.txt',
        'val_file': 'data/medical_corpus/val.txt',
        'tokenizer_path': 'tokenizer_medical_50k/tokenizer.json',
        'save_every': 1000,
        'eval_every': 500,
        'output_dir': 'checkpoints/hwat_med_125m',
        'resume_from': None,
    }

# ═══════════════════════════════════════════════════════════════════════════════
# DATASET
# ═══════════════════════════════════════════════════════════════════════════════

class MedicalDataset(Dataset):
    """Dataset streaming pour gros corpus médical."""
    
    def __init__(self, file_path: str, tokenizer: Tokenizer, seq_len: int, 
                 stride: int = None, max_samples: int = None):
        self.file_path = Path(file_path)
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.stride = stride or seq_len // 2
        self.max_samples = max_samples
        
        # Charger et tokeniser tout le fichier (pour CPU, OK si < 100MB)
        print(f"  📖 Chargement {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"  🔤 Tokenisation...")
        encoded = tokenizer.encode(text)
        self.tokens = encoded.ids
        print(f"  ✅ {len(self.tokens):,} tokens chargés")
        
        # Créer les indices de début de séquence
        self.indices = list(range(0, len(self.tokens) - seq_len - 1, self.stride))
        if max_samples:
            self.indices = self.indices[:max_samples]
        
        print(f"  📊 {len(self.indices):,} échantillons (stride={self.stride})")
    
    def __len__(self):
        return len(self.indices)
    
    def __getitem__(self, idx):
        start = self.indices[idx]
        end = start + self.seq_len + 1
        chunk = self.tokens[start:end]
        
        x = torch.tensor(chunk[:-1], dtype=torch.long)
        y = torch.tensor(chunk[1:], dtype=torch.long)
        return x, y


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE HWAT-MED (avec LoRA support)
# ═══════════════════════════════════════════════════════════════════════════════

class LoRALinear(nn.Module):
    """LoRA (Low-Rank Adaptation) pour fine-tuning efficace."""
    
    def __init__(self, in_features: int, out_features: int, rank: int = 32, alpha: float = 32.0):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        # Poids de base (gelés)
        self.weight = nn.Parameter(torch.empty(out_features, in_features))
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        self.weight.requires_grad = False
        
        # LoRA weights (entraînables)
        self.lora_A = nn.Parameter(torch.empty(rank, in_features))
        self.lora_B = nn.Parameter(torch.empty(out_features, rank))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)
    
    def forward(self, x):
        # Base: x @ W^T
        base = F.linear(x, self.weight)
        # LoRA: x @ A^T @ B^T * scaling
        lora = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling
        return base + lora


class HWATMed(OptimizedHWAT):
    """HWAT-Med avec support LoRA pour spécialisation."""
    
    def __init__(self, *args, lora_rank: int = 32, lora_alpha: float = 32.0, **kwargs):
        # Désactiver l'init parente pour réinitialiser avec LoRA
        self.lora_rank = lora_rank
        self.lora_alpha = lora_alpha
        super().__init__(*args, **kwargs)
    
    def _init_blocks(self):
        """Remplace les MLP par versions LoRA."""
        D, H, L = self.dim, self.hidden_dim, self.n_layers
        dtype = self.dtype
        
        def det_normal(size, seed):
            gen = torch.Generator()
            gen.manual_seed(seed & 0xFFFFFFFF)
            return torch.randn(size, generator=gen, dtype=dtype)
        
        self.W1 = nn.ModuleList()
        self.b1 = nn.ParameterList()
        self.W2 = nn.ModuleList()
        self.b2 = nn.ParameterList()
        self.ln_gamma = nn.ParameterList()
        self.ln_beta = nn.ParameterList()
        
        for layer_id in range(L):
            lim1 = math.sqrt(3.0 / D)
            lim2 = math.sqrt(3.0 / H)
            s1 = _fnv1a(f"mlp_w1_{layer_id}")
            s3 = _fnv1a(f"mlp_w2_{layer_id}")
            
            # W1 avec LoRA
            w1_base = det_normal(D * H, s1).reshape(D, H) * 2 * lim1 - lim1
            lora_w1 = LoRALinear(D, H, rank=self.lora_rank, alpha=self.lora_alpha)
            lora_w1.weight.data = w1_base
            self.W1.append(lora_w1)
            self.b1.append(nn.Parameter(torch.zeros(H, dtype=dtype)))
            
            # W2 avec LoRA
            w2_base = det_normal(H * D, s3).reshape(H, D) * 2 * lim2 - lim2
            lora_w2 = LoRALinear(H, D, rank=self.lora_rank, alpha=self.lora_alpha)
            lora_w2.weight.data = w2_base
            self.W2.append(lora_w2)
            self.b2.append(nn.Parameter(torch.zeros(D, dtype=dtype)))
            
            self.ln_gamma.append(nn.Parameter(torch.ones(D, dtype=dtype)))
            self.ln_beta.append(nn.Parameter(torch.zeros(D, dtype=dtype)))
    
    def enable_lora_only(self):
        """Gèle tout sauf les poids LoRA."""
        for name, param in self.named_parameters():
            if 'lora_' in name:
                param.requires_grad = True
            else:
                param.requires_grad = False
        # Compter
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        print(f"  🔒 LoRA only: {trainable:,}/{total:,} params entraînables ({100*trainable/total:.1f}%)")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRAÎNEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def create_model(config: dict, device: torch.device) -> HWATMed:
    """Crée le modèle HWAT-Med."""
    print(f"\n🏗️ Création HWAT-Med...")
    print(f"   vocab={config['vocab_size']}, dim={config['dim']}, "
          f"layers={config['n_layers']}, heads={config['n_heads']}, "
          f"seq_len={config['max_seq_len']}")
    
    model = HWATMed(
        vocab_size=config['vocab_size'],
        dim=config['dim'],
        n_layers=config['n_layers'],
        n_heads=config['n_heads'],
        max_seq_len=config['max_seq_len'],
        hidden_mult=config['hidden_mult'],
        use_float32=True,
        lora_rank=32,
        lora_alpha=32.0,
    ).to(device)
    
    print(f"   Paramètres totaux: {sum(p.numel() for p in model.parameters()):,}")
    return model


def load_checkpoint(model: HWATMed, checkpoint_path: str, device: torch.device):
    """Charge un checkpoint (compatible NPZ→PT converti)."""
    print(f"  📥 Chargement checkpoint: {checkpoint_path}")
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    
    # Adapter les clés si nécessaire
    state_dict = ckpt.get('model_state_dict', ckpt)
    
    # Filtrer les clés compatibles
    model_dict = model.state_dict()
    filtered = {k: v for k, v in state_dict.items() if k in model_dict and v.shape == model_dict[k].shape}
    
    print(f"   Clés chargées: {len(filtered)}/{len(model_dict)}")
    model_dict.update(filtered)
    model.load_state_dict(model_dict, strict=False)
    
    return ckpt.get('config', {})


def evaluate(model: HWATMed, val_loader: DataLoader, device: torch.device, max_batches: int = 20):
    """Évaluation validation."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    
    with torch.no_grad():
        for i, (x, y) in enumerate(val_loader):
            if i >= max_batches:
                break
            x, y = x.to(device), y.to(device)
            
            # Forward par échantillon (pas de batch natif dans HWAT)
            batch_loss = 0.0
            for b in range(x.size(0)):
                logits = model(x[b])  # [L, V]
                loss = F.cross_entropy(logits, y[b], ignore_index=0)
                batch_loss += loss
            
            batch_loss = batch_loss / x.size(0)
            total_loss += batch_loss.item() * x.size(0) * x.size(1)
            total_tokens += x.size(0) * x.size(1)
    
    avg_loss = total_loss / max(1, total_tokens)
    ppl = math.exp(min(avg_loss, 20))  # Cap pour éviter overflow
    return avg_loss, ppl


def train_step(model: HWATMed, x: torch.Tensor, y: torch.Tensor, optimizer: torch.optim.Optimizer,
               device: torch.device, scaler: torch.cuda.amp.GradScaler = None):
    """Un step d'entraînement."""
    model.train()
    x, y = x.to(device), y.to(device)
    
    # Forward par échantillon
    total_loss = 0.0
    for b in range(x.size(0)):
        logits = model(x[b])  # [L, V]
        loss = F.cross_entropy(logits, y[b], ignore_index=0)
        total_loss += loss
    
    loss = total_loss / x.size(0)
    
    # Backward
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    
    return loss.item()


def main():
    print("═" * 70)
    print("  🏥 HWAT-MED ENTRAÎNEMENT — Phase 2")
    print("═" * 70)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"  Device: {device}")
    if device.type == 'cuda':
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        print(f"  ⚠️  CPU uniquement — entraînement TRÈS LENT")
        print(f"     Pour vrai entraînement: utiliser GPU (A100, H100, Colab, Kaggle)")
    
    # Tokenizer
    print(f"\n🔤 Chargement tokenizer...")
    tokenizer = Tokenizer.from_file(str(_ENGINE / CONFIG['tokenizer_path']))
    print(f"   Vocab size: {tokenizer.get_vocab_size():,}")
    
    # Datasets
    print(f"\n📊 Préparation datasets...")
    train_dataset = MedicalDataset(
        _ENGINE / CONFIG['train_file'], tokenizer, 
        seq_len=CONFIG['seq_len'], stride=CONFIG['seq_len'] // 2,
        max_samples=50000 if device.type == 'cpu' else None
    )
    val_dataset = MedicalDataset(
        _ENGINE / CONFIG['val_file'], tokenizer,
        seq_len=CONFIG['seq_len'], stride=CONFIG['seq_len'],
        max_samples=2000 if device.type == 'cpu' else None
    )
    
    train_loader = DataLoader(train_dataset, batch_size=CONFIG['batch_size'], 
                              shuffle=True, num_workers=0, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=CONFIG['batch_size'], 
                            shuffle=False, num_workers=0)
    
    # Modèle
    model = create_model(CONFIG, device)
    
    # Resume si spécifié
    start_step = 0
    if CONFIG['resume_from']:
        ckpt_config = load_checkpoint(model, CONFIG['resume_from'], device)
        start_step = ckpt_config.get('step', 0)
        print(f"  ↩️  Reprise à step {start_step}")
    
    # Optimiseur
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=CONFIG['lr'],
        weight_decay=CONFIG['weight_decay'],
        betas=(0.9, 0.95),
        eps=1e-8,
    )
    
    # LR scheduler (cosine avec warmup)
    def lr_lambda(step):
        if step < CONFIG['warmup_steps']:
            return step / CONFIG['warmup_steps']
        progress = (step - CONFIG['warmup_steps']) / max(1, CONFIG['max_steps'] - CONFIG['warmup_steps'])
        return CONFIG['min_lr'] / CONFIG['lr'] + (1 - CONFIG['min_lr'] / CONFIG['lr']) * 0.5 * (1 + math.cos(math.pi * progress))
    
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    
    # Mixed precision (GPU only)
    scaler = torch.cuda.amp.GradScaler() if device.type == 'cuda' else None
    
    # Output dir
    output_dir = _ENGINE / CONFIG['output_dir']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Boucle d'entraînement
    print(f"\n🚀 Début entraînement: {CONFIG['max_steps']:,} steps")
    print(f"   Batch size: {CONFIG['batch_size']} × {CONFIG['grad_accum']} accum = {CONFIG['batch_size'] * CONFIG['grad_accum']} effective")
    print(f"   Seq len: {CONFIG['seq_len']}")
    print(f"   LR: {CONFIG['lr']} → {CONFIG['min_lr']} (warmup {CONFIG['warmup_steps']})")
    
    model.train()
    step = start_step
    accum_loss = 0.0
    t0 = time.time()
    
    try:
        while step < CONFIG['max_steps']:
            for x, y in train_loader:
                if step >= CONFIG['max_steps']:
                    break
                
                # Gradient accumulation
                loss = train_step(model, x, y, optimizer, device, scaler)
                accum_loss += loss
                
                if (step + 1) % CONFIG['grad_accum'] == 0:
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                    
                    # Logs
                    if step % 10 == 0:
                        avg_loss = accum_loss / CONFIG['grad_accum']
                        ppl = math.exp(min(avg_loss, 20))
                        lr = scheduler.get_last_lr()[0]
                        elapsed = time.time() - t0
                        steps_per_sec = (step + 1) / elapsed if elapsed > 0 else 0
                        eta_hours = (CONFIG['max_steps'] - step) / max(1, steps_per_sec) / 3600
                        
                        print(f"  Step {step:6d} | Loss: {avg_loss:.4f} | PPL: {ppl:.2f} | "
                              f"LR: {lr:.2e} | {steps_per_sec:.2f} step/s | ETA: {eta_hours:.1f}h")
                    
                    accum_loss = 0.0
                
                # Évaluation
                if step % CONFIG['eval_every'] == 0 and step > 0:
                    val_loss, val_ppl = evaluate(model, val_loader, device, max_batches=10)
                    print(f"  📊 VAL Step {step} | Loss: {val_loss:.4f} | PPL: {val_ppl:.2f}")
                    model.train()
                
                # Checkpoint
                if step % CONFIG['save_every'] == 0 and step > 0:
                    ckpt_path = output_dir / f"step{step}.pt"
                    torch.save({
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'scheduler_state_dict': scheduler.state_dict(),
                        'config': CONFIG,
                        'step': step,
                        'loss': accum_loss / max(1, CONFIG['grad_accum']),
                    }, str(ckpt_path))
                    print(f"  💾 Checkpoint: {ckpt_path.name}")
                
                step += 1
    
    except KeyboardInterrupt:
        print("\n⏹️  Interruption utilisateur")
    
    # Checkpoint final
    final_path = output_dir / "model_final.pt"
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': CONFIG,
        'step': step,
    }, str(final_path))
    print(f"\n✅ Entraînement terminé. Modèle final: {final_path}")
    
    # Évaluation finale
    val_loss, val_ppl = evaluate(model, val_loader, device, max_batches=50)
    print(f"  📊 FINAL VAL | Loss: {val_loss:.4f} | PPL: {val_ppl:.2f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())