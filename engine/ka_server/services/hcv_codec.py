"""
KA Server — Service HCV Codec (Compression Harmonique)
=======================================================
Support HCV WASM (navigateur) + Fallback serveur (Python/Cloud).
Architecture hybride : compression locale si possible, sinon serveur.
"""

import os
import logging
import base64
import io
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

log = logging.getLogger(__name__)

# État global
_HCV_WASM_READY = False
_HCV_SERVER_AVAILABLE = False
_HCV_ANDROID_CODEC = None
_HCV_UPSCALER = None
_HCV_PRO_CODEC = None
_HCV_WASM_MODULE = None


@dataclass
class CompressionResult:
    """Résultat de compression."""
    success: bool
    compressed_data: bytes = None
    compressed_size: int = 0
    original_size: int = 0
    ratio: float = 1.0
    saved_percent: float = 0.0
    quality: str = 'standard'  # 'archive', 'standard', 'eco'
    method: str = 'none'  # 'wasm', 'server', 'fallback'
    error: str = None


@dataclass
class UpscaleResult:
    """Résultat d'upscaling."""
    success: bool
    upscaled_data: bytes = None
    width: int = 0
    height: int = 0
    scale_factor: float = 1.0
    method: str = 'none'
    error: str = None


def init_hcv_codec() -> Dict[str, bool]:
    """
    Initialise les codecs HCV (WASM + serveur).
    Retourne dict de disponibilité.
    """
    global _HCV_WASM_READY, _HCV_SERVER_AVAILABLE
    global _HCV_ANDROID_CODEC, _HCV_UPSCALER, _HCV_PRO_CODEC, _HCV_WASM_MODULE
    
    results = {'wasm': False, 'server': False, 'android': False, 'upscaler': False, 'pro': False}
    
    # 1. Essayer codecs serveur (Python natif / .so)
    _try_load_server_codecs(results)
    
    # 2. WASM sera chargé côté client (navigateur) via hcv_wasm_loader.js
    # Ici on marque juste que le support WASM est prévu
    _HCV_WASM_READY = True  # Le module JS existe
    results['wasm'] = True
    
    _HCV_SERVER_AVAILABLE = any([results['android'], results['upscaler'], results['pro']])
    
    log.info(f"  📦 HCV Codec: WASM={results['wasm']}, Server={_HCV_SERVER_AVAILABLE} "
             f"(android={results['android']}, upscaler={results['upscaler']}, pro={results['pro']})")
    
    return results


