#!/usr/bin/env python3
"""
Harmonic Text Generator - Generateur de texte harmonique haute qualite
=======================================================================
Remplace le decodeur heuristique de Phase 5 par un veritable decodeur
harmonique avec vocabulaire appris et generation par resonance.

Architecture :
    1. HarmonicVocabulary : Vocabulaire harmonique (token embeddings + projections)
    2. HarmonicDecoder : Decodeur qui projette un vecteur harmonique vers
       une distribution sur le vocabulaire
    3. HarmonicTextGenerator : Generateur complet qui utilise le decodeur
       pour produire du texte token par token par resonance

Principe :
    Au lieu de templates textuels, chaque token est genere par resonance
    entre le vecteur harmonique courant et les embeddings du vocabulaire.
    Le token le plus resonant est selectionne.

    generation_token = argmax(resonance_measure(harmonic_vector, vocab_embeddings))

Dependances :
    - harmonic_complex_weights.py (resonance_measure, PHI)
    - harmonic_backprop.py (HarmonicBackpropNetwork)
"""

import os
import re
import json
import math
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from collections import Counter
from dataclasses import dataclass, field

from harmonic_complex_weights import (
    HarmonicLinear, resonance_measure, phase_rotation,
    PHI, PHI_INV, TAU
)
from harmonic_backprop import (
    HarmonicBackpropNetwork
)

# ----------------------------------------------------------------------------
# CONSTANTES
# ----------------------------------------------------------------------------

# Dimensions
VOCAB_SIZE = 256       # Taille du vocabulaire harmonique
EMBED_DIM = 64         # Dimension d'embedding
HIDDEN_DIM = 128       # Dimension cachee du decodeur
NUM_LAYERS = 3         # Couches du decodeur
NUM_HEADS = 4          # Tetes d'attention harmonique

# Generation
MAX_TOKENS = 128       # Tokens max par generation
TEMPERATURE = 0.8      # Temperature pour l'echantillonnage
TOP_K = 20             # Top-K sampling
REPETITION_PENALTY = 1.2  # Penalite de repetition

# Resonance
RESONANCE_THRESHOLD = 0.3  # Seuil de resonance minimal
FEEDBACK_STRENGTH = 0.12
COUPLING_STRENGTH = 0.06


# =========================================================================
# VOCABULAIRE HARMONIQUE
# =========================================================================

