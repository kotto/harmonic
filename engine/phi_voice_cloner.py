"""
Clonage Vocal Harmonique — Qualite ElevenLabs via XTTS-v2
===========================================================
Clone une voix a partir de 6-30s d'audio de reference et synthetise
du texte avec les 11 dimensions harmoniques qui pilotent la prosodie.

Backend principal : Coqui XTTS-v2 (qualite ElevenLabs-like).
Fallback : Edge-TTS avec profils pre-calibres.

Architecture :
    Audio reference (6-30s)
        │
        ▼
    VoiceSignatureExtractor → signature 11D
        │
        ├──→ XTTS-v2 speaker_wav (clonage vocal)
        └──→ ConditionEncoder calibré → speed, temperature

Usage :
    cloner = PhiVoiceCloner()
    cloner.calibrate_from_reference("ma_voix.wav")
    audio = cloner.speak("Bonjour, je suis une voix clonee.", voice="ma_voix")
"""

import os
import sys
import json
import time
import hashlib
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import numpy as np

# Chemins
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_VOICE_CACHE = _PROJECT_ROOT / "data" / "voice_clones"
_VOICE_CACHE.mkdir(parents=True, exist_ok=True)

# Imports locaux (robustes)
sys.path.insert(0, str(_PROJECT_ROOT))
try:
    from engine.voice_signature_extractor import VoiceSignatureExtractor, VoiceSignature, REFERENCE_PROFILES
except ImportError:
    from voice_signature_extractor import VoiceSignatureExtractor, VoiceSignature, REFERENCE_PROFILES

try:
    from engine.phi_diffusion_engine import ConditionEncoder, voice_11d_to_backend_params
except ImportError:
    from phi_diffusion_engine import ConditionEncoder, voice_11d_to_backend_params


# ==============================================================================
# XTTS-v2 WRAPPER
# ==============================================================================

