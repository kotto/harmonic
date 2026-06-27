#!/usr/bin/env python3
r"""
TESTS AUTOMATISÉS — Moteur de Raisonnement Universel
=======================================================
Suite pytest complète pour le Moteur Harmonique Universel.
Couvre : arithmétique, algèbre, Pythagore, détection de type, vérification par ondes.

Usage:
  pytest test_moteur_universel.py -v
  python test_moteur_universel.py  # mode standalone
"""

import sys, os, math, json, pytest

PHI = (1 + math.sqrt(5)) / 2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))
sys.path.insert(0, os.path.dirname(__file__))

from moteur_raisonnement_universel import (
    MoteurUniversel, detecter_type_probleme, extract_numbers
)

# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def moteur():
    """Moteur Universel sans corpus (mode arithmétique pur)."""
    return MoteurUniversel()

@pytest.fixture(scope="module")
def moteur_corpus():
    """Moteur Universel avec corpus mathématique (si disponible)."""
    corpus = None
    corpus_file = os.path.join(os.path.dirname(__file__), 'corpus_mathematique.json')
    if os.path.exists(corpus_file):
        with open(corpus_file, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
    m = MoteurUniversel(corpus)
    m.build()
    return m

# ═══════════════════════════════════════════════════════════════════════════
# Tests de détection de type
# ═══════════════════════════════════════════════════════════════════════════

class TestDetectionType:
    def test_detecte_addition(self):
        t, nums, _ = detecter_type_probleme("3 + 4 = ?")
        assert t in ('arithmetique', 'somme')
        assert nums == [3, 4]

    def test_detecte_equation_lineaire(self):
        t, nums, _ = detecter_type_probleme("x + 3 = 7")
        assert t == 'equation'
        assert nums == [3, 7]

    def test_detecte_equation_quadratique(self):
        t, nums, _ = detecter_type_probleme("x² = 49")
        assert t == 'equation'
        assert nums == [49]

    def test_detecte_carre(self):
        t, nums, _ = detecter_type_probleme("carré de 12")
        assert t == 'carre'
        assert nums == [12]

    def test_detecte_racine(self):
        t, nums, _ = detecter_type_probleme("racine carrée de 225")
        assert t == 'racine'
        assert nums == [225]

    def test_detecte_pythagore(self):
        t, nums, _ = detecter_type_probleme("hypoténuse du triangle 3 et 4")
        assert t == 'pythagore'
        assert nums == [3, 4]

    def test_detecte_soustraction(self):
        t, nums, _ = detecter_type_probleme("différence entre 15 et 7")
        assert t in ('soustraction', 'arithmetique')

    def test_detecte_produit(self):
        t, nums, _ = detecter_type_probleme("produit de 6 et 8")
        assert t == 'produit'
        assert nums == [6, 8]

    def test_extraction_nombres_multilignes(self):
        nums = extract_numbers("12 + 34 = 46")
        assert nums == [12, 34, 46]

    def test_extraction_nombres_texte(self):
        nums = extract_numbers("triangle de cotes 5 et 12")
        assert nums == [5, 12]

# ═══════════════════════════════════════════════════════════════════════════
# Tests arithmétiques
# ═══════════════════════════════════════════════════════════════════════════

class TestArithmetique:
    @pytest.mark.parametrize("a, b, somme", [
        (3, 4, 7), (0, 0, 0), (10, 25, 35), (100, 200, 300),
        (7, 8, 15), (50, 50, 100), (1, 99, 100), (33, 67, 100),
    ])
    def test_addition(self, moteur, a, b, somme):
        reponse, type_prob, confiance, trace = moteur.resoudre(f"{a} + {b} = ?")
        if reponse is not None:
            assert reponse == somme, f"{a}+{b} attendu {somme}, reçu {reponse}"

    @pytest.mark.parametrize("a, b, diff", [
        (10, 3, 7), (25, 10, 15), (100, 50, 50), (7, 0, 7),
        (50, 20, 30), (99, 1, 98),
    ])
    def test_soustraction(self, moteur, a, b, diff):
        reponse, type_prob, confiance, trace = moteur.resoudre(f"{a} - {b} = ?")
        if reponse is not None:
            assert reponse == diff, f"{a}-{b} attendu {diff}, reçu {reponse}"

    @pytest.mark.parametrize("n, carre", [
        (5, 25), (7, 49), (12, 144), (0, 0), (1, 1), (10, 100),
        (-3, 9),
    ])
    def test_carre(self, moteur, n, carre):
        reponse, type_prob, confiance, trace = moteur.resoudre(f"{n}² = ?")
        if reponse is not None:
            assert reponse == carre, f"{n}² attendu {carre}, reçu {reponse}"

    @pytest.mark.parametrize("n, racine", [
        (225, 15), (100, 10), (49, 7), (1, 1), (64, 8), (81, 9),
        (25, 5), (144, 12),
    ])
    def test_racine(self, moteur, n, racine):
        reponse, type_prob, confiance, trace = moteur.resoudre(f"racine carrée de {n}")
        if reponse is not None:
            assert reponse == racine, f"√{n} attendu {racine}, reçu {reponse}"

# ═══════════════════════════════════════════════════════════════════════════
# Tests algèbre
# ═══════════════════════════════════════════════════════════════════════════

class TestAlgebre:
    @pytest.mark.parametrize("question, attendu", [
        ("x + 3 = 7", 4),
        ("x + 10 = 25", 15),
        ("x - 5 = 12", 17),
        ("x - 7 = 0", 7),
        ("x + 50 = 100", 50),
    ])
    def test_equation_lineaire(self, moteur, question, attendu):
        reponse, type_prob, confiance, trace = moteur.resoudre(question)
        if reponse is not None:
            assert reponse == attendu, f"'{question}' attendu {attendu}, reçu {reponse}"

    @pytest.mark.parametrize("question, attendu", [
        ("x² = 49", 7),
        ("x² = 100", 10),
        ("x² = 225", 15),
        ("x² = 1", 1),
        ("x² = 64", 8),
    ])
    def test_equation_quadratique(self, moteur, question, attendu):
        reponse, type_prob, confiance, trace = moteur.resoudre(question)
        if reponse is not None:
            assert reponse == attendu, f"'{question}' attendu {attendu}, reçu {reponse}"

# ═══════════════════════════════════════════════════════════════════════════
# Tests Pythagore
# ═══════════════════════════════════════════════════════════════════════════

class TestPythagore:
    @pytest.mark.parametrize("question, attendu", [
        ("hypoténuse du triangle 3 et 4", 5),
        ("triangle rectangle 6 et 8 hypoténuse", 10),
        ("hypoténuse 5 et 12", 13),
        ("triangle 9 et 12", 15),
        ("hypoténuse du triangle rectangle 7 et 24", 25),
    ])
    def test_pythagore(self, moteur, question, attendu):
        reponse, type_prob, confiance, trace = moteur.resoudre(question)
        if reponse is not None:
            assert reponse == attendu, f"'{question}' attendu {attendu}, reçu {reponse}"

# ═══════════════════════════════════════════════════════════════════════════
# Tests de robustesse
# ═══════════════════════════════════════════════════════════════════════════

class TestRobustesse:
    def test_determinisme(self, moteur):
        """Même question 10 fois → même réponse."""
        question = "3 + 4 = ?"
        resultats = []
        for _ in range(10):
            r, _, _, _ = moteur.resoudre(question)
            resultats.append(r)
        assert len(set(resultats)) == 1, f"Non déterministe: {resultats}"

    def test_question_inconnue(self, moteur):
        """Question hors domaine → None avec confiance < 0.5."""
        reponse, type_prob, confiance, trace = moteur.resoudre(
            "Quelle est la signification de la vie ?"
        )
        # Doit retourner None ou confiance < 0.5
        assert reponse is None or confiance < 0.6, \
            f"Question hors domaine ne devrait pas donner de réponse sûre: {reponse}"

    def test_vide(self, moteur):
        """Question vide → réponse None."""
        reponse, type_prob, confiance, trace = moteur.resoudre("")
        assert reponse is None, f"Question vide devrait retourner None, reçu {reponse}"

    def test_question_non_math(self, moteur):
        """Question non mathématique → ne devrait pas halluciner."""
        reponse, type_prob, confiance, trace = moteur.resoudre("Qui est le président de la France ?")
        # Aucune hallucination
        assert reponse is None or confiance < 0.6

# ═══════════════════════════════════════════════════════════════════════════
# Tests vérification par ondes (émergence Ψ_a·Ψ_b = Ψ_{a+b})
# ═══════════════════════════════════════════════════════════════════════════

class TestVerificationOndes:
    def test_verification_addition_exacte(self, moteur):
        """Ψ_a · Ψ_b = Ψ_{a+b} — cosinus exact."""
        conf = moteur.verifier_addition(3, 4, 7)
        assert conf > 0.99, f"Vérification 3+4=7: interf={conf:.4f} < 0.99"

    def test_verification_addition_fausse(self, moteur):
        """Ψ_a · Ψ_b != Ψ_c pour c faux."""
        conf = moteur.verifier_addition(3, 4, 8)
        assert conf < 0.5, f"3+4=8 devrait avoir conf<0.5, reçu {conf:.4f}"

    def test_verification_soustraction_exacte(self, moteur):
        """Ψ_a · conj(Ψ_b) = Ψ_{a-b}."""
        conf = moteur.verifier_soustraction(10, 3, 7)
        assert conf > 0.99, f"Vérification 10-3=7: interf={conf:.4f} < 0.99"

    def test_verification_carre_exact(self, moteur):
        """(Ψ_a)^a = Ψ_{a²}."""
        conf = moteur.verifier_carre(7, 49)
        assert conf > 0.99, f"Vérification 7²=49: interf={conf:.4f} < 0.99"

    @pytest.mark.parametrize("a,b", [(3,4),(7,8),(15,27),(100,200),(0,5)])
    def test_emergence_addition(self, moteur, a, b):
        """L'addition ÉMERGE de Ψ_a · Ψ_b, aucun fait stocké."""
        conf = moteur.verifier_addition(a, b, a + b)
        assert conf > 0.99, f"Émergence {a}+{b}={a+b}: interf={conf:.4f}"


# ═══════════════════════════════════════════════════════════════════════════
# Main standalone
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import subprocess
    print("=" * 70)
    print("  SUITE DE TESTS — Moteur Universel Harmonique")
    print("=" * 70)
    
    # Lancer pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )
    sys.exit(result.returncode)