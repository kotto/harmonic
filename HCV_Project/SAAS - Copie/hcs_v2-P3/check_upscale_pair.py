#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np
import hashlib

pairs = [
    ('test_original.png', 'test_api_upscaled.png'),
    ('hcs_source.png', 'hcs_upscale_2.0x.png'),
]

for orig_name, up_name in pairs:
    try:
        orig = Image.open(orig_name).convert('RGB')
        up = Image.open(up_name).convert('RGB')
        
        hash_orig = hashlib.md5(np.array(orig).tobytes()).hexdigest()[:8]
        hash_up = hashlib.md5(np.array(up).tobytes()).hexdigest()[:8]
        
        ratio_w = up.width / orig.width
        ratio_h = up.height / orig.height
        
        print(f"--- Paire: {orig_name} vs {up_name} ---")
        print(f"  Original: {orig.width}x{orig.height}px  hash={hash_orig}")
        print(f"  Upscale:  {up.width}x{up.height}px  hash={hash_up}")
        print(f"  Ratio:    {ratio_w:.2f}x / {ratio_h:.2f}x")
        print(f"  Fichiers identiques: {hash_orig == hash_up}")
        print(f"  Upscale reel: {up.width > orig.width}")
        print()
    except Exception as e:
        print(f"Erreur {orig_name}/{up_name}: {e}")
        print()

# Tester maintenant avec hcs_source.png en envoyant a l'API
import requests, base64, io

print("--- Test API live avec hcs_source.png ---")
with open('hcs_source.png', 'rb') as f:
    files = {'file': ('hcs_source.png', f, 'image/png')}
    data = {'scale_factor': '2x', 'energy_level': 'standard'}
    response = requests.post('http://localhost:8009/api/v2/upscale/image', files=files, data=data, timeout=60)

result = response.json()
print(f"Success: {result.get('success')}")
print(f"Shape originale: {result.get('original_shape')}")
print(f"Shape cible:     {result.get('target_shape')}")
print(f"Facteur:         {result.get('upscale_factor')}")

if result.get('upscaled_image_base64'):
    img_data = base64.b64decode(result['upscaled_image_base64'])
    api_result = Image.open(io.BytesIO(img_data)).convert('RGB')
    source = Image.open('hcs_source.png').convert('RGB')
    
    hash_src = hashlib.md5(np.array(source).tobytes()).hexdigest()[:8]
    hash_res = hashlib.md5(np.array(api_result).tobytes()).hexdigest()[:8]
    
    print(f"Source:   {source.width}x{source.height}  hash={hash_src}")
    print(f"Resultat: {api_result.width}x{api_result.height}  hash={hash_res}")
    print(f"Images identiques: {hash_src == hash_res}")
    
    # Sauvegarder la paire pour comparaison visuelle
    api_result.save('hcs_upscale_api_result.png')
    print(f"Image sauvegardee: hcs_upscale_api_result.png")
    
    if api_result.width > source.width:
        print(f"\n>>> UPSCALE CONFIRME: {source.width}x{source.height} --> {api_result.width}x{api_result.height} (diff content: {hash_src != hash_res}) <<<")
    else:
        print(f"\n>>> PROBLEME: pas d'upscale detecte <<<")
