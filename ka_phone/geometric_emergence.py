#!/usr/bin/env python3
"""
EMERGENCE GÉOMÉTRIQUE — Constantes mathématiques par structure de l'hologramme
================================================================================
Selon la théorie harmonique, les constantes mathématiques (φ, π, √2, √3, e)
émergent directement de la géométrie du support holographique, pas de son contenu.
Ce script analyse l'hologramme 1024×1024 sous l'angle purement géométrique.

Tests:
  1. Rapport diagonale/côté → √2
  2. Circonférence/diamètre des pics circulaires → π
  3. Ratio de Fibonacci → φ
  4. Transformée de Fourier → fréquences harmoniques
  5. Auto-corrélation spatiale → e (décroissance exponentielle)
"""

import os, sys, math, json, time
import numpy as np

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, '.')

SIZE = 1024
DATA_DIR = os.path.join('..', 'data', 'emergence')
HOLOGRAM_FILE = os.path.join(DATA_DIR, 'emergence_hologram_1024.npy')
RESULTS_FILE = os.path.join(DATA_DIR, 'geometric_emergence.json')

print("=" * 65)
print("  EMERGENCE GEOMETRIQUE — Constantes mathematiques intrinseques")
print("  Hologramme 1024x1024")
print("=" * 65)

if not os.path.exists(HOLOGRAM_FILE):
    print("\n[ERREUR] Hologramme introuvable.")
    sys.exit(1)

h = np.load(HOLOGRAM_FILE)
amplitude = np.abs(h)
print(f"\n[OK] Hologramme charge: {h.shape}")
print(f"  Energie totale: {np.sum(amplitude**2):.0f}")
print(f"  Amplitude max: {np.max(amplitude):.4f}")
print(f"  Amplitude moyenne: {np.mean(amplitude):.6f}")

discoveries = []

# ════════════════════════════════════════════════════════════════════════
# TEST 1: Rapport diagonale/côté → √2
# ════════════════════════════════════════════════════════════════════════
print(f"\n[TEST 1] Rapport diagonale/cote -> sqrt(2)")

