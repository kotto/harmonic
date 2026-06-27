#!/usr/bin/env python3
"""
Script de débogage pour le service audio harmonique
"""

import asyncio
import aiohttp
import json
import time

async def debug_deepseek_endpoint():
    """Débogue l'endpoint /deepseek_enhance"""
    base_url = "http://localhost:9017"
    
    async with aiohttp.ClientSession() as session:
        # Test de l'endpoint /deepseek_enhance
        request_data = {
            "prompt": "Améliorer audio MP3 128kbps vers qualité studio FLAC 24bit/96kHz",
            "enhancement_mode": "harmonic_master",
            "temperature": 0.0,
            "max_tokens": 500
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            async with session.post(
                f"{base_url}/deepseek_enhance",
                json=request_data,
                headers=headers,
                timeout=10
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print("=== DEBUG /deepseek_enhance ===")
                    print(f"Status: {response.status}")
                    print(f"Success: {data.get('success')}")
                    print(f"Description length: {len(data.get('enhanced_audio_description', ''))}")
                    print(f"Description preview: {data.get('enhanced_audio_description', '')[:100]}...")
                    print(f"Quality score: {data.get('quality_score')}")
                    print(f"Processing time: {data.get('processing_time_ms')}ms")
                    print(f"Error message: {data.get('error_message')}")
                    
                    # Vérifications détaillées
                    checks = [
                        data.get("success") == True,
                        "enhanced_audio_description" in data,
                        len(data.get("enhanced_audio_description", "")) > 50,
                        "harmonic_parameters" in data,
                        "quality_score" in data,
                        data.get("quality_score", 0) > 0.5
                    ]
                    
                    print(f"\nChecks: {checks}")
                    
                else:
                    error_text = await response.text()
                    print(f"Error status: {response.status}")
                    print(f"Error text: {error_text}")
        
        except Exception as e:
            print(f"Exception: {e}")

async def debug_process_endpoint():
    """Débogue l'endpoint /process"""
    base_url = "http://localhost:9017"
    
    async with aiohttp.ClientSession() as session:
        # Test de l'endpoint /process avec MP3 128kbps
        request_data = {
            "source_format": "mp3_128",
            "target_mode": "hcs_clarity",
            "duration_seconds": 60.0,
            "channels": 2,
            "real_time": False
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            async with session.post(
                f"{base_url}/process",
                json=request_data,
                headers=headers,
                timeout=10
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print("\n=== DEBUG /process ===")
                    print(f"Status: {response.status}")
                    print(f"Success: {data.get('success')}")
                    print(f"Session ID: {data.get('session_id')}")
                    print(f"Processing time: {data.get('processing_time_ms')}ms")
                    
                    # Vérifications détaillées
                    basic_checks = [
                        data.get("success") == True,
                        "session_id" in data,
                        "source_signature" in data,
                        "upscale_result" in data,
                        "quality_improvement" in data,
                        data.get("processing_time_ms", 0) > 0
                    ]
                    
                    print(f"\nBasic checks: {basic_checks}")
                    
                    # Afficher les données de qualité
                    if "quality_improvement" in data:
                        quality = data["quality_improvement"]
                        print(f"\nQuality improvement:")
                        for key, value in quality.items():
                            print(f"  {key}: {value}")
                    
                else:
                    error_text = await response.text()
                    print(f"Error status: {response.status}")
                    print(f"Error text: {error_text}")
        
        except Exception as e:
            print(f"Exception: {e}")

async def main():
    """Fonction principale"""
    print("Démarrage du débogage du service audio harmonique...")
    
    # Vérifier si le service est en cours d'exécution
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9017/health", timeout=5) as response:
                if response.status == 200:
                    print("Service disponible OK")
                else:
                    print(f"Service non disponible: {response.status}")
                    return
    except Exception as e:
        print(f"Service non accessible: {e}")
        return
    
    # Déboguer les endpoints
    await debug_deepseek_endpoint()
    await debug_process_endpoint()

if __name__ == "__main__":
    asyncio.run(main())