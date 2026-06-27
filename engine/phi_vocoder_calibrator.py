"""
Phase 2 — Auto-Calibration du φ-Vocoder par Résonance
========================================================
Compare la sortie du φ-Vocoder avec les fichiers audio réels
du corpus LJSpeech, mesure l'écart spectral, et ajuste les
paramètres du vocodeur pour minimiser la différence.

Principe :
  1. Prendre un fichier LJSpeech réel
  2. Extraire sa signature vocale 11D (VoiceSignatureExtractor)
  3. Synthétiser le même son via le φ-Vocoder (PhiVocoder)
  4. Extraire la signature 11D de la synthèse
  5. Calculer la distance φ-pondérée entre les deux signatures
  6. Ajuster les paramètres du φ-Vocoder pour réduire la distance
  7. Répéter jusqu'à convergence

C'est la boucle de rétroaction harmonique — le vocodeur
s'auto-améliore en écoutant ses propres sorties.

Usage :
    calibrator = PhiVocoderCalibrator()
    calibrator.load_reference_signatures("data/voice_signatures/ljspeech_signatures.json")
    losses = calibrator.calibrate(epochs=50, learning_rate=0.01)
    calibrator.save_params("models/voice/phi_vocoder_params.npz")
"""

import math
import json
import os
import sys
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import numpy as np

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =========================================================================
# CONSTANTES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI

# Paramètres ajustables du φ-Vocoder
ADJUSTABLE_PARAMS = [
    'formant_shift',       # Décalage global des formants (Hz relatif)
    'formant_bandwidth',   # Facteur de largeur de bande
    'harmonic_decay',      # Facteur de décroissance harmonique
    'breath_gain',         # Gain du bruit de souffle
    'amplitude_comp',      # Compensation d'amplitude
    'timbre_warp',         # Déformation du timbre (non-linéarité)
]

# Plages autorisées pour chaque paramètre
PARAM_RANGES = {
    'formant_shift':     (-0.3,  0.3),    # ±30% de décalage
    'formant_bandwidth': (0.3,   3.0),    # 0.3× à 3× la largeur de bande
    'harmonic_decay':    (0.3,   1.5),    # Décroissance harmonique
    'breath_gain':       (0.0,   2.0),    # Gain souffle
    'amplitude_comp':    (0.3,   3.0),    # Compensation amplitude
    'timbre_warp':       (-0.5,  0.5),    # Warp non-linéaire
}

# Poids φ des dimensions vocales pour la distance
PHI_WEIGHTS = np.array([
    1.0,           # H_pitch_mean
    1.0,           # H_pitch_range
    1.0,           # H_speed
    PHI,           # H_timbre
    PHI_INV,       # H_breathiness
    1.0,           # H_resonance
    PHI_INV ** 2,  # H_emotion_range
    PHI,           # H_clarity
    PHI_INV,       # H_pause_pattern
    PHI,           # H_phi_alignment
    PHI,           # H_naturalness
])


# =========================================================================
# PARAMÈTRES DU VOCODEUR AJUSTABLES
# =========================================================================

