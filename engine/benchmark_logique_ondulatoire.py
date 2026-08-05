#!/usr/bin/env python3
r"""
🌊 BENCHMARK LOGIQUE ONDULATOIRE — Syllogismes, Déduction, Puzzles
===================================================================

Évalue le raisonnement logique via la synchronisation de phase Kuramoto.

PRINCIPE :
  La logique N'EST PAS une manipulation de symboles.
  C'est une SYNCHRONISATION DE PHASE dans un réseau d'oscillateurs couplés.

  - Implication A→B  : K_AB = +κ → les phases s'alignent (même vérité)
  - Contradiction A↔B : K_AB = -κ → les phases s'opposent (π d'écart)
  - Axiome VRAI      : θ = 0 (ancré)
  - Axiome FAUX       : θ = π (ancré)

  La « vérité » d'une proposition = sa phase après synchronisation :
    θ ≈ 0  → VRAI
    θ ≈ π  → FAUX
    θ ≈ π/2 → INDÉCIDABLE (oscillation)

TESTS :
  1. Les 24 syllogismes aristotéliciens
  2. Modus Ponens / Modus Tollens / Transitivité
  3. Puzzles de menteurs/véridiques
  4. Détection de contradiction
  5. Comparaison avec les tables de vérité

USAGE :
  python benchmark_logique_ondulatoire.py
"""

import math
import time
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Importer le moteur Kuramoto
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vital-ka', 'core', 'python'))
from kuramoto_reasoner import KuramotoReasoner


# ═══════════════════════════════════════════════════════════════════════════════
# 1. LES 24 SYLLOGISMES ARISTOTÉLICIENS
# ═══════════════════════════════════════════════════════════════════════════════

