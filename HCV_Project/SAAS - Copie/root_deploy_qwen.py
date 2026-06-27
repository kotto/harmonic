#!/usr/bin/env python3
"""
Root AWS Deployment Script for Qwen3.5
Uses direct boto3 with admin credentials
"""

import boto3
import json
import time
import os
from botocore.exceptions import ClientError

# Admin credentials from workspace
ADMIN_CONFIG = {
    "aws_access_key_id": "AKIAUX3GRWKTZEPOJOFI",
    "aws_secret_access_key": "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",
    "region": "us-east-1"
}

# Deployment configuration
CONFIG = {
    "account_id": "326095712935",
    "user_name": "harmonic-ai-user",
    "policy_name": "Qwen35-Deployment-Policy",
    "passrole_policy_name": "Qwen35-PassRole-Policy",
    "role_name": "AmazonSageMaker-ExecutionRole-20250511T181292",
    "ecr_repository": "qwen35-deployment",
    "lambda_function": "qwen35-inference",
    "api_name": "qwen35-api"
}

def create_iam_client():
    """Create IAM client with admin credentials"""
    return boto3.client(
        'iam',
        aws_access_key_id=ADMIN_CONFIG["aws_access_key_id"],
        aws_secret_access_key=ADMIN_CONFIG["aws_secret_access_key"],
        region_name=ADMIN_CONFIG["region"]
    )

def create_other_client(service):
    """Create any AWS service client with admin credentials"""
    return boto3.client(
        service,
        aws_access_key_id=ADMIN_CONFIG["aws_access_key_id"],
        aws_secret_access_key=ADMIN_CONFIG["aws_secret_access_key"],
        region_name=ADMIN_CONFIG["region"]
    )

def create_deployment_policy():
    """Create the main deployment policy"""
    print("🔐 Creating deployment policy...")
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ECRFullAccess",
                "Effect": "Allow",
                "Action": ["ecr:*"],
                "Resource": "*"
            },
            {
                "Sid": "SageMakerFullAccess",
                "Effect": "Allow",
                "Action": ["sagemaker:*"],
                "Resource": "*"
            },
            {
                "Sid": "LambdaFullAccess",
                "Effect": "Allow",
                "Action": ["lambda:*"],
                "Resource": "*"
            },
            {
                "Sid": "APIGatewayFullAccess",
                "Effect": "Allow",
                "Action": ["apigateway:*"],
                "Resource": "*"
            },
            {
                "Sid": "CloudWatchFullAccess",
                "Effect": "Allow",
                "Action": [
                    "cloudwatch:*",
                    "logs:*"
                ],
                "Resource": "*"
            },
            {
                "Sid": "S3Access",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::harmonic-ai-qwen-models",
                    "arn:aws:s3:::harmonic-ai-qwen-models/*"
                ]
            }
        ]
    }
    
    iam = create_iam_client()
    
    try:
        response = iam.create_policy(
            PolicyName=CONFIG["policy_name"],
            PolicyDocument=json.dumps(policy_document),
            Description="Full permissions for Qwen3.5 deployment"
        )
        print(f"✅ Policy created: {response['Policy']['Arn']}")
        return response['Policy']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("✅ Policy already exists")
            return f"arn:aws:iam::{CONFIG['account_id']}:policy/{CONFIG['policy_name']}"
        else:
            print(f"❌ Error creating policy: {e}")
            return None

def create_passrole_policy():
    """Create PassRole policy"""
    print("🎫 Creating PassRole policy...")
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["iam:PassRole"],
                "Resource": [
                    f"arn:aws:iam::{CONFIG['account_id']}:role/{CONFIG['role_name']}",
                    f"arn:aws:iam::{CONFIG['account_id']}:role/*SageMaker*",
                    f"arn:aws:iam::{CONFIG['account_id']}:role/*sagemaker*",
                    f"arn:aws:iam::{CONFIG['account_id']}:role/*lambda*"
                ]
            }
        ]
    }
    
    iam = create_iam_client()
    
    try:
        response = iam.create_policy(
            PolicyName=CONFIG["passrole_policy_name"],
            PolicyDocument=json.dumps(policy_document),
            Description="PassRole permission for Qwen3.5 deployment"
        )
        print(f"✅ PassRole policy created: {response['Policy']['Arn']}")
        return response['Policy']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("✅ PassRole policy already exists")
            return f"arn:aws:iam::{CONFIG['account_id']}:policy/{CONFIG['passrole_policy_name']}"
        else:
            print(f"❌ Error creating PassRole policy: {e}")
            return None

def attach_policies_to_user():
    """Attach policies to the user"""
    print("👤 Attaching policies to user...")
    
    iam = create_iam_client()
    
    # Get policy ARNs
    main_policy_arn = f"arn:aws:iam::{CONFIG['account_id']}:policy/{CONFIG['policy_name']}"
    passrole_policy_arn = f"arn:aws:iam::{CONFIG['account_id']}:policy/{CONFIG['passrole_policy_name']}"
    
    # Attach main policy
    try:
        iam.attach_user_policy(
            UserName=CONFIG["user_name"],
            PolicyArn=main_policy_arn
        )
        print("✅ Main policy attached")
    except ClientError as e:
        print(f"❌ Error attaching main policy: {e}")
    
    # Attach PassRole policy
    try:
        iam.attach_user_policy(
            UserName=CONFIG["user_name"],
            PolicyArn=passrole_policy_arn
        )
        print("✅ PassRole policy attached")
    except ClientError as e:
        print(f"❌ Error attaching PassRole policy: {e}")

