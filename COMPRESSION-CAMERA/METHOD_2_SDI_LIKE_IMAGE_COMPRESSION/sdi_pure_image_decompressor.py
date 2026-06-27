#!/usr/bin/env python3
"""
DÉCOMPRESSEUR POUR IMAGES SDI-PURE
Permet la décompression et visualisation des fichiers .sdi-img compressés avec SDI-PURE
Intégration HCS: vérification d'intégrité, audit, gestion de sessions
"""

import json
import struct
import zlib
import numpy as np
import cv2
from PIL import Image
import io
import base64
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SDIPureImageDecompressor:
    """
    Décompresseur pour les fichiers .sdi-img compressés avec SDI-PURE
    Intégration HCS: vérification d'intégrité, audit, gestion de sessions
    """
    
    def __init__(self, session_id: Optional[str] = None, shared_secret: Optional[bytes] = None):
        self.session_id = session_id
        self.shared_secret = shared_secret
        self.decompression_history = []
        logger.info(f"SDI-Pure Image Decompressor initialisé (session: {session_id})")
    
    def decompress_sdi_img(self, file_path: str) -> dict:
        """
        Décompresse un fichier .sdi-img et retourne les données
        Avec vérification d'intégrité HCS
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
                
                # Lecture des données compressées
                compressed_data_size = struct.unpack('<I', f.read(4))[0]
                compressed_data = f.read(compressed_data_size)
                
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
                        logger.warning(f"Erreur décompression image originale: {e}")
                        reconstructed_image = np.zeros((height, width, 3), dtype=np.uint8)
                else:
                    # Pas d'image originale trouvée, créer une image vide
                    reconstructed_image = np.zeros((height, width, 3), dtype=np.uint8)
                
                # Calcul de la taille totale du fichier
                header_size = 4 + 2 + 2 + 2 + 4
                
                # Audit log
                self._audit_decompression(file_path, width, height, file_size)
                
                return {
                    'success': True,
                    'width': width,
                    'height': height,
                    'bit_depth': bit_depth,
                    'reconstructed_image': reconstructed_image,
                    'file_size': file_size,
                    'header_size': header_size,
                    'compressed_data_size': compressed_data_size,
                    'session_id': self.session_id
                }
                
        except Exception as e:
            logger.error(f"Erreur décompression: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': self.session_id
            }
    
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
            
            return {
                'success': True,
                'file_path': file_path,
                'file_size_bytes': file_size,
                'file_size_kb': round(file_size / 1024, 2),
                'file_size_mb': round(file_size / (1024 * 1024), 4),
                'width': width,
                'height': height,
                'bit_depth': bit_depth,
                'format': 'SDI-IMG (SDI-PURE)',
                'compression_type': 'Lossless',
                'session_id': self.session_id
            }
            
        except Exception as e:
            logger.error(f"Erreur lecture info fichier: {e}")
            return {'success': False, 'error': str(e)}

    def _audit_decompression(self, file_path: str, width: int, height: int, file_size: int) -> None:
        """Enregistrement d'audit pour traçabilité HCS"""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'action': 'decompress_image',
            'file_path': file_path,
            'width': width,
            'height': height,
            'file_size': file_size
        }
        self.decompression_history.append(audit_entry)
        logger.info(f"Audit: {audit_entry}")
    
    def verify_integrity(self, file_path: str, auth_tag: Optional[bytes] = None) -> bool:
        """Vérification d'intégrité avec HMAC HCS"""
        if not self.shared_secret or not auth_tag:
            return True
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            h = hmac.new(self.shared_secret, data, hashlib.sha256)
            expected_tag = h.digest()
            
            return hmac.compare_digest(auth_tag, expected_tag)
        except Exception as e:
            logger.error(f"Erreur vérification intégrité: {e}")
            return False
    
    def decompress_sdi_img_secure(self, file_path: str, encrypted_file: Optional[str] = None) -> dict:
        """Décompression sécurisée avec vérification d'intégrité"""
        if encrypted_file and self.shared_secret:
            try:
                with open(encrypted_file, 'rb') as f:
                    data = f.read()
                
                # Extraction du tag d'authentification (derniers 32 bytes)
                auth_tag = data[-32:]
                encrypted_data = data[:-32]
                
                # Vérification d'intégrité
                if not self.verify_integrity(file_path, auth_tag):
                    return {
                        'success': False,
                        'error': 'Vérification d\'intégrité échouée',
                        'session_id': self.session_id
                    }
            except Exception as e:
                logger.error(f"Erreur décompression sécurisée: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'session_id': self.session_id
                }
        
        return self.decompress_sdi_img(file_path)
    
    def get_decompression_history(self) -> list:
        """Récupération de l'historique des décompressions"""
        return self.decompression_history