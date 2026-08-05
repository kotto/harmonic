#!/usr/bin/env python
"""
KA Care — Serveur HTTPS Local
==============================
Version sécurisée du serveur WiFi avec SSL/TLS.
Permet l'accès à la caméra depuis tous les appareils
sur le réseau local (HTTPS requis par les navigateurs).

Usage :
  python ka_serve_https.py
  
Le navigateur affichera un avertissement de sécurité
(certificat auto-signé) → cliquer "Avancé" → "Accepter le risque"
"""

import http.server
import ssl
import socket
import os
import sys
import webbrowser
from pathlib import Path

PORT = 8765
DIR = Path(__file__).parent

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

class KAServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        super().do_GET()

def start():
    ip = get_local_ip()
    
    # Vérifier que les certificats existent
    cert_file = DIR / 'cert.pem'
    key_file = DIR / 'key.pem'
    
    if not cert_file.exists() or not key_file.exists():
        print("❌ Certificats SSL introuvables. Lancez d'abord :")
        print("   python ka_serve.py")
        print("   (les certificats sont generes automatiquement)")
        return
    
    # Créer le serveur HTTP
    server = http.server.HTTPServer(('0.0.0.0', PORT), KAServer)
    
    # Wrapper SSL
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert_file), str(key_file))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    
    print(f"""
╔══════════════════════════════════════════════════╗
║      KA CARE — Serveur HTTPS Local (SSL)        ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  🔐 Certificat auto-signé — accepter l'alerte    ║
║     du navigateur (Avancé → Accepter le risque)  ║
║                                                  ║
║  🔗 Médecin : https://localhost:{PORT}             ║
║  📱 Patient : https://{ip}:{PORT}         ║
║                                                  ║
║  📸 Caméra accessible sur TOUS les appareils !   ║
║                                                  ║
║  ⌨️  Ctrl+C pour arrêter                          ║
╚══════════════════════════════════════════════════╝
""")
    
    webbrowser.open(f'https://localhost:{PORT}')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté.")
        server.server_close()

if __name__ == '__main__':
    start()
