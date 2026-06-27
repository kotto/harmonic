"""
IMPLEMENTATION NUMERIQUE DE L'EQUATION DE HARPER POUR V_H(x)
=============================================================

But: Verifier que les frequences spectrales corrigees
     f_m(E) = m*Omega*k(E)/phi correspondent aux gamma_n de Riemann.

Methode:
1. Construire V_H(x) a partir des H_n et des log(p)
2. Prendre les coefficients de Fourier V_m
3. Construire la matrice de Harper tronquee
4. Diagonaliser pour differentes valeurs de k (Bloch momentum)
5. Extraire la densite d'etats et les oscillations
6. Comparer les frequences d'oscillation avec gamma_n
"""

import math
import numpy as np
from scipy import linalg

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e_val = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)

Hn = [phi, pi, e_val, sqrt2, sqrt3, sqrt5, e_val/pi]
Hn_names = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']

# Known zeta zeros (first 50)
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
]

def primes_upto(n):
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n+1, i):
                sieve[j] = False
    return [i for i in range(2, n+1) if sieve[i]]

print("=" * 75)
print("EQUATION DE HARPER POUR V_H(x) - IMPLEMENTATION NUMERIQUE")
print("=" * 75)

# ================================================================
# 1. CONSTRUCT V_H(x) AND ITS FOURIER COEFFICIENTS
# ================================================================
print("\n" + "=" * 75)
print("1. COEFFICIENTS DE FOURIER DE V_H(x)")
print("=" * 75)

# V_H(x) = sum_{n=1..7} H_n * sum_{p <= P_n} cos(2*pi*log(p)*x/phi)
# where P_n is the n-th prime

primes = primes_upto(500)
print(f"Using primes up to 500 ({len(primes)} primes)")

# The frequencies are: omega_p = 2*pi*log(p)/phi
# But for the Harper equation, we work with the module:
# Omega = {log(p)} (the 2*pi/phi factor scales everything)

# Fourier coefficients V_m for each frequency m*Omega
# Since V_H has terms cos(2*pi*log(p)*x/phi), 
# the frequencies are: +/- log(p) * (2*pi/phi)
# In dimensionless units (setting 2*pi/phi = 1):
#   Omega = {log(p) : p prime}
#   V_{p} = coefficient at frequency log(p)

# Actually, let's build the potential in terms of dimensionless x
# V_H(x) = sum_n H_n * sum_{p <= p_nth} cos(log(p) * x)
# where x is scaled such that the fundamental frequency is 1.

# We'll work with: omega_p = log(p) 
# and cos(omega_p * x) terms

# The Fourier coefficient for frequency omega is the amplitude:
fourier_amplitudes = {}  # frequency -> amplitude
for n_idx, h in enumerate(Hn, 1):
    # P_n is the n-th prime
    if n_idx <= len(primes):
        limit = primes[n_idx - 1]
        for p in primes:
            if p <= limit:
                freq = math.log(p)
                if freq not in fourier_amplitudes:
                    fourier_amplitudes[freq] = 0
                fourier_amplitudes[freq] += h

frequencies = sorted(fourier_amplitudes.keys())
print(f"\nFourier spectrum ({len(frequencies)} distinct frequencies):")
for i, freq in enumerate(frequencies[:15]):
    amp = fourier_amplitudes[freq]
    print(f"  omega_{i+1} = log({int(math.exp(freq))}) = {freq:.6f},  V = {amp:.6f}")

# ================================================================
# 2. BUILD THE HARPER MATRIX
# ================================================================
print("\n" + "=" * 75)
print("2. CONSTRUCTION DE LA MATRICE DE HARPER")
print("=" * 75)

# The Harper equation for a 1D quasi-periodic operator:
# (E - (k + n*omega_0)^2) * c_n = sum_m V_m * c_{n-m}
#
# For multiple frequencies, it's a matrix in Z^d where d = number of frequencies.
# BUT: if the frequencies are log(p) which are Q-linearly independent (Baker),
# this is an INFINITE-dimensional problem.
#
# APPROXIMATION: We truncate to N Fourier modes.
# This is like the "almost-Mathieu" operator but with prime log-frequencies.

# For numerical tractability: use a 1D approximation
# Keep only the N strongest Fourier modes
# and treat them as a 1D quasi-periodic operator with effective frequency.

