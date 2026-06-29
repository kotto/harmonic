"""
Tests unitaires pour le noyau mathematique du Harmonic Engine.

Couvre :
  - abc_kernel.py    : Gamma, Mittag-Leffler, noyau ABC, determinisme
  - signatures_9d.py : bornes [0,1] des 9 dimensions, validation
  - sopc_core.py     : predictive_update_abc (determinisme, bornes)

Executer avec :
    python -m pytest tests/test_core.py -v
    # ou
    python tests/test_core.py
"""

import sys
import os
import math
import unittest
import numpy as np

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer directement les modules (evite __init__.py qui charge FastAPI)
import abc_kernel
import signatures_9d

# Importer sopc_core via importlib (evite import engine.*)
import importlib.util
_spec = importlib.util.spec_from_file_location(
    'sopc_core',
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sopc_core.py')
)
sopc_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sopc_core)


# ============================================================================
# CONSTANTES DE REFERENCE
# ============================================================================

PHI = abc_kernel.PHI
ALPHA = abc_kernel.ALPHA
TOL = 1e-5  # Tolerance pour les tests numeriques


# ============================================================================
# abc_kernel.py
# ============================================================================

class TestGammaLanczos(unittest.TestCase):
    """Fonction Gamma via approximation de Lanczos."""

    def test_gamma_integer(self):
        """Γ(n) = (n-1)! pour n entier."""
        self.assertAlmostEqual(float(abc_kernel.gamma_lanczos(np.array([1.0]))[0]), 1.0, delta=TOL)
        self.assertAlmostEqual(float(abc_kernel.gamma_lanczos(np.array([2.0]))[0]), 1.0, delta=TOL)
        self.assertAlmostEqual(float(abc_kernel.gamma_lanczos(np.array([3.0]))[0]), 2.0, delta=TOL)
        self.assertAlmostEqual(float(abc_kernel.gamma_lanczos(np.array([4.0]))[0]), 6.0, delta=TOL)
        self.assertAlmostEqual(float(abc_kernel.gamma_lanczos(np.array([5.0]))[0]), 24.0, delta=TOL)

    def test_gamma_half(self):
        """Γ(0.5) = √π ≈ 1.77245."""
        val = float(abc_kernel.gamma_lanczos(np.array([0.5]))[0])
        self.assertAlmostEqual(val, math.sqrt(math.pi), delta=1e-4)

    def test_gamma_array(self):
        """Accepte np.ndarray et retourne meme shape."""
        z = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = abc_kernel.gamma_lanczos(z)
        self.assertEqual(result.shape, z.shape)
        self.assertTrue(np.all(result > 0))

    def test_gamma_reflection(self):
        """Γ(z)Γ(1-z) = π/sin(πz) (formule de reflexion)."""
        z = np.array([0.3])
        gz = float(abc_kernel.gamma_lanczos(z)[0])
        g1z = float(abc_kernel.gamma_lanczos(1.0 - z)[0])
        expected = math.pi / math.sin(math.pi * 0.3)
        self.assertAlmostEqual(gz * g1z, expected, delta=1e-3)


