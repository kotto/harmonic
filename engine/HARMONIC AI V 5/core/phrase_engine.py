"""
HARMONIC AI V 5 — Phrase Engine (Phraséologie conversationnelle)
=================================================================
Port enrichi de wave_response.py + harmoniq_styler.py vers la V5.

Transforme un résultat brut (nombre, fait, liste) en phrase française
complète et naturelle, selon l'intention détectée — sans LLM.

Deux canaux :
  1. Factuel  : templates par intention (math, code, query, reason...)
                → « 2 + 3 × 4 = 14. »
                → « J'en déduis : [conclusion]. »
  2. Prose    : surface_grammar.surface() compose les faits en prose
                naturelle avec morphologie + renforcement d'amplitude.
                → « Le diabète de type 1 est causé par une déficience
                    en insuline. »

Contrat : la surface ne produit JAMAIS un mot hors des faits.

Usage :
  from core.phrase_engine import PhraseEngine

  pe = PhraseEngine()
  pe.synthesize(intent='math', value=14, expr='2 + 3 × 4')
  # "2 + 3 × 4 = 14."

  pe.synthesize(intent='query', value="Paris", question="capitale France ?")
  # "Voici ce que je trouve : Paris."

  pe.feedback(0.9)   # renforce les structures utilisées
"""

from typing import Any, Dict, List, Optional, Tuple

from core.surface_grammar import (
    surface, paraphrase, SurfaceMemory, fact_from_text,
)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _fmt_number(v) -> str:
    """14.0 → '14', 2.5 → '2.5'."""
    try:
        f = float(v)
        if f == int(f):
            return str(int(f))
        return str(round(f, 4))
    except (TypeError, ValueError):
        return str(v)


def _clean_value(value) -> str:
    """Convertit une valeur en texte lisible."""
    try:
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            return _fmt_number(value)
        if hasattr(value, 'ndim') and value.ndim == 2:
            return " ".join(str(w) for w in value[:, 0])
        if isinstance(value, (list, tuple)) and value:
            words = []
            for it in value:
                if isinstance(it, (list, tuple)) and it:
                    words.append(str(it[0]))
                else:
                    words.append(str(it))
            return " ".join(words)
        if hasattr(value, 'shape'):
            return ""
        return str(value)
    except Exception:
        return str(value)


# ═══════════════════════════════════════════════════════════
# PHRASE ENGINE
# ═══════════════════════════════════════════════════════════

