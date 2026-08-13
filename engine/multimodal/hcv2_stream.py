#!/usr/bin/env python3
"""
hcv2_stream — Outil de segmentation VOD pour le streaming HCV2
===============================================================
Découpe une vidéo en segments .hcv2 + génère le manifest HLS (.m3u8).

Usage:
    python hcv2_stream.py segment --input video.mp4 --output ./segments/ --segment-duration 2
    python hcv2_stream.py manifest --input ./segments/ --output playlist.m3u8
    python hcv2_stream.py serve --port 8080 --dir ./segments/
"""
import sys, os, time, json, struct, math, subprocess, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import cv2
from PIL import Image
from multimodal.harmonic_codec import HarmonicCodec
from multimodal.harmonic_database import HarmonicDatabase
from multimodal.build_dict import build_dictionary


def extract_frames(video_path, max_frames=0, target_size=None):
    """Extrait les frames d'une vidéo."""
    cap = cv2.VideoCapture(video_path)
    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    while cap.isOpened():
        ok, f = cap.read()
        if not ok: break
        f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        if target_size and max(f.shape[:2]) > target_size:
            s = target_size / max(f.shape[:2])
            f = cv2.resize(f, (int(f.shape[1]*s), int(f.shape[0]*s)))
        frames.append(f)
        if max_frames and len(frames) >= max_frames:
            break
    cap.release()
    return frames, fps, total


def segment_video(frames, fps, gop_size=12, skip_threshold=5.0, dict_path=None):
    """Segmente une vidéo en GOPs .hcv2."""
    if dict_path and Path(dict_path).exists():
        db = HarmonicDatabase()
        db.load(str(dict_path))
    else:
        db = HarmonicDatabase(patch_size=32, K=8, stride=32)
    
    hc = HarmonicCodec(db, use_hcv=True, quality=100)
    segments = []
    n_frames = len(frames)
    seg_duration = gop_size / fps  # secondes par segment
    
    for start in range(0, n_frames, gop_size):
        end = min(start + gop_size, n_frames)
        gop_frames = frames[start:end]
        
        t0 = time.perf_counter()
        data = hc.encode_video(gop_frames, concept='default',
                               skip_threshold=skip_threshold,
                               motion_search_range=8,
                               gop_size=gop_size)
        enc_time = time.perf_counter() - t0
        
        segments.append({
            'data': data,
            'start_frame': start,
            'end_frame': end,
            'duration': seg_duration,
            'enc_time': enc_time,
            'size': len(data),
        })
        
        sys.stdout.write(f"\r  Segment {start//gop_size + 1}/{(n_frames+gop_size-1)//gop_size} "
                        f"({len(data)//1024} Ko, {enc_time:.1f}s)")
        sys.stdout.flush()
    
    print()
    return segments


def generate_manifest(segments, output_dir, fps, name="playlist"):
    """Génère le manifest HLS (.m3u8)."""
    manifest_path = Path(output_dir) / f"{name}.m3u8"
    with open(manifest_path, 'w') as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:7\n")
        f.write(f"#EXT-X-TARGETDURATION:{int(segments[0]['duration'])+1}\n")
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
        f.write("#EXT-X-PLAYLIST-TYPE:VOD\n\n")
        for i, seg in enumerate(segments):
            f.write(f"#EXTINF:{seg['duration']:.3f},\n")
            f.write(f"segment_{i:04d}.hcv2\n")
        f.write("#EXT-X-ENDLIST\n")
    return manifest_path


