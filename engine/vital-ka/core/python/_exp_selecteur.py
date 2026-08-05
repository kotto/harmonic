# -*- coding: utf-8 -*-
"""Axe 3b — SÉLECTEUR : émergence prioritaire, sinon mémoire.

Rejoue les deux pipelines en SAUVEGARDANT les valeurs (vA, vB) en JSON
(pour ne plus jamais les recalculer), puis évalue les sélecteurs :

  1. UNION (oracle)   : i correct si A ou B correct.
  2. SÉLECTEUR B→A    : si B sert → B ; sinon A. (refus calibré d'abord)
  3. SÉLECTEUR A→B    : si A sert → A ; sinon B.
  4. Répartition des corrects A-only entre servies-B (perdus) et
     refus-B (récupérables) — l'écart entre union et B→A.
"""
import json
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

exp = [_extract_final(p['answer']) for p in problems]

# ── Pipeline A : MÉMOIRE ─────────────────────────────────────────────────────
mem = GSM8KChainMemory()
mem.load()
vA = [None] * N
t = time.time()
for i in range(N):
    if exp[i] is None:
        continue
    vA[i] = mem.solve_role_guided(i, top_k=10, by='profile', min_sources=1)[0]
print('mémoire   : %.0f s' % (time.time() - t))

# ── Pipeline B : ÉMERGENCE ───────────────────────────────────────────────────
vB = [None] * N
t = time.time()
for i in range(N):
    if exp[i] is None:
        continue
    r = solve_consensus(problems[i]['question'])
    vB[i] = r[0] if r is not None else None
print('émergence : %.0f s' % (time.time() - t))

# ── Sauvegarde (ne plus jamais recalculer) ───────────────────────────────────
with open('_valeurs_croisement.json', 'w', encoding='utf-8') as f:
    json.dump({'vA': vA, 'vB': vB}, f, ensure_ascii=False)
print('sauvegardé : _valeurs_croisement.json')

# ── Analyse ──────────────────────────────────────────────────────────────────
def ok(v, e):
    return v is not None and e is not None and abs(v - e) < 1e-6

A = {i for i in range(N) if ok(vA[i], exp[i])}
B = {i for i in range(N) if ok(vB[i], exp[i])}
B_serv = {i for i in range(N) if vB[i] is not None}
A_serv = {i for i in range(N) if vA[i] is not None}

a_in_refus_b = A - B_serv          # corrects A récupérés quand B refuse
b_in_refus_a = B - A_serv
print()
print('corrects A : %d | corrects B : %d | A∩B : %d' % (len(A), len(B), len(A & B)))
print('UNION (oracle)       : %.1f%% (%d)' % (100.0 * len(A | B) / N, len(A | B)))
print('A-only dans refus-B  : %d / %d (récupérables par B→A)'
      % (len(a_in_refus_b), len(A - B)))
print('B-only dans refus-A  : %d / %d (récupérables par A→B)'
      % (len(b_in_refus_a), len(B - A)))

sel_BA = len(B | a_in_refus_b)      # B prioritaire, sinon A
sel_AB = len(A | b_in_refus_a)      # A prioritaire, sinon B
print()
print('SÉLECTEUR B→A : %.1f%% (%d)   <— émergence d’abord' % (100.0 * sel_BA / N, sel_BA))
print('SÉLECTEUR A→B : %.1f%% (%d)' % (100.0 * sel_AB / N, sel_AB))
print('précision B→A : %.1f%% (sur %d servies)'
      % (100.0 * sel_BA / max(1, len(B_serv | A)), len(B_serv | A)))
print('durée totale : %.0f s' % (time.time() - t0))
