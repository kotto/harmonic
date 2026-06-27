#!/usr/bin/env python3
"""
Smart Upscaler pour HCV16 Mobile
Upscaler intelligent qui choisit la meilleure méthode selon le contenu
"""

import numpy as np
import cv2
from .base_upscaler import BaseUpscaler
from .lanczos_upscaler import LanczosUpscaler
from typing import Tuple, Dict, Any
import time

class SmartUpscaler(BaseUpscaler):
    """Upscaler intelligent adaptatif"""
    
    def __init__(self, target_resolution: Tuple[int, int] = (3840, 2160)):
        super().__init__(target_resolution)
        self.name = "SmartUpscaler"
        
        # Upscalers disponibles
        self.lanczos_upscaler = LanczosUpscaler(target_resolution)
        
        # Statistiques d'usage
        self.method_stats = {
            'lanczos': {'count': 0, 'total_time': 0.0},
            'bicubic': {'count': 0, 'total_time': 0.0},
            'bilinear': {'count': 0, 'total_time': 0.0}
        }
    
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """
        Upscaling intelligent selon analyse du contenu
        """
        # Analyse du contenu pour choisir la méthode optimale
        content_analysis = self.analyze_content(image)
        
        # Sélection de la méthode
        method = self.select_optimal_method(content_analysis)
        
        # Upscaling avec la méthode choisie
        start_time = time.time()
        upscaled = self.apply_method(image, method)
        processing_time = time.time() - start_time
        
        # Mise à jour statistiques
        self.method_stats[method]['count'] += 1
        self.method_stats[method]['total_time'] += processing_time
        
        return upscaled
    
    def analyze_content(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyse le contenu de l'image pour optimiser l'upscaling
        """
        # Conversion en niveaux de gris pour analyse
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # 1. Analyse de la netteté
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness = min(laplacian_var / 1000.0, 1.0)
        
        # 2. Analyse des contours
        edges = cv2.Canny((gray * 255).astype(np.uint8), 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # 3. Analyse de la texture
        # Calcul de la variance locale pour détecter les textures
        kernel = np.ones((5, 5), np.float32) / 25
        local_mean = cv2.filter2D(gray, -1, kernel)
        local_variance = cv2.filter2D(gray**2, -1, kernel) - local_mean**2
        texture_complexity = np.mean(local_variance)
        
        # 4. Analyse du bruit
        # Estimation du bruit par différence avec version lissée
        blurred = cv2.GaussianBlur(gray, (5, 5), 1)
        noise_level = np.std(gray - blurred)
        
        # 5. Classification du type de contenu
        content_type = self.classify_content_type(sharpness, edge_density, texture_complexity)
        
        return {
            'sharpness': sharpness,
            'edge_density': edge_density,
            'texture_complexity': texture_complexity,
            'noise_level': noise_level,
            'content_type': content_type,
            'image_size': gray.shape
        }
    
    def classify_content_type(self, sharpness: float, edge_density: float, texture_complexity: float) -> str:
        """
        Classifie le type de contenu de l'image
        """
        if edge_density > 0.1 and sharpness > 0.5:
            return 'detailed'  # Images détaillées (texte, graphiques)
        elif texture_complexity > 0.01:
            return 'textured'  # Images avec textures (paysages, matériaux)
        elif sharpness < 0.3:
            return 'blurry'    # Images floues ou de faible qualité
        else:
            return 'smooth'    # Images lisses (portraits, objets simples)
    
    def select_optimal_method(self, content_analysis: Dict[str, Any]) -> str:
        """
        Sélectionne la méthode d'upscaling optimale selon l'analyse
        """
        content_type = content_analysis['content_type']
        sharpness = content_analysis['sharpness']
        noise_level = content_analysis['noise_level']
        
        # Règles de sélection
        if content_type == 'detailed' and sharpness > 0.6:
            return 'lanczos'    # Meilleur pour les détails fins
        elif content_type == 'textured':
            return 'lanczos'    # Bon pour les textures
        elif content_type == 'blurry' or noise_level > 0.1:
            return 'bicubic'    # Plus doux pour images floues/bruitées
        else:
            return 'bilinear'   # Plus rapide pour contenu simple
    
    def apply_method(self, image: np.ndarray, method: str) -> np.ndarray:
        """
        Applique la méthode d'upscaling sélectionnée
        """
        if method == 'lanczos':
            return self.lanczos_upscaler.upscale(image)
        elif method == 'bicubic':
            return cv2.resize(image, self.target_resolution, interpolation=cv2.INTER_CUBIC)
        elif method == 'bilinear':
            return cv2.resize(image, self.target_resolution, interpolation=cv2.INTER_LINEAR)
        else:
            # Fallback vers Lanczos
            return self.lanczos_upscaler.upscale(image)
    
    def upscale_with_preprocessing(self, image: np.ndarray) -> np.ndarray:
        """
        Upscaling avec pré-traitement adaptatif
        """
        content_analysis = self.analyze_content(image)
        
        # Pré-traitement selon le type de contenu
        preprocessed = self.preprocess_image(image, content_analysis)
        
        # Upscaling
        upscaled = self.upscale(preprocessed)
        
        # Post-traitement si nécessaire
        final = self.postprocess_image(upscaled, content_analysis)
        
        return final
    
    def preprocess_image(self, image: np.ndarray, analysis: Dict[str, Any]) -> np.ndarray:
        """
        Pré-traitement adaptatif avant upscaling
        """
        processed = image.copy()
        
        # Réduction du bruit si nécessaire
        if analysis['noise_level'] > 0.05:
            if len(processed.shape) == 3:
                processed = cv2.bilateralFilter(processed, 5, 50, 50)
            else:
                processed = cv2.bilateralFilter(processed, 5, 50, 50)
        
        # Amélioration de la netteté pour images floues
        if analysis['content_type'] == 'blurry' and analysis['sharpness'] < 0.3:
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            if len(processed.shape) == 3:
                for c in range(processed.shape[2]):
                    processed[:,:,c] = cv2.filter2D(processed[:,:,c], -1, kernel)
            else:
                processed = cv2.filter2D(processed, -1, kernel)
            
            processed = np.clip(processed, 0, 1)
        
        return processed
    
    def postprocess_image(self, image: np.ndarray, analysis: Dict[str, Any]) -> np.ndarray:
        """
        Post-traitement après upscaling
        """
        # Pour l'instant, pas de post-traitement
        # Peut être étendu avec amélioration de netteté, etc.
        return image
    
    def get_method_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques d'usage des méthodes
        """
        stats = {}
        
        for method, data in self.method_stats.items():
            if data['count'] > 0:
                avg_time = data['total_time'] / data['count']
                stats[method] = {
                    'usage_count': data['count'],
                    'total_time': data['total_time'],
                    'avg_time_per_image': avg_time,
                    'usage_percentage': 0  # Calculé après
                }
        
        # Calcul des pourcentages d'usage
        total_count = sum(data['count'] for data in self.method_stats.values())
        if total_count > 0:
            for method in stats:
                stats[method]['usage_percentage'] = (
                    stats[method]['usage_count'] / total_count * 100
                )
        
        return stats
    
    def optimize_for_mobile(self, battery_level: float = 1.0, cpu_load: float = 0.0) -> None:
        """
        Optimise les paramètres selon l'état du mobile
        """
        # Ajustement selon le niveau de batterie
        if battery_level < 0.2:  # Batterie faible
            # Privilégier les méthodes rapides
            self.prefer_fast_methods = True
        else:
            self.prefer_fast_methods = False
        
        # Ajustement selon la charge CPU
        if cpu_load > 0.8:  # CPU chargé
            self.prefer_fast_methods = True
    
    def benchmark_methods(self, test_image: np.ndarray, iterations: int = 5) -> Dict[str, float]:
        """
        Benchmark des différentes méthodes sur une image test
        """
        methods = ['lanczos', 'bicubic', 'bilinear']
        results = {}
        
        for method in methods:
            times = []
            
            for _ in range(iterations):
                start_time = time.time()
                self.apply_method(test_image, method)
                processing_time = time.time() - start_time
                times.append(processing_time)
            
            results[method] = {
                'avg_time': np.mean(times),
                'std_time': np.std(times),
                'min_time': np.min(times),
                'max_time': np.max(times)
            }
        
        return results