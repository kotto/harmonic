"""
golden_entropy.py — L'ENTROPIE DORÉE (piste 5) : le codeur arithmétique
======================================================================
La distribution dorée pₙ = (1−1/φ)·(1/φ)ⁿ — la géométrique dont la
MOYENNE EST φ (E3 — la statistique thermique dorée, vérifiée 1,1×10⁻¹⁶).
Elle code les symboles de la compression (les longueurs de courses des
coefficients gardés/éliminés, les amplitudes delta-encodées).

Codeur arithmétique à précision fixe (range coder) avec la CDF dorée :
  F(n) = 1 − (1/φ)^{n+1}  (la somme des probabilités 0..n)

Usage :
  blob = golden_encode(symbols, max_symbol)   # → octets
  symbols = golden_decode(blob, count, max_symbol)
"""

import math

import numpy as np

PHI = (1 + np.sqrt(5)) / 2
Q = 1 / PHI                 # la raison de la distribution dorée
PREC = 32                   # précision fixe du range coder (2^32)
MAX_SYMBOL_SAFE = 46        # Q^n > 2^-32 ⟺ n ≤ 46 — la queue sous la
                            # précision serait un incrément nul (blocage)


def golden_cdf(max_symbol: int) -> np.ndarray:
    """La CDF dorée normalisée : F(n) = 1 − (1/φ)^{n+1}, sur 0..max_symbol."""
    n = np.arange(max_symbol + 1)
    cdf = 1.0 - Q ** (n + 1)
    cdf /= cdf[-1]
    return cdf


def golden_encode(symbols, max_symbol: int) -> bytes:
    """Code une séquence de symboles 0..max_symbol avec la distribution dorée."""
    cdf = golden_cdf(max_symbol)
    total = 1 << PREC
    lo, hi = 0, total
    out = bytearray()
    pending = 0
    for s in symbols:
        r = hi - lo
        lo_new = lo + int(r * (cdf[s - 1] if s > 0 else 0.0))
        hi_new = lo + int(r * cdf[s])
        if hi_new - lo_new <= 0 or hi_new - lo_new == r:
            # garde anti-blocage : un incrément nul (queue sous précision)
            # forcerait une boucle infinie — on force un pas minimal
            lo_new = lo + 1
            hi_new = lo + 2
        lo, hi = lo_new, hi_new
        # renormalisation E1/E2 (range coder standard)
        while True:
            if hi <= total // 2:
                out.append(0); lo *= 2; hi *= 2
            elif lo >= total // 2:
                out.append(1); lo = 2 * (lo - total // 2); hi = 2 * (hi - total // 2)
            elif lo >= total // 4 and hi <= 3 * total // 4:
                pending += 1
                lo = 2 * (lo - total // 4)
                hi = 2 * (hi - total // 4)
            else:
                break
        if hi <= total // 2 or lo >= total // 2:
            while pending:
                out.append(1 if out[-1] == 0 else 0)
                pending -= 1
            pending = 0
    # finalisation
    out.append(1 if lo < total // 2 else 0)
    for _ in range(3):
        out.append(0)
    while pending:
        out.append(1 if out[-1] == 0 else 0)
        pending -= 1
    return bytes(out)


def golden_decode(data: bytes, count: int, max_symbol: int) -> list:
    """Décode `count` symboles depuis les octets (le miroir de l'encodeur)."""
    cdf = golden_cdf(max_symbol)
    total = 1 << PREC
    bits = np.unpackbits(np.frombuffer(data, np.uint8))
    pos = 0

    def next_bit():
        nonlocal pos
        b = int(bits[pos]) if pos < len(bits) else 0
        pos += 1
        return b

    lo, hi = 0, total
    val = 0
    for _ in range(PREC):
        val = (val << 1) | next_bit()
    out = []
    for _ in range(count):
        r = hi - lo
        target = int((val - lo) / r * total)
        # trouver le symbole par la CDF
        s = 0
        while s < max_symbol and target >= int(cdf[s] * total):
            s += 1
        out.append(s)
        lo_new = lo + int(r * (cdf[s - 1] if s > 0 else 0.0))
        hi_new = lo + int(r * cdf[s])
        if hi_new - lo_new <= 0 or hi_new - lo_new == r:
            lo_new = lo + 1
            hi_new = lo + 2
        lo, hi = lo_new, hi_new
        while True:
            if hi <= total // 2:
                lo *= 2; hi *= 2; val = (val << 1) | next_bit()
            elif lo >= total // 2:
                lo = 2 * (lo - total // 2); hi = 2 * (hi - total // 2)
                val = 2 * (val - total // 2) | next_bit()
            elif lo >= total // 4 and hi <= 3 * total // 4:
                lo = 2 * (lo - total // 4); hi = 2 * (hi - total // 4)
                val = val - total // 4
                val = 2 * val | next_bit()
            else:
                break
    return out


def mask_run_lengths(mask: np.ndarray) -> list:
    """Les courses de la sélection (1 = gardé, 0 = éliminé) — les symboles
    de l'entropie dorée : les runs de 0 et de 1 alternés."""
    runs = []
    cur = mask[0]
    length = 1
    for b in mask[1:]:
        if b == cur:
            length += 1
        else:
            runs.append(length)
            cur = b
            length = 1
    runs.append(length)
    return runs
