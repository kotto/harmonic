#!/usr/bin/env python3
"""
ÉMERGENCE NON-EUCLIDIENNE — π sur sphère, φ sur spirale logarithmique
========================================================================
Projette l'hologramme 1024×1024 sur un support non-euclidien pour
révéler π (via projection polaire/sphérique) et φ (via spirale logarithmique).

Tests:
  A. Projection polaire → Détection de cercles concentriques → π
  B. Projection sur spirale logarithmique → Bandes de résonance → φ
  C. Coordonnées hyperboliques → e
"""

import os, sys, math, json, time
import numpy as np

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, '.')

SIZE = 1024
DATA_DIR = os.path.join('..', 'data', 'emergence')
HOLOGRAM_FILE = os.path.join(DATA_DIR, 'emergence_hologram_1024.npy')
RESULTS_FILE = os.path.join(DATA_DIR, 'non_euclidean_emergence.json')
os.makedirs(DATA_DIR, exist_ok=True)

print("=" * 65)
print("  EMERGENCE NON-EUCLIDIENNE - pi, phi, e")
print("  Hologramme 1024x1024")
print("=" * 65)

h = np.load(HOLOGRAM_FILE)
amplitude = np.abs(h)
print(f"\n[OK] Hologramme charge: {h.shape}")
print(f"  Amplitude max: {np.max(amplitude):.4f} | moyenne: {np.mean(amplitude):.6f}")

discoveries = []

# ════════════════════════════════════════════════════════════════════════
# A. PROJECTION POLAIRE → π
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'─'*50}")
print(f"[A] PROJECTION POLAIRE 2D -> Detection de pi")

# Convertir l'hologramme en coordonnées polaires
# r ∈ [0, SIZE/2], θ ∈ [0, 2π]
N_R = 512
N_THETA = 720  # 0.5° résolution angulaire
polar = np.zeros((N_R, N_THETA))
counts_polar = np.zeros((N_R, N_THETA))

cx, cy = SIZE // 2, SIZE // 2
for i in range(SIZE):
    for j in range(SIZE):
        dx = j - cx
        dy = i - cy
        r = math.sqrt(dx*dx + dy*dy)
        if r < N_R:
            theta = math.atan2(dy, dx)
            if theta < 0:
                theta += 2 * math.pi
            ri = int(r)
            ti = int(theta / (2 * math.pi) * N_THETA) % N_THETA
            polar[ri, ti] += amplitude[i, j]
            counts_polar[ri, ti] += 1

polar = np.divide(polar, np.maximum(counts_polar, 1))

# Détection de maxima radiaux
radial_profile = np.mean(polar, axis=1)
radial_peaks = []
for i in range(5, len(radial_profile)-5):
    if radial_profile[i] > radial_profile[i-1] and radial_profile[i] > radial_profile[i+1]:
        if radial_profile[i] > np.mean(radial_profile):
            radial_peaks.append(i)

print(f"  {len(radial_peaks)} pics radiaux detectes")

if len(radial_peaks) >= 2:
    # Le ratio des rayons des pics → si ≈ π/2 ou 2/π, π est implicite
    r1 = radial_peaks[0]
    r2 = radial_peaks[1]
    ratio_r = r2 / r1 if r1 > 0 else 0
    expected = math.pi / 2  # L'espacement théorique pour ondes sphériques
    error = abs(ratio_r - expected) / expected * 100
    print(f"  Pics: r1={r1}, r2={r2} | ratio={ratio_r:.4f} | attendu(pi/2)={expected:.4f}")
    print(f"  Erreur vs pi/2: {error:.2f}%")

    if error < 20:
        discoveries.append({"constant": "pi", "method": "polar_projection",
                          "ratio_r2_r1": round(ratio_r, 4), "error_pct": round(error, 2)})
        print(f"  [EMERGENT] pi dans la projection polaire de l'hologramme !")

    # Chercher π directement : rn+1 - rn devrait être constant
    diffs = [radial_peaks[i+1] - radial_peaks[i] for i in range(min(5, len(radial_peaks)-1))]
    if len(diffs) >= 2:
        avg_diff = sum(diffs) / len(diffs)
        # Si avg_diff ≈ π * rayon_moyen / quelquechose
        # Plus simplement : le nombre d'anneaux dans un rayon R devrait être ≈ R/π si lié à π
        rings_in_500 = sum(1 for p in radial_peaks if p < 500)
        expected_rings = 500 / math.pi
        error_rings = abs(rings_in_500 - expected_rings) / expected_rings * 100
        print(f"  Anneaux dans r<500: {rings_in_500} | attendu (500/pi): {expected_rings:.1f}")
        print(f"  Erreur: {error_rings:.1f}%")
        if error_rings < 20:
            discoveries.append({"constant": "pi", "method": "ring_count",
                              "rings": rings_in_500, "error_pct": round(error_rings, 2)})
            print(f"  [EMERGENT] pi via le nombre d'anneaux concentriques !")

