"""
🌊 phrase_engine.py — Phraséologie conversationnelle (KA Server)
================================================================
Couche de phraséologie qui transforme un fait vérifié en phrase française
naturelle — sans LLM.

Deux canaux :
  1. phrase_fact(sujet, relation, objet) — composition de syntagmes
     (surface_grammar) avec fallback SÛR sur le triplet brut.
  2. prose(fact_text) — extraction de triplet puis composition naturelle.

Renforcement d'amplitude (SurfaceMemory) : la phraséologie s'ajuste
aux retours utilisateur (r > 0.7 renforce, r < 0.3 affaiblit).

Usage :
    from ka_server.services.phrase_engine import get_phrase_engine

    pe = get_phrase_engine()
    pe.phrase_fact('lumiere', 'est une', 'onde electromagnetique')
    # → "La lumière est une onde électromagnétique."

    pe.feedback(0.9)   # renforce les structures utilisées
"""

import logging
from typing import Dict, List, Optional, Tuple

from ka_server.services.surface_grammar import (
    surface, paraphrase, SurfaceMemory, fact_from_text, phrase_fact,
)

log = logging.getLogger(__name__)


class PhraseEngine:
    """Synthétise des phrases naturelles à partir de faits vérifiés."""

    def __init__(self, memory: SurfaceMemory = None):
        self._memory = memory or SurfaceMemory()

    # ── API PRINCIPALE ──────────────────────────────────────────

    def phrase_fact(self, sujet: str, relation: str, objet: str) -> str:
        """Phrase naturelle d'un triplet (sujet, relation, objet)."""
        return phrase_fact(sujet, relation, objet, self._memory)

    def prose(self, fact_text: str, variation: int = 0) -> str:
        """Transforme un fait textuel en prose naturelle."""
        fact = fact_from_text(fact_text)
        if not fact:
            t = fact_text.strip().rstrip('.')
            if t:
                t = t[0].upper() + t[1:]
            return t + '.'
        phrase, _ = surface(fact, self._memory, variation=variation)
        return phrase

    def prose_many(self, fact_texts: List[str]) -> str:
        """Assemble plusieurs faits en prose fluide."""
        phrases = [self.prose(ft, variation=i)
                   for i, ft in enumerate(fact_texts[:3])]
        phrases = [p for p in phrases if p]
        return " ".join(phrases) if phrases else ""

    # ── RENFORCEMENT ───────────────────────────────────────────

    def feedback(self, rating: float) -> Dict:
        """Applique un retour utilisateur (r ∈ [0, 1])."""
        return self._memory.apply_feedback(rating)

    @property
    def memory_stats(self) -> Dict:
        return self._memory.stats()

    def __repr__(self) -> str:
        s = self._memory.stats()
        return f"PhraseEngine({s['structures_apprises']} structures apprises)"


# ── Singleton ──────────────────────────────────────────────
_engine: Optional[PhraseEngine] = None


def get_phrase_engine() -> PhraseEngine:
    global _engine
    if _engine is None:
        _engine = PhraseEngine()
    return _engine


# ═══════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    pe = PhraseEngine()

    print("=== PHRASE_FACT ===")
    for fact in [
        ('lumiere', 'est une', 'onde electromagnetique'),
        ('soleil', 'est', 'une etoile'),
        ('phi', 'est', 'nombre d or'),
        ('COVID-19', 'conduite', 'Isolement immédiat. Test PCR.'),
        ('le diabete de type 1', 'est cause par', 'une deficience en insuline'),
    ]:
        print('  •', pe.phrase_fact(*fact))

    print("\n=== PROSE ===")
    for f in [
        "Le restaurant préféré de Sophie est Le Petit Cambodge",
        "Paris est la capitale de la France",
        "Sophie habite à Paris",
    ]:
        print('  •', pe.prose(f))

    print("\n=== RENFORCEMENT ===")
    print('  feedback(0.9):', pe.feedback(0.9))
    print('  stats:', pe.memory_stats)
