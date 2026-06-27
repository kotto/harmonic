#!/usr/bin/env python3
"""Test simple pour déboguer le mode"""

import asyncio
import aiohttp
import json

async def test_mode():
    """Teste un mode spécifique"""
    base_url = "http://localhost:9017"
    
    async with aiohttp.ClientSession() as session:
        # Test avec mode hcs_spatial
        request_data = {
            "source_format": "mp3_320",
            "target_mode": "hcs_spatial",
            "duration_seconds": 30.0,
            "channels": 2,
            "real_time": False
        }
        
        print(f"Test avec mode: {request_data['target_mode']}")
        print(f"Source format: {request_data['source_format']}")
        
        # Créer FormData
        form_data = aiohttp.FormData()
        for key, value in request_data.items():
            form_data.add_field(key, str(value))
        
        try:
            async with session.post(
                f"{base_url}/process",
                data=form_data,
                timeout=30
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print(f"\nRésultat:")
                    print(f"  Mode retourné: {data.get('upscale_result', {}).get('mode')}")
                    print(f"  Source format: {data.get('source_signature', {}).get('source_format')}")
                    
                    # Afficher les améliorations
                    if "quality_improvement" in data:
                        improvements = data["quality_improvement"]
                        print(f"\nAméliorations:")
                        for key, value in improvements.items():
                            print(f"  {key}: {value}")
                    
                    return data
                else:
                    error_text = await response.text()
                    print(f"Erreur HTTP: {response.status}")
                    print(f"Message: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"Exception: {e}")
            return None

async def main():
    """Fonction principale"""
    print("Début du test de débogage...")
    result = await test_mode()
    
    if result:
        print(f"\nTest terminé avec succès")
        with open("debug_mode_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("Résultats sauvegardés dans debug_mode_result.json")
    else:
        print(f"\nTest échoué")

if __name__ == "__main__":
    asyncio.run(main())