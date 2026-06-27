#!/usr/bin/env python3
"""
Test du système de compression harmonique HCS
"""

import requests
import time
import os
import json
import base64

def test_harmonic_health():
    """Test de santé du système harmonique"""
    
    print("🎵 Test de santé du système harmonique...")
    
    try:
        response = requests.get("http://localhost:8000/api/v3/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Système harmonique: {data['status']}")
            print(f"📊 Compression harmonique: {data['harmonic_compression']}")
            print(f"🎯 Référence guidée: {data['reference_guided']}")
            print(f"🌊 Constantes chargées: {data['constants_loaded']}")
            print(f"📈 Version: {data['version']}")
            return True
        else:
            print(f"❌ Erreur santé: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False

def test_harmonic_constants():
    """Test des constantes harmoniques"""
    
    print("\n🌊 Test des constantes harmoniques...")
    
    try:
        response = requests.get("http://localhost:8000/api/v3/constants")
        
        if response.status_code == 200:
            data = response.json()
            constants = data['constants']
            
            print(f"✅ Constantes chargées: {len(constants)}")
            print(f"🎵 Nombre d'or: {constants['golden_ratio']}")
            print(f"📏 Pi: {constants['pi']}")
            print(f"📈 E: {constants['e']}")
            print(f"📐 √2: {constants['sqrt2']}")
            print(f"🌟 Fibonacci: {len(constants['fibonacci_sequence'])} termes")
            print(f"🎼 Série harmonique: {len(constants['harmonic_series'])} termes")
            print(f"🔢 Harmoniques premiers: {len(constants['prime_harmonics'])}")
            
            return True
        else:
            print(f"❌ Erreur constantes: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur constantes: {e}")
        return False

def test_harmonic_stats():
    """Test des statistiques du système"""
    
    print("\n📊 Test des statistiques harmoniques...")
    
    try:
        response = requests.get("http://localhost:8000/api/v3/stats")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Statistiques obtenues")
            
            capabilities = data['capabilities']
            print(f"\n🎯 Capacités:")
            for capability, enabled in capabilities.items():
                status = "✅" if enabled else "❌"
                print(f"  {status} {capability}")
            
            performance = data['performance']
            print(f"\n📈 Performance attendue:")
            for metric, value in performance.items():
                print(f"  📊 {metric}: {value}")
            
            return True
        else:
            print(f"❌ Erreur stats: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur stats: {e}")
        return False

def test_harmonic_compression():
    """Test de compression harmonique"""
    
    print("\n🎵 Test de compression harmonique...")
    
    video_path = "test_1080p_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Fichier vidéo non trouvé: {video_path}")
        return False
    
    try:
        # Préparer le fichier
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Test de compression
        files = {'file': (video_path, video_data, 'video/mp4')}
        data = {
            'priority': 'balanced',
            'quality_threshold': 0.7
        }
        
        print(f"📬 Envoi de la requête de compression harmonique...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/v3/harmonic-compress",
            files=files,
            data=data
        )
        
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Compression harmonique réussie!")
            print(f"⏱️ Temps de requête: {request_time:.2f}s")
            print(f"🎯 Méthode: {result['method']}")
            print(f"📊 Frames compressées: {result['frame_count']}")
            print(f"⏱️ Temps compression: {result['compression_time']:.2f}s")
            print(f"📈 Version: {result['version']}")
            print(f"🎵 Constantes utilisées: {len(result['harmonic_constants_used'])}")
            
            # Métadonnées de la référence
            ref_metadata = result.get('reference_metadata', {})
            print(f"\n📸 Référence:")
            print(f"  📐 Résolution: {ref_metadata.get('resolution', 'N/A')}")
            print(f"  🎨 Canaux: {ref_metadata.get('channels', 'N/A')}")
            print(f"  💡 Luminosité: {ref_metadata.get('brightness', 'N/A'):.2f}")
            print(f"  📊 Contraste: {ref_metadata.get('contrast', 'N/A'):.2f}")
            
            return True
        else:
            print(f"❌ Erreur compression: {response.status_code}")
            print(f"📊 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur compression: {e}")
        return False

