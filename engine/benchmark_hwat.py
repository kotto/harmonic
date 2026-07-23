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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harmonic_transformer import (
    HWAT, HarmonicEmbedding, SpectralOperator, PhaseAttention, PHI, TAU
)


# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════

VOCAB = 500
DIM = 64
N_BLOCKS = 3
SEQ_LEN = 64
N_TRIALS = 200   # paires aléatoires testées par métrique


# ════════════════════════════════════════════════════════════════
# UTILITAIRES
# ════════════════════════════════════════════════════════════════

def _cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-30 or nb < 1e-30:
        return 0.0
    return float(np.abs(np.vdot(a, b)) / (na * nb))


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
        "HWAT complet (N blocs)": HWATConfig(VOCAB, DIM, N_BLOCKS),
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
    hwat = results["HWAT complet (N blocs)"]
    print(f"  • Sélectivité positionnelle : "
          f"FFT {base[0]:.3f} → Emb {emb[0]:.3f} → HWAT {hwat[0]:.3f}")
    print(f"  • Sélectivité lexicale      : "
          f"FFT {base[1]:.3f} → Emb {emb[1]:.3f} → HWAT {hwat[1]:.3f}")
    print(f"  • Sélectivité anaphorique   : "
          f"FFT {base[2]:.3f} → Emb {emb[2]:.3f} → HWAT {hwat[2]:.3f}")

    print("\n  Conclusion (honnête) :")
    improved_all = (hwat[0] < base[0]) and (hwat[1] < base[1]) and (hwat[2] < base[2])
    fully_solved = (hwat[0] < 0.5) and (hwat[1] < 0.5) and (hwat[2] < 0.5)
    if improved_all and fully_solved:
        print("  ✅ HWAT récupère PLEINEMENT la sélectivité fine.")
    elif improved_all:
        print("  ⚠ HWAT améliore toutes les métriques (gain ×"
              f"{base[0]/max(hwat[0],1e-6):.2f} sur positionnel) MAIS")
        print("    ne passe pas encore sous 0.5 partout. Les blocs résiduels")
        print("    + LayerNorm atténuent la sélectivité brute de l'embedding.")
        print("    → Pistes : réduire N_BLOCKS, normalisation différente,")
        print("      ou pondérer la phase plus fortement dans la tête LM.")
    else:
        print("  ❌ HWAT n'améliore pas toutes les métriques.")

    print("\n" + "═" * 70)


if __name__ == "__main__":
    main()
