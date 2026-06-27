"""Mesure le PSNR vidéo entre source et restauré via ffmpeg + opencv."""
import glob, os, tempfile, subprocess, sys
import numpy as np
import cv2

tmp_dir = tempfile.gettempdir()
print(f"Temp dir: {tmp_dir}")

# Trouver les fichiers source et restauré
mp4_files = sorted(glob.glob(os.path.join(tmp_dir, 'tmp*.mp4')), key=os.path.getmtime)
restored = [f for f in mp4_files if '_restored' in f]
sources = [f for f in mp4_files if '_restored' not in f and '.hcvb' not in f]

if not restored:
    print("Pas de fichier restauré trouvé. Lançons un test complet.")
    sys.path.insert(0, 'codecs')
    from hcv_video_boost_codec import HCVVideoBoost
    
    # Utiliser B3.mp4 s'il existe
    test_video = None
    for p in ['../B3.mp4', 'B3.mp4']:
        if os.path.exists(p):
            test_video = p
            break
    
    if not test_video:
        print("Pas de vidéo de test trouvée")
        sys.exit(1)
    
    print(f"Test avec: {test_video} ({os.path.getsize(test_video)/1024/1024:.1f} MB)")
    codec = HCVVideoBoost(quality='high')
    out_hcvb = os.path.join(tmp_dir, '_psnr_test.hcvb')
    out_restored = os.path.join(tmp_dir, '_psnr_test_restored.mp4')
    
    _, enc_stats = codec.encode(test_video, out_hcvb)
    print(f"Encoded: {enc_stats['compressed_size']/1024/1024:.2f} MB, ratio={enc_stats['ratio']}")
    
    _, dec_stats = codec.decode(out_hcvb, out_restored)
    print(f"Restored: {os.path.getsize(out_restored)/1024/1024:.2f} MB")
    
    source_path = test_video
    restored_path = out_restored
else:
    source_path = sources[-1] if sources else None
    restored_path = restored[-1]
    print(f"Source: {source_path} ({os.path.getsize(source_path)/1024/1024:.1f} MB)" if source_path else "Source non trouvée")
    print(f"Restored: {restored_path} ({os.path.getsize(restored_path)/1024/1024:.1f} MB)")

if not source_path:
    print("Impossible de trouver la source")
    sys.exit(1)

# Calculer PSNR frame par frame via OpenCV
cap_src = cv2.VideoCapture(source_path)
cap_rst = cv2.VideoCapture(restored_path)

psnr_values = []
ssim_values = []
frame_count = 0
max_frames = 30  # Limiter pour la vitesse

while frame_count < max_frames:
    ret1, f1 = cap_src.read()
    ret2, f2 = cap_rst.read()
    if not ret1 or not ret2:
        break
    
    # Redimensionner au même format si nécessaire
    if f1.shape != f2.shape:
        f2 = cv2.resize(f2, (f1.shape[1], f1.shape[0]), interpolation=cv2.INTER_LANCZOS4)
    
    psnr = cv2.PSNR(f1, f2)
    psnr_values.append(psnr)
    frame_count += 1

cap_src.release()
cap_rst.release()

if psnr_values:
    avg_psnr = np.mean(psnr_values)
    min_psnr = np.min(psnr_values)
    max_psnr = np.max(psnr_values)
    print(f"\n=== PSNR Vidéo (sur {frame_count} frames) ===")
    print(f"  Moyenne: {avg_psnr:.2f} dB")
    print(f"  Min:     {min_psnr:.2f} dB")
    print(f"  Max:     {max_psnr:.2f} dB")
    print(f"\nInterprétation:")
    if avg_psnr > 40:
        print(f"  > 40 dB = Quasi-transparent, différences invisibles")
    elif avg_psnr > 35:
        print(f"  35-40 dB = Très bonne qualité, différences subtiles")
    elif avg_psnr > 30:
        print(f"  30-35 dB = Bonne qualité, légères différences visibles")
    else:
        print(f"  < 30 dB = Qualité moyenne, différences notables")
else:
    print("Aucune frame analysée")
