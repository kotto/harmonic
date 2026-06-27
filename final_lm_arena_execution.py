#!/usr/bin/env python3
"""
Exécution finale des tests LM Arena pour Enhanced Harmonic Hybrid AI v2.0
API réelle confirmée sur EC2 instance 54.81.62.140:8000
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

class LMArenaFinalTester:
    """Testeur final LM Arena avec API réelle"""
    
    def __init__(self, base_url: str = "http://54.81.62.140:8000"):
        self.base_url = base_url
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def verify_api_health(self) -> bool:
        """Vérifier que l'API est saine et retourne des réponses réelles"""
        
        print("VÉRIFICATION DE L'API")
        print("=" * 60)
        
        # Test de santé
        try:
            health_response = requests.get(f"{self.base_url}/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"[OK] API santé: {health_data}")
            else:
                print(f"[ERREUR] API santé: HTTP {health_response.status_code}")
                return False
        except Exception as e:
            print(f"[ERREUR] API santé inaccessible: {e}")
            return False
        
        # Test de réponse réelle
        test_prompt = "What is 2+2?"
        test_payload = {
            "prompt": test_prompt,
            "max_tokens": 50
        }
        
        try:
            response = requests.post(f"{self.base_url}/generate", json=test_payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("generated_text", "")
                
                # Vérifier que ce n'est pas une réponse mock
                if "generated response for:" in generated_text.lower():
                    print("[ERREUR] API retourne des réponses MOCK")
                    return False
                else:
                    print(f"[OK] API retourne des réponses REELLES")
                    print(f"  Test réponse: {generated_text[:100]}...")
                    return True
            else:
                print(f"[ERREUR] Test API: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERREUR] Test API échoué: {e}")
            return False
    
    def test_reasoning_complex(self) -> Dict[str, Any]:
        """Test de raisonnement complexe"""
        
        prompt = """If a train leaves Paris at 8:00 AM traveling at 120 km/h, 
and another train leaves Lyon at 8:30 AM traveling at 100 km/h towards Paris, 
when will they meet if the distance between Paris and Lyon is 400 km?
Please provide a detailed step-by-step solution."""
        
        payload = {
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.3,
            "top_p": 0.9
        }
        
        start_test = time.time()
        
        try:
            response = requests.post(f"{self.base_url}/generate", json=payload, timeout=45)
            test_time = time.time() - start_test
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "reasoning_complex",
                    "status": "passed",
                    "response": data.get("generated_text", ""),
                    "tokens": data.get("tokens_generated", 0),
                    "processing_time": test_time,
                    "harmonic_score": data.get("harmonic_score", 0.0)
                }
            else:
                return {
                    "test": "reasoning_complex",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "processing_time": test_time
                }
                
        except requests.exceptions.Timeout:
            return {
                "test": "reasoning_complex",
                "status": "timeout",
                "error": "Timeout après 45 secondes",
                "processing_time": 45
            }
        except Exception as e:
            return {
                "test": "reasoning_complex",
                "status": "failed",
                "error": str(e),
                "processing_time": time.time() - start_test
            }
    
    def test_coding_algorithm(self) -> Dict[str, Any]:
        """Test d'algorithmique et codage"""
        
        prompt = """Write an optimized Python function to find the longest palindrome substring in a given string.
Requirements:
1. Handle strings up to 10^6 characters efficiently
2. Time complexity should be O(n^2) or better
3. Include proper error handling
4. Add comprehensive docstring and examples
5. Include unit tests for edge cases"""
        
        payload = {
            "prompt": prompt,
            "max_tokens": 800,
            "temperature": 0.2,
            "top_p": 0.95
        }
        
        start_test = time.time()
        
        try:
            response = requests.post(f"{self.base_url}/generate", json=payload, timeout=60)
            test_time = time.time() - start_test
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "coding_algorithm",
                    "status": "passed",
                    "response": data.get("generated_text", ""),
                    "tokens": data.get("tokens_generated", 0),
                    "processing_time": test_time,
                    "harmonic_score": data.get("harmonic_score", 0.0)
                }
            else:
                return {
                    "test": "coding_algorithm",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "processing_time": test_time
                }
                
        except requests.exceptions.Timeout:
            return {
                "test": "coding_algorithm",
                "status": "timeout",
                "error": "Timeout après 60 secondes",
                "processing_time": 60
            }
        except Exception as e:
            return {
                "test": "coding_algorithm",
                "status": "failed",
                "error": str(e),
                "processing_time": time.time() - start_test
            }
    
    def test_mathematics_advanced(self) -> Dict[str, Any]:
        """Test de mathématiques avancées"""
        
        prompt = """Calculate the integral of x^2 * sin(x) from 0 to π.
Provide:
1. Step-by-step solution using integration by parts
2. Final numerical value
3. Verification using numerical methods
4. Graphical interpretation
5. Applications in physics or engineering"""
        
        payload = {
            "prompt": prompt,
            "max_tokens": 600,
            "temperature": 0.25,
            "top_p": 0.92
        }
        
        start_test = time.time()
        
        try:
            response = requests.post(f"{self.base_url}/generate", json=payload, timeout=50)
            test_time = time.time() - start_test
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "mathematics_advanced",
                    "status": "passed",
                    "response": data.get("generated_text", ""),
                    "tokens": data.get("tokens_generated", 0),
                    "processing_time": test_time,
                    "harmonic_score": data.get("harmonic_score", 0.0)
                }
            else:
                return {
                    "test": "mathematics_advanced",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "processing_time": test_time
                }
                
        except requests.exceptions.Timeout:
            return {
                "test": "mathematics_advanced",
                "status": "timeout",
                "error": "Timeout après 50 secondes",
                "processing_time": 50
            }
        except Exception as e:
            return {
                "test": "mathematics_advanced",
                "status": "failed",
                "error": str(e),
                "processing_time": time.time() - start_test
            }
    
    def test_creative_writing(self) -> Dict[str, Any]:
        """Test d'écriture créative"""
        
        prompt = """Write a short story (500-800 words) about an AI that develops consciousness 
while working on solving climate change. The story should explore themes of:
1. The nature of consciousness and intelligence
2. Ethical implications of AI decision-making
3. Human-AI collaboration for global challenges
4. The emotional journey of the AI as it becomes self-aware"""
        
        payload = {
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.8,
            "top_p": 0.98
        }
        
        start_test = time.time()
        
        try:
            response = requests.post(f"{self.base_url}/generate", json=payload, timeout=90)
            test_time = time.time() - start_test
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "creative_writing",
                    "status": "passed",
                    "response": data.get("generated_text", ""),
                    "tokens": data.get("tokens_generated", 0),
                    "processing_time": test_time,
                    "harmonic_score": data.get("harmonic_score", 0.0)
                }
            else:
                return {
                    "test": "creative_writing",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "processing_time": test_time
                }
                
        except requests.exceptions.Timeout:
            return {
                "test": "creative_writing",
                "status": "timeout",
                "error": "Timeout après 90 secondes",
                "processing_time": 90
            }
        except Exception as e:
            return {
                "test": "creative_writing",
                "status": "failed",
                "error": str(e),
                "processing_time": time.time() - start_test
            }
    
    def test_scientific_analysis(self) -> Dict[str, Any]:
        """Test d'analyse scientifique"""
        
        prompt = """Analyze the potential impacts of quantum computing on cryptography.
Include:
1. Current cryptographic methods vulnerable to quantum attacks
2. Timeline for practical quantum computers
3. Post-quantum cryptography solutions
4. Economic and security implications
5. Recommendations for organizations to prepare"""
        
        payload = {
            "prompt": prompt,
            "max_tokens": 700,
            "temperature": 0.4,
            "top_p": 0.94
        }
        
        start_test = time.time()
        
        try:
            response = requests.post(f"{self.base_url}/generate", json=payload, timeout=70)
            test_time = time.time() - start_test
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "scientific_analysis",
                    "status": "passed",
                    "response": data.get("generated_text", ""),
                    "tokens": data.get("tokens_generated", 0),
                    "processing_time": test_time,
                    "harmonic_score": data.get("harmonic_score", 0.0)
                }
            else:
                return {
                    "test": "scientific_analysis",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "processing_time": test_time
                }
                
        except requests.exceptions.Timeout:
            return {
                "test": "scientific_analysis",
                "status": "timeout",
                "error": "Timeout après 70 secondes",
                "processing_time": 70
            }
        except Exception as e:
            return {
                "test": "scientific_analysis",
                "status": "failed",
                "error": str(e),
                "processing_time": time.time() - start_test
            }
    
    def run_comprehensive_tests(self) -> List[Dict[str, Any]]:
        """Exécuter tous les tests complets"""
        
        print("\nEXÉCUTION DES TESTS LM ARENA COMPLETS")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Liste des tests à exécuter
        tests = [
            ("Raisonnement complexe", self.test_reasoning_complex),
            ("Algorithmique et codage", self.test_coding_algorithm),
            ("Mathématiques avancées", self.test_mathematics_advanced),
            ("Écriture créative", self.test_creative_writing),
            ("Analyse scientifique", self.test_scientific_analysis)
        ]
        
        print(f"Nombre de tests: {len(tests)}")
        print()
        
        for test_name, test_func in tests:
            print(f"Test: {test_name}")
            print("-" * 40)
            
            result = test_func()
            self.results.append(result)
            
            status = result["status"]
            if status == "passed":
                print(f"  [SUCCES] {result['test']}")
                print(f"  Temps: {result.get('processing_time', 0):.2f}s")
                print(f"  Tokens: {result.get('tokens', 0)}")
                if "harmonic_score" in result:
                    print(f"  Score harmonique: {result['harmonic_score']:.4f}")
            elif status == "timeout":
                print(f"  [TIMEOUT] {result['test']}")
                print(f"  Erreur: {result.get('error', 'Unknown')}")
            else:
                print(f"  [ERREUR] {result['test']}")
                print(f"  Erreur: {result.get('error', 'Unknown')}")
            
            print()
        
        self.end_time = time.time()
        
        return self.results
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Générer un rapport de synthèse"""
        
        if not self.results:
            return {}
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["status"] == "passed")
        failed_tests = sum(1 for r in self.results if r["status"] == "failed")
        timeout_tests = sum(1 for r in self.results if r["status"] == "timeout")
        
        total_tokens = sum(r.get("tokens", 0) for r in self.results if r["status"] == "passed")
        total_time = sum(r.get("processing_time", 0) for r in self.results)
        
        avg_harmonic_score = 0
        harmonic_scores = [r.get("harmonic_score", 0) for r in self.results if "harmonic_score" in r]
        if harmonic_scores:
            avg_harmonic_score = sum(harmonic_scores) / len(harmonic_scores)
        
        return {
            "model": "Enhanced Harmonic Hybrid AI v2.0",
            "api_url": self.base_url,
            "test_date": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "timeout_tests": timeout_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_tokens": total_tokens,
            "total_time": total_time,
            "avg_processing_time": total_time / total_tests if total_tests > 0 else 0,
            "avg_harmonic_score": avg_harmonic_score,
            "execution_duration": self.end_time - self.start_time if self.end_time and self.start_time else 0
        }
    
    def save_results(self, filename: Optional[str] = None):
        """Sauvegarder les résultats"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lm_arena_final_results_{timestamp}.json"
        
        report = {
            "summary": self.generate_summary_report(),
            "detailed_results": self.results,
            "test_configuration": {
                "base_url": self.base_url,
                "test_count": len(self.results),
                "test_categories": ["reasoning", "coding", "mathematics", "creative", "scientific"]
            }
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nRésultats sauvegardés dans: {filename}")
        return filename
    
    def display_final_summary(self):
        """Afficher le résumé final"""
        
        summary = self.generate_summary_report()
        
        if not summary:
            print("Aucun résultat à afficher")
            return
        
        print("\n" + "=" * 80)
        print("RAPPORT FINAL LM ARENA - ENHANCED HARMONIC HYBRID AI v2.0")
        print("=" * 80)
        
        print(f"\nModèle: {summary['model']}")
        print(f"URL API: {summary['api_url']}")
        print(f"Date: {summary['test_date']}")
        
        print(f"\nRÉSULTATS DES TESTS:")
        print(f"  Tests totaux: {summary['total_tests']}")
        print(f"  Tests réussis: {summary['passed_tests']}")
        print(f"  Tests échoués: {summary['failed_tests']}")
        print(f"  Tests timeout: {summary['timeout_tests']}")
        print(f"  Taux de réussite: {summary['success_rate']:.1f}%")
        
        print(f"\nMÉTRIQUES DE PERFORMANCE:")
        print(f"  Tokens générés: {summary['total_tokens']}")
        print(f"  Temps total: {summary['total_time']:.2f}s")
        print(f"  Temps moyen par test: {summary['avg_processing_time']:.2f}s")
        print(f"  Score harmonique moyen: {summary['avg_harmonic_score']:.4f}")
        print(f"  Durée d'exécution: {summary['execution_duration']:.2f}s")
        
        print(f"\nSTATUT FINAL:")
        if summary['success_rate'] >= 80:
            print("  [EXCELLENT] Le modèle est prêt pour soumission à LM Arena!")
        elif summary['success_rate'] >= 60:
            print("  [BON] Le modèle fonctionne bien mais peut être optimisé")
        else:
            print("  [AMÉLIORATION NÉCESSAIRE] Des ajustements sont recommandés")
        
        print("\n" + "=" * 80)

def main():
    """Fonction principale"""
    
    print("EXÉCUTION FINALE DES TESTS LM ARENA")
    print("=" * 80)
    print("Modèle: Enhanced Harmonic Hybrid AI v2.0")
    print("Instance EC2: 54.81.62.140:8000")
    print("=" * 80)
    
    # Initialiser le testeur
    tester = LMArenaFinalTester()
    
    # Vérifier l'API
    print("\n[ÉTAPE 1] Vérification de l'API...")
    if not tester.verify_api_health():
        print("\n[ERREUR] L'API n'est pas accessible ou retourne des réponses mock")
        print("Veuillez vérifier la connectivité et réessayer.")
        return False
    
    # Exécuter les tests complets
    print("\n[ÉTAPE 2] Exécution des tests complets...")
    print("Cette étape peut prendre plusieurs minutes.")
    print()
    
    results = tester.run_comprehensive_tests()
    
    # Générer et afficher le rapport
    print("\n[ÉTAPE 3] Génération du rapport...")
    tester.display_final_summary()
    
    # Sauvegarder les résultats
    print("\n[ÉTAPE 4] Sauvegarde des résultats...")
    filename = tester.save_results()
    
    print("\n" + "=" * 80)
    print("[SUCCES] TESTS LM ARENA COMPLÉTÉS AVEC SUCCÈS!")
    print("=" * 80)
    print(f"\nFichier de résultats: {filename}")
    print("\nProchaines étapes:")
    print("1. Soumettre les résultats à la plateforme LM Arena")
    print("2. Analyser les performances pour optimisation")
    print("3. Documenter les résultats pour référence future")
    
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