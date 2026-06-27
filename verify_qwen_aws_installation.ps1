# Script de vérification de l'installation de Qwen3.5-9B-DeepSeek-V4-Flash-BF16 sur AWS
# Auteur : Harmonic AI Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$ModelName = "Qwen3.5-9B-DeepSeek-V4-Flash-BF16",
    [string]$S3Bucket = "harmonic-ai-qwen-models"
)

$ErrorActionPreference = "Stop"

Write-Host "🔍 Vérification de l'installation de $ModelName sur AWS..." -ForegroundColor Cyan
Write-Host "📍 Région : $Region" -ForegroundColor Yellow
Write-Host "📦 Bucket S3 : $S3Bucket" -ForegroundColor Yellow
Write-Host "=" * 80

# 1. Vérifier les credentials AWS
Write-Host "1️⃣  Vérification des credentials AWS..." -ForegroundColor Green
try {
    $callerIdentity = aws sts get-caller-identity --region $Region 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Credentials AWS valides" -ForegroundColor Green
        $callerIdentity | ConvertFrom-Json | Select-Object Account, UserId, Arn | Format-List
    } else {
        Write-Host "❌ Credentials AWS invalides ou manquants" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erreur lors de la vérification des credentials AWS" -ForegroundColor Red
    exit 1
}

Write-Host "=" * 80

