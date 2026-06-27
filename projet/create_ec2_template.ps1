# Script simple pour créer un template EC2 pour Qwen3.5
# Auteur : Harmonic AI Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$TemplateName = "qwen35-prod-template",
    [string]$OutputFile = "ec2-template.json"
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 Création d'un template EC2 pour Qwen3.5..." -ForegroundColor Cyan
Write-Host "📍 Région : $Region" -ForegroundColor Yellow
Write-Host "🏷️  Nom du template : $TemplateName" -ForegroundColor Yellow
Write-Host "=" * 80

# Vérifier les credentials AWS
try {
    $callerIdentity = aws sts get-caller-identity --region $Region 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Credentials AWS valides" -ForegroundColor Green
    } else {
        Write-Host "❌ Credentials AWS invalides ou manquants" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erreur lors de la vérification des credentials AWS" -ForegroundColor Red
    exit 1
}

# Définir le user data (script bash simple)
$userDataScript = @'
#!/bin/bash
# Installation automatique pour Qwen3.5

# Mettre à jour le système
apt-get update -y
apt-get upgrade -y

# Installer les dépendances de base
apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    git \
    curl \
    wget \
    htop \
    nvtop \
    nvidia-cuda-toolkit

# Configurer Python
python3.10 -m venv /opt/qwen-venv
source /opt/qwen-venv/bin/activate
pip install --upgrade pip

# Installer PyTorch avec CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Installer les autres dépendances
pip install transformers accelerate fastapi uvicorn boto3 numpy requests pydantic

# Créer la structure de répertoires
mkdir -p /opt/qwen35/{app,model,logs}

# Créer un service systemd simple
cat > /etc/systemd/system/qwen35.service << 'EOF'
[Unit]
Description=Qwen3.5 API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/qwen35
ExecStart=/opt/qwen-venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
Environment="PYTHONPATH=/opt/qwen35"
Environment="MODEL_PATH=/opt/qwen35/model"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable qwen35.service

echo "✅ Installation terminée. Redémarrage dans 30 secondes..."
sleep 30
reboot
'@

# Encoder le user data en base64
$encodedUserData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($userDataScript))

# Créer le template EC2
$ec2Template = @{
    LaunchTemplateName = $TemplateName
    VersionDescription = "Version 1.0 - Template pour Qwen3.5"
    LaunchTemplateData = @{
        ImageId = "ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS
        InstanceType = "g5.2xlarge"
        KeyName = "qwen35-keypair"
        SecurityGroupIds = @("sg-qwen35-prod")
        IamInstanceProfile = @{
            Arn = "arn:aws:iam::326095712935:instance-profile/qwen35-ec2-role"
        }
        BlockDeviceMappings = @(
            @{
                DeviceName = "/dev/sda1"
                Ebs = @{
                    VolumeSize = 100
                    VolumeType = "gp3"
                    DeleteOnTermination = $true
                }
            }
            @{
                DeviceName = "/dev/sdb"
                Ebs = @{
                    VolumeSize = 500
                    VolumeType = "gp3"
                    DeleteOnTermination = $true
                }
            }
        )
        TagSpecifications = @(
            @{
                ResourceType = "instance"
                Tags = @(
                    @{Key = "Name"; Value = "qwen35-production-instance"}
                    @{Key = "Environment"; Value = "Production"}
                    @{Key = "Project"; Value = "Harmonic-AI"}
                    @{Key = "Model"; Value = "Qwen3.5-9B-DeepSeek-V4-Flash-BF16"}
                    @{Key = "ManagedBy"; Value = "PowerShell Script"}
                )
            }
        )
        UserData = $encodedUserData
    }
}

# Sauvegarder le template dans un fichier JSON
$ec2Template | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "✅ Template EC2 créé avec succès !" -ForegroundColor Green
Write-Host "📁 Fichier : $OutputFile" -ForegroundColor Cyan

# Afficher un résumé du template
Write-Host "`n📊 RÉSUMÉ DU TEMPLATE :" -ForegroundColor Yellow
Write-Host "=" * 80

$summary = @{
    "Nom du template" = $TemplateName
    "Région" = $Region
    "Type d'instance" = "g5.2xlarge"
    "GPU" = "NVIDIA A10G (24GB VRAM)"
    "AMI" = "Ubuntu 22.04 LTS"
    "Stockage système" = "100 GB (gp3)"
    "Stockage données" = "500 GB (gp3)"
    "Groupe de sécurité" = "sg-qwen35-prod"
    "Rôle IAM" = "qwen35-ec2-role"
    "Ports ouverts" = "22 (SSH), 80 (HTTP), 443 (HTTPS), 8080 (API)"
}

$summary.GetEnumerator() | ForEach-Object {
    Write-Host "   $($_.Key.PadRight(25)) : $($_.Value)" -ForegroundColor Gray
}

# Instructions pour utiliser le template
Write-Host "`n🚀 INSTRUCTIONS POUR UTILISER LE TEMPLATE :" -ForegroundColor Magenta
Write-Host "=" * 80

$instructions = @(
    "1. Vérifier que les ressources AWS existent :",
    "   - Paire de clés : qwen35-keypair",
    "   - Groupe de sécurité : sg-qwen35-prod",
    "   - Rôle IAM : qwen35-ec2-role",
    "",
    "2. Créer le template de lancement :",
    "   aws ec2 create-launch-template --cli-input-json file://$OutputFile --region $Region",
    "",
    "3. Lancer une instance EC2 :",
    "   aws ec2 run-instances --launch-template LaunchTemplateName=$TemplateName --count 1 --region $Region",
    "",
    "4. Récupérer l'adresse IP publique :",
    "   aws ec2 describe-instances --filters 'Name=tag:Name,Values=qwen35-production-instance' --query 'Reservations[].Instances[].PublicIpAddress' --output text --region $Region",
    "",
    "5. Se connecter via SSH :",
    "   ssh -i ~/.ssh/qwen35-keypair.pem ubuntu@<IP_PUBLIQUE>",
    "",
    "6. Tester l'API Qwen3.5 :",
    "   curl http://localhost:8080/health"
)

foreach ($instruction in $instructions) {
    Write-Host "   $instruction" -ForegroundColor Gray
}

Write-Host "=" * 80
Write-Host "🎉 Template EC2 prêt pour le déploiement de Qwen3.5 !" -ForegroundColor Green