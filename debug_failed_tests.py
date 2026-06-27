#!/usr/bin/env python3
"""Script pour déboguer les tests échoués du service audio harmonique"""

import json
import asyncio
import aiohttp
from typing import Dict, Any

async def debug_failed_tests():
    """Débogue les tests échoués"""
    
    # Lire les résultats des tests
    with open('harmonic_audio_test_results_20260516_154231.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("Analyse des tests échoués:")
    print("=" * 60)
    
    # Analyser chaque test échoué
    for test_result in results["results"]:
        if not test_result.get("success", True):
            print(f"\nTest échoué: {test_result['test']}")
            print(f"Status code: {test_result.get('status_code')}")
            
            # Afficher les checks
            if "checks" in test_result:
                checks = test_result["checks"]
                if isinstance(checks, dict):
                    print(f"Basic checks: {checks.get('basic', [])}")
                    print(f"Improvement checks: {checks.get('improvements', [])}")
                else:
                    print(f"Checks: {checks}")
            
            # Afficher les améliorations attendues vs réelles
            if "expected_improvements" in test_result and "actual_improvements" in test_result:
                expected = test_result["expected_improvements"]
                actual = test_result["actual_improvements"]
                
                print("\nComparaison améliorations:")
                for key, expected_range in expected.items():
                    actual_value = actual.get(key, "NON TROUVE")
                    print(f"  {key}:")
                    print(f"    Attendu: {expected_range['min']}-{expected_range['max']}")
                    print(f"    Obtenu: {actual_value}")
            
            # Afficher les données si disponibles
            if "data" in test_result:
                data = test_result["data"]
                if "upscale_result" in data:
                    upscale = data["upscale_result"]
                    print(f"\nRésultat upscale:")
                    print(f"  Mode: {upscale.get('mode')}")
                    print(f"  spatial_channels_added: {upscale.get('spatial_channels_added')}")
                    print(f"  dynamic_range_gain_db: {upscale.get('dynamic_range_gain_db')}")
                    print(f"  freq_extension_khz: {upscale.get('freq_extension_khz')}")
    
    # Tester manuellement les endpoints problématiques
    print("\n" + "=" * 60)
    print("Tests manuels des endpoints problématiques:")
    print("=" * 60)
    
    base_url = "http://localhost:9017"
    
    async with aiohttp.ClientSession() as session:
        # Test du mode hcs_spatial
        print("\nTest manuel mode hcs_spatial:")
        
        form_data = aiohttp.FormData()
        form_data.add_field("source_format", "mp3_320")
        form_data.add_field("target_mode", "hcs_spatial")
        form_data.add_field("duration_seconds", "45.0")
        form_data.add_field("channels", "2")
        form_data.add_field("real_time", "false")
        
        async with session.post(
            f"{base_url}/process",
            data=form_data,
            timeout=10
        ) as response:
            
            if response.status == 200:
                data = await response.json()
                print(f"Status: {response.status}")
                print(f"Session ID: {data.get('session_id')}")
                
                if "upscale_result" in data:
                    upscale = data["upscale_result"]
                    print(f"Mode: {upscale.get('mode')}")
                    print(f"spatial_channels_added: {upscale.get('spatial_channels_added')}")
                    print(f"dynamic_range_gain_db: {upscale.get('dynamic_range_gain_db')}")
                    print(f"freq_extension_khz: {upscale.get('freq_extension_khz')}")
                    
                    # Vérifier les valeurs
                    spatial_added = upscale.get("spatial_channels_added")
                    if spatial_added == 14:
                        print("✓ spatial_channels_added = 14 (CORRECT)")
                    else:
                        print(f"✗ spatial_channels_added = {spatial_added} (ATTENDU: 14)")
                
                if "quality_improvement" in data:
                    quality = data["quality_improvement"]
                    print(f"\nAméliorations qualité:")
                    for key, value in quality.items():
                        print(f"  {key}: {value}")
            else:
                print(f"Erreur: Status {response.status}")
                error_text = await response.text()
                print(f"Message: {error_text}")

async def main():
    """Fonction principale"""
    await debug_failed_tests()

if __name__ == "__main__":
    asyncio.run(main())