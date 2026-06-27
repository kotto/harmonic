@echo off
echo 🌊 HCS V2 - Test Camera 8K
echo ==================================
cd /d "%~dp0"

echo 📦 Installation dépendances...
pip install -r requirements_camera.txt

echo 🚀 Lancement test camera 8K...
python test_camera_8k.py

pause