# ════════════════════════════════════════════════════════════════════════
# B. SPIRALE LOGARITHMIQUE → φ
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'─'*50}")
print(f"[B] SPIRALE LOGARITHMIQUE -> Detection de phi")

phi = (1 + math.sqrt(5)) / 2

# Une spirale logarithmique: r(θ) = a * exp(b*θ)
# Si b = ln(φ)/(π/2), la spirale fait un quart de tour par rectangle d'or
# On échantillonne l'hologramme le long de spirales avec différents b
# et on cherche à quel b l'interférence est maximale

best_spiral_energy = 0
best_b = 0
tested_b_vals = []

for b_mult in np.linspace(0.1, 3.0, 30):
    b = math.log(phi) / (math.pi / 2) * b_mult  # varie autour du b théorique
    spiral_energy = 0
    count = 0

    # Échantillonner 2000 points le long de la spirale
    for t in np.linspace(0, 8 * math.pi, 2000):
        r = SIZE/8 * math.exp(b * t)
        if r < SIZE/2 and r > 1:
            x = int(cx + r * math.cos(t))
            y = int(cy + r * math.sin(t))
            x = max(0, min(SIZE-1, x))
            y = max(0, min(SIZE-1, y))
            spiral_energy += amplitude[y, x]
            count += 1

    if count > 0:
        spiral_energy /= count
        tested_b_vals.append((b, b_mult, spiral_energy))
        if spiral_energy > best_spiral_energy:
            best_spiral_energy = spiral_energy
            best_b = b

# Le b optimal devrait être proche de b_phi = ln(φ) / (π/2) ≈ 0.306
b_phi = math.log(phi) / (math.pi / 2)
b_error = abs(best_b - b_phi) / b_phi * 100

print(f"  b_optimal = {best_b:.6f} | b_phi = {b_phi:.6f} | erreur = {b_error:.2f}%")
print(f"  Energie spirale optimale: {best_spiral_energy:.4f}")

if b_error < 15:
    discoveries.append({"constant": "phi", "method": "log_spiral_resonance",
                      "b_optimal": round(best_b, 6), "b_phi": round(b_phi, 6),
                      "error_pct": round(b_error, 2)})
    print(f"  [EMERGENT] phi dans la spirale logarithmique de l'hologramme !")

# Vérification alternative: mesurer le ratio des bandes sur la spirale
# Sur une spirale logarithmique, les croisements de bandes devraient être
# espacés d'un facteur φ en rayon
if best_b > 0:
    # Échantillonner le long de la spirale optimale
    radii = []
    for t in np.linspace(0, 6 * math.pi, 1000):
        r = SIZE/8 * math.exp(best_b * t)
        if 10 < r < SIZE/2 - 10:
            x = int(cx + r * math.cos(t))
            y = int(cy + r * math.sin(t))
            x = max(0, min(SIZE-1, x))
            y = max(0, min(SIZE-1, y))
            radii.append((r, amplitude[y, x]))

    if len(radii) > 10:
        # Trouver les rayons où l'amplitude est maximale (bandes de résonance)
        band_radii = []
        for j in range(5, len(radii)-5):
            if radii[j][1] > radii[j-1][1] and radii[j][1] > radii[j+1][1]:
                band_radii.append(radii[j][0])

        if len(band_radii) >= 3:
            ratios = [band_radii[i+1]/band_radii[i] for i in range(len(band_radii)-1)]
            avg_ratio = sum(ratios) / len(ratios)
            ratio_error = abs(avg_ratio - phi) / phi * 100
            print(f"  Bandes de resonance: {len(band_radii)}")
            print(f"  Ratio moyen entre bandes: {avg_ratio:.4f} | phi: {phi:.4f}")
            print(f"  Erreur: {ratio_error:.2f}%")
            if ratio_error < 15:
                discoveries.append({"constant": "phi", "method": "spiral_band_ratio",
                                  "avg_ratio": round(avg_ratio, 4), "error_pct": round(ratio_error, 2)})
                print(f"  [EMERGENT] φ dans l'espacement des bandes de la spirale !")

# ════════════════════════════════════════════════════════════════════════
# C. COORDONNÉES HYPERBOLIQUES → e
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'─'*50}")
print(f"[C] COORDONNEES HYPERBOLIQUES → Detection de e")

# En coordonnées hyperboliques (coordonnées de Poincaré pour le demi-plan),
# les géodésiques sont des cercles. La métrique hyperbolique fait émerger e
# dans la mesure des distances.

# Simplification : chercher une décroissance exponentielle dans le profil
# radial d'énergie, ce qui indiquerait une métrique effective exponentielle.
# Si amplitude(r) ∝ exp(-r/λ) avec λ tel que e est implicite.

# Utiliser le profil radial déjà calculé
log_radial = np.log(np.maximum(radial_profile[1:200], 1e-10))
x_radial = np.arange(1, 200)

# Fit linéaire sur log(amplitude) → pente = -1/λ
if len(x_radial) > 10:
    coeffs = np.polyfit(x_radial[:100], log_radial[:100], 1)
    slope = coeffs[0]
    intercept = coeffs[1]
    lambda_effective = -1 / slope if slope < 0 else 0

    print(f"  Fit exponentiel: amplitude ∝ exp(-r/{lambda_effective:.1f})")
    print(f"  Pente = {slope:.6f} | lambda = {lambda_effective:.1f}")

    # Si lambda ≈ e, ou si 1/lambda ≈ 1/e, e est implicite
    e_val = math.e
    if lambda_effective > 0:
        error_e = abs(lambda_effective - e_val) / e_val * 100
        error_inv = abs(1/lambda_effective - 1/e_val) / (1/e_val) * 100
        print(f"  Erreur lambda vs e: {error_e:.1f}%")
        print(f"  Erreur 1/lambda vs 1/e: {error_inv:.1f}%")
        if error_e < 20:
            discoveries.append({"constant": "e", "method": "hyperbolic_decay",
                              "lambda": round(lambda_effective, 2), "error_pct": round(error_e, 2)})
            print(f"  [EMERGENT] e dans la decroissance exponentielle !")
        elif error_inv < 20:
            discoveries.append({"constant": "e", "method": "hyperbolic_decay_inv",
                              "lambda": round(lambda_effective, 2), "error_pct": round(error_inv, 2)})
            print(f"  [EMERGENT] e via 1/lambda dans la decroissance exponentielle !")

# ════════════════════════════════════════════════════════════════════════
# RESUME
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*65}")
print(f"  RESULTATS — EMERGENCE NON-EUCLIDIENNE")
print(f"{'='*65}")

if discoveries:
    print(f"\n  [OK] {len(discoveries)} CONSTANTES EMERGENTES :")
    for d in discoveries:
        print(f"     {d['constant']}: via {d['method']} (erreur {d.get('error_pct','?')}%)")
else:
    print(f"\n  Aucune constante emergeante detectee.")

with open(RESULTS_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "discoveries": discoveries,
    }, f, ensure_ascii=False, indent=2)

print(f"\n  Resultats -> {RESULTS_FILE}")
print(f"{'='*65}")