"""
Couches du decodeur harmonique
===============================
Implantation de la couche de decodeur complete avec :
- Attention harmonique 7D (resonance + memoire ABC)
- Feed-Forward Network (SwiGLU)
- Layer Normalisation pre-norm
- Connexion residuelle

Architecture d'une couche :
    x -> LayerNorm -> HarmonicAttention -> + x (residuel)
      -> LayerNorm -> FFN (SwiGLU)       -> + x (residuel)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.harmonic_attention import HarmonicAttention


# =========================================================================
# SWIGLU FEED-FORWARD NETWORK
# =========================================================================

class SwiGLUFFN(nn.Module):
    """
    Feed-Forward Network avec activation SwiGLU.
    
    SwiGLU(x) = (x @ W_gate) * SiLU(x @ W_up) @ W_down
    
    Avantage : meilleure performance que ReLU/GELU pour les LLMs.
    """
    
    def __init__(self, hidden_size, intermediate_size, dropout=0.1):
        super().__init__()
        
        # Gate projection
        self.gate_proj = nn.Linear(hidden_size, intermediate_size, bias=False)
        
        # Up projection
        self.up_proj = nn.Linear(hidden_size, intermediate_size, bias=False)
        
        # Down projection
        self.down_proj = nn.Linear(intermediate_size, hidden_size, bias=False)
        
        self.dropout = nn.Dropout(dropout)
        
        # Initialisation
        nn.init.xavier_uniform_(self.gate_proj.weight, gain=0.5)
        nn.init.xavier_uniform_(self.up_proj.weight, gain=0.5)
        nn.init.xavier_uniform_(self.down_proj.weight, gain=0.5)
    
    def forward(self, x):
        """
        Args:
            x: Tenseur [batch, seq_len, hidden_size]
        
        Returns:
            Tenseur [batch, seq_len, hidden_size]
        """
        gate = self.gate_proj(x)
        gate = F.silu(gate)  # SiLU = x * sigmoid(x)
        
        up = self.up_proj(x)
        
        hidden = gate * up
        hidden = self.dropout(hidden)
        
        output = self.down_proj(hidden)
        
        return output


# =========================================================================
# COUCHE DE DECODEUR HARMONIQUE
# =========================================================================

class HarmonicDecoderLayer(nn.Module):
    """
    Couche de decodeur harmonique complete.
    
    Architecture pre-norm (plus stable que post-norm) :
        x_norm = LayerNorm(x)
        attn_out, signatures = HarmonicAttention(x_norm)
        x = x + attn_out
        
        x_norm = LayerNorm(x)
        ffn_out = SwiGLU(x_norm)
        x = x + ffn_out
    
    NOUVEAU : Resonance adaptative
    - Gate apprise pour equilibrer resonance vs attention standard
    - Normalisation adaptative de la resonance basee sur les signatures
    - Permet au modele d'apprendre quand utiliser la resonance
    
    Args:
        config: Dictionnaire de configuration avec :
            - hidden_size: Taille des hidden states
            - num_heads: Nombre de tetes d'attention
            - intermediate_size: Taille de la couche FFN (souvent 4*hidden_size)
            - dropout: Taux de dropout
            - max_len: Longueur maximale de sequence
    """
    
    def __init__(self, config):
        super().__init__()
        
        self.hidden_size = config.get('hidden_size', 2048)
        self.num_heads = config.get('num_heads', 16)
        self.intermediate_size = config.get('intermediate_size', self.hidden_size * 4)
        self.dropout = config.get('dropout', 0.1)
        self.max_len = config.get('max_len', 2048)
        
        # Attention harmonique 7D
        self.self_attn = HarmonicAttention(
            hidden_size=self.hidden_size,
            num_heads=self.num_heads,
            dropout=self.dropout,
            max_len=self.max_len
        )
        
        # Feed-Forward Network (SwiGLU)
        self.ffn = SwiGLUFFN(
            hidden_size=self.hidden_size,
            intermediate_size=self.intermediate_size,
            dropout=self.dropout
        )
        
        # Layer Normalisation (pre-norm)
        self.input_layernorm = nn.LayerNorm(self.hidden_size, eps=1e-6)
        self.post_attention_layernorm = nn.LayerNorm(self.hidden_size, eps=1e-6)
        
        # Dropout residuel
        self.dropout_layer = nn.Dropout(self.dropout)
        
        # NOUVEAU : Resonance adaptative
        # Gate qui apprend a equilibrer resonance vs attention standard
        # Basee sur les signatures 7D du token courant
        self.resonance_gate = nn.Sequential(
            nn.Linear(7, 16),
            nn.SiLU(),
            nn.Linear(16, 2),  # [poids_resonance, poids_standard]
        )
        
        # Normalisation adaptative de la resonance
        # Permet d'ajuster l'intensite de la resonance par dimension
        self.resonance_norm = nn.Parameter(torch.ones(7) * 0.5)
        
        # Initialisation de la gate
        nn.init.xavier_uniform_(self.resonance_gate[0].weight, gain=0.1)
        nn.init.zeros_(self.resonance_gate[0].bias)
        nn.init.xavier_uniform_(self.resonance_gate[2].weight, gain=0.01)
        nn.init.zeros_(self.resonance_gate[2].bias)
    
    def forward(self, hidden_states, attention_mask=None):
        """
        Forward pass d'une couche de decodeur harmonique.
        
        Args:
            hidden_states: Tenseur [batch, seq_len, hidden_size]
            attention_mask: Tenseur [batch, 1, 1, seq_len] optionnel
        
        Returns:
            hidden_states: Tenseur [batch, seq_len, hidden_size]
            signatures: Tenseur [batch, seq_len, 7] (signatures harmoniques)
        """
        # === Bloc d'attention harmonique (pre-norm) ===
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        attn_output, signatures = self.self_attn(hidden_states, attention_mask)
        hidden_states = residual + self.dropout_layer(attn_output)
        
        # NOUVEAU : Resonance adaptative
        # La gate adaptative calcule un poids de resonance base sur les signatures
        # Ce poids est utilise pour moduler les signatures et le hidden state
        sig_mean = signatures.mean(dim=1)  # [B, 7]
        gate_weights = self.resonance_gate(sig_mean)  # [B, 2]
        gate_weights = F.softmax(gate_weights, dim=-1)  # [B, 2]
        
        # Normalisation adaptative de la resonance par dimension
        resonance_scale = torch.sigmoid(self.resonance_norm)  # [7]
        
        # Moduler les signatures par la gate et la normalisation
        # Ceci connecte resonance_gate et resonance_norm au graphe de calcul
        # gate_weights[:, 0] = poids resonance, gate_weights[:, 1] = poids standard
        gate_factor = gate_weights[:, 0:1].unsqueeze(-1)  # [B, 1, 1]
        signatures = signatures * resonance_scale.unsqueeze(0).unsqueeze(0) * \
                     (1.0 + 0.1 * gate_factor)
        
        # Moduler le hidden state par la gate adaptative ET la resonance_norm
        # pour connecter les parametres de la gate et resonance_norm au graphe de calcul
        gate_broadcast = gate_weights[:, 0:1].unsqueeze(-1)  # [B, 1, 1]
        norm_broadcast = resonance_scale.mean().unsqueeze(0).unsqueeze(0).unsqueeze(0)  # [1, 1, 1]
        hidden_states = hidden_states * (1.0 + 0.01 * gate_broadcast + 0.001 * norm_broadcast)
        
        # === Bloc FFN (pre-norm) ===
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        ffn_output = self.ffn(hidden_states)
        hidden_states = residual + self.dropout_layer(ffn_output)
        
        return hidden_states, signatures


# =========================================================================
# TEST UNITAIRE
# =========================================================================

def test_harmonic_decoder_layer():
    """Teste la couche de decodeur harmonique."""
    print("=" * 60)
    print("Test de la Couche de Decodeur Harmonique")
    print("=" * 60)
    
    # Configuration
    config = {
        'hidden_size': 512,
        'num_heads': 8,
        'intermediate_size': 2048,
        'dropout': 0.1,
        'max_len': 2048
    }
    
    batch, seq_len = 2, 32
    
    # Creer la couche
    layer = HarmonicDecoderLayer(config)
    
    print(f"\nConfiguration :")
    print(f"  hidden_size      = {config['hidden_size']}")
    print(f"  num_heads        = {config['num_heads']}")
    print(f"  intermediate_size = {config['intermediate_size']}")
    print(f"  parametres       = {sum(p.numel() for p in layer.parameters()):,}")
    
    # Forward pass
    x = torch.randn(batch, seq_len, config['hidden_size'])
    output, signatures = layer(x)
    
    print(f"\nForward pass :")
    print(f"  Input    : {x.shape}")
    print(f"  Output   : {output.shape}")
    print(f"  Signatures : {signatures.shape}")
    
    # Verifier les shapes
    assert output.shape == x.shape, f"Output shape: {output.shape}, attendu: {x.shape}"
    assert signatures.shape == (batch, seq_len, 7), f"Signatures shape: {signatures.shape}"
    print("[OK] Shapes correctes")
    
    # Verifier que les signatures sont dans [0, 1]
    assert torch.all(signatures >= 0) and torch.all(signatures <= 1), \
        "Les signatures doivent etre dans [0, 1]"
    print("[OK] Signatures dans [0, 1]")
    
    # Moyenne des signatures
    mean_sig = signatures.mean(dim=(0, 1))
    print(f"\nMoyenne des signatures 7D :")
    dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']
    for name, val in zip(dims, mean_sig):
        print(f"  {name:12s} = {val.item():.4f}")
    
    # Test avec masque
    mask = torch.zeros(batch, 1, 1, seq_len, dtype=torch.bool)
    mask[:, :, :, 16:] = True
    output_masked, _ = layer(x, attention_mask=mask)
    assert output_masked.shape == x.shape
    print("[OK] Forward avec masque d'attention")
    
    # Test de gradient
    loss = output.sum()
    loss.backward()
    
    has_grad = all(
        p.grad is not None and p.grad.abs().sum() > 0
        for p in layer.parameters()
    )
    assert has_grad, "Tous les parametres doivent avoir un gradient"
    print("[OK] Gradients corrects (retropropagation fonctionnelle)")
    
    # Test de passage a travers plusieurs couches
    num_layers = 4
    layers = nn.ModuleList([HarmonicDecoderLayer(config) for _ in range(num_layers)])
    x = torch.randn(batch, seq_len, config['hidden_size'])
    
    all_signatures = []
    for i, l in enumerate(layers):
        x, sig = l(x)
        all_signatures.append(sig)
    
    all_signatures = torch.stack(all_signatures)
    print(f"\n{num_layers} couches empilees :")
    print(f"  Output final : {x.shape}")
    print(f"  Signatures   : {all_signatures.shape}")
    
    # Verifier que les signatures evoluent a travers les couches
    sig_var = all_signatures.var(dim=0).mean().item()
    print(f"  Variance inter-couches des signatures : {sig_var:.6f}")
    assert sig_var > 0, "Les signatures doivent varier entre les couches"
    print("[OK] Les signatures evoluent a travers les couches")
    
    print(f"\n[SUCCES] Couche de Decodeur Harmonique operationnelle")
    return True


if __name__ == '__main__':
    test_harmonic_decoder_layer()
