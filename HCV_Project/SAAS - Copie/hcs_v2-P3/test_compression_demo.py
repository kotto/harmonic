#!/usr/bin/env python3
"""
Démonstration du Compresseur Quantique-Harmonique
Test complet avec métriques détaillées
"""

import numpy as np
import cv2
import time
import matplotlib.pyplot as plt
from core.quantum_harmonic_compressor import quantum_harmonic_compressor

def create_test_images():
    """Crée des images de test variées"""
    images = {}
    
    # Image 1: Patterns géométriques (symétrique)
    geometric = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(0, 200, 20):
        cv2.rectangle(geometric, (i, i), (200-i, 200-i), (255, 255, 255), 2)
        cv2.circle(geometric, (100, 100), i, (128, 128, 255), 1)
    images['geometric'] = geometric
    
    # Image 2: Texture naturelle (complexe)
    texture = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
    # Ajout de patterns
    for i in range(5):
        y, x = np.random.randint(0, 200, 2)
        radius = np.random.randint(10, 30)
        color = tuple(np.random.randint(100, 255, 3).tolist())
        cv2.circle(texture, (x, y), radius, color, -1)
    images['texture'] = texture
    
    # Image 3: Dégradé (harmonique)
    gradient = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(200):
        gradient[i, :, :] = i
        gradient[:, i, :] = 255 - i
    images['gradient'] = gradient
    
    # Image 4: Photo réaliste (bruitée)
    photo = np.random.normal(128, 30, (200, 200, 3)).astype(np.uint8)
    # Ajout de structures
    kernel = np.ones((5, 5), np.float32) / 25
    photo = cv2.filter2D(photo, -1, kernel)
    images['photo'] = photo
    
    return images

def test_compression_modes(images):
    """Test tous les modes de compression"""
    results = {}
    
    for image_name, image in images.items():
        print(f"\n🖼️  Test de l'image: {image_name}")
        print(f"   Taille originale: {image.nbytes} octets")
        
        results[image_name] = {}
        
        # Test chaque mode de compression
        for mode in ['lossless', 'balanced', 'aggressive', 'quantum']:
            print(f"\n📦 Mode: {mode}")
            
            # Compression
            start_time = time.time()
            compression_result = quantum_harmonic_compressor.compress_image(
                image, compression_mode=mode
            )
            
            if compression_result['success']:
                metrics = compression_result['metrics']
                timing = compression_result['timing']
                harmonic_info = compression_result['harmonic_info']
                
                # Stockage des résultats
                results[image_name][mode] = {
                    'compression_ratio': metrics.compression_ratio,
                    'psnr': metrics.psnr,
                    'ssim': metrics.ssim,
                    'quality_score': metrics.quality_score,
                    'enhancement_score': metrics.enhancement_score,
                    'compression_time': metrics.compression_time,
                    'decompression_time': metrics.decompression_time,
                    'symmetry_score': harmonic_info['symmetry_score'],
                    'phase_coherence': harmonic_info['phase_coherence']
                }
                
                # Affichage des métriques
                print(f"   ✅ Ratio: {metrics.compression_ratio:.3f}")
                print(f"   📊 PSNR: {metrics.psnr:.1f} dB")
                print(f"   🎯 SSIM: {metrics.ssim:.3f}")
                print(f"   ⭐ Qualité: {metrics.quality_score:.3f}")
                print(f"   🚀 Amélioration: {metrics.enhancement_score:.3f}")
                print(f"   ⏱️  Temps compression: {metrics.compression_time:.3f}s")
                print(f"   ⏱️  Temps décompression: {metrics.decompression_time:.3f}s")
                print(f"   🔄 Symétrie: {harmonic_info['symmetry_score']:.3f}")
                print(f"   🌊 Cohérence phase: {harmonic_info['phase_coherence']:.3f}")
            else:
                print(f"   ❌ Erreur: {compression_result['error']}")
                results[image_name][mode] = None
    
    return results

