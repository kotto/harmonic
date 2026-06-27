#!/usr/bin/env python3
# coding: utf-8
"""
STEERABLE SHARPENER — Phase 4 IA Expert Recommendations
=========================================================
Remplace le cœur SVD par une approche multi-échelle orientable
avec DCT lapped + pyramide gaussienne + gain adaptatif spatial-fréquentiel.

Recommandations IA experte :
  1. 8×8 SVD → overlapping 8×8 DCT (lapped DCT)
  2. Ajouter décomposition multi-échelle (pyramide orientable)
  3. Gain scalaire Hₙ → champ de gain adaptatif :
       edge-aware
       variance-aware
       spectral-decay-aware
  4. CNN léger optionnel (prédit la carte de gain, pas les pixels)

Insight fondamental :
  Le gap vs Midjourney n'est PAS l'erreur de reconstruction (SVD est optimal)
  mais la MODÉLISATION DE LA DISTRIBUTION DES HAUTES FRÉQUENCES
  conditionnée par la sémantique.

Pipeline :
  1. Lapped DCT 8×8 avec fenêtre de Hann → coefficients fréquentiels locaux
  2. Pyramide gaussienne 3 niveaux → séparation échelles
  3. Par échelle et par bloc :
       - Edge map (gradient) → gain √5
       - Variance map → gain e
       - Spectral decay → modulation Hₙ
  4. Reconstruction par synthèse de pyramide inverse
  5. DCT inverse avec overlap-add

Usage :
  python steerable_sharpener.py --demo
  python steerable_sharpener.py --image photo.jpg
"""

import numpy as np, math, sys, os, time, argparse
from typing import Dict, Any, List, Tuple, Optional
from scipy.ndimage import gaussian_filter, sobel, laplace
from scipy.fftpack import dct, idct
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import (PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, H_CONSTANTS,
                                      HarmonicColorMapper, normalize_field)


# ==============================================================================
# LAPPED DCT 8×8 (remplace SVD)
# ==============================================================================

def create_hann_window(size: int) -> np.ndarray:
    """Fenêtre de Hann 2D (size × size)."""
    h = 0.5 * (1 - np.cos(2 * np.pi * np.arange(size) / (size - 1)))
    return np.outer(h, h)


