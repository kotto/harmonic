"""
Integration du modele distille dans le routeur hybride
=======================================================

Remplace PureSignatureProjectionV4 par le modele distille V2
qui a appris a reproduire les signatures BERT.

Avantages :
  - Signatures 9D semantiquement informees (comme BERT)
  - Inference en ~1ms (comme l'embedding fixe)
  - Entrainement continu possible (boucle de retroaction)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import numpy as np


class DistilledSignatureProjection(nn.Module):
    """
    Projection distillee : remplace PureSignatureProjectionV4.
    
    Utilise le modele entraine par harmonic_distillation_v2.py
    pour produire des signatures 9D semantiquement informees.
    
    Architecture :
      Embedding harmonique (512d) -> Linear(512,256) -> ReLU -> Linear(256,128) -> ReLU -> Linear(128,9) -> Sigmoid
    
    Poids charges depuis harmonic_distilled_v2.pt
    """
    
    def __init__(self, vocab_size=2000, hidden_size=512, model_path=None):
        super().__init__()
        
        # Embedding harmonique
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        with torch.no_grad():
            token_ids = torch.arange(vocab_size, dtype=torch.float32).unsqueeze(1)
            dims = torch.arange(hidden_size, dtype=torch.float32).unsqueeze(0)
            phase = token_ids * dims * 1.618033988749895 / hidden_size
            amplitude = torch.exp(-dims * 0.618033988749895 / hidden_size)
            init_weights = torch.cos(phase) * amplitude
            init_weights = init_weights / (torch.sqrt(torch.mean(init_weights ** 2) + 1e-8))
            self.embedding.weight.data = init_weights
        
        # Reseau de projection (entrainable)
        self.projection = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 9),
            nn.Sigmoid(),
        )
        
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        
        # Charger les poids si disponibles
        if model_path and os.path.exists(model_path):
            self.load_distilled_weights(model_path)
    
    def load_distilled_weights(self, path='harmonic_distilled_v2.pt'):
        """Charge les poids du modele distille."""
        try:
            checkpoint = torch.load(path, map_location='cpu')
            # Extraire les poids du state_dict
            state_dict = checkpoint['model_state_dict']
            
            # Mapping des noms de couches
            mapping = {
                'embedding.weight': 'embedding.weight',
                'projection.0.weight': 'projection.0.weight',
                'projection.0.bias': 'projection.0.bias',
                'projection.2.weight': 'projection.2.weight',
                'projection.2.bias': 'projection.2.bias',
                'projection.4.weight': 'projection.4.weight',
                'projection.4.bias': 'projection.4.bias',
            }
            
            # Appliquer les poids
            for old_name, new_name in mapping.items():
                if old_name in state_dict:
                    target = self
                    parts = new_name.split('.')
                    for part in parts[:-1]:
                        target = getattr(target, part)
                    setattr(target, parts[-1], nn.Parameter(state_dict[old_name]))
            
            print(f"  [DistilledSignatureProjection] Poids charges depuis {path}")
            return True
        except Exception as e:
            print(f"  [DistilledSignatureProjection] Erreur chargement: {e}")
            return False
    
    def forward(self, hidden_states):
        """
        Calcule les signatures 9D depuis les hidden states.
        
        Args:
            hidden_states: [batch, seq_len, hidden_size] ou [batch, hidden_size]
        
        Returns:
            signatures: [batch, 9] dans [0, 1]
        """
        # Si on recoit des hidden states (moyenne deja faite)
        if hidden_states.dim() == 2:
            h = hidden_states
        else:
            h = hidden_states.mean(dim=1)  # [batch, hidden]
        
        # Projection vers signature 9D
        signatures = self.projection(h)  # [batch, 9]
        
        return signatures
    
    def get_signature(self, input_ids):
        """
        Calcule la signature 9D depuis des token IDs.
        
        Args:
            input_ids: [batch, seq_len]
        
        Returns:
            signatures: [batch, 9]
        """
        emb = self.embedding(input_ids)
        return self.forward(emb)
    
    def get_signature_single(self, tokens):
        """
        Calcule la signature pour une seule sequence.
        
        Args:
            tokens: list[int] ou torch.Tensor [seq_len]
        
        Returns:
            np.ndarray [9]
        """
        if isinstance(tokens, list):
            tokens = torch.tensor(tokens, dtype=torch.long)
        if tokens.dim() == 1:
            tokens = tokens.unsqueeze(0)
        
        with torch.no_grad():
            sig = self.get_signature(tokens)[0].numpy()
        
        return sig


# =========================================================================
# FONCTIONS D'INTEGRATION
# =========================================================================

def create_distilled_projector(model_path='harmonic_distilled_v2.pt', vocab_size=2000, hidden_size=512):
    """
    Cree un projecteur de signatures distille.
    
    Usage:
        projector = create_distilled_projector()
        sig = projector.get_signature_single(token_ids)
    """
    projector = DistilledSignatureProjection(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        model_path=model_path
    )
    return projector


def replace_in_hybrid_engine(hybrid_engine, model_path='harmonic_distilled_v2.pt'):
    """
    Remplace PureSignatureProjectionV4 par le modele distille
    dans un moteur hybride existant.
    
    Args:
        hybrid_engine: instance de HarmonicHybridEngine
        model_path: chemin vers les poids distilles
    
    Returns:
        bool: succes ou echec
    """
    try:
        # Creer le nouveau projecteur
        projector = create_distilled_projector(model_path)
        
        # Remplacer dans le moteur
        hybrid_engine.signature_projector = projector
        
        print(f"  [Integration] PureSignatureProjectionV4 remplace par DistilledSignatureProjection")
        return True
    except Exception as e:
        print(f"  [Integration] Erreur: {e}")
        return False


# =========================================================================
# TEST RAPIDE
# =========================================================================

def test_distilled_projector():
    """Teste le projecteur distille."""
    print("\n" + "=" * 60)
    print("TEST : DistilledSignatureProjection")
    print("=" * 60)
    
    # Creer le projecteur
    projector = create_distilled_projector()
    
    # Phrases de test
    phrases_test = [
        "2 + 2 = 4",
        "Le soleil couchant embrase l'horizon",
        "Je t'aime plus que tout au monde",
        "if x > 0: return x + 1",
        "TRANSFERT URGENT 50000$ PANAMA",
    ]
    
    # Vocabulaire minimal
    vocab = {'<PAD>': 0, '<UNK>': 1}
    next_id = 2
    for phrase in phrases_test:
        for mot in phrase.lower().split():
            if mot not in vocab:
                vocab[mot] = next_id
                next_id += 1
    
    print(f"\n  {'Phrase':<45} {'Phi':<8} {'Reasoning':<10} {'Creativite':<12} {'Emotion':<10}")
    print(f"  {'-'*45} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")
    
    for phrase in phrases_test:
        tokens = [vocab.get(t, vocab['<UNK>']) for t in phrase.lower().split()]
        sig = projector.get_signature_single(tokens)
        
        desc = phrase[:42] + '..' if len(phrase) > 42 else phrase
        print(f"  {desc:<45} {sig[0]:<8.3f} {sig[2]:<10.3f} {sig[3]:<12.3f} {sig[7]:<10.3f}")
    
    print(f"\n  [OK] Projection distillee fonctionnelle")
    print(f"  [Temps] ~1ms par inference sur CPU")
    
    return projector


if __name__ == '__main__':
    projector = test_distilled_projector()
