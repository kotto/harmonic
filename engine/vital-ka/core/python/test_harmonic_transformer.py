"""
Tests formels pour HWAT — Harmonic Wavelet Attention Transformer
=================================================================
Valide les invariants mathématiques du PROPOSAL.md :

  T1. Déterminisme : 2 forwards identiques → sortie identique (bit-exact)
  T2. ISTFT parfaite : |reconstruct(STFT(x)) - x| < 1e-9 en zone centrale
  T3. Sélectivité lexicale : sim(t1, t2) < 0.5 si t1 ≠ t2
  T4. Sélectivité positionnelle : sim(token@p1, token@p2) < 0.5 si p1 ≠ p2
  T5. Zéro dropout/bruit : variance nulle sur 100 forwards
  T6. Ordre fixe : préserve l'asymétrie (token avant ≠ token après)
  T7. Phase ≠ Amplitude : changer l'amplitude sans la phase ≠ changer la phase
  T8. Complétude du pipeline : logits bien formés, gradient-friendly (forme)
  T9. Window multi-échelle : coeffs distincts par échelle (ondelettes ≠ FFT)
  T10. Causalité optionnelle : mask causal ne casse pas le forward

Lancer : python test_harmonic_transformer.py
"""

import sys
import math
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harmonic_transformer import (
    HWAT, HarmonicEmbedding, SpectralOperator, PhaseAttention,
    HarmonicMLP, HarmonicBlock, PHI, TAU
)


# ════════════════════════════════════════════════════════════════
# UTILITAIRES
# ════════════════════════════════════════════════════════════════

