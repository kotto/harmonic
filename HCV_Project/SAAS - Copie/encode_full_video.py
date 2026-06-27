#!/usr/bin/env python3
"""
Script pour encoder la vidéo complète (1700 frames) avec paramètres optimisés
Charge le fichier video.mp4 source de 11.31 MB
"""

import numpy as np
import cv2
from harmonic_codec_v16 import HCV16Writer
import time
import os

def load_video_frames(video_path, max_frames=None):
    """
    Charge les frames depuis un fichier vidéo MP4/AVI/MOV
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé: {video_path}")
    
    print(f"📹 Chargement vidéo: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Impossible d'ouvrir la vidéo: {video_path}")
    
    # Informations vidéo
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"   Résolution: {width}x{height}")
    print(f"   FPS: {fps:.2f}")
    print(f"   Frames totales: {total_frames}")
    
    if max_frames:
        frames_to_load = min(total_frames, max_frames)
        print(f"   Limitation: {frames_to_load} frames")
    else:
        frames_to_load = total_frames
    
    frames = []
    frame_count = 0
    
    while frame_count < frames_to_load:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Conversion BGR -> RGB et 8bit -> 16bit
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_16bit = (frame_rgb.astype(np.uint16) << 4)  # 8bit -> 12bit
        
        frames.append(frame_16bit)
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"   Chargé {frame_count}/{frames_to_load} frames...")
    
    cap.release()
    print(f"✅ {len(frames)} frames chargées")
    
    return frames, {
        'fps': fps,
        'width': width, 
        'height': height,
        'total_frames': total_frames
    }

def encode_full_video():
    print("🎬 ENCODAGE VIDÉO COMPLÈTE HCV16")
    print("=" * 50)
    
    # Chemins des fichiers
    source_video = "B3.mp4"  # Votre fichier source de 11.31 MB
    output_file = "B3_complete.hcv16"
    
    # Vérification du fichier source
    if not os.path.exists(source_video):
        print(f"❌ Fichier source non trouvé: {source_video}")
        print("   Placez votre fichier video.mp4 dans le répertoire courant")
        return None
    
    source_size_mb = os.path.getsize(source_video) / (1024 * 1024)
    print(f"📁 Source: {source_video} ({source_size_mb:.2f} MB)")
    print()
    
    try:
        # Chargement des frames
        start_load = time.time()
        frames, video_info = load_video_frames(source_video)
        load_time = time.time() - start_load
        print(f"⏱️  Temps de chargement: {load_time:.1f}s")
        print()
        
        # Paramètres optimisés basés sur la vidéo réelle
        params = {
            'path': output_file,
            'mode': 'LOSSLESS',  # Mode lossless pour comparaison exacte
            'bit_depth': 12,
            'width': video_info['width'],
            'height': video_info['height'],
            'fps': (int(video_info['fps']), 1),
            'colorspace': 'BGR',
            'ref_interval': 30,  # I-frame tous les 30 frames (optimisé)
            'seq_id': 42
        }
        
        print(f"📊 Paramètres d'encodage:")
        print(f"   Mode: {params['mode']}")
        print(f"   Résolution: {params['width']}x{params['height']}")
        print(f"   FPS: {params['fps'][0]}")
        print(f"   I-frames: tous les {params['ref_interval']} frames")
        print(f"   Frames totales: {len(frames)}")
        print()
        
        # Estimation I-frames vs P-frames
        i_frames = (len(frames) // params['ref_interval']) + 1
        p_frames = len(frames) - i_frames
        print(f"📈 Répartition:")
        print(f"   I-frames: {i_frames}")
        print(f"   P-frames: {p_frames}")
        print()
        
        # Encodage
        print("🔧 Début encodage HCV16...")
        start_encode = time.time()
        
        writer = HCV16Writer(**params)
        for i, frame in enumerate(frames):
            writer.add_frame(frame, i)
            
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_encode
                progress = (i + 1) / len(frames) * 100
                if i > 0:
                    eta = elapsed / (i + 1) * (len(frames) - i - 1)
                    fps_current = (i + 1) / elapsed
                    print(f"   Encodé {i + 1}/{len(frames)} frames ({progress:.1f}%) - {fps_current:.1f} fps - ETA: {eta:.0f}s")
        
        file_size = writer.finalize()
        
        end_time = time.time()
        total_time = end_time - start_encode
        
        print()
        print("✅ ENCODAGE TERMINÉ")
        print("=" * 50)
        print(f"📁 Fichier: {output_file}")
        print(f"📊 Taille: {file_size / (1024*1024):.2f} MB")
        print(f"⏱️  Temps total: {total_time:.1f}s")
        print(f"🚀 Vitesse moyenne: {len(frames)/total_time:.1f} fps")
        print()
        
        # Calcul du ratio de compression réel
        ratio = source_size_mb / (file_size / (1024*1024))
        reduction = (1 - (file_size / (1024*1024)) / source_size_mb) * 100
        
        print(f"📈 COMPRESSION RÉELLE:")
        print(f"   Source: {source_size_mb:.2f} MB")
        print(f"   HCV16: {file_size / (1024*1024):.2f} MB")
        print(f"   Ratio: {ratio:.2f}x")
        print(f"   Réduction: {reduction:.1f}%")
        print()
        
        # Comparaison avec les 5 frames
        print(f"📊 COMPARAISON:")
        print(f"   5 frames: 3.37 MB → ratio 3.36x")
        print(f"   {len(frames)} frames: {file_size / (1024*1024):.2f} MB → ratio {ratio:.2f}x")
        
        if ratio > 3.0:
            print(f"   🎉 Excellent ! Ratio supérieur à 3x maintenu")
        elif ratio > 2.0:
            print(f"   ✅ Bon ratio, dans la fourchette attendue")
        else:
            print(f"   ⚠️  Ratio plus faible que prévu, optimisations possibles")
        
        return file_size
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    encode_full_video()