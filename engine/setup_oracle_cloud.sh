#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════╗
# ║  ORACLE CLOUD — Setup Qwen 3B + TTS Haute Qualité               ║
# ║  Always Free: 4 cœurs ARM, 24 Go RAM, 200 Go stockage           ║
# ╚═══════════════════════════════════════════════════════════════════╝
#
# EXÉCUTION (sur le serveur Oracle) :
#   ssh ubuntu@<IP_ORACLE>
#   curl -sSL https://raw.githubusercontent.com/.../setup_oracle.sh | bash
#   OU copier ce fichier et l'exécuter : bash setup_oracle.sh
#
# DURÉE : ~15-20 minutes (dépend du téléchargement)
# ESPACE : ~5 Go (modèle Qwen 2 Go + TTS 1.5 Go + dépendances)
# PORT : 8080 (API)

set -euo pipefail

echo "🌊 ORACLE CLOUD — Setup THU : Qwen 3B + TTS Haute Qualité"
echo "=========================================================="
echo ""

# ═══════════════════════════════════════════════════════════════════
# 1. MISE À JOUR SYSTÈME
# ═══════════════════════════════════════════════════════════════════
echo "📦 Mise à jour du système..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv \
    build-essential cmake curl git wget ffmpeg espeak-ng \
    libsndfile1 libsndfile1-dev > /dev/null 2>&1
echo "   ✅ Système prêt"

# ═══════════════════════════════════════════════════════════════════
# 2. ENVIRONNEMENT PYTHON
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "🐍 Création de l'environnement Python..."
cd ~
python3 -m venv thu_env --system-site-packages
source thu_env/bin/activate
pip install --upgrade pip -q
echo "   ✅ Environnement créé"

# ═══════════════════════════════════════════════════════════════════
# 3. LLM — Qwen 2.5 3B Instruct (llama.cpp)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "═" * 60
echo "  🤖 ÉTAPE 1 — LLM : Qwen 2.5 3B Instruct Q4_K_M"
echo "═" * 60

# Compiler llama.cpp (optimisé ARM)
echo "📦 Installation de llama-cpp-python..."
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
    pip install llama-cpp-python -q 2>&1 | tail -1
echo "   ✅ llama-cpp-python installé"

# Télécharger le modèle
MODEL_DIR=~/models
mkdir -p $MODEL_DIR
MODEL_FILE="$MODEL_DIR/Qwen2.5-3B-Instruct-Q4_K_M.gguf"

if [ -f "$MODEL_FILE" ]; then
    echo "   ✅ Modèle déjà présent : $MODEL_FILE"
else
    echo "📥 Téléchargement de Qwen 2.5 3B Q4_K_M (~2 Go)..."
    wget -q --show-progress \
        "https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf" \
        -O "$MODEL_FILE"
    echo "   ✅ Modèle téléchargé"
fi

SIZE_MB=$(du -m "$MODEL_FILE" | cut -f1)
echo "   📦 Taille : ${SIZE_MB} Mo"

# ═══════════════════════════════════════════════════════════════════
# 4. TTS — Synthèse Vocale Haute Qualité
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "═" * 60
echo "  🎙️  ÉTAPE 2 — TTS Haute Qualité (multi-voix)"
echo "═" * 60

# Option A : edge-tts (GRATUIT, excellent, zéro modèle, fr+en)
echo "📦 Installation de edge-tts (Microsoft Edge TTS gratuit)..."
pip install edge-tts -q
echo "   ✅ edge-tts : voix neurales FR (Denise, Henri, Eloise) + EN (Jenny, Guy, Aria)"

# Option B : Piper TTS (LOCAL, rapide, MIT, 60+ voix, <100ms)
echo ""
echo "📦 Installation de Piper TTS (synthèse locale, open source MIT)..."
PIPER_DIR=~/piper_tts
mkdir -p $PIPER_DIR

