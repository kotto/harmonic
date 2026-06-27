"""
🌊 Module Principal de Compression Harmonique - Phase 1
Implémentation du cœur de la compression harmonique avec précision étendue
"""

import numpy as np
from typing import Dict, Tuple, Optional
import time
import warnings

import sys
import os
from pathlib import Path

# Ajout du chemin parent pour les imports relatifs
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from precision.extended_precision import ExtendedPrecision, KahanSummation, CompensatedSummation
from optimization.critical_optimization import CriticalOptimization, MemoryOptimizer


class HarmonicCompressor:
    """
    Compresseur harmonique avec précision étendue (Phase 1)
    """
    
    def __init__(self, precision_bits: int = 128):
        """
        Initialise le compresseur harmonique
        
        Args:
            precision_bits: Nombre de bits de précision (défaut: 128)
        """
        self.precision_manager = ExtendedPrecision(precision_bits)
        self.optimizer = CriticalOptimization(self.precision_manager)
        
        # Statistiques de compression
        self.compression_stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0.0,
            'encoding_time': 0.0,
            'decoding_time': 0.0,
            'psnr': 0.0,
            'ssim': 0.0
        }
    
    def encode(self, signal: np.ndarray) -> Dict:
        """
        Encode un signal en utilisant la compression harmonique
        
        Args:
            signal: Signal d'entrée à compresser
            
        Returns:
            Dictionnaire contenant les données compressées
        """
        start_time = time.time()
        
        # Validation du signal
        if not isinstance(signal, np.ndarray):
            raise ValueError("Le signal doit être un numpy array")
        
        if signal.size == 0:
            raise ValueError("Le signal ne peut pas être vide")
        
        # Conversion en float64 si nécessaire
        if signal.dtype != np.float64:
            signal = signal.astype(np.float64)
        
        # Optimisation mémoire pour les signaux volumineux
        if signal.size > 10000:
            signal = self._optimize_large_signal(signal)
        
        # Projection harmonique optimisée
        coefficients = self.optimizer.optimized_harmonic_projection(signal)
        
        # Calcul des coefficients haute précision
        high_precision_coeffs = self.optimizer.optimized_coefficient_computation(signal)
        
        # Compression des coefficients
        compressed_coeffs = self._compress_coefficients(coefficients, high_precision_coeffs)
        
        # Métadonnées
        metadata = {
            'original_shape': signal.shape,
            'original_dtype': str(signal.dtype),
            'precision_bits': self.precision_manager.precision,
            'compression_method': 'harmonic_phase1',
            'timestamp': time.time()
        }
        
        # Données compressées
        compressed_data = {
            'coefficients': compressed_coeffs,
            'high_precision': high_precision_coeffs,
            'metadata': metadata
        }
        
        # Mise à jour des statistiques
        self.compression_stats['original_size'] = signal.nbytes
        self.compression_stats['compressed_size'] = self._calculate_compressed_size(compressed_data)
        self.compression_stats['compression_ratio'] = (
            self.compression_stats['original_size'] / self.compression_stats['compressed_size']
        )
        self.compression_stats['encoding_time'] = time.time() - start_time
        
        return compressed_data
    
    def decode(self, compressed_data: Dict) -> np.ndarray:
        """
        Décode des données compressées harmoniques
        
        Args:
            compressed_data: Données compressées
            
        Returns:
            Signal reconstruit
        """
        start_time = time.time()
        
        # Validation des données
        if not isinstance(compressed_data, dict):
            raise ValueError("Les données compressées doivent être un dictionnaire")
        
        required_keys = ['coefficients', 'high_precision', 'metadata']
        for key in required_keys:
            if key not in compressed_data:
                raise ValueError(f"Clé manquante: {key}")
        
        # Extraction des métadonnées
        metadata = compressed_data['metadata']
        original_shape = metadata['original_shape']
        
        # Décompression des coefficients
        coefficients = self._decompress_coefficients(compressed_data['coefficients'])
        high_precision_coeffs = compressed_data['high_precision']
        
        # Reconstruction optimisée
        reconstructed = self.optimizer.optimized_reconstruction(
            high_precision_coeffs, 
            np.prod(original_shape)
        )
        
        # Reshape au format original
        reconstructed = reconstructed.reshape(original_shape)
        
        # Conversion au type original
        original_dtype = metadata['original_dtype']
        if original_dtype == 'float64':
            reconstructed = reconstructed.astype(np.float64)
        elif original_dtype == 'float32':
            reconstructed = reconstructed.astype(np.float32)
        else:
            reconstructed = reconstructed.astype(np.float64)
        
        # Mise à jour des statistiques
        self.compression_stats['decoding_time'] = time.time() - start_time
        
        return reconstructed
    
    def _optimize_large_signal(self, signal: np.ndarray) -> np.ndarray:
        """
        Optimise le traitement des signaux volumineux
        
        Args:
            signal: Signal volumineux
            
        Returns:
            Signal optimisé
        """
        return MemoryOptimizer.process_large_signal(signal, chunk_size=1024)
    
    def _compress_coefficients(self, coeffs: Dict, high_precision_coeffs: Dict) -> Dict:
        """
        Compresse les coefficients pour un stockage efficace
        
        Args:
            coeffs: Coefficients standards
            high_precision_coeffs: Coefficients haute précision
            
        Returns:
            Coefficients compressés
        """
        compressed = {}
        
        # Compression des coefficients standards (float64)
        for name, coeff in coeffs.items():
            # Quantification adaptative
            quantized = self._adaptive_quantization(coeff)
            compressed[name] = {
                'value': quantized,
                'precision': 'standard',
                'original_value': coeff
            }
        
        # Compression des coefficients haute précision
        for name, coeff in high_precision_coeffs.items():
            # Conversion en string pour préserver la précision
            compressed[f'{name}_hp'] = {
                'value': str(coeff),
                'precision': 'high',
                'original_value': coeff
            }
        
        return compressed
    
    def _decompress_coefficients(self, compressed_coeffs: Dict) -> Dict:
        """
        Décompresse les coefficients
        
        Args:
            compressed_coeffs: Coefficients compressés
            
        Returns:
            Coefficients décompressés
        """
        decompressed = {}
        
        for key, data in compressed_coeffs.items():
            if key.endswith('_hp'):
                # Coefficient haute précision
                name = key[:-3]  # Enlever '_hp'
                decompressed[name] = float(data['value'])
            else:
                # Coefficient standard
                decompressed[key] = data['value']
        
        return decompressed
    
    def _adaptive_quantization(self, value: float) -> float:
        """
        Quantification adaptative basée sur la magnitude
        
        Args:
            value: Valeur à quantifier
            
        Returns:
            Valeur quantifiée
        """
        abs_value = abs(value)
        
        # Adaptation basée sur la magnitude
        if abs_value > 1000:
            step = 0.1
        elif abs_value > 100:
            step = 0.01
        elif abs_value > 10:
            step = 0.001
        elif abs_value > 1:
            step = 0.0001
        else:
            step = 0.00001
        
        return round(value / step) * step
    
    def _calculate_compressed_size(self, compressed_data: Dict) -> int:
        """
        Calcule la taille des données compressées
        
        Args:
            compressed_data: Données compressées
            
        Returns:
            Taille en bytes
        """
        import pickle
        
        # Sérialisation pour estimer la taille
        serialized = pickle.dumps(compressed_data)
        return len(serialized)
    
    def calculate_psnr(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """
        Calcule le PSNR entre l'original et le reconstruit
        
        Args:
            original: Signal original
            reconstructed: Signal reconstruit
            
        Returns:
            Valeur PSNR en dB
        """
        if original.shape != reconstructed.shape:
            raise ValueError("Les signaux doivent avoir la même forme")
        
        # Conversion en float64 pour le calcul
        orig = original.astype(np.float64)
        recon = reconstructed.astype(np.float64)
        
        # Calcul du MSE
        mse = np.mean((orig - recon) ** 2)
        
        if mse == 0:
            return float('inf')  # PSNR infini pour reconstruction parfaite
        
        # Calcul du PSNR
        max_pixel = 255.0 if orig.max() <= 255.0 else orig.max()
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        
        self.compression_stats['psnr'] = psnr
        
        return psnr
    
    def calculate_ssim(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """
        Calcule le SSIM (simplifié)
        
        Args:
            original: Signal original
            reconstructed: Signal reconstruit
            
        Returns:
            Valeur SSIM
        """
        # SSIM simplifié (pour 1D)
        if original.shape != reconstructed.shape:
            raise ValueError("Les signaux doivent avoir la même forme")
        
        orig_mean = np.mean(original)
        recon_mean = np.mean(reconstructed)
        
        orig_var = np.var(original)
        recon_var = np.var(reconstructed)
        
        cov = np.cov(original.flatten(), reconstructed.flatten())[0, 1]
        
        # Constantes SSIM
        k1 = 0.01
        k2 = 0.03
        L = 255.0 if original.max() <= 255.0 else original.max()
        
        c1 = (k1 * L) ** 2
        c2 = (k2 * L) ** 2
        c3 = c2 / 2
        
        numerator = (2 * orig_mean * recon_mean + c1) * (2 * cov + c2)
        denominator = (orig_mean ** 2 + recon_mean ** 2 + c1) * (orig_var + recon_var + c2)
        
        ssim = numerator / denominator
        
        self.compression_stats['ssim'] = ssim
        
        return ssim
    
    def get_compression_stats(self) -> Dict:
        """
        Retourne les statistiques de compression
        
        Returns:
            Dictionnaire des statistiques
        """
        return self.compression_stats.copy()
    
    def reset_stats(self):
        """Réinitialise les statistiques"""
        self.compression_stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0.0,
            'encoding_time': 0.0,
            'decoding_time': 0.0,
            'psnr': 0.0,
            'ssim': 0.0
        }
    
    def benchmark_compression(self, test_signal: np.ndarray, iterations: int = 10) -> Dict:
        """
        Benchmark complet de la compression
        
        Args:
            test_signal: Signal de test
            iterations: Nombre d'itérations
            
        Returns:
            Statistiques de benchmark
        """
        print(f"🚀 Benchmark de compression harmonique ({iterations} itérations)")
        
        total_encoding_time = 0
        total_decoding_time = 0
        total_psnr = 0
        total_ssim = 0
        total_ratio = 0
        
        for i in range(iterations):
            # Encodage
            start_time = time.time()
            compressed = self.encode(test_signal)
            encoding_time = time.time() - start_time
            
            # Décodage
            start_time = time.time()
            reconstructed = self.decode(compressed)
            decoding_time = time.time() - start_time
            
            # Qualité
            psnr = self.calculate_psnr(test_signal, reconstructed)
            ssim = self.calculate_ssim(test_signal, reconstructed)
            
            # Accumulation
            total_encoding_time += encoding_time
            total_decoding_time += decoding_time
            total_psnr += psnr
            total_ssim += ssim
            total_ratio += self.compression_stats['compression_ratio']
            
            if i == 0:
                print(f"📊 Itération {i+1}: PSNR={psnr:.2f}dB, SSIM={ssim:.4f}, Ratio={self.compression_stats['compression_ratio']:.2f}x")
        
        # Moyennes
        avg_encoding_time = total_encoding_time / iterations
        avg_decoding_time = total_decoding_time / iterations
        avg_psnr = total_psnr / iterations
        avg_ssim = total_ssim / iterations
        avg_ratio = total_ratio / iterations
        
        stats = {
            'iterations': iterations,
            'avg_encoding_time': avg_encoding_time,
            'avg_decoding_time': avg_decoding_time,
            'avg_psnr': avg_psnr,
            'avg_ssim': avg_ssim,
            'avg_compression_ratio': avg_ratio,
            'total_time': total_encoding_time + total_decoding_time
        }
        
        print(f"📈 Résultats moyens:")
        print(f"   PSNR: {avg_psnr:.2f} dB")
        print(f"   SSIM: {avg_ssim:.4f}")
        print(f"   Ratio: {avg_ratio:.2f}x")
        print(f"   Encodage: {avg_encoding_time:.4f}s")
        print(f"   Décodage: {avg_decoding_time:.4f}s")
        
        return stats


if __name__ == "__main__":
    # Test du compresseur harmonique
    print("🌊 Test du compresseur harmonique (Phase 1)")
    
    # Initialisation
    compressor = HarmonicCompressor(precision_bits=128)
    
    # Signal de test
    np.random.seed(42)
    test_signal = np.random.randn(1000).astype(np.float64) * 100
    
    print(f"📊 Signal de test: {len(test_signal)} échantillons")
    
    # Test de compression
    compressed = compressor.encode(test_signal)
    print(f"🗜️ Compression terminée")
    
    # Test de décompression
    reconstructed = compressor.decode(compressed)
    print(f"🔄 Décompression terminée")
    
    # Calcul de la qualité
    psnr = compressor.calculate_psnr(test_signal, reconstructed)
    ssim = compressor.calculate_ssim(test_signal, reconstructed)
    
    print(f"📈 Qualité:")
    print(f"   PSNR: {psnr:.2f} dB")
    print(f"   SSIM: {ssim:.4f}")
    
    # Statistiques
    stats = compressor.get_compression_stats()
    print(f"📊 Statistiques:")
    print(f"   Ratio compression: {stats['compression_ratio']:.2f}x")
    print(f"   Temps encodage: {stats['encoding_time']:.4f}s")
    print(f"   Temps décodage: {stats['decoding_time']:.4f}s")
    
    # Benchmark
    benchmark_stats = compressor.benchmark_compression(test_signal, iterations=5)
    
    print("🎯 Compresseur harmonique opérationnel!")
