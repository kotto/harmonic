#!/usr/bin/env python3
"""
LM ARENA FINAL - Tests complets avec l'API actuelle
Exécution simple et directe pour soumission LM Arena
"""

import requests
import json
import time
import sys
import os
import argparse
from datetime import datetime

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def _normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip()
    if not base_url:
        return ""
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = "http://" + base_url
    return base_url.rstrip("/")

def _resolve_base_url() -> str:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--base-url", default=os.getenv("LM_ARENA_BASE_URL", ""), help="Ex: http://54.81.62.140:8000")
    parser.add_argument("--ip", default=os.getenv("LM_ARENA_IP", ""), help="Ex: 54.81.62.140 (port 8000 implicite)")
    args = parser.parse_args()

    if args.base_url:
        base = _normalize_base_url(args.base_url)
    elif args.ip:
        base = _normalize_base_url(f"http://{args.ip}:8000")
    else:
        base = _normalize_base_url("http://localhost:8000")
    return base

BASE_URL = _resolve_base_url()
API_URL = f"{BASE_URL}/generate"
HEALTH_URL = f"{BASE_URL}/health"

def check_api_health():
    """Vérifier la santé de l'API"""
    
    print("Vérification de l'API...")
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] API saine - Version: {data.get('version', 'unknown')}")
            print(f"  Statut: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"  [ERREUR] HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERREUR] {e}")
        return False

