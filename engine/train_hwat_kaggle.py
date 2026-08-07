"""
🌊 HWAT-Med-125M — Kaggle/Colab GPU Training
============================================
Complete training script for HWAT-Med-125M on medical corpus.
Copy-paste into Kaggle/Colab notebook with GPU enabled.

Usage:
  1. Enable GPU: Kaggle Settings → Accelerator → GPU P100/T4
  2. Run this entire script in a single cell
  3. Checkpoints saved to /kaggle/working/checkpoints/
"""

import math, time, random, sys, os
from pathlib import Path
from typing import List, Iterator

# ═══════════════════════════════════════════════════════════════════════════════
# 0. SETUP — GPU Check
# ═══════════════════════════════════════════════════════════════════════════════

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("=" * 70)
print("  🌊 HWAT-Med-125M Training — Kaggle/Colab")
print(f"  Device: {device}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"  CUDA: {torch.version.cuda}")
    torch.backends.cudnn.benchmark = True
else:
    print("  ⚠️  NO GPU — Training will be VERY slow!")
    print("     Enable GPU: Settings → Accelerator → GPU")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. MODEL — HWAT with LoRA support (self-contained)
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
TAU = 2.0 * math.pi

def _fnv1a(s: str) -> int:
    h = 2166136261
    for ch in s.encode('utf-8'):
        h ^= ch; h = (h * 16777619) & 0xFFFFFFFF
    return h

def phase_attention_fast(psi: torch.Tensor, n_heads: int, causal: bool = True) -> torch.Tensor:
    """Wave-interference attention: phase coherence × amplitude."""
    L, D = psi.shape
    head_dim = D // n_heads
    heads = psi.reshape(L, n_heads, head_dim).permute(1, 0, 2)  # [H, L, d]
    
    A = heads.abs().float()
    phi = heads.angle().float()
    cos_phi = torch.cos(phi)
    sin_phi = torch.sin(phi)
    
    # Phase coherence: cos(φᵢ - φⱼ) = cosφᵢcosφⱼ + sinφᵢsinφⱼ
    phase_scores = (cos_phi @ cos_phi.transpose(1,2) + sin_phi @ sin_phi.transpose(1,2)) / head_dim
    
    # Amplitude modulation
    A_norm_sq = (A**2).sum(dim=-1)  # [H, L]
    amp_scores = torch.sqrt(torch.clamp(
        A_norm_sq.unsqueeze(2) * A_norm_sq.unsqueeze(1), min=1e-10
    ))
    
    scores = phase_scores * amp_scores
    
    if causal:
        mask = torch.triu(torch.ones(L, L, device=psi.device, dtype=torch.float32), diagonal=1)
        scores = scores - 1e9 * mask.unsqueeze(0)
    
    scores = scores - scores.max(dim=-1, keepdim=True).values
    attn = torch.softmax(scores.double(), dim=-1).float()
    
    out = attn.to(heads.dtype) @ heads  # [H, L, d]
    return out.permute(1, 0, 2).reshape(L, D).to(psi.dtype)

def mlp_fast(psi: torch.Tensor, W1: nn.Parameter, W2: nn.Parameter, 
             b1: nn.Parameter = None, b2: nn.Parameter = None) -> torch.Tensor:
    """MLP on amplitude space, phase preserved."""
    A = psi.abs().float()
    phase = psi.angle().float()
    h = A @ W1
    if b1 is not None:
        h = h + b1
    h = F.relu(h)
    A_new = h @ W2
    if b2 is not None:
        A_new = A_new + b2
    return (A_new * (torch.cos(phase) + 1j*torch.sin(phase))).to(psi.dtype)

def layernorm_amp_fast(psi: torch.Tensor, gamma: nn.Parameter = None, 
                       beta: nn.Parameter = None, eps: float = 1e-6) -> torch.Tensor:
    """LayerNorm on amplitude only."""
    A = psi.abs()
    mu = A.mean(dim=-1, keepdim=True)
    sigma = A.std(dim=-1, keepdim=True) + eps
    A_norm = (A - mu) / sigma
    if gamma is not None:
        A_norm = A_norm * gamma
    if beta is not None:
        A_norm = A_norm + beta
    phase = psi.angle()
    return (A_norm * (torch.cos(phase) + 1j*torch.sin(phase))).to(psi.dtype)


class LoRALinear(nn.Module):
    """LoRA (Low-Rank Adaptation) for efficient fine-tuning."""
    
    def __init__(self, in_features: int, out_features: int, rank: int = 32, alpha: float = 32.0):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        # Base weights (frozen)
        self.weight = nn.Parameter(torch.empty(out_features, in_features))
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        self.weight.requires_grad = False
        
        # LoRA weights (trainable)
        self.lora_A = nn.Parameter(torch.empty(rank, in_features))
        self.lora_B = nn.Parameter(torch.empty(out_features, rank))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Base: x @ W^T
        base = F.linear(x, self.weight)
        # LoRA: x @ A^T @ B^T * scaling
        lora = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling
        return base + lora
    
    def enable_lora_only(self):
        """Freeze base, train only LoRA."""
        self.weight.requires_grad = False
        self.lora_A.requires_grad = True
        self.lora_B.requires_grad = True


class HWATMed(nn.Module):
    """HWAT-Med with LoRA support for medical specialization."""
    
    def __init__(self, vocab_size: int, dim: int = 1024, n_layers: int = 12, 
                 n_heads: int = 16, max_seq_len: int = 512, hidden_mult: int = 4,
                 use_float32: bool = True, lora_rank: int = 32, lora_alpha: float = 32.0):
        super().__init__()
        self.vocab_size = vocab_size
        self.dim = dim
        self.n_layers = n_layers
        self.n_heads = n_heads
        self.max_seq_len = max_seq_len
        self.hidden_dim = dim * hidden_mult
        self.dtype = torch.float32 if use_float32 else torch.bfloat16
        self.lora_rank = lora_rank
        self.lora_alpha = lora_alpha
        self.ctype = torch.complex64 if use_float32 else torch.complex64  # bfloat16 complex not stable
        
        # Deterministic embeddings
        sigma = 1.0 / math.sqrt(dim)
        
        def det_norm(size, seed):
            g = torch.Generator()
            g.manual_seed(seed & 0xFFFFFFFF)
            return torch.randn(size, generator=g, dtype=torch.float32)
        
        # Token embeddings
        A_tab = torch.zeros(vocab_size, dim)
        phi_tok = torch.zeros(vocab_size, dim)
        for tok in range(vocab_size):
            v = det_norm(dim, _fnv1a(f"amp_{tok}")) * sigma
            A_tab[tok] = v / (v.norm() + 1e-30)
            phi_tok[tok] = det_norm(dim, _fnv1a(f"phi_{tok}")).fmod(1.0) * TAU
        
        # Positional encoding (φ-spaced)
        phi_pos = torch.zeros(max_seq_len, dim)
        ks = torch.arange(dim, dtype=torch.float32) / max(dim - 1, 1)
        omegas = 0.1 * torch.pow(torch.tensor(math.pi / 0.1), ks)
        for p in range(max_seq_len):
            phi_pos[p] = omegas * p
        
        self.register_buffer('A_table', A_tab)
        self.register_buffer('phi_token', phi_tok)
        self.register_buffer('phi_pos', phi_pos)
        
        # Blocks with LoRA MLPs
        self.W1 = nn.ModuleList()
        self.b1 = nn.ParameterList()
        self.W2 = nn.ModuleList()
        self.b2 = nn.ParameterList()
        self.ln_gamma = nn.ParameterList()
        self.ln_beta = nn.ParameterList()
        
        for layer_id in range(n_layers):
            lim1 = math.sqrt(3.0 / dim)
            lim2 = math.sqrt(3.0 / self.hidden_dim)
            s1 = _fnv1a(f"mlp_w1_{layer_id}")
            s3 = _fnv1a(f"mlp_w2_{layer_id}")
            
            # W1 with LoRA
            w1_base = det_norm(dim * self.hidden_dim, s1).reshape(dim, self.hidden_dim) * 2 * lim1 - lim1
            lora_w1 = LoRALinear(dim, self.hidden_dim, rank=lora_rank, alpha=lora_alpha)
            lora_w1.weight.data = w1_base
            self.W1.append(lora_w1)
            self.b1.append(nn.Parameter(torch.zeros(self.hidden_dim, dtype=torch.float32)))
            
            # W2 with LoRA
            w2_base = det_norm(self.hidden_dim * dim, s3).reshape(self.hidden_dim, dim) * 2 * lim2 - lim2
            lora_w2 = LoRALinear(self.hidden_dim, dim, rank=lora_rank, alpha=lora_alpha)
            lora_w2.weight.data = w2_base
            self.W2.append(lora_w2)
            self.b2.append(nn.Parameter(torch.zeros(dim, dtype=torch.float32)))
            
            # LayerNorm
            self.ln_gamma.append(nn.Parameter(torch.ones(dim, dtype=torch.float32)))
            self.ln_beta.append(nn.Parameter(torch.zeros(dim, dtype=torch.float32)))
        
        # LM Head
        g = torch.Generator()
        g.manual_seed(_fnv1a("lm_head") & 0xFFFFFFFF)
        self.lm_head = nn.Parameter(torch.randn(2*dim, vocab_size, generator=g) * math.sqrt(2.0 / (2*dim)))
        self.lm_bias = nn.Parameter(torch.zeros(vocab_size))
        
        print(f"  HWAT-Med created: {sum(p.numel() for p in self.parameters()):,} parameters")
    
    def embed(self, token_ids: torch.Tensor) -> torch.Tensor:
        L = min(len(token_ids), self.max_seq_len)
        token_ids = token_ids[:L]
        A = self.A_table[token_ids]
        phi_t = self.phi_token[token_ids]
        phi_p = self.phi_pos[:L]
        phi = phi_t + phi_p
        return (A * (torch.cos(phi) + 1j*torch.sin(phi))).to(self.ctype)
    
    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        psi = self.embed(token_ids)
        for li in range(self.n_layers):
            # Attention block
            x = layernorm_amp_fast(psi, self.ln_gamma[li], self.ln_beta[li])
            x = phase_attention_fast(x, self.n_heads, causal=True)
            psi = psi + x
            
            # MLP block
            x = layernorm_amp_fast(psi, self.ln_gamma[li], self.ln_beta[li])
            x = mlp_fast(x, self.W1[li].weight, self.W2[li].weight, 
                        self.b1[li], self.b2[li])
            psi = psi + x
        
        # Output projection
        psi_flat = torch.cat([psi.real.float(), psi.imag.float()], dim=-1)
        return psi_flat @ self.lm_head + self.lm_bias
    
    def enable_lora_only(self):
        """Freeze all except LoRA adapters."""
        for name, param in self.named_parameters():
            if 'lora_' in name:
                param.requires_grad = True
            else:
                param.requires_grad = False
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.parameters())
        print(f"  🔒 LoRA mode: {trainable:,}/{total:,} trainable ({100*trainable/total:.1f}%)")
    
    def load_pretrained(self, checkpoint_path: str, device: torch.device):
        """Load pretrained weights (from NPZ→PT conversion)."""
        print(f"  📥 Loading pretrained: {checkpoint_path}")
        ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
        state_dict = ckpt.get('model_state_dict', ckpt)
        
        # Match and load compatible keys
        model_dict = self.state_dict()
        matched = 0
        for k, v in state_dict.items():
            if k in model_dict and v.shape == model_dict[k].shape:
                model_dict[k].copy_(v)
                matched += 1
            elif k in model_dict:
                print(f"    ⚠️ Shape mismatch {k}: ckpt={v.shape} model={model_dict[k].shape}")
        
        print(f"    ✅ Matched {matched}/{len(model_dict)} parameters")
        return ckpt.get('config', {})


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TOKENIZER LOADER
# ═══════════════════════════════════════════════════════════════════════════════