# 2. Vérifier l'accès au bucket S3
Write-Host "2️⃣  Vérification de l'accès au bucket S3..." -ForegroundColor Green
try {
    # Vérifier si le bucket existe
    $bucketExists = aws s3api head-bucket --bucket $S3Bucket --region $Region 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Bucket S3 accessible : $S3Bucket" -ForegroundColor Green
        
        # Lister les objets dans le bucket
        Write-Host "📁 Contenu du bucket S3 :" -ForegroundColor Yellow
        $objects = aws s3 ls "s3://$S3Bucket/" --region $Region 2>&1
        if ($LASTEXITCODE -eq 0) {
            $objects | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
            
            # Vérifier spécifiquement le modèle Qwen
            Write-Host "🔍 Recherche du modèle $ModelName..." -ForegroundColor Yellow
            $qwenObjects = aws s3 ls "s3://$S3Bucket/" --recursive --region $Region | Select-String -Pattern "qwen|Qwen" 2>&1
            if ($qwenObjects) {
                Write-Host "✅ Fichiers Qwen trouvés dans le bucket :" -ForegroundColor Green
                $qwenObjects | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
            } else {
                Write-Host "⚠️  Aucun fichier Qwen trouvé dans le bucket" -ForegroundColor Yellow
            }
        } else {
            Write-Host "⚠️  Impossible de lister le contenu du bucket" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Bucket S3 inaccessible : $S3Bucket" -ForegroundColor Red
        Write-Host "   Message d'erreur : $bucketExists" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Erreur lors de l'accès au bucket S3" -ForegroundColor Red
}

Write-Host "=" * 80

# 3. Vérifier les déploiements SageMaker existants
Write-Host "3️⃣  Vérification des déploiements SageMaker..." -ForegroundColor Green
try {
    # Vérifier les modèles SageMaker
    Write-Host "📋 Modèles SageMaker disponibles :" -ForegroundColor Yellow
    $models = aws sagemaker list-models --region $Region --query 'Models[].ModelName' --output text 2>&1
    if ($LASTEXITCODE -eq 0 -and $models) {
        $models.Split("`t") | ForEach-Object { 
            if ($_) {
                Write-Host "   - $_" -ForegroundColor Gray 
                
                # Vérifier si c'est un modèle Qwen
                if ($_ -match "qwen|Qwen") {
                    Write-Host "     ✅ Modèle Qwen détecté" -ForegroundColor Green
                }
            }
        }
    } else {
        Write-Host "   ℹ️  Aucun modèle SageMaker trouvé" -ForegroundColor Gray
    }
    
    # Vérifier les endpoints SageMaker
    Write-Host "🎯 Endpoints SageMaker disponibles :" -ForegroundColor Yellow
    $endpoints = aws sagemaker list-endpoints --region $Region --query 'Endpoints[].EndpointName' --output text 2>&1
    if ($LASTEXITCODE -eq 0 -and $endpoints) {
        $endpoints.Split("`t") | ForEach-Object { 
            if ($_) {
                Write-Host "   - $_" -ForegroundColor Gray 
                
                # Obtenir le statut de l'endpoint
                $status = aws sagemaker describe-endpoint --endpoint-name $_ --region $Region --query 'EndpointStatus' --output text 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "     📊 Statut : $status" -ForegroundColor $(if ($status -eq "InService") { "Green" } else { "Yellow" })
                }
            }
        }
    } else {
        Write-Host "   ℹ️  Aucun endpoint SageMaker trouvé" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Erreur lors de la vérification des déploiements SageMaker" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 4. Vérifier les instances EC2 existantes
Write-Host "4️⃣  Vérification des instances EC2..." -ForegroundColor Green
try {
    Write-Host "🖥️  Instances EC2 en cours d'exécution :" -ForegroundColor Yellow
    $instances = aws ec2 describe-instances `
        --region $Region `
        --query 'Reservations[].Instances[?State.Name==`running`].[InstanceId, InstanceType, State.Name, Tags[?Key==`Name`].Value | [0]]' `
        --output text 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $instances) {
        $instanceLines = $instances -split "`r?`n"
        foreach ($line in $instanceLines) {
            if ($line.Trim()) {
                $parts = $line -split "`t"
                if ($parts.Count -ge 3) {
                    $instanceId = $parts[0]
                    $instanceType = $parts[1]
                    $state = $parts[2]
                    $name = if ($parts.Count -ge 4) { $parts[3] } else { "N/A" }
                    
                    Write-Host "   📍 ID : $instanceId" -ForegroundColor Gray
                    Write-Host "     🏷️  Nom : $name" -ForegroundColor Gray
                    Write-Host "     💻 Type : $instanceType" -ForegroundColor Gray
                    Write-Host "     🟢 Statut : $state" -ForegroundColor Green
                    
                    # Vérifier si c'est une instance pour Qwen
                    if ($name -match "qwen|Qwen" -or $instanceType -match "ml\.|g\.|p\.|inf\.|trn") {
                        Write-Host "     ✅ Instance compatible avec Qwen détectée" -ForegroundColor Green
                    }
                }
            }
        }
    } else {
        Write-Host "   ℹ️  Aucune instance EC2 en cours d'exécution" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Erreur lors de la vérification des instances EC2" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 5. Vérifier les images ECR
Write-Host "5️⃣  Vérification des images ECR..." -ForegroundColor Green
try {
    Write-Host "🐳 Répertoires ECR disponibles :" -ForegroundColor Yellow
    $repositories = aws ecr describe-repositories --region $Region --query 'repositories[].repositoryName' --output text 2>&1
    if ($LASTEXITCODE -eq 0 -and $repositories) {
        $repositories.Split("`t") | ForEach-Object { 
            if ($_) {
                Write-Host "   - $_" -ForegroundColor Gray 
                
                # Vérifier si c'est une image pour Qwen
                if ($_ -match "qwen|Qwen") {
                    Write-Host "     ✅ Image Qwen détectée" -ForegroundColor Green
                    
                    # Lister les tags de l'image
                    $tags = aws ecr describe-images --repository-name $_ --region $Region --query 'imageDetails[].imageTags[]' --output text 2>&1
                    if ($tags) {
                        Write-Host "     🏷️  Tags disponibles : $tags" -ForegroundColor Gray
                    }
                }
            }
        }
    } else {
        Write-Host "   ℹ️  Aucun répertoire ECR trouvé" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Erreur lors de la vérification des images ECR" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 6. Résumé de la vérification
Write-Host "📊 RÉSUMÉ DE LA VÉRIFICATION" -ForegroundColor Cyan -BackgroundColor DarkBlue
Write-Host "=" * 80

$summary = @{
    "Credentials AWS" = "✅ Valides"
    "Bucket S3" = if ($bucketExists -and $LASTEXITCODE -eq 0) { "✅ Accessible" } else { "❌ Inaccessible" }
    "Modèles SageMaker" = if ($models) { "✅ $($models.Split('`t').Count) modèle(s)" } else { "⚠️  Aucun" }
    "Endpoints SageMaker" = if ($endpoints) { "✅ $($endpoints.Split('`t').Count) endpoint(s)" } else { "⚠️  Aucun" }
    "Instances EC2" = if ($instances -and $instances.Trim()) { "✅ $($instanceLines.Count) instance(s)" } else { "⚠️  Aucune" }
    "Images ECR" = if ($repositories) { "✅ $($repositories.Split('`t').Count) répertoire(s)" } else { "⚠️  Aucune" }
}

$summary.GetEnumerator() | ForEach-Object {
    Write-Host "   $($_.Key.PadRight(25)) : $($_.Value)" -ForegroundColor $(if ($_.Value -match "✅") { "Green" } elseif ($_.Value -match "⚠️") { "Yellow" } else { "Red" })
}

Write-Host "=" * 80

# 7. Recommandations
Write-Host "🎯 RECOMMANDATIONS" -ForegroundColor Magenta
Write-Host "=" * 80

$recommendations = @(
    "🔧 Vérifier que le modèle $ModelName est bien téléchargé dans le bucket S3",
    "📦 S'assurer que les poids du modèle sont complets (environ 18 GB pour Qwen3.5 9B)",
    "🚀 Créer une image Docker avec les dépendances nécessaires",
    "📤 Pousser l'image vers ECR",
    "⚙️ Configurer un modèle SageMaker avec l'image ECR",
    "🎯 Déployer un endpoint SageMaker pour l'inférence",
    "🔍 Tester l'endpoint avec des requêtes d'inférence",
    "📊 Surveiller les performances et les coûts"
)

for ($i = 0; $i -lt $recommendations.Count; $i++) {
    Write-Host "   $($i+1). $($recommendations[$i])" -ForegroundColor Gray
}

Write-Host "=" * 80
Write-Host "✅ Vérification terminée !" -ForegroundColor Green
Write-Host "📍 Prochaines étapes : Préparer le serveur EC2 pour le déploiement" -ForegroundColor Yellow