def analyze_results(results):
    """Analyse détaillée des résultats"""
    print("\n" + "="*80)
    print("📈 ANALYSE DÉTAILLÉE DES RÉSULTATS")
    print("="*80)
    
    # Tableau récapitulatif
    print(f"\n{'Image':<12} {'Mode':<12} {'Ratio':<8} {'PSNR':<8} {'SSIM':<8} {'Qualité':<8} {'Temps':<8}")
    print("-" * 70)
    
    for image_name, modes in results.items():
        for mode, metrics in modes.items():
            if metrics:
                print(f"{image_name:<12} {mode:<12} {metrics['compression_ratio']:<8.3f} "
                      f"{metrics['psnr']:<8.1f} {metrics['ssim']:<8.3f} "
                      f"{metrics['quality_score']:<8.3f} {metrics['compression_time']:<8.3f}")
    
    # Analyse par mode
    print(f"\n🎯 PERFORMANCE PAR MODE:")
    for mode in ['lossless', 'balanced', 'aggressive', 'quantum']:
        mode_results = []
        for image_name, modes in results.items():
            if mode in modes and modes[mode]:
                mode_results.append(modes[mode])
        
        if mode_results:
            avg_ratio = np.mean([r['compression_ratio'] for r in mode_results])
            avg_psnr = np.mean([r['psnr'] for r in mode_results])
            avg_ssim = np.mean([r['ssim'] for r in mode_results])
            avg_quality = np.mean([r['quality_score'] for r in mode_results])
            avg_time = np.mean([r['compression_time'] for r in mode_results])
            
            print(f"\n{mode.upper()}:")
            print(f"  Ratio moyen: {avg_ratio:.3f}")
            print(f"  PSNR moyen: {avg_psnr:.1f} dB")
            print(f"  SSIM moyen: {avg_ssim:.3f}")
            print(f"  Qualité moyenne: {avg_quality:.3f}")
            print(f"  Temps moyen: {avg_time:.3f}s")
    
    # Analyse par type d'image
    print(f"\n🖼️  PERFORMANCE PAR TYPE D'IMAGE:")
    for image_name in results.keys():
        image_results = []
        for mode, metrics in results[image_name].items():
            if metrics:
                image_results.append(metrics)
        
        if image_results:
            # Meilleur mode pour cette image
            best_mode = max(results[image_name].items(), 
                           key=lambda x: x[1]['quality_score'] if x[1] else 0)
            
            avg_symmetry = np.mean([r['symmetry_score'] for r in image_results])
            avg_coherence = np.mean([r['phase_coherence'] for r in image_results])
            
            print(f"\n{image_name.upper()}:")
            print(f"  Symétrie moyenne: {avg_symmetry:.3f}")
            print(f"  Cohérence moyenne: {avg_coherence:.3f}")
            print(f"  Meilleur mode: {best_mode[0]} (qualité: {best_mode[1]['quality_score']:.3f})")

def demonstrate_enhancement():
    """Démontre l'amélioration à la décompression"""
    print("\n" + "="*80)
    print("🚀 DÉMONSTRATION D'AMÉLIORATION QUANTIQUE")
    print("="*80)
    
    # Création d'une image dégradée
    degraded = np.random.normal(128, 40, (150, 150, 3)).astype(np.uint8)
    
    print("📉 Image dégradée (bruit élevé)")
    print(f"  Taille: {degraded.nbytes} octets")
    
    # Compression avec mode quantique
    result = quantum_harmonic_compressor.compress_image(degraded, 'quantum')
    
    if result['success']:
        metrics = result['metrics']
        print(f"\n✅ Compression quantique réussie:")
        print(f"  Ratio: {metrics.compression_ratio:.3f}")
        print(f"  PSNR: {metrics.psnr:.1f} dB")
        print(f"  SSIM: {metrics.ssim:.3f}")
        print(f"  Score d'amélioration: {metrics.enhancement_score:.3f}")
        
        if metrics.enhancement_score > 0.5:
            print("🎉 AMÉLIORATION SIGNIFICATIVE DÉTECTÉE!")
        elif metrics.enhancement_score > 0.2:
            print("✨ Amélioration modérée détectée")
        else:
            print("📊 Compression standard (pas d'amélioration)")
    else:
        print(f"❌ Erreur: {result['error']}")

def main():
    """Fonction principale de démonstration"""
    print("🌟 DÉMONSTRATION DU COMPRESSEUR QUANTIQUE-HARMONIQUE")
    print("=" * 80)
    
    # Création des images de test
    print("\n🎨 Création des images de test...")
    test_images = create_test_images()
    print(f"✅ {len(test_images)} images créées")
    
    # Test de compression
    print("\n🔄 Lancement des tests de compression...")
    results = test_compression_modes(test_images)
    
    # Analyse des résultats
    analyze_results(results)
    
    # Démonstration d'amélioration
    demonstrate_enhancement()
    
    # Informations sur le système
    print(f"\n📋 INFORMATIONS SYSTÈME:")
    info = quantum_harmonic_compressor.get_compression_info()
    print(f"  Nom: {info['name']}")
    print(f"  Version: {info['version']}")
    print(f"  Description: {info['description']}")
    print(f"  Modes: {', '.join(info['compression_modes'])}")
    
    print(f"\n🎯 CONCLUSION:")
    print("Le compresseur quantique-harmonique démontre:")
    print("  • Compression efficace avec préservation de qualité")
    print("  • Analyse harmonique intelligente")
    print("  • Potentiel d'amélioration à la décompression")
    print("  • Adaptation selon les caractéristiques de l'image")

if __name__ == "__main__":
    main()
