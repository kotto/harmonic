# -*- coding: utf-8 -*-
"""Axe 3c — SÉLECTEUR À CONFIANCE : consensus fort vs faible.

1. Diagnostic : les 3 corrects A perdus par B→A (B sert une valeur
   FAUSSE là où A était juste) + les corrects B-only.
2. Confiance : re-joue l'émergence en capturant le NOMBRE de stratégies
   qui soutiennent le résultat (consensus ≥2 = fort, 1 = faible).
   → précision servie par niveau de confiance.
3. Sélecteur : B seulement si consensus FORT, sinon A (vA déjà
   sauvegardée — pas de re-run mémoire).
"""
import json
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from word_problem_state import WordProblemStateSolver, _solve_direct, normalize

problems = load_gsm8k()
N = len(problems)

with open('_valeurs_croisement.json', encoding='utf-8') as f:
    data = json.load(f)
vA = data['vA']
vB = data['vB']

exp = []
for p in problems:
    a = p['answer']
    m = None
    import re
    mm = re.search(r'####\s*(-?\d+(?:\.\d+)?)', a)
    m = float(mm.group(1)) if mm else None
    exp.append(m)

def ok(v, e):
    return v is not None and e is not None and abs(v - e) < 1e-6

A = {i for i in range(N) if ok(vA[i], exp[i])}
B = {i for i in range(N) if ok(vB[i], exp[i])}
B_serv = {i for i in range(N) if vB[i] is not None}

# ── 1. Diagnostic des 3 perdus (A juste, B sert FAUX) ───────────────────────
perdus = sorted(i for i in A - B
                if i in B_serv and vA[i] is not None
                and abs(vB[i] - vA[i]) >= 1e-6)
print('== 3 perdus par B→A (A juste, B sert faux) : %d ==' % len(perdus))
for i in perdus:
    print('  [%d] A=%.4g B=%.4g exp=%.4g' % (i, vA[i], vB[i], exp[i]))
    print('      %s' % problems[i]['question'][:130])

# ── 2. Confiance : consensus fort vs faible ─────────────────────────────────
solver = WordProblemStateSolver()
conf = [None] * N          # nombre de stratégies soutenant le résultat B
vB2 = [None] * N
t0 = time.time()
for i in range(N):
    q = problems[i]['question']
    qn = normalize(q)
    strategies = {}
    etat = solver.solve(q, use_compounds=False)
    if etat is not None:
        strategies['etat'] = etat
    composes = solver._solve_compound(qn)
    if composes is not None:
        strategies['composes'] = composes
    directe = _solve_direct(qn)
    if directe is not None:
        strategies['directe'] = directe
    if not strategies:
        continue
    votes = {}
    for name, (result, _steps) in strategies.items():
        votes.setdefault(round(result, 6), []).append(name)
    best_result, backers = max(votes.items(), key=lambda kv: len(kv[1]))
    vB2[i] = best_result
    conf[i] = len(backers)
print('émergence détaillée : %.0f s' % (time.time() - t0))

# cohérence vB2 vs vB (sauvegardé) — contrôle de reproductibilité
same = sum(1 for i in range(N) if vB2[i] == vB[i]
           or (vB2[i] is None and vB[i] is None))
print('cohérence re-run/JSON : %d/%d' % (same, N))

# ── précision par niveau de confiance ────────────────────────────────────────
for c in (1, 2, 3):
    serv = [i for i in range(N) if conf[i] == c]
    corr = sum(1 for i in serv if ok(vB2[i], exp[i]))
    print('confiance %d : servies %d | corrects %d | précision %.1f%%'
          % (c, len(serv), corr, 100.0 * corr / max(1, len(serv))))

# ── 3. Sélecteurs ────────────────────────────────────────────────────────────
# B→A (baseline) — B sert → B ; sinon A
sel = set()
for i in range(N):
    if vB[i] is not None:
        if ok(vB[i], exp[i]):
            sel.add(i)
    elif vA[i] is not None and ok(vA[i], exp[i]):
        sel.add(i)
print()
print('SÉLECTEUR B→A (réf)       : %.1f%% (%d)' % (100.0 * len(sel) / N, len(sel)))

# B-fort→A — B seulement si consensus ≥2 ; sinon A
sel2 = set()
serv2 = 0
for i in range(N):
    if conf[i] is not None and conf[i] >= 2:
        serv2 += 1
        if ok(vB2[i], exp[i]):
            sel2.add(i)
    else:
        if vA[i] is not None and ok(vA[i], exp[i]):
            sel2.add(i)
print('SÉLECTEUR B-fort→A        : %.1f%% (%d) | servies %d | précision %.1f%%'
      % (100.0 * len(sel2) / N, len(sel2), serv2,
         100.0 * len(sel2) / max(1, serv2)))

# B-fort→B-faible→A : B si fort ; B si faible ET A refuse ; sinon A
sel3 = set()
serv3 = 0
for i in range(N):
    if conf[i] is not None:
        if conf[i] >= 2:
            serv3 += 1
            if ok(vB2[i], exp[i]):
                sel3.add(i)
        elif vA[i] is None:          # B faible, A refuse → B quand même
            serv3 += 1
            if ok(vB2[i], exp[i]):
                sel3.add(i)
        else:                        # B faible, A sert → A
            if ok(vA[i], exp[i]):
                sel3.add(i)
    else:
        if vA[i] is not None and ok(vA[i], exp[i]):
            sel3.add(i)
print('SÉLECTEUR B-fort→B-faible→A : %.1f%% (%d) | servies %d | précision %.1f%%'
      % (100.0 * len(sel3) / N, len(sel3), serv3,
         100.0 * len(sel3) / max(1, serv3)))
