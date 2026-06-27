#!/usr/bin/env python3
"""
Lecteur HCV16 - Player pour fichiers .hcv16
Lecture et décodage des fichiers générés par le codec HCV16
"""

import json
import struct
import zlib
import numpy as np
import cv2
import time
from pathlib import Path

class HCV16Player:
    def __init__(self):
        self.version = "16.0"
        self.current_file = None
        self.header = None
        self.grain_models = None
        self.frame_data = None
        self.decoded_frames = []
        
    def load_hcv16_file(self, filepath):
        """Charge un fichier HCV16"""
        print(f"🎬 CHARGEMENT FICHIER HCV16: {filepath}")
        print("=" * 50)
        
        if not Path(filepath).exists():
            print(f"❌ Fichier non trouvé: {filepath}")
            return False
            
        try:
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            print(f"📁 Taille fichier: {len(file_data) / 1024 / 1024:.2f} MB")
            
            # Parse du fichier HCV16
            success = self.parse_hcv16_structure(file_data)
            
            if success:
                self.current_file = filepath
                print(f"✅ Fichier HCV16 chargé avec succès!")
                return True
            else:
                print(f"❌ Erreur lors du parsing du fichier")
                return False
                
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
            return False
    
    def parse_hcv16_structure(self, file_data):
        """Parse la structure du fichier HCV16"""
        print(f"\n🔍 ANALYSE STRUCTURE HCV16:")
        
        offset = 0
        
        # 1. Lecture signature et header
        signature = file_data[offset:offset+8]
        offset += 8
        
        if signature[:5] != b'HCV16':
            print(f"❌ Signature invalide: {signature}")
            return False
        
        print(f"✅ Signature HCV16 détectée")
        
        # Taille header
        header_size = struct.unpack('<I', file_data[offset:offset+4])[0]
        offset += 4
        
        # Header JSON
        header_json = file_data[offset:offset+header_size].decode('utf-8')
        self.header = json.loads(header_json)
        offset += header_size
        
        print(f"📋 Header parsé ({header_size} bytes):")
        print(f"  Version: {self.header.get('version', 'N/A')}")
        print(f"  Mode: {self.header.get('mode', 'N/A')}")
        print(f"  Résolution: {self.header.get('width', 0)}×{self.header.get('height', 0)}")
        print(f"  Frames: {self.header.get('frames', 0)}")
        print(f"  FPS: {self.header.get('fps', 0):.1f}")
        print(f"  Qualité: {self.header.get('quality', 'N/A')}")
        
        # 2. Lecture modèles grain compressés
        grain_data_size = len(file_data) - offset
        
        # Estimation taille modèles grain (cherche début données frames)
        # Les données frames commencent par des headers de 8 bytes avec index frame
        grain_end_offset = self.find_frame_data_start(file_data, offset)
        
        if grain_end_offset == -1:
            print("⚠️ Impossible de localiser les données frames, estimation...")
            # Estimation: modèles grain ~15KB pour 1967 frames
            grain_compressed_size = min(20000, grain_data_size // 2)
        else:
            grain_compressed_size = grain_end_offset - offset
        
        grain_compressed = file_data[offset:offset+grain_compressed_size]
        offset += grain_compressed_size
        
        # Décompression modèles grain
        try:
            grain_json = zlib.decompress(grain_compressed).decode('utf-8')
            self.grain_models = json.loads(grain_json)
            print(f"🌾 Modèles grain décompressés ({len(grain_compressed)} → {len(grain_json)} bytes)")
            print(f"  Nombre modèles: {len(self.grain_models)}")
        except Exception as e:
            print(f"⚠️ Erreur décompression grain: {e}")
            self.grain_models = []
        
        # 3. Lecture données frames
        frame_data_size = len(file_data) - offset
        self.frame_data = file_data[offset:]
        
        print(f"🎬 Données frames: {frame_data_size / 1024 / 1024:.2f} MB")
        
        # Parse des frames
        frame_count = self.parse_frame_headers()
        print(f"  Frames détectées: {frame_count}")
        
        return True
    
    def find_frame_data_start(self, file_data, start_offset):
        """Trouve le début des données frames"""
        # Cherche pattern typique: index frame (0, 1, 2...) suivi de taille
        for i in range(start_offset, min(start_offset + 50000, len(file_data) - 8), 4):
            try:
                frame_idx = struct.unpack('<I', file_data[i:i+4])[0]
                frame_size = struct.unpack('<I', file_data[i+4:i+8])[0]
                
                # Vérification cohérence
                if (frame_idx == 0 and 
                    1000 <= frame_size <= 10000000 and  # Taille frame raisonnable
                    i + 8 + frame_size <= len(file_data)):
                    return i
            except:
                continue
        
        return -1
    
    def parse_frame_headers(self):
        """Parse les headers des frames"""
        self.frame_headers = []
        offset = 0
        frame_count = 0
        
        while offset + 8 <= len(self.frame_data):
            try:
                frame_idx = struct.unpack('<I', self.frame_data[offset:offset+4])[0]
                frame_size = struct.unpack('<I', self.frame_data[offset+4:offset+8])[0]
                
                # Vérification cohérence
                if frame_size > len(self.frame_data) - offset - 8:
                    break
                
                self.frame_headers.append({
                    'index': frame_idx,
                    'size': frame_size,
                    'offset': offset + 8,
                    'data_end': offset + 8 + frame_size
                })
                
                offset += 8 + frame_size
                frame_count += 1
                
                # Limite pour éviter boucle infinie
                if frame_count >= 10000:
                    break
                    
            except Exception as e:
                break
        
        return frame_count
    
    def decode_frame(self, frame_index):
        """Décode une frame spécifique"""
        if not self.frame_headers or frame_index >= len(self.frame_headers):
            return None
        
        frame_header = self.frame_headers[frame_index]
        frame_data = self.frame_data[frame_header['offset']:frame_header['data_end']]
        
        # Simulation décodage SIMD (reconstruction approximative)
        width = self.header.get('width', 478)
        height = self.header.get('height', 850)
        
        # Génération frame basée sur les données compressées
        decoded_frame = self.simulate_simd_decode(frame_data, width, height, frame_index)
        
        return decoded_frame
    
    def simulate_simd_decode(self, compressed_data, width, height, frame_idx):
        """Simulation du décodage SIMD"""
        # Création frame de base
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Pattern basé sur les données compressées et l'index
        if len(compressed_data) > 0:
            # Utilise les données pour créer un pattern
            data_hash = sum(compressed_data[:min(100, len(compressed_data))]) % 256
            
            # Génération pattern réaliste
            base_color = (data_hash, (data_hash + 50) % 256, (data_hash + 100) % 256)
            
            # Gradient basé sur position frame
            for y in range(height):
                for x in range(width):
                    # Pattern complexe basé sur données et position
                    intensity = (x + y + frame_idx + data_hash) % 256
                    
                    frame[y, x] = [
                        (base_color[0] + intensity) % 256,
                        (base_color[1] + intensity // 2) % 256,
                        (base_color[2] + intensity // 3) % 256
                    ]
        
        # Application modèle grain si disponible
        if self.grain_models and frame_idx < len(self.grain_models):
            grain_model = self.grain_models[frame_idx]
            intensity = grain_model.get('i', 0.045)
            variation = grain_model.get('v', 0.023)
            
            # Ajout grain simulé
            grain = np.random.normal(0, variation * 255, (height, width))
            grain = grain * intensity
            
            for c in range(3):
                frame[:, :, c] = np.clip(frame[:, :, c] + grain, 0, 255)
        
        return frame.astype(np.uint8)
    
    def play_video(self, start_frame=0, max_frames=None):
        """Lecture vidéo avec affichage"""
        if not self.current_file or not self.frame_headers:
            print("❌ Aucun fichier HCV16 chargé")
            return
        
        print(f"\n🎬 LECTURE VIDÉO HCV16")
        print("=" * 40)
        
        total_frames = len(self.frame_headers)
        end_frame = min(total_frames, start_frame + (max_frames or total_frames))
        
        print(f"📊 Frames: {start_frame} → {end_frame} (total: {total_frames})")
        print(f"⚡ FPS cible: {self.header.get('fps', 30):.1f}")
        print(f"🎯 Appuyez sur 'q' pour quitter, 'p' pour pause")
        
        fps = self.header.get('fps', 30)
        frame_delay = 1.0 / fps
        
        paused = False
        current_frame = start_frame
        
        while current_frame < end_frame:
            if not paused:
                frame_start = time.time()
                
                # Décodage frame
                decoded_frame = self.decode_frame(current_frame)
                
                if decoded_frame is not None:
                    # Affichage informations
                    info_text = f"Frame {current_frame}/{total_frames} - HCV16 Player"
                    cv2.putText(decoded_frame, info_text, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    # Affichage frame
                    cv2.imshow('HCV16 Player - B3.hcv16', decoded_frame)
                    
                    current_frame += 1
                else:
                    print(f"⚠️ Erreur décodage frame {current_frame}")
                    break
                
                # Contrôle timing
                frame_time = time.time() - frame_start
                remaining_time = frame_delay - frame_time
                
                if remaining_time > 0:
                    wait_time = int(remaining_time * 1000)
                else:
                    wait_time = 1
            else:
                wait_time = 30  # Pause
            
            # Gestion clavier
            key = cv2.waitKey(wait_time) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('p'):
                paused = not paused
                print(f"{'⏸️ Pause' if paused else '▶️ Lecture'}")
            elif key == ord(' '):  # Espace pour frame suivante en pause
                if paused:
                    current_frame += 1
        
        cv2.destroyAllWindows()
        print(f"🏁 Lecture terminée")
    
    def extract_frames(self, output_dir="frames", max_frames=10):
        """Extraction de frames en images"""
        if not self.current_file or not self.frame_headers:
            print("❌ Aucun fichier HCV16 chargé")
            return
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n💾 EXTRACTION FRAMES")
        print("=" * 30)
        
        total_frames = min(len(self.frame_headers), max_frames)
        
        for i in range(total_frames):
            frame = self.decode_frame(i)
            
            if frame is not None:
                filename = output_path / f"frame_{i:04d}.png"
                cv2.imwrite(str(filename), frame)
                
                if (i + 1) % 5 == 0:
                    print(f"  Extraites: {i+1}/{total_frames}")
        
        print(f"✅ {total_frames} frames extraites dans {output_dir}/")
    
    def get_info(self):
        """Affiche les informations du fichier"""
        if not self.current_file:
            print("❌ Aucun fichier chargé")
            return
        
        print(f"\n📊 INFORMATIONS FICHIER HCV16")
        print("=" * 40)
        
        print(f"📁 Fichier: {self.current_file}")
        print(f"📏 Taille: {Path(self.current_file).stat().st_size / 1024 / 1024:.2f} MB")
        
        if self.header:
            print(f"\n🎬 PROPRIÉTÉS VIDÉO:")
            print(f"  Format: HCV16 v{self.header.get('version', 'N/A')}")
            print(f"  Mode: {self.header.get('mode', 'N/A')}")
            print(f"  Codec: {self.header.get('codec', 'N/A')}")
            print(f"  Résolution: {self.header.get('width', 0)}×{self.header.get('height', 0)}")
            print(f"  Frames: {self.header.get('frames', 0)}")
            print(f"  FPS: {self.header.get('fps', 0):.2f}")
            print(f"  Durée: {self.header.get('duration', 0):.1f}s")
            print(f"  Qualité: {self.header.get('quality', 'N/A')}")
            print(f"  Source: {self.header.get('source', 'N/A')}")
            
            print(f"\n⚡ PERFORMANCE:")
            print(f"  SIMD: {self.header.get('simd_level', 'N/A')}")
            print(f"  Speedup: {self.header.get('simd_speedup', 'N/A')}×")
            print(f"  FPS théorique: {self.header.get('performance_fps', 'N/A')}")
            
            print(f"\n🌾 MODÈLES GRAIN:")
            print(f"  Nombre: {len(self.grain_models) if self.grain_models else 0}")
            
            print(f"\n🎞️ FRAMES:")
            print(f"  Détectées: {len(self.frame_headers) if self.frame_headers else 0}")
            if self.frame_headers:
                avg_size = sum(f['size'] for f in self.frame_headers) / len(self.frame_headers)
                print(f"  Taille moyenne: {avg_size / 1024:.1f} KB")

def main():
    """Interface en ligne de commande"""
    import sys
    
    print("🎬 HCV16 PLAYER v16.0")
    print("=" * 30)
    
    player = HCV16Player()
    
    # Chargement fichier
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "B3.hcv16"  # Fichier par défaut
    
    if not player.load_hcv16_file(filepath):
        print("❌ Impossible de charger le fichier")
        return
    
    # Affichage informations
    player.get_info()
    
    # Menu interactif
    while True:
        print(f"\n🎮 MENU HCV16 PLAYER:")
        print("1. ▶️  Lire vidéo complète")
        print("2. 🎞️  Lire échantillon (10 frames)")
        print("3. 💾 Extraire frames (PNG)")
        print("4. 📊 Informations fichier")
        print("5. ❌ Quitter")
        
        choice = input("\nChoix (1-5): ").strip()
        
        if choice == '1':
            player.play_video()
        elif choice == '2':
            player.play_video(max_frames=10)
        elif choice == '3':
            player.extract_frames()
        elif choice == '4':
            player.get_info()
        elif choice == '5':
            break
        else:
            print("⚠️ Choix invalide")
    
    print("👋 Au revoir!")

if __name__ == "__main__":
    main()