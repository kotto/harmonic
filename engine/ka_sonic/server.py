"""
KA Sonic Server — Blueprint Flask pour l'API de synthèse vocale.

Endpoints :
  POST /api/voice/speak        → WAV complet (RIFF header)
  POST /api/voice/stream       → WAV chunké phrase par phrase
  GET  /api/voice/voices       → liste voix disponibles
  GET  /api/voice/capabilities → capacités détectées
  GET  /api/voice/stats        → stats sessions + moteur
  POST /api/voice/clone        → clone une voix (multipart WAV)

Sécurité :
  - Auth configurable (X-API-Key / Bearer token)
  - Rate limiting par user_id (header X-User-Id) avec fallback IP
  - Validation d'entrée (longueur max, détection répétition)
  - Anti-fuite mémoire rate limit store

Branchement :
    from ka_sonic.server import register_ka_sonic
    register_ka_sonic(app)
"""

import os
import sys
import io
import time
import struct
import threading
import logging
from typing import Optional, Dict, Deque
from collections import deque

from flask import Blueprint, request, jsonify, send_file, Response

log = logging.getLogger("ka_sonic.server")

# ═══════════════════════════════════════════════════════════════════════════════
# Blueprint
# ═══════════════════════════════════════════════════════════════════════════════

ka_sonic_bp = Blueprint("ka_sonic", __name__, url_prefix="/api/voice")

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

AUTH_REQUIRED = os.environ.get("KA_SONIC_AUTH_REQUIRED", "0") == "1"
API_KEYS = set(
    k.strip() for k in os.environ.get("KA_SONIC_API_KEYS", "").split(",") if k.strip()
)

TTS_RATE_LIMIT_WINDOW = 60
TTS_RATE_LIMIT_MAX = 20
_rate_limit_store: Dict[str, Deque[float]] = {}
_rate_limit_lock = threading.Lock()
_rate_limit_max_entries = 2000
_last_rate_cleanup = time.time()

MAX_TEXT_LENGTH = 2000
MAX_REPETITION_RATIO = 0.5
MAX_UPLOAD_SIZE = 5 * 1024 * 1024

# Session manager (lazy init)
_session_mgr = None


def _get_manager():
    global _session_mgr
    if _session_mgr is None:
        from .session import get_session_manager
        _session_mgr = get_session_manager()
    return _session_mgr


# ═══════════════════════════════════════════════════════════════════════════════
# Utilitaires
# ═══════════════════════════════════════════════════════════════════════════════

def _user_id() -> str:
    return request.headers.get("X-User-Id", "").strip() or \
           request.headers.get("X-Forwarded-For", request.remote_addr or "anonymous")


def _client_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "0.0.0.0")


def _json() -> dict:
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:
        return {}


def _validate_text(text: str) -> Optional[tuple]:
    """Valide l'entrée. Retourne (erreur, status) ou None."""
    if not text:
        return jsonify({"error": "missing 'text'"}), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"text too long ({len(text)} chars, max {MAX_TEXT_LENGTH})"}), 400
    if len(text) > 10:
        from collections import Counter
        if Counter(text.lower()).most_common(1)[0][1] / len(text) > MAX_REPETITION_RATIO:
            return jsonify({"error": "excessive character repetition"}), 400
    return None


def _check_rate(user_id: str) -> Optional[tuple]:
    """Rate limiting. Retourne (erreur, status) ou None."""
    global _last_rate_cleanup
    now = time.time()
    window = now - TTS_RATE_LIMIT_WINDOW

    with _rate_limit_lock:
        # Anti-fuite
        if len(_rate_limit_store) > _rate_limit_max_entries or (now - _last_rate_cleanup) > 300:
            expired = [k for k, v in _rate_limit_store.items() if not v or v[-1] < window]
            for k in expired:
                del _rate_limit_store[k]
            _last_rate_cleanup = now

        ts = _rate_limit_store.get(user_id)
        if ts is None:
            ts = deque()
            _rate_limit_store[user_id] = ts
        while ts and ts[0] < window:
            ts.popleft()
        if len(ts) >= TTS_RATE_LIMIT_MAX:
            retry = int(ts[0] - window)
            return jsonify({"error": "rate limit exceeded", "retry_after_seconds": max(1, retry)}), 429
        ts.append(now)
    return None


def _check_auth() -> Optional[tuple]:
    """Vérifie l'authentification."""
    if not AUTH_REQUIRED:
        return None
    api_key = request.headers.get("X-API-Key", "").strip()
    if api_key and api_key in API_KEYS:
        return None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth[7:].strip() in API_KEYS:
        return None
    return jsonify({"error": "authentication required", "methods": ["X-API-Key", "Bearer"]}), 401


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@ka_sonic_bp.route("/capabilities", methods=["GET"])
def capabilities_endpoint():
    from . import capabilities
    return jsonify(capabilities())


