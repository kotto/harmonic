#!/usr/bin/env python3
"""
Test des métriques hybrides HCV16 sur B3.mp4
Comparaison approche SIMD vs approche hybride
"""

import cv2
import numpy as np
import time
import json
import os
from sklearn.cluster import KMeans

class HCV16HybridMetricsTester:
    def __init__(self):
        self.hybrid_strategies = {
            'artifact_cleaning': 'Nettoyage artefacts H.264',
            'entropy_clustering': 'Réduction entropie par clustering',
            'perceptual_optimization': 'Optimisation perceptuelle ROI',
            'content_restoration': 'Restauration contenu original'
        }
        
    def load_b3_sample(self, max_frames=10):
        """Chargement échantillon B3.mp4 pour tests métriques"""
        print(f"🔄 Chargement échantillon B3.mp4 ({max_frames} frames)...")
        
        if not os.path.exists('B3.mp4'):
            print("❌ B3.mp4 non trouvé")
            return None, None
        
        cap = cv2.VideoCapture('B3.mp4')
        if not cap.isOpened():
            return None, None
        
        # Propriétés
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        video_info = {
            'width': width,
            'height': height,
            'fps': fps,
            'source_type': 'H.264 pré-compressé'
        }
        
        frames = []
        frame_idx = 0
        
        while frame_idx < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Conversion YUV 10-bit simulé
            frame_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            y_10bit = frame_yuv[:, :, 0].astype(np.uint16) * 4 + 64
            
            frames.append({
                'frame_idx': frame_idx,
                'y': y_10bit,
                'original_8bit': frame_yuv[:, :, 0]
            })
            
            frame_idx += 1
        
        cap.release()
        print(f"✅ {len(frames)} frames chargées")
        
        return frames, video_info

    def analyze_h264_artifacts_metrics(self, frame_data):
        """Analyse quantitative des artefacts H.264"""
        y_channel = frame_data['y']
        height, width = y_channel.shape
        
        # 1. Détection artefacts de blocs
        block_artifacts = self.detect_blocking_artifacts_score(y_channel)
        
        # 2. Artefacts de quantification
        quantization_artifacts = self.detect_quantization_artifacts_score(y_channel)
        
        # 3. Artefacts de mouvement/compression
        compression_artifacts = self.detect_compression_artifacts_score(y_channel)
        
        # 4. Analyse entropie
        entropy_score = self.calculate_entropy_metrics(y_channel)
        
        artifacts_metrics = {
            'blocking_score': float(block_artifacts),
            'quantization_score': float(quantization_artifacts),
            'compression_score': float(compression_artifacts),
            'entropy_original': float(entropy_score['entropy']),
            'entropy_normalized': float(entropy_score['normalized_entropy']),
            'complexity_score': float(entropy_score['complexity']),
            'total_artifact_score': float((block_artifacts + quantization_artifacts + compression_artifacts) / 3)
        }
        
        return artifacts_metrics

    def detect_blocking_artifacts_score(self, y_channel):
        """Score quantitatif des artefacts de blocs"""
        height, width = y_channel.shape
        block_discontinuities = []
        
        # Analyse discontinuités aux frontières 8x8 et 16x16
        for block_size in [8, 16]:
            for y in range(0, height - block_size, block_size):
                for x in range(0, width - block_size, block_size):
                    if x + block_size < width:
                        # Discontinuité horizontale
                        left_edge = y_channel[y:y+block_size, x+block_size-1]
                        right_edge = y_channel[y:y+block_size, x+block_size]
                        h_disc = np.mean(np.abs(left_edge.astype(np.int16) - right_edge.astype(np.int16)))
                        block_discontinuities.append(h_disc)
                    
                    if y + block_size < height:
                        # Discontinuité verticale
                        top_edge = y_channel[y+block_size-1, x:x+block_size]
                        bottom_edge = y_channel[y+block_size, x:x+block_size]
                        v_disc = np.mean(np.abs(top_edge.astype(np.int16) - bottom_edge.astype(np.int16)))
                        block_discontinuities.append(v_disc)
        
        return np.mean(block_discontinuities) if block_discontinuities else 0

    def detect_quantization_artifacts_score(self, y_channel):
        """Score artefacts de quantification"""
        # Analyse des gradients pour détecter les "paliers"
        grad_x = cv2.Sobel(y_channel.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(y_channel.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Histogramme des gradients
        hist, _ = np.histogram(gradient_magnitude.flatten(), bins=64, range=(0, 100))
        hist_norm = hist / np.sum(hist)
        
        # Mesure de "spikiness" (quantification crée des pics)
        spikiness = np.std(hist_norm) / (np.mean(hist_norm) + 1e-10)
        
        return spikiness

    def detect_compression_artifacts_score(self, y_channel):
        """Score artefacts de compression généraux"""
        # Analyse texture/bruit haute fréquence
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]], dtype=np.float32)
        high_freq_response = cv2.filter2D(y_channel.astype(np.float32), -1, kernel)
        
        # Mesure de l'irrégularité (compression crée du bruit)
        noise_level = np.std(high_freq_response)
        mean_response = np.mean(np.abs(high_freq_response))
        
        return noise_level / (mean_response + 1e-10)

    def calculate_entropy_metrics(self, y_channel):
        """Calcul métriques d'entropie détaillées"""
        # Entropie de Shannon
        hist, _ = np.histogram(y_channel.flatten(), bins=256, range=(64, 940))
        hist_norm = hist / np.sum(hist)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        
        # Entropie normalisée (0-1)
        max_entropy = np.log2(256)
        normalized_entropy = entropy / max_entropy
        
        # Complexité (mesure de distribution)
        complexity = np.sum(hist_norm * (hist_norm > 0.001))  # Nombre de bins significatifs
        
        return {
            'entropy': entropy,
            'normalized_entropy': normalized_entropy,
            'complexity': complexity
        }

    def apply_artifact_cleaning_strategy(self, frame_data, artifacts_metrics):
        """Application stratégie nettoyage artefacts"""
        y_original = frame_data['y'].copy()
        
        # Nettoyage adaptatif selon scores d'artefacts
        if artifacts_metrics['blocking_score'] > 5:
            # Déblocking léger
            y_cleaned = cv2.GaussianBlur(y_original.astype(np.float32), (3, 3), 0.5)
        else:
            y_cleaned = y_original.astype(np.float32)
        
        if artifacts_metrics['quantization_score'] > 2:
            # Lissage des paliers
            y_cleaned = cv2.bilateralFilter(y_cleaned.astype(np.uint8), 5, 10, 10).astype(np.float32) * 4
        
        return np.clip(y_cleaned, 64, 940).astype(np.uint16)

    def apply_entropy_clustering_strategy(self, frame_data):
        """Application clustering pour réduction entropie"""
        y_original = frame_data['y']
        height, width = y_original.shape
        
        # K-means clustering des valeurs
        pixels = y_original.flatten().reshape(-1, 1)
        n_clusters = min(128, len(np.unique(pixels)) // 2)  # Réduction adaptative
        
        if n_clusters < 16:
            return y_original  # Pas assez de variété
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clustered_pixels = kmeans.fit_predict(pixels)
        
        # Reconstruction
        cluster_centers = kmeans.cluster_centers_.flatten()
        reconstructed = cluster_centers[clustered_pixels].reshape(height, width)
        
        return reconstructed.astype(np.uint16)

    def apply_perceptual_optimization_strategy(self, frame_data):
        """Application optimisation perceptuelle"""
        y_original = frame_data['y']
        
        # Détection régions d'intérêt
        edges = cv2.Canny((y_original / 4).astype(np.uint8), 50, 150)
        roi_mask = edges.astype(np.float32) / 255
        
        # Quantification variable selon ROI
        quantized = y_original.copy().astype(np.float32)
        
        # Zones importantes : quantification fine
        important_mask = roi_mask > 0.3
        quantized[important_mask] = np.round(quantized[important_mask] / 1) * 1
        
        # Zones moins importantes : quantification plus agressive
        unimportant_mask = roi_mask <= 0.3
        quantized[unimportant_mask] = np.round(quantized[unimportant_mask] / 4) * 4
        
        return np.clip(quantized, 64, 940).astype(np.uint16)

    def calculate_compression_potential_metrics(self, original_frame, processed_frame):
        """Calcul métriques potentiel de compression"""
        # Entropie avant/après
        entropy_original = self.calculate_entropy_metrics(original_frame)
        entropy_processed = self.calculate_entropy_metrics(processed_frame)
        
        # Réduction entropie
        entropy_reduction = (entropy_original['entropy'] - entropy_processed['entropy']) / entropy_original['entropy']
        
        # Estimation gain compression (approximation)
        estimated_compression_gain = entropy_reduction * 0.7  # Facteur empirique
        
        # Mesure de préservation qualité (PSNR simplifié)
        mse = np.mean((original_frame.astype(np.float32) - processed_frame.astype(np.float32)) ** 2)
        psnr = 20 * np.log10(940 / (np.sqrt(mse) + 1e-10))  # 940 = max value 10-bit
        
        return {
            'entropy_reduction_percent': entropy_reduction * 100,
            'estimated_compression_gain_percent': estimated_compression_gain * 100,
            'psnr_db': psnr,
            'quality_preservation': min(100, max(0, (psnr - 30) / 20 * 100))  # Score 0-100
        }

    def run_hybrid_metrics_test(self):
        """Test complet métriques hybrides sur B3.mp4"""
        print("=" * 80)
        print("🔬 TEST MÉTRIQUES HYBRIDES HCV16 SUR B3.MP4")
        print("=" * 80)
        
        # Chargement échantillon
        frames, video_info = self.load_b3_sample(max_frames=5)
        if not frames:
            return None
        
        print(f"\n📊 Contexte test:")
        print(f"  Résolution: {video_info['width']}×{video_info['height']}")
        print(f"  Frames analysées: {len(frames)}")
        print(f"  Source: {video_info['source_type']}")
        
        # Analyse artefacts sur échantillon
        print(f"\n🔍 ANALYSE ARTEFACTS H.264:")
        
        artifacts_analysis = []
        for frame in frames:
            artifacts = self.analyze_h264_artifacts_metrics(frame)
            artifacts_analysis.append(artifacts)
        
        # Moyennes des métriques d'artefacts
        avg_artifacts = {
            'blocking_score': np.mean([a['blocking_score'] for a in artifacts_analysis]),
            'quantization_score': np.mean([a['quantization_score'] for a in artifacts_analysis]),
            'compression_score': np.mean([a['compression_score'] for a in artifacts_analysis]),
            'entropy_original': np.mean([a['entropy_original'] for a in artifacts_analysis]),
            'total_artifact_score': np.mean([a['total_artifact_score'] for a in artifacts_analysis])
        }
        
        print(f"  Score artefacts blocs: {avg_artifacts['blocking_score']:.2f}")
        print(f"  Score quantification: {avg_artifacts['quantization_score']:.2f}")
        print(f"  Score compression: {avg_artifacts['compression_score']:.2f}")
        print(f"  Entropie moyenne: {avg_artifacts['entropy_original']:.2f} bits/symbole")
        print(f"  Score total artefacts: {avg_artifacts['total_artifact_score']:.2f}")
        
        # Test des stratégies hybrides
        strategies_results = {}
        
        strategies = [
            ('original', lambda f, a: f['y']),
            ('artifact_cleaning', lambda f, a: self.apply_artifact_cleaning_strategy(f, a)),
            ('entropy_clustering', lambda f, a: self.apply_entropy_clustering_strategy(f)),
            ('perceptual_optimization', lambda f, a: self.apply_perceptual_optimization_strategy(f))
        ]
        
        for strategy_name, strategy_func in strategies:
            print(f"\n{'='*60}")
            print(f"STRATÉGIE: {strategy_name.upper()}")
            print(f"{'='*60}")
            
            strategy_metrics = []
            
            for i, frame in enumerate(frames):
                artifacts = artifacts_analysis[i]
                
                # Application stratégie
                if strategy_name == 'original':
                    processed_frame = strategy_func(frame, artifacts)
                else:
                    processed_frame = strategy_func(frame, artifacts)
                
                # Calcul métriques compression
                compression_metrics = self.calculate_compression_potential_metrics(
                    frame['y'], processed_frame)
                
                strategy_metrics.append(compression_metrics)
            
            # Moyennes des métriques
            avg_metrics = {
                'entropy_reduction_percent': np.mean([m['entropy_reduction_percent'] for m in strategy_metrics]),
                'estimated_compression_gain_percent': np.mean([m['estimated_compression_gain_percent'] for m in strategy_metrics]),
                'psnr_db': np.mean([m['psnr_db'] for m in strategy_metrics]),
                'quality_preservation': np.mean([m['quality_preservation'] for m in strategy_metrics])
            }
            
            strategies_results[strategy_name] = avg_metrics
            
            print(f"  Réduction entropie: {avg_metrics['entropy_reduction_percent']:.1f}%")
            print(f"  Gain compression estimé: {avg_metrics['estimated_compression_gain_percent']:.1f}%")
            print(f"  PSNR: {avg_metrics['psnr_db']:.1f} dB")
            print(f"  Préservation qualité: {avg_metrics['quality_preservation']:.1f}%")
            
            # Évaluation stratégie
            if avg_metrics['estimated_compression_gain_percent'] > 15 and avg_metrics['quality_preservation'] > 80:
                evaluation = "🎯 EXCELLENTE"
            elif avg_metrics['estimated_compression_gain_percent'] > 10 and avg_metrics['quality_preservation'] > 70:
                evaluation = "✅ BONNE"
            elif avg_metrics['estimated_compression_gain_percent'] > 5:
                evaluation = "⚠️ MODÉRÉE"
            else:
                evaluation = "❌ INSUFFISANTE"
            
            print(f"  Évaluation: {evaluation}")
        
        # Comparaison avec approche SIMD
        print(f"\n{'='*80}")
        print("📊 COMPARAISON APPROCHES")
        print(f"{'='*80}")
        
        # Chargement résultats SIMD si disponibles
        simd_results = None
        if os.path.exists('b3_simd_complete_results.json'):
            with open('b3_simd_complete_results.json', 'r') as f:
                simd_results = json.load(f)
        
        print(f"\n🔄 APPROCHE SIMD (si disponible):")
        if simd_results:
            best_simd = simd_results['modes_results']['archive_simd']
            print(f"  Ratio compression: {best_simd['compression_ratio']:.2f}×")
            print(f"  Performance: {best_simd['fps_simd']:.1f} fps")
            print(f"  Temps réel: {'✅' if best_simd['realtime_30fps'] else '❌'}")
        else:
            print("  ⚠️ Résultats SIMD non disponibles")
        
        print(f"\n🔬 APPROCHE HYBRIDE:")
        best_hybrid = max(strategies_results.keys(), 
                         key=lambda k: strategies_results[k]['estimated_compression_gain_percent'])
        best_hybrid_metrics = strategies_results[best_hybrid]
        
        print(f"  Meilleure stratégie: {best_hybrid.upper()}")
        print(f"  Gain compression: {best_hybrid_metrics['estimated_compression_gain_percent']:.1f}%")
        print(f"  Préservation qualité: {best_hybrid_metrics['quality_preservation']:.1f}%")
        print(f"  PSNR: {best_hybrid_metrics['psnr_db']:.1f} dB")
        
        # Recommandations
        print(f"\n🎯 RECOMMANDATIONS:")
        
        if avg_artifacts['total_artifact_score'] > 10:
            print("  • Artefacts H.264 significatifs détectés")
            print("  • Stratégie hybride recommandée (nettoyage + optimisation)")
            print("  • Pipeline: Analyse → Nettoyage → Compression optimisée")
        else:
            print("  • Artefacts H.264 modérés")
            print("  • Approche SIMD directe peut suffire")
            print("  • Optimisations perceptuelles optionnelles")
        
        # Sauvegarde résultats
        final_results = {
            'video_info': video_info,
            'artifacts_analysis': avg_artifacts,
            'strategies_results': strategies_results,
            'best_hybrid_strategy': best_hybrid,
            'recommendations': {
                'artifact_level': 'high' if avg_artifacts['total_artifact_score'] > 10 else 'moderate',
                'recommended_approach': 'hybrid' if avg_artifacts['total_artifact_score'] > 10 else 'simd_direct'
            }
        }
        
        with open('hcv16_hybrid_metrics_results.json', 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        print(f"\n📁 Résultats sauvegardés: hcv16_hybrid_metrics_results.json")
        
        return final_results

def main():
    tester = HCV16HybridMetricsTester()
    results = tester.run_hybrid_metrics_test()
    
    if results:
        print(f"\n🎉 TEST MÉTRIQUES HYBRIDES TERMINÉ!")
        print(f"✅ Analyse complète des stratégies d'optimisation pour B3.mp4")
    else:
        print(f"\n❌ Échec du test métriques hybrides")

if __name__ == "__main__":
    main()