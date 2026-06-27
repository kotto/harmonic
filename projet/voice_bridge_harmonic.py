#!/usr/bin/env python3
"""
VOICE BRIDGE HARMONIQUE — STT (whisper.cpp) + Hologramme + TTS (Piper)
======================================================================
Intégration complète de la reconnaissance vocale et synthèse vocale
avec le système harmonique holographique.

Architecture :
  Micro → whisper.cpp (STT) → Hologramme → LLM → Piper (TTS) → Haut-parleur
                                    ↑                     |
                                    └─── Feedback ────────┘

Modes :
  --mode stt      : Test de reconnaissance vocale seule
  --mode tts      : Test de synthèse vocale seule
  --mode full     : Conversation vocale complète (STT + Hologramme + LLM + TTS)
  --mode simulate : Mode simulation (sans matériel audio, pour test)

Dépendances (optionnelles, installation automatique guidée) :
  - whisper.cpp  : Reconnaissance vocale (STT) — MIT, 75-142 Mo
  - piper-tts    : Synthèse vocale (TTS) — MIT, ~50 Mo
  - sounddevice  : Capture/lecture audio — MIT
  - numpy        : Déjà installé (moteur harmonique)

Usage :
  python voice_bridge_harmonic.py --mode full
  python voice_bridge_harmonic.py --mode stt --file audio.wav
  python voice_bridge_harmonic.py --mode simulate --prompt "Bonjour, comment ça va ?"
"""

import os
import sys
import json
import time
import wave
import struct
import hashlib
import argparse
import subprocess
import tempfile
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from collections import OrderedDict

import numpy as np

# Ajouter le projet au path
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# Imports du système harmonique (bypass torch)
from bridge_harmonic_deepseek_gguf import (
    BridgeHarmoniqueGGUF, CacheReseauHarmonique,
    detecter_modele_gguf, HologrammeMonde, TokeniseurOndes,
    LecteurResonantMultiple, VOCABULAIRE_BASE
)

# =========================================================================
# CONFIGURATION
# =========================================================================

# Modèles audio
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "tiny")  # tiny (75 Mo), base (142 Mo), small (466 Mo)
WHISPER_LANG = os.environ.get("WHISPER_LANG", "fr")       # Langue par défaut
PIPER_VOICE = os.environ.get("PIPER_VOICE", "fr_FR-siwis-medium")  # Voix française
PIPER_MODEL_PATH = os.environ.get("PIPER_MODEL_PATH", "")  # Chemin personnalisé

# Audio
SAMPLE_RATE = int(os.environ.get("AUDIO_SAMPLE_RATE", "16000"))
CHANNELS = int(os.environ.get("AUDIO_CHANNELS", "1"))
RECORD_SECONDS = int(os.environ.get("AUDIO_RECORD_SECONDS", "10"))
SILENCE_THRESHOLD = float(os.environ.get("AUDIO_SILENCE_THRESHOLD", "0.02"))
SILENCE_DURATION = int(os.environ.get("AUDIO_SILENCE_DURATION", "2"))  # secondes de silence avant stop

# =========================================================================
# DÉTECTION DES DÉPENDANCES
# =========================================================================

def _check_dependency(module_name: str, install_hint: str) -> bool:
    """Vérifie si un module Python est disponible."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        print(f"  ⚠️  {module_name} non installé. {install_hint}")
        return False

def _check_command(command: str) -> bool:
    """Vérifie si une commande système est disponible."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

@dataclass
class AudioCapabilities:
    """Capacités audio détectées du système."""
    stt_available: bool = False
    stt_method: str = "none"
    tts_available: bool = False
    tts_method: str = "none"
    microphone_available: bool = False
    speakers_available: bool = False
    
    def can_record(self) -> bool:
        return self.microphone_available and self.stt_available
    
    def can_speak(self) -> bool:
        return self.speakers_available and self.tts_available
    
    def can_full_conversation(self) -> bool:
        return self.can_record() and self.can_speak()

