#!/usr/bin/env python3
"""
Test LM Arena pour l'instance EC2 réelle qwen35-ec2-server
===========================================================

Ce script essaie de trouver et tester l'instance EC2 déployée
"""

import requests
import json
import time
import sys
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

def find_ec2_ip():
    """Essayer de trouver l'adresse IP de l'instance EC2"""
    print("🔍 Recherche de l'adresse IP de l'instance EC2...")
    
    # Essayer différentes méthodes pour trouver l'IP
    possible_ips = []
    
    # 1. Vérifier les fichiers de configuration existants
    config_files = [
        "ec2-instance-config.json",
        "launch-config.json",
        "ec2-template.json"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Chercher l'IP dans différentes structures
                    if isinstance(config, dict):
                        # Chercher dans différentes parties du JSON
                        for key in ['PublicIpAddress', 'public_ip', 'ip_address', 'IP']:
                            if key in config:
                                ip = config[key]
                                if ip and ip != '0.0.0.0':
                                    possible_ips.append(ip)
                                    print(f"  📋 Trouvé dans {config_file}: {ip}")
            except:
                pass
    
    # 2. Essayer de lire depuis les logs ou fichiers de déploiement
    log_patterns = [
        "*.log",
        "deploy*.txt",
        "status*.json"
    ]
    
    # 3. Essayer avec AWS CLI si disponible
    try:
        # Essayer différentes requêtes AWS
        commands = [
            'aws ec2 describe-instances --filters "Name=tag:Name,Values=qwen35-ec2-server" --query "Reservations[].Instances[].PublicIpAddress" --output text --region us-east-1',
            'aws ec2 describe-instances --filters "Name=tag:Name,Values=qwen35-production-instance" --query "Reservations[].Instances[].PublicIpAddress" --output text --region us-east-1',
            'aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query "Reservations[].Instances[].PublicIpAddress" --output text --region us-east-1'
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    ip = result.stdout.strip()
                    if ip and ip != 'None':
                        possible_ips.append(ip)
                        print(f"  🌐 Trouvé via AWS CLI: {ip}")
            except:
                pass
    except:
        print("  ⚠️ AWS CLI non disponible ou erreur d'exécution")
    
    # 4. IPs connues des déploiements précédents
    known_ips = [
        "54.166.179.141",  # DeepSeek instance
        "3.95.231.91",     # Autre instance potentielle
        "98.82.7.99",      # Autre instance potentielle
    ]
    
    for ip in known_ips:
        possible_ips.append(ip)
    
    # Nettoyer et dédupliquer
    unique_ips = []
    for ip in possible_ips:
        if ip and ip not in unique_ips:
            unique_ips.append(ip)
    
    return unique_ips

def test_api_endpoint(ip: str, port: int = 8080) -> Optional[Dict]:
    """Tester un endpoint API spécifique"""
    url = f"http://{ip}:{port}"
    
    print(f"\n🧪 Test de l'API à {url}...")
    
    # D'abord tester le health check
    health_url = f"{url}/health"
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"  ✅ Health check réussi")
            health_data = response.json()
            print(f"  📊 Status: {health_data.get('status', 'N/A')}")
            return {
                'ip': ip,
                'port': port,
                'health_check': True,
                'health_data': health_data,
                'url': url
            }
        else:
            print(f"  ❌ Health check échoué: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"  ⏱️ Timeout sur health check")
    except requests.exceptions.ConnectionError:
        print(f"  🔌 Erreur de connexion")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    
    return None

def run_lm_arena_tests(api_url: str) -> Dict:
    """Exécuter les tests LM Arena sur l'API"""
    print(f"\n🚀 Exécution des tests LM Arena sur {api_url}")
    print("=" * 60)
    
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
        }
    ]
    
    results = []
    total_weight = sum(test['weight'] for test in test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}: {test_case['category']}")
        print(f"Prompt: {test_case['prompt'][:80]}...")
        
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
                api_url,
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
                
                # Extraire le texte généré
                generated_text = ''
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
                
                # Calcul du score simplifié
                length_score = min(1.0, len(generated_text) / test_case['expected_length'])
                
                # Score de qualité basique
                quality_score = 0.5  # Score de base
                
                # Vérifications basiques
                if len(generated_text.strip()) > 20:
                    quality_score += 0.2
                
                if test_case['category'] == 'coding' and 'def ' in generated_text:
                    quality_score += 0.1
                
                if test_case['category'] == 'mathematics' and any(op in generated_text for op in ['+', '-', '*', '/', '=']):
                    quality_score += 0.1
                
                if 'erreur' not in generated_text.lower() and 'error' not in generated_text.lower():
                    quality_score += 0.1
                
                quality_score = min(1.0, quality_score)
                
                # Score total
                total_score = (length_score * 0.3) + (quality_score * 0.7)
                test_result['score'] = quality_score
                test_result['total_score'] = total_score
                test_result['success'] = True
                
                print(f"  ✅ Succès")
                print(f"  ⏱️ Temps: {response_time:.2f}s")
                print(f"  📏 Longueur: {len(generated_text)} caractères")
                print(f"  🎯 Score: {total_score:.3f}")
                print(f"  📝 Aperçu: {generated_text[:100]}...")
                
            else:
                print(f"  ❌ Erreur HTTP: {response.status_code}")
                print(f"  📋 Réponse: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"  ⏱️ Timeout: La requête a dépassé 30 secondes")
        except requests.exceptions.ConnectionError:
            print(f"  🔌 Erreur connexion: Impossible de se connecter à l'API")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
        
        results.append(test_result)
        time.sleep(1)  # Pause entre les tests
    
    # Calcul des résultats globaux
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS GLOBAUX")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    # Score pondéré
    weighted_score = 0
    if successful_tests > 0:
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
    
    print(f"Tests totaux: {total_tests}")
    print(f"Tests réussis: {successful_tests}")
    print(f"Taux de succès: {success_rate:.1%}")
    print(f"Score pondéré: {weighted_score:.3f}")
    print(f"Note: {overall_grade}")
    
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
    
    # Calcul des moyennes
    for cat in categories:
        if categories[cat]['scores']:
            categories[cat]['avg_score'] = sum(categories[cat]['scores']) / len(categories[cat]['scores'])
    
    print(f"\n📈 PERFORMANCE PAR CATÉGORIE:")
    for cat, data in categories.items():
        success_rate_cat = data['success'] / data['total'] if data['total'] > 0 else 0
        print(f"  {cat}: {data['success']}/{data['total']} ({success_rate_cat:.1%}), Score moyen: {data['avg_score']:.3f}")
    
    # Sauvegarde des résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"ec2_real_test_results_{timestamp}.json"
    
    results_summary = {
        'model_name': 'Qwen3.5-9B-DeepSeek-V4-Flash-BF16 (EC2)',
        'test_date': datetime.now().isoformat(),
        'api_url': api_url,
        'overall_score': weighted_score,
        'overall_grade': overall_grade,
        'success_rate': success_rate,
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'categories': categories,
        'detailed_results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats détaillés sauvegardés dans: {results_file}")
    
    return results_summary

def main():
    """Fonction principale"""
    print("🏆 TEST LM ARENA POUR INSTANCE EC2 RÉELLE")
    print("=" * 60)
    print("Instance: qwen35-ec2-server")
    print("Région: us-east-1")
    print("Ports testés: 8080, 8000, 80")
    print("=" * 60)
    
    # Trouver les IPs possibles
    possible_ips = find_ec2_ip()
    
    if not possible_ips:
        print("❌ Aucune adresse IP trouvée pour l'instance EC2")
        print("Veuillez fournir l'adresse IP manuellement ou vérifier:")
        print("1. Que l'instance est en cours d'exécution")
        print("2. Que les permissions AWS sont correctes")
        print("3. Que l'instance a une IP publique")
        return
    
    print(f"\n🔍 IPs à tester: {', '.join(possible_ips)}")
    
    # Tester différents ports pour chaque IP
    ports_to_test = [8080, 8000, 80]
    working_endpoints = []
    
    for ip in possible_ips:
        for port in ports_to_test:
            result = test_api_endpoint(ip, port)
            if result:
                working_endpoints.append(result)
    
    if not working_endpoints:
        print("\n❌ Aucun endpoint API fonctionnel trouvé")
        print("Vérifiez que:")
        print("1. L'instance EC2 est en cours d'exécution")
        print("2. Le service Qwen3.5 est démarré")
        print("3. Les règles de sécurité autorisent l'accès")
        print("4. Le port est correct (8080, 8000 ou 80)")
        return
    
    print(f"\n✅ Endpoints fonctionnels trouvés: {len(working_endpoints)}")
    
    # Utiliser le premier endpoint fonctionnel
    endpoint = working_endpoints[0]
    api_url = endpoint['url'] + '/generate'  # Supposons l'endpoint /generate
    
    print(f"\n🎯 Utilisation de l'endpoint: {api_url}")
    
    # Exécuter les tests LM Arena
    try:
        results = run_lm_arena_tests(api_url)
        
        # Conclusion
        print("\n" + "=" * 60)
        print("🎯 CONCLUSION")
        print("=" * 60)
        
        if results['overall_grade'] in ['A+', 'A', 'B+']:
            print("✅ STATUT: PRÊT POUR COMPÉTITION LM ARENA")
            print(f"L'instance EC2 montre des performances solides.")
            print(f"Score ELO estimé: {1200 + (results['overall_score'] * 100):.0f}")
        elif results['overall_grade'] in ['B', 'C+']:
            print("⚠️ STATUT: AMÉLIORATIONS NÉCESSAIRES")
            print(f"L'instance a besoin d'optimisations avant la compétition.")
        else:
            print("❌ STATUT: NON COMPÉTITIF")
            print(f"Des améliorations majeures sont nécessaires.")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        print("Vérifiez que l'endpoint /generate existe et fonctionne correctement.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔴 Test interrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        sys.exit(1)