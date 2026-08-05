# -*- coding: utf-8 -*-
"""Exp 6 — Kuramoto sur propositions : le raisonnement = synchronisation.

Tests falsifiables de l'hypothèse « la validité d'un argument est une
propriété de la topologie de couplage, pas des symboles » :

  A. Syllogisme SANS règle de transitivité : C (Socrate mortel) doit
     converger vers 0° par pur effet de topologie.
  B. Contradiction injectée : régime frustré — la cohérence r chute,
     les phases ne se stabilisent plus (battement non résolu).
  C. K sous le niveau de bruit : r n'atteint jamais de point fixe.
  D. N propositions, matrice de couplage réelle (graphe d'implications) :
     la classification par phase doit reproduire la fermeture logique.
  E. Frustration : un conflit interne au cluster vrai fait chuter r
     (détection de contradiction = basse cohérence).
  F. Spectre de K : le mode dominant porte la séparation vrai/faux.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np

from kuramoto_reasoner import KuramotoReasoner, potential

np.set_printoptions(precision=3, suppress=True)

# ═══════════════════════════════════════════════════════════════════════════════
# A. SYLLOGISME (Socrate) — sans règle de transitivité
# ═══════════════════════════════════════════════════════════════════════════════
print('=== A. SYLLOGISME — inférence par topologie, zéro règle ===')
net = KuramotoReasoner(['Socrate', 'Homme', 'Mortel'], kappa=1.0)
net.add_implication('Socrate', 'Homme')      # Socrate est un homme
net.add_implication('Homme', 'Mortel')       # tous les hommes sont mortels
net.anchor('Socrate', True)                  # axiome : Socrate existe/vrai
th, r = net.run(2000, seed=1)
for name, i in net.idx.items():
    print('  %-8s θ = %6.1f° → %s' % (name, np.degrees(th[i] % (2*np.pi)),
                                      net.verdict(th[i])))
print('  cohérence finale r = %.3f' % r[-1])

# ═══════════════════════════════════════════════════════════════════════════════
# B. CONTRADICTION : « Socrate est immortel » (bouton D)
# ═══════════════════════════════════════════════════════════════════════════════
print('\n=== B. CONTRADICTION injectée — régime frustré ===')
netB = KuramotoReasoner(['Socrate', 'Homme', 'Mortel', 'Immortel'], kappa=1.0)
netB.add_implication('Socrate', 'Homme')
netB.add_implication('Homme', 'Mortel')
netB.add_implication('Socrate', 'Immortel')      # l'hypothèse contradictoire
netB.add_contradiction('Mortel', 'Immortel')     # ↔
netB.anchor('Socrate', True)
thB, rB = netB.run(3000, seed=1)
for name, i in netB.idx.items():
    print('  %-8s θ = %6.1f° → %s' % (name, np.degrees(thB[i] % (2*np.pi)),
                                      netB.verdict(thB[i])))
print('  cohérence finale r = %.3f (vs %.3f sans contradiction)'
      % (rB[-1], r[-1]))
print('  r à t=500  : %.3f | à t=3000 : %.3f  (oscille ? → battement non résolu)'
      % (rB[500], rB[-1]))

# ═══════════════════════════════════════════════════════════════════════════════
# C. COUPLAGE SOUS LE BRUIT → pas de convergence
# ═══════════════════════════════════════════════════════════════════════════════
print('\n=== C. Couplage sous le bruit (κ=0.2, σ=5.0) — pas de point fixe ===')
netC = KuramotoReasoner(['Socrate', 'Homme', 'Mortel'], kappa=0.2, sigma=5.0)
netC.add_implication('Socrate', 'Homme')
netC.add_implication('Homme', 'Mortel')
netC.anchor('Socrate', True)
thC, rC = netC.run(4000, seed=7)
print('  r final = %.3f | dernière fenêtre : %.3f ± %.3f (le point fixe '
      'n\'existe pas : le bruit domine le couplage)'
      % (rC[-1], rC[-1000:].mean(), rC[-1000:].std()))
print('  (comparaison κ=1.0, σ=0 : r → 1.000, point fixe stable)')

# ═══════════════════════════════════════════════════════════════════════════════
# D. N PROPOSITIONS : matrice de couplage réelle vs fermeture logique
# ═══════════════════════════════════════════════════════════════════════════════
print('\n=== D. N propositions — accord phase / fermeture logique ===')

def gen_problem(n_true=6, n_false=3, edges_per_node=2, seed=0):
    """Graphe d'implications : cluster VRAI (ancré 0), cluster FAUX (ancré π),
    arêtes dans chaque cluster. La vérité logique d'un nœud = son cluster."""
    rng = np.random.default_rng(seed)
    nodes = [f'v{i}' for i in range(n_true)] + [f'f{i}' for i in range(n_false)]
    idx = {n: i for i, n in enumerate(nodes)}
    g = KuramotoReasoner(nodes, kappa=1.0)
    # ancres : racines de chaque cluster
    for i in range(n_true):
        g.anchor(f'v{i}', True)
    for i in range(n_false):
        g.anchor(f'f{i}', False)
    # arêtes d'implication (DAG par ordre d'index)
    for cl, base in ((range(n_true), 0), (range(n_false), n_true)):
        for i in cl:
            for _ in range(edges_per_node):
                j = int(rng.integers(i + 1, len(cl))) if i + 1 < len(cl) else None
                if j is not None:
                    g.add_implication(nodes[base + i], nodes[base + j])
    return nodes, idx, g


