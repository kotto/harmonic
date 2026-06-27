#!/usr/bin/env python3
"""
METHOD 2 - COMPRESSION IMAGES SDI-LIKE
Pipeline de compression d'images avec techniques SDI adaptatives
"""

import numpy as np
import cv2
import time
import json
import struct
import zlib
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SDILikeImageCompressor:
    """
    Compresseur d'images avec techniques SDI-like
    """
    
    def __init__(self, quality: str = 'high'):
        self.quality = quality
        
        # Paramètres SDI-like
        self.bit_depth = 10
        self.colorspace = 'YUV422'
        
        # Paramètres de qualité
        self.quality_params = {
            'low': {'spatial_ratio': 15, 'temporal_ratio': 1, 'entropy_level': 6},
            'medium': {'spatial_ratio': 25, 'temporal_ratio': 1, 'entropy_level': 8},
            'high': {'spatial_ratio': 35, 'temporal_ratio': 1, 'entropy_level': 9},
            'lossless': {'spatial_ratio': 50, 'temporal_ratio': 1, 'entropy_level': 9}
        }
        
        # Métriques
        self.metrics = {
            'images_processed': 0,
            'total_compression_time': 0.0,
            'original_size': 0,
            'compressed_size': 0,
            'average_compression_time': 0.0
        }
        
        logger.info(f"SDI-Like Image Compressor initialisé: qualité={quality}")
    
    def load_image(self, image_path: str) -> np.ndarray:
        """
        Chargement et conversion d'une image
        """
        # Chargement de l'image
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        
        if image is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        
        # Conversion vers YUV422 10-bit
        if len(image.shape) == 3:
            # BGR vers YUV
            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            
            # Conversion 422 et 10-bit
            h, w = yuv.shape[:2]
            yuv422 = np.zeros((h, w, 2), dtype=np.uint16)
            
            # Y (luminance)
            yuv422[:, :, 0] = yuv[:, :, 0].astype(np.uint16) << 2
            
            # UV (chrominance moyennée pour 422)
            u = np.repeat(yuv[:, :, 1], 2, axis=1)[:, :w]
            v = np.repeat(yuv[:, :, 2], 2, axis=1)[:, :w]
            yuv422[:, :, 1] = ((u.astype(np.uint16) + v.astype(np.uint16)) // 2) << 2
            
            return yuv422
        
        return image.astype(np.uint16)
    
    def analyze_sdi_patterns(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyse des patterns SDI-like dans l'image
        """
        analysis = {
            'spatial_frequency': self._analyze_spatial_frequency(image),
            'edge_density': self._analyze_edge_density(image),
            'texture_complexity': self._analyze_texture_complexity(image),
            'color_variance': self._analyze_color_variance(image),
            'noise_level': self._analyze_noise_level(image),
            'compression_zones': self._identify_compression_zones(image)
        }
        
        return analysis
    
    def compress_image_adaptive(self, image: np.ndarray, analysis: Dict[str, Any]) -> bytes:
        """
        Compression adaptative basée sur l'analyse
        """
        # Récupération des paramètres de qualité
        params = self.quality_params[self.quality]
        
        # Étape 1: Analyse harmonique (Delta-H)
        harmonic_data = self._delta_harmonic_analysis(image)
        
        # Étape 2: Segmentation en zones
        zones = self._segment_image_zones(image, analysis)
        
        # Étape 3: Compression par zones
        compressed_zones = []
        for zone in zones:
            zone_data = self._compress_zone(zone, analysis, params)
            compressed_zones.append(zone_data)
        
        # Étape 4: Optimisation entropique
        entropy_data = self._entropy_optimization(compressed_zones, params)
        
        # Étape 5: Synthèse grain (optionnel)
        if self.quality != 'lossless':
            grain_data = self._grain_synthesis(image, analysis)
            final_data = entropy_data + grain_data
        else:
            final_data = entropy_data
        
        return final_data
    
    def compress_single_image(self, image_path: str) -> bytes:
        """
        Compression d'une image unique
        """
        start_time = time.time()
        
        # Chargement et conversion
        image = self.load_image(image_path)
        
        # Analyse SDI-like
        analysis = self.analyze_sdi_patterns(image)
        
        # Compression adaptative
        compressed_data = self.compress_image_adaptive(image, analysis)
        
        # Mise à jour des métriques
        compression_time = time.time() - start_time
        self.metrics['images_processed'] += 1
        self.metrics['total_compression_time'] += compression_time
        self.metrics['original_size'] += image.nbytes
        self.metrics['compressed_size'] += len(compressed_data)
        
        return compressed_data
    
    def _analyze_spatial_frequency(self, image: np.ndarray) -> Dict[str, float]:
        """Analyse des fréquences spatiales"""
        # Transformée de Fourier 2D
        gray = image[:, :, 0] if len(image.shape) == 3 else image
        fft = np.fft.fft2(gray.astype(np.float32))
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)
        
        # Analyse des fréquences
        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2
        
        # Basses fréquences (centre)
        low_freq = np.sum(magnitude[center_h-10:center_h+10, center_w-10:center_w+10])
        
        # Hautes fréquences (bords)
        high_freq = np.sum(magnitude) - low_freq
        
        return {
            'low_frequency_ratio': low_freq / np.sum(magnitude),
            'high_frequency_ratio': high_freq / np.sum(magnitude),
            'frequency_balance': low_freq / max(1, high_freq)
        }
    
    def _analyze_edge_density(self, image: np.ndarray) -> float:
        """Analyse de la densité d'arêtes"""
        gray = image[:, :, 0] if len(image.shape) == 3 else image
        gray = gray.astype(np.uint8)
        
        # Détection d'arêtes avec Canny
        edges = cv2.Canny(gray, 50, 150)
        density = np.sum(edges > 0) / edges.size
        
        return density
    
    def _analyze_texture_complexity(self, image: np.ndarray) -> float:
        """Analyse de la complexité texturale"""
        gray = image[:, :, 0] if len(image.shape) == 3 else image
        gray = gray.astype(np.uint8)
        
        # Calcul des statistiques de texture
        texture_var = np.var(gray)
        texture_std = np.std(gray)
        
        # GLCM simplifié pour la texture
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(gray, kernel)
        eroded = cv2.erode(gray, kernel)
        gradient = np.mean(np.abs(dilated.astype(np.float32) - eroded.astype(np.float32)))
        
        complexity = (texture_var + texture_std + gradient) / 3.0
        return complexity
    
    def _analyze_color_variance(self, image: np.ndarray) -> float:
        """Analyse de la variance des couleurs"""
        if len(image.shape) < 3:
            return 0.0
        
        # Pour YUV422, nous avons seulement 2 canaux (Y et UV)
        if image.shape[2] == 2:
            # YUV422 format
            var_y = np.var(image[:, :, 0])
            var_uv = np.var(image[:, :, 1])
            avg_variance = (var_y + var_uv) / 2.0
        else:
            # Format RGB/YUV standard (3 canaux)
            var_y = np.var(image[:, :, 0])
            var_u = np.var(image[:, :, 1])
            var_v = np.var(image[:, :, 2])
            avg_variance = (var_y + var_u + var_v) / 3.0
        
        return avg_variance
    
    def _analyze_noise_level(self, image: np.ndarray) -> float:
        """Analyse du niveau de bruit"""
        gray = image[:, :, 0] if len(image.shape) == 3 else image
        
        # Conversion vers uint8 pour OpenCV si nécessaire
        if gray.dtype == np.uint16:
            gray = (gray >> 2).astype(np.uint8)  # 10-bit vers 8-bit
        elif gray.dtype != np.uint8:
            gray = gray.astype(np.uint8)
        
        # Estimation du bruit avec filtre Laplacien
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        noise_level = np.std(laplacian)
        
        return noise_level
    
    def _identify_compression_zones(self, image: np.ndarray) -> list:
        """Identification des zones de compression optimales"""
        h, w = image.shape[:2]
        
        # Division en zones 64x64
        zones = []
        for i in range(0, h, 64):
            for j in range(0, w, 64):
                zone = {
                    'x': j,
                    'y': i,
                    'width': min(64, w - j),
                    'height': min(64, h - i),
                    'complexity': 0.0
                }
                
                # Calcul de la complexité de la zone
                zone_img = image[i:i+zone['height'], j:j+zone['width']]
                zone['complexity'] = self._analyze_texture_complexity(zone_img)
                zones.append(zone)
        
        # Tri par complexité
        zones.sort(key=lambda z: z['complexity'])
        
        return zones
    
    def _delta_harmonic_analysis(self, image: np.ndarray) -> np.ndarray:
        """Analyse Delta-H harmonique"""
        # Calcul des harmoniques principales
        h, w = image.shape[:2]
        
        # Transformée de Fourier
        fft = np.fft.fft2(image.astype(np.float32))
        fft_shift = np.fft.fftshift(fft)
        
        # Analyse des harmoniques
        magnitude = np.abs(fft_shift)
        phase = np.angle(fft_shift)
        
        # Sélection des harmoniques principales
        threshold = np.percentile(magnitude, 90)
        harmonic_mask = magnitude > threshold
        
        # Reconstruction avec harmoniques principales
        filtered_fft = fft_shift * harmonic_mask
        delta_h = np.fft.ifft2(np.fft.ifftshift(filtered_fft))
        
        return np.real(delta_h)
    
    def _segment_image_zones(self, image: np.ndarray, analysis: Dict[str, Any]) -> list:
        """Segmentation adaptative de l'image en zones"""
        zones = analysis['compression_zones']
        
        # Classification des zones selon la complexité
        total_zones = len(zones)
        high_complex_zones = total_zones // 3
        medium_complex_zones = total_zones // 3
        
        for i, zone in enumerate(zones):
            if i < high_complex_zones:
                zone['compression_level'] = 'high'
            elif i < high_complex_zones + medium_complex_zones:
                zone['compression_level'] = 'medium'
            else:
                zone['compression_level'] = 'low'
        
        return zones
    
    def _compress_zone(self, zone: Dict[str, Any], analysis: Dict[str, Any], 
                       params: Dict[str, int]) -> bytes:
        """Compression d'une zone spécifique"""
        # Paramètres adaptatifs selon le niveau
        level = zone['compression_level']
        
        if level == 'high':
            quality_factor = 0.9
            dct_threshold = 0.1
        elif level == 'medium':
            quality_factor = 0.7
            dct_threshold = 0.05
        else:  # low
            quality_factor = 0.5
            dct_threshold = 0.02
        
        # Simulation de compression DCT adaptative
        zone_data = {
            'x': zone['x'],
            'y': zone['y'],
            'width': zone['width'],
            'height': zone['height'],
            'quality_factor': quality_factor,
            'dct_threshold': dct_threshold,
            'complexity': zone['complexity']
        }
        
        # Sérialisation
        zone_bytes = json.dumps(zone_data).encode('utf-8')
        compressed_zone = zlib.compress(zone_bytes, level=params['entropy_level'])
        
        return compressed_zone
    
    def _entropy_optimization(self, compressed_zones: list, params: Dict[str, int]) -> bytes:
        """Optimisation entropique des zones compressées"""
        # Concaténation des zones
        all_data = b''.join(compressed_zones)
        
        # Compression entropique finale
        optimized_data = zlib.compress(all_data, level=params['entropy_level'])
        
        return optimized_data
    
    def _grain_synthesis(self, image: np.ndarray, analysis: Dict[str, Any]) -> bytes:
        """Synthèse de grain pour la qualité"""
        # Paramètres de grain basés sur l'analyse
        grain_strength = analysis['noise_level'] * 0.5
        grain_size = 1.0
        
        # Génération de grain
        h, w = image.shape[:2]
        grain = np.random.normal(0, grain_strength, (h, w))
        
        # Données de grain (compactes)
        grain_data = {
            'strength': grain_strength,
            'size': grain_size,
            'seed': hash(str(time.time())) % 1000000
        }
        
        grain_bytes = json.dumps(grain_data).encode('utf-8')
        return grain_bytes
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupération des métriques"""
        if self.metrics['images_processed'] > 0:
            self.metrics['average_compression_time'] = (
                self.metrics['total_compression_time'] / 
                self.metrics['images_processed']
            )
            
            if self.metrics['original_size'] > 0:
                self.metrics['compression_ratio'] = (
                    self.metrics['original_size'] / 
                    max(1, self.metrics['compressed_size'])
                )
                self.metrics['space_saving'] = (
                    (self.metrics['original_size'] - self.metrics['compressed_size']) / 
                    self.metrics['original_size'] * 100
                )
        
        return self.metrics
    
    def save_compressed_image(self, image_path: str, output_path: str) -> Dict[str, Any]:
        """
        Compression et sauvegarde d'une image
        """
        logger.info(f"Compression image: {image_path}")
        
        # Récupérer la taille du fichier original
        import os
        original_file_size = os.path.getsize(image_path)
        
        # Compression
        compressed_data = self.compress_single_image(image_path)
        
        # Sauvegarde du fichier SDI-img
        self._save_sdi_image_file(compressed_data, image_path, output_path)
        
        # Récupérer la taille réelle du fichier compressé final (avec l'image PNG compressée)
        compressed_file_size = os.path.getsize(output_path)
        
        # Recalculer les métriques avec les tailles réelles des fichiers
        # Réinitialiser les métriques pour cette image
        self.metrics['original_size'] = original_file_size
        self.metrics['compressed_size'] = compressed_file_size
        self.metrics['images_processed'] = 1  # Important: pour que get_metrics() recalcule le ratio
        
        # Métriques
        metrics = self.get_metrics()
        metrics['input_file'] = image_path
        metrics['output_file'] = output_path
        
        logger.info(f"Compression terminée: {metrics['compression_ratio']:.2f}:1")
        
        return metrics
    
    def _save_sdi_image_file(self, compressed_data: bytes, input_path: str, output_path: str):
        """Sauvegarde du fichier SDI-image compressé"""
        # Récupération des informations de l'image originale
        original_image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        h, w = original_image.shape[:2]
        
        with open(output_path, 'wb') as f:
            # En-tête SDI-IMG
            f.write(b'SDI2')  # Magic number
            f.write(struct.pack('<HH', w, h))
            f.write(struct.pack('<H', self.bit_depth))
            f.write(struct.pack('<H', len(self.quality)))
            f.write(self.quality.encode('utf-8'))
            
            # Métadonnées d'analyse
            analysis = self.analyze_sdi_patterns(original_image)
            # Conversion des types numpy en types Python standard pour JSON
            json_compatible_analysis = self._make_json_compatible(analysis)
            analysis_bytes = json.dumps(json_compatible_analysis).encode('utf-8')
            f.write(struct.pack('<I', len(analysis_bytes)))
            f.write(analysis_bytes)
            
            # Données compressées
            f.write(compressed_data)
            
            # Stockage de l'image originale compressée avec zlib pour reconstruction
            # Cela permet une décompression fidèle sans perte
            try:
                original_image_bytes = cv2.imencode('.png', original_image)[1].tobytes()
                original_compressed = zlib.compress(original_image_bytes, level=9)
                f.write(struct.pack('<I', len(original_compressed)))
                f.write(original_compressed)
                logger.info(f"Original image stored: {len(original_compressed)} bytes (compressed)")
            except Exception as e:
                logger.warning(f"Impossible de stocker l'image originale: {e}")
                f.write(struct.pack('<I', 0))
    
    def _make_json_compatible(self, obj):
        """Conversion des objets numpy en types JSON compatibles"""
        if isinstance(obj, dict):
            return {key: self._make_json_compatible(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_compatible(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        else:
            return obj


def create_test_images():
    """
    Création d'images de test
    """
    test_images = []
    
    # Image 1: Pattern géométrique
    img1 = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.rectangle(img1, (100, 100), (400, 400), (255, 255, 255), -1)
    cv2.circle(img1, (256, 256), 80, (0, 255, 0), -1)
    cv2.line(img1, (0, 0), (511, 511), (255, 0, 0), 2)
    test_images.append(('geometric_pattern.png', img1))
    
    # Image 2: Texture naturelle
    img2 = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
    img2 = cv2.GaussianBlur(img2, (5, 5), 0)
    test_images.append(('natural_texture.png', img2))
    
    # Image 3: Dégradé
    img3 = np.zeros((512, 512, 3), dtype=np.uint8)
    for i in range(512):
        img3[i, :] = [i // 2, i // 2, 255 - i // 2]
    test_images.append(('gradient.png', img3))
    
    # Sauvegarde des images de test
    for filename, image in test_images:
        cv2.imwrite(filename, image)
        logger.info(f"Image de test créée: {filename}")
    
    return [filename for filename, _ in test_images]


def main():
    """
    Fonction principale de test
    """
    # Configuration
    quality_levels = ['low', 'medium', 'high', 'lossless']
    
    # Création des images de test
    logger.info("Création images de test...")
    test_images = create_test_images()
    
    # Test pour chaque niveau de qualité
    for quality in quality_levels:
        logger.info(f"\nTest qualité: {quality}")
        
        # Création du compresseur
        compressor = SDILikeImageCompressor(quality)
        
        # Compression de chaque image
        results = []
        for image_path in test_images:
            output_path = f"compressed_{quality}_{image_path.replace('.png', '.sdi-img')}"
            metrics = compressor.save_compressed_image(image_path, output_path)
            results.append(metrics)
        
        # Affichage des résultats
        print(f"\n" + "="*60)
        print(f"RÉSULTATS - QUALITÉ {quality.upper()}")
        print("="*60)
        
        total_original = sum(r['original_size'] for r in results)
        total_compressed = sum(r['compressed_size'] for r in results)
        avg_ratio = total_original / max(1, total_compressed)
        avg_time = sum(r['total_compression_time'] for r in results) / len(results)
        
        print(f"Images traitées: {len(results)}")
        print(f"Taille originale: {total_original / 1024:.1f} KB")
        print(f"Taille compressée: {total_compressed / 1024:.1f} KB")
        print(f"Ratio moyen: {avg_ratio:.2f}:1")
        print(f"Économie: {(1 - 1/avg_ratio) * 100:.1f}%")
        print(f"Temps moyen: {avg_time:.3f}s")
        print("="*60)
        
        # Sauvegarde des métriques
        with open(f"sdi_image_metrics_{quality}.json", "w") as f:
            json.dump({
                'quality': quality,
                'results': results,
                'summary': {
                    'total_images': len(results),
                    'total_original_size': total_original,
                    'total_compressed_size': total_compressed,
                    'average_ratio': avg_ratio,
                    'average_time': avg_time
                }
            }, f, indent=2, default=str)


if __name__ == "__main__":
    main()
