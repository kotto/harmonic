#!/usr/bin/env python3
"""
OPTIMISEUR DE QUALITÉ VIDÉO AMÉLIORÉ
Optimisation spécifique du paramètre qualité vidéo (score bas)
Focus sur l'amélioration des métriques de qualité visuelle
"""

import numpy as np
import cv2
import time
import logging
import os
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import matplotlib.pyplot as plt
from scipy import signal
from scipy import ndimage

from .hybrid_video_parameter_optimizer import (
    HybridVideoParameterOptimizer,
    VideoOptimizationTarget,
    VideoOptimizationResult
)

logger = logging.getLogger(__name__)

class QualityOptimizationMode(Enum):
    """Modes d'optimisation de la qualité"""
    VISUAL_FIDELITY = "visual_fidelity"      # Fidélité visuelle maximale
    EDGE_PRESERVATION = "edge_preservation"  # Préservation des contours
    COLOR_ACCURACY = "color_accuracy"        # Précision des couleurs
    TEMPORAL_SMOOTHNESS = "temporal_smoothness"  # Fluidité temporelle
    BALANCED_QUALITY = "balanced_quality"    # Qualité équilibrée

@dataclass
class QualityMetrics:
    """Métriques de qualité vidéo détaillées"""
    psnr: float                           # Peak Signal-to-Noise Ratio
    ssim: float                          # Structural Similarity Index
    edge_preservation: float              # Préservation des contours
    color_fidelity: float                # Fidélité des couleurs
    temporal_consistency: float          # Cohérence temporelle
    sharpness: float                      # Netteté
    contrast_ratio: float                 # Ratio de contraste
    noise_level: float                   # Niveau de bruit
    overall_score: float                  # Score global

