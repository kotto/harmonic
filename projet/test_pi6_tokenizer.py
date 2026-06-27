#!/usr/bin/env python3
"""Test du tokeniseur pi/6."""
import math, numpy as np

# Simuler VOCABULAIRE_BASE
VOCAB = ['<PAD>','<UNK>','<BOS>','<EOS>'] + [f'tok_{i}' for i in range(319)]
vs = len(VOCAB)

print(f"Test pi/6 tokenizer avec {vs} tokens")

# Mode pi/6
ANGLE_STEP = math.pi / 6.0
AREA_UNIT = (2.0 * math.pi)**2 / vs

kx = np.zeros(vs)
ky = np.zeros(vs)
for i in range(vs):
    angle  = (i * ANGLE_STEP) % (2.0 * math.pi)
    radius = math.sqrt((i + 0.5) * AREA_UNIT / math.pi)
    kx[i] = radius * np.cos(angle)
    ky[i] = radius * np.sin(angle)

# Unicite
from collections import Counter
pairs = [(round(kx[i],10), round(ky[i],10)) for i in range(vs)]
dups = [k for k,v in Counter(pairs).items() if v > 1]
print(f"Vecteurs uniques: {len(set(pairs))}/{vs}")
print(f"Doublons: {len(dups)}")

# Angles
angles_deg = sorted(set(round(math.degrees(math.atan2(ky[i], kx[i])) % 360, 2) for i in range(vs)))
print(f"Angles distincts: {len(angles_deg)} (attendu: 12)")
print(f"Angles (deg): {angles_deg}")

# Verification 12 branches
expected_angles = set(round((a * 30) % 360, 2) for a in range(12))
found_angles = set(angles_deg)
print(f"12 angles pi/6 presents: {expected_angles.issubset(found_angles)}")

# Test avec vocab etendu (1141 tokens)
vs2 = 1141
AREA_UNIT2 = (2.0 * math.pi)**2 / vs2
kx2 = np.zeros(vs2)
ky2 = np.zeros(vs2)
for i in range(vs2):
    angle  = (i * ANGLE_STEP) % (2.0 * math.pi)
    radius = math.sqrt((i + 0.5) * AREA_UNIT2 / math.pi)
    kx2[i] = radius * np.cos(angle)
    ky2[i] = radius * np.sin(angle)

pairs2 = [(round(kx2[i],10), round(ky2[i],10)) for i in range(vs2)]
dups2 = [k for k,v in Counter(pairs2).items() if v > 1]
print(f"\n--- Test avec {vs2} tokens ---")
print(f"Vecteurs uniques: {len(set(pairs2))}/{vs2}")
print(f"Doublons: {len(dups2)}")

angles_deg2 = sorted(set(round(math.degrees(math.atan2(kx2[i], ky2[i])) % 360, 2) for i in range(vs2)))
print(f"Angles distincts: {len(angles_deg2)}")

print("\nOK Test pi/6 reussi!" if len(dups) == 0 and len(dups2) == 0 else "ECHEC!")
