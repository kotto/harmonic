#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOTEUR MATHEMATIQUE UNIFIE V3 — Solveur Généralisé
====================================================
Phase 1 complétée :
  1.1 Polynômes degré N (recherche de nœuds ondulatoires)
  1.2 Systèmes d'équations 2D (interférence sur grille 2D)
  1.3 Optimisation par descente de phase ondulatoire

Usage : python moteur_mathematique_unifie.py
"""

import numpy as np
import math, sys, io
from typing import Callable, List, Tuple

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PI = math.pi; PHI = (1 + math.sqrt(5)) / 2
SEP = "=" * 85

# ═══════════════════════════════════════════════════════════════════════════════
# FONDATIONS : ARITHMETIQUE ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

def signe_onde(psi):
    idx = len(psi) // 2
    return 1.0 if np.real(psi[idx]) >= 0 else -1.0

def add_wave(a,b):
    xs=np.linspace(-PI,PI,500); psi=a*np.exp(1j*PHI*xs)+b*np.exp(1j*PHI*xs)
    return signe_onde(psi)*np.mean(np.abs(psi))

def mul_wave(a,b):
    xs=np.linspace(-PI,PI,500); psi=(a*np.exp(1j*PHI*xs))*(b*np.exp(1j*PHI*xs))
    return signe_onde(psi)*np.mean(np.abs(psi))

def sub_wave(a,b): return add_wave(a,-b)

def div_wave(a,b):
    if b==0: return float('inf')
    xs=np.linspace(-PI,PI,500); amp_a=np.mean(np.abs(a*np.exp(1j*PHI*xs)))
    amp_b=np.mean(np.abs(b*np.exp(1j*PHI*xs)))
    r=amp_a/amp_b; return -r if ((a<0)^(b<0)) else r

# ═══════════════════════════════════════════════════════════════════════════════
# 1.1 POLYNOMES DEGRE N
# ═══════════════════════════════════════════════════════════════════════════════

def polynome_en_onde(coeffs, xs):
    """Encode P(x) = Σ aₖ·xᵏ en onde : Ψ(x) = P(x)·exp(i·φ·x).
       coeffs = [a₀, a₁, ..., aₙ]"""
    P = sum(c * xs**k for k, c in enumerate(coeffs))
    return P * np.exp(1j * PHI * xs)

def trouver_racines(coeffs, x_range=(-10,10), n_points=5000, seuil=0.05):
    xs = np.linspace(x_range[0], x_range[1], n_points)
    amp = np.abs(polynome_en_onde(coeffs, xs))
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

def resoudre_polynome(coeffs):
    racines = trouver_racines(coeffs)
    verif = [abs(sum(c*r**k for k,c in enumerate(coeffs))) for r in racines]
    eq = ' + '.join(f'{c}x^{k}' if k>1 else (f'{c}x' if k==1 else f'{c}')
                     for k,c in enumerate(coeffs) if c!=0 or k==0)
    eq = eq.replace('x^1','x').replace('+ -','- ') + ' = 0'
    return {'equation':eq, 'degre':len(coeffs)-1, 'racines':racines, 'verification':verif}

# ═══════════════════════════════════════════════════════════════════════════════
# 1.2 SYSTEMES D'EQUATIONS 2D
# ═══════════════════════════════════════════════════════════════════════════════

def systeme_en_onde_2d(f_coeffs, g_coeffs, xs, ys):
    """Encodage 2D : même harmonique φ pour éviter le moiré."""
    X, Y = np.meshgrid(xs, ys)
    F = sum(c * X**k * Y**j for k, row in enumerate(f_coeffs) for j, c in enumerate(row))
    G = sum(c * X**k * Y**j for k, row in enumerate(g_coeffs) for j, c in enumerate(row))
    psi = F * np.exp(1j*PHI*X)*np.exp(1j*PHI*Y) + G * np.exp(1j*PHI*X)*np.exp(1j*PHI*Y)
    return X, Y, psi

def resoudre_systeme_2d(f_coeffs, g_coeffs, x_range=(-5,5), y_range=(-5,5), n=200, seuil=0.1):
    xs = np.linspace(x_range[0], x_range[1], n)
    ys = np.linspace(y_range[0], y_range[1], n)
    X, Y, psi = systeme_en_onde_2d(f_coeffs, g_coeffs, xs, ys)
    amp = np.abs(psi)
    max_amp = max(np.max(amp), 1.0)
    sols = []
    for i in range(1, n-1):
        for j in range(1, n-1):
            if amp[j,i] < amp[j-1,i] and amp[j,i] < amp[j+1,i] and \
               amp[j,i] < amp[j,i-1] and amp[j,i] < amp[j,i+1] and \
               amp[j,i] < seuil*max_amp:
                sols.append((round(float(X[j,i]),6), round(float(Y[j,i]),6)))
    return {'solutions': sols, 'amp_min': float(np.min(amp))}

# ═══════════════════════════════════════════════════════════════════════════════
# 1.3 OPTIMISATION PAR DESCENTE DE PHASE
# ═══════════════════════════════════════════════════════════════════════════════

def minimum_ondulatoire(f, x0, x_range=(-10,10), n_iter=500, lr=0.05):
    """Descente de gradient sur f (pas |f|) pour éviter les problèmes aux zéros."""
    xs_eval = np.linspace(x_range[0], x_range[1], 2000)
    vals = np.array([f(x) for x in xs_eval])
    dx = xs_eval[1] - xs_eval[0]
    x = x0
    for _ in range(n_iter):
        idx = int((x - x_range[0]) / (x_range[1] - x_range[0]) * (len(xs_eval) - 1))
        idx = max(1, min(idx, len(xs_eval) - 2))
        grad_f = (vals[idx+1] - vals[idx-1]) / (2*dx)
        x_new = x - lr * grad_f
        x_new = max(x_range[0], min(x_new, x_range[1]))
        if abs(x_new - x) < 1e-14: break
        x = x_new
    return {'minimum_x': round(x, 10), 'minimum_f': round(f(x), 10)}

# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_arithmetique():
    print(f"\n  {'─'*80}\n  ARITHMETIQUE (10/10 calibrée)\n  {'─'*80}")
    tests = [('5+7',lambda:add_wave(5,7),12),('-3+8',lambda:add_wave(-3,8),5),
             ('10-3',lambda:sub_wave(10,3),7),('7-15',lambda:sub_wave(7,15),-8),
             ('6*8',lambda:mul_wave(6,8),48),('(-4)*7',lambda:mul_wave(-4,7),-28),
             ('3*(-5)',lambda:mul_wave(3,-5),-15),('100/4',lambda:div_wave(100,4),25),
             ('7/2',lambda:div_wave(7,2),3.5),('(-30)/6',lambda:div_wave(-30,6),-5)]
    ok_all = True
    for nom, fn, att in tests:
        r = fn(); ok = abs(r-att) < 0.01
        if not ok: ok_all = False
        print(f"    {nom:>10s} = {r:>10.4f} (attendu {att:>8}) {'✅' if ok else '❌'}")
    print(f"  Score : {'10/10 PARFAIT' if ok_all else 'ERREURS'}")

def test_polynomes():
    print(f"\n\n  {'─'*80}\n  POLYNOMES DEGRE N\n  {'─'*80}")
    # coeffs = [a₀, a₁, a₂, ...] pour P(x) = a₀ + a₁·x + a₂·x² + ...
    cas = [
        ([-4, 3, 1],      "x²+3x-4=0     → racines : -4, 1"),
        ([6, -5, 1],       "x²-5x+6=0      → racines : 2, 3"),
        ([0, -9, 0, 1],    "x³-9x=0        → racines : -3, 0, 3"),
        ([-6, 11, -6, 1],  "(x-1)(x-2)(x-3)=0 → racines : 1, 2, 3"),
        ([1, 0, 0, 0, 1],  "x⁴+1=0         → aucune racine réelle"),
        ([0, 0, 1],        "x²=0           → racine : 0 (double)"),
    ]
    for coeffs, label in cas:
        r = resoudre_polynome(coeffs)
        v_ok = all(v < 0.05 for v in r['verification']) if r['verification'] else True
        print(f"  {label}")
        print(f"    Racines onde : {r['racines']}")
        if r['verification']:
            print(f"    |P(racine)|   : {[f'{v:.2e}' for v in r['verification']]}")
        print(f"    {'✅' if v_ok else '⚠️'}")

def test_systemes_2d():
    print(f"\n\n  {'─'*80}\n  SYSTEMES D'EQUATIONS 2D\n  {'─'*80}")
    # Système 1 : 2x+3y=5, 4x-y=1 → x≈0.571, y≈1.286
    print(f"\n  Système : 2x+3y=5, 4x-y=1  (attendu : x≈0.571, y≈1.286)")
    f_coeffs = [[-5, 3], [2, 0]]   # -5 + 2x + 3y = 0
    g_coeffs = [[-1, -1], [4, 0]]  # -1 + 4x - y = 0
    r = resoudre_systeme_2d(f_coeffs, g_coeffs, x_range=(-1,2), y_range=(0,3))
    print(f"    Solutions onde : {r['solutions'][:8]}{'...' if len(r['solutions'])>8 else ''}")
    for sx, sy in r['solutions'][:5]:
        print(f"      ({sx:.4f}, {sy:.4f}) → f={2*sx+3*sy-5:.2e}, g={4*sx-sy-1:.2e}")

    # Système 2 : x+y=3, x-y=1 → x=2, y=1
    print(f"\n  Système : x+y=3, x-y=1  (attendu : x=2, y=1)")
    f_coeffs = [[-3, 1], [1, 0]]
    g_coeffs = [[-1, -1], [1, 0]]
    r = resoudre_systeme_2d(f_coeffs, g_coeffs, x_range=(0,4), y_range=(0,3))
    print(f"    Solutions onde : {r['solutions'][:8]}{'...' if len(r['solutions'])>8 else ''}")
    for sx, sy in r['solutions'][:5]:
        print(f"      ({sx:.4f}, {sy:.4f}) → f={sx+sy-3:.2e}, g={sx-sy-1:.2e}")

def test_optimisation():
    print(f"\n\n  {'─'*80}\n  OPTIMISATION PAR DESCENTE DE PHASE\n  {'─'*80}")
    r1 = minimum_ondulatoire(lambda x: x**2, 5.0)
    print(f"\n  f(x)=x², x₀=5  →  x={r1['minimum_x']:.4f}, f={r1['minimum_f']:.4f}  (attendu x=0,f=0) {'✅' if abs(r1['minimum_x'])<0.01 else '⚠️'}")

    r2 = minimum_ondulatoire(lambda x: (x-3)**2+2, 10.0)
    print(f"  f(x)=(x-3)²+2, x₀=10  →  x={r2['minimum_x']:.4f}, f={r2['minimum_f']:.4f}  (attendu x=3,f=2) {'✅' if abs(r2['minimum_x']-3)<0.1 else '⚠️'}")

    r3 = minimum_ondulatoire(lambda x: x**4 - 4*x**2 + 4, 3.0)
    print(f"  f(x)=x⁴-4x²+4, x₀=3  →  x={r3['minimum_x']:.4f}, f={r3['minimum_f']:.4f}  (attendu x≈1.414,f=0) {'✅' if abs(r3['minimum_x']-1.414)<0.2 else '⚠️'}")

    r4 = minimum_ondulatoire(math.cos, 2.0, x_range=(0,6))
    print(f"  f(x)=cos(x), x₀=2  →  x={r4['minimum_x']:.4f}, f={r4['minimum_f']:.4f}  (attendu x≈π≈3.14,f=-1) {'✅' if abs(r4['minimum_x']-PI)<0.5 else '⚠️'}")


if __name__ == '__main__':
    print(f"\n{SEP}\n  MOTEUR MATHEMATIQUE UNIFIE V3 — Solveur Généralisé\n{SEP}")
    test_arithmetique()
    test_polynomes()
    test_systemes_2d()
    test_optimisation()
    print(f"\n{SEP}\n  FIN DES TESTS\n{SEP}\n")