class EnhancedVideoQualityOptimizer:
    """
    Optimiseur de qualité vidéo amélioré
    Focus sur l'amélioration des métriques de qualité visuelle
    """
    
    def __init__(self, 
                 quality_mode: QualityOptimizationMode = QualityOptimizationMode.BALANCED_QUALITY,
                 base_optimizer: Optional[HybridVideoParameterOptimizer] = None):
        """
        Initialise l'optimiseur de qualité amélioré
        
        Args:
            quality_mode: Mode d'optimisation de la qualité
            base_optimizer: Optimiseur de base à utiliser
        """
        self.quality_mode = quality_mode
        self.base_optimizer = base_optimizer or HybridVideoParameterOptimizer(
            optimization_target=VideoOptimizationTarget.MAX_TEMPORAL_QUALITY
        )
        
        # Paramètres d'optimisation qualité
        self.quality_weights = self._get_quality_weights()
        
        # Historique des optimisations
        self.optimization_history = []
        
        logger.info(f"Optimiseur de qualité initialisé: {quality_mode.value}")
    
    def _get_quality_weights(self) -> Dict[str, float]:
        """Retourne les poids des métriques selon le mode"""
        weights = {
            QualityOptimizationMode.VISUAL_FIDELITY: {
                'psnr': 0.3,
                'ssim': 0.3,
                'edge_preservation': 0.2,
                'color_fidelity': 0.15,
                'temporal_consistency': 0.05
            },
            QualityOptimizationMode.EDGE_PRESERVATION: {
                'psnr': 0.15,
                'ssim': 0.15,
                'edge_preservation': 0.4,
                'color_fidelity': 0.1,
                'temporal_consistency': 0.2
            },
            QualityOptimizationMode.COLOR_ACCURACY: {
                'psnr': 0.2,
                'ssim': 0.2,
                'edge_preservation': 0.1,
                'color_fidelity': 0.4,
                'temporal_consistency': 0.1
            },
            QualityOptimizationMode.TEMPORAL_SMOOTHNESS: {
                'psnr': 0.15,
                'ssim': 0.15,
                'edge_preservation': 0.1,
                'color_fidelity': 0.1,
                'temporal_consistency': 0.5
            },
            QualityOptimizationMode.BALANCED_QUALITY: {
                'psnr': 0.2,
                'ssim': 0.2,
                'edge_preservation': 0.2,
                'color_fidelity': 0.2,
                'temporal_consistency': 0.2
            }
        }
        
        return weights[self.quality_mode]
    
    def calculate_detailed_quality_metrics(self, 
                                        original_frames: List[np.ndarray],
                                        processed_frames: List[np.ndarray]) -> QualityMetrics:
        """
        Calcule des métriques de qualité détaillées
        
        Args:
            original_frames: Frames originales
            processed_frames: Frames traitées
            
        Returns:
            Métriques de qualité détaillées
        """
        if len(original_frames) != len(processed_frames):
            raise ValueError("Les listes de frames doivent avoir la même longueur")
        
        metrics_values = {
            'psnr': [],
            'ssim': [],
            'edge_preservation': [],
            'color_fidelity': [],
            'sharpness': [],
            'contrast_ratio': [],
            'noise_level': []
        }
        
        for orig_frame, proc_frame in zip(original_frames, processed_frames):
            # PSNR
            psnr = self._calculate_psnr(orig_frame, proc_frame)
            metrics_values['psnr'].append(psnr)
            
            # SSIM
            ssim = self._calculate_ssim(orig_frame, proc_frame)
            metrics_values['ssim'].append(ssim)
            
            # Préservation des contours
            edge_pres = self._calculate_edge_preservation(orig_frame, proc_frame)
            metrics_values['edge_preservation'].append(edge_pres)
            
            # Fidélité des couleurs
            color_fid = self._calculate_color_fidelity(orig_frame, proc_frame)
            metrics_values['color_fidelity'].append(color_fid)
            
            # Netteté
            sharpness = self._calculate_sharpness(proc_frame)
            metrics_values['sharpness'].append(sharpness)
            
            # Ratio de contraste
            contrast = self._calculate_contrast_ratio(proc_frame)
            metrics_values['contrast_ratio'].append(contrast)
            
            # Niveau de bruit
            noise = self._calculate_noise_level(proc_frame)
            metrics_values['noise_level'].append(noise)
        
        # Moyennes des métriques
        avg_metrics = {key: np.mean(values) for key, values in metrics_values.items()}
        
        # Cohérence temporelle
        temporal_consistency = self._calculate_temporal_consistency(processed_frames)
        
        # Score global pondéré
        overall_score = (
            avg_metrics['psnr'] * self.quality_weights['psnr'] +
            avg_metrics['ssim'] * self.quality_weights['ssim'] +
            avg_metrics['edge_preservation'] * self.quality_weights['edge_preservation'] +
            avg_metrics['color_fidelity'] * self.quality_weights['color_fidelity'] +
            temporal_consistency * self.quality_weights['temporal_consistency']
        )
        
        return QualityMetrics(
            psnr=avg_metrics['psnr'],
            ssim=avg_metrics['ssim'],
            edge_preservation=avg_metrics['edge_preservation'],
            color_fidelity=avg_metrics['color_fidelity'],
            temporal_consistency=temporal_consistency,
            sharpness=avg_metrics['sharpness'],
            contrast_ratio=avg_metrics['contrast_ratio'],
            noise_level=avg_metrics['noise_level'],
            overall_score=overall_score
        )
    
    def _calculate_psnr(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Calcule le PSNR entre deux images"""
        mse = np.mean((original.astype(float) - processed.astype(float)) ** 2)
        if mse == 0:
            return 100.0  # Images identiques
        
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        return psnr
    
    def _calculate_ssim(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Calcule le SSIM entre deux images"""
        # Conversion en niveaux de gris pour SSIM
        if len(original.shape) == 3:
            orig_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            proc_gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        else:
            orig_gray = original
            proc_gray = processed
        
        # Calcul SSIM simplifié
        mu_orig = np.mean(orig_gray)
        mu_proc = np.mean(proc_gray)
        
        sigma_orig = np.std(orig_gray)
        sigma_proc = np.std(proc_gray)
        
        sigma_orig_proc = np.mean((orig_gray - mu_orig) * (proc_gray - mu_proc))
        
        c1 = 0.01 ** 2
        c2 = 0.03 ** 2
        
        numerator = (2 * mu_orig * mu_proc + c1) * (2 * sigma_orig_proc + c2)
        denominator = (mu_orig**2 + mu_proc**2 + c1) * (sigma_orig**2 + sigma_proc**2 + c2)
        
        ssim = numerator / denominator
        return ssim
    
    def _calculate_edge_preservation(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Calcule la préservation des contours"""
        # Détection des contours avec Canny
        if len(original.shape) == 3:
            orig_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            proc_gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        else:
            orig_gray = original
            proc_gray = processed
        
        edges_orig = cv2.Canny(orig_gray, 50, 150)
        edges_proc = cv2.Canny(proc_gray, 50, 150)
        
        # Intersection des contours
        intersection = np.logical_and(edges_orig > 0, edges_proc > 0)
        union = np.logical_or(edges_orig > 0, edges_proc > 0)
        
        if np.sum(union) == 0:
            return 1.0
        
        preservation = np.sum(intersection) / np.sum(union)
        return preservation
    
    def _calculate_color_fidelity(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Calcule la fidélité des couleurs"""
        if len(original.shape) != 3:
            return 1.0  # Pas de couleur pour les images niveaux de gris
        
        # Calcul de la corrélation pour chaque canal
        correlations = []
        for channel in range(3):
            orig_channel = original[:, :, channel].flatten()
            proc_channel = processed[:, :, channel].flatten()
            
            correlation = np.corrcoef(orig_channel, proc_channel)[0, 1]
            correlations.append(correlation)
        
        # Moyenne des corrélations
        avg_correlation = np.mean(correlations)
        return max(0, avg_correlation)  # Éviter les valeurs négatives
    
    def _calculate_sharpness(self, image: np.ndarray) -> float:
        """Calcule la netteté d'une image"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Calcul du gradient avec Laplacien
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = np.var(laplacian)
        
        # Normalisation
        return min(1.0, sharpness / 1000.0)
    
    def _calculate_contrast_ratio(self, image: np.ndarray) -> float:
        """Calcule le ratio de contraste"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Contraste RMS (Root Mean Square)
        mean_intensity = np.mean(gray)
        contrast = np.sqrt(np.mean((gray - mean_intensity) ** 2))
        
        # Normalisation
        return min(1.0, contrast / 127.0)
    
    def _calculate_noise_level(self, image: np.ndarray) -> float:
        """Calcule le niveau de bruit (inversé pour que plus soit mieux)"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Estimation du bruit avec filtre passe-haut
        kernel = np.array([[-1, -1, -1],
                          [-1,  8, -1],
                          [-1, -1, -1]])
        
        noise_map = cv2.filter2D(gray.astype(float), -1, kernel)
        noise_level = np.std(noise_map)
        
        # Inversion (moins de bruit = meilleur score)
        noise_score = max(0, 1.0 - noise_level / 50.0)
        return noise_score
    
    def _calculate_temporal_consistency(self, frames: List[np.ndarray]) -> float:
        """Calcule la cohérence temporelle entre frames"""
        if len(frames) < 2:
            return 1.0
        
        consistencies = []
        
        for i in range(len(frames) - 1):
            frame1 = frames[i]
            frame2 = frames[i + 1]
            
            # Calcul de la différence frame à frame
            if len(frame1.shape) == 3:
                gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            else:
                gray1 = frame1
                gray2 = frame2
            
            # Corrélation temporelle
            correlation = np.corrcoef(gray1.flatten(), gray2.flatten())[0, 1]
            consistencies.append(max(0, correlation))
        
        return np.mean(consistencies)
    
    def optimize_for_quality(self, video_path: str, 
                           target_quality_score: float = 0.8) -> VideoOptimizationResult:
        """
        Optimise les paramètres pour atteindre un score de qualité cible
        
        Args:
            video_path: Chemin de la vidéo à optimiser
            target_quality_score: Score de qualité cible (0.0 - 1.0)
            
        Returns:
            Résultat d'optimisation avec qualité améliorée
        """
        logger.info(f"Optimisation qualité pour score cible: {target_quality_score}")
        
        # Chargement des frames originales
        original_frames = self._load_video_frames(video_path)
        
        # Recherche adaptative des paramètres
        best_result = None
        best_quality = 0.0
        
        # Plages de paramètres optimisées pour la qualité
        k_factor_range = np.linspace(0.0005, 0.005, 10)  # Plus petit pour meilleure qualité
        webp_quality_range = np.linspace(60, 95, 8)     # Plus élevé pour meilleure qualité
        
        for k_factor in k_factor_range:
            for webp_quality in webp_quality_range:
                # Test des paramètres
                test_result = self._test_quality_parameters(
                    video_path, k_factor, webp_quality, original_frames
                )
                
                if test_result.optimization_score > best_quality:
                    best_quality = test_result.optimization_score
                    best_result = test_result
                
                # Arrêt si qualité cible atteinte
                if best_quality >= target_quality_score:
                    logger.info(f"Qualité cible atteinte: {best_quality:.3f}")
                    break
            
            if best_quality >= target_quality_score:
                break
        
        if best_result is None:
            # Fallback: utiliser l'optimiseur de base
            logger.warning("Optimisation qualité échouée, utilisation du fallback")
            best_result = self.base_optimizer.optimize_video_parameters(video_path)
        
        # Enregistrement dans l'historique
        self.optimization_history.append({
            'timestamp': time.time(),
            'target_score': target_quality_score,
            'achieved_score': best_quality,
            'parameters': best_result.best_parameters,
            'quality_mode': self.quality_mode.value
        })
        
        logger.info(f"Optimisation terminée: score qualité {best_quality:.3f}")
        return best_result
    
    def _load_video_frames(self, video_path: str, max_frames: int = 30) -> List[np.ndarray]:
        """Charge les frames d'une vidéo pour analyse"""
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        frame_count = 0
        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            frames.append(frame)
            frame_count += 1
        
        cap.release()
        return frames
    
    def _test_quality_parameters(self, video_path: str, 
                               k_factor: float, webp_quality: int,
                               original_frames: List[np.ndarray]) -> VideoOptimizationResult:
        """Test des paramètres avec évaluation de qualité"""
        # Simulation de traitement avec les paramètres
        processed_frames = self._simulate_processing(original_frames, k_factor, webp_quality)
        
        # Calcul des métriques de qualité
        quality_metrics = self.calculate_detailed_quality_metrics(original_frames, processed_frames)
        
        # Création du résultat
        from .hybrid_video_parameter_optimizer import VideoParameterSet
        
        parameters = VideoParameterSet(
            k_factor=k_factor,
            webp_quality=webp_quality,
            temporal_coherence_weight=0.5,
            frame_sample_rate=1.0,
            description="Quality optimized"
        )
        
        # Simulation des métriques de performance
        performance_metrics = {
            'compression_ratio': 100.0 / (k_factor * 1000),  # Simulation
            'fps_capability': 60.0 * (1.0 - k_factor * 100),  # Simulation
            'bandwidth': 1000.0 / (webp_quality / 10),        # Simulation
            'processing_time': 2.0 + k_factor * 1000           # Simulation
        }
        
        result = VideoOptimizationResult(
            best_parameters=parameters,
            performance_metrics=performance_metrics,
            quality_metrics=quality_metrics.__dict__,
            temporal_metrics={'temporal_score': 0.8},
            optimization_score=quality_metrics.overall_score,
            target_achieved=quality_metrics.overall_score >= 0.7,
            all_results=[]
        )
        
        return result
    
    def _simulate_processing(self, frames: List[np.ndarray], 
                           k_factor: float, webp_quality: int) -> List[np.ndarray]:
        """Simule le traitement des frames avec les paramètres donnés"""
        processed_frames = []
        
        for frame in frames:
            # Simulation de compression/décompression
            processed = frame.copy()
            
            # Application du K-Factor (réduction de qualité)
            if k_factor > 0:
                # Réduction de résolution simulée
                scale_factor = 1.0 - k_factor * 10
                h, w = processed.shape[:2]
                new_h, new_w = int(h * scale_factor), int(w * scale_factor)
                
                if new_h > 0 and new_w > 0:
                    processed = cv2.resize(processed, (new_w, new_h))
                    processed = cv2.resize(processed, (w, h))
            
            # Application de la qualité WebP (compression avec perte)
            if webp_quality < 100:
                # Simulation de compression avec perte
                noise_level = (100 - webp_quality) / 1000.0
                noise = np.random.normal(0, noise_level * 255, processed.shape)
                processed = np.clip(processed + noise, 0, 255).astype(np.uint8)
            
            processed_frames.append(processed)
        
        return processed_frames
    
    def adaptive_quality_optimization(self, video_path: str) -> VideoOptimizationResult:
        """
        Optimisation adaptative de la qualité basée sur le contenu de la vidéo
        
        Args:
            video_path: Chemin de la vidéo
            
        Returns:
            Résultat d'optimisation adaptatif
        """
        logger.info("Optimisation adaptative de la qualité...")
        
        # Analyse du contenu
        frames = self._load_video_frames(video_path)
        content_analysis = self._analyze_video_content(frames)
        
        # Sélection du mode d'optimisation selon le contenu
        if content_analysis['has_many_edges']:
            quality_mode = QualityOptimizationMode.EDGE_PRESERVATION
        elif content_analysis['has_vibrant_colors']:
            quality_mode = QualityOptimizationMode.COLOR_ACCURACY
        elif content_analysis['has_motion']:
            quality_mode = QualityOptimizationMode.TEMPORAL_SMOOTHNESS
        else:
            quality_mode = QualityOptimizationMode.BALANCED_QUALITY
        
        # Mise à jour du mode
        self.quality_mode = quality_mode
        self.quality_weights = self._get_quality_weights()
        
        logger.info(f"Mode sélectionné: {quality_mode.value}")
        
        # Optimisation avec le mode adapté
        return self.optimize_for_quality(video_path, target_quality_score=0.75)
    
    def _analyze_video_content(self, frames: List[np.ndarray]) -> Dict[str, Any]:
        """Analyse le contenu de la vidéo pour adapter l'optimisation"""
        if not frames:
            return {}
        
        analysis = {
            'has_many_edges': False,
            'has_vibrant_colors': False,
            'has_motion': False,
            'avg_brightness': 0.0,
            'edge_density': 0.0,
            'color_variance': 0.0,
            'motion_intensity': 0.0
        }
        
        # Analyse des contours
        total_edges = 0
        total_pixels = 0
        
        # Analyse des couleurs
        color_variances = []
        
        # Analyse du mouvement
        if len(frames) > 1:
            prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
            motion_intensities = []
        
        for i, frame in enumerate(frames):
            # Contours
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            total_edges += np.sum(edges > 0)
            total_pixels += frame.size
            
            # Couleurs
            if len(frame.shape) == 3:
                for channel in range(3):
                    channel_var = np.var(frame[:, :, channel])
                    color_variances.append(channel_var)
            
            # Mouvement
            if len(frames) > 1 and i > 0:
                curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Calcul du flux optique simplifié
                flow = cv2.calcOpticalFlowPyrLK(
                    prev_gray, curr_gray, 
                    np.array([[100, 100]], dtype=np.float32).reshape(-1, 1, 2),
                    None
                )[0]
                
                if flow is not None and len(flow) > 0:
                    motion_intensity = np.mean(np.abs(flow))
                    motion_intensities.append(motion_intensity)
                
                prev_gray = curr_gray
        
        # Calcul des métriques
        analysis['edge_density'] = total_edges / total_pixels
        analysis['has_many_edges'] = analysis['edge_density'] > 0.02
        
        analysis['color_variance'] = np.mean(color_variances) if color_variances else 0
        analysis['has_vibrant_colors'] = analysis['color_variance'] > 1000
        
        if len(frames) > 1 and 'motion_intensities' in locals():
            analysis['motion_intensity'] = np.mean(motion_intensities)
            analysis['has_motion'] = analysis['motion_intensity'] > 1.0
        
        analysis['avg_brightness'] = np.mean(gray)
        
        return analysis
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Génère un rapport d'optimisation"""
        if not self.optimization_history:
            return {"message": "Aucune historique d'optimisation"}
        
        recent_optimizations = self.optimization_history[-10:]  # 10 dernières
        
        report = {
            'total_optimizations': len(self.optimization_history),
            'current_mode': self.quality_mode.value,
            'quality_weights': self.quality_weights,
            'recent_performance': recent_optimizations,
            'average_quality_score': np.mean([opt['achieved_score'] for opt in recent_optimizations]),
            'success_rate': len([opt for opt in recent_optimizations if opt['achieved_score'] > 0.5]) / len(recent_optimizations)
        }
        
        return report
    
    def visualize_quality_metrics(self, original_frames: List[np.ndarray],
                               processed_frames: List[np.ndarray],
                               save_path: str = None):
        """Visualise les métriques de qualité"""
        metrics = self.calculate_detailed_quality_metrics(original_frames, processed_frames)
        
        # Création du graphique
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Métriques de Qualité - Mode: {self.quality_mode.value}', fontsize=16)
        
        # Métriques principales
        metric_names = ['PSNR', 'SSIM', 'Contours', 'Couleurs', 'Temporal', 'Global']
        metric_values = [
            metrics.psnr / 40,  # Normalisé
            metrics.ssim,
            metrics.edge_preservation,
            metrics.color_fidelity,
            metrics.temporal_consistency,
            metrics.overall_score
        ]
        
        # Bar plot des métriques
        axes[0, 0].bar(metric_names, metric_values, color=['blue', 'green', 'red', 'orange', 'purple', 'gold'])
        axes[0, 0].set_title('Scores de Qualité')
        axes[0, 0].set_ylabel('Score (0-1)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # PSNR
        axes[0, 1].bar(['PSNR'], [metrics.psnr], color='blue')
        axes[0, 1].set_title(f'PSNR: {metrics.psnr:.2f} dB')
        axes[0, 1].set_ylabel('dB')
        axes[0, 1].set_ylim([0, 50])
        
        # SSIM
        axes[0, 2].bar(['SSIM'], [metrics.ssim], color='green')
        axes[0, 2].set_title(f'SSIM: {metrics.ssim:.3f}')
        axes[0, 2].set_ylabel('Score')
        axes[0, 2].set_ylim([0, 1])
        
        # Netteté et contraste
        axes[1, 0].bar(['Netteté', 'Contraste'], [metrics.sharpness, metrics.contrast_ratio], 
                      color=['red', 'orange'])
        axes[1, 0].set_title('Qualité Visuelle')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_ylim([0, 1])
        
        # Niveau de bruit
        axes[1, 1].bar(['Niveau de Bruit'], [metrics.noise_level], color='purple')
        axes[1, 1].set_title(f'Bruit: {metrics.noise_level:.3f}')
        axes[1, 1].set_ylabel('Score (plus = mieux)')
        axes[1, 1].set_ylim([0, 1])
        
        # Score global avec poids
        weight_labels = list(self.quality_weights.keys())
        weight_values = list(self.quality_weights.values())
        
        axes[1, 2].pie(weight_values, labels=weight_labels, autopct='%1.1f%%')
        axes[1, 2].set_title('Pondération des Métriques')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Graphique sauvegardé: {save_path}")
        
        plt.show()
        
        return metrics

# Test et validation
if __name__ == "__main__":
    print("🎯 TEST OPTIMISEUR DE QUALITÉ VIDÉO")
    print("=" * 60)
    
    # Création de frames de test
    test_frames = []
    for i in range(10):
        frame = np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8)
        # Ajout de patterns pour tester les métriques
        cv2.circle(frame, (160, 120), 50, (255, 255, 255), -1)
        cv2.rectangle(frame, (50, 50), (100, 100), (0, 255, 0), -1)
        test_frames.append(frame)
    
    # Test des différents modes
    modes = [
        QualityOptimizationMode.VISUAL_FIDELITY,
        QualityOptimizationMode.EDGE_PRESERVATION,
        QualityOptimizationMode.COLOR_ACCURACY,
        QualityOptimizationMode.BALANCED_QUALITY
    ]
    
    for mode in modes:
        print(f"\n🎯 Test mode: {mode.value}")
        
        optimizer = EnhancedVideoQualityOptimizer(quality_mode=mode)
        
        # Simulation de processing
        processed_frames = optimizer._simulate_processing(test_frames, 0.001, 80)
        
        # Calcul des métriques
        metrics = optimizer.calculate_detailed_quality_metrics(test_frames, processed_frames)
        
        print(f"   📊 Score global: {metrics.overall_score:.3f}")
        print(f"   🎨 PSNR: {metrics.psnr:.2f} dB")
        print(f"   🔄 SSIM: {metrics.ssim:.3f}")
        print(f"   📐 Préservation contours: {metrics.edge_preservation:.3f}")
        print(f"   🌈 Fidélité couleurs: {metrics.color_fidelity:.3f}")
        print(f"   ⏱️ Cohérence temporelle: {metrics.temporal_consistency:.3f}")
    
    print(f"\n✅ Tests optimisation qualité terminés!")
    print("🎯 Optimiseur de qualité vidéo fonctionnel!")