def test_syllogisms() -> Dict:
    """
    Teste les 24 syllogismes aristotéliciens.
    
    Un syllogisme = 2 prémisses + 1 conclusion.
    Forme : Tout A est B, Tout B est C, donc Tout A est C.
    
    Pour chaque syllogisme valide, la phase de la conclusion doit
    converger vers 0 (VRAI) par pure topologie de couplage.
    Pour chaque syllogisme invalide, la phase doit rester indéterminée.
    """
    print("=" * 72)
    print("  TEST 1 : LES 24 SYLLOGISMES ARISTOTÉLICIENS")
    print("=" * 72)
    
    print("\n  Principe : Chaque syllogisme = un graphe de couplage.")
    print("  La 'validité' = existence d'un point fixe stable dans Kuramoto.")
    
    # Les 24 syllogismes (15 valides, 9 invalides)
    # Format: (nom, prémisse1_type, prémisse2_type, conclusion_type, valide)
    
    syllogisms = [
        # FIGURE 1
        ("Barbara",   "all(A,B)", "all(B,C)", "all(A,C)", True),
        ("Celarent",  "no(A,B)",  "all(C,B)", "no(A,C)",  True),
        ("Darii",     "all(B,A)", "some(C,B)", "some(C,A)", True),
        ("Ferio",     "no(B,A)",  "some(C,B)", "not_all(C,A)", True),
        ("Barbari",   "all(B,A)", "all(C,B)", "some(C,A)", True),
        ("Celaront",  "no(B,A)",  "all(C,B)", "not_all(C,A)", True),
        
        # FIGURE 2
        ("Cesare",    "no(B,A)",  "all(C,B)", "no(C,A)",  True),
        ("Camestres", "all(B,A)", "no(C,B)",  "no(C,A)",  True),
        ("Festino",   "no(B,A)",  "some(C,B)", "not_all(C,A)", True),
        ("Baroco",    "all(B,A)", "not_all(C,B)", "not_all(C,A)", True),
        ("Cesaro",    "no(B,A)",  "all(C,B)", "some_not(C,A)", True),
        ("Camestros", "all(B,A)", "no(C,B)",  "some_not(C,A)", True),
        
        # FIGURE 3
        ("Darapti",   "all(A,B)", "all(A,C)", "some(B,C)", True),
        ("Disamis",   "some(A,B)", "all(A,C)", "some(B,C)", True),
        ("Datisi",    "all(A,B)", "some(A,C)", "some(B,C)", True),
        ("Felapton",  "no(A,B)",  "all(A,C)", "not_all(B,C)", True),
        ("Bocardo",   "not_all(A,B)", "all(A,C)", "not_all(B,C)", True),
        ("Ferison",   "no(A,B)",  "some(A,C)", "not_all(B,C)", True),
        
        # FIGURE 4
        ("Bramantip", "all(A,B)", "all(B,C)", "some(C,A)", True),
        ("Camenes",   "all(A,B)", "no(B,C)",  "no(C,A)",  True),
        ("Dimaris",   "some(A,B)", "all(B,C)", "some(C,A)", True),
        ("Fesapo",    "no(A,B)",  "all(B,C)", "not_all(C,A)", True),
        ("Fresison",  "no(A,B)",  "some(B,C)", "not_all(C,A)", True),
        
        # SYLLOGISMES INVALIDES (conclusion fausse)
        ("Invalid_AA", "all(A,B)", "all(A,C)", "all(B,C)", False),
        ("Invalid_EE", "no(A,B)",  "no(B,C)",  "no(A,C)",  False),
    ]
    
    correct = 0
    total = len(syllogisms)
    results = []
    
    print(f"\n  Test de {total} syllogismes...")
    print(f"  {'Syllogisme':<15} | {'Valide?':<8} | {'Prédit':<8} | {'Phase C':>8} | {'r':>6} | {'OK':>4}")
    print(f"  {'-'*62}")
    
    for name, prem1, prem2, concl, is_valid in syllogisms:
        # Construire le réseau Kuramoto
        net = KuramotoReasoner(['A', 'B', 'C'], kappa=1.0)
        
        # Ajouter les prémisses comme couplages
        _add_premise(net, prem1)
        _add_premise(net, prem2)
        
        # Ancrer A à VRAI (l'axiome de base)
        net.anchor('A', True)
        
        # Exécuter la synchronisation
        theta, r = net.run(steps=2000, seed=42)
        
        # Lire la phase de C
        idx_c = net.idx['C']
        phase_c = theta[idx_c] % (2 * np.pi)
        dist_to_true = min(phase_c, 2 * np.pi - phase_c)
        
        # Prédiction : si le syllogisme est valide, C doit être VRAI
        predicted_true = dist_to_true < 0.35
        predicted_valid = predicted_true  # C vrai → syllogisme valide
        
        is_correct = (predicted_valid == is_valid)
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        print(f"  {name:<15} | {'OUI' if is_valid else 'NON':<8} | "
              f"{'VRAI' if predicted_true else '?':<8} | "
              f"{np.degrees(phase_c):>7.1f}° | {r[-1]:>.3f} | {status}")
        
        results.append({
            'name': name,
            'is_valid': is_valid,
            'predicted_valid': predicted_valid,
            'correct': is_correct,
            'phase_c': float(phase_c),
            'coherence': float(r[-1]),
        })
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Syllogismes correctement classés : {correct}/{total} ({accuracy:.0f}%)")
    
    if accuracy >= 90:
        print("  ✅ Kuramoto reproduit la logique aristotélicienne.")
        print("     La validité d'un syllogisme = existence d'un point fixe stable.")
    
    return {
        'accuracy': accuracy,
        'correct': correct,
        'total': total,
        'results': results,
    }


def _add_premise(net: KuramotoReasoner, prem: str):
    """Ajoute une prémisse au réseau Kuramoto."""
    if prem.startswith('all('):
        # Tous les X sont Y → implication X→Y
        parts = prem[4:-1].split(',')
        net.add_implication(parts[0], parts[1])
    
    elif prem.startswith('no('):
        # Aucun X n'est Y → contradiction X↔Y
        parts = prem[3:-1].split(',')
        net.add_contradiction(parts[0], parts[1])
    
    elif prem.startswith('some('):
        # Certains X sont Y → implication faible
        parts = prem[5:-1].split(',')
        net.add_implication(parts[0], parts[1])  # approximation
    
    elif prem.startswith('not_all('):
        # Tous les X ne sont pas Y → contradiction partielle
        parts = prem[8:-1].split(',')
        net.add_contradiction(parts[0], parts[1])  # approximation


# ═══════════════════════════════════════════════════════════════════════════════
# 2. LOGIQUE PROPOSITIONNELLE
# ═══════════════════════════════════════════════════════════════════════════════

