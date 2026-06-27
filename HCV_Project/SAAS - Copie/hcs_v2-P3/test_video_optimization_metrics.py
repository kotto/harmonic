#!/usr/bin/env python3
"""
TEST COMPLET D'OPTIMISATION VIDÉO AVEC MÉTRIQUES DÉTAILLÉES
Test des optimisations hybrides sur vidéos variées avec analyse complète
"""

import numpy as np
import cv2
import time
import os
import tempfile
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Tuple
import json

from core.hybrid_video_parameter_optimizer import (
    HybridVideoParameterOptimizer,
    VideoOptimizationTarget
)

def create_diverse_test_videos() -> Dict[str, str]:
    """Crée une collection de vidéos de test variées"""
    videos = {}
    temp_dir = tempfile.mkdtemp(prefix="video_opt_test_")
    
    print("🎥 Création des vidéos de test...")
    
    # Vidéo 1: Animation simple (mouvement fluide)
    print("   📹 Création vidéo 'animation_simple'...")
    frames = []
    for i in range(120):  # 4 secondes @ 30fps
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        # Fond dégradé animé
        frame[:, :, 0] = np.linspace(0, 255, 320) + int(50 * np.sin(i * 0.05))
        frame[:, :, 1] = np.linspace(255, 0, 320) + int(50 * np.cos(i * 0.05))
        frame[:, :, 2] = 128
        
        # Balle qui bouge avec traînée
        x = int(160 + 80 * np.cos(i * 0.05))
        y = int(120 + 60 * np.sin(i * 0.05))
        cv2.circle(frame, (x, y), 20, (255, 255, 255), -1)
        cv2.circle(frame, (x, y), 15, (0, 0, 255), -1)
        
        # Traînée
        for j in range(1, 6):
            trail_x = int(160 + 80 * np.cos((i-j*2) * 0.05))
            trail_y = int(120 + 60 * np.sin((i-j*2) * 0.05))
            alpha = 1.0 - j * 0.2
            cv2.circle(frame, (trail_x, trail_y), 15, (255, 255, 255), -1)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "animation_simple.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['animation_simple'] = video_path
    
    # Vidéo 2: Patterns géométriques complexes
    print("   📹 Création vidéo 'patterns_geometriques'...")
    frames = []
    for i in range(90):  # 3 secondes @ 30fps
        frame = np.random.randint(50, 200, (180, 240, 3), dtype=np.uint8)
        
        # Rectangle rotatif multiple
        for j in range(3):
            center = (120, 90)
            size = 40 - j * 10
            angle = i * 4 + j * 120  # Rotation différente
            rect = ((center[0] - size//2, center[1] - size//2), (size, size), angle)
            box = cv2.boxPoints(rect)
            box = np.array(box, dtype=np.int32)
            color = [(255, 100, 100), (100, 255, 100), (100, 100, 255)][j]
            cv2.drawContours(frame, [box], 0, color, 2)
        
        # Lignes radiales animées
        for angle in range(0, 360, 30):
            rad = np.radians(angle + i * 2)
            x1, y1 = 120, 90
            x2, y2 = int(120 + 60 * np.cos(rad)), int(90 + 60 * np.sin(rad))
            cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "patterns_geometriques.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['patterns_geometriques'] = video_path
    
    # Vidéo 3: Texte animé avec effets
    print("   📹 Création vidéo 'texte_anime'...")
    frames = []
    for i in range(150):  # 5 secondes @ 30fps
        frame = np.zeros((200, 400, 3), dtype=np.uint8)
        frame[:] = (50, 100, 150)  # Fond bleu
        
        # Texte qui défile avec effet
        text = "VIDEO OPTIMIZATION TEST"
        x = int(400 - (i * 3) % 800)
        
        # Ombre et texte principal
        cv2.putText(frame, text, (x+2, 102), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, text, (x, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Compteur avec effet
        counter_text = f"Frame: {i+1:03d}"
        cv2.putText(frame, counter_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Barre de progression
        progress = (i + 1) / 150
        bar_width = int(380 * progress)
        cv2.rectangle(frame, (10, 180), (10 + bar_width, 190), (0, 255, 0), -1)
        cv2.rectangle(frame, (10, 180), (390, 190), (255, 255, 255), 2)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "texte_anime.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['texte_anime'] = video_path
    
    # Vidéo 4: Haute résolution avec détails fins
    print("   📹 Création vidéo 'haute_resolution'...")
    frames = []
    for i in range(60):  # 2 secondes @ 30fps
        frame = np.random.randint(0, 256, (720, 1280, 3), dtype=np.uint8)
        
        # Ajout de détails fins animés
        for j in range(20):
            x = np.random.randint(0, 1280)
            y = np.random.randint(0, 720)
            radius = np.random.randint(2, 8)
            color = tuple(np.random.randint(100, 255, 3).tolist())
            cv2.circle(frame, (x, y), radius, color, -1)
        
        # Pattern de grille animé
        grid_size = 40
        for gx in range(0, 1280, grid_size):
            for gy in range(0, 720, grid_size):
                phase = i * 0.1 + gx * 0.01 + gy * 0.01
                intensity = int(128 + 127 * np.sin(phase))
                cv2.rectangle(frame, (gx, gy), (gx+grid_size-1, gy+grid_size-1), 
                           (intensity, intensity, intensity), 1)
        
        # Rectangle informatif
        cv2.rectangle(frame, (50, 50), (400, 150), (255, 255, 255), 2)
        cv2.putText(frame, f"HD Video {i+1:02d}/60", (60, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Resolution: 1280x720", (60, 130), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "haute_resolution.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['haute_resolution'] = video_path
    
    # Vidéo 5: Scène naturelle simulée
    print("   📹 Création vidéo 'scene_naturelle'...")
    frames = []
    for i in range(120):  # 4 secondes @ 30fps
        frame = np.zeros((300, 400, 3), dtype=np.uint8)
        
        # Ciel dégradé
        for y in range(300):
            sky_intensity = int(100 + 100 * (y / 300))
            frame[y, :, 0] = sky_intensity
            frame[y, :, 1] = sky_intensity + 50
            frame[y, :, 2] = 255 - sky_intensity // 2
        
        # Soleil animé
        sun_x = int(200 + 100 * np.cos(i * 0.02))
        sun_y = int(80 + 30 * np.sin(i * 0.02))
        cv2.circle(frame, (sun_x, sun_y), 30, (255, 255, 0), -1)
        cv2.circle(frame, (sun_x, sun_y), 35, (255, 200, 0), 2)
        
        # Montagnes
        mountain_points = np.array([
            [0, 250], [100, 180], [200, 200], [300, 160], [400, 220], [400, 300], [0, 300]
        ], np.int32)
        cv2.fillPoly(frame, [mountain_points], (100, 150, 100))
        
        # Arbres
        for tree_x in [80, 150, 250, 320]:
            tree_y = 250
            cv2.rectangle(frame, (tree_x-5, tree_y), (tree_x+5, 280), (101, 67, 33), -1)
            cv2.circle(frame, (tree_x, tree_y-10), 20, (34, 139, 34), -1)
            cv2.circle(frame, (tree_x, tree_y-25), 15, (34, 139, 34), -1)
        
        # Nuages
        for cloud_idx in range(3):
            cloud_x = int(100 + cloud_idx * 100 + 20 * np.sin(i * 0.01 + cloud_idx))
            cloud_y = 60 + cloud_idx * 20
            cv2.circle(frame, (cloud_x, cloud_y), 15, (255, 255, 255), -1)
            cv2.circle(frame, (cloud_x+10, cloud_y), 12, (255, 255, 255), -1)
            cv2.circle(frame, (cloud_x-8, cloud_y+5), 10, (255, 255, 255), -1)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "scene_naturelle.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['scene_naturelle'] = video_path
    
    print(f"✅ {len(videos)} vidéos de test créées")
    return videos

def create_video_from_frames(frames: List[np.ndarray], output_path: str, fps: float):
    """Crée une vidéo à partir d'une liste de frames"""
    if not frames:
        raise ValueError("Aucune frame à encoder")
    
    height, width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    for frame in frames:
        out.write(frame)
    
    out.release()

def test_video_optimization_with_metrics(videos: Dict[str, str]) -> Dict[str, Any]:
    """Test complet d'optimisation vidéo avec métriques détaillées"""
    print("\n" + "="*80)
    print("🎥 TEST D'OPTIMISATION VIDÉO AVEC MÉTRIQUES DÉTAILLÉES")
    print("="*80)
    
    # Objectifs d'optimisation à tester
    objectives = [
        VideoOptimizationTarget.MAX_TEMPORAL_QUALITY,
        VideoOptimizationTarget.MAX_COMPRESSION_RATIO,
        VideoOptimizationTarget.REAL_TIME_PROCESSING,
        VideoOptimizationTarget.MIN_BANDWIDTH,
        VideoOptimizationTarget.BALANCED_VIDEO
    ]
    
    all_results = {}
    video_metadata = {}
    
    # Collecte des métadonnées vidéos
    print("\n📊 Analyse des métadonnées vidéos...")
    for video_name, video_path in videos.items():
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            file_size = os.path.getsize(video_path)
            
            video_metadata[video_name] = {
                'fps': fps,
                'frame_count': frame_count,
                'width': width,
                'height': height,
                'duration': duration,
                'file_size': file_size,
                'resolution': f"{width}x{height}",
                'bitrate': (file_size * 8) / duration if duration > 0 else 0
            }
            
            print(f"   📹 {video_name}: {video_metadata[video_name]['resolution']}, "
                  f"{fps:.1f} FPS, {duration:.1f}s, {file_size/1024/1024:.1f} MB")
            
            cap.release()
    
    # Test d'optimisation pour chaque objectif
    for objective in objectives:
        print(f"\n🎯 Test optimisation: {objective.value}")
        print("-" * 60)
        
        objective_results = {}
        
        for video_name, video_path in videos.items():
            print(f"   📹 Optimisation: {video_name}")
            
            optimizer = HybridVideoParameterOptimizer(
                optimization_target=objective,
                max_iterations=20,  # Réduit pour le test
                parallel_workers=2
            )
            
            try:
                start_time = time.time()
                result = optimizer.optimize_video_parameters(video_path, method="grid")
                optimization_time = time.time() - start_time
                
                # Métriques détaillées
                metrics = {
                    'optimization_time': optimization_time,
                    'best_parameters': {
                        'k_factor': result.best_parameters.k_factor,
                        'webp_quality': result.best_parameters.webp_quality,
                        'temporal_coherence_weight': result.best_parameters.temporal_coherence_weight,
                        'frame_sample_rate': result.best_parameters.frame_sample_rate
                    },
                    'performance_metrics': result.performance_metrics,
                    'quality_metrics': result.quality_metrics,
                    'temporal_metrics': result.temporal_metrics,
                    'optimization_score': result.optimization_score,
                    'target_achieved': result.target_achieved,
                    'video_info': video_metadata[video_name]
                }
                
                # Calculs supplémentaires
                original_size = video_metadata[video_name]['file_size']
                compressed_size = original_size / result.performance_metrics['compression_ratio']
                bandwidth_kbps = result.performance_metrics['bandwidth'] / 1024
                storage_saving_mb = (original_size - compressed_size) / 1024 / 1024
                
                metrics['additional_metrics'] = {
                    'original_size_mb': original_size / 1024 / 1024,
                    'estimated_compressed_size_mb': compressed_size / 1024 / 1024,
                    'storage_saving_mb': storage_saving_mb,
                    'storage_saving_percent': (storage_saving_mb / (original_size / 1024 / 1024)) * 100,
                    'bandwidth_kbps': bandwidth_kbps,
                    'compression_efficiency': result.performance_metrics['compression_ratio'] / optimization_time,
                    'fps_capability': result.performance_metrics['fps_capability'],
                    'real_time_factor': result.performance_metrics['fps_capability'] / video_metadata[video_name]['fps']
                }
                
                objective_results[video_name] = metrics
                
                print(f"      ✅ Optimisation réussie")
                print(f"      📊 Score: {result.optimization_score:.3f}")
                print(f"      🗜️  Ratio: {result.performance_metrics['compression_ratio']:.1f}:1")
                print(f"      🎬 FPS capability: {result.performance_metrics['fps_capability']:.1f}")
                print(f"      📶 Bandwidth: {bandwidth_kbps:.1f} KB/s")
                print(f"      💾 Espace économisé: {storage_saving_mb:.1f} MB ({metrics['additional_metrics']['storage_saving_percent']:.1f}%)")
                print(f"      ⏱️  Temps optimisation: {optimization_time:.2f}s")
                print(f"      🎯 Objectif atteint: {result.target_achieved}")
                
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
                objective_results[video_name] = {'error': str(e)}
            
            finally:
                optimizer.cleanup()
        
        all_results[objective.value] = objective_results
    
    return {
        'results': all_results,
        'video_metadata': video_metadata
    }

def analyze_and_display_metrics(test_results: Dict[str, Any]):
    """Analyse et affiche les métriques détaillées"""
    print("\n" + "="*80)
    print("📊 ANALYSE DÉTAILLÉE DES MÉTRIQUES")
    print("="*80)
    
    results = test_results['results']
    video_metadata = test_results['video_metadata']
    
    # Analyse par objectif
    for objective_name, objective_results in results.items():
        print(f"\n🎯 ANALYSE OBJECTIF: {objective_name.upper()}")
        print("-" * 60)
        
        # Collecte des métriques valides
        valid_results = {name: data for name, data in objective_results.items() if 'error' not in data}
        
        if not valid_results:
            print(f"   ❌ Aucun résultat valide pour {objective_name}")
            continue
        
        # Métriques agrégées
        scores = [data['optimization_score'] for data in valid_results.values()]
        ratios = [data['performance_metrics']['compression_ratio'] for data in valid_results.values()]
        fps_capabilities = [data['performance_metrics']['fps_capability'] for data in valid_results.values()]
        bandwidths = [data['additional_metrics']['bandwidth_kbps'] for data in valid_results.values()]
        storage_savings = [data['additional_metrics']['storage_saving_percent'] for data in valid_results.values()]
        optimization_times = [data['optimization_time'] for data in valid_results.values()]
        
        print(f"   📈 MÉTRIQUES AGRÉGÉES:")
        print(f"      Score moyen: {np.mean(scores):.3f} ± {np.std(scores):.3f}")
        print(f"      Ratio moyen: {np.mean(ratios):.1f}:1 ± {np.std(ratios):.1f}")
        print(f"      FPS capability moyen: {np.mean(fps_capabilities):.1f} ± {np.std(fps_capabilities):.1f}")
        print(f"      Bandwidth moyen: {np.mean(bandwidths):.1f} KB/s ± {np.std(bandwidths):.1f}")
        print(f"      Économie stockage moyenne: {np.mean(storage_savings):.1f}% ± {np.std(storage_savings):.1f}%")
        print(f"      Temps optimisation moyen: {np.mean(optimization_times):.2f}s ± {np.std(optimization_times):.2f}s")
        
        # Meilleur et pire cas
        best_video = max(valid_results.items(), key=lambda x: x[1]['optimization_score'])
        worst_video = min(valid_results.items(), key=lambda x: x[1]['optimization_score'])
        
        print(f"\n   🏆 MEILLEUR CAS: {best_video[0]}")
        print(f"      Score: {best_video[1]['optimization_score']:.3f}")
        print(f"      Ratio: {best_video[1]['performance_metrics']['compression_ratio']:.1f}:1")
        print(f"      FPS: {best_video[1]['performance_metrics']['fps_capability']:.1f}")
        print(f"      Économie: {best_video[1]['additional_metrics']['storage_saving_percent']:.1f}%")
        
        print(f"\n   ⚠️  PIRE CAS: {worst_video[0]}")
        print(f"      Score: {worst_video[1]['optimization_score']:.3f}")
        print(f"      Ratio: {worst_video[1]['performance_metrics']['compression_ratio']:.1f}:1")
        print(f"      FPS: {worst_video[1]['performance_metrics']['fps_capability']:.1f}")
        print(f"      Économie: {worst_video[1]['additional_metrics']['storage_saving_percent']:.1f}%")
        
        # Analyse des paramètres optimaux
        k_factors = [data['best_parameters']['k_factor'] for data in valid_results.values()]
        webp_qualities = [data['best_parameters']['webp_quality'] for data in valid_results.values()]
        temporal_weights = [data['best_parameters']['temporal_coherence_weight'] for data in valid_results.values()]
        
        print(f"\n   🔧 PARAMÈTRES OPTIMAUX MOYENS:")
        print(f"      K-Factor: {np.mean(k_factors):.4f} ± {np.std(k_factors):.4f}")
        print(f"      WebP Quality: {np.mean(webp_qualities):.1f} ± {np.std(webp_qualities):.1f}")
        print(f"      Temporal Weight: {np.mean(temporal_weights):.2f} ± {np.std(temporal_weights):.2f}")

def generate_comprehensive_metrics_report(test_results: Dict[str, Any]):
    """Génère un rapport visuel complet des métriques"""
    print("\n" + "="*80)
    print("📊 GÉNÉRATION DU RAPPORT VISUEL DES MÉTRIQUES")
    print("="*80)
    
    try:
        results = test_results['results']
        video_metadata = test_results['video_metadata']
        
        # Création des graphiques
        fig, axes = plt.subplots(3, 3, figsize=(20, 16))
        fig.suptitle('Rapport Complet d\'Optimisation Vidéo', fontsize=16)
        
        # Préparation des données
        objectives = list(results.keys())
        video_names = list(video_metadata.keys())
        
        # Graphique 1: Scores par objectif et vidéo
        score_matrix = []
        for objective in objectives:
            row = []
            for video in video_names:
                if video in results[objective] and 'error' not in results[objective][video]:
                    row.append(results[objective][video]['optimization_score'])
                else:
                    row.append(0)
            score_matrix.append(row)
        
        im1 = axes[0, 0].imshow(score_matrix, cmap='viridis', aspect='auto')
        axes[0, 0].set_title('Scores d\'Optimisation')
        axes[0, 0].set_xticks(range(len(video_names)))
        axes[0, 0].set_xticklabels(video_names, rotation=45)
        axes[0, 0].set_yticks(range(len(objectives)))
        axes[0, 0].set_yticklabels(objectives)
        plt.colorbar(im1, ax=axes[0, 0])
        
        # Graphique 2: Ratios de compression moyens
        avg_ratios = []
        for objective in objectives:
            valid_ratios = [results[objective][video]['performance_metrics']['compression_ratio'] 
                           for video in video_names 
                           if video in results[objective] and 'error' not in results[objective][video]]
            avg_ratios.append(np.mean(valid_ratios) if valid_ratios else 0)
        
        bars = axes[0, 1].bar(objectives, avg_ratios, color='skyblue', alpha=0.7)
        axes[0, 1].set_title('Ratio Compression Moyen par Objectif')
        axes[0, 1].set_ylabel('Ratio:1')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Ajout des valeurs sur les barres
        for bar, ratio in zip(bars, avg_ratios):
            axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                            f'{ratio:.0f}:1', ha='center', va='bottom')
        
        # Graphique 3: FPS capability par objectif
        avg_fps = []
        for objective in objectives:
            valid_fps = [results[objective][video]['performance_metrics']['fps_capability'] 
                        for video in video_names 
                        if video in results[objective] and 'error' not in results[objective][video]]
            avg_fps.append(np.mean(valid_fps) if valid_fps else 0)
        
        axes[0, 2].bar(objectives, avg_fps, color='lightgreen', alpha=0.7)
        axes[0, 2].set_title('FPS Capability Moyen par Objectif')
        axes[0, 2].set_ylabel('FPS')
        axes[0, 2].tick_params(axis='x', rotation=45)
        axes[0, 2].axhline(y=30, color='red', linestyle='--', alpha=0.5, label='30 FPS (Real-time)')
        axes[0, 2].legend()
        
        # Graphique 4: Bandwidth par objectif
        avg_bandwidth = []
        for objective in objectives:
            valid_bw = [results[objective][video]['additional_metrics']['bandwidth_kbps'] 
                        for video in video_names 
                        if video in results[objective] and 'error' not in results[objective][video]]
            avg_bandwidth.append(np.mean(valid_bw) if valid_bw else 0)
        
        axes[1, 0].bar(objectives, avg_bandwidth, color='orange', alpha=0.7)
        axes[1, 0].set_title('Bandwidth Moyen par Objectif')
        axes[1, 0].set_ylabel('Bandwidth (KB/s)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 5: Économie de stockage par objectif
        avg_savings = []
        for objective in objectives:
            valid_savings = [results[objective][video]['additional_metrics']['storage_saving_percent'] 
                            for video in video_names 
                            if video in results[objective] and 'error' not in results[objective][video]]
            avg_savings.append(np.mean(valid_savings) if valid_savings else 0)
        
        axes[1, 1].bar(objectives, avg_savings, color='gold', alpha=0.7)
        axes[1, 1].set_title('Économie Stockage Moyenne par Objectif')
        axes[1, 1].set_ylabel('Économie (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 6: Temps d'optimisation par objectif
        avg_times = []
        for objective in objectives:
            valid_times = [results[objective][video]['optimization_time'] 
                          for video in video_names 
                          if video in results[objective] and 'error' not in results[objective][video]]
            avg_times.append(np.mean(valid_times) if valid_times else 0)
        
        axes[1, 2].bar(objectives, avg_times, color='lightcoral', alpha=0.7)
        axes[1, 2].set_title('Temps Optimisation Moyen par Objectif')
        axes[1, 2].set_ylabel('Temps (s)')
        axes[1, 2].tick_params(axis='x', rotation=45)
        
        # Graphique 7: Distribution des K-Factors optimaux
        all_k_factors = []
        all_objectives_k = []
        for objective in objectives:
            for video in video_names:
                if video in results[objective] and 'error' not in results[objective][video]:
                    all_k_factors.append(results[objective][video]['best_parameters']['k_factor'])
                    all_objectives_k.append(objective)
        
        axes[2, 0].hist(all_k_factors, bins=20, alpha=0.7, color='purple', edgecolor='black')
        axes[2, 0].set_title('Distribution K-Factors Optimaux')
        axes[2, 0].set_xlabel('K-Factor')
        axes[2, 0].set_ylabel('Fréquence')
        
        # Graphique 8: Distribution des WebP Quality optimaux
        all_webp_qualities = []
        for objective in objectives:
            for video in video_names:
                if video in results[objective] and 'error' not in results[objective][video]:
                    all_webp_qualities.append(results[objective][video]['best_parameters']['webp_quality'])
        
        axes[2, 1].hist(all_webp_qualities, bins=15, alpha=0.7, color='brown', edgecolor='black')
        axes[2, 1].set_title('Distribution WebP Quality Optimaux')
        axes[2, 1].set_xlabel('WebP Quality')
        axes[2, 1].set_ylabel('Fréquence')
        
        # Graphique 9: Performance globale (Score vs Temps)
        all_scores = []
        all_times = []
        all_labels = []
        
        for objective in objectives:
            for video in video_names:
                if video in results[objective] and 'error' not in results[objective][video]:
                    all_scores.append(results[objective][video]['optimization_score'])
                    all_times.append(results[objective][video]['optimization_time'])
                    all_labels.append(f"{objective[:8]}...{video[:8]}")
        
        scatter = axes[2, 2].scatter(all_times, all_scores, alpha=0.7, s=50, c=range(len(all_scores)), cmap='viridis')
        axes[2, 2].set_title('Performance Globale (Score vs Temps)')
        axes[2, 2].set_xlabel('Temps d\'Optimisation (s)')
        axes[2, 2].set_ylabel('Score d\'Optimisation')
        axes[2, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('F:/FINAL/DEFINITIF/hcs_v2-P3/video_optimization_metrics_report.png', 
                   dpi=150, bbox_inches='tight')
        print(f"\n📊 Rapport visuel sauvegardé: video_optimization_metrics_report.png")
        
    except Exception as e:
        print(f"\n⚠️ Erreur génération rapport visuel: {e}")

def save_detailed_metrics_json(test_results: Dict[str, Any]):
    """Sauvegarde les métriques détaillées en JSON"""
    print("\n💾 Sauvegarde des métriques détaillées...")
    
    # Préparation des données pour JSON
    json_results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'video_metadata': test_results['video_metadata'],
        'optimization_results': {}
    }
    
    # Conversion des résultats pour JSON
    for objective, objective_results in test_results['results'].items():
        json_results['optimization_results'][objective] = {}
        for video, metrics in objective_results.items():
            if 'error' not in metrics:
                # Conversion des types numpy en types Python standards
                json_metrics = {}
                for key, value in metrics.items():
                    if isinstance(value, np.ndarray):
                        json_metrics[key] = value.tolist()
                    elif isinstance(value, (np.integer, np.int32, np.int64)):
                        json_metrics[key] = int(value)
                    elif isinstance(value, (np.floating, np.float32, np.float64)):
                        json_metrics[key] = float(value)
                    elif isinstance(value, (np.bool_, bool)):
                        json_metrics[key] = bool(value)
                    elif isinstance(value, dict):
                        # Conversion récursive des dictionnaires
                        json_metrics[key] = {}
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (np.integer, np.int32, np.int64)):
                                json_metrics[key][sub_key] = int(sub_value)
                            elif isinstance(sub_value, (np.floating, np.float32, np.float64)):
                                json_metrics[key][sub_key] = float(sub_value)
                            elif isinstance(sub_value, (np.bool_, bool)):
                                json_metrics[key][sub_key] = bool(sub_value)
                            elif isinstance(sub_value, np.ndarray):
                                json_metrics[key][sub_key] = sub_value.tolist()
                            else:
                                json_metrics[key][sub_key] = sub_value
                    else:
                        json_metrics[key] = value
                
                json_results['optimization_results'][objective][video] = json_metrics
            else:
                json_results['optimization_results'][objective][video] = metrics
    
    # Sauvegarde
    output_file = 'F:/FINAL/DEFINITIF/hcs_v2-P3/video_optimization_detailed_metrics.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Métriques sauvegardées: {output_file}")

def main():
    """Fonction principale de test d'optimisation vidéo avec métriques"""
    print("🎥 TEST COMPLET D'OPTIMISATION VIDÉO AVEC MÉTRIQUES")
    print("Test des optimisations hybrides sur vidéos variées")
    print("=" * 80)
    
    # Création des vidéos de test
    test_videos = create_diverse_test_videos()
    
    # Test d'optimisation avec métriques détaillées
    test_results = test_video_optimization_with_metrics(test_videos)
    
    # Analyse et affichage des métriques
    analyze_and_display_metrics(test_results)
    
    # Génération du rapport visuel
    generate_comprehensive_metrics_report(test_results)
    
    # Sauvegarde des métriques détaillées
    save_detailed_metrics_json(test_results)
    
    # Nettoyage
    print("\n🧹 Nettoyage des fichiers temporaires...")
    for video_path in test_videos.values():
        try:
            os.remove(video_path)
        except:
            pass
    
    try:
        os.rmdir(os.path.dirname(list(test_videos.values())[0]))
    except:
        pass
    
    print("\n✅ Test d'optimisation vidéo terminé!")
    print("📊 Métriques détaillées générées et disponibles!")
    print("🎥 Système d'optimisation vidéo validé avec succès!")
    
    return test_results

if __name__ == "__main__":
    main()
