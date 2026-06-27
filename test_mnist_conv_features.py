"""
Test MNIST — Features convolutives aleatoires + Reservoir Harmonique
=====================================================================
Objectif : Atteindre >95% en utilisant des patches 5x5
avec filtres aleatoires pour capturer les motifs locaux.

Version : 8 filtres, lots de 1000, reservoir d=256 (max memoire CPU)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import time
import gc

from harmonic_resonance_learning import PHI


class ConvFeatureExtractor(nn.Module):
    """Extracteur de features convolutives aleatoires."""
    
    def __init__(self, n_filters=8, seed=42):
        super().__init__()
        torch.manual_seed(seed)
        
        self.conv = nn.Conv2d(1, n_filters, kernel_size=5, padding=2)
        nn.init.normal_(self.conv.weight, mean=0.0, std=0.1)
        nn.init.normal_(self.conv.bias, mean=0.0, std=0.01)
        
        with torch.no_grad():
            for i in range(self.conv.weight.shape[0]):
                for c in range(self.conv.weight.shape[1]):
                    kernel = self.conv.weight[i, c]
                    for y in range(5):
                        for x in range(5):
                            d = math.sqrt((y-2)**2 + (x-2)**2)
                            kernel[y, x] *= PHI ** (-d) * math.cos(2 * math.pi * d / PHI)
        
        for p in self.parameters():
            p.requires_grad = False
        
        self.feature_dim = n_filters * 7 * 7
    
    def forward(self, x):
        f = self.conv(x)
        f = torch.tanh(f)
        f = F.avg_pool2d(f, 4)
        return f.view(x.shape[0], -1)


class HarmonicConvReservoir(nn.Module):
    """Classifieur avec features conv + reservoir harmonique."""
    
    def __init__(self, n_filters=8, d_hidden=256, n_classes=10, phi=PHI):
        super().__init__()
        self.phi = phi
        self.d_hidden = d_hidden
        
        self.conv_extractor = ConvFeatureExtractor(n_filters)
        conv_dim = self.conv_extractor.feature_dim
        
        self.register_buffer('conv_mean', torch.zeros(conv_dim))
        self.register_buffer('conv_std', torch.ones(conv_dim))
        self._fitted = False
        
        torch.manual_seed(123)
        W_proj = torch.randn(d_hidden, conv_dim) * 0.1
        i = torch.arange(d_hidden, dtype=torch.float32).unsqueeze(1)
        j = torch.arange(conv_dim, dtype=torch.float32).unsqueeze(0)
        d = torch.abs(i - j)
        harmonic_mask = phi ** (-d / conv_dim) * torch.cos(2 * math.pi * d / (phi * conv_dim))
        W_proj = W_proj * harmonic_mask
        W_proj = W_proj / (torch.norm(W_proj, dim=1, keepdim=True) + 1e-8)
        
        self.W_proj = nn.Parameter(W_proj, requires_grad=False)
        self.bias = nn.Parameter(torch.randn(d_hidden) * 0.1, requires_grad=False)
        
        self.output_layer = nn.Linear(2 * d_hidden, n_classes, bias=False)
        
        self.register_buffer('_XtX_acc', torch.zeros(2 * d_hidden, 2 * d_hidden))
        self.register_buffer('_XtY_acc', torch.zeros(2 * d_hidden, n_classes))
    
    def fit_normalizer(self, x):
        with torch.no_grad():
            features = self.conv_extractor(x)
            self.conv_mean = features.mean(dim=0)
            self.conv_std = features.std(dim=0).clamp(min=1e-8)
            self._fitted = True
    
    def _reservoir_features(self, x):
        conv_feat = self.conv_extractor(x)
        if self._fitted:
            conv_feat = (conv_feat - self.conv_mean) / self.conv_std
        z = conv_feat @ self.W_proj.T + self.bias
        features = torch.cat([torch.tanh(z), torch.sin(z)], dim=-1)
        return features
    
    def learn_batch(self, inputs, labels):
        batch_size = inputs.shape[0]
        targets = torch.zeros(batch_size, self.output_layer.out_features)
        targets[torch.arange(batch_size), labels] = 1.0
        
        with torch.no_grad():
            h = self._reservoir_features(inputs)
            self._XtX_acc += h.T @ h
            self._XtY_acc += h.T @ targets
    
    def solve(self):
        d = 2 * self.d_hidden
        lam = 1.0 / (self.phi * self.phi)
        XtX_reg = self._XtX_acc + lam * torch.eye(d)
        
        try:
            W = torch.linalg.solve(XtX_reg, self._XtY_acc)
        except:
            U, S, Vh = torch.linalg.svd(XtX_reg)
            S_inv = torch.where(S > 1e-10, 1.0 / S, torch.zeros_like(S))
            XtX_inv = Vh.T @ torch.diag(S_inv) @ U.T
            W = XtX_inv @ self._XtY_acc
        
        self.output_layer.weight.data = W.T
    
    def forward(self, x):
        h = self._reservoir_features(x)
        return h @ self.output_layer.weight.T
    
    def predict(self, x):
        return self.forward(x).argmax(dim=-1)


def main():
    print("=" * 60)
    print("MNIST — CONV (5x5, 8 filtres) + RESERVOIR (d=256)")
    print("=" * 60)
    
    from torchvision import datasets, transforms
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST('./data', train=False, download=True, transform=transform)
    
    model = HarmonicConvReservoir(n_filters=8, d_hidden=256, n_classes=10)
    
    print("  Normalisation (1000)...")
    X_sample = torch.stack([train_dataset[i][0] for i in range(1000)])
    model.fit_normalizer(X_sample)
    del X_sample
    gc.collect()
    
    print("  Apprentissage (lots de 1000)...")
    t_start = time.time()
    batch_size = 1000
    
    for start in range(0, 60000, batch_size):
        end = min(start + batch_size, 60000)
        batch_X = torch.stack([train_dataset[i][0] for i in range(start, end)])
        batch_y = torch.tensor([train_dataset[i][1] for i in range(start, end)])
        model.learn_batch(batch_X, batch_y)
        pct = (end / 60000) * 100
        elapsed = time.time() - t_start
        print(f"    Lot {start//batch_size + 1}: {start}-{end} ({pct:.0f}%) - {elapsed:.1f}s")
        del batch_X, batch_y
        gc.collect()
    
    print("  Resolution...")
    model.solve()
    t_train = time.time() - t_start
    print(f"  Temps: {t_train:.3f}s")
    
    print("  Evaluation...")
    X_test = torch.stack([test_dataset[i][0] for i in range(10000)])
    y_test = torch.tensor([test_dataset[i][1] for i in range(10000)])
    
    with torch.no_grad():
        pred = model.predict(X_test)
        acc = (pred == y_test).float().mean().item()
        
        confusion = torch.zeros(10, 10, dtype=torch.long)
        for i in range(len(y_test)):
            confusion[y_test[i], pred[i]] += 1
    
    print(f"  Precision: {acc:.2%}")
    for i in range(10):
        total = confusion[i].sum().item()
        correct = confusion[i, i].item()
        if total > 0:
            print(f"    {i}: {correct}/{total} = {correct/total:.1%}")
    
    print(f"\n{'='*60}")
    print(f"RESULTAT: {acc:.2%} en {t_train:.3f}s")
    print(f"{'='*60}")
    
    if acc > 0.95:
        print(f"\n🎉🎉🎉 OBJECTIF 95% ATTEINT !")
    elif acc > 0.93:
        print(f"\n🎉 Tres proche du 95% !")
    elif acc > 0.90:
        print(f"\n👍 Bon resultat (>90%)")
    else:
        print(f"\n⚠️  En dessous de 90%.")


if __name__ == '__main__':
    main()
