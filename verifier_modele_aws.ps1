# Script de VÃ©rification du ModÃ¨le RÃ©el sur AWS Instance
# Auteur : Harmonic AI
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$InstanceIP = "__EC2_IP__",
    [string]$SSHKeyPath = "$env:USERPROFILE\.ssh\deepseek_ec2",
    [string]$SSHUser = "ec2-user",
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# Fonctions de logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = @{
        "INFO" = "White"
        "SUCCESS" = "Green"
        "WARNING" = "Yellow"
        "ERROR" = "Red"
        "DEBUG" = "Gray"
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color[$Level]
}

function Test-SSHConnection {
    param([string]$HostIP, [int]$Port = 22)
    
    Write-Log "Test de connexion SSH Ã  ${HostIP}:${Port}..." "INFO"
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $result = $tcpClient.BeginConnect($HostIP, $Port, $null, $null)
        $wait = $result.AsyncWaitHandle.WaitOne(5000, $false)
        
        if ($wait -and $tcpClient.Connected) {
            $tcpClient.EndConnect($result)
            $tcpClient.Close()
            Write-Log "Connexion SSH OK" "SUCCESS"
            return $true
        } else {
            $tcpClient.Close()
            Write-Log "Connexion SSH Ã©chouÃ©e (timeout)" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Erreur de connexion SSH: $_" "ERROR"
        return $false
    }
}

function Execute-SSHCommand {
    param(
        [string]$HostIP,
        [string]$User,
        [string]$KeyPath,
        [string]$Command
    )
    
    Write-Log "ExÃ©cution de commande SSH: $Command" "DEBUG"
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Commande SSH: ssh -i `"$KeyPath`" $User@$HostIP `"$Command`"" "INFO"
        return "DRY_RUN"
    }
    
    try {
        # Utilisation de plink (PuTTY) pour une meilleure gestion SSH sous Windows
        if (Test-Path "C:\Program Files\PuTTY\plink.exe") {
            $plinkPath = "C:\Program Files\PuTTY\plink.exe"
            $args = "-i", "`"$KeyPath`"", "-ssh", "$User@$HostIP", "`"$Command`""
            $result = & $plinkPath $args 2>&1
        } else {
            # Fallback Ã  ssh natif
            $result = ssh -i "`"$KeyPath`"" ${User}@${HostIP} "`"$Command`"" 2>&1
        }
        
        return $result -join "`n"
    } catch {
        Write-Log "Erreur lors de l'exÃ©cution SSH: $_" "ERROR"
        return $null
    }
}

# Main execution
Write-Log "=== VÃ‰RIFICATION MODÃˆLE AWS HARMONIC AI ===" "INFO"
Write-Log "Instance: $InstanceIP" "INFO"
Write-Log "Utilisateur SSH: $SSHUser" "INFO"
Write-Log "ClÃ© SSH: $SSHKeyPath" "INFO"

# VÃ©rifier que la clÃ© SSH existe
if (-not (Test-Path $SSHKeyPath)) {
    Write-Log "ERREUR: ClÃ© SSH introuvable Ã  $SSHKeyPath" "ERROR"
    Write-Log "Veuillez vÃ©rifier le chemin de la clÃ© SSH." "INFO"
    exit 1
}

# Tester la connexion SSH
if (-not (Test-SSHConnection -HostIP $InstanceIP)) {
    Write-Log "Impossible de se connecter Ã  l'instance AWS." "ERROR"
    exit 1
}

Write-Log "Connexion SSH Ã©tablie avec succÃ¨s." "SUCCESS"

# 1. VÃ©rifier les processus en cours
Write-Log "`n1. VÃ‰RIFICATION DES PROCESSUS EN COURS" "INFO"

$processes = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "ps aux | grep -E '(qwen|deepseek|python|api)' | grep -v grep"
if ($processes) {
    Write-Log "Processus trouvÃ©s:" "INFO"
    $processes -split "`n" | ForEach-Object { Write-Log "  $_" "INFO" }
} else {
    Write-Log "Aucun processus trouvÃ©." "WARNING"
}

# 2. VÃ©rifier le service systemd
Write-Log "`n2. VÃ‰RIFICATION DU SERVICE SYSTEMD" "INFO"

$serviceStatus = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "sudo systemctl status deepseek-api 2>/dev/null || echo 'Service non trouvÃ©'"
Write-Log "Status du service deepseek-api:" "INFO"
$serviceStatus -split "`n" | ForEach-Object { Write-Log "  $_" "INFO" }

# 3. VÃ©rifier le fichier API
Write-Log "`n3. VÃ‰RIFICATION DU FICHIER API" "INFO"

