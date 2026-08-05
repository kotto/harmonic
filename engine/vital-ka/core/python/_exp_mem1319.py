# -*- coding: utf-8 -*-
"""Axe 1b — MÉMOIRE (retrieval) avec LOO strict sur les 1319.

Comparaison équitable avec l'émergence pas-à-pas (1.4%) :
  1. ORACLE LOO : le squelette du problème existe-t-il ailleurs ?
  2. JALON squelette : retrieve by='profile' (top-1 / top-10, LOO).
  3. JALON familles : StructureIndex (top-1 / top-10, LOO).
  4. PASS@1 : solve_role_guided(by='profile', min_sources=1) sur 1319.
"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import _extract_final, GSM8KChainMemory, StructureIndex

problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

mem = GSM8KChainMemory()
mem.load()
skel_by_idx = [mem.patterns[i]['chain'].skeleton for i in range(N)]

# ── 1. ORACLE LOO (squelette présent ailleurs dans la base) ────────────────
seen = {}
for sk in skel_by_idx:
    seen[sk] = seen.get(sk, 0) + 1
exact = sum(1 for sk in skel_by_idx if seen[sk] >= 2)
print('ORACLE LOO exact : %.1f%% (%d/%d)' % (100.0 * exact / N, exact, N))

# ── 2. JALON profile (retrieval, LOO) ──────────────────────────────────────
top1 = top10 = 0
for i in range(N):
    sk_true = skel_by_idx[i]
    hits = mem.retrieve(problems[i]['question'], exclude=i, top_k=10,
                        by='profile')
    skels = [skel_by_idx[j] for j, _s in hits]
    if skels and skels[0] == sk_true:
        top1 += 1
    if sk_true in skels:
        top10 += 1
print('JALON profile   top-1 : %.1f%% | top-10 : %.1f%%'
      % (100.0 * top1 / N, 100.0 * top10 / N))
print('  (%.0f s)' % (time.time() - t0))

# ── 3. JALON familles (StructureIndex, LOO) ─────────────────────────────────
st = StructureIndex(mem)
st.build()
print('familles structurelles :', len(st.families))
top1f = top10f = 0
for i in range(N):
    sk_true = skel_by_idx[i]
    fams = st.retrieve(problems[i]['question'], top_k=10, exclude_idx=i)
    skels_f = [f for f, _s in fams]
    if skels_f and skels_f[0] == sk_true:
        top1f += 1
    if sk_true in skels_f:
        top10f += 1
print('JALON familles  top-1 : %.1f%% | top-10 : %.1f%%'
      % (100.0 * top1f / N, 100.0 * top10f / N))
print('  (%.0f s)' % (time.time() - t0))

# ── 4. PASS@1 — solve_role_guided sur les 1319 (LOO) ───────────────────────
served = correct = refused = 0
for i in range(N):
    exp = _extract_final(problems[i]['answer'])
    if exp is None:
        continue
    v, _nsrc, _sk = mem.solve_role_guided(i, top_k=10, by='profile',
                                          min_sources=1)
    if v is None:
        refused += 1
        continue
    served += 1
    if abs(v - exp) < 1e-6:
        correct += 1
print('PASS@1 rôle guidé (profile, LOO) : %.1f%% (%d) | servies %d | '
      'précision servie %.1f%% | refus %d'
      % (100.0 * correct / N, correct, served,
         100.0 * correct / max(1, served), refused))
print('durée totale : %.0f s' % (time.time() - t0))
