#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST INTEGRATION SDXL HARMONIQUE - Validation Complète
========================================================
Script de test pour valider l'intégration SDXL + HCV PRO
avec génération d'images et vidéos de haute qualité.
"""

import os
import sys
import time
import numpy as np
import logging
from pathlib import Path

# Ajout du chemin courant
sys.path.insert(0, str(Path(__file__).parent))

from integration_sdxl_harmonic import SDXLHarmonicIntegrator, GenerationConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_image_generation():
    """Test la génération d'images avec différentes configurations"""
    print("🎨 TEST GÉNÉRATION D'IMAGES")
    print("=" * 40)
    
    integrator = SDXLHarmonicIntegrator()
    
    # Configurations de test
    test_configs = [
        {
            "name": "Portrait 4K",
            "prompt": "beautiful harmonic portrait of a woman, golden ratio proportions, cinematic lighting, ultra detailed",
            "target_resolution": "4k",
            "upscale_factor": 2.0,
            "energy_level": "quantum"
        },
        {
            "name": "Paysage 8K",
            "prompt": "epic harmonic landscape with phi spirals, mountain ranges, golden hour lighting, 8k resolution",
            "target_resolution": "8k", 
            "upscale_factor": 4.0,
            "energy_level": "ultra"
        },
        {
            "name": "Art Abstrait",
            "prompt": "harmonic abstract art with sacred geometry, fibonacci patterns, vibrant colors, mathematical precision",
            "target_resolution": "2k",
            "upscale_factor": 1.5,
            "energy_level": "high"
        }
    ]
    
    results = []
    
    for i, test_cfg in enumerate(test_configs, 1):
        print(f"\n🎯 Test {i}/3: {test_cfg['name']}")
        print(f"📝 Prompt: {test_cfg['prompt']}")
        
        config = GenerationConfig(
            prompt=test_cfg["prompt"],
            negative_prompt="blurry, low quality, distorted, ugly",
            width=1024,
            height=1024,
            num_inference_steps=15,
            guidance_scale=7.5,
            target_resolution=test_cfg["target_resolution"],
            upscale_factor=test_cfg["upscale_factor"],
            energy_level=test_cfg["energy_level"],
            upload_to_s3=True
        )
        
        start_time = time.time()
        result = integrator.generate_image_harmonic(config)
        duration = time.time() - start_time
        
        if result["success"]:
            print(f"✅ Succès en {duration:.2f}s")
            print(f"📐 Résolution: {result.get('upscaled_image')}")
            print(f"📦 Compression: {result.get('compression_ratio', 'N/A')}:1")
            print(f"☁️ Upload: {'✅' if result.get('s3_url') else '❌'}")
            
            results.append({
                "test": test_cfg["name"],
                "success": True,
                "duration_s": duration,
                "compression_ratio": result.get('compression_ratio'),
                "s3_uploaded": result.get('s3_url') is not None
            })
        else:
            print(f"❌ Erreur: {result.get('error')}")
            results.append({
                "test": test_cfg["name"],
                "success": False,
                "error": result.get('error'),
                "duration_s": duration
            })
    
    return results

def test_video_generation():
    """Test la génération de vidéos longues"""
    print("\n🎬 TEST GÉNÉRATION DE VIDÉOS")
    print("=" * 40)
    
    integrator = SDXLHarmonicIntegrator()
    
    # Configurations vidéo de test
    video_configs = [
        {
            "name": "Vidéo Courte 4K",
            "prompt": "harmonic animation of golden ratio spirals, flowing energy, 4k quality",
            "n_frames": 24,
            "fps": 24.0,
            "target_resolution": "4k",
            "energy_level": "quantum"
        },
        {
            "name": "Vidéo Longue 2K",
            "prompt": "journey through harmonic dimensions, sacred geometry evolution, cinematic",
            "n_frames": 120,  # 5 secondes à 24fps
            "fps": 24.0,
            "target_resolution": "2k",
            "energy_level": "high"
        },
        {
            "name": "Vidéo Ultra-Longue 1080p",
            "prompt": "time-lapse of harmonic patterns forming and dissolving, mathematical beauty",
            "n_frames": 240,  # 10 secondes à 24fps
            "fps": 24.0,
            "target_resolution": "1080p",
            "energy_level": "standard"
        }
    ]
    
    results = []
    
    for i, test_cfg in enumerate(video_configs, 1):
        print(f"\n🎬 Test {i}/3: {test_cfg['name']}")
        print(f"📝 Prompt: {test_cfg['prompt']}")
        print(f"🎬 Frames: {test_cfg['n_frames']} @ {test_cfg['fps']}fps")
        
        config = GenerationConfig(
            prompt=test_cfg["prompt"],
            negative_prompt="blurry, low quality, flickering, inconsistent",
            width=1024,
            height=1024,
            n_frames=test_cfg["n_frames"],
            fps=test_cfg["fps"],
            target_resolution=test_cfg["target_resolution"],
            energy_level=test_cfg["energy_level"],
            upload_to_s3=True
        )
        
        start_time = time.time()
        result = integrator.generate_video_harmonic(config)
        duration = time.time() - start_time
        
        if result["success"]:
            print(f"✅ Succès en {duration:.2f}s")
            print(f"🎬 Frames: {result.get('n_frames')}")
            print(f"📦 Compression moyenne: {result.get('avg_compression_ratio', 0):.2f}:1")
            print(f"☁️ Upload: {'✅' if result.get('s3_url') else '❌'}")
            
            results.append({
                "test": test_cfg["name"],
                "success": True,
                "duration_s": duration,
                "n_frames": result.get('n_frames'),
                "compression_ratio": result.get('avg_compression_ratio'),
                "s3_uploaded": result.get('s3_url') is not None
            })
        else:
            print(f"❌ Erreur: {result.get('error')}")
            results.append({
                "test": test_cfg["name"],
                "success": False,
                "error": result.get('error'),
                "duration_s": duration
            })
    
    return results

