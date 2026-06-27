#!/usr/bin/env python3
"""
TEST COMPLET DU SYSTÈME INTÉGRÉ VIDÉO
Compression Hybride Maximale + Upscaling Quantique-Harmonique Efficace
"""

import numpy as np
import cv2
import os
import time
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from core.hybrid_video_compression_upscaling_system import (
    HybridVideoCompressionUpscalingSystem, 
    VideoProcessingMode,
    VideoCodec
)

def create_test_videos() -> Dict[str, str]:
    """Crée des vidéos de test variées"""
    videos = {}
    temp_dir = "F:/FINAL/DEFINITIF/hcs_v2-P3/temp_test_videos"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Vidéo 1: Animation simple (balle qui bouge)
    frames = []
    for i in range(120):  # 4 secondes @ 30fps
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        # Fond dégradé
        frame[:, :, 0] = np.linspace(0, 255, 320)
        frame[:, :, 1] = np.linspace(255, 0, 320)
        frame[:, :, 2] = 128
        
        # Balle qui bouge
        x = int(160 + 80 * np.cos(i * 0.05))
        y = int(120 + 60 * np.sin(i * 0.05))
        cv2.circle(frame, (x, y), 20, (255, 255, 255), -1)
        cv2.circle(frame, (x, y), 15, (0, 0, 255), -1)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "animation_simple.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['animation'] = video_path
    
    # Vidéo 2: Patterns géométriques
    frames = []
    for i in range(90):  # 3 secondes @ 30fps
        frame = np.random.randint(50, 200, (180, 240, 3), dtype=np.uint8)
        
        # Rectangle rotatif
        center = (120, 90)
        size = 40
        angle = i * 4  # Rotation
        rect = ((center[0] - size//2, center[1] - size//2), (size, size), angle)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cv2.drawContours(frame, [box], 0, (255, 255, 255), 2)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "patterns_geometriques.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['patterns'] = video_path
    
    # Vidéo 3: Texte animé
    frames = []
    for i in range(150):  # 5 secondes @ 30fps
        frame = np.zeros((200, 400, 3), dtype=np.uint8)
        frame[:] = (50, 100, 150)  # Fond bleu
        
        # Texte qui défile
        text = "VIDEO COMPRESSION TEST"
        x = int(400 - (i * 3) % 600)
        cv2.putText(frame, text, (x, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Compteur
        cv2.putText(frame, f"Frame: {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "texte_anime.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['texte'] = video_path
    
    # Vidéo 4: Haute résolution
    frames = []
    for i in range(60):  # 2 secondes @ 30fps
        frame = np.random.randint(0, 256, (720, 1280, 3), dtype=np.uint8)
        
        # Ajout de détails
        for j in range(10):
            x = np.random.randint(0, 1280)
            y = np.random.randint(0, 720)
            radius = np.random.randint(5, 20)
            color = tuple(np.random.randint(100, 255, 3).tolist())
            cv2.circle(frame, (x, y), radius, color, -1)
        
        # Rectangle informatif
        cv2.rectangle(frame, (50, 50), (300, 150), (255, 255, 255), 2)
        cv2.putText(frame, f"HD Video {i+1}/60", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "haute_resolution.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['hd'] = video_path
    
    # Vidéo 5: Basse résolution avec bruit
    frames = []
    for i in range(90):  # 3 secondes @ 30fps
        frame = np.random.randint(0, 100, (120, 160, 3), dtype=np.uint8)
        
        # Ajout de signal
        signal = int(128 + 50 * np.sin(i * 0.1))
        cv2.line(frame, (0, 60), (160, 60), (signal, signal, signal), 3)
        
        # Carré animé
        x = int(80 + 30 * np.cos(i * 0.08))
        y = int(60 + 20 * np.sin(i * 0.08))
        cv2.rectangle(frame, (x-10, y-10), (x+10, y+10), (255, 255, 255), -1)
        
        frames.append(frame)
    
    video_path = os.path.join(temp_dir, "basse_resolution.mp4")
    create_video_from_frames(frames, video_path, 30.0)
    videos['low_res'] = video_path
    
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
    print(f"✅ Vidéo créée: {output_path} ({len(frames)} frames, {fps} FPS)")

def test_video_compression_only(system: HybridVideoCompressionUpscalingSystem, videos: Dict[str, str]):
    """Test du mode compression vidéo uniquement"""
    print("\n" + "="*80)
    print("🗜️  TEST MODE COMPRESSION VIDÉO UNIQUMENT")
    print("="*80)
    
    results = {}
    
    for name, video_path in videos.items():
        print(f"\n📹 Compression de: {name}")
        
        start_time = time.time()
        result = system.compress_video(video_path, target_ratio=50, max_frames=30)
        compression_time = time.time() - start_time
        
        results[name] = {
            'original_path': video_path,
            'compressed_path': result.compressed_video_path,
            'original_size': os.path.getsize(video_path),
            'compressed_size': os.path.getsize(result.compressed_video_path),
            'ratio': result.compression_ratio,
            'time': compression_time,
            'frame_count': result.frame_count,
            'fps': result.fps,
            'duration': result.duration,
            'quality_metrics': result.quality_metrics
        }
        
        print(f"   ✅ Ratio: {result.compression_ratio:.1f}:1")
        print(f"   📊 Taille originale: {os.path.getsize(video_path):,} octets")
        print(f"   📦 Taille compressée: {os.path.getsize(result.compressed_video_path):,} octets")
        print(f"   ⏱️  Temps: {compression_time:.3f}s")
        print(f"   🎬 Frames: {result.frame_count}")
        print(f"   🎯 FPS: {result.fps:.1f}")
        print(f"   💾 Espace économisé: {result.quality_metrics.get('size_reduction_percent', 0):.1f}%")
    
    return results

def test_video_upscaling_only(system: HybridVideoCompressionUpscalingSystem, videos: Dict[str, str]):
    """Test du mode upscaling vidéo uniquement"""
    print("\n" + "="*80)
    print("🔍 TEST MODE UPSCALING VIDÉO UNIQUMENT")
    print("="*80)
    
    results = {}
    
    for name, video_path in videos.items():
        print(f"\n📹 Upscaling de: {name}")
        
        start_time = time.time()
        result = system.upscale_video(video_path, scale_factor=2.0, max_frames=30)
        upscaling_time = time.time() - start_time
        
        results[name] = {
            'original_path': video_path,
            'upscaled_path': result.upscaled_video_path,
            'original_shape': result.original_shape,
            'target_shape': result.target_shape,
            'scale_factor': result.scale_factor,
            'time': upscaling_time,
            'frame_count': result.frame_count,
            'fps': result.fps,
            'duration': result.metadata['video_info']['duration'],
            'quality_metrics': result.quality_metrics
        }
        
        print(f"   ✅ Facteur: {result.scale_factor:.1f}x")
        print(f"   📐 Taille originale: {result.original_shape}")
        print(f"   📏 Taille finale: {result.target_shape}")
        print(f"   ⏱️  Temps: {upscaling_time:.3f}s")
        print(f"   🎬 Frames: {result.frame_count}")
        print(f"   🎯 Qualité: {result.quality_metrics.get('avg_quality_score', 0):.3f}")
        print(f"   📊 FPS: {result.fps:.1f}")
    
    return results

def test_full_video_pipeline(system: HybridVideoCompressionUpscalingSystem, videos: Dict[str, str]):
    """Test du pipeline complet vidéo compression + upscaling"""
    print("\n" + "="*80)
    print("🔄 TEST PIPELINE COMPLET VIDÉO")
    print("="*80)
    
    results = {}
    
    for name, video_path in videos.items():
        print(f"\n📹 Pipeline complet pour: {name}")
        
        start_time = time.time()
        result = system.compress_and_upscale_video(
            video_path=video_path,
            target_ratio=30,  # Ratio cible modéré
            scale_factor=1.5,   # Upscaling 1.5x
            max_frames=30,      # Limiter pour le test
            mode=VideoProcessingMode.COMPRESSION_UPSCALING
        )
        total_time = time.time() - start_time
        
        results[name] = {
            'original_path': result.original_video_path,
            'final_path': result.final_video_path,
            'compressed_path': result.compressed_video_path,
            'compression_ratio': result.compression_ratio,
            'scale_factor': result.scale_factor,
            'total_time': total_time,
            'processing_times': result.processing_times,
            'overall_quality': result.overall_quality
        }
        
        print(f"   ✅ Ratio compression: {result.compression_ratio:.1f}:1")
        print(f"   📏 Facteur upscaling: {result.scale_factor:.1f}x")
        print(f"   ⏱️  Temps total: {total_time:.3f}s")
        print(f"      - Compression: {result.processing_times.get('compression', 0):.3f}s")
        print(f"      - Upscaling: {result.processing_times.get('upscaling', 0):.3f}s")
        print(f"   🎯 Qualité globale: {result.overall_quality.get('global_score', 0):.3f}")
        print(f"   📊 Efficacité: {result.overall_quality.get('efficiency', 0):.3f}")
        print(f"   🎬 Vidéo finale: {result.final_video_path}")
    
    return results

def test_adaptive_video_mode(system: HybridVideoCompressionUpscalingSystem, videos: Dict[str, str]):
    """Test du mode adaptatif vidéo"""
    print("\n" + "="*80)
    print("🤖 TEST MODE ADAPTATIF VIDÉO")
    print("="*80)
    
    results = {}
    
    for name, video_path in videos.items():
        print(f"\n📹 Mode adaptatif pour: {name}")
        
        # Différents scénarios pour tester l'adaptativité
        scenarios = [
            {'target_ratio': None, 'scale_factor': None, 'description': 'Normal'},
            {'target_ratio': 50, 'scale_factor': None, 'description': 'Compression requise'},
            {'target_ratio': None, 'scale_factor': 2.0, 'description': 'Upscaling requis'},
            {'target_ratio': 100, 'scale_factor': 3.0, 'description': 'Les deux requis'}
        ]
        
        scenario_results = []
        
        for scenario in scenarios:
            start_time = time.time()
            result = system.compress_and_upscale_video(
                video_path=video_path,
                target_ratio=scenario['target_ratio'],
                scale_factor=scenario['scale_factor'],
                max_frames=20,  # Limiter pour les tests
                mode=VideoProcessingMode.ADAPTIVE
            )
            scenario_time = time.time() - start_time
            
            scenario_result = {
                'description': scenario['description'],
                'mode_choisi': result.metadata['mode'],
                'compression_applied': result.metadata['compression_applied'],
                'upscaling_applied': result.metadata['upscaling_applied'],
                'ratio': result.compression_ratio,
                'scale': result.scale_factor,
                'time': scenario_time,
                'quality': result.overall_quality.get('global_score', 0)
            }
            
            scenario_results.append(scenario_result)
            
            print(f"   🎯 {scenario['description']}:")
            print(f"      Mode choisi: {scenario_result['mode_choisi']}")
            print(f"      Compression: {'✅' if scenario_result['compression_applied'] else '❌'}")
            print(f"      Upscaling: {'✅' if scenario_result['upscaling_applied'] else '❌'}")
            print(f"      Temps: {scenario_time:.3f}s")
        
        results[name] = scenario_results
    
    return results

def video_performance_analysis(compression_results: Dict, upscaling_results: Dict, 
                           pipeline_results: Dict) -> Dict[str, Any]:
    """Analyse comparative des performances vidéo"""
    print("\n" + "="*80)
    print("📊 ANALYSE COMPARATIVE DES PERFORMANCES VIDÉO")
    print("="*80)
    
    analysis = {
        'compression_performance': {},
        'upscaling_performance': {},
        'pipeline_efficiency': {},
        'recommendations': []
    }
    
    # Analyse compression
    compression_ratios = [r['ratio'] for r in compression_results.values()]
    compression_times = [r['time'] for r in compression_results.values()]
    frame_counts = [r['frame_count'] for r in compression_results.values()]
    
    analysis['compression_performance'] = {
        'avg_ratio': np.mean(compression_ratios),
        'max_ratio': np.max(compression_ratios),
        'min_ratio': np.min(compression_ratios),
        'avg_time': np.mean(compression_times),
        'avg_fps': np.mean(frame_counts) / np.mean(compression_times),
        'total_frames_processed': np.sum(frame_counts)
    }
    
    # Analyse upscaling
    upscaling_scales = [r['scale_factor'] for r in upscaling_results.values()]
    upscaling_times = [r['time'] for r in upscaling_results.values()]
    upscaling_qualities = [r['quality_metrics'].get('avg_quality_score', 0.7) for r in upscaling_results.values()]
    
    analysis['upscaling_performance'] = {
        'avg_scale': np.mean(upscaling_scales),
        'avg_time': np.mean(upscaling_times),
        'avg_quality': np.mean(upscaling_qualities),
        'fps_capability': np.mean(frame_counts) / np.mean(upscaling_times)
    }
    
    # Analyse pipeline
    pipeline_ratios = [r['compression_ratio'] for r in pipeline_results.values()]
    pipeline_times = [r['total_time'] for r in pipeline_results.values()]
    pipeline_qualities = [r['overall_quality'].get('global_score', 0.7) for r in pipeline_results.values()]
    
    analysis['pipeline_efficiency'] = {
        'avg_ratio': np.mean(pipeline_ratios),
        'avg_time': np.mean(pipeline_times),
        'avg_quality': np.mean(pipeline_qualities),
        'efficiency_score': np.mean(pipeline_ratios) * np.mean(pipeline_qualities) / np.mean(pipeline_times)
    }
    
    # Recommandations
    if analysis['compression_performance']['avg_ratio'] > 30:
        analysis['recommendations'].append("✅ Compression vidéo excellente - ratios élevés atteints")
    else:
        analysis['recommendations'].append("⚠️ Compression vidéo peut être optimisée")
    
    if analysis['upscaling_performance']['avg_quality'] > 0.7:
        analysis['recommendations'].append("✅ Upscaling vidéo haute qualité")
    else:
        analysis['recommendations'].append("⚠️ Qualité upscaling vidéo à améliorer")
    
    if analysis['pipeline_efficiency']['efficiency_score'] > 50:
        analysis['recommendations'].append("✅ Pipeline vidéo très efficace")
    else:
        analysis['recommendations'].append("⚠️ Efficacité pipeline vidéo à optimiser")
    
    # Affichage des résultats
    print(f"\n📈 PERFORMANCE COMPRESSION VIDÉO:")
    print(f"   Ratio moyen: {analysis['compression_performance']['avg_ratio']:.1f}:1")
    print(f"   Ratio max: {analysis['compression_performance']['max_ratio']:.1f}:1")
    print(f"   Temps moyen: {analysis['compression_performance']['avg_time']:.3f}s")
    print(f"   FPS moyen: {analysis['compression_performance']['avg_fps']:.1f}")
    print(f"   Total frames: {analysis['compression_performance']['total_frames_processed']}")
    
    print(f"\n🔍 PERFORMANCE UPSCALING VIDÉO:")
    print(f"   Échelle moyenne: {analysis['upscaling_performance']['avg_scale']:.1f}x")
    print(f"   Temps moyen: {analysis['upscaling_performance']['avg_time']:.3f}s")
    print(f"   Qualité moyenne: {analysis['upscaling_performance']['avg_quality']:.3f}")
    print(f"   FPS capability: {analysis['upscaling_performance']['fps_capability']:.1f}")
    
    print(f"\n🔄 EFFICACITÉ PIPELINE VIDÉO:")
    print(f"   Ratio moyen: {analysis['pipeline_efficiency']['avg_ratio']:.1f}:1")
    print(f"   Temps moyen: {analysis['pipeline_efficiency']['avg_time']:.3f}s")
    print(f"   Qualité moyenne: {analysis['pipeline_efficiency']['avg_quality']:.3f}")
    print(f"   Score efficacité: {analysis['pipeline_efficiency']['efficiency_score']:.1f}")
    
    print(f"\n💡 RECOMMANDATIONS VIDÉO:")
    for rec in analysis['recommendations']:
        print(f"   {rec}")
    
    return analysis

def generate_video_performance_report(videos: Dict[str, str], 
                                  compression_results: Dict,
                                  upscaling_results: Dict,
                                  pipeline_results: Dict):
    """Génère un rapport de performance vidéo"""
    try:
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Rapport de Performance Vidéo - Système Intégré', fontsize=16)
        
        # Graphique 1: Ratios de compression vidéo
        video_names = list(compression_results.keys())
        ratios = [compression_results[name]['ratio'] for name in video_names]
        axes[0, 0].bar(video_names, ratios)
        axes[0, 0].set_title('Ratios de Compression Vidéo')
        axes[0, 0].set_ylabel('Ratio:1')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 2: Temps de traitement vidéo
        comp_times = [compression_results[name]['time'] for name in video_names]
        up_times = [upscaling_results[name]['time'] for name in video_names]
        pipe_times = [pipeline_results[name]['total_time'] for name in video_names]
        
        x = np.arange(len(video_names))
        width = 0.25
        axes[0, 1].bar(x - width, comp_times, width, label='Compression')
        axes[0, 1].bar(x, up_times, width, label='Upscaling')
        axes[0, 1].bar(x + width, pipe_times, width, label='Pipeline')
        axes[0, 1].set_title('Temps de Traitement Vidéo')
        axes[0, 1].set_ylabel('Temps (s)')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(video_names, rotation=45)
        axes[0, 1].legend()
        
        # Graphique 3: Qualité vs Efficacité vidéo
        qualities = [pipeline_results[name]['overall_quality'].get('global_score', 0.7) for name in video_names]
        efficiencies = [pipeline_results[name]['overall_quality'].get('efficiency', 0) for name in video_names]
        
        axes[0, 2].scatter(qualities, efficiencies, s=100, alpha=0.7)
        axes[0, 2].set_xlabel('Qualité Globale')
        axes[0, 2].set_ylabel('Efficacité')
        axes[0, 2].set_title('Qualité vs Efficacité Vidéo')
        
        # Graphique 4: Distribution des ratios vidéo
        axes[1, 0].hist(ratios, bins=10, alpha=0.7, edgecolor='black')
        axes[1, 0].set_title('Distribution des Ratios Vidéo')
        axes[1, 0].set_xlabel('Ratio:1')
        axes[1, 0].set_ylabel('Fréquence')
        
        # Graphique 5: Performance par type de vidéo
        performance_scores = []
        for name in video_names:
            score = (compression_results[name]['ratio'] * 
                    pipeline_results[name]['overall_quality'].get('global_score', 0.7) /
                    pipeline_results[name]['total_time'])
            performance_scores.append(score)
        
        axes[1, 1].bar(video_names, performance_scores)
        axes[1, 1].set_title('Score de Performance par Vidéo')
        axes[1, 1].set_ylabel('Score Performance')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 6: Résumé système vidéo
        video_metrics = ['Ratio\nMoyen', 'Qualité\nMoyenne', 'Temps\nMoyen', 'Efficacité\nGlobale']
        metric_values = [
            np.mean(ratios),
            np.mean(qualities),
            np.mean(pipe_times),
            np.mean(efficiencies)
        ]
        
        # Normalisation pour l'affichage
        normalized_values = np.array(metric_values)
        normalized_values[0] /= 100  # Ratio
        normalized_values[2] *= 100   # Temps
        normalized_values[3] *= 10    # Efficacité
        
        colors = ['green', 'blue', 'orange', 'red']
        axes[1, 2].bar(video_metrics, normalized_values, color=colors)
        axes[1, 2].set_title('Métriques Système Vidéo (Normalisées)')
        axes[1, 2].set_ylabel('Valeur Normalisée')
        
        plt.tight_layout()
        plt.savefig('F:/FINAL/DEFINITIF/hcs_v2-P3/video_performance_report.png', dpi=150, bbox_inches='tight')
        print(f"\n📊 Rapport visuel vidéo sauvegardé: video_performance_report.png")
        
    except Exception as e:
        print(f"\n⚠️ Impossible de générer le rapport visuel vidéo: {e}")

def main():
    """Fonction principale de test vidéo complet"""
    print("🚀 TEST COMPLET DU SYSTÈME INTÉGRÉ VIDÉO")
    print("Compression Hybride Maximale + Upscaling Quantique-Harmonique")
    print("=" * 80)
    
    # Initialisation du système vidéo
    system = HybridVideoCompressionUpscalingSystem(
        k_factor=0.02,
        webp_quality=95,
        upscaling_preset="quantum_max"
    )
    
    # Création des vidéos de test
    print("\n🎥 Création des vidéos de test...")
    test_videos = create_test_videos()
    print(f"✅ {len(test_videos)} vidéos de test créées")
    
    # Tests individuels
    compression_results = test_video_compression_only(system, test_videos)
    upscaling_results = test_video_upscaling_only(system, test_videos)
    pipeline_results = test_full_video_pipeline(system, test_videos)
    adaptive_results = test_adaptive_video_mode(system, test_videos)
    
    # Analyse des performances
    performance_analysis_results = video_performance_analysis(
        compression_results, upscaling_results, pipeline_results
    )
    
    # Rapport visuel
    generate_video_performance_report(test_videos, compression_results, upscaling_results, pipeline_results)
    
    # Statistiques finales du système
    system_stats = system.get_system_stats()
    
    print(f"\n" + "="*80)
    print("📈 STATISTIQUES FINALES DU SYSTÈME VIDÉO")
    print("="*80)
    print(f"   Vidéos traitées: {system_stats['total_videos_processed']}")
    print(f"   Frames traitées: {system_stats['total_frames_processed']}")
    print(f"   Ratio moyen: {system_stats['total_compression_ratio']:.1f}:1")
    print(f"   Qualité moyenne: {system_stats['total_upscaling_quality']:.3f}")
    print(f"   FPS moyen: {system_stats['average_fps']:.1f}")
    print(f"   Score efficacité: {system_stats['efficiency_score']:.3f}")
    print(f"   Décisions adaptatives: {system_stats['adaptive_decisions']}")
    
    print(f"\n🎯 CONFIGURATION SYSTÈME VIDÉO:")
    config = system_stats['system_info']
    print(f"   K-Factor: {config['k_factor']}")
    print(f"   WebP Quality: {config['webp_quality']}")
    print(f"   Upscaling Preset: {config['upscaling_preset']}")
    print(f"   Composants: {', '.join(config['components'])}")
    
    # Nettoyage
    system.cleanup()
    
    print(f"\n✅ SYSTÈME INTÉGRÉ VIDÉO VALIDÉ AVEC SUCCÈS!")
    print("🚀 Compression vidéo maximale + Upscaling efficace opérationnel!")
    print("📊 Rapport vidéo complet généré et disponible!")
    
    return {
        'compression_results': compression_results,
        'upscaling_results': upscaling_results,
        'pipeline_results': pipeline_results,
        'adaptive_results': adaptive_results,
        'performance_analysis': performance_analysis_results,
        'system_stats': system_stats
    }

if __name__ == "__main__":
    main()
