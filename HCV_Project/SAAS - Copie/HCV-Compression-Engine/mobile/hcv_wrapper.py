"""
HCV PRO Decoder Python Wrapper
Phase 2 - Étape 1
Interface minimaliste pour la bibliothèque C
"""

import ctypes
import os
from pathlib import Path
from typing import Optional

_native_available = False
_hcv = None

_lib_path = Path(__file__).parent / "libhcvdecoder.so"

try:
    if _lib_path.exists():
        _hcv = ctypes.CDLL(str(_lib_path))
        _native_available = True
except Exception:
    _native_available = False

# Initialisation globale
_initialized = False

def hcv_init() -> None:
    """Initialise le décodeur HCV. Détecte automatiquement le niveau SIMD."""
    global _initialized
    if not _native_available:
        return
    _hcv.hcv_decoder_init.restype = ctypes.c_int
    _hcv.hcv_decode_frame.restype = ctypes.c_int
    _hcv.hcv_decoder_version.restype = ctypes.c_char_p
    _hcv.hcv_decoder_init()
    _initialized = True

def hcv_decode(compressed_data: bytes, width: int, height: int) -> Optional[bytearray]:
    """
    Décode un frame HCV compressé
    :param compressed_data: Données compressées
    :param width: Largeur de l'image
    :param height: Hauteur de l'image
    :return: Buffer pixels décodés ou None en cas d'erreur
    """
    if not _native_available:
        return None
        
    if not _initialized:
        hcv_init()
    
    output_size = width * height * 2  # uint16_t par pixel
    output = bytearray(output_size)
    
    res = _hcv.hcv_decode_frame(
        ctypes.c_char_p(compressed_data),
        ctypes.c_size_t(len(compressed_data)),
        ctypes.c_char_p(output),
        ctypes.c_int(width),
        ctypes.c_int(height)
    )
    
    return output if res == 0 else None

def hcv_version() -> str:
    """Retourne la version de la bibliothèque"""
    if not _native_available:
        return "LOGICIAL ONLY"
    return _hcv.hcv_decoder_version().decode('utf-8')

# Initialisation automatique à l'import
hcv_init()

if __name__ == "__main__":
    # Test rapide
    print(f"✅ HCV Decoder chargé")
    print(f"✅ Version: {hcv_version()}")
    
    # Test benchmark 12MP
    import time
    WIDTH = 4032
    HEIGHT = 3024
    
    test_data = b'\x90\x01' * (WIDTH * HEIGHT)
    
    start = time.time()
    for i in range(100):
        out = hcv_decode(test_data, WIDTH, HEIGHT)
    end = time.time()
    
    per_ms = ((end - start) * 1000) / 100
    print(f"\n✅ Benchmark 12MP: {per_ms:.2f} ms / frame")
    print(f"✅ FPS: {1000 / per_ms:.1f}")
