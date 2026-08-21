#!/usr/bin/env python3
"""
harmonic_numbers.py — Traducteur numérique harmonique
=====================================================

Encodage des nombres (ℕ, ℚ, ℝ) en vecteurs d'onde ℂ⁵¹²
préservant la structure arithmétique par résonance de phase.

Théorie : 
- Nombre = somme de chiffres × puissances de base φ
- Chaque position = fréquence harmonique (k-ième harmonique)
- Chaque chiffre = phase (0 à 2π selon valeur)
- Addition = superposition de phases (même fréquence)
- Multiplication = binding (convolution circulaire → produit tensoriel)

Base φ (1.618...) pour redondance minimale, unicité représentation.
"""

import numpy as np
from typing import Union, Tuple, List, Optional
import math

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTES HARMONIQUES
# ──────────────────────────────────────────────────────────────────────────────

PHI = (1 + np.sqrt(5)) / 2  # Nombre d'or ≈ 1.618033988749895
PHI_INV = 1 / PHI            # ≈ 0.6180339887498949

DIM = 512                    # Dimension espace harmonique (puissance de 2 pour FFT)
N_HARMONICS = 16             # Nombre d'harmoniques (positions maximales)
PHASES_PER_DIGIT = 10        # 10 phases pour chiffres 0-9 (base 10) ou base φ

# Fréquences de base : harmoniques 1, φ, φ², φ³... (échelle logarithmique)
HARMONIC_FREQS = np.array([PHI ** k for k in range(N_HARMONICS)], dtype=np.float64)
# Normaliser pour éviter overflow
HARMONIC_FREQS = HARMONIC_FREQS / HARMONIC_FREQS.max()

# Phases pour chiffres 0-9 : 0, 2π/10, 4π/10, ... 18π/10
DIGIT_PHASES = np.array([2 * np.pi * d / PHASES_PER_DIGIT for d in range(10)], dtype=np.float64)

# ──────────────────────────────────────────────────────────────────────────────
# ENCODAGE / DÉCODAGE
# ──────────────────────────────────────────────────────────────────────────────

def _number_to_phi_digits(n: float, max_digits: int = N_HARMONICS) -> np.ndarray:
    """
    Convertit un nombre en représentation en base φ (système de numération phi).
    Retourne un vecteur de 'chiffres' (coefficients) pour chaque puissance de φ.
    Algorithme glouton standard pour base φ.
    """
    if n == 0:
        return np.zeros(max_digits, dtype=np.float64)
    
    sign = 1.0 if n >= 0 else -1.0
    n = abs(n)
    
    digits = np.zeros(max_digits, dtype=np.float64)
    remaining = n
    
    # Puissances de φ décroissantes
    for k in reversed(range(max_digits)):
        phi_pow = PHI ** k
        if remaining >= phi_pow * 0.5:  # Seuil pour éviter représentations multiples
            # Combien de fois phi_pow rentre ?
            coeff = int(remaining / phi_pow)
            # Limiter pour base φ (chiffres 0 ou 1 seulement, pas de 2 consécutifs)
            coeff = min(coeff, 1)
            if coeff > 0:
                digits[k] = coeff
                remaining -= coeff * phi_pow
    
    return digits * sign


def _phi_digits_to_number(digits: np.ndarray) -> float:
    """Reconstruit le nombre à partir des coefficients base φ."""
    return np.sum(digits * np.array([PHI ** k for k in range(len(digits))]))


