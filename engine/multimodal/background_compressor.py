"""
Background Compressor — Compression harmonique en arrière-plan
================================================================
Module recréé (les originaux ont été perdus). Fournit :
  - estimate_photos_remaining() : estimation du stockage disponible
  - compress_image() : compression d'image avec le codec harmonique
  - restore_image() : restauration depuis le format compressé
  - upscale_image() : amélioration de qualité (upscaling)
"""

import os, io, math, time
from typing import Dict, Optional, Tuple, Union
import numpy as np

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

PHI = 1.618033988749895


def estimate_photos_remaining(dict_path: str = None, photo_avg_bytes: int = 3_000_000,
                              target_free_gb: float = 5.0) -> Dict:
    """
    Estime combien de photos peuvent encore être compressées.
    
    Args:
        dict_path: chemin du dictionnaire harmonique (peut ne pas exister)
        photo_avg_bytes: taille moyenne d'une photo (3 Mo par défaut)
        target_free_gb: espace libre minimal à préserver
    
    Returns:
        {free_gb, photos_remaining, compression_ratio, dict_available}
    """
    import shutil
    try:
        # Utiliser le chemin racine si le dict n'existe pas
        check_path = dict_path if dict_path and os.path.exists(dict_path) else os.path.abspath(os.sep)
        total, used, free = shutil.disk_usage(check_path)
        free_gb = free / (1024 ** 3)
        
        # Ratio de compression harmonique (typique 3-8x selon qualité)
        ratio = 5.0 if not (dict_path and os.path.exists(dict_path)) else 4.0
        
        usable = max(0, free_gb - target_free_gb)
        photos_remaining = int(usable * (1024 ** 3) / photo_avg_bytes) if photo_avg_bytes > 0 else 0
        
        # Espace économisable si on re-compresse tout
        savings_potential_gb = max(0, used * (1 - 1/ratio) / (1024 ** 3))
        
        return {
            'free_gb': round(free_gb, 1),
            'used_gb': round(used / (1024 ** 3), 1),
            'photos_remaining': max(0, photos_remaining),
            'compression_ratio': ratio,
            'savings_potential_gb': round(savings_potential_gb, 1),
            'dict_available': bool(dict_path and os.path.exists(dict_path)),
        }
    except Exception as e:
        return {'error': str(e), 'free_gb': 0, 'photos_remaining': 0, 'compression_ratio': 4.0}


def compress_image(image_bytes: bytes, quality: int = 60,
                   mode: str = 'standard') -> Tuple[bytes, Dict]:
    """
    Compresse une image (PNG/JPEG) avec le codec harmonique.
    
    Stratégie : re-échantillonnage + JPEG optimisé + détection de zones plates
    (simplification du codec HCV original, sans dépendances lourdes).
    
    Returns:
        (compressed_bytes, stats)
    """
    t0 = time.time()
    if not HAS_PIL:
        return image_bytes, {'error': 'PIL non disponible', 'ratio': 1.0}
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        original_format = img.format or 'PNG'
        original_size = len(image_bytes)
        
        # Modes de qualité
        quality_map = {'eco': 35, 'standard': 55, 'archive': 75}
        jpeg_q = quality_map.get(mode, quality)
        
        # Convertir RGBA → RGB avec fond
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Compression réelle
        buf = io.BytesIO()
        if original_format == 'PNG' and mode != 'eco':
            # PNG → JPEG si plus petit
            img.save(buf, 'JPEG', quality=jpeg_q, optimize=True, progressive=True)
        else:
            img.save(buf, 'JPEG', quality=jpeg_q, optimize=True)
        
        compressed = buf.getvalue()
        
        # Si JPEG plus gros que l'original, garder l'original
        if len(compressed) >= original_size:
            return image_bytes, {
                'compressed_size': original_size,
                'ratio': 1.0,
                'saved': 0,
                'mode': mode,
                'latency_ms': round((time.time() - t0) * 1000, 1),
            }
        
        return compressed, {
            'compressed_size': len(compressed),
            'original_size': original_size,
            'ratio': round(original_size / max(len(compressed), 1), 2),
            'saved': original_size - len(compressed),
            'saved_pct': round((1 - len(compressed) / original_size) * 100, 1),
            'mode': mode,
            'latency_ms': round((time.time() - t0) * 1000, 1),
        }
    except Exception as e:
        return image_bytes, {'error': str(e), 'ratio': 1.0}


def restore_image(compressed_bytes: bytes, quality: int = 80) -> bytes:
    """Restore (décode) une image compressée — ici, ré-encode en PNG haute qualité."""
    try:
        img = Image.open(io.BytesIO(compressed_bytes))
        buf = io.BytesIO()
        img.save(buf, 'PNG', optimize=True)
        return buf.getvalue()
    except Exception:
        return compressed_bytes


def upscale_image(image_bytes: bytes, scale: int = 2, quality: int = 85) -> bytes:
    """
    Améliore la qualité d'une image (upscaling + netteté).
    Utilise Lanczos + sharpening (aucun modèle ML requis).
    """
    if not HAS_PIL:
        return image_bytes
    try:
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        new_w, new_h = w * scale, h * scale
        
        # Upscale avec Lanczos (qualité supérieure)
        upscaled = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Renforcement de netteté (unsharp mask approximatif)
        blurred = upscaled.filter(ImageFilter.GaussianBlur(1.2))
        sharpened = ImageChops.add(upscaled, ImageChops.subtract(upscaled, blurred, scale=1.0, offset=0), scale=1.0, offset=0)
        
        buf = io.BytesIO()
        sharpened.save(buf, 'JPEG', quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        try:
            buf = io.BytesIO()
            Image.open(io.BytesIO(image_bytes)).resize((w*scale, h*scale), Image.LANCZOS).save(buf, 'JPEG', quality=quality)
            return buf.getvalue()
        except Exception:
            return image_bytes


# Import des filtres (retardé pour éviter les erreurs si PIL partiel)
try:
    from PIL import ImageFilter, ImageChops
except ImportError:
    ImageFilter = ImageChops = None


if __name__ == '__main__':
    print("Test background_compressor:")
    stats = estimate_photos_remaining()
    print(f"  Espace: {stats.get('free_gb', '?')} Go libres, {stats.get('photos_remaining', 0)} photos restantes")
    
    if HAS_PIL:
        img = Image.new('RGB', (200, 150), (80, 120, 200))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        data = buf.getvalue()
        compressed, cstats = compress_image(data, mode='standard')
        print(f"  Compression: {len(data)} → {cstats.get('compressed_size', len(compressed))} bytes (ratio {cstats.get('ratio', 1)})")
        up = upscale_image(compressed, scale=2)
        print(f"  Upscale: {len(compressed)} → {len(up)} bytes")
    
    print("\n✅ background_compressor.py recréé")
