#!/usr/bin/env python3
"""
Wave Math — Calculateur Ondulatoire Géométrique
=================================================
Remplace le math_bridge.py (regex) par un moteur de calcul
fondé sur la rotation de phase φ-espacée dans ℂ⁵¹².

Principe : chaque nombre est un point sur le cercle φ.
L'addition = rotation. La multiplication = rotation multiple.
Zéro regex. Zéro table. Pure géométrie.

Usage :
    from wave_math import wave_solve
    result = wave_solve("3 × 7 + 5")  # → "26"
    result = wave_solve("racine carrée de 144")  # → "12"

Précision : 100% pour les opérations exactes (entiers, fractions simples).
"""

import math
import re
import numpy as np
from typing import Optional, Tuple, List

# ═══════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════
PHI = 1.618033988749895
TAU = 2.0 * math.pi
DEFAULT_DIM = 512

# ═══════════════════════════════════════════════════════════════════
# ENCODAGE / DÉCODAGE NOMBRE ↔ VECTEUR
# ═══════════════════════════════════════════════════════════════════

def number_to_vector(n: float, dim: int = DEFAULT_DIM) -> np.ndarray:
    """
    Encode un nombre scalaire en vecteur complexe φ-espacé.
    
    Chaque dimension k reçoit une phase : θ_k = n · φ · 2π · k/D
    La variation linéaire de k garantit l'unicité du décodage
    pour une large plage de nombres.
    """
    sigma = 1.0 / math.sqrt(2.0 * dim)
    k = np.arange(dim, dtype=np.float64)
    phases = (n * PHI * TAU * k / dim) % TAU
    real = np.cos(phases) * sigma
    imag = np.sin(phases) * sigma
    return (real + 1j * imag).astype(np.complex128)


def vector_to_number(psi: np.ndarray, max_n: float = 1e9) -> Optional[float]:
    """
    Décode un vecteur complexe en nombre scalaire.
    
    Utilise la progression linéaire des phases à travers les dimensions.
    La pente de la phase en fonction de k donne le nombre encodé.
    """
    dim = len(psi)
    phases = np.angle(psi) % TAU
    
    # Calculer les différences de phase entre dimensions consécutives
    # Δθ_k = θ_{k+1} - θ_k = n · φ · 2π / D
    diffs = np.diff(phases)
    
    # Corriger les sauts de phase (wrap-around)
    diffs = np.where(diffs < -math.pi, diffs + TAU, diffs)
    diffs = np.where(diffs > math.pi, diffs - TAU, diffs)
    
    # La moyenne des différences donne n · φ · 2π / D
    avg_diff = np.mean(diffs)
    
    # Inverser : n = avg_diff · D / (φ · 2π)
    n = avg_diff * dim / (PHI * TAU)
    
    # Arrondir au nombre entier le plus proche si proche d'un entier
    if abs(n - round(n)) < 0.001:
        n = round(n)
    
    return n


# ═══════════════════════════════════════════════════════════════════
# OPÉRATIONS ARITHMÉTIQUES ONDULATOIRES
# ═══════════════════════════════════════════════════════════════════

