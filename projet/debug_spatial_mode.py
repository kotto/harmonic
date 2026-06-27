#!/usr/bin/env python3
"""Débogage spécifique du mode spatial"""

import asyncio
import aiohttp
import json

async def debug_spatial():
    """Débogue le mode spatial en détail"""
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
        
        print(f"Test détaillé du mode spatial")
        print(f"Données envoyées: {json.dumps(request_data, indent=2)}")
        
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
                    
                    print(f"\nRéponse complète:")
                    print(json.dumps(data, indent=2))
                    
                    # Analyse spécifique
                    if "upscale_result" in data:
                        upscale = data["upscale_result"]
                        print(f"\nAnalyse de upscale_result:")
                        print(f"  Mode: {upscale.get('mode')}")
                        print(f"  Target format: {upscale.get('target_format')}")
                        print(f"  Target channels: {upscale.get('target_channels')}")
                        print(f"  Spatial channels added: {upscale.get('spatial_channels_added')}")
                        print(f"  Dynamic range gain: {upscale.get('dynamic_range_gain_db')} dB")
                        print(f"  Freq extension: {upscale.get('freq_extension_khz')} kHz")
                    
                    if "quality_improvement" in data:
                        improvements = data["quality_improvement"]
                        print(f"\nContenu de quality_improvement:")
                        for key, value in improvements.items():
                            print(f"  {key}: {value}")
                    
                    # Vérifier les attentes
                    expected = {
                        "dynamic_range_gain_db": {"min": 40, "max": 60},
                        "spatial_channels_added": {"min": 14, "max": 14},
                        "quality_score_improvement": {"min": 0.8, "max": 1.5}
                    }
                    
                    print(f"\nVérification des attentes:")
                    for key, expected_range in expected.items():
                        if key in improvements:
                            value = improvements[key]
                            is_in_range = expected_range["min"] <= value <= expected_range["max"]
                            status = "PASS" if is_in_range else "FAIL"
                            print(f"  {key}: {value} (attendu: {expected_range['min']}-{expected_range['max']}) [{status}]")
                        else:
                            print(f"  {key}: NON TROUVÉ dans quality_improvement [FAIL]")
                    
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
    print("Début du débogage du mode spatial")
    result = await debug_spatial()
    
    if result:
        print("\nDébogage terminé avec succès")
        with open("debug_spatial_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("Résultats sauvegardés dans debug_spatial_result.json")
    else:
        print("\nDébogage échoué")

if __name__ == "__main__":
    asyncio.run(main())