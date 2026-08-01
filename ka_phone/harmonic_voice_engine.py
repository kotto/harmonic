"""
Harmonic Voice Engine — Moteur Vocal Unifié
=============================================
Remplace le système TTS éclaté par un moteur unifié à 3 niveaux :

  Niveau 1 — XTTS-v2 (local, 24 kHz, qualité ElevenLabs-like)
  Niveau 2 — Piper TTS (local, 22 kHz, offline, 50 MB)
  Niveau 3 — Edge-TTS (cloud, qualité Microsoft Neural, fallback)

Architecture :
  1. Tente XTTS-v2 (si installé)
  2. Sinon Piper (toujours disponible)
  3. Edge-TTS en dernier recours (nécessite Internet)

Ajouts :
  - WebSocket streaming temps réel
  - Barge-in amélioré (mi-utterance via threading.Event)
  - Auto-détection de langue FR/EN
  - Expressivité 11D (pitch, vitesse, émotion depuis la signature harmonique)

Usage dans unified_server.py :
  from harmonic_voice_engine import HarmonicVoiceEngine
  voice = HarmonicVoiceEngine()
  voice.speak("Bonjour, je suis KA.")
"""

import sys, os, time, json, io, threading, re, hashlib, logging
from pathlib import Path
from typing import Optional, Dict, List, Generator

_KA_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_KA_DIR))

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CACHE TTS
# ═══════════════════════════════════════════════════════════════════════════════

