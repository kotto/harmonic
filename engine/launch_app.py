# -*- coding: utf-8 -*-
"""
🚀 Lancement de l'application KA Care
=====================================
- Sert le frontend (docs/) sur http://localhost:8080
- Sert l'API hologrammes sur http://localhost:8010 (déjà actif)

Usage : python launch_app.py
       python launch_app.py --port 8080
"""
import argparse
import http.server
import functools
import os
import threading
import webbrowser
import time
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
DOCS = ENGINE / "docs"
PORT = 8080


class KaHandler(http.server.SimpleHTTPRequestHandler):
    """Sert les fichiers de docs/ avec CORS pour l'API."""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Anti-cache : le frontend évolue vite, le navigateur doit
        # toujours recevoir la dernière version des fichiers.
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, fmt, *args):
        # Log minimal
        print(f"  [frontend] {self.address_string()} {fmt % args}")


def check_api() -> bool:
    """Vérifie que l'API hologrammes est joignable."""
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:8010/health', timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description='Lance KA Care')
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()

    # 1. Vérifier l'API
    api_ok = check_api()
    print("=" * 60)
    print("  🚀 KA CARE — Lancement")
    print("=" * 60)
    if api_ok:
        print("  ✅ API hologrammes : http://localhost:8010 (JOIGNABLE)")
    else:
        print("  ⚠️  API hologrammes : non joignable (diagnostic en local uniquement)")
        print("     Lancer : python -u -c \"import uvicorn; from inference_server import app;"
              " uvicorn.run(app, host='127.0.0.1', port=8010)\"")
    print(f"  📁 Frontend : {DOCS}")
    print(f"  🌐 URL      : http://localhost:{args.port}/ka_care.html")
    print("=" * 60)

    # 2. Lancer le serveur statique
    os.chdir(DOCS)
    handler = functools.partial(KaHandler, directory=str(DOCS))
    server = http.server.ThreadingHTTPServer(('0.0.0.0', args.port), handler)
    print(f"\n  🟢 Serveur frontend démarré sur http://localhost:{args.port}")
    print("  (Ctrl+C pour arrêter)\n")

    # 3. Ouvrir le navigateur
    if not args.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(
            f'http://localhost:{args.port}/ka_care.html')).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  ⏹️  Arrêt du serveur.")
        server.shutdown()


if __name__ == "__main__":
    main()
