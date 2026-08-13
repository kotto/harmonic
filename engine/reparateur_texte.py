#!/usr/bin/env python3
"""
reparateur_texte.py — Correction des traductions DeepSeek par le texte source
=============================================================================

PRINCIPE (piste 1) :

  Le texte source (input) contient la vérité : les nombres et leur rôle.
  La traduction DeepSeek (output) est bruitée : ops manquantes, opérandes
  faux, placeholders 0, entités incohérentes.

  Le réparateur compare les deux profils et corrige la traduction :

    1. NOMBRES DU TEXTE : multiset des nombres (avec % normalisés)
    2. NOMBRES DES OPS   : opérandes réellement utilisés
    3. ÉCARTS :
       • nombre du texte jamais utilisé → op manquante ou opérande faux
       • opérande d'op absent du texte  → valeur précalculée/derivée
       • INIT value=0                   → placeholder à corriger
    4. TYPE DE QUESTION (dernier énoncé) → opération finale attendue

  Réparations appliquées en cascade (chacune mesurée) :
    R1. placeholder INIT(0) avec objet ← nombre du texte voisin
    R2. SUBTRACT après MULTIPLY(f<1) avec opérande hors-texte → opérande = dérivée
    R3. op manquante finale (nombres non utilisés × type de question)

USAGE :
  python reparateur_texte.py --diagnostic
  python reparateur_texte.py --benchmark
"""

import sys, os, re, json, math
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codec_binding import parse_ops, expected_answer, encoder_operations_v2
from codec_trajectoire import decoder_trames

NUM_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(%|percent)?', re.IGNORECASE)


def extraire_nombres_texte(input_text: str) -> List[float]:
    """Multiset des nombres du texte, % normalisés en fractions."""
    nums = []
    for m in NUM_RE.finditer(input_text):
        n = float(m.group(1))
        if m.group(2):
            n /= 100.0
        nums.append(n)
    return nums


def nombres_ops(ops: List[dict]) -> List[float]:
    """Multiset des opérandes numériques réellement utilisés par les ops."""
    nums = []
    for op in ops:
        for key in ('value', 'multiplier', 'per_unit', 'rate',
                    'duration', 'divisor'):
            v = op.get(key)
            if isinstance(v, (int, float)):
                nums.append(float(v))
    return nums


def type_question(input_text: str) -> str:
    """Classe la question par mots-clés du dernier énoncé."""
    q = input_text.split('.')[-1].lower() + input_text.split('?')[-2].lower() \
        if '?' in input_text else input_text.split('.')[-1].lower()
    if 'average' in q or 'per ' in q and 'each' not in q:
        return 'average'
    if 'each' in q or 'per ' in q:
        return 'each'
    if 'how many' in q:
        return 'how_many'
    if 'how much' in q:
        return 'how_much'
    if 'total' in q:
        return 'total'
    if 'left' in q:
        return 'left'
    if 'spend' in q or 'cost' in q or 'pay' in q:
        return 'spend'
    return 'autre'


def diagnostic(dataset: str = 'data/deepseek_distill_test.json',
               limit: Optional[int] = None) -> dict:
    """Compare les profils de nombres texte/ops sur les échecs du codec."""
    d = json.load(open(dataset, encoding='utf-8'))
    stats = Counter()
    repairables = []
    n_fail = 0
    for i, item in enumerate(d):
        if limit and i >= limit:
            break
        ops = parse_ops(item['output'])
        exp = expected_answer(item['answer'])
        if exp is None:
            continue
        got = decoder_trames(encoder_operations_v2(ops, True, False, False))
        if abs(got - exp) < 1e-6:
            continue  # déjà résolu
        n_fail += 1

        txt_nums = extraire_nombres_texte(item['input'])
        op_nums = nombres_ops(ops)
        t = Counter(txt_nums)
        for n in op_nums:
            # retirer de t (consommation approchée)
            for key in list(t.keys()):
                if abs(key - n) < 1e-9 and t[key] > 0:
                    t[key] -= 1
                    if t[key] == 0:
                        del t[key]
                    break
        unused = sorted(t.elements())
        # opérandes hors-texte
        texte_set = set(txt_nums)
        hors_texte = [n for n in op_nums
                      if not any(abs(n - x) < 1e-9 for x in texte_set)
                      and n not in (0.0, 1.0)]
        placeholders = [op for op in ops
                        if op['op'] == 'INIT' and op.get('value', 1) == 0.0]
        tq = type_question(item['input'])

        if unused:
            stats['nombres_non_utilisés'] += 1
        if hors_texte:
            stats['opérandes_hors_texte'] += 1
        if placeholders:
            stats['placeholder_INIT_0'] += 1
        stats[f'question_{tq}'] += 1

        repairables.append({
            'i': i, 'unused': unused, 'hors_texte': hors_texte,
            'placeholders': len(placeholders), 'question': tq,
            'got': got, 'exp': exp,
            'n_ops': len(ops),
        })

    print(f"\n═══ DIAGNOSTIC SUR {n_fail} ÉCHECS ═══")
    print(f"Échecs avec nombres du texte non utilisés : {stats['nombres_non_utilisés']}")
    print(f"Échecs avec opérandes hors-texte          : {stats['opérandes_hors_texte']}")
    print(f"Échecs avec INIT(value=0) placeholder      : {stats['placeholder_INIT_0']}")
    print(f"\nRépartition des types de question :")
    for k in sorted(stats):
        if k.startswith('question_'):
            print(f"  {k[9:]:<12s} : {stats[k]}")
    return {'stats': stats, 'repairables': repairables}


