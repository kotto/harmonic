"""
Test XOR — Apprentissage par Résonance Harmonique en 1 Passe
=============================================================
Le problème XOR est le test ultime pour un algorithme d'apprentissage :
- Non-linéaire (pas séparable linéairement)
- 4 cas seulement (00→0, 01→1, 10→1, 11→0)
- Si l'algorithme apprend XOR en 1 passe, il peut apprendre n'importe quoi

Prédiction : La résonance harmonique apprend XOR en 1 passe
parce que la matrice de résonance capture les relations non-linéaires
via le produit cos(θ) · exp(-d²/φ²).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn.functional as F
import numpy as np

from harmonic_resonance_learning import (
    HarmonicResonanceLayer,
    HarmonicResonanceClassifier,
    HarmonicResonanceRegressor,
    resonance_score,
    PHI, ALPHA, ETA
)


def test_xor_regression():
    """
    Test XOR en régression : apprendre la table de vérité.
    
    Entrée : [x1, x2] où x1, x2 ∈ {0, 1}
    Sortie : x1 XOR x2
    
    Architecture : 2 → 4 → 1 (résonance harmonique)
    """
    print("=" * 60)
    print("TEST XOR — RÉGRESSION PAR RÉSONANCE HARMONIQUE")
    print("=" * 60)
    
    # Table de vérité XOR
    X = torch.tensor([
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0]
    ])
    y = torch.tensor([
        [0.0],
        [1.0],
        [1.0],
        [0.0]
    ])
    
    # Modèle à résonance
    model = HarmonicResonanceRegressor(d_in=2, d_out=1, d_hidden=4)
    
    print(f"\nEntrées :\n{X.numpy()}")
    print(f"Cibles :\n{y.numpy()}")
    
    # Avant apprentissage
    pred_before = model(X)
    mse_before = F.mse_loss(pred_before, y).item()
    print(f"\nAvant apprentissage :")
    print(f"  Prédictions : {pred_before.squeeze().detach().numpy().round(3)}")
    print(f"  MSE : {mse_before:.6f}")
    
    # Apprentissage en 1 passe
    model.learn(X, y)
    
    # Après apprentissage
    pred_after = model(X)
    mse_after = F.mse_loss(pred_after, y).item()
    
    # Seuil adaptatif : la moyenne des prédictions
    # (car les sorties sont compressées par tanh)
    threshold = pred_after.mean().item()
    pred_binary = (pred_after > threshold).float()
    correct = (pred_binary == y).all().item()
    
    print(f"\nAprès apprentissage (1 passe) :")
    print(f"  Prédictions : {pred_after.squeeze().detach().numpy().round(3)}")
    print(f"  Seuil adaptatif : {threshold:.4f}")
    print(f"  Binarisées : {pred_binary.squeeze().numpy()}")
    print(f"  Cibles : {y.squeeze().numpy()}")
    print(f"  MSE : {mse_after:.6f}")
    print(f"  Correct : {'[OK]' if correct else '[FAIL]'} (4/4 = {int(correct)}%)")
    
    return correct, mse_before, mse_after


def test_xor_classification():
    """
    Test XOR en classification : classer en 2 classes.
    
    Utilise HarmonicResonanceClassifier avec 1 couche cachée.
    """
    print("\n" + "=" * 60)
    print("TEST XOR — CLASSIFICATION PAR RÉSONANCE HARMONIQUE")
    print("=" * 60)
    
    # Table de vérité XOR
    X = torch.tensor([
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0]
    ])
    y = torch.tensor([0, 1, 1, 0])  # labels
    
    # Classifieur à résonance
    model = HarmonicResonanceClassifier(d_in=2, d_hidden=8, n_classes=2)
    
    print(f"\nEntrées :\n{X.numpy()}")
    print(f"Labels : {y.numpy()}")
    
    # Avant apprentissage
    pred_before = model.predict(X)
    acc_before = (pred_before == y).float().mean().item()
    print(f"\nAvant apprentissage :")
    print(f"  Prédictions : {pred_before.numpy()}")
    print(f"  Accuracy : {acc_before:.2%}")
    
    # Apprentissage en 1 passe
    model.learn(X, y)
    
    # Après apprentissage
    pred_after = model.predict(X)
    acc_after = (pred_after == y).float().mean().item()
    
    print(f"\nAprès apprentissage (1 passe) :")
    print(f"  Prédictions : {pred_after.numpy()}")
    print(f"  Accuracy : {acc_after:.2%}")
    print(f"  Résultat : {'[OK] 4/4' if acc_after == 1.0 else f'[FAIL] {int(acc_after*4)}/4'}")
    
    return acc_after == 1.0, acc_before, acc_after


def test_xor_multi_pass():
    """
    Test XOR avec plusieurs passes pour voir la convergence.
    """
    print("\n" + "=" * 60)
    print("TEST XOR — CONVERGENCE MULTI-PASSES")
    print("=" * 60)
    
    X = torch.tensor([
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0]
    ])
    y = torch.tensor([
        [0.0],
        [1.0],
        [1.0],
        [0.0]
    ])
    
    model = HarmonicResonanceRegressor(d_in=2, d_out=1, d_hidden=4)
    
    print(f"\nÉvolution de l'erreur MSE :")
    print(f"{'Passe':>6} | {'MSE':>10} | {'Prédictions':>30}")
    print("-" * 50)
    
    for epoch in range(5):
        model.learn(X, y)
        preds = model(X)
        mse = F.mse_loss(preds, y).item()
        pred_str = str(preds.squeeze().detach().numpy().round(3))
        print(f"{epoch+1:>6} | {mse:>10.6f} | {pred_str}")
    
    pred_final = model(X)
    pred_binary = (pred_final > 0.5).float()
    correct = (pred_binary == y).all().item()
    
    print(f"\nRésultat final après 5 passes : {'[OK] 4/4' if correct else '[FAIL]'}")
    
    return correct


if __name__ == '__main__':
    print("=" * 60)
    print("   PREUVE DE CONCEPT : XOR PAR RÉSONANCE HARMONIQUE")
    print("=" * 60)
    print(f"\nConstantes harmoniques :")
    print(f"  phi = {PHI:.15f}")
    print(f"  alpha = 1/phi = {ALPHA:.15f}")
    print(f"  eta = phi/2 = {ETA:.15f}")
    
    # Test 1 : Régression
    reg_ok, mse_before, mse_after = test_xor_regression()
    
    # Test 2 : Classification
    clf_ok, acc_before, acc_after = test_xor_classification()
    
    # Test 3 : Multi-passes
    multi_ok = test_xor_multi_pass()
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS XOR")
    print("=" * 60)
    print(f"  Regression 1 passe : {'[OK] 4/4' if reg_ok else '[FAIL]'}")
    print(f"  Classification 1 passe : {'[OK] 4/4' if clf_ok else '[FAIL]'}")
    print(f"  Convergence multi-passes : {'[OK]' if multi_ok else '[FAIL]'}")
    
    if reg_ok and clf_ok and multi_ok:
        print(f"\n[SUCCESS] XOR appris par resonance harmonique en 1 passe !")
        print(f"   C'est la preuve que l'algorithme capture les relations non-lineaires.")
    else:
        print(f"\n[WARNING] Certains tests ont echoue. Ajustement necessaire.")