# SIMPLIFIED MODEL: Since log(p) are incommensurate but ALL are logs of primes,
# we can order them and keep the first N_modes.
# The Harper matrix becomes:
#   H_{i,j} = delta_{i,j} * (k + i*omega_eff)^2 + V_{i-j}
# where omega_eff is an effective fundamental frequency.

N_modes = 50  # number of Fourier modes to keep
num_k_points = 100  # number of Bloch momentum values
k_values = np.linspace(0, 2*pi, num_k_points)

# Use the first N_modes frequencies and amplitudes
freqs_used = frequencies[:N_modes]
amps_used = [fourier_amplitudes[f] for f in freqs_used]

# Effective 1D frequency: geometric mean
# For a multi-frequency operator, we can approximate by a 1D model
# with effective frequency omega_eff = min(log(p)) = log(2)
omega_eff = math.log(2)  # smallest frequency

print(f"Using effective 1D model with omega_eff = log(2) = {omega_eff:.6f}")
print(f"Number of Fourier modes: {N_modes}")
print(f"Number of k-points: {num_k_points}")

# Build Harper matrix for each k
all_eigenvalues = []
print(f"\nDiagonalizing Harper matrix for {num_k_points} k-values...")

for ki, k in enumerate(k_values):
    # Build the Harper matrix H_{i,j} for i,j in [-N_modes//2, N_modes//2]
    # H_{i,j} = delta_{i,j} * (k + i*omega_eff)^2 + V_{i-j}
    
    N = N_modes
    H = np.zeros((N, N), dtype=complex)
    
    idx_to_n = {}  # matrix index -> Fourier index
    n_values = list(range(-N//2, N//2))
    
    for i, ni in enumerate(n_values):
        # Diagonal: kinetic energy
        # Actually for Schrodinger on the line: H = p^2 + V(x)
        # In momentum representation: p -> k + n*omega_eff
        # So kinetic term = (k + n*omega_eff)^2
        H[i, i] = (k + ni * omega_eff)**2
        
        # Off-diagonal: potential coupling
        for j, nj in enumerate(n_values):
            if i != j:
                diff = ni - nj  # this corresponds to frequency index
                # Find the Fourier amplitude for this frequency difference
                # In a true Harper model: V(i-j) is the Fourier coefficient
                # at frequency (i-j)*omega_eff
                
                # Simplified: use the actual Fourier amplitudes
                # Map diff to an effective amplitude
                abs_diff = abs(diff)
                if abs_diff < len(amps_used) and abs_diff > 0:
                    # Use the amplitude at index abs_diff-1
                    H[i, j] = amps_used[min(abs_diff-1, len(amps_used)-1)] / 2.0
                elif abs_diff == 0:
                    pass  # already handled by diagonal
                else:
                    # For larger frequency differences, amplitude decays
                    H[i, j] = amps_used[-1] / (abs_diff * 2.0)
    
    # Diagonalize
    eigenvalues = np.sort(np.real(np.linalg.eigvals(H)))
    all_eigenvalues.append(eigenvalues)

print("Diagonalization complete.")

# ================================================================
# 3. COMPUTE THE DENSITY OF STATES
# ================================================================
print("\n" + "=" * 75)
print("3. DENSITE D'ETATS ET OSCILLATIONS")
print("=" * 75)

# Collect all eigenvalues
all_ev = np.concatenate(all_eigenvalues)
all_ev = np.sort(all_ev)

# Compute integrated density of states N(E)
# N(E) = fraction of eigenvalues <= E (normalized)
E_range = np.linspace(all_ev[0], min(all_ev[-1], 500), 2000)
N_E = np.array([np.sum(all_ev <= E)/len(all_ev) for E in E_range])

# The smooth part: for 1D free particle, N_0(E) = sqrt(E)/pi
# But with quasi-periodic potential, the smooth part is modified
# Let's fit a polynomial to N(E) to extract the oscillating part
poly_coeffs = np.polyfit(E_range, N_E, 5)
N_smooth = np.polyval(poly_coeffs, E_range)
N_osc = N_E - N_smooth

print(f"E range: {all_ev[0]:.4f} to {min(all_ev[-1], 500):.4f}")
print(f"Number of eigenvalues: {len(all_ev)}")

# ================================================================
# 4. FIND OSCILLATION FREQUENCIES IN N_osc(E)
# ================================================================
print("\n" + "=" * 75)
print("4. ANALYSE FREQUENTIELLE DE N_osc(E)")
print("=" * 75)

# Take Fourier transform of N_osc with respect to sqrt(E)
# since the Thouless formula gives oscillations in sqrt(E)
# N_osc ~ sum_m c_m * sin(2*pi * m*Omega * sqrt(E) / phi)

sqrt_E = np.sqrt(np.maximum(E_range, 1e-10))
# Sample uniformly in sqrt(E)
sqrt_E_uniform = np.linspace(sqrt_E[0], sqrt_E[-1], len(E_range))
N_osc_interp = np.interp(sqrt_E_uniform**2, E_range, N_osc)

# Compute Fourier transform
FT = np.fft.rfft(N_osc_interp)
freqs_fft = np.fft.rfftfreq(len(N_osc_interp), sqrt_E_uniform[1] - sqrt_E_uniform[0])
power = np.abs(FT)**2

# Find peaks in the power spectrum
# Expected frequencies (from Thouless): f_m = m*log(p) * sqrt(E)/(2*phi)
# These depend on E, so they're not sharp in the Fourier transform.
# Instead, we look for peaks in the *range* of gamma_n.

print("\nTop 20 frequency peaks in N_osc(E):")
peaks = []
for i in range(1, len(power)-1):
    if power[i] > power[i-1] and power[i] > power[i+1] and power[i] > np.median(power):
        peaks.append((freqs_fft[i], power[i], i))

peaks.sort(key=lambda x: -x[1])
for i, (freq, pow_val, idx) in enumerate(peaks[:20]):
    print(f"  freq = {freq:.6f},  power = {pow_val:.2e}")

# ================================================================
# 5. COMPARE PEAKS WITH ZETA ZEROS
# ================================================================
print("\n" + "=" * 75)
print("5. COMPARAISON AVEC LES ZEROS DE RIEMANN")
print("=" * 75)

# The spectral frequencies in the Thouless formula are:
# f_m(E) = m * log(p) * sqrt(E) / (2*phi)
# For the first few m and p, at typical E ~ 100 (gamma ~ 30-100):
# sqrt(E) ~ 10
# f ~ 1 * log(2) * 10 / (2*1.618) ~ 2.1
# f ~ 1 * log(3) * 10 / (2*1.618) ~ 3.4
# f ~ 1 * log(5) * 10 / (2*1.618) ~ 4.9
# ...
# f ~ 1 * log(prime) * 10 / (2*1.618)

# These are STILL too small compared to gamma_n ~ 14-50.
# The gap-labelling theorem suggests the frequencies should be:
# gamma_n correspond to COMBINATIONS of the fundamental frequencies.
# Specifically: gamma_n = phi * (combination of log(p))

# Let's test: can we express gamma_n as phi * sum c_p * log(p)?

print("Testing: gamma_n = phi * sum_{p} n_p * log(p)")
print("(Gap-Labelling prediction for quasi-periodic operators)\n")

for idx, gn in enumerate(zeta_zeros[:10]):
    best_combo = None
    best_err = float('inf')
    
    # Simple test: gamma_n / phi should be close to integer * log(prime)
    target = gn / phi
    for p_index, p in enumerate(primes[:50]):
        log_p = math.log(p)
        # Check how many times log_p fits into target
        n_int = round(target / log_p)
        if n_int > 0:
            approx = phi * n_int * log_p
            err = abs(approx - gn)
            if err < best_err:
                best_err = err
                best_combo = f"{n_int}*log({p})"
    
    print(f"  gamma_{idx+1} = {gn:.4f}: best = {best_combo} -> phi*{best_combo} = {phi * round(target/math.log(primes[0])) * math.log(primes[0]):.4f} (err={best_err:.2f})")

# Better: gamma_n / (phi * log(p)) should be close to integer
print("\nDetailed: gamma_n / (phi * log(p)) for small primes:")
for gn_idx in range(5):
    gn = zeta_zeros[gn_idx]
    print(f"\n  gamma_{gn_idx+1} = {gn:.4f}:")
    for p in primes[:10]:
        log_p = math.log(p)
        ratio = gn / (phi * log_p)
        nearest_int = round(ratio)
        err = abs(ratio - nearest_int) / ratio * 100
        if err < 10:
            print(f"    / (phi*log({p})) = {ratio:.4f} ~ {nearest_int} (err={err:.2f}%)")

# ================================================================
# 6. DIRECT NUMERICAL COMPARISON VIA LYAPUNOV EXPONENT
# ================================================================
print("\n" + "=" * 75)
print("6. APPROCHE ALTERNATIVE: EXPOSANT DE LYAPUNOV")
print("=" * 75)

# For a quasi-periodic potential, the spectral gaps occur at energies
# where the Lyapunov exponent gamma(E) > 0.
# The integrated density of states N(E) in the gaps takes values
# that are integer combinations of the frequencies Omega = {log(p)}.

# Let's test this gap-labelling prediction numerically.
# We already have N(E) from the diagonalization.
# We need to identify the gaps (regions where the density of states is flat).

# Find gaps: regions where N(E) is constant (to within tolerance)
dN = np.diff(N_E)
gap_threshold = np.median(np.abs(dN[dN != 0])) * 0.1
gaps = []
in_gap = False
gap_start = 0
for i in range(len(dN)):
    if abs(dN[i]) < gap_threshold and not in_gap:
        in_gap = True
        gap_start = i
    elif abs(dN[i]) >= gap_threshold and in_gap:
        in_gap = False
        if i - gap_start > 3:  # at least 3 points wide
            gaps.append((E_range[gap_start], E_range[i], N_E[gap_start]))

print(f"Found {len(gaps)} spectral gaps")
print(f"Gap-labelling test: N(E) in gaps should be integer combinations of log(p)\n")

if len(gaps) > 0:
    print("First few gaps and their N(E) values:")
    for i, (E_start, E_end, N_val) in enumerate(gaps[:10]):
        print(f"  Gap {i+1}: E in [{E_start:.2f}, {E_end:.2f}], N(E) = {N_val:.6f}")
    
    # Check if N(E) in gaps matches integer combos of log(p)
    print("\nTesting gap-labelling: N(E) mod combos of log(p)")
    for i, (E_start, E_end, N_val) in enumerate(gaps[:5]):
        print(f"  Gap {i+1}: N(E) = {N_val:.6f}")
        for p in primes[:15]:
            log_p = math.log(p)
            ratio = N_val / log_p
            nearest = round(ratio)
            if abs(ratio - nearest) < 0.1:
                print(f"    = {nearest} * log({p}) = {nearest*log_p:.6f} (diff={abs(N_val - nearest*log_p):.6f})")
                break

# ================================================================
# 7. CONCLUSIONS
# ================================================================
print("\n" + "=" * 75)
print("7. CONCLUSIONS DE L'IMPLEMENTATION DE HARPER")
print("=" * 75)

print("""
RESULTATS DE L'IMPLEMENTATION:

1. Le potentiel V_H(x) avec frequences log(p) genere un operateur
   quasi-periodique dont le spectre presente une structure de bandes.

2. Les frequences d'oscillation de la densite d'etats (formule de Thouless)
   sont de l'ordre f ~ m*log(p)*sqrt(E)/(2*phi), soit ~2-10 pour E~100.

3. Ces frequences sont ENCORE trop petites par rapport aux gamma_n (~14-200).
   Un facteur ~5-10 persiste meme avec le modele de Harper.

4. L'EXPLICATION: le modele 1D effectif avec omega_eff = log(2) est
   une approximation trop grossiere. Le vrai potentiel a 7*N frequences
   incommensurables, ce qui cree un spectre de type "Cantor" dont la
   structure fine est determinee par TOUTES les combinaisons lineaires.

5. PROCHAINE ETAPE NECESSAIRE: implementer un modele 2D ou 3D de Harper
   (comme le papillon de Hofstadter generalise) avec les 7 couches H_n
   comme amplitudes pour les frequences log(p). C'est un probleme
   numeriquement lourd mais conceptuellement clair.

6. LA PISTE LA PLUS PROMETTEUSE: le gap-labelling (theoreme de 
   Johnson-Moser) predit que N(E) dans les gaps vaut des combinaisons
   lineaires entieres de log(p). Si les gamma_n correspondent aux BORDS
   des gaps, alors ils sont determines par ces combinaisons.
""")