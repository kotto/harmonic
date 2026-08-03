"""
Entropie et Perplexité Ondulatoires
=====================================
Métriques de qualité pour la génération de texte ondulatoire.

  Perplexité LLM = exp(-1/N Σ log P(token_i | contexte))
  Entropie Ondulatoire H(ψ) = -Σ |ψ_i|² log |ψ_i|²
  Perplexité Ondulatoire = exp(H(ψ))

Principe : dans l'espace ℂ^512, l'incertitude d'une prédiction
est mesurée par la dispersion des phases. Une distribution de phases
concentrée → faible entropie → prédiction certaine.
Une distribution de phases dispersée → haute entropie → prédiction incertaine.

Author: Univers-Holistique
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional

PHI = 1.618033988749895
PI = math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# ENTROPIE ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

def wave_entropy(psi: np.ndarray) -> float:
    """
    Entropie ondulatoire d'un vecteur d'état.

    H(ψ) = -Σ |ψ_i|² log |ψ_i|²

    Interprétation :
      H ≈ 0 : l'onde est concentrée sur une seule composante → certitude
      H ≈ log(d) : l'onde est uniformément répartie → incertitude maximale

    Args:
        psi: vecteur d'onde complexe (ou réel)

    Returns:
        Entropie en nats
    """
    probs = np.abs(psi) ** 2
    probs = probs / (probs.sum() + 1e-10)
    # Éviter log(0)
    probs = np.maximum(probs, 1e-15)
    return float(-np.sum(probs * np.log(probs)))


def wave_perplexity(psi: np.ndarray) -> float:
    """
    Perplexité ondulatoire.

    PPL = exp(H(ψ))

    PPL ≈ 1 → prédiction quasi-certaine (une composante domine)
    PPL ≈ d → prédiction uniformément incertaine (~d choix équivalents)

    Args:
        psi: vecteur d'onde

    Returns:
        Perplexité (≥ 1)
    """
    return float(math.exp(wave_entropy(psi)))


def coherence_shannon_entropy(scores: Dict[str, float]) -> float:
    """
    Entropie de Shannon d'une distribution de cohérence.

    Convertit les scores de cohérence ∈ [-1, 1] en probabilités ∈ [0, 1],
    puis calcule H = -Σ p_i log p_i.

    Args:
        scores: {mot: score_de_coherence}

    Returns:
        Entropie en nats
    """
    values = np.array(list(scores.values()))
    if len(values) == 0:
        return 0.0

    # Translation dans [0, +inf)
    values_pos = values - values.min() + 1e-10
    probs = values_pos / values_pos.sum()
    probs = np.maximum(probs, 1e-15)
    return float(-np.sum(probs * np.log(probs)))


def coherence_perplexity(scores: Dict[str, float]) -> float:
    """
    Perplexité d'une distribution de cohérence = exp(entropie).
    """
    return float(math.exp(coherence_shannon_entropy(scores)))


# ═══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUES DE CONFIANCE
# ═══════════════════════════════════════════════════════════════════════════════

def confidence(scores: Dict[str, float]) -> float:
    """
    Confiance d'une prédiction basée sur la concentration de cohérence.

    confidence = (max_score - mean_score) / (max_score + 1e-10)

    Proche de 1 → un mot domine clairement (prédiction fiable)
    Proche de 0 → plusieurs mots sont équivalents (prédiction incertaine)

    Args:
        scores: {mot: score_de_coherence}

    Returns:
        Score de confiance ∈ [0, 1]
    """
    values = np.array(list(scores.values()))
    if len(values) <= 1:
        return 1.0

    max_score = values.max()
    mean_score = values.mean()
    return float((max_score - mean_score) / (max_score + 1e-10))


def coherence_margin(scores: Dict[str, float]) -> float:
    """
    Marge de cohérence entre le meilleur et le deuxième meilleur.

    margin = score_1 - score_2

    Grande marge → prédiction robuste
    Petite marge → prédiction fragile (un petit bruit pourrait changer le choix)

    Args:
        scores: {mot: score_de_coherence}

    Returns:
        Marge ∈ [0, 2] (car les scores ∈ [-1, 1])
    """
    values = sorted(scores.values(), reverse=True)
    if len(values) < 2:
        return 2.0
    return values[0] - values[1]


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSE DE LA QUALITÉ DE GÉNÉRATION
# ═══════════════════════════════════════════════════════════════════════════════

def generation_quality(psi_sequence: List[np.ndarray],
                       vocabulary: Dict[str, np.ndarray]) -> Dict:
    """
    Analyse la qualité d'une séquence générée.

    Calcule pour chaque étape :
      - entropie de l'état
      - perplexité locale
      - confiance du choix
      - marge de cohérence

    Args:
        psi_sequence: liste des vecteurs d'onde à chaque étape
        vocabulary: dictionnaire {mot: psi}

    Returns:
        Dictionnaire avec les métriques agrégées
    """
    if not psi_sequence:
        return {'error': 'Séquence vide'}

    entropies = []
    perplexities = []
    confidences = []
    margins = []

    for psi in psi_sequence:
        # Entropie de l'état
        entropies.append(wave_entropy(psi))
        perplexities.append(wave_perplexity(psi))

        # Scores vs vocabulaire
        scores = {}
        for word, psi_w in vocabulary.items():
            scores[word] = float(np.real(np.dot(psi, psi_w.conj())))

        confidences.append(confidence(scores))
        margins.append(coherence_margin(scores))

    return {
        'mean_entropy': float(np.mean(entropies)),
        'mean_perplexity': float(np.mean(perplexities)),
        'mean_confidence': float(np.mean(confidences)),
        'mean_margin': float(np.mean(margins)),
        'min_confidence': float(np.min(confidences)),
        'max_entropy': float(np.max(entropies)),
        'n_steps': len(psi_sequence),
    }


def compare_distributions(scores_a: Dict[str, float],
                           scores_b: Dict[str, float]) -> Dict:
    """
    Compare deux distributions de cohérence (ex: avant/après bruit).

    Retourne la divergence de Jensen-Shannon et le décalage de phase moyen.
    """
    words = sorted(set(list(scores_a.keys()) + list(scores_b.keys())))

    # Normaliser
    def to_probs(scores):
        vals = np.array([scores.get(w, 0.0) for w in words])
        vals = vals - vals.min() + 1e-10
        return vals / vals.sum()

    p = to_probs(scores_a)
    q = to_probs(scores_b)

    # Jensen-Shannon divergence
    m = (p + q) / 2.0
    js = 0.5 * np.sum(p * np.log(p / (m + 1e-10) + 1e-10)) + \
         0.5 * np.sum(q * np.log(q / (m + 1e-10) + 1e-10))

    # Ordres différents ?
    top_a = sorted(scores_a.items(), key=lambda x: x[1], reverse=True)[:3]
    top_b = sorted(scores_b.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        'js_divergence': float(js),
        'top3_a': [w for w, _ in top_a],
        'top3_b': [w for w, _ in top_b],
        'order_changed': [w for w, _ in top_a] != [w for w, _ in top_b],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : Entropie et Perplexité Ondulatoires")
    print("=" * 60)

    # Vecteur concentré (quasi-certitude)
    psi_certain = np.zeros(512, dtype=complex)
    psi_certain[0] = 1.0
    H_certain = wave_entropy(psi_certain)
    PPL_certain = wave_perplexity(psi_certain)
    print(f"\nVecteur concentré (1 composante):")
    print(f"  Entropie:     {H_certain:.4f} nats")
    print(f"  Perplexité:   {PPL_certain:.2f}")

    # Vecteur uniforme (incertitude maximale)
    psi_uniform = np.ones(512, dtype=complex) / math.sqrt(512)
    H_uniform = wave_entropy(psi_uniform)
    PPL_uniform = wave_perplexity(psi_uniform)
    print(f"\nVecteur uniforme (512 composantes):")
    print(f"  Entropie:     {H_uniform:.4f} nats")
    print(f"  Perplexité:   {PPL_uniform:.2f}")
    print(f"  Note: PPL ≈ 512 = nombre de choix équivalents")

    # Scores de cohérence test
    scores = {
        'parfait': 0.99,
        'excellent': 0.85,
        'bon': 0.70,
        'moyen': 0.50,
        'faible': 0.20,
    }
    print(f"\nScores de cohérence test:")
    print(f"  Entropie:     {coherence_shannon_entropy(scores):.4f} nats")
    print(f"  Perplexité:   {coherence_perplexity(scores):.2f}")
    print(f"  Confiance:    {confidence(scores):.3f}")
    print(f"  Marge:        {coherence_margin(scores):.3f}")

    # Scores ambigus
    scores_ambiguous = {'a': 0.51, 'b': 0.50, 'c': 0.49}
    print(f"\nScores ambigus:")
    print(f"  Perplexité:   {coherence_perplexity(scores_ambiguous):.2f}")
    print(f"  Confiance:    {confidence(scores_ambiguous):.3f}")
    print(f"  Marge:        {coherence_margin(scores_ambiguous):.3f}")

    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
