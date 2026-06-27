"""
Modele Harmonique PUR (HarmonicPureForCausalLM)
================================================
Modele de langage causal avec ZERO parametre entrainable
dans l'attention et les couches de transformation.

Architecture :
1. Embedding de tokens FIXE (base sur PHI, pas entrainable)
2. N couches de decodeur harmonique pur (0 parametre)
3. LM Head FIXE (base sur PHI, pas entrainable)

Le modele complet a SEULEMENT les parametres suivants :
- Embedding : matrice fixe basee sur PHI (non entrainable)
- Couches : matrices fixes basees sur PHI (non entrainables)
- LM Head : matrice fixe basee sur PHI (non entrainable)

Soit 0 parametre entrainable au total.

Proprietes :
- Deterministe : la meme entree donne toujours la meme sortie
- Pas de retropropagation necessaire
- Pas d'optimiseur, pas de learning rate
- Peut tourner sur CPU avec des performances predictibles
"""

import math
from typing import List, Dict, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.harmonic_pure_layers import PureHarmonicDecoderLayer
from model.abc_kernel import PHI, ALPHA


# =========================================================================
# EMBEDDING HARMONIQUE FIXE
# =========================================================================

class HarmonicFixedEmbedding(nn.Module):
    """
    Embedding de tokens FIXE (non entrainable).
    
    Base sur les harmoniques spheriques :
    emb[token_id, i] = cos(token_id * i * PHI / d) * exp(-i * ALPHA / d)
    
    Proprietes :
    - Chaque token a une signature unique basee sur PHI
    - Les tokens proches ont des embeddings correles
    - Decroissance exponentielle avec la dimension
    """
    
    def __init__(self, vocab_size, hidden_size):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        
        # Embedding fixe base sur PHI
        token_ids = torch.arange(vocab_size, dtype=torch.float32).unsqueeze(1)
        dims = torch.arange(hidden_size, dtype=torch.float32).unsqueeze(0)
        
        # Phase harmonique
        phase = token_ids * dims * PHI / hidden_size
        
        # Amplitude (decroissance)
        amplitude = torch.exp(-dims * ALPHA / hidden_size)
        
        # Embedding = cos(phase) * amplitude
        embedding = torch.cos(phase) * amplitude
        
        # Normalisation
        embedding = embedding / torch.sqrt(torch.mean(embedding ** 2) + 1e-8)
        
        self.register_buffer('weight_fixed', embedding)
    
    def forward(self, input_ids):
        """
        Args:
            input_ids: [batch, seq_len]
        Returns:
            embeddings: [batch, seq_len, hidden_size]
        """
        return F.embedding(input_ids, self.weight_fixed)


# =========================================================================
# LM HEAD HARMONIQUE FIXE
# =========================================================================

class HarmonicFixedLMHead(nn.Module):
    """
    LM Head FIXE (non entrainable) — VERSION AMELIOREE.
    
    Projette les hidden states vers le vocabulaire avec normalisation
    pour eviter le biais vers les tokens harmoniques dominants.
    
    logits = (hidden_states @ embedding.T / sqrt(hidden_size)) * PHI
    """
    
    def __init__(self, embedding):
        super().__init__()
        # Poids lies avec l'embedding
        self.register_buffer('weight_fixed', embedding.weight_fixed.clone())
        
        # Pre-calculer la norme de chaque embedding pour normalisation
        with torch.no_grad():
            weight_norm = torch.norm(embedding.weight_fixed, dim=1, keepdim=True)
            self.register_buffer('weight_norm', weight_norm)
    
    def forward(self, hidden_states):
        """
        Args:
            hidden_states: [batch, seq_len, hidden_size]
        Returns:
            logits: [batch, seq_len, vocab_size] — distribution normalisee
        """
        # Calcul des logits (utiliser weight_fixed, pas weight)
        logits = F.linear(hidden_states, self.weight_fixed) * PHI
        
        # Normaliser pour compenser le biais harmonique
        logits = logits / (self.weight_norm.view(1, 1, -1) + 1e-8)
        logits = logits * PHI  # Re-appliquer PHI pour garder l'echelle
        
        return logits


