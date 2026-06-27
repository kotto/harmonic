#!/usr/bin/env python3
"""
Analyse de performance complète et honnête
Tests approfondis avec métriques détaillées
"""

import numpy as np
from PIL import Image
import io
import requests
import time
import json
import statistics
from core.holographic_compressor import holographic_compressor

class PerformanceAnalyzer:
    """Analyseur de performance complet pour les systèmes de compression"""
    
    def __init__(self):
        self.hcs_results = []
        self.holographic_results = []
        
    def create_realistic_test_images(self):
        """Crée des images de test réalistes et variées"""
        images = {}
        
        # Image 1: Photo naturelle simulée
        nature = np.zeros((480, 640, 3), dtype=np.uint8)
        for i in range(480):
            for j in range(640):
                # Simulation de ciel
                if i < 160:
                    nature[i, j] = [135 + np.random.randint(-20, 20), 
                                   206 + np.random.randint(-20, 20), 
                                   235 + np.random.randint(-20, 20)]
                # Simulation de terrain
                elif i < 320:
                    nature[i, j] = [34 + np.random.randint(-10, 10), 
                                   139 + np.random.randint(-20, 20), 
                                   34 + np.random.randint(-10, 10)]
                # Simulation de rochers
                else:
                    nature[i, j] = [101 + np.random.randint(-30, 30), 
                                   67 + np.random.randint(-20, 20), 
                                   33 + np.random.randint(-15, 15)]
        images['nature'] = nature
        
        # Image 2: Portrait simulé
        portrait = np.ones((480, 640, 3), dtype=np.uint8) * 240
        # Peau
        center_y, center_x = 240, 320
        for i in range(480):
            for j in range(640):
                dist_face = np.sqrt((i - center_y)**2 + (j - center_x)**2)
                if dist_face < 150:
                    portrait[i, j] = [205 + np.random.randint(-15, 15), 
                                     133 + np.random.randint(-15, 15), 
                                     63 + np.random.randint(-10, 10)]
        images['portrait'] = portrait
        
        # Image 3: Texte et graphiques
        text_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        # Simulation de texte
        for i in range(50, 430, 40):
            for j in range(50, 590, 8):
                if (i // 40 + j // 8) % 2 == 0:
                    text_image[i:i+20, j:j+4] = [0, 0, 0]
        images['text'] = text_image
        
        # Image 4: Image médicale simulée
        medical = np.zeros((480, 640), dtype=np.uint8)
        for i in range(480):
            for j in range(640):
                # Simulation de tissu
                noise = np.random.normal(0, 10)
                base_value = 128 + int(50 * np.sin(i/50) * np.cos(j/50))
                medical[i, j] = np.clip(base_value + noise, 0, 255)
        # Convertir en RGB
        medical_rgb = np.stack([medical, medical, medical], axis=2)
        images['medical'] = medical_rgb
        
        return images
    
    def test_hcs_comprehensive(self, images):
        """Test complet du système HCS"""
        print('⚡ TEST COMPLET HCS HYBRIDE')
        print('=' * 60)
        
        for img_name, img_array in images.items():
            print(f'\n📸 {img_name.upper()}:')
            
            # Convertir en bytes
            pil_image = Image.fromarray(img_array, mode='RGB')
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            image_data = buffer.getvalue()
            
            original_size = len(image_data)
            print(f'   Taille originale: {original_size:,} octets')
            
            # Test avec différentes configurations
            configs = [
                {'target_ratio': None, 'name': 'auto'},
                {'target_ratio': 50, 'name': 'target_50'},
                {'target_ratio': 100, 'name': 'target_100'},
                {'target_ratio': 200, 'name': 'target_200'},
                {'target_ratio': 500, 'name': 'target_500'}
            ]
            
            img_results = {'image_name': img_name, 'original_size': original_size}
            
            for config in configs:
                try:
                    files = {'file': (f'{img_name}.png', image_data, 'image/png')}
                    data = {}
                    if config['target_ratio'] is not None:
                        data['target_ratio'] = str(config['target_ratio'])
                    
                    start_time = time.time()
                    response = requests.post(
                        'http://localhost:8006/api/v2/compress/image',
                        files=files,
                        data=data,
                        timeout=30
                    )
                    compression_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        metrics = {
                            'config': config['name'],
                            'target_ratio': config['target_ratio'],
                            'compression_ratio': result['compression_ratio'],
                            'k_ratio': result['k_ratio'],
                            'webp_ratio': result['webp_ratio'],
                            'space_saved_percent': result['space_saved_percent'],
                            'compression_time': compression_time,
                            'original_size': original_size,
                            'compressed_size': result.get('compressed_size', 0),
                            'performance_score': result['compression_ratio'] / compression_time
                        }
                        
                        print(f'   {config["name"]}: {result["compression_ratio"]:.1f}:1 en {compression_time:.3f}s')
                        print(f'      K: {result["k_ratio"]:.1f}:1, WebP: {result["webp_ratio"]:.1f}:1')
                        print(f'      Performance: {metrics["performance_score"]:.1f} ratio/s')
                        
                        img_results[config['name']] = metrics
                    else:
                        print(f'   {config["name"]}: Erreur HTTP {response.status_code}')
                        
                except Exception as e:
                    print(f'   {config["name"]}: Exception {e}')
            
            self.hcs_results.append(img_results)
    
    def test_holographic_comprehensive(self, images):
        """Test complet du système holographique"""
        print('\n🌌 TEST COMPLET HOLOGRAPHIQUE')
        print('=' * 60)
        
        principles = ['ads_cft', 'bekenstein', 'quantum_hologram', 'entropy_max']
        
        for img_name, img_array in images.items():
            print(f'\n📸 {img_name.upper()}:')
            
            original_size = img_array.nbytes
            print(f'   Taille originale: {original_size:,} octets')
            
            img_results = {'image_name': img_name, 'original_size': original_size}
            
            for principle in principles:
                try:
                    start_time = time.time()
                    result = holographic_compressor.compress_image_holographic(img_array, principle)
                    compression_time = time.time() - start_time
                    
                    if result['success']:
                        metrics = {
                            'principle': principle,
                            'compression_ratio': result['compression_ratio'],
                            'fidelity': result['quality_metrics']['holographic_fidelity'],
                            'quality': result['quality_metrics']['global_quality'],
                            'entropy_preservation': result['quality_metrics']['entropy_preservation'],
                            'coherence_preservation': result['quality_metrics']['coherence_preservation'],
                            'compression_time': compression_time,
                            'original_size': original_size,
                            'performance_score': result['compression_ratio'] / compression_time
                        }
                        
                        print(f'   {principle}: {result["compression_ratio"]:.1f}:1 en {compression_time:.3f}s')
                        print(f'      Fidélité: {result["quality_metrics"]["holographic_fidelity"]:.3f}')
                        print(f'      Qualité: {result["quality_metrics"]["global_quality"]:.3f}')
                        print(f'      Performance: {metrics["performance_score"]:.1f} ratio/s')
                        
                        img_results[principle] = metrics
                    else:
                        print(f'   {principle}: Échec - {result.get("error", "Erreur")}')
                        
                except Exception as e:
                    print(f'   {principle}: Exception {e}')
            
            self.holographic_results.append(img_results)
    
    def analyze_performance(self):
        """Analyse comparative détaillée"""
        print('\n📊 ANALYSE DE PERFORMANCE COMPARATIVE')
        print('=' * 80)
        
        # Extraire les métriques HCS
        hcs_ratios = []
        hcs_times = []
        hcs_performance = []
        
        for result in self.hcs_results:
            for key, metrics in result.items():
                if key not in ['image_name', 'original_size'] and isinstance(metrics, dict):
                    hcs_ratios.append(metrics['compression_ratio'])
                    hcs_times.append(metrics['compression_time'])
                    hcs_performance.append(metrics['performance_score'])
        
        # Extraire les métriques holographiques
        holographic_ratios = []
        holographic_times = []
        holographic_performance = []
        holographic_fidelities = []
        
        for result in self.holographic_results:
            for key, metrics in result.items():
                if key not in ['image_name', 'original_size'] and isinstance(metrics, dict):
                    holographic_ratios.append(metrics['compression_ratio'])
                    holographic_times.append(metrics['compression_time'])
                    holographic_performance.append(metrics['performance_score'])
                    holographic_fidelities.append(metrics['fidelity'])
        
        # Statistiques HCS
        print('\n⚡ STATISTIQUES HCS HYBRIDE:')
        print(f'   Tests effectués: {len(hcs_ratios)}')
        print(f'   Ratio moyen: {statistics.mean(hcs_ratios):.1f}:1')
        print(f'   Ratio médian: {statistics.median(hcs_ratios):.1f}:1')
        print(f'   Ratio min: {min(hcs_ratios):.1f}:1')
        print(f'   Ratio max: {max(hcs_ratios):.1f}:1')
        print(f'   Temps moyen: {statistics.mean(hcs_times):.3f}s')
        print(f'   Performance moyenne: {statistics.mean(hcs_performance):.1f} ratio/s')
        
        # Statistiques holographique
        print('\n🌌 STATISTIQUES HOLOGRAPHIQUE:')
        print(f'   Tests effectués: {len(holographic_ratios)}')
        print(f'   Ratio moyen: {statistics.mean(holographic_ratios):.1f}:1')
        print(f'   Ratio médian: {statistics.median(holographic_ratios):.1f}:1')
        print(f'   Ratio min: {min(holographic_ratios):.1f}:1')
        print(f'   Ratio max: {max(holographic_ratios):.1f}:1')
        print(f'   Temps moyen: {statistics.mean(holographic_times):.3f}s')
        print(f'   Fidélité moyenne: {statistics.mean(holographic_fidelities):.3f}')
        print(f'   Performance moyenne: {statistics.mean(holographic_performance):.1f} ratio/s')
        
        # Comparaison directe
        print('\n🏆 COMPARAISON DIRECTE:')
        hcs_avg_ratio = statistics.mean(hcs_ratios)
        holo_avg_ratio = statistics.mean(holographic_ratios)
        hcs_avg_time = statistics.mean(hcs_times)
        holo_avg_time = statistics.mean(holographic_times)
        
        ratio_advantage = hcs_avg_ratio / holo_avg_ratio
        time_advantage = holo_avg_time / hcs_avg_time
        
        print(f'   Avantage de ratio HCS: {ratio_advantage:.1f}x supérieur')
        print(f'   Avantage de temps HCS: {time_advantage:.1f}x plus rapide')
        print(f'   Efficacité globale HCS: {ratio_advantage * time_advantage:.1f}x supérieure')
        
        # Recommandation finale
        print('\n🎯 RECOMMANDATION FINALE:')
        if ratio_advantage > 10 and time_advantage > 2:
            print('   🥇 HCS HYBRIDE: Choix évident pour la production')
            print('   ✅ Performance supérieure sur tous les plans')
            print('   ✅ Prévisible et fiable')
            print('   ✅ Infrastructure mature')
        elif ratio_advantage > 5:
            print('   🥇 HCS HYBRIDE: Recommandé pour la plupart des usages')
            print('   ✅ Meilleure performance globale')
        else:
            print('   ⚖️  CHOIX CONTEXTUEL: Dépend des besoins spécifiques')
        
        print('\n🔬 HOLOGRAPHIQUE: Recherche fondamentale prometteuse')
        print('   🌈 Base théorique fascinante')
        print('   🚀 Potentiel à long terme')
        print('   ⚠️  Nécessite optimisation pour production')
    
    def generate_report(self):
        """Génère un rapport détaillé"""
        report = {
            'timestamp': time.time(),
            'hcs_results': self.hcs_results,
            'holographic_results': self.holographic_results,
            'summary': {
                'hcs_tests': len(self.hcs_results),
                'holographic_tests': len(self.holographic_results),
                'test_images': len(self.hcs_results)
            }
        }
        
        with open('performance_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print('\n📄 Rapport détaillé sauvegardé dans performance_report.json')

def main():
    """Fonction principale d'analyse"""
    analyzer = PerformanceAnalyzer()
    
    try:
        # Créer des images de test réalistes
        print('🎨 Création des images de test réalistes...')
        test_images = analyzer.create_realistic_test_images()
        
        # Tester HCS
        analyzer.test_hcs_comprehensive(test_images)
        
        # Tester holographique
        analyzer.test_holographic_comprehensive(test_images)
        
        # Analyser les performances
        analyzer.analyze_performance()
        
        # Générer le rapport
        analyzer.generate_report()
        
        print('\n✅ ANALYSE DE PERFORMANCE TERMINÉE!')
        
    except Exception as e:
        print(f'❌ ERREUR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
