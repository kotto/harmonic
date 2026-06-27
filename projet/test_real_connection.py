#!/usr/bin/env python3
"""
🧪 TEST CONNEXION RÉELLE - DEEPSEEK HARMONIC V2
Test complet de l'API après déploiement de la version locale
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import concurrent.futures

class RealConnectionTester:
    """Testeur de connexion réelle"""
    
    def __init__(self):
        self.base_url = "http://54.81.62.140:8000"
        self.test_timeout = 30
        self.results = {
            "tests": [],
            "summary": {},
            "timestamp": datetime.now().isoformat()
        }
        
    def test_health_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint health"""
        print("🏥 Test endpoint /health...")
        
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.test_timeout
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = data.get("status", "unknown")
                    
                    print(f"  ✅ Health OK: {status} ({elapsed:.2f}s)")
                    
                    return {
                        "test": "health",
                        "status": "passed",
                        "response_time": elapsed,
                        "data": data,
                        "message": f"Health check successful: {status}"
                    }
                    
                except json.JSONDecodeError:
                    print(f"  ⚠️ Health retourne non-JSON: {response.text[:100]}")
                    
                    return {
                        "test": "health",
                        "status": "warning",
                        "response_time": elapsed,
                        "data": {"raw_response": response.text[:200]},
                        "message": "Health check returned non-JSON response"
                    }
            else:
                print(f"  ❌ Health échoué: HTTP {response.status_code}")
                
                return {
                    "test": "health",
                    "status": "failed",
                    "response_time": elapsed,
                    "data": {"status_code": response.status_code},
                    "message": f"Health check failed with HTTP {response.status_code}"
                }
                
        except requests.Timeout:
            elapsed = time.time() - start_time
            print(f"  ❌ Health timeout après {elapsed:.2f}s")
            
            return {
                "test": "health",
                "status": "failed",
                "response_time": elapsed,
                "data": {},
                "message": "Health check timeout"
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Health erreur: {e}")
            
            return {
                "test": "health",
                "status": "failed",
                "response_time": elapsed,
                "data": {"error": str(e)},
                "message": f"Health check error: {e}"
            }
    
    def test_root_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint racine"""
        print("🌐 Test endpoint / (racine)...")
        
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/",
                timeout=self.test_timeout
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    message = data.get("message", "No message")
                    
                    print(f"  ✅ Racine OK: {message[:50]}... ({elapsed:.2f}s)")
                    
                    return {
                        "test": "root",
                        "status": "passed",
                        "response_time": elapsed,
                        "data": data,
                        "message": f"Root endpoint successful"
                    }
                    
                except json.JSONDecodeError:
                    print(f"  ⚠️ Racine retourne non-JSON")
                    
                    return {
                        "test": "root",
                        "status": "warning",
                        "response_time": elapsed,
                        "data": {"raw_response": response.text[:200]},
                        "message": "Root endpoint returned non-JSON"
                    }
            else:
                print(f"  ❌ Racine échoué: HTTP {response.status_code}")
                
                return {
                    "test": "root",
                    "status": "failed",
                    "response_time": elapsed,
                    "data": {"status_code": response.status_code},
                    "message": f"Root endpoint failed with HTTP {response.status_code}"
                }
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Racine erreur: {e}")
            
            return {
                "test": "root",
                "status": "failed",
                "response_time": elapsed,
                "data": {"error": str(e)},
                "message": f"Root endpoint error: {e}"
            }
    
    def test_info_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint info"""
        print("📊 Test endpoint /info...")
        
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/info",
                timeout=self.test_timeout
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    model_name = data.get("name", "Unknown")
                    version = data.get("version", "Unknown")
                    
                    print(f"  ✅ Info OK: {model_name} v{version} ({elapsed:.2f}s)")
                    
                    # Vérifier que ce n'est pas une version mock
                    is_mock = any([
                        "mock" in str(data).lower(),
                        "generated response" in str(data).lower()
                    ])
                    
                    if is_mock:
                        print(f"  ⚠️ Version MOCK détectée dans /info")
                        
                        return {
                            "test": "info",
                            "status": "failed",
                            "response_time": elapsed,
                            "data": data,
                            "message": "Info endpoint returns mock version"
                        }
                    else:
                        return {
                            "test": "info",
                            "status": "passed",
                            "response_time": elapsed,
                            "data": data,
                            "message": f"Info endpoint successful: {model_name} v{version}"
                        }
                    
                except json.JSONDecodeError:
                    print(f"  ⚠️ Info retourne non-JSON")
                    
                    return {
                        "test": "info",
                        "status": "warning",
                        "response_time": elapsed,
                        "data": {"raw_response": response.text[:200]},
                        "message": "Info endpoint returned non-JSON"
                    }
            else:
                print(f"  ❌ Info échoué: HTTP {response.status_code}")
                
                return {
                    "test": "info",
                    "status": "failed",
                    "response_time": elapsed,
                    "data": {"status_code": response.status_code},
                    "message": f"Info endpoint failed with HTTP {response.status_code}"
                }
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Info erreur: {e}")
            
            return {
                "test": "info",
                "status": "failed",
                "response_time": elapsed,
                "data": {"error": str(e)},
                "message": f"Info endpoint error: {e}"
            }
    
    def test_generate_endpoint(self, prompt: str, test_name: str) -> Dict[str, Any]:
        """Teste l'endpoint generate avec un prompt spécifique"""
        print(f"🧠 Test {test_name}: {prompt[:40]}...")
        
        start_time = time.time()
        
        try:
            payload = {
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.7,
                "use_evolution": True,
                "deepseek_harmonic": True
            }
            
            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=self.test_timeout
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Vérifications importantes
                    is_mock = any([
                        "Generated response for:" in content,
                        "mock" in content.lower(),
                        "[Deepseek" in content and "]" in content and "|" in content
                    ])
                    
                    is_real = any([
                        "Solution Python" in content,
                        "```python" in content,
                        "équation" in content.lower(),
                        "explication" in content.lower(),
                        "analyse harmonique" in content.lower()
                    ])
                    
                    response_length = len(content)
                    
                    if is_mock:
                        print(f"  ❌ {test_name}: Réponse MOCK détectée")
                        
                        return {
                            "test": f"generate_{test_name}",
                            "status": "failed",
                            "response_time": elapsed,
                            "data": {"content_preview": content[:100]},
                            "message": f"Generate endpoint returns mock response for {test_name}",
                            "is_mock": True,
                            "response_length": response_length
                        }
                    elif is_real:
                        print(f"  ✅ {test_name}: Réponse RÉELLE ({response_length} chars, {elapsed:.2f}s)")
                        
                        return {
                            "test": f"generate_{test_name}",
                            "status": "passed",
                            "response_time": elapsed,
                            "data": {"content_preview": content[:100]},
                            "message": f"Generate endpoint returns real response for {test_name}",
                            "is_mock": False,
                            "response_length": response_length
                        }
                    else:
                        print(f"  ⚠️ {test_name}: Réponse indéterminée ({response_length} chars)")
                        
                        return {
                            "test": f"generate_{test_name}",
                            "status": "warning",
                            "response_time": elapsed,
                            "data": {"content_preview": content[:100]},
                            "message": f"Generate endpoint returns indeterminate response for {test_name}",
                            "is_mock": None,
                            "response_length": response_length
                        }
                    
                except json.JSONDecodeError:
                    print(f"  ❌ {test_name}: Réponse non-JSON")
                    
                    return {
                        "test": f"generate_{test_name}",
                        "status": "failed",
                        "response_time": elapsed,
                        "data": {"raw_response": response.text[:200]},
                        "message": f"Generate endpoint returned non-JSON for {test_name}",
                        "is_mock": None,
                        "response_length": len(response.text)
                    }
            else:
                print(f"  ❌ {test_name}: HTTP {response.status_code}")
                
                return {
                    "test": f"generate_{test_name}",
                    "status": "failed",
                    "response_time": elapsed,
                    "data": {"status_code": response.status_code},
                    "message": f"Generate endpoint failed with HTTP {response.status_code} for {test_name}",
                    "is_mock": None,
                    "response_length": 0
                }
                
        except requests.Timeout:
            elapsed = time.time() - start_time
            print(f"  ❌ {test_name}: Timeout après {elapsed:.2f}s")
            
            return {
                "test": f"generate_{test_name}",
                "status": "failed",
                "response_time": elapsed,
                "data": {},
                "message": f"Generate endpoint timeout for {test_name}",
                "is_mock": None,
                "response_length": 0
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ {test_name}: Erreur {e}")
            
            return {
                "test": f"generate_{test_name}",
                "status": "failed",
                "response_time": elapsed,
                "data": {"error": str(e)},
                "message": f"Generate endpoint error for {test_name}: {e}",
                "is_mock": None,
                "response_length": 0
            }
    
    def run_lm_arena_tests(self) -> List[Dict[str, Any]]:
        """Exécute les tests LM Arena"""
        print("\n🏆 TESTS LM ARENA")
        print("=" * 40)
        
        test_cases = [
            {
                "name": "reasoning",
                "prompt": "If a train leaves Paris at 8:00 AM traveling at 120 km/h, and another train leaves Lyon at 8:30 AM traveling at 150 km/h towards Paris, when will they meet if the distance between Paris and Lyon is 450 km?"
            },
            {
                "name": "coding",
                "prompt": "Write a Python function to find the longest palindrome substring in a given string. Optimize for time complexity."
            },
            {
                "name": "mathematics",
                "prompt": "Calculate the integral of x^2 * sin(x) from 0 to pi. Show step-by-step solution."
            },
            {
                "name": "science",
                "prompt": "Explain the difference between classical mechanics and quantum mechanics in simple terms."
            },
            {
                "name": "creativity",
                "prompt": "Write a short story about an AI that discovers it has emotions."
            }
        ]
        
        results = []
        
        # Exécuter les tests en parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_test = {
                executor.submit(self.test_generate_endpoint, tc["prompt"], tc["name"]): tc
                for tc in test_cases
            }
            
            for future in concurrent.futures.as_completed(future_to_test):
                test_case = future_to_test[future]
                try:
                    result = future.result(timeout=45)
                    results.append(result)
                except Exception as e:
                    print(f"❌ Test {test_case['name']} exception: {e}")
                    
                    results.append({
                        "test": f"generate_{test_case['name']}",
                        "status": "failed",
                        "response_time": 0,
                        "data": {"error": str(e)},
                        "message": f"Test {test_case['name']} exception: {e}",
                        "is_mock": None,
                        "response_length": 0
                    })
        
        return results
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyse les résultats des tests"""
        print("\n📊 ANALYSE DES RÉSULTATS")
        print("=" * 40)
        
        # Compter les résultats
        total_tests = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"] if t["status"] == "passed")
        failed = sum(1 for t in self.results["tests"] if t["status"] == "failed")
        warnings = sum(1 for t in self.results["tests"] if t["status"] == "warning")
        
        # Analyser les réponses generate
        generate_tests = [t for t in self.results["tests"] if t["test"].startswith("generate_")]
        mock_responses = sum(1 for t in generate_tests if t.get("is_mock") == True)
        real_responses = sum(1 for t in generate_tests if t.get("is_mock") == False)
        indeterminate = sum(1 for t in generate_tests if t.get("is_mock") is None)
        
        # Calculer les temps de réponse
        response_times = [t["response_time"] for t in self.results["tests"] if "response_time" in t]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Calculer le score LM Arena
        if generate_tests:
            # Score basé sur la qualité des réponses
            quality_score = (real_responses / len(generate_tests)) * 100
            speed_score = max(0, 100 - (avg_response_time * 10))  # Pénalité pour temps > 10s
            reliability_score = (passed / total_tests) * 100
            
            lm_arena_score = (quality_score * 0.5) + (speed_score * 0.3) + (reliability_score * 0.2)
        else:
            lm_arena_score = 0
        
        analysis = {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "generate_tests": len(generate_tests),
            "mock_responses": mock_responses,
            "real_responses": real_responses,
            "indeterminate_responses": indeterminate,
            "response_times": {
                "average": avg_response_time,
                "max": max_response_time,
                "min": min_response_time,
                "count": len(response_times)
            },
            "lm_arena_score": lm_arena_score,
            "lm_arena_grade": self._get_grade(lm_arena_score),
            "recommendations": self._get_recommendations(mock_responses, real_responses, avg_response_time)
        }
        
        # Afficher l'analyse
        print(f"📈 Résumé des tests:")
        print(f"  • Total: {total_tests}")
        print(f"  • Réussis: {passed} ({analysis['success_rate']:.1f}%)")
        print(f"  • Échoués: {failed}")
        print(f"  • Avertissements: {warnings}")
        
        print(f"\n📊 Analyse des réponses:")
        print(f"  • Réponses réelles: {real_responses}/{len(generate_tests)}")
        print(f"  • Réponses mock: {mock_responses}/{len(generate_tests)}")
        print(f"  • Indéterminées: {indeterminate}/{len(generate_tests)}")
        
        print(f"\n⏱️  Performance:")
        print(f"  • Temps moyen: {avg_response_time:.2f}s")
        print(f"  • Temps max: {max_response_time:.2f}s")
        print(f"  • Temps min: {min_response_time:.2f}s")
        
        print(f"\n🏆 Score LM Arena: {lm_arena_score:.3f} ({analysis['lm_arena_grade']})")
        
        print(f"\n💡 Recommandations:")
        for rec in analysis["recommendations"]:
            print(f"  • {rec}")
        
        return analysis
    
    def _get_grade(self, score: float) -> str:
        """Convertit un score en grade"""
        if score >= 95:
            return "A++"
        elif score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "C+"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _get_recommendations(self, mock: int, real: int, avg_time: float) -> List[str]:
        """Génère des recommandations basées sur les résultats"""
        recommendations = []
        
        if mock > 0:
            recommendations.append("L'API retourne encore des réponses mock. Exécutez 'python enable_real_api.py' pour activer les réponses réelles.")
        
        if real == 0 and mock == 0:
            recommendations.append("Aucune réponse réelle détectée. Vérifiez le déploiement avec 'python deploy_local_to_ec2.py'.")
        
        if avg_time > 5:
            recommendations.append(f"Temps de réponse élevé ({avg_time:.2f}s). Vérifiez la performance de l'instance EC2.")
        
        if real > 0:
            recommendations.append("L'API retourne des réponses réelles. Prêt pour les tests LM Arena!")
        
        if not recommendations:
            recommendations.append("Tous les tests passent. L'API est opérationnelle.")
        
        return recommendations
    
    def save_results(self, filename: str = "lm_arena_real_test_results.json"):
        """Sauvegarde les résultats dans un fichier JSON"""
        output_file = filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvegardés dans: {output_file}")
        return output_file
    
    def run_complete_test(self) -> bool:
        """Exécute le test complet"""
        print("=" * 60)
        print("🧪 TEST COMPLET CONNEXION RÉELLE - DEEPSEEK HARMONIC V2")
        print("=" * 60)
        
        print(f"\n🌐 URL de test: {self.base_url}")
        print(f"⏱️  Timeout: {self.test_timeout}s")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Exécuter les tests de base
        print("\n🔧 TESTS DE BASE")
        print("-" * 30)
        
        basic_tests = [
            self.test_health_endpoint,
            self.test_root_endpoint,
            self.test_info_endpoint
        ]
        
        for test_func in basic_tests:
            result = test_func()
            self.results["tests"].append(result)
        
        # Vérifier si les tests de base ont réussi
        basic_failed = any(t["status"] == "failed" for t in self.results["tests"])
        
        if basic_failed:
            print("\n❌ Tests de base échoués. Arrêt des tests avancés.")
            self.results["summary"] = {"status": "basic_tests_failed"}
            return False
        
        # Exécuter les tests LM Arena
        lm_arena_results = self.run_lm_arena_tests()
        self.results["tests"].extend(lm_arena_results)
        
        # Analyser les résultats
        analysis = self.analyze_results()
        self.results["summary"] = analysis
        
        # Sauvegarder les résultats
        results_file = self.save_results()
        
        # Résumé final
        print("\n" + "=" * 60)
        print("🎯 TEST COMPLET TERMINÉ")
        print("=" * 60)
        
        print(f"\n📊 Score final: {analysis['lm_arena_score']:.3f} ({analysis['lm_arena_grade']})")
        print(f"📈 Taux de réussite: {analysis['success_rate']:.1f}%")
        print(f"📄 Fichier résultats: {results_file}")
        
        if analysis["real_responses"] > 0:
            print("\n✅ L'API retourne des réponses RÉELLES!")
            print("   Prêt pour la soumission LM Arena.")
            return True
        else:
            print("\n❌ L'API retourne encore des réponses MOCK.")
            print("   Exécutez 'python enable_real_api.py' pour activer les réponses réelles.")
            return False

def main():
    """Fonction principale"""
    tester = RealConnectionTester()
    
    try:
        success = tester.run_complete_test()
        
        print("\n📋 Étapes suivantes:")
        if success:
            print("1. ✅ L'API est prête pour les tests LM Arena")
            print("2. 🧪 Exécutez les tests complets avec 'python final_test_script.py'")
            print("3. 🏆 Soumettez les résultats à LM Arena")
        else:
            print("1. 🔧 Résolvez les problèmes de connexion avec 'python prepare_ssh_connection.py'")
            print("2. 🚀 Déployez la version locale avec 'python deploy_local_to_ec2.py'")
            print("3. 🔧 Activez les réponses réelles avec 'python enable_real_api.py'")
            print("4. 🧪 Retestez avec 'python test_real_connection.py'")
        
        return success
        
    except KeyboardInterrupt:
        print("\n❌ Test interrompu par l'utilisateur")
        return False
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)