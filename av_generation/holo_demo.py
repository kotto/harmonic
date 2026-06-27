"""Quick demo: extract image from SVD hologram and show all 5 stages."""
import numpy as np, os, sys, glob, time
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import HarmonicColorMapper
from holographic_one_shot import HolographicTrainer, HolographicGenerator
from harmonic_sharpener import HarmonicSharpener

out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'hologram_demo')
os.makedirs(out_dir, exist_ok=True)

# Find an existing generated image
files = []
for pattern in [
    'av_generation_output/unified/generations/unified_*.png',
    'unified_*.png',
    'av_generation_output/creativity/*.png',
    'av_generation_output/superior/generations/*.png',
]:
    files = glob.glob(os.path.join(os.path.dirname(__file__), '..', pattern))
    if files: break

if files:
    fpath = files[0]
    print(f"Image source: {fpath}")
    img = np.array(Image.open(fpath).convert('L'), dtype=np.float64) / 255.0
else:
    print("Generating test image...")
    from harmonic_generator_core import HarmonicField
    field = HarmonicField(width=400, height=400, seed=42)
    psi = field.get_psi_total()
    img = (psi + 1) / 2
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    fpath = os.path.join(out_dir, '_source.png')
    Image.fromarray(rgb, 'RGB').save(fpath)

h, w = img.shape
print(f"Dimensions: {w}x{h}")

# 1. Extract SVD hologram
t0 = time.time()
sig = HolographicTrainer.train_image(img, K=16)
print(f"\n1. HOLOGRAMME SVD extrait:")
print(f"   Matrice: {sig.hologram.shape} ({sig.hologram.nbytes} octets)")
print(f"   Coefficients: {sig.coefficients.shape} ({sig.coefficients.nbytes} octets)")
print(f"   Energie K=4: {sig.coherence_score():.1%}")
print(f"   Energie K=8: {sum(sig.energy_spectrum()[:8]):.1%}")

# 2. Reconstruct from hologram
recon = HolographicGenerator.reconstruct(sig, width=w, height=h)
mse = np.mean((img - recon)**2)
psnr = 10 * np.log10(1.0/(mse+1e-12))
print(f"\n2. RECONSTRUCTION depuis l'hologramme:")
print(f"   PSNR: {psnr:.1f} dB")
print(f"   MSE: {mse:.6f}")

# 3. Sharpener (residue + 7Hn)
sharpener = HarmonicSharpener(K=16)
sharp = sharpener.sharpen(img, strength=1.0)
metrics = sharpener.analyze_sharpness(sharp)
print(f"\n3. SHARPENED (residu + 7Hn):")
print(f"   Acutance: {metrics['acutance']:.4f}")

# Save all images
def save_grey(arr, name):
    u8 = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(np.stack([u8]*3, axis=-1), 'RGB').save(os.path.join(out_dir, name))

save_grey(img, '01_original.png')
save_grey(recon, '02_from_hologram.png')
save_grey(sharp, '03_sharpened_7Hn.png')

# Hologram matrix visualization
holo = sig.hologram
holo = (holo - holo.min()) / (holo.max() - holo.min() + 1e-12)
holo_img = Image.fromarray((holo*255).astype(np.uint8)).resize((256, 64), Image.NEAREST)
holo_img.save(os.path.join(out_dir, '04_hologram_16x64.png'))

# Residue amplified
residue = np.abs(img - recon) * 15
save_grey(np.clip(residue, 0, 1), '05_residue_x15.png')

print(f"\nTemps total: {(time.time()-t0)*1000:.0f}ms")
print(f"\nFichiers generes dans: {out_dir}/")
for f in sorted(os.listdir(out_dir)):
    sz = os.path.getsize(os.path.join(out_dir, f))
    print(f"  {f} ({sz:,} o)")

print(f"""
Interpretation:
  01_original.png       - L'image source originale
  02_from_hologram.png  - Reconstruite depuis l'hologramme SVD 16x64 (PSNR {psnr:.0f} dB)
  03_sharpened_7Hn.png  - Apres reinjection du residu amplifie par les 7Hn
  04_hologram_16x64.png - L'hologramme lui-meme (la matrice de 16 vecteurs propres)
  05_residue_x15.png    - Le residu spectral (hautes frequences) amplifie x15
""")