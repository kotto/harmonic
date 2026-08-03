"""
Signatures Harmoniques 9D — Version 4 Robuste (numpy + torch)
==============================================================
Version autonome des signatures harmoniques 9D.
Fonctionne avec numpy PUR (sans torch) par defaut,
mais supporte aussi les tenseurs torch.

Les 9 dimensions (chacune dans [0,1]) :
1. phi        : entropie normalisee (diversite)
2. alpha      : rugosite fractale (complexite)
3. reasoning  : coherence causale
4. creativity : divergence semantique
5. math       : periodicite numerique
6. factual    : ancrage/confiance factuelle
7. code       : structure hierarchique
8. emotion    : charge emotionnelle
9. temporal   : ancrage temporel
"""

import math
import numpy as np


# =========================================================================
# DETECTION AUTO : numpy vs torch
# =========================================================================

def _is_tensor(x):
    """Detecte si x est un tenseur torch ou numpy."""
    return hasattr(x, 'device') and hasattr(x, 'requires_grad')

def _to_numpy(x):
    """Convertit en numpy si c'est un tenseur."""
    if _is_tensor(x):
        return x.detach().cpu().numpy()
    return x


# =========================================================================
# FONCTIONS 9D — Version numpy native
# =========================================================================

def compute_phi_np(hidden_states):
    """
    phi : entropie normalisee.
    phi = 1 - max(softmax(x))
    Garantie : phi ∈ [0, 1]
    """
    # Softmax manuel (stable)
    e_x = np.exp(hidden_states - hidden_states.max(axis=-1, keepdims=True))
    p = e_x / (e_x.sum(axis=-1, keepdims=True) + 1e-10)
    max_p = p.max(axis=-1, keepdims=True)
    phi = 1.0 - max_p
    return phi


def compute_alpha_np(hidden_states):
    """
    alpha : rugosite fractale.
    alpha = mean(1 - cos(x_i, x_{i+lag})) / 2
    Garantie : alpha ∈ [0, 1]
    """
    eps = 1e-8
    norm = np.linalg.norm(hidden_states, axis=-1, keepdims=True)
    x_norm = hidden_states / (norm + eps)
    
    rugosites = []
    for lag in [1, 2, 3]:
        if lag >= hidden_states.shape[1]:
            continue
        cos_lag = np.sum(x_norm[:, :-lag] * x_norm[:, lag:], axis=-1, keepdims=True)
        # Padding
        pad_width = ((0, 0), (0, lag), (0, 0))
        cos_lag = np.pad(cos_lag, pad_width)
        rug = 1.0 - cos_lag
        rugosites.append(rug)
    
    if rugosites:
        alpha = np.mean(np.stack(rugosites, axis=-1), axis=-1)
    else:
        alpha = np.zeros_like(hidden_states[..., :1])
    
    alpha = alpha / 2.0  # Ramener dans [0, 1]
    return alpha


def compute_reasoning_np(hidden_states):
    """
    reasoning : coherence causale.
    R = (cos(x_i, x_{i+1}) + 1) / 2
    Garantie : R ∈ [0, 1]
    """
    eps = 1e-8
    norm = np.linalg.norm(hidden_states, axis=-1, keepdims=True)
    x_norm = hidden_states / (norm + eps)
    
    cos_sim = np.sum(x_norm[:, :-1] * x_norm[:, 1:], axis=-1, keepdims=True)
    pad_width = ((0, 0), (0, 1), (0, 0))
    cos_sim = np.pad(cos_sim, pad_width)
    reasoning = (cos_sim + 1.0) / 2.0
    return reasoning


def compute_creativity_np(hidden_states):
    """
    creativity : divergence semantique.
    C = 1 - max_{j!=i} (cos(x_i, x_j) + 1) / 2
    Garantie : C ∈ [0, 1]
    """
    batch, seq_len, _ = hidden_states.shape
    eps = 1e-8
    
    norm = np.linalg.norm(hidden_states, axis=-1, keepdims=True)
    x_norm = hidden_states / (norm + eps)
    
    # Matrice de similarite
    sim_matrix = np.matmul(x_norm, x_norm.transpose(0, 2, 1))
    sim_matrix = (sim_matrix + 1.0) / 2.0
    
    # Masquer la diagonale
    mask = np.eye(seq_len).reshape(1, seq_len, seq_len)
    sim_matrix = sim_matrix * (1.0 - mask)
    
    max_sim = sim_matrix.max(axis=-1, keepdims=True)
    creativity = 1.0 - max_sim
    return creativity


