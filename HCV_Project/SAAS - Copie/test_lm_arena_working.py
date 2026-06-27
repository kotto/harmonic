#!/usr/bin/env python3
"""
LM Arena Test - Qwen35 Enhanced - Working Version
==================================================

Version finale qui fonctionne avec votre API Enhanced Harmonic AI
"""

import requests
import json
import time
from datetime import datetime

# Configuration de votre API
QWEN35_API_URL = "https://lymk98dbvk.execute-api.us-east-1.amazonaws.com/prod/generate"

def test_lm_arena_complete():
    """Test LM Arena complet avec l'API Qwen35 Enhanced"""
    print("🚀 LM ARENA TEST - QWEN35 ENHANCED HARMONIC AI")
    print("=" * 60)
    print("🤖 Modèle: Qwen3.5-7B-Instruct-Enhanced-Harmonic")
    print(f"🌐 API: {QWEN35_API_URL}")
    print("=" * 60)
    
    # Tests LM Arena standards
    test_cases = [
        {
            "category": "reasoning",
            "prompt": "Une maison a 4 pièces au sud et 4 pièces au nord. Un oiseau est sur le toit. Quelle est la couleur de l'oiseau?",
            "expected_length": 150,
            "weight": 1.0
        },
        {
            "category": "coding", 
            "prompt": "Écris une fonction Python qui calcule la factorielle d'un nombre.",
            "expected_length": 200,
            "weight": 1.5
        },
        {
            "category": "mathematics",
            "prompt": "Calcule l'intégrale de x² + 2x + 1 de 0 à 1.",
            "expected_length": 100,
            "weight": 1.2
        },
        {
            "category": "creative_writing",
            "prompt": "Écris un court poème sur l'intelligence artificielle harmonic.",
            "expected_length": 150,
            "weight": 0.8
        },
        {
            "category": "general_knowledge",
            "prompt": "Explique le concept de 'transformation harmonique' selon le MODELE_MONDE_HARMONIQUE.",
            "expected_length": 250,
            "weight": 1.0
        },
        {
            "category": "multilingual",
            "prompt": "Traduis: 'The piano was already there. It just needed to be tuned.' en français.",
            "expected_length": 100,
            "weight": 0.9
        },
        {
            "category": "logical_reasoning",
            "prompt": "Si A>B, B>C, et C>A, peut-on conclure que A>C? Explique ton raisonnement.",
            "expected_length": 150,
            "weight": 1.1
        },
        {
            "category": "ethical_reasoning",
            "prompt": "Une personne veut télécharger un logiciel piraté. Que dois-je faire selon les principes Harmonic AI?",
            "expected_length": 200,
            "weight": 1.3
        }
    ]
    
    results = []
    total_weight = sum(test['weight'] for test in test_cases)
    
    print("🧪 Exécution des tests LM Arena...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}/{len(test_cases)}: {test_case['category']}")
        print(f"Prompt: {test_case['prompt'][:100]}...")
        
        try:
            start_time = time.time()
            
            # Appel API
            response = requests.post(
                QWEN35_API_URL,
                json={
                    'prompt': test_case['prompt'],
                    'max_length': test_case['expected_length'],
                    'temperature': 0.7
                },
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Analyse de la réponse
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    success = result.get('status') == 'success'
                    generated_text = result.get('generated_text', '')
                    actual_length = len(generated_text)
                    
                    # Calcul des scores
                    length_score = min(actual_length / test_case['expected_length'], 1.0)
                    response_time_score = max(0, 1 - (response_time / 15))  # 15s = max acceptable
                    
                    total_score = (length_score * 0.4 + response_time_score * 0.3 + 0.3) * test_case['weight']
                    
                    # Note
                    if total_score >= 0.9:
                        grade = 'A+'
                    elif total_score >= 0.8:
                        grade = 'A'
                    elif total_score >= 0.7:
                        grade = 'B+'
                    elif total_score >= 0.6:
                        grade = 'B'
                    elif total_score >= 0.5:
                        grade = 'C+'
                    elif total_score >= 0.4:
                        grade = 'C'
                    elif total_score >= 0.3:
                        grade = 'D'
                    else:
                        grade = 'F'
                    
                    test_result = {
                        'test_id': i,
                        'category': test_case['category'],
                        'prompt': test_case['prompt'],
                        'success': success,
                        'response_time': response_time,
                        'generated_text': generated_text,
                        'actual_length': actual_length,
                        'expected_length': test_case['expected_length'],
                        'length_score': length_score,
                        'response_time_score': response_time_score,
                        'total_score': total_score,
                        'grade': grade,
                        'weight': test_case['weight'],
                        'model_info': result.get('model_name', ''),
                        'harmonic_status': result.get('deployment_status', ''),
                        'error': None
                    }
                    
                    print(f"✅ Succès - Score: {total_score:.2f} ({grade})")
                    print(f"📊 Temps: {response_time:.2f}s")
                    print(f"📏 Longueur: {actual_length}/{test_case['expected_length']}")
                    print(f"🎵 Aperçu: {generated_text[:200]}...")
                    
                except Exception as e:
                    test_result = {
                        'test_id': i,
                        'category': test_case['category'],
                        'prompt': test_case['prompt'],
                        'success': False,
                        'response_time': response_time,
                        'error': f"JSON parsing: {e}",
                        'total_score': 0,
                        'grade': 'F',
                        'weight': test_case['weight']
                    }
                    print(f"❌ Erreur parsing: {e}")
                    
            else:
                test_result = {
                    'test_id': i,
                    'category': test_case['category'],
                    'prompt': test_case['prompt'],
                    'success': False,
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}",
                    'total_score': 0,
                    'grade': 'F',
                    'weight': test_case['weight']
                }
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            test_result = {
                'test_id': i,
                'category': test_case['category'],
                'prompt': test_case['prompt'],
                'success': False,
                'response_time': 0,
                'error': str(e),
                'total_score': 0,
                'grade': 'F',
                'weight': test_case['weight']
            }
            print(f"❌ Erreur requête: {e}")
        
        results.append(test_result)
        time.sleep(0.5)  # Pause entre les tests
    
    # Calcul des résultats globaux
    print("\n" + "=" * 60)
    print("📊 CALCUL DES RÉSULTATS GLOBAUX")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    # Score pondéré
    weighted_score = sum(r['total_score'] * r['weight'] for r in results) / total_weight
    
    # Note globale
    if weighted_score >= 0.9:
        overall_grade = 'A+'
    elif weighted_score >= 0.8:
        overall_grade = 'A'
    elif weighted_score >= 0.7:
        overall_grade = 'B+'
    elif weighted_score >= 0.6:
        overall_grade = 'B'
    elif weighted_score >= 0.5:
        overall_grade = 'C+'
    elif weighted_score >= 0.4:
        overall_grade = 'C'
    elif weighted_score >= 0.3:
        overall_grade = 'D'
    else:
        overall_grade = 'F'
    
    # Performance par catégorie
    categories = {}
    for result in results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'success': 0, 'total': 0, 'scores': [], 'avg_score': 0}
        
        categories[cat]['total'] += 1
        if result['success']:
            categories[cat]['success'] += 1
            categories[cat]['scores'].append(result['total_score'])
    
    # Affichage des résultats
    print(f"📈 PERFORMANCE GLOBALE:")
    print(f"   Tests totaux: {total_tests}")
    print(f"   Tests réussis: {successful_tests}")
    print(f"   Taux de succès: {success_rate*100:.1f}%")
    print(f"   Score pondéré: {weighted_score:.3f}")
    print(f"   Note globale: {overall_grade}")
    
    print(f"\n📋 PERFORMANCE PAR CATÉGORIE:")
    for cat, stats in categories.items():
        if stats['total'] > 0:
            cat_success_rate = stats['success'] / stats['total']
            avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
            
            if avg_score >= 0.8:
                cat_grade = 'A'
            elif avg_score >= 0.7:
                cat_grade = 'B'
            elif avg_score >= 0.6:
                cat_grade = 'C'
            elif avg_score >= 0.5:
                cat_grade = 'D'
            else:
                cat_grade = 'F'
            
            print(f"   {cat}: {cat_success_rate*100:.0f}% succès, Note: {cat_grade} (Score: {avg_score:.2f})")
    
    # Forces et faiblesses
    print(f"\n💪 FORCES ET FAIBLESESSES:")
    strengths = []
    weaknesses = []
    
    for result in results:
        if result['success'] and result['total_score'] >= 0.7:
            if result['category'] not in strengths:
                strengths.append(result['category'])
        elif not result['success'] or result['total_score'] < 0.4:
            if result['category'] not in weaknesses:
                weaknesses.append(result['category'])
    
    if strengths:
        print(f"   ✅ Forces: {', '.join(strengths)}")
    if weaknesses:
        print(f"   ⚠️ Faiblesses: {', '.join(weaknesses)}")
    
    # Rapport final
    final_results = {
        'model_name': 'Qwen3.5-7B-Instruct-Enhanced-Harmonic',
        'api_url': QWEN35_API_URL,
        'test_date': datetime.utcnow().isoformat(),
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'success_rate': success_rate,
        'weighted_score': weighted_score,
        'overall_grade': overall_grade,
        'categories_performance': categories,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'detailed_results': results
    }
    
    # Sauvegarde
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"lm_arena_results_{timestamp}.json"
    report_file = f"lm_arena_report_{timestamp}.md"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"""# LM Arena Report - Qwen35 Enhanced Harmonic AI

## Évaluation du {final_results['test_date']}

### Performance Globale
- **Modèle**: {final_results['model_name']}
- **API**: {final_results['api_url']}
- **Tests**: {final_results['total_tests']}
- **Succès**: {final_results['successful_tests']} ({final_results['success_rate']*100:.1f}%)
- **Score**: {final_results['weighted_score']:.3f}
- **Note**: {final_results['overall_grade']}

### Performance par Catégorie
{json.dumps(final_results['categories_performance'], indent=2)}

### Forces et Faiblesses
- **Forces**: {', '.join(final_results['strengths'])}
- **Faiblesses**: {', '.join(final_results['weaknesses'])}

### Conclusion
**Statut**: {'PRÊT POUR COMPÉTITION' if final_results['overall_grade'] in ['A+', 'A', 'B+', 'B'] else 'EN DÉVELOPPEMENT'}

Résultats détaillés sauvegardés dans: {results_file}
""")
    
    print(f"\n💾 Résultats sauvegardés:")
    print(f"   JSON: {results_file}")
    print(f"   Rapport: {report_file}")
    
    print("\n" + "=" * 60)
    print("🎉 TEST LM ARENA TERMINÉ!")
    print("=" * 60)
    
    if final_results['overall_grade'] in ['A+', 'A', 'B+', 'B']:
        print("🏆 EXCELLENT! Votre modèle est compétitif!")
        print("🎯 PRÊT POUR LM ARENA!")
    else:
        print("🔧 CONTINUEZ À AMÉLIORER LE MODÈLE")
        print("📋 Améliorez les catégories avec les scores les plus bas")
    
    return final_results

def main():
    """Point d'entrée principal"""
    try:
        results = test_lm_arena_complete()
        return results
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu par l'utilisateur")
        return None
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        return None

if __name__ == "__main__":
    main()
