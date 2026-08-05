"""
Benchmark HWAT — Comparaison des architectures harmoniques
============================================================
Mesure la récupération de sélectivité fine apportée par HWAT par
rapport à l'architecture actuelle (FFT globale, harmonic_engine.py).

Trois configurations comparées sur 3 métriques de sélectivité :
  - BASELINE : FFT globale (1 spectre pour toute la séquence)
  - STFT     : STFT multi-échelle seule (piste A du PROPOSAL)
  - HWAT     : STFT + attention de phase + MLP (pistes A+B+C+D combinées)

Métriques :
  M1. Sélectivité positionnelle : sim(token, même_token @ autre_pos)
      → Doit être faible (sinon le modèle confond l'ordre des mots)
  M2. Sélectivité lexicale       : sim(token_a, token_b) pour a≠b
      → Doit être faible (sinon le modèle confond les mots)
  M3. Sélectivité anaphorique   : capacité à distinguer 2 occurrences
      du même mot à des rôles syntaxiques différents
      → Doit être faible (problème exact de l'IA harmonique actuelle)

Hypothèse du PROPOSAL : BASELINE perd la sélectivité (Gabor),
                        HWAT la récupère via l'attention de phase.

Lancer : python benchmark_hwat.py
"""

import sys
import math
import numpy as np
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harmonic_transformer import (
    HWAT, HarmonicEmbedding, SpectralOperator, PhaseAttention, PHI, TAU
)
from adaptive_spectral_operator import AdaptiveSpectralOperator


# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════

VOCAB = 500
DIM = 64
N_BLOCKS = 3
SEQ_LEN = 64
N_TRIALS = 50    # paires aléatoires testées par métrique (suffisant pour μ fiable)

# Type du bloc à utiliser dans HWAT (fixe ou adaptatif)
BLOCK_TYPE = "adaptive"  # "fixed" | "adaptive"


# ════════════════════════════════════════════════════════════════
# UTILITAIRES
# ════════════════════════════════════════════════════════════════

def _cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-30 or nb < 1e-30:
        return 0.0
    return float(np.abs(np.vdot(a, b)) / (na * nb))


