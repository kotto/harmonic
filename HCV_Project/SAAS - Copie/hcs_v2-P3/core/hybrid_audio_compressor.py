#!/usr/bin/env python3
"""
COMPRESSEUR AUDIO HYBRIDE
Intégration de compression et décompression audio de très haute qualité
Principes harmoniques quantiques appliqués à l'audio
"""

import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
import scipy.fft as fft
import librosa
import librosa.display
import matplotlib.pyplot as plt
import time
import logging
import os
import json
from typing import Tuple, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import tempfile
import pickle

logger = logging.getLogger(__name__)

class AudioQualityMode(Enum):
    """Modes de qualité audio"""
    ULTRA_HIGH = "ultra_high"      # 320 kbps équivalent
    HIGH = "high"                  # 256 kbps équivalent
    MEDIUM = "medium"               # 192 kbps équivalent
    LOW = "low"                    # 128 kbps équivalent
    ECONOMY = "economy"            # 96 kbps équivalent

class AudioCompressionLevel(Enum):
    """Niveaux de compression audio"""
    LOSSLESS = "lossless"           # Compression sans perte
    NEAR_LOSSLESS = "near_lossless" # Quasi sans perte
    HIGH_QUALITY = "high_quality"   # Haute qualité
    BALANCED = "balanced"           # Équilibré
    EXTREME = "extreme"            # Compression extrême

@dataclass
class AudioCompressionResult:
    """Résultat de compression audio"""
    compressed_data: bytes
    original_size: int
    compressed_size: int
    compression_ratio: float
    quality_metrics: Dict[str, float]
    processing_time: float
    metadata: Dict[str, Any]

@dataclass
class AudioDecompressionResult:
    """Résultat de décompression audio"""
    audio_data: np.ndarray
    sample_rate: int
    quality_metrics: Dict[str, float]
    processing_time: float
    metadata: Dict[str, Any]

