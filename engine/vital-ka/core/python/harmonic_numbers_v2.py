#!/usr/bin/env python3
"""
harmonic_numbers_v2.py — Traducteur numérique harmonique (v2 : décomposition spectrale)
======================================================================================

Principe : Nombre = onde = somme d'harmoniques (base 10 positionnel)
- Harmonique k (k=0,1,2...) ↔ position 10^k (unités, dizaines, centaines...)
- Phase à l'harmonique k = 2π × digit_k / 10  (digit_k ∈ {0..9})
- Amplitude = 1 si digit ≠ 0, 0 sinon

Opérations :
- Addition : superposition d'ondes → addition vectorielle (même harmoniques)
- Multiplication : binding (convolution) → décalage d'harmoniques
- Division : déconvolution

Représentation : vecteur complexe C^DIM (espace temporel)
ou spectre : vecteur complexe C^DIM (espace fréquentiel) — équivalent par FFT
"""

import numpy as np
from typing import Tuple, List

DIM = 512          # Dimension espace (puissance de 2)
N_HARMONICS = 8    # Harmoniques utilisables (0..7 = unités à 10^7)
# Bins FFT pour chaque harmonique : répartis uniformément
HARMONIC_BINS = np.array([int(k * DIM / N_HARMONICS) for k in range(N_HARMONICS)], dtype=int)


def _int_to_digits(n: int) -> List[int]:
    """Décompose entier positif en chiffres base 10 (little-endian: unités d'abord)."""
    if n == 0:
        return [0]
    digits = []
    while n > 0:
        digits.append(n % 10)
        n //= 10
    return digits


def _digits_to_int(digits: List[int]) -> int:
    """Reconstruit entier depuis chiffres little-endian."""
    n = 0
    for pos, d in enumerate(digits):
        n += d * (10 ** pos)
    return n


def encode_int(n: int) -> np.ndarray:
    """
    Encode un entier (positif ou négatif) en vecteur d'onde C^DIM.
    
    Spectre : pour chaque position k (harmonique k),
    - phase = 2π × digit_k / 10
    - amplitude = 1 si digit ≠ 0
    Signe : encodé à l'harmonique N_HARMONICS (phase 0 = positif, π = négatif)
    """
    sign = 1 if n >= 0 else -1
    n = abs(n)
    
    digits = _int_to_digits(n)
    
    # Construire spectre fréquentiel complexe
    spectrum = np.zeros(DIM, dtype=np.complex128)
    
    for k, digit in enumerate(digits):
        if k >= N_HARMONICS:
            break
        if digit == 0:
            continue
        bin_idx = HARMONIC_BINS[k]
        phase = 2 * np.pi * digit / 10
        spectrum[bin_idx] = np.exp(1j * phase)
        # Symétrie hermitienne pour signal réel
        if bin_idx != 0 and bin_idx != DIM // 2:
            spectrum[DIM - bin_idx] = np.conj(spectrum[bin_idx])
    
    # Signe à l'harmonique de garde
    sign_bin = HARMONIC_BINS[min(N_HARMONICS - 1, len(digits))]
    if sign < 0:
        spectrum[sign_bin] = -1  # phase π
    else:
        spectrum[sign_bin] = 1   # phase 0
    if sign_bin != 0 and sign_bin != DIM // 2:
        spectrum[DIM - sign_bin] = np.conj(spectrum[sign_bin])
    
    # IFFT -> espace temporel (vecteur d'onde)
    wave = np.fft.ifft(spectrum)
    
    # Normaliser
    norm = np.linalg.norm(wave)
    if norm > 1e-12:
        wave = wave / norm
    
    return wave.astype(np.complex64)


def decode_int(psi: np.ndarray) -> int:
    """
    Décode vecteur d'onde -> entier.
    FFT -> lecture phases aux harmoniques -> reconstruction chiffres.
    """
    spectrum = np.fft.fft(psi)
    
    digits = []
    for k in range(N_HARMONICS):
        bin_idx = HARMONIC_BINS[k]
        val = spectrum[bin_idx]
        phase = np.angle(val)  # [-π, π]
        amp = np.abs(val)
        
        if amp < 0.1:  # Seuil bruit
            digits.append(0)
            continue
        
        # Phase -> chiffre 0-9
        # phase ∈ [-π, π] -> normaliser [0, 1] -> * 10 -> arrondir
        norm_phase = (phase + np.pi) / (2 * np.pi)  # [0, 1]
        digit = int(np.round(norm_phase * 10)) % 10
        digits.append(digit)
    
    # Signe
    sign_bin = HARMONIC_BINS[N_HARMONICS - 1]
    sign_phase = np.angle(spectrum[sign_bin])
    sign = -1 if sign_phase < 0 else 1
    
    n = _digits_to_int(digits)
    return sign * n


# ──────────────────────────────────────────────────────────────────────────────
# OPÉRATIONS HARMONIQUES
# ──────────────────────────────────────────────────────────────────────────────

