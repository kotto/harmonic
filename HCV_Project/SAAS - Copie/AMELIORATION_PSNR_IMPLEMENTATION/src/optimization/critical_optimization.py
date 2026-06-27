"""
🔬 Module d'Optimisation des Calculs Critiques - Phase 1
Optimisation des opérations critiques pour améliorer le PSNR
"""

import numpy as np
from typing import Tuple, List, Optional
import numba
from numba import jit, prange
import time
import sys
import os
from pathlib import Path

# Ajout du chemin parent pour les imports relatifs
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from precision.extended_precision import ExtendedPrecision, KahanSummation, CompensatedSummation


class CriticalOptimization:
    """
    Classe pour optimiser les calculs critiques dans la compression harmonique
    """
    
    def __init__(self, precision_manager: ExtendedPrecision):
        """
        Initialise l'optimiseur de calculs critiques
        
        Args:
            precision_manager: Gestionnaire de précision étendue
        """
        self.precision = precision_manager
        self.optimization_stats = {
            'projection_time': 0.0,
            'coefficient_time': 0.0,
            'reconstruction_time': 0.0,
            'total_time': 0.0
        }
    
    @staticmethod
    @jit(nopython=True, parallel=True)
    def optimized_dot_product_64(signal: np.ndarray, harmonic: float) -> float:
        """
        Produit scalaire optimisé en 64-bit avec Numba
        
        Args:
            signal: Signal d'entrée
            harmonic: Constante harmonique
            
        Returns:
            Produit scalaire optimisé
        """
        result = 0.0
        n = len(signal)
        
        # Parallelisation de la somme
        partial_sums = np.zeros(8)  # 8 threads
        
        for i in prange(n):
            thread_id = i % 8
            partial_sums[thread_id] += signal[i] * harmonic
        
        # Somme finale des sommes partielles
        for i in range(8):
            result += partial_sums[i]
        
        return result
    
    def optimized_dot_product_128(self, signal: np.ndarray, harmonic: float) -> np.float128:
        """
        Produit scalaire optimisé en 128-bit avec Kahan
        
        Args:
            signal: Signal d'entrée (converti en float128)
            harmonic: Constante harmonique
            
        Returns:
            Produit scalaire optimisé en float128
        """
        # Conversion en float128
        signal_128 = signal.astype(np.float128)
        harmonic_128 = np.float128(harmonic)
        
        # Utilisation de Kahan summation
        terms = [(val, harmonic_128) for val in signal_128]
        return KahanSummation.kahan_sum_128([val * harmonic_128 for val in signal_128])
    
    def optimized_harmonic_projection(self, signal: np.ndarray) -> dict:
        """
        Projection harmonique optimisée avec mesure de performance
        
        Args:
            signal: Signal d'entrée
            
        Returns:
            Coefficients harmoniques optimisés
        """
        start_time = time.time()
        
        coefficients = {}
        harmonic_constants = {
            'phi': 1.6180339887498948482,
            'pi': 3.14159265358979323846,
            'e': 2.71828182845904523536,
            'sqrt2': 1.41421356237309504880,
            'sqrt3': 1.73205080756887729353,
            'sqrt5': 2.23606797749978969641,
            'e_pi': 0.86525597943226513569
        }
        
        # Utilisation de la précision étendue pour les calculs critiques
        for name, constant in harmonic_constants.items():
            coeff = self.optimized_dot_product_128(signal, constant)
            coefficients[name] = coeff
        
        self.optimization_stats['projection_time'] = time.time() - start_time
        
        return coefficients
    
    def optimized_coefficient_computation(self, signal: np.ndarray) -> dict:
        """
        Calcul optimisé des coefficients avec intégration haute précision
        
        Args:
            signal: Signal d'entrée
            
        Returns:
            Coefficients calculés avec haute précision
        """
        start_time = time.time()
        
        # Utilisation de la précision mpmath pour l'intégration
        mp_signal = self.precision.to_mp(signal)
        coefficients = {}
        
        for name, constant in self.precision.harmonic_constants.items():
            # Intégration numérique haute précision
            coeff = self._high_precision_integration(mp_signal, constant)
            coefficients[name] = coeff
        
        self.optimization_stats['coefficient_time'] = time.time() - start_time
        
        return coefficients
    
    def _high_precision_integration(self, signal, harmonic) -> float:
        """
        Intégration numérique haute précision
        
        Args:
            signal: Signal en format mpmath
            harmonic: Constante harmonique
            
        Returns:
            Résultat de l'intégration
        """
        n = len(signal)
        result = self.precision.to_mp(0.0)
        
        # Méthode de Simpson pour l'intégration
        if n % 2 == 1:
            n -= 1  # Simpson nécessite un nombre pair de points
        
        h = self.precision.to_mp(1.0) / self.precision.to_mp(n - 1)
        
        # Simpson's rule
        result += signal[0] * harmonic
        result += signal[n-1] * harmonic
        
        for i in range(1, n-1, 2):
            result += 4 * signal[i] * harmonic
        
        for i in range(2, n-2, 2):
            result += 2 * signal[i] * harmonic
        
        result *= h / 3
        
        return float(result)
    
    def optimized_reconstruction(self, coefficients: dict, signal_length: int) -> np.ndarray:
        """
        Reconstruction optimisée avec sommation compensée
        
        Args:
            coefficients: Coefficients harmoniques
            signal_length: Longueur du signal
            
        Returns:
            Signal reconstruit optimisé
        """
        start_time = time.time()
        
        reconstructed = np.zeros(signal_length, dtype=np.float128)
        
        # Constantes harmoniques en float128
        harmonic_constants = {
            'phi': np.float128(1.6180339887498948482),
            'pi': np.float128(3.14159265358979323846),
            'e': np.float128(2.71828182845904523536),
            'sqrt2': np.float128(1.41421356237309504880),
            'sqrt3': np.float128(1.73205080756887729353),
            'sqrt5': np.float128(2.23606797749978969641),
            'e_pi': np.float128(0.86525597943226513569)
        }
        
        # Reconstruction avec sommation compensée pour chaque échantillon
        for i in range(signal_length):
            terms = []
            for name, coeff in coefficients.items():
                terms.append((coeff, harmonic_constants[name]))
            
            reconstructed[i] = CompensatedSummation.compensated_sum_128(terms)
        
        self.optimization_stats['reconstruction_time'] = time.time() - start_time
        
        return reconstructed
    
    @staticmethod
    @jit(nopython=True)
    def vectorized_operations(signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Opérations vectorisées optimisées
        
        Args:
            signal: Signal d'entrée
            
        Returns:
            Tuple (signal_normalized, signal_enhanced)
        """
        # Normalisation vectorisée
        signal_mean = np.mean(signal)
        signal_std = np.std(signal)
        signal_normalized = (signal - signal_mean) / (signal_std + 1e-8)
        
        # Enhancement vectorisé
        signal_enhanced = signal_normalized * (1 + 0.1 * np.sin(signal_normalized))
        
        return signal_normalized, signal_enhanced
    
    def benchmark_optimization(self, signal: np.ndarray, iterations: int = 100) -> dict:
        """
        Benchmark des optimisations
        
        Args:
            signal: Signal de test
            iterations: Nombre d'itérations
            
        Returns:
            Statistiques de performance
        """
        print(f"🚀 Benchmark des optimisations ({iterations} itérations)")
        
        # Test sans optimisation
        start_time = time.time()
        for _ in range(iterations):
            # Projection standard
            coeff_standard = {}
            for name, constant in [1.618, 3.141, 2.718, 1.414, 1.732, 2.236, 0.865]:
                coeff_standard[f'test_{name}'] = np.dot(signal, constant)
        
        standard_time = time.time() - start_time
        
        # Test avec optimisation
        start_time = time.time()
        for _ in range(iterations):
            coeff_optimized = self.optimized_harmonic_projection(signal)
        
        optimized_time = time.time() - start_time
        
        speedup = standard_time / optimized_time if optimized_time > 0 else float('inf')
        
        stats = {
            'standard_time': standard_time,
            'optimized_time': optimized_time,
            'speedup': speedup,
            'iterations_per_second': iterations / optimized_time,
            'projection_time': self.optimization_stats['projection_time'],
            'coefficient_time': self.optimization_stats['coefficient_time'],
            'reconstruction_time': self.optimization_stats['reconstruction_time']
        }
        
        print(f"⚡ Accélération: {speedup:.2f}x")
        print(f"📊 Itérations/seconde: {stats['iterations_per_second']:.2f}")
        
        return stats


class MemoryOptimizer:
    """
    Optimisation de l'utilisation mémoire
    """
    
    @staticmethod
    def memory_efficient_processing(signal: np.ndarray, chunk_size: int = 1024) -> List[np.ndarray]:
        """
        Traitement efficace en mémoire par chunks
        
        Args:
            signal: Signal d'entrée
            chunk_size: Taille des chunks
            
        Returns:
            Liste des chunks traités
        """
        chunks = []
        n = len(signal)
        
        for i in range(0, n, chunk_size):
            chunk = signal[i:i + chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    @staticmethod
    def process_large_signal(signal: np.ndarray, chunk_size: int = 1024) -> np.ndarray:
        """
        Traite un signal volumineux par chunks
        
        Args:
            signal: Signal volumineux
            chunk_size: Taille des chunks
            
        Returns:
            Signal traité
        """
        chunks = MemoryOptimizer.memory_efficient_processing(signal, chunk_size)
        processed_chunks = []
        
        for chunk in chunks:
            # Traitement du chunk
            processed_chunk = chunk * 1.1  # Exemple de traitement
            processed_chunks.append(processed_chunk)
        
        # Concaténation des chunks
        return np.concatenate(processed_chunks)


if __name__ == "__main__":
    # Test du module d'optimisation
    print("🔬 Test du module d'optimisation des calculs critiques")
    
    # Initialisation
    precision_manager = ExtendedPrecision(128)
    optimizer = CriticalOptimization(precision_manager)
    
    # Signal de test
    test_signal = np.random.randn(1000).astype(np.float64)
    
    # Test d'optimisation
    coefficients = optimizer.optimized_harmonic_projection(test_signal)
    print(f"📊 Coefficients optimisés: {list(coefficients.keys())}")
    
    # Test de reconstruction
    reconstructed = optimizer.optimized_reconstruction(coefficients, len(test_signal))
    print(f"🔄 Signal reconstruit: {len(reconstructed)} échantillons")
    
    # Benchmark
    stats = optimizer.benchmark_optimization(test_signal, iterations=50)
    print(f"📈 Stats: {stats}")
    
    # Test d'optimisation mémoire
    large_signal = np.random.randn(10000)
    processed = MemoryOptimizer.process_large_signal(large_signal)
    print(f"🧠 Signal volumineux traité: {len(processed)} échantillons")
    
    print("🎯 Module d'optimisation des calculs critiques opérationnel!")