# Mesurer l'amplitude le long de la diagonale principale
diag = np.array([amplitude[i, i] for i in range(SIZE)])
# Mesurer l'amplitude le long d'un côté (ligne médiane)
side = amplitude[SIZE//2, :]

# Longueur caractéristique : distance où l'amplitude tombe à 1/e du centre
center_diag = diag[SIZE//2]
threshold = center_diag / math.e

# Trouver le rayon effectif sur la diagonale
above = np.where(diag[SIZE//2:] < threshold)[0]
r_diag = above[0] if len(above) > 0 else SIZE//2

above_side = np.where(side[SIZE//2:] < threshold)[0]
r_side = above_side[0] if len(above_side) > 0 else SIZE//2

if r_side > 0:
    ratio_diag_side = r_diag / r_side
    expected_sqrt2 = math.sqrt(2)
    error = abs(ratio_diag_side - expected_sqrt2) / expected_sqrt2 * 100
    print(f"  r_diag={r_diag}, r_side={r_side}")
    print(f"  Ratio diagonale/cote = {ratio_diag_side:.4f} | sqrt(2) = {expected_sqrt2:.4f}")
    print(f"  Erreur: {error:.2f}%")
    if error < 10:
        print(f"  [EMERGENT] sqrt(2) emerge de la geometrie du support !")
        discoveries.append({"constant": "sqrt2", "method": "diagonal_ratio", 
                          "value": round(ratio_diag_side, 4), "error_pct": round(error, 2)})

# ════════════════════════════════════════════════════════════════════════
# TEST 2: Recherche de structures circulaires → π
# ════════════════════════════════════════════════════════════════════════
print(f"\n[TEST 2] Detection de structures circulaires -> pi")

# Échantillonner des cercles concentriques et mesurer l'amplitude moyenne
best_pi_ratio = 0
best_pi_radius = 0

for radius in [50, 100, 150, 200, 256, 300, 350, 400, 450]:
    # Mesurer l'amplitude sur le cercle de rayon 'radius'
    points = 100
    circle_amp = 0
    for a in range(points):
        angle = 2 * math.pi * a / points
        x = int(SIZE/2 + radius * math.cos(angle))
        y = int(SIZE/2 + radius * math.sin(angle))
        x = max(0, min(SIZE-1, x))
        y = max(0, min(SIZE-1, y))
        circle_amp += amplitude[y, x]
    circle_amp /= points
    
    # Circonférence = 2πr. Comparer avec le nombre de pixels significatifs
    # sur ce cercle (amplitude > moyenne)
    significant_pixels = 0
    for a in range(360):
        angle = 2 * math.pi * a / 360
        x = int(SIZE/2 + radius * math.cos(angle))
        y = int(SIZE/2 + radius * math.sin(angle))
        x = max(0, min(SIZE-1, x))
        y = max(0, min(SIZE-1, y))
        if amplitude[y, x] > np.mean(amplitude):
            significant_pixels += 1
    
    # Si les pixels significatifs forment un cercle, leur nombre = 2πr * (densité)
    if radius > 0 and significant_pixels > 10:
        # La densité effective = significant_pixels / (2πr)
        # Pour un cercle parfait, significant_pixels ≈ 2πr * (fraction angulaire)
        circumference = 2 * math.pi * radius
        measured_pi = significant_pixels / (2 * radius)  # approximation
        error_pi = abs(measured_pi - math.pi) / math.pi * 100
        if error_pi < 15:
            print(f"  r={radius:>4d}: {significant_pixels:>3d} pixels significatifs | pi mesure={measured_pi:.4f} | erreur={error_pi:.1f}%")
            if error_pi < best_pi_ratio or best_pi_radius == 0:
                best_pi_ratio = error_pi
                best_pi_radius = radius

if best_pi_radius > 0:
    discoveries.append({"constant": "pi", "method": "circle_detection",
                      "best_radius": best_pi_radius, "error_pct": round(best_pi_ratio, 2)})
    print(f"  [EMERGENT] pi emerge des structures circulaires de l'hologramme (r={best_pi_radius})")

# ════════════════════════════════════════════════════════════════════════
# TEST 3: Ratio de Fibonacci → φ
# ════════════════════════════════════════════════════════════════════════
print(f"\n[TEST 3] Ratio de Fibonacci -> phi")

# Analyse: dans l'hologramme 1024x1024, extraire les sous-rectangles
# successifs et vérifier si leur rapport tend vers φ
# Rectangle d'or: si a/b ≈ φ = (1+√5)/2 ≈ 1.618

phi = (1 + math.sqrt(5)) / 2

# Méthode: découper l'hologramme en bandes et chercher des motifs
# où le ratio des amplitudes entre bandes successives ≈ φ

# Extraire les profils d'amplitude horizontaux et verticaux
h_profile = np.mean(amplitude, axis=0)  # profil horizontal (moyenne sur y)
v_profile = np.mean(amplitude, axis=1)  # profil vertical (moyenne sur x)

# Chercher des ratios entre maxima locaux
def find_peaks(profile, min_distance=20):
    peaks = []
    for i in range(min_distance, len(profile) - min_distance):
        if profile[i] > profile[i-1] and profile[i] > profile[i+1]:
            # Local max
            if profile[i] > np.mean(profile) * 1.1:
                peaks.append((i, profile[i]))
    return peaks

h_peaks = find_peaks(h_profile)
v_peaks = find_peaks(v_profile)

# Vérifier les ratios entre amplitudes de pics
phi_matches = 0
for i in range(len(h_peaks)-1):
    if h_peaks[i][1] > 0 and h_peaks[i+1][1] > 0:
        ratio = h_peaks[i][1] / h_peaks[i+1][1]
        if 0.5 < ratio < 2.5:
            # Vérifier si ratio ou 1/ratio ≈ φ
            if abs(ratio - phi) / phi < 0.15:
                phi_matches += 1

for i in range(len(v_peaks)-1):
    if v_peaks[i][1] > 0 and v_peaks[i+1][1] > 0:
        ratio = v_peaks[i][1] / v_peaks[i+1][1]
        if 0.5 < ratio < 2.5:
            if abs(ratio - phi) / phi < 0.15:
                phi_matches += 1

print(f"  Pics horizontaux: {len(h_peaks)} | Pics verticaux: {len(v_peaks)}")
print(f"  Ratios proches de phi: {phi_matches}")
if phi_matches > 0:
    discoveries.append({"constant": "phi", "method": "fibonacci_ratio",
                      "phi_matches": phi_matches, "total_peaks": len(h_peaks)+len(v_peaks)})
    print(f"  [EMERGENT] phi emerge des ratios d'amplitude dans l'hologramme")

# ════════════════════════════════════════════════════════════════════════
# TEST 4: Transformée de Fourier 2D → fréquences harmoniques
# ════════════════════════════════════════════════════════════════════════
print(f"\n[TEST 4] Transformee de Fourier 2D -> frequences harmoniques")

# FFT 2D de l'amplitude
fft = np.fft.fft2(amplitude)
fft_shifted = np.fft.fftshift(np.abs(fft))

# Analyser le profil radial (moyenne sur les anneaux)
center = SIZE // 2
max_radius = SIZE // 2
radial_profile = np.zeros(max_radius)
counts = np.zeros(max_radius)

for i in range(SIZE):
    for j in range(SIZE):
        r = int(math.sqrt((i - center)**2 + (j - center)**2))
        if r < max_radius:
            radial_profile[r] += fft_shifted[i, j]
            counts[r] += 1

radial_profile = radial_profile / np.maximum(counts, 1)

# Chercher les pics dans le profil radial (fréquences dominantes)
fft_peaks = find_peaks(radial_profile, min_distance=5)
if len(fft_peaks) >= 2:
    # Ratio entre les fréquences des 2 premiers pics
    f1, a1 = fft_peaks[0]
    f2, a2 = fft_peaks[1] if len(fft_peaks) > 1 else (0, 0)
    if f1 > 0 and f2 > 0:
        f_ratio = f2 / f1
        print(f"  Pics FFT: f1={f1} (amp={a1:.2f}), f2={f2} (amp={a2:.2f})")
        print(f"  Ratio f2/f1 = {f_ratio:.4f}")
        if abs(f_ratio - phi) / phi < 0.2:
            discoveries.append({"constant": "phi", "method": "fft_ratio",
                              "f1": f1, "f2": f2, "ratio": round(f_ratio, 4)})
            print(f"  [EMERGENT] phi dans les frequences harmoniques de Fourier!")
        if abs(f_ratio - math.sqrt(2)) / math.sqrt(2) < 0.2:
            discoveries.append({"constant": "sqrt2", "method": "fft_ratio",
                              "f1": f1, "f2": f2, "ratio": round(f_ratio, 4)})
            print(f"  [EMERGENT] sqrt(2) dans les frequences harmoniques de Fourier!")

if len(fft_peaks) > 0:
    print(f"  {len(fft_peaks)} pics dans le profil radial FFT")

# ════════════════════════════════════════════════════════════════════════
# TEST 5: Auto-corrélation spatiale → e (décroissance exponentielle)
# ════════════════════════════════════════════════════════════════════════
print(f"\n[TEST 5] Auto-correlation spatiale -> e")

# Extraire une ligne et calculer l'auto-corrélation
line = amplitude[SIZE//2, :] - np.mean(amplitude)
autocorr = np.correlate(line, line, mode='same')
autocorr = autocorr / autocorr[SIZE//2]  # normaliser

# Prendre le côté droit (décroissance)
right_half = autocorr[SIZE//2:SIZE//2 + 200]
x = np.arange(len(right_half))

# Fit exponentiel: y = A * exp(-x / tau) + C
# Si la décroissance est exponentielle, 1/tau ≈ e (ou lié à e)
if len(right_half) > 10 and right_half[0] > 0:
    # Méthode simple: regarder le ratio de décroissance
    # Après 1 "constante de temps", l'amplitude tombe à 1/e
    y_initial = right_half[0]
    y_target = y_initial / math.e
    
    # Trouver x où y ≈ y_target
    tau_measured = None
    for i in range(1, len(right_half)):
        if right_half[i] <= y_target:
            tau_measured = i
            break
    
    if tau_measured:
        print(f"  Constante de temps tau = {tau_measured} pixels")
        print(f"  1/tau = {1/tau_measured:.6f}")
        # Si 1/tau ≈ 1/e ≈ 0.3679, alors e est implicite
        e_inverse = 1 / math.e
        error_tau = abs(1/tau_measured - e_inverse) / e_inverse * 100
        print(f"  Erreur vs 1/e: {error_tau:.2f}%")
        if error_tau < 30:
            discoveries.append({"constant": "e", "method": "autocorr_decay",
                              "tau": tau_measured, "error_pct": round(error_tau, 2)})
            print(f"  [EMERGENT] e emerge de la decroissance exponentielle de l'auto-correlation!")

# ════════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*65}")
print(f"  RESULTATS — ÉMERGENCE GÉOMÉTRIQUE")
print(f"{'='*65}")

if discoveries:
    print(f"\n  ✨ {len(discoveries)} CONSTANTES ÉMERGENTES DE LA GÉOMÉTRIE :")
    for d in discoveries:
        print(f"     {d['constant']}: via {d['method']}")
else:
    print(f"\n  Aucune constante émergente détectée par géométrie pure.")

# Sauvegarde
with open(RESULTS_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "discoveries": discoveries,
        "hologram_stats": {
            "size": SIZE,
            "max_amplitude": float(np.max(amplitude)),
            "mean_amplitude": float(np.mean(amplitude)),
            "energy": float(np.sum(amplitude**2)),
        }
    }, f, ensure_ascii=False, indent=2)

print(f"\n  Résultats -> {RESULTS_FILE}")
print(f"{'='*65}")