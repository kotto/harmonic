@echo off
title Wave Voice — Synthèse Vocale
cd /d "%~dp0\..\.."
echo.
echo   🎤 Wave Voice — Démarrage
echo   =========================
echo.
echo  1. Lancer le serveur KA Voice
echo  2. Tester le φ-Vocoder
echo  3. Lancer le benchmark HCV2 audio
echo.
echo  Choisissez (1-3) :
set /p choix="> "
if "%choix%"=="1" python ka_voice_server.py
if "%choix%"=="2" python phi_vocoder_calibrator.py
if "%choix%"=="3" python harmonic_voice_codec_v2.py --benchmark
if errorlevel 1 (
  echo [ERREUR] Python introuvable
  pause
)