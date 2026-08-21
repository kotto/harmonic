#!/usr/bin/env python3
"""
parseur_annotations.py — Extraction des opérations depuis les annotations
==========================================================================

Format GSM8K : « ... 2*20=<<2*20=40>>40 ... » ou « 12+12+20=<<12+12+20=44>>44 »

Le parseur convertit chaque annotation <<expr=result>> en une séquence
d'opérations au format du codec :

  • expressions multi-opérandes chaînées (60/100*150, 12+12+20) décomposées
    en étapes binaires de gauche à droite (mêmes règles de priorité que
    GSM8K : évaluation séquentielle, * et / avant + et - au sein des
    parenthèses — ici sans parenthèses imbriquées)
  • l'opérande gauche du premier pas est INIT si ce n'est pas la chaîne
  • les opérandes droits ne deviennent JAMAIS INIT (sémantique du codec :
    la chaîne porte l'accumulation)
  • '+8' en tête d'annotation = continuation de chaîne (la valeur vient
    d'une étape précédente non annotée)
  • nombres négatifs ('-30') et parenthèses ('1.75-(-1.25)') gérés

USAGE :
  from parseur_annotations import anot2ops
  ops = anot2ops(answer_text)
"""

import re
from typing import List, Dict

ANOT_RE = re.compile(r'<<([^>]+)>>')
OP_MAP = {'+': 'ADD', '-': 'SUBTRACT', '*': 'MULTIPLY', '/': 'DIVIDE'}


def _nettoyer(expr: str) -> str:
    """Enlève parenthèses et normalise les doubles signes."""
    s = expr.replace('(', '').replace(')', '')
    s = re.sub(r'--', '+', s)
    s = re.sub(r'\+-', '-', s)
    s = re.sub(r'-\+', '-', s)
    s = re.sub(r'\+\+', '+', s)
    return s


def anot2ops(answer: str, verbose: bool = False) -> List[dict]:
    """Convertit les annotations <<...>> d'une réponse en opérations."""
    ops: List[dict] = []
    chain = None

    for m in ANOT_RE.finditer(answer):
        expr = m.group(1)
        if '=' not in expr:
            continue
        chain_expr, result_str = expr.split('=', 1)
        try:
            result = float(result_str)
        except ValueError:
            continue

        clean = _nettoyer(chain_expr)

        # '+8' en tête : continuation de chaîne (pas un nouvel INIT)
        if clean.startswith('+'):
            clean = clean[1:]
            if chain is None:
                chain = 0.0

        # nombre négatif en tête : '-30/3' → INIT(-30)
        neg = 1.0
        if clean.startswith('-'):
            clean = clean[1:]
            neg = -1.0

        tokens = re.findall(r'[\+\-\*\/]|\d+(?:\.\d+)?', clean)
        if not tokens:
            continue
        try:
            cur = float(tokens[0]) * neg
        except ValueError:
            continue

        # INIT si la valeur de départ diffère de la chaîne courante
        if chain is None or abs(cur - chain) > 1e-9:
            ops.append({'op': 'INIT', 'value': cur})
            chain = cur

        # Étapes binaires : nombre op nombre op nombre ...
        i = 1
        while i + 1 < len(tokens) + 1 and i + 1 <= len(tokens) - 1:
            if i + 1 >= len(tokens):
                break
            op = tokens[i]
            nxt_str = tokens[i + 1]
            if op not in OP_MAP:
                break
            try:
                nxt = float(nxt_str)
            except ValueError:
                break
            mapped = OP_MAP[op]
            if mapped == 'ADD':
                ops.append({'op': 'ADD', 'value': nxt})
                cur += nxt
            elif mapped == 'SUBTRACT':
                ops.append({'op': 'SUBTRACT', 'value': nxt})
                cur -= nxt
            elif mapped == 'MULTIPLY':
                ops.append({'op': 'MULTIPLY', 'multiplier': nxt})
                cur *= nxt
            elif mapped == 'DIVIDE':
                ops.append({'op': 'DIVIDE', 'divisor': nxt})
                cur = cur / nxt if nxt != 0 else cur
            i += 2

        chain = result

    return ops


def reponse_finale(answer: str) -> float:
    """Extrait la réponse officielle #### N."""
    m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', answer)
    return float(m.group(1)) if m else None


if __name__ == '__main__':
    # Test rapide
    tests = [
        ('2*20=<<2*20=40>>40', 40.0),
        ('60/100*150 = <<60/100*150=90>>90', 90.0),
        ('12+12+20=$<<12+12+20=44>>44', 44.0),
        ('The number of wins is L + <<+8=8>>8.', 8.0),
        ('1.75-(-1.25) = <<1.75-(-1.25)=3>>3', 3.0),
        ('-48+21+(-3) = <<-48+21+(-3)=-30>>-30', -30.0),
    ]
    for answer, attendu in tests:
        ops = anot2ops(answer)
        print(f'{answer}')
        print(f'  → {[o["op"] for o in ops]}')
