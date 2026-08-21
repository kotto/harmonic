@echo off
title Harmonic AI
cd /d "%~dp0\..\.."
echo.
echo   🧠 Harmonic AI — Démarrage
echo   ===========================
echo.
echo  1. Lancer la démo du langage ondulatoire
echo  2. Tester le raisonnement
echo  3. Lancer le serveur HPU
echo.
echo  Choisissez (1-3) :
set /p choix="> "
if "%choix%"=="1" python demo_langage_ondulatoire.py
if "%choix%"=="2" python wave_reasoning.py --test
if "%choix%"=="3" python server_hpu_cloud.py
if errorlevel 1 (
  echo [ERREUR] Python introuvable
  pause
)