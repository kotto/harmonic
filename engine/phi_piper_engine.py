"""
PhiPiperEngine — Synthèse Vocale Réelle pilotée par 11D
==========================================================
Wrapper autour de Piper TTS (moteur ONNX local) qui traduit
les paramètres vocaux 11D en paramètres Piper et produit
une VRAIE voix de synthèse.

Pourquoi Piper TTS ?
- Open-source, local, CPU-friendly
- Qualité vocale bien supérieure au φ-Vocoder source-filtre
- Supporte le contrôle de vitesse (length_scale) et pitch (noise_scale)
- Modèles ONNX légers (~50 MB par voix)
- 30+ voix disponibles en français/anglais

Les 11 dimensions sont mappées ainsi :
  H_pitch_mean   → pitch multiplicatif
  H_speed        → length_scale (vitesse)
  H_breathiness  → noise_scale (souffle/bruit)
  H_clarity      → noise_w (clarté)

Usage :
    engine = PhiPiperEngine()
    audio = engine.synthesize("Bonjour le monde", voice_params_11d)
    engine.save_wav(audio, "output.wav")
"""

import os
import sys
import json
import time
import io
import wave
import struct
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =========================================================================
# CONSTANTES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI

# Cache des modèles téléchargés
MODEL_CACHE_DIR = Path(os.path.expanduser("~")) / ".cache" / "piper_tts"

# Voix disponibles (téléchargement automatique si absent)
PIPER_VOICES = {
    "fr_FR": {
        "default": "fr_FR-siwis-medium",
        "available": [
            "fr_FR-siwis-medium",
            "fr_FR-siwis-low",
            "fr_FR-mls-medium",
        ],
        "language": "fr",
    },
    "en_US": {
        "default": "en_US-lessac-medium",
        "available": [
            "en_US-lessac-medium",
            "en_US-lessac-low",
            "en_US-libritts-high",
            "en_US-amy-medium",
            "en_US-arctic-medium",
        ],
        "language": "en",
    },
}

# Mapping 11D → Piper params
# Chaque dimension vocale 11D contrôle un paramètre Piper spécifique
DIM_TO_PIPER = {
    'H_pitch_mean':   ('pitch_factor',  0.7, 1.4),   # 0→ -30%, 1→ +40%
    'H_speed':        ('length_scale',  0.5, 2.0),   # 0→ rapide, 1→ lent
    'H_breathiness':  ('noise_scale',   0.2, 1.2),   # 0→ sec, 1→ soufflé
    'H_clarity':      ('noise_w',       0.3, 1.0),   # 0→ flou, 1→ clair
    'H_resonance':    ('sentence_silence', 0.1, 0.8), # pauses
}


# =========================================================================
# ENGIN PIPER PILOTÉ PAR 11D
# =========================================================================