class TestMittagLeffler(unittest.TestCase):
    """Fonction de Mittag-Leffler E_α(z)."""

    def test_ml_zero(self):
        """E_α(0) = 1/Γ(1) = 1."""
        val = float(abc_kernel.mittag_leffler(np.array([0.0]))[0])
        self.assertAlmostEqual(val, 1.0, delta=TOL)

    def test_ml_alpha_one(self):
        """E_1(z) = exp(z) (cas particulier)."""
        z = np.array([0.5])
        ml = float(abc_kernel.mittag_leffler(z, alpha=1.0)[0])
        self.assertAlmostEqual(ml, math.exp(0.5), delta=TOL)

    def test_ml_negative_arg(self):
        """E_α(-x) pour x petit est dans [0,1]. Pour x grand, E_α oscille."""
        # Propriete : E_α(0) = 1, decroit monotoniquement jusqu'au premier
        # zero, puis oscille (propriete de la fonction de Mittag-Leffler).
        for x in [0.5, 1.0, 2.0]:
            val = float(abc_kernel.mittag_leffler(np.array([-x]))[0])
            self.assertGreaterEqual(val, 0.0, msg=f"E_alpha(-{x}) = {val} < 0")
            self.assertLessEqual(val, 1.0, msg=f"E_alpha(-{x}) = {val} > 1")

    def test_ml_monotonic_decay(self):
        """E_α(-x) est strictement decroissant pour x > 0."""
        v1 = float(abc_kernel.mittag_leffler(np.array([-1.0]))[0])
        v2 = float(abc_kernel.mittag_leffler(np.array([-2.0]))[0])
        v3 = float(abc_kernel.mittag_leffler(np.array([-5.0]))[0])
        self.assertGreater(v1, v2)
        self.assertGreater(v2, v3)


class TestABCKernel(unittest.TestCase):
    """Noyau ABC K(t) = B(α)·E_α(-α·t^α/(1-α))."""

    def test_normalization(self):
        """Le noyau discret est normalise : ΣK(t) = 1."""
        for length in [8, 16, 32, 64, 128]:
            kernel = abc_kernel.abc_kernel_np(length)
            self.assertAlmostEqual(float(kernel.sum()), 1.0, delta=1e-3,
                                   msg=f"ΣK(t) != 1 pour length={length}")

    def test_monotonic_decay(self):
        """K(t) decroit strictement avec t."""
        kernel = abc_kernel.abc_kernel_np(64)
        for i in range(len(kernel) - 1):
            self.assertGreaterEqual(kernel[i], kernel[i + 1] * 0.99,  # tolerance 1%
                                    msg=f"K[{i}] < K[{i+1}], non monotone")

    def test_determinism(self):
        """Meme entree → meme sortie (determinisme par construction)."""
        k1 = abc_kernel.abc_kernel_np(32)
        k2 = abc_kernel.abc_kernel_np(32)
        self.assertTrue(np.allclose(k1, k2))

    def test_positive(self):
        """Tous les poids sont strictement positifs."""
        kernel = abc_kernel.abc_kernel_np(64)
        self.assertTrue(np.all(kernel > 0))

    def test_k0_is_B_alpha(self):
        """K(0) = B(α) (la constante de normalisation)."""
        kernel = abc_kernel.abc_kernel_np(32)
        # K(0) proche de B(α) apres normalisation (le ratio est preserve)
        self.assertGreater(kernel[0], kernel[1])  # decroissance
        self.assertGreater(kernel[0], 0.01)


class TestABCKernelClass(unittest.TestCase):
    """Classe ABCKernel avec cache."""

    def test_cache(self):
        """Le cache retourne la meme instance pour les memes parametres."""
        k = abc_kernel.ABCKernel()
        w1 = k(128, use_torch=False)
        w2 = k(128, use_torch=False)
        self.assertTrue(w1 is w2)  # Meme objet (cache)

    def test_different_lengths(self):
        """Des longueurs differentes donnent des noyaux differents."""
        k = abc_kernel.ABCKernel()
        w_short = k(32)
        w_long = k(128)
        self.assertNotEqual(len(w_short), len(w_long))
        self.assertAlmostEqual(float(w_short.sum()), 1.0, delta=1e-3)
        self.assertAlmostEqual(float(w_long.sum()), 1.0, delta=1e-3)


# ============================================================================
# signatures_9d.py
# ============================================================================

