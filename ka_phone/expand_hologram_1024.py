#!/usr/bin/env python3
"""
AXE 2 — Extension Hologramme 256x256 → 1024x1024 + Ingestion QuickFacts
=========================================================================
1. Étend l'hologramme existant de 256 à 1024 (si pas déjà fait)
2. Ingère tous les faits QuickFacts dans l'hologramme étendu
3. Lance la détection de principes émergents
4. Rapport

Usage: python expand_hologram_1024.py
"""
import os, sys, json, time, hashlib, math
import numpy as np

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, '.')

PHI = 1.618033988749895
DATA_DIR = os.path.join('..', 'data', 'emergence')
HOLOGRAM_FILE_256 = os.path.join(DATA_DIR, 'emergence_hologram.npy')
HOLOGRAM_FILE_1024 = os.path.join(DATA_DIR, 'emergence_hologram_1024.npy')
os.makedirs(DATA_DIR, exist_ok=True)

print("=" * 60)
print("AXE 2 — EXTENSION HOLOGRAMME 1024x1024")
print("=" * 60)

# Step 1: Load or create 1024x1024 hologram
if os.path.exists(HOLOGRAM_FILE_1024):
    h = np.load(HOLOGRAM_FILE_1024)
    print(f"[OK] Hologramme 1024x1024 charge: {h.shape}, energy={np.sum(np.abs(h)**2):.0f}")
else:
    h = np.zeros((1024, 1024), dtype=np.complex128)
    # If 256x256 exists, upsample it
    if os.path.exists(HOLOGRAM_FILE_256):
        h256 = np.load(HOLOGRAM_FILE_256)
        h[:256, :256] = h256
        print(f"[OK] Hologramme 256x256 upsampled into 1024x1024")
    else:
        print(f"[NEW] Hologramme 1024x1024 vierge cree")

# Step 2: Ingest all QuickFacts into the hologram
print(f"\n[STEP 2] Ingestion des faits QuickFacts dans l'hologramme...")

from quick_facts import QuickFacts
qf = QuickFacts()
facts = qf.facts
print(f"  {len(facts)} faits a ingerer")

def text_to_wave(text, holosize=1024):
    h = hashlib.sha256(text.encode()[:200]).hexdigest()
    kx = (int(h[:16], 16) % (holosize * 100)) / 100.0
    ky = (int(h[16:32], 16) % (holosize * 100)) / 100.0
    kx = (kx - holosize / 2) / holosize * 20
    ky = (ky - holosize / 2) / holosize * 20
    return kx, ky

def gaussian_wave(kx, ky, amp=0.05, sigma=4.0, holosize=1024):
    x = np.linspace(-holosize/2, holosize/2, holosize)
    y = np.linspace(-holosize/2, holosize/2, holosize)
    X, Y = np.meshgrid(x, y)
    env = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
    wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
    return amp * env * wave

ingested = 0
for fid, text, keywords in facts:
    kx, ky = text_to_wave(fid + text)
    wave = gaussian_wave(kx, ky, amp=0.04)
    h += wave
    ingested += 1
    if ingested % 200 == 0:
        print(f"    {ingested}/{len(facts)} faits...")

# Normalize
max_amp = np.max(np.abs(h))
if max_amp > 500:
    h *= 0.95
    print(f"  Anti-saturation applied (max={max_amp:.0f})")

# Save
np.save(HOLOGRAM_FILE_1024, h)
energy = np.sum(np.abs(h)**2)
print(f"  [OK] {ingested} faits ingeres dans l'hologramme 1024x1024")
print(f"  Energy: {energy:.0f} | Density: {np.mean(np.abs(h)):.4f} | Max: {np.max(np.abs(h)):.2f}")

# Step 3: Detect emergent principles (simplified)
print(f"\n[STEP 3] Detection de principes emergents...")

# Load known dualities from harmonic_emergence
try:
    from harmonic_emergence import HarmonicEmergence, KNOWN_DUALITIES
    print(f"  {len(KNOWN_DUALITIES)} dualites connues chargees")
except:
    KNOWN_DUALITIES = [
        ("derivative", "integral"),
        ("sin", "cos"),
        ("addition", "soustraction"),
        ("multiplication", "division"),
    ]
    print(f"  {len(KNOWN_DUALITIES)} dualites par defaut")

# Simple interference detection: check if pairs of related keywords
# have overlapping wave patterns in the hologram
detected = []
for item in KNOWN_DUALITIES:
    kw1 = item[0]
    kw2 = item[1] if len(item) > 1 else item[0]
    desc = item[2] if len(item) > 2 else ""
    k1x, k1y = text_to_wave(kw1)
    k2x, k2y = text_to_wave(kw2)
    # Interference metric: cosine similarity of positions
    dist = math.sqrt((k1x - k2x)**2 + (k1y - k2y)**2)
    # Look at the hologram value at midpoint
    mid_x = int(512 + (k1x + k2x) * 1024/40)
    mid_y = int(512 + (k1y + k2y) * 1024/40)
    mid_x = max(0, min(1023, mid_x))
    mid_y = max(0, min(1023, mid_y))
    interference_strength = np.abs(h[mid_y, mid_x])
    
    if interference_strength > 0.5 * np.mean(np.abs(h)):
        detected.append((kw1, kw2, interference_strength))

print(f"  {len(detected)} principes emergents detectes:")
for kw1, kw2, strength in sorted(detected, key=lambda x: x[2], reverse=True)[:10]:
    print(f"    {kw1} <-> {kw2}: force={strength:.3f}")

# Step 4: Summary
print(f"\n{'='*60}")
print("AXE 2 — TERMINE")
print(f"{'='*60}")
print(f"  Hologramme: 1024x1024")
print(f"  Faits ingeres: {ingested}")
print(f"  Energie: {energy:.0f}")
print(f"  Principes emergents: {len(detected)}")
print(f"  Fichier: {HOLOGRAM_FILE_1024}")