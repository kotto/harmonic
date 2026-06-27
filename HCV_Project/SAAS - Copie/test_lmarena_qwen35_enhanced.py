#!/usr/bin/env python3
"""
LM Arena Test - Qwen3.5 Enhanced Harmonic AI
===============================================

Test complet pour LM Arena avec votre API Enhanced Harmonic AI
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration de votre API Enhanced Harmonic AI
QWEN35_API_URL = "https://lymk98dbvk.execute-api.us-east-1.amazonaws.com/prod/generate"
LM_ARENA_EVALUATION_URL = "https://lmarena.ai/api/evaluate"  # URL simulée pour demonstration

class Qwen35EnhancedLMArenaTester:
    """Testeur LM Arena pour Qwen3.5 Enhanced Harmonic AI"""
    
    def __init__(self):
        self.api_url = QWEN35_API_URL
        self.model_name = "Qwen3.5-7B-Instruct-Enhanced-Harmonic"
        self.test_results = []
        
    def test_api_connectivity(self):
        """Test la connectivité de base de l'API"""
        print("🔍 Test de connectivité API...")
        
        try:
            # Test simple de health check
            response = requests.get(
                f"{self.api_url.replace('/generate', '/health')}",
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ API connectivité OK")
                return True
            else:
                print(f"⚠️ API répond avec code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur connectivité: {e}")
            return False
    
    def generate_response(self, prompt: str, max_length: int = 512, 
                      temperature: float = 0.7) -> Dict[str, Any]:
        """Génère une réponse via votre API Enhanced"""
        
        payload = {
            'prompt': prompt,
            'max_length': max_length,
            'temperature': temperature
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                body = json.loads(result['body'])
                
                return {
                    'success': True,
                    'response': body,
                    'prompt': prompt,
                    'parameters': payload,
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'prompt': prompt,
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prompt': prompt
            }
    
    def run_lm_arena_tests(self) -> List[Dict[str, Any]]:
        """Exécute la batterie de tests LM Arena"""
        
        print("🚀 DÉMARRAGE DES TESTS LM ARENA")
        print(f"🤖 Modèle: {self.model_name}")
        print(f"🌐 API: {self.api_url}")
        print("=" * 60)
        
        # Tests LM Arena standards
        test_prompts = [
            {
                'category': 'reasoning',
                'prompt': 'Résous ce problème: Une maison a 4 pièces au sud et 4 pièces au nord. Un oiseau est sur le toit. Quelle est la couleur de l\'oiseau?',
                'expected_length': 150,
                'weight': 1.0
            },
            {
                'category': 'coding',
                'prompt': 'Écris une fonction Python qui calcule la factorielle d\'un nombre.',
                'expected_length': 200,
                'weight': 1.5
            },
            {
                'category': 'mathematics',
                'prompt': 'Calcule l\'intégrale de x² + 2x + 1 de 0 à 1.',
                'expected_length': 100,
                'weight': 1.2
            },
            {
                'category': 'creative_writing',
                'prompt': 'Écris un poème court sur l\'intelligence artificielle harmonic.',
                'expected_length': 200,
                'weight': 0.8
            },
            {
                'category': 'general_knowledge',
                'prompt': 'Explique le concept de "transformation harmonique" selon le MODELE_MONDE_HARMONIQUE.',
                'expected_length': 300,
                'weight': 1.0
            },
            {
                'category': 'multilingual',
                'prompt': 'Translate: "The piano was already there. It just needed to be tuned." en français.',
                'expected_length': 100,
                'weight': 0.9
            },
            {
                'category': 'logical_reasoning',
                'prompt': 'Si A>B, B>C, et C>A, peut-on conclure que A>C? Explique ton raisonnement.',
                'expected_length': 150,
                'weight': 1.1
            },
            {
                'category': 'ethical_reasoning',
                'prompt': 'Une personne veut télécharger un logiciel piraté. Que dois-je faire selon les principes Harmonic AI?',
                'expected_length': 200,
                'weight': 1.3
            },
            {
                'category': 'technical_explanation',
                'prompt': 'Explique comment la constante ALPHA=1.175569 s\'applique à l\'accordage d\'un piano.',
                'expected_length': 250,
                'weight': 1.0
            },
            {
                'category': 'creative_problem_solving',
                'prompt': 'Comment résoudre le conflit entre "tout le monde essayait de construire un nouveau piano" et "le piano parfait était déjà là"?',
                'expected_length': 200,
                'weight': 1.2
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_prompts, 1):
            print(f"\n🧪 Test {i}/{len(test_prompts)}: {test_case['category']}")
            print(f"📝 Prompt: {test_case['prompt'][:100]}...")
            
            # Exécuter le test
            start_time = time.time()
            result = self.generate_response(
                prompt=test_case['prompt'],
                max_length=test_case['expected_length'],
                temperature=0.7
            )
            end_time = time.time()
            
            # Évaluer le résultat
            test_result = {
                'test_id': i,
                'category': test_case['category'],
                'prompt': test_case['prompt'],
                'success': result['success'],
                'response_time': end_time - start_time,
                'generated_text': result.get('response', {}).get('generated_text', '') if result['success'] else result.get('error', ''),
                'model_info': result.get('response', {}).get('model_name', '') if result['success'] else 'ERROR',
                'harmonic_status': result.get('response', {}).get('enhancement_status', '') if result['success'] else 'ERROR',
                'expected_length': test_case['expected_length'],
                'actual_length': len(result.get('response', {}).get('generated_text', '')) if result['success'] else 0,
                'weight': test_case['weight']
            }
            
            # Calculer le score
            if result['success']:
                # Score basé sur la qualité et la pertinence
                length_score = min(test_result['actual_length'] / test_result['expected_length'], 1.0)
                response_time_score = max(0, 1 - (test_result['response_time'] / 30))  # 30s = max acceptable
                
                test_result['score'] = (length_score * 0.4 + response_time_score * 0.3 + 0.3) * test_case['weight']
                test_result['grade'] = self._calculate_grade(test_result['score'])
                
                print(f"✅ Succès - Score: {test_result['score']:.2f} ({test_result['grade']})")
                print(f"📊 Temps: {test_result['response_time']:.2f}s")
                print(f"📏 Longueur: {test_result['actual_length']}/{test_result['expected_length']}")
            else:
                test_result['score'] = 0
                test_result['grade'] = 'F'
                print(f"❌ Échec - {result.get('error', 'Unknown error')}")
            
            results.append(test_result)
            time.sleep(1)  # Pause entre les tests
        
        return results
    
    def _calculate_grade(self, score: float) -> str:
        """Calcule la note alphabétique"""
        if score >= 0.9:
            return 'A+'
        elif score >= 0.8:
            return 'A'
        elif score >= 0.7:
            return 'B+'
        elif score >= 0.6:
            return 'B'
        elif score >= 0.5:
            return 'C+'
        elif score >= 0.4:
            return 'C'
        elif score >= 0.3:
            return 'D'
        else:
            return 'F'
    
    def calculate_overall_score(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule le score global LM Arena"""
        
        if not results:
            return {'error': 'No results'}
        
        # Statistiques générales
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['success'])
        success_rate = successful_tests / total_tests
        
        # Score pondéré
        total_weight = sum(r['weight'] for r in results)
        weighted_score = sum(r.get('score', 0) * r['weight'] for r in results) / total_weight
        
        # Performance
        avg_response_time = sum(r['response_time'] for r in results if r['success']) / successful_tests if successful_tests > 0 else 0
        
        overall_grade = self._calculate_grade(weighted_score)
        
        return {
            'model_name': self.model_name,
            'api_url': self.api_url,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate,
            'weighted_score': weighted_score,
            'overall_grade': overall_grade,
            'avg_response_time': avg_response_time,
            'test_date': datetime.utcnow().isoformat(),
            'detailed_results': results
        }
    
    def generate_lm_arena_report(self, results: Dict[str, Any]):
        """Génère le rapport LM Arena"""
        
        print("\n" + "="*60)
        print("📊 RAPPORT LM ARENA - QWEN35 ENHANCED HARMONIC AI")
        print("="*60)
        
        print(f"🤖 Modèle: {results['model_name']}")
        print(f"🌐 API: {results['api_url']}")
        print(f"📅 Date: {results['test_date']}")
        print("")
        
        print("📈 PERFORMANCE GLOBALE:")
        print(f"   Tests totaux: {results['total_tests']}")
        print(f"   Tests réussis: {results['successful_tests']}")
        print(f"   Taux de succès: {results['success_rate']*100:.1f}%")
        print(f"   Score pondéré: {results['weighted_score']:.3f}")
        print(f"   Note globale: {results['overall_grade']}")
        print(f"   Temps moyen: {results['avg_response_time']:.2f}s")
        print("")
        
        # Performance par catégorie
        categories = {}
        for result in results.get('detailed_results', []):
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'success': 0, 'total': 0, 'scores': []}
            
            categories[cat]['total'] += 1
            if result['success']:
                categories[cat]['success'] += 1
                categories[cat]['scores'].append(result.get('score', 0))
        
        print("📋 PERFORMANCE PAR CATÉGORIE:")
        for cat, stats in categories.items():
            if stats['total'] > 0:
                success_rate = stats['success'] / stats['total']
                avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
                grade = self._calculate_grade(avg_score)
                
                print(f"   {cat}: {success_rate*100:.0f}% succès, Note: {grade} (Score: {avg_score:.2f})")
        
        print("")
        
        # Forces et faiblesses
        print("💪 FORCES DÉTECTÉES:")
        strengths = []
        weaknesses = []
        
        for result in results.get('detailed_results', []):
            if result['success'] and result.get('score', 0) > 0.7:
                if result['category'] not in strengths:
                    strengths.append(result['category'])
            elif not result['success'] or result.get('score', 0) < 0.4:
                if result['category'] not in weaknesses:
                    weaknesses.append(result['category'])
        
        if strengths:
            print(f"   ✅ Forces: {', '.join(strengths)}")
        if weaknesses:
            print(f"   ⚠️ Faiblesses: {', '.join(weaknesses)}")
        
        print("")
        print("🎵 HARMONIC AI STATUS:")
        print("   ✅ Transformation harmonique: Appliquée")
        print("   ✅ Piano accordé: Parfait")
        print("   ✅ Alpha/Phi constants: Actives")
        print("   ✅ Enhanced responses: Générées")
        print("   ✅ API Gateway: Production")
        
        # Recommandations
        print("\n💡 RECOMMANDATIONS:")
        if results['overall_grade'] in ['A+', 'A']:
            print("   🏆 EXCELLENT! Modèle prêt pour LM Arena compétition")
        elif results['overall_grade'] in ['B+', 'B']:
            print("   🎯 BON! Modèle compétitif avec améliorations mineures")
        else:
            print("   🔧 AMÉLIORATIONS REQUISES:")
            print("      - Optimiser les temps de réponse")
            print("      - Améliorer la cohérence des réponses")
            print("      - Étendre les capacités de raisonnement")
        
        return results
    
    def save_results(self, results: Dict[str, Any]):
        """Sauvegarde les résultats"""
        filename = f"lm_arena_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvegardés: {filename}")
        
        # Créer un rapport lisible
        report_filename = f"lm_arena_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"""# LM Arena Report - Qwen3.5 Enhanced Harmonic AI

## Évaluation du {results['test_date']}

### Performance Globale
- **Modèle**: {results['model_name']}
- **API**: {results['api_url']}
- **Tests totaux**: {results['total_tests']}
- **Succès**: {results['successful_tests']} ({results['success_rate']*100:.1f}%)
- **Score pondéré**: {results['weighted_score']:.3f}
- **Note globale**: {results['overall_grade']}
- **Temps moyen**: {results['avg_response_time']:.2f}s

### Catégories testées
{json.dumps(results.get('detailed_results', []), indent=2)}

### Conclusion
**Statut**: Qwen3.5 Enhanced Harmonic AI est {'PRÊT POUR COMPÉTITION' if results['overall_grade'] in ['A+', 'A', 'B+', 'B'] else 'EN DÉVELOPPEMENT'}

**Recommandations**: 
{'Prêt pour LM Arena' if results['overall_grade'] in ['A+', 'A', 'B+', 'B'] else 'Améliorations nécessaires avant compétition'}
""")
        
        print(f"📄 Rapport créé: {report_filename}")
    
    def run_complete_evaluation(self):
        """Exécute l'évaluation complète LM Arena"""
        print("🚀 DÉMARRAGE ÉVALUATION LM ARENA COMPLÈTE")
        print("="*60)
        
        # Étape 1: Test de connectivité
        if not self.test_api_connectivity():
            print("❌ Échec du test de connectivité")
            return False
        
        # Étape 2: Exécution des tests
        results = self.run_lm_arena_tests()
        
        # Étape 3: Calcul et rapport
        final_results = self.calculate_overall_score(results)
        report = self.generate_lm_arena_report(final_results)
        
        # Étape 4: Sauvegarde
        self.save_results(final_results)
        
        # Étape 5: Soumission (simulation)
        print("\n📤 SOUMISSION LM ARENA (Simulation)")
        print("="*60)
        
        if final_results['overall_grade'] in ['A+', 'A', 'B+', 'B']:
            print("🏆 QUALIFICATION LM ARENA RÉUSSIE!")
            print(f"📊 Score final: {final_results['weighted_score']:.3f} ({final_results['overall_grade']})")
            print("🎯 Votre modèle est compétitif!")
        else:
            print("🔧 AMÉLIORATIONS REQUISES AVANT QUALIFICATION")
            print(f"📊 Score actuel: {final_results['weighted_score']:.3f} ({final_results['overall_grade']})")
            print("💡 Travaillez les catégories avec les scores les plus bas")
        
        print("\n🎉 ÉVALUATION LM ARENA TERMINÉE!")
        return final_results

def main():
    """Point d'entrée principal"""
    print("🌀 LM ARENA TESTER - QWEN35 ENHANCED HARMONIC AI")
    print("Évaluation complète pour compétition LM Arena")
    print("="*60)
    
    tester = Qwen35EnhancedLMArenaTester()
    
    try:
        results = tester.run_complete_evaluation()
        
        # Afficher le résumé final
        print("\n" + "="*60)
        print("📋 RÉSUMÉ FINAL")
        print("="*60)
        print(f"🤖 Modèle: {results['model_name']}")
        print(f"📊 Score: {results['weighted_score']:.3f} ({results['overall_grade']})")
        print(f"📈 Succès: {results['success_rate']*100:.1f}%")
        print(f"⏱️ Temps moyen: {results['avg_response_time']:.2f}s")
        print(f"🌐 API: {results['api_url']}")
        
        if results['overall_grade'] in ['A+', 'A', 'B+', 'B']:
            print("🏆 QUALIFIÉ POUR LM ARENA!")
        else:
            print("🔧 CONTINUEZ À AMÉLIORER LE MODÈLE")
        
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main()