class VocoderParams:
    """Paramètres ajustables du φ-Vocoder."""

    def __init__(self):
        # Valeurs par défaut (centre de la plage)
        self.formant_shift = 0.0        # Décalage relatif
        self.formant_bandwidth = 1.0     # Facteur de largeur
        self.harmonic_decay = 1.0        # Facteur de décroissance
        self.breath_gain = 1.0           # Gain souffle
        self.amplitude_comp = 1.0         # Compensation
        self.timbre_warp = 0.0            # Warp

    def to_dict(self) -> Dict[str, float]:
        return {
            'formant_shift': self.formant_shift,
            'formant_bandwidth': self.formant_bandwidth,
            'harmonic_decay': self.harmonic_decay,
            'breath_gain': self.breath_gain,
            'amplitude_comp': self.amplitude_comp,
            'timbre_warp': self.timbre_warp,
        }

    def to_array(self) -> np.ndarray:
        return np.array([
            self.formant_shift, self.formant_bandwidth,
            self.harmonic_decay, self.breath_gain,
            self.amplitude_comp, self.timbre_warp,
        ])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'VocoderParams':
        p = cls()
        p.formant_shift = float(arr[0])
        p.formant_bandwidth = float(arr[1])
        p.harmonic_decay = float(arr[2])
        p.breath_gain = float(arr[3])
        p.amplitude_comp = float(arr[4])
        p.timbre_warp = float(arr[5])
        return p

    def clamp(self):
        """Limite les paramètres dans leurs plages autorisées."""
        for name, (vmin, vmax) in PARAM_RANGES.items():
            val = getattr(self, name)
            setattr(self, name, np.clip(val, vmin, vmax))

    def apply_to_formants(self, base_formants: np.ndarray) -> np.ndarray:
        """
        Applique les paramètres aux formants de base.
        Returns: formants ajustés [5]
        """
        f = base_formants.copy()

        # Décalage global
        f *= (1.0 + self.formant_shift)

        # Timbre warp : déforme non-linéairement l'espacement
        if abs(self.timbre_warp) > 0.001:
            # Compression ou expansion de l'espacement selon φ
            center = 3  # F3 comme pivot
            for i in range(5):
                dist = i - center
                f[i] *= (1.0 + self.timbre_warp * dist * 0.1)

        return f

    def apply_to_harmonics(self, base_amplitudes: np.ndarray) -> np.ndarray:
        """
        Applique la décroissance harmonique et la compensation.
        Returns: amplitudes ajustées [32]
        """
        n = len(base_amplitudes)
        # Décroissance modifiée : φ^(-n * decay_factor)
        indices = np.arange(n)
        amps = PHI_INV ** (indices * self.harmonic_decay)
        amps *= self.amplitude_comp
        return amps

    def apply_breath(self, base_breath: float) -> float:
        """Ajuste le gain de souffle."""
        return base_breath * self.breath_gain


# =========================================================================
# CALIBRATEUR DU φ-VOCODEUR
# =========================================================================

