#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUALITY BENCHMARK — Métrique Q_HF sur corpus et images générées
==================================================================
Mesure la qualité haute fréquence (Q_HF) selon le cadre ondulatoire :

Q_HF = Q_pente × Q_bords × Q_textures × Q_grain

Où :
  Q_pente    = exp(-|pente_réelle − (−2.0)|)     → décroissance 1/f²
  Q_bords    = energy_bande[0.10-0.45] / cible_naturelle
  Q_textures = energy_bande[0.15-0.35] / cible_naturelle
  Q_grain    = energy_bande[0.30-0.45] / cible_naturelle

Cibles naturelles (mesurées sur photos réelles) :
  - Pente spectrale : -2.0
  - Énergie bords : 8-15% de l'énergie totale
  - Énergie textures : 15-25%
  - Énergie grain : 3-8%

Usage :
  python quality_benchmark.py --corpus   # Mesurer Q_HF sur le corpus
  python quality_benchmark.py --demo     # Benchmark complet avec/sans correction
"""

import sys, os, numpy as np, math, time, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image
from scipy.ndimage import laplace as lap_func, gaussian_filter
from harmonic_generator_core import HarmonicField, HarmonicColorMapper, normalize_field, H_CONSTANTS, PHI, PI, SQRT5, E_PI
from harmonic_detail_synthesizer import HarmonicDetailSynthesizer, enhance_existing_pipeline
from harmonic_image_generator import save_as_png


# ==============================================================================
# FONCTIONS DE MESURE Q_HF
# ==============================================================================

def measure_spectral_slope(image: np.ndarray) -> float:
    """Mesure la pente spectrale radiale (doit être proche de -2.0 pour 1/f²)."""
    h, w = image.shape
    fft = np.abs(np.fft.fft2(image))
    fft_s = np.fft.fftshift(fft)
    Y, X = np.ogrid[:h, :w]
    cy, cx = h//2, w//2
    R = np.sqrt((Y-cy)**2 + (X-cx)**2).astype(int)
    
    rad_e = np.bincount(R.flatten(), weights=fft_s.flatten()**2)
    rad_c = np.bincount(R.flatten())
    valid = rad_c > 0
    f = np.arange(len(rad_e))[valid]
    e = rad_e[valid] / rad_c[valid]
    
    vr = (f >= 1) & (f <= min(h//6, w//6, max(f)))
    if np.sum(vr) > 5:
        log_f = np.log(f[vr] + 1e-12)
        log_e = np.log(e[vr] + 1e-30)
        slope, _ = np.polyfit(log_f, log_e, 1)
        return float(slope)
    return np.nan


def measure_band_energy(image: np.ndarray, f_min: float, f_max: float) -> float:
    """Mesure l'énergie dans une bande de fréquences normalisées [0, 0.5]."""
    h, w = image.shape
    fft = np.abs(np.fft.fft2(image))
    fft_s = np.fft.fftshift(fft)
    Y, X = np.ogrid[:h, :w]
    cy, cx = h//2, w//2
    f_radius = np.sqrt(((Y-cy)/cy)**2 + ((X-cx)/cx)**2)  # Normalisé [0, √2]
    
    band_mask = (f_radius >= f_min) & (f_radius <= f_max)
    energy_band = np.sum(fft_s[band_mask] ** 2)
    energy_total = np.sum(fft_s ** 2) + 1e-12
    return float(energy_band / energy_total)


def compute_lap_std(image: np.ndarray) -> float:
    """Écart-type du Laplacien (proxy de densité de bords)."""
    return float(np.std(lap_func(image)))


