#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test complet des modules de compression HCS
Verification des metriques et validation des performances
"""

import sys
import os
import numpy as np
import time
import json
from datetime import datetime

# Configurer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("TEST COMPLET DES MODULES DE COMPRESSION HCS")
print("=" * 70)
print()

# ============================================================================
# TEST 1: K-FACTOR ENGINE
# ============================================================================
print("TEST 1: K-FACTOR ENGINE")
print("-" * 70)

try:
    from core.k_factor_engine import KFactorEngine
    
    k_engine = KFactorEngine(k_factor=0.02)
    print(f"[OK] K-Factor Engine initialise: K=0.02 -> Ratio garanti: 50:1")
    
    # Test sur differentes tailles d'images
    test_sizes = [
        (240, 320, "QVGA"),
        (480, 640, "VGA"),
        (720, 1280, "HD"),
        (1080, 1920, "Full HD")
    ]
    
    k_results = []
    for height, width, name in test_sizes:
        test_image = np.random.rand(height, width, 3).astype(np.float32)
        compressed, metadata = k_engine.compress_image(test_image)
        
        k_results.append({
            'resolution': name,
            'original_size': int(metadata['original_size']),
            'compressed_size': int(metadata['compressed_size']),
            'ratio': float(metadata['actual_ratio']),
            'guarantee_met': bool(metadata['guarantee_met']),
            'time': float(metadata['processing_time'])
        })
        
        status = "[OK]" if metadata['guarantee_met'] else "[FAIL]"
        print(f"   {status} {name} ({width}x{height}): "
              f"Ratio={metadata['actual_ratio']:.1f}:1, "
              f"Temps={metadata['processing_time']:.3f}s")
    
    # Validation globale
    all_guarantees_met = all(r['guarantee_met'] for r in k_results)
    avg_ratio = np.mean([r['ratio'] for r in k_results])
    avg_time = np.mean([r['time'] for r in k_results])
    
    print(f"\nRESULTATS K-FACTOR:")
    print(f"   Ratio moyen: {avg_ratio:.1f}:1")
    print(f"   Temps moyen: {avg_time:.3f}s")
    print(f"   Garantie respectee: {'[OK] OUI' if all_guarantees_met else '[FAIL] NON'}")
    
    k_factor_valid = all_guarantees_met
    
except Exception as e:
    print(f"[ERROR] K-Factor Engine: {e}")
    import traceback
    traceback.print_exc()
    k_factor_valid = False
    k_results = []

print()

# ============================================================================
# TEST 2: WEBP OPTIMIZER
# ============================================================================
print("TEST 2: WEBP OPTIMIZER")
print("-" * 70)

try:
    from core.webp_optimizer import WebPOptimizer
    
    webp_optimizer = WebPOptimizer(quality=95, method=6)
    print(f"[OK] WebP Optimizer initialise: Qualite=95, Methode=6")
    
    # Test sur differents types de contenu
    content_types = [
        ("Simple/Uniforme", np.ones((480, 640, 3)) * 0.5),
        ("Aleatoire", np.random.rand(480, 640, 3)),
        ("Clair", np.random.rand(480, 640, 3) * 0.3 + 0.7),
        ("Fonce", np.random.rand(480, 640, 3) * 0.3),
        ("Texture", np.random.rand(480, 640, 3) * 0.5 + np.sin(np.linspace(0, 10, 640))[:, None, None])
    ]
    
    webp_results = []
    for name, image in content_types:
        image_uint8 = (image * 255).astype(np.uint8)
        webp_data, metadata = webp_optimizer.optimize_image(image_uint8)
        
        webp_results.append({
            'content_type': name,
            'ratio': float(metadata['compression_ratio']),
            'space_saved': float(metadata['space_saved_percent']),
            'content_analysis': str(metadata['content_analysis']['content_type']),
            'expected_ratio': float(metadata['content_analysis']['expected_webp_ratio']),
            'time': float(metadata['processing_time'])
        })
        
        print(f"   [OK] {name}: Ratio={metadata['compression_ratio']:.1f}:1, "
              f"Contenu={metadata['content_analysis']['content_type']}, "
              f"Niveau={metadata['optimization_level']}")
    
    # Statistiques WebP
    avg_webp_ratio = np.mean([r['ratio'] for r in webp_results])
    avg_webp_time = np.mean([r['time'] for r in webp_results])
    
    print(f"\nRESULTATS WEBP:")
    print(f"   Ratio moyen: {avg_webp_ratio:.1f}:1")
    print(f"   Temps moyen: {avg_webp_time:.3f}s")
    print(f"   Performance: {'[OK] EXCELLENTE' if avg_webp_ratio > 20 else '[WARN] MODEREE'}")
    
    webp_valid = avg_webp_ratio > 10  # Au moins 10:1
    
except Exception as e:
    print(f"[ERROR] WebP Optimizer: {e}")
    import traceback
    traceback.print_exc()
    webp_valid = False
    webp_results = []

print()

# ============================================================================
# TEST 3: HYBRID COMPRESSOR (COMPRESSION COMPLETE)
# ============================================================================
print("TEST 3: HYBRID COMPRESSOR (COMPRESSION COMPLETE)")
print("-" * 70)

try:
    from core.hybrid_compressor import HybridCompressor
    
    compressor = HybridCompressor(k_factor=0.02, webp_quality=95)
    print(f"[OK] Hybrid Compressor initialise: K=0.02, WebP=95")
    print(f"   Objectif: 50:1 (K) x 20-60:1 (WebP) = 1000-3000:1")
    
    # Test sur differentes resolutions et contenus
    hybrid_tests = [
        ("Small Simple", np.ones((240, 320, 3)) * 0.5),
        ("Medium Random", np.random.rand(480, 640, 3)),
        ("Large Complex", np.random.rand(1080, 1920, 3)),
        ("Nature-like", np.random.rand(720, 1280, 3) * 0.4 + 0.3),
    ]
    
    hybrid_results = []
    for name, image in hybrid_tests:
        compressed_data, metadata = compressor.compress_image(image)
        
        hybrid_results.append({
            'name': name,
            'shape': list(metadata['original_shape']),
            'k_ratio': float(metadata['k_ratio']),
            'webp_ratio': float(metadata['webp_ratio']),
            'hybrid_ratio': float(metadata['hybrid_ratio']),
            'space_saved': float(metadata['space_saved_percent']),
            'time': float(metadata['total_time']),
            'fps': float(metadata['fps_estimate']),
            'content_type': str(metadata['content_type']),
            'performance_level': str(metadata['optimization_level'])
        })
        
        print(f"\n   [OK] {name} {metadata['original_shape'][:2]}:")
        print(f"      K-Ratio: {metadata['k_ratio']:.1f}:1")
        print(f"      WebP-Ratio: {metadata['webp_ratio']:.1f}:1")
        print(f"      HYBRID TOTAL: {metadata['hybrid_ratio']:.1f}:1")
        print(f"      Economie: {metadata['space_saved_percent']:.1f}%")
        print(f"      Temps: {metadata['total_time']:.3f}s ({metadata['fps_estimate']:.1f} FPS)")
        print(f"      Niveau: {metadata['optimization_level'].upper()}")
    
    # Statistiques Hybrid
    avg_hybrid_ratio = np.mean([r['hybrid_ratio'] for r in hybrid_results])
    avg_k_ratio = np.mean([r['k_ratio'] for r in hybrid_results])
    avg_webp_ratio_hybrid = np.mean([r['webp_ratio'] for r in hybrid_results])
    avg_fps = np.mean([r['fps'] for r in hybrid_results])
    
    print(f"\nRESULTATS HYBRID COMPRESSOR:")
    print(f"   Ratio K moyen: {avg_k_ratio:.1f}:1 (garanti: 50:1)")
    print(f"   Ratio WebP moyen: {avg_webp_ratio_hybrid:.1f}:1")
    print(f"   RATIO HYBRIDE MOYEN: {avg_hybrid_ratio:.1f}:1")
    print(f"   FPS moyen: {avg_fps:.1f}")
    perf_level = '[OK] EXCEPTIONNELLE' if avg_hybrid_ratio > 500 else '[OK] EXCELLENTE' if avg_hybrid_ratio > 200 else '[WARN] MODEREE'
    print(f"   Performance: {perf_level}")
    
    hybrid_valid = avg_hybrid_ratio > 100  # Au moins 100:1
    
    # Test du benchmark complet
    print(f"\nTEST BENCHMARK:")
    test_images = [np.random.rand(480, 640, 3) for _ in range(5)]
    benchmark_results = compressor.benchmark(test_images)
    
    summary = benchmark_results['summary']
    print(f"   Ratio moyen: {summary['average_ratio']:.1f}:1")
    print(f"   Ratio min/max: {summary['min_ratio']:.1f}:1 / {summary['max_ratio']:.1f}:1")
    print(f"   FPS moyen: {summary['average_fps']:.1f}")
    
    # Distribution des performances
    print(f"\nDISTRIBUTION DES PERFORMANCES:")
    dist = summary['performance_distribution']
    for level, data in dist.items():
        if data['count'] > 0:
            bar = "#" * int(data['percentage'] / 5)
            print(f"   {level:12}: {bar} {data['count']} ({data['percentage']:.1f}%)")
    
    # Statistiques finales
    stats = compressor.get_stats()
    print(f"\nSTATISTIQUES GLOBALES:")
    print(f"   Total traite: {stats['total_processed']}")
    print(f"   Ratio moyen: {stats['total_hybrid_ratio']:.1f}:1")
    print(f"   Temps moyen: {stats['total_time']:.3f}s")
    print(f"   Efficacite K: {stats['k_efficiency']:.1f}%")
    print(f"   Efficacite WebP: {stats['webp_efficiency']:.1f}%")
    
except Exception as e:
    print(f"[ERROR] Hybrid Compressor: {e}")
    import traceback
    traceback.print_exc()
    hybrid_valid = False
    hybrid_results = []

print()

# ============================================================================
# TEST 4: HYBRID VIDEO PARAMETER OPTIMIZER
# ============================================================================
print("TEST 4: HYBRID VIDEO PARAMETER OPTIMIZER")
print("-" * 70)

try:
    from core.hybrid_video_parameter_optimizer import (
        HybridVideoParameterOptimizer,
        VideoOptimizationTarget
    )
    import cv2
    import tempfile
    
    print(f"[OK] Hybrid Video Parameter Optimizer disponible")
    
    # Creation d'une video de test
    print(f"\nCreation d'une video de test...")
    
    temp_video = tempfile.mktemp(suffix=".mp4")
    
    # Creer 90 frames (3 secondes @ 30fps) avec mouvement
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, 30.0, (640, 480))
    
    for i in range(90):
        # Frame avec mouvement circulaire
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Fond degrade
        frame[:, :, 0] = int(50 + 30 * np.sin(i * 0.1))  # B
        frame[:, :, 1] = int(50 + 30 * np.cos(i * 0.1))  # G
        frame[:, :, 2] = int(100)  # R
        
        # Cercle en mouvement
        center_x = int(320 + 100 * np.sin(i * 0.15))
        center_y = int(240 + 80 * np.cos(i * 0.1))
        cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), -1)
        
        # Texte
        cv2.putText(frame, f"Frame {i}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    
    video_size = os.path.getsize(temp_video)
    print(f"   [OK] Video de test creee: {video_size:,} bytes ({video_size/1024/1024:.2f} MB)")
    
    # Test avec differents objectifs
    video_results = []
    
    objectives = [
        ("Balanced", VideoOptimizationTarget.BALANCED_VIDEO),
        ("Max Quality", VideoOptimizationTarget.MAX_TEMPORAL_QUALITY),
        ("Max Compression", VideoOptimizationTarget.MAX_COMPRESSION_RATIO),
    ]
    
    for obj_name, objective in objectives:
        print(f"\nTest objectif: {obj_name}")
        
        optimizer = HybridVideoParameterOptimizer(
            optimization_target=objective,
            max_iterations=10,  # Reduit pour le test
            temporal_analysis=True
        )
        
        start_time = time.time()
        result = optimizer.optimize_video_parameters(temp_video, method="grid")
        opt_time = time.time() - start_time
        
        video_results.append({
            'objective': obj_name,
            'k_factor': float(result.best_parameters.k_factor),
            'webp_quality': int(result.best_parameters.webp_quality),
            'temporal_weight': float(result.best_parameters.temporal_coherence_weight),
            'score': float(result.optimization_score),
            'compression_ratio': float(result.performance_metrics['compression_ratio']),
            'spatial_quality': float(result.quality_metrics['spatial_quality']),
            'temporal_quality': float(result.quality_metrics['temporal_quality']),
            'fps_capability': float(result.performance_metrics['fps_capability']),
            'target_achieved': bool(result.target_achieved),
            'optimization_time': float(opt_time)
        })
        
        print(f"   [OK] Optimisation terminee en {opt_time:.1f}s")
        print(f"      K={result.best_parameters.k_factor:.4f}, "
              f"WebP={result.best_parameters.webp_quality}, "
              f"Temporal={result.best_parameters.temporal_coherence_weight:.2f}")
        print(f"      Score: {result.optimization_score:.3f}")
        print(f"      Ratio: {result.performance_metrics['compression_ratio']:.1f}:1")
        print(f"      Qualite spatiale: {result.quality_metrics['spatial_quality']:.3f}")
        print(f"      Qualite temporelle: {result.quality_metrics['temporal_quality']:.3f}")
        print(f"      FPS capability: {result.performance_metrics['fps_capability']:.1f}")
        print(f"      Objectif atteint: {'[OK]' if result.target_achieved else '[FAIL]'}")
        
        optimizer.cleanup()
    
    # Nettoyage
    os.remove(temp_video)
    
    print(f"\nRESULTATS VIDEO OPTIMIZER:")
    avg_video_ratio = np.mean([r['compression_ratio'] for r in video_results])
    avg_video_quality = np.mean([r['spatial_quality'] for r in video_results])
    avg_video_fps = np.mean([r['fps_capability'] for r in video_results])
    
    print(f"   Ratio moyen: {avg_video_ratio:.1f}:1")
    print(f"   Qualite spatiale moyenne: {avg_video_quality:.3f}")
    print(f"   FPS capability moyen: {avg_video_fps:.1f}")
    
    video_valid = avg_video_ratio > 10 and avg_video_quality > 0.5
    
except Exception as e:
    print(f"[ERROR] Video Optimizer: {e}")
    import traceback
    traceback.print_exc()
    video_valid = False
    video_results = []

print()

# ============================================================================
# RAPPORT FINAL
# ============================================================================
print("=" * 70)
print("RAPPORT FINAL DE TESTS")
print("=" * 70)

# Synthese des resultats
all_tests = {
    'K-Factor Engine': k_factor_valid,
    'WebP Optimizer': webp_valid,
    'Hybrid Compressor': hybrid_valid,
    'Video Optimizer': video_valid
}

print("\nETAT DES MODULES:")
for module, status in all_tests.items():
    icon = "[OK]" if status else "[FAIL]"
    print(f"   {icon} {module}: {'FONCTIONNEL' if status else 'ERREUR'}")

all_valid = all(all_tests.values())

print(f"\n{'[SUCCESS]' if all_valid else '[WARNING]'} RESULTAT GLOBAL: "
      f"{'TOUS LES MODULES FONCTIONNELS' if all_valid else 'CERTAINS MODULES EN ERREUR'}")

# Metriques globales
print("\nMETRIQUES DE PERFORMANCE:")
if k_results:
    print(f"   K-Factor: Ratio moyen = {np.mean([r['ratio'] for r in k_results]):.1f}:1")
if webp_results:
    print(f"   WebP: Ratio moyen = {avg_webp_ratio:.1f}:1")
if hybrid_results:
    print(f"   Hybrid: Ratio moyen = {avg_hybrid_ratio:.1f}:1, FPS = {avg_fps:.1f}")
if video_results:
    print(f"   Video: Ratio moyen = {avg_video_ratio:.1f}:1, Qualite = {avg_video_quality:.3f}")

# Sauvegarde des resultats
results_data = {
    'timestamp': datetime.now().isoformat(),
    'all_modules_valid': all_valid,
    'tests': {
        'k_factor': {
            'valid': k_factor_valid,
            'results': k_results
        },
        'webp': {
            'valid': webp_valid,
            'results': webp_results
        },
        'hybrid': {
            'valid': hybrid_valid,
            'results': hybrid_results
        },
        'video': {
            'valid': video_valid,
            'results': video_results
        }
    },
    'summary': {
        'avg_k_ratio': float(np.mean([r['ratio'] for r in k_results])) if k_results else 0,
        'avg_webp_ratio': float(avg_webp_ratio) if webp_results else 0,
        'avg_hybrid_ratio': float(avg_hybrid_ratio) if hybrid_results else 0,
        'avg_fps': float(avg_fps) if hybrid_results else 0,
        'avg_video_ratio': float(avg_video_ratio) if video_results else 0,
        'avg_video_quality': float(avg_video_quality) if video_results else 0
    }
}

# Sauvegarde JSON
results_file = 'compression_test_results.json'
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump(results_data, f, indent=2, default=str)

print(f"\nResultats sauvegardes dans: {results_file}")

print("\n" + "=" * 70)
print("TESTS TERMINEES")
print("=" * 70)

# Code de retour
sys.exit(0 if all_valid else 1)