def _cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Similarité cosinus entre deux vecteurs complexes (|⟨a|b⟩| / (||a||·||b||))."""
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-30 or nb < 1e-30:
        return 0.0
    return float(np.abs(np.vdot(a, b)) / (na * nb))


class TestReport:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def check(self, name: str, cond: bool, detail: str = ""):
        status = "✅ PASS" if cond else "❌ FAIL"
        self.results.append((status, name, detail))
        if cond:
            self.passed += 1
        else:
            self.failed += 1

    def summary(self):
        print("\n" + "=" * 65)
        total = self.passed + self.failed
        print(f"  RÉSULTAT : {self.passed}/{total} tests validés")
        print("=" * 65)
        for status, name, detail in self.results:
            line = f"  {status}  {name}"
            if detail:
                line += f"  ({detail})"
            print(line)
        return self.failed == 0


# ════════════════════════════════════════════════════════════════
# TESTS
# ════════════════════════════════════════════════════════════════

def test_determinism(report: TestReport):
    """T1. Deux forwards identiques → sorties bit-exact identiques."""
    model = HWAT(vocab_size=100, dim=32, n_blocks=2, max_len=64)
    tokens = np.array([3, 17, 42, 8, 91])
    out1 = model.forward(tokens)
    out2 = model.forward(tokens)
    max_diff = float(np.max(np.abs(out1 - out2)))
    report.check("T1 Déterminisme (2 forwards bit-exact)",
                 max_diff < 1e-15,
                 f"Δmax = {max_diff:.2e}")


def test_istft_perfect(report: TestReport):
    """T2. ISTFT reconstruction parfaite en zone centrale (invariant COLA)."""
    op = SpectralOperator(dim=16, window_sizes=(16, 32, 64))
    L = 256
    rng = np.random.RandomState(42)
    x = rng.randn(L, 16)
    psi = x.astype(complex)
    recon = op.reconstruct(psi)
    w = max(op.window_sizes)
    center = slice(w, L - w)
    err = float(np.max(np.abs(x[center] - recon[center])))
    report.check("T2 ISTFT parfaite (zone centrale)",
                 err < 1e-9,
                 f"err centrale = {err:.2e}")


def test_lexical_selectivity(report: TestReport):
    """T3. Deux tokens différents → similarité < 0.5."""
    model = HWAT(vocab_size=200, dim=64, n_blocks=0, max_len=32)
    # n_blocks=0 pour tester l'embedding brut (avant tout apprentissage)
    a = model.embedder(np.array([7]))[0]
    b = model.embedder(np.array([99]))[0]
    sim = _cos_sim(a, b)
    report.check("T3 Sélectivité lexicale (t1≠t2 → sim<0.5)",
                 sim < 0.5,
                 f"sim = {sim:.3f}")


def test_positional_selectivity(report: TestReport):
    """T4. Même token, positions différentes → similarité < 0.5."""
    model = HWAT(vocab_size=200, dim=64, n_blocks=0, max_len=32)
    a = model.embedder(np.array([42, 0, 0, 0, 0]))[0]
    b = model.embedder(np.array([0, 0, 42, 0, 0]))[2]
    sim = _cos_sim(a, b)
    report.check("T4 Sélectivité positionnelle (Δpos → sim<0.5)",
                 sim < 0.5,
                 f"sim = {sim:.3f}")


def test_no_noise_no_dropout(report: TestReport):
    """T5. 100 forwards de la MÊME entrée → variance inter-run nulle.

    NB : on ne calcule pas np.var(outs) sur tout le tableau (qui inclurait
    la variance légitime entre positions/tokens). On mesure la variance
    EXTERNE : chaque exécution doit donner bit-exact le même résultat.
    """
    model = HWAT(vocab_size=100, dim=32, n_blocks=2, max_len=16)
    tokens = np.array([5, 12, 88, 3])
    ref = model.forward(tokens).copy()
    max_run_diff = 0.0
    for _ in range(100):
        out = model.forward(tokens)
        d = float(np.max(np.abs(out - ref)))
        max_run_diff = max(max_run_diff, d)
    report.check("T5 Zéro bruit / zéro dropout (run-to-run bit-exact)",
                 max_run_diff < 1e-15,
                 f"Δmax inter-run = {max_run_diff:.2e}")


def test_fixed_order(report: TestReport):
    """T6. Ordre préservé : token 7 en pos 0 ≠ token 7 en pos 3."""
    model = HWAT(vocab_size=100, dim=32, n_blocks=1, max_len=16)
    seq_a = np.array([7, 8, 9, 10])
    seq_b = np.array([10, 9, 8, 7])  # inversé
    ea = model.embed(seq_a)
    eb = model.embed(seq_b)
    # L'embedding du token 7 doit différer entre pos 0 et pos 3
    sim = _cos_sim(ea[0], eb[3])  # token 7 à pos 0 vs pos 3
    report.check("T6 Ordre fixe (token @pos0 ≠ token @pos3)",
                 sim < 0.7,
                 f"sim(token 7 @0 vs @3) = {sim:.3f}")


def test_phase_vs_amplitude(report: TestReport):
    """T7. Phase et amplitude sont des canaux indépendants."""
    emb = HarmonicEmbedding(vocab_size=10, dim=32, max_len=8)
    # Deux tokens de même amplitude forcée
    A_fake = np.ones((10, 32))
    A_fake = A_fake / np.linalg.norm(A_fake, axis=1, keepdims=True)
    emb2 = HarmonicEmbedding(vocab_size=10, dim=32, max_len=8)
    emb2.set_semantic_amplitudes(A_fake)
    # Tous les tokens ont la même amplitude → seule la phase les distingue
    a = emb2(np.array([1]))[0]
    b = emb2(np.array([2]))[0]
    sim_same_amp = _cos_sim(a, b)
    report.check("T7 Phase indépendante de l'amplitude "
                 "(même A, token ≠ → sim<0.5)",
                 sim_same_amp < 0.5,
                 f"sim = {sim_same_amp:.3f}")


def test_pipeline_shape(report: TestReport):
    """T8. Logits bien formés : [L, vocab_size], finis."""
    model = HWAT(vocab_size=50, dim=32, n_blocks=2, max_len=16)
    tokens = np.array([0, 1, 2, 3, 4])
    logits = model.forward(tokens)
    ok_shape = logits.shape == (5, 50)
    ok_finite = np.all(np.isfinite(logits))
    report.check("T8 Pipeline complet (shape + fini)",
                 ok_shape and ok_finite,
                 f"shape={logits.shape}, finite={ok_finite}")


def test_multiscale_wavelets(report: TestReport):
    """T9. Coefficients distincts par échelle (preuve multi-échelle)."""
    op = SpectralOperator(dim=24, window_sizes=(8, 16, 32))
    rng = np.random.RandomState(7)
    x = rng.randn(64, 24).astype(complex)
    out = op.forward(x)
    per_scale = 24 // 3
    c1 = np.abs(out[:, :per_scale])
    c2 = np.abs(out[:, per_scale:2 * per_scale])
    c3 = np.abs(out[:, 2 * per_scale:])
    # Les distributions d'amplitude par échelle doivent DIFFÉRER
    # (sinon c'est qu'une seule FFT comme l'ancien code)
    diff_12 = abs(c1.mean() - c2.mean()) + abs(c1.std() - c2.std())
    diff_13 = abs(c1.mean() - c3.mean()) + abs(c1.std() - c3.std())
    report.check("T9 Multi-échelle (coeffs distincts par fenêtre)",
                 diff_12 > 0.01 or diff_13 > 0.01,
                 f"|Δμ+Δσ|(8 vs 16)={diff_12:.3f}, (8 vs 32)={diff_13:.3f}")


def test_causal_mask(report: TestReport):
    """T10. Le masque causal ne casse pas le forward."""
    emb = HarmonicEmbedding(vocab_size=50, dim=32, max_len=16)
    attn_causal = PhaseAttention(dim=32, n_heads=4, causal=True)
    attn_open = PhaseAttention(dim=32, n_heads=4, causal=False)
    psi = emb(np.array([1, 2, 3, 4, 5]))
    out_c = attn_causal.forward(psi)
    out_o = attn_open.forward(psi)
    ok_shape = out_c.shape == psi.shape == out_o.shape
    ok_finite = np.all(np.isfinite(out_c)) and np.all(np.isfinite(out_o))
    report.check("T10 Masque causal (forward stable)",
                 ok_shape and ok_finite,
                 f"shapes ok={ok_shape}, finite={ok_finite}")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("═" * 65)
    print("  TESTS — Harmonic Wavelet Attention Transformer (HWAT)")
    print("═" * 65)

    report = TestReport()
    test_determinism(report)
    test_istft_perfect(report)
    test_lexical_selectivity(report)
    test_positional_selectivity(report)
    test_no_noise_no_dropout(report)
    test_fixed_order(report)
    test_phase_vs_amplitude(report)
    test_pipeline_shape(report)
    test_multiscale_wavelets(report)
    test_causal_mask(report)

    ok = report.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
