"""
KA VOICE SERVER — Serveur vocal offline (Piper neuronal + pipeline harmonique)
==============================================================================
Expose le pipeline PhiPiperEngine sur http://localhost:8420 pour que le client
JS (vital_ka_voice.js) puisse l'utiliser comme chemin PRINCIPAL de synthèse.

Routes :
    GET  /api/voice/offline/caps
         → { offline_ready, engines:{piper:bool}, enhancements:{harmonic_post_processor:true} }
    POST /api/voice/offline        body: { text, voice, speed, enhanced }
         → audio/x-wav (WAV mono 16-bit, 22 kHz)
    GET  /api/voice/health
         → { status:"ok", piper_loaded:bool, voice, uptime_s }
    GET  /
         → page d'accueil (vérif rapide navigateur)

Architecture :
    - Chargement UNIQUE du modèle Piper au démarrage (warm-up) → synchro ~300 ms
    - Thread-safe : un seul PiperVoice, syntheses sérialisées par un verrou
    - Zéro hallucination : lit exactement le texte envoyé, aucune reformulation

Démarrage :
    python ka_voice_server.py            # port 8420
    python ka_voice_server.py --port 9000
    python ka_voice_server.py --voice en_US-lessac-medium
==============================================================================
"""
import os
import sys
import time
import json
import threading
import argparse
import io
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE_DIR)

# Mapping noms courts → noms complets Piper (défense en profondeur)
_VOICE_ALIASES = {
    'siwis': 'fr_FR-siwis-medium',
    'siwis_low': 'fr_FR-siwis-low',
    'siwis_medium': 'fr_FR-siwis-medium',
    'tom': 'fr_FR-tom-medium',
    'tom_medium': 'fr_FR-tom-medium',
    'mls': 'fr_FR-mls-medium',
    'mls_medium': 'fr_FR-mls-medium',
    'upmc': 'fr_FR-upmc-medium',
    'upmc_medium': 'fr_FR-upmc-medium',
    'gilles': 'fr_FR-gilles-low',
    'gilles_low': 'fr_FR-gilles-low',
    'lessac': 'en_US-lessac-medium',
    'lessac_low': 'en_US-lessac-low',
    'libritts': 'en_US-libritts-high',
    'amy': 'en_US-amy-medium',
    'arctic': 'en_US-arctic-medium',
}

def _resolve_voice(name: str) -> str:
    """Résout un alias de voix en nom complet Piper."""
    return _VOICE_ALIASES.get(name.lower(), name)


# ═══════════════════════════════════════════════════════════════════════════
# MOTEUR VOCAL — singleton thread-safe
# ═══════════════════════════════════════════════════════════════════════════

