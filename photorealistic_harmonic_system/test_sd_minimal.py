#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST RAPIDE STABLE DIFFUSION
===========================

Test minimal pour vérifier fonctionnalité SD.

@author: K.A. (KA Method)
"""

import sys
from pathlib import Path
import time

# Test importations
print("🔍 TEST IMPORTATIONS STABLE DIFFUSION")
print("=" * 50)

try:
    print("1️⃣ Test diffusers...")
    import diffusers
    print(f"   ✅ diffusers: {diffusers.__version__}")
except ImportError as e:
    print(f"   ❌ diffusers: {e}")
    diffusers = None

try:
    print("2️⃣ Test transformers...")
    import transformers
    print(f"   ✅ transformers: {transformers.__version__}")
except ImportError as e:
    print(f"   ❌ transformers: {e}")
    transformers = None

try:
    print("3️⃣ Test torch...")
    import torch
    print(f"   ✅ torch: {torch.__version__}")
    print(f"   🔧 CUDA disponible: {torch.cuda.is_available()}")
except ImportError as e:
    print(f"   ❌ torch: {e}")
    torch = None

# Test pipeline minimal
if diffusers and torch:
    print("\n🎨 TEST PIPELINE MINIMAL")
    print("=" * 30)
    
    try:
        from diffusers import StableDiffusionPipeline
        
        print("   🔄 Chargement pipeline (petit modèle)...")
        
        # Utilisation modèle léger pour test
        pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            safety_checker=None,  # Désactivation pour rapidité
            requires_safety_checker=False
        )
        
        print("   ✅ Pipeline chargé")
        
        # Test génération rapide
        print("   🎨 Test génération rapide...")
        prompt = "a beautiful landscape"
        
        # Réduction paramètres pour test rapide
        image = pipe(
            prompt,
            num_inference_steps=10,  # Moins d'étapes
            guidance_scale=7.5,
            height=256,  # Petite résolution
            width=256
        ).images[0]
        
        # Sauvegarde test
        test_path = Path("E:/photorealistic_harmonic_system/test_photo.png")
        image.save(test_path)
        print(f"   ✅ Image test sauvegardée: {test_path}")
        
    except Exception as e:
        print(f"   ❌ Erreur pipeline: {e}")
else:
    print("\n⚠️  Dépendances manquantes - installation nécessaire")

print("\n🏁 TEST TERMINÉ")