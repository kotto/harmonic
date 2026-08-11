"""
Harmonic Codec CLI — Compression/Décompression d'images et vidéos
==================================================================

Usage:
    python hc.py compress image.jpg -o output.hhc
    python hc.py decompress output.hhc -o restored.png
    python hc.py benchmark image.jpg
    python hc.py build-dict --corpus ./images/ -o dict.hdb
    python hc.py video input_frames/ -o video.hhc

Pour le mode dictionnaire (meilleure compression):
    python hc.py build-dict --corpus ./training_images/ -o dict.hdb
    python hc.py compress image.jpg -d dict.hdb -o output.hhc
"""

import sys
import os
import argparse
import time
from pathlib import Path
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ENGINE_DIR))
sys.path.insert(0, str(_ENGINE_DIR / 'multimodal'))


def load_image(path: str, max_size: int = 4096) -> np.ndarray:
    """Charge une image RGB uint8."""
    try:
        import cv2
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Impossible de lire: {path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except ImportError:
        from PIL import Image
        img = np.array(Image.open(path).convert('RGB'))
    
    H, W = img.shape[:2]
    if max(H, W) > max_size:
        scale = max_size / max(H, W)
        new_h, new_w = int(H * scale), int(W * scale)
        try:
            import cv2
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        except:
            from PIL import Image
            img = np.array(Image.fromarray(img).resize((new_w, new_h), Image.LANCZOS))
    
    return img


def save_image(img: np.ndarray, path: str):
    """Sauvegarde une image RGB uint8."""
    try:
        import cv2
        cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    except ImportError:
        from PIL import Image
        Image.fromarray(img).save(path)


def cmd_compress(args):
    """Compresse une image."""
    from harmonic_database import HarmonicDatabase
    from harmonic_codec import HarmonicCodec
    
    img = load_image(args.input)
    print(f"📥 Image: {img.shape[1]}×{img.shape[0]} RGB  {img.nbytes/1024:.0f} Ko")
    
    # Charger le dictionnaire si fourni
    db = None
    if args.dict:
        db = HarmonicDatabase()
        db.load(args.dict)
        print(f"📚 Dictionnaire: {args.dict}  ({len(db._shards)} shards)")
    else:
        db = HarmonicDatabase(patch_size=args.patch_size, K=args.K, stride=args.patch_size)
    
    # Créer le codec
    hc = HarmonicCodec(db, use_hcv=args.hcv, quality=args.quality, zstd_level=args.zstd_level)
    
    # Encoder
    t0 = time.perf_counter()
    if args.v2 and db and len(db._shards) > 0:
        data = hc.encode_v2(img)
        mode = 'V2 (dictionnaire partagé)'
    elif db and len(db._shards) > 0:
        # Sélecteur optimal : le plus petit de V2 DICT / FULL (zéro perte)
        data, mode = hc.encode_best(img)
        mode = f'BEST ({mode})'
    else:
        data = hc.encode_full(img)
        mode = 'FULL (autonome)'
    encode_ms = (time.perf_counter() - t0) * 1000
    
    # Sauvegarder
    output = args.output or (Path(args.input).stem + '.hhc')
    with open(output, 'wb') as f:
        f.write(data)
    
    ratio = img.nbytes / len(data)
    print(f"📦 Mode: {mode}")
    print(f"   {img.nbytes/1024:.0f}K → {len(data)/1024:.1f}K  ({ratio:.1f}:1)  {encode_ms:.0f}ms")
    print(f"✅ Sauvegardé: {output}")


def cmd_decompress(args):
    """Décompresse un bitstream HHDC/HHD2."""
    from harmonic_database import HarmonicDatabase
    from harmonic_codec import HarmonicCodec
    
    with open(args.input, 'rb') as f:
        data = f.read()
    
    # Détecter le format
    magic = data[:4]
    is_v2 = (magic == b'HHD2')
    
    # Charger le dictionnaire si fourni (requis pour V2)
    db = None
    if args.dict:
        db = HarmonicDatabase()
        db.load(args.dict)
    
    hc = HarmonicCodec(db or HarmonicDatabase(patch_size=16, K=8), use_hcv=False)
    
    t0 = time.perf_counter()
    if is_v2:
        result = hc.decode_v2(data, database=db)
    else:
        result = hc.decode_full(data)
    decode_ms = (time.perf_counter() - t0) * 1000
    
    if isinstance(result, tuple):
        img, meta = result
    else:
        img, meta = result, {}
    
    output = args.output or (Path(args.input).stem + '_restored.png')
    save_image(img, output)
    
    print(f"📤 Décompressé: {img.shape[1]}×{img.shape[0]}  {decode_ms:.0f}ms")
    print(f"   Format: {'HHD2' if is_v2 else 'HHDC'}  Mode: {meta.get('shared_dict', False)}")
    print(f"✅ Sauvegardé: {output}")


def cmd_benchmark(args):
    """Benchmark complet d'une image."""
    from harmonic_database import HarmonicDatabase
    from harmonic_codec import HarmonicCodec
    
    img = load_image(args.input, max_size=2048)
    print(f"📥 Image: {img.shape[1]}×{img.shape[0]} RGB  {img.nbytes/1024:.0f} Ko\n")
    
    configs = [
        ('FULL ps=8',  HarmonicCodec(HarmonicDatabase(patch_size=8,  K=4, stride=8),  use_hcv=False, quality=100)),
        ('FULL ps=16', HarmonicCodec(HarmonicDatabase(patch_size=16, K=4, stride=16), use_hcv=False, quality=100)),
        ('FULL ps=32', HarmonicCodec(HarmonicDatabase(patch_size=32, K=4, stride=32), use_hcv=False, quality=100)),
        ('Q70 ps=16',  HarmonicCodec(HarmonicDatabase(patch_size=16, K=4, stride=16), use_hcv=False, quality=70)),
        ('Q45 ps=16',  HarmonicCodec(HarmonicDatabase(patch_size=16, K=4, stride=16), use_hcv=False, quality=45)),
    ]
    
    # Ajouter mode dictionnaire si dispo
    if args.dict and Path(args.dict).exists():
        db = HarmonicDatabase()
        db.load(args.dict)
        configs.insert(0, ('V2 DICT', HarmonicCodec(db, use_hcv=False, quality=100)))
    
    print(f"{'Mode':<15} {'Ratio':>8} {'PSNR':>8} {'Encode':>8} {'Décode':>8}  {'Taille'}")
    print('-' * 65)
    
    for name, hc in configs:
        result = hc.benchmark(img)
        print(f"{name:<15} {result['ratio']:>7.1f}x {result['psnr_db']:>7.1f}dB "
              f"{result['encode_ms']:>7.0f}ms {result['decode_ms']:>7.0f}ms  "
              f"{result['bitstream_bytes']/1024:.1f}K")


def cmd_build_dict(args):
    """Construit un dictionnaire harmonique."""
    from build_dict import build_dictionary
    
    build_dictionary(
        corpus_dir=args.corpus,
        output_path=args.output,
        patch_size=args.patch_size,
        K=args.K,
        stride=args.stride,
        quality=args.quality,
        max_images=args.max_images,
    )


def cmd_video(args):
    """Compresse une séquence vidéo (dossier d'images)."""
    from harmonic_database import HarmonicDatabase
    from harmonic_codec import HarmonicCodec
    
    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"❌ {args.input} n'est pas un dossier")
        return
    
    # Charger les frames
    frames = []
    for img_path in sorted(input_dir.glob('*')):
        if img_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp'}:
            try:
                frames.append(load_image(str(img_path), max_size=2048))
            except:
                pass
    
    if not frames:
        print(f"❌ Aucune image trouvée dans {args.input}")
        return
    
    print(f"📥 {len(frames)} frames  {frames[0].shape[1]}×{frames[0].shape[0]}")
    
    db = HarmonicDatabase(patch_size=args.patch_size, K=args.K, stride=args.patch_size)
    hc = HarmonicCodec(db, use_hcv=False, quality=args.quality)
    
    t0 = time.perf_counter()
    data = hc.encode_video(frames, skip_threshold=args.skip_threshold,
                          motion_search_range=args.motion_range)
    encode_ms = (time.perf_counter() - t0) * 1000
    
    output = args.output or 'video.hhc'
    with open(output, 'wb') as f:
        f.write(data)
    
    raw_total = sum(f.nbytes for f in frames)
    ratio = raw_total / len(data)
    
    print(f"📦 {raw_total/1024:.0f}K → {len(data)/1024:.1f}K  ({ratio:.1f}:1)  {encode_ms:.0f}ms")
    print(f"   Skip: {hc._last_video_skip_rate*100:.0f}%  MC: {hc._last_video_mc_rate*100:.0f}%")
    print(f"✅ Sauvegardé: {output}")


