#!/usr/bin/env python3
"""
Test simple pour valider les claims community-proof
"""

import json
import time
import requests

def test_health(api_url):
    """Test de santÃ© du service"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Service santÃ©: ACTIF")
            return True
        else:
            print(f"[ERREUR] Service santÃ©: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERREUR] Service santÃ©: {e}")
        return False

def test_determinism_simple(api_url):
    """Test simple de dÃ©terminisme"""
    print("\n[TEST] DÃ©terminisme (2 appels identiques)...")
    
    prompt = "Quelle est la capitale de la France?"
    payload = {
        "prompt": prompt,
        "max_tokens": 50,
        "temperature": 0.0,
        "verified_mode": True
    }
    
    responses = []
    response_ids = []
    
    for i in range(2):
        try:
            response = requests.post(f"{api_url}/generate", json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                responses.append(data)
                rid = data.get("response_id", "")
                response_ids.append(rid)
                print(f"  Appel {i+1}: response_id = {rid[:16]}...")
            else:
                print(f"  [ERREUR] HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"  [ERREUR] {e}")
            return False
        
        time.sleep(0.5)
    
    # VÃ©rification
    if response_ids[0] and response_ids[0] == response_ids[1]:
        print("  [OK] DÃ©terminisme vÃ©rifiÃ©: response_id identiques")
        return True
    else:
        print("  [ERREUR] DÃ©terminisme Ã©chouÃ©: response_id diffÃ©rents")
        return False

def test_verified_mode(api_url):
    """Test du mode vÃ©rifiÃ©"""
    print("\n[TEST] Mode vÃ©rifiÃ© (abstention sans sources)...")
    
    # Question factuelle sans sources
    prompt = "Quel est le PIB de l'Allemagne en 2025?"
    payload = {
        "prompt": prompt,
        "max_tokens": 100,
        "verified_mode": True,
        "sources": []
    }
    
    try:
        response = requests.post(f"{api_url}/generate", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "").lower()
            
            # VÃ©rifier l'abstention
            if "abstention" in content or "abstain" in content or "sources" in content:
                print(f"  [OK] Abstention dÃ©tectÃ©e: {content[:80]}...")
                return True
            else:
                print(f"  [ATTENTION] Pas d'abstention claire: {content[:80]}...")
                return False
        else:
            print(f"  [ERREUR] HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERREUR] {e}")
        return False

def main():
    """Fonction principale"""
    api_url = "http://__EC2_IP__:8000"
    
    print("=" * 60)
    print("TEST COMMUNITY-PROOF - DeepSeek Harmonic V2")
    print("=" * 60)
    print(f"API: {api_url}")
    
    # ExÃ©cuter les tests
    tests = [
        ("SantÃ© du service", test_health, api_url),
        ("DÃ©terminisme", test_determinism_simple, api_url),
        ("Mode vÃ©rifiÃ©", test_verified_mode, api_url)
    ]
    
    results = []
    
    for test_name, test_func, arg in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func(arg)
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERREUR CRITIQUE] {e}")
            results.append((test_name, False))
    
    # RÃ©sumÃ©
    print("\n" + "=" * 60)
    print("RESUME DES TESTS")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASSE" if result else "ECHOUE"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    score = (passed / total * 100) if total > 0 else 0
    
    print(f"\nScore: {passed}/{total} ({score:.1f}%)")
    
    # GÃ©nÃ©rer un rapport
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "api_url": api_url,
        "results": [
            {"test": name, "passed": result} 
            for name, result in results
        ],
        "summary": {
            "passed": passed,
            "total": total,
            "score_percent": score
        }
    }
    
    report_file = f"community_test_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nRapport sauvegarde: {report_file}")
    
    # Conclusion
    if passed == total:
        print("\n[SUCCES] Tous les tests sont passes!")
        print("Les claims community-proof sont verifies.")
    else:
        print(f"\n[ATTENTION] {total - passed} test(s) ont echoue")
        print("Verifiez la configuration du serveur.")

if __name__ == "__main__":
    main()