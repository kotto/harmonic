#!/usr/bin/env python3
"""
SPEECH SERVICE — STT + TTS open-source pour KA Phone
======================================================
Speech-to-Text : faster-whisper (modèle tiny, CPU, ~75 Mo)
Text-to-Speech : Piper TTS (modèle français siwis/upmc, ~50 Mo)

Installation :
  pip install faster-whisper
  # Piper : téléchargement automatique du binaire au premier usage

Usage :
  from speech_service import SpeechService
  svc = SpeechService()
  text = svc.transcribe("audio.wav")  # STT
  svc.synthesize("Bonjour", "output.wav")  # TTS
"""

import os, sys, json, io, wave, tempfile, subprocess, shutil, hashlib, asyncio, time, threading
from typing import Optional, Tuple, List, Generator
from collections import OrderedDict
import numpy as np

# faster-whisper : détection SANS import — `import faster_whisper` tire
# ctranslate2 → torch (~7 s). L'import réel est différé au premier
# appel de _load_whisper() (transcription uniquement).
try:
    import importlib.util
    HAS_WHISPER = importlib.util.find_spec("faster_whisper") is not None
except Exception:
    HAS_WHISPER = False

# edge_tts : détection sans import (aiohttp ≈ 1-2 s) — import différé à la synthèse
try:
    HAS_EDGE_TTS = importlib.util.find_spec("edge_tts") is not None
except Exception:
    HAS_EDGE_TTS = False
# Voix françaises neuronales (gratuites via API Edge)
EDGE_FR_VOICES = [
    "fr-FR-HenriNeural",     # Homme, chaleureux
    "fr-FR-DeniseNeural",    # Femme, claire
    "fr-FR-EloiseNeural",    # Femme, jeune
    "fr-FR-VivienneNeural",  # Femme, neutre
    "fr-FR-JeromeNeural",    # Homme, professionnel
] if HAS_EDGE_TTS else []

# VAD + Streaming TTS (intégration)
try:
    from vad_service import VADService, VADAudioRecorder
    HAS_VAD = True
except ImportError:
    HAS_VAD = False

try:
    from tts_streaming import TTSStreamingService, TTSCache, combine_audio_chunks
    HAS_STREAMING_TTS = True
except ImportError:
    HAS_STREAMING_TTS = False

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "speech")
PIPER_DIR = os.path.join(DATA_DIR, "piper")
PIPER_BINARY_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
PIPER_FR_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx"
PIPER_FR_MODEL_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PIPER_DIR, exist_ok=True)