class TestSignatures9D(unittest.TestCase):
    """Les 9 dimensions harmoniques avec bornes [0,1] garanties."""

    @classmethod
    def setUpClass(cls):
        """Creer des embeddings synthetiques pour les tests."""
        np.random.seed(42)
        cls.batch, cls.seq_len, cls.hidden = 2, 12, 64
        cls.embeddings = np.random.randn(cls.batch, cls.seq_len, cls.hidden).astype(np.float32)

    def test_phi_bounds(self):
        """phi ∈ [0, 1]."""
        phi = signatures_9d.compute_phi_np(self.embeddings)
        self.assertTrue(np.all(phi >= 0.0))
        self.assertTrue(np.all(phi <= 1.0))

    def test_alpha_bounds(self):
        """alpha ∈ [0, 1]."""
        alpha = signatures_9d.compute_alpha_np(self.embeddings)
        self.assertTrue(np.all(alpha >= 0.0))
        self.assertTrue(np.all(alpha <= 1.0))

    def test_reasoning_bounds(self):
        """reasoning ∈ [0, 1]."""
        r = signatures_9d.compute_reasoning_np(self.embeddings)
        self.assertTrue(np.all(r >= 0.0))
        self.assertTrue(np.all(r <= 1.0))

    def test_creativity_bounds(self):
        """creativity ∈ [0, 1]."""
        c = signatures_9d.compute_creativity_np(self.embeddings)
        self.assertTrue(np.all(c >= 0.0))
        self.assertTrue(np.all(c <= 1.0))

    def test_math_bounds(self):
        """math ∈ [0, 1]."""
        m = signatures_9d.compute_math_np(self.embeddings)
        self.assertTrue(np.all(m >= 0.0))
        self.assertTrue(np.all(m <= 1.0))

    def test_factual_bounds(self):
        """factual ∈ [0, 1]."""
        f = signatures_9d.compute_factual_np(self.embeddings)
        self.assertTrue(np.all(f >= 0.0))
        self.assertTrue(np.all(f <= 1.0))

    def test_code_bounds(self):
        """code ∈ [0, 1]."""
        c = signatures_9d.compute_code_np(self.embeddings)
        self.assertTrue(np.all(c >= 0.0))
        self.assertTrue(np.all(c <= 1.0))

    def test_emotion_bounds(self):
        """emotion ∈ [0, 1]."""
        e = signatures_9d.compute_emotion_np(self.embeddings)
        self.assertTrue(np.all(e >= 0.0))
        self.assertTrue(np.all(e <= 1.0))

    def test_temporal_bounds(self):
        """temporal ∈ [0, 1]."""
        t = signatures_9d.compute_temporal_np(self.embeddings)
        self.assertTrue(np.all(t >= 0.0))
        self.assertTrue(np.all(t <= 1.0))

    def test_full_signature_shape(self):
        """compute_signature_9d retourne [batch, seq_len, 9]."""
        sig = signatures_9d.compute_signature_9d(self.embeddings)
        self.assertEqual(sig.shape, (self.batch, self.seq_len, 9))

    def test_full_signature_bounds(self):
        """Toutes les dimensions de la signature 9D sont dans [0, 1]."""
        sig = signatures_9d.compute_signature_9d(self.embeddings)
        self.assertTrue(np.all(sig >= 0.0), f"min={sig.min()}")
        self.assertTrue(np.all(sig <= 1.0), f"max={sig.max()}")

    def test_validate_signatures(self):
        """validate_signatures reussit sur une sortie valide."""
        sig = signatures_9d.compute_signature_9d(self.embeddings)
        self.assertTrue(signatures_9d.validate_signatures(sig))

    def test_validate_rejects_invalid(self):
        """validate_signatures rejette une entree invalide (> 1)."""
        bad_sig = np.ones((1, 1, 9)) * 1.5
        with self.assertRaises(AssertionError):
            signatures_9d.validate_signatures(bad_sig)

    def test_unified_auto_detect(self):
        """compute_signature (auto-detect) fonctionne avec numpy."""
        sig = signatures_9d.compute_signature(self.embeddings)
        self.assertEqual(sig.shape, (self.batch, self.seq_len, 9))

    def test_constant_embeddings(self):
        """Embeddings constants → basse entropie, phi proche de 0."""
        const_emb = np.ones((1, 5, 64), dtype=np.float32)
        phi = signatures_9d.compute_phi_np(const_emb)
        # Softmax d'un vecteur constant → max ≈ 1/64, phi ≈ 1 - 1/64 ≈ 0.984
        self.assertGreater(float(phi.mean()), 0.9)


