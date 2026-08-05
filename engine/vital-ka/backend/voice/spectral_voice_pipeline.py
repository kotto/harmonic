"""
SpectralVoicePipeline — Pipeline Complet de Synthèse Vocale Harmonique
======================================================================
Intègre l'extraction de signatures vocales, l'entraînement du décodeur,
et l'interface de synthèse pour tts_server.py.

Architecture :
    User Message
        │
        ▼
    HarmonicResonator (Couche 0) → SpectralMessage 11D
        │
        ├──→ Décodeur Texte → TEXTE AFFICHÉ
        │
        └──→ SpectralVoicePipeline → AUDIO (WAV/MP3)
                 │
                 ├── VoiceSignatureExtractor (analyse de voix)
                 ├── HarmonicVoiceTrainer (mapping + synthèse)
                 └── Profils vocaux de référence (6 profils)

Point d'entrée principal pour l'intégration :
    pipeline = SpectralVoicePipeline()
    audio_bytes = pipeline.synthesize(spectral_message_11d, voice="lj_speech_female_us")

Intégration avec tts_server.py :
    - Nouvelle route : POST /speak_spectral avec SpectralMessage JSON
    - Remplace l'ancienne interface : tts_server.synthesize(text="...", voice="default")
    - Par : tts_server.synthesize(spectral_message=msg, voice="default")

Usage :
    from engine.spectral_voice_pipeline import SpectralVoicePipeline

    pipeline = SpectralVoicePipeline()
    pipeline.initialize()  # Charge les profils + modèle

    # Synthèse depuis un SpectralMessage
    audio = pipeline.synthesize(spectral_11d, voice="lj_speech_female_us")

    # Synthèse depuis un SpectralProblem (HarmonicResonator)
    audio = pipeline.synthesize_from_problem(spectral_problem, "default")
"""

import math
import os
import json
import time
from typing import Dict, Optional, Tuple, List, Any
from pathlib import Path
import numpy as np

# =========================================================================
# CONSTANTES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI

# Configuration par défaut
DEFAULT_MODEL_DIR = Path("models/voice")
DEFAULT_SIGNATURES_DIR = Path("data/voice_signatures")
DEFAULT_OUTPUT_DIR = Path("data/voice_output")

# Mapping émotion SpectralMessage → ajustement vocal
# Chaque dimension sémantique module des paramètres vocaux spécifiques
EMOTION_TO_VOICE_MODULATION = {
    'neutre':      {'speed_factor': 1.0, 'pitch_factor': 1.0, 'breath_add': 0.0},
    'joyeux':      {'speed_factor': 1.15, 'pitch_factor': 1.1, 'breath_add': -0.05},
    'triste':      {'speed_factor': 0.85, 'pitch_factor': 0.9, 'breath_add': 0.1},
    'urgent':      {'speed_factor': 1.4, 'pitch_factor': 1.05, 'breath_add': -0.1},
    'calme':       {'speed_factor': 0.9, 'pitch_factor': 0.95, 'breath_add': 0.05},
    'autoritaire': {'speed_factor': 0.95, 'pitch_factor': 1.0, 'breath_add': -0.15},
    'doux':        {'speed_factor': 0.88, 'pitch_factor': 0.92, 'breath_add': 0.08},
    'excité':      {'speed_factor': 1.3, 'pitch_factor': 1.15, 'breath_add': -0.08},
}


# =========================================================================
# PIPELINE VOCAL SPECTRAL
# =========================================================================

