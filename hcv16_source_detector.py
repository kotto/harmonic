#!/usr/bin/env python3
"""
HCV16 Source Detector - Détection automatique du type de source
Choix optimal du modèle selon RAW vs Compressed
"""

import numpy as np
import cv2
import json
from pathlib import Path

class HCV16SourceDetector:
    def __init__(self):
        self.detection_thresholds = {
            'grain_variance_raw': 0.01,      # Variance grain pour RAW
            'compression_artifacts': 0.005,   # Seuil artifacts compression
            'bit_depth_effective': 10,        # Bits effectifs minimum RAW
            'frequency_richness': 0.8         # Richesse fréquentielle RAW
        }
    
    def detect_source_type(self, video_frames):
        """Détection automatique du type de source"""
        print("🔍 Détection du type de source...")
        
        # Analyse sur échantillon de frames
        sample_frames = video_frames[:min(10, len(video_frames))]
        
        # Tests de détection
        grain_analysis = self.analyze_grain_characteristics(sample_frames)
        compression_analysis = self.detect_compression_artifacts(sample_frames)
        bit_depth_analysis = self.analyze_effective_bit_depth(sample_frames)
        frequency_analysis = self.analyze_frequency_content(sample_frames)
        
        # Score de "RAW-ness"
        raw_score = self.calculate_raw_score(
            grain_analysis, 
            compression_analysis, 
            bit_depth_analysis, 
            frequency_analysis
        )
        
        # Décision finale
        source_type = self.determine_source_type(raw_score)
        recommended_strategy = self.recommend_strategy(source_type, raw_score)
        
        result = {
            'source_type': source_type,
            'raw_score': raw_score,
            'recommended_strategy': recommended_strategy,
            'analysis_details': {
                'grain': grain_analysis,
                'compression': compression_analysis,
                'bit_depth': bit_depth_analysis,
                'frequency': frequency_analysis
            }
        }
        
        print(f"📊 Source détectée: {source_type}")
        print(f"🎯 Stratégie recommandée: {recommended_strategy}")
        print(f"📈 Score RAW: {raw_score:.2f}/1.0")
        
        return result
    
    def analyze_grain_characteristics(self, frames):
        """Analyse des caractéristiques du grain"""
        grain_metrics = []
        
        for frame in frames:
            if len(frame.shape) == 3:
                # Conversion en niveaux de gris
                gray = cv2.cvtColor((frame * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
                gray = gray.astype(np.float32) / 255.0
            else:
                gray = frame
            
            # Extraction du grain (filtre passe-haut)
            kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]]) / 8
            grain = cv2.filter2D(gray, -1, kernel)
            
            # Métriques du grain
            grain_variance = np.var(grain)
            grain_mean = np.abs(np.mean(grain))
            grain_distribution = self.test_grain_normality(grain)
            
            grain_metrics.append({
                'variance': grain_variance,
                'mean_abs': grain_mean,
                'normality': grain_distribution
            })
        
        # Moyennes
        avg_variance = np.mean([m['variance'] for m in grain_metrics])
        avg_normality = np.mean([m['normality'] for m in grain_metrics])
        
        # Classification
        is_natural_grain = (
            avg_variance > self.detection_thresholds['grain_variance_raw'] and
            avg_normality > 0.7  # Distribution proche de normale
        )
        
        return {
            'variance': avg_variance,
            'normality': avg_normality,
            'is_natural': is_natural_grain,
            'quality': 'high' if is_natural_grain else 'low'
        }
    
    def detect_compression_artifacts(self, frames):
        """Détection d'artifacts de compression"""
        artifact_scores = []
        
        for frame in frames:
            if len(frame.shape) == 3:
                gray = cv2.cvtColor((frame * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
            else:
                gray = (frame * 255).astype(np.uint8)
            
            # Détection de blocs 8x8 (H.264/H.265)
            block_artifacts = self.detect_block_artifacts(gray)
            
            # Détection de ringing
            ringing_artifacts = self.detect_ringing_artifacts(gray)
            
            # Détection de banding
            banding_artifacts = self.detect_banding_artifacts(gray)
            
            total_artifacts = block_artifacts + ringing_artifacts + banding_artifacts
            artifact_scores.append(total_artifacts)
        
        avg_artifacts = np.mean(artifact_scores)
        
        return {
            'artifact_level': avg_artifacts,
            'is_compressed': avg_artifacts > self.detection_thresholds['compression_artifacts'],
            'confidence': min(avg_artifacts * 10, 1.0)
        }
    
    def analyze_effective_bit_depth(self, frames):
        """Analyse de la profondeur de bits effective"""
        bit_depths = []
        
        for frame in frames:
            # Histogramme des valeurs
            if len(frame.shape) == 3:
                frame_flat = frame.flatten()
            else:
                frame_flat = frame.flatten()
            
            # Conversion en entiers pour histogramme
            values = (frame_flat * 255).astype(np.uint8)
            hist, _ = np.histogram(values, bins=256, range=(0, 255))
            
            # Nombre de bins utilisés
            used_bins = np.sum(hist > 0)
            
            # Estimation de la profondeur effective
            effective_bits = np.log2(used_bins) if used_bins > 0 else 8
            bit_depths.append(effective_bits)
        
        avg_bit_depth = np.mean(bit_depths)
        
        return {
            'effective_bits': avg_bit_depth,
            'is_high_depth': avg_bit_depth > self.detection_thresholds['bit_depth_effective'],
            'utilization': avg_bit_depth / 8.0  # Normalisation sur 8 bits
        }
    
    def analyze_frequency_content(self, frames):
        """Analyse du contenu fréquentiel"""
        frequency_richness = []
        
        for frame in frames:
            if len(frame.shape) == 3:
                gray = cv2.cvtColor((frame * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
            else:
                gray = (frame * 255).astype(np.uint8)
            
            # FFT 2D
            fft = np.fft.fft2(gray)
            fft_magnitude = np.abs(fft)
            
            # Analyse des hautes fréquences
            h, w = fft_magnitude.shape
            high_freq_region = fft_magnitude[h//4:3*h//4, w//4:3*w//4]
            low_freq_region = fft_magnitude[:h//4, :w//4]
            
            # Ratio hautes/basses fréquences
            high_freq_energy = np.mean(high_freq_region)
            low_freq_energy = np.mean(low_freq_region)
            
            richness = high_freq_energy / (low_freq_energy + 1e-6)
            frequency_richness.append(richness)
        
        avg_richness = np.mean(frequency_richness)
        
        return {
            'richness': avg_richness,
            'is_rich': avg_richness > self.detection_thresholds['frequency_richness'],
            'detail_level': 'high' if avg_richness > 1.0 else 'medium' if avg_richness > 0.5 else 'low'
        }
    
    def test_grain_normality(self, grain_data):
        """Test de normalité de la distribution du grain"""
        # Test simplifié de normalité (Shapiro-Wilk approximation)
        sample = grain_data.flatten()[:1000]  # Échantillon pour performance
        
        # Calcul des moments
        mean = np.mean(sample)
        std = np.std(sample)
        
        # Test de symétrie et kurtosis
        skewness = np.mean(((sample - mean) / std) ** 3)
        kurtosis = np.mean(((sample - mean) / std) ** 4) - 3
        
        # Score de normalité (0-1)
        normality_score = max(0, 1 - abs(skewness) - abs(kurtosis) / 2)
        
        return normality_score
    
    def detect_block_artifacts(self, gray_image):
        """Détection d'artifacts de blocs 8x8"""
        h, w = gray_image.shape
        block_score = 0
        
        # Vérification des frontières de blocs 8x8
        for y in range(8, h, 8):
            for x in range(8, w, 8):
                if y < h and x < w:
                    # Différence aux frontières de blocs
                    vertical_diff = abs(int(gray_image[y-1, x]) - int(gray_image[y, x]))
                    horizontal_diff = abs(int(gray_image[y, x-1]) - int(gray_image[y, x]))
                    
                    block_score += (vertical_diff + horizontal_diff) / 2
        
        # Normalisation
        num_blocks = (h // 8) * (w // 8)
        return block_score / (num_blocks * 255) if num_blocks > 0 else 0
    
    def detect_ringing_artifacts(self, gray_image):
        """Détection d'artifacts de ringing"""
        # Filtre de détection des contours
        sobel_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)
        
        # Magnitude du gradient
        gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # Détection de sur-oscillations près des contours
        edges = gradient_magnitude > np.percentile(gradient_magnitude, 90)
        
        # Score de ringing (oscillations près des contours)
        ringing_score = np.std(gradient_magnitude[edges]) / 255 if np.any(edges) else 0
        
        return ringing_score
    
    def detect_banding_artifacts(self, gray_image):
        """Détection d'artifacts de banding"""
        # Histogramme
        hist, _ = np.histogram(gray_image, bins=256, range=(0, 255))
        
        # Détection de pics isolés (banding)
        hist_smooth = cv2.GaussianBlur(hist.astype(np.float32), (5, 1), 1)
        hist_diff = np.abs(hist.astype(np.float32) - hist_smooth.flatten())
        
        # Score de banding
        banding_score = np.mean(hist_diff) / np.max(hist) if np.max(hist) > 0 else 0
        
        return banding_score
    
    def calculate_raw_score(self, grain_analysis, compression_analysis, bit_depth_analysis, frequency_analysis):
        """Calcul du score de "RAW-ness" (0-1)"""
        # Pondération des critères
        weights = {
            'grain_natural': 0.3,
            'no_compression': 0.3,
            'high_bit_depth': 0.2,
            'frequency_rich': 0.2
        }
        
        # Scores individuels
        grain_score = 1.0 if grain_analysis['is_natural'] else 0.0
        compression_score = 0.0 if compression_analysis['is_compressed'] else 1.0
        bit_depth_score = 1.0 if bit_depth_analysis['is_high_depth'] else 0.0
        frequency_score = 1.0 if frequency_analysis['is_rich'] else 0.0
        
        # Score pondéré
        raw_score = (
            weights['grain_natural'] * grain_score +
            weights['no_compression'] * compression_score +
            weights['high_bit_depth'] * bit_depth_score +
            weights['frequency_rich'] * frequency_score
        )
        
        return raw_score
    
    def determine_source_type(self, raw_score):
        """Détermination du type de source"""
        if raw_score >= 0.7:
            return 'RAW'
        elif raw_score >= 0.3:
            return 'LIGHTLY_COMPRESSED'
        else:
            return 'HEAVILY_COMPRESSED'
    
    def recommend_strategy(self, source_type, raw_score):
        """Recommandation de stratégie selon le type de source"""
        if source_type == 'RAW':
            return {
                'strategy': 'C',
                'name': 'Signal + Grain Synthesis',
                'expected_ratio': '300-400×',
                'expected_psnr': '75+ dB',
                'grain_handling': 'synthetic_regeneration'
            }
        elif source_type == 'LIGHTLY_COMPRESSED':
            return {
                'strategy': 'B+',
                'name': 'Enhanced Signal Pure',
                'expected_ratio': '80-150×',
                'expected_psnr': '65+ dB',
                'grain_handling': 'suppressed'
            }
        else:  # HEAVILY_COMPRESSED
            return {
                'strategy': 'B',
                'name': 'Signal Pure',
                'expected_ratio': '20-50×',
                'expected_psnr': '55+ dB',
                'grain_handling': 'suppressed'
            }

def test_source_detection():
    """Test du détecteur de source"""
    detector = HCV16SourceDetector()
    
    # Simulation de frames RAW
    print("=== Test Source RAW ===")
    raw_frames = []
    for i in range(5):
        # Frame avec grain naturel
        frame = np.random.random((540, 960, 3)).astype(np.float32)
        # Ajout de grain gaussien naturel
        grain = np.random.normal(0, 0.02, frame.shape[:2])
        for c in range(3):
            frame[:, :, c] += grain
        frame = np.clip(frame, 0, 1)
        raw_frames.append(frame)
    
    raw_result = detector.detect_source_type(raw_frames)
    
    # Simulation de frames compressées
    print("\n=== Test Source Compressée ===")
    compressed_frames = []
    for i in range(5):
        # Frame avec moins de détails (simulation compression)
        frame = np.random.random((540, 960, 3)).astype(np.float32)
        # Réduction de la richesse fréquentielle
        frame = cv2.GaussianBlur(frame, (3, 3), 1)
        # Quantification (simulation artifacts)
        frame = np.round(frame * 64) / 64
        compressed_frames.append(frame)
    
    compressed_result = detector.detect_source_type(compressed_frames)
    
    # Sauvegarde des résultats
    results = {
        'raw_source': raw_result,
        'compressed_source': compressed_result
    }
    
    with open('source_detection_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nRésultats sauvegardés: source_detection_results.json")
    
    return results

if __name__ == "__main__":
    test_source_detection()