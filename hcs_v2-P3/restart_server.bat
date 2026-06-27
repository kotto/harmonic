@echo off
echo Arret du serveur existant...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *hcs_test_interface*" 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Relance du serveur HCS avec corrections...
cd /d "f:\FINAL\DEFINITIF\hcs_v2-P3"
python hcs_test_interface.py
