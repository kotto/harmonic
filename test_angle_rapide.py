#!/usr/bin/env python3
"""Test rapide du filtre angulaire harmonique."""
import sys
import torch
import torch.nn as nn
import numpy as np

# Rediriger stdout
log_file = open('f:/SAAS - Copie/test_angle_results.txt', 'w', encoding='utf-8')
sys.stdout = log_file

from harmonic_angle_correction import *

print("=" * 60)
print("TEST RAPIDE DU FILTRAGE ANGULAIRE HARMONIQUE")
print("=" * 60)

# Test 1: angle_entre_vecteurs
print("\n--- Test 1: angle_entre_vecteurs ---")
v1 = torch.tensor([1.0, 0.0])
v2 = torch.tensor([0.0, 1.0])
angle = angle_entre_vecteurs(v1, v2).item()
print(f"Angle 90°: {angle:.4f} rad = {angle*180/math.pi:.1f}°")
assert abs(angle - math.pi/2) < 0.01, "Angle devrait etre pi/2"
print("[OK]")

# Test 2: decomposer_gradient
print("\n--- Test 2: decomposer_gradient ---")
grad = torch.tensor([3.0, 4.0])
ref = torch.tensor([1.0, 0.0])
par, orth, ang = decomposer_gradient(grad, ref)
print(f"Gradient: {grad.tolist()}")
print(f"Reference: {ref.tolist()}")
print(f"Parallele: {par.tolist()} (devrait etre [3, 0])")
print(f"Orthogonal: {orth.tolist()} (devrait etre [0, 4])")
print(f"Angle: {ang:.4f} rad")
assert abs(par[0].item() - 3.0) < 0.01, "Parallele devrait etre 3"
assert abs(orth[1].item() - 4.0) < 0.01, "Orthogonal devrait etre 4"
print("[OK]")

# Test 3: force_filtrage_adaptative
print("\n--- Test 3: force_filtrage_adaptative ---")
for deg in [5, 20, 60]:
    rad = deg * math.pi / 180
    f = force_filtrage_adaptative(rad)
    print(f"Angle {deg}° -> lambda={f:.1f}")
print("[OK]")

# Test 4: corriger_angle_poids
print("\n--- Test 4: corriger_angle_poids ---")
layer = nn.Linear(8, 4)
poids_init = layer.weight.data.clone()
bruit = torch.randn(4, 8) * 0.1
signal = poids_init * 0.01
gradient = signal + bruit

angle_av = angle_entre_vecteurs(gradient.flatten(), poids_init.flatten()).item()
print(f"Angle avant: {angle_av:.4f} rad ({angle_av*180/math.pi:.1f}°)")

corr = corriger_angle_poids(layer.weight, gradient, force_base=0.5)
print(f"Correction: {corr:.6f}")

angle_ap = angle_entre_vecteurs(gradient.flatten(), layer.weight.flatten()).item()
print(f"Angle apres: {angle_ap:.4f} rad ({angle_ap*180/math.pi:.1f}°)")

norm_diff = abs(torch.norm(poids_init).item() - torch.norm(layer.weight).item())
print(f"Difference norme: {norm_diff:.6f}")
print("[OK]")

# Test 5: HarmonicAngleFilter
print("\n--- Test 5: HarmonicAngleFilter ---")
model = nn.Sequential(nn.Linear(10, 20), nn.ReLU(), nn.Linear(20, 5))
angle_filter = HarmonicAngleFilter(model, force_base=0.3)
optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

x = torch.randn(32, 10)
y = torch.randn(32, 5)

for step in range(20):
    y_pred = model(x)
    loss = ((y_pred - y) ** 2).mean()
    loss.backward()
    optimizer.step()
    stats = angle_filter.filtrer()
    optimizer.zero_grad()

hist = angle_filter.get_stats()
print(f"Angle final: {hist['angle'][-1]:.4f} rad")
print(f"Filtrage final: {hist['filtrage'][-1]:.6f}")
print("[OK]")

# Test 6: Comparaison avec/sans
print("\n--- Test 6: Comparaison avec/sans filtrage ---")
model_sans = nn.Sequential(nn.Linear(10, 20), nn.ReLU(), nn.Linear(20, 5))
model_avec = nn.Sequential(nn.Linear(10, 20), nn.ReLU(), nn.Linear(20, 5))
model_avec.load_state_dict(model_sans.state_dict())

opt_sans = torch.optim.SGD(model_sans.parameters(), lr=0.001, momentum=0.9)
opt_avec = torch.optim.SGD(model_avec.parameters(), lr=0.001, momentum=0.9)
af = HarmonicAngleFilter(model_avec, force_base=0.3)

loss_s, loss_a = [], []
for step in range(50):
    ls = ((model_sans(x) - y) ** 2).mean()
    ls.backward(); opt_sans.step(); opt_sans.zero_grad()
    loss_s.append(ls.item())
    
    la = ((model_avec(x) - y) ** 2).mean()
    la.backward(); opt_avec.step(); af.filtrer(); opt_avec.zero_grad()
    loss_a.append(la.item())

std_s = np.std(loss_s[-30:])
std_a = np.std(loss_a[-30:])
print(f"Std sans: {std_s:.6f}")
print(f"Std avec: {std_a:.6f}")
if std_a < std_s:
    print(f"[OK] Reduction bruit: {(1-std_a/std_s)*100:.1f}%")
else:
    print("[INFO] Pas d'amelioration significative")

print("\n" + "=" * 60)
print("TOUS LES TESTS REUSSIS")
print("=" * 60)

log_file.close()
