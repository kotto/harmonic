"""
KA Light Server — Serveur léger (voice + engine bridge)
=========================================================
Démarre en <2 secondes, <200 MB RAM.
Expose les endpoints essentiels sans charger les 30 modules lourds.

Endpoints :
  GET  /api/stats
  POST /api/voice/speak
  POST /api/voice/stream
  POST /api/voice/barge-in
  GET  /api/voice/stats
  GET  /api/engine/compute?expr=
  GET  /api/engine/grover?target=&n=
  GET  /api/engine/fold?seq=
  GET  /api/health

Usage :
  python ka_light.py              # port 8421
  python ka_light.py --port 8080  # port personnalisé
"""

import sys, os, json, http.server, time, logging
from pathlib import Path

_KA_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_KA_DIR))
sys.path.insert(0, str(_KA_DIR.parent / 'engine'))

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# ═══ INIT (lazy — chargé uniquement si appelé) ═══
voice_engine = None
engine_bridge = None

def get_voice():
    global voice_engine
    if voice_engine is None:
        from harmonic_voice_engine import HarmonicVoiceEngine
        voice_engine = HarmonicVoiceEngine()
        log.info("Voice engine: ready")
    return voice_engine

def get_bridge():
    global engine_bridge
    if engine_bridge is None:
        from engine_bridge import EngineBridge
        engine_bridge = EngineBridge()
        log.info("Engine bridge: ready")
    return engine_bridge


# ═══ HTTP HANDLER ═══
class LightHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        # Default → ka_web_complete.html
        if path == '/' or path == '':
            path = '/ka_web_complete.html'
        
        # Static files
        if path.startswith('/www/'): filepath = path[1:]
        else: filepath = path.lstrip('/')
        
        mime = {'.html':'text/html','.css':'text/css','.js':'application/javascript',
                '.json':'application/json','.png':'image/png','.svg':'image/svg+xml',
                '.wav':'audio/wav','.mp3':'audio/mpeg','.ico':'image/x-icon'}
        ext = os.path.splitext(filepath)[1].lower()
        
        for base in [os.path.join(_KA_DIR, 'www'), _KA_DIR]:
            fullpath = os.path.join(base, filepath)
            if os.path.isfile(fullpath):
                ct = mime.get(ext, 'text/plain') + '; charset=utf-8'
                self.send_response(200)
                self.send_header('Content-Type', ct)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(fullpath, 'rb') as f:
                    self.wfile.write(f.read())
                return
        
        # ── API routes ────────────────────────────────────────────────────
        if self.path == '/api/health':
            self._json({'status': 'ok', 'voice': voice_engine is not None})
        elif self.path == '/api/stats':
            self._json({
                'voice': get_voice().stats if get_voice() else None,
                'ram_free_gb': round(__import__('psutil').virtual_memory().available / (1024**3), 2),
                'api': 'KA Web Complete v3',
            })
        elif self.path == '/api/voice/stats':
            self._json(get_voice().stats)
        elif self.path.startswith('/api/engine/compute'):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            expr = qs.get('expr', [''])[0]
            self._json({'expr': expr, 'result': get_bridge().compute(expr) if expr else '?'})
        else:
            self.send_response(404); self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/chat':
            data = self._read_json()
            msg = data.get('message', '')
            response = get_bridge().ask(msg)
            self._json({'response': response, 'source': 'ondulatoire'})
        elif self.path == '/api/create':
            data = self._read_json()
            n = data.get('n', 3)
            try:
                from engine.reasoning_engine import ReasoningEngine
                engine = ReasoningEngine(get_bridge()._enricher if hasattr(get_bridge(), '_enricher') else None)
                ideas = engine.create(n_ideas=n)
            except:
                ideas = [f"Connexion créative {i+1}: laissez les ondes interférer." for i in range(n)]
            self._json({'ideas': ideas})
        elif self.path == '/api/voice/speak':
            data = self._read_json()
            v = get_voice()
            lang = data.get('lang', None)
            if lang: v.set_language(lang)
            audio = v.speak(data.get('text',''), data.get('voice','denise'), float(data.get('speed',1.0)))
            self._audio(audio)
        elif self.path == '/api/voice/stream':
            data = self._read_json()
            chunks = [c for c, _ in get_voice().speak_stream(data.get('text',''), data.get('voice','denise'), float(data.get('speed',1.0)))]
            self._audio(b''.join(chunks))
        elif self.path == '/api/voice/barge-in':
            get_voice().barge_in()
            self._json({'barge_in': True})
        else:
            self.send_response(404); self.end_headers()
    
    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _audio(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'audio/wav')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data if data else b'')
    
    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        if not length:
            return {}
        raw = self.rfile.read(length)
        # Try UTF-8 first, then latin1 as fallback
        try:
            return json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            try:
                return json.loads(raw.decode('latin-1'))
            except Exception:
                return {}
    
    def log_message(self, *a): pass


# ═══ DÉMARRAGE ═══
if __name__ == '__main__':
    from socketserver import ThreadingMixIn
    
    class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
        """Serveur multi-thread — chaque requête dans son propre thread."""
        daemon_threads = True
    port = int(os.environ.get('PORT', 8421))
    if '--port' in sys.argv:
        idx = sys.argv.index('--port')
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    
    log.info(f"KA Light Server on http://localhost:{port}")
    log.info(f"  GET  /api/health")
    log.info(f"  GET  /api/stats")
    log.info(f"  POST /api/voice/speak")
    log.info(f"  POST /api/voice/stream")
    log.info(f"  GET  /api/engine/compute?expr=3+4")
    
    server = ThreadedHTTPServer(('0.0.0.0', port), LightHandler)
    log.info(f"Ready.")
    
    # Pre-warm: charger les blocs curated ET le bridge en arrière-plan
    def _prewarm():
        try:
            get_voice()  # init voice engine
            log.info("Voice engine warmed up")
        except: pass
        try:
            get_bridge()  # init engine bridge (159 blocs + 12K phases, ~3s)
            log.info("Engine bridge warmed up")
        except: pass
    
    import threading
    threading.Thread(target=_prewarm, daemon=True).start()
    
    server.serve_forever()
