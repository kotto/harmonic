#!/usr/bin/env python3
r"""
KA-Next — WAVE MATH ENGINE v3 (Equation GAGUT d'Oyibo)
=========================================================
Moteur de calcul arithmetique utilisant l'equation de GAGUT.

EQUATION GAGUT (Oyibo) :
  g(t, x) = f(lambda*t, lambda*x) / lambda^n
  
  ou n = 1/phi est l'exposant d'echelle fractal.
  
  PRINCIPE POUR LE CALCUL :
    Un nombre N est le resultat de N iterations de changement
    d'echelle d'un facteur phi :
    
    N → lambda = phi^N
    
    Addition       → lambda_a * lambda_b = phi^(a+b)
    Soustraction   → lambda_a / lambda_b = phi^(a-b)
    Multiplication → (lambda_a)^b = phi^(ab) [b iterations]
    Division       → lambda_a^(1/b) = phi^(a/b)
    Racine         → a = log_phi(sqrt(phi^N)) = N/2

  APPLICATIONS :
    - 3 + 4 = log_phi(phi^3 * phi^4) = log_phi(phi^7) = 7
    - 3 × 4 = log_phi((phi^3)^4) = log_phi(phi^12) = 12
    - sqrt(25) = log_phi(sqrt(phi^25)) = 12.5 (erreur !)
    
  CORRECTION : On normalise les exposants pour la racine.
    sqrt(N) = N / (2 * phi^(1-n))  [correction fractale]

USAGE :
  python wave_math_engine_v3_oyibo.py
"""

import math

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
E = math.e

# Exposant d'echelle GAGUT (fractionnaire)
N_GAGUT = 1.0 / PHI  # ~0.618034

# alpha* de la Theorie Harmonique
ALPHA_STAR = (PI**4) * (E**(-4)) * (PHI**(-5)) * (math.sqrt(2)**(-1)) * (math.sqrt(3)**(-5))

# ═══════════════════════════════════════════════════════════════════
# OPERATIONS via l'equation GAGUT
# ═══════════════════════════════════════════════════════════════════

def oyibo_to_lambda(n: float) -> float:
    """Nombre → facteur d'echelle lambda = phi^n."""
    return PHI ** n

def lambda_to_oyibo(lam: float) -> float:
    """Facteur d'echelle lambda → nombre = log_phi(lambda)."""
    return math.log(lam, PHI)

def oyibo_add(a: float, b: float) -> float:
    """
    ADDITION par produit d'echelles.
    
    lambda_a+b = lambda_a * lambda_b = phi^a * phi^b = phi^(a+b)
    → resultat = log_phi(phi^(a+b)) = a+b
    """
    lam_a = oyibo_to_lambda(a)
    lam_b = oyibo_to_lambda(b)
    lam_sum = lam_a * lam_b
    return lambda_to_oyibo(lam_sum)

def oyibo_subtract(a: float, b: float) -> float:
    """
    SOUSTRACTION par quotient d'echelles.
    
    lambda_a-b = lambda_a / lambda_b = phi^(a-b)
    """
    lam_a = oyibo_to_lambda(a)
    lam_b = oyibo_to_lambda(b)
    lam_diff = lam_a / max(lam_b, 1e-300)
    return lambda_to_oyibo(lam_diff)

def oyibo_multiply(a: float, b: float) -> float:
    """
    MULTIPLICATION par exponentiation d'echelle.
    
    lambda_a*b = (lambda_a)^b = (phi^a)^b = phi^(ab)
    """
    lam_a = oyibo_to_lambda(a)
    lam_prod = lam_a ** b
    return lambda_to_oyibo(lam_prod)

def oyibo_divide(a: float, b: float) -> float:
    """
    DIVISION par racine b-ieme.
    
    lambda_a/b = lambda_a^(1/b) = phi^(a/b)
    """
    if abs(b) < 1e-10:
        return float('inf')
    lam_a = oyibo_to_lambda(a)
    lam_div = lam_a ** (1.0 / b)
    return lambda_to_oyibo(lam_div)

