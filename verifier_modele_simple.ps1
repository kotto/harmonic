# Script simplifiÃ© pour vÃ©rifier le modÃ¨le sur AWS
# Version: 1.0

Write-Host "=== VÃ‰RIFICATION MODÃˆLE AWS HARMONIC AI ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host "Instance: __EC2_IP__" -ForegroundColor White
Write-Host "Utilisateur: ec2-user" -ForegroundColor White
Write-Host "ClÃ© SSH: $env:USERPROFILE\.ssh\deepseek_ec2" -ForegroundColor White
Write-Host ""

# VÃ©rifier si la clÃ© SSH existe
$sshKeyPath = "$env:USERPROFILE\.ssh\deepseek_ec2"
if (-not (Test-Path $sshKeyPath)) {
    Write-Host "ERREUR: ClÃ© SSH introuvable Ã  $sshKeyPath" -ForegroundColor Red
    Write-Host "Veuillez vÃ©rifier le chemin de la clÃ© SSH." -ForegroundColor Yellow
    exit 1
}

Write-Host "âœ… ClÃ© SSH trouvÃ©e: $sshKeyPath" -ForegroundColor Green

# Tester la connexion SSH
Write-Host "`n1. TEST DE CONNEXION SSH..." -ForegroundColor Cyan

try {
    $connectionTest = Test-NetConnection -ComputerName __EC2_IP__ -Port 22 -WarningAction SilentlyContinue
    if ($connectionTest.TcpTestSucceeded) {
        Write-Host "   âœ… Connexion SSH OK (port 22 ouvert)" -ForegroundColor Green
    } else {
        Write-Host "   âŒ Connexion SSH Ã©chouÃ©e" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   âš ï¸  Erreur lors du test de connexion: $_" -ForegroundColor Yellow
}

# Tester la connexion API
Write-Host "`n2. TEST DE CONNEXION API (port 8000)..." -ForegroundColor Cyan

try {
    $apiTest = Test-NetConnection -ComputerName __EC2_IP__ -Port 8000 -WarningAction SilentlyContinue
    if ($apiTest.TcpTestSucceeded) {
        Write-Host "   âœ… API accessible (port 8000 ouvert)" -ForegroundColor Green
    } else {
        Write-Host "   âŒ API non accessible" -ForegroundColor Red
    }
} catch {
    Write-Host "   âš ï¸  Erreur lors du test API: $_" -ForegroundColor Yellow
}

# Tester l'endpoint /health
Write-Host "`n3. TEST ENDPOINT /health..." -ForegroundColor Cyan

try {
    $healthResponse = Invoke-RestMethod -Uri "http://__EC2_IP__:8000/health" -TimeoutSec 10
    Write-Host "   âœ… Health check rÃ©ussi" -ForegroundColor Green
    Write-Host "   Status: $($healthResponse.status)" -ForegroundColor White
    Write-Host "   Version: $($healthResponse.version)" -ForegroundColor White
    
    if ($healthResponse.features) {
        Write-Host "   Features:" -ForegroundColor White
        $healthResponse.features.PSObject.Properties | ForEach-Object {
            Write-Host "     $($_.Name): $($_.Value)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   âŒ Health check Ã©chouÃ©: $_" -ForegroundColor Red
}

# Demander au modÃ¨le de s'identifier
Write-Host "`n4. IDENTIFICATION DU MODÃˆLE..." -ForegroundColor Cyan

$identifyPrompt = "Quel modÃ¨le d'IA es-tu ? Donne ton nom complet, ta version, et tes spÃ©cifications techniques."
$requestBody = @{
    prompt = $identifyPrompt
    max_tokens = 500
    temperature = 0.0
    arena_mode = $true
} | ConvertTo-Json

try {
    $modelResponse = Invoke-RestMethod -Uri "http://__EC2_IP__:8000/generate" `
        -Method Post `
        -Body $requestBody `
        -ContentType "application/json" `
        -TimeoutSec 30
    
    Write-Host "   âœ… RÃ©ponse reÃ§ue du modÃ¨le" -ForegroundColor Green
    Write-Host "   Version API: $($modelResponse.version)" -ForegroundColor White
    
    if ($modelResponse.backend_used) {
        Write-Host "   Backend utilisÃ©: $($modelResponse.backend_used)" -ForegroundColor White
    }
    
    # Afficher un extrait de la rÃ©ponse
    $contentPreview = $modelResponse.content.Substring(0, [Math]::Min(200, $modelResponse.content.Length))
    Write-Host "   Extrait rÃ©ponse: $contentPreview..." -ForegroundColor Gray
    
    # Analyser la rÃ©ponse pour identifier le modÃ¨le
    if ($modelResponse.content -match "Qwen.*DeepSeek.*V4.*Flash" -or $modelResponse.content -match "DeepSeek.*V4.*Flash.*Qwen") {
        Write-Host "   ðŸ” MODÃˆLE IDENTIFIÃ‰: Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf" -ForegroundColor Green
        Write-Host "   Architecture: Hybrid MoE avec 384 experts" -ForegroundColor White
        Write-Host "   Taille: 17.9 GB" -ForegroundColor White
    } elseif ($modelResponse.content -match "DeepSeek.*v3\.2") {
        Write-Host "   ðŸ” MODÃˆLE IDENTIFIÃ‰: DeepSeek v3.2" -ForegroundColor Yellow
        Write-Host "   ATTENTION: Ce n'est pas le modÃ¨le hybrid Qwen-DeepSeek-V4" -ForegroundColor Yellow
    } else {
        Write-Host "   ðŸ” MODÃˆLE: Impossible d'identifier prÃ©cisÃ©ment" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "   âŒ Ã‰chec de l'identification: $_" -ForegroundColor Red
}

# VÃ©rifier les processus via SSH (simplifiÃ©)
Write-Host "`n5. VÃ‰RIFICATION PROCESSUS (via SSH)..." -ForegroundColor Cyan

try {
    # Construire la commande SSH
    $sshCommand = "ssh -i `"$sshKeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@__EC2_IP__ 'ps aux | grep -E \"(qwen|deepseek|python.*api)\" | grep -v grep | head -5'"
    
    Write-Host "   ExÃ©cution: $sshCommand" -ForegroundColor Gray
    $processes = Invoke-Expression $sshCommand 2>$null
    
    if ($processes) {
        Write-Host "   âœ… Processus trouvÃ©s:" -ForegroundColor Green
        $processes -split "`n" | ForEach-Object {
            if ($_) {
                Write-Host "     $_" -ForegroundColor White
            }
        }
    } else {
        Write-Host "   âš ï¸  Aucun processus trouvÃ©" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   âš ï¸  Erreur lors de la vÃ©rification SSH: $_" -ForegroundColor Yellow
}

# RÃ©sumÃ©
Write-Host "`n=== RÃ‰SUMÃ‰ ===" -ForegroundColor Cyan

$summary = @{
    "Connexion SSH" = if ($connectionTest.TcpTestSucceeded) { "âœ… OK" } else { "âŒ Ã‰chec" }
    "API accessible" = if ($apiTest.TcpTestSucceeded) { "âœ… OK" } else { "âŒ Ã‰chec" }
    "Health check" = if ($healthResponse -and $healthResponse.status -eq "healthy") { "âœ… Healthy" } else { "âŒ Ã‰chec" }
    "ModÃ¨le identifiÃ©" = if ($modelResponse -and $modelResponse.content -match "Qwen.*DeepSeek.*V4") { "âœ… Qwen-DeepSeek-V4" } else { "âš ï¸  Incertain" }
}

foreach ($key in $summary.Keys) {
    Write-Host "$key : $($summary[$key])" -ForegroundColor White
}

# Conclusion
Write-Host "`n=== CONCLUSION ===" -ForegroundColor Cyan

if ($summary["Connexion SSH"] -eq "âœ… OK" -and $summary["API accessible"] -eq "âœ… OK") {
    Write-Host "âœ… L'instance AWS est opÃ©rationnelle" -ForegroundColor Green
    
    if ($summary["ModÃ¨le identifiÃ©"] -eq "âœ… Qwen-DeepSeek-V4") {
        Write-Host "âœ… ModÃ¨le correct: Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf" -ForegroundColor Green
        Write-Host "   Architecture hybrid avancÃ©e avec 384 experts MoE" -ForegroundColor White
        Write-Host "   Performance base estimÃ©e: 1460+ points LM Arena" -ForegroundColor White
    } else {
        Write-Host "âš ï¸  ModÃ¨le non identifiÃ© avec certitude" -ForegroundColor Yellow
        Write-Host "   VÃ©rification manuelle recommandÃ©e" -ForegroundColor Yellow
    }
} else {
    Write-Host "âŒ ProblÃ¨mes dÃ©tectÃ©s avec l'instance AWS" -ForegroundColor Red
}

Write-Host "`n=== RECOMMANDATIONS ===" -ForegroundColor Cyan
Write-Host "1. VÃ©rifier manuellement: ssh -i `"$sshKeyPath`" ec2-user@__EC2_IP__" -ForegroundColor White
Write-Host "2. Examiner: cat /opt/deepseek/api.py | grep -i model" -ForegroundColor White
Write-Host "3. Consulter logs: sudo journalctl -u deepseek-api | tail -50" -ForegroundColor White
Write-Host "4. Mettre Ã  jour la documentation avec les informations rÃ©elles" -ForegroundColor White

Write-Host "`nVÃ©rification terminÃ©e Ã  $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray