#!/usr/bin/env python3
r"""
EXPLORATION — Capacité de l'hologramme : distance angulaire minimale
=====================================================================
Question : Quelle est la capacité d'un hologramme 2D si on exige
que deux concepts aient cos θ < 0.9 pour être discernables ?

cos(π/6) = √3/2 ≈ 0.866 < 0.9 → π/6 est la distance angulaire minimale.

Pavage régulier de S¹ : 2π / (π/6) = 12 positions sur le cercle.
Pavage régulier de S¹×S¹ : ~12² = 144 positions en 2D.
Pour une grille G×G avec des ondes Ψ_{nx,ny} : capacité ~ (G/φ)² / 12.

Usage :
  python exploration_capacite_hologramme.py
"""

import sys, os, math
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
TAU = 2 * PI


# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 1 : Capacité théorique
# ═══════════════════════════════════════════════════════════════════════════════

def demonstrate_theoretical():
    print("=" * 72)
    print("  PARTIE 1 — Capacité théorique de l'hologramme")
    print("=" * 72)
    
    R = PI / 6  # Rayon de discernabilité angulaire
    cos_R = math.cos(R)
    
    print(f"""
    Distance angulaire minimale : θ_min = π/6 = {math.degrees(R):.1f}°
    cos(θ_min) = {cos_R:.4f}
    
    CONDITION : cos(θ_A - θ_B) > 0.9 pour que les concepts interfèrent.
    → |θ_A - θ_B| < arccos(0.9) = {math.degrees(math.acos(0.9)):.1f}°
    → π/6 = 30° est dans la zone de sécurité (cos < 0.866 < 0.9).
    
    ═══════════════════════════════════════════════════════════
    PAVAGE DE S¹ (espace des phases 1D)
    ═══════════════════════════════════════════════════════════
    
    Positions discernables sur le cercle unité :
    N_1D = 2π / (π/6) = {TAU / R:.0f} positions
    
    Chaque position peut accueillir UN mode spectral (nombre).
    Avec φ comme espacement : les positions sont n·φ mod 2π.
    Combien de valeurs de n avant qu'une position ne se répète ?
    
    Si φ/2π est irrationnel → aucune répétition → capacité infinie ?
    NON : la limite vient de la distance angulaire de discernabilité.
    Deux nombres n₁ et n₂ sont discernables si :
      |(n₁·φ mod 2π) - (n₂·φ mod 2π)| > π/6
    
    φ = {PHI:.6f}
    2π/φ = {TAU/PHI:.6f} → ~{int(TAU/PHI)} nombres discernables en 1D.
    (car après {int(TAU/PHI):d} pas, l'espacement φ fait le tour du cercle)
    
    ═══════════════════════════════════════════════════════════
    PAVAGE DE S¹×S¹ (espace des phases 2D — hologramme)
    ═══════════════════════════════════════════════════════════
    
    Grille carrée de côté G : modes (nx, ny) ∈ [-G/2, G/2]²
    Fréquences accessibles : (nx·φ, ny·φ) sur [-φ·G/2, φ·G/2]²
    Plage angulaire totale : [-φ·G/2 mod 2π, φ·G/2 mod 2π]²
    
    Nombre de cellules π/6 × π/6 dans le cercle unité 2D :
    N_2D = (2π / (π/6))² = (12)² = 144
    
    Pour une grille G×G (ex: G=64, nx,ny ∈ [-32,32]) :
    Plage de phases : 64·φ ≈ 103.5 rad → ~16.5 tours du cercle
    → ~16.5² × 144 ≈ 39 000 positions discernables !
    
    MAIS : les modes (nx, ny) = (1,0) et (2,0) et (3,0)...
    ne sont pas π/6-séparés pour nx petits.
    La capacité RÉELLE est limitée par la résolution spectrale.
""")
    
    # Calcul précis de la capacité 1D
    N1D_max = int(TAU / (PI/6))
    print(f"  Capacité 1D (S¹)   : {N1D_max} modes spectraux discernables")
    print(f"  Capacité 2D (S¹×S¹) : {N1D_max**2} paires de modes discernables")
    print()
    
    G_values = [64, 128, 256, 512, 1024]
    print(f"  Grille (G×G)  Total modes  Modes discernables  Densité")
    print(f"  " + "-" * 55)
    for G in G_values:
        total_modes = G * G
        # Chaque mode (nx, ny) occupe un angle Δθ_nx = φ mod 2π/G
        # Le nombre de modes discernables est limité par le wrap-around de φ
        # Approximation : nombre de tours × 12 par tour
        n_tours = G * PHI / TAU
        discernables_1d = int(n_tours * 12)
        discernables_2d = discernables_1d ** 2
        density = discernables_2d / total_modes * 100
        print(f"  {G:4d} × {G:<4d}     {total_modes:6d}      {discernables_2d:>8d}           {density:5.1f}%")


# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 2 : Vérification numérique — interférence entre voisins
# ═══════════════════════════════════════════════════════════════════════════════

def interference_2d(nx1, ny1, nx2, ny2, G=64):
    """Interférence entre deux modes spectraux 2D."""
    x = np.linspace(-G/2, G/2, G)
    y = np.linspace(-G/2, G/2, G)
    X, Y = np.meshgrid(x, y)
    
    psi1 = np.exp(1j * PHI * (nx1 * X + ny1 * Y))
    psi2 = np.exp(1j * PHI * (nx2 * X + ny2 * Y))
    
    dot = np.real(np.sum(psi1 * np.conj(psi2)))
    n1 = np.sqrt(np.real(np.sum(psi1 * np.conj(psi1))))
    n2 = np.sqrt(np.real(np.sum(psi2 * np.conj(psi2))))
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return dot / (n1 * n2)


