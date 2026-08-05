# -*- coding: utf-8 -*-
"""Axe 1c — INDEX SPECTRAL (PPMI → S¹) avec LOO strict sur les 1319.

Découverte 3.5 du document fondateur : plonger les SLOTS SÉMANTIQUES
(rôles, opérations, directions, catégories d'entités, intention) dans
S¹ via PPMI → SVD. La résonance se fait sur la FORME, pas le lexique.

Jalons à battre :
  JALON profile  top-1 : 1.5% | top-10 : 9.8%
  JALON familles top-1 : 1.3% | top-10 : 6.7%

Mesures :
  1. JALON spectral : retrieve LOO top-1 / top-10 (même métrique).
  2. PASS@1 : famille top-1 → valeur intra-famille (consensus) →
     comparée à la réponse officielle (servies / correctes / refus).
"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import (_extract_final, GSM8KChainMemory, StructureIndex,
                        SpectralStructureIndex, question_numbers,
                        role_numbers)

problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

mem = GSM8KChainMemory()
mem.load()
skel_by_idx = [mem.patterns[i]['chain'].skeleton for i in range(N)]

# ── construction des deux index ─────────────────────────────────────────────
st = StructureIndex(mem)
st.build()
print('familles structurelles :', len(st.families))

si = SpectralStructureIndex(mem)
n_fam = si.build()
print('familles spectrales     :', n_fam)
print('slots plongés (PPMI)    :', len(si._concept_phases))
print('  (%.0f s)' % (time.time() - t0))

# ── 1. JALON spectral — retrieve LOO top-1 / top-10 ─────────────────────────
top1 = top10 = refus = 0
for i in range(N):
    sk_true = skel_by_idx[i]
    hits = si.retrieve(problems[i]['question'], top_k=10, exclude_idx=i)
    if not hits:
        refus += 1
        continue
    skels = [sk for sk, _s in hits]
    if skels[0] == sk_true:
        top1 += 1
    if sk_true in skels:
        top10 += 1
print('JALON spectral top-1 : %.1f%% | top-10 : %.1f%% | refus %d'
      % (100.0 * top1 / N, 100.0 * top10 / N, refus))
print('  (%.0f s)' % (time.time() - t0))

# ── 2. PASS@1 — famille top-1 → consensus intra-famille (LOO) ───────────────
served = correct = refused = 0
for i in range(N):
    exp = _extract_final(problems[i]['answer'])
    if exp is None:
        continue
    hits = si.retrieve(problems[i]['question'], top_k=1, exclude_idx=i)
    if not hits:
        refused += 1
        continue
    sk_top, _score = hits[0]
    fam = st.families.get(sk_top)
    if fam is None:
        refused += 1
        continue
    prof = question_numbers(problems[i]['question'])
    t_roles = [r for _v, r in role_numbers(problems[i]['question'])]
    v = st._family_value(fam, prof, t_roles, max_perms=32, exclude_idx=i)
    if v is None:
        refused += 1
        continue
    served += 1
    if abs(v - exp) < 1e-6:
        correct += 1
print('PASS@1 spectral : %.1f%% (%d) | servies %d | précision servie %.1f%% '
      '| refus %d'
      % (100.0 * correct / N, correct, served,
         100.0 * correct / max(1, served), refused))
print('durée totale : %.0f s' % (time.time() - t0))
