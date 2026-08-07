"""
Bridge — Pont déterministe entre les couches symbolique (ℂ⁵¹²) et acoustique (ℝ¹⁶).

Rôle : pour chaque diphone cible (gauche, droite), cette couche :
  1. Encode les phonèmes en ψ via le SymbolicEncoder (composition linguistique)
  2. Projette chaque phonème vers des features acoustiques cibles (règles)
  3. Modifie les cibles via l'émotion + la prosodie française
  4. Combine les features acoustiques gauche+droite en un vecteur cible 16D
  5. Interroge l'AcousticEncoder KD-tree pour le meilleur diphone
  6. Concatène les diphones avec crossfade
  7. Applique la signature vocale (pitch, timbre, breathiness)

Le pont est 100% déterministe — aucune matrice apprise, uniquement des
règles phonétiques et des projections arithmétiques simples.

Flux complet :
    texte → phonèmes → [SymbolicEncoder: ψ_symbolique]
                     → [Bridge: features acoustiques cibles + émotion + prosodie]
                     → [AcousticEncoder KD-tree: diphone réel]
                     → [concaténation + signature vocale]
"""

import math
import re
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from .symbolic_encoder import SymbolicEncoder, encode_phoneme, bind, unbind, similarity
from .acoustic_encoder import (
    AcousticEncoder, AcousticEntry, phoneme_to_acoustic_target,
    ACOUSTIC_DIM, weighted_distance,
)
from .glottal_synth import build_synthetic_bank, SynthDiphone
from .phoneme_features import PHONEME_FEATURES, VOYELLES, OCCLUSIVES

DEFAULT_SR = 22050

# ═══════════════════════════════════════════════════════════════════════════════
# ÉMOTIONS — Table de modulation
# ═══════════════════════════════════════════════════════════════════════════════

# Chaque émotion modifie le vecteur acoustique cible :
#   [f0_shift, f0_range, speed, timbre, breathiness, energy, duration_factor, pause_factor]
EMOTION_PROFILES: Dict[str, Tuple[float, ...]] = {
    "neutre":     ( 0.0,  0.0,  1.0,  0.0,  0.0,   0.0,  1.0,   1.0),
    "joyeux":     (+0.15, 0.3,  1.15, 0.1, -0.05,  0.1,  0.85,  0.8),
    "triste":     (-0.10,-0.2,  0.85,-0.1,  0.1,  -0.15, 1.2,   1.3),
    "urgent":     (+0.10, 0.15, 1.25, 0.05,  0.0,   0.15, 0.75,  0.5),
    "calme":      (-0.05,-0.1,  0.80, 0.0,   0.05, -0.1,  1.1,   1.5),
    "autoritaire":(+0.05, 0.1,  1.0,  0.0,  -0.05,  0.2,  0.95,  0.7),
    "chaleureux": (+0.05, 0.2,  0.95, 0.05,  0.05,  0.05, 1.0,   1.0),
    "tendre":     (-0.05, 0.15, 0.85, 0.0,   0.1,  -0.05, 1.1,   1.2),
}

# Contours F0 par émotion (modulation temporelle sur la phrase)
# Format : [(position_normalisée 0..1, multiplicateur_f0)]
EMOTION_F0_CONTOURS: Dict[str, List[Tuple[float, float]]] = {
    "neutre":     [(0.0, 1.0), (0.5, 1.0), (1.0, 0.9)],
    "joyeux":     [(0.0, 0.9), (0.4, 1.15), (0.7, 1.2), (1.0, 1.05)],
    "triste":     [(0.0, 1.0), (0.5, 0.9), (1.0, 0.75)],
    "urgent":     [(0.0, 1.05), (0.3, 1.1), (1.0, 1.0)],
    "calme":      [(0.0, 0.95), (0.5, 1.0), (1.0, 0.9)],
    "autoritaire":[(0.0, 1.05), (0.3, 1.1), (0.6, 1.0), (1.0, 0.85)],
    "chaleureux": [(0.0, 1.0), (0.3, 1.1), (0.6, 1.05), (1.0, 1.0)],
    "tendre":     [(0.0, 0.95), (0.5, 1.05), (1.0, 0.9)],
}


# ═══════════════════════════════════════════════════════════════════════════════
# PROSODIE FRANÇAISE — Détection des groupes accentuels
# ═══════════════════════════════════════════════════════════════════════════════

