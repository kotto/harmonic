# ============================================================
# SCRIPT DE LIBERATION D'ESPACE DISQUE C: -> E:
# À exécuter en tant qu'ADMINISTRATEUR dans PowerShell
# ============================================================

$ErrorActionPreference = "Continue"
$logFile = "E:\nettoyage_C_log.txt"
$targetDrive = "E:"

function Log {
    param($msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$ts - $msg"
    Write-Host $line -ForegroundColor Cyan
    Add-Content -Path $logFile -Value $line
}

Log "========== DEBUT NETTOYAGE C: =========="
Log "Espace C: avant nettoyage :"
Get-PSDrive C | ForEach-Object { Log "C: Libre=$([math]::Round($_.Free/1GB,2)) Go / Total=$([math]::Round(($_.Used+$_.Free)/1GB,2)) Go" }

# ============================================================
# ÉTAPE 1 : NETTOYAGE FICHIERS TEMPORAIRES (SANS RISQUE)
# ============================================================
Write-Host "`n===== ÉTAPE 1: Nettoyage fichiers temporaires =====" -ForegroundColor Green

$tempPaths = @(
    "C:\Windows\Temp",
    "$env:TEMP",
    "C:\Windows\Prefetch",
    "C:\Windows\SoftwareDistribution\Download"
)

foreach ($path in $tempPaths) {
    if (Test-Path $path) {
        try {
            $before = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            Remove-Item "$path\*" -Recurse -Force -ErrorAction SilentlyContinue 2>$null
            $after = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            $freed = [math]::Round(($before - $after)/1MB, 1)
            Log "Nettoyé: $path -> $freed Mo libérés"
        } catch {
            Log "Erreur nettoyage $path : $_"
        }
    }
}

# Nettoyage disque Windows
try {
    Start-Process cleanmgr -ArgumentList "/sagerun:1" -Wait -NoNewWindow
    Log "Nettoyage disque Windows exécuté"
} catch {
    Log "Erreur cleanmgr: $_"
}

# Vider la corbeille
try {
    Clear-RecycleBin -Force -ErrorAction SilentlyContinue
    Log "Corbeille vidée"
} catch {
    Log "Erreur corbeille: $_"
}

# ============================================================
# ÉTAPE 2 : NETTOYAGE CACHES DÉVELOPPEMENT (C:\Users\maatc)
# ============================================================
Write-Host "`n===== ÉTAPE 2: Nettoyage caches développement =====" -ForegroundColor Green

$cachePaths = @(
    "$env:USERPROFILE\.cache",
    "$env:USERPROFILE\.npm\_cacache",
    "$env:USERPROFILE\.gradle\caches",
    "$env:USERPROFILE\.m2\repository",
    "$env:USERPROFILE\.cargo\registry\cache",
    "$env:USERPROFILE\AppData\Local\pip\cache",
    "$env:USERPROFILE\AppData\Local\Temp"
)

foreach ($path in $cachePaths) {
    if (Test-Path $path) {
        try {
            $before = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            Remove-Item "$path\*" -Recurse -Force -ErrorAction SilentlyContinue 2>$null
            $freed = [math]::Round($before/1GB, 2)
            Log "Cache nettoyé: $path -> $freed Go libérés"
        } catch {
            Log "Erreur cache $path : $_"
        }
    }
}

# ============================================================
# ÉTAPE 3 : DÉPLACER .ollama (modèles IA) VERS E:
# ============================================================
Write-Host "`n===== ÉTAPE 3: Déplacement .ollama vers E: =====" -ForegroundColor Green

$ollamaSrc = "$env:USERPROFILE\.ollama"
$ollamaDst = "$targetDrive\ollama_models"

if (Test-Path $ollamaSrc) {
    try {
        # Créer dossier cible
        New-Item -ItemType Directory -Path $ollamaDst -Force | Out-Null
        
        # Copier
        Log "Copie de .ollama vers $ollamaDst ..."
        robocopy "$ollamaSrc" "$ollamaDst" /E /MOVE /R:2 /W:5
        
        # Créer lien symbolique
        cmd /c mklink /J "$ollamaSrc" "$ollamaDst"
        Log ".ollama déplacé vers E: et jonction créée"
    } catch {
        Log "Erreur déplacement .ollama : $_"
    }
}

# ============================================================
# ÉTAPE 4 : DOCKER - DÉPLACER VERS E:
# ============================================================
Write-Host "`n===== ÉTAPE 4: Docker -> E: =====" -ForegroundColor Green

$dockerDataDefault = "$env:ProgramData\Docker"
$dockerDataNew = "$targetDrive\DockerData"

if (Test-Path $dockerDataDefault) {
    try {
        # Arrêter Docker si nécessaire
        net stop com.docker.service 2>$null
        net stop docker 2>$null
        
        New-Item -ItemType Directory -Path $dockerDataNew -Force | Out-Null
        
        # Copier les données Docker
        robocopy "$dockerDataDefault" "$dockerDataNew" /E /MOVE /R:2 /W:5
        
        # Créer la jonction
        cmd /c mklink /J "$dockerDataDefault" "$dockerDataNew"
        Log "Données Docker déplacées vers E:"
    } catch {
        Log "Erreur Docker: $_"
    }
}

# ============================================================
# ÉTAPE 5 : MONGODB - DÉPLACER DATA VERS E:
# ============================================================
Write-Host "`n===== ÉTAPE 5: MongoDB data -> E: =====" -ForegroundColor Green

$mongoDataDefault = "C:\data\db"
$mongoDataNew = "$targetDrive\MongoDB\data\db"

if (Test-Path $mongoDataDefault) {
    try {
        net stop MongoDB 2>$null
        New-Item -ItemType Directory -Path $mongoDataNew -Force | Out-Null
        robocopy "$mongoDataDefault" "$mongoDataNew" /E /MOVE /R:2 /W:5
        cmd /c mklink /J "$mongoDataDefault" "$mongoDataNew"
        Log "Données MongoDB déplacées vers E:"
    } catch {
        Log "Erreur MongoDB: $_"
    }
}

# ============================================================
# ÉTAPE 6 : POSTGRESQL - DÉPLACER DATA VERS E:
# ============================================================
Write-Host "`n===== ÉTAPE 6: PostgreSQL data -> E: =====" -ForegroundColor Green

$pgDataDefault = "C:\Program Files\PostgreSQL\*\data"
$pgDataNew = "$targetDrive\PostgreSQL\data"

$pgDataDir = Get-ChildItem "C:\Program Files\PostgreSQL\*\data" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pgDataDir) {
    try {
        net stop postgresql* 2>$null
        New-Item -ItemType Directory -Path $pgDataNew -Force | Out-Null
        robocopy $pgDataDir.FullName $pgDataNew /E /MOVE /R:2 /W:5
        cmd /c mklink /J $pgDataDir.FullName $pgDataNew
        Log "Données PostgreSQL déplacées vers E:"
    } catch {
        Log "Erreur PostgreSQL: $_"
    }
}

