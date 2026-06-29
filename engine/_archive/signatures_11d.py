"""
Signatures Harmoniques 11D — Extension des signatures 9D avec Raisonnement Ondulatoire
=====================================================================================
Ajoute 2 dimensions harmoniques aux 9 dimensions existantes :

10. H_resonance : score de résonance (0-1) entre le message courant et le contexte
    - Élevé = le message « s'accorde » avec ce qui précède
    - Faible = rupture, changement de sujet, dissonance

11. H_coherence : score de cohérence spectrale interne (0-1)
    - Élevé = le message est structurellement harmonieux
    - Faible = contradiction interne, incohérence

Calibration sur φ (1.618...) : les seuils de détection sont espacés par le nombre d'or.
"""
import math
import numpy as np

# =========================================================================
# DIMENSION 10 — H_RESONANCE : Résonance avec le contexte
# =========================================================================

def compute_resonance_np(signature_current, signature_context):
    """
    H_resonance : mesure de l'interférence constructive entre le message
    courant et le contexte conversationnel.
    
    H_res = Σ (S_current[i] * S_context[i]) / (||S_current|| * ||S_context||)
    
    Interprétation :
    - H_res > 0.8  : forte résonance (le message s'inscrit naturellement dans la conversation)
    - 0.5 < H_res < 0.8 : résonance modérée
    - H_res < 0.5  : faible résonance (rupture, nouveau sujet, dissonance)
    
    Args:
        signature_current: np.ndarray [batch, 9] ou [9]
        signature_context: np.ndarray [batch, 9] ou [9]
    
    Returns:
        resonance: float ou np.ndarray [batch, 1] dans [0, 1]
    """
    if signature_current.ndim == 1:
        signature_current = signature_current.reshape(1, -1)
    if signature_context.ndim == 1:
        signature_context = signature_context.reshape(1, -1)
    
    # Normalisation
    norm_current = np.linalg.norm(signature_current, axis=-1, keepdims=True)
    norm_context = np.linalg.norm(signature_context, axis=-1, keepdims=True)
    
    s_norm = signature_current / (norm_current + 1e-8)
    c_norm = signature_context / (norm_context + 1e-8)
    
    # Cosinus de similarité ramené dans [0, 1]
    cosine = np.sum(s_norm * c_norm, axis=-1, keepdims=True)
    resonance = (cosine + 1.0) / 2.0
    
    # Appliquer une pondération phi : les résonances proches de φ⁻¹ (≈0.618)
    # sont amplifiées (point d'équilibre harmonique)
    phi = 1.6180339887
    phi_inv = 1.0 / phi  # ≈ 0.618
    phi_boost = 1.0 - np.abs(resonance - phi_inv)  # pic à φ⁻¹
    phi_boost = np.clip(phi_boost, 0.0, 1.0)
    
    # Mélange : 80% résonance brute + 20% boost φ
    resonance_enhanced = 0.8 * resonance + 0.2 * phi_boost
    
    return np.clip(resonance_enhanced, 0.0, 1.0)


# =========================================================================
# DIMENSION 11 — H_COHERENCE : Cohérence spectrale interne
# =========================================================================

def compute_coherence_np(signature_9d):
    """
    H_coherence : mesure de la cohérence interne du message.
    
    Un message cohérent a ses 9 dimensions équilibrées —
    aucune dimension ne domine excessivement, et la variance
    entre dimensions est faible.
    
    H_coh = 1 - (std_dev / mean) * φ_adjust
    
    Interprétation :
    - H_coh > 0.85 : message très cohérent (spectre équilibré)
    - 0.6 < H_coh < 0.85 : message modérément cohérent
    - H_coh < 0.6 : message incohérent (dimensions déséquilibrées)
    
    Args:
        signature_9d: np.ndarray [batch, 9] ou [9]
    
    Returns:
        coherence: float ou np.ndarray [batch, 1] dans [0, 1]
    """
    if signature_9d.ndim == 1:
        signature_9d = signature_9d.reshape(1, -1)
    
    mean = signature_9d.mean(axis=-1, keepdims=True)
    std = signature_9d.std(axis=-1, keepdims=True)
    
    # Coefficient de variation (CV)
    cv = std / (mean + 1e-8)
    
    # Ajustement phi : le CV est comparé à φ⁻² (≈ 0.382)
    # Un CV de φ⁻² correspond à l'équilibre harmonique idéal
    phi = 1.6180339887
    cv_ideal = 1.0 / (phi * phi)  # ≈ 0.382
    cv_penalty = np.abs(cv - cv_ideal) / cv_ideal
    
    coherence = 1.0 - cv_penalty
    coherence = np.clip(coherence, 0.0, 1.0)
    
    return coherence


# =========================================================================
# FONCTION PRINCIPALE : Signature 11D
# =========================================================================

