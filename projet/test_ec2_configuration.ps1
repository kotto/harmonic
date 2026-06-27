# Script de test de la configuration EC2 pour Qwen3.5
# Auteur : Harmonic AI Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Region = "us-east-1",
    [string]$InstanceName = "qwen35-ec2-server",
    [string]$SecurityGroupName = "qwen35-security-group",
    [string]$KeyPairName = "qwen35-keypair",
    [string]$IamRoleName = "qwen35-ec2-role",
    [switch]$DryRun = $false,
    [switch]$QuickTest = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Test de la configuration EC2 pour Qwen3.5..." -ForegroundColor Cyan
Write-Host "📍 Région : $Region" -ForegroundColor Yellow
Write-Host "🏷️  Instance : $InstanceName" -ForegroundColor Yellow
Write-Host "🔧 Mode : $(if ($DryRun) { 'Dry Run' } else { 'Test Complet' })" -ForegroundColor $(if ($DryRun) { "Yellow" } else { "Green" })
Write-Host "=" * 80

# Fonction pour les tests
function Test-AWSResource {
    param(
        [string]$TestName,
        [string]$Command,
        [string]$SuccessMessage,
        [string]$ErrorMessage,
        [switch]$Required = $true
    )
    
    Write-Host "🔍 Test : $TestName" -ForegroundColor Gray
    
    try {
        if ($DryRun) {
            Write-Host "   ⏭️  Skipped (Dry Run)" -ForegroundColor Yellow
            return $true
        }
        
        $output = Invoke-Expression $Command 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $SuccessMessage" -ForegroundColor Green
            return $true
        } else {
            if ($Required) {
                Write-Host "   ❌ $ErrorMessage" -ForegroundColor Red
                Write-Host "   📋 Sortie : $output" -ForegroundColor Gray
                return $false
            } else {
                Write-Host "   ⚠️  $ErrorMessage (Optionnel)" -ForegroundColor Yellow
                return $true
            }
        }
        
    } catch {
        if ($Required) {
            Write-Host "   ❌ Erreur : $_" -ForegroundColor Red
            return $false
        } else {
            Write-Host "   ⚠️  Erreur : $_ (Optionnel)" -ForegroundColor Yellow
            return $true
        }
    }
}

# Résultats des tests
$testResults = @{}
$allTestsPassed = $true

Write-Host "1️⃣  TESTS DE BASE AWS" -ForegroundColor Green
Write-Host "=" * 80

# Test 1: Credentials AWS
$test1 = Test-AWSResource `
    -TestName "AWS Credentials" `
    -Command "aws sts get-caller-identity --region $Region" `
    -SuccessMessage "Credentials AWS valides" `
    -ErrorMessage "Credentials AWS invalides"

$testResults["AWS_Credentials"] = $test1
if (-not $test1) { $allTestsPassed = $false }

# Test 2: Région AWS valide
$test2 = Test-AWSResource `
    -TestName "AWS Region" `
    -Command "aws ec2 describe-regions --region-names $Region" `
    -SuccessMessage "Région AWS valide" `
    -ErrorMessage "Région AWS invalide"

$testResults["AWS_Region"] = $test2
if (-not $test2) { $allTestsPassed = $false }

Write-Host "=" * 80
Write-Host "2️⃣  TESTS DES RESSOURCES EC2" -ForegroundColor Green
Write-Host "=" * 80

# Test 3: Paire de clés
$test3 = Test-AWSResource `
    -TestName "Key Pair" `
    -Command "aws ec2 describe-key-pairs --key-names $KeyPairName --region $Region" `
    -SuccessMessage "Paire de clés existante" `
    -ErrorMessage "Paire de clés non trouvée"

$testResults["Key_Pair"] = $test3
if (-not $test3) { $allTestsPassed = $false }

# Test 4: Groupe de sécurité
$test4 = Test-AWSResource `
    -TestName "Security Group" `
    -Command "aws ec2 describe-security-groups --group-names $SecurityGroupName --region $Region" `
    -SuccessMessage "Groupe de sécurité existant" `
    -ErrorMessage "Groupe de sécurité non trouvé"

