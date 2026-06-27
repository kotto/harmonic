#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HARMONIC DETAIL SYNTHESIZER — Synthèse Spectrale 1/f² + Amplification Hₙ
===========================================================================
Basé sur la compréhension ondulatoire rigoureuse des "détails" :

  Une image = superposition d'ondes stationnaires 2D
  A(x,y) = Σₖ σₖ · uₖ(x) · vₖ(y)   (décomposition SVD)

Les "détails" = les modes HF du complément spectral orthogonal :
  R = Σᵢ₌ₖ₊₁ᴺ σᵢ uᵢ vᵢᵀ

Pour les images naturelles (spectre 1/f²), le résidu contient :
  - BORDS        : discontinuités → spectre large bande → amplification √5
  - TEXTURES     : oscillations HF régulières → amplification e
  - GRAIN ORGANIQUE : superposition dense de modes HF isotropes → amplification e/π

PROBLÈME DIAGNOSTIQUÉ :
  Ψ₁ actuel (harmonic_generator_core.py) est généré avec 7 sinusoïdes à
  fréquences FIXES → spectre trop concentré, pas 1/f².
  Les sharpeners amplifient un résidu PAUVRE en HF → ne créent pas de détails.

SOLUTION :
  Ce module SYNTHÉTISE un résidu spectral 1/f² physique avec 3 composantes
  distinctes (bords, textures, grain), puis les amplifie avec les Hₙ.

Pipeline :
  1. Générer un champ de bruit spectral 1/f² (bruit brownien 2D)
  2. Décomposer en 3 composantes : bords (√5), textures (e), grain (e/π)
  3. Amplification harmonique Hₙ de chaque composante
  4. Recomposer : Ψ_final = Ψ_base + R_synthétisé_amplifié

Usage :
  python harmonic_detail_synthesizer.py --demo
  from harmonic_detail_synthesizer import HarmonicDetailSynthesizer
