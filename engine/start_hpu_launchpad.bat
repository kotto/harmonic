@echo off
title HPU Launchpad — Toutes les applications
cd /d "%~dp0\.."
echo.
echo   🌊 HPU Launchpad — Applications harmoniques
echo   ==========================================
echo.
echo   1. ☁️  HPU Cloud — API de calcul
echo   2. 🎵 HCV Compression — Codec audio/vidéo
echo   3. 🧠 Harmonic AI — IA ondulatoire
echo   4. 🏥 KA Care — Médecine harmonique
echo   5. 🔬 HarmoFold — Repliement de protéines
echo   6. 📊 Periodic Table — Particules et éléments
echo   7. 🧮 GSM8K — Raisonnement mathématique
echo   8. 🎤 Wave Voice — Synthèse vocale
echo   9. ⚡ Tout démarrer
echo   0. Quitter
echo.

:menu
set /p choix="Choix (0-9) : "

if "%choix%"=="1" start "HPU Cloud" cmd /c python server_hpu_cloud.py
if "%choix%"=="2" start "HCV" cmd /c python harmonic_voice_codec_v2.py
if "%choix%"=="3" start "Harmonic AI" cmd /c python wave_reasoning.py --test
if "%choix%"=="4" start "KA Care" cmd /c python ka_care.py
if "%choix%"=="5" start "HarmoFold" cmd /c python harmofold_v2.py
if "%choix%"=="6" start "Periodic Table" cmd /c python generer_tableau_periodique_T6.py
if "%choix%"=="7" start "GSM8K" cmd /c python -c "from wave_math import wave_solve; print(wave_solve('15 + 27'))"
if "%choix%"=="8" start "Wave Voice" cmd /c python ka_voice_server.py
if "%choix%"=="9" (
  start "HPU Cloud" cmd /c python server_hpu_cloud.py
  echo Tous les services lancés.
)
if "%choix%"=="0" exit /b

if not "%choix%"=="" (
  echo.
  goto menu
)
pause