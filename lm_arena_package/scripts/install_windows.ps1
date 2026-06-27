# ==============================================
#  Installation du Package LM Arena - Windows
#  Harmonic AI - L'IA Community-Proof
# ==============================================

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Installation du Package LM Arena" -ForegroundColor Cyan
Write-Host "  Harmonic AI - L'IA Community-Proof" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Fonction pour afficher les messages d'erreur
function Show-Error {
    param([string]$Message)
    Write-Host "[i] $Message" -ForegroundColor Red
    exit 1
}

# Fonction pour afficher les messages de succès
function Show-Success {
    param([string]$Message)
    Write-Host "[+] $Message" -ForegroundColor Green
}

# Fonction pour afficher les messages d'information
function Show-Info {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Yellow
}

# ==============================================
# ÉTAPE 1 : Vérification des prérequis
# ==============================================

Show-Info "Étape 1 : Vérification des prérequis"

# Vérifier Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Show-Error "Python n'est pas installé ou n'est pas dans le PATH"
}
Show-Success "Python trouvé : $pythonVersion"

# Vérifier pip
$pipVersion = pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Show-Error "pip n'est pas installé ou n'est pas dans le PATH"
}
Show-Success "pip trouvé : $($pipVersion.Split(' ')[1])"

# Vérifier Git
$gitVersion = git --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Show-Warning "Git n'est pas installé (recommandé pour les mises à jour)"
} else {
    Show-Success "Git trouvé : $($gitVersion.Split(' ')[2])"
}

# ==============================================
# ÉTAPE 2 : Création de l'environnement virtuel
# ==============================================

Show-Info "Étape 2 : Création de l'environnement virtuel"

$venvPath = ".\venv"
if (Test-Path $venvPath) {
    Show-Info "Environnement virtuel existant détecté, suppression..."
    Remove-Item -Path $venvPath -Recurse -Force
}

# Créer l'environnement virtuel
python -m venv $venvPath
if ($LASTEXITCODE -ne 0) {
    Show-Error "Échec de la création de l'environnement virtuel"
}
Show-Success "Environnement virtuel créé : $venvPath"

# ==============================================
# ÉTAPE 3 : Activation et installation des dépendances
# ==============================================

Show-Info "Étape 3 : Activation et installation des dépendances"

# Activer l'environnement virtuel
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Show-Error "Script d'activation introuvable : $activateScript"
}

# Exécuter l'activation dans un nouveau processus
& $activateScript

# Mettre à jour pip
Show-Info "Mise à jour de pip..."
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Show-Error "Échec de la mise à jour de pip"
}
Show-Success "pip mis à jour avec succès"

# Installer les dépendances
Show-Info "Installation des dépendances depuis requirements.txt..."
if (Test-Path "..\config\requirements.txt") {
    pip install -r "..\config\requirements.txt"
} elseif (Test-Path "requirements.txt") {
    pip install -r "requirements.txt"
} else {
    Show-Error "Fichier requirements.txt introuvable"
}

if ($LASTEXITCODE -ne 0) {
    Show-Error "Échec de l'installation des dépendances"
}
Show-Success "Dépendances installées avec succès"

# ==============================================
# ÉTAPE 4 : Configuration de l'environnement
# ==============================================

Show-Info "Étape 4 : Configuration de l'environnement"

# Créer le fichier .env à partir de l'exemple
$envExample = "..\config\.env.example"
$envFile = "..\config\.env"

if (Test-Path $envExample) {
    if (-not (Test-Path $envFile)) {
        Copy-Item $envExample $envFile
        Show-Success "Fichier .env créé à partir de l'exemple"
        
        # Demander à l'utilisateur de configurer les clés API
        Write-Host ""
        Write-Host "⚠️  IMPORTANT : Configurez vos clés API dans le fichier :" -ForegroundColor Yellow
        Write-Host "   $((Get-Item $envFile).FullName)" -ForegroundColor White
        Write-Host ""
        Write-Host "Variables à configurer :" -ForegroundColor Cyan
        Write-Host "  - API_KEY : Votre clé API pour l'authentification" -ForegroundColor Gray
        Write-Host "  - DEEPSEEK_API_KEY : Clé pour l'API DeepSeek (optionnel)" -ForegroundColor Gray
        Write-Host "  - AWS_ACCESS_KEY_ID : Identifiant AWS (pour déploiement)" -ForegroundColor Gray
        Write-Host "  - AWS_SECRET_ACCESS_KEY : Clé secrète AWS" -ForegroundColor Gray
        Write-Host ""
    } else {
        Show-Info "Fichier .env existe déjà, conservation"
    }
} else {
    Show-Warning "Fichier .env.example introuvable, création manuelle nécessaire"
}

