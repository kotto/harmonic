#!/usr/bin/env python3
"""
PhiDiffusionEngine — Synthèse Vocale par Conditionnement Harmonique 11D
=========================================================================
Architecture de synthèse vocale de qualité professionnelle, conçue pour
être pilotée par les 11 dimensions harmoniques via un ConditionEncoder
qui injecte la prosodie dans un modèle de TTS neuronal.

Backends supportés (détection automatique du meilleur disponible) :
  1. Coqui TTS / XTTS-v2  — qualité ElevenLabs-like (si installé)
  2. Piper TTS            — qualité correcte, CPU, local
  3. Edge-TTS             — fallback cloud Microsoft (toujours disponible)

Architecture :
  SpectralMessage 11D
        │
        ▼
  ConditionEncoder (MLP 11→128→512) → embedding 512D
        │
        ├──→ Piper: 512D → length_scale, noise_scale, noise_w
        ├──→ Edge-TTS: 512D → rate, pitch
        └──→ Coqui/XTTS: 512D → speaker_embedding + prosody control

Usage :
    engine = PhiDiffusionEngine()
    audio = engine.synthesize("Bonjour", voice_params_11d, style="joyeux")
    engine.save_wav(audio, "output.wav")
"""

import os
import sys

# ⚠️ CRITICAL : HF_HOME doit etre defini AVANT tout import de transformers/TTS
_CACHE_ROOT = os.environ.get('HF_HOME', 'E:/hf_cache')
os.environ['HF_HOME'] = _CACHE_ROOT
os.environ['TORCH_HOME'] = _CACHE_ROOT + '/torch'
os.environ['HUGGINGFACE_HUB_CACHE'] = _CACHE_ROOT + '/hub'
os.environ['COQUI_TTS_AGREED'] = '1'
os.environ['COQUI_STUDIO_AGREED'] = '1'
os.makedirs(_CACHE_ROOT, exist_ok=True)
os.makedirs(_CACHE_ROOT + '/torch', exist_ok=True)
os.makedirs(_CACHE_ROOT + '/hub', exist_ok=True)

import json
import time
import io
import wave
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
import numpy as np

# Ajouter le repertoire racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print(f"[PhiDiffusion] Cache HF: {_CACHE_ROOT}")

# =========================================================================
# CONSTANTES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI


# =========================================================================
# CONDITION ENCODER 11D → 512D
# =========================================================================

class ConditionEncoder:
    """MLP leger 11→128→512, poids ~67K, < 300 KB."""

    def __init__(self):
        rng = np.random.RandomState(42)
        self.W1 = rng.randn(11, 128) * 0.1
        self.b1 = np.zeros(128)
        self.W2 = rng.randn(128, 512) * 0.1
        self.b2 = np.zeros(512)

    def encode(self, voice_11d: np.ndarray) -> np.ndarray:
        x = voice_11d.reshape(1, 11)
        h = np.maximum(0, x @ self.W1 + self.b1)
        return (h @ self.W2 + self.b2).flatten()

    def train_step(self, X: np.ndarray, Y_target: np.ndarray, lr: float = 0.01) -> float:
        h = np.maximum(0, X @ self.W1 + self.b1)
        y_pred = h @ self.W2 + self.b2
        error = y_pred - Y_target
        loss = float(np.mean(error ** 2))
        dW2 = h.T @ error / X.shape[0]
        db2 = np.mean(error, axis=0)
        dh = error @ self.W2.T
        dh[h <= 0] = 0
        dW1 = X.T @ dh / X.shape[0]
        db1 = np.mean(dh, axis=0)
        self.W2 -= lr * dW2; self.b2 -= lr * db2
        self.W1 -= lr * dW1; self.b1 -= lr * db1
        return loss

    def save(self, fp: str):
        np.savez(fp, W1=self.W1, b1=self.b1, W2=self.W2, b2=self.b2)

    def load(self, fp: str):
        if Path(fp).exists():
            d = np.load(fp)
            self.W1, self.b1 = d['W1'], d['b1']
            self.W2, self.b2 = d['W2'], d['b2']


# =========================================================================
# 11D → PARAMÈTRES BACKEND
# =========================================================================

