@echo off
title HCS MiniCDN - Demarrage
color 0B
echo.
echo  =========================================================
echo    HCS MiniCDN v1.0 - Distribution 4K/8K Mondial
echo  =========================================================
echo.
echo  Verification des dependances...
pip install fastapi uvicorn httpx --quiet 2>nul

echo.
echo  Demarrage du CDN...
echo.
echo  Ports utilises:
echo    9000  - CDN Gateway (API + WebSocket)
echo    9001  - Dashboard Admin
echo    9010  - TV Broadcast 4K
echo    9011  - TV Broadcast 8K
echo    9012  - Mobile Streaming USA 8K
echo    9013  - Mobile Streaming Afrique
echo    9014  - VOD Premium
echo    9015  - Live Events
echo    9016  - Archive Storage
echo.
echo  Dashboard: http://localhost:9000/dashboard
echo  API Docs:  http://localhost:9000/docs
echo  Health:    http://localhost:9000/health
echo.

cd /d "%~dp0\.."
python -m cdn.services.launch_all_services

pause
