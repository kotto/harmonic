"""
KA Server — Service Voice Engine (Piper TTS + Vosk STT)
========================================================
Gestion paresseuse des modèles vocaux avec téléchargement à la demande.
"""

import logging
import os
import json
import subprocess
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

log = logging.getLogger(__name__)

# État global
_VOICE_ENGINE = None
_PIPER_READY = False
_VOSK_READY = False
_MODELS_DIR = None
_DOWNLOAD_LOCKS = {}


@dataclass
class VoiceStatus:
    tts_available: bool
    stt_available: bool
    piper_version: str = None
    vosk_version: str = None
    models: dict = None
    error: str = None


def init_voice_engine(models_dir: str = None) -> Optional['VoiceEngine']:
    """Initialise le moteur vocal (lazy - télécharge modèles si nécessaire)."""
    global _VOICE_ENGINE, _MODELS_DIR, _PIPER_READY, _VOSK_READY
    
    if _VOICE_ENGINE is not None:
        return _VOICE_ENGINE
    
    # Déterminer dossier modèles
    if models_dir:
        _MODELS_DIR = Path(models_dir)
    else:
        _MODELS_DIR = Path(__file__).resolve().parent.parent.parent / 'models' / 'voice'
    
    _MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Vérifier Piper
    _PIPER_READY = _check_piper()
    
    # Vérifier Vosk
    _VOSK_READY = _check_vosk()
    
    if not _PIPER_READY and not _VOSK_READY:
        log.warning("  🎤 Voice Engine: ni Piper ni Vosk disponibles")
        return None
    
    _VOICE_ENGINE = VoiceEngine(_MODELS_DIR)
    log.info(f"  🎤 Voice Engine initialisé (Piper={_PIPER_READY}, Vosk={_VOSK_READY})")
    return _VOICE_ENGINE


def get_voice_engine() -> Optional['VoiceEngine']:
    return _VOICE_ENGINE


def _check_piper() -> bool:
    """Vérifie si Piper TTS est installé."""
    try:
        import piper
        return True
    except ImportError:
        # Essayer binaire
        for cmd in ['piper', 'piper-tts']:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, check=True)
                return True
            except Exception:
                pass
    return False


def _check_vosk() -> bool:
    """Vérifie si Vosk STT est installé."""
    try:
        import vosk
        return True
    except ImportError:
        return False