def closure_accuracy(g, steps=1500, seed=0):
    """% de nœuds dont la phase reproduit la vérité de leur cluster, +
    cohérence intra-cluster-vrai (la cohérence GLOBALE r est basse dès
    qu'un cluster FAUX existe : les deux clusters s'annulent en phase)."""
    th, r = g.run(steps, seed=seed)
    ok = total = 0
    true_idx = [i for n, i in g.idx.items() if n.startswith('v')]
    r_true = abs(np.mean(np.exp(1j * th[true_idx])))
    for name, i in g.idx.items():
        expected = 'true' if name.startswith('v') else 'false'
        v = g.verdict(th[i])
        if v == '?':
            continue
        total += 1
        ok += (v == expected)
    return 100.0 * ok / max(1, total), float(r[-1]), float(r_true)


accs, rs_true = [], []
for seed in range(20):
    nodes, idx, g = gen_problem(seed=seed)
    acc, r_fin, r_true = closure_accuracy(g, seed=seed)
    accs.append(acc)
    rs_true.append(r_true)
print('  accords phase/fermeture : moyenne %.1f%% (min %.1f%%)'
      % (np.mean(accs), np.min(accs)))
print('  cohérence intra-cluster-vrai r_true : moyenne %.3f '
      '(le cluster cohérent, isolé du cluster faux)' % np.mean(rs_true))

# ═══════════════════════════════════════════════════════════════════════════════
# E. FRUSTRATION : conflit interne au cluster vrai → r chute
# ═══════════════════════════════════════════════════════════════════════════════
print('\n=== E. Frustration — conflit interne, r comme détecteur ===')

def gen_true_net(seed, conflict=False):
    """Ancres v0, v1 (vraies, 0°), nœuds LIBRES Xi tirés vers 0° par
    v0. Avec conflit : Xi est AUSSI repoussé vers 180° par une
    contradiction avec v1 → nœud libre déchiré entre deux ancres."""
    nodes = [f'v{i}' for i in range(2)] + [f'x{i}' for i in range(4)]
    g = KuramotoReasoner(nodes, kappa=1.0)
    g.anchor('v0', True)
    g.anchor('v1', True)
    for i in range(4):
        g.add_implication('v0', f'x{i}')       # pousse vers 0°
        if conflict:
            g.add_contradiction('v1', f'x{i}')  # repousse vers 180° → conflit
    return g

r_clean, r_frus = [], []
for seed in range(15):
    r_clean.append(closure_accuracy(gen_true_net(seed, False), seed=seed)[1])
    r_frus.append(closure_accuracy(gen_true_net(seed, True), seed=seed)[1])
print('  r final sans conflit : %.3f | avec conflit interne : %.3f'
      % (np.mean(r_clean), np.mean(r_frus)))
print('  séparation : %.1f pts de cohérence (le conflit est lisible dans r)'
      % (100 * (np.mean(r_clean) - np.mean(r_frus))))

# ═══════════════════════════════════════════════════════════════════════════════
# F. SPECTRE DE K : le mode dominant porte la séparation vrai/faux
# ═══════════════════════════════════════════════════════════════════════════════
print('\n=== F. Spectre de la matrice de couplage K ===')
_, _, gF = gen_problem(seed=3)
evals, evecs = np.linalg.eigh(gF.K)
dom = evecs[:, -1]                       # vecteur propre dominant
truth = np.array([1.0 if n.startswith('v') else -1.0 for n in gF.names])
corr = np.corrcoef(np.sign(dom), truth)[0, 1]
print('  valeurs propres de K :', evals)
print('  corrélation (signe du mode dominant | cluster vrai/faux) : %.2f' % corr)
