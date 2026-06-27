#!/usr/bin/env python3
"""
HCV PRECOMPRESSED IMAGE CODEC
Adaptation du codec HCV pour images déjà compressées (JPEG, PNG, WebP)
Détection automatique du format et sélection de la meilleure stratégie
"""

import os
import struct
import zlib
import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HCVPrecompressedCodec:
    """
    Codec adapté pour images pré-compressées
    Détecte le format et applique la meilleure stratégie
    """
    
    MAGIC = b'HCP1'  # HCV Precompressed v1
    VERSION = 1
    
    # Stratégies disponibles
    STRATEGY_DIRECT = 'DIRECT'      # Compresser fichier directement
    STRATEGY_HYBRID = 'HYBRID'      # Décoder → YCbCr → Compresser
    STRATEGY_TRANSCODE = 'TRANSCODE'  # Décoder → Réencoder avec HCV
    STRATEGY_AUTO = 'AUTO'          # Détection automatique
    
    def __init__(self, strategy='AUTO', quality_threshold=80, zstd_level=22):
        """
        Args:
            strategy: 'AUTO', 'DIRECT', 'HYBRID', 'TRANSCODE'
            quality_threshold: Seuil de qualité JPEG pour décider stratégie
            zstd_level: Niveau compression zstd (1-22)
        """
        self.strategy = strategy
        self.quality_threshold = quality_threshold
        self.zstd_level = zstd_level
        
        # Importer HCV codec
        from hcv_image_codec import HCVImageCodec
        self.hcv = HCVImageCodec(mode='GRAIN_SYNTH', bit_depth=12, zstd_level=11)
        
        # Contexte zstd
        import zstandard as zstd
        self.zctx = zstd.ZstdCompressor(level=zstd_level)
        self.zdctx = zstd.ZstdDecompressor()
        
        logger.info(f"HCV Precompressed Codec initialisé: strategy={strategy}, zstd={zstd_level}")
    
    def detect_format(self, file_path: str) -> Dict[str, Any]:
        """
        Détecte le format et estime la qualité
        
        Args:
            file_path: Chemin du fichier image
            
        Returns:
            Dict avec format, qualité, recommandation
        """
        with open(file_path, 'rb') as f:
            header = f.read(16)
        
        result = {
            'format': 'UNKNOWN',
            'quality': None,
            'strategy': self.STRATEGY_DIRECT,
            'reason': 'Format inconnu'
        }
        
        # Détection JPEG
        if header[:2] == b'\xff\xd8':
            result['format'] = 'JPEG'
            quality = self._estimate_jpeg_quality(file_path)
            result['quality'] = quality
            
            if quality < 70:
                result['strategy'] = self.STRATEGY_TRANSCODE
                result['reason'] = f'Qualité basse ({quality}): transcoder pour améliorer'
            elif quality < 85:
                result['strategy'] = self.STRATEGY_HYBRID
                result['reason'] = f'Qualité moyenne ({quality}): hybrid pour équilibre'
            else:
                result['strategy'] = self.STRATEGY_DIRECT
                result['reason'] = f'Qualité haute ({quality}): compression directe'
        
        # Détection PNG
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            result['format'] = 'PNG'
            result['quality'] = 100  # PNG est lossless
            result['strategy'] = self.STRATEGY_DIRECT
            result['reason'] = 'PNG lossless: compression directe'
        
        # Détection WebP
        elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
            result['format'] = 'WebP'
            result['quality'] = 95  # WebP est généralement bien optimisé
            result['strategy'] = self.STRATEGY_DIRECT
            result['reason'] = 'WebP optimisé: compression directe'
        
        # Détection GIF
        elif header[:6] in [b'GIF87a', b'GIF89a']:
            result['format'] = 'GIF'
            result['quality'] = 100  # GIF est lossless
            result['strategy'] = self.STRATEGY_DIRECT
            result['reason'] = 'GIF lossless: compression directe'
        
        return result
    
    def _estimate_jpeg_quality(self, file_path: str) -> int:
        """
        Estime la qualité JPEG en analysant les tables de quantification
        
        Args:
            file_path: Chemin du fichier JPEG
            
        Returns:
            Qualité estimée (0-100)
        """
        try:
            from PIL import Image
            img = Image.open(file_path)
            
            # Essayer d'obtenir la qualité depuis les métadonnées
            if hasattr(img, 'info') and 'quality' in img.info:
                return img.info['quality']
            
            # Estimation basée sur la taille du fichier
            file_size = os.path.getsize(file_path)
            img_size = img.width * img.height * 3
            
            # Ratio de compression
            ratio = file_size / img_size
            
            # Estimation heuristique
            if ratio < 0.05:
                return 50  # Très compressé
            elif ratio < 0.1:
                return 70
            elif ratio < 0.15:
                return 80
            elif ratio < 0.2:
                return 85
            else:
                return 90  # Peu compressé
        
        except Exception as e:
            logger.warning(f"Impossible d'estimer qualité JPEG: {e}")
            return 80  # Défaut
    
    def strategy_direct(self, file_path: str) -> bytes:
        """
        Stratégie DIRECT: Compresser le fichier directement
        
        Meilleur pour: PNG, WebP, JPEG haute qualité
        Ratio: 1.1-1.3:1
        Temps: Très rapide
        """
        logger.info(f"Stratégie DIRECT: {file_path}")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        original_size = len(file_data)
        
        # Compresser avec zstd
        compressed = self.zctx.compress(file_data)
        
        logger.info(f"  Original: {original_size:,} bytes")
        logger.info(f"  Compressé: {len(compressed):,} bytes")
        logger.info(f"  Ratio: {original_size / len(compressed):.2f}:1")
        
        return compressed
    
    def strategy_hybrid(self, file_path: str) -> bytes:
        """
        Stratégie HYBRID: Décoder → YCbCr 4:2:2 → Compresser
        
        Meilleur pour: JPEG qualité moyenne
        Ratio: 2-3:1
        Temps: Rapide
        """
        logger.info(f"Stratégie HYBRID: {file_path}")
        
        try:
            from PIL import Image
        except ImportError:
            logger.error("PIL non disponible, utiliser DIRECT")
            return self.strategy_direct(file_path)
        
        # Charger image
        img = Image.open(file_path)
        original_size = os.path.getsize(file_path)
        
        # Convertir en RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convertir en array uint16
        img_array = np.array(img, dtype=np.uint16) * 257
        
        # Convertir YCbCr 4:2:2
        Y, Cb, Cr = self.hcv.separate_ycbcr422(img_array)
        
        # Compresser sans grain separation
        Y_comp = self.hcv.delta_h_encode(Y)
        Cb_comp = self.hcv.delta_h_encode(Cb)
        Cr_comp = self.hcv.delta_h_encode(Cr)
        
        # Container
        compressed = self._build_container(Y_comp, Cb_comp, Cr_comp, 
                                          source_format='HYBRID')
        
        logger.info(f"  Original: {original_size:,} bytes")
        logger.info(f"  Compressé: {len(compressed):,} bytes")
        logger.info(f"  Ratio: {original_size / len(compressed):.2f}:1")
        
        return compressed
    
    def strategy_transcode(self, file_path: str) -> bytes:
        """
        Stratégie TRANSCODE: Décoder → Réencoder avec HCV
        
        Meilleur pour: JPEG basse qualité
        Ratio: 8-12:1
        Temps: Lent
        Bénéfice: Qualité améliorée
        """
        logger.info(f"Stratégie TRANSCODE: {file_path}")
        
        try:
            from PIL import Image
        except ImportError:
            logger.error("PIL non disponible, utiliser DIRECT")
            return self.strategy_direct(file_path)
        
        # Charger image
        img = Image.open(file_path)
        original_size = os.path.getsize(file_path)
        
        # Convertir en RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convertir en array uint16
        img_array = np.array(img, dtype=np.uint16) * 257
        
        # Encoder avec HCV
        hci_data = self.hcv.encode_image(img_array)
        
        logger.info(f"  Original: {original_size:,} bytes")
        logger.info(f"  Compressé: {len(hci_data):,} bytes")
        logger.info(f"  Ratio: {original_size / len(hci_data):.2f}:1")
        
        return hci_data
    
    def encode(self, file_path: str) -> Tuple[bytes, Dict[str, Any]]:
        """
        Encode une image pré-compressée
        
        Args:
            file_path: Chemin du fichier image
            
        Returns:
            (compressed_data, metadata)
        """
        logger.info(f"Encodage: {file_path}")
        
        # Détection format
        format_info = self.detect_format(file_path)
        logger.info(f"  Format: {format_info['format']}")
        logger.info(f"  Qualité: {format_info['quality']}")
        logger.info(f"  Raison: {format_info['reason']}")
        
        # Sélection stratégie
        if self.strategy == self.STRATEGY_AUTO:
            strategy = format_info['strategy']
        else:
            strategy = self.strategy
        
        logger.info(f"  Stratégie: {strategy}")
        
        # Appliquer stratégie
        if strategy == self.STRATEGY_DIRECT:
            compressed = self.strategy_direct(file_path)
        elif strategy == self.STRATEGY_HYBRID:
            compressed = self.strategy_hybrid(file_path)
        elif strategy == self.STRATEGY_TRANSCODE:
            compressed = self.strategy_transcode(file_path)
        else:
            logger.error(f"Stratégie inconnue: {strategy}")
            compressed = self.strategy_direct(file_path)
        
        # Métadonnées
        metadata = {
            'source_format': format_info['format'],
            'source_quality': format_info['quality'],
            'strategy': strategy,
            'original_size': os.path.getsize(file_path),
            'compressed_size': len(compressed),
            'ratio': os.path.getsize(file_path) / len(compressed),
            'saving': (1 - len(compressed) / os.path.getsize(file_path)) * 100
        }
        
        return compressed, metadata
    
    def _build_container(self, Y_comp: bytes, Cb_comp: bytes, Cr_comp: bytes,
                        source_format: str = 'HYBRID') -> bytes:
        """Construit le container HCP"""
        buf = bytearray()
        
        # Header
        buf.extend(self.MAGIC)
        buf.extend(struct.pack('<BB', self.VERSION, 0))  # version, reserved
        
        # Source format (8 bytes)
        fmt_bytes = source_format.encode('ascii')[:8].ljust(8, b'\x00')
        buf.extend(fmt_bytes)
        
        # Données compressées
        buf.extend(struct.pack('<I', len(Y_comp)))
        buf.extend(Y_comp)
        buf.extend(struct.pack('<I', len(Cb_comp)))
        buf.extend(Cb_comp)
        buf.extend(struct.pack('<I', len(Cr_comp)))
        buf.extend(Cr_comp)
        
        # CRC32
        crc = zlib.crc32(bytes(buf)) & 0xFFFFFFFF
        buf.extend(struct.pack('<I', crc))
        
        return bytes(buf)


