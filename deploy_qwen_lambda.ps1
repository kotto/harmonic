# Qwen3.5 Lambda Deployment (Simplified Version)
# Uses Lambda + API Gateway instead of SageMaker
# Requires minimal AWS permissions

param(
    [string]$Region = "us-east-1",
    [string]$FunctionName = "qwen35-inference",
    [string]$ApiName = "qwen35-api"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Qwen3.5 Lambda deployment..." -ForegroundColor Green

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
New-Item -ItemType Directory -Path "lambda-qwen" -Force | Out-Null

# Create Lambda function code
Write-Host "📝 Creating Lambda function..." -ForegroundColor Yellow
@"
import json
import boto3
import os
import base64
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Handle different API Gateway formats
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        # Extract prompt from request
        prompt = body.get('prompt', 'Hello from Qwen3.5!')
        max_length = body.get('max_length', 100)
        temperature = body.get('temperature', 0.7)
        
        # Simulate Qwen3.5 inference (replace with actual model loading)
        # For now, return a mock response
        response_text = f"Qwen3.5 response to: '{prompt[:50]}...' (Mock response - model loading requires S3 setup)"
        
        # Create response
        response = {
            'generated_text': response_text,
            'model_name': 'Qwen3.5-7B-Instruct',
            'timestamp': datetime.utcnow().isoformat(),
            'parameters': {
                'max_length': max_length,
                'temperature': temperature
            },
            'status': 'success',
            'note': 'This is a mock response. Actual model integration requires S3 model files and proper permissions.'
        }
        
        # API Gateway response format
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        error_response = {
            'error': str(e),
            'message': 'An error occurred during inference',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(error_response)
        }

# Health check endpoint
def health_check():
    return {
        'status': 'healthy',
        'service': 'Qwen3.5 Lambda',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'model_loaded': False,
        'note': 'Model loading requires proper S3 setup and permissions'
    }
"@ | Out-File -FilePath "lambda-qwen\lambda_function.py" -Encoding UTF8

# Create requirements.txt
@"
boto3>=1.26.0
requests>=2.31.0
"@ | Out-File -FilePath "lambda-qwen\requirements.txt" -Encoding UTF8

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
Compress-Archive -Path "lambda-qwen\*" -DestinationPath "qwen35-lambda.zip" -Force

# Try to create Lambda function
Write-Host "🚀 Deploying Lambda function..." -ForegroundColor Yellow
try {
    $lambdaRole = "arn:aws:iam::326095712935:role/lambda-execution-role"
    
    # Create Lambda function
    $result = aws lambda create-function `
        --function-name $FunctionName `
        --runtime python3.9 `
        --handler lambda_function.lambda_handler `
        --zip-file fileb://qwen35-lambda.zip `
        --role $lambdaRole `
        --description "Qwen3.5 inference API" `
        --timeout 300 `
        --memory-size 1024 `
        --environment Variables="{MODEL_NAME=Qwen3.5,REGION=$Region}" `
        --region $Region | ConvertFrom-Json
    
    Write-Host "✅ Lambda function created: $($result.FunctionName)" -ForegroundColor Green
    Write-Host "📍 Function ARN: $($result.FunctionArn)" -ForegroundColor Cyan
    
} catch {
    Write-Host "⚠️ Lambda creation failed. Trying to update existing function..." -ForegroundColor Yellow
    try {
        aws lambda update-function-code `
            --function-name $FunctionName `
            --zip-file fileb://qwen35-lambda.zip `
            --region $Region | Out-Null
        
        Write-Host "✅ Lambda function updated" -ForegroundColor Green
    } catch {
        Write-Host "❌ Lambda deployment failed: $_" -ForegroundColor Red
        Write-Host "📋 Manual deployment required:" -ForegroundColor Cyan
        Write-Host "   1. Upload qwen35-lambda.zip to Lambda console" -ForegroundColor White
        Write-Host "   2. Create function with runtime python3.9" -ForegroundColor White
        Write-Host "   3. Set handler to lambda_function.lambda_handler" -ForegroundColor White
        Write-Host "   4. Set timeout to 300s and memory to 1024MB" -ForegroundColor White
    }
}

