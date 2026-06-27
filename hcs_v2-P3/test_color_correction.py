#!/usr/bin/env python3
"""
Test de correction des couleurs pour l'upscaling quantique-harmonique
"""

import numpy as np
import cv2
from PIL import Image
import io
import base64
import sys
import os

# Ajout des chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_color_conversion():
    """Test la conversion des couleurs"""
    print("🎨 Test de conversion des couleurs")
    print("=" * 50)
    
    # Créer une image test avec des couleurs distinctes
    h, w = 200, 200
    test_image = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Créer des zones de couleurs distinctes
    test_image[0:100, 0:100] = [255, 0, 0]    # Rouge
    test_image[0:100, 100:200] = [0, 255, 0]  # Vert  
    test_image[100:200, 0:100] = [0, 0, 255]  # Bleu
    test_image[100:200, 100:200] = [255, 255, 0]  # Jaune
    
    print("Image originale créée avec:")
    print("- Zone 1: Rouge [255, 0, 0]")
    print("- Zone 2: Vert [0, 255, 0]")  
    print("- Zone 3: Bleu [0, 0, 255]")
    print("- Zone 4: Jaune [255, 255, 0]")
    
    # Sauvegarder l'original
    cv2.imwrite('test_original.png', test_image)
    print("✅ Image originale sauvegardée: test_original.png")
    
    # Convertir en PIL et revenir
    pil_image = Image.fromarray(test_image)
    pil_array = np.array(pil_image)
    cv2.imwrite('test_pil_roundtrip.png', pil_array)
    print("✅ Test PIL roundtrip: test_pil_roundtrip.png")
    
    # Test conversion BGR/RGB
    bgr_image = cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR)
    rgb_back = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    cv2.imwrite('test_bgr_rgb_conversion.png', rgb_back)
    print("✅ Test BGR/RGB conversion: test_bgr_rgb_conversion.png")
    
    # Vérifier les couleurs
    print("\n🔍 Vérification des couleurs:")
    zones = [
        ("Rouge original", test_image[50, 50]),
        ("Vert original", test_image[50, 150]),
        ("Bleu original", test_image[150, 50]),
        ("Jaune original", test_image[150, 150]),
        ("Rouge PIL", pil_array[50, 50]),
        ("Vert PIL", pil_array[50, 150]),
        ("Bleu PIL", pil_array[150, 50]),
        ("Jaune PIL", pil_array[150, 150]),
        ("Rouge BGR/RGB", rgb_back[50, 50]),
        ("Vert BGR/RGB", rgb_back[50, 150]),
        ("Bleu BGR/RGB", rgb_back[150, 50]),
        ("Jaune BGR/RGB", rgb_back[150, 150]),
    ]
    
    for name, color in zones:
        print(f"  {name}: {color}")
    
    return test_image

def test_upscaler_colors():
    """Test l'upscaler avec l'image de couleurs"""
    print("\n🌊 Test de l'upscaler avec couleurs")
    print("=" * 50)
    
    try:
        from core.harmonic_upscaler import harmonic_upscaler_api
        
        # Créer l'image test
        test_image = test_color_conversion()
        
        # Tester l'upscaling
        result = harmonic_upscaler_api.upscale_image(
            image_array=test_image,
            factor='2x',
            energy_level='standard'
        )
        
        if result['success']:
            # Décoder l'image retournée
            img_data = base64.b64decode(result['upscaled_image_base64'])
            nparr = np.frombuffer(img_data, np.uint8)
            upscaled = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            cv2.imwrite('test_upscaled_colors.png', upscaled)
            print("✅ Image upscalée sauvegardée: test_upscaled_colors.png")
            
            # Vérifier les couleurs dans l'image upscalée
            print("\n🔍 Couleurs dans l'image upscalée:")
            zones_upscaled = [
                ("Rouge upscalé", upscaled[100, 100]),
                ("Vert upscalé", upscaled[100, 300]),
                ("Bleu upscalé", upscaled[300, 100]),
                ("Jaune upscalé", upscaled[300, 300]),
            ]
            
            for name, color in zones_upscaled:
                print(f"  {name}: {color}")
            
            print(f"\n📊 Résultat upscaling:")
            print(f"   Taille: {test_image.shape} → {result['target_shape']}")
            print(f"   Niveau: {result['reality_level_used']}")
            print(f"   PSNR: {result['quality_metrics']['psnr']:.1f} dB")
            
        else:
            print(f"❌ Erreur upscaling: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")

def test_api_colors():
    """Test l'API avec les couleurs"""
    print("\n🌐 Test de l'API avec couleurs")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # Créer l'image test
        test_image = test_color_conversion()
        
        # Convertir en bytes pour l'API
        _, buffer = cv2.imencode('.png', test_image)
        img_bytes = buffer.tobytes()
        
        # Envoyer à l'API
        files = {'file': ('test_colors.png', img_bytes, 'image/png')}
        data = {
            'factor': '2x',
            'energy_level': 'standard'
        }
        
        response = requests.post('http://localhost:8008/api/v2/upscale/image', 
                           files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            
            if result['success']:
                # Sauvegarder le résultat
                img_data = base64.b64decode(result['upscaled_image_base64'])
                with open('test_api_upscaled.png', 'wb') as f:
                    f.write(img_data)
                print("✅ Image API upscalée sauvegardée: test_api_upscaled.png")
                
                print(f"\n📊 Résultat API:")
                print(f"   Taille: {result['original_shape']} → {result['target_shape']}")
                print(f"   Niveau: {result['reality_level_used']}")
                print(f"   PSNR: {result['quality_metrics']['psnr']:.1f} dB")
                
            else:
                print(f"❌ Erreur API: {result.get('error')}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Erreur test API: {e}")

if __name__ == "__main__":
    print("🚀 TEST DE CORRECTION DES COULEURS")
    print("Test du problème de conversion RGB/BGR dans l'upscaling")
    print("=" * 70)
    
    # Test 1: Conversion de base
    test_color_conversion()
    
    # Test 2: Upscaler direct
    test_upscaler_colors()
    
    # Test 3: API complète
    test_api_colors()
    
    print("\n🎉 Tests terminés!")
    print("Vérifiez les fichiers PNG générés pour valider les couleurs")
