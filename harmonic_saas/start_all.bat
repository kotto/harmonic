@echo off
echo ============================================
echo Harmonic AI SaaS - Démarrage des services
echo ============================================
echo.

REM Vérifier si Docker est installé
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Vérifier si Docker est en cours d'exécution
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas en cours d'exécution
    echo Veuillez démarrer Docker Desktop et réessayer
    pause
    exit /b 1
)

echo [1/5] Arrêt des services existants (si présents)
docker-compose down

echo [2/5] Construction des images Docker
docker-compose build

echo [3/5] Démarrage des services de base (PostgreSQL, Redis, MongoDB)
docker-compose up -d postgres redis mongodb

echo [4/5] Attente de l'initialisation des bases de données...
timeout /t 10 /nobreak >nul

echo [5/5] Démarrage de l'API FastAPI
docker-compose up -d api

echo.
echo ============================================
echo Services démarrés avec succès !
echo ============================================
echo.
echo Accès aux services :
echo - Dashboard Frontend : http://localhost:8080
echo - API Backend        : http://localhost:9000
echo - Documentation API  : http://localhost:9000/docs
echo - Métriques Prometheus : http://localhost:9000/metrics
echo - PostgreSQL         : localhost:5432
echo - Redis              : localhost:6379
echo - MongoDB            : localhost:27017
echo.
echo Pour démarrer les services audio/vidéo harmoniques :
echo 1. Assurez-vous que les services harmoniques sont en cours d'exécution
echo 2. Utilisez le dashboard pour uploader et traiter des fichiers
echo.
echo Pour arrêter tous les services : docker-compose down
echo.
pause