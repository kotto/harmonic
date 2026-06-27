#!/usr/bin/env python3
"""
HCV Video Boost — Décodeur Autonome
====================================

Décode un fichier .hcvb en vidéo MP4 restaurée.

Usage:
  python hcvb_decoder.py input.hcvb                    → input_restored.mp4
  python hcvb_decoder.py input.hcvb -o output.mp4      → output.mp4
  python hcvb_decoder.py input.hcvb --info              → affiche les métadonnées

Format .hcvb:
  [32 bytes header][H264/AAC MP4 payload]
  Header: MAGIC(4) + version(1) + quality(1) + orig_w(2) + orig_h(2)
          + new_w(2) + new_h(2) + fps*100(4) + payload_size(4) + reserved(11)

Nécessite: ffmpeg (via imageio-ffmpeg ou PATH système)
"""

import os
import sys
import struct
import subprocess
import tempfile
import time
import argparse
from pathlib import Path


# ─── Trouver ffmpeg ────────────────────────────────────────────────────────

def find_ffmpeg():
    """Trouve le chemin de ffmpeg."""
    try:
        import imageio_ffmpeg
        path = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(path):
            return path
    except ImportError:
        pass
    for name in ['ffmpeg', 'ffmpeg.exe']:
        try:
            r = subprocess.run([name, '-version'], capture_output=True, timeout=5)
            if r.returncode == 0:
                return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return None


# ─── Constantes ────────────────────────────────────────────────────────────

MAGIC = b'HCVB'
HEADER_FMT = '<4sBBHHHHII11s'
HEADER_SIZE = struct.calcsize(HEADER_FMT)
QUALITY_NAMES = {0: 'ultra', 1: 'high', 2: 'balanced', 3: 'compact'}


# ─── Fonctions ─────────────────────────────────────────────────────────────

def read_header(filepath):
    """Lit et parse le header d'un fichier .hcvb."""
    with open(filepath, 'rb') as f:
        raw = f.read(HEADER_SIZE)
    if len(raw) < HEADER_SIZE:
        raise ValueError(f"Fichier trop petit ({len(raw)} bytes, minimum {HEADER_SIZE})")
    
    magic, ver, qi, orig_w, orig_h, new_w, new_h, fps100, comp_size, _ = \
        struct.unpack(HEADER_FMT, raw)
    
    if magic != MAGIC:
        raise ValueError(f"Pas un fichier .hcvb (magic: {magic!r}, attendu: {MAGIC!r})")
    
    return {
        'version': ver,
        'quality': QUALITY_NAMES.get(qi, f'unknown({qi})'),
        'quality_idx': qi,
        'original_width': orig_w,
        'original_height': orig_h,
        'compressed_width': new_w,
        'compressed_height': new_h,
        'fps': fps100 / 100.0,
        'payload_size': comp_size,
        'header_size': HEADER_SIZE,
        'file_size': os.path.getsize(filepath),
    }


