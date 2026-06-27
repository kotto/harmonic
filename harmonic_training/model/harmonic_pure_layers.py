"""
Couches de Decodeur Harmonique PUR
===================================
ZERO parametre entrainable dans l'attention et le FFN.

Architecture :
1. Attention harmonique pure (resonance 7D + noyau ABC)
2. Transformation deterministe des signatures (pas de SwiGLU)
3. Connexion residuelle

La transformation des signatures est une fonction deterministe :
    x_out = x + W_harmonic @ (sigmas * abc_kernel)
ou W_harmonic est une matrice FIXE (pas entrainable) basee sur PHI.

Proprietes :
- O(d^2) en calcul mais O(1) en parametres entrainables
- Les poids W_harmonic sont initialises une fois pour toutes
- La seule chose qui change entre les couches est l'etat des signatures
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.harmonic_pure_attention import PureHarmonicAttention
from model.abc_kernel import PHI, ALPHA


# =========================================================================
# POIDS HARMONIQUES FIXES (matrices deterministes)
# =========================================================================

def create_harmonic_weight_matrix(hidden_size):
    """
    Cree une matrice de poids harmonique FIXE.
    
    Basee sur les puissances de PHI (nombre d'or) :
    W[i,j] = PHI^(-|i-j|) * cos(2*pi*|i-j|/PHI)
    
    Cette matrice a des proprietes de resonance :
    - Decroissance exponentielle avec la distance (PHI^(-d))
    - Oscillation harmonique (cos)
    - Autosimilarite fractale
    
    Args:
        hidden_size: Taille de la matrice
    
    Returns:
        W: Tenseur [hidden_size, hidden_size] fixe
    """
    device = torch.device('cpu')
    
    # Indices
    i = torch.arange(hidden_size, device=device).unsqueeze(1)
    j = torch.arange(hidden_size, device=device).unsqueeze(0)
    d = torch.abs(i - j).float()  # [D, D]
    
    # Poids harmonique
    W = PHI ** (-d) * torch.cos(2 * math.pi * d / PHI)
    
    # Normalisation pour que la norme de W soit ~1
    W = W / torch.sqrt(torch.mean(W ** 2) + 1e-8)
    
    return W


def create_harmonic_ffn_weights(hidden_size, intermediate_size):
    """
    Cree les poids fixes pour la transformation FFN harmonique.
    
    Remplace SwiGLU par une transformation harmonique :
    - W_gate : projection harmonique (basee sur PHI)
    - W_up : projection harmonique (basee sur ALPHA)
    - W_down : projection harmonique (basee sur PHI^2)
    
    Args:
        hidden_size: Taille d'entree/sortie
        intermediate_size: Taille intermediaire
    
    Returns:
        W_gate: [intermediate_size, hidden_size]
        W_up: [intermediate_size, hidden_size]
        W_down: [hidden_size, intermediate_size]
    """
    device = torch.device('cpu')
    
    # W_gate : base sur PHI
    i = torch.arange(intermediate_size, device=device).unsqueeze(1)
    j = torch.arange(hidden_size, device=device).unsqueeze(0)
    d = torch.abs(i.float() / intermediate_size - j.float() / hidden_size)
    W_gate = PHI ** (-d * 10) * torch.cos(2 * math.pi * d * PHI)
    W_gate = W_gate / torch.sqrt(torch.mean(W_gate ** 2) + 1e-8)
    
    # W_up : base sur ALPHA
    W_up = ALPHA ** (d * 5) * torch.sin(2 * math.pi * d * PHI)
    W_up = W_up / torch.sqrt(torch.mean(W_up ** 2) + 1e-8)
    
    # W_down : base sur PHI^2
    i2 = torch.arange(hidden_size, device=device).unsqueeze(1)
    j2 = torch.arange(intermediate_size, device=device).unsqueeze(0)
    d2 = torch.abs(i2.float() / hidden_size - j2.float() / intermediate_size)
    W_down = (PHI ** 2) ** (-d2 * 10) * torch.cos(2 * math.pi * d2 * PHI)
    W_down = W_down / torch.sqrt(torch.mean(W_down ** 2) + 1e-8)
    
    return W_gate, W_up, W_down


# =========================================================================
# TRANSFORMEE HARMONIQUE FIXE (remplace SwiGLU)
# =========================================================================

class HarmonicFixedTransform(nn.Module):
    """
    Transformation harmonique FIXE.
    
    Remplace SwiGLU par :
    1. Projection harmonique fixe (W_gate, W_up)
    2. Activation harmonique (sigmas * PHI)
    3. Projection de sortie fixe (W_down)
    
    ZERO parametre entrainable.
    """
    
    def __init__(self, hidden_size, intermediate_size=None):
        super().__init__()
        if intermediate_size is None:
            intermediate_size = hidden_size * 4
        
        # Poids fixes (non entrainables)
        W_gate, W_up, W_down = create_harmonic_ffn_weights(
            hidden_size, intermediate_size
        )
        
        self.register_buffer('W_gate_fixed', W_gate)
        self.register_buffer('W_up_fixed', W_up)
        self.register_buffer('W_down_fixed', W_down)
    
    def forward(self, x):
        """
        Forward pass de la transformation harmonique fixe.
        
        Args:
            x: [batch, seq_len, hidden_size]
        Returns:
            output: [batch, seq_len, hidden_size]
        """
        # Projections fixes
        gate = F.linear(x, self.W_gate_fixed)  # [B, S, I]
        up = F.linear(x, self.W_up_fixed)      # [B, S, I]
        
        # Activation harmonique (remplace SiLU)
        # gate_active = gate * sigmoid(gate) * PHI  (harmonique)
        gate_active = gate * torch.sigmoid(gate * ALPHA) * PHI
        
        # Combinaison
        hidden = gate_active * up  # [B, S, I]
        
        # Projection de sortie fixe
        output = F.linear(hidden, self.W_down_fixed)  # [B, S, D]
        
        return output


# =========================================================================
# COUCHE DE DECODEUR HARMONIQUE PURE
# =========================================================================

class PureHarmonicDecoderLayer(nn.Module):
    """
    Couche de decodeur harmonique PURE.
    
    ZERO parametre entrainable.
    
    Architecture :
        x_norm = x (pas de LayerNorm - pas de parametres)
        attn_out, sigmas = PureHarmonicAttention(x_norm)
        x = x + attn_out
        
        x_norm = x
        ffn_out = HarmonicFixedTransform(x_norm)
        x = x + ffn_out
    
    Proprietes :
    - Tous les poids sont des matrices fixes basees sur PHI
    - Les signatures 7D sont des formules fermees
    - Le noyau ABC est deterministe
    - La seule chose qui change entre les couches est l'etat
    """
    
    def __init__(self, hidden_size, intermediate_size=None, max_len=2048):
        super().__init__()
        if intermediate_size is None:
            intermediate_size = hidden_size * 4
        
        self.hidden_size = hidden_size
        
        # Attention harmonique pure (0 parametre entrainable)
        self.self_attn = PureHarmonicAttention(max_len=max_len)
        
        # Transformation FFN harmonique fixe (0 parametre entrainable)
        self.ffn = HarmonicFixedTransform(hidden_size, intermediate_size)
        
        # NOTE : Pas de LayerNorm car elle a des parametres entrainables
        # On utilise une normalisation deterministe basee sur la norme L2
    
    def _normalize(self, x):
        """
        Normalisation deterministe (pas de parametres).
        
        x_norm = x / (||x|| + eps) * sqrt(d)
        
        Args:
            x: [batch, seq_len, hidden_size]
        Returns:
            x_norm: meme shape
        """
        norm = torch.norm(x, dim=-1, keepdim=True)
        return x * math.sqrt(self.hidden_size) / (norm + 1e-8)
    
    def forward(self, hidden_states, attention_mask=None):
        """
        Forward pass de la couche de decodeur harmonique pure.
        
        Args:
            hidden_states: [batch, seq_len, hidden_size]
            attention_mask: [batch, 1, 1, seq_len] optionnel
        
        Returns:
            hidden_states: [batch, seq_len, hidden_size]
            signatures: [batch, seq_len, 7]
        """
        # === Bloc d'attention harmonique pure ===
        residual = hidden_states
        hidden_states = self._normalize(hidden_states)
        attn_output, signatures = self.self_attn(hidden_states, attention_mask)
        hidden_states = residual + attn_output
        
        # === Bloc FFN harmonique fixe ===
        residual = hidden_states
        hidden_states = self._normalize(hidden_states)
        ffn_output = self.ffn(hidden_states)
        hidden_states = residual + ffn_output
        
        return hidden_states, signatures


# =========================================================================
# TEST
# =========================================================================

def test_pure_harmonic_decoder_layer():
    """Teste la couche de decodeur harmonique pure."""
    print("=" * 60)
    print("Test de la Couche de Decodeur Harmonique PURE")
    print("=" * 60)
    
    hidden_size = 512
    intermediate_size = 2048
    batch, seq_len = 2, 32
    
    layer = PureHarmonicDecoderLayer(
        hidden_size=hidden_size,
        intermediate_size=intermediate_size,
        max_len=2048
    )
    
    total_params = sum(p.numel() for p in layer.parameters())
    print(f"\nConfiguration :")
    print(f"  hidden_size       = {hidden_size}")
    print(f"  intermediate_size = {intermediate_size}")
    print(f"  Parametres        = {total_params:,}")
    print(f"  (tous des buffers fixes, 0 entrainable)")
    
    # Forward pass
    x = torch.randn(batch, seq_len, hidden_size)
    output, signatures = layer(x)
    
    print(f"\nForward pass :")
    print(f"  Input    : {x.shape}")
    print(f"  Output   : {output.shape}")
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
    mask[:, :, :, 16:] = True
    output_masked, _ = layer(x, attention_mask=mask)
    assert output_masked.shape == x.shape
    print("[OK] Forward avec masque")
    
    # Test de reproductibilite
    output2, sig2 = layer(x)
    assert torch.allclose(output, output2)
    assert torch.allclose(signatures, sig2)
    print("[OK] Reproducible (deterministe)")
    
    # Test de passage a travers plusieurs couches
    num_layers = 4
    layers = nn.ModuleList([
        PureHarmonicDecoderLayer(hidden_size, intermediate_size)
        for _ in range(num_layers)
    ])
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
    
    print(f"\n[SUCCES] Couche de Decodeur Harmonique PURE operationnelle")
    return True


if __name__ == '__main__':
    test_pure_harmonic_decoder_layer()
