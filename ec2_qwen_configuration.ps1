# Configuration du serveur EC2 pour Qwen3.5-9B-DeepSeek-V4-Flash-BF16
# Auteur : Harmonic AI Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$InstanceName = "qwen35-ec2-server",
    [string]$KeyPairName = "qwen35-keypair",
    [string]$SecurityGroupName = "qwen35-security-group",
    [string]$VpcId = "",
    [string]$SubnetId = "",
    [string]$IamRoleName = "qwen35-ec2-role"
)

$ErrorActionPreference = "Stop"

Write-Host "⚙️  Configuration du serveur EC2 pour Qwen3.5-9B-DeepSeek-V4-Flash-BF16..." -ForegroundColor Cyan
Write-Host "📍 Région : $Region" -ForegroundColor Yellow
Write-Host "🏷️  Nom de l'instance : $InstanceName" -ForegroundColor Yellow
Write-Host "=" * 80

# 1. Vérifier les credentials AWS
Write-Host "1️⃣  Vérification des credentials AWS..." -ForegroundColor Green
try {
    $callerIdentity = aws sts get-caller-identity --region $Region 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Credentials AWS valides" -ForegroundColor Green
        $accountId = ($callerIdentity | ConvertFrom-Json).Account
        Write-Host "   📊 Compte AWS : $accountId" -ForegroundColor Gray
    } else {
        Write-Host "❌ Credentials AWS invalides ou manquants" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erreur lors de la vérification des credentials AWS" -ForegroundColor Red
    exit 1
}

Write-Host "=" * 80