class SpectralVoicePipeline:
    """
    Pipeline complet de synthèse vocale pilotée par SpectralMessage.

    Orchestre :
    1. L'extraction de signatures vocales (VoiceSignatureExtractor)
    2. L'entraînement du décodeur (HarmonicVoiceTrainer)
    3. La synthèse audio avec modulation harmonique

    C'est le point d'entrée unifié pour toute synthèse vocale.
    """

    def __init__(self,
                 model_dir: str = str(DEFAULT_MODEL_DIR),
                 signatures_dir: str = str(DEFAULT_SIGNATURES_DIR),
                 output_dir: str = str(DEFAULT_OUTPUT_DIR)):
        """
        Args:
            model_dir: Répertoire pour les modèles entraînés
            signatures_dir: Répertoire pour les signatures vocales extraites
            output_dir: Répertoire pour les fichiers audio générés
        """
        self.model_dir = Path(model_dir)
        self.signatures_dir = Path(signatures_dir)
        self.output_dir = Path(output_dir)

        # Créer les répertoires
        for d in [self.model_dir, self.signatures_dir, self.output_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Composants (initialisés paresseusement)
        self._extractor = None
        self._trainer = None
        self._initialized = False

        # Statistiques
        self.stats = {
            'total_synthesized': 0,
            'total_extracted': 0,
            'total_trained_epochs': 0,
            'avg_synthesis_time_ms': 0,
            'last_error': None,
        }

        # Cache des signatures extraites
        self._signature_cache: Dict[str, np.ndarray] = {}

    # -----------------------------------------------------------------
    # INITIALISATION
    # -----------------------------------------------------------------

    def initialize(self, load_profiles: bool = True,
                   load_model: bool = True) -> 'SpectralVoicePipeline':
        """
        Initialise le pipeline : charge les profils vocaux et le modèle.

        Returns:
            self (fluent interface)
        """
        # Initialiser le trainer
        from engine.harmonic_voice_trainer import HarmonicVoiceTrainer
        model_path = str(self.model_dir / "spectral_voice_mapper.npz")

        self._trainer = HarmonicVoiceTrainer(model_path=model_path if load_model else None)

        if load_profiles:
            self._trainer.load_profiles()

        # Initialiser l'extractor
        from engine.voice_signature_extractor import VoiceSignatureExtractor
        self._extractor = VoiceSignatureExtractor()

        self._initialized = True
        return self

    @property
    def trainer(self):
        """Accès paresseux au trainer."""
        if self._trainer is None:
            from engine.harmonic_voice_trainer import HarmonicVoiceTrainer
            model_path = str(self.model_dir / "spectral_voice_mapper.npz")
            self._trainer = HarmonicVoiceTrainer(model_path=model_path)
            self._trainer.load_profiles()
        return self._trainer

    @property
    def extractor(self):
        """Accès paresseux à l'extractor."""
        if self._extractor is None:
            from engine.voice_signature_extractor import VoiceSignatureExtractor
            self._extractor = VoiceSignatureExtractor()
        return self._extractor

    # -----------------------------------------------------------------
    # SYNTHÈSE VOCALE (POINT D'ENTRÉE PRINCIPAL)
    # -----------------------------------------------------------------

    def synthesize(self, spectral_message: np.ndarray,
                   voice: str = "default",
                   text: Optional[str] = None,
                   output_path: Optional[str] = None) -> bytes:
        """
        POINT D'ENTRÉE PRINCIPAL — Synthétise l'audio depuis un SpectralMessage.

        Args:
            spectral_message: Signature 11D du SpectralMessage [11]
            voice: Nom du profil vocal ("lj_speech_female_us", "vctk_p225_male_uk", etc.)
            text: Texte optionnel (si non fourni, génération à partir du SpectralMessage)
            output_path: Chemin de sortie optionnel

        Returns:
            audio_bytes: Données audio MP3
        """
        t_start = time.time()

        try:
            # Si pas de texte fourni, le SpectralMessage pilote entièrement la synthèse
            if text is None:
                text = self._decode_spectral_to_text(spectral_message)

            # Synthèse via le trainer
            audio_bytes, actual_path = self.trainer.synthesize_from_text(
                text=text,
                spectral_message=spectral_message,
                voice_profile=voice,
                output_path=output_path,
            )

            # Mettre à jour les stats
            elapsed_ms = (time.time() - t_start) * 1000
            self.stats['total_synthesized'] += 1
            n = self.stats['total_synthesized']
            self.stats['avg_synthesis_time_ms'] = (
                (self.stats['avg_synthesis_time_ms'] * (n - 1) + elapsed_ms) / n
            )

            return audio_bytes

        except Exception as e:
            self.stats['last_error'] = str(e)
            print(f"[SpectralVoicePipeline] Erreur synthèse: {e}")
            return b''

    def synthesize_from_problem(self, spectral_problem,
                                voice: str = "default",
                                output_path: Optional[str] = None) -> bytes:
        """
        Synthétise l'audio depuis un SpectralProblem (sortie du HarmonicResonator).

        Args:
            spectral_problem: SpectralProblem avec harmonics, reasoning_types, etc.
            voice: Nom du profil vocal
            output_path: Chemin de sortie optionnel

        Returns:
            audio_bytes: Données audio MP3
        """
        # Convertir le SpectralProblem en signature 11D
        spectral_11d = self._problem_to_spectral_11d(spectral_problem)

        # Utiliser le texte du problème
        text = spectral_problem.raw_text if hasattr(spectral_problem, 'raw_text') else None

        return self.synthesize(spectral_11d, voice=voice, text=text, output_path=output_path)

    def synthesize_from_text(self, text: str,
                             emotion: str = "neutre",
                             voice: str = "default",
                             output_path: Optional[str] = None) -> bytes:
        """
        Synthétise du texte avec modulation émotionnelle (sans SpectralMessage).

        Utile pour l'API simple : GET /speak?text=...&emotion=joyeux&voice=...

        Args:
            text: Texte à synthétiser
            emotion: Émotion ("neutre", "joyeux", "triste", "urgent", ...)
            voice: Nom du profil vocal
            output_path: Chemin de sortie optionnel

        Returns:
            audio_bytes: Données audio MP3
        """
        # Construire un SpectralMessage synthétique à partir de l'émotion
        spectral_11d = self._emotion_to_spectral_11d(emotion)

        return self.synthesize(spectral_11d, voice=voice, text=text, output_path=output_path)

    # -----------------------------------------------------------------
    # EXTRACTION DE SIGNATURES
    # -----------------------------------------------------------------

    def extract_voice_signature(self, audio_path: str,
                                cache: bool = True) -> np.ndarray:
        """
        Extrait la signature vocale 11D d'un fichier audio.

        Args:
            audio_path: Chemin vers le fichier audio
            cache: Si True, met en cache la signature

        Returns:
            voice_array: np.ndarray [11]
        """
        if cache and audio_path in self._signature_cache:
            return self._signature_cache[audio_path].copy()

        sig = self.extractor.extract(audio_path)
        voice_array = sig.to_array()

        if cache:
            self._signature_cache[audio_path] = voice_array

        self.stats['total_extracted'] += 1
        return voice_array

    def extract_corpus_signatures(self, audio_dir: str,
                                  output_json: Optional[str] = None) -> List[Dict]:
        """
        Extrait les signatures de tout un corpus audio.

        Args:
            audio_dir: Répertoire contenant les fichiers audio
            output_json: Chemin du fichier JSON de sortie

        Returns:
            Liste de dicts {file, signature_11d, ...}
        """
        from engine.voice_signature_extractor import extract_corpus_signatures

        if output_json is None:
            output_json = str(self.signatures_dir / f"corpus_signatures_{int(time.time())}.json")

        return extract_corpus_signatures(audio_dir, output_json)

    def select_top_voices(self, signatures_json: str, top_n: int = 20) -> List[Dict]:
        """
        Sélectionne les meilleures voix d'un corpus.
        """
        from engine.voice_signature_extractor import select_top_voices
        return select_top_voices(signatures_json, top_n)

    # -----------------------------------------------------------------
    # ENTRAÎNEMENT
    # -----------------------------------------------------------------

    def train(self, signatures_json: str,
              epochs: int = 100,
              learning_rate: float = 0.01) -> List[float]:
        """
        Entraîne le modèle de mapping SpectralMessage → Paramètres vocaux.

        Args:
            signatures_json: Chemin vers le JSON de signatures
            epochs: Nombre d'époques
            learning_rate: Taux d'apprentissage

        Returns:
            losses: Historique des pertes
        """
        losses = self.trainer.train_from_signatures_json(
            signatures_json, epochs, learning_rate
        )

        # Sauvegarder le modèle
        model_path = self.model_dir / "spectral_voice_mapper.npz"
        self.trainer.save_model(str(model_path))

        self.stats['total_trained_epochs'] += epochs
        return losses

    def apply_learning_optimization(self, adjustment_params: Dict[str, float]):
        """
        Applique les ajustements du MetaLearningLoop (recursive_learner.py)
        au modèle vocal.
        """
        self.trainer.apply_resonance_optimization(adjustment_params)
        # Sauvegarder après optimisation
        model_path = self.model_dir / "spectral_voice_mapper.npz"
        self.trainer.save_model(str(model_path))

    # -----------------------------------------------------------------
    # MÉTHODES INTERNES
    # -----------------------------------------------------------------

    def _decode_spectral_to_text(self, spectral_11d: np.ndarray) -> str:
        """
        Génère un texte de fallback à partir d'un SpectralMessage.
        Dans la version complète, le texte proviendrait du décodeur de texte.
        """
        # Fallback : message générique basé sur les dimensions dominantes
        dominant_idx = int(np.argmax(spectral_11d))

        messages = [
            "Texte généré à partir du message spectral.",
            "Contenu synthétisé par le décodeur harmonique.",
            "Message vocal harmonique de démonstration.",
            "Le système de synthèse vocale est opérationnel.",
            "Voici un exemple de synthèse pilotée par SpectralMessage.",
        ]

        # Choix déterministe basé sur la signature
        msg_idx = int(spectral_11d[dominant_idx] * len(messages)) % len(messages)
        return messages[msg_idx]

    def _problem_to_spectral_11d(self, spectral_problem) -> np.ndarray:
        """
        Convertit un SpectralProblem (HarmonicResonator) en signature 11D.
        """
        # Extraire les harmoniques dans l'ordre canonique
        harmonic_keys = [
            'H_factual', 'H_logical', 'H_emotional', 'H_creative',
            'H_temporal', 'H_spatial', 'H_relational',
        ]

        # Récupérer les valeurs des harmoniques
        harmonics = spectral_problem.harmonics if hasattr(spectral_problem, 'harmonics') else {}
        h_values = [harmonics.get(k, PHI_INV) for k in harmonic_keys]

        # Compléter avec les 4 dimensions supplémentaires
        reasoning_types = spectral_problem.reasoning_types if hasattr(spectral_problem, 'reasoning_types') else {}
        reasoning_val = np.mean(list(reasoning_types.values())) if reasoning_types else PHI_INV

        complexity = spectral_problem.complexity if hasattr(spectral_problem, 'complexity') else PHI_INV
        urgency = spectral_problem.urgency if hasattr(spectral_problem, 'urgency') else PHI_INV

        # Construire l'array 11D (ordre canonique de signatures_11d.py)
        spectral_11d = np.array([
            h_values[0],  # H_factual → phi
            h_values[3],  # H_creative → alpha
            h_values[1],  # H_logical → reasoning
            h_values[3],  # H_creative → creativity
            0.0,           # math (non présent dans SpectralProblem)
            h_values[0],  # H_factual → factual
            0.0,           # code (non présent)
            h_values[2],  # H_emotional → emotion
            urgency,       # temporal → urgence
            complexity,    # coherence approximée
            h_values[6],  # H_relational → resonance
        ])

        return np.clip(spectral_11d, 0.0, 1.0)

    def _emotion_to_spectral_11d(self, emotion: str) -> np.ndarray:
        """
        Crée un SpectralMessage 11D synthétique à partir d'un label émotionnel.
        """
        mod = EMOTION_TO_VOICE_MODULATION.get(emotion, EMOTION_TO_VOICE_MODULATION['neutre'])

        # Base neutre (toutes dimensions à φ⁻¹)
        spectral = np.full(11, PHI_INV)

        # Moduler selon l'émotion
        # Dimension 'emotion' (idx 7) : impactée
        spectral[7] = PHI_INV + (mod['speed_factor'] - 1.0) * 0.5
        spectral[7] = np.clip(spectral[7], 0.0, 1.0)

        # Dimension 'temporal' (idx 8) : urgence
        if emotion in ['urgent', 'excité']:
            spectral[8] = 0.8
        elif emotion in ['calme', 'triste']:
            spectral[8] = 0.3

        # Dimension 'creativity' (idx 3) : expressivité
        if emotion in ['joyeux', 'excité']:
            spectral[3] = 0.7
        elif emotion in ['triste']:
            spectral[3] = 0.4

        # Dimension 'alpha' (idx 1) : amplitude
        if emotion in ['autoritaire', 'urgent']:
            spectral[1] = 0.75
        elif emotion in ['doux', 'calme']:
            spectral[1] = 0.4

        return np.clip(spectral, 0.0, 1.0)

    # -----------------------------------------------------------------
    # INTERFACE POUR tts_server.py
    # -----------------------------------------------------------------

    def synthesize_for_tts_server(self, text: str = "",
                                  spectral_message_json: Optional[str] = None,
                                  voice: str = "default",
                                  emotion: str = "neutre") -> Tuple[bytes, str]:
        """
        Interface unifiée pour tts_server.py.

        Accepte soit du texte simple, soit un SpectralMessage JSON,
        et retourne l'audio + content-type.

        Args:
            text: Texte à synthétiser (mode simple)
            spectral_message_json: SpectralMessage 11D en JSON (mode spectral)
            voice: Nom du profil vocal
            emotion: Émotion pour la modulation

        Returns:
            (audio_bytes, content_type)
        """
        if spectral_message_json:
            try:
                spectral_11d = np.array(json.loads(spectral_message_json))
                if spectral_11d.shape != (11,):
                    raise ValueError(f"Le SpectralMessage doit avoir 11 dimensions, "
                                     f"reçu {spectral_11d.shape}")
                audio = self.synthesize(
                    spectral_11d, voice=voice, text=text or None
                )
            except (json.JSONDecodeError, ValueError) as e:
                print(f"[SpectralVoicePipeline] SpectralMessage invalide: {e}")
                audio = self.synthesize_from_text(text=text or "", emotion=emotion, voice=voice)
        else:
            audio = self.synthesize_from_text(
                text=text, emotion=emotion, voice=voice
            )

        return audio, "audio/mpeg"

    # -----------------------------------------------------------------
    # ÉVALUATION MOS
    # -----------------------------------------------------------------

    def evaluate_mos(self, test_files: List[str],
                     reference_scores: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Évalue le score MOS (Mean Opinion Score) estimé sur des fichiers de test.

        Extrait les signatures vocales et calcule le H_naturalness moyen.

        Args:
            test_files: Liste de chemins audio
            reference_scores: Scores de référence optionnels

        Returns:
            Dict avec mos_score, per_file_scores, avg_naturalness, etc.
        """
        naturalness_scores = []

        for f in test_files:
            try:
                sig = self.extract_voice_signature(f, cache=False)
                # H_naturalness est l'index 10
                naturalness = sig[10]
                # Convertir [0,1] → MOS [1,5]
                mos = naturalness * 4.0 + 1.0
                naturalness_scores.append({
                    'file': f,
                    'H_naturalness': float(naturalness),
                    'mos_estimated': float(mos),
                })
            except Exception as e:
                naturalness_scores.append({
                    'file': f,
                    'error': str(e),
                })

        avg_naturalness = np.mean([
            s['H_naturalness'] for s in naturalness_scores if 'H_naturalness' in s
        ]) if naturalness_scores else 0.0

        avg_mos = np.mean([
            s['mos_estimated'] for s in naturalness_scores if 'mos_estimated' in s
        ]) if naturalness_scores else 0.0

        return {
            'mos_avg_estimated': float(avg_mos),
            'mos_target': 4.0,
            'mos_success': avg_mos > 4.0,
            'avg_H_naturalness': float(avg_naturalness),
            'num_files': len(test_files),
            'per_file': naturalness_scores,
        }

    # -----------------------------------------------------------------
    # STATS ET ÉTAT
    # -----------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du pipeline."""
        return {
            **self.stats,
            'num_profiles': len(self.trainer.voice_profiles),
            'profiles': self.trainer.list_profiles(),
            'model_weights_summary': self.trainer.mapper.get_weights_summary(),
        }

    def save_state(self):
        """Sauvegarde l'état complet du pipeline."""
        # Sauvegarder le modèle
        model_path = self.model_dir / "spectral_voice_mapper.npz"
        self.trainer.save_model(str(model_path))

        # Sauvegarder les stats
        stats_path = self.model_dir / "pipeline_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def load_state(self):
        """Charge l'état sauvegardé."""
        stats_path = self.model_dir / "pipeline_stats.json"
        if stats_path.exists():
            with open(stats_path, 'r') as f:
                self.stats = json.load(f)


# =========================================================================
# SINGLETON GLOBAL
# =========================================================================

# Instance globale du pipeline (initialisée à la demande)
_pipeline_instance: Optional[SpectralVoicePipeline] = None


def get_pipeline() -> SpectralVoicePipeline:
    """
    Retourne l'instance globale du SpectralVoicePipeline.
    Pattern Singleton pour réutilisation dans tout le projet.
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = SpectralVoicePipeline()
        _pipeline_instance.initialize()
    return _pipeline_instance


def reset_pipeline():
    """Réinitialise l'instance globale."""
    global _pipeline_instance
    _pipeline_instance = None


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST SpectralVoicePipeline — Pipeline Complet")
    print("=" * 60)

    # Test 1 : Initialisation
    pipeline = SpectralVoicePipeline()
    pipeline.initialize()
    print(f"\n✓ Pipeline initialisé")
    print(f"  Profils: {pipeline.trainer.list_profiles()}")
    print(f"  Modèle chargé: {pipeline._initialized}")

    # Test 2 : Synthèse depuis SpectralMessage
    spectral_11d = np.array([
        PHI_INV, 0.5, 0.7, 0.6, 0.3, 0.55, 0.2, 0.8, 0.65, PHI_INV, 0.618
    ])

    print(f"\n--- Test synthèse depuis SpectralMessage ---")
    audio = pipeline.synthesize(
        spectral_11d,
        voice="default",
        text="Bonjour, ceci est un test de la synthèse vocale harmonique.",
    )

    if audio:
        output_file = str(pipeline.output_dir / "test_spectral_output.mp3")
        with open(output_file, 'wb') as f:
            f.write(audio)
        print(f"  ✓ Audio généré : {len(audio)} octets → {output_file}")
    else:
        print(f"  ⚠ Synthèse échouée (Edge-TTS requis)")

    # Test 3 : Synthèse par émotion
    print(f"\n--- Test synthèse par émotion ---")
    for emotion in ['joyeux', 'calme', 'autoritaire']:
        audio = pipeline.synthesize_from_text(
            text=f"Ceci est un test avec l'émotion {emotion}.",
            emotion=emotion,
            voice="default",
        )
        if audio:
            print(f"  ✓ {emotion:>12}: {len(audio)} octets")
        else:
            print(f"  ⚠ {emotion:>12}: échoué")

    # Test 4 : Stats
    print(f"\n--- Statistiques ---")
    for k, v in pipeline.get_stats().items():
        if isinstance(v, (int, float, str)):
            print(f"  {k}: {v}")

    print("\n" + "=" * 60)