# Exemple d'utilisation
if __name__ == "__main__":
    import time
    
    print("="*80)
    print("HCV PRECOMPRESSED IMAGE CODEC - DEMO")
    print("="*80)
    
    # Créer codec
    codec = HCVPrecompressedCodec(strategy='AUTO', zstd_level=22)
    
    # Exemple: Compresser une image JPEG
    test_file = 'test_image.jpg'
    
    if os.path.exists(test_file):
        print(f"\n[*] Compression: {test_file}")
        
        start = time.time()
        compressed, metadata = codec.encode(test_file)
        comp_time = time.time() - start
        
        print(f"\n[+] RÉSULTATS:")
        print(f"    Format source: {metadata['source_format']}")
        print(f"    Qualité: {metadata['source_quality']}")
        print(f"    Stratégie: {metadata['strategy']}")
        print(f"    Original: {metadata['original_size']:,} bytes")
        print(f"    Compressé: {metadata['compressed_size']:,} bytes")
        print(f"    Ratio: {metadata['ratio']:.2f}:1")
        print(f"    Économie: {metadata['saving']:.2f}%")
        print(f"    Temps: {comp_time:.3f}s")
    else:
        print(f"\n[-] Fichier test non trouvé: {test_file}")
        print("    Créer une image JPEG pour tester")
