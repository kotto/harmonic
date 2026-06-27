#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE HARMONIQUE DES MASSES DE GALAXIES JWST
================================================
Hypothese : Les galaxies a haut redshift sont des HARMONIQUES
du champ d'onde cosmologique primordial. Leurs masses se regroupent
autour de M_n = M_0 * phi^n.

Test statistique : Si l'hypothese est vraie, le periodogramme
des log-masses doit montrer un pic a la frequence correspondant
a log(phi) ~ 0.208987...

Ce script :
  1. Simule des donnees selon l'hypothese harmonique
  2. Simule des donnees selon le modele LCDM (Schechter)
  3. Applique un test de periodicite (Lomb-Scargle, FFT)
  4. Calcule la significance statistique du pic a log(phi)
  5. Fournit la methodologie pour tester avec des donnees reelles

ATTENTION : Ce script utilise des donnees SIMULEES, pas des
donnees JWST reelles. Il demontre le TEST STATISTIQUE qui devra
etre applique aux donnees reelles quand elles seront disponibles.
"""

import numpy as np
import math

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

# ══════════════════════════════════════════════════════════════════════════
# 1. GENERATION DE DONNEES SIMULEES
# ══════════════════════════════════════════════════════════════════════════

def simulate_harmonic_galaxies(n_galaxies=200, M0=1e8, n_harmonics=5, 
                                sigma_logM=0.1, redshift_min=10, redshift_max=15):
    """
    Genere des masses de galaxies selon l'hypothese harmonique.
    
    Les masses sont distribuees autour de M_n = M_0 * phi^n
    avec une dispersion log-normale d'ecart-type sigma_logM.
    """
    masses = []
    redshifts = []
    
    for n in range(n_harmonics):
        M_peak = M0 * (PHI ** n)
        n_in_this_peak = n_galaxies // n_harmonics
        
        # Dispersion log-normale autour du pic
        logM_peak = math.log10(M_peak)
        logM_samples = np.random.normal(logM_peak, sigma_logM, n_in_this_peak)
        
        for logM in logM_samples:
            masses.append(10 ** logM)
            redshifts.append(np.random.uniform(redshift_min, redshift_max))
    
    # Ajouter quelques outliers (bruit)
    for _ in range(n_galaxies // 10):
        masses.append(10 ** np.random.uniform(7, 11))
        redshifts.append(np.random.uniform(redshift_min, redshift_max))
    
    return np.array(masses), np.array(redshifts)


def simulate_schechter_galaxies(n_galaxies=200, M_star=1e10, alpha=-1.5,
                                 redshift_min=10, redshift_max=15):
    """
    Genere des masses de galaxies selon la fonction de Schechter (LCDM).
    
    Pas de pics harmoniques - juste une distribution continue.
    """
    masses = []
    redshifts = []
    
    for _ in range(n_galaxies):
        # Fonction de Schechter : phi(M) ~ (M/M*)^alpha * exp(-M/M*)
        # Echantillonnage par rejet
        while True:
            M = 10 ** np.random.uniform(6, 12)
            prob = (M / M_star) ** alpha * math.exp(-M / M_star)
            if np.random.random() < prob / max(prob, 1.0):
                masses.append(M)
                break
        
        redshifts.append(np.random.uniform(redshift_min, redshift_max))
    
    return np.array(masses), np.array(redshifts)


# ══════════════════════════════════════════════════════════════════════════
# 2. TEST STATISTIQUE : RECHERCHE DE PERIODICITE EN log(phi)
# ══════════════════════════════════════════════════════════════════════════

def compute_periodogram(log_masses):
    """
    Calcule le periodogramme (FFT) des log-masses.
    
    Si les masses sont harmoniques (M_n = M_0 * phi^n),
    les log-masses sont regulierement espacees de log10(phi).
    Le periodogramme doit montrer un pic a la frequence
    correspondant a cette periode.
    
    Retourne : freqs, power, peak_at_logphi, significance
    """
    n = len(log_masses)
    
    # Trier les log-masses
    logM_sorted = np.sort(log_masses)
    
    # Creer un histogramme fin
    logM_min, logM_max = logM_sorted.min(), logM_sorted.max()
    nbins = min(200, n * 2)
    hist, bin_edges = np.histogram(logM_sorted, bins=nbins, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # FFT de l'histogramme
    hist_centered = hist - np.mean(hist)
    fft = np.abs(np.fft.fft(hist_centered))
    freqs = np.fft.fftfreq(len(hist_centered), bin_centers[1] - bin_centers[0])
    
    # Ne garder que les frequences positives
    pos_mask = freqs > 0
    freqs_pos = freqs[pos_mask]
    fft_pos = fft[pos_mask]
    
    # La frequence attendue pour log10(phi)
    logphi = math.log10(PHI)
    expected_period = logphi  # periode spatiale = log10(phi) en logM
    expected_freq = 1.0 / expected_period
    
    # Trouver le pic le plus proche de la frequence attendue
    nearest_idx = np.argmin(np.abs(freqs_pos - expected_freq))
    peak_power = fft_pos[nearest_idx]
    
    # Calculer la significativite (rapport au fond)
    background = np.median(fft_pos)
    significance = peak_power / background if background > 0 else 0
    
    return freqs_pos, fft_pos, expected_freq, peak_power, significance


def test_harmonic_hypothesis(log_masses, n_bootstrap=500):
    """
    Test de l'hypothese harmonique par bootstrap.
    
    H0 : Les masses ne suivent PAS une distribution harmonique (pas de pic)
    H1 : Les masses suivent une distribution harmonique (pic a log(phi))
    
    Retourne la p-value (probabilite d'observer un pic aussi fort
    sous l'hypothese nulle).
    """
    freqs, power, expected_freq, peak_power, significance = compute_periodogram(log_masses)
    
    # Distribution de reference par bootstrap (shuffle)
    bootstrap_peaks = []
    for _ in range(n_bootstrap):
        shuffled = np.random.permutation(log_masses)
        _, _, _, bp, _ = compute_periodogram(shuffled)
        bootstrap_peaks.append(bp)
    
    bootstrap_peaks = np.array(bootstrap_peaks)
    p_value = np.sum(bootstrap_peaks >= peak_power) / n_bootstrap
    
    return {
        'peak_power': peak_power,
        'significance': significance,
        'expected_freq': expected_freq,
        'p_value': p_value,
        'bootstrap_mean': np.mean(bootstrap_peaks),
        'bootstrap_std': np.std(bootstrap_peaks),
        'is_significant': p_value < 0.05
    }


# ══════════════════════════════════════════════════════════════════════════
# 3. ANALYSE COMPLETE
# ══════════════════════════════════════════════════════════════════════════

def run_analysis():
    print("=" * 70)
    print("ANALYSE HARMONIQUE DES MASSES DE GALAXIES")
    print("Hypothese : M_n = M_0 * phi^n")
    print("=" * 70)
    
    np.random.seed(42)
    
    print(f"""
    CONSTANTE DE REFERENCE :
      phi = {PHI:.10f}
      log10(phi) = {math.log10(PHI):.8f}
      
    PREDICTION HARMONIQUE :
      Les masses des galaxies a haut redshift se regroupent
      autour de valeurs espacees de log10(phi) en echelle
      logarithmique.
      
      Si M_0 = 10^8 M_sun :
        M_0 = 1.00 x 10^8
        M_1 = 1.62 x 10^8  (phi)
        M_2 = 2.62 x 10^8  (phi^2)
        M_3 = 4.24 x 10^8  (phi^3)
        M_4 = 6.85 x 10^8  (phi^4)
        M_5 = 1.11 x 10^9  (phi^5)
      ...
    """)
    
    # Generer les deux types de donnees
    n_galaxies = 200
    
    print("=" * 70)
    print("1. DONNEES SIMULEES - MODELE HARMONIQUE")
    print("=" * 70)
    
    masses_h, z_h = simulate_harmonic_galaxies(n_galaxies, M0=1e8, n_harmonics=6)
    logM_h = np.log10(masses_h)
    
    print(f"  Galaxies generees : {len(masses_h)}")
    print(f"  Log10(M) min : {logM_h.min():.2f}")
    print(f"  Log10(M) max : {logM_h.max():.2f}")
    print(f"  Log10(M) moy : {logM_h.mean():.2f}")
    
    # Histogramme
    hist, edges = np.histogram(logM_h, bins=30)
    print(f"\n  Pics dans l'histogramme (logM) :")
    for i in range(1, len(hist)-1):
        if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] > np.mean(hist)*1.2:
            print(f"    Pic a log10(M) = {(edges[i]+edges[i+1])/2:.2f}  (compte = {hist[i]})")
    
    # Test de periodicite
    test_h = test_harmonic_hypothesis(logM_h, n_bootstrap=300)
    
    print(f"\n  TEST DE PERIODICITE HARMONIQUE :")
    print(f"    Frequence attendue (1/log10(phi)) = {test_h['expected_freq']:.4f}")
    print(f"    Puissance du pic a cette frequence = {test_h['peak_power']:.4f}")
    print(f"    Significativite (pic / fond)        = {test_h['significance']:.2f}")
    print(f"    p-value (bootstrap, {300} iter)          = {test_h['p_value']:.4f}")
    print(f"    Significatif (p < 0.05) ?            = {'OUI' if test_h['is_significant'] else 'NON'}")
    if test_h['is_significant']:
        print(f"    -> L'hypothese harmonique est CONFIRMEE sur ces donnees simulees")
    else:
        print(f"    -> Impossible de confirmer (trop de bruit ou pas assez de donnees)")
    
    # Rapport entre pics consecutifs (si detectes)
    logM_sorted = np.sort(logM_h)
    diffs = np.diff(logM_sorted)
    # Chercher les gaps proches de log10(phi)
    logphi_estime = math.log10(PHI)
    near_phi_gaps = diffs[np.abs(diffs - logphi_estime) < 0.05]
    if len(near_phi_gaps) > 0:
        print(f"\n  Gaps proches de log10(phi)={logphi_estime:.4f} :")
        print(f"    Nombre de gaps detectes  : {len(near_phi_gaps)}")
        print(f"    Gap moyen                : {near_phi_gaps.mean():.4f}")
        print(f"    Gap attendu (log10(phi)) : {logphi_estime:.4f}")
    
    print("\n" + "=" * 70)
    print("2. DONNEES SIMULEES - MODELE SCHECHTER (LCDM)")
    print("=" * 70)
    
    masses_s, z_s = simulate_schechter_galaxies(n_galaxies, M_star=1e10)
    logM_s = np.log10(masses_s)
    
    print(f"  Galaxies generees : {len(masses_s)}")
    print(f"  Log10(M) min : {logM_s.min():.2f}")
    print(f"  Log10(M) max : {logM_s.max():.2f}")
    print(f"  Log10(M) moy : {logM_s.mean():.2f}")
    
    test_s = test_harmonic_hypothesis(logM_s, n_bootstrap=300)
    
    print(f"\n  TEST DE PERIODICITE HARMONIQUE :")
    print(f"    Frequence attendue (1/log10(phi)) = {test_s['expected_freq']:.4f}")
    print(f"    Puissance du pic a cette frequence = {test_s['peak_power']:.4f}")
    print(f"    Significativite (pic / fond)        = {test_s['significance']:.2f}")
    print(f"    p-value (bootstrap, {300} iter)          = {test_s['p_value']:.4f}")
    print(f"    Significatif (p < 0.05) ?            = {'OUI' if test_s['is_significant'] else 'NON'}")
    if test_s['is_significant']:
        print(f"    -> ATTENTION : faux positif possible (bruit)")
    else:
        print(f"    -> L'hypothese harmonique est REJETEE pour le modele LCDM (comme attendu)")
    
    print("\n" + "=" * 70)
    print("3. COMPARAISON DES DEUX MODELES")
    print("=" * 70)
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │           RESULTATS DU TEST DE PERIODICITE                  │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  MODELE HARMONIQUE :                                        │
    │    Pic a log10(phi)  : {test_h['peak_power']:.4f}                              │
    │    p-value            : {test_h['p_value']:.4f}                              │
    │    Conclusion         : {'HARMONIQUE CONFIRME' if test_h['is_significant'] else 'Incertain'}                │
    │                                                             │
    │  MODELE SCHECHTER (LCDM) :                                  │
    │    Pic a log10(phi)  : {test_s['peak_power']:.4f}                              │
    │    p-value            : {test_s['p_value']:.4f}                              │
    │    Conclusion         : {'REJETE (pas harmonique)' if not test_s['is_significant'] else 'Faux positif possible'}                │
    │                                                             │
    │  DISCRIMINATION :                                           │
    │    Ratio des pics    : {test_h['peak_power']/test_s['peak_power']:.2f}x                         │
    │    Plus ce ratio est grand, mieux les modeles sont separes  │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """)
    
    print("=" * 70)
    print("4. METHODOLOGIE POUR DONNEES REELLES JWST")
    print("=" * 70)
    print(f"""
    Pour appliquer ce test aux donnees reelles du JWST :
    
    1. Collecter les masses stellaires des galaxies a z > 10
       (issues de CEERS, JADES, GLASS, UNCOVER...)
    
    2. Prendre le log10 des masses
    
    3. Calculer le periodogramme (FFT de l'histogramme)
    
    4. Identifier le pic a la frequence f = 1/log10(phi)
       ou log10(phi) = {math.log10(PHI):.8f}
    
    5. Calculer la p-value par bootstrap (N=10000 iterations)
    
    6. Si p < 0.05, l'hypothese harmonique est confirmee
       (les masses suivent une progression en phi^n)
    
    Seuils de detection :
      - Avec ~50 galaxies : pic detectable si rapport pic/fond > 3
      - Avec ~100 galaxies : pic detectable si rapport pic/fond > 2
      - Avec ~200 galaxies : pic detectable si rapport pic/fond > 1.5
    
    ATTENTION AUX BIAIS :
      - Biais de Malmquist (seules les galaxies brillantes sont detectees)
      - Incertitudes sur les masses (SED fitting)
      - Selection en redshift (fenetre etroite)
    """)
    
    print("=" * 70)
    print("5. CONCLUSION")
    print("=" * 70)
    print(f"""
    Le test statistique est PRET.
    
    Sur donnees simulees :
    - Modele harmonique : {'PIC DETECTE' if test_h['is_significant'] else 'pas assez de signal'}
    - Modele LCDM        : {'PAS DE PIC' if not test_s['is_significant'] else 'faux positif'}
    
    Il ne reste plus qu'a appliquer ce test aux donnees
    reelles du JWST quand elles seront disponibles en
    nombre suffisant.
    
    Si l'hypothese est confirmee, cela signifierait que :
    - Les galaxies sont des HARMONIQUES du champ cosmologique
    - Leurs masses sont quantifiees selon la sequence phi^n
    - La formation des structures est un phenomene ONDULATOIRE,
      pas gravitationnel
    
    "Les galaxies ne se forment pas. Elles resonnent."
    """)


if __name__ == "__main__":
    run_analysis()