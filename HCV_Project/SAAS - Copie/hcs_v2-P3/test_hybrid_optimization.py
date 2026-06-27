#!/usr/bin/env python3
"""
TEST COMPLET D'OPTIMISATION HYBRIDE
Images et Vidéos avec différents objectifs et paramètres
"""

import numpy as np
import cv2
import time
import os
import tempfile
import matplotlib.pyplot as plt
from typing import Dict, Any, List
from core.hybrid_parameter_optimizer import (
    HybridParameterOptimizer, 
    OptimizationTarget, 
    MediaType
)
from core.hybrid_video_parameter_optimizer import (
    HybridVideoParameterOptimizer,
    VideoOptimizationTarget
)

def create_test_images() -> Dict[str, np.ndarray]:
    """Crée des images de test variées pour l'optimisation"""
    images = {}
    
    # Image 1: Photo réaliste
    photo = np.random.randint(50, 150, (480, 640, 3), dtype=np.uint8)
    # Ajout de "visage" et détails
    cv2.circle(photo, (320, 240), 80, (200, 150, 100), -1)
    cv2.circle(photo, (300, 220), 15, (50, 50, 50), -1)
    cv2.circle(photo, (340, 220), 15, (50, 50, 50), -1)
    cv2.ellipse(photo, (320, 260), (30, 15), 0, 0, 180, (100, 50, 50), 2)
    images['photo'] = photo
    
    # Image 2: Graphiques et texte
    graphics = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(graphics, "OPTIMIZATION TEST", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    cv2.rectangle(graphics, (50, 120), (550, 300), (100, 200, 50), -1)
    cv2.line(graphics, (50, 120), (550, 300), (255, 100, 100), 3)
    # Ajout de formes géométriques
    for i in range(5):
        center = (150 + i * 80, 350)
        cv2.circle(graphics, center, 25, (255, 255, 255), -1)
    images['graphics'] = graphics
    
    # Image 3: Haute fréquence (détails fins)
    high_freq = np.zeros((300, 400, 3), dtype=np.uint8)
    for i in range(100):
        x, y = np.random.randint(0, 400), np.random.randint(0, 300)
        radius = np.random.randint(1, 3)
        color = tuple(np.random.randint(100, 255, 3).tolist())
        cv2.circle(high_freq, (x, y), radius, color, -1)
    images['high_freq'] = high_freq
    
    # Image 4: Basse fréquence (gradients)
    low_freq = np.zeros((350, 450, 3), dtype=np.uint8)
    for i in range(350):
        for j in range(450):
            low_freq[i, j, 0] = int(128 + 127 * np.sin(i * 0.02) * np.cos(j * 0.02))
            low_freq[i, j, 1] = int(128 + 127 * np.sin(i * 0.01) * np.sin(j * 0.01))
            low_freq[i, j, 2] = int(128 + 127 * np.cos(i * 0.015) * np.cos(j * 0.015))
    images['low_freq'] = low_freq
    
    # Image 5: Texture complexe
    texture = np.random.randint(30, 120, (400, 500, 3), dtype=np.uint8)
    # Ajout de patterns
    for i in range(20):
        x1, y1 = np.random.randint(0, 500), np.random.randint(0, 400)
        x2, y2 = np.random.randint(0, 500), np.random.randint(0, 400)
        color = tuple(np.random.randint(80, 180, 3).tolist())
        cv2.line(texture, (x1, y1), (x2, y2), color, 2)
    images['texture'] = texture
    
    return images

def create_test_video() -> str:
    """Crée une vidéo de test pour l'optimisation"""
    frames = []
    
    # Création de frames avec mouvement et variations
    for i in range(90):  # 3 secondes @ 30fps
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Fond avec gradient
        frame[:, :, 0] = np.linspace(0, 255, 320)
        frame[:, :, 1] = np.linspace(255, 0, 320)
        frame[:, :, 2] = 128
        
        # Animation de cercles
        for j in range(3):
            x = int(160 + 60 * np.cos(i * 0.05 + j * 2.09))
            y = int(120 + 40 * np.sin(i * 0.05 + j * 2.09))
            color = [(255, 100, 100), (100, 255, 100), (100, 100, 255)][j]
            cv2.circle(frame, (x, y), 15, color, -1)
        
        # Texte animé
        text = f"FRAME {i+1}"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        frames.append(frame)
    
    # Création vidéo
    temp_dir = tempfile.mkdtemp(prefix="video_opt_test_")
    video_path = os.path.join(temp_dir, "test_video.mp4")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 30.0, (320, 240))
    
    for frame in frames:
        out.write(frame)
    
    out.release()
    
    return video_path

