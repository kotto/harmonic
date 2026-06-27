#!/usr/bin/env python3
"""
Tests LM Arena pour Connective AI Optimized
Validation pour score cible 0.980 (Top 3)
"""

import requests
import json
import time
import statistics
from typing import Dict, List, Any

class ConnectiveAITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_results = []
    
    def test_health(self) -> bool:
        """Test health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_determinism(self, prompt: str, iterations: int = 10) -> Dict[str, Any]:
        """Test de déterminisme"""
        print(f"🧪 Test déterminisme: '{prompt}' ({iterations} itérations)")
        
        results = []
        response_times = []
        
        for i in range(iterations):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/generate",
                    json={"prompt": prompt},
                    timeout=10
                )
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    results.append(result)
                    response_times.append(result.get("processing_time", processing_time))
                    print(f"  ✅ Itération {i+1}: {result['response'][:50]}...")
                    print(f"     Temps: {result['processing_time']:.3f}s, Cache: {result.get('from_cache', False)}")
                else:
                    print(f"  ❌ Itération {i+1}: Erreur {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Itération {i+1}: Exception {e}")
        
        # Analyse déterminisme
        if results:
            responses = [r["response"] for r in results]
            expert_lists = [tuple(sorted(r.get("harmonic_metadata", {}).get("expert_ids", []))) for r in results]
            
            response_consistency = 1.0 if len(set(responses)) == 1 else 0.0
            expert_consistency = 1.0 if len(set(expert_lists)) == 1 else 0.0
            
            overall_score = (response_consistency + expert_consistency) / 2
            
            return {
                "prompt": prompt,
                "iterations": iterations,
                "successful_requests": len(results),
                "determinism_score": overall_score,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "cache_hit_rate": sum(1 for r in results if r.get("from_cache", False)) / len(results),
                "results": results
            }
        
        return {"error": "No successful requests"}
    
    def test_performance(self, prompts: List[str]) -> Dict[str, Any]:
        """Test de performance"""
        print(f"🚀 Test performance: {len(prompts)} prompts")
        
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"  📝 Prompt {i+1}: '{prompt}'")
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/generate",
                    json={"prompt": prompt},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "prompt": prompt,
                        "response_time": result.get("processing_time", 0),
                        "from_cache": result.get("from_cache", False),
                        "quality_score": result.get("quality_metrics", {}).get("overall_quality", 0)
                    })
                    print(f"    ✅ Temps: {result['processing_time']:.3f}s, Qualité: {result.get('quality_metrics', {}).get('overall_quality', 0):.3f}")
                else:
                    print(f"    ❌ Erreur: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Exception: {e}")
        
        if results:
            response_times = [r["response_time"] for r in results]
            quality_scores = [r["quality_score"] for r in results]
            cache_hits = sum(1 for r in results if r["from_cache"])
            
            return {
                "total_prompts": len(prompts),
                "successful_requests": len(results),
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "avg_quality_score": statistics.mean(quality_scores),
                "cache_hit_rate": cache_hits / len(results),
                "results": results
            }
        
        return {"error": "No successful requests"}
    
    def test_lm_arena_benchmarks(self) -> Dict[str, Any]:
        """Tests spécifiques LM Arena"""
        print("🏆 Tests LM Arena Benchmarks")
        
        # Prompts typiques LM Arena
        test_prompts = [
            "Quelle est la capitale de la France?",
            "Écris une fonction Python pour calculer la factorielle",
            "Combien font 2 + 2?",
            "Explique la photosynthèse en termes simples",
            "Résous l'équation x² + 5x + 6 = 0",
            "Décris les principes de l'intelligence artificielle",
            "Quelle est l'importance du nombre d'or en mathématiques?",
            "Écris un poème sur la technologie",
            "Analyse l'impact de l'IA sur la société",
            "Explique le concept d'apprentissage automatique"
        ]
        
        # Test déterminisme sur un prompt
        determinism_result = self.test_determinism("Bonjour Connective AI", 10)
        
        # Test performance sur tous les prompts
        performance_result = self.test_performance(test_prompts)
        
        # Récupération métriques système
        try:
            metrics_response = requests.get(f"{self.base_url}/metrics", timeout=5)
            system_metrics = metrics_response.json() if metrics_response.status_code == 200 else {}
        except:
            system_metrics = {}
        
        # Récupération score LM Arena
        try:
            score_response = requests.get(f"{self.base_url}/lm_arena_score", timeout=5)
            lm_arena_score = score_response.json() if score_response.status_code == 200 else {}
        except:
            lm_arena_score = {}
        
        return {
            "determinism_test": determinism_result,
            "performance_test": performance_result,
            "system_metrics": system_metrics,
            "lm_arena_score": lm_arena_score,
            "timestamp": time.time()
        }
    
    def calculate_final_score(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcul score final LM Arena"""
        
        determinism_score = test_results.get("determinism_test", {}).get("determinism_score", 0)
        performance_score = min(1.0, 0.1 / max(test_results.get("performance_test", {}).get("avg_response_time", 0.1), 0.001))
        quality_score = test_results.get("performance_test", {}).get("avg_quality_score", 0)
        robustness_score = test_results.get("performance_test", {}).get("successful_requests", 0) / max(test_results.get("performance_test", {}).get("total_prompts", 1), 1)
        
        overall_score = (determinism_score + performance_score + quality_score + robustness_score) / 4
        
        # Position estimée
        if overall_score >= 0.98:
            position = "Top 1"
        elif overall_score >= 0.96:
            position = "Top 3"
        elif overall_score >= 0.94:
            position = "Top 5"
        elif overall_score >= 0.90:
            position = "Top 10"
        else:
            position = "Top 20"
        
        return {
            "determinism_score": determinism_score,
            "performance_score": performance_score,
            "quality_score": quality_score,
            "robustness_score": robustness_score,
            "overall_score": overall_score,
            "estimated_position": position,
            "target_score": 0.980,
            "success": overall_score >= 0.980
        }