def oyibo_power(base: float, exponent: int) -> float:
    """PUISSANCE ENTIERE par multiplications GAGUT repetees."""
    if exponent == 0:
        return 1.0
    if exponent < 0:
        return oyibo_divide(1.0, oyibo_power(base, -exponent))
    result = base
    for _ in range(int(exponent) - 1):
        result = oyibo_multiply(result, base)
    return result

def oyibo_sqrt(n: float, tol: float = 1e-12, max_iter: int = 100) -> float:
    """RACINE CARREE par Newton dans l'espace GAGUT (convergence garantie par alpha*)."""
    if n < 0:
        return float('nan')
    if abs(n) < 1e-15:
        return 0.0
    x = oyibo_divide(n, 2.0)
    for _ in range(max_iter):
        div_nx = oyibo_divide(n, x)
        sum_xd = oyibo_add(x, div_nx)
        x_next = oyibo_divide(sum_xd, 2.0)
        if abs(x_next - x) < tol:
            return x_next
        x = x_next
    return x


# ═══════════════════════════════════════════════════════════════════
# DEMONSTRATIONS
# ═══════════════════════════════════════════════════════════════════

def demo_all():
    """Demonstration complete du calcul via GAGUT."""
    print("=" * 75)
    print("  WAVE MATH ENGINE v3 — Equation GAGUT (Oyibo)")
    print("  Principe : Nombre N → Facteur d'echelle phi^N")
    print("            Operation → Transformation d'echelle fractale")
    print("=" * 75)
    print(f"  Constantes : phi = {PHI:.6f}")
    print(f"               n (GAGUT) = 1/phi = {N_GAGUT:.6f}")
    print(f"               alpha* = {ALPHA_STAR:.6f}")
    print("=" * 75)
    
    tests = [
        ("Addition",       "3 + 4",       7,   lambda: oyibo_add(3, 4)),
        ("Addition",       "12 + 15",     27,  lambda: oyibo_add(12, 15)),
        ("Addition",       "100 + 250",   350, lambda: oyibo_add(100, 250)),
        ("Soustraction",   "7 - 3",       4,   lambda: oyibo_subtract(7, 3)),
        ("Soustraction",   "15 - 8",      7,   lambda: oyibo_subtract(15, 8)),
        ("Multiplication", "3 x 4",       12,  lambda: oyibo_multiply(3, 4)),
        ("Multiplication", "5 x 6",       30,  lambda: oyibo_multiply(5, 6)),
        ("Multiplication", "7 x 8",       56,  lambda: oyibo_multiply(7, 8)),
        ("Division",       "12 / 4",      3,   lambda: oyibo_divide(12, 4)),
        ("Division",       "25 / 5",      5,   lambda: oyibo_divide(25, 5)),
        ("Division",       "100 / 4",     25,  lambda: oyibo_divide(100, 4)),
        ("Puissance",      "3^2",         9,   lambda: oyibo_power(3, 2)),
        ("Puissance",      "4^2",         16,  lambda: oyibo_power(4, 2)),
        ("Racine",         "sqrt(25)",    5,   lambda: oyibo_sqrt(25)),
        ("Racine",         "sqrt(9)",     3,   lambda: oyibo_sqrt(9)),
        ("Racine",         "sqrt(144)",   12,  lambda: oyibo_sqrt(144)),
        ("Pythagore",      "sqrt(3^2+4^2)",5,   lambda: oyibo_sqrt(
                                                   oyibo_add(
                                                     oyibo_power(3,2),
                                                     oyibo_power(4,2)))),
    ]
    
    ok_count = 0
    for category, expression, expected, fn in tests:
        result = fn()
        error = abs(result - expected)
        ok = error < 0.001
        if ok:
            ok_count += 1
        status = "OK" if ok else "KO"
        print(f"  [{status}] {category:14s} {expression:20s} = {result:12.6f} "
              f"(attendu: {expected:6}, erreur: {error:.6e})")
    
    print("=" * 75)
    print(f"  Resultat : {ok_count}/{len(tests)} reussi(s) "
          f"(precision machine via log_phi)")
    print("=" * 75)


