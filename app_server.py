#!/usr/bin/env python3
"""
HCV Studio — Serveur Flask Principal
Lance l'application web avec toutes les méthodes de compression
"""

import os
import sys
from pathlib import Path

# Essayer d'importer Flask, sinon utiliser un serveur simple
try:
    from flask import Flask, send_file, jsonify
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("⚠️  Flask non installé, utilisation du serveur HTTP simple")

if HAS_FLASK:
    app = Flask(__name__, static_folder='COMPRESSION-SOLUTIONS', static_url_path='')
    
    @app.route('/')
    def index():
        """Page d'accueil - Dashboard"""
        return send_file('COMPRESSION-SOLUTIONS/index.html')
    
    @app.route('/compression')
    def compression():
        """Interface de compression unifiée"""
        return send_file('COMPRESSION-SOLUTIONS/demo.html')
    
    @app.route('/demo')
    def demo():
        """Démo interactive"""
        return send_file('COMPRESSION-SOLUTIONS/demo.html')
    
    @app.route('/studio')
    def studio():
        """HCV Studio"""
        return send_file('hcv_studio.html')
    
    @app.route('/player')
    def player():
        """Lecteur HCV"""
        return send_file('hcv_studio.html')
    
    @app.route('/api/health')
    def health():
        """Health check"""
        return jsonify({
            'ok': True,
            'status': 'running',
            'message': 'HCV Studio + Harmonic AI'
        })
    
    # =====================================================================
    # HARMONIC AI ENDPOINTS
    # =====================================================================
    
    # Initialisation lazy du modele Harmonic AI
    _harmonic_ai = None
    
    def _get_ai():
        global _harmonic_ai
        if _harmonic_ai is None:
            import sys
            sys.path.insert(0, 'engine')
            from harmonic_ai import HarmonicAI
            _harmonic_ai = HarmonicAI(use_memory=True)
        return _harmonic_ai
    
    @app.route('/api/ask')
    def api_ask():
        """Reponse factuelle"""
        from flask import request
        q = request.args.get('q', '')
        if not q:
            return jsonify({'error': 'Parametre q requis'}), 400
        ai = _get_ai()
        response = ai.ask(q)
        return jsonify({'question': q, 'response': response, 'model': 'harmonic-v1'})
    
    @app.route('/api/reason')
    def api_reason():
        """Raisonnement en chaine"""
        from flask import request
        q = request.args.get('q', '')
        if not q:
            return jsonify({'error': 'Parametre q requis'}), 400
        ai = _get_ai()
        response = ai.reason(q)
        return jsonify({'question': q, 'response': response, 'model': 'harmonic-v1'})
    
    @app.route('/api/create')
    def api_create():
        """Connexions creatives"""
        from flask import request
        n = int(request.args.get('n', '3'))
        ai = _get_ai()
        ideas = ai.create(n=n)
        return jsonify({'ideas': ideas, 'model': 'harmonic-v1'})
    
    @app.route('/api/haiku')
    def api_haiku():
        """Haiku"""
        ai = _get_ai()
        return jsonify({'haiku': ai.haiku(), 'model': 'harmonic-v1'})
    
    @app.route('/api/stats')
    def api_stats():
        """Statistiques du modele"""
        ai = _get_ai()
        return jsonify({'stats': ai.stats, 'model': 'harmonic-v1'})
    
    # ====================================================================
    
    @app.route('/api/info')
    def info():
        """Info sur l'application"""
        return jsonify({
            'name': 'HCV Studio',
            'version': '1.0.0',
            'methods': 7,
            'formats': '15+',
            'features': [
                'Mobile photo compression (HEIC, JPEG)',
                'Mobile video compression (MP4, MOV)',
                'Pre-compressed image compression',
                'Professional video formats (H.264, H.265, SDI)'
            ]
        })
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Server error'}), 500
    
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 3000))
        
        print('\n')
        print('╔════════════════════════════════════════════════════════╗')
        print('║          🎬 HCV Studio — Serveur Lancé                 ║')
        print('╚════════════════════════════════════════════════════════╝')
        print('\n')
        print(f'✅ Serveur Flask en écoute sur: http://localhost:{port}')
        print('\n')
        print('📱 Interfaces disponibles:')
        print(f'   • Dashboard principal:      http://localhost:{port}/')
        print(f'   • Compression unifiée:      http://localhost:{port}/compression')
        print(f'   • HCV Studio:               http://localhost:{port}/studio')
        print(f'   • Lecteur HCV:              http://localhost:{port}/player')
        print('\n')
        print('🔌 API Endpoints:')
        print(f'   • Santé du serveur:         http://localhost:{port}/api/health')
        print(f'   • Infos serveur:            http://localhost:{port}/api/info')
        print('\n')
        print('💡 Appuyez sur Ctrl+C pour arrêter le serveur')
        print('\n')
        
        app.run(host='0.0.0.0', port=port, debug=False)

else:
    # Fallback: serveur HTTP simple
    import http.server
    import socketserver
    
    class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.path = '/COMPRESSION-SOLUTIONS/index.html'
            elif self.path == '/compression':
                self.path = '/COMPRESSION-SOLUTIONS/unified_compression.html'
            elif self.path == '/studio':
                self.path = '/hcv_studio.html'
            elif self.path == '/player':
                self.path = '/hcv_studio.html'
            elif self.path == '/api/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok":true,"status":"running"}')
                return
            elif self.path == '/api/info':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"name":"HCV Studio","version":"1.0.0","methods":7}')
                return
            
            return super().do_GET()
    
    port = int(os.environ.get('PORT', 3000))
    os.chdir(Path(__file__).parent)
    
    with socketserver.TCPServer(("", port), MyHTTPRequestHandler) as httpd:
        print('\n')
        print('╔════════════════════════════════════════════════════════╗')
        print('║          🎬 HCV Studio — Serveur Lancé                 ║')
        print('╚════════════════════════════════════════════════════════╝')
        print('\n')
        print(f'✅ Serveur HTTP en écoute sur: http://localhost:{port}')
        print('\n')
        print('📱 Interfaces disponibles:')
        print(f'   • Dashboard principal:      http://localhost:{port}/')
        print(f'   • Compression unifiée:      http://localhost:{port}/compression')
        print(f'   • HCV Studio:               http://localhost:{port}/studio')
        print(f'   • Lecteur HCV:              http://localhost:{port}/player')
        print('\n')
        print('💡 Appuyez sur Ctrl+C pour arrêter le serveur')
        print('\n')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n\n🛑 Arrêt du serveur...')
            sys.exit(0)