class PhiVocoderCalibrator:
    """
    Auto-calibre le φ-Vocoder en comparant analyse-synthèse
    sur un corpus de référence (LJSpeech).

    Boucle Phase 2 — Affinage par résonance.
    """

    def __init__(self, reference_json: Optional[str] = None):
        """
        Args:
            reference_json: Chemin vers le JSON de signatures LJSpeech
        """
        self.reference_data: List[Dict] = []
        self.params = VocoderParams()
        self.loss_history: List[float] = []
        self.best_params = None
        self.best_loss = float('inf')

        # Charger les données si fournies
        if reference_json and Path(reference_json).exists():
            self.load_reference_signatures(reference_json)

    def load_reference_signatures(self, json_path: str):
        """
        Charge les signatures vocales 11D de référence.
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            self.reference_data = json.load(f)

        print(f"[Calibrator] {len(self.reference_data)} signatures de reference chargees")

    def calibrate(self,
                  epochs: int = 50,
                  learning_rate: float = 0.01,
                  batch_size: int = 100,
                  verbose: bool = True) -> List[float]:
        """
        Exécute la boucle d'auto-calibration.

        Pour chaque époque :
        1. Échantillonne N fichiers du corpus
        2. Pour chaque fichier : extrait signature réelle, synthétise,
           extrait signature synthétique, calcule distance
        3. Calcule le gradient par perturbation φ
        4. Met à jour les paramètres

        Args:
            epochs: Nombre d'itérations
            learning_rate: Taux d'apprentissage
            batch_size: Nombre de fichiers par époque
            verbose: Affiche la progression

        Returns:
            loss_history: Historique des pertes
        """
        if len(self.reference_data) < 10:
            print("[Calibrator] Pas assez de donnees (< 10), calibration impossible")
            return []

        # Initialiser l'extracteur et le vocodeur
        from engine.voice_signature_extractor import VoiceSignatureExtractor
        from engine.phi_vocoder import PhiVocoder, PhiSourceParams

        extractor = VoiceSignatureExtractor()
        vocoder = PhiVocoder(sample_rate=22050)

        print(f"[Calibrator] Demarrage calibration — {epochs} epoques, "
              f"lr={learning_rate}, batch={batch_size}")
        t_start = time.time()

        for epoch in range(epochs):
            # Échantillonner un batch aléatoire
            indices = np.random.choice(
                len(self.reference_data),
                size=min(batch_size, len(self.reference_data)),
                replace=False
            )

            epoch_losses = []

            for idx in indices:
                entry = self.reference_data[idx]
                audio_path = entry['file']

                # Vérifier que le fichier existe
                if not Path(audio_path).exists():
                    continue

                try:
                    # 1. Extraire la signature réelle
                    real_sig = extractor.extract(audio_path)
                    real_array = real_sig.to_array()

                    # 2. Synthétiser avec le φ-Vocoder
                    # Appliquer nos paramètres de calibration
                    adjusted_params = self._apply_params_to_11d(real_array)

                    # Synthétiser : durée = durée du fichier réel
                    duration = entry.get('duration', 2.0)
                    if duration <= 0:
                        duration = 2.0
                    synth_audio = vocoder.synthesize(adjusted_params, duration=duration)

                    # 3. Extraire la signature de la synthèse
                    # Sauvegarder temporairement puis extraire
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                        from engine.phi_vocoder import save_wav
                        save_wav(synth_audio, tmp.name)
                        synth_sig = extractor.extract(tmp.name)
                        synth_array = synth_sig.to_array()
                    Path(tmp.name).unlink(missing_ok=True)

                    # 4. Distance φ-pondérée
                    distance = self._phi_distance(real_array, synth_array)
                    epoch_losses.append(distance)

                except Exception as e:
                    continue

            if not epoch_losses:
                continue

            mean_loss = float(np.mean(epoch_losses))
            self.loss_history.append(mean_loss)

            # Mettre à jour les meilleurs paramètres
            if mean_loss < self.best_loss:
                self.best_loss = mean_loss
                self.best_params = self.params.to_array().copy()

            # 5. Gradient par perturbation φ
            if epoch < epochs - 1:  # Ne pas optimiser après la dernière époque
                self._phi_gradient_step(
                    extractor, vocoder,
                    learning_rate, batch_size, epoch
                )

            if verbose and epoch % 10 == 0:
                elapsed = time.time() - t_start
                print(f"  Epoch {epoch:4d}/{epochs} — loss: {mean_loss:.6f} "
                      f"(best: {self.best_loss:.6f}) — {elapsed:.0f}s")

        elapsed = time.time() - t_start
        print(f"[Calibrator] Termine — {epochs} epoques en {elapsed:.0f}s")
        print(f"  Loss initiale: {self.loss_history[0]:.6f}")

        if len(self.loss_history) > 1:
            print(f"  Loss finale: {self.loss_history[-1]:.6f} "
                  f"({(1 - self.loss_history[-1]/self.loss_history[0])*100:.1f}% amelioration)")

        print(f"  Meilleurs parametres: {self.params.to_dict()}")

        # Restaurer les meilleurs paramètres
        if self.best_params is not None:
            self.params = VocoderParams.from_array(self.best_params)

        return self.loss_history

    def _phi_gradient_step(self, extractor, vocoder,
                           learning_rate: float, batch_size: int,
                           epoch: int):
        """
        Calcule le gradient par perturbation φ.
        
        Au lieu de rétropropager, on teste de petites perturbations
        aléatoires espacées par φ, et on garde la meilleure direction.
        """
        # Facteur de décroissance φ : les pas deviennent plus petits
        decay = PHI_INV ** (epoch / 10.0)
        lr = learning_rate * decay

        # Générer 3 perturbations φ-espacées
        np.random.seed(epoch * 137 + 42)  # Reproductible par époque
        perturbations = []
        for i in range(3):
            # Direction aléatoire avec magnitude décroissante
            direction = np.random.randn(6)
            direction /= np.linalg.norm(direction) + 1e-8
            # Magnitude espacée par φ
            magnitude = lr * (PHI_INV ** i)
            perturbations.append(direction * magnitude)

        # Tester chaque perturbation
        original_params = self.params.to_array()
        best_loss = float('inf')
        best_update = np.zeros(6)

        for pert in perturbations:
            candidate = original_params + pert
            candidate = np.clip(candidate,
                               np.array([PARAM_RANGES[p][0] for p in ADJUSTABLE_PARAMS]),
                               np.array([PARAM_RANGES[p][1] for p in ADJUSTABLE_PARAMS]))

            # Évaluer sur un petit sous-ensemble (10 fichiers)
            test_indices = np.random.choice(len(self.reference_data), size=10, replace=False)
            losses = []

            for idx in test_indices:
                entry = self.reference_data[idx]
                audio_path = entry['file']
                if not Path(audio_path).exists():
                    continue

                try:
                    real_sig = extractor.extract(audio_path)
                    real_array = real_sig.to_array()
                    adjusted = self._apply_params_to_11d(
                        real_array, candidate_params=candidate
                    )
                    duration = entry.get('duration', 2.0)
                    if duration <= 0:
                        duration = 2.0
                    synth_audio = vocoder.synthesize(adjusted, duration=duration)

                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                        from engine.phi_vocoder import save_wav
                        save_wav(synth_audio, tmp.name)
                        synth_sig = extractor.extract(tmp.name)
                        synth_array = synth_sig.to_array()
                    Path(tmp.name).unlink(missing_ok=True)

                    loss = self._phi_distance(real_array, synth_array)
                    losses.append(loss)
                except Exception:
                    continue

            if losses:
                mean_loss = float(np.mean(losses))
                if mean_loss < best_loss:
                    best_loss = mean_loss
                    best_update = pert

        # Appliquer la meilleure perturbation
        if np.any(best_update != 0):
            new_params = self.params.to_array() + best_update
            # Clipper dans les plages
            for i, name in enumerate(ADJUSTABLE_PARAMS):
                vmin, vmax = PARAM_RANGES[name]
                new_params[i] = np.clip(new_params[i], vmin, vmax)
            self.params = VocoderParams.from_array(new_params)

    def _apply_params_to_11d(self, voice_11d: np.ndarray,
                              candidate_params: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Applique les paramètres de calibration à une signature 11D,
        produisant les paramètres ajustés pour le φ-Vocoder.

        Les ajustements principaux :
        - H_pitch_range modifié par formant_shift
        - H_timbre modifié par timbre_warp
        - H_breathiness modifié par breath_gain
        - H_clarity modifié par formant_bandwidth
        - H_naturalness modifié par amplitude_comp
        """
        params = self.params if candidate_params is None else VocoderParams.from_array(candidate_params)
        adjusted = voice_11d.copy()

        # Le formant_shift affecte le timbre perçu
        adjusted[3] = np.clip(adjusted[3] + params.formant_shift * 0.3, 0, 1)

        # Le timbre_warp affecte aussi le timbre (non-linéaire)
        if abs(params.timbre_warp) > 0.001:
            adjusted[3] = adjusted[3] ** (1.0 + params.timbre_warp * 0.5)
            adjusted[3] = np.clip(adjusted[3], 0, 1)

        # Le breath_gain module le souffle
        adjusted[4] = np.clip(adjusted[4] * params.breath_gain, 0, 1)

        # Le formant_bandwidth module la clarté
        adjusted[7] = np.clip(adjusted[7] * (2.0 - params.formant_bandwidth * 0.5), 0, 1)

        # L'amplitude_comp module la naturalité
        adjusted[10] = np.clip(adjusted[10] * params.amplitude_comp, 0, 1)

        return adjusted

    def _phi_distance(self, sig1: np.ndarray, sig2: np.ndarray) -> float:
        """
        Distance φ-pondérée entre deux signatures 11D.
        """
        weights = PHI_WEIGHTS / np.sum(PHI_WEIGHTS)
        diff = (sig1 - sig2) ** 2
        return float(np.sqrt(np.sum(diff * weights)))

    def save_params(self, filepath: str):
        """Sauvegarde les paramètres calibrés."""
        np.savez(filepath, **self.params.to_dict())
        print(f"[Calibrator] Parametres sauvegardes dans {filepath}")

    def load_params(self, filepath: str):
        """Charge des paramètres calibrés."""
        if Path(filepath).exists():
            data = np.load(filepath)
            for name in ADJUSTABLE_PARAMS:
                if name in data:
                    setattr(self.params, name, float(data[name]))
            print(f"[Calibrator] Parametres charges depuis {filepath}")

    def apply_to_vocoder(self, vocoder) -> 'PhiVocoder':
        """
        Applique les paramètres calibrés à un φ-Vocoder existant
        en modifiant ses constantes internes.
        """
        import engine.phi_vocoder as pv

        # Modifier les formants de référence
        base_formants = pv.PHI_FORMANTS_REF.copy()
        adjusted_formants = self.params.apply_to_formants(base_formants)

        # Modifier les largeurs de bande
        adjusted_bw = pv.FORMANT_BANDWIDTHS * self.params.formant_bandwidth

        # Appliquer au vocodeur
        # Note : ces constantes sont au niveau module, on les remplace
        pv.PHI_FORMANTS_REF[:] = adjusted_formants
        pv.FORMANT_BANDWIDTHS[:] = np.clip(adjusted_bw, 20, 500)

        return vocoder


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST PhiVocoderCalibrator — Auto-Calibration par Resonance")
    print("=" * 60)

    calibrator = PhiVocoderCalibrator()

    # Test 1 : Calibration sur donnees simulees
    print("\n--- Test calibration simulee ---")
    # Simuler des signatures de reference
    np.random.seed(42)
    n_ref = 30
    calibrator.reference_data = [
        {
            'file': 'simulated_sample.wav',
            'signature_11d': {
                'H_pitch_mean': 0.65 + np.random.normal(0, 0.05),
                'H_pitch_range': 0.45 + np.random.normal(0, 0.05),
                'H_speed': 0.55 + np.random.normal(0, 0.05),
                'H_timbre': 0.68 + np.random.normal(0, 0.05),
                'H_breathiness': 0.15 + np.random.normal(0, 0.03),
                'H_resonance': 0.72 + np.random.normal(0, 0.05),
                'H_emotion_range': 0.35 + np.random.normal(0, 0.05),
                'H_clarity': 0.80 + np.random.normal(0, 0.05),
                'H_pause_pattern': 0.40 + np.random.normal(0, 0.05),
                'H_phi_alignment': 0.72 + np.random.normal(0, 0.05),
                'H_naturalness': 0.80 + np.random.normal(0, 0.05),
            },
            'duration': 2.0,
        }
        for _ in range(n_ref)
    ]

    losses = calibrator.calibrate(epochs=10, learning_rate=0.02, batch_size=10)

    if losses:
        print(f"\n  Amelioration: {(1 - losses[-1]/losses[0])*100:.1f}%")
        print(f"  Params finaux: {calibrator.params.to_dict()}")

    # Test 2 : Avec vraies signatures LJSpeech (si dispo)
    lj_path = "data/voice_signatures/ljspeech_signatures.json"
    if Path(lj_path).exists():
        print(f"\n{'=' * 60}")
        print("TEST SUR LJSPEECH REEL")
        print("=" * 60)
        real_cal = PhiVocoderCalibrator(lj_path)
        real_losses = real_cal.calibrate(epochs=20, learning_rate=0.01, batch_size=50)
        if real_losses:
            real_cal.save_params("models/voice/phi_vocoder_params.npz")

    print("\n" + "=" * 60)