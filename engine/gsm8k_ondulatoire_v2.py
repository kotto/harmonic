#!/usr/bin/env python3
r"""
🌊 GSM8K ONDULATOIRE v2 — Résonance d'action + Gabarits structurels
====================================================================

Hybride entre la machine à états relationnelle (word_problem_state)
et la sélection d'action par résonance ondulatoire.

INNOVATIONS vs v1 :
  1. Lorsqu'une phrase produit PLUSIEURS actions candidates (ambiguïté),
     on encode la phrase en ONDE et on mesure sa RÉSONANCE avec chaque
     prototype d'action — on choisit la meilleure, pas act[0].

  2. GABARITS STRUCTURELS : 15 motifs récurrents GSM8K encodés comme
     prototypes de séquences d'actions. Si un problème matche un gabarit,
     le contexte oriente la sélection.

  3. ARITHMÉTIQUE ÉMERGENTE : PhaseEncoder (±) + LogEncoder (×÷).

  4. BENCHMARK au niveau PROBLÈME (pas opération).

USAGE :
  python gsm8k_ondulatoire_v2.py --sample 200   # 200 problèmes rapides
  python gsm8k_ondulatoire_v2.py --full          # 1319 problèmes
"""

import sys, os, json, re, time, math
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from word_problem_state import (
    WordProblemStateSolver, normalize, _detect_all, _clean_obj, _num,
)
from wave_lang import encode, superpose, resonate, DEFAULT_DIM

from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PROTOTYPES D'ACTION (encodés comme ondes)
# ═══════════════════════════════════════════════════════════════════════════════

MOTS_ACTION = {
    'init': ['has', 'had', 'have', 'owns', 'started with', 'bought', 'collected',
             'found', 'bakes', 'makes', 'produces', 'harvests', 'there are',
             'there were', 'weighs', 'grows', 'plants', 'purchased', 'packed'],
    'add':  ['buys', 'gains', 'gets', 'receives', 'earns', 'adds', 'more',
             'again', 'additional', 'also', 'another', 'next', 'then', 'picks',
             'collects', 'obtains', 'wins', 'in addition'],
    'sub':  ['sells', 'gives away', 'gives', 'loses', 'spends', 'eats', 'ate',
             'removes', 'takes away', 'dropped', 'uses', 'throws away',
             'left', 'remainder', 'remaining', 'after', 'less', 'fewer',
             'gave', 'donated', 'burned', 'consumed', 'drank'],
    'mult': ['times', 'twice', 'double', 'triple', 'per', 'each', 'every',
             'as many', 'as much', 'product', 'by', 'costs', 'at'],
    'div':  ['divided by', 'split', 'shared equally', 'among', 'half', 'third',
             'quarter', 'each of', 'each person', 'per person', 'evenly',
             'equal parts', 'each receives'],
    'rate': ['per day', 'per hour', 'per week', 'a day', 'a week',
             'every morning', 'every day', 'daily', 'weekly', 'in one day'],
    'money': ['dollar', 'dollars', '$', 'cent', 'cents', 'paid', 'pay',
              'cost', 'costs', 'spend', 'spent', 'money', 'price', 'worth'],
    'total': ['total', 'altogether', 'in all', 'sum', 'combined', 'together',
              'overall', 'entire', 'whole'],
    'relation': ['times as many', 'times as much', 'more than', 'less than',
                 'fewer than', 'as old as', 'half as many', 'difference'],
}

_ACTION_PROTOS: Dict[str, np.ndarray] = {}


def _get_prototypes(dim: int = DEFAULT_DIM) -> Dict[str, np.ndarray]:
    if _ACTION_PROTOS:
        return _ACTION_PROTOS
    for action, mots in MOTS_ACTION.items():
        waves = [encode(m, dim=dim) for m in mots]
        proto = superpose(*waves) if waves else np.zeros(dim)
        _ACTION_PROTOS[action] = proto / (np.linalg.norm(proto) + 1e-9)
    return _ACTION_PROTOS


