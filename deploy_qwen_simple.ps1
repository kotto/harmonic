# Simplified Qwen3.5 Deployment - Direct Lambda Approach
# Bypasses IAM policy creation by using existing roles

param(
    [string]$Region = "us-east-1",
    [string]$FunctionName = "qwen35-simple",
    [string]$RoleName = "lambda-execution-role"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Simplified Qwen3.5 Deployment..." -ForegroundColor Green

# Check AWS credentials
Write-Host "📋 Verifying AWS credentials..." -ForegroundColor Yellow
try {
    $caller = aws sts get-caller-identity | ConvertFrom-Json
    Write-Host "✅ AWS credentials verified for $($caller.UserId)" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not found" -ForegroundColor Red
    exit 1
}

# Create Lambda function directory
Write-Host "📁 Creating Lambda deployment package..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "lambda-simple" -Force | Out-Null

# Create simplified Lambda function
Write-Host "📝 Creating simplified Lambda function..." -ForegroundColor Yellow
@"
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    """
    Simplified Qwen3.5 Lambda function
    Returns mock responses ready for model integration
    """
    try:
        # Handle different input formats
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        # Extract parameters
        prompt = body.get('prompt', 'Hello from Qwen3.5!')
        max_length = body.get('max_length', 100)
        temperature = body.get('temperature', 0.7)
        
        # Generate mock response (replace with actual model later)
        response_text = f"""Qwen3.5 Response:
        
Prompt: {prompt}

This is a mock response from Qwen3.5-7B-Instruct. The actual model integration requires:
1. S3 access to model files
2. Proper IAM permissions
3. Model loading infrastructure

Generated with parameters:
- Max length: {max_length}
- Temperature: {temperature}
- Timestamp: {datetime.utcnow().isoformat()}

Status: Ready for model integration 🚀"""
        
        # Create response
        response = {
            'generated_text': response_text,
            'model_name': 'Qwen3.5-7B-Instruct-Mock',
            'timestamp': datetime.utcnow().isoformat(),
            'parameters': {
                'max_length': max_length,
                'temperature': temperature
            },
            'status': 'success',
            'deployment_status': 'mock_ready',
            'next_steps': [
                'Add S3 permissions for model files',
                'Upload Qwen3.5 model to S3',
                'Integrate actual model loading',
                'Configure proper IAM roles'
            ]
        }
        
        # Return API Gateway compatible response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
            },
            'body': json.dumps(response, indent=2)
        }
        
    except Exception as e:
        # Error handling
        error_response = {
            'error': str(e),
            'message': 'Qwen3.5 Lambda function encountered an error',
            'timestamp': datetime.utcnow().isoformat(),
            'function': 'qwen35-simple',
            'troubleshooting': 'Check Lambda logs in CloudWatch'
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(error_response, indent=2)
        }

# Health check function
def health_check():
    return {
        'service': 'Qwen3.5 Simple Lambda',
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'model_loaded': False,
        'ready_for_integration': True
    }
"@ | Out-File -FilePath "lambda-simple\lambda_function.py" -Encoding UTF8

# Create requirements.txt
@"
boto3>=1.26.0
"@ | Out-File -FilePath "lambda-simple\requirements.txt" -Encoding UTF8

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
Compress-Archive -Path "lambda-simple\*" -DestinationPath "qwen35-simple.zip" -Force