# Mots grammaticaux (ne portent pas d'accent, sauf en fin de groupe)
GRAMMATICAL_WORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "au", "aux",
    "ce", "cet", "cette", "ces", "mon", "ton", "son", "ma", "ta", "sa",
    "mes", "tes", "ses", "notre", "votre", "leur", "nos", "vos", "leurs",
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "me", "te", "se", "le", "la", "lui", "leur", "y", "en",
    "que", "qui", "dont", "où", "quoi",
    "ne", "pas", "plus", "jamais", "rien",
    "et", "ou", "mais", "donc", "car", "ni", "or",
    "à", "dans", "par", "pour", "sur", "sous", "avec", "sans",
    "très", "trop", "peu", "bien", "mal", "mieux",
}


def detect_accentual_groups(words: List[str]) -> List[List[int]]:
    """Détecte les groupes accentuels dans une liste de mots.

    Règle française : le dernier mot lexical (non-grammatical) de chaque
    groupe reçoit l'accent. Un groupe se termine avant une pause (ponctuation)
    ou après ~7 syllabes.

    Retourne : liste de groupes, chaque groupe = liste d'indices de mots.
    """
    if not words:
        return []

    groups = []
    current = []
    syllable_count = 0

    for i, word in enumerate(words):
        current.append(i)
        # Estimation syllabes : ~1.5 syllabes par mot en français
        syllable_count += max(1, len(word) // 3)

        # Fin de groupe si ponctuation ou > 7 syllabes
        has_punctuation = word and word[-1] in ".!?,;:"
        if has_punctuation or syllable_count >= 7 or i == len(words) - 1:
            groups.append(current)
            current = []
            syllable_count = 0

    if current:
        groups.append(current)

    return groups


def get_accented_syllable(words: List[str], group: List[int]) -> int:
    """Retourne l'index du mot accentué dans le groupe.
    
    Règle : dernier mot LEXICAL du groupe. Si tous grammaticaux, dernier mot.
    """
    for idx in reversed(group):
        word = words[idx].strip(".!,?;:").lower()
        if word not in GRAMMATICAL_WORDS:
            return idx
    return group[-1]


# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# Pont Symbolique → Acoustique
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicBridge:
    """Pont déterministe entre les couches symbolique et acoustique.
    
    Usage :
        bridge = HarmonicBridge()
        bridge.build_bank()
        audio = bridge.speak("Bonjour", voice="femme", emotion="joyeux")
        bridge.clone_voice("reference.wav", name="Pierre")
        audio = bridge.speak("Bonjour", voice="Pierre")
    """

    def __init__(self, sr: int = DEFAULT_SR):
        self.sr = sr
        self.symbolic = SymbolicEncoder()
        self.acoustic = AcousticEncoder(dim=ACOUSTIC_DIM)
        self._bank: List[SynthDiphone] = []
        self._bank_built = False
        
        # Voix : signature 11D (DSP) + voice print harmonique (filtre spectral)
        from .voice_signature import VoiceSignature, DEFAULT_VOICES
        self._voices: Dict[str, VoiceSignature] = dict(DEFAULT_VOICES)
        self._voice_prints: Dict[str, object] = {}  # HarmonicVoicePrint
        self._default_voice = "homme"
        self._use_harmonic_clone = True  # priorité au clonage harmonique si dispo

    # ── Construction de la banque synthétique ──────────────────────────

    def build_bank(self, phonemes: Optional[List[str]] = None, f0_default: float = 120.0):
        """Construit la banque de diphones synthétiques et l'index KD-tree."""
        self._bank = build_synthetic_bank(
            phonemes=phonemes, sr=self.sr, f0_default=f0_default,
        )
        
        # Peupler l'AcousticEncoder
        for diph in self._bank:
            # Features acoustiques du diphone depuis les règles
            feat_left = phoneme_to_acoustic_target(diph.left)
            feat_right = phoneme_to_acoustic_target(diph.right)
            # Combiner : moyenne pondérée (plus de poids au phonème droit pour la transition)
            features = 0.4 * feat_left + 0.6 * feat_right
            # Ajouter l'info de durée réelle
            features[3] = diph.duration_s / 0.25  # normaliser durée
            
            self.acoustic.add_diphone(
                left=diph.left, right=diph.right,
                features=features, audio=diph.audio,
                sample_rate=diph.sample_rate,
            )
        
        self.acoustic.build_index()
        self._bank_built = True

    @property
    def bank_size(self) -> int:
        return len(self._bank)

    # ── Projection : phonème → cible acoustique (règles) ──────────────

    def _target_features(self, left: str, right: str, f0: float = 120.0, duration_s: float = 0.120) -> np.ndarray:
        """Calcule le vecteur de features acoustiques cible pour un diphone donné.
        
        Combine les projections individuelles gauche/droite avec les paramètres
        de prosodie (F0, durée).
        """
        fl = phoneme_to_acoustic_target(left)
        fr = phoneme_to_acoustic_target(right)
        
        # Combinaison pondérée (transition gauche→droite)
        target = 0.4 * fl + 0.6 * fr
        
        # Injecter F0 et durée cible (depuis la prosodie)
        if f0 > 0:
            f0_log = math.log(f0 / 100.0) / math.log(400.0 / 100.0)
            target[0] = np.clip(f0_log, 0.0, 1.0)
        else:
            target[0] = 0.0
        target[3] = np.clip(duration_s / 0.25, 0.0, 1.0)
        
        return target.astype(np.float32)

    # ── Synthèse par retrieval ─────────────────────────────────────────

    def synthesize(
        self,
        phonemes: List[str],
        f0: float = 120.0,
        speed: float = 1.0,
        emotion: str = "neutre",
        voice: str = "default",
    ) -> np.ndarray:
        """Synthétise une séquence de phonèmes en audio avec émotion + voix.
        
        Args:
            phonemes : liste de symboles phonétiques
            f0 : F0 de base (Hz), modifiée par la voix + émotion
            speed : facteur de vitesse
            emotion : nom de l'émotion (neutre, joyeux, triste, urgent, calme, ...)
            voice : nom de la voix (homme, femme, enfant, ou nom cloné)
        
        Returns:
            audio float32 [-1, 1] à self.sr Hz
        """
        if not self._bank_built:
            self.build_bank()
        
        if len(phonemes) < 2:
            return self._single_phoneme(phonemes[0] if phonemes else "_", f0)
        
        # RNG déterministe (seed basée sur le texte)
        text_seed = hash("".join(phonemes)) & 0x7FFFFFFF
        rng = np.random.RandomState(text_seed)
        
        # Émotion
        emo = EMOTION_PROFILES.get(emotion, EMOTION_PROFILES["neutre"])
        f0_shift, f0_range, emo_speed, timbre_mod, breath_mod, energy_mod, dur_mod, pause_mod = emo
        contour = EMOTION_F0_CONTOURS.get(emotion, EMOTION_F0_CONTOURS["neutre"])
        
        # Vitesse effective
        effective_speed = max(0.25, speed * emo_speed)
        
        # Construire les diphones avec modulation F0 par contour
        fragments = []
        n_diphones = len(phonemes) - 1
        
        for i in range(n_diphones):
            left = phonemes[i]
            right = phonemes[i + 1]
            
            # Position normalisée dans la phrase (0..1)
            pos_norm = i / max(n_diphones, 1)
            
            # F0 modulé par le contour émotionnel
            f0_mult = _interp_contour(contour, pos_norm)
            f0_target = f0 * f0_mult + f0_shift * 120.0
            
            # Durée cible (modifiée par prosodie + émotion)
            dur = 0.120 / effective_speed * dur_mod
            
            # Features cibles
            target = self._target_features(left, right, f0=f0_target, duration_s=dur)
            
            # Modulation émotion sur le timbre/énergie
            target[2] = np.clip(target[2] + energy_mod, 0.0, 1.0)
            target[8] = np.clip(target[8] + timbre_mod * 0.3, 0.0, 1.0)
            
            # Query KD-tree
            results = self.acoustic.query(target, k=3)
            if results:
                best_entry, _ = results[0]
                audio = best_entry.audio.copy()
            else:
                audio = np.zeros(int(dur * self.sr), dtype=np.float32)
            
            fragments.append(audio)
        
        # Concaténation
        audio = self._concatenate(fragments, overlap_ms=10)
        
        # Appliquer la signature vocale
        audio = self._apply_voice(audio, voice, f0)
        
        # Appliquer la breathiness de l'émotion (déterministe via rng)
        if abs(breath_mod) > 0.01:
            noise = rng.normal(0, 0.2, len(audio)).astype(np.float32)
            noise = np.diff(noise, prepend=noise[0])
            audio = audio * (1.0 - abs(breath_mod) * 0.5) + noise * max(0, breath_mod) * 0.3
        
        # Normalisation finale
        peak = np.max(np.abs(audio)) + 1e-10
        return (audio / peak * 0.95).astype(np.float32)

    def speak(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        emotion: str = "neutre",
        language: str = "fr",
    ) -> bytes:
        """Synthèse haut niveau : texte → WAV bytes avec header RIFF complet.
        
        Args:
            text : texte français
            voice : nom de voix (homme, femme, enfant, ou clonée)
            speed : vitesse (0.5=lent, 2.0=rapide)
            emotion : émotion (neutre, joyeux, triste, urgent, calme, ...)
            language : code langue (fr seulement pour l'instant)
        
        Returns:
            bytes WAV RIFF complet (header 44 octets + PCM 16-bit)
        """
        import io
        import wave as wavlib
        
        # G2P
        phonemes = simple_g2p(text)
        if not phonemes:
            phonemes = ["_"]
        
        # F0 selon la voix
        f0 = self._voice_f0(voice)
        
        # Synthèse
        audio = self.synthesize(phonemes, f0=f0, speed=speed, emotion=emotion, voice=voice)
        
        # Encodage WAV
        audio = np.clip(audio, -1.0, 1.0)
        pcm = (audio * 32767.0).astype("<i2")
        buf = io.BytesIO()
        with wavlib.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sr)
            w.writeframes(pcm.tobytes())
        return buf.getvalue()

    # ── Gestion des voix ────────────────────────────────────────────────

    def _voice_f0(self, voice: str) -> float:
        """Retourne la F0 de base pour une voix donnée."""
        sig = self._voices.get(voice)
        if sig is None:
            sig = self._voices.get(self._default_voice)
        if sig is None:
            return 120.0
        # pitch_mean [0,1] → Hz
        return 80.0 * math.exp(sig[0] * math.log(400.0 / 80.0))

    def _apply_voice(self, audio: np.ndarray, voice: str, base_f0: float) -> np.ndarray:
        """Applique la signature vocale (harmonique prioritaire, sinon 11D)."""
        if voice in ("default", "auto"):
            return audio
        
        # 1. Essayer le clonage harmonique (filtre spectral — meilleure qualité)
        if self._use_harmonic_clone and voice in self._voice_prints:
            try:
                from .harmonic_cloner import apply_voice_print
                return apply_voice_print(audio, self._voice_prints[voice], self.sr)
            except Exception:
                pass  # fallback ci-dessous
        
        # 2. Fallback : signature 11D (DSP classique)
        sig = self._voices.get(voice)
        if sig is None:
            return audio
        try:
            from .voice_signature import apply_signature
            seed = abs(hash(voice)) & 0x7FFFFFFF
            return apply_signature(audio.astype(np.float64), sig, self.sr, seed=seed)
        except ImportError:
            return audio

    def clone_voice(self, wav_path: str, name: str) -> bool:
        """Clone une voix depuis un fichier WAV (clonage harmonique prioritaire).
        
        Args:
            wav_path : chemin vers un WAV (3-30 secondes, mono ou stéréo)
            name : nom à donner à la voix clonée
        
        Returns:
            True si succès
        """
        try:
            # Priorité : clonage harmonique (filtre spectral)
            from .harmonic_cloner import extract_from_wav as harmonic_extract
            vp = harmonic_extract(wav_path)
            vp.source_name = wav_path
            self._voice_prints[name] = vp
            
            # Backup : signature 11D (DSP)
            from .voice_signature import extract_from_wav as sig_extract
            self._voices[name] = sig_extract(wav_path)
            
            return True
        except Exception as e:
            # Fallback : signature 11D seule
            try:
                from .voice_signature import extract_from_wav as sig_extract
                self._voices[name] = sig_extract(wav_path)
                return True
            except Exception:
                import logging
                logging.getLogger("ka_sonic.bridge").error(f"clone_voice failed: {e}")
                return False

    @property
    def voices(self) -> List[str]:
        return sorted(self._voices.keys())

    def _single_phoneme(self, phoneme: str, f0: float = 120.0) -> np.ndarray:
        """Synthèse d'un phonème isolé (entouré de silence)."""
        results = self.acoustic.query(
            self._target_features("_", phoneme, f0=f0), k=1,
        )
        if results:
            return results[0][0].audio.copy()
        return np.zeros(int(0.120 * self.sr), dtype=np.float32)

    def _concatenate(self, fragments: List[np.ndarray], overlap_ms: float = 10.0) -> np.ndarray:
        """Concatène des fragments audio avec crossfade cosinusoïdal."""
        if not fragments:
            return np.zeros(0, dtype=np.float32)
        if len(fragments) == 1:
            return fragments[0]
        
        ov = int(overlap_ms / 1000.0 * self.sr)
        if ov < 2:
            ov = 2
        
        total_len = sum(len(f) for f in fragments) - ov * (len(fragments) - 1)
        out = np.zeros(total_len, dtype=np.float32)
        norm = np.zeros(total_len, dtype=np.float32)
        
        pos = 0
        for f in fragments:
            L = len(f)
            win = np.hanning(L)  # fenêtre de Hann
            out[pos:pos + L] += f * win
            norm[pos:pos + L] += win
            pos += L - ov
        
        norm[norm < 1e-6] = 1.0
        result = out / norm
        
        # Normalisation finale
        peak = np.max(np.abs(result)) + 1e-10
        return (result / peak * 0.95).astype(np.float32)

    # ── Stats ──────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "bank_size": len(self._bank),
            "bank_built": self._bank_built,
            "acoustic": self.acoustic.stats(),
            "sr": self.sr,
        }


