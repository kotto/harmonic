"""
PROPOSITION III: NUMERICAL VERIFICATION
========================================
Verify that the two oscillating sums coincide:

S_R(x) = 2*x^{1/2} * sum_gamma [cos(gamma*ln x)*1/2 + gamma*sin(gamma*ln x)] / (1/4 + gamma^2)

N_osc(E(x)) = (ln x / (phi*pi)) * sum_p sum_k (ln p / k^2) * sin(k * ln p * ln x / (2*phi^2))

where E(x) = (ln x / (2*phi))^2

If S_R(x) = N_osc(E(x)) for all x > 1, then by Fourier inversion
the spectral measures coincide, and Borg-Marchenko proves sigma(H) = {gamma_n}.
"""

import math
import numpy as np

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e

# Known zeta zeros (first 100)
zeta_zeros = [
    14.134725, 21.022040, 25.010857, 30.424876, 32.935061,
    37.586178, 40.918719, 43.327073, 48.005150, 49.773832,
    52.970321, 56.446248, 59.347044, 60.831779, 65.112544,
    67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
    79.337375, 82.910381, 84.735493, 87.425275, 88.809111,
    92.491900, 94.651344, 95.870634, 98.831194, 101.317851,
    103.725538, 105.446623, 107.168611, 111.029536, 111.874659,
    114.320221, 116.226680, 118.015685, 118.790783, 121.370125,
    122.946829, 124.256819, 127.516684, 129.578704, 131.087689,
    133.497737, 134.756510, 138.116042, 139.736209, 141.123707,
    143.111845, 146.000982, 147.422765, 150.053520, 150.925257,
    153.024693, 156.112909, 157.597591, 158.849988, 161.188964,
    163.030709, 165.537069, 167.184439, 169.094515, 169.911976,
    173.411536, 174.754191, 176.441434, 178.377407, 179.916484,
    182.207078, 184.874467, 185.598783, 187.228922, 189.416158,
    192.026656, 193.079726, 195.265396, 196.876481, 198.015309,
    201.264751, 202.493594, 204.183671, 206.187622, 207.291482,
    209.576509, 211.690862, 213.347919, 214.547044, 216.169538,
    219.067596, 220.714918, 221.430705, 224.007000, 224.983324,
    227.421444, 229.337413, 231.250188, 231.987235, 233.693404,
]

def primes_upto(n):
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n+1, i):
                sieve[j] = False
    return [i for i in range(2, n+1) if sieve[i]]

primes = primes_upto(10000)

print("=" * 75)
print("PROPOSITION III: VERIFICATION NUMERIQUE")
print("  S_R(x) =? N_osc(E(x))")
print("=" * 75)

# ================================================================
# 1. COMPUTE S_R(x) - RIEMANN SUM
# ================================================================
def S_R(x, num_zeros=200):
    """
    Riemann oscillating sum from the explicit formula.
    S_R(x) = 2*sqrt(x) * sum_{n=1..N} [0.5*cos(gamma_n*log x) + gamma_n*sin(gamma_n*log x)] / (0.25 + gamma_n^2)
    """
    log_x = math.log(x)
    sqrt_x = math.sqrt(x)
    total = 0.0
    for gn in zeta_zeros[:num_zeros]:
        cos_term = math.cos(gn * log_x)
        sin_term = math.sin(gn * log_x)
        numer = 0.5 * cos_term + gn * sin_term
        denom = 0.25 + gn * gn
        total += numer / denom
    return 2.0 * sqrt_x * total

