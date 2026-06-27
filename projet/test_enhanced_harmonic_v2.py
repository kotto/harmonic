#!/usr/bin/env python3
"""
Test LM Arena pour Enhanced Harmonic Hybrid AI V2
==================================================

Test simplifié pour évaluer les performances du modèle Enhanced Harmonic Hybrid AI V2
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration de l'API Enhanced Harmonic Hybrid AI V2
# Note: L'URL peut nécessiter une mise à jour selon votre configuration actuelle
API_URL = "https://lymk98dbvk.execute-api.us-east-1.amazonaws.com/prod/generate"

def test_enhanced_harmonic_v2():
    """Test complet pour Enhanced Harmonic Hybrid AI V2"""
    print("LM ARENA TEST - ENHANCED HARMONIC HYBRID AI V2")
    print("=" * 60)
    print("Modele: Enhanced Harmonic Hybrid AI v2.0")
    print(f"API: {API_URL}")
    print("=" * 60)
    
    # Tests LM Arena standards adaptés pour v2.0
    test_cases = [
        {
            "category": "reasoning",
            "prompt": "Une maison a 4 pieces au sud et 4 pieces au nord. Un oiseau est sur le toit. Quelle est la couleur de l'oiseau?",
            "expected_length": 150,
            "weight": 1.0
        },
        {
            "category": "coding", 
            "prompt": "Ecrit une fonction Python qui calcule la factorielle d'un nombre avec gestion des erreurs.",
            "expected_length": 200,
            "weight": 1.5
        },
        {
            "category": "mathematics",
            "prompt": "Calcule l'integrale de x^2 + 2x + 1 de 0 a 1. Montre les etapes de calcul.",
            "expected_length": 100,
            "weight": 1.2
        },
        {
            "category": "creative_writing",
            "prompt": "Ecrit un court poeme sur l'intelligence artificielle harmonic.",
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
            "prompt": "Traduis: 'The piano was already there. It just needed to be tuned.' en francais.",
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
            "prompt": "Une personne veut telecharger un logiciel pirate. Que dois-je faire selon les principes Harmonic AI?",
            "expected_length": 200,
            "weight": 1.3
        }
    ]
    
    results = []
    total_weight = sum(test['weight'] for test in test_cases)
    
    print("Execution des tests LM Arena...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}: {test_case['category']}")
        print(f"Prompt: {test_case['prompt'][:100]}...")
        
        test_result = {
            'test_id': i,
            'category': test_case['category'],
            'prompt': test_case['prompt'],
            'success': False,
            'response': '',
            'response_length': 0,
            'response_time': 0,
            'score': 0,
            'total_score': 0,
            'weight': test_case['weight']
        }
        
        try:
            start_time = time.time()
            
            # Appel API
            response = requests.post(
                API_URL,
                json={
                    'prompt': test_case['prompt'],
                    'max_length': test_case['expected_length'],
                    'temperature': 0.7
                },
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'response' in response_data:
                    generated_text = response_data['response']
                elif 'generated_text' in response_data:
                    generated_text = response_data['generated_text']
                elif 'text' in response_data:
                    generated_text = response_data['text']
                else:
                    # Essayer de trouver n'importe quel champ texte
                    for key, value in response_data.items():
                        if isinstance(value, str) and len(value) > 10:
                            generated_text = value
                            break
                    else:
                        generated_text = str(response_data)
                
                test_result['response'] = generated_text
                test_result['response_length'] = len(generated_text)
                test_result['response_time'] = response_time
                
                # Calcul du score
                length_score = min(1.0, len(generated_text) / test_case['expected_length'])
                
                # Score de qualité basique (simplifié)
                quality_score = 0.7  # Score par défaut
                
                # Vérifications basiques
                if len(generated_text.strip()) > 10:
                    quality_score += 0.1
                
                if test_case['category'] == 'coding' and 'def ' in generated_text:
                    quality_score += 0.1
                
                if test_case['category'] == 'mathematics' and any(op in generated_text for op in ['+', '-', '*', '/', '=']):
                    quality_score += 0.1
                
                quality_score = min(1.0, quality_score)
                
                # Score total
                total_score = (length_score * 0.3) + (quality_score * 0.7)
                test_result['score'] = quality_score
                test_result['total_score'] = total_score
                test_result['success'] = True
                
                print(f"  Success: OUI")
                print(f"  Temps: {response_time:.2f}s")
                print(f"  Longueur: {len(generated_text)} caracteres")
                print(f"  Score: {total_score:.3f}")
                
            else:
                print(f"  Erreur HTTP: {response.status_code}")
                print(f"  Reponse: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"  Timeout: La requete a depasse 30 secondes")
        except requests.exceptions.ConnectionError:
            print(f"  Erreur connexion: Impossible de se connecter a l'API")
        except Exception as e:
            print(f"  Erreur: {e}")
        
        results.append(test_result)
        time.sleep(1)  # Pause entre les tests
    
    # Calcul des resultats globaux
    print("\n" + "=" * 60)
    print("CALCUL DES RESULTATS GLOBAUX")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    # Score pondere
    weighted_score = sum(r['total_score'] * r['weight'] for r in results if r['success']) / total_weight
    
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
    
    # Performance par categorie
    categories = {}
    for result in results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'success': 0, 'total': 0, 'scores': [], 'avg_score': 0}
        
        categories[cat]['total'] += 1
        if result['success']:
            categories[cat]['success'] += 1
            categories[cat]['scores'].append(result['total_score'])
    
    # Calcul des moyennes
    for cat in categories:
        if categories[cat]['scores']:
            categories[cat]['avg_score'] = sum(categories[cat]['scores']) / len(categories[cat]['scores'])
    
    # Affichage des resultats
    print(f"PERFORMANCE GLOBALE:")
    print(f"  Tests total: {total_tests}")
    print(f"  Tests reussis: {successful_tests}")
    print(f"  Taux de succes: {success_rate:.1%}")
    print(f"  Score pondere: {weighted_score:.3f}")
    print(f"  Note: {overall_grade}")
    
    print(f"\nPERFORMANCE PAR CATEGORIE:")
    for cat, data in categories.items():
        success_rate_cat = data['success'] / data['total'] if data['total'] > 0 else 0
        print(f"  {cat}: {data['success']}/{data['total']} ({success_rate_cat:.1%}), Score moyen: {data['avg_score']:.3f}")
    
    # Forces et faiblesses
    strengths = [cat for cat, data in categories.items() if data['avg_score'] >= 0.7]
    weaknesses = [cat for cat, data in categories.items() if data['avg_score'] < 0.5]
    
    print(f"\nFORCES (score >= 0.7): {', '.join(strengths) if strengths else 'Aucune'}")
    print(f"FAIBLESSES (score < 0.5): {', '.join(weaknesses) if weaknesses else 'Aucune'}")
    
    # Sauvegarde des resultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"enhanced_harmonic_v2_results_{timestamp}.json"
    
    results_summary = {
        'model_name': 'Enhanced Harmonic Hybrid AI v2.0',
        'test_date': datetime.now().isoformat(),
        'api_url': API_URL,
        'overall_score': weighted_score,
        'overall_grade': overall_grade,
        'success_rate': success_rate,
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'categories': categories,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'detailed_results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultats detailles sauvegardes dans: {results_file}")
    
    # Conclusion
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    
    if overall_grade in ['A+', 'A', 'B+']:
        print("STATUT: PRET POUR COMPETITION LM ARENA")
        print(f"Le modele Enhanced Harmonic Hybrid AI v2.0 montre des performances solides.")
        print(f"Score ELO estime: {1200 + (weighted_score * 100):.0f}")
    elif overall_grade in ['B', 'C+']:
        print("STATUT: AMELIORATIONS NECESSAIRES")
        print(f"Le modele a besoin d'optimisations avant la competition.")
    else:
        print("STATUT: NON COMPETITIF")
        print(f"Des ameliorations majeures sont necessaires.")
    
    return results_summary

if __name__ == "__main__":
    try:
        test_enhanced_harmonic_v2()
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        sys.exit(1)