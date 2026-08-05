"""
KA Server — Service Harmonic AI v3 (Intelligence Ondulatoire Unifiée)
======================================================================

Branche le moteur 3-espaces (Phase + Log + Kuramoto + Champ continu)
sur le serveur KA. Complémentaire de l'ancien harmonic_ai (ℂ⁵¹²+RAG).

Le service est LAZY : le moteur n'est initialisé qu'au premier appel.
"""

import logging
import re
import sys
import os

log = logging.getLogger(__name__)

# Singleton
_engine = None
_engine_ready = False


def _resolve_vital_python():
    """Résout le chemin vital-ka/core/python (emplacement des moteurs)."""
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        cand = os.path.join(here, 'vital-ka', 'core', 'python')
        if os.path.exists(os.path.join(cand, 'harmonic_ai_v3.py')):
            return cand
        here = os.path.dirname(here)
    return None


def get_harmonic_v3():
    """Retourne le moteur Harmonic AI v3 (lazy init)."""
    global _engine, _engine_ready
    if _engine_ready:
        return _engine

    try:
        vital = _resolve_vital_python()
        if vital and vital not in sys.path:
            sys.path.insert(0, vital)
        from harmonic_ai_v3 import HarmonicAI
        _engine = HarmonicAI()
        _engine_ready = True
        log.info("HarmonicAI v3 initialisé (Phase + Log + Kuramoto + Champ)")
    except Exception as e:
        log.warning(f"HarmonicAI v3 indisponible : {e}")
        _engine = None
        _engine_ready = True
    return _engine


def is_available() -> bool:
    return get_harmonic_v3() is not None


def _detect_arithmetic(message: str):
    """Détecte une expression arithmétique simple → (a, op, b)."""
    m = re.search(r'(-?\d+\.?\d*)\s*([+\-*/])\s*(-?\d+\.?\d*)', message)
    if not m:
        return None
    a, op, b = float(m.group(1)), m.group(2), float(m.group(3))
    return a, op, b


def process_harmonic(message: str, candidates: list = None) -> dict:
    """
    Traite un message avec le moteur v3.

    Retourne un dict :
      {'handled': True/False, 'kind': 'arithmetic'|'qa'|'logic'|'none',
       'result': ..., 'explanation': str, 'coherence': float}
    """
    engine = get_harmonic_v3()
    if engine is None:
        return {'handled': False, 'kind': 'none', 'reason': 'engine_unavailable'}

    # 1. Arithmétique émergente
    arith = _detect_arithmetic(message)
    if arith:
        a, op, b = arith
        expr = f"{a:g}{op}{b:g}"
        try:
            result = engine.solve(expr)
            if op == '+':
                kind = 'addition_emergence'
            elif op == '-':
                kind = 'soustraction_emergence'
            elif op == '*':
                kind = 'multiplication_emergence'
            else:
                kind = 'division_emergence'
            return {
                'handled': True, 'kind': kind,
                'result': result,
                'explanation': f"{a:g} {op} {b:g} = {result:g} (émergence ondulatoire, 0 fait stocké)",
                'coherence': engine.coherence(),
            }
        except Exception as e:
            log.debug(f"Arithmetic failed: {e}")

    # 2. QA factuelle (si la base contient des faits)
    if engine.stats['facts'] > 0 and candidates:
        try:
            results = engine.ask(message, candidates, steps=500)
            if results and results[0][1] > 0.3:
                return {
                    'handled': True, 'kind': 'qa',
                    'result': results[0][0],
                    'explanation': f"Inférence Kuramoto : {results[0][0]} "
                                   f"(score {results[0][1]:.2f}, verdict {results[0][2]})",
                    'coherence': engine.coherence(),
                    'top': results[:3],
                }
        except Exception as e:
            log.debug(f"QA failed: {e}")

    return {'handled': False, 'kind': 'none'}


def seed_default_knowledge():
    """Enseigne les faits fondamentaux au moteur v3 (si vide)."""
    engine = get_harmonic_v3()
    if engine is None or engine.stats['facts'] > 0:
        return
    facts = [
        ("Paris", "capitale_de", "France"),
        ("Londres", "capitale_de", "Angleterre"),
        ("Tokyo", "capitale_de", "Japon"),
        ("Madrid", "capitale_de", "Espagne"),
        ("Berlin", "capitale_de", "Allemagne"),
        ("Rome", "capitale_de", "Italie"),
        ("Ottawa", "capitale_de", "Canada"),
        ("chat", "est_un", "félin"),
        ("chien", "est_un", "mammifère"),
        ("Paris", "ville_de", "France"),
        ("Lyon", "ville_de", "France"),
        ("Marseille", "ville_de", "France"),
        ("Londres", "ville_de", "Angleterre"),
        ("eau", "gèle_à", "0"),
        ("eau", "bout_à", "100"),
    ]
    engine.ingest_facts(facts)
    log.info(f"HarmonicAI v3 : {len(facts)} faits de base ingérés")