class HarmonicVocabulary:
    """
    Vocabulaire harmonique avec embeddings appris.
    
    Chaque token (mot ou sous-mot) est associe a un vecteur harmonique
    dans l'espace d'embedding. La resonance entre un vecteur harmonique
    et un embedding de token determine la probabilite de ce token.
    
    Le vocabulaire est construit a partir d'un corpus de textes,
    puis les embeddings sont appris par resonance.
    """
    
    def __init__(self, vocab_size=VOCAB_SIZE, embed_dim=EMBED_DIM):
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        
        # Vocabulaire : token -> index
        self.token_to_id = {}
        self.id_to_token = {}
        
        # Embeddings harmoniques des tokens
        self.token_embeddings = nn.Embedding(vocab_size, embed_dim)
        
        # Initialisation harmonique
        with torch.no_grad():
            nn.init.normal_(self.token_embeddings.weight, mean=0.0, std=PHI_INV)
            # Normaliser chaque embedding a la norme PHI_INV
            norms = self.token_embeddings.weight.norm(dim=1, keepdim=True)
            self.token_embeddings.weight = nn.Parameter(
                self.token_embeddings.weight / norms * PHI_INV
            )
        
        # Tokens speciaux
        self.PAD_ID = 0
        self.BOS_ID = 1  # Beginning of sequence
        self.EOS_ID = 2  # End of sequence
        self.UNK_ID = 3  # Unknown token
        
        # Initialiser les tokens speciaux
        self._init_special_tokens()
    
    def _init_special_tokens(self):
        """Initialise les tokens speciaux dans le vocabulaire."""
        special_tokens = ['<PAD>', '<BOS>', '<EOS>', '<UNK>']
        for i, token in enumerate(special_tokens):
            self.token_to_id[token] = i
            self.id_to_token[i] = token
    
    def build_from_texts(self, texts: List[str], min_freq: int = 2):
        """
        Construit le vocabulaire a partir d'une liste de textes.
        
        Args:
            texts: Liste de textes d'entrainement
            min_freq: Frequence minimale pour inclure un token
        """
        # Tokenisation simple (mots + ponctuation)
        all_tokens = []
        for text in texts:
            tokens = self._tokenize(text)
            all_tokens.extend(tokens)
        
        # Compter les frequences
        counter = Counter(all_tokens)
        
        # Filtrer par frequence
        vocab_tokens = [t for t, c in counter.items() if c >= min_freq]
        
        # Trier par frequence decroissante
        vocab_tokens.sort(key=lambda t: -counter[t])
        
        # Ajouter au vocabulaire (apres les tokens speciaux)
        start_id = len(self.token_to_id)
        for i, token in enumerate(vocab_tokens[:self.vocab_size - start_id]):
            idx = start_id + i
            self.token_to_id[token] = idx
            self.id_to_token[idx] = token
        
        # Mettre a jour la taille reelle
        self.vocab_size = len(self.token_to_id)
        
        print(f"Vocabulaire construit : {self.vocab_size} tokens")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenisation simple en mots et ponctuation.
        
        Args:
            text: Texte a tokeniser
        
        Returns:
            tokens: Liste de tokens
        """
        # Separer la ponctuation
        text = re.sub(r'([.,!?;:()\[\]{}"\'-])', r' \1 ', text)
        # Separer les apostrophes
        text = re.sub(r"n't", " n't", text)
        text = re.sub(r"'re", " 're", text)
        text = re.sub(r"'s", " 's", text)
        text = re.sub(r"'m", " 'm", text)
        text = re.sub(r"'ll", " 'll", text)
        text = re.sub(r"'ve", " 've", text)
        text = re.sub(r"'d", " 'd", text)
        # Tokeniser
        tokens = text.lower().split()
        return tokens
    
    def encode(self, text: str) -> torch.Tensor:
        """
        Encode un texte en sequence d'IDs.
        
        Args:
            text: Texte a encoder
        
        Returns:
            ids: Tenseur [seq_len] IDs des tokens
        """
        tokens = self._tokenize(text)
        ids = [self.BOS_ID]
        for token in tokens:
            ids.append(self.token_to_id.get(token, self.UNK_ID))
        ids.append(self.EOS_ID)
        return torch.tensor(ids, dtype=torch.long)
    
    def decode(self, ids: torch.Tensor) -> str:
        """
        Decode une sequence d'IDs en texte.
        
        Args:
            ids: Tenseur [seq_len] IDs des tokens
        
        Returns:
            text: Texte decode
        """
        tokens = []
        for idx in ids.tolist():
            if idx == self.EOS_ID:
                break
            if idx == self.BOS_ID or idx == self.PAD_ID:
                continue
            token = self.id_to_token.get(idx, '<UNK>')
            tokens.append(token)
        
        # Reassembler (enlevant les espaces avant ponctuation)
        text = ' '.join(tokens)
        text = re.sub(r'\s+([.,!?;:()\[\]{}"\'-])', r'\1', text)
        text = re.sub(r"\s+'\s+", "'", text)
        text = re.sub(r"\s+n't", "n't", text)
        
        return text
    
    def get_embeddings(self, ids: torch.Tensor) -> torch.Tensor:
        """
        Recupere les embeddings pour une sequence d'IDs.
        
        Args:
            ids: Tenseur [batch, seq_len] IDs des tokens
        
        Returns:
            embeddings: Tenseur [batch, seq_len, embed_dim]
        """
        return self.token_embeddings(ids)
    
    def get_all_embeddings(self) -> torch.Tensor:
        """
        Recupere tous les embeddings du vocabulaire.
        
        Returns:
            embeddings: Tenseur [vocab_size, embed_dim]
        """
        return self.token_embeddings.weight
    
    def resonance_with_vocab(self, vector: torch.Tensor) -> torch.Tensor:
        """
        Mesure la resonance d'un vecteur avec tous les tokens du vocabulaire.
        
        Args:
            vector: Tenseur [embed_dim] vecteur harmonique
        
        Returns:
            resonance: Tenseur [vocab_size] scores de resonance
        """
        # vector: [embed_dim] -> [1, embed_dim]
        # embeddings: [vocab_size, embed_dim]
        vector = vector.unsqueeze(0)  # [1, embed_dim]
        embeddings = self.get_all_embeddings().unsqueeze(0)  # [1, vocab_size, embed_dim]
        
        # Resonance measure
        resonance = resonance_measure(
            vector.unsqueeze(0).expand(embeddings.size(1), -1, -1),  # [vocab_size, 1, embed_dim]
            embeddings.transpose(0, 1)  # [vocab_size, 1, embed_dim]
        )  # [vocab_size, 1]
        
        return resonance.squeeze(-1)  # [vocab_size]
    
    def __len__(self):
        return self.vocab_size


# =========================================================================
# ATTENTION HARMONIQUE AMELIOREE (resonance_measure)
# =========================================================================

class HarmonicAttentionLayer(nn.Module):
    """
    Couche d'attention harmonique utilisant resonance_measure.
    
    Au lieu de softmax(Q @ K^T / sqrt(d)), on utilise :
        attention_weights = resonance_measure(Q, K)
    
    Proprietes :
        - resonance_measure est symetrique et bornee dans [-1, 1]
        - Pas de softmax necessaire (deja normalise)
        - La resonance capture la similarite harmonique complexe
        - Supporte le masque causal et padding
    """
    
    def __init__(self, embed_dim, num_heads=4, dropout=0.1):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        assert embed_dim % num_heads == 0, \
            f"embed_dim ({embed_dim}) doit etre divisible par num_heads ({num_heads})"
        
        # Projections Q, K, V harmoniques
        self.q_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.k_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.v_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.o_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        
        self.dropout = nn.Dropout(dropout)
        
        # Initialisation
        with torch.no_grad():
            nn.init.xavier_uniform_(self.v_proj.weight, gain=PHI_INV)
            nn.init.xavier_uniform_(self.o_proj.weight, gain=PHI_INV)
    
    def forward(self, x, attention_mask=None, causal=True):
        """
        Attention harmonique par resonance.
        
        Args:
            x: Tenseur [batch, seq_len, embed_dim]
            attention_mask: [batch, 1, 1, seq_len] (True = masque)
            causal: Masque causal (causal LM)
        
        Returns:
            output: [batch, seq_len, embed_dim]
            attention_weights: [batch, num_heads, seq_len, seq_len]
        """
        batch, seq_len, _ = x.shape
        
        # Projections harmoniques
        Q = self.q_proj(x)  # [B, S, D]
        K = self.k_proj(x)  # [B, S, D]
        V = self.v_proj(x)  # [B, S, D]
        
        # Reshape pour multi-head
        Q = Q.view(batch, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Calcul de la resonance pour chaque paire de têtes
        # Q: [B, H, S, D], K: [B, H, S, D]
        # resonance_measure entre chaque paire de positions
        
        # Pour chaque tête, calculer la matrice de resonance
        attention_weights = []
        for h in range(self.num_heads):
            q_h = Q[:, h, :, :]  # [B, S, D]
            k_h = K[:, h, :, :]  # [B, S, D]
            
            # resonance_measure pour chaque paire (i, j)
            # On utilise le produit scalaire complexe comme resonance
            # q_h @ k_h^T donne la similarite
            scores = torch.bmm(q_h, k_h.transpose(1, 2))  # [B, S, S]
            
            # Normaliser par la dimension
            scores = scores / math.sqrt(self.head_dim)
            
            # Appliquer tanh pour borner dans [-1, 1] (comme resonance_measure)
            scores = torch.tanh(scores)
            
            attention_weights.append(scores)
        
        attention_weights = torch.stack(attention_weights, dim=1)  # [B, H, S, S]
        
        # Masque causal
        if causal:
            causal_mask = torch.triu(
                torch.ones(seq_len, seq_len, device=x.device), diagonal=1
            ).bool()
            attention_weights = attention_weights.masked_fill(
                causal_mask.unsqueeze(0).unsqueeze(0), float('-inf')
            )
        
        # Masque d'attention (padding)
        if attention_mask is not None:
            attention_weights = attention_weights.masked_fill(
                attention_mask, float('-inf')
            )
        
        # Softmax sur la resonance
        attn_probs = F.softmax(attention_weights, dim=-1)
        attn_probs = self.dropout(attn_probs)
        
        # Appliquer l'attention
        output = torch.matmul(attn_probs, V)  # [B, H, S, D]
        
        # Reassemblage
        output = output.transpose(1, 2).contiguous().view(batch, seq_len, -1)
        output = self.o_proj(output)
        
        return output, attn_probs


# =========================================================================
# DECODEUR HARMONIQUE
# =========================================================================

class HarmonicDecoder(nn.Module):
    """
    Decodeur harmonique qui projette un vecteur harmonique vers
    une distribution sur le vocabulaire.
    
    Architecture :
        vecteur harmonique [embed_dim]
            -> HarmonicAttentionLayer (resonance)
            -> HarmonicBackpropNetwork (feedback)
            -> Projection lineaire -> distribution vocabulaire
    
    Le decodeur apprend a associer chaque region de l'espace harmonique
    a des tokens specifiques du vocabulaire.
    """
    
    def __init__(self, vocab_size=VOCAB_SIZE, embed_dim=EMBED_DIM,
                 hidden_dim=HIDDEN_DIM, num_layers=NUM_LAYERS,
                 num_heads=NUM_HEADS):
        super().__init__()
        
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Vocabulaire harmonique
        self.vocab = HarmonicVocabulary(vocab_size, embed_dim)
        
        # Embedding de position harmonique
        self.pos_embedding = nn.Embedding(MAX_TOKENS, embed_dim)
        with torch.no_grad():
            nn.init.normal_(self.pos_embedding.weight, mean=0.0, std=PHI_INV)
        
        # Couches d'attention harmonique
        self.attention_layers = nn.ModuleList([
            HarmonicAttentionLayer(embed_dim, num_heads)
            for _ in range(num_layers)
        ])
        
        # Layer norms
        self.input_norm = nn.LayerNorm(embed_dim)
        self.output_norm = nn.LayerNorm(embed_dim)
        
        # Projection finale vers vocabulaire
        self.lm_head = nn.Linear(embed_dim, vocab_size, bias=False)
        
        # Lier les poids de l'embedding et du LM head (weight tying)
        self.lm_head.weight = self.vocab.token_embeddings.weight
        
        # Initialisation
        with torch.no_grad():
            nn.init.xavier_uniform_(self.lm_head.weight, gain=0.5)
    
    def forward(self, input_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass du decodeur.
        
        Args:
            input_ids: [batch, seq_len] IDs des tokens d'entree
            attention_mask: [batch, 1, 1, seq_len] optionnel
        
        Returns:
            logits: [batch, seq_len, vocab_size] logits de prediction
        """
        batch, seq_len = input_ids.shape
        
        # Embedding des tokens
        x = self.vocab.get_embeddings(input_ids)  # [B, S, D]
        
        # Ajout de l'embedding de position
        positions = torch.arange(seq_len, device=input_ids.device)
        x = x + self.pos_embedding(positions).unsqueeze(0)
        
        # Normalisation d'entree
        x = self.input_norm(x)
        
        # Couches d'attention harmonique
        for attn_layer in self.attention_layers:
            x, _ = attn_layer(x, attention_mask, causal=True)
        
        # Normalisation de sortie
        x = self.output_norm(x)
        
        # Projection vers vocabulaire
        logits = self.lm_head(x)  # [B, S, V]
        
        return logits
    
    def generate_from_vector(self, vector: torch.Tensor,
                             max_tokens: int = MAX_TOKENS,
                             temperature: float = TEMPERATURE,
                             top_k: int = TOP_K) -> str:
        """
        Genere du texte a partir d'un vecteur harmonique.
        
        Args:
            vector: [embed_dim] vecteur harmonique
            max_tokens: Nombre max de tokens a generer
            temperature: Temperature d'echantillonnage
            top_k: Top-K sampling
        
        Returns:
            text: Texte genere
        """
        self.eval()
        
        with torch.no_grad():
            # Commencer par le token BOS
            generated = [self.vocab.BOS_ID]
            input_ids = torch.tensor([generated], dtype=torch.long)
            
            for _ in range(max_tokens):
                # Forward pass
                logits = self.forward(input_ids)  # [1, seq_len, vocab_size]
                
                # Prendre le dernier token
                next_logits = logits[0, -1, :]  # [vocab_size]
                
                # Ajouter la resonance avec le vecteur harmonique
                resonance_scores = self.vocab.resonance_with_vocab(vector)
                next_logits = next_logits + resonance_scores * FEEDBACK_STRENGTH
                
                # Temperature
                next_logits = next_logits / temperature
                
                # Penalite de repetition
                for token_id in set(generated):
                    next_logits[token_id] /= REPETITION_PENALTY
                
                # Top-K filtering
                if top_k > 0:
                    indices_to_remove = next_logits.argsort(descending=True)[top_k:]
                    next_logits[indices_to_remove] = float('-inf')
                
                # Echantillonnage
                probs = F.softmax(next_logits, dim=-1)
                next_token = torch.multinomial(probs, 1).item()
                
                # Arret si EOS
                if next_token == self.vocab.EOS_ID:
                    break
                
                generated.append(next_token)
                input_ids = torch.tensor([generated], dtype=torch.long)
        
        # Decoder en texte
        text = self.vocab.decode(torch.tensor(generated))
        
        return text
    
    def train_step(self, input_ids: torch.Tensor,
                   labels: Optional[torch.Tensor] = None) -> Dict[str, Any]:
        """
        Pas d'entrainement du decodeur.
        
        Args:
            input_ids: [batch, seq_len] sequences d'entree
            labels: [batch, seq_len] cibles (shifted)
        
        Returns:
            metrics: Dictionnaire de metriques
        """
        self.train()
        
        if labels is None:
            labels = input_ids[:, 1:].contiguous()
            input_ids = input_ids[:, :-1].contiguous()
        
        logits = self.forward(input_ids)
        
        # Cross-entropy loss
        loss = F.cross_entropy(
            logits.view(-1, self.vocab_size),
            labels.view(-1),
            ignore_index=self.vocab.PAD_ID
        )
        
        # Perplexity
        perplexity = math.exp(min(loss.item(), 10))
        
        return {
            'loss': loss,
            'perplexity': perplexity
        }