def lapped_dct_decompose(image: np.ndarray, block_size: int = 8,
                          overlap: float = 0.5) -> Dict[str, Any]:
    """
    Décomposition DCT par blocs avec overlap (lapped DCT).
    
    Avantages vs SVD :
      - Base cosinus naturelle (JPEG-like, excellente pour images naturelles)
      - Overlap supprime les artefacts de bloc
      - Efficace en calcul (O(N log N) vs O(N³) pour SVD)
    
    Returns:
        dict avec 'reconstructed', 'coeffs_blocks', 'residue', 'freq_bands'
    """
    H, W = image.shape
    bs = block_size
    stride = int(bs * (1 - overlap))
    window = create_hann_window(bs)
    
    # Accumulateurs
    recon_accum = np.zeros((H, W), dtype=np.float64)
    weight_accum = np.zeros((H, W), dtype=np.float64)
    
    # Stocker tous les coefficients DCT
    all_coeffs = []
    freq_band_energy = {f'band_{i}': [] for i in range(3)}  # low, mid, high
    
    for y in range(0, H - bs + 1, stride):
        for x in range(0, W - bs + 1, stride):
            block = image[y:y+bs, x:x+bs]
            
            # Fenêtrage Hann
            block_windowed = block * window
            
            # DCT 2D (Type II, norm='ortho')
            coeffs = dct(dct(block_windowed.T, type=2, norm='ortho').T, 
                         type=2, norm='ortho')
            
            # Analyse fréquentielle par bande
            # Bande 1 (basse fréq) : coin supérieur gauche 2×2
            low_energy = np.sum(coeffs[:2, :2] ** 2)
            # Bande 2 (moyenne fréq) : reste du coin 4×4
            mid_energy = np.sum(coeffs[:4, :4] ** 2) - low_energy
            # Bande 3 (haute fréq) : tout le reste
            high_energy = np.sum(coeffs ** 2) - low_energy - mid_energy
            
            freq_band_energy['band_0'].append(low_energy)
            freq_band_energy['band_1'].append(mid_energy)
            freq_band_energy['band_2'].append(high_energy)
            
            # Quantification du nombre de coefficients significatifs (spectral decay)
            sorted_coeffs = np.sort(np.abs(coeffs.flatten()))[::-1]
            cumsum = np.cumsum(sorted_coeffs ** 2)
            total = cumsum[-1] + 1e-12
            
            # Trouver K pour 95% de l'énergie
            K_95 = np.searchsorted(cumsum, 0.95 * total) + 1
            # Trouver K pour 99% de l'énergie
            K_99 = np.searchsorted(cumsum, 0.99 * total) + 1
            
            all_coeffs.append({
                'coeffs': coeffs,
                'pos': (y, x),
                'K_95': int(K_95),
                'K_99': int(K_99),
                'spectral_decay': float(K_95 / (bs * bs)),  # ratio de compression
            })
            
            # Reconstruction (pour le résidu)
            block_recon = idct(idct(coeffs, type=2, norm='ortho').T,
                               type=2, norm='ortho')
            recon_accum[y:y+bs, x:x+bs] += block_recon * window
            weight_accum[y:y+bs, x:x+bs] += window
    
    weight_accum = np.maximum(weight_accum, 1e-12)
    reconstructed = recon_accum / weight_accum
    residue = image - reconstructed
    
    # Métriques
    mse = np.mean(residue ** 2)
    psnr = 10 * math.log10(1.0 / (mse + 1e-12)) if mse > 0 else 999
    
    return {
        'reconstructed': reconstructed,
        'residue': residue,
        'coeffs_blocks': all_coeffs,
        'freq_bands': freq_band_energy,
        'metrics': {
            'mse': float(mse),
            'psnr_db': float(psnr),
            'n_blocks': len(all_coeffs),
            'avg_K_95': float(np.mean([c['K_95'] for c in all_coeffs])),
            'avg_spectral_decay': float(np.mean([c['spectral_decay'] for c in all_coeffs])),
        },
    }


# ==============================================================================
# PYRAMIDE GAUSSIENNE MULTI-ÉCHELLE
# ==============================================================================

def gaussian_pyramid(image: np.ndarray, n_levels: int = 3) -> List[np.ndarray]:
    """
    Construit une pyramide gaussienne de l'image.
    
    Niveau 0 : image originale
    Niveau 1 : ½ résolution (lissée + sous-échantillonnée)
    Niveau 2 : ¼ résolution
    
    Returns:
        Liste de niveaux de la pyramide [level_0, level_1, level_2, ...]
    """
    pyramid = [image.copy()]
    current = image.copy()
    
    for level in range(1, n_levels):
        # Lissage gaussien (σ adapté à l'échelle)
        sigma = 1.0 * (2 ** (level - 1))
        blurred = gaussian_filter(current, sigma=sigma)
        
        # Sous-échantillonnage 2×
        h, w = blurred.shape
        current = blurred[::2, ::2]
        pyramid.append(current)
    
    return pyramid


def laplacian_pyramid(gaussian_pyr: List[np.ndarray]) -> List[np.ndarray]:
    """
    Construit une pyramide laplacienne à partir de la pyramide gaussienne.
    
    Chaque niveau = différence entre le niveau gaussien et sa version upscalée.
    """
    laplacian_pyr = []
    
    for i in range(len(gaussian_pyr) - 1):
        # Upscale du niveau i+1 au niveau i
        coarse = gaussian_pyr[i + 1]
        h, w = gaussian_pyr[i].shape
        
        # Upsample bilinéaire
        from PIL import Image as PILImage
        coarse_img = PILImage.fromarray((coarse * 255).astype(np.uint8))
        upscaled = np.array(coarse_img.resize((w, h), PILImage.LANCZOS), 
                           dtype=np.float64) / 255.0
        
        # Différence = détails à cette échelle
        detail = gaussian_pyr[i] - upscaled
        laplacian_pyr.append(detail)
    
    # Dernier niveau = image la plus grossière
    laplacian_pyr.append(gaussian_pyr[-1])
    
    return laplacian_pyr


