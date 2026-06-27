# Script simple pour vÃ©rifier l'Ã©tat AWS
# Harmonic AI - 15 Mai 2026

Write-Host "========================================"
Write-Host "VERIFICATION ETAT AWS HARMONIC AI"
Write-Host "========================================"
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# 1. Test de connexion Ã  l'instance AWS
Write-Host "1. TEST DE CONNEXION A L'INSTANCE AWS"
Write-Host "   Instance: __EC2_IP__"
Write-Host "   Ports testes: 22 (SSH), 8000 (API)"
Write-Host ""

# Test du port 22 (SSH)
Write-Host "   Port 22 (SSH): " -NoNewline
try {
    $tcpTest22 = Test-NetConnection -ComputerName __EC2_IP__ -Port 22 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($tcpTest22.TcpTestSucceeded) {
        Write-Host "ACCESSIBLE" -ForegroundColor Green
    } else {
        Write-Host "INACCESSIBLE" -ForegroundColor Red
    }
} catch {
    Write-Host "ERREUR DE TEST" -ForegroundColor Red
}

# Test du port 8000 (API)
Write-Host "   Port 8000 (API): " -NoNewline
try {
    $tcpTest8000 = Test-NetConnection -ComputerName __EC2_IP__ -Port 8000 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($tcpTest8000.TcpTestSucceeded) {
        Write-Host "ACCESSIBLE" -ForegroundColor Green
    } else {
        Write-Host "INACCESSIBLE" -ForegroundColor Red
    }
} catch {
    Write-Host "ERREUR DE TEST" -ForegroundColor Red
}

Write-Host ""

# 2. VÃ©rification des credentials AWS
Write-Host "2. VERIFICATION CREDENTIALS AWS"
try {
    $callerIdentity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Credentials AWS valides" -ForegroundColor Green
        $identity = $callerIdentity | ConvertFrom-Json
        Write-Host "   Compte: $($identity.Account)"
        Write-Host "   Utilisateur: $($identity.UserId)"
    } else {
        Write-Host "   Credentials AWS invalides ou manquants" -ForegroundColor Red
    }
} catch {
    Write-Host "   Erreur lors de la verification AWS" -ForegroundColor Red
}

Write-Host ""

# 3. RÃ©sumÃ©
Write-Host "3. RESUME"
Write-Host "========================================"

$instanceAccessible = $false
if ($tcpTest8000 -and $tcpTest8000.TcpTestSucceeded) {
    $instanceAccessible = $true
    Write-Host "   Instance AWS: ACCESSIBLE" -ForegroundColor Green
} else {
    Write-Host "   Instance AWS: INACCESSIBLE" -ForegroundColor Red
}

if ($callerIdentity -and $LASTEXITCODE -eq 0) {
    Write-Host "   Credentials AWS: VALIDES" -ForegroundColor Green
} else {
    Write-Host "   Credentials AWS: INVALIDES" -ForegroundColor Red
}

Write-Host ""

# 4. Recommandations
Write-Host "4. RECOMMANDATIONS"
Write-Host "========================================"

if (-not $instanceAccessible) {
    Write-Host "   - Verifier l'etat de l'instance via console AWS"
    Write-Host "   - Examiner les Security Groups (ports 22 et 8000)"
    Write-Host "   - Redemarrer l'instance si necessaire"
    Write-Host ""
    Write-Host "   ATTENTION: L'instance AWS est inaccessible"
    Write-Host "   Cela empeche les tests LM Arena et l'acces au dashboard"
    Write-Host "   Action requise: Diagnostic manuel via console AWS"
} else {
    Write-Host "   PRET POUR LES TESTS LM ARENA" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================"
Write-Host "SUPPORT HARMONIC AI"
Write-Host "========================================"
Write-Host "Pour assistance technique:"
Write-Host "- Console AWS: https://console.aws.amazon.com"
Write-Host "- Documentation: verification_modele_reel_aws.md"
Write-Host "- Tests LM Arena: lm_arena_test_final.py"