def compute_q_hf(image: np.ndarray) -> dict:
    """
    Calcule Q_HF complet pour une image.
    
    Returns:
        dict avec Q_pente, Q_bords, Q_textures, Q_grain, Q_HF (moyenne géométrique)
    """
    # Pente spectrale
    slope = measure_spectral_slope(image)
    q_pente = math.exp(-abs(slope - (-2.0))) if not np.isnan(slope) else 0.0
    
    # Énergie par bande
    e_edges = measure_band_energy(image, 0.10, 0.45)     # Bande bords
    e_textures = measure_band_energy(image, 0.15, 0.35)   # Bande textures
    e_grain = measure_band_energy(image, 0.30, 0.45)      # Bande grain
    
    # Cibles naturelles (médianes mesurées sur photos réelles)
    TARGET_EDGES = 0.10      # 10% énergie dans la bande bords
    TARGET_TEXTURES = 0.18   # 18% énergie bande textures
    TARGET_GRAIN = 0.04      # 4% énergie bande grain
    
    # Q par bande : rapport à la cible, saturé à 1.0
    q_edges = min(1.0, e_edges / TARGET_EDGES)
    q_textures = min(1.0, e_textures / TARGET_TEXTURES)
    q_grain = min(1.0, e_grain / TARGET_GRAIN)
    
    # Q_HF = moyenne géométrique des 4 composantes
    values = [q_pente, q_edges, q_textures, q_grain]
    values = [max(0.001, v) for v in values]  # Éviter zéro
    q_hf = math.exp(sum(math.log(v) for v in values) / 4)
    
    # Proxy de densité de bords
    lap_std = compute_lap_std(image)
    
    return {
        'slope': round(slope, 3) if not np.isnan(slope) else None,
        'q_pente': round(q_pente, 4),
        'e_edges': round(e_edges, 6),
        'q_edges': round(q_edges, 4),
        'e_textures': round(e_textures, 6),
        'q_textures': round(q_textures, 4),
        'e_grain': round(e_grain, 6),
        'q_grain': round(q_grain, 4),
        'q_hf': round(q_hf, 4),
        'lap_std': round(lap_std, 6),
    }


# ==============================================================================
# BENCHMARK CORPUS
# ==============================================================================

