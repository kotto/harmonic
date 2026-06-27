"""
HarmonicVoiceTrainer — Entraîneur de Décodeur Vocal Harmonique
===============================================================
Entraîne un modèle de mapping SpectralMessage → paramètres vocaux,
puis synthétise l'audio via un vocodeur (HiFi-GAN φ-spaced ou Edge-TTS).

Architecture :
    1. SpectralMessage (signature 11D sémantique)
       → 2. Paramètres vocaux 11D (pitch, timbre, vitesse…)
       → 3. Fichier audio (WAV/MP3)

Fonctionnement :
    - Phase d'entraînement : apprend le mapping SpectralMessage → paramètres vocaux
      à partir d'un dataset de paires (SpectralMessage, VoiceSignature 11D)
    - Phase d'inférence : synthétise l'audio correspondant à un SpectralMessage
      en appliquant un profil vocal cible

Synergie avec l'existant :
    - reçoit les SpectralMessages de harmonic_resonator.py
    - utilise les signatures 11D de voice_signature_extractor.py
    - peut être optimisé par recursive_learner.py

Usage :
    trainer = HarmonicVoiceTrainer()
    trainer.load_profiles()  # Charge les profils de référence
    audio = trainer.synthesize(spectral_message, voice_profile="lj_speech_female_us")
"""

import math
import os
import json
import tempfile
import subprocess
import shutil
import hashlib
from typing import Dict, Optional, Tuple, List, Any
from pathlib import Path
import numpy as np

# =========================================================================
# CONSTANTES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # ≈ 0.618
PHI_SQ = PHI * PHI

# Dimensions du mapping SpectralMessage → Paramètres vocaux
# Les 11 dimensions sémantiques → 11 paramètres vocaux
MAPPING_DIMENSIONS = {
    'phi': 'H_pitch_mean',        # φ → f₀ de base
    'alpha': 'H_speed',           # α (amplitude) → débit
    'reasoning': 'H_clarity',     # Raisonnement → clarté articulatoire
    'creativity': 'H_emotion_range',  # Créativité → plage expressive
    'math': 'H_resonance',        # Math → résonance (structure)
    'factual': 'H_pause_pattern', # Factuel → pattern de pauses
    'code': 'H_timbre',           # Code → timbre (précision)
    'emotion': 'H_breathiness',   # Émotion → breathiness (expressivité)
    'temporal': 'H_pitch_range',  # Temporel → variation de hauteur
    'coherence': 'H_phi_alignment',  # Cohérence → alignement φ
    'resonance': 'H_naturalness', # Résonance → naturalité
}

# Noms des dimensions sémantiques (dans l'ordre de signatures_11d.py)
SEMANTIC_DIM_NAMES = [
    'phi', 'alpha', 'reasoning', 'creativity', 'math',
    'factual', 'code', 'emotion', 'temporal', 'coherence', 'resonance',
]

# Noms des dimensions vocales (dans l'ordre de voice_signature_extractor.py)
VOICE_DIM_NAMES = [
    'H_pitch_mean', 'H_pitch_range', 'H_speed', 'H_timbre',
    'H_breathiness', 'H_resonance', 'H_emotion_range', 'H_clarity',
    'H_pause_pattern', 'H_phi_alignment', 'H_naturalness',
]


# =========================================================================
# MODÈLE DE MAPPING SPECTRAL → VOCAL
# =========================================================================

