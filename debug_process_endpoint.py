#!/usr/bin/env python3
"""
Débogage spécifique de l'endpoint /process
"""

import asyncio
import aiohttp
import json
import time

async def main():
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
            start_time = time.time()
            async with session.post(
                f"{base_url}/process",
                json=request_data,
                headers=headers,
                timeout=10
            ) as response:
                
                processing_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    raw_text = await response.text()
                    print("=== RAW RESPONSE TEXT (first 1000 chars) ===")
                    print(raw_text[:1000])
                    print("...")
                    
                    try:
                        data = json.loads(raw_text)
                        print("\n=== PARSED JSON ===")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        
                        # Vérifications spécifiques
                        print("\n=== SPECIFIC CHECKS ===")
                        print(f"Success: {data.get('success')}")
                        print(f"Session ID: {data.get('session_id')}")
                        print(f"Processing time: {data.get('processing_time_ms')}ms")
                        print(f"Has source_signature: {'source_signature' in data}")
                        print(f"Has upscale_result: {'upscale_result' in data}")
                        print(f"Has quality_improvement: {'quality_improvement' in data}")
                        
                        if 'quality_improvement' in data:
                            quality = data['quality_improvement']
                            print(f"\nQuality improvement details:")
                            for key, value in quality.items():
                                print(f"  {key}: {value}")
                        
                        # Vérifier pourquoi processing_time_ms est 0
                        print(f"\n=== DEBUG processing_time_ms ===")
                        print(f"Client measured time: {processing_time_ms:.1f}ms")
                        print(f"Server reported time: {data.get('processing_time_ms')}ms")
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error: {e}")
                
                else:
                    error_text = await response.text()
                    print(f"Error status: {response.status}")
                    print(f"Error text: {error_text}")
        
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())