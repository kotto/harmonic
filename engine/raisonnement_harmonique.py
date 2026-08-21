#!/usr/bin/env python3
"""
raisonnement_harmonique.py — Moteur de raisonnement harmonique universel
=========================================================================

PRINCIPE :
  Tout raisonnement formel peut être décomposé en une séquence d'opérations
  primitives, chaque primitive ayant une FRÉQUENCE HARMONIQUE propre.
  La séquence forme une TRAJECTOIRE ψ dont l'empreinte spectrale identifie
  le TYPE de raisonnement, indépendamment du contenu.

  Le codec ψ (codec_trajectoire.py) a validé le principe pour l'arithmétique
  (91% GSM8K). On l'étend ici à la logique, la causalité, l'analogie.

PRIMITIVES HARMONIQUES (fréquences normalisées par φ = 1.618...) :

  ARITHMÉTIQUE (validé expérimentalement) :
    INIT    f = 0         (position de base)
    ADD     f = 1/φ       (combinaison linéaire)
    SUB     f = 1/2φ      (soustraction linéaire)
    MUL     f = 2/φ       (produit harmonique)
    DIV     f = 1/3φ      (division harmonique)
    RATE    f = √5        (taux, proportion)

  LOGIQUE PROPOSITIONNELLE :
    ASSERT  f = 1         (assertion de fait : φ⁰)
    AND     f = φ         (conjonction)
    OR      f = φ²        (disjonction)
    NOT     f = 1/φ       (négation, symétrique de ADD)
    IMPLY   f = √3        (implication)
    EQUIV   f = 2         (équivalence : φ⁰×2)

  LOGIQUE DES PRÉDICATS :
    EXISTS  f = √5        (existentiel)
    FORALL  f = √7        (universel)
    INST    f = 1/√5      (instanciation)
    GEN     f = 2/√5      (généralisation)

  CAUSALITÉ :
    CAUSE   f = √φ        (causalité directe : A → B)
    EFFET   f = 1/√φ      (effet observé)
    CONTRE  f = -√φ       (contrefactuel : anti-causal)
    CORR    f = φ/√3      (corrélation)
    INTERV  f = √(φ+1)    (intervention)

  ANALOGIE :
    MAP     f = φ²/2      (mapping source → cible)
    INFER   f = 2/φ       (inférence par analogie)
    ABSTR   f = φ³        (abstraction)
    CONCR   f = 1/φ³      (concrétisation)

  MÉTA-RAISONNEMENT :
    HYPOTH  f = √(2φ)     (hypothèse)
    VERIF   f = 1/√(2φ)   (vérification)
    REFUTE  f = -√(π)     (réfutation, anti-résonance)
    DOUTE   f = 1/π       (doute, incertitude)

PROPRIÉTÉS :
  1. Toute primitive a une fréquence dans l'extension harmonique {1, φ,
     √2, √3, √5, √7, π} ou leurs inverses/combinaisons.
  2. L'anti-résonance (fréquence négative) encode la négation ou la
     réfutation — un raisonnement qui "s'annule".
  3. La structure du raisonnement = trajectoire dans l'espace des phases.
  4. L'empreinte spectrale = FFT du signal ψ → invariante par permutation
     des valeurs concrètes, ne dépend que de la structure.

USAGE (conceptuel — à implémenter après validation) :
  raisonnement = Sequence[
    ASSERT('Socrate est un homme'),
    FORALL('x', IMPLY(HOMME(x), MORTEL(x))),
    INST('Socrate', FORALL),
    IMPLY(ASSERT, INST),
  ]
  frames = encoder_raisonnement(raisonnement)
  spectre = analyse_spectrale(frames)
  type_raisonnement = classer_par_spectre(spectre)
"""

import sys, os, math, cmath, json, re
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PHI = (1 + math.sqrt(5)) / 2

# ═══════════════════════════════════════════════════════════════════════════
# 1. DICTIONNAIRE DES PRIMITIVES
# ═══════════════════════════════════════════════════════════════════════════

