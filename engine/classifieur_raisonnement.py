#!/usr/bin/env python3
"""
classifieur_raisonnement.py — Classification des types de raisonnement
par filtres adaptés harmoniques.

PRINCIPE (même correction que le passage v1→v2 en arithmétique) :
  La FFT brute sur des signaux courts avec fréquences non commensurables
  produit des fuites spectrales (CORR domine artificiellement).
  La solution : FILTRE ADAPTÉ (corrélation exacte par forme d'onde).

  Chaque type de raisonnement a une TRAJECTOIRE ψ caractéristique :
    - séquence d'opérations (profil opératoire)
    - chaque opération a un ANGLE DE DÉPLACEMENT harmonique unique
    - la séquence des angles identifie le type de raisonnement
    - un classifieur par corrélation détecte quel type de raisonnement
      est le plus proche de la trajectoire observée

USAGE :
  python classifieur_raisonnement.py
"""

import sys, os, math, cmath, json
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from raisonnement_harmonique import PRIMITIVES, encoder_raisonnement, PHI

# ═══════════════════════════════════════════════════════════════════════════
# 1. SCHÉMAS DE RAISONNEMENT CANONIQUES (trajectoires de référence)
# ═══════════════════════════════════════════════════════════════════════════

# Chaque schéma = séquence d'opérations avec leur ANGLE harmonique
# angle = 2π × freq / φ  (normalisé dans [0, 2π))

def angle_operation(op: str) -> float:
    """Angle harmonique de l'opération : 2π × freq / φ."""
    freq = PRIMITIVES.get(op, {}).get('freq', 0.5)
    return (2 * math.pi * abs(freq) / PHI) % (2 * math.pi)


