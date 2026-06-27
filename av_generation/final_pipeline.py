#!/usr/bin/env python3
# coding: utf-8
"""
FINAL PIPELINE — Hologramme + Couleur + Upscale + Sharpener
=============================================================
Pipeline complet en 5 etapes :
  1. Extraction hologramme SVD (K=16, 8 Ko par canal RGB)
  2. Reconstruction couleur depuis l'hologramme (PSNR ~38 dB)
  3. Harmonic Sharpener (residu + 7Hn) 
  4. Real Upscale (SVD 2x -> Lanczos -> Hn sharpen -> 4K)
  5. Sauvegarde comparative

Usage :
  python final_pipeline.py --demo
  python final_pipeline.py --image photo.jpg --upscale 4k
"""

import numpy as np, os, sys, time, glob, argparse
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import HarmonicColorMapper, save_image
from holographic_one_shot import HolographicTrainer, HolographicGenerator
from harmonic_sharpener import HarmonicSharpener
from unified_superior_engine import RealUpscalePipeline


def process_image_rgb(img_rgb, K=16, upscale_res=None):
    """Traite une image couleur : SVD par canal + sharpener + upscale."""
    h, w, c = img_rgb.shape
    
    # Etape 1 : SVD par canal R,G,B
    holograms = {}
    reconstructions = {}
    metrics = {}
    
    for ch_idx, ch_name in enumerate(['R', 'G', 'B']):
        ch = img_rgb[:,:,ch_idx].astype(np.float64) / 255.0
        sig = HolographicTrainer.train_image(ch, K=K)
        recon = HolographicGenerator.reconstruct(sig, width=w, height=h)
        
        diff = ch - recon
        mse = float(np.mean(diff ** 2))
        psnr = float(10 * np.log10(1.0 / (mse + 1e-12))) if mse > 0 else 999
        
        holograms[ch_name] = sig
        reconstructions[ch_name] = recon
        metrics[ch_name] = {'mse': mse, 'psnr': psnr}
    
    # Reconstruire l'image RGB
    recon_rgb = np.stack([reconstructions[c] for c in ['R','G','B']], axis=-1)
    recon_rgb = np.clip(recon_rgb, 0, 1)
    
    # Etape 2 : Harmonic Sharpener (sur luminance)
    lum = 0.299 * reconstructions['R'] + 0.587 * reconstructions['G'] + 0.114 * reconstructions['B']
    sharpener = HarmonicSharpener(K=K)
    sharp_lum = sharpener.sharpen(lum, strength=1.0)
    
    # Appliquer le sharpening aux canaux RGB (proportionnellement)
    ratio = sharp_lum / (lum + 1e-12)
    ratio = np.clip(ratio, 0.5, 2.0)
    sharp_rgb = recon_rgb.copy()
    for c in range(3):
        sharp_rgb[:,:,c] = np.clip(sharp_rgb[:,:,c] * ratio, 0, 1)
    
    # Etape 3 : Upscale (si demandé)
    if upscale_res and upscale_res != 'sd':
        from unified_superior_engine import RESOLUTIONS
        target_w, target_h = RESOLUTIONS.get(upscale_res, (512, 512))
        
        upscaler = RealUpscalePipeline()
        upscaled_channels = []
        for c in range(3):
            ch = sharp_rgb[:,:,c]
            # SVD 2x
            if ch.shape[1] < target_w // 2:
                ch = upscaler.svd_upscale(ch, K=K)
            # Lanczos vers cible
            if ch.shape[1] != target_w or ch.shape[0] != target_h:
                ch = upscaler.lanczos_upscale(ch, target_w, target_h)
            # Hn sharpen
            ch = upscaler.harmonic_sharpen(ch)
            upscaled_channels.append(ch)
        
        final_rgb = np.stack(upscaled_channels, axis=-1)
        final_rgb = np.clip(final_rgb, 0, 1)
    else:
        final_rgb = sharp_rgb
    
    # Etape 4 : Métriques finales
    original_lum = 0.299 * img_rgb[:,:,0].astype(float)/255 + 0.587 * img_rgb[:,:,1].astype(float)/255 + 0.114 * img_rgb[:,:,2].astype(float)/255
    final_lum = 0.299 * final_rgb[:,:,0] + 0.587 * final_rgb[:,:,1] + 0.114 * final_rgb[:,:,2]
    
    # Mesurer netteté
    sharp_metrics = sharpener.analyze_sharpness(final_lum)
    
    return {
        'reconstructed': recon_rgb,
        'sharpened': final_rgb,
        'holograms': holograms,
        'metrics': {
            'per_channel': metrics,
            'avg_psnr': np.mean([m['psnr'] for m in metrics.values()]),
            'avg_mse': np.mean([m['mse'] for m in metrics.values()]),
            'sharpness': sharp_metrics,
        },
    }