def reparer_et_soudre(item: dict, resolve_rate: bool = True) -> Tuple[float, dict]:
    """
    Réparation complète : R2 (via texte_nums dans l'encodeur) + R3
    (opérations finales manquantes générées à partir des nombres
    inutilisés du texte, classées par score non supervisé).
    """
    ops = parse_ops(item['output'])
    txt_nums = extraire_nombres_texte(item['input'])
    tq = type_question(item['input'])

    # nombres consommés par les ops (INIT inclus)
    used = list(nombres_ops(ops))
    t = Counter(round(v, 6) for v in txt_nums)
    for n in used:
        key = round(n, 6)
        for k in list(t.keys()):
            if abs(k - key) < 1e-9 and t[k] > 0:
                t[k] -= 1
                if t[k] == 0:
                    del t[k]
                break
    unused = sorted(t.elements())

    candidats = [(ops, None)]  # (séquence, dernière op ajoutée)
    if unused:
        for u in set(unused):
            for ope in ('MULTIPLY', 'DIVIDE', 'ADD', 'SUBTRACT'):
                candidats.append((ops + [{'op': ope, 'value': u}], ope))
        if len(unused) >= 2:
            for u1 in set(unused):
                for u2 in set(unused):
                    for ope1 in ('MULTIPLY', 'DIVIDE'):
                        for ope2 in ('MULTIPLY', 'DIVIDE', 'ADD', 'SUBTRACT'):
                            candidats.append((ops + [{'op': ope1, 'value': u1},
                                                     {'op': ope2, 'value': u2}],
                                              ope2))

    def score(resultat, n_add, derniere_op):
        if resultat is None or resultat < 0:
            return -10.0
        s = 0.0
        if abs(resultat - round(resultat)) < 1e-6:
            s += 2.0  # GSM8K : réponses entières
        if derniere_op == 'DIVIDE' and tq in ('each', 'how_many', 'average'):
            s += 1.0
        if derniere_op == 'MULTIPLY' and tq in ('spend', 'how_much'):
            s += 1.0
        if derniere_op == 'SUBTRACT' and tq == 'left':
            s += 1.0
        if n_add == 0:
            s += 3.0  # baseline entière : prior FORT (la traduction
                      # telle quelle est plus fiable qu'un append spéculatif)
        else:
            s -= 0.1 * n_add
        return s

    best = None
    for cand, derniere_op in candidats:
        n_add = len(cand) - len(ops)
        frames = encoder_operations_v2(cand, True, resolve_rate, False, True,
                                       txt_nums)
        r = decoder_trames(frames)
        sc = score(r, n_add, derniere_op)
        if best is None or sc > best[0]:
            best = (sc, r, n_add, derniere_op)
    return best[1], {'n_add': best[2], 'derniere_op': best[3], 'unused': unused,
                     'question': tq}


def benchmark_reparation(dataset: str = 'data/deepseek_distill_test.json',
                         verbose: bool = False) -> dict:
    """Benchmark complet : réparation texte + codec v2."""
    d = json.load(open(dataset, encoding='utf-8'))
    ok, n = 0, 0
    details = []
    for i, item in enumerate(d):
        exp = expected_answer(item['answer'])
        if exp is None:
            continue
        n += 1
        got, info = reparer_et_soudre(item)
        good = abs(got - exp) < 1e-6
        ok += good
        if not good:
            details.append((i, got, exp, info))
    if verbose:
        print("\nÉCHECS RESTANTS (extraits) :")
        for i, got, exp, info in details[:10]:
            print(f"  [{i}] got={got} exp={exp} | unused={info['unused']} "
                  f"q={info['question']} n_add={info['n_add']}")
    return {'ok': ok, 'n': n, 'pct': 100 * ok / n}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--diagnostic', action='store_true')
    p.add_argument('--benchmark', action='store_true')
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    if args.diagnostic:
        diag = diagnostic()
        if args.verbose:
            print("\nEXEMPLES RÉPARABLES (nombres non utilisés) :")
            for r in diag['repairables'][:10]:
                if r['unused']:
                    print(f"  [{r['i']}] unused={r['unused']} hors_texte={r['hors_texte']} "
                          f"q={r['question']} got={r['got']} exp={r['exp']}")

    if args.benchmark:
        r = benchmark_reparation(verbose=args.verbose)
        print(f"\n═══ BENCHMARK RÉPARATION TEXTE ═══")
        print(f"Réparé + codec v2 : {r['ok']}/{r['n']} ({r['pct']:.1f}%)")