$apiFile = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "ls -la /opt/deepseek/ 2>/dev/null || echo 'RÃ©pertoire /opt/deepseek/ non trouvÃ©'"
Write-Log "Contenu de /opt/deepseek/:" "INFO"
$apiFile -split "`n" | ForEach-Object { Write-Log "  $_" "INFO" }

# 4. VÃ©rifier le contenu du fichier API
Write-Log "`n4. CONTENU DU FICHIER API" "INFO"

$apiContent = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "head -100 /opt/deepseek/api.py 2>/dev/null || echo 'Fichier /opt/deepseek/api.py non trouvÃ©'"
Write-Log "Extrait du fichier API:" "INFO"
$apiContent -split "`n" | ForEach-Object { Write-Log "  $_" "INFO" }

# 5. Rechercher des rÃ©fÃ©rences Ã  Qwen ou DeepSeek
Write-Log "`n5. RECHERCHE DE RÃ‰FÃ‰RENCES AU MODÃˆLE" "INFO"

$modelRefs = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "grep -i -E '(qwen|deepseek|model.*name|model.*path)' /opt/deepseek/api.py 2>/dev/null | head -20"
if ($modelRefs) {
    Write-Log "RÃ©fÃ©rences au modÃ¨le trouvÃ©es:" "INFO"
    $modelRefs -split "`n" | ForEach-Object { Write-Log "  $_" "INFO" }
} else {
    Write-Log "Aucune rÃ©fÃ©rence explicite au modÃ¨le trouvÃ©e." "WARNING"
}

# 6. VÃ©rifier les fichiers de modÃ¨le
Write-Log "`n6. RECHERCHE DE FICHIERS DE MODÃˆLE" "INFO"

