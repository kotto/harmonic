#!/usr/bin/env python3
"""
DÉBOGAGE DE LA RECONSTRUCTION D'IMAGE
Diagnostic du problème d'image noire
"""

import numpy as np
import cv2
from PIL import Image
import io
import base64

def test_image_reconstruction():
    """Test de la fonction de reconstruction d'image"""
    
    print("=== DÉBOGAGE RECONSTRUCTION IMAGE ===")
    
    # Test 1: Image de base
    print("\n1. Test image de base (400x600)")
    base_image = np.zeros((600, 400, 3), dtype=np.uint8)
    
    # Ajout d'un motif simple
    for y in range(0, 600, 50):
        for x in range(0, 400, 50):
            if (x // 50 + y // 50) % 2 == 0:
                base_image[y:y+50, x:x+50] = [100, 150, 200]
            else:
                base_image[y:y+50, x:x+50] = [200, 150, 100]
    
    # Ajout de texte
    cv2.putText(base_image, "TEST IMAGE", (50, 300), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    
    print(f"Image base shape: {base_image.shape}")
    print(f"Image base dtype: {base_image.dtype}")
    print(f"Valeurs uniques: {np.unique(base_image)}")
    
    # Test 2: Conversion en base64
    print("\n2. Test conversion base64")
    try:
        pil_image = Image.fromarray(base_image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_string}"
        print(f"Base64 conversion: SUCCESS ({len(base64_string)} chars)")
        print(f"Data URL: {data_url[:50]}...")
    except Exception as e:
        print(f"Base64 conversion ERROR: {e}")
        return
    
    # Test 3: Sauvegarde et rechargement
    print("\n3. Test sauvegarde/rechargement")
    try:
        cv2.imwrite('debug_test_image.png', base_image)
        reloaded = cv2.imread('debug_test_image.png')
        print(f"Reloaded shape: {reloaded.shape}")
        print(f"Reloaded dtype: {reloaded.dtype}")
        print(f"Values match: {np.array_equal(base_image, reloaded)}")
    except Exception as e:
        print(f"Save/reload ERROR: {e}")
    
    # Test 4: Simulation des métadonnées
    print("\n4. Test avec métadonnées simulées")
    metadata = {
        'quality': 'high',
        'width': 400,
        'height': 600,
        'compression_zones': [{'complexity': 0.5}]
    }
    
    # Test 5: Reconstruction avec différentes approches
    print("\n5. Test reconstruction approches")
    
    # Approche 1: Image simple avec motif
    simple_image = np.full((600, 400, 3), [80, 80, 80], dtype=np.uint8)
    cv2.putText(simple_image, "SDI-IMG", (100, 250), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    cv2.putText(simple_image, "Compressed", (100, 300), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    
    # Approche 2: Image avec dégradé
    gradient_image = np.zeros((600, 400, 3), dtype=np.uint8)
    for y in range(600):
        for x in range(400):
            gradient_image[y, x] = [
                min(255, int(128 + x * 0.3)),
                min(255, int(128 + y * 0.2)),
                min(255, int(128 + (x + y) * 0.1))
            ]
    
    cv2.putText(gradient_image, "SDI-IMG Preview", (50, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Approche 3: Image avec pattern basé sur métadonnées
    complexity = metadata.get('compression_zones', [{}])[0].get('complexity', 0.5)
    pattern_image = np.zeros((600, 400, 3), dtype=np.uint8)
    
    for y in range(600):
        for x in range(400):
            # Pattern basé sur la complexité
            base_val = int(128 + complexity * 50)
            variation = int((x + y) * complexity * 0.1) % 50
            
            pattern_image[y, x] = [
                min(255, base_val + variation),
                min(255, base_val),
                min(255, base_val - variation // 2)
            ]
    
    cv2.putText(pattern_image, "SDI-IMG", (150, 280), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
    cv2.putText(pattern_image, f"Complexity: {complexity:.2f}", (100, 320), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Test 6: Conversion de toutes les approches en base64
    print("\n6. Test conversion toutes approches")
    approaches = [
        ("Base", base_image),
        ("Simple", simple_image),
        ("Gradient", gradient_image),
        ("Pattern", pattern_image)
    ]
    
    for name, img in approaches:
        try:
            pil_img = Image.fromarray(img)
            buffer = io.BytesIO()
            pil_img.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()
            base64_str = base64.b64encode(img_bytes).decode('utf-8')
            print(f"{name:10}: SUCCESS ({len(base64_str)} chars)")
            
            # Sauvegarde pour vérification visuelle
            cv2.imwrite(f'debug_{name.lower()}_image.png', img)
            
        except Exception as e:
            print(f"{name:10}: ERROR - {e}")
    
    print("\n=== FIN DÉBOGAGE ===")
    print("Images de debug sauvegardées:")
    print("- debug_test_image.png")
    print("- debug_base_image.png")
    print("- debug_simple_image.png")
    print("- debug_gradient_image.png")
    print("- debug_pattern_image.png")

if __name__ == "__main__":
    test_image_reconstruction()
