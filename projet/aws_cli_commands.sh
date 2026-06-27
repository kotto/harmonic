#!/bin/bash
"""
🚀 COMMANDES AWS CLI POUR AUGMENTATION PERMISSIONS DEEPSEEK V4 PRO
Script bash pour exécuter manuellement les commandes AWS CLI
"""

echo "🚀 AUGMENTATION PERMISSIONS AWS CLI - DEEPSEEK V4 PRO"
echo "======================================================"

# Configuration
AWS_ACCESS_KEY="AKIAUX3GRWKTZEPOJOFI"
AWS_SECRET_KEY="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"
AWS_REGION="us-east-1"
USER_NAME="harmonic-ai-user"

echo "📋 Configuration AWS:"
echo "   Access Key: ${AWS_ACCESS_KEY:0:20}..."
echo "   Secret Key: ${AWS_SECRET_KEY:0:20}..."
echo "   Region: ${AWS_REGION}"
echo "   User: ${USER_NAME}"

# Configurer AWS CLI
echo ""
echo "🔧 Configuration AWS CLI..."
aws configure set aws_access_key_id ${AWS_ACCESS_KEY}
aws configure set aws_secret_access_key ${AWS_SECRET_KEY}
aws configure set region ${AWS_REGION}

# Vérifier la configuration
echo ""
echo "🔍 Vérification configuration AWS CLI..."
aws configure list

# Créer la politique S3
echo ""
echo "📝 Création politique S3..."
aws iam create-policy \
    --policy-name DeepSeekCompleteS3Access \
    --policy-document file://s3-policy.json \
    --description "Accès S3 complet pour DeepSeek V4 Pro - Tous les buckets"

# Créer la politique IAM
echo ""
echo "📝 Création politique IAM..."
aws iam create-policy \
    --policy-name DeepSeekCompleteIAMAccess \
    --policy-document file://iam-policy.json \
    --description "Accès IAM complet pour DeepSeek V4 Pro"

# Obtenir les ARNs des politiques
echo ""
echo "🔍 Obtention ARNs des politiques..."
S3_POLICY_ARN=$(aws iam list-policies --query 'Policies[?PolicyName==`DeepSeekCompleteS3Access`].Arn' --output text)
IAM_POLICY_ARN=$(aws iam list-policies --query 'Policies[?PolicyName==`DeepSeekCompleteIAMAccess`].Arn' --output text)

echo "   S3 Policy ARN: ${S3_POLICY_ARN}"
echo "   IAM Policy ARN: ${IAM_POLICY_ARN}"

# Attacher les politiques à l'utilisateur
echo ""
echo "🔗 Attachement politiques à l'utilisateur..."
aws iam attach-user-policy \
    --user-name ${USER_NAME} \
    --policy-arn ${S3_POLICY_ARN}

aws iam attach-user-policy \
    --user-name ${USER_NAME} \
    --policy-arn ${IAM_POLICY_ARN}

echo "✅ Politiques attachées"

# Attendre la propagation des permissions
echo ""
echo "⏳ Attente propagation permissions (30 secondes)..."
sleep 30

# Tester l'accès au bucket DeepSeek
echo ""
echo "🔍 Test accès bucket DeepSeek..."
aws s3 ls s3://deepseek-models-326095712935/ --recursive --no-paginate

# Tester l'accès à tous les buckets
echo ""
echo "🔍 Test accès tous les buckets..."
for bucket in deepseek-models-326095712935 harmonic-ai-knowledge-base connective-ai-deployment hcv-pro-deepseek-frontend-326095712935 hcv-pro-deepseek-test-326095712935; do
    echo "🔍 Test bucket: ${bucket}"
    aws s3 ls s3://${bucket}/ --recursive --max-items 5
done

echo ""
echo "🏆 AUGMENTATION PERMISSIONS TERMINÉE!"
echo "✅ Prêt pour télécharger DeepSeek V4 Pro (1.2TB)"
echo "✅ Exécuter: python download_deepseek_weights_s3.py"