# 2. Créer ou vérifier la paire de clés
Write-Host "2️⃣  Configuration de la paire de clés..." -ForegroundColor Green
$keyPairPath = "$env:USERPROFILE\.ssh\$KeyPairName.pem"
try {
    # Vérifier si la paire de clés existe déjà
    $existingKeyPairs = aws ec2 describe-key-pairs --region $Region --query 'KeyPairs[].KeyName' --output text 2>&1
    if ($existingKeyPairs -match $KeyPairName) {
        Write-Host "✅ Paire de clés existante : $KeyPairName" -ForegroundColor Green
        
        # Vérifier si le fichier PEM existe localement
        if (Test-Path $keyPairPath) {
            Write-Host "   📁 Fichier PEM local trouvé : $keyPairPath" -ForegroundColor Gray
        } else {
            Write-Host "⚠️  Fichier PEM local non trouvé. Vous devrez télécharger la clé depuis AWS Console." -ForegroundColor Yellow
        }
    } else {
        Write-Host "🔑 Création d'une nouvelle paire de clés..." -ForegroundColor Yellow
        $keyPair = aws ec2 create-key-pair `
            --key-name $KeyPairName `
            --region $Region `
            --query 'KeyMaterial' `
            --output text 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # Sauvegarder la clé privée
            $keyPair | Out-File -FilePath $keyPairPath -Encoding ASCII
            Write-Host "✅ Paire de clés créée : $KeyPairName" -ForegroundColor Green
            Write-Host "   📁 Clé privée sauvegardée : $keyPairPath" -ForegroundColor Gray
            
            # Sécuriser les permissions du fichier (sur Linux/macOS)
            if ($IsLinux -or $IsMacOS) {
                chmod 400 $keyPairPath
            }
        } else {
            Write-Host "❌ Erreur lors de la création de la paire de clés" -ForegroundColor Red
            Write-Host "   Message : $keyPair" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "⚠️  Erreur lors de la configuration de la paire de clés" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 3. Créer ou vérifier le groupe de sécurité
Write-Host "3️⃣  Configuration du groupe de sécurité..." -ForegroundColor Green
try {
    # Vérifier si le groupe de sécurité existe déjà
    $existingSg = aws ec2 describe-security-groups `
        --region $Region `
        --group-names $SecurityGroupName 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $sgId = ($existingSg | ConvertFrom-Json).SecurityGroups[0].GroupId
        Write-Host "✅ Groupe de sécurité existant : $SecurityGroupName (ID: $sgId)" -ForegroundColor Green
    } else {
        Write-Host "🛡️  Création d'un nouveau groupe de sécurité..." -ForegroundColor Yellow
        
        # Si VpcId n'est pas spécifié, obtenir le VPC par défaut
        if ([string]::IsNullOrEmpty($VpcId)) {
            $defaultVpc = aws ec2 describe-vpcs `
                --region $Region `
                --filters "Name=isDefault,Values=true" `
                --query 'Vpcs[0].VpcId' `
                --output text 2>&1
            
            if ($LASTEXITCODE -eq 0 -and $defaultVpc) {
                $VpcId = $defaultVpc
                Write-Host "   📍 VPC par défaut détecté : $VpcId" -ForegroundColor Gray
            } else {
                Write-Host "❌ Impossible de trouver un VPC par défaut" -ForegroundColor Red
                exit 1
            }
        }
        
        # Créer le groupe de sécurité
        $newSg = aws ec2 create-security-group `
            --group-name $SecurityGroupName `
            --description "Security group for Qwen3.5 EC2 instance" `
            --vpc-id $VpcId `
            --region $Region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $sgId = ($newSg | ConvertFrom-Json).GroupId
            Write-Host "✅ Groupe de sécurité créé : $SecurityGroupName (ID: $sgId)" -ForegroundColor Green
            
            # Ajouter les règles de sécurité
            Write-Host "   🔧 Configuration des règles de sécurité..." -ForegroundColor Gray
            
            # SSH (port 22)
            aws ec2 authorize-security-group-ingress `
                --group-id $sgId `
                --protocol tcp `
                --port 22 `
                --cidr 0.0.0.0/0 `
                --region $Region | Out-Null
            
            # HTTP (port 80)
            aws ec2 authorize-security-group-ingress `
                --group-id $sgId `
                --protocol tcp `
                --port 80 `
                --cidr 0.0.0.0/0 `
                --region $Region | Out-Null
            
            # HTTPS (port 443)
            aws ec2 authorize-security-group-ingress `
                --group-id $sgId `
                --protocol tcp `
                --port 443 `
                --cidr 0.0.0.0/0 `
                --region $Region | Out-Null
            
            # API port (8080)
            aws ec2 authorize-security-group-ingress `
                --group-id $sgId `
                --protocol tcp `
                --port 8080 `
                --cidr 0.0.0.0/0 `
                --region $Region | Out-Null
            
            # API port (8000)
            aws ec2 authorize-security-group-ingress `
                --group-id $sgId `
                --protocol tcp `
                --port 8000 `
                --cidr 0.0.0.0/0 `
                --region $Region | Out-Null
            
            Write-Host "   ✅ Règles de sécurité configurées" -ForegroundColor Green
        } else {
            Write-Host "❌ Erreur lors de la création du groupe de sécurité" -ForegroundColor Red
            Write-Host "   Message : $newSg" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "⚠️  Erreur lors de la configuration du groupe de sécurité" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 4. Créer ou vérifier le rôle IAM
Write-Host "4️⃣  Configuration du rôle IAM..." -ForegroundColor Green
try {
    # Vérifier si le rôle existe déjà
    $existingRole = aws iam get-role --role-name $IamRoleName --region $Region 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $roleArn = ($existingRole | ConvertFrom-Json).Role.Arn
        Write-Host "✅ Rôle IAM existant : $IamRoleName (ARN: $roleArn)" -ForegroundColor Green
    } else {
        Write-Host "👤 Création d'un nouveau rôle IAM..." -ForegroundColor Yellow
        
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
            --region $Region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $roleArn = ($newRole | ConvertFrom-Json).Role.Arn
            Write-Host "✅ Rôle IAM créé : $IamRoleName (ARN: $roleArn)" -ForegroundColor Green
            
            # Attacher les politiques nécessaires
            Write-Host "   🔧 Attachement des politiques IAM..." -ForegroundColor Gray
            
            # AmazonS3ReadOnlyAccess pour lire les modèles depuis S3
            aws iam attach-role-policy `
                --role-name $IamRoleName `
                --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess `
                --region $Region | Out-Null
            
            # AmazonEC2ContainerRegistryReadOnly pour lire les images ECR
            aws iam attach-role-policy `
                --role-name $IamRoleName `
                --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly `
                --region $Region | Out-Null
            
            # CloudWatchAgentServerPolicy pour la surveillance
            aws iam attach-role-policy `
                --role-name $IamRoleName `
                --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy `
                --region $Region | Out-Null
            
            Write-Host "   ✅ Politiques IAM attachées" -ForegroundColor Green
            
            # Créer le profil d'instance
            aws iam create-instance-profile `
                --instance-profile-name $IamRoleName `
                --region $Region | Out-Null
            
            aws iam add-role-to-instance-profile `
                --instance-profile-name $IamRoleName `
                --role-name $IamRoleName `
                --region $Region | Out-Null
            
            Write-Host "   ✅ Profil d'instance créé" -ForegroundColor Green
            
            # Nettoyer le fichier temporaire
            Remove-Item -Path "trust-policy.json" -Force -ErrorAction SilentlyContinue
        } else {
            Write-Host "❌ Erreur lors de la création du rôle IAM" -ForegroundColor Red
            Write-Host "   Message : $newRole" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "⚠️  Erreur lors de la configuration du rôle IAM" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 5. Configuration de l'instance EC2
Write-Host "5️⃣  Configuration de l'instance EC2..." -ForegroundColor Green

# Définir les paramètres de l'instance
$instanceConfig = @{
    # Instance type optimisée pour l'inférence LLM
    InstanceType = "g5.2xlarge"  # GPU NVIDIA A10G avec 24GB VRAM
    
    # AMI Ubuntu 22.04 avec support GPU
    ImageId = "ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS en us-east-1
    
    # Stockage
    BlockDeviceMappings = @(
        @{
            DeviceName = "/dev/sda1"
            Ebs = @{
                VolumeSize = 100  # 100 GB pour le système
                VolumeType = "gp3"
                DeleteOnTermination = $true
            }
        },
        @{
            DeviceName = "/dev/sdb"
            Ebs = @{
                VolumeSize = 500  # 500 GB pour les données et modèles
                VolumeType = "gp3"
                DeleteOnTermination = $true
            }
        }
    )
    
    # Tags
    TagSpecifications = @(
        @{
            ResourceType = "instance"
            Tags = @(
                @{Key = "Name"; Value = $InstanceName},
                @{Key = "Project"; Value = "Harmonic-AI"},
                @{Key = "Model"; Value = "Qwen3.5-9B-DeepSeek-V4-Flash-BF16"},
                @{Key = "Environment"; Value = "Production"}
            )
        }
    )
    
    # Configuration réseau
    NetworkInterfaces = @(
        @{
            DeviceIndex = 0
            AssociatePublicIpAddress = $true
            Groups = @($sgId)
            DeleteOnTermination = $true
        }
    )
    
    # IAM Instance Profile
    IamInstanceProfile = @{
        Name = $IamRoleName
    }
    
    # User data pour l'installation automatique
    UserData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(@"
#!/bin/bash
# User data script for Qwen3.5 EC2 instance

# Mettre à jour le système
apt-get update -y
apt-get upgrade -y

# Installer les dépendances système
apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    git \
    curl \
    wget \
    htop \
    nvtop \
    nvidia-cuda-toolkit \
    docker.io \
    docker-compose

# Configurer Docker pour l'utilisateur courant
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

# Créer un environnement virtuel Python
python3.10 -m venv /opt/qwen-venv
source /opt/qwen-venv/bin/activate

# Installer les dépendances Python
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers accelerate fastapi uvicorn boto3 numpy requests pydantic

# Créer la structure de répertoires
mkdir -p /opt/qwen35/{app,model,logs,data}

# Télécharger le script de démarrage
cat > /opt/qwen35/start.sh << 'EOF'
#!/bin/bash
source /opt/qwen-venv/bin/activate
cd /opt/qwen35
python app/main.py
EOF

chmod +x /opt/qwen35/start.sh

# Créer un service systemd
cat > /etc/systemd/system/qwen35.service << 'EOF'
[Unit]
Description=Qwen3.5 API Service
After=network.target docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/qwen35
ExecStart=/opt/qwen35/start.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PYTHONPATH=/opt/qwen35"
Environment="MODEL_PATH=/opt/qwen35/model"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable qwen35.service

# Configurer CloudWatch Agent
curl -O https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb

# Redémarrer pour appliquer les changements
echo "Installation terminée. Redémarrage dans 30 secondes..."
sleep 30
reboot
"@))
}

# Afficher la configuration
Write-Host "📋 Configuration de l'instance EC2 :" -ForegroundColor Yellow
$instanceConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "ec2-instance-config.json" -Encoding UTF8
Get-Content "ec2-instance-config.json" | Write-Host -ForegroundColor Gray

Write-Host "=" * 80

# 6. Résumé de la configuration
Write-Host "📊 RÉSUMÉ DE LA CONFIGURATION EC2" -ForegroundColor Cyan -BackgroundColor DarkBlue
Write-Host "=" * 80

$summary = @{
    "Région AWS" = $Region
    "Nom de l'instance" = $InstanceName
    "Type d'instance" = $instanceConfig.InstanceType
    "GPU" = "NVIDIA A10G (24GB VRAM)"
    "Stockage système" = "100 GB (gp3)"
    "Stockage données" = "500 GB (gp3)"
    "Système d'exploitation" = "Ubuntu 22.04 LTS"
    "Paire de clés" = $KeyPairName
    "Groupe de sécurité" = "$SecurityGroupName (ID: $sgId)"
    "Rôle IAM" = $IamRoleName
    "Ports ouverts" = "22 (SSH), 80 (HTTP), 443 (HTTPS), 8080, 8000 (API)"
}

$summary.GetEnumerator() | ForEach-Object {
    Write-Host "   $($_.Key.PadRight(25)) : $($_.Value)" -ForegroundColor Gray
}

Write-Host "=" * 80

# 7. Instructions pour le lancement
Write-Host "🚀 INSTRUCTIONS POUR LANCER L'INSTANCE EC2" -ForegroundColor Magenta
Write-Host "=" * 80

$instructions = @(
    "1. Vérifier que la configuration est correcte dans 'ec2-instance-config.json'",
    "2. Lancer l'instance avec la commande :",
    "   aws ec2 run-instances --cli-input-json file://ec2-instance-config.json --region $Region",
    "3. Attendre que l'instance soit en état 'running'",
    "4. Récupérer l'adresse IP publique de l'instance",
    "5. Se connecter via SSH : ssh -i $keyPairPath ubuntu@<IP_PUBLIQUE>",
    "6. Vérifier l'installation avec : systemctl status qwen35.service",
    "7. Tester l'API : curl http://<IP_PUBLIQUE>:8080/health"
)

for ($i = 0; $i -lt $instructions.Count; $i++) {
    Write-Host "   $($instructions[$i])" -ForegroundColor Gray
}

Write-Host "=" * 80
Write-Host "✅ Configuration EC2 terminée !" -ForegroundColor Green
Write-Host "📍 Prochaines étapes : Préparer les scripts de déploiement" -ForegroundColor Yellow

# Nettoyage
Remove-Item -Path "ec2-instance-config.json" -Force -ErrorAction SilentlyContinue