SCHEMAS = {
    'deductif': {
        'ops': [('ASSERT', 1.0), ('FORALL', 1.0), ('INST', 0.6), ('IMPLY', 0.9)],
        'description': "Syllogisme : Socrate est un homme → ∀x Homme(x)⇒Mortel(x) → Mortel(Socrate)",
        'domaine': 'logique',
    },
    'causal': {
        'ops': [('CAUSE', 1.0), ('ASSERT', 0.7), ('EFFET', 0.9), ('CONTRE', 0.3)],
        'description': "Causalité : pluie → croissance, observé, contrefactuel",
        'domaine': 'causalite',
    },
    'analogique': {
        'ops': [('MAP', 1.0), ('ABSTR', 0.7), ('INFER', 0.9), ('CONCR', 0.5)],
        'description': "Analogie : atome = système solaire (mapping → abstraction → inférence)",
        'domaine': 'analogie',
    },
    'abductif': {
        'ops': [('EFFET', 0.8), ('HYPOTH', 0.9), ('CAUSE', 0.7), ('VERIF', 0.6)],
        'description': "Abduction : symptômes → hypothèse → cause → vérification",
        'domaine': 'causalite',
    },
    'inductif': {
        'ops': [('ASSERT', 0.5), ('ASSERT', 0.5), ('GEN', 0.8), ('CORR', 0.6)],
        'description': "Induction : observations → généralisation → corrélation",
        'domaine': 'logique',
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RAISONNEMENT JURIDIQUE
    # ═══════════════════════════════════════════════════════════════════════════
    'juridique_syllogisme': {
        'ops': [('FAIT', 0.8), ('NORME', 1.0), ('QUALIF', 0.9), ('IMPLY', 0.7)],
        'description': "Syllogisme juridique : fait → norme → qualification → conclusion",
        'domaine': 'juridique',
    },
    'juridique_conflit': {
        'ops': [('NORME', 1.0), ('NORME', 1.0), ('CONFLIT', 0.9), ('PONDERE', 0.8)],
        'description': "Conflit de normes : deux règles contradictoires, balancement",
        'domaine': 'juridique',
    },
    'juridique_precedent': {
        'ops': [('FAIT', 0.7), ('PRECED', 0.9), ('DISTING', 0.6), ('QUALIF', 0.8)],
        'description': "Raisonnement par précédent : fait → précédent → distinction → qualification",
        'domaine': 'juridique',
    },
    'juridique_interpretation': {
        'ops': [('NORME', 0.9), ('INTERPR', 1.0), ('FAIT', 0.7), ('QUALIF', 0.8)],
        'description': "Interprétation : norme ambiguë → interprétation → fait → qualification",
        'domaine': 'juridique',
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RAISONNEMENT MÉDICAL
    # ═══════════════════════════════════════════════════════════════════════════
    'medical_diagnostic': {
        'ops': [('SYMPT', 0.7), ('SIGNE', 0.6), ('DIFF', 0.9), ('CONFIRM', 0.8),
                ('TRAIT', 0.7)],
        'description': "Diagnostic : symptôme → signe → différentiel → confirmation → traitement",
        'domaine': 'medical',
    },
    'medical_differentiel': {
        'ops': [('SYMPT', 0.7), ('DIFF', 0.9), ('EXCLURE', 0.8), ('CONFIRM', 0.8)],
        'description': "Diagnostic différentiel : symptôme → hypothèses → exclusion → confirmation",
        'domaine': 'medical',
    },
    'medical_pronostic': {
        'ops': [('DIFF', 0.8), ('TRAIT', 0.7), ('PROGN', 0.9), ('RECID', 0.5)],
        'description': "Pronostic : diagnostic → traitement → pronostic → risque de récidive",
        'domaine': 'medical',
    },
    'medical_comorbidite': {
        'ops': [('ANTEC', 0.6), ('COMORB', 0.8), ('DIFF', 0.7), ('TRAIT', 0.9)],
        'description': "Comorbidité : antécédents → comorbidités → diagnostic adapté → traitement",
        'domaine': 'medical',
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# 2. ENCODEUR PROPRE : trames par transition
# ═══════════════════════════════════════════════════════════════════════════

def encoder_reasoning(schema: List[Tuple[str, float]]) -> List[dict]:
    """Encode un raisonnement en TRAMES ψ (comme le codec arithmétique).

    Chaque opération émet 2 trames :
      1. Montée d'étage : amp=1.0, phase=π/2 (structure)
      2. Déplacement     : amp=profondeur, phase=angle_harmonique (contenu)
    """
    trames = []
    for op, profondeur in schema:
        angle = angle_operation(op)
        # Montée d'étage
        trames.append({'code': op, 'amp': 1.0, 'phase': math.pi / 2,
                       'type': 'structure', 'value': None})
        # Déplacement (le contenu de l'opération)
        trames.append({'code': op, 'amp': profondeur, 'phase': angle,
                       'type': 'contenu', 'value': op})
    return trames


def decoder_trajectoire(trames: List[dict]) -> List[complex]:
    """Décode la trajectoire par somme cumulative (exact)."""
    z = 0.0 + 0.0j
    points = [z]
    for t in trames:
        z += t['amp'] * cmath.exp(1j * t['phase'])
        points.append(z)
    return points


# ═══════════════════════════════════════════════════════════════════════════
# 3. CLASSIFIEUR PAR FILTRES ADAPTÉS
# ═══════════════════════════════════════════════════════════════════════════

def detecter_operations_par_angle(points: List[complex]) -> List[Tuple[str, float]]:
    """Détecte les opérations par l'angle des déplacements horizontaux.

    Retourne une liste de (opération, domaine) pour chaque déplacement
    horizontal détecté.
    """
    ops_detectees = []
    for k in range(1, len(points)):
        delta = points[k] - points[k - 1]
        angle = cmath.phase(delta) % (2 * math.pi)
        amp = abs(delta)

        if abs(angle - math.pi / 2) < 0.3 or amp < 0.01:
            continue

        # Matcher l'angle à l'opération la plus proche
        meilleur_op, meilleur_score, meilleur_dom = None, float('inf'), None
        for op, info in PRIMITIVES.items():
            angle_ref = angle_operation(op)
            diff = min(abs(angle - angle_ref), 2 * math.pi - abs(angle - angle_ref))
            if diff < meilleur_score:
                meilleur_score = diff
                meilleur_op = op
                meilleur_dom = info.get('domaine', '?')

        ops_detectees.append((meilleur_op, meilleur_dom))

    return ops_detectees


def classer_par_trajectoire(points: List[complex]) -> Tuple[str, str, float]:
    """Classe le raisonnement par CORRÉLATION DE TRAJECTOIRE COMPLÈTE.

    Pour chaque schéma de référence, génère sa trajectoire ψ et calcule
    la corrélation entre la trajectoire test et la trajectoire de référence.
    Le schéma avec la meilleure corrélation est le classement retenu.

    Cette méthode contourne le problème de détection individuelle des
    opérations : c'est la FORME GLOBALE de la trajectoire qui identifie
    le type de raisonnement, pas les angles individuels.
    """
    meilleur_schema, meilleur_score, meilleur_domaine = None, 0.0, None

    for nom_schema, info in SCHEMAS.items():
        # Générer la trajectoire de référence
        trames_ref = encoder_reasoning(info['ops'])
        points_ref = decoder_trajectoire(trames_ref)

        # Aligner les deux trajectoires à la même longueur
        n = min(len(points), len(points_ref))
        if n < 3:
            continue

        # Normaliser les amplitudes
        x_test = np.array([p.real for p in points[:n]])
        x_ref = np.array([p.real for p in points_ref[:n]])
        x_test = (x_test - np.mean(x_test)) / (np.std(x_test) + 1e-9)
        x_ref = (x_ref - np.mean(x_ref)) / (np.std(x_ref) + 1e-9)

        # Corrélation croisée normalisée
        corr = np.correlate(x_test, x_ref, mode='valid')[0]
        correlation = corr / n  # normalisé

        # Bonus si le domaine correspond
        score = (correlation + 1) / 2  # normalisé dans [0, 1]

        if score > meilleur_score:
            meilleur_score = score
            meilleur_schema = nom_schema
            meilleur_domaine = info.get('domaine', '?')

    return meilleur_schema, meilleur_domaine, meilleur_score


def classer_raisonnement(ops_detectees: List[Tuple[str, float]],
                          points: Optional[List[complex]] = None) -> Tuple[str, float]:
    """Classe le raisonnement par DICE sur les opérations, avec
    renforcement par corrélation de trajectoire quand disponible."""
    if not ops_detectees:
        return 'inconnu', 0.0

    # Si on a la trajectoire, utiliser la corrélation
    if points is not None:
        schema, domaine, score = classer_par_trajectoire(points)
        if score > 0.5:
            return schema, score

    # Fallback DICE (quand la corrélation ne donne pas de résultat clair)
    domaines = Counter(d for _, d in ops_detectees)
    domaine_principal = domaines.most_common(1)[0][0]
    ops_seules = [op for op, _ in ops_detectees]

    candidats = [(nom, info) for nom, info in SCHEMAS.items()
                 if info.get('domaine', '') == domaine_principal]
    if not candidats:
        candidats = list(SCHEMAS.items())

    meilleur_schema, meilleur_score = None, 0.0
    for nom_schema, info in candidats:
        ops_ref = [o for o, _ in info['ops']]
        detect = Counter(ops_seules)
        ref = Counter(ops_ref)
        intersect = sum((detect & ref).values())
        union = sum((detect | ref).values())
        dice = 2 * intersect / (intersect + union) if (intersect + union) > 0 else 0.0

        ordre_bonus = 0.0
        for i, (op, _) in enumerate(info['ops']):
            if op in ops_seules:
                pos = ops_seules.index(op) / len(ops_seules)
                pos_attendue = i / len(info['ops'])
                ordre_bonus += max(0, 1.0 - abs(pos - pos_attendue))

        score = dice + 0.3 * ordre_bonus / len(info['ops'])
        if score > meilleur_score:
            meilleur_score = score
            meilleur_schema = nom_schema

    return meilleur_schema, meilleur_score


# ═══════════════════════════════════════════════════════════════════════════
# 4. TEST COMPLET
# ═══════════════════════════════════════════════════════════════════════════

def test_complet():
    print("═══ CLASSIFIEUR DE RAISONNEMENT PAR FILTRES ADAPTÉS ═══\n")
    print(f"{'RAISONNEMENT':<30s} {'DÉTECTÉ':<20s} {'SCORE':<8s} {'RÉSULTAT':<10s}")
    print("-" * 70)

    total, ok = 0, 0
    for nom_schema, info in SCHEMAS.items():
        # Encoder le raisonnement
        trames = encoder_reasoning(info['ops'])
        points = decoder_trajectoire(trames)

        # Classifier par corrélation de trajectoire
        schema, domaine, score = classer_par_trajectoire(points)

        resultat = '✅' if schema == nom_schema else '❌'
        total += 1
        ok += (schema == nom_schema)

        print(f"{nom_schema:<30s} {schema:<20s} {score:.4f}  {resultat:<10s}")

    print(f"\n  Score classification : {ok}/{total} ({100*ok/total:.1f}%)\n")

    # Test de généralisation
    print("═══ TEST DE GÉNÉRALISATION : raisonnements hybrides ═══\n")
    
    test_cases = [
        ("Planification (ASSERT → CAUSE → EFFET → IMPLY)",
         [('ASSERT', 0.5), ('CAUSE', 0.8), ('EFFET', 0.6), ('IMPLY', 0.7)]),
        ("Contentieux (FAIT → NORME → CONFLIT → PONDERE → IMPLY)",
         [('FAIT', 0.7), ('NORME', 0.8), ('CONFLIT', 0.6), ('PONDERE', 0.7), ('IMPLY', 0.5)]),
        ("Cas clinique (SYMPT → DIFF → EXCLURE → CONFIRM → TRAIT → PROGN)",
         [('SYMPT', 0.6), ('DIFF', 0.8), ('EXCLURE', 0.7), ('CONFIRM', 0.7), ('TRAIT', 0.6), ('PROGN', 0.5)]),
        ("Appel (FAIT → PROCED → NORME → INTERPR → QUALIF → DISTING)",
         [('FAIT', 0.6), ('PROCED', 0.5), ('NORME', 0.7), ('INTERPR', 0.6), ('QUALIF', 0.7), ('DISTING', 0.5)]),
        ("Patient chronique (ANTEC → COMORB → DIFF → TRAIT → PROGN → RECID)",
         [('ANTEC', 0.5), ('COMORB', 0.6), ('DIFF', 0.7), ('TRAIT', 0.6), ('PROGN', 0.6), ('RECID', 0.4)]),
    ]
    
    for desc, ops in test_cases:
        trames = encoder_reasoning(ops)
        points = decoder_trajectoire(trames)
        schema, domaine, score = classer_par_trajectoire(points)
        print(f"  {desc}")
        print(f"  → {schema} (domaine={domaine}, score={score:.4f})")
        print()


if __name__ == '__main__':
    test_complet()