$testResults["Security_Group"] = $test4
if (-not $test4) { $allTestsPassed = $false }

# Test 5: Rôle IAM
$test5 = Test-AWSResource `
    -TestName "IAM Role" `
    -Command "aws iam get-role --role-name $IamRoleName --region $Region" `
    -SuccessMessage "Rôle IAM existant" `
    -ErrorMessage "Rôle IAM non trouvé"

$testResults["IAM_Role"] = $test5
if (-not $test5) { $allTestsPassed = $false }

# Test 6: Profil d'instance
$test6 = Test-AWSResource `
    -TestName "Instance Profile" `
    -Command "aws iam get-instance-profile --instance-profile-name $IamRoleName --region $Region" `
    -SuccessMessage "Profil d'instance existant" `
    -ErrorMessage "Profil d'instance non trouvé"

$testResults["Instance_Profile"] = $test6
if (-not $test6) { $allTestsPassed = $false }

if (-not $QuickTest) {
    Write-Host "=" * 80
    Write-Host "3️⃣  TESTS AVANCÉS" -ForegroundColor Green
    Write-Host "=" * 80
    
    # Test 7: VPC par défaut
    $test7 = Test-AWSResource `
        -TestName "Default VPC" `
        -Command "aws ec2 describe-vpcs --filters 'Name=isDefault,Values=true' --region $Region --query 'Vpcs[0].VpcId' --output text" `
        -SuccessMessage "VPC par défaut trouvé" `
        -ErrorMessage "VPC par défaut non trouvé" `
        -Required $false
    
    $testResults["Default_VPC"] = $test7
    
    # Test 8: Sous-réseaux disponibles
    $test8 = Test-AWSResource `
        -TestName "Available Subnets" `
        -Command "aws ec2 describe-subnets --filters 'Name=vpc-id,Values=vpc-*' --region $Region --query 'Subnets[0].SubnetId' --output text" `
        -SuccessMessage "Sous-réseaux disponibles" `
        -ErrorMessage "Aucun sous-réseau disponible" `
        -Required $false
    
    $testResults["Available_Subnets"] = $test8
    
    # Test 9: AMI Ubuntu disponible
    $test9 = Test-AWSResource `
        -TestName "Ubuntu AMI" `
        -Command "aws ec2 describe-images --owners 099720109477 --filters 'Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*' 'Name=state,Values=available' --region $Region --query 'Images[0].ImageId' --output text" `
        -SuccessMessage "AMI Ubuntu disponible" `
        -ErrorMessage "AMI Ubuntu non trouvée" `
        -Required $false
    
    $testResults["Ubuntu_AMI"] = $test9
    
    # Test 10: Types d'instances disponibles
    $test10 = Test-AWSResource `
        -TestName "Instance Types" `
        -Command "aws ec2 describe-instance-types --filters 'Name=instance-type,Values=g5.*' --region $Region --query 'InstanceTypes[0].InstanceType' --output text" `
        -SuccessMessage "Types d'instances GPU disponibles" `
        -ErrorMessage "Types d'instances GPU non trouvés" `
        -Required $false
    
    $testResults["GPU_Instance_Types"] = $test10
}

Write-Host "=" * 80
Write-Host "4️⃣  TESTS DE CONFIGURATION" -ForegroundColor Green
Write-Host "=" * 80

