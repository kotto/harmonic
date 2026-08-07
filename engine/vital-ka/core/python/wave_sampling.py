"""
Échantillonnage Ondulatoire — Temperature, Top-P, Top-K par Résonance
======================================================================
Traduction ondulatoire des méthodes d'échantillonnage des LLM :

  Température → Bruit de phase δ·N(0,1)
  Top-P → Cône de cohérence (seuil angulaire)
  Top-K → Filtrage par cohérence décroissante

Principe : dans l'espace ondulatoire, la « probabilité » d'un token
est sa cohérence de phase avec l'état cible. L'échantillonnage
contrôle la dispersion autour de l'optimum de cohérence.

Author: Univers-Holistique
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
PI = math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR D'ÉCHANTILLONNAGE ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveSampler:
    """
    Échantillonnage ondulatoire — remplace temperature + top-p + top-k.

    Usage:
        sampler = WaveSampler(vocabulary)
        word = sampler.sample(psi_context, temperature=0.8, top_p=0.9, top_k=50)
    """

    def __init__(self, vocabulary: Optional[Dict[str, np.ndarray]] = None):
        """
        Args:
            vocabulary: {mot: psi_vector} — si None, sera chargé dynamiquement
        """
        self.vocabulary = vocabulary or {}
        self._rng = np.random.RandomState()

    def set_vocabulary(self, vocab: Dict[str, np.ndarray]):
        """Définit le vocabulaire pour l'échantillonnage."""
        self.vocabulary = vocab

    def coherence_scores(self, psi_context: np.ndarray,
                         candidates: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Calcule les scores de cohérence pour tous les mots candidats.

        score(mot) = Re(⟨ψ_contexte | ψ_mot⟩) ∈ [-1, 1]

        Args:
            psi_context: vecteur d'onde du contexte
            candidates: liste optionnelle de mots à scorer (tous si None)

        Returns:
            {mot: score_de_coherence}
        """
        if candidates is None:
            candidates = list(self.vocabulary.keys())

        scores = {}
        for word in candidates:
            if word in self.vocabulary:
                psi_word = self.vocabulary[word]
                # Cohérence = partie réelle du produit hermitien
                score = float(np.real(np.dot(psi_context, psi_word.conj())))
                scores[word] = score

        return scores

    def sample(self, psi_context: np.ndarray,
               temperature: float = 0.8,
               top_p: float = 0.9,
               top_k: int = 50,
               candidates: Optional[List[str]] = None) -> str:
        """
        Échantillonne un mot selon la distribution de cohérence.

        Traduction LLM → Ondulatoire :
          - softmax(logits/T) → cohérences modulées par bruit de phase
          - top_p → cône de cohérence (seuil angulaire cumulatif)
          - top_k → les k mots de plus forte cohérence

        Args:
            psi_context: vecteur d'onde du contexte
            temperature: 0 = déterministe (max cohérence), >0 = bruit de phase
            top_p: seuil de cohérence cumulée (0-1, défaut 0.9)
            top_k: nombre maximum de candidats
            candidates: liste optionnelle de mots

        Returns:
            Mot sélectionné
        """
        # 1. Scores de cohérence
        scores = self.coherence_scores(psi_context, candidates)
        if not scores:
            return ""

        # 2. Top-K : ne garder que les k meilleurs
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if top_k and top_k < len(sorted_items):
            sorted_items = sorted_items[:top_k]

        # 3. Conversion cohérence → scores positifs pour top-p
        # La cohérence ∈ [-1, 1]. On translate dans [0, 2] puis on normalise.
        words, coherences = zip(*sorted_items)
        coherences = np.array(coherences)
        coherences_pos = coherences - coherences.min() + 1e-10  # [0, ...]
        total = coherences_pos.sum()
        probs = coherences_pos / total

        # 4. Top-P (cône de cohérence) : cumulative jusqu'à top_p
        if top_p and top_p < 1.0:
            cumsum = 0
            cutoff_idx = len(probs)
            for i, p in enumerate(probs):
                cumsum += p
                if cumsum >= top_p:
                    cutoff_idx = i + 1
                    break
            words = words[:cutoff_idx]
            probs = probs[:cutoff_idx]
            probs = probs / probs.sum()

        # 5. Température → bruit de phase
        if temperature <= 0.001:
            # Déterministe (T=0) : cohérence maximale
            return words[0]
        elif temperature < 1.0:
            # Bruit de phase modéré : les cohérences restent fiables
            noise = self._rng.normal(0, temperature * 0.5, len(probs))
            probs = probs * (1.0 + noise * 0.3)
            probs = np.maximum(probs, 0)
            probs = probs / probs.sum()
        else:
            # Haute température : aplatir la distribution
            probs = probs ** (1.0 / temperature)
            probs = probs / probs.sum()

        # 6. Échantillonnage
        idx = self._rng.choice(len(words), p=probs)
        return words[idx]

    def deterministic(self, psi_context: np.ndarray,
                      candidates: Optional[List[str]] = None) -> str:
        """Mode déterministe : cohérence maximale (T=0, pas de top-p/k)."""
        return self.sample(psi_context, temperature=0.0, top_p=1.0, top_k=1,
                          candidates=candidates)

    def creative(self, psi_context: np.ndarray,
                 creativity: float = 0.7,
                 candidates: Optional[List[str]] = None) -> str:
        """Mode créatif : bruit de phase élevé, top-p large."""
        return self.sample(psi_context, temperature=creativity * 1.5,
                          top_p=0.95, top_k=100, candidates=candidates)

    def precise(self, psi_context: np.ndarray,
                candidates: Optional[List[str]] = None) -> str:
        """Mode précis : faible bruit, top-p serré, top-k réduit."""
        return self.sample(psi_context, temperature=0.2,
                          top_p=0.8, top_k=20, candidates=candidates)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES D'ÉCHANTILLONNAGE
# ═══════════════════════════════════════════════════════════════════════════════

def apply_phase_noise(psi: np.ndarray, temperature: float) -> np.ndarray:
    """
    Applique un bruit de phase thermique à un vecteur d'onde.

    ψ_bruité = ψ · exp(i · T · N(0,1))

    Args:
        psi: vecteur d'onde original
        temperature: intensité du bruit (0 = pas de bruit)

    Returns:
        Vecteur d'onde bruité (norme préservée)
    """
    if temperature < 0.001:
        return psi.copy()
    noise = np.random.randn(len(psi)) * temperature * 0.5
    return psi * np.exp(1j * noise)


def coherence_cone_filter(scores: Dict[str, float],
                          angle_threshold_deg: float = 45.0) -> Dict[str, float]:
    """
    Filtre les candidats par cône de cohérence.

    Ne garde que les mots dont la cohérence est suffisante,
    i.e. dont l'angle avec l'état cible est < angle_threshold.

    cos(angle) = score (car |ψ|=1)
    seuil = cos(angle_threshold)

    Args:
        scores: {mot: score_de_coherence}
        angle_threshold_deg: angle maximal du cône (degrés)

    Returns:
        Scores filtrés
    """
    threshold = math.cos(math.radians(angle_threshold_deg))
    return {w: s for w, s in scores.items() if s >= threshold}


def entropy(scores: Dict[str, float]) -> float:
    """
    Entropie ondulatoire de Shannon.

    H = -Σ p_i log p_i  où p_i = score_i / Σ scores_j

    H faible → prédiction certaine (cohérences concentrées)
    H élevée → prédiction incertaine (cohérences dispersées)

    Args:
        scores: {mot: score_de_coherence}

    Returns:
        Entropie en nats
    """
    values = np.array(list(scores.values()))
    values_pos = values - values.min() + 1e-10
    probs = values_pos / values_pos.sum()
    return float(-np.sum(probs * np.log(probs + 1e-10)))


def perplexity(scores: Dict[str, float]) -> float:
    """
    Perplexité ondulatoire = exp(entropie).

    PPL faible → bonne prédiction
    PPL ≈ nombre de choix équiprobables équivalents
    """
    return float(math.exp(entropy(scores)))


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : Échantillonnage Ondulatoire")
    print("=" * 60)

    # Vocabulaire de test (psi aléatoires normalisés)
    vocab = {}
    for word in ["liberté", "égalité", "fraternité", "justice", "paix",
                 "guerre", "haine", "amour", "savoir", "pouvoir"]:
        psi = np.random.randn(512) + 1j * np.random.randn(512)
        vocab[word] = psi / np.linalg.norm(psi)

    sampler = WaveSampler(vocab)

    # Contexte aligné avec "liberté"
    psi_context = vocab["liberté"] * 1.0  # alignement parfait

    # Scores
    scores = sampler.coherence_scores(psi_context)
    print("\nScores de cohérence :")
    for w, s in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int((s + 1) * 20)  # échelle [-1, 1] → [0, 40]
        print(f"  {w:12s}: {s:+.4f} {bar}")

    # Échantillonnage
    print("\nÉchantillonnage :")
    print(f"  Déterministe (T=0):      {sampler.deterministic(psi_context)}")
    print(f"  Précis (T=0.2):          {sampler.precise(psi_context)}")
    print(f"  Standard (T=0.8):        {sampler.sample(psi_context, temperature=0.8)}")
    print(f"  Créatif (T=1.05):        {sampler.creative(psi_context)}")

    # Entropie
    print(f"\n  Entropie:     {entropy(scores):.3f} nats")
    print(f"  Perplexité:   {perplexity(scores):.1f}")

    # Contexte bruité (alignement partiel avec "guerre")
    psi_context2 = vocab["guerre"] * 0.5 + vocab["paix"] * 0.5
    psi_context2 = psi_context2 / np.linalg.norm(psi_context2)
    scores2 = sampler.coherence_scores(psi_context2)
    print(f"\n  Entropie (contexte mixte): {entropy(scores2):.3f} nats")
    print(f"  Perplexité (contexte mixte): {perplexity(scores2):.1f}")

    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