def detecter_capacites_audio() -> AudioCapabilities:
    """Détecte les capacités audio du système."""
    caps = AudioCapabilities()
    
    print("\n  Détection des capacités audio...")
    
    # --- STT (whisper.cpp) ---
    # Méthode 1 : binaire whisper.cpp dans le PATH
    if _check_command("whisper-cpp --version") or _check_command("whisper --version"):
        caps.stt_available = True
        caps.stt_method = "whisper.cpp (binary)"
        print("  ✅ whisper.cpp (binaire) détecté")
    # Méthode 2 : Python wrapper whisper-cpp
    elif _check_dependency("whisper_cpp", "pip install whisper-cpp-python"):
        caps.stt_available = True
        caps.stt_method = "whisper_cpp (Python)"
        print("  ✅ whisper_cpp (Python) détecté")
    # Méthode 3 : faster-whisper
    elif _check_dependency("faster_whisper", "pip install faster-whisper"):
        caps.stt_available = True
        caps.stt_method = "faster-whisper (Python)"
        print("  ✅ faster-whisper (Python) détecté")
    # Méthode 4 : openai-whisper
    elif _check_dependency("whisper", "pip install openai-whisper"):
        caps.stt_available = True
        caps.stt_method = "whisper (OpenAI, Python)"
        print("  ✅ openai-whisper (Python) détecté")
    else:
        print("  ⚠️  Aucun moteur STT détecté. Utilisation du mode simulation.")
        print("      Pour installer : pip install openai-whisper")
        print("      Ou compiler whisper.cpp : https://github.com/ggerganov/whisper.cpp")
    
    # --- TTS (Piper) ---
    # Méthode 1 : binaire piper dans le PATH
    if _check_command("piper --version") or _check_command("echo test | piper --model fr_FR-siwis-medium.onnx --output_file /dev/null"):
        caps.tts_available = True
        caps.tts_method = "piper (binary)"
        print("  ✅ piper (binaire) détecté")
    # Méthode 2 : Python wrapper piper-tts
    elif _check_dependency("piper_tts", "pip install piper-tts"):
        caps.tts_available = True
        caps.tts_method = "piper_tts (Python)"
        print("  ✅ piper_tts (Python) détecté")
    else:
        print("  ⚠️  Aucun moteur TTS détecté. Utilisation du mode simulation.")
        print("      Pour installer : pip install piper-tts")
        print("      Ou : https://github.com/rhasspy/piper")
    
    # --- Périphériques audio ---
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        output_devices = [d for d in devices if d['max_output_channels'] > 0]
        
        caps.microphone_available = len(input_devices) > 0
        caps.speakers_available = len(output_devices) > 0
        
        if caps.microphone_available:
            print(f"  ✅ Micro détecté : {input_devices[0]['name']}")
        else:
            print("  ⚠️  Aucun micro détecté")
        
        if caps.speakers_available:
            print(f"  ✅ Haut-parleur détecté : {output_devices[0]['name']}")
        else:
            print("  ⚠️  Aucun haut-parleur détecté")
            
    except ImportError:
        print("  ⚠️  sounddevice non installé (pip install sounddevice)")
        print("      Micro/haut-parleur non détectables sans sounddevice")
    
    return caps


# =========================================================================
# MOTEUR STT : WHISPER.CPP
# =========================================================================

