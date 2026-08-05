"""
🌊 HWAT PyTorch — Harmonic Wavelet Attention Transformer (GPU-ready)
====================================================================
Version PyTorch de hwat_optimized.py — identique fonctionnellement mais
tourne sur GPU (CUDA, MPS) ou CPU avec le même code.

Différences avec la version NumPy :
  - torch au lieu de numpy
  - torch.nn.Parameter pour les poids entraînables
  - torch.optim.Adam pour l'optimiseur intégré
  - torch.nn.functional.cross_entropy pour la loss
  - torch.Generator pour l'initialisation déterministe
  - device-aware : cpu | cuda | mps automatique

Usage :
  from hwat_torch import OptimizedHWAT, create_125m_model
  model = create_125m_model().cuda()
  logits = model(token_ids)  # forward pass sur GPU

Original NumPy : hwat_optimized.py (conservé intact)
"""

import math, time
from typing import List, Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES (équivalents NumPy → PyTorch)
# ═══════════════════════════════════════════════════════════════════════════════

def _fnv1a(s: str) -> int:
    h = 2166136261
    for ch in s.encode('utf-8'):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE ATTENTION (PyTorch)
# ═══════════════════════════════════════════════════════════════════════════════

def phase_attention_fast(psi: torch.Tensor, n_heads: int,
                         causal: bool = True) -> torch.Tensor:
    """
    Phase attention vectorisée par matmul — version PyTorch.

    Identique à la version NumPy mais utilise torch.
    Compatible GPU via les tenseurs PyTorch.

    Args:
        psi: [L, D] complex64 ou complex128
        n_heads: nombre de têtes
        causal: masque causal

    Returns:
        out: [L, D] complexe
    """
    L, D = psi.shape
    head_dim = D // n_heads

    # Split heads: [L, D] → [H, L, d]
    heads = psi.reshape(L, n_heads, head_dim).permute(1, 0, 2)
    H, L, d = heads.shape

    # Travailler en float32
    A = heads.abs().float()        # [H, L, d]
    phi = heads.angle().float()    # [H, L, d]

    # Scores de phase : cos(φ_i - φ_j) = cos(φ_i)cos(φ_j) + sin(φ_i)sin(φ_j)
    cos_phi = torch.cos(phi)
    sin_phi = torch.sin(phi)

    phase_scores = (cos_phi @ cos_phi.transpose(1, 2) +
                    sin_phi @ sin_phi.transpose(1, 2))
    phase_scores = phase_scores / d

    # Poids d'amplitude
    A_norm_sq = (A ** 2).sum(dim=-1)
    amp_scores = torch.sqrt(
        torch.clamp(A_norm_sq.unsqueeze(2) * A_norm_sq.unsqueeze(1), min=1e-10)
    )

    scores = phase_scores * amp_scores

    # Masque causal
    if causal:
        mask = torch.triu(torch.ones(L, L, device=psi.device, dtype=torch.float32), diagonal=1)
        scores = scores - 1e9 * mask.unsqueeze(0)

    # Softmax (double precision pour stabilité)
    scores = scores - scores.max(dim=-1, keepdim=True).values
    attn = torch.softmax(scores.double(), dim=-1).float()

    # Appliquer l'attention — attn est float, heads est complexe
    out = attn.to(heads.dtype) @ heads  # [H, L, L] @ [H, L, d] → [H, L, d]

    # Merge heads: [H, L, d] → [L, D]
    result = out.permute(1, 0, 2).reshape(L, D)
    return result.to(psi.dtype)


# ═══════════════════════════════════════════════════════════════════════════════
# MLP (PyTorch)
# ═══════════════════════════════════════════════════════════════════════════════

def mlp_fast(psi: torch.Tensor, W1: torch.Tensor, W2: torch.Tensor,
             b1: Optional[torch.Tensor] = None,
             b2: Optional[torch.Tensor] = None) -> torch.Tensor:
    """MLP sur l'amplitude — version PyTorch."""
    A = psi.abs().float()
    phase = psi.angle().float()

    h = A @ W1
    if b1 is not None:
        h = h + b1
    h = F.relu(h)
    A_new = h @ W2
    if b2 is not None:
        A_new = A_new + b2

    return (A_new * (torch.cos(phase) + 1j * torch.sin(phase))).to(psi.dtype)


