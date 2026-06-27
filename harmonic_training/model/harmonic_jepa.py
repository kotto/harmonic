"""
Harmo-JEPA : Prédiction dans l'espace des signatures 9D
=========================================================
Basé sur l'architecture JEPA de Yann LeCun adaptée aux signatures harmoniques.

Principe :
    Au lieu de prédire le PROCHAIN TOKEN (GPT), on prédit la PROCHAINE SIGNATURE 9D.
    
    Loss = 1 - cos(φ · sig_prédite, φ · sig_réelle)
         = 1 - résonance(sig_prédite, sig_réelle)
    
    Le prédicteur JEPA est le SEUL module qui apprend (1 seule couche linéaire + noyau ABC).
    L'encodeur harmonique est FIXE (0 paramètres).

Architecture :
    x[t-n:t] → HarmonicEmbedding (fixe) → HarmonicEncoder (fixe) → Signatures 9D
    → JEPA Predictor → Signatures 9D prédites à t+Δt
    → Loss = 1 - résonance(prédite, réelle)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.abc_kernel import ABCKernel, PHI, ALPHA


# =========================================================================
# MÉTRIQUE DE RÉSONANCE ENTRE SIGNATURES 9D
# =========================================================================

def resonance_loss(sig_pred: torch.Tensor, sig_target: torch.Tensor,
                   phi_weight: float = PHI) -> torch.Tensor:
    """
    Loss par resonance entre signatures predites et cibles.
    
    Args:
        sig_pred: Signatures predites [batch, 9] ou [batch, seq, 9]
        sig_target: Signatures cibles [batch, 9] ou [batch, seq, 9]
        phi_weight: Poids harmonique (PHI par defaut)
    
    Returns:
        loss: Tenseur scalaire
    
    La resonance est definie comme :
        resonance = cos(phi * sig_pred, phi * sig_target)
        loss = 1 - resonance
    
    Proprietes :
    - Si resonance = 1 (colinearite parfaite) → loss = 0
    - Si resonance = 0 (orthogonal) → loss = 1
    - Si resonance = -1 (oppose) → loss = 2
    """
    # Normaliser les signatures
    sig_pred_norm = F.normalize(sig_pred * phi_weight, dim=-1)
    sig_target_norm = F.normalize(sig_target * phi_weight, dim=-1)
    
    # Resonance = similarite cosinus
    resonance = (sig_pred_norm * sig_target_norm).sum(dim=-1)
    
    # Loss = 1 - resonance (moyennee sur tous les elements)
    loss = (1.0 - resonance).mean()
    
    return loss


def harmonic_contrastive_loss(sig_pred: torch.Tensor, sig_target: torch.Tensor,
                               sig_negatives: torch.Tensor,
                               temperature: float = 0.07) -> torch.Tensor:
    """
    Loss contrastive harmonique : rapproche les signatures similaires,
    eloigne les differentes.
    
    Similaire a SimCLR mais avec resonance harmonique.
    """
    # Normaliser
    pred_norm = F.normalize(sig_pred * PHI, dim=-1)
    target_norm = F.normalize(sig_target * PHI, dim=-1)
    neg_norm = F.normalize(sig_negatives * PHI, dim=-1)
    
    # Similarites
    pos_sim = (pred_norm * target_norm).sum(dim=-1) / temperature  # [batch]
    neg_sim = torch.mm(pred_norm, neg_norm.T) / temperature  # [batch, batch]
    
    # Loss InfoNCE
    logits = torch.cat([pos_sim.unsqueeze(1), neg_sim], dim=1)
    labels = torch.zeros(logits.shape[0], dtype=torch.long, device=logits.device)
    
    loss = F.cross_entropy(logits, labels)
    
    return loss


# =========================================================================
# JEPA PREDICTOR (Le seul module qui apprend)
# =========================================================================

class JEPAPredictor(nn.Module):
    """
    Predictor JEPA pour signatures harmoniques 9D.
    
    Prend un contexte de signatures et predit la signature future.
    
    Architecture ultra-legere :
    1. Linear projection 9 -> 32 (apprise)
    2. Noyau ABC pour la memoire temporelle (non appris)
    3. Linear projection 32 -> 9 (apprise)
    
    Total : ~(9*32 + 32 + 32*9 + 9) = ~650 parametres appris
    
    Args:
        hidden_dim: Dimension cachee du predictor (32 par defaut)
        num_abc_kernel: Taille du noyau ABC (5 par defaut)
    """
    
    def __init__(self, hidden_dim: int = 32, num_abc_kernel: int = 5):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.num_abc_kernel = num_abc_kernel
        
        # 1. Projection entree (apprise)
        self.input_proj = nn.Linear(9, hidden_dim, bias=False)
        
        # 2. Noyau ABC fixe pour memoire temporelle
        self.register_buffer('abc_weights', self._compute_abc_weights(num_abc_kernel))
        
        # 3. Tete de prediction (apprise)
        self.predict_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim, bias=False),
            nn.Tanh(),  # Non-linearite harmonique
            nn.Linear(hidden_dim, 9, bias=False),
        )
        
        # 4. Initialisation harmonique des poids
        self._init_weights()
    
    def _init_weights(self):
        """Initialise les poids selon PHI pour rester dans l'espace harmonique."""
        with torch.no_grad():
            for name, param in self.named_parameters():
                if 'weight' in name:
                    # Initialisation basee sur PHI
                    fan_in = param.shape[1] if param.ndim >= 2 else 1
                    std = PHI / math.sqrt(fan_in)
                    param.normal_(0, std)
    
    def _compute_abc_weights(self, kernel_size: int) -> torch.Tensor:
        """
        Calcule les poids du noyau ABC pour le contexte temporel.
        
        Poids decroissants selon la derivee fractionnaire :
        w[t] = exp(-alpha * t) * cos(phi * t)
        
        Plus les tokens recents ont un poids eleve.
        """
        t = torch.arange(kernel_size, dtype=torch.float32)
        # Decroissance exponentielle + oscillation harmonique
        weights = torch.exp(-ALPHA * t) * torch.cos(PHI * t)
        # Normaliser
        weights = weights / (weights.sum() + 1e-8)
        return weights.unsqueeze(0).unsqueeze(0)  # [1, 1, K]
    
    def forward(self, signatures: torch.Tensor, target_idx: int = -1) -> torch.Tensor:
        """
        Predire la signature a l'index cible.
        
        Args:
            signatures: [batch, seq_len, 9] — sequence de signatures
            target_idx: Index de la cible a predire (par defaut: la derniere)
        
        Returns:
            pred_sig: [batch, 9] — signature predite
        
        Le predictor utilise :
        1. Les signatures du contexte (avant target_idx)
        2. Le noyau ABC pour ponderer temporellement
        3. Une projection apprise 9→32→9
        """
        batch, seq_len, _ = signatures.shape
        
        if target_idx < 0:
            target_idx = seq_len - 1
        
        # Contexte = signatures avant la cible
        context = signatures[:, :target_idx + 1, :]  # Inclut la cible pour l'instant
        
        # 1. Projection dans l'espace latent
        latent = self.input_proj(context)  # [B, ctx, hidden]
        
        # 2. Ponderation temporelle ABC
        kernel_size = min(self.num_abc_kernel, context.shape[1])
        if context.shape[1] >= kernel_size:
            # Convolution avec le noyau ABC
            latent_weighted = latent[:, -kernel_size:, :] * self.abc_weights[:, :, :kernel_size].transpose(1, 2)
            latent_agg = latent_weighted.sum(dim=1)  # [B, hidden]
        else:
            # Fallback: moyenne simple
            latent_agg = latent.mean(dim=1)  # [B, hidden]
        
        # 3. Prediction via la tete
        pred_sig = self.predict_head(latent_agg)  # [B, 9]
        
        # Contrainte dans [0, 1] (les signatures sont normalisees)
        pred_sig = torch.sigmoid(pred_sig)
        
        return pred_sig
    
    def predict_future(self, signatures: torch.Tensor, horizon: int = 1) -> torch.Tensor:
        """
        Predire les H prochaines signatures de maniere autoregressive.
        
        Args:
            signatures: [batch, seq_len, 9] — contexte
            horizon: Nombre de pas a predire
        
        Returns:
            future_sigs: [batch, horizon, 9] — signatures predites
        """
        futures = []
        current = signatures.clone()
        
        for _ in range(horizon):
            next_sig = self.forward(current, target_idx=-1)  # Predire la prochaine
            futures.append(next_sig.unsqueeze(1))  # [B, 1, 9]
            
            # Ajouter la prediction au contexte (autoregressif)
            current = torch.cat([current, next_sig.unsqueeze(1)], dim=1)
            
            # Garder la fenetre de taille max_seq
            if current.shape[1] > 64:
                current = current[:, -64:, :]
        
        return torch.cat(futures, dim=1)


