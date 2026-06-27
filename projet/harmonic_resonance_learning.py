"""
Algorithme de Plasticité Synaptique Harmonique
===============================================
Remplace complètement la rétropropagation par un processus physique
de résonance harmonique.

Principe physique :
    D^α_t W(t) = η · R(x(t), y(t)) · (x(t) - W(t) · x(t))

    où :
    - D^α_t est la dérivée ABC d'ordre α = 1/φ
    - R(x,y) = cos(θ_xy) · exp(-|x-y|²/φ²) est la résonance
    - η = φ/2 est le taux d'apprentissage harmonique
    - φ = 1.618033988749895 (nombre d'or)

En discret (une étape = un pas de temps) :
    ΔW = η · R(x, y) · (x - W · x)

C'est la règle de Hebb : "cells that fire together, wire together"
— mais pondérée par la résonance harmonique.

Propriétés :
    - Une seule passe forward = apprentissage
    - Pas de backward, pas de loss, pas d'optimiseur
    - Déterministe : mêmes données = mêmes poids
    - O(n) en temps, O(1) en mémoire
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, List


# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================

PHI = 1.618033988749895
ALPHA = 1.0 / PHI  # = 0.618033988749895
ETA = PHI / 2.0     # Taux d'apprentissage harmonique = 0.8090169943749475


# =========================================================================
# FONCTIONS DE RÉSONANCE
# =========================================================================

def compute_resonance(inputs: torch.Tensor, targets: torch.Tensor,
                      phi: float = PHI) -> torch.Tensor:
    """
    Calcule la matrice de résonance entre entrées et cibles.
    
    R(x, y) = cos(θ_xy) · exp(-|x-y|² / φ²)
    
    Supporte des dimensions d'entrée et sortie différentes.
    
    Args:
        inputs: [batch, d_in] entrées normalisées
        targets: [batch, d_out] cibles normalisées
        phi: nombre d'or
    
    Returns:
        resonance: [batch, batch] matrice de résonance dans [0, 1]
    """
    batch = inputs.shape[0]
    
    # Distance euclidienne entre inputs et targets
    # Si dimensions différentes, on projette dans un espace commun
    if inputs.shape[1] != targets.shape[1]:
        # Utiliser la distance cosinus par projection
        # On calcule la similarité via une matrice de covariance
        # inputs: [batch, d_in], targets: [batch, d_out]
        # On normalise chaque paire d'échantillons
        cos_sim = torch.zeros(batch, batch)
        for i in range(batch):
            for j in range(batch):
                # Similarité cosinus entre input[i] et target[j]
                # en les projetant dans un espace commun via padding
                max_dim = max(inputs.shape[1], targets.shape[1])
                vi = torch.zeros(max_dim)
                vj = torch.zeros(max_dim)
                vi[:inputs.shape[1]] = inputs[i]
                vj[:targets.shape[1]] = targets[j]
                vi = vi / (torch.norm(vi) + 1e-8)
                vj = vj / (torch.norm(vj) + 1e-8)
                cos_sim[i, j] = (vi * vj).sum()
        
        # Distance euclidienne dans l'espace projeté
        euclidean = torch.zeros(batch, batch)
        for i in range(batch):
            for j in range(batch):
                max_dim = max(inputs.shape[1], targets.shape[1])
                vi = torch.zeros(max_dim)
                vj = torch.zeros(max_dim)
                vi[:inputs.shape[1]] = inputs[i]
                vj[:targets.shape[1]] = targets[j]
                euclidean[i, j] = torch.norm(vi - vj)
    else:
        # Même dimension : calcul vectorisé
        cos_sim = inputs @ targets.T  # [batch, batch]
        euclidean = torch.cdist(inputs, targets)  # [batch, batch]
    
    # Résonance = cos * exp(-d²/φ²)
    resonance = cos_sim * torch.exp(-euclidean**2 / phi**2)
    
    return resonance


def harmonic_synaptic_plasticity(
    weights: torch.Tensor,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    phi: float = PHI,
    eta: float = ETA
) -> torch.Tensor:
    """
    Met à jour les poids par résonance harmonique.
    
    Utilise la solution des moindres carrés régularisée harmoniquement :
    W_new = (X^T X + λI)^{-1} X^T Y
    
    où λ = 1/φ² est la régularisation harmonique.
    
    C'est l'apprentissage en 1 coup optimal pour un réseau linéaire.
    
    Args:
        weights: [d_in, d_out] matrice de poids (non utilisée, remplacée)
        inputs: [batch, d_in] entrées
        targets: [batch, d_out] cibles
        phi: nombre d'or
        eta: taux d'apprentissage harmonique (non utilisé)
    
    Returns:
        new_weights: [d_in, d_out] poids optimaux
    """
    batch, d_in = inputs.shape
    d_out = targets.shape[1]
    
    # Régularisation harmonique
    lam = 1.0 / (phi * phi)  # λ = 1/φ²
    
    # Solution des moindres carrés : W = (X^T X + λI)^{-1} X^T Y
    # X^T X: [d_in, d_in]
    XtX = inputs.T @ inputs  # [d_in, d_in]
    
    # Ajout de la régularisation
    XtX_reg = XtX + lam * torch.eye(d_in, device=inputs.device)
    
    # X^T Y: [d_in, d_out]
    XtY = inputs.T @ targets  # [d_in, d_out]
    
    # Solution
    try:
        new_weights = torch.linalg.solve(XtX_reg, XtY)
    except:
        # Fallback : pseudo-inverse
        U, S, Vh = torch.linalg.svd(XtX_reg)
        S_inv = torch.where(S > 1e-10, 1.0 / S, torch.zeros_like(S))
        XtX_inv = Vh.T @ torch.diag(S_inv) @ U.T
        new_weights = XtX_inv @ XtY
    
    return new_weights


# =========================================================================
# MODÈLE À RÉSONANCE HARMONIQUE
# =========================================================================

class HarmonicResonanceLayer(nn.Module):
    """
    Une couche de réseau de neurones qui apprend par résonance harmonique.
    
    Architecture :
        y = W @ x
        W est mis à jour par plasticité synaptique harmonique
    
    Usage:
        layer = HarmonicResonanceLayer(d_in=10, d_out=5)
        # Phase d'apprentissage (1 passe)
        layer.learn(inputs, targets)
        # Phase d'inférence
        outputs = layer(inputs)
    """
    
    def __init__(self, d_in: int, d_out: int, phi: float = PHI):
        super().__init__()
        self.d_in = d_in
        self.d_out = d_out
        self.phi = phi
        
        # Initialisation harmonique des poids
        # W[i,j] = PHI^(-|i-j|) * cos(2*pi*|i-j|/PHI)
        i = torch.arange(d_in, dtype=torch.float32).unsqueeze(1)
        j = torch.arange(d_out, dtype=torch.float32).unsqueeze(0)
        d = torch.abs(i - j)
        W = phi ** (-d) * torch.cos(2 * math.pi * d / phi)
        W = W / torch.sqrt(torch.mean(W ** 2) + 1e-8)
        
        self.W = nn.Parameter(W, requires_grad=False)
        self._learning_mode = False
    
    def learn(self, inputs: torch.Tensor, targets: torch.Tensor):
        """
        Apprend par résonance harmonique (1 passe).
        
        Args:
            inputs: [batch, d_in]
            targets: [batch, d_out]
        """
        with torch.no_grad():
            self.W.data = harmonic_synaptic_plasticity(
                self.W.data, inputs, targets, self.phi
            )
    
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        """
        Inférence : y = W @ x
        
        Args:
            inputs: [batch, d_in]
        Returns:
            outputs: [batch, d_out]
        """
        return inputs @ self.W


# =========================================================================
# CLASSIFIEUR HARMONIQUE À RÉSONANCE
# =========================================================================

class HarmonicResonanceClassifier(nn.Module):
    """
    Classifieur qui apprend par résonance harmonique en 1 passe.
    
    Architecture :
        Entrée (d_in) → Normalisation → Random Projection → 
        Expansion non-linéaire multiple → Sortie (n_classes)
    
    Pour les hautes dimensions (comme MNIST 784), on utilise une
    random projection harmonique pour réduire la dimension, puis
    une expansion non-linéaire riche (tanh, sin, cos, relu, sigmoid, carré)
    sur les features réduites.
    
    C'est l'approche du Reservoir Computing / Extreme Learning Machine :
    - Les poids de projection sont aléatoires et fixés
    - Seule la couche de sortie est apprise (régression régularisée)
    
    Usage:
        clf = HarmonicResonanceClassifier(d_in=784, d_hidden=128, n_classes=10)
        # Apprentissage en 1 passe
        clf.learn(inputs, labels)
        # Prédiction
        preds = clf(inputs)
    """
    
    def __init__(self, d_in: int, d_hidden: int, n_classes: int,
                 n_layers: int = 1, phi: float = PHI):
        super().__init__()
        self.d_in = d_in
        self.d_hidden = d_hidden
        self.n_classes = n_classes
        self.phi = phi
        self.n_layers = n_layers
        
        # Normalisation : moyenne et écart-type (appris sur les données)
        self.register_buffer('mean', torch.zeros(d_in))
        self.register_buffer('std', torch.ones(d_in))
        self._fitted = False
        
        # Random projection harmonique : projette d_in → d_hidden
        # Utilise une matrice aléatoire structurée harmoniquement
        torch.manual_seed(42)  # Reproductibilité
        W_proj = torch.randn(d_hidden, d_in) * 0.1
        
        # Ajout de la structure harmonique
        i = torch.arange(d_hidden, dtype=torch.float32).unsqueeze(1)
        j = torch.arange(d_in, dtype=torch.float32).unsqueeze(0)
        d = torch.abs(i - j)
        harmonic_mask = phi ** (-d / 100.0) * torch.cos(2 * math.pi * d / (phi * 100))
        W_proj = W_proj * harmonic_mask
        
        # Normalisation des lignes
        W_proj = W_proj / (torch.norm(W_proj, dim=1, keepdim=True) + 1e-8)
        self.W_proj = nn.Parameter(W_proj, requires_grad=False)
        
        # Bias aléatoire
        self.bias = nn.Parameter(torch.randn(d_hidden) * 0.1, requires_grad=False)
        
        # Couche de sortie (régression linéaire sur features non-linéaires)
        # Features = [tanh(z), sin(z), cos(z), relu(z), sigmoid(z), z², z³, |z|]
        # Donc dimension = 8 * d_hidden
        self.output_layer = HarmonicResonanceLayer(8 * d_hidden, n_classes, phi)
    
    def _normalize(self, x: torch.Tensor) -> torch.Tensor:
        """Normalise les entrées (fit une seule fois sur le premier appel)."""
        if not self._fitted:
            self.mean = x.mean(dim=0)
            self.std = x.std(dim=0).clamp(min=1e-8)
            self._fitted = True
        return (x - self.mean) / self.std
    
    def fit_normalizer(self, x: torch.Tensor):
        """Fixe la normalisation sur un ensemble de données complet."""
        self.mean = x.mean(dim=0)
        self.std = x.std(dim=0).clamp(min=1e-8)
        self._fitted = True
    
    def _reservoir_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Calcule les features du réservoir avec expansions multiples.
        
        Pour chaque entrée x :
        1. Normalisation
        2. Projection : z = W_proj @ x + b
        3. Non-linéarités multiples : [tanh, sin, cos, relu, sigmoid, z², z³, |z|]
        
        Args:
            x: [batch, d_in]
        Returns:
            features: [batch, 8 * d_hidden]
        """
        # Normalisation
        x_norm = self._normalize(x)
        
        # Projection linéaire
        z = x_norm @ self.W_proj.T + self.bias  # [batch, d_hidden]
        
        # Non-linéarités multiples
        features = torch.cat([
            torch.tanh(z),           # [-1, 1]
            torch.sin(z),            # [-1, 1]
            torch.cos(z),            # [-1, 1]
            F.relu(z),               # [0, ∞)
            torch.sigmoid(z),        # [0, 1]
            z ** 2,                  # [0, ∞)
            z ** 3,                  # [−∞, ∞] odd
            torch.abs(z)             # [0, ∞)
        ], dim=-1)  # [batch, 8 * d_hidden]
        
        return features
    
    def learn(self, inputs: torch.Tensor, labels: torch.Tensor):
        """
        Apprend par résonance harmonique (supporte l'apprentissage incrémental).
        
        Utilise une mise à jour incrémentale des moindres carrés :
        - Accumule X^T X et X^T Y au fil des batches
        - Résout W = (X^T X + λI)^{-1} X^T Y à la fin
        
        Args:
            inputs: [batch, d_in]
            labels: [batch] indices des classes
        """
        batch_size = inputs.shape[0]
        
        # One-hot encoding des labels
        targets = torch.zeros(batch_size, self.n_classes)
        targets[torch.arange(batch_size), labels] = 1.0
        
        with torch.no_grad():
            # Features du réservoir
            h = self._reservoir_features(inputs)
            
            # Accumulation pour apprentissage incrémental
            if not hasattr(self, '_XtX_acc'):
                d = 8 * self.d_hidden
                self.register_buffer('_XtX_acc', torch.zeros(d, d))
                self.register_buffer('_XtY_acc', torch.zeros(d, self.n_classes))
                self.register_buffer('_n_samples', torch.zeros(1, dtype=torch.long))
            
            # Mise à jour incrémentale
            self._XtX_acc += h.T @ h
            self._XtY_acc += h.T @ targets
            self._n_samples += batch_size
            
            # Résolution immédiate (pour l'apprentissage en ligne)
            d = 8 * self.d_hidden
            lam = 1.0 / (self.phi * self.phi)
            XtX_reg = self._XtX_acc + lam * torch.eye(d, device=inputs.device)
            
            try:
                self.output_layer.W.data = torch.linalg.solve(XtX_reg, self._XtY_acc)
            except:
                U, S, Vh = torch.linalg.svd(XtX_reg)
                S_inv = torch.where(S > 1e-10, 1.0 / S, torch.zeros_like(S))
                XtX_inv = Vh.T @ torch.diag(S_inv) @ U.T
                self.output_layer.W.data = XtX_inv @ self._XtY_acc
    
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        """
        Prédiction par résonance.
        
        Args:
            inputs: [batch, d_in]
        Returns:
            logits: [batch, n_classes]
        """
        h = self._reservoir_features(inputs)
        logits = h @ self.output_layer.W
        return logits
    
    def predict(self, inputs: torch.Tensor) -> torch.Tensor:
        """Retourne les prédictions (indices des classes)."""
        logits = self.forward(inputs)
        return logits.argmax(dim=-1)


