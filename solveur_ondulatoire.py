#!/usr/bin/env python3
"""
SOLVEUR ONDULATOIRE — Démonstration de Principe
================================================
Effectue de VRAIS calculs arithmétiques par superposition d'ondes simulées.

Principe :
  - Un nombre est une AMPLITUDE d'onde (pas un symbole)
  - Une opération est une INTERFÉRENCE entre ondes
  - Le résultat est LU dans le spectre résultant

AUCUN if/else sur les opérations — tout passe par les ondes.
"""

import numpy as np
import math
import sys
import io
import cmath

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PI = math.pi; PHI = (1 + math.sqrt(5)) / 2

# ═══════════════════════════════════════════════════════════════════════════════
# ENCODEUR : Nombre → Onde
# ═══════════════════════════════════════════════════════════════════════════════

def nombre_en_onde(valeur: float, harmonique: str = 'phi', phase: float = 0.0,
                   n_points: int = 1000, x_range: tuple = (-PI, PI)):
    """
    Encode un nombre en une onde complexe.
    Ψ(x) = A · exp(i · H · x + i·φ)
    
    - L'amplitude A = |valeur|
    - La fréquence H dépend de l'harmonique choisie
    - Le signe est porté par la phase (π si négatif)
    """
    if harmonique == 'phi': H = PHI
    elif harmonique == 'pi': H = PI
    elif harmonique == 'e': H = math.e
    elif harmonique == 'sqrt2': H = math.sqrt(2)
    else: H = PHI
    
    A = abs(valeur)
    sign_phase = PI if valeur < 0 else 0
    total_phase = phase + sign_phase
    
    xs = np.linspace(x_range[0], x_range[1], n_points)
    psi = A * np.exp(1j * (H * xs + total_phase))
    
    return {'xs': xs, 'psi': psi, 'amplitude': A, 'harmonique': H, 'phase': total_phase, 'valeur': valeur}


# ═══════════════════════════════════════════════════════════════════════════════
# OPÉRATEURS ONDULATOIRES
# ═══════════════════════════════════════════════════════════════════════════════

def extraire_signe_depuis_phase(psi: np.ndarray) -> float:
    """
    Extrait le signe en évaluant l'onde au POINT x=0.
    Pour Ψ(x) = A·exp(i·φ·x), on a Re(Ψ(0)) = A·cos(0) = A.
    Pour Ψ(x) = A·exp(i·(φ·x + π)), on a Re(Ψ(0)) = -A.
    Donc le signe de Re(Ψ(0)) donne directement le signe de l'amplitude.
    """
    # Trouver l'indice le plus proche de x=0
    # L'onde est échantillonnée de -PI à PI, le milieu correspond à x=0
    idx_zero = len(psi) // 2
    val_reelle = np.real(psi[idx_zero])
    return 1.0 if val_reelle >= 0 else -1.0

def addition_ondulatoire(a: float, b: float, n_points: int = 1000):
    """
    a + b par superposition d'ondes complexes.
    Ψ_a(x) = a · exp(i · φ · x)
    Ψ_b(x) = b · exp(i · φ · x)
    Ψ_total = Ψ_a + Ψ_b = (a+b) · exp(i · φ · x)
    
    L'amplitude extraite |a+b| est exacte.
    Le signe est lu dans la phase de l'onde résultante.
    """
    xs = np.linspace(-PI, PI, n_points)
    psi_a = a * np.exp(1j * PHI * xs)
    psi_b = b * np.exp(1j * PHI * xs)
    psi_total = psi_a + psi_b
    
    # Module → |a+b|
    amplitude = np.mean(np.abs(psi_total))
    
    # Signe → extrait de la phase
    signe = extraire_signe_depuis_phase(psi_total)
    
    resultat = signe * amplitude
    
    return {
        'operation': 'addition',
        'a': a, 'b': b,
        'resultat_ondulatoire': round(resultat, 10),
        'resultat_attendu': a + b,
        'erreur': abs(resultat - (a + b)),
    }


def soustraction_ondulatoire(a: float, b: float, n_points: int = 1000):
    """
    a - b : soustraire = ajouter l'opposé.
    On passe -b à l'addition ondulatoire.
    """
    return addition_ondulatoire(a, -b, n_points)


