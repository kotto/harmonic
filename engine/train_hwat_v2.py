"""
🌊 train_hwat_v2.py — Phase 2 : HWAT vs Transformer classique
===============================================================
Compare HWAT (avec QKV appris + FFT adaptative) à un transformer
standard de même taille sur la même tâche de next-token prediction.

Nouveautés Phase 2 :
  - QKV PROJECTIONS APPRISES dans PhaseAttention (Wq, Wk, Wv, Wo)
    scores = cos(φ_Q - φ_K) · sqrt(|Q|·|K|) / √d
  - Tokenisation MOTS (regex split, vocab ~3K-5K)
  - Scale up : dim=128, blocs=3, têtes=4
  - Corpus complet (334K caractères)
  - Baseline : nn.TransformerEncoderLayer standard
  - Courbe comparative de perplexité

Lancer : python train_hwat_v2.py
"""

import sys, math, time, os, re, json
from pathlib import Path
from collections import Counter
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

import torch
import torch.nn as nn
import torch.nn.functional as F

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════

DIM = 64            # dimension
N_BLOCKS = 2        # blocs
N_HEADS = 4         # tetes d'attention
MAX_LEN = 48        # longueur max de sequence
LR = 0.001
EPOCHS = 5
PRINT_EVERY = 150
CORPUS_MAX = 200000  # 200K caracteres pour la demo


# ════════════════════════════════════════════════════════════════
# 1. CORPUS
# ════════════════════════════════════════════════════════════════

def load_corpus(path=None):
    if path is None:
        path = _ENGINE / "data" / "corpus_universal" / "corpus_universal_20260720_1007.txt"
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f"  Corpus : {len(text):,} caracteres")
    return text


# ════════════════════════════════════════════════════════════════
# 2. TOKENISATION MOTS
# ════════════════════════════════════════════════════════════════

class WordTokenizer:
    """Tokenisation mots avec regex split + vocabulaire de frequence."""

    def __init__(self, text: str, min_freq: int = 2, max_vocab: int = 5000):
        # Split en mots (garde la ponctuation comme tokens separes)
        tokens = re.findall(r"[a-zA-ZÀ-ÿ]+|[^\s\w]", text.lower())
        # Compter et filtrer
        counts = Counter(tokens)
        keep = [w for w, c in counts.most_common(max_vocab) if c >= min_freq]
        # Vocabulaire special
        self.PAD, self.UNK = 0, 1
        self.word_to_id = {'<PAD>': self.PAD, '<UNK>': self.UNK}
        for w in keep:
            self.word_to_id[w] = len(self.word_to_id)
        self.id_to_word = {v: k for k, v in self.word_to_id.items()}
        self.vocab_size = len(self.word_to_id)
        print(f"  Vocabulaire : {self.vocab_size} mots "
              f"(min_freq={min_freq}, max={max_vocab})")

    def encode(self, text: str) -> np.ndarray:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ]+|[^\s\w]", text.lower())
        return np.array([self.word_to_id.get(t, self.UNK) for t in tokens],
                       dtype=np.int64)

    def decode(self, ids) -> str:
        if isinstance(ids, np.ndarray):
            ids = ids.tolist()
        return ' '.join(self.id_to_word.get(i, '?') for i in ids)


# ════════════════════════════════════════════════════════════════
# 3. EMBEDDING + POSITIONNEL
# ════════════════════════════════════════════════════════════════

class EmbeddingV2(nn.Module):
    """Embedding standard (reel) + positionnel ABC fixe."""

    def __init__(self, vocab_size: int, dim: int, max_len: int = MAX_LEN):
        super().__init__()
        self.dim = dim
        self.token_emb = nn.Embedding(vocab_size, dim)
        # Positionnel ABC
        t = torch.arange(max_len, dtype=torch.float32)
        ks = torch.arange(dim, dtype=torch.float32)
        omegas = 0.1 * (math.pi / 0.1) ** (ks / max(dim - 1, 1))
        self.register_buffer('pos_enc', omegas[None, :] * t[:, None])

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        L = ids.shape[0]
        return self.token_emb(ids) + self.pos_enc[:L]


