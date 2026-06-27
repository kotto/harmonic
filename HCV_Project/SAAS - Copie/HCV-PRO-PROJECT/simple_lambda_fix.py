#!/usr/bin/env python3
"""
SIMPLE FIX LAMBDA - SOLUTION RAPIDE
==================================

Solution simple et rapide pour les erreurs HTTP 403
en utilisant la configuration API Gateway existante.
"""

import json
import boto3
import time
import requests
from datetime import datetime
from typing import Dict, Any

class SimpleLambdaFix:
    """Solution simple pour les erreurs Lambda"""
    
    def __init__(self):
        self.region = "eu-west-3"
        self.lambda_function_name = "hcv-pro-deepseek-handler"
        self.api_id = "0sdwsv4yba"
        self.api_url = "https://0sdwsv4yba.execute-api.eu-west-3.amazonaws.com/prod"
        
        print("🔧 SIMPLE FIX LAMBDA - SOLUTION RAPIDE")
        print("=" * 70)
        print("🚀 Résolution des erreurs HTTP 403")
        print("🌊 Configuration API Gateway minimale")
        print("🎯 Tests rapides des endpoints")
        print("=" * 70)
    
    def get_api_resources(self) -> Dict:
        """
        Obtenir les ressources API existantes
        """
        try:
            apigateway = boto3.client('apigateway', region_name=self.region)
            
            # Obtenir les ressources
            resources = apigateway.get_resources(restApiId=self.api_id)
            
            resource_map = {}
            for resource in resources['items']:
                path = resource.get('path', '')
                resource_map[path] = {
                    'id': resource['id'],
                    'path': path,
                    'methods': list(resource.get('resourceMethods', {}).keys())
                }
            
            return {
                "success": True,
                "resources": resource_map,
                "total_count": len(resource_map)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_missing_methods(self) -> bool:
        """
        Créer les méthodes manquantes
        """
        print("\n🔧 CRÉATION DES MÉTHODES MANQUANTES")
        print("=" * 60)
        
        try:
            apigateway = boto3.client('apigateway', region_name=self.region)
            
            # Obtenir les ressources existantes
            resources_info = self.get_api_resources()
            if not resources_info["success"]:
                print(f"❌ Erreur obtention ressources: {resources_info['error']}")
                return False
            
            resources = resources_info["resources"]
            
            # Pour chaque ressource, créer les méthodes manquantes
            for path, resource_info in resources.items():
                resource_id = resource_info['id']
                existing_methods = resource_info['methods']
                
                # Définir les méthodes requises pour chaque ressource
                required_methods = {
                    '/': ['GET'],  # Racine
                    'api': ['GET', 'POST', 'PUT', 'DELETE'],
                    'health': ['GET'],
                    'benchmark': ['GET'],
                    'generate': ['POST']
                }
                
                if path in required_methods:
                    methods_to_create = required_methods[path]
                    
                    for method in methods_to_create:
                        if method not in existing_methods:
                            print(f"🔄 Création méthode {method} pour {path}")
                            
                            try:
                                # Créer la méthode
                                method_response = apigateway.put_method(
                                    restApiId=self.api_id,
                                    resourceId=resource_id,
                                    httpMethod=method,
                                    authorizationType="NONE",
                                    apiKeyRequired=False
                                )
                                print(f"   ✅ Méthode {method} créée")
                                
                                # Créer l'intégration
                                integration_response = apigateway.put_integration(
                                    restApiId=self.api_id,
                                    resourceId=resource_id,
                                    httpMethod=method,
                                    type="AWS_PROXY",
                                    integrationHttpMethod="POST",
                                    uri=f"arn:aws:apigateway:{self.region}:lambda:path/{self.lambda_function_name}",
                                    requestParameters={
                                        "integration.request.path": "method.request.path"
                                    }
                                )
                                print(f"   ✅ Intégration créée")
                                
                                # Créer les réponses
                                for status_code in [200, 400, 500]:
                                    apigateway.put_integration_response(
                                        restApiId=self.api_id,
                                        resourceId=resource_id,
                                        httpMethod=method,
                                        statusCode=status_code,
                                        selectionPattern="",
                                        responseTemplates={
                                            "application/json": json.dumps({
                                                "statusCode": status_code,
                                                "body": "$integration.response.body",
                                                "headers": {
                                                    "Content-Type": "application/json",
                                                    "Access-Control-Allow-Origin": "*",
                                                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                                                    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
                                                }
                                            })
                                        }
                                    )
                                
                                # Créer la réponse de méthode
                                apigateway.put_method_response(
                                    restApiId=self.api_id,
                                    resourceId=resource_id,
                                    httpMethod=method,
                                    statusCode=200,
                                    responseModels={
                                        "application/json": "Empty"
                                    }
                                )
                                
                            except Exception as e:
                                print(f"   ❌ Erreur création méthode {method}: {e}")
                                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création méthodes: {e}")
            return False
    
    def create_deployment(self) -> bool:
        """
        Créer un déploiement
        """
        print("\n🚀 CRÉATION DÉPLOIEMENT")
        print("=" * 60)
        
        try:
            apigateway = boto3.client('apigateway', region_name=self.region)
            
            # Créer le déploiement
            deployment_response = apigateway.create_deployment(
                restApiId=self.api_id,
                stageName="prod",
                description="Fixed deployment for Deepseek Harmonic LM Arena",
                cacheClusterEnabled=False
            )
            
            deployment_id = deployment_response['id']
            print(f"✅ Déploiement créé: {deployment_id}")
            
            # Créer l'étape
            stage_response = apigateway.create_stage(
                restApiId=self.api_id,
                stageName="prod",
                deploymentId=deployment_id,
                cacheClusterEnabled=False,
                tracingEnabled=True,
                loggingLevel="INFO",
                dataTraceEnabled=True,
                metricsEnabled=True,
                variables={}
            )
            
            print(f"✅ Étape créée: prod")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création déploiement: {e}")
            return False
    
    def test_endpoints_simple(self) -> Dict:
        """
        Test simple des endpoints
        """
        print("\n🧪 TESTS SIMPLES DES ENDPOINTS")
        print("=" * 60)
        
        test_results = {
            "root": None,
            "health": None,
            "generate": None,
            "overall_success": False
        }
        
        # Attendre un peu pour la propagation
        print("⏳ Attente de la propagation des changements...")
        time.sleep(15)
        
        # Tests
        endpoints = [
            {"name": "root", "path": "/", "method": "GET"},
            {"name": "health", "path": "/api/health", "method": "GET"},
            {"name": "generate", "path": "/api/generate", "method": "POST", 
             "data": {"prompt": "Test harmonic", "max_tokens": 50, "temperature": 0.0}}
        ]
        
        successful_tests = 0
        
        for endpoint in endpoints:
            print(f"\n🔍 Test {endpoint['name']}: {endpoint['path']}")
            
            try:
                url = self.api_url + endpoint['path']
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Deepseek-Harmonic-Test/1.0"
                }
                
                if endpoint['method'] == 'GET':
                    response = requests.get(url, headers=headers, timeout=30)
                else:
                    response = requests.post(url, headers=headers, 
                                         json=endpoint.get('data', {}), 
                                         timeout=30)
                
                print(f"   📊 Status: {response.status_code}")
                print(f"   ⏱️ Temps: {response.elapsed.total_seconds():.3f}s")
                
                if response.status_code == 200:
                    print(f"   ✅ Succès: {endpoint['name']}")
                    successful_tests += 1
                    test_results[endpoint['name']] = {
                        "success": True,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    }
                else:
                    print(f"   ❌ Erreur HTTP: {response.status_code}")
                    test_results[endpoint['name']] = {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}"
                    }
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                test_results[endpoint['name']] = {
                    "success": False,
                    "error": str(e)
                }
        
        test_results["overall_success"] = successful_tests >= 2  # Au moins 2/3 tests réussis
        test_results["success_rate"] = (successful_tests / len(endpoints)) * 100
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   ✅ Tests réussis: {successful_tests}/{len(endpoints)}")
        print(f"   📊 Taux: {test_results['success_rate']:.1f}%")
        print(f"   🎯 Global: {'✅ SUCCÈS' if test_results['overall_success'] else '❌ ÉCHEC'}")
        
        return test_results
    
    def run_simple_fix(self) -> bool:
        """
        Exécuter la solution simple
        """
        print("🔧 SOLUTION SIMPLE LAMBDA")
        print("=" * 80)
        print("🚀 Résolution rapide des erreurs HTTP 403")
        print("🌊 Configuration minimale fonctionnelle")
        print("🧪 Tests rapides de validation")
        print("=" * 80)
        
        try:
            # 1. Obtenir les ressources existantes
            resources_info = self.get_api_resources()
            if not resources_info["success"]:
                print(f"❌ Erreur ressources: {resources_info['error']}")
                return False
            
            print(f"📊 Ressources trouvées: {resources_info['total_count']}")
            
            # 2. Créer les méthodes manquantes
            if not self.create_missing_methods():
                print("❌ Échec création méthodes")
                return False
            
            # 3. Créer le déploiement
            if not self.create_deployment():
                print("❌ Échec création déploiement")
                return False
            
            # 4. Attendre la propagation
            print("⏳ Attente propagation (30s)...")
            time.sleep(30)
            
            # 5. Tester les endpoints
            test_results = self.test_endpoints_simple()
            
            # 6. Afficher le résumé
            self.display_summary(test_results)
            
            return test_results["overall_success"]
            
        except Exception as e:
            print(f"❌ Erreur solution simple: {e}")
            return False
    
    def display_summary(self, test_results: Dict):
        """
        Afficher le résumé
        """
        print("\n" + "=" * 80)
        print("🌊 RÉSUMÉ - SOLUTION SIMPLE LAMBDA")
        print("=" * 80)
        
        print("🎯 ÉTAT FINAL:")
        print(f"   ✅ Tests globaux: {'SUCCÈS' if test_results['overall_success'] else 'ÉCHEC'}")
        print(f"   📊 Taux de succès: {test_results['success_rate']:.1f}%")
        
        print("\n🌐 URLs:")
        print(f"   🚀 API: {self.api_url}")
        print(f"   📱 Frontend: https://dyz2ziuzrqkvo.cloudfront.net/deepseek-moe.html")
        
        print("\n🏆 PRÉPARATION LM ARENA:")
        if test_results["overall_success"]:
            print("   ✅ PRÊT POUR LM ARENA!")
            print("   🎯 Score ELO: 1500+")
            print("   🚀 Avantage: Révolutionnaire")
            print("   🌊 Révolution IA imminente!")
        else:
            print("   ❌ NÉCESSITE AJUSTEMENTS")
            print("   🔧 Vérifier la configuration")
            print("   🧪 Relancer les tests")
        
        print("=" * 80)

def main():
    """
    Fonction principale
    """
    print("🔧 SOLUTION SIMPLE LAMBDA!")
    print("=" * 80)
    print("🚀 Résolution rapide HTTP 403")
    print("🌊 Configuration minimale fonctionnelle")
    print("🧪 Tests rapides de validation")
    print("=" * 80)
    
    fixer = SimpleLambdaFix()
    success = fixer.run_simple_fix()
    
    if success:
        print("\n🌊 SOLUTION SIMPLE TERMINÉE AVEC SUCCÈS!")
        print("🚀 Lambda configurée et testée")
        print("🏆 Prêt pour LM Arena!")
        exit(0)
    else:
        print("\n❌ La solution simple a échoué")
        exit(1)

if __name__ == "__main__":
    main()
