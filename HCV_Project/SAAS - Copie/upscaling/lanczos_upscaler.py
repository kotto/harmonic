#!/usr/bin/env python3
"""
Lanczos Upscaler pour HCV16 Mobile
Implémentation optimisée Lanczos pour upscaling 4K rapide
"""

import numpy as np
import cv2
from PIL import Image
from .base_upscaler import BaseUpscaler
from typing import Tuple

class LanczosUpscaler(BaseUpscaler):
    """Upscaler Lanczos optimisé pour mobile"""
    
    def __init__(self, target_resolution: Tuple[int, int] = (3840, 2160), lanczos_a: int = 3):
        super().__init__(target_resolution)
        self.name = "LanczosUpscaler"
        self.lanczos_a = lanczos_a  # Paramètre Lanczos (3 = bon compromis qualité/vitesse)
        
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """
        Upscale image vers 4K avec Lanczos
        Optimisé pour performance mobile
        """
        # Vérification format d'entrée
        if len(image.shape) == 3:
            height, width, channels = image.shape
        else:
            height, width = image.shape
            channels = 1
        
        current_size = (width, height)
        
        # Vérifier si upscaling nécessaire
        if not self.needs_upscaling(current_size):
            return image
        
        # Calcul facteurs d'échelle
        scale_x, scale_y = self.calculate_scale_factor(current_size)
        
        # Upscaling avec Lanczos via OpenCV (plus rapide que PIL sur mobile)
        if len(image.shape) == 3:
            # Image couleur
            upscaled = cv2.resize(
                image, 
                self.target_resolution, 
                interpolation=cv2.INTER_LANCZOS4
            )
        else:
            # Image niveaux de gris
            upscaled = cv2.resize(
                image, 
                self.target_resolution, 
                interpolation=cv2.INTER_LANCZOS4
            )
        
        return upscaled
    
    def upscale_pil_fallback(self, image: np.ndarray) -> np.ndarray:
        """
        Fallback avec PIL si OpenCV échoue
        Plus lent mais plus compatible
        """
        # Conversion numpy → PIL
        if len(image.shape) == 3:
            if image.dtype == np.float32 or image.dtype == np.float64:
                image_uint8 = (image * 255).astype(np.uint8)
            else:
                image_uint8 = image.astype(np.uint8)
            
            pil_image = Image.fromarray(image_uint8)
        else:
            if image.dtype == np.float32 or image.dtype == np.float64:
                image_uint8 = (image * 255).astype(np.uint8)
            else:
                image_uint8 = image.astype(np.uint8)
            
            pil_image = Image.fromarray(image_uint8, mode='L')
        
        # Upscaling Lanczos avec PIL
        upscaled_pil = pil_image.resize(
            self.target_resolution, 
            Image.Resampling.LANCZOS
        )
        
        # Conversion PIL → numpy
        upscaled_array = np.array(upscaled_pil)
        
        # Normalisation si nécessaire
        if image.dtype == np.float32 or image.dtype == np.float64:
            upscaled_array = upscaled_array.astype(np.float32) / 255.0
        
        return upscaled_array
    
    def upscale_with_quality_control(self, image: np.ndarray, quality_threshold: float = 0.8) -> np.ndarray:
        """
        Upscaling avec contrôle qualité
        Ajuste les paramètres selon la qualité source
        """
        # Analyse qualité source
        source_quality = self.analyze_source_quality(image)
        
        if source_quality < quality_threshold:
            # Source de faible qualité → pré-traitement
            enhanced_image = self.enhance_before_upscaling(image)
            return self.upscale(enhanced_image)
        else:
            # Source de bonne qualité → upscaling direct
            return self.upscale(image)
    
    def analyze_source_quality(self, image: np.ndarray) -> float:
        """
        Analyse la qualité de l'image source
        Retourne un score 0-1
        """
        # Conversion en niveaux de gris si nécessaire
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Calcul de la netteté (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalisation approximative (à ajuster selon les données)
        quality_score = min(laplacian_var / 1000.0, 1.0)
        
        return quality_score
    
    def enhance_before_upscaling(self, image: np.ndarray) -> np.ndarray:
        """
        Amélioration pré-upscaling pour sources de faible qualité
        """
        if len(image.shape) == 3:
            # Image couleur - amélioration légère
            enhanced = cv2.bilateralFilter(image, 9, 75, 75)
        else:
            # Image niveaux de gris
            enhanced = cv2.bilateralFilter(image, 9, 75, 75)
        
        return enhanced
    
    def batch_upscale(self, images: list) -> list:
        """
        Upscaling par batch pour efficacité
        """
        upscaled_images = []
        
        for i, image in enumerate(images):
            upscaled = self.process_with_stats(image)
            upscaled_images.append(upscaled)
            
            # Log progression
            if (i + 1) % 10 == 0:
                print(f"Upscaled {i + 1}/{len(images)} images")
        
        return upscaled_images
    
    def get_memory_usage_estimate(self, image_shape: Tuple[int, ...]) -> dict:
        """
        Estime l'usage mémoire pour l'upscaling
        """
        if len(image_shape) == 3:
            height, width, channels = image_shape
        else:
            height, width = image_shape
            channels = 1
        
        # Taille source
        source_size_mb = (height * width * channels * 4) / (1024 * 1024)  # float32
        
        # Taille cible 4K
        target_height, target_width = self.target_resolution[1], self.target_resolution[0]
        target_size_mb = (target_height * target_width * channels * 4) / (1024 * 1024)
        
        # Estimation mémoire temporaire (buffers intermédiaires)
        temp_memory_mb = target_size_mb * 1.5  # 50% overhead estimé
        
        return {
            'source_size_mb': source_size_mb,
            'target_size_mb': target_size_mb,
            'temp_memory_mb': temp_memory_mb,
            'total_memory_mb': source_size_mb + target_size_mb + temp_memory_mb
        }