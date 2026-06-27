# Configuration des groupes de sécurité et règles réseau pour EC2 Qwen3.5
# Auteur : Harmonic AI Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$SecurityGroupName = "qwen35-security-group",
    [string]$VpcId = "",
    [switch]$CreateNew = $false,
    [switch]$UpdateExisting = $false,
    [switch]$ListOnly = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🛡️  Configuration des groupes de sécurité EC2 pour Qwen3.5..." -ForegroundColor Cyan
Write-Host "📍 Région : $Region" -ForegroundColor Yellow
Write-Host "🏷️  Nom du groupe : $SecurityGroupName" -ForegroundColor Yellow
Write-Host "=" * 80

# 1. Vérifier les credentials AWS
Write-Host "1️⃣  Vérification des credentials AWS..." -ForegroundColor Green
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

Write-Host "=" * 80

# 2. Obtenir ou créer le VPC
Write-Host "2️⃣  Configuration du VPC..." -ForegroundColor Green
try {
    if ([string]::IsNullOrEmpty($VpcId)) {
        Write-Host "🔍 Recherche du VPC par défaut..." -ForegroundColor Gray
        $defaultVpc = aws ec2 describe-vpcs `
            --region $Region `
            --filters "Name=isDefault,Values=true" `
            --query 'Vpcs[0].VpcId' `
            --output text 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $defaultVpc) {
            $VpcId = $defaultVpc
            Write-Host "✅ VPC par défaut trouvé : $VpcId" -ForegroundColor Green
        } else {
            Write-Host "❌ Aucun VPC par défaut trouvé" -ForegroundColor Red
            Write-Host "   ℹ️  Vous devez spécifier un VPC avec le paramètre -VpcId" -ForegroundColor Gray
            exit 1
        }
    } else {
        # Vérifier que le VPC spécifié existe
        Write-Host "🔍 Vérification du VPC spécifié..." -ForegroundColor Gray
        $vpcExists = aws ec2 describe-vpcs --vpc-ids $VpcId --region $Region 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ VPC valide : $VpcId" -ForegroundColor Green
        } else {
            Write-Host "❌ VPC invalide : $VpcId" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "❌ Erreur lors de la configuration du VPC" -ForegroundColor Red
    exit 1
}

Write-Host "=" * 80