def compute_signature_11d(hidden_states, signature_context=None):
    """
    Calcule les 11 dimensions harmoniques = 9D + H_resonance + H_coherence.
    
    Args:
        hidden_states: np.ndarray [batch, seq_len, hidden_size]
        signature_context: np.ndarray [batch, 9] ou None
                          Si None, H_resonance = 0.618 (φ⁻¹, point neutre)
    
    Returns:
        signatures: np.ndarray [batch, seq_len, 11]
    """
    # Importer les fonctions 9D existantes
    from engine.signatures_9d import (
        compute_phi_np, compute_alpha_np, compute_reasoning_np,
        compute_creativity_np, compute_math_np, compute_factual_np,
        compute_code_np, compute_emotion_np, compute_temporal_np
    )
    
    # Calcul des 9 dimensions existantes
    phi = compute_phi_np(hidden_states)
    alpha = compute_alpha_np(hidden_states)
    reasoning = compute_reasoning_np(hidden_states)
    creativity = compute_creativity_np(hidden_states)
    math_val = compute_math_np(hidden_states)
    factual = compute_factual_np(hidden_states)
    code = compute_code_np(hidden_states)
    emotion = compute_emotion_np(hidden_states)
    temporal = compute_temporal_np(hidden_states)
    
    # Assemblage 9D
    signatures_9d = np.concatenate([
        phi, alpha, reasoning, creativity, math_val, factual, code,
        emotion, temporal
    ], axis=-1)
    
    # H_COHERENCE (dimension 10)
    # Calculée sur la moyenne des 9D sur la séquence
    seq_mean = signatures_9d.mean(axis=1)  # [batch, 9]
    coherence = compute_coherence_np(seq_mean)  # [batch, 1]
    
    # H_RESONANCE (dimension 11)
    if signature_context is not None:
        resonance = compute_resonance_np(seq_mean, signature_context)
    else:
        # Pas de contexte : résonance par défaut = φ⁻¹ (point neutre)
        resonance = np.ones((hidden_states.shape[0], 1)) * (1.0 / 1.6180339887)
    
    # Étendre à la dimension sequence
    seq_len = hidden_states.shape[1]
    coherence_seq = np.tile(coherence, (1, seq_len, 1))
    resonance_seq = np.tile(resonance, (1, seq_len, 1))
    
    # Assemblage 11D
    signatures_11d = np.concatenate([
        signatures_9d, coherence_seq, resonance_seq
    ], axis=-1)
    
    return signatures_11d


# =========================================================================
# FONCTIONS UTILITAIRES
# =========================================================================

def interpret_resonance(resonance_value):
    """Interprète une valeur de résonance en langage naturel."""
    if resonance_value > 0.85:
        return "forte résonance — parfait accord"
    elif resonance_value > 0.72:
        return "bonne résonance — accord naturel"
    elif resonance_value > 0.618:
        return "résonance équilibrée — point φ⁻¹"
    elif resonance_value > 0.5:
        return "résonance faible — léger décalage"
    elif resonance_value > 0.382:
        return "faible résonance — changement de sujet"
    else:
        return "très faible résonance — rupture de contexte"


def interpret_coherence(coherence_value):
    """Interprète une valeur de cohérence en langage naturel."""
    if coherence_value > 0.90:
        return "excellente cohérence — spectre parfaitement équilibré"
    elif coherence_value > 0.80:
        return "très bonne cohérence — spectre bien équilibré"
    elif coherence_value > 0.65:
        return "bonne cohérence — léger déséquilibre"
    elif coherence_value > 0.50:
        return "cohérence modérée — déséquilibre notable"
    elif coherence_value > 0.35:
        return "faible cohérence — spectre déséquilibré"
    else:
        return "très faible cohérence — incohérence détectée"


def compute_context_signature(conversation_history, window_size=5):
    """
    Calcule une signature de contexte à partir de l'historique de conversation.
    
    Args:
        conversation_history: liste de signatures 9D [n_messages, 9]
        window_size: nombre de messages récents à considérer
    
    Returns:
        context_signature: np.ndarray [9] — signature moyenne du contexte
    """
    if not conversation_history:
        return None
    
    # Prendre les derniers messages
    recent = conversation_history[-window_size:]
    
    # Pondération exponentielle décroissante (plus de poids aux messages récents)
    weights = np.exp(-np.arange(len(recent))[::-1] / 3.0)
    weights = weights / weights.sum()
    
    context = np.average(recent, axis=0, weights=weights)
    return context


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST SIGNATURES 11D — Extension Raisonnement Ondulatoire")
    print("=" * 60)
    
    # Créer des données test
    batch_size = 2
    seq_len = 10
    hidden_size = 64
    
    np.random.seed(42)
    hidden = np.random.randn(batch_size, seq_len, hidden_size)
    
    # Test sans contexte
    sig11 = compute_signature_11d(hidden, signature_context=None)
    print(f"\nShape signature 11D: {sig11.shape}")
    print(f"Dimensions: {sig11.shape[-1]}")
    print(f"Range: [{sig11.min():.3f}, {sig11.max():.3f}]")
    
    # Test avec contexte
    context = np.random.rand(batch_size, 9)
    sig11_ctx = compute_signature_11d(hidden, signature_context=context)
    
    # Moyennes des dimensions
    print("\nMoyennes par dimension (batch 0, derniers tokens):")
    dim_names = ["φ", "α", "raison", "créa", "math", "factuel", "code", "émotion", "temporel", "COHÉR", "RÉSON"]
    mean_vals = sig11_ctx[0, -1, :]
    for name, val in zip(dim_names, mean_vals):
        bar = "█" * int(val * 40)
        print(f"  {name:>8}: {val:.4f} {bar}")
    
    # Test interprétation
    print("\nInterprétation de la cohérence:")
    test_vals = [0.95, 0.82, 0.66, 0.48, 0.30, 0.12]
    for v in test_vals:
        print(f"  {v:.2f} → {interpret_coherence(v)}")
    
    print("\nInterprétation de la résonance:")
    test_vals = [0.90, 0.75, 0.618, 0.52, 0.40, 0.25]
    for v in test_vals:
        print(f"  {v:.2f} → {interpret_resonance(v)}")
    
    print("\n✓ Test signatures 11D réussi!")
    print("=" * 60)