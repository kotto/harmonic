# -*- coding: utf-8 -*-
"""Axe 3 — CROISEMENT des pipelines : mémoire (rôle guidé) vs émergence.

Enregistre les indices des problèmes corrects de chaque pipeline, puis :
  1. Ensemble : |A|, |B|, intersection, A-only, B-only, union (pass@1 combiné).
  2. VOTE par accord : si les deux servent le MÊME résultat → servi ;
     sinon refus (la précision d'accord est la mesure clé).
"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import _extract_final, GSM8KChainMemory
from word_problem_state import solve_consensus

problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

mem = GSM8KChainMemory()
mem.load()

exp = [_extract_final(p['answer']) for p in problems]

# ── Pipeline A : MÉMOIRE (rôle guidé, LOO, min_sources=1) ───────────────────
vA = [None] * N
t = time.time()
for i in range(N):
    if exp[i] is None:
        continue
    vA[i] = mem.solve_role_guided(i, top_k=10, by='profile', min_sources=1)[0]
print('mémoire     : %.0f s' % (time.time() - t))

# ── Pipeline B : ÉMERGENCE (consensus état + composés + directe) ─────────────
vB = [None] * N
t = time.time()
for i in range(N):
    if exp[i] is None:
        continue
    r = solve_consensus(problems[i]['question'])
    vB[i] = r[0] if r is not None else None
print('émergence   : %.0f s' % (time.time() - t))

# ── Analyse ──────────────────────────────────────────────────────────────────
A = {i for i in range(N) if vA[i] is not None and exp[i] is not None
     and abs(vA[i] - exp[i]) < 1e-6}
B = {i for i in range(N) if vB[i] is not None and exp[i] is not None
     and abs(vB[i] - exp[i]) < 1e-6}
print()
print('Mémoire  (A) : %d corrects  (%d servies)'
      % (len(A), sum(1 for i in range(N) if vA[i] is not None)))
print('Émergence (B): %d corrects  (%d servies)'
      % (len(B), sum(1 for i in range(N) if vB[i] is not None)))
print('Intersection : %d | A-only : %d | B-only : %d'
      % (len(A & B), len(A - B), len(B - A)))
print('UNION (pass@1 combiné, oracle) : %.1f%% (%d/%d)'
      % (100.0 * len(A | B) / N, len(A | B), N))

# ── Vote par accord ──────────────────────────────────────────────────────────
served = agreed = correct = 0
for i in range(N):
    if vA[i] is None or vB[i] is None or exp[i] is None:
        continue
    if abs(vA[i] - vB[i]) < 1e-6:
        agreed += 1
        served += 1
        if abs(vA[i] - exp[i]) < 1e-6:
            correct += 1
print()
print('VOTE accord : servies %d | corrects %d | pass@1 %.1f%% '
      '| précision accord %.1f%%'
      % (served, correct, 100.0 * correct / N,
         100.0 * correct / max(1, served)))
print('durée totale : %.0f s' % (time.time() - t0))
