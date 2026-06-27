#!/usr/bin/env python3
"""
DIAGNOSTIC DE LA RÉPONSE LAMBDA
=================================

Script pour diagnostiquer ce qui se passe dans la fonction Lambda
et comprendre pourquoi les endpoints retournent None.
"""

import boto3
import json
from datetime import datetime

def debug_lambda_response():
    """Diagnostiquer la réponse Lambda"""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-3')
    function_name = 'hcv-pro-deepseek-handler'
    
    print("🔍 DIAGNOSTIC DE LA RÉPONSE LAMBDA")
    print("=" * 50)
    
    try:
        # Test 1: Invocation simple
        print("📦 Test 1: Invocation simple")
        
        test_event = {
            "httpMethod": "GET",
            "path": "/api/health"
        }
        
        print(f"   📦 Event: {json.dumps(test_event, indent=2)}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        print(f"   📊 StatusCode: {response.get('StatusCode', 'N/A')}")
        print(f"   📊 ExecutedVersion: {response.get('ExecutedVersion', 'N/A')}")
        print(f"   📊 LogResult: {response.get('LogResult', 'N/A')}")
        
        # Analyser le payload
        payload = response.get('Payload')
        print(f"   📊 Payload type: {type(payload)}")
        
        if hasattr(payload, 'read'):
            print("   📦 Payload est un StreamingBody, lecture...")
            payload_bytes = payload.read()
            print(f"   � Payload bytes length: {len(payload_bytes)}")
            
            try:
                decoded_payload = payload_bytes.decode('utf-8')
                print(f"   📊 Payload décodé: {decoded_payload}")
                
                parsed_payload = json.loads(decoded_payload)
                print(f"   📊 Payload parsé: {parsed_payload}")
                
                print(f"   📊 StatusCode (parsed): {parsed_payload.get('statusCode', 'N/A')}")
                print(f"   📊 Body (parsed): {parsed_payload.get('body', 'N/A')}")
                
                if parsed_payload.get('statusCode') == 200:
                    body = json.loads(parsed_payload.get('body', '{}'))
                    print(f"   ✅ Status: {body.get('status', 'Unknown')}")
                else:
                    print(f"   ❌ Status: {parsed_payload.get('statusCode')}")
                    
            except Exception as e:
                print(f"   ❌ Erreur parsing payload: {e}")
        else:
            print(f"   � Payload n'est pas streamable: {payload}")
        
        # Test 2: Invocation avec payload vide
        print("\n📦 Test 2: Invocation avec payload vide")
        
        response2 = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=""
        )
        
        print(f"   📊 StatusCode: {response2.get('StatusCode', 'N/A')}")
        print(f"   📊 Payload: {response2.get('Payload')}")
        
    except Exception as e:
        print(f"❌ Erreur diagnostic: {e}")

if __name__ == "__main__":
    debug_lambda_response()
