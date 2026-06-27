# Variables d'environnement AWS pour Harmonic AI
# A exécuter dans PowerShell: .\set_aws_env.ps1

$env:AWS_ACCESS_KEY_ID = "VOTRE_ACCESS_KEY_ID"
$env:AWS_SECRET_ACCESS_KEY = "VOTRE_SECRET_ACCESS_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_REGION = "us-east-1"
$env:HARMONIC_BUCKET = "harmonic-ai-knowledge-base"

Write-Host "Variables d'environnement AWS configurees"
Write-Host "Bucket: $env:HARMONIC_BUCKET"
Write-Host "Region: $env:AWS_REGION"
Write-Host "Pret pour l'upload S3"