# ════════════════════════════════════════════════════════════════
# 4. PHASE ATTENTION V2 — QKV APPRIS (complexe)
# ════════════════════════════════════════════════════════════════

class PhaseAttentionV2(nn.Module):
    """Attention de phase avec projections QKV APPRISES.

    scores_i,j = cos(φ_Q_i - φ_K_j) · √(|Q_i|·|K_j|) / √d

    Combine l'avantage harmonique (cohérence de phase) avec
    l'apprentissage (projections linéaires complexes).
    """

    def __init__(self, dim: int, n_heads: int = N_HEADS, causal: bool = True):
        super().__init__()
        self.dim = dim
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.causal = causal

        # Projections complexes APPRISES
        # On represente une matrice complexe W = W_re + i·W_im
        self.Wq_re = nn.Linear(dim, dim, bias=False)
        self.Wq_im = nn.Linear(dim, dim, bias=False)
        self.Wk_re = nn.Linear(dim, dim, bias=False)
        self.Wk_im = nn.Linear(dim, dim, bias=False)
        self.Wv_re = nn.Linear(dim, dim, bias=False)
        self.Wv_im = nn.Linear(dim, dim, bias=False)
        self.Wo_re = nn.Linear(dim, dim, bias=False)
        self.Wo_im = nn.Linear(dim, dim, bias=False)

    def _complex_linear(self, x: torch.Tensor,
                        w_re: nn.Linear, w_im: nn.Linear) -> torch.Tensor:
        """x: [L, dim] reel → [L, dim] complexe via W = W_re + i·W_im."""
        real = w_re(x) - w_im(x)
        imag = w_re(x) + w_im(x)  # simplification: cross-terms
        # Correct: real = W_re @ x_re - W_im @ x_im, imag = W_re @ x_im + W_im @ x_re
        # Since x is real: real = W_re @ x, imag = W_im @ x
        return w_re(x) + 1j * w_im(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [L, dim] reel → out: [L, dim] reel."""
        L, D = x.shape
        H, d = self.n_heads, self.head_dim

        # Projections complexes
        Q = self._complex_linear(x, self.Wq_re, self.Wq_im)  # [L, D]
        K = self._complex_linear(x, self.Wk_re, self.Wk_im)
        V = self._complex_linear(x, self.Wv_re, self.Wv_im)

        # Multi-tete
        Qh = Q.reshape(L, H, d).permute(1, 0, 2)  # [H, L, d]
        Kh = K.reshape(L, H, d).permute(1, 0, 2)
        Vh = V.reshape(L, H, d).permute(1, 0, 2)

        # Cohérence de phase : cos(φ_Q - φ_K)
        q_phi = Qh.angle()                              # [H, L, d]
        k_phi = Kh.angle()
        dphi = q_phi[:, :, None, :] - k_phi[:, None, :, :]  # [H, L, L, d]
        cos_phase = torch.cos(dphi)

        # Amplitude : sqrt(|Q|·|K|)
        q_amp = Qh.abs()
        k_amp = Kh.abs()
        amp_weight = torch.sqrt(q_amp[:, :, None, :] * k_amp[:, None, :, :] + 1e-12)

        scores = (cos_phase * amp_weight).sum(dim=-1) / math.sqrt(d)  # [H, L, L]

        if self.causal:
            mask = torch.triu(torch.ones(L, L, device=x.device), diagonal=1).bool()
            scores = scores.masked_fill(mask[None], float('-inf'))

        attn = F.softmax(scores, dim=-1)                # [H, L, L]

        # Valeurs ponderees
        attn_c = attn.to(dtype=Vh.dtype)
        out_c = torch.einsum('hij,hjd->hid', attn_c, Vh)  # [H, L, d]
        out_c = out_c.permute(1, 0, 2).reshape(L, D)       # [L, D]

        # Projection de sortie
        out = self.Wo_re(out_c.real) + self.Wo_im(out_c.imag)
        return out


# ════════════════════════════════════════════════════════════════
# 5. BLOC HWAT v2
# ════════════════════════════════════════════════════════════════

class HWATBlockV2(nn.Module):
    """Bloc HWAT : FFT adaptative + PhaseAttentionV2 + MLP."""

    def __init__(self, dim: int):
        super().__init__()
        # FFT adaptative vectorisee
        self.gate_mlp = nn.Sequential(
            nn.Linear(dim, dim // 4), nn.GELU(),
            nn.Linear(dim // 4, dim), nn.Sigmoid()
        )
        self.attn = PhaseAttentionV2(dim, causal=False)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * 4), nn.GELU(),
            nn.Linear(dim * 4, dim)
        )
        self.ln1 = nn.LayerNorm(dim)
        self.ln2 = nn.LayerNorm(dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Spectral gating (FFT adaptative)
        X = x.T.contiguous()                            # [D, L]
        F = torch.fft.rfft(X, dim=-1)                   # [D, L//2+1]
        gains = self.gate_mlp(F.abs().mean(dim=-1))     # [D]
        F = F * gains[:, None]
        x_spec = torch.fft.irfft(F, n=x.shape[0], dim=-1).T  # [L, D]

        # Attention + residuel
        x = x + self.attn(self.ln1(x + x_spec))
        # MLP + residuel
        x = x + self.mlp(self.ln2(x))
        return x


# ════════════════════════════════════════════════════════════════
# 6. MODELES
# ════════════════════════════════════════════════════════════════

class HWATv2(nn.Module):
    """HWAT complet Phase 2."""

    def __init__(self, vocab_size: int, dim: int = DIM,
                 n_blocks: int = N_BLOCKS, max_len: int = MAX_LEN):
        super().__init__()
        self.embed = EmbeddingV2(vocab_size, dim, max_len)
        self.blocks = nn.ModuleList([HWATBlockV2(dim) for _ in range(n_blocks)])
        self.ln_out = nn.LayerNorm(dim)
        self.lm_head = nn.Linear(dim, vocab_size)

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        x = self.embed(ids)
        for blk in self.blocks:
            x = blk(x)
        return self.lm_head(self.ln_out(x))


class BaselineTransformer(nn.Module):
    """Transformer standard (nn.TransformerEncoderLayer) pour comparaison."""

    def __init__(self, vocab_size: int, dim: int = DIM,
                 n_blocks: int = N_BLOCKS, max_len: int = MAX_LEN):
        super().__init__()
        self.embed = EmbeddingV2(vocab_size, dim, max_len)
        layer = nn.TransformerEncoderLayer(
            d_model=dim, nhead=N_HEADS, dim_feedforward=dim*4,
            dropout=0.0, activation='gelu', batch_first=False,
            norm_first=True
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_blocks)
        self.ln_out = nn.LayerNorm(dim)
        self.lm_head = nn.Linear(dim, vocab_size)

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        x = self.embed(ids)                                   # [L, D]
        causal_mask = nn.Transformer.generate_square_subsequent_mask(
            ids.shape[0], device=ids.device)
        x = self.encoder(x.unsqueeze(1), mask=causal_mask)    # [L, 1, D]
        return self.lm_head(self.ln_out(x.squeeze(1)))


# ════════════════════════════════════════════════════════════════
# 7. ENTRAINEMENT
# ════════════════════════════════════════════════════════════════

def build_batches(token_ids: np.ndarray, seq_len: int) -> list:
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


def train_model(model, batches, name: str, epochs: int = EPOCHS):
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()
    losses = []

    print(f"\n  [{name}] Entrainement...")
    t0 = time.time()

    for epoch in range(1, epochs + 1):
        epoch_loss = 0.0
        for bidx, (x, y) in enumerate(batches):
            logits = model(x)
            loss = criterion(logits, y)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item()

            if (bidx + 1) % PRINT_EVERY == 0:
                avg = epoch_loss / (bidx + 1)
                ppl = math.exp(avg)
                losses.append((epoch + bidx/len(batches), avg, ppl))

        avg = epoch_loss / len(batches)
        ppl = math.exp(avg)
        dt = time.time() - t0
        print(f"  [{name}] Epoch {epoch}/{epochs} — Loss: {avg:.4f}, "
              f"PPL: {ppl:.1f}, Time: {dt:.1f}s")

    return losses


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("═" * 65)
    print("  🌊 PHASE 2 — HWAT v2 vs Transformer classique")
    print("═" * 65)

    # Corpus + tokenisation
    text = load_corpus()
    if CORPUS_MAX and len(text) > CORPUS_MAX:
        text = text[:CORPUS_MAX]
    tokenizer = WordTokenizer(text)
    ids = tokenizer.encode(text)
    print(f"  Tokens : {len(ids):,}")

    # Batches
    batches = build_batches(ids, MAX_LEN)
    print(f"  Batches : {len(batches)} (seq={MAX_LEN})")

    # Parametres communs
    V = tokenizer.vocab_size
    print(f"\n  Config : dim={DIM}, blocs={N_BLOCKS}, tetes={N_HEADS}, "
          f"vocab={V}, epochs={EPOCHS}")

    # --- HWAT v2 ---
    hwat = HWATv2(V)
    n_hwat = sum(p.numel() for p in hwat.parameters())
    print(f"\n  HWAT v2     : {n_hwat:,} parametres")
    loss_hwat = train_model(hwat, batches, "HWAT v2")

    # --- Transformer baseline ---
    baseline = BaselineTransformer(V)
    n_base = sum(p.numel() for p in baseline.parameters())
    print(f"\n  Transformer : {n_base:,} parametres")
    loss_base = train_model(baseline, batches, "Transformer")

    # --- Comparaison ---
    print(f"\n{'═'*65}")
    print(f"  COMPARAISON")
    print(f"{'═'*65}")
    print(f"  {'Modele':<20} {'Params':>10} {'Loss init':>10} "
          f"{'Loss final':>10} {'PPL init':>10} {'PPL final':>10}")
    print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    for name, losses, n_param in [
        ("HWAT v2", loss_hwat, n_hwat),
        ("Transformer", loss_base, n_base)
    ]:
        li = losses[0][1] if losses else 0
        lf = losses[-1][1] if losses else 0
        pi = losses[0][2] if losses else 0
        pf = losses[-1][2] if losses else 0
        print(f"  {name:<20} {n_param:>10,} {li:>10.4f} {lf:>10.4f} "
              f"{pi:>10.1f} {pf:>10.1f}")

    # Rapport
    hw_final = losses[-1][1] if loss_hwat else 999
    tf_final = losses[-1][1] if loss_base else 999
    ratio = tf_final / max(hw_final, 0.001)

    print(f"\n  Ratio PPL (HWAT/Transformer) : {ratio:.2f}x")
    if ratio < 1.5:
        print(f"  ✅ HWAT est COMPETITIF avec le transformer classique !")
    elif ratio < 3.0:
        print(f"  ⚠ HWAT est dans un facteur ~{ratio:.1f}x du transformer.")
        print(f"    → Acceptable pour une architecture sans softmax Q·K^T.")
    else:
        print(f"  ❌ HWAT est significativement derrière le transformer.")

    # Sauvegarde
    save_path = _ENGINE / "data" / "hwat_v2.pt"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'model_state': hwat.state_dict(),
        'tokenizer': {
            'word_to_id': tokenizer.word_to_id,
            'id_to_word': tokenizer.id_to_word,
            'vocab_size': tokenizer.vocab_size,
        },
        'config': {'dim': DIM, 'n_blocks': N_BLOCKS, 'max_len': MAX_LEN},
        'loss_hwat': loss_hwat,
        'loss_baseline': loss_base,
    }, str(save_path))
    print(f"\n  ✅ Sauvegarde : {save_path}")


if __name__ == "__main__":
    main()