def test_harmonic_demo():
    """Test de démonstration harmonique complète"""
    
    print("\n🎭 Test de démonstration harmonique complète...")
    
    video_path = "test_1080p_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Fichier vidéo non trouvé: {video_path}")
        return False
    
    try:
        # Préparer le fichier
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Test de démonstration
        files = {'file': (video_path, video_data, 'video/mp4')}
        data = {'priority': 'balanced'}
        
        print(f"🎬 Démonstration compression + reconstruction...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/v3/harmonic-demo",
            files=files,
            data=data
        )
        
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Démonstration harmonique réussie!")
            print(f"⏱️ Temps total: {request_time:.2f}s")
            print(f"🎯 Méthode: {result['method']}")
            
            # Compression
            compression = result['compression']
            print(f"\n📼 Compression:")
            print(f"  ⏱️ Temps: {compression['time']:.2f}s")
            print(f"  📊 Frames: {compression['frames']}")
            print(f"  💡 Qualité référence: {compression['reference_quality']:.2f}")
            
            # Reconstruction
            reconstruction = result['reconstruction']
            print(f"\n🔄 Reconstruction:")
            print(f"  ⏱️ Temps: {reconstruction['time']:.2f}s")
            print(f"  📊 Frames: {reconstruction['frames']}")
            print(f"  🎯 Score qualité: {reconstruction['quality_score']:.2f}")
            
            # Performance
            performance = result['performance']
            print(f"\n📈 Performance:")
            print(f"  📊 Ratio compression: {performance['compression_ratio']}")
            print(f"  📈 Amélioration qualité: {performance['quality_improvement']}")
            print(f"  🎵 Enhancement harmonique: {performance['harmonic_enhancement']}")
            
            return True
        else:
            print(f"❌ Erreur démonstration: {response.status_code}")
            print(f"📊 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur démonstration: {e}")
        return False

def test_harmonic_info():
    """Test des informations harmoniques"""
    
    print("\n📚 Test des informations harmoniques...")
    
    try:
        response = requests.get("http://localhost:8000/api/v3/harmonic-info")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Informations harmoniques obtenues")
            print(f"🎵 Système: {data['system']['name']}")
            print(f"📈 Version: {data['system']['version']}")
            
            # Features
            print(f"\n🎯 Fonctionnalités:")
            for feature in data['system']['features']:
                print(f"  ✅ {feature}")
            
            # Performance
            performance = data['performance']
            print(f"\n📊 Performance:")
            for metric, value in performance.items():
                print(f"  📈 {metric}: {value}")
            
            # Applications
            print(f"\n🎬 Applications:")
            for app in data['applications']:
                print(f"  🎯 {app}")
            
            return True
        else:
            print(f"❌ Erreur infos: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur infos: {e}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🎵 Test Complet du Système de Compression Harmonique HCS")
    print("=" * 60)
    
    tests = [
        ("Santé du système", test_harmonic_health),
        ("Constantes harmoniques", test_harmonic_constants),
        ("Statistiques système", test_harmonic_stats),
        ("Compression harmonique", test_harmonic_compression),
        ("Démonstration complète", test_harmonic_demo),
        ("Informations système", test_harmonic_info)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{status} - {test_name}")
        if result:
            success_count += 1
    
    print(f"\n📈 Résultat global: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("🎉 TOUS LES TESTS RÉUSSIS - Système harmonique opérationnel!")
    elif success_count >= len(results) * 0.8:
        print("⚠️  MAJORITÉ DES TESTS RÉUSSIS - Système partiellement opérationnel")
    else:
        print("❌ PLUSIEURS TESTS EN ÉCHEC - Système nécessite des corrections")
    
    return success_count == len(results)

if __name__ == "__main__":
    main()
