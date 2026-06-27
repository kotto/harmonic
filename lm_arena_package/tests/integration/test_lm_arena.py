#!/usr/bin/env python3
"""
Test d'intÃ©gration LM Arena
============================
Teste la connexion avec les services LM Arena existants
- DeepSeek API AWS (__EC2_IP__:8000)
- Services harmoniques audio/vidÃ©o
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# Configuration
DEEPSEEK_API_URL = "http://__EC2_IP__:8000"
AUDIO_SERVICE_URL = "http://localhost:9017"
VIDEO_SERVICE_URL = "http://localhost:9018"

async def test_deepseek_api():
    """Test de connexion Ã  l'API DeepSeek AWS"""
    print("\n" + "="*60)
    print("Test API DeepSeek AWS")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test de santÃ©
            print("1. Test endpoint /health...")
            health_response = await client.get(f"{DEEPSEEK_API_URL}/health")
            print(f"   Status: {health_response.status_code}")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   RÃ©ponse: {json.dumps(health_data, indent=2)}")
            else:
                print(f"   Erreur: {health_response.text}")
            
            # Test de gÃ©nÃ©ration
            print("\n2. Test gÃ©nÃ©ration de rÃ©ponse...")
            payload = {
                "prompt": "Bonjour, comment Ã§a va?",
                "max_tokens": 100,
                "temperature": 0.0,
                "verified_mode": True,
                "arena_mode": True
            }
            
            start_time = time.time()
            gen_response = await client.post(f"{DEEPSEEK_API_URL}/generate", json=payload)
            processing_time = time.time() - start_time
            
            print(f"   Status: {gen_response.status_code}")
            print(f"   Temps de traitement: {processing_time:.2f}s")
            
            if gen_response.status_code == 200:
                gen_data = gen_response.json()
                print(f"   RÃ©ponse: {gen_data.get('response', '')[:200]}...")
                print(f"   Confiance: {gen_data.get('confidence', 0):.2f}")
                print(f"   Mode vÃ©rifiÃ©: {gen_data.get('verified_mode', False)}")
                print(f"   Citations: {len(gen_data.get('citations', []))}")
                return True
            else:
                print(f"   Erreur: {gen_response.text}")
                return False
                
    except httpx.TimeoutException:
        print("   [ERREUR] Timeout - L'API DeepSeek ne rÃ©pond pas")
        return False
    except httpx.ConnectError:
        print("   [ERREUR] Connexion refusÃ©e - VÃ©rifiez l'URL et le port")
        return False
    except Exception as e:
        print(f"   [ERREUR] {str(e)}")
        return False

async def test_audio_service():
    """Test de connexion au service audio harmonique"""
    print("\n" + "="*60)
    print("Test Service Audio Harmonique")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test de santÃ©
            print("1. Test endpoint /health...")
            health_response = await client.get(f"{AUDIO_SERVICE_URL}/health")
            print(f"   Status: {health_response.status_code}")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   RÃ©ponse: {json.dumps(health_data, indent=2)}")
                return True
            else:
                print(f"   Erreur: {health_response.text}")
                return False
                
    except httpx.TimeoutException:
        print("   [ERREUR] Timeout - Le service audio ne rÃ©pond pas")
        print("   Note: Le service audio doit Ãªtre dÃ©marrÃ© sÃ©parÃ©ment")
        return False
    except httpx.ConnectError:
        print("   [ERREUR] Connexion refusÃ©e - VÃ©rifiez que le service audio est en cours d'exÃ©cution")
        return False
    except Exception as e:
        print(f"   [ERREUR] {str(e)}")
        return False