def main():
    """Fonction principale de test"""
    
    # Configuration
    base_url = "http://54.221.137.228:8000"  # À adapter avec l'IP réelle
    
    print("🚀 TESTS CONNECTIVE AI OPTIMIZED - LM ARENA")
    print("=" * 50)
    print(f"🌐 URL: {base_url}")
    print("")
    
    tester = ConnectiveAITester(base_url)
    
    # Test health
    if not tester.test_health():
        print("❌ Health check failed - arrêt des tests")
        return
    
    # Tests LM Arena
    test_results = tester.test_lm_arena_benchmarks()
    
    # Calcul score final
    final_score = tester.calculate_final_score(test_results)
    
    # Affichage résultats
    print("\n" + "=" * 50)
    print("🏆 RÉSULTATS FINAUX LM ARENA")
    print("=" * 50)
    
    print(f"📊 Score Global: {final_score['overall_score']:.3f}")
    print(f"🎯 Score Cible: {final_score['target_score']:.3f}")
    print(f"🏆 Position Estimée: {final_score['estimated_position']}")
    print(f"✅ Succès: {'OUI' if final_score['success'] else 'NON'}")
    
    print(f"\n📋 Détail des Scores:")
    print(f"🧪 Déterminisme: {final_score['determinism_score']:.3f}")
    print(f"⚡ Performance: {final_score['performance_score']:.3f}")
    print(f"🎯 Qualité: {final_score['quality_score']:.3f}")
    print(f"🛡️ Robustesse: {final_score['robustness_score']:.3f}")
    
    # Métriques système
    system_metrics = test_results.get("system_metrics", {})
    if system_metrics:
        print(f"\n📊 Métriques Système:")
        print(f"📈 Requêtes totales: {system_metrics.get('total_requests', 0)}")
        print(f"✅ Requêtes réussies: {system_metrics.get('successful_requests', 0)}")
        print(f"⏱️ Temps moyen: {system_metrics.get('avg_response_time', 0):.3f}s")
        print(f"🎯 Qualité moyenne: {system_metrics.get('avg_quality_score', 0):.3f}")
        print(f"💾 Cache hit rate: {system_metrics.get('cache_metrics', {}).get('hit_rate', 0):.2%}")
    
    # Score LM Arena officiel
    lm_arena_score = test_results.get("lm_arena_score", {}).get("current_score", {})
    if lm_arena_score:
        print(f"\n🏆 Score LM Arena Officiel:")
        print(f"📊 Score Global: {lm_arena_score.get('overall_score', 0):.3f}")
        print(f"🧪 Déterminisme: {lm_arena_score.get('determinism_score', 0):.3f}")
        print(f"⚡ Performance: {lm_arena_score.get('performance_score', 0):.3f}")
        print(f"🎯 Qualité: {lm_arena_score.get('quality_score', 0):.3f}")
        print(f"🛡️ Robustesse: {lm_arena_score.get('robustness_score', 0):.3f}")
    
    # Sauvegarde résultats
    results_file = "lm_arena_test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "final_score": final_score,
            "test_results": test_results,
            "timestamp": time.time()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans: {results_file}")
    
    # Recommandations
    print(f"\n🎯 RECOMMANDATIONS:")
    if final_score['success']:
        print("✅ EXCELLENT! Système prêt pour LM Arena Top 3")
        print("🚀 Procéder à la soumission officielle")
    else:
        gap = final_score['target_score'] - final_score['overall_score']
        print(f"⚠️  Gap à combler: {gap:.3f} points")
        print("🔧 Optimisations recommandées:")
        
        if final_score['determinism_score'] < 1.0:
            print("  - Améliorer le routing déterministe")
        if final_score['performance_score'] < 0.95:
            print("  - Optimiser les temps de réponse")
        if final_score['quality_score'] < 0.98:
            print("  - Améliorer la qualité des réponses")
        if final_score['robustness_score'] < 0.99:
            print("  - Renforcer la robustesse")

if __name__ == "__main__":
    main()
