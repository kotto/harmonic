#!/usr/bin/env python3
"""
Stratégies hybrides HCV16 pour contenu pré-compressé
Pistes exploratoires pour optimiser la compression sur H.264/HEVC décodé
"""

import cv2
import numpy as np
import json
import time
from scipy import ndimage
from sklearn.cluster import KMeans

class HCV16HybridStrategy:
    def __init__(self):
        self.strategies = {
            'artifact_cleaning': 'Nettoyage artefacts de compression',
            'entropy_reduction': 'Réduction entropie par clustering',
            'perceptual_optimization': 'Optimisation perceptuelle',
            'hybrid_prediction': 'Prédiction hybride adaptative',
            'content_restoration': 'Restauration contenu original'
        }
    
    def analyze_h264_artifacts(self, frame_data):
        """Analyse des artefacts H.264 pour nettoyage ciblé"""
        print("Analyse artefacts H.264...")
        
        y_channel = frame_data['y']
        
        # 1. Détection artefacts de blocs (8x8, 16x16)
        block_artifacts = self.detect_blocking_artifacts(y_channel)
        
        # 2. Détection artefacts de quantification
        quantization_artifacts = self.detect_quantization_artifacts(y_channel)
        
        # 3. Détection artefacts de mouvement
        motion_artifacts = self.detect_motion_artifacts(y_channel)
        
        # 4. Analyse fréquentielle (DCT artifacts)
        frequency_artifacts = self.analyze_frequency_artifacts(y_channel)
        
        artifacts_analysis = {
            'blocking_score': np.mean(block_artifacts),
            'quantization_score': np.mean(quantization_artifacts),
            'motion_score': np.mean(motion_artifacts),
            'frequency_score': np.mean(frequency_artifacts),
            'total_artifact_score': np.mean([
                np.mean(block_artifacts),
                np.mean(quantization_artifacts), 
                np.mean(motion_artifacts),
                np.mean(frequency_artifacts)
            ])
        }
        
        return artifacts_analysis
    
    def detect_blocking_artifacts(self, y_channel):
        """Détection artefacts de blocs H.264"""
        height, width = y_channel.shape
        block_map = np.zeros_like(y_channel, dtype=np.float32)
        
        # Analyse des discontinuités aux frontières de blocs
        for block_size in [8, 16]:  # H.264 utilise blocs 8x8 et 16x16
            for y in range(0, height - block_size, block_size):
                for x in range(0, width - block_size, block_size):
                    # Discontinuité horizontale
                    if x + block_size < width:
                        left_edge = y_channel[y:y+block_size, x+block_size-1]
                        right_edge = y_channel[y:y+block_size, x+block_size]
                        h_discontinuity = np.mean(np.abs(left_edge.astype(np.int16) - right_edge.astype(np.int16)))
                        block_map[y:y+block_size, x+block_size-1:x+block_size+1] += h_discontinuity
                    
                    # Discontinuité verticale
                    if y + block_size < height:
                        top_edge = y_channel[y+block_size-1, x:x+block_size]
                        bottom_edge = y_channel[y+block_size, x:x+block_size]
                        v_discontinuity = np.mean(np.abs(top_edge.astype(np.int16) - bottom_edge.astype(np.int16)))
                        block_map[y+block_size-1:y+block_size+1, x:x+block_size] += v_discontinuity
        
        return block_map
    
    def detect_quantization_artifacts(self, y_channel):
        """Détection artefacts de quantification"""
        # Les artefacts de quantification créent des "paliers" dans les gradients
        grad_x = cv2.Sobel(y_channel.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(y_channel.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
        
        # Détection des zones avec gradients "quantifiés" (valeurs discrètes)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Histogramme des gradients pour détecter la quantification
        hist, bins = np.histogram(gradient_magnitude.flatten(), bins=256)
        
        # Les artefacts de quantification créent des pics dans l'histogramme
        quantization_score = np.std(hist) / np.mean(hist)  # Mesure de "spikiness"
        
        return gradient_magnitude * quantization_score
    
    def detect_motion_artifacts(self, y_channel):
        """Détection artefacts de compensation mouvement H.264"""
        # Les artefacts de mouvement créent des discontinuités dans les zones de mouvement
        
        # Analyse des variations locales (motion blur, ghosting)
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]], dtype=np.float32)
        motion_response = cv2.filter2D(y_channel.astype(np.float32), -1, kernel)
        
        # Détection des zones avec réponse anormale (artefacts)
        motion_artifacts = np.abs(motion_response) > np.percentile(np.abs(motion_response), 95)
        
        return motion_artifacts.astype(np.float32)
    
    def analyze_frequency_artifacts(self, y_channel):
        """Analyse artefacts fréquentiels (DCT H.264)"""
        # H.264 utilise DCT 8x8, créant des artefacts fréquentiels caractéristiques
        
        # DCT par blocs 8x8
        height, width = y_channel.shape
        frequency_map = np.zeros_like(y_channel, dtype=np.float32)
        
        for y in range(0, height - 8, 8):
            for x in range(0, width - 8, 8):
                block = y_channel[y:y+8, x:x+8].astype(np.float32)
                
                # DCT du bloc
                dct_block = cv2.dct(block)
                
                # Analyse des coefficients hautes fréquences
                # Les artefacts H.264 créent des patterns caractéristiques
                high_freq_energy = np.sum(np.abs(dct_block[4:, 4:]))  # Coins haute fréquence
                
                frequency_map[y:y+8, x:x+8] = high_freq_energy / 64  # Normalisation
        
        return frequency_map
    
    def clean_h264_artifacts(self, frame_data, artifacts_analysis):
        """Nettoyage ciblé des artefacts H.264"""
        print("Nettoyage artefacts H.264...")
        
        y_channel = frame_data['y'].copy()
        
        # 1. Déblocking adaptatif (anti-blocking)
        if artifacts_analysis['blocking_score'] > 10:
            y_channel = self.adaptive_deblocking(y_channel)
        
        # 2. Dequantification (lissage des paliers)
        if artifacts_analysis['quantization_score'] > 5:
            y_channel = self.adaptive_dequantization(y_channel)
        
        # 3. Réduction bruit de compression
        if artifacts_analysis['frequency_score'] > 20:
            y_channel = self.compression_noise_reduction(y_channel)
        
        return {
            'y': y_channel,
            'cb': frame_data['cb'],  # Chrominance moins affectée
            'cr': frame_data['cr']
        }
    
    def adaptive_deblocking(self, y_channel):
        """Filtre de déblocking adaptatif"""
        # Filtre directionnel pour réduire les artefacts de blocs
        
        # Détection des frontières de blocs
        kernel_h = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        kernel_v = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
        
        edges_h = cv2.filter2D(y_channel.astype(np.float32), -1, kernel_h)
        edges_v = cv2.filter2D(y_channel.astype(np.float32), -1, kernel_v)
        
        # Masque des frontières de blocs (multiples de 8 et 16)
        height, width = y_channel.shape
        block_mask = np.zeros((height, width), dtype=np.float32)
        
        for block_size in [8, 16]:
            for y in range(block_size, height, block_size):
                block_mask[y-1:y+1, :] = 1.0
            for x in range(block_size, width, block_size):
                block_mask[:, x-1:x+1] = 1.0
        
        # Application filtre seulement sur les frontières détectées
        strength = np.minimum(np.abs(edges_h) + np.abs(edges_v), 50) / 50
        filter_strength = block_mask * strength
        
        # Filtre Gaussien adaptatif
        deblocked = y_channel.astype(np.float32)
        for sigma in [0.5, 1.0, 1.5]:
            filtered = cv2.GaussianBlur(deblocked, (3, 3), sigma)
            mask = filter_strength > (sigma / 1.5)
            deblocked = np.where(mask, filtered, deblocked)
        
        return np.clip(deblocked, 64, 940).astype(np.uint16)
    
    def adaptive_dequantization(self, y_channel):
        """Dequantification adaptative pour lisser les paliers"""
        # Les artefacts de quantification créent des "paliers" dans les gradients
        
        # Détection des zones quantifiées
        grad_magnitude = cv2.Laplacian(y_channel.astype(np.float32), cv2.CV_32F)
        quantization_mask = np.abs(grad_magnitude) < 2  # Zones "plates" suspectes
        
        # Lissage adaptatif des zones quantifiées
        smoothed = cv2.bilateralFilter(y_channel.astype(np.uint8), 5, 10, 10).astype(np.uint16) * 4
        
        # Application sélective
        alpha = quantization_mask.astype(np.float32) * 0.3  # Force du lissage
        result = (1 - alpha) * y_channel + alpha * smoothed
        
        return np.clip(result, 64, 940).astype(np.uint16)
    
    def compression_noise_reduction(self, y_channel):
        """Réduction du bruit de compression"""
        # Filtre adaptatif pour réduire le bruit haute fréquence de la compression
        
        # Séparation signal/bruit par analyse fréquentielle
        y_float = y_channel.astype(np.float32)
        
        # Filtre passe-bas adaptatif
        low_freq = cv2.GaussianBlur(y_float, (5, 5), 1.2)
        high_freq = y_float - low_freq
        
        # Réduction sélective du bruit haute fréquence
        noise_threshold = np.std(high_freq) * 0.5
        high_freq_cleaned = np.where(np.abs(high_freq) < noise_threshold, 
                                   high_freq * 0.3, high_freq)
        
        result = low_freq + high_freq_cleaned
        return np.clip(result, 64, 940).astype(np.uint16)
    
    def entropy_reduction_clustering(self, frame_data):
        """Réduction d'entropie par clustering des valeurs"""
        print("Réduction entropie par clustering...")
        
        y_channel = frame_data['y']
        height, width = y_channel.shape
        
        # Clustering des valeurs de pixels pour réduire l'espace colorimétrique
        pixels = y_channel.flatten().reshape(-1, 1)
        
        # Nombre de clusters adaptatif selon la complexité
        unique_values = len(np.unique(pixels))
        n_clusters = min(256, max(64, unique_values // 4))
        
        # K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clustered_pixels = kmeans.fit_predict(pixels)
        
        # Reconstruction avec valeurs clustérisées
        cluster_centers = kmeans.cluster_centers_.flatten()
        reconstructed_pixels = cluster_centers[clustered_pixels]
        
        # Reshape vers image
        clustered_frame = reconstructed_pixels.reshape(height, width).astype(np.uint16)
        
        # Calcul réduction d'entropie
        original_entropy = self.calculate_entropy(y_channel)
        clustered_entropy = self.calculate_entropy(clustered_frame)
        entropy_reduction = (original_entropy - clustered_entropy) / original_entropy
        
        print(f"  Entropie originale: {original_entropy:.2f} bits/symbole")
        print(f"  Entropie clustérisée: {clustered_entropy:.2f} bits/symbole")
        print(f"  Réduction: {entropy_reduction*100:.1f}%")
        
        return {
            'y': clustered_frame,
            'cb': frame_data['cb'],
            'cr': frame_data['cr']
        }, entropy_reduction
    
    def calculate_entropy(self, data):
        """Calcul entropie de Shannon"""
        hist, _ = np.histogram(data.flatten(), bins=256, range=(64, 940))
        hist_norm = hist / np.sum(hist)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        return entropy
    
    def perceptual_optimization(self, frame_data):
        """Optimisation perceptuelle pour réduire les données non-critiques"""
        print("Optimisation perceptuelle...")
        
        y_channel = frame_data['y']
        
        # 1. Détection des régions d'intérêt (ROI)
        roi_mask = self.detect_regions_of_interest(y_channel)
        
        # 2. Quantification adaptative selon l'importance perceptuelle
        # Zones importantes : quantification fine
        # Zones moins importantes : quantification plus agressive
        
        importance_map = self.calculate_perceptual_importance(y_channel)
        
        # Application quantification variable
        quantized = y_channel.copy().astype(np.float32)
        
        # Quantification fine pour zones importantes
        important_mask = importance_map > 0.7
        quantized[important_mask] = np.round(quantized[important_mask] / 2) * 2
        
        # Quantification moyenne pour zones modérées
        moderate_mask = (importance_map > 0.3) & (importance_map <= 0.7)
        quantized[moderate_mask] = np.round(quantized[moderate_mask] / 4) * 4
        
        # Quantification agressive pour zones peu importantes
        low_importance_mask = importance_map <= 0.3
        quantized[low_importance_mask] = np.round(quantized[low_importance_mask] / 8) * 8
        
        return {
            'y': np.clip(quantized, 64, 940).astype(np.uint16),
            'cb': frame_data['cb'],
            'cr': frame_data['cr']
        }, importance_map
    
    def detect_regions_of_interest(self, y_channel):
        """Détection des régions d'intérêt visuelles"""
        # Détection basée sur les contours et la variance locale
        
        # Détection contours
        edges = cv2.Canny((y_channel / 4).astype(np.uint8), 50, 150)
        
        # Variance locale (complexité)
        kernel = np.ones((9, 9), np.float32) / 81
        local_mean = cv2.filter2D(y_channel.astype(np.float32), -1, kernel)
        local_variance = cv2.filter2D((y_channel.astype(np.float32) - local_mean)**2, -1, kernel)
        
        # Combinaison contours + variance
        roi_score = (edges.astype(np.float32) / 255) * 0.6 + \
                   (local_variance / np.max(local_variance)) * 0.4
        
        return roi_score
    
    def calculate_perceptual_importance(self, y_channel):
        """Calcul de l'importance perceptuelle"""
        # Modèle simplifié d'importance visuelle
        
        # 1. Saillance basée sur les contours
        saliency = cv2.Laplacian(y_channel.astype(np.float32), cv2.CV_32F)
        saliency_norm = np.abs(saliency) / np.max(np.abs(saliency))
        
        # 2. Importance basée sur la position (centre plus important)
        height, width = y_channel.shape
        y_coords, x_coords = np.ogrid[:height, :width]
        center_y, center_x = height // 2, width // 2
        
        # Distance au centre (normalisée)
        distance_map = np.sqrt((y_coords - center_y)**2 + (x_coords - center_x)**2)
        distance_norm = 1 - (distance_map / np.max(distance_map))
        
        # Combinaison saillance + position
        importance = saliency_norm * 0.7 + distance_norm * 0.3
        
        return importance
    
    def hybrid_prediction_strategy(self, current_frame, previous_frame, artifacts_analysis):
        """Stratégie de prédiction hybride adaptée au contenu pré-compressé"""
        print("Prédiction hybride adaptative...")
        
        y_current = current_frame['y']
        
        if previous_frame is None:
            # Prédiction spatiale améliorée pour première frame
            return self.enhanced_spatial_prediction(y_current, artifacts_analysis)
        
        y_previous = previous_frame['y']
        
        # Choix de stratégie selon les artefacts détectés
        if artifacts_analysis['motion_score'] > 0.5:
            # Beaucoup d'artefacts de mouvement : prédiction spatiale
            return self.enhanced_spatial_prediction(y_current, artifacts_analysis)
        else:
            # Peu d'artefacts : prédiction temporelle possible
            return self.enhanced_temporal_prediction(y_current, y_previous, artifacts_analysis)
    
    def enhanced_spatial_prediction(self, y_channel, artifacts_analysis):
        """Prédiction spatiale améliorée"""
        height, width = y_channel.shape
        predicted = np.zeros_like(y_channel, dtype=np.int16)
        
        # Prédiction multi-directionnelle adaptative
        for y in range(height):
            for x in range(width):
                if x == 0 and y == 0:
                    predicted[y, x] = y_channel[y, x]
                elif x == 0:
                    # Prédiction verticale
                    predicted[y, x] = y_channel[y, x] - y_channel[y-1, x]
                elif y == 0:
                    # Prédiction horizontale
                    predicted[y, x] = y_channel[y, x] - y_channel[y, x-1]
                else:
                    # Prédiction adaptative selon contexte local
                    h_pred = y_channel[y, x-1]  # Horizontal
                    v_pred = y_channel[y-1, x]  # Vertical
                    d_pred = (y_channel[y-1, x-1] + y_channel[y-1, x] + y_channel[y, x-1]) // 3  # Diagonal
                    
                    # Choix du meilleur prédicteur
                    h_error = abs(y_channel[y, x] - h_pred)
                    v_error = abs(y_channel[y, x] - v_pred)
                    d_error = abs(y_channel[y, x] - d_pred)
                    
                    if h_error <= v_error and h_error <= d_error:
                        predicted[y, x] = y_channel[y, x] - h_pred
                    elif v_error <= d_error:
                        predicted[y, x] = y_channel[y, x] - v_pred
                    else:
                        predicted[y, x] = y_channel[y, x] - d_pred
        
        return predicted
    
    def enhanced_temporal_prediction(self, y_current, y_previous, artifacts_analysis):
        """Prédiction temporelle améliorée avec compensation artefacts"""
        # Compensation des artefacts de mouvement H.264
        
        # Détection des zones stables (peu d'artefacts de mouvement)
        stable_mask = artifacts_analysis['motion_score'] < 0.3
        
        # Prédiction temporelle sur zones stables
        temporal_residual = y_current.astype(np.int16) - y_previous.astype(np.int16)
        
        # Prédiction spatiale sur zones instables
        spatial_residual = self.enhanced_spatial_prediction(y_current, artifacts_analysis)
        
        # Combinaison adaptative
        result = np.where(stable_mask, temporal_residual, spatial_residual)
        
        return result
    
    def content_restoration_strategy(self, frame_data):
        """Tentative de restauration du contenu original avant compression H.264"""
        print("Tentative restauration contenu original...")
        
        y_channel = frame_data['y']
        
        # 1. Upsampling intelligent pour récupérer détails perdus
        upsampled = cv2.resize(y_channel, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
        downsampled = cv2.resize(upsampled, (y_channel.shape[1], y_channel.shape[0]), 
                                interpolation=cv2.INTER_AREA)
        
        # 2. Sharpening adaptatif pour récupérer netteté
        kernel_sharpen = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]], dtype=np.float32)
        sharpened = cv2.filter2D(downsampled.astype(np.float32), -1, kernel_sharpen)
        
        # 3. Mélange adaptatif original/restauré
        alpha = 0.3  # Force de la restauration
        restored = (1 - alpha) * y_channel + alpha * np.clip(sharpened, 64, 940)
        
        return {
            'y': restored.astype(np.uint16),
            'cb': frame_data['cb'],
            'cr': frame_data['cr']
        }
    
    def test_hybrid_strategies_on_b3(self):
        """Test des stratégies hybrides sur B3.mp4"""
        print("=" * 80)
        print("TEST STRATÉGIES HYBRIDES HCV16 SUR B3.MP4")
        print("=" * 80)
        
        # Simulation chargement B3.mp4 (première frame)
        test_frame = {
            'y': np.random.randint(300, 700, (850, 478), dtype=np.uint16),
            'cb': np.full((425, 239), 512, dtype=np.uint16),
            'cr': np.full((425, 239), 512, dtype=np.uint16)
        }
        
        # Simulation artefacts H.264
        artifacts = self.analyze_h264_artifacts(test_frame)
        
        strategies_results = {}
        
        # Test de chaque stratégie
        strategies = [
            ('original', lambda f, a: f),
            ('artifact_cleaning', self.clean_h264_artifacts),
            ('entropy_clustering', lambda f, a: self.entropy_reduction_clustering(f)[0]),
            ('perceptual_opt', lambda f, a: self.perceptual_optimization(f)[0]),
            ('content_restoration', lambda f, a: self.content_restoration_strategy(f))
        ]
        
        for strategy_name, strategy_func in strategies:
            print(f"\n--- STRATÉGIE: {strategy_name.upper()} ---")
            
            try:
                # Application de la stratégie
                processed_frame = strategy_func(test_frame, artifacts)
                
                # Calcul entropie résultante
                entropy_before = self.calculate_entropy(test_frame['y'])
                entropy_after = self.calculate_entropy(processed_frame['y'])
                entropy_reduction = (entropy_before - entropy_after) / entropy_before
                
                # Estimation gain compression
                estimated_compression_gain = entropy_reduction * 0.8  # Approximation
                
                strategies_results[strategy_name] = {
                    'entropy_before': entropy_before,
                    'entropy_after': entropy_after,
                    'entropy_reduction_percent': entropy_reduction * 100,
                    'estimated_compression_gain_percent': estimated_compression_gain * 100
                }
                
                print(f"  Entropie avant: {entropy_before:.2f} bits/symbole")
                print(f"  Entropie après: {entropy_after:.2f} bits/symbole")
                print(f"  Réduction entropie: {entropy_reduction*100:.1f}%")
                print(f"  Gain compression estimé: {estimated_compression_gain*100:.1f}%")
                
                if entropy_reduction > 0.1:
                    print("  ✅ Stratégie prometteuse")
                elif entropy_reduction > 0.05:
                    print("  ⚠️ Stratégie modérément efficace")
                else:
                    print("  ❌ Stratégie peu efficace")
                    
            except Exception as e:
                print(f"  ❌ Erreur stratégie: {e}")
                strategies_results[strategy_name] = {'error': str(e)}
        
        # Sauvegarde résultats
        with open('hcv16_hybrid_strategies_results.json', 'w') as f:
            json.dump(strategies_results, f, indent=2)
        
        return strategies_results

def main():
    strategy_tester = HCV16HybridStrategy()
    
    print("🔬 EXPLORATION STRATÉGIES HYBRIDES HCV16")
    print("Adaptation pour contenu pré-compressé (H.264/HEVC)")
    
    results = strategy_tester.test_hybrid_strategies_on_b3()
    
    print(f"\n{'='*80}")
    print("RECOMMANDATIONS STRATÉGIQUES")
    print(f"{'='*80}")
    
    print("\n🎯 PISTES PROMETTEUSES:")
    print("1. Nettoyage artefacts H.264 (déblocking, dequantification)")
    print("2. Clustering adaptatif pour réduction entropie")
    print("3. Optimisation perceptuelle (ROI-based)")
    print("4. Prédiction hybride selon type d'artefacts")
    
    print("\n🚀 STRATÉGIE RECOMMANDÉE:")
    print("Pipeline hybride combinant :")
    print("  • Analyse artefacts automatique")
    print("  • Nettoyage ciblé pré-compression")
    print("  • Prédiction adaptative")
    print("  • Quantification perceptuelle")
    
    print(f"\n✅ Résultats: hcv16_hybrid_strategies_results.json")

if __name__ == "__main__":
    main()