"""
Tests de response_composer.py — synthèse multi-faits
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from question_analyzer import analyze_question
from response_composer import ResponseComposer, compose_response


@pytest.fixture
def composer():
    return ResponseComposer(seed=42)


class TestResponseComposer:
    def test_definition_with_facts(self, composer):
        intent = analyze_question("explique la lumiere")
        facts = [
            ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
            ("lumiere", "se deplace a", "300000 km/s", "PHYSIQUE_FOND"),
        ]
        response = composer.compose(intent, facts)
        assert len(response) > 20
        assert "lumiere" in response.lower() or "Lumiere" in response or "lumière" in response.lower()
        # Une définition doit contenir un verbe définitoire
        assert any(w in response.lower() for w in ['définit', 'definit', 'désigne', 'entend', 'correspond'])

    def test_mecanisme_with_facts(self, composer):
        intent = analyze_question("pourquoi le coeur pompe le sang")
        facts = [
            ("coeur", "pompe", "le sang", "BIOLOGIE"),
            ("sang", "transporte", "l oxygene", "BIOLOGIE"),
        ]
        response = composer.compose(intent, facts)
        assert len(response) > 30
        # Un mécanisme doit contenir des connecteurs causaux
        assert any(w in response.lower() for w in ['explique', 'raison', 'cause', 'conduit', 'résulte'])

    def test_identite_short(self, composer):
        intent = analyze_question("qui a decouvert la relativite")
        facts = [("einstein", "a decouvert", "la relativite", "PHYSIQUE_FOND")]
        response = composer.compose(intent, facts)
        assert len(response) > 10
        assert "einstein" in response.lower() or "Einstein" in response

    def test_factualite_short(self, composer):
        intent = analyze_question("quand einstein a publie la relativite")
        facts = [("einstein", "a publie", "la relativite en 1905", "PASSE")]
        response = composer.compose(intent, facts)
        assert len(response) > 10

    def test_with_enrichissement(self, composer):
        """Quand un bloc de savoir est disponible, il est utilisé en priorité."""
        intent = analyze_question("explique la lumiere")
        facts = []
        bloc = "La lumiere est une onde electromagnetique. Elle se propage a 300000 km/s."
        response = composer.compose(intent, facts, bloc)
        assert "onde electromagnetique" in response.lower()

    def test_enrichissement_priority(self, composer):
        """Le bloc doit être utilisé, pas les faits bruts."""
        intent = analyze_question("explique la lumiere")
        facts = [("lumiere", "est", "tres jolie", "GENERAL")]
        bloc = "La lumiere est une onde electromagnetique voyageant a 300000 km/s."
        response = composer.compose(intent, facts, bloc)
        assert "onde electromagnetique" in response.lower()

    def test_empty_facts(self, composer):
        intent = analyze_question("explique le zeptoplasma")
        response = composer.compose(intent, [])
        assert len(response) > 10
        assert "connais" in response.lower() or "sujet" in response.lower()

    def test_response_variety(self):
        """Les réponses pour une même question doivent varier."""
        c1 = ResponseComposer(seed=1)
        c2 = ResponseComposer(seed=999)
        intent = analyze_question("explique la lumiere")
        facts = [("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND")]
        r1 = c1.compose(intent, facts)
        r2 = c2.compose(intent, facts)
        assert r1 != r2  # Différentes seeds → réponses différentes

    def test_filter_facts_relevant(self, composer):
        """_filter_facts doit éliminer les faits hors-sujet."""
        intent = analyze_question("explique la lumiere")
        facts = [
            ("lumiere", "est une", "onde", "PHYSIQUE_FOND"),
            ("musique", "est", "l art des sons", "CULTURE"),
            ("coeur", "pompe", "le sang", "BIOLOGIE"),
        ]
        filtered = composer._filter_facts(facts, intent)
        assert len(filtered) <= 2  # Au moins "musique" doit être filtré
        assert all('lumiere' in f[0].lower() for f in filtered) or len(filtered) < len(facts)

    def test_filter_facts_fallback(self, composer):
        """Si le filtrage est trop strict, garder au moins 1 fait."""
        intent = analyze_question("explique le zeptoplasma")
        facts = [("musique", "est", "l art des sons", "CULTURE")]
        filtered = composer._filter_facts(facts, intent)
        assert len(filtered) >= 1  # Fallback

    def test_compose_response_convenience(self):
        """La fonction de commodité compose_response() fonctionne."""
        response = compose_response(
            "explique la lumiere",
            [("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND")]
        )
        assert len(response) > 15

    def test_comparison(self, composer):
        intent = analyze_question("difference entre onde et particule")
        facts = [
            ("onde", "transporte", "de l energie", "PHYSIQUE_FOND"),
            ("particule", "possede", "une masse", "PHYSIQUE_FOND"),
        ]
        response = composer.compose(intent, facts)
        assert len(response) > 20
        assert "onde" in response.lower() and "particule" in response.lower()

    def test_procedure(self, composer):
        intent = analyze_question("comment faire pour cuire un oeuf")
        facts = [("oeuf", "doit etre", "cuit 3 minutes", "GENERAL")]
        response = composer.compose(intent, facts)
        assert len(response) > 15
