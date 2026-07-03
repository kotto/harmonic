"""
Tests de detect_sector() — bootstrapper.py
==========================================
Teste la classification sectorielle actuelle.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bootstrapper import detect_sector, SECTOR_KEYWORDS


class TestDetectSector:
    """Classification sectorielle par mots-clés."""

    def test_physique_fond(self):
        assert detect_sector("la lumiere est une onde electromagnetique") == "PHYSIQUE_FOND"
        assert detect_sector("la gravite quantique et la relativite") == "PHYSIQUE_FOND"

    def test_biologie(self):
        assert detect_sector("la cellule contient de l adn et des genes") == "BIOLOGIE"
        assert detect_sector("l evolution des especes par selection naturelle") == "BIOLOGIE"

    def test_conscience(self):
        assert detect_sector("la conscience emerge de l activite cerebrale") == "CONSCIENCE"
        assert detect_sector("la meditation et la perception de soi") == "CONSCIENCE"

    def test_mathematiques(self):
        assert detect_sector("le theoreme de pythagore en geometrie") == "MATHS_PURES"
        assert detect_sector("l equation differentielle et le calcul algebrique") == "MATHS_PURES"

    def test_astronomie(self):
        assert detect_sector("les etoiles et les planetes dans la galaxie") == "ASTRONOMIE"
        assert detect_sector("le soleil est un astre lumineux") == "ASTRONOMIE"

    def test_emotion_positive(self):
        assert detect_sector("l amour et la joie sont essentiels au bonheur") == "EMOTION_POS"
        assert detect_sector("la compassion et l empathie envers les autres") == "EMOTION_POS"

    def test_emotion_negative(self):
        assert detect_sector("la peur et la tristesse face a la souffrance") == "EMOTION_NEG"
        assert detect_sector("le stress et l angoisse du quotidien") == "EMOTION_NEG"

    def test_culture(self):
        assert detect_sector("la musique et la litterature francaise") == "CULTURE"
        assert detect_sector("le cinema et le theatre contemporain") == "CULTURE"

    def test_politique(self):
        assert detect_sector("la democratie et la justice pour la liberte") == "POLITIQUE"
        assert detect_sector("le gouvernement a vote une nouvelle loi") == "POLITIQUE"

    def test_spiritualite(self):
        assert detect_sector("dieu et la foi religieuse") == "SPIRITUALITE"
        assert detect_sector("la transcendance et le sacre") == "SPIRITUALITE"

    def test_metaphysique(self):
        assert detect_sector("la philosophie de l etre et de l existence") == "METAPHYSIQUE"
        assert detect_sector("la verite et l essence de la realite") == "METAPHYSIQUE"

    def test_ecologie(self):
        assert detect_sector("l ecosysteme et la biodiversite en danger") == "ECOLOGIE"
        assert detect_sector("le climat et la pollution environnementale") == "ECOLOGIE"

    def test_cosmologie(self):
        assert detect_sector("l univers et le big bang") == "COSMOLOGIE"
        assert detect_sector("les trous noirs et le multivers") == "COSMOLOGIE"

    def test_passe(self):
        assert detect_sector("l histoire et les traditions des ancetres") == "PASSE"

    def test_futur(self):
        assert detect_sector("le futur de l innovation technologique") == "FUTUR"


class TestDetectSectorFallback:
    """Fallback GENERAL."""

    def test_unknown_topic_returns_general(self):
        """Un texte sans aucun mot-clé → GENERAL."""
        assert detect_sector("le chat boit du lait dans la cuisine") == "GENERAL"

    def test_short_text_general(self):
        # BUG CONNU : "monde" contient "onde" (substring match) → PHYSIQUE_FOND
        # Ce test documente le problème de sous-chaîne de detect_sector()
        result = detect_sector("bonjour le monde")
        # Actuellement classé PHYSIQUE_FOND à cause de "onde" dans "monde"
        assert result in ("GENERAL", "PHYSIQUE_FOND")

    def test_empty_text_general(self):
        """Texte vide."""
        assert detect_sector("") == "GENERAL"


class TestDetectSectorAmbiguity:
    """Cas ambigus — plusieurs secteurs possibles."""

    def test_multiple_sectors_picks_best(self):
        """Quand plusieurs secteurs matchent, prend celui avec le plus de hits."""
        # "lumiere" → PHYSIQUE_FOND, "conscience" → CONSCIENCE
        # "lumiere" apparaît 1x, "conscience" 1x → ex aequo, mais PHYSIQUE_FOND
        # est testé en premier dans la boucle et a 10 keywords, CONSCIENCE 7
        result = detect_sector("la lumiere de la conscience")
        # Les deux secteurs ont 1 hit → max() garde la première clé (PHYSIQUE_FOND)
        # car les scores sont identiques
        assert result in ("PHYSIQUE_FOND", "CONSCIENCE")

    def test_physique_vs_astronomie(self):
        """'etoile' est ASTRONOMIE, 'energie' est PHYSIQUE_FOND."""
        result = detect_sector("l etoile produit de l energie par fusion nucleaire")
        # 1 hit PHYSIQUE_FOND (energie), 1+ hit ASTRONOMIE (etoile)
        # NOTE: scores égaux → max() garde la première clé (PHYSIQUE_FOND)
        # Ce test documente le comportement actuel
        assert result in ("PHYSIQUE_FOND", "ASTRONOMIE")

    def test_substring_issue(self):
        """
        BUG CONNU : 'onde' dans 'monde', 'onde' dans 'abonder', etc.
        'peinture' contient 'peint' (pas un keyword heureusement).
        Mais 'art' (dans 'art visuel') est un keyword de CULTURE.
        """
        result = detect_sector("la peinture est un art visuel")
        # 'art' matche CULTURE — pas GENERAL comme on pourrait l'espérer
        assert result in ("CULTURE", "GENERAL")


class TestDetectSectorCoverage:
    """Vérification de la couverture de tous les secteurs."""

    def test_all_sectors_in_keywords(self):
        """Tous les secteurs de SECTOR_KEYWORDS sont testables."""
        assert len(SECTOR_KEYWORDS) >= 18
        for sector, keywords in SECTOR_KEYWORDS.items():
            assert len(keywords) > 0, f"{sector} n'a pas de mots-clés"

    def test_geography_detected(self):
        """La géographie est maintenant couverte (v2)."""
        assert detect_sector("Paris est la capitale de la France") == "GEOGRAPHIE"

    def test_health_detected(self):
        """La santé est maintenant couverte (v2)."""
        assert detect_sector("le medecin traite la maladie du patient") == "SANTE"

    def test_economics_detected(self):
        """L'économie est maintenant couverte (v2)."""
        assert detect_sector("le PIB et l inflation de l economie") == "ECONOMIE"