class PhraseEngine:
    """
    Synthétise une réponse naturelle à partir d'un résultat de pipeline.
    
    Deux modes :
    - template (par intention) : précis, déterministe, zéro hallucination
    - prose (surface_grammar)  : pour les faits factuels (triplets)
    
    Le renforcement d'amplitude (SurfaceMemory) ajuste la phraséologie
    selon les retours utilisateur.
    """

    def __init__(self, memory: SurfaceMemory = None):
        self._memory = memory or SurfaceMemory()

    # ═══════════════════════════════════════════════════════════
    # SYNTHÈSE PRINCIPALE
    # ═══════════════════════════════════════════════════════════

    def synthesize(self, intent: str, value: Any = None,
                   question: str = '', expr: str = '',
                   facts: List[str] = None) -> str:
        """
        Construit la réponse finale selon l'intention.
        
        Args:
            intent: type d'intention (math, code, query, reason, ...)
            value: résultat brut du raisonnement
            question: question d'origine
            expr: expression mathématique (si math)
            facts: liste de faits texte (pour le mode prose)
        """
        handler = getattr(self, f'_resp_{intent}', None)
        if handler is not None:
            try:
                resp = handler(value=value, question=question, expr=expr,
                               facts=facts)
                if resp:
                    return resp
            except Exception:
                pass
        return self._resp_fallback(value)

    # ── Par intention ──────────────────────────────────────────

    def _resp_math(self, **kw) -> str:
        expr = kw.get('expr', '')
        value = kw.get('value')
        if value is None:
            return ""
        if expr:
            return f"{expr} = {_fmt_number(value)}."
        return f"Le résultat est {_fmt_number(value)}."

    def _resp_code(self, **kw) -> str:
        value = kw.get('value') or ''
        return f"Voici le code généré :\n{value}" if value else "Voici le code généré."

    def _resp_reason(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        return f"J'en déduis : {text}." if text else "Voici mon raisonnement."

    def _resp_query(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        if text and not text.startswith(('Je ', 'Voici', 'Il ', 'Elle ')):
            return f"Voici ce que je trouve : {text}."
        return text or "Voici ce que je trouve."

    def _resp_store_fact(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        return f"Fait mémorisé : {text}." if text else "Fait mémorisé."

    def _resp_creative(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        return f"Voici une idée : {text}." if text else "Voici une idée."

    def _resp_compare(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        return f"Voici l'analyse : {text}." if text else "Voici l'analyse."

    def _resp_classify(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        return f"Voici la classification : {text}." if text else "Voici la classification."

    def _resp_analogize(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        return f"Par analogie : {text}." if text else "Par analogie."

    def _resp_action(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        return text if text else "Action effectuée."

    def _resp_chat(self, **kw) -> str:
        value = kw.get('value')
        text = _clean_value(value) if value is not None else ""
        return text if text else "Je t'écoute."

    def _resp_fallback(self, value) -> str:
        text = _clean_value(value)
        if text:
            return f"{text}."
        return "Voici ma réponse."

    # ═══════════════════════════════════════════════════════════
    # MODE PROSE (surface_grammar)
    # ═══════════════════════════════════════════════════════════

    def prose(self, fact_text: str, variation: int = 0) -> str:
        """
        Transforme un fait textuel en prose naturelle (surface grammar).
        
        Args:
            fact_text: phrase factuelle (« Sophie aime le chocolat noir »)
            variation: indice de paraphrase (0..n)
        """
        fact = fact_from_text(fact_text)
        if not fact:
            # Pas de triplet détectable → majuscule initiale sans casser
            # les noms propres (« Paris » reste « Paris »)
            t = fact_text.strip().rstrip('.')
            if t:
                t = t[0].upper() + t[1:]
            return t + '.'
        phrase, keys = surface(fact, self._memory, variation=variation)
        return phrase

    def prose_many(self, fact_texts: List[str]) -> str:
        """Assemble plusieurs faits en prose fluide."""
        phrases = []
        for i, ft in enumerate(fact_texts[:3]):
            p = self.prose(ft, variation=i)
            if p:
                phrases.append(p)
        return " ".join(phrases) if phrases else ""

    # ═══════════════════════════════════════════════════════════
    # RENFORCEMENT
    # ═══════════════════════════════════════════════════════════

    def feedback(self, rating: float) -> Dict:
        """Applique un retour utilisateur à la phraséologie (r ∈ [0, 1])."""
        return self._memory.apply_feedback(rating)

    @property
    def memory_stats(self) -> Dict:
        return self._memory.stats()

    def __repr__(self) -> str:
        s = self._memory.stats()
        return f"PhraseEngine({s['structures_apprises']} structures apprises)"


# ═══════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    pe = PhraseEngine()

    print("=== TEMPLATES PAR INTENTION ===")
    print('  math       :', pe.synthesize('math', value=14, expr='2 + 3 × 4'))
    print('  math %     :', pe.synthesize('math', value=30, expr='15% de 200'))
    print('  reason     :', pe.synthesize('reason', value='il pleut car le ciel est couvert'))
    print('  query      :', pe.synthesize('query', value='Paris'))
    print('  store_fact :', pe.synthesize('store_fact', value='ton anniversaire est le 15 mars'))
    print('  compare    :', pe.synthesize('compare', value='le chat est indépendant, le chien fidèle'))
    print('  classify   :', pe.synthesize('classify', value='pomme, banane → fruits'))
    print('  analogize  :', pe.synthesize('analogize', value='la mémoire est comme un océan'))
    print('  chat       :', pe.synthesize('chat', value='Bonjour ! Comment vas-tu ?'))

    print("\n=== MODE PROSE (surface grammar) ===")
    faits = [
        "Sophie aime le chocolat noir",
        "Paris est la capitale de la France",
        "Le diabète de type 1 est causé par une déficience en insuline",
    ]
    for f in faits:
        print('  •', pe.prose(f))
        print('    paraphrases:', [p for p in paraphrase(fact_from_text(f) or ('', '', ''), 3) if p])

    print("\n=== RENFORCEMENT ===")
    print('  feedback(0.9):', pe.feedback(0.9))
    print('  stats:', pe.memory_stats)