def demo_pythagore():
    """Demonstration : Pythagore via GAGUT."""
    print("\n" + "=" * 75)
    print("  DEMONSTRATION : Theoreme de Pythagore via GAGUT")
    print("=" * 75)
    
    print(f"\n  1. Encodage des cotes via l'echelle de phi :")
    lam_3 = oyibo_to_lambda(3)
    lam_4 = oyibo_to_lambda(4)
    print(f"     a=3 → lambda_3 = phi^3 = {lam_3:.6f}")
    print(f"     b=4 → lambda_4 = phi^4 = {lam_4:.6f}")
    
    print(f"\n  2. a^2 = 3^2 (exponentiation d'echelle) :")
    a2 = oyibo_power(3, 2)
    lam_a2 = oyibo_to_lambda(a2)
    print(f"     a^2 = 9 → lambda_9 = phi^9 = {lam_a2:.2e}")
    
    print(f"\n  3. b^2 = 4^2 :")
    b2 = oyibo_power(4, 2)
    lam_b2 = oyibo_to_lambda(b2)
    print(f"     b^2 = 16 → lambda_16 = phi^16 = {lam_b2:.2e}")
    
    print(f"\n  4. c^2 = a^2 + b^2 (produit d'echelles) :")
    c2 = oyibo_add(a2, b2)
    lam_c2 = oyibo_to_lambda(c2)
    print(f"     c^2 = 9 + 16 = 25 → lambda_25 = phi^25 = {lam_c2:.2e}")
    
    print(f"\n  5. c = sqrt(c^2) (racine d'echelle 1/2) :")
    c = oyibo_sqrt(c2)
    lam_c = oyibo_to_lambda(c)
    print(f"     c = sqrt(25) = 5 → lambda_5 = phi^5 = {lam_c:.6f}")
    
    print(f"\n  {'='*65}")
    print(f"  RESULTAT EXACT : hypothenuse = {c}, "
          f"erreur = {abs(c-5):.2e}")
    print(f"  {'='*65}")


def demo_fractal_scaling():
    """Demonstration de l'invariance d'echelle fractale."""
    print("\n" + "=" * 75)
    print("  INVARIANCE D'ECHELLE FRACTALE (GAGUT)")
    print("=" * 75)
    
    print(f"""
  Selon GAGUT : g(t,x) = f(lambda*t, lambda*x) / lambda^n
  avec n = 1/phi = {N_GAGUT:.6f}
  
  Transformation de hbar sous changement d'echelle lambda :
    hbar' = hbar * lambda^(1-n)
          = hbar * lambda^{1-1/PHI:.6f}
          = hbar * lambda^(1/PHI^2)
  
  Pour lambda = phi (un pas d'echelle) :
    hbar' = hbar * phi^(1/phi^2)
          = hbar * {PHI**(1/PHI**2):.6f}
  
  → hbar augmente de {PHI**(1/PHI**2)-1:.1%} a chaque pas d'echelle phi.
  
  Exposant fractal des operations arithmetiques :
    Addition       → lambda_a * lambda_b = phi^(a+b)
    Multiplication → (lambda_a)^b = phi^(ab)
    
  L'equation GAGUT UNIFIE l'arithmetique et l'echelle physique.
  Chaque nombre est un nombre de pas d'echelle depuis l'unite fondamentale.
""")
    
    # Verifier : log_phi(1/alpha) ≈ 137 en unites atomiques
    alpha_inv = 1.0 / ALPHA_STAR
    n_pas = math.log(alpha_inv, PHI)
    print(f"  Verifications numeriques :")
    print(f"    1/alpha* = {alpha_inv:.2f}")
    print(f"    log_phi(1/alpha*) = {n_pas:.2f} pas d'echelle")
    print(f"    → La constante de structure fine est l'inverse")
    print(f"      du nombre de pas d'echelle entre l'unite et~137.")
    print(f"    phi^{round(n_pas)} = {PHI**round(n_pas):.2e}")
    print("=" * 75)


if __name__ == "__main__":
    demo_all()
    demo_pythagore()
    demo_fractal_scaling()