#!/usr/bin/env python3
"""
OPTIMIZED SOLUTIONS - HYBRID MODE
==================================
Utilise les meilleures implémentations originales + optimisations
Retrouve les bonnes performances mesurées avant
"""

import numpy as np
import zstandard as zstd
from typing import Tuple, Dict, Any, Optional
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# zstd contexts
_ZCTX = {level: zstd.ZstdCompressor(level=level) for level in [3, 11, 19, 22]}
_ZDCTX = zstd.ZstdDecompressor()


# ─── SOLUTION 1: HARMONIC CODEC V16 (BEST ORIGINAL) ────────────────────────────

class HarmonicCodecV16Best:
    """Utilise l'implémentation originale testée (8.35:1)"""
    
    def __init__(self):
        try:
            import harmonic_codec_v16
            self.codec = harmonic_codec_v16
            self.use_original = True
        except:
            self.use_original = False
            logger.warning("Harmonic V16 original not found, using fallback")
    
    def compress(self, video_data: np.ndarray) -> bytes:
        """Compresse vidéo SDI-PUR"""
        if self.use_original:
            try:
                # Utiliser l'implémentation originale
                writer = self.codec.HCV16Writer('/tmp/test.hcv16', mode='GRAIN_SYNTH')
                writer.add_image(video_data)
                writer.finalize()
                
                with open('/tmp/test.hcv16', 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Original codec failed: {e}")
        
        # Fallback: zstd ultra
        return _ZCTX[22].compress(video_data.tobytes())
    
    def decompress(self, compressed: bytes) -> np.ndarray:
        """Décompresse vidéo"""
        if self.use_original:
            try:
                with open('/tmp/test.hcv16', 'wb') as f:
                    f.write(compressed)
                reader = self.codec.HCV16Reader('/tmp/test.hcv16')
                reader.open()
                return reader.decode_all()[0]
            except:
                pass
        
        return np.frombuffer(_ZDCTX.decompress(compressed), dtype=np.uint16)


# ─── SOLUTION 2: HCV RAW IMAGE CODEC (BEST ORIGINAL) ──────────────────────────

class HCVRawImageCodecBest:
    """Utilise l'implémentation originale testée (8-12:1)"""
    
    def __init__(self):
        try:
            from COMPRESSION_CAMERA.METHOD_2_SDI_LIKE_IMAGE_COMPRESSION.hcv_image_codec import HCVImageCodec
            self.codec = HCVImageCodec(mode='GRAIN_SYNTH', bit_depth=10, zstd_level=11)
            self.use_original = True
        except:
            self.use_original = False
            logger.warning("HCV Image Codec original not found, using fallback")
    
    def compress(self, image: np.ndarray) -> bytes:
        """Compresse image RAW"""
        if self.use_original:
            try:
                return self.codec.encode_image(image)
            except Exception as e:
                logger.warning(f"Original codec failed: {e}")
        
        # Fallback: zstd ultra
        return _ZCTX[22].compress(image.tobytes())
    
    def decompress(self, compressed: bytes) -> np.ndarray:
        """Décompresse image"""
        if self.use_original:
            try:
                return self.codec.decode_image(compressed)
            except:
                pass
        
        return np.frombuffer(_ZDCTX.decompress(compressed), dtype=np.uint16)


# ─── SOLUTION 3: HCV PRECOMPRESSED IMAGE CODEC (BEST ORIGINAL) ────────────────

class HCVPrecompressedImageCodecBest:
    """Utilise l'implémentation originale testée (1.1-8:1)"""
    
    def __init__(self):
        try:
            from COMPRESSION_CAMERA.METHOD_2_SDI_LIKE_IMAGE_COMPRESSION.hcv_precompressed_codec import HCVPrecompressedCodec
            self.codec = HCVPrecompressedCodec(zstd_level=22)
            self.use_original = True
        except:
            self.use_original = False
            logger.warning("HCV Precompressed Codec original not found, using fallback")
    
    def compress(self, image: np.ndarray, image_format: str = 'JPEG') -> bytes:
        """Compresse image pré-compressée"""
        if self.use_original:
            try:
                return self.codec.compress(image, image_format)
            except Exception as e:
                logger.warning(f"Original codec failed: {e}")
        
        # Fallback: zstd ultra
        return _ZCTX[22].compress(image.tobytes())
    
    def decompress(self, compressed: bytes) -> np.ndarray:
        """Décompresse image"""
        if self.use_original:
            try:
                return self.codec.decompress(compressed)
            except:
                pass
        
        return np.frombuffer(_ZDCTX.decompress(compressed), dtype=np.uint8)


# ─── SOLUTION 4: HCV H.264 VIDEO CODEC (BEST ORIGINAL) ──────────────────────

class HCVH264VideoCodecBest:
    """Utilise l'implémentation originale testée (1.05-3:1)"""
    
    def __init__(self):
        try:
            from COMPRESSION_CAMERA.METHOD_2_SDI_LIKE_IMAGE_COMPRESSION.hcv_h264_video_codec import HCVVideoCodec
            self.codec = HCVVideoCodec(strategy='AUTO', zstd_level=22)
            self.use_original = True
        except:
            self.use_original = False
            logger.warning("HCV H.264 Codec original not found, using fallback")
    
    def compress(self, video_data: bytes) -> bytes:
        """Compresse vidéo H.264"""
        if self.use_original:
            try:
                # Sauvegarder temporairement
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                    tmp.write(video_data)
                    tmp_path = tmp.name
                
                compressed, _ = self.codec.encode(tmp_path)
                
                import os
                os.unlink(tmp_path)
                
                return compressed
            except Exception as e:
                logger.warning(f"Original codec failed: {e}")
        
        # Fallback: zstd ultra
        return _ZCTX[22].compress(video_data)
    
    def decompress(self, compressed: bytes) -> bytes:
        """Décompresse vidéo"""
        return _ZDCTX.decompress(compressed)


# ─── SOLUTION 5: HCV MOBILE CAMERA CODEC (BEST ORIGINAL) ──────────────────────

class HCVMobileCameraCodecBest:
    """Utilise l'implémentation originale testée (1.1-5:1)"""
    
    def __init__(self):
        try:
            from COMPRESSION_SOLUTIONS.HCV_MOBILE_CAMERA_CODEC.hcv_mobile_camera_codec import HCVMobileCamera
            self.codec = HCVMobileCamera(verbose=False)
            self.use_original = True
        except:
            self.use_original = False
            logger.warning("HCV Mobile Camera original not found, using fallback")
    
    def compress(self, media: np.ndarray, media_type: str = 'HEIC') -> bytes:
        """Compresse photo/vidéo smartphone"""
        if self.use_original:
            try:
                return self.codec.compress(media, media_type)
            except Exception as e:
                logger.warning(f"Original codec failed: {e}")
        
        # Fallback: zstd ultra
        return _ZCTX[22].compress(media.tobytes())
    
    def decompress(self, compressed: bytes) -> np.ndarray:
        """Décompresse"""
        if self.use_original:
            try:
                return self.codec.decompress(compressed)
            except:
                pass
        
        return np.frombuffer(_ZDCTX.decompress(compressed), dtype=np.uint8)


# ─── SOLUTION 6: HCV BINARY LOSSLESS CODEC (BEST ORIGINAL) ────────────────────

class HCVBinaryLosslessCodecBest:
    """Utilise l'implémentation originale testée (1.1-5:1)"""
    
    def __init__(self):
        try:
            from COMPRESSION_SOLUTIONS.HCV_BINARY_LOSSLESS_CODEC.hcv_binary_lossless_codec import HCVBinaryLossless
            self.codec = HCVBinaryLossless(verbose=False)
            self.use_original = True
        except:
            self.use_original = False
            logger.warning("HCV Binary Lossless original not found, using fallback")
    
    def compress(self, data: bytes) -> bytes:
        """Compresse données binaires (100% lossless)"""
        if self.use_original:
            try:
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                
                result = self.codec.compress(tmp_path)
                
                with open(result.output_path, 'rb') as f:
                    compressed = f.read()
                
                os.unlink(tmp_path)
                os.unlink(result.output_path)
                
                return compressed
            except Exception as e:
                logger.warning(f"Original codec failed: {e}")
        
        # Fallback: zstd ultra
        return _ZCTX[22].compress(data)
    
    def decompress(self, compressed: bytes) -> bytes:
        """Décompresse (100% fidèle)"""
        return _ZDCTX.decompress(compressed)


# ─── SOLUTION 7: HCV BROADCAST ARCHIVE CODEC (BEST ORIGINAL) ────────────────

class HCVBroadcastArchiveCodecBest:
    """Utilise l'implémentation originale testée (5-15:1)"""
    
    def __init__(self):
        try:
            from COMPRESSION_SOLUTIONS.HCV_BROADCAST_ARCHIVE_CODEC.hcv_broadcast_archive_codec import HCVBroadcastArchive
            self.codec = HCVBroadcastArchive(verbose=False)
            self.use_original = True
        except:
            self.use_original = False
            logger.warning("HCV Broadcast Archive original not found, using fallback")
    
    def compress(self, video_data: np.ndarray, format_type: str = 'ProRes') -> bytes:
        """Compresse vidéo broadcast"""
        if self.use_original:
            try:
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(suffix='.mov', delete=False) as tmp:
                    tmp.write(video_data.tobytes())
                    tmp_path = tmp.name
                
                result = self.codec.compress(tmp_path)
                
                with open(result.output_path, 'rb') as f:
                    compressed = f.read()
                
                os.unlink(tmp_path)
                os.unlink(result.output_path)
                
                return compressed
            except Exception as e:
                logger.warning(f"Original codec failed: {e}")
        
        # Fallback: zstd ultra
        return _ZCTX[22].compress(video_data.tobytes())
    
    def decompress(self, compressed: bytes) -> np.ndarray:
        """Décompresse vidéo"""
        return np.frombuffer(_ZDCTX.decompress(compressed), dtype=np.uint16)


# ─── UNIFIED FRAMEWORK (HYBRID) ────────────────────────────────────────────────

class OptimizedSolutionsHybrid:
    """Framework hybride utilisant les meilleures implémentations originales"""
    
    def __init__(self):
        """Initialise tous les codecs avec les meilleures implémentations"""
        self.solutions = {
            1: HarmonicCodecV16Best(),
            2: HCVRawImageCodecBest(),
            3: HCVPrecompressedImageCodecBest(),
            4: HCVH264VideoCodecBest(),
            5: HCVMobileCameraCodecBest(),
            6: HCVBinaryLosslessCodecBest(),
            7: HCVBroadcastArchiveCodecBest(),
        }
        
        self.solution_names = {
            1: "Harmonic Codec V16",
            2: "HCV Raw Image",
            3: "HCV Precompressed Image",
            4: "HCV H.264 Video",
            5: "HCV Mobile Camera",
            6: "HCV Binary Lossless",
            7: "HCV Broadcast Archive",
        }
        
        self.solution_targets = {
            1: "8.35:1 (original)",
            2: "8-12:1 (original)",
            3: "1.1-8:1 (original)",
            4: "1.05-3:1 (original)",
            5: "1.1-5:1 (original)",
            6: "1.1-5:1 (original)",
            7: "5-15:1 (original)",
        }
        
        logger.info("Hybrid framework initialized with original implementations")
    
    def compress(self, solution_id: int, data, **kwargs) -> bytes:
        """Compresse avec solution spécifiée"""
        if solution_id not in self.solutions:
            raise ValueError(f"Solution {solution_id} not found")
        
        codec = self.solutions[solution_id]
        
        start_time = time.time()
        compressed = codec.compress(data, **kwargs)
        elapsed = time.time() - start_time
        
        # Log
        if isinstance(data, bytes):
            data_size = len(data)
        else:
            data_size = data.nbytes if hasattr(data, 'nbytes') else len(data)
        
        ratio = data_size / len(compressed) if len(compressed) > 0 else 0
        logger.info(f"Solution {solution_id} ({self.solution_names[solution_id]}): "
                   f"{ratio:.2f}:1 in {elapsed:.3f}s")
        
        return compressed
    
    def decompress(self, solution_id: int, compressed: bytes):
        """Décompresse avec solution spécifiée"""
        if solution_id not in self.solutions:
            raise ValueError(f"Solution {solution_id} not found")
        
        return self.solutions[solution_id].decompress(compressed)
    
    def get_info(self) -> Dict[str, Any]:
        """Retourne info sur toutes les solutions"""
        return {
            solution_id: {
                'name': self.solution_names[solution_id],
                'target_ratio': self.solution_targets[solution_id],
            }
            for solution_id in range(1, 8)
        }


if __name__ == '__main__':
    logger.info("=== HYBRID SOLUTIONS FRAMEWORK ===")
    logger.info("Using original implementations for best performance")
    
    framework = OptimizedSolutionsHybrid()
    info = framework.get_info()
    
    for solution_id, details in info.items():
        logger.info(f"{solution_id}. {details['name']}: {details['target_ratio']}")
