#!/usr/bin/env python3
"""Test de requête brute pour voir les données reçues"""

import asyncio
import aiohttp
import json

async def test_raw():
    """Teste une requête brute"""
    base_url = "http://localhost:9017"
    
    # Démarrer le service si nécessaire
    print("Vérification du service...")
    
    async with aiohttp.ClientSession() as session:
        # Test de santé
        try:
            async with session.get(f"{base_url}/health", timeout=5) as response:
                if response.status == 200:
                    print("Service en ligne")
                else:
                    print(f"Service hors ligne: {response.status}")
                    return
        except Exception as e:
            print(f"Service inaccessible: {e}")
            return
        
        # Test avec données brutes
        raw_data = {
            "source_format": "mp3_320",
            "target_mode": "hcs_spatial",
            "duration_seconds": 30.0,
            "channels": 2,
            "real_time": False
        }
        
        print(f"\nDonnées envoyées:")
        print(json.dumps(raw_data, indent=2))
        
        # Envoyer la requête
        try:
            async with session.post(
                f"{base_url}/process",
                json=raw_data,  # Utiliser json au lieu de form-data
                timeout=30
            ) as response:
                
                print(f"\nStatut HTTP: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"\nDonnées reçues:")
                    print(json.dumps(data, indent=2))
                    
                    # Extraire les informations importantes
                    if "upscale_result" in data:
                        upscale = data["upscale_result"]
                        print(f"\nMode dans upscale_result: {upscale.get('mode')}")
                    
                    if "source_signature" in data:
                        source = data["source_signature"]
                        print(f"Source format dans source_signature: {source.get('source_format')}")
                    
                    return data
                else:
                    error_text = await response.text()
                    print(f"\nErreur: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"Exception: {e}")
            return None

async def main():
    """Fonction principale"""
    print("Test de requête brute")
    result = await test_raw()
    
    if result:
        print("\nTest terminé avec succès")
    else:
        print("\nTest échoué")

if __name__ == "__main__":
    asyncio.run(main())