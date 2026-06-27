# Script de génération des templates de lancement EC2 pour Qwen3.5 (Version corrigée)
# Auteur : Harmonic AI Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$TemplateName = "production_medium",
    [string]$OutputFile = "ec2-launch-template.json",
    [switch]$ListTemplates = $false,
    [switch]$GenerateAll = $false
)

$ErrorActionPreference = "Stop"

Write-Host "📋 Génération des templates de lancement EC2 pour Qwen3.5..." -ForegroundColor Cyan
Write-Host "📍 Région : $Region" -ForegroundColor Yellow
Write-Host "🏷️  Template : $TemplateName" -ForegroundColor Yellow
Write-Host "=" * 80

# Définir les templates disponibles avec syntaxe PowerShell correcte
$templates = @{
    "development" = @{
        Name = "qwen35-dev-template"
        Description = "Template de développement pour Qwen3.5"
        InstanceType = "g5.xlarge"
        ImageId = "ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS
        KeyName = "qwen35-keypair"
        SecurityGroupIds = @("sg-qwen35-dev")
        IamInstanceProfile = @{Arn = "arn:aws:iam::326095712935:instance-profile/qwen35-ec2-role"}
        BlockDeviceMappings = @(
            @{
                DeviceName = "/dev/sda1"
                Ebs = @{
                    VolumeSize = 50
                    VolumeType = "gp3"
                    DeleteOnTermination = $true
                }
            }
            @{
                DeviceName = "/dev/sdb"
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
                    @{Key = "Name"; Value = "qwen35-dev-instance"}
                    @{Key = "Environment"; Value = "Development"}
                    @{Key = "Project"; Value = "Harmonic-AI"}
                    @{Key = "Model"; Value = "Qwen3.5-9B-DeepSeek-V4-Flash-BF16"}
                )
            }
        )
        UserData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(@"
#!/bin/bash
# Script d'installation pour développement

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
    nvtop

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

echo "✅ Installation de développement terminée"
"@))
    }
    
    "production_small" = @{
        Name = "qwen35-prod-small-template"
        Description = "Template de production petite taille pour Qwen3.5"
        InstanceType = "g5.2xlarge"
        ImageId = "ami-0c55b159cbfafe1f0"
        KeyName = "qwen35-keypair"
        SecurityGroupIds = @("sg-qwen35-prod")
        IamInstanceProfile = @{Arn = "arn:aws:iam::326095712935:instance-profile/qwen35-ec2-role"}
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
                    @{Key = "Name"; Value = "qwen35-prod-small-instance"}
                    @{Key = "Environment"; Value = "Production"}
                    @{Key = "Project"; Value = "Harmonic-AI"}
                    @{Key = "Model"; Value = "Qwen3.5-9B-DeepSeek-V4-Flash-BF16"}
                    @{Key = "CostCenter"; Value = "AI-Research"}
                )
            }
        )
        UserData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(@"
#!/bin/bash
# Script d'installation pour production petite taille

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

# Configurer Docker
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

# Configurer Python
python3.10 -m venv /opt/qwen-venv
source /opt/qwen-venv/bin/activate
pip install --upgrade pip

# Installer PyTorch avec CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Installer les autres dépendances
pip install transformers accelerate fastapi uvicorn boto3 numpy requests pydantic

# Créer la structure de répertoires
mkdir -p /opt/qwen35/{app,model,logs,config}

# Télécharger le script de démarrage
cat > /opt/qwen35/start_api.sh << 'EOF'
#!/bin/bash
source /opt/qwen-venv/bin/activate
cd /opt/qwen35

# Vérifier si le modèle est déjà téléchargé
if [ ! -f "/opt/qwen35/model/config.json" ]; then
    echo "📥 Téléchargement du modèle depuis S3..."
    aws s3 cp s3://harmonic-ai-qwen-models/qwen35/model.tar.gz /tmp/model.tar.gz
    tar -xzf /tmp/model.tar.gz -C /opt/qwen35/model/
    rm /tmp/model.tar.gz
    echo "✅ Modèle téléchargé et extrait"
fi

# Démarrer l'API
echo "🚀 Démarrage de l'API Qwen3.5..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 2
EOF

chmod +x /opt/qwen35/start_api.sh

# Créer un service systemd
cat > /etc/systemd/system/qwen35.service << 'EOF'
[Unit]
Description=Qwen3.5 API Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/qwen35
ExecStart=/opt/qwen35/start_api.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PYTHONPATH=/opt/qwen35"
Environment="MODEL_PATH=/opt/qwen35/model"
Environment="AWS_REGION=us-east-1"

# Limites de ressources
LimitNOFILE=65536
LimitNPROC=65536

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable qwen35.service

# Installer et configurer CloudWatch Agent
curl -O https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb

# Créer la configuration CloudWatch
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "metrics": {
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["/", "/dev/sdb"]
      },
      "nvidia_gpu": {
        "measurement": ["utilization_gpu", "utilization_memory", "memory_used", "memory_total"],
        "metrics_collection_interval": 60
      }
    },
    "append_dimensions": {
      "InstanceId": "$${aws:InstanceId}",
      "InstanceType": "$${aws:InstanceType}",
      "AutoScalingGroupName": "$${aws:AutoScalingGroupName}"
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/qwen35/logs/api.log",
            "log_group_name": "/aws/ec2/qwen35/api",
            "log_stream_name": "$${instance_id}"
          },
          {
            "file_path": "/var/log/syslog",
            "log_group_name": "/aws/ec2/qwen35/system",
            "log_stream_name": "$${instance_id}"
          }
        ]
      }
    }
  }
}
EOF

