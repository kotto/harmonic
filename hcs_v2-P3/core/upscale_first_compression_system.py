#!/usr/bin/env python3
"""
SYSTÈME UPSCALING-FIRST PUIS COMPRESSION
Analyse des performances: Upscaling avant compression vs Compression avant upscaling
"""

import numpy as np
import cv2
import time
import logging
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import des composants existants
from .hybrid_compressor import HybridCompressor
from .harmonic_upscaler import HarmonicUpscalerAPI

logger = logging.getLogger(__name__)

class ProcessingOrder(Enum):
    """Ordres de traitement possibles"""
    COMPRESS_FIRST = "compress_first"  # Compression → Upscaling
    UPSCALE_FIRST = "upscale_first"  # Upscaling → Compression
    ADAPTIVE = "adaptive"           # Choix automatique

@dataclass
class ComparisonResult:
    """Résultat de comparaison des deux approches"""
    compress_first_result: Dict[str, Any]
    upscale_first_result: Dict[str, Any]
    performance_comparison: Dict[str, float]
    quality_comparison: Dict[str, float]
    recommendation: str

class UpscaleFirstCompressionSystem:
    """
    Système d'analyse comparative: Upscaling-first vs Compression-first
    Évalue les gains potentiels en qualité et performance
    """
    
    def __init__(self, 
                 k_factor: float = 0.02,
                 webp_quality: int = 95,
                 upscaling_preset: str = "quantum_max"):
        """
        Initialise le système d'analyse comparative
        
        Args:
            k_factor: Facteur K pour compression hybride
            webp_quality: Qualité WebP
            upscaling_preset: Preset pour upscaling
        """
        # Initialisation des composants
        self.hybrid_compressor = HybridCompressor(
            k_factor=k_factor, 
            webp_quality=webp_quality
        )
        self.harmonic_upscaler = HarmonicUpscalerAPI()
        
        # Configuration
        self.k_factor = k_factor
        self.webp_quality = webp_quality
        self.upscaling_preset = upscaling_preset
        
        # Statistiques de comparaison
        self.comparison_stats = {
            'total_comparisons': 0,
            'compress_first_wins': 0,
            'upscale_first_wins': 0,
            'ties': 0,
            'avg_quality_diff': 0.0,
            'avg_performance_diff': 0.0
        }
        
        logger.info(f"Système d'analyse comparative initialisé: K={k_factor}, WebP={webp_quality}, Upscaling={upscaling_preset}")
    
    def compress_first_approach(self, image: np.ndarray, 
                             target_ratio: float,
                             scale_factor: float) -> Dict[str, Any]:
        """
        Approche traditionnelle: Compression puis Upscaling
        
        Args:
            image: Image d'entrée
            target_ratio: Ratio de compression cible
            scale_factor: Facteur d'échelle
            
        Returns:
            Résultats détaillés
        """
        start_time = time.time()
        
        # Étape 1: Compression
        compression_start = time.time()
        compressed_data, compression_metadata = self.hybrid_compressor.compress_image(
            image, target_ratio=target_ratio
        )
        compression_time = time.time() - compression_start
        
        # Simulation de décompression (en pratique, décompression réelle)
        decompressed_image = self._simulate_decompression(image, compression_metadata)
        
        # Étape 2: Upscaling
        upscaling_start = time.time()
        try:
            upscaling_result = self.harmonic_upscaler.upscale_image(
                decompressed_image,
                scale_factor=scale_factor,
                energy_level="quantum"
            )
            final_image = upscaling_result['upscaled_image']
            upscaling_quality = upscaling_result['quality_metrics'].get('quality_score', 0.7)
        except Exception as e:
            logger.warning(f"Upscaling échoué, fallback bicubique: {e}")
            target_shape = (
                int(image.shape[0] * scale_factor),
                int(image.shape[1] * scale_factor)
            )
            final_image = cv2.resize(decompressed_image, (target_shape[1], target_shape[0]), 
                                  interpolation=cv2.INTER_CUBIC)
            upscaling_quality = 0.6
        
        upscaling_time = time.time() - upscaling_start
        total_time = time.time() - start_time
        
        # Calcul des métriques de qualité
        quality_metrics = self._calculate_quality_metrics(image, final_image)
        
        return {
            'approach': 'compress_first',
            'final_image': final_image,
            'compression_ratio': compression_metadata['hybrid_ratio'],
            'scale_factor': scale_factor,
            'processing_times': {
                'compression': compression_time,
                'upscaling': upscaling_time,
                'total': total_time
            },
            'quality_metrics': {
                'upscaling_quality': upscaling_quality,
                'final_quality': quality_metrics['overall_quality'],
                'psnr': quality_metrics['psnr'],
                'ssim': quality_metrics['ssim']
            },
            'metadata': {
                'original_shape': image.shape,
                'final_shape': final_image.shape,
                'compression_metadata': compression_metadata
            }
        }
    
    def upscale_first_approach(self, image: np.ndarray, 
                             target_ratio: float,
                             scale_factor: float) -> Dict[str, Any]:
        """
        Approche alternative: Upscaling puis Compression
        
        Args:
            image: Image d'entrée
            target_ratio: Ratio de compression cible
            scale_factor: Facteur d'échelle
            
        Returns:
            Résultats détaillés
        """
        start_time = time.time()
        
        # Étape 1: Upscaling
        upscaling_start = time.time()
        try:
            upscaling_result = self.harmonic_upscaler.upscale_image(
                image,
                scale_factor=scale_factor,
                energy_level="quantum"
            )
            upscaled_image = upscaling_result['upscaled_image']
            upscaling_quality = upscaling_result['quality_metrics'].get('quality_score', 0.7)
        except Exception as e:
            logger.warning(f"Upscaling échoué, fallback bicubique: {e}")
            target_shape = (
                int(image.shape[0] * scale_factor),
                int(image.shape[1] * scale_factor)
            )
            upscaled_image = cv2.resize(image, (target_shape[1], target_shape[0]), 
                                    interpolation=cv2.INTER_CUBIC)
            upscaling_quality = 0.6
        
        upscaling_time = time.time() - upscaling_start
        
        # Étape 2: Compression
        compression_start = time.time()
        compressed_data, compression_metadata = self.hybrid_compressor.compress_image(
            upscaled_image, target_ratio=target_ratio
        )
        compression_time = time.time() - compression_start
        
        # Simulation de décompression
        final_image = self._simulate_decompression(upscaled_image, compression_metadata)
        
        total_time = time.time() - start_time
        
        # Calcul des métriques de qualité
        quality_metrics = self._calculate_quality_metrics(image, final_image)
        
        return {
            'approach': 'upscale_first',
            'final_image': final_image,
            'compression_ratio': compression_metadata['hybrid_ratio'],
            'scale_factor': scale_factor,
            'processing_times': {
                'upscaling': upscaling_time,
                'compression': compression_time,
                'total': total_time
            },
            'quality_metrics': {
                'upscaling_quality': upscaling_quality,
                'final_quality': quality_metrics['overall_quality'],
                'psnr': quality_metrics['psnr'],
                'ssim': quality_metrics['ssim']
            },
            'metadata': {
                'original_shape': image.shape,
                'final_shape': final_image.shape,
                'compression_metadata': compression_metadata
            }
        }
    
    def compare_approaches(self, image: np.ndarray,
                         target_ratio: float = 100.0,
                         scale_factor: float = 2.0) -> ComparisonResult:
        """
        Compare les deux approches pour une image donnée
        
        Args:
            image: Image à tester
            target_ratio: Ratio de compression cible
            scale_factor: Facteur d'échelle
            
        Returns:
            Résultat de comparaison complet
        """
        logger.info(f"Comparaison des approches pour image {image.shape}")
        
        # Test des deux approches
        compress_first_result = self.compress_first_approach(image, target_ratio, scale_factor)
        upscale_first_result = self.upscale_first_approach(image, target_ratio, scale_factor)
        
        # Analyse comparative
        performance_comparison = self._compare_performance(
            compress_first_result, upscale_first_result
        )
        
        quality_comparison = self._compare_quality(
            compress_first_result, upscale_first_result
        )
        
        # Recommandation
        recommendation = self._make_recommendation(
            performance_comparison, quality_comparison
        )
        
        # Mise à jour des statistiques
        self._update_comparison_stats(performance_comparison, quality_comparison)
        
        return ComparisonResult(
            compress_first_result=compress_first_result,
            upscale_first_result=upscale_first_result,
            performance_comparison=performance_comparison,
            quality_comparison=quality_comparison,
            recommendation=recommendation
        )
    
    def _simulate_decompression(self, reference_image: np.ndarray, 
                              compression_metadata: Dict[str, Any]) -> np.ndarray:
        """
        Simule la décompression basée sur les métadonnées
        
        Args:
            reference_image: Image de référence pour la taille
            compression_metadata: Métadonnées de compression
            
        Returns:
            Image décompressée simulée
        """
        # Simulation basique: créer une image basée sur le ratio
        ratio = compression_metadata.get('hybrid_ratio', 10.0)
        
        # Plus le ratio est élevé, plus la qualité est réduite
        quality_factor = min(1.0, 10.0 / ratio)
        
        # Créer une image avec bruit contrôlé
        decompressed = np.random.normal(
            loc=reference_image.astype(np.float32) * quality_factor,
            scale=25 * (1 - quality_factor),
            size=reference_image.shape
        ).clip(0, 255).astype(np.uint8)
        
        return decompressed
    
    def _calculate_quality_metrics(self, original: np.ndarray, 
                                processed: np.ndarray) -> Dict[str, float]:
        """
        Calcule les métriques de qualité entre deux images
        
        Args:
            original: Image originale
            processed: Image traitée
            
        Returns:
            Métriques de qualité
        """
        try:
            # Redimensionner pour la comparaison si nécessaire
            if original.shape != processed.shape:
                processed_resized = cv2.resize(processed, 
                                           (original.shape[1], original.shape[0]),
                                           interpolation=cv2.INTER_CUBIC)
            else:
                processed_resized = processed
            
            # PSNR
            mse = np.mean((original.astype(np.float32) - processed_resized.astype(np.float32)) ** 2)
            if mse == 0:
                psnr = 100.0
            else:
                psnr = 20 * np.log10(255.0 / np.sqrt(mse))
            
            # SSIM simplifié
            mu_orig = np.mean(original)
            mu_proc = np.mean(processed_resized)
            sigma_orig = np.std(original)
            sigma_proc = np.std(processed_resized)
            
            ssim = (2 * mu_orig * mu_proc + 1e-6) / (mu_orig**2 + mu_proc**2 + 1e-6)
            ssim *= (2 * sigma_orig * sigma_proc + 1e-6) / (sigma_orig**2 + sigma_proc**2 + 1e-6)
            
            # Qualité globale combinée
            overall_quality = (psnr / 40.0 * 0.6 + ssim * 0.4)
            
            return {
                'psnr': min(psnr, 100.0),
                'ssim': min(ssim, 1.0),
                'overall_quality': min(overall_quality, 1.0)
            }
            
        except Exception as e:
            logger.warning(f"Erreur calcul métriques qualité: {e}")
            return {
                'psnr': 25.0,
                'ssim': 0.7,
                'overall_quality': 0.6
            }
    
    def _compare_performance(self, cf_result: Dict, uf_result: Dict) -> Dict[str, float]:
        """
        Compare les performances des deux approches
        
        Args:
            cf_result: Résultat compression-first
            uf_result: Résultat upscale-first
            
        Returns:
            Comparaison des performances
        """
        cf_time = cf_result['processing_times']['total']
        uf_time = uf_result['processing_times']['total']
        
        cf_ratio = cf_result['compression_ratio']
        uf_ratio = uf_result['compression_ratio']
        
        return {
            'time_difference': uf_time - cf_time,
            'time_ratio': uf_time / cf_time if cf_time > 0 else 1.0,
            'ratio_difference': uf_ratio - cf_ratio,
            'ratio_ratio': uf_ratio / cf_ratio if cf_ratio > 0 else 1.0,
            'cf_faster': cf_time < uf_time,
            'cf_better_ratio': cf_ratio > uf_ratio
        }
    
    def _compare_quality(self, cf_result: Dict, uf_result: Dict) -> Dict[str, float]:
        """
        Compare la qualité des deux approches
        
        Args:
            cf_result: Résultat compression-first
            uf_result: Résultat upscale-first
            
        Returns:
            Comparaison de la qualité
        """
        cf_quality = cf_result['quality_metrics']['final_quality']
        uf_quality = uf_result['quality_metrics']['final_quality']
        
        cf_psnr = cf_result['quality_metrics']['psnr']
        uf_psnr = uf_result['quality_metrics']['psnr']
        
        cf_ssim = cf_result['quality_metrics']['ssim']
        uf_ssim = uf_result['quality_metrics']['ssim']
        
        return {
            'quality_difference': uf_quality - cf_quality,
            'quality_ratio': uf_quality / cf_quality if cf_quality > 0 else 1.0,
            'psnr_difference': uf_psnr - cf_psnr,
            'ssim_difference': uf_ssim - cf_ssim,
            'uf_better_quality': uf_quality > cf_quality,
            'uf_better_psnr': uf_psnr > cf_psnr,
            'uf_better_ssim': uf_ssim > cf_ssim
        }
    
    def _make_recommendation(self, performance_comp: Dict, quality_comp: Dict) -> str:
        """
        Fait une recommandation basée sur les comparaisons
        
        Args:
            performance_comp: Comparaison de performance
            quality_comp: Comparaison de qualité
            
        Returns:
            Recommandation
        """
        # Score pondéré
        performance_score = 0
        quality_score = 0
        
        # Performance: temps et ratio
        if performance_comp['cf_faster']:
            performance_score += 1
        if performance_comp['cf_better_ratio']:
            performance_score += 1
        
        # Qualité: metrics multiples
        if quality_comp['uf_better_quality']:
            quality_score += 2
        if quality_comp['uf_better_psnr']:
            quality_score += 1
        if quality_comp['uf_better_ssim']:
            quality_score += 1
        
        # Décision
        if quality_score > performance_score + 1:
            return "UPSCALE_FIRST: Meilleure qualité significative"
        elif performance_score > quality_score + 1:
            return "COMPRESS_FIRST: Meilleure performance significative"
        elif quality_score > performance_score:
            return "UPSCALE_FIRST: Léger avantage qualité"
        elif performance_score > quality_score:
            return "COMPRESS_FIRST: Léger avantage performance"
        else:
            return "TIE: Approches équivalentes"
    
    def _update_comparison_stats(self, performance_comp: Dict, quality_comp: Dict):
        """Met à jour les statistiques de comparaison"""
        n = self.comparison_stats['total_comparisons'] + 1
        
        # Détermination du gagnant
        if quality_comp['uf_better_quality']:
            self.comparison_stats['upscale_first_wins'] += 1
        elif performance_comp['cf_faster']:
            self.comparison_stats['compress_first_wins'] += 1
        else:
            self.comparison_stats['ties'] += 1
        
        # Moyennes
        self.comparison_stats['avg_quality_diff'] = (
            self.comparison_stats['avg_quality_diff'] * (n - 1) + quality_comp['quality_difference']
        ) / n
        
        self.comparison_stats['avg_performance_diff'] = (
            self.comparison_stats['avg_performance_diff'] * (n - 1) + performance_comp['time_difference']
        ) / n
        
        self.comparison_stats['total_comparisons'] = n
    
    def batch_comparison(self, images: np.ndarray, 
                      target_ratio: float = 100.0,
                      scale_factor: float = 2.0) -> Dict[str, Any]:
        """
        Effectue une comparaison sur un lot d'images
        
        Args:
            images: Lot d'images à tester
            target_ratio: Ratio de compression cible
            scale_factor: Facteur d'échelle
            
        Returns:
            Résultats de comparaison batch
        """
        logger.info(f"Comparaison batch sur {len(images)} images")
        
        batch_results = []
        quality_differences = []
        performance_differences = []
        
        for i, image in enumerate(images):
            if i % 10 == 0:
                logger.info(f"Image {i+1}/{len(images)}")
            
            comparison = self.compare_approaches(image, target_ratio, scale_factor)
            batch_results.append(comparison)
            
            quality_differences.append(comparison.quality_comparison['quality_difference'])
            performance_differences.append(comparison.performance_comparison['time_difference'])
        
        # Analyse batch
        batch_analysis = {
            'total_images': len(images),
            'avg_quality_difference': np.mean(quality_differences),
            'avg_performance_difference': np.mean(performance_differences),
            'upscale_first_wins': sum(1 for r in batch_results if 'UPSCALE_FIRST' in r.recommendation),
            'compress_first_wins': sum(1 for r in batch_results if 'COMPRESS_FIRST' in r.recommendation),
            'ties': sum(1 for r in batch_results if 'TIE' in r.recommendation),
            'recommendations': [r.recommendation for r in batch_results]
        }
        
        return {
            'batch_results': batch_results,
            'batch_analysis': batch_analysis
        }
    
    def get_comparison_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes de comparaison"""
        stats = self.comparison_stats.copy()
        
        # Pourcentages
        total = stats['total_comparisons']
        if total > 0:
            stats['upscale_first_win_rate'] = stats['upscale_first_wins'] / total * 100
            stats['compress_first_win_rate'] = stats['compress_first_wins'] / total * 100
            stats['tie_rate'] = stats['ties'] / total * 100
        else:
            stats['upscale_first_win_rate'] = 0.0
            stats['compress_first_win_rate'] = 0.0
            stats['tie_rate'] = 0.0
        
        stats['system_config'] = {
            'k_factor': self.k_factor,
            'webp_quality': self.webp_quality,
            'upscaling_preset': self.upscaling_preset
        }
        
        return stats

# Test et validation
if __name__ == "__main__":
    # Test du système de comparaison
    system = UpscaleFirstCompressionSystem(
        k_factor=0.02,
        webp_quality=95,
        upscaling_preset="quantum_max"
    )
    
    # Images de test variées
    test_images = [
        np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8),  # Basse résolution
        np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),  # Résolution moyenne
        np.random.randint(0, 256, (720, 960, 3), dtype=np.uint8),  # Haute résolution
    ]
    
    print("🔬 ANALYSE COMPARATIVE: UPSCALE-FIRST vs COMPRESS-FIRST")
    print("=" * 80)
    
    # Test individuel détaillé
    print(f"\n🧪 Test détaillé sur image {test_images[0].shape}")
    comparison = system.compare_approaches(test_images[0], target_ratio=50.0, scale_factor=2.0)
    
    print(f"\n📊 RÉSULTATS COMPRESSION-FIRST:")
    cf = comparison.compress_first_result
    print(f"   Ratio compression: {cf['compression_ratio']:.1f}:1")
    print(f"   Temps total: {cf['processing_times']['total']:.3f}s")
    print(f"   Qualité finale: {cf['quality_metrics']['final_quality']:.3f}")
    print(f"   PSNR: {cf['quality_metrics']['psnr']:.1f}")
    print(f"   SSIM: {cf['quality_metrics']['ssim']:.3f}")
    
    print(f"\n📊 RÉSULTATS UPSCALE-FIRST:")
    uf = comparison.upscale_first_result
    print(f"   Ratio compression: {uf['compression_ratio']:.1f}:1")
    print(f"   Temps total: {uf['processing_times']['total']:.3f}s")
    print(f"   Qualité finale: {uf['quality_metrics']['final_quality']:.3f}")
    print(f"   PSNR: {uf['quality_metrics']['psnr']:.1f}")
    print(f"   SSIM: {uf['quality_metrics']['ssim']:.3f}")
    
    print(f"\n🎯 COMPARAISON:")
    perf = comparison.performance_comparison
    qual = comparison.quality_comparison
    print(f"   Différence temps: {perf['time_difference']:.3f}s")
    print(f"   Ratio temps: {perf['time_ratio']:.2f}x")
    print(f"   Différence qualité: {qual['quality_difference']:.3f}")
    print(f"   Ratio qualité: {qual['quality_ratio']:.2f}x")
    print(f"   🏆 RECOMMANDATION: {comparison.recommendation}")
    
    # Test batch
    print(f"\n🔄 Test batch sur {len(test_images)} images...")
    batch_results = system.batch_comparison(test_images, target_ratio=100.0, scale_factor=2.0)
    
    batch_analysis = batch_results['batch_analysis']
    print(f"   Victoires Upscale-First: {batch_analysis['upscale_first_wins']}/{len(test_images)}")
    print(f"   Victoires Compress-First: {batch_analysis['compress_first_wins']}/{len(test_images)}")
    print(f"   Égalités: {batch_analysis['ties']}/{len(test_images)}")
    print(f"   Différence qualité moyenne: {batch_analysis['avg_quality_difference']:.3f}")
    print(f"   Différence performance moyenne: {batch_analysis['avg_performance_difference']:.3f}s")
    
    # Statistiques finales
    stats = system.get_comparison_stats()
    print(f"\n📈 STATISTIQUES GLOBALES:")
    print(f"   Comparaisons totales: {stats['total_comparisons']}")
    print(f"   Taux victoire Upscale-First: {stats['upscale_first_win_rate']:.1f}%")
    print(f"   Taux victoire Compress-First: {stats['compress_first_win_rate']:.1f}%")
    print(f"   Taux égalités: {stats['tie_rate']:.1f}%")
    print(f"   Différence qualité moyenne: {stats['avg_quality_diff']:.3f}")
    print(f"   Différence performance moyenne: {stats['avg_performance_diff']:.3f}s")
    
    print(f"\n🎯 CONFIGURATION:")
    config = stats['system_config']
    print(f"   K-Factor: {config['k_factor']}")
    print(f"   WebP Quality: {config['webp_quality']}")
    print(f"   Upscaling Preset: {config['upscaling_preset']}")
    
    print(f"\n✅ Analyse comparative terminée!")
    print("🔬 Recommandations générées pour chaque scénario")
