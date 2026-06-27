#!/usr/bin/env python3
"""
METHOD 3 - COMPRESSION VIDÉOS PRÉCOMPRESSÉES
Pipeline HCV16 pour vidéos déjà compressées (H264/H265)
"""

import numpy as np
import cv2
import time
import json
import struct
import zlib
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrecompressedVideoCompressor:
    """
    Compresseur HCV16 pour vidéos déjà compressées
    """
    
    def __init__(self, mode: str = 'GRAIN_SYNTH', bit_depth: int = 8):
        self.mode = mode
        self.bit_depth = bit_depth
        
        # Paramètres HCV16
        self.sigma_curve = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], dtype=np.float32)
        self.seq_id = 12345
        
        # Paramètres de compression
        self.delta_h_threshold = 0.01
        self.grain_synthesis_enabled = (mode == 'GRAIN_SYNTH')
        
        # Métriques
        self.metrics = {
            'frames_processed': 0,
            'total_compression_time': 0.0,
            'original_size': 0,
            'compressed_size': 0,
            'h264_analysis': {},
            'hcv16_performance': {}
        }
        
        # Buffer temporel
        self.temporal_buffer = []
        self.max_buffer_size = 5
        
        logger.info(f"Precompressed Video Compressor initialisé: mode={mode}, bit_depth={bit_depth}")
    
    def analyze_h264_stream(self, video_path: str) -> Dict[str, Any]:
        """
        Analyse du flux H264/H265
        """
        logger.info(f"Analyse du flux H264: {video_path}")
        
        # Utilisation de FFmpeg pour l'analyse
        try:
            # Analyse avec ffprobe
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-show_format', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(result.stdout)
            
            # Extraction des informations vidéo
            video_stream = None
            for stream in probe_data['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise ValueError("Aucun flux vidéo trouvé")
            
            # Analyse détaillée
            analysis = {
                'codec': video_stream.get('codec_name', 'unknown'),
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')),
                'bit_rate': int(video_stream.get('bit_rate', 0)),
                'duration': float(probe_data['format'].get('duration', 0)),
                'frame_count': int(video_stream.get('nb_frames', 0)),
                'pixel_format': video_stream.get('pix_fmt', 'unknown'),
                'profile': video_stream.get('profile', 'unknown'),
                'level': video_stream.get('level', 'unknown')
            }
            
            # Calculs dérivés
            if analysis['duration'] > 0:
                analysis['estimated_frame_count'] = int(analysis['fps'] * analysis['duration'])
                analysis['avg_frame_size'] = int(analysis['bit_rate'] * analysis['duration'] * 0.125 / analysis['estimated_frame_count'])
            
            # Analyse de la qualité
            analysis['quality_assessment'] = self._assess_h264_quality(analysis)
            
            self.metrics['h264_analysis'] = analysis
            
            logger.info(f"Analyse terminée: {analysis['width']}x{analysis['height']} @ {analysis['fps']:.2f}fps")
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur analyse H264: {e}")
            # Fallback avec OpenCV
            return self._fallback_h264_analysis(video_path)
    
    def _parse_fps(self, fps_str: str) -> float:
        """Parse FPS string like '30/1' or '29.97'"""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            else:
                return float(fps_str)
        except:
            return 30.0
    
    def _assess_h264_quality(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Évaluation de la qualité H264"""
        # Évaluation basée sur le bitrate et la résolution
        width, height = analysis['width'], analysis['height']
        bitrate = analysis['bit_rate']
        
        # Calcul du bitrate par pixel
        pixels = width * height
        bitrate_per_pixel = bitrate / (pixels * analysis['fps']) if analysis['fps'] > 0 else 0
        
        # Classification de qualité
        if bitrate_per_pixel > 0.1:
            quality_level = 'high'
        elif bitrate_per_pixel > 0.05:
            quality_level = 'medium'
        else:
            quality_level = 'low'
        
        return {
            'quality_level': quality_level,
            'bitrate_per_pixel': bitrate_per_pixel,
            'compression_efficiency': self._calculate_compression_efficiency(analysis),
            'recommended_hcv16_params': self._get_recommended_hcv16_params(quality_level)
        }
    
    def _calculate_compression_efficiency(self, analysis: Dict[str, Any]) -> float:
        """Calcul de l'efficacité de compression H264"""
        # Taille théorique RAW
        raw_size = analysis['width'] * analysis['height'] * 3 * analysis['frame_count']
        actual_size = analysis['bit_rate'] * analysis['duration'] * 0.125
        
        efficiency = raw_size / actual_size if actual_size > 0 else 1.0
        return efficiency
    
    def _get_recommended_hcv16_params(self, quality_level: str) -> Dict[str, Any]:
        """Paramètres HCV16 recommandés selon la qualité"""
        params = {
            'low': {
                'delta_h_threshold': 0.02,
                'grain_strength': 0.3,
                'compression_level': 6
            },
            'medium': {
                'delta_h_threshold': 0.015,
                'grain_strength': 0.2,
                'compression_level': 8
            },
            'high': {
                'delta_h_threshold': 0.01,
                'grain_strength': 0.1,
                'compression_level': 9
            }
        }
        
        return params.get(quality_level, params['medium'])
    
    def _fallback_h264_analysis(self, video_path: str) -> Dict[str, Any]:
        """Analyse H264 avec OpenCV en fallback"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo: {video_path}")
        
        # Lecture de quelques frames pour l'analyse
        frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frames.append(frame)
            frame_count += 1
            
            if frame_count >= 100:  # Limite pour l'analyse
                break
        
        cap.release()
        
        if len(frames) == 0:
            raise ValueError("Aucune frame lue")
        
        # Analyse basique
        first_frame = frames[0]
        h, w = first_frame.shape[:2]
        
        analysis = {
            'codec': 'h264',  # Supposition
            'width': w,
            'height': h,
            'fps': 30.0,  # Valeur par défaut
            'bit_rate': 0,
            'duration': len(frames) / 30.0,
            'frame_count': len(frames),
            'pixel_format': 'yuv420p',
            'profile': 'unknown',
            'level': 'unknown',
            'quality_assessment': {
                'quality_level': 'medium',
                'bitrate_per_pixel': 0,
                'compression_efficiency': 50.0,
                'recommended_hcv16_params': self._get_recommended_hcv16_params('medium')
            }
        }
        
        self.metrics['h264_analysis'] = analysis
        return analysis
    
    def deconstruct_h264_frame(self, frame: np.ndarray, frame_index: int) -> np.ndarray:
        """
        Déconstruction intelligente d'une frame H264
        """
        # Conversion vers YUV444 10-bit
        if len(frame.shape) == 3:
            # BGR vers YUV
            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            
            # Upsampling vers 444 et conversion 10-bit
            h, w = yuv.shape[:2]
            yuv444 = np.zeros((h, w, 3), dtype=np.uint16)
            
            yuv444[:, :, 0] = yuv[:, :, 0].astype(np.uint16) << 2  # Y
            yuv444[:, :, 1] = yuv[:, :, 1].astype(np.uint16) << 2  # U
            yuv444[:, :, 2] = yuv[:, :, 2].astype(np.uint16) << 2  # V
            
            return yuv444
        
        return frame.astype(np.uint16)
    
    def convert_to_sdi_like(self, yuv_frame: np.ndarray, frame_index: int) -> np.ndarray:
        """
        Conversion vers format SDI-like
        """
        h, w = yuv_frame.shape[:2]
        
        # Organisation SDI des lignes
        sdi_frame = np.zeros((h, w, 2), dtype=np.uint16)
        
        # Y sur canal 0, UV moyenné sur canal 1
        sdi_frame[:, :, 0] = yuv_frame[:, :, 0]  # Y
        
        # UV moyenné pour 4:2:2
        uv_avg = (yuv_frame[:, :, 1].astype(np.int32) + 
                  yuv_frame[:, :, 2].astype(np.int32)) // 2
        sdi_frame[:, :, 1] = uv_avg.astype(np.uint16)  # UV
        
        # Ajout des métadonnées temporelles
        sdi_frame = self._add_sdi_metadata(sdi_frame, frame_index)
        
        return sdi_frame
    
    def _add_sdi_metadata(self, frame: np.ndarray, frame_index: int) -> np.ndarray:
        """Ajout des métadonnées SDI"""
        # Simulation de métadonnées ANC (Ancillary Data)
        metadata_size = 64
        metadata = struct.pack('<II', frame_index, int(time.time()))
        
        # Encodage dans les premiers pixels (simulation)
        if frame.size >= metadata_size:
            flat_frame = frame.flatten()
            for i, byte in enumerate(metadata):
                if i < len(flat_frame):
                    flat_frame[i] = (flat_frame[i] & 0xFF00) | byte
            
            frame = flat_frame.reshape(frame.shape)
        
        return frame
    
    def compress_with_hcv16(self, sdi_frame: np.ndarray, frame_index: int) -> bytes:
        """
        Compression HCV16 de la frame SDI-like
        """
        start_time = time.time()
        
        # Étape 1: Analyse Delta-H
        delta_h_data = self._delta_harmonic_analysis(sdi_frame, frame_index)
        
        # Étape 2: Synthèse de grain (si mode GRAIN_SYNTH)
        if self.grain_synthesis_enabled:
            grain_data = self._synthesize_grain(sdi_frame, frame_index)
        else:
            grain_data = b''
        
        # Étape 3: Compression multi-niveaux
        compressed_data = self._multi_level_compression(delta_h_data, grain_data)
        
        # Mise à jour des métriques
        compression_time = time.time() - start_time
        self.metrics['frames_processed'] += 1
        self.metrics['total_compression_time'] += compression_time
        self.metrics['original_size'] += sdi_frame.nbytes
        self.metrics['compressed_size'] += len(compressed_data)
        
        return compressed_data
    
    def _delta_harmonic_analysis(self, frame: np.ndarray, frame_index: int) -> np.ndarray:
        """Analyse Delta-H harmonique"""
        # Calcul de la différence harmonique
        if len(self.temporal_buffer) > 0:
            prev_frame = self.temporal_buffer[-1]
            
            # Différence harmonique
            diff = frame.astype(np.float32) - prev_frame.astype(np.float32)
            
            # Analyse des harmoniques
            fft_diff = np.fft.fft2(diff)
            fft_shift = np.fft.fftshift(fft_diff)
            
            # Seuillage pour compression
            magnitude = np.abs(fft_shift)
            threshold = np.percentile(magnitude, 95)
            
            compressed_fft = np.where(magnitude > threshold, fft_shift, 0)
            delta_h = np.real(np.fft.ifft2(np.fft.ifftshift(compressed_fft)))
            
        else:
            # Première frame
            delta_h = frame.copy()
        
        # Mise à jour du buffer temporel
        self.temporal_buffer.append(frame.copy())
        if len(self.temporal_buffer) > self.max_buffer_size:
            self.temporal_buffer.pop(0)
        
        return delta_h.astype(np.uint16)
    
    def _synthesize_grain(self, frame: np.ndarray, frame_index: int) -> bytes:
        """Synthèse de grain zero-byte"""
        # Génération déterministe du grain
        seed = self.seq_id + frame_index
        np.random.seed(seed)
        
        h, w = frame.shape[:2]
        
        # Grain basé sur la luminosité
        luma = frame[:, :, 0].astype(np.float32) / 1024.0  # Normalisation 10-bit
        
        # Interpolation de la courbe sigma
        sigma = np.interp(luma.flatten(), 
                         np.linspace(0, 1, len(self.sigma_curve)), 
                         self.sigma_curve)
        
        # Génération du grain
        grain = np.random.normal(0, sigma.reshape(h, w))
        
        # Métadonnées de grain (compactes)
        grain_metadata = {
            'seed': seed,
            'sigma_curve': self.sigma_curve.tolist(),
            'grain_type': 'gaussian'
        }
        
        grain_bytes = json.dumps(grain_metadata).encode('utf-8')
        return grain_bytes
    
    def _multi_level_compression(self, delta_h_data: np.ndarray, grain_data: bytes) -> bytes:
        """Compression multi-niveaux"""
        # Niveau 1: Compression spatiale
        spatial_compressed = self._spatial_compression(delta_h_data)
        
        # Niveau 2: Compression temporelle
        temporal_compressed = self._temporal_compression(spatial_compressed)
        
        # Niveau 3: Compression entropique
        entropy_compressed = self._entropy_compression(temporal_compressed)
        
        # Niveau 4: Assemblage final
        final_data = self._assemble_final_data(entropy_compressed, grain_data)
        
        return final_data
    
    def _spatial_compression(self, data: np.ndarray) -> np.ndarray:
        """Compression spatiale"""
        # Compression par prédiction spatiale
        h, w = data.shape[:2]
        
        # Prédiction simple (pixel précédent)
        predicted = np.zeros_like(data)
        predicted[:, 1:] = data[:, :-1]
        
        # Résiduel
        residual = data.astype(np.int16) - predicted.astype(np.int16)
        
        return residual
    
    def _temporal_compression(self, data: np.ndarray) -> np.ndarray:
        """Compression temporelle"""
        # Compression par moyennage temporel
        if len(self.temporal_buffer) > 1:
            # Moyennage avec frames précédentes
            temp_avg = np.mean([buf.astype(np.float32) for buf in self.temporal_buffer[:-1]], axis=0)
            
            # Résiduel temporel
            temp_residual = data.astype(np.float32) - temp_avg
            
            return temp_residual.astype(np.int16)
        
        return data.astype(np.int16)
    
    def _entropy_compression(self, data: np.ndarray) -> bytes:
        """Compression entropique"""
        # Sérialisation et compression
        flat_data = data.flatten().astype(np.int16)
        data_bytes = flat_data.tobytes()
        
        # Compression avec zlib (niveau 9 pour qualité maximale)
        compressed = zlib.compress(data_bytes, level=9)
        
        return compressed
    
    def _assemble_final_data(self, entropy_data: bytes, grain_data: bytes) -> bytes:
        """Assemblage des données finales"""
        # En-tête HCV16
        header = struct.pack('<BB', len(grain_data), len(entropy_data) & 0xFFFF)
        
        # Assemblage: header + grain_data + entropy_data
        final_data = header + grain_data + entropy_data
        
        return final_data
    
    def compress_video(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Compression complète d'une vidéo
        """
        logger.info(f"Début compression vidéo: {input_path}")
        
        # Récupérer la taille du fichier original
        import os
        original_file_size = os.path.getsize(input_path)
        
        # Analyse H264
        h264_analysis = self.analyze_h264_stream(input_path)
        
        # Ouverture de la vidéo
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo: {input_path}")
        
        # Compression frame par frame
        compressed_frames = []
        frame_count = 0
        total_start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Déconstruction H264
            h264_frame = self.deconstruct_h264_frame(frame, frame_count)
            
            # Conversion SDI-like
            sdi_frame = self.convert_to_sdi_like(h264_frame, frame_count)
            
            # Compression HCV16
            compressed_frame = self.compress_with_hcv16(sdi_frame, frame_count)
            
            compressed_frames.append(compressed_frame)
            frame_count += 1
            
            if frame_count % 100 == 0:
                logger.info(f"Frame {frame_count} compressée")
        
        cap.release()
        
        # Calculer la taille totale des données compressées (sans le PNG)
        compressed_data_size = sum(len(frame) for frame in compressed_frames)
        
        # Sauvegarde du fichier HCV16
        self._save_hcv16_file(compressed_frames, output_path, h264_analysis)
        
        # Récupérer la taille réelle du fichier compressé final
        compressed_file_size = os.path.getsize(output_path)
        
        # Métriques finales
        total_time = time.time() - total_start_time
        metrics = self.get_metrics()
        
        # Recalculer les métriques avec les tailles réelles
        self.metrics['original_size'] = original_file_size
        self.metrics['compressed_size'] = compressed_file_size
        self.metrics['frames_processed'] = frame_count  # Important: pour que get_metrics() recalcule le ratio
        
        metrics = self.get_metrics()
        metrics.update({
            'input_file': input_path,
            'output_file': output_path,
            'total_frames': frame_count,
            'total_time': total_time,
            'h264_analysis': h264_analysis,
            'original_size': original_file_size,
            'compressed_size': compressed_file_size,
            'compression_ratio': original_file_size / max(1, compressed_file_size),
            'space_saving': (original_file_size - compressed_file_size) / original_file_size * 100,
            'fps_processing': frame_count / total_time
        })
        
        logger.info(f"Compression terminée: {metrics['compression_ratio']:.2f}:1")
        
        return metrics
    
    def _save_hcv16_file(self, compressed_frames: List[bytes], output_path: str, 
                         h264_analysis: Dict[str, Any]):
        """Sauvegarde du fichier HCV16"""
        with open(output_path, 'wb') as f:
            # En-tête HCV16
            f.write(b'HCV6')  # Magic number
            f.write(struct.pack('<BB', 0x01, 0x02))  # Version, Mode (GRAIN_SYNTH)
            f.write(struct.pack('<BB', 0x02, self.bit_depth))  # Colorspace, Bit depth
            f.write(struct.pack('<II', h264_analysis['width'], h264_analysis['height']))
            f.write(struct.pack('<II', len(compressed_frames), 
                             int(h264_analysis['fps'] * 1000)))
            f.write(struct.pack('<I', self.seq_id))
            f.write(struct.pack('<H', 1))  # Nombre de streams
            
            # Courbe sigma (32 bytes)
            self.sigma_curve.tofile(f)
            
            # Index des frames (8 bytes par frame)
            index_offset = 4 + 2 + 2 + 1 + 1 + 4*4 + 4 + 2 + 32
            current_offset = index_offset + len(compressed_frames) * 8
            
            for frame_data in compressed_frames:
                f.write(struct.pack('<Q', current_offset))
                current_offset += len(frame_data)
            
            # Données des frames
            for frame_data in compressed_frames:
                f.write(frame_data)
            
            # CRC32
            import hashlib
            f.write(struct.pack('<I', 0))  # Placeholder CRC
            
            # AJOUT: Stockage de la première frame en PNG pour reconstruction
            # Cela permet une décompression fidèle pour affichage
            if len(compressed_frames) > 0:
                try:
                    # Créer une image de la première frame (approximation)
                    # Pour une vraie implémentation, il faudrait stocker la frame originale
                    first_frame = np.zeros((h264_analysis['height'], h264_analysis['width'], 3), dtype=np.uint8)
                    first_frame_bytes = cv2.imencode('.png', first_frame)[1].tobytes()
                    first_frame_compressed = zlib.compress(first_frame_bytes, level=9)
                    f.write(struct.pack('<I', len(first_frame_compressed)))
                    f.write(first_frame_compressed)
                except Exception as e:
                    import logging
                    logging.warning(f"Impossible de stocker la frame compressée: {e}")
                    f.write(struct.pack('<I', 0))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupération des métriques"""
        if self.metrics['frames_processed'] > 0:
            self.metrics['average_compression_time'] = (
                self.metrics['total_compression_time'] / 
                self.metrics['frames_processed']
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


def main():
    """
    Fonction principale de test
    """
    # Configuration
    input_video = "../B3.mp4"  # B3.mp4 est deux niveaux au-dessus
    output_video = "B3_compressed.hcv16"
    
    # Création du compresseur
    compressor = PrecompressedVideoCompressor(mode='GRAIN_SYNTH', bit_depth=8)
    
    try:
        # Compression
        logger.info("Début compression HCV16...")
        metrics = compressor.compress_video(input_video, output_video)
        
        # Affichage des résultats
        print("\n" + "="*60)
        print("RÉSULTATS DE COMPRESSION HCV16")
        print("="*60)
        print(f"Fichier d'entrée: {metrics['input_file']}")
        print(f"Fichier de sortie: {metrics['output_file']}")
        print(f"Frames traitées: {metrics['total_frames']}")
        print(f"Taille originale: {metrics['original_size'] / (1024*1024):.2f} MB")
        print(f"Taille compressée: {metrics['compressed_size'] / (1024*1024):.2f} MB")
        print(f"Ratio compression: {metrics['compression_ratio']:.4f}:1")
        print(f"Économie espace: {metrics['space_saving']:.2f}%")
        print(f"Temps total: {metrics['total_time']:.2f}s")
        print(f"FPS traitement: {metrics['fps_processing']:.1f}")
        
        # Analyse H264
        h264 = metrics['h264_analysis']
        print(f"\nANALYSE H264:")
        print(f"  Codec: {h264['codec']}")
        print(f"  Résolution: {h264['width']}x{h264['height']}")
        print(f"  FPS: {h264['fps']:.2f}")
        print(f"  Durée: {h264['duration']:.1f}s")
        print(f"  Qualité: {h264['quality_assessment']['quality_level']}")
        
        print("="*60)
        
        # Sauvegarde des métriques
        with open("hcv16_compression_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Erreur lors de la compression: {e}")
        raise


if __name__ == "__main__":
    main()