def demo_final_pipeline():
    """Demo complete avec upscale."""
    print("═" * 70)
    print("  FINAL PIPELINE — Hologramme + Couleur + Upscale + Sharpener")
    print("═" * 70)
    
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'final_pipeline')
    os.makedirs(out_dir, exist_ok=True)
    
    # Prendre une vraie photo
    files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..',
                        'av_generation_output/massive_dataset/**/*.jpg'), recursive=True))
    fpath = files[50]
    print(f"\n  Photo source : {os.path.basename(fpath)}")
    
    img_color = np.array(Image.open(fpath).convert('RGB'))
    h, w = img_color.shape[:2]
    print(f"  Dimensions : {w}x{h}")
    
    # Sauvegarder l'original
    Image.fromarray(img_color).save(os.path.join(out_dir, '01_original.jpg'))
    
    # Pipeline complet
    t0 = time.time()
    result = process_image_rgb(img_color, K=16, upscale_res=None)
    elapsed = (time.time() - t0) * 1000
    
    # Metriques
    m = result['metrics']
    print(f"\n  📊 Métriques SVD par canal :")
    for ch in ['R', 'G', 'B']:
        print(f"    Canal {ch} : PSNR={m['per_channel'][ch]['psnr']:.1f} dB | MSE={m['per_channel'][ch]['mse']:.6f}")
    print(f"    PSNR moyen : {m['avg_psnr']:.1f} dB")
    print(f"    Sharpness  : acutance={m['sharpness']['acutance']:.4f} | lap_std={m['sharpness']['laplacian_std']:.4f}")
    print(f"    Temps      : {elapsed:.0f}ms")
    
    # Taille hologramme
    total_holo_bytes = sum(result['holograms'][c].hologram.nbytes + result['holograms'][c].coefficients.nbytes for c in 'RGB')
    print(f"    Hologramme : {total_holo_bytes:,} octets (3 canaux x K=16)")
    print(f"    Original   : {os.path.getsize(fpath):,} octets")
    print(f"    Ratio      : {os.path.getsize(fpath)/max(1,total_holo_bytes):.1f}x")
    
    # Sauvegarder
    Image.fromarray((result['reconstructed']*255).astype(np.uint8)).save(os.path.join(out_dir, '02_reconstructed.png'))
    Image.fromarray((result['sharpened']*255).astype(np.uint8)).save(os.path.join(out_dir, '03_sharpened.png'))
    
    # Upscale 4K
    print(f"\n  🔼 Upscale 4K...")
    t0 = time.time()
    result_4k = process_image_rgb(img_color, K=16, upscale_res='4k')
    up_elapsed = (time.time() - t0) * 1000
    print(f"    Dimensions 4K : {result_4k['sharpened'].shape[1]}x{result_4k['sharpened'].shape[0]}")
    print(f"    Temps upscale : {up_elapsed:.0f}ms")
    Image.fromarray((result_4k['sharpened']*255).astype(np.uint8)).save(os.path.join(out_dir, '04_upscaled_4k.png'))
    
    print(f"\n  ✅ Fichiers dans : {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        print(f"    {f}")
    
    print(f"""
  Résumé :
    01_original.jpg       - Photo réelle originale ({w}x{h})
    02_reconstructed.png  - Reconstruite depuis hologramme SVD K=16 (PSNR {m['avg_psnr']:.0f} dB)
    03_sharpened.png      - Après Harmonic Sharpener (résidu + 7Hn)
    04_upscaled_4k.png    - Upscale SVD 2x -> Lanczos -> 4K

  Hologramme total : {total_holo_bytes:,} octets pour stocker l'image entière (vs {os.path.getsize(fpath):,} o JPEG)
  C'est l'équivalent de compresser la photo en une matrice d'ondes propres.
""")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Final Pipeline')
    parser.add_argument('--demo', action='store_true', help='Démo complète')
    parser.add_argument('--image', type=str, default=None, help='Image source')
    parser.add_argument('--upscale', type=str, default=None, choices=['sd','hd','4k','8k'])
    parser.add_argument('--output', type=str, default='final_output.png')
    args = parser.parse_args()
    
    if args.image:
        img = np.array(Image.open(args.image).convert('RGB'))
        result = process_image_rgb(img, K=16, upscale_res=args.upscale)
        out = (result['sharpened'] * 255).astype(np.uint8)
        Image.fromarray(out).save(args.output)
        m = result['metrics']
        print(f"Image sauvegardée : {args.output}")
        print(f"PSNR moyen : {m['avg_psnr']:.1f} dB")
        if args.upscale:
            print(f"Dimensions : {out.shape[1]}x{out.shape[0]}")
    else:
        demo_final_pipeline()