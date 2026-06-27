#!/usr/bin/env python3
# coding: utf-8
"""
TRAIN & BENCHMARK — Entraînement CNN + Comparaison finale
===========================================================
1. Entraîne le CNN guidance (45K params) sur le dataset 2964 images
2. Compare tous les sharpeners sur un ensemble de test
3. Génère un rapport de benchmark complet

Usage :
  python train_and_benchmark.py
"""

import numpy as np, math, sys, os, time, json, glob
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import (PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, H_CONSTANTS,
                                      HarmonicColorMapper, HarmonicField, normalize_field)
from holographic_one_shot import HolographicTrainer, HolographicGenerator
from harmonic_sharpener import HarmonicSharpener
from adaptive_sharpener import AdaptiveHarmonicSharpener
from harmonic_cnn_guidance import HarmonicGuidanceCNN, train_cnn_guidance


def benchmark_all_sharpeners(test_images, output_dir):
    """Compare tous les sharpeners sur un ensemble de test."""
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("  BENCHMARK COMPARATIF — Tous les Sharpeners")
    print("=" * 70)
    
    simple_sharp = HarmonicSharpener(K=16)
    adaptive_sharp = AdaptiveHarmonicSharpener(K=16)
    cnn_sharp = HarmonicGuidanceCNN()
    
    all_metrics = {
        'simple': {'acutance': [], 'lap_std': [], 'time_ms': []},
        'adaptive': {'acutance': [], 'lap_std': [], 'time_ms': []},
        'cnn': {'acutance': [], 'lap_std': [], 'time_ms': []},
    }
    
    for idx, img in enumerate(test_images):
        print(f"\n  Image {idx+1}/{len(test_images)} ({img.shape[1]}×{img.shape[0]})...")
        
        # Simple Sharpener
        t0 = time.time()
        simple = simple_sharp.sharpen(img, strength=1.0)
        t_simple = (time.time() - t0) * 1000
        m_simple = simple_sharp.analyze_sharpness(simple)
        
        # Adaptive Sharpener
        t0 = time.time()
        adaptive = adaptive_sharp.sharpen_adaptive(img, strength=1.0)
        t_adaptive = (time.time() - t0) * 1000
        m_adaptive = simple_sharp.analyze_sharpness(adaptive)
        
        # CNN Guidance
        t0 = time.time()
        cnn_result = cnn_sharp.apply_to_image(img)
        t_cnn = (time.time() - t0) * 1000
        m_cnn = simple_sharp.analyze_sharpness(cnn_result)
        
        # Accumuler
        for name, m, t in [('simple', m_simple, t_simple),
                            ('adaptive', m_adaptive, t_adaptive),
                            ('cnn', m_cnn, t_cnn)]:
            all_metrics[name]['acutance'].append(m['acutance'])
            all_metrics[name]['lap_std'].append(m['laplacian_std'])
            all_metrics[name]['time_ms'].append(t)
        
        print(f"    Simple:   acut={m_simple['acutance']:.4f} lap={m_simple['laplacian_std']:.4f} ({t_simple:.0f}ms)")
        print(f"    Adaptive: acut={m_adaptive['acutance']:.4f} lap={m_adaptive['laplacian_std']:.4f} ({t_adaptive:.0f}ms)")
        print(f"    CNN:      acut={m_cnn['acutance']:.4f} lap={m_cnn['laplacian_std']:.4f} ({t_cnn:.0f}ms)")
    
    # Rapport
    print(f"\n{'='*70}")
    print(f"  RAPPORT FINAL — Moyennes sur {len(test_images)} images")
    print(f"{'='*70}")
    
    orig_metrics = simple_sharp.analyze_sharpness(test_images[0]) if test_images else {}
    
    print(f"""
  | Sharpener      | Acutance moy | Laplacian Std moy | Temps moy (ms) |
  |----------------|-------------|-------------------|----------------|
  | Original       | {orig_metrics.get('acutance', 0):13.4f} | {orig_metrics.get('laplacian_std', 0):17.4f} | {'—':14s} |
  | Simple         | {np.mean(all_metrics['simple']['acutance']):13.4f} | {np.mean(all_metrics['simple']['lap_std']):17.4f} | {np.mean(all_metrics['simple']['time_ms']):14.0f} |
  | Adaptive (P1)  | {np.mean(all_metrics['adaptive']['acutance']):13.4f} | {np.mean(all_metrics['adaptive']['lap_std']):17.4f} | {np.mean(all_metrics['adaptive']['time_ms']):14.0f} |
  | CNN (P3)       | {np.mean(all_metrics['cnn']['acutance']):13.4f} | {np.mean(all_metrics['cnn']['lap_std']):17.4f} | {np.mean(all_metrics['cnn']['time_ms']):14.0f} |
""")
    
    # Sauvegarder rapport JSON
    report = {
        'n_images': len(test_images),
        'averages': {
            name: {
                'acutance': float(np.mean(vals['acutance'])),
                'laplacian_std': float(np.mean(vals['lap_std'])),
                'time_ms': float(np.mean(vals['time_ms'])),
            }
            for name, vals in all_metrics.items()
        }
    }
    with open(os.path.join(output_dir, 'benchmark_report.json'), 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n  Rapport JSON : {output_dir}/benchmark_report.json")
    
    return all_metrics


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  TRAIN & BENCHMARK — CNN Guidance + Comparaison Finale           ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    base_dir = os.path.join(os.path.dirname(__file__), '..',
                            'av_generation_output', 'train_benchmark')
    os.makedirs(base_dir, exist_ok=True)
    
    dataset_path = os.path.join(os.path.dirname(__file__), '..',
                                'av_generation_output', 'massive_dataset')
    
    # 1. Entraînement CNN
    if os.path.isdir(dataset_path):
        print("\n  [Étape 1/3] Entraînement CNN guidance...")
        cnn = HarmonicGuidanceCNN()
        train_cnn_guidance(cnn, dataset_path, n_epochs=15, lr=0.002)
    else:
        print(f"\n  ⚠️ Dataset non trouvé : {dataset_path}")
        print("  Utilisation du CNN avec poids initiaux.")
        cnn = HarmonicGuidanceCNN()
    
    # 2. Préparer images de test
    print("\n  [Étape 2/3] Préparation images de test...")
    test_images = []
    
    # Images générées variées
    for seed in [42, 137, 256, 512, 1024]:
        field = HarmonicField(width=256, height=256, seed=seed)
        psi = field.get_psi_total()
        H, W = psi.shape
        x = np.linspace(-1, 1, W)
        y = np.linspace(-1, 1, H)
        X, Y = np.meshgrid(x, y)
        R = np.sqrt(X**2 + Y**2)
        theta = np.arctan2(Y, X)
        psi += 0.2 * np.sin(X * 40 * SQRT5) * np.cos(Y * 40 * SQRT5)
        psi += 0.1 * np.sin(R * 30 + theta * 10)
        psi = normalize_field(psi)
        img = (psi + 1) / 2
        test_images.append(img)
    
    # Ajouter des vraies photos si dispo
    if os.path.isdir(dataset_path):
        real_files = sorted(glob.glob(os.path.join(dataset_path, '**', '*.jpg'), recursive=True))
        for f in real_files[:5]:
            img = np.array(Image.open(f).convert('L'), dtype=np.float64) / 255.0
            if img.shape[0] >= 128 and img.shape[1] >= 128:
                # Redimensionner pour cohérence
                img = np.array(Image.fromarray(
                    (img*255).astype(np.uint8)
                ).resize((256, 256), Image.LANCZOS), dtype=np.float64) / 255.0
                test_images.append(img)
    
    print(f"  {len(test_images)} images de test prêtes")
    
    # 3. Benchmark
    print("\n  [Étape 3/3] Benchmark comparatif...")
    results = benchmark_all_sharpeners(test_images, base_dir)
    
    # Sauvegarder des exemples visuels
    print("\n  Sauvegarde d'exemples visuels...")
    example_img = test_images[0]
    
    simple_sharp = HarmonicSharpener(K=16)
    adaptive_sharp = AdaptiveHarmonicSharpener(K=16)
    
    for name, arr in [
        ('original', example_img),
        ('simple', simple_sharp.sharpen(example_img, strength=1.0)),
        ('adaptive', adaptive_sharp.sharpen_adaptive(example_img, strength=1.0)),
        ('cnn', cnn.apply_to_image(example_img)),
    ]:
        u8 = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3, -1), 'RGB').save(
            os.path.join(base_dir, f'example_{name}.png'))
    
    print(f"\n  ✅ Benchmark terminé. Fichiers dans : {base_dir}/")
    for f in sorted(os.listdir(base_dir)):
        print(f"    {f}")


if __name__ == '__main__':
    main()