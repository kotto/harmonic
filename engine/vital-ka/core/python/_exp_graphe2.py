# -*- coding: utf-8 -*-
"""Exp 3.1 — Requête RELATIONNELLE ABSTRAITE (structure, pas lexique).

Variante du graphe d'atomes : entités/propriétaires → catégories
(objet, $, personne…) + arêtes causales résultat→entrée entre états.
Test direct de « similarité par configuration relationnelle ».
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from wave_gsm8k import (GSM8KChainMemory, StructureIndex, GraphIndex,
                        extract_atoms, _extract_final)
from benchmark_gsm8k import load_gsm8k

# ── Sanity : atomes ABSTRAITS ───────────────────────────────────────────────
print('=== SANITY atomes (abstraits) ===')
for q in ['Janet sells 9 eggs and each egg costs 2 dollars.',
          'Kylar buys 3 glasses at 5 dollars each.']:
    print(' Q:', q[:70])
    for a in extract_atoms(q, abstract=True):
        print('   ', {k: v for k, v in a.items()})

problems = load_gsm8k()[:100]
mem = GSM8KChainMemory()
mem.load()
st_idx = StructureIndex(mem)
st_idx.build()
gr_abs = GraphIndex(mem, abstract=True)
gr_abs.build()
gr_cau = GraphIndex(mem, abstract=True, causal=True)
n_cau = gr_cau.build()
print('\nGraphes encodés (abstrait) : %d/%d | (abstrait+causal) : %d/%d'
      % (len(gr_abs.psi_graphs), len(mem.patterns), n_cau, len(mem.patterns)))

# ── Jalon : squelette exact en top-k (retrieval GRAPHE strict) ──────────────
for label, gr in [('abstrait', gr_abs), ('abstrait+causal', gr_cau)]:
    top1 = top10 = total = 0
    for i, p in enumerate(problems):
        sk_true = mem.patterns[i]['chain'].skeleton
        hits = gr.retrieve(p['question'], top_k=10, exclude_idx=i)
        skels = [mem.patterns[j]['chain'].skeleton for j, _s in hits]
        total += 1
        if skels and skels[0] == sk_true:
            top1 += 1
        if sk_true in skels:
            top10 += 1
    print('JALON squelette (GRAPHE %-16s) : top-1 %.1f%% | top-10 %.1f%%'
          % (label, 100 * top1 / total, 100 * top10 / total))


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
measure('graphe ABSTRAIT (top-10, fam>=1)',
        lambda i, p: gr_abs.solve(i, top_k=10, min_sources=1)[0])
measure('graphe ABSTRAIT+CAUSAL (top-10, fam>=1)',
        lambda i, p: gr_cau.solve(i, top_k=10, min_sources=1)[0])
measure('graphe ABSTRAIT+CAUSAL (top-10, fam>=2) [gate]',
        lambda i, p: gr_cau.solve(i, top_k=10, min_sources=2)[0])