def _resonance_score(sentence: str, protos: Dict[str, np.ndarray],
                     dim: int = DEFAULT_DIM) -> Dict[str, float]:
    words = [w for w in re.findall(r'[a-zà-ÿ]+', sentence.lower()) if len(w) > 1]
    if not words:
        return {}
    psi = superpose(*[encode(w, dim=dim) for w in words])
    psi = psi / (np.linalg.norm(psi) + 1e-9)
    return {a: float(resonate(psi, p)) for a, p in protos.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GABARITS EXÉCUTABLES (prototypes de séquences GSM8K)
#
# Chaque gabarit contient :
#   kw    : mots-clés pour la résonance ondulatoire
#   ops   : séquence d'opérations à appliquer aux nombres extraits
#   order : comment utiliser les nombres ([0,1]=n0 op n1, [0,1,2]=n0 op n1 op n2)
#   hint  : indice de sélection (ex: 'largest' = utiliser le plus grand nombre)
# ═══════════════════════════════════════════════════════════════════════════════

GABARITS_EXEC = [
    # Simple : N objets à P chacun → N × P
    {'name': 'achat_items', 'ops': ['*'],
     'kw': ['each', 'cost', 'per', 'dollars each', 'how much did', 'spent',
            'total cost', 'buys', 'bought', 'at', 'price', 'paid'],
     'order': [0, 1], 'hint': None},
    # N items × P dollars EACH → actually [1] * [0] for "N items at $P each"
    {'name': 'items_at_price', 'ops': ['*'],
     'kw': ['at', 'each', 'dollars', 'per', 'a piece', 'for'],
     'order': [0, 1], 'hint': 'each_last'},
    # "What is the total cost of N items if each costs P?" → N * P
    {'name': 'each_has', 'ops': ['*'],
     'kw': ['each', 'has', 'have', 'in', 'boxes', 'bags', 'containers', 'total',
            'how many', 'altogether'],
     'order': [0, 1], 'hint': 'largest_first'},
    # Perte : avait N, perd/donne K → N − K
    {'name': 'perte_reste', 'ops': ['-'],
     'kw': ['left', 'remain', 'remaining', 'ate', 'sold', 'gave away',
            'spent', 'lost', 'loses', 'how many left', 'how many remain'],
     'order': [0, 1], 'hint': 'largest_first'},
    # Gain : a N, gagne K → N + K
    {'name': 'gain_accumule', 'ops': ['+'],
     'kw': ['altogether', 'in all', 'total', 'combined', 'together',
            'more', 'additional', 'buys more', 'gets more', 'added'],
     'order': [0, 1], 'hint': None},
    # Production/réduction : produit N par jour, consomme K → N × J − K
    {'name': 'production_jour', 'ops': ['*', '-'],
     'kw': ['per day', 'every day', 'every morning', 'a day', 'lays',
            'bakes', 'makes', 'produces', 'after', 'eats', 'consumes',
            'each day', 'daily', 'days'],
     'order': [0, 1, 2], 'hint': 'prod_rate_days_eat'},
    # Comparaison : A a N, B a K fois plus → N × K ou N + N×K (total)
    {'name': 'comparaison_multi', 'ops': ['*'],
     'kw': ['times as many', 'times as much', 'twice', 'as many as',
            'half as many', 'three times', 'four times', 'as much as'],
     'order': [0, 1], 'hint': 'mult_factor'},
    # Partage égal : N divisé entre K → N / K
    {'name': 'partage_egal', 'ops': ['/'],
     'kw': ['shared equally', 'among', 'split', 'divided equally',
            'each gets', 'each person', 'each child', 'each receives',
            'per person', 'how many each'],
     'order': [0, 1], 'hint': 'largest_first'},
    # Règle de trois : N pour K dollars → M pour X dollars → X = M * K / N
    {'name': 'regle_de_trois', 'ops': ['*', '/'],
     'kw': ['for', 'dollars', 'each', 'cost', 'how many', 'how much',
            'at this rate', 'would'],
     'order': [0, 1, 2], 'hint': 'cross_multiply'},
    # Profit : acheté A, vendu B → B − A
    {'name': 'profit', 'ops': ['-'],
     'kw': ['profit', 'earn', 'bought for', 'sold for', 'how much profit',
            'how much did', 'make'],
     'order': [0, 1], 'hint': 'largest_first'},
    # Pourcentage : N avec K% → N × (1 ± K/100)
    {'name': 'pourcentage', 'ops': ['*'],
     'kw': ['percent', '%', 'off', 'discount', 'sale', 'tip', 'tax',
            'interest', 'reduced by'],
     'order': [0, 1], 'hint': 'percent_calc'},
    # Différence : A a N, B a K → |N − K| (how many more/less)
    {'name': 'difference', 'ops': ['-'],
     'kw': ['how many more', 'how many fewer', 'how many less',
            'what is the difference', 'how much more', 'difference',
            'compared to', 'compare'],
     'order': [0, 1], 'hint': 'largest_first'},
    # Fraction : N, prends K/N → N × K/N  ou  N − N×K/N (reste)
    {'name': 'fraction', 'ops': ['*'],
     'kw': ['half of', 'a third of', 'a quarter of', 'two thirds',
            'three quarters', 'of the', 'kept', 'took', 'gave',
            'fraction'],
     'order': [0, 1], 'hint': 'fraction_of'},
    # Salaire : rate × heures
    {'name': 'salaire', 'ops': ['*'],
     'kw': ['earns', 'per hour', 'per day', 'works', 'hours', 'days',
            'weeks', 'how much', 'salary', 'wages', 'makes'],
     'order': [0, 1], 'hint': None},
]


def _gabarit_scores(q: str, protos: Dict[str, np.ndarray],
                    dim: int = DEFAULT_DIM) -> List[Tuple[dict, float]]:
    words = [w for w in re.findall(r'[a-zà-ÿ]+', q.lower()) if len(w) > 1]
    psi_q = superpose(*[encode(w, dim=dim) for w in words])
    psi_q = psi_q / (np.linalg.norm(psi_q) + 1e-9)
    scores = []
    for g in GABARITS_EXEC:
        gwords = ' '.join(g['kw'])
        kw_words = [w for w in re.findall(r'[a-zà-ÿ]+', gwords.lower()) if len(w) > 1]
        psi_g = superpose(*[encode(w, dim=dim) for w in kw_words])
        psi_g = psi_g / (np.linalg.norm(psi_g) + 1e-9)
        scores.append((g, float(resonate(psi_q, psi_g))))
    scores.sort(key=lambda x: -x[1])
    return scores


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SOLVEUR HYBRIDE
# ═══════════════════════════════════════════════════════════════════════════════




# ── GABARIT EXECUTION ────────────────────────────────────────────────────

def _extract_numbers(text: str) -> list:
    """Extrait tous les nombres d'un texte, dans l'ordre d'apparition."""
    import re as _r
    nums = []
    for m in _r.finditer(r'(\d+(?:\.\d+)?)', normalize(text)):
        v = _num(m.group(1))
        if v > 0 and v not in nums:
            nums.append(v)
    return nums


def _apply_hint(nums: list, hint):
    if not hint or len(nums) < 2:
        return nums
    if hint == 'largest_first':
        huge = max(nums)
        return [huge] + [n for n in nums if n != huge]
    if hint == 'prod_rate_days_eat':
        return nums[:3]
    if hint == 'cross_multiply':
        return nums[:3]
    return nums


def _execute_gabarit(g: dict, nums: list, solver) -> float:
    nums = _apply_hint(nums, g.get('hint'))
    order = g.get('order', [0, 1])
    ops = g.get('ops', ['*'])
    values = [nums[i] for i in order if i < len(nums)]
    if len(values) < 2:
        return None
    result = values[0]
    phase, log = solver.phase, solver.log_enc
    for k, op in enumerate(ops):
        if k + 1 >= len(values):
            break
        b = values[k + 1]
        if op == '+':
            result = phase.add(float(result), float(b))
        elif op == '-':
            result = phase.subtract(float(result), float(b))
        elif op == '*':
            r = log.multiply(float(result), float(b))
            result = r if r is not None else float(result) * float(b)
        elif op == '/':
            r = log.divide(float(result), float(b)) if b != 0 else None
            result = r if r is not None else (float(result) / float(b) if b != 0 else 0.0)
    return float(result)
class OndulatoireGSM8K:
    """Solveur GSM8K hybride : état relationnel + résonance ondulatoire."""

    def __init__(self):
        self.state_solver = WordProblemStateSolver()
        self.phase = PhaseEncoder(500000)
        self.log_enc = LogWaveEncoder(grid_size=2048, SCALE=300.0)
        self.protos = _get_prototypes()
        self.dim = DEFAULT_DIM
        self.stats = {
            'total': 0, 'correct': 0,
            'gabarit_match': 0, 'resonance_used': 0,
            'emergence_ops': 0, 'fallback_ops': 0, 'no_solution': 0,
        }

    def _resonate_best_action(self, sentence: str,
                               candidates: List[Dict]) -> Optional[Dict]:
        if len(candidates) <= 1:
            return candidates[0] if candidates else None
        scores = _resonance_score(sentence, self.protos, self.dim)
        proto_keys = {
            'init': ['init'], 'add': ['add'], 'sub': ['sub'],
            'mult': ['mult', 'money', 'total'],
            'set_mult': ['relation', 'mult'],
            'rel': ['relation', 'mult'],
            'div': ['div'],
            'rate': ['rate'], 'rate_each': ['money', 'rate'],
            'sell_at': ['money'], 'buy_at': ['money'],
            'items_at': ['money', 'mult'], 'pack': ['mult'],
            'frac_of': ['div'], 'each_has': ['mult'],
            'set_plus': ['add'], 'set_minus': ['sub'],
        }
        best_candidate, best_score = candidates[0], -1.0
        for act in candidates:
            keys = proto_keys.get(act.get('op', ''), ['init'])
            sc = max(scores.get(k, 0.0) for k in keys)
            if sc > best_score:
                best_score = sc
                best_candidate = act
        if best_score > 0 and len(candidates) > 1:
            self.stats['resonance_used'] += 1
        return best_candidate

    def solve(self, question: str) -> Optional[float]:
        q = normalize(question)

        # ── Étape 1 : Gabarits exécutables ──
        gabarits = _gabarit_scores(q, self.protos, self.dim)
        if gabarits and gabarits[0][1] > 0.15:
            self.stats['gabarit_match'] += 1
            best_gabarit = gabarits[0][0]
            nums = _extract_numbers(question)
            if len(nums) >= 2:
                result = _execute_gabarit(best_gabarit, nums, self)
                if result is not None:
                    return result

        # ── Étape 2 : Solveur d'état avec résonance ──
        import word_problem_state as wps
        _orig = wps._detect_all
        def _resonant(sentence, last_person=None, last_obj=None):
            candidates = _orig(sentence, last_person, last_obj)
            if len(candidates) <= 1:
                return candidates
            best = self._resonate_best_action(sentence, candidates)
            others = [c for c in candidates if c is not best]
            return [best] + others[:4]
        wps._detect_all = _resonant
        try:
            r = self.state_solver.solve(question, use_compounds=True)
        finally:
            wps._detect_all = _orig
        if r is not None:
            return r[0]

        # ── Étape 3 : Gabarit retry (seuil plus bas) ──
        if gabarits and gabarits[0][1] > 0.10:
            best_gabarit = gabarits[0][0]
            nums = _extract_numbers(question)
            if len(nums) >= 2:
                result = _execute_gabarit(best_gabarit, nums, self)
                if result is not None:
                    return result

        # ── Étape 4 : Consensus fallback ──
        from word_problem_state import solve_consensus
        r = solve_consensus(question)
        return r[0] if r else None


# ═══════════════════════════════════════════════════════════════════════════════
# 4. BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════


def load_gsm8k(path: str = None) -> List[Dict]:
    if path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f]