def encode_number(n: float, dim: int = DIM) -> np.ndarray:
    """
    Encode un nombre scalaire en vecteur d'onde harmonique ℂ^dim.
    
    Principe : 
    - Décompose n en base φ → coefficients par harmonique
    - Chaque harmonique k → fréquence f_k = φ^k
    - Phase = 2π × coefficient (0 ou 1 pour base φ standard)
    - Amplitude = coefficient
    - Synthèse : somme d'ondes complexes e^(i × phase_k) à chaque fréquence
    
    Le vecteur résultant est la FFT inverse du spectre harmonique.
    """
    # 1. Décomposition base φ
    coeffs = _number_to_phi_digits(n, N_HARMONICS)
    
    # 2. Construire spectre fréquentiel (seules N_HARMONICS premières bins)
    spectrum = np.zeros(dim, dtype=np.complex128)
    
    for k, coeff in enumerate(coeffs):
        if abs(coeff) > 1e-12:
            # Fréquence harmonique k → bin FFT correspondant
            # Mapper harmonique logarithmique vers bins linéaires FFT
            bin_idx = int(k * dim / N_HARMONICS) % dim
            
            # Phase = 2π × coeff (pour base φ, coeff ∈ {0, 1} → phase 0 ou 2π)
            # Mais on utilise phase proportionnelle pour généraliser
            phase = 2 * np.pi * coeff
            
            # Composante complexe
            spectrum[bin_idx] = coeff * np.exp(1j * phase)
            
            # Symétrie hermitienne pour signal réel (conjugé à -freq)
            if bin_idx != 0 and bin_idx != dim // 2:
                spectrum[dim - bin_idx] = np.conj(spectrum[bin_idx])
    
    # 3. FFT inverse → vecteur d'onde temporel (espace ℂ^dim)
    wave = np.fft.ifft(spectrum)
    
    # Normaliser énergie = 1
    norm = np.linalg.norm(wave)
    if norm > 1e-12:
        wave = wave / norm
    
    return wave.astype(np.complex64)


def decode_number(psi: np.ndarray, dim: int = DIM) -> float:
    """
    Décode un vecteur d'onde harmonique → nombre scalaire.
    
    Méthode : FFT → analyse spectrale aux harmoniques φ^k → lecture phases/amplitudes
    → reconstruction base φ → nombre.
    """
    # 1. FFT pour aller en fréquentiel
    spectrum = np.fft.fft(psi)
    
    # 2. Lire coefficients aux harmoniques φ^k
    coeffs = np.zeros(N_HARMONICS, dtype=np.float64)
    
    for k in range(N_HARMONICS):
        bin_idx = int(k * dim / N_HARMONICS) % dim
        val = spectrum[bin_idx]
        
        # Amplitude = module, Phase = argument
        amp = np.abs(val)
        phase = np.angle(val)
        
        # Pour base φ standard, coeff = amp (0 ou 1)
        # Phase devrait être multiple de 2π
        coeffs[k] = amp
    
    # 3. Reconstruction nombre
    return _phi_digits_to_number(coeffs)


def encode_number_phase(n: float, dim: int = DIM) -> np.ndarray:
    """
    Version alternative : encodage par phase pure (sans amplitude).
    Chaque harmonique porte l'information dans sa phase seulement.
    Meilleure propriété : addition = superposition de phases.
    """
    coeffs = _number_to_phi_digits(n, N_HARMONICS)
    
    spectrum = np.zeros(dim, dtype=np.complex128)
    
    for k, coeff in enumerate(coeffs):
        if abs(coeff) > 1e-12:
            bin_idx = int(k * dim / N_HARMONICS) % dim
            
            # Phase encode le coefficient (0 → 0, 1 → π, etc.)
            # Pour addition par superposition : phase_add = phase_a + phase_b
            phase = coeff * np.pi  # 0 ou π pour base φ
            
            spectrum[bin_idx] = np.exp(1j * phase)
            
            if bin_idx != 0 and bin_idx != dim // 2:
                spectrum[dim - bin_idx] = np.conj(spectrum[bin_idx])
    
    wave = np.fft.ifft(spectrum)
    norm = np.linalg.norm(wave)
    if norm > 1e-12:
        wave = wave / norm
    
    return wave.astype(np.complex64)


def decode_number_phase(psi: np.ndarray, dim: int = DIM) -> float:
    """Décodage pour encodage par phase pure."""
    spectrum = np.fft.fft(psi)
    
    coeffs = np.zeros(N_HARMONICS, dtype=np.float64)
    
    for k in range(N_HARMONICS):
        bin_idx = int(k * dim / N_HARMONICS) % dim
        val = spectrum[bin_idx]
        phase = np.angle(val)
        
        # Phase → coefficient (modulo 2π)
        # phase ∈ [-π, π], normaliser vers [0, 1]
        coeff = (phase + np.pi) / (2 * np.pi)  # 0 → 0.5, π → 1.0
        # Arrondir au plus proche (0 ou 1 pour base φ)
        coeffs[k] = np.round(coeff)
    
    return _phi_digits_to_number(coeffs)


# ──────────────────────────────────────────────────────────────────────────────
# OPÉRATIONS ARITHMÉTIQUES HARMONIQUES
# ──────────────────────────────────────────────────────────────────────────────

