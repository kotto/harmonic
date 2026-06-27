#!/usr/bin/env python3
"""
Script final pour supprimer les buckets AWS inutilises
Conserve uniquement les ressources du projet Harmonic AI et HCV-PROF
"""

import subprocess
import json
import time
from datetime import datetime

def run_command(cmd):
    """Executer une commande shell"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout: La commande a pris trop de temps"
    except Exception as e:
        return False, "", f"Exception: {str(e)}"

def delete_s3_bucket(bucket_name):
    """Supprimer un bucket S3"""
    print(f"Suppression du bucket: {bucket_name}")
    
    # Etape 1: Vider le bucket
    print(f"  Etape 1: Vidage du bucket...")
    empty_cmd = f"aws s3 rm s3://{bucket_name} --recursive"
    success1, output1, error1 = run_command(empty_cmd)
    
    if not success1:
        if "NoSuchBucket" in error1:
            print(f"    Bucket {bucket_name} n'existe pas ou deja supprime")
            return True
        else:
            print(f"    Erreur lors du vidage: {error1}")
            return False
    
    # Etape 2: Supprimer le bucket
    print(f"  Etape 2: Suppression du bucket...")
    delete_cmd = f"aws s3api delete-bucket --bucket {bucket_name}"
    success2, output2, error2 = run_command(delete_cmd)
    
    if success2:
        print(f"    Bucket {bucket_name} supprime avec succes")
        return True
    else:
        print(f"    Erreur lors de la suppression: {error2}")
        return False

def main():
    """Fonction principale"""
    print("=" * 70)
    print("NETTOYAGE FINAL AWS - HARMONIC AI")
    print("=" * 70)
    print("Ce script va supprimer les buckets S3 inutilises")
    print()
    
    # Buckets a conserver (projet Harmonic AI et HCV-PROF)
    buckets_to_keep = [
        'harmonic-ai-knowledge-base',
        'hcv-pro-frontend-326095712935',
        'hcv-pro-deepseek-frontend-326095712935',
        'hcv-pro-deepseek-test-326095712935',
        'hcv-compression-engine-frontend-326095712935'
    ]
    
    # Buckets a supprimer
    buckets_to_delete = [
        'amazon-sagemaker-326095712935-us-east-1-3jkmqv6lj7x73b',
        'connective-ai-deployment',
        'deepseek-models-326095712935',
        'elasticbeanstalk-eu-west-3-326095712935'
    ]
    
    print("RESUME DES OPERATIONS:")
    print(f"• Buckets a conserver: {len(buckets_to_keep)}")
    for bucket in buckets_to_keep:
        print(f"  - {bucket}")
    
    print(f"\n• Buckets a supprimer: {len(buckets_to_delete)}")
    for bucket in buckets_to_delete:
        print(f"  - {bucket}")
    
    print("\n" + "=" * 70)
    print("DEBUT DU NETTOYAGE")
    print("=" * 70)
    
    # Supprimer chaque bucket
    results = []
    for bucket in buckets_to_delete:
        print(f"\nTraitement du bucket: {bucket}")
        success = delete_s3_bucket(bucket)
        results.append({
            'bucket': bucket,
            'success': success
        })
        
        # Petite pause entre les suppressions
        if bucket != buckets_to_delete[-1]:
            time.sleep(2)
    
    # Afficher le resume
    print("\n" + "=" * 70)
    print("RAPPORT FINAL")
    print("=" * 70)
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"Buckets traites: {len(results)}")
    print(f"Suppressions reussies: {successful}")
    print(f"Suppressions echouees: {failed}")
    
    if failed > 0:
        print("\nBuckets avec erreurs:")
        for r in results:
            if not r['success']:
                print(f"  • {r['bucket']}")
    
    # Sauvegarder le rapport
    report = {
        'timestamp': datetime.now().isoformat(),
        'operation': 'Nettoyage AWS Buckets S3',
        'buckets_kept': buckets_to_keep,
        'deletion_results': results,
        'summary': {
            'total_processed': len(results),
            'successful': successful,
            'failed': failed
        }
    }
    
    report_file = 'aws_buckets_cleanup_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nRapport sauvegarde dans: {report_file}")
    
    if failed == 0:
        print("\nNETTOYAGE TERMINE AVEC SUCCES!")
        return 0
    else:
        print(f"\nNETTOYAGE TERMINE AVEC {failed} ERREUR(S)")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)