# Démarrer CloudWatch Agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazoncloudwatch-agent/etc/amazon-cloudwatch-agent.json

echo "✅ Installation de production terminée. Redémarrage dans 30 secondes..."
sleep 30
reboot
"@))
    }
    
    "production_medium" = @{
        Name = "qwen35-prod-medium-template"
        Description = "Template de production taille moyenne pour Qwen3.5"
        InstanceType = "g5.4xlarge"
        ImageId = "ami-0c55b159cbfafe1f0"
        KeyName = "qwen35-keypair"
        SecurityGroupIds = @("sg-qwen35-prod")
        IamInstanceProfile = @{Arn = "arn:aws:iam::326095712935:instance-profile/qwen35-ec2-role"}
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
                    VolumeSize = 1000
                    VolumeType = "gp3"
                    DeleteOnTermination = $true
                }
            }
            @{
                DeviceName = "/dev/sdc"
                Ebs = @{
                    VolumeSize = 500
                    VolumeType = "io2"
                    Iops = 16000
                    DeleteOnTermination = $true
                }
            }
        )
        TagSpecifications = @(
            @{
                ResourceType = "instance"
                Tags = @(
                    @{Key = "Name"; Value = "qwen35-prod-medium-instance"}
                    @{Key = "Environment"; Value = "Production"}
                    @{Key = "Project"; Value = "Harmonic-AI"}
                    @{Key = "Model"; Value = "Qwen3.5-9B-DeepSeek-V4-Flash-BF16"}
                    @{Key = "CostCenter"; Value = "AI-Research"}
                    @{Key = "AutoScaling"; Value = "Enabled"}
                )
            }
        )
        UserData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(@"
#!/bin/bash
# Script d'installation pour production taille moyenne

apt-get update -y
apt-get upgrade -y

# Installer les dépendances système complètes
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
    nvidia-docker2 \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx

# Configurer Docker avec NVIDIA
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update
apt-get install -y nvidia-docker2
systemctl restart docker

# Configurer l'utilisateur Docker
usermod -aG docker ubuntu

# Configurer Python
python3.10 -m venv /opt/qwen-venv
source /opt/qwen-venv/bin/activate
pip install --upgrade pip

# Installer PyTorch avec CUDA optimisé
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install xformers

# Installer les autres dépendances
pip install transformers>=4.35.0 \
    accelerate>=0.24.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    boto3>=1.28.0 \
    numpy>=1.24.0 \
    requests>=2.31.0 \
    pydantic>=2.4.0 \
    python-multipart \
    redis \
    pymongo

# Créer la structure de répertoires
mkdir -p /opt/qwen35/{app,model,logs,config,cache,data}
chown -R ubuntu:ubuntu /opt/qwen35

# Configurer NGINX comme reverse proxy
cat > /etc/nginx/sites-available/qwen35 << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer sizes
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8080/health;
    }
}
EOF

ln -sf /etc/nginx/sites-available/qwen35 /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Créer le script de démarrage optimisé
cat > /opt/qwen35/start_optimized.sh << 'EOF'
#!/bin/bash
source /opt/qwen-venv/bin/activate
cd /opt/qwen35

# Variables d'environnement pour optimisation
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
export CUDA_LAUNCH_BLOCKING=1
export OMP_NUM_THREADS=8

# Vérifier et télécharger le modèle si nécessaire
MODEL_READY=false
if [ -f "/opt/qwen35/model/config.json" ]; then
    MODEL_READY=true
else
    echo "📥 Téléchargement du modèle depuis S3..."
    if aws s3 cp "s3://harmonic-ai-qwen-models/qwen35/model.tar.gz" /tmp/model.tar.gz; then
        tar -xzf /tmp/model.tar.gz -C /opt/qwen35/model/
        rm /tmp/model.tar.gz
        MODEL_READY=true
        echo "✅ Modèle téléchargé et extrait"
    else
        echo "❌ Échec du téléchargement du modèle"
        exit 1
    fi
fi

if [ "$MODEL_READY" = true ]; then
    echo "🚀 Démarrage de l'API Qwen3.5 optimisée..."
    
    # Paramètres optimisés pour g5.4xlarge
    python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8080 \
        --workers 4 \
        --limit-concurrency 100 \
        --backlog 1000 \
        --timeout-keep-alive 30 \
        --log-level info