def _try_load_server_codecs(results: dict):
    """Tente de charger les codecs Python natifs."""
    global _HCV_ANDROID_CODEC, _HCV_UPSCALER, _HCV_PRO_CODEC
    
    HCV_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'HCV-Compression-Engine'
    if not HCV_DIR.exists():
        # Fallback Render
        HCV_DIR = Path(__file__).resolve().parent.parent.parent / 'HCV-Compression-Engine'
    if not HCV_DIR.exists():
        for candidate in Path(__file__).resolve().parent.parent.parent.parent.glob('*HCV*'):
            if candidate.is_dir():
                HCV_DIR = candidate
                break
    
    if not HCV_DIR.exists():
        log.info("  📦 HCV-Compression-Engine non trouvé — mode WASM uniquement")
        return
    
    import importlib.util
    
    # Codec Android Boost
    android_path = HCV_DIR / 'codecs' / 'hcv_android_boost_codec.py'
    if android_path.exists():
        try:
            spec = importlib.util.spec_from_file_location('hcv_android_boost', str(android_path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _HCV_ANDROID_CODEC = mod.HCVAndroidBoostCodec
            results['android'] = True
            log.info("  📦 HCV Android Boost Codec chargé")
        except Exception as e:
            log.warning(f"  📦 HCV Android Boost: {e}")
    
    # Upscaler
    upscaler_path = HCV_DIR / 'mobile' / 'upscaler.py'
    if upscaler_path.exists():
        try:
            spec = importlib.util.spec_from_file_location('hcv_upscaler', str(upscaler_path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _HCV_UPSCALER = mod.HCVUpscaler
            results['upscaler'] = True
            log.info("  📦 HCV Upscaler chargé")
        except Exception as e:
            log.warning(f"  📦 HCV Upscaler: {e}")
    
    # Pro Codec
    pro_path = HCV_DIR / 'codecs' / 'hcv_pro_codec.py'
    if pro_path.exists():
        try:
            spec = importlib.util.spec_from_file_location('hcv_pro_codec', str(pro_path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _HCV_PRO_CODEC = mod.HCVProCodec
            results['pro'] = True
            log.info("  📦 HCV Pro Codec chargé")
        except Exception as e:
            log.warning(f"  📦 HCV Pro Codec: {e}")


# ── Compression ──────────────────────────────────────────────────────────────

def compress_image(image_data: bytes, quality: str = 'standard', 
                   method: str = 'auto') -> CompressionResult:
    """
    Compresse une image.
    
    Args:
        image_data: Données image brutes (bytes)
        quality: 'archive' (max compression), 'standard', 'eco' (min compression)
        method: 'auto' (WASM si navigateur, sinon serveur), 'wasm', 'server', 'fallback'
    
    Returns:
        CompressionResult
    """
    original_size = len(image_data)
    
    # Map quality → paramètre codec
    quality_map = {
        'archive': 90,   # Qualité haute, compression max
        'standard': 75,
        'eco': 50,       # Compression max, qualité acceptable
    }
    q_param = quality_map.get(quality, 75)
    
    # Méthode auto : serveur si dispo, sinon fallback
    if method == 'auto':
        method = 'server' if _HCV_SERVER_AVAILABLE else 'fallback'
    
    # 1. Codec serveur Android Boost (le plus performant)
    if method == 'server' and _HCV_ANDROID_CODEC:
        try:
            codec = _HCV_ANDROID_CODEC()
            # Le codec attend un chemin fichier, on utilise un buffer
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_in:
                tmp_in.write(image_data)
                tmp_in_path = tmp_in.name
            
            tmp_out_path = tmp_in_path.replace('.jpg', '_hcv.hcv')
            
            # Compresser
            result = codec.compress(tmp_in_path, tmp_out_path, quality=q_param)
            
            if result and os.path.exists(tmp_out_path):
                with open(tmp_out_path, 'rb') as f:
                    compressed = f.read()
                
                # Nettoyage
                try:
                    os.unlink(tmp_in_path)
                    os.unlink(tmp_out_path)
                except Exception:
                    pass
                
                compressed_size = len(compressed)
                ratio = original_size / compressed_size if compressed_size > 0 else 1.0
                saved = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                
                return CompressionResult(
                    success=True,
                    compressed_data=compressed,
                    compressed_size=compressed_size,
                    original_size=original_size,
                    ratio=ratio,
                    saved_percent=saved,
                    quality=quality,
                    method='server_android'
                )
        except Exception as e:
            log.warning(f"HCV Android compression failed: {e}")
    
    # 2. Codec Pro
    if method == 'server' and _HCV_PRO_CODEC:
        try:
            codec = _HCV_PRO_CODEC()
            # API similaire
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_in:
                tmp_in.write(image_data)
                tmp_in_path = tmp_in.name
            tmp_out_path = tmp_in_path.replace('.jpg', '_hcv.hcv')
            
            result = codec.compress(tmp_in_path, tmp_out_path, quality=q_param)
            
            if result and os.path.exists(tmp_out_path):
                with open(tmp_out_path, 'rb') as f:
                    compressed = f.read()
                try:
                    os.unlink(tmp_in_path)
                    os.unlink(tmp_out_path)
                except Exception:
                    pass
                
                compressed_size = len(compressed)
                ratio = original_size / compressed_size if compressed_size > 0 else 1.0
                saved = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                
                return CompressionResult(
                    success=True,
                    compressed_data=compressed,
                    compressed_size=compressed_size,
                    original_size=original_size,
                    ratio=ratio,
                    saved_percent=saved,
                    quality=quality,
                    method='server_pro'
                )
        except Exception as e:
            log.warning(f"HCV Pro compression failed: {e}")
    
    # 3. Fallback : compression JPEG standard (Pillow)
    return _fallback_compress(image_data, quality, original_size)


def _fallback_compress(image_data: bytes, quality: str, original_size: int) -> CompressionResult:
    """Fallback compression avec Pillow (JPEG standard)."""
    try:
        from PIL import Image
        import io
        
        quality_map = {'archive': 85, 'standard': 70, 'eco': 50}
        q = quality_map.get(quality, 70)
        
        img = Image.open(io.BytesIO(image_data))
        
        # Convertir en RGB si nécessaire (JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=q, optimize=True)
        compressed = output.getvalue()
        
        compressed_size = len(compressed)
        ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        saved = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        return CompressionResult(
            success=True,
            compressed_data=compressed,
            compressed_size=compressed_size,
            original_size=original_size,
            ratio=ratio,
            saved_percent=saved,
            quality=quality,
            method='fallback_pillow'
        )
    except Exception as e:
        log.error(f"Fallback compression failed: {e}")
        return CompressionResult(
            success=False,
            original_size=original_size,
            error=str(e),
            method='failed'
        )


# ── Upscaling ────────────────────────────────────────────────────────────────

def upscale_image(image_data: bytes, scale: float = 2.0) -> UpscaleResult:
    """
    Upscale une image (×2, ×4).
    Utilise HCV Upscaler si dispo, sinon Pillow LANCZOS.
    """
    try:
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(image_data))
        orig_w, orig_h = img.size
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        
        # 1. HCV Upscaler (reconstruction harmonique)
        if _HCV_UPSCALER:
            try:
                upscaler = _HCV_UPSCALER()
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_in:
                    tmp_in.write(image_data)
                    tmp_in_path = tmp_in.name
                tmp_out_path = tmp_in_path.replace('.jpg', f'_up{int(scale)}x.jpg')
                
                result = upscaler.upscale(tmp_in_path, tmp_out_path, scale=int(scale))
                
                if result and os.path.exists(tmp_out_path):
                    with open(tmp_out_path, 'rb') as f:
                        upscaled = f.read()
                    try:
                        os.unlink(tmp_in_path)
                        os.unlink(tmp_out_path)
                    except Exception:
                        pass
                    
                    return UpscaleResult(
                        success=True,
                        upscaled_data=upscaled,
                        width=new_w,
                        height=new_h,
                        scale_factor=scale,
                        method='hcv_upscaler'
                    )
            except Exception as e:
                log.warning(f"HCV Upscaler failed: {e}")
        
        # 2. Fallback Pillow LANCZOS (haute qualité)
        img_up = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        if img_up.mode in ('RGBA', 'LA', 'P'):
            img_up = img_up.convert('RGB')
        img_up.save(output, format='JPEG', quality=85, optimize=True)
        upscaled = output.getvalue()
        
        return UpscaleResult(
            success=True,
            upscaled_data=upscaled,
            width=new_w,
            height=new_h,
            scale_factor=scale,
            method='fallback_lanczos'
        )
        
    except Exception as e:
        log.error(f"Upscale failed: {e}")
        return UpscaleResult(
            success=False,
            error=str(e),
            method='failed'
        )


# ── Analyse stockage (pour dashboard) ────────────────────────────────────────

def analyze_storage(file_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Analyse un fichier pour estimer la compression HCV.
    Retourne métriques pour l'UI.
    """
    original_size = len(file_data)
    
    # Estimation basée sur type fichier
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Ratios HCV typiques observés
    hcv_ratios = {
        'jpg': 28, 'jpeg': 28, 'png': 35, 'webp': 30, 'heic': 40,
        'mp4': 37, 'mov': 35, 'avi': 30, 'mkv': 33,
        'pdf': 50, 'txt': 60, 'docx': 45,
    }
    
    ratio = hcv_ratios.get(ext, 25)  # Default conservatif
    estimated_compressed = original_size / ratio
    savings_pct = int((1 - 1/ratio) * 100)
    
    return {
        'original_size': original_size,
        'original_size_mb': round(original_size / 1e6, 1),
        'estimated_compressed_size': int(estimated_compressed),
        'estimated_compressed_mb': round(estimated_compressed / 1e6, 1),
        'estimated_ratio': ratio,
        'estimated_savings_percent': savings_pct,
        'format': ext.upper(),
        'hcv_available': _HCV_SERVER_AVAILABLE,
        'wasm_available': _HCV_WASM_READY,
    }


def get_hcv_status() -> Dict[str, Any]:
    """Retourne le statut des codecs HCV."""
    return {
        'wasm_ready': _HCV_WASM_READY,
        'server_available': _HCV_SERVER_AVAILABLE,
        'codecs': {
            'android_boost': _HCV_ANDROID_CODEC is not None,
            'upscaler': _HCV_UPSCALER is not None,
            'pro': _HCV_PRO_CODEC is not None,
        },
        'fallback': 'pillow_jpeg',
    }


# Initialisation paresseuse
def ensure_initialized():
    if not (_HCV_WASM_READY or _HCV_SERVER_AVAILABLE):
        init_hcv_codec()