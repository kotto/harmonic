#!/usr/bin/env python
"""
Vital Ka — Serveur Local WiFi
=============================
Démarre un serveur HTTP sur le réseau local pour que
les patients puissent accéder à Vital Ka sans installation.

Usage :
  python ka_serve.py
  → Serveur démarré sur http://192.168.1.5:8765

Le médecin partage l'URL avec les patients sur le même WiFi.
Les patients ouvrent l'URL dans leur navigateur mobile.
"""

import http.server
import socket
import os
import sys
import webbrowser
import threading
from pathlib import Path

PORT = 8765
DIR = Path(__file__).parent

def get_local_ip():
    """Détecte l'IP locale sur le réseau WiFi"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def get_wifi_ips():
    """Liste toutes les IPs locales (WiFi, Ethernet...)"""
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip not in ips and not ip.startswith('127.'):
                ips.append(ip)
    except:
        pass
    return ips

class KAServer(http.server.SimpleHTTPRequestHandler):
    """Serveur HTTP avec CORS pour les Single Page Apps"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/vital_ka.html'
        super().do_GET()

def start_server():
    ip = get_local_ip()
    wifi_ips = get_wifi_ips()
    
    # ThreadingHTTPServer : traite les requêtes en parallèle (nécessaire car
    # l'app lance ~14 fetch JSON simultanés via Promise.all au démarrage ;
    # le HTTPServer monothread les sérialise et fait expirer les plus lentes).
    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), KAServer)

    print("""
╔══════════════════════════════════════════════════╗
║           VITAL KA — Serveur WiFi Local          ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  🔗 Liens d'accès :                              ║""")

    print(f"║  • Local    → http://localhost:{PORT}/vital_ka.html")

    for ip_addr in wifi_ips:
        print(f"║  • WiFi     → http://{ip_addr}:{PORT}/vital_ka.html")
    
    print(f"""║                                                  ║
║  📱 Patient → http://{ip}:{PORT}/ka_patient.html
║                                                  ║
║  💡 Le médecin partage l'URL WiFi aux patients.  ║
║  Les 2 appareils doivent être sur le même réseau. ║
║                                                  ║
║  ⌨️  Ctrl+C pour arrêter le serveur               ║
╚══════════════════════════════════════════════════╝
""")
    
    # Ouvrir automatiquement dans le navigateur
    webbrowser.open(f'http://localhost:{PORT}/vital_ka.html')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté.")
        server.shutdown()

if __name__ == '__main__':
    start_server()
