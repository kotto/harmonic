#!/usr/bin/env python3
"""
Test final de latence sans caracteres Unicode
"""

import time
import asyncio
import aiohttp

async def test_service():
    """Teste le service audio harmonique"""
    url = "http://localhost:9017"
    
    print("Test de latence du service audio harmonique")
    print("=" * 50)
    
    # Test /health
    print("1. Test endpoint /health:")
    try:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/health", timeout=5) as resp:
                latency = (time.time() - start) * 1000
                if resp.status == 200:
                    print(f"   Latence: {latency:.1f}ms")
                    print(f"   Status: {resp.status}")
                else:
                    print(f"   Erreur: Status {resp.status}")
    except Exception as e:
        print(f"   Erreur: {e}")
        return False
    
    # Test /process avec donnees minimales
    print("\n2. Test endpoint /process (simulation):")
    try:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("source_format", "mp3_128")
            data.add_field("target_mode", "hcs_clarity")
            data.add_field("duration_seconds", "10.0")
            data.add_field("channels", "2")
            data.add_field("real_time", "false")
            
            async with session.post(
                f"{url}/process",
                data=data,
                timeout=15
            ) as resp:
                latency = (time.time() - start) * 1000
                if resp.status == 200:
                    result = await resp.json()
                    print(f"   Latence: {latency:.1f}ms")
                    print(f"   Status: {resp.status}")
                    print(f"   Success: {result.get('success', False)}")
                    
                    # Analyse
                    print("\n" + "=" * 50)
                    print("ANALYSE:")
                    print("=" * 50)
                    
                    if latency <= 2000:
                        print(f"OK - OBJECTIF ATTEINT! ({latency:.0f}ms <= 2000ms)")
                    else:
                        print(f"PAS OK - OBJECTIF NON ATTEINT ({latency:.0f}ms > 2000ms)")
                        print(f"  Retard: {latency - 2000:.0f}ms")
                    
                    # Recommandations
                    print("\nRECOMMANDATIONS:")
                    if latency > 3000:
                        print("- Optimisation CRITIQUE requise")
                        print("- Implementer cache LRU")
                        print("- Reduire temps de simulation")
                    elif latency > 2000:
                        print("- Optimisation necessaire")
                        print("- Ajouter caching simple")
                        print("- Optimiser les sleeps")
                    else:
                        print("- Bonne performance")
                        print("- Ajouter cache pour ameliorer")
                        print("- Optimiser numpy operations")
                    
                    return True
                else:
                    print(f"   Erreur: Status {resp.status}")
                    return False
    except Exception as e:
        print(f"   Erreur: {e}")
        return False

async def main():
    """Fonction principale"""
    await test_service()

if __name__ == "__main__":
    asyncio.run(main())