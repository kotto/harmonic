@echo off
REM ══════════════════════════════════════════════════════
REM  Vital Ka — Démarrage en 1 clic (Windows)
REM  Lance le serveur vocal (8420) + l'application (8765)
REM ══════════════════════════════════════════════════════
cd /d "%~dp0"
title Vital Ka — Serveurs
python start_vital_ka.py
if errorlevel 1 (
  echo.
  echo [ERREUR] Python introuvable ou demarrage echoue.
  echo Verifiez que Python 3.10+ est installe et dans le PATH.
  pause
)