def benchmark_corpus(dataset_dir: str = None, max_images: int = 100):
    """Mesure Q_HF sur le corpus d'images réelles (référence)."""
    if dataset_dir is None:
        dataset_dirs = [
            os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'unified', 'dataset'),
            os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'massive_dataset'),
        ]
        for d in dataset_dirs:
            if os.path.isdir(d):
                dataset_dir = d
                break
    
    if not dataset_dir:
        print("Aucun dataset trouvé.")
        return None
    
    all_files = sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpg'), recursive=True))
    all_files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpeg'), recursive=True))
    all_files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.png'), recursive=True))
    
    n = min(len(all_files), max_images)
    print(f"Analyse Q_HF sur {n} photos du corpus...")
    
    results = []
    for i, fpath in enumerate(all_files[:n]):
        try:
            img = np.array(Image.open(fpath).convert('L'), dtype=np.float64) / 255.0
            # Limiter taille
            h, w = img.shape
            if min(h, w) > 256:
                scale = 256.0 / max(h, w)
                nh, nw = int(h*scale), int(w*scale)
                img = np.array(Image.fromarray((img*255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS), dtype=np.float64) / 255.0
            
            q = compute_q_hf(img)
            results.append(q)
            if (i+1) % 25 == 0:
                print(f"  {i+1}/{n}...")
        except:
            continue
    
    if not results:
        return None
    
    # Agrégation
    q_hf_vals = [r['q_hf'] for r in results]
    q_pente_vals = [r['q_pente'] for r in results]
    slopes = [r['slope'] for r in results if r['slope'] is not None]
    e_edges_vals = [r['e_edges'] for r in results]
    e_textures_vals = [r['e_textures'] for r in results]
    e_grain_vals = [r['e_grain'] for r in results]
    lap_vals = [r['lap_std'] for r in results]
    
    stats = {
        'n_images': len(results),
        'q_hf': {
            'mean': round(np.mean(q_hf_vals), 4),
            'median': round(np.median(q_hf_vals), 4),
            'std': round(np.std(q_hf_vals), 4),
            'p10': round(np.percentile(q_hf_vals, 10), 4),
            'p90': round(np.percentile(q_hf_vals, 90), 4),
        },
        'slope': {
            'mean': round(np.mean(slopes), 2),
            'std': round(np.std(slopes), 2),
        },
        'energy_edges': round(np.mean(e_edges_vals), 6),
        'energy_textures': round(np.mean(e_textures_vals), 6),
        'energy_grain': round(np.mean(e_grain_vals), 6),
        'lap_std': round(np.mean(lap_vals), 6),
    }
    
    print(f"\n{'='*60}")
    print("  RÉFÉRENCE CORPUS — Q_HF sur photos réelles")
    print(f"{'='*60}")
    print(f"  Images analysées : {stats['n_images']}")
    print(f"  Q_HF moyen   : {stats['q_hf']['mean']:.4f} (médiane {stats['q_hf']['median']:.4f})")
    print(f"  Q_HF [P10-P90] : [{stats['q_hf']['p10']:.4f} — {stats['q_hf']['p90']:.4f}]")
    print(f"  Pente moyenne : {stats['slope']['mean']:.2f} ± {stats['slope']['std']:.2f}")
    print(f"  Énergie bords (0.10-0.45) : {stats['energy_edges']:.4f}")
    print(f"  Énergie textures (0.15-0.35) : {stats['energy_textures']:.4f}")
    print(f"  Énergie grain (0.30-0.45) : {stats['energy_grain']:.4f}")
    print(f"  LapStd moyen : {stats['lap_std']:.4f}")
    
    return stats


# ==============================================================================
# CORRECTION HF DANS LE DETAIL SYNTHESIZER
# ==============================================================================

def enhance_with_hf_boost(base_image: np.ndarray, strength: float = 1.0,
                           detail_seed: int = None) -> np.ndarray:
    """
    Version améliorée de enhance_existing_pipeline avec :
    - Injection ciblée par bande spectrale (×3 bords, ×4 textures, ×2 grain)
    - Conditionnement spatial du gain (edge-aware, variance-aware)
    - Anti-ringing adaptatif
    """
    H, W = base_image.shape
    import random
    rng = np.random.RandomState(detail_seed if detail_seed else 42)
    
    # 1. Générer bruit 1/f² full band
    fy = np.fft.fftfreq(H).reshape(-1, 1)
    fx = np.fft.fftfreq(W).reshape(1, -1)
    f_radius = np.sqrt(fx**2 + fy**2)
    f_radius = np.maximum(f_radius, 1.0 / max(H, W))
    
    noise_real = rng.randn(H, W)
    noise_imag = rng.randn(H, W)
    noise_fft = noise_real + 1j * noise_imag
    spectral_filter = 1.0 / (f_radius ** 1.0)
    spectral_filter = np.minimum(spectral_filter, 100.0)
    
    # Diviser en 3 bandes avec gains différenciés
    # Bande bords [0.10-0.45] : gain ×3
    band_edges = ((f_radius >= 0.10) & (f_radius <= 0.45)).astype(np.float64)
    # Bande textures [0.15-0.35] : gain ×4
    band_textures = ((f_radius >= 0.15) & (f_radius <= 0.35)).astype(np.float64)
    # Bande grain [0.30-0.45] : gain ×2
    band_grain = ((f_radius >= 0.30) & (f_radius <= 0.45)).astype(np.float64)
    
    # Gain par bande
    gain_edges = 3.0 * strength
    gain_textures = 4.0 * strength
    gain_grain = 2.0 * strength
    
    # Appliquer les gains dans l'espace de Fourier
    boosted_filter = spectral_filter.copy()
    boosted_filter += spectral_filter * band_edges * (gain_edges - 1.0)
    boosted_filter += spectral_filter * band_textures * (gain_textures - 1.0) * 0.5  # Éviter doublon avec edges
    boosted_filter += spectral_filter * band_grain * (gain_grain - 1.0) * 0.3
    
    filtered_fft = noise_fft * boosted_filter
    residue = np.fft.ifft2(filtered_fft).real
    
    # Normaliser le résidu
    r_max = np.max(np.abs(residue))
    if r_max > 1e-12:
        residue = residue / r_max
    
    # 2. Conditionnement spatial du gain
    # Edge map
    gy, gx = np.gradient(base_image)
    edge_map = np.sqrt(gx**2 + gy**2)
    edge_map = edge_map / (np.max(edge_map) + 1e-12)
    
    # Variance locale
    var_map = np.zeros_like(base_image)
    bs = 16
    for y in range(0, H, bs):
        for x in range(0, W, bs):
            ye, xe = min(y+bs, H), min(x+bs, W)
            var_map[y:ye, x:xe] = np.var(base_image[y:ye, x:xe])
    var_map = var_map / (np.max(var_map) + 1e-12)
    
    # Carte de gain spatiale
    spatial_gain = np.ones_like(base_image)
    # Bords : gain √5 dans zones de fort gradient
    spatial_gain += edge_map * (SQRT5 - 1) * 1.5 * strength
    # Textures : gain e dans zones de variance moyenne
    spatial_gain += var_map * (math.e - 1) * 0.8 * strength
    # Anti-ringing : atténuer près des bords très forts
    damping = 1.0 - edge_map * 0.5 * strength
    damping = np.clip(damping, 0.3, 1.0)
    spatial_gain *= damping
    spatial_gain = np.clip(spatial_gain, 0.5, 4.0)
    
    # 3. Appliquer le résidu avec gain spatial
    base_std = np.std(base_image)
    residue_std = np.std(residue)
    if residue_std > 1e-12:
        target_std = base_std * 0.12 * strength  # 12% amplitude (plus agressif)
        residue = residue * (target_std / residue_std)
    
    enhanced = base_image + residue * spatial_gain * 0.7
    
    # Clipping sigmoïde
    enhanced = np.clip(enhanced, -0.05, 1.05)
    enhanced = 1.0 / (1.0 + np.exp(-(enhanced - 0.5) * 12))
    
    return enhanced


# ==============================================================================
# BENCHMARK COMPLET : AVANT/APRÈS CORRECTION HF
# ==============================================================================

def benchmark_hf_improvement():
    """Compare Q_HF avant et après correction HF."""
    print("=" * 80)
    print("  BENCHMARK Q_HF — Avant vs Après Correction HF")
    print("=" * 80)
    
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'quality_benchmark')
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Mesurer la référence sur le corpus
    corpus_stats = benchmark_corpus(max_images=100)
    if corpus_stats:
        q_hf_ref = corpus_stats['q_hf']['median']
        print(f"\n  → Q_HF référence (corpus photos réelles) : {q_hf_ref:.4f}")
    else:
        q_hf_ref = 0.5  # Fallback
        print(f"\n  → Q_HF référence (estimé) : {q_hf_ref:.4f}")
    
    # 2. Générer des images de test (méthode actuelle vs corrigée)
    configs = [
        (256, 256, 42, 'cosmique'),
        (256, 256, 12345, 'solaire'),
        (512, 512, 7777, 'forest'),
        (512, 512, 99999, 'aurore'),
        (256, 256, 11111, 'galactique'),
    ]
    
    results = {'base': [], 'old_detail': [], 'new_hf_boost': []}
    
    for width, height, seed, style in configs:
        # --- Image de base (Ψ seul, sans détails) ---
        field = HarmonicField(width=width, height=height, seed=seed)
        psi = field.get_psi_total()
        base_img = (psi + 1) / 2
        q_base = compute_q_hf(base_img)
        results['base'].append(q_base['q_hf'])
        
        # --- Ancien detail synthesizer ---
        old_detail = enhance_existing_pipeline(base_img, strength=1.0, detail_seed=seed+1000)
        q_old = compute_q_hf(old_detail)
        results['old_detail'].append(q_old['q_hf'])
        
        # --- Nouveau HF boost ---
        new_detail = enhance_with_hf_boost(base_img, strength=1.0, detail_seed=seed+1000)
        q_new = compute_q_hf(new_detail)
        results['new_hf_boost'].append(q_new['q_hf'])
        
        # Sauver les images
        base_rgb = HarmonicColorMapper.harmonic_hsl(psi, palette=style)
        save_as_png(base_rgb, os.path.join(out_dir, f'base_{width}x{height}_s{seed}_{style}.png'))
        
        old_field = old_detail * 2 - 1
        old_rgb = HarmonicColorMapper.harmonic_hsl(old_field, palette=style)
        save_as_png(old_rgb, os.path.join(out_dir, f'old_detail_{width}x{height}_s{seed}_{style}.png'))
        
        new_field = new_detail * 2 - 1
        new_rgb = HarmonicColorMapper.harmonic_hsl(new_field, palette=style)
        save_as_png(new_rgb, os.path.join(out_dir, f'new_hf_{width}x{height}_s{seed}_{style}.png'))
    
    # 3. Rapport
    print(f"\n{'='*80}")
    print("  RÉSULTATS — Q_HF AVANT / APRÈS CORRECTION")
    print(f"{'='*80}")
    
    for label, vals in [('Base (Ψ seul)', results['base']),
                          ('Ancien Detail Synth', results['old_detail']),
                          ('Nouveau HF Boost', results['new_hf_boost'])]:
        m = np.mean(vals)
        print(f"  {label:<25s} : Q_HF = {m:.4f} | vs réf {q_hf_ref:.4f} = {m/q_hf_ref*100:.0f}%")
    
    gain_vs_base = np.mean(results['new_hf_boost']) / max(1e-12, np.mean(results['base']))
    gain_vs_old = np.mean(results['new_hf_boost']) / max(1e-12, np.mean(results['old_detail']))
    
    print(f"\n  Gain HF Boost vs Base      : ×{gain_vs_base:.1f}")
    print(f"  Gain HF Boost vs Old Detail : ×{gain_vs_old:.1f}")
    
    # 4. Analyse détaillée d'un exemple
    print(f"\n{'='*80}")
    print("  ANALYSE DÉTAILLÉE — Exemple 512×512 forest")
    print(f"{'='*80}")
    
    field = HarmonicField(width=512, height=512, seed=7777)
    psi = field.get_psi_total()
    base = (psi + 1) / 2
    old_d = enhance_existing_pipeline(base, strength=1.0, detail_seed=8777)
    new_d = enhance_with_hf_boost(base, strength=1.0, detail_seed=8777)
    
    for label, img in [('Base', base), ('Old Detail', old_d), ('New HF Boost', new_d)]:
        q = compute_q_hf(img)
        print(f"\n  {label}:")
        print(f"    Q_HF       = {q['q_hf']:.4f}")
        print(f"    Q_pente    = {q['q_pente']:.4f}  (pente = {q['slope']})")
        print(f"    Q_bords    = {q['q_edges']:.4f}  (énergie = {q['e_edges']:.6f})")
        print(f"    Q_textures = {q['q_textures']:.4f}  (énergie = {q['e_textures']:.6f})")
        print(f"    Q_grain    = {q['q_grain']:.4f}  (énergie = {q['e_grain']:.6f})")
        print(f"    LapStd     = {q['lap_std']:.6f}")
    
    print(f"\n  Fichiers dans : {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        print(f"    {f}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Quality Benchmark — Q_HF métrique')
    parser.add_argument('--corpus', action='store_true', help='Benchmark Q_HF sur le corpus uniquement')
    parser.add_argument('--demo', action='store_true', help='Benchmark complet avant/après correction')
    parser.add_argument('--n-images', type=int, default=100, help='Nombre d\'images du corpus à analyser')
    
    args = parser.parse_args()
    
    if args.corpus:
        benchmark_corpus(max_images=args.n_images)
    else:
        benchmark_hf_improvement()