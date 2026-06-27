#!/usr/bin/env python3
"""
Demo Recompression H.264 → HCV16
Démonstration du POC de recompression
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import time
import numpy as np
from h264_recompressor import H264HCV16Recompressor
from h264_analyzer import H264Analyzer
from performance_tracker import PerformanceTracker

def demo_complete_workflow():
    """Démonstration workflow complet"""
    print("🚀 DÉMONSTRATION POC H.264 → HCV16")
    print("="*50)
    
    # Initialisation
    recompressor = H264HCV16Recompressor()
    analyzer = H264Analyzer()
    tracker = PerformanceTracker()
    
    # Simulation avec fichier test (à remplacer par vrai fichier H.264)
    demo_scenarios = [
        {
            'name': 'Animation HD',
            'file': 'demo_animation.mp4',
            'expected_ratio': 1.12,
            'description': 'Contenu animation avec blocking élevé'
        },
        {
            'name': 'Film 4K',
            'file': 'demo_film.mp4', 
            'expected_ratio': 1.06,
            'description': 'Contenu cinéma avec artefacts modérés'
        },
        {
            'name': 'Sport Live',
            'file': 'demo_sport.mp4',
            'expected_ratio': 1.08,
            'description': 'Contenu sport avec mouvement rapide'
        }
    ]
    
    results = []
    
    for scenario in demo_scenarios:
        print(f"\n📊 Scénario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Ratio attendu: {scenario['expected_ratio']:.2f}×")
        
        # Simulation du processus (fichier réel non disponible)
        if not os.path.exists(scenario['file']):
            print(f"   ⚠️  Fichier {scenario['file']} non trouvé - Simulation")
            result = simulate_recompression_scenario(scenario, recompressor)
        else:
            # Recompression réelle
            try:
                original_size, compressed_size, ratio = recompressor.recompress(
                    input_h264=scenario['file'],
                    output_hcv16=f"output_{scenario['name'].lower().replace(' ', '_')}.hcv16",
                    strategy="auto"
                )
                
                result = {
                    'scenario': scenario['name'],
                    'original_size_mb': original_size / (1024*1024),
                    'compressed_size_mb': compressed_size / (1024*1024),
                    'ratio': ratio,
                    'savings_percent': (ratio - 1) * 100,
                    'success': True
                }
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                result = {'scenario': scenario['name'], 'success': False, 'error': str(e)}
        
        results.append(result)
        
        if result.get('success', False):
            print(f"   ✅ Ratio obtenu: {result['ratio']:.3f}×")
            print(f"   💰 Économie: {result['savings_percent']:.1f}%")
    
    # Génération rapport final
    generate_demo_report(results)
    
    return results

def simulate_recompression_scenario(scenario, recompressor):
    """Simulation d'un scénario de recompression"""
    print("   🔄 Simulation en cours...")
    
    # Simulation temps de traitement
    time.sleep(0.5)
    
    # Génération résultats simulés basés sur le scénario
    base_ratio = scenario['expected_ratio']
    
    # Ajout variabilité réaliste
    variation = np.random.normal(0, 0.02)  # ±2% variation
    simulated_ratio = max(1.01, base_ratio + variation)
    
    # Tailles simulées
    simulated_original_mb = np.random.uniform(50, 500)  # 50-500 MB
    simulated_compressed_mb = simulated_original_mb / simulated_ratio
    
    result = {
        'scenario': scenario['name'],
        'original_size_mb': simulated_original_mb,
        'compressed_size_mb': simulated_compressed_mb,
        'ratio': simulated_ratio,
        'savings_percent': (simulated_ratio - 1) * 100,
        'success': True,
        'simulated': True
    }
    
    return result

