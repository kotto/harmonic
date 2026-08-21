@echo off
title HarmoFold — Protéines
cd /d "%~dp0\..\.."
echo.
echo   🔬 HarmoFold — Démarrage
echo   ========================
echo.
python harmofold_v2.py
if errorlevel 1 (
  echo [ERREUR] Python introuvable
  pause
)