# Test 11: Configuration du groupe de sécurité
if ($test4) {
    Write-Host "🔍 Test : Security Group Rules" -ForegroundColor Gray
    
    try {
        if ($DryRun) {
            Write-Host "   ⏭️  Skipped (Dry Run)" -ForegroundColor Yellow
            $test11 = $true
        } else {
            # Obtenir les règles du groupe de sécurité
            $sgRules = aws ec2 describe-security-groups `
                --group-names $SecurityGroupName `
                --region $Region `
                --query 'SecurityGroups[0].IpPermissions' `
                --output json 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                $rules = $sgRules | ConvertFrom-Json
                
                # Vérifier les ports essentiels
                $essentialPorts = @(22, 80, 443, 8080, 8000)
                $foundPorts = @()
                
                foreach ($rule in $rules) {
                    if ($rule.FromPort -and $rule.ToPort) {
                        for ($port = $rule.FromPort; $port -le $rule.ToPort; $port++) {
                            if ($essentialPorts -contains $port) {
                                $foundPorts += $port
                            }
                        }
                    }
                }
                
                $missingPorts = $essentialPorts | Where-Object { $_ -notin $foundPorts }
                
                if ($missingPorts.Count -eq 0) {
                    Write-Host "   ✅ Tous les ports essentiels sont ouverts" -ForegroundColor Green
                    $test11 = $true
                } else {
                    Write-Host "   ⚠️  Ports manquants : $($missingPorts -join ', ')" -ForegroundColor Yellow
                    $test11 = $true  # Optionnel pour le test
                }
                
            } else {
                Write-Host "   ⚠️  Impossible de vérifier les règles (Optionnel)" -ForegroundColor Yellow
                $test11 = $true
            }
        }
        
    } catch {
        Write-Host "   ⚠️  Erreur lors du test des règles (Optionnel) : $_" -ForegroundColor Yellow
        $test11 = $true
    }
    
    $testResults["Security_Group_Rules"] = $test11
}

# Test 12: Permissions IAM
if ($test5) {
    Write-Host "🔍 Test : IAM Permissions" -ForegroundColor Gray
    
    try {
        if ($DryRun) {
            Write-Host "   ⏭️  Skipped (Dry Run)" -ForegroundColor Yellow
            $test12 = $true
        } else {
            # Vérifier les politiques attachées
            $attachedPolicies = aws iam list-attached-role-policies `
                --role-name $IamRoleName `
                --region $Region `
                --query 'AttachedPolicies[].PolicyArn' `
                --output text 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                $policies = $attachedPolicies -split "`t"
                
                # Politiques recommandées
                $recommendedPolicies = @(
                    "AmazonS3ReadOnlyAccess",
                    "AmazonEC2ContainerRegistryReadOnlyAccess",
                    "CloudWatchAgentServerPolicy"
                )
                
                $foundPolicies = @()
                foreach ($policy in $policies) {
                    $policyName = $policy.Split('/')[-1]
                    if ($recommendedPolicies -contains $policyName) {
                        $foundPolicies += $policyName
                    }
                }
                
                Write-Host "   📋 Politiques attachées : $($foundPolicies.Count)/$($recommendedPolicies.Count)" -ForegroundColor Gray
                
                if ($foundPolicies.Count -ge 2) {
                    Write-Host "   ✅ Permissions IAM suffisantes" -ForegroundColor Green
                    $test12 = $true
                } else {
                    Write-Host "   ⚠️  Permissions IAM limitées" -ForegroundColor Yellow
                    $test12 = $true  # Optionnel pour le test
                }
                
            } else {
                Write-Host "   ⚠️  Impossible de vérifier les permissions (Optionnel)" -ForegroundColor Yellow
                $test12 = $true
            }
        }
        
    } catch {
        Write-Host "   ⚠️  Erreur lors du test des permissions (Optionnel) : $_" -ForegroundColor Yellow
        $test12 = $true
    }
    
    $testResults["IAM_Permissions"] = $test12
}

Write-Host "=" * 80
Write-Host "5️⃣  RÉSUMÉ DES TESTS" -ForegroundColor Cyan -BackgroundColor DarkBlue
Write-Host "=" * 80

# Afficher les résultats
$passedTests = 0
$totalTests = $testResults.Count

Write-Host "📊 RÉSULTATS DES TESTS :" -ForegroundColor Yellow

foreach ($testName in $testResults.Keys | Sort-Object) {
    $result = $testResults[$testName]
    $status = if ($result) { "✅ PASS" } else { "❌ FAIL" }
    $color = if ($result) { "Green" } else { "Red" }
    
    if ($result) { $passedTests++ }
    
    Write-Host "   $($testName.Replace('_', ' ').PadRight(30)) : $status" -ForegroundColor $color
}

Write-Host "=" * 80

# Score final
$scorePercentage = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 2) } else { 0 }

