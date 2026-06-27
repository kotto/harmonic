#!/usr/bin/env python3
"""
Moteur de Compression Harmonique HCS
Implémentation complète de la compression guidée par harmoniques et référence
"""

import numpy as np
import cv2
import base64
import time
import tempfile
import os
from typing import Dict, Any, List, Tuple
from scipy import fft
from scipy.signal import find_peaks
import json

# Constantes harmoniques universelles
HARMONIC_CONSTANTS = {
    'golden_ratio': 1.618033988749,      # Φ - proportion divine
    'pi': 3.141592653589793,            # π - circularité
    'e': 2.718281828459045,             # e - croissance naturelle
    'sqrt2': 1.414213562373095,          # √2 - diagonal
    'phi_squared': 2.618033988749,       # Φ² - harmonie supérieure
    'fibonacci_sequence': [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144],
    'harmonic_series': [1, 1/2, 1/3, 1/4, 1/5, 1/6, 1/7, 1/8],
    'prime_harmonics': [2, 3, 5, 7, 11, 13, 17, 19, 23, 29],
    'fundamental_freq': 1.0,              # Fréquence fondamentale
    'golden_angle': np.pi * (3 - np.sqrt(5))  # Angle d'or
}

class HarmonicAnalyzer:
    """Analyseur harmonique pour frames vidéo"""
    
    def __init__(self):
        self.constants = HARMONIC_CONSTANTS
    
    def analyze(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyse harmonique complète d'une frame"""
        
        # Convertir en grayscale pour l'analyse
        if len(frame.shape) == 3:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_frame = frame
        
        # 1. Transformée de Fourier 2D
        fft_2d = fft.fft2(gray_frame)
        fft_shifted = fft.fftshift(fft_2d)
        
        # 2. Décomposition en bandes harmoniques
        harmonic_bands = self._extract_harmonic_bands(fft_shifted)
        
        # 3. Calcul des constantes harmoniques
        harmonic_constants = self._calculate_harmonic_constants(harmonic_bands)
        
        # 4. Détection des fréquences fondamentales
        fundamental_freqs = self._detect_fundamental_frequencies(fft_shifted)
        
        # 5. Distribution d'énergie
        energy_distribution = self._calculate_energy_distribution(fft_shifted)
        
        return {
            'fft_spectrum': fft_shifted,
            'harmonic_bands': harmonic_bands,
            'constants': harmonic_constants,
            'fundamentals': fundamental_freqs,
            'energy_distribution': energy_distribution,
            'frame_shape': frame.shape
        }
    
    def _extract_harmonic_bands(self, fft_spectrum: np.ndarray) -> Dict[str, np.ndarray]:
        """Extraire les bandes harmoniques"""
        
        h, w = fft_spectrum.shape
        center_y, center_x = h // 2, w // 2
        
        # Créer des masques pour différentes bandes
        bands = {}
        
        # Bande basse fréquence (structure globale)
        low_freq_mask = np.zeros((h, w), dtype=bool)
        low_freq_radius = min(h, w) // 8
        y, x = np.ogrid[:h, :w]
        mask = (x - center_x)**2 + (y - center_y)**2 <= low_freq_radius**2
        low_freq_mask[mask] = True
        bands['low_freq'] = fft_spectrum * low_freq_mask
        
        # Bande moyenne fréquence (détails importants)
        mid_freq_mask = np.zeros((h, w), dtype=bool)
        mid_freq_inner = min(h, w) // 8
        mid_freq_outer = min(h, w) // 4
        mask = ((x - center_x)**2 + (y - center_y)**2 >= mid_freq_inner**2) & \
               ((x - center_x)**2 + (y - center_y)**2 <= mid_freq_outer**2)
        mid_freq_mask[mask] = True
        bands['mid_freq'] = fft_spectrum * mid_freq_mask
        
        # Bande haute fréquence (finesse)
        high_freq_mask = np.zeros((h, w), dtype=bool)
        high_freq_inner = min(h, w) // 4
        high_freq_outer = min(h, w) // 2
        mask = ((x - center_x)**2 + (y - center_y)**2 >= high_freq_inner**2) & \
               ((x - center_x)**2 + (y - center_y)**2 <= high_freq_outer**2)
        high_freq_mask[mask] = True
        bands['high_freq'] = fft_spectrum * high_freq_mask
        
        return bands
    
    def _calculate_harmonic_constants(self, harmonic_bands: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculer les constantes harmoniques"""
        
        constants = {}
        
        # Énergie dans chaque bande
        for band_name, band_data in harmonic_bands.items():
            energy = np.sum(np.abs(band_data)**2)
            constants[f'{band_name}_energy'] = energy
        
        # Ratios harmoniques
        if harmonic_bands['low_freq'].size > 0:
            low_energy = np.sum(np.abs(harmonic_bands['low_freq'])**2)
            mid_energy = np.sum(np.abs(harmonic_bands['mid_freq'])**2)
            high_energy = np.sum(np.abs(harmonic_bands['high_freq'])**2)
            
            total_energy = low_energy + mid_energy + high_energy
            if total_energy > 0:
                constants['low_ratio'] = low_energy / total_energy
                constants['mid_ratio'] = mid_energy / total_energy
                constants['high_ratio'] = high_energy / total_energy
        
        return constants
    
    def _detect_fundamental_frequencies(self, fft_spectrum: np.ndarray) -> List[Tuple[float, float]]:
        """Détecter les fréquences fondamentales"""
        
        # Calculer le spectre de puissance
        power_spectrum = np.abs(fft_spectrum)**2
        
        # Trouver les pics dans le spectre
        h, w = power_spectrum.shape
        center_y, center_x = h // 2, w // 2
        
        # Extraire le profil radial
        y, x = np.ogrid[:h, :w]
        distances = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # Moyenner par distance du centre
        max_distance = int(np.min([center_x, center_y]))
        radial_profile = np.zeros(max_distance)
        
        for r in range(max_distance):
            mask = (distances >= r) & (distances < r + 1)
            if np.any(mask):
                radial_profile[r] = np.mean(power_spectrum[mask])
        
        # Trouver les pics
        peaks, properties = find_peaks(radial_profile, height=np.max(radial_profile) * 0.1)
        
        # Retourner les fréquences fondamentales
        fundamentals = []
        for peak in peaks[:5]:  # Top 5 fréquences
            freq = peak / max_distance  # Normaliser
            amplitude = radial_profile[peak]
            fundamentals.append((freq, amplitude))
        
        return fundamentals
    
    def _calculate_energy_distribution(self, fft_spectrum: np.ndarray) -> np.ndarray:
        """Calculer la distribution d'énergie"""
        
        power_spectrum = np.abs(fft_spectrum)**2
        total_energy = np.sum(power_spectrum)
        
        if total_energy > 0:
            return power_spectrum / total_energy
        else:
            return power_spectrum

class ReferenceCapturer:
    """Captureur de frame de référence optimisée"""
    
    def __init__(self):
        self.harmonic_analyzer = HarmonicAnalyzer()
    
    def capture_optimal_frame(self, video_path: str) -> Dict[str, Any]:
        """Capturer la frame optimale comme référence"""
        
        cap = cv2.VideoCapture(video_path)
        frames_data = []
        
        # Analyser les 30 premières frames
        for i in range(min(30, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))):
            ret, frame = cap.read()
            if ret:
                # Évaluer qualité de la frame
                quality_score = self._evaluate_frame_quality(frame)
                harmonic_analysis = self.harmonic_analyzer.analyze(frame)
                
                frames_data.append({
                    'index': i,
                    'frame': frame,
                    'quality_score': quality_score,
                    'harmonic_analysis': harmonic_analysis
                })
        
        cap.release()
        
        # Sélectionner la meilleure frame
        if frames_data:
            best_frame_data = max(frames_data, key=lambda x: x['quality_score'])
            
            # Sauvegarder en lossless
            reference_path = tempfile.mktemp(suffix='.png')
            cv2.imwrite(reference_path, best_frame_data['frame'], 
                      [cv2.IMWRITE_PNG_COMPRESSION, 0])
            
            return {
                'reference_path': reference_path,
                'frame_index': best_frame_data['index'],
                'frame': best_frame_data['frame'],
                'quality_score': best_frame_data['quality_score'],
                'harmonic_analysis': best_frame_data['harmonic_analysis'],
                'metadata': self._extract_metadata(best_frame_data['frame'])
            }
        
        return None
    
    def _evaluate_frame_quality(self, frame: np.ndarray) -> float:
        """Évaluer la qualité d'une frame"""
        
        # Convertir en grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Calculer différents métriques de qualité
        score = 0.0
        
        # 1. Sharpness (variance du Laplacian)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        score += laplacian_var / 1000.0  # Normaliser
        
        # 2. Contrast (écart-type)
        contrast = np.std(gray)
        score += contrast / 127.0  # Normaliser
        
        # 3. Distribution d'énergie (harmonique)
        fft = np.fft.fft2(gray)
        fft_shifted = np.fft.fftshift(fft)
        power_spectrum = np.abs(fft_shifted)**2
        
        # Préférence pour les basses fréquences
        h, w = power_spectrum.shape
        center_y, center_x = h // 2, w // 2
        low_freq_region = power_spectrum[center_y-h//8:center_y+h//8, 
                                       center_x-w//8:center_x+w//8]
        low_freq_energy = np.sum(low_freq_region)
        total_energy = np.sum(power_spectrum)
        
        if total_energy > 0:
            score += (low_freq_energy / total_energy) * 2.0  # Pondération forte
        
        return score
    
    def _extract_metadata(self, frame: np.ndarray) -> Dict[str, Any]:
        """Extraire les métadonnées de la frame"""
        
        return {
            'resolution': frame.shape[:2],
            'channels': frame.shape[2] if len(frame.shape) == 3 else 1,
            'dtype': str(frame.dtype),
            'dominant_colors': self._get_dominant_colors(frame),
            'brightness': np.mean(frame),
            'contrast': np.std(frame)
        }
    
    def _get_dominant_colors(self, frame: np.ndarray, k: int = 5) -> List[List[int]]:
        """Extraire les couleurs dominantes"""
        
        # Reshape pour K-means
        data = frame.reshape((-1, 3))
        data = np.float32(data)
        
        # K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convertir en entiers
        centers = np.uint8(centers)
        
        return centers.tolist()

class HarmonicCompressor:
    """Compresseur guidé par harmoniques"""
    
    def __init__(self):
        self.constants = HARMONIC_CONSTANTS
        self.harmonic_analyzer = HarmonicAnalyzer()
    
    def compress(self, frame: np.ndarray, frame_harmonics: Dict[str, Any], 
                reference_harmonics: Dict[str, Any]) -> Dict[str, Any]:
        """Compression guidée par harmoniques"""
        
        # 1. Calculer les poids harmoniques
        weights = self._calculate_harmonic_weights(frame_harmonics, reference_harmonics)
        
        # 2. Préservation des fréquences essentielles
        preserved_spectrum = self._preserve_essential_frequencies(
            frame_harmonics['fft_spectrum'],
            weights,
            frame_harmonics['fundamentals']
        )
        
        # 3. Compression adaptative selon harmoniques
        compressed_frame = self._adaptive_harmonic_compression(
            frame,
            preserved_spectrum,
            frame_harmonics['constants']
        )
        
        return {
            'compressed_frame': compressed_frame,
            'harmonic_weights': weights,
            'preserved_frequencies': preserved_spectrum,
            'compression_ratio': self._calculate_compression_ratio(frame, compressed_frame)
        }
    
    def _calculate_harmonic_weights(self, frame_harmonics: Dict[str, Any], 
                                   reference_harmonics: Dict[str, Any]) -> np.ndarray:
        """Calculer les poids harmoniques"""
        
        h, w = frame_harmonics['frame_shape'][:2]
        weights = np.ones((h, w))
        
        # Poids basés sur les constantes harmoniques
        center_y, center_x = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        
        # Distribution spiralée de Fibonacci
        for i, fib_val in enumerate(self.constants['fibonacci_sequence'][:8]):
            angle = i * self.constants['golden_angle']
            radius = np.sqrt(i) * fib_val / max(self.constants['fibonacci_sequence'][:8])
            
            fx = int(center_x + radius * np.cos(angle))
            fy = int(center_y + radius * np.sin(angle))
            
            if 0 <= fx < w and 0 <= fy < h:
                weights[fy, fx] = fib_val / max(self.constants['fibonacci_sequence'][:8])
        
        # Normalisation
        weights = weights / np.max(weights)
        
        return weights
    
    def _preserve_essential_frequencies(self, fft_spectrum: np.ndarray, 
                                      weights: np.ndarray, 
                                      fundamentals: List[Tuple[float, float]]) -> np.ndarray:
        """Préserver les fréquences essentielles"""
        
        preserved = fft_spectrum.copy()
        h, w = fft_spectrum.shape
        
        # Renforcer les fréquences fondamentales
        center_y, center_x = h // 2, w // 2
        
        for freq, amplitude in fundamentals:
            # Calculer la position dans le spectre
            radius = int(freq * min(h, w) // 2)
            if radius > 0:
                y, x = np.ogrid[:h, :w]
                mask = ((x - center_x)**2 + (y - center_y)**2 <= radius**2)
                preserved[mask] *= (1.0 + amplitude * 0.5)
        
        return preserved
    
    def _adaptive_harmonic_compression(self, frame: np.ndarray, 
                                     preserved_spectrum: np.ndarray,
                                     constants: Dict[str, float]) -> np.ndarray:
        """Compression adaptative selon harmoniques"""
        
        # Reconstruction partielle pour guidage
        fft_ishifted = np.fft.ifftshift(preserved_spectrum)
        partial_reconstruction = np.real(np.fft.ifft2(fft_ishifted))
        
        # Normalisation
        if np.max(partial_reconstruction) > 0:
            partial_reconstruction = (partial_reconstruction / np.max(partial_reconstruction) * 255).astype(np.uint8)
        
        # Adapter la compression selon les constantes harmoniques
        if len(frame.shape) == 3:
            h, w, c = frame.shape
            compressed = np.zeros_like(frame)
            for ch in range(c):
                compressed[:, :, ch] = self._compress_channel(
                    frame[:, :, ch], 
                    partial_reconstruction,
                    constants
                )
        else:
            compressed = self._compress_channel(frame, partial_reconstruction, constants)
        
        return compressed
    
    def _compress_channel(self, channel: np.ndarray, 
                        guidance: np.ndarray, 
                        constants: Dict[str, float]) -> np.ndarray:
        """Compresser un canal avec guidage harmonique"""
        
        # Fusionner avec le guidage
        alpha = 0.7  # Poids du guidage
        fused = alpha * channel + (1 - alpha) * guidance
        
        # Compression agressive mais guidée
        # Réduction de résolution selon constante d'or
        scale_factor = 1.0 / self.constants['golden_ratio']
        
        h, w = channel.shape
        new_h, new_w = int(h * scale_factor), int(w * scale_factor)
        new_h, new_w = max(1, new_h), max(1, new_w)
        
        resized = cv2.resize(fused, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Qualité JPEG basse mais guidée
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 15]
        _, encoded = cv2.imencode('.jpg', resized, encode_param)
        decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        
        if decoded is not None and len(decoded.shape) == 3:
            decoded = cv2.cvtColor(decoded, cv2.COLOR_BGR2GRAY)
        
        # Retourner à la taille originale
        if decoded is not None:
            final = cv2.resize(decoded, (w, h), interpolation=cv2.INTER_CUBIC)
        else:
            final = cv2.resize(resized, (w, h), interpolation=cv2.INTER_CUBIC)
        
        return final.astype(np.uint8)
    
    def _calculate_compression_ratio(self, original: np.ndarray, 
                                   compressed: np.ndarray) -> float:
        """Calculer le ratio de compression"""
        
        original_size = original.nbytes
        compressed_size = compressed.nbytes
        
        if compressed_size > 0:
            return original_size / compressed_size
        else:
            return 1.0

class HarmonicReconstructor:
    """Reconstructeur guidé par harmoniques et référence"""
    
    def __init__(self):
        self.constants = HARMONIC_CONSTANTS
        self.harmonic_analyzer = HarmonicAnalyzer()
    
    def reconstruct(self, compressed_data: Dict[str, Any], 
                  reference_frame: np.ndarray,
                  reference_harmonics: Dict[str, Any],
                  harmonic_constants: Dict[str, float]) -> np.ndarray:
        """Reconstruction guidée par harmoniques et référence"""
        
        # 1. Analyse harmonique de la référence
        ref_harmonics = reference_harmonics
        
        # 2. Fusion des spectres harmoniques
        merged_spectrum = self._merge_harmonic_spectra(
            compressed_data['preserved_frequencies'],
            ref_harmonics['fft_spectrum'],
            harmonic_constants
        )
        
        # 3. Reconstruction inverse
        reconstructed_frame = self._inverse_harmonic_transform(merged_spectrum)
        
        # 4. Enhancement guidé par harmoniques
        enhanced_frame = self._harmonic_enhancement(
            reconstructed_frame,
            ref_harmonics,
            harmonic_constants
        )
        
        # 5. Fusion avec la référence
        final_frame = self._fusion_with_reference(
            enhanced_frame,
            reference_frame,
            compressed_data['harmonic_weights']
        )
        
        return final_frame
    
    def _merge_harmonic_spectra(self, compressed_spectrum: np.ndarray,
                               reference_spectrum: np.ndarray,
                               constants: Dict[str, float]) -> np.ndarray:
        """Fusionner les spectres harmoniques"""
        
        # Fusion pondérée selon les constantes harmoniques
        alpha = constants.get('golden_ratio', 1.618) / (constants.get('golden_ratio', 1.618) + 1.0)
        
        merged = alpha * reference_spectrum + (1 - alpha) * compressed_spectrum
        
        return merged
    
    def _inverse_harmonic_transform(self, spectrum: np.ndarray) -> np.ndarray:
        """Reconstruction par transformée inverse harmonique"""
        
        # 1. Décalage inverse du spectre
        fft_ishifted = np.fft.ifftshift(spectrum)
        
        # 2. Transformée inverse
        reconstructed = np.fft.ifft2(fft_ishifted)
        
        # 3. Partie réelle
        real_reconstructed = np.real(reconstructed)
        
        # 4. Normalisation
        if np.max(real_reconstructed) > 0:
            normalized = (real_reconstructed / np.max(real_reconstructed) * 255).astype(np.uint8)
        else:
            normalized = real_reconstructed.astype(np.uint8)
        
        return normalized
    
    def _harmonic_enhancement(self, frame: np.ndarray,
                            reference_harmonics: Dict[str, Any],
                            constants: Dict[str, float]) -> np.ndarray:
        """Enhancement guidé par harmoniques"""
        
        enhanced = frame.copy()
        
        # 1. Enhancement basé sur le nombre d'or
        enhanced = self._golden_ratio_enhancement(enhanced, constants['golden_ratio'])
        
        # 2. Smoothness basé sur π
        enhanced = self._pi_based_smoothing(enhanced, constants['pi'])
        
        # 3. Contrast basé sur e
        enhanced = self._e_based_contrast(enhanced, constants['e'])
        
        # 4. Detail enhancement basé sur √2
        enhanced = self._sqrt2_detail_enhancement(enhanced, constants['sqrt2'])
        
        return enhanced
    
    def _golden_ratio_enhancement(self, frame: np.ndarray, golden_ratio: float) -> np.ndarray:
        """Enhancement basé sur le nombre d'or"""
        
        # Ajustement de luminosité selon φ
        enhanced = cv2.convertScaleAbs(frame, alpha=golden_ratio/2, beta=0)
        
        # Sharpening avec kernel basé sur φ
        kernel = np.array([[-1, -1, -1],
                         [-1, golden_ratio*2, -1],
                         [-1, -1, -1]]) / golden_ratio
        
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
    
    def _pi_based_smoothing(self, frame: np.ndarray, pi: float) -> np.ndarray:
        """Smoothness basé sur π"""
        
        # Kernel gaussien avec sigma basé sur π
        kernel_size = int(pi * 2) | 1  # Impair
        sigma = pi / 3
        
        smoothed = cv2.GaussianBlur(frame, (kernel_size, kernel_size), sigma)
        
        return cv2.addWeighted(frame, 0.6, smoothed, 0.4, 0)
    
    def _e_based_contrast(self, frame: np.ndarray, e: float) -> np.ndarray:
        """Contrast basé sur e"""
        
        # Ajustement de contraste avec e
        alpha = e / 2.5  # Facteur de contraste
        beta = 128 * (1 - alpha)  # Ajustement de luminosité
        
        contrasted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        
        return cv2.addWeighted(frame, 0.5, contrasted, 0.5, 0)
    
    def _sqrt2_detail_enhancement(self, frame: np.ndarray, sqrt2: float) -> np.ndarray:
        """Enhancement de détails basé sur √2"""
        
        # Unsharp masking avec facteur √2
        blurred = cv2.GaussianBlur(frame, (0, 0), sqrt2)
        enhanced = cv2.addWeighted(frame, 1 + sqrt2/4, blurred, -sqrt2/4, 0)
        
        return enhanced
    
    def _fusion_with_reference(self, enhanced_frame: np.ndarray,
                             reference_frame: np.ndarray,
                             weights: np.ndarray) -> np.ndarray:
        """Fusion avec la frame de référence"""
        
        # Normaliser les poids
        if np.max(weights) > 0:
            normalized_weights = weights / np.max(weights)
        else:
            normalized_weights = weights
        
        # Fusion adaptative
        if len(enhanced_frame.shape) == 2 and len(reference_frame.shape) == 3:
            # Convertir en couleur si nécessaire
            enhanced_color = cv2.cvtColor(enhanced_frame, cv2.COLOR_GRAY2BGR)
        else:
            enhanced_color = enhanced_frame
        
        # Fusion pondérée
        fused = cv2.addWeighted(enhanced_color, 0.7, reference_frame, 0.3, 0)
        
        return fused

class HarmonicCompressionSystem:
    """Système complet de compression harmonique"""
    
    def __init__(self):
        self.harmonic_analyzer = HarmonicAnalyzer()
        self.reference_capturer = ReferenceCapturer()
        self.harmonic_compressor = HarmonicCompressor()
        self.harmonic_reconstructor = HarmonicReconstructor()
        self.constants = HARMONIC_CONSTANTS
    
    def compress_with_harmonics(self, video_path: str, priority: str = 'balanced') -> Dict[str, Any]:
        """Compression complète avec guidage harmonique"""
        
        start_time = time.time()
        
        # 1. Capturer référence
        print("🎵 Capture de la référence harmonique...")
        reference_data = self.reference_capturer.capture_optimal_frame(video_path)
        
        if not reference_data:
            return {'success': False, 'error': 'Impossible de capturer la référence'}
        
        # 2. Analyse harmonique de la référence
        print("🌊 Analyse harmonique de la référence...")
        reference_harmonics = self.harmonic_analyzer.analyze(reference_data['frame'])
        
        # 3. Compression vidéo guidée par harmoniques
        print("🎼 Compression guidée par harmoniques...")
        compressed_video = []
        
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Paramètres selon priorité
        if priority == 'speed':
            frame_step = max(1, frame_count // 10)  # 10 frames
        elif priority == 'quality':
            frame_step = max(1, frame_count // 5)   # 5 frames
        else:  # balanced
            frame_step = max(1, frame_count // 8)   # 8 frames
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % frame_step == 0:
                # Analyse harmonique
                frame_harmonics = self.harmonic_analyzer.analyze(frame)
                
                # Compression guidée
                compressed_frame_data = self.harmonic_compressor.compress(
                    frame,
                    frame_harmonics,
                    reference_harmonics
                )
                
                compressed_video.append(compressed_frame_data)
            
            frame_idx += 1
        
        cap.release()
        
        compression_time = time.time() - start_time
        
        # 4. Créer package harmonique
        package = {
            'success': True,
            'compressed_video': compressed_video,
            'reference_frame': reference_data['frame'],
            'reference_harmonics': reference_harmonics,
            'harmonic_constants': self.constants,
            'metadata': reference_data['metadata'],
            'compression_time': compression_time,
            'frame_count': len(compressed_video),
            'priority': priority
        }
        
        print(f"✅ Compression harmonique terminée: {len(compressed_video)} frames en {compression_time:.2f}s")
        
        return package
    
    def reconstruct_with_harmonics(self, package: Dict[str, Any]) -> np.ndarray:
        """Reconstruction guidée par harmoniques"""
        
        print("🎵 Reconstruction harmonique...")
        start_time = time.time()
        
        reconstructed_frames = []
        
        for compressed_frame_data in package['compressed_video']:
            # Reconstruction guidée par harmoniques
            reconstructed = self.harmonic_reconstructor.reconstruct(
                compressed_frame_data,
                package['reference_frame'],
                package['reference_harmonics'],
                package['harmonic_constants']
            )
            reconstructed_frames.append(reconstructed)
        
        reconstruction_time = time.time() - start_time
        
        print(f"✅ Reconstruction harmonique terminée: {len(reconstructed_frames)} frames en {reconstruction_time:.2f}s")
        
        return {
            'frames': reconstructed_frames,
            'reconstruction_time': reconstruction_time,
            'frame_count': len(reconstructed_frames)
        }

# Point d'entrée principal
if __name__ == "__main__":
    # Test du système
    system = HarmonicCompressionSystem()
    
    # Test avec une vidéo
    video_path = "test_1080p_video.mp4"
    
    if os.path.exists(video_path):
        print("🎵 Test du système de compression harmonique...")
        
        # Compression
        result = system.compress_with_harmonics(video_path, priority='balanced')
        
        if result['success']:
            print(f"✅ Compression réussie: {result['frame_count']} frames")
            print(f"⏱️ Temps: {result['compression_time']:.2f}s")
            
            # Reconstruction
            reconstruction = system.reconstruct_with_harmonics(result)
            print(f"✅ Reconstruction réussie: {reconstruction['frame_count']} frames")
            print(f"⏱️ Temps: {reconstruction['reconstruction_time']:.2f}s")
        else:
            print(f"❌ Erreur: {result['error']}")
    else:
        print(f"❌ Fichier vidéo non trouvé: {video_path}")