async def test_video_service():
    """Test de connexion au service vidÃ©o harmonique"""
    print("\n" + "="*60)
    print("Test Service VidÃ©o Harmonique")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test de santÃ©
            print("1. Test endpoint /health...")
            health_response = await client.get(f"{VIDEO_SERVICE_URL}/health")
            print(f"   Status: {health_response.status_code}")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   RÃ©ponse: {json.dumps(health_data, indent=2)}")
                return True
            else:
                print(f"   Erreur: {health_response.text}")
                return False
                
    except httpx.TimeoutException:
        print("   [ERREUR] Timeout - Le service vidÃ©o ne rÃ©pond pas")
        print("   Note: Le service vidÃ©o doit Ãªtre dÃ©marrÃ© sÃ©parÃ©ment")
        return False
    except httpx.ConnectError:
        print("   [ERREUR] Connexion refusÃ©e - VÃ©rifiez que le service vidÃ©o est en cours d'exÃ©cution")
        return False
    except Exception as e:
        print(f"   [ERREUR] {str(e)}")
        return False

async def test_saas_backend():
    """Test du backend SaaS local"""
    print("\n" + "="*60)
    print("Test Backend SaaS Local")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test de santÃ©
            print("1. Test endpoint /health...")
            health_response = await client.get("http://localhost:9000/health")
            print(f"   Status: {health_response.status_code}")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   RÃ©ponse: {json.dumps(health_data, indent=2)}")
                return True
            else:
                print(f"   Erreur: {health_response.text}")
                return False
                
    except httpx.TimeoutException:
        print("   [ERREUR] Timeout - Le backend SaaS n'est pas dÃ©marrÃ©")
        print("   ExÃ©cutez: docker-compose up -d api")
        return False
    except httpx.ConnectError:
        print("   [ERREUR] Connexion refusÃ©e - Le backend SaaS n'Ã©coute pas sur le port 9000")
        return False
    except Exception as e:
        print(f"   [ERREUR] {str(e)}")
        return False

async def test_frontend():
    """Test du frontend local"""
    print("\n" + "="*60)
    print("Test Frontend Local")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test de la page principale
            print("1. Test page principale...")
            frontend_response = await client.get("http://localhost:8080")
            print(f"   Status: {frontend_response.status_code}")
            if frontend_response.status_code == 200:
                print("   Frontend accessible avec succÃ¨s")
                return True
            else:
                print(f"   Erreur: {frontend_response.text}")
                return False
                
    except httpx.TimeoutException:
        print("   [ERREUR] Timeout - Le frontend n'est pas dÃ©marrÃ©")
        print("   ExÃ©cutez: cd frontend && start_frontend.bat")
        return False
    except httpx.ConnectError:
        print("   [ERREUR] Connexion refusÃ©e - Le frontend n'Ã©coute pas sur le port 8080")
        return False
    except Exception as e:
        print(f"   [ERREUR] {str(e)}")
        return False

async def run_all_tests():
    """ExÃ©cute tous les tests d'intÃ©gration"""
    print("\n" + "="*60)
    print("TEST D'INTÃ‰GRATION COMPLET - HARMONIC AI SAAS")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test DeepSeek API
    results['deepseek'] = await test_deepseek_api()
    
    # Test Audio Service
    results['audio'] = await test_audio_service()
    
    # Test Video Service
    results['video'] = await test_video_service()
    
    # Test SaaS Backend
    results['saas_backend'] = await test_saas_backend()
    
    # Test Frontend
    results['frontend'] = await test_frontend()
    
    # RÃ©sumÃ©
    print("\n" + "="*60)
    print("RÃ‰SUMÃ‰ DES TESTS")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for service, passed in results.items():
        status = "âœ“ PASS" if passed else "âœ— FAIL"
        print(f"{service:20} {status}")
    
    print("\n" + "-"*60)
    print(f"Total: {passed_tests}/{total_tests} tests passÃ©s")
    
    if passed_tests == total_tests:
        print("\nðŸŽ‰ TOUS LES TESTS SONT PASSÃ‰S AVEC SUCCÃˆS !")
        print("Le dashboard SaaS est prÃªt pour l'intÃ©gration LM Arena.")
    else:
        print("\nâš ï¸  Certains tests ont Ã©chouÃ©.")
        print("VÃ©rifiez la configuration des services.")
    
    return all(results.values())

def main():
    """Fonction principale"""
    try:
        success = asyncio.run(run_all_tests())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nTest interrompu par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n[ERREUR CRITIQUE] {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\nCode de sortie: {exit_code}")
    exit(exit_code)