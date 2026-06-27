#!/usr/bin/env python3
"""
Script de vérification des permissions Qwen3.5 Enhanced Harmonic AI
"""

import boto3
import json
from datetime import datetime

def verify_permissions():
    """Vérifie toutes les permissions requises pour Qwen3.5 Enhanced"""
    print("🔍 VÉRIFICATION DES PERMISSIONS QWEN3.5 ENHANCED HARMONIC AI")
    print("=" * 70)
    print(f"📅 Date: {datetime.utcnow().isoformat()}")
    print(f"👤 User: harmonic-ai-user")
    print(f"🏢 Account: 326095712935")
    print(f"🌍 Region: us-east-1")
    print("=" * 70)
    
    # Clients AWS
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        iam_client = boto3.client('iam', region_name='us-east-1')
        s3_client = boto3.client('s3', region_name='us-east-1')
        ecr_client = boto3.client('ecr', region_name='us-east-1')
        apigateway_client = boto3.client('apigateway', region_name='us-east-1')
        
        results = {}
        
        # Test Lambda permissions
        print("\n🔧 TEST LAMBDA PERMISSIONS")
        print("-" * 40)
        
        try:
            response = lambda_client.get_function(FunctionName='qwen35-simple')
            results['lambda_get_function'] = '✅ OK'
            print("✅ lambda:GetFunction - OK")
        except Exception as e:
            results['lambda_get_function'] = f'❌ {str(e)}'
            print(f"❌ lambda:GetFunction - {str(e)}")
        
        try:
            lambda_client.update_function_configuration(
                FunctionName='qwen35-simple',
                Timeout=300
            )
            results['lambda_update_config'] = '✅ OK'
            print("✅ lambda:UpdateFunctionConfiguration - OK")
        except Exception as e:
            results['lambda_update_config'] = f'❌ {str(e)}'
            print(f"❌ lambda:UpdateFunctionConfiguration - {str(e)}")
        
        # Test IAM permissions
        print("\n🔐 TEST IAM PERMISSIONS")
        print("-" * 40)
        
        try:
            response = iam_client.list_attached_user_policies(UserName='harmonic-ai-user')
            results['iam_list_policies'] = '✅ OK'
            print("✅ iam:ListAttachedUserPolicies - OK")
        except Exception as e:
            results['iam_list_policies'] = f'❌ {str(e)}'
            print(f"❌ iam:ListAttachedUserPolicies - {str(e)}")
        
        try:
            iam_client.get_role(RoleName='AmazonSageMaker-ExecutionRole-20250511T181292')
            results['iam_get_role'] = '✅ OK'
            print("✅ iam:GetRole - OK")
        except Exception as e:
            results['iam_get_role'] = f'❌ {str(e)}'
            print(f"❌ iam:GetRole - {str(e)}")
        
        # Test S3 permissions
        print("\n📦 TEST S3 PERMISSIONS")
        print("-" * 40)
        
        try:
            s3_client.head_bucket(Bucket='harmonic-ai-qwen-models')
            results['s3_head_bucket'] = '✅ OK'
            print("✅ s3:HeadBucket (harmonic-ai-qwen-models) - OK")
        except Exception as e:
            results['s3_head_bucket'] = f'❌ {str(e)}'
            print(f"❌ s3:HeadBucket - {str(e)}")
        
        try:
            s3_client.list_buckets()
            results['s3_list_buckets'] = '✅ OK'
            print("✅ s3:ListBuckets - OK")
        except Exception as e:
            results['s3_list_buckets'] = f'❌ {str(e)}'
            print(f"❌ s3:ListBuckets - {str(e)}")
        
        # Test ECR permissions
        print("\n📦 TEST ECR PERMISSIONS")
        print("-" * 40)
        
        try:
            ecr_client.describe_repositories()
            results['ecr_describe_repositories'] = '✅ OK'
            print("✅ ecr:DescribeRepositories - OK")
        except Exception as e:
            results['ecr_describe_repositories'] = f'❌ {str(e)}'
            print(f"❌ ecr:DescribeRepositories - {str(e)}")
        
        # Test API Gateway permissions
        print("\n🌐 TEST API GATEWAY PERMISSIONS")
        print("-" * 40)
        
        try:
            apigateway_client.get_rest_apis()
            results['apigateway_get_apis'] = '✅ OK'
            print("✅ apigateway:GetRestApis - OK")
        except Exception as e:
            results['apigateway_get_apis'] = f'❌ {str(e)}'
            print(f"❌ apigateway:GetRestApis - {str(e)}")
        
        # Résumé
        print("\n📊 RÉSUMÉ DES PERMISSIONS")
        print("=" * 70)
        
        total_tests = len(results)
        passed_tests = sum(1 for v in results.values() if '✅' in v)
        
        print(f"📈 Tests réussis: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        for test_name, result in results.items():
            status_icon = "✅" if "✅" in result else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        # Recommandations
        print("\n💡 RECOMMANDATIONS")
        print("-" * 40)
        
        if passed_tests == total_tests:
            print("🎉 TOUTES LES PERMISSIONS SONT OK!")
            print("✅ Vous pouvez maintenant lancer:")
            print("   python qwen35_harmonic_simple.py")
        else:
            print("⚠️ PERMISSIONS MANQUANTES - Contactez l'admin AWS")
            print("📋 Utilisez la procédure dans AWS_ADMIN_REQUEST_PROCEDURE.md")
        
        return results
        
    except Exception as e:
        print(f"❌ Erreur critique: {str(e)}")
        return None

def main():
    """Point d'entrée principal"""
    results = verify_permissions()
    
    if results:
        # Sauvegarder les résultats
        with open('permissions_verification_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'user': 'harmonic-ai-user',
                'account': '326095712935',
                'region': 'us-east-1',
                'results': results
            }, f, indent=2)
        
        print(f"\n💾 Résultats sauvegardés dans: permissions_verification_results.json")

if __name__ == "__main__":
    main()
