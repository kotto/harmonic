#!/usr/bin/env python3
"""Script de débogage pour les valeurs de test audio harmonique"""

import asyncio
import aiohttp
import json
import time

async def test_specific_mode(source_format: str, target_mode: str, test_name: str):
    """Teste un mode spécifique en détail"""
    base_url = "http://localhost:9017"
    
    async with aiohttp.ClientSession() as session:
        # Données de test
        request_data = {
            "source_format": source_format,
            "target_mode": target_mode,
            "duration_seconds": 30.0,
            "channels": 2,
            "real_time": False
        }
        
        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print(f"Source: {source_format}, Target: {target_mode}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
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
                
                processing_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    print(f"Temps de réponse: {processing_time_ms:.1f}ms")
                    print(f"Session ID: {data.get('session_id')}")
                    
                    # Afficher les améliorations de qualité
                    if "quality_improvement" in data:
                        improvements = data["quality_improvement"]
                        print("\nAméliorations mesurées:")
                        for key, value in improvements.items():
                            print(f"  {key}: {value}")
                    
                    # Afficher le résultat d'upscaling
                    if "upscale_result" in data:
                        upscale = data["upscale_result"]
                        print("\nRésultat d'upscaling:")
                        print(f"  Mode: {upscale.get('mode')}")
                        print(f"  Target format: {upscale.get('target_format')}")
                        print(f"  Dynamic range gain: {upscale.get('dynamic_range_gain_db')} dB")
                        print(f"  Freq extension: {upscale.get('freq_extension_khz')} kHz")
                        print(f"  Quality before: {upscale.get('quality_score_before')}")
                        print(f"  Quality after: {upscale.get('quality_score_after')}")
                        print(f"  Quality improvement: {upscale.get('quality_score_after', 0) - upscale.get('quality_score_before', 0):.2f}")
                        print(f"  K factor: {upscale.get('hcs_harmonic_k_factor')}")
                    
                    # Afficher la signature source
                    if "source_signature" in data:
                        source = data["source_signature"]
                        print("\nSignature source:")
                        print(f"  Source format: {source.get('source_format')}")
                        print(f"  Max freq detected: {source.get('max_freq_detected_khz')} kHz")
                        print(f"  Dynamic range: {source.get('dynamic_range_db')} dB")
                        print(f"  Perceptual quality: {source.get('perceptual_quality_score')}")
                    
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
    
    # Tests pour chaque mode problématique
    test_cases = [
        {
            "name": "MP3 320kbps -> Dolby Atmos 9.1.6 (Spatial)",
            "source_format": "mp3_320",
            "target_mode": "hcs_spatial",
            "expected": {
                "dynamic_range_gain_db": {"min": 40, "max": 60},
                "freq_extension_khz": {"min": 15, "max": 25},
                "quality_score_improvement": {"min": 0.8, "max": 1.5}
            }
        },
        {
            "name": "FLAC 16-bit -> PCM 32/192 Master",
            "source_format": "flac_16",
            "target_mode": "hcs_master",
            "expected": {
                "dynamic_range_gain_db": {"min": 90, "max": 110},
                "freq_extension_khz": {"min": 70, "max": 80},
                "quality_score_improvement": {"min": 0.5, "max": 1.2}
            }
        },
        {
            "name": "Audio GSM -> FLAC 24/96 Restauré",
            "source_format": "phone_gsm",
            "target_mode": "hcs_restore",
            "expected": {
                "dynamic_range_gain_db": {"min": 100, "max": 130},
                "freq_extension_khz": {"min": 40, "max": 50},
                "quality_score_improvement": {"min": 2.0, "max": 3.0}
            }
        }
    ]
    
    all_results = []
    
    for test_case in test_cases:
        result = await test_specific_mode(
            test_case["source_format"],
            test_case["target_mode"],
            test_case["name"]
        )
        
        if result:
            # Vérifier les améliorations
            quality_improvement = result.get("quality_improvement", {})
            expected = test_case["expected"]
            
            print(f"\n{'='*60}")
            print(f"VÉRIFICATION DES ATTENTES - {test_case['name']}")
            print(f"{'='*60}")
            
            for key, expected_range in expected.items():
                if key in quality_improvement:
                    value = quality_improvement[key]
                    is_in_range = expected_range["min"] <= value <= expected_range["max"]
                    status = "PASS" if is_in_range else "FAIL"
                    print(f"{key}: {value:.1f} (attendu: {expected_range['min']}-{expected_range['max']}) [{status}]")
                else:
                    print(f"{key}: NON TROUVÉ dans quality_improvement")
            
            all_results.append({
                "test": test_case["name"],
                "result": result,
                "quality_improvement": quality_improvement
            })
        
        # Pause entre les tests
        await asyncio.sleep(1)
    
    # Sauvegarder les résultats
    with open("debug_test_values_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("RÉSULTATS SAUVEGARDÉS DANS: debug_test_values_results.json")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())