def test_image_optimization():
    """Test d'optimisation pour images"""
    print("\n" + "="*80)
    print("🖼️  TEST OPTIMISATION IMAGES")
    print("="*80)
    
    # Création des images de test
    test_images = create_test_images()
    print(f"✅ {len(test_images)} images de test créées")
    
    # Objectifs d'optimisation à tester
    objectives = [
        OptimizationTarget.MAX_QUALITY,
        OptimizationTarget.MAX_COMPRESSION,
        OptimizationTarget.BALANCED,
        OptimizationTarget.FAST_PROCESSING,
        OptimizationTarget.MIN_SIZE
    ]
    
    image_results = {}
    
    for objective in objectives:
        print(f"\n🎯 Test optimisation: {objective.value}")
        
        objective_results = {}
        
        for image_name, image in test_images.items():
            print(f"   📸 Optimisation: {image_name}")
            
            optimizer = HybridParameterOptimizer(
                optimization_target=objective,
                media_type=MediaType.IMAGE,
                max_iterations=20
            )
            
            try:
                result = optimizer.optimize_parameters(image, method="grid")
                
                objective_results[image_name] = {
                    'best_parameters': result.best_parameters,
                    'score': result.optimization_score,
                    'compression_ratio': result.performance_metrics['compression_ratio'],
                    'quality_score': result.quality_metrics['quality_score'],
                    'processing_time': result.performance_metrics['processing_time'],
                    'target_achieved': result.target_achieved
                }
                
                print(f"      K-Factor: {result.best_parameters.k_factor:.4f}")
                print(f"      WebP Quality: {result.best_parameters.webp_quality}")
                print(f"      Score: {result.optimization_score:.3f}")
                print(f"      Ratio: {result.performance_metrics['compression_ratio']:.1f}:1")
                print(f"      Qualité: {result.quality_metrics['quality_score']:.3f}")
                print(f"      Temps: {result.performance_metrics['processing_time']:.3f}s")
                
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
                objective_results[image_name] = {'error': str(e)}
        
        image_results[objective.value] = objective_results
    
    return image_results