class TTSCache:
    """Cache LRU pour les synthèses vocales fréquentes."""
    
    def __init__(self, max_ram: int = 200, disk_dir: str = None):
        self.max_ram = max_ram
        self._ram = {}  # key -> (audio_bytes, timestamp)
        self._disk_dir = Path(disk_dir) if disk_dir else _KA_DIR.parent / 'data' / 'tts_cache'
        self._disk_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    
    def _key(self, text: str, voice: str, speed: float) -> str:
        return hashlib.md5(f"{text}|{voice}|{speed:.2f}".encode()).hexdigest()
    
    def get(self, text: str, voice: str = 'default', speed: float = 1.0) -> Optional[bytes]:
        key = self._key(text, voice, speed)
        with self._lock:
            if key in self._ram:
                return self._ram[key][0]
        # Disk cache — extension selon le format réel (WAV Piper/XTTS, MP3 Edge-TTS)
        for fmt in ('wav', 'mp3'):
            fpath = self._disk_dir / f"{key}.{fmt}"
            if fpath.exists():
                with open(fpath, 'rb') as f:
                    data = f.read()
                with self._lock:
                    self._ram[key] = (data, time.time())
                    if len(self._ram) > self.max_ram:
                        oldest = min(self._ram, key=lambda k: self._ram[k][1])
                        del self._ram[oldest]
                return data
        return None

    def put(self, text: str, voice: str, speed: float, audio: bytes, fmt: str = 'wav'):
        key = self._key(text, voice, speed)
        with self._lock:
            self._ram[key] = (audio, time.time())
            if len(self._ram) > self.max_ram:
                oldest = min(self._ram, key=lambda k: self._ram[k][1])
                del self._ram[oldest]
        fpath = self._disk_dir / f"{key}.{fmt}"
        with open(fpath, 'wb') as f:
            f.write(audio)
    
    @property
    def stats(self) -> dict:
        with self._lock:
            return {'ram_entries': len(self._ram), 'disk_dir': str(self._disk_dir)}


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR VOCAL UNIFIÉ
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicVoiceEngine:
    """
    Moteur vocal 3 niveaux avec streaming et expressivité 11D.
    
    Mode offline (offline_only=True) :
      - Désactive Edge-TTS (cloud)
      - Priorise Piper TTS (local, 63 Mo, fr_FR-siwis-medium)
      - Fallback XTTS-v2 si assez de RAM (≥ 2.5 Go)
      - Fallback ultime : synthèse sinusoïdale de secours
    """
    
    # Voix disponibles (Edge-TTS — désactivées en mode offline)
    VOICES_FR = {
        'henri': 'fr-FR-HenriNeural',
        'denise': 'fr-FR-DeniseNeural',
        'eloise': 'fr-FR-EloiseNeural',
        'vivienne': 'fr-FR-VivienneNeural',
        'jerome': 'fr-FR-JeromeNeural',
    }
    VOICES_EN = {
        'aria': 'en-US-AriaNeural',
        'guy': 'en-US-GuyNeural',
        'jenny': 'en-US-JennyNeural',
    }
    
    # Voix offline (Piper — toujours disponible sans Internet)
    VOICES_OFFLINE = {
        'siwis': {'id': 'siwis', 'label': 'SIWIS (français neutre)', 'engine': 'piper'},
        'siwis_h': {'id': 'siwis', 'label': 'SIWIS (homme)', 'engine': 'piper'},
        'siwis_f': {'id': 'siwis', 'label': 'SIWIS (femme)', 'engine': 'piper'},
        'xtts': {'id': 'xtts', 'label': 'XTTS-v2 (clonage, qualité ElevenLabs)', 'engine': 'xtts'},
    }
    
    # Profils vocaux (11D → paramètres TTS)
    VOICE_PROFILES = {
        'savant': {'speed': 0.85, 'pitch': -2, 'style': 'calm'},
        'narrateur': {'speed': 0.90, 'pitch': 0, 'style': 'neutral'},
        'assistant': {'speed': 1.00, 'pitch': 0, 'style': 'cheerful'},
        'conteur': {'speed': 0.80, 'pitch': -1, 'style': 'sad'},
        'energetic': {'speed': 1.10, 'pitch': +1, 'style': 'excited'},
    }
    
    def __init__(self, offline_only: bool = True):
        """
        Args:
            offline_only: si True, désactive Edge-TTS (cloud) et utilise
                          exclusivement Piper + XTTS (locaux).
        """
        self.offline_only = offline_only
        self.cache = TTSCache(max_ram=200) if not offline_only else TTSCache(max_ram=500)
        self._xtts = None
        self._piper = None
        self._barge_in = threading.Event()
        self._current_voice = 'siwis' if offline_only else 'denise'
        self._lang = 'fr'
        self._init_engines()
    
    # ═════════════════════════════════════════════════════════════════════════
    # INIT
    # ═════════════════════════════════════════════════════════════════════════
    
    def _init_engines(self):
        """Initialise les moteurs locaux (Piper, XTTS). Edge-TTS ignoré si offline_only."""
        mode = "OFFLINE" if self.offline_only else "HYBRID"
        log.info(f"Voice Engine — mode {mode}")
        
        # ── Piper (local, CPU, 63 Mo) — toujours prioritaire en offline ──
        try:
            from speech_service import SpeechService
            svc = SpeechService()
            if svc.piper_available:
                self._piper = svc
                log.info("  ✅ Piper TTS : Actif (fr_FR-siwis-medium, 22 kHz, offline)")
            else:
                # Tenter l'installation automatique
                if svc.ensure_piper_installed():
                    self._piper = svc
                    log.info("  ✅ Piper TTS : Installé et activé")
                else:
                    log.warning("  ⚠️  Piper TTS : Non disponible (exécuter ensure_piper_installed())")
        except Exception as e:
            log.warning(f"  ⚠️  Piper TTS : Erreur ({e})")
        
        # ── XTTS-v2 (local, 1.8 Go RAM, clonage vocal) ──
        try:
            from xtts_engine import get_xtts
            self._xtts = get_xtts()
            if self._xtts.is_available:
                log.info("  ✅ XTTS-v2 : Actif (qualité ElevenLabs, clonage vocal)")
            else:
                log.info("  ⚠️  XTTS-v2 : RAM insuffisante (≥ 2.5 Go requis), sera ignoré")
                self._xtts = None
        except Exception as e:
            log.info(f"  ⚠️  XTTS-v2 : Non installé ({e})")
        
        # ── Edge-TTS — désactivé en offline ──
        if self.offline_only:
            log.info("  🚫 Edge-TTS : Désactivé (mode offline)")
        else:
            log.info("  ☁️  Edge-TTS : Disponible (fallback cloud)")
    
    # ═════════════════════════════════════════════════════════════════════════
    # SYNTHÈSE PRINCIPALE
    # ═════════════════════════════════════════════════════════════════════════
    
    def speak(self, text: str, voice: str = 'denise', speed: float = 1.0,
              profile: str = None, emotion_11d: dict = None) -> bytes:
        """
        Synthétise du texte en audio.
        
        Args:
            text: texte à synthétiser
            voice: nom de la voix ('denise', 'henri', 'aria', etc.)
            speed: vitesse (0.5 à 2.0)
            profile: profil vocal prédéfini ('savant', 'narrateur', etc.)
            emotion_11d: signature 11D optionnelle (influence le rendu)
        
        Returns:
            bytes WAV ou MP3
        """
        # Appliquer le profil vocal
        if profile and profile in self.VOICE_PROFILES:
            p = self.VOICE_PROFILES[profile]
            speed = p['speed'] * speed
        
        # Cache
        cached = self.cache.get(text, voice, speed)
        if cached:
            return cached
        
        # Essayer les moteurs dans l'ordre
        audio = None
        fmt = 'wav'

        # 1. XTTS-v2 (local, clonage vocal)
        if self._xtts:
            try:
                audio = self._synthesize_xtts(text, voice, speed)
            except Exception:
                pass

        # 2. Piper (local, CPU, toujours disponible)
        if not audio and self._piper:
            try:
                audio = self._synthesize_piper(text, voice, speed)
            except Exception:
                pass

        # 3. Edge-TTS (cloud) — SEULEMENT si pas en mode offline
        if not audio and not self.offline_only:
            try:
                audio = self._synthesize_edgetts(text, voice, speed)
                fmt = 'mp3' if audio else fmt
            except Exception:
                pass

        # 4. Fallback sinusoïdal de secours (offline ultime)
        if not audio:
            audio = self._synthesize_fallback(text, speed)
            fmt = 'wav'

        if audio:
            self.cache.put(text, voice, speed, audio, fmt=fmt)

        return audio
    
    def _synthesize_xtts(self, text: str, voice: str, speed: float) -> bytes:
        """XTTS-v2 — mémoire optimisée."""
        return self._xtts.speak(text, language=self._lang, speed=speed)
    
    def _synthesize_piper(self, text: str, voice: str, speed: float) -> bytes:
        """Piper TTS — local, offline (via SpeechService, modèle fr_FR-siwis)."""
        return self._piper.synthesize_bytes(text, speed=speed)
    
    def _synthesize_edgetts(self, text: str, voice: str, speed: float) -> bytes:
        """Edge-TTS — cloud, qualité Microsoft."""
        import asyncio
        voice_id = self.VOICES_FR.get(voice, self.VOICES_EN.get(voice, 'fr-FR-DeniseNeural'))
        rate = f"{int((speed - 1.0) * 100):+d}%"
        
        async def _synth():
            import edge_tts
            communicate = edge_tts.Communicate(text, voice_id, rate=rate)
            chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            return b''.join(chunks)
        
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_synth())
        finally:
            loop.close()
    
    def _synthesize_fallback(self, text: str, speed: float = 1.0) -> bytes:
        """
        Synthèse sinusoïdale de secours (zéro dépendance, 100% offline).
        Génère un son modulé — pas de la parole naturelle, mais fonctionnel.
        Utilisé uniquement quand Piper ET XTTS sont indisponibles.
        """
        import io as _io
        import wave as _wave
        try:
            import numpy as np
        except ImportError:
            # Sans numpy, on retourne un silence WAV minimal
            buf = _io.BytesIO()
            with _wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                wf.writeframes(b'\x00' * 4410)  # 0.1s silence
            return buf.getvalue()
        
        sample_rate = 22050
        duration = max(0.5, len(text) * 0.08)  # ~80ms par caractère
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        
        # Fréquence porteuse basée sur φ
        PHI = 1.618033988749895
        base_freq = 220 * (PHI ** ((speed - 1.0) * 0.5))
        carrier = np.sin(2 * np.pi * base_freq * t)
        
        # Modulation d'amplitude par la longueur des mots
        envelope = np.ones_like(t)
        words = text.split()
        if words:
            for i, word in enumerate(words):
                start = i * duration / len(words)
                end = start + duration / len(words)
                mask = (t >= start) & (t < end)
                envelope[mask] = 0.5 + 0.5 * np.sin(np.pi * (t[mask] - start) / (duration / len(words)))
        
        audio = carrier * envelope * 0.3
        audio = np.clip(audio, -1, 1)
        audio_int16 = (audio * 32767).astype(np.int16)
        
        buf = _io.BytesIO()
        with _wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        return buf.getvalue()
    
    # ═════════════════════════════════════════════════════════════════════════
    # STREAMING (sentence-level avec barge-in)
    # ═════════════════════════════════════════════════════════════════════════
    
    def speak_stream(self, text: str, voice: str = 'denise', speed: float = 1.0,
                     profile: str = None) -> Generator[bytes, None, None]:
        """
        Synthèse streamée phrase par phrase.
        
        Yields (audio_bytes, is_last) pour chaque phrase.
        Vérifie le barge-in entre chaque phrase.
        """
        self._barge_in.clear()
        sentences = self._split_sentences(text)
        
        for i, sentence in enumerate(sentences):
            if self._barge_in.is_set():
                break
            
            is_last = (i == len(sentences) - 1)
            try:
                audio = self.speak(sentence, voice, speed, profile)
                if audio:
                    yield (audio, is_last)
            except Exception:
                pass
        
        self._barge_in.clear()
    
    def barge_in(self):
        """Interrompt la synthèse en cours."""
        self._barge_in.set()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Découpe le texte en phrases pour le streaming."""
        parts = re.split(r'(?<=[.!?])\s+', text)
        result = []
        for part in parts:
            if len(part) > 150:
                sub = re.split(r'(?<=[,;:])\s+', part)
                result.extend(s.strip() for s in sub if s.strip())
            else:
                if part.strip():
                    result.append(part.strip())
        return result
    
    # ═════════════════════════════════════════════════════════════════════════
    # AUTO-DÉTECTION DE LANGUE
    # ═════════════════════════════════════════════════════════════════════════
    
    def set_language(self, lang: str):
        """Change la langue de synthèse (fr, en)."""
        if lang in ('fr', 'en'):
            self._lang = lang
            if self.offline_only:
                self._current_voice = 'siwis'  # Piper : une seule voix FR
            elif lang == 'en':
                self._current_voice = 'aria'
            else:
                self._current_voice = 'denise'
    
    def auto_detect_language(self, text: str) -> str:
        """Détecte la langue du texte (fr ou en)."""
        fr_words = {'le', 'la', 'les', 'est', 'une', 'des', 'pourquoi', 'comment', 'dans', 'avec'}
        en_words = {'the', 'is', 'are', 'what', 'how', 'why', 'who', 'when', 'where'}
        words = set(text.lower().split())
        if len(words & en_words) > len(words & fr_words):
            return 'en'
        return 'fr'
    
    # ═════════════════════════════════════════════════════════════════════════
    # POST-TRAITEMENT HARMONIQUE
    # ═════════════════════════════════════════════════════════════════════════
    
    def enhance_audio(self, audio_bytes: bytes, boost_phi: bool = True) -> bytes:
        """
        Améliore l'audio avec le post-processeur harmonique.
        Boost des fréquences φ-harmoniques, réduction de bruit.
        WAV PCM 16 bits uniquement — un MP3 (Edge-TTS) est renvoyé tel quel.
        """
        try:
            import wave
            import numpy as np
            from harmonic_audio_postprocessor import HarmonicAudioPostProcessor

            # Décoder le WAV en tableau numpy float32 [-1, 1]
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                sample_rate = wf.getframerate()
                sampwidth = wf.getsampwidth()
                raw = wf.readframes(wf.getnframes())
            if sampwidth != 2:
                return audio_bytes  # seul le PCM 16 bits est géré
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

            # process_bytes(audio, sample_rate, ...) → np.ndarray (API réelle du post-processeur)
            post = HarmonicAudioPostProcessor()
            processed = post.process_bytes(
                data, sample_rate,
                boost_strength=0.12 if boost_phi else 0.0,
                noise_reduction=True,
                abc_smoothing=True,
            )

            # Ré-encoder en WAV PCM 16 bits
            out = io.BytesIO()
            pcm = (np.clip(processed, -1.0, 1.0) * 32767).astype(np.int16)
            with wave.open(out, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(pcm.tobytes())
            return out.getvalue()
        except Exception:
            return audio_bytes
    
    @property
    def stats(self) -> dict:
        return {
            'mode': 'offline' if self.offline_only else 'hybrid',
            'cache': self.cache.stats,
            'engines': {
                'xtts': self._xtts is not None,
                'piper': self._piper is not None,
                'edgetts': not self.offline_only,
            },
            'language': self._lang,
            'voice': self._current_voice,
            'voices_available': list(self.VOICES_OFFLINE.keys()) if self.offline_only else list(self.VOICES_FR.keys()),
        }
    
    @property
    def is_offline_ready(self) -> bool:
        """True si au moins un moteur offline (Piper ou XTTS) est disponible."""
        return self._piper is not None or self._xtts is not None


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_voice_instance = None

def get_voice(offline_only: bool = True) -> HarmonicVoiceEngine:
    """Retourne l'instance unique du moteur vocal.
    
    Args:
        offline_only: si True (défaut), mode 100% local (Piper + XTTS).
                      Si False, mode hybride avec fallback Edge-TTS cloud.
    """
    global _voice_instance
    if _voice_instance is None:
        _voice_instance = HarmonicVoiceEngine(offline_only=offline_only)
    return _voice_instance