def harmonic_add(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """
    Addition harmonique : superposition des ondes (somme vectorielle).
    Propriété : decode(harmonic_add(encode(a), encode(b))) ≈ a + b
    """
    result = psi_a + psi_b
    # Renormaliser
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


def harmonic_sub(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """Soustraction : interférence destructive (psi_a - psi_b)."""
    result = psi_a - psi_b
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


def harmonic_mul(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """
    Multiplication harmonique : binding (convolution circulaire = produit tensoriel en fréquentiel).
    En domaine fréquentiel : spectrum_c = spectrum_a × spectrum_b (produit point par point).
    """
    # FFT
    spec_a = np.fft.fft(psi_a)
    spec_b = np.fft.fft(psi_b)
    
    # Produit point par point (binding)
    spec_c = spec_a * spec_b
    
    # IFFT
    result = np.fft.ifft(spec_c)
    
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


def harmonic_div(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
    """Division : déconvolution (division en fréquentiel)."""
    spec_a = np.fft.fft(psi_a)
    spec_b = np.fft.fft(psi_b)
    
    # Éviter division par zéro
    eps = 1e-12
    spec_c = spec_a / (spec_b + eps)
    
    result = np.fft.ifft(spec_c)
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


def harmonic_pow(psi_a: np.ndarray, exponent: float) -> np.ndarray:
    """Puissance : élévation en fréquentiel."""
    spec_a = np.fft.fft(psi_a)
    spec_c = np.power(spec_a + 1e-12, exponent)
    result = np.fft.ifft(spec_c)
    norm = np.linalg.norm(result)
    if norm > 1e-12:
        result = result / norm
    return result


# ──────────────────────────────────────────────────────────────────────────────
# ENCODAGE ENTIER SIMPLE (BASE 10) — POUR GSM8K
# ──────────────────────────────────────────────────────────────────────────────

def encode_int_simple(n: int, dim: int = DIM) -> np.ndarray:
    """
    Encodage simple pour entiers (base 10, chiffres 0-9).
    Chaque chiffre = phase, position = harmonique.
    Optimisé pour GSM8K (nombres < 10000 typiquement).
    """
    if n == 0:
        return np.zeros(dim, dtype=np.complex64)
    
    sign = 1 if n >= 0 else -1
    n = abs(n)
    
    # Extraire chiffres base 10
    digits = []
    while n > 0:
        digits.append(n % 10)
        n //= 10
    
    spectrum = np.zeros(dim, dtype=np.complex128)
    
    for pos, digit in enumerate(digits):
        if pos >= N_HARMONICS:
            break
        bin_idx = int(pos * dim / N_HARMONICS) % dim
        
        # Phase = 2π × digit / 10
        phase = 2 * np.pi * digit / 10
        
        spectrum[bin_idx] = np.exp(1j * phase)
        if bin_idx != 0 and bin_idx != dim // 2:
            spectrum[dim - bin_idx] = np.conj(spectrum[bin_idx])
    
    # Encoder signe dans harmonique supplémentaire
    sign_bin = int(N_HARMONICS * dim / N_HARMONICS) % dim
    if sign < 0:
        spectrum[sign_bin] = -1  # Phase π
    else:
        spectrum[sign_bin] = 1   # Phase 0
    
    wave = np.fft.ifft(spectrum)
    norm = np.linalg.norm(wave)
    if norm > 1e-12:
        wave = wave / norm
    
    return wave.astype(np.complex64)


def decode_int_simple(psi: np.ndarray, dim: int = DIM) -> int:
    """Décodage entiers base 10."""
    spectrum = np.fft.fft(psi)
    
    digits = []
    for pos in range(N_HARMONICS):
        bin_idx = int(pos * dim / N_HARMONICS) % dim
        val = spectrum[bin_idx]
        phase = np.angle(val)
        
        # Phase → chiffre 0-9
        digit = int(np.round((phase + np.pi) / (2 * np.pi) * 10)) % 10
        digits.append(digit)
    
    # Reconstruire nombre
    n = 0
    for pos, digit in enumerate(digits):
        n += digit * (10 ** pos)
    
    # Signe
    sign_bin = int(N_HARMONICS * dim / N_HARMONICS) % dim
    sign_phase = np.angle(spectrum[sign_bin])
    if sign_phase < 0:  # Phase π = négatif
        n = -n
    
    return n


# ──────────────────────────────────────────────────────────────────────────────
# TESTS & VALIDATION
# ──────────────────────────────────────────────────────────────────────────────

def _test_roundtrip():
    """Test encode -> decode identite."""
    print("Test roundtrip (encode -> decode)...")
    test_values = [0, 1, 2, 3, 5, 8, 10, 13, 21, 34, 55, 89, 100, 144, 233, 377, 610, 987, 1000, 1597]
    
    errors = []
    for n in test_values:
        psi = encode_number(n)
        decoded = decode_number(psi)
        err = abs(decoded - n)
        if err > 0.5:
            errors.append((n, decoded, err))
            print(f"  KO {n} -> {decoded:.2f} (err={err:.2f})")
        else:
            print(f"  OK {n} -> {decoded:.2f}")
    
    print(f"Roundtrip: {len(test_values) - len(errors)}/{len(test_values)} OK")
    return errors


def _test_arithmetic():
    """Test operations arithmetiques harmoniques."""
    print("\nTest operations arithmetiques...")
    
    test_cases = [
        (5, 3, 'add', 8),
        (10, 4, 'sub', 6),
        (6, 7, 'mul', 42),
        (20, 4, 'div', 5),
        (2, 3, 'pow', 8),
    ]
    
    for a, b, op, expected in test_cases:
        psi_a = encode_number(a)
        psi_b = encode_number(b)
        
        if op == 'add':
            psi_r = harmonic_add(psi_a, psi_b)
        elif op == 'sub':
            psi_r = harmonic_sub(psi_a, psi_b)
        elif op == 'mul':
            psi_r = harmonic_mul(psi_a, psi_b)
        elif op == 'div':
            psi_r = harmonic_div(psi_a, psi_b)
        elif op == 'pow':
            psi_r = harmonic_pow(psi_a, b)
        
        result = decode_number(psi_r)
        err = abs(result - expected)
        status = "OK" if err < 1.0 else "KO"
        print(f"  {status} {a} {op} {b} = {result:.2f} (attendu {expected}, err={err:.2f})")


def _test_simple_int():
    """Test encodage entiers simple (base 10)."""
    print("\nTest encodage entiers simple (base 10)...")
    
    test_values = [0, 1, 5, 8, 10, 13, 42, 100, 123, 999, 1000, 5000, -5, -42, -100]
    
    for n in test_values:
        psi = encode_int_simple(n)
        decoded = decode_int_simple(psi)
        err = abs(decoded - n)
        status = "OK" if err == 0 else "KO"
        print(f"  {status} {n} -> {decoded} (err={err})")


def _test_gsm8k_patterns():
    """Test patterns GSM8K typiques."""
    print("\nTest patterns GSM8K...")
    
    # Pattern: "John has 5 apples. He buys 3 more. Total?"
    psi_5 = encode_int_simple(5)
    psi_3 = encode_int_simple(3)
    psi_total = harmonic_add(psi_5, psi_3)
    total = decode_int_simple(psi_total)
    print(f"  5 + 3 = {total} (attendu 8) {'OK' if total == 8 else 'KO'}")
    
    # Pattern: "10 cookies, ate 4. Left?"
    psi_10 = encode_int_simple(10)
    psi_4 = encode_int_simple(4)
    psi_left = harmonic_sub(psi_10, psi_4)
    left = decode_int_simple(psi_left)
    print(f"  10 - 4 = {left} (attendu 6) {'OK' if left == 6 else 'KO'}")
    
    # Pattern: "6 boxes x 5 pencils = ?"
    psi_6 = encode_int_simple(6)
    psi_5 = encode_int_simple(5)
    psi_prod = harmonic_mul(psi_6, psi_5)
    prod = decode_int_simple(psi_prod)
    print(f"  6 x 5 = {prod} (attendu 30) {'OK' if prod == 30 else 'KO'}")
    
    # Pattern: "20 dollars / 4 = ? per item"
    psi_20 = encode_int_simple(20)
    psi_4 = encode_int_simple(4)
    psi_quot = harmonic_div(psi_20, psi_4)
    quot = decode_int_simple(psi_quot)
    print(f"  20 / 4 = {quot} (attendu 5) {'OK' if quot == 5 else 'KO'}")


if __name__ == "__main__":
    print("=" * 60)
    print("HARMONIC NUMBERS - TRADUCTEUR NUMERIQUE HARMONIQUE")
    print("=" * 60)
    
    _test_roundtrip()
    _test_arithmetic()
    _test_simple_int()
    _test_gsm8k_patterns()
    
    print("\n" + "=" * 60)
    print("Tests termines")
    print("=" * 60)