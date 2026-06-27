"""
Harmonic Resonance Deep — Architecture Multi-Couche par Résonance
==================================================================
Principe : Chaque couche de résonance affine les features de la couche
précédente en apprenant une transformation résiduelle.

Architecture :
  Entree -> [ResonanceLayer x N] -> ClassificationLayer

Chaque ResonanceLayer :
  1. Projette les features d'entree dans un reservoir harmonique
  2. Applique 8 non-linearites
  3. Apprend une transformation residuelle par moindres carres
  4. Combine entree + residu (skip connection)

Avantage : Chaque couche peut corriger les erreurs de la precedente.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import time

from harmonic_resonance_learning import PHI, ALPHA, ETA


class ResonanceLayer(nn.Module):
    """
    Une couche de resonance qui apprend a affiner ses entrees.
    
    Pour chaque couche :
    - Reservoir : d_in -> d_hidden avec 8 non-linearites
    - Apprentissage : W_out = (H^T H + lambda*I)^{-1} H^T (target - input)
    - Sortie : input + H @ W_out (residual learning)
    """
    
    def __init__(self, d_in: int, d_hidden: int, lam: float = 0.38,
                 phi: float = PHI, layer_id: int = 0):
        super().__init__()
        self.d_in = d_in
        self.d_hidden = d_hidden
        self.lam = lam
        self.phi = phi
        self.layer_id = layer_id
        
        # Normalisation par couche
        self.register_buffer('mean', torch.zeros(d_in))
        self.register_buffer('std', torch.ones(d_in))
        self._fitted = False
        
        # Random projection harmonique (seed differente par couche)
        torch.manual_seed(42 + layer_id * 1000)
        W_proj = torch.randn(d_hidden, d_in) * 0.1
        
        # Structure harmonique
        i = torch.arange(d_hidden, dtype=torch.float32).unsqueeze(1)
        j = torch.arange(d_in, dtype=torch.float32).unsqueeze(0)
        d = torch.abs(i - j)
        harmonic_mask = phi ** (-d / 100.0) * torch.cos(2 * math.pi * d / (phi * 100))
        W_proj = W_proj * harmonic_mask
        W_proj = W_proj / (torch.norm(W_proj, dim=1, keepdim=True) + 1e-8)
        self.W_proj = nn.Parameter(W_proj, requires_grad=False)
        
        # Bias
        self.bias = nn.Parameter(torch.randn(d_hidden) * 0.1, requires_grad=False)
        
        # Couche de sortie residuelle : 8*d_hidden -> d_in
        d_features = 8 * d_hidden
        self.W_out = nn.Parameter(torch.zeros(d_features, d_in), requires_grad=False)
        
        # Accumulateurs
        self.register_buffer('_XtX_acc', torch.zeros(d_features, d_features))
        self.register_buffer('_XtY_acc', torch.zeros(d_features, d_in))
        self.register_buffer('_n_samples', torch.zeros(1, dtype=torch.long))
    
    def fit_normalizer(self, x: torch.Tensor):
        """Normalisation par couche."""
        self.mean = x.mean(dim=0)
        self.std = x.std(dim=0).clamp(min=1e-8)
        self._fitted = True
    
    def _reservoir(self, x: torch.Tensor) -> torch.Tensor:
        """Calcule les 8 features du reservoir."""
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
    
    def learn(self, inputs: torch.Tensor, targets: torch.Tensor):
        """
        Apprend la transformation residuelle.
        
        Args:
            inputs: [batch, d_in] features d'entree
            targets: [batch, d_in] features cibles (idealement la couche suivante)
        """
        batch_size = inputs.shape[0]
        
        # La cible est le residu : ce qu'il faut ajouter a input pour atteindre target
        residual_target = targets - inputs
        
        with torch.no_grad():
            h = self._reservoir(inputs)
            
            self._XtX_acc += h.T @ h
            self._XtY_acc += h.T @ residual_target
            self._n_samples += batch_size
            
            d = 8 * self.d_hidden
            XtX_reg = self._XtX_acc + self.lam * torch.eye(d, device=inputs.device)
            
            try:
                self.W_out.data = torch.linalg.solve(XtX_reg, self._XtY_acc)
            except:
                U, S, Vh = torch.linalg.svd(XtX_reg)
                S_inv = torch.where(S > 1e-10, 1.0 / S, torch.zeros_like(S))
                XtX_inv = Vh.T @ torch.diag(S_inv) @ U.T
                self.W_out.data = XtX_inv @ self._XtY_acc
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward : input + residu."""
        h = self._reservoir(x)
        residual = h @ self.W_out
        return x + residual