# ═══════════════════════════════════════════════════════════════════════════════
# LAYERNORM (PyTorch)
# ═══════════════════════════════════════════════════════════════════════════════

def layernorm_amp_fast(psi: torch.Tensor,
                       gamma: Optional[torch.Tensor] = None,
                       beta: Optional[torch.Tensor] = None,
                       eps: float = 1e-6) -> torch.Tensor:
    """LayerNorm sur l'amplitude — version PyTorch."""
    A = psi.abs()
    mu = A.mean(dim=-1, keepdim=True)
    sigma = A.std(dim=-1, keepdim=True) + eps
    A_norm = (A - mu) / sigma

    if gamma is not None:
        A_norm = A_norm * gamma
    if beta is not None:
        A_norm = A_norm + beta

    phase = psi.angle()
    return (A_norm * (torch.cos(phase) + 1j * torch.sin(phase))).to(psi.dtype)


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE HWAT PYTHORCH
# ═══════════════════════════════════════════════════════════════════════════════

class OptimizedHWAT(nn.Module):
    """
    HWAT avec forward pass optimisé — version PyTorch GPU-ready.

    Paramètres identiques à la version NumPy (hwat_optimized.py).
    Hérite de nn.Module → automatiquement .cuda(), .to(device), etc.
    """

    def __init__(self,
                 vocab_size: int,
                 dim: int = 1024,
                 n_layers: int = 12,
                 n_heads: int = 16,
                 max_seq_len: int = 256,
                 hidden_mult: int = 4,
                 use_float32: bool = True):
        super().__init__()
        self.vocab_size = vocab_size
        self.dim = dim
        self.n_layers = n_layers
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.max_seq_len = max_seq_len
        self.hidden_dim = dim * hidden_mult
        self.dtype = torch.float32 if use_float32 else torch.float64
        self.ctype = torch.complex64 if use_float32 else torch.complex128

        # Embedding déterministe (buffer = pas de gradient)
        self._init_embedding()

        # Blocs MLP (paramètres entraînables)
        self._init_blocks()

        # Tête de langage (paramètre entraînable)
        self._init_lm_head()

        self._count_params()

    def _init_embedding(self):
        """Embedding déterministe φ-espacé (pas de gradient)."""
        V, D = self.vocab_size, self.dim
        dtype = self.dtype
        sigma = 1.0 / math.sqrt(D)

        # Utiliser torch.Generator pour la reproductibilité déterministe
        def det_normal(size, seed):
            gen = torch.Generator()
            gen.manual_seed(seed & 0xFFFFFFFF)
            return torch.randn(size, generator=gen, dtype=dtype)

        A_table = torch.zeros(V, D, dtype=dtype)
        phi_token = torch.zeros(V, D, dtype=dtype)
        for tok in range(V):
            s_a = _fnv1a(f"amp_{tok}")
            v = det_normal(D, s_a) * sigma
            A_table[tok] = v / (v.norm() + 1e-30)

            s_p = _fnv1a(f"phi_{tok}")
            phi_token[tok] = det_normal(D, s_p).fmod(1.0) * TAU

        # Phase positionnelle
        phi_pos = torch.zeros(self.max_seq_len, D, dtype=dtype)
        ks = torch.arange(D, dtype=dtype) / max(D - 1, 1)
        omegas = 0.1 * torch.pow(torch.tensor(math.pi / 0.1), ks)
        for pos in range(self.max_seq_len):
            phi_pos[pos] = omegas * pos

        self.register_buffer('A_table', A_table)
        self.register_buffer('phi_token', phi_token)
        self.register_buffer('phi_pos', phi_pos)

    def _init_blocks(self):
        """Initialise les poids entraînables des blocs MLP."""
        D, H, L = self.dim, self.hidden_dim, self.n_layers
        dtype = self.dtype

        def det_normal(size, seed):
            gen = torch.Generator()
            gen.manual_seed(seed & 0xFFFFFFFF)
            return torch.randn(size, generator=gen, dtype=dtype)

        self.W1 = nn.ParameterList()
        self.b1 = nn.ParameterList()
        self.W2 = nn.ParameterList()
        self.b2 = nn.ParameterList()
        self.ln_gamma = nn.ParameterList()
        self.ln_beta = nn.ParameterList()

        for layer_id in range(L):
            lim1 = math.sqrt(3.0 / D)
            lim2 = math.sqrt(3.0 / H)
            s1 = _fnv1a(f"mlp_w1_{layer_id}")
            s3 = _fnv1a(f"mlp_w2_{layer_id}")

            w1 = det_normal(D * H, s1).reshape(D, H) * 2 * lim1 - lim1
            w2 = det_normal(H * D, s3).reshape(H, D) * 2 * lim2 - lim2

            self.W1.append(nn.Parameter(w1))
            self.b1.append(nn.Parameter(torch.zeros(H, dtype=dtype)))
            self.W2.append(nn.Parameter(w2))
            self.b2.append(nn.Parameter(torch.zeros(D, dtype=dtype)))
            self.ln_gamma.append(nn.Parameter(torch.ones(D, dtype=dtype)))
            self.ln_beta.append(nn.Parameter(torch.zeros(D, dtype=dtype)))

    def _init_lm_head(self):
        D, V = self.dim, self.vocab_size
        dtype = self.dtype
        gen = torch.Generator()
        gen.manual_seed(_fnv1a("lm_head") & 0xFFFFFFFF)
        self.lm_head = nn.Parameter(
            torch.randn(2 * D, V, generator=gen, dtype=dtype) *
            math.sqrt(2.0 / (2 * D))
        )
        self.lm_bias = nn.Parameter(torch.zeros(V, dtype=dtype))

    def _count_params(self):
        count = sum(p.numel() for p in self.parameters())
        print(f"  HWAT PyTorch: {count:,} paramètres ({self.dtype})")

    def embed(self, token_ids: torch.Tensor) -> torch.Tensor:
        """Encode les tokens en vecteurs complexes ψ."""
        L = min(len(token_ids), self.max_seq_len)
        token_ids = token_ids[:L]

        A = self.A_table[token_ids]
        phi_tok = self.phi_token[token_ids]
        phi_pos = self.phi_pos[:L]
        phi = phi_tok + phi_pos

        return (A * (torch.cos(phi) + 1j * torch.sin(phi))).to(self.ctype)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass optimisé.

        Args:
            token_ids: [L] entiers

        Returns:
            logits: [L, vocab_size] float
        """
        psi = self.embed(token_ids)

        for layer_idx in range(self.n_layers):
            # Pre-norm + Attention
            x = layernorm_amp_fast(psi, self.ln_gamma[layer_idx],
                                   self.ln_beta[layer_idx])
            x = phase_attention_fast(x, self.n_heads, causal=True)
            psi = psi + x

            # Pre-norm + MLP
            x = layernorm_amp_fast(psi, self.ln_gamma[layer_idx],
                                   self.ln_beta[layer_idx])
            x = mlp_fast(x, self.W1[layer_idx], self.W2[layer_idx],
                        self.b1[layer_idx], self.b2[layer_idx])
            psi = psi + x

        # Tête LM
        psi_real = psi.real.float()
        psi_imag = psi.imag.float()
        psi_flat = torch.cat([psi_real, psi_imag], dim=-1)
        logits = psi_flat @ self.lm_head + self.lm_bias

        return logits


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def create_125m_model(vocab_size: int = 50000) -> OptimizedHWAT:
    """Crée un HWAT de ~125M paramètres."""
    return OptimizedHWAT(
        vocab_size=vocab_size, dim=1024, n_layers=12, n_heads=16,
        max_seq_len=256, hidden_mult=4, use_float32=True,
    )


def create_4_7m_model(vocab_size: int = 5000) -> OptimizedHWAT:
    """Crée un HWAT de ~4.7M paramètres."""
    return OptimizedHWAT(
        vocab_size=vocab_size, dim=256, n_layers=4, n_heads=4,
        max_seq_len=64, hidden_mult=4, use_float32=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRAÎNEMENT RAPIDE (compatible Kaggle/Colab)
# ═══════════════════════════════════════════════════════════════════════════════

def train_epoch(model: OptimizedHWAT, sequences: List[List[int]],
                batch_size: int, seq_len: int, optimizer: torch.optim.Optimizer,
                device: torch.device):
    """Une époque d'entraînement sur GPU."""
    import random
    model.train()
    total_loss = 0.0
    n_batches = len(sequences) // batch_size
    random.shuffle(sequences)

    for bi in range(n_batches):
        batch_seqs = sequences[bi * batch_size:(bi + 1) * batch_size]
        inputs = torch.zeros(batch_size, seq_len, dtype=torch.long, device=device)
        targets = torch.zeros(batch_size, seq_len, dtype=torch.long, device=device)

        for i, s in enumerate(batch_seqs):
            n = min(len(s), seq_len + 1)
            inputs[i, :n - 1] = torch.tensor(s[:n - 1], device=device)
            targets[i, :n - 1] = torch.tensor(s[1:n], device=device)

        # Forward
        batch_loss = 0.0
        for b in range(batch_size):
            logits = model(inputs[b])  # [L, V]
            loss = F.cross_entropy(
                logits.unsqueeze(0).transpose(1, 2),
                targets[b].unsqueeze(0),
                ignore_index=0,
            )
            batch_loss += loss

        batch_loss = batch_loss / batch_size
        total_loss += batch_loss.item()

        # Backward
        optimizer.zero_grad()
        batch_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

    return total_loss / max(1, n_batches)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST / BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"  Device: {device}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # ── Petit modèle ──
    print("\n── 1. Petit modèle (4.7M) ──")
    model_4m = create_4_7m_model(vocab_size=5000).to(device)
    print(f"  Paramètres: {sum(p.numel() for p in model_4m.parameters()):,}")

    tokens = torch.randint(0, 1000, (64,), device=device)

    # Warmup
    with torch.no_grad():
        _ = model_4m(tokens)
        _ = model_4m(tokens)

    # Benchmark
    n_runs = 50
    t0 = time.perf_counter()
    with torch.no_grad():
        for _ in range(n_runs):
            logits = model_4m(tokens)
    if device.type == 'cuda':
        torch.cuda.synchronize()
    t1 = time.perf_counter()
    avg_ms = (t1 - t0) / n_runs * 1000
    print(f"  Forward pass: {avg_ms:.2f} ms (moy. {n_runs} runs)")

    # ── Modèle 125M ──
    print("\n── 2. Modèle 125M ──")
    model_125m = create_125m_model(vocab_size=50000).to(device)
    print(f"  Paramètres: {sum(p.numel() for p in model_125m.parameters()):,}")

    tokens = torch.randint(0, 10000, (256,), device=device)

    # Warmup
    with torch.no_grad():
        _ = model_125m(tokens[:64])
        _ = model_125m(tokens[:128])
        _ = model_125m(tokens)

    # Benchmark
    n_runs = 10
    t0 = time.perf_counter()
    with torch.no_grad():
        for _ in range(n_runs):
            logits = model_125m(tokens)
    if device.type == 'cuda':
        torch.cuda.synchronize()
    t1 = time.perf_counter()
    avg_ms = (t1 - t0) / n_runs * 1000
    steps_per_sec = 1000 / avg_ms
    print(f"  Forward pass: {avg_ms:.2f} ms (~{steps_per_sec:.1f} step/s)")

    # Estimation entraînement
    if steps_per_sec > 0:
        for total_steps in [10000, 50000, 100000]:
            minutes = total_steps / steps_per_sec / 60
            print(f"    {total_steps:,} steps → {minutes:.0f} min ({minutes/60:.1f}h)")

    print("\n  ✅ HWAT PyTorch — Prêt pour Kaggle/Colab GPU")