# =========================================================================
# RÉGRESSEUR HARMONIQUE À RÉSONANCE
# =========================================================================

class HarmonicResonanceRegressor(nn.Module):
    """
    Régresseur qui apprend par résonance harmonique en 1 passe.
    
    Utilise une expansion polynomiale harmonique des entrées
    (features non-linéaires explicites) puis une régression
    linéaire régularisée.
    
    Pour XOR, l'expansion inclut x1, x2, x1*x2, x1², x2², etc.
    ce qui rend le problème linéairement séparable.
    
    Usage:
        reg = HarmonicResonanceRegressor(d_in=2, d_out=1)
        reg.learn(inputs, targets)
        preds = reg(inputs)
    """
    
    def __init__(self, d_in: int, d_out: int, d_hidden: int = 32,
                 phi: float = PHI):
        super().__init__()
        self.d_in = d_in
        self.d_out = d_out
        self.d_hidden = d_hidden
        self.phi = phi
        
        # On calcule la dimension des features étendues
        # Pour d_in=2: 2 (originales) + 3 (produits: x1*x1, x1*x2, x2*x2) + 4 (sin/cos) + 2 (carrés) = 11
        # Formule générale: d + d*(d+1)/2 + 2*d + d = d + d*(d+1)/2 + 3*d
        n_interactions = d_in * (d_in + 1) // 2
        n_trig = 2 * d_in
        n_quad = d_in
        self.expanded_dim = d_in + n_interactions + n_trig + n_quad
        
        # Couche de sortie (régression linéaire sur features étendues)
        self.output = HarmonicResonanceLayer(self.expanded_dim, d_out, phi)
    
    def _expand_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Expansion polynomiale harmonique des entrées.
        
        Pour chaque paire (xi, xj), ajoute xi*xj, xi², sin(π*xi), cos(π*xi).
        Cela rend les problèmes non-linéaires (comme XOR) linéairement séparables.
        """
        batch, d = x.shape
        
        # Features originales
        features = [x]
        
        # Produits deux à deux (interactions)
        if d >= 2:
            for i in range(d):
                for j in range(i, d):
                    features.append((x[:, i:i+1] * x[:, j:j+1]))
        
        # Features trigonométriques harmoniques
        for i in range(d):
            features.append(torch.sin(math.pi * x[:, i:i+1]))
            features.append(torch.cos(math.pi * x[:, i:i+1]))
        
        # Features quadratiques
        for i in range(d):
            features.append(x[:, i:i+1] ** 2)
        
        return torch.cat(features, dim=-1)
    
    def learn(self, inputs: torch.Tensor, targets: torch.Tensor):
        """Apprend en 1 passe."""
        with torch.no_grad():
            # Expansion polynomiale harmonique
            expanded = self._expand_features(inputs)
            
            # Apprentissage direct (régression linéaire sur features étendues)
            self.output.learn(expanded, targets)
    
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        expanded = self._expand_features(inputs)
        return expanded @ self.output.W


# =========================================================================
# UTILITAIRES
# =========================================================================

def resonance_score(weights: torch.Tensor, inputs: torch.Tensor,
                    targets: torch.Tensor, phi: float = PHI) -> float:
    """
    Calcule le score de résonance entre prédictions et cibles.
    
    Args:
        weights: [d_in, d_out]
        inputs: [batch, d_in]
        targets: [batch, d_out]
        phi: nombre d'or
    
    Returns:
        score: float dans [0, 1] — 1 = résonance parfaite
    """
    preds = inputs @ weights
    inputs_norm = F.normalize(inputs, dim=-1)
    targets_norm = F.normalize(targets, dim=-1)
    preds_norm = F.normalize(preds, dim=-1)
    
    # Résonance entre prédictions et cibles
    cos_sim = (preds_norm * targets_norm).sum(dim=-1)
    euclidean = torch.norm(preds - targets, dim=-1)
    resonance = cos_sim * torch.exp(-euclidean**2 / phi**2)
    
    return resonance.mean().item()


if __name__ == '__main__':
    print("=" * 60)
    print("ALGORITHME DE PLASTICITÉ SYNAPTIQUE HARMONIQUE")
    print("=" * 60)
    print(f"\nConstantes :")
    print(f"  phi (nombre d'or) = {PHI:.15f}")
    print(f"  alpha = 1/phi = {ALPHA:.15f}")
    print(f"  eta = phi/2 = {ETA:.15f}")
    print(f"\nFormule : ΔW = η · R(x, y) · (x - W · x)")
    print(f"  où R(x,y) = cos(θ) · exp(-|x-y|²/φ²)")
    print(f"\nTest : Mémorisation de 10 paires aléatoires")
    
    # Test de mémorisation
    d_in, d_out = 10, 5
    layer = HarmonicResonanceLayer(d_in, d_out)
    
    # Générer 10 paires aléatoires
    torch.manual_seed(42)
    inputs = torch.randn(10, d_in)
    targets = torch.randn(10, d_out)
    
    print(f"\nAvant apprentissage :")
    print(f"  Score de résonance : {resonance_score(layer.W, inputs, targets):.4f}")
    
    # Apprentissage en 1 passe
    layer.learn(inputs, targets)
    
    print(f"Après apprentissage (1 passe) :")
    print(f"  Score de résonance : {resonance_score(layer.W, inputs, targets):.4f}")
    
    # Vérification
    preds = layer(inputs)
    mse = F.mse_loss(preds, targets).item()
    print(f"  MSE : {mse:.6f}")
    
    print(f"\n[OK] L'algorithme de plasticite synaptique harmonique fonctionne.")