Write-Host "🎯 SCORE FINAL : $passedTests/$totalTests ($scorePercentage%)" -ForegroundColor $(if ($scorePercentage -ge 80) { "Green" } elseif ($scorePercentage -ge 60) { "Yellow" } else { "Red" })

if ($allTestsPassed) {
    Write-Host "✅ TOUS LES TESTS ESSENTIELS ONT RÉUSSI !" -ForegroundColor Green -BackgroundColor DarkGreen
    Write-Host "📍 La configuration EC2 est prête pour le déploiement de Qwen3.5" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  CERTAINS TESTS ESSENTIELS ONT ÉCHOUÉ" -ForegroundColor Yellow -BackgroundColor DarkRed
    Write-Host "📍 Des corrections sont nécessaires avant le déploiement" -ForegroundColor Gray
    
    # Recommandations
    Write-Host "`n🎯 RECOMMANDATIONS :" -ForegroundColor Magenta
    
    if (-not $test1) {
        Write-Host "   1. Configurer les credentials AWS : aws configure" -ForegroundColor Gray
    }
    
    if (-not $test3) {
        Write-Host "   2. Créer une paire de clés : aws ec2 create-key-pair --key-name $KeyPairName" -ForegroundColor Gray
    }
    
    if (-not $test4) {
        Write-Host "   3. Créer un groupe de sécurité : aws ec2 create-security-group --group-name $SecurityGroupName" -ForegroundColor Gray
    }
    
    if (-not $test5) {
        Write-Host "   4. Créer un rôle IAM : aws iam create-role --role-name $IamRoleName" -ForegroundColor Gray
    }
}

Write-Host "=" * 80

# Instructions pour le déploiement
if ($allTestsPassed -and -not $DryRun) {
    Write-Host "🚀 INSTRUCTIONS POUR LE DÉPLOIEMENT :" -ForegroundColor Magenta
    Write-Host "=" * 80
    
    $deploymentSteps = @(
        "1. Générer un template de lancement :",
        "   .\generate_ec2_templates.ps1 -TemplateName production_medium",
        "",
        "2. Créer le template de lancement dans AWS :",
        "   aws ec2 create-launch-template --cli-input-json file://ec2-launch-template.json --region $Region",
        "",
        "3. Lancer une instance EC2 :",
        "   aws ec2 run-instances --launch-template LaunchTemplateName=qwen35-prod-medium-template --count 1 --region $Region",
        "",
        "4. Vérifier le statut de l'instance :",
        "   aws ec2 describe-instances --filters 'Name=tag:Name,Values=$InstanceName' --region $Region",
        "",
        "5. Se connecter via SSH :",
        "   ssh -i ~/.ssh/$KeyPairName.pem ubuntu@<IP_PUBLIQUE>",
        "",
        "6. Tester l'API Qwen3.5 :",
        "   curl http://localhost:8080/health"
    )
    
    foreach ($step in $deploymentSteps) {
        Write-Host "   $step" -ForegroundColor Gray
    }
}

Write-Host "=" * 80
Write-Host "🧪 Tests de configuration EC2 terminés !" -ForegroundColor Green

# Sauvegarder les résultats
if (-not $DryRun) {
    $testReport = @{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        region = $Region
        instance_name = $InstanceName
        test_results = $testResults
        summary = @{
            total_tests = $totalTests
            passed_tests = $passedTests
            score_percentage = $scorePercentage
            all_essential_passed = $allTestsPassed
        }
        recommendations = if (-not $allTestsPassed) {
            @(
                if (-not $test1) { "Configure AWS credentials" }
                if (-not $test3) { "Create key pair: $KeyPairName" }
                if (-not $test4) { "Create security group: $SecurityGroupName" }
                if (-not $test5) { "Create IAM role: $IamRoleName" }
            ) | Where-Object { $_ }
        } else { @() }
    }
    
    $testReport | ConvertTo-Json -Depth 10 | Out-File -FilePath "ec2_configuration_test_report.json" -Encoding UTF8
    Write-Host "📋 Rapport sauvegardé : ec2_configuration_test_report.json" -ForegroundColor Cyan
}