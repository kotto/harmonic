# AWS Permissions Setup Commands for Qwen3.5 Deployment (PowerShell Version)
# Run these commands as AWS administrator or with appropriate permissions

param(
    [string]$AWS_ACCOUNT_ID = "326095712935",
    [string]$USER_NAME = "harmonic-ai-user",
    [string]$POLICY_NAME = "Qwen35-Deployment-Policy",
    [string]$ROLE_NAME = "AmazonSageMaker-ExecutionRole-20250511T181292"
)

Write-Host "🔧 Setting up AWS permissions for Qwen3.5 deployment..." -ForegroundColor Green

Write-Host "📋 Account ID: $AWS_ACCOUNT_ID" -ForegroundColor Cyan
Write-Host "👤 User: $USER_NAME" -ForegroundColor Cyan
Write-Host "📜 Policy: $POLICY_NAME" -ForegroundColor Cyan

# Check if policy file exists
if (-not (Test-Path "aws_permissions_policy.json")) {
    Write-Host "❌ aws_permissions_policy.json not found. Please create it first." -ForegroundColor Red
    exit 1
}

# Create the IAM policy
Write-Host "🔐 Creating IAM policy..." -ForegroundColor Yellow
try {
    $policyContent = Get-Content "aws_permissions_policy.json" -Raw
    aws iam create-policy `
        --policy-name "$POLICY_NAME" `
        --policy-document "$policyContent" `
        --description "Full permissions for Qwen3.5 deployment including ECR, SageMaker, and CloudWatch"
    Write-Host "✅ Policy created successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Policy may already exist or error occurred: $_" -ForegroundColor Yellow
}

# Attach the policy to the user
Write-Host "👤 Attaching policy to user..." -ForegroundColor Yellow
try {
    aws iam attach-user-policy `
        --user-name "$USER_NAME" `
        --policy-arn "arn:aws:iam::$AWS_ACCOUNT_ID:policy/$POLICY_NAME"
    Write-Host "✅ Policy attached to user" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to attach policy: $_" -ForegroundColor Red
}

# Verify the policy attachment
Write-Host "✅ Verifying policy attachment..." -ForegroundColor Yellow
aws iam list-attached-user-policies `
    --user-name "$USER_NAME" `
    --query "AttachedPolicies[?PolicyName=='$POLICY_NAME']"

# Check if SageMaker execution role exists, create if not
Write-Host "🔍 Checking SageMaker execution role..." -ForegroundColor Yellow
try {
    aws iam get-role --role-name "$ROLE_NAME" | Out-Null
    Write-Host "✅ SageMaker execution role already exists" -ForegroundColor Green
} catch {
    Write-Host "📝 Creating SageMaker execution role..." -ForegroundColor Yellow
    
    $trustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    Service = "sagemaker.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        )
    }
    
    $trustPolicyJson = $trustPolicy | ConvertTo-Json -Depth 10
    
    aws iam create-role `
        --role-name "$ROLE_NAME" `
        --assume-role-policy-document "$trustPolicyJson" `
        --description "SageMaker execution role for Qwen3.5 deployment"
    
    # Attach SageMaker full access policy to the role
    Write-Host "🔗 Attaching SageMaker policy to role..." -ForegroundColor Yellow
    aws iam attach-role-policy `
        --role-name "$ROLE_NAME" `
        --policy-arn "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
    
    # Attach CloudWatch policy to the role
    Write-Host "📊 Attaching CloudWatch policy to role..." -ForegroundColor Yellow
    aws iam attach-role-policy `
        --role-name "$ROLE_NAME" `
        --policy-arn "arn:aws:iam::aws:policy/CloudWatchFullAccess"
    
    # Attach S3 policy to the role
    Write-Host "📦 Attaching S3 policy to role..." -ForegroundColor Yellow
    aws iam attach-role-policy `
        --role-name "$ROLE_NAME" `
        --policy-arn "arn:aws:iam::aws:policy/AmazonS3FullAccess"
    
    Write-Host "✅ SageMaker execution role created and configured" -ForegroundColor Green
}

# Grant PassRole permission to the user for the SageMaker role
Write-Host "🎫 Granting PassRole permission..." -ForegroundColor Yellow

$passRolePolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = "iam:PassRole"
            Resource = "arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME"
        }
    )
}

$passRolePolicyJson = $passRolePolicy | ConvertTo-Json -Depth 10

# Create PassRole policy
try {
    aws iam create-policy `
        --policy-name "Qwen35-PassRole-Policy" `
        --policy-document "$passRolePolicyJson" `
        --description "PassRole permission for Qwen3.5 SageMaker execution role"
    
    # Attach PassRole policy to user
    aws iam attach-user-policy `
        --user-name "$USER_NAME" `
        --policy-arn "arn:aws:iam::$AWS_ACCOUNT_ID:policy/Qwen35-PassRole-Policy"
    
    Write-Host "✅ PassRole permission granted" -ForegroundColor Green
} catch {
    Write-Host "⚠️ PassRole policy may already exist: $_" -ForegroundColor Yellow
}

# Test permissions
Write-Host "🧪 Testing permissions..." -ForegroundColor Yellow

Write-Host "Testing ECR access..." -ForegroundColor Cyan
try {
    aws ecr describe-repositories --region us-east-1 | Out-Null
    Write-Host "✅ ECR access OK" -ForegroundColor Green
} catch {
    Write-Host "❌ ECR access failed: $_" -ForegroundColor Red
}

Write-Host "Testing SageMaker access..." -ForegroundColor Cyan
try {
    aws sagemaker list-endpoints --region us-east-1 | Out-Null
    Write-Host "✅ SageMaker access OK" -ForegroundColor Green
} catch {
    Write-Host "❌ SageMaker access failed: $_" -ForegroundColor Red
}

Write-Host "Testing CloudWatch access..." -ForegroundColor Cyan
try {
    aws cloudwatch list-metrics --region us-east-1 | Out-Null
    Write-Host "✅ CloudWatch access OK" -ForegroundColor Green
} catch {
    Write-Host "❌ CloudWatch access failed: $_" -ForegroundColor Red
}

Write-Host "Testing IAM PassRole..." -ForegroundColor Cyan
try {
    aws iam simulate-principal-policy `
        --policy-source-arn "arn:aws:iam::$AWS_ACCOUNT_ID:user/$USER_NAME" `
        --action-names "iam:PassRole" `
        --resource-arns "arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME" `
        --region us-east-1 | Out-Null
    Write-Host "✅ PassRole access OK" -ForegroundColor Green
} catch {
    Write-Host "❌ PassRole access failed: $_" -ForegroundColor Red
}

Write-Host "🎉 Permissions setup completed!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "📋 Summary of created resources:" -ForegroundColor Cyan
Write-Host "   - Policy: $POLICY_NAME" -ForegroundColor White
Write-Host "   - PassRole Policy: Qwen35-PassRole-Policy" -ForegroundColor White
Write-Host "   - Role: $ROLE_NAME" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "⏳ Please wait 1-2 minutes for permissions to propagate across AWS regions." -ForegroundColor Yellow
Write-Host "🔄 After waiting, you can run the deployment script again." -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "🧪 To verify permissions are working, run:" -ForegroundColor Cyan
Write-Host "   aws sts get-caller-identity" -ForegroundColor White
Write-Host "   aws ecr describe-repositories --region us-east-1" -ForegroundColor White
Write-Host "   aws sagemaker list-endpoints --region us-east-1" -ForegroundColor White