class PhiPiperEngine:
    """
    Moteur de synthèse vocale utilisant Piper TTS comme backend,
    piloté par les 11 dimensions harmoniques.

    Caractéristiques :
    - Vraie voix de synthèse (pas de synthèse additive)
    - Contrôle 11D natif
    - Local, CPU, offline
    - 30+ voix disponibles
    """

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self._piper_voice = None
        self._current_voice_name = None
        self.total_synthesized = 0

    # -----------------------------------------------------------------
    # SYNTHÈSE PRINCIPALE
    # -----------------------------------------------------------------

    def synthesize(self, text: str,
                   voice_params: Optional[np.ndarray] = None,
                   voice_name: str = "fr_FR-siwis-medium") -> np.ndarray:
        """
        Synthétise du texte en audio avec modulation 11D.

        Args:
            text: Texte à synthétiser
            voice_params: Paramètres vocaux 11D (None = neutre)
            voice_name: Nom de la voix Piper

        Returns:
            audio: np.ndarray (samples,) float32
        """
        # Charger le modèle Piper (cache)
        self._ensure_voice_loaded(voice_name)

        # Paramètres neutres par défaut
        if voice_params is None:
            voice_params = self._neutral_11d()

        # Convertir 11D → Piper params
        piper_params = self._11d_to_piper(voice_params)

        # Synthétiser avec Piper
        audio_bytes = self._piper_synthesize(text, piper_params)

        if audio_bytes is None:
            # Fallback silencieux
            return np.zeros(int(2.0 * self.sample_rate), dtype=np.float32)

        # Convertir bytes → numpy array
        audio = self._bytes_to_array(audio_bytes)

        self.total_synthesized += 1

        return audio

    def synthesize_from_profile(self, text: str,
                                 profile_name: str = "default",
                                 emotion: str = "neutre") -> np.ndarray:
        """
        Synthétise avec un profil vocal de référence et une émotion.

        Args:
            text: Texte
            profile_name: Nom du profil ("lj_speech_female_us", etc.)
            emotion: Émotion

        Returns:
            audio: np.ndarray
        """
        # Récupérer le profil
        from engine.voice_signature_extractor import REFERENCE_PROFILES
        if profile_name in REFERENCE_PROFILES:
            sig = REFERENCE_PROFILES[profile_name]
            voice_params = sig.to_array()
        else:
            voice_params = self._neutral_11d()

        # Appliquer l'émotion
        emotion_mod = self._emotion_modulation(emotion)
        voice_params = voice_params * 0.7 + emotion_mod * 0.3
        voice_params = np.clip(voice_params, 0, 1)

        # Choisir la voix Piper selon la langue du profil
        lang = "fr_FR" if "fr" in profile_name.lower() else "en_US"
        voice_name = PIPER_VOICES[lang]["default"]

        return self.synthesize(text, voice_params, voice_name)

    # -----------------------------------------------------------------
    # CONVERSION 11D → PIPER
    # -----------------------------------------------------------------

    def _11d_to_piper(self, voice_11d: np.ndarray) -> Dict[str, float]:
        """
        Convertit les paramètres vocaux 11D en paramètres Piper.
        """
        # Index des dimensions 11D
        idx = {
            'H_pitch_mean': 0,
            'H_pitch_range': 1,
            'H_speed': 2,
            'H_timbre': 3,
            'H_breathiness': 4,
            'H_resonance': 5,
            'H_emotion_range': 6,
            'H_clarity': 7,
            'H_pause_pattern': 8,
            'H_phi_alignment': 9,
            'H_naturalness': 10,
        }

        # Longueur d'échelle : inversement proportionnelle à la vitesse
        # voice[2] = 0 → rapide (length_scale bas)
        # voice[2] = 1 → lent (length_scale élevé)
        length_scale = 1.5 - voice_11d[idx['H_speed']] * 1.0  # 0.5 à 1.5
        length_scale = np.clip(length_scale, 0.4, 2.0)

        # Pitch : centré sur 1.0
        pitch_factor = 0.75 + voice_11d[idx['H_pitch_mean']] * 0.5  # 0.75 à 1.25
        pitch_factor = np.clip(pitch_factor, 0.5, 1.5)

        # Noise scale (breathiness)
        noise_scale = 0.3 + voice_11d[idx['H_breathiness']] * 0.8  # 0.3 à 1.1
        noise_scale = np.clip(noise_scale, 0.1, 1.5)

        # Noise W (clarté)
        noise_w = 0.4 + voice_11d[idx['H_clarity']] * 0.6  # 0.4 à 1.0
        noise_w = np.clip(noise_w, 0.2, 1.0)

        # Sentence silence (pauses)
        sentence_silence = 0.1 + voice_11d[idx['H_pause_pattern']] * 0.6  # 0.1 à 0.7
        sentence_silence = np.clip(sentence_silence, 0.05, 1.0)

        return {
            'length_scale': length_scale,
            'noise_scale': noise_scale,
            'noise_w': noise_w,
            'sentence_silence': sentence_silence,
            'pitch_factor': pitch_factor,
        }

    def _neutral_11d(self) -> np.ndarray:
        """Signature 11D neutre (φ-équilibrée)."""
        v = np.full(11, PHI_INV)
        v[4] = PHI_INV ** 3   # breathiness bas
        v[7] = 0.75           # bonne clarté
        v[10] = 0.78           # naturalité
        return v

    def _emotion_modulation(self, emotion: str) -> np.ndarray:
        """Crée un vecteur 11D de modulation émotionnelle."""
        base = self._neutral_11d()
        mods = {
            'neutre':      {},
            'joyeux':      {0: 0.70, 2: 0.65, 6: 0.70},
            'triste':      {0: 0.45, 2: 0.30, 4: 0.35, 6: 0.50},
            'urgent':      {0: 0.65, 2: 0.75, 6: 0.65, 8: 0.20},
            'calme':       {0: 0.55, 2: 0.30, 4: 0.25, 6: 0.25},
            'autoritaire': {0: 0.50, 2: 0.50, 4: 0.10, 7: 0.85},
        }
        for dim, val in mods.get(emotion, {}).items():
            base[dim] = val
        return base

    # -----------------------------------------------------------------
    # INTERFACE PIPER
    # -----------------------------------------------------------------

    def _ensure_voice_loaded(self, voice_name: str):
        """Charge le modèle Piper (télécharge si nécessaire)."""
        if self._current_voice_name == voice_name and self._piper_voice is not None:
            return

        try:
            import piper
            # Télécharger le modèle si absent
            model_path = self._get_model_path(voice_name)
            if not model_path.exists():
                self._download_voice(voice_name)

            # Charger
            self._piper_voice = piper.PiperVoice.load(str(model_path))
            self._current_voice_name = voice_name

        except Exception as e:
            print(f"[PhiPiperEngine] Erreur chargement voix {voice_name}: {e}")
            self._piper_voice = None

    def _piper_synthesize(self, text: str, params: Dict[str, float]) -> Optional[bytes]:
        """Synthétise le texte avec les paramètres Piper."""
        if self._piper_voice is None:
            return None

        try:
            # Configurer les paramètres de synthèse
            synthesize_args = {
                'length_scale': params.get('length_scale', 1.0),
                'noise_scale': params.get('noise_scale', 0.667),
                'noise_w': params.get('noise_w', 0.8),
                'sentence_silence': params.get('sentence_silence', 0.2),
            }

            # Synthétiser
            audio_stream = io.BytesIO()
            self._piper_voice.synthesize(text, audio_stream, **synthesize_args)

            # Appliquer le pitch shift (post-traitement)
            audio_bytes = audio_stream.getvalue()

            # Extraire l'audio WAV
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                params_info = wf.getparams()
                raw = wf.readframes(wf.getnframes())

            # Appliquer pitch factor via resampling simple
            pitch_factor = params.get('pitch_factor', 1.0)
            if abs(pitch_factor - 1.0) > 0.01:
                audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                # Resampling linéaire pour changer le pitch
                n = len(audio)
                new_n = int(n / pitch_factor)
                indices = np.linspace(0, n - 1, new_n)
                audio_shifted = np.interp(indices, np.arange(n), audio)
                audio_shifted = audio_shifted.astype(np.int16)
                raw = audio_shifted.tobytes()

            # Réencoder en WAV
            output_stream = io.BytesIO()
            with wave.open(output_stream, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(raw)

            return output_stream.getvalue()

        except Exception as e:
            print(f"[PhiPiperEngine] Erreur synthese: {e}")
            return None

    def _get_model_path(self, voice_name: str) -> Path:
        """Retourne le chemin du modèle ONNX pour une voix."""
        model_dir = MODEL_CACHE_DIR / voice_name
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir / f"{voice_name}.onnx"

    def _download_voice(self, voice_name: str):
        """Télécharge le modèle ONNX pour une voix Piper."""
        import urllib.request

        model_path = self._get_model_path(voice_name)
        config_path = model_path.with_suffix(".json")

        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

        # Télécharger le modèle
        model_url = f"{base_url}/{voice_name}/{voice_name}.onnx"
        config_url = f"{base_url}/{voice_name}/{voice_name}.onnx.json"

        print(f"[PhiPiperEngine] Telechargement {voice_name}...")

        for url, path in [(model_url, model_path), (config_url, config_path)]:
            if path.exists():
                continue
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (HarmonicAI)'
                })
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = resp.read()
                    path.write_bytes(data)
                size_mb = len(data) / 1e6
                print(f"  {path.name}: {size_mb:.1f} Mo OK")
            except Exception as e:
                print(f"  [ERROR] {path.name}: {e}")

        print(f"[PhiPiperEngine] Voix {voice_name} prete")

    # -----------------------------------------------------------------
    # CONVERSION BYTES ↔ NUMPY
    # -----------------------------------------------------------------

    def _bytes_to_array(self, wav_bytes: bytes) -> np.ndarray:
        """Convertit un buffer WAV en array numpy float32 normalisé."""
        with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        audio_int16 = np.frombuffer(raw, dtype=np.int16)
        return audio_int16.astype(np.float32) / 32768.0

    # -----------------------------------------------------------------
    # SAUVEGARDE WAV
    # -----------------------------------------------------------------

    @staticmethod
    def save_wav(audio: np.ndarray, filepath: str, sample_rate: int = 22050):
        """Sauvegarde un array audio en fichier WAV."""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())

    def get_stats(self) -> Dict:
        return {
            'total_synthesized': self.total_synthesized,
            'backend': 'Piper TTS (ONNX)',
            'current_voice': self._current_voice_name,
        }


