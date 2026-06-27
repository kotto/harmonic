"""
Attention Harmonique PURE
=========================
ZERO parametre entrainable dans l'attention.

Principe :
1. Les signatures 7D sont calculees par des formules fermees deterministes
   (pas de projection apprise)
2. La matrice de resonance R = sigmas @ sigmas.T remplace completement QK^T
3. Le noyau ABC (derivee fractionnaire) pondere la memoire non-locale
4. Les "valeurs" sont les hidden states eux-memes (pas de projection V)
5. La sortie est une somme ponderee des hidden states par les poids harmoniques

Architecture :
    scores[i,j] = resonance[i,j] * abc_weights[i-j]  (causal)
    output[i] = sum_j softmax(scores[i,:])_j * hidden_states[j]

Constantes deterministes :
    - PHI = 1.618033988749895 (nombre d'or)
    - ALPHA = 1/PHI = 0.618033988749895
    - B_1_PHI = 0.8506508083
    - Les 7 dimensions sont des fonctions analytiques des hidden states
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.abc_kernel import ABCKernel, ALPHA, B_1_PHI, PHI


# =========================================================================
# FONCTIONS DE SIGNATURE DETERMINISTES (formules fermees)
# =========================================================================

def compute_phi(hidden_states):
    """
    Dimension phi : diversite/entropie de la representation.
    
    Formule fermee : entropie de Shannon normalisee de la distribution
    d'activation sur les dimensions cachees.
    
    phi(x) = -sum_k p_k * log(p_k + eps) / log(d)
    ou p_k = softmax(x_k / tau) et tau = sqrt(d)
    
    Args:
        hidden_states: [batch, seq_len, hidden_size]
    Returns:
        phi: [batch, seq_len, 1] dans [0, 1]
    """
    d = hidden_states.shape[-1]
    tau = math.sqrt(d)
    
    # Distribution d'activation normalisee
    p = F.softmax(hidden_states / tau, dim=-1)  # [B, S, D]
    
    # Entropie de Shannon normalisee
    log_p = torch.log(p + 1e-10)
    entropy = -torch.sum(p * log_p, dim=-1)  # [B, S]
    entropy = entropy / math.log(d)  # normalise dans [0, 1]
    
    return entropy.unsqueeze(-1)  # [B, S, 1]


def compute_alpha(hidden_states):
    """
    Dimension alpha : complexite/variance fractale.
    
    Formule fermee : rapport de variance entre echelles locales et globales.
    Mesure la "rugosite" de la representation.
    
    alpha(x) = var_locale / (var_globale + eps)
    ou var_locale = variance sur fenetre glissante de taille 3
      var_globale = variance totale de la sequence
    
    Args:
        hidden_states: [batch, seq_len, hidden_size]
    Returns:
        alpha: [batch, seq_len, 1] dans [0, 1]
    """
    # Variance globale par token
    var_global = hidden_states.var(dim=-1, keepdim=True)  # [B, S, 1]
    var_global = var_global / (var_global.max(dim=1, keepdim=True)[0] + 1e-8)
    
    # Variance locale (difference avec le voisin)
    diff_left = F.pad(hidden_states[:, 1:] - hidden_states[:, :-1], (0, 0, 1, 0))
    diff_right = F.pad(hidden_states[:, :-1] - hidden_states[:, 1:], (0, 0, 0, 1))
    var_local = (diff_left ** 2 + diff_right ** 2).mean(dim=-1, keepdim=True) / 2
    var_local = var_local / (var_local.max(dim=1, keepdim=True)[0] + 1e-8)
    
    # Rapport de variance (normalise par sigmoid)
    ratio = var_local / (var_global + 1e-8)
    alpha = torch.sigmoid(ratio - 1.0)  # centre autour de 1
    
    return alpha  # [B, S, 1]


def compute_reasoning(hidden_states):
    """
    Dimension reasoning : capacite de raisonnement logique.
    
    Formule fermee : coherence directionnelle des activations.
    Mesure a quel point les activations sont alignees entre elles.
    
    reasoning(x) = |mean(x)| / (mean(|x|) + eps)
    Plus les activations pointent dans la meme direction,
    plus le raisonnement est "coherent".
    
    Args:
        hidden_states: [batch, seq_len, hidden_size]
    Returns:
        reasoning: [batch, seq_len, 1] dans [0, 1]
    """
    mean_abs = hidden_states.abs().mean(dim=-1, keepdim=True)  # [B, S, 1]
    abs_mean = hidden_states.mean(dim=-1, keepdim=True).abs()  # [B, S, 1]
    
    coherence = abs_mean / (mean_abs + 1e-8)
    reasoning = torch.sigmoid(3.0 * (coherence - 0.5))  # mise a l'echelle
    
    return reasoning  # [B, S, 1]


def compute_creativity(hidden_states):
    """
    Dimension creativity : capacite creative/divergente.
    
    Formule fermee : diversite des activations entre tokens voisins.
    Mesure a quel point la representation change entre tokens.
    
    creativity(x) = 1 - cos(x_i, x_{i+1})
    Plus les tokens voisins sont differents, plus c'est "creatif".
    
    Args:
        hidden_states: [batch, seq_len, hidden_size]
    Returns:
        creativity: [batch, seq_len, 1] dans [0, 1]
    """
    # Similarite cosinus entre tokens consecutifs
    x_norm = F.normalize(hidden_states, dim=-1)  # [B, S, D]
    cos_sim = (x_norm[:, :-1] * x_norm[:, 1:]).sum(dim=-1, keepdim=True)  # [B, S-1, 1]
    
    # Padding pour garder la meme longueur
    cos_sim = F.pad(cos_sim, (0, 0, 0, 1))  # [B, S, 1]
    
    # Diversite = 1 - similarite
    diversity = 1.0 - cos_sim
    creativity = torch.sigmoid(3.0 * (diversity - 0.3))
    
    return creativity  # [B, S, 1]


def compute_math(hidden_states):
    """
    Dimension math : capacite mathematique.
    
    Formule fermee : regularite/periodicite des activations.
    Mesure la presence de motifs periodiques dans la representation.
    
    math(x) = max(autocorrelation(x)) / autocorrelation(0)
    Plus il y a de periodicite, plus c'est "mathematique".
    
    Args:
        hidden_states: [batch, seq_len, hidden_size]
    Returns:
        math: [batch, seq_len, 1] dans [0, 1]
    """
    # Autocorrelation approximee par similarite avec un decalage
    x_norm = F.normalize(hidden_states, dim=-1)
    
    # Decalage de 1 pas
    shifted = F.pad(x_norm[:, :-1], (0, 0, 1, 0))
    autocorr = (x_norm * shifted).sum(dim=-1, keepdim=True)  # [B, S, 1]
    
    # Normalisation
    math_val = torch.sigmoid(3.0 * (autocorr - 0.3))
    
    return math_val  # [B, S, 1]


def compute_factual(hidden_states):
    """
    Dimension factual : ancrage factuel.
    
    Formule fermee : stabilite/magnitude des activations.
    Mesure la "confiance" de la representation.
    
    factual(x) = ||x|| / (max||x|| + eps)
    Plus la norme est grande, plus c'est "factuel".
    
    Args:
        hidden_states: [batch, seq_len, hidden_size]
    Returns:
        factual: [batch, seq_len, 1] dans [0, 1]
    """
    norm = torch.norm(hidden_states, dim=-1, keepdim=True)  # [B, S, 1]
    norm_max = norm.max(dim=1, keepdim=True)[0]
    factual = norm / (norm_max + 1e-8)
    
    return factual  # [B, S, 1]


def compute_code(hidden_states):
    """
    Dimension code : capacite de programmation.
    
    Formule fermee : structure hierarchique des activations.
    Mesure le rapport entre basses et hautes frequences.
    
    code(x) = ||basses_frequences|| / (||hautes_frequences|| + eps)
    
    Args:
        hidden_states: [batch, seq_len, hidden_size]
    Returns:
        code: [batch, seq_len, 1] dans [0, 1]
    """
    # Separation basse/haute frequence par average pooling
    # Convolution 1D multi-canaux via avg_pool1d
    h_perm = hidden_states.permute(0, 2, 1)  # [B, D, S]
    
    # Average pooling = filtre passe-bas multi-canaux
    if h_perm.shape[-1] >= 3:
        low_freq = F.avg_pool1d(h_perm, kernel_size=3, stride=1, padding=1)  # [B, D, S]
    else:
        low_freq = h_perm  # pas assez de tokens
    
    low_freq = low_freq.permute(0, 2, 1)  # [B, S, D]
    
    # Hautes frequences = residu
    high_freq = hidden_states - low_freq
    
    # Rapport
    low_norm = torch.norm(low_freq, dim=-1, keepdim=True)
    high_norm = torch.norm(high_freq, dim=-1, keepdim=True)
    
    ratio = low_norm / (high_norm + 1e-8)
    code = torch.sigmoid(ratio - 1.0)
    
    return code  # [B, S, 1]


# =========================================================================
# PROJECTION DE SIGNATURE PURE (deterministe, 0 parametre)
# =========================================================================

class PureSignatureProjection(nn.Module):
    """
    Projection de signature 7D PUREMENT DETERMINISTE.
    
    ZERO parametre entrainable. Chaque dimension est calculee
    par une formule fermee analytique.
    
    Les 7 dimensions :
    - phi : entropie normalisee (diversite)
    - alpha : variance fractale (complexite)
    - reasoning : coherence directionnelle
    - creativity : diversite inter-tokens
    - math : periodicite/autocorrelation
    - factual : norme/confiance
    - code : structure hierarchique
    """
    
    def __init__(self):
        super().__init__()
        # ZERO parametre - tout est deterministe
    
    def forward(self, hidden_states):
        """
        Calcule les signatures 7D de maniere deterministe.
        
        Args:
            hidden_states: [batch, seq_len, hidden_size]
        Returns:
            signatures: [batch, seq_len, 7] dans [0, 1]
        """
        phi = compute_phi(hidden_states)
        alpha = compute_alpha(hidden_states)
        reasoning = compute_reasoning(hidden_states)
        creativity = compute_creativity(hidden_states)
        math_val = compute_math(hidden_states)
        factual = compute_factual(hidden_states)
        code = compute_code(hidden_states)
        
        signatures = torch.cat([
            phi, alpha, reasoning, creativity, math_val, factual, code
        ], dim=-1)  # [B, S, 7]
        
        return signatures


# =========================================================================
# ATTENTION HARMONIQUE PURE
# =========================================================================

class PureHarmonicAttention(nn.Module):
    """
    Attention harmonique PURE — ZERO parametre entrainable.
    
    Remplace completement QKV par :
    1. Signatures 7D deterministes (formules fermees)
    2. Matrice de resonance R = sigmas @ sigmas.T
    3. Noyau ABC (memoire non-locale, deja deterministe)
    4. Somme ponderee directe des hidden states
    
    scores[i,j] = resonance[i,j] * abc_weights[i-j]  (causal)
    output[i] = sum_j softmax(scores[i,:])_j * hidden_states[j]
    
    Proprietes :
    - O(n^2) en memoire (comme l'attention standard)
    - Mais O(1) en parametres (contre O(d^2) pour QKV)
    - La resonance capture les relations semantiques
    - Le noyau ABC capture la memoire temporelle
    """
    
    def __init__(self, max_len=2048):
        super().__init__()
        # ZERO parametre entrainable
        self.abc_kernel = ABCKernel(max_len=max_len)
        self.signature_proj = PureSignatureProjection()
    
    def forward(self, hidden_states, attention_mask=None):
        """
        Forward pass de l'attention harmonique pure.
        
        Args:
            hidden_states: [batch, seq_len, hidden_size]
            attention_mask: [batch, 1, 1, seq_len] optionnel (True = masquer)
        
        Returns:
            output: [batch, seq_len, hidden_size]
            signatures: [batch, seq_len, 7]
        """
        batch, seq_len, hidden_size = hidden_states.shape
        
        # 1. Signatures harmoniques 7D (deterministes)
        signatures = self.signature_proj(hidden_states)  # [B, S, 7]
        
        # 2. Matrice de resonance R = sigmas @ sigmas.T
        #    R[i,j] = similarite entre signature du token i et j
        resonance = torch.bmm(signatures, signatures.transpose(1, 2))  # [B, S, S]
        resonance = resonance / 7.0  # normalise dans [0, 1] (les sigmas sont dans [0,1])
        
        # 3. Poids ABC (memoire non-locale)
        abc_weights = self.abc_kernel.forward(seq_len)  # [S]
        
        # Matrice de poids ABC causale
        indices_i = torch.arange(seq_len, device=hidden_states.device).unsqueeze(1)
        indices_j = torch.arange(seq_len, device=hidden_states.device).unsqueeze(0)
        distance = indices_i - indices_j  # [S, S]
        
        causal_mask = distance >= 0
        abc_matrix = torch.where(
            causal_mask,
            abc_weights[distance.clamp(min=0)],
            torch.zeros_like(distance, dtype=torch.float32)
        )  # [S, S]
        
        # 4. Scores harmoniques = resonance * memoire ABC
        #    PAS de QK^T, PAS de scale, PAS de softmax prealable
        scores = resonance * abc_matrix.unsqueeze(0)  # [B, S, S]
        
        # 5. Masque d'attention (padding)
        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask.squeeze(1), float('-inf'))
        
        # 6. Softmax
        attn_weights = F.softmax(scores, dim=-1)  # [B, S, S]
        
        # 7. Somme ponderee des hidden states (PAS de projection V)
        output = torch.bmm(attn_weights, hidden_states)  # [B, S, D]
        
        return output, signatures


# =========================================================================
# TEST
# =========================================================================

def test_pure_harmonic_attention():
    """Teste l'attention harmonique pure."""
    print("=" * 60)
    print("Test de l'Attention Harmonique PURE")
    print("=" * 60)
    
    batch, seq_len, hidden_size = 2, 16, 512
    
    attn = PureHarmonicAttention(max_len=2048)
    
    total_params = sum(p.numel() for p in attn.parameters())
    print(f"\nConfiguration :")
    print(f"  batch       = {batch}")
    print(f"  seq_len     = {seq_len}")
    print(f"  hidden_size = {hidden_size}")
    print(f"  Parametres  = {total_params:,}")
    print(f"  (dont noyau ABC = {sum(p.numel() for p in attn.abc_kernel.parameters())})")
    
    # Forward pass
    x = torch.randn(batch, seq_len, hidden_size)
    output, signatures = attn(x)
    
    print(f"\nForward pass :")
    print(f"  Input      : {x.shape}")
    print(f"  Output     : {output.shape}")
    print(f"  Signatures : {signatures.shape}")
    
    # Verifications
    assert output.shape == x.shape
    assert signatures.shape == (batch, seq_len, 7)
    assert torch.all(signatures >= 0) and torch.all(signatures <= 1)
    print("[OK] Signatures dans [0, 1]")
    
    # Profil des signatures
    mean_sig = signatures.mean(dim=(0, 1))
    dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']
    print(f"\nProfil de signature moyen :")
    for name, val in zip(dims, mean_sig):
        print(f"  {name:12s} = {val.item():.4f}")
    
    # Test avec masque
    mask = torch.zeros(batch, 1, 1, seq_len, dtype=torch.bool)
    mask[:, :, :, 8:] = True
    output_masked, _ = attn(x, attention_mask=mask)
    assert output_masked.shape == x.shape
    print("[OK] Forward avec masque")
    
    # Test de reproductibilite (determinisme)
    output2, sig2 = attn(x)
    assert torch.allclose(output, output2)
    assert torch.allclose(signatures, sig2)
    print("[OK] Reproducible (deterministe)")
    
    # Test de passage a travers plusieurs couches
    num_layers = 4
    layers = [PureHarmonicAttention(max_len=2048) for _ in range(num_layers)]
    x = torch.randn(batch, seq_len, hidden_size)
    
    all_signatures = []
    for l in layers:
        x, sig = l(x)
        all_signatures.append(sig)
    
    all_signatures = torch.stack(all_signatures)
    print(f"\n{num_layers} couches empilees :")
    print(f"  Output final : {x.shape}")
    print(f"  Signatures   : {all_signatures.shape}")
    
    sig_var = all_signatures.var(dim=0).mean().item()
    print(f"  Variance inter-couches : {sig_var:.6f}")
    assert sig_var > 0, "Les signatures doivent varier entre les couches"
    print("[OK] Les signatures evoluent a travers les couches")
    
    print(f"\n[SUCCES] Attention Harmonique PURE operationnelle")
    return True


if __name__ == '__main__':
    test_pure_harmonic_attention()