def load_tokenizer(tokenizer_path: str):
    """Load tokenizer, downloading if needed."""
    from tokenizers import Tokenizer
    
    path = Path(tokenizer_path)
    if not path.exists():
        # Try to find in common locations
        for alt in [
            '/kaggle/input/vital-ka-tokenizer/tokenizer.json',
            '/content/tokenizer_medical_50k/tokenizer.json',
            './tokenizer_medical_50k/tokenizer.json',
        ]:
            if Path(alt).exists():
                path = Path(alt)
                break
    
    if not path.exists():
        raise FileNotFoundError(f"Tokenizer not found at {tokenizer_path}")
    
    tokenizer = Tokenizer.from_file(str(path))
    print(f"  ✅ Tokenizer loaded: {tokenizer.get_vocab_size():,} vocab")
    return tokenizer


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DATASET
# ═══════════════════════════════════════════════════════════════════════════════

class MedicalDataset(Dataset):
    """Streaming dataset for large medical corpus."""
    
    def __init__(self, file_path: str, tokenizer, seq_len: int, stride: int = None, 
                 max_samples: int = None, max_chars: int = None):
        self.file_path = Path(file_path)
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.stride = stride or seq_len // 2
        self.max_samples = max_samples
        
        print(f"  📖 Loading corpus: {file_path}")
        
        # Read file (with optional char limit for quick testing)
        if max_chars:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read(max_chars)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        print(f"  🔤 Tokenizing {len(text):,} characters...")
        encoded = tokenizer.encode(text)
        self.tokens = encoded.ids
        print(f"  ✅ {len(self.tokens):,} tokens")
        
        # Create sample indices
        self.indices = list(range(0, len(self.tokens) - seq_len - 1, self.stride))
        if max_samples:
            self.indices = self.indices[:max_samples]
        
        print(f"  📊 {len(self.indices):,} samples (stride={self.stride})")
    
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
# 4. TRAINING CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG = {
    # Model (125M params)
    'vocab_size': 50000,
    'dim': 1024,
    'n_layers': 12,
    'n_heads': 16,
    'max_seq_len': 512,
    'hidden_mult': 4,
    'use_float32': True,
    'lora_rank': 32,
    'lora_alpha': 32.0,
    
    # Training
    'batch_size': 4,          # Per GPU
    'seq_len': 256,           # Training sequence length
    'grad_accum': 8,          # Effective batch = 32
    'lr': 2e-4,
    'min_lr': 2e-5,
    'warmup_steps': 1000,
    'max_steps': 100000,      # 100k steps continued pre-training
    'grad_clip': 1.0,
    'weight_decay': 0.1,
    
    # Data
    'train_file': 'data/medical_corpus/train.txt',
    'val_file': 'data/medical_corpus/val.txt',
    'tokenizer_path': 'tokenizer_medical_50k/tokenizer.json',
    
    # Logging / Checkpointing
    'log_every': 10,
    'eval_every': 500,
    'save_every': 2000,
    'output_dir': '/kaggle/working/checkpoints/hwat_med_125m',
    
    # Resume
    'resume_from': None,  # e.g., '/kaggle/working/checkpoints/hwat_med_125m/step50000.pt'
    
    # Quick test mode (set to True for debugging)
    'quick_test': False,
    'quick_test_steps': 100,
    'quick_test_max_chars': 100000,
}

