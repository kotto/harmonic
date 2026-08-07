#!/usr/bin/env python3
"""
TTS STREAMING SERVICE — Streaming + Cache + Barge-in pour KA Phone
====================================================================
Optimise la latence perçue en :
  1. Découpant le texte en phrases courtes
  2. Générant l'audio phrase par phrase (streaming)
  3. Permettant l'interruption (barge-in) entre chaque phrase
  4. Cachant les phrases fréquentes déjà synthétisées

Usage :
    from tts_streaming import TTSStreamingService
    tts = TTSStreamingService()
    
    # Streaming avec barge-in
    for audio_chunk, is_last in tts.speak_stream("Bonjour, je suis KA.", voice="denise"):
        if tts.check_barge_in():
            break  # L'utilisateur a interrompu
        play(audio_chunk)
    
    # Génération standard avec cache
    audio = tts.speak_cached("Bonjour")
"""

import os
import sys
import json
import time
import wave
import io
import hashlib
import threading
import tempfile
import asyncio
from typing import Optional, List, Tuple, Generator, Dict
from collections import OrderedDict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data", "speech", "tts_cache")
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# TTS CACHE
# ══════════════════════════════════════════════════════════════════════════

class TTSCache:
    """
    Cache LRU pour les phrases TTS fréquentes.
    Évite de re-synthétiser les salutations, erreurs, etc.
    """

    def __init__(self, max_size: int = 100, cache_dir: str = DATA_DIR):
        self.max_size = max_size
        self.cache_dir = cache_dir
        self.cache: OrderedDict[str, Dict] = OrderedDict()
        self._load_disk_cache()

    def _key(self, text: str, voice: str, speed: float) -> str:
        return hashlib.md5(f"{text}|{voice}|{speed}".encode()).hexdigest()[:12]

    def get(self, text: str, voice: str = "default", speed: float = 1.0) -> Optional[bytes]:
        """Récupère l'audio du cache."""
        res = self.get_ex(text, voice, speed)
        return res[0] if res else None

    def get_ex(self, text: str, voice: str = "default", speed: float = 1.0) -> Optional[Tuple[bytes, str]]:
        """Récupère (audio, format) du cache — format ∈ {'wav', 'mp3'}."""
        key = self._key(text, voice, speed)
        # Check RAM cache
        if key in self.cache:
            self.cache.move_to_end(key)
            entry = self.cache[key]
            return entry["audio"], entry.get("fmt", "wav")
        # Check disk cache (extension selon le format réel)
        for fmt in ("wav", "mp3"):
            disk_path = os.path.join(self.cache_dir, f"{key}.{fmt}")
            if os.path.exists(disk_path):
                with open(disk_path, "rb") as f:
                    audio = f.read()
                self.cache[key] = {"audio": audio, "text": text[:60], "fmt": fmt}
                if len(self.cache) > self.max_size:
                    self.cache.popitem(last=False)
                return audio, fmt
        return None

    def put(self, text: str, audio: bytes, voice: str = "default", speed: float = 1.0, fmt: str = "wav"):
        """Stocke l'audio dans le cache (RAM + disque) avec son format réel."""
        key = self._key(text, voice, speed)
        # RAM cache
        self.cache[key] = {"audio": audio, "text": text[:60], "fmt": fmt}
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
        # Disk cache — l'extension reflète le contenu (MP3 Edge-TTS ≠ WAV Piper)
        disk_path = os.path.join(self.cache_dir, f"{key}.{fmt}")
        try:
            with open(disk_path, "wb") as f:
                f.write(audio)
        except Exception:
            pass

    def preload_common_phrases(self, synthesizer_fn):
        """
        Pré-génère les phrases les plus fréquentes.
        synthesizer_fn: fonction (text) -> bytes
        """
        common_phrases = [
            "Bonjour, je suis KA, ton double numérique. Que puis-je faire pour toi ?",
            "Je ne comprends pas. Peux-tu répéter ?",
            "Je n'ai pas trouvé de réponse dans ma base. Essaie de reformuler.",
            "D'accord.",
            "Merci.",
            "Au revoir.",
            "Oui.",
            "Non.",
            "Je suis là.",
            "Pause.",
        ]
        for phrase in common_phrases:
            if self.get(phrase) is None:
                try:
                    audio = synthesizer_fn(phrase)
                    if audio:
                        self.put(phrase, audio)
                        print(f"  [TTS Cache] Pré-généré: '{phrase[:40]}...' ({len(audio)} bytes)")
                except Exception as e:
                    print(f"  [TTS Cache] Erreur pré-génération '{phrase[:30]}': {e}")

    def _load_disk_cache(self):
        """Recense le cache disque au démarrage SANS tout charger en RAM.

        Avant : chaque instanciation lisait tous les .wav du disque en mémoire
        (orchestrateur → 1 instance par speak() → rechargement complet à chaque
        phrase). Désormais le disque n'est lu qu'à la demande (dans get_ex).
        """
        if not os.path.exists(self.cache_dir):
            return
        count = sum(1 for f in os.listdir(self.cache_dir)
                    if f.endswith(".wav") or f.endswith(".mp3"))
        if count > 0:
            print(f"  [TTS Cache] {count} fichiers disponibles sur disque (chargement paresseux)")

    def stats(self) -> dict:
        return {
            "ram_entries": len(self.cache),
            "max_size": self.max_size,
            "disk_cache_dir": self.cache_dir,
            "disk_files": len([f for f in os.listdir(self.cache_dir) if f.endswith(".wav") or f.endswith(".mp3")]) if os.path.exists(self.cache_dir) else 0,
        }