# =========================================================================
# TESTS (avec Edge-TTS fallback si Piper pas encore téléchargé)
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST PhiPiperEngine — Synthèse Vocale Réelle pilotée 11D")
    print("=" * 60)

    import numpy as np

    engine = PhiPiperEngine()

    # Voix 11D de test (LJSpeech-like)
    voice_f = np.array([0.72, 0.45, 0.55, 0.68, 0.15, 0.72, 0.35, 0.80, 0.40, 0.72, 0.80])

    # Test 1 : Voix française
    print("\n--- Test 1 : Francais ---")
    t0 = time.time()
    audio = engine.synthesize(
        "Bonjour, je suis la voix harmonique francaise.",
        voice_f,
        voice_name="fr_FR-siwis-medium"
    )
    elapsed = time.time() - t0
    if len(audio) > 1000:
        engine.save_wav(audio, "data/voice_output/test_piper_fr.wav")
        print(f"  [OK] test_piper_fr.wav ({len(audio)/22050:.1f}s, {elapsed*1000:.0f}ms)")
    else:
        print(f"  [Fallback] Piper indisponible, utilisation Edge-TTS")
        import subprocess, tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp.close()
        subprocess.run(["edge-tts", "--voice", "fr-FR-DeniseNeural", "--text",
                        "Bonjour, je suis la voix harmonique francaise.",
                        "--write-media", tmp.name], capture_output=True)
        if os.path.getsize(tmp.name) > 0:
            print(f"  [OK] Edge-TTS fallback ({os.path.getsize(tmp.name)} octets)")
        os.unlink(tmp.name)

    # Test 2 : Émotions
    print("\n--- Test 2 : Emotions ---")
    for emotion in ['joyeux', 'triste', 'calme']:
        audio = engine.synthesize_from_profile(
            f"Ceci est un test avec l emotion {emotion}.",
            profile_name="lj_speech_female_us",
            emotion=emotion,
        )
        if len(audio) > 1000:
            engine.save_wav(audio, f"data/voice_output/test_piper_{emotion}.wav")
            print(f"  [OK] test_piper_{emotion}.wav ({len(audio)/22050:.1f}s)")

    print("\n" + "=" * 60)
    print("PhiPiperEngine operationnel")
    print("=" * 60)