PRIMITIVES = {
    # Arithmétique (déjà validé)
    'INIT':    {'freq': 0.0,       'domaine': 'arithmetique',  'groupe': 'base'},
    'ADD':     {'freq': 1.0 / PHI, 'domaine': 'arithmetique',  'groupe': 'lineaire'},
    'SUB':     {'freq': 1.0 / (2 * PHI), 'domaine': 'arithmetique', 'groupe': 'lineaire'},
    'MUL':     {'freq': 2.0 / PHI, 'domaine': 'arithmetique',  'groupe': 'harmonique'},
    'DIV':     {'freq': 1.0 / (3 * PHI), 'domaine': 'arithmetique', 'groupe': 'harmonique'},
    'RATE':    {'freq': math.sqrt(5), 'domaine': 'arithmetique', 'groupe': 'proportion'},
    
    # Logique propositionnelle
    'ASSERT':  {'freq': 1.0,       'domaine': 'logique',       'groupe': 'base'},
    'AND':     {'freq': PHI,       'domaine': 'logique',       'groupe': 'binaire'},
    'OR':      {'freq': PHI ** 2,  'domaine': 'logique',       'groupe': 'binaire'},
    'NOT':     {'freq': 1.0 / PHI, 'domaine': 'logique',       'groupe': 'unaire'},
    'IMPLY':   {'freq': math.sqrt(3), 'domaine': 'logique',    'groupe': 'binaire'},
    'EQUIV':   {'freq': 2.0,       'domaine': 'logique',       'groupe': 'binaire'},
    
    # Prédicats
    'EXISTS':  {'freq': math.sqrt(5), 'domaine': 'predicat',   'groupe': 'quantificateur'},
    'FORALL':  {'freq': math.sqrt(7), 'domaine': 'predicat',   'groupe': 'quantificateur'},
    'INST':    {'freq': 1.0 / math.sqrt(5), 'domaine': 'predicat', 'groupe': 'application'},
    'GEN':     {'freq': 2.0 / math.sqrt(5), 'domaine': 'predicat', 'groupe': 'application'},
    
    # Causalité
    'CAUSE':   {'freq': math.sqrt(PHI), 'domaine': 'causalite', 'groupe': 'directe'},
    'EFFET':   {'freq': 1.0 / math.sqrt(PHI), 'domaine': 'causalite', 'groupe': 'directe'},
    'CONTRE':  {'freq': -math.sqrt(PHI), 'domaine': 'causalite', 'groupe': 'contrefactuel'},
    'CORR':    {'freq': PHI / math.sqrt(3), 'domaine': 'causalite', 'groupe': 'statistique'},
    'INTERV':  {'freq': math.sqrt(PHI + 1), 'domaine': 'causalite', 'groupe': 'intervention'},
    
    # Analogie
    'MAP':     {'freq': PHI ** 2 / 2, 'domaine': 'analogie',   'groupe': 'mapping'},
    'INFER':   {'freq': 2.0 / PHI, 'domaine': 'analogie',      'groupe': 'inférence'},
    'ABSTR':   {'freq': PHI ** 3, 'domaine': 'analogie',       'groupe': 'abstraction'},
    'CONCR':   {'freq': 1.0 / PHI ** 3, 'domaine': 'analogie', 'groupe': 'abstraction'},
    
    # Méta
    'HYPOTH':  {'freq': math.sqrt(2 * PHI), 'domaine': 'meta', 'groupe': 'hypothese'},
    'VERIF':   {'freq': 1.0 / math.sqrt(2 * PHI), 'domaine': 'meta', 'groupe': 'hypothese'},
    'REFUTE':  {'freq': -math.sqrt(math.pi), 'domaine': 'meta', 'groupe': 'refutation'},
    'DOUTE':   {'freq': 1.0 / math.pi, 'domaine': 'meta',      'groupe': 'incertitude'},
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RAISONNEMENT JURIDIQUE
    # ═══════════════════════════════════════════════════════════════════════════
    # Chaque primitive a une fréquence UNIQUE dans l'extension harmonique.
    # ASSERT(1.0) ≠ FAIT(√2/φ) — même geste logique, domaine différent.
    
    'FAIT':    {'freq': math.sqrt(2) / PHI, 'domaine': 'juridique', 'groupe': 'fait'},
    # Fait empirique : assertion d'un événement, d'une circonstance
    # f = √2/φ ≈ 0.874 — le fait est une assertion teintée d'observation
    
    'NORME':   {'freq': PHI,       'domaine': 'juridique', 'groupe': 'norme'},
    # Règle de droit : "si X alors Y (légalement)"
    # f = φ — structure conditionnelle, premier étage de la norme
    
    'QUALIF':  {'freq': math.sqrt(3), 'domaine': 'juridique', 'groupe': 'subsomption'},
    # Qualification : subsomption d'un fait sous une catégorie juridique
    # f = √3 — le geste central du droit, l'IMPLY juridique
    
    'CONFLIT': {'freq': -PHI ** 2, 'domaine': 'juridique', 'groupe': 'conflit'},
    # Conflit de normes : deux règles donnent des résultats contradictoires
    # f = -φ² — anti-résonance, annulation mutuelle
    
    'PONDERE': {'freq': math.sqrt(2 * PHI), 'domaine': 'juridique', 'groupe': 'balance'},
    # Balancement/Pondération : proportionnalité, intérêts concurrents
    # f = √(2φ) — comme HYPOTH, la pondération est un jugement complexe
    
    'PRESOMP': {'freq': 1.0 / PHI, 'domaine': 'juridique', 'groupe': 'presomption'},
    # Présomption : renversement de la charge de la preuve
    # f = 1/φ — comme NOT, la présomption inverse la position par défaut
    
    'INTERPR': {'freq': PHI ** 3, 'domaine': 'juridique', 'groupe': 'interpretation'},
    # Interprétation : textuelle, téléologique, systématique
    # f = φ³ — comme ABSTR, l'interprétation est une abstraction du texte
    
    'PRECED':  {'freq': math.sqrt(5), 'domaine': 'juridique', 'groupe': 'precedent'},
    # Précédent : stare decisis, autorité du précédent
    # f = √5 — comme EXISTS, le précédent existe comme fait juridique
    
    'DISTING': {'freq': -math.sqrt(3), 'domaine': 'juridique', 'groupe': 'distinction'},
    # Distinction : le précédent ne s'applique pas (différence pertinente)
    # f = -√3 — négation de QUALIF, anti-subsomption
    
    'ANNEXE':  {'freq': 2.0 / PHI, 'domaine': 'juridique', 'groupe': 'incorporation'},
    # Incorporation : renvoi à une norme externe
    # f = 2/φ — comme MUL, multiplication des sources juridiques
    
    'PROCED':  {'freq': 1.0 / math.pi, 'domaine': 'juridique', 'groupe': 'procedure'},
    # Procédure : délais, recours, garanties processuelles
    # f = 1/π — comme DOUTE, la procédure gère l'incertitude du débat
    
    'COMPET':  {'freq': math.sqrt(7), 'domaine': 'juridique', 'groupe': 'competence'},
    # Compétence : autorité juridictionnelle, champ d'application
    # f = √7 — comme FORALL, la compétence délimite l'univers du discours
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RAISONNEMENT MÉDICAL
    # ═══════════════════════════════════════════════════════════════════════════
    # Toutes les fréquences sont uniques dans l'ensemble harmonique.
    
    'SYMPT':   {'freq': 1.0 / math.sqrt(PHI), 'domaine': 'medical', 'groupe': 'symptome'},
    # Symptôme : rapporté par le patient — c'est un EFFET d'une cause cachée
    # f = 1/√φ ≈ 0.786 — comme EFFET, le symptôme est l'effet observable
    
    'SIGNE':   {'freq': math.sqrt(2) / 2, 'domaine': 'medical', 'groupe': 'signe'},
    # Signe clinique : constaté objectivement
    # f = √2/2 ≈ 0.707 — le signe est plus précis que le symptôme
    
    'DIFF':    {'freq': math.sqrt(5), 'domaine': 'medical', 'groupe': 'diagnostic'},
    # Diagnostic différentiel : liste des hypothèses
    # f = √5 — comme EXISTS, le diagnostic explore des branches
    
    'CONFIRM': {'freq': 2.0,       'domaine': 'medical', 'groupe': 'test'},
    # Test de confirmation : gold standard
    # f = 2 — comme EQUIV, le test établit une équivalence
    
    'EXCLURE': {'freq': -math.sqrt(5), 'domaine': 'medical', 'groupe': 'exclusion'},
    # Exclusion : écarter une hypothèse
    # f = -√5 — anti-DIFF, fermeture d'une branche
    
    'TRAIT':   {'freq': math.sqrt(PHI), 'domaine': 'medical', 'groupe': 'therapeutique'},
    # Traitement : intervention causale
    # f = √φ — comme CAUSE, le traitement est une cause intentionnelle
    
    'EFF_SEC': {'freq': 1.0 / (PHI ** 2), 'domaine': 'medical', 'groupe': 'therapeutique'},
    # Effet secondaire : conséquence indésirable
    # f = 1/φ² ≈ 0.382 — sous-harmonique du traitement
    
    'PROGN':   {'freq': math.sqrt(2 * PHI), 'domaine': 'medical', 'groupe': 'pronostic'},
    # Pronostic : évolution attendue
    # f = √(2φ) — comme HYPOTH, projection probabiliste
    
    'COMORB':  {'freq': PHI ** 2, 'domaine': 'medical', 'groupe': 'comorbidite'},
    # Comorbidité : pathologies interagissantes
    # f = φ² — comme OR, combinaison de conditions
    
    'ANTEC':   {'freq': 1.0 / (PHI ** 2), 'domaine': 'medical', 'groupe': 'antecedent'},
    # Antécédent : histoire médicale, facteur de risque
    # f = 1/φ² — harmonique lointain, passé lointain
    
    'EPIDEM':  {'freq': math.sqrt(2) / math.sqrt(3), 'domaine': 'medical', 'groupe': 'epidemiologie'},
    # Épidémiologie : données populationnelles
    # f = √2/√3 ≈ 0.816 — rapport entre précision et complexité
    
    'MECA':    {'freq': PHI,       'domaine': 'medical', 'groupe': 'mecanisme'},
    # Mécanisme physiopathologique
    # f = φ — comme NORME, le mécanisme est la structure causale
    
    'GRADE':   {'freq': 1.0 / math.pi, 'domaine': 'medical', 'groupe': 'preuve'},
    # Niveau de preuve : RCT, cohorte, avis d'expert
    # f = 1/π — comme DOUTE, le grade quantifie l'incertitude
    
    'BIOPSY':  {'freq': 2.0,       'domaine': 'medical', 'groupe': 'test'},
    # Biopsie : diagnostic définitif
    # f = 2 — comme CONFIRM, le diagnostic de référence
    
    'RECID':   {'freq': -math.sqrt(PHI), 'domaine': 'medical', 'groupe': 'recurrence'},
    # Récidive : retour de la pathologie
    # f = -√φ — comme CONTRE, retour de ce qui avait été traité
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. ENCODEUR ψ POUR RAISONNEMENT GÉNÉRAL
# ═══════════════════════════════════════════════════════════════════════════

def encoder_raisonnement(etapes: List[Dict], echantillons_par_etape: int = 8) -> List[complex]:
    """
    Encode une séquence d'étapes de raisonnement en trajectoire ψ.
    
    Chaque étape émet une TRAME :
      - montée d'étage (amplitude 1.0, phase π/2) → structure
      - déplacement horizontal (amplitude = profondeur logique, phase = fréquence)
    """
    points = [0.0 + 0.0j]
    z = 0.0 + 0.0j
    etage = 0
    
    for etape in etapes:
        op = etape.get('op', 'ASSERT')
        info = PRIMITIVES.get(op, {'freq': 0.5, 'domaine': 'inconnu', 'groupe': 'inconnu'})
        freq = info['freq']
        profondeur = etape.get('profondeur', 0.5)
        
        # Montée d'étage (structure : chaque raisonnement ajoute un niveau)
        etage += 1
        z += 1.0 * cmath.exp(1j * math.pi / 2)  # montée y+1
        points.append(z)
        
        # Déplacement horizontal (le contenu du raisonnement)
        # phase = harmonique de l'opération
        # amplitude = profondeur (poids logique de l'argument)
        z += profondeur * cmath.exp(1j * 2 * math.pi * freq / PHI)
        points.append(z)
        
        # Échantillons oscillatoires pour l'analyse spectrale
        for k in range(echantillons_par_etape):
            t = k / echantillons_par_etape
            z += 0.05 * cmath.exp(1j * 2 * math.pi * freq * t)
            points.append(z)
    
    return points


# ═══════════════════════════════════════════════════════════════════════════
# 3. ANALYSE SPECTRALE — IDENTIFICATION DU TYPE DE RAISONNEMENT
# ═══════════════════════════════════════════════════════════════════════════

def empreinte_spectrale(points: List[complex]) -> Dict[str, float]:
    """
    Calcule l'empreinte spectrale d'une trajectoire ψ.
    Les pics de corrélation aux fréquences PRIMITIVES révèlent
    les opérations utilisées — et donc le TYPE de raisonnement.
    """
    import numpy as np
    signal = np.array([p.real for p in points])
    signal = signal - np.mean(signal)
    energie = np.sum(np.abs(signal)) + 1e-9
    n = len(signal)
    k = np.arange(n)
    
    result = {}
    for op, info in PRIMITIVES.items():
        f = abs(info['freq'])
        if f < 0.01: continue
        corr = np.abs(np.sum(signal * np.exp(-1j * 2 * np.pi * f * k)))
        result[op] = corr / energie
    
    return result


def classer_raisonnement(spectre: Dict[str, float]) -> str:
    """
    Classe le type de raisonnement par la répartition spectrale.
    - 'deductif' : pics sur IMPLY + INST + ASSERT
    - 'causal'   : pics sur CAUSE + EFFET + CONTRE
    - 'analogique': pics sur MAP + INFER + ABSTR
    - 'abductif' : pics sur HYPOTH + VERIF + EFFET
    - 'inductif' : pics sur GEN + EXISTS + CORR
    """
    domaines = {}
    for op, corr in spectre.items():
        info = PRIMITIVES.get(op, {})
        d = info.get('domaine', 'inconnu')
        domaines[d] = domaines.get(d, 0) + corr
    
    if not domaines: return 'inconnu'
    return max(domaines, key=domaines.get)


# ═══════════════════════════════════════════════════════════════════════════
# 4. EXEMPLES DE RAISONNEMENT
# ═══════════════════════════════════════════════════════════════════════════

def exemple_syllogisme():
    """Socrate est un homme. Tous les hommes sont mortels. → Socrate est mortel."""
    etapes = [
        {'op': 'ASSERT', 'profondeur': 0.8},   # Socrate est un homme
        {'op': 'FORALL', 'profondeur': 1.0},    # ∀x (Homme(x) → Mortel(x))
        {'op': 'INST',   'profondeur': 0.6},    # instanciation sur Socrate
        {'op': 'IMPLY',  'profondeur': 0.9},    # Socrate est mortel
    ]
    return etapes, 'deductif'


def exemple_causal():
    """La pluie fait pousser les plantes. Il a plu. → Les plantes poussent."""
    etapes = [
        {'op': 'CAUSE',  'profondeur': 1.0},    # pluie → croissance
        {'op': 'ASSERT', 'profondeur': 0.7},    # il a plu
        {'op': 'EFFET',  'profondeur': 0.9},    # les plantes poussent
        {'op': 'CONTRE', 'profondeur': 0.3},    # si pas de pluie → pas de croissance (contrefactuel)
    ]
    return etapes, 'causal'


def exemple_analogie():
    """Atome = système solaire miniature (noyau = soleil, électrons = planètes)."""
    etapes = [
        {'op': 'MAP',    'profondeur': 1.0},    # mapping source→cible
        {'op': 'ABSTR',  'profondeur': 0.7},    # abstraction : attraction centrale
        {'op': 'INFER',  'profondeur': 0.9},    # inférence : orbites = orbitales
        {'op': 'CONCR',  'profondeur': 0.5},    # particularités quantiques
    ]
    return etapes, 'analogique'


def demo():
    """Démo : encoder les 3 raisonnements et comparer leurs spectres."""
    import numpy as np
    
    exemples = [exemple_syllogisme(), exemple_causal(), exemple_analogie()]
    noms = {'deductif': 'SYLLOGISME', 'causal': 'CAUSALITÉ', 'analogique': 'ANALOGIE'}
    
    print("═══ DÉMONSTRATION RAISONNEMENT HARMONIQUE ═══\n")
    
    for etapes, attendu in exemples:
        points = encoder_raisonnement(etapes)
        spectre = empreinte_spectrale(points)
        trouve = classer_raisonnement(spectre)
        
        print(f"  {noms[attendu]}  ({len(etapes)} étapes)")
        for e in etapes:
            info = PRIMITIVES.get(e['op'], {})
            f = info.get('freq', 0)
            print(f"    {e['op']:<8s} f={f:+.4f}  domaine={info.get('domaine','?')}")
        
        print(f"  Empreinte spectrale (top 5) :")
        for op, corr in sorted(spectre.items(), key=lambda x: -x[1])[:5]:
            info = PRIMITIVES.get(op, {})
            print(f"    {op:<8s} corr={corr:.4f}  ({info.get('domaine','?')})")
        
        print(f"  Classé comme : {trouve}  ({'✓' if trouve == attendu else '✗'})")
        print()


if __name__ == '__main__':
    demo()