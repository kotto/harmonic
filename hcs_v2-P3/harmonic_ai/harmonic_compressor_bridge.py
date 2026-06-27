#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HarmonicCompressorBridge - Compression harmonique des images/videos generees
=============================================================================
Integre le HarmonicEncoder (core/harmonic_encoder.py) dans le pipeline de
generation Harmonic AI.

Avantage cle : les images generees par synthese harmonique sont IDEALES
pour la compression harmonique car leur contenu spectral est deja organise
en series harmoniques -> ratios de compression superieurs aux images naturelles.

Compression guidee par signature :
  - La signature 512D encode la complexite spectrale de l'image
  - -> Qualite ajustee automatiquement : image simple -> Q=60 (ratio 35:1)
  - -> Image complexe -> Q=85 (ratio 8:1 mais PSNR 38 dB)
  - La signature est embeddee dans le fichier .hce -> reconstruction sans BDD

Format .hce (Harmonic Codec Encoded) :
  - Pur NumPy/SciPy, zero dependance binaire
  - Ratios : Q=90 -> 6:1 | Q=75 -> 18:1 | Q=60 -> 35:1 | Q=50 -> 50:1
  - PSNR  : Q=90 -> 38dB | Q=75 -> 33dB  | Q=60 -> 27dB  | Q=50 -> 24dB

Pipeline complet :
  Prompt -> Generation -> Upscaling -> Compression HCE -> Fichier .hce
                                             |
                         La signature est embeddee dans le .hce
                         -> Decompression intelligente + re-ingestion BDD