# Utilitaires déterministes locaux (pour AdaptiveBlock)
def _bench_fnv1a_32(s: str) -> int:
    h = 2166136261
    for ch in s.encode('utf-8'):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _bench_det_normal(d: int, seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    return rng.randn(d).astype(np.float64)


# ════════════════════════════════════════════════════════════════
# CONFIGURATIONS À COMPARER
# ════════════════════════════════════════════════════════════════

class BaselineGlobalFFT:
    """Architecture actuelle (harmonic_engine.py : FFT globale sur la séquence).

    Calcule UNE FFT pour toute la séquence puis projette sur chaque token.
    C'est exactement ce qui perd la sélectivité (théorème de Gabor).
    """

    def __init__(self, vocab: int, dim: int):
        self.vocab = vocab
        self.dim = dim
        # Embedding plat : pas de phase positionnelle (comme l'ancien code)
        sigma = 1.0 / math.sqrt(dim)
        self.A = np.zeros((vocab, dim))
        for t in range(vocab):
            rng = np.random.RandomState(t * 2654435761 % 2**31)
            v = rng.randn(dim) * sigma
            self.A[t] = v / np.linalg.norm(v)

    def embed(self, tokens: np.ndarray) -> np.ndarray:
        """FFT globale → SPECTRE PARTAGÉ entre tous les tokens.

        Modélise exactement l'architecture actuelle (harmonic_engine.py) :
        une seule FFT pour toute la séquence, puis features spectrales
        broadcastées → tous les tokens voient le MÊME vecteur.
        C'est ce qui détruit la sélectivité positionnelle.
        """
        L = len(tokens)
        # 1. Embedding plat par token (pas de phase positionnelle)
        x = self.A[tokens]                                # [L, dim] réel
        # 2. UNE FFT globale (vecteur spectral unique pour toute la séquence)
        X = np.fft.rfft(x, axis=0)                        # [L//2+1, dim]
        # 3. Features spectrales agrégées (centroide spectral par dim)
        #    → 1 vecteur partagé, broadcasté sur tous les tokens
        shared = X.mean(axis=0)                           # [dim] complexe
        return np.tile(shared, (L, 1))                    # [L, dim] identique


class STFTOnly:
    """STFT multi-échelle seule (piste A) — sans attention."""

    def __init__(self, vocab: int, dim: int):
        self.emb = HarmonicEmbedding(vocab, dim=dim, max_len=SEQ_LEN * 2)
        self.spectral = SpectralOperator(dim, window_sizes=(16, 32, 64))

    def embed(self, tokens: np.ndarray) -> np.ndarray:
        psi = self.emb(tokens)
        return self.spectral.forward(psi)


class HWATConfig:
    """HWAT complet (pistes A+B+C+D combinées)."""

    def __init__(self, vocab: int, dim: int, n_blocks: int):
        self.model = HWAT(vocab_size=vocab, dim=dim,
                          n_blocks=n_blocks, n_heads=4,
                          max_len=SEQ_LEN * 2,
                          window_sizes=(16, 32, 64))

    def embed(self, tokens: np.ndarray) -> np.ndarray:
        return self.model.deep_embed(tokens)


class HWATEmbeddingOnly:
    """HWAT embedding brut (HarmonicEmbedding seul) — pour isoler le
    potentiel de sélectivité avant que les blocs résiduels ne l'atténuent."""

    def __init__(self, vocab: int, dim: int):
        self.model = HWAT(vocab_size=vocab, dim=dim, n_blocks=0,
                          max_len=SEQ_LEN * 2)

    def embed(self, tokens: np.ndarray) -> np.ndarray:
        return self.model.embed(tokens)


class AdaptiveBlock:
    """Un bloc harmonique ADAPTATIF (Fourier apprise, pas STFT fixe).

    Reproduction minimale de HarmonicBlock mais avec
    AdaptiveSpectralOperator au lieu de SpectralOperator.
    """

    def __init__(self, dim: int, n_heads: int = 4,
                 window_sizes: Tuple[int, ...] = (16, 32, 64),
                 hidden_mult: int = 4, block_id: int = 0):
        self.spectral = AdaptiveSpectralOperator(dim, window_sizes,
                                                  layer_id=block_id)
        self.attn = PhaseAttention(dim, n_heads=n_heads)
        from harmonic_transformer import HarmonicMLP
        self.mlp = HarmonicMLP(dim, hidden_mult=hidden_mult,
                               seed_salt=block_id)
        # LayerNorm déterministe
        s = _bench_fnv1a_32(f"adap_ln_{block_id}")
        self.ln_gamma = np.ones(dim) + 0.01 * _bench_det_normal(dim, s)
        self.ln_beta = _bench_det_normal(dim, _bench_fnv1a_32(
            f"adap_ln_b_{block_id}")) * 0.01

    def _layernorm_amp(self, psi: np.ndarray) -> np.ndarray:
        A = np.abs(psi)
        mu = A.mean(axis=-1, keepdims=True)
        sigma = A.std(axis=-1, keepdims=True) + 1e-6
        A_norm = (A - mu) / sigma * self.ln_gamma + self.ln_beta
        return A_norm * np.exp(1j * np.angle(psi))

    def forward(self, psi: np.ndarray) -> np.ndarray:
        x = self._layernorm_amp(psi)
        x = self.spectral.forward(x)
        x = self.attn.forward(x)
        psi = psi + x
        x = self._layernorm_amp(psi)
        x = self.mlp.forward(x)
        psi = psi + x
        return psi


class HWATAdaptiveConfig:
    """HWAT avec blocs ADAPTATIFS (piste B — filtre adaptatif).

    Chaque bloc utilise AdaptiveSpectralOperator qui apprend
    sa propre base de Fourier en fonction du contenu.
    """

    def __init__(self, vocab: int, dim: int, n_blocks: int,
                 max_len: int = SEQ_LEN * 2):
        self.emb = HarmonicEmbedding(vocab, dim=dim, max_len=max_len)
        self.blocks = [
            AdaptiveBlock(dim, n_heads=4,
                          window_sizes=(16, 32, 64),
                          block_id=i)
            for i in range(n_blocks)
        ]

    def embed(self, tokens: np.ndarray) -> np.ndarray:
        psi = self.emb(tokens)
        for blk in self.blocks:
            psi = blk.forward(psi)
        return psi


# ════════════════════════════════════════════════════════════════
# MÉTRIQUES DE SÉLECTIVITÉ
# ════════════════════════════════════════════════════════════════

def metric_positional(cfg, rng: np.random.RandomState) -> float:
    """M1. sim(token @ pos i, même token @ pos j), i≠j. Plus bas = mieux."""
    sims = []
    for _ in range(N_TRIALS):
        tok = rng.randint(0, VOCAB)
        i, j = rng.randint(0, SEQ_LEN, 2)
        if i == j:
            continue
        seq_i = np.zeros(SEQ_LEN, dtype=int)
        seq_i[i] = tok
        seq_j = np.zeros(SEQ_LEN, dtype=int)
        seq_j[j] = tok
        a = cfg.embed(seq_i)[i]
        b = cfg.embed(seq_j)[j]
        sims.append(_cos_sim(a, b))
    return float(np.mean(sims))


def metric_lexical(cfg, rng: np.random.RandomState) -> float:
    """M2. sim(token_a, token_b) à la même position. Plus bas = mieux."""
    sims = []
    for _ in range(N_TRIALS):
        a_tok, b_tok = rng.randint(0, VOCAB, 2)
        if a_tok == b_tok:
            continue
        pos = rng.randint(0, SEQ_LEN)
        seq_a = np.zeros(SEQ_LEN, dtype=int)
        seq_a[pos] = a_tok
        seq_b = np.zeros(SEQ_LEN, dtype=int)
        seq_b[pos] = b_tok
        a = cfg.embed(seq_a)[pos]
        b = cfg.embed(seq_b)[pos]
        sims.append(_cos_sim(a, b))
    return float(np.mean(sims))


def metric_anaphoric(cfg, rng: np.random.RandomState) -> float:
    """M3. 2 occurrences du même mot à des positions distinctes,
    dans une phrase bruitée. Le modèle doit-il les distinguer ?

    C'est le test clé : un LLM classique les distingue (rôles syntaxiques),
    une FFT globale ne le peut PAS.
    Plus bas = mieux.
    """
    sims = []
    for _ in range(N_TRIALS):
        tok = rng.randint(0, VOCAB)
        # Phrase : tokens aléatoires sauf 2 occurrences de `tok`
        seq = rng.randint(0, VOCAB, SEQ_LEN)
        i, j = rng.randint(0, SEQ_LEN, 2)
        if i == j:
            continue
        seq[i] = tok
        seq[j] = tok
        emb = cfg.embed(seq)
        sims.append(_cos_sim(emb[i], emb[j]))
    return float(np.mean(sims))


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("═" * 70)
    print("  BENCHMARK — Sélectivité fine : FFT globale vs STFT vs HWAT")
    print("═" * 70)
    print(f"  Vocab={VOCAB}, dim={DIM}, blocs={N_BLOCKS}, "
          f"seq={SEQ_LEN}, trials/métrique={N_TRIALS}\n")

    rng = np.random.RandomState(2026)

    configs = {
        "BASELINE (FFT globale) ": BaselineGlobalFFT(VOCAB, DIM),
        "STFT multi-échelle    ": STFTOnly(VOCAB, DIM),
        "HWAT embedding brut   ": HWATEmbeddingOnly(VOCAB, DIM),
        "HWAT blocs FIXES      ": HWATConfig(VOCAB, DIM, N_BLOCKS),
        "HWAT blocs ADAPTATIFS ": HWATAdaptiveConfig(VOCAB, DIM, N_BLOCKS),
    }

    # Header
    print(f"  {'Configuration':<25} {'M1 Pos':>10} {'M2 Lex':>10} {'M3 Ana':>10}  Verdict")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10}  {'-'*20}")

    results = {}
    for name, cfg in configs.items():
        m1 = metric_positional(cfg, rng)
        m2 = metric_lexical(cfg, rng)
        m3 = metric_anaphoric(cfg, rng)
        # Verdict : sélectivité "bonne" si toutes < 0.5
        ok = (m1 < 0.5) and (m2 < 0.5) and (m3 < 0.5)
        verdict = "✅ SELECTIF" if ok else "⚠ PARTIEL"
        results[name] = (m1, m2, m3, verdict)
        print(f"  {name:<25} {m1:>10.3f} {m2:>10.3f} {m3:>10.3f}  {verdict}")

    # Analyse comparative
    print("\n" + "─" * 70)
    print("  ANALYSE")
    print("─" * 70)
    base = results["BASELINE (FFT globale) "]
    emb = results["HWAT embedding brut   "]
    hwat_fixed = results["HWAT blocs FIXES      "]
    hwat_adapt = results["HWAT blocs ADAPTATIFS "]
    print(f"  • Sélectivité positionnelle : "
          f"FFT {base[0]:.3f} → Emb {emb[0]:.3f} → "
          f"BlocsFIXES {hwat_fixed[0]:.3f} → BlocsADAPT {hwat_adapt[0]:.3f}")
    print(f"  • Sélectivité lexicale      : "
          f"FFT {base[1]:.3f} → Emb {emb[1]:.3f} → "
          f"BlocsFIXES {hwat_fixed[1]:.3f} → BlocsADAPT {hwat_adapt[1]:.3f}")
    print(f"  • Sélectivité anaphorique   : "
          f"FFT {base[2]:.3f} → Emb {emb[2]:.3f} → "
          f"BlocsFIXES {hwat_fixed[2]:.3f} → BlocsADAPT {hwat_adapt[2]:.3f}")

    # Gains relatifs de l'adaptatif par rapport au fixe
    gain_pos = (emb[0] / max(hwat_adapt[0], 1e-6)) / (emb[0] / max(hwat_fixed[0], 1e-6))
    gain_lex = (emb[1] / max(hwat_adapt[1], 1e-6)) / (emb[1] / max(hwat_fixed[1], 1e-6))
    gain_ana = (emb[2] / max(hwat_adapt[2], 1e-6)) / (emb[2] / max(hwat_fixed[2], 1e-6))
    print(f"\n  Gain ADAPTATIF / FIXE (préservation de la sélectivité) :")
    print(f"    Positionnel : ×{gain_pos:.2f}")
    print(f"    Lexical     : ×{gain_lex:.2f}")
    print(f"    Anaphorique : ×{gain_ana:.2f}")

    print("\n  Conclusion (honnête) :")
    improved_all = (hwat_adapt[0] < hwat_fixed[0] and
                    hwat_adapt[1] < hwat_fixed[1] and
                    hwat_adapt[2] < hwat_fixed[2])
    fully_solved = (hwat_adapt[0] < 0.5 and hwat_adapt[1] < 0.5 and
                    hwat_adapt[2] < 0.5)
    if improved_all and fully_solved:
        print("  ✅ L'opérateur adaptatif résout PLEINEMENT le problème !")
    elif improved_all:
        print("  ✅ L'opérateur adaptatif PRÉSERVE mieux la sélectivité")
        print(f"    que les blocs fixes sur TOUTES les métriques.")
        print(f"    → L'hypothèse du PROPOSAL est confirmée : apprendre la base")
        print(f"      de Fourier en fonction du contexte est SUPÉRIEUR à une")
        print(f"      STFT à fenêtres fixes.")
    elif gain_pos > 1.0 or gain_lex > 1.0 or gain_ana > 1.0:
        print("  ⚠ L'adaptatif améliore certaines métriques mais pas toutes.")
    else:
        print("  ❌ L'opérateur adaptatif dégrade la sélectivité.")

    print("\n" + "═" * 70)


if __name__ == "__main__":
    main()