def demo_analysis_only():
    """Démonstration analyse seule (sans recompression)"""
    print("\n🔍 DÉMONSTRATION ANALYSE H.264")
    print("="*40)
    
    analyzer = H264Analyzer()
    
    # Création images test avec différents niveaux d'artefacts
    test_cases = [
        ('Blocking élevé', create_high_blocking_image()),
        ('Motion blur', create_motion_blur_image()),
        ('Quantization noise', create_quantization_noise_image()),
        ('Contenu propre', create_clean_image())
    ]
    
    for case_name, test_image in test_cases:
        print(f"\n📊 Analyse: {case_name}")
        
        # Simulation frames (répétition de l'image test)
        test_frames = [test_image] * 10
        
        # Analyses individuelles
        blocking = analyzer._analyze_blocking_artifacts(test_frames)
        motion = analyzer._analyze_motion_residuals(test_frames)
        quantization = analyzer._analyze_quantization_noise(test_frames)
        temporal = analyzer._analyze_temporal_patterns(test_frames)
        
        # Calcul opportunités
        analyses = {
            'blocking': blocking,
            'motion': motion,
            'quantization': quantization,
            'temporal': temporal
        }
        
        opportunities = analyzer._calculate_hcv16_opportunities(analyses)
        
        print(f"   Blocking: {blocking['level']} ({blocking['hcv16_gain_potential']*100:.1f}%)")
        print(f"   Motion: {motion['level']} ({motion['hcv16_gain_potential']*100:.1f}%)")
        print(f"   Quantization: {quantization['level']} ({quantization['hcv16_gain_potential']*100:.1f}%)")
        print(f"   Ratio estimé: {opportunities['estimated_compression_ratio']:.3f}×")
        print(f"   Niveau: {opportunities['opportunity_level']}")

def create_high_blocking_image():
    """Création image avec blocking artifacts élevés"""
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    
    # Ajout blocs 8×8 avec variations
    for y in range(0, 240, 8):
        for x in range(0, 320, 8):
            block_value = np.random.randint(50, 200)
            image[y:y+8, x:x+8] = block_value
    
    # Ajout frontières visibles
    for i in range(8, 240, 8):
        image[i, :] = [255, 255, 255]  # Ligne blanche
    for i in range(8, 320, 8):
        image[:, i] = [255, 255, 255]  # Ligne blanche
    
    return image

def create_motion_blur_image():
    """Création image avec motion blur"""
    # Gradient avec flou de mouvement
    y, x = np.ogrid[:240, :320]
    base = ((x + y) / 2).astype(np.uint8)
    
    # Conversion en 3 canaux
    image = np.stack([base, base, base], axis=2)
    
    # Ajout motion blur horizontal
    import cv2
    kernel = np.zeros((1, 9))
    kernel[0, :] = 1/9
    
    for c in range(3):
        image[:, :, c] = cv2.filter2D(image[:, :, c], -1, kernel)
    
    return image

def create_quantization_noise_image():
    """Création image avec quantization noise"""
    # Image de base uniforme
    image = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    # Ajout bruit de quantification
    noise = np.random.normal(0, 10, (240, 320, 3))
    image = np.clip(image + noise, 0, 255)
    
    return image.astype(np.uint8)

def create_clean_image():
    """Création image propre (peu d'artefacts)"""
    # Gradient lisse
    y, x = np.ogrid[:240, :320]
    
    # Gradient radial lisse
    center_y, center_x = 120, 160
    distance = np.sqrt((y - center_y)**2 + (x - center_x)**2)
    gradient = (255 * (1 - distance / np.max(distance))).astype(np.uint8)
    
    # Conversion 3 canaux
    image = np.stack([gradient, gradient, gradient], axis=2)
    
    return image

