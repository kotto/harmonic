#!/usr/bin/env python3
"""
TEST COMPLET D'ANALYSE UPSCALE-FIRST vs COMPRESS-FIRST
Évaluation des gains en qualité et performance
"""

import numpy as np
import cv2
import time
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from core.upscale_first_compression_system import UpscaleFirstCompressionSystem

def create_comprehensive_test_images() -> Dict[str, np.ndarray]:
    """Crée des images de test variées pour l'analyse"""
    images = {}
    
    # Image 1: Haute fréquence (détails fins)
    high_freq = np.zeros((300, 400, 3), dtype=np.uint8)
    for i in range(50):
        x, y = np.random.randint(0, 400), np.random.randint(0, 300)
        radius = np.random.randint(1, 3)
        color = tuple(np.random.randint(100, 255, 3).tolist())
        cv2.circle(high_freq, (x, y), radius, color, -1)
    images['high_frequency'] = high_freq
    
    # Image 2: Basse fréquence (gradients doux)
    low_freq = np.zeros((300, 400, 3), dtype=np.uint8)
    for i in range(300):
        for j in range(400):
            low_freq[i, j, 0] = int(128 + 127 * np.sin(i * 0.02) * np.cos(j * 0.02))
            low_freq[i, j, 1] = int(128 + 127 * np.sin(i * 0.01) * np.sin(j * 0.01))
            low_freq[i, j, 2] = int(128 + 127 * np.cos(i * 0.015) * np.cos(j * 0.015))
    images['low_frequency'] = low_freq
    
    # Image 3: Texte et graphiques
    graphics = np.zeros((250, 350, 3), dtype=np.uint8)
    cv2.putText(graphics, "TEST QUALITY", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    cv2.rectangle(graphics, (50, 120), (300, 200), (100, 200, 50), -1)
    cv2.line(graphics, (50, 120), (300, 200), (255, 100, 100), 2)
    images['graphics'] = graphics
    
    # Image 4: Photo réaliste simulée
    photo = np.random.randint(50, 150, (400, 600, 3), dtype=np.uint8)
    # Ajout de "visage"
    cv2.circle(photo, (300, 200), 80, (200, 150, 100), -1)
    cv2.circle(photo, (280, 180), 15, (50, 50, 50), -1)
    cv2.circle(photo, (320, 180), 15, (50, 50, 50), -1)
    cv2.ellipse(photo, (300, 220), (30, 15), 0, 0, 180, (100, 50, 50), 2)
    images['photo'] = photo
    
    # Image 5: Pattern géométrique complexe
    pattern = np.zeros((350, 350, 3), dtype=np.uint8)
    for i in range(10):
        center = (175, 175)
        radius = 150 - i * 15
        color = tuple(np.random.randint(50, 200, 3).tolist())
        cv2.circle(pattern, center, radius, color, 2)
    # Ajout de lignes radiales
    for angle in range(0, 360, 30):
        rad = np.radians(angle)
        x1, y1 = 175, 175
        x2, y2 = int(175 + 150 * np.cos(rad)), int(175 + 150 * np.sin(rad))
        cv2.line(pattern, (x1, y1), (x2, y2), (255, 255, 255), 1)
    images['pattern'] = pattern
    
    # Image 6: Bruit et texture
    noise = np.random.normal(128, 30, (300, 400, 3)).astype(np.uint8)
    # Ajout de structure
    for i in range(20):
        x1, y1 = np.random.randint(0, 400), np.random.randint(0, 300)
        x2, y2 = np.random.randint(0, 400), np.random.randint(0, 300)
        cv2.line(noise, (x1, y1), (x2, y2), (200, 200, 200), 1)
    images['noise'] = noise
    
    return images

def test_scenarios_analysis(system: UpscaleFirstCompressionSystem, images: Dict[str, np.ndarray]):
    """Test différents scénarios d'analyse"""
    print("\n" + "="*80)
    print("🔬 ANALYSE DÉTAILLÉE PAR SCÉNARIOS")
    print("="*80)
    
    scenarios = [
        {'target_ratio': 20.0, 'scale_factor': 2.0, 'name': 'Compression forte, Upscaling 2x'},
        {'target_ratio': 50.0, 'scale_factor': 2.0, 'name': 'Compression moyenne, Upscaling 2x'},
        {'target_ratio': 100.0, 'scale_factor': 2.0, 'name': 'Compression faible, Upscaling 2x'},
        {'target_ratio': 50.0, 'scale_factor': 1.5, 'name': 'Compression moyenne, Upscaling 1.5x'},
        {'target_ratio': 50.0, 'scale_factor': 3.0, 'name': 'Compression moyenne, Upscaling 3x'},
    ]
    
    scenario_results = {}
    
    for scenario in scenarios:
        print(f"\n🎯 Scénario: {scenario['name']}")
        print(f"   Ratio cible: {scenario['target_ratio']}:1, Échelle: {scenario['scale_factor']}x")
        
        scenario_data = {
            'upscale_first_wins': 0,
            'compress_first_wins': 0,
            'ties': 0,
            'avg_quality_diff': 0.0,
            'avg_time_diff': 0.0,
            'detailed_results': []
        }
        
        quality_diffs = []
        time_diffs = []
        
        for name, image in images.items():
            comparison = system.compare_approaches(
                image, 
                scenario['target_ratio'], 
                scenario['scale_factor']
            )
            
            scenario_data['detailed_results'].append({
                'image_name': name,
                'comparison': comparison
            })
            
            quality_diffs.append(comparison.quality_comparison['quality_difference'])
            time_diffs.append(comparison.performance_comparison['time_difference'])
            
            if 'UPSCALE_FIRST' in comparison.recommendation:
                scenario_data['upscale_first_wins'] += 1
            elif 'COMPRESS_FIRST' in comparison.recommendation:
                scenario_data['compress_first_wins'] += 1
            else:
                scenario_data['ties'] += 1
        
        scenario_data['avg_quality_diff'] = np.mean(quality_diffs)
        scenario_data['avg_time_diff'] = np.mean(time_diffs)
        scenario_data['upscale_first_win_rate'] = scenario_data['upscale_first_wins'] / len(images) * 100
        scenario_data['compress_first_win_rate'] = scenario_data['compress_first_wins'] / len(images) * 100
        
        scenario_results[scenario['name']] = scenario_data
        
        print(f"   Victoires Upscale-First: {scenario_data['upscale_first_wins']}/{len(images)} ({scenario_data['upscale_first_win_rate']:.1f}%)")
        print(f"   Victoires Compress-First: {scenario_data['compress_first_wins']}/{len(images)} ({scenario_data['compress_first_win_rate']:.1f}%)")
        print(f"   Différence qualité moyenne: {scenario_data['avg_quality_diff']:.3f}")
        print(f"   Différence temps moyenne: {scenario_data['avg_time_diff']:.3f}s")
    
    return scenario_results

def image_type_analysis(system: UpscaleFirstCompressionSystem, images: Dict[str, np.ndarray]):
    """Analyse par type d'image"""
    print("\n" + "="*80)
    print("🖼️  ANALYSE PAR TYPE D'IMAGE")
    print("="*80)
    
    image_type_results = {}
    
    for image_name, image in images.items():
        print(f"\n📸 Analyse: {image_name}")
        
        # Test avec différents paramètres
        test_params = [
            {'ratio': 30.0, 'scale': 1.5},
            {'ratio': 50.0, 'scale': 2.0},
            {'ratio': 100.0, 'scale': 2.5}
        ]
        
        image_data = {
            'best_approach': '',
            'best_quality_gain': 0.0,
            'worst_quality_loss': 0.0,
            'best_time_gain': 0.0,
            'worst_time_loss': 0.0,
            'detailed_tests': []
        }
        
        quality_gains = []
        time_gains = []
        
        for params in test_params:
            comparison = system.compare_approaches(image, params['ratio'], params['scale'])
            
            quality_diff = comparison.quality_comparison['quality_difference']
            time_diff = -comparison.performance_comparison['time_difference']  # Négatif = gain
            
            quality_gains.append(quality_diff)
            time_gains.append(time_diff)
            
            image_data['detailed_tests'].append({
                'params': params,
                'comparison': comparison,
                'quality_diff': quality_diff,
                'time_diff': time_diff
            })
            
            print(f"   Ratio {params['ratio']}:1, Échelle {params['scale']}x")
            print(f"      Qualité: {comparison.quality_comparison['quality_difference']:+.3f}")
            print(f"      Temps: {comparison.performance_comparison['time_difference']:+.3f}s")
            print(f"      Recommandation: {comparison.recommendation}")
        
        # Analyse des meilleurs/pires cas
        image_data['best_quality_gain'] = max(quality_gains)
        image_data['worst_quality_loss'] = min(quality_gains)
        image_data['best_time_gain'] = max(time_gains)
        image_data['worst_time_loss'] = min(time_gains)
        
        # Détermination de la meilleure approche globale
        upscale_better = sum(1 for q in quality_gains if q > 0)
        compress_better = sum(1 for q in quality_gains if q < 0)
        
        if upscale_better > compress_better:
            image_data['best_approach'] = 'UPSCALE_FIRST'
        elif compress_better > upscale_better:
            image_data['best_approach'] = 'COMPRESS_FIRST'
        else:
            image_data['best_approach'] = 'TIE'
        
        image_type_results[image_name] = image_data
        
        print(f"   🏆 Meilleure approche: {image_data['best_approach']}")
        print(f"   📈 Gain qualité max: {image_data['best_quality_gain']:+.3f}")
        print(f"   ⏱️  Gain temps max: {image_data['best_time_gain']:+.3f}s")
    
    return image_type_results

def generate_comprehensive_report(scenario_results: Dict, 
                                image_type_results: Dict,
                                system_stats: Dict):
    """Génère un rapport complet d'analyse"""
    print("\n" + "="*80)
    print("📊 GÉNÉRATION DU RAPPORT COMPLET")
    print("="*80)
    
    try:
        # Graphique 1: Performance par scénario
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Analyse Upscale-First vs Compress-First', fontsize=16)
        
        # Scénarios
        scenario_names = list(scenario_results.keys())
        uf_wins = [scenario_results[name]['upscale_first_wins'] for name in scenario_names]
        cf_wins = [scenario_results[name]['compress_first_wins'] for name in scenario_names]
        ties = [scenario_results[name]['ties'] for name in scenario_names]
        
        x = np.arange(len(scenario_names))
        width = 0.25
        
        axes[0, 0].bar(x - width, uf_wins, width, label='Upscale-First')
        axes[0, 0].bar(x, cf_wins, width, label='Compress-First')
        axes[0, 0].bar(x + width, ties, width, label='Égalité')
        axes[0, 0].set_title('Victoires par Scénario')
        axes[0, 0].set_ylabel('Nombre de victoires')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels([name[:20] for name in scenario_names], rotation=45)
        axes[0, 0].legend()
        
        # Gains de qualité par scénario
        quality_diffs = [scenario_results[name]['avg_quality_diff'] for name in scenario_names]
        colors = ['green' if q > 0 else 'red' for q in quality_diffs]
        axes[0, 1].bar(scenario_names, quality_diffs, color=colors, alpha=0.7)
        axes[0, 1].set_title('Gain Qualité Moyen par Scénario')
        axes[0, 1].set_ylabel('Différence de qualité')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Gains de temps par scénario
        time_diffs = [scenario_results[name]['avg_time_diff'] for name in scenario_names]
        colors = ['green' if t < 0 else 'red' for t in time_diffs]
        axes[0, 2].bar(scenario_names, time_diffs, color=colors, alpha=0.7)
        axes[0, 2].set_title('Gain Temps Moyen par Scénario')
        axes[0, 2].set_ylabel('Différence de temps (s)')
        axes[0, 2].tick_params(axis='x', rotation=45)
        axes[0, 2].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Analyse par type d'image
        image_names = list(image_type_results.keys())
        best_approaches = [image_type_results[name]['best_approach'] for name in image_names]
        max_quality_gains = [image_type_results[name]['best_quality_gain'] for name in image_names]
        
        # Distribution des meilleures approches
        approach_counts = {'UPSCALE_FIRST': 0, 'COMPRESS_FIRST': 0, 'TIE': 0}
        for approach in best_approaches:
            approach_counts[approach] += 1
        
        axes[1, 0].pie(approach_counts.values(), labels=approach_counts.keys(), autopct='%1.1f%%')
        axes[1, 0].set_title('Meilleure Approche par Type d\'Image')
        
        # Gains de qualité max par type
        colors = ['green' if q > 0 else 'red' for q in max_quality_gains]
        axes[1, 1].bar(image_names, max_quality_gains, color=colors, alpha=0.7)
        axes[1, 1].set_title('Gain Qualité Max par Type d\'Image')
        axes[1, 1].set_ylabel('Gain qualité max')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Statistiques globales
        global_metrics = [
            system_stats['upscale_first_win_rate'],
            system_stats['compress_first_win_rate'],
            system_stats['tie_rate']
        ]
        metric_labels = ['Upscale-First', 'Compress-First', 'Égalité']
        colors = ['lightblue', 'lightcoral', 'lightgray']
        
        axes[1, 2].bar(metric_labels, global_metrics, color=colors)
        axes[1, 2].set_title('Taux de Victoire Global')
        axes[1, 2].set_ylabel('Pourcentage (%)')
        
        plt.tight_layout()
        plt.savefig('F:/FINAL/DEFINITIF/hcs_v2-P3/upscale_first_analysis_report.png', 
                   dpi=150, bbox_inches='tight')
        print(f"\n📊 Rapport visuel sauvegardé: upscale_first_analysis_report.png")
        
    except Exception as e:
        print(f"\n⚠️ Erreur génération rapport visuel: {e}")

def main():
    """Fonction principale d'analyse complète"""
    print("🔬 ANALYSE COMPLÈTE: UPSCALE-FIRST vs COMPRESS-FIRST")
    print("Évaluation des gains en qualité et performance")
    print("=" * 80)
    
    # Initialisation du système
    system = UpscaleFirstCompressionSystem(
        k_factor=0.02,
        webp_quality=95,
        upscaling_preset="quantum_max"
    )
    
    # Création des images de test
    print("\n🎨 Création des images de test...")
    test_images = create_comprehensive_test_images()
    print(f"✅ {len(test_images)} types d'images créés")
    
    # Analyse par scénarios
    scenario_results = test_scenarios_analysis(system, test_images)
    
    # Analyse par type d'image
    image_type_results = image_type_analysis(system, test_images)
    
    # Statistiques globales
    stats = system.get_comparison_stats()
    
    # Génération du rapport
    generate_comprehensive_report(scenario_results, image_type_results, stats)
    
    # Conclusions
    print(f"\n" + "="*80)
    print("🎯 CONCLUSIONS DE L'ANALYSE")
    print("="*80)
    
    print(f"\n📈 RÉSULTATS GLOBAUX:")
    print(f"   Comparaisons totales: {stats['total_comparisons']}")
    print(f"   Victoires Upscale-First: {stats['upscale_first_win_rate']:.1f}%")
    print(f"   Victoires Compress-First: {stats['compress_first_win_rate']:.1f}%")
    print(f"   Égalités: {stats['tie_rate']:.1f}%")
    print(f"   Gain qualité moyen: {stats['avg_quality_diff']:+.3f}")
    print(f"   Gain performance moyen: {stats['avg_performance_diff']:+.3f}s")
    
    # Recommandations générales
    print(f"\n💡 RECOMMANDATIONS GÉNÉRALES:")
    
    if stats['upscale_first_win_rate'] > 60:
        print("   🏆 UPSCALE-FIRST est généralement supérieur")
        print("   ✅ Recommandé pour la qualité maximale")
        print("   📈 Avantages: Préservation des détails, meilleure reconstruction")
    elif stats['compress_first_win_rate'] > 60:
        print("   🏆 COMPRESS-FIRST est généralement supérieur")
        print("   ✅ Recommandé pour la performance maximale")
        print("   ⚡ Avantages: Temps de traitement réduit, ratio optimal")
    else:
        print("   ⚖️  Les deux approches sont équivalentes")
        print("   🔄 Recommandation: Adapter selon le cas d'usage")
        print("   🎯 Facteurs: Type d'image, ratio cible, échelle")
    
    # Recommandations spécifiques
    print(f"\n🎯 RECOMMANDATIONS SPÉCIFIQUES:")
    
    # Analyse des meilleurs scénarios pour upscale-first
    best_uf_scenario = max(scenario_results.items(), 
                          key=lambda x: x[1]['upscale_first_win_rate'])
    print(f"   🥇 Meilleur scénario Upscale-First: {best_uf_scenario[0]}")
    print(f"      Taux de victoire: {best_uf_scenario[1]['upscale_first_win_rate']:.1f}%")
    
    # Analyse des types d'images favorables
    uf_favored_images = [name for name, data in image_type_results.items() 
                         if data['best_approach'] == 'UPSCALE_FIRST']
    if uf_favored_images:
        print(f"   🖼️  Images favorables à Upscale-First: {', '.join(uf_favored_images)}")
    
    cf_favored_images = [name for name, data in image_type_results.items() 
                         if data['best_approach'] == 'COMPRESS_FIRST']
    if cf_favored_images:
        print(f"   🖼️  Images favorables à Compress-First: {', '.join(cf_favored_images)}")
    
    print(f"\n✅ Analyse complète terminée!")
    print("📊 Rapport détaillé généré et disponible!")
    print("🔬 Recommandations spécifiques fournies pour chaque cas d'usage")
    
    return {
        'scenario_results': scenario_results,
        'image_type_results': image_type_results,
        'system_stats': stats
    }

if __name__ == "__main__":
    main()
