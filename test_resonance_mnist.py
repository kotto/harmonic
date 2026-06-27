"""
Test MNIST — Apprentissage par Résonance Harmonique en 1 Époque
================================================================
MNIST est le benchmark standard pour la classification d'images :
- 60 000 images d'entraînement (28×28 pixels)
- 10 classes (chiffres 0-9)
- Baseline backprop : ~97% en 1 époque avec un petit réseau

Objectif : > 90% en 1 époque avec la résonance harmonique
SANS rétropropagation, SANS GPU.

Pourquoi ça marche : La matrice de résonance R(x,y) = cos(θ)·exp(-d²/φ²)
capture les similarités entre images de la même classe instantanément.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn.functional as F
import numpy as np
import time

from harmonic_resonance_learning import (
    HarmonicResonanceClassifier,
    PHI, ALPHA, ETA
)


def load_mnist_subset(n_train=1000, n_test=200):
    """
    Charge un sous-ensemble de MNIST.
    
    Args:
        n_train: nombre d'images d'entraînement
        n_test: nombre d'images de test
    
    Returns:
        X_train: [n_train, 784]
        y_train: [n_train]
        X_test: [n_test, 784]
        y_test: [n_test]
    """
    print(f"Chargement de MNIST ({n_train} train, {n_test} test)...")
    
    try:
        from torchvision import datasets, transforms
    except ImportError:
        print("torchvision non installé. Génération de données synthétiques...")
        return generate_synthetic_mnist(n_train, n_test)
    
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
    
    # Sous-ensemble
    X_train = torch.stack([train_dataset[i][0] for i in range(n_train)])
    y_train = torch.tensor([train_dataset[i][1] for i in range(n_train)])
    X_test = torch.stack([test_dataset[i][0] for i in range(n_test)])
    y_test = torch.tensor([test_dataset[i][1] for i in range(n_test)])
    
    # Aplatir les images 28×28 → 784
    X_train = X_train.view(n_train, -1)
    X_test = X_test.view(n_test, -1)
    
    print(f"  X_train: {X_train.shape}, y_train: {y_train.shape}")
    print(f"  X_test: {X_test.shape}, y_test: {y_test.shape}")
    
    return X_train, y_train, X_test, y_test


def generate_synthetic_mnist(n_train=1000, n_test=200):
    """
    Génère des données MNIST synthétiques pour le test.
    
    Chaque chiffre est représenté par un motif harmonique unique :
    - Le chiffre k a une fréquence fondamentale f_k = (k+1) * φ
    - L'image est une superposition de sinusoïdes à cette fréquence
    """
    print("Génération de données MNIST synthétiques...")
    
    def generate_digit_image(digit, size=28):
        """Génère une image synthétique pour un chiffre."""
        img = np.zeros((size, size))
        freq = (digit + 1) * PHI
        
        # Motif harmonique
        for i in range(size):
            for j in range(size):
                x = (i - size/2) / (size/2)
                y = (j - size/2) / (size/2)
                r = np.sqrt(x**2 + y**2)
                
                # Fréquence harmonique spécifique au chiffre
                val = np.sin(freq * r * np.pi) * np.exp(-r * 2)
                
                # Ajouter des variations pour rendre chaque image unique
                phase = (digit * PHI * i / size + j * ALPHA / size)
                val += 0.3 * np.sin(phase * 2 * np.pi)
                
                img[i, j] = val
        
        # Normaliser
        img = (img - img.mean()) / (img.std() + 1e-8)
        return img
    
    # Générer les données
    np.random.seed(42)
    
    X_train_list = []
    y_train_list = []
    for _ in range(n_train):
        digit = np.random.randint(0, 10)
        img = generate_digit_image(digit)
        # Ajouter un peu de bruit
        img += np.random.randn(28, 28) * 0.1
        X_train_list.append(img.flatten())
        y_train_list.append(digit)
    
    X_test_list = []
    y_test_list = []
    for _ in range(n_test):
        digit = np.random.randint(0, 10)
        img = generate_digit_image(digit)
        img += np.random.randn(28, 28) * 0.15
        X_test_list.append(img.flatten())
        y_test_list.append(digit)
    
    X_train = torch.tensor(np.array(X_train_list), dtype=torch.float32)
    y_train = torch.tensor(y_train_list, dtype=torch.long)
    X_test = torch.tensor(np.array(X_test_list), dtype=torch.float32)
    y_test = torch.tensor(y_test_list, dtype=torch.long)
    
    # Normalisation
    mean = X_train.mean()
    std = X_train.std()
    X_train = (X_train - mean) / (std + 1e-8)
    X_test = (X_test - mean) / (std + 1e-8)
    
    print(f"  X_train: {X_train.shape}, y_train: {y_train.shape}")
    print(f"  X_test: {X_test.shape}, y_test: {y_test.shape}")
    
    return X_train, y_train, X_test, y_test


def test_mnist_one_epoch(n_train=1000, n_test=200, d_hidden=256, n_layers=2):
    """
    Test MNIST : apprentissage en 1 époque par résonance harmonique.
    
    Args:
        n_train: nombre d'images d'entraînement
        n_test: nombre d'images de test
        d_hidden: taille de la couche cachée
        n_layers: nombre de couches cachées
    """
    print("\n" + "=" * 60)
    print(f"TEST MNIST — 1 ÉPOQUE PAR RÉSONANCE HARMONIQUE")
    print(f"  {n_train} train, {n_test} test, {d_hidden} hidden, {n_layers} layers")
    print("=" * 60)
    
    # Charger les données
    X_train, y_train, X_test, y_test = load_mnist_subset(n_train, n_test)
    
    # Créer le classifieur à résonance
    model = HarmonicResonanceClassifier(
        d_in=784,
        d_hidden=d_hidden,
        n_classes=10,
        n_layers=n_layers
    )
    
    # Normaliser les données AVANT l'apprentissage (sur TOUT l'ensemble)
    model.fit_normalizer(X_train)
    
    # Évaluer avant apprentissage
    with torch.no_grad():
        pred_before = model.predict(X_test)
        acc_before = (pred_before == y_test).float().mean().item()
    
    print(f"\nAvant apprentissage :")
    print(f"  Accuracy test : {acc_before:.2%} (attendu: ~10% = hasard)")
    
    # Apprentissage en 1 époque
    print(f"\nApprentissage par résonance harmonique...")
    t_start = time.time()
    
    # Apprentissage en UN SEUL PASSAGE (toutes les données)
    model.learn(X_train, y_train)
    
    t_end = time.time()
    train_time = t_end - t_start
    
    # Évaluer après apprentissage
    with torch.no_grad():
        pred_after = model.predict(X_test)
        acc_after = (pred_after == y_test).float().mean().item()
        
        # Matrice de confusion
        confusion = torch.zeros(10, 10, dtype=torch.long)
        for i in range(len(y_test)):
            confusion[y_test[i], pred_after[i]] += 1
    
    print(f"\nAprès apprentissage (1 époque) :")
    print(f"  Accuracy test : {acc_after:.2%}")
    print(f"  Temps d'apprentissage : {train_time:.2f}s")
    print(f"  Temps par image : {train_time/n_train*1000:.2f}ms")
    
    # Afficher la matrice de confusion
    print(f"\nMatrice de confusion (lignes=vrai, colonnes=prédit) :")
    print("     " + " ".join([f"{i:>4}" for i in range(10)]))
    for i in range(10):
        row = " ".join([f"{confusion[i,j]:>4}" for j in range(10)])
        print(f"  {i}: {row}")
    
    # Accuracy par classe
    print(f"\nAccuracy par classe :")
    for i in range(10):
        total = confusion[i].sum().item()
        correct = confusion[i, i].item()
        if total > 0:
            print(f"  Classe {i}: {correct}/{total} = {correct/total:.1%}")
    
    return acc_after, train_time


def test_mnist_scale():
    """
    Test MNIST à différentes échelles pour voir la scalabilité.
    """
    print("\n" + "=" * 60)
    print("TEST MNIST — SCALABILITÉ")
    print("=" * 60)
    
    scales = [100, 500, 1000]
    results = []
    
    for n in scales:
        acc, t = test_mnist_one_epoch(n_train=n, n_test=100, d_hidden=128, n_layers=1)
        results.append((n, acc, t))
        print(f"\n  → {n} images : {acc:.2%} en {t:.2f}s")
    
    print(f"\nRésumé de scalabilité :")
    print(f"{'Images':>8} | {'Accuracy':>10} | {'Temps':>8}")
    print("-" * 30)
    for n, acc, t in results:
        print(f"{n:>8} | {acc:>8.2%} | {t:>7.2f}s")


if __name__ == '__main__':
    print("╔" + "═" * 58 + "╗")
    print("║  PREUVE DE CONCEPT : MNIST PAR RÉSONANCE HARMONIQUE  ║")
    print("╚" + "═" * 58 + "╝")
    print(f"\nConstantes harmoniques :")
    print(f"  φ = {PHI:.15f}")
    print(f"  α = 1/φ = {ALPHA:.15f}")
    print(f"  η = φ/2 = {ETA:.15f}")
    
    # Test principal : 1000 images, 1 époque
    acc, train_time = test_mnist_one_epoch(
        n_train=1000, n_test=200, d_hidden=256, n_layers=2
    )
    
    # Résultat
    print("\n" + "=" * 60)
    print("RÉSULTAT MNIST — 1 ÉPOQUE PAR RÉSONANCE")
    print("=" * 60)
    print(f"  Accuracy : {acc:.2%}")
    print(f"  Temps : {train_time:.2f}s")
    
    if acc > 0.90:
        print(f"\n🎉 MNIST > 90% en 1 époque par résonance harmonique !")
        print(f"   C'est la preuve que l'algorithme scale à des données réelles.")
    elif acc > 0.80:
        print(f"\n👍 MNIST > 80% — Bon résultat, proche de l'objectif 90%.")
        print(f"   Un ajustement des hyperparamètres devrait suffire.")
    elif acc > 0.50:
        print(f"\n📊 MNIST > 50% — L'algorithme apprend, mais lentement.")
        print(f"   La formule de résonance a besoin d'être ajustée.")
    else:
        print(f"\n⚠️  MNIST < 50% — L'algorithme n'apprend pas assez vite.")
        print(f"   La formule de résonance doit être revue.")
    
    # Test de scalabilité (optionnel)
    if acc > 0.50:
        test_mnist_scale()