def compute_math_np(hidden_states):
    """
    math : precision numerique / periodicite.
    M = max(autocorrelation(x, lag)) pour lag > 0
    Garantie : M ∈ [0, 1]
    """
    eps = 1e-8
    norm = np.linalg.norm(hidden_states, axis=-1, keepdims=True)
    x_norm = hidden_states / (norm + eps)
    
    autocorrs = []
    for lag in [1, 2, 3, 4]:
        if lag >= hidden_states.shape[1]:
            continue
        pad_width = ((0, 0), (lag, 0), (0, 0))
        shifted = np.pad(x_norm[:, :-lag], pad_width)
        ac = np.sum(x_norm * shifted, axis=-1, keepdims=True)
        autocorrs.append(ac)
    
    if autocorrs:
        math_val = np.stack(autocorrs, axis=-1).max(axis=-1)
    else:
        math_val = np.zeros_like(hidden_states[..., :1])
    
    math_val = (math_val + 1.0) / 2.0
    return math_val


def compute_factual_np(hidden_states):
    """
    factual : ancrage factuel / confiance.
    F = 1 - variance(softmax(x)) normalisee
    Garantie : F ∈ [0, 1]
    """
    e_x = np.exp(hidden_states - hidden_states.max(axis=-1, keepdims=True))
    p = e_x / (e_x.sum(axis=-1, keepdims=True) + 1e-10)
    
    var_p = p.var(axis=-1, keepdims=True)
    var_max = 0.25
    factual = 1.0 - np.clip(var_p / var_max, 0.0, 1.0)
    return factual


def compute_code_np(hidden_states):
    """
    code : structure hierarchique.
    C = sigmoid(ratio_basses_frequences - 1)
    Garantie : C ∈ [0, 1]
    """
    hidden = hidden_states
    
    # Filtre moyenneur (basses frequences)
    low_freq = np.zeros_like(hidden)
    if hidden.shape[1] >= 3:
        low_freq[:, 1:-1, :] = (hidden[:, :-2, :] + 2 * hidden[:, 1:-1, :] + hidden[:, 2:, :]) / 4.0
    low_freq[:, 0, :] = (2 * hidden[:, 0, :] + hidden[:, 1, :]) / 3.0 if hidden.shape[1] > 1 else hidden[:, 0, :]
    if hidden.shape[1] > 1:
        low_freq[:, -1, :] = (hidden[:, -2, :] + 2 * hidden[:, -1, :]) / 3.0
    
    high_freq = hidden - low_freq
    
    low_norm = np.linalg.norm(low_freq, axis=-1, keepdims=True)
    high_norm = np.linalg.norm(high_freq, axis=-1, keepdims=True)
    
    ratio = low_norm / (high_norm + 1e-8)
    code = 1.0 / (1.0 + np.exp(-(ratio - 1.0)))  # sigmoid
    return code


def compute_emotion_np(hidden_states):
    """
    emotion : charge emotionnelle.
    E = tanh(|skewness|) * (1 - 0.5 * sigmoid(kurtosis_exces))
    Garantie : E ∈ [0, 1]
    """
    mean = hidden_states.mean(axis=1, keepdims=True)
    x_centre = hidden_states - mean
    
    m2 = np.mean(x_centre ** 2, axis=-1, keepdims=True)
    m3 = np.mean(x_centre ** 3, axis=-1, keepdims=True)
    skewness = m3 / (m2 ** 1.5 + 1e-8)
    
    m4 = np.mean(x_centre ** 4, axis=-1, keepdims=True)
    kurtosis = m4 / (m2 ** 2 + 1e-8) - 3.0
    
    skew_norm = np.tanh(np.abs(skewness))
    kurt_norm = 1.0 / (1.0 + np.exp(-kurtosis))  # sigmoid
    
    emotion = skew_norm * (1.0 - 0.5 * kurt_norm)
    return emotion


def compute_temporal_np(hidden_states):
    """
    temporal : ancrage temporel.
    T = (1 - cos(x_i, x_{i+1})) / 2
    Garantie : T ∈ [0, 1]
    """
    eps = 1e-8
    norm = np.linalg.norm(hidden_states, axis=-1, keepdims=True)
    x_norm = hidden_states / (norm + eps)
    
    cos_sim = np.sum(x_norm[:, :-1] * x_norm[:, 1:], axis=-1, keepdims=True)
    pad_width = ((0, 0), (0, 1), (0, 0))
    cos_sim = np.pad(cos_sim, pad_width)
    
    variation = 1.0 - cos_sim
    temporal = variation / 2.0
    return temporal


