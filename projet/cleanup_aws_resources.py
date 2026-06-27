#!/usr/bin/env python3
"""
Script de nettoyage AWS pour Harmonic AI
Conserve uniquement les ressources specifiees
"""

import subprocess
import json
import sys
import time
from datetime import datetime

class AWSCleanup:
    """Nettoyage AWS selectif"""
    
    def __init__(self):
        # Ressources a conserver
        self.resources_to_keep = {
            'ec2_instances': [
                'i-040cd889e745cbedd',  # connective-ai-deepseek-v4-final-port-8000 (arret)
                'i-0716d7805ca2c22e9'   # DeepSeek-Harmonic-V2 (running)
            ],
            's3_buckets': [
                'harmonic-ai-knowledge-base',  # Base de connaissances Harmonic AI
                'hcv-pro-frontend-326095712935',  # Frontend HCV-PROF
                'hcv-pro-deepseek-frontend-326095712935',  # Frontend DeepSeek HCV-PROF
                'hcv-pro-deepseek-test-326095712935',  # Test DeepSeek HCV-PROF
                'hcv-compression-engine-frontend-326095712935'  # Moteur compression HCV
            ]
        }
        
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'project': 'Harmonic AI - Nettoyage AWS',
            'resources_kept': self.resources_to_keep,
            'resources_removed': {
                'ec2_instances': [],
                's3_buckets': []
            },
            'errors': [],
            'status': 'IN_PROGRESS'
        }
    
    def run_command(self, command):
        """Executer une commande shell"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Timeout: La commande a pris trop de temps"
        except Exception as e:
            return False, "", f"Exception: {str(e)}"
    
    def list_all_ec2_instances(self, region='us-east-1'):
        """Lister toutes les instances EC2"""
        print(f"Liste des instances EC2 dans {region}...")
        
        command = f"aws ec2 describe-instances --region {region} --query 'Reservations[].Instances[].[InstanceId, State.Name, Tags[?Key==\"Name\"].Value|[0]]' --output text"
        success, output, error = self.run_command(command)
        
        instances = []
        if success and output:
            lines = output.strip().split('\n')
            for line in lines:
                parts = line.split('\t')
                if len(parts) >= 2:
                    instance_id = parts[0]
                    state = parts[1]
                    name = parts[2] if len(parts) > 2 else 'Sans nom'
                    instances.append({
                        'instance_id': instance_id,
                        'state': state,
                        'name': name,
                        'region': region
                    })
        
        return instances
    
    def list_all_s3_buckets(self):
        """Lister tous les buckets S3"""
        print("Liste des buckets S3...")
        
        command = "aws s3api list-buckets --output json"
        success, output, error = self.run_command(command)
        
        buckets = []
        if success and output:
            try:
                data = json.loads(output)
                buckets = [bucket['Name'] for bucket in data['Buckets']]
            except json.JSONDecodeError:
                print("  Erreur de parsing JSON")
        
        return buckets
    
    def terminate_ec2_instance(self, instance_id, region):
        """Terminer une instance EC2"""
        print(f"  Terminaison de l'instance {instance_id}...")
        
        command = f"aws ec2 terminate-instances --region {region} --instance-ids {instance_id}"
        success, output, error = self.run_command(command)
        
        if success:
            print(f"    Instance {instance_id} terminee avec succes")
            return True
        else:
            print(f"    Erreur lors de la terminaison: {error}")
            self.report['errors'].append(f"EC2 {instance_id}: {error}")
            return False
    
    def delete_s3_bucket(self, bucket_name):
        """Supprimer un bucket S3"""
        print(f"  Suppression du bucket S3 {bucket_name}...")
        
        # D'abord vider le bucket
        empty_command = f"aws s3 rm s3://{bucket_name} --recursive"
        success1, output1, error1 = self.run_command(empty_command)
        
        if not success1 and "NoSuchBucket" not in error1:
            print(f"    Erreur lors du vidage: {error1}")
            self.report['errors'].append(f"S3 {bucket_name} (vidage): {error1}")
            return False
        
        # Puis supprimer le bucket
        delete_command = f"aws s3api delete-bucket --bucket {bucket_name}"
        success2, output2, error2 = self.run_command(delete_command)
        
        if success2:
            print(f"    Bucket {bucket_name} supprime avec succes")
            return True
        else:
            print(f"    Erreur lors de la suppression: {error2}")
            self.report['errors'].append(f"S3 {bucket_name} (suppression): {error2}")
            return False
    
    def identify_resources_to_remove(self):
        """Identifier les ressources a supprimer"""
        print("Identification des ressources a supprimer...")
        
        resources_to_remove = {
            'ec2_instances': [],
            's3_buckets': []
        }
        
        # Identifier les instances EC2 a supprimer
        all_instances = self.list_all_ec2_instances('us-east-1')
        
        for instance in all_instances:
            if instance['instance_id'] not in self.resources_to_keep['ec2_instances']:
                resources_to_remove['ec2_instances'].append(instance)
                print(f"  Instance a supprimer: {instance['instance_id']} ({instance['name']}) - {instance['state']}")
        
        # Identifier les buckets S3 a supprimer
        all_buckets = self.list_all_s3_buckets()
        
        for bucket in all_buckets:
            if bucket not in self.resources_to_keep['s3_buckets']:
                resources_to_remove['s3_buckets'].append(bucket)
                print(f"  Bucket a supprimer: {bucket}")
        
        return resources_to_remove
    
    def display_summary(self, resources_to_remove):
        """Afficher un resume des operations"""
        print("\n" + "=" * 70)
        print("RESUME DU NETTOYAGE AWS")
        print("=" * 70)
        
        print("\nRESSOURCES A CONSERVER:")
        print(f"  Instances EC2 ({len(self.resources_to_keep['ec2_instances'])}):")
        for instance_id in self.resources_to_keep['ec2_instances']:
            print(f"    • {instance_id}")
        
        print(f"\n  Buckets S3 ({len(self.resources_to_keep['s3_buckets'])}):")
        for bucket in self.resources_to_keep['s3_buckets']:
            print(f"    • {bucket}")
        
        print("\nRESSOURCES A SUPPRIMER:")
        total_to_remove = len(resources_to_remove['ec2_instances']) + len(resources_to_remove['s3_buckets'])
        
        if total_to_remove == 0:
            print("  Aucune ressource a supprimer - environnement deja propre!")
            return False
        
        if resources_to_remove['ec2_instances']:
            print(f"  Instances EC2 ({len(resources_to_remove['ec2_instances'])}):")
            for instance in resources_to_remove['ec2_instances']:
                print(f"    • {instance['instance_id']} ({instance['name']}) - {instance['state']}")
        
        if resources_to_remove['s3_buckets']:
            print(f"  Buckets S3 ({len(resources_to_remove['s3_buckets'])}):")
            for bucket in resources_to_remove['s3_buckets']:
                print(f"    • {bucket}")
        
        print(f"\nTotal des ressources a supprimer: {total_to_remove}")
        
        return True
    
    def perform_cleanup(self, resources_to_remove):
        """Effectuer le nettoyage"""
        print("\n" + "=" * 70)
        print("EXECUTION DU NETTOYAGE")
        print("=" * 70)
        
        removed_resources = {
            'ec2_instances': [],
            's3_buckets': []
        }
        
        # Supprimer les instances EC2
        if resources_to_remove['ec2_instances']:
            print("\nSuppression des instances EC2...")
            
            for instance in resources_to_remove['ec2_instances']:
                if self.terminate_ec2_instance(instance['instance_id'], instance['region']):
                    removed_resources['ec2_instances'].append(instance)
        
        # Supprimer les buckets S3
        if resources_to_remove['s3_buckets']:
            print("\nSuppression des buckets S3...")
            
            for bucket in resources_to_remove['s3_buckets']:
                if self.delete_s3_bucket(bucket):
                    removed_resources['s3_buckets'].append(bucket)
        
        self.report['resources_removed'] = removed_resources
        
        return removed_resources
    
    def generate_final_report(self):
        """Generer le rapport final"""
        print("\n" + "=" * 70)
        print("RAPPORT FINAL")
        print("=" * 70)
        
        total_removed = (
            len(self.report['resources_removed']['ec2_instances']) +
            len(self.report['resources_removed']['s3_buckets'])
        )
        
        if total_removed > 0:
            self.report['status'] = 'CLEANUP_COMPLETED'
            print(f"Nettoyage termine avec succes!")
            print(f"Ressources supprimees: {total_removed}")
        else:
            self.report['status'] = 'NO_CLEANUP_NEEDED'
            print("Aucune ressource a supprimer - environnement deja propre")
        
        # Afficher le resume
        print("\nRESUME FINAL:")
        print(f"• Instances EC2 conservees: {len(self.resources_to_keep['ec2_instances'])}")
        print(f"• Buckets S3 conserves: {len(self.resources_to_keep['s3_buckets'])}")
        print(f"• Instances EC2 supprimees: {len(self.report['resources_removed']['ec2_instances'])}")
        print(f"• Buckets S3 supprimes: {len(self.report['resources_removed']['s3_buckets'])}")
        
        if self.report['errors']:
            print(f"\nErreurs rencontrees: {len(self.report['errors'])}")
            for error in self.report['errors']:
                print(f"  • {error}")
        
        # Sauvegarder le rapport
        report_file = 'aws_cleanup_final_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\nRapport sauvegarde dans: {report_file}")
        
        return self.report
    
    def run_cleanup(self):
        """Executer le nettoyage complet"""
        print("=" * 70)
        print("NETTOYAGE AWS SELECTIF - HARMONIC AI")
        print("=" * 70)
        print("Ce script va:")
        print("1. Conserver les 2 instances EC2 specifiees")
        print("2. Conserver les buckets S3 du projet HCV-PROF")
        print("3. Supprimer toutes les autres ressources AWS")
        print()
        
        # Identifier les ressources a supprimer
        resources_to_remove = self.identify_resources_to_remove()
        
        # Afficher le resume
        if not self.display_summary(resources_to_remove):
            self.report['status'] = 'NO_CLEANUP_NEEDED'
            return self.report
        
        # Demander confirmation
        print("\n" + "=" * 70)
        response = input("Confirmer la suppression? (oui/non): ").strip().lower()
        
        if response != 'oui':
            print("Nettoyage annule par l'utilisateur")
            self.report['status'] = 'CANCELLED_BY_USER'
            return self.report
        
        # Effectuer le nettoyage
        removed_resources = self.perform_cleanup(resources_to_remove)
        
        # Generer le rapport final
        final_report = self.generate_final_report()
        
        return final_report

def main():
    """Fonction principale"""
    cleanup = AWSCleanup()
    report = cleanup.run_cleanup()
    
    # Code de sortie
    if report['status'] in ['CLEANUP_COMPLETED', 'NO_CLEANUP_NEEDED']:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)