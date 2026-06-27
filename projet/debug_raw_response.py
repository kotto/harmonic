#!/usr/bin/env python3
"""
Examine la réponse JSON brute du service
"""

import asyncio
import aiohttp
import json

async def main():
    base_url = "http://localhost:9017"
    
    async with aiohttp.ClientSession() as session:
        # Test /deepseek_enhance
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
                    raw_text = await response.text()
                    print("=== RAW RESPONSE TEXT ===")
                    print(raw_text[:500])
                    print("...")
                    
                    # Essayer de parser le JSON
                    try:
                        data = json.loads(raw_text)
                        print("\n=== PARSED JSON ===")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        
                        # Vérifier les champs
                        print("\n=== FIELD CHECK ===")
                        print(f"Has 'enhanced_audio_description': {'enhanced_audio_description' in data}")
                        if 'enhanced_audio_description' in data:
                            desc = data['enhanced_audio_description']
                            print(f"Type: {type(desc)}")
                            print(f"Length: {len(desc)}")
                            print(f"Value: {repr(desc)}")
                        
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