# Script de déploiement EC2 pour Qwen3.5-9B-DeepSeek-V4-Flash-BF16
# Auteur : Harmonic AI Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$InstanceName = "qwen35-ec2-server",
    [string]$KeyPairName = "qwen35-keypair",
    [string]$SecurityGroupName = "qwen35-security-group",
    [string]$IamRoleName = "qwen35-ec2-role",
    [string]$S3Bucket = "harmonic-ai-qwen-models",
    [string]$ModelPath = "qwen35/model.tar.gz",
    [switch]$SkipConfiguration = $false,
    [switch]$SkipModelDownload = $false,
    [switch]$SkipDeployment = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Déploiement EC2 pour Qwen3.5-9B-DeepSeek-V4-Flash-BF16..." -ForegroundColor Cyan
Write-Host "📍 Région : $Region" -ForegroundColor Yellow
Write-Host "🏷️  Nom de l'instance : $InstanceName" -ForegroundColor Yellow
Write-Host "=" * 80

# Fonction pour afficher les étapes
function Write-Step {
    param([string]$Step, [string]$Message)
    Write-Host "`n$Step $Message" -ForegroundColor Green
}

# Fonction pour exécuter une commande et vérifier le résultat
function Invoke-CheckedCommand {
    param([string]$Command, [string]$SuccessMessage, [string]$ErrorMessage)
    
    Write-Host "   ▶ Exécution : $Command" -ForegroundColor Gray
    $output = Invoke-Expression $Command 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $SuccessMessage" -ForegroundColor Green
        return $output
    } else {
        Write-Host "   ❌ $ErrorMessage" -ForegroundColor Red
        Write-Host "   📋 Sortie : $output" -ForegroundColor Gray
        throw $ErrorMessage
    }
}

# 1. Vérifier les prérequis
Write-Step "1️⃣" "Vérification des prérequis..."

try {
    # Vérifier AWS CLI
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ AWS CLI installé : $($awsVersion -split ' ')[0]" -ForegroundColor Green
    } else {
        Write-Host "   ❌ AWS CLI non installé" -ForegroundColor Red
        exit 1
    }
    
    # Vérifier les credentials AWS
    $callerIdentity = aws sts get-caller-identity --region $Region 2>&1
    if ($LASTEXITCODE -eq 0) {
        $accountId = ($callerIdentity | ConvertFrom-Json).Account
        Write-Host "   ✅ Credentials AWS valides (Compte: $accountId)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Credentials AWS invalides ou manquants" -ForegroundColor Red
        exit 1
    }
    
    # Vérifier Docker (optionnel pour EC2)
    try {
        docker version | Out-Null
        Write-Host "   ✅ Docker installé" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Docker non installé (optionnel pour EC2)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "   ❌ Erreur lors de la vérification des prérequis" -ForegroundColor Red
    exit 1
}

Write-Host "=" * 80

