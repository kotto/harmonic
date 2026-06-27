"""
Décodeur SDI - Convertit les fichiers SDI en vidéo et images
"""

import struct
import numpy as np
from PIL import Image
import io
import base64
import cv2
import os
import zlib
from typing import Dict, Any, Tuple, Optional


class SDIDecoder:
    """Décodeur pour les fichiers vidéo SDI"""
    
    def __init__(self):
        self.header = None
        self.frame_index = []
        self.frames_data = []
        
    def read_sdi_file(self, filepath: str) -> Dict[str, Any]:
        """Lit un fichier SDI et extrait les métadonnées"""
        try:
            with open(filepath, 'rb') as f:
                # Lecture du magic number
                magic = f.read(4)
                if magic != b'SDI1':
                    return {'success': False, 'error': 'Format SDI invalide'}
                
                # Lecture de l'en-tête
                width, height, fps_millis, bit_depth = struct.unpack('<HHHH', f.read(8))
                
                # Stockage des métadonnées
                self.header = {
                    'width': width,
                    'height': height,
                    'fps': fps_millis / 1000.0,
                    'bit_depth': bit_depth
                }
                
                # Calcul du nombre de frames
                file_size = os.path.getsize(filepath)
                index_start = 8
                frame_count = (file_size - index_start) // 8
                
                # Lecture de l'index des frames
                f.seek(index_start)
                self.frame_index = []
                for i in range(min(frame_count, 1000)):  # Limite à 1000 frames
                    try:
                        offset = struct.unpack('<Q', f.read(8))[0]
                        self.frame_index.append(offset)
                    except:
                        break
                
                # Lecture des données des frames
                self.frames_data = []
                for i in range(len(self.frame_index)):
                    f.seek(self.frame_index[i])
                    if i < len(self.frame_index) - 1:
                        frame_size = self.frame_index[i + 1] - self.frame_index[i]
                    else:
                        current_pos = f.tell()
                        f.seek(0, 2)
                        file_size = f.tell()
                        frame_size = file_size - current_pos
                        f.seek(current_pos)
                    
                    frame_data = f.read(frame_size)
                    self.frames_data.append(frame_data)
                
                return {
                    'success': True,
                    'header': self.header
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def decompress_frame(self, frame_data: bytes, frame_index: int = 0) -> Optional[np.ndarray]:
        """Décompresse une frame SDI en image numpy"""
        try:
            width = self.header['width']
            height = self.header['height']
            
            # Structure des données compressées:
            # - Analyse patterns (4 bytes)
            # - Données spatiales compressées
            # - Données temporelles
            
            if len(frame_data) < 4:
                return None
            
            # Lecture de l'analyse de patterns
            pattern_analysis = struct.unpack('<I', frame_data[:4])[0]
            
            # Extraction des données spatiales
            spatial_data = frame_data[4:4 + width * height * 3 // 4]
            
            # Extraction des données temporelles
            temporal_data = frame_data[4 + width * height * 3 // 4:]
            
            # Reconstruction de la frame
            # Création d'une image YUV de base
            yuv_frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Décodage des données spatiales
            if len(spatial_data) > 0:
                spatial_values = np.frombuffer(spatial_data[:min(len(spatial_data), width*height)], dtype=np.uint8)
                if len(spatial_values) > 0:
                    yuv_frame[:, :, 0] = np.resize(spatial_values, (height, width))
            
            # Application des données temporelles
            if len(temporal_data) > 0:
                temporal_values = np.frombuffer(temporal_data[:min(len(temporal_data), width*height)], dtype=np.uint8)
                if len(temporal_values) > 0:
                    temporal_matrix = np.resize(temporal_values, (height, width))
                    yuv_frame[:, :, 0] = np.clip(
                        yuv_frame[:, :, 0].astype(np.int16) + temporal_matrix.astype(np.int16) - 128,
                        0, 255
                    ).astype(np.uint8)
            
            # Remplissage des canaux U et V (chrominance)
            yuv_frame[:, :, 1] = 128
            yuv_frame[:, :, 2] = 128
            
            return yuv_frame
            
        except Exception as e:
            print(f"Erreur décompression frame {frame_index}: {e}")
            return None
    
    def yuv_to_rgb(self, yuv_frame: np.ndarray) -> np.ndarray:
        """Convertit une frame YUV en RGB"""
        try:
            # Conversion YUV -> BGR (OpenCV)
            bgr_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR)
            # Conversion BGR -> RGB
            rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            return rgb_frame
        except Exception as e:
            print(f"Erreur conversion YUV->RGB: {e}")
            return yuv_frame
    
    def get_first_frame_image(self, filepath: str) -> Dict[str, Any]:
        """Extrait et retourne la première frame en tant qu'image"""
        try:
            # Lecture du fichier
            read_result = self.read_sdi_file(filepath)
            if not read_result['success']:
                return read_result
            
            if len(self.frames_data) == 0:
                return {'success': False, 'error': 'Aucune frame trouvée'}
            
            # Essayer de lire la première frame compressée à la fin du fichier
            try:
                with open(filepath, 'rb') as f:
                    f.seek(0, 2)  # Aller à la fin
                    file_size = f.tell()
                    
                    # Lire les 4 derniers bytes pour voir la taille de la frame compressée
                    f.seek(file_size - 4)
                    first_frame_compressed_size = struct.unpack('<I', f.read(4))[0]
                    
                    # Vérifier que la taille est raisonnable
                    if first_frame_compressed_size > 0 and first_frame_compressed_size < file_size - 100:
                        # Lire la frame compressée
                        f.seek(file_size - first_frame_compressed_size - 4)
                        first_frame_compressed_data = f.read(first_frame_compressed_size)
                        
                        # Décompresser avec zlib
                        first_frame_bytes = zlib.decompress(first_frame_compressed_data)
                        # Décoder l'image PNG
                        nparr = np.frombuffer(first_frame_bytes, np.uint8)
                        rgb_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        # Conversion en base64
                        buffer = io.BytesIO()
                        pil_image = Image.fromarray(cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2RGB))
                        pil_image.save(buffer, format='PNG')
                        image_bytes = buffer.getvalue()
                        base64_string = base64.b64encode(image_bytes).decode('utf-8')
                        
                        return {
                            'success': True,
                            'image_data': f'data:image/png;base64,{base64_string}',
                            'width': self.header['width'],
                            'height': self.header['height'],
                            'frame_number': 0,
                            'total_frames': len(self.frames_data),
                            'fps': self.header['fps'],
                            'bit_depth': self.header['bit_depth']
                        }
            except Exception as e:
                print(f"Zlib decompression error: {e}")
            
            # Fallback: Décompression de la première frame
            yuv_frame = self.decompress_frame(self.frames_data[0], 0)
            if yuv_frame is None:
                return {'success': False, 'error': 'Erreur de décompression'}
            
            # Conversion en RGB
            rgb_frame = self.yuv_to_rgb(yuv_frame)
            
            # Conversion en image PIL
            pil_image = Image.fromarray(rgb_frame)
            
            # Conversion en base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            return {
                'success': True,
                'image_data': f'data:image/png;base64,{base64_string}',
                'width': self.header['width'],
                'height': self.header['height'],
                'frame_number': 0,
                'total_frames': len(self.frames_data),
                'fps': self.header['fps'],
                'bit_depth': self.header['bit_depth']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def decompress_to_mp4(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """Décompresse un fichier SDI en vidéo MP4"""
        try:
            # Lecture du fichier
            read_result = self.read_sdi_file(input_path)
            if not read_result['success']:
                return read_result
            
            width = self.header['width']
            height = self.header['height']
            fps = self.header['fps']
            
            # Création du writer vidéo
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Décompression de chaque frame
            for i, frame_data in enumerate(self.frames_data):
                yuv_frame = self.decompress_frame(frame_data, i)
                if yuv_frame is not None:
                    rgb_frame = self.yuv_to_rgb(yuv_frame)
                    # Conversion RGB -> BGR pour OpenCV
                    bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
                    out.write(bgr_frame)
            
            out.release()
            
            return {
                'success': True,
                'output_path': output_path,
                'frame_count': len(self.frames_data),
                'fps': fps,
                'width': width,
                'height': height
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_video_info(self, filepath: str) -> Dict[str, Any]:
        """Retourne les informations sur la vidéo SDI"""
        try:
            read_result = self.read_sdi_file(filepath)
            if not read_result['success']:
                return read_result
            
            return {
                'success': True,
                'info': {
                    'format': 'SDI Pure',
                    'width': self.header['width'],
                    'height': self.header['height'],
                    'frame_count': len(self.frames_data),
                    'fps': self.header['fps'],
                    'duration': len(self.frames_data) / self.header['fps'] if self.header['fps'] > 0 else 0,
                    'bit_depth': self.header['bit_depth'],
                    'file_size': os.path.getsize(filepath)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Test du décodeur
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sdi_decoder.py <fichier.sdi-vid>")
        sys.exit(1)
    
    decoder = SDIDecoder()
    
    # Test lecture
    filepath = sys.argv[1]
    print(f"Lecture du fichier: {filepath}")
    
    # Informations vidéo
    info_result = decoder.get_video_info(filepath)
    if info_result['success']:
        print("\nInformations vidéo:")
        for key, value in info_result['info'].items():
            print(f"  {key}: {value}")
    
    # Extraction première frame
    frame_result = decoder.get_first_frame_image(filepath)
    if frame_result['success']:
        print(f"\nPremière frame extraite: {frame_result['width']}x{frame_result['height']}")
        # Sauvegarde de l'image
        image_data = base64.b64decode(frame_result['image_data'].split(',')[1])
        with open('first_frame_sdi.png', 'wb') as f:
            f.write(image_data)
        print("Image sauvegardée: first_frame_sdi.png")
    else:
        print(f"Erreur: {frame_result['error']}")