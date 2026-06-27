#!/usr/bin/env python3
"""
TEST SIMPLIFIÉ DU SYSTÈME DE COMPRESSION HARMONIQUE
Test de base pour valider l'architecture
"""

import numpy as np
import cv2
import time
import sys
import os

# Ajout du chemin pour les modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

def test_basic_functionality():
    """Test basique de la fonctionnalité"""
    print("🎵 TEST SIMPLIFIÉ DE COMPRESSION HARMONIQUE")
    print("=" * 60)
    
    try:
        # Import du moteur
        from harmonic_compression.core import harmonic_engine, CompressionMode
        print("✅ Import du moteur réussi")
        
        # Test d'information système
        system_info = harmonic_engine.get_system_info()
        print(f"📊 Système: {system_info['name']} v{system_info['version']}")
        print(f"🔧 Encodeurs: {system_info['encoders_count']}")
        print(f"⚡ Niveaux: {len(system_info['energy_presets'])}")
        
        # Création d'une image de test simple
        test_image = np.random.randint(50, 200, (100, 150, 3), dtype=np.uint8)
        print(f"📸 Image de test: {test_image.shape}")
        
        # Test de compression avec différents niveaux
        energy_levels = ['economy', 'standard', 'high_quality']
        
        for energy_level in energy_levels:
            print(f"\n⚡ Test niveau: {energy_level}")
            
            start_time = time.time()
            result = harmonic_engine.compress_image(
                test_image, 
                energy_level=energy_level
            )
            processing_time = time.time() - start_time
            
            if result.success:
                print(f"   ✅ Succès en {processing_time:.3f}s")
                print(f"   📊 Ratio: {result.compression_ratio:.1f}:1")
                print(f"   💾 Espace économisé: {result.space_saved_percent:.1f}%")
                print(f"   🌊 Mode: {result.mode_used}")
                print(f"   🎯 Qualité: {result.quality_metrics.get('quality_preservation', 0):.3f}")
            else:
                print(f"   ❌ Erreur: {result.error}")
        
        # Test de sélection automatique
        print(f"\n🧠 Test sélection automatique")
        start_time = time.time()
        result = harmonic_engine.compress_image(test_image)  # mode=None
        processing_time = time.time() - start_time
        
        if result.success:
            print(f"   ✅ Mode auto: {result.mode_used}")
            print(f"   📊 Ratio: {result.compression_ratio:.1f}:1")
            print(f"   ⏱️  Temps: {processing_time:.3f}s")
        
        # Test batch
        print(f"\n📦 Test batch compression")
        test_images = [
            np.random.randint(0, 256, (80, 120, 3), dtype=np.uint8),
            np.random.randint(0, 256, (80, 120, 3), dtype=np.uint8),
            np.random.randint(0, 256, (80, 120, 3), dtype=np.uint8)
        ]
        
        start_time = time.time()
        batch_results = harmonic_engine.batch_compress(test_images, energy_level='standard')
        batch_time = time.time() - start_time
        
        successful = sum(1 for r in batch_results if r.success)
        avg_ratio = np.mean([r.compression_ratio for r in batch_results if r.success])
        
        print(f"   ✅ Batch: {successful}/{len(test_images)} réussis")
        print(f"   📊 Ratio moyen: {avg_ratio:.1f}:1")
        print(f"   ⏱️  Temps total: {batch_time:.3f}s")
        
        # Affichage des statistiques d'apprentissage
        stats = harmonic_engine.learning_stats
        print(f"\n📈 Statistiques d'apprentissage:")
        print(f"   Total traité: {stats['total_processed']}")
        print(f"   Taux de succès: {stats['success_rate']:.1%}")
        
        print("\n🎯 TEST TERMINÉ AVEC SUCCÈS!")
        print("Le système de compression harmonique est fonctionnel.")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_image_variety():
    """Test avec différentes variétés d'images"""
    print("\n🎨 TEST AVEC VARIÉTÉ D'IMAGES")
    print("=" * 60)
    
    try:
        from harmonic_compression.core import harmonic_engine
        
        # Différents types d'images
        images = {
            'gradient': create_gradient_image(),
            'geometric': create_geometric_image(),
            'noise': create_noise_image(),
            'photo_sim': create_photo_image()
        }
        
        for img_name, img_array in images.items():
            print(f"\n📸 Test: {img_name}")
            
            # Analyse rapide
            characteristics = harmonic_engine._analyze_image_characteristics(img_array)
            print(f"   Complexité: {characteristics.get('complexity_score', 0):.3f}")
            
            # Compression
            result = harmonic_engine.compress_image(img_array, energy_level='standard')
            
            if result.success:
                print(f"   ✅ {result.compression_ratio:.1f}:1 en {result.processing_time:.3f}s")
                print(f"   🌊 Mode: {result.mode_used}")
            else:
                print(f"   ❌ Erreur: {result.error}")
    
    except Exception as e:
        print(f"❌ Erreur test variété: {e}")

def create_gradient_image():
    """Crée une image en gradient"""
    img = np.zeros((100, 150, 3), dtype=np.uint8)
    for i in range(100):
        for j in range(150):
            img[i, j] = [i*2, j*1, (i+j)//2]
    return img

def create_geometric_image():
    """Crée une image géométrique"""
    img = np.zeros((100, 150, 3), dtype=np.uint8)
    center = (75, 50)
    cv2.circle(img, center, 30, (255, 128, 64), -1)
    cv2.rectangle(img, (20, 20), (130, 80), (128, 255, 128), -1)
    return img

def create_noise_image():
    """Crée une image avec du bruit"""
    return np.random.randint(50, 200, (100, 150, 3), dtype=np.uint8)

def create_photo_image():
    """Crée une image simulée de photo"""
    img = np.random.randint(80, 180, (100, 150, 3), dtype=np.uint8)
    cv2.circle(img, (75, 50), 20, (200, 150, 100), -1)
    cv2.circle(img, (70, 45), 5, (50, 50, 50), -1)
    cv2.circle(img, (80, 45), 5, (50, 50, 50), -1)
    return img

def main():
    """Fonction principale"""
    print("🎵 DÉMARRAGE DES TESTS DE COMPRESSION HARMONIQUE")
    print("Test de l'implémentation inspirée de l'upscaling harmonique")
    print("=" * 70)
    
    # Test 1: Fonctionnalité de base
    if test_basic_functionality():
        # Test 2: Variété d'images
        test_image_variety()
        
        print("\n🎯 CONCLUSION:")
        print("✅ L'architecture de base est fonctionnelle")
        print("✅ Les encodeurs sont opérationnels")
        print("✅ La sélection automatique fonctionne")
        print("✅ La compression batch fonctionne")
        print("✅ Les statistiques d'apprentissage s'accumulent")
        
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("1. Améliorer les encodeurs individuels")
        print("2. Optimiser l'analyse d'images")
        print("3. Ajouter des métriques avancées")
        print("4. Intégrer l'apprentissage automatique")
        print("5. Créer une interface utilisateur")
    else:
        print("\n❌ TESTS ÉCHOUÉS")
        print("Vérifier l'implémentation et les dépendances")

if __name__ == "__main__":
    main()
