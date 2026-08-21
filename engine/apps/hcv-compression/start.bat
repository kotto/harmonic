@echo off
title HCV Compression
cd /d "%~dp0\..\.."
echo.
echo   🎵 HCV Compression — Démarrage
echo   ==============================
echo.
echo  Lancement du benchmark HCV2...
python benchmark_hcv2_vs_standards.py
if errorlevel 1 (
  echo [ERREUR] Python introuvable
  pause
)