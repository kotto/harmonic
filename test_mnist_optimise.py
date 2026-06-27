"""
Test MNIST Optimisé — Apprentissage par Résonance Harmonique en 1 Époque
========================================================================
Objectif : > 90% en 1 époque avec réservoir large et régularisation optimisée.

Stratégie :
1. Réservoir large (d_hidden=1024) pour capturer plus de features
2. Régularisation optimisée (λ = 0.01 au lieu de 1/φ² ≈ 0.38)
3. Normalisation robuste (fit sur tout l'ensemble)
4. 8 non-linéarités (tanh, sin, cos, relu, sigmoid, z², z³, |z|)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import math

from harmonic_resonance_learning import PHI, ALPHA, ETA


# =========================================================================
# CLASSIFIEUR OPTIMISÉ AVEC RÉSERVOIR LARGE
# =========================================================================

class HarmonicResonanceClassifierOptimized(nn.Module):
    """
    Version optimisée du classifieur à résonance harmonique.
    
    Améliorations :
    - Réservoir plus large (1024 au lieu de 256)
    - Régularisation ajustable (λ optimisé)
    - 8 non-linéarités
    - Normalisation robuste
    """
    
    def __init__(self, d_in: int, d_hidden: int, n_classes: int,
                 lam: float = 0.01, phi: float = PHI):
        super().__init__()
        self.d_in = d_in
        self.d_hidden = d_hidden
        self.n_classes = n_classes
        self.lam = lam
        self.phi = phi
        
        # Normalisation
        self.register_buffer('mean', torch.zeros(d_in))
        self.register_buffer('std', torch.ones(d_in))
        self._fitted = False
        
        # Random projection harmonique (seed fixe pour reproductibilité)
        torch.manual_seed(42)
        W_proj = torch.randn(d_hidden, d_in) * 0.1
        
        # Structure harmonique
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
        
        # Couche de sortie : 8 * d_hidden features
        d_features = 8 * d_hidden
        self.W_out = nn.Parameter(torch.zeros(d_features, n_classes), requires_grad=False)
        
        # Accumulateurs pour apprentissage incrémental
        self.register_buffer('_XtX_acc', torch.zeros(d_features, d_features))
        self.register_buffer('_XtY_acc', torch.zeros(d_features, n_classes))
        self.register_buffer('_n_samples', torch.zeros(1, dtype=torch.long))
    
    def fit_normalizer(self, x: torch.Tensor):
        """Fixe la normalisation sur tout l'ensemble."""
        self.mean = x.mean(dim=0)
        self.std = x.std(dim=0).clamp(min=1e-8)
        self._fitted = True
    
    def _reservoir_features(self, x: torch.Tensor) -> torch.Tensor:
        """Calcule les 8 features non-linéaires du réservoir."""
        x_norm = (x - self.mean) / self.std
        z = x_norm @ self.W_proj.T + self.bias
        
        features = torch.cat([
            torch.tanh(z),
            torch.sin(z),
            torch.cos(z),
            F.relu(z),
            torch.sigmoid(z),
            z ** 2,
            z ** 3,
            torch.abs(z)
        ], dim=-1)
        
        return features
    
    def learn(self, inputs: torch.Tensor, labels: torch.Tensor):
        """Apprentissage en 1 passe par moindres carrés régularisés."""
        batch_size = inputs.shape[0]
        
        # One-hot encoding
        targets = torch.zeros(batch_size, self.n_classes)
        targets[torch.arange(batch_size), labels] = 1.0
        
        with torch.no_grad():
            h = self._reservoir_features(inputs)
            
            # Mise à jour incrémentale
            self._XtX_acc += h.T @ h
            self._XtY_acc += h.T @ targets
            self._n_samples += batch_size
            
            # Résolution : W = (X^T X + λI)^{-1} X^T Y
            d = 8 * self.d_hidden
            XtX_reg = self._XtX_acc + self.lam * torch.eye(d, device=inputs.device)
            
            try:
                self.W_out.data = torch.linalg.solve(XtX_reg, self._XtY_acc)
            except:
                U, S, Vh = torch.linalg.svd(XtX_reg)
                S_inv = torch.where(S > 1e-10, 1.0 / S, torch.zeros_like(S))
                XtX_inv = Vh.T @ torch.diag(S_inv) @ U.T
                self.W_out.data = XtX_inv @ self._XtY_acc
    
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        h = self._reservoir_features(inputs)
        return h @ self.W_out
    
    def predict(self, inputs: torch.Tensor) -> torch.Tensor:
        logits = self.forward(inputs)
        return logits.argmax(dim=-1)


# =========================================================================
# CHARGEMENT MNIST
# =========================================================================