# ==============================================================================
# GAIN ADAPTATIF SPATIAL-FRÉQUENTIEL
# ==============================================================================

class SpatialFreqGainField:
    """
    Champ de gain adaptatif spatial-fréquentiel.
    
    Remplace le gain scalaire Hₙ par une carte de gain par pixel
    qui dépend de :
      - edge_map : présence de bords (gradient)
      - variance_map : texture vs surface lisse
      - spectral_decay : compressibilité locale
    """
    
    @staticmethod
    def compute_edge_map(image: np.ndarray) -> np.ndarray:
        """Carte de bords (gradient normalisé)."""
        gy, gx = np.gradient(image)
        edge_map = np.sqrt(gx**2 + gy**2)
        return edge_map / (np.max(edge_map) + 1e-12)
    
    @staticmethod
    def compute_variance_map(image: np.ndarray, block_size: int = 8) -> np.ndarray:
        """Carte de variance locale."""
        H, W = image.shape
        var_map = np.zeros((H, W), dtype=np.float64)
        
        for y in range(0, H, block_size):
            for x in range(0, W, block_size):
                ye = min(y + block_size, H)
                xe = min(x + block_size, W)
                patch = image[y:ye, x:xe]
                var_map[y:ye, x:xe] = float(np.var(patch))
        
        return var_map / (np.max(var_map) + 1e-12)
    
    @staticmethod
    def compute_spectral_decay_map(coeffs_blocks: List[Dict], 
                                    H: int, W: int, block_size: int = 8) -> np.ndarray:
        """Carte de décroissance spectrale (compressibilité locale)."""
        decay_map = np.ones((H, W), dtype=np.float64)
        
        for block_info in coeffs_blocks:
            y, x = block_info['pos']
            bs = block_size
            # spectral_decay = K_95 / 64 : ratio de coefficients pour 95% énergie
            # Plus c'est petit, plus l'énergie est concentrée (basse fréquence dominante)
            decay = 1.0 - block_info['spectral_decay']  # 0 = très compressible, 1 = non compressible
            decay_map[y:y+bs, x:x+bs] = max(0.01, decay)
        
        return np.clip(decay_map, 0, 1)
    
    @classmethod
    def compute_adaptive_gain(cls, image: np.ndarray, 
                               residue: np.ndarray,
                               coeffs_blocks: List[Dict],
                               strength: float = 1.0) -> np.ndarray:
        """
        Calcule le gain adaptatif complet par pixel.
        
        Gain = base + 
               edge_map × √5 × strength      (bords = netteté)
               + variance_map × e × 0.5      (textures = détails)
               + (1-decay_map) × π × 0.3      (zones compressibles = structure)
               - edge_map × e × 0.2          (anti-ringing sur bords forts)
        """
        H, W = image.shape
        
        # Cartes
        edge_map = cls.compute_edge_map(image)
        var_map = cls.compute_variance_map(image, block_size=8)
        decay_map = cls.compute_spectral_decay_map(coeffs_blocks, H, W, block_size=8)
        
        # Gain de base
        gain = np.ones((H, W), dtype=np.float64)
        
        # H₆ (√5) : amplification sur les bords
        edge_gain = edge_map * SQRT5 * 0.8 * strength
        
        # H₃ (e) : amplification sur les zones texturées
        texture_gain = var_map * E * 0.5 * strength
        
        # H₂ (π) : renforcement périodique dans les zones structurées (non compressibles)
        structure_gain = (1.0 - decay_map) * PI * 0.3 * strength
        
        # H₃ (e) : anti-ringing sur les bords forts
        anti_ringing = edge_map * E * 0.25 * strength
        anti_ringing = np.clip(anti_ringing, 0, 0.5)
        
        gain = 1.0 + edge_gain + texture_gain + structure_gain
        gain = gain * (1.0 - anti_ringing)
        
        return np.clip(gain, 0.5, 3.0)


