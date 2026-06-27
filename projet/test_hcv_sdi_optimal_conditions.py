#!/usr/bin/env python3
"""
Test HCV SDI dans conditions optimales pour comprendre les ratios annoncés
"""

import numpy as np
import cv2
import json
import time
import zstandard as zstd

class HCVSDIOptimalTester:
    def __init__(self):
        self.modes = {
            'fast': {'zstd_level': 3, 'expected_ratio': 9.56},
            'sdi': {'zstd_level': 11, 'expected_ratio': 11.85}, 
            'archive': {'zstd_level': 19, 'expected_ratio': 16.19}
        }
        
    def generate_optimal_content(self, width=1920, height=1080, frames=30, scenario='studio'):
        """Génère du contenu dans les conditions les plus favorables"""
        print(f"Génération contenu optimal '{scenario}': {width}x{height}, {frames} frames")
        
        video_data = []
        
        for frame_idx in range(frames):
            if scenario == 'studio':
                # Studio avec fond uniforme (cas idéal broadcast)
                y_channel = np.full((height, width), 400, dtype=np.uint16)  # Fond uniforme
                
                # Quelques éléments graphiques nets (logos, bandeaux)
                y_channel[50:100, 100:500] = 800  # Bandeau
                y_channel[height-60:height-20, 200:800] = 200  # Sous-titres
                
                # Zone présentateur (uniforme aussi)
                y_channel[200:600, 600:1200] = 500  # Zone présentateur
                
            elif scenario == 'graphics_only':
                # Contenu purement graphique (très compressible)
                y_channel = np.full((height, width), 512, dtype=np.uint16)
                
                # Zones de couleur parfaitement uniformes
                y_channel[:height//2, :width//2] = 200
                y_channel[:height//2, width//2:] = 800
                y_channel[height//2:, :width//2] = 600
                y_channel[height//2:, width//2:] = 300
                
            elif scenario == 'test_pattern':
                # Mire de test (répétitions parfaites)
                y_channel = np.full((height, width), 512, dtype=np.uint16)
                
                # Barres de couleur
                bar_width = width // 8
                colors = [100, 200, 300, 400, 500, 600, 700, 800]
                for i, color in enumerate(colors):
                    x_start = i * bar_width
                    x_end = min((i + 1) * bar_width, width)
                    y_channel[:, x_start:x_end] = color
                    
            elif scenario == 'minimal_variation':
                # Variation minimale (presque uniforme)
                base_color = 400 + (frame_idx % 10)  # Variation très lente
                y_channel = np.full((height, width), base_color, dtype=np.uint16)
                
                # Quelques zones avec variation minimale
                y_channel[100:200, 100:200] = base_color + 10
                y_channel[300:400, 300:400] = base_color - 10
                
            # Chrominance très uniforme (4:2:2)
            cb_channel = np.full((height//2, width//2), 512, dtype=np.uint16)
            cr_channel = np.full((height//2, width//2), 512, dtype=np.uint16)
            
            # Grain capteur minimal ou nul
            if scenario == 'test_pattern':
                # Pas de grain du tout
                pass
            else:
                # Grain très léger
                grain = np.random.normal(0, 0.5, (height, width)).astype(np.int16)
                y_channel = np.clip(y_channel.astype(np.int32) + grain, 64, 940).astype(np.uint16)
            
            frame_data = {
                'y': y_channel,
                'cb': cb_channel,
                'cr': cr_channel,
                'frame_idx': frame_idx
            }
            video_data.append(frame_data)
            
        return video_data
    
    def compress_hcv_sdi_advanced(self, video_data, mode='sdi'):
        """Compression HCV SDI avec toutes les optimisations"""
        print(f"Compression HCV SDI avancée mode: {mode}")
        
        config = self.modes[mode]
        compressor = zstd.ZstdCompressor(level=config['zstd_level'])
        
        # Header minimal
        header_size = 256
        
        # Modèle de grain global (très compact pour contenu uniforme)
        grain_model_size = 64
        
        total_size = header_size + grain_model_size
        
        for i, frame in enumerate(video_data):
            # Détection zones uniformes
            y_data = frame['y']
            
            # Prédiction optimale selon le contenu
            if i > 0:
                # Prédiction temporelle parfaite pour contenu statique
                prev_y = video_data[i-1]['y']
                y_predicted = prev_y.copy()
            else:
                # Prédiction spatiale optimisée
                y_predicted = np.zeros_like(y_data)
                # Prédiction par blocs uniformes
                for y in range(0, y_data.shape[0], 64):
                    for x in range(0, y_data.shape[1], 64):
                        block = y_data[y:y+64, x:x+64]
                        if block.size > 0:
                            # Prédiction par valeur moyenne du bloc
                            mean_val = np.mean(block)
                            y_predicted[y:y+64, x:x+64] = mean_val
            
            # Résidu (très faible pour contenu uniforme)
            y_residual = y_data.astype(np.int32) - y_predicted.astype(np.int32)
            
            # Quantification adaptative agressive
            if mode == 'fast':
                y_quantized = (y_residual / 2).astype(np.int16) * 2
            elif mode == 'sdi':
                y_quantized = (y_residual / 4).astype(np.int16) * 4
            else:  # archive
                y_quantized = (y_residual / 8).astype(np.int16) * 8
            
            # Compression avec dictionnaire optimisé
            y_compressed = compressor.compress(y_quantized.tobytes())
            
            # Chrominance (très compressible car uniforme)
            cb_compressed = compressor.compress(frame['cb'].tobytes())
            cr_compressed = compressor.compress(frame['cr'].tobytes())
            
            # Grain : modèle global (économie maximale)
            grain_residual = np.array([0, 0, 0, 0], dtype=np.int16)  # Quasi-nul
            grain_compressed = compressor.compress(grain_residual.tobytes())
            
            frame_size = len(y_compressed) + len(cb_compressed) + len(cr_compressed) + len(grain_compressed)
            total_size += frame_size
            
        return total_size
    
    def calculate_entropy(self, video_data):
        """Calcule l'entropie du contenu"""
        if not video_data:
            return 0
            
        # Échantillonnage sur plusieurs frames
        all_pixels = []
        for frame in video_data[:5]:  # 5 frames échantillon
            all_pixels.extend(frame['y'].flatten()[::100])  # Sous-échantillonnage
            
        # Histogramme et entropie
        hist, _ = np.histogram(all_pixels, bins=256, range=(64, 940))
        hist_norm = hist / np.sum(hist)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        
        return entropy
    
    def run_optimal_tests(self):
        """Tests dans conditions optimales"""
        print("=" * 80)
        print("TEST HCV SDI - CONDITIONS OPTIMALES")
        print("=" * 80)
        
        scenarios = [
            'studio',           # Studio broadcast typique
            'graphics_only',    # Contenu purement graphique
            'test_pattern',     # Mire de test
            'minimal_variation' # Variation minimale
        ]
        
        all_results = {}
        
        for scenario in scenarios:
            print(f"\n{'='*60}")
            print(f"SCÉNARIO: {scenario.upper()}")
            print(f"{'='*60}")
            
            # Génération contenu optimal
            video_data = self.generate_optimal_content(1920, 1080, 30, scenario)
            raw_size = self.calculate_raw_sdi_size(video_data)
            entropy = self.calculate_entropy(video_data)
            
            print(f"Taille raw SDI: {raw_size/1024/1024:.2f} MB")
            print(f"Entropie contenu: {entropy:.2f} bits/symbole")
            
            results = {
                'scenario': scenario,
                'raw_size_mb': raw_size / 1024 / 1024,
                'entropy': entropy,
                'modes': {}
            }
            
            # Test des 3 modes
            for mode_name in self.modes.keys():
                start_time = time.time()
                
                compressed_size = self.compress_hcv_sdi_advanced(video_data, mode_name)
                ratio = raw_size / compressed_size
                expected = self.modes[mode_name]['expected_ratio']
                achievement = (ratio / expected) * 100
                
                processing_time = time.time() - start_time
                
                results['modes'][mode_name] = {
                    'compressed_size_mb': compressed_size / 1024 / 1024,
                    'compression_ratio': ratio,
                    'expected_ratio': expected,
                    'achievement_percent': achievement,
                    'processing_time_sec': processing_time
                }
                
                # Affichage résultats
                print(f"\n{mode_name.upper()}:")
                print(f"  Ratio mesuré: {ratio:.2f}×")
                print(f"  Ratio attendu: {expected:.2f}×")
                print(f"  Atteinte objectif: {achievement:.1f}%")
                
                # Évaluation
                if achievement >= 90:
                    status = "🎯 OBJECTIF ATTEINT"
                elif achievement >= 70:
                    status = "✅ TRÈS BON"
                elif achievement >= 50:
                    status = "⚠️ ACCEPTABLE"
                else:
                    status = "❌ INSUFFISANT"
                print(f"  Statut: {status}")
            
            all_results[scenario] = results
        
        # Analyse des conditions optimales
        print(f"\n{'='*80}")
        print("ANALYSE CONDITIONS OPTIMALES")
        print(f"{'='*80}")
        
        best_scenario = None
        best_achievement = 0
        
        for scenario, data in all_results.items():
            max_achievement = max([mode['achievement_percent'] for mode in data['modes'].values()])
            print(f"\n{scenario.upper()}:")
            print(f"  Entropie: {data['entropy']:.2f} bits/symbole")
            print(f"  Meilleure performance: {max_achievement:.1f}% objectif")
            
            if max_achievement > best_achievement:
                best_achievement = max_achievement
                best_scenario = scenario
        
        print(f"\n🏆 MEILLEUR SCÉNARIO: {best_scenario.upper()}")
        print(f"🎯 MEILLEURE PERFORMANCE: {best_achievement:.1f}% de l'objectif")
        
        if best_achievement >= 80:
            print("✅ Les ratios annoncés sont ATTEIGNABLES dans des conditions optimales")
        else:
            print("⚠️ Les ratios annoncés restent difficiles à atteindre même en conditions optimales")
        
        # Sauvegarde
        with open('hcv_sdi_optimal_conditions_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        
        return all_results
    
    def calculate_raw_sdi_size(self, video_data):
        """Calcule la taille raw SDI"""
        if not video_data:
            return 0
        frame = video_data[0]
        h, w = frame['y'].shape
        bytes_per_pixel = 2.5  # YCbCr 4:2:2 10-bit
        frame_size = int(w * h * bytes_per_pixel)
        return frame_size * len(video_data)

def main():
    tester = HCVSDIOptimalTester()
    results = tester.run_optimal_tests()
    
    print(f"\n{'='*80}")
    print("CONCLUSION SUR LES CONDITIONS OPTIMALES")
    print(f"{'='*80}")
    print("Ce test révèle dans quelles conditions les ratios HCV SDI")
    print("annoncés peuvent être approchés ou atteints.")

if __name__ == "__main__":
    main()