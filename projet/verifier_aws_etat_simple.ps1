# Script de vÃ©rification simplifiÃ© de l'Ã©tat AWS et du modÃ¨le S3
# Harmonic AI - 15 Mai 2026

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "ðŸ” VÃ‰RIFICATION Ã‰TAT AWS HARMONIC AI" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# 1. VÃ©rification de la connexion Ã  l'instance AWS
Write-Host "1ï¸âƒ£  TEST DE CONNEXION Ã€ L'INSTANCE AWS" -ForegroundColor Green
Write-Host "   Instance: __EC2_IP__" -ForegroundColor Gray
Write-Host "   Ports testÃ©s: 22 (SSH), 8000 (API)" -ForegroundColor Gray
Write-Host ""

# Test du port 22 (SSH)
Write-Host "   Port 22 (SSH): " -NoNewline
try {
    $tcpTest = Test-NetConnection -ComputerName __EC2_IP__ -Port 22 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($tcpTest.TcpTestSucceeded) {
        Write-Host "âœ… ACCESSIBLE" -ForegroundColor Green
    } else {
        Write-Host "âŒ INACCESSIBLE" -ForegroundColor Red
    }
} catch {
    Write-Host "âŒ ERREUR DE TEST" -ForegroundColor Red
}

# Test du port 8000 (API)
Write-Host "   Port 8000 (API): " -NoNewline
try {
    $tcpTest = Test-NetConnection -ComputerName __EC2_IP__ -Port 8000 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($tcpTest.TcpTestSucceeded) {
        Write-Host "âœ… ACCESSIBLE" -ForegroundColor Green
    } else {
        Write-Host "âŒ INACCESSIBLE" -ForegroundColor Red
    }
} catch {
    Write-Host "âŒ ERREUR DE TEST" -ForegroundColor Red
}

Write-Host ""

# 2. VÃ©rification des credentials AWS
Write-Host "2ï¸âƒ£  VÃ‰RIFICATION CREDENTIALS AWS" -ForegroundColor Green
try {
    $callerIdentity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   âœ… Credentials AWS valides" -ForegroundColor Green
        $identity = $callerIdentity | ConvertFrom-Json
        Write-Host "   Compte: $($identity.Account)" -ForegroundColor Gray
        Write-Host "   Utilisateur: $($identity.UserId)" -ForegroundColor Gray
    } else {
        Write-Host "   âŒ Credentials AWS invalides ou manquants" -ForegroundColor Red
        Write-Host "   Message: $callerIdentity" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   âŒ Erreur lors de la vÃ©rification AWS" -ForegroundColor Red
}

Write-Host ""

# 3. VÃ©rification du modÃ¨le sur S3
Write-Host "3ï¸âƒ£  VÃ‰RIFICATION MODÃˆLE S3" -ForegroundColor Green
Write-Host "   Bucket: deepseek-models-326095712935" -ForegroundColor Gray
Write-Host "   Chemin: deepseek-v4-pro/" -ForegroundColor Gray
Write-Host "   ModÃ¨le attendu: Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf" -ForegroundColor Gray
Write-Host ""

try {
    # VÃ©rifier si le bucket existe
    Write-Host "   VÃ©rification bucket... " -NoNewline
    $bucketCheck = aws s3api head-bucket --bucket deepseek-models-326095712935 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "âœ… EXISTE" -ForegroundColor Green
        
        # Lister les fichiers dans le bucket
        Write-Host "   Liste des fichiers... " -NoNewline
        $files = aws s3 ls s3://deepseek-models-326095712935/deepseek-v4-pro/ --recursive 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "âœ… DISPONIBLE" -ForegroundColor Green
            Write-Host ""
            Write-Host "   Fichiers trouvÃ©s:" -ForegroundColor Gray
            
            # Afficher les fichiers principaux
            $fileCount = 0
            $files | ForEach-Object {
                if ($fileCount -lt 10) {  # Limiter Ã  10 fichiers pour la lisibilitÃ©
                    Write-Host "   - $_" -ForegroundColor Gray
                }
                $fileCount++
            }
            
            Write-Host ""
            Write-Host "   Total fichiers: $fileCount" -ForegroundColor Gray
            
            # VÃ©rifier la prÃ©sence de fichiers clÃ©s
            $hasConfig = $files -match "config\.json"
            $hasWeights = $files -match "\.safetensors|\.gguf"
            
            Write-Host ""
            Write-Host "   Fichiers clÃ©s:" -ForegroundColor Gray
            if ($hasConfig) {
                Write-Host "   âœ… config.json prÃ©sent" -ForegroundColor Green
            } else {
                Write-Host "   âŒ config.json manquant" -ForegroundColor Red
            }
            
            if ($hasWeights) {
                Write-Host "   âœ… Fichiers de poids prÃ©sents" -ForegroundColor Green
            } else {
                Write-Host "   âŒ Fichiers de poids manquants" -ForegroundColor Red
            }
            
        } else {
            Write-Host "âŒ ERREUR DE LISTE" -ForegroundColor Red
            Write-Host "   Message: $files" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "âŒ N'EXISTE PAS" -ForegroundColor Red
        Write-Host "   Message: $bucketCheck" -ForegroundColor Yellow
    }
} catch {
    Write-Host "âŒ ERREUR DE VÃ‰RIFICATION S3" -ForegroundColor Red
}