# ==============================================================================
# STEERABLE SHARPENER (DCT + Pyramide + Gain Adaptatif)
# ==============================================================================

class SteerableSharpener:
    """
    Sharpener orientable multi-échelle avec DCT lapped + gain adaptatif.
    
    Implémente les recommandations IA experte Phase 4.
    """
    
    def __init__(self, block_size: int = 8, overlap: float = 0.5,
                  n_pyramid_levels: int = 3):
        self.block_size = block_size
        self.overlap = overlap
        self.n_pyramid_levels = n_pyramid_levels
    
    def sharpen(self, image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """
        Sharpening steerable complet.
        
        Pipeline :
          1. Pyramide gaussienne → 3 niveaux d'échelle
          2. Pour chaque niveau : lapped DCT + gain adaptatif
          3. Reconstruction par pyramide inverse
        """
        H, W = image.shape
        
        # 1. Pyramide gaussienne
        print(f"    Construction pyramide gaussienne ({self.n_pyramid_levels} niveaux)...")
        gaussian_pyr = gaussian_pyramid(image, self.n_pyramid_levels)
        
        # 2. Traiter chaque niveau de la pyramide
        enhanced_pyr = []
        
        for level, level_img in enumerate(gaussian_pyr):
            # Ajuster la force selon le niveau (plus fort sur détails fins)
            level_strength = strength * (1.0 + level * 0.3)
            
            # Lapped DCT
            decomp = lapped_dct_decompose(level_img, 
                                           block_size=self.block_size,
                                           overlap=self.overlap)
            
            # Gain adaptatif spatial-fréquentiel
            gain_map = SpatialFreqGainField.compute_adaptive_gain(
                level_img, decomp['residue'], decomp['coeffs_blocks'],
                strength=level_strength
            )
            
            # Appliquer le gain au résidu
            residue_enhanced = decomp['residue'] * gain_map * (0.5 + level * 0.25)
            
            # Reconstruction
            enhanced = decomp['reconstructed'] + residue_enhanced
            enhanced = np.clip(enhanced, 0, 1)
            
            enhanced_pyr.append(enhanced)
        
        # 3. Reconstruction par pyramide inverse
        result = self._reconstruct_from_pyramid(enhanced_pyr, H, W)
        
        return np.clip(result, 0, 1)
    
    def _reconstruct_from_pyramid(self, enhanced_pyr: List[np.ndarray],
                                    target_h: int, target_w: int) -> np.ndarray:
        """
        Reconstruit une image à partir d'une pyramide améliorée.
        
        Combine les niveaux par addition pondérée après upscale.
        """
        # Commencer par le niveau le plus grossier et upscaler progressivement
        result = enhanced_pyr[-1]  # Niveau le plus grossier
        
        for level in range(len(enhanced_pyr) - 2, -1, -1):
            h, w = enhanced_pyr[level].shape
            
            # Upscale au niveau supérieur
            from PIL import Image as PILImage
            result_img = PILImage.fromarray((result * 255).astype(np.uint8))
            result_upscaled = np.array(result_img.resize((w, h), PILImage.LANCZOS),
                                       dtype=np.float64) / 255.0
            
            # Ajouter les détails de ce niveau
            # Poids plus important pour les niveaux fins (plus de détails)
            weight = 0.5 + level * 0.15
            result = result_upscaled * (1 - weight) + enhanced_pyr[level] * weight
        
        # S'assurer que la taille finale correspond
        if result.shape[0] != target_h or result.shape[1] != target_w:
            from PIL import Image as PILImage
            result_img = PILImage.fromarray((result * 255).astype(np.uint8))
            result = np.array(result_img.resize((target_w, target_h), PILImage.LANCZOS),
                             dtype=np.float64) / 255.0
        
        return result
    
    def analyze_sharpness(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse de netteté (compatible avec les autres sharpeners)."""
        from harmonic_sharpener import HarmonicSharpener
        return HarmonicSharpener(K=16).analyze_sharpness(image)


# ==============================================================================
# DÉMO
# ==============================================================================

def demo_steerable():
    print("═" * 70)
    print("  STEERABLE SHARPENER — Phase 4 IA Expert")
    print("  Lapped DCT + Pyramide Gaussienne + Gain Adaptatif")
    print("═" * 70)
    
    out_dir = os.path.join(os.path.dirname(__file__), '..',
                           'av_generation_output', 'steerable')
    os.makedirs(out_dir, exist_ok=True)
    
    # Image test
    from harmonic_generator_core import HarmonicField, HarmonicColorMapper
    from harmonic_image_generator import save_as_png
    
    print("\n  [1] Création image test...")
    field = HarmonicField(width=256, height=256, seed=42)
    psi = field.get_psi_total()
    H, W = psi.shape
    x = np.linspace(-1, 1, W)
    y = np.linspace(-1, 1, H)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    psi += 0.25 * np.sin(X*50*SQRT5) * np.cos(Y*50*SQRT5)
    psi += 0.15 * np.sin(R*40 + theta*12)
    psi += 0.10 * np.cos(X*30) * np.cos(Y*20)
    psi = normalize_field(psi)
    
    image = (psi + 1) / 2
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    save_as_png(rgb, os.path.join(out_dir, '01_original.png'))
    
    # Test Steerable Sharpener
    print("\n  [2] Steerable Sharpener (DCT + Pyramide + Gain Adaptatif)...")
    steerable = SteerableSharpener(block_size=8, overlap=0.5, n_pyramid_levels=3)
    
    t0 = time.time()
    sharp = steerable.sharpen(image, strength=1.0)
    time_steerable = (time.time() - t0) * 1000
    
    # Métriques
    m_orig = steerable.analyze_sharpness(image)
    m_sharp = steerable.analyze_sharpness(sharp)
    
    print(f"""
  📊 Métriques Steerable Sharpener

  | Version              | Acutance | Laplacian Std | HF Ratio |
  |----------------------|----------|---------------|----------|
  | Original             | {m_orig['acutance']:8.4f} | {m_orig['laplacian_std']:13.4f} | {m_orig['hf_ratio']:8.4f} |
  | Steerable Sharp      | {m_sharp['acutance']:8.4f} | {m_sharp['laplacian_std']:13.4f} | {m_sharp['hf_ratio']:8.4f} |

  Gain vs Original :
    Acutance : {(m_sharp['acutance']/max(1e-12,m_orig['acutance'])-1)*100:+.0f}%
    Laplacian Std : {(m_sharp['laplacian_std']/max(1e-12,m_orig['laplacian_std'])-1)*100:+.0f}%

  Temps : {time_steerable:.0f}ms
""")
    
    # Sauvegarder
    u8 = (np.clip(sharp, 0, 1)*255).astype(np.uint8)
    Image.fromarray(np.stack([u8]*3, -1), 'RGB').save(
        os.path.join(out_dir, '02_steerable_sharp.png'))
    
    print(f"\n  ✅ Fichiers dans : {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        print(f"    {f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Steerable Sharpener')
    parser.add_argument('--demo', action='store_true', help='Démo')
    parser.add_argument('--image', type=str, default=None, help='Image')
    args = parser.parse_args()
    
    if args.image:
        img = np.array(Image.open(args.image).convert('L'), dtype=np.float64) / 255.0
        steerable = SteerableSharpener(block_size=8, overlap=0.5, n_pyramid_levels=3)
        sharp = steerable.sharpen(img, strength=1.0)
        out = args.image.replace('.', '_steerable.')
        u8 = (np.clip(sharp,0,1)*255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3,-1),'RGB').save(out)
        print(f"Image: {out}")
    else:
        demo_steerable()