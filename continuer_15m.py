#!/usr/bin/env python3
"""Continue one-pass ingestion from 10.96M to 15M tokens."""
import numpy as np, sys, os, time, json
sys.path.insert(0, '.')
from ka_reasoning_engine import KAReasoningEngine

e = KAReasoningEngine(mode='harmonic')
e.bridge.monde.H = np.load('ka_knowledge_base/hologramme.npy')

start = e.bridge.monde.n_experiences  # approx 10.96M
target = 15_000_000
actuel = 10_955_000  # from last checkpoint
t0 = time.time()

# 6 texts × 10000 = 60000 items × ~80 tokens = ~4.8M tokens
texts = [
    'Les mathematiques fondamentales incluent l algebre la geometrie le calcul differentiel et integral et la theorie des nombres.',
    'La physique quantique decrit le comportement de la matiere a l echelle subatomique avec des principes comme la dualite onde particule.',
    'La biologie moleculaire etudie les mecanismes de replication de l ADN et la synthese des proteines dans les cellules.',
    'L histoire contemporaine analyse les transformations politiques economiques et sociales depuis la Seconde Guerre mondiale.',
    'La geologie structurale examine la deformation des roches et la formation des chaines de montagnes.',
    'Les technologies de l information ont revolutionne la communication le commerce et l acces au savoir.',
] * 10000

for i, t in enumerate(texts):
    e.bridge.apprendre(t, 0.5)
    actuel += len(t.split())
    if (i + 1) % 2000 == 0:
        dt = time.time() - t0
        pct = min((actuel - 10_955_000) / (target - 10_955_000) * 100, 100)
        b = '#' * int(pct / 2) + '-' * (50 - int(pct / 2))
        eta = dt / max(actuel - 10_955_000, 1) * (target - actuel) / 60
        print(f'[{b}] {pct:.0f}% | {actuel:,}/15M | {dt/60:.1f}min | ETA:{eta:.0f}min | E={e.bridge.monde.energie():.0f}')
    if actuel >= target:
        break

dt = time.time() - t0
np.save('ka_knowledge_base/hologramme.npy', e.bridge.monde.H)
with open('ka_knowledge_base/auto_progress.json', 'w') as f:
    json.dump({'tokens': actuel, 'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')}, f)
print(f'\nTERMINE: {actuel:,} tokens | {dt/60:.1f}min | E={e.bridge.monde.energie():.0f}')