def serve_directory(port=8080, directory='./segments/'):
    """Lance un serveur HTTP simple pour le streaming."""
    import http.server
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    handler.extensions_map.update({
        '.hcv2': 'application/octet-stream',
        '.m3u8': 'application/vnd.apple.mpegurl',
    })
    print(f"🚀 Serveur streaming : http://localhost:{port}")
    print(f"   Player : http://localhost:{port}/player.html")
    http.server.HTTPServer(('0.0.0.0', port), handler).serve_forever()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='HCV2 Stream — Segmentation VOD')
    sub = parser.add_subparsers(dest='command')
    
    p_seg = sub.add_parser('segment', help='Segmenter une vidéo')
    p_seg.add_argument('--input', '-i', required=True, help='Vidéo source')
    p_seg.add_argument('--output', '-o', default='./segments', help='Dossier de sortie')
    p_seg.add_argument('--gop-size', type=int, default=12, help='Frames par GOP/segment')
    p_seg.add_argument('--max-frames', type=int, default=0, help='Max frames à traiter')
    p_seg.add_argument('--target-size', type=int, default=1080, help='Résolution cible (max)')
    p_seg.add_argument('--dict', '-d', help='Dictionnaire optionnel')
    p_seg.add_argument('--skip', type=float, default=5.0, help='Skip threshold')
    
    p_man = sub.add_parser('manifest', help='Générer le manifest HLS')
    p_man.add_argument('--input', '-i', default='./segments', help='Dossier des segments')
    p_man.add_argument('--output', '-o', default='playlist.m3u8', help='Fichier manifest')
    p_man.add_argument('--fps', type=float, default=24.0, help='FPS de la vidéo')
    p_man.add_argument('--name', default='playlist', help='Nom du manifest')
    
    p_serve = sub.add_parser('serve', help='Serveur HTTP de streaming')
    p_serve.add_argument('--port', type=int, default=8080, help='Port')
    p_serve.add_argument('--dir', default='./segments', help='Dossier des segments')
    
    args = parser.parse_args()
    
    if args.command == 'segment':
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📥 Extraction des frames : {args.input}")
        frames, fps, total = extract_frames(args.input, args.max_frames, args.target_size)
        print(f"   {len(frames)} frames extraites ({fps:.1f} fps)")
        
        print(f"🗜️ Segmentation (GOP={args.gop_size})...")
        segments = segment_video(frames, fps, args.gop_size, args.skip, args.dict)
        
        print(f"💾 Sauvegarde des segments...")
        for i, seg in enumerate(segments):
            path = output_dir / f"segment_{i:04d}.hcv2"
            with open(path, 'wb') as f:
                f.write(seg['data'])
        
        print(f"📋 Génération du manifest...")
        manifest = generate_manifest(segments, output_dir, fps)
        
        total = sum(s['size'] for s in segments)
        raw = sum(f.nbytes for f in frames)
        print(f"\n✅ Segmentation terminée")
        print(f"   {len(segments)} segments, {total//1024} Ko total")
        print(f"   Ratio moyen : {raw/total:.1f}×")
        print(f"   Manifest : {manifest}")
        print(f"   Pour lire : python hcv2_stream.py serve --dir {output_dir}")
    
    elif args.command == 'manifest':
        input_dir = Path(args.input)
        segments = sorted(input_dir.glob("segment_*.hcv2"))
        if not segments:
            sys.exit("Aucun segment trouvé")
        
        seg_infos = []
        for s in segments:
            with open(s, 'rb') as f:
                hdr = f.read(12)
            h = struct.unpack('<I', hdr[0:4])[0]
            w = struct.unpack('<I', hdr[4:8])[0]
            size = s.stat().st_size
            seg_infos.append({'path': s.name, 'size': size, 'h': h, 'w': w})
        
        manifest = Path(args.output)
        with open(manifest, 'w') as f:
            f.write("#EXTM3U\n#EXT-X-VERSION:7\n")
            f.write(f"#EXT-X-TARGETDURATION:2\n#EXT-X-MEDIA-SEQUENCE:0\n#EXT-X-PLAYLIST-TYPE:VOD\n\n")
            for s in seg_infos:
                f.write(f"#EXTINF:2.000,\n{s['path']}\n")
            f.write("#EXT-X-ENDLIST\n")
        
        print(f"✅ Manifest créé : {manifest}")
        print(f"   {len(seg_infos)} segments, {sum(s['size'] for s in seg_infos)//1024} Ko total")
    
    elif args.command == 'serve':
        serve_directory(args.port, args.dir)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()