def benchmark(sample: int = None, quick: bool = False) -> dict:
    solver = OndulatoireGSM8K()
    problems = load_gsm8k()
    if sample:
        import random
        random.seed(42)
        problems = random.sample(problems, min(sample, len(problems)))
    elif quick:
        problems = problems[:200]

    correct, no_sol, total = 0, 0, len(problems)
    times = []

    for i, p in enumerate(problems):
        q = p.get('question', '')
        ans_str = p.get('answer', '')
        expected = None
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
        if m:
            expected = float(m.group(1))

        t0 = time.time()
        result = solver.solve(q)
        dt = (time.time() - t0) * 1000
        times.append(dt)

        if result is None:
            no_sol += 1
        elif expected is not None and abs(result - expected) < 1e-6:
            correct += 1

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{total} — {correct}/{i + 1} "
                  f"correct ({100 * correct / (i + 1):.1f}%) "
                  f"[résonance:{solver.stats['resonance_used']} "
                  f"gabarits:{solver.stats['gabarit_match']}]")

    accuracy = 100 * correct / total if total > 0 else 0.0
    return {
        'accuracy': round(accuracy, 2),
        'correct': correct,
        'total': total,
        'no_solution': no_sol,
        'emergence_ops': solver.stats['emergence_ops'],
        'fallback_ops': solver.stats['fallback_ops'],
        'resonance_used': solver.stats['resonance_used'],
        'gabarit_match': solver.stats['gabarit_match'],
        'avg_ms': round(np.mean(times), 1) if times else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, default=None)
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()

    print("🌊 GSM8K Ondulatoire v2 — Résonance d'action + Gabarits structurels")
    sample = args.sample
    if args.full:
        sample = None
    elif args.quick and sample is None:
        sample = 200

    result = benchmark(sample=sample, quick=args.quick)
    print(f"\n═══ RÉSULTATS GSM8K Ondulatoire v2 ═══")
    print(f"  Problèmes : {result['total']}")
    print(f"  Corrects : {result['correct']}")
    print(f"  Accuracy : {result['accuracy']:.1f}%")
    print(f"  Sans solution : {result['no_solution']}")
    print(f"  Résonance utilisée : {result['resonance_used']}×")
    print(f"  Gabarits matchés : {result['gabarit_match']}")
    print(f"  Ops émergentes : {result['emergence_ops']}")
    print(f"  Ops fallback : {result['fallback_ops']}")
    print(f"  Temps moyen : {result['avg_ms']:.1f} ms")
    print()

    out_path = os.path.join(os.path.dirname(__file__),
                            'data', 'benchmarks', 'gsm8k_ondulatoire_v2.json')
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
    except Exception:
        out_path = 'gsm8k_ondulatoire_v2.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  📊 Rapport : {out_path}")
