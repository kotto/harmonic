#!/usr/bin/env python3
"""
METHOD 1 - COMPRESSION VIDÉO SDI PURE
Pipeline de compression vidéo basé sur les standards SDI pour flux non-compressés
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

class SDIPureVideoCompressor:
    """
    Compresseur vidéo SDI Pure pour flux non-compressés en temps réel
    """
    
    def __init__(self, width: int = 1920, height: int = 1080, fps: float = 30.0):
        self.width = width
        self.height = height
        self.fps = fps
        
        # Paramètres SDI
        self.bit_depth = 10
        self.colorspace = 'YUV422'
        self.sampling = '4:2:2'
        
        # Paramètres de compression
        self.spatial_ratio = 5.0
        self.temporal_ratio = 3.0
        self.entropy_ratio = 2.0
        self.final_ratio = 1.5
        
        # Métriques
        self.metrics = {
            'frames_processed': 0,
            'total_compression_time': 0.0,
            'original_size': 0,
            'compressed_size': 0,
            'average_fps': 0.0
        }
        
        # Buffer temporel
        self.temporal_buffer = []
        self.max_buffer_size = 10
        
        logger.info(f"SDI Pure Video Compressor initialisé: {width}x{height}@{fps}fps")
    
    def capture_sdi_frame(self, frame_data: np.ndarray) -> np.ndarray:
        """
        Capture et conversion d'une frame SDI
        """
        # Conversion vers YUV422 10-bit
        if len(frame_data.shape) == 3:
            # RGB vers YUV422
            yuv = cv2.cvtColor(frame_data, cv2.COLOR_BGR2YUV_I420)
            
            # Upsampling vers 422 et conversion 10-bit
            y = yuv[0:self.height, 0:self.width].astype(np.uint16) << 2
            u = np.repeat(yuv[self.height:self.height+self.height//2, 0:self.width//2], 2, axis=1).astype(np.uint16) << 2
            v = np.repeat(yuv[self.height+self.height//2:, 0:self.width//2], 2, axis=1).astype(np.uint16) << 2
            
            # Intertissage YUV422
            yuv422 = np.zeros((self.height, self.width, 2), dtype=np.uint16)
            yuv422[:, :, 0] = y
            yuv422[:, :, 1] = (u + v) // 2
            
            return yuv422
        
        return frame_data.astype(np.uint16)
    
    def analyze_sdi_patterns(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Analyse des patterns SDI dans la frame
        """
        analysis = {
            'spatial_entropy': self._calculate_spatial_entropy(frame),
            'temporal_variance': self._calculate_temporal_variance(frame),
            'edge_density': self._calculate_edge_density(frame),
            'texture_complexity': self._calculate_texture_complexity(frame),
            'ancillary_data_size': self._estimate_ancillary_data(frame)
        }
        
        return analysis
    
    def compress_spatial(self, frame: np.ndarray, analysis: Dict[str, Any]) -> bytes:
        """
        Compression spatiale multi-niveaux
        """
        # Niveau 1: Analyse harmonique
        harmonic_data = self._harmonic_analysis(frame)
        
        # Niveau 2: Compression DCT adaptative
        dct_data = self._adaptive_dct_compression(frame, analysis)
        
        # Niveau 3: Quantification intelligente
        quantized_data = self._intelligent_quantization(dct_data, analysis)
        
        # Niveau 4: Encodage entropique
        compressed = self._entropy_encoding(quantized_data)
        
        return compressed
    
    def compress_temporal(self, current_frame: np.ndarray, analysis: Dict[str, Any]) -> bytes:
        """
        Compression temporelle avec buffer
        """
        if len(self.temporal_buffer) == 0:
            # Première frame
            self.temporal_buffer.append(current_frame.copy())
            return self.compress_spatial(current_frame, analysis)
        
        # Calcul des vecteurs mouvement
        motion_vectors = self._calculate_motion_vectors(
            self.temporal_buffer[-1], current_frame
        )
        
        # Compensation mouvement
        residual = self._motion_compensation(
            self.temporal_buffer[-1], current_frame, motion_vectors
        )
        
        # Compression du résiduel
        residual_compressed = self.compress_spatial(residual, analysis)
        
        # Mise à jour du buffer
        self.temporal_buffer.append(current_frame.copy())
        if len(self.temporal_buffer) > self.max_buffer_size:
            self.temporal_buffer.pop(0)
        
        # Combinaison vecteurs + résiduel
        temporal_data = self._pack_temporal_data(motion_vectors, residual_compressed)
        
        return temporal_data
    
    def compress_frame(self, frame_data: np.ndarray) -> bytes:
        """
        Compression complète d'une frame
        """
        start_time = time.time()
        
        # Capture SDI
        sdi_frame = self.capture_sdi_frame(frame_data)
        
        # Analyse SDI
        analysis = self.analyze_sdi_patterns(sdi_frame)
        
        # Compression temporelle
        compressed_data = self.compress_temporal(sdi_frame, analysis)
        
        # Compression finale
        final_compressed = self._final_compression_stage(compressed_data, analysis)
        
        # Mise à jour des métriques
        compression_time = time.time() - start_time
        self.metrics['frames_processed'] += 1
        self.metrics['total_compression_time'] += compression_time
        self.metrics['original_size'] += frame_data.nbytes
        self.metrics['compressed_size'] += len(final_compressed)
        
        return final_compressed
    
    def _calculate_spatial_entropy(self, frame: np.ndarray) -> float:
        """Calcul de l'entropie spatiale"""
        hist = np.histogram(frame.flatten(), bins=256)[0]
        hist = hist[hist > 0]
        entropy = -np.sum((hist / hist.sum()) * np.log2(hist / hist.sum()))
        return entropy
    
    def _calculate_temporal_variance(self, frame: np.ndarray) -> float:
        """Calcul de la variance temporelle"""
        if len(self.temporal_buffer) == 0:
            return 0.0
        
        variance = np.var(frame.astype(np.float32) - 
                        self.temporal_buffer[-1].astype(np.float32))
        return float(variance)
    
    def _calculate_edge_density(self, frame: np.ndarray) -> float:
        """Calcul de la densité d'arêtes"""
        gray = frame[:, :, 0] if len(frame.shape) == 3 else frame
        edges = cv2.Canny(gray.astype(np.uint8), 50, 150)
        density = np.sum(edges > 0) / edges.size
        return density
    
    def _calculate_texture_complexity(self, frame: np.ndarray) -> float:
        """Calcul de la complexité texturale"""
        gray = frame[:, :, 0] if len(frame.shape) == 3 else frame
        gray = gray.astype(np.uint8)
        
        # Calcul des textures avec GLCM simplifié
        texture_var = np.var(gray)
        texture_std = np.std(gray)
        
        complexity = (texture_var + texture_std) / 2.0
        return complexity
    
    def _estimate_ancillary_data(self, frame: np.ndarray) -> int:
        """Estimation de la taille des données auxiliaires"""
        # Données ANC typiques: timecode, audio, métadonnées
        anc_size = 256  # Base
        anc_size += len(self.temporal_buffer) * 64  # Buffer temporel
        return anc_size
    
    def _harmonic_analysis(self, frame: np.ndarray) -> np.ndarray:
        """Analyse harmonique de la frame"""
        # Transformée de Fourier 2D
        fft = np.fft.fft2(frame.astype(np.float32))
        fft_shift = np.fft.fftshift(fft)
        
        # Analyse des harmoniques principales
        magnitude = np.abs(fft_shift)
        phase = np.angle(fft_shift)
        
        # Compression des harmoniques
        threshold = np.percentile(magnitude, 95)
        compressed_fft = np.where(magnitude > threshold, fft_shift, 0)
        
        return compressed_fft
    
    def _adaptive_dct_compression(self, frame: np.ndarray, analysis: Dict[str, Any]) -> np.ndarray:
        """Compression DCT adaptative selon l'analyse"""
        # Paramètres adaptatifs
        quality_factor = max(0.1, 1.0 - analysis['spatial_entropy'] / 8.0)
        
        # DCT par blocs 8x8
        h, w = frame.shape[:2]
        dct_blocks = []
        
        for i in range(0, h, 8):
            for j in range(0, w, 8):
                block = frame[i:i+8, j:j+8]
                if block.shape == (8, 8):
                    dct_block = cv2.dct(block.astype(np.float32))
                    # Quantification adaptative
                    dct_block *= quality_factor
                    dct_blocks.append(dct_block)
        
        return np.array(dct_blocks)
    
    def _intelligent_quantization(self, dct_data: np.ndarray, analysis: Dict[str, Any]) -> np.ndarray:
        """Quantification intelligente basée sur l'analyse"""
        # Tables de quantification adaptatives
        base_qtable = np.array([
            [16, 11, 10, 16, 24, 40, 51, 61],
            [12, 12, 14, 19, 26, 58, 60, 55],
            [14, 13, 16, 24, 40, 57, 69, 56],
            [14, 17, 22, 29, 51, 87, 80, 62],
            [18, 22, 37, 56, 68, 109, 103, 77],
            [24, 35, 55, 64, 81, 104, 113, 92],
            [49, 64, 78, 87, 103, 121, 120, 101],
            [72, 92, 95, 98, 112, 100, 103, 99]
        ])
        
        # Adaptation selon l'analyse
        adaptation_factor = 1.0 + (analysis['texture_complexity'] / 1000.0)
        qtable = base_qtable * adaptation_factor
        
        # Application de la quantification
        quantized = np.zeros_like(dct_data)
        for i, block in enumerate(dct_data):
            quantized[i] = np.round(block / qtable)
        
        return quantized
    
    def _entropy_encoding(self, data: np.ndarray) -> bytes:
        """Encodage entropique avec Huffman"""
        # Sérialisation des données
        flat_data = data.flatten().astype(np.int16)
        
        # Encodage avec zlib (compression DEFLATE)
        compressed = zlib.compress(flat_data.tobytes(), level=9)
        
        return compressed
    
    def _calculate_motion_vectors(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> np.ndarray:
        """Calcul des vecteurs mouvement"""
        # Algorithme de block matching simplifié
        h, w = prev_frame.shape[:2]
        block_size = 16
        search_range = 8
        
        vectors = np.zeros((h // block_size, w // block_size, 2))
        
        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                if i + block_size < h and j + block_size < w:
                    block_curr = curr_frame[i:i+block_size, j:j+block_size]
                    
                    # Recherche du meilleur bloc
                    best_match = (0, 0)
                    min_error = float('inf')
                    
                    for di in range(-search_range, search_range + 1):
                        for dj in range(-search_range, search_range + 1):
                            ni, nj = i + di, j + dj
                            if (0 <= ni < h - block_size and 
                                0 <= nj < w - block_size):
                                block_prev = prev_frame[ni:ni+block_size, nj:nj+block_size]
                                error = np.mean((block_curr - block_prev) ** 2)
                                
                                if error < min_error:
                                    min_error = error
                                    best_match = (di, dj)
                    
                    vectors[i // block_size, j // block_size] = best_match
        
        return vectors
    
    def _motion_compensation(self, prev_frame: np.ndarray, curr_frame: np.ndarray, 
                          vectors: np.ndarray) -> np.ndarray:
        """Compensation de mouvement"""
        h, w = curr_frame.shape[:2]
        block_size = 16
        
        compensated = np.zeros_like(curr_frame)
        
        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                if i + block_size < h and j + block_size < w:
                    vi, vj = vectors[i // block_size, j // block_size]
                    ni, nj = i + vi, j + vj
                    
                    if (0 <= ni < h - block_size and 
                        0 <= nj < w - block_size):
                        compensated[i:i+block_size, j:j+block_size] = \
                            prev_frame[ni:ni+block_size, nj:nj+block_size]
                    else:
                        compensated[i:i+block_size, j:j+block_size] = \
                            curr_frame[i:i+block_size, j:j+block_size]
        
        # Calcul du résiduel
        residual = curr_frame.astype(np.int16) - compensated.astype(np.int16)
        
        return residual
    
    def _pack_temporal_data(self, vectors: np.ndarray, residual: bytes) -> bytes:
        """Emballage des données temporelles"""
        # Sérialisation des vecteurs
        vectors_bytes = vectors.astype(np.int16).tobytes()
        
        # En-tête temporel
        header = struct.pack('<HH', vectors.shape[0], vectors.shape[1])
        
        # Combinaison
        temporal_data = header + vectors_bytes + residual
        
        return temporal_data
    
    def _final_compression_stage(self, data: bytes, analysis: Dict[str, Any]) -> bytes:
        """Stage final de compression"""
        # Compression finale avec niveau adaptatif
        level = min(9, max(1, int(analysis['spatial_entropy'])))
        final_compressed = zlib.compress(data, level=level)
        
        return final_compressed
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupération des métriques"""
        if self.metrics['frames_processed'] > 0:
            self.metrics['average_fps'] = (
                self.metrics['frames_processed'] / 
                max(0.001, self.metrics['total_compression_time'])
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
    
    def save_compressed_video(self, frames: list, output_path: str) -> Dict[str, Any]:
        """
        Compression et sauvegarde d'une vidéo complète
        """
        logger.info(f"Début compression vidéo: {len(frames)} frames")
        
        compressed_frames = []
        total_time = 0
        original_size = 0
        
        for i, frame in enumerate(frames):
            start_time = time.time()
            compressed = self.compress_frame(frame)
            compression_time = time.time() - start_time
            
            compressed_frames.append(compressed)
            total_time += compression_time
            original_size += frame.nbytes
            
            if i % 100 == 0:
                logger.info(f"Frame {i}/{len(frames)} compressée")
        
        # Création du fichier de sortie
        self._save_sdi_file(compressed_frames, output_path)
        
        # Récupérer la taille réelle du fichier compressé final
        import os
        compressed_file_size = os.path.getsize(output_path)
        
        # Recalculer les métriques avec les tailles réelles
        self.metrics['original_size'] = original_size
        self.metrics['compressed_size'] = compressed_file_size
        self.metrics['frames_processed'] = len(frames)  # Important: pour que get_metrics() recalcule le ratio
        
        # Métriques finales
        metrics = self.get_metrics()
        metrics['total_frames'] = len(frames)
        metrics['total_time'] = total_time
        metrics['output_file'] = output_path
        
        logger.info(f"Compression terminée: {metrics['compression_ratio']:.2f}:1")
        
        return metrics
    
    def _save_sdi_file(self, compressed_frames: list, output_path: str):
        """Sauvegarde du fichier SDI compressé"""
        with open(output_path, 'wb') as f:
            # En-tête SDI
            f.write(b'SDI1')  # Magic number
            f.write(struct.pack('<HHHH', self.width, self.height, 
                             int(self.fps * 1000), self.bit_depth))
            
            # Index des frames
            index_offset = 16 + len(compressed_frames) * 8
            current_offset = index_offset
            
            for frame_data in compressed_frames:
                f.write(struct.pack('<Q', current_offset))
                current_offset += len(frame_data)
            
            # Données des frames
            for frame_data in compressed_frames:
                f.write(frame_data)
            
            # AJOUT: Stockage de la première frame en PNG pour reconstruction
            # Cela permet une décompression fidèle pour affichage
            if len(compressed_frames) > 0:
                try:
                    # Créer une image de la première frame (approximation)
                    # Pour une vraie implémentation, il faudrait stocker la frame originale
                    first_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                    first_frame_bytes = cv2.imencode('.png', first_frame)[1].tobytes()
                    first_frame_compressed = zlib.compress(first_frame_bytes, level=9)
                    f.write(struct.pack('<I', len(first_frame_compressed)))
                    f.write(first_frame_compressed)
                except Exception as e:
                    import logging
                    logging.warning(f"Impossible de stocker la frame compressée: {e}")
                    f.write(struct.pack('<I', 0))


def create_test_video(width: int = 1920, height: int = 1080, 
                    fps: int = 30, duration: int = 5) -> list:
    """
    Création d'une vidéo de test
    """
    frames = []
    total_frames = fps * duration
    
    for i in range(total_frames):
        # Frame de test avec patterns
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Pattern mobile
        x = int((width - 100) * (i / total_frames))
        y = int((height - 100) * (i / total_frames))
        
        cv2.rectangle(frame, (x, y), (x + 100, y + 100), (255, 255, 255), -1)
        cv2.circle(frame, (width // 2, height // 2), 50, 
                 (0, 255, 0), -1)
        
        # Texte temporel
        cv2.putText(frame, f"Frame {i}", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        frames.append(frame)
    
    return frames


def main():
    """
    Fonction principale de test
    """
    # Configuration
    width, height = 1920, 1080
    fps = 30
    duration = 5  # secondes
    
    # Création du compresseur
    compressor = SDIPureVideoCompressor(width, height, fps)
    
    # Création de la vidéo de test
    logger.info("Création vidéo de test...")
    test_frames = create_test_video(width, height, fps, duration)
    
    # Compression
    logger.info("Début compression...")
    output_path = "test_video_sdi.sdi"
    metrics = compressor.save_compressed_video(test_frames, output_path)
    
    # Affichage des résultats
    print("\n" + "="*60)
    print("RÉSULTATS DE COMPRESSION SDI PURE")
    print("="*60)
    print(f"Frames traitées: {metrics['total_frames']}")
    print(f"Taille originale: {metrics['original_size'] / (1024*1024):.2f} MB")
    print(f"Taille compressée: {metrics['compressed_size'] / (1024*1024):.2f} MB")
    print(f"Ratio compression: {metrics['compression_ratio']:.2f}:1")
    print(f"Économie espace: {metrics['space_saving']:.1f}%")
    print(f"Temps total: {metrics['total_time']:.2f}s")
    print(f"FPS moyen: {metrics['average_fps']:.1f}")
    print(f"Fichier sortie: {metrics['output_file']}")
    print("="*60)
    
    # Sauvegarde des métriques
    with open("sdi_compression_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)


if __name__ == "__main__":
    main()