$modelFiles = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "find / -name '*.gguf' -type f 2>/dev/null | head -10"
if ($modelFiles) {
    Write-Log "Fichiers GGUF trouvÃ©s:" "INFO"
    $modelFiles -split "`n" | ForEach-Object { 
        if ($_) {
            $size = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "ls -lh `"$_`" 2>/dev/null | awk '{print \$5}'"
            Write-Log "  $_ ($size)" "INFO"
        }
    }
} else {
    Write-Log "Aucun fichier GGUF trouvÃ©." "WARNING"
}

# 7. VÃ©rifier les variables d'environnement
Write-Log "`n7. VARIABLES D'ENVIRONNEMENT" "INFO"

$envVars = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "printenv | grep -E '(MODEL|DEEPSEEK|QWEN|HARMONIC)' | sort"
if ($envVars) {
    Write-Log "Variables d'environnement pertinentes:" "INFO"
    $envVars -split "`n" | ForEach-Object { Write-Log "  $_" "INFO" }
} else {
    Write-Log "Aucune variable d'environnement pertinente trouvÃ©e." "WARNING"
}

# 8. Tester l'API directement
Write-Log "`n8. TEST DE L'API DIRECT" "INFO"

$healthTest = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command "curl -s http://localhost:8000/health 2>/dev/null || echo 'API non accessible'"
if ($healthTest -and $healthTest -ne "DRY_RUN") {
    try {
        $healthJson = $healthTest | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($healthJson) {
            Write-Log "Health check rÃ©ussi:" "SUCCESS"
            Write-Log "  Status: $($healthJson.status)" "INFO"
            Write-Log "  Version: $($healthJson.version)" "INFO"
            Write-Log "  Features: $($healthJson.features | ConvertTo-Json -Compress)" "INFO"
        } else {
            Write-Log "RÃ©ponse Health: $healthTest" "INFO"
        }
    } catch {
        Write-Log "RÃ©ponse Health (raw): $healthTest" "INFO"
    }
} else {
    Write-Log "API non accessible." "WARNING"
}

# 9. Demander au modÃ¨le de s'identifier
Write-Log "`n9. IDENTIFICATION DU MODÃˆLE" "INFO"

$identifyPrompt = "Quel modÃ¨le d'IA es-tu ? Donne ton nom complet, ta version, et tes spÃ©cifications techniques."
$identifyCommand = "curl -s -X POST http://localhost:8000/generate -H 'Content-Type: application/json' -d '{\"prompt\": \"$identifyPrompt\", \"max_tokens\": 500, \"temperature\": 0.0}' 2>/dev/null || echo 'Ã‰chec de la requÃªte'"

$modelResponse = Execute-SSHCommand -HostIP $InstanceIP -User $SSHUser -KeyPath $SSHKeyPath -Command $identifyCommand
if ($modelResponse -and $modelResponse -ne "DRY_RUN" -and $modelResponse -notmatch "Ã‰chec") {
    try {
        $responseJson = $modelResponse | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($responseJson) {
            Write-Log "RÃ©ponse du modÃ¨le:" "SUCCESS"
            Write-Log "  Contenu: $($responseJson.content.Substring(0, [Math]::Min(200, $responseJson.content.Length)))..." "INFO"
            Write-Log "  Version: $($responseJson.version)" "INFO"
            if ($responseJson.backend_used) {
                Write-Log "  Backend: $($responseJson.backend_used)" "INFO"
            }
        } else {
            Write-Log "RÃ©ponse (raw): $modelResponse" "INFO"
        }
    } catch {
        Write-Log "RÃ©ponse (raw): $modelResponse" "INFO"
    }
} else {
    Write-Log "Impossible d'obtenir une rÃ©ponse du modÃ¨le." "WARNING"
}

Write-Log "`n=== RÃ‰SUMÃ‰ DE LA VÃ‰RIFICATION ===" "INFO"

# Analyse des rÃ©sultats
$summary = @{
    "Connexion SSH" = if (Test-SSHConnection -HostIP $InstanceIP) { "âœ… OK" } else { "âŒ Ã‰chec" }
    "Service actif" = if ($serviceStatus -match "active.*running") { "âœ… Actif" } else { "âš ï¸ Inactif ou erreur" }
    "Fichier API" = if ($apiFile -match "api\.py") { "âœ… PrÃ©sent" } else { "âŒ Absent" }
    "RÃ©fÃ©rences modÃ¨le" = if ($modelRefs -match "(qwen|deepseek)") { "âœ… TrouvÃ©es" } else { "âš ï¸ Non trouvÃ©es" }
    "Fichiers GGUF" = if ($modelFiles -match "\.gguf") { "âœ… PrÃ©sents" } else { "âš ï¸ Absents" }
    "Health API" = if ($healthTest -match '"status":"healthy"') { "âœ… Healthy" } else { "âš ï¸ ProblÃ¨me" }
}

foreach ($key in $summary.Keys) {
    Write-Log "$key : $($summary[$key])" "INFO"
}

# Conclusion
Write-Log "`n=== CONCLUSION ===" "INFO"

if ($summary["Connexion SSH"] -eq "âœ… OK" -and $summary["Health API"] -eq "âœ… Healthy") {
    Write-Log "L'instance AWS est opÃ©rationnelle et l'API fonctionne." "SUCCESS"
    
    if ($summary["RÃ©fÃ©rences modÃ¨le"] -eq "âœ… TrouvÃ©es") {
        Write-Log "Le modÃ¨le semble Ãªtre correctement rÃ©fÃ©rencÃ©." "SUCCESS"
        
        # Essayer d'identifier le modÃ¨le spÃ©cifique
        if ($modelRefs -match "qwen.*deepseek.*v4.*flash" -or $modelRefs -match "deepseek.*v4.*flash.*qwen") {
            Write-Log "MODÃˆLE IDENTIFIÃ‰: Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf" "SUCCESS"
            Write-Log "C'est le modÃ¨le hybrid avancÃ© avec 384 experts MoE." "INFO"
        } elseif ($modelRefs -match "deepseek.*v3\.2") {
            Write-Log "MODÃˆLE IDENTIFIÃ‰: DeepSeek v3.2 (version de base)" "WARNING"
            Write-Log "Ce n'est pas le modÃ¨le hybrid Qwen-DeepSeek-V4." "WARNING"
        } else {
            Write-Log "MODÃˆLE: RÃ©fÃ©rences trouvÃ©es mais identification prÃ©cise impossible." "INFO"
        }
    } else {
        Write-Log "ATTENTION: Aucune rÃ©fÃ©rence explicite au modÃ¨le trouvÃ©e." "WARNING"
        Write-Log "Le modÃ¨le rÃ©ellement utilisÃ© n'est pas clair." "WARNING"
    }
} else {
    Write-Log "PROBLÃˆME: L'instance AWS ou l'API a des problÃ¨mes." "ERROR"
}

Write-Log "`n=== RECOMMANDATIONS ===" "INFO"
Write-Log "1. VÃ©rifier manuellement le fichier /opt/deepseek/api.py" "INFO"
Write-Log "2. Examiner les logs du service: sudo journalctl -u deepseek-api" "INFO"
Write-Log "3. Tester une requÃªte complÃ¨te avec un prompt spÃ©cifique" "INFO"
Write-Log "4. Mettre Ã  jour la documentation avec les informations rÃ©elles" "INFO"

Write-Log "`nVÃ©rification terminÃ©e Ã  $(Get-Date -Format 'HH:mm:ss')" "INFO"