# ============================================================
# ÉTAPE 7 : DÉSACTIVER L'HIBERNATION (libère = taille RAM)
# ============================================================
Write-Host "`n===== ÉTAPE 7: Désactiver hibernation =====" -ForegroundColor Green
try {
    powercfg /h off
    Log "Hibernation désactivée (fichier hiberfil.sys supprimé)"
} catch {
    Log "Erreur désactivation hibernation: $_"
}

# ============================================================
# ÉTAPE 8 : DÉPLACER LE PAGEFILE SUR E:
# ============================================================
Write-Host "`n===== ÉTAPE 8: Pagefile sur E: =====" -ForegroundColor Green
try {
    # Régler pagefile: 2 Go min sur C:, le reste sur E:
    $computerSystem = Get-WmiObject Win32_ComputerSystem -EnableAllPrivileges
    $computerSystem.AutomaticManagedPagefile = $false
    $computerSystem.Put() | Out-Null
    
    $pageFileSettings = Get-WmiObject Win32_PageFileSetting
    if ($pageFileSettings) {
        $pageFileSettings.Delete() | Out-Null
    }
    
    # Pagefile 2 Go sur C:
    Set-WmiInstance -Class Win32_PageFileSetting -Arguments @{Name="C:\pagefile.sys"; InitialSize=2048; MaximumSize=4096}
    # Pagefile géré par système sur E:
    Set-WmiInstance -Class Win32_PageFileSetting -Arguments @{Name="E:\pagefile.sys"; InitialSize=0; MaximumSize=0}
    
    Log "Pagefile configuré: 2-4 Go sur C:, système géré sur E:"
    Log "!! REDÉMARRAGE NÉCESSAIRE pour appliquer le changement de pagefile !!"
} catch {
    Log "Erreur pagefile: $_"
}