class VoiceEngine:
    """Wrapper thread-safe autour PhiPiperEngine avec warm-up au démarrage."""

    def __init__(self, voice: str = "fr_FR-siwis-medium"):
        self.voice_name = voice
        self.piper_loaded = False
        self.start_time = time.time()
        self._lock = threading.Lock()
        self._engine = None
        self._init_error = None

    def warm_up(self):
        """Charge Piper une fois pour toutes (au démarrage du serveur)."""
        print(f"[KA_VOICE_SERVER] Warm-up Piper ({self.voice_name})...")
        try:
            from phi_piper_engine import PhiPiperEngine
            import numpy as np
            self._engine = PhiPiperEngine()
            self._engine._ensure_voice_loaded(self.voice_name)
            self.piper_loaded = self._engine._piper_voice is not None
            if self.piper_loaded:
                # Première synthèse (compilation ONNX / lazy init)
                t0 = time.time()
                audio = self._engine.synthesize("Système vocal prêt.", voice_name=self.voice_name)
                ms = (time.time() - t0) * 1000
                rms = float(np.sqrt(np.mean(audio ** 2))) if len(audio) else 0
                print(f"[KA_VOICE_SERVER] ✅ Piper prêt — warm {ms:.0f}ms, RMS {rms:.3f}")
            else:
                self._init_error = "PiperVoice non chargé après _ensure_voice_loaded"
                print(f"[KA_VOICE_SERVER] ❌ {self._init_error}")
        except Exception as e:
            self._init_error = str(e)
            self.piper_loaded = False
            print(f"[KA_VOICE_SERVER] ❌ Erreur warm-up: {e}")

    def synthesize(self, text: str, voice: str = None, speed: float = 1.0,
                   enhanced: bool = True) -> bytes:
        """Synthétise le texte → WAV mono 16-bit bytes. Thread-safe (verrou)."""
        if not self.piper_loaded or self._engine is None:
            raise RuntimeError("Piper non chargé")
        with self._lock:
            import numpy as np
            # H_speed (idx 2) : 0=rapide, 1=lent — TOUJOURS appliqué.
            # Avec length_scale = 0.50 + H_speed * 1.05 :
            #   speed=1.0 → 0.48 → ls≈1.0 (défaut Piper)
            #   speed=1.35 → 0.10 → ls≈0.60 (rapide, reste intelligible)
            #   speed=0.70 → 0.79 → ls≈1.33 (lent, apaisant)
            h_speed = max(0.0, min(1.0, 1.55 - speed * 1.07))
            if enhanced:
                # Profil harmonique 11D : conseiller soignant (clarté +++
                #   naturalité, breathiness basse pour voix nette de diagnostic)
                params = np.array([0.72, 0.45, h_speed,
                                   0.68, 0.15, 0.72, 0.35, 0.80, 0.40, 0.72, 0.80])
            else:
                # Sans pipeline harmonique : neutre 11D, seul H_speed varie
                params = np.full(11, 0.618)  # φ⁻¹ neutre
                params[2] = h_speed           # vitesse uniquement
            voice = _resolve_voice(voice or self.voice_name)
            audio = self._engine.synthesize(text, params, voice_name=voice)
            # Réencoder en WAV bytes
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self._engine.sample_rate)
                wf.writeframes((np.clip(audio, -1.0, 1.0) * 32767).astype('<i2').tobytes())
            return buf.getvalue()

    def uptime(self) -> float:
        return time.time() - self.start_time


# ═══════════════════════════════════════════════════════════════════════════
# SERVEUR HTTP
# ═══════════════════════════════════════════════════════════════════════════

ENGINE = None  # VoiceEngine global