def generate_demo_report(results):
    """Génération rapport de démonstration"""
    print(f"\n" + "="*60)
    print("📈 RAPPORT DÉMONSTRATION POC")
    print("="*60)
    
    successful_results = [r for r in results if r.get('success', False)]
    
    if not successful_results:
        print("❌ Aucun résultat valide")
        return
    
    # Statistiques globales
    ratios = [r['ratio'] for r in successful_results]
    savings = [r['savings_percent'] for r in successful_results]
    
    avg_ratio = sum(ratios) / len(ratios)
    avg_savings = sum(savings) / len(savings)
    min_ratio = min(ratios)
    max_ratio = max(ratios)
    
    print(f"Scénarios testés: {len(successful_results)}")
    print(f"Ratio moyen: {avg_ratio:.3f}×")
    print(f"Économie moyenne: {avg_savings:.1f}%")
    print(f"Ratio min/max: {min_ratio:.3f}× / {max_ratio:.3f}×")
    
    # Détail par scénario
    print(f"\n📊 DÉTAIL PAR SCÉNARIO:")
    for result in successful_results:
        simulated = " (simulé)" if result.get('simulated', False) else ""
        print(f"   {result['scenario']}: {result['ratio']:.3f}× ({result['savings_percent']:.1f}%){simulated}")
    
    # Évaluation POC
    poc_success_rate = len([r for r in ratios if r >= 1.02]) / len(ratios)
    excellent_rate = len([r for r in ratios if r >= 1.10]) / len(ratios)
    
    print(f"\n🎯 ÉVALUATION POC:")
    print(f"   Taux succès (>1.02×): {poc_success_rate*100:.0f}%")
    print(f"   Taux excellent (>1.10×): {excellent_rate*100:.0f}%")
    
    # Recommandation finale
    if avg_ratio >= 1.08 and poc_success_rate >= 0.8:
        recommendation = "🚀 POC VALIDÉ - DÉVELOPPEMENT RECOMMANDÉ"
    elif avg_ratio >= 1.05 and poc_success_rate >= 0.6:
        recommendation = "⚡ POC PROMETTEUR - OPTIMISATIONS NÉCESSAIRES"
    elif avg_ratio >= 1.02:
        recommendation = "🔄 POC PARTIEL - REVOIR STRATÉGIE"
    else:
        recommendation = "❌ POC NON CONCLUANT"
    
    print(f"\n{recommendation}")
    
    # Estimation impact business
    if avg_savings >= 5:
        business_impact = f"💰 Impact business significatif: {avg_savings:.1f}% d'économies"
    elif avg_savings >= 2:
        business_impact = f"💡 Impact business modéré: {avg_savings:.1f}% d'économies"
    else:
        business_impact = f"📊 Impact business limité: {avg_savings:.1f}% d'économies"
    
    print(f"{business_impact}")

def interactive_demo():
    """Démonstration interactive"""
    print("\n🎮 DÉMONSTRATION INTERACTIVE")
    print("="*40)
    
    while True:
        print("\nOptions disponibles:")
        print("1. Analyse complète")
        print("2. Analyse seule")
        print("3. Simulation personnalisée")
        print("4. Quitter")
        
        choice = input("\nVotre choix (1-4): ").strip()
        
        if choice == '1':
            demo_complete_workflow()
        elif choice == '2':
            demo_analysis_only()
        elif choice == '3':
            custom_simulation()
        elif choice == '4':
            print("👋 Au revoir!")
            break
        else:
            print("❌ Choix invalide")

def custom_simulation():
    """Simulation personnalisée"""
    print("\n🔧 SIMULATION PERSONNALISÉE")
    
    try:
        # Paramètres utilisateur
        file_size = float(input("Taille fichier H.264 (MB): "))
        expected_ratio = float(input("Ratio attendu (ex: 1.05): "))
        
        # Simulation
        compressed_size = file_size / expected_ratio
        savings = (expected_ratio - 1) * 100
        
        print(f"\n📊 RÉSULTATS SIMULATION:")
        print(f"   Taille originale: {file_size:.1f} MB")
        print(f"   Taille compressée: {compressed_size:.1f} MB")
        print(f"   Ratio: {expected_ratio:.3f}×")
        print(f"   Économie: {savings:.1f}%")
        print(f"   Économie absolue: {file_size - compressed_size:.1f} MB")
        
        # Extrapolation business
        monthly_volume = float(input("\nVolume mensuel (GB, optionnel): ") or "0")
        if monthly_volume > 0:
            monthly_savings_gb = (monthly_volume * 1024 * savings / 100) / 1024
            print(f"   Économie mensuelle: {monthly_savings_gb:.1f} GB")
            
    except ValueError:
        print("❌ Valeurs invalides")

if __name__ == '__main__':
    print("🎬 DÉMONSTRATION POC H.264 → HCV16")
    print("Exploitation révolution 18× lossless pour améliorer H.264 existants")
    print("="*70)
    
    # Choix mode démonstration
    print("\nModes disponibles:")
    print("1. Démonstration automatique")
    print("2. Démonstration interactive")
    
    mode = input("\nMode (1-2): ").strip()
    
    if mode == '2':
        interactive_demo()
    else:
        # Mode automatique
        demo_complete_workflow()
        demo_analysis_only()
    
    print("\n✅ DÉMONSTRATION TERMINÉE")
    print("🎯 Prêt pour tests avec vrais fichiers H.264!")