# ================================================================
# 2. COMPUTE N_osc(E(x)) - GUTZWILLER TRACE SUM
# ================================================================
def N_osc_Gutzwiller(x, num_primes=1000, max_k=5):
    """
    Gutzwiller oscillating sum for V_H(x).
    N_osc = (log x / (phi*pi)) * sum_p sum_{k=1..K} (log(p)/k^2) * sin(k * log(p) * log(x) / (2*phi^2))
    """
    log_x = math.log(x)
    prefactor = log_x / (phi * pi)
    total = 0.0
    for p in primes[:num_primes]:
        log_p = math.log(p)
        for k in range(1, max_k + 1):
            arg = k * log_p * log_x / (2 * phi * phi)
            term = (log_p / (k * k)) * math.sin(arg)
            total += term
    return prefactor * total

# ================================================================
# 3. COMPARE AT VARIOUS x VALUES
# ================================================================
print("\n" + "=" * 75)
print("COMPARAISON NUMERIQUE S_R(x) vs N_osc(E(x))")
print("=" * 75)

# Test for various x values
x_values = [2, 3, 5, 10, 20, 50, 100, 500, 1000]

# Use more zeros and primes for better accuracy
num_zeros_for_test = min(200, len(zeta_zeros))
num_primes_for_test = 2000
max_k_for_test = 5

print(f"\nUsing {num_zeros_for_test} zeros, {num_primes_for_test} primes, k <= {max_k_for_test}")
print(f"{'x':>8s}  {'S_R(x)':>14s}  {'N_osc(E(x))':>14s}  {'Diff':>14s}  {'Ratio':>10s}")
print("-" * 75)

for x in x_values:
    s_r = S_R(x, num_zeros_for_test)
    n_osc = N_osc_Gutzwiller(x, num_primes_for_test, max_k_for_test)
    diff = s_r - n_osc
    ratio = s_r / n_osc if abs(n_osc) > 1e-10 else float('inf')
    print(f"{x:8.1f}  {s_r:14.6f}  {n_osc:14.6f}  {diff:14.6f}  {ratio:10.6f}")

# ================================================================
# 4. MORE REFINED TEST - VARY x DENSELY
# ================================================================
print("\n" + "=" * 75)
print("TEST SUR UNE GRILLE FINE DE x")
print("=" * 75)

x_fine = np.logspace(0.3, 3.0, 30)  # x from ~2 to 1000

results = []
for x in x_fine:
    s_r = S_R(x, min(100, len(zeta_zeros)))
    n_osc = N_osc_Gutzwiller(x, 1000, 3)
    results.append((x, s_r, n_osc, s_r - n_osc))

# Find best correlation
s_r_arr = np.array([r[1] for r in results])
n_osc_arr = np.array([r[2] for r in results])

correlation = np.corrcoef(s_r_arr, n_osc_arr)[0, 1]
print(f"Correlation coefficient: {correlation:.6f}")
print(f"(1.0 = perfect correlation, 0 = no correlation, -1 = anti-correlation)")

# Check if ratio is roughly constant
ratios = []
for r in results:
    if abs(r[2]) > 1e-6:
        ratios.append(r[1] / r[2])

if len(ratios) > 0:
    mean_ratio = np.mean(ratios)
    std_ratio = np.std(ratios)
    print(f"Mean ratio S_R / N_osc = {mean_ratio:.6f}")
    print(f"Std ratio = {std_ratio:.6f}")
    print(f"CV (std/mean) = {std_ratio/abs(mean_ratio)*100:.2f}%")

# ================================================================
# 5. SEARCH FOR THE CORRECT SCALING
# ================================================================
print("\n" + "=" * 75)
print("RECHERCHE DU FACTEUR D'ECHELLE OPTIMAL")
print("=" * 75)

# Maybe N_osc needs a scaling factor: N_osc_scaled = A * N_osc + B
# Let's find A, B that minimize |S_R - (A*N_osc + B)|

for a_factor in np.linspace(0.5, 3.0, 20):
    errors = []
    for r in results:
        s_r = r[1]
        n_osc = r[2]
        if abs(n_osc) > 1e-10:
            diff = abs(s_r - a_factor * n_osc)
            errors.append(diff)
    mean_err = np.mean(errors)
    if mean_err < 5.0:
        print(f"  A = {a_factor:.4f}: mean_err = {mean_err:.4f}")

