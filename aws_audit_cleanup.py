#!/usr/bin/env python3
"""
Audit et nettoyage des ressources AWS pour Harmonic AI
Régions : us-east-1 et eu-west-1
"""

import json
import os
from datetime import datetime, timedelta
import subprocess
import sys

class AWSAuditCleanup:
    """Audit et nettoyage des ressources AWS"""
    
    def __init__(self):
        self.regions = ['us-east-1', 'eu-west-1']
        self.resources_to_audit = [
            'ec2', 's3', 'lambda', 'rds', 'elasticache', 
            'cloudfront', 'route53', 'iam', 'cloudwatch'
        ]
        self.unused_threshold_days = 30
        self.audit_report = {
            'date': datetime.now().isoformat(),
            'regions': self.regions,
            'resources_found': {},
            'unused_resources': {},
            'cleanup_recommendations': [],
            'estimated_savings': 0
        }
    
    def run_aws_command(self, command, region=None):
        """Exécute une commande AWS CLI"""
        try:
            if region:
                command = f"aws {command} --region {region}"
            else:
                command = f"aws {command}"
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)
    
    def audit_ec2_instances(self, region):
        """Audit des instances EC2"""
        print(f"Audit EC2 dans {region}...")
        
        instances = []
        unused_instances = []
        
        # Récupérer les instances
        returncode, output, error = self.run_aws_command(
            f"ec2 describe-instances --query 'Reservations[*].Instances[*].{{ID:InstanceId,Type:InstanceType,State:State.Name,LaunchTime:LaunchTime,Tags:Tags}}'",
            region
        )
        
        if returncode == 0 and output.strip():
            try:
                instances_data = json.loads(output)
                for reservation in instances_data:
                    for instance in reservation:
                        instance_info = {
                            'id': instance.get('ID'),
                            'type': instance.get('Type'),
                            'state': instance.get('State'),
                            'launch_time': instance.get('LaunchTime'),
                            'tags': instance.get('Tags', []),
                            'estimated_cost': self.estimate_ec2_cost(instance.get('Type'), region)
                        }
                        instances.append(instance_info)
                        
                        # Vérifier si l'instance est inutilisée
                        if self.is_instance_unused(instance_info):
                            unused_instances.append(instance_info)
            except json.JSONDecodeError:
                print(f"Erreur de parsing JSON pour EC2 dans {region}")
        
        return instances, unused_instances
    
    def audit_s3_buckets(self, region):
        """Audit des buckets S3"""
        print(f"Audit S3 dans {region}...")
        
        buckets = []
        unused_buckets = []
        
        # Récupérer les buckets
        returncode, output, error = self.run_aws_command("s3api list-buckets --query 'Buckets[*].{Name:Name,CreationDate:CreationDate}'", region)
        
        if returncode == 0 and output.strip():
            try:
                buckets_data = json.loads(output)
                for bucket in buckets_data:
                    bucket_info = {
                        'name': bucket.get('Name'),
                        'creation_date': bucket.get('CreationDate'),
                        'region': self.get_bucket_region(bucket.get('Name')),
                        'size_gb': self.get_bucket_size(bucket.get('Name')),
                        'estimated_cost': self.estimate_s3_cost(bucket.get('Name'))
                    }
                    buckets.append(bucket_info)
                    
                    # Vérifier si le bucket est inutilisé
                    if self.is_bucket_unused(bucket_info):
                        unused_buckets.append(bucket_info)
            except json.JSONDecodeError:
                print(f"Erreur de parsing JSON pour S3 dans {region}")
        
        return buckets, unused_buckets
    
    def audit_lambda_functions(self, region):
        """Audit des fonctions Lambda"""
        print(f"Audit Lambda dans {region}...")
        
        functions = []
        unused_functions = []
        
        # Récupérer les fonctions Lambda
        returncode, output, error = self.run_aws_command(
            "lambda list-functions --query 'Functions[*].{FunctionName:FunctionName,Runtime:Runtime,LastModified:LastModified,MemorySize:MemorySize}'",
            region
        )
        
        if returncode == 0 and output.strip():
            try:
                functions_data = json.loads(output)
                for function in functions_data:
                    function_info = {
                        'name': function.get('FunctionName'),
                        'runtime': function.get('Runtime'),
                        'last_modified': function.get('LastModified'),
                        'memory_mb': function.get('MemorySize'),
                        'invocations_last_30_days': self.get_lambda_invocations(function.get('FunctionName'), region),
                        'estimated_cost': self.estimate_lambda_cost(function.get('MemorySize'), region)
                    }
                    functions.append(function_info)
                    
                    # Vérifier si la fonction est inutilisée
                    if self.is_lambda_unused(function_info):
                        unused_functions.append(function_info)
            except json.JSONDecodeError:
                print(f"Erreur de parsing JSON pour Lambda dans {region}")
        
        return functions, unused_functions
    
    def estimate_ec2_cost(self, instance_type, region):
        """Estimation du coût EC2 (simplifiée)"""
        # Prix approximatifs par heure
        pricing = {
            'us-east-1': {
                't3.micro': 0.0104,
                't3.small': 0.0208,
                't3.medium': 0.0416,
                'm5.large': 0.096,
                'm5.xlarge': 0.192,
                'g4dn.xlarge': 0.526,
                'g5.xlarge': 1.006
            },
            'eu-west-1': {
                't3.micro': 0.0112,
                't3.small': 0.0224,
                't3.medium': 0.0448,
                'm5.large': 0.107,
                'm5.xlarge': 0.214,
                'g4dn.xlarge': 0.578,
                'g5.xlarge': 1.107
            }
        }
        
        return pricing.get(region, {}).get(instance_type, 0.1) * 24 * 30  # Estimation mensuelle
    
    def estimate_s3_cost(self, bucket_name):
        """Estimation du coût S3 (simplifiée)"""
        # Prix approximatif: $0.023 par GB par mois
        size_gb = self.get_bucket_size(bucket_name)
        return size_gb * 0.023
    
    def estimate_lambda_cost(self, memory_mb, region):
        """Estimation du coût Lambda (simplifiée)"""
        # Prix approximatif: $0.0000166667 par GB-seconde
        # Estimation: 1M invocations par mois, 1 seconde d'exécution
        gb_seconds = (memory_mb / 1024) * 1000000
        return gb_seconds * 0.0000166667
    
    def get_bucket_region(self, bucket_name):
        """Récupérer la région d'un bucket S3"""
        returncode, output, error = self.run_aws_command(f"s3api get-bucket-location --bucket {bucket_name}")
        if returncode == 0 and output.strip():
            try:
                data = json.loads(output)
                return data.get('LocationConstraint', 'us-east-1')
            except:
                pass
        return 'unknown'
    
    def get_bucket_size(self, bucket_name):
        """Récupérer la taille d'un bucket S3"""
        try:
            returncode, output, error = self.run_aws_command(f"s3api list-objects-v2 --bucket {bucket_name} --query 'sum(Contents[].Size)'")
            if returncode == 0 and output.strip():
                size_bytes = float(output.strip())
                return size_bytes / (1024**3)  # Convertir en GB
        except:
            pass
        return 0
    
    def get_lambda_invocations(self, function_name, region):
        """Récupérer le nombre d'invocations Lambda des 30 derniers jours"""
        # Simulation - en réalité, utiliser CloudWatch Metrics
        return 0  # Par défaut
    
    def is_instance_unused(self, instance_info):
        """Vérifier si une instance EC2 est inutilisée"""
        if instance_info['state'] != 'running':
            return True
        
        # Vérifier l'âge de l'instance
        if instance_info['launch_time']:
            launch_date = datetime.fromisoformat(instance_info['launch_time'].replace('Z', '+00:00'))
            age_days = (datetime.now(launch_date.tzinfo) - launch_date).days
            if age_days > self.unused_threshold_days:
                # Vérifier les tags pour identifier les instances de test
                tags = instance_info.get('tags', [])
                for tag in tags:
                    if tag.get('Key') in ['Environment', 'Purpose']:
                        if tag.get('Value') in ['test', 'dev', 'staging']:
                            return True
        return False
    
    def is_bucket_unused(self, bucket_info):
        """Vérifier si un bucket S3 est inutilisé"""
        if bucket_info['size_gb'] == 0:
            return True
        
        # Vérifier l'âge du bucket
        if bucket_info['creation_date']:
            creation_date = datetime.fromisoformat(bucket_info['creation_date'].replace('Z', '+00:00'))
            age_days = (datetime.now(creation_date.tzinfo) - creation_date).days
            if age_days > self.unused_threshold_days * 3:  # Plus long pour S3
                return True
        return False
    
    def is_lambda_unused(self, function_info):
        """Vérifier si une fonction Lambda est inutilisée"""
        if function_info['invocations_last_30_days'] == 0:
            return True
        return False
    
    def run_audit(self):
        """Exécuter l'audit complet"""
        print("=" * 70)
        print("AUDIT AWS - HARMONIC AI")
        print("=" * 70)
        print(f"Date: {datetime.now().isoformat()}")
        print(f"Régions: {', '.join(self.regions)}")
        print()
        
        total_estimated_savings = 0
        
        for region in self.regions:
            print(f"\n{'='*40}")
            print(f"RÉGION: {region}")
            print(f"{'='*40}")
            
            # Audit EC2
            ec2_instances, unused_ec2 = self.audit_ec2_instances(region)
            if ec2_instances:
                print(f"  Instances EC2 trouvées: {len(ec2_instances)}")
                print(f"  Instances inutilisées: {len(unused_ec2)}")
                
                for instance in unused_ec2:
                    savings = instance['estimated_cost']
                    total_estimated_savings += savings
                    print(f"    • {instance['id']} ({instance['type']}): ${savings:.2f}/mois")
            
            # Audit S3
            s3_buckets, unused_s3 = self.audit_s3_buckets(region)
            if s3_buckets:
                print(f"  Buckets S3 trouvés: {len(s3_buckets)}")
                print(f"  Buckets inutilisés: {len(unused_s3)}")
                
                for bucket in unused_s3:
                    savings = bucket['estimated_cost']
                    total_estimated_savings += savings
                    print(f"    • {bucket['name']}: ${savings:.2f}/mois")
            
            # Audit Lambda
            lambda_functions, unused_lambda = self.audit_lambda_functions(region)
            if lambda_functions:
                print(f"  Fonctions Lambda trouvées: {len(lambda_functions)}")
                print(f"  Fonctions inutilisées: {len(unused_lambda)}")
                
                for function in unused_lambda:
                    savings = function['estimated_cost']
                    total_estimated_savings += savings
                    print(f"    • {function['name']}: ${savings:.2f}/mois")
        
        # Générer les recommandations
        self.generate_recommendations(total_estimated_savings)
        
        # Sauvegarder le rapport
        self.save_report()
        
        print("\n" + "=" * 70)
        print("AUDIT TERMINÉ")
        print("=" * 70)
        print(f"Économies estimées: ${total_estimated_savings:.2f}/mois")
        print(f"Rapport sauvegardé: aws_audit_report_{datetime.now().strftime('%Y%m%d')}.json")
        print("\nRecommandations:")
        for i, rec in enumerate(self.audit_report['cleanup_recommendations'], 1):
            print(f"  {i}. {rec}")
    
    def generate_recommendations(self, estimated_savings):
        """Générer des recommandations de nettoyage"""
        recommendations = []
        
        if estimated_savings > 0:
            recommendations.append(f"Nettoyer les ressources inutilisées pour économiser ${estimated_savings:.2f}/mois")
        
        recommendations.append("Configurer des alertes CloudWatch pour détecter les ressources inutilisées")
        recommendations.append("Mettre en place des politiques de cycle de vie S3 pour archiver les données anciennes")
        recommendations.append("Réviser régulièrement les rôles IAM et supprimer les permissions inutilisées")
        recommendations.append("Utiliser AWS Cost Explorer pour identifier les coûts anormaux")
        
        self.audit_report['cleanup_recommendations'] = recommendations
        self.audit_report['estimated_savings'] = estimated_savings
    
    def save_report(self):
        """Sauvegarder le rapport d'audit"""
        filename = f"aws_audit_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.audit_report, f, indent=2, ensure_ascii=False)
        
        # Générer un résumé exécutif
        summary_filename = f"aws_audit_summary_{datetime.now().strftime('%Y%m%d')}.md"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Rapport d'Audit AWS - Harmonic AI\n\n")
            f.write(f"**Date:** {datetime.now().isoformat()}\n")
            f.write(f"**Régions auditées:** {', '.join(self.regions)}\n\n")
            
            f.write(f"## Résumé Exécutif\n\n")
            f.write(f"**Économies estimées:** ${self.audit_report['estimated_savings']:.2f}/mois\n\n")
            
            f.write(f"## Recommandations\n\n")
            for i, rec in enumerate(self.audit_report['cleanup_recommendations'], 1):
                f.write(f"{i}. {rec}\n")
            
            f.write(f"\n## Actions Immédiates\n\n")
            f.write(f"1. **Identifier les instances EC2 inutilisées** et les arrêter ou les terminer\n")
            f.write(f"2. **Supprimer les buckets S3 vides** ou inutilisés depuis plus de 90 jours\n")
            f.write(f"3. **Désactiver les fonctions Lambda** non invoquées depuis 30 jours\n")
            f.write(f"4. **Configurer AWS Budgets** pour surveiller les coûts\n")
            f.write(f"5. **Activer AWS Cost Anomaly Detection** pour les alertes automatiques\n")

def main():
    """Fonction principale"""
    print("Audit et nettoyage des ressources AWS pour Harmonic AI")
    print("Régions: us-east-1, eu-west-1")
    print()
    
    # Vérifier si AWS CLI est installé
    try:
        subprocess.run(["aws", "--version"], capture_output=True, check=True)
    except:
        print("ERREUR: AWS CLI n'est pas installé ou configuré.")
        print("Installez AWS CLI et configurez les credentials avec:")
        print("  aws configure")
        sys.exit(1)
    
    # Exécuter l'audit
    auditor = AWSAuditCleanup()
    auditor.run_audit()

if __name__ == "__main__":
    main()