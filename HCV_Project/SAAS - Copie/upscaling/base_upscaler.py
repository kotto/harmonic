#!/usr/bin/env python3
"""
Base Upscaler pour HCV16 Mobile
Architecture modulaire pour différents algorithmes d'upscaling
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Optional
import time

class BaseUpscaler(ABC):
    """Classe de base pour tous les upscalers"""
    
    def __init__(self, target_resolution: Tuple[int, int] = (3840, 2160)):
        self.target_resolution = target_resolution  # 4K par défaut
        self.name = "BaseUpscaler"
        self.performance_stats = {
            'total_processed': 0,
            'total_time': 0.0,
            'avg_time_per_image': 0.0
        }
    
    @abstractmethod
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """Méthode abstraite d'upscaling"""
        pass
    
    def calculate_scale_factor(self, current_size: Tuple[int, int]) -> Tuple[float, float]:
        """Calcule les facteurs d'échelle pour atteindre la résolution cible"""
        current_width, current_height = current_size
        target_width, target_height = self.target_resolution
        
        scale_x = target_width / current_width
        scale_y = target_height / current_height
        
        return scale_x, scale_y
    
    def needs_upscaling(self, current_size: Tuple[int, int]) -> bool:
        """Détermine si l'upscaling est nécessaire"""
        current_width, current_height = current_size
        target_width, target_height = self.target_resolution
        
        return current_width < target_width or current_height < target_height
    
    def process_with_stats(self, image: np.ndarray) -> np.ndarray:
        """Traite l'image avec collecte de statistiques"""
        start_time = time.time()
        
        result = self.upscale(image)
        
        processing_time = time.time() - start_time
        self.performance_stats['total_processed'] += 1
        self.performance_stats['total_time'] += processing_time
        self.performance_stats['avg_time_per_image'] = (
            self.performance_stats['total_time'] / self.performance_stats['total_processed']
        )
        
        return result
    
    def get_performance_stats(self) -> dict:
        """Retourne les statistiques de performance"""
        return self.performance_stats.copy()
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.performance_stats = {
            'total_processed': 0,
            'total_time': 0.0,
            'avg_time_per_image': 0.0
        }