Write-Host ""

# 4. RÃ©sumÃ© et recommandations
Write-Host "4ï¸âƒ£  RÃ‰SUMÃ‰ ET RECOMMANDATIONS" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "ðŸ“Š Ã‰TAT ACTUEL:" -ForegroundColor Yellow

# Ã‰valuation de l'Ã©tat
$instanceAccessible = $false
$awsCredentialsValid = $false
$s3BucketExists = $false

# DÃ©terminer l'Ã©tat
if ($tcpTest8000 -and $tcpTest8000.TcpTestSucceeded) {
    $instanceAccessible = $true
    Write-Host "   Instance AWS: âœ… ACCESSIBLE" -ForegroundColor Green
} else {
    Write-Host "   Instance AWS: âŒ INACCESSIBLE" -ForegroundColor Red
}

if ($callerIdentity -and $LASTEXITCODE -eq 0) {
    $awsCredentialsValid = $true
    Write-Host "   Credentials AWS: âœ… VALIDES" -ForegroundColor Green
} else {
    Write-Host "   Credentials AWS: âŒ INVALIDES" -ForegroundColor Red
}

if ($bucketCheck -and $LASTEXITCODE -eq 0) {
    $s3BucketExists = $true
    Write-Host "   Bucket S3: âœ… EXISTE" -ForegroundColor Green
} else {
    Write-Host "   Bucket S3: âŒ N'EXISTE PAS" -ForegroundColor Red
}

Write-Host ""

# Recommandations
Write-Host "ðŸš€ RECOMMANDATIONS:" -ForegroundColor Yellow

if (-not $instanceAccessible) {
    Write-Host "   1. VÃ©rifier l'Ã©tat de l'instance via console AWS" -ForegroundColor Gray
    Write-Host "   2. Examiner les Security Groups (ports 22 et 8000)" -ForegroundColor Gray
    Write-Host "   3. RedÃ©marrer l'instance si nÃ©cessaire" -ForegroundColor Gray
}

if (-not $awsCredentialsValid) {
    Write-Host "   4. Configurer les credentials AWS avec: aws configure" -ForegroundColor Gray
}

if (-not $s3BucketExists) {
    Write-Host "   5. VÃ©rifier le nom du bucket S3 ou les permissions" -ForegroundColor Gray
}

if ($instanceAccessible -and $awsCredentialsValid -and $s3BucketExists) {
    Write-Host "   âœ… Tous les systÃ¨mes sont opÃ©rationnels!" -ForegroundColor Green
    Write-Host "   Prochaine Ã©tape: ExÃ©cuter les tests LM Arena" -ForegroundColor Gray
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "ðŸ“ž SUPPORT HARMONIC AI" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Pour assistance technique:" -ForegroundColor Gray
Write-Host "- Console AWS: https://console.aws.amazon.com" -ForegroundColor Gray
Write-Host "- Documentation: verification_modele_reel_aws.md" -ForegroundColor Gray
Write-Host "- Tests LM Arena: lm_arena_test_final.py" -ForegroundColor Gray
Write-Host ""

# Message final
if (-not $instanceAccessible) {
    Write-Host "ATTENTION: L'instance AWS est inaccessible" -ForegroundColor Red
    Write-Host "   Cela empeche les tests LM Arena et l'acces au dashboard" -ForegroundColor Yellow
    Write-Host "   Action requise: Diagnostic manuel via console AWS" -ForegroundColor Yellow
} else {
    Write-Host "PRET POUR LES TESTS LM ARENA" -ForegroundColor Green
}

Write-Host ""