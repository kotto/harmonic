# Test Qwen3.5 Lambda Function
import json
import boto3

# Test the Lambda function
lambda_client = boto3.client('lambda', region_name='us-east-1')

try:
    # Test data
    test_payload = {
        'prompt': 'Hello Qwen3.5! How are you today?',
        'max_length': 100,
        'temperature': 0.7
    }
    
    # Invoke Lambda
    response = lambda_client.invoke(
        FunctionName='qwen35-simple',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_payload)
    )
    
    # Parse response
    result = json.loads(response['Payload'].read())
    
    print("🚀 Qwen3.5 Lambda Test Results:")
    print(f"Status Code: {result.get('statusCode')}")
    
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        print(f"Status: {body.get('status')}")
        print(f"Model: {body.get('model_name')}")
        print(f"Generated Text Preview: {body.get('generated_text', '')[:200]}...")
    else:
        print(f"Error: {result}")
        
except Exception as e:
    print(f"❌ Test failed: {e}")

print("\n📋 Next Steps:")
print("1. Set up API Gateway for HTTP access")
print("2. Add S3 permissions for model files")
print("3. Integrate actual Qwen3.5 model")
print("4. Configure proper IAM roles")