def _interp_contour(contour: List[Tuple[float, float]], pos: float) -> float:
    """Interpole linéairement dans un contour (pos ∈ [0,1])."""
    if not contour:
        return 1.0
    if pos <= contour[0][0]:
        return contour[0][1]
    if pos >= contour[-1][0]:
        return contour[-1][1]
    for i in range(len(contour) - 1):
        x0, y0 = contour[i]
        x1, y1 = contour[i + 1]
        if x0 <= pos <= x1:
            t = (pos - x0) / (x1 - x0 + 1e-10)
            return y0 + t * (y1 - y0)
    return 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# G2P simplifié (fallback sans espeak-ng)
# ═══════════════════════════════════════════════════════════════════════════════

from .phoneme_features import GRAPHEME_TO_PHONEME as _G2P

def simple_g2p(text: str) -> List[str]:
    """Phonémisation simplifiée du français (sans espeak-ng).
    
    Approche : règles de correspondance graphème→phonème + heuristiques
    pour les liaisons et élisions. Suffisant pour le prototype.
    
    Args:
        text : texte en français (minuscules, sans ponctuation excessive)
    
    Returns:
        liste de symboles phonétiques
    """
    text = text.lower().strip()
    # Supprimer la ponctuation sauf les apostrophes
    import re
    text = re.sub(r"[^\w\s']", "", text)
    
    # Découper en mots
    words = text.split()
    phonemes = []
    
    for wi, word in enumerate(words):
        if word in ("l'", "d'", "s'", "n'", "m'", "t'", "c'", "j'"):
            # Élision : rattacher au mot suivant
            continue
        
        # Essayer de phonémiser le mot
        word_ph = _phonemize_word(word, is_first=(wi == 0), is_last=(wi == len(words)-1))
        if phonemes and word_ph:
            phonemes.append("#")  # frontière de mot
        phonemes.extend(word_ph)
    
    return phonemes


