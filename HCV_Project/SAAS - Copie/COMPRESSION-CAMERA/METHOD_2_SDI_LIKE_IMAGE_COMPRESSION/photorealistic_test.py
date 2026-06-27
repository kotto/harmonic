#!/usr/bin/env python3
"""
TEST DE COMPRESSION SDI-LIKE SUR IMAGES PHOTORÉALISTES
Création et test d'images naturelles réelles
"""

import numpy as np
import cv2
import time
import json
from pathlib import Path
import logging
from sdi_like_image_compression import SDILikeImageCompressor

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhotorealisticImageGenerator:
    """
    Générateur d'images photoréalistes pour les tests
    """
    
    def __init__(self):
        self.width = 1024
        self.height = 768
        
    def create_natural_landscape(self) -> np.ndarray:
        """
        Crée un paysage naturel photoréaliste
        """
        logger.info("Création paysage naturel...")
        
        # Base du ciel
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Ciel avec dégradé
        for y in range(self.height // 2):
            # Dégradé bleu vers blanc
            factor = y / (self.height // 2)
            image[y, :, 0] = int(135 + 120 * factor)  # R
            image[y, :, 1] = int(206 + 49 * factor)   # G
            image[y, :, 2] = int(235 + 20 * factor)   # B
        
        # Montagnes en arrière-plan
        mountain_points = []
        for x in range(0, self.width, 10):
            y = self.height // 2 + int(50 * np.sin(x * 0.01) + 30 * np.sin(x * 0.03))
            mountain_points.append((x, y))
        
        # Remplissage des montagnes
        for i in range(len(mountain_points) - 1):
            x1, y1 = mountain_points[i]
            x2, y2 = mountain_points[i + 1]
            
            for y in range(y1, self.height):
                for x in range(x1, x2):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        # Couleur montagne
                        image[y, x] = [101, 67, 33]
        
        # Ajout de nuages
        for _ in range(15):
            cx = np.random.randint(100, self.width - 100)
            cy = np.random.randint(50, self.height // 3)
            radius = np.random.randint(30, 80)
            
            cv2.circle(image, (cx, cy), radius, (255, 255, 255), -1)
            cv2.circle(image, (cx + 20, cy - 10), radius // 2, (255, 255, 255), -1)
            cv2.circle(image, (cx - 15, cy + 5), radius // 3, (255, 255, 255), -1)
        
        # Ajout d'arbres
        for _ in range(20):
            x = np.random.randint(50, self.width - 50)
            y = np.random.randint(self.height // 2 + 50, self.height - 50)
            
            # Tronc
            cv2.rectangle(image, (x - 5, y), (x + 5, y + 40), (101, 67, 33), -1)
            
            # Feuillage (circles)
            cv2.circle(image, (x, y - 10), 20, (34, 139, 34), -1)
            cv2.circle(image, (x - 10, y - 5), 15, (34, 139, 34), -1)
            cv2.circle(image, (x + 10, y - 5), 15, (34, 139, 34), -1)
        
        # Ajout d'herbe/texture
        for y in range(self.height // 2 + 100, self.height):
            for x in range(self.width):
                if np.random.random() < 0.1:
                    image[y, x] = [34 + np.random.randint(-10, 10), 
                                  139 + np.random.randint(-20, 20), 
                                  34 + np.random.randint(-10, 10)]
        
        return image
    
    def create_portrait_photo(self) -> np.ndarray:
        """
        Crée un portrait photoréaliste
        """
        logger.info("Création portrait photoréaliste...")
        
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Fond flou (bokeh)
        for y in range(self.height):
            for x in range(self.width):
                # Couleurs de fond chaudes
                base_color = np.array([240, 220, 200])
                noise = np.random.randint(-30, 30, 3)
                image[y, x] = np.clip(base_color + noise, 0, 255)
        
        # Flou gaussien pour le fond
        image = cv2.GaussianBlur(image, (15, 15), 0)
        
        # Visage (ellipse)
        center_x, center_y = self.width // 2, self.height // 2
        
        # Création du visage
        mask = np.zeros((self.height, self.width), dtype=np.uint8)
        cv2.ellipse(mask, (center_x, center_y), (150, 200), 0, 0, 360, 255, -1)
        
        # Couleur de peau
        skin_color = np.array([255, 220, 177])
        for y in range(self.height):
            for x in range(self.width):
                if mask[y, x] > 0:
                    # Variation de couleur de peau
                    variation = np.random.randint(-15, 15, 3)
                    image[y, x] = np.clip(skin_color + variation, 0, 255)
        
        # Ajout d'ombres et lumière
        # Ombre sur le côté gauche
        shadow_mask = np.zeros((self.height, self.width), dtype=np.uint8)
        cv2.ellipse(shadow_mask, (center_x - 50, center_y), (100, 150), 0, 90, 270, 100, -1)
        
        for y in range(self.height):
            for x in range(self.width):
                if shadow_mask[y, x] > 0:
                    image[y, x] = image[y, x] * 0.7
        
        # Lumière sur le côté droit
        light_mask = np.zeros((self.height, self.width), dtype=np.uint8)
        cv2.ellipse(light_mask, (center_x + 50, center_y), (80, 120), 0, 270, 90, 80, -1)
        
        for y in range(self.height):
            for x in range(self.width):
                if light_mask[y, x] > 0:
                    image[y, x] = np.clip(image[y, x] * 1.2, 0, 255)
        
        # Yeux
        eye_y = center_y - 50
        # Oeil gauche
        cv2.circle(image, (center_x - 40, eye_y), 15, (255, 255, 255), -1)
        cv2.circle(image, (center_x - 40, eye_y), 8, (70, 130, 180), -1)
        cv2.circle(image, (center_x - 38, eye_y - 2), 3, (0, 0, 0), -1)
        
        # Oeil droit
        cv2.circle(image, (center_x + 40, eye_y), 15, (255, 255, 255), -1)
        cv2.circle(image, (center_x + 40, eye_y), 8, (70, 130, 180), -1)
        cv2.circle(image, (center_x + 42, eye_y - 2), 3, (0, 0, 0), -1)
        
        # Bouche
        mouth_y = center_y + 80
        cv2.ellipse(image, (center_x, mouth_y), (40, 20), 0, 0, 180, (200, 100, 100), -1)
        
        # Cheveux
        hair_points = []
        for x in range(center_x - 180, center_x + 180, 10):
            y = center_y - 180 + int(30 * np.sin(x * 0.02))
            hair_points.append((x, y))
        
        for i in range(len(hair_points) - 1):
            x1, y1 = hair_points[i]
            x2, y2 = hair_points[i + 1]
            cv2.line(image, (x1, y1), (x2, y2), (50, 30, 20), 8)
        
        # Texture cheveux
        for _ in range(500):
            x = np.random.randint(center_x - 180, center_x + 180)
            y = np.random.randint(center_y - 200, center_y - 100)
            if 0 <= x < self.width and 0 <= y < self.height:
                image[y, x] = [50 + np.random.randint(-10, 10), 
                              30 + np.random.randint(-5, 5), 
                              20 + np.random.randint(-5, 5)]
        
        return image
    
    def create_architecture_photo(self) -> np.ndarray:
        """
        Crée une photo d'architecture photoréaliste
        """
        logger.info("Création photo architecture...")
        
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Ciel
        for y in range(self.height // 3):
            factor = y / (self.height // 3)
            image[y, :, 0] = int(200 + 55 * factor)
            image[y, :, 1] = int(220 + 35 * factor)
            image[y, :, 2] = int(240 + 15 * factor)
        
        # Bâtiment principal
        building_x = self.width // 4
        building_y = self.height // 3
        building_w = self.width // 2
        building_h = self.height * 2 // 3
        
        # Structure du bâtiment
        cv2.rectangle(image, (building_x, building_y), 
                     (building_x + building_w, building_y + building_h), 
                     (180, 180, 190), -1)
        
        # Fenêtres
        window_rows = 8
        window_cols = 6
        window_w = building_w // (window_cols * 2)
        window_h = building_h // (window_rows * 2)
        
        for row in range(window_rows):
            for col in range(window_cols):
                x = building_x + col * (building_w // window_cols) + window_w // 2
                y = building_y + row * (building_h // window_rows) + window_h // 2
                
                # Cadre de fenêtre
                cv2.rectangle(image, (x, y), (x + window_w, y + window_h), (100, 100, 110), -1)
                # Verre (reflet)
                cv2.rectangle(image, (x + 2, y + 2), (x + window_w - 2, y + window_h - 2), 
                             (150, 180, 200), -1)
                # Reflet
                cv2.rectangle(image, (x + 2, y + 2), (x + window_w // 3, y + window_h // 3), 
                             (200, 220, 230), -1)
        
        # Porte
        door_x = building_x + building_w // 2 - 30
        door_y = building_y + building_h - 120
        cv2.rectangle(image, (door_x, door_y), (door_x + 60, door_y + 120), (80, 60, 40), -1)
        
        # Sol
        image[building_y + building_h:, :] = [120, 120, 130]
        
        # Ajout de texture au sol
        for y in range(building_y + building_h, self.height):
            for x in range(self.width):
                if np.random.random() < 0.05:
                    image[y, x] = [100 + np.random.randint(-20, 20), 
                                  100 + np.random.randint(-20, 20), 
                                  110 + np.random.randint(-20, 20)]
        
        # Ombres
        shadow_mask = np.zeros((self.height, self.width), dtype=np.uint8)
        cv2.rectangle(shadow_mask, (building_x + 20, building_y + building_h), 
                      (building_x + building_w + 20, self.height - 10), 100, -1)
        
        for y in range(self.height):
            for x in range(self.width):
                if shadow_mask[y, x] > 0:
                    image[y, x] = image[y, x] * 0.6
        
        # Nuages
        for _ in range(8):
            cx = np.random.randint(100, self.width - 100)
            cy = np.random.randint(30, self.height // 4)
            radius = np.random.randint(40, 80)
            
            cv2.circle(image, (cx, cy), radius, (255, 255, 255), -1)
            cv2.circle(image, (cx + 25, cy - 10), radius // 2, (255, 255, 255), -1)
            cv2.circle(image, (cx - 20, cy + 8), radius // 3, (255, 255, 255), -1)
        
        return image
    
    def create_macro_photography(self) -> np.ndarray:
        """
        Crée une photo macro photoréaliste (fleur/insecte)
        """
        logger.info("Création photo macro...")
        
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Fond très flou (bokeh extrême)
        for y in range(self.height):
            for x in range(self.width):
                # Couleurs de fond vertes
                base_color = np.array([50, 150, 50])
                noise = np.random.randint(-40, 40, 3)
                image[y, x] = np.clip(base_color + noise, 0, 255)
        
        # Flou extrême pour le fond
        image = cv2.GaussianBlur(image, (25, 25), 0)
        
        # Fleur principale au centre
        center_x, center_y = self.width // 2, self.height // 2
        
        # Pétales
        num_petals = 12
        petal_length = 80
        petal_width = 30
        
        for i in range(num_petals):
            angle = (2 * np.pi * i) / num_petals
            
            # Coordonnées du pétale
            for j in range(petal_length):
                x = int(center_x + j * np.cos(angle))
                y = int(center_y + j * np.sin(angle))
                
                # Largeur du pétale
                width_factor = 1 - (j / petal_length) * 0.5
                current_width = int(petal_width * width_factor)
                
                for k in range(-current_width // 2, current_width // 2):
                    px = x + int(k * np.sin(angle))
                    py = y - int(k * np.cos(angle))
                    
                    if 0 <= px < self.width and 0 <= py < self.height:
                        # Couleur rose avec variation
                        base_petal = np.array([255, 182, 193])
                        variation = np.random.randint(-20, 20, 3)
                        image[py, px] = np.clip(base_petal + variation, 0, 255)
        
        # Centre de la fleur
        cv2.circle(image, (center_x, center_y), 25, (255, 220, 100), -1)
        
        # Texture du centre (pollen)
        for _ in range(200):
            x = center_x + np.random.randint(-20, 20)
            y = center_y + np.random.randint(-20, 20)
            if 0 <= x < self.width and 0 <= y < self.height:
                image[y, x] = [200 + np.random.randint(-30, 30), 
                              180 + np.random.randint(-30, 30), 
                              50 + np.random.randint(-20, 20)]
        
        # Gouttes de rosée
        for _ in range(15):
            x = np.random.randint(center_x - 100, center_x + 100)
            y = np.random.randint(center_y - 100, center_y + 100)
            
            # Goutte avec reflet
            cv2.circle(image, (x, y), 3, (200, 220, 255), -1)
            cv2.circle(image, (x - 1, y - 1), 1, (255, 255, 255), -1)
        
        # Feuilles
        for i in range(3):
            leaf_x = center_x + np.random.randint(-150, 150)
            leaf_y = center_y + np.random.randint(-100, 100)
            
            # Forme de feuille (ellipse)
            cv2.ellipse(image, (leaf_x, leaf_y), (40, 15), 
                       np.random.randint(-45, 45), 0, 360, (34, 139, 34), -1)
            
            # Veine centrale
            cv2.line(image, (leaf_x - 40, leaf_y), (leaf_x + 40, leaf_y), (20, 100, 20), 2)
        
        return image
    
    def create_night_scene(self) -> np.ndarray:
        """
        Crée une scène de nuit photoréaliste
        """
        logger.info("Création scène de nuit...")
        
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Ciel nocturne
        for y in range(self.height):
            for x in range(self.width):
                # Dégradé bleu nuit
                factor = y / self.height
                image[y, x, 0] = int(10 + 20 * factor)  # R
                image[y, x, 1] = int(10 + 30 * factor)  # G
                image[y, x, 2] = int(30 + 60 * factor)  # B
        
        # Étoiles
        for _ in range(200):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height // 2)
            brightness = np.random.randint(150, 255)
            image[y, x] = [brightness, brightness, brightness]
        
        # Lune
        moon_x, moon_y = self.width - 150, 100
        cv2.circle(image, (moon_x, moon_y), 40, (240, 240, 220), -1)
        
        # Cratères de lune
        for _ in range(8):
            crater_x = moon_x + np.random.randint(-30, 30)
            crater_y = moon_y + np.random.randint(-30, 30)
            cv2.circle(image, (crater_x, crater_y), 3, (220, 220, 200), -1)
        
        # Bâtiments en silhouette
        buildings = [
            (100, 400, 150, 600),
            (200, 350, 250, 600),
            (300, 380, 340, 600),
            (400, 320, 450, 600),
            (500, 360, 540, 600),
            (600, 340, 640, 600),
        ]
        
        for x1, y1, x2, y2 in buildings:
            cv2.rectangle(image, (x1, y1), (x2, y2), (20, 20, 30), -1)
            
            # Fenêtres éclairées
            for floor in range(y1, y2 - 40, 40):
                for window in range(x1 + 10, x2 - 10, 20):
                    if np.random.random() < 0.7:  # 70% des fenêtres allumées
                        cv2.rectangle(image, (window, floor), (window + 15, floor + 25), 
                                     (255, 220, 150), -1)
        
        # Rue
        image[550:, :] = [40, 40, 50]
        
        # Lumières de rue
        for x in range(50, self.width, 150):
            cv2.rectangle(image, (x - 2, 400), (x + 2, 550), (255, 255, 200), -1)
            
            # Halo de lumière
            for radius in range(10, 30, 5):
                alpha = 50 - radius
                cv2.circle(image, (x, 400), radius, (255, 255, 200), alpha)
        
        # Voiture avec phares
        car_x, car_y = 300, 520
        cv2.rectangle(image, (car_x - 30, car_y - 10), (car_x + 30, car_y + 10), 
                     (100, 100, 120), -1)
        
        # Phares de voiture
        # Phare gauche
        for i in range(50):
            x = car_x - 30 - i
            y = car_y
            if x >= 0:
                brightness = 255 - i * 4
                cv2.circle(image, (x, y), 3, (brightness, brightness, 200), -1)
        
        # Phare droit
        for i in range(50):
            x = car_x + 30 + i
            y = car_y
            if x < self.width:
                brightness = 255 - i * 4
                cv2.circle(image, (x, y), 3, (brightness, brightness, 200), -1)
        
        return image


def test_photorealistic_compression():
    """
    Test de compression sur images photoréalistes
    """
    logger.info("DÉBUT TEST COMPRESSION PHOTORÉALISTE")
    
    # Création du générateur
    generator = PhotorealisticImageGenerator()
    
    # Création des images photoréalistes
    images = {
        'landscape_natural': generator.create_natural_landscape(),
        'portrait_photo': generator.create_portrait_photo(),
        'architecture_photo': generator.create_architecture_photo(),
        'macro_photography': generator.create_macro_photography(),
        'night_scene': generator.create_night_scene()
    }
    
    # Sauvegarde des images originales
    original_files = {}
    for name, image in images.items():
        filename = f"{name}.png"
        cv2.imwrite(filename, image)
        original_files[name] = filename
        logger.info(f"Image sauvegardée: {filename}")
    
    # Test de compression pour chaque niveau de qualité
    quality_levels = ['lossless', 'high', 'medium', 'low']
    all_results = {}
    
    for quality in quality_levels:
        logger.info(f"\nTest qualité: {quality.upper()}")
        
        # Création du compresseur
        compressor = SDILikeImageCompressor(quality)
        
        results = []
        
        for name, image_path in original_files.items():
            output_path = f"compressed_{quality}_{name}.sdi-img"
            
            try:
                metrics = compressor.save_compressed_image(image_path, output_path)
                results.append(metrics)
                
                logger.info(f"  {name}: {metrics['compression_ratio']:.2f}:1")
                
            except Exception as e:
                logger.error(f"  Erreur compression {name}: {e}")
                continue
        
        # Calcul des statistiques
        if results:
            total_original = sum(r['original_size'] for r in results)
            total_compressed = sum(r['compressed_size'] for r in results)
            avg_ratio = total_original / max(1, total_compressed)
            avg_time = sum(r['total_compression_time'] for r in results) / len(results)
            
            print(f"\n" + "="*60)
            print(f"RÉSULTATS - QUALITÉ {quality.upper()} - PHOTORÉALISTE")
            print("="*60)
            print(f"Images traitées: {len(results)}")
            print(f"Taille originale: {total_original / (1024*1024):.2f} MB")
            print(f"Taille compressée: {total_compressed / (1024*1024):.2f} MB")
            print(f"Ratio moyen: {avg_ratio:.2f}:1")
            print(f"Économie: {(1 - 1/avg_ratio) * 100:.1f}%")
            print(f"Temps moyen: {avg_time:.3f}s")
            
            # Détails par image
            print(f"\nDÉTAILS PAR IMAGE:")
            for i, result in enumerate(results):
                img_name = original_files[list(original_files.keys())[i]]
                print(f"  {img_name}: {result['compression_ratio']:.2f}:1")
            
            print("="*60)
            
            all_results[quality] = {
                'quality': quality,
                'results': results,
                'summary': {
                    'total_images': len(results),
                    'total_original_size': total_original,
                    'total_compressed_size': total_compressed,
                    'average_ratio': avg_ratio,
                    'average_time': avg_time
                }
            }
            
            # Sauvegarde des métriques
            with open(f"photorealistic_metrics_{quality}.json", "w") as f:
                json.dump(all_results[quality], f, indent=2, default=str)
    
    # Comparaison globale
    print(f"\n" + "="*80)
    print("COMPARAISON GLOBALE - IMAGES PHOTORÉALISTES")
    print("="*80)
    
    for quality, data in all_results.items():
        summary = data['summary']
        print(f"{quality.upper():10}: {summary['average_ratio']:6.2f}:1 | "
              f"Économie: {(1 - 1/summary['average_ratio']) * 100:5.1f}% | "
              f"Temps: {summary['average_time']:6.3f}s")
    
    print("="*80)
    
    return all_results


if __name__ == "__main__":
    test_photorealistic_compression()