# ══════════════════════════════════════════════════════════════════════════
# TTS STREAMING SERVICE
# ══════════════════════════════════════════════════════════════════════════

class TTSStreamingService:
    """
    Service TTS avec streaming, cache et barge-in.

    Stratégie :
      1. Edge-TTS (qualité quasi-humaine, gratuit) → streaming
      2. Piper TTS (local, CPU) → fallback
      3. Tout est caché
    """

    def __init__(self, speech_service=None):
        self.speech_service = speech_service
        self.cache = TTSCache()
        self.barge_in_flag = threading.Event()
        self.is_playing = False

        # Délai entre phrases (pour respiration naturelle)
        self.inter_phrase_delay = 0.15

        # VAD service (pour barge-in externe)
        self.vad_service = None

    def set_vad(self, vad_service):
        """Lie un VAD pour le barge-in automatique."""
        self.vad_service = vad_service

    # ═══ BARGE-IN ═══

    def request_barge_in(self):
        """Demande l'interruption du TTS en cours."""
        self.barge_in_flag.set()
        if self.vad_service:
            self.vad_service.barge_in_requested = True

    def check_barge_in(self) -> bool:
        """Vérifie si une interruption a été demandée."""
        # Check flag interne
        if self.barge_in_flag.is_set():
            self.barge_in_flag.clear()
            self.is_playing = False
            return True
        # Check VAD externe
        if self.vad_service and self.vad_service.check_barge_in():
            self.barge_in_flag.clear()
            self.is_playing = False
            return True
        return False

    def start_playback(self):
        """Signale le début de la lecture."""
        self.barge_in_flag.clear()
        self.is_playing = True
        if self.vad_service:
            self.vad_service.start_tts_playback()

    def stop_playback(self):
        """Signale la fin de la lecture."""
        self.is_playing = False
        if self.vad_service:
            self.vad_service.stop_tts_playback()

    # ═══ SYNTHÈSE AVEC CACHE ═══

    def speak_cached(self, text: str, voice: str = "denise", speed: float = 1.0) -> Optional[bytes]:
        """
        Synthétise avec cache. Retourne l'audio complet en une fois.

        Args:
            text: Texte à synthétiser
            voice: "denise", "henri", "eloise", "vivienne", "jerome" (Edge) ou "piper" (local)
            speed: Facteur de vitesse (1.0 = normal)

        Returns:
            bytes WAV/MP3 ou None si erreur
        """
        res = self.speak_cached_ex(text, voice, speed)
        return res[0] if res else None

    def speak_cached_ex(self, text: str, voice: str = "denise", speed: float = 1.0) -> Optional[Tuple[bytes, str]]:
        """Comme speak_cached mais retourne (audio, format) — 'mp3' (Edge) ou 'wav' (Piper)."""
        # Check cache
        cached = self.cache.get_ex(text, voice, speed)
        if cached:
            return cached

        # Synthétiser
        res = self._synthesize_ex(text, voice, speed)
        if res:
            audio, fmt = res
            self.cache.put(text, audio, voice, speed, fmt=fmt)
            return audio, fmt
        return None

    def speak_stream(self, text: str, voice: str = "denise", speed: float = 1.0) -> Generator[Tuple[bytes, bool], None, None]:
        """
        Synthétise en streaming, phrase par phrase.
        Permet le barge-in entre chaque phrase.

        Yields:
            (audio_bytes, is_last_phrase) pour chaque phrase
            Si barge-in, stop immédiatement après la phrase en cours
        """
        for audio, _fmt, is_last in self.speak_stream_ex(text, voice, speed):
            yield audio, is_last

    def speak_stream_ex(self, text: str, voice: str = "denise", speed: float = 1.0) -> Generator[Tuple[bytes, str, bool], None, None]:
        """
        Comme speak_stream mais yield (audio_bytes, format, is_last_phrase).
        Le format est constant pour tout le stream ('mp3' Edge ou 'wav' Piper).
        """
        self.start_playback()

        # Découper en phrases
        sentences = self._split_sentences(text)
        total = len(sentences)

        for i, sentence in enumerate(sentences):
            if self.check_barge_in():
                break

            is_last = (i == total - 1)

            # Synthétiser la phrase
            res = self.speak_cached_ex(sentence, voice, speed)
            if res:
                audio, fmt = res
                yield audio, fmt, is_last

        self.stop_playback()

    def speak_all_at_once(self, text: str, voice: str = "denise", speed: float = 1.0) -> Optional[bytes]:
        """
        Synthétise tout le texte d'un coup (non-streaming).
        Pour les réponses courtes ou quand le barge-in n'est pas nécessaire.
        """
        return self.speak_cached(text, voice, speed)

    # ═══ DÉCOUPAGE ═══

    def _split_sentences(self, text: str) -> List[str]:
        """
        Découpe le texte en phrases pour streaming.
        Gère la ponctuation française.
        """
        import re

        # Nettoyer
        text = text.strip()
        if not text:
            return []

        # Patterns de fin de phrase
        # On split sur . ! ? ... mais on garde les séparateurs
        parts = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ű\d"«\'\(])', text)

        # Si le split n'a rien donné (une seule phrase)
        if len(parts) <= 1:
            # Split sur , ; : pour les phrases longues
            if len(text) > 150:
                parts = re.split(r'(?<=[,;:])\s+(?=[a-zà-ű])', text)
            else:
                return [text]

        # Nettoyer les parties vides
        result = [p.strip() for p in parts if p.strip()]

        # Si une phrase est trop longue (>200 chars), la couper sur les virgules
        final = []
        for phrase in result:
            if len(phrase) > 200:
                sub = re.split(r'(?<=,)\s+', phrase)
                final.extend([s.strip() for s in sub if s.strip()])
            else:
                final.append(phrase)

        return final if final else [text]

    # ═══ BACKEND TTS ═══

    def _synthesize(self, text: str, voice: str, speed: float) -> Optional[bytes]:
        """Synthétise via le meilleur backend disponible (Edge-TTS → Piper)."""
        res = self._synthesize_ex(text, voice, speed)
        return res[0] if res else None

    def _synthesize_ex(self, text: str, voice: str, speed: float) -> Optional[Tuple[bytes, str]]:
        """
        Synthétise le texte via le meilleur backend disponible.
        Priorité : Edge-TTS → Piper → None
        Retourne (audio_bytes, format) — 'mp3' pour Edge-TTS, 'wav' pour Piper.
        """
        if not self.speech_service:
            # Initialiser speech_service paresseusement
            try:
                from speech_service import SpeechService
                self.speech_service = SpeechService()
            except ImportError:
                return None

        svc = self.speech_service

        # 1. Edge-TTS
        if svc.is_edge_tts_available():
            edge_voice = self._map_voice_to_edge(voice)
            result = svc.synthesize_bytes_edge(text, voice=edge_voice, speed=speed)
            if result:
                return result, "mp3"

        # 2. Piper (local)
        result = svc.synthesize_bytes(text, speed=speed)
        if result:
            return result, "wav"

        return None

    def _map_voice_to_edge(self, name: str) -> str:
        """Mappe un nom court à une voix Edge-TTS complète.

        Les noms complets ('fr-FR-HenriNeural', envoyés par l'orchestrateur
        via les profils de voix) sont passés tels quels.
        """
        if not name:
            return "fr-FR-DeniseNeural"
        if "neural" in name.lower():  # déjà un nom complet Edge-TTS
            return name
        mapping = {
            "denise": "fr-FR-DeniseNeural",
            "henri": "fr-FR-HenriNeural",
            "eloise": "fr-FR-EloiseNeural",
            "vivienne": "fr-FR-VivienneNeural",
            "jerome": "fr-FR-JeromeNeural",
        }
        return mapping.get(name.lower(), "fr-FR-DeniseNeural")

    # ═══ PRÉ-CHARGEMENT ═══

    def preload_common(self):
        """Pré-génère les phrases fréquentes."""
        def synth_fn(text):
            return self._synthesize(text, "denise", 1.0)
        self.cache.preload_common_phrases(synth_fn)

    def get_cache_stats(self) -> dict:
        return self.cache.stats()


# ══════════════════════════════════════════════════════════════════════════
# UTILITAIRES AUDIO
# ══════════════════════════════════════════════════════════════════════════

def combine_audio_chunks(chunks: List[bytes]) -> Optional[bytes]:
    """
    Combine plusieurs chunks audio WAV en un seul.
    Suppose que tous les chunks ont le même format (sample rate, channels, etc.).
    """
    if not chunks:
        return None
    if len(chunks) == 1:
        return chunks[0]

    try:
        # Lire le premier chunk pour obtenir le format
        with wave.open(io.BytesIO(chunks[0]), 'rb') as wf0:
            params = wf0.getparams()

        # Assembler tous les chunks
        output = io.BytesIO()
        with wave.open(output, 'wb') as wf_out:
            wf_out.setparams(params)
            for chunk in chunks:
                with wave.open(io.BytesIO(chunk), 'rb') as wf_in:
                    wf_out.writeframes(wf_in.readframes(wf_in.getnframes()))

        return output.getvalue()
    except Exception:
        # Si WAV parsing échoue, concaténer les bytes bruts (MP3 probablement)
        return b''.join(chunks)


# ══════════════════════════════════════════════════════════════════════════
# PRELOADER (à appeler au démarrage du serveur)
# ══════════════════════════════════════════════════════════════════════════

def preload_tts_cache():
    """Fonction utilitaire pour précharger le cache TTS au démarrage."""
    try:
        tts = TTSStreamingService()
        # Note: preload_common() déclenche Edge-TTS → nécessite connexion internet
        # Ne pas appeler ici pour éviter latence au démarrage
        # tts.preload_common()
        print(f"  [TTS Streaming] Pré-chargement terminé. Cache: {tts.get_cache_stats()}")
        return tts
    except Exception as e:
        print(f"  [TTS Streaming] Erreur pré-chargement: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("TTS STREAMING SERVICE — Test")
    print("=" * 60)

    # Test découpage
    tts = TTSStreamingService()
    test_text = "Bonjour, je suis KA, ton double numérique. Que puis-je faire pour toi ? Je peux répondre à tes questions, écrire des poèmes, ou t'aider avec tes calculs."
    sentences = tts._split_sentences(test_text)
    print(f"\n  Découpage en {len(sentences)} phrases:")
    for i, s in enumerate(sentences):
        print(f"    [{i}] {s}")

    # Test cache
    from collections import OrderedDict
    print(f"\n  Cache stats: {json.dumps(tts.get_cache_stats(), indent=2)}")

    # Test barge-in simulé
    print("\n  Test barge-in simulé:")
    print("    - Début playback → is_playing=True")
    tts.start_playback()
    print(f"      is_playing: {tts.is_playing}")

    print("    - Simulation interruption utilisateur...")
    tts.request_barge_in()
    interrupted = tts.check_barge_in()
    print(f"      barge-in détecté: {interrupted}")
    print(f"      is_playing: {tts.is_playing}")

    print("\n  ✅ TTS Streaming Service fonctionnel")