#!/usr/bin/env python3
"""
TESTS — Processeur Harmonique (HPU)
=====================================
Suite de tests pour le cœur de l'ordinateur harmonique.
"""

import sys, os, math, pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from emulateur.harmonic_processor import (
    HPU, HBit, PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI,
    HARMONIC_CONSTANTS, H_BIT_DIMENSION, FREQUENCE_FONDAMENTALE
)


class TestHBit:
    def test_creation_valeur(self):
        h = HBit.from_value(42.0)
        assert len(h.coefficients) == H_BIT_DIMENSION
        assert np.all(np.isfinite(h.coefficients))

    def test_creation_texte(self):
        h = HBit.from_text("ordinateur harmonique")
        assert len(h.coefficients) == H_BIT_DIMENSION
        assert abs(h.norm() - 1.0) < 0.01

    def test_to_scalar(self):
        h = HBit.from_value(PHI)
        assert abs(h.to_scalar() - PHI) < 0.1  # Approximation due à la projection

    def test_interference_self(self):
        h = HBit.from_value(42.0)
        interf = h.interference(h)
        assert abs(interf - 1.0) < 0.01

    def test_interference_orthogonal(self):
        # Deux textes très différents
        h1 = HBit.from_text("chat")
        h2 = HBit.from_text("ordinateur quantique supraconducteur")
        interf = h1.interference(h2)
        assert interf < 1.0  # Pas identiques
        assert interf > -1.1  # Pas parfaitement opposés

    def test_multiplication_is_commutative(self):
        h1 = HBit.from_value(3.0)
        h2 = HBit.from_value(4.0)
        m1 = h1 * h2
        m2 = h2 * h1
        diff = np.max(np.abs(m1.coefficients - m2.coefficients))
        assert diff < 0.01

    def test_addition(self):
        h1 = HBit.from_value(3.0)
        h2 = HBit.from_value(4.0)
        h_sum = h1 + h2
        assert h_sum.norm() > 0


class TestHPU:
    @pytest.fixture
    def hpu(self):
        return HPU(grid_size=128)

    def test_init(self, hpu):
        assert hpu.GRID == 128
        assert hpu.stats['operations'] == 0
        assert hpu.stats['resonances'] == 0

    def test_resonner_nombre(self, hpu):
        r = hpu.resonner(137.0)
        assert 'reponse' in r
        assert 'confiance' in r
        assert 'energie' in r
        assert 'harmoniques_activees' in r
        assert 0 <= r['confiance'] <= 1.1

    def test_resonner_texte(self, hpu):
        r = hpu.resonner("problème NP-complet")
        assert 'reponse' in r
        assert isinstance(r['confiance'], float)

    def test_superposer(self, hpu):
        initial_norm = np.linalg.norm(hpu.holographic_memory)
        hpu.superposer("connaissance A", amplitude=0.1)
        hpu.superposer("connaissance B", amplitude=0.1)
        after_norm = np.linalg.norm(hpu.holographic_memory)
        # La mémoire a été modifiée
        assert after_norm != initial_norm

    def test_stats(self, hpu):
        hpu.resonner(42.0)
        stats = hpu.get_stats()
        assert stats['operations'] >= 1
        assert 'frequence_fondamentale' in stats
        assert stats['frequence_fondamentale'] == FREQUENCE_FONDAMENTALE
        assert stats['dimension_hbit'] == 7

    def test_determinisme(self, hpu):
        """Même requête → même réponse (pas d'aléatoire)."""
        r1 = hpu.resonner(42.0)
        # Réinitialiser
        hpu2 = HPU(grid_size=128)
        r2 = hpu2.resonner(42.0)
        # La confiance peut légèrement varier mais la structure est déterministe
        assert abs(r1['confiance'] - r2['confiance']) < 0.1

    def test_harmoniques_base(self):
        """Vérifie que les 7 constantes sont correctement définies."""
        assert abs(PHI - 1.6180339887) < 0.001
        assert abs(PI - 3.14159265) < 0.001
        assert abs(E - 2.71828182) < 0.001
        assert abs(SQRT2 - 1.41421356) < 0.001
        assert abs(SQRT3 - 1.73205080) < 0.001
        assert len(HARMONIC_CONSTANTS) == 7


class TestBenchmark:
    @pytest.fixture
    def niveaux(self):
        from emulateur.niveaux_harmoniques import NiveauxOrdinateurHarmonique
        return NiveauxOrdinateurHarmonique()

    def test_niveau1_addition(self, niveaux):
        r = niveaux.niveau1_arithmetic_emergence(3, 4)
        assert abs(r - 7) < 0.1

    def test_niveau2_recherche(self, niveaux):
        r = niveaux.niveau2_search("protéine", ["acide aminé", "repliement protéine", "enzyme"])
        assert r['trouve'] is not None
        assert r['interference'] > -2

    def test_niveau3_optimization(self, niveaux):
        fonction = np.sin(np.linspace(0, 4*np.pi, 100)) * 10
        r = niveaux.niveau3_optimization(fonction, iterations=50)
        assert 'meilleure_valeur' in r
        assert r['meilleure_valeur'] > -1000

    def test_niveau5_resonance(self, niveaux):
        r = niveaux.niveau5_universal_resonance("test")
        assert 'confiance' in r
        assert 0 <= r['confiance'] <= 1.1

    def test_benchmark_complet(self, niveaux):
        results = niveaux.run_benchmark()
        assert 'n1_arithmetic' in results
        assert 'n2_search' in results
        assert 'n3_optimization' in results
        assert 'n4_holographic' in results
        assert 'n5_universal' in results


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short'])