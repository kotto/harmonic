#!/usr/bin/env python3
"""
OPTIMISEUR DE PARAMÈTRES HYBRIDE
Optimisation automatique des paramètres K-Factor et WebP Quality
Pour images et vidéos avec analyse de performance et qualité
"""

import numpy as np
import cv2
import time
import logging
import os
from typing import List, Tuple, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Import des composants existants
from .hybrid_compressor import HybridCompressor
from .harmonic_upscaler import HarmonicUpscalerAPI

logger = logging.getLogger(__name__)

class OptimizationTarget(Enum):
    """Objectifs d'optimisation"""
    MAX_QUALITY = "max_quality"
    MAX_COMPRESSION = "max_compression"
    BALANCED = "balanced"
    FAST_PROCESSING = "fast_processing"
    MIN_SIZE = "min_size"

class MediaType(Enum):
    """Types de médias supportés"""
    IMAGE = "image"
    VIDEO = "video"

@dataclass
class ParameterSet:
    """Ensemble de paramètres à tester"""
    k_factor: float
    webp_quality: int
    description: str

@dataclass
class OptimizationResult:
    """Résultat d'optimisation"""
    best_parameters: ParameterSet
    performance_metrics: Dict[str, float]
    quality_metrics: Dict[str, float]
    optimization_score: float
    target_achieved: bool
    all_results: List[Dict[str, Any]]

