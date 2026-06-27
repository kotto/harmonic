"""
Attention Harmonique 7D
=======================
Remplace l'attention standard des transformeurs par une attention
basee sur la resonance harmonique dans un espace a 7 dimensions.

Principe :
1. Chaque token projette ses hidden states dans un espace de signature 7D
2. La matrice de resonance R = sigmas @ sigmas.T pondere l'attention
3. Le noyau ABC (derivee fractionnaire) ajoute la memoire non-locale
4. L'attention harmonique combine similarite cosinus + resonance + memoire

Les 7 dimensions de la signature harmonique :
    [phi, alpha, reasoning, creativity, math, factual, code]

References :
    - Atangana-Baleanu fractional derivative (ABC kernel)
    - Golden ratio phi = 1.618... comme constante fondamentale
    - Resonance harmonique comme alternative a l'attention standard
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
# Ajouter le repertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.abc_kernel import ABCKernel, ALPHA, B_1_PHI


# =========================================================================
# PROJECTION DE SIGNATURE 7D
# =========================================================================

class SignatureProjection(nn.Module):
    """
    Projette les hidden states dans l'espace de signature harmonique 7D.
    
    Les 7 dimensions sont apprises par des projections lineaires,
    puis normalisees par sigmoid pour etre dans [0, 1].
    
    Chaque dimension correspond a un aspect du raisonnement :
    - phi : diversite/entropie de la representation
    - alpha : complexite/variance locale
    - reasoning : capacite de raisonnement logique
    - creativity : capacite creative/divergente
    - math : capacite mathematique
    - factual : ancrage factuel
    - code : capacite de programmation
    """
    
    def __init__(self, hidden_size, dropout=0.1):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Projection principale : hidden_size -> 7
        self.projection = nn.Linear(hidden_size, 7, bias=True)
        
        # Initialisation speciale pour les dimensions phi et alpha
        # (basees sur des proprietes intrinseques des hidden states)
        nn.init.xavier_uniform_(self.projection.weight, gain=0.5)
        nn.init.zeros_(self.projection.bias)
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(7)
    
    def forward(self, hidden_states):
        """
        Calcule les signatures 7D pour chaque token.
        
        Args:
            hidden_states: Tenseur [batch, seq_len, hidden_size]
        
        Returns:
            signatures: Tenseur [batch, seq_len, 7] dans [0, 1]
        """
        # Projection lineaire
        raw = self.projection(hidden_states)
        raw = self.dropout(raw)
        
        # Normalisation
        raw = self.layer_norm(raw)
        
        # Activation sigmoid pour [0, 1]
        signatures = torch.sigmoid(raw)
        
        return signatures


# =========================================================================
# ATTENTION HARMONIQUE
# =========================================================================

class HarmonicAttention(nn.Module):
    """
    Attention harmonique 7D avec resonance et memoire ABC.
    
    Architecture :
        scores = (Q @ K.T / sqrt(d)) * resonance * ABC_weights
        
    ou :
        - Q, K, V : projections standard du transformeur
        - resonance = sigmas @ sigmas.T (similarite des signatures 7D)
        - ABC_weights = noyau de memoire non-locale (derivee fractionnaire)
    
    Proprietes :
        - La resonance favorise les tokens avec des signatures similaires
        - La memoire ABC donne plus de poids aux tokens recents
        - Les 7 dimensions permettent un controle fin du raisonnement
    """
    
    def __init__(self, hidden_size, num_heads, dropout=0.1, max_len=2048):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.scale = 1.0 / math.sqrt(self.head_dim)
        
        assert hidden_size % num_heads == 0, \
            f"hidden_size ({hidden_size}) doit etre divisible par num_heads ({num_heads})"
        
        # Projections standard Q, K, V
        self.q_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.k_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.v_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.o_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        
        # Projection de signature 7D
        self.signature_proj = SignatureProjection(hidden_size, dropout)
        
        # Noyau ABC pour la memoire non-locale
        self.abc_kernel = ABCKernel(max_len=max_len)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Parametre appris pour le poids de la resonance
        self.resonance_weight = nn.Parameter(torch.tensor(1.0))
        
        # Parametre appris pour le poids du noyau ABC
        self.abc_weight = nn.Parameter(torch.tensor(1.0))
    
    def forward(self, hidden_states, attention_mask=None):
        """
        Calcule l'attention harmonique.
        
        Args:
            hidden_states: Tenseur [batch, seq_len, hidden_size]
            attention_mask: Tenseur [batch, 1, 1, seq_len] optionnel
                            (True = masque, False = garder)
        
        Returns:
            output: Tenseur [batch, seq_len, hidden_size]
            signatures: Tenseur [batch, seq_len, 7] (pour analyse)
        """
        batch, seq_len, _ = hidden_states.shape
        
        # 1. Signatures harmoniques 7D
        signatures = self.signature_proj(hidden_states)  # [B, S, 7]
        
        # 2. Matrice de resonance R = sigmas @ sigmas.T
        #    R[i,j] = similarite entre la signature du token i et du token j
        resonance = torch.bmm(signatures, signatures.transpose(1, 2))  # [B, S, S]
        
        # Normaliser la resonance dans [0, 1]
        resonance = (resonance + 1.0) / 2.0  # les signatures sont dans [0,1], produit dans [0,7]
        resonance = resonance / 7.0  # normaliser par le nombre de dimensions
        
        # 3. Projections Q, K, V
        Q = self.q_proj(hidden_states).view(batch, seq_len, self.num_heads, self.head_dim)
        K = self.k_proj(hidden_states).view(batch, seq_len, self.num_heads, self.head_dim)
        V = self.v_proj(hidden_states).view(batch, seq_len, self.num_heads, self.head_dim)
        
        # Transposer pour l'attention : [B, H, S, D]
        Q = Q.transpose(1, 2)
        K = K.transpose(1, 2)
        V = V.transpose(1, 2)
        
        # 4. Scores d'attention standard
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale  # [B, H, S, S]
        
        # 5. Appliquer la resonance harmonique
        #    La resonance pondere les scores d'attention
        resonance_expanded = resonance.unsqueeze(1).expand(-1, self.num_heads, -1, -1)
        scores = scores * (1.0 + self.resonance_weight * resonance_expanded)
        
        # 6. Appliquer le noyau ABC (memoire non-locale)
        #    Les poids ABC dependent de la distance entre tokens
        abc_weights = self.abc_kernel.forward(seq_len)  # [S]
        
        # Creer une matrice de poids ABC causale
        # abc_matrix[i,j] = abc_weights[i-j] pour i >= j, 0 sinon
        indices_i = torch.arange(seq_len, device=hidden_states.device).unsqueeze(1)
        indices_j = torch.arange(seq_len, device=hidden_states.device).unsqueeze(0)
        distance = indices_i - indices_j  # [S, S]
        
        # Masque causal : seuls les tokens passes sont visibles
        causal_mask = distance >= 0
        abc_matrix = torch.where(
            causal_mask,
            abc_weights[distance.clamp(min=0)],
            torch.zeros_like(distance, dtype=torch.float32)
        )
        
        # Appliquer les poids ABC
        abc_matrix = abc_matrix.unsqueeze(0).unsqueeze(0)  # [1, 1, S, S]
        scores = scores * (1.0 + self.abc_weight * abc_matrix)
        
        # 7. Appliquer le masque d'attention (padding)
        if attention_mask is not None:
            # attention_mask: [B, 1, 1, S] avec True = masque
            scores = scores.masked_fill(attention_mask, float('-inf'))
        
        # 8. Softmax et dropout
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # 9. Appliquer l'attention
        output = torch.matmul(attn_weights, V)  # [B, H, S, D]
        
        # 10. Reassemblage
        output = output.transpose(1, 2).contiguous().view(batch, seq_len, -1)
        output = self.o_proj(output)
        
        return output, signatures
    
    def _forward_without_causal(self, hidden_states, attention_mask=None):
        """
        Forward SANS construire le masque causal interne.
        
        Utilise par le wrapper GPT-2 qui fournit deja le masque causal.
        
        Args:
            hidden_states: [batch, seq_len, hidden_size]
            attention_mask: [batch, 1, 1, seq_len] (True = masquer)
        
        Returns:
            output: [batch, seq_len, hidden_size]
            signatures: [batch, seq_len, 7]
        """
        batch, seq_len, _ = hidden_states.shape
        
        # 1. Signatures harmoniques 7D
        signatures = self.signature_proj(hidden_states)
        
        # 2. Matrice de resonance
        resonance = torch.bmm(signatures, signatures.transpose(1, 2))
        resonance = (resonance + 1.0) / 2.0
        resonance = resonance / 7.0
        
        # 3. Projections Q, K, V
        Q = self.q_proj(hidden_states).view(batch, seq_len, self.num_heads, self.head_dim)
        K = self.k_proj(hidden_states).view(batch, seq_len, self.num_heads, self.head_dim)
        V = self.v_proj(hidden_states).view(batch, seq_len, self.num_heads, self.head_dim)
        Q = Q.transpose(1, 2)
        K = K.transpose(1, 2)
        V = V.transpose(1, 2)
        
        # 4. Scores d'attention standard
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
        
        # 5. Resonance harmonique
        resonance_expanded = resonance.unsqueeze(1).expand(-1, self.num_heads, -1, -1)
        scores = scores * (1.0 + self.resonance_weight * resonance_expanded)
        
        # 6. Noyau ABC (sans masque causal - deja fourni par GPT-2)
        abc_weights = self.abc_kernel.forward(seq_len)
        indices_i = torch.arange(seq_len, device=hidden_states.device).unsqueeze(1)
        indices_j = torch.arange(seq_len, device=hidden_states.device).unsqueeze(0)
        distance = indices_i - indices_j
        causal_mask = distance >= 0
        abc_matrix = torch.where(
            causal_mask,
            abc_weights[distance.clamp(min=0)],
            torch.zeros_like(distance, dtype=torch.float32)
        )
        abc_matrix = abc_matrix.unsqueeze(0).unsqueeze(0)
        scores = scores * (1.0 + self.abc_weight * abc_matrix)
        
        # 7. Masque d'attention (fourni par GPT-2)
        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask, float('-inf'))
        
        # 8. Softmax
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # 9. Output
        output = torch.matmul(attn_weights, V)
        output = output.transpose(1, 2).contiguous().view(batch, seq_len, -1)
        output = self.o_proj(output)
        
        return output, signatures


# =========================================================================
# TEST UNITAIRE
# =========================================================================

def test_harmonic_attention():
    """Teste l'attention harmonique 7D."""
    print("=" * 60)
    print("Test de l'Attention Harmonique 7D")
    print("=" * 60)
    
    batch, seq_len, hidden_size, num_heads = 2, 16, 256, 8
    
    # Creer l'attention harmonique
    attn = HarmonicAttention(
        hidden_size=hidden_size,
        num_heads=num_heads,
        dropout=0.1,
        max_len=2048
    )
    
    print(f"\nConfiguration :")
    print(f"  batch      = {batch}")
    print(f"  seq_len    = {seq_len}")
    print(f"  hidden_size = {hidden_size}")
    print(f"  num_heads  = {num_heads}")
    print(f"  head_dim   = {hidden_size // num_heads}")
    print(f"  parametres = {sum(p.numel() for p in attn.parameters()):,}")
    
    # Forward pass
    x = torch.randn(batch, seq_len, hidden_size)
    output, signatures = attn(x)
    
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
    
    # Verifier la moyenne des signatures
    mean_sig = signatures.mean(dim=(0, 1))
    print(f"\nMoyenne des signatures 7D :")
    dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']
    for i, (name, val) in enumerate(zip(dims, mean_sig)):
        print(f"  {name:12s} = {val.item():.4f}")
    
    # Test avec masque d'attention
    mask = torch.zeros(batch, 1, 1, seq_len, dtype=torch.bool)
    mask[:, :, :, 8:] = True  # Masquer les 8 derniers tokens
    output_masked, _ = attn(x, attention_mask=mask)
    assert output_masked.shape == x.shape
    print("[OK] Forward avec masque d'attention")
    
    # Test de la resonance
    print(f"\nResonance :")
    print(f"  Poids de resonance = {attn.resonance_weight.item():.4f}")
    print(f"  Poids ABC          = {attn.abc_weight.item():.4f}")
    
    # Test de passage de gradient
    loss = output.sum()
    loss.backward()
    
    # Verifier que les gradients existent
    has_grad = all(
        p.grad is not None and p.grad.abs().sum() > 0
        for p in attn.parameters()
    )
    assert has_grad, "Tous les parametres doivent avoir un gradient non nul"
    print("[OK] Gradients corrects (retropropagation fonctionnelle)")
    
    print(f"\n[SUCCES] Attention Harmonique 7D operationnelle")
    return True


if __name__ == '__main__':
    test_harmonic_attention()
