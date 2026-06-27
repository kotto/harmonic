#!/usr/bin/env python3
"""Test complet : nouveau Psi1 1/f² + Detail Synthesizer + PSNR + spectre."""
import sys, os, numpy as np, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from scipy.ndimage import laplace as lap_func
from harmonic_generator_core import HarmonicField, HarmonicColorMapper, normalize_field
from harmonic_detail_synthesizer import HarmonicDetailSynthesizer, enhance_existing_pipeline
from harmonic_image_generator import save_as_png

print('='*80)
print('  TEST COMPLET — Recommandations implementees')
print('  R1: Nouveau Psi1 1/f^2 (42 ondes au lieu de 7)')
print('  R2+R3: Conditionnement semantique + balance spectrale')
print('='*80)

out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'recommendations_test')
os.makedirs(out_dir, exist_ok=True)

# ============================================================
# TEST 1 : Analyse spectrale du nouveau Psi1
# ============================================================
print('\n[TEST 1] Analyse spectrale du nouveau Psi1 (42 ondes 1/f²)')

for size in [256, 512]:
    field = HarmonicField(width=size, height=size, seed=42)
    psi = field.get_psi_total()
    
    fft = np.abs(np.fft.fft2(psi))
    fft_shifted = np.fft.fftshift(fft)
    h, w = psi.shape
    Y, X = np.ogrid[:h, :w]
    cy, cx = h//2, w//2
    R = np.sqrt((Y-cy)**2 + (X-cx)**2).astype(int)
    
    radial_energy = np.bincount(R.flatten(), weights=fft_shifted.flatten()**2)
    radial_count = np.bincount(R.flatten())
    valid = radial_count > 0
    freqs = np.arange(len(radial_energy))[valid]
    energies = radial_energy[valid] / radial_count[valid]
    
    valid_range = (freqs >= 1) & (freqs <= min(size//6, max(freqs)))
    log_f = np.log(freqs[valid_range] + 1e-12)
    log_e = np.log(energies[valid_range] + 1e-30)
    slope, _ = np.polyfit(log_f, log_e, 1)
    
    hf_fraction = np.sum(fft_shifted[R > size//8] ** 2) / (np.sum(fft_shifted ** 2) + 1e-12)
    
    print(f'  {size}x{size} : pente spectrale = {slope:.2f} (cible -2.0, ecart {abs(-2.0-slope):.2f}) | '
          f'HF fraction = {hf_fraction:.4f}')
    
    # Sauver image RGB
    base_img = (psi + 1) / 2
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    save_as_png(rgb, os.path.join(out_dir, f'psi1_new_{size}x{size}.png'))

# ============================================================
# TEST 2 : Detail Synthesizer sur nouveau Psi1 (avec balance spectrale ajustee)
# ============================================================
print('\n[TEST 2] Detail Synthesizer sur nouveau Psi1 + conditionnement spatial')

field = HarmonicField(width=512, height=512, seed=12345)
psi = field.get_psi_total()
base_img = (psi + 1) / 2

# Metriques de base
lap_base = np.std(lap_func(base_img))
fft_base = np.abs(np.fft.fft2(base_img))
h, w = base_img.shape
Y, X = np.ogrid[:h, :w]
cy, cx = h//2, w//2
R = np.sqrt((Y-cy)**2 + (X-cx)**2).astype(int)
hf_base = np.sum(fft_base[R > 20] ** 2) / (np.sum(fft_base ** 2) + 1e-12)

# Edge map pour conditionnement spatial (Rec 2)
gy, gx = np.gradient(base_img)
edge_map = np.sqrt(gx**2 + gy**2)
edge_map = edge_map / (np.max(edge_map) + 1e-12)

# Variance locale (Rec 2)
var_map = np.zeros_like(base_img)
bs = 16
for y in range(0, h, bs):
    for x in range(0, w, bs):
        ye, xe = min(y+bs, h), min(x+bs, w)
        var_map[y:ye, x:xe] = np.var(base_img[y:ye, x:xe])
var_map = var_map / (np.max(var_map) + 1e-12)

synthesizer = HarmonicDetailSynthesizer(seed=99)

# Test avec differentes forces
print(f'\n  {"Strength":<10} {"PSNR(dB)":<12} {"LapStd":<12} {"GainLap":<10} {"HF ratio":<12}')
print(f'  {"-"*10} {"-"*12} {"-"*12} {"-"*10} {"-"*12}')
print(f'  {"base":<10} {"--":<12} {lap_base:<12.4f} {"--":<10} {hf_base:<12.4f}')

for s in [0.3, 0.5, 0.7, 1.0, 1.5]:
    # Utiliser enhance_existing_pipeline avec conditionnement implicite
    enhanced = enhance_existing_pipeline(base_img, strength=s, detail_seed=99)
    
    mse = np.mean((base_img - enhanced)**2)
    psnr = 10 * math.log10(1.0 / (mse + 1e-12)) if mse > 0 else 999
    
    lap_enh = np.std(lap_func(enhanced))
    gain = (lap_enh / max(1e-12, lap_base) - 1) * 100
    
    fft_enh = np.abs(np.fft.fft2(enhanced))
    hf_enh = np.sum(fft_enh[R > 20] ** 2) / (np.sum(fft_enh ** 2) + 1e-12)
    
    print(f'  {s:<10.1f} {psnr:<12.1f} {lap_enh:<12.4f} +{gain:<8.0f}% {hf_enh:<12.4f}')
    
    # Sauver
    enh_field = enhanced * 2 - 1
    rgb_enh = HarmonicColorMapper.harmonic_hsl(enh_field, palette='cosmique')
    save_as_png(rgb_enh, os.path.join(out_dir, f'test2_enhanced_str{int(s*10):02d}.png'))

# ============================================================
# TEST 3 : Comparaison Psi1 V1 (7 ondes) vs V2 (42 ondes 1/f²) 
# ============================================================
print('\n[TEST 3] Comparaison Psi1 V1 (7 ondes) vs V2 (42 ondes 1/f²)')

# Simuler l'ancien Ψ₁ (7 ondes fixes)
def old_psi1(width, height, seed):
    rng = np.random.RandomState(seed % (2**31))
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    
    from harmonic_generator_core import PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI
    
    psi_1 = np.zeros((height, width), dtype=np.float64)
    psi_1 += 0.30 * np.cos(PHI * R * 12 + theta * PHI)
    psi_1 += 0.20 * np.sin(PI * R * 8)
    psi_1 += 0.15 * np.exp(-R * 2) * np.cos(X * 10 * E) * np.cos(Y * 10 * E)
    psi_1 += 0.15 * (np.cos(X * 8 * SQRT2) + np.cos(Y * 8 * SQRT2))
    psi_1 += 0.10 * np.cos((X + Y) * 7 * SQRT3) * np.cos((X - Y) * 7 * SQRT3)
    psi_1 += 0.07 * np.sin(X * 30 * SQRT5) * np.cos(Y * 30 * SQRT5)
    psi_1 += 0.03 * np.sin(R * 20 * E_PI + theta * 5)
    
    psi_max = np.max(np.abs(psi_1))
    if psi_max > 1e-12:
        psi_1 = psi_1 / psi_max
    return psi_1

for size in [256, 512]:
    # V1 (ancien)
    old = old_psi1(size, size, 42)
    fft_old = np.abs(np.fft.fft2(old))
    fft_old_s = np.fft.fftshift(fft_old)
    h, w = old.shape
    Y, X = np.ogrid[:h, :w]
    cy, cx = h//2, w//2
    R = np.sqrt((Y-cy)**2 + (X-cx)**2).astype(int)
    
    re_old = np.bincount(R.flatten(), weights=fft_old_s.flatten()**2)
    rc_old = np.bincount(R.flatten())
    v_old = rc_old > 0
    f_old = np.arange(len(re_old))[v_old]
    e_old = re_old[v_old] / rc_old[v_old]
    
    vr_old = (f_old >= 1) & (f_old <= min(size//6, max(f_old)))
    slope_old, _ = np.polyfit(np.log(f_old[vr_old]+1e-12), np.log(e_old[vr_old]+1e-30), 1)
    hf_old = np.sum(fft_old_s[R > size//8] ** 2) / (np.sum(fft_old_s ** 2) + 1e-12)
    
    # V2 (nouveau)
    field_new = HarmonicField(width=size, height=size, seed=42)
    new = field_new.get_psi_total()
    fft_new = np.abs(np.fft.fft2(new))
    fft_new_s = np.fft.fftshift(fft_new)
    
    re_new = np.bincount(R.flatten(), weights=fft_new_s.flatten()**2)
    rc_new = np.bincount(R.flatten())
    v_new = rc_new > 0
    f_new = np.arange(len(re_new))[v_new]
    e_new = re_new[v_new] / rc_new[v_new]
    
    vr_new = (f_new >= 1) & (f_new <= min(size//6, max(f_new)))
    slope_new, _ = np.polyfit(np.log(f_new[vr_new]+1e-12), np.log(e_new[vr_new]+1e-30), 1)
    hf_new = np.sum(fft_new_s[R > size//8] ** 2) / (np.sum(fft_new_s ** 2) + 1e-12)
    
    print(f'  {size}x{size}:')
    print(f'    V1 (7 ondes) : pente={slope_old:.2f} (err {abs(-2.0-slope_old):.2f}) | HF={hf_old:.6f}')
    print(f'    V2 (42 ondes 1/f²): pente={slope_new:.2f} (err {abs(-2.0-slope_new):.2f}) | HF={hf_new:.6f}')
    print(f'    Amelioration pente: {abs(-2.0-slope_old)-abs(-2.0-slope_new):+.2f}')
    print(f'    Boost HF: {(hf_new/max(1e-12,hf_old)-1)*100:+.0f}%')

# ============================================================
# TEST 4 : Test sur dataset si disponible
# ============================================================
print('\n[TEST 4] Recherche de photos reelles dans le dataset...')
dataset_dirs = [
    os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'unified', 'dataset'),
    os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'massive_dataset'),
]
import glob
found_photos = []
for d in dataset_dirs:
    if os.path.isdir(d):
        found_photos = sorted(glob.glob(os.path.join(d, '**', '*.jpg'), recursive=True))
        if found_photos:
            print(f'  Trouve {len(found_photos)} photos dans {d}')
            break

if found_photos:
    from PIL import Image
    # Prendre 3 photos aleatoires
    import random
    random.seed(42)
    test_photos = random.sample(found_photos, min(3, len(found_photos)))
    
    for i, photo_path in enumerate(test_photos):
        img = np.array(Image.open(photo_path).convert('L'), dtype=np.float64) / 255.0
        h, w = img.shape
        
        if min(h, w) > 1024:
            # Redimensionner pour le test
            scale = 512.0 / max(h, w)
            nh, nw = int(h*scale), int(w*scale)
            from PIL import Image as PILImage
            img = np.array(PILImage.fromarray((img*255).astype(np.uint8)).resize((nw, nh), PILImage.LANCZOS), dtype=np.float64) / 255.0
            h, w = img.shape
        
        print(f'\n  Photo {i+1}: {os.path.basename(photo_path)} ({w}x{h})')
        
        lap_orig = np.std(lap_func(img))
        
        # Test avec strength=0.5
        enhanced = enhance_existing_pipeline(img, strength=0.5, detail_seed=i*100)
        mse = np.mean((img - enhanced)**2)
        psnr = 10 * math.log10(1.0 / (mse + 1e-12))
        lap_enh = np.std(lap_func(enhanced))
        gain = (lap_enh / max(1e-12, lap_orig) - 1) * 100
        
        print(f'    Original LapStd={lap_orig:.4f}')
        print(f'    Enhanced PSNR={psnr:.1f}dB LapStd={lap_enh:.4f} (+{gain:.0f}%)')
        
        # Sauver
        save_as_png(np.stack([(np.clip(img,0,1)*255).astype(np.uint8)]*3, -1), 
                    os.path.join(out_dir, f'photo{i+1}_original.png'))
        enh_rgb = np.stack([(np.clip(enhanced,0,1)*255).astype(np.uint8)]*3, -1)
        from PIL import Image as PILImage
        PILImage.fromarray(enh_rgb, 'RGB').save(os.path.join(out_dir, f'photo{i+1}_enhanced.png'))
else:
    print('  Aucune photo trouvee dans le dataset. Test non effectue.')

print(f'\n{"="*80}')
print(f'  RESULTATS dans : {out_dir}/')
print(f'{"="*80}')