# =========================================================================
# MODELE HARMONIQUE PUR
# =========================================================================

class HarmonicPureForCausalLM(nn.Module):
    """
    Modele de langage causal harmonique PUR.
    
    ZERO parametre entrainable.
    
    Architecture :
    1. HarmonicFixedEmbedding (fixe)
    2. N x PureHarmonicDecoderLayer (fixes)
    3. HarmonicFixedLMHead (fixe)
    
    Usage:
        model = HarmonicPureForCausalLM(
            vocab_size=50304,
            hidden_size=512,
            num_layers=8,
            max_len=2048
        )
        logits, signatures = model(input_ids)
        # Pas de loss, pas de backward - modele deterministe
    """
    
    def __init__(self, vocab_size=50304, hidden_size=512, num_layers=8,
                 intermediate_size=None, max_len=2048):
        super().__init__()
        
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.max_len = max_len
        
        if intermediate_size is None:
            intermediate_size = hidden_size * 4
        
        # Embedding fixe
        self.token_embedding = HarmonicFixedEmbedding(vocab_size, hidden_size)
        
        # Couches de decodeur harmonique pur
        self.layers = nn.ModuleList([
            PureHarmonicDecoderLayer(
                hidden_size=hidden_size,
                intermediate_size=intermediate_size,
                max_len=max_len
            )
            for _ in range(num_layers)
        ])
        
        # LM Head fixe (poids lies avec l'embedding)
        self.lm_head = HarmonicFixedLMHead(self.token_embedding)
    
    def forward(self, input_ids, attention_mask=None):
        """
        Forward pass du modele harmonique pur.
        
        Args:
            input_ids: [batch, seq_len]
            attention_mask: [batch, seq_len] optionnel (1=garder, 0=masquer)
        
        Returns:
            logits: [batch, seq_len, vocab_size]
            signatures: [num_layers, batch, seq_len, 7]
        """
        batch, seq_len = input_ids.shape
        
        # 1. Embedding fixe
        hidden_states = self.token_embedding(input_ids)
        
        # 2. Preparer le masque d'attention
        if attention_mask is not None:
            extended_mask = attention_mask[:, None, None, :]
            extended_mask = (1.0 - extended_mask) * torch.finfo(hidden_states.dtype).min
        else:
            extended_mask = None
        
        # 3. Passer a travers les couches harmoniques pures
        all_signatures = []
        for layer in self.layers:
            hidden_states, signatures = layer(hidden_states, extended_mask)
            all_signatures.append(signatures)
        
        # 4. LM Head fixe
        logits = self.lm_head(hidden_states)
        
        # Empiler les signatures
        signatures = torch.stack(all_signatures)  # [L, B, S, 7]
        
        return logits, signatures
    
    def generate(self, input_ids, max_new_tokens=100, temperature=0.8, 
                 top_k=40, top_p=0.9, repetition_penalty=1.1,
                 resonance_phi=True):
        """
        Generation autoregressive avec sampling harmonique enrichi.
        
        Caracteristiques :
        - Temperature sampling
        - Top-k filtering
        - Top-p (nucleus) sampling
        - Repetition penalty
        - Guidance par resonance phi (optionnelle)
        
        Args:
            input_ids: [batch, seq_len]
            max_new_tokens: Nombre de tokens a generer
            temperature: Temperature du softmax (0.0 = argmax)
            top_k: Top-k sampling (0 = desactive)
            top_p: Top-p nucleus sampling (1.0 = desactive)
            repetition_penalty: Penalite de repetition (>1.0 penalise)
            resonance_phi: Activer la guidance par resonance phi
        
        Returns:
            generated: [batch, seq_len + max_new_tokens]
            tokens_info: Liste des tokens generes avec leurs scores
        """
        self.eval()
        generated = input_ids.clone()
        tokens_info = []
        
        # Pre-calculer les frequences harmoniques pour la resonance
        if resonance_phi:
            # Les frequences harmoniques basees sur PHI
            harm_freqs = torch.tensor([
                1.0,           # fondamental
                PHI,           # nombre d'or
                PHI ** 2,      # puissance 2
                1.0 / PHI,     # sous-harmonique
                PHI ** 0.5,    # racine
            ], dtype=torch.float32)
            # Normaliser pour que la somme soit ~1
            harm_freqs = harm_freqs / harm_freqs.sum()
        
        with torch.no_grad():
            for step in range(max_new_tokens):
                # Tronquer si trop long
                if generated.shape[1] > self.max_len:
                    generated = generated[:, -self.max_len:]
                
                # Forward pass
                logits, signatures = self.forward(generated)
                
                # Dernier token
                next_logits = logits[:, -1, :].clone()
                
                # 1. Repetition penalty
                if repetition_penalty > 1.0:
                    for batch_idx in range(generated.shape[0]):
                        for token_id in generated[batch_idx, -50:]:  # fenetre 50 tokens
                            if next_logits[batch_idx, token_id] < 0:
                                next_logits[batch_idx, token_id] *= repetition_penalty
                            else:
                                next_logits[batch_idx, token_id] /= repetition_penalty
                
                # 2. Temperature
                if temperature > 0:
                    next_logits = next_logits / temperature
                else:
                    # Argmax
                    next_token = next_logits.argmax(dim=-1, keepdim=True)
                    generated = torch.cat([generated, next_token], dim=-1)
                    tokens_info.append({
                        'step': step,
                        'token_id': next_token.item(),
                        'mode': 'argmax'
                    })
                    continue
                
                # 3. Top-k filtering
                if top_k > 0:
                    top_k_vals, top_k_idx = torch.topk(next_logits, min(top_k, next_logits.shape[-1]), dim=-1)
                    next_logits = torch.full_like(next_logits, float('-inf'))
                    next_logits.scatter_(1, top_k_idx, top_k_vals)
                
                # 4. Top-p (nucleus) sampling
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(next_logits, descending=True, dim=-1)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    # Remove tokens with cumulative probability above threshold
                    sorted_indices_to_remove = cumulative_probs > top_p
                    # Shift the indices to keep at least min_tokens_to_keep
                    sorted_indices_to_remove[:, 1:] = sorted_indices_to_remove[:, :-1].clone()
                    sorted_indices_to_remove[:, 0] = False
                    
                    for batch_idx in range(next_logits.shape[0]):
                        indices_to_remove = sorted_indices[batch_idx][sorted_indices_to_remove[batch_idx]]
                        next_logits[batch_idx, indices_to_remove] = float('-inf')
                
                # 5. Resonance phi guidance
                if resonance_phi and step > 0:
                    # Utiliser la signature phi de la derniere couche
                    # pour favoriser les tokens harmoniquement aligns
                    phi_sig = signatures[-1, 0, -1, 0].item()  # phi de la derniere couche
                    
                    # Les tokens avec des ids proches des harmoniques de PHI
                    # recoivent un bonus de resonance
                    resonance_bonus = 0.1 * phi_sig
                    vocab_size = next_logits.shape[-1]
                    
                    # Tokens dont l'id est un multiple harmonique de PHI
                    harm_idx = (torch.arange(vocab_size, dtype=torch.float32) * PHI).long() % vocab_size
                    for h in harm_idx[:5]:  # 5 harmoniques
                        next_logits[0, h] += resonance_bonus
                
                # 6. Sampling
                probs = F.softmax(next_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                
                # 7. Concatener
                generated = torch.cat([generated, next_token], dim=-1)
                
                # 8. Infos
                token_score = float(probs[0, next_token[0, 0]].item())
                tokens_info.append({
                    'step': step,
                    'token_id': next_token.item(),
                    'score': token_score,
                    'temperature': temperature,
                    'top_k': top_k,
                    'top_p': top_p,
                })
                
                # Arret si token EOS (si l'ID est dans le vocabulaire)
                if next_token.item() == 3:  # <EOS>
                    break
        
        return generated, tokens_info
    
    def generate_text(self, prompt_tokens: List[int], max_new_tokens=100, **kwargs):
        """
        Generation a partir d'une liste de tokens.
        
        Args:
            prompt_tokens: Liste d'ids de tokens
            max_new_tokens: Nombre de tokens a generer
            **kwargs: Parametres passes a generate()
        
        Returns:
            generated_tokens: Liste complete des tokens
            tokens_info: Infos de generation
        """
        input_ids = torch.tensor([prompt_tokens], dtype=torch.long)
        generated, tokens_info = self.generate(input_ids, max_new_tokens, **kwargs)
        return generated[0].tolist(), tokens_info
    
    def get_signature_profile(self, input_ids):
        """
        Analyse le profil de signature harmonique.
        
        Args:
            input_ids: [batch, seq_len]
        Returns:
            profile: [num_layers, 7]
        """
        self.eval()
        with torch.no_grad():
            _, signatures = self.forward(input_ids)
            profile = signatures.mean(dim=(1, 2))  # [L, 7]
        return profile


# =========================================================================
# TEST
# =========================================================================

def test_harmonic_pure_model():
    """Teste le modele harmonique pur."""
    print("=" * 60)
    print("Test du Modele Harmonique PUR")
    print("=" * 60)
    
    vocab_size = 1000
    hidden_size = 128
    num_layers = 4
    max_len = 512
    
    model = HarmonicPureForCausalLM(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        max_len=max_len
    )
    
    # Compter les parametres
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"\nConfiguration :")
    print(f"  vocab_size       = {vocab_size}")
    print(f"  hidden_size      = {hidden_size}")
    print(f"  num_layers       = {num_layers}")
    print(f"  max_len          = {max_len}")
    print(f"  Parametres totaux = {total_params:,}")
    print(f"  Parametres entrainables = {trainable_params:,}")
    
    # Forward pass
    batch, seq_len = 2, 32
    input_ids = torch.randint(1, vocab_size - 1, (batch, seq_len))
    
    logits, signatures = model(input_ids)
    
    print(f"\nForward pass :")
    print(f"  Input      : {input_ids.shape}")
    print(f"  Logits     : {logits.shape}")
    print(f"  Signatures : {signatures.shape}")
    
    # Verifications
    assert logits.shape == (batch, seq_len, vocab_size)
    assert signatures.shape == (num_layers, batch, seq_len, 7)
    print("[OK] Shapes correctes")
    
    # Verifier que les signatures sont dans [0, 1]
    assert torch.all(signatures >= 0) and torch.all(signatures <= 1)
    print("[OK] Signatures dans [0, 1]")
    
    # Profil des signatures par couche
    profile = model.get_signature_profile(input_ids)
    dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']
    print(f"\nProfil de signature par couche :")
    for i in range(num_layers):
        vals = profile[i]
        print(f"  Couche {i:2d} : " + " | ".join(
            f"{d}={v.item():.3f}" for d, v in zip(dims, vals)
        ))
    
    # Test de reproductibilite
    logits2, sig2 = model(input_ids)
    assert torch.allclose(logits, logits2)
    assert torch.allclose(signatures, sig2)
    print("[OK] Reproducible (deterministe)")
    
    # Test de generation
    prompt = torch.randint(1, vocab_size - 1, (1, 8))
    generated = model.generate(prompt, max_new_tokens=16, temperature=0.8)
    print(f"\nGeneration :")
    print(f"  Prompt    : {prompt.shape}")
    print(f"  Genere    : {generated.shape}")
    assert generated.shape[1] == prompt.shape[1] + 16
    print("[OK] Generation autoregressive fonctionnelle")
    
    # Test avec masque d'attention
    mask = torch.ones(batch, seq_len, dtype=torch.long)
    mask[:, 16:] = 0
    logits_masked, _ = model(input_ids, attention_mask=mask)
    assert logits_masked.shape == logits.shape
    print("[OK] Forward avec masque d'attention")
    
    # Verifier que le modele n'a PAS de gradients
    has_grad_params = any(p.requires_grad for p in model.parameters())
    assert not has_grad_params, "Le modele ne doit pas avoir de parametres entrainables"
    print("[OK] Aucun parametre entrainable (verifie)")
    
    print(f"\n[SUCCES] Modele Harmonique PUR operationnel")
    print(f"  -> {total_params:,} parametres, dont {trainable_params} entrainables")
    print(f"  -> Peut tourner sur CPU sans retropropagation")
    return True


if __name__ == '__main__':
    test_harmonic_pure_model()
