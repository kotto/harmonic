@echo off
echo ============================================
echo Harmonic AI SaaS - Démarrage du frontend
echo ============================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python 3.8+ : https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Installation des dépendances Python (si nécessaire)
pip install --quiet http-server >nul 2>&1

echo [2/3] Démarrage du serveur HTTP sur le port 8080
echo.
echo Frontend accessible à : http://localhost:8080
echo.
echo Appuyez sur Ctrl+C pour arrêter le serveur
echo.

REM Démarrer le serveur HTTP Python
python -m http.server 8080 --directory .

if errorlevel 1 (
    echo.
    echo [ERREUR] Impossible de démarrer le serveur HTTP
    echo Vérifiez que le port 8080 n'est pas déjà utilisé
    pause
)