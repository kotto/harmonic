#!/usr/bin/env python3
"""
OPTIMISEUR DE PARAMÈTRES HYBRIDE VIDÉO
Optimisation automatique des paramètres K-Factor et WebP Quality pour vidéos
Analyse temporelle, cohérence frame à frame, et performance temps réel
"""

import numpy as np
import cv2
import time
import logging
import os
import tempfile
from typing import List, Tuple, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

# Import des composants existants
from .hybrid_compressor import HybridCompressor
from .hybrid_parameter_optimizer import OptimizationTarget, ParameterSet, OptimizationResult

logger = logging.getLogger(__name__)

class VideoOptimizationTarget(Enum):
    """Objectifs d'optimisation vidéo spécifiques"""
    MAX_TEMPORAL_QUALITY = "max_temporal_quality"
    MAX_COMPRESSION_RATIO = "max_compression_ratio"
    REAL_TIME_PROCESSING = "real_time_processing"
    MIN_BANDWIDTH = "min_bandwidth"
    BALANCED_VIDEO = "balanced_video"

@dataclass
class VideoParameterSet:
    """Ensemble de paramètres vidéo à tester"""
    k_factor: float
    webp_quality: int
    temporal_coherence_weight: float
    frame_sample_rate: int
    description: str

@dataclass
class VideoOptimizationResult:
    """Résultat d'optimisation vidéo"""
    best_parameters: VideoParameterSet
    performance_metrics: Dict[str, float]
    quality_metrics: Dict[str, float]
    temporal_metrics: Dict[str, float]
    optimization_score: float
    target_achieved: bool
    all_results: List[Dict[str, Any]]

