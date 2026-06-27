# Configuration AWS pour Harmonic AI
# Exécutez: .\set_aws_env_configured.ps1

$env:AWS_ACCESS_KEY_ID = "AKIAUX3GRWKTZEPOJOFI"
$env:AWS_SECRET_ACCESS_KEY = "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"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_REGION = "us-east-1"
$env:HARMONIC_BUCKET = "harmonic-ai-knowledge-base"

Write-Host "Variables AWS configurées"
Write-Host "Bucket: $env:HARMONIC_BUCKET"
Write-Host "Region: $env:AWS_REGION"
Write-Host "Prêt pour l'upload S3"
