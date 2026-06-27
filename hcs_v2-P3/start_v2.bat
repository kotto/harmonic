@echo off
echo Arret serveur existant...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo.
echo Lancement HCS Interface V2...
cd /d "f:\FINAL\DEFINITIF\hcs_v2-P3"
python hcs_test_interface_v2.py
