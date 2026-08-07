#!/usr/bin/env python
"""
Vital Ka — Lanceur Unifié
==========================
Démarre les 2 serveurs nécessaires à l'application complète :

  1. Serveur vocal  : ka_voice_server.py  (port 8420) — Piper TTS neuronal offline
  2. Serveur applicatif : ka_serve.py     (port 8765) — interface web médecin/patient

Fonctions produit :
  - Détecte et tue les processus zombies sur les ports avant démarrage
  - Attend que le serveur vocal soit réellement prêt (health check HTTP)
  - Démarre le serveur vocal même sans modèle Piper (mode dégradé navigateur)
  - Ctrl+C arrête proprement les deux serveurs
  - Journal clair des URLs d'accès (local + WiFi)

Usage :
  python start_vital_ka.py            # démarrage standard
  python start_vital_ka.py --no-browser
  python start_vital_ka.py --no-voice  # sans serveur vocal (TTS navigateur)
"""

import argparse
import http.server
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

DIR = Path(__file__).parent
PORT_APP = 8765
PORT_VOICE = 8420


# ─────────────────────────────────────────────────────────────
# Utilitaires réseau
# ─────────────────────────────────────────────────────────────

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def get_wifi_ips():
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip not in ips and not ip.startswith('127.'):
                ips.append(ip)
    except Exception:
        pass
    return ips


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def kill_port_zombies(port):
    """Tue les processus écoutant sur le port (Windows netstat/taskkill)."""
    if os.name != 'nt':
        return 0
    try:
        out = subprocess.check_output(
            ['netstat', '-ano'], text=True, encoding='utf-8', errors='ignore')
        pids = set()
        for line in out.splitlines():
            parts = line.split()
            if (len(parts) >= 5 and parts[1].endswith(f':{port}')
                    and 'LISTENING' in parts[3].upper()):
                pids.add(parts[-1])
        killed = 0
        for pid in pids:
            try:
                subprocess.run(['taskkill', '//F', '//PID', pid],
                               capture_output=True, timeout=10)
                killed += 1
            except Exception:
                pass
        return killed
    except Exception:
        return 0


def wait_http_ready(url, timeout=60.0):
    """Attend qu'un endpoint HTTP réponde 200. Retourne True si prêt."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


# ─────────────────────────────────────────────────────────────
# Serveur vocal (subprocess)
# ─────────────────────────────────────────────────────────────

class VoiceServer:
    def __init__(self):
        self.proc = None
        self.ready = False

    def start(self):
        if port_in_use(PORT_VOICE):
            n = kill_port_zombies(PORT_VOICE)
            if n:
                print(f'   🧹 {n} processus zombie(s) tué(s) sur :{PORT_VOICE}')
                time.sleep(1)
        print(f'   ⏳ Démarrage ka_voice_server.py (Piper TTS)...')
        self.proc = subprocess.Popen(
            [sys.executable, str(DIR / 'ka_voice_server.py')],
            cwd=str(DIR),
            stdout=subprocess.DEVNULL,   # logs voix masqués (santé via /health)
            stderr=subprocess.DEVNULL,
        )
        self.ready = wait_http_ready(
            f'http://localhost:{PORT_VOICE}/api/voice/health', timeout=60)
        return self.ready

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass


# ─────────────────────────────────────────────────────────────
# Serveur applicatif (thread principal)
# ─────────────────────────────────────────────────────────────

class KAServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_GET(self):
        if self.path in ('/', ''):
            self.path = '/vital_ka.html'
        super().do_GET()

    def log_message(self, fmt, *args):
        # Log compact : seulement les erreurs (4xx/5xx)
        code = args[1] if len(args) > 1 else ''
        if str(code).startswith(('4', '5')):
            super().log_message(fmt, *args)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Vital Ka — Lanceur Unifié')
    parser.add_argument('--no-browser', action='store_true',
                        help='Ne pas ouvrir le navigateur automatiquement')
    parser.add_argument('--no-voice', action='store_true',
                        help='Ne pas démarrer le serveur vocal (TTS navigateur)')
    args = parser.parse_args()

    print()
    print('═' * 56)
    print('   🌿 VITAL KA — Démarrage de la plateforme')
    print('═' * 56)

    # ── 1. Serveur vocal ──
    voice = VoiceServer()
    voice_ok = False
    if not args.no_voice:
        print('\n🎙️  [1/2] Serveur vocal (port 8420)')
        voice_ok = voice.start()
        if voice_ok:
            print('   ✅ Piper TTS prêt — voix neuronale fr_FR-siwis-medium')
        else:
            print('   ⚠️  Serveur vocal non prêt après 60s')
            print('      → L\'app basculera sur la voix du navigateur')
    else:
        print('\n🎙️  [1/2] Serveur vocal désactivé (--no-voice)')

    # ── 2. Serveur applicatif ──
    print('\n📱 [2/2] Serveur applicatif (port 8765)')
    if port_in_use(PORT_APP):
        n = kill_port_zombies(PORT_APP)
        if n:
            print(f'   🧹 {n} processus zombie(s) tué(s) sur :{PORT_APP}')
            time.sleep(1)

    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT_APP), KAServer)
    ip = get_local_ip()

    print('   ✅ Prêt\n')
    print('═' * 56)
    print('   🔗 ACCÈS')
    print('═' * 56)
    print(f'   💻 Médecin (local)  → http://localhost:{PORT_APP}/vital_ka.html')
    for wip in get_wifi_ips():
        print(f'   📶 Médecin (WiFi)   → http://{wip}:{PORT_APP}/vital_ka.html')
    print(f'   👤 Patient          → http://{ip}:{PORT_APP}/ka_patient.html')
    print()
    print(f'   🎙️  Voix : {"Piper neuronal (serveur)" if voice_ok else "navigateur (fallback)"}')
    print('   ⌨️  Ctrl+C pour tout arrêter')
    print('═' * 56)
    print()

    if not args.no_browser:
        webbrowser.open(f'http://localhost:{PORT_APP}/vital_ka.html')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print('\n👋 Arrêt des serveurs...')
        server.shutdown()
        voice.stop()
        print('   ✅ Vital Ka arrêté proprement.')


if __name__ == '__main__':
    main()
