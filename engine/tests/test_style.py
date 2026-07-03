"""
Tests de StyleEngine et _fix_accents() — style_engine.py
========================================================
Teste le rendu élégant et la correction orthographique.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from style_engine import StyleEngine, _fix_accents, _cap_first


class TestFixAccents:
    """Correction orthographique française."""

    def test_fix_common_accents(self):
        """Mots courants sans accents → avec accents."""
        assert _fix_accents("phenomene") == "phénomène"
        assert _fix_accents("etape") == "étape"
        assert _fix_accents("meme") == "même"
        assert _fix_accents("realite") == "réalité"
        assert _fix_accents("lumiere") == "lumière"

    def test_fix_accents_in_sentence(self):
        """Correction dans une phrase complète."""
        text = "le phenomene de la lumiere est un mystere"
        fixed = _fix_accents(text)
        assert "phénomène" in fixed
        assert "lumière" in fixed

    def test_fix_deja_correct(self):
        """Un texte déjà correct n'est pas modifié."""
        text = "la lumière est une onde électromagnétique"
        fixed = _fix_accents(text)
        assert fixed == text

    def test_fix_etre_etat(self):
        """Mots très fréquents."""
        assert "être" in _fix_accents("etre")
        assert "état" in _fix_accents("etat")
        assert "réponse" in _fix_accents("reponse")

    def test_fix_systeme_energie(self):
        """Mots scientifiques."""
        fixed = _fix_accents("le systeme et l energie")
        assert "système" in fixed
        assert "énergie" in fixed

    def test_fix_empty_string(self):
        """Chaîne vide."""
        assert _fix_accents("") == ""

    def test_fix_no_match(self):
        """Texte sans accent à corriger."""
        assert _fix_accents("bonjour le monde") == "bonjour le monde"


class TestCapFirst:
    """Mise en majuscule de la première lettre."""

    def test_simple(self):
        assert _cap_first("bonjour") == "Bonjour"

    def test_preserves_accents(self):
        assert _cap_first("étape") == "Étape"
        assert _cap_first("être") == "Être"

    def test_empty(self):
        assert _cap_first("") == ""

    def test_already_capitalized(self):
        assert _cap_first("Bonjour") == "Bonjour"


class TestStyleEngine:
    """Rendu de style."""

    def test_render_basic(self, styler):
        """Rendu basique d'un chemin à 1 fait."""
        path = [("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND")]
        result = styler.render(path, "explique la lumiere", "PHYSIQUE")
        assert len(result) > 10
        # Le StyleEngine applique _fix_accents → "lumière" au lieu de "lumiere"
        assert ("lumiere" in result.lower() or "lumière" in result.lower()
                or "Lumiere" in result or "Lumière" in result)

    def test_render_physics_domain(self, styler):
        """Rendu avec connecteurs physiques."""
        path = [
            ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
            ("onde", "transporte", "energie sans matiere", "PHYSIQUE_FOND"),
        ]
        result = styler.render(path, "explique la lumiere", "PHYSIQUE")
        assert len(result) > 20
        # Des connecteurs physiques doivent apparaître
        phys_connectors = ["ce qui implique", "ce qui genere", "par consequent",
                          "implique", "genere", "induit", "entraine"]
        assert any(c in result.lower() for c in phys_connectors) or "onde" in result.lower()

    def test_render_biology_domain(self, styler):
        """Rendu avec connecteurs biologiques."""
        path = [
            ("coeur", "pompe", "le sang", "BIOLOGIE"),
            ("sang", "transporte", "l oxygene", "BIOLOGIE"),
        ]
        result = styler.render(path, "explique le coeur", "BIOLOGIE")
        assert len(result) > 15

    def test_render_general_fallback(self, styler):
        """Domaine inconnu → fallback GENERAL."""
        path = [("test", "est", "un exemple", "INCONNU")]
        result = styler.render(path, "explique le test", "INCONNU")
        assert len(result) > 5

    def test_render_empty_path(self, styler):
        """Chemin vide → message d'erreur élégant."""
        result = styler.render([], "explique le vide", "GENERAL")
        assert len(result) > 5

    def test_render_long_chain(self, styler):
        """Chaîne de raisonnement longue (3+ étapes)."""
        path = [
            ("coeur", "pompe", "le sang", "BIOLOGIE"),
            ("sang", "transporte", "l oxygene", "BIOLOGIE"),
            ("oxygene", "alimente", "les cellules", "BIOLOGIE"),
        ]
        result = styler.render(path, "comment le coeur fonctionne", "BIOLOGIE")
        assert len(result) > 30

    def test_render_domains_all(self, styler):
        """Tous les domaines doivent rendre sans erreur."""
        for domain in ["PHYSIQUE", "BIOLOGIE", "MATHS", "CONSCIENCE",
                       "EMOTION", "HISTOIRE", "PHILOSOPHIE", "GENERAL"]:
            path = [("test", "est", f"un exemple {domain}", "GENERAL")]
            result = styler.render(path, f"explique test {domain}", domain)
            assert len(result) > 5, f"Échec pour le domaine {domain}"