class HarmonicDeepResonance(nn.Module):
    """
    Architecture multi-couche par resonance harmonique.
    
    Principe :
    1. Premiere couche : apprend a separer les classes dans l'espace des features
    2. Couches suivantes : affinent les features residuellement
    3. Classification finale par moindres carres regularises
    
    La magie : chaque couche voit les erreurs residuelles de la precedente
    et les corrige.
    """
    
    def __init__(self, d_in: int, d_hidden: int, n_classes: int,
                 n_layers: int = 3, lam: float = 0.38, phi: float = PHI):
        super().__init__()
        self.d_in = d_in
        self.d_hidden = d_hidden
        self.n_classes = n_classes
        self.n_layers = n_layers
        self.lam = lam
        self.phi = phi
        
        # Couches de resonance
        self.layers = nn.ModuleList([
            ResonanceLayer(d_in, d_hidden, lam, phi, layer_id=i)
            for i in range(n_layers)
        ])
        
        # Couche de classification finale
        d_features = 8 * d_hidden
        self.W_class = nn.Parameter(torch.zeros(d_features, n_classes), requires_grad=False)
        
        # Accumulateurs pour la classification
        self.register_buffer('_XtX_cls', torch.zeros(d_features, d_features))
        self.register_buffer('_XtY_cls', torch.zeros(d_features, n_classes))
        
        # Pour stocker les activations
        self._activations = {}
    
    def fit_normalizer(self, x: torch.Tensor):
        """Normalise la premiere couche."""
        self.layers[0].fit_normalizer(x)
    
    def learn(self, inputs: torch.Tensor, labels: torch.Tensor):
        """
        Apprentissage multi-couche en 1 passe.
        
        Strategie :
        - Couche 0 : apprend a separer les classes (cible = one-hot)
        - Couche 1..N-1 : apprend a corriger les residus
        - Classification finale : utilise les features du reservoir de la derniere couche
        """
        batch_size = inputs.shape[0]
        
        # One-hot encoding
        targets = torch.zeros(batch_size, self.n_classes)
        targets[torch.arange(batch_size), labels] = 1.0
        
        # Propagation a travers toutes les couches
        x = inputs.clone()
        
        with torch.no_grad():
            for i, layer in enumerate(self.layers):
                # Normaliser si besoin
                if not layer._fitted:
                    layer.fit_normalizer(x)
                
                if i == 0:
                    # Premiere couche : cible = features qui aident la classification
                    # On utilise les labels comme cible (propage vers l'espace des classes)
                    h = layer._reservoir(x)
                    
                    # Apprendre la couche de classification
                    self._XtX_cls += h.T @ h
                    self._XtY_cls += h.T @ targets
                    
                    d = 8 * self.d_hidden
                    XtX_reg = self._XtX_cls + self.lam * torch.eye(d, device=inputs.device)
                    
                    try:
                        self.W_class.data = torch.linalg.solve(XtX_reg, self._XtY_cls)
                    except:
                        U, S, Vh = torch.linalg.svd(XtX_reg)
                        S_inv = torch.where(S > 1e-10, 1.0 / S, torch.zeros_like(S))
                        XtX_inv = Vh.T @ torch.diag(S_inv) @ U.T
                        self.W_class.data = XtX_inv @ self._XtY_cls
                    
                    # La cible pour la couche 0 est la projection des labels
                    # dans l'espace des features
                    target_features = h @ self.W_class  # [batch, n_classes]
                    
                    # Etendre a d_in dimensions
                    if self.d_in > self.n_classes:
                        target_extended = torch.zeros(batch_size, self.d_in)
                        target_extended[:, :self.n_classes] = target_features
                    else:
                        target_extended = target_features[:, :self.d_in]
                    
                    layer.learn(x, target_extended)
                    x = layer(x)
                    
                else:
                    # Couches suivantes : cible = features de la couche precedente
                    # apres classification (auto-consistance)
                    h = layer._reservoir(x)
                    
                    # La cible est de rendre x plus proche des centroides de classe
                    pred = h @ self.W_class
                    pred_classes = pred.argmax(dim=-1)
                    
                    # Centroides par classe dans l'espace des features
                    centroids = torch.zeros(self.n_classes, self.d_in, device=x.device)
                    counts = torch.zeros(self.n_classes, device=x.device)
                    for b in range(batch_size):
                        c = pred_classes[b]
                        centroids[c] += x[b]
                        counts[c] += 1
                    
                    for c in range(self.n_classes):
                        if counts[c] > 0:
                            centroids[c] /= counts[c]
                    
                    # Cible : se rapprocher du centroide de sa classe
                    target_features = torch.zeros(batch_size, self.d_in, device=x.device)
                    for b in range(batch_size):
                        target_features[b] = centroids[pred_classes[b]]
                    
                    layer.learn(x, target_features)
                    x = layer(x)
    
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        """Forward pass complete."""
        x = inputs.clone()
        
        for layer in self.layers:
            x = layer(x)
        
        # Utiliser la derniere couche pour la classification
        h = self.layers[-1]._reservoir(x)
        return h @ self.W_class
    
    def predict(self, inputs: torch.Tensor) -> torch.Tensor:
        logits = self.forward(inputs)
        return logits.argmax(dim=-1)