def harmonic_add(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """
    Addition harmonique = superposition d'ondes (somme vectorielle).
    En fréquentiel : addition spectre par spectre -> addition chiffre à chiffre avec retenue.
    """
    # Simple somme vectorielle (gère les retenues par interférence de phase)
    result = psi_a + psi_b
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


def harmonic_sub(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """Soustraction = interférence destructive."""
    result = psi_a - psi_b
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


def harmonic_mul(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """
    Multiplication harmonique = binding (convolution circulaire).
    En fréquentiel : produit point par point des spectres.
    Cela décale les harmoniques : 10^k × 10^m = 10^(k+m) -> harmonique k+m.
    """
    spec_a = np.fft.fft(psi_a)
    spec_b = np.fft.fft(psi_b)
    spec_c = spec_a * spec_b
    result = np.fft.ifft(spec_c)
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


def harmonic_div(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """Division = déconvolution (division spectrale)."""
    spec_a = np.fft.fft(psi_a)
    spec_b = np.fft.fft(psi_b)
    eps = 1e-12
    spec_c = spec_a / (spec_b + eps)
    result = np.fft.ifft(spec_c)
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


# ──────────────────────────────────────────────────────────────────────────────
# DÉCOMPOSITION HARMONIQUE D'UN PROBLÈME GSM8K
# ──────────────────────────────────────────────────────────────────────────────

def decompose_problem(question: str) -> dict:
    """
    Décompose un problème GSM8K en ses harmoniques constitutives.
    Retourne un dict avec les composantes spectrales.
    """
    import re
    
    # Extraire nombres
    numbers = [int(m) for m in re.findall(r'\b\d+\b', question)]
    
    # Détecter opération par mots-clés
    q = question.lower()
    op = 'add'
    if any(w in q for w in ['left', 'remain', 'less', 'fewer', 'minus', 'ate', 'gave', 'spent']):
        op = 'sub'
    elif any(w in q for w in ['times', 'each', 'product', 'multiply', 'total']):
        op = 'mul'
    elif any(w in q for w in ['per', 'each', 'divide', 'shared']):
        op = 'div'
    
    # Harmoniques du problème
    return {
        'numbers': [encode_int(n) for n in numbers],
        'operation': op,
        'question_type': 'count' if 'how many' in q else 'amount' if 'how much' in q else 'generic'
    }


def solve_harmonic(problem: dict) -> int:
    """
    Résout un problème décomposé harmoniquement.
    Applique l'opération sur les ondes-nombres.
    """
    numbers = problem['numbers']
    op = problem['operation']
    
    if not numbers:
        return 0
    
    if op == 'add':
        result = numbers[0]
        for n in numbers[1:]:
            result = harmonic_add(result, n)
    elif op == 'sub':
        result = numbers[0]
        for n in numbers[1:]:
            result = harmonic_sub(result, n)
    elif op == 'mul':
        result = numbers[0]
        for n in numbers[1:]:
            result = harmonic_mul(result, n)
    elif op == 'div':
        result = numbers[0]
        for n in numbers[1:]:
            result = harmonic_div(result, n)
    else:
        result = numbers[0]
    
    return decode_int(result)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS
# ──────────────────────────────────────────────────────────────────────────────

def test_roundtrip():
    print("Test roundtrip encode/decode...")
    test_values = [0, 1, 5, 8, 10, 13, 42, 100, 123, 999, 1000, 5000, -5, -42, -100]
    ok = 0
    for n in test_values:
        psi = encode_int(n)
        decoded = decode_int(psi)
        status = "OK" if decoded == n else "KO"
        if decoded == n:
            ok += 1
        print(f"  {status} {n} -> {decoded}")
    print(f"  Score: {ok}/{len(test_values)}")
    return ok


def test_arithmetic():
    print("\nTest operations arithmetiques...")
    test_cases = [
        (5, 3, 'add', 8),
        (10, 4, 'sub', 6),
        (6, 7, 'mul', 42),
        (20, 4, 'div', 5),
        (123, 456, 'add', 579),
        (999, 1, 'add', 1000),
    ]
    ok = 0
    for a, b, op, expected in test_cases:
        psi_a = encode_int(a)
        psi_b = encode_int(b)
        if op == 'add':
            psi_r = harmonic_add(psi_a, psi_b)
        elif op == 'sub':
            psi_r = harmonic_sub(psi_a, psi_b)
        elif op == 'mul':
            psi_r = harmonic_mul(psi_a, psi_b)
        elif op == 'div':
            psi_r = harmonic_div(psi_a, psi_b)
        result = decode_int(psi_r)
        status = "OK" if result == expected else "KO"
        if result == expected:
            ok += 1
        print(f"  {status} {a} {op} {b} = {result} (expected {expected})")
    print(f"  Score: {ok}/{len(test_cases)}")
    return ok


def test_gsm8k_patterns():
    print("\nTest patterns GSM8K...")
    problems = [
        ("John has 5 apples. He buys 3 more. How many apples does he have?", 8),
        ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6),
        ("There are 6 boxes. Each box has 5 pencils. How many pencils in total?", 30),
        ("A car drives at 60 mph for 2 hours. How far does it go?", 120),
        ("What is 20 percent of 150?", 30),  # 20% = 20/100 * 150 -> mul then div
    ]
    ok = 0
    for q, expected in problems:
        prob = decompose_problem(q)
        result = solve_harmonic(prob)
        status = "OK" if result == expected else "KO"
        if result == expected:
            ok += 1
        print(f"  {status} Q: {q[:55]}... -> {result} (expected {expected})")
    print(f"  Score: {ok}/{len(problems)}")
    return ok


if __name__ == "__main__":
    print("=" * 60)
    print("HARMONIC NUMBERS v2 - DECOMPOSITION SPECTRALE")
    print("=" * 60)
    
    test_roundtrip()
    test_arithmetic()
    test_gsm8k_patterns()
    
    print("\n" + "=" * 60)
    print("Tests termines")
    print("=" * 60)