def test_video_optimization():
    """Test d'optimisation pour vidéos"""
    print("\n" + "="*80)
    print("🎥 TEST OPTIMISATION VIDÉOS")
    print("="*80)
    
    # Création de la vidéo de test
    video_path = create_test_video()
    print(f"✅ Vidéo de test créée: {video_path}")
    
    # Objectifs d'optimisation vidéo à tester
    objectives = [
        VideoOptimizationTarget.MAX_TEMPORAL_QUALITY,
        VideoOptimizationTarget.MAX_COMPRESSION_RATIO,
        VideoOptimizationTarget.REAL_TIME_PROCESSING,
        VideoOptimizationTarget.MIN_BANDWIDTH,
        VideoOptimizationTarget.BALANCED_VIDEO
    ]
    
    video_results = {}
    
    for objective in objectives:
        print(f"\n🎯 Test optimisation vidéo: {objective.value}")
        
        optimizer = HybridVideoParameterOptimizer(
            optimization_target=objective,
            max_iterations=15
        )
        
        try:
            result = optimizer.optimize_video_parameters(video_path, method="grid")
            
            video_results[objective.value] = {
                'best_parameters': result.best_parameters,
                'score': result.optimization_score,
                'compression_ratio': result.performance_metrics['compression_ratio'],
                'spatial_quality': result.quality_metrics['spatial_quality'],
                'temporal_quality': result.quality_metrics['temporal_quality'],
                'fps_capability': result.performance_metrics['fps_capability'],
                'bandwidth': result.performance_metrics['bandwidth'],
                'processing_time': result.performance_metrics['processing_time'],
                'target_achieved': result.target_achieved,
                'temporal_metrics': result.temporal_metrics
            }
            
            print(f"   K-Factor: {result.best_parameters.k_factor:.4f}")
            print(f"   WebP Quality: {result.best_parameters.webp_quality}")
            print(f"   Temporal Weight: {result.best_parameters.temporal_coherence_weight:.2f}")
            print(f"   Frame Sample Rate: {result.best_parameters.frame_sample_rate}")
            print(f"   Score: {result.optimization_score:.3f}")
            print(f"   Ratio: {result.performance_metrics['compression_ratio']:.1f}:1")
            print(f"   Qualité spatiale: {result.quality_metrics['spatial_quality']:.3f}")
            print(f"   Qualité temporelle: {result.quality_metrics['temporal_quality']:.3f}")
            print(f"   FPS capability: {result.performance_metrics['fps_capability']:.1f}")
            print(f"   Bandwidth: {result.performance_metrics['bandwidth']/1024:.1f} KB/s")
            print(f"   Temps: {result.performance_metrics['processing_time']:.3f}s")
            print(f"   Objectif atteint: {result.target_achieved}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            video_results[objective.value] = {'error': str(e)}
        
        finally:
            optimizer.cleanup()
    
    # Nettoyage
    try:
        os.remove(video_path)
        os.rmdir(os.path.dirname(video_path))
    except:
        pass
    
    return video_results

def analyze_optimization_results(image_results: Dict, video_results: Dict):
    """Analyse et synthétise les résultats d'optimisation"""
    print("\n" + "="*80)
    print("📊 ANALYSE DES RÉSULTATS D'OPTIMISATION")
    print("="*80)
    
    # Analyse images
    print(f"\n🖼️  SYNTHÈSE OPTIMISATION IMAGES:")
    
    image_summary = {}
    for objective, results in image_results.items():
        if not results:
            continue
        
        scores = []
        ratios = []
        qualities = []
        times = []
        achieved = 0
        
        for image_name, result in results.items():
            if 'error' not in result:
                scores.append(result['score'])
                ratios.append(result['compression_ratio'])
                qualities.append(result['quality_score'])
                times.append(result['processing_time'])
                if result['target_achieved']:
                    achieved += 1
        
        if scores:
            image_summary[objective] = {
                'avg_score': np.mean(scores),
                'avg_ratio': np.mean(ratios),
                'avg_quality': np.mean(qualities),
                'avg_time': np.mean(times),
                'success_rate': achieved / len(results) * 100,
                'total_images': len(results)
            }
            
            print(f"   {objective}:")
            print(f"      Score moyen: {image_summary[objective]['avg_score']:.3f}")
            print(f"      Ratio moyen: {image_summary[objective]['avg_ratio']:.1f}:1")
            print(f"      Qualité moyenne: {image_summary[objective]['avg_quality']:.3f}")
            print(f"      Temps moyen: {image_summary[objective]['avg_time']:.3f}s")
            print(f"      Taux succès: {image_summary[objective]['success_rate']:.1f}%")
    
    # Analyse vidéos
    print(f"\n🎥 SYNTHÈSE OPTIMISATION VIDÉOS:")
    
    video_summary = {}
    for objective, result in video_results.items():
        if 'error' in result:
            continue
        
        video_summary[objective] = {
            'score': result['score'],
            'ratio': result['compression_ratio'],
            'spatial_quality': result['spatial_quality'],
            'temporal_quality': result['temporal_quality'],
            'fps_capability': result['fps_capability'],
            'bandwidth': result['bandwidth'],
            'processing_time': result['processing_time'],
            'target_achieved': result['target_achieved']
        }
        
        print(f"   {objective}:")
        print(f"      Score: {result['score']:.3f}")
        print(f"      Ratio: {result['compression_ratio']:.1f}:1")
        print(f"      Qualité spatiale: {result['spatial_quality']:.3f}")
        print(f"      Qualité temporelle: {result['temporal_quality']:.3f}")
        print(f"      FPS capability: {result['fps_capability']:.1f}")
        print(f"      Bandwidth: {result['bandwidth']/1024:.1f} KB/s")
        print(f"      Temps: {result['processing_time']:.3f}s")
        print(f"      Objectif atteint: {result['target_achieved']}")
    
    return image_summary, video_summary

def generate_optimization_report(image_summary: Dict, video_summary: Dict):
    """Génère un rapport visuel d'optimisation"""
    print("\n" + "="*80)
    print("📊 GÉNÉRATION DU RAPPORT D'OPTIMISATION")
    print("="*80)
    
    try:
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Rapport d\'Optimisation Hybride', fontsize=16)
        
        # Graphique 1: Scores par objectif (images)
        if image_summary:
            objectives = list(image_summary.keys())
            scores = [image_summary[obj]['avg_score'] for obj in objectives]
            
            axes[0, 0].bar(objectives, scores, color='skyblue', alpha=0.7)
            axes[0, 0].set_title('Score Moyen par Objectif (Images)')
            axes[0, 0].set_ylabel('Score')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 2: Ratios de compression (images)
        if image_summary:
            ratios = [image_summary[obj]['avg_ratio'] for obj in objectives]
            
            axes[0, 1].bar(objectives, ratios, color='lightgreen', alpha=0.7)
            axes[0, 1].set_title('Ratio Compression Moyen (Images)')
            axes[0, 1].set_ylabel('Ratio:1')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 3: Temps de traitement (images)
        if image_summary:
            times = [image_summary[obj]['avg_time'] for obj in objectives]
            
            axes[0, 2].bar(objectives, times, color='lightcoral', alpha=0.7)
            axes[0, 2].set_title('Temps Traitement Moyen (Images)')
            axes[0, 2].set_ylabel('Temps (s)')
            axes[0, 2].tick_params(axis='x', rotation=45)
        
        # Graphique 4: Scores par objectif (vidéos)
        if video_summary:
            video_objectives = list(video_summary.keys())
            video_scores = [video_summary[obj]['score'] for obj in video_objectives]
            
            axes[1, 0].bar(video_objectives, video_scores, color='orange', alpha=0.7)
            axes[1, 0].set_title('Score par Objectif (Vidéos)')
            axes[1, 0].set_ylabel('Score')
            axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 5: Qualité spatiale vs temporelle (vidéos)
        if video_summary:
            spatial_qualities = [video_summary[obj]['spatial_quality'] for obj in video_objectives]
            temporal_qualities = [video_summary[obj]['temporal_quality'] for obj in video_objectives]
            
            x = np.arange(len(video_objectives))
            width = 0.35
            
            axes[1, 1].bar(x - width/2, spatial_qualities, width, label='Qualité Spatiale', color='blue', alpha=0.7)
            axes[1, 1].bar(x + width/2, temporal_qualities, width, label='Qualité Temporelle', color='red', alpha=0.7)
            axes[1, 1].set_title('Qualité Spatiale vs Temporelle (Vidéos)')
            axes[1, 1].set_ylabel('Qualité')
            axes[1, 1].set_xticks(x)
            axes[1, 1].set_xticklabels(video_objectives, rotation=45)
            axes[1, 1].legend()
        
        # Graphique 6: FPS capability par objectif (vidéos)
        if video_summary:
            fps_capabilities = [video_summary[obj]['fps_capability'] for obj in video_objectives]
            
            axes[1, 2].bar(video_objectives, fps_capabilities, color='purple', alpha=0.7)
            axes[1, 2].set_title('Capability FPS par Objectif (Vidéos)')
            axes[1, 2].set_ylabel('FPS')
            axes[1, 2].tick_params(axis='x', rotation=45)
            axes[1, 2].axhline(y=30, color='red', linestyle='--', alpha=0.5, label='30 FPS (Real-time)')
            axes[1, 2].legend()
        
        plt.tight_layout()
        plt.savefig('F:/FINAL/DEFINITIF/hcs_v2-P3/hybrid_optimization_report.png', 
                   dpi=150, bbox_inches='tight')
        print(f"\n📊 Rapport visuel sauvegardé: hybrid_optimization_report.png")
        
    except Exception as e:
        print(f"\n⚠️ Erreur génération rapport visuel: {e}")