class SpeechService:
    """Service de reconnaissance et synthèse vocale."""

    def __init__(self):
        self.whisper_model = None
        self.whisper_loaded = False
        self.piper_available = self._check_piper()

    # ═══ SPEECH-TO-TEXT (faster-whisper) ═══

    def _load_whisper(self):
        if self.whisper_loaded or not HAS_WHISPER:
            return self.whisper_model
        try:
            from faster_whisper import WhisperModel  # import paresseux (lourd)
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8",
                                              download_root=os.path.join(DATA_DIR, "whisper"))
            self.whisper_loaded = True
            print(f"  [Speech] faster-whisper modele tiny charge")
        except Exception as e:
            print(f"  [Speech] Erreur chargement faster-whisper: {e}")
            self.whisper_model = None
        return self.whisper_model

    def transcribe(self, audio_path: str, language: str = "fr") -> Optional[Tuple[str, float]]:
        """
        Transcrit un fichier audio en texte.
        Retourne (texte, confiance) ou None si échec.
        """
        model = self._load_whisper()
        if model is None:
            return None
        try:
            segments, info = model.transcribe(audio_path, language=language, beam_size=5,
                                               vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
            # Le générateur ne peut être consommé qu'une seule fois
            segments = list(segments)
            full_text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
            confidence = sum(seg.avg_logprob for seg in segments) / max(len(segments), 1)
            # Convert logprob to 0-1 confidence
            confidence = max(0.0, min(1.0, (confidence + 2.0) / 4.0))
            return full_text, confidence
        except Exception as e:
            print(f"  [Speech] Erreur transcription: {e}")
            return None

    def transcribe_bytes(self, wav_bytes: bytes, language: str = "fr") -> Optional[Tuple[str, float]]:
        """Transcrit des bytes WAV en texte."""
        import tempfile
        # Fichier temporaire unique (évite les collisions entre requêtes concurrentes)
        fd, tmp_path = tempfile.mkstemp(prefix="stt_", suffix=".wav", dir=DATA_DIR)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(wav_bytes)
            return self.transcribe(tmp_path, language)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ═══ TEXT-TO-SPEECH (Piper) ═══

    def _check_piper(self) -> bool:
        """Vérifie si Piper est disponible."""
        piper_exe = self._piper_exe()
        return os.path.exists(piper_exe)

    def _piper_exe(self) -> str:
        return os.path.join(PIPER_DIR, "piper", "piper.exe")

    def _piper_model_path(self) -> str:
        return os.path.join(PIPER_DIR, "fr_FR-siwis-medium.onnx")

    def _piper_model_json_path(self) -> str:
        return os.path.join(PIPER_DIR, "fr_FR-siwis-medium.onnx.json")

    def ensure_piper_installed(self) -> bool:
        """Installe Piper si nécessaire."""
        if self.piper_available:
            return True

        print("  [Speech] Installation de Piper TTS...")
        try:
            import urllib.request

            # Télécharger le binaire Piper
            piper_zip = os.path.join(PIPER_DIR, "piper_windows.zip")
            if not os.path.exists(self._piper_exe()):
                print("    Telechargement du binaire Piper...")
                urllib.request.urlretrieve(PIPER_BINARY_URL, piper_zip)
                import zipfile
                with zipfile.ZipFile(piper_zip, 'r') as zf:
                    zf.extractall(PIPER_DIR)
                os.remove(piper_zip)
                print("    Binaire Piper installe.")

            # Télécharger le modèle français
            model_path = self._piper_model_path()
            if not os.path.exists(model_path):
                print("    Telechargement du modele francais (siwis medium)...")
                urllib.request.urlretrieve(PIPER_FR_MODEL_URL, model_path)
            json_path = self._piper_model_json_path()
            if not os.path.exists(json_path):
                urllib.request.urlretrieve(PIPER_FR_MODEL_JSON_URL, json_path)
                print("    Modele francais installe (~50 Mo).")

            self.piper_available = True
            print("  [Speech] Piper TTS pret.")
            return True
        except Exception as e:
            print(f"  [Speech] Erreur installation Piper: {e}")
            return False

    def synthesize(self, text: str, output_path: str, speed: float = 1.0) -> bool:
        """
        Synthetise du texte en parole via Piper.
        Retourne True si succes.
        """
        if not self.piper_available:
            if not self.ensure_piper_installed():
                return False
            if not self.piper_available:
                return False

        piper_exe = self._piper_exe()
        model_path = self._piper_model_path()

        try:
            # Piper lit le texte sur STDIN ; -f désigne le fichier WAV de sortie.
            # length_scale > 1 = parole PLUS LENTE (inverse de notre convention speed).
            cmd = [piper_exe, "-m", model_path, "-f", output_path]
            if speed != 1.0:
                cmd.extend(["--length_scale", str(round(1.0 / max(speed, 0.25), 3))])

            subprocess.run(cmd, input=text, capture_output=True, text=True,
                           encoding="utf-8", timeout=60)

            return os.path.exists(output_path) and os.path.getsize(output_path) > 100
        except Exception as e:
            print(f"  [Speech] Erreur synthese Piper: {e}")
            return False

    def synthesize_bytes(self, text: str, speed: float = 1.0) -> Optional[bytes]:
        """Synthetise et retourne les bytes WAV."""
        import tempfile
        fd, tmp_output = tempfile.mkstemp(prefix="tts_", suffix=".wav", dir=DATA_DIR)
        os.close(fd)
        try:
            if self.synthesize(text, tmp_output, speed):
                with open(tmp_output, "rb") as f:
                    return f.read()
            return None
        finally:
            if os.path.exists(tmp_output):
                os.remove(tmp_output)

    # ═══ TEXT-TO-SPEECH (Edge-TTS — voix neuronales Microsoft, gratuit) ═══

    def is_edge_tts_available(self) -> bool:
        return HAS_EDGE_TTS

    def synthesize_edge(self, text: str, output_path: str, voice: str = None, speed: float = 1.0) -> bool:
        """
        Synthetise du texte en parole via Edge-TTS (Microsoft).
        Voix neuronales gratuites, qualité quasi-humaine.
        Retourne True si succes.
        """
        if not HAS_EDGE_TTS:
            return False

        if voice is None:
            import random
            voice = random.choice(EDGE_FR_VOICES)

        # Construire le paramètre de vitesse au format Edge-TTS: "+20%" ou "-10%"
        rate_str = f"{int((speed - 1.0) * 100):+d}%"

        async def _run():
            import edge_tts  # import paresseux (aiohttp ≈ 1-2 s au 1er appel)
            communicate = edge_tts.Communicate(text, voice, rate=rate_str)
            await communicate.save(output_path)

        try:
            # Détecter si on est déjà dans une event loop
            try:
                loop = asyncio.get_running_loop()
                # On est dans un contexte async — utiliser run_coroutine_threadsafe
                import concurrent.futures
                future = asyncio.run_coroutine_threadsafe(_run(), loop)
                future.result(timeout=60)
            except RuntimeError:
                # Pas de loop running — on peut utiliser asyncio.run
                asyncio.run(_run())

            return os.path.exists(output_path) and os.path.getsize(output_path) > 100
        except Exception as e:
            print(f"  [Speech] Erreur synthese Edge-TTS: {e}")
            return False

    def synthesize_bytes_edge(self, text: str, voice: str = None, speed: float = 1.0) -> Optional[bytes]:
        """Synthetise via Edge-TTS et retourne les bytes MP3."""
        import tempfile
        fd, tmp_output = tempfile.mkstemp(prefix="tts_edge_", suffix=".mp3", dir=DATA_DIR)
        os.close(fd)
        try:
            if self.synthesize_edge(text, tmp_output, voice, speed):
                with open(tmp_output, "rb") as f:
                    return f.read()
            return None
        finally:
            if os.path.exists(tmp_output):
                os.remove(tmp_output)

    # ═══ FALLBACK: Web Speech API (navigateur) ═══
    # Quand le serveur n'a pas faster-whisper, le front utilise l'API navigateur

    def is_stt_available(self) -> bool:
        # Ne PAS charger le modèle ici : le chargement (~75 Mo, plusieurs secondes)
        # est différé au premier appel de transcribe().
        return HAS_WHISPER

    def is_tts_available(self) -> bool:
        """Edge-TTS prioritaire, sinon Piper."""
        if HAS_EDGE_TTS:
            return True
        return self.piper_available or self.ensure_piper_installed()

    def get_capabilities(self) -> dict:
        tts_engine = "none"
        if HAS_EDGE_TTS:
            tts_engine = "Edge-TTS (Microsoft Neural)"
        elif self.piper_available:
            tts_engine = "Piper TTS (siwis medium)"
        return {
            "stt": self.is_stt_available(),
            "stt_engine": "faster-whisper (tiny)",
            "tts": self.is_tts_available(),
            "tts_engine": tts_engine,
        }

    # Mapping partagé des noms courts → voix Edge-TTS complètes
    EDGE_SHORT_MAP = {
        "henri": "fr-FR-HenriNeural",
        "denise": "fr-FR-DeniseNeural",
        "eloise": "fr-FR-EloiseNeural",
        "vivienne": "fr-FR-VivienneNeural",
        "jerome": "fr-FR-JeromeNeural",
    }

    def resolve_edge_voice(self, voice: Optional[str], default: str = "fr-FR-HenriNeural") -> str:
        """Accepte les noms courts ('henri', 'denise') ou complets ('fr-FR-HenriNeural')."""
        if voice is None:
            return default
        return self.EDGE_SHORT_MAP.get(voice.lower(), voice)

    def synthesize_best_ex(self, text: str, voice: str = None, speed: float = 1.0) -> Optional[Tuple[bytes, str]]:
        """
        Synthetise avec le meilleur moteur disponible : Edge-TTS → Piper → None.
        Retourne (audio_bytes, format) où format vaut 'mp3' (Edge-TTS) ou 'wav' (Piper),
        ou None si aucun moteur n'a réussi.
        """
        # 1. Edge-TTS (qualité quasi-humaine, gratuit)
        if HAS_EDGE_TTS:
            edge_voice = self.resolve_edge_voice(voice)
            result = self.synthesize_bytes_edge(text, edge_voice, speed)
            if result:
                return result, "mp3"

        # 2. Piper (local, open-source)
        result = self.synthesize_bytes(text, speed)
        if result:
            return result, "wav"

        return None

    def synthesize_best(self, text: str, output_path: str = None, voice: str = None, speed: float = 1.0) -> Optional[bytes]:
        """
        Synthetise avec le meilleur moteur disponible : Edge-TTS → Piper → None.
        Retourne les bytes audio (MP3 pour Edge-TTS, WAV pour Piper).
        Accepte les noms courts ('henri', 'denise') ou complets ('fr-FR-HenriNeural').
        """
        res = self.synthesize_best_ex(text, voice=voice, speed=speed)
        return res[0] if res else None

    # ═══ VAD (Voice Activity Detection) ═══

    def is_vad_available(self) -> bool:
        return HAS_VAD

    def create_vad(self) -> Optional['VADService']:
        """Crée une instance VAD."""
        if not HAS_VAD:
            return None
        try:
            return VADService(sample_rate=16000, frame_duration_ms=30)
        except Exception as e:
            print(f"  [Speech] Erreur création VAD: {e}")
            return None

    def create_recorder(self) -> Optional['VADAudioRecorder']:
        """Crée un enregistreur avec VAD intégré."""
        if not HAS_VAD:
            return None
        try:
            return VADAudioRecorder(sample_rate=16000, chunk_duration_ms=30)
        except Exception as e:
            print(f"  [Speech] Erreur création Recorder: {e}")
            return None

    # ═══ STREAMING TTS ═══

    def is_streaming_tts_available(self) -> bool:
        return HAS_STREAMING_TTS

    def create_streaming_tts(self) -> Optional['TTSStreamingService']:
        """Crée un service TTS avec streaming, cache, et barge-in."""
        if not HAS_STREAMING_TTS:
            return None
        try:
            tts = TTSStreamingService(speech_service=self)
            # Lier le VAD si disponible
            if HAS_VAD:
                vad = self.create_vad()
                if vad:
                    tts.set_vad(vad)
            return tts
        except Exception as e:
            print(f"  [Speech] Erreur création Streaming TTS: {e}")
            return None

    # ═══ BARGE-IN ═══

    def request_barge_in(self, tts_service: Optional['TTSStreamingService'] = None) -> bool:
        """
        Demande l'interruption du TTS en cours.
        Retourne True si un barge-in a été déclenché.
        """
        if tts_service:
            tts_service.request_barge_in()
            return True
        return False

    # ═══ CAPABILITIES (mise à jour) ═══

    def get_full_capabilities(self) -> dict:
        """Retourne les capacités complètes incluant VAD et streaming."""
        caps = self.get_capabilities()
        caps.update({
            "vad": self.is_vad_available(),
            "vad_engine": "silero-vad + energy-fallback" if HAS_VAD and VADService.has_silero() else ("energy-based" if HAS_VAD else "none"),
            "streaming_tts": self.is_streaming_tts_available(),
            "barge_in": self.is_streaming_tts_available(),
        })
        return caps


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    svc = SpeechService()
    print("Speech Service - Test")
    print(f"  STT (faster-whisper): {svc.is_stt_available()}")
    print(f"  TTS (Piper): {svc.is_tts_available()}")
    print(f"  Capabilities: {json.dumps(svc.get_capabilities(), indent=2)}")