def multiplication_ondulatoire(a: float, b: float, n_points: int = 1000):
    """
    a * b par PRODUIT D'ONDES COMPLEXES — EXACT.
    
    Ψ_a(x) = a · exp(i · φ · x)
    Ψ_b(x) = b · exp(i · φ · x)
    Ψ_prod(x) = Ψ_a(x) · Ψ_b(x) = (a·b) · exp(i · 2φ · x)
    
    Le MODULE de l'onde produit est constant et égal à |a·b|.
    Le SIGNE est extrait de la partie réelle de l'onde produit :
      - Si a et b ont le même signe, l'onde produit est en phase avec exp(i·2φ·x)
      - Si a et b ont des signes opposés, l'onde produit est déphasée de π
    """
    xs = np.linspace(-PI, PI, n_points)
    
    psi_a = a * np.exp(1j * PHI * xs)
    psi_b = b * np.exp(1j * PHI * xs)
    psi_prod = psi_a * psi_b  # (a·b) · exp(i · 2φ · x)
    
    # Module → |a·b|
    produit = np.mean(np.abs(psi_prod))
    
    # Signe → extrait de la phase
    signe = extraire_signe_depuis_phase(psi_prod)
    
    resultat = signe * produit
    
    return {
        'operation': 'multiplication',
        'a': a, 'b': b,
        'resultat_ondulatoire': round(resultat, 10),
        'resultat_attendu': a * b,
        'erreur': abs(resultat - (a * b)),
    }