"""

import os
import sys
import io
import time
import json
import struct
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Constantes
PHI = 1.6180339887
MAGIC_HCE_AI = b'HCEAI\x01'  # Extension du format HCE avec signature harmonique

# Niveaux de qualite predefinies
QUALITY_PRESETS = {
    "lossless":   {"quality": 98, "label": "quasi-lossless", "ratio_est": 2.0},
    "high":       {"quality": 85, "label": "haute qualite",   "ratio_est": 8.0},
    "balanced":   {"quality": 75, "label": "equilibre",       "ratio_est": 18.0},
    "efficient":  {"quality": 60, "label": "efficace",        "ratio_est": 35.0},
    "compact":    {"quality": 50, "label": "compact",         "ratio_est": 50.0},
    "archive":    {"quality": 35, "label": "archivage",       "ratio_est": 120.0},
}

# Qualite derivee depuis la complexite de la signature
# (image simple = moins de qualite necessaire = meilleur ratio)
SIGNATURE_QUALITY_MAP = [
    (0.00, 0.05,  55),   # Tres simple  -> Q=55 (~45:1)
    (0.05, 0.08,  65),   # Simple       -> Q=65 (~25:1)
    (0.08, 0.12,  75),   # Moyen        -> Q=75 (~18:1)
    (0.12, 0.18,  82),   # Complexe     -> Q=82 (~10:1)
    (0.18, 1.00,  88),   # Tres complexe-> Q=88 (~6:1)
]


class HarmonicCompressorBridge:
    """
    Bridge de compression harmonique pour les images/videos generees.

    Les images generees par synthese harmonique ont une structure spectrale
    tres reguliere -> les coefficients DCT se concentrent sur peu de
    frequences -> compression bien superieure aux images photographiques.

    Usage:
        bridge = HarmonicCompressorBridge()
        # Compression simple
        hce_bytes, meta = bridge.compress(image)
        # Compression guidee par signature
        hce_bytes, meta = bridge.compress_with_signature(image, signature)
        # Sauvegarde complete
        meta = bridge.save(image, "output.hce", signature=sig)
        # Chargement
        image, sig, info = bridge.load("output.hce")
    """

    def __init__(
        self,
        default_quality: float = 75.0,
        preset: Optional[str] = "balanced",
        auto_quality: bool = True,
    ):
        """
        Args:
            default_quality: qualite par defaut (1-100)
            preset: preset de qualite (priorite sur default_quality)
            auto_quality: ajuster la qualite automatiquement depuis la signature
        """
        # Charge le preset
        if preset and preset in QUALITY_PRESETS:
            self.default_quality = QUALITY_PRESETS[preset]["quality"]
        else:
            self.default_quality = float(default_quality)

        self.auto_quality = auto_quality
        self._encoder = None  # Charge a la demande

        # Charge le HarmonicEncoder
        self._load_encoder()

    def _load_encoder(self):
        """Charge l'encodeur depuis core/harmonic_encoder.py."""
        try:
            core_path = Path(__file__).parent.parent / "core"
            if str(core_path) not in sys.path:
                sys.path.insert(0, str(core_path))

            from harmonic_encoder import HarmonicEncoder, psnr as calc_psnr, _SCIPY_OK
            self._HarmonicEncoder = HarmonicEncoder
            self._calc_psnr = calc_psnr
            self._scipy_ok = _SCIPY_OK
            self._available = True
            logger.info(f"HarmonicEncoder charge (scipy_dct={_SCIPY_OK})")

        except ImportError as e:
            logger.warning(f"core/harmonic_encoder.py indisponible: {e}")
            self._HarmonicEncoder = None
            self._available = False

    # ------------------------------------------------------------------
    # Compression principale
    # ------------------------------------------------------------------

    def compress(
        self,
        image: np.ndarray,
        quality: Optional[float] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compresse une image en format harmonique .hce.

        Args:
            image: image RGB uint8 (H, W, 3) ou float32 [0,1]
            quality: qualite 1-100 (None = defaut)

        Returns:
            (hce_bytes, metadonnees dict)
        """
        t0 = time.time()
        img_f = self._to_float32(image)
        q = quality or self.default_quality

        if not self._available:
            return self._compress_fallback(img_f, q, t0)

        encoder = self._HarmonicEncoder(quality=q, use_ycbcr=True, chroma_subsample=True)
        hce_bytes, meta = encoder.encode(img_f)

        meta["compress_time_ms"] = (time.time() - t0) * 1000
        meta["quality_used"] = q
        meta["signature_guided"] = False
        return hce_bytes, meta

    def compress_with_signature(
        self,
        image: np.ndarray,
        signature: np.ndarray,
        quality: Optional[float] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compression guidee par la signature harmonique.

        La complexite spectrale de la signature determine la qualite optimale:
        - Image generee simple (peu de frequences) -> Q faible -> ratio eleve
        - Image complexe (beaucoup de frequences) -> Q haute -> meilleur PSNR

        La signature est embeddee dans le fichier resultant pour permettre:
        1. La re-ingestion automatique dans la BDD a la decompression
        2. Le guidage de la decompression (parametres adaptatifs)

        Args:
            image: RGB uint8 ou float32
            signature: vecteur 512D
            quality: qualite forcee (None = auto depuis signature)

        Returns:
            (hce_bytes_avec_signature, meta)
        """
        t0 = time.time()

        # Qualite auto depuis signature
        if quality is None and self.auto_quality:
            quality = self._derive_quality_from_signature(signature)

        # Compression standard
        hce_core, meta = self.compress(image, quality=quality)

        # Encapsulation avec signature et metadonnees etendues
        hce_ai = self._wrap_with_signature(hce_core, signature, meta)

        meta["signature_guided"] = True
        meta["quality_used"] = quality
        meta["quality_derived"] = self._describe_quality(quality)
        meta["encoded_bytes_total"] = len(hce_ai)
        meta["overhead_signature_bytes"] = len(hce_ai) - len(hce_core)
        meta["compress_time_ms"] = (time.time() - t0) * 1000

        return hce_ai, meta

    def decompress(self, hce_bytes: bytes) -> Tuple[np.ndarray, Optional[np.ndarray], Dict]:
        """
        Decompresse un fichier .hce (avec ou sans signature).

        Returns:
            (image_float32, signature_ou_None, metadonnees)
        """
        t0 = time.time()

        # Detecte si c'est un HCEAI (avec signature) ou HCE standard
        if hce_bytes[:6] == MAGIC_HCE_AI:
            hce_core, signature, embedded_meta = self._unwrap_with_signature(hce_bytes)
        else:
            hce_core = hce_bytes
            signature = None
            embedded_meta = {}

        if not self._available:
            image = self._decompress_fallback(hce_core)
        else:
            encoder = self._HarmonicEncoder()
            image = encoder.decode(hce_core)

        meta = {
            "decompress_time_ms": (time.time() - t0) * 1000,
            "has_signature": signature is not None,
            "image_shape": image.shape,
            **embedded_meta,
        }

        return image, signature, meta

    # ------------------------------------------------------------------
    # Sauvegarde / Chargement fichiers
    # ------------------------------------------------------------------

    def save(
        self,
        image: np.ndarray,
        path: str,
        signature: Optional[np.ndarray] = None,
        quality: Optional[float] = None,
        extra_meta: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Sauvegarde une image compresse en format .hce.

        Args:
            image: RGB uint8 ou float32
            path: chemin de sortie (.hce recommande)
            signature: signature 512D (embed dans le fichier si fournie)
            quality: qualite (None = auto)
            extra_meta: metadonnees supplementaires a embedder

        Returns:
            metadonnees de compression
        """
        t0 = time.time()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if signature is not None:
            hce_bytes, meta = self.compress_with_signature(image, signature, quality)
        else:
            hce_bytes, meta = self.compress(image, quality)

        # Embed extra_meta si fourni
        if extra_meta:
            meta["extra"] = extra_meta

        path.write_bytes(hce_bytes)

        meta["file_path"] = str(path)
        meta["file_size_bytes"] = path.stat().st_size
        meta["save_time_ms"] = (time.time() - t0) * 1000

        logger.info(
            f"Sauvegarde {path.name}: "
            f"{meta['original_bytes']:,} -> {meta['file_size_bytes']:,} bytes "
            f"({meta['compression_ratio']:.1f}:1) | "
            f"Q={meta['quality_used']:.0f} | "
            f"{meta['save_time_ms']:.1f}ms"
        )
        return meta

    def load(self, path: str) -> Tuple[np.ndarray, Optional[np.ndarray], Dict]:
        """
        Charge et decompresse un fichier .hce.

        Returns:
            (image_float32_[0,1], signature_512D_ou_None, metadonnees)
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier .hce introuvable: {path}")

        hce_bytes = path.read_bytes()
        image, signature, meta = self.decompress(hce_bytes)

        meta["file_path"] = str(path)
        meta["file_size_bytes"] = path.stat().st_size
        return image, signature, meta

    def save_video(
        self,
        frames: List[np.ndarray],
        base_path: str,
        signatures: Optional[List[np.ndarray]] = None,
        quality: Optional[float] = None,
        fps: float = 24.0,
    ) -> Dict[str, Any]:
        """
        Sauvegarde une sequence video frame par frame en .hce.
        Chaque frame est compresse individuellement avec sa signature.

        Le dossier cree contient:
          base_path/
            manifest.json        (fps, n_frames, resolution, stats)
            frame_0000.hce
            frame_0001.hce
            ...

        Args:
            frames: liste de frames uint8 RGB
            base_path: dossier de sortie
            signatures: liste de signatures (None = extraction auto)
            quality: qualite (None = auto par frame)
            fps: images par seconde

        Returns:
            stats de compression video
        """
        from .harmonic_signature import HarmonicSignatureExtractor

        base = Path(base_path)
        base.mkdir(parents=True, exist_ok=True)

        extractor = HarmonicSignatureExtractor()
        n = len(frames)
        total_orig = 0
        total_comp = 0
        frame_stats = []
        t0 = time.time()

        for i, frame in enumerate(frames):
            # Signature (fournie ou extraite)
            if signatures is not None and i < len(signatures):
                sig = signatures[i]
            else:
                sig, _ = extractor.extract(frame)

            frame_path = base / f"frame_{i:04d}.hce"
            meta = self.save(frame, str(frame_path), signature=sig, quality=quality)

            total_orig += meta.get("original_bytes", frame.nbytes)
            total_comp += meta.get("file_size_bytes", 0)
            frame_stats.append({
                "frame": i,
                "ratio": meta.get("compression_ratio", 1.0),
                "quality": meta.get("quality_used", 75),
                "size_bytes": meta.get("file_size_bytes", 0),
            })

        elapsed = time.time() - t0
        global_ratio = total_orig / max(1, total_comp)

        # Manifest JSON
        manifest = {
            "fps": fps,
            "n_frames": n,
            "resolution": list(frames[0].shape[:2][::-1]) if frames else [0, 0],
            "total_original_bytes": total_orig,
            "total_compressed_bytes": total_comp,
            "global_ratio": global_ratio,
            "space_saved_pct": (1 - total_comp / max(1, total_orig)) * 100,
            "encode_time_s": elapsed,
            "fps_encoding": n / elapsed if elapsed > 0 else 0,
            "has_signatures": True,
            "frame_stats": frame_stats,
        }
        (base / "manifest.json").write_text(json.dumps(manifest, indent=2))

        logger.info(
            f"Video sauvee: {n} frames | "
            f"ratio global {global_ratio:.1f}:1 | "
            f"{total_comp/1024:.1f} KB | "
            f"{elapsed:.1f}s"
        )
        return manifest

    def load_video(self, base_path: str) -> Tuple[List[np.ndarray], List[Optional[np.ndarray]], Dict]:
        """
        Charge une sequence video compressee.

        Returns:
            (frames, signatures, manifest)
        """
        base = Path(base_path)
        manifest_path = base / "manifest.json"

        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
        else:
            manifest = {}

        frame_files = sorted(base.glob("frame_*.hce"))
        frames = []
        signatures = []

        for f in frame_files:
            img, sig, _ = self.load(str(f))
            frames.append((img * 255).clip(0, 255).astype(np.uint8))
            signatures.append(sig)

        return frames, signatures, manifest

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------

    def _to_float32(self, image: np.ndarray) -> np.ndarray:
        """Convertit uint8 ou float32 en float32 [0,1]."""
        if image.dtype == np.uint8:
            return image.astype(np.float32) / 255.0
        elif image.dtype in (np.float32, np.float64):
            return np.clip(image, 0.0, 1.0).astype(np.float32)
        else:
            return image.astype(np.float32) / image.max()

    def _derive_quality_from_signature(self, signature: np.ndarray) -> float:
        """Determine la qualite optimale depuis la signature harmonique."""
        # Complexite = energie des coefficients DC + texture
        spectral_std = float(np.std(signature[:64]))    # Bloc Fourier-Phi
        texture_mean = float(np.mean(np.abs(signature[128:192])))  # Bloc DCT
        grad_mean = float(np.mean(np.abs(signature[192:256])))    # Bloc gradients

        # Complexite composite [0, ~0.3]
        complexity = (spectral_std + texture_mean + grad_mean) / 3.0

        # Mapping complexite -> qualite
        for low, high, q in SIGNATURE_QUALITY_MAP:
            if low <= complexity < high:
                return float(q)

        return self.default_quality

    def _describe_quality(self, quality: float) -> str:
        """Description textuelle de la qualite."""
        for name, info in QUALITY_PRESETS.items():
            if abs(info["quality"] - quality) <= 3:
                return f"{name} ({info['label']}, ~{info['ratio_est']:.0f}:1)"
        return f"custom ({quality:.0f})"

    def _wrap_with_signature(
        self, hce_core: bytes, signature: np.ndarray, meta: Dict
    ) -> bytes:
        """
        Encapsule les bytes HCE avec la signature harmonique.

        Format HCEAI :
          [MAGIC 6B]
          [signature_size:uint16]   -> 512 * 4 = 2048 bytes
          [signature float32 512D]
          [meta_json_size:uint32]
          [meta_json UTF-8]
          [hce_core_size:uint32]
          [hce_core data]
        """
        buf = io.BytesIO()
        buf.write(MAGIC_HCE_AI)

        # Signature
        sig_bytes = signature.astype(np.float32).tobytes()
        buf.write(struct.pack('<H', len(sig_bytes)))
        buf.write(sig_bytes)

        # Metadonnees JSON (subset leger)
        meta_light = {
            "quality": meta.get("quality_used", self.default_quality),
            "ratio": meta.get("compression_ratio", 1.0),
            "original_shape": list(meta.get("original_shape", [0, 0, 3])),
            "encoder": "HarmonicCompressorBridge_v1",
        }
        meta_bytes = json.dumps(meta_light).encode("utf-8")
        buf.write(struct.pack('<I', len(meta_bytes)))
        buf.write(meta_bytes)

        # Core HCE
        buf.write(struct.pack('<I', len(hce_core)))
        buf.write(hce_core)

        return buf.getvalue()

    def _unwrap_with_signature(
        self, hce_ai_bytes: bytes
    ) -> Tuple[bytes, np.ndarray, Dict]:
        """Decapsule un fichier HCEAI -> (hce_core, signature, meta)."""
        buf = io.BytesIO(hce_ai_bytes)
        magic = buf.read(6)
        if magic != MAGIC_HCE_AI:
            raise ValueError(f"Magic HCEAI invalide: {magic!r}")

        # Signature
        sig_size = struct.unpack('<H', buf.read(2))[0]
        sig_bytes = buf.read(sig_size)
        signature = np.frombuffer(sig_bytes, dtype=np.float32).copy()

        # Metadonnees JSON
        meta_size = struct.unpack('<I', buf.read(4))[0]
        meta_json = buf.read(meta_size).decode("utf-8")
        meta = json.loads(meta_json)

        # Core HCE
        core_size = struct.unpack('<I', buf.read(4))[0]
        hce_core = buf.read(core_size)

        return hce_core, signature, meta

    def _compress_fallback(
        self, img_f: np.ndarray, quality: float, t0: float
    ) -> Tuple[bytes, Dict]:
        """Fallback PNG si HarmonicEncoder indisponible."""
        try:
            from PIL import Image as PILImage
            img_u8 = (img_f * 255).clip(0, 255).astype(np.uint8)
            buf = io.BytesIO()
            PILImage.fromarray(img_u8).save(buf, format="PNG", optimize=True)
            data = buf.getvalue()
        except Exception:
            data = img_f.astype(np.float16).tobytes()

        orig = img_f.nbytes
        meta = {
            "encoder": "fallback_png",
            "quality_used": quality,
            "original_bytes": orig,
            "encoded_bytes": len(data),
            "compression_ratio": orig / max(1, len(data)),
            "space_saved_pct": (1 - len(data) / orig) * 100,
            "compress_time_ms": (time.time() - t0) * 1000,
        }
        return data, meta

    def _decompress_fallback(self, data: bytes) -> np.ndarray:
        """Fallback decompression PNG."""
        try:
            from PIL import Image as PILImage
            img = PILImage.open(io.BytesIO(data))
            return np.array(img).astype(np.float32) / 255.0
        except Exception:
            return np.zeros((64, 64, 3), dtype=np.float32)

    # ------------------------------------------------------------------
    # Info & stats
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._available

    def get_status(self) -> Dict[str, Any]:
        return {
            "available": self._available,
            "scipy_dct": getattr(self, "_scipy_ok", False),
            "default_quality": self.default_quality,
            "auto_quality": self.auto_quality,
            "presets": {k: v["ratio_est"] for k, v in QUALITY_PRESETS.items()},
        }

    def estimate_compressed_size(
        self, image: np.ndarray, quality: Optional[float] = None
    ) -> Dict[str, Any]:
        """Estime la taille compressee sans encoder reellement."""
        q = quality or self.default_quality
        H, W = image.shape[:2]
        orig_bytes = H * W * 3 * 4  # float32

        # Ratio estime
        if self._available:
            enc = self._HarmonicEncoder(quality=q)
            ratio = enc.estimate_ratio_from_quality()
            psnr_est = enc.estimate_psnr_from_quality()
        else:
            ratio = 10.0
            psnr_est = 30.0

        return {
            "original_bytes": orig_bytes,
            "estimated_compressed_bytes": int(orig_bytes / ratio),
            "estimated_ratio": ratio,
            "estimated_psnr_db": psnr_est,
            "quality": q,
        }


# ---------------------------------------------------------------------------
# Fonctions conveniences
# ---------------------------------------------------------------------------

def compress_generated_image(
    image: np.ndarray,
    signature: Optional[np.ndarray] = None,
    quality: str = "balanced",
) -> Tuple[bytes, Dict]:
    """
    Compresse une image generee en un seul appel.

    Args:
        image: image RGB uint8
        signature: signature harmonique (optionnelle)
        quality: preset ("lossless"|"high"|"balanced"|"efficient"|"compact")

    Returns:
        (hce_bytes, metadonnees)
    """
    bridge = HarmonicCompressorBridge(preset=quality, auto_quality=(signature is not None))
    if signature is not None:
        return bridge.compress_with_signature(image, signature)
    return bridge.compress(image)


def save_generated_image(
    image: np.ndarray,
    path: str,
    signature: Optional[np.ndarray] = None,
    quality: str = "balanced",
) -> Dict:
    """Sauvegarde une image generee compressee."""
    bridge = HarmonicCompressorBridge(preset=quality, auto_quality=True)
    return bridge.save(image, path, signature=signature)


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO)
    print("=== Test HarmonicCompressorBridge ===\n")

    bridge = HarmonicCompressorBridge(preset="balanced", auto_quality=True)
    print(f"Status: {bridge.get_status()}")
    print(f"Disponible: {bridge.is_available()}")

    # Image de test
    np.random.seed(42)
    H, W = 128, 128
    test_img = (np.random.rand(H, W, 3) * 255).astype(np.uint8)

    # Compression simple
    print(f"\nTest compression simple {H}x{W}...")
    hce, meta = bridge.compress(test_img, quality=75.0)
    print(f"  {test_img.nbytes:,} bytes -> {len(hce):,} bytes")
    print(f"  Ratio: {meta['compression_ratio']:.1f}:1")
    print(f"  Space saved: {meta['space_saved_pct']:.1f}%")
    print(f"  Temps: {meta['compress_time_ms']:.1f}ms")

    # Decompression
    img_dec, sig_dec, meta_dec = bridge.decompress(hce)
    print(f"  Decompr: {img_dec.shape} float32 [0,1]")

    # Compression avec signature
    print(f"\nTest compression avec signature...")
    sys.path.insert(0, str(Path(__file__).parent))
    from harmonic_signature import HarmonicSignatureExtractor
    extractor = HarmonicSignatureExtractor()
    sig, sig_meta = extractor.extract(test_img)
    print(f"  Signature: {sig.shape}, complexite={np.std(sig[:64]):.4f}")

    hce_ai, meta_ai = bridge.compress_with_signature(test_img, sig)
    print(f"  {test_img.nbytes:,} bytes -> {len(hce_ai):,} bytes")
    print(f"  Ratio: {meta_ai['compression_ratio']:.1f}:1")
    print(f"  Qualite auto: {meta_ai.get('quality_derived', 'N/A')}")
    print(f"  Overhead signature: {meta_ai.get('overhead_signature_bytes',0):,} bytes")

    # Decompression avec signature
    img_ai, sig_loaded, meta_load = bridge.decompress(hce_ai)
    print(f"  Decompr: {img_ai.shape}, signature={sig_loaded is not None}")
    if sig_loaded is not None:
        sim = float(np.dot(sig, sig_loaded))
        print(f"  Similarite signature: {sim:.6f} (1.0 = identique)")

    # Sauvegarde fichier
    print(f"\nTest sauvegarde/chargement...")
    save_meta = bridge.save(test_img, "test_output.hce", signature=sig)
    print(f"  Fichier: {save_meta['file_path']}")
    print(f"  Taille: {save_meta['file_size_bytes']:,} bytes")

    img_loaded, sig_loaded2, _ = bridge.load("test_output.hce")
    print(f"  Charge: {img_loaded.shape}")
    if sig_loaded2 is not None:
        sim2 = float(np.dot(sig, sig_loaded2))
        print(f"  Similarite signature: {sim2:.6f}")

    # Nettoyage
    import os
    if os.path.exists("test_output.hce"):
        os.remove("test_output.hce")

    # Test toutes qualites
    print(f"\nComparaison qualites (image {H}x{W}):")
    print(f"  {'Preset':<12} {'Q':>4} {'Ratio':>8} {'Taille':>10} {'Temps':>8}")
    print(f"  {'-'*12} {'-'*4} {'-'*8} {'-'*10} {'-'*8}")
    for pname, pinfo in QUALITY_PRESETS.items():
        q = pinfo["quality"]
        b, m = bridge.compress(test_img, quality=float(q))
        print(
            f"  {pname:<12} {q:>4.0f} "
            f"{m['compression_ratio']:>7.1f}:1 "
            f"{len(b):>8,} B "
            f"{m['compress_time_ms']:>6.1f}ms"
        )

    print("\n=== Test termine ===")
