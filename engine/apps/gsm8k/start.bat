@echo off
title GSM8K — Raisonnement Mathématique
cd /d "%~dp0\..\.."
echo.
echo   🧮 GSM8K — Démarrage
echo   =====================
echo.
echo  1. Lancer le benchmark GSM8K (complet)
echo  2. Test rapide
echo  3. Lancer l'API HPU (pour requêtes GSM8K)
echo.
echo  Choisissez (1-3) :
set /p choix="> "
if "%choix%"=="1" python benchmark_gsm8k_ondulatoire.py
if "%choix%"=="2" python -c "from wave_math import wave_solve; print(wave_solve('15 + 27'))"
if "%choix%"=="3" python server_hpu_cloud.py
if errorlevel 1 (
  echo [ERREUR] Python introuvable
  pause
)