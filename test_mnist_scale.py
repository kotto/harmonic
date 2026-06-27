"""
Test MNIST — Scalabilité avec plus de données
==============================================
Objectif : Vérifier si plus de données améliore l'accuracy.
- 1000, 2000, 5000, 10000 images d'entraînement
- Configuration optimale : d_hidden=256, λ=1/φ²
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import time

from harmonic_resonance_learning import (
    HarmonicResonanceClassifier,
    PHI, ALPHA, ETA
)


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


def test_scale(n_train, n_test=200, d_hidden=256):
    """Teste avec n_train images."""
    print(f"\n{'='*60}")
    print(f"TEST: {n_train} train, {n_test} test, d_hidden={d_hidden}")
    print(f"{'='*60}")
    
    X_train, y_train, X_test, y_test = load_mnist_subset(n_train, n_test)
    if X_train is None:
        return 0.0, 0.0
    
    model = HarmonicResonanceClassifier(
        d_in=784, d_hidden=d_hidden, n_classes=10, n_layers=1
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
    
    print(f"  Après: {acc_after:.2%}")
    print(f"  Temps: {train_time:.3f}s ({train_time/n_train*1000:.3f}ms/image)")
    
    # Accuracy par classe
    print(f"  Par classe:")
    for i in range(10):
        total = confusion[i].sum().item()
        correct = confusion[i, i].item()
        if total > 0:
            print(f"    {i}: {correct}/{total} = {correct/total:.1%}")
    
    return acc_after, train_time


def main():
    print("╔" + "═" * 58 + "╗")
    print("║  MNIST SCALABILITÉ — RÉSONANCE HARMONIQUE  ║")
    print("╚" + "═" * 58 + "╝")
    
    scales = [1000, 2000, 5000, 10000]
    results = []
    
    for n in scales:
        acc, t = test_scale(n_train=n, n_test=200, d_hidden=256)
        results.append((n, acc, t))
    
    # Résumé
    print(f"\n{'='*60}")
    print("RÉSUMÉ SCALABILITÉ")
    print(f"{'='*60}")
    print(f"{'Images':>8} | {'Accuracy':>10} | {'Temps':>10} | {'ms/image':>10}")
    print("-" * 44)
    for n, acc, t in results:
        ms_per_img = t / n * 1000
        print(f"{n:>8} | {acc:>8.2%} | {t:>8.3f}s | {ms_per_img:>8.3f}ms")
    
    best_n, best_acc, _ = max(results, key=lambda x: x[1])
    print(f"\nMeilleur résultat : {best_n} images → {best_acc:.2%}")
    
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