# =========================================================================
# PROJECTION DE SIGNATURE 9D (numpy native)
# =========================================================================

def compute_signature_9d(hidden_states):
    """
    Calcule les 9 dimensions harmoniques.
    
    Args:
        hidden_states: np.ndarray [batch, seq_len, hidden_size]
    
    Returns:
        signatures: np.ndarray [batch, seq_len, 9]
    """
    phi = compute_phi_np(hidden_states)
    alpha = compute_alpha_np(hidden_states)
    reasoning = compute_reasoning_np(hidden_states)
    creativity = compute_creativity_np(hidden_states)
    math_val = compute_math_np(hidden_states)
    factual = compute_factual_np(hidden_states)
    code = compute_code_np(hidden_states)
    emotion = compute_emotion_np(hidden_states)
    temporal = compute_temporal_np(hidden_states)
    
    signatures = np.concatenate([
        phi, alpha, reasoning, creativity, math_val, factual, code,
        emotion, temporal
    ], axis=-1)
    
    return signatures


# =========================================================================
# WRAPPER TORCH (si disponible)
# =========================================================================

def compute_signature_9d_torch(hidden_states):
    """
    Version torch des signatures 9D.
    
    Args:
        hidden_states: torch.Tensor [batch, seq_len, hidden_size]
    
    Returns:
        signatures: torch.Tensor [batch, seq_len, 9]
    """
    import torch
    import torch.nn.functional as F
    
    # Phi : entropie normalisee
    d = hidden_states.shape[-1]
    tau = math.sqrt(d)
    p = F.softmax(hidden_states / tau, dim=-1)
    max_p = p.max(dim=-1, keepdim=True)[0]
    phi = 1.0 - max_p
    
    # Alpha : rugosite fractale
    x_norm = F.normalize(hidden_states, dim=-1)
    rugosites = []
    for lag in [1, 2, 3]:
        if lag >= hidden_states.shape[1]:
            continue
        cos_lag = (x_norm[:, :-lag] * x_norm[:, lag:]).sum(dim=-1, keepdim=True)
        cos_lag = F.pad(cos_lag, (0, 0, 0, lag))
        rug = 1.0 - cos_lag
        rugosites.append(rug)
    if rugosites:
        alpha = torch.stack(rugosites, dim=-1).mean(dim=-1) / 2.0
    else:
        alpha = torch.zeros_like(hidden_states[..., :1])
    
    # Reasoning : coherence causale
    cos_sim = (x_norm[:, :-1] * x_norm[:, 1:]).sum(dim=-1, keepdim=True)
    cos_sim = F.pad(cos_sim, (0, 0, 0, 1))
    reasoning = (cos_sim + 1.0) / 2.0
    
    # Creativity : divergence semantique
    batch, seq_len, _ = hidden_states.shape
    sim_matrix = torch.bmm(x_norm, x_norm.transpose(1, 2))
    sim_matrix = (sim_matrix + 1.0) / 2.0
    mask = torch.eye(seq_len, device=hidden_states.device).unsqueeze(0)
    sim_matrix = sim_matrix * (1.0 - mask)
    max_sim = sim_matrix.max(dim=-1)[0].unsqueeze(-1)
    creativity = 1.0 - max_sim
    
    # Math : periodicite
    autocorrs = []
    for lag in [1, 2, 3, 4]:
        if lag >= hidden_states.shape[1]:
            continue
        shifted = F.pad(x_norm[:, :-lag], (0, 0, lag, 0))
        ac = (x_norm * shifted).sum(dim=-1, keepdim=True)
        autocorrs.append(ac)
    if autocorrs:
        math_val = torch.stack(autocorrs, dim=-1).max(dim=-1)[0]
    else:
        math_val = torch.zeros_like(hidden_states[..., :1])
    math_val = (math_val + 1.0) / 2.0
    
    # Factual : confiance
    p = F.softmax(hidden_states / math.sqrt(d), dim=-1)
    var_p = p.var(dim=-1, keepdim=True)
    var_max = 0.25
    factual = 1.0 - torch.clamp(var_p / var_max, 0.0, 1.0)
    
    # Code : structure hierarchique
    hidden = hidden_states
    low_freq = torch.zeros_like(hidden)
    if hidden.shape[1] >= 3:
        low_freq[:, 1:-1, :] = (hidden[:, :-2, :] + 2 * hidden[:, 1:-1, :] + hidden[:, 2:, :]) / 4.0
    low_freq[:, 0, :] = (2 * hidden[:, 0, :] + hidden[:, 1, :]) / 3.0 if hidden.shape[1] > 1 else hidden[:, 0, :]
    if hidden.shape[1] > 1:
        low_freq[:, -1, :] = (hidden[:, -2, :] + 2 * hidden[:, -1, :]) / 3.0
    high_freq = hidden - low_freq
    low_norm = torch.norm(low_freq, dim=-1, keepdim=True)
    high_norm = torch.norm(high_freq, dim=-1, keepdim=True)
    ratio = low_norm / (high_norm + 1e-8)
    code = torch.sigmoid(ratio - 1.0)
    
    # Emotion : charge emotionnelle
    mean = hidden_states.mean(dim=1, keepdim=True)
    x_centre = hidden_states - mean
    m2 = (x_centre ** 2).mean(dim=-1, keepdim=True)
    m3 = (x_centre ** 3).mean(dim=-1, keepdim=True)
    skewness = m3 / (m2 ** 1.5 + 1e-8)
    m4 = (x_centre ** 4).mean(dim=-1, keepdim=True)
    kurtosis = m4 / (m2 ** 2 + 1e-8) - 3.0
    skew_norm = torch.tanh(torch.abs(skewness))
    kurt_norm = torch.sigmoid(kurtosis)
    emotion = skew_norm * (1.0 - 0.5 * kurt_norm)
    
    # Temporal : variation temporelle
    cos_sim = (x_norm[:, :-1] * x_norm[:, 1:]).sum(dim=-1, keepdim=True)
    cos_sim = F.pad(cos_sim, (0, 0, 0, 1))
    variation = 1.0 - cos_sim
    temporal = variation / 2.0
    
    signatures = torch.cat([
        phi, alpha, reasoning, creativity, math_val, factual, code,
        emotion, temporal
    ], dim=-1)
    
    return signatures