# ============================================================
# ÉTAPE 9 : NETTOYAGE WINDOWS UPDATE (utilise la commande DISM)
# ============================================================
Write-Host "`n===== ÉTAPE 9: Nettoyage Windows Update =====" -ForegroundColor Green
try {
    # Nettoyer le cache Windows Update
    net stop wuauserv 2>$null
    Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
    net start wuauserv 2>$null
    
    # Nettoyer les composants inutilisés (DISM)
    Log "Exécution DISM cleanup..."
    Dism /online /Cleanup-Image /StartComponentCleanup /ResetBase /Quiet
    
    Log "Nettoyage Windows Update terminé"
} catch {
    Log "Erreur nettoyage Windows Update: $_"
}

# ============================================================
# ÉTAPE 10 : NETTOYAGE NPM, PIP, CARGO
# ============================================================
Write-Host "`n===== ÉTAPE 10: Nettoyage gestionnaires packages =====" -ForegroundColor Green

try { npm cache clean --force 2>$null; Log "Cache npm nettoyé" } catch { Log "npm: $_" }
try { pip cache purge 2>$null; Log "Cache pip nettoyé" } catch { Log "pip: $_" }
try { 
    if (Get-Command cargo -ErrorAction SilentlyContinue) {
        cargo cache remove 2>$null
        Log "Cache cargo nettoyé"
    }
} catch { Log "cargo: $_" }
try { docker system prune -a -f 2>$null; Log "Docker system prune exécuté" } catch { Log "docker: $_" }

# ============================================================
# ÉTAPE 11 : WSL - DÉPLACER VERS E:
# ============================================================
Write-Host "`n===== ÉTAPE 11: WSL -> E: =====" -ForegroundColor Green
try {
    wsl --shutdown 2>$null
    # Export et réimport WSL sur E:
    $wslDistros = wsl -l -q 2>$null
    foreach ($distro in $wslDistros) {
        if ($distro.Trim() -ne "") {
            $distroName = $distro.Trim()
            $exportPath = "$targetDrive\WSL\$distroName.tar"
            $importPath = "$targetDrive\WSL\$distroName"
            
            New-Item -ItemType Directory -Path (Split-Path $exportPath -Parent) -Force | Out-Null
            New-Item -ItemType Directory -Path $importPath -Force | Out-Null
            
            Log "Export WSL $distroName ..."
            wsl --export $distroName $exportPath
            wsl --unregister $distroName
            Log "Import WSL $distroName sur E: ..."
            wsl --import $distroName $importPath $exportPath
            Remove-Item $exportPath -Force
            Log "WSL $distroName déplacé vers E:"
        }
    }
} catch {
    Log "Erreur WSL: $_"
}

# ============================================================
# RÉSULTAT FINAL
# ============================================================
Write-Host "`n===== RESULTAT FINAL =====" -ForegroundColor Green
Log "========== NETTOYAGE TERMINE =========="
Log "Espace C: après nettoyage :"
Get-PSDrive C | ForEach-Object { Log "C: Libre=$([math]::Round($_.Free/1GB,2)) Go / Total=$([math]::Round(($_.Used+$_.Free)/1GB,2)) Go" }
Log "Espace E: après nettoyage :"
Get-PSDrive E | ForEach-Object { Log "E: Libre=$([math]::Round($_.Free/1GB,2)) Go / Total=$([math]::Round(($_.Used+$_.Free)/1GB,2)) Go" }

Write-Host "`n=========================================" -ForegroundColor Yellow
Write-Host "!! ACTIONS MANUELLES RECOMMANDÉES :" -ForegroundColor Yellow
Write-Host "1. REDÉMARRER le PC pour appliquer le pagefile" -ForegroundColor Yellow
Write-Host "2. Déplacer Documents/Images/Bureau vers E:\ (clic droit > Propriétés > Emplacement)" -ForegroundColor Yellow
Write-Host "3. Désinstaller les gros programmes peu utilisés de C: et les réinstaller sur E:" -ForegroundColor Yellow
Write-Host "4. Utiliser WinDirStat ou TreeSize pour trouver d'autres gros dossiers" -ForegroundColor Yellow
Write-Host "5. Dans Paramètres > Stockage > Nouveau contenu, mettre E: comme emplacement par défaut" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Yellow
Write-Host "`nJournal enregistré dans: $logFile" -ForegroundColor Green