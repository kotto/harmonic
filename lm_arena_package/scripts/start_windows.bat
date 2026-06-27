@echo off
REM ==============================================
REM  Démarrage du Package LM Arena - Windows
REM  Harmonic AI - L'IA Community-Proof
REM ==============================================

echo ==============================================
echo   Démarrage du Package LM Arena
echo   Harmonic AI - L'IA Community-Proof
echo ==============================================
echo.

REM ==============================================
REM ÉTAPE 1 : Vérification des prérequis
REM ==============================================

echo [*] Étape 1 : Vérification des prérequis

REM Vérifier l'environnement virtuel
if not exist ".\venv" (
    echo [i] Environnement virtuel introuvable. Exécutez d'abord .\scripts\install_windows.ps1
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
call .\venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo [i] Échec de l'activation de l'environnement virtuel
    pause
    exit /b 1
)
echo [+] Environnement virtuel activé

REM Vérifier les dépendances Python
echo [*] Vérification des dépendances Python...
python -c "
import sys
try:
    import fastapi
    import uvicorn
    import pydantic
    import sqlalchemy
    import redis
    import celery
    print('[+] Toutes les dépendances sont disponibles')
except ImportError as e:
    print(f'[i] Erreur: {e}')
    sys.exit(1)
"
if %ERRORLEVEL% neq 0 (
    echo [i] Échec de la vérification des dépendances Python
    pause
    exit /b 1
)

REM ==============================================
REM ÉTAPE 2 : Arrêt des services existants
REM ==============================================

echo [*] Étape 2 : Arrêt des services existants

REM Ports des services
set API_PORT=8000
set FRONTEND_PORT=8080
set AUDIO_SERVICE_PORT=9017
set VIDEO_SERVICE_PORT=9018
set MONITORING_PORT=9090

REM Arrêter les services existants sur les mêmes ports
echo [*] Arrêt des services existants sur les ports utilisés...

REM Fonction pour trouver et arrêter un processus sur un port
call :stop_process_on_port %API_PORT% "API Backend"
call :stop_process_on_port %FRONTEND_PORT% "Frontend"
call :stop_process_on_port %AUDIO_SERVICE_PORT% "Service Audio"
call :stop_process_on_port %VIDEO_SERVICE_PORT% "Service Vidéo"
call :stop_process_on_port %MONITORING_PORT% "Monitoring"

REM ==============================================
REM ÉTAPE 3 : Démarrage des services
REM ==============================================

echo [*] Étape 3 : Démarrage des services

REM Créer le répertoire des logs
if not exist "..\logs" mkdir "..\logs"
echo [+] Répertoire des logs créé

REM 3.1 Démarrage de l'API Backend
echo [*] Démarrage de l'API Backend (FastAPI)...
cd ..\backend
start "API Backend" /B python -m uvicorn main:app --host 0.0.0.0 --port %API_PORT% --reload > ..\logs\api.log 2>&1
timeout /t 3 /nobreak > nul
cd ..\scripts

REM Vérifier si l'API est en cours d'exécution
call :check_port %API_PORT% "API Backend"
if %ERRORLEVEL% equ 0 (
    echo [+] API Backend démarrée avec succès
) else (
    echo [i] Échec du démarrage de l'API Backend
)

REM 3.2 Démarrage des services harmoniques
echo [*] Démarrage des services harmoniques...

REM Service audio
echo [*] Démarrage du service audio...
cd ..\backend\services
start "Service Audio" /B python audio_service.py --port %AUDIO_SERVICE_PORT% > ..\..\logs\audio_service.log 2>&1
timeout /t 2 /nobreak > nul
cd ..\..\scripts

call :check_port %AUDIO_SERVICE_PORT% "Service Audio"
if %ERRORLEVEL% equ 0 (
    echo [+] Service audio démarré avec succès
) else (
    echo [!] Service audio non démarré (peut être désactivé)
)

REM Service vidéo
echo [*] Démarrage du service vidéo...
cd ..\backend\services
start "Service Vidéo" /B python video_service.py --port %VIDEO_SERVICE_PORT% > ..\..\logs\video_service.log 2>&1
timeout /t 2 /nobreak > nul
cd ..\..\scripts

call :check_port %VIDEO_SERVICE_PORT% "Service Vidéo"
if %ERRORLEVEL% equ 0 (
    echo [+] Service vidéo démarré avec succès
) else (
    echo [!] Service vidéo non démarré (peut être désactivé)
)

REM 3.3 Démarrage du frontend (simulé)
echo [*] Démarrage du frontend...
cd ..\frontend
start "Frontend" /B python -m http.server %FRONTEND_PORT% > ..\logs\frontend.log 2>&1
timeout /t 2 /nobreak > nul
cd ..\scripts

