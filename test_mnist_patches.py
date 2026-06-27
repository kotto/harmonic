"""
Test MNIST — Features Locales par Patches + Résonance Harmonique
================================================================
Problème : La random projection globale (784→256) perd l'information
de voisinage locale (pixels proches = même région de l'image).

Solution : Découper l'image 28×28 en patches 7×7 (16 patches),
appliquer la résonance sur chaque patch, puis concaténer.

Avantages :
- Chaque patch capture une région locale (4× plus petit = moins de paramètres)
- 16 patches × features = plus de diversité
- Invariance locale préservée
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
# CLASSIFIEUR À PATCHES LOCAUX
# =========================================================================

class HarmonicPatchClassifier(nn.Module):
    """
    Classifieur à résonance harmonique avec features locales par patches.
    
    Architecture :
    - Découpage de l'image 28×28 en patches 7×7 (16 patches de 49 pixels)
    - Chaque patch est projeté indépendamment dans un espace de features
    - Les features de tous les patches sont concaténées
    - Une couche de sortie linéaire régularisée fait la classification
    
    Pour chaque patch (49 pixels) :
    - Random projection → 32 features
    - 8 non-linéarités → 256 features par patch
    - 16 patches × 256 = 4096 features total
    """
    
    def __init__(self, patch_size: int = 7, n_patches_per_side: int = 4,
                 d_hidden_per_patch: int = 32, n_classes: int = 10,
                 lam: float = 0.38, phi: float = PHI):
        super().__init__()
        self.patch_size = patch_size
        self.n_patches_per_side = n_patches_per_side
        self.n_patches = n_patches_per_side ** 2
        self.d_hidden_per_patch = d_hidden_per_patch
        self.n_classes = n_classes
        self.lam = lam
        self.phi = phi
        
        d_in_patch = patch_size * patch_size  # 49
        d_features_per_patch = 8 * d_hidden_per_patch  # 256
        self.d_features_total = self.n_patches * d_features_per_patch  # 4096
        
        # Normalisation par patch
        self.register_buffer('mean', torch.zeros(self.n_patches, d_in_patch))
        self.register_buffer('std', torch.ones(self.n_patches, d_in_patch))
        self._fitted = False
        
        # Random projections pour chaque patch
        torch.manual_seed(42)
        W_proj_list = []
        bias_list = []
        for p in range(self.n_patches):
            Wp = torch.randn(d_hidden_per_patch, d_in_patch) * 0.1
            
            # Structure harmonique intra-patch
            i = torch.arange(d_hidden_per_patch, dtype=torch.float32).unsqueeze(1)
            j = torch.arange(d_in_patch, dtype=torch.float32).unsqueeze(0)
            d = torch.abs(i - j)
            harmonic_mask = phi ** (-d / 10.0) * torch.cos(2 * math.pi * d / (phi * 10))
            Wp = Wp * harmonic_mask
            Wp = Wp / (torch.norm(Wp, dim=1, keepdim=True) + 1e-8)
            W_proj_list.append(Wp)
            bias_list.append(torch.randn(d_hidden_per_patch) * 0.1)
        
        self.W_proj = nn.Parameter(torch.stack(W_proj_list), requires_grad=False)
        self.bias = nn.Parameter(torch.stack(bias_list), requires_grad=False)
        
        # Couche de sortie
        self.W_out = nn.Parameter(
            torch.zeros(self.d_features_total, n_classes), requires_grad=False
        )
        
        # Accumulateurs
        self.register_buffer('_XtX_acc', 
            torch.zeros(self.d_features_total, self.d_features_total))
        self.register_buffer('_XtY_acc', 
            torch.zeros(self.d_features_total, n_classes))
        self.register_buffer('_n_samples', torch.zeros(1, dtype=torch.long))
    
    def _extract_patches(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extrait les patches d'une image 28×28.
        
        Args:
            x: [batch, 784]
        Returns:
            patches: [batch, n_patches, patch_size²]
        """
        batch = x.shape[0]
        # Reshape en 28×28
        img = x.view(batch, 28, 28)
        
        # Découpage en patches
        ps = self.patch_size  # 7
        nps = self.n_patches_per_side  # 4
        stride = 28 // nps  # 7
        
        patches = []
        for i in range(nps):
            for j in range(nps):
                y_start = i * stride
                x_start = j * stride
                patch = img[:, y_start:y_start+ps, x_start:x_start+ps]
                patch = patch.reshape(batch, -1)  # [batch, 49]
                patches.append(patch)
        
        return torch.stack(patches, dim=1)  # [batch, 16, 49]
    
    def fit_normalizer(self, x: torch.Tensor):
        """Normalisation par patch."""
        patches = self._extract_patches(x)  # [batch, 16, 49]
        self.mean = patches.mean(dim=0)  # [16, 49]
        self.std = patches.std(dim=0).clamp(min=1e-8)  # [16, 49]
        self._fitted = True
    
    def _patch_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Calcule les features pour chaque patch.
        
        Args:
            x: [batch, 784]
        Returns:
            features: [batch, d_features_total]
        """
        batch = x.shape[0]
        patches = self._extract_patches(x)  # [batch, 16, 49]
        
        # Normalisation par patch
        patches_norm = (patches - self.mean.unsqueeze(0)) / self.std.unsqueeze(0)
        
        # Projection pour chaque patch
        all_features = []
        for p in range(self.n_patches):
            # [batch, 49] @ [49, 32] + [32] → [batch, 32]
            z = patches_norm[:, p, :] @ self.W_proj[p].T + self.bias[p]
            
            # 8 non-linéarités → [batch, 256]
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
            all_features.append(features)
        
        # Concaténer tous les patches → [batch, 4096]
        return torch.cat(all_features, dim=-1)
    
    def learn(self, inputs: torch.Tensor, labels: torch.Tensor):
        """Apprentissage en 1 passe."""
        batch_size = inputs.shape[0]
        targets = torch.zeros(batch_size, self.n_classes)
        targets[torch.arange(batch_size), labels] = 1.0
        
        with torch.no_grad():
            h = self._patch_features(inputs)
            
            self._XtX_acc += h.T @ h
            self._XtY_acc += h.T @ targets
            self._n_samples += batch_size
            
            XtX_reg = self._XtX_acc + self.lam * torch.eye(
                self.d_features_total, device=inputs.device
            )
            
            try:
                self.W_out.data = torch.linalg.solve(XtX_reg, self._XtY_acc)
            except:
                U, S, Vh = torch.linalg.svd(XtX_reg)
                S_inv = torch.where(S > 1e-10, 1.0 / S, torch.zeros_like(S))
                XtX_inv = Vh.T @ torch.diag(S_inv) @ U.T
                self.W_out.data = XtX_inv @ self._XtY_acc
    
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        h = self._patch_features(inputs)
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
# TEST
# =========================================================================

def test_patch_config(n_train, n_test, d_hidden_per_patch, lam, label=""):
    """Teste une configuration par patches."""
    print(f"\n{'='*60}")
    print(f"PATCH CONFIG: {label}")
    print(f"  {n_train} train, {n_test} test, d_hidden/patch={d_hidden_per_patch}, λ={lam}")
    print(f"{'='*60}")
    
    X_train, y_train, X_test, y_test = load_mnist_subset(n_train, n_test)
    if X_train is None:
        return 0.0
    
    model = HarmonicPatchClassifier(
        patch_size=7, n_patches_per_side=4,
        d_hidden_per_patch=d_hidden_per_patch,
        n_classes=10, lam=lam
    )
    
    model.fit_normalizer(X_train)
    
    with torch.no_grad():
        pred_before = model.predict(X_test)
        acc_before = (pred_before == y_test).float().mean().item()
    
    print(f"  Avant: {acc_before:.2%}")
    
    t_start = time.time()
    model.learn(X_train, y_train)
    t_end = time.time()
    
    with torch.no_grad():
        pred_after = model.predict(X_test)
        acc_after = (pred_after == y_test).float().mean().item()
        
        confusion = torch.zeros(10, 10, dtype=torch.long)
        for i in range(len(y_test)):
            confusion[y_test[i], pred_after[i]] += 1
    
    print(f"  Après: {acc_after:.2%}")
    print(f"  Temps: {t_end - t_start:.3f}s")
    print(f"  Par classe:")
    for i in range(10):
        total = confusion[i].sum().item()
        correct = confusion[i, i].item()
        if total > 0:
            print(f"    {i}: {correct}/{total} = {correct/total:.1%}")
    
    return acc_after


def main():
    print("╔" + "═" * 58 + "╗")
    print("║  MNIST PATCHES — RÉSONANCE HARMONIQUE  ║")
    print("╚" + "═" * 58 + "╝")
    
    results = []
    
    # Test 1: Baseline (patch 7×7, 32 hidden/patch, λ=0.38)
    acc1 = test_patch_config(1000, 200, 32, 0.38, "Patch 7×7, 32/patch, λ=1/φ²")
    results.append(("Patch 32", acc1))
    
    # Test 2: Plus de features par patch (64/patch)
    acc2 = test_patch_config(1000, 200, 64, 0.38, "Patch 7×7, 64/patch, λ=1/φ²")
    results.append(("Patch 64", acc2))
    
    # Test 3: λ plus faible (0.1)
    acc3 = test_patch_config(1000, 200, 32, 0.1, "Patch 7×7, 32/patch, λ=0.1")
    results.append(("Patch λ0.1", acc3))
    
    # Test 4: λ plus fort (1.0)
    acc4 = test_patch_config(1000, 200, 32, 1.0, "Patch 7×7, 32/patch, λ=1.0")
    results.append(("Patch λ1.0", acc4))
    
    # Test 5: Plus de données (2000 train)
    acc5 = test_patch_config(2000, 200, 32, 0.38, "2000 train, 32/patch, λ=1/φ²")
    results.append(("2000+Patch32", acc5))
    
    # Résumé
    print(f"\n{'='*60}")
    print("RÉSUMÉ DES TESTS PATCHES")
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
