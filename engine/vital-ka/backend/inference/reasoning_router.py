"""
🔮 reasoning_router.py — Pont Intent Router → Wave Logic
==========================================================
Connecte les questions de raisonnement en langage naturel
au moteur de logique ondulatoire (wave_logic.py).

Pipeline :
  1. Détecter le type de raisonnement (syllogisme, déduction, analogie...)
  2. Extraire les prémisses de la question
  3. Appeler WaveLogic.solve(premises, question)
  4. Valider avec ConsciousCritic (si disponible)
  5. Retourner la conclusion formatée

Usage :
  from reasoning_router import solve_reasoning
  result = solve_reasoning("Si Socrate est un homme et que tous les hommes sont mortels, que peut-on conclure ?")
"""

import sys, re, math
from pathlib import Path
from typing import Optional, List, Tuple

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))


# ════════════════════════════════════════════════════════════════
# 1. INITIALISATION (lazy)
# ════════════════════════════════════════════════════════════════

_wave_logic = None
_conscious_critic = None


def _get_wave_logic():
    global _wave_logic
    if _wave_logic is None:
        try:
            from wave_logic import WaveLogic
            from holographic_encoder import HolographicEncoder
            enc = HolographicEncoder()
            _wave_logic = WaveLogic(enc)
        except Exception as e:
            print(f"  ⚠ WaveLogic non disponible: {e}")
            _wave_logic = False
    return _wave_logic if _wave_logic is not False else None


def _get_critic():
    global _conscious_critic
    if _conscious_critic is None:
        try:
            from conscious_critic import ConsciousCritic
            _conscious_critic = ConsciousCritic()
        except Exception:
            _conscious_critic = False
    return _conscious_critic if _conscious_critic is not False else None


# ════════════════════════════════════════════════════════════════
# 2. EXTRACTION DES PRÉMISSES
# ════════════════════════════════════════════════════════════════

def _extract_premises(question: str) -> List[str]:
    """Extrait les prémisses d'une question de raisonnement."""
    q = question.strip()

    # Pattern 1 : « Si A, (alors) B »
    si_match = re.search(
        r'(?:si|supposons\s+que)\s+(.+?)(?:,?\s*(?:que\s+peut|alors|donc|qu\'est|quel|quelle|comment|pourquoi)|$)',
        q, re.IGNORECASE)
    if si_match:
        condition = si_match.group(1).strip().rstrip('.,;')
        parts = re.split(r'\s+et\s+que\s+|\s+et\s+|\s*,\s*(?=[A-ZÀ-ÿ])', condition)
        premises = [p.strip().rstrip('.,;?!') for p in parts if len(p.strip()) > 3]
        # Ajouter les phrases après le "Si..." comme prémisses additionnelles
        sentences = re.split(r'(?<=[.!?])\s+', q)
        for s in sentences[1:]:
            s = s.strip().rstrip('.,;?!')
            if len(s) > 5 and not re.match(
                r'^(que|quel|quelle|quels|quelles|comment|pourquoi|peut|qu\'est)',
                s, re.IGNORECASE):
                if s not in premises:
                    premises.append(s)
        if premises:
            return premises[:3]

    # Pattern 2 : « A. B. Que peut-on conclure ? » (phrases séparées)
    sentences = re.split(r'(?<=[.!?])\s+', q)
    if len(sentences) >= 2:
        premises = []
        for s in sentences:
            s = s.strip().rstrip('.,;?!')
            # Ignorer les questions
            if len(s) > 5 and not re.match(
                r'^(que|quel|quelle|quels|quelles|comment|pourquoi|peut|qu\'est)',
                s, re.IGNORECASE):
                premises.append(s)
        if len(premises) >= 1:
            return premises[:3]

    # Pattern 3 : « Sachant que A, B. Que... »
    sachant = re.search(r'sachant\s+que\s+(.+?)(?:[.!?]|$)', q, re.IGNORECASE)
    if sachant:
        parts = re.split(r'\s+et\s+que\s+|\s+et\s+|,', sachant.group(1))
        return [p.strip().rstrip('.,;') for p in parts if len(p.strip()) > 3]

    # Pattern 4 : « Tous les X sont Y. Z est X. » → syllogisme
    tous_match = re.findall(r'((?:tous\s+les?|tout\s+les?|chaque|aucun)\s+.+?[.!?])', q, re.IGNORECASE)
    if tous_match:
        return [m.strip().rstrip('.,;?!') for m in tous_match[:2]]

    # Fallback : question entière comme prémisse unique
    if len(q) > 10:
        return [q.rstrip('?.,;')]

    return []


# ════════════════════════════════════════════════════════════════
# 3. RÉSOLUTION
# ════════════════════════════════════════════════════════════════

def solve_reasoning(question: str) -> Optional[str]:
    """Point d'entrée principal pour le raisonnement ondulatoire.

    Args:
        question: question en langage naturel

    Returns:
        Réponse formatée, ou None si non résoluble
    """
    wl = _get_wave_logic()
    if not wl:
        return None

    # Extraire les prémisses
    premises = _extract_premises(question)
    if not premises or len(premises[0]) < 3:
        return None

    # Extraire la question (ce qu'on cherche)
    q_match = re.search(r'(?:que\s+peut[-\s]on\s+(?:en\s+)?(?:conclure|déduire|dire)|qu\'est[-\s]ce\s+qu[-\s]on\s+peut)\s*(.+?)[?]*$',
                       question, re.IGNORECASE)
    sub_question = q_match.group(1).strip() if q_match else question[:80]

    # Résoudre
    try:
        result = wl.solve(premises, sub_question)
        if not result or not result.is_valid:
            return None

        # Formater
        confidence = result.confidence
        conf_bar = '█' * int(confidence * 10) + '░' * (10 - int(confidence * 10))

        lines = [
            f"🌊 Raisonnement ondulatoire ({result.method})",
            f"   Confiance : {conf_bar} {confidence:.0%}",
            f"   Cohérence : {result.coherence:+.3f}",
            "",
            f"   📐 Prémisses :",
        ]
        for p in premises[:3]:
            lines.append(f"      • {p[:80]}")
        lines.append(f"   🎯 Conclusion : {result.conclusion}")

        if result.steps:
            lines.append(f"   📝 Étapes : {' → '.join(result.steps[:3])}")

        return '\n'.join(lines)

    except Exception as e:
        return f"🌊 Raisonnement: {str(e)[:100]}"

    return None


# ════════════════════════════════════════════════════════════════
# 4. DÉMO
# ════════════════════════════════════════════════════════════════

def demo():
    print("═" * 55)
    print("  🔮 REASONING ROUTER — Démo")
    print("═" * 55)

    tests = [
        "Si Socrate est un homme et que tous les hommes sont mortels, que peut-on conclure ?",
        "Tous les chats sont des félins. Les félins sont des mammifères. Que peut-on déduire ?",
        "Si la lumière est une onde et que les ondes transportent de l'énergie, que peut-on conclure ?",
        "Sachant que A implique B et que B implique C, que déduire ?",
        "Si le sol est mouillé alors il a plu. Le sol est mouillé. Que peut-on déduire ?",
    ]

    for q in tests:
        print(f"\n  Q: {q[:80]}...")
        r = solve_reasoning(q)
        if r:
            print(r)
        else:
            print("  → Non résoluble (prémisses non détectées)")

    print(f"\n  ✅ Reasoning router prêt.")


if __name__ == "__main__":
    demo()