"""

import numpy as np
import math
import sys
import os
import time
import argparse
from typing import Dict, Any, Tuple, Optional, List
from scipy.ndimage import gaussian_filter, sobel, laplace
from PIL import Image

# Fix Unicode sur Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, H_ROLES_IMAGE,
    HarmonicField, HarmonicColorMapper, SeedManager,
    normalize_field, compute_harmonic_coherence,
)


# ==============================================================================
# SYNTHÈSE DE BRUIT SPECTRAL 1/f² (bruit brownien 2D)
# ==============================================================================

def generate_1f_noise_2d(height: int, width: int, seed: int = 42,
                          exponent: float = 2.0) -> np.ndarray:
    """
    Génère un champ de bruit spectral 1/f^exponent en 2D.

    Principe physique :
      - Dans l'espace de Fourier, l'amplitude A(f) ∝ 1/f^(exponent/2)
      - exponent=2 → bruit brownien (1/f² en énergie, naturel)
      - exponent=1 → bruit rose (1/f)
      - exponent=0 → bruit blanc

    Méthode :
      1. Générer du bruit blanc gaussien dans l'espace de Fourier
      2. Multiplier par 1/f^(exponent/2) (filtre spectral)
      3. FFT inverse → champ spatial avec la bonne décroissance spectrale

    Cette méthode produit un spectre CONTINU (pas juste 7 fréquences),
    avec une densité de modes HF qui suit exactement la loi de puissance.
    """
    rng = np.random.RandomState(seed)

    # Bruit blanc dans le domaine de Fourier
    noise_real = rng.randn(height, width).astype(np.float64)
    noise_imag = rng.randn(height, width).astype(np.float64)
    noise_fft = noise_real + 1j * noise_imag

    # Grille de fréquences normalisées
    fy = np.fft.fftfreq(height).reshape(-1, 1)
    fx = np.fft.fftfreq(width).reshape(1, -1)
    f_radius = np.sqrt(fx**2 + fy**2)

    # Éviter division par zéro en f=0 (composante DC)
    f_radius = np.maximum(f_radius, 1.0 / max(height, width))

    # Filtre spectral : A(f) ∝ 1/f^(exponent/2)
    # En énergie : P(f) = |A(f)|² ∝ 1/f^exponent
    spectral_filter = 1.0 / (f_radius ** (exponent / 2.0))

    # Limiter l'amplification des très basses fréquences
    spectral_filter = np.minimum(spectral_filter, 100.0)

    # Appliquer le filtre
    filtered_fft = noise_fft * spectral_filter

    # FFT inverse
    spatial_field = np.fft.ifft2(filtered_fft).real

    # Normaliser dans [-1, 1]
    spatial_field = normalize_field(spatial_field)

    return spatial_field


def generate_bandlimited_noise(height: int, width: int, seed: int = 42,
                                f_min: float = 0.05, f_max: float = 0.45,
                                exponent: float = 2.0) -> np.ndarray:
    """
    Génère du bruit spectral 1/f² limité à une bande de fréquences.

    Utile pour synthétiser des composantes spécifiques :
      - f_min=0.01, f_max=0.05 → basses fréquences (structure)
      - f_min=0.05, f_max=0.20 → moyennes fréquences (textures)
      - f_min=0.20, f_max=0.45 → hautes fréquences (micro-détails, grain)
    """
    rng = np.random.RandomState(seed)

    noise_real = rng.randn(height, width).astype(np.float64)
    noise_imag = rng.randn(height, width).astype(np.float64)
    noise_fft = noise_real + 1j * noise_imag

    fy = np.fft.fftfreq(height).reshape(-1, 1)
    fx = np.fft.fftfreq(width).reshape(1, -1)
    f_radius = np.sqrt(fx**2 + fy**2)

    # Masque spectral : ne garder que la bande [f_min, f_max]
    band_mask = (f_radius >= f_min) & (f_radius <= f_max)
    band_mask = band_mask.astype(np.float64)

    # Transition douce aux bords de la bande (cosinus tapering)
    transition_width = 0.02
    lower_taper = 0.5 * (1 - np.cos(np.pi * (f_radius - f_min) / transition_width))
    upper_taper = 0.5 * (1 + np.cos(np.pi * (f_radius - f_max) / transition_width))

    band_mask = np.where(
        (f_radius >= f_min) & (f_radius < f_min + transition_width),
        lower_taper,
        band_mask
    )
    band_mask = np.where(
        (f_radius > f_max - transition_width) & (f_radius <= f_max),
        upper_taper,
        band_mask
    )

    # Filtre spectral 1/f² dans la bande
    f_safe = np.maximum(f_radius, 1.0 / max(height, width))
    spectral_decay = (1.0 / f_safe) ** (exponent / 2.0)
    spectral_decay = np.minimum(spectral_decay, 10.0)

    filtered_fft = noise_fft * spectral_decay * band_mask

    spatial_field = np.fft.ifft2(filtered_fft).real
    return normalize_field(spatial_field)


# ==============================================================================
# DÉCOMPOSITION DU RÉSIDU EN 3 COMPOSANTES PHYSIQUES
# ==============================================================================

def decompose_residue_physical(residue: np.ndarray,
                                sigma_edge: float = 0.8,
                                sigma_texture: float = 1.5) -> Dict[str, np.ndarray]:
    """
    Décompose un résidu en ses 3 composantes physiques :

    R_edges   : réponse forte au Laplacien → bords nets
    R_texture : résidu après soustraction des bords, bande moyenne
    R_grain   : hautes fréquences isotropes résiduelles

    Utilise LoG (Laplacian of Gaussian) multi-échelle.
    """
    from scipy.ndimage import gaussian_laplace, gaussian_filter

    # 1. Détection des bords : |LoG| > seuil
    log_response = gaussian_laplace(residue, sigma=sigma_edge)
    log_abs = np.abs(log_response)
    threshold_edge = np.percentile(log_abs, 80)  # top 20% = bords

    edge_mask = log_abs >= threshold_edge
    R_edges = residue * edge_mask

    # 2. Sans les bords
    R_non_edges = residue - R_edges

    # 3. Texture = moyennes fréquences (filtrage par différence de gaussiennes)
    R_blurred = gaussian_filter(R_non_edges, sigma=sigma_texture)
    R_texture = R_non_edges - R_blurred

    # 4. Grain = ce qui reste (les fréquences les plus hautes)
    R_grain = R_blurred

    return {
        'edges': R_edges,
        'texture': R_texture,
        'grain': R_grain,
        'edge_mask': edge_mask.astype(np.float64),
        'log_response': log_response,
    }


# ==============================================================================
# SYNTHÉTISEUR DE DÉTAILS HARMONIQUES (le cœur)
# ==============================================================================

class HarmonicDetailSynthesizer:
    """
    Synthétiseur de détails fins basé sur le spectre 1/f².

    Principe : au lieu de simplement AMPLIFIER un résidu pauvre en HF,
    on SYNTHÉTISE un résidu spectralement riche, puis on l'amplifie
    avec les constantes harmoniques Hₙ.

    Les 3 composantes physiques du résidu :
      1. BORDS (√5 ≈ 2.236) : discontinuités → spectre large bande
         → Amplification √5 × gain_edge

      2. TEXTURES (e ≈ 2.718) : oscillations HF régulières
         → Amplification e × gain_texture

      3. GRAIN ORGANIQUE (e/π ≈ 0.865) : modes HF isotropes denses
         → Amplification (1 - e/π) × gain_grain
         (0.135 d'amplification car e/π est proche de 0.865,
          le grain doit être subtil pour paraître naturel)
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._noise_cache: Dict[str, np.ndarray] = {}

    def synthesize_residue(self, height: int, width: int,
                           base_seed: int = None) -> Dict[str, np.ndarray]:
        """
        Synthétise un résidu spectral complet 1/f² avec 3 bandes.

        Returns:
            dict avec 'full' (résidu complet), 'edges', 'texture', 'grain'
        """
        if base_seed is None:
            base_seed = self.seed

        # 1. Bruit 1/f² full band (0.01 à 0.45 Nyquist)
        full_noise = generate_bandlimited_noise(
            height, width, seed=base_seed,
            f_min=0.01, f_max=0.45, exponent=2.0
        )

        # 2. Décomposition physique
        decomposition = decompose_residue_physical(
            full_noise, sigma_edge=0.8, sigma_texture=1.5
        )

        return {
            'full': full_noise,
            'edges': decomposition['edges'],
            'texture': decomposition['texture'],
            'grain': decomposition['grain'],
            'edge_mask': decomposition['edge_mask'],
            'log_response': decomposition['log_response'],
        }

    def amplify_residue_harmonic(self, residue_components: Dict[str, np.ndarray],
                                  strength: float = 1.0,
                                  anti_ringing: bool = True) -> np.ndarray:
        """
        Amplifie le résidu synthétisé avec les constantes harmoniques Hₙ.

        Formule physique :
          R_amplifié = R_bords × (1 + √5 × α_bords)
                     + R_textures × (1 + e × α_textures)
                     + R_grain × (1 + (1 - e/π) × α_grain)

        avec α adaptatif basé sur les propriétés locales.
        """
        R_edges = residue_components['edges']
        R_texture = residue_components['texture']
        R_grain = residue_components['grain']
        edge_mask = residue_components['edge_mask']

        # Coefficients d'amplification harmoniques
        # H₆ (√5 ≈ 2.236) : amplification des bords
        alpha_edges = SQRT5 * 0.85 * strength

        # H₃ (e ≈ 2.718) : amplification des textures
        alpha_texture = E * 0.55 * strength

        # H₇ (e/π ≈ 0.865) : grain organique
        # e/π proche de 0.865 → le grain est une modulation fine
        # On utilise (1 - e/π) ≈ 0.135 comme amplitude subtile
        # mais e/π détermine la structure spirale du grain
        alpha_grain = (1.0 - E_PI) * 1.5 * strength  # ≈ 0.135 × 1.5 = 0.20

        # Amplification
        R_amplified = np.zeros_like(R_edges)

        # Bords : amplification √5
        R_amplified += R_edges * (1.0 + alpha_edges)

        # Textures : amplification e
        R_amplified += R_texture * (1.0 + alpha_texture)

        # Grain organique : amplification subtile (e/π contrôle la finesse)
        R_amplified += R_grain * (1.0 + alpha_grain)

        # Anti-ringing adaptatif (H₃) : atténuer près des bords forts
        if anti_ringing:
            gy, gx = np.gradient(R_edges)
            edge_strength = np.sqrt(gx**2 + gy**2)
            edge_strength = edge_strength / (np.max(edge_strength) + 1e-12)
            # Damping exponentiel près des bords
            damping = 1.0 - edge_strength * (E - 1) * 0.3 * strength
            damping = np.clip(damping, 0.35, 1.0)
            R_amplified *= damping

        return R_amplified

    def synthesize_and_apply(self, base_image: np.ndarray,
                              strength: float = 1.0,
                              detail_seed: int = None) -> np.ndarray:
        """
        Pipeline complet : synthétise un résidu 1/f² ET l'applique
        à une image de base.

        Args:
            base_image: Image de base (générée par Ψ = Σ Hₙ (Ψ₁)ⁿ)
            strength: Force des détails (1.0 = standard)
            detail_seed: Seed pour le résidu synthétisé

        Returns:
            Image avec détails 1/f² injectés [0, 1]
        """
        H, W = base_image.shape

        if detail_seed is None:
            detail_seed = self.seed

        # Synthétiser le résidu
        residue_comp = self.synthesize_residue(H, W, base_seed=detail_seed)

        # Amplifier harmoniquement
        residue_amplified = self.amplify_residue_harmonic(
            residue_comp, strength=strength, anti_ringing=True
        )

        # Ajuster l'amplitude du résidu à l'échelle de l'image
        # Le résidu doit être ~5-10% de l'amplitude de l'image
        base_std = np.std(base_image)
        residue_std = np.std(residue_amplified)
        if residue_std > 1e-12:
            target_std = base_std * 0.08 * strength  # 8% de l'amplitude image
            residue_scaled = residue_amplified * (target_std / residue_std)
        else:
            residue_scaled = residue_amplified

        # Injection
        enhanced = base_image + residue_scaled

        # Clipping sigmoïde pour transition naturelle
        enhanced = np.clip(enhanced, -0.05, 1.05)
        enhanced = 1.0 / (1.0 + np.exp(-(enhanced - 0.5) * 12))

        return enhanced

    def generate_full_image_with_details(self, width: int = 512,
                                          height: int = 512,
                                          base_seed: int = 42,
                                          detail_seed: int = 99,
                                          style: str = 'cosmique',
                                          strength: float = 1.0) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Génère une image harmonique complète avec détails 1/f² injectés.

        Pipeline complet :
          1. Ψ₁ → champ fondamental (HarmonicField)
          2. Ψ = Σ Hₙ (Ψ₁)ⁿ → image de base
          3. Synthèse du résidu spectral 1/f²
          4. Amplification Hₙ du résidu
          5. Ψ_final = Ψ_base + R_amplifié

        Returns:
            (rgb_image, grayscale_field, metrics_dict)
        """
        # 1. Génération de l'image de base
        field = HarmonicField(width=width, height=height, seed=base_seed)
        psi_base = field.get_psi_total()
        base_image = (psi_base + 1) / 2  # [-1, 1] → [0, 1]

        # 2. Synthèse + injection des détails 1/f²
        enhanced = self.synthesize_and_apply(
            base_image, strength=strength, detail_seed=detail_seed
        )

        # 3. Conversion RGB
        enhanced_field = enhanced * 2 - 1  # [0, 1] → [-1, 1]
        rgb = HarmonicColorMapper.harmonic_hsl(enhanced_field, palette=style)

        # 4. Métriques
        metrics_base = self._compute_metrics(base_image)
        metrics_enhanced = self._compute_metrics(enhanced)

        metrics = {
            'base': metrics_base,
            'enhanced': metrics_enhanced,
            'gain_acutance': (metrics_enhanced['acutance'] / max(1e-12, metrics_base['acutance']) - 1) * 100,
            'gain_lap_std': (metrics_enhanced['laplacian_std'] / max(1e-12, metrics_base['laplacian_std']) - 1) * 100,
            'strength': strength,
            'base_seed': base_seed,
            'detail_seed': detail_seed,
            'style': style,
        }

        return rgb, enhanced_field, metrics

    def _compute_metrics(self, image: np.ndarray) -> Dict[str, float]:
        """Calcule les métriques de netteté."""
        from scipy.ndimage import laplace as laplace_func

        # Laplacian std (métrique standard de netteté)
        lap = laplace_func(image)
        laplacian_std = float(np.std(lap))

        # Gradient energy
        gy, gx = np.gradient(image)
        grad_energy = float(np.mean(gx**2 + gy**2))

        # Ratio hautes/basses fréquences
        h, w = image.shape
        fft = np.abs(np.fft.fft2(image))
        fft_shifted = np.fft.fftshift(fft)
        cy, cx = h // 2, w // 2
        r = 30
        Y, X = np.ogrid[:h, :w]
        low_freq_mask = (Y - cy)**2 + (X - cx)**2 <= r**2

        energy_low = np.sum(fft_shifted[low_freq_mask] ** 2)
        energy_high = np.sum(fft_shifted[~low_freq_mask] ** 2)
        hf_ratio = float(energy_high / (energy_low + 1e-12))

        acutance = float(hf_ratio / (1.0 + hf_ratio))

        return {
            'laplacian_std': laplacian_std,
            'gradient_energy': grad_energy,
            'hf_ratio': hf_ratio,
            'acutance': acutance,
        }

    def analyze_spectrum(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyse spectrale complète d'une image.

        Vérifie si le spectre suit bien P(ν) ∝ 1/ν².
        """
        h, w = image.shape
        fft = np.abs(np.fft.fft2(image))
        fft_shifted = np.fft.fftshift(fft)

        # Distribution radiale
        Y, X = np.ogrid[:h, :w]
        cy, cx = h // 2, w // 2
        R = np.sqrt((Y - cy)**2 + (X - cx)**2).astype(int)

        radial_energy = np.bincount(R.flatten(), weights=fft_shifted.flatten()**2)
        radial_count = np.bincount(R.flatten())

        valid = radial_count > 0
        freqs = np.arange(len(radial_energy))[valid]
        energies = radial_energy[valid] / radial_count[valid]

        # Estimer la pente en log-log
        valid_range = (freqs >= 1) & (freqs <= min(40, max(freqs)))
        if np.sum(valid_range) > 5:
            log_f = np.log(freqs[valid_range] + 1e-12)
            log_e = np.log(energies[valid_range] + 1e-30)
            slope, intercept = np.polyfit(log_f, log_e, 1)
        else:
            slope = np.nan
            intercept = np.nan

        # Écart au spectre naturel 1/f²
        natural_slope = -2.0
        spectral_error = abs(natural_slope - slope) if not np.isnan(slope) else np.nan

        return {
            'spectral_slope': float(slope) if not np.isnan(slope) else None,
            'natural_slope': natural_slope,
            'spectral_error': float(spectral_error) if not np.isnan(spectral_error) else None,
            'freqs': freqs.tolist(),
            'energies': energies.tolist(),
            'hf_energy_fraction': float(
                np.sum(fft_shifted[R > 20] ** 2) / (np.sum(fft_shifted ** 2) + 1e-12)
            ),
        }