def _phonemize_word(word: str, is_first: bool = False, is_last: bool = False) -> List[str]:
    """Phonémise un mot français simple."""
    if not word:
        return []
    
    phonemes = []
    i = 0
    while i < len(word):
        matched = False
        # Essayer les digrammes/trigrammes les plus longs d'abord
        for length in [4, 3, 2, 1]:
            if i + length <= len(word):
                chunk = word[i:i + length]
                if chunk in _G2P:
                    ph = _G2P[chunk]
                    # Ajouter chaque symbole (peut être multi-caractère comme "wɛ̃")
                    for p in ph if isinstance(ph, list) else [ph]:
                        # Simplifier : traiter les séquences comme des phonèmes uniques
                        pass
                    # Version simple : ajouter le mapping direct
                    result = _G2P[chunk]
                    # Si le résultat contient des phonèmes multiples (ex: "wa" → ["w", "a"])
                    if len(result) > 2 and result not in _G2P.values():
                        # Séquence complexe, ajouter caractère par caractère (approximation)
                        for ch in result:
                            if ch in PHONEME_FEATURES:
                                phonemes.append(ch)
                    else:
                        if result in PHONEME_FEATURES:
                            phonemes.append(result)
                        else:
                            # Fallback
                            for ch in chunk:
                                if ch in _G2P and _G2P[ch] in PHONEME_FEATURES:
                                    phonemes.append(_G2P[ch])
                    i += length
                    matched = True
                    break
        if not matched:
            i += 1  # ignorer le caractère inconnu
    
    return phonemes