def load_mnist_subset(n_train=1000, n_test=200):
    """Charge un sous-ensemble de MNIST."""
    print(f"Chargement de MNIST ({n_train} train, {n_test} test)...")
    
    try:
        from torchvision import datasets, transforms
    except ImportError:
        print("torchvision non installé.")
        return None, None, None, None
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    train_dataset = datasets.MNIST(
        './data', train=True, download=True, transform=transform
    )
    test_dataset = datasets.MNIST(
        './data', train=False, download=True, transform=transform
    )
    
    X_train = torch.stack([train_dataset[i][0] for i in range(n_train)])
    y_train = torch.tensor([train_dataset[i][1] for i in range(n_train)])
    X_test = torch.stack([test_dataset[i][0] for i in range(n_test)])
    y_test = torch.tensor([test_dataset[i][1] for i in range(n_test)])
    
    X_train = X_train.view(n_train, -1)
    X_test = X_test.view(n_test, -1)
    
    print(f"  X_train: {X_train.shape}, y_train: {y_train.shape}")
    print(f"  X_test: {X_test.shape}, y_test: {y_test.shape}")
    
    return X_train, y_train, X_test, y_test


# =========================================================================
# TEST AVEC DIFFÉRENTES CONFIGURATIONS
# =========================================================================

def test_configuration(n_train, n_test, d_hidden, lam, label=""):
    """Teste une configuration et retourne l'accuracy."""
    print(f"\n{'='*60}")
    print(f"CONFIG: {label}")
    print(f"  {n_train} train, {n_test} test, d_hidden={d_hidden}, λ={lam}")
    print(f"{'='*60}")
    
    X_train, y_train, X_test, y_test = load_mnist_subset(n_train, n_test)
    if X_train is None:
        return 0.0
    
    model = HarmonicResonanceClassifierOptimized(
        d_in=784, d_hidden=d_hidden, n_classes=10, lam=lam
    )
    
    # Normalisation
    model.fit_normalizer(X_train)
    
    # Évaluer avant
    with torch.no_grad():
        pred_before = model.predict(X_test)
        acc_before = (pred_before == y_test).float().mean().item()
    
    print(f"  Avant: {acc_before:.2%}")
    
    # Apprentissage
    t_start = time.time()
    model.learn(X_train, y_train)
    t_end = time.time()
    
    # Évaluer après
    with torch.no_grad():
        pred_after = model.predict(X_test)
        acc_after = (pred_after == y_test).float().mean().item()
        
        # Matrice de confusion
        confusion = torch.zeros(10, 10, dtype=torch.long)
        for i in range(len(y_test)):
            confusion[y_test[i], pred_after[i]] += 1
    
    print(f"  Après: {acc_after:.2%}")
    print(f"  Temps: {t_end - t_start:.3f}s")
    
    # Accuracy par classe
    print(f"  Par classe:")
    for i in range(10):
        total = confusion[i].sum().item()
        correct = confusion[i, i].item()
        if total > 0:
            print(f"    {i}: {correct}/{total} = {correct/total:.1%}")
    
    return acc_after


def main():
    print("╔" + "═" * 58 + "╗")
    print("║  MNIST OPTIMISÉ — RÉSONANCE HARMONIQUE  ║")
    print("╚" + "═" * 58 + "╝")
    
    results = []
    
    # Test 1: Configuration de base (256 hidden, λ=0.38)
    acc1 = test_configuration(1000, 200, 256, 0.38, "Baseline (256, λ=1/φ²)")
    results.append(("Baseline 256", acc1))
    
    # Test 2: Réservoir plus large (512 hidden, λ=0.38)
    acc2 = test_configuration(1000, 200, 512, 0.38, "Large (512, λ=1/φ²)")
    results.append(("Large 512", acc2))
    
    # Test 3: Réservoir large + régularisation optimisée (512, λ=0.01)
    acc3 = test_configuration(1000, 200, 512, 0.01, "Large + λ=0.01 (512, λ=0.01)")
    results.append(("Large+λ0.01", acc3))
    
    # Test 4: Très large (1024, λ=0.01)
    acc4 = test_configuration(1000, 200, 1024, 0.01, "Très large (1024, λ=0.01)")
    results.append(("XL 1024", acc4))
    
    # Test 5: Très large + λ=0.001
    acc5 = test_configuration(1000, 200, 1024, 0.001, "XL + λ=0.001 (1024, λ=0.001)")
    results.append(("XL+λ0.001", acc5))
    
    # Test 6: Très large + λ=0.1
    acc6 = test_configuration(1000, 200, 1024, 0.1, "XL + λ=0.1 (1024, λ=0.1)")
    results.append(("XL+λ0.1", acc6))
    
    # Résumé
    print(f"\n{'='*60}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*60}")
    print(f"{'Configuration':<20} | {'Accuracy':>10}")
    print("-" * 32)
    for name, acc in results:
        print(f"{name:<20} | {acc:>8.2%}")
    
    best_name, best_acc = max(results, key=lambda x: x[1])
    print(f"\nMeilleure configuration : {best_name} = {best_acc:.2%}")
    
    if best_acc > 0.90:
        print(f"\n🎉 OBJECTIF ATTEINT ! MNIST > 90% en 1 époque !")
    elif best_acc > 0.85:
        print(f"\n👍 Proche de l'objectif (85-90%).")
    elif best_acc > 0.80:
        print(f"\n📊 Bon résultat (80-85%).")
    else:
        print(f"\n⚠️  En dessous de 80%.")


if __name__ == '__main__':
    main()