call :check_port %FRONTEND_PORT% "Frontend"
if %ERRORLEVEL% equ 0 (
    echo [+] Frontend démarré avec succès
) else (
    echo [!] Frontend non démarré (peut être désactivé)
)

REM 3.4 Démarrage du monitoring (simulé)
echo [*] Démarrage du monitoring...
cd ..\monitoring
start "Monitoring" /B python -m http.server %MONITORING_PORT% > ..\logs\monitoring.log 2>&1
timeout /t 2 /nobreak > nul
cd ..\scripts

call :check_port %MONITORING_PORT% "Monitoring"
if %ERRORLEVEL% equ 0 (
    echo [+] Monitoring démarré avec succès
) else (
    echo [!] Monitoring non démarré (peut être désactivé)
)

REM ==============================================
REM ÉTAPE 4 : Tests de connectivité
REM ==============================================

echo [*] Étape 4 : Tests de connectivité

REM Tester l'API
echo [*] Test de l'API Backend...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:%API_PORT%/health' -UseBasicParsing -TimeoutSec 5 | Out-Null; Write-Host '[+] API Backend répond correctement' -ForegroundColor Green } catch { Write-Host '[!] API Backend ne répond pas au test de santé' -ForegroundColor Yellow }"

REM Tester le frontend
echo [*] Test du frontend...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:%FRONTEND_PORT%' -UseBasicParsing -TimeoutSec 5 | Out-Null; Write-Host '[+] Frontend répond correctement' -ForegroundColor Green } catch { Write-Host '[!] Frontend ne répond pas' -ForegroundColor Yellow }"

REM ==============================================
REM ÉTAPE 5 : Finalisation
REM ==============================================

echo [*] Étape 5 : Finalisation

echo.
echo ✅ DÉMARRAGE TERMINÉ AVEC SUCCÈS !
echo.

echo 🌐 ACCÈS AUX SERVICES :
echo ======================
echo   • API Backend : http://localhost:%API_PORT%
echo   • Documentation API : http://localhost:%API_PORT%/docs
echo   • Frontend : http://localhost:%FRONTEND_PORT%
echo   • Monitoring : http://localhost:%MONITORING_PORT%
echo.

echo 📋 INFORMATIONS DE DÉBOGAGE :
echo =============================
echo   • Logs API : ..\logs\api.log
echo   • Logs Audio : ..\logs\audio_service.log
echo   • Logs Vidéo : ..\logs\video_service.log
echo   • Logs Frontend : ..\logs\frontend.log
echo   • Logs Monitoring : ..\logs\monitoring.log
echo.

echo 🔧 COMMANDES UTILES :
echo ====================
echo   • Arrêter tous les services : .\scripts\stop_windows.bat
echo   • Vérifier l'état : .\scripts\status_windows.bat
echo   • Redémarrer : .\scripts\restart_windows.bat
echo   • Tests LM Arena : .\scripts\test_lm_arena_windows.bat
echo.

echo 📞 SUPPORT :
echo ===========
echo   • Documentation : ..\docs\guides\
echo   • Problèmes : Consultez ..\docs\guides\checklist.md
echo   • Tests : .\scripts\final_check.bat
echo.

echo ==============================================
echo   Harmonic AI - L'IA Community-Proof
echo   Services démarrés avec succès ! 🚀
echo ==============================================

REM Désactiver l'environnement virtuel
deactivate

echo.
pause
exit /b 0

REM ==============================================
REM SOUS-ROUTINES
REM ==============================================

:stop_process_on_port
REM Arrête un processus sur un port spécifique
REM %1 = port, %2 = nom du service
setlocal
set PORT=%1
set SERVICE_NAME=%2

REM Utiliser netstat pour trouver le PID
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    set PID=%%a
)

if defined PID (
    echo [*] Arrêt du processus %PID% (%SERVICE_NAME% sur port %PORT%)
    taskkill /F /PID %PID% >nul 2>&1
    echo [+] Processus arrêté
) else (
    echo [-] Aucun processus trouvé sur le port %PORT% (%SERVICE_NAME%)
)
endlocal
exit /b 0

:check_port
REM Vérifie si un port est en écoute
REM %1 = port, %2 = nom du service
setlocal
set PORT=%1
set SERVICE_NAME=%2

REM Utiliser netstat pour vérifier le port
netstat -ano | findstr ":%PORT%" | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [+] %SERVICE_NAME% est en cours d'exécution sur le port %PORT%
    endlocal
    exit /b 0
) else (
    echo [-] %SERVICE_NAME% n'est pas en cours d'exécution sur le port %PORT%
    endlocal
    exit /b 1
)