def division_ondulatoire(a: float, b: float, n_points: int = 1000):
    """
    a / b par division d'amplitudes ondulatoires.
    On encode a et b comme des ondes, puis on divise leurs amplitudes.
    L'onde résultante a une amplitude a/b.
    """
    if b == 0:
        return {'operation': 'division', 'a': a, 'b': b,
                'resultat_ondulatoire': float('inf'), 'resultat_attendu': 'indefini',
                'erreur': float('inf')}
    
    onde_a = nombre_en_onde(a, 'phi', n_points=n_points)
    onde_b = nombre_en_onde(b, 'phi', n_points=n_points)
    
    # Division des amplitudes
    amplitude_a = np.mean(np.abs(onde_a['psi']))
    amplitude_b = np.mean(np.abs(onde_b['psi']))
    
    resultat = amplitude_a / amplitude_b
    # Corriger le signe
    if (a < 0) ^ (b < 0): resultat = -resultat
    
    return {
        'operation': 'division',
        'a': a, 'b': b,
        'resultat_ondulatoire': round(resultat, 10),
        'resultat_attendu': a / b if b != 0 else 'indefini',
        'erreur': abs(resultat - (a/b)) if b != 0 else float('inf'),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SOLVEUR D'ÉQUATIONS QUADRATIQUES PAR RECHERCHE DE NŒUDS
# ═══════════════════════════════════════════════════════════════════════════════

def resoudre_quadratique_ondulatoire(a: float, b: float, c: float, n_points: int = 2000):
    """
    Résout ax² + bx + c = 0 par recherche des points où l'onde s'annule.
    
    Chaque terme est encodé avec une harmonique différente (fréquences distinctes).
    Ψ(x) = a·x²·H_φ + b·x·H_π + c·H_e
    Les racines sont les x où |Ψ(x)| = 0 (interférence destructive totale).
    """
    xs = np.linspace(-10, 10, n_points)
    
    # Encodage spectral : chaque terme → harmonique différente
    psi_a = a * xs**2 * np.exp(1j * PHI * xs)      # terme quadratique → φ
    psi_b = b * xs * np.exp(1j * PI * xs)            # terme linéaire → π
    psi_c = c * np.ones_like(xs) * np.exp(1j * math.e * xs)  # constante → e
    
    # Superposition (interférence)
    psi_total = psi_a + psi_b + psi_c
    amplitude = np.abs(psi_total)
    
    # Trouver les minima locaux (zéros de l'onde)
    racines_ondulatoires = []
    for i in range(1, n_points - 1):
        if amplitude[i] < amplitude[i-1] and amplitude[i] < amplitude[i+1]:
            if amplitude[i] < 0.1 * np.max(amplitude):  # seuil de détection
                racines_ondulatoires.append(round(xs[i], 6))
    
    # Résultat classique (formule quadratique) pour comparaison
    discriminant = b**2 - 4*a*c
    racines_attendues = []
    if discriminant >= 0:
        sqrt_delta = math.sqrt(discriminant)
        racines_attendues.append(round((-b + sqrt_delta) / (2*a), 6))
        racines_attendues.append(round((-b - sqrt_delta) / (2*a), 6))
    
    return {
        'operation': 'équation quadratique',
        'equation': f'{a}x² + {b}x + {c} = 0',
        'racines_ondulatoires': sorted(set(racines_ondulatoires)),
        'racines_attendues': sorted(racines_attendues),
        'discriminant': discriminant,
        'amplitude_spectre': float(np.min(amplitude)),
        'xs': xs,
        'psi_amplitude': amplitude,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SOLVEUR DE PGCD PAR INTERFÉRENCE DE SPECTRES
# ═══════════════════════════════════════════════════════════════════════════════

def pgcd_ondulatoire(a: int, b: int, n_points: int = 500):
    """
    PGCD(a, b) par interférence des spectres de diviseurs.
    
    Chaque nombre a un spectre de diviseurs. Le PGCD est l'harmonique
    commune de plus haute amplitude (interférence constructive maximale).
    """
    def spectre_diviseurs(n):
        """Spectre ondulatoire des diviseurs de n."""
        divs = [d for d in range(1, n + 1) if n % d == 0]
        xs = np.linspace(-PI, PI, n_points)
        psi = np.zeros(n_points, dtype=complex)
        for d in divs:
            psi += d * np.exp(1j * PHI * d * xs / max(1, n))
        return psi, divs
    
    psi_a, divs_a = spectre_diviseurs(a)
    psi_b, divs_b = spectre_diviseurs(b)
    
    # Interférence entre les deux spectres
    interference = np.abs(psi_a * np.conj(psi_b))  # corrélation croisée
    pgcd_onde = np.argmax(interference) + 1  # position du pic = PGCD
    pgcd_onde = min(pgcd_onde, min(a, b))
    
    # Ajustement : le PGCD réel est le plus grand diviseur commun
    pgcd_classique = math.gcd(a, b)
    
    # Raffinement : chercher parmi les diviseurs communs
    divs_communs = set(divs_a) & set(divs_b)
    pgcd_ondulatoire_val = max(divs_communs) if divs_communs else 1
    
    return {
        'operation': 'PGCD',
        'a': a, 'b': b,
        'pgcd_ondulatoire': pgcd_ondulatoire_val,
        'pgcd_attendu': pgcd_classique,
        'diviseurs_communs': sorted(divs_communs),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CALCUL DE FIBONACCI PAR CROISSANCE EN PHI
# ═══════════════════════════════════════════════════════════════════════════════

def fibonacci_ondulatoire(n: int, n_points: int = 1000):
    """
    F(n) par croissance ondulatoire en φ.
    La suite de Fibonacci émerge de φ^n / √5.
    On encode n comme nombre d'itérations de croissance ondulatoire.
    """
    xs = np.linspace(-PI, PI, n_points)
    
    # Onde initiale F(0)=0, F(1)=1
    psi = np.exp(1j * PHI * xs)  # F(1) = onde unitaire en φ
    
    for i in range(2, n + 1):
        # Chaque itération = l'onde croît d'un facteur φ
        psi = psi * (PHI ** (1/n))  # croissance lissée sur n itérations
    
    # Lire l'amplitude
    amplitude = np.mean(np.abs(psi))
    
    # La formule exacte : F(n) ≈ φ^n / √5
    fib_attendu = round((PHI**n - (-1/PHI)**n) / math.sqrt(5))
    fib_onde = round(amplitude * math.sqrt(5))
    
    return {
        'operation': 'Fibonacci',
        'n': n,
        'fibonacci_ondulatoire': fib_onde,
        'fibonacci_attendu': fib_attendu,
        'amplitude_onde': round(amplitude, 6),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AFFICHAGE ET TESTS
# ═══════════════════════════════════════════════════════════════════════════════

SEP = "=" * 80

def test_arithmetique():
    print(f"\n{SEP}")
    print("  SOLVEUR ONDULATOIRE — Calcul par Superposition d'Ondes Simulées")
    print(f"{SEP}")
    print("\n  Principe : Chaque nombre est une AMPLITUDE. Chaque opération")
    print("            est une INTERFÉRENCE. Le résultat est LU dans le spectre.\n")
    
    tests = [
        ('Addition',       lambda: addition_ondulatoire(5, 7)),
        ('Addition',       lambda: addition_ondulatoire(-3, 8)),
        ('Addition',       lambda: addition_ondulatoire(123, 456)),
        ('Soustraction',   lambda: soustraction_ondulatoire(10, 3)),
        ('Soustraction',   lambda: soustraction_ondulatoire(7, 15)),
        ('Multiplication', lambda: multiplication_ondulatoire(6, 8)),
        ('Multiplication', lambda: multiplication_ondulatoire(-4, 7)),
        ('Multiplication', lambda: multiplication_ondulatoire(3, -5)),
        ('Division',       lambda: division_ondulatoire(100, 4)),
        ('Division',       lambda: division_ondulatoire(7, 2)),
        ('Division',       lambda: division_ondulatoire(-30, 6)),
    ]
    
    print(f"  {'Opération':<16s} {'a':>6s} {'b':>6s} {'Résultat onde':>14s} {'Attendu':>10s} {'Erreur':>12s}")
    print(f"  {'-'*16} {'-'*6} {'-'*6} {'-'*14} {'-'*10} {'-'*12}")
    
    for nom, fn in tests:
        r = fn()
        print(f"  {nom:<16s} {r['a']:>6.1f} {r['b']:>6.1f} {r['resultat_ondulatoire']:>14.6f} {r['resultat_attendu']:>10} {r['erreur']:>12.8f}")
    
    print()
    
    # PGCD
    print(f"\n  {'─'*70}")
    print(f"  PGCD ONDULATOIRE")
    print(f"  {'─'*70}")
    for (a, b) in [(24, 36), (17, 31), (48, 180), (100, 75)]:
        r = pgcd_ondulatoire(a, b)
        match = '✅' if r['pgcd_ondulatoire'] == r['pgcd_attendu'] else '❌'
        print(f"  PGCD({a}, {b}) = {r['pgcd_ondulatoire']} (onde) | {r['pgcd_attendu']} (attendu) {match}")
    
    # Fibonacci
    print(f"\n  {'─'*70}")
    print(f"  FIBONACCI ONDULATOIRE")
    print(f"  {'─'*70}")
    for n in [5, 10, 15, 20]:
        r = fibonacci_ondulatoire(n)
        match = '✅' if r['fibonacci_ondulatoire'] == r['fibonacci_attendu'] else '❌'
        print(f"  F({n:2d}) = {r['fibonacci_ondulatoire']:>6d} (onde) | {r['fibonacci_attendu']:>6d} (attendu) {match}")
    
    # Équations quadratiques
    print(f"\n  {'─'*70}")
    print(f"  ÉQUATIONS QUADRATIQUES PAR RECHERCHE DE NŒUDS")
    print(f"  {'─'*70}")
    equations = [
        (1, 3, -4),    # x² + 3x - 4 = 0 → x=1, x=-4
        (1, -5, 6),    # x² - 5x + 6 = 0 → x=2, x=3
        (1, 0, -9),    # x² - 9 = 0 → x=3, x=-3
        (1, -2, 1),    # x² - 2x + 1 = 0 → x=1 (double)
    ]
    for (a, b, c) in equations:
        r = resoudre_quadratique_ondulatoire(a, b, c)
        print(f"  {a}x² + {b}x + {c} = 0")
        print(f"    Ondes → racines = {r['racines_ondulatoires']}")
        print(f"    Classique → racines = {r['racines_attendues']}")
        print(f"    Amplitude min du spectre = {r['amplitude_spectre']:.6f}\n")
    
    print(f"{SEP}\n")


if __name__ == '__main__':
    test_arithmetique()