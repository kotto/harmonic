@echo off
REM HCS Harmonic Music Generator - Start Script (Windows)

echo 🎵 HCS Harmonic Music Generator Starting...
echo ==========================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed
    pause
    exit /b 1
)

REM Check pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Create directories
echo 📁 Creating directories...
if not exist "templates" mkdir templates
if not exist "static" mkdir static
if not exist "generated_music" mkdir generated_music

REM Start server
echo 🚀 Starting server...
echo 🌐 Web Interface: http://localhost:8020
echo 📊 API Documentation: http://localhost:8020/docs
echo ==========================================

python server.py

pause