class HybridParameterOptimizer:
    """
    Optimiseur automatique des paramètres hybrides
    Recherche les meilleurs K-Factor et WebP Quality selon les objectifs
    """
    
    def __init__(self, 
                 optimization_target: OptimizationTarget = OptimizationTarget.BALANCED,
                 media_type: MediaType = MediaType.IMAGE,
                 max_iterations: int = 50,
                 parallel_workers: Optional[int] = None):
        """
        Initialise l'optimiseur de paramètres
        
        Args:
            optimization_target: Objectif d'optimisation
            media_type: Type de média (image/vidéo)
            max_iterations: Nombre maximum d'itérations
            parallel_workers: Nombre de workers pour parallélisation
        """
        self.optimization_target = optimization_target
        self.media_type = media_type
        self.max_iterations = max_iterations
        self.parallel_workers = parallel_workers or min(4, mp.cpu_count())
        
        # Espaces de recherche pour les paramètres
        self.k_factor_range = (0.001, 0.1)  # K-Factor
        self.webp_quality_range = (30, 100)  # WebP Quality
        
        # Historique d'optimisation
        self.optimization_history = []
        self.best_global_result = None
        
        # Métriques de pondération selon l'objectif
        self.weights = self._get_objective_weights()
        
        logger.info(f"Optimiseur initialisé: target={optimization_target.value}, media={media_type.value}")
    
    def _get_objective_weights(self) -> Dict[str, float]:
        """Définit les poids selon l'objectif d'optimisation"""
        if self.optimization_target == OptimizationTarget.MAX_QUALITY:
            return {
                'quality_score': 0.7,
                'compression_ratio': 0.1,
                'processing_time': 0.2,
                'size_efficiency': 0.0
            }
        elif self.optimization_target == OptimizationTarget.MAX_COMPRESSION:
            return {
                'quality_score': 0.1,
                'compression_ratio': 0.7,
                'processing_time': 0.1,
                'size_efficiency': 0.1
            }
        elif self.optimization_target == OptimizationTarget.BALANCED:
            return {
                'quality_score': 0.3,
                'compression_ratio': 0.3,
                'processing_time': 0.2,
                'size_efficiency': 0.2
            }
        elif self.optimization_target == OptimizationTarget.FAST_PROCESSING:
            return {
                'quality_score': 0.2,
                'compression_ratio': 0.1,
                'processing_time': 0.6,
                'size_efficiency': 0.1
            }
        elif self.optimization_target == OptimizationTarget.MIN_SIZE:
            return {
                'quality_score': 0.1,
                'compression_ratio': 0.4,
                'processing_time': 0.1,
                'size_efficiency': 0.4
            }
        else:
            return {'quality_score': 0.25, 'compression_ratio': 0.25, 'processing_time': 0.25, 'size_efficiency': 0.25}
    
    def generate_parameter_candidates(self, method: str = "grid") -> List[ParameterSet]:
        """
        Génère des candidats de paramètres à tester
        
        Args:
            method: Méthode de génération (grid, random, adaptive)
            
        Returns:
            Liste des ensembles de paramètres
        """
        candidates = []
        
        if method == "grid":
            # Grille systématique
            k_values = np.linspace(self.k_factor_range[0], self.k_factor_range[1], 8)
            quality_values = np.linspace(self.webp_quality_range[0], self.webp_quality_range[1], 8)
            
            for k in k_values:
                for q in quality_values:
                    candidates.append(ParameterSet(
                        k_factor=k,
                        webp_quality=int(q),
                        description=f"Grid_K{k:.3f}_Q{int(q)}"
                    ))
        
        elif method == "random":
            # Échantillonnage aléatoire
            for _ in range(self.max_iterations):
                k = np.random.uniform(self.k_factor_range[0], self.k_factor_range[1])
                q = np.random.randint(self.webp_quality_range[0], self.webp_quality_range[1] + 1)
                candidates.append(ParameterSet(
                    k_factor=k,
                    webp_quality=q,
                    description=f"Random_K{k:.3f}_Q{q}"
                ))
        
        elif method == "adaptive":
            # Adaptatif basé sur l'historique
            if len(self.optimization_history) > 0:
                # Analyse des meilleurs résultats précédents
                best_results = sorted(self.optimization_history, key=lambda x: x['score'], reverse=True)[:5]
                
                # Génération autour des meilleurs paramètres
                for result in best_results:
                    k_center = result['k_factor']
                    q_center = result['webp_quality']
                    
                    # Variation autour du centre
                    for _ in range(3):
                        k = np.random.normal(k_center, k_center * 0.2)
                        k = np.clip(k, self.k_factor_range[0], self.k_factor_range[1])
                        q = np.random.normal(q_center, 10)
                        q = np.clip(q, self.webp_quality_range[0], self.webp_quality_range[1])
                        
                        candidates.append(ParameterSet(
                            k_factor=k,
                            webp_quality=int(q),
                            description=f"Adaptive_K{k:.3f}_Q{int(q)}"
                        ))
            else:
                # Fallback vers grille si pas d'historique
                return self.generate_parameter_candidates("grid")
        
        return candidates[:self.max_iterations]
    
    def evaluate_parameters(self, 
                          media_data: Union[np.ndarray, str],
                          parameters: ParameterSet) -> Dict[str, Any]:
        """
        Évalue un ensemble de paramètres sur les données média
        
        Args:
            media_data: Image (numpy array) ou vidéo (chemin fichier)
            parameters: Paramètres à tester
            
        Returns:
            Métriques d'évaluation
        """
        try:
            # Création du compresseur avec les paramètres
            compressor = HybridCompressor(
                k_factor=parameters.k_factor,
                webp_quality=parameters.webp_quality
            )
            
            if self.media_type == MediaType.IMAGE:
                return self._evaluate_image_parameters(media_data, compressor, parameters)
            else:
                return self._evaluate_video_parameters(media_data, compressor, parameters)
                
        except Exception as e:
            logger.error(f"Erreur évaluation paramètres {parameters.description}: {e}")
            return {
                'k_factor': parameters.k_factor,
                'webp_quality': parameters.webp_quality,
                'description': parameters.description,
                'error': str(e),
                'score': 0.0
            }
    
    def _evaluate_image_parameters(self, 
                                image: np.ndarray,
                                compressor: HybridCompressor,
                                parameters: ParameterSet) -> Dict[str, Any]:
        """Évalue les paramètres pour une image"""
        start_time = time.time()
        
        # Compression
        compressed_data, metadata = compressor.compress_image(image)
        
        # Simulation de décompression
        original_size = image.nbytes
        compressed_size = len(compressed_data)
        actual_ratio = original_size / compressed_size
        
        # Calcul qualité (simplifié)
        quality_score = self._calculate_image_quality(image, compressed_data, metadata)
        
        processing_time = time.time() - start_time
        
        # Efficacité taille
        size_efficiency = actual_ratio / processing_time if processing_time > 0 else 0
        
        # Score composite selon les poids
        score = (
            quality_score * self.weights['quality_score'] +
            min(actual_ratio / 100, 1.0) * self.weights['compression_ratio'] +
            max(0, 1 - processing_time / 1.0) * self.weights['processing_time'] +
            min(size_efficiency / 1000, 1.0) * self.weights['size_efficiency']
        )
        
        return {
            'k_factor': parameters.k_factor,
            'webp_quality': parameters.webp_quality,
            'description': parameters.description,
            'compression_ratio': actual_ratio,
            'quality_score': quality_score,
            'processing_time': processing_time,
            'size_efficiency': size_efficiency,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'score': score,
            'metadata': metadata
        }
    
    def _evaluate_video_parameters(self, 
                                 video_path: str,
                                 compressor: HybridCompressor,
                                 parameters: ParameterSet) -> Dict[str, Any]:
        """Évalue les paramètres pour une vidéo"""
        start_time = time.time()
        
        # Extraction de quelques frames pour l'évaluation
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Échantillonnage de frames
        sample_frames = []
        sample_indices = np.linspace(0, min(frame_count - 1, 30), 5, dtype=int)
        
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                sample_frames.append(frame)
        
        cap.release()
        
        if not sample_frames:
            raise ValueError("Impossible d'extraire des frames de la vidéo")
        
        # Évaluation sur les frames échantillonnées
        total_ratio = 0
        total_quality = 0
        frame_times = []
        
        for frame in sample_frames:
            frame_start = time.time()
            compressed_data, metadata = compressor.compress_image(frame)
            frame_time = time.time() - frame_start
            
            frame_times.append(frame_time)
            total_ratio += metadata['hybrid_ratio']
            total_quality += self._calculate_image_quality(frame, compressed_data, metadata)
        
        avg_ratio = total_ratio / len(sample_frames)
        avg_quality = total_quality / len(sample_frames)
        avg_frame_time = np.mean(frame_times)
        
        processing_time = time.time() - start_time
        
        # Estimation taille vidéo
        original_size = os.path.getsize(video_path)
        estimated_compressed_size = original_size / avg_ratio
        
        # Score composite
        score = (
            avg_quality * self.weights['quality_score'] +
            min(avg_ratio / 100, 1.0) * self.weights['compression_ratio'] +
            max(0, 1 - avg_frame_time / 0.1) * self.weights['processing_time'] +
            min(avg_ratio / processing_time, 1.0) * self.weights['size_efficiency']
        )
        
        return {
            'k_factor': parameters.k_factor,
            'webp_quality': parameters.webp_quality,
            'description': parameters.description,
            'compression_ratio': avg_ratio,
            'quality_score': avg_quality,
            'processing_time': processing_time,
            'frame_processing_time': avg_frame_time,
            'fps': fps,
            'frames_evaluated': len(sample_frames),
            'original_size': original_size,
            'estimated_compressed_size': estimated_compressed_size,
            'score': score
        }
    
    def _calculate_image_quality(self, 
                                original: np.ndarray,
                                compressed_data: bytes,
                                metadata: Dict[str, Any]) -> float:
        """
        Calcule un score de qualité (simplifié pour la démo)
        
        Args:
            original: Image originale
            compressed_data: Données compressées
            metadata: Métadonnées de compression
            
        Returns:
            Score de qualité (0-1)
        """
        try:
            # Simulation basique de qualité basée sur le ratio
            ratio = metadata.get('hybrid_ratio', 10.0)
            
            # Plus le ratio est faible, meilleure est la qualité
            if ratio < 10:
                return 0.9
            elif ratio < 25:
                return 0.8
            elif ratio < 50:
                return 0.7
            elif ratio < 100:
                return 0.6
            else:
                return 0.5
                
        except Exception:
            return 0.7  # Valeur par défaut
    
    def optimize_parameters(self, 
                          media_data: Union[np.ndarray, str],
                          method: str = "adaptive") -> OptimizationResult:
        """
        Lance l'optimisation des paramètres
        
        Args:
            media_data: Données média à optimiser
            method: Méthode de génération de candidats
            
        Returns:
            Résultat d'optimisation complet
        """
        logger.info(f"Début optimisation paramètres: {self.optimization_target.value}")
        
        # Génération des candidats
        candidates = self.generate_parameter_candidates(method)
        logger.info(f"Génération de {len(candidates)} candidats")
        
        # Évaluation parallèle
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []
            for candidate in candidates:
                future = executor.submit(self.evaluate_parameters, media_data, candidate)
                futures.append(future)
            
            for future in futures:
                try:
                    result = future.result(timeout=30)  # Timeout 30s
                    if 'error' not in result:
                        all_results.append(result)
                except Exception as e:
                    logger.warning(f"Erreur évaluation parallèle: {e}")
        
        # Tri par score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        if not all_results:
            raise ValueError("Aucun résultat valide obtenu")
        
        # Meilleur résultat
        best_result = all_results[0]
        best_parameters = ParameterSet(
            k_factor=best_result['k_factor'],
            webp_quality=best_result['webp_quality'],
            description=best_result['description']
        )
        
        # Mise à jour historique
        self.optimization_history.extend(all_results)
        if self.best_global_result is None or best_result['score'] > self.best_global_result['score']:
            self.best_global_result = best_result.copy()
        
        # Vérification objectif atteint
        target_achieved = self._check_target_achieved(best_result)
        
        logger.info(f"Optimisation terminée: K={best_parameters.k_factor:.4f}, Q={best_parameters.webp_quality}")
        logger.info(f"Score: {best_result['score']:.3f}, Objectif atteint: {target_achieved}")
        
        return OptimizationResult(
            best_parameters=best_parameters,
            performance_metrics={
                'compression_ratio': best_result.get('compression_ratio', 0),
                'processing_time': best_result.get('processing_time', 0),
                'size_efficiency': best_result.get('size_efficiency', 0)
            },
            quality_metrics={
                'quality_score': best_result.get('quality_score', 0),
                'estimated_psnr': best_result.get('quality_score', 0) * 40  # Estimation
            },
            optimization_score=best_result['score'],
            target_achieved=target_achieved,
            all_results=all_results[:10]  # Top 10 résultats
        )
    
    def _check_target_achieved(self, result: Dict[str, Any]) -> bool:
        """Vérifie si l'objectif d'optimisation est atteint"""
        if self.optimization_target == OptimizationTarget.MAX_QUALITY:
            return result.get('quality_score', 0) > 0.8
        elif self.optimization_target == OptimizationTarget.MAX_COMPRESSION:
            return result.get('compression_ratio', 0) > 50
        elif self.optimization_target == OptimizationTarget.BALANCED:
            return (result.get('quality_score', 0) > 0.6 and 
                   result.get('compression_ratio', 0) > 20 and
                   result.get('processing_time', 999) < 1.0)
        elif self.optimization_target == OptimizationTarget.FAST_PROCESSING:
            return result.get('processing_time', 999) < 0.5
        elif self.optimization_target == OptimizationTarget.MIN_SIZE:
            return result.get('compression_ratio', 0) > 100
        else:
            return result.get('score', 0) > 0.5
    
    def save_optimization_results(self, filepath: str):
        """Sauvegarde les résultats d'optimisation"""
        results_data = {
            'optimization_target': self.optimization_target.value,
            'media_type': self.media_type.value,
            'best_global_result': self.best_global_result,
            'optimization_history': self.optimization_history[-50:],  # Derniers 50
            'weights': self.weights
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Résultats sauvegardés: {filepath}")
    
    def load_optimization_results(self, filepath: str):
        """Charge les résultats d'optimisation précédents"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                results_data = json.load(f)
            
            self.best_global_result = results_data.get('best_global_result')
            self.optimization_history = results_data.get('optimization_history', [])
            
            logger.info(f"Résultats chargés: {filepath}")
        except Exception as e:
            logger.warning(f"Impossible de charger les résultats: {e}")
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'optimisation"""
        if not self.optimization_history:
            return {'status': 'no_data', 'message': 'Aucune optimisation effectuée'}
        
        # Analyse des résultats
        scores = [r['score'] for r in self.optimization_history]
        ratios = [r.get('compression_ratio', 0) for r in self.optimization_history]
        qualities = [r.get('quality_score', 0) for r in self.optimization_history]
        times = [r.get('processing_time', 0) for r in self.optimization_history]
        
        return {
            'status': 'completed',
            'optimization_target': self.optimization_target.value,
            'media_type': self.media_type.value,
            'total_evaluations': len(self.optimization_history),
            'best_score': max(scores),
            'avg_score': np.mean(scores),
            'best_ratio': max(ratios),
            'avg_ratio': np.mean(ratios),
            'best_quality': max(qualities),
            'avg_quality': np.mean(qualities),
            'best_time': min(times),
            'avg_time': np.mean(times),
            'best_parameters': self.best_global_result if self.best_global_result else None
        }

# Test et validation
if __name__ == "__main__":
    # Test de l'optimiseur
    print("🔧 TEST OPTIMISEUR DE PARAMÈTRES HYBRIDE")
    print("=" * 60)
    
    # Image de test
    test_image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    
    # Test différents objectifs
    objectives = [
        OptimizationTarget.MAX_QUALITY,
        OptimizationTarget.MAX_COMPRESSION,
        OptimizationTarget.BALANCED,
        OptimizationTarget.FAST_PROCESSING
    ]
    
    for objective in objectives:
        print(f"\n🎯 Test optimisation: {objective.value}")
        
        optimizer = HybridParameterOptimizer(
            optimization_target=objective,
            media_type=MediaType.IMAGE,
            max_iterations=20
        )
        
        result = optimizer.optimize_parameters(test_image, method="grid")
        
        print(f"   Meilleurs paramètres:")
        print(f"      K-Factor: {result.best_parameters.k_factor:.4f}")
        print(f"      WebP Quality: {result.best_parameters.webp_quality}")
        print(f"   Score: {result.optimization_score:.3f}")
        print(f"   Ratio: {result.performance_metrics['compression_ratio']:.1f}:1")
        print(f"   Qualité: {result.quality_metrics['quality_score']:.3f}")
        print(f"   Temps: {result.performance_metrics['processing_time']:.3f}s")
        print(f"   Objectif atteint: {result.target_achieved}")
    
    print(f"\n✅ Tests optimisation terminés!")
    print("🔧 Optimiseur de paramètres hybride fonctionnel!")