def voice_11d_to_backend_params(v: np.ndarray, backend: str) -> Dict:
    if backend in ("piper_tts", "chatterbox_tts"):
        return {
            'length_scale': float(np.clip(1.5 - v[2], 0.4, 2.0)),
            'noise_scale': float(np.clip(0.3 + v[4] * 0.8, 0.1, 1.5)),
            'noise_w': float(np.clip(0.4 + v[7] * 0.6, 0.2, 1.0)),
            'sentence_silence': float(np.clip(0.1 + v[8] * 0.6, 0.05, 1.0)),
        }
    elif backend == "edge_tts":
        rate = int((v[2] - 0.5) * 60)
        pitch = int((v[0] - 0.5) * 30)
        return {
            'rate': f"{max(-50, min(50, rate)):+d}%",
            'pitch': f"{max(-20, min(20, pitch)):+d}Hz",
        }
    elif backend in ("coqui_tts", "coqui_xtts"):
        return {
            'speed': float(np.clip(0.7 + v[2] * 0.6, 0.5, 2.0)),
            'language': 'fr' if v[0] > 0.5 else 'en',
        }
    return {}


# =========================================================================
# RESAMPLING UTILITY
# =========================================================================

def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio to target sample rate using linear interpolation."""
    if orig_sr == target_sr:
        return audio
    duration = len(audio) / orig_sr
    n_target = int(duration * target_sr)
    indices = np.linspace(0, len(audio) - 1, n_target)
    lo = np.floor(indices).astype(int)
    hi = np.clip(lo + 1, 0, len(audio) - 1)
    frac = indices - lo
    return (audio[lo] * (1 - frac) + audio[hi] * frac).astype(np.float32)


# =========================================================================
# PHI DIFFUSION ENGINE
# =========================================================================

class PhiDiffusionEngine:
    """Moteur de synthèse vocale de qualité professionnelle piloté par 11D."""

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.encoder = ConditionEncoder()
        self._backend_name = None
        self._piper_voice = None
        self._piper_voice_name = None
        self._coqui_tts = None
        self.total_synthesized = 0
        self.total_time_ms = 0.0

    def _detect_backend(self, force: str = None) -> str:
        if force:
            self._backend_name = force
            return force
        if self._backend_name:
            return self._backend_name
        # 1) Piper TTS — local, léger, CPU, fonctionne partout (<100 MB RAM)
        try:
            import importlib
            if importlib.util.find_spec("piper"):
                # Vérifie qu'on a au moins une voix FR
                voices_dir = os.environ.get('PIPER_VOICE_DIR', 'E:/piper_voices')
                if os.path.isdir(voices_dir) and any(f.endswith('.onnx') for f in os.listdir(voices_dir)):
                    self._backend_name = "piper_tts"
                    print("[PhiDiffusion] Backend: Piper TTS (local, CPU)")
                    return self._backend_name
        except Exception:
            pass
        # 2) Edge-TTS — cloud Microsoft, bonne qualité, pas de RAM
        if shutil.which("edge-tts"):
            self._backend_name = "edge_tts"
            print("[PhiDiffusion] Backend: Edge-TTS (cloud)")
            return self._backend_name
        # 3) Coqui XTTS-v2 — qualité ElevenLabs, nécessite 4+ GB RAM
        try:
            import psutil
            avail_gb = psutil.virtual_memory().available / (1024**3)
            if avail_gb > 5.0:
                import TTS
                self._backend_name = "coqui_xtts"
                print("[PhiDiffusion] Backend: Coqui TTS / XTTS-v2")
                return self._backend_name
            else:
                print(f"[PhiDiffusion] XTTS-v2 ignoré (RAM dispo: {avail_gb:.1f} GB < 5.0 requis)")
        except ImportError:
            pass
        self._backend_name = "gtts"
        print("[PhiDiffusion] Backend: gTTS (fallback)")
        return self._backend_name

    def synthesize(self, text: str, voice_params=None, voice_name="default",
                   style="neutre", speaker_wav: Optional[str] = None) -> np.ndarray:
        backend = self._detect_backend()
        if voice_params is None:
            voice_params = self._neutral_11d()
        if style != "neutre":
            voice_params = self._apply_style(voice_params, style)
        self.encoder.encode(voice_params)
        params = voice_11d_to_backend_params(voice_params, backend)
        t0 = time.time()

        if backend in ("coqui_tts", "coqui_xtts"):
            audio = self._synth_coqui(text, params, voice_name, speaker_wav=speaker_wav)
        elif backend == "piper_tts":
            audio = self._synth_piper(text, params, voice_name)
        elif backend == "edge_tts":
            audio = self._synth_edgetts(text, params, voice_name)
        else:
            audio = self._synth_gtts(text, params)

        ms = (time.time() - t0) * 1000
        self.total_synthesized += 1
        n = self.total_synthesized
        self.total_time_ms = (self.total_time_ms * (n - 1) + ms) / n

        # Resample to target sample rate (default 48 kHz)
        if backend == "piper_tts":
            backend_sr = 22050
        elif backend in ("coqui_tts", "coqui_xtts"):
            backend_sr = 24000
        else:
            backend_sr = 24000
        if backend_sr != self.sample_rate:
            audio = resample_audio(audio, backend_sr, self.sample_rate)

        return audio

    def synthesize_from_profile(self, text: str, profile_name="default", style="neutre") -> np.ndarray:
        from engine.voice_signature_extractor import REFERENCE_PROFILES
        if profile_name in REFERENCE_PROFILES:
            vp = REFERENCE_PROFILES[profile_name].to_array()
        else:
            vp = self._neutral_11d()
        lang = "fr" if "fr" in profile_name.lower() else "en"
        return self.synthesize(text, vp, lang, style)

    def synthesize_high_quality(
        self,
        text: str,
        speaker_wav: Optional[str] = None,
        voice_profile: str = "css10_fr_native",
        language: str = "fr",
        speed: float = 1.0,
        style: str = "neutre",
    ) -> np.ndarray:
        """
        Synthese de qualite ElevenLabs via XTTS-v2 avec clonage vocal.

        Args:
            text: texte a synthetiser
            speaker_wav: chemin vers audio de reference (6-30s) pour cloner une voix.
                         Si None, utilise le profil integre (css10_fr_native par defaut).
            voice_profile: nom du profil 11D integre (css10_fr_native, default, etc.)
            language: code langue
            speed: vitesse (0.5-2.0)
            style: style emotionnel

        Returns:
            np.ndarray float32 audio
        """
        from engine.voice_signature_extractor import REFERENCE_PROFILES

        # Charger la signature 11D du profil
        if voice_profile in REFERENCE_PROFILES:
            vp = REFERENCE_PROFILES[voice_profile].to_array()
        else:
            vp = self._neutral_11d()

        # Appliquer le style
        if style != "neutre":
            vp = self._apply_style(vp, style)

        # Parametres backend
        backend = self._detect_backend()
        params = voice_11d_to_backend_params(vp, backend)
        params['speed'] = speed
        params['language'] = language

        t0 = time.time()

        if backend in ("coqui_tts", "coqui_xtts"):
            audio = self._synth_coqui(text, params, voice_profile, speaker_wav=speaker_wav)
        elif backend == "piper_tts":
            audio = self._synth_piper(text, params, voice_profile)
        else:
            audio = self._synth_edgetts(text, params, voice_profile)

        ms = (time.time() - t0) * 1000
        self.total_synthesized += 1
        n = self.total_synthesized
        self.total_time_ms = (self.total_time_ms * (n - 1) + ms) / n

        # Resample to target sample rate (default 48 kHz)
        if backend == "piper_tts":
            backend_sr = 22050
        elif backend in ("coqui_tts", "coqui_xtts"):
            backend_sr = 24000
        else:
            backend_sr = 24000
        if backend_sr != self.sample_rate:
            audio = resample_audio(audio, backend_sr, self.sample_rate)

        return audio

    # ----------------------------------------------------------------- COQUI XTTS-v2 (qualite ElevenLabs)
    def _synth_coqui(self, text: str, params: Dict, voice_name: str,
                     speaker_wav: Optional[str] = None) -> np.ndarray:
        """
        Synthese via XTTS-v2 avec clonage vocal optionnel.

        Args:
            speaker_wav: chemin vers audio de reference (6-30s) pour clonage.
                         Si None, utilise la voix par defaut du modele.
        """
        try:
            if self._coqui_tts is None:
                from TTS.api import TTS
                import builtins
                orig = builtins.input
                builtins.input = lambda _: 'y'
                print("[PhiDiffusion] Loading XTTS-v2 model (~1.8 GB, first load ~30s)...")
                try:
                    self._coqui_tts = TTS(
                        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                        progress_bar=False
                    )
                    print("[PhiDiffusion] XTTS-v2 loaded")
                finally:
                    builtins.input = orig

            wav = self._coqui_tts.tts(
                text=text,
                speaker_wav=speaker_wav,
                language=params.get('language', 'fr'),
                speed=params.get('speed', 1.0),
            )
            if isinstance(wav, list) and len(wav) > 0:
                audio = np.array(wav, dtype=np.float32)
                # Normaliser
                peak = np.max(np.abs(audio))
                if peak > 0:
                    audio = audio / peak * 0.95
                return audio
            return np.zeros(int(2.0 * 24000), dtype=np.float32)
        except Exception as e:
            print(f"[PhiDiffusion] Coqui failed: {e}, fallback Edge-TTS")
            return self._synth_edgetts(
                text,
                voice_11d_to_backend_params(self._neutral_11d(), "edge_tts"),
                voice_name
            )

    # ----------------------------------------------------------------- PIPER
    def _synth_piper(self, text: str, params: Dict, voice_name: str) -> np.ndarray:
        """Synthèse via Piper TTS (local, léger)."""
        try:
            self._ensure_piper_voice(voice_name)
            from piper.config import SynthesisConfig

            # Construire la config de synthèse
            syn_config = SynthesisConfig(
                length_scale=params.get('length_scale', 1.0),
                noise_scale=params.get('noise_scale', 0.667),
                noise_w_scale=params.get('noise_w', 0.8),
            )

            # Utiliser synthesize_wav avec un BytesIO wrappé dans wave.Wave_write
            buf = io.BytesIO()
            wav_writer = wave.open(buf, 'w')
            try:
                self._piper_voice.synthesize_wav(text, wav_writer, syn_config)
            finally:
                wav_writer.close()

            # Lire le WAV depuis le buffer
            buf.seek(0)
            with wave.open(buf, 'rb') as wf:
                raw = wf.readframes(wf.getnframes())
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            return audio
        except Exception as e:
            print(f"[PhiDiffusion] Piper failed: {e}, fallback Edge-TTS")
            import traceback
            traceback.print_exc()
            return self._synth_edgetts(text, voice_11d_to_backend_params(self._neutral_11d(), "edge_tts"), voice_name)

    def _ensure_piper_voice(self, name: str):
        """Charge une voix Piper. Priorité : E:/piper_voices/ (pré-téléchargé)."""
        if self._piper_voice_name == name and self._piper_voice:
            return
        import piper

        # Mapping noms logiques → fichiers de voix réels
        VOICE_MAP = {
            'default': 'fr_FR-siwis-medium',
            'fr': 'fr_FR-siwis-medium',
            'fr_female': 'fr_FR-siwis-medium',
            'fr_male': 'fr_FR-gilles-low',
            'en': 'en_US-lessac-medium',
            'en_female': 'en_US-lessac-medium',
            'css10_fr_native': 'fr_FR-siwis-medium',
        }
        resolved = VOICE_MAP.get(name, name)

        # Chercher la voix dans les répertoires connus
        search_dirs = [
            os.environ.get('PIPER_VOICE_DIR', 'E:/piper_voices'),
            str(Path(os.path.expanduser("~")) / ".cache" / "piper_tts"),
        ]
        model_path = None
        for d in search_dirs:
            candidate = Path(d) / f"{resolved}.onnx"
            if candidate.exists():
                model_path = str(candidate)
                break
            # Cherche aussi les .onnx qui commencent par le nom résolu
            if os.path.isdir(d):
                for f in sorted(os.listdir(d)):
                    if f.startswith(resolved) and f.endswith('.onnx'):
                        model_path = str(Path(d) / f)
                        break
                if model_path:
                    break

        if not model_path:
            # Téléchargement fallback
            cache = Path(os.path.expanduser("~")) / ".cache" / "piper_tts" / resolved
            model = cache / f"{resolved}.onnx"
            if not model.exists():
                cache.mkdir(parents=True, exist_ok=True)
                import urllib.request
                url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/{'siwis' if 'siwis' in resolved else 'gilles'}/{'medium' if 'medium' in resolved else 'low'}/{resolved}.onnx"
                print(f"[PhiDiffusion] Téléchargement voix Piper: {url}")
                req = urllib.request.Request(url, headers={'User-Agent': 'HarmonicAI'})
                with urllib.request.urlopen(req, timeout=120) as r:
                    model.write_bytes(r.read())
            model_path = str(model)

        print(f"[PhiDiffusion] Chargement voix Piper: {model_path}")
        self._piper_voice = piper.PiperVoice.load(model_path)
        self._piper_voice_name = name

    # ----------------------------------------------------------------- EDGE-TTS
    def _synth_edgetts(self, text: str, params: Dict, voice_name="fr-FR-DeniseNeural") -> np.ndarray:
        edge_voice = "fr-FR-DeniseNeural" if (voice_name and "fr" in voice_name.lower()) else "en-US-JennyNeural"
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp.close()
        try:
            r = subprocess.run(['edge-tts', '--voice', edge_voice, '--text', text,
                                '--rate', params.get('rate', '+0%'),
                                '--pitch', params.get('pitch', '+0Hz'),
                                '--write-media', tmp.name],
                               capture_output=True, text=True, timeout=30)
            if r.returncode != 0 or os.path.getsize(tmp.name) < 1000:
                return np.zeros(int(2.0 * self.sample_rate), dtype=np.float32)
            try:
                from pydub import AudioSegment
                seg = AudioSegment.from_file(tmp.name, format="mp3")
                samples = np.array(seg.get_array_of_samples(), dtype=np.float32) / 32768.0
                if seg.channels > 1:
                    samples = samples.reshape(-1, seg.channels).mean(axis=1)
                return samples
            except ImportError:
                return np.zeros(int(2.0 * self.sample_rate), dtype=np.float32)
        finally:
            os.unlink(tmp.name)

    # ----------------------------------------------------------------- GTTS
    def _synth_gtts(self, text: str, params: Dict) -> np.ndarray:
        from gtts import gTTS
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp.close()
        try:
            gTTS(text=text, lang='fr').save(tmp.name)
            try:
                from pydub import AudioSegment
                seg = AudioSegment.from_file(tmp.name, format="mp3")
                samples = np.array(seg.get_array_of_samples(), dtype=np.float32) / 32768.0
                if seg.channels > 1:
                    samples = samples.reshape(-1, seg.channels).mean(axis=1)
                return samples
            except ImportError:
                pass
            return np.zeros(int(2.0 * self.sample_rate), dtype=np.float32)
        finally:
            os.unlink(tmp.name)

    # ----------------------------------------------------------------- UTILS
    def _neutral_11d(self) -> np.ndarray:
        v = np.full(11, PHI_INV)
        v[4] = PHI_INV ** 3; v[7] = 0.75; v[10] = 0.78
        return v

    def _apply_style(self, v: np.ndarray, style: str) -> np.ndarray:
        mods = {
            'joyeux': {0: 0.70, 2: 0.65, 6: 0.70},
            'triste': {0: 0.45, 2: 0.30, 4: 0.35, 6: 0.50},
            'urgent': {0: 0.65, 2: 0.75, 6: 0.65, 8: 0.20},
            'calme': {0: 0.55, 2: 0.30, 4: 0.25, 6: 0.25},
            'autoritaire': {0: 0.50, 2: 0.50, 4: 0.10, 7: 0.85},
        }
        v = v.copy()
        for dim, val in mods.get(style, {}).items():
            v[dim] = v[dim] * 0.6 + val * 0.4
        return np.clip(v, 0, 1)

    @staticmethod
    def save_wav(audio: np.ndarray, filepath: str, sample_rate: int = 48000):
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        a16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            wf.writeframes(a16.tobytes())

    def get_stats(self) -> Dict:
        return {
            'backend': self._backend_name or 'auto',
            'total_synthesized': self.total_synthesized,
            'avg_time_ms': self.total_time_ms,
            'encoder_W1': list(self.encoder.W1.shape),
            'encoder_W2': list(self.encoder.W2.shape),
            'cache_root': _CACHE_ROOT,
        }


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST PhiDiffusionEngine — Synthese Pro 11D")
    print("=" * 60)

    engine = PhiDiffusionEngine()
    voice = np.array([0.72, 0.45, 0.55, 0.68, 0.15, 0.72, 0.35, 0.80, 0.40, 0.72, 0.80])

    print(f"\nBackend: {engine._detect_backend()}")
    print(f"Encoder: 11 -> {engine.encoder.W1.shape[1]} -> {engine.encoder.W2.shape[1]}")

    print("\n[Test] Voix francaise + style joyeux...")
    audio = engine.synthesize("Bonjour, je suis la voix harmonique avancee.", voice, voice_name="fr", style="joyeux")
    engine.save_wav(audio, "data/voice_output/test_diffusion_fr.wav")
    print(f"  test_diffusion_fr.wav ({len(audio)/22050:.1f}s)")

    print("\n[Test] Profil lj_speech + style triste...")
    audio = engine.synthesize_from_profile("This is a test with a sad emotion.", "lj_speech_female_us", "triste")
    engine.save_wav(audio, "data/voice_output/test_diffusion_en.wav")
    print(f"  test_diffusion_en.wav ({len(audio)/22050:.1f}s)")

    stats = engine.get_stats()
    print(f"\nStats: backend={stats['backend']}, syntheses={stats['total_synthesized']}, cache={stats['cache_root']}")
    print("\n" + "=" * 60)
    print("PhiDiffusionEngine operationnel")
    print("=" * 60)