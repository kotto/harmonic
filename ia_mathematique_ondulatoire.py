#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IA MATHEMATIQUE ONDULATOIRE — Intégration Traducteur + Solveur
===============================================================
Combine :
  1. Traducteur sémantique (langage naturel → domaine + paramètres)
  2. Solveur ondulatoire (calcul effectif par ondes)
  3. Résolution complète : problème en français → solution numérique

Architecture :
  Problème en langage naturel
    → Analyse sémantique (détection domaine + extraction paramètres)
    → Encodage en ondes (Ψ(x) = P(x)·exp(i·φ·x))
    → Résolution par interférence / recherche de nœuds / descente
    → Solution numérique + explication

Usage :
  python ia_mathematique_ondulatoire.py
  python ia_mathematique_ondulatoire.py -p "résoudre x²+3x-4=0"
"""

import numpy as np
import math, sys, io, re
from typing import Tuple, List, Callable

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PI = math.pi; PHI = (1 + math.sqrt(5)) / 2
SEP = "=" * 85

# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 1 : TRADUCTEUR SEMANTIQUE (langage naturel → paramètres)
# ═══════════════════════════════════════════════════════════════════════════════

def analyser_probleme(texte: str) -> dict:
    """
    Analyse un problème en langage naturel et extrait le domaine + paramètres.
    Retourne un dict avec 'domaine', 'parametres', 'equation_str'.
    """
    t = texte.lower()
    
    # Détection du domaine
    a_polynome = any(m in t for m in ['polynome','equation','racine','resoudre','factoriser',
                                        'x²','x^2','x³','x^3','degre','quadratique','cubique'])
    a_systeme = any(m in t for m in ['systeme','equations','inconnues','2x2','lineaire'])
    a_optimisation = any(m in t for m in ['minimum','maximum','optimiser','minimiser','maximiser',
                                           'optimum','trouver le point'])
    a_derivee = any(m in t for m in ['derivee','deriver','differentielle','tangente','pente'])
    a_integrale = any(m in t for m in ['integrale','integrer','aire sous','surface','primitive'])
    a_arithmetique = any(m in t for m in ['calculer','addition','multiplication','somme','produit',
                                            'quotient','difference','+','-','*','/','×'])
    
    # Extraction des coefficients polynomiaux
    coeffs = None
    if a_polynome:
        coeffs = extraire_coefficients_polynome(t)
    
    # Extraction des opérations arithmétiques
    operation = None
    if a_arithmetique:
        operation = extraire_operation_arithmetique(t)
    
    # Détermination du domaine final
    if coeffs is not None:
        domaine = 'polynome'
    elif operation is not None:
        domaine = 'arithmetique'
    elif a_systeme:
        domaine = 'systeme'
    elif a_optimisation:
        domaine = 'optimisation'
    elif a_derivee:
        domaine = 'derivee'
    elif a_integrale:
        domaine = 'integrale'
    else:
        domaine = 'indetermine'
    
    return {
        'domaine': domaine,
        'coeffs': coeffs,
        'operation': operation,
        'texte_original': texte,
    }


def extraire_coefficients_polynome(texte: str) -> List[float]:
    """Extrait les coefficients [a₀, a₁, a₂, ...] d'un polynôme dans un texte."""
    # Motif 1 : forme canonique ax²+bx+c=0
    # Chercher les nombres avec leur signe
    termes = re.findall(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*x\^?(\d*)', texte)
    if not termes:
        # Essayer x², x sans ^
        termes = re.findall(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*x²?', texte)
        if termes:
            # Simplifié
            pass
    
    # Approche robuste : parser terme à terme
    # Cherche a*x^2, b*x, c
    a = b = c = 0.0
    
    # Coefficient de x²
    m_x2 = re.search(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*x\s*\^?\s*2', texte)
    if m_x2:
        s = m_x2.group(1).strip().replace(' ', '')
        if s in ['+', '-', '']: s += '1'
        a = float(s)
    
    m_x2_alt = re.search(r'([+-]?\s*\d*\.?\d*)\s*x²', texte)
    if m_x2_alt and a == 0:
        s = m_x2_alt.group(1).strip().replace(' ', '')
        if s in ['+', '-', '']: s += '1'
        a = float(s)
    
    # Coefficient de x (pas x²)
    m_x = re.search(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*x\b(?!\^|²)', texte)
    if m_x:
        s = m_x.group(1).strip().replace(' ', '')
        if s in ['+', '-', '']: s += '1'
        b = float(s)
    
    # Terme constant
    m_c = re.findall(r'([+-]?\s*\d+\.?\d*)\s*=\s*0', texte)
    if not m_c:
        m_c = re.findall(r'([+-]\s*\d+\.?\d*)(?!\s*\*?\s*x)', texte)
    
    # Méthode alternative : chercher tous les nombres
    nums = re.findall(r'([+-]?\s*\d+\.?\d*)', texte)
    nums = [float(n.replace(' ', '')) for n in nums if n.strip()]
    
    # Heuristique : si on a 3 nombres et qu'on a détecté un polynôme,
    # ce sont probablement c, b, a (ordre croissant des puissances)
    if len(nums) >= 3 and a == 0 and b == 0:
        # On prend les 3 derniers nombres (les plus pertinents)
        # Format typique : x² + 3x - 4 = 0 → nombres : 2, 3, -4
        # On veut c=-4, b=3, a=1
        relevant = nums[-3:]
        c, b, a = relevant[0], relevant[1], 1.0  # a implicite = 1
    
    if a != 0 or b != 0 or c != 0:
        return [c, b, a]  # [a₀, a₁, a₂]
    
    return None


def extraire_operation_arithmetique(texte: str) -> dict:
    """Extrait a op b depuis un texte arithmétique."""
    nums = re.findall(r'(\d+\.?\d*)', texte)
    if len(nums) >= 2:
        a = float(nums[0])
        b = float(nums[-1])
        if '+' in texte or 'addition' in texte or 'somme' in texte:
            return {'op': '+', 'a': a, 'b': b}
        elif '*' in texte or '×' in texte or 'multiplication' in texte or 'produit' in texte:
            return {'op': '*', 'a': a, 'b': b}
        elif '/' in texte or 'division' in texte or 'quotient' in texte:
            return {'op': '/', 'a': a, 'b': b}
        elif '-' in texte or 'soustraction' in texte or 'difference' in texte:
            return {'op': '-', 'a': a, 'b': b}
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 2 : SOLVEUR ONDULATOIRE (calcul effectif)
# ═══════════════════════════════════════════════════════════════════════════════

def add_wave(a,b):    
    xs=np.linspace(-PI,PI,500); psi=a*np.exp(1j*PHI*xs)+b*np.exp(1j*PHI*xs)
    idx=len(psi)//2; s=1.0 if np.real(psi[idx])>=0 else -1.0
    return s*np.mean(np.abs(psi))

def mul_wave(a,b):    
    xs=np.linspace(-PI,PI,500); psi=(a*np.exp(1j*PHI*xs))*(b*np.exp(1j*PHI*xs))
    idx=len(psi)//2; s=1.0 if np.real(psi[idx])>=0 else -1.0
    return s*np.mean(np.abs(psi))

def sub_wave(a,b): return add_wave(a,-b)

def div_wave(a,b):
    if b==0: return float('inf')
    xs=np.linspace(-PI,PI,500); amp_a=np.mean(np.abs(a*np.exp(1j*PHI*xs)))
    amp_b=np.mean(np.abs(b*np.exp(1j*PHI*xs)))
    r=amp_a/amp_b; return -r if ((a<0)^(b<0)) else r

def trouver_racines(coeffs, x_range=(-10,10), n_points=5000, seuil=0.05):
    xs = np.linspace(x_range[0], x_range[1], n_points)
    P = sum(c * xs**k for k, c in enumerate(coeffs))
    psi = P * np.exp(1j * PHI * xs)
    amp = np.abs(psi)
    max_amp = max(np.max(amp), 1.0)
    racines = []
    for i in range(1, n_points-1):
        if amp[i] < amp[i-1] and amp[i] < amp[i+1] and amp[i] < seuil*max_amp:
            racines.append(round(float(xs[i]), 10))
    uniques = []
    for r in sorted(racines):
        if not uniques or abs(r - uniques[-1]) > 0.01:
            uniques.append(r)
    return uniques


# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 3 : RESOLUTION UNIFIEE (analyse + calcul)
# ═══════════════════════════════════════════════════════════════════════════════

def resoudre(texte: str) -> dict:
    """
    Prend un problème en langage naturel et retourne la solution calculée
    par le moteur ondulatoire.
    """
    analyse = analyser_probleme(texte)
    domaine = analyse['domaine']
    
    if domaine == 'polynome' and analyse['coeffs']:
        coeffs = analyse['coeffs']
        racines = trouver_racines(coeffs)
        verif = [abs(sum(c*r**k for k,c in enumerate(coeffs))) for r in racines]
        
        # Formater l'équation
        eq_parts = []
        for k, c in enumerate(coeffs):
            if c == 0: continue
            if k == 0: eq_parts.append(f'{c}')
            elif k == 1: eq_parts.append(f'{c}x')
            else: eq_parts.append(f'{c}x^{k}')
        eq_str = ' + '.join(eq_parts).replace('+ -', '- ') + ' = 0'
        
        return {
            'domaine': 'polynome',
            'equation': eq_str,
            'racines': racines,
            'verification': verif,
            'nb_racines': len(racines),
            'explication': f"Les racines sont les points où |Ψ(x)| = |P(x)| = 0. L'onde P(x)·exp(i·φ·x) s'annule exactement aux racines du polynôme.",
        }
    
    elif domaine == 'arithmetique' and analyse['operation']:
        op = analyse['operation']
        a, b = op['a'], op['b']
        
        if op['op'] == '+':
            resultat = add_wave(a, b)
            explication = f"Addition par superposition d'ondes : Ψ({a}) + Ψ({b}) = Ψ({a+b})"
        elif op['op'] == '-':
            resultat = sub_wave(a, b)
            explication = f"Soustraction : Ψ({a}) + Ψ({-b}) = Ψ({a-b})"
        elif op['op'] == '*':
            resultat = mul_wave(a, b)
            explication = f"Multiplication par produit d'ondes : Ψ({a})·Ψ({b}) = {a}·{b}·exp(i·2φ·x)"
        elif op['op'] == '/':
            resultat = div_wave(a, b)
            explication = f"Division par quotient d'amplitudes : |Ψ({a})| / |Ψ({b})| = {a}/{b}"
        else:
            resultat = None
            explication = ""
        
        return {
            'domaine': 'arithmetique',
            'operation': f'{a} {op["op"]} {b}',
            'resultat': resultat,
            'explication': explication,
        }
    
    elif domaine == 'optimisation':
        return {
            'domaine': 'optimisation',
            'explication': "Fonction d'optimisation non spécifiée. Exemple : 'trouver le minimum de x²'.",
        }
    
    elif domaine == 'derivee':
        return {
            'domaine': 'derivee',
            'explication': "Fonction à dériver non spécifiée. Exemple : 'dériver sin(x) en x=0'.",
        }
    
    elif domaine == 'integrale':
        return {
            'domaine': 'integrale',
            'explication': "Fonction à intégrer non spécifiée. Exemple : 'intégrer x de 0 à 4'.",
        }
    
    else:
        return {
            'domaine': 'indetermine',
            'explication': "Domaine non reconnu. Essayez : 'résoudre x²+3x-4=0', 'calculer 5+7', 'minimum de x²', 'dérivée de sin(x) en 0'.",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS & DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    problemes = [
        "Résoudre l'équation x² + 3x - 4 = 0",
        "Résoudre x² - 5x + 6 = 0",
        "Résoudre x³ - 9x = 0",
        "Calculer 5 + 7",
        "Multiplication de 6 par 8",
        "Que vaut 100 divisé par 4 ?",
        "Trouver les racines de x²+3x-4=0",
    ]
    
    print(f"\n{SEP}")
    print(f"  IA MATHÉMATIQUE ONDULATOIRE")
    print(f"  Traducteur + Solveur Unifiés")
    print(f"{SEP}")
    
    for texte in problemes:
        print(f"\n  {'─'*78}")
        print(f"  🎤 Problème : \"{texte}\"")
        r = resoudre(texte)
        print(f"  📊 Domaine   : {r['domaine']}")
        
        if r['domaine'] == 'polynome':
            print(f"  📐 Équation  : {r['equation']}")
            print(f"  🌊 Racines   : {r['racines']}")
            if r['verification']:
                print(f"  ✅ Vérifiées : {[f'{v:.2e}' for v in r['verification']]}")
            print(f"  💡 {r['explication'][:100]}...")
        elif r['domaine'] == 'arithmetique':
            print(f"  🔢 Opération : {r['operation']}")
            print(f"  🌊 Résultat  : {r['resultat']}")
            print(f"  💡 {r['explication']}")
        else:
            print(f"  💡 {r['explication']}")
    
    print(f"\n{SEP}")
    print(f"  FIN DE LA DÉMONSTRATION")
    print(f"{SEP}\n")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--probleme', type=str, default=None)
    args = p.parse_args()
    
    if args.probleme:
        r = resoudre(args.probleme)
        if r['domaine'] == 'polynome':
            print(f"Équation : {r['equation']}")
            print(f"Racines  : {r['racines']}")
            if r['verification']:
                print(f"Vérif    : {[f'{v:.2e}' for v in r['verification']]}")
        elif r['domaine'] == 'arithmetique':
            print(f"{r['operation']} = {r['resultat']}")
        else:
            print(r['explication'])
    else:
        demo()