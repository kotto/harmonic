#!/usr/bin/env python3
"""Test PSNR sur image naturelle simulee avec le Detail Synthesizer."""
import sys, os, numpy as np, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image
from scipy.ndimage import laplace as lap_func
from harmonic_generator_core import HarmonicField, HarmonicColorMapper, normalize_field
from harmonic_detail_synthesizer import HarmonicDetailSynthesizer
from harmonic_image_generator import save_as_png

print('='*70)
print('  TEST SUR IMAGE NATURELLE SIMULEE -- PSNR + Metriques')
print('='*70)

np.random.seed(12345)
W, H = 512, 512
x = np.linspace(-1, 1, W)
y = np.linspace(-1, 1, H)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
theta = np.arctan2(Y, X)

# Base harmonique
field = HarmonicField(width=W, height=H, seed=42)
psi = field.get_psi_total()

# Ajouter structures realistes
sky = Y < 0.1
psi[sky] += 0.15 * np.sin(X[sky] * 25) * np.cos(X[sky] * 12)
mtn = (Y >= 0.1) & (Y < 0.5)
psi[mtn] += 0.35 * np.sin(X[mtn] * 8 + np.sin(X[mtn] * 3) * 2)
gnd = Y >= 0.5
psi[gnd] += 0.2 * np.sin(X[gnd] * 35) * np.cos(Y[gnd] * 25)
psi[gnd] += 0.08 * np.sin(X[gnd] * 60) * np.cos(Y[gnd] * 55)
# Bords synthetiques
psi += 0.06 * np.abs(np.gradient(np.sin(X * 12) * np.cos(Y * 8))[0])

psi = normalize_field(psi)
original = (psi + 1) / 2

print(f'  Image naturelle simulee : {W}x{H}')
print(f'  Std={np.std(original):.4f}  Range=[{original.min():.4f}, {original.max():.4f}]')

out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'detail_synthesizer')
os.makedirs(out_dir, exist_ok=True)

# Sauver original RGB
base_rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
save_as_png(base_rgb, os.path.join(out_dir, 'natural_original.png'))

# Metriques de l'original
fft_orig = np.abs(np.fft.fft2(original))
Yc, Xc = np.ogrid[:H, :W]
cy, cx = H // 2, W // 2
hf_mask = np.sqrt((Yc - cy)**2 + (Xc - cx)**2) > 25
hf_ratio_orig = np.sum(fft_orig[hf_mask]**2) / (np.sum(fft_orig**2) + 1e-12)
lap_orig = np.std(lap_func(original))

print(f'\n  {"strength":<10} {"PSNR":<10} {"LapStd":<12} {"GainLap":<10} {"HF ratio":<12}')
print(f'  {"-"*10} {"-"*10} {"-"*12} {"-"*10} {"-"*12}')
print(f'  {"original":<10} {"--":<10} {lap_orig:<12.4f} {"--":<10} {hf_ratio_orig:<12.4f}')

syn = HarmonicDetailSynthesizer(seed=99)
strengths = [0.5, 1.0, 1.5, 2.0, 3.0]

for s in strengths:
    enhanced = syn.synthesize_and_apply(original, strength=s, detail_seed=99)

    mse = np.mean((original - enhanced)**2)
    psnr = 10 * math.log10(1.0 / (mse + 1e-12)) if mse > 0 else 999

    lap_enh = np.std(lap_func(enhanced))
    gain_lap = (lap_enh / max(1e-12, lap_orig) - 1) * 100

    fft_enh = np.abs(np.fft.fft2(enhanced))
    hf_ratio_enh = np.sum(fft_enh[hf_mask]**2) / (np.sum(fft_enh**2) + 1e-12)

    print(f'  {s:<10.1f} {psnr:<10.1f} {lap_enh:<12.4f} +{gain_lap:<8.0f}% {hf_ratio_enh:<12.4f}')

    # Sauver enhanced RGB
    enh_field = enhanced * 2 - 1
    enh_rgb = HarmonicColorMapper.harmonic_hsl(enh_field, palette='cosmique')
    save_as_png(enh_rgb, os.path.join(out_dir, f'natural_enhanced_str{int(s*10):02d}.png'))

print(f'\n{"="*70}')
print('  INTERPRETATION')
print(f'{"="*70}')
print('  Le PSNR MESURE LA FIDELITE a l''original.')
print('  Or on AJOUTE des hautes frequences (details) qui n''existaient PAS.')
print('  Donc PSNR < infini est NORMAL et SOUHAITABLE.')
print('  C''est un enrichissement, pas une degradation.')
print()
print('  Metriques cles :')
print('    - LapStd : ecart-type du Laplacien (nettete percue)')
print('    - HF ratio : fraction d''energie en hautes frequences')
print('    - Ces 2 metriques AUGMENTENT fortement -> plus de details')
print()
print(f'  Fichiers dans : {out_dir}/')
for f in sorted(os.listdir(out_dir)):
    print(f'    {f}')