class SpectralToVoiceMapper:
    """
    Modèle léger de mapping SpectralMessage (11D sémantique) → Paramètres vocaux (11D).

    Utilise une matrice de transformation [11×11] apprise par régression
    linéaire φ-régularisée. Poids total < 50 MB.

    Le mapping est initialisé avec la matrice d'identité (1:1 direct)
    puis affiné par entraînement sur paires (SpectralMessage, VoiceSignature).
    """

    def __init__(self):
        # Matrice de transformation [11, 11]
        # Initialisation : identité + perturbations φ
        self.W = np.eye(11) * PHI_INV  # Diagonale pondérée φ⁻¹

        # Les dimensions croisées sont initialisées à φ⁻³ (très faible)
        for i in range(11):
            for j in range(11):
                if i != j:
                    # Couplages φ-espacement : plus la distance est grande,
                    # plus le couplage est faible
                    dist = abs(i - j)
                    self.W[i, j] = (PHI_INV ** (dist + 2)) * (0.1 if (i + j) % 2 == 0 else -0.05)

        # Biais
        self.b = np.zeros(11)

        # Normalisation de la matrice
        self._normalize_weights()

    def _normalize_weights(self):
        """Normalise les poids pour que la somme par ligne ≈ 1."""
        row_sums = np.sum(np.abs(self.W), axis=1, keepdims=True)
        row_sums = np.maximum(row_sums, 1e-8)
        self.W = self.W / row_sums

    def forward(self, spectral_11d: np.ndarray) -> np.ndarray:
        """
        Transforme une signature sémantique 11D en paramètres vocaux 11D.

        Args:
            spectral_11d: np.ndarray [11] ou [batch, 11]

        Returns:
            voice_params: np.ndarray [11] ou [batch, 11] normalisé [0, 1]
        """
        x = np.atleast_2d(spectral_11d)  # [batch, 11]
        y = x @ self.W + self.b
        y = np.clip(y, 0.0, 1.0)

        if spectral_11d.ndim == 1:
            return y[0]
        return y

    def train_step(self, spectral_batch: np.ndarray,
                   voice_batch: np.ndarray,
                   learning_rate: float = 0.01) -> float:
        """
        Une étape d'entraînement : régression linéaire avec régularisation φ.

        Args:
            spectral_batch: [N, 11] signatures sémantiques
            voice_batch: [N, 11] signatures vocales cibles
            learning_rate: taux d'apprentissage

        Returns:
            loss: erreur quadratique moyenne de cette étape
        """
        N = spectral_batch.shape[0]

        # Forward
        y_pred = spectral_batch @ self.W + self.b  # [N, 11]

        # Erreur
        error = y_pred - voice_batch  # [N, 11]

        # Gradient
        dW = spectral_batch.T @ error / N  # [11, 11]
        db = np.mean(error, axis=0)  # [11]

        # Régularisation φ : pénaliser les poids hors-diagonale
        # pour maintenir la structure (préserver le mapping direct)
        reg = np.zeros_like(self.W)
        for i in range(11):
            for j in range(11):
                if i != j:
                    reg[i, j] = PHI_INV * 0.1 * self.W[i, j]

        # Mise à jour
        self.W -= learning_rate * (dW + reg)
        self.b -= learning_rate * db

        # Clip pour stabilité
        self.W = np.clip(self.W, -2.0, 2.0)
        self.b = np.clip(self.b, -0.5, 0.5)

        self._normalize_weights()

        # Loss
        loss = float(np.mean(error ** 2))
        return loss

    def save(self, filepath: str):
        """Sauvegarde le modèle."""
        np.savez(filepath, W=self.W, b=self.b)

    def load(self, filepath: str):
        """Charge le modèle."""
        data = np.load(filepath)
        self.W = data['W']
        self.b = data['b']

    def get_weights_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des poids pour debugging."""
        return {
            'W_shape': list(self.W.shape),
            'W_mean': float(np.mean(self.W)),
            'W_std': float(np.std(self.W)),
            'W_max_off_diag': float(np.max(np.abs(self.W - np.diag(np.diag(self.W))))),
            'b_mean': float(np.mean(self.b)),
            'diagonal': [float(self.W[i, i]) for i in range(11)],
        }


# =========================================================================
# ENTRAÎNEUR VOCAL HARMONIQUE
# =========================================================================

class HarmonicVoiceTrainer:
    """
    Entraîneur du décodeur vocal harmonique.

    Combine :
    - Le mapping SpectralMessage → paramètres vocaux (SpectralToVoiceMapper)
    - La synthèse audio via Edge-TTS (rôle du vocodeur pour le prototype)
    - L'application de profils vocaux de référence

    Usage :
        trainer = HarmonicVoiceTrainer()
        trainer.load_profiles()
        audio_data = trainer.synthesize(spectral_message, voice_profile="lj_speech_female_us")
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Args:
            model_path: Chemin vers le modèle entraîné (fichier .npz)
        """
        self.mapper = SpectralToVoiceMapper()

        if model_path and os.path.exists(model_path):
            self.mapper.load(model_path)
            print(f"[HarmonicVoiceTrainer] Modèle chargé depuis {model_path}")

        # Banque de profils vocaux
        self.voice_profiles: Dict[str, np.ndarray] = {}

        # Profil par défaut (φ-neutre)
        self.default_profile = np.full(11, PHI_INV)
        self.default_profile[4] = PHI_INV ** 3   # H_breathiness bas
        self.default_profile[7] = 0.75            # H_clarity bon
        self.default_profile[10] = 0.78           # H_naturalness

        # Disponibilité Edge-TTS
        self._edge_tts_available = bool(shutil.which("edge-tts"))

        if not self._edge_tts_available:
            print("[HarmonicVoiceTrainer] ⚠ edge-tts non trouvé. pip install edge-tts")

    # -----------------------------------------------------------------
    # GESTION DES PROFILS
    # -----------------------------------------------------------------

    def load_profiles(self, profiles_dict: Optional[Dict[str, np.ndarray]] = None):
        """
        Charge les profils vocaux de référence.

        Args:
            profiles_dict: Dict {nom: array[11]} ou None pour charger
                          les profils depuis voice_signature_extractor.py
        """
        if profiles_dict:
            self.voice_profiles = profiles_dict
            return

        # Charger depuis le module voice_signature_extractor
        try:
            from engine.voice_signature_extractor import REFERENCE_PROFILES
            for name, sig in REFERENCE_PROFILES.items():
                self.voice_profiles[name] = sig.to_array()
            print(f"[HarmonicVoiceTrainer] {len(self.voice_profiles)} profils chargés "
                  f"depuis voice_signature_extractor")
        except ImportError:
            print("[HarmonicVoiceTrainer] ⚠ voice_signature_extractor non trouvé. "
                  "Profils par défaut uniquement.")
            self.voice_profiles["default"] = self.default_profile

    def add_profile(self, name: str, voice_array: np.ndarray):
        """Ajoute un profil vocal."""
        if voice_array.shape != (11,):
            raise ValueError(f"Le profil doit être un array [11], reçu {voice_array.shape}")
        self.voice_profiles[name] = voice_array

    def get_profile(self, name: str) -> np.ndarray:
        """Récupère un profil vocal par son nom."""
        if name in self.voice_profiles:
            return self.voice_profiles[name].copy()
        if name == "default" or name not in self.voice_profiles:
            return self.default_profile.copy()
        return self.default_profile.copy()

    def list_profiles(self) -> List[str]:
        """Liste les profils disponibles."""
        return sorted(self.voice_profiles.keys())

    # -----------------------------------------------------------------
    # MAPPING SPECTRAL → VOCAL
    # -----------------------------------------------------------------

    def spectral_to_voice(self, spectral_11d: np.ndarray,
                          voice_profile: str = "default") -> np.ndarray:
        """
        Convertit un SpectralMessage 11D en paramètres vocaux 11D,
        en appliquant le profil vocal spécifié.

        Args:
            spectral_11d: Signature sémantique 11D [11]
            voice_profile: Nom du profil vocal ou "default"

        Returns:
            voice_params: Paramètres vocaux 11D normalisés [0, 1]
        """
        # Mapping de base via le modèle entraîné
        base_voice = self.mapper.forward(spectral_11d)

        # Récupérer le profil cible
        profile = self.get_profile(voice_profile)

        # Fusionner : 60% profil cible + 40% mapping spectral
        # La fusion utilise φ pour préserver l'identité du locuteur
        # tout en modulant l'expressivité selon le contenu
        fusion_weight = PHI_INV  # 0.618 — poids du profil (identité forte)

        # Modulation émotionnelle : les dimensions liées à l'émotion
        # (H_breathiness idx 4, H_emotion_range idx 6, H_pitch_range idx 1)
        # sont davantage influencées par le contenu spectral
        voice_params = fusion_weight * profile + (1.0 - fusion_weight) * base_voice

        # Ajuster les dimensions expressives en fonction du contenu
        # H_emotion_range (idx 6) : booster si le SpectralMessage a une forte
        # dimension 'emotion' ou 'creativity'
        emotion_boost = (spectral_11d[7] + spectral_11d[3]) / 2.0  # emotion + creativity
        voice_params[6] = voice_params[6] * 0.7 + emotion_boost * 0.3

        # H_speed (idx 2) : moduler selon l'urgence temporelle
        temporal_factor = spectral_11d[8]  # temporal
        voice_params[2] = voice_params[2] * 0.6 + temporal_factor * 0.4

        # H_pitch_range (idx 1) : moduler selon l'émotion et la créativité
        voice_params[1] = voice_params[1] * 0.65 + emotion_boost * 0.35

        return np.clip(voice_params, 0.0, 1.0)

    def get_voice_params_for_tts(self, voice_params: np.ndarray,
                                 voice_name: str = "default") -> Dict[str, float]:
        """
        Convertit les paramètres vocaux 11D en paramètres exploitables
        par un moteur TTS (Edge-TTS, Piper, etc.).

        Returns:
            Dict avec :
            - 'rate': vitesse de parole (pitch relatif en %)
            - 'pitch': hauteur relative (Hz shift)
            - 'volume': volume
            - 'style': style vocal pour Edge-TTS
        """
        # H_speed (idx 2) → rate
        # Edge-TTS rate : -50% à +50%
        rate = int((voice_params[2] - 0.5) * 100)  # -50 à +50
        rate = max(-50, min(50, rate))

        # H_pitch_mean (idx 0) → pitch shift
        # Edge-TTS pitch : -20Hz à +20Hz
        pitch_shift = int((voice_params[0] - 0.618) * 60)  # -20 à +23
        pitch_shift = max(-20, min(20, pitch_shift))

        # H_breathiness (idx 4) → style
        # Style : "whispering" si breathiness > 0.4, sinon "general"
        style = "whispering" if voice_params[4] > 0.4 else "general"

        # H_naturalness (idx 10) → volume adjustment
        volume = max(50, min(200, int(voice_params[10] * 200)))

        return {
            'rate': f"{rate:+d}%",
            'pitch': f"{pitch_shift:+d}Hz",
            'volume': volume,
            'style': style,
        }

    # -----------------------------------------------------------------
    # SYNTHÈSE VOCALE
    # -----------------------------------------------------------------

    def synthesize(self, spectral_message: np.ndarray,
                   voice_profile: str = "default",
                   output_path: Optional[str] = None) -> Tuple[bytes, str]:
        """
        Synthétise l'audio correspondant à un SpectralMessage.

        Pipeline :
            1. SpectralMessage (11D sémantique)
            2. → Paramètres vocaux (11D) via le mapper
            3. → Texte à synthétiser (via le SpectralProblem original ou fallback)
            4. → Audio via Edge-TTS

        Args:
            spectral_message: Signature 11D du SpectralMessage [11]
            voice_profile: Nom du profil vocal
            output_path: Chemin de sortie optionnel pour le fichier audio

        Returns:
            (audio_bytes, output_path) — bytes du MP3 + chemin du fichier
        """
        # Étape 1 : SpectralMessage → Paramètres vocaux
        voice_params = self.spectral_to_voice(spectral_message, voice_profile)

        # Étape 2 : Paramètres vocaux → Paramètres TTS
        tts_params = self.get_voice_params_for_tts(voice_params, voice_profile)

        # Étape 3 : Synthèse via Edge-TTS
        audio_bytes, actual_path = self._synthesize_edge_tts(
            text=tts_params.get('text', ''),
            rate=tts_params['rate'],
            pitch=tts_params['pitch'],
            volume=tts_params['volume'],
            output_path=output_path,
        )

        return audio_bytes, actual_path

    def synthesize_from_text(self, text: str,
                             spectral_message: Optional[np.ndarray] = None,
                             voice_profile: str = "default",
                             output_path: Optional[str] = None) -> Tuple[bytes, str]:
        """
        Synthétise du texte en audio avec modulation vocale harmonique.

        Si spectral_message est fourni, il module la voix.
        Sinon, utilise le profil vocal tel quel.

        Args:
            text: Texte à synthétiser
            spectral_message: Signature sémantique 11D optionnelle
            voice_profile: Nom du profil vocal
            output_path: Chemin de sortie optionnel

        Returns:
            (audio_bytes, output_path)
        """
        # Profil de base
        profile = self.get_profile(voice_profile)

        if spectral_message is not None:
            # Moduler le profil avec le contenu spectral
            voice_params = self.spectral_to_voice(spectral_message, voice_profile)
        else:
            # Utiliser le profil tel quel
            voice_params = profile

        # Paramètres TTS
        tts_params = self.get_voice_params_for_tts(voice_params, voice_profile)

        # Synthèse
        audio_bytes, actual_path = self._synthesize_edge_tts(
            text=text,
            rate=tts_params['rate'],
            pitch=tts_params['pitch'],
            volume=tts_params['volume'],
            output_path=output_path,
        )

        return audio_bytes, actual_path

    def _synthesize_edge_tts(self, text: str, rate: str = "+0%",
                             pitch: str = "+0Hz", volume: int = 100,
                             output_path: Optional[str] = None) -> Tuple[bytes, str]:
        """
        Synthèse vocale via Edge-TTS avec paramètres vocaux modulés.
        """
        if not text:
            return b'', ''

        # Voix française par défaut
        voice = "fr-FR-DeniseNeural"

        # Créer un fichier temporaire si pas de output_path
        if output_path:
            out_path = output_path
            use_temp = False
        else:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.close()
            out_path = tmp.name
            use_temp = True

        if not self._edge_tts_available:
            # Fallback : fichier vide avec message
            print("[HarmonicVoiceTrainer] Edge-TTS non disponible.")
            if use_temp:
                os.unlink(out_path)
            return b'', ''

        # Commande Edge-TTS avec paramètres vocaux
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--rate", rate,
            "--pitch", pitch,
            "--write-media", out_path,
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                print(f"[HarmonicVoiceTrainer] Edge-TTS erreur: {proc.stderr}")
                if use_temp and os.path.exists(out_path):
                    os.unlink(out_path)
                return b'', ''

            # Lire le fichier
            with open(out_path, 'rb') as f:
                audio_bytes = f.read()

            if use_temp:
                os.unlink(out_path)
                return audio_bytes, ''

            return audio_bytes, out_path

        except subprocess.TimeoutExpired:
            print("[HarmonicVoiceTrainer] Edge-TTS timeout")
            if use_temp and os.path.exists(out_path):
                os.unlink(out_path)
            return b'', ''
        except Exception as e:
            print(f"[HarmonicVoiceTrainer] Erreur: {e}")
            if use_temp and os.path.exists(out_path):
                os.unlink(out_path)
            return b'', ''

    # -----------------------------------------------------------------
    # ENTRAÎNEMENT
    # -----------------------------------------------------------------

    def train(self, dataset: List[Tuple[np.ndarray, np.ndarray]],
              epochs: int = 100, learning_rate: float = 0.01,
              verbose: bool = True) -> List[float]:
        """
        Entraîne le mapper SpectralMessage → Paramètres vocaux.

        Args:
            dataset: Liste de paires (spectral_11d, voice_11d)
            epochs: Nombre d'époques
            learning_rate: Taux d'apprentissage
            verbose: Afficher la progression

        Returns:
            losses: Historique des pertes par époque
        """
        if len(dataset) < 10:
            print("[HarmonicVoiceTrainer] Dataset trop petit (< 10), entraînement ignoré.")
            return []

        X = np.array([d[0] for d in dataset])
        Y = np.array([d[1] for d in dataset])

        losses = []

        for epoch in range(epochs):
            # Shuffle
            indices = np.random.permutation(len(X))
            X_shuffled = X[indices]
            Y_shuffled = Y[indices]

            # Mini-batch
            batch_size = min(32, len(X))
            epoch_losses = []

            for i in range(0, len(X), batch_size):
                X_batch = X_shuffled[i:i + batch_size]
                Y_batch = Y_shuffled[i:i + batch_size]

                loss = self.mapper.train_step(X_batch, Y_batch, learning_rate)
                epoch_losses.append(loss)

            mean_loss = float(np.mean(epoch_losses))
            losses.append(mean_loss)

            if verbose and epoch % 20 == 0:
                print(f"  Epoch {epoch:4d}/{epochs} — loss: {mean_loss:.6f}")

        if verbose:
            print(f"[HarmonicVoiceTrainer] Entraînement terminé — "
                  f"loss finale: {losses[-1]:.6f}")

        return losses

    def train_from_signatures_json(self, signatures_json_path: str,
                                   epochs: int = 100,
                                   learning_rate: float = 0.01) -> List[float]:
        """
        Entraîne le mapper à partir d'un fichier JSON de signatures vocales.

        Le SpectralMessage est généré aléatoirement pour l'entraînement initial.
        Dans une version avancée, on utiliserait les vrais SpectralMessages
        associés aux énoncés.
        """
        with open(signatures_json_path, 'r', encoding='utf-8') as f:
            signatures_data = json.load(f)

        dataset = []
        for entry in signatures_data:
            if 'signature_11d' not in entry:
                continue

            # Signature vocale (cible)
            voice_sig = np.array([
                entry['signature_11d'][dim]
                for dim in VOICE_DIM_NAMES
            ])

            # Signature spectrale simulée (pour prototype)
            # Dans la version finale, on extrairait le vrai SpectralMessage
            # correspondant au texte de l'énoncé
            spectral_sig = self._simulate_spectral_from_voice(voice_sig)

            dataset.append((spectral_sig, voice_sig))

        return self.train(dataset, epochs, learning_rate)

    def _simulate_spectral_from_voice(self, voice_sig: np.ndarray) -> np.ndarray:
        """
        Simule une signature spectrale à partir d'une signature vocale.
        Utilisé pour le prototypage en attendant le dataset apparié réel.

        Le mapping inversé approximatif : H_vocal → H_semantic
        Utilise la matrice de mapping en sens inverse avec bruit φ.
        """
        # Inversion approximative de la matrice de mapping
        try:
            W_inv = np.linalg.pinv(self.mapper.W)
            spectral = voice_sig @ W_inv.T
        except np.linalg.LinAlgError:
            spectral = voice_sig.copy()

        # Ajouter du bruit φ (petite perturbation pour robustesse)
        noise = np.random.normal(0, 0.02, size=spectral.shape)
        spectral = spectral + noise

        return np.clip(spectral, 0.0, 1.0)

    # -----------------------------------------------------------------
    # OPTIMISATION PAR RÉSONANCE (synergie avec recursive_learner.py)
    # -----------------------------------------------------------------

    def apply_resonance_optimization(self, adjustment_params: Dict[str, float]):
        """
        Applique les ajustements de paramètres provenant du MetaLearningLoop
        (recursive_learner.py) pour améliorer la qualité vocale.

        Args:
            adjustment_params: Dict de paramètres ajustés
        """
        # Ajuster les poids diagonaux de la matrice selon les paramètres
        if 'creativity_boost' in adjustment_params:
            # Plus de créativité = plus de couplage hors-diagonal
            boost = adjustment_params['creativity_boost']
            for i in range(11):
                for j in range(11):
                    if i != j:
                        dist = abs(i - j)
                        self.mapper.W[i, j] += boost * (PHI_INV ** (dist + 3))

        if 'coherence_threshold' in adjustment_params:
            # Ajuster la diagonale (force du mapping direct)
            delta = adjustment_params['coherence_threshold'] - PHI_INV
            for i in range(11):
                self.mapper.W[i, i] += delta * 0.1

        if 'emotional_sensitivity' in adjustment_params:
            # Ajuster les couplages liés à l'émotion (dimensions 7, 3)
            sensitivity = adjustment_params['emotional_sensitivity']
            for i in [7, 3]:  # emotion, creativity
                for j in [1, 6]:  # pitch_range, emotion_range
                    if i != j:
                        self.mapper.W[i, j] += (sensitivity - 0.5) * 0.05

        self.mapper._normalize_weights()

    def save_model(self, filepath: str):
        """Sauvegarde le modèle entraîné."""
        self.mapper.save(filepath)
        print(f"[HarmonicVoiceTrainer] Modèle sauvegardé dans {filepath}")

    def load_model(self, filepath: str):
        """Charge un modèle entraîné."""
        if os.path.exists(filepath):
            self.mapper.load(filepath)
            print(f"[HarmonicVoiceTrainer] Modèle chargé depuis {filepath}")
        else:
            print(f"[HarmonicVoiceTrainer] ⚠ Fichier modèle introuvable: {filepath}")


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST HarmonicVoiceTrainer — Décodeur Vocal Harmonique")
    print("=" * 60)

    trainer = HarmonicVoiceTrainer()

    # Test 1 : Chargement des profils
    trainer.load_profiles()
    print(f"\nProfils disponibles: {trainer.list_profiles()}")
    print(f"Profil par défaut: {trainer.default_profile}")

    # Test 2 : Mapping SpectralMessage → Paramètres vocaux
    spectral_msg = np.array([
        PHI_INV,      # phi
        0.5,           # alpha
        0.7,           # reasoning
        0.6,           # creativity
        0.3,           # math
        0.55,          # factual
        0.2,           # code
        0.8,           # emotion (forte émotion)
        0.65,          # temporal
        PHI_INV,      # coherence
        0.618,         # resonance
    ])

    print(f"\nSpectralMessage test : {spectral_msg.round(3)}")

    voice_params = trainer.spectral_to_voice(spectral_msg, voice_profile="default")
    print(f"\nParamètres vocaux résultants [0-1] :")
    for i, name in enumerate(VOICE_DIM_NAMES):
        val = voice_params[i]
        bar = "█" * int(val * 40)
        print(f"  {name:>18}: {val:.4f} {bar}")

    # Test 3 : Paramètres TTS
    tts_params = trainer.get_voice_params_for_tts(voice_params)
    print(f"\nParamètres TTS : {tts_params}")

    # Test 4 : Entraînement simulé
    print(f"\n--- Test entraînement simulé ---")
    np.random.seed(42)
    X_sim = np.random.rand(50, 11)  # 50 SpectralMessages simulés
    Y_sim = np.random.rand(50, 11)  # 50 signatures vocales simulées

    dataset = [(X_sim[i], Y_sim[i]) for i in range(50)]
    losses = trainer.train(dataset, epochs=40, learning_rate=0.005)
    print(f"\nHistorique des pertes: [{losses[0]:.6f} → {losses[-1]:.6f}]")
    print(f"Résumé des poids: {trainer.mapper.get_weights_summary()}")

    # Test 5 : Synthèse avec Edge-TTS (si dispo)
    if trainer._edge_tts_available:
        print(f"\n--- Test synthèse Edge-TTS ---")
        audio_bytes, path = trainer.synthesize_from_text(
            text="Bonjour, je suis l'assistant vocal harmonique. Comment puis-je vous aider ?",
            spectral_message=spectral_msg,
            voice_profile="default",
        )
        if audio_bytes:
            print(f"  ✓ Audio généré : {len(audio_bytes)} octets")
            # Sauvegarder le test
            test_path = "test_harmonic_voice_output.mp3"
            if not path:
                with open(test_path, 'wb') as f:
                    f.write(audio_bytes)
                print(f"  ✓ Fichier sauvegardé : {test_path}")
        else:
            print(f"  ⚠ Synthèse échouée (Edge-TTS peut ne pas être installé)")
    else:
        print(f"\n⚠ Edge-TTS non disponible — pas de test de synthèse")

    print("\n" + "=" * 60)