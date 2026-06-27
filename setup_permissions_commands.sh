#!/bin/bash

# AWS Permissions Setup Commands for Qwen3.5 Deployment
# Run these commands as AWS administrator or with appropriate permissions

echo "🔧 Setting up AWS permissions for Qwen3.5 deployment..."

# Variables
AWS_ACCOUNT_ID="326095712935"
USER_NAME="harmonic-ai-user"
POLICY_NAME="Qwen35-Deployment-Policy"
ROLE_NAME="AmazonSageMaker-ExecutionRole-20250511T181292"

echo "📋 Account ID: $AWS_ACCOUNT_ID"
echo "👤 User: $USER_NAME"
echo "📜 Policy: $POLICY_NAME"

# Create the IAM policy
echo "🔐 Creating IAM policy..."
aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file://aws_permissions_policy.json \
    --description "Full permissions for Qwen3.5 deployment including ECR, SageMaker, and CloudWatch"

# Attach the policy to the user
echo "👤 Attaching policy to user..."
aws iam attach-user-policy \
    --user-name "$USER_NAME" \
    --policy-arn "arn:aws:iam::$AWS_ACCOUNT_ID:policy/$POLICY_NAME"

# Verify the policy attachment
echo "✅ Verifying policy attachment..."
aws iam list-attached-user-policies \
    --user-name "$USER_NAME" \
    --query "AttachedPolicies[?PolicyName=='$POLICY_NAME']"

# Check if SageMaker execution role exists, create if not
echo "🔍 Checking SageMaker execution role..."
ROLE_EXISTS=$(aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null || echo "not_found")

if [ "$ROLE_EXISTS" = "not_found" ]; then
    echo "📝 Creating SageMaker execution role..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document '{
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
        }' \
        --description "SageMaker execution role for Qwen3.5 deployment"
    
    # Attach SageMaker full access policy to the role
    echo "🔗 Attaching SageMaker policy to role..."
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
    
    # Attach CloudWatch policy to the role
    echo "📊 Attaching CloudWatch policy to role..."
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/CloudWatchFullAccess"
    
    # Attach S3 policy to the role
    echo "📦 Attaching S3 policy to role..."
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonS3FullAccess"
else
    echo "✅ SageMaker execution role already exists"
fi

# Grant PassRole permission to the user for the SageMaker role
echo "🎫 Granting PassRole permission..."
cat > pass_role_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME"
        }
    ]
}
EOF

# Create PassRole policy
aws iam create-policy \
    --policy-name "Qwen35-PassRole-Policy" \
    --policy-document file://pass_role_policy.json \
    --description "PassRole permission for Qwen3.5 SageMaker execution role"

# Attach PassRole policy to user
aws iam attach-user-policy \
    --user-name "$USER_NAME" \
    --policy-arn "arn:aws:iam::$AWS_ACCOUNT_ID:policy/Qwen35-PassRole-Policy"

# Test permissions
echo "🧪 Testing permissions..."
echo "Testing ECR access..."
aws ecr describe-repositories --region us-east-1 2>/dev/null && echo "✅ ECR access OK" || echo "❌ ECR access failed"

echo "Testing SageMaker access..."
aws sagemaker list-endpoints --region us-east-1 2>/dev/null && echo "✅ SageMaker access OK" || echo "❌ SageMaker access failed"

echo "Testing CloudWatch access..."
aws cloudwatch list-metrics --region us-east-1 2>/dev/null && echo "✅ CloudWatch access OK" || echo "❌ CloudWatch access failed"

echo "Testing IAM PassRole..."
aws iam simulate-principal-policy \
    --policy-source-arn "arn:aws:iam::$AWS_ACCOUNT_ID:user/$USER_NAME" \
    --action-names "iam:PassRole" \
    --resource-arns "arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME" \
    --region us-east-1 2>/dev/null && echo "✅ PassRole access OK" || echo "❌ PassRole access failed"

# Cleanup temporary files
rm -f pass_role_policy.json

echo "🎉 Permissions setup completed!"
echo ""
echo "📋 Summary of created resources:"
echo "   - Policy: $POLICY_NAME"
echo "   - PassRole Policy: Qwen35-PassRole-Policy"
echo "   - Role: $ROLE_NAME"
echo ""
echo "⏳ Please wait 1-2 minutes for permissions to propagate across AWS regions."
echo "🔄 After waiting, you can run the deployment script again."
echo ""
echo "🧪 To verify permissions are working, run:"
echo "   aws sts get-caller-identity"
echo "   aws ecr describe-repositories --region us-east-1"
echo "   aws sagemaker list-endpoints --region us-east-1"
