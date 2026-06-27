#!/bin/bash
# Configuration AWS pour Harmonic AI
# Exécutez: source set_aws_env_configured.sh

export AWS_ACCESS_KEY_ID="AKIAUX3GRWKTZEPOJOFI"
export AWS_SECRET_ACCESS_KEY="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"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_REGION="us-east-1"
export HARMONIC_BUCKET="harmonic-ai-knowledge-base"

echo "Variables AWS configurées"
echo "Bucket: $HARMONIC_BUCKET"
echo "Region: $AWS_REGION"
echo "Prêt pour l'upload S3"
