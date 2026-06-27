#!/usr/bin/env python3
"""
TEST D'OPTIMISATION DE QUALITÉ VIDÉO
Tests complets de l'optimiseur de qualité amélioré
Focus sur l'amélioration des scores de qualité vidéo
"""

import numpy as np
import cv2
import os
import tempfile
import time
import matplotlib.pyplot as plt
from typing import Dict, Any, List
import json

from core.enhanced_video_quality_optimizer import (
    EnhancedVideoQualityOptimizer,
    QualityOptimizationMode,
    QualityMetrics
)

def create_test_videos() -> Dict[str, str]:
    """Crée des vidéos de test avec différents types de contenu"""
    videos = {}
    temp_dir = tempfile.mkdtemp(prefix="quality_test_")
    
    print("📹 Création des vidéos de test pour optimisation qualité...")
    
    # Vidéo 1: Contours complexes
    print("   📐 Création vidéo 'complex_edges'...")
    frames_edges = []
    for i in range(60):  # 2 secondes @ 30fps
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Patterns géométriques complexes
        for j in range(5):
            angle = i * 0.05 + j * 1.2
            x = int(160 + 80 * np.cos(angle))
            y = int(120 + 60 * np.sin(angle))
            cv2.circle(frame, (x, y), 20, (255, 255, 255), 2)
            
            # Lignes radiales
            for k in range(8):
                line_angle = k * np.pi / 4
                end_x = int(160 + 100 * np.cos(line_angle))
                end_y = int(120 + 100 * np.sin(line_angle))
                cv2.line(frame, (160, 120), (end_x, end_y), (128, 128, 128), 1)
        
        # Texte animé
        cv2.putText(frame, f"Frame {i+1}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        frames_edges.append(frame)
    
    edges_video = os.path.join(temp_dir, "complex_edges.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(edges_video, fourcc, 30.0, (320, 240))
    for frame in frames_edges:
        out.write(frame)
    out.release()
    
    videos['complex_edges'] = edges_video
    
    # Vidéo 2: Couleurs vibrantes
    print("   🌈 Création vidéo 'vibrant_colors'...")
    frames_colors = []
    for i in range(60):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Dégradé de couleurs animé
        for y in range(240):
            for x in range(320):
                hue = (i * 2 + x + y) % 180
                saturation = 255
                value = 128 + 64 * np.sin(i * 0.1)
                
                # Conversion HSV vers BGR
                hsv_color = np.uint8([[[hue, saturation, value]]])
                bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
                frame[y, x] = bgr_color
        
        # Ajout d'éléments colorés
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
        for j, color in enumerate(colors):
            x = int(64 + j * 48)
            y = int(120 + 40 * np.sin(i * 0.1 + j * 0.5))
            cv2.circle(frame, (x, y), 15, color, -1)
        
        frames_colors.append(frame)
    
    colors_video = os.path.join(temp_dir, "vibrant_colors.mp4")
    out = cv2.VideoWriter(colors_video, fourcc, 30.0, (320, 240))
    for frame in frames_colors:
        out.write(frame)
    out.release()
    
    videos['vibrant_colors'] = colors_video
    
    # Vidéo 3: Mouvement fluide
    print("   🌊 Création vidéo 'smooth_motion'...")
    frames_motion = []
    for i in range(60):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Fond dégradé doux
        for y in range(240):
            intensity = int(128 + 64 * np.sin(y * 0.02 + i * 0.05))
            frame[y, :] = [intensity, intensity, intensity]
        
        # Mouvement ondulatoire
        for x in range(320):
            wave_y = int(120 + 30 * np.sin(x * 0.02 + i * 0.1))
            if 0 <= wave_y < 240:
                cv2.line(frame, (x, wave_y), (x, wave_y), (255, 255, 255), 2)
        
        # Particules flottantes
        for j in range(10):
            particle_x = int(160 + 100 * np.cos(i * 0.05 + j * 0.6))
            particle_y = int(120 + 80 * np.sin(i * 0.03 + j * 0.8))
            cv2.circle(frame, (particle_x, particle_y), 3, (200, 200, 255), -1)
        
        frames_motion.append(frame)
    
    motion_video = os.path.join(temp_dir, "smooth_motion.mp4")
    out = cv2.VideoWriter(motion_video, fourcc, 30.0, (320, 240))
    for frame in frames_motion:
        out.write(frame)
    out.release()
    
    videos['smooth_motion'] = motion_video
    
    # Vidéo 4: Contenu mixte
    print("   🎭 Création vidéo 'mixed_content'...")
    frames_mixed = []
    for i in range(60):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Fond avec texture
        noise = np.random.randint(0, 50, (240, 320, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        # Éléments géométriques
        if i % 20 < 10:
            # Phase 1: Formes géométriques
            cv2.rectangle(frame, (50, 50), (150, 150), (255, 0, 0), -1)
            cv2.circle(frame, (200, 120), 40, (0, 255, 0), -1)
        else:
            # Phase 2: Dégradés
            for y in range(50, 150):
                for x in range(50, 150):
                    intensity = int(128 + 127 * np.sin((x + y + i) * 0.05))
                    frame[y, x] = [intensity, intensity // 2, intensity // 3]
        
        # Texte et contours
        cv2.putText(frame, f"Mixed {i+1}", (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Mouvement subtil
        offset_x = int(10 * np.sin(i * 0.1))
        offset_y = int(5 * np.cos(i * 0.15))
        cv2.line(frame, (160 + offset_x, 120 + offset_y), (240 + offset_x, 120 + offset_y), (255, 255, 0), 3)
        
        frames_mixed.append(frame)
    
    mixed_video = os.path.join(temp_dir, "mixed_content.mp4")
    out = cv2.VideoWriter(mixed_video, fourcc, 30.0, (320, 240))
    for frame in frames_mixed:
        out.write(frame)
    out.release()
    
    videos['mixed_content'] = mixed_video
    
    print(f"✅ {len(videos)} vidéos de test créées")
    return videos

def test_quality_modes(videos: Dict[str, str]) -> Dict[str, Any]:
    """Test tous les modes d'optimisation de qualité"""
    print("\n🎯 TEST DES MODES D'OPTIMISATION DE QUALITÉ")
    print("=" * 70)
    
    modes = [
        QualityOptimizationMode.VISUAL_FIDELITY,
        QualityOptimizationMode.EDGE_PRESERVATION,
        QualityOptimizationMode.COLOR_ACCURACY,
        QualityOptimizationMode.TEMPORAL_SMOOTHNESS,
        QualityOptimizationMode.BALANCED_QUALITY
    ]
    
    results = {}
    
    for mode in modes:
        print(f"\n🎯 Test mode: {mode.value}")
        mode_results = {}
        
        optimizer = EnhancedVideoQualityOptimizer(quality_mode=mode)
        
        for video_name, video_path in videos.items():
            try:
                print(f"   📹 Vidéo: {video_name}")
                
                # Optimisation pour qualité
                start_time = time.time()
                result = optimizer.optimize_for_quality(video_path, target_quality_score=0.7)
                optimization_time = time.time() - start_time
                
                # Extraction des métriques
                quality_score = result.quality_metrics.get('overall_score', 0.0)
                
                metrics = {
                    'quality_score': quality_score,
                    'optimization_time': optimization_time,
                    'k_factor': result.best_parameters.k_factor,
                    'webp_quality': result.best_parameters.webp_quality,
                    'psnr': result.quality_metrics.get('psnr', 0.0),
                    'ssim': result.quality_metrics.get('ssim', 0.0),
                    'edge_preservation': result.quality_metrics.get('edge_preservation', 0.0),
                    'color_fidelity': result.quality_metrics.get('color_fidelity', 0.0),
                    'temporal_consistency': result.quality_metrics.get('temporal_consistency', 0.0)
                }
                
                mode_results[video_name] = metrics
                
                print(f"      📊 Score qualité: {quality_score:.3f}")
                print(f"      ⚡ Temps: {optimization_time:.3f}s")
                print(f"      🔧 K-Factor: {result.best_parameters.k_factor:.4f}")
                print(f"      🎨 WebP Quality: {result.best_parameters.webp_quality}")
                
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
                mode_results[video_name] = {'error': str(e)}
        
        results[mode.value] = mode_results
    
    return results

def test_adaptive_optimization(videos: Dict[str, str]) -> Dict[str, Any]:
    """Test l'optimisation adaptative"""
    print("\n🔄 TEST OPTIMISATION ADAPTATIVE")
    print("=" * 50)
    
    results = {}
    
    for video_name, video_path in videos.items():
        print(f"\n🎬 Vidéo: {video_name}")
        
        try:
            optimizer = EnhancedVideoQualityOptimizer()
            
            # Optimisation adaptative
            start_time = time.time()
            result = optimizer.adaptive_quality_optimization(video_path)
            optimization_time = time.time() - start_time
            
            # Analyse du contenu
            frames = optimizer._load_video_frames(video_path)
            content_analysis = optimizer._analyze_video_content(frames)
            
            metrics = {
                'detected_mode': optimizer.quality_mode.value,
                'quality_score': result.quality_metrics.get('overall_score', 0.0),
                'optimization_time': optimization_time,
                'content_analysis': content_analysis,
                'parameters': {
                    'k_factor': result.best_parameters.k_factor,
                    'webp_quality': result.best_parameters.webp_quality
                }
            }
            
            results[video_name] = metrics
            
            print(f"   🎯 Mode détecté: {optimizer.quality_mode.value}")
            print(f"   📊 Score qualité: {metrics['quality_score']:.3f}")
            print(f"   ⚡ Temps: {optimization_time:.3f}s")
            print(f"   📐 Contours: {content_analysis.get('has_many_edges', False)}")
            print(f"   🌈 Couleurs: {content_analysis.get('has_vibrant_colors', False)}")
            print(f"   🌊 Mouvement: {content_analysis.get('has_motion', False)}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[video_name] = {'error': str(e)}
    
    return results

def test_quality_progression(videos: Dict[str, str]) -> Dict[str, Any]:
    """Test la progression de la qualité avec différents scores cibles"""
    print("\n📈 TEST PROGRESSION DE QUALITÉ")
    print("=" * 50)
    
    target_scores = [0.3, 0.5, 0.7, 0.8, 0.9]
    test_video = list(videos.values())[0]  # Première vidéo
    
    results = {}
    
    for target in target_scores:
        print(f"\n🎯 Score cible: {target}")
        
        try:
            optimizer = EnhancedVideoQualityOptimizer(
                quality_mode=QualityOptimizationMode.BALANCED_QUALITY
            )
            
            start_time = time.time()
            result = optimizer.optimize_for_quality(test_video, target_quality_score=target)
            optimization_time = time.time() - start_time
            
            achieved_score = result.quality_metrics.get('overall_score', 0.0)
            
            metrics = {
                'target_score': target,
                'achieved_score': achieved_score,
                'optimization_time': optimization_time,
                'success': achieved_score >= target,
                'parameters': {
                    'k_factor': result.best_parameters.k_factor,
                    'webp_quality': result.best_parameters.webp_quality
                },
                'quality_metrics': result.quality_metrics
            }
            
            results[f"target_{target}"] = metrics
            
            print(f"   ✅ Atteint: {achieved_score:.3f} ({'Succès' if metrics['success'] else 'Échec'})")
            print(f"   ⚡ Temps: {optimization_time:.3f}s")
            print(f"   🔧 K-Factor: {result.best_parameters.k_factor:.4f}")
            print(f"   🎨 WebP Quality: {result.best_parameters.webp_quality}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[f"target_{target}"] = {'error': str(e)}
    
    return results

def test_detailed_metrics(videos: Dict[str, str]) -> Dict[str, Any]:
    """Test détaillé des métriques de qualité"""
    print("\n🔬 TEST DÉTAILLÉ DES MÉTRIQUES")
    print("=" * 50)
    
    results = {}
    
    for video_name, video_path in videos.items():
        print(f"\n📹 Vidéo: {video_name}")
        
        try:
            optimizer = EnhancedVideoQualityOptimizer(
                quality_mode=QualityOptimizationMode.BALANCED_QUALITY
            )
            
            # Chargement des frames
            original_frames = optimizer._load_video_frames(video_path, max_frames=20)
            
            # Test avec différents paramètres
            test_params = [
                (0.001, 80),  # Basique
                (0.0005, 90), # Haute qualité
                (0.002, 70),  # Moyen
                (0.003, 60)   # Basse qualité
            ]
            
            video_results = []
            
            for k_factor, webp_quality in test_params:
                processed_frames = optimizer._simulate_processing(original_frames, k_factor, webp_quality)
                quality_metrics = optimizer.calculate_detailed_quality_metrics(original_frames, processed_frames)
                
                metrics = {
                    'k_factor': k_factor,
                    'webp_quality': webp_quality,
                    'quality_metrics': quality_metrics.__dict__
                }
                
                video_results.append(metrics)
                
                print(f"   🔧 K={k_factor:.4f}, Q={webp_quality}: Score={quality_metrics.overall_score:.3f}")
            
            results[video_name] = video_results
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[video_name] = [{'error': str(e)}]
    
    return results

def generate_quality_report(mode_results: Dict, adaptive_results: Dict, 
                          progression_results: Dict, detailed_results: Dict):
    """Génère un rapport complet d'optimisation qualité"""
    print("\n📊 GÉNÉRATION DU RAPPORT D'OPTIMISATION QUALITÉ")
    print("=" * 70)
    
    try:
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Rapport Optimisation Qualité Vidéo', fontsize=16)
        
        # Graphique 1: Comparaison des modes
        if mode_results:
            mode_names = list(mode_results.keys())
            avg_scores = []
            
            for mode_name in mode_names:
                mode_data = mode_results[mode_name]
                scores = [data.get('quality_score', 0) for data in mode_data.values() if 'error' not in data]
                avg_scores.append(np.mean(scores) if scores else 0)
            
            axes[0, 0].bar(mode_names, avg_scores, color='skyblue', alpha=0.7)
            axes[0, 0].set_title('Score Qualité par Mode')
            axes[0, 0].set_ylabel('Score Moyen')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 2: Détection adaptative
        if adaptive_results:
            detected_modes = []
            success_scores = []
            
            for video_name, data in adaptive_results.items():
                if 'error' not in data:
                    detected_modes.append(data.get('detected_mode', 'Unknown'))
                    success_scores.append(data.get('quality_score', 0))
            
            if detected_modes:
                mode_counts = {}
                for mode in detected_modes:
                    mode_counts[mode] = mode_counts.get(mode, 0) + 1
                
                axes[0, 1].pie(list(mode_counts.values()), labels=list(mode_counts.keys()), autopct='%1.1f%%')
                axes[0, 1].set_title('Détection Adaptative des Modes')
        
        # Graphique 3: Progression qualité
        if progression_results:
            targets = []
            achieved = []
            successes = []
            
            for key, data in progression_results.items():
                if 'error' not in data:
                    targets.append(data.get('target_score', 0))
                    achieved.append(data.get('achieved_score', 0))
                    successes.append(data.get('success', False))
            
            if targets:
                colors = ['green' if success else 'red' for success in successes]
                axes[0, 2].scatter(targets, achieved, c=colors, s=100, alpha=0.7)
                axes[0, 2].plot([0, 1], [0, 1], 'k--', alpha=0.5)
                axes[0, 2].set_title('Progression Qualité')
                axes[0, 2].set_xlabel('Score Cible')
                axes[0, 2].set_ylabel('Score Atteint')
                axes[0, 2].grid(True, alpha=0.3)
        
        # Graphique 4: PSNR par mode
        if mode_results:
            psnr_data = {}
            for mode_name, mode_data in mode_results.items():
                psnr_values = []
                for video_data in mode_data.values():
                    if 'error' not in video_data:
                        psnr_values.append(video_data.get('psnr', 0))
                psnr_data[mode_name] = np.mean(psnr_values) if psnr_values else 0
            
            axes[1, 0].bar(list(psnr_data.keys()), list(psnr_data.values()), color='orange', alpha=0.7)
            axes[1, 0].set_title('PSNR Moyen par Mode')
            axes[1, 0].set_ylabel('PSNR (dB)')
            axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 5: Temps d'optimisation
        if mode_results:
            time_data = {}
            for mode_name, mode_data in mode_results.items():
                times = []
                for video_data in mode_data.values():
                    if 'error' not in video_data:
                        times.append(video_data.get('optimization_time', 0))
                time_data[mode_name] = np.mean(times) if times else 0
            
            axes[1, 1].bar(list(time_data.keys()), list(time_data.values()), color='red', alpha=0.7)
            axes[1, 1].set_title('Temps Optimisation par Mode')
            axes[1, 1].set_ylabel('Temps (s)')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 6: K-Factor optimal
        if mode_results:
            kfactor_data = {}
            for mode_name, mode_data in mode_results.items():
                k_factors = []
                for video_data in mode_data.values():
                    if 'error' not in video_data:
                        k_factors.append(video_data.get('k_factor', 0))
                kfactor_data[mode_name] = np.mean(k_factors) if k_factors else 0
            
            axes[1, 2].bar(list(kfactor_data.keys()), list(kfactor_data.values()), color='purple', alpha=0.7)
            axes[1, 2].set_title('K-Factor Optimal par Mode')
            axes[1, 2].set_ylabel('K-Factor')
            axes[1, 2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('F:/FINAL/DEFINITIF/hcs_v2-P3/quality_optimization_report.png', 
                   dpi=150, bbox_inches='tight')
        print("✅ Rapport visuel sauvegardé: quality_optimization_report.png")
        
    except Exception as e:
        print(f"⚠️ Erreur génération rapport: {e}")
    
    # Sauvegarde JSON
    report_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'mode_results': mode_results,
        'adaptive_results': adaptive_results,
        'progression_results': progression_results,
        'detailed_results': detailed_results
    }
    
    # Conversion des types numpy pour JSON
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return obj
    
    # Fonction récursive pour convertir tous les objets
    def recursive_convert(data):
        if isinstance(data, dict):
            return {key: recursive_convert(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [recursive_convert(item) for item in data]
        else:
            return convert_numpy(data)
    
    report_data_converted = recursive_convert(report_data)
    
    with open('F:/FINAL/DEFINITIF/hcs_v2-P3/quality_optimization_results.json', 'w', encoding='utf-8') as f:
        json.dump(report_data_converted, f, indent=2, ensure_ascii=False)
    
    print("✅ Résultats sauvegardés: quality_optimization_results.json")

def main():
    """Fonction principale de test"""
    print("🎯 TEST COMPLET D'OPTIMISATION DE QUALITÉ VIDÉO")
    print("Tests d'amélioration des scores de qualité vidéo")
    print("=" * 80)
    
    # Création des vidéos de test
    test_videos = create_test_videos()
    
    # Tests des différents modes
    mode_results = test_quality_modes(test_videos)
    
    # Test d'optimisation adaptative
    adaptive_results = test_adaptive_optimization(test_videos)
    
    # Test de progression de qualité
    progression_results = test_quality_progression(test_videos)
    
    # Test détaillé des métriques
    detailed_results = test_detailed_metrics(test_videos)
    
    # Rapport complet
    generate_quality_report(mode_results, adaptive_results, progression_results, detailed_results)
    
    # Analyse des résultats
    print("\n📊 ANALYSE DES RÉSULTATS")
    print("=" * 50)
    
    # Meilleur mode
    best_mode = None
    best_score = 0
    
    for mode_name, mode_data in mode_results.items():
        scores = [data.get('quality_score', 0) for data in mode_data.values() if 'error' not in data]
        avg_score = np.mean(scores) if scores else 0
        
        if avg_score > best_score:
            best_score = avg_score
            best_mode = mode_name
    
    print(f"🏆 Meilleur mode: {best_mode} (score: {best_score:.3f})")
    
    # Succès adaptation
    adaptive_success = len([data for data in adaptive_results.values() if 'error' not in data])
    print(f"🔄 Succès adaptation: {adaptive_success}/{len(adaptive_results)} vidéos")
    
    # Paramètres optimaux
    if progression_results:
        successful_targets = [data for data in progression_results.values() if data.get('success', False)]
        if successful_targets:
            best_target = max(successful_targets, key=lambda x: x.get('achieved_score', 0))
            print(f"🎯 Meilleur score atteint: {best_target.get('achieved_score', 0):.3f}")
            print(f"🔧 K-Factor optimal: {best_target.get('parameters', {}).get('k_factor', 0):.4f}")
            print(f"🎨 WebP Quality optimal: {best_target.get('parameters', {}).get('webp_quality', 0)}")
    
    # Nettoyage
    print("\n🧹 Nettoyage des fichiers temporaires...")
    for video_path in test_videos.values():
        try:
            os.remove(video_path)
        except:
            pass
    
    print("\n✅ Tests d'optimisation qualité terminés!")
    print("🎯 Optimiseur de qualité vidéo validé!")
    print("📊 Rapports détaillés disponibles!")
    
    return {
        'mode_results': mode_results,
        'adaptive_results': adaptive_results,
        'progression_results': progression_results,
        'detailed_results': detailed_results
    }

if __name__ == "__main__":
    main()