class VoiceHandler(BaseHTTPRequestHandler):

    # Log discret
    def log_message(self, fmt, *args):
        pass  # silencieux ; les infos utiles sont dans /health

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _wav(self, wav_bytes: bytes):
        self.send_response(200)
        self.send_header('Content-Type', 'audio/wav')
        self.send_header('Content-Length', str(len(wav_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(wav_bytes)

    def _cors_preflight(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._cors_preflight()

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/voice/offline/caps':
            return self._json(200, {
                'offline_ready': ENGINE.piper_loaded if ENGINE else False,
                'engines': {'piper': ENGINE.piper_loaded if ENGINE else False},
                'enhancements': {'harmonic_post_processor': True},
                'voice': ENGINE.voice_name if ENGINE else None,
            })
        if path == '/api/voice/health':
            return self._json(200, {
                'status': 'ok' if (ENGINE and ENGINE.piper_loaded) else 'degraded',
                'piper_loaded': ENGINE.piper_loaded if ENGINE else False,
                'voice': ENGINE.voice_name if ENGINE else None,
                'uptime_s': round(ENGINE.uptime(), 1) if ENGINE else 0,
                'error': ENGINE._init_error if ENGINE else 'no engine',
            })
        if path == '/' or path == '/index.html':
            html = _LANDING.format(
                status='✅ Prêt' if (ENGINE and ENGINE.piper_loaded) else '❌ Piper non chargé',
                voice=ENGINE.voice_name if ENGINE else '?',
                uptime=f"{ENGINE.uptime():.0f}s" if ENGINE else '0',
                error=ENGINE._init_error or 'aucune',
            )
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(404, {'error': 'not found', 'path': path})

    def do_POST(self):
        path = self.path.split('?')[0]
        if path != '/api/voice/offline':
            return self._json(404, {'error': 'not found', 'path': path})
        if not ENGINE or not ENGINE.piper_loaded:
            return self._json(503, {'error': 'Piper non chargé',
                                    'detail': ENGINE._init_error if ENGINE else 'no engine'})
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length) if length else b'{}'
            payload = json.loads(raw.decode('utf-8') or '{}')
            text = (payload.get('text') or '').strip()
            if not text:
                return self._json(400, {'error': 'texte vide'})
            if len(text) > 2000:
                text = text[:2000]  # garde-fou
            voice = _resolve_voice(payload.get('voice') or ENGINE.voice_name)
            speed = float(payload.get('speed') or 1.0)
            enhanced = payload.get('enhanced', True)
            t0 = time.time()
            wav_bytes = ENGINE.synthesize(text, voice=voice, speed=speed, enhanced=enhanced)
            ms = (time.time() - t0) * 1000
            print(f"[KA_VOICE_SERVER] synth {len(wav_bytes)} octets, {ms:.0f}ms, "
                  f"texte={len(text)}c, voice={voice}")
            return self._wav(wav_bytes)
        except Exception as e:
            print(f"[KA_VOICE_SERVER] ERREUR synth: {e}")
            return self._json(500, {'error': 'synthèse échouée', 'detail': str(e)})


_LANDING = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>KA VOICE SERVER</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0d1117;color:#c9d1d9;
margin:0;padding:40px;line-height:1.6}}
h1{{color:#58a6ff}} .ok{{color:#3fb950;font-size:1.4em}} .meta{{color:#8b949e}}
code{{background:#161b22;padding:2px 6px;border-radius:4px}}
</style></head><body>
<h1>🎤 KA VOICE SERVER</h1>
<p class="ok">{status}</p>
<p class="meta">Voix : <code>{voice}</code> · Uptime : <code>{uptime}</code></p>
<p class="meta">Erreur init : <code>{error}</code></p>
<hr>
<p>Routes :</p>
<ul>
<li><code>GET /api/voice/offline/caps</code> — capacités (offline_ready, piper)</li>
<li><code>POST /api/voice/offline</code> — synthèse WAV (body JSON: text, voice, speed, enhanced)</li>
<li><code>GET /api/voice/health</code> — santé détaillée</li>
</ul>
<p class="meta">Le client JS vital_ka_voice.js détecte ce serveur automatiquement.</p>
</body></html>"""


def main():
    global ENGINE
    parser = argparse.ArgumentParser(description="KA Voice Server (Piper offline)")
    parser.add_argument('--port', type=int, default=8420)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--voice', default='fr_FR-siwis-medium',
                        help='Voix Piper (fr_FR-siwis-medium, en_US-lessac-medium, ...)')
    args = parser.parse_args()

    ENGINE = VoiceEngine(voice=args.voice)
    ENGINE.warm_up()

    # ThreadingHTTPServer : traite les requêtes en parallèle (la sonde /caps du
    # client et les POST /offline de synthèse ne doivent pas se bloquer mutuellement).
    # allow_reuse_address évite le "Address already in use" au redémarrage rapide.
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((args.host, args.port), VoiceHandler)
    server.daemon_threads = True
    url = f"http://localhost:{args.port}"
    print(f"\n[KA_VOICE_SERVER] 🎤 Écoute sur {url}")
    print(f"[KA_VOICE_SERVER]    Piper: {'✅' if ENGINE.piper_loaded else '❌'} "
          f"| voice={args.voice} | enhanced=harmonic 11D")
    print(f"[KA_VOICE_SERVER]    Ctrl+C pour arrêter\n")
    sys.stdout.flush()  # forcer l'affichage de la bannière (buffers)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[KA_VOICE_SERVER] Arrêt demandé.")
        server.shutdown()


if __name__ == "__main__":
    main()
