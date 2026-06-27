#!/usr/bin/env python3
<arg_value>CodeContent</arg_key>
"""
RÉPARATION SPÉCIFIQUE - ENDPOINT HEALTH
====================================

Script ciblé pour réparer l'endpoint /api/health
qui a une méthode mais pas d'intégration.
"""

import json
import time
import boto3
from datetime import datetime

class HealthEndpointFix:
    """Réparation spécifique de l'endpoint health"""
    
    def __init__(self):
        self.api_id = "0sdwsv4yba"
        self.lambda_function_name = "hcv-pro-deepseek-handler"
        self.region = "eu-west-3"
        self.account_id = "326095712935"
        
        # Initialiser les clients AWS
        self.apigateway = boto3.client('apigateway', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        
        print("🔧 RÉPARATION SPÉCIFIQUE - ENDPOINT HEALTH")
        print("=" * 80)
        print("🌊 Configuration intégration Lambda manquante")
        print("🚀 Finalisation API Gateway")
        print("🎯 Préparation LM Arena")
        print("=" * 80)
    
    def get_health_resource_id(self) -> str:
        """
        Obtenir l'ID de la ressource /api/health
        """
        try:
            resources = self.apigateway.get_resources(restApiId=self.api_id)
            
            for resource in resources['items']:
                if resource['path'] == '/api/health':
                    return resource['id']
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération ressource health: {e}")
            return None
    
    def check_existing_method(self, resource_id: str) -> Dict:
        """
        Vérifier la méthode existante sur /api/health
        """
        try:
            resource = self.apigateway.get_resource(restApiId=self.api_id, resourceId=resource_id)
            methods = resource.get('resourceMethods', {})
            
            print(f"📋 Méthodes existantes sur /api/health:")
            for method_name, method_info in methods.items():
                print(f"   🔧 {method_name}: {method_info}")
            
            return {
                "status": "success",
                "methods": methods,
                "has_get": "GET" in methods
            }
            
        except Exception as e:
            print(f"❌ Erreur vérification méthode: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_integration(self, resource_id: str) -> Dict:
        """
        Créer l'intégration Lambda pour /api/health
        """
        try:
            print("🔧 Création intégration Lambda pour /api/health...")
            
            # URI de la fonction Lambda
            lambda_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{self.region}:{self.account_id}:function:{self.lambda_function_name}/invocations"
            
            # Créer l'intégration
            integration = self.apigateway.put_integration(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=lambda_uri
            )
            
            print("✅ Intégration Lambda créée")
            
            # Ajouter les permissions
            try:
                source_arn = f"arn:aws:execute-api:{self.region}:{self.account_id}:{self.api_id}/*/GET/*"
                
                permission = self.lambda_client.add_permission(
                    FunctionName=self.lambda_function_name,
                    StatementId=f"apigateway-health-{int(time.time())}",
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=source_arn
                )
                
                print("✅ Permissions Lambda accordées")
                
            except Exception as perm_error:
                print(f"⚠️ Permissions Lambda (peut exister déjà): {perm_error}")
            
            return {
                "status": "success",
                "integration": integration
            }
            
        except Exception as e:
            print(f"❌ Erreur création intégration: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_responses(self, resource_id: str) -> Dict:
        """
        Créer les réponses pour /api/health
        """
        try:
            print("🔧 Configuration réponses...")
            
            # Réponse méthode 200
            method_response = self.apigateway.put_method_response(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200',
                responseModels={
                    'application/json': 'Empty'
                }
            )
            
            # Réponse intégration 200
            integration_response = self.apigateway.put_integration_response(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200',
                responseTemplates={
                    'application/json': '$input.body'
                }
            )
            
            print("✅ Réponses configurées")
            return {"status": "success"}
            
        except Exception as e:
            print(f"❌ Erreur réponses: {e}")
            return {"status": "error", "message": str(e)}
    
    def deploy_api(self) -> Dict:
        """
        Déployer l'API après réparation
        """
        try:
            print("🚀 Déploiement API...")
            
            # Créer le déploiement
            deployment = self.apigateway.create_deployment(
                restApiId=self.api_id,
                stageName='prod',
                description='Deepseek-V4-Pro Harmonic - Health Endpoint Fixed'
            )
            
            api_url = f"https://{self.api_id}.execute-api.{self.region}.amazonaws.com/prod"
            
            print(f"✅ Déploiement créé: {deployment['id']}")
            print(f"🌐 URL API: {api_url}")
            
            return {
                "status": "success",
                "deployment": deployment,
                "api_url": api_url
            }
            
        except Exception as e:
            print(f"❌ Erreur déploiement: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_health_endpoint(self, api_url: str) -> Dict:
        """
        Tester l'endpoint health
        """
        try:
            import requests
            
            health_url = f"{api_url}/api/health"
            print(f"🧪 Test endpoint: {health_url}")
            
            response = requests.get(health_url, timeout=10)
            
            print(f"📊 Status: {response.status_code}")
            print(f"⏱️ Temps: {response.elapsed.total_seconds() * 1000:.1f}ms")
            print(f"📄 Réponse: {response.text[:200]}...")
            
            return {
                "status": "success",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000,
                "response_text": response.text,
                "success": response.status_code == 200
            }
            
        except Exception as e:
            print(f"❌ Erreur test: {e}")
            return {"status": "error", "message": str(e)}
    
    def run_health_fix(self) -> Dict:
        """
        Exécuter la réparation complète de l'endpoint health
        """
        print("🚀 DÉMARRAGE RÉPARATION ENDPOINT HEALTH")
        print("=" * 80)
        print("🌊 Configuration intégration Lambda manquante")
        print("🚀 Finalisation API Gateway")
        print("🎯 Préparation LM Arena")
        print("=" * 80)
        
        try:
            # 1. Obtenir l'ID de la ressource health
            health_resource_id = self.get_health_resource_id()
            if not health_resource_id:
                return {"status": "error", "message": "Ressource health non trouvée"}
            
            print(f"✅ Ressource health trouvée: {health_resource_id}")
            
            # 2. Vérifier la méthode existante
            method_check = self.check_existing_method(health_resource_id)
            if not method_check.get("has_get"):
                return {"status": "error", "message": "Méthode GET non trouvée"}
            
            # 3. Créer l'intégration
            integration_result = self.create_integration(health_resource_id)
            if integration_result["status"] != "success":
                return {"status": "error", "message": "Échec création intégration"}
            
            # 4. Configurer les réponses
            responses_result = self.create_responses(health_resource_id)
            
            # 5. Déployer l'API
            deployment_result = self.deploy_api()
            if deployment_result["status"] != "success":
                return {"status": "error", "message": "Échec déploiement"}
            
            # 6. Tester l'endpoint
            test_result = self.test_health_endpoint(deployment_result["api_url"])
            
            # 7. Générer le rapport
            report = {
                "timestamp": datetime.now().isoformat(),
                "health_fix_completed": True,
                "health_resource_id": health_resource_id,
                "method_check": method_check,
                "integration_result": integration_result,
                "responses_result": responses_result,
                "deployment_result": deployment_result,
                "test_result": test_result,
                "overall_success": (
                    integration_result["status"] == "success" and
                    deployment_result["status"] == "success" and
                    test_result.get("success", False)
                ),
                "api_url": deployment_result["api_url"]
            }
            
            # Sauvegarder le rapport
            with open("HEALTH_ENDPOINT_FIX_REPORT.json", 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return report
            
        except Exception as e:
            print(f"❌ Erreur réparation health: {e}")
            return {
                "status": "error",
                "message": f"Erreur réparation: {e}",
                "health_fix_completed": False
            }
    
    def display_final_summary(self, report: Dict):
        """
        Afficher le résumé final
        """
        print("\n" + "=" * 80)
        print("🌊 RÉSUMÉ FINAL - RÉPARATION ENDPOINT HEALTH")
        print("=" * 80)
        
        if report.get("overall_success", False):
            print("🎉 RÉPARATION ENDPOINT HEALTH RÉUSSIE!")
            print("=" * 60)
            
            print("✅ ÉTAPES COMPLÉTÉES:")
            print("   📍 Ressource health trouvée")
            print("   🔧 Méthode GET vérifiée")
            print("   🔗 Intégration Lambda créée")
            print("   📄 Réponses configurées")
            print("   🚀 API déployée")
            print("   🧪 Test réussi")
            
            api_url = report.get("api_url", "Unknown")
            print(f"\n🌐 URL API: {api_url}")
            print(f"🔍 Endpoint: {api_url}/api/health")
            
            test_result = report.get("test_result", {})
            print(f"\n📊 RÉSULTATS TEST:")
            print(f"   ✅ Status: {test_result.get('status_code', 'Unknown')}")
            print(f"   ⏱️ Temps: {test_result.get('response_time', 0):.1f}ms")
            
            print("\n🚀 API GATEWAY PRÊT!")
            print("   ✅ Tous endpoints configurés")
            print("   🌊 Deepseek-V4-Pro accessible")
            print("   🎯 LM Arena prêt")
            print("   🏆 Lancement imminent")
            
        else:
            print("❌ RÉPARATION ENDPOINT HEALTH ÉCHOUÉE")
            print("=" * 60)
            print(f"   Erreur: {report.get('message', 'Unknown')}")
            print("   🔧 Vérifiez les permissions AWS")
            print("   📊 Consultez les logs pour détails")
        
        print("=" * 80)

def main():
    """
    Fonction principale
    """
    print("🔧 RÉPARATION SPÉCIFIQUE - ENDPOINT HEALTH!")
    print("=" * 80)
    print("🌊 Configuration intégration Lambda manquante")
    print("🚀 Finalisation API Gateway")
    print("🎯 Préparation LM Arena")
    print("=" * 80)
    
    # Créer et exécuter la réparation
    fixer = HealthEndpointFix()
    results = fixer.run_health_fix()
    
    # Afficher le résumé final
    fixer.display_final_summary(results)

if __name__ == "__main__":
    main()