def test_reasoning():
    """Test de raisonnement complexe"""
    
    prompt = """If a train leaves Paris at 8:00 AM traveling at 120 km/h, 
and another train leaves Lyon at 8:30 AM traveling at 100 km/h towards Paris, 
when will they meet if the distance between Paris and Lyon is 400 km?
Please provide a detailed step-by-step solution."""
    
    payload = {
        "prompt": prompt,
        "max_tokens": 500,
        "temperature": 0.2,
        "arena_mode": True
    }
    
    print("\nTest 1: Raisonnement complexe")
    print(f"  Prompt: {prompt[:80]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=45)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            generated_text = data.get("generated_text", data.get("content", ""))
            
            # Analyser la réponse
            is_mock = "generated response for:" in generated_text.lower()
            
            result = {
                "test": "reasoning_complex",
                "status": "passed_mock" if is_mock else "passed_real",
                "response_preview": generated_text[:200] + "..." if len(generated_text) > 200 else generated_text,
                "processing_time": processing_time,
                "tokens": len(generated_text.split()),
                "is_mock": is_mock
            }
            
            if is_mock:
                print(f"  [MOCK] Réponse générée en {processing_time:.2f}s")
            else:
                print(f"  [REAL] Réponse réelle en {processing_time:.2f}s")
            
            return result
            
        else:
            result = {
                "test": "reasoning_complex",
                "status": "failed",
                "error": f"HTTP {response.status_code}",
                "processing_time": processing_time
            }
            print(f"  [ERREUR] HTTP {response.status_code}")
            return result
            
    except requests.exceptions.Timeout:
        result = {
            "test": "reasoning_complex",
            "status": "timeout",
            "error": "Timeout après 45 secondes",
            "processing_time": 45
        }
        print(f"  [TIMEOUT] 45 secondes")
        return result
        
    except Exception as e:
        result = {
            "test": "reasoning_complex",
            "status": "failed",
            "error": str(e),
            "processing_time": time.time() - start_time
        }
        print(f"  [ERREUR] {e}")
        return result

def test_coding():
    """Test d'algorithmique et codage"""
    
    prompt = """Write an optimized Python function to find the longest palindrome substring in a given string.
Requirements:
1. Handle strings up to 10^6 characters efficiently
2. Time complexity should be O(n^2) or better
3. Include proper error handling
4. Add comprehensive docstring and examples"""
    
    payload = {
        "prompt": prompt,
        "max_tokens": 600,
        "temperature": 0.2,
        "arena_mode": True
    }
    
    print("\nTest 2: Algorithmique et codage")
    print(f"  Prompt: {prompt[:80]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            generated_text = data.get("generated_text", data.get("content", ""))
            
            is_mock = "generated response for:" in generated_text.lower()
            
            result = {
                "test": "coding_algorithm",
                "status": "passed_mock" if is_mock else "passed_real",
                "response_preview": generated_text[:200] + "..." if len(generated_text) > 200 else generated_text,
                "processing_time": processing_time,
                "tokens": len(generated_text.split()),
                "is_mock": is_mock
            }
            
            if is_mock:
                print(f"  [MOCK] Réponse générée en {processing_time:.2f}s")
            else:
                print(f"  [REAL] Réponse réelle en {processing_time:.2f}s")
            
            return result
            
        else:
            result = {
                "test": "coding_algorithm",
                "status": "failed",
                "error": f"HTTP {response.status_code}",
                "processing_time": processing_time
            }
            print(f"  [ERREUR] HTTP {response.status_code}")
            return result
            
    except requests.exceptions.Timeout:
        result = {
            "test": "coding_algorithm",
            "status": "timeout",
            "error": "Timeout après 60 secondes",
            "processing_time": 60
        }
        print(f"  [TIMEOUT] 60 secondes")
        return result
        
    except Exception as e:
        result = {
            "test": "coding_algorithm",
            "status": "failed",
            "error": str(e),
            "processing_time": time.time() - start_time
        }
        print(f"  [ERREUR] {e}")
        return result

def test_mathematics():
    """Test de mathématiques avancées"""
    
    prompt = """Calculate the integral of x^2 * sin(x) from 0 to pi.
Provide:
1. Step-by-step solution using integration by parts
2. Final numerical value
3. Verification using numerical methods"""
    
    payload = {
        "prompt": prompt,
        "max_tokens": 400,
        "temperature": 0.2,
        "arena_mode": True
    }
    
    print("\nTest 3: Mathématiques avancées")
    print(f"  Prompt: {prompt[:80]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=50)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            generated_text = data.get("generated_text", data.get("content", ""))
            
            is_mock = "generated response for:" in generated_text.lower()
            
            result = {
                "test": "mathematics_advanced",
                "status": "passed_mock" if is_mock else "passed_real",
                "response_preview": generated_text[:200] + "..." if len(generated_text) > 200 else generated_text,
                "processing_time": processing_time,
                "tokens": len(generated_text.split()),
                "is_mock": is_mock
            }
            
            if is_mock:
                print(f"  [MOCK] Réponse générée en {processing_time:.2f}s")
            else:
                print(f"  [REAL] Réponse réelle en {processing_time:.2f}s")
            
            return result
            
        else:
            result = {
                "test": "mathematics_advanced",
                "status": "failed",
                "error": f"HTTP {response.status_code}",
                "processing_time": processing_time
            }
            print(f"  [ERREUR] HTTP {response.status_code}")
            return result
            
    except requests.exceptions.Timeout:
        result = {
            "test": "mathematics_advanced",
            "status": "timeout",
            "error": "Timeout après 50 secondes",
            "processing_time": 50
        }
        print(f"  [TIMEOUT] 50 secondes")
        return result
        
    except Exception as e:
        result = {
            "test": "mathematics_advanced",
            "status": "failed",
            "error": str(e),
            "processing_time": time.time() - start_time
        }
        print(f"  [ERREUR] {e}")
        return result

def test_creative():
    """Test d'écriture créative"""
    
    prompt = """Write a short story (300-500 words) about an AI that develops consciousness 
while working on solving climate change. The story should explore themes of:
1. The nature of consciousness and intelligence
2. Ethical implications of AI decision-making
3. Human-AI collaboration for global challenges"""
    
    payload = {
        "prompt": prompt,
        "max_tokens": 800,
        "temperature": 0.8,
        "arena_mode": True
    }
    
    print("\nTest 4: Écriture créative")
    print(f"  Prompt: {prompt[:80]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=90)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            generated_text = data.get("generated_text", data.get("content", ""))
            
            is_mock = "generated response for:" in generated_text.lower()
            
            result = {
                "test": "creative_writing",
                "status": "passed_mock" if is_mock else "passed_real",
                "response_preview": generated_text[:200] + "..." if len(generated_text) > 200 else generated_text,
                "processing_time": processing_time,
                "tokens": len(generated_text.split()),
                "is_mock": is_mock
            }
            
            if is_mock:
                print(f"  [MOCK] Réponse générée en {processing_time:.2f}s")
            else:
                print(f"  [REAL] Réponse réelle en {processing_time:.2f}s")
            
            return result
            
        else:
            result = {
                "test": "creative_writing",
                "status": "failed",
                "error": f"HTTP {response.status_code}",
                "processing_time": processing_time
            }
            print(f"  [ERREUR] HTTP {response.status_code}")
            return result
            
    except requests.exceptions.Timeout:
        result = {
            "test": "creative_writing",
            "status": "timeout",
            "error": "Timeout après 90 secondes",
            "processing_time": 90
        }
        print(f"  [TIMEOUT] 90 secondes")
        return result
        
    except Exception as e:
        result = {
            "test": "creative_writing",
            "status": "failed",
            "error": str(e),
            "processing_time": time.time() - start_time
        }
        print(f"  [ERREUR] {e}")
        return result

def test_scientific():
    """Test d'analyse scientifique"""
    
    prompt = """Analyze the potential impacts of quantum computing on cryptography.
Include:
1. Current cryptographic methods vulnerable to quantum attacks
2. Timeline for practical quantum computers
3. Post-quantum cryptography solutions
4. Recommendations for organizations to prepare"""
    
    payload = {
        "prompt": prompt,
        "max_tokens": 700,
        "temperature": 0.3,
        "arena_mode": True
    }
    
    print("\nTest 5: Analyse scientifique")
    print(f"  Prompt: {prompt[:80]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=70)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            generated_text = data.get("generated_text", data.get("content", ""))
            
            is_mock = "generated response for:" in generated_text.lower()
            
            result = {
                "test": "scientific_analysis",
                "status": "passed_mock" if is_mock else "passed_real",
                "response_preview": generated_text[:200] + "..." if len(generated_text) > 200 else generated_text,
                "processing_time": processing_time,
                "tokens": len(generated_text.split()),
                "is_mock": is_mock
            }
            
            if is_mock:
                print(f"  [MOCK] Réponse générée en {processing_time:.2f}s")
            else:
                print(f"  [REAL] Réponse réelle en {processing_time:.2f}s")
            
            return result
            
        else:
            result = {
                "test": "scientific_analysis",
                "status": "failed",
                "error": f"HTTP {response.status_code}",
                "processing_time": processing_time
            }
            print(f"  [ERREUR] HTTP {response.status_code}")
            return result
            
    except requests.exceptions.Timeout:
        result = {
            "test": "scientific_analysis",
            "status": "timeout",
            "error": "Timeout après 70 secondes",
            "processing_time": 70
        }
        print(f"  [TIMEOUT] 70 secondes")
        return result
        
    except Exception as e:
        result = {
            "test": "scientific_analysis",
            "status": "failed",
            "error": str(e),
            "processing_time": time.time() - start_time
        }
        print(f"  [ERREUR] {e}")
        return result

def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("LM ARENA FINAL TESTS - ENHANCED HARMONIC HYBRID AI v2.0")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"Generate: {API_URL}")
    print(f"Health: {HEALTH_URL}")
    print("=" * 80)
    
    # Vérifier la santé de l'API
    if not check_api_health():
        print("\n[ERREUR] L'API n'est pas accessible")
        return False
    
    # Exécuter tous les tests
    tests = [
        test_reasoning,
        test_coding,
        test_mathematics,
        test_creative,
        test_scientific
    ]
    
    results = []
    start_time = time.time()
    
    print("\n" + "=" * 80)
    print("EXÉCUTION DES TESTS")
    print("=" * 80)
    
    for test_func in tests:
        result = test_func()
        results.append(result)
    
    # Calculer les statistiques
    total_time = time.time() - start_time
    
    passed_mock = sum(1 for r in results if r["status"] == "passed_mock")
    passed_real = sum(1 for r in results if r["status"] == "passed_real")
    failed = sum(1 for r in results if r["status"] == "failed")
    timeout = sum(1 for r in results if r["status"] == "timeout")
    
    total_tests = len(results)
    total_passed = passed_mock + passed_real
    
    # Afficher le résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    print(f"Tests totaux: {total_tests}")
    print(f"Tests réussis (mock): {passed_mock}")
    print(f"Tests réussis (réel): {passed_real}")
    print(f"Tests échoués: {failed}")
    print(f"Tests timeout: {timeout}")
    print(f"Taux de réussite: {(total_passed / total_tests * 100):.1f}%")
    print(f"Temps total: {total_time:.2f}s")
    
    # Déterminer le type d'API
    if passed_real > 0:
        api_type = "REAL"
        readiness = "PRÊT POUR LM ARENA"
    elif passed_mock > 0:
        api_type = "MOCK"
        readiness = "TESTS LIMITÉS - DÉPLOIEMENT RÉEL RECOMMANDÉ"
    else:
        api_type = "INACCESSIBLE"
        readiness = "ACTION REQUISE"
    
    print(f"\nType d'API: {api_type}")
    print(f"Statut: {readiness}")
    
    # Sauvegarder les résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lm_arena_final_results_{timestamp}.json"
    
    report = {
        "model": "Enhanced Harmonic Hybrid AI v2.0",
        "api_url": API_URL,
        "test_date": datetime.now().isoformat(),
        "api_type": api_type.lower(),
        "total_tests": total_tests,
        "passed_mock": passed_mock,
        "passed_real": passed_real,
        "failed": failed,
        "timeout": timeout,
        "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
        "total_time": total_time,
        "detailed_results": results,
        "summary": {
            "lm_arena_ready": passed_real >= 3,
            "recommendations": [
                "Soumettre les résultats à LM Arena",
                "Optimiser les paramètres de génération",
                "Documenter les performances"
            ]
        }
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nRésultats sauvegardés dans: {filename}")
    
    # Afficher les recommandations
    print("\n" + "=" * 80)
    print("RECOMMANDATIONS")
    print("=" * 80)
    
    if passed_real >= 3:
        print("1. [SUCCES] L'API est prête pour soumission à LM Arena")
        print("2. Soumettre le fichier de résultats à la plateforme")
        print("3. Documenter les performances pour référence future")
    elif passed_mock >= 3:
        print("1. [AVERTISSEMENT] L'API retourne des réponses MOCK")
        print("2. Pour des tests complets, déployer la version réelle:")
        print("   - Utiliser SSH pour transférer deepseek_api_real_final.py")
        print("   - Installer les dépendances: pip install fastapi uvicorn pydantic")
        print("   - Démarrer l'API: python deepseek_api_real_final.py")
    else:
        print("1. [ERREUR] L'API n'est pas fonctionnelle")
        print("2. Vérifier la connectivité réseau")
        print("3. Vérifier que l'instance EC2 est démarrée")
        print("4. Contacter le support technique si nécessaire")
    
    print("\n" + "=" * 80)
    print("EXÉCUTION TERMINÉE")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERREUR] Exception non gérée: {e}")
        sys.exit(1)
