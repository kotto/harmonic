"""
XTTS Engine — Synthèse vocale locale haute qualité (mémoire optimisée)
========================================================================
Wrapper mémoire-optimisé pour Coqui XTTS-v2.

Problème résolu :
  XTTS-v2 charge ~1.8 GB en RAM. Sur un serveur 8 GB, le chargement
  échoue si >5 GB sont déjà utilisés. Le modèle n'était jamais chargé.

Solutions :
  1. Chargement lazy (seulement quand on synthétise)
  2. Instance unique (singleton, pas de double chargement)
  3. Seuil RAM abaissé à 2.5 GB (XTTS ≈ 1.8 GB + marge)
  4. Mode CPU forcé (pas de VRAM GPU)
  5. Nettoyage automatique après 5 min d'inactivité
  6. Fallback silencieux vers Edge-TTS si RAM insuffisante

Usage :
  from xtts_engine import get_xtts
  xtts = get_xtts()
  audio = xtts.speak("Bonjour", language="fr")

Dépendances (optionnelles) :
  pip install TTS coqui-tts  # ~1.8 GB de modèles téléchargés automatiquement
"""

import sys, os, time, threading, gc, logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class XTTSEngine:
    """
    Moteur XTTS-v2 mémoire-optimisé.
    
    Charge le modèle UNE fois, le conserve en mémoire 5 minutes
    après la dernière utilisation, puis le libère.
    """
    
    # Configuration mémoire
    MIN_FREE_RAM_GB = 2.5      # RAM libre minimum (XTTS ≈ 1.8 GB)
    IDLE_TIMEOUT_S = 300        # 5 minutes d'inactivité → déchargement
    MAX_TEXT_LENGTH = 500       # Éviter les textes trop longs (OOM)
    
    def __init__(self):
        self._model = None
        self._last_used = 0.0
        self._lock = threading.Lock()
        self._cleanup_timer = None
        self._available = None  # None = pas encore vérifié
    
    @property
    def is_available(self) -> bool:
        """Vérifie si XTTS est disponible (RAM suffisante + module installé)."""
        if self._available is not None:
            return self._available
        
        # Vérifier que TTS est installé (sans importer — juste le package)
        try:
            import importlib.util
            spec = importlib.util.find_spec("TTS")
            if spec is None:
                self._available = False
                return False
        except Exception:
            self._available = False
            return False
        
        # Vérifier la RAM disponible
        try:
            import psutil
            avail_gb = psutil.virtual_memory().available / (1024**3)
            if avail_gb < self.MIN_FREE_RAM_GB:
                log.info(f"XTTS: RAM insuffisante ({avail_gb:.1f} GB libre < {self.MIN_FREE_RAM_GB} requis)")
                # Ne PAS mettre en cache : la RAM peut se libérer → réessai au prochain appel
                return False
        except ImportError:
            pass  # psutil non installé → on tente quand même
        
        self._available = True
        return True
    
    def _load_model(self):
        """Charge le modèle XTTS (appelé une seule fois)."""
        if self._model is not None:
            return
        
        with self._lock:
            if self._model is not None:
                return
            
            log.info("XTTS: Chargement du modèle...")
            t0 = time.time()
            
            try:
                from TTS.api import TTS
                
                # Mode CPU uniquement (pas de GPU)
                import os
                os.environ["CUDA_VISIBLE_DEVICES"] = ""
                
                self._model = TTS(
                    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                    progress_bar=False,
                    gpu=False,
                )
                
                dt = time.time() - t0
                log.info(f"XTTS: Modèle chargé en {dt:.1f}s")
                
            except Exception as e:
                log.warning(f"XTTS: Échec du chargement ({e})")
                self._model = None
                self._available = False
                raise
    
    def _schedule_cleanup(self):
        """Planifie le déchargement après période d'inactivité."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
        
        self._cleanup_timer = threading.Timer(self.IDLE_TIMEOUT_S, self._unload)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
    
    def _unload(self):
        """Décharge le modèle pour libérer la RAM."""
        with self._lock:
            if self._model is not None:
                log.info("XTTS: Déchargement (inactivité)")
                self._model = None
                gc.collect()
    
    def speak(self, text: str, language: str = "fr",
              speaker_wav: str = None, speed: float = 1.0) -> Optional[bytes]:
        """
        Synthétise du texte en audio.
        
        Args:
            text: texte à synthétiser (max 500 caractères)
            language: 'fr', 'en', 'es', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko'
            speaker_wav: chemin vers un fichier WAV de référence (clonage vocal)
            speed: vitesse (0.5 à 2.0)
        
        Returns:
            bytes WAV 24 kHz, ou None si échec
        """
        if not self.is_available:
            return None
        
        # Limiter la taille du texte
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH]
        
        try:
            self._load_model()

            with self._lock:
                self._last_used = time.time()

            # Synthèse — fichier temporaire réel (BytesIO n'est pas accepté par
            # tous les backends Coqui : soundfile exige un chemin)
            import os, tempfile
            fd, tmp_path = tempfile.mkstemp(prefix="xtts_", suffix=".wav")
            os.close(fd)
            try:
                # Choisir le speaker : XTTS-v2 est un modèle de CLONAGE —
                # il n'a pas de liste `speakers` et exige speaker_wav.
                kwargs = dict(text=text, file_path=tmp_path,
                              language=language, speed=speed)
                speakers = getattr(self._model, "speakers", None)
                if speaker_wav:
                    kwargs["speaker_wav"] = speaker_wav
                elif speakers:
                    kwargs["speaker"] = speakers[0]  # modèles multi-locuteurs

                self._model.tts_to_file(**kwargs)

                with open(tmp_path, "rb") as f:
                    audio = f.read()
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            # Planifier le nettoyage
            self._schedule_cleanup()

            return audio

        except Exception as e:
            log.warning(f"XTTS: Erreur de synthèse ({e})")
            return None
    
    def speak_stream(self, text: str, language: str = "fr") -> list:
        """
        Synthèse streamée : découpe le texte en phrases et synthétise séparément.
        """
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        results = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            audio = self.speak(sentence, language)
            if audio:
                results.append(audio)
        
        return results
    
    @property
    def stats(self) -> dict:
        return {
            'available': self.is_available,
            'loaded': self._model is not None,
            'last_used': self._last_used,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_xtts_instance = None

def get_xtts() -> XTTSEngine:
    """Retourne l'instance unique du moteur XTTS."""
    global _xtts_instance
    if _xtts_instance is None:
        _xtts_instance = XTTSEngine()
    return _xtts_instance
