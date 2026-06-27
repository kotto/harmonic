#!/usr/bin/env python3
"""
HARMONIC COMPRESSION ENGINE
Moteur principal de compression harmonique
"""

import numpy as np
import cv2
import time
import json
from typing import Dict, Any, Tuple, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
import pickle
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompressionMode(Enum):
    """Modes de compression harmonique"""
    STRUCTURAL = "structural"
    ENTROPIC = "entropic"
    FREQUENCY = "frequency"
    ADAPTIVE = "adaptive"
    QUANTUM_HARMONIC = "quantum_harmonic"
    HYBRID = "hybrid"

@dataclass
class CompressionResult:
    """Résultat de compression harmonique"""
    success: bool
    original_shape: Tuple[int, ...]
    compressed_data: bytes
    compression_ratio: float
    space_saved_percent: float
    processing_time: float
    mode_used: str
    quality_metrics: Dict[str, float]
    energy_used: float
    metadata: Dict[str, Any]
    error: Optional[str] = None

class HarmonicCompressionEngine:
    """
    Moteur principal de compression harmonique
    Inspiré des principes de succès de l'upscaling harmonique
    """
    
    def __init__(self):
        # Presets énergétiques (inspirés de l'upscaling)
        self.energy_presets = {
            'economy': 1e-16,      # Ultra-rapide
            'standard': 1e-15,     # Équilibre optimal
            'high_quality': 1e-14,  # Haute qualité
            'ultra': 1e-13,        # Qualité maximale
            'quantum': 1e-12        # Niveau quantique
        }
        
        # Configuration des encodeurs
        self.encoders = {}
        self._initialize_encoders()
        
        # Statistiques d'apprentissage
        self.learning_stats = {
            'total_processed': 0,
            'mode_performance': {mode.value: {'count': 0, 'avg_ratio': 0.0, 'avg_quality': 0.0} 
                               for mode in CompressionMode},
            'success_rate': 0.0
        }
        
        logger.info("🎵 Moteur de compression harmonique initialisé")
    
    def _initialize_encoders(self):
        """Initialise les différents encodeurs"""
        try:
            from .encoders import (
                StructuralEncoder, EntropicEncoder, 
                AdaptiveEncoder, QuantumHarmonicEncoder
            )
            
            self.encoders = {
                CompressionMode.STRUCTURAL: StructuralEncoder(),
                CompressionMode.ENTROPIC: EntropicEncoder(),
                CompressionMode.ADAPTIVE: AdaptiveEncoder(),
                CompressionMode.QUANTUM_HARMONIC: QuantumHarmonicEncoder()
            }
            
            logger.info(f"✅ {len(self.encoders)} encodeurs initialisés")
            
        except ImportError as e:
            logger.warning(f"⚠️ Import encodeurs impossible: {e}")
            self._create_fallback_encoders()
    
    def _create_fallback_encoders(self):
        """Crée des encodeurs de secours simplifiés"""
        class FallbackEncoder:
            def encode(self, image, energy_budget, target_ratio=None):
                # Compression simple par ré-échantillonnage
                h, w = image.shape[:2]
                scale_factor = 0.5  # Réduction 2x
                
                if len(image.shape) == 3:
                    compressed = cv2.resize(image, (w//2, h//2), 
                                        interpolation=cv2.INTER_AREA)
                else:
                    compressed = cv2.resize(image, (w//2, h//2), 
                                        interpolation=cv2.INTER_AREA)
                
                # Sérialisation
                data = {
                    'method': 'fallback',
                    'data': compressed.tobytes(),
                    'shape': compressed.shape,
                    'scale_factor': scale_factor
                }
                
                compressed_bytes = pickle.dumps(data)
                original_size = image.nbytes
                compression_ratio = original_size / len(compressed_bytes)
                
                return compressed_bytes, {
                    'compression_ratio': compression_ratio,
                    'quality_preservation': 0.7,
                    'energy_efficiency': 0.6
                }
        
        for mode in CompressionMode:
            self.encoders[mode] = FallbackEncoder()
        
        logger.info("🔄 Encodeurs de secours créés")
    
    def compress_image(self, 
                     image: np.ndarray,
                     mode: Optional[str] = None,
                     energy_level: str = 'standard',
                     target_ratio: Optional[float] = None) -> CompressionResult:
        """
        Compression principale d'image avec algorithmes harmoniques
        
        Args:
            image: Image numpy array (H, W) ou (H, W, C)
            mode: Mode de compression (auto-détection si None)
            energy_level: Niveau énergétique ('economy' à 'quantum')
            target_ratio: Ratio cible (optionnel)
        
        Returns:
            CompressionResult: Résultat détaillé de la compression
        """
        start_time = time.time()
        
        try:
            # Validation de l'image
            if not isinstance(image, np.ndarray) or image.size == 0:
                return CompressionResult(
                    success=False,
                    original_shape=(),
                    compressed_data=b'',
                    compression_ratio=0.0,
                    space_saved_percent=0.0,
                    processing_time=0.0,
                    mode_used='',
                    quality_metrics={},
                    energy_used=0.0,
                    metadata={},
                    error="Image invalide"
                )
            
            # Analyse des caractéristiques
            characteristics = self._analyze_image_characteristics(image)
            
            # Sélection du mode optimal
            if mode is None:
                selected_mode = self._select_optimal_mode(characteristics, energy_level)
            else:
                selected_mode = CompressionMode(mode)
            
            # Allocation énergétique
            energy_budget = self.energy_presets.get(energy_level, 1e-15)
            
            logger.info(f"🎵 Compression: {image.shape} → {selected_mode.value}")
            logger.info(f"   Énergie: {energy_level} ({energy_budget:.2e} J)")
            logger.info(f"   Complexité: {characteristics['complexity_score']:.3f}")
            
            # Application de la compression
            encoder = self.encoders[selected_mode]
            compressed_data, metrics = encoder.encode(
                image, energy_budget, target_ratio
            )
            
            # Calcul des métriques finales
            original_size = image.nbytes
            compression_ratio = original_size / len(compressed_data)
            processing_time = time.time() - start_time
            
            # Création du résultat
            result = CompressionResult(
                success=True,
                original_shape=image.shape,
                compressed_data=compressed_data,
                compression_ratio=compression_ratio,
                space_saved_percent=(1 - 1/compression_ratio) * 100,
                processing_time=processing_time,
                mode_used=selected_mode.value,
                quality_metrics=metrics,
                energy_used=energy_budget * metrics.get('energy_efficiency', 0.8),
                metadata={
                    'characteristics': characteristics,
                    'energy_level': energy_level,
                    'target_ratio': target_ratio,
                    'encoder_version': '1.0.0'
                }
            )
            
            # Mise à jour des statistiques
            self._update_learning_stats(selected_mode, compression_ratio, metrics)
            
            logger.info(f"✅ Compression réussie: {compression_ratio:.1f}:1 en {processing_time:.3f}s")
            logger.info(f"   Qualité: {metrics.get('quality_preservation', 0):.3f}")
            logger.info(f"   Efficacité: {metrics.get('energy_efficiency', 0):.3f}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Erreur compression: {e}")
            
            return CompressionResult(
                success=False,
                original_shape=image.shape if 'image' in locals() else (),
                compressed_data=b'',
                compression_ratio=0.0,
                space_saved_percent=0.0,
                processing_time=processing_time,
                mode_used=mode or 'unknown',
                quality_metrics={},
                energy_used=0.0,
                metadata={},
                error=str(e)
            )
    
    def _analyze_image_characteristics(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyse approfondie des caractéristiques de l'image"""
        try:
            from .analyzers import ImageAnalyzer
            analyzer = ImageAnalyzer()
            return analyzer.analyze(image)
        except ImportError:
            # Analyse de secours simplifiée
            return self._fallback_analysis(image)
    
    def _fallback_analysis(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyse de secours si les modules ne sont pas disponibles"""
        h, w = image.shape[:2]
        
        # Conversion en niveaux de gris si nécessaire
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Analyse structurelle
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Analyse de symétrie
        left_half = gray[:, :w//2]
        right_half = np.fliplr(gray[:, w//2:])
        symmetry = np.corrcoef(left_half.flatten(), right_half.flatten())[0,1]
        if np.isnan(symmetry):
            symmetry = 0.0
        
        # Analyse de texture
        texture_variance = np.var(gray)
        
        # Score de complexité (0-1)
        complexity_score = min(1.0, (edge_density + texture_variance/1000 + (1-symmetry))/3)
        
        return {
            'edge_density': edge_density,
            'symmetry': max(symmetry, 0.0),
            'texture_variance': texture_variance,
            'complexity_score': complexity_score,
            'resolution': (h, w),
            'channels': image.shape[2] if len(image.shape) == 3 else 1
        }
    
    def _select_optimal_mode(self, 
                           characteristics: Dict[str, Any], 
                           energy_level: str) -> CompressionMode:
        """Sélection intelligente du mode optimal"""
        
        complexity = characteristics['complexity_score']
        symmetry = characteristics['symmetry']
        edge_density = characteristics['edge_density']
        
        # Logique de sélection
        if symmetry > 0.7 and edge_density < 0.3:
            # Image très symétrique et simple
            return CompressionMode.STRUCTURAL
        
        elif edge_density > 0.6 and complexity > 0.7:
            # Image complexe avec beaucoup de détails
            return CompressionMode.QUANTUM_HARMONIC
        
        elif complexity < 0.4:
            # Image simple, compression entropique efficace
            return CompressionMode.ENTROPIC
        
        elif energy_level in ['ultra', 'quantum']:
            # Haute énergie disponible, mode avancé
            return CompressionMode.QUANTUM_HARMONIC
        
        else:
            # Cas par défaut : adaptatif
            return CompressionMode.ADAPTIVE
    
    def _update_learning_stats(self, 
                           mode: CompressionMode, 
                           ratio: float, 
                           metrics: Dict[str, float]):
        """Met à jour les statistiques d'apprentissage"""
        self.learning_stats['total_processed'] += 1
        
        mode_stats = self.learning_stats['mode_performance'][mode.value]
        n = mode_stats['count']
        
        # Mise à jour des moyennes
        mode_stats['count'] = n + 1
        mode_stats['avg_ratio'] = (mode_stats['avg_ratio'] * n + ratio) / (n + 1)
        mode_stats['avg_quality'] = (mode_stats['avg_quality'] * n + 
                                   metrics.get('quality_preservation', 0)) / (n + 1)
        
        # Mise à jour du taux de succès
        total = self.learning_stats['total_processed']
        successful = sum(stats['count'] for stats in 
                       self.learning_stats['mode_performance'].values())
        self.learning_stats['success_rate'] = successful / total
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retourne les informations complètes du système"""
        return {
            'name': 'Harmonic Compression Engine',
            'version': '1.0.0',
            'description': 'Système de compression adaptative inspiré de l\'upscaling harmonique',
            'modes_available': [mode.value for mode in CompressionMode],
            'energy_presets': self.energy_presets,
            'encoders_count': len(self.encoders),
            'learning_stats': self.learning_stats,
            'capabilities': [
                'Analyse adaptative intelligente',
                'Sélection automatique du mode optimal',
                'Allocation énergétique dynamique',
                'Apprentissage continu',
                'Compression multi-niveaux'
            ]
        }
    
    def batch_compress(self, 
                     images: List[np.ndarray],
                     mode: Optional[str] = None,
                     energy_level: str = 'standard',
                     target_ratio: Optional[float] = None) -> List[CompressionResult]:
        """Compression par lot d'images"""
        results = []
        
        logger.info(f"🔄 Compression batch: {len(images)} images")
        
        for i, image in enumerate(images):
            logger.info(f"   Image {i+1}/{len(images)}")
            result = self.compress_image(image, mode, energy_level, target_ratio)
            results.append(result)
        
        # Statistiques du batch
        successful = sum(1 for r in results if r.success)
        avg_ratio = np.mean([r.compression_ratio for r in results if r.success])
        avg_time = np.mean([r.processing_time for r in results if r.success])
        
        logger.info(f"✅ Batch terminé: {successful}/{len(images)} réussis")
        logger.info(f"   Ratio moyen: {avg_ratio:.1f}:1")
        logger.info(f"   Temps moyen: {avg_time:.3f}s")
        
        return results

# Instance globale pour utilisation facile
harmonic_engine = HarmonicCompressionEngine()