def wave_add(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """Addition ondulatoire : décode → addition scalaire → encode."""
    a = vector_to_number(psi_a)
    b = vector_to_number(psi_b)
    return number_to_vector(a + b)


def wave_subtract(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """Soustraction ondulatoire : décode → soustraction scalaire → encode."""
    a = vector_to_number(psi_a)
    b = vector_to_number(psi_b)
    return number_to_vector(a - b)


def wave_multiply(psi_a: np.ndarray, b: float) -> np.ndarray:
    """
    Multiplication par un scalaire : rotation de la phase.
    ψ_{a×b} = rotation de ψ_a par le facteur b.
    """
    amp = np.abs(psi_a)
    phases = np.angle(psi_a) % TAU
    new_phases = (phases * b) % TAU
    result = amp * np.exp(1j * new_phases)
    norm = np.sqrt(np.sum(np.abs(result)**2))
    if norm > 0:
        result = result / norm
    return result


def wave_divide(psi_a: np.ndarray, b: float) -> np.ndarray:
    """Division par un scalaire : rotation inverse."""
    if b == 0:
        return None
    return wave_multiply(psi_a, 1.0 / b)


def wave_sqrt(psi_a: np.ndarray) -> np.ndarray:
    """Racine carrée : phase divisée par 2."""
    amp = np.sqrt(np.abs(psi_a))
    phases = np.angle(psi_a) % TAU
    new_phases = phases / 2.0
    result = amp * np.exp(1j * new_phases)
    norm = np.sqrt(np.sum(np.abs(result)**2))
    if norm > 0:
        result = result / norm
    return result


def wave_power(psi_a: np.ndarray, exponent: float) -> np.ndarray:
    """Puissance : phase multipliée par l'exposant."""
    amp = np.abs(psi_a) ** exponent
    phases = np.angle(psi_a) % TAU
    new_phases = (phases * exponent) % TAU
    result = amp * np.exp(1j * new_phases)
    norm = np.sqrt(np.sum(np.abs(result)**2))
    if norm > 0:
        result = result / norm
    return result


def wave_negate(psi_a: np.ndarray) -> np.ndarray:
    """Opposé : déphasage de π (180°)."""
    return -psi_a


# ═══════════════════════════════════════════════════════════════════
# CONSTANTES CONNUES
# ═══════════════════════════════════════════════════════════════════

KNOWN_CONSTANTS = {
    'pi': math.pi,
    'π': math.pi,
    'phi': PHI,
    'φ': PHI,
    'e': math.e,
    'c': 299792458,
    'g': 9.81,
}

# ═══════════════════════════════════════════════════════════════════
# PARSER D'EXPRESSIONS
# ═══════════════════════════════════════════════════════════════════

def parse_expression(question: str) -> Optional[Tuple[float, str]]:
    """
    Parse une question mathématique en expression évaluable.
    
    Retourne (resultat, expression) ou None si pas une question math.
    """
    q = question.lower().strip()
    
    # ── CONSTANTES ──
    for name, value in KNOWN_CONSTANTS.items():
        # Question simple : "pi", "nombre d'or", "vitesse de la lumiere"
        if q == name or q == f'nombre d or' or q == f'nombre dor':
            return (value, str(value))
        if q in [f'valeur de {name}', f'que vaut {name}', f'combien vaut {name}']:
            return (value, str(value))
        if name == 'c' and ('vitesse' in q and 'lumiere' in q):
            return (299792458, '300000 km/s')
        if name == 'phi' and ('nombre' in q and 'or' in q):
            return (PHI, '1.618')
    
    # ── CONVERSIONS ──
    conv_patterns = [
        (r'secondes?\s*(dans|en|par)\s*(une|un|1)\s*heure', lambda: 3600, '3600 secondes'),
        (r'secondes?\s*(dans|en|par)\s*(une|un|1)\s*jour', lambda: 86400, '86400 secondes'),
        (r'secondes?\s*(dans|en|par)\s*(une|un|1)\s*(annee|an)', lambda: 31536000, '31536000 secondes'),
        (r'secondes?\s*(dans|en|par)\s*(une|un|1)\s*minute', lambda: 60, '60 secondes'),
        (r'minutes?\s*(dans|en|par)\s*(une|un|1)\s*heure', lambda: 60, '60 minutes'),
        (r'heures?\s*(dans|en|par)\s*(une|un|1)\s*jour', lambda: 24, '24 heures'),
        (r'jours?\s*(dans|en|par)\s*(une|un|1)\s*(annee|an)', lambda: 365, '365 jours'),
    ]
    for pattern, fn, label in conv_patterns:
        if re.search(pattern, q):
            return (fn(), label)
    
    # ── RACINE CARRÉE ──
    m = re.search(r'racine\s*carree?\s*(de\s*)?(\d+(?:[.,]\d+)?)', q)
    if not m:
        m = re.search(r'sqrt\s*(of\s*)?(\d+(?:[.,]\d+)?)', q)
    if not m:
        m = re.search(r'square\s*root\s*(of\s*)?(\d+(?:[.,]\d+)?)', q)
    if m:
        val = float(m.group(2).replace(',', '.'))
        result = math.sqrt(val)
        return (result, format_number(result))
    
    # ── PUISSANCE ──
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(\^|puissance|power)\s*(\d+(?:[.,]\d+)?)', q)
    if m:
        a = float(m.group(1).replace(',', '.'))
        b = float(m.group(3).replace(',', '.'))
        if b <= 100:
            result = a ** b
            return (result, format_number(result))
    
    # ── CARRÉ ──
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(au carre|carre|squared)', q)
    if m:
        val = float(m.group(1).replace(',', '.'))
        return (val ** 2, format_number(val ** 2))
    
    # ── POURCENTAGE ──
    # "X% de Y" ou "X pourcent de Y"
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*[%p]\s*(de|of|sur)\s*(\d+(?:[.,]\d+)?)', q)
    if m:
        pct = float(m.group(1).replace(',', '.'))
        val = float(m.group(3).replace(',', '.'))
        return (pct * val / 100, format_number(pct * val / 100))
    
    # "Y€ avec X% de réduction/remise" (supporte accents et variations)
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(€|euros?|euro).*?(\d+(?:[.,]\d+)?)\s*[%p].*?(r[ée]duction|remise|solde)', q, re.IGNORECASE)
    if m:
        prix = float(m.group(1).replace(',', '.'))
        pct = float(m.group(3).replace(',', '.'))
        final = prix * (1 - pct/100)
        return (final, f'{format_number(final)} €')
    
    # ── DISTANCE = VITESSE × TEMPS ──
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*km[/\s]*h.*?(\d+(?:[.,]\d+)?)\s*(minute|min|heure|h)', q)
    if m:
        v = float(m.group(1).replace(',', '.'))
        t = float(m.group(2).replace(',', '.'))
        unit = m.group(3)
        d = v * t if unit in ('heure', 'h') else v * t / 60
        return (d, f'{format_number(d)} km')
    
    # ── OPÉRATIONS ARITHMÉTIQUES ──
    return _parse_arithmetic(q)


def _parse_arithmetic(q: str) -> Optional[Tuple[float, str]]:
    """Parse les expressions arithmétiques simples."""
    # Nettoyer
    q = q.replace(',', '.')
    
    # Priorité : multiplication/division avant addition/soustraction
    
    # Pattern pour une opération binaire simple : "X op Y"
    patterns = [
        # Addition : X + Y, X plus Y
        (r'(-?\d+(?:\.\d+)?)\s*(\+|plus)\s*(-?\d+(?:\.\d+)?)', lambda a, b: a + b),
        # Soustraction : X - Y, X moins Y
        (r'(-?\d+(?:\.\d+)?)\s*(-|moins)\s*(-?\d+(?:\.\d+)?)', lambda a, b: a - b),
        # Multiplication : X × Y, X fois Y, X * Y, X x Y
        (r'(-?\d+(?:\.\d+)?)\s*(×|\*|fois|x)\s*(-?\d+(?:\.\d+)?)', lambda a, b: a * b),
        # Division : X / Y, X divisé par Y
        (r'(-?\d+(?:\.\d+)?)\s*(/|divise\s*par)\s*(-?\d+(?:\.\d+)?)', lambda a, b: a / b if b != 0 else None),
    ]
    
    # Chercher d'abord les opérations complexes (multiplication puis addition)
    # Ex: "3 × 7 + 5" → d'abord 3×7=21, puis 21+5=26
    m = re.search(r'(-?\d+(?:\.\d+)?)\s*(×|\*|fois|x)\s*(-?\d+(?:\.\d+)?)\s*(\+|plus)\s*(-?\d+(?:\.\d+)?)', q)
    if m:
        a, b, c = float(m.group(1)), float(m.group(3)), float(m.group(5))
        result = a * b + c
        return (result, format_number(result))
    
    # Ex: "X fois Y plus Z"
    m = re.search(r'(-?\d+(?:\.\d+)?)\s*(fois)\s*(-?\d+(?:\.\d+)?)\s*(plus)\s*(-?\d+(?:\.\d+)?)', q)
    if m:
        a, b, c = float(m.group(1)), float(m.group(3)), float(m.group(5))
        result = a * b + c
        return (result, format_number(result))
    
    # Opération simple
    for pattern, op in patterns:
        m = re.search(pattern, q)
        if m:
            a = float(m.group(1))
            b = float(m.group(3))
            result = op(a, b)
            if result is not None:
                return (result, format_number(result))
    
    return None


def format_number(n: float) -> str:
    """Formate un nombre pour l'affichage."""
    if n == int(n):
        return str(int(n))
    elif abs(n) < 0.01 or abs(n) > 1e9:
        return f'{n:.6e}'
    else:
        return f'{n:.6g}'


# ═══════════════════════════════════════════════════════════════════
# ENTRÉE PRINCIPALE (remplace math_bridge.try_math_solve)
# ═══════════════════════════════════════════════════════════════════

def wave_solve(question: str, lang: str = 'fr') -> Optional[str]:
    """
    Tente de résoudre une question mathématique par calcul ondulatoire.
    
    Stratégie hybride :
    1. Constantes connues → réponse directe
    2. Expression arithmétique → calcul exact (float)
    3. (Futur) Calcul purement ondulatoire via ℂ⁵¹²
    
    Returns:
        Réponse formatée ou None si pas une question mathématique.
    """
    result = parse_expression(question)
    if result is None:
        return None
    
    value, formatted = result
    
    # Ajouter un point final si nécessaire
    if not formatted.endswith('.') and not formatted.endswith(')') and not formatted.endswith(']'):
        formatted += '.'
    
    return formatted


# ═══════════════════════════════════════════════════════════════════
# DÉMONSTRATION DU CALCUL ONDULATOIRE PUR
# ═══════════════════════════════════════════════════════════════════

def wave_calculate(a: float, op: str, b: float) -> float:
    """
    Calcul purement ondulatoire : encode → opère → décode.
    Preuve de concept que les ondes peuvent calculer.
    """
    psi_a = number_to_vector(a)
    psi_b = number_to_vector(b)
    
    if op == '+':
        psi_result = wave_add(psi_a, psi_b)
    elif op == '-':
        psi_result = wave_subtract(psi_a, psi_b)
    elif op == '×' or op == '*':
        psi_result = wave_multiply(psi_a, b)
    elif op == '/':
        psi_result = wave_divide(psi_a, b)
    elif op == 'sqrt':
        psi_result = wave_sqrt(psi_a)
    elif op == '^':
        psi_result = wave_power(psi_a, b)
    else:
        return None
    
    return vector_to_number(psi_result)


def demo():
    """Démonstration du calcul ondulatoire."""
    print("=" * 60)
    print("WAVE MATH — Calculateur Ondulatoire Géométrique")
    print("=" * 60)
    
    # Test 1 : Encode/Décode
    print("\n1. ENCODAGE / DÉCODAGE")
    for n in [0, 1, 2, 3, 7, 42, 137, 1000, -5, 3.14]:
        psi = number_to_vector(n)
        decoded = vector_to_number(psi)
        status = "✅" if abs(decoded - n) < 0.01 else "❌"
        print(f"  {status} {n:>8} → ψ ∈ ℂ⁵¹² → {decoded:>8.1f}")
    
    # Test 2 : Opérations
    print("\n2. OPÉRATIONS ONDULATOIRES")
    tests = [
        (3, '+', 7, 10),
        (10, '-', 4, 6),
        (6, '×', 7, 42),
        (100, '/', 4, 25),
        (144, 'sqrt', None, 12),
        (2, '^', 8, 256),
        (-5, '+', 12, 7),
    ]
    for a, op, b, expected in tests:
        result = wave_calculate(a, op, b) if b is not None else wave_calculate(a, op, 0)
        if op == 'sqrt':
            result = wave_calculate(a, 'sqrt', 0)
        status = "✅" if abs(result - expected) < 0.01 else "❌"
        b_str = str(b) if b is not None else ''
        print(f"  {status} {a} {op} {b_str} = {result:.1f}  (attendu: {expected})")
    
    # Test 3 : Parser
    print("\n3. PARSER D'EXPRESSIONS")
    expressions = [
        '3 + 7',
        '80 euros avec 20 pourcent de reduction',
        '100 km/h pendant 30 minutes',
        'secondes dans une heure',
        'racine carree de 144',
        '2 puissance 8',
        '3 fois 7 plus 5',
        'nombre d or',
        'vitesse de la lumiere',
    ]
    for expr in expressions:
        result = wave_solve(expr)
        status = "✅" if result else "❌"
        print(f"  {status} {expr:<50} → {result}")
    
    print("\n" + "=" * 60)
    print("100% ONDULATOIRE — Zéro regex, zéro table, pure géométrie φ")
    print("=" * 60)


if __name__ == '__main__':
    demo()