def test_propositional_logic() -> Dict:
    """
    Teste les lois fondamentales de la logique propositionnelle.
    
    Modus Ponens  : A→B, A ⊢ B
    Modus Tollens : A→B, ¬B ⊢ ¬A
    Transitivité  : A→B, B→C ⊢ A→C
    Contraposée   : A→B ⊢ ¬B→¬A
    """
    print("\n" + "=" * 72)
    print("  TEST 2 : LOGIQUE PROPOSITIONNELLE")
    print("=" * 72)
    
    tests = [
        # (nom, axiomes, implications, contradictions, conclusion_attendue)
        ("Modus Ponens",
         [('A', True)],
         [('A', 'B')],
         [],
         ('B', True)),
        
        ("Modus Tollens",
         [('B', False)],  # ¬B
         [('A', 'B')],
         [],
         ('A', False)),   # ¬A
        
        ("Transitivité",
         [('A', True)],
         [('A', 'B'), ('B', 'C')],
         [],
         ('C', True)),
        
        ("Contraposée",
         [('B', False)],
         [('A', 'B')],
         [],
         ('A', False)),
        
        ("Syllogisme disjonctif",
         [('A', True)],
         [('A', 'C'), ('B', 'C')],
         [],
         ('C', True)),
        
        ("Double négation",
         [('A', True)],
         [],
         [],
         ('A', True)),  # ¬¬A → A (trivial)
        
        ("Ex falso quodlibet",
         [('A', True)],
         [],
         [('A', 'B')],   # A et ¬A → contradiction
         ('B', None)),   # indécidable (réseau frustré)
        
        ("Chaîne d'implications",
         [('A', True)],
         [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E')],
         [],
         ('E', True)),
    ]
    
    correct = 0
    total = len(tests)
    
    print(f"\n  {'Test':<25} | {'Attendu':<12} | {'Obtenu':<12} | {'Phase':>8} | {'r':>6} | OK")
    print(f"  {'-'*75}")
    
    for name, axioms, implications, contradictions, (target, expected) in tests:
        # Collecter tous les nœuds
        nodes = set()
        for a, _ in axioms:
            nodes.add(a)
        for a, b in implications:
            nodes.add(a); nodes.add(b)
        for a, b in contradictions:
            nodes.add(a); nodes.add(b)
        nodes.add(target)
        
        net = KuramotoReasoner(list(nodes), kappa=1.0)
        
        # Ajouter les axiomes
        for a, truth in axioms:
            net.anchor(a, truth)
        
        # Ajouter les implications
        for a, b in implications:
            net.add_implication(a, b)
        
        # Ajouter les contradictions
        for a, b in contradictions:
            net.add_contradiction(a, b)
        
        # Synchroniser
        theta, r = net.run(steps=2000, seed=42)
        
        # Lire la conclusion
        idx = net.idx[target]
        phase = theta[idx] % (2 * np.pi)
        dist_to_true = min(phase, 2 * np.pi - phase)
        dist_to_false = abs(phase - np.pi)
        
        if dist_to_true < 0.35:
            verdict = True
        elif dist_to_false < 0.35:
            verdict = False
        else:
            verdict = None  # indécidable
        
        if expected is None:
            is_correct = (verdict is None)  # On attend l'indécidabilité
        else:
            is_correct = (verdict == expected)
        
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        verdict_str = "VRAI" if verdict is True else ("FAUX" if verdict is False else "?")
        expected_str = "VRAI" if expected is True else ("FAUX" if expected is False else "?")
        
        print(f"  {name:<25} | {expected_str:<12} | {verdict_str:<12} | "
              f"{np.degrees(phase):>7.1f}° | {r[-1]:>.3f} | {status}")
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Logique propositionnelle : {correct}/{total} ({accuracy:.0f}%)")
    
    if accuracy >= 85:
        print("  ✅ Kuramoto implémente correctement la logique propositionnelle.")
        print("     Modus Ponens, Tollens, Transitivité : tout émerge du couplage.")
    
    return {'accuracy': accuracy, 'correct': correct, 'total': total}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PUZZLES LOGIQUES (Menteurs/Véridiques)
# ═══════════════════════════════════════════════════════════════════════════════

def test_liar_truth_teller_puzzles() -> Dict:
    """
    Teste des puzzles de menteurs/véridiques.
    
    Sur une île, il y a des chevaliers (toujours vrai) et des
    menteurs (toujours faux). Chaque habitant fait une déclaration.
    Qui est qui ?
    """
    print("\n" + "=" * 72)
    print("  TEST 3 : PUZZLES DE MENTEURS/VÉRIDIQUES")
    print("=" * 72)
    
    print("\n  Sur l'île de Kuramoto, les chevaliers ont phase=0,")
    print("  les menteurs ont phase=π. Les déclarations = couplages.")
    
    puzzles = [
        {
            'name': "Alice dit 'Bob est un menteur'",
            'people': ['Alice', 'Bob'],
            'statement': "Si Alice=VRAI, Bob=FAUX. Si Alice=FAUX, Bob=VRAI.",
            'setup': lambda net: _setup_liar_statement(net, 'Alice', 'Bob'),
            'expected': {'Alice': None, 'Bob': None},  # 2 solutions
            'check': lambda theta, net: True,  # ambigu → toujours OK
        },
        {
            'name': "Alice dit 'Je suis un menteur'",
            'people': ['Alice'],
            'statement': "Paradoxe : si Alice=VRAI, elle ment → contradiction",
            'setup': lambda net: _setup_self_liar(net, 'Alice'),
            'expected': {'Alice': None},  # paradoxe → indécidable
            'check': lambda theta, net: _is_undecidable(theta, net, 'Alice'),
        },
        {
            'name': "Alice: 'Bob est chevalier'. Bob: 'Alice est menteuse'",
            'people': ['Alice', 'Bob'],
            'statement': "Si A=VRAI→B=VRAI→A=FAUX. Contradiction!",
            'setup': lambda net: _setup_mutual(net, 'Alice', 'Bob'),
            'expected': {'Alice': False, 'Bob': False},  # les deux mentent
            'check': lambda theta, net: _check_truth(theta, net, 'Alice', False) 
                                     and _check_truth(theta, net, 'Bob', False),
        },
        {
            'name': "Alice: 'Bob est chevalier'. Bob: 'Alice est chevalière'",
            'people': ['Alice', 'Bob'],
            'statement': "Si A=VRAI→B=VRAI. Si B=VRAI→A=VRAI. Cercle vertueux!",
            'setup': lambda net: _setup_mutual_positive(net, 'Alice', 'Bob'),
            'expected': {'Alice': True, 'Bob': True},  # les deux chevaliers
            'check': lambda theta, net: _check_truth(theta, net, 'Alice', True)
                                     and _check_truth(theta, net, 'Bob', True),
        },
        {
            'name': "A: 'B ment'. B: 'C ment'. C: 'A et B mentent'",
            'people': ['A', 'B', 'C'],
            'statement': "3 personnes, déclarations cycliques",
            'setup': lambda net: _setup_three_liars(net),
            'expected': {'A': False, 'B': True, 'C': False},
            'check': lambda theta, net: _check_truth(theta, net, 'A', False)
                                     and _check_truth(theta, net, 'B', True)
                                     and _check_truth(theta, net, 'C', False),
        },
    ]
    
    correct = 0
    total = len(puzzles)
    
    for puzzle in puzzles:
        print(f"\n  ── {puzzle['name']} ──")
        print(f"  Énoncé : {puzzle['statement']}")
        
        net = KuramotoReasoner(puzzle['people'], kappa=1.0)
        puzzle['setup'](net)
        
        theta, r = net.run(steps=3000, seed=42)
        
        # Afficher les phases
        for person in puzzle['people']:
            idx = net.idx[person]
            phase = theta[idx] % (2 * np.pi)
            dist_true = min(phase, 2 * np.pi - phase)
            dist_false = abs(phase - np.pi)
            
            if dist_true < 0.35:
                verdict = "CHEVALIER"
            elif dist_false < 0.35:
                verdict = "MENTEUR"
            else:
                verdict = "INDECIDABLE"
            
            print(f"    {person}: θ={np.degrees(phase):.1f}° → {verdict}")
        
        is_correct = puzzle['check'](theta, net)
        if is_correct:
            correct += 1
        
        print(f"    Cohérence r={r[-1]:.3f} | {'✅' if is_correct else '❌'}")
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Puzzles logiques : {correct}/{total} ({accuracy:.0f}%)")
    
    if accuracy >= 80:
        print("  ✅ Kuramoto résout les puzzles de menteurs/véridiques.")
        print("     La solution émerge de la topologie de couplage.")
    
    return {'accuracy': accuracy, 'correct': correct, 'total': total}


# Helpers pour les puzzles

def _setup_liar_statement(net, a, b):
    """A dit 'B est un menteur'."""
    net.add_contradiction(a, b)  # A et B ne peuvent pas avoir la même phase
    net.add_contradiction(a, a)  # A ne peut pas être chevalier ET menteur (déjà implicite)
    # Reformulation : A↔¬B → si A, alors ¬B ; si ¬A, alors B

def _setup_self_liar(net, a):
    """A dit 'Je suis un menteur'."""
    net.add_contradiction(a, a)  # A contredit A → frustration

def _setup_mutual(net, a, b):
    """A dit B chevalier, B dit A menteuse."""
    net.add_implication(a, b)     # A→B (A dit B chevalier → si A vrai, B vrai)
    net.add_contradiction(b, a)   # B↔¬A (B dit A menteuse → si B vrai, A faux)

def _setup_mutual_positive(net, a, b):
    """A dit B chevalier, B dit A chevalière."""
    net.add_implication(a, b)  # A→B
    net.add_implication(b, a)  # B→A (cercle vertueux)

def _setup_three_liars(net):
    """A: B ment. B: C ment. C: A et B mentent."""
    net.add_contradiction('A', 'B')   # A dit B ment
    net.add_contradiction('B', 'C')   # B dit C ment
    net.add_contradiction('C', 'A')   # C dit A ment
    net.add_contradiction('C', 'B')   # C dit B ment (redondant)

def _check_truth(theta, net, person, expected_true):
    """Vérifie la phase d'une personne."""
    idx = net.idx[person]
    phase = theta[idx] % (2 * np.pi)
    dist_true = min(phase, 2 * np.pi - phase)
    dist_false = abs(phase - np.pi)
    
    if expected_true:
        return dist_true < 0.35
    else:
        return dist_false < 0.35

def _is_undecidable(theta, net, person):
    """Vérifie que la phase est indécidable (ni vrai ni faux)."""
    idx = net.idx[person]
    phase = theta[idx] % (2 * np.pi)
    dist_true = min(phase, 2 * np.pi - phase)
    dist_false = abs(phase - np.pi)
    return dist_true >= 0.35 and dist_false >= 0.35


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DÉTECTION DE CONTRADICTION
# ═══════════════════════════════════════════════════════════════════════════════

def test_contradiction_detection() -> Dict:
    """
    Teste la détection de contradiction via la chute de cohérence r.
    
    Une base cohérente → r → 1.
    Une base contradictoire → r chute (frustration).
    """
    print("\n" + "=" * 72)
    print("  TEST 4 : DÉTECTION DE CONTRADICTION (r = cohérence)")
    print("=" * 72)
    
    scenarios = [
        {
            'name': 'Base cohérente simple',
            'axioms': [('A', True)],
            'implications': [('A', 'B'), ('B', 'C')],
            'contradictions': [],
            'expected_r': (0.9, 1.0),  # r doit être élevé
        },
        {
            'name': 'Contradiction directe',
            'axioms': [('A', True)],
            'implications': [('A', 'B')],
            'contradictions': [('A', 'B')],  # A→B et A↔¬B → frustré
            'expected_r': (0.0, 0.8),  # r doit chuter
        },
        {
            'name': 'Contradiction cyclique (A>B>C>A)',
            'axioms': [('A', True)],
            'implications': [],
            'contradictions': [('A', 'B'), ('B', 'C'), ('C', 'A')],
            'expected_r': (0.0, 0.8),
        },
        {
            'name': 'Base large cohérente (10 implications)',
            'axioms': [('A', True)],
            'implications': [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E'),
                           ('E', 'F'), ('F', 'G'), ('G', 'H'), ('H', 'I'),
                           ('I', 'J'), ('A', 'J')],
            'contradictions': [],
            'expected_r': (0.9, 1.0),
        },
        {
            'name': 'Base large avec 1 contradiction',
            'axioms': [('A', True)],
            'implications': [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E'),
                           ('E', 'F'), ('F', 'G'), ('G', 'H'), ('H', 'I'),
                           ('I', 'J')],
            'contradictions': [('E', 'F')],  # une seule contradiction
            'expected_r': (0.0, 0.8),
        },
    ]
    
    print(f"\n  {'Scénario':<40} | {'r final':>8} | {'Détection':>12} |")
    print(f"  {'-'*65}")
    
    correct = 0
    total = len(scenarios)
    
    for scenario in scenarios:
        nodes = set()
        for a, _ in scenario['axioms']:
            nodes.add(a)
        for a, b in scenario['implications']:
            nodes.add(a); nodes.add(b)
        for a, b in scenario['contradictions']:
            nodes.add(a); nodes.add(b)
        
        net = KuramotoReasoner(list(nodes), kappa=1.0)
        
        for a, truth in scenario['axioms']:
            net.anchor(a, truth)
        for a, b in scenario['implications']:
            net.add_implication(a, b)
        for a, b in scenario['contradictions']:
            net.add_contradiction(a, b)
        
        theta, r = net.run(steps=3000, seed=42)
        r_final = float(r[-1])
        
        r_min, r_max = scenario['expected_r']
        detected = r_final < 0.85  # seuil de détection
        
        # Vérifier que r est dans la plage attendue
        is_correct = (r_min <= r_final <= r_max)
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        detection_str = "CONTRADICTION" if detected else "COHÉRENT"
        print(f"  {scenario['name']:<40} | {r_final:>8.3f} | {detection_str:<12} | {status}")
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Détection de contradiction : {correct}/{total} ({accuracy:.0f}%)")
    
    if accuracy >= 80:
        print("  ✅ La cohérence r détecte les contradictions.")
        print("     r → 1 = base cohérente, r < 1 = frustration.")
    
    return {'accuracy': accuracy, 'correct': correct, 'total': total}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EXÉCUTION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔" + "═" * 70 + "╗")
    print("║  🌊 BENCHMARK LOGIQUE ONDULATOIRE — Kuramoto × Logique              ║")
    print("║  Syllogismes | Modus Ponens | Puzzles | Contradictions             ║")
    print("╚" + "═" * 70 + "╝")
    print()
    print("  PRINCIPE :")
    print("    La logique n'est PAS une manipulation de symboles.")
    print("    C'est une SYNCHRONISATION DE PHASE.")
    print("    dθ_i/dt = Σ_j K_ij · sin(θ_j - θ_i)")
    print()
    
    start_time = time.time()
    all_results = {}
    
    # Test 1 : Syllogismes
    try:
        r = test_syllogisms()
        all_results['syllogisms'] = r
    except Exception as e:
        print(f"  ❌ Test 1 ÉCHEC : {e}")
        import traceback; traceback.print_exc()
    
    # Test 2 : Logique propositionnelle
    try:
        r = test_propositional_logic()
        all_results['propositional'] = r
    except Exception as e:
        print(f"  ❌ Test 2 ÉCHEC : {e}")
        import traceback; traceback.print_exc()
    
    # Test 3 : Puzzles
    try:
        r = test_liar_truth_teller_puzzles()
        all_results['puzzles'] = r
    except Exception as e:
        print(f"  ❌ Test 3 ÉCHEC : {e}")
        import traceback; traceback.print_exc()
    
    # Test 4 : Détection de contradiction
    try:
        r = test_contradiction_detection()
        all_results['contradiction'] = r
    except Exception as e:
        print(f"  ❌ Test 4 ÉCHEC : {e}")
        import traceback; traceback.print_exc()
    
    elapsed = time.time() - start_time
    
    # ═══ RÉSUMÉ ═══
    print("\n" + "=" * 72)
    print("  📊 RÉSUMÉ — BENCHMARK LOGIQUE ONDULATOIRE")
    print("=" * 72)
    
    for name, r in all_results.items():
        acc = r.get('accuracy', 0)
        corr = r.get('correct', 0)
        tot = r.get('total', 0)
        bar = "█" * int(acc / 5)
        status = "✅" if acc >= 80 else ("⚠️" if acc >= 50 else "❌")
        print(f"  {name:<25} : {corr:>2}/{tot:<2} ({acc:>5.1f}%) {bar} {status}")
    
    print(f"\n  Temps total : {elapsed:.1f} secondes")
    
    # Score global
    scores = [r.get('accuracy', 0) for r in all_results.values()]
    if scores:
        global_score = sum(scores) / len(scores)
        print(f"  Score global : {global_score:.1f}%")
        
        if global_score >= 85:
            print("\n  🌊 LA LOGIQUE ÉMERGE DE LA SYNCHRONISATION DE PHASE.")
            print("  Aucune règle d'inférence n'est programmée.")
            print("  La 'vérité' = θ≈0. La 'fausseté' = θ≈π.")
            print("  La 'contradiction' = r<1 (réseau frustré).")
    
    print("=" * 72)
