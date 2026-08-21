@echo off
title Tableau Périodique THU
cd /d "%~dp0\..\.."
echo.
echo   📊 Tableau Périodique — Démarrage
echo   ================================
echo.
echo  1. Générer le tableau des particules (T6)
echo  2. Afficher la carte des particules
echo  3. Afficher les 118 éléments
echo.
echo  Choisissez (1-3) :
set /p choix="> "
if "%choix%"=="1" python generer_tableau_periodique_T6.py
if "%choix%"=="2" python carte_particules_T6.py
if "%choix%"=="3" python generation_tableau_periodique.py
if errorlevel 1 (
  echo [ERREUR] Python introuvable
  pause
)