# =========================================================================
# TEST
# =========================================================================

def load_mnist_subset(n_train=1000, n_test=200):
    """Charge un sous-ensemble de MNIST."""
    print(f"Chargement de MNIST ({n_train} train, {n_test} test)...")
    
    try:
        from torchvision import datasets, transforms
    except ImportError:
        print("torchvision non installe.")
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


def test_deep_resonance(n_train, n_test, d_hidden, n_layers, lam, label=""):
    """Teste l'architecture multi-couche."""
    print(f"\n{'='*60}")
    print(f"DEEP RESONANCE: {label}")
    print(f"  {n_train} train, {n_test} test, d_hidden={d_hidden}, layers={n_layers}, lam={lam}")
    print(f"{'='*60}")
    
    X_train, y_train, X_test, y_test = load_mnist_subset(n_train, n_test)
    if X_train is None:
        return 0.0, 0.0
    
    model = HarmonicDeepResonance(
        d_in=784, d_hidden=d_hidden, n_classes=10,
        n_layers=n_layers, lam=lam
    )
    
    model.fit_normalizer(X_train)
    
    with torch.no_grad():
        pred_before = model.predict(X_test)
        acc_before = (pred_before == y_test).float().mean().item()
    
    print(f"  Avant: {acc_before:.2%}")
    
    t_start = time.time()
    model.learn(X_train, y_train)
    t_end = time.time()
    train_time = t_end - t_start
    
    with torch.no_grad():
        pred_after = model.predict(X_test)
        acc_after = (pred_after == y_test).float().mean().item()
        
        confusion = torch.zeros(10, 10, dtype=torch.long)
        for i in range(len(y_test)):
            confusion[y_test[i], pred_after[i]] += 1
    
    print(f"  Apres: {acc_after:.2%}")
    print(f"  Temps: {train_time:.3f}s")
    print(f"  Par classe:")
    for i in range(10):
        total = confusion[i].sum().item()
        correct = confusion[i, i].item()
        if total > 0:
            print(f"    {i}: {correct}/{total} = {correct/total:.1%}")
    
    return acc_after, train_time


def main():
    print("=" * 60)
    print("HARMONIC DEEP RESONANCE — Architecture Multi-Couche")
    print("=" * 60)
    
    results = []
    
    # Test 1: 1 couche (baseline)
    acc1, t1 = test_deep_resonance(1000, 200, 256, 1, 0.38, "1 couche (baseline)")
    results.append(("1 couche", acc1, t1))
    
    # Test 2: 2 couches
    acc2, t2 = test_deep_resonance(1000, 200, 256, 2, 0.38, "2 couches")
    results.append(("2 couches", acc2, t2))
    
    # Test 3: 3 couches
    acc3, t3 = test_deep_resonance(1000, 200, 256, 3, 0.38, "3 couches")
    results.append(("3 couches", acc3, t3))
    
    # Test 4: 2 couches + plus de donnees
    acc4, t4 = test_deep_resonance(5000, 200, 256, 2, 0.38, "2 couches, 5000 data")
    results.append(("2c+5k", acc4, t4))
    
    # Test 5: 3 couches + plus de donnees
    acc5, t5 = test_deep_resonance(5000, 200, 256, 3, 0.38, "3 couches, 5000 data")
    results.append(("3c+5k", acc5, t5))
    
    # Resume
    print(f"\n{'='*60}")
    print("RESUME DEEP RESONANCE")
    print(f"{'='*60}")
    print(f"{'Configuration':<20} | {'Accuracy':>10} | {'Temps':>10}")
    print("-" * 44)
    for name, acc, t in results:
        print(f"{name:<20} | {acc:>8.2%} | {t:>8.3f}s")
    
    best_name, best_acc, _ = max(results, key=lambda x: x[1])
    print(f"\nMeilleure configuration : {best_name} = {best_acc:.2%}")
    
    if best_acc > 0.90:
        print(f"\n🎉 OBJECTIF ATTEINT ! MNIST > 90% en 1 epoque !")
    elif best_acc > 0.85:
        print(f"\n👍 Proche de l'objectif (85-90%).")
    else:
        print(f"\n📊 En dessous de 85%.")


if __name__ == '__main__':
    main()
