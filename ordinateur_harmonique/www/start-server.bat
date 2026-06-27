@echo off
title Architecture Harmonique - Serveur Local
echo ============================================
echo   Architecture Harmonique - Serveur Local
echo ============================================
echo.
echo Demarrage du serveur sur http://localhost:8080
echo.
echo NE FERMEZ PAS CETTE FENETRE.
echo Pour arreter : fermez cette fenetre.
echo ============================================
echo.
start http://localhost:8080
python -m http.server 8080
pause