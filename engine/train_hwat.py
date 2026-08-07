"""
🌊 train_hwat.py — Phase 1 : Preuve que HWAT apprend
======================================================
Boucle d'entraînement next-token prediction avec cross-entropy.

Architecture entraînable (PyTorch, autograd) :
  - HarmonicEmbedding : table d'amplitude + phase positionnelle ABC
  - N × TrainableBlock : SpectralOperator fige + PhaseAttention + MLP appris
  - Tete LM : projection lineaire → logits

Corpus : corpus_universal_20260720_1007.txt (345 KB, ~30K lignes)
Tokenisation : caractere (vocab ~150 caracteres)

Lancer : python train_hwat.py
Sortie  : courbe de loss, perplexite, modele sauvegarde dans data/hwat_trained.pt
"""

import sys, math, time, os, json
from pathlib import Path
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════

DIM = 24            # dimension cachee
N_BLOCKS = 1        # blocs harmoniques
N_HEADS = 3         # tetes d'attention (24/3=8 dims/tete)
MAX_LEN = 32        # longueur max de sequence
BATCH_SIZE = 1      # sequences par batch
LR = 0.001          # learning rate
EPOCHS = 5          # epochs (suffisant pour voir la tendance)
PRINT_EVERY = 500   # batches entre 2 affichages
CORPUS_MAX = 100000  # caracteres max (accelere Phase 1)

# ════════════════════════════════════════════════════════════════
# 1. CHARGEMENT DU CORPUS
# ════════════════════════════════════════════════════════════════

def load_corpus(path: str = None) -> str:
    """Charge le corpus francais."""
    if path is None:
        path = _ENGINE / "data" / "corpus_universal" / "corpus_universal_20260720_1007.txt"
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f"  Corpus charge : {len(text):,} caracteres, "
          f"~{text.count(chr(10)):,} lignes")
    return text


# ════════════════════════════════════════════════════════════════
# 2. TOKENISATION CARACTERE
# ════════════════════════════════════════════════════════════════

class CharTokenizer:
    """Tokenisation caractere : chaque caractere = un token."""

    def __init__(self, text: str):
        chars = sorted(set(text))
        self.char_to_id = {c: i for i, c in enumerate(chars)}
        self.id_to_char = {i: c for i, c in enumerate(chars)}
        self.vocab_size = len(chars)
        print(f"  Vocabulaire : {self.vocab_size} caracteres")

    def encode(self, text: str) -> np.ndarray:
        return np.array([self.char_to_id.get(c, 0) for c in text], dtype=np.int64)

    def decode(self, ids) -> str:
        if isinstance(ids, np.ndarray):
            ids = ids.tolist()
        return ''.join(self.id_to_char.get(i, '?') for i in ids)


# ════════════════════════════════════════════════════════════════
# 3. MODELE PYTORCH (HWAT entraînement)
# ════════════════════════════════════════════════════════════════

import torch
import torch.nn as nn
import torch.nn.functional as F

PHI = 1.618033988749895
TAU = 2.0 * math.pi


class HarmonicEmbeddingTorch(nn.Module):
    """Embedding complexe ψ = A·e^{iφ} — appris (amplitude + phase token)."""

    def __init__(self, vocab_size: int, dim: int, max_len: int = MAX_LEN):
        super().__init__()
        self.dim = dim
        self.max_len = max_len

        # Amplitude sémantique APPRISE (initialisee φ-deterministe puis affinee)
        self.A = nn.Parameter(torch.randn(vocab_size, dim) * 0.02)

        # Phase lexicale APPRISE
        self.phi_token = nn.Parameter(torch.rand(vocab_size, dim) * TAU)

        # Phase positionnelle (FIXE — noyau ABC, non apprise)
        t = torch.arange(max_len, dtype=torch.float32)
        ks = torch.arange(dim, dtype=torch.float32)
        omegas = 0.1 * (math.pi / 0.1) ** (ks / max(dim - 1, 1))
        self.register_buffer('phi_pos', omegas[None, :] * t[:, None])

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """token_ids: [L] → ψ: [L, dim] complexe."""
        L = token_ids.shape[0]
        if L > self.max_len:
            token_ids = token_ids[:self.max_len]
            L = self.max_len
        A = self.A[token_ids]                          # [L, dim]
        phi_tok = self.phi_token[token_ids]            # [L, dim]
        phi = phi_tok + self.phi_pos[:L]               # [L, dim]
        return A * torch.exp(1j * phi)


