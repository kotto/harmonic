#!/usr/bin/env python3
"""
METRICS MODULE
Métriques de qualité et de performance pour la compression harmonique
"""

import numpy as np
from typing import Dict, Any, Tuple
from dataclasses import dataclass
import cv2

@dataclass
class CompressionMetrics:
    """Métriques de compression de base"""
    compression_ratio: float
    space_saved_percent: float
    processing_time: float
    energy_efficiency: float
    bytes_per_pixel: float

@dataclass
class QualityMetrics:
    """Métriques de qualité de reconstruction"""
    psnr: float
    ssim: float
    lpips: float
    fid_score: float
    structural_preservation: float
    color_preservation: float
    overall_quality: float

class MetricsCalculator:
    """Calculateur de métriques pour la compression harmonique"""
    
    def __init__(self):
        self.cache = {}
    
    def calculate_compression_metrics(self, 
                                    original: np.ndarray, 
                                    compressed: bytes,
                                    processing_time: float) -> CompressionMetrics:
        """Calcule les métriques de compression"""
        
        original_size = original.nbytes
        compressed_size = len(compressed)
        
        compression_ratio = original_size / compressed_size
        space_saved_percent = (1 - compressed_size / original_size) * 100
        bytes_per_pixel = compressed_size / (original.shape[0] * original.shape[1])
        
        # Efficacité énergétique (simulation)
        energy_efficiency = min(1.0, compression_ratio / 100.0)
        
        return CompressionMetrics(
            compression_ratio=compression_ratio,
            space_saved_percent=space_saved_percent,
            processing_time=processing_time,
            energy_efficiency=energy_efficiency,
            bytes_per_pixel=bytes_per_pixel
        )
    
    def calculate_quality_metrics(self, 
                                original: np.ndarray, 
                                reconstructed: np.ndarray) -> QualityMetrics:
        """Calcule les métriques de qualité"""
        
        # PSNR
        psnr = self._calculate_psnr(original, reconstructed)
        
        # SSIM
        ssim = self._calculate_ssim(original, reconstructed)
        
        # LPIPS (simulation)
        lpips = self._calculate_lpips_simulation(original, reconstructed)
        
        # FID Score (simulation)
        fid_score = self._calculate_fid_simulation(original, reconstructed)
        
        # Préservation structurelle
        structural_preservation = self._calculate_structural_preservation(original, reconstructed)
        
        # Préservation des couleurs
        color_preservation = self._calculate_color_preservation(original, reconstructed)
        
        # Qualité globale
        overall_quality = self._calculate_overall_quality(
            psnr, ssim, structural_preservation, color_preservation
        )
        
        return QualityMetrics(
            psnr=psnr,
            ssim=ssim,
            lpips=lpips,
            fid_score=fid_score,
            structural_preservation=structural_preservation,
            color_preservation=color_preservation,
            overall_quality=overall_quality
        )
    
    def _calculate_psnr(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """Calcule le PSNR (Peak Signal-to-Noise Ratio)"""
        mse = np.mean((original.astype(np.float32) - reconstructed.astype(np.float32)) ** 2)
        
        if mse == 0:
            return float('inf')
        
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        
        return psnr
    
    def _calculate_ssim(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """Calcule le SSIM (Structural Similarity Index)"""
        
        # Conversion en niveaux de gris si nécessaire
        if len(original.shape) == 3:
            orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
            recon_gray = cv2.cvtColor(reconstructed, cv2.COLOR_RGB2GRAY)
        else:
            orig_gray = original
            recon_gray = reconstructed
        
        # Paramètres SSIM
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        window_size = 11
        
        # Calcul des moyennes locales
        mu_orig = cv2.GaussianBlur(orig_gray.astype(np.float32), (window_size, window_size), 1.5)
        mu_recon = cv2.GaussianBlur(recon_gray.astype(np.float32), (window_size, window_size), 1.5)
        
        mu_orig_sq = mu_orig ** 2
        mu_recon_sq = mu_recon ** 2
        mu_orig_recon = mu_orig * mu_recon
        
        sigma_orig_sq = cv2.GaussianBlur((orig_gray.astype(np.float32) - mu_orig) ** 2, 
                                       (window_size, window_size), 1.5)
        sigma_recon_sq = cv2.GaussianBlur((recon_gray.astype(np.float32) - mu_recon) ** 2, 
                                        (window_size, window_size), 1.5)
        sigma_orig_recon = cv2.GaussianBlur((orig_gray.astype(np.float32) - mu_orig) * 
                                            (recon_gray.astype(np.float32) - mu_recon), 
                                            (window_size, window_size), 1.5)
        
        # Calcul SSIM
        numerator = (2 * mu_orig_recon + C1) * (2 * sigma_orig_recon + C2)
        denominator = (mu_orig_sq + mu_recon_sq + C1) * (sigma_orig_sq + sigma_recon_sq + C2)
        
        ssim_map = numerator / denominator
        ssim = np.mean(ssim_map)
        
        return ssim
    
    def _calculate_lpips_simulation(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """Simulation du LPIPS (Learned Perceptual Image Patch Similarity)"""
        
        # Simulation basée sur la différence de gradient
        if len(original.shape) == 3:
            orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
            recon_gray = cv2.cvtColor(reconstructed, cv2.COLOR_RGB2GRAY)
        else:
            orig_gray = original
            recon_gray = reconstructed
        
        # Calcul des gradients
        grad_orig_x = cv2.Sobel(orig_gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_orig_y = cv2.Sobel(orig_gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_recon_x = cv2.Sobel(recon_gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_recon_y = cv2.Sobel(recon_gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Différence de gradients
        grad_diff = np.sqrt((grad_orig_x - grad_recon_x) ** 2 + (grad_orig_y - grad_recon_y) ** 2)
        
        # Normalisation pour simuler LPIPS (plus petit = meilleur)
        lpips_score = np.mean(grad_diff) / 255.0
        
        return min(1.0, lpips_score)
    
    def _calculate_fid_simulation(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """Simulation du FID Score (Fréchet Inception Distance)"""
        
        # Simulation basée sur les statistiques des pixels
        if len(original.shape) == 3:
            # Statistiques par canal
            orig_mean = np.mean(original, axis=(0, 1))
            recon_mean = np.mean(reconstructed, axis=(0, 1))
            
            orig_cov = np.cov(original.reshape(-1, 3).T)
            recon_cov = np.cov(reconstructed.reshape(-1, 3).T)
        else:
            # Statistiques globales
            orig_mean = np.mean(original)
            recon_mean = np.mean(reconstructed)
            
            orig_cov = np.cov(original.flatten())
            recon_cov = np.cov(reconstructed.flatten())
        
        # Calcul de la distance de Fréchet (simplifiée)
        mean_diff = np.sum((orig_mean - recon_mean) ** 2)
        
        try:
            cov_sqrt = np.sqrt(orig_cov * recon_cov + 1e-10)
            cov_diff = np.trace(orig_cov + recon_cov - 2 * cov_sqrt)
        except:
            cov_diff = 0.0
        
        fid_score = mean_diff + cov_diff
        
        # Normalisation
        return min(1.0, fid_score / 1000.0)
    
    def _calculate_structural_preservation(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """Calcule la préservation des structures"""
        
        # Détection de contours
        if len(original.shape) == 3:
            orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
            recon_gray = cv2.cvtColor(reconstructed, cv2.COLOR_RGB2GRAY)
        else:
            orig_gray = original
            recon_gray = reconstructed
        
        # Contours Canny
        edges_orig = cv2.Canny(orig_gray, 50, 150)
        edges_recon = cv2.Canny(recon_gray, 50, 150)
        
        # Intersection des contours
        intersection = np.logical_and(edges_orig > 0, edges_recon > 0)
        union = np.logical_or(edges_orig > 0, edges_recon > 0)
        
        if np.sum(union) == 0:
            return 1.0
        
        # IoU des contours
        iou = np.sum(intersection) / np.sum(union)
        
        return iou
    
    def _calculate_color_preservation(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """Calcule la préservation des couleurs"""
        
        if len(original.shape) != 3 or len(reconstructed.shape) != 3:
            return 1.0  # Pas de couleur à préserver
        
        # Corrélation par canal
        correlations = []
        for channel in range(3):
            orig_channel = original[:, :, channel].flatten()
            recon_channel = reconstructed[:, :, channel].flatten()
            
            correlation = np.corrcoef(orig_channel, recon_channel)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            
            correlations.append(max(0.0, correlation))
        
        return np.mean(correlations)
    
    def _calculate_overall_quality(self, psnr: float, ssim: float, 
                                 structural: float, color: float) -> float:
        """Calcule un score de qualité global"""
        
        # Normalisation des métriques
        psnr_norm = min(1.0, psnr / 40.0)  # 40 dB = excellent
        ssim_norm = ssim  # Déjà 0-1
        structural_norm = structural  # Déjà 0-1
        color_norm = color  # Déjà 0-1
        
        # Pondération
        weights = {
            'psnr': 0.3,
            'ssim': 0.3,
            'structural': 0.2,
            'color': 0.2
        }
        
        overall = (
            weights['psnr'] * psnr_norm +
            weights['ssim'] * ssim_norm +
            weights['structural'] * structural_norm +
            weights['color'] * color_norm
        )
        
        return overall

# Classes d'alias pour compatibilité
CompressionMetrics = CompressionMetrics
QualityMetrics = QualityMetrics