# Télécharger le binaire Piper (ARM64)
if [ ! -f "$PIPER_DIR/piper" ]; then
    wget -q "https://github.com/rhasspy/piper/releases/latest/download/piper_linux_aarch64.tar.gz" \
        -O /tmp/piper.tar.gz
    tar -xzf /tmp/piper.tar.gz -C $PIPER_DIR
    chmod +x $PIPER_DIR/piper/piper
    PIPER_BIN="$PIPER_DIR/piper/piper"
    echo "   ✅ Piper binaire installé (ARM64)"
else
    PIPER_BIN="$PIPER_DIR/piper/piper"
    echo "   ✅ Piper déjà installé"
fi

# Télécharger les voix FR + EN (haute qualité)
VOICES_DIR="$PIPER_DIR/voices"
mkdir -p $VOICES_DIR

# Français — voix féminine (sixtiz, qualité medium)
if [ ! -f "$VOICES_DIR/fr_FR-siwis-medium.onnx" ]; then
    echo "   📥 Téléchargement voix FR (siwis, medium)..."
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx" \
        -O "$VOICES_DIR/fr_FR-siwis-medium.onnx"
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json" \
        -O "$VOICES_DIR/fr_FR-siwis-medium.onnx.json"
fi

# Français — voix masculine (gilles, qualité low pour variété)
if [ ! -f "$VOICES_DIR/fr_FR-gilles-low.onnx" ]; then
    echo "   📥 Téléchargement voix FR (gilles, low)..."
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/gilles/low/fr_FR-gilles-low.onnx" \
        -O "$VOICES_DIR/fr_FR-gilles-low.onnx"
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/gilles/low/fr_FR-gilles-low.onnx.json" \
        -O "$VOICES_DIR/fr_FR-gilles-low.onnx.json"
fi

# Anglais — voix féminine (libritts, high quality)
if [ ! -f "$VOICES_DIR/en_US-libritts-high.onnx" ]; then
    echo "   📥 Téléchargement voix EN (libritts, high)..."
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts/high/en_US-libritts-high.onnx" \
        -O "$VOICES_DIR/en_US-libritts-high.onnx"
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts/high/en_US-libritts-high.onnx.json" \
        -O "$VOICES_DIR/en_US-libritts-high.onnx.json"
fi

# Installer le wrapper Python Piper
pip install piper-tts -q 2>/dev/null || echo "   ⚠️  piper-tts PyPI non disponible — utilisation via subprocess"

echo "   ✅ Piper TTS : local, rapide (<100ms), MIT, 60+ voix, offline"

# Option C : Voxtral TTS (Mistral) — CC BY-NC 4.0, non-commercial uniquement
echo ""
echo "   ℹ️  Voxtral TTS (Mistral) :"
echo "      • Modèle : CC BY-NC 4.0 (usage NON commercial uniquement)"
echo "      • Qualité : excellente, clonage vocal en 2-3s"
echo "      • API Mistral : payante (~$0.01/min), pas de tier gratuit"
echo "      • Pour usage médical commercial → licence séparée requise"
echo "      • Non installé par défaut (restriction de licence)"

# Option D : Coqui XTTS v2 (local, premium, clonage, CPML license)
echo ""
echo "📦 Installation de Coqui TTS (XTTS v2, premium, clonage vocal)..."
pip install TTS -q 2>&1 | tail -3 || echo "   ⚠️  Coqui TTS optionnel (~1.5 Go) — edge-tts + Piper suffisent"
echo "   ✅ TTS prêt (edge-tts + Piper + Coqui optionnel)"

# ═══════════════════════════════════════════════════════════════════
# 4b. STT — Reconnaissance Vocale (Whisper local)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "═" * 60
echo "  🎤 ÉTAPE 2b — STT (Speech-to-Text)"
echo "═" * 60

echo "📦 Installation de faster-whisper (local, MIT, CPU)..."
pip install faster-whisper -q 2>&1 | tail -1
echo "   ✅ faster-whisper installé (tiny model, ~1 Go RAM)"

# Télécharger le modèle Whisper tiny (~75 Mo)
WHISPER_CACHE=~/.cache/huggingface/hub
echo "   📥 Modèle Whisper tiny (~75 Mo) sera téléchargé au premier appel"
echo "   ✅ STT prêt (faster-whisper local + Voxtral API optionnel)"