def show_info(filepath):
    """Affiche les métadonnées d'un fichier .hcvb."""
    info = read_header(filepath)
    file_size = info['file_size']
    
    print(f"\n{'='*50}")
    print(f"  HCV Video Boost — Info fichier")
    print(f"{'='*50}")
    print(f"  Fichier:      {filepath}")
    print(f"  Taille:       {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    print(f"  Version:      {info['version']}")
    print(f"  Qualité:      {info['quality']}")
    print(f"  Résolution originale:  {info['original_width']}x{info['original_height']}")
    print(f"  Résolution compressée: {info['compressed_width']}x{info['compressed_height']}")
    print(f"  Scale factor: {info['compressed_width']/info['original_width']:.2f}x")
    print(f"  FPS:          {info['fps']:.2f}")
    print(f"  Payload:      {info['payload_size']:,} bytes ({info['payload_size']/1024/1024:.2f} MB)")
    print(f"  Header:       {info['header_size']} bytes")
    print(f"{'='*50}\n")
    return info


def decode(input_path, output_path=None, verbose=True):
    """Décode un fichier .hcvb en MP4.
    
    Args:
        input_path: chemin du fichier .hcvb
        output_path: chemin de sortie (auto si None)
        verbose: afficher les messages de progression
    
    Returns:
        (output_path, info_dict)
    """
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("ERREUR: ffmpeg non trouvé!")
        print("  Installer: pip install imageio-ffmpeg")
        print("  Ou: télécharger ffmpeg depuis https://ffmpeg.org/download.html")
        sys.exit(1)
    
    t0 = time.perf_counter()
    
    # Lire le header
    info = read_header(input_path)
    orig_w = info['original_width']
    orig_h = info['original_height']
    
    if verbose:
        print(f"Décodage: {input_path}")
        print(f"  Résolution: {info['compressed_width']}x{info['compressed_height']} → {orig_w}x{orig_h}")
        print(f"  Qualité: {info['quality']}")
    
    # Extraire le payload MP4 dans un fichier temporaire
    tmp_mp4 = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
    with open(input_path, 'rb') as src:
        src.seek(HEADER_SIZE)
        with open(tmp_mp4, 'wb') as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
    
    if output_path is None:
        stem = Path(input_path).stem
        output_path = str(Path(input_path).parent / f'{stem}_restored.mp4')
    
    # Upscale Lanczos + léger sharpen via ffmpeg (avec audio)
    rw = orig_w - (orig_w % 2)
    rh = orig_h - (orig_h % 2)
    
    cmd = [
        ffmpeg, '-y', '-i', tmp_mp4,
        '-vf', f'scale={rw}:{rh}:flags=lanczos,unsharp=3:3:0.5:3:3:0.0',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '17',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        output_path
    ]
    
    if verbose:
        print(f"  ffmpeg: upscale + sharpen...")
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        # Fallback
        if verbose:
            print(f"  Fallback encoder...")
        cmd2 = [
            ffmpeg, '-y', '-i', tmp_mp4,
            '-vf', f'scale={rw}:{rh}:flags=lanczos,unsharp=3:3:0.5:3:3:0.0',
            '-c:v', 'mpeg4', '-q:v', '2',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            output_path
        ]
        r = subprocess.run(cmd2, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            os.unlink(tmp_mp4)
            raise RuntimeError(f"ffmpeg decode failed:\n{r.stderr[-500:]}")
    
    os.unlink(tmp_mp4)
    
    elapsed = time.perf_counter() - t0
    restored_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    
    if verbose:
        print(f"  Sortie: {output_path}")
        print(f"  Taille: {restored_size:,} bytes ({restored_size/1024/1024:.2f} MB)")
        print(f"  Temps:  {elapsed:.1f}s")
        print(f"  ✅ Décodage terminé!")
    
    return output_path, {
        **info,
        'output_path': output_path,
        'restored_size': restored_size,
        'decode_time': round(elapsed, 1),
    }


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='HCV Video Boost — Décodeur autonome (.hcvb → .mp4)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python hcvb_decoder.py video.hcvb                  Décode → video_restored.mp4
  python hcvb_decoder.py video.hcvb -o sortie.mp4    Décode → sortie.mp4
  python hcvb_decoder.py video.hcvb --info            Affiche les métadonnées
  python hcvb_decoder.py *.hcvb                       Décode tous les fichiers
"""
    )
    parser.add_argument('input', nargs='+', help='Fichier(s) .hcvb à décoder')
    parser.add_argument('-o', '--output', help='Chemin de sortie (un seul fichier)')
    parser.add_argument('--info', action='store_true', help='Afficher les métadonnées uniquement')
    parser.add_argument('-q', '--quiet', action='store_true', help='Mode silencieux')
    
    args = parser.parse_args()
    
    if args.output and len(args.input) > 1:
        print("ERREUR: -o ne peut être utilisé qu'avec un seul fichier d'entrée")
        sys.exit(1)
    
    for filepath in args.input:
        if not os.path.exists(filepath):
            print(f"ERREUR: fichier introuvable: {filepath}")
            continue
        
        try:
            if args.info:
                show_info(filepath)
            else:
                decode(filepath, args.output, verbose=not args.quiet)
                if not args.quiet:
                    print()
        except Exception as e:
            print(f"ERREUR: {filepath}: {e}")
            if not args.quiet:
                import traceback
                traceback.print_exc()


if __name__ == '__main__':
    main()