@ka_sonic_bp.route("/voices", methods=["GET"])
def voices_endpoint():
    uid = _user_id()
    bridge = _get_manager().get_bridge(uid)
    return jsonify({"voices": bridge.voices, "default": bridge._default_voice})


@ka_sonic_bp.route("/stats", methods=["GET"])
def stats_endpoint():
    return jsonify({
        "sessions": _get_manager().stats(),
    })


@ka_sonic_bp.route("/speak", methods=["POST"])
def speak_endpoint():
    """Synthétise un texte en WAV complet."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    uid = _user_id()
    rate_err = _check_rate(uid)
    if rate_err:
        return rate_err

    data = _json()
    text = data.get("text", "").strip()
    
    err = _validate_text(text)
    if err:
        return err

    voice = data.get("voice", "homme")
    speed = max(0.25, min(2.0, float(data.get("speed", 1.0))))
    emotion = data.get("emotion", "neutre")

    try:
        bridge = _get_manager().get_bridge(uid)
        wav = bridge.speak(text, voice=voice, speed=speed, emotion=emotion)
    except Exception as e:
        log.exception("/speak error")
        return jsonify({"error": str(e)}), 500

    log.info(f"🎙️ /speak '{text[:40]}' voice={voice} emotion={emotion} user={uid} [{len(wav)}B]")
    return send_file(io.BytesIO(wav), mimetype="audio/wav", download_name="ka_speech.wav")


@ka_sonic_bp.route("/stream", methods=["POST"])
def stream_endpoint():
    """Stream WAV par phrases (chaque chunk = WAV RIFF complet)."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    uid = _user_id()
    rate_err = _check_rate(uid)
    if rate_err:
        return rate_err

    data = _json()
    text = data.get("text", "").strip()
    err = _validate_text(text)
    if err:
        return err

    voice = data.get("voice", "homme")
    speed = max(0.25, min(2.0, float(data.get("speed", 1.0))))
    emotion = data.get("emotion", "neutre")

    import re
    sentences = re.split(r"(?<=[.!?])\s+", text)

    def generate():
        bridge = _get_manager().get_bridge(uid)
        for sent in sentences:
            if not sent.strip():
                continue
            try:
                wav = bridge.speak(sent.strip(), voice=voice, speed=speed, emotion=emotion)
                yield wav
            except Exception:
                yield b""

    return Response(generate(), mimetype="audio/wav")


@ka_sonic_bp.route("/clone", methods=["POST"])
def clone_endpoint():
    """Clone une voix depuis un WAV (multipart)."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    uid = _user_id()
    rate_err = _check_rate(uid)
    if rate_err:
        return rate_err

    if "wav" not in request.files:
        return jsonify({"error": "missing 'wav' file"}), 400

    name = (request.form.get("voice_name") or "").strip()
    if not name:
        return jsonify({"error": "missing 'voice_name'"}), 400
    name = "".join(c for c in name if c.isalnum() or c in "-_")[:32]

    wav_file = request.files["wav"]
    wav_file.seek(0, 2)
    size = wav_file.tell()
    wav_file.seek(0)

    if size > MAX_UPLOAD_SIZE:
        return jsonify({"error": f"file too large ({size}B, max {MAX_UPLOAD_SIZE}B)"}), 400
    if size < 44:
        return jsonify({"error": "file too small for WAV"}), 400

    header = wav_file.read(44)
    wav_file.seek(0)
    if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
        return jsonify({"error": "invalid WAV (no RIFF header)"}), 400

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
        wav_file.save(tmp_path)

    try:
        ok = _get_manager().clone_voice(uid, tmp_path, name)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if not ok:
        return jsonify({"error": "clone failed"}), 500

    log.info(f"🎭 Voix clonée: {name} (user={uid})")
    return jsonify({"ok": True, "voice": name})


# ═══════════════════════════════════════════════════════════════════════════════
# Enregistrement
# ═══════════════════════════════════════════════════════════════════════════════

def register_ka_sonic(app) -> bool:
    """Enregistre le Blueprint KA Sonic sur une app Flask."""
    try:
        app.register_blueprint(ka_sonic_bp)
        log.info("🎙️ KA Sonic Blueprint enregistré sur /api/voice")
        return True
    except Exception as e:
        log.error(f"register_ka_sonic échec: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# CLI autonome
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    try:
        from flask_cors import CORS
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    except ImportError:
        pass
    register_ka_sonic(app)

    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8770)
    args = p.parse_args()

    print(f"\n🎙️ KA Sonic v2 — http://{args.host}:{args.port}")
    print("   POST /api/voice/speak  body: {\"text\": \"Bonjour\"}")
    print("   GET  /api/voice/voices")
    print("   GET  /api/voice/capabilities\n")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