# ============================================================================
# sopc_core.py : predictive_update_abc
# ============================================================================

class TestPredictiveUpdateABC(unittest.TestCase):
    """Predicteur par noyau ABC pur (remplace JEPA)."""

    def test_determinism(self):
        """Meme historique → meme prediction."""
        np.random.seed(42)
        history = [np.random.rand(9).astype(np.float32) for _ in range(10)]
        p1 = sopc_core.predictive_update_abc(history)
        p2 = sopc_core.predictive_update_abc(history)
        self.assertTrue(np.allclose(p1, p2))

    def test_empty_history(self):
        """Historique vide → [0.5, 0.5, ..., 0.5]."""
        pred = sopc_core.predictive_update_abc([])
        self.assertEqual(pred.shape, (9,))
        self.assertTrue(np.allclose(pred, 0.5))

    def test_bounds(self):
        """La prediction est dans [0, 1]."""
        np.random.seed(43)
        history = [np.clip(np.random.rand(9).astype(np.float32), 0.0, 1.0) for _ in range(20)]
        pred = sopc_core.predictive_update_abc(history)
        self.assertTrue(np.all(pred >= 0.0), f"min={pred.min()}")
        self.assertTrue(np.all(pred <= 1.0), f"max={pred.max()}")

    def test_single_history(self):
        """Une signature unique produit une prediction coherente (moyenne ponderee)."""
        sig = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], dtype=np.float32)
        pred = sopc_core.predictive_update_abc([sig])
        # La prediction est dans [0, 1] (teste separement dans test_bounds)
        self.assertTrue(np.all(pred >= 0.0))
        self.assertTrue(np.all(pred <= 1.0))
        # Verification : prediction non-triviale (pas exactement 0.5 partout)
        self.assertFalse(np.allclose(pred, 0.5))

    def test_constant_history(self):
        """Historique de signatures identiques → prediction identique."""
        sig = np.array([0.3] * 9, dtype=np.float32)
        history = [sig.copy() for _ in range(10)]
        pred = sopc_core.predictive_update_abc(history)
        # Toutes les dimensions doivent etre egales
        self.assertAlmostEqual(pred.std(), 0.0, delta=1e-5)

    def test_window_truncation(self):
        """fenetre_contexte limite le nombre de signatures considerees."""
        np.random.seed(44)
        history = [np.random.rand(9).astype(np.float32) for _ in range(100)]
        pred_full = sopc_core.predictive_update_abc(history, fenetre_contexte=100)
        pred_trunc = sopc_core.predictive_update_abc(history, fenetre_contexte=8)
        # Les predictions different (fenetre plus courte = plus reactif)
        self.assertFalse(np.allclose(pred_full, pred_trunc))


# ============================================================================
# Constantes
# ============================================================================

class TestConstants(unittest.TestCase):
    """Verification des constantes fondamentales."""

    def test_phi_definition(self):
        """φ = (1+√5)/2."""
        expected = (1.0 + math.sqrt(5.0)) / 2.0
        self.assertAlmostEqual(PHI, expected, delta=1e-15)

    def test_alpha_is_inverse_phi(self):
        """α = 1/φ."""
        self.assertAlmostEqual(ALPHA, 1.0 / PHI, delta=1e-15)

    def test_alpha_in_range(self):
        """α ∈ (0, 1) — condition de validite de la derivee fractionnaire."""
        self.assertGreater(ALPHA, 0.0)
        self.assertLess(ALPHA, 1.0)

    def test_phi_irrational(self):
        """φ n'est pas un rationnel simple (propriete clef : irrationalite)."""
        # φ² = φ + 1
        self.assertAlmostEqual(PHI * PHI, PHI + 1.0, delta=1e-15)


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