# =========================================================================
# GENERATEUR DE TEXTE HARMONIQUE HAUTE QUALITE
# =========================================================================

class HarmonicTextGenerator:
    """
    Generateur de texte harmonique haute qualite.
    
    Combine :
        1. HarmonicResonanceGenerator (Phase 5) pour l'evolution du template
        2. HarmonicDecoder pour la generation token par token
        3. Resonance avec le vocabulaire pour la selection des tokens
    
    Le processus de generation :
        1. Le template et le prompt sont encodes en vecteurs harmoniques
        2. Le reseau de resonance fait evoluer le template vers le prompt
        3. Le decodeur genere du texte token par token, guide par le vecteur
        4. Chaque token est choisi par resonance avec le vocabulaire
    """
    
    def __init__(self, vocab_size=VOCAB_SIZE, embed_dim=EMBED_DIM,
                 hidden_dim=HIDDEN_DIM, num_layers=NUM_LAYERS):
        
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Decodeur harmonique
        self.decoder = HarmonicDecoder(
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers
        )
        
        # Reseau de resonance (pour l'evolution du template)
        layer_sizes = [embed_dim]
        for _ in range(num_layers - 1):
            layer_sizes.append(hidden_dim)
        layer_sizes.append(embed_dim)
        
        self.resonance_network = HarmonicBackpropNetwork(
            layer_sizes,
            feedback_strength=FEEDBACK_STRENGTH,
            coupling_strength=COUPLING_STRENGTH
        )
        
        # Encodeur de texte simple (pour les prompts)
        self.text_encoder = self._build_text_encoder()
        
        # Statistiques
        self.stats = {
            'total_generations': 0,
            'avg_tokens': 0,
            'total_tokens': 0
        }
    
    def _build_text_encoder(self):
        """Cree un encodeur de texte simple."""
        char_vocab = {c: i for i, c in enumerate(
            'abcdefghijklmnopqrstuvwxyz0123456789 .,!?;:()[]{}"\'-_/\\@#$%^&*+=<>'
        )}
        
        class SimpleEncoder(nn.Module):
            def __init__(self, char_vocab, embed_dim):
                super().__init__()
                self.char_vocab = char_vocab
                self.vocab_size = len(char_vocab)
                self.embed_dim = embed_dim
                self.proj = nn.Linear(self.vocab_size, embed_dim, bias=False)
                
                with torch.no_grad():
                    nn.init.normal_(self.proj.weight, mean=0.0, std=PHI_INV)
            
            def forward(self, text):
                if not text:
                    return torch.zeros(self.embed_dim)
                
                text = text.lower()
                char_vectors = []
                for c in text[:200]:
                    if c in self.char_vocab:
                        idx = self.char_vocab[c]
                        one_hot = torch.zeros(self.vocab_size)
                        one_hot[idx] = 1.0
                        char_vectors.append(one_hot)
                
                if not char_vectors:
                    return torch.zeros(self.embed_dim)
                
                char_tensor = torch.stack(char_vectors)
                projected = self.proj(char_tensor)
                
                # Pooling harmonique
                weights = torch.tensor([PHI_INV ** i for i in range(len(projected))])
                weights = weights / weights.sum()
                
                vector = (projected * weights.unsqueeze(-1)).sum(dim=0)
                
                norm = vector.norm()
                if norm > 0:
                    vector = vector / norm * PHI_INV
                
                return vector
        
        return SimpleEncoder(char_vocab, self.embed_dim)
    
    def generate(self, template_text: str, prompt_text: str,
                 max_tokens: int = MAX_TOKENS,
                 temperature: float = TEMPERATURE,
                 top_k: int = TOP_K) -> str:
        """
        Genere du texte de haute qualite par resonance harmonique.
        
        Args:
            template_text: Texte du template (condition initiale)
            prompt_text: Texte du prompt (cible)
            max_tokens: Nombre max de tokens
            temperature: Temperature d'echantillonnage
            top_k: Top-K sampling
        
        Returns:
            text: Texte genere
        """
        # 1. Encoder le template et le prompt
        template_vec = self.text_encoder(template_text)
        prompt_vec = self.text_encoder(prompt_text)
        
        # 2. Faire evoluer le template par resonance
        current = template_vec.clone().unsqueeze(0)  # [1, embed_dim]
        prompt_vec_batch = prompt_vec.unsqueeze(0)   # [1, embed_dim]
        
        for i in range(10):  # iterations de resonance
            output = self.resonance_network(current)
            loss, resonances = self.resonance_network.train_step(
                current, prompt_vec_batch
            )
            current = output
        
        # 3. Generer du texte a partir du vecteur final
        harmonic_vector = current.squeeze(0)  # [embed_dim]
        
        text = self.decoder.generate_from_vector(
            harmonic_vector,
            max_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k
        )
        
        # 4. Mettre a jour les stats
        self.stats['total_generations'] += 1
        token_count = len(self.decoder.vocab._tokenize(text))
        self.stats['total_tokens'] += token_count
        self.stats['avg_tokens'] = self.stats['total_tokens'] / self.stats['total_generations']
        
        return text
    
    def generate_from_prompt(self, prompt_text: str,
                              max_tokens: int = MAX_TOKENS,
                              temperature: float = TEMPERATURE) -> str:
        """
        Genere du texte directement a partir d'un prompt (sans template).
        
        Args:
            prompt_text: Texte du prompt
            max_tokens: Nombre max de tokens
            temperature: Temperature
        
        Returns:
            text: Texte genere
        """
        # Utiliser le prompt lui-meme comme template
        return self.generate(prompt_text, prompt_text, max_tokens, temperature)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de generation."""
        return {
            **self.stats,
            'vocab_size': self.decoder.vocab.vocab_size,
            'embed_dim': self.embed_dim,
            'hidden_dim': self.hidden_dim,
            'num_layers': self.num_layers,
            'decoder_params': sum(p.numel() for p in self.decoder.parameters()),
            'resonance_params': sum(p.numel() for p in self.resonance_network.parameters())
        }


# =========================================================================
# TESTS
# =========================================================================

def test_harmonic_vocabulary():
    """Test du vocabulaire harmonique."""
    print("=" * 60)
    print("TEST : HarmonicVocabulary")
    print("=" * 60)
    
    vocab = HarmonicVocabulary(vocab_size=64, embed_dim=16)
    
    print(f"\nVocabulaire initial : {len(vocab)} tokens")
    print(f"  Embed dim: {vocab.embed_dim}")
    
    # Tester l'encodage
    text = "Bonjour le monde"
    ids = vocab.encode(text)
    print(f"\nEncodage de '{text}':")
    print(f"  IDs: {ids.tolist()}")
    
    # Tester le decodage
    decoded = vocab.decode(ids)
    print(f"  Decode: '{decoded}'")
    
    # Tester les embeddings
    embeddings = vocab.get_embeddings(ids.unsqueeze(0))
    print(f"  Embeddings shape: {embeddings.shape}")
    
    # Tester la resonance avec le vocabulaire
    vector = torch.randn(16)
    resonance = vocab.resonance_with_vocab(vector)
    print(f"  Resonance shape: {resonance.shape}")
    print(f"  Resonance min: {resonance.min().item():.4f}")
    print(f"  Resonance max: {resonance.max().item():.4f}")
    
    assert ids[0] == vocab.BOS_ID, "Premier token doit etre BOS"
    assert ids[-1] == vocab.EOS_ID, "Dernier token doit etre EOS"
    assert embeddings.shape == (1, len(ids), 16), f"Shape incorrecte: {embeddings.shape}"
    assert resonance.shape == (64,), f"Shape resonance incorrecte: {resonance.shape}"
    
    print("\n[OK] Vocabulaire harmonique operationnel")
    return True


def test_harmonic_attention_layer():
    """Test de la couche d'attention harmonique."""
    print("=" * 60)
    print("TEST : HarmonicAttentionLayer")
    print("=" * 60)
    
    batch, seq_len, embed_dim, num_heads = 2, 8, 32, 4
    
    attn = HarmonicAttentionLayer(embed_dim, num_heads)
    
    print(f"\nArchitecture:")
    print(f"  embed_dim: {embed_dim}")
    print(f"  num_heads: {num_heads}")
    print(f"  head_dim: {attn.head_dim}")
    
    x = torch.randn(batch, seq_len, embed_dim)
    output, attn_weights = attn(x)
    
    print(f"\nForward pass:")
    print(f"  Input: {x.shape}")
    print(f"  Output: {output.shape}")
    print(f"  Attention weights: {attn_weights.shape}")
    
    assert output.shape == x.shape, f"Output shape: {output.shape}"
    assert attn_weights.shape == (batch, num_heads, seq_len, seq_len)
    
    # Test avec masque causal
    output_causal, _ = attn(x, causal=True)
    assert output_causal.shape == x.shape
    
    # Test de gradient
    loss = output.sum()
    loss.backward()
    
    has_grad = all(
        p.grad is not None and p.grad.abs().sum() > 0
        for p in attn.parameters()
    )
    assert has_grad, "Tous les parametres doivent avoir un gradient"
    
    print("\n[OK] Attention harmonique operationnelle")
    return True


