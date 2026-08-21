#!/usr/bin/env python3
"""
harmonic_numbers_v3.py — Traducteur numérique harmonique (v3 : phase-pure, pas de normalisation)
================================================================================================

Principes corrigés :
1. Bins FFT : éviter 0 (DC) et DIM/2 (Nyquist), utiliser range(1, DIM//2)
2. Une harmonique par position décimale -> bin dédié
3. Pas de normalisation finale (garder amplitudes relatives = info chiffre != 0)
3. Phase = information, Amplitude = présence (1.0 si digit != 0)
4. Signe = harmonique dédiée (la plus haute)
5. Retenues (carry) : gérées naturellement par interférence de phase
"""

import numpy as np
from typing import List

DIM = 512                    # Puissance de 2
N_POSITIONS = 8              # Positions décimales max (unités à 10^7)
SIGN_POS = N_POSITIONS       # Position du signe

# Bins FFT : 1 harmonique = 2 bins (positif + négatif pour signal réel)
# Utiliser bins 1..N_POSITIONS*2 pour les chiffres, bin dédié pour signe
# Bin k correspond à fréquence k/DIM
DIGIT_BINS = np.array([1 + k * 2 for k in range(N_POSITIONS)], dtype=int)  # 1, 3, 5, 7, 9, 11, 13, 15
SIGN_BIN = 1 + N_POSITIONS * 2 + 1  # Bin suivant disponible (17)

assert SIGN_BIN < DIM // 2, "Pas assez de bins"


def _int_to_digits(n: int) -> List[int]:
    """Décompose entier positif en chiffres base 10 (little-endian)."""
    if n == 0:
        return [0]
    digits = []
    while n > 0:
        digits.append(n % 10)
        n //= 10
    return digits


def _digits_to_int(digits: List[int]) -> int:
    n = 0
    for pos, d in enumerate(digits):
        n += d * (10 ** pos)
    return n


def encode_int(n: int) -> np.ndarray:
    """
    Encode entier -> vecteur d'onde C^DIM (espace temporel).
    
    Spectre fréquentiel (côté positif seulement, 0..DIM//2) :
    - Pour chaque position k (0=unités, 1=dizaines...):
        bin = DIGIT_BINS[k]
        phase = 2π * digit / 10
        amplitude = 1.0 si digit != 0 else 0.0
    - Signe : bin SIGN_BIN, phase 0 (positif) ou π (négatif), amplitude 1.0
    
    Côté négatif : conjugué symétrique pour signal réel.
    """
    sign = 1 if n >= 0 else -1
    n = abs(n)
    
    digits = _int_to_digits(n)
    
    # Spectre COMPLET (0..DIM-1), initialisé à 0
    spectrum = np.zeros(DIM, dtype=np.complex128)
    
    # Chiffres
    for k, digit in enumerate(digits):
        if k >= N_POSITIONS:
            break
        if digit == 0:
            continue
        bin_pos = DIGIT_BINS[k]
        phase = 2 * np.pi * digit / 10
        spectrum[bin_pos] = np.exp(1j * phase)  # amplitude = 1
        # Conjugué symétrique
        spectrum[DIM - bin_pos] = np.exp(-1j * phase)
    
    # Signe
    if sign < 0:
        spectrum[SIGN_BIN] = -1  # phase π
        spectrum[DIM - SIGN_BIN] = -1
    else:
        spectrum[SIGN_BIN] = 1   # phase 0
        spectrum[DIM - SIGN_BIN] = 1
    
    # IFFT -> espace temporel
    # PAS DE NORMALISATION : amplitudes relatives portent l'info
    wave = np.fft.ifft(spectrum)
    
    return wave.astype(np.complex64)


def decode_int(psi: np.ndarray) -> int:
    """
    Décode vecteur d'onde -> entier.
    FFT -> lecture phases aux bins dédiés.
    """
    spectrum = np.fft.fft(psi)
    
    digits = []
    for k in range(N_POSITIONS):
        bin_pos = DIGIT_BINS[k]
        val = spectrum[bin_pos]
        phase = np.angle(val)
        amp = np.abs(val)
        
        if amp < 0.5:  # Seuil : pas de chiffre
            digits.append(0)
            continue
        
        # Phase -> chiffre 0-9
        # phase ∈ [-π, π] -> [0, 1) -> * 10
        norm_phase = (phase + np.pi) / (2 * np.pi)
        digit = int(np.round(norm_phase * 10)) % 10
        digits.append(digit)
    
    # Signe
    sign_val = spectrum[SIGN_BIN]
    sign_phase = np.angle(sign_val)
    sign = -1 if sign_phase < 0 else 1
    
    n = _digits_to_int(digits)
    return sign * n


# ──────────────────────────────────────────────────────────────────────────────
# OPÉRATIONS HARMONIQUES (ESPECTRE)
# ──────────────────────────────────────────────────────────────────────────────