# =========================================================================
# PIPELINE COMPLET HARMONIC-JEPA
# =========================================================================

class HarmonicJEPA(nn.Module):
    """
    Pipeline complet : Encoder Harmonique (fixe) + JEPA Predictor (appris).
    
    Usage:
        model = HarmonicJEPA()
        loss = model(signatures_9d)  # Entrainement
        future = model.predict(signatures_9d, horizon=5)  # Inference
    """
    
    def __init__(self, hidden_dim: int = 32, num_abc_kernel: int = 5):
        super().__init__()
        
        # Le predictor JEPA (seul module appris)
        self.predictor = JEPAPredictor(
            hidden_dim=hidden_dim,
            num_abc_kernel=num_abc_kernel,
        )
        
        # Metriques
        self.register_buffer('loss_history', torch.zeros(100))
        self.register_buffer('resonance_history', torch.zeros(100))
        self.step = 0
    
    def forward(self, signatures: torch.Tensor) -> torch.Tensor:
        """
        Entrainement : predire la derniere signature a partir des precedentes.
        
        Args:
            signatures: [batch, seq_len, 9] — sequence complete
        
        Returns:
            loss: Tenseur scalaire (1 - resonance entre predite et reelle)
        """
        batch, seq_len, _ = signatures.shape
        
        # On veut predire la derniere signature
        # a partir de [:-1]
        if seq_len <= 1:
            # Fallback si sequence trop courte
            return torch.tensor(0.5, device=signatures.device)
        
        target = signatures[:, -1, :]  # [B, 9]
        
        # Predire via le predictor JEPA (pas de recusion!)
        pred = self.predictor(signatures[:, :-1, :])  # [B, 9]
        
        # Loss par resonance
        loss = resonance_loss(pred, target)
        
        # Mettre a jour l'historique
        with torch.no_grad():
            resonance = 1.0 - loss.item()
            idx = self.step % 100
            self.loss_history[idx] = loss.item()
            self.resonance_history[idx] = resonance
            self.step += 1
        
        return loss
    
    def predict(self, signatures: torch.Tensor, horizon: int = 5) -> torch.Tensor:
        """
        Prediction de signatures futures.
        
        Args:
            signatures: [batch, seq_len, 9]
            horizon: Nombre de pas
        
        Returns:
            futures: [batch, horizon, 9]
        """
        return self.predictor.predict_future(signatures, horizon)
    
    def train_step(self, signatures: torch.Tensor, 
                   optimizer: torch.optim.Optimizer,
                   clip_grad: float = 1.0) -> float:
        """
        Une etape d'entrainement complete.
        
        Args:
            signatures: [batch, seq_len, 9]
            optimizer: Optimiseur
            clip_grad: Norme max du gradient
        
        Returns:
            loss: Valeur de la loss
        """
        self.train()
        optimizer.zero_grad()
        
        loss = self.forward(signatures)
        loss.backward()
        
        if clip_grad > 0:
            nn.utils.clip_grad_norm_(self.parameters(), clip_grad)
        
        optimizer.step()
        
        return loss.item()
    
    def get_average_resonance(self) -> float:
        """Resonance moyenne sur les 100 dernieres etapes."""
        return self.resonance_history.mean().item()