# Try to create Lambda function with basic execution role
Write-Host "🚀 Deploying Lambda function..." -ForegroundColor Yellow
try {
    # Try different role options
    $roleOptions = @(
        "arn:aws:iam::326095712935:role/lambda-execution-role",
        "arn:aws:iam::326095712935:role/LambdaExecutionRole",
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    )
    
    $lambdaArn = $null
    
    foreach ($role in $roleOptions) {
        try {
            Write-Host "🔍 Trying role: $role" -ForegroundColor Cyan
            
            # Try to create function
            $result = aws lambda create-function `
                --function-name $FunctionName `
                --runtime python3.9 `
                --handler lambda_function.lambda_handler `
                --zip-file fileb://qwen35-simple.zip `
                --role $role `
                --description "Simplified Qwen3.5 inference API" `
                --timeout 300 `
                --memory-size 512 `
                --environment Variables="{FUNCTION_VERSION=simple,MODEL_STATUS=mock}" `
                --region $Region 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                $lambdaArn = ($result | ConvertFrom-Json).FunctionArn
                Write-Host "✅ Lambda function created with role: $role" -ForegroundColor Green
                break
            }
        } catch {
            Write-Host "⚠️ Role failed: $role" -ForegroundColor Yellow
            continue
        }
    }
    
    if (-not $lambdaArn) {
        # Try to update existing function
        Write-Host "🔄 Trying to update existing function..." -ForegroundColor Yellow
        try {
            aws lambda update-function-code `
                --function-name $FunctionName `
                --zip-file fileb://qwen35-simple.zip `
                --region $Region | Out-Null
            
            Write-Host "✅ Lambda function updated" -ForegroundColor Green
            $lambdaArn = "arn:aws:lambda:$Region:326095712935:function:$FunctionName"
        } catch {
            Write-Host "❌ All deployment attempts failed" -ForegroundColor Red
            throw
        }
    }
    
} catch {
    Write-Host "❌ Lambda deployment failed: $_" -ForegroundColor Red
    Write-Host "📋 Manual deployment instructions:" -ForegroundColor Cyan
    Write-Host "   1. Open AWS Lambda console" -ForegroundColor White
    Write-Host "   2. Create function: $FunctionName" -ForegroundColor White
    Write-Host "   3. Runtime: Python 3.9" -ForegroundColor White
    Write-Host "   4. Upload: qwen35-simple.zip" -ForegroundColor White
    Write-Host "   5. Handler: lambda_function.lambda_handler" -ForegroundColor White
    Write-Host "   6. Memory: 512MB, Timeout: 300s" -ForegroundColor White
    exit 1
}

# Test the Lambda function
Write-Host "🧪 Testing Lambda function..." -ForegroundColor Yellow
try {
    $testEvent = @{
        prompt = "Hello from Qwen3.5 simplified deployment!"
        max_length = 150
        temperature = 0.8
    } | ConvertTo-Json
    
    $result = aws lambda invoke `
        --function-name $FunctionName `
        --payload "$testEvent" `
        --region $Region `
        response.json | ConvertFrom-Json
    
    Write-Host "✅ Lambda test successful" -ForegroundColor Green
    Write-Host "📊 Status Code: $($result.StatusCode)" -ForegroundColor Cyan
    
    # Show response content
    if (Test-Path "response.json") {
        $responseContent = Get-Content "response.json" | ConvertFrom-Json
        Write-Host "📝 Response Status: $($responseContent.status)" -ForegroundColor White
        Write-Host "🤖 Model: $($responseContent.model_name)" -ForegroundColor White
    }
    
} catch {
    Write-Host "❌ Lambda test failed: $_" -ForegroundColor Red
}

# Create simple API Gateway using console instructions
Write-Host "🌐 API Gateway Setup Instructions:" -ForegroundColor Yellow
Write-Host "📋 Manual API Gateway creation:" -ForegroundColor Cyan
Write-Host "   1. Open API Gateway console" -ForegroundColor White
Write-Host "   2. Create new REST API" -ForegroundColor White
Write-Host "   3. Add resource: /generate" -ForegroundColor White
Write-Host "   4. Add POST method" -ForegroundColor White
Write-Host "   5. Integration type: Lambda Function" -ForegroundColor White
Write-Host "   6. Lambda function: $FunctionName" -ForegroundColor White
Write-Host "   7. Deploy to stage: prod" -ForegroundColor White

# Create test script
Write-Host "📝 Creating test script..." -ForegroundColor Yellow
@"
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
        FunctionName='$FunctionName',
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
"@ | Out-File -FilePath "test_qwen_lambda.py" -Encoding UTF8

# Cleanup
Write-Host "🧹 Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item -Path "lambda-simple" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "qwen35-simple.zip" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "response.json" -Force -ErrorAction SilentlyContinue

Write-Host "🎉 Simplified deployment completed!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "   - Lambda Function: $FunctionName" -ForegroundColor White
Write-Host "   - Region: $Region" -ForegroundColor White
Write-Host "   - Memory: 512MB" -ForegroundColor White
Write-Host "   - Timeout: 300s" -ForegroundColor White
Write-Host "   - Status: Mock ready for integration" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "🧪 Test with: python test_qwen_lambda.py" -ForegroundColor Cyan
Write-Host "🌐 API Gateway: Manual setup required" -ForegroundColor White
Write-Host "📖 See instructions above for API Gateway setup" -ForegroundColor White
