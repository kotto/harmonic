@echo off
title HPU Cloud
cd /d "%~dp0\..\.."
echo.
echo   🌊 HPU Cloud — Démarrage
echo   ========================
echo.
python server_hpu_cloud.py
if errorlevel 1 (
  echo [ERREUR] Python introuvable
  pause
)