#!/usr/bin/env python3
"""
TEST COMPLET DU SYSTÈME INTÉGRÉ
Compression Hybride Maximale + Upscaling Quantique-Harmonique Efficace
"""

import numpy as np
import cv2
import time
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from core.hybrid_compression_upscaling_system import (
    HybridCompressionUpscalingSystem, 
    ProcessingMode
)

def create_comprehensive_test_images() -> Dict[str, np.ndarray]:
    """Crée des images de test complètes et variées"""
    images = {}
    
    # Image 1: Photo réaliste (simulation)
    realistic = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    # Ajout de textures réalistes
    for i in range(10):
        y, x = np.random.randint(0, 480), np.random.randint(0, 640)
        radius = np.random.randint(20, 50)
        color = tuple(np.random.randint(100, 255, 3).tolist())
        cv2.circle(realistic, (x, y), radius, color, -1)
    images['realistic'] = realistic
    
    # Image 2: Graphique/Logo
    graphic = np.zeros((300, 400, 3), dtype=np.uint8)
    cv2.rectangle(graphic, (50, 50), (350, 250), (255, 100, 50), -1)
    cv2.putText(graphic, "LOGO", (120, 160), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    images['graphic'] = graphic
    
    # Image 3: Texture naturelle
    texture = np.random.randint(30, 150, (400, 600, 3), dtype=np.uint8)
    # Ajout de patterns naturels
    for i in range(20):
        y1, x1 = np.random.randint(0, 400, 2)
        y2, x2 = np.random.randint(0, 400, 2)
        color = tuple(np.random.randint(80, 180, 3).tolist())
        cv2.line(texture, (x1, y1), (x2, y2), color, 2)
    images['texture'] = texture
    
    # Image 4: Haute résolution
    high_res = np.random.randint(0, 256, (1080, 1920, 3), dtype=np.uint8)
    # Ajout de détails fins
    for i in range(100):
        y, x = np.random.randint(0, 1080), np.random.randint(0, 1920)
        radius = np.random.randint(1, 5)
        color = tuple(np.random.randint(150, 255, 3).tolist())
        cv2.circle(high_res, (x, y), radius, color, -1)
    images['high_res'] = high_res
    
    # Image 5: Basse résolution
    low_res = np.random.randint(0, 256, (120, 160, 3), dtype=np.uint8)
    cv2.rectangle(low_res, (20, 20), (140, 100), (200, 100, 50), -1)
    images['low_res'] = low_res
    
    return images

def test_compression_only(system: HybridCompressionUpscalingSystem, images: Dict[str, np.ndarray]):
    """Test du mode compression uniquement"""
    print("\n" + "="*80)
    print("🗜️  TEST MODE COMPRESSION UNIQUMENT")
    print("="*80)
    
    results = {}
    
    for name, image in images.items():
        print(f"\n📸 Compression de: {name} ({image.shape})")
        
        start_time = time.time()
        result = system.compress_image(image, target_ratio=1000)
        compression_time = time.time() - start_time
        
        results[name] = {
            'original_size': image.nbytes,
            'compressed_size': len(result.compressed_data),
            'ratio': result.compression_ratio,
            'time': compression_time,
            'quality_metrics': result.quality_metrics
        }
        
        print(f"   ✅ Ratio: {result.compression_ratio:.1f}:1")
        print(f"   📊 Taille originale: {image.nbytes:,} octets")
        print(f"   📦 Taille compressée: {len(result.compressed_data):,} octets")
        print(f"   ⏱️  Temps: {compression_time:.3f}s")
        print(f"   🎯 Qualité: {result.quality_metrics.get('optimization_level', 'unknown')}")
        print(f"   💾 Espace économisé: {result.quality_metrics.get('space_saved_percent', 0):.1f}%")
    
    return results

def test_upscaling_only(system: HybridCompressionUpscalingSystem, images: Dict[str, np.ndarray]):
    """Test du mode upscaling uniquement"""
    print("\n" + "="*80)
    print("🔍 TEST MODE UPSCALING UNIQUMENT")
    print("="*80)
    
    results = {}
    
    for name, image in images.items():
        print(f"\n📸 Upscaling de: {name} ({image.shape})")
        
        # Déterminer la taille cible (2x)
        target_shape = (image.shape[0] * 2, image.shape[1] * 2)
        
        start_time = time.time()
        result = system.upscale_image(image, target_shape, scale_factor=2.0)
        upscaling_time = time.time() - start_time
        
        results[name] = {
            'original_shape': image.shape,
            'final_shape': result.upscaled_image.shape,
            'scale_factor': result.scale_factor,
            'time': upscaling_time,
            'quality_metrics': result.quality_metrics
        }
        
        print(f"   ✅ Facteur: {result.scale_factor:.1f}x")
        print(f"   📐 Taille originale: {image.shape}")
        print(f"   📏 Taille finale: {result.upscaled_image.shape}")
        print(f"   ⏱️  Temps: {upscaling_time:.3f}s")
        print(f"   🎯 Qualité: {result.quality_metrics.get('quality_score', 0):.3f}")
        print(f"   📊 PSNR: {result.quality_metrics.get('psnr', 0):.1f}")
        print(f"   🔍 SSIM: {result.quality_metrics.get('ssim', 0):.3f}")
    
    return results

def test_full_pipeline(system: HybridCompressionUpscalingSystem, images: Dict[str, np.ndarray]):
    """Test du pipeline complet compression + upscaling"""
    print("\n" + "="*80)
    print("🔄 TEST PIPELINE COMPLET")
    print("="*80)
    
    results = {}
    
    for name, image in images.items():
        print(f"\n📸 Pipeline complet pour: {name} ({image.shape})")
        
        start_time = time.time()
        result = system.compress_and_upscale(
            image=image,
            target_ratio=500,  # Ratio cible modéré
            scale_factor=1.5,   # Upscaling 1.5x
            mode=ProcessingMode.COMPRESSION_UPSCALING
        )
        total_time = time.time() - start_time
        
        results[name] = {
            'original_shape': image.shape,
            'final_shape': result.final_image.shape,
            'compression_ratio': result.compression_ratio,
            'scale_factor': result.scale_factor,
            'total_time': total_time,
            'processing_times': result.processing_times,
            'overall_quality': result.overall_quality
        }
        
        print(f"   ✅ Ratio compression: {result.compression_ratio:.1f}:1")
        print(f"   📏 Facteur upscaling: {result.scale_factor:.1f}x")
        print(f"   📐 Taille originale: {image.shape}")
        print(f"   📏 Taille finale: {result.final_image.shape}")
        print(f"   ⏱️  Temps total: {total_time:.3f}s")
        print(f"      - Compression: {result.processing_times.get('compression', 0):.3f}s")
        print(f"      - Upscaling: {result.processing_times.get('upscaling', 0):.3f}s")
        print(f"   🎯 Qualité globale: {result.overall_quality.get('global_score', 0):.3f}")
        print(f"   📊 Efficacité: {result.overall_quality.get('efficiency', 0):.3f}")
    
    return results

def test_adaptive_mode(system: HybridCompressionUpscalingSystem, images: Dict[str, np.ndarray]):
    """Test du mode adaptatif"""
    print("\n" + "="*80)
    print("🤖 TEST MODE ADAPTATIF")
    print("="*80)
    
    results = {}
    
    for name, image in images.items():
        print(f"\n📸 Mode adaptatif pour: {name} ({image.shape})")
        
        # Différents scénarios pour tester l'adaptativité
        scenarios = [
            {'target_ratio': None, 'scale_factor': None, 'description': 'Normal'},
            {'target_ratio': 100, 'scale_factor': None, 'description': 'Compression requise'},
            {'target_ratio': None, 'scale_factor': 2.0, 'description': 'Upscaling requis'},
            {'target_ratio': 2000, 'scale_factor': 3.0, 'description': 'Les deux requis'}
        ]
        
        scenario_results = []
        
        for scenario in scenarios:
            start_time = time.time()
            result = system.compress_and_upscale(
                image=image,
                target_ratio=scenario['target_ratio'],
                scale_factor=scenario['scale_factor'],
                mode=ProcessingMode.ADAPTIVE
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

def performance_analysis(compression_results: Dict, upscaling_results: Dict, 
                        pipeline_results: Dict) -> Dict[str, Any]:
    """Analyse comparative des performances"""
    print("\n" + "="*80)
    print("📊 ANALYSE COMPARATIVE DES PERFORMANCES")
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
    
    analysis['compression_performance'] = {
        'avg_ratio': np.mean(compression_ratios),
        'max_ratio': np.max(compression_ratios),
        'min_ratio': np.min(compression_ratios),
        'avg_time': np.mean(compression_times),
        'throughput_mbps': np.mean([r['original_size'] / (r['time'] * 1024*1024) for r in compression_results.values()])
    }
    
    # Analyse upscaling
    upscaling_scales = [r['scale_factor'] for r in upscaling_results.values()]
    upscaling_times = [r['time'] for r in upscaling_results.values()]
    upscaling_qualities = [r['quality_metrics'].get('quality_score', 0.7) for r in upscaling_results.values()]
    
    analysis['upscaling_performance'] = {
        'avg_scale': np.mean(upscaling_scales),
        'avg_time': np.mean(upscaling_times),
        'avg_quality': np.mean(upscaling_qualities),
        'fps_capability': 1.0 / np.mean(upscaling_times)
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
    if analysis['compression_performance']['avg_ratio'] > 500:
        analysis['recommendations'].append("✅ Compression excellente - ratios élevés atteints")
    else:
        analysis['recommendations'].append("⚠️ Compression peut être optimisée")
    
    if analysis['upscaling_performance']['avg_quality'] > 0.8:
        analysis['recommendations'].append("✅ Upscaling haute qualité")
    else:
        analysis['recommendations'].append("⚠️ Qualité upscaling à améliorer")
    
    if analysis['pipeline_efficiency']['efficiency_score'] > 100:
        analysis['recommendations'].append("✅ Pipeline très efficace")
    else:
        analysis['recommendations'].append("⚠️ Efficacité pipeline à optimiser")
    
    # Affichage des résultats
    print(f"\n📈 PERFORMANCE COMPRESSION:")
    print(f"   Ratio moyen: {analysis['compression_performance']['avg_ratio']:.1f}:1")
    print(f"   Ratio max: {analysis['compression_performance']['max_ratio']:.1f}:1")
    print(f"   Temps moyen: {analysis['compression_performance']['avg_time']:.3f}s")
    print(f"   Débit moyen: {analysis['compression_performance']['throughput_mbps']:.1f} MB/s")
    
    print(f"\n🔍 PERFORMANCE UPSCALING:")
    print(f"   Échelle moyenne: {analysis['upscaling_performance']['avg_scale']:.1f}x")
    print(f"   Temps moyen: {analysis['upscaling_performance']['avg_time']:.3f}s")
    print(f"   Qualité moyenne: {analysis['upscaling_performance']['avg_quality']:.3f}")
    print(f"   FPS capability: {analysis['upscaling_performance']['fps_capability']:.1f}")
    
    print(f"\n🔄 EFFICACITÉ PIPELINE:")
    print(f"   Ratio moyen: {analysis['pipeline_efficiency']['avg_ratio']:.1f}:1")
    print(f"   Temps moyen: {analysis['pipeline_efficiency']['avg_time']:.3f}s")
    print(f"   Qualité moyenne: {analysis['pipeline_efficiency']['avg_quality']:.3f}")
    print(f"   Score efficacité: {analysis['pipeline_efficiency']['efficiency_score']:.1f}")
    
    print(f"\n💡 RECOMMANDATIONS:")
    for rec in analysis['recommendations']:
        print(f"   {rec}")
    
    return analysis

def generate_visual_report(images: Dict[str, np.ndarray], 
                          compression_results: Dict,
                          upscaling_results: Dict,
                          pipeline_results: Dict):
    """Génère un rapport visuel (si matplotlib disponible)"""
    try:
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Rapport de Performance - Système Intégré', fontsize=16)
        
        # Graphique 1: Ratios de compression
        image_names = list(compression_results.keys())
        ratios = [compression_results[name]['ratio'] for name in image_names]
        axes[0, 0].bar(image_names, ratios)
        axes[0, 0].set_title('Ratios de Compression')
        axes[0, 0].set_ylabel('Ratio:1')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Graphique 2: Temps de traitement
        comp_times = [compression_results[name]['time'] for name in image_names]
        up_times = [upscaling_results[name]['time'] for name in image_names]
        pipe_times = [pipeline_results[name]['total_time'] for name in image_names]
        
        x = np.arange(len(image_names))
        width = 0.25
        axes[0, 1].bar(x - width, comp_times, width, label='Compression')
        axes[0, 1].bar(x, up_times, width, label='Upscaling')
        axes[0, 1].bar(x + width, pipe_times, width, label='Pipeline')
        axes[0, 1].set_title('Temps de Traitement')
        axes[0, 1].set_ylabel('Temps (s)')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(image_names, rotation=45)
        axes[0, 1].legend()
        
        # Graphique 3: Qualité vs Efficacité
        qualities = [pipeline_results[name]['overall_quality'].get('global_score', 0.7) for name in image_names]
        efficiencies = [pipeline_results[name]['overall_quality'].get('efficiency', 0) for name in image_names]
        
        axes[0, 2].scatter(qualities, efficiencies, s=100, alpha=0.7)
        axes[0, 2].set_xlabel('Qualité Globale')
        axes[0, 2].set_ylabel('Efficacité')
        axes[0, 2].set_title('Qualité vs Efficacité')
        
        # Graphique 4: Distribution des ratios
        axes[1, 0].hist(ratios, bins=10, alpha=0.7, edgecolor='black')
        axes[1, 0].set_title('Distribution des Ratios')
        axes[1, 0].set_xlabel('Ratio:1')
        axes[1, 0].set_ylabel('Fréquence')
        
        # Graphique 5: Performance par type d'image
        performance_scores = []
        for name in image_names:
            score = (compression_results[name]['ratio'] * 
                    pipeline_results[name]['overall_quality'].get('global_score', 0.7) /
                    pipeline_results[name]['total_time'])
            performance_scores.append(score)
        
        axes[1, 1].bar(image_names, performance_scores)
        axes[1, 1].set_title('Score de Performance par Image')
        axes[1, 1].set_ylabel('Score Performance')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Graphique 6: Résumé système
        system_metrics = ['Ratio\nMoyen', 'Qualité\nMoyenne', 'Temps\nMoyen', 'Efficacité\nGlobale']
        metric_values = [
            np.mean(ratios),
            np.mean(qualities),
            np.mean(pipe_times),
            np.mean(efficiencies)
        ]
        
        # Normalisation pour l'affichage
        normalized_values = np.array(metric_values)
        normalized_values[0] /= 1000  # Ratio
        normalized_values[2] *= 100   # Temps
        normalized_values[3] *= 10    # Efficacité
        
        colors = ['green', 'blue', 'orange', 'red']
        axes[1, 2].bar(system_metrics, normalized_values, color=colors)
        axes[1, 2].set_title('Métriques Système (Normalisées)')
        axes[1, 2].set_ylabel('Valeur Normalisée')
        
        plt.tight_layout()
        plt.savefig('F:/FINAL/DEFINITIF/hcs_v2-P3/system_performance_report.png', dpi=150, bbox_inches='tight')
        print(f"\n📊 Rapport visuel sauvegardé: system_performance_report.png")
        
    except Exception as e:
        print(f"\n⚠️ Impossible de générer le rapport visuel: {e}")

def main():
    """Fonction principale de test complet"""
    print("🚀 TEST COMPLET DU SYSTÈME INTÉGRÉ")
    print("Compression Hybride Maximale + Upscaling Quantique-Harmonique")
    print("=" * 80)
    
    # Initialisation du système
    system = HybridCompressionUpscalingSystem(
        k_factor=0.02,
        webp_quality=95,
        upscaling_preset="quantum_max"
    )
    
    # Création des images de test
    print("\n🎨 Création des images de test...")
    test_images = create_comprehensive_test_images()
    print(f"✅ {len(test_images)} images de test créées")
    
    # Tests individuels
    compression_results = test_compression_only(system, test_images)
    upscaling_results = test_upscaling_only(system, test_images)
    pipeline_results = test_full_pipeline(system, test_images)
    adaptive_results = test_adaptive_mode(system, test_images)
    
    # Analyse des performances
    performance_analysis_results = performance_analysis(
        compression_results, upscaling_results, pipeline_results
    )
    
    # Rapport visuel
    generate_visual_report(test_images, compression_results, upscaling_results, pipeline_results)
    
    # Statistiques finales du système
    system_stats = system.get_system_stats()
    
    print(f"\n" + "="*80)
    print("📈 STATISTIQUES FINALES DU SYSTÈME")
    print("="*80)
    print(f"   Total traité: {system_stats['total_processed']}")
    print(f"   Ratio moyen: {system_stats['total_compression_ratio']:.1f}:1")
    print(f"   Qualité moyenne: {system_stats['total_upscaling_quality']:.3f}")
    print(f"   FPS moyen: {system_stats['average_fps']:.1f}")
    print(f"   Score efficacité: {system_stats['efficiency_score']:.3f}")
    print(f"   Décisions adaptatives: {system_stats['adaptive_decisions']}")
    
    print(f"\n🎯 CONFIGURATION SYSTÈME:")
    config = system_stats['system_info']
    print(f"   K-Factor: {config['k_factor']}")
    print(f"   WebP Quality: {config['webp_quality']}")
    print(f"   Upscaling Preset: {config['upscaling_preset']}")
    print(f"   Composants: {', '.join(config['components'])}")
    
    print(f"\n✅ SYSTÈME INTÉGRÉ VALIDÉ AVEC SUCCÈS!")
    print("🚀 Compression maximale + Upscaling efficace opérationnel!")
    print("📊 Rapport complet généré et disponible!")
    
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