def test_harmonic_decoder():
    """Test du decodeur harmonique."""
    print("=" * 60)
    print("TEST : HarmonicDecoder")
    print("=" * 60)
    
    decoder = HarmonicDecoder(
        vocab_size=64,
        embed_dim=32,
        hidden_dim=64,
        num_layers=2,
        num_heads=4
    )
    
    print(f"\nArchitecture:")
    print(f"  vocab_size: {decoder.vocab_size}")
    print(f"  embed_dim: {decoder.embed_dim}")
    print(f"  hidden_dim: {decoder.hidden_dim}")
    print(f"  num_layers: {decoder.num_layers}")
    print(f"  Parametres: {sum(p.numel() for p in decoder.parameters()):,}")
    
    # Forward pass
    batch, seq_len = 2, 8
    input_ids = torch.randint(0, 64, (batch, seq_len))
    logits = decoder(input_ids)
    
    print(f"\nForward pass:")
    print(f"  Input: {input_ids.shape}")
    print(f"  Logits: {logits.shape}")
    
    assert logits.shape == (batch, seq_len, 64), f"Shape incorrecte: {logits.shape}"
    
    # Train step
    metrics = decoder.train_step(input_ids)
    print(f"\nTrain step:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
    
    # Generation from vector
    vector = torch.randn(32)
    text = decoder.generate_from_vector(vector, max_tokens=20)
    print(f"\nGeneration from vector:")
    print(f"  Texte: '{text}'")
    
    assert len(text) > 0, "Texte genere vide"
    
    print("\n[OK] Decodeur harmonique operationnel")
    return True


def test_harmonic_text_generator():
    """Test du generateur de texte harmonique haute qualite."""
    print("=" * 60)
    print("TEST : HarmonicTextGenerator")
    print("=" * 60)
    
    generator = HarmonicTextGenerator(
        vocab_size=64,
        embed_dim=16,
        hidden_dim=32,
        num_layers=2
    )
    
    print(f"\nArchitecture:")
    print(f"  vocab_size: {generator.decoder.vocab_size}")
    print(f"  embed_dim: {generator.embed_dim}")
    print(f"  hidden_dim: {generator.hidden_dim}")
    print(f"  num_layers: {generator.num_layers}")
    
    # Tester la generation avec template
    template = "Reponse harmonique pour le prompt suivant"
    prompt = "Expliquer le concept de resonance"
    
    print(f"\nTemplate: {template}")
    print(f"Prompt: {prompt}")
    
    text = generator.generate(template, prompt, max_tokens=30)
    print(f"\nTexte genere ({len(text)} chars):")
    print(f"  '{text}'")
    
    assert len(text) > 0, "Texte genere vide"
    
    # Tester la generation sans template
    text2 = generator.generate_from_prompt("Bonjour le monde", max_tokens=20)
    print(f"\nGeneration sans template:")
    print(f"  '{text2}'")
    
    assert len(text2) > 0, "Texte genere vide"
    
    # Stats
    stats = generator.get_stats()
    print(f"\nStats:")
    for k, v in stats.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.2f}")
        else:
            print(f"  {k}: {v}")
    
    print("\n[OK] Generateur de texte harmonique operationnel")
    return True


def run_all_tests():
    """Execute tous les tests du generateur harmonique."""
    print("\n" + "=" * 60)
    print("GENERATEUR DE TEXTE HARMONIQUE - TESTS COMPLETS")
    print("=" * 60)
    
    tests = [
        ("HarmonicVocabulary", test_harmonic_vocabulary),
        ("HarmonicAttentionLayer", test_harmonic_attention_layer),
        ("HarmonicDecoder", test_harmonic_decoder),
        ("HarmonicTextGenerator", test_harmonic_text_generator),
    ]
    
    passed = 0
    for name, test_fn in tests:
        print()
        try:
            result = test_fn()
            if result:
                print(f"\n  >>> {name}: [OK]")
                passed += 1
            else:
                print(f"\n  >>> {name}: [ECHEC]")
        except Exception as e:
            import traceback
            print(f"\n  >>> {name}: [ERREUR] {e}")
            traceback.print_exc()
    
    print(f"\n{'=' * 60}")
    print(f"RESULTATS : {passed}/{len(tests)} tests passes")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_all_tests()