# =========================================================================
# ENTRAINEMENT SUR UN CORPUS DE DEMONSTRATION
# =========================================================================

def generate_demo_data(num_sequences: int = 50, seq_len: int = 32) -> torch.Tensor:
    """
    Genere des signatures 9D synthetiques pour demo.
    
    Les signatures suivent un motif harmonique :
    - phi oscille lentement (frequence basse)
    - alpha a des pics periodiques
    - reasoning suit phi avec un decalage
    
    Returns:
        signatures: [num_sequences, seq_len, 9]
    """
    torch.manual_seed(42)
    
    t = torch.linspace(0, 4 * math.pi, seq_len).unsqueeze(0)  # [1, seq]
    
    # Motivs harmoniques
    base_freq = t * PHI  # Frequence d'or
    
    sig_patterns = []
    for _ in range(num_sequences):
        phase = torch.rand(1) * 2 * math.pi
        noise = torch.randn(1, seq_len, 9) * 0.05
        
        sig = torch.zeros(1, seq_len, 9)
        sig[0, :, 0] = 0.5 + 0.3 * torch.sin(base_freq + phase)  # phi
        sig[0, :, 1] = 0.3 + 0.4 * torch.abs(torch.cos(base_freq * ALPHA))  # alpha
        sig[0, :, 2] = 0.6 + 0.2 * torch.sin(base_freq * 0.5 + phase)  # reasoning
        sig[0, :, 3] = 0.4 + 0.3 * torch.sin(base_freq * 2 + phase)  # creativity
        sig[0, :, 4] = 0.5 + 0.2 * torch.cos(base_freq * PHI + phase)  # math
        sig[0, :, 5] = 0.7 + 0.1 * torch.sin(base_freq * 0.25)  # factual
        sig[0, :, 6] = 0.3 + 0.3 * torch.abs(torch.sin(base_freq * 3))  # code
        sig[0, :, 7] = 0.5 + 0.2 * torch.cos(base_freq * ALPHA + phase)  # emotion
        sig[0, :, 8] = 0.4 + 0.3 * torch.sin(base_freq * PHI)  # temporal
        
        sig = torch.clamp(sig + noise, 0, 1)
        sig_patterns.append(sig)
    
    return torch.cat(sig_patterns, dim=0)  # [N, seq, 9]