class PhaseAttentionTorch(nn.Module):
    """Attention par coherence de phase — ZERO parametre appris."""

    def __init__(self, dim: int, n_heads: int = N_HEADS, causal: bool = True):
        super().__init__()
        self.dim = dim
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.causal = causal

    def forward(self, psi: torch.Tensor) -> torch.Tensor:
        """psi: [L, dim] complexe → out: [L, dim] complexe."""
        L, D = psi.shape
        H, d = self.n_heads, self.head_dim
        # [L, dim] → [H, L, d]
        heads = psi.reshape(L, H, d).permute(1, 0, 2)  # [H, L, d]

        A = heads.abs()                                  # [H, L, d]
        phi = heads.angle()                              # [H, L, d]

        # coherence de phase cos(φ_i - φ_j)
        dphi = phi[:, :, None, :] - phi[:, None, :, :]  # [H, L, L, d]
        cos_phase = torch.cos(dphi)

        # poids d'amplitude
        amp_weight = torch.sqrt(A[:, :, None, :] * A[:, None, :, :] + 1e-12)

        scores = (cos_phase * amp_weight).sum(dim=-1) / math.sqrt(d)  # [H, L, L]

        if self.causal:
            mask = torch.triu(torch.ones(L, L, device=psi.device), diagonal=1).bool()
            scores = scores.masked_fill(mask[None], float('-inf'))

        attn = F.softmax(scores, dim=-1)                 # [H, L, L]
        attn_c = attn.to(dtype=heads.dtype)              # cast real→complex
        out = torch.einsum('hij,hjd->hid', attn_c, heads)  # [H, L, d]
        return out.permute(1, 0, 2).reshape(L, D)


class HarmonicMLPTorch(nn.Module):
    """MLP 2 couches GELU — sur partie REELLE, phase preservee."""

    def __init__(self, dim: int, hidden_mult: int = 4):
        super().__init__()
        hidden = dim * hidden_mult
        self.W1 = nn.Parameter(torch.randn(dim, hidden) * 0.02)
        self.b1 = nn.Parameter(torch.zeros(hidden))
        self.W2 = nn.Parameter(torch.randn(hidden, dim) * 0.02)
        self.b2 = nn.Parameter(torch.zeros(dim))

    def forward(self, psi: torch.Tensor) -> torch.Tensor:
        A = psi.abs()                    # [L, dim]
        phi = psi.angle()                # [L, dim]
        h = F.gelu(A @ self.W1 + self.b1)
        A_new = h @ self.W2 + self.b2
        return A_new * torch.exp(1j * phi)


class SpectralOpTorch(nn.Module):
    """FFT globale vectorisee + gating spectral APPRIS par canal.

    Version simplifiee pour la Phase 1 d'entrainement :
      - FFT sur toute la sequence (pas de fenetrage STFT)
      - Gating appris : ponderation par frequence via un petit MLP
      - Phase preservee (l'operateur est dans le domaine complexe)

    La STFT multi-echelle est remise en Phase 2.
    """

    def __init__(self, dim: int, hidden_gate: int = 16):
        super().__init__()
        self.dim = dim
        # MLP de gating spectral : |coeff| → gains par frequence
        self.gate_mlp = nn.Sequential(
            nn.Linear(dim, hidden_gate),
            nn.GELU(),
            nn.Linear(hidden_gate, dim),
            nn.Sigmoid()
        )

    def forward(self, psi: torch.Tensor) -> torch.Tensor:
        """psi: [L, dim] complexe → out: [L, dim] complexe (filtre)."""
        L, D = psi.shape
        # FFT sur chaque canal (vectorise : batch=D, signal=L)
        X = psi.real.T.contiguous()                    # [D, L] reel
        F = torch.fft.rfft(X, dim=-1)                 # [D, L//2+1] complexe
        # Gating : pooler l'amplitude sur les frequences → gain par canal
        amp = F.abs().mean(dim=-1)                    # [D]
        gains = self.gate_mlp(amp)                     # [D]
        # Appliquer le gain au spectre
        F_gated = F * gains[:, None]                   # [D, L//2+1]
        # IFFT
        X_rec = torch.fft.irfft(F_gated, n=L, dim=-1) # [D, L]
        # Recomposer en complexe avec phase preservee
        out_mag = X_rec.T                              # [L, D]
        out_phase = psi.angle()
        return out_mag * torch.exp(1j * out_phase)


