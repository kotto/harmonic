#!/usr/bin/env python3
"""
Audit simplifié des ressources AWS pour Harmonic AI
Version robuste avec gestion d'erreurs
"""

import json
import os
from datetime import datetime
import subprocess
import sys

class SimpleAWSAudit:
    """Audit AWS simplifié et robuste"""
    
    def __init__(self):
        self.regions = ['us-east-1', 'eu-west-1']
        self.report = {
            'date': datetime.now().isoformat(),
            'regions': self.regions,
            'findings': [],
            'recommendations': [],
            'status': 'completed'
        }
    
    def run_safe_command(self, command, region=None):
        """Exécuter une commande AWS CLI avec gestion d'erreurs"""
        try:
            if region:
                full_command = f"aws {command} --region {region}"
            else:
                full_command = f"aws {command}"
            
            result = subprocess.run(
                full_command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, f"Erreur: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout: La commande a pris trop de temps"
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def check_ec2_instances(self, region):
        """Vérifier les instances EC2"""
        print(f"  Vérification EC2 dans {region}...")
        
        success, output = self.run_safe_command(
            "ec2 describe-instances --query 'Reservations[*].Instances[*].{ID:InstanceId,Type:InstanceType,State:State.Name}'",
            region
        )
        
        if success and output:
            try:
                data = json.loads(output)
                instance_count = 0
                for reservation in data:
                    if isinstance(reservation, list):
                        instance_count += len(reservation)
                    else:
                        instance_count += 1
                
                if instance_count > 0:
                    self.report['findings'].append({
                        'type': 'ec2',
                        'region': region,
                        'count': instance_count,
                        'message': f"{instance_count} instance(s) EC2 trouvée(s)"
                    })
                    return instance_count
            except json.JSONDecodeError:
                self.report['findings'].append({
                    'type': 'error',
                    'region': region,
                    'message': "Erreur de parsing JSON pour EC2"
                })
        elif not success:
            self.report['findings'].append({
                'type': 'error',
                'region': region,
                'message': output
            })
        
        return 0
    
    def check_s3_buckets(self, region):
        """Vérifier les buckets S3"""
        print(f"  Vérification S3 dans {region}...")
        
        success, output = self.run_safe_command(
            "s3api list-buckets --query 'Buckets[*].Name'",
            region
        )
        
        if success and output:
            try:
                # Essayer de parser comme JSON
                if output.startswith('['):
                    buckets = json.loads(output)
                    bucket_count = len(buckets)
                else:
                    # Compter les lignes
                    bucket_count = len([line for line in output.split('\n') if line.strip()])
                
                if bucket_count > 0:
                    self.report['findings'].append({
                        'type': 's3',
                        'region': region,
                        'count': bucket_count,
                        'message': f"{bucket_count} bucket(s) S3 trouvé(s)"
                    })
                    return bucket_count
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON valide, compter les lignes
                lines = [line.strip() for line in output.split('\n') if line.strip()]
                bucket_count = len(lines)
                
                if bucket_count > 0:
                    self.report['findings'].append({
                        'type': 's3',
                        'region': region,
                        'count': bucket_count,
                        'message': f"{bucket_count} bucket(s) S3 trouvé(s) (format brut)"
                    })
                    return bucket_count
        elif not success:
            self.report['findings'].append({
                'type': 'error',
                'region': region,
                'message': f"Erreur S3: {output}"
            })
        
        return 0
    
    def check_lambda_functions(self, region):
        """Vérifier les fonctions Lambda"""
        print(f"  Vérification Lambda dans {region}...")
        
        success, output = self.run_safe_command(
            "lambda list-functions --query 'Functions[*].FunctionName'",
            region
        )
        
        if success and output:
            try:
                if output.startswith('['):
                    functions = json.loads(output)
                    function_count = len(functions)
                else:
                    function_count = len([line for line in output.split('\n') if line.strip()])
                
                if function_count > 0:
                    self.report['findings'].append({
                        'type': 'lambda',
                        'region': region,
                        'count': function_count,
                        'message': f"{function_count} fonction(s) Lambda trouvée(s)"
                    })
                    return function_count
            except json.JSONDecodeError:
                lines = [line.strip() for line in output.split('\n') if line.strip()]
                function_count = len(lines)
                
                if function_count > 0:
                    self.report['findings'].append({
                        'type': 'lambda',
                        'region': region,
                        'count': function_count,
                        'message': f"{function_count} fonction(s) Lambda trouvée(s) (format brut)"
                    })
                    return function_count
        elif not success:
            self.report['findings'].append({
                'type': 'error',
                'region': region,
                'message': f"Erreur Lambda: {output}"
            })
        
        return 0
    
    def check_iam_roles(self):
        """Vérifier les rôles IAM"""
        print("  Vérification IAM...")
        
        success, output = self.run_safe_command(
            "iam list-roles --query 'Roles[*].RoleName'"
        )
        
        if success and output:
            try:
                if output.startswith('['):
                    roles = json.loads(output)
                    role_count = len(roles)
                else:
                    role_count = len([line for line in output.split('\n') if line.strip()])
                
                if role_count > 0:
                    self.report['findings'].append({
                        'type': 'iam',
                        'region': 'global',
                        'count': role_count,
                        'message': f"{role_count} rôle(s) IAM trouvé(s)"
                    })
                    return role_count
            except json.JSONDecodeError:
                lines = [line.strip() for line in output.split('\n') if line.strip()]
                role_count = len(lines)
                
                if role_count > 0:
                    self.report['findings'].append({
                        'type': 'iam',
                        'region': 'global',
                        'count': role_count,
                        'message': f"{role_count} rôle(s) IAM trouvé(s) (format brut)"
                    })
                    return role_count
        elif not success:
            self.report['findings'].append({
                'type': 'error',
                'region': 'global',
                'message': f"Erreur IAM: {output}"
            })
        
        return 0
    
    def generate_recommendations(self):
        """Générer des recommandations basées sur les findings"""
        recommendations = []
        
        # Recommandations générales
        recommendations.append("Réviser régulièrement les instances EC2 et arrêter celles inutilisées")
        recommendations.append("Nettoyer les buckets S3 vides ou obsolètes")
        recommendations.append("Désactiver les fonctions Lambda non utilisées")
        recommendations.append("Auditer les rôles IAM et supprimer les permissions inutiles")
        recommendations.append("Configurer AWS Budgets pour surveiller les coûts")
        
        # Ajouter des recommandations spécifiques basées sur les findings
        ec2_count = sum(f['count'] for f in self.report['findings'] if f['type'] == 'ec2')
        if ec2_count > 5:
            recommendations.append(f"Considérer la consolidation des {ec2_count} instances EC2")
        
        s3_count = sum(f['count'] for f in self.report['findings'] if f['type'] == 's3')
        if s3_count > 10:
            recommendations.append(f"Auditer les {s3_count} buckets S3 pour suppression des doublons")
        
        self.report['recommendations'] = recommendations
    
    def run_audit(self):
        """Exécuter l'audit complet"""
        print("=" * 70)
        print("AUDIT AWS SIMPLIFIÉ - HARMONIC AI")
        print("=" * 70)
        print(f"Date: {datetime.now().isoformat()}")
        print(f"Régions: {', '.join(self.regions)}")
        print()
        
        total_resources = 0
        
        for region in self.regions:
            print(f"{'='*40}")
            print(f"RÉGION: {region}")
            print(f"{'='*40}")
            
            # Vérifier les ressources
            ec2_count = self.check_ec2_instances(region)
            s3_count = self.check_s3_buckets(region)
            lambda_count = self.check_lambda_functions(region)
            
            region_total = ec2_count + s3_count + lambda_count
            total_resources += region_total
            
            print(f"  Total ressources dans {region}: {region_total}")
            print(f"    • EC2: {ec2_count}")
            print(f"    • S3: {s3_count}")
            print(f"    • Lambda: {lambda_count}")
            print()
        
        # Vérifier IAM (global)
        print(f"{'='*40}")
        print("IAM (GLOBAL)")
        print(f"{'='*40}")
        iam_count = self.check_iam_roles()
        total_resources += iam_count
        print(f"  Rôles IAM: {iam_count}")
        
        # Générer les recommandations
        self.generate_recommendations()
        
        # Sauvegarder le rapport
        self.save_report()
        
        print("\n" + "=" * 70)
        print("AUDIT TERMINÉ")
        print("=" * 70)
        print(f"Total ressources trouvées: {total_resources}")
        print(f"Rapport sauvegardé: aws_simple_audit_{datetime.now().strftime('%Y%m%d')}.json")
        
        print("\nRecommandations principales:")
        for i, rec in enumerate(self.report['recommendations'][:5], 1):
            print(f"  {i}. {rec}")
        
        print("\nActions recommandées:")
        print("  1. Identifier les ressources inutilisées")
        print("  2. Configurer des alertes de coût")
        print("  3. Mettre en place des politiques de cycle de vie")
        print("  4. Réviser régulièrement les accès IAM")
        print("  5. Surveiller les coûts avec AWS Cost Explorer")
    
    def save_report(self):
        """Sauvegarder le rapport d'audit"""
        filename = f"aws_simple_audit_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        # Générer un résumé exécutif en Markdown
        summary_filename = f"aws_audit_summary_{datetime.now().strftime('%Y%m%d')}.md"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write("# Rapport d'Audit AWS Simplifié - Harmonic AI\n\n")
            f.write(f"**Date:** {self.report['date']}\n")
            f.write(f"**Statut:** {self.report['status']}\n")
            f.write(f"**Régions auditées:** {', '.join(self.report['regions'])}\n\n")
            
            f.write("## Résumé des Findings\n\n")
            for finding in self.report['findings']:
                if finding['type'] != 'error':
                    f.write(f"- **{finding['type'].upper()}** ({finding['region']}): {finding['message']}\n")
            
            f.write("\n## Recommandations\n\n")
            for i, rec in enumerate(self.report['recommendations'], 1):
                f.write(f"{i}. {rec}\n")
            
            f.write("\n## Plan d'Action\n\n")
            f.write("1. **Identifier et documenter** toutes les ressources AWS\n")
            f.write("2. **Étiqueter correctement** les ressources (Environment, Owner, Project)\n")
            f.write("3. **Configurer AWS Budgets** avec alertes à 80% et 100% du budget\n")
            f.write("4. **Activer AWS Cost Anomaly Detection** pour surveillance automatique\n")
            f.write("5. **Mettre en place des politiques de cycle de vie** S3 et EC2\n")
            f.write("6. **Auditer régulièrement les accès IAM** (tous les 30 jours)\n")
            f.write("7. **Documenter l'architecture** et les dépendances entre ressources\n")

def main():
    """Fonction principale"""
    print("Audit AWS simplifié pour Harmonic AI")
    print("Version robuste avec gestion d'erreurs")
    print()
    
    # Vérifier si AWS CLI est installé
    try:
        subprocess.run(["aws", "--version"], capture_output=True, check=True)
        print("AWS CLI détecté ✓")
    except:
        print("AVERTISSEMENT: AWS CLI n'est pas installé ou configuré.")
        print("L'audit continuera mais certaines vérifications échoueront.")
        print("Pour une audit complet, installez AWS CLI et configurez les credentials.")
        print("  aws configure")
        print()
    
    # Exécuter l'audit
    auditor = SimpleAWSAudit()
    auditor.run_audit()

if __name__ == "__main__":
    main()