class VoiceEngine:
    """Moteur vocal unifié Piper + Vosk."""
    
    PIPER_VOICES = {
        'fr_FR': 'fr_FR-siwis-medium',
        'fr_FR-siwis': 'fr_FR-siwis-medium',
        'fr_FR-upmc': 'fr_FR-upmc-medium',
        'en_US': 'en_US-lessac-medium',
        'en_US-lessac': 'en_US-lessac-medium',
        'en_US-libritts': 'en_US-libritts_r-medium',
        'de_DE': 'de_DE-thorsten-medium',
        'es_ES': 'es_ES-sharvard-medium',
        'it_IT': 'it_IT-riccardo-medium',
    }
    
    VOSK_MODELS = {
        'fr': 'vosk-model-fr-0.22',
        'en': 'vosk-model-en-us-0.22',
        'de': 'vosk-model-de-0.21',
        'es': 'vosk-model-es-0.42',
        'it': 'vosk-model-it-0.22',
    }
    
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.piper_bin = self._find_piper()
        self._vosk_models = {}
        self._piper_voices_cache = {}
    
    def _find_piper(self) -> str:
        for cmd in ['piper', 'piper-tts']:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, check=True)
                return cmd
            except Exception:
                pass
        return 'piper'  # Fallback
    
    # ── TTS (Piper) ─────────────────────────────────────────────────────────
    
    def synthesize(self, text: str, voice: str = 'fr_FR', speed: float = 1.0) -> Optional[bytes]:
        """Synthèse vocale avec Piper."""
        if not _PIPER_READY:
            log.warning("Piper non disponible")
            return None
        
        # Résoudre nom voix
        voice_id = self.PIPER_VOICES.get(voice, voice)
        
        # S'assurer que le modèle existe
        model_path = self._ensure_piper_model(voice_id)
        if not model_path:
            return None
        
        try:
            # Piper en ligne de commande (plus robuste que l'API Python)
            cmd = [
                self.piper_bin,
                '--model', str(model_path),
                '--output_raw',  # Sortie PCM brut
            ]
            
            if speed != 1.0:
                cmd.extend(['--length_scale', str(1.0 / speed)])
            
            proc = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                check=True
            )
            
            # Convertir PCM brut → WAV
            return self._pcm_to_wav(proc.stdout)
            
        except subprocess.CalledProcessError as e:
            log.error(f"Piper failed: {e.stderr.decode() if e.stderr else e}")
            return None
        except Exception as e:
            log.error(f"TTS error: {e}")
            return None
    
    def _ensure_piper_model(self, voice_id: str) -> Optional[Path]:
        """Télécharge modèle Piper si nécessaire."""
        model_path = self.models_dir / 'piper' / f'{voice_id}.onnx'
        config_path = self.models_dir / 'piper' / f'{voice_id}.onnx.json'
        
        if model_path.exists() and config_path.exists():
            return model_path
        
        # Télécharger
        lock_key = f'piper_{voice_id}'
        if lock_key not in _DOWNLOAD_LOCKS:
            _DOWNLOAD_LOCKS[lock_key] = threading.Lock()
        
        with _DOWNLOAD_LOCKS[lock_key]:
            # Double-check après lock
            if model_path.exists() and config_path.exists():
                return model_path
            
            log.info(f"  🎤 Téléchargement modèle Piper: {voice_id}")
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # URL Hugging Face (structure: lang/lang_code/voice_name/quality/voice_id.onnx)
            # Ex: fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
            # voice_id = 'fr_FR-siwis-medium'
            parts = voice_id.split('-')  # ['fr_FR', 'siwis', 'medium']
            lang_code = parts[0]          # 'fr_FR'
            lang = lang_code.split('_')[0]  # 'fr'
            voice_name = parts[1] if len(parts) > 1 else 'siwis'  # 'siwis'
            quality = parts[2] if len(parts) > 2 else 'medium'     # 'medium'
            vpath = f'{lang}/{lang_code}/{voice_name}/{quality}/{voice_id}'
            base_url = f'https://huggingface.co/rhasspy/piper-voices/resolve/main/{vpath}'
            
            try:
                import urllib.request
                urllib.request.urlretrieve(f'{base_url}.onnx', model_path)
                urllib.request.urlretrieve(f'{base_url}.onnx.json', config_path)
                log.info(f"  🎤 Modèle Piper téléchargé: {voice_id}")
                return model_path
            except Exception as e:
                log.error(f"  🎤 Échec téléchargement Piper {voice_id}: {e}")
                # Nettoyer fichiers partiels
                for p in [model_path, config_path]:
                    if p.exists():
                        p.unlink()
                return None
    
    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 22050, channels: int = 1, bits: int = 16) -> bytes:
        """Convertit PCM brut en WAV."""
        import wave
        import io
        
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(bits // 8)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm_data)
        return output.getvalue()
    
    # ── STT (Vosk) ──────────────────────────────────────────────────────────
    
    def transcribe(self, audio_data: bytes, language: str = 'fr') -> Optional[str]:
        """Transcription vocale avec Vosk."""
        if not _VOSK_READY:
            log.warning("Vosk non disponible")
            return None
        
        try:
            import vosk
        except ImportError:
            return None
        
        # S'assurer que le modèle existe
        model = self._ensure_vosk_model(language)
        if not model:
            return None
        
        try:
            # Convertir audio en format Vosk (16kHz mono PCM)
            pcm_data = self._convert_audio_for_vosk(audio_data)
            if not pcm_data:
                return None
            
            rec = vosk.KaldiRecognizer(model, 16000)
            rec.SetWords(True)
            
            # Traiter par chunks
            chunk_size = 4000
            for i in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[i:i+chunk_size]
                rec.AcceptWaveform(chunk)
            
            result = json.loads(rec.FinalResult())
            return result.get('text', '').strip()
            
        except Exception as e:
            log.error(f"STT error: {e}")
            return None
    
    def _ensure_vosk_model(self, language: str):
        """Charge/télécharge modèle Vosk."""
        if language in self._vosk_models:
            return self._vosk_models[language]
        
        model_name = self.VOSK_MODELS.get(language, self.VOSK_MODELS['en'])
        model_path = self.models_dir / 'vosk' / model_name
        
        if not model_path.exists():
            lock_key = f'vosk_{language}'
            if lock_key not in _DOWNLOAD_LOCKS:
                _DOWNLOAD_LOCKS[lock_key] = threading.Lock()
            
            with _DOWNLOAD_LOCKS[lock_key]:
                if model_path.exists():
                    pass
                else:
                    log.info(f"  🎤 Téléchargement modèle Vosk: {model_name}")
                    model_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        import urllib.request
                        import zipfile
                        
                        url = f'https://alphacephei.com/vosk/models/{model_name}.zip'
                        zip_path = model_path.parent / f'{model_name}.zip'
                        
                        urllib.request.urlretrieve(url, zip_path)
                        
                        with zipfile.ZipFile(zip_path, 'r') as zf:
                            zf.extractall(model_path.parent)
                        
                        zip_path.unlink()
                        log.info(f"  🎤 Modèle Vosk téléchargé: {model_name}")
                    except Exception as e:
                        log.error(f"  🎤 Échec téléchargement Vosk {model_name}: {e}")
                        return None
        
        try:
            import vosk
            model = vosk.Model(str(model_path))
            self._vosk_models[language] = model
            return model
        except Exception as e:
            log.error(f"  🎤 Erreur chargement modèle Vosk: {e}")
            return None
    
    def _convert_audio_for_vosk(self, audio_data: bytes) -> Optional[bytes]:
        """Convertit audio en 16kHz mono PCM pour Vosk."""
        try:
            import io
            import wave
            
            # Lire WAV existant
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_in:
                n_channels = wav_in.getnchannels()
                sample_width = wav_in.getsampwidth()
                frame_rate = wav_in.getframerate()
                frames = wav_in.readframes(wav_in.getnframes())
            
            # Si déjà bon format, retourner
            if frame_rate == 16000 and n_channels == 1 and sample_width == 2:
                return frames
            
            # Resample avec audioop (std lib) ou pydub si dispo
            try:
                import audioop
                
                # Convertir en mono
                if n_channels > 1:
                    frames = audioop.tomono(frames, sample_width, 1.0, 1.0)
                
                # Resample
                if frame_rate != 16000:
                    frames = audioop.ratecv(frames, sample_width, 1, frame_rate, 16000, None)[0]
                
                # Assurer 16-bit
                if sample_width != 2:
                    if sample_width == 1:
                        frames = audioop.lin2lin(frames, 1, 2)
                    elif sample_width == 3:
                        frames = audioop.lin2lin(frames, 3, 2)
                    elif sample_width == 4:
                        frames = audioop.lin2lin(frames, 4, 2)
                
                return frames
            except Exception:
                # Fallback pydub
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment(
                        data=frames,
                        sample_width=sample_width,
                        frame_rate=frame_rate,
                        channels=n_channels
                    )
                    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                    return audio.raw_data
                except Exception:
                    pass
            
            return None
        except Exception as e:
            log.error(f"Audio conversion failed: {e}")
            return None
    
    # ── Utilitaires ─────────────────────────────────────────────────────────
    
    def list_voices(self) -> List[Dict[str, Any]]:
        """Liste les voix disponibles."""
        voices = []
        
        # Piper
        if _PIPER_READY:
            for key, model_id in self.PIPER_VOICES.items():
                lang = key.split('_')[0]
                voices.append({
                    'id': key,
                    'model_id': model_id,
                    'engine': 'piper',
                    'language': lang,
                    'downloaded': self._is_piper_downloaded(model_id),
                })
        
        # Vosk
        if _VOSK_READY:
            for lang, model_name in self.VOSK_MODELS.items():
                voices.append({
                    'id': f'vosk_{lang}',
                    'model_id': model_name,
                    'engine': 'vosk',
                    'language': lang,
                    'type': 'stt',
                    'downloaded': (self.models_dir / 'vosk' / model_name).exists(),
                })
        
        return voices
    
    def _is_piper_downloaded(self, model_id: str) -> bool:
        path = self.models_dir / 'piper' / f'{model_id}.onnx'
        return path.exists()
    
    def get_status(self) -> VoiceStatus:
        """Status du moteur vocal."""
        return VoiceStatus(
            tts_available=_PIPER_READY,
            stt_available=_VOSK_READY,
            models={
                'piper': [v for v in self.list_voices() if v['engine'] == 'piper'],
                'vosk': [v for v in self.list_voices() if v['engine'] == 'vosk'],
            }
        )


# Fonctions utilitaires pour compatibilité
def synthesize_text(text: str, voice: str = 'fr_FR') -> Optional[bytes]:
    """API simple pour TTS."""
    engine = get_voice_engine()
    if engine:
        return engine.synthesize(text, voice)
    return None


def transcribe_audio(audio_data: bytes, language: str = 'fr') -> Optional[str]:
    """API simple pour STT."""
    engine = get_voice_engine()
    if engine:
        return engine.transcribe(audio_data, language)
    return None