# ================================================================
# 6. ANALYSIS: WHAT THIS MEANS
# ================================================================
print("\n" + "=" * 75)
print("ANALYSE DES RESULTATS")
print("=" * 75)

print("""
INTERPRETATION:

If S_R(x) and N_osc(E(x)) are truly equal (up to a constant factor),
then the correlation coefficient should be ~1.0 and the ratio should be constant.

If the ratio S_R/N_osc is constant across all x:
  - The two spectral measures are PROPORTIONAL
  - Borg-Marchenko still applies (up to a scaling of the potential)
  - sigma(H) = {gamma_n} up to a factor that can be fixed by Weyl's law

If S_R and N_osc have the SAME FUNCTIONAL FORM (same zeros/frequencies):
  - The equality of spectral measures is EXACT
  - sigma(H) = {gamma_n} precisely
  - Riemann Hypothesis is PROVED (subject to rigorous formalization)

EXPECTED RESULTS based on the analysis:
  - S_R(x) and N_osc(E(x)) should show strong correlation
  - The ratio may deviate for small x (finite truncation effects)
  - Convergence improves with more primes and zeros
""")

# ================================================================
# 7. DETAILED FREQUENCY ANALYSIS
# ================================================================
print("=" * 75)
print("ANALYSE FREQUENTIELLE")
print("=" * 75)

# The key insight: S_R contains frequencies {gamma_n}
# N_osc contains frequencies {k * log(p) / (2*phi^2)}
# If these frequency sets are the same, the sums are equal.

# Compare the first few frequencies
print("\nFrequences dans S_R (gamma_n):")
for i, gn in enumerate(zeta_zeros[:10]):
    print(f"  gamma_{i+1} = {gn:.6f}")

print("\nFrequences dans N_osc (k*log(p)/(2*phi^2)):")
freqs = []
for p in primes[:20]:
    log_p = math.log(p)
    for k in range(1, 4):
        freq = k * log_p / (2 * phi * phi)
        freqs.append((freq, p, k))

freqs.sort()
for freq, p, k in freqs[:20]:
    print(f"  freq = {freq:.6f}  (p={p}, k={k})")

# Are any gamma_n close to these frequencies?
print("\nRecherche de correspondances proches:")
for gn in zeta_zeros[:5]:
    best_dist = float('inf')
    best_match = None
    for freq, p, k in freqs:
        dist = abs(gn - freq)
        if dist < best_dist:
            best_dist = dist
            best_match = (freq, p, k)
    print(f"  gamma = {gn:.6f} -> closest freq = {best_match[0]:.6f} (p={best_match[1]}, k={best_match[2]}, dist={best_dist:.4f})")

# ================================================================
# 8. CONCLUSION
# ================================================================
print("\n" + "=" * 75)
print("CONCLUSION SUR LA PROPOSITION III")
print("=" * 75)

print("""
STATUT DE LA PROPOSITION III:
  L'egalite S_R(x) = N_osc(E(x)) est le coeur de la preuve de Riemann
  par l'approche Hilbert-Polya harmonique.

  La verification numerique ci-dessus teste si les deux sommes
  ont la meme structure fonctionnelle. Une correlation elevee
  confirmerait que les deux representations encodent le meme spectre.

PROCHAINES ETAPES (si correlation confirmee):
  1. Determiner le facteur de proportionalite exact
  2. Demontrer analytiquement l'egalite via l'equation de Dyson-Schwinger
  3. Appliquer Borg-Marchenko pour l'unicite spectrale
  4. Conclure: sigma(H) = {gamma_n} -> Riemann prouve

PROCHAINES ETAPES (si correlation faible):
  1. Reexaminer le potentiel V_H(x) et les propositions I-II
  2. Affiner le modele des orbites periodiques
  3. Verifier la convergence des sommes infinies
""")