# ═══════════════════════════════════════════════════════════════════
# 5. CRÉATION DU SERVEUR API
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "═" * 60
echo "  🌐 ÉTAPE 3 — Serveur API"
echo "═" * 60

cat > ~/thu_server.py << 'PYEOF'
"""
🌊 THU SERVER — Qwen 3B + TTS Haute Qualité
=============================================
API REST : /query (texte), /tts (synthèse vocale)

DÉMARRAGE :
  source ~/thu_env/bin/activate
  python ~/thu_server.py

ENDPOINTS :
  POST /query     → { "question": "...", "mode": "rapide|elite" }
  POST /tts       → { "text": "...", "lang": "fr|en", "voice": "female|male" }
  GET  /health    → statut
  GET  /voices    → listes des voix disponibles
"""

import sys, os, json, time, re, io, base64
from pathlib import Path
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ─── IMPORTS (lazy loading au démarrage) ───
import asyncio
import subprocess

MODEL_PATH = os.path.expanduser("~/models/Qwen2.5-3B-Instruct-Q4_K_M.gguf")
TTS_MODE = "edge"  # "edge", "piper", "coqui", ou "voxtral"

# Importer le moteur de voix émotionnelle
try:
    from harmonic_voice_emotion import HarmonicVoiceEmotion
    VOICE_EMOTION = HarmonicVoiceEmotion()
    HAS_EMOTION = True
except ImportError:
    VOICE_EMOTION = None
    HAS_EMOTION = False

# Importer le moteur STT + Voice Analyzer
try:
    from harmonic_stt import STTEngine, HarmonicVoiceAnalyzer, BidirectionalPipeline
    STT_ENGINE = STTEngine()
    VOICE_ANALYZER = HarmonicVoiceAnalyzer()
    BIDIR_PIPELINE = BidirectionalPipeline(
        stt_engine=STT_ENGINE,
        voice_analyzer=VOICE_ANALYZER,
        voice_emotion=VOICE_EMOTION,
    )
    HAS_STT = True
    print(f"🎤 STT backends: {STT_ENGINE.available}")
except ImportError as e:
    STT_ENGINE = None
    VOICE_ANALYZER = None
    BIDIR_PIPELINE = None
    HAS_STT = False
    print(f"⚠️  STT non disponible: {e}")

# Chemins Piper TTS
PIPER_BIN = os.path.expanduser("~/piper_tts/piper/piper")
PIPER_VOICES = os.path.expanduser("~/piper_tts/voices")
PIPER_VOICES_MAP = {
    ("fr", "female"): "fr_FR-siwis-medium",
    ("fr", "male"):   "fr_FR-gilles-low",
    ("en", "female"): "en_US-libritts-high",
    ("en", "male"):   "en_US-libritts-high",
}

# Voxtral (Mistral) — nécessite clé API et licence commerciale
VOXTRAL_API_KEY = os.environ.get("VOXTRAL_API_KEY", "")
VOXTRAL_BASE_URL = "https://api.mistral.ai/v1"

# ─── QWEN PHRASER ───

class QwenPhraser:
    """Client LLM local — reformulation de faits médicaux."""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._llm = None
    
    @property
    def llm(self):
        if self._llm is None:
            from llama_cpp import Llama
            print(f"🤖 Chargement de Qwen 3B...")
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=4096,
                n_threads=4,
                verbose=False,
            )
            print(f"   ✅ Modèle chargé")
        return self._llm
    
    def phrase(self, facts_text: str, question: str = "",
               lang: str = "fr") -> str:
        """Reformule des faits en français ou anglais naturel."""
        
        if lang == "fr":
            system_prompt = (
                "Tu es un assistant médical francophone. "
                "Reformule les faits fournis en français naturel et élégant, "
                "comme le ferait un médecin. "
                "N'invente RIEN. N'ajoute AUCUNE information. "
                "Écris UN SEUL paragraphe fluide."
            )
        else:
            system_prompt = (
                "You are a medical assistant. "
                "Rephrase the provided facts in natural, elegant English, "
                "as a doctor would. "
                "Do NOT invent anything. Do NOT add ANY information. "
                "Write ONE fluent paragraph."
            )
        
        user_prompt = f"QUESTION : {question}\n\nFAITS :\n{facts_text}"
        
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=512,
            stop=["\n\n"],
        )
        return response["choices"][0]["message"]["content"]


