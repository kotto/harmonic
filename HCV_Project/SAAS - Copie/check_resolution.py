#!/usr/bin/env python3
"""
Script pour vérifier la résolution des fichiers HCV16
"""

from harmonic_codec_v16 import HCV16Reader

def check_resolution(filename):
    print(f"📁 Analyse de {filename}")
    try:
        import struct
        
        with open(filename, 'rb') as f:
            # Lire le header HCV16 complet
            magic = f.read(4)
            if magic != b'HCV6':
                print(f"   ❌ Pas un fichier HCV16 valide")
                return None, None, None
            
            # Format header: '<BBBBIIIIIIHH'
            header_data = f.read(struct.calcsize('<BBBBIIIIIIHH'))
            (version, mode, colorspace, bit_depth,
             width, height, n_frames,
             fps_num, fps_den, seq_id, n_streams, _) = struct.unpack('<BBBBIIIIIIHH', header_data)
        
        print(f"   Résolution: {width}×{height}")
        print(f"   Frames: {n_frames}")
        print(f"   Bit depth: {bit_depth}")
        print(f"   Mode: {mode}")
        print(f"   Format: {'Horizontal' if width > height else 'Vertical' if height > width else 'Carré'}")
        print(f"   Ratio: {width/height:.2f}")
        
        # Impact sur Delta-H
        pixels_per_line = width
        if pixels_per_line < 1000:
            print(f"   ⚠️  Lignes courtes ({pixels_per_line}px) → Delta-H moins efficace")
        elif pixels_per_line > 1500:
            print(f"   ✅ Lignes longues ({pixels_per_line}px) → Delta-H efficace")
        else:
            print(f"   📊 Lignes moyennes ({pixels_per_line}px) → Delta-H standard")
            
        return width, height, n_frames
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None, None, None

if __name__ == "__main__":
    print("🔍 VÉRIFICATION RÉSOLUTION HCV16")
    print("=" * 40)
    
    files = ['b3.hcv16', 'e02yeaTm.hcv16']
    
    for filename in files:
        try:
            w, h, f = check_resolution(filename)
            print()
        except FileNotFoundError:
            print(f"   ❌ Fichier non trouvé: {filename}")
            print()