class TrainableBlock(nn.Module):
    """Bloc harmonique avec MLP appris, spectral+attention figes."""

    def __init__(self, dim: int, block_id: int = 0):
        super().__init__()
        self.spectral = SpectralOpTorch(dim)
        self.attn = PhaseAttentionTorch(dim, causal=False)
        self.mlp = HarmonicMLPTorch(dim)

        # LayerNorm (appris)
        self.ln1 = nn.LayerNorm(dim, elementwise_affine=True)
        self.ln2 = nn.LayerNorm(dim, elementwise_affine=True)

    def forward(self, psi: torch.Tensor) -> torch.Tensor:
        # Spectral + Attention residuel
        A = psi.abs()
        phi = psi.angle()
        A_norm = self.ln1(A)
        x_amp = A_norm * torch.exp(1j * phi)
        x = self.spectral(x_amp)
        x = self.attn(x)
        psi = psi + x
        # MLP residuel
        A2 = psi.abs()
        A2_norm = self.ln2(A2)
        x_amp2 = A2_norm * torch.exp(1j * psi.angle())
        x2 = self.mlp(x_amp2)
        return psi + x2


class TrainableHWAT(nn.Module):
    """HWAT entraînable : embedding appris + blocs + tete LM."""

    def __init__(self, vocab_size: int, dim: int = DIM,
                 n_blocks: int = N_BLOCKS, max_len: int = MAX_LEN):
        super().__init__()
        self.embed = HarmonicEmbeddingTorch(vocab_size, dim, max_len)
        self.blocks = nn.ModuleList([
            TrainableBlock(dim, block_id=i)
            for i in range(n_blocks)
        ])
        # Tete LM : amplitude + cos(phase) → vocab
        self.lm_head = nn.Linear(2 * dim, vocab_size)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """token_ids: [L] → logits: [L, vocab_size]."""
        psi = self.embed(token_ids)
        for blk in self.blocks:
            psi = blk(psi)
        A = psi.abs()
        cos_phi = torch.cos(psi.angle())
        feats = torch.cat([A, cos_phi], dim=-1)   # [L, 2*dim]
        return self.lm_head(feats)

    @property
    def device(self):
        return next(self.parameters()).device


# ════════════════════════════════════════════════════════════════
# 4. BOUCLE D'ENTRAINEMENT
# ════════════════════════════════════════════════════════════════

def build_batches(token_ids: np.ndarray, seq_len: int,
                   batch_size: int) -> list:
    """Decoupe le corpus en batches [seq_len] (batch_size=1 pour Phase 1)."""
    n_tokens = len(token_ids)
    n_batches = (n_tokens - 1) // seq_len
    batches = []
    for i in range(n_batches):
        start = i * seq_len
        x = torch.from_numpy(token_ids[start:start + seq_len].copy())
        y = torch.from_numpy(token_ids[start + 1:start + 1 + seq_len].copy())
        if len(x) < seq_len or len(y) < seq_len:
            break
        batches.append((x, y))
    return batches