# Adjust for quick test
if CONFIG['quick_test']:
    CONFIG['max_steps'] = CONFIG['quick_test_steps']
    CONFIG['eval_every'] = 20
    CONFIG['save_every'] = 50
    CONFIG['log_every'] = 5


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TRAINING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate(model: HWATMed, val_loader: DataLoader, device: torch.device, max_batches: int = 20):
    """Evaluate on validation set."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    
    with torch.no_grad():
        for i, (x, y) in enumerate(val_loader):
            if i >= max_batches:
                break
            x, y = x.to(device), y.to(device)
            
            batch_loss = 0.0
            for b in range(x.size(0)):
                logits = model(x[b])
                loss = F.cross_entropy(logits, y[b], ignore_index=0)
                batch_loss += loss
            
            batch_loss = batch_loss / x.size(0)
            total_loss += batch_loss.item() * x.size(0) * x.size(1)
            total_tokens += x.size(0) * x.size(1)
    
    avg_loss = total_loss / max(1, total_tokens)
    ppl = math.exp(min(avg_loss, 20))
    return avg_loss, ppl


def train_one_batch(model: HWATMed, x: torch.Tensor, y: torch.Tensor, 
                    optimizer: torch.optim.Optimizer, device: torch.device,
                    scaler: torch.cuda.amp.GradScaler = None) -> float:
    """Train on one batch (with gradient accumulation support)."""
    model.train()
    x, y = x.to(device), y.to(device)
    
    if scaler is not None:
        with torch.cuda.amp.autocast():
            total_loss = 0.0
            for b in range(x.size(0)):
                logits = model(x[b])
                loss = F.cross_entropy(logits, y[b], ignore_index=0)
                total_loss += loss
            loss = total_loss / x.size(0)
        
        scaler.scale(loss).backward()
        return loss.item()
    else:
        total_loss = 0.0
        for b in range(x.size(0)):
            logits = model(x[b])
            loss = F.cross_entropy(logits, y[b], ignore_index=0)
            total_loss += loss
        loss = total_loss / x.size(0)
        
        loss.backward()
        return loss.item()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MAIN TRAINING LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  🏥 HWAT-MED-125M TRAINING")
    print("  Continued Pre-training on Medical Corpus")
    print("=" * 70)
    
    # Load tokenizer
    print(f"\n🔤 Loading tokenizer...")
    tokenizer = load_tokenizer(CONFIG['tokenizer_path'])
    
    # Datasets
    print(f"\n📊 Preparing datasets...")
    if CONFIG['quick_test']:
        train_dataset = MedicalDataset(
            CONFIG['train_file'], tokenizer, CONFIG['seq_len'],
            stride=CONFIG['seq_len'] // 2,
            max_samples=2000,
            max_chars=CONFIG['quick_test_max_chars']
        )
        val_dataset = MedicalDataset(
            CONFIG['val_file'], tokenizer, CONFIG['seq_len'],
            stride=CONFIG['seq_len'],
            max_samples=200,
            max_chars=10000
        )
    else:
        train_dataset = MedicalDataset(
            CONFIG['train_file'], tokenizer, CONFIG['seq_len'],
            stride=CONFIG['seq_len'] // 2
        )
        val_dataset = MedicalDataset(
            CONFIG['val_file'], tokenizer, CONFIG['seq_len'],
            stride=CONFIG['seq_len']
        )
    
    train_loader = DataLoader(train_dataset, batch_size=CONFIG['batch_size'],
                              shuffle=True, num_workers=2, drop_last=True, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=CONFIG['batch_size'],
                            shuffle=False, num_workers=1, pin_memory=True)
    
    # Model
    print(f"\n🏗️ Creating model...")
    model = HWATMed(
        vocab_size=CONFIG['vocab_size'],
        dim=CONFIG['dim'],
        n_layers=CONFIG['n_layers'],
        n_heads=CONFIG['n_heads'],
        max_seq_len=CONFIG['max_seq_len'],
        hidden_mult=CONFIG['hidden_mult'],
        use_float32=CONFIG['use_float32'],
        lora_rank=CONFIG['lora_rank'],
        lora_alpha=CONFIG['lora_alpha'],
    ).to(device)
    
    # Load pretrained if available (only if architectures match)
    start_step = 0
    if CONFIG['resume_from'] and Path(CONFIG['resume_from']).exists():
        ckpt_config = model.load_pretrained(CONFIG['resume_from'], device)
        start_step = ckpt_config.get('step', 0)
        print(f"  ↩️ Resuming from step {start_step}")
    else:
        # Try to load from local checkpoints (only if vocab/dim match)
        # Note: Local checkpoints are from smaller models (vocab=1000, dim=64)
        # so they won't match the 125M config (vocab=50000, dim=1024).
        # For continued pre-training, you need a matching 125M checkpoint.
        print("  ℹ️  Starting from random initialization (no matching 125M checkpoint found)")
        print("      For continued pre-training, provide a matching checkpoint via CONFIG['resume_from']")
    
    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=CONFIG['lr'],
        weight_decay=CONFIG['weight_decay'],
        betas=(0.9, 0.95),
        eps=1e-8,
    )
    
    # LR Scheduler (cosine with warmup)
    def lr_lambda(step):
        if step < CONFIG['warmup_steps']:
            return step / CONFIG['warmup_steps']
        progress = (step - CONFIG['warmup_steps']) / max(1, CONFIG['max_steps'] - CONFIG['warmup_steps'])
        return CONFIG['min_lr'] / CONFIG['lr'] + (1 - CONFIG['min_lr'] / CONFIG['lr']) * 0.5 * (1 + math.cos(math.pi * progress))
    
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    
    # Mixed precision
    scaler = torch.cuda.amp.GradScaler() if device.type == 'cuda' else None
    
    # Output directory
    output_dir = Path(CONFIG['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Training state
    step = start_step
    accum_loss = 0.0
    accum_count = 0
    t0 = time.time()
    best_val_loss = float('inf')
    
    print(f"\n🚀 Starting training: {CONFIG['max_steps']:,} steps")
    print(f"   Effective batch: {CONFIG['batch_size']} × {CONFIG['grad_accum']} = {CONFIG['batch_size'] * CONFIG['grad_accum']}")
    print(f"   Seq len: {CONFIG['seq_len']}")
    print(f"   LR: {CONFIG['lr']} → {CONFIG['min_lr']} (warmup {CONFIG['warmup_steps']})")
    print(f"   Output: {output_dir}")
    print("-" * 70)
    
    try:
        while step < CONFIG['max_steps']:
            for x, y in train_loader:
                if step >= CONFIG['max_steps']:
                    break
                
                # Train step
                loss = train_one_batch(model, x, y, optimizer, device, scaler)
                accum_loss += loss
                accum_count += 1
                
                # Gradient accumulation
                if (accum_count % CONFIG['grad_accum']) == 0:
                    if scaler is not None:
                        scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(model.parameters(), CONFIG['grad_clip'])
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), CONFIG['grad_clip'])
                        optimizer.step()
                    
                    scheduler.step()
                    optimizer.zero_grad()
                    
                    # Logging
                    if step % CONFIG['log_every'] == 0:
                        avg_loss = accum_loss / CONFIG['grad_accum']
                        ppl = math.exp(min(avg_loss, 20))
                        lr = scheduler.get_last_lr()[0]
                        elapsed = time.time() - t0
                        steps_per_sec = (step + 1) / elapsed if elapsed > 0 else 0
                        eta_hours = (CONFIG['max_steps'] - step) / max(1, steps_per_sec) / 3600
                        
                        print(f"  Step {step:6d} | Loss: {avg_loss:.4f} | PPL: {ppl:.2f} | "
                              f"LR: {lr:.2e} | {steps_per_sec:.2f} step/s | ETA: {eta_hours:.1f}h")
                    
                    accum_loss = 0.0
                
                # Evaluation
                if step % CONFIG['eval_every'] == 0 and step > 0:
                    val_loss, val_ppl = evaluate(model, val_loader, device, max_batches=20)
                    print(f"  📊 VAL Step {step} | Loss: {val_loss:.4f} | PPL: {val_ppl:.2f}")
                    
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        best_path = output_dir / "model_best.pt"
                        torch.save({
                            'model_state_dict': model.state_dict(),
                            'optimizer_state_dict': optimizer.state_dict(),
                            'scheduler_state_dict': scheduler.state_dict(),
                            'config': CONFIG,
                            'step': step,
                            'val_loss': val_loss,
                        }, str(best_path))
                        print(f"  💾 Best model saved: {best_path}")
                    
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
                        'loss': accum_loss / max(1, accum_count),
                    }, str(ckpt_path))
                    print(f"  💾 Checkpoint: {ckpt_path.name}")
                
                step += 1
    
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    
    # Final checkpoint
    final_path = output_dir / "model_final.pt"
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
        'config': CONFIG,
        'step': step,
    }, str(final_path))
    
    total_time = time.time() - t0
    print(f"\n{'='*70}")
    print(f"  ✅ Training complete!")
    print(f"  Steps: {step} | Time: {total_time/3600:.2f}h")
    print(f"  Steps/sec: {step/total_time:.2f}")
    print(f"  Final model: {final_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()