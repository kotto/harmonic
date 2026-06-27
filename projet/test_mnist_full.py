"""
Test MNIST — Dataset complet (60000 images)
=============================================
Objectif : Atteindre >95% avec le dataset complet.
Configuration optimale : d_hidden=256, lambda=1/phi^2

Note : 
- Passe 1 : calcul de la normalisation sur TOUT le dataset
- Passe 2 : apprentissage incremental avec normalisation correcte
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import time
import gc

from harmonic_resonance_learning import (
    HarmonicResonanceClassifier,
    PHI, ALPHA, ETA
)


def test_full_mnist_two_pass(d_hidden=256, lam=None, batch_size=5000):
    """Test en 2 passes : normalisation puis apprentissage."""
    if lam is None:
        lam = 1.0 / PHI ** 2
    
    print(f"\n{'='*60}")
    print(f"MNIST COMPLET (2 passes): d_hidden={d_hidden}, lam={lam:.4f}")
    print(f"{'='*60}")
    
    try:
        from torchvision import datasets, transforms
    except ImportError:
        print("torchvision non installe.")
        return 0.0, 0.0
    
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
    
    # Test set (10000 images)
    print("  Chargement test set...")
    X_test = torch.stack([test_dataset[i][0] for i in range(10000)])
    y_test = torch.tensor([test_dataset[i][1] for i in range(10000)])
    X_test = X_test.view(10000, -1)
    gc.collect()
    
    model = HarmonicResonanceClassifier(
        d_in=784, d_hidden=d_hidden, n_classes=10, n_layers=1
    )
    
    # === PASSE 1 : Calcul de la normalisation sur TOUT le dataset ===
    print("  Passe 1 : calcul normalisation sur 60000 images...")
    mean_acc = torch.zeros(784)
    var_acc = torch.zeros(784)
    n_total = 60000
    
    for start in range(0, n_total, batch_size):
        end = min(start + batch_size, n_total)
        batch_X = torch.stack([train_dataset[i][0] for i in range(start, end)])
        batch_X = batch_X.view(end - start, -1)
        
        # Welford's algorithm pour moyenne et variance
        for i in range(batch_X.shape[0]):
            x = batch_X[i]
            n = start + i + 1
            delta = x - mean_acc
            mean_acc = mean_acc + delta / n
            delta2 = x - mean_acc
            var_acc = var_acc + delta * delta2
        
        del batch_X
        gc.collect()
    
    std_acc = torch.sqrt(var_acc / (n_total - 1)).clamp(min=1e-8)
    
    # Appliquer la normalisation
    model.mean = mean_acc
    model.std = std_acc
    model._fitted = True
    
    print(f"  Normalisation calculee sur {n_total} echantillons")
    
    # Evaluation avant
    with torch.no_grad():
        pred_before = model.predict(X_test)
        acc_before = (pred_before == y_test).float().mean().item()
    print(f"  Avant: {acc_before:.2%}")
    
    # === PASSE 2 : Apprentissage incremental ===
    print(f"  Passe 2 : apprentissage incremental (lots de {batch_size})...")
    t_start = time.time()
    
    for start in range(0, n_total, batch_size):
        end = min(start + batch_size, n_total)
        batch_X = torch.stack([train_dataset[i][0] for i in range(start, end)])
        batch_y = torch.tensor([train_dataset[i][1] for i in range(start, end)])
        batch_X = batch_X.view(end - start, -1)
        
        model.learn(batch_X, batch_y)
        
        pct = (end / n_total) * 100
        elapsed = time.time() - t_start
        print(f"    Lot {start//batch_size + 1}: {start}-{end} ({pct:.0f}%) - {elapsed:.1f}s")
        
        del batch_X, batch_y
        gc.collect()
    
    t_train = time.time() - t_start
    
    print(f"  Temps d'apprentissage: {t_train:.3f}s")
    print(f"  Debit: {60000/t_train:.0f} images/s")
    
    # Evaluation
    print("  Evaluation sur 10000 test...")
    with torch.no_grad():
        pred_after = model.predict(X_test)
        acc_after = (pred_after == y_test).float().mean().item()
        
        confusion = torch.zeros(10, 10, dtype=torch.long)
        for i in range(len(y_test)):
            confusion[y_test[i], pred_after[i]] += 1
    
    print(f"  Apres: {acc_after:.2%}")
    print(f"  Temps total: {t_train:.3f}s")
    print(f"  Par classe:")
    for i in range(10):
        total = confusion[i].sum().item()
        correct = confusion[i, i].item()
        if total > 0:
            print(f"    {i}: {correct}/{total} = {correct/total:.1%}")
    
    return acc_after, t_train


def main():
    print("=" * 60)
    print("MNIST COMPLET — RESONANCE HARMONIQUE")
    print("=" * 60)
    
    acc, t = test_full_mnist_two_pass(d_hidden=256, batch_size=5000)
    
    print(f"\n{'='*60}")
    print(f"RESULTAT FINAL: {acc:.2%} en {t:.3f}s")
    print(f"{'='*60}")
    
    if acc > 0.95:
        print(f"\n🎉🎉🎉 OBJECTIF ATTEINT ! MNIST > 95% en 1 epoque !")
    elif acc > 0.93:
        print(f"\n🎉 Tres proche du 95% !")
    elif acc > 0.90:
        print(f"\n👍 Bon resultat (>90%)")
    else:
        print(f"\n⚠️  En dessous de 90%.")


if __name__ == '__main__':
    main()