# ==============================================================================
# COMPARAISON AVANT/APRÈS — Génération avec vs sans détails 1/f²
# ==============================================================================

def compare_with_without_details():
    """
    Comparaison visuelle et métrique :
      - Image générée SANS détails 1/f² (méthode actuelle)
      - Image générée AVEC détails 1/f² synthétisés (méthode améliorée)
    """
    print("=" * 80)
    print("  COMPARAISON : Sans vs Avec Détails 1/f²")
    print("  Diagnostic : Psi1 actuel = 7 sinusoides → spectre pauvre en HF")
    print("  Solution  : Synthese de residu spectral 1/f^2 + amplification H_n")
    print("=" * 80)

    out_dir = os.path.join(os.path.dirname(__file__), '..',
                           'av_generation_output', 'detail_synthesizer')
    os.makedirs(out_dir, exist_ok=True)

    synthesizer = HarmonicDetailSynthesizer(seed=42)

    # Test sur plusieurs tailles et forces
    configs = [
        (256, 256, 42, 1.0, 'cosmique'),
        (512, 512, 12345, 1.5, 'solaire'),
        (512, 512, 7777, 2.0, 'forest'),
    ]

    all_results = []

    for width, height, seed, strength, style in configs:
        print(f"\n  [{width}×{height}] seed={seed}, strength={strength}, style={style}")

        # Génération SANS détails (méthode actuelle)
        field = HarmonicField(width=width, height=height, seed=seed)
        psi_base = field.get_psi_total()
        base_img = (psi_base + 1) / 2
        base_rgb = HarmonicColorMapper.harmonic_hsl(psi_base, palette=style)

        # Génération AVEC détails 1/f²
        rgb_enhanced, enhanced_field, metrics = synthesizer.generate_full_image_with_details(
            width=width, height=height,
            base_seed=seed, detail_seed=seed + 1000,
            style=style, strength=strength,
        )

        # Analyse spectrale
        spectrum_base = synthesizer.analyze_spectrum(base_img)
        spectrum_enhanced = synthesizer.analyze_spectrum((enhanced_field + 1) / 2)

        # Sauvegarde
        from harmonic_image_generator import save_as_png
        base_path = os.path.join(out_dir, f'base_{width}x{height}_s{seed}_{style}.png')
        enh_path = os.path.join(out_dir, f'enhanced_{width}x{height}_s{seed}_{style}_str{int(strength*10)}.png')
        save_as_png(base_rgb, base_path)
        save_as_png(rgb_enhanced, enh_path)

        # Rapport
        m = metrics
        print(f"    Métriques :")
        print(f"      Acutance  : {m['base']['acutance']:.4f} → {m['enhanced']['acutance']:.4f} "
              f"(+{m['gain_acutance']:.0f}%)")
        print(f"      Laplacian Std : {m['base']['laplacian_std']:.4f} → {m['enhanced']['laplacian_std']:.4f} "
              f"(+{m['gain_lap_std']:.0f}%)")
        print(f"      Pente spectrale base : {spectrum_base['spectral_slope']:.2f} "
              f"(cible -2.0, erreur={spectrum_base['spectral_error']:.2f})")
        print(f"      Pente spectrale enh  : {spectrum_enhanced['spectral_slope']:.2f} "
              f"(cible -2.0, erreur={spectrum_enhanced['spectral_error']:.2f})")
        print(f"      HF fraction base : {spectrum_base['hf_energy_fraction']:.4f}")
        print(f"      HF fraction enh  : {spectrum_enhanced['hf_energy_fraction']:.4f}")

        all_results.append({
            'config': (width, height, seed, strength, style),
            'metrics': metrics,
            'spectrum_base': {k: v for k, v in spectrum_base.items() if k not in ('freqs', 'energies')},
            'spectrum_enhanced': {k: v for k, v in spectrum_enhanced.items() if k not in ('freqs', 'energies')},
        })

    # Rapport global
    print(f"\n{'='*80}")
    print("  RAPPORT GLOBAL")
    print(f"{'='*80}")

    avg_gain_acutance = np.mean([r['metrics']['gain_acutance'] for r in all_results])
    avg_gain_lap = np.mean([r['metrics']['gain_lap_std'] for r in all_results])
    avg_spectral_err_base = np.mean([r['spectrum_base']['spectral_error'] for r in all_results if r['spectrum_base']['spectral_error'] is not None])
    avg_spectral_err_enh = np.mean([r['spectrum_enhanced']['spectral_error'] for r in all_results if r['spectrum_enhanced']['spectral_error'] is not None])

    print(f"  Gain acutance moyen       : +{avg_gain_acutance:.0f}%")
    print(f"  Gain Laplacian std moyen   : +{avg_gain_lap:.0f}%")
    print(f"  Erreur spectrale base      : {avg_spectral_err_base:.2f} (écart à -2.0)")
    print(f"  Erreur spectrale enhanced  : {avg_spectral_err_enh:.2f} (écart à -2.0)")
    print(f"\n  Fichiers dans : {out_dir}")

    # Démo du résidu synthétisé
    print(f"\n  [DÉMO] Visualisation du résidu 1/f² synthétisé...")
    residue_comp = synthesizer.synthesize_residue(256, 256, base_seed=99)

    for name in ['full', 'edges', 'texture', 'grain']:
        viz = np.abs(residue_comp[name]) * 10
        viz = np.clip(viz, 0, 1)
        u8 = (viz * 255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3, axis=-1), 'RGB').save(
            os.path.join(out_dir, f'residue_synthesized_{name}.png'))

    print(f"    ✓ Résidu full, edges, texture, grain → {out_dir}/residue_synthesized_*.png")
    print(f"\n  ✅ Démonstration terminée.")
    print(f"  💡 Le résidu 1/f² synthétisé contient les HAUTES FRÉQUENCES")
    print(f"     que Ψ₁ actuel (7 sinusoïdes) ne produit pas.")
    print(f"     C'est CE résidu qui porte les détails (bords, textures, grain).")