def test_system_integration():
    """Test l'intégration complète du système"""
    print("\n🔧 TEST INTÉGRATION SYSTÈME")
    print("=" * 40)
    
    integrator = SDXLHarmonicIntegrator()
    status = integrator.get_system_status()
    
    print("📊 Statut des composants:")
    for component, available in status["components"].items():
        status_icon = "✅" if available else "❌"
        print(f"  {status_icon} {component}: {'Disponible' if available else 'Indisponible'}")
    
    print(f"\n🌐 Disponibilités globales:")
    print(f"  SDXL: {'✅' if status['sdxl_available'] else '❌'}")
    print(f"  Harmonique: {'✅' if status['harmonic_available'] else '❌'}")
    print(f"  HCV PRO: {'✅' if status['hcv_available'] else '❌'}")
    print(f"  S3: {'✅' if status['s3_available'] else '❌'}")
    
    # Test de compatibilité
    all_available = all([
        status['sdxl_available'],
        status['harmonic_available'], 
        status['hcv_available'],
        status['s3_available']
    ])
    
    if all_available:
        print("\n🏆 SYSTÈME COMPLET - Tous les composants disponibles!")
        return True
    else:
        print("\n⚠️ SYSTÈME PARTIEL - Certains composants manquent")
        return False

def generate_report(image_results, video_results, system_ok):
    """Génère un rapport de test"""
    report = {
        "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system_status": {
            "all_components_available": system_ok,
            "integration_ready": system_ok
        },
        "image_tests": {
            "total_tests": len(image_results),
            "successful_tests": sum(1 for r in image_results if r["success"]),
            "success_rate": sum(1 for r in image_results if r["success"]) / len(image_results) if image_results else 0,
            "avg_duration_s": np.mean([r["duration_s"] for r in image_results if "duration_s" in r]) if image_results else 0,
            "avg_compression_ratio": np.mean([r["compression_ratio"] for r in image_results if r.get("compression_ratio")]) if image_results else 0,
            "s3_upload_success_rate": sum(1 for r in image_results if r.get("s3_uploaded")) / len(image_results) if image_results else 0
        },
        "video_tests": {
            "total_tests": len(video_results),
            "successful_tests": sum(1 for r in video_results if r["success"]),
            "success_rate": sum(1 for r in video_results if r["success"]) / len(video_results) if video_results else 0,
            "avg_duration_s": np.mean([r["duration_s"] for r in video_results if "duration_s" in r]) if video_results else 0,
            "avg_compression_ratio": np.mean([r["compression_ratio"] for r in video_results if r.get("compression_ratio")]) if video_results else 0,
            "total_frames_generated": sum(r["n_frames"] for r in video_results if r.get("n_frames")) if video_results else 0,
            "s3_upload_success_rate": sum(1 for r in video_results if r.get("s3_uploaded")) / len(video_results) if video_results else 0
        }
    }
    
    # Sauvegarde du rapport
    report_path = "test_integration_sdxl_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Rapport sauvegardé: {report_path}")
    return report

def main():
    """Fonction principale de test"""
    print("🧪 TEST COMPLET INTÉGRATION SDXL HARMONIQUE")
    print("=" * 60)
    
    # 1. Test système
    system_ok = test_system_integration()
    
    if not system_ok:
        print("\n⚠️ Tests limités - système incomplet")
    
    # 2. Test génération images
    image_results = test_image_generation()
    
    # 3. Test génération vidéos
    video_results = test_video_generation()
    
    # 4. Génération rapport
    report = generate_report(image_results, video_results, system_ok)
    
    # 5. Affichage résumé
    print(f"\n🏆 RÉSUMÉ DES TESTS")
    print("=" * 30)
    print(f"📊 Images: {report['image_tests']['successful_tests']}/{report['image_tests']['total_tests']} réussies")
    print(f"🎬 Vidéos: {report['video_tests']['successful_tests']}/{report['video_tests']['total_tests']} réussies")
    print(f"📦 Compression moyenne: {report['image_tests']['avg_compression_ratio']:.2f}:1")
    print(f"☁️ Upload S3: Images {report['image_tests']['s3_upload_success_rate']:.1%}, Vidéos {report['video_tests']['s3_upload_success_rate']:.1%}")
    print(f"🎬 Total frames générées: {report['video_tests']['total_frames_generated']}")
    
    if system_ok and report['image_tests']['success_rate'] > 0.8 and report['video_tests']['success_rate'] > 0.8:
        print(f"\n🏆 INTÉGRATION SDXL HARMONIQUE RÉUSSIE!")
    else:
        print(f"\n⚠️ INTÉGRATION PARTIELLE - Vérifier les composants")

if __name__ == "__main__":
    main()
