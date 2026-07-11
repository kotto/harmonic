#!/usr/bin/env python3
"""
Wave Fine-Tune — Ajustement des ψ par la contrainte ⊛
=======================================================
Pour chaque fait (sujet, relation, objet), la contrainte est :
    ψ_sujet ⊛ ψ_relation ≈ ψ_objet

Cet ajustement itératif minimise l'erreur totale :
    L = Σ ||ψ_s ⊛ ψ_r - ψ_o||²

C'est l'équivalent ondulatoire de la rétropropagation,
mais sans gradient — c'est de l'algèbre linéaire dans ℂ⁵¹².

ALGORITHME (inspiré de Hebb : "fire together, wire together") :
  1. Pour chaque fait (s, r, o) :
     a. Calculer la prédiction : ψ_pred = ψ_s ⊛ ψ_r
     b. Calculer l'erreur : E = ψ_pred - ψ_o
     c. Ajuster ψ_s : ψ_s += η · (E ⊗ ψ_r)   (corrélation circulaire)
     d. Ajuster ψ_r : ψ_r += η · (ψ_s* ⊗ E)
     e. Normaliser les vecteurs modifiés
  2. Répéter jusqu'à convergence

USAGE :
  from wave_fine_tune import WaveFineTuner
  tuner = WaveFineTuner(encoder)
  tuner.fine_tune(knowledge_base, epochs=3)
"""

import math
import numpy as np
from typing import List, Tuple, Optional
import logging

log = logging.getLogger(__name__)

PHI = 1.618033988749895


def _circular_convolve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """a ⊛ b = IFFT(FFT(a) · FFT(b))"""
    A = np.fft.fft(a)
    B = np.fft.fft(b)
    return np.fft.ifft(A * B)


def _circular_correlate(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """a ⊗ b = IFFT(FFT(a) · conj(FFT(b))) — unbinding"""
    A = np.fft.fft(a)
    B = np.fft.fft(b)
    return np.fft.ifft(A * np.conj(B))


def _normalize(psi: np.ndarray) -> np.ndarray:
    """Normalise un vecteur ψ à la norme unitaire."""
    norm = np.sqrt(np.sum(np.abs(psi) ** 2))
    if norm > 1e-15:
        return psi / norm
    return psi


class WaveFineTuner:
    """
    Ajuste les ψ pour que ψ_s ⊛ ψ_r ≈ ψ_o pour tous les faits.
    """

    def __init__(self, encoder, learning_rate: float = 0.01):
        self.encoder = encoder
        self.lr = learning_rate
        self.dim = encoder.dim

    def fine_tune(self, knowledge_base: List[Tuple[str, str, str, str]],
                  epochs: int = 3, verbose: bool = True) -> dict:
        """
        Ajuste itérativement les ψ de la KB.

        Args:
            knowledge_base: liste de (sujet, relation, objet, secteur)
            epochs: nombre de passes complètes
            verbose: afficher la progression

        Returns:
            dict avec les métriques d'entraînement
        """
        history = {'epoch': [], 'loss': [], 'adjusted': []}

        for epoch in range(epochs):
            total_loss = 0.0
            adjusted = 0

            for s, r, o, sec in knowledge_base:
                # Encoder les mots
                psi_s = self._get_vec(s)
                psi_r = self._get_vec(r)
                psi_o = self._get_vec(o)

                if psi_s is None or psi_r is None or psi_o is None:
                    continue

                # Prédiction : ψ_pred = ψ_s ⊛ ψ_r
                psi_pred = _circular_convolve(psi_s, psi_r)

                # Erreur
                error = psi_pred - psi_o
                loss = float(np.sum(np.abs(error) ** 2))
                total_loss += loss

                # Ajuster ψ_s : Δψ_s = η · (error ⊗ ψ_r)
                correction_s = _circular_correlate(error, psi_r) * self.lr
                psi_s_new = _normalize(psi_s - correction_s)

                # Ajuster ψ_o : Δψ_o = η · (ψ_pred - ψ_o)  (rapprocher de la réalité)
                correction_o = error * self.lr
                psi_o_new = _normalize(psi_o + correction_o)

                # Appliquer
                self._set_vec(s, psi_s_new)
                self._set_vec(o, psi_o_new)
                adjusted += 1

            avg_loss = total_loss / max(adjusted, 1)
            history['epoch'].append(epoch)
            history['loss'].append(avg_loss)
            history['adjusted'].append(adjusted)

            if verbose:
                log.info(f"  Epoch {epoch+1}/{epochs}: loss={avg_loss:.4f}, "
                         f"adjusted={adjusted} faits")

        return history

    def _get_vec(self, word: str) -> Optional[np.ndarray]:
        """Récupère le ψ d'un mot, l'encode si nécessaire."""
        w = word.lower().strip()
        if w in self.encoder.word_vectors:
            return self.encoder.word_vectors[w].copy()
        # Encoder le mot (créé s'il n'existe pas)
        return self.encoder.encode_word(w)

    def _set_vec(self, word: str, psi: np.ndarray):
        """Met à jour le ψ d'un mot."""
        w = word.lower().strip()
        self.encoder.word_vectors[w] = psi


def demo(encoder, kb):
    """Démonstration du fine-tuning."""
    print("=" * 60)
    print("WAVE FINE-TUNE — Ajustement par contrainte ⊛")
    print("=" * 60)

    # Mesurer la cohérence avant
    pairs = [
        ('lumiere', 'onde'),
        ('lumiere', 'photon'),
        ('paris', 'france'),
    ]
    print("\nAvant fine-tuning:")
    for w1, w2 in pairs:
        v1 = encoder.word_vectors.get(w1)
        v2 = encoder.word_vectors.get(w2)
        if v1 is not None and v2 is not None:
            coh = float(np.real(np.dot(v1, np.conj(v2))))
            print(f"  {w1:15} ↔ {w2:15} → coh={coh:+.3f}")

    # Fine-tune
    tuner = WaveFineTuner(encoder, learning_rate=0.01)
    history = tuner.fine_tune(kb, epochs=3)

    print(f"\nAprès fine-tuning ({len(history['epoch'])} epochs):")
    for w1, w2 in pairs:
        v1 = encoder.word_vectors.get(w1)
        v2 = encoder.word_vectors.get(w2)
        if v1 is not None and v2 is not None:
            coh = float(np.real(np.dot(v1, np.conj(v2))))
            print(f"  {w1:15} ↔ {w2:15} → coh={coh:+.3f}")

    print(f"\nLoss finale: {history['loss'][-1]:.4f}")
    return history


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    from harmonic_brain import HarmonicBrain
    from harmonic_model import KNOWLEDGE_BASE

    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]
    brain = HarmonicBrain(facts[:500])
    demo(brain.unconscious.encoder, facts[:500])
