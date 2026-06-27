#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
from PIL import Image
import io
import base64

image_path = 'f:/FINAL/DEFINITIF/hcs_v2-P3/test_image.png'

# Verifier la taille originale
orig = Image.open(image_path)
print(f"Image originale: {orig.width} x {orig.height} px")

# Envoyer a l'API upscale
with open(image_path, 'rb') as f:
    files = {'file': ('test_image.png', f, 'image/png')}
    data = {'scale_factor': '2x', 'energy_level': 'standard'}
    response = requests.post('http://localhost:8009/api/v2/upscale/image', files=files, data=data, timeout=60)

print(f"HTTP Status: {response.status_code}")
result = response.json()

# Utiliser les bonnes cles
original_shape = result.get('original_shape')
target_shape = result.get('target_shape')
upscale_factor = result.get('upscale_factor')
quality_metrics = result.get('quality_metrics', {})
processing_time = result.get('processing_time', 0)

print(f"Success: {result.get('success')}")
print(f"Shape originale: {original_shape}")
print(f"Shape cible: {target_shape}")
print(f"Facteur d'upscale: {upscale_factor}")
print(f"Temps de traitement: {processing_time:.3f}s")
print(f"Metriques qualite: {quality_metrics}")

# Verifier l'image upscalee
if result.get('upscaled_image_base64'):
    img_data = base64.b64decode(result['upscaled_image_base64'])
    img = Image.open(io.BytesIO(img_data))
    print(f"\nDimensions image retournee: {img.width} x {img.height} px")
    
    # Sauvegarder pour comparaison visuelle
    img.save('f:/FINAL/DEFINITIF/hcs_v2-P3/test_upscaled_result.png')
    print(f"Image sauvegardee: test_upscaled_result.png")
    
    # Verifier l'upscale reel
    ratio_w = img.width / orig.width
    ratio_h = img.height / orig.height
    print(f"Ratio effectif: {ratio_w:.2f}x (largeur), {ratio_h:.2f}x (hauteur)")
    
    if img.width > orig.width and img.height > orig.height:
        print(f"\n>>> UPSCALE CONFIRME: {orig.width}x{orig.height} --> {img.width}x{img.height} <<<")
    else:
        print(f"\n>>> PROBLEME: image non upscalee! {orig.width}x{orig.height} --> {img.width}x{img.height} <<<")
else:
    print("Pas d'image base64 dans la reponse")
    print(f"Cles disponibles: {list(result.keys())}")