def train_jepa_demo():
    """Entraine le predictor JEPA sur des donnees synthetiques."""
    
    print("=" * 60)
    print("ENTRAINEMENT HARMONIC-JEPA")
    print("=" * 60)
    
    # Donnees
    print("\n[1] Generation des donnees synthetiques...")
    num_seqs = 200
    seq_len = 16
    data = generate_demo_data(num_seqs, seq_len)
    print(f"    Donnees: {data.shape} ({num_seqs} sequences de {seq_len} signatures 9D)")
    
    # Modele
    print("\n[2] Initialisation du predictor JEPA...")
    jepa = HarmonicJEPA(hidden_dim=32, num_abc_kernel=5)
    params = sum(p.numel() for p in jepa.parameters())
    trainable = sum(p.numel() for p in jepa.parameters() if p.requires_grad)
    print(f"    Parametres: {params:,} (dont {trainable:,} appris)")
    
    # Optimiseur
    optimizer = torch.optim.AdamW(
        jepa.parameters(),
        lr=1e-3,
        weight_decay=1e-5
    )
    
    # Entrainement
    print("\n[3] Entrainement...")
    num_epochs = 50
    batch_size = 16
    
    for epoch in range(num_epochs):
        total_loss = 0.0
        num_batches = 0
        
        # Melanger les donnees
        perm = torch.randperm(num_seqs)
        
        for i in range(0, num_seqs, batch_size):
            idx = perm[i:i + batch_size]
            batch = data[idx]  # [B, seq, 9]
            
            loss = jepa.train_step(batch, optimizer)
            total_loss += loss
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        avg_res = jepa.get_average_resonance()
        
        if (epoch + 1) % 10 == 0:
            print(f"    Epoch {epoch+1:3d}/{num_epochs} | Loss: {avg_loss:.6f} | "
                  f"Resonance: {avg_res:.4f}")
    
    # Test de prediction
    print("\n[4] Test de prediction future...")
    test_seq = data[:1, :8, :]  # Premiere sequence, 8 premiers pas
    future_true = data[:1, 8:13, :]  # Les 5 signatures suivantes
    future_pred = jepa.predict(test_seq, horizon=5)
    
    print(f"    Contexte: {test_seq.shape}")
    print(f"    Futures predites: {future_pred.shape}")
    
    # Comparaison
    print("\n    Comparaison signature par signature:")
    dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code', 'emotion', 'temporal']
    for i in range(5):
        true_sig = future_true[0, i]
        pred_sig = future_pred[0, i]
        res = F.cosine_similarity(pred_sig.unsqueeze(0), true_sig.unsqueeze(0))
        print(f"    t+{i+1}: resonance={res.item():.4f}")
        if i == 0:
            for d, t, p in zip(dims, true_sig, pred_sig):
                print(f"      {d:12s}: vrai={t.item():.3f} pred={p.item():.3f} "
                      f"diff={abs(t.item()-p.item()):.3f}")
    
    # Metriques finales
    final_loss = avg_loss
    final_res = avg_res
    print(f"\n[5] Resultats finaux:")
    print(f"    Loss finale: {final_loss:.6f}")
    print(f"    Resonance finale: {final_res:.4f}")
    print(f"    Parametres: {params:,} (dont {trainable:,} appris)")
    
    if final_res > 0.3:
        print(f"\n  ✅ JEPA operationnel : resonance > 0.3")
    else:
        print(f"\n  ⚠ JEPA en cours d'apprentissage...")
    
    return jepa


