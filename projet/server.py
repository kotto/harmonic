#!/usr/bin/env python3
"""
HCV Studio — Serveur Web Principal
Lance l'application web avec toutes les méthodes de compression
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Handler personnalisé pour servir les fichiers statiques"""
    
    def do_GET(self):
        """Gère les requêtes GET"""
        # Redirection de la racine vers index.html
        if self.path == '/':
            self.path = '/COMPRESSION-SOLUTIONS/index.html'
        elif self.path == '/compression':
            self.path = '/COMPRESSION-SOLUTIONS/unified_compression.html'
        elif self.path == '/studio':
            self.path = '/hcv_studio.html'
        elif self.path == '/player':
            self.path = '/hcv_studio.html'
        
        # Servir le fichier
        return super().do_GET()
    
    def end_headers(self):
        """Ajoute les headers de sécurité"""
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        return super().end_headers()

def run_server(port=3000):
    """Lance le serveur HTTP"""
    os.chdir(Path(__file__).parent)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MyHTTPRequestHandler)
    
    print('\n')
    print('╔════════════════════════════════════════════════════════╗')
    print('║          🎬 HCV Studio — Serveur Lancé                 ║')
    print('╚════════════════════════════════════════════════════════╝')
    print('\n')
    print(f'✅ Serveur en écoute sur: http://localhost:{port}')
    print('\n')
    print('📱 Interfaces disponibles:')
    print(f'   • Dashboard principal:      http://localhost:{port}/')
    print(f'   • Compression unifiée:      http://localhost:{port}/compression')
    print(f'   • HCV Studio:               http://localhost:{port}/studio')
    print(f'   • Lecteur HCV:              http://localhost:{port}/player')
    print('\n')
    print('📚 Documentation:')
    print('   • QUICK_START_DEPLOYMENT.md')
    print('   • README_MOBILE_INTEGRATION.md')
    print('   • DOCUMENTATION_INDEX.md')
    print('\n')
    print('💡 Appuyez sur Ctrl+C pour arrêter le serveur')
    print('\n')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n\n🛑 Arrêt du serveur...')
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    run_server(port)
