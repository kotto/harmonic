#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCS V2 - Performance Optimizer
Optimisation CPU maximale pour l'Ordinateur Harmonique
"""

import os
import sys
import time
import numpy as np
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import queue
import psutil
from functools import lru_cache
import numba as nb

class HarmonicPerformanceOptimizer:
    """Optimiseur de performance pour l'Ordinateur Harmonique"""
    
    def __init__(self):
        self.phi_constant = 2.618
        self.cpu_count = mp.cpu_count()
        self.memory_info = psutil.virtual_memory()
        self.cache_size = 1024
        self.block_size = (32, 32)
        self.thread_pool = None
        self.process_pool = None
        
        # Optimisations
        self.enable_numba = True
        self.enable_multiprocessing = True
        self.enable_caching = True
        self.enable_vectorization = True
        
        print(f"🌊 Optimiseur HCS initialisé")
        print(f"   📊 CPU Cores: {self.cpu_count}")
        print(f"   💾 Mémoire: {self.memory_info.total / (1024**3):.1f} GB")
        print(f"   🚀 Block Size: {self.block_size}")
        print(f"   🌊 Constante φ: {self.phi_constant}")
    
    def optimize_harmonic_computation(self, image, scale_factor=2.0, strength=0.7):
        """Optimisation computation harmonique"""
        height, width = image.shape[:2]
        new_height, new_width = int(height * scale_factor), int(width * scale_factor)
        
        # Sélection de la meilleure méthode
        if self.enable_numba:
            return self._numba_harmonic_upscale(image, scale_factor, strength)
        elif self.enable_multiprocessing:
            return self._multiprocess_harmonic_upscale(image, scale_factor, strength)
        else:
            return self._vectorized_harmonic_upscale(image, scale_factor, strength)
    
    @nb.jit(nopython=True, parallel=True, cache=True)
    def _numba_harmonic_transform(self, image, scale_factor, strength, phi_const):
        """Transformation harmonique optimisée avec Numba"""
        height, width = image.shape[:2]
        new_height, new_width = int(height * scale_factor), int(width * scale_factor)
        
        if len(image.shape) == 3:
            upscaled = np.zeros((new_height, new_width, 3), dtype=np.uint8)
            
            for i in nb.prange(new_height):
                for j in range(new_width):
                    # Coordonnées normalisées
                    x, y = j / new_width, i / new_height
                    
                    # Calcul harmonique optimisé
                    harmonic_value = (
                        np.sin(2 * np.pi * phi_const * x) * 
                        np.cos(2 * np.pi * phi_const * y) +
                        np.sin(4 * np.pi * phi_const * x * y) / phi_const
                    )
                    
                    # Interpolation harmonique
                    src_x = int(j / scale_factor)
                    src_y = int(i / scale_factor)
                    
                    if 0 <= src_x < width and 0 <= src_y < height:
                        enhancement = (harmonic_value + 1) * 0.5 * strength + (1 - strength)
                        
                        for c in range(3):
                            upscaled[i, j, c] = np.clip(
                                image[src_y, src_x, c] * enhancement,
                                0, 255
                            )
        else:
            upscaled = np.zeros((new_height, new_width), dtype=np.uint8)
            
            for i in nb.prange(new_height):
                for j in range(new_width):
                    x, y = j / new_width, i / new_height
                    
                    harmonic_value = (
                        np.sin(2 * np.pi * phi_const * x) * 
                        np.cos(2 * np.pi * phi_const * y) +
                        np.sin(4 * np.pi * phi_const * x * y) / phi_const
                    )
                    
                    src_x = int(j / scale_factor)
                    src_y = int(i / scale_factor)
                    
                    if 0 <= src_x < width and 0 <= src_y < height:
                        enhancement = (harmonic_value + 1) * 0.5 * strength + (1 - strength)
                        upscaled[i, j] = np.clip(
                            image[src_y, src_x] * enhancement,
                            0, 255
                        )
        
        return upscaled
    
    def _numba_harmonic_upscale(self, image, scale_factor, strength):
        """Upscaling harmonique avec Numba"""
        return self._numba_harmonic_transform(image, scale_factor, strength, self.phi_constant)
    
    def _multiprocess_harmonic_upscale(self, image, scale_factor, strength):
        """Upscaling harmonique multiprocessus"""
        height, width = image.shape[:2]
        new_height, new_width = int(height * scale_factor), int(width * scale_factor)
        
        if len(image.shape) == 3:
            upscaled = np.zeros((new_height, new_width, 3), dtype=np.uint8)
        else:
            upscaled = np.zeros((new_height, new_width), dtype=np.uint8)
        
        # Division en blocs pour traitement parallèle
        block_height = min(self.block_size[0], new_height)
        block_width = min(self.block_size[1], new_width)
        
        # Création du pool de processus
        with ProcessPoolExecutor(max_workers=self.cpu_count) as executor:
            futures = []
            
            for i in range(0, new_height, block_height):
                for j in range(0, new_width, block_width):
                    end_i = min(i + block_height, new_height)
                    end_j = min(j + block_width, new_width)
                    
                    future = executor.submit(
                        self._process_harmonic_block,
                        image, upscaled, i, j, end_i, end_j,
                        scale_factor, strength, self.phi_constant
                    )
                    futures.append(future)
            
            # Attendre fin de tous les blocs
            for future in futures:
                future.result()
        
        return upscaled
    
    @staticmethod
    def _process_harmonic_block(image, upscaled, y_start, x_start, y_end, x_end, 
                               scale_factor, strength, phi_const):
        """Traitement d'un bloc harmonique"""
        height, width = image.shape[:2]
        new_height, new_width = upscaled.shape[:2]
        
        for i in range(y_start, y_end):
            for j in range(x_start, x_end):
                # Coordonnées normalisées
                x, y = j / new_width, i / new_height
                
                # Calcul harmonique
                harmonic_value = (
                    np.sin(2 * np.pi * phi_const * x) * 
                    np.cos(2 * np.pi * phi_const * y) +
                    np.sin(4 * np.pi * phi_const * x * y) / phi_const
                )
                
                # Interpolation harmonique
                src_x = int(j / scale_factor)
                src_y = int(i / scale_factor)
                
                if 0 <= src_x < width and 0 <= src_y < height:
                    enhancement = (harmonic_value + 1) * 0.5 * strength + (1 - strength)
                    
                    if len(image.shape) == 3:
                        for c in range(3):
                            upscaled[i, j, c] = np.clip(
                                image[src_y, src_x, c] * enhancement,
                                0, 255
                            )
                    else:
                        upscaled[i, j] = np.clip(
                            image[src_y, src_x] * enhancement,
                            0, 255
                        )
    
    def _vectorized_harmonic_upscale(self, image, scale_factor, strength):
        """Upscaling harmonique vectorisé"""
        height, width = image.shape[:2]
        new_height, new_width = int(height * scale_factor), int(width * scale_factor)
        
        # Création de grilles coordonnées vectorisées
        y_coords, x_coords = np.mgrid[0:new_height, 0:new_width]
        
        # Normalisation
        x_norm = x_coords / new_width
        y_norm = y_coords / new_height
        
        # Calcul harmonique vectorisé
        harmonic_value = (
            np.sin(2 * np.pi * self.phi_constant * x_norm) * 
            np.cos(2 * np.pi * self.phi_constant * y_norm) +
            np.sin(4 * np.pi * self.phi_constant * x_norm * y_norm) / self.phi_constant
        )
        
        # Interpolation
        src_x = (x_coords / scale_factor).astype(int)
        src_y = (y_coords / scale_factor).astype(int)
        
        # Masque pour coordonnées valides
        valid_mask = (src_x >= 0) & (src_x < width) & (src_y >= 0) & (src_y < height)
        
        # Initialisation
        if len(image.shape) == 3:
            upscaled = np.zeros((new_height, new_width, 3), dtype=np.uint8)
            
            for c in range(3):
                channel = image[:, :, c]
                enhanced = channel[src_y[valid_mask], src_x[valid_mask]]
                enhancement = (harmonic_value[valid_mask] + 1) * 0.5 * strength + (1 - strength)
                upscaled[valid_mask, c] = np.clip(enhanced * enhancement, 0, 255).astype(np.uint8)
        else:
            upscaled = np.zeros((new_height, new_width), dtype=np.uint8)
            enhanced = image[src_y[valid_mask], src_x[valid_mask]]
            enhancement = (harmonic_value[valid_mask] + 1) * 0.5 * strength + (1 - strength)
            upscaled[valid_mask] = np.clip(enhanced * enhancement, 0, 255).astype(np.uint8)
        
        return upscaled
    
    @lru_cache(maxsize=1024)
    def _cached_harmonic_value(self, x, y):
        """Calcul harmonique avec cache"""
        return (
            np.sin(2 * np.pi * self.phi_constant * x) * 
            np.cos(2 * np.pi * self.phi_constant * y) +
            np.sin(4 * np.pi * self.phi_constant * x * y) / self.phi_constant
        )
    
    def benchmark_optimization_methods(self, test_image):
        """Benchmark des méthodes d'optimisation"""
        print("🚀 Benchmark Méthodes d'Optimisation")
        print("=" * 50)
        
        methods = []
        results = {}
        
        # Test 1: Méthode de base
        start_time = time.time()
        result_basic = self._vectorized_harmonic_upscale(test_image, 2.0, 0.7)
        basic_time = time.time() - start_time
        results['basic'] = {'time': basic_time, 'method': 'Vectorisé'}
        
        # Test 2: Multiprocessing
        if self.enable_multiprocessing:
            start_time = time.time()
            result_mp = self._multiprocess_harmonic_upscale(test_image, 2.0, 0.7)
            mp_time = time.time() - start_time
            results['multiprocessing'] = {'time': mp_time, 'method': 'Multiprocessus'}
        
        # Test 3: Numba
        if self.enable_numba:
            start_time = time.time()
            result_numba = self._numba_harmonic_upscale(test_image, 2.0, 0.7)
            numba_time = time.time() - start_time
            results['numba'] = {'time': numba_time, 'method': 'Numba'}
        
        # Affichage résultats
        print("\n📊 Résultats Performance:")
        baseline = results['basic']['time']
        
        for method, data in results.items():
            speedup = baseline / data['time']
            print(f"   {data['method']:15}: {data['time']:.3f}s ({speedup:.2f}x)")
        
        # Meilleure méthode
        best_method = min(results.keys(), key=lambda k: results[k]['time'])
        print(f"\n🏆 Meilleure méthode: {results[best_method]['method']}")
        
        return results
    
    def optimize_system_resources(self):
        """Optimisation des ressources système"""
        print("🔧 Optimisation Ressources Système")
        
        # Configuration CPU
        cpu_affinity = list(range(self.cpu_count))
        try:
            psutil.Process().cpu_affinity(cpu_affinity)
            print(f"   📊 CPU Affinity: {cpu_affinity}")
        except:
            print("   ⚠️ CPU Affinity non disponible")
        
        # Configuration mémoire
        memory_limit = self.memory_info.available * 0.8
        print(f"   💾 Limite mémoire: {memory_limit / (1024**3):.1f} GB")
        
        # Configuration threads
        optimal_threads = min(self.cpu_count, 8)  # Limiter pour éviter l'oversubscription
        print(f"   🧵 Threads optimaux: {optimal_threads}")
        
        return {
            'cpu_threads': optimal_threads,
            'memory_limit': memory_limit,
            'cpu_affinity': cpu_affinity
        }
    
    def profile_performance(self, test_function, *args, **kwargs):
        """Profilage de performance"""
        print("📊 Profilage Performance")
        
        # Mesures avant
        cpu_before = psutil.cpu_percent()
        memory_before = psutil.virtual_memory().percent
        
        # Exécution
        start_time = time.time()
        result = test_function(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Mesures après
        cpu_after = psutil.cpu_percent()
        memory_after = psutil.virtual_memory().percent
        
        # Calcul métriques
        cpu_usage = cpu_after - cpu_before
        memory_usage = memory_after - memory_before
        
        profile = {
            'execution_time': execution_time,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'throughput': (args[0].size if args else 0) / execution_time if execution_time > 0 else 0
        }
        
        print(f"   ⏱️ Temps: {execution_time:.3f}s")
        print(f"   📊 CPU: {cpu_usage:+.1f}%")
        print(f"   💾 Mémoire: {memory_usage:+.1f}%")
        print(f"   🚀 Débit: {profile['throughput']:.0f} pixels/s")
        
        return result, profile

def test_performance_optimization():
    """Test complet de l'optimisation"""
    print("🌊 HCS V2 - Test Performance Optimale")
    print("=" * 60)
    
    optimizer = HarmonicPerformanceOptimizer()
    
    # Image de test
    test_image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    print(f"📏 Image test: {test_image.shape}")
    
    # Optimisation système
    system_config = optimizer.optimize_system_resources()
    
    # Benchmark méthodes
    benchmark_results = optimizer.benchmark_optimization_methods(test_image)
    
    # Test profilage
    print("\n📊 Test Profilage Performance:")
    
    def test_upscale():
        return optimizer.optimize_harmonic_computation(test_image, 2.0, 0.7)
    
    result, profile = optimizer.profile_performance(test_upscale)
    
    print(f"\n🏆 Performance Optimale:")
    print(f"   📏 Dimensions: {result.shape}")
    print(f"   ⏱️ Temps: {profile['execution_time']:.3f}s")
    print(f"   🚀 Débit: {profile['throughput']:.0f} pixels/s")
    
    return optimizer, benchmark_results, profile

if __name__ == "__main__":
    test_performance_optimization()
