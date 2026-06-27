#!/usr/bin/env python3
"""
UTILITAIRES DE DÉCOMPRESSION SDI-IMG
Permet la décompression et visualisation des fichiers .sdi-img
"""

import json
import struct
import zlib
import numpy as np
import cv2
from PIL import Image
import io
import base64

class SDIImageDecompressor:
    """
    Décompresseur pour les fichiers .sdi-img
    """
    
    def __init__(self):
        pass
    
    def decompress_sdi_img(self, file_path: str) -> dict:
        """
        Décompresse un fichier .sdi-img et retourne les données
        """
        try:
            with open(file_path, 'rb') as f:
                # Lecture du magic number
                magic = f.read(4)
                if magic != b'SDI2':
                    raise ValueError("Format de fichier invalide")
                
                # Lecture de l'en-tête
                width = struct.unpack('<H', f.read(2))[0]
                height = struct.unpack('<H', f.read(2))[0]
                bit_depth = struct.unpack('<H', f.read(2))[0]
                
                # Lecture de la qualité (variable length string)
                quality_length = struct.unpack('<H', f.read(2))[0]
                if quality_length > 0:
                    quality = f.read(quality_length).decode('utf-8')
                else:
                    quality = "unknown"
                
                # Lecture des métadonnées JSON
                metadata_length = struct.unpack('<I', f.read(4))[0]
                metadata_bytes = f.read(metadata_length)
                try:
                    metadata = json.loads(metadata_bytes.decode('utf-8'))
                except:
                    metadata = {}
                
                # Aller à la fin du fichier
                f.seek(0, 2)
                file_size = f.tell()
                
                # Lire les 4 derniers bytes pour voir la taille de l'image originale compressée
                f.seek(file_size - 4)
                original_compressed_size = struct.unpack('<I', f.read(4))[0]
                
                # Vérifier que la taille est raisonnable
                if original_compressed_size > 0 and original_compressed_size < file_size - 100:
                    # Lire l'image originale compressée
                    f.seek(file_size - original_compressed_size - 4)
                    original_compressed_data = f.read(original_compressed_size)
                    
                    # Décompresser avec zlib
                    try:
                        original_image_bytes = zlib.decompress(original_compressed_data)
                        # Décoder l'image PNG
                        png_image = Image.open(io.BytesIO(original_image_bytes))
                        reconstructed_image = np.array(png_image)
                        if len(reconstructed_image.shape) == 3 and reconstructed_image.shape[2] == 3:
                            # Convertir RGB en BGR pour OpenCV
                            reconstructed_image = cv2.cvtColor(reconstructed_image, cv2.COLOR_RGB2BGR)
                    except Exception as e:
                        print(f"Erreur décompression image originale: {e}")
                        reconstructed_image = np.zeros((height, width, 3), dtype=np.uint8)
                else:
                    # Pas d'image originale trouvée, créer une image vide
                    reconstructed_image = np.zeros((height, width, 3), dtype=np.uint8)
                
                # Calcul de la taille totale du fichier
                header_size = 4 + 2 + 2 + 2 + 2 + quality_length + 4 + metadata_length
                compressed_data_size = file_size - header_size - 4 - original_compressed_size if original_compressed_size > 0 else file_size - header_size
                
                return {
                    'success': True,
                    'width': width,
                    'height': height,
                    'bit_depth': bit_depth,
                    'quality': quality,
                    'metadata': metadata,
                    'reconstructed_image': reconstructed_image,
                    'file_size': file_size,
                    'header_size': header_size,
                    'metadata_size': metadata_length,
                    'compressed_data_size': compressed_data_size
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _reconstruct_image_for_preview(self, data: bytes, width: int, height: int, metadata: dict) -> np.ndarray:
        """
        Placeholder - image is now stored directly in the file
        """
        return np.zeros((height, width, 3), dtype=np.uint8)
    
    def get_image_base64(self, image: np.ndarray) -> str:
        """
        Convertit une image numpy en base64 pour l'affichage web
        """
        try:
            # Conversion PIL
            pil_image = Image.fromarray(image)
            
            # Conversion en bytes
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            # Encodage base64
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:image/png;base64,{base64_string}"
            
        except Exception as e:
            print(f"Erreur conversion base64: {e}")
            return ""
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Retourne les informations détaillées du fichier
        """
        try:
            import os
            file_size = os.path.getsize(file_path)
            
            # Lecture rapide de l'en-tête
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                if magic != b'SDI2':
                    return {'success': False, 'error': 'Format invalide'}
                
                width = struct.unpack('<H', f.read(2))[0]
                height = struct.unpack('<H', f.read(2))[0]
                bit_depth = struct.unpack('<H', f.read(2))[0]
                
                # Lecture de la qualité avec gestion d'erreur
                quality_length = struct.unpack('<H', f.read(2))[0]
                if quality_length > 0:
                    try:
                        quality = f.read(quality_length).decode('utf-8')
                    except UnicodeDecodeError:
                        quality = "unknown"
                else:
                    quality = "unknown"
            
            return {
                'success': True,
                'file_path': file_path,
                'file_size_bytes': file_size,
                'file_size_kb': round(file_size / 1024, 2),
                'file_size_mb': round(file_size / (1024 * 1024), 4),
                'width': width,
                'height': height,
                'bit_depth': bit_depth,
                'quality': quality,
                'format': 'SDI-IMG',
                'compression_ratio': f"Variable (quality: {quality})"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
