#!/usr/bin/env python
"""
HarmonicVisuals CLI — Génération d'images et vidéos en ligne de commande
=========================================================================

Usage:
  python scripts/generate.py "sunset over mountains" --mode geometric --width 1024
  python scripts/generate.py "forest path" --mode hybrid --upscale 4 --compress
  python scripts/generate.py "city lights at night" --video --duration 5 --fps 24
"""

import sys, os, argparse, time
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from harmonic_visuals import HarmonicVisuals

def main():
    p = argparse.ArgumentParser(description='HarmonicVisuals — Générateur d\'images/vidéos')
    p.add_argument('prompt', nargs='?', default='abstract geometric pattern', help='Prompt textuel')
    p.add_argument('--mode', choices=['geometric','realistic','hybrid'], default='geometric')
    p.add_argument('--width', type=int, default=512); p.add_argument('--height', type=int, default=512)
    p.add_argument('--upscale', type=int, choices=[2,4], help='Facteur upscale')
    p.add_argument('--compress', action='store_true', help='Compresser HCV')
    p.add_argument('--video', action='store_true', help='Générer une vidéo')
    p.add_argument('--duration', type=float, default=3.0, help='Durée vidéo (s)')
    p.add_argument('--fps', type=int, default=12, help='FPS vidéo')
    p.add_argument('--output', '-o', default=None, help='Fichier de sortie')
    args = p.parse_args()
    
    print(f'🎨 HarmonicVisuals v1.0 — Mode: {args.mode}')
    hv = HarmonicVisuals()
    
    if args.video:
        print(f'🎬 Génération vidéo: \"{args.prompt}\" ({args.duration}s, {args.fps}fps)...')
        frames = hv.generate_video(args.prompt, args.duration, args.fps, args.width, args.height, args.mode)
        print(f'✓ {len(frames)} frames générées')
        # Sauvegarde GIF
        try:
            from PIL import Image
            gif_path = args.output or 'output.gif'
            Image.fromarray(frames[0]).save(gif_path, save_all=True, append_images=[Image.fromarray(f) for f in frames[1:]], duration=int(1000/args.fps), loop=0)
            print(f'✓ Sauvegardé: {gif_path}')
        except: print('⚠ Sauvegarde GIF impossible (installer Pillow)')
    else:
        print(f'🖼️  Génération: \"{args.prompt}\" ({args.width}×{args.height})...')
        t0 = time.perf_counter()
        result = hv.pipeline(args.prompt, mode=args.mode, width=args.width, height=args.height,
                            upscale=args.upscale, compress=args.compress)
        elapsed = (time.perf_counter()-t0)*1000
        img = result['image']
        out = args.output or 'output.png'
        from PIL import Image; Image.fromarray(img).save(out)
        print(f'✓ {out} ({img.shape[1]}×{img.shape[0]}, {elapsed:.0f}ms)')
        if result.get('compression_ratio'):
            print(f'  Compression: {result["compression_ratio"]}:1')

if __name__ == '__main__': main()
