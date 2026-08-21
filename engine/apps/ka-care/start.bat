@echo off
title KA Care — Médecine Harmonique
cd /d "%~dp0\..\.."
echo.
echo   🏥 KA Care — Démarrage
echo   ======================
echo.
echo  1. Lancer le serveur KA Care
echo  2. Valider T* (température dorée)
echo  3. Calibration
echo.
echo  Choisissez (1-3) :
set /p choix="> "
if "%choix%"=="1" python ka_care.py
if "%choix%"=="2" python depot_e3_tstar.py
if "%choix%"=="3" python ka_care_calibrate.py
if errorlevel 1 (
  echo [ERREUR] Python introuvable
  pause
)