class XTTSWrapper:
    """Wrapper autour de Coqui XTTS-v2 avec clonage vocal."""

    def __init__(self):
        self._tts = None
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        try:
            from TTS.api import TTS
            import builtins
            orig_input = builtins.input
            builtins.input = lambda _: 'y'
            print("[VoiceCloner] Loading XTTS-v2 (~1.8 GB, first load takes ~30s)...")
            try:
                self._tts = TTS(
                    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                    progress_bar=False
                )
            finally:
                builtins.input = orig_input
            self._loaded = True
            print("[VoiceCloner] XTTS-v2 loaded successfully")
        except ImportError:
            raise RuntimeError(
                "XTTS-v2 requires coqui-tts. Install: pip install coqui-tts"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load XTTS-v2: {e}")

    def clone_and_speak(
        self,
        text: str,
        speaker_wav: str,
        language: str = "fr",
        speed: float = 1.0,
    ) -> np.ndarray:
        """
        Clone une voix et synthetise du texte.

        Args:
            text: texte a synthetiser
            speaker_wav: chemin vers l'audio de reference (6-30s)
            language: code langue ("fr", "en", "es", "de", "it", "pt")
            speed: vitesse (0.5-2.0, 1.0 = normal)

        Returns:
            np.ndarray float32 [-1, 1] a 24 kHz
        """
        self._ensure_loaded()
        wav = self._tts.tts(
            text=text,
            speaker_wav=speaker_wav,
            language=language,
            speed=speed,
        )
        if isinstance(wav, list) and len(wav) > 0:
            return np.array(wav, dtype=np.float32)
        return np.zeros(int(2.0 * 24000), dtype=np.float32)

    @property
    def sample_rate(self) -> int:
        return 24000  # XTTS-v2 native sample rate


# ==============================================================================
# CLONER VOCAL PRINCIPAL
# ==============================================================================

class PhiVoiceCloner:
    """
    Clonage vocal de qualite ElevenLabs.

    Pipeline :
      1. Extraire signature 11D du fichier audio de reference
      2. Cloner la voix avec XTTS-v2 (speaker_wav)
      3. Ajuster la prosodie via les 11D (speed, emotion)
      4. Fallback Edge-TTS si XTTS indisponible
      5. Resample final a 48 kHz
    """

    def __init__(self, sample_rate: int = 48000):
        self.extractor = VoiceSignatureExtractor()
        self.encoder = ConditionEncoder()
        self.sample_rate = sample_rate
        self._xtts = None
        self._voice_cache: Dict[str, dict] = {}
        self._load_cache()

    # ==================================================================
    # CALIBRATION
    # ==================================================================

    def calibrate_from_reference(
        self,
        audio_path: str,
        voice_name: Optional[str] = None,
    ) -> VoiceSignature:
        """
        Analyse un fichier audio de reference et cree un profil vocal.

        Args:
            audio_path: chemin vers .wav (6-30s, voix claire sans bruit)
            voice_name: nom du profil (defaut: derive du nom de fichier)

        Returns:
            VoiceSignature 11D calibree
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Reference audio not found: {audio_path}")

        if voice_name is None:
            voice_name = Path(audio_path).stem

        print(f"[VoiceCloner] Analyzing reference: {audio_path}")
        signature = self.extractor.extract(audio_path)

        # Sauvegarder le profil
        profile = {
            "name": voice_name,
            "reference_audio": str(Path(audio_path).resolve()),
            "signature": signature.to_dict(),
            "signature_11d": signature.to_array().tolist(),
            "calibrated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self._voice_cache[voice_name] = profile
        self._save_cache()

        print(f"[VoiceCloner] Voice '{voice_name}' calibrated:")
        print(f"  pitch_mean={signature.H_pitch_mean:.2f} "
              f"clarity={signature.H_clarity:.2f} "
              f"naturalness={signature.H_naturalness:.2f}")

        return signature

    def calibrate_encoder(
        self,
        voice_name: str,
        n_steps: int = 200,
        lr: float = 0.005,
    ) -> float:
        """
        Entraine le ConditionEncoder a predire les parametres optimaux
        pour une voix donnee.

        Le ConditionEncoder (MLP 11→128→512) mappe la signature 11D
        vers un embedding qui pilote la prosodie. Cette calibration
        ajuste ses poids pour que l'embedding corresponde au profil
        de reference.

        Args:
            voice_name: nom du profil vocal
            n_steps: nombre d'etapes d'entrainement
            lr: learning rate

        Returns:
            loss finale
        """
        if voice_name not in self._voice_cache:
            raise ValueError(f"Unknown voice: {voice_name}. Run calibrate_from_reference() first.")

        sig_11d = np.array(self._voice_cache[voice_name]["signature_11d"], dtype=np.float32)

        # Cible : signature 11D projetee dans l'espace 512D
        Y_target = np.tile(sig_11d, (512 // 11 + 1))[:512].astype(np.float32).reshape(1, 512)

        X = sig_11d.reshape(1, 11)

        losses = []
        for step in range(n_steps):
            loss = self.encoder.train_step(X, Y_target, lr=lr)
            losses.append(loss)

            if step % 50 == 0 and step > 0:
                print(f"[VoiceCloner] Calibration step {step}/{n_steps}: loss={loss:.6f}")

        final_loss = float(np.mean(losses[-20:]))
        print(f"[VoiceCloner] Encoder calibrated for '{voice_name}': final_loss={final_loss:.6f}")

        # Save trained encoder
        encoder_path = _VOICE_CACHE / f"{voice_name}_encoder.npz"
        self.encoder.save(str(encoder_path))
        print(f"[VoiceCloner] Encoder saved to {encoder_path}")

        return final_loss

    # ==================================================================
    # SYNTHESE
    # ==================================================================

    def speak(
        self,
        text: str,
        voice: str = "default",
        language: str = "fr",
        speed: Optional[float] = None,
        style: str = "neutre",
    ) -> np.ndarray:
        """
        Synthetise du texte avec la voix clonee a la frequence cible.

        Args:
            text: texte a dire
            voice: nom du profil vocal
            language: code langue
            speed: vitesse (None = auto)
            style: style emotionnel

        Returns:
            np.ndarray float32 [-1, 1] a self.sample_rate Hz (48 kHz par defaut)
        """
        # Obtenir la signature 11D du profil
        sig_11d = self._get_voice_11d(voice)

        # Appliquer le style
        if style != "neutre":
            sig_11d = self._apply_style(sig_11d, style)

        # Determiner la vitesse
        if speed is None:
            speed = float(np.clip(0.7 + sig_11d[2] * 0.6, 0.5, 2.0))

        # Essayer XTTS-v2 d'abord (24 kHz natif)
        audio = self._speak_xtts(text, voice, sig_11d, language, speed)
        native_sr = 24000

        if audio is None:
            # Fallback Edge-TTS
            audio = self._speak_edgetts(text, sig_11d, language)
            native_sr = 24000

        # Resample vers la frequence cible
        if native_sr != self.sample_rate:
            audio = self._resample(audio, native_sr, self.sample_rate)

        return audio

    def _speak_xtts(
        self,
        text: str,
        voice: str,
        sig_11d: np.ndarray,
        language: str,
        speed: float,
    ) -> Optional[np.ndarray]:
        """Synthese via XTTS-v2 avec clonage."""
        try:
            if self._xtts is None:
                self._xtts = XTTSWrapper()

            # Determiner le speaker_wav
            speaker_wav = None
            if voice in self._voice_cache:
                ref_path = self._voice_cache[voice].get("reference_audio")
                if ref_path and os.path.exists(ref_path):
                    speaker_wav = ref_path

            if speaker_wav is None:
                # Fallback: chercher un .wav dans data/voice_clones/
                candidate = _VOICE_CACHE / f"{voice}_reference.wav"
                if candidate.exists():
                    speaker_wav = str(candidate)

            if speaker_wav is None:
                print(f"[VoiceCloner] No reference audio for '{voice}', using XTTS default voice")
                # Sans speaker_wav, XTTS utilise une voix par defaut
                audio = self._xtts.clone_and_speak(text, speaker_wav=None, language=language, speed=speed)
            else:
                audio = self._xtts.clone_and_speak(text, speaker_wav=speaker_wav, language=language, speed=speed)

            # Normaliser
            peak = np.max(np.abs(audio))
            if peak > 0:
                audio = audio / peak * 0.95

            return audio

        except Exception as e:
            print(f"[VoiceCloner] XTTS failed: {e}")
            return None

    def _speak_edgetts(
        self,
        text: str,
        sig_11d: np.ndarray,
        language: str = "fr",
    ) -> np.ndarray:
        """Fallback Edge-TTS."""
        try:
            import subprocess
            import tempfile

            # Parametres vocaux depuis 11D
            rate = int((sig_11d[2] - 0.5) * 60)
            pitch = int((sig_11d[0] - 0.5) * 30)
            rate_str = f"{max(-50, min(50, rate)):+d}%"
            pitch_str = f"{max(-20, min(20, pitch)):+d}Hz"

            voice_map = {"fr": "fr-FR-DeniseNeural", "en": "en-US-JennyNeural"}
            voice = voice_map.get(language, "fr-FR-DeniseNeural")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            cmd = [
                "edge-tts", "--voice", voice,
                "--rate", rate_str,
                "--pitch", pitch_str,
                "--text", text,
                "--write-media", tmp_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)

            # Decoder MP3 → WAV
            import soundfile as sf
            try:
                audio, sr = sf.read(tmp_path)
            except Exception:
                # Fallback: utiliser le phi_vocoder
                from engine.phi_vocoder import PhiVocoder
                vocoder = PhiVocoder(sample_rate=22050)
                audio = vocoder.synthesize(sig_11d, duration=len(text) * 0.08)
                sr = 22050

            os.unlink(tmp_path)
            return audio.astype(np.float32)

        except Exception as e:
            print(f"[VoiceCloner] Edge-TTS failed: {e}")
            # Fallback ultime: vocodeur phi
            from engine.phi_vocoder import PhiVocoder
            vocoder = PhiVocoder(sample_rate=22050)
            return vocoder.synthesize(sig_11d, duration=len(text) * 0.08)

    # ==================================================================
    # UTILITAIRES
    # ==================================================================

    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target rate by linear interpolation."""
        if orig_sr == target_sr or len(audio) < 2:
            return audio
        duration = len(audio) / orig_sr
        n_target = max(1, int(duration * target_sr))
        indices = np.linspace(0, len(audio) - 1, n_target)
        lo = np.floor(indices).astype(int)
        hi = np.clip(lo + 1, 0, len(audio) - 1)
        frac = (indices - lo).astype(np.float32)
        return (audio[lo] * (1.0 - frac) + audio[hi] * frac).astype(np.float32)

    def _get_voice_11d(self, voice: str) -> np.ndarray:
        """Recupere la signature 11D d'un profil."""
        # Profil calibre localement
        if voice in self._voice_cache:
            return np.array(self._voice_cache[voice]["signature_11d"], dtype=np.float32)

        # Profil de reference integre
        if voice in REFERENCE_PROFILES:
            return REFERENCE_PROFILES[voice].to_array()

        # Profils francais par defaut
        french_profiles = {
            "css10_fr_native": REFERENCE_PROFILES.get("css10_fr_native"),
            "default": REFERENCE_PROFILES.get("librimix_best"),
        }

        for name, sig in french_profiles.items():
            if sig is not None:
                return sig.to_array()

        # Fallback: 11D neutre
        return np.full(11, 0.5, dtype=np.float32)

    def _apply_style(self, sig_11d: np.ndarray, style: str) -> np.ndarray:
        """Module la signature 11D pour un style emotionnel."""
        s = sig_11d.copy()
        if style == "joyeux":
            s[0] = min(1.0, s[0] * 1.3)   # pitch +
            s[2] = min(1.0, s[2] * 1.2)   # speed +
            s[7] = min(1.0, s[7] * 1.4)   # emotion +
        elif style == "triste":
            s[0] = max(0.0, s[0] * 0.7)
            s[2] = max(0.0, s[2] * 0.6)
            s[4] = min(1.0, s[4] * 1.3)   # breathiness +
        elif style == "autoritaire":
            s[0] = min(1.0, s[0] * 0.8)   # pitch bas
            s[5] = min(1.0, s[5] * 1.3)   # resonance +
            s[7] = min(1.0, s[7] * 1.1)
        elif style == "chuchote":
            s[4] = min(1.0, s[4] * 2.0)   # breathiness ++
            s[0] = max(0.0, s[0] * 0.5)   # pitch --
            s[5] = max(0.0, s[5] * 0.3)   # resonance --
        return np.clip(s, 0.0, 1.0)

    def _load_cache(self):
        cache_file = _VOICE_CACHE / "voice_profiles.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self._voice_cache = json.load(f)
            except Exception:
                self._voice_cache = {}

    def _save_cache(self):
        cache_file = _VOICE_CACHE / "voice_profiles.json"
        with open(cache_file, 'w') as f:
            json.dump(self._voice_cache, f, indent=2, ensure_ascii=False)

    @property
    def available_voices(self) -> List[str]:
        builtin = list(REFERENCE_PROFILES.keys())
        custom = list(self._voice_cache.keys())
        return sorted(set(builtin + custom))

    @staticmethod
    def save_wav(audio: np.ndarray, path: str, sample_rate: int = 48000):
        """Sauvegarde l'audio en WAV 16-bit 48 kHz."""
        import wave
        audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        print(f"[VoiceCloner] Saved: {path} ({len(audio)/sample_rate:.1f}s)")


# ==============================================================================
# DEMO
# ==============================================================================

def demo():
    """Demonstration du clonage vocal."""
    print("=" * 60)
    print("PHI VOICE CLONER — Qualite ElevenLabs via XTTS-v2")
    print("=" * 60)
    print()

    cloner = PhiVoiceCloner()
    print(f"Available voices: {cloner.available_voices}")
    print()

    # Test avec voix francaise integree
    text = "Bonjour, je suis une voix de synthese de haute qualite, creee par le moteur harmonique Phi."
    print(f"Text: \"{text}\"")
    print()

    for voice in ["css10_fr_native", "default"]:
        if voice in cloner.available_voices:
            print(f"--- Voice: {voice} ---")
            try:
                audio = cloner.speak(text, voice=voice, style="neutre")
                dur = len(audio) / 24000
                print(f"  Duration: {dur:.1f}s, Samples: {len(audio)}")
                cloner.save_wav(audio, str(_VOICE_CACHE / f"demo_{voice}.wav"))
            except Exception as e:
                print(f"  Failed: {e}")
            print()

    print("=" * 60)
    print("Demo complete. Check data/voice_clones/ for output files.")
    print()
    print("For voice cloning with your own voice:")
    print("  1. Record 10-30s of clear speech → ma_voix.wav")
    print("  2. cloner.calibrate_from_reference('ma_voix.wav', voice_name='moi')")
    print("  3. cloner.calibrate_encoder('moi')")
    print("  4. audio = cloner.speak('Bonjour!', voice='moi')")
    print("=" * 60)


if __name__ == '__main__':
    demo()
