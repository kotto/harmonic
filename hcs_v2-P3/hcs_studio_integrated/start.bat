@echo off
title HCS Studio Integrated - Starting Server
color 0A

echo ========================================
echo    HCS Studio Integrated
echo    Complete Media Processing Suite
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some dependencies may have failed to install.
    echo The server will try to start with available modules.
)
echo.

echo Starting HCS Studio Integrated Server...
echo Server will be available at: http://localhost:8013
echo Press Ctrl+C to stop the server
echo.

python server.py

echo.
echo Server stopped.
pause