# =========================================================================
# FONCTION UNIFIE (auto-detect)
# =========================================================================

def compute_signature(hidden_states):
    """
    Calcule les signatures 9D (auto-detect numpy ou torch).
    
    Args:
        hidden_states: np.ndarray ou torch.Tensor [batch, seq_len, hidden_size]
    
    Returns:
        signatures: meme type que l'entree [batch, seq_len, 9]
    """
    if _is_tensor(hidden_states):
        return compute_signature_9d_torch(hidden_states)
    else:
        if not isinstance(hidden_states, np.ndarray):
            hidden_states = np.array(hidden_states)
        return compute_signature_9d(hidden_states)


# =========================================================================
# VALIDATION
# =========================================================================

SIGNATURE_DIMS = [
    'phi', 'alpha', 'reasoning', 'creativity',
    'math', 'factual', 'code', 'emotion', 'temporal'
]


def validate_signatures(signatures):
    """Verifie que les signatures sont valides."""
    assert signatures.shape[-1] == 9, f"Attendu 9 dims, recu {signatures.shape[-1]}"
    s_min = signatures.min()
    s_max = signatures.max()
    assert s_min >= 0.0, f"Valeur negative trouvee: {s_min}"
    assert s_max <= 1.0, f"Valeur > 1 trouvee: {s_max}"
    return True


def demo_signatures():
    """Demonstration rapide des signatures 9D."""
    print("=" * 70)
    print("DEMO : Signatures Harmoniques 9D")
    print("=" * 70)
    
    # Creer des embeddings fictifs
    batch, seq_len, hidden = 3, 10, 64
    np.random.seed(42)
    
    # Different types d'embeddings
    embeddings = np.random.randn(batch, seq_len, hidden).astype(np.float32)
    
    sig = compute_signature(embeddings)
    validate_signatures(sig)
    
    print(f"\nEntree : {embeddings.shape}")
    print(f"Signatures : {sig.shape}")
    
    print(f"\nProfils moyens (sur {seq_len} tokens) :")
    print(f"{'Batch':<8} ", end="")
    for d in SIGNATURE_DIMS:
        print(f"{d[:4]:>6}", end=" ")
    print()
    print("-" * (8 + 9 * 7))
    
    for i in range(batch):
        profile = sig[i].mean(axis=0)
        print(f"{'B'+str(i):<8} ", end="")
        for j in range(9):
            print(f"{profile[j]:6.3f}", end=" ")
        print()
    
    print("\n[OK] Signatures 9D operationnelles (numpy native)")
    return sig


if __name__ == '__main__':
    demo_signatures()