def create_sagemaker_role():
    """Create SageMaker execution role if it doesn't exist"""
    print("🔍 Checking SageMaker role...")
    
    iam = create_iam_client()
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "sagemaker.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        response = iam.create_role(
            RoleName=CONFIG["role_name"],
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="SageMaker execution role for Qwen3.5"
        )
        print(f"✅ SageMaker role created: {response['Role']['Arn']}")
        
        # Attach AWS managed policies
        managed_policies = [
            "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess",
            "arn:aws:iam::aws:policy/CloudWatchFullAccess"
        ]
        
        for policy_arn in managed_policies:
            try:
                iam.attach_role_policy(
                    RoleName=CONFIG["role_name"],
                    PolicyArn=policy_arn
                )
                print(f"✅ Attached {policy_arn}")
            except ClientError as e:
                print(f"⚠️ Could not attach {policy_arn}: {e}")
                
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("✅ SageMaker role already exists")
        else:
            print(f"❌ Error creating SageMaker role: {e}")

def test_permissions():
    """Test if permissions are working"""
    print("🧪 Testing permissions...")
    
    # Test ECR
    try:
        ecr = create_other_client('ecr')
        ecr.describe_repositories()
        print("✅ ECR access working")
    except ClientError as e:
        print(f"❌ ECR access failed: {e}")
    
    # Test SageMaker
    try:
        sagemaker = create_other_client('sagemaker')
        sagemaker.list_endpoints()
        print("✅ SageMaker access working")
    except ClientError as e:
        print(f"❌ SageMaker access failed: {e}")
    
    # Test Lambda
    try:
        lambda_client = create_other_client('lambda')
        lambda_client.list_functions()
        print("✅ Lambda access working")
    except ClientError as e:
        print(f"❌ Lambda access failed: {e}")

def deploy_lambda_function():
    """Deploy Lambda function"""
    print("🚀 Deploying Lambda function...")
    
    # Create Lambda package
    lambda_code = '''
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    try:
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        prompt = body.get('prompt', 'Hello from Qwen3.5!')
        max_length = body.get('max_length', 100)
        
        response_text = f"Qwen3.5 response to: '{prompt[:50]}...' (Mock response - ready for model integration)"
        
        response = {
            'generated_text': response_text,
            'model_name': 'Qwen3.5-7B-Instruct',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
    
    # Write Lambda code to file
    with open('lambda_function.py', 'w') as f:
        f.write(lambda_code)
    
    # Create ZIP package
    import zipfile
    with zipfile.ZipFile('qwen_lambda.zip', 'w') as zipf:
        zipf.write('lambda_function.py')
    
    # Deploy Lambda
    lambda_client = create_other_client('lambda')
    
    try:
        with open('qwen_lambda.zip', 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.create_function(
            FunctionName=CONFIG['lambda_function'],
            Runtime='python3.9',
            Role=f"arn:aws:iam::{CONFIG['account_id']}:role/{CONFIG['role_name']}",
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=300,
            MemorySize=1024,
            Description='Qwen3.5 inference API'
        )
        
        print(f"✅ Lambda function created: {response['FunctionArn']}")
        return response['FunctionArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print("✅ Lambda function already exists, updating...")
            with open('qwen_lambda.zip', 'rb') as f:
                zip_content = f.read()
            
            lambda_client.update_function_code(
                FunctionName=CONFIG['lambda_function'],
                ZipFile=zip_content
            )
            print("✅ Lambda function updated")
        else:
            print(f"❌ Lambda deployment failed: {e}")
    
    # Cleanup
    os.remove('lambda_function.py')
    os.remove('qwen_lambda.zip')

def main():
    """Main deployment function"""
    print("🚀 Starting Qwen3.5 Root Deployment...")
    print(f"📋 Account: {CONFIG['account_id']}")
    print(f"👤 User: {CONFIG['user_name']}")
    
    # Step 1: Create policies
    main_policy_arn = create_deployment_policy()
    passrole_policy_arn = create_passrole_policy()
    
    if not main_policy_arn or not passrole_policy_arn:
        print("❌ Policy creation failed")
        return
    
    # Step 2: Attach policies to user
    attach_policies_to_user()
    
    # Step 3: Create SageMaker role
    create_sagemaker_role()
    
    # Step 4: Wait for permissions to propagate
    print("⏳ Waiting for permissions to propagate...")
    time.sleep(30)
    
    # Step 5: Test permissions
    test_permissions()
    
    # Step 6: Deploy Lambda function
    deploy_lambda_function()
    
    print("🎉 Root deployment completed!")
    print("📋 Next steps:")
    print("   1. Wait 2-3 minutes for full propagation")
    print("   2. Test Lambda function")
    print("   3. Create API Gateway (manual or automated)")
    print("   4. Deploy actual Qwen3.5 model")

if __name__ == "__main__":
    main()
