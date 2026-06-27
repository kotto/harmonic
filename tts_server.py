#!/usr/bin/env python3
"""
Serveur TTS Harmonique — Edge-TTS + SpectralVoicePipeline
Démarrage : python tts_server.py
API HTTP :
  GET  /speak?text=...&voice=...&emotion=... → audio/mpeg (mode texte simple)
  POST /speak_spectral                        → audio/mpeg (mode SpectralMessage 11D)
  GET  /voices                                → JSON (voix Edge-TTS)
  GET  /voices_harmonic                       → JSON (profils vocaux harmoniques)
  GET  /health                                → JSON (statut)
  GET  /voice_stats                           → JSON (stats du pipeline)
"""
import subprocess
import tempfile
import os
import json
import shutil
import cgi
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 5050
ENGINE = "edge"
EDGE_VOICE = "fr-FR-DeniseNeural"
EDGE_VOICES_FR = [
    "fr-FR-DeniseNeural", "fr-FR-HenriNeural",
    "fr-FR-EloiseNeural", "fr-FR-YvetteNeural", "fr-FR-JeromeNeural",
    "fr-CA-AntoineNeural", "fr-CA-SylvieNeural"
]

# Initialisation paresseuse du pipeline harmonique
_spectral_pipeline = None

def get_spectral_pipeline():
    """Initialise et retourne le SpectralVoicePipeline (singleton)."""
    global _spectral_pipeline
    if _spectral_pipeline is None:
        try:
            from engine.spectral_voice_pipeline import SpectralVoicePipeline
            _spectral_pipeline = SpectralVoicePipeline()
            _spectral_pipeline.initialize(load_profiles=True, load_model=True)
            print("[TTS] Pipeline spectral harmonique initialisé")
        except ImportError as e:
            print(f"[TTS] ⚠ Pipeline spectral non disponible: {e}")
            return None
    return _spectral_pipeline

def speak_edge(text, voice_name=None):
    voice = voice_name or EDGE_VOICE
    if not shutil.which("edge-tts"):
        return None
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", tmp.name]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[Edge-TTS] Erreur: {proc.stderr}")
        os.unlink(tmp.name)
        return None
    return tmp.name

class TTSServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # ---- /speak : mode texte simple (compatible existant) ----
        if parsed.path == "/speak" or parsed.path == "/":
            text = params.get("text", [""])[0]
            voice = params.get("voice", [None])[0]
            engine = params.get("engine", ["edge"])[0]
            emotion = params.get("emotion", ["neutre"])[0]  # Nouveau paramètre

            if not text:
                self.send_error(400, "Parametre 'text' requis")
                return

            # Essayer le pipeline spectral si disponible
            pipeline = get_spectral_pipeline()
            if pipeline and engine == "harmonic":
                try:
                    audio_bytes, content_type = pipeline.synthesize_for_tts_server(
                        text=text, voice=voice or "default", emotion=emotion
                    )
                    if audio_bytes:
                        self.send_response(200)
                        self.send_header("Content-Type", content_type)
                        self.send_header("Content-Length", str(len(audio_bytes)))
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(audio_bytes)
                        return
                except Exception as e:
                    print(f"[TTS] Pipeline spectral échoué, fallback Edge-TTS: {e}")

            # Fallback Edge-TTS
            audio_path = None
            content_type = "audio/mpeg"

            if engine in ("edge", "harmonic"):
                audio_path = speak_edge(text, voice)
                content_type = "audio/mpeg"

            if not audio_path:
                self.send_error(500, "TTS non disponible")
                return

            with open(audio_path, "rb") as f:
                data = f.read()
            os.unlink(audio_path)

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return

        # ---- /voices : voix Edge-TTS ----
        if parsed.path == "/voices":
            voices = {
                "edge": {"fr": EDGE_VOICES_FR, "default": EDGE_VOICE},
                "engine": "edge"
            }
            data = json.dumps(voices, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return

        # ---- /voices_harmonic : profils vocaux harmoniques ----
        if parsed.path == "/voices_harmonic":
            pipeline = get_spectral_pipeline()
            if pipeline:
                profiles = {
                    "harmonic_profiles": pipeline.trainer.list_profiles(),
                    "default": "default",
                    "emotion_modulations": ["neutre", "joyeux", "triste", "urgent", "calme", "autoritaire", "doux", "excité"],
                }
            else:
                profiles = {"error": "Pipeline spectral non disponible"}
            data = json.dumps(profiles, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return

        # ---- /health : statut ----
        if parsed.path == "/health":
            edge_ok = bool(shutil.which("edge-tts"))
            pipeline = get_spectral_pipeline()
            status = {
                "edge_tts": "ok" if edge_ok else "missing",
                "engine": "edge",
                "spectral_pipeline": "ok" if pipeline else "unavailable",
            }
            data = json.dumps(status, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return

        # ---- /voice_stats : statistiques du pipeline ----
        if parsed.path == "/voice_stats":
            pipeline = get_spectral_pipeline()
            if pipeline:
                stats = pipeline.get_stats()
                # Convertir les valeurs non-sérialisables
                for k, v in list(stats.items()):
                    if isinstance(v, (np.ndarray,)):
                        stats[k] = str(v)
            else:
                stats = {"error": "Pipeline spectral non disponible"}
            data = json.dumps(stats, indent=2, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_error(404, "Route inconnue")

    def do_POST(self):
        """Route POST pour les SpectralMessages JSON."""
        parsed = urlparse(self.path)

        if parsed.path == "/speak_spectral":
            # Lire le corps de la requête
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            try:
                body = json.loads(post_data)
            except json.JSONDecodeError:
                self.send_error(400, "JSON invalide")
                return

            spectral_json = body.get('spectral_message') or body.get('spectral')
            text = body.get('text', '')
            voice = body.get('voice', 'default')
            emotion = body.get('emotion', 'neutre')

            pipeline = get_spectral_pipeline()
            if not pipeline:
                self.send_error(503, "Pipeline spectral non disponible")
                return

            if spectral_json:
                # Mode SpectralMessage
                spectral_str = json.dumps(spectral_json) if not isinstance(spectral_json, str) else spectral_json
                audio_bytes, content_type = pipeline.synthesize_for_tts_server(
                    text=text,
                    spectral_message_json=spectral_str,
                    voice=voice,
                    emotion=emotion,
                )
            elif text:
                # Mode texte + émotion
                audio_bytes, content_type = pipeline.synthesize_for_tts_server(
                    text=text, voice=voice, emotion=emotion
                )
            else:
                self.send_error(400, "'text' ou 'spectral_message' requis")
                return

            if not audio_bytes:
                self.send_error(500, "Synthèse échouée")
                return

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(audio_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(audio_bytes)
            return

        self.send_error(404, "Route POST inconnue")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[TTS] {args[0]}")

if __name__ == "__main__":
    import numpy as np
    print("=" * 60)
    print("  Serveur TTS Harmonique — Edge-TTS + SpectralVoicePipeline")
    print(f"  Port : {PORT}")
    print("  API  : GET  /speak?text=Bonjour&emotion=joyeux")
    print("         POST /speak_spectral  (JSON SpectralMessage 11D)")
    print("         GET  /voices")
    print("         GET  /voices_harmonic")
    print("         GET  /health")
    print("         GET  /voice_stats")
    print("=" * 60)

    if not shutil.which("edge-tts"):
        print("\n[!] edge-tts non trouve. pip install edge-tts")
    else:
        print("[*] Edge-TTS detecte")

    # Pré-initialiser le pipeline spectral au démarrage
    print("\n[*] Initialisation du pipeline spectral harmonique...")
    pipeline = get_spectral_pipeline()
    if pipeline:
        print(f"[*] Pipeline OK — {len(pipeline.trainer.voice_profiles)} profils vocaux chargés")
        print(f"[*] Profils: {pipeline.trainer.list_profiles()}")
    else:
        print("[!] Pipeline spectral non disponible (mode Edge-TTS uniquement)")

    server = HTTPServer(("", PORT), TTSServer)
    print(f"\n[*] Serveur demarre sur http://localhost:{PORT}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Arret du serveur.")
        server.shutdown()