# 2. Configuration de l'environnement AWS (si non ignoré)
if (-not $SkipConfiguration) {
    Write-Step "2️⃣" "Configuration de l'environnement AWS..."
    
    try {
        # Vérifier/créer la paire de clés
        Write-Host "   🔑 Configuration de la paire de clés..." -ForegroundColor Gray
        $existingKeyPairs = aws ec2 describe-key-pairs --region $Region --query 'KeyPairs[].KeyName' --output text 2>&1
        
        if ($existingKeyPairs -match $KeyPairName) {
            Write-Host "   ✅ Paire de clés existante : $KeyPairName" -ForegroundColor Green
        } else {
            Write-Host "   📝 Création d'une nouvelle paire de clés..." -ForegroundColor Gray
            $keyPair = aws ec2 create-key-pair `
                --key-name $KeyPairName `
                --region $Region `
                --query 'KeyMaterial' `
                --output text
            
            # Sauvegarder la clé privée
            $keyPairPath = "$env:USERPROFILE\.ssh\$KeyPairName.pem"
            $keyPair | Out-File -FilePath $keyPairPath -Encoding ASCII
            Write-Host "   ✅ Paire de clés créée et sauvegardée : $keyPairPath" -ForegroundColor Green
        }
        
        # Vérifier/créer le groupe de sécurité
        Write-Host "   🛡️  Configuration du groupe de sécurité..." -ForegroundColor Gray
        $existingSg = aws ec2 describe-security-groups --region $Region --group-names $SecurityGroupName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $sgId = ($existingSg | ConvertFrom-Json).SecurityGroups[0].GroupId
            Write-Host "   ✅ Groupe de sécurité existant : $SecurityGroupName (ID: $sgId)" -ForegroundColor Green
        } else {
            # Obtenir le VPC par défaut
            $defaultVpc = aws ec2 describe-vpcs `
                --region $Region `
                --filters "Name=isDefault,Values=true" `
                --query 'Vpcs[0].VpcId' `
                --output text
            
            # Créer le groupe de sécurité
            $newSg = aws ec2 create-security-group `
                --group-name $SecurityGroupName `
                --description "Security group for Qwen3.5 EC2 instance" `
                --vpc-id $defaultVpc `
                --region $Region
            
            $sgId = $newSg.GroupId
            Write-Host "   ✅ Groupe de sécurité créé : $SecurityGroupName (ID: $sgId)" -ForegroundColor Green
            
            # Ajouter les règles de sécurité
            $rules = @(
                @{Protocol="tcp"; Port=22; Description="SSH"},
                @{Protocol="tcp"; Port=80; Description="HTTP"},
                @{Protocol="tcp"; Port=443; Description="HTTPS"},
                @{Protocol="tcp"; Port=8080; Description="API"},
                @{Protocol="tcp"; Port=8000; Description="API Alt"}
            )
            
            foreach ($rule in $rules) {
                aws ec2 authorize-security-group-ingress `
                    --group-id $sgId `
                    --protocol $rule.Protocol `
                    --port $rule.Port `
                    --cidr 0.0.0.0/0 `
                    --region $Region | Out-Null
                Write-Host "   🔧 Règle ajoutée : $($rule.Port) ($($rule.Description))" -ForegroundColor Gray
            }
        }
        
        # Vérifier/créer le rôle IAM
        Write-Host "   👤 Configuration du rôle IAM..." -ForegroundColor Gray
        $existingRole = aws iam get-role --role-name $IamRoleName --region $Region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $roleArn = ($existingRole | ConvertFrom-Json).Role.Arn
            Write-Host "   ✅ Rôle IAM existant : $IamRoleName (ARN: $roleArn)" -ForegroundColor Green
        } else {
            # Créer le document de confiance
            $trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
            
            $trustPolicy | Out-File -FilePath "trust-policy.json" -Encoding UTF8
            
            # Créer le rôle
            $newRole = aws iam create-role `
                --role-name $IamRoleName `
                --assume-role-policy-document file://trust-policy.json `
                --region $Region
            
            $roleArn = $newRole.Role.Arn
            Write-Host "   ✅ Rôle IAM créé : $IamRoleName (ARN: $roleArn)" -ForegroundColor Green
            
            # Attacher les politiques
            $policies = @(
                "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
                "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
                "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
            )
            
            foreach ($policy in $policies) {
                aws iam attach-role-policy `
                    --role-name $IamRoleName `
                    --policy-arn $policy `
                    --region $Region | Out-Null
                Write-Host "   🔧 Politique attachée : $($policy.Split('/')[-1])" -ForegroundColor Gray
            }
            
            # Créer le profil d'instance
            aws iam create-instance-profile `
                --instance-profile-name $IamRoleName `
                --region $Region | Out-Null
            
            aws iam add-role-to-instance-profile `
                --instance-profile-name $IamRoleName `
                --role-name $IamRoleName `
                --region $Region | Out-Null
            
            Write-Host "   ✅ Profil d'instance créé" -ForegroundColor Green
            
            # Nettoyer
            Remove-Item -Path "trust-policy.json" -Force -ErrorAction SilentlyContinue
        }
        
        Write-Host "   ✅ Configuration AWS terminée" -ForegroundColor Green
        
    } catch {
        Write-Host "   ❌ Erreur lors de la configuration AWS" -ForegroundColor Red
        Write-Host "   📋 Détails : $_" -ForegroundColor Gray
        exit 1
    }
} else {
    Write-Step "2️⃣" "Configuration AWS ignorée (SkipConfiguration activé)"
}

Write-Host "=" * 80

# 3. Téléchargement du modèle (si non ignoré)
if (-not $SkipModelDownload) {
    Write-Step "3️⃣" "Téléchargement du modèle depuis S3..."
    
    try {
        # Vérifier si le bucket S3 existe
        Write-Host "   📦 Vérification du bucket S3..." -ForegroundColor Gray
        $bucketExists = aws s3api head-bucket --bucket $S3Bucket --region $Region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Bucket S3 accessible : $S3Bucket" -ForegroundColor Green
            
            # Vérifier si le modèle existe dans S3
            Write-Host "   🔍 Recherche du modèle dans S3..." -ForegroundColor Gray
            $modelExists = aws s3 ls "s3://$S3Bucket/$ModelPath" --region $Region 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ Modèle trouvé dans S3 : $ModelPath" -ForegroundColor Green
                
                # Obtenir la taille du modèle
                $modelSize = aws s3 ls "s3://$S3Bucket/$ModelPath" --region $Region --human-readable --summarize | Select-String "Total Size"
                Write-Host "   📊 Taille du modèle : $modelSize" -ForegroundColor Gray
                
            } else {
                Write-Host "   ⚠️  Modèle non trouvé dans S3 : $ModelPath" -ForegroundColor Yellow
                Write-Host "   ℹ️  Vous devrez télécharger le modèle manuellement" -ForegroundColor Gray
            }
            
        } else {
            Write-Host "   ❌ Bucket S3 inaccessible : $S3Bucket" -ForegroundColor Red
            Write-Host "   ℹ️  Créez le bucket S3 et téléchargez-y le modèle" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "   ⚠️  Erreur lors de la vérification du modèle S3" -ForegroundColor Yellow
        Write-Host "   📋 Détails : $_" -ForegroundColor Gray
    }
} else {
    Write-Step "3️⃣" "Téléchargement du modèle ignoré (SkipModelDownload activé)"
}