# ─── TTS EDGE (Microsoft Neural, gratuit, fr+en) ───

async def edge_tts(text: str, lang: str = "fr", 
                   voice: str = "female") -> bytes:
    """Synthèse vocale via Microsoft Edge TTS (gratuit, neural)."""
    import edge_tts
    
    EDGE_VOICES = {
        ("fr", "female"): "fr-FR-DeniseNeural",
        ("fr", "male"):   "fr-FR-HenriNeural", 
        ("en", "female"): "en-US-JennyNeural", 
        ("en", "male"):   "en-US-GuyNeural",
        ("fr", "warm"):   "fr-FR-EloiseNeural",
        ("en", "warm"):   "en-US-AriaNeural",
    }
    
    voice_name = EDGE_VOICES.get((lang, voice), EDGE_VOICES[("fr", "female")])
    
    output_path = "/tmp/tts_output.mp3"
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)
    
    with open(output_path, "rb") as f:
        return f.read()


# ─── TTS PIPER (local, MIT, <100ms, 60+ voix) ───

def piper_tts(text: str, lang: str = "fr", 
              voice: str = "female") -> bytes:
    """Synthèse vocale via Piper TTS (local, open source MIT)."""
    voice_key = PIPER_VOICES_MAP.get((lang, voice), PIPER_VOICES_MAP[("fr", "female")])
    model_path = os.path.join(PIPER_VOICES, f"{voice_key}.onnx")
    model_config = os.path.join(PIPER_VOICES, f"{voice_key}.onnx.json")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Voix Piper introuvable: {model_path}")
    
    # Piper via subprocess (ultra-rapide)
    proc = subprocess.run(
        [PIPER_BIN, "--model", model_path, "--config", model_config,
         "--output_file", "/tmp/piper_output.wav"],
        input=text.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    
    if proc.returncode != 0:
        raise RuntimeError(f"Piper error: {proc.stderr.decode()}")
    
    # Optionnel : convertir WAV en MP3 avec ffmpeg
    subprocess.run(
        ["ffmpeg", "-i", "/tmp/piper_output.wav", 
         "-codec:a", "libmp3lame", "-qscale:a", "2", 
         "/tmp/tts_output.mp3", "-y"],
        capture_output=True, timeout=10,
    )
    
    with open("/tmp/tts_output.mp3", "rb") as f:
        return f.read()


# ─── TTS VOXTral (Mistral) — CC BY-NC 4.0, API payante ───

VOXTRAL_AVAILABLE = bool(os.environ.get("VOXTRAL_API_KEY", ""))

def voxtral_tts(text: str, lang: str = "fr",
                voice: str = "female",
                speed: float = 1.0,
                emotion: str = "neutre") -> bytes:
    """Synthèse vocale via Voxtral TTS (Mistral API).
    
    ⚠️  CC BY-NC 4.0 : usage NON commercial uniquement.
    Pour usage commercial → licence séparée avec Mistral.
    Nécessite VOXTRAL_API_KEY dans l'environnement.
    
    Paramètres vocaux supportés :
      voice  : "alloy", "echo", "shimmer", "fable", "onyx", "nova"
      speed  : 0.25 à 4.0 (1.0 = normal) — modulation de débit
      emotion: adapte la voix (via sélection + préfixe textuel)
    """
    import requests
    
    if not VOXTRAL_API_KEY:
        raise RuntimeError("VOXTRAL_API_KEY non définie. export VOXTRAL_API_KEY=votre_clef")
    
    # Mapping voix selon émotion
    VOIXTRAL_EMOTION_VOICES = {
        "calme":       "nova",      # voix douce
        "empathie":    "shimmer",   # voix chaleureuse
        "reconfort":   "shimmer",
        "joie":        "alloy",     # voix claire
        "enthousiasme": "fable",    # voix expressive
        "alerte":      "onyx",      # voix grave/sérieuse
        "urgence":     "onyx",
        "tristesse":   "echo",      # voix posée
        "neutre":      "alloy",
        "professionnel": "alloy",
    }
    
    # Sélection de la voix selon émotion + genre
    if voice == "female":
        voice_map = {"alloy": "alloy", "echo": "shimmer", "shimmer": "shimmer",
                     "nova": "nova", "fable": "fable", "onyx": "onyx"}
    else:
        voice_map = {"alloy": "onyx", "echo": "echo", "shimmer": "onyx",
                     "nova": "onyx", "fable": "fable", "onyx": "onyx"}
    
    voxtral_voice = voice_map.get(VOIXTRAL_EMOTION_VOICES.get(emotion, "alloy"), "alloy")
    
    headers = {
        "Authorization": f"Bearer {VOXTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "voxtral-mini-tts-2603",
        "input": text,
        "voice": voxtral_voice,
        "response_format": "mp3",
        "speed": max(0.25, min(4.0, speed)),
    }
    
    resp = requests.post(
        f"{VOXTRAL_BASE_URL}/audio/speech",
        headers=headers,
        json=payload,
        timeout=30,
    )
    
    if resp.status_code != 200:
        raise RuntimeError(f"Voxtral API error ({resp.status_code}): {resp.text[:200]}")
    
    return resp.content


# ─── TTS COQUI XTTS v2 (local, CPML, clonage vocal) ───

def coqui_tts(text: str, lang: str = "fr",
              voice: str = "female") -> bytes:
    """Synthèse vocale via Coqui XTTS v2 (local, premium)."""
    from TTS.api import TTS as CoquiTTS
    
    # Modèle XTTS v2 (multilingue, clonage vocal)
    tts = CoquiTTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
    
    output_path = "/tmp/coqui_output.wav"
    tts.tts_to_file(
        text=text,
        language=lang if lang == "fr" else "en",
        file_path=output_path,
    )
    
    # Convertir en MP3
    subprocess.run(
        ["ffmpeg", "-i", output_path, 
         "-codec:a", "libmp3lame", "-qscale:a", "2", 
         "/tmp/tts_output.mp3", "-y"],
        capture_output=True, timeout=10,
    )
    
    with open("/tmp/tts_output.mp3", "rb") as f:
        return f.read()


# ─── DISPATCHER TTS ───

def synthesize(text: str, lang: str = "fr", 
               voice: str = "female", mode: str = None) -> bytes:
    """Synthèse vocale — sélectionne le moteur selon le mode."""
    if mode is None:
        mode = TTS_MODE
    
    if mode == "edge":
        return asyncio.run(edge_tts(text, lang, voice))
    elif mode == "piper":
        return piper_tts(text, lang, voice)
    elif mode == "voxtral":
        return voxtral_tts(text, lang, voice)
    elif mode == "coqui":
        return coqui_tts(text, lang, voice)
    else:
        # Fallback : essayer dans l'ordre edge → piper
        try:
            return asyncio.run(edge_tts(text, lang, voice))
        except Exception:
            return piper_tts(text, lang, voice)


# ─── SERVEUR HTTP ───

PHRASER = None

class THUHandler(BaseHTTPRequestHandler):
    
    def _json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/health":
            self._json_response({
                "status": "ok",
                "model": "Qwen 2.5 3B Q4_K_M",
                "tts": TTS_MODE,
                "tts_engines": ["edge", "piper", "coqui", "voxtral"],
                "stt": HAS_STT,
                "stt_backends": STT_ENGINE.available if HAS_STT and STT_ENGINE else [],
                "emotion": HAS_EMOTION,
                "bidirectional": HAS_STT and BIDIR_PIPELINE is not None,
                "loaded": PHRASER is not None,
            })
        elif path == "/voices":
            voices_info = {
                "engines": {
                    "edge": {
                        "type": "Microsoft Edge Neural (gratuit, illimité)",
                        "fr": {"female": "Denise", "male": "Henri", "warm": "Eloise"},
                        "en": {"female": "Jenny", "male": "Guy", "warm": "Aria"},
                    },
                    "piper": {
                        "type": "Piper TTS (local, MIT, <100ms)",
                        "fr": {"female": "siwis-medium", "male": "gilles-low"},
                        "en": {"female": "libritts-high", "male": "libritts-high"},
                    },
                    "voxtral": {
                        "type": "Voxtral TTS — Mistral (CC BY‑NC 4.0, API payante)",
                        "requires": "VOXTRAL_API_KEY + licence commerciale",
                    },
                    "coqui": {
                        "type": "Coqui XTTS v2 (local, CPML, clonage vocal)",
                    },
                },
                "emotion": {
                    "available": HAS_EMOTION,
                    "emotions": list(EMOTIONAL_SPACE.keys()) if HAS_EMOTION else [],
                    "contexts": ["general", "diagnostic", "urgence", "conseil", "explication", "empathie"],
                    "description": "Modulation vocale émotionnelle par primitives THU (φ-pitch, φ-rate, φ-volume)",
                },
                "default_tts": TTS_MODE,
            }
        else:
            self._json_response({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        # Lire le body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._json_response({"error": "Invalid JSON"}, 400)
            return
        
        if path == "/query":
            question = data.get("question", "")
            mode = data.get("mode", "rapide")
            lang = data.get("lang", "fr")
            
            if not question:
                self._json_response({"error": "Missing 'question'"}, 400)
                return
            
            t0 = time.time()
            
            # Récupérer les faits depuis le retriever (appel interne)
            facts_text = data.get("facts", "")
            
            if mode == "elite" and facts_text:
                global PHRASER
                if PHRASER is None:
                    PHRASER = QwenPhraser(MODEL_PATH)
                
                response = PHRASER.phrase(facts_text, question, lang)
            else:
                response = facts_text or question
            
            elapsed = time.time() - t0
            
            self._json_response({
                "query": question,
                "answer": response,
                "mode": mode,
                "lang": lang,
                "time_ms": round(elapsed * 1000),
            })
        
        elif path == "/speak":
            # Pipeline complet : LLM + TTS + voix émotionnelle
            question = data.get("question", "")
            facts = data.get("facts", "")
            response_text = data.get("response_text", "")
            lang = data.get("lang", "fr")
            voice = data.get("voice", "female")
            tts_mode = data.get("tts_mode", TTS_MODE)
            context = data.get("context", "general")
            
            if not question and not response_text:
                self._json_response({"error": "Missing 'question' or 'response_text'"}, 400)
                return
            
            t0 = time.time()
            
            # 1. Si pas de réponse fournie, phraser avec Qwen
            if not response_text and facts:
                global PHRASER
                if PHRASER is None:
                    PHRASER = QwenPhraser(MODEL_PATH)
                response_text = PHRASER.phrase(facts, question, lang)
            elif not response_text:
                response_text = question
            
            # 2. Détection d'émotion + modulation vocale
            emotional_params = {}
            if HAS_EMOTION and VOICE_EMOTION:
                user_emotion = VOICE_EMOTION.detect_emotion(question, lang)
                voice_params = VOICE_EMOTION.get_voice_params(user_emotion, context, lang)
                meta = VOICE_EMOTION.to_emotion_metadata(user_emotion, voice_params)
                emotional_params = {
                    "emotion": user_emotion,
                    "voice_params": voice_params,
                    "metadata": meta,
                }
                
                # SSML pour edge-tts
                if tts_mode == "edge":
                    import edge_tts
                    ssml = VOICE_EMOTION.to_ssml(response_text, voice_params, user_emotion, context, lang)
                    voice_name = voice_params.get("voice", "fr-FR-DeniseNeural")
                    communicate = edge_tts.Communicate(ssml, voice_name)
                    output_path = "/tmp/tts_emotional.mp3"
                    asyncio.run(communicate.save(output_path))
                    with open(output_path, "rb") as f:
                        audio_bytes = f.read()
                else:
                    audio_bytes = synthesize(response_text, lang, voice, mode=tts_mode)
            else:
                audio_bytes = synthesize(response_text, lang, voice, mode=tts_mode)
            
            elapsed = time.time() - t0
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            self._json_response({
                "audio_base64": audio_b64,
                "format": "mp3",
                "response_text": response_text,
                "lang": lang, "voice": voice, "tts_mode": tts_mode,
                "time_ms": round(elapsed * 1000),
                **emotional_params,
            })
        
        elif path == "/listen":
            # STT + analyse émotionnelle de la voix
            lang = data.get("lang", "fr")
            audio_b64 = data.get("audio_base64", "")
            
            if not audio_b64:
                self._json_response({"error": "Missing 'audio_base64'"}, 400)
                return
            
            t0 = time.time()
            
            try:
                audio_bytes = base64.b64decode(audio_b64)
                
                if HAS_STT and BIDIR_PIPELINE:
                    result = BIDIR_PIPELINE.listen(audio_bytes, lang)
                elif HAS_STT and STT_ENGINE:
                    # Fallback: STT seul
                    transcription = STT_ENGINE.transcribe(audio_bytes, lang)
                    voice_emotion = VOICE_ANALYZER.analyze(audio_bytes) if VOICE_ANALYZER else {}
                    result = {
                        "text": transcription.get("text", ""),
                        "stt_backend": transcription.get("backend"),
                        "stt_confidence": transcription.get("confidence", 0),
                        "emotion_voice": voice_emotion,
                    }
                else:
                    result = {"error": "STT non disponible. Installer faster-whisper.", "text": ""}
                
                result["time_ms"] = round((time.time() - t0) * 1000)
                self._json_response(result)
                
            except Exception as e:
                self._json_response({"error": str(e), "text": ""}, 500)
        
        elif path == "/converse":
            # Boucle bidirectionnelle complète : audio → texte → réponse → audio
            lang = data.get("lang", "fr")
            audio_b64 = data.get("audio_base64", "")
            context = data.get("context", "general")
            voice = data.get("voice", "female")
            tts_mode = data.get("tts_mode", TTS_MODE)
            
            if not audio_b64:
                self._json_response({"error": "Missing 'audio_base64'"}, 400)
                return
            
            t0 = time.time()
            
            try:
                audio_bytes = base64.b64decode(audio_b64)
                
                if HAS_STT and BIDIR_PIPELINE:
                    result = BIDIR_PIPELINE.converse(
                        audio_bytes, lang, context, tts_mode, voice
                    )
                elif HAS_STT and STT_ENGINE:
                    # Fallback: STT → echo simple
                    transcription = STT_ENGINE.transcribe(audio_bytes, lang)
                    text = transcription.get("text", "")
                    result = {
                        "text": text,
                        "response_text": f"J'ai entendu : {text}" if text else "Je n'ai pas compris.",
                        "stt_backend": transcription.get("backend"),
                        "audio_base64": "",
                    }
                else:
                    result = {"error": "STT non disponible", "text": ""}
                
                result["time_ms"] = round((time.time() - t0) * 1000)
                self._json_response(result)
                
            except Exception as e:
                self._json_response({"error": str(e), "text": ""}, 500)
        
        elif path == "/tts":
            text = data.get("text", "")
            lang = data.get("lang", "fr")
            voice = data.get("voice", "female")
            tts_mode = data.get("tts_mode", TTS_MODE)
            
            if not text:
                self._json_response({"error": "Missing 'text'"}, 400)
                return
            
            t0 = time.time()
            
            try:
                audio_bytes = synthesize(text, lang, voice, mode=tts_mode)
                elapsed = time.time() - t0
                audio_b64 = base64.b64encode(audio_bytes).decode()
                
                self._json_response({
                    "audio_base64": audio_b64,
                    "format": "mp3",
                    "lang": lang, "voice": voice, "tts_mode": tts_mode,
                    "time_ms": round(elapsed * 1000),
                })
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        
        else:
            self._json_response({"error": "Not found"}, 404)


def main():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), THUHandler)
    print(f"🌊 THU Server — Qwen 3B + TTS Multi-Moteur + Voix Émotionnelle")
    print(f"   Port      : {port}")
    print(f"   LLM       : Qwen 2.5 3B Q4_K_M")
    print(f"   TTS       : {TTS_MODE} (edge-tts | piper | coqui | voxtral)")
    print(f"   Émotion   : HarmonicVoiceEmotion (φ-modulé)")
    print(f"   Démarrage : http://0.0.0.0:{port}")
    print()
    print(f"   Endpoints :")
    print(f"     POST /query   → LLM (reformulation de faits)")
    print(f"     POST /tts     → TTS (synthèse vocale + voix émotionnelle)")
    print(f"     POST /speak   → Pipeline complet (LLM + TTS + émotion)")
    print(f"     GET  /health   → Statut")
    print(f"     GET  /voices   → Voix et émotions disponibles")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du serveur")
        server.shutdown()


if __name__ == "__main__":
    main()
PYEOF

echo "   ✅ Serveur créé : ~/thu_server.py"

# ═══════════════════════════════════════════════════════════════════
# 6. SERVICE SYSTEMD (démarrage automatique)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "📦 Configuration du service systemd..."

cat | sudo tee /etc/systemd/system/thu-server.service > /dev/null << EOF
[Unit]
Description=THU Server — Qwen 3B + TTS
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER
Environment="PATH=/home/$USER/thu_env/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/$USER/thu_env/bin/python /home/$USER/thu_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable thu-server.service
echo "   ✅ Service installé"

# ═══════════════════════════════════════════════════════════════════
# 7. PORT ORACLE (ouvrir le firewall)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "🔓 Configuration du firewall Oracle..."

# Oracle Ubuntu utilise iptables par défaut
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || sudo apt-get install -y -qq iptables-persistent > /dev/null 2>&1 && sudo netfilter-persistent save

echo "   ✅ Port 8080 ouvert"
echo ""
echo "═" * 60
echo "  ✅ INSTALLATION TERMINÉE"
echo "═" * 60
echo ""
echo "  🚀 DÉMARRAGE MANUEL :"
echo "     source ~/thu_env/bin/activate"
echo "     python ~/thu_server.py"
echo ""
echo "  🚀 DÉMARRAGE AUTO :"
echo "     sudo systemctl start thu-server"
echo ""
echo "  🧪 TEST LLM :"
echo "     curl -X POST http://localhost:8080/query \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"question\":\"symptômes du paludisme\",\"facts\":\"Paludisme simple → présente: fièvre cyclique\\nPaludisme simple → présente: frissons\",\"mode\":\"elite\",\"lang\":\"fr\"}'"
echo ""
echo "  🎙️  TEST TTS (edge-tts) :"
echo "     curl -X POST http://localhost:8080/tts \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"text\":\"Bonjour, je suis votre assistant médical.\",\"lang\":\"fr\",\"voice\":\"female\",\"tts_mode\":\"edge\"}'"
echo ""
echo "  🎭 TEST VOIX ÉMOTIONNELLE (LLM + TTS + Émotion) :"
echo "     curl -X POST http://localhost:8080/speak \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"question\":\"Je suis très inquiet docteur, j\\\"ai de la fièvre depuis 3 jours.\",\"facts\":\"Paludisme simple → présente: fièvre cyclique\\nPaludisme simple → présente: frissons\\nPaludisme simple → traitement: CTA\",\"context\":\"empathie\",\"lang\":\"fr\"}'"
echo ""
echo "  🎤 TEST STT (reconnaissance vocale) :"
echo "     curl -X POST http://localhost:8080/listen \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"audio_base64\":\"...\",\"lang\":\"fr\"}'"
echo ""
echo "  🔄 TEST CONVERSATION (full duplex) :"
echo "     curl -X POST http://localhost:8080/converse \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"audio_base64\":\"...\",\"lang\":\"fr\",\"context\":\"general\"}'"
echo ""
echo "  📡 N'OUBLIE PAS : ouvrir le port 8080 dans la console Oracle Cloud"
echo "     (Virtual Cloud Network → Security List → Ingress Rules)"
echo ""
echo "  📡 N'OUBLIE PAS : ouvrir le port 8080 dans la console Oracle Cloud"
echo "     (Virtual Cloud Network → Security List → Ingress Rules)"
echo ""

# Démarrage du service
read -p "Démarrer le service maintenant ? [o/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    sudo systemctl start thu-server
    sleep 3
    sudo systemctl status thu-server --no-pager
fi