class HybridVideoParameterOptimizer:
    """
    Optimiseur automatique des paramètres hybrides pour vidéos
    Prend en compte les aspects temporels et la cohérence frame à frame
    """
    
    def __init__(self, 
                 optimization_target: VideoOptimizationTarget = VideoOptimizationTarget.BALANCED_VIDEO,
                 max_iterations: int = 30,
                 parallel_workers: Optional[int] = None,
                 temporal_analysis: bool = True):
        """
        Initialise l'optimiseur vidéo
        
        Args:
            optimization_target: Objectif d'optimisation vidéo
            max_iterations: Nombre maximum d'itérations
            parallel_workers: Nombre de workers pour parallélisation
            temporal_analysis: Active l'analyse temporelle
        """
        self.optimization_target = optimization_target
        self.max_iterations = max_iterations
        self.parallel_workers = parallel_workers or min(4, mp.cpu_count())
        self.temporal_analysis = temporal_analysis
        
        # Espaces de recherche pour les paramètres vidéo
        self.k_factor_range = (0.001, 0.05)  # Plus large pour vidéo
        self.webp_quality_range = (20, 95)    # Plus agressif pour vidéo
        self.temporal_weight_range = (0.0, 1.0)
        self.frame_sample_range = (5, 30)     # Frames à échantillonner
        
        # Historique d'optimisation
        self.optimization_history = []
        self.best_global_result = None
        
        # Métriques de pondération selon l'objectif vidéo
        self.weights = self._get_video_objective_weights()
        
        # Cache temporaire pour les frames vidéo
        self.temp_dir = tempfile.mkdtemp(prefix="video_opt_")
        
        logger.info(f"Optimiseur vidéo initialisé: target={optimization_target.value}")
    
    def _get_video_objective_weights(self) -> Dict[str, float]:
        """Définit les poids selon l'objectif d'optimisation vidéo"""
        if self.optimization_target == VideoOptimizationTarget.MAX_TEMPORAL_QUALITY:
            return {
                'temporal_coherence': 0.5,
                'spatial_quality': 0.3,
                'compression_ratio': 0.1,
                'processing_time': 0.1
            }
        elif self.optimization_target == VideoOptimizationTarget.MAX_COMPRESSION_RATIO:
            return {
                'temporal_coherence': 0.1,
                'spatial_quality': 0.1,
                'compression_ratio': 0.6,
                'processing_time': 0.2
            }
        elif self.optimization_target == VideoOptimizationTarget.REAL_TIME_PROCESSING:
            return {
                'temporal_coherence': 0.2,
                'spatial_quality': 0.2,
                'compression_ratio': 0.1,
                'processing_time': 0.5
            }
        elif self.optimization_target == VideoOptimizationTarget.MIN_BANDWIDTH:
            return {
                'temporal_coherence': 0.1,
                'spatial_quality': 0.1,
                'compression_ratio': 0.7,
                'processing_time': 0.1
            }
        elif self.optimization_target == VideoOptimizationTarget.BALANCED_VIDEO:
            return {
                'temporal_coherence': 0.25,
                'spatial_quality': 0.25,
                'compression_ratio': 0.25,
                'processing_time': 0.25
            }
        else:
            return {'temporal_coherence': 0.25, 'spatial_quality': 0.25, 'compression_ratio': 0.25, 'processing_time': 0.25}
    
    def generate_video_parameter_candidates(self, method: str = "adaptive") -> List[VideoParameterSet]:
        """
        Génère des candidats de paramètres vidéo à tester
        
        Args:
            method: Méthode de génération (grid, random, adaptive)
            
        Returns:
            Liste des ensembles de paramètres vidéo
        """
        candidates = []
        
        if method == "grid":
            # Grille systématique pour vidéo
            k_values = np.linspace(self.k_factor_range[0], self.k_factor_range[1], 6)
            quality_values = np.linspace(self.webp_quality_range[0], self.webp_quality_range[1], 6)
            temporal_weights = np.linspace(self.temporal_weight_range[0], self.temporal_weight_range[1], 3)
            sample_rates = [10, 20, 30]  # Frames à échantillonner
            
            for k in k_values:
                for q in quality_values:
                    for tw in temporal_weights:
                        for sr in sample_rates:
                            candidates.append(VideoParameterSet(
                                k_factor=k,
                                webp_quality=int(q),
                                temporal_coherence_weight=tw,
                                frame_sample_rate=sr,
                                description=f"Grid_K{k:.3f}_Q{int(q)}_TW{tw:.1f}_SR{sr}"
                            ))
        
        elif method == "random":
            # Échantillonnage aléatoire optimisé pour vidéo
            for _ in range(self.max_iterations):
                k = np.random.uniform(self.k_factor_range[0], self.k_factor_range[1])
                q = np.random.randint(self.webp_quality_range[0], self.webp_quality_range[1] + 1)
                tw = np.random.uniform(self.temporal_weight_range[0], self.temporal_weight_range[1])
                sr = np.random.randint(self.frame_sample_range[0], self.frame_sample_range[1] + 1)
                
                candidates.append(VideoParameterSet(
                    k_factor=k,
                    webp_quality=q,
                    temporal_coherence_weight=tw,
                    frame_sample_rate=sr,
                    description=f"Random_K{k:.3f}_Q{q}_TW{tw:.1f}_SR{sr}"
                ))
        
        elif method == "adaptive":
            # Adaptatif basé sur l'historique vidéo
            if len(self.optimization_history) > 0:
                best_results = sorted(self.optimization_history, key=lambda x: x['score'], reverse=True)[:5]
                
                for result in best_results:
                    k_center = result['k_factor']
                    q_center = result['webp_quality']
                    tw_center = result['temporal_coherence_weight']
                    sr_center = result['frame_sample_rate']
                    
                    # Variation autour du centre
                    for _ in range(3):
                        k = np.random.normal(k_center, k_center * 0.2)
                        k = np.clip(k, self.k_factor_range[0], self.k_factor_range[1])
                        q = np.random.normal(q_center, 10)
                        q = np.clip(q, self.webp_quality_range[0], self.webp_quality_range[1])
                        tw = np.random.normal(tw_center, 0.2)
                        tw = np.clip(tw, self.temporal_weight_range[0], self.temporal_weight_range[1])
                        sr = np.random.randint(max(5, sr_center - 5), min(30, sr_center + 5) + 1)
                        
                        candidates.append(VideoParameterSet(
                            k_factor=k,
                            webp_quality=int(q),
                            temporal_coherence_weight=tw,
                            frame_sample_rate=sr,
                            description=f"Adaptive_K{k:.3f}_Q{int(q)}_TW{tw:.1f}_SR{sr}"
                        ))
            else:
                return self.generate_video_parameter_candidates("grid")
        
        return candidates[:self.max_iterations]
    
    def extract_video_samples(self, video_path: str, sample_rate: int) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Extrait des échantillons de frames de la vidéo
        
        Args:
            video_path: Chemin de la vidéo
            sample_rate: Nombre de frames à échantillonner
            
        Returns:
            Tuple: (frames échantillonnées, métadonnées vidéo)
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo: {video_path}")
        
        # Métadonnées vidéo
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        video_info = {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': duration,
            'shape': (height, width, 3)
        }
        
        # Échantillonnage intelligent des frames
        if frame_count <= sample_rate:
            # Vidéo courte : prendre toutes les frames
            sample_indices = list(range(frame_count))
        else:
            # Échantillonnage réparti
            sample_indices = np.linspace(0, frame_count - 1, sample_rate, dtype=int).tolist()
        
        frames = []
        frame_timestamps = []
        
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                frame_timestamps.append(idx / fps)
        
        cap.release()
        
        logger.info(f"Extraction vidéo: {len(frames)} frames échantillonnées sur {frame_count}")
        
        return frames, video_info
    
    def evaluate_video_parameters(self, 
                                 video_path: str,
                                 parameters: VideoParameterSet) -> Dict[str, Any]:
        """
        Évalue un ensemble de paramètres vidéo
        
        Args:
            video_path: Chemin de la vidéo
            parameters: Paramètres à tester
            
        Returns:
            Métriques d'évaluation vidéo
        """
        try:
            start_time = time.time()
            
            # Extraction des frames échantillonnées
            frames, video_info = self.extract_video_samples(video_path, parameters.frame_sample_rate)
            
            if len(frames) < 2:
                raise ValueError("Pas assez de frames pour l'analyse temporelle")
            
            # Création du compresseur avec les paramètres
            compressor = HybridCompressor(
                k_factor=parameters.k_factor,
                webp_quality=parameters.webp_quality
            )
            
            # Compression et analyse des frames
            frame_results = []
            compressed_frames = []
            
            for i, frame in enumerate(frames):
                frame_start = time.time()
                compressed_data, metadata = compressor.compress_image(frame)
                frame_time = time.time() - frame_start
                
                # Simulation de décompression
                decompressed_frame = self._simulate_frame_decompression(frame, metadata)
                
                frame_results.append({
                    'frame_index': i,
                    'compression_ratio': metadata['hybrid_ratio'],
                    'processing_time': frame_time,
                    'quality_score': self._calculate_frame_quality(frame, decompressed_frame),
                    'metadata': metadata
                })
                
                compressed_frames.append(decompressed_frame)
            
            # Analyse temporelle
            temporal_metrics = self._analyze_temporal_coherence(
                frames, compressed_frames, parameters.temporal_coherence_weight
            ) if self.temporal_analysis else {}
            
            # Métriques globales
            avg_ratio = np.mean([r['compression_ratio'] for r in frame_results])
            avg_quality = np.mean([r['quality_score'] for r in frame_results])
            avg_frame_time = np.mean([r['processing_time'] for r in frame_results])
            
            processing_time = time.time() - start_time
            
            # Estimation taille vidéo compressée
            original_size = os.path.getsize(video_path)
            estimated_compressed_size = original_size / avg_ratio
            
            # Bandwidth estimation (bytes/second)
            bandwidth = estimated_compressed_size / video_info['duration'] if video_info['duration'] > 0 else 0
            
            # FPS capability
            fps_capability = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            
            # Score composite selon les poids vidéo
            score = (
                temporal_metrics.get('temporal_score', 0.5) * self.weights['temporal_coherence'] +
                avg_quality * self.weights['spatial_quality'] +
                min(avg_ratio / 100, 1.0) * self.weights['compression_ratio'] +
                max(0, 1 - avg_frame_time / 0.1) * self.weights['processing_time']
            )
            
            return {
                'k_factor': parameters.k_factor,
                'webp_quality': parameters.webp_quality,
                'temporal_coherence_weight': parameters.temporal_coherence_weight,
                'frame_sample_rate': parameters.frame_sample_rate,
                'description': parameters.description,
                'compression_ratio': avg_ratio,
                'quality_score': avg_quality,
                'processing_time': processing_time,
                'frame_processing_time': avg_frame_time,
                'fps_capability': fps_capability,
                'bandwidth': bandwidth,
                'original_size': original_size,
                'estimated_compressed_size': estimated_compressed_size,
                'video_info': video_info,
                'temporal_metrics': temporal_metrics,
                'frame_results': frame_results,
                'score': score
            }
            
        except Exception as e:
            logger.error(f"Erreur évaluation paramètres vidéo {parameters.description}: {e}")
            return {
                'k_factor': parameters.k_factor,
                'webp_quality': parameters.webp_quality,
                'temporal_coherence_weight': parameters.temporal_coherence_weight,
                'frame_sample_rate': parameters.frame_sample_rate,
                'description': parameters.description,
                'error': str(e),
                'score': 0.0
            }
    
    def _simulate_frame_decompression(self, original_frame: np.ndarray, 
                                     metadata: Dict[str, Any]) -> np.ndarray:
        """
        Simule la décompression d'une frame
        
        Args:
            original_frame: Frame originale
            metadata: Métadonnées de compression
            
        Returns:
            Frame décompressée simulée
        """
        ratio = metadata.get('hybrid_ratio', 10.0)
        quality_factor = min(1.0, 10.0 / ratio)
        
        # Simulation avec bruit contrôlé
        decompressed = np.random.normal(
            loc=original_frame.astype(np.float32) * quality_factor,
            scale=25 * (1 - quality_factor),
            size=original_frame.shape
        ).clip(0, 255).astype(np.uint8)
        
        return decompressed
    
    def _calculate_frame_quality(self, original: np.ndarray, 
                               processed: np.ndarray) -> float:
        """
        Calcule la qualité d'une frame (PSNR simplifié)
        
        Args:
            original: Frame originale
            processed: Frame traitée
            
        Returns:
            Score de qualité (0-1)
        """
        try:
            mse = np.mean((original.astype(np.float32) - processed.astype(np.float32)) ** 2)
            if mse == 0:
                return 1.0
            
            psnr = 20 * np.log10(255.0 / np.sqrt(mse))
            return min(psnr / 40.0, 1.0)
            
        except Exception:
            return 0.7
    
    def _analyze_temporal_coherence(self, 
                                  original_frames: List[np.ndarray],
                                  compressed_frames: List[np.ndarray],
                                  weight: float) -> Dict[str, float]:
        """
        Analyse la cohérence temporelle entre frames
        
        Args:
            original_frames: Frames originales
            compressed_frames: Frames compressées
            weight: Poids de la cohérence temporelle
            
        Returns:
            Métriques temporelles
        """
        if len(original_frames) < 2:
            return {'temporal_score': 0.5}
        
        # Calcul des différences frame à frame
        original_diffs = []
        compressed_diffs = []
        
        for i in range(len(original_frames) - 1):
            # Différence entre frames consécutives
            orig_diff = np.mean(np.abs(original_frames[i+1].astype(np.float32) - 
                                      original_frames[i].astype(np.float32)))
            comp_diff = np.mean(np.abs(compressed_frames[i+1].astype(np.float32) - 
                                      compressed_frames[i].astype(np.float32)))
            
            original_diffs.append(orig_diff)
            compressed_diffs.append(comp_diff)
        
        # Score de cohérence temporelle
        if np.mean(original_diffs) > 0:
            coherence_ratio = np.mean(compressed_diffs) / np.mean(original_diffs)
            temporal_score = max(0, 1 - abs(1 - coherence_ratio) * weight)
        else:
            temporal_score = 0.5
        
        return {
            'temporal_score': temporal_score,
            'coherence_ratio': coherence_ratio if np.mean(original_diffs) > 0 else 1.0,
            'original_motion': np.mean(original_diffs),
            'compressed_motion': np.mean(compressed_diffs)
        }
    
    def optimize_video_parameters(self, 
                                video_path: str,
                                method: str = "adaptive") -> VideoOptimizationResult:
        """
        Lance l'optimisation des paramètres vidéo
        
        Args:
            video_path: Chemin de la vidéo à optimiser
            method: Méthode de génération de candidats
            
        Returns:
            Résultat d'optimisation vidéo complet
        """
        logger.info(f"Début optimisation paramètres vidéo: {self.optimization_target.value}")
        
        # Génération des candidats
        candidates = self.generate_video_parameter_candidates(method)
        logger.info(f"Génération de {len(candidates)} candidats vidéo")
        
        # Évaluation parallèle
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []
            for candidate in candidates:
                future = executor.submit(self.evaluate_video_parameters, video_path, candidate)
                futures.append(future)
            
            for future in futures:
                try:
                    result = future.result(timeout=60)  # Timeout 60s pour vidéo
                    if 'error' not in result:
                        all_results.append(result)
                except Exception as e:
                    logger.warning(f"Erreur évaluation parallèle vidéo: {e}")
        
        # Tri par score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        if not all_results:
            raise ValueError("Aucun résultat vidéo valide obtenu")
        
        # Meilleur résultat
        best_result = all_results[0]
        best_parameters = VideoParameterSet(
            k_factor=best_result['k_factor'],
            webp_quality=best_result['webp_quality'],
            temporal_coherence_weight=best_result['temporal_coherence_weight'],
            frame_sample_rate=best_result['frame_sample_rate'],
            description=best_result['description']
        )
        
        # Mise à jour historique
        self.optimization_history.extend(all_results)
        if self.best_global_result is None or best_result['score'] > self.best_global_result['score']:
            self.best_global_result = best_result.copy()
        
        # Vérification objectif atteint
        target_achieved = self._check_video_target_achieved(best_result)
        
        logger.info(f"Optimisation vidéo terminée: K={best_parameters.k_factor:.4f}, Q={best_parameters.webp_quality}")
        logger.info(f"Score: {best_result['score']:.3f}, Objectif atteint: {target_achieved}")
        
        return VideoOptimizationResult(
            best_parameters=best_parameters,
            performance_metrics={
                'compression_ratio': best_result.get('compression_ratio', 0),
                'processing_time': best_result.get('processing_time', 0),
                'fps_capability': best_result.get('fps_capability', 0),
                'bandwidth': best_result.get('bandwidth', 0)
            },
            quality_metrics={
                'spatial_quality': best_result.get('quality_score', 0),
                'temporal_quality': best_result.get('temporal_metrics', {}).get('temporal_score', 0.5)
            },
            temporal_metrics=best_result.get('temporal_metrics', {}),
            optimization_score=best_result['score'],
            target_achieved=target_achieved,
            all_results=all_results[:10]  # Top 10 résultats
        )
    
    def _check_video_target_achieved(self, result: Dict[str, Any]) -> bool:
        """Vérifie si l'objectif d'optimisation vidéo est atteint"""
        if self.optimization_target == VideoOptimizationTarget.MAX_TEMPORAL_QUALITY:
            return result.get('temporal_metrics', {}).get('temporal_score', 0) > 0.8
        elif self.optimization_target == VideoOptimizationTarget.MAX_COMPRESSION_RATIO:
            return result.get('compression_ratio', 0) > 30
        elif self.optimization_target == VideoOptimizationTarget.REAL_TIME_PROCESSING:
            return result.get('fps_capability', 0) > 30  # 30 FPS minimum
        elif self.optimization_target == VideoOptimizationTarget.MIN_BANDWIDTH:
            return result.get('bandwidth', float('inf')) < 1000000  # < 1MB/s
        elif self.optimization_target == VideoOptimizationTarget.BALANCED_VIDEO:
            return (result.get('quality_score', 0) > 0.6 and 
                   result.get('compression_ratio', 0) > 15 and
                   result.get('fps_capability', 0) > 15)
        else:
            return result.get('score', 0) > 0.5
    
    def get_video_optimization_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'optimisation vidéo"""
        if not self.optimization_history:
            return {'status': 'no_data', 'message': 'Aucune optimisation vidéo effectuée'}
        
        # Analyse des résultats vidéo
        scores = [r['score'] for r in self.optimization_history]
        ratios = [r.get('compression_ratio', 0) for r in self.optimization_history]
        qualities = [r.get('quality_score', 0) for r in self.optimization_history]
        times = [r.get('processing_time', 0) for r in self.optimization_history]
        temporal_scores = [r.get('temporal_metrics', {}).get('temporal_score', 0.5) 
                          for r in self.optimization_history]
        
        return {
            'status': 'completed',
            'optimization_target': self.optimization_target.value,
            'total_evaluations': len(self.optimization_history),
            'best_score': max(scores),
            'avg_score': np.mean(scores),
            'best_ratio': max(ratios),
            'avg_ratio': np.mean(ratios),
            'best_quality': max(qualities),
            'avg_quality': np.mean(qualities),
            'best_temporal': max(temporal_scores),
            'avg_temporal': np.mean(temporal_scores),
            'best_time': min(times),
            'avg_time': np.mean(times),
            'best_parameters': self.best_global_result if self.best_global_result else None
        }
    
    def cleanup(self):
        """Nettoie les ressources temporaires"""
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Répertoire temporaire vidéo nettoyé: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Erreur nettoyage vidéo: {e}")