Write-Host "=" * 80

# 4. Déploiement de l'instance EC2 (si non ignoré)
if (-not $SkipDeployment) {
    Write-Step "4️⃣" "Déploiement de l'instance EC2..."
    
    try {
        # Vérifier si l'instance existe déjà
        Write-Host "   🔍 Vérification des instances existantes..." -ForegroundColor Gray
        $existingInstances = aws ec2 describe-instances `
            --region $Region `
            --filters "Name=tag:Name,Values=$InstanceName" `
            --query 'Reservations[].Instances[].InstanceId' `
            --output text 2>&1
        
        if ($existingInstances) {
            Write-Host "   ⚠️  Instance existante détectée : $existingInstances" -ForegroundColor Yellow
            
            # Obtenir le statut de l'instance
            $instanceStatus = aws ec2 describe-instances `
                --region $Region `
                --instance-ids $existingInstances `
                --query 'Reservations[].Instances[].State.Name' `
                --output text
            
            Write-Host "   📊 Statut actuel : $instanceStatus" -ForegroundColor Gray
            
            if ($instanceStatus -eq "running") {
                Write-Host "   ✅ Instance déjà en cours d'exécution" -ForegroundColor Green
                
                # Obtenir l'adresse IP publique
                $publicIp = aws ec2 describe-instances `
                    --region $Region `
                    --instance-ids $existingInstances `
                    --query 'Reservations[].Instances[].PublicIpAddress' `
                    --output text
                
                Write-Host "   🌐 Adresse IP publique : $publicIp" -ForegroundColor Cyan
                
                # Passer directement au test
                $instanceId = $existingInstances
                $skipLaunch = $true
            } else {
                Write-Host "   🔄 Démarrage de l'instance existante..." -ForegroundColor Gray
                aws ec2 start-instances --instance-ids $existingInstances --region $Region | Out-Null
                $instanceId = $existingInstances
                $skipLaunch = $true
            }
        } else {
            $skipLaunch = $false
        }
        
        if (-not $skipLaunch) {
            # Créer la configuration de l'instance
            Write-Host "   📝 Création de la configuration de l'instance..." -ForegroundColor Gray
            
            $instanceConfig = @{
                ImageId = "ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS
                InstanceType = "g5.2xlarge"
                KeyName = $KeyPairName
                MinCount = 1
                MaxCount = 1
                SecurityGroupIds = @($sgId)
                IamInstanceProfile = @{Name = $IamRoleName}
                BlockDeviceMappings = @(
                    @{
                        DeviceName = "/dev/sda1"
                        Ebs = @{
                            VolumeSize = 100
                            VolumeType = "gp3"
                            DeleteOnTermination = $true
                        }
                    }
                )
                TagSpecifications = @(
                    @{
                        ResourceType = "instance"
                        Tags = @(
                            @{Key = "Name"; Value = $InstanceName},
                            @{Key = "Project"; Value = "Harmonic-AI"},
                            @{Key = "Model"; Value = "Qwen3.5-9B-DeepSeek-V4-Flash-BF16"}
                        )
                    }
                )
                UserData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(@"
#!/bin/bash
# Installation automatique pour Qwen3.5

# Mettre à jour le système
apt-get update -y
apt-get upgrade -y

# Installer les dépendances
apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    git \
    curl \
    wget \
    htop \
    nvidia-cuda-toolkit

# Configurer Python
python3.10 -m venv /opt/qwen-venv
source /opt/qwen-venv/bin/activate
pip install --upgrade pip

# Installer PyTorch avec support CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Installer les autres dépendances
pip install transformers accelerate fastapi uvicorn boto3 numpy requests pydantic

# Créer la structure de répertoires
mkdir -p /opt/qwen35/{app,model,logs}

# Créer le fichier de configuration
cat > /opt/qwen35/config.json << 'EOF'
{
  "model_name": "Qwen3.5-9B-DeepSeek-V4-Flash-BF16",
  "model_path": "/opt/qwen35/model",
  "api_port": 8080,
  "max_sequence_length": 4096,
  "device": "cuda"
}
EOF

# Créer le script de démarrage
cat > /opt/qwen35/start_api.sh << 'EOF'
#!/bin/bash
source /opt/qwen-venv/bin/activate
cd /opt/qwen35

# Télécharger le modèle depuis S3 si nécessaire
if [ ! -f "/opt/qwen35/model/config.json" ]; then
    echo "Téléchargement du modèle depuis S3..."
    aws s3 cp s3://$S3Bucket/$ModelPath /tmp/model.tar.gz
    tar -xzf /tmp/model.tar.gz -C /opt/qwen35/model/
    rm /tmp/model.tar.gz
fi

# Démarrer l'API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
EOF

chmod +x /opt/qwen35/start_api.sh

# Créer un service systemd
cat > /etc/systemd/system/qwen35.service << 'EOF'
[Unit]
Description=Qwen3.5 API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/qwen35
ExecStart=/opt/qwen35/start_api.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PYTHONPATH=/opt/qwen35"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable qwen35.service
systemctl start qwen35.service

echo "✅ Installation terminée. Qwen3.5 API démarrée sur le port 8080."
"@))
            }
            
            # Sauvegarder la configuration
            $instanceConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "launch-config.json" -Encoding UTF8
            
            # Lancer l'instance
            Write-Host "   🚀 Lancement de l'instance EC2..." -ForegroundColor Gray
            $launchResult = aws ec2 run-instances `
                --cli-input-json file://launch-config.json `
                --region $Region
            
            $instanceId = $launchResult.Instances[0].InstanceId
            Write-Host "   ✅ Instance lancée : $instanceId" -ForegroundColor Green
            
            # Nettoyer
            Remove-Item -Path "launch-config.json" -Force -ErrorAction SilentlyContinue
        }
        
        # Attendre que l'instance soit en cours d'exécution
        Write-Host "   ⏳ Attente du démarrage de l'instance..." -ForegroundColor Gray
        aws ec2 wait instance-running --instance-ids $instanceId --region $Region
        
        # Obtenir les détails de l'instance
        Write-Host "   📋 Récupération des détails de l'instance..." -ForegroundColor Gray
        $instanceDetails = aws ec2 describe-instances `
            --instance-ids $instanceId `
            --region $Region `
            --query 'Reservations[].Instances[0]'
        
        $publicIp = $instanceDetails.PublicIpAddress
        $privateIp = $instanceDetails.PrivateIpAddress
        $instanceType = $instanceDetails.InstanceType
        $state = $instanceDetails.State.Name
        
        Write-Host "   ✅ Instance prête :" -ForegroundColor Green
        Write-Host "      🌐 IP Publique : $publicIp" -ForegroundColor Cyan
        Write-Host "      🔒 IP Privée : $privateIp" -ForegroundColor Gray
        Write-Host "      💻 Type : $instanceType" -ForegroundColor Gray
        Write-Host "      🟢 Statut : $state" -ForegroundColor Green
        
        # Attendre que le service soit prêt (environ 2 minutes)
        Write-Host "   ⏳ Attente de l'initialisation du service (2 minutes)..." -ForegroundColor Gray
        Start-Sleep -Seconds 120
        
    } catch {
        Write-Host "   ❌ Erreur lors du déploiement EC2" -ForegroundColor Red
        Write-Host "   📋 Détails : $_" -ForegroundColor Gray
        exit 1
    }
} else {
    Write-Step "4️⃣" "Déploiement EC2 ignoré (SkipDeployment activé)"
}

Write-Host "=" * 80

# 5. Test du déploiement
Write-Step "5️⃣" "Test du déploiement..."
try {
    if ($publicIp) {
        Write-Host "   🧪 Test de l'API Qwen3.5..." -ForegroundColor Gray
        
        # Test de santé
        Write-Host "   🔍 Test de santé (health check)..." -ForegroundColor Gray
        $healthUrl = "http://$publicIp`:8080/health"
        
        try {
            $healthResponse = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 30
            Write-Host "   ✅ Health check réussi : $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Health check échoué : $_" -ForegroundColor Yellow
            Write-Host "   ℹ️  Le service peut mettre plus de temps à démarrer" -ForegroundColor Gray
        }
        
        # Test de génération de texte
        Write-Host "   📝 Test de génération de texte..." -ForegroundColor Gray
        $generateUrl = "http://$publicIp`:8080/generate"
        $testPrompt = @{
            prompt = "Bonjour, comment ça va?"
            max_length = 50
            temperature = 0.7
        } | ConvertTo-Json
        
        try {
            $generateResponse = Invoke-RestMethod -Uri $generateUrl -Method Post -Body $testPrompt -ContentType "application/json" -TimeoutSec 60
            Write-Host "   ✅ Génération de texte réussie !" -ForegroundColor Green
            Write-Host "   📋 Réponse : $($generateResponse.generated_text)" -ForegroundColor Gray
        } catch {
            Write-Host "   ⚠️  Génération de texte échouée : $_" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "   ℹ️  Aucune IP publique disponible pour les tests" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "   ⚠️  Erreur lors des tests" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 6. Résumé final
Write-Step "📊" "RÉSUMÉ DU DÉPLOIEMENT"
Write-Host "=" * 80

$deploymentSummary = @{
    "Statut" = "✅ Déploiement terminé"
    "Région AWS" = $Region
    "ID de l'instance" = $instanceId
    "Nom de l'instance" = $InstanceName
    "Type d'instance" = $instanceType
    "IP Publique" = if ($publicIp) { $publicIp } else { "N/A" }
    "IP Privée" = if ($privateIp) { $privateIp } else { "N/A" }
    "Groupe de sécurité" = $SecurityGroupName
    "Rôle IAM" = $IamRoleName
    "Bucket S3" = $S3Bucket
    "Port API" = "8080"
}

$deploymentSummary.GetEnumerator() | ForEach-Object {
    Write-Host "   $($_.Key.PadRight(25)) : $($_.Value)" -ForegroundColor Gray
}

Write-Host "=" * 80

# 7. Instructions de connexion
Write-Step "🔗" "INSTRUCTIONS DE CONNEXION"
Write-Host "=" * 80

if ($publicIp -and $KeyPairName) {
    $keyPairPath = "$env:USERPROFILE\.ssh\$KeyPairName.pem"
    
    $connectionInstructions = @(
        "1. Se connecter via SSH :",
        "   ssh -i `"$keyPairPath`" ubuntu@$publicIp",
        "",
        "2. Vérifier le statut du service :",
        "   sudo systemctl status qwen35.service",
        "",
        "3. Voir les logs du service :",
        "   sudo journalctl -u qwen35.service -f",
        "",
        "4. Tester l'API localement :",
        "   curl http://localhost:8080/health",
        "",
        "5. Tester l'API depuis l'extérieur :",
        "   curl http://$publicIp`:8080/health",
        "",
        "6. Arrêter le service :",
        "   sudo systemctl stop qwen35.service",
        "",
        "7. Redémarrer le service :",
        "   sudo systemctl restart qwen35.service"
    )
    
    foreach ($instruction in $connectionInstructions) {
        Write-Host "   $instruction" -ForegroundColor Gray
    }
} else {
    Write-Host "   ℹ️  Instructions de connexion non disponibles" -ForegroundColor Gray
}

Write-Host "=" * 80
Write-Host "🎉 Déploiement EC2 pour Qwen3.5-9B-DeepSeek-V4-Flash-BF16 terminé avec succès !" -ForegroundColor Green
Write-Host "📍 Prochaines étapes : Configurer la surveillance et l'optimisation" -ForegroundColor Yellow