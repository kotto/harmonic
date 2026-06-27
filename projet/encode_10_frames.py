#!/usr/bin/env python3
"""
Script pour encoder exactement 10 frames de B3.mp4
"""

import numpy as np
import cv2
from harmonic_codec_v16 import HCV16Writer
import time
import os

def encode_10_frames():
    print("🎬 ENCODAGE 10 FRAMES HCV16")
    print("=" * 40)
    
    source_video = "B3.mp4"
    output_file = "B3_10frames.hcv16"
    max_frames = 10
    
    # Vérification du fichier source
    if not os.path.exists(source_video):
        print(f"❌ Fichier source non trouvé: {source_video}")
        return None
    
    source_size_mb = os.path.getsize(source_video) / (1024 * 1024)
    print(f"📁 Source: {source_video} ({source_size_mb:.2f} MB)")
    print(f"🎯 Objectif: {max_frames} frames")
    print()
    
    try:
        # Chargement des frames
        print(f"📹 Chargement de {max_frames} frames...")
        cap = cv2.VideoCapture(source_video)
        
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo: {source_video}")
        
        # Informations vidéo
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"   Résolution source: {width}×{height}")
        print(f"   FPS: {fps:.2f}")
        print(f"   Frames totales disponibles: {total_frames}")
        print(f"   Format: {'Horizontal' if width > height else 'Vertical'}")
        print()
        
        # Chargement des 10 premières frames
        frames = []
        for i in range(max_frames):
            ret, frame = cap.read()
            if not ret:
                print(f"⚠️  Seulement {i} frames disponibles")
                break
                
            # Conversion BGR -> RGB et 8bit -> 12bit
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_12bit = (frame_rgb.astype(np.uint16) << 4)  # 8bit -> 12bit
            frames.append(frame_12bit)
        
        cap.release()
        print(f"✅ {len(frames)} frames chargées")
        print()
        
        # Paramètres d'encodage optimisés
        params = {
            'path': output_file,
            'mode': 'LOSSLESS',  # Mode lossless pour comparaison exacte
            'bit_depth': 12,
            'width': width,
            'height': height,
            'fps': (int(fps), 1),
            'colorspace': 'BGR',
            'ref_interval': 60,  # I-frame tous les 60 frames (au lieu de 30)
            'seq_id': 42
        }
        
        print(f"📊 Paramètres d'encodage:")
        print(f"   Mode: {params['mode']}")
        print(f"   Résolution: {params['width']}×{params['height']}")
        print(f"   Frames à encoder: {len(frames)}")
        print(f"   I-frame: frame 0 seulement")
        print(f"   P-frames: frames 1-{len(frames)-1}")
        print()
        
        # Encodage
        print("🔧 Début encodage...")
        start_time = time.time()
        
        writer = HCV16Writer(**params)
        for i, frame in enumerate(frames):
            writer.add_frame(frame, i)
            print(f"   Frame {i+1}/{len(frames)} encodée")
        
        file_size = writer.finalize()
        
        end_time = time.time()
        encoding_time = end_time - start_time
        
        print()
        print("✅ ENCODAGE TERMINÉ")
        print("=" * 40)
        print(f"📁 Fichier: {output_file}")
        print(f"📊 Taille: {file_size / (1024*1024):.2f} MB")
        print(f"⏱️  Temps: {encoding_time:.2f}s")
        print()
        
        # Comparaison avec les anciens résultats
        print(f"📈 COMPARAISON:")
        print(f"   5 frames (ancien): 3.37 MB")
        print(f"   {len(frames)} frames (nouveau): {file_size / (1024*1024):.2f} MB")
        
        if len(frames) > 5:
            ratio_growth = (file_size / (1024*1024)) / 3.37
            expected_linear = len(frames) / 5 * 3.37
            print(f"   Croissance réelle: {ratio_growth:.2f}x")
            print(f"   Croissance linéaire attendue: {expected_linear:.2f} MB")
            
            if file_size / (1024*1024) < expected_linear * 0.8:
                print(f"   🎉 Excellente compression inter-frame !")
            elif file_size / (1024*1024) < expected_linear:
                print(f"   ✅ Bonne compression inter-frame")
            else:
                print(f"   ⚠️  Compression inter-frame limitée")
        
        # Calcul du ratio de compression
        estimated_raw_size = len(frames) * width * height * 3 * 2 / (1024*1024)  # 16-bit RGB
        compression_ratio = estimated_raw_size / (file_size / (1024*1024))
        
        print()
        print(f"📊 RATIO DE COMPRESSION:")
        print(f"   RAW estimé: {estimated_raw_size:.0f} MB")
        print(f"   HCV16: {file_size / (1024*1024):.2f} MB")
        print(f"   Ratio: {compression_ratio:.1f}x")
        
        return file_size
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    result = encode_10_frames()
    if result:
        print(f"\n🎯 Fichier créé avec succès !")
        print(f"   Vous pouvez maintenant tester avec ce fichier réaliste.")