# 3. Vérifier les groupes de sécurité existants
Write-Host "3️⃣  Vérification des groupes de sécurité..." -ForegroundColor Green
try {
    # Vérifier si le groupe de sécurité existe déjà
    $existingSg = aws ec2 describe-security-groups `
        --region $Region `
        --group-names $SecurityGroupName 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $sgId = ($existingSg | ConvertFrom-Json).SecurityGroups[0].GroupId
        $sgDescription = ($existingSg | ConvertFrom-Json).SecurityGroups[0].Description
        Write-Host "✅ Groupe de sécurité existant trouvé :" -ForegroundColor Green
        Write-Host "   📍 ID : $sgId" -ForegroundColor Gray
        Write-Host "   📝 Description : $sgDescription" -ForegroundColor Gray
        Write-Host "   🌐 VPC : $VpcId" -ForegroundColor Gray
        
        $sgExists = $true
    } else {
        Write-Host "ℹ️  Groupe de sécurité non trouvé : $SecurityGroupName" -ForegroundColor Gray
        $sgExists = $false
    }
    
    # Si ListOnly est activé, afficher les règles existantes et quitter
    if ($ListOnly -and $sgExists) {
        Write-Host "📋 Règles de sécurité existantes :" -ForegroundColor Yellow
        
        # Règles entrantes
        $ingressRules = ($existingSg | ConvertFrom-Json).SecurityGroups[0].IpPermissions
        if ($ingressRules) {
            Write-Host "   🔽 Règles entrantes (Ingress) :" -ForegroundColor Cyan
            foreach ($rule in $ingressRules) {
                $fromPort = if ($rule.FromPort) { $rule.FromPort } else { "All" }
                $toPort = if ($rule.ToPort) { $rule.ToPort } else { "All" }
                $protocol = if ($rule.IpProtocol -eq "-1") { "All" } else { $rule.IpProtocol }
                
                Write-Host "      📌 Protocole : $protocol, Ports : $fromPort-$toPort" -ForegroundColor Gray
                
                foreach ($ipRange in $rule.IpRanges) {
                    Write-Host "         🌐 CIDR : $($ipRange.CidrIp)" -ForegroundColor Gray
                }
            }
        }
        
        # Règles sortantes
        $egressRules = ($existingSg | ConvertFrom-Json).SecurityGroups[0].IpPermissionsEgress
        if ($egressRules) {
            Write-Host "   🔼 Règles sortantes (Egress) :" -ForegroundColor Cyan
            foreach ($rule in $egressRules) {
                $fromPort = if ($rule.FromPort) { $rule.FromPort } else { "All" }
                $toPort = if ($rule.ToPort) { $rule.ToPort } else { "All" }
                $protocol = if ($rule.IpProtocol -eq "-1") { "All" } else { $rule.IpProtocol }
                
                Write-Host "      📌 Protocole : $protocol, Ports : $fromPort-$toPort" -ForegroundColor Gray
                
                foreach ($ipRange in $rule.IpRanges) {
                    Write-Host "         🌐 CIDR : $($ipRange.CidrIp)" -ForegroundColor Gray
                }
            }
        }
        
        exit 0
    }
    
} catch {
    Write-Host "⚠️  Erreur lors de la vérification des groupes de sécurité" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 4. Créer ou mettre à jour le groupe de sécurité
if ($CreateNew -or (-not $sgExists -and $UpdateExisting)) {
    Write-Host "4️⃣  Création d'un nouveau groupe de sécurité..." -ForegroundColor Green
    
    try {
        if ($sgExists -and $CreateNew) {
            Write-Host "⚠️  Le groupe de sécurité existe déjà. Utilisez -UpdateExisting pour le mettre à jour." -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host "🔧 Création du groupe de sécurité..." -ForegroundColor Gray
        $newSg = aws ec2 create-security-group `
            --group-name $SecurityGroupName `
            --description "Security group for Qwen3.5 EC2 instance - LLM inference API" `
            --vpc-id $VpcId `
            --region $Region
        
        $sgId = $newSg.GroupId
        Write-Host "✅ Groupe de sécurité créé : $SecurityGroupName (ID: $sgId)" -ForegroundColor Green
        
        $sgExists = $true
        $UpdateExisting = $true  # Pour configurer les règles après création
        
    } catch {
        Write-Host "❌ Erreur lors de la création du groupe de sécurité" -ForegroundColor Red
        Write-Host "   📋 Détails : $_" -ForegroundColor Gray
        exit 1
    }
}

Write-Host "=" * 80

# 5. Configurer les règles de sécurité
if ($UpdateExisting -and $sgExists) {
    Write-Host "5️⃣  Configuration des règles de sécurité..." -ForegroundColor Green
    
    try {
        # Définir les règles recommandées pour Qwen3.5
        $recommendedRules = @(
            # Règles entrantes (Ingress)
            @{Type="ingress"; Protocol="tcp"; Port=22; CIDR="0.0.0.0/0"; Description="SSH Access"},
            @{Type="ingress"; Protocol="tcp"; Port=80; CIDR="0.0.0.0/0"; Description="HTTP Access"},
            @{Type="ingress"; Protocol="tcp"; Port=443; CIDR="0.0.0.0/0"; Description="HTTPS Access"},
            @{Type="ingress"; Protocol="tcp"; Port=8080; CIDR="0.0.0.0/0"; Description="Qwen3.5 API Port"},
            @{Type="ingress"; Protocol="tcp"; Port=8000; CIDR="0.0.0.0/0"; Description="Alternative API Port"},
            @{Type="ingress"; Protocol="tcp"; Port=8501; CIDR="0.0.0.0/0"; Description="Streamlit Dashboard"},
            @{Type="ingress"; Protocol="tcp"; Port=3000; CIDR="0.0.0.0/0"; Description="Web Interface"},
            
            # Règles sortantes (Egress) - Accès complet pour téléchargements
            @{Type="egress"; Protocol="-1"; Port=0; CIDR="0.0.0.0/0"; Description="All Outbound Traffic"}
        )
        
        Write-Host "📋 Règles recommandées pour Qwen3.5 :" -ForegroundColor Yellow
        foreach ($rule in $recommendedRules) {
            $portDisplay = if ($rule.Port -eq 0) { "All" } else { $rule.Port }
            $protocolDisplay = if ($rule.Protocol -eq "-1") { "All" } else { $rule.Protocol }
            
            Write-Host "   $($rule.Type.ToUpper()) : $protocolDisplay:$portDisplay ($($rule.Description))" -ForegroundColor Gray
        }
        
        # Appliquer les règles
        Write-Host "🔧 Application des règles de sécurité..." -ForegroundColor Gray
        
        foreach ($rule in $recommendedRules) {
            $ruleType = $rule.Type
            $protocol = $rule.Protocol
            $port = $rule.Port
            $cidr = $rule.CIDR
            $description = $rule.Description
            
            # Pour les règles sortantes avec protocole "-1", utiliser une syntaxe différente
            if ($ruleType -eq "egress" -and $protocol -eq "-1") {
                Write-Host "   🔼 Ajout de la règle sortante : All traffic" -ForegroundColor Gray
                
                aws ec2 authorize-security-group-egress `
                    --group-id $sgId `
                    --ip-permissions "IpProtocol=-1,FromPort=-1,ToPort=-1,IpRanges=[{CidrIp=$cidr}]" `
                    --region $Region | Out-Null
                    
            } elseif ($port -eq 0) {
                # Pour les ports "All"
                Write-Host "   🔽 Ajout de la règle $ruleType : $protocol (All ports)" -ForegroundColor Gray
                
                if ($ruleType -eq "ingress") {
                    aws ec2 authorize-security-group-ingress `
                        --group-id $sgId `
                        --ip-permissions "IpProtocol=$protocol,FromPort=-1,ToPort=-1,IpRanges=[{CidrIp=$cidr}]" `
                        --region $Region | Out-Null
                } else {
                    aws ec2 authorize-security-group-egress `
                        --group-id $sgId `
                        --ip-permissions "IpProtocol=$protocol,FromPort=-1,ToPort=-1,IpRanges=[{CidrIp=$cidr}]" `
                        --region $Region | Out-Null
                }
                
            } else {
                # Pour les ports spécifiques
                Write-Host "   🔽 Ajout de la règle $ruleType : $protocol:$port" -ForegroundColor Gray
                
                if ($ruleType -eq "ingress") {
                    aws ec2 authorize-security-group-ingress `
                        --group-id $sgId `
                        --protocol $protocol `
                        --port $port `
                        --cidr $cidr `
                        --region $Region | Out-Null
                } else {
                    aws ec2 authorize-security-group-egress `
                        --group-id $sgId `
                        --protocol $protocol `
                        --port $port `
                        --cidr $cidr `
                        --region $Region | Out-Null
                }
            }
            
            Write-Host "      ✅ Règle ajoutée : $description" -ForegroundColor Green
        }
        
        Write-Host "✅ Toutes les règles de sécurité ont été configurées" -ForegroundColor Green
        
    } catch {
        Write-Host "⚠️  Erreur lors de la configuration des règles de sécurité" -ForegroundColor Yellow
        Write-Host "   📋 Détails : $_" -ForegroundColor Gray
    }
}

Write-Host "=" * 80

# 6. Vérification finale
Write-Host "6️⃣  Vérification finale de la configuration..." -ForegroundColor Green
try {
    if ($sgExists) {
        # Obtenir les détails du groupe de sécurité
        $sgDetails = aws ec2 describe-security-groups `
            --group-ids $sgId `
            --region $Region `
            --query 'SecurityGroups[0]'
        
        $sgDetailsObj = $sgDetails | ConvertFrom-Json
        
        Write-Host "📊 RÉSUMÉ DE LA CONFIGURATION DE SÉCURITÉ" -ForegroundColor Cyan -BackgroundColor DarkBlue
        Write-Host "=" * 80
        
        $securitySummary = @{
            "ID du groupe" = $sgId
            "Nom" = $sgDetailsObj.GroupName
            "Description" = $sgDetailsObj.Description
            "VPC ID" = $sgDetailsObj.VpcId
            "Règles entrantes" = $sgDetailsObj.IpPermissions.Count
            "Règles sortantes" = $sgDetailsObj.IpPermissionsEgress.Count
        }
        
        $securitySummary.GetEnumerator() | ForEach-Object {
            Write-Host "   $($_.Key.PadRight(25)) : $($_.Value)" -ForegroundColor Gray
        }
        
        # Afficher les règles détaillées
        Write-Host "`n🔍 RÈGLES DÉTAILLÉES :" -ForegroundColor Yellow
        
        # Règles entrantes
        if ($sgDetailsObj.IpPermissions.Count -gt 0) {
            Write-Host "   🔽 RÈGLES ENTRANTES (INGRESS) :" -ForegroundColor Cyan
            foreach ($rule in $sgDetailsObj.IpPermissions) {
                $fromPort = if ($rule.FromPort) { $rule.FromPort } else { "All" }
                $toPort = if ($rule.ToPort) { $rule.ToPort } else { "All" }
                $protocol = if ($rule.IpProtocol -eq "-1") { "All" } else { $rule.IpProtocol }
                
                Write-Host "      📌 $protocol : $fromPort-$toPort" -ForegroundColor Gray
                
                foreach ($ipRange in $rule.IpRanges) {
                    Write-Host "         🌐 $($ipRange.CidrIp)" -ForegroundColor Gray
                }
            }
        }
        
        # Règles sortantes
        if ($sgDetailsObj.IpPermissionsEgress.Count -gt 0) {
            Write-Host "`n   🔼 RÈGLES SORTANTES (EGRESS) :" -ForegroundColor Cyan
            foreach ($rule in $sgDetailsObj.IpPermissionsEgress) {
                $fromPort = if ($rule.FromPort) { $rule.FromPort } else { "All" }
                $toPort = if ($rule.ToPort) { $rule.ToPort } else { "All" }
                $protocol = if ($rule.IpProtocol -eq "-1") { "All" } else { $rule.IpProtocol }
                
                Write-Host "      📌 $protocol : $fromPort-$toPort" -ForegroundColor Gray
                
                foreach ($ipRange in $rule.IpRanges) {
                    Write-Host "         🌐 $($ipRange.CidrIp)" -ForegroundColor Gray
                }
            }
        }
        
    } else {
        Write-Host "ℹ️  Aucun groupe de sécurité configuré" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "⚠️  Erreur lors de la vérification finale" -ForegroundColor Yellow
}

Write-Host "=" * 80

# 7. Recommandations de sécurité
Write-Host "7️⃣  RECOMMANDATIONS DE SÉCURITÉ AVANCÉE" -ForegroundColor Magenta
Write-Host "=" * 80

$securityRecommendations = @(
    "🔒 Restreindre l'accès SSH à votre IP publique uniquement",
    "🌐 Utiliser un VPN ou AWS Direct Connect pour l'accès interne",
    "🛡️  Mettre en place un Web Application Firewall (WAF)",
    "🔑 Implémenter l'authentification par clé API pour l'API Qwen3.5",
    "📊 Activer AWS CloudTrail pour l'audit des accès",
    "🚨 Configurer des alertes CloudWatch pour les activités suspectes",
    "🔐 Chiffrer les volumes EBS avec AWS KMS",
    "📝 Mettre en place une politique IAM avec le principe du moindre privilège"
)

for ($i = 0; $i -lt $securityRecommendations.Count; $i++) {
    Write-Host "   $($i+1). $($securityRecommendations[$i])" -ForegroundColor Gray
}

Write-Host "=" * 80
Write-Host "✅ Configuration de sécurité EC2 terminée !" -ForegroundColor Green
Write-Host "📍 Groupe de sécurité prêt : $SecurityGroupName (ID: $sgId)" -ForegroundColor Cyan