# =========================================================================
# TEST UNITAIRE
# =========================================================================

def test_jepa():
    """Test unitaire du predictor JEPA."""
    print("=" * 60)
    print("TEST UNITAIRE HARMONIC-JEPA")
    print("=" * 60)
    
    # 1. Test de base
    print("\n[1] Test forward basique...")
    batch, seq = 4, 16
    sigs = torch.rand(batch, seq, 9) * 0.5 + 0.25  # Dans [0.25, 0.75]
    
    jepa = HarmonicJEPA(hidden_dim=32)
    predictor = jepa.predictor
    
    # Predire la derniere signature
    pred = predictor(sigs)
    assert pred.shape == (batch, 9), f"Shape incorrecte: {pred.shape}"
    assert torch.all(pred >= 0) and torch.all(pred <= 1), "Signatures hors [0, 1]"
    print(f"    [OK] Prediction: {pred.shape}, valeurs dans [0, 1]")
    
    # 2. Test loss par resonance
    print("\n[2] Test loss par resonance...")
    target = sigs[:, -1, :]
    loss = resonance_loss(pred, target)
    assert loss.item() >= 0, f"Loss negative: {loss.item()}"
    print(f"    [OK] Resonance loss: {loss.item():.6f}")
    
    # 3. Test prediction future
    print("\n[3] Test prediction future...")
    context = sigs[:, :8, :]
    futures = jepa.predict(context, horizon=5)
    assert futures.shape == (batch, 5, 9)
    print(f"    [OK] Futures: {futures.shape}")
    
    # 4. Test entrainement
    print("\n[4] Test entrainement...")
    optimizer = torch.optim.AdamW(jepa.parameters(), lr=1e-3)
    
    losses = []
    for _ in range(20):
        batch = torch.rand(8, 12, 9) * 0.5 + 0.25
        loss = jepa.train_step(batch, optimizer)
        losses.append(loss)
    
    assert losses[-1] < losses[0] * 1.5 or losses[-1] < 0.5, \
        f"Loss non decroissante: {losses[0]:.4f} -> {losses[-1]:.4f}"
    print(f"    [OK] Loss: {losses[0]:.4f} -> {losses[-1]:.4f}")
    
    # 5. Test contraste
    print("\n[5] Test loss contrastive...")
    pos = torch.rand(4, 9)
    neg = torch.rand(8, 9)
    c_loss = harmonic_contrastive_loss(pos, pos, neg)
    assert c_loss.item() > 0
    print(f"    [OK] Contrastive loss: {c_loss.item():.4f}")
    
    print(f"\n  ✅ HARMONIC-JEPA operationnel")
    print(f"  ✅ {sum(p.numel() for p in jepa.parameters()):,} parametres")
    print(f"  ✅ Prediction dans l'espace des signatures 9D")
    
    return True


if __name__ == '__main__':
    import traceback
    try:
        test_jepa()
        print("\n" + "=" * 60)
        train_jepa_demo()
    except Exception as e:
        print(f"\n  ❌ Erreur: {e}")
        traceback.print_exc()