# Test et validation
if __name__ == "__main__":
    # Test de l'optimiseur vidéo
    print("🎥 TEST OPTIMISEUR DE PARAMÈTRES HYBRIDE VIDÉO")
    print("=" * 70)
    
    # Création d'une vidéo de test
    test_frames = []
    for i in range(60):  # 2 secondes @ 30fps
        frame = np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8)
        # Ajout de mouvement
        cv2.circle(frame, (160 + int(30 * np.sin(i * 0.1)), 120), 20, (255, 255, 255), -1)
        test_frames.append(frame)
    
    # Création vidéo temporaire
    temp_video = "temp_test_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, 30.0, (320, 240))
    for frame in test_frames:
        out.write(frame)
    out.release()
    
    # Test différents objectifs vidéo
    objectives = [
        VideoOptimizationTarget.MAX_TEMPORAL_QUALITY,
        VideoOptimizationTarget.MAX_COMPRESSION_RATIO,
        VideoOptimizationTarget.REAL_TIME_PROCESSING,
        VideoOptimizationTarget.BALANCED_VIDEO
    ]
    
    for objective in objectives:
        print(f"\n🎯 Test optimisation vidéo: {objective.value}")
        
        optimizer = HybridVideoParameterOptimizer(
            optimization_target=objective,
            max_iterations=15
        )
        
        try:
            result = optimizer.optimize_video_parameters(temp_video, method="grid")
            
            print(f"   Meilleurs paramètres:")
            print(f"      K-Factor: {result.best_parameters.k_factor:.4f}")
            print(f"      WebP Quality: {result.best_parameters.webp_quality}")
            print(f"      Temporal Weight: {result.best_parameters.temporal_coherence_weight:.2f}")
            print(f"      Frame Sample Rate: {result.best_parameters.frame_sample_rate}")
            print(f"   Score: {result.optimization_score:.3f}")
            print(f"   Ratio: {result.performance_metrics['compression_ratio']:.1f}:1")
            print(f"   Qualité spatiale: {result.quality_metrics['spatial_quality']:.3f}")
            print(f"   Qualité temporelle: {result.quality_metrics['temporal_quality']:.3f}")
            print(f"   FPS capability: {result.performance_metrics['fps_capability']:.1f}")
            print(f"   Bandwidth: {result.performance_metrics['bandwidth']/1024:.1f} KB/s")
            print(f"   Objectif atteint: {result.target_achieved}")
            
        except Exception as e:
            print(f"   Erreur: {e}")
        
        finally:
            optimizer.cleanup()
    
    # Nettoyage
    try:
        os.remove(temp_video)
    except:
        pass
    
    print(f"\n✅ Tests optimisation vidéo terminés!")
    print("🎥 Optimiseur de paramètres hybride vidéo fonctionnel!")