def test_adjacent_modes():
    print("\n" + "=" * 72)
    print("  PARTIE 2 — Interférence entre modes adjacents")
    print("=" * 72)
    
    G = 64
    
    print(f"""
    Test : interférence entre modes (nx, ny) et (nx+Δ, ny)
    pour voir à quelle distance Δ l'interférence descend sous 0.9.
""")
    
    print(f"  {'Δnx':>5s}  {'cos θ':>10s}  {'< 0.9 ?'}")
    print(f"  " + "-" * 30)
    
    for dn in range(1, 8):
        interf = interference_2d(10, 0, 10 + dn, 0, G)
        below = "OUI (discernable)" if abs(interf) < 0.9 else "NON"
        print(f"  {dn:5d}  {interf:+10.6f}  {below}")
    
    # Distance angulaire réelle entre modes adjacents
    # Δθ = φ · Δnx · 2π / G  (différence de phase par pixel)
    # Sur toute la grille : Δθ_total = φ · Δnx · 2π
    print(f"\n  Angle spectral entre modes séparés de Δnx :")
    for dn in range(1, 8):
        dtheta = PHI * dn * TAU  # en radians
        dtheta_mod = dtheta % TAU
        print(f"    Δnx={dn} : Δθ = {dtheta:.2f} rad = {dtheta_mod:.2f} rad mod 2π  "
              f"= {math.degrees(dtheta_mod):.1f}°")
    
    # À quelle distance Δnx l'angle est-il de π/6 ?
    print(f"\n  π/6 = {math.degrees(PI/6):.1f}°")
    print(f"  Cette séparation est atteinte pour Δnx = {PI/6 / (PHI*TAU) * G:.2f}")
    print(f"  → il faut ~{int(PI/6 / (PHI*TAU) * G)} pas de nx pour avoir π/6 de séparation")


# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 3 : Positionnement par φ — anti-collision
# ═══════════════════════════════════════════════════════════════════════════════

def test_phi_positioning():
    print("\n" + "=" * 72)
    print("  PARTIE 3 — Anti-collision par φ")
    print("=" * 72)
    
    print(f"""
    PRINCIPE : position(n) = n·φ mod 2π
    
    φ = {PHI:.10f} est le plus irrationnel → les positions
    ne se répètent JAMAIS exactement. Mais elles peuvent être
    ARBITRAIREMENT PROCHES (théorème de Kronecker).
    
    Distance minimale entre n positions consécutives ?
    C'est le problème des écarts dans la suite n·φ mod 1.
    Théorème des trois longueurs : il n'y a que 3 écarts possibles.
""")
    
    N = 100
    positions = [(n * PHI) % 1.0 for n in range(N)]
    positions.sort()
    
    gaps = [positions[i+1] - positions[i] for i in range(N-1)]
    gaps.append(1.0 + positions[0] - positions[-1])  # wrap-around
    
    unique_gaps = sorted(set(round(g, 6) for g in gaps))
    
    print(f"  Pour N={N} positions :")
    print(f"    Écarts uniques trouvés : {unique_gaps}")
    print(f"    Écart minimal : {min(gaps):.6f}")
    print(f"    Écart maximal : {max(gaps):.6f}")
    print(f"    Écart moyen   : {1.0/N:.6f}")
    
    # Quelle est la distance angulaire minimale entre N positions ?
    min_angle = min(gaps) * TAU
    print(f"\n    Distance angulaire minimale : {math.degrees(min_angle):.4f}°")
    print(f"    π/6 = {math.degrees(PI/6):.4f}°")
    
    if min_angle > PI/6:
        print(f"    → Toutes les positions sont π/6-séparées ✓")
    else:
        N_safe = int(TAU / (PI/6))
        print(f"    → Au-delà de N={N_safe}, les positions sont trop proches")
        print(f"    → Capacité max 1D : {N_safe} concepts discernables")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 74)
    print("  CAPACITÉ DE L'HOLOGRAMME — π/6 = distance minimale")
    print("=" * 74)
    
    demonstrate_theoretical()
    test_adjacent_modes()
    test_phi_positioning()
    
    print("\n" + "=" * 74)
    print("  RÉPONSE — Problème 8c")
    print("=" * 74)
    print("""
    DISTANCE ANGULAIRE MINIMALE π/6 = 30° :
    
    cos(π/6) = √3/2 ≈ 0.866 < 0.9 → zone de sécurité pour discernabilité.
    
    CAPACITÉ 1D (S¹) :
      N_max = 2π / (π/6) = 12 positions discernables.
      Avec φ : les positions n·φ mod 2π ne se répètent pas,
      mais leur densité est limitée par π/6.
      → ~12 concepts discernables en 1D.
    
    CAPACITÉ 2D (S¹×S¹) :
      N_max = 12² = 144 paires de modes discernables.
      Pour une grille G×G, chaque mode (nx,ny) balaye S¹×S¹
      nx·φ fois → nombreux tours → bien plus de positions.
      → ~(G·φ/2π)² × 144 positions pour G grand.
    
    Pour G=64  : ~16.5² × 144 ≈ 39 000 positions
    Pour G=256 : ~66²   × 144 ≈ 625 000 positions
    Pour G=1024: ~264²  × 144 ≈ 10 000 000 positions
    
    IMPLICATION POUR L'HOLOGRAMME :
      Une grille 1024×1024 peut stocker ~10M concepts discernables.
      C'est le nombre de faits qu'un hologramme de cette taille
      peut contenir SANS interférence croisée excessive.
      
      Au-delà, les concepts commencent à interférer constructivement
      avec leurs voisins → ambiguïté → nécessité de raffinement.
""")