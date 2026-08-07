#!/usr/bin/env python3
"""
VAD SERVICE — Voice Activity Detection + Barge-in pour KA Phone
================================================================
Détection de parole en temps réel sur CPU avec silero-vad.
Permet le déclenchement automatique de l'enregistrement
et l'interruption (barge-in) quand l'utilisateur parle.

Usage :
    from vad_service import VADService
    vad = VADService()
    is_speech = vad.detect(audio_chunk)  # True/False
    vad.start_listening()                # Réinitialise l'état
"""

import os
import time
import json
import wave
import threading
import struct
from collections import deque
from typing import Optional, Tuple
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data", "speech", "vad")
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# SILERO-VAD — Chargement lazy
# ══════════════════════════════════════════════════════════════════════════

# torch : détection SANS import (~2 s) — import différé au chargement de silero
try:
    import importlib.util as _ilu
    HAS_TORCH = _ilu.find_spec("torch") is not None
except Exception:
    HAS_TORCH = False
torch = None  # importé paresseusement dans _ensure_silero

HAS_SILERO = False
_silero_model = None
_silero_utils = None


def _ensure_silero():
    """Charge silero-vad lazily (1.5 Mo)."""
    global HAS_SILERO, _silero_model, _silero_utils, torch
    if HAS_SILERO:
        return True
    if not HAS_TORCH:
        print("[VAD] PyTorch non installé → fallback energy-based VAD")
        return False
    try:
        import torch  # import paresseux (~2 s) — seulement si VAD neuronal demandé
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        _silero_model = model
        _silero_utils = utils
        HAS_SILERO = True
        print("[VAD] silero-vad chargé (1.5 Mo, CPU)")
        return True
    except Exception as e:
        print(f"[VAD] Erreur chargement silero-vad: {e} → fallback energy-based")
        return False


# ══════════════════════════════════════════════════════════════════════════
# VAD SERVICE
# ══════════════════════════════════════════════════════════════════════════