# ==============================================
# ÉTAPE 5 : Initialisation de la base de données
# ==============================================

Show-Info "Étape 5 : Initialisation de la base de données"

# Vérifier si Docker est disponible pour la base de données
$dockerAvailable = $false
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerAvailable = $true
        Show-Success "Docker trouvé : $($dockerVersion.Split(' ')[2])"
    }
} catch {
    Show-Warning "Docker non disponible, base de données locale recommandée"
}

if ($dockerAvailable) {
    Show-Info "Démarrage des services avec Docker Compose..."
    
    $dockerComposeFile = "..\config\docker-compose.yml"
    if (Test-Path $dockerComposeFile) {
        # Démarrer les services en arrière-plan
        docker-compose -f $dockerComposeFile up -d
        if ($LASTEXITCODE -ne 0) {
            Show-Warning "Échec du démarrage Docker Compose, vérification manuelle nécessaire"
        } else {
            Show-Success "Services Docker démarrés avec succès"
            
            # Attendre que les services soient prêts
            Show-Info "Attente de la disponibilité des services..."
            Start-Sleep -Seconds 10
        }
    } else {
        Show-Warning "Fichier docker-compose.yml introuvable"
    }
}

# ==============================================
# ÉTAPE 6 : Vérification de l'installation
# ==============================================

Show-Info "Étape 6 : Vérification de l'installation"

# Vérifier les imports Python
Show-Info "Vérification des imports Python..."
$testScript = @"
import sys
sys.path.insert(0, '..\backend')

try:
    import fastapi
    import uvicorn
    import pydantic
    import sqlalchemy
    import redis
    import celery
    print("SUCCESS: Toutes les dépendances sont importables")
except ImportError as e:
    print(f"ERROR: Import échoué: {e}")
    sys.exit(1)
"@

$testScript | Out-File -FilePath "test_imports.py" -Encoding UTF8
python test_imports.py
if ($LASTEXITCODE -ne 0) {
    Show-Error "Échec des imports Python"
}
Remove-Item "test_imports.py" -Force
Show-Success "Toutes les dépendances Python sont importables"

# ==============================================
# ÉTAPE 7 : Finalisation
# ==============================================

Show-Info "Étape 7 : Finalisation"

Write-Host ""
Write-Host "✅ INSTALLATION TERMINÉE AVEC SUCCÈS !" -ForegroundColor Green
Write-Host ""

Write-Host "📋 RÉSUMÉ DE L'INSTALLATION :" -ForegroundColor Cyan
Write-Host "  • Python : $($pythonVersion.Split(' ')[1])" -ForegroundColor Gray
Write-Host "  • Environnement virtuel : $venvPath" -ForegroundColor Gray
Write-Host "  • Dépendances : Installées avec succès" -ForegroundColor Gray
if ($dockerAvailable) {
    Write-Host "  • Services Docker : Démarrés" -ForegroundColor Gray
}
Write-Host ""

Write-Host "🚀 POUR DÉMARRER LES SERVICES :" -ForegroundColor Cyan
Write-Host "  1. Exécutez : .\scripts\start_windows.bat" -ForegroundColor White
Write-Host "  2. Ou exécutez : .\scripts\start_all.bat" -ForegroundColor White
Write-Host ""

Write-Host "🌐 ACCÈS AUX SERVICES :" -ForegroundColor Cyan
Write-Host "  • API Backend : http://localhost:8000" -ForegroundColor White
Write-Host "  • Documentation API : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Frontend : http://localhost:8080" -ForegroundColor White
Write-Host "  • Monitoring : http://localhost:9090" -ForegroundColor White
Write-Host ""

Write-Host "🔧 CONFIGURATION MANUELLE :" -ForegroundColor Yellow
Write-Host "  • Modifiez le fichier .env pour configurer vos clés API" -ForegroundColor Gray
Write-Host "  • Consultez docs/guides/ pour la documentation complète" -ForegroundColor Gray
Write-Host ""

Write-Host "📞 SUPPORT :" -ForegroundColor Cyan
Write-Host "  • Documentation : docs/guides/" -ForegroundColor Gray
Write-Host "  • Tests : .\scripts\final_check.bat" -ForegroundColor Gray
Write-Host "  • Problèmes : Consultez docs/guides/checklist.md" -ForegroundColor Gray
Write-Host ""

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Harmonic AI - L'IA Community-Proof" -ForegroundColor Cyan
Write-Host "  Prêt pour LM Arena ! 🏆" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan