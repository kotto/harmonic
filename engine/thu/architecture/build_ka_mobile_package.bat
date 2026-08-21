@echo off
:: ═══════════════════════════════════════════════════════════════════════════════
:: build_ka_mobile_package.bat — Crée l'archive à déployer sur Oracle Cloud
:: ═══════════════════════════════════════════════════════════════════════════════
:: Usage :
::   1. Noter l'IP du VPS Oracle (visible dans la console)
::   2. Lancer ce script
::   3. Saisir l'IP quand demandé
:: ═══════════════════════════════════════════════════════════════════════════════

echo ╔══════════════════════════════════════════════════════════════╗
echo ║     KA MOBILE — Package de déploiement                     ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

setlocal enabledelayedexpansion

:: Déterminer le chemin du projet
set ENGINE_DIR=E:\SAAS - Copie\engine
set PACKAGE_DIR=%TEMP%\ka-mobile-package
set ARCHIVE=%TEMP%\ka-mobile.tar.gz

:: Créer le dossier de package
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%" 2>nul
mkdir "%PACKAGE_DIR%\ka_server" 2>nul
mkdir "%PACKAGE_DIR%\ka_server\routes" 2>nul
mkdir "%PACKAGE_DIR%\ka_server\services" 2>nul
mkdir "%PACKAGE_DIR%\ka-mobile-android\www" 2>nul
mkdir "%PACKAGE_DIR%\thu\architecture" 2>nul

echo [1/4] Copie des fichiers du serveur...

:: Fichiers racine
copy "%ENGINE_DIR%\ka_launcher.py" "%PACKAGE_DIR%\" >nul
copy "%ENGINE_DIR%\ka_config.py" "%PACKAGE_DIR%\" >nul
copy "%ENGINE_DIR%\ka_mobile_compress.py" "%PACKAGE_DIR%\" >nul
copy "%ENGINE_DIR%\ka_background_compress.py" "%PACKAGE_DIR%\" >nul
copy "%ENGINE_DIR%\hcv2_video_pipeline.py" "%PACKAGE_DIR%\" >nul
copy "%ENGINE_DIR%\requirements.txt" "%PACKAGE_DIR%\" >nul
copy "%ENGINE_DIR%\thu\phi_post_filter.py" "%PACKAGE_DIR%\thu\" >nul
copy "%ENGINE_DIR%\thu\architecture\deploy_ka_mobile.sh" "%PACKAGE_DIR%\thu\architecture\" >nul

:: Module ka_server (package)
echo [2/4] Copie du module ka_server...
xcopy "%ENGINE_DIR%\ka_server\__init__.py" "%PACKAGE_DIR%\ka_server\" >nul
xcopy "%ENGINE_DIR%\ka_server\app.py" "%PACKAGE_DIR%\ka_server\" >nul
xcopy "%ENGINE_DIR%\ka_server\routes\__init__.py" "%PACKAGE_DIR%\ka_server\routes\" >nul
xcopy "%ENGINE_DIR%\ka_server\routes\media.py" "%PACKAGE_DIR%\ka_server\routes\" >nul
xcopy "%ENGINE_DIR%\ka_server\routes\voice.py" "%PACKAGE_DIR%\ka_server\routes\" >nul
xcopy "%ENGINE_DIR%\ka_server\services\voice_engine.py" "%PACKAGE_DIR%\ka_server\services\" >nul

:: App frontend
echo [3/4] Copie de l'application frontend...
xcopy "%ENGINE_DIR%\ka-mobile-android\www\ka_index.html" "%PACKAGE_DIR%\ka-mobile-android\www\" >nul

:: Copier le script de déploiement aussi à la racine pour accès direct
copy "%ENGINE_DIR%\thu\architecture\deploy_ka_mobile.sh" "%PACKAGE_DIR%\deploy_ka_mobile.sh" >nul

echo [4/4] Création de l'archive...
:: Utiliser tar via Git Bash si disponible
where tar >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    tar czf "%ARCHIVE%" -C "%PACKAGE_DIR%" .
    echo.
    echo ✓ Archive créée : %ARCHIVE%
    echo   Taille : %~z1 octets
) else (
    echo ⚠ tar non trouvé. Utilisation de la copie directe.
    echo L'archive est dans %PACKAGE_DIR%
    echo Copie manuelle : xcopy "%PACKAGE_DIR%" "root@IP:/root/ka-mobile/"
)

echo.
echo ──────────────────────────────────────────────────────────────
echo  COMMANDE DE TRANSFERT
echo ──────────────────────────────────────────────────────────────
echo.
set /p VPS_IP="IP du VPS Oracle : "
if not "!VPS_IP!"=="" (
    echo.
    echo scp -i ~/Downloads/ma_cle.key "%ARCHIVE%" root@!VPS_IP!:/root/ka-mobile/
    echo.
    echo Puis sur le VPS :
    echo   cd /root/ka-mobile && tar xzf ka-mobile.tar.gz && bash deploy_ka_mobile.sh
    echo.
) else (
    echo IP non saisie. Commande manuelle :
    echo   scp -i ~/Downloads/ma_cle.key "%ARCHIVE%" root@IP_VPS:/root/ka-mobile/
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo.
pause