class VADService:
    """
    Détecteur d'activité vocale avec support barge-in.

    Deux modes :
      1. Silero-VAD (si PyTorch dispo) — réseau neuronal léger, précis
      2. Energy-based (fallback) — seuil d'énergie RMS, zero dépendance
    """

    def __init__(self, sample_rate: int = 16000, frame_duration_ms: int = 30):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)  # 480 échantillons @30ms
        self.frame_duration_ms = frame_duration_ms

        # État
        self.is_speaking = False
        self.speech_start_time: Optional[float] = None
        self.speech_end_time: Optional[float] = None
        self.silence_duration = 0.0
        self.speech_duration = 0.0

        # Buffers
        self.energy_history = deque(maxlen=50)
        self.speech_prob_history = deque(maxlen=20)

        # Paramètres energy-based (fallback)
        self.energy_threshold = 0.02       # Seuil RMS pour détecter parole
        self.silence_timeout = 0.8         # Secondes de silence avant fin de parole
        self.speech_confirm_frames = 3     # Frames consécutives pour confirmer début parole
        self._speech_frame_count = 0
        self._silence_frame_count = 0

        # Compteurs
        self.consecutive_speech = 0
        self.consecutive_silence = 0

        # Barge-in
        self.barge_in_requested = False
        self.tts_is_playing = False

        # Historique des détections (pour debug)
        self.detection_log = deque(maxlen=100)

        # Charger silero si dispo
        self._has_silero = _ensure_silero()

        # Stats
        self.stats = {
            "total_frames": 0,
            "speech_frames": 0,
            "silence_frames": 0,
            "barge_in_events": 0,
            "engine": "silero-vad" if self._has_silero else "energy-based",
        }

    # ═══ DÉTECTION PRINCIPALE ═══

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        Détecte si un chunk audio contient de la parole.

        Args:
            audio_chunk: np.ndarray float32 [-1, 1], mono

        Returns:
            True si parole détectée, False sinon
        """
        self.stats["total_frames"] += 1

        if self._has_silero:
            is_speech = self._detect_silero(audio_chunk)
        else:
            is_speech = self._detect_energy(audio_chunk)

        # Mise à jour de l'état
        self._update_state(is_speech)

        # Log
        self.detection_log.append({
            "time": time.time(),
            "speech": is_speech,
            "speaking": self.is_speaking,
        })

        # Vérifier barge-in
        if is_speech and self.tts_is_playing:
            self.barge_in_requested = True
            self.stats["barge_in_events"] += 1

        return is_speech

    def _detect_silero(self, audio_chunk: np.ndarray) -> bool:
        """Détection via silero-vad."""
        try:
            # Convertir en tensor
            tensor = torch.from_numpy(audio_chunk.copy()).float()

            # Silero attend 512 ou 1024 échantillons pour 16000 Hz
            if len(tensor) < 512:
                # Pad si trop court
                padded = torch.zeros(512)
                padded[:len(tensor)] = tensor
                tensor = padded

            # Découper en chunks de 512 si plus long
            if len(tensor) > 512:
                speech_probs = []
                for i in range(0, len(tensor) - 256, 256):
                    chunk = tensor[i:i+512]
                    if len(chunk) < 512:
                        break
                    prob = _silero_model(chunk.unsqueeze(0), self.sample_rate).item()
                    speech_probs.append(prob)
                speech_prob = np.mean(speech_probs) if speech_probs else 0.0
            else:
                speech_prob = _silero_model(tensor.unsqueeze(0), self.sample_rate).item()

            self.speech_prob_history.append(speech_prob)
            return speech_prob > 0.5

        except Exception as e:
            # Fallback silencieux vers energy-based
            return self._detect_energy(audio_chunk)

    def _detect_energy(self, audio_chunk: np.ndarray) -> bool:
        """Détection par seuil d'énergie RMS (fallback)."""
        if len(audio_chunk) == 0:
            return False
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        self.energy_history.append(rms)

        # Calcul dynamique du seuil
        if len(self.energy_history) >= 10:
            avg_noise = np.mean(list(self.energy_history)[:10])
            threshold = max(self.energy_threshold, avg_noise * 2.5)
        else:
            threshold = self.energy_threshold

        return rms > threshold

    def _update_state(self, is_speech: bool):
        """Met à jour l'état de parole (début/fin de segment)."""
        if is_speech:
            self.stats["speech_frames"] += 1
            self.consecutive_speech += 1
            self.consecutive_silence = 0
            self.silence_duration = 0.0

            if not self.is_speaking and self.consecutive_speech >= self.speech_confirm_frames:
                # Début de parole
                self.is_speaking = True
                self.speech_start_time = time.time()
                self._speech_frame_count = 0

            if self.is_speaking:
                self._speech_frame_count += 1
                self.speech_duration = self._speech_frame_count * self.frame_duration_ms / 1000.0

        else:
            self.stats["silence_frames"] += 1
            self.consecutive_silence += 1
            self.consecutive_speech = 0

            if self.is_speaking:
                self.silence_duration += self.frame_duration_ms / 1000.0
                if self.silence_duration >= self.silence_timeout:
                    # Fin de parole
                    self.is_speaking = False
                    self.speech_end_time = time.time()

    # ═══ BARGE-IN ═══

    def start_tts_playback(self):
        """Signale que le TTS commence à jouer."""
        self.tts_is_playing = True
        self.barge_in_requested = False

    def stop_tts_playback(self):
        """Signale que le TTS a fini de jouer."""
        self.tts_is_playing = False
        self.barge_in_requested = False

    def check_barge_in(self) -> bool:
        """Vérifie si l'utilisateur a interrompu le TTS."""
        if self.barge_in_requested:
            self.barge_in_requested = False
            self.tts_is_playing = False
            return True
        return False

    # ═══ UTILITAIRES ═══

    def reset(self):
        """Réinitialise l'état du VAD."""
        self.is_speaking = False
        self.speech_start_time = None
        self.speech_end_time = None
        self.silence_duration = 0.0
        self.speech_duration = 0.0
        self.consecutive_speech = 0
        self.consecutive_silence = 0
        self._speech_frame_count = 0
        self._silence_frame_count = 0
        self.barge_in_requested = False
        self.tts_is_playing = False
        self.energy_history.clear()
        self.speech_prob_history.clear()
        self.detection_log.clear()

    def get_state(self) -> dict:
        """Retourne l'état complet du VAD."""
        return {
            "is_speaking": self.is_speaking,
            "speech_duration_s": round(self.speech_duration, 2),
            "silence_duration_s": round(self.silence_duration, 2),
            "tts_playing": self.tts_is_playing,
            "barge_in_pending": self.barge_in_requested,
            "engine": self.stats["engine"],
            "consecutive_speech": self.consecutive_speech,
            "consecutive_silence": self.consecutive_silence,
        }

    def get_stats(self) -> dict:
        return {
            **self.stats,
            "barge_in_events": self.stats["barge_in_events"],
            "current_state": self.get_state(),
        }

    @staticmethod
    def is_available() -> bool:
        """Vérifie si un VAD est disponible (silero ou fallback)."""
        return True  # Energy-based est toujours disponible

    @staticmethod
    def has_silero() -> bool:
        return HAS_SILERO


# ══════════════════════════════════════════════════════════════════════════
# AUDIO RECORDER AVEC VAD
# ══════════════════════════════════════════════════════════════════════════

class VADAudioRecorder:
    """
    Enregistreur audio qui démarre/stoppe automatiquement via VAD.
    Capture micro → détection parole → enregistrement automatique.
    """

    def __init__(self, sample_rate: int = 16000, chunk_duration_ms: int = 30):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.chunk_duration_ms = chunk_duration_ms

        self.vad = VADService(sample_rate, chunk_duration_ms)
        self.is_recording = False
        self.recording_buffer: list = []
        self.full_recording: Optional[np.ndarray] = None

        # Paramètres
        self.max_recording_s = 15.0   # Max secondes d'enregistrement
        self.min_recording_s = 0.5    # Min secondes pour considérer valide
        self.pre_speech_buffer_s = 0.3  # Garder 300ms avant détection parole

        # Thread d'enregistrement
        self._stop_flag = threading.Event()
        self._record_thread: Optional[threading.Thread] = None

        # Sounddevice (import lazy)
        self._sd = None

    def _ensure_sd(self):
        if self._sd is None:
            try:
                import sounddevice as sd
                self._sd = sd
                # Lister les périphériques
                devices = sd.query_devices()
                input_devices = [d for d in devices if d['max_input_channels'] > 0]
                if input_devices:
                    print(f"[Recorder] Périphériques d'entrée: {len(input_devices)}")
                    for d in input_devices[:3]:
                        print(f"  - {d['name']} ({d['max_input_channels']}ch, {int(d['default_samplerate'])}Hz)")
                else:
                    print("[Recorder] ⚠ Aucun périphérique d'entrée détecté!")
            except ImportError:
                print("[Recorder] sounddevice non installé — pip install sounddevice")
                raise

    def start_monitoring(self) -> bool:
        """Démarre la surveillance VAD en arrière-plan."""
        try:
            self._ensure_sd()
        except Exception:
            return False

        self._stop_flag.clear()
        self._record_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._record_thread.start()
        return True

    def stop_monitoring(self):
        """Arrête la surveillance."""
        self._stop_flag.set()
        if self._record_thread:
            self._record_thread.join(timeout=2.0)

    def _monitor_loop(self):
        """Boucle de surveillance continue (tourne dans un thread)."""
        pre_buffer = deque(maxlen=int(self.pre_speech_buffer_s * 1000 / self.chunk_duration_ms))

        def callback(indata, frames, time_info, status):
            mono = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
            pre_buffer.append(mono)

            is_speech = self.vad.detect(mono)

            if is_speech and not self.is_recording:
                # Début d'enregistrement — inclure le pre-buffer
                self.recording_buffer = list(pre_buffer)
                self.is_recording = True
            elif self.is_recording:
                # Continuer l'enregistrement
                self.recording_buffer.append(mono)
                if not self.vad.is_speaking:
                    # L'utilisateur a fini de parler
                    self._finalize_recording()
                elif len(self.recording_buffer) * self.chunk_duration_ms / 1000.0 >= self.max_recording_s:
                    # Durée max atteinte
                    self._finalize_recording()

        try:
            with self._sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=callback,
                blocksize=self.chunk_size,
            ):
                self._stop_flag.wait()
        except Exception as e:
            print(f"[Recorder] Erreur stream audio: {e}")

    def _finalize_recording(self):
        """Finalise l'enregistrement en cours."""
        duration_s = len(self.recording_buffer) * self.chunk_duration_ms / 1000.0
        if duration_s >= self.min_recording_s and self.recording_buffer:
            self.full_recording = np.concatenate(self.recording_buffer)
            self.vad.reset()
            self.is_recording = False
        else:
            # Trop court, on ignore
            self.recording_buffer = []
            self.full_recording = None
            self.is_recording = False

    def get_recording(self) -> Optional[Tuple[np.ndarray, int]]:
        """
        Récupère le dernier enregistrement complet.

        Returns:
            (audio_np, sample_rate) ou None si pas d'enregistrement
        """
        if self.full_recording is not None:
            rec = self.full_recording.copy()
            self.full_recording = None
            return rec, self.sample_rate
        return None

    def save_wav(self, audio: np.ndarray, path: str) -> bool:
        """Sauvegarde un array numpy en fichier WAV."""
        try:
            audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
            with wave.open(path, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            return True
        except Exception as e:
            print(f"[Recorder] Erreur sauvegarde WAV: {e}")
            return False


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("VAD SERVICE — Test")
    print("=" * 60)
    print(f"  Silero-VAD: {VADService.has_silero()}")
    print(f"  Energy-VAD: {VADService.is_available()}")

    # Test simple avec audio synthétique
    vad = VADService()
    print(f"  Engine: {vad.stats['engine']}")

    # Simuler quelques chunks
    sr = 16000
    t_silence = np.linspace(0, 0.1, int(0.1 * sr), endpoint=False)
    t_speech = np.linspace(0, 0.1, int(0.1 * sr), endpoint=False)

    silence = np.random.randn(len(t_silence)) * 0.005  # Bruit faible
    speech = np.sin(2 * np.pi * 440 * t_speech) * 0.3  # Son fort

    test_audio = np.concatenate([
        silence,
        silence,
        speech,
        speech,
        speech,
        silence,
        silence,
    ])

    # Découper en chunks de 30ms
    chunk_size = int(0.03 * sr)  # 480 samples
    print(f"\n  Test sur {len(test_audio)/sr:.1f}s d'audio synthétique:")
    for i in range(0, len(test_audio) - chunk_size, chunk_size):
        chunk = test_audio[i:i + chunk_size]
        is_speech = vad.detect(chunk)
        bar = "█" if is_speech else "░"
        if i % (chunk_size * 10) == 0:  # Print every 300ms
            print(f"    {i/sr:4.1f}s {bar}  speaking={vad.is_speaking}")

    print(f"\n  Stats: {json.dumps(vad.get_stats(), indent=2)}")
    print("  ✅ VAD fonctionnel")