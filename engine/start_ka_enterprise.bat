@echo off
title KA Enterprise — Business Harmonique
echo.
echo   🏢 KA Enterprise v4.0 — Intelligence d'Entreprise Harmonique
echo   ============================================================
echo.
echo   Demarrage sur http://localhost:8767
echo   Mode multi-tenant, authentification, audit
echo.
python ka_launcher.py --product enterprise %*
pause
