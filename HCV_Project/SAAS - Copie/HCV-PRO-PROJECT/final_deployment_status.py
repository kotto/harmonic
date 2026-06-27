#!/usr/bin/env python3
"""
STATUT FINAL DU DÉPLOIEMENT AWS - RÉCAPITULATIF COMPLET
====================================================

Analyse complète du déploiement AWS existant et recommandations
pour le lancement sur LM Arena avec Deepseek Harmonique.
"""

import json
import boto3
from datetime import datetime
from pathlib import Path

class FinalDeploymentStatus:
    """Analyse du statut final du déploiement"""
    
    def __init__(self):
        self.region = "eu-west-3"
        self.account_id = "326095712935"
        self.bucket_name = "hcv-pro-deepseek-frontend-326095712935"
        self.cloudfront_domain = "dyz2ziuzrqkvo.cloudfront.net"
        self.lambda_function_name = "hcv-pro-deepseek-handler"
        
        print("🔍 STATUT FINAL DU DÉPLOIEMENT AWS")
        print("=" * 70)
        print("🌊 Deepseek Harmonique + LM Arena")
        print("📊 Analyse complète de l'infrastructure")
        print("🚀 Recommandations pour le lancement")
        print("=" * 70)
    
    def analyze_current_status(self) -> dict:
        """
        Analyser le statut actuel complet
        """
        print("\n📊 ANALYSE DU STATUT ACTUEL")
        print("=" * 60)
        
        status = {
            "s3_status": self.check_s3_status(),
            "cloudfront_status": self.check_cloudfront_status(),
            "lambda_status": self.check_lambda_status(),
            "api_gateway_status": self.check_api_gateway_status(),
            "overall_health": "unknown"
        }
        
        # Évaluer la santé globale
        healthy_components = sum(1 for comp in status.values() if isinstance(comp, dict) and comp.get("healthy", False))
        total_components = 4
        
        if healthy_components == total_components:
            status["overall_health"] = "excellent"
        elif healthy_components >= 3:
            status["overall_health"] = "good"
        elif healthy_components >= 2:
            status["overall_health"] = "fair"
        else:
            status["overall_health"] = "poor"
        
        return status
    
    def check_s3_status(self) -> dict:
        """
        Vérifier le statut S3
        """
        try:
            s3_client = boto3.client('s3', region_name=self.region)
            
            # Vérifier l'existence du bucket
            s3_client.head_bucket(Bucket=self.bucket_name)
            
            # Vérifier les fichiers clés
            key_files = ['deepseek-moe.html', 'index.html']
            existing_files = []
            
            for file_key in key_files:
                try:
                    s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
                    existing_files.append(file_key)
                except:
                    pass
            
            # Vérifier la configuration du site web
            try:
                website_config = s3_client.get_bucket_website(Bucket=self.bucket_name)
                index_suffix = website_config.get('IndexDocument', {}).get('Suffix', '')
                website_configured = index_suffix == 'deepseek-moe.html'
            except:
                website_configured = False
            
            return {
                "healthy": True,
                "bucket_accessible": True,
                "existing_files": existing_files,
                "website_configured": website_configured,
                "url": f"http://{self.bucket_name}.s3-website-{self.region}.amazonaws.com",
                "frontend_url": f"http://{self.bucket_name}.s3-website-{self.region}.amazonaws.com/deepseek-moe.html"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "bucket_accessible": False
            }
    
    def check_cloudfront_status(self) -> dict:
        """
        Vérifier le statut CloudFront
        """
        try:
            cloudfront = boto3.client('cloudfront')
            
            # Lister les distributions
            distributions = cloudfront.list_distributions()
            cloudfront_found = False
            
            for dist in distributions['DistributionList'].get('Items', []):
                if dist['DomainName'] == self.cloudfront_domain:
                    cloudfront_found = True
                    status = dist.get('Status', 'Unknown')
                    enabled = dist.get('Enabled', False)
                    
                    return {
                        "healthy": enabled and status == 'Deployed',
                        "domain": self.cloudfront_domain,
                        "status": status,
                        "enabled": enabled,
                        "frontend_url": f"https://{self.cloudfront_domain}/deepseek-moe.html"
                    }
            
            return {
                "healthy": False,
                "error": "CloudFront distribution non trouvée",
                "domain": self.cloudfront_domain
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def check_lambda_status(self) -> dict:
        """
        Vérifier le statut Lambda
        """
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Obtenir les informations de la fonction
            response = lambda_client.get_function(FunctionName=self.lambda_function_name)
            
            config = response['Configuration']
            state = config.get('State', 'Unknown')
            last_update_status = config.get('LastUpdateStatus', 'Unknown')
            
            # Vérifier l'environnement
            env_vars = config.get('Environment', {}).get('Variables', {})
            
            # Tester la fonction
            try:
                test_event = {
                    "httpMethod": "GET",
                    "path": "/api/health",
                    "headers": {"Content-Type": "application/json"},
                    "body": ""
                }
                
                invoke_response = lambda_client.invoke(
                    FunctionName=self.lambda_function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_event)
                )
                
                payload = json.loads(invoke_response['Payload'].read().decode('utf-8'))
                function_working = payload.get('statusCode') == 200
                
            except:
                function_working = False
            
            return {
                "healthy": state == 'Active' and last_update_status == 'Successful' and function_working,
                "state": state,
                "last_update_status": last_update_status,
                "runtime": config.get('Runtime', 'Unknown'),
                "memory": config.get('MemorySize', 0),
                "timeout": config.get('Timeout', 0),
                "environment": env_vars,
                "function_working": function_working,
                "arn": config.get('FunctionArn', '')
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def check_api_gateway_status(self) -> dict:
        """
        Vérifier le statut API Gateway
        """
        try:
            apigateway = boto3.client('apigateway', region_name=self.region)
            
            # Lister les APIs
            apis = apigateway.get_rest_apis()
            api_found = False
            
            for api in apis['items']:
                if 'deepseek' in api['name'].lower():
                    api_found = True
                    
                    # Obtenir les ressources
                    resources = apigateway.get_resources(restApiId=api['id'])
                    resource_count = len(resources['items'])
                    
                    return {
                        "healthy": True,
                        "api_id": api['id'],
                        "name": api['name'],
                        "description": api.get('description', ''),
                        "resource_count": resource_count,
                        "api_url": f"https://{api['id']}.execute-api.{self.region}.amazonaws.com/prod"
                    }
            
            return {
                "healthy": False,
                "error": "API Gateway non trouvée",
                "api_found": api_found
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def generate_lm_arena_readiness_report(self, status: dict) -> dict:
        """
        Générer le rapport de préparation LM Arena
        """
        print("\n🎯 RAPPORT DE PRÉPARATION LM ARENA")
        print("=" * 60)
        
        readiness = {
            "lm_arena_ready": False,
            "overall_score": 0,
            "components_ready": {},
            "missing_items": [],
            "recommendations": [],
            "estimated_effort": "unknown"
        }
        
        scores = {}
        
        # Évaluer S3
        s3_status = status["s3_status"]
        if s3_status.get("healthy", False):
            s3_score = 25
            readiness["components_ready"]["s3"] = True
            if "deepseek-moe.html" in s3_status.get("existing_files", []):
                s3_score += 25
            else:
                readiness["missing_items"].append("Fichier deepseek-moe.html sur S3")
        else:
            s3_score = 0
            readiness["components_ready"]["s3"] = False
            readiness["missing_items"].append("Configuration S3")
        scores["s3"] = s3_score
        
        # Évaluer CloudFront
        cf_status = status["cloudfront_status"]
        if cf_status.get("healthy", False):
            cf_score = 50
            readiness["components_ready"]["cloudfront"] = True
        else:
            cf_score = 0
            readiness["components_ready"]["cloudfront"] = False
            readiness["missing_items"].append("Configuration CloudFront")
        scores["cloudfront"] = cf_score
        
        # Évaluer Lambda
        lambda_status = status["lambda_status"]
        if lambda_status.get("healthy", False):
            lambda_score = 50
            readiness["components_ready"]["lambda"] = True
            
            # Vérifier les variables d'environnement
            env_vars = lambda_status.get("environment", {})
            required_vars = ["HARMONIC_MODE", "DETERMINISTIC_MODE", "LM_ARENA_MODE"]
            missing_vars = [var for var in required_vars if var not in env_vars]
            
            if missing_vars:
                lambda_score -= 10
                readiness["missing_items"].extend([f"Variable {var}" for var in missing_vars])
        else:
            lambda_score = 0
            readiness["components_ready"]["lambda"] = False
            readiness["missing_items"].append("Configuration Lambda")
        scores["lambda"] = lambda_score
        
        # Évaluer API Gateway
        api_status = status["api_gateway_status"]
        if api_status.get("healthy", False):
            api_score = 50
            readiness["components_ready"]["api_gateway"] = True
        else:
            api_score = 0
            readiness["components_ready"]["api_gateway"] = False
            readiness["missing_items"].append("Configuration API Gateway")
        scores["api_gateway"] = api_score
        
        # Calculer le score total
        total_score = sum(scores.values())
        max_score = 200
        readiness["overall_score"] = (total_score / max_score) * 100
        
        # Déterminer si prêt pour LM Arena
        readiness["lm_arena_ready"] = readiness["overall_score"] >= 75
        
        # Générer les recommandations
        if readiness["overall_score"] < 100:
            readiness["recommendations"] = [
                "Compléter la configuration des composants manquants",
                "Tester tous les endpoints API",
                "Valider la performance déterministe",
                "Préparer la documentation LM Arena"
            ]
        
        # Estimer l'effort
        if readiness["overall_score"] >= 90:
            readiness["estimated_effort"] = "Minimal - < 1 heure"
        elif readiness["overall_score"] >= 75:
            readiness["estimated_effort"] = "Modéré - 2-4 heures"
        elif readiness["overall_score"] >= 50:
            readiness["estimated_effort"] = "Significatif - 1-2 jours"
        else:
            readiness["estimated_effort"] = "Majeur - 3-5 jours"
        
        # Afficher le rapport
        print(f"📊 Score de préparation: {readiness['overall_score']:.1f}%")
        print(f"🎯 Prêt pour LM Arena: {'✅ OUI' if readiness['lm_arena_ready'] else '❌ NON'}")
        print(f"⏱️ Effort estimé: {readiness['estimated_effort']}")
        
        if readiness["missing_items"]:
            print("\n❌ Éléments manquants:")
            for item in readiness["missing_items"]:
                print(f"   • {item}")
        
        if readiness["recommendations"]:
            print("\n💡 Recommandations:")
            for rec in readiness["recommendations"]:
                print(f"   • {rec}")
        
        return readiness
    
    def create_action_plan(self, status: dict, readiness: dict) -> dict:
        """
        Créer le plan d'action
        """
        print("\n🚀 PLAN D'ACTION POUR LM ARENA")
        print("=" * 60)
        
        action_plan = {
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_actions": [],
            "success_criteria": {},
            "timeline": {}
        }
        
        # Actions immédiates (dans l'heure)
        if not status["s3_status"].get("healthy", False):
            action_plan["immediate_actions"].append("Configurer le bucket S3 avec politique d'accès public")
        
        if not status["cloudfront_status"].get("healthy", False):
            action_plan["immediate_actions"].append("Activer et configurer la distribution CloudFront")
        
        if not status["lambda_status"].get("healthy", False):
            action_plan["immediate_actions"].append("Finaliser la mise à jour de la fonction Lambda")
        
        # Actions court terme (1-2 jours)
        action_plan["short_term_actions"] = [
            "Tester tous les endpoints API",
            "Valider la performance déterministe",
            "Optimiser les temps de réponse",
            "Créer la documentation LM Arena"
        ]
        
        # Actions long terme (1 semaine)
        action_plan["long_term_actions"] = [
            "Monitorer les performances en production",
            "Optimiser basé sur l'usage réel",
            "Préparer l'expansion pour charge virale",
            "Développer les prochaines fonctionnalités"
        ]
        
        # Critères de succès
        action_plan["success_criteria"] = {
            "technical": [
                "Frontend accessible via CloudFront",
                "API Lambda fonctionnelle avec <100ms response time",
                "Couche harmonique activée et testée",
                "0% hallucination validé"
            ],
            "lm_arena": [
                "Score ELO > 1400",
                "Win rate > 95% vs modèles existants",
                "Consistency = 100%",
                "User preference > 90%"
            ],
            "operational": [
                "Uptime > 99.9%",
                "Auto-scaling fonctionnel",
                "Monitoring complet",
                "Alerting configuré"
            ]
        }
        
        # Timeline
        action_plan["timeline"] = {
            "day_1": "Actions immédiates - Configuration de base",
            "day_2_3": "Actions court terme - Tests et validation",
            "day_4_7": "Actions long terme - Optimisation",
            "day_8": "Lancement officiel LM Arena"
        }
        
        # Afficher le plan
        print("🚀 ACTIONS IMMÉDIATES (Aujourd'hui):")
        for action in action_plan["immediate_actions"]:
            print(f"   • {action}")
        
        print("\n📅 ACTIONS COURT TERME (1-2 jours):")
        for action in action_plan["short_term_actions"]:
            print(f"   • {action}")
        
        print("\n🌊 ACTIONS LONG TERME (1 semaine):")
        for action in action_plan["long_term_actions"]:
            print(f"   • {action}")
        
        return action_plan
    
    def generate_final_report(self):
        """
        Générer le rapport final complet
        """
        print("\n" + "=" * 80)
        print("🌊 RAPPORT FINAL - DÉPLOIEMENT AWS POUR LM ARENA")
        print("=" * 80)
        
        # Analyser le statut actuel
        status = self.analyze_current_status()
        
        # Générer le rapport de préparation
        readiness = self.generate_lm_arena_readiness_report(status)
        
        # Créer le plan d'action
        action_plan = self.create_action_plan(status, readiness)
        
        # Créer le rapport final
        final_report = {
            "timestamp": datetime.now().isoformat(),
            "deployment_status": status,
            "lm_arena_readiness": readiness,
            "action_plan": action_plan,
            "summary": {
                "overall_health": status["overall_health"],
                "lm_arena_ready": readiness["lm_arena_ready"],
                "readiness_score": readiness["overall_score"],
                "estimated_effort": readiness["estimated_effort"],
                "recommended_launch_date": self.calculate_launch_date(readiness)
            }
        }
        
        # Sauvegarder le rapport
        report_path = "FINAL_DEPLOYMENT_REPORT.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Rapport final sauvegardé: {report_path}")
        
        # Afficher le résumé final
        print("\n🏆 RÉSUMÉ FINAL:")
        print(f"🌊 Santé globale: {status['overall_health']}")
        print(f"🎯 Prêt pour LM Arena: {'✅ OUI' if readiness['lm_arena_ready'] else '❌ NON'}")
        print(f"📊 Score de préparation: {readiness['overall_score']:.1f}%")
        print(f"⏱️ Effort requis: {readiness['estimated_effort']}")
        print(f"🚅 Date de lancement recommandée: {self.calculate_launch_date(readiness)}")
        
        return final_report
    
    def calculate_launch_date(self, readiness: dict) -> str:
        """
        Calculer la date de lancement recommandée
        """
        from datetime import datetime, timedelta
        
        if readiness["overall_score"] >= 90:
            launch_date = datetime.now() + timedelta(days=1)
        elif readiness["overall_score"] >= 75:
            launch_date = datetime.now() + timedelta(days=3)
        elif readiness["overall_score"] >= 50:
            launch_date = datetime.now() + timedelta(days=7)
        else:
            launch_date = datetime.now() + timedelta(days=14)
        
        return launch_date.strftime("%Y-%m-%d")

def main():
    """
    Fonction principale
    """
    print("🔍 STATUT FINAL DU DÉPLOIEMENT AWS!")
    print("=" * 80)
    print("🌊 Deepseek Harmonique + LM Arena")
    print("📊 Analyse complète de l'infrastructure")
    print("🚀 Plan d'action pour le lancement")
    print("=" * 80)
    
    # Générer le rapport final
    analyzer = FinalDeploymentStatus()
    report = analyzer.generate_final_report()
    
    print("\n🌊 ANALYSE TERMINÉE!")
    print("📊 Rapport complet généré")
    print("🚀 Plan d'action défini")
    print("🎯 Prêt pour la prochaine étape!")

if __name__ == "__main__":
    main()
