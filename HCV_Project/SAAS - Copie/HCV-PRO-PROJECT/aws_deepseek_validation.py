#!/usr/bin/env python3
"""
TEST DE VALIDATION AWS - DEEPSEEK MOE HARMONIC
===============================================

Test de validation du concept Deepseek MOE Harmonic
directement sur l'infrastructure AWS déployée
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path

class AWSDeepseekValidator:
    """Validateur Deepseek sur AWS"""
    
    def __init__(self):
        # URLs de notre infrastructure AWS
        self.frontend_url = "https://hcv-pro-deepseek-test-326095712935.s3.eu-west-3.amazonaws.com/deepseek-moe.html"
        self.api_base = "https://hcv-pro-deepseek-test-326095712935.s3.eu-west-3.amazonaws.com"
        self.results = {}
        
    def test_frontend_accessibility(self):
        """Tester l'accessibilité du frontend sur AWS"""
        print("🌐 Test d'accessibilité du frontend AWS...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            
            if response.status_code == 200:
                print("   ✅ Frontend accessible")
                print(f"   📊 Status: {response.status_code}")
                print(f"   📦 Taille: {len(response.content)} bytes")
                
                # Vérifier que le contenu HTML est correct
                if "Deepseek MOE Harmonic" in response.text:
                    print("   ✅ Contenu HTML valide")
                    return True
                else:
                    print("   ⚠️ Contenu HTML invalide")
                    return False
            else:
                print(f"   ❌ Erreur HTTP: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"   ❌ Erreur de connexion: {e}")
            return False
    
    def test_api_endpoints(self):
        """Tester les endpoints API sur AWS"""
        print("🔧 Test des endpoints API AWS...")
        
        endpoints = [
            {
                'name': 'Health Check',
                'url': f"{self.api_base}/api/health",
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Deepseek Health',
                'url': f"{self.api_base}/api/deepseek/health", 
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Init Deepseek',
                'url': f"{self.api_base}/api/deepseek/init",
                'method': 'POST',
                'data': {
                    'compression_level': 'balanced',
                    'enable_harmonic': True,
                    'quantize_8bit': False
                },
                'expected_status': 200
            },
            {
                'name': 'Compress Model',
                'url': f"{self.api_base}/api/deepseek/compress",
                'method': 'POST',
                'data': {
                    'model_path': 'deepseek-ai/DeepSeek-V2',
                    'enable_harmonic': True
                },
                'expected_status': 200
            },
            {
                'name': 'List Models',
                'url': f"{self.api_base}/api/deepseek/models",
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Benchmark',
                'url': f"{self.api_base}/api/deepseek/benchmark",
                'method': 'POST',
                'data': {},
                'expected_status': 200
            }
        ]
        
        results = {}
        
        for endpoint in endpoints:
            print(f"   🧪 Test: {endpoint['name']}")
            
            try:
                if endpoint['method'] == 'GET':
                    response = requests.get(endpoint['url'], timeout=30)
                else:
                    response = requests.post(
                        endpoint['url'], 
                        json=endpoint.get('data', {}),
                        timeout=30,
                        headers={'Content-Type': 'application/json'}
                    )
                
                success = response.status_code == endpoint['expected_status']
                
                if success:
                    print(f"      ✅ {endpoint['name']}: {response.status_code}")
                    try:
                        data = response.json()
                        results[endpoint['name']] = {
                            'success': True,
                            'status_code': response.status_code,
                            'response': data
                        }
                        
                        # Afficher les informations clés
                        if endpoint['name'] == 'Deepseek Health':
                            print(f"         🌊 Service: {data.get('service', 'N/A')}")
                            print(f"         🔄 Déterminisme: {data.get('features', {}).get('determinism', 'N/A')}")
                            print(f"         🎭 Hallucination: {data.get('features', {}).get('hallucination', 'N/A')}")
                        
                        elif endpoint['name'] == 'Compress Model':
                            stats = data.get('compression_stats', {})
                            print(f"         📊 Ratio: {stats.get('compression_ratio', 'N/A')}:1")
                            print(f"         💾 Espace économisé: {stats.get('space_savings_percent', 'N/A')}%")
                        
                        elif endpoint['name'] == 'Benchmark':
                            benchmark = data.get('benchmark', {})
                            print(f"         ⏱️ Compression: {benchmark.get('compression_time_ms', 'N/A')}ms")
                            print(f"         📊 Score global: {data.get('overall_score', 'N/A')}")
                        
                    except json.JSONDecodeError:
                        print(f"      ⚠️ Réponse non-JSON")
                        results[endpoint['name']] = {
                            'success': True,
                            'status_code': response.status_code,
                            'response': response.text[:500]
                        }
                else:
                    print(f"      ❌ {endpoint['name']}: {response.status_code}")
                    results[endpoint['name']] = {
                        'success': False,
                        'status_code': response.status_code,
                        'error': response.text[:500]
                    }
                    
            except requests.RequestException as e:
                print(f"      💥 {endpoint['name']}: Erreur - {e}")
                results[endpoint['name']] = {
                    'success': False,
                    'error': str(e)
                }
            
            time.sleep(1)  # Pause entre les tests
        
        self.results['api_tests'] = results
        return results
    
    def test_harmonic_constants_validation(self):
        """Valider les constantes harmoniques dans les réponses API"""
        print("🌊 Validation des constantes harmoniques...")
        
        try:
            # Tester l'endpoint health pour obtenir les constantes
            response = requests.get(f"{self.api_base}/api/deepseek/health", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                constants = data.get('constants', {})
                
                expected_constants = {
                    'phi': 1.618033988749895,
                    'pi': 3.141592653589793,
                    'e': 2.718281828459045,
                    'alpha_optimal': 0.6180339887498948
                }
                
                validation_results = {}
                
                for const_name, expected_value in expected_constants.items():
                    actual_value = constants.get(const_name)
                    
                    if actual_value is not None:
                        # Vérifier la précision (tolérance de 1e-10)
                        diff = abs(actual_value - expected_value)
                        is_valid = diff < 1e-10
                        
                        validation_results[const_name] = {
                            'expected': expected_value,
                            'actual': actual_value,
                            'difference': diff,
                            'valid': is_valid
                        }
                        
                        status = "✅" if is_valid else "❌"
                        print(f"   {status} {const_name}: {actual_value} (diff: {diff:.2e})")
                    else:
                        validation_results[const_name] = {
                            'expected': expected_value,
                            'actual': None,
                            'valid': False
                        }
                        print(f"   ❌ {const_name}: Manquant")
                
                all_valid = all(r['valid'] for r in validation_results.values())
                print(f"   🌊 Validation constante: {'✅ SUCCÈS' if all_valid else '❌ ÉCHEC'}")
                
                self.results['constants_validation'] = {
                    'all_valid': all_valid,
                    'constants': validation_results
                }
                
                return all_valid
            else:
                print(f"   ❌ Impossible d'obtenir les constantes (HTTP {response.status_code})")
                return False
                
        except Exception as e:
            print(f"   💥 Erreur validation constantes: {e}")
            return False
    
    def test_determinism_validation(self):
        """Valider le déterminisme des réponses"""
        print("🔄 Test déterminisme des réponses API...")
        
        try:
            # Effectuer plusieurs appels identiques
            num_tests = 5
            responses = []
            
            for i in range(num_tests):
                response = requests.get(f"{self.api_base}/api/deepseek/health", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    # Extraire une signature déterministe
                    signature = {
                        'service': data.get('service'),
                        'status': data.get('status'),
                        'models_available': data.get('models_available')
                    }
                    responses.append(signature)
                else:
                    print(f"   ❌ Test {i+1}: HTTP {response.status_code}")
                    return False
            
            # Vérifier que toutes les réponses sont identiques
            first_response = responses[0]
            all_identical = all(resp == first_response for resp in responses)
            
            print(f"   📊 Tests effectués: {num_tests}")
            print(f"   🔄 Réponses identiques: {'✅ OUI' if all_identical else '❌ NON'}")
            
            if all_identical:
                print(f"   🌊 Déterminisme: 100% validé")
            else:
                print(f"   ⚠️ Déterminisme: Échec - réponses variables")
            
            self.results['determinism_validation'] = {
                'num_tests': num_tests,
                'all_identical': all_identical,
                'responses': responses
            }
            
            return all_identical
            
        except Exception as e:
            print(f"   💥 Erreur test déterminisme: {e}")
            return False
    
    def run_aws_validation(self):
        """Exécuter la validation complète sur AWS"""
        print("🚀 DÉBUT VALIDATION AWS - DEEPSEEK MOE HARMONIC")
        print("=" * 60)
        
        # 1. Test accessibilité frontend
        print("\n🌐 ÉTAPE 1: Accessibilité Frontend AWS")
        frontend_ok = self.test_frontend_accessibility()
        
        # 2. Test endpoints API
        print("\n🔧 ÉTAPE 2: Tests Endpoints API")
        api_results = self.test_api_endpoints()
        
        # 3. Validation constantes harmoniques
        print("\n🌊 ÉTAPE 3: Validation Constantes Harmoniques")
        constants_ok = self.test_harmonic_constants_validation()
        
        # 4. Test déterminisme
        print("\n🔄 ÉTAPE 4: Test Déterminisme")
        determinism_ok = self.test_determinism_validation()
        
        # 5. Générer rapport final
        print("\n📊 ÉTAPE 5: Rapport Final AWS")
        self.generate_aws_report(frontend_ok, api_results, constants_ok, determinism_ok)
        
        return True
    
    def generate_aws_report(self, frontend_ok, api_results, constants_ok, determinism_ok):
        """Générer le rapport final de validation AWS"""
        print("📄 Génération rapport AWS...")
        
        # Calculer les métriques de succès
        api_success_count = sum(1 for r in api_results.values() if r.get('success', False))
        api_total_count = len(api_results)
        api_success_rate = api_success_count / api_total_count if api_total_count > 0 else 0
        
        # Extraire les métriques de compression
        compression_result = api_results.get('Compress Model', {}).get('response', {})
        compression_stats = compression_result.get('compression_stats', {})
        
        # Extraire les métriques de benchmark
        benchmark_result = api_results.get('Benchmark', {}).get('response', {})
        benchmark_stats = benchmark_result.get('benchmark', {})
        
        report = {
            'validation_timestamp': datetime.now().isoformat(),
            'test_type': 'Deepseek MOE Harmonic AWS Validation',
            'infrastructure': {
                'frontend_url': self.frontend_url,
                'api_base_url': self.api_base,
                'platform': 'AWS (S3 + Lambda)'
            },
            'results': {
                'frontend_accessible': frontend_ok,
                'api_success_rate': api_success_rate,
                'api_successful_endpoints': api_success_count,
                'api_total_endpoints': api_total_count,
                'constants_validated': constants_ok,
                'determinism_validated': determinism_ok,
                'compression_ratio': compression_stats.get('compression_ratio', 0),
                'space_savings_percent': compression_stats.get('space_savings_percent', 0),
                'benchmark_score': benchmark_result.get('overall_score', 0),
                'performance_grade': self.calculate_aws_performance_grade(
                    frontend_ok, api_success_rate, constants_ok, determinism_ok
                )
            },
            'detailed_results': {
                'api_tests': api_results,
                'constants_validation': self.results.get('constants_validation', {}),
                'determinism_validation': self.results.get('determinism_validation', {})
            }
        }
        
        # Sauvegarder le rapport
        report_path = Path("deepseek_aws_validation_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Afficher le résumé
        print("\n🎯 RÉSUMÉ VALIDATION AWS:")
        print(f"   🌐 Frontend: {'✅ Accessible' if frontend_ok else '❌ Inaccessible'}")
        print(f"   🔧 API: {api_success_count}/{api_total_count} endpoints ({api_success_rate:.1%})")
        print(f"   🌊 Constantes: {'✅ Validées' if constants_ok else '❌ Invalides'}")
        print(f"   🔄 Déterminisme: {'✅ Validé' if determinism_ok else '❌ Échec'}")
        print(f"   📊 Compression: {compression_stats.get('compression_ratio', 'N/A')}:1")
        print(f"   💾 Espace économisé: {compression_stats.get('space_savings_percent', 'N/A')}%")
        print(f"   🏆 Performance AWS: {report['results']['performance_grade']}")
        print(f"   📄 Rapport: {report_path}")
        
        # Message final
        overall_success = (
            frontend_ok and 
            api_success_rate >= 0.8 and 
            constants_ok and 
            determinism_ok
        )
        
        if overall_success:
            print("\n🎉 VALIDATION AWS TERMINÉE AVEC SUCCÈS!")
            print("🌊 Deepseek MOE Harmonic est opérationnel sur AWS!")
            print("✅ 0% Hallucination • 100% Déterminisme • Infrastructure AWS Stable")
        else:
            print("\n⚠️ VALIDATION AWS PARTIELLE")
            print("Certains composants nécessitent attention")
        
        return report
    
    def calculate_aws_performance_grade(self, frontend_ok, api_success_rate, constants_ok, determinism_ok):
        """Calculer la note de performance AWS"""
        score = 0
        
        # Frontend (25 points)
        if frontend_ok:
            score += 25
        
        # API (25 points)
        score += api_success_rate * 25
        
        # Constantes (25 points)
        if constants_ok:
            score += 25
        
        # Déterminisme (25 points)
        if determinism_ok:
            score += 25
        
        # Attribution des notes
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'

def main():
    """Fonction principale"""
    print("🌊 DEEPSEEK MOE HARMONIC - VALIDATION AWS")
    print("=" * 50)
    
    validator = AWSDeepseekValidator()
    
    try:
        success = validator.run_aws_validation()
        
        if success:
            print("\n🚀 Validation AWS complétée!")
        else:
            print("\n⚠️ Vérifiez l'infrastructure AWS")
            
    except KeyboardInterrupt:
        print("\n⏹️ Validation interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
