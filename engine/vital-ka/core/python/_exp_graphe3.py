# -*- coding: utf-8 -*-
"""Exp 3.2 — Classement STRUCTUREL dans le voisinage relationnel.

Le top-1 était gelé à 2.0% (toute requête). Ici on change la FONCTION
DE CLASSEMENT, pas la requête : résonance brute (linear) vs alignement
de configuration (fit, Jaccard structurel) vs fusion (blend).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from wave_gsm8k import (GSM8KChainMemory, GraphIndex, _extract_final)
from benchmark_gsm8k import load_gsm8k

problems = load_gsm8k()[:100]
mem = GSM8KChainMemory()
mem.load()
gr = GraphIndex(mem, abstract=True, causal=True)
gr.build()
print('Graphes encodés (abstrait+causal) :', len(gr.psi_graphs))

# ── Jalon : squelette exact en top-k (3 fonctions de classement) ────────────
for rank in ('linear', 'fit', 'blend'):
    top1 = top10 = total = 0
    for i, p in enumerate(problems):
        sk_true = mem.patterns[i]['chain'].skeleton
        hits = gr.retrieve(p['question'], top_k=10, exclude_idx=i, rank=rank)
        skels = [mem.patterns[j]['chain'].skeleton for j, _s in hits]
        total += 1
        if skels and skels[0] == sk_true:
            top1 += 1
        if sk_true in skels:
            top10 += 1
    print('JALON squelette (rank=%-8s) : top-1 %.1f%% | top-10 %.1f%%'
          % (rank, 100 * top1 / total, 100 * top10 / total))


def measure(label, fn):
    served = correct = refused = 0
    for i, p in enumerate(problems):
        exp = _extract_final(p['answer'])
        if exp is None:
            continue
        v = fn(i, p)
        if v is None:
            refused += 1
            continue
        served += 1
        if abs(v - exp) < 1e-6:
            correct += 1
    print('%-52s pass@1 %.1f%% (%d) | servies %d | précision servie %.1f%% | refus %d'
          % (label, 100.0 * correct / len(problems), correct, served,
             100.0 * correct / max(1, served), refused))


print('\n=== PASS@1 (100) — leave-one-out STRICT ===')
measure('rôle guidé (profil, top-10, fam>=1) [réf]',
        lambda i, p: mem.solve_role_guided(i, top_k=10, by='profile',
                                           min_sources=1)[0])
measure('graphe rank=fit (top-10, fam>=1)',
        lambda i, p: gr.solve(i, top_k=10, min_sources=1, rank='fit')[0])
measure('graphe rank=blend (top-10, fam>=1)',
        lambda i, p: gr.solve(i, top_k=10, min_sources=1, rank='blend')[0])
measure('graphe rank=blend (top-10, fam>=2) [gate]',
        lambda i, p: gr.solve(i, top_k=10, min_sources=2, rank='blend')[0])
