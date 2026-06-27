#!/bin/bash
# Variables d'environnement AWS pour Harmonic AI
# A exécuter: source set_aws_env.sh

export AWS_ACCESS_KEY_ID="VOTRE_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="VOTRE_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_REGION="us-east-1"
export HARMONIC_BUCKET="harmonic-ai-knowledge-base"

echo "Variables d'environnement AWS configurees"
echo "Bucket: $HARMONIC_BUCKET"
echo "Region: $AWS_REGION"
echo "Pret pour l'upload S3"
