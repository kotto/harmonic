#!/usr/bin/env python3
"""
ANALYZERS MODULE
Analyse approfondie des caractéristiques d'images
"""

import numpy as np
import cv2
from typing import Dict, Any, Tuple
from scipy import fft, ndimage
from sklearn.cluster import KMeans

class ImageAnalyzer:
    """
    Analyseur d'images complet pour la compression harmonique
    Inspiré des principes d'analyse de l'upscaling harmonique
    """
    
    def __init__(self):
        self.analysis_cache = {}
    
    def analyze(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyse complète des caractéristiques de l'image
        
        Args:
            image: Image numpy array (H, W) ou (H, W, C)
            
        Returns:
            Dict: Caractéristiques complètes de l'image
        """
        # Vérification du cache
        image_hash = hash(image.tobytes())
        if image_hash in self.analysis_cache:
            return self.analysis_cache[image_hash]
        
        # Analyse multi-niveaux
        characteristics = {
            'structural': self._analyze_structural_properties(image),
            'entropic': self._analyze_entropic_properties(image),
            'frequency': self._analyze_frequency_properties(image),
            'semantic': self._analyze_semantic_properties(image),
            'texture': self._analyze_texture_properties(image)
        }
        
        # Score de complexité unifié
        characteristics['complexity_score'] = self._calculate_complexity_score(characteristics)
        characteristics['resolution'] = image.shape[:2]
        characteristics['channels'] = image.shape[2] if len(image.shape) == 3 else 1
        
        # Mise en cache
        self.analysis_cache[image_hash] = characteristics
        
        return characteristics
    
    def _analyze_structural_properties(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse des propriétés structurelles (contours, formes, symétrie)"""
        
        # Conversion en niveaux de gris si nécessaire
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        h, w = gray.shape
        
        # 1. Détection de contours multiples
        edges_canny = cv2.Canny(gray, 50, 150)
        edges_sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=3)
        edges_laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # Densité de contours
        edge_density_canny = np.sum(edges_canny > 0) / edges_canny.size
        edge_density_sobel = np.sum(np.abs(edges_sobel) > 30) / edges_sobel.size
        edge_density_laplacian = np.sum(np.abs(edges_laplacian) > 20) / edges_laplacian.size
        
        edge_density = (edge_density_canny + edge_density_sobel + edge_density_laplacian) / 3
        
        # 2. Analyse de symétrie multiple
        # Symétrie horizontale
        left_half = gray[:, :w//2]
        right_half = np.fliplr(gray[:, w//2:])
        symmetry_h = np.corrcoef(left_half.flatten(), right_half.flatten())[0,1]
        if np.isnan(symmetry_h):
            symmetry_h = 0.0
        
        # Symétrie verticale
        top_half = gray[:h//2, :]
        bottom_half = np.flipud(gray[h//2:, :])
        symmetry_v = np.corrcoef(top_half.flatten(), bottom_half.flatten())[0,1]
        if np.isnan(symmetry_v):
            symmetry_v = 0.0
        
        # Symétrie diagonale
        diag_symmetry = self._calculate_diagonal_symmetry(gray)
        
        symmetry = max(symmetry_h, symmetry_v, diag_symmetry)
        
        # 3. Détection de formes géométriques
        contours, _ = cv2.findContours(edges_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyse des contours
        contour_areas = [cv2.contourArea(c) for c in contours]
        contour_perimeters = [cv2.arcLength(c, True) for c in contours]
        
        # Circularité moyenne
        circularities = []
        for area, perimeter in zip(contour_areas, contour_perimeters):
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter ** 2)
                circularities.append(min(circularity, 1.0))
        
        avg_circularity = np.mean(circularities) if circularities else 0.0
        
        # 4. Régularité des patterns
        regularity = self._calculate_pattern_regularity(gray)
        
        return {
            'edge_density': edge_density,
            'symmetry_horizontal': max(symmetry_h, 0.0),
            'symmetry_vertical': max(symmetry_v, 0.0),
            'symmetry_diagonal': diag_symmetry,
            'symmetry_overall': symmetry,
            'avg_circularity': avg_circularity,
            'pattern_regularity': regularity,
            'contour_count': len(contours),
            'structural_complexity': edge_density * (1.0 - symmetry) * (1.0 - regularity)
        }
    
    def _analyze_entropic_properties(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse des propriétés entropiques (information, redondance)"""
        
        # Entropie de Shannon par canal
        if len(image.shape) == 3:
            channel_entropies = []
            for channel in range(3):
                channel_data = image[:, :, channel]
                entropy = self._calculate_shannon_entropy(channel_data)
                channel_entropies.append(entropy)
            
            global_entropy = np.mean(channel_entropies)
            max_entropy = 8.0  # Maximum pour 8 bits
            entropy_efficiency = global_entropy / max_entropy
        else:
            global_entropy = self._calculate_shannon_entropy(image)
            entropy_efficiency = global_entropy / 8.0
        
        # Entropie locale (variation spatiale)
        local_entropy = self._calculate_local_entropy(image)
        
        # Redondance spatiale
        spatial_redundancy = self._calculate_spatial_redundancy(image)
        
        # Redondance temporelle (si disponible)
        temporal_redundancy = 0.0  # Placeholder pour futures extensions
        
        # Information mutuelle entre canaux
        mutual_information = 0.0
        if len(image.shape) == 3:
            mutual_information = self._calculate_mutual_information(image)
        
        return {
            'global_entropy': global_entropy,
            'local_entropy': local_entropy,
            'entropy_efficiency': entropy_efficiency,
            'spatial_redundancy': spatial_redundancy,
            'temporal_redundancy': temporal_redundancy,
            'mutual_information': mutual_information,
            'information_density': global_entropy / (image.shape[0] * image.shape[1]),
            'compressibility_potential': spatial_redundancy * entropy_efficiency
        }
    
    def _analyze_frequency_properties(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse des propriétés fréquentielles (FFT, ondelettes)"""
        
        # Conversion en niveaux de gris pour l'analyse fréquentielle
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Transformée de Fourier 2D
        fft_image = fft.fft2(gray)
        fft_shifted = fft.fftshift(fft_image)
        magnitude = np.abs(fft_shifted)
        phase = np.angle(fft_shifted)
        
        h, w = magnitude.shape
        center_y, center_x = h // 2, w // 2
        
        # Analyse par bandes fréquentielles
        # Basses fréquences (centre)
        low_freq_radius = min(h, w) // 8
        y, x = np.ogrid[:h, :w]
        low_freq_mask = (x - center_x)**2 + (y - center_y)**2 <= low_freq_radius**2
        low_freq_energy = np.sum(magnitude[low_freq_mask])
        
        # Fréquences moyennes
        mid_freq_radius = min(h, w) // 4
        mid_freq_mask = ((x - center_x)**2 + (y - center_y)**2 <= mid_freq_radius**2) & ~low_freq_mask
        mid_freq_energy = np.sum(magnitude[mid_freq_mask])
        
        # Hautes fréquences
        high_freq_energy = np.sum(magnitude[~mid_freq_mask & ~low_freq_mask])
        
        total_energy = low_freq_energy + mid_freq_energy + high_freq_energy
        
        # Ratios énergétiques
        low_freq_ratio = low_freq_energy / total_energy
        mid_freq_ratio = mid_freq_energy / total_energy
        high_freq_ratio = high_freq_energy / total_energy
        
        # Analyse de la distribution fréquentielle
        freq_std = np.std(magnitude)
        freq_skewness = self._calculate_skewness(magnitude.flatten())
        freq_kurtosis = self._calculate_kurtosis(magnitude.flatten())
        
        # Fréquence dominante
        dominant_freq_idx = np.unravel_index(np.argmax(magnitude), magnitude.shape)
        dominant_freq_magnitude = magnitude[dominant_freq_idx]
        
        return {
            'low_frequency_ratio': low_freq_ratio,
            'mid_frequency_ratio': mid_freq_ratio,
            'high_frequency_ratio': high_freq_ratio,
            'frequency_spread': freq_std,
            'frequency_skewness': freq_skewness,
            'frequency_kurtosis': freq_kurtosis,
            'dominant_frequency': dominant_freq_idx,
            'dominant_magnitude': dominant_freq_magnitude,
            'spectral_centroid': self._calculate_spectral_centroid(magnitude),
            'spectral_bandwidth': self._calculate_spectral_bandwidth(magnitude)
        }
    
    def _analyze_semantic_properties(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse des propriétés sémantiques (objets, scènes)"""
        
        # Pour l'instant, analyse heuristique simple
        # Dans une version complète, utiliserait des réseaux de neurones
        
        h, w = image.shape[:2]
        
        # Détection de régions uniformes (zones "simples")
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Segmentation simple par k-means
        pixel_values = gray.reshape(-1, 1)
        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        kmeans.fit(pixel_values)
        segmented = kmeans.labels_.reshape(gray.shape)
        
        # Analyse des segments
        unique_segments = np.unique(segmented)
        segment_sizes = [np.sum(segmented == seg) for seg in unique_segments]
        
        # Uniformité des segments
        segment_uniformities = []
        for seg in unique_segments:
            mask = segmented == seg
            segment_pixels = gray[mask]
            if len(segment_pixels) > 0:
                uniformity = 1.0 - (np.std(segment_pixels) / 255.0)
                segment_uniformities.append(uniformity)
        
        avg_segment_uniformity = np.mean(segment_uniformities) if segment_uniformities else 0.0
        
        # Complexité sémantique (nombre et variété des segments)
        semantic_complexity = len(unique_segments) / 10.0  # Normalisé
        size_variance = np.var(segment_sizes) / (h * w)  # Normalisé
        
        return {
            'segment_count': len(unique_segments),
            'avg_segment_uniformity': avg_segment_uniformity,
            'segment_size_variance': size_variance,
            'semantic_complexity': min(semantic_complexity, 1.0),
            'scene_complexity': semantic_complexity * (1.0 - avg_segment_uniformity),
            'object_density': len(unique_segments) / (h * w) * 10000  # Normalisé
        }
    
    def _analyze_texture_properties(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse des propriétés de texture"""
        
        # Conversion en niveaux de gris
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Matrices de co-occurrence (GLCM)
        glcm = self._calculate_glcm(gray, distances=[1, 2], angles=[0, 45, 90, 135])
        
        # Caractéristiques de texture
        contrast = self._calculate_glcm_contrast(glcm)
        dissimilarity = self._calculate_glcm_dissimilarity(glcm)
        homogeneity = self._calculate_glcm_homogeneity(glcm)
        energy = self._calculate_glcm_energy(glcm)
        correlation = self._calculate_glcm_correlation(glcm)
        
        # Analyse par filtres de Gabor
        gabor_responses = []
        for theta in [0, 45, 90, 135]:
            real, _ = cv2.getGaborKernel((15, 15), 3, np.radians(theta), 10.0, 0.5, 0, ktype=cv2.CV_32F)
            filtered = cv2.filter2D(gray, cv2.CV_8UC3, real)
            gabor_responses.append(np.std(filtered))
        
        avg_gabor_response = np.mean(gabor_responses)
        gabor_variance = np.var(gabor_responses)
        
        return {
            'contrast': contrast,
            'dissimilarity': dissimilarity,
            'homogeneity': homogeneity,
            'energy': energy,
            'correlation': correlation,
            'avg_gabor_response': avg_gabor_response,
            'gabor_variance': gabor_variance,
            'texture_complexity': contrast * (1.0 - homogeneity) * avg_gabor_response,
            'texture_directionality': gabor_variance
        }
    
    def _calculate_complexity_score(self, characteristics: Dict[str, Any]) -> float:
        """Calcule un score de complexité unifié (0-1)"""
        
        struct = characteristics['structural']
        entropic = characteristics['entropic']
        freq = characteristics['frequency']
        semantic = characteristics['semantic']
        texture = characteristics['texture']
        
        # Pondération des différentes composantes
        weights = {
            'structural': 0.3,
            'entropic': 0.25,
            'frequency': 0.2,
            'semantic': 0.15,
            'texture': 0.1
        }
        
        # Scores individuels (normalisés 0-1)
        structural_score = min(1.0, struct['structural_complexity'])
        entropic_score = min(1.0, (1.0 - entropic['compressibility_potential']))
        frequency_score = min(1.0, freq['high_frequency_ratio'] + freq['frequency_spread'] / 1000)
        semantic_score = min(1.0, semantic['semantic_complexity'])
        texture_score = min(1.0, texture['texture_complexity'])
        
        # Score composite
        complexity_score = (
            weights['structural'] * structural_score +
            weights['entropic'] * entropic_score +
            weights['frequency'] * frequency_score +
            weights['semantic'] * semantic_score +
            weights['texture'] * texture_score
        )
        
        return min(1.0, complexity_score)
    
    # Méthodes utilitaires pour les calculs
    def _calculate_shannon_entropy(self, data: np.ndarray) -> float:
        """Calcule l'entropie de Shannon"""
        hist, _ = np.histogram(data, bins=256, density=True)
        hist = hist[hist > 0]
        return -np.sum(hist * np.log2(hist + 1e-10))
    
    def _calculate_local_entropy(self, image: np.ndarray, window_size: int = 8) -> float:
        """Calcule l'entropie locale moyenne"""
        h, w = image.shape[:2]
        local_entropies = []
        
        for i in range(0, h - window_size, window_size):
            for j in range(0, w - window_size, window_size):
                window = image[i:i+window_size, j:j+window_size]
                local_ent = self._calculate_shannon_entropy(window)
                local_entropies.append(local_ent)
        
        return np.mean(local_entropies) if local_entropies else 0.0
    
    def _calculate_spatial_redundancy(self, image: np.ndarray) -> float:
        """Calcule la redondance spatiale"""
        h, w = image.shape[:2]
        
        # Prédiction simple par voisinage
        if len(image.shape) == 3:
            predicted = np.zeros_like(image)
            for c in range(3):
                channel = image[:, :, c]
                # Prédiction par moyenne des voisins
                predicted[1:h-1, 1:w-1, c] = (
                    channel[0:h-2, 1:w-1] + channel[2:h, 1:w-1] +
                    channel[1:h-1, 0:w-2] + channel[1:h-1, 2:w]
                ) / 4.0
        else:
            predicted = np.zeros_like(image)
            predicted[1:h-1, 1:w-1] = (
                image[0:h-2, 1:w-1] + image[2:h, 1:w-1] +
                image[1:h-1, 0:w-2] + image[1:h-1, 2:w]
            ) / 4.0
        
        # Erreur de prédiction
        error = np.mean(np.abs(image.astype(np.float32) - predicted))
        redundancy = 1.0 - (error / 255.0)
        
        return max(0.0, min(1.0, redundancy))
    
    def _calculate_mutual_information(self, image: np.ndarray) -> float:
        """Calcule l'information mutuelle entre canaux RGB"""
        if len(image.shape) != 3 or image.shape[2] != 3:
            return 0.0
        
        mi_values = []
        for i in range(3):
            for j in range(i+1, 3):
                channel_i = image[:, :, i].flatten()
                channel_j = image[:, :, j].flatten()
                
                # Histogramme joint
                hist_2d, _, _ = np.histogram2d(channel_i, channel_j, bins=32)
                hist_2d = hist_2d / np.sum(hist_2d)
                
                # Histogrammes marginaux
                hist_i = np.sum(hist_2d, axis=1)
                hist_j = np.sum(hist_2d, axis=0)
                
                # Information mutuelle
                mi = 0.0
                for ii in range(len(hist_i)):
                    for jj in range(len(hist_j)):
                        if hist_2d[ii, jj] > 0 and hist_i[ii] > 0 and hist_j[jj] > 0:
                            mi += hist_2d[ii, jj] * np.log2(
                                hist_2d[ii, jj] / (hist_i[ii] * hist_j[jj])
                            )
                
                mi_values.append(max(0.0, mi))
        
        return np.mean(mi_values) if mi_values else 0.0
    
    def _calculate_diagonal_symmetry(self, gray: np.ndarray) -> float:
        """Calcule la symétrie diagonale"""
        h, w = gray.shape
        min_dim = min(h, w)
        
        # Diagonale principale
        diag_main = np.diagonal(gray[:min_dim, :min_dim])
        diag_flipped = np.fliplr(gray[:min_dim, :min_dim])
        diag_flipped_main = np.diagonal(diag_flipped)
        
        symmetry_main = np.corrcoef(diag_main, diag_flipped_main)[0,1]
        return max(0.0, symmetry_main) if not np.isnan(symmetry_main) else 0.0
    
    def _calculate_pattern_regularity(self, gray: np.ndarray) -> float:
        """Calcule la régularité des patterns"""
        h, w = gray.shape
        
        # Autocorrélation pour détecter la périodicité
        autocorr = ndimage.correlate(gray, gray, mode='constant')
        center = h * w
        
        # Variance de l'autocorrélation autour du centre
        window_size = 20
        start_idx = max(0, center - window_size)
        end_idx = min(len(autocorr), center + window_size)
        
        autocorr_variance = np.var(autocorr[start_idx:end_idx])
        regularity = 1.0 / (1.0 + autocorr_variance / (h * w))
        
        return min(1.0, regularity)
    
    def _calculate_glcm(self, image: np.ndarray, distances: list, angles: list) -> np.ndarray:
        """Calcule la matrice de co-occurrence de niveaux de gris"""
        # Simplification : utilise OpenCV si disponible
        try:
            # Quantification à 8 niveaux pour simplifier
            quantized = (image // 32).astype(np.uint8)
            
            # Calcul GLCM simplifié
            glcm = np.zeros((8, 8, len(distances), len(angles)))
            
            for d_idx, distance in enumerate(distances):
                for a_idx, angle in enumerate(angles):
                    for i in range(8):
                        for j in range(8):
                            # Comptage des co-occurrences
                            mask_i = quantized == i
                            shifted = ndimage.rotate(quantized, angle, reshape=False)
                            mask_j = shifted == i
                            
                            # Décalage selon la distance
                            if distance == 1:
                                shifted_j = np.roll(shifted, 1, axis=1)
                            else:
                                shifted_j = np.roll(np.roll(shifted, distance, axis=0), distance, axis=1)
                            
                            mask_j = shifted_j == j
                            cooccurrence = np.sum(mask_i & mask_j)
                            glcm[i, j, d_idx, a_idx] = cooccurrence
            
            return glcm
            
        except Exception:
            # Fallback : matrice simple
            return np.ones((8, 8, 1, 1))
    
    def _calculate_glcm_contrast(self, glcm: np.ndarray) -> float:
        """Calcule le contraste à partir de GLCM"""
        i, j = np.meshgrid(range(glcm.shape[0]), range(glcm.shape[1]))
        return np.sum(glcm * (i - j) ** 2)
    
    def _calculate_glcm_dissimilarity(self, glcm: np.ndarray) -> float:
        """Calcule la dissimilarité à partir de GLCM"""
        i, j = np.meshgrid(range(glcm.shape[0]), range(glcm.shape[1]))
        return np.sum(glcm * np.abs(i - j))
    
    def _calculate_glcm_homogeneity(self, glcm: np.ndarray) -> float:
        """Calcule l'homogénéité à partir de GLCM"""
        i, j = np.meshgrid(range(glcm.shape[0]), range(glcm.shape[1]))
        return np.sum(glcm / (1 + np.abs(i - j)))
    
    def _calculate_glcm_energy(self, glcm: np.ndarray) -> float:
        """Calcule l'énergie à partir de GLCM"""
        return np.sum(glcm ** 2)
    
    def _calculate_glcm_correlation(self, glcm: np.ndarray) -> float:
        """Calcule la corrélation à partir de GLCM"""
        # Simplification
        return np.sum(glcm) / np.sum(glcm + 1e-10)
    
    def _calculate_spectral_centroid(self, magnitude: np.ndarray) -> float:
        """Calcule le centroïde spectral"""
        h, w = magnitude.shape
        y, x = np.ogrid[:h, :w]
        
        numerator = np.sum(magnitude * np.sqrt(x**2 + y**2))
        denominator = np.sum(magnitude)
        
        return numerator / (denominator + 1e-10)
    
    def _calculate_spectral_bandwidth(self, magnitude: np.ndarray) -> float:
        """Calcule la largeur de bande spectrale"""
        centroid = self._calculate_spectral_centroid(magnitude)
        h, w = magnitude.shape
        y, x = np.ogrid[:h, :w]
        
        distances = np.sqrt(x**2 + y**2)
        bandwidth = np.sqrt(np.sum(magnitude * (distances - centroid)**2) / (np.sum(magnitude) + 1e-10))
        
        return bandwidth
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calcule l'asymétrie (skewness)"""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / (std + 1e-10)) ** 3)
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calcule l'aplatissement (kurtosis)"""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / (std + 1e-10)) ** 4) - 3

class CompressionComplexityAnalyzer:
    """
    Analyseur spécialisé pour la complexité de compression
    """
    
    def analyze_compressibility(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse le potentiel de compressibilité"""
        analyzer = ImageAnalyzer()
        characteristics = analyzer.analyze(image)
        
        # Facteurs de compressibilité
        factors = {
            'low_edge_density': 1.0 - characteristics['structural']['edge_density'],
            'high_symmetry': characteristics['structural']['symmetry_overall'],
            'high_redundancy': characteristics['entropic']['spatial_redundancy'],
            'low_frequency_dominance': characteristics['frequency']['low_frequency_ratio'],
            'low_semantic_complexity': 1.0 - characteristics['semantic']['semantic_complexity'],
            'low_texture_complexity': 1.0 - characteristics['texture']['texture_complexity']
        }
        
        # Score de compressibilité pondéré
        weights = {
            'low_edge_density': 0.25,
            'high_symmetry': 0.20,
            'high_redundancy': 0.25,
            'low_frequency_dominance': 0.15,
            'low_semantic_complexity': 0.10,
            'low_texture_complexity': 0.05
        }
        
        compressibility_score = sum(
            weights[factor] * factors[factor] for factor in factors
        )
        
        # Estimation du ratio de compression
        estimated_ratio = 10.0 + compressibility_score * 990.0  # 10:1 à 1000:1
        
        return {
            'compressibility_score': min(1.0, compressibility_score),
            'estimated_ratio': estimated_ratio,
            'factors': factors,
            'recommended_method': self._recommend_compression_method(characteristics),
            'confidence': min(1.0, compressibility_score * 1.2)
        }
    
    def _recommend_compression_method(self, characteristics: Dict[str, Any]) -> str:
        """Recommande la méthode de compression optimale"""
        struct = characteristics['structural']
        entropic = characteristics['entropic']
        freq = characteristics['frequency']
        
        if struct['symmetry_overall'] > 0.8 and struct['edge_density'] < 0.2:
            return 'structural'
        elif entropic['spatial_redundancy'] > 0.8:
            return 'entropic'
        elif freq['low_frequency_ratio'] > 0.7:
            return 'frequency'
        elif characteristics['complexity_score'] > 0.8:
            return 'quantum_harmonic'
        else:
            return 'adaptive'
