@echo off
title KA Care - Serveur HTTPS Local
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════╗
echo ║     KA CARE — Serveur HTTPS Local (SSL)     ║
echo ╠══════════════════════════════════════════════╣

REM Ouvrir le port dans le pare-feu
netsh advfirewall firewall add rule name="KA Care HTTPS" dir=in action=allow protocol=TCP localport=8765 >nul 2>&1
echo ║  ✅ Pare-feu : port 8765 ouvert              ║

REM Trouver l'IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do set IP=%%a
set IP=%IP: =%
echo ║  📡 IP locale : %IP%                          ║
echo ╠══════════════════════════════════════════════╣
echo ║                                                ║
echo ║  🔐 Le navigateur va afficher une alerte       ║
echo ║     Cliquer : Avance → Accepter le risque     ║
echo ║                                                ║
echo ║  🔗 https://localhost:8765                     ║
echo ║  📱 https://%IP%:8765/ka_patient.html          ║
echo ║                                                ║
echo ║  📸 Camera accessible depuis TOUS les app. !   ║
echo ║                                                ║
echo ║  ⌨️  Ctrl+C pour arreter                       ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM Generer certificat si absent
if not exist cert.pem (
    echo 🔐 Generation du certificat SSL...
    python -c "exec(open('_gen_cert.py').read())"
)

python ka_serve_https.py
pause