def _to_spectrum(psi: np.ndarray) -> np.ndarray:
    """Retourne spectre côté positif seulement (bins 0..DIM//2)."""
    return np.fft.fft(psi)[:DIM//2 + 1]


def _from_spectrum(spec_half: np.ndarray) -> np.ndarray:
    """Reconstruit onde complète depuis demi-spectre (symétrie hermitienne)."""
    spec_full = np.zeros(DIM, dtype=np.complex128)
    spec_full[:DIM//2 + 1] = spec_half
    # Côté négatif = conjugué inversé (sans DC et Nyquist)
    spec_full[DIM//2 + 1:] = np.conj(spec_half[-2:0:-1])
    return np.fft.ifft(spec_full).astype(np.complex64)


def harmonic_add(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """
    Addition harmonique = superposition en domaine spectral.
    Addition chiffre à chiffre avec retenue gérée par phase.
    """
    spec_a = _to_spectrum(psi_a)
    spec_b = _to_spectrum(psi_b)
    spec_c = spec_a + spec_b
    return _from_spectrum(spec_c)


def harmonic_sub(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """Soustraction = ajout de l'opposé (phase + π)."""
    spec_a = _to_spectrum(psi_a)
    spec_b = _to_spectrum(psi_b)
    spec_c = spec_a - spec_b
    return _from_spectrum(spec_c)


def harmonic_mul(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """
    Multiplication = binding (convolution) = produit spectral.
    Décale harmoniques : position k + position m = position k+m.
    """
    spec_a = _to_spectrum(psi_a)
    spec_b = _to_spectrum(psi_b)
    spec_c = spec_a * spec_b
    return _from_spectrum(spec_c)


def harmonic_div(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """Division = déconvolution."""
    spec_a = _to_spectrum(psi_a)
    spec_b = _to_spectrum(psi_b)
    eps = 1e-12
    spec_c = spec_a / (spec_b + eps)
    return _from_spectrum(spec_c)


# ──────────────────────────────────────────────────────────────────────────────
# DÉCOMPOSITION PROBLÈME GSM8K
# ──────────────────────────────────────────────────────────────────────────────

def decompose_gsm8k(question: str) -> dict:
    """Extrait nombres et opération d'une question GSM8K."""
    import re
    numbers = [int(m) for m in re.findall(r'\b\d+\b', question)]
    q = question.lower()
    op = 'add'
    if any(w in q for w in ['left', 'remain', 'less', 'fewer', 'minus', 'ate', 'gave', 'spent']):
        op = 'sub'
    elif any(w in q for w in ['times', 'each', 'product', 'multiply', 'total', 'area']):
        op = 'mul'
    elif any(w in q for w in ['per', 'each', 'divide', 'shared', 'percent', '%']):
        op = 'div'
    return {
        'numbers': [encode_int(n) for n in numbers],
        'operation': op,
        'raw_numbers': numbers,
        'question': question
    }


def solve_harmonic(problem: dict) -> int:
    """Résout problème décomposé par opérations harmoniques."""
    numbers = problem['numbers']
    op = problem['operation']
    
    if not numbers:
        return 0
    
    result = numbers[0]
    for n in numbers[1:]:
        if op == 'add':
            result = harmonic_add(result, n)
        elif op == 'sub':
            result = harmonic_sub(result, n)
        elif op == 'mul':
            result = harmonic_mul(result, n)
        elif op == 'div':
            result = harmonic_div(result, n)
    
    return decode_int(result)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS
# ──────────────────────────────────────────────────────────────────────────────

def test_roundtrip():
    print("Test roundtrip encode/decode...")
    test_values = [0, 1, 5, 8, 10, 13, 42, 100, 123, 999, 1000, 5000, -5, -42, -100, -999]
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
        (12, 12, 'mul', 144),
        (100, 25, 'div', 4),
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


def test_gsm8k():
    print("\nTest patterns GSM8K...")
    problems = [
        ("John has 5 apples. He buys 3 more. How many apples does he have?", 8),
        ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6),
        ("There are 6 boxes. Each box has 5 pencils. How many pencils in total?", 30),
        ("A car drives at 60 mph for 2 hours. How far does it go?", 120),
    ]
    ok = 0
    for q, expected in problems:
        prob = decompose_gsm8k(q)
        result = solve_harmonic(prob)
        status = "OK" if result == expected else "KO"
        if result == expected:
            ok += 1
        print(f"  {status} {q[:55]}... -> {result} (expected {expected})")
    print(f"  Score: {ok}/{len(problems)}")
    return ok


if __name__ == "__main__":
    print("=" * 60)
    print("HARMONIC NUMBERS v3 - PHASE PURE, NO NORMALIZATION")
    print("=" * 60)
    
    test_roundtrip()
    test_arithmetic()
    test_gsm8k()
    
    print("\n" + "=" * 60)
    print("Tests termines")
    print("=" * 60)