def main():
    parser = argparse.ArgumentParser(
        description='Harmonic Codec — Compression harmonique d\'images et vidéos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest='command', help='Commande')
    
    # compress
    p = sub.add_parser('compress', help='Compresser une image')
    p.add_argument('input', help='Image source')
    p.add_argument('-o', '--output', help='Fichier de sortie (.hhc)')
    p.add_argument('-d', '--dict', help='Dictionnaire entraîné (.hdb)')
    p.add_argument('--v2', action='store_true', help='Mode dictionnaire partagé (HHD2)')
    p.add_argument('--hcv', action='store_true', help='Utiliser HCV Pro pour le résidu')
    p.add_argument('--quality', type=int, default=100, help='Qualité 0-100')
    p.add_argument('--zstd-level', type=int, default=11, help='Niveau zstd 1-22')
    p.add_argument('--patch-size', type=int, default=32)
    p.add_argument('--K', type=int, default=4)
    
    # decompress
    p = sub.add_parser('decompress', help='Décompresser un fichier .hhc')
    p.add_argument('input', help='Bitstream HHDC/HHD2')
    p.add_argument('-o', '--output', help='Image de sortie')
    p.add_argument('-d', '--dict', help='Dictionnaire partagé (pour HHD2)')
    
    # benchmark
    p = sub.add_parser('benchmark', help='Benchmarker une image')
    p.add_argument('input', help='Image source')
    p.add_argument('-d', '--dict', help='Dictionnaire partagé')
    
    # build-dict
    p = sub.add_parser('build-dict', help='Construire un dictionnaire')
    p.add_argument('--corpus', required=True, help='Dossier d\'images d\'entraînement')
    p.add_argument('-o', '--output', default='harmonic_dict.hdb')
    p.add_argument('--patch-size', type=int, default=32)
    p.add_argument('--K', type=int, default=8)
    p.add_argument('--stride', type=int, default=None)
    p.add_argument('--quality', choices=['fast', 'balanced', 'deep'], default='balanced')
    p.add_argument('--max-images', type=int, default=None)
    
    # video
    p = sub.add_parser('video', help='Compresser une séquence vidéo')
    p.add_argument('input', help='Dossier de frames')
    p.add_argument('-o', '--output')
    p.add_argument('--patch-size', type=int, default=32)
    p.add_argument('--K', type=int, default=4)
    p.add_argument('--quality', type=int, default=100)
    p.add_argument('--skip-threshold', type=float, default=5.0)
    p.add_argument('--motion-range', type=int, default=8)
    
    args = parser.parse_args()
    
    if args.command == 'compress':
        cmd_compress(args)
    elif args.command == 'decompress':
        cmd_decompress(args)
    elif args.command == 'benchmark':
        cmd_benchmark(args)
    elif args.command == 'build-dict':
        cmd_build_dict(args)
    elif args.command == 'video':
        cmd_video(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
