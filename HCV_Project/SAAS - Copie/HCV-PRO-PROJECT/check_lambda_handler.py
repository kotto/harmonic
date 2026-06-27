#!/usr/bin/env python3
"""
VÉRIFICATION DU CONTENU DE LA FONCTION LAMBDA
============================================

Script pour vérifier ce qui est actuellement déployé dans la fonction Lambda.
"""

import boto3
import json
from datetime import datetime

def check_lambda_handler():
    """Vérifier le contenu actuel de la fonction Lambda"""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-3')
    function_name = 'hcv-pro-deepseek-handler'
    
    print("🔍 VÉRIFICATION DU CONTENU LAMBDA")
    print("=" * 50)
    
    try:
        # Obtenir la configuration de la fonction
        response = lambda_client.get_function(FunctionName=function_name)
        
        print(f"📦 Fonction: {function_name}")
        print(f"📊 Runtime: {response['Configuration']['Runtime']}")
        print(f"📊 Handler: {response['Configuration']['Handler']}")
        print(f"📊 Memory: {response['Configuration']['MemorySize']}MB")
        print(f"📊 Timeout: {response['Configuration']['Timeout']}s")
        print(f"📊 State: {response['Configuration']['State']}")
        print(f"📊 Last Modified: {response['Configuration']['LastModified']}")
        
        # Obtenir le code source
        try:
            code_response = lambda_client.get_function_code(FunctionName=function_name)
            code_bytes = code_response['Code']['ZipFile']
            
            print(f"📊 Taille du code: {len(code_bytes)} bytes")
            
            # Extraire et lister les fichiers
            import zipfile
            import io
            
            with zipfile.ZipFile(io.BytesIO(code_bytes), 'r') as zip_file:
                file_list = zip_file.namelist()
                print(f"📦 Fichiers dans le package:")
                for file_name in file_list:
                    print(f"   📄 {file_name}")
        
        except Exception as e:
            print(f"❌ Erreur lecture code: {e}")
        
        # Tester l'invocation pour voir l'erreur exacte
        print("\n🧪 Test d'invocation pour voir l'erreur...")
        
        test_event = {
            "httpMethod": "GET",
            "path": "/api/health"
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        payload_bytes = response['Payload'].read()
        decoded_payload = payload_bytes.decode('utf-8')
        parsed_payload = json.loads(decoded_payload)
        
        print(f"📊 StatusCode: {parsed_payload.get('statusCode')}")
        print(f"📊 Error: {parsed_payload.get('errorMessage', 'None')}")
        print(f"📊 Error Type: {parsed_payload.get('errorType', 'None')}")
        
        if parsed_payload.get('stackTrace'):
            print("📊 Stack Trace:")
            for line in parsed_payload.get('stackTrace', []):
                print(f"   {line}")
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")

if __name__ == "__main__":
    check_lambda_handler()