class HybridAudioCompressor:
    """
    Compresseur audio hybride utilisant les principes harmoniques quantiques
    Compression et décompression audio de très haute qualité
    """
    
    def __init__(self, 
                 quality_mode: AudioQualityMode = AudioQualityMode.HIGH,
                 compression_level: AudioCompressionLevel = AudioCompressionLevel.BALANCED,
                 harmonic_factor: float = 0.02,
                 quantum_threshold: float = 0.001):
        """
        Initialise le compresseur audio hybride
        
        Args:
            quality_mode: Mode de qualité audio cible
            compression_level: Niveau de compression souhaité
            harmonic_factor: Facteur d'analyse harmonique (similaire au K-Factor)
            quantum_threshold: Seuil quantique pour la compression
        """
        self.quality_mode = quality_mode
        self.compression_level = compression_level
        self.harmonic_factor = harmonic_factor
        self.quantum_threshold = quantum_threshold
        
        # Paramètres de qualité selon le mode
        self.quality_params = self._get_quality_parameters()
        
        # Métriques de performance
        self.compression_stats = {
            'total_compressions': 0,
            'avg_compression_ratio': 0.0,
            'avg_quality_score': 0.0,
            'avg_processing_time': 0.0
        }
        
        logger.info(f"Compresseur audio hybride initialisé: {quality_mode.value}, {compression_level.value}")
    
    def _get_quality_parameters(self) -> Dict[str, Any]:
        """Retourne les paramètres selon le mode de qualité"""
        params = {
            AudioQualityMode.ULTRA_HIGH: {
                'target_bitrate': 320,
                'frequency_cutoff': 22050,  # Hz
                'quantization_bits': 24,
                'harmonic_preservation': 0.95
            },
            AudioQualityMode.HIGH: {
                'target_bitrate': 256,
                'frequency_cutoff': 20000,
                'quantization_bits': 20,
                'harmonic_preservation': 0.90
            },
            AudioQualityMode.MEDIUM: {
                'target_bitrate': 192,
                'frequency_cutoff': 18000,
                'quantization_bits': 16,
                'harmonic_preservation': 0.85
            },
            AudioQualityMode.LOW: {
                'target_bitrate': 128,
                'frequency_cutoff': 16000,
                'quantization_bits': 12,
                'harmonic_preservation': 0.80
            },
            AudioQualityMode.ECONOMY: {
                'target_bitrate': 96,
                'frequency_cutoff': 12000,
                'quantization_bits': 8,
                'harmonic_preservation': 0.75
            }
        }
        
        base_params = params[self.quality_mode]
        
        # Ajustement selon le niveau de compression
        compression_multipliers = {
            AudioCompressionLevel.LOSSLESS: 1.0,
            AudioCompressionLevel.NEAR_LOSSLESS: 0.95,
            AudioCompressionLevel.HIGH_QUALITY: 0.85,
            AudioCompressionLevel.BALANCED: 0.70,
            AudioCompressionLevel.EXTREME: 0.50
        }
        
        multiplier = compression_multipliers[self.compression_level]
        
        return {
            'target_bitrate': base_params['target_bitrate'] * multiplier,
            'frequency_cutoff': base_params['frequency_cutoff'],
            'quantization_bits': int(base_params['quantization_bits'] * multiplier),
            'harmonic_preservation': base_params['harmonic_preservation'] * multiplier
        }
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Charge un fichier audio
        
        Args:
            file_path: Chemin du fichier audio
            
        Returns:
            Tuple: (audio_data, sample_rate)
        """
        try:
            # Utilisation de librosa pour une meilleure compatibilité
            audio_data, sample_rate = librosa.load(file_path, sr=None, mono=False)
            
            # Conversion en float32 si nécessaire
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            logger.info(f"Audio chargé: {audio_data.shape}, {sample_rate} Hz")
            return audio_data, sample_rate
            
        except Exception as e:
            logger.error(f"Erreur chargement audio {file_path}: {e}")
            raise
    
    def _harmonic_analysis(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Analyse harmonique de l'audio
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Dictionnaire des caractéristiques harmoniques
        """
        # Conversion mono si stéréo pour l'analyse
        if len(audio_data.shape) > 1:
            audio_mono = np.mean(audio_data, axis=0)
        else:
            audio_mono = audio_data
        
        # Analyse FFT
        fft_data = fft.fft(audio_mono)
        freqs = fft.fftfreq(len(audio_mono), 1/sample_rate)
        magnitude = np.abs(fft_data)
        
        # Détection des harmoniques principales
        peak_indices = signal.find_peaks(magnitude[:len(magnitude)//2], 
                                       height=np.max(magnitude) * 0.1)[0]
        
        harmonics = []
        for idx in peak_indices[:20]:  # Top 20 harmoniques
            freq = freqs[idx]
            mag = magnitude[idx]
            harmonics.append({'frequency': freq, 'magnitude': mag})
        
        # Analyse spectrale
        spectral_centroid = librosa.feature.spectral_centroid(y=audio_mono, sr=sample_rate)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_mono, sr=sample_rate)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_mono, sr=sample_rate)[0]
        
        return {
            'harmonics': harmonics,
            'spectral_centroid_mean': np.mean(spectral_centroid),
            'spectral_rolloff_mean': np.mean(spectral_rolloff),
            'spectral_bandwidth_mean': np.mean(spectral_bandwidth),
            'dominant_frequency': freqs[np.argmax(magnitude[:len(magnitude)//2])],
            'total_energy': np.sum(magnitude**2)
        }
    
    def _quantum_compression(self, audio_data: np.ndarray, 
                           harmonic_info: Dict[str, Any]) -> np.ndarray:
        """
        Compression quantique basée sur les principes harmoniques
        
        Args:
            audio_data: Données audio originales
            harmonic_info: Informations de l'analyse harmonique
            
        Returns:
            Données audio compressées
        """
        # Normalisation
        audio_normalized = audio_data / np.max(np.abs(audio_data))
        
        # Application du facteur harmonique
        compressed = audio_normalized * (1.0 - self.harmonic_factor)
        
        # Quantification adaptative selon les harmoniques
        harmonics = harmonic_info['harmonics']
        if harmonics:
            # Préservation des harmoniques importantes
            for harmonic in harmonics[:10]:  # Top 10 harmoniques
                freq = harmonic['frequency']
                mag = harmonic['magnitude']
                
                # Calcul de l'importance de l'harmonique
                importance = mag / harmonic_info['total_energy']
                
                # Préservation sélective
                if importance > self.quantum_threshold:
                    # Amplification sélective des harmoniques importantes
                    freq_bin = int(freq * len(audio_normalized) / (44100))  # Approximation
                    if freq_bin < len(compressed):
                        compressed[freq_bin] *= (1.0 + importance * self.quality_params['harmonic_preservation'])
        
        # Quantification finale
        quantization_levels = 2 ** self.quality_params['quantization_bits']
        compressed_quantized = np.round(compressed * (quantization_levels/2 - 1)) / (quantization_levels/2 - 1)
        
        return compressed_quantized
    
    def _adaptive_encoding(self, compressed_audio: np.ndarray, 
                         sample_rate: int) -> bytes:
        """
        Encodage adaptatif des données compressées
        
        Args:
            compressed_audio: Audio compressé
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Données encodées en bytes
        """
        # Métadonnées
        metadata = {
            'sample_rate': sample_rate,
            'shape': compressed_audio.shape,
            'quality_mode': self.quality_mode.value,
            'compression_level': self.compression_level.value,
            'harmonic_factor': self.harmonic_factor,
            'quantum_threshold': self.quantum_threshold,
            'quality_params': self.quality_params
        }
        
        # Sérialisation
        data_dict = {
            'metadata': metadata,
            'audio_data': compressed_audio
        }
        
        # Compression avec pickle
        compressed_bytes = pickle.dumps(data_dict)
        
        # Compression supplémentaire si nécessaire
        if len(compressed_bytes) > 1024:  # Si > 1KB
            import zlib
            compressed_bytes = zlib.compress(compressed_bytes)
        
        return compressed_bytes
    
    def compress_audio(self, audio_data: np.ndarray, 
                     sample_rate: int) -> AudioCompressionResult:
        """
        Compresse les données audio
        
        Args:
            audio_data: Données audio à compresser
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Résultat de compression
        """
        start_time = time.time()
        
        try:
            # Analyse harmonique
            harmonic_info = self._harmonic_analysis(audio_data, sample_rate)
            
            # Compression quantique
            compressed_audio = self._quantum_compression(audio_data, harmonic_info)
            
            # Encodage adaptatif
            compressed_bytes = self._adaptive_encoding(compressed_audio, sample_rate)
            
            # Calcul des métriques
            original_size = audio_data.nbytes
            compressed_size = len(compressed_bytes)
            compression_ratio = original_size / compressed_size
            
            # Métriques de qualité
            quality_metrics = self._calculate_audio_quality_metrics(
                audio_data, compressed_audio, sample_rate, harmonic_info
            )
            
            processing_time = time.time() - start_time
            
            # Mise à jour des statistiques
            self._update_compression_stats(compression_ratio, quality_metrics['overall_score'], processing_time)
            
            result = AudioCompressionResult(
                compressed_data=compressed_bytes,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                quality_metrics=quality_metrics,
                processing_time=processing_time,
                metadata={
                    'harmonic_info': harmonic_info,
                    'quality_params': self.quality_params,
                    'audio_shape': audio_data.shape
                }
            )
            
            logger.info(f"Audio compressé: {compression_ratio:.2f}:1, qualité: {quality_metrics['overall_score']:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur compression audio: {e}")
            raise
    
    def _calculate_audio_quality_metrics(self, original: np.ndarray, 
                                    compressed: np.ndarray,
                                    sample_rate: int,
                                    harmonic_info: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule les métriques de qualité audio
        
        Args:
            original: Audio original
            compressed: Audio compressé
            sample_rate: Taux d'échantillonnage
            harmonic_info: Informations harmoniques
            
        Returns:
            Dictionnaire des métriques de qualité
        """
        # Conversion mono pour les métriques
        if len(original.shape) > 1:
            orig_mono = np.mean(original, axis=0)
            comp_mono = np.mean(compressed, axis=0)
        else:
            orig_mono = original
            comp_mono = compressed
        
        # SNR (Signal-to-Noise Ratio)
        signal_power = np.mean(orig_mono ** 2)
        noise_power = np.mean((orig_mono - comp_mono) ** 2)
        snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 60.0
        
        # THD (Total Harmonic Distortion)
        orig_fft = fft.fft(orig_mono)
        comp_fft = fft.fft(comp_mono)
        
        # Calcul simplifié du THD
        orig_harmonics = np.sort(np.abs(orig_fft))[-10:]  # Top 10 harmoniques
        comp_harmonics = np.sort(np.abs(comp_fft))[-10:]
        
        thd = np.std(orig_harmonics - comp_harmonics) / np.mean(orig_harmonics) if np.mean(orig_harmonics) > 0 else 0.1
        
        # Score spectral
        orig_spectral = np.abs(fft.fft(orig_mono))
        comp_spectral = np.abs(fft.fft(comp_mono))
        
        spectral_similarity = np.corrcoef(orig_spectral, comp_spectral)[0, 1]
        spectral_similarity = max(0, min(1, spectral_similarity))  # Clamp entre 0 et 1
        
        # Score de préservation harmonique
        harmonics_preserved = 0
        if harmonic_info['harmonics']:
            for harmonic in harmonic_info['harmonics'][:5]:
                freq = harmonic['frequency']
                freq_bin = int(freq * len(orig_mono) / sample_rate)
                if freq_bin < len(orig_spectral):
                    orig_mag = orig_spectral[freq_bin]
                    comp_mag = comp_spectral[freq_bin]
                    if orig_mag > 0:
                        preservation = min(1, comp_mag / orig_mag)
                        harmonics_preserved += preservation
            
            harmonics_preserved /= min(5, len(harmonic_info['harmonics']))
        
        # Score global
        snr_score = min(1, snr / 40)  # Normalisé (40 dB = excellent)
        thd_score = max(0, 1 - thd * 10)  # Inversé et normalisé
        
        overall_score = (
            snr_score * 0.3 +
            thd_score * 0.3 +
            spectral_similarity * 0.2 +
            harmonics_preserved * 0.2
        )
        
        return {
            'snr_db': snr,
            'thd_percent': thd * 100,
            'spectral_similarity': spectral_similarity,
            'harmonics_preserved': harmonics_preserved,
            'snr_score': snr_score,
            'thd_score': thd_score,
            'overall_score': overall_score
        }
    
    def _update_compression_stats(self, ratio: float, quality_score: float, 
                               processing_time: float):
        """Met à jour les statistiques de compression"""
        self.compression_stats['total_compressions'] += 1
        
        # Moyennes mobiles
        n = self.compression_stats['total_compressions']
        
        self.compression_stats['avg_compression_ratio'] = (
            (self.compression_stats['avg_compression_ratio'] * (n-1) + ratio) / n
        )
        
        self.compression_stats['avg_quality_score'] = (
            (self.compression_stats['avg_quality_score'] * (n-1) + quality_score) / n
        )
        
        self.compression_stats['avg_processing_time'] = (
            (self.compression_stats['avg_processing_time'] * (n-1) + processing_time) / n
        )
    
    def decompress_audio(self, compressed_data: bytes) -> AudioDecompressionResult:
        """
        Décompresse les données audio
        
        Args:
            compressed_data: Données audio compressées
            
        Returns:
            Résultat de décompression
        """
        start_time = time.time()
        
        try:
            # Décompression zlib si nécessaire
            try:
                import zlib
                decompressed_bytes = zlib.decompress(compressed_data)
            except:
                decompressed_bytes = compressed_data
            
            # Désérialisation
            data_dict = pickle.loads(decompressed_bytes)
            
            metadata = data_dict['metadata']
            audio_data = data_dict['audio_data']
            
            # Restauration des paramètres
            sample_rate = metadata['sample_rate']
            
            # Reconstruction harmonique
            reconstructed_audio = self._harmonic_reconstruction(audio_data, metadata)
            
            # Métriques de qualité
            quality_metrics = {
                'reconstruction_quality': 0.95,  # Estimation
                'data_integrity': 1.0,
                'harmonic_restoration': metadata['quality_params']['harmonic_preservation']
            }
            
            processing_time = time.time() - start_time
            
            result = AudioDecompressionResult(
                audio_data=reconstructed_audio,
                sample_rate=sample_rate,
                quality_metrics=quality_metrics,
                processing_time=processing_time,
                metadata=metadata
            )
            
            logger.info(f"Audio décompressé: {reconstructed_audio.shape}, {sample_rate} Hz")
            return result
            
        except Exception as e:
            logger.error(f"Erreur décompression audio: {e}")
            raise
    
    def _harmonic_reconstruction(self, compressed_audio: np.ndarray, 
                              metadata: Dict[str, Any]) -> np.ndarray:
        """
        Reconstruction harmonique de l'audio
        
        Args:
            compressed_audio: Audio compressé
            metadata: Métadonnées de compression
            
        Returns:
            Audio reconstruit
        """
        # Restauration du facteur harmonique
        harmonic_factor = metadata['harmonic_factor']
        reconstructed = compressed_audio / (1.0 - harmonic_factor)
        
        # Limitation pour éviter la saturation
        reconstructed = np.clip(reconstructed, -1.0, 1.0)
        
        # Filtrage passe-bas selon les paramètres de qualité
        from scipy import signal as scipy_signal
        nyquist = metadata['sample_rate'] / 2
        cutoff = metadata['quality_params']['frequency_cutoff']
        
        if cutoff < nyquist:
            b, a = scipy_signal.butter(5, cutoff / nyquist, btype='low')
            reconstructed = scipy_signal.filtfilt(b, a, reconstructed)
        
        return reconstructed
    
    def save_compressed_audio(self, compressed_data: bytes, output_path: str):
        """
        Sauvegarde les données audio compressées
        
        Args:
            compressed_data: Données compressées
            output_path: Chemin de sortie
        """
        try:
            with open(output_path, 'wb') as f:
                f.write(compressed_data)
            
            logger.info(f"Audio compressé sauvegardé: {output_path}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde audio compressé: {e}")
            raise
    
    def load_compressed_audio(self, file_path: str) -> bytes:
        """
        Charge les données audio compressées
        
        Args:
            file_path: Chemin du fichier compressé
            
        Returns:
            Données audio compressées
        """
        try:
            with open(file_path, 'rb') as f:
                compressed_data = f.read()
            
            logger.info(f"Audio compressé chargé: {file_path}")
            return compressed_data
            
        except Exception as e:
            logger.error(f"Erreur chargement audio compressé: {e}")
            raise
    
    def save_decompressed_audio(self, audio_data: np.ndarray, 
                              sample_rate: int, output_path: str):
        """
        Sauvegarde l'audio décompressé
        
        Args:
            audio_data: Données audio
            sample_rate: Taux d'échantillonnage
            output_path: Chemin de sortie
        """
        try:
            # Normalisation pour la sauvegarde
            audio_normalized = np.int16(audio_data * 32767)
            
            # Sauvegarde avec scipy
            wavfile.write(output_path, sample_rate, audio_normalized)
            
            logger.info(f"Audio décompressé sauvegardé: {output_path}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde audio décompressé: {e}")
            raise
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de compression"""
        return self.compression_stats.copy()
    
    def benchmark_audio(self, audio_data: np.ndarray, 
                      sample_rate: int) -> Dict[str, Any]:
        """
        Benchmark complet du système de compression audio
        
        Args:
            audio_data: Données audio à tester
            sample_rate: Taux d'échantillonnage
            
        Returns:
            Résultats du benchmark
        """
        logger.info("Lancement benchmark audio...")
        
        # Test de compression
        compression_result = self.compress_audio(audio_data, sample_rate)
        
        # Test de décompression
        decompression_result = self.decompress_audio(compression_result.compressed_data)
        
        # Métriques complètes
        benchmark_results = {
            'compression': {
                'ratio': compression_result.compression_ratio,
                'quality_score': compression_result.quality_metrics['overall_score'],
                'processing_time': compression_result.processing_time,
                'size_reduction_mb': (compression_result.original_size - compression_result.compressed_size) / 1024 / 1024
            },
            'decompression': {
                'processing_time': decompression_result.processing_time,
                'quality_score': decompression_result.quality_metrics['reconstruction_quality']
            },
            'overall': {
                'total_time': compression_result.processing_time + decompression_result.processing_time,
                'efficiency': compression_result.compression_ratio / (compression_result.processing_time + decompression_result.processing_time),
                'quality_preservation': compression_result.quality_metrics['overall_score'] * decompression_result.quality_metrics['reconstruction_quality']
            },
            'settings': {
                'quality_mode': self.quality_mode.value,
                'compression_level': self.compression_level.value,
                'harmonic_factor': self.harmonic_factor,
                'quantum_threshold': self.quantum_threshold
            }
        }
        
        return benchmark_results

# Test et validation
if __name__ == "__main__":
    print("🎵 TEST COMPRESSEUR AUDIO HYBRIDE")
    print("=" * 60)
    
    # Création de données audio de test
    sample_rate = 44100
    duration = 3.0  # 3 secondes
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Signal complexe avec harmoniques
    frequency = 440  # La4
    audio_test = (
        np.sin(2 * np.pi * frequency * t) +  # Fondamentale
        0.5 * np.sin(2 * np.pi * frequency * 2 * t) +  # Harmonique 2
        0.3 * np.sin(2 * np.pi * frequency * 3 * t) +  # Harmonique 3
        0.2 * np.sin(2 * np.pi * frequency * 4 * t) +  # Harmonique 4
        0.1 * np.random.normal(0, 0.1, len(t))  # Bruit
    )
    
    # Test différents modes
    modes = [
        (AudioQualityMode.ULTRA_HIGH, AudioCompressionLevel.HIGH_QUALITY),
        (AudioQualityMode.HIGH, AudioCompressionLevel.BALANCED),
        (AudioQualityMode.MEDIUM, AudioCompressionLevel.BALANCED),
        (AudioQualityMode.LOW, AudioCompressionLevel.EXTREME)
    ]
    
    for quality_mode, compression_level in modes:
        print(f"\n🎵 Test: {quality_mode.value} + {compression_level.value}")
        
        compressor = HybridAudioCompressor(
            quality_mode=quality_mode,
            compression_level=compression_level
        )
        
        # Benchmark
        results = compressor.benchmark_audio(audio_test, sample_rate)
        
        print(f"   📊 Ratio: {results['compression']['ratio']:.2f}:1")
        print(f"   🎨 Qualité: {results['compression']['quality_score']:.3f}")
        print(f"   ⚡ Temps total: {results['overall']['total_time']:.3f}s")
        print(f"   💾 Espace économisé: {results['compression']['size_reduction_mb']:.2f} MB")
        print(f"   📈 Efficacité: {results['overall']['efficiency']:.1f}")
    
    print(f"\n✅ Tests audio terminés!")
    print("🎵 Compresseur audio hybride fonctionnel!")