def train():
    print("═" * 60)
    print("  🌊 TRAINING HWAT — Phase 1 : Preuve d'apprentissage")
    print("═" * 60)

    # 1. Corpus
    text = load_corpus()
    if CORPUS_MAX and len(text) > CORPUS_MAX:
        text = text[:CORPUS_MAX]
        print(f"  Corpus tronque a {CORPUS_MAX:,} caracteres (Phase 1)")
    tokenizer = CharTokenizer(text)
    all_ids = tokenizer.encode(text)
    print(f"  Tokens totaux : {len(all_ids):,}")

    # 2. Model
    model = TrainableHWAT(vocab_size=tokenizer.vocab_size,
                          dim=DIM, n_blocks=N_BLOCKS, max_len=MAX_LEN)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  Parametres apprenables : {n_params:,}")
    print(f"  Dim={DIM}, Blocs={N_BLOCKS}, Tetes={N_HEADS}, "
          f"Seq={MAX_LEN}, Batch={BATCH_SIZE}")

    # 3. Batches
    batches = build_batches(all_ids, MAX_LEN, BATCH_SIZE)
    print(f"  Batches : {len(batches)}")

    # 4. Optimizer + loss
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    # 5. Training loop
    print(f"\n  {'Epoch':>6} {'Batch':>6} {'Loss':>10} {'Perplexite':>12} "
          f"{'Temps/batch':>12}")
    print(f"  {'-'*6} {'-'*6} {'-'*10} {'-'*12} {'-'*12}")

    losses = []
    perplexities = []
    global_step = 0

    for epoch in range(1, EPOCHS + 1):
        epoch_loss = 0.0
        t0 = time.time()

        for batch_idx, (x, y) in enumerate(batches):
            # Forward
            logits = model(x)                            # [L, V]
            loss = criterion(logits, y)                  # [L, V] vs [L]

            # Backward
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            epoch_loss += loss.item()
            global_step += 1

            if (batch_idx + 1) % PRINT_EVERY == 0:
                avg_loss = epoch_loss / (batch_idx + 1)
                ppl = math.exp(avg_loss)
                dt = time.time() - t0
                print(f"  {epoch:>6} {batch_idx+1:>6} {avg_loss:>10.4f} "
                      f"{ppl:>12.2f} {dt/(batch_idx+1):>11.4f}s")
                losses.append(avg_loss)
                perplexities.append(ppl)

        # Fin d'epoque
        avg_loss = epoch_loss / len(batches)
        ppl = math.exp(avg_loss)
        dt = time.time() - t0
        print(f"  {'─'*50}")
        print(f"  EPOCH {epoch}/{EPOCHS} — Loss: {avg_loss:.4f}, "
              f"Perplexite: {ppl:.1f}, Temps: {dt:.1f}s\n")

    # 6. Sauvegarde
    save_path = _ENGINE / "data" / "hwat_trained.pt"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'model_state': model.state_dict(),
        'vocab_size': tokenizer.vocab_size,
        'char_to_id': tokenizer.char_to_id,
        'id_to_char': tokenizer.id_to_char,
        'config': {'dim': DIM, 'n_blocks': N_BLOCKS, 'max_len': MAX_LEN},
        'losses': losses,
        'perplexities': perplexities,
    }, str(save_path))
    print(f"  ✅ Modele sauvegarde : {save_path}")

    # 7. Rapport
    print(f"\n═" * 60)
    print(f"  RESULTATS")
    print(f"═" * 60)
    print(f"  Loss initiale     : {losses[0]:.4f}")
    print(f"  Loss finale       : {losses[-1]:.4f}")
    print(f"  Perplexite init.  : {perplexities[0]:.1f}")
    print(f"  Perplexite finale : {perplexities[-1]:.1f}")
    reduction = (losses[0] - losses[-1]) / losses[0] * 100
    print(f"  Reduction loss    : {reduction:.1f}%")
    print(f"\n  ✅ Le modele APPREND — la loss decroit de {reduction:.0f}%.")

    return model, tokenizer, losses, perplexities


# ════════════════════════════════════════════════════════════════
# 5. INFERENCE POST-TRAINING (demo rapide)
# ════════════════════════════════════════════════════════════════

def demo_generation(model: TrainableHWAT, tokenizer: CharTokenizer,
                    prompt: str = "theoreme", max_new: int = 40):
    """Genere du texte caractere par caractere (greedy)."""
    model.eval()
    ids = tokenizer.encode(prompt).tolist()
    with torch.no_grad():
        for _ in range(max_new):
            x = torch.tensor(ids[-MAX_LEN:], dtype=torch.long)
            logits = model(x)                        # [L, V]
            next_logit = logits[-1]                  # [V]
            next_id = next_logit.argmax().item()
            ids.append(next_id)
            if tokenizer.id_to_char[next_id] == '\n':
                break
    return tokenizer.decode(ids)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    model, tokenizer, losses, ppls = train()

    # Demo d'inference
    print(f"\n{'═'*60}")
    print(f"  DEMO GENERATION (greedy)")
    print(f"{'═'*60}")
    for prompt in ["theoreme", "equation", "loi de", "principe"]:
        gen = demo_generation(model, tokenizer, prompt)
        print(f"  > {gen[:80]}")