# Try to create API Gateway
Write-Host "🌐 Creating API Gateway..." -ForegroundColor Yellow
try {
    # Create REST API
    $apiResult = aws apigateway create-rest-api `
        --name $ApiName `
        --description "Qwen3.5 inference API" `
        --region $Region | ConvertFrom-Json
    
    $apiId = $apiResult.id
    Write-Host "✅ API Gateway created: $apiId" -ForegroundColor Green
    
    # Get root resource
    $resources = aws apigateway get-resources `
        --rest-api-id $apiId `
        --region $Region | ConvertFrom-Json
    
    $rootId = $resources.items | Where-Object { $_.path -eq "/" } | Select-Object -ExpandProperty id
    
    # Create resource
    $resource = aws apigateway create-resource `
        --rest-api-id $apiId `
        --parent-id $rootId `
        --path-part "generate" `
        --region $Region | ConvertFrom-Json
    
    $resourceId = $resource.id
    
    # Add POST method
    aws apigateway put-method `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method POST `
        --authorization-type "NONE" `
        --region $Region | Out-Null
    
    # Add Lambda integration
    $lambdaArn = "arn:aws:lambda:$Region:326095712935:function:$FunctionName"
    
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method POST `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri "arn:aws:apigateway:$Region:lambda:path/2015-03-31/functions/$lambdaArn/invocations" `
        --region $Region | Out-Null
    
    # Add GET method for health check
    aws apigateway put-method `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method GET `
        --authorization-type "NONE" `
        --region $Region | Out-Null
    
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method GET `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri "arn:aws:apigateway:$Region:lambda:path/2015-03-31/functions/$lambdaArn/invocations" `
        --region $Region | Out-Null
    
    # Deploy API
    aws apigateway create-deployment `
        --rest-api-id $apiId `
        --stage-name prod `
        --region $Region | Out-Null
    
    $apiUrl = "https://$apiId.execute-api.$Region.amazonaws.com/prod/generate"
    Write-Host "🌐 API Gateway deployed: $apiUrl" -ForegroundColor Green
    
    # Add Lambda permission for API Gateway
    aws lambda add-permission `
        --function-name $FunctionName `
        --statement-id "apigateway-$apiId" `
        --action "lambda:InvokeFunction" `
        --principal "apigateway.amazonaws.com" `
        --source-arn "arn:aws:execute-api:$Region:326095712935:$apiId/*/POST/generate" `
        --region $Region | Out-Null
    
    aws lambda add-permission `
        --function-name $FunctionName `
        --statement-id "apigateway-$apiId-get" `
        --action "lambda:InvokeFunction" `
        --principal "apigateway.amazonaws.com" `
        --source-arn "arn:aws:execute-api:$Region:326095712935:$apiId/*/GET/generate" `
        --region $Region | Out-Null
    
    Write-Host "🎉 Full deployment completed!" -ForegroundColor Green
    Write-Host "📍 API URL: $apiUrl" -ForegroundColor Cyan
    Write-Host "🧪 Test with: curl -X POST $apiUrl -H 'Content-Type: application/json' -d '{\"prompt\":\"Hello\"}'" -ForegroundColor White
    
} catch {
    Write-Host "⚠️ API Gateway creation failed: $_" -ForegroundColor Yellow
    Write-Host "📋 API Gateway requires additional permissions" -ForegroundColor Red
}

# Test Lambda function directly
Write-Host "🧪 Testing Lambda function..." -ForegroundColor Yellow
try {
    $testEvent = @{
        prompt = "Hello, how are you?"
        max_length = 100
    } | ConvertTo-Json
    
    $result = aws lambda invoke `
        --function-name $FunctionName `
        --payload "$testEvent" `
        --region $Region `
        response.json | ConvertFrom-Json
    
    Write-Host "✅ Lambda test successful" -ForegroundColor Green
    Write-Host "📊 Response: $($result.StatusCode)" -ForegroundColor Cyan
    
    # Show response content
    if (Test-Path "response.json") {
        $responseContent = Get-Content "response.json" | ConvertFrom-Json
        Write-Host "📝 Generated text: $($responseContent.generated_text)" -ForegroundColor White
    }
    
} catch {
    Write-Host "❌ Lambda test failed: $_" -ForegroundColor Red
}

# Cleanup
Write-Host "🧹 Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item -Path "lambda-qwen" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "qwen35-lambda.zip" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "response.json" -Force -ErrorAction SilentlyContinue

Write-Host "🎯 Lambda deployment completed!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "   - Lambda Function: $FunctionName" -ForegroundColor White
Write-Host "   - Region: $Region" -ForegroundColor White
Write-Host "   - Memory: 1024MB" -ForegroundColor White
Write-Host "   - Timeout: 300s" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "🔧 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Add proper S3 permissions for model loading" -ForegroundColor White
Write-Host "   2. Upload Qwen3.5 model files to S3" -ForegroundColor White
Write-Host "   3. Update Lambda function to load actual model" -ForegroundColor White
Write-Host "   4. Configure API Gateway if needed" -ForegroundColor White
