# Script de génération des templates de lancement EC2 pour Qwen3.5 (Version simplifiée)
# Auteur : Harmonic AI Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$TemplateName = "production_medium",
    [string]$OutputFile = "ec2-launch-template.json",
    [switch]$ListTemplates = $false
)

$ErrorActionPreference = "Stop"

Write-Host "📋 Génération des templates de lancement EC2 pour Qwen3.5..." -ForegroundColor Cyan
Write-Host "📍 Région : $Region" -ForegroundColor Yellow
Write-Host "🏷️  Template : $TemplateName" -ForegroundColor Yellow
Write-Host "=" * 80

# Définir les templates disponibles
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
        UserData = "IyEvYmluL2Jhc2gKIyBTY3JpcHQgZCd
        # User data simplifié pour développement
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
        UserData = "IyEvYmluL2Jhc2gKIyBTY3JpcHQgZCd
        # User data simplifié pour production petite
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
        UserData = "IyEvYmluL2Jhc2gKIyBTY3JpcHQgZCd
        # User data simplifié pour production moyenne
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
    
    # Créer un user data simple pour éviter les problèmes de syntaxe
    $simpleUserData = @"
#!/bin/bash
# Installation automatique pour Qwen3.5

apt-get update -y
apt-get upgrade -y

# Installer les dépendances de base
apt-get install -y python3.10 python3-pip python3.10-venv git curl wget htop

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

echo "✅ Installation terminée. Redémarrage dans 30 secondes..."
sleep 30
reboot
"@
    
    # Encoder en base64
    $encodedUserData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($simpleUserData))
    
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
            UserData = $encodedUserData
        }
    }
    
    # Sauvegarder dans un fichier
    $launchTemplateData | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8
    
    Write-Host "✅ Template généré avec succès : $OutputFile" -ForegroundColor Green
    Write-Host "📍 Utilisation : aws ec2 create-launch-template --cli-input-json file://$OutputFile --region $Region" -ForegroundColor Cyan
    
    # Afficher un aperçu du template
    Write-Host "`n🔍 APERÇU DU TEMPLATE :" -ForegroundColor Yellow
    Write-Host "=" * 80
    
    $preview = @{
        "LaunchTemplateName" = $template.Name
        "InstanceType" = $template.InstanceType
        "ImageId" = $template.ImageId
        "KeyName" = $template.KeyName
        "SecurityGroupIds" = $template.SecurityGroupIds -join ", "
        "BlockDeviceMappings" = $template.BlockDeviceMappings.Count
        "Tags" = $template.TagSpecifications[0].Tags.Count
    }
    
    $preview.GetEnumerator() | ForEach-Object {
        Write-Host "   $($_.Key.PadRight(25)) : $($_.Value)" -ForegroundColor Gray
    }
    
} else {
    Write-Host "❌ Template non trouvé : $TemplateName" -ForegroundColor Red
    Write-Host "   ℹ️  Utilisez -ListTemplates pour voir les templates disponibles" -ForegroundColor Gray
    exit 1
}

Write-Host "=" * 80
Write-Host "🎉 Génération des templates EC2 terminée !" -ForegroundColor Green