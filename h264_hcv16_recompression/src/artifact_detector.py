#!/usr/bin/env python3
"""
Artifact Detector
Détection spécialisée d'artefacts H.264 exploitables par HCV16
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import ndimage
from skimage import feature, filters

class ArtifactDetector:
    """Détecteur d'artefacts spécialisé pour optimisation HCV16"""
    
    def __init__(self):
        self.detection_cache = {}
        
    def detect_all_artifacts(self, frame: np.ndarray) -> Dict:
        """Détection complète de tous les artefacts"""
        
        # Conversion en niveaux de gris si nécessaire
        if len(frame.shape) == 3:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_frame = frame
            
        results = {
            'blocking_artifacts': self.detect_blocking_artifacts(gray_frame),
            'ringing_artifacts': self.detect_ringing_artifacts(gray_frame),
            'mosquito_noise': self.detect_mosquito_noise(gray_frame),
            'quantization_noise': self.detect_quantization_noise(gray_frame),
            'motion_blur': self.detect_motion_blur(gray_frame),
            'compression_patterns': self.detect_compression_patterns(gray_frame)
        }
        
        # Score global d'exploitabilité HCV16
        results['hcv16_exploitability'] = self._calculate_exploitability_score(results)
        
        return results
    
    def detect_blocking_artifacts(self, image: np.ndarray) -> Dict:
        """Détection avancée d'artefacts de blocs"""
        
        # 1. Détection grilles 8×8 et 16×16
        block_8_strength = self._detect_block_boundaries(image, 8)
        block_16_strength = self._detect_block_boundaries(image, 16)
        
        # 2. Analyse directionnelle
        horizontal_blocking = self._detect_directional_blocking(image, 'horizontal')
        vertical_blocking = self._detect_directional_blocking(image, 'vertical')
        
        # 3. Analyse fréquentielle
        freq_blocking = self._detect_frequency_blocking(image)
        
        # 4. Score combiné
        combined_score = (block_8_strength + block_16_strength + 
                         horizontal_blocking + vertical_blocking + freq_blocking) / 5
        
        return {
            'block_8_strength': block_8_strength,
            'block_16_strength': block_16_strength,
            'horizontal_strength': horizontal_blocking,
            'vertical_strength': vertical_blocking,
            'frequency_strength': freq_blocking,
            'combined_score': combined_score,
            'severity': self._classify_severity(combined_score),
            'hcv16_gain_potential': self._estimate_blocking_gain(combined_score)
        }
    
    def _detect_block_boundaries(self, image: np.ndarray, block_size: int) -> float:
        """Détection frontières de blocs spécifiques"""
        h, w = image.shape
        
        # Calcul gradients aux frontières de blocs
        boundary_strengths = []
        
        # Frontières verticales
        for x in range(block_size, w, block_size):
            if x < w - 1:
                left_col = image[:, x-1].astype(float)
                right_col = image[:, x].astype(float)
                boundary_strength = np.mean(np.abs(left_col - right_col))
                boundary_strengths.append(boundary_strength)
        
        # Frontières horizontales
        for y in range(block_size, h, block_size):
            if y < h - 1:
                top_row = image[y-1, :].astype(float)
                bottom_row = image[y, :].astype(float)
                boundary_strength = np.mean(np.abs(top_row - bottom_row))
                boundary_strengths.append(boundary_strength)
        
        if boundary_strengths:
            avg_strength = np.mean(boundary_strengths)
            # Normalisation (0-1)
            return min(1.0, avg_strength / 30.0)
        
        return 0.0
    
    def _detect_directional_blocking(self, image: np.ndarray, direction: str) -> float:
        """Détection blocking directionnel"""
        
        if direction == 'horizontal':
            # Filtre détection lignes horizontales
            kernel = np.array([[-1, -1, -1], [2, 2, 2], [-1, -1, -1]])
        else:  # vertical
            # Filtre détection lignes verticales
            kernel = np.array([[-1, 2, -1], [-1, 2, -1], [-1, 2, -1]])
        
        filtered = cv2.filter2D(image.astype(np.float32), -1, kernel)
        
        # Analyse périodicité
        if direction == 'horizontal':
            profile = np.mean(np.abs(filtered), axis=1)
        else:
            profile = np.mean(np.abs(filtered), axis=0)
        
        # Détection pics périodiques (8 ou 16 pixels)
        periodicity_8 = self._detect_periodicity(profile, 8)
        periodicity_16 = self._detect_periodicity(profile, 16)
        
        return max(periodicity_8, periodicity_16)
    
    def _detect_periodicity(self, signal: np.ndarray, period: int) -> float:
        """Détection périodicité dans signal 1D"""
        if len(signal) < period * 3:
            return 0.0
        
        # Autocorrélation pour détecter périodicité
        correlations = []
        for shift in range(period - 2, period + 3):  # Tolérance ±2
            if shift < len(signal):
                corr = np.corrcoef(signal[:-shift], signal[shift:])[0, 1]
                if not np.isnan(corr):
                    correlations.append(abs(corr))
        
        return max(correlations) if correlations else 0.0
    
    def _detect_frequency_blocking(self, image: np.ndarray) -> float:
        """Détection blocking par analyse fréquentielle"""
        
        # FFT 2D
        fft_image = np.fft.fft2(image)
        fft_magnitude = np.abs(fft_image)
        
        h, w = fft_magnitude.shape
        
        # Recherche pics aux fréquences de blocs (1/8 et 1/16)
        freq_8_h = h // 8
        freq_8_w = w // 8
        freq_16_h = h // 16
        freq_16_w = w // 16
        
        # Intensité aux fréquences de blocking
        blocking_intensity = 0
        
        # Pics horizontaux
        if freq_8_h < h:
            blocking_intensity += fft_magnitude[freq_8_h, 0]
        if freq_16_h < h:
            blocking_intensity += fft_magnitude[freq_16_h, 0]
        
        # Pics verticaux
        if freq_8_w < w:
            blocking_intensity += fft_magnitude[0, freq_8_w]
        if freq_16_w < w:
            blocking_intensity += fft_magnitude[0, freq_16_w]
        
        # Normalisation
        total_energy = np.sum(fft_magnitude)
        if total_energy > 0:
            return min(1.0, blocking_intensity / (total_energy * 0.01))
        
        return 0.0
    
    def detect_ringing_artifacts(self, image: np.ndarray) -> Dict:
        """Détection artefacts de ringing (oscillations près des contours)"""
        
        # 1. Détection contours
        edges = cv2.Canny(image, 50, 150)
        
        # 2. Analyse oscillations près des contours
        ringing_strength = self._analyze_edge_oscillations(image, edges)
        
        # 3. Analyse fréquentielle du ringing
        freq_ringing = self._detect_frequency_ringing(image, edges)
        
        combined_score = (ringing_strength + freq_ringing) / 2
        
        return {
            'edge_oscillations': ringing_strength,
            'frequency_ringing': freq_ringing,
            'combined_score': combined_score,
            'severity': self._classify_severity(combined_score),
            'hcv16_gain_potential': combined_score * 0.06  # 6% max gain
        }
    
    def _analyze_edge_oscillations(self, image: np.ndarray, edges: np.ndarray) -> float:
        """Analyse oscillations près des contours"""
        
        # Dilatation des contours pour zone d'analyse
        kernel = np.ones((5, 5), np.uint8)
        edge_region = cv2.dilate(edges, kernel, iterations=1)
        
        # Extraction pixels près des contours
        edge_pixels = image[edge_region > 0]
        
        if len(edge_pixels) < 10:
            return 0.0
        
        # Analyse variance locale (indicateur d'oscillations)
        local_variance = np.var(edge_pixels)
        
        # Normalisation
        return min(1.0, local_variance / 1000.0)
    
    def _detect_frequency_ringing(self, image: np.ndarray, edges: np.ndarray) -> float:
        """Détection ringing par analyse fréquentielle"""
        
        # Masque région près des contours
        kernel = np.ones((7, 7), np.uint8)
        edge_region = cv2.dilate(edges, kernel, iterations=1)
        
        # Application masque
        masked_image = image.copy()
        masked_image[edge_region == 0] = 0
        
        # FFT de la région
        fft_masked = np.fft.fft2(masked_image)
        fft_magnitude = np.abs(fft_masked)
        
        # Analyse hautes fréquences (indicateur de ringing)
        h, w = fft_magnitude.shape
        high_freq_region = fft_magnitude[h//4:3*h//4, w//4:3*w//4]
        
        high_freq_energy = np.sum(high_freq_region)
        total_energy = np.sum(fft_magnitude)
        
        if total_energy > 0:
            return min(1.0, high_freq_energy / (total_energy * 0.1))
        
        return 0.0
    
    def detect_mosquito_noise(self, image: np.ndarray) -> Dict:
        """Détection mosquito noise (bruit autour des contours)"""
        
        # 1. Détection contours forts
        edges = cv2.Canny(image, 100, 200)
        
        # 2. Analyse texture autour des contours
        mosquito_strength = self._analyze_edge_texture(image, edges)
        
        # 3. Détection patterns haute fréquence
        hf_patterns = self._detect_high_frequency_patterns(image, edges)
        
        combined_score = (mosquito_strength + hf_patterns) / 2
        
        return {
            'edge_texture_noise': mosquito_strength,
            'high_frequency_patterns': hf_patterns,
            'combined_score': combined_score,
            'severity': self._classify_severity(combined_score),
            'hcv16_gain_potential': combined_score * 0.04  # 4% max gain
        }
    
    def _analyze_edge_texture(self, image: np.ndarray, edges: np.ndarray) -> float:
        """Analyse texture autour des contours"""
        
        # Zone d'analyse autour des contours
        kernel = np.ones((9, 9), np.uint8)
        edge_region = cv2.dilate(edges, kernel, iterations=1)
        edge_region = edge_region - edges  # Seulement la zone autour
        
        if np.sum(edge_region) == 0:
            return 0.0
        
        # Calcul Local Binary Pattern pour texture
        from skimage.feature import local_binary_pattern
        
        lbp = local_binary_pattern(image, 8, 1, method='uniform')
        
        # Analyse LBP dans région des contours
        edge_lbp = lbp[edge_region > 0]
        
        if len(edge_lbp) < 10:
            return 0.0
        
        # Variance LBP comme indicateur de bruit texture
        lbp_variance = np.var(edge_lbp)
        
        return min(1.0, lbp_variance / 50.0)
    
    def _detect_high_frequency_patterns(self, image: np.ndarray, edges: np.ndarray) -> float:
        """Détection patterns haute fréquence près des contours"""
        
        # Filtre passe-haut
        kernel_hf = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        high_freq = cv2.filter2D(image.astype(np.float32), -1, kernel_hf)
        
        # Zone près des contours
        kernel = np.ones((7, 7), np.uint8)
        edge_region = cv2.dilate(edges, kernel, iterations=1)
        
        # Analyse haute fréquence dans cette zone
        hf_near_edges = high_freq[edge_region > 0]
        
        if len(hf_near_edges) < 10:
            return 0.0
        
        # Énergie haute fréquence
        hf_energy = np.mean(np.abs(hf_near_edges))
        
        return min(1.0, hf_energy / 30.0)
    
    def detect_quantization_noise(self, image: np.ndarray) -> Dict:
        """Détection bruit de quantification"""
        
        # 1. Analyse uniformité du bruit
        noise_uniformity = self._analyze_noise_uniformity(image)
        
        # 2. Détection patterns de quantification
        quant_patterns = self._detect_quantization_patterns(image)
        
        # 3. Analyse grain
        grain_characteristics = self._analyze_grain_structure(image)
        
        combined_score = (noise_uniformity + quant_patterns + grain_characteristics) / 3
        
        return {
            'noise_uniformity': noise_uniformity,
            'quantization_patterns': quant_patterns,
            'grain_characteristics': grain_characteristics,
            'combined_score': combined_score,
            'severity': self._classify_severity(combined_score),
            'grain_synthesis_applicable': combined_score > 0.6,
            'hcv16_gain_potential': combined_score * 0.08  # 8% max gain
        }
    
    def _analyze_noise_uniformity(self, image: np.ndarray) -> float:
        """Analyse uniformité du bruit"""
        
        # Division en blocs pour analyse locale
        h, w = image.shape
        block_size = 32
        
        block_variances = []
        block_means = []
        
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = image[y:y+block_size, x:x+block_size]
                block_variances.append(np.var(block))
                block_means.append(np.mean(block))
        
        if len(block_variances) < 2:
            return 0.0
        
        # Uniformité basée sur consistance des variances
        variance_consistency = 1.0 - (np.std(block_variances) / (np.mean(block_variances) + 1e-6))
        
        # Uniformité basée sur consistance des moyennes
        mean_consistency = 1.0 - (np.std(block_means) / (np.mean(block_means) + 1e-6))
        
        return max(0.0, min(1.0, (variance_consistency + mean_consistency) / 2))
    
    def _detect_quantization_patterns(self, image: np.ndarray) -> float:
        """Détection patterns de quantification"""
        
        # Histogramme pour détecter pics de quantification
        hist, bins = np.histogram(image.flatten(), bins=256, range=(0, 256))
        
        # Recherche de pics réguliers (indicateur de quantification)
        peak_distances = []
        peaks = []
        
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] > np.mean(hist) * 1.2:
                peaks.append(i)
        
        # Calcul distances entre pics
        for i in range(1, len(peaks)):
            peak_distances.append(peaks[i] - peaks[i-1])
        
        if len(peak_distances) < 2:
            return 0.0
        
        # Régularité des distances (indicateur quantification)
        distance_variance = np.var(peak_distances)
        distance_mean = np.mean(peak_distances)
        
        if distance_mean > 0:
            regularity = 1.0 - (distance_variance / (distance_mean ** 2))
            return max(0.0, min(1.0, regularity))
        
        return 0.0
    
    def _analyze_grain_structure(self, image: np.ndarray) -> float:
        """Analyse structure du grain"""
        
        # Filtre passe-haut pour isoler le grain
        kernel = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])
        grain = cv2.filter2D(image.astype(np.float32), -1, kernel)
        
        # Analyse statistique du grain
        grain_std = np.std(grain)
        grain_mean = np.mean(np.abs(grain))
        
        # Analyse fréquentielle du grain
        fft_grain = np.fft.fft2(grain)
        fft_magnitude = np.abs(fft_grain)
        
        # Énergie haute fréquence (caractéristique du grain)
        h, w = fft_magnitude.shape
        hf_region = fft_magnitude[h//3:, w//3:]
        hf_energy = np.sum(hf_region)
        total_energy = np.sum(fft_magnitude)
        
        if total_energy > 0:
            hf_ratio = hf_energy / total_energy
        else:
            hf_ratio = 0.0
        
        # Score combiné
        grain_score = (grain_std / 50.0 + hf_ratio) / 2
        
        return min(1.0, grain_score)
    
    def detect_motion_blur(self, image: np.ndarray) -> Dict:
        """Détection flou de mouvement"""
        
        # 1. Analyse directionnelle du flou
        blur_directions = self._analyze_blur_directions(image)
        
        # 2. Estimation intensité du flou
        blur_intensity = self._estimate_blur_intensity(image)
        
        # 3. Détection patterns de mouvement
        motion_patterns = self._detect_motion_patterns(image)
        
        combined_score = (blur_intensity + motion_patterns) / 2
        
        return {
            'blur_directions': blur_directions,
            'blur_intensity': blur_intensity,
            'motion_patterns': motion_patterns,
            'combined_score': combined_score,
            'severity': self._classify_severity(combined_score),
            'hcv16_gain_potential': combined_score * 0.05  # 5% max gain
        }
    
    def _analyze_blur_directions(self, image: np.ndarray) -> Dict:
        """Analyse directions du flou"""
        
        # Filtres directionnels
        kernels = {
            'horizontal': np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]),
            'vertical': np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]),
            'diagonal1': np.array([[0, 1, 2], [-1, 0, 1], [-2, -1, 0]]),
            'diagonal2': np.array([[2, 1, 0], [1, 0, -1], [0, -1, -2]])
        }
        
        direction_strengths = {}
        
        for direction, kernel in kernels.items():
            filtered = cv2.filter2D(image.astype(np.float32), -1, kernel)
            strength = np.mean(np.abs(filtered))
            direction_strengths[direction] = strength
        
        # Normalisation
        max_strength = max(direction_strengths.values())
        if max_strength > 0:
            for direction in direction_strengths:
                direction_strengths[direction] /= max_strength
        
        return direction_strengths
    
    def _estimate_blur_intensity(self, image: np.ndarray) -> float:
        """Estimation intensité du flou"""
        
        # Variance du Laplacien (mesure de netteté)
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        laplacian_var = np.var(laplacian)
        
        # Conversion en score de flou (inverse de la netteté)
        # Plus la variance est faible, plus l'image est floue
        blur_score = 1.0 - min(1.0, laplacian_var / 1000.0)
        
        return max(0.0, blur_score)
    
    def _detect_motion_patterns(self, image: np.ndarray) -> float:
        """Détection patterns de mouvement"""
        
        # Analyse texture directionnelle
        # Utilisation de filtres de Gabor pour détecter orientations préférentielles
        
        angles = [0, 45, 90, 135]  # Angles en degrés
        responses = []
        
        for angle in angles:
            # Filtre de Gabor simplifié
            kernel = cv2.getGaborKernel((15, 15), 3, np.radians(angle), 2*np.pi/3, 0.5, 0, ktype=cv2.CV_32F)
            filtered = cv2.filter2D(image.astype(np.float32), -1, kernel)
            response = np.mean(np.abs(filtered))
            responses.append(response)
        
        # Détection orientation dominante (indicateur de mouvement directionnel)
        if max(responses) > 0:
            orientation_strength = max(responses) / (np.mean(responses) + 1e-6)
            return min(1.0, (orientation_strength - 1.0) / 2.0)
        
        return 0.0
    
    def detect_compression_patterns(self, image: np.ndarray) -> Dict:
        """Détection patterns généraux de compression"""
        
        # 1. Analyse entropie locale
        local_entropy = self._calculate_local_entropy(image)
        
        # 2. Détection régularités spatiales
        spatial_regularity = self._detect_spatial_regularity(image)
        
        # 3. Analyse complexité
        complexity_score = self._analyze_complexity(image)
        
        combined_score = (local_entropy + spatial_regularity + complexity_score) / 3
        
        return {
            'local_entropy': local_entropy,
            'spatial_regularity': spatial_regularity,
            'complexity_score': complexity_score,
            'combined_score': combined_score,
            'compressibility': 1.0 - combined_score,  # Inverse de la complexité
            'hcv16_gain_potential': (1.0 - combined_score) * 0.10  # 10% max gain
        }
    
    def _calculate_local_entropy(self, image: np.ndarray) -> float:
        """Calcul entropie locale"""
        
        # Division en blocs
        h, w = image.shape
        block_size = 16
        entropies = []
        
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = image[y:y+block_size, x:x+block_size]
                
                # Histogramme du bloc
                hist, _ = np.histogram(block.flatten(), bins=32, range=(0, 256))
                hist = hist / np.sum(hist)  # Normalisation
                
                # Entropie
                entropy = -np.sum(hist * np.log2(hist + 1e-10))
                entropies.append(entropy)
        
        if entropies:
            avg_entropy = np.mean(entropies)
            return min(1.0, avg_entropy / 5.0)  # Normalisation
        
        return 0.0
    
    def _detect_spatial_regularity(self, image: np.ndarray) -> float:
        """Détection régularités spatiales"""
        
        # Autocorrélation 2D pour détecter patterns répétitifs
        h, w = image.shape
        
        # Calcul sur région centrale pour éviter effets de bord
        center_h, center_w = h // 4, w // 4
        roi = image[center_h:3*center_h, center_w:3*center_w]
        
        # Autocorrélation avec décalages multiples
        correlations = []
        
        for shift_y in range(1, min(16, roi.shape[0] // 4)):
            for shift_x in range(1, min(16, roi.shape[1] // 4)):
                if shift_y < roi.shape[0] and shift_x < roi.shape[1]:
                    roi1 = roi[:-shift_y, :-shift_x]
                    roi2 = roi[shift_y:, shift_x:]
                    
                    if roi1.size > 0 and roi2.size > 0:
                        corr = np.corrcoef(roi1.flatten(), roi2.flatten())[0, 1]
                        if not np.isnan(corr):
                            correlations.append(abs(corr))
        
        if correlations:
            max_correlation = max(correlations)
            return max_correlation
        
        return 0.0
    
    def _analyze_complexity(self, image: np.ndarray) -> float:
        """Analyse complexité de l'image"""
        
        # 1. Complexité basée sur gradients
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        gradient_complexity = np.mean(gradient_magnitude) / 255.0
        
        # 2. Complexité fréquentielle
        fft_image = np.fft.fft2(image)
        fft_magnitude = np.abs(fft_image)
        
        # Énergie haute fréquence
        h, w = fft_magnitude.shape
        hf_region = fft_magnitude[h//4:3*h//4, w//4:3*w//4]
        hf_energy = np.sum(hf_region)
        total_energy = np.sum(fft_magnitude)
        
        freq_complexity = hf_energy / (total_energy + 1e-10)
        
        # 3. Complexité texture
        # Utilisation variance locale
        kernel = np.ones((5, 5), np.float32) / 25
        local_mean = cv2.filter2D(image.astype(np.float32), -1, kernel)
        local_variance = cv2.filter2D((image.astype(np.float32) - local_mean)**2, -1, kernel)
        texture_complexity = np.mean(local_variance) / (255.0**2)
        
        # Score combiné
        combined_complexity = (gradient_complexity + freq_complexity + texture_complexity) / 3
        
        return min(1.0, combined_complexity)
    
    def _calculate_exploitability_score(self, artifacts: Dict) -> Dict:
        """Calcul score global d'exploitabilité HCV16"""
        
        # Pondération des différents artefacts
        weights = {
            'blocking_artifacts': 0.30,  # Impact élevé
            'quantization_noise': 0.25,  # Grain synthesis
            'compression_patterns': 0.20,  # Patterns généraux
            'ringing_artifacts': 0.15,   # Impact modéré
            'mosquito_noise': 0.10       # Impact faible
        }
        
        # Calcul score pondéré
        total_score = 0.0
        total_weight = 0.0
        
        for artifact_type, weight in weights.items():
            if artifact_type in artifacts:
                artifact_score = artifacts[artifact_type].get('combined_score', 0)
                total_score += artifact_score * weight
                total_weight += weight
        
        if total_weight > 0:
            weighted_score = total_score / total_weight
        else:
            weighted_score = 0.0
        
        # Estimation gain HCV16 total
        total_gain = sum(artifacts[art].get('hcv16_gain_potential', 0) 
                        for art in artifacts if isinstance(artifacts[art], dict))
        
        # Classification exploitabilité
        if weighted_score >= 0.7:
            exploitability_level = 'EXCELLENTE'
        elif weighted_score >= 0.5:
            exploitability_level = 'BONNE'
        elif weighted_score >= 0.3:
            exploitability_level = 'MODÉRÉE'
        else:
            exploitability_level = 'FAIBLE'
        
        return {
            'weighted_score': weighted_score,
            'exploitability_level': exploitability_level,
            'estimated_total_gain': total_gain,
            'compression_ratio_estimate': 1.0 + total_gain,
            'poc_recommended': weighted_score >= 0.3
        }
    
    def _classify_severity(self, score: float) -> str:
        """Classification sévérité artefact"""
        if score >= 0.7:
            return 'ÉLEVÉ'
        elif score >= 0.4:
            return 'MODÉRÉ'
        elif score >= 0.2:
            return 'FAIBLE'
        else:
            return 'MINIMAL'
    
    def _estimate_blocking_gain(self, score: float) -> float:
        """Estimation gain HCV16 pour blocking artifacts"""
        # Gain potentiel basé sur intensité des artefacts
        if score >= 0.8:
            return 0.15  # 15% gain
        elif score >= 0.6:
            return 0.10  # 10% gain
        elif score >= 0.4:
            return 0.06  # 6% gain
        elif score >= 0.2:
            return 0.03  # 3% gain
        else:
            return 0.01  # 1% gain minimal