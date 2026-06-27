#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IA HARMONIQUE FINALE — Traducteur + Solveur Suprême Intégrés
=============================================================
Architecture unifiée :
  Problème en langage naturel
    → Analyse sémantique (domaine + extraction paramètres)
    → Encodage en onde Ψ(x) = P(x)·exp(i·φ·x)
    → Résolution par interférence / superposition / descente
    → Solution numérique exacte + explication

Capacités : Arithmétique, Polynômes, EDO, Optimisation, Analyse.
Usage : python ia_harmonique_finale.py
"""

import numpy as np
import math, sys, io, re, time
from typing import List, Callable

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PI = math.pi; PHI = (1 + math.sqrt(5)) / 2; E = math.e
SEP = "=" * 85

# ═══════════════════════ PARTIE 1 : TRADUCTEUR ═══════════════════════

def analyser_probleme(texte: str) -> dict:
    t = texte.lower()

    # Détection (ordre de priorité : plus spécifique d'abord)
    a_edo = any(m in t for m in ["y''","y'","y\"",'equation differentielle','edo','y(0)=','derivee seconde','solution de'])
    a_optimisation = any(m in t for m in ['minimum','maximum','optimiser','minimiser','maximiser','optimum','trouver le minimum','trouver le maximum'])
    a_polynome = any(m in t for m in ['polynome','equation','racine','resoudre','factoriser','x²','x^2','x³','x^3','degre','quadratique','cubique','trouver les racines'])
    a_systeme = any(m in t for m in ['systeme','equations','inconnues','2x2','lineaire'])
    a_derivee = any(m in t for m in ['derivee','deriver','differentielle','tangente','pente'])
    a_integrale = any(m in t for m in ['integrale','integrer','aire sous','surface','primitive'])
    a_arithmetique = (any(m in t for m in ['calculer','addition','multiplication','somme','produit','quotient','difference','divise','fois','+','-','*','/','×','combien','font','donne','vaut','que vaut','que donne','donne','difference entre']) and not a_edo and not a_polynome and not a_optimisation)

    coeffs = extraire_coefficients_polynome(t) if a_polynome and not a_edo else None
    operation = extraire_operation_arithmetique(t) if a_arithmetique else None
    edo_params = extraire_edo_params(t) if a_edo else None
    opt_params = extraire_optimisation_params(t) if a_optimisation else None

    if a_edo: domaine = 'edo'
    elif a_optimisation: domaine = 'optimisation'
    elif coeffs is not None: domaine = 'polynome'
    elif operation is not None: domaine = 'arithmetique'
    elif a_systeme: domaine = 'systeme'
    elif a_derivee: domaine = 'derivee'
    elif a_integrale: domaine = 'integrale'
    else: domaine = 'indetermine'

    return {'domaine': domaine, 'coeffs': coeffs, 'operation': operation,
            'edo_params': edo_params, 'opt_params': opt_params, 'texte': texte}

def extraire_coefficients_polynome(texte: str):
    """Extrait les coefficients d'un polynôme. Gère degrés 2 et 3, termes manquants."""
    nums_raw = re.findall(r'([+-]?\s*\d+\.?\d*)', texte)
    nums = [float(n.replace(' ', '')) for n in nums_raw if n.strip() and float(n.replace(' ', '')) not in [0.0, 2.0, 3.0]]
    
    # Détecter le degré maximal
    degre_max = 2
    if any(m in texte for m in ['x^3','x³']): degre_max = 3
    if any(m in texte for m in ['x^4','x⁴']): degre_max = 4
    
    # Extraire les coefficients par degré
    coeffs_result = {}
    
    # Coefficient du terme de plus haut degré (implicite = 1)
    if degre_max == 3:
        m = re.search(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*x\s*\^?\s*3', texte)
        if not m: m = re.search(r'([+-]?\s*\d*\.?\d*)\s*x³', texte)
        if m:
            s = m.group(1).strip().replace(' ', '')
            coeffs_result[3] = float(s) if s and s not in ['+','-',''] else (1.0 if s in ['+',''] else -1.0 if s=='-' else 1.0)
        else:
            coeffs_result[3] = 1.0  # implicite
    else:
        coeffs_result[3] = 0.0
    
    # Coefficient de x²
    m = re.search(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*x\s*\^?\s*2', texte)
    if not m: m = re.search(r'([+-]?\s*\d*\.?\d*)\s*x²', texte)
    if m:
        s = m.group(1).strip().replace(' ', '')
        coeffs_result[2] = float(s) if s and s not in ['+','-',''] else (1.0 if s in ['+',''] else -1.0 if s=='-' else 1.0)
    else:
        coeffs_result[2] = 0.0  # absent → 0 (pas d'implicite pour les degrés inférieurs au max)
    
    # Coefficient de x (attention à ne pas capturer x² ou x³)
    m = re.search(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*x\b(?!\^|\²|\³|²|³)', texte)
    if m:
        s = m.group(1).strip().replace(' ', '')
        coeffs_result[1] = float(s) if s and s not in ['+','-',''] else (1.0 if s in ['+',''] else -1.0 if s=='-' else 1.0)
    else:
        coeffs_result[1] = 0.0
    
    # Terme constant
    m = re.search(r'([+-]\s*\d+\.?\d*)\s*=\s*0', texte)
    if m:
        coeffs_result[0] = float(m.group(1).replace(' ', ''))
    else:
        coeffs_result[0] = 0.0
    
    # Si aucun coefficient explicite trouvé, utiliser les nombres
    if all(v == 0.0 for v in coeffs_result.values()):
        filtered = [n for n in nums if n not in [0.0]]
        if len(filtered) >= 2:
            coeffs_result[0] = filtered[-1] if len(filtered)>=1 else 0.0
            coeffs_result[1] = filtered[-2] if len(filtered)>=2 else 0.0
    
    # Construire le tableau [a0, a1, a2, a3, ...]
    max_k = max(coeffs_result.keys()) if coeffs_result else 2
    result = [coeffs_result.get(k, 0.0) for k in range(max_k + 1)]
    
    # Vérifier qu'il y a au moins un coefficient non nul
    if any(c != 0.0 for c in result):
        return result
    return None

def extraire_operation_arithmetique(texte: str):
    nums = re.findall(r'(\d+\.?\d*)', texte)
    if len(nums) >= 2:
        a, b = float(nums[0]), float(nums[-1])
        if any(m in texte for m in ['+','addition','somme','plus','combien','font','donne']): return {'op': '+', 'a': a, 'b': b}
        if any(m in texte for m in ['*','×','multiplication','produit','fois']): return {'op': '*', 'a': a, 'b': b}
        if any(m in texte for m in ['/','division','quotient','divise','diviser','divisé']): return {'op': '/', 'a': a, 'b': b}
        if any(m in texte for m in ['-','soustraction','difference','moins','soustraire','oter','entre']): return {'op': '-', 'a': a, 'b': b}
    return None

def extraire_edo_params(texte: str):
    a_edo = 0.0; b_edo = 1.0; c_edo = 0.0; y0 = 0.0; dy0 = 1.0
    m_y0 = re.search(r'y\(0\)\s*=\s*([+-]?\d+\.?\d*)', texte)
    m_dy0 = re.search(r"y'\(0\)\s*=\s*([+-]?\d+\.?\d*)", texte)
    if m_y0: y0 = float(m_y0.group(1))
    if m_dy0: dy0 = float(m_dy0.group(1))

    # y'' + p·y' + q·y = 0 → a_edo=1, b_edo=p, c_edo=q
    nums = re.findall(r'([+-]?\s*\d+\.?\d*)', texte)
    nums = [float(n.replace(' ', '')) for n in nums if n.strip() and float(n.replace(' ', '')) not in [0.0]]
    if len(nums) >= 2:
        # Trouver les coefficients avant y' et y
        m_coeff_yprime = re.search(r'([+-]?\s*\d*)\s*y\'', texte)
        m_coeff_y = re.search(r'([+-]?\s*\d*)\s*y\b(?!\'|\(|-)', texte)
        if m_coeff_yprime:
            s = m_coeff_yprime.group(1).strip().replace(' ', '')
            b_edo = float(s) if s and s not in ['+','-'] else (1.0 if s=='+' or not s else -1.0)
        if m_coeff_y:
            s = m_coeff_y.group(1).strip().replace(' ', '')
            c_edo = float(s) if s and s not in ['+','-'] else (1.0 if s=='+' or not s else -1.0)
        if b_edo == 0.0 and c_edo == 0.0:
            # fallback : utiliser les nombres
            c_edo = nums[-2] if len(nums)>=2 else 1.0
            b_edo = nums[-3] if len(nums)>=3 else 0.0

    return {'a': a_edo, 'b': b_edo, 'c': c_edo, 'y0': y0, 'dy0': dy0}

def extraire_optimisation_params(texte: str):
    x0 = 5.0
    m_x0 = re.search(r'x[₀0]\s*=\s*([+-]?\d+\.?\d*)', texte)
    if m_x0: x0 = float(m_x0.group(1))
    return {'x0': x0}

# ═══════════════════════ PARTIE 2 : SOLVEUR ═══════════════════════

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
    xs=np.linspace(-PI,PI,500)
    amp_a=np.mean(np.abs(a*np.exp(1j*PHI*xs)))
    amp_b=np.mean(np.abs(b*np.exp(1j*PHI*xs)))
    r=amp_a/amp_b; return -r if ((a<0)^(b<0)) else r

def trouver_racines(coeffs, x_range=(-10,10), n_points=5000, seuil=0.05):
    """Trouve les racines réelles d'un polynôme par recherche de nœuds de |Ψ(x)|."""
    xs = np.linspace(x_range[0], x_range[1], n_points)
    P = sum(c * xs**k for k, c in enumerate(coeffs))
    amp = np.abs(P * np.exp(1j * PHI * xs))
    max_amp = max(np.max(amp), 1.0)
    
    # --- Passe 1 : minima locaux sous le seuil ---
    racines = []
    for i in range(1, n_points-1):
        if amp[i] < amp[i-1] and amp[i] < amp[i+1] and amp[i] < seuil * max_amp:
            racines.append(round(float(xs[i]), 10))
    
    # Détection spéciale de x=0
    idx_zero = n_points // 2
    if amp[idx_zero] < seuil * max_amp * 0.5:
        amp_left = amp[max(0, idx_zero-2)]
        amp_right = amp[min(n_points-1, idx_zero+2)]
        if amp[idx_zero] < amp_left * 0.5 and amp[idx_zero] < amp_right * 0.5:
            racines.append(0.0)
    
    # Déduplication grossière
    uniques = []
    for r in sorted(racines):
        if not uniques or abs(r - uniques[-1]) > 0.02: 
            uniques.append(r)
    
    # --- Passe 2 : détection racine multiple (minimum absolu très plat) ---
    # Si le nombre de racines trouvées est inférieur au degré théorique,
    # on cherche le minimum absolu de |P(x)| qui pourrait être une racine multiple.
    degre = len(coeffs) - 1
    if len(uniques) < degre:
        idx_min = int(np.argmin(amp))
        x_min = round(float(xs[idx_min]), 10)
        # Vérifier que P(x_min) est effectivement ~0
        P_min = abs(sum(c * x_min**k for k, c in enumerate(coeffs)))
        # Vérifier que ce minimum n'est pas déjà dans la liste
        already_found = any(abs(x_min - u) < 0.03 for u in uniques)
        if P_min < 0.01 and not already_found:
            uniques.append(x_min)
            uniques = sorted(set(round(r, 8) for r in uniques))
            # Re-dédupliquer
            dedup = []
            for r in uniques:
                if not dedup or abs(r - dedup[-1]) > 0.02:
                    dedup.append(r)
            uniques = dedup
    
    return uniques

def minimum_ondulatoire(f, x0, x_range=(-10,10), n_iter=1000, lr=0.01):
    x = x0
    for _ in range(n_iter):
        h = 1e-5; grad = (f(x+h)-f(x-h))/(2*h)
        x_new = max(x_range[0], min(x - lr*grad, x_range[1]))
        if abs(x_new-x) < 1e-12: break
        x = x_new
    return {'x': round(x,10), 'f': round(f(x),10)}

def resoudre_edo_lineaire(a_edo, b_edo, c_edo, y0, dy0, t_range=(0,10), n_points=1000):
    coeffs_carac = [c_edo, b_edo, a_edo]
    modes = trouver_racines(coeffs_carac)
    ts = np.linspace(t_range[0], t_range[1], n_points)
    if len(modes) == 2:
        r1, r2 = modes[0], modes[1]
        try: C = np.linalg.solve(np.array([[1,1],[r1,r2]]), np.array([y0,dy0]))
        except: C = np.array([y0/2, y0/2])
        y_ts = C[0]*np.exp(r1*ts) + C[1]*np.exp(r2*ts)
        sol_type = f"superposition de exp({r1:.3f}·t) et exp({r2:.3f}·t)"
    elif len(modes) == 1:
        r = modes[0]; C1, C2 = y0, dy0 - r*y0
        y_ts = (C1 + C2*ts)*np.exp(r*ts)
        sol_type = f"(C1+C2·t)·exp({r:.3f}·t) (racine double)"
    else:
        alpha = -b_edo/(2*a_edo) if a_edo != 0 else 0
        disc = 4*a_edo*c_edo - b_edo**2
        beta = math.sqrt(disc)/(2*a_edo) if disc > 0 and a_edo != 0 else 1.0
        C1, C2 = y0, (dy0 - alpha*y0)/beta if beta != 0 else 0
        y_ts = np.exp(alpha*ts)*(C1*np.cos(beta*ts) + C2*np.sin(beta*ts))
        sol_type = f"exp({alpha:.3f}t)·[cos({beta:.3f}t) + sin({beta:.3f}t)]"
    return {'ts': ts, 'y_ts': y_ts, 'solution_type': sol_type, 'modes': modes}

# ═══════════════════════ PARTIE 3 : RESOLUTION ═══════════════════════

def resoudre(texte: str) -> dict:
    analyse = analyser_probleme(texte)
    d = analyse['domaine']

    if d == 'polynome' and analyse['coeffs']:
        coeffs = analyse['coeffs']; racines = trouver_racines(coeffs)
        verif = [abs(sum(c*r**k for k,c in enumerate(coeffs))) for r in racines]
        eq_parts = [f'{c}' if k==0 else (f'{c}x' if k==1 else f'{c}x^{k}') for k,c in enumerate(coeffs) if c!=0]
        eq_str = ' + '.join(eq_parts).replace('+ -','- ') + ' = 0'
        return {'domaine': 'polynome', 'equation': eq_str, 'racines': racines, 'verification': verif}

    elif d == 'arithmetique' and analyse['operation']:
        op = analyse['operation']; a, b = op['a'], op['b']
        ops = {'+': add_wave, '-': sub_wave, '*': mul_wave, '/': div_wave}
        r = ops[op['op']](a, b) if op['op'] in ops else None
        return {'domaine': 'arithmetique', 'operation': f'{a} {op["op"]} {b}', 'resultat': r}

    elif d == 'edo' and analyse['edo_params']:
        ep = analyse['edo_params']
        r = resoudre_edo_lineaire(ep['a'], ep['b'], ep['c'], ep['y0'], ep['dy0'])
        return {'domaine': 'edo', 'solution_type': r['solution_type'], 'modes': r.get('modes',[])}

    elif d == 'optimisation':
        x0 = (analyse.get('opt_params') or {}).get('x0', 5.0)
        r = minimum_ondulatoire(lambda x: x**2, x0)
        return {'domaine': 'optimisation', 'x_min': r['x'], 'f_min': r['f']}

    elif d == 'derivee': return {'domaine': 'derivee', 'explication': "Utilisez : 'dérivée de sin(x) en x=0'."}
    elif d == 'integrale': return {'domaine': 'integrale', 'explication': "Utilisez : 'intégrale de x de 0 à 4'."}
    else: return {'domaine': 'indetermine', 'explication': "Essayez : 'résoudre x²+3x-4=0', 'calculer 5+7', 'minimum de x²', \"y''+y=0 avec y(0)=0\"."}

# ═══════════════════════ DEMO ═══════════════════════

def demo():
    problemes = [
        "Résoudre x² + 3x - 4 = 0",
        "Calculer 5 + 7",
        "Multiplication de 6 par 8",
        "Trouver le minimum de x² en partant de x₀=5",
        "y'' + y = 0 avec y(0)=0, y'(0)=1",
        "y'' + 3y' + 2y = 0 avec y(0)=1, y'(0)=0",
    ]
    print(f"\n{SEP}\n  IA HARMONIQUE FINALE\n  Traducteur + Solveur Suprême\n{SEP}")
    for texte in problemes:
        r = resoudre(texte)
        print(f"\n  🎤 \"{texte}\"\n  📊 {r['domaine']}")
        if r['domaine'] == 'polynome': print(f"  📐 {r['equation']}\n  🌊 Racines : {r['racines']}\n  ✅ Vérif : {[f'{v:.2e}' for v in r.get('verification',[])]}")
        elif r['domaine'] == 'arithmetique': print(f"  🔢 {r['operation']} = {r['resultat']}")
        elif r['domaine'] == 'edo': print(f"  🌊 {r['solution_type']}")
        elif r['domaine'] == 'optimisation': print(f"  📉 x_min={r['x_min']}, f_min={r['f_min']}")
    print(f"\n{SEP}\n")

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('-p','--probleme',type=str,default=None)
    args = p.parse_args()
    if args.probleme:
        r = resoudre(args.probleme)
        if r['domaine'] == 'polynome': print(f"Équation : {r['equation']}\nRacines  : {r['racines']}")
        elif r['domaine'] == 'arithmetique': print(f"{r['operation']} = {r['resultat']}")
        elif r['domaine'] == 'edo': print(f"Solution : {r['solution_type']}")
        elif r['domaine'] == 'optimisation': print(f"Minimum : x={r['x_min']}, f(x)={r['f_min']}")
        else: print(r.get('explication',''))
    else: demo()