class WhisperSTT:
    """
    Interface unifiée pour la reconnaissance vocale (STT).
    
    Supporte plusieurs backends :
    - whisper.cpp (binaire compilé)
    - whisper_cpp (wrapper Python)
    - faster-whisper (CTranslate2)
    - openai-whisper (implémentation Python originale)
    
    Priorité : whisper.cpp > faster-whisper > openai-whisper > simulation
    """
    
    def __init__(self, model_size: str = WHISPER_MODEL, language: str = WHISPER_LANG):
        self.model_size = model_size
        self.language = language
        self._model = None
        self._method = None
        self._init_backend()
    
    def _init_backend(self):
        """Initialise le meilleur backend disponible."""
        # Essayer whisper.cpp binaire
        if _check_command("whisper --version"):
            self._method = "whisper.cpp_binary"
            print(f"  [STT] whisper.cpp (binaire) — modèle: {self.model_size}")
            return
        
        # Essayer Python whisper_cpp
        try:
            from whisper_cpp import Whisper
            model_path = f"ggml-{self.model_size}.bin"
            self._model = Whisper(model_path)
            self._method = "whisper_cpp_python"
            print(f"  [STT] whisper_cpp (Python) — modèle: {self.model_size}")
            return
        except (ImportError, FileNotFoundError):
            pass
        
        # Essayer faster-whisper
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_size, device="cpu", compute_type="int8"
            )
            self._method = "faster_whisper"
            print(f"  [STT] faster-whisper — modèle: {self.model_size}")
            return
        except ImportError:
            pass
        
        # Essayer openai-whisper
        try:
            import whisper
            self._model = whisper.load_model(self.model_size)
            self._method = "openai_whisper"
            print(f"  [STT] openai-whisper — modèle: {self.model_size}")
            return
        except ImportError:
            pass
        
        # Fallback : simulation
        self._method = "simulation"
        print("  [STT] Mode simulation (pas de moteur STT disponible)")
    
    def transcrire(self, audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
        """
        Transcrit de l'audio en texte.
        
        Args:
            audio_data: Tableau numpy float32 [-1.0, 1.0]
            sample_rate: Taux d'échantillonnage
        
        Returns:
            Texte transcrit
        """
        if self._method == "simulation":
            return self._transcrire_simulation(audio_data)
        elif self._method == "whisper.cpp_binary":
            return self._transcrire_cpp_binary(audio_data, sample_rate)
        elif self._method == "whisper_cpp_python":
            return self._transcrire_cpp_python(audio_data, sample_rate)
        elif self._method == "faster_whisper":
            return self._transcrire_faster_whisper(audio_data, sample_rate)
        elif self._method == "openai_whisper":
            return self._transcrire_openai_whisper(audio_data, sample_rate)
        return ""
    
    def _transcrire_cpp_binary(self, audio: np.ndarray, sr: int) -> str:
        """Transcription via binaire whisper.cpp."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Sauvegarder en WAV 16-bit PCM
            audio_int16 = (audio * 32767).astype(np.int16)
            with wave.open(f.name, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(audio_int16.tobytes())
            
            try:
                result = subprocess.run(
                    ["whisper", "-m", f"ggml-{self.model_size}.bin",
                     "-l", self.language, "-f", f.name, "--no-timestamps"],
                    capture_output=True, text=True, timeout=30
                )
                return result.stdout.strip()
            except subprocess.TimeoutExpired:
                return "[Timeout STT]"
            finally:
                os.unlink(f.name)
    
    def _transcrire_cpp_python(self, audio: np.ndarray, sr: int) -> str:
        """Transcription via wrapper Python whisper_cpp."""
        if self._model is None:
            return "[STT non initialisé]"
        result = self._model.transcribe(audio, language=self.language)
        return result.get("text", "").strip()
    
    def _transcrire_faster_whisper(self, audio: np.ndarray, sr: int) -> str:
        """Transcription via faster-whisper (CTranslate2)."""
        if self._model is None:
            return "[STT non initialisé]"
        segments, _ = self._model.transcribe(audio, language=self.language)
        return " ".join(seg.text for seg in segments).strip()
    
    def _transcrire_openai_whisper(self, audio: np.ndarray, sr: int) -> str:
        """Transcription via openai-whisper."""
        if self._model is None:
            return "[STT non initialisé]"
        # Whisper s'attend à un audio normalisé
        audio_float = audio.astype(np.float32)
        result = self._model.transcribe(
            audio_float, language=self.language, fp16=False
        )
        return result.get("text", "").strip()
    
    def _transcrire_simulation(self, audio: np.ndarray) -> str:
        """Mode simulation : analyse l'énergie audio pour feedback."""
        energie = np.mean(np.abs(audio))
        duree = len(audio) / SAMPLE_RATE
        
        if energie < SILENCE_THRESHOLD:
            return "[silence]"
        
        # Simulation : retourne des infos sur l'audio capté
        return (
            f"[SIMULATION STT] Audio capté : {duree:.1f}s, "
            f"énergie={energie:.4f}. "
            f"Installez whisper.cpp pour la transcription réelle."
        )
    
    def transcrire_fichier(self, filepath: str) -> str:
        """Transcrit un fichier audio."""
        if self._method == "whisper.cpp_binary":
            try:
                result = subprocess.run(
                    ["whisper", "-m", f"ggml-{self.model_size}.bin",
                     "-l", self.language, "-f", filepath, "--no-timestamps"],
                    capture_output=True, text=True, timeout=60
                )
                return result.stdout.strip()
            except subprocess.TimeoutExpired:
                return "[Timeout STT]"
        
        # Charger et transcrire
        try:
            with wave.open(filepath, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                return self.transcrire(audio, wf.getframerate())
        except Exception as e:
            return f"[Erreur STT: {e}]"


# =========================================================================
# MOTEUR TTS : PIPER
# =========================================================================

class PiperTTS:
    """
    Interface unifiée pour la synthèse vocale (TTS).
    
    Supporte :
    - piper (binaire compilé)
    - piper-tts (wrapper Python)
    - simulation (fallback)
    """
    
    def __init__(self, voice: str = PIPER_VOICE):
        self.voice = voice
        self._model = None
        self._method = None
        self._init_backend()
    
    def _init_backend(self):
        """Initialise le meilleur backend disponible."""
        # Essayer piper-tts Python
        try:
            import piper_tts
            self._model = piper_tts
            self._method = "piper_tts_python"
            print(f"  [TTS] piper-tts (Python) — voix: {self.voice}")
            return
        except ImportError:
            pass
        
        # Essayer piper binaire
        if _check_command("piper --help"):
            self._method = "piper_binary"
            print(f"  [TTS] piper (binaire) — voix: {self.voice}")
            return
        
        # Fallback
        self._method = "simulation"
        print("  [TTS] Mode simulation (pas de moteur TTS disponible)")
    
    def synthetiser(self, texte: str) -> Optional[np.ndarray]:
        """
        Synthétise du texte en audio.
        
        Args:
            texte: Texte à synthétiser
        
        Returns:
            Tableau numpy float32 [-1.0, 1.0] ou None
        """
        if self._method == "simulation":
            return self._synthetiser_simulation(texte)
        elif self._method == "piper_tts_python":
            return self._synthetiser_python(texte)
        elif self._method == "piper_binary":
            return self._synthetiser_binary(texte)
        return None
    
    def _synthetiser_python(self, texte: str) -> np.ndarray:
        """Synthèse via wrapper Python piper-tts."""
        try:
            import io
            audio_bytes = self._model.synthesize(texte, self.voice)
            # piper-tts retourne des bytes WAV
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                return audio
        except Exception as e:
            print(f"  [TTS] Erreur Python : {e}")
            return self._synthetiser_fallback(texte)
    
    def _synthetiser_binary(self, texte: str) -> np.ndarray:
        """Synthèse via binaire piper."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            try:
                result = subprocess.run(
                    ["piper", "--model", self.voice,
                     "--output_file", f.name],
                    input=texte.encode('utf-8'),
                    capture_output=True, timeout=30
                )
                if result.returncode == 0:
                    with wave.open(f.name, 'rb') as wf:
                        frames = wf.readframes(wf.getnframes())
                        return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            finally:
                os.unlink(f.name)
        return self._synthetiser_fallback(texte)
    
    def _synthetiser_simulation(self, texte: str) -> np.ndarray:
        """Simule la synthèse."""
        return self._synthetiser_fallback(texte)
    
    def _synthetiser_fallback(self, texte: str) -> np.ndarray:
        """Fallback : génère un bip simple."""
        duree = 0.1  # 100ms de bip
        t = np.linspace(0, duree, int(SAMPLE_RATE * duree), endpoint=False)
        return np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.3
    
    def synthetiser_fichier(self, texte: str, filepath: str) -> bool:
        """Synthétise et sauvegarde dans un fichier WAV."""
        audio = self.synthetiser(texte)
        if audio is None:
            return False
        
        audio_int16 = (audio * 32767).astype(np.int16)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())
        return True


# =========================================================================
# CONTRÔLEUR AUDIO (Micro / Haut-parleur)
# =========================================================================

class AudioController:
    """Gestion de la capture et lecture audio."""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._sd_available = _check_dependency("sounddevice", "pip install sounddevice")
    
    def enregistrer(self, duree: float = RECORD_SECONDS,
                    detection_silence: bool = True) -> np.ndarray:
        """
        Enregistre depuis le micro.
        
        Args:
            duree: Durée max d'enregistrement en secondes
            detection_silence: Si True, arrête après détection de silence
        
        Returns:
            Audio numpy float32 [-1.0, 1.0]
        """
        if not self._sd_available:
            print("  [Audio] sounddevice non installé. Mode simulation.")
            return np.zeros(int(self.sample_rate * 1.0), dtype=np.float32)
        
        import sounddevice as sd
        
        print(f"\n  🎤 Écoute... (max {duree}s, parlez maintenant)")
        
        if detection_silence:
            return self._enregistrer_avec_silence(duree)
        else:
            audio = sd.rec(
                int(duree * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            print("  ✅ Enregistrement terminé")
            return audio.flatten()
    
    def _enregistrer_avec_silence(self, duree_max: float) -> np.ndarray:
        """Enregistre avec détection automatique de silence."""
        import sounddevice as sd
        
        chunks = []
        silencieux_depuis = 0
        chunk_duree = 0.5  # 500ms par chunk
        chunk_samples = int(chunk_duree * self.sample_rate)
        
        total_samples = 0
        max_samples = int(duree_max * self.sample_rate)
        
        while total_samples < max_samples:
            chunk = sd.rec(
                chunk_samples,
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            chunk = chunk.flatten()
            chunks.append(chunk)
            total_samples += chunk_samples
            
            energie = np.mean(np.abs(chunk))
            
            if energie < SILENCE_THRESHOLD:
                silencieux_depuis += 1
            else:
                silencieux_depuis = 0
            
            # Stop après X secondes de silence consécutif
            if silencieux_depuis * chunk_duree >= SILENCE_DURATION and len(chunks) > 5:
                # Garder les chunks avant le silence
                audio = np.concatenate(chunks[:-SILENCE_DURATION])
                print(f"  ✅ Silence détecté, arrêt après {len(audio)/self.sample_rate:.1f}s")
                return audio
        
        audio = np.concatenate(chunks)
        print(f"  ✅ Durée max atteinte : {len(audio)/self.sample_rate:.1f}s")
        return audio
    
    def jouer(self, audio: np.ndarray):
        """Joue de l'audio via le haut-parleur."""
        if not self._sd_available:
            print("  [Audio] sounddevice non installé. Mode simulation.")
            return
        
        import sounddevice as sd
        
        audio_clipped = np.clip(audio, -1.0, 1.0)
        sd.play(audio_clipped, self.sample_rate)
        sd.wait()
    
    def jouer_fichier(self, filepath: str):
        """Joue un fichier WAV."""
        with wave.open(filepath, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            self.jouer(audio)


# =========================================================================
# BRIDGE VOCAL COMPLET
# =========================================================================

class VoiceHarmoniqueBridge:
    """
    Bridge vocal complet : STT → Hologramme → LLM → TTS.
    
    Architecture :
      Micro → [WhisperSTT] → texte → [Hologramme] → contexte
                                                   ↓
      Haut-parleur ← [PiperTTS] ← audio ← [BridgeHarmoniqueGGUF] ← prompt enrichi
    """
    
    def __init__(self, mode: str = "harmonic",
                 model_size: str = WHISPER_MODEL,
                 voice: str = PIPER_VOICE):
        """
        Args:
            mode: Mode du bridge ("harmonic", "hybrid", "llm_only")
            model_size: Taille du modèle Whisper ("tiny", "base", "small")
            voice: Voix Piper
        """
        self.mode = mode
        
        print(f"\n{'='*70}")
        print(f"VOICE BRIDGE HARMONIQUE — Initialisation")
        print(f"{'='*70}")
        
        # Détection des capacités
        self.caps = detecter_capacites_audio()
        
        # --- STT ---
        print(f"\n[1/4] Initialisation STT (Whisper)...")
        self.stt = WhisperSTT(model_size=model_size)
        
        # --- TTS ---
        print(f"\n[2/4] Initialisation TTS (Piper)...")
        self.tts = PiperTTS(voice=voice)
        
        # --- Bridge Harmonique ---
        print(f"\n[3/4] Initialisation Bridge Harmonique...")
        try:
            self.bridge = BridgeHarmoniqueGGUF(mode=mode, n_lecteurs=8)
        except FileNotFoundError:
            # Mode harmonic sans LLM
            self.bridge = BridgeHarmoniqueGGUF(mode="harmonic", n_lecteurs=8)
            print("  ⚠️  LLM GGUF non trouvé, passage en mode harmonic")
        
        # --- Audio ---
        print(f"\n[4/4] Initialisation contrôleur audio...")
        self.audio = AudioController()
        
        # Statistiques
        self.stats = {
            "conversations": 0,
            "mots_transcrits": 0,
            "mots_synthetises": 0,
            "temps_total": 0.0,
        }
        
        print(f"\n{'='*70}")
        print(f"VOICE BRIDGE PRÊT")
        print(f"  Mode    : {mode}")
        print(f"  STT     : {self.caps.stt_method}")
        print(f"  TTS     : {self.caps.tts_method}")
        print(f"  Micro   : {'✅' if self.caps.microphone_available else '❌'}")
        print(f"  Speaker : {'✅' if self.caps.speakers_available else '❌'}")
        print(f"{'='*70}")
    
    def ecouter(self, duree: float = RECORD_SECONDS) -> str:
        """
        Étape 1 : Écoute le micro et transcrit en texte.
        
        Returns:
            Texte transcrit
        """
        audio = self.audio.enregistrer(duree=duree, detection_silence=True)
        texte = self.stt.transcrire(audio, SAMPLE_RATE)
        
        if texte.startswith("[") and texte.endswith("]"):
            print(f"  ← [Audio non transcrit : {texte}]")
        else:
            print(f"  ← Vous avez dit : \"{texte}\"")
        
        return texte
    
    def comprendre(self, texte: str) -> Dict:
        """
        Étape 2 : Apprentissage holographique + extraction du contexte.
        
        Returns:
            Résultat de génération
        """
        resultat = self.bridge.generer(
            prompt=texte,
            max_tokens=200,
            temperature=0.7,
            feedback=True
        )
        
        return resultat
    
    def parler(self, texte: str):
        """
        Étape 3 : Synthèse vocale et lecture.
        """
        print(f"  → Réponse : \"{texte[:100]}{'...' if len(texte) > 100 else ''}\"")
        
        audio = self.tts.synthetiser(texte)
        if audio is not None and len(audio) > 0:
            self.audio.jouer(audio)
        
        self.stats["mots_synthetises"] += len(texte.split())
    
    def conversation(self, tours: int = 0, duree_ecoute: float = RECORD_SECONDS):
        """
        Boucle de conversation vocale complète.
        
        Args:
            tours: Nombre de tours (0 = illimité)
            duree_ecoute: Durée d'écoute par tour
        """
        print(f"\n{'='*70}")
        print(f"CONVERSATION VOCALE DÉMARRÉE")
        print(f"  Mode : {self.mode}")
        print(f"  Tours : {'illimité' if tours == 0 else tours}")
        print(f"  Dites 'quitter' ou 'stop' pour terminer")
        print(f"  Dites 'stats' pour voir les statistiques")
        print(f"  Dites 'top' pour voir les tokens résonants")
        print(f"{'='*70}")
        
        tour = 0
        while tours == 0 or tour < tours:
            tour += 1
            print(f"\n--- Tour {tour} ---")
            
            # 1. Écouter
            t0 = time.time()
            texte = self.ecouter(duree=duree_ecoute)
            
            if not texte or texte.startswith("[silence]") or texte.startswith("[SIMULATION"):
                continue
            
            # Commandes spéciales
            texte_lower = texte.lower().strip()
            if texte_lower in ("quitter", "stop", "exit", "quit"):
                print("  👋 Fin de la conversation.")
                break
            if texte_lower == "stats":
                print(f"  📊 Stats : {json.dumps(self.stats, indent=2)}")
                print(f"  📊 Cache : {json.dumps(self.bridge.cache.stats(), indent=2)}")
                continue
            if texte_lower == "top":
                self.bridge.afficher_top_tokens()
                continue
            if texte_lower in ("diagnostic", "diag"):
                print(json.dumps(self.bridge.diagnostiquer(), indent=2, ensure_ascii=False, default=str))
                continue
            
            # 2. Comprendre (hologramme + LLM)
            resultat = self.comprendre(texte)
            
            # 3. Parler
            reponse = resultat.get("texte_genere", "Je n'ai pas compris.")
            self.parler(reponse)
            
            # Stats
            dt = time.time() - t0
            self.stats["conversations"] += 1
            self.stats["mots_transcrits"] += len(texte.split())
            self.stats["temps_total"] += dt
            
            print(f"  ⏱️  {dt:.1f}s | E={resultat.get('energie_hologramme', 0):.0f} | "
                  f"cache={'✓' if resultat.get('cache_hit') else '✗'}")
        
        print(f"\n  Conversations : {self.stats['conversations']}")
        print(f"  Mots transcrits : {self.stats['mots_transcrits']}")
        print(f"  Mots synthétisés : {self.stats['mots_synthetises']}")
        print(f"  Temps total : {self.stats['temps_total']:.0f}s")
    
    def transcrire_fichier(self, filepath: str) -> str:
        """Transcrit un fichier audio."""
        print(f"\n  Transcription de : {filepath}")
        texte = self.stt.transcrire_fichier(filepath)
        print(f"  Texte : \"{texte}\"")
        return texte
    
    def synthetiser_fichier(self, texte: str, filepath: str) -> bool:
        """Synthétise du texte et sauvegarde en WAV."""
        print(f"\n  Synthèse : \"{texte[:50]}...\" → {filepath}")
        ok = self.tts.synthetiser_fichier(texte, filepath)
        if ok:
            print(f"  ✅ Fichier sauvegardé : {filepath}")
        return ok
    
    def diagnostiquer(self) -> Dict:
        """Diagnostic complet du bridge vocal."""
        return {
            "audio": {
                "stt_method": self.caps.stt_method,
                "tts_method": self.caps.tts_method,
                "microphone": self.caps.microphone_available,
                "speakers": self.caps.speakers_available,
                "full_conversation": self.caps.can_full_conversation(),
            },
            "bridge": self.bridge.diagnostiquer(),
            "stats": self.stats,
        }


# =========================================================================
# MAIN
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Voice Bridge Harmonique — STT + Hologramme + TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Conversation vocale complète
  python voice_bridge_harmonic.py --mode full
  
  # Transcrire un fichier audio
  python voice_bridge_harmonic.py --mode stt --file enregistrement.wav
  
  # Synthétiser du texte en audio
  python voice_bridge_harmonic.py --mode tts --text "Bonjour, je suis Harmonic AI"
  
  # Mode simulation (test sans matériel audio)
  python voice_bridge_harmonic.py --mode simulate --prompt "Comment fonctionne la résonance ?"
  
  # Diagnostic complet
  python voice_bridge_harmonic.py --diagnostic
        """
    )
    
    parser.add_argument("--mode", type=str, default="full",
                       choices=["full", "stt", "tts", "simulate", "diagnostic"],
                       help="Mode de fonctionnement (defaut: full)")
    parser.add_argument("--bridge-mode", type=str, default="harmonic",
                       choices=["harmonic", "hybrid", "llm_only"],
                       help="Mode du bridge harmonique (defaut: harmonic)")
    parser.add_argument("--file", type=str, default="",
                       help="Fichier audio à transcrire (mode stt)")
    parser.add_argument("--text", type=str, default="",
                       help="Texte à synthétiser (mode tts)")
    parser.add_argument("--output", type=str, default="output.wav",
                       help="Fichier de sortie audio")
    parser.add_argument("--prompt", type=str, default="",
                       help="Prompt pour le mode simulation")
    parser.add_argument("--tours", type=int, default=0,
                       help="Nombre de tours de conversation (0=illimité)")
    parser.add_argument("--whisper-model", type=str, default=WHISPER_MODEL,
                       choices=["tiny", "base", "small", "medium"],
                       help="Taille du modèle Whisper (defaut: tiny)")
    parser.add_argument("--piper-voice", type=str, default=PIPER_VOICE,
                       help="Voix Piper (defaut: fr_FR-siwis-medium)")
    parser.add_argument("--diagnostic", action="store_true",
                       help="Afficher le diagnostic complet")
    
    args = parser.parse_args()
    
    # Initialisation
    bridge = VoiceHarmoniqueBridge(
        mode=args.bridge_mode,
        model_size=args.whisper_model,
        voice=args.piper_voice,
    )
    
    # Diagnostic
    if args.diagnostic or args.mode == "diagnostic":
        print(f"\n{'='*70}")
        print("DIAGNOSTIC COMPLET")
        print(f"{'='*70}")
        print(json.dumps(bridge.diagnostiquer(), indent=2, ensure_ascii=False, default=str))
        return
    
    # Mode STT seul
    if args.mode == "stt":
        if args.file:
            bridge.transcrire_fichier(args.file)
        else:
            texte = bridge.ecouter(duree=RECORD_SECONDS)
            if not texte.startswith("[") :
                print(f"\n  Transcription : {texte}")
        return
    
    # Mode TTS seul
    if args.mode == "tts":
        if args.text:
            bridge.synthetiser_fichier(args.text, args.output)
        else:
            texte = input("Texte à synthétiser : ")
            bridge.synthetiser_fichier(texte, args.output)
        return
    
    # Mode simulation
    if args.mode == "simulate":
        prompt = args.prompt or input("\n  Prompt : ")
        resultat = bridge.comprendre(prompt)
        
        print(f"\n  Contexte harmonique :")
        print(f"  {' '.join(resultat.get('contexte_harmonique', [])[:10])}")
        print(f"\n  Réponse :")
        print(f"  {'─'*60}")
        print(f"  {resultat['texte_genere']}")
        print(f"  {'─'*60}")
        print(f"\n  Stats : {resultat['n_tokens']} tokens | "
              f"{resultat['temps_ms']:.0f}ms | "
              f"E={resultat['energie_hologramme']:.0f}")
        return
    
    # Mode conversation complète
    if args.mode == "full":
        if bridge.caps.can_full_conversation():
            bridge.conversation(tours=args.tours)
        elif bridge.caps.can_record():
            print("\n  ⚠️  TTS non disponible. Mode STT + affichage texte.")
            bridge.conversation(tours=args.tours)
        else:
            print("\n  ⚠️  Audio non disponible. Passage en mode simulation.")
            print("  Tapez vos messages texte (ou 'quit' pour quitter) :")
            while True:
                try:
                    texte = input("\n  Vous > ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                
                if not texte:
                    continue
                if texte.lower() in ("quit", "exit", "q"):
                    break
                
                resultat = bridge.comprendre(texte)
                print(f"  IA   > {resultat['texte_genere']}")
                print(f"  [{resultat['n_tokens']}t | {resultat['temps_ms']:.0f}ms | "
                      f"E={resultat['energie_hologramme']:.0f}]")


if __name__ == "__main__":
    main()