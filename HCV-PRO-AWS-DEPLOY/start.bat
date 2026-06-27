@echo off
REM Script de démarrage HCV-PRO-PROJECT pour Windows
REM Vérifie les dépendances et lance le serveur

echo.
echo ============================================================
echo   HCV PRO - Plateforme de Compression Multimédia
echo ============================================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://www.python.org
    pause
    exit /b 1
)

echo [OK] Python détecté
python --version

REM Vérifier si les dépendances sont installées
echo.
echo [INFO] Vérification des dépendances...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] Les dépendances ne sont pas installées
    echo [INFO] Installation des dépendances...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERREUR] Impossible d'installer les dépendances
        pause
        exit /b 1
    )
)

echo [OK] Dépendances vérifiées

REM Lancer le serveur
echo.
echo ============================================================
echo   Démarrage du serveur...
echo ============================================================
echo.
echo   Interface Web: http://localhost:3000
echo   API Health:    http://localhost:3000/api/health
echo.
echo   Appuyez sur Ctrl+C pour arrêter le serveur
echo ============================================================
echo.

python server/hcv_pro_server.py

pause
