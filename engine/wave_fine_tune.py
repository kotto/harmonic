#!/usr/bin/env python3
"""
Wave Fine-Tune V2 — Moindres Carrés Alternés dans le Domaine de Fourier
=========================================================================
Pour chaque fait (sujet, relation, objet) :
    ψ_s ⊛ ψ_r ≈ ψ_o

Dans le domaine de Fourier, la convolution devient multiplication :
    ψ̃_s[k] · ψ̃_r[k] ≈ ψ̃_o[k]

SOLUTION (moindres carrés alternés) :
  Pour un mot w utilisé comme sujet :
    ψ̃_w[k] = Σ (ψ̃_o · ψ̃_r*) / Σ |ψ̃_r|²   (sur tous les faits où w est sujet)
  
  Puis normalisation dans le domaine temporel.

C'est la solution CLOSED-FORM optimale par fréquence.

USAGE :
  from wave_fine_tune import WaveFineTuner
  tuner = WaveFineTuner(encoder)
  tuner.fine_tune(knowledge_base, epochs=5)
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict
from collections import defaultdict
import logging

log = logging.getLogger(__name__)

PHI = 1.618033988749895


class WaveFineTuner:
    """
    Ajuste les ψ par moindres carrés alternés RÉGULARISÉS.
    
    L = Σ ||ψ_s ⊛ ψ_r - ψ_o||² + λ · Σ ||ψ - ψ_SVD||²
    
    λ contrôle l'équilibre entre :
      - Apprendre les relations (contrainte ⊛)
      - Préserver le sens (spectral embedding SVD)
    """

    def __init__(self, encoder, learning_rate: float = 1.0, lambda_reg: float = 1.0):
        self.encoder = encoder
        self.lr = learning_rate
        self.lambda_reg = lambda_reg  # Poids de la préservation sémantique
        self.dim = encoder.dim
        self.psi_svd = {}  # Sauvegarde des vecteurs SVD originaux

    def fine_tune(self, knowledge_base: List[Tuple[str, str, str, str]],
                  epochs: int = 5, verbose: bool = True) -> dict:
        """
        Ajuste itérativement les ψ par moindres carrés alternés.

        Args:
            knowledge_base: liste de (sujet, relation, objet, secteur)
            epochs: nombre de passes complètes
            verbose: afficher la progression

        Returns:
            dict avec métriques
        """
        history = {'epoch': [], 'loss': [], 'words_updated': []}

        # Construire les index : pour chaque mot, quels faits l'utilisent ?
        facts_by_subject = defaultdict(list)  # mot → [(r, o), ...]
        facts_by_object = defaultdict(list)   # mot → [(s, r), ...]
        all_words = set()

        for s, r, o, sec in knowledge_base:
            ws, wr, wo = s.lower().strip(), r.lower().strip(), o.lower().strip()
            facts_by_subject[ws].append((wr, wo))
            facts_by_object[wo].append((ws, wr))
            all_words.update([ws, wr, wo])

        # Filtrer : ne garder que les mots présents dans l'encodeur
        vocab = {w for w in all_words if w in self.encoder.word_vectors}

        # 🔥 SAUVEGARDER les vecteurs SVD originaux (pour la régularisation)
        self.psi_svd = {w: self.encoder.word_vectors[w].copy() for w in vocab}

        for epoch in range(epochs):
            total_loss = 0.0
            words_updated = 0

            # Étape 1 : Optimiser les ψ_sujet (en fixant ψ_relation et ψ_objet)
            words_updated += self._optimize_by_role(
                facts_by_subject, vocab, role='subject', epoch=epoch)

            # Étape 2 : Optimiser les ψ_objet (en fixant ψ_sujet et ψ_relation)
            words_updated += self._optimize_by_role(
                facts_by_object, vocab, role='object', epoch=epoch)

            # Calculer la loss
            total_loss = self._compute_loss(knowledge_base, vocab)
            avg_loss = total_loss / max(len(knowledge_base), 1)

            history['epoch'].append(epoch)
            history['loss'].append(avg_loss)
            history['words_updated'].append(words_updated)

            if verbose:
                log.info(f"  Epoch {epoch+1}/{epochs}: loss={avg_loss:.4f}, "
                         f"updated={words_updated} mots")

        return history

    def _optimize_by_role(self, facts_by_role: Dict[str, List],
                          vocab: set, role: str, epoch: int) -> int:
        """
        Optimise les ψ pour un rôle donné (sujet ou objet).
        
        SOLUTION RÉGULARISÉE (dans le domaine de Fourier) :
          ψ̃_w[k] = (Σ ψ̃_target · ψ̃_other* + λ · ψ̃_SVD[k]) / (Σ |ψ̃_other|² + λ)
        
        λ = 0 → solution non régularisée (instable)
        λ = ∞ → conserve ψ_SVD (aucun apprentissage)
        λ = 1 → équilibre optimal
        """
        updated = 0
        epsilon = 1e-8
        lam = self.lambda_reg

        for word in vocab:
            if word not in facts_by_role or not facts_by_role[word]:
                continue

            facts = facts_by_role[word]
            if len(facts) < 1:
                continue

            # Accumuler numérateur et dénominateur dans le domaine de Fourier
            num = np.zeros(self.dim, dtype=np.complex128)
            den = np.zeros(self.dim, dtype=np.float64)

            for other_word, target_word in facts:
                if other_word not in vocab or target_word not in vocab:
                    continue

                psi_other = self.encoder.word_vectors[other_word]
                psi_target = self.encoder.word_vectors[target_word]

                psi_other_f = np.fft.fft(psi_other)
                psi_target_f = np.fft.fft(psi_target)

                num += psi_target_f * np.conj(psi_other_f)
                den += np.abs(psi_other_f) ** 2

            # 🔥 RÉGULARISATION : ajouter le terme de préservation SVD
            if word in self.psi_svd and lam > 0:
                psi_svd_f = np.fft.fft(self.psi_svd[word])
                num += lam * psi_svd_f
                den += lam  # scalaire ajouté à chaque dimension

            if np.all(den < epsilon):
                continue

            # Solution optimale régularisée
            psi_new_f = num / (den + epsilon)
            psi_new = np.fft.ifft(psi_new_f)

            # Normaliser
            norm = np.sqrt(np.sum(np.abs(psi_new) ** 2))
            if norm > 1e-15:
                psi_new /= norm

            # Appliquer avec learning rate
            if self.lr >= 1.0:
                self.encoder.word_vectors[word] = psi_new
            else:
                psi_old = self.encoder.word_vectors[word]
                self.encoder.word_vectors[word] = psi_old + self.lr * (psi_new - psi_old)
                norm = np.sqrt(np.sum(np.abs(self.encoder.word_vectors[word]) ** 2))
                if norm > 1e-15:
                    self.encoder.word_vectors[word] /= norm

            updated += 1

        return updated

    def _compute_loss(self, knowledge_base: List, vocab: set) -> float:
        """Calcule la loss totale L = Σ ||ψ_s ⊛ ψ_r - ψ_o||²."""
        total = 0.0
        count = 0
        for s, r, o, sec in knowledge_base:
            ws, wr, wo = s.lower().strip(), r.lower().strip(), o.lower().strip()
            if ws not in vocab or wr not in vocab or wo not in vocab:
                continue
            psi_s = self.encoder.word_vectors[ws]
            psi_r = self.encoder.word_vectors[wr]
            psi_o = self.encoder.word_vectors[wo]
            # Convolution via FFT
            psi_pred = np.fft.ifft(np.fft.fft(psi_s) * np.fft.fft(psi_r))
            error = np.sum(np.abs(psi_pred - psi_o) ** 2)
            total += error
            count += 1
        return total / max(count, 1)


def demo(encoder, kb):
    """Démonstration du fine-tuning par moindres carrés."""
    print("=" * 60)
    print("WAVE FINE-TUNE V2 — Moindres Carrés Alternés (Fourier)")
    print("=" * 60)

    pairs = [('lumiere', 'onde'), ('lumiere', 'photon'),
             ('paris', 'france'), ('terre', 'gravite')]

    # Avant
    print("\nAvant:")
    for w1, w2 in pairs:
        v1 = encoder.word_vectors.get(w1)
        v2 = encoder.word_vectors.get(w2)
        if v1 is not None and v2 is not None:
            coh = float(np.real(np.dot(v1, np.conj(v2))))
            print(f"  {w1:15} ↔ {w2:15} → coh={coh:+.3f}")

    # Fine-tune
    tuner = WaveFineTuner(encoder, learning_rate=1.0)
    history = tuner.fine_tune(kb, epochs=5)

    # Après
    print(f"\nAprès ({len(history['epoch'])} epochs):")
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