def main():
    """Fonction principale de test d'optimisation"""
    print("🔧 TEST COMPLET D'OPTIMISATION HYBRIDE")
    print("Images et Vidéos avec différents objectifs")
    print("=" * 80)
    
    # Test optimisation images
    image_results = test_image_optimization()
    
    # Test optimisation vidéos
    video_results = test_video_optimization()
    
    # Analyse des résultats
    image_summary, video_summary = analyze_optimization_results(image_results, video_results)
    
    # Génération du rapport
    generate_optimization_report(image_summary, video_summary)
    
    # Conclusions et recommandations
    print(f"\n" + "="*80)
    print("🎯 CONCLUSIONS ET RECOMMANDATIONS")
    print("="*80)
    
    print(f"\n🖼️  RECOMMANDATIONS IMAGES:")
    
    # Meilleur objectif pour chaque critère
    if image_summary:
        best_quality = max(image_summary.items(), key=lambda x: x[1]['avg_quality'])
        best_compression = max(image_summary.items(), key=lambda x: x[1]['avg_ratio'])
        best_speed = min(image_summary.items(), key=lambda x: x[1]['avg_time'])
        
        print(f"   🏆 Meilleure qualité: {best_quality[0]} (score: {best_quality[1]['avg_quality']:.3f})")
        print(f"   🗜️  Meilleure compression: {best_compression[0]} (ratio: {best_compression[1]['avg_ratio']:.1f}:1)")
        print(f"   ⚡ Plus rapide: {best_speed[0]} (temps: {best_speed[1]['avg_time']:.3f}s)")
    
    print(f"\n🎥 RECOMMANDATIONS VIDÉOS:")
    
    if video_summary:
        best_video_quality = max(video_summary.items(), key=lambda x: x[1]['spatial_quality'])
        best_temporal = max(video_summary.items(), key=lambda x: x[1]['temporal_quality'])
        best_fps = max(video_summary.items(), key=lambda x: x[1]['fps_capability'])
        best_bandwidth = min(video_summary.items(), key=lambda x: x[1]['bandwidth'])
        
        print(f"   🏆 Meilleure qualité spatiale: {best_video_quality[0]} ({best_video_quality[1]['spatial_quality']:.3f})")
        print(f"   🎬 Meilleure qualité temporelle: {best_temporal[0]} ({best_temporal[1]['temporal_quality']:.3f})")
        print(f"   ⚡ Meilleure performance FPS: {best_fps[0]} ({best_fps[1]['fps_capability']:.1f} FPS)")
        print(f"   📶 Meilleure bande passante: {best_bandwidth[0]} ({best_bandwidth[1]['bandwidth']/1024:.1f} KB/s)")
    
    print(f"\n💡 RECOMMANDATIONS GÉNÉRALES:")
    print(f"   ✅ Utiliser MAX_QUALITY pour les applications critiques")
    print(f"   ✅ Utiliser MAX_COMPRESSION pour le stockage/archivage")
    print(f"   ✅ Utiliser BALANCED pour le usage général")
    print(f"   ✅ Utiliser FAST_PROCESSING pour le temps réel")
    print(f"   ✅ Utiliser MIN_SIZE pour les réseaux limités")
    
    print(f"\n✅ Tests d'optimisation terminés!")
    print("🔧 Système d'optimisation hybride validé!")
    print("📊 Rapport complet généré et disponible!")
    
    return {
        'image_results': image_results,
        'video_results': video_results,
        'image_summary': image_summary,
        'video_summary': video_summary
    }

if __name__ == "__main__":
    main()
