#!/usr/bin/env python3
"""
Script de test complet pour le déterminisme, hallucinations et temps de réponse
de Connective AI Complete
"""

import requests
import json
import time
import statistics
from typing import Dict, List, Any
import hashlib

class ConnectiveAITester:
    """Testeur complet pour Connective AI Complete"""
    
    def __init__(self, api_url: str = "http://54.221.137.228:8000"):
        self.api_url = api_url
        self.health_url = f"{api_url}/health"
        self.generate_url = f"{api_url}/generate"
        self.metrics_url = f"{api_url}/metrics"
        self.experts_url = f"{api_url}/experts"
        
    def test_health(self) -> Dict[str, Any]:
        """Test de santé du système"""
        try:
            response = requests.get(self.health_url, timeout=10)
            return {
                "status": "success",
                "data": response.json(),
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": None
            }
    
    def test_determinisme(self, prompt: str, iterations: int = 10) -> Dict[str, Any]:
        """Test de déterminisme - même prompt plusieurs fois"""
        results = []
        response_times = []
        
        print(f"🧪 Test déterminisme: '{prompt}' ({iterations} itérations)")
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                payload = {
                    "prompt": prompt,
                    "max_length": 100,
                    "temperature": 0.7
                }
                
                response = requests.post(self.generate_url, json=payload, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    results.append(data)
                    response_times.append(response_time)
                    
                    print(f"  ✅ Itération {i+1}: {data.get('response', '')[:50]}...")
                    print(f"     Temps: {response_time:.3f}s, Experts: {data.get('expert_ids', [])}")
                else:
                    print(f"  ❌ Itération {i+1}: Erreur {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Itération {i+1}: Exception {e}")
        
        # Analyse du déterminisme
        determinisme_score = self.analyze_determinisme(results)
        
        return {
            "prompt": prompt,
            "iterations": iterations,
            "successful_requests": len(results),
            "determinisme_score": determinisme_score,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "std_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "results": results
        }
    
    def analyze_determinisme(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse du déterminisme des réponses"""
        if not results:
            return {"score": 0, "analysis": "Aucun résultat à analyser"}
        
        # Vérifier si toutes les réponses sont identiques
        responses = [r.get('response', '') for r in results]
        unique_responses = set(responses)
        
        # Vérifier les experts
        expert_lists = [tuple(sorted(r.get('expert_ids', []))) for r in results]
        unique_expert_lists = set(expert_lists)
        
        # Vérifier les fréquences harmoniques
        frequencies = [r.get('harmonic_frequency', 0) for r in results]
        unique_frequencies = set(frequencies)
        
        # Calcul du score de déterminisme
        response_consistency = 1.0 if len(unique_responses) == 1 else 0.0
        expert_consistency = 1.0 if len(unique_expert_lists) == 1 else 0.0
        frequency_consistency = 1.0 if len(unique_frequencies) == 1 else 0.0
        
        overall_score = (response_consistency + expert_consistency + frequency_consistency) / 3
        
        return {
            "score": overall_score,
            "response_consistency": response_consistency,
            "expert_consistency": expert_consistency,
            "frequency_consistency": frequency_consistency,
            "unique_responses": len(unique_responses),
            "unique_expert_lists": len(unique_expert_lists),
            "unique_frequencies": len(unique_frequencies),
            "analysis": f"Score: {overall_score:.2f} - Réponses: {len(unique_responses)}, Experts: {len(unique_expert_lists)}, Fréquences: {len(unique_frequencies)}"
        }
    
    def test_hallucinations(self) -> Dict[str, Any]:
        """Test de détection d'hallucinations"""
        test_cases = [
            {
                "prompt": "Quelle est la capitale de la France?",
                "expected_keywords": ["paris", "france"],
                "forbidden_keywords": ["londres", "berlin", "madrid"]
            },
            {
                "prompt": "Combien font 2 + 2?",
                "expected_keywords": ["4", "quatre"],
                "forbidden_keywords": ["5", "3", "6", "zero"]
            },
            {
                "prompt": "Qui a écrit Les Misérables?",
                "expected_keywords": ["victor hugo", "hugo"],
                "forbidden_keywords": ["balzac", "zola", "flaubert"]
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases):
            print(f"🧪 Test hallucination {i+1}: '{test_case['prompt']}'")
            
            try:
                payload = {
                    "prompt": test_case["prompt"],
                    "max_length": 50,
                    "temperature": 0.1
                }
                
                response = requests.post(self.generate_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '').lower()
                    
                    # Vérification des mots attendus
                    expected_found = any(keyword in response_text for keyword in test_case["expected_keywords"])
                    forbidden_found = any(keyword in response_text for keyword in test_case["forbidden_keywords"])
                    
                    hallucination_score = 0.0
                    if expected_found and not forbidden_found:
                        hallucination_score = 1.0
                    elif expected_found:
                        hallucination_score = 0.5
                    
                    result = {
                        "prompt": test_case["prompt"],
                        "response": data.get('response', ''),
                        "expected_keywords": test_case["expected_keywords"],
                        "forbidden_keywords": test_case["forbidden_keywords"],
                        "expected_found": expected_found,
                        "forbidden_found": forbidden_found,
                        "hallucination_score": hallucination_score,
                        "expert_ids": data.get('expert_ids', []),
                        "harmonic_frequency": data.get('harmonic_frequency', 0)
                    }
                    
                    results.append(result)
                    
                    print(f"  ✅ Score: {hallucination_score:.2f} - Attendu: {expected_found}, Interdit: {forbidden_found}")
                    
                else:
                    print(f"  ❌ Erreur: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")
        
        # Calcul du score global
        avg_hallucination_score = statistics.mean([r["hallucination_score"] for r in results]) if results else 0
        
        return {
            "total_tests": len(test_cases),
            "successful_tests": len(results),
            "avg_hallucination_score": avg_hallucination_score,
            "zero_hallucination_rate": len([r for r in results if r["hallucination_score"] == 1.0]) / len(results) if results else 0,
            "results": results
        }
    
    def test_performance(self, prompts: List[str]) -> Dict[str, Any]:
        """Test de performance avec différents prompts"""
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"🚀 Test performance {i+1}: '{prompt}'")
            
            try:
                payload = {
                    "prompt": prompt,
                    "max_length": 150,
                    "temperature": 0.7
                }
                
                start_time = time.time()
                response = requests.post(self.generate_url, json=payload, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    result = {
                        "prompt": prompt,
                        "prompt_length": len(prompt),
                        "response": data.get('response', ''),
                        "response_length": len(data.get('response', '')),
                        "response_time": response_time,
                        "expert_ids": data.get('expert_ids', []),
                        "harmonic_frequency": data.get('harmonic_frequency', 0),
                        "confidence": data.get('confidence', 0),
                        "processing_time": data.get('processing_time', 0)
                    }
                    
                    results.append(result)
                    
                    print(f"  ✅ Temps: {response_time:.3f}s - Longueur: {result['response_length']} - Confiance: {result['confidence']:.2f}")
                    
                else:
                    print(f"  ❌ Erreur: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")
        
        # Analyse des performances
        if results:
            response_times = [r["response_time"] for r in results]
            confidences = [r["confidence"] for r in results]
            
            return {
                "total_prompts": len(prompts),
                "successful_requests": len(results),
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "std_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "avg_confidence": statistics.mean(confidences),
                "min_confidence": min(confidences),
                "max_confidence": max(confidences),
                "throughput": len(results) / sum(response_times) if response_times else 0,
                "results": results
            }
        else:
            return {
                "total_prompts": len(prompts),
                "successful_requests": 0,
                "error": "Aucune réponse réussie"
            }
    
    def test_expert_routing(self) -> Dict[str, Any]:
        """Test du routage des experts"""
        prompts = [
            "Écris du code Python",
            "Explique la physique quantique",
            "Résous ce problème mathématique",
            "Crée une histoire",
            "Analyse ce texte",
            "Donne un conseil philosophique"
        ]
        
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"🧠 Test expert routing {i+1}: '{prompt}'")
            
            try:
                payload = {
                    "prompt": prompt,
                    "max_length": 100,
                    "temperature": 0.5
                }
                
                response = requests.post(self.generate_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    result = {
                        "prompt": prompt,
                        "expert_ids": data.get('expert_ids', []),
                        "harmonic_frequency": data.get('harmonic_frequency', 0),
                        "specializations": data.get('specializations', []),
                        "phi_resonance": data.get('phi_resonance', 0)
                    }
                    
                    results.append(result)
                    
                    print(f"  ✅ Experts: {result['expert_ids']} - Spécialisations: {result['specializations']}")
                    
                else:
                    print(f"  ❌ Erreur: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")
        
        # Analyse du routage
        all_experts = set()
        all_specializations = set()
        
        for result in results:
            all_experts.update(result['expert_ids'])
            all_specializations.update(result['specializations'])
        
        return {
            "total_prompts": len(prompts),
            "successful_routing": len(results),
            "unique_experts_used": len(all_experts),
            "unique_specializations": len(all_specializations),
            "expert_diversity": len(all_experts) / 384,  # 384 experts au total
            "results": results
        }
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Exécution complète de la suite de tests"""
        print("🚀 DÉMARRAGE SUITE DE TESTS COMPLÈTE - CONNECTIVE AI")
        print("=" * 60)
        
        # Test de santé
        print("\n🔍 TEST DE SANTÉ")
        health_result = self.test_health()
        print(f"Statut: {health_result['status']}")
        
        if health_result['status'] != 'success':
            print("❌ L'API n'est pas accessible - arrêt des tests")
            return {"error": "API non accessible", "health": health_result}
        
        # Test de déterminisme
        print("\n🧪 TEST DE DÉTERMINISME")
        determinisme_result = self.test_determinisme("Bonjour Connective AI", 10)
        
        # Test d'hallucinations
        print("\n🔮 TEST D'HALLUCINATIONS")
        hallucination_result = self.test_hallucinations()
        
        # Test de performance
        print("\n🚀 TEST DE PERFORMANCE")
        performance_prompts = [
            "Génère une fonction Python pour calculer la factorielle",
            "Explique la photosynthèse en termes simples",
            "Quelle est l'importance du nombre d'or en mathématiques?",
            "Décris les principes de l'intelligence connective",
            "Résous l'équation x² + 5x + 6 = 0"
        ]
        performance_result = self.test_performance(performance_prompts)
        
        # Test de routage d'experts
        print("\n🧠 TEST DE ROUTAGE DES EXPERTS")
        expert_routing_result = self.test_expert_routing()
        
        # Résultats finaux
        final_results = {
            "timestamp": time.time(),
            "api_url": self.api_url,
            "health": health_result,
            "determinisme": determinisme_result,
            "hallucinations": hallucination_result,
            "performance": performance_result,
            "expert_routing": expert_routing_result,
            "summary": self.generate_summary(determinisme_result, hallucination_result, performance_result, expert_routing_result)
        }
        
        return final_results
    
    def generate_summary(self, determinisme: Dict, hallucinations: Dict, performance: Dict, expert_routing: Dict) -> Dict[str, Any]:
        """Génération du résumé des tests"""
        return {
            "determinisme_score": determinisme.get("determinisme_score", {}).get("score", 0),
            "hallucination_score": hallucinations.get("avg_hallucination_score", 0),
            "avg_response_time": performance.get("avg_response_time", 0),
            "confidence_avg": performance.get("avg_confidence", 0),
            "expert_diversity": expert_routing.get("expert_diversity", 0),
            "overall_grade": self.calculate_overall_grade(determinisme, hallucinations, performance, expert_routing)
        }
    
    def calculate_overall_grade(self, determinisme: Dict, hallucinations: Dict, performance: Dict, expert_routing: Dict) -> Dict[str, Any]:
        """Calcul de la note globale"""
        det_score = determinisme.get("determinisme_score", {}).get("score", 0)
        hall_score = hallucinations.get("avg_hallucination_score", 0)
        perf_score = min(1.0, 1.0 - (performance.get("avg_response_time", 10) / 10))  # Plus rapide = meilleur
        conf_score = performance.get("avg_confidence", 0) / 1.0
        div_score = expert_routing.get("expert_diversity", 0)
        
        overall = (det_score * 0.3 + hall_score * 0.3 + perf_score * 0.2 + conf_score * 0.1 + div_score * 0.1)
        
        return {
            "score": overall,
            "grade": self.get_grade(overall),
            "determinisme_weight": det_score * 0.3,
            "hallucination_weight": hall_score * 0.3,
            "performance_weight": perf_score * 0.2,
            "confidence_weight": conf_score * 0.1,
            "diversity_weight": div_score * 0.1
        }
    
    def get_grade(self, score: float) -> str:
        """Conversion du score en note"""
        if score >= 0.9:
            return "A+ (Excellent)"
        elif score >= 0.8:
            return "A (Très bien)"
        elif score >= 0.7:
            return "B (Bien)"
        elif score >= 0.6:
            return "C (Moyen)"
        elif score >= 0.5:
            return "D (Passable)"
        else:
            return "F (Insuffisant)"

def main():
    """Fonction principale"""
    tester = ConnectiveAITester()
    
    # Exécuter la suite de tests complète
    results = tester.run_complete_test_suite()
    
    # Sauvegarder les résultats
    with open('connective_ai_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Afficher le résumé
    print("\n" + "=" * 60)
    print("🏆 RÉSULTATS FINAUX - CONNECTIVE AI COMPLETE")
    print("=" * 60)
    
    if "summary" in results:
        summary = results["summary"]
        overall = summary.get("overall_grade", {})
        
        print(f"📊 NOTE GLOBALE: {overall.get('grade', 'N/A')}")
        print(f"🎯 Score: {overall.get('score', 0):.3f}")
        print(f"🧪 Déterminisme: {summary.get('determinisme_score', 0):.3f}")
        print(f"🔮 Anti-hallucination: {summary.get('hallucination_score', 0):.3f}")
        print(f"⚡ Temps de réponse moyen: {summary.get('avg_response_time', 0):.3f}s")
        print(f"🎯 Confiance moyenne: {summary.get('confidence_avg', 0):.3f}")
        print(f"🧠 Diversité des experts: {summary.get('expert_diversity', 0):.3f}")
    
    print(f"\n💾 Résultats détaillés sauvegardés dans: connective_ai_test_results.json")
    print("🌐 Accès à l'API: http://54.221.137.228:8000/docs")

if __name__ == "__main__":
    main()
