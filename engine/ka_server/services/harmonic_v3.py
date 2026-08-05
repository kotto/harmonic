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


# ── Détecteur arithmétique NATUREL (pour le chat) ──
_ARITH_KEYWORDS = {
    'combien', 'font', 'font', 'calcule', 'calcul', 'fait', 'vaut', 'resultat',
    'add', 'addition', 'additionne', 'soustrait', 'multiplie', 'divise',
    'plus', 'moins', 'fois', 'divisé', 'divise', 'egale', 'égal',
}

# Pourcentages : "15% de 200", "20 pour cent de 150"
_PCT = re.compile(r'([\d.]+)\s*%\s*(?:de|d\'|sur)?\s*([\d.]+)', re.IGNORECASE)


def detect_and_solve_math(message: str) -> dict:
    """
    Détecte et résout une expression arithmétique en langage naturel.

    Retourne :
      {'handled': True, 'expression': str, 'result': float,
       'method': 'emergence_add'|'emergence_sub'|'emergence_mul'|'emergence_div',
       'explanation': str}
    ou {'handled': False} si pas d'arithmétique.

    Supporte : opérations simples, chaînes gauche-droite, décimaux, négatifs,
    pourcentages ("15% de 200"), et mots ("plus", "fois", "divisé par").
    """
    msg = message.strip()
    low = msg.lower()

    # ── Pourcentage : "15% de 200" ──
    pct = _PCT.search(msg)
    if pct:
        p, base = float(pct.group(1)), float(pct.group(2))
        result = base * p / 100.0
        return {
            'handled': True, 'expression': f"{p}% de {base}",
            'result': result, 'method': 'emergence_pct',
            'explanation': f"{p}% de {base} = {result:g} (émergence ondulatoire)",
        }

    # ── Parenthèses de base : "a*(b/c)", "a*(b+c)", "(a/b)*c" ──
    # Pattern 1 : a*(b op c)     → 4 groupes : a, b, op, c
    pm1 = re.search(r'([\d.]+)\s*\*\s*\(([\d.]+)\s*([+\-*/])\s*([\d.]+)\)', msg)
    # Pattern 2 : (a op b)*c     → 4 groupes : a, op, b, c
    pm2 = re.search(r'\(([\d.]+)\s*([+\-*/])\s*([\d.]+)\)\s*\*\s*([\d.]+)', msg)
    engine = get_harmonic_v3()
    op_fn = {'+': 'add', '-': 'subtract', '*': 'multiply', '/': 'divide'}
    if engine is not None and (pm1 or pm2):
        try:
            if pm1:
                a, b, op_s, c = pm1.groups()
                inner = engine.solve_op(op_fn[op_s], float(b), float(c))
                result = engine.solve_op('multiply', float(a), inner)
                expr = pm1.group(0)
            else:
                a, op_s, b, c = pm2.groups()
                inner = engine.solve_op(op_fn[op_s], float(a), float(b))
                result = engine.solve_op('multiply', inner, float(c))
                expr = pm2.group(0)
            return {
                'handled': True, 'expression': expr,
                'result': result, 'method': 'emergence_paren',
                'explanation': f"{expr} = {result:g} (émergence ondulatoire)",
            }
        except Exception:
            pass

    # ── Traduire les mots en symboles ──
    expr = low
    expr = re.sub(r'divisé\s*par|divise\s*par|divisée\s*par', '/', expr)
    expr = re.sub(r'\bmultiplié\s*par\b|\bmultiplie\s*par\b|\bfois\b', '*', expr)
    expr = re.sub(r'\bplus\b', '+', expr)
    expr = re.sub(r'\bmoins\b', '-', expr)

    # Extraire la première expression arithmétique
    m = re.search(r'(-?\d+\.?\d*)\s*([+\-*/])\s*(-?\d+\.?\d*)'
                  r'(\s*([+\-*/])\s*(-?\d+\.?\d*))*', expr)
    if not m:
        return {'handled': False}

    expression = m.group(0).strip()
    if not expression:
        return {'handled': False}

    # Résoudre gauche-droite
    tokens = re.findall(r'[+\-*/]|[-]?[\d.]+', expression)
    if len(tokens) < 3:
        return {'handled': False}

    engine = get_harmonic_v3()
    if engine is None:
        return {'handled': False}

    idx = 0
    if tokens[idx] in '+-*/':
        current = -float(tokens[idx+1]) if tokens[idx] == '-' else float(tokens[idx+1])
        idx += 2
    else:
        current = float(tokens[idx])
        idx += 1

    ops_used = []
    while idx < len(tokens) - 1:
        op_sym = tokens[idx]
        if tokens[idx+1] in '+-*/':
            sign = -1.0 if tokens[idx+1] == '-' else 1.0
            b = sign * float(tokens[idx+2])
            idx += 1
        else:
            b = float(tokens[idx+1])

        op_map = {'+': 'add', '-': 'subtract', '*': 'multiply', '/': 'divide'}
        op = op_map[op_sym]
        ops_used.append(op)
        current = engine.solve_op(op, current, b)
        idx += 2

    method = 'emergence_' + ('_'.join(ops_used) if ops_used else 'arith')
    return {
        'handled': True, 'expression': expression,
        'result': current, 'method': method,
        'explanation': f"{expression} = {current:g} (émergence ondulatoire, 0 fait stocké)",
        'ops': ops_used,
    }


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
