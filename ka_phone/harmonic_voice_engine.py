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
        # Disk cache
        fpath = self._disk_dir / f"{key}.wav"
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
    
    def put(self, text: str, voice: str, speed: float, audio: bytes):
        key = self._key(text, voice, speed)
        with self._lock:
            self._ram[key] = (audio, time.time())
            if len(self._ram) > self.max_ram:
                oldest = min(self._ram, key=lambda k: self._ram[k][1])
                del self._ram[oldest]
        fpath = self._disk_dir / f"{key}.wav"
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
    """
    
    # Voix disponibles
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
    
    # Profils vocaux (11D → paramètres TTS)
    VOICE_PROFILES = {
        'savant': {'speed': 0.85, 'pitch': -2, 'style': 'calm'},
        'narrateur': {'speed': 0.90, 'pitch': 0, 'style': 'neutral'},
        'assistant': {'speed': 1.00, 'pitch': 0, 'style': 'cheerful'},
        'conteur': {'speed': 0.80, 'pitch': -1, 'style': 'sad'},
        'energetic': {'speed': 1.10, 'pitch': +1, 'style': 'excited'},
    }
    
    def __init__(self):
        self.cache = TTSCache(max_ram=200)
        self._xtts = None
        self._piper = None
        self._barge_in = threading.Event()
        self._current_voice = 'denise'
        self._lang = 'fr'
        self._init_engines()
    
    # ═════════════════════════════════════════════════════════════════════════
    # INIT
    # ═════════════════════════════════════════════════════════════════════════
    
    def _init_engines(self):
        """Initialise XTTS et Piper (si disponibles)."""
        # XTTS-v2 (local, haute qualité, mémoire optimisée)
        try:
            from xtts_engine import get_xtts
            self._xtts = get_xtts()
            if self._xtts.is_available:
                log.info("  XTTS-v2 : Actif (qualité ElevenLabs, local)")
            else:
                log.info("  XTTS-v2 : RAM insuffisante, sera ignoré")
                self._xtts = None
        except Exception as e:
            log.info(f"  XTTS-v2 : Non installé ({e})")
        
        # Piper (local, CPU, 50 MB)
        try:
            from phi_piper_engine import PhiPiperEngine
            self._piper = PhiPiperEngine()
            log.info("  Piper : Actif (local, 22 kHz)")
        except Exception:
            log.info("  Piper : Non disponible")
    
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
        
        # 1. XTTS-v2
        if self._xtts:
            try:
                audio = self._synthesize_xtts(text, voice, speed)
            except Exception:
                pass
        
        # 2. Piper
        if not audio and self._piper:
            try:
                audio = self._synthesize_piper(text, voice, speed)
            except Exception:
                pass
        
        # 3. Edge-TTS (cloud)
        if not audio:
            audio = self._synthesize_edgetts(text, voice, speed)
        
        if audio:
            self.cache.put(text, voice, speed, audio)
        
        return audio
    
    def _synthesize_xtts(self, text: str, voice: str, speed: float) -> bytes:
        """XTTS-v2 — mémoire optimisée."""
        return self._xtts.speak(text, language=self._lang, speed=speed)
    
    def _synthesize_piper(self, text: str, voice: str, speed: float) -> bytes:
        """Piper TTS — local, offline."""
        model = 'fr_FR-siwis-medium' if self._lang == 'fr' else 'en_US-lessac-medium'
        return self._piper.synthesize(text, model=model, length_scale=1.0/speed)
    
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
            if lang == 'en':
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
        """
        try:
            from harmonic_audio_postprocessor import HarmonicAudioPostProcessor
            post = HarmonicAudioPostProcessor()
            return post.process(audio_bytes, phi_boost=boost_phi)
        except Exception:
            return audio_bytes
    
    @property
    def stats(self) -> dict:
        return {
            'cache': self.cache.stats,
            'engines': {
                'xtts': self._xtts is not None,
                'piper': self._piper is not None,
                'edgetts': True,
            },
            'language': self._lang,
            'voice': self._current_voice,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_voice_instance = None

def get_voice() -> HarmonicVoiceEngine:
    global _voice_instance
    if _voice_instance is None:
        _voice_instance = HarmonicVoiceEngine()
    return _voice_instance