else
    echo "❌ Modèle non disponible"
    exit 1
fi
EOF

chmod +x /opt/qwen35/start_optimized.sh

# Créer un service systemd optimisé
cat > /etc/systemd/system/qwen35-optimized.service << 'EOF'
[Unit]
Description=Qwen3.5 Optimized API Service
After=network.target nginx.service docker.service
Requires=nginx.service docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/qwen35
ExecStart=/opt/qwen35/start_optimized.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environnement optimisé
Environment="PYTHONPATH=/opt/qwen35"
Environment="MODEL_PATH=/opt/qwen35/model"
Environment="TRANSFORMERS_CACHE=/opt/qwen35/cache"
Environment="HF_HOME=/opt/qwen35/cache"
Environment="AWS_REGION=us-east-1"
Environment="CUDA_VISIBLE_DEVICES=0,1"

# Limites de ressources optimisées
LimitNOFILE=100000
LimitNPROC=100000
LimitMEMLOCK=infinity
LimitSTACK=infinity

# Paramètres de sécurité
NoNewPrivileges=true
ProtectSystem=strict
PrivateTmp=true
PrivateDevices=true
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable qwen35-optimized.service

# Configuration avancée de monitoring
mkdir -p /opt/qwen35/monitoring

# Script de monitoring GPU
cat > /opt/qwen35/monitoring/gpu_monitor.sh << 'EOF'
#!/bin/bash
while true; do
    TIMESTAMP=$(date +%s)
    GPU_STATS=$(nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits)
    echo "$TIMESTAMP,$GPU_STATS" >> /opt/qwen35/logs/gpu_metrics.csv
    sleep 10
done
EOF

chmod +x /opt/qwen35/monitoring/gpu_monitor.sh

# Démarrer les services
systemctl start qwen35-optimized.service

# Démarrer le monitoring GPU en arrière-plan
nohup /opt/qwen35/monitoring/gpu_monitor.sh > /dev/null 2>&1 &

echo "✅ Installation de production taille moyenne terminée"
echo "📊 Services démarrés :"
echo "   - Qwen3.5 API (port 8080)"
echo "   - NGINX Reverse Proxy (port 80)"
echo "   - GPU Monitoring"
"@))
    }
}

# 1. Lister les templates disponibles
if ($ListTemplates) {
    Write-Host "📋 TEMPLATES DISPONIBLES :" -ForegroundColor Cyan
    Write-Host "=" * 80
    
    foreach ($templateName in $templates.Keys | Sort-Object) {
        $template = $templates[$templateName]
        Write-Host "🏷️  $templateName" -ForegroundColor Yellow
        Write-Host "   📝 $($template.Description)" -ForegroundColor Gray
        Write-Host "   💻 Instance Type: $($template.InstanceType)" -ForegroundColor Gray
        Write-Host "   📊 GPU: $(if ($template.InstanceType -match 'g5') { 'NVIDIA A10G' } else { 'CPU Only' })" -ForegroundColor Gray
        Write-Host ""
    }
    
    exit 0
}

# 2. Générer un template spécifique
if ($templates.ContainsKey($TemplateName)) {
    $template = $templates[$TemplateName]
    
    Write-Host "🔧 Génération du template : $TemplateName" -ForegroundColor Green
    Write-Host "   📝 $($template.Description)" -ForegroundColor Gray
    Write-Host "   💻 Type d'instance : $($template.InstanceType)" -ForegroundColor Gray
    Write-Host "   🌐 Région : $Region" -ForegroundColor Gray
    
    # Créer la configuration complète
    $launchTemplateData = @{
        LaunchTemplateName = $template.Name
        VersionDescription = "Version 1.0 - $TemplateName"
        LaunchTemplateData = @{
            ImageId = $template.ImageId
            InstanceType = $template.InstanceType
            KeyName = $template.KeyName
            SecurityGroupIds = $template.SecurityGroupIds
            IamInstanceProfile = $template.IamInstanceProfile
            BlockDeviceMappings = $template.BlockDeviceMappings
            TagSpecifications = $template.TagSpecifications
            UserData = $template.UserData
        }
    }
    
    # Sauvegarder dans un fichier
    $launchTemplateData | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8
    
    Write-Host "✅ Template généré avec succès : $OutputFile" -ForegroundColor Green
    Write-Host "📍 Utilisation : aws ec2 create-launch-template --cli-input-json file://$OutputFile --region $Region" -ForegroundColor Cyan
    
} else {
    Write-Host "❌ Template non trouvé : $TemplateName" -ForegroundColor Red
    Write-Host "   ℹ️  Utilisez -ListTemplates pour voir les templates disponibles" -ForegroundColor Gray
    exit 1
}

Write-Host "=" * 80
Write-Host "🎉 Génération des templates EC2 terminée !" -ForegroundColor Green