# ==============================================================================
# INTÉGRATION AVEC LE PIPELINE EXISTANT
# ==============================================================================

def enhance_existing_pipeline(base_image: np.ndarray, strength: float = 1.0,
                               detail_seed: int = None) -> np.ndarray:
    """
    Fonction d'intégration simple pour le pipeline existant.

    Usage dans unified_superior_engine.py ou final_pipeline.py :
      from harmonic_detail_synthesizer import enhance_existing_pipeline
      enhanced = enhance_existing_pipeline(base_image, strength=1.0)
    """
    synthesizer = HarmonicDetailSynthesizer(seed=detail_seed or 42)
    return synthesizer.synthesize_and_apply(base_image, strength=strength)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Harmonic Detail Synthesizer — 1/f² Spectral')
    parser.add_argument('--demo', action='store_true', help='Démo comparative complète')
    parser.add_argument('--image', type=str, default=None, help='Image à enrichir')
    parser.add_argument('--strength', type=float, default=1.0, help='Force des détails')
    parser.add_argument('--output', type=str, default=None, help='Fichier de sortie')

    args = parser.parse_args()

    if args.image:
        img = np.array(Image.open(args.image).convert('L'), dtype=np.float64) / 255.0
        enhanced = enhance_existing_pipeline(img, strength=args.strength)
        out = args.output or args.image.replace('.', '_detailed.')
        rgb_out = np.stack([(np.clip(enhanced, 0, 1) * 255).astype(np.uint8)] * 3, axis=-1)
        Image.fromarray(rgb_out, 'RGB').save(out)
        print(f"Image enrichie : {out}")
    else:
        compare_with_without_details()