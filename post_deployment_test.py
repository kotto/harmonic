#!/usr/bin/env python3
"""
Test post-déploiement pour vérifier que l'API DeepSeek Harmonic V2 fonctionne correctement
Ce script doit être exécuté APRÈS le déploiement sur l'instance EC2
"""

import requests
import json
import time
import sys

def test_api_health(api_url):
    """Teste la santé de l'API"""
    print("1. Test de santé de l'API...")
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ API saine: {data.get('status', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
            return True, data
        else:
            print(f"   ✘ Erreur HTTP: {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print("   ✘ Impossible de se connecter à l'API")
        return False, None
    except Exception as e:
        print(f"   ✘ Exception: {e}")
        return False, None

def test_api_root(api_url):
    """Teste l'endpoint racine"""
    print("2. Test de l'endpoint racine...")
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Endpoint racine OK")
            print(f"   Message: {data.get('message', 'N/A')}")
            return True, data
        else:
            print(f"   ✘ Erreur HTTP: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"   ✘ Exception: {e}")
        return False, None

def test_generation_simple(api_url):
    """Teste la génération simple"""
    print("3. Test de génération simple...")
    try:
        payload = {
            "prompt": "Bonjour, test de l'API DeepSeek Harmonic V2",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        start_time = time.time()
        response = requests.post(
            f"{api_url}/generate",
            json=payload,
            timeout=30
        )
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Génération réussie ({processing_time:.2f}s)")
            print(f"   Confiance: {data.get('confidence', 0):.2f}")
            print(f"   Version: {data.get('version', 'N/A')}")
            print(f"   Prévisualisation: {data.get('content', '')[:100]}...")
            return True, data
        else:
            print(f"   ✘ Erreur HTTP: {response.status_code}")
            print(f"   Réponse: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"   ✘ Exception: {e}")
        return False, None

def test_lm_arena_scenarios(api_url):
    """Teste les scénarios LM Arena"""
    print("4. Tests des scénarios LM Arena...")
    
    scenarios = [
        {
            "name": "Raisonnement logique",
            "prompt": "Un train quitte Paris à 8h du matin voyageant à 120 km/h, et un autre train quitte Lyon à 9h voyageant à 100 km/h. Paris et Lyon sont distants de 500 km. À quelle heure les trains se croiseront-ils?",
            "expected_keywords": ["train", "Paris", "Lyon", "km/h", "heure"]
        },
        {
            "name": "Codage Python",
            "prompt": "Écris une fonction Python pour trouver la plus longue sous-chaîne palindrome dans une chaîne donnée.",
            "expected_keywords": ["def", "python", "fonction", "palindrome", "chaîne"]
        },
        {
            "name": "Mathématiques avancées",
            "prompt": "Calcule l'intégrale de x^2 * sin(x) de 0 à π.",
            "expected_keywords": ["intégrale", "x^2", "sin(x)", "π", "calcul"]
        },
        {
            "name": "Connaissance générale",
            "prompt": "Explique le principe de la relativité générale d'Einstein.",
            "expected_keywords": ["Einstein", "relativité", "gravité", "espace-temps", "principe"]
        },
        {
            "name": "Créativité",
            "prompt": "Écris une courte histoire de science-fiction sur une IA qui découvre l'émotion.",
            "expected_keywords": ["IA", "émotion", "histoire", "science-fiction", "découvre"]
        }
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for scenario in scenarios:
        print(f"   • {scenario['name']}...")
        try:
            payload = {
                "prompt": scenario["prompt"],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{api_url}/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "").lower()
                
                # Vérifier les mots-clés attendus
                keyword_matches = 0
                for keyword in scenario["expected_keywords"]:
                    if keyword.lower() in content:
                        keyword_matches += 1
                
                if keyword_matches >= 2:  # Au moins 2 mots-clés correspondants
                    print(f"     ✓ Réussi ({keyword_matches}/5 mots-clés)")
                    passed += 1
                    results.append({
                        "scenario": scenario["name"],
                        "success": True,
                        "keyword_matches": keyword_matches,
                        "confidence": data.get("confidence", 0)
                    })
                else:
                    print(f"     ✘ Échoué (seulement {keyword_matches}/5 mots-clés)")
                    failed += 1
                    results.append({
                        "scenario": scenario["name"],
                        "success": False,
                        "keyword_matches": keyword_matches
                    })
            else:
                print(f"     ✘ Erreur HTTP: {response.status_code}")
                failed += 1
                results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"     ✘ Exception: {e}")
            failed += 1
            results.append({
                "scenario": scenario["name"],
                "success": False,
                "error": str(e)
            })
    
    return results, passed, failed

def test_external_connectivity():
    """Teste la connectivité externe"""
    print("5. Test de connectivité externe...")
    try:
        # Obtenir l'IP publique
        response = requests.get("https://api.ipify.org?format=json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            public_ip = data.get("ip", "N/A")
            print(f"   ✓ IP publique: {public_ip}")
            return True, public_ip
        else:
            print(f"   ✘ Impossible d'obtenir l'IP publique")
            return False, None
    except Exception as e:
        print(f"   ✘ Exception: {e}")
        return False, None

def generate_report(results, health_ok, root_ok, gen_ok, connectivity_ok, public_ip):
    """Génère un rapport de test"""
    print("\n" + "=" * 70)
    print("RAPPORT DE TEST POST-DEPLOIEMENT")
    print("=" * 70)
    
    total_tests = 5 + len(results)  # 5 tests de base + scénarios LM Arena
    passed_tests = sum([
        1 if health_ok else 0,
        1 if root_ok else 0,
        1 if gen_ok else 0,
        1 if connectivity_ok else 0,
        sum(1 for r in results if r.get("success", False))
    ])
    
    print(f"Tests totaux: {total_tests}")
    print(f"Tests réussis: {passed_tests}")
    print(f"Taux de réussite: {passed_tests/total_tests*100:.1f}%")
    print()
    
    print("Détails des tests:")
    print(f"  1. Santé API: {'✓' if health_ok else '✘'}")
    print(f"  2. Endpoint racine: {'✓' if root_ok else '✘'}")
    print(f"  3. Génération simple: {'✓' if gen_ok else '✘'}")
    print(f"  4. Connectivité externe: {'✓' if connectivity_ok else '✘'} (IP: {public_ip or 'N/A'})")
    print()
    
    print("Scénarios LM Arena:")
    for result in results:
        status = "✓" if result.get("success", False) else "✘"
        matches = result.get("keyword_matches", 0)
        confidence = result.get("confidence", 0)
        if confidence > 0:
            print(f"  {status} {result['scenario']}: {matches}/5 mots-clés, confiance {confidence:.2f}")
        else:
            print(f"  {status} {result['scenario']}: {matches}/5 mots-clés")
    
    print()
    print("RECOMMANDATIONS POUR LM ARENA:")
    if passed_tests == total_tests:
        print("  ✓ L'API est prête pour LM Arena!")
        print(f"  URL à utiliser: http://{public_ip}:8000")
        print("  Endpoint: /generate")
        print("  Méthode: POST")
        print("  Format: JSON avec champ 'prompt'")
    else:
        print("  ✘ Des problèmes ont été détectés:")
        if not health_ok:
            print("  - L'API santé ne répond pas")
        if not root_ok:
            print("  - L'endpoint racine ne fonctionne pas")
        if not gen_ok:
            print("  - La génération échoue")
        if not connectivity_ok:
            print("  - La connectivité externe est problématique")
        
        failed_scenarios = [r['scenario'] for r in results if not r.get('success', True)]
        if failed_scenarios:
            print(f"  - Scénarios LM Arena échoués: {', '.join(failed_scenarios)}")
    
    print("\n" + "=" * 70)

def save_results_to_file(results, health_ok, root_ok, gen_ok, connectivity_ok, public_ip):
    """Sauvegarde les résultats dans un fichier JSON"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"post_deployment_test_{timestamp}.json"
    
    report = {
        "test_date": timestamp,
        "api_url": "http://localhost:8000",
        "public_ip": public_ip,
        "summary": {
            "health_test": health_ok,
            "root_test": root_ok,
            "generation_test": gen_ok,
            "connectivity_test": connectivity_ok,
            "lm_arena_scenarios_passed": sum(1 for r in results if r.get("success", False)),
            "lm_arena_scenarios_total": len(results)
        },
        "lm_arena_scenarios": results,
        "recommendations": {
            "lm_arena_ready": (health_ok and root_ok and gen_ok and connectivity_ok and 
                              all(r.get("success", False) for r in results)),
            "base_url": f"http://{public_ip}:8000" if public_ip else "N/A",
            "endpoint": "/generate",
            "method": "POST"
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Rapport sauvegardé dans: {filename}")
    return filename

def main():
    """Fonction principale"""
    print("=" * 70)
    print("TEST POST-DEPLOIEMENT - DEEPSEEK HARMONIC V2 API")
    print("=" * 70)
    print("Ce script teste l'API après déploiement sur EC2")
    print("Assurez-vous que l'API est démarrée avant d'exécuter ce test")
    print("=" * 70)
    print()
    
    # URL de l'API (localhost car exécuté sur l'instance EC2)
    api_url = "http://localhost:8000"
    
    print(f"URL de test: {api_url}")
    print()
    
    # Exécuter les tests
    health_ok, health_data = test_api_health(api_url)
    print()
    
    root_ok, root_data = test_api_root(api_url)
    print()
    
    gen_ok, gen_data = test_generation_simple(api_url)
    print()
    
    results, passed_scenarios, failed_scenarios = test_lm_arena_scenarios(api_url)
    print()
    
    connectivity_ok, public_ip = test_external_connectivity()
    print()
    
    # Générer le rapport
    generate_report(results, health_ok, root_ok, gen_ok, connectivity_ok, public_ip)
    
    # Sauvegarder les résultats
    report_file = save_results_to_file(results, health_ok, root_ok, gen_ok, connectivity_ok, public_ip)
    
    print("\n" + "=" * 70)
    print("PROCHAINES ETAPES:")
    print("1. Si tous les tests sont OK, l'API est prête pour LM Arena")
    print("2. Utilisez cette URL pour LM Arena: http://<IP_PUBLIQUE>:8000")
    print("3. Pour vérifier l'IP publique: curl -s ifconfig.me")
    print("4. Pour surveiller les logs: sudo journalctl -u deepseek-api -f")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nErreur lors de l'exécution du test: {e}")
        sys.exit(1)