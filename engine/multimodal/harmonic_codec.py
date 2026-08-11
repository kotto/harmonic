"""
Harmonic Codec — Codec unifié Harmonic Dictionary + HCV PRO
=============================================================

Pipeline encode:
  Image → patches → HarmonicDatabase.retrieve() → matched_patch
       → residual = original - matched (int16)
       → Delta-H + zstd → compressed_residual
  Bitstream = [header] + [patch_id(4B) + payload] × N_patches

Pipeline decode:
  Bitstream → header → for each patch: read ID → dict lookup → read residual
           → Delta-H decode → matched + residual → clip → assemble

Usage:
    from multimodal.harmonic_codec import HarmonicCodec
    codec = HarmonicCodec(db, use_hcv=True)
    data = codec.encode(image, concept='sunset')
    reconstructed = codec.decode(data)
"""

import sys
import math
import struct
import time
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

from multimodal.hcv_bridge import is_hcv_available, get_hcv_codec, get_hcv_functions

# Constantes du format de bitstream
MAGIC = b'HHDC'  # Harmonic-HCV Dictionary Codec
VERSION = 1
HEADER_SIZE = 16  # magic(4) + version(1) + patch_size(2) + grid_h(2) + grid_w(2) + flags(1) + K(1) + reserved(3)


class HarmonicCodec:
    """
    Codec unifié : Harmonic Dictionary + HCV Delta-H.

    Si use_hcv=False, utilise uniquement les IDs du dictionnaire (lossless exact).
    Si use_hcv=True, ajoute le residual HCV pour une reconstruction améliorée.
    """

    def __init__(self, database, use_hcv: bool = True, zstd_level: int = 11,
                 quality: int = 100):
        """
        Args:
            database: instance HarmonicDatabase
            use_hcv: activer HCV PRO
            zstd_level: compression zstd (1-22)
            quality: 0-100. 100=lossless, 45=visually lossless (~45dB PSNR),
                     30=acceptable, 10=très compressé
        """
        self.db = database
        self.ps = database.patch_size
        self.use_hcv = use_hcv
        self.zstd_level = zstd_level
        self.quality = quality
        self._quant_step = self._quality_to_step(quality)

        # Pont HCV
        self._hcv = None
        self._hcv_funcs = None
        if use_hcv:
            try:
                self._hcv = get_hcv_codec(bit_depth=8, zstd_level=zstd_level)
                self._hcv_funcs = get_hcv_functions()
            except Exception:
                self._hcv = None
                self._hcv_funcs = None

        # Compresseurs zstd réutilisables (évite recréation par patch)
        import zstandard as _zstd
        self._zstd_cctx = _zstd.ZstdCompressor(level=zstd_level)
        self._zstd_dctx = _zstd.ZstdDecompressor()

        # Seuil de distance pour le retrieval (au-delà → pas de bon match)
        self.match_threshold = 0.3  # L2 en espace des signatures (float32 normalisé)

        # Mode de résidu doré (P1 — la troncature 1/(φ·m)) : remplace la DCT
        # lossy par la diffract + seuil doré du codec modal HCV2 (zéro paramètre).
        self.golden_residual = False

        # Stats
        self.encode_time = 0.0
        self.decode_time = 0.0
        self.last_psnr = 0.0
        self.last_ratio = 0.0
        self._last_match_rate = 0.0
        self._last_video_match_rate = 0.0   # match rate for video (P-frames)
        self._last_video_skip_rate = 0.0     # skip rate for video (P-frames)
        self._last_video_mc_rate = 0.0       # motion-compensated skip rate

    @staticmethod
    def _quality_to_step(quality: int) -> int:
        """Convertit qualité (0-100) en pas de quantification Delta-H.
        
        Calibré empiriquement pour ps=16-64:
          100 → step=0 (lossless)
          90  → step=0 (visually lossless, pas de différence visible)
          70  → step=2 (~38dB, bonne qualité)
          45  → step=6 (~30dB, acceptable)
          30  → step=12 (~25dB, économique)
          10  → step=25 (~20dB, très compressé)
        """
        if quality >= 92:
            return 0
        if quality >= 80:
            return 1
        if quality >= 60:
            return 2
        if quality >= 50:
            return 4
        if quality >= 40:
            return 6
        if quality >= 30:
            return 10
        if quality >= 20:
            return 16
        if quality >= 10:
            return 22
        return 30

    def set_quality(self, quality: int):
        """Change la qualité à la volée."""
        self.quality = quality
        self._quant_step = self._quality_to_step(quality)

    @property
    def hcv_available(self) -> bool:
        return self._hcv is not None

    # ═══════════════════════════════════════════════════════════════════════
    # ENCODE
    # ═══════════════════════════════════════════════════════════════════════

    def encode(self, image: np.ndarray, concept: str = 'default',
               stride: int = None) -> bytes:
        """
        Encode une image en bitstream HHDC.

        Args:
            image: (H, W, 3) uint8
            concept: concept pour le retrieval
            stride: pas entre patches (défaut: patch_size)
        Returns:
            bytes — bitstream HHDC
        """
        t0 = time.perf_counter()
        img = np.asarray(image, dtype=np.uint8)
        H, W = img.shape[:2]
        ps = self.ps
        st = stride if stride is not None else ps

        n_h = max(1, (H + st - 1) // st)
        n_w = max(1, (W + st - 1) // st)

        # Header
        header = struct.pack(
            '<4sBHHHBB3s',
            MAGIC,           # 4B magic
            VERSION,         # 1B version
            ps,              # 2B patch_size
            n_h,             # 2B grid height
            n_w,             # 2B grid width
            1 if self.use_hcv else 0,  # 1B flags (bit 0: HCV enabled)
            self.db.K,       # 1B K (DFT coefficients)
            b'\x00\x00\x00', # 3B reserved
        )

        # Buffer pour les payloads
        payloads = []

        for i in range(n_h):
            for j in range(n_w):
                y0, x0 = i * st, j * st
                y1, x1 = min(y0 + ps, H), min(x0 + ps, W)

                # Pad si nécessaire (bord droit/bas)
                patch = np.zeros((ps, ps, 3), dtype=np.uint8)
                ph, pw = y1 - y0, x1 - x0
                patch[:ph, :pw] = img[y0:y1, x0:x1]

                # Retrieval dans le dictionnaire
                matched = self.db.retrieve(concept, patch)
                if matched is None:
                    # Pas de match → stocker le patch brut (fallback)
                    matched = np.zeros((ps, ps, 3), dtype=np.uint8)

                # Residual
                residual = patch.astype(np.int16) - matched.astype(np.int16)

                # Encoder le residual avec HCV ou stocker brut
                if self.use_hcv and self._hcv_funcs:
                    payload = self._encode_residual_hcv(residual)
                else:
                    payload = self._encode_residual_raw(residual)

                # Paquet: [concept_hash:2B][payload_len:4B][payload]
                concept_hash = (hash(concept) & 0xFFFF)
                pkt = struct.pack('<HI', concept_hash, len(payload)) + payload
                payloads.append(pkt)

        bitstream = header + b''.join(payloads)

        self.encode_time = time.perf_counter() - t0
        raw_bytes = H * W * 3
        self.last_ratio = raw_bytes / len(bitstream) if len(bitstream) > 0 else 0

        return bitstream

    def _encode_residual_hcv(self, residual: np.ndarray) -> bytes:
        """Encode un residual de patch via Delta-H + zstd."""
        parts = []
        for c in range(3):
            channel = residual[:, :, c].astype(np.int32)
            # Delta-H encode
            delta = channel.copy()
            delta[:, 1:] -= channel[:, :-1]
            # Pack manuel + zstd
            packed = self._pack_and_compress(delta)
            parts.append(struct.pack('<I', len(packed)))
            parts.append(packed)
        return b''.join(parts)

    def _encode_residual_raw(self, residual: np.ndarray) -> bytes:
        """Stocke le residual brut (sans HCV, fallback)."""
        return residual.astype(np.int16).tobytes()

    def _pack_and_compress(self, arr: np.ndarray) -> bytes:
        """Pack un array int32 en bytes + zstd compress."""
        raw = arr.tobytes()
        return self._zstd_cctx.compress(raw)

    # ═══════════════════════════════════════════════════════════════════════
    # DECODE
    # ═══════════════════════════════════════════════════════════════════════

    def decode(self, data: bytes) -> Tuple[np.ndarray, dict]:
        """
        Décode un bitstream HHDC en image.

        Returns:
            (image_rgb, metadata)
        """
        t0 = time.perf_counter()

        if len(data) < HEADER_SIZE:
            raise ValueError(f"Bitstream trop court: {len(data)} bytes")

        # Parser le header
        magic, version, ps, n_h, n_w, flags, K, reserved = struct.unpack(
            '<4sBHHHBB3s', data[:HEADER_SIZE]
        )

        if magic != MAGIC:
            raise ValueError(f"Magic invalide: {magic!r}, attendu {MAGIC!r}")

        use_hcv = (flags & 1) == 1

        # Image de sortie
        final_h = n_h * ps
        final_w = n_w * ps
        image = np.zeros((final_h, final_w, 3), dtype=np.float32)
        weight = np.zeros((final_h, final_w, 1), dtype=np.float32)

        offset = HEADER_SIZE

        for i in range(n_h):
            for j in range(n_w):
                if offset + 6 > len(data):
                    break

                # Lire le paquet
                concept_hash, payload_len = struct.unpack('<HI', data[offset:offset + 6])
                offset += 6

                if offset + payload_len > len(data):
                    break

                payload = data[offset:offset + payload_len]
                offset += payload_len

                # Décoder le residual
                if use_hcv:
                    residual = self._decode_residual_hcv(payload, ps)
                else:
                    residual = self._decode_residual_raw(payload, ps)

                # Le "matched" vient du dictionnaire — ici on utilise le residual
                # comme approximation (le dictionnaire n'est pas transmis dans le bitstream)
                # Pour le roundtrip, on reconstruit avec le residual seul
                # (le matched serait identique côté décodeur si le dictionnaire est partagé)
                patch = residual  # simplification: on stocke tout dans le residual pour le roundtrip

                # Assemblage avec blend (ou pas si pas de recouvrement)
                y0, x0 = i * ps, j * ps
                y1, x1 = min(y0 + ps, final_h), min(x0 + ps, final_w)
                ph, pw = y1 - y0, x1 - x0

                # Pas de blend si le patch est entier (pas de bordure)
                if ph == ps and pw == ps:
                    image[y0:y1, x0:x1] += patch[:ph, :pw].astype(np.float32)
                    weight[y0:y1, x0:x1] += 1.0
                else:
                    wy = HarmonicCodec._blend_window(ph)[:, None].astype(np.float32)
                    wx = HarmonicCodec._blend_window(pw)[None, :].astype(np.float32)
                    w = wy * wx
                    image[y0:y1, x0:x1] += patch[:ph, :pw].astype(np.float32) * w[:, :, None]
                    weight[y0:y1, x0:x1] += w[:, :, None]

        weight[weight < 1e-15] = 1.0
        image = image / weight
        image = np.clip(image, 0, 255).astype(np.uint8)

        self.decode_time = time.perf_counter() - t0

        meta = {
            'patch_size': ps,
            'grid': (n_h, n_w),
            'hcv_enabled': use_hcv,
            'version': version,
        }
        return image, meta

    def _decode_residual_hcv(self, payload: bytes, ps: int) -> np.ndarray:
        """Décode un residual HCV → patch (ps, ps, 3)."""
        dctx = self._zstd_dctx
        residual = np.zeros((ps, ps, 3), dtype=np.int16)
        poff = 0

        for c in range(3):
            if poff + 4 > len(payload):
                break
            chunk_len = struct.unpack('<I', payload[poff:poff + 4])[0]
            poff += 4
            if poff + chunk_len > len(payload):
                break
            compressed = payload[poff:poff + chunk_len]
            poff += chunk_len

            # Décompresser
            raw = dctx.decompress(compressed)
            delta = np.frombuffer(raw, dtype=np.int32).reshape(ps, ps).copy()
            # Delta-H decode: cumsum horizontal
            channel = delta.copy()
            channel[:, 0] = delta[:, 0]
            for col in range(1, ps):
                channel[:, col] = channel[:, col - 1] + delta[:, col]
            residual[:, :, c] = np.clip(channel, -32768, 32767).astype(np.int16)

        return residual

    def _decode_residual_raw(self, payload: bytes, ps: int) -> np.ndarray:
        """Décode un residual brut (sans HCV)."""
        residual = np.frombuffer(payload, dtype=np.int16).reshape(ps, ps, 3)
        return residual

    # ═══════════════════════════════════════════════════════════════════════
    # ENCODE/DECODE SIMPLIFIÉ (pour roundtrip sans dictionnaire partagé)
    # ═══════════════════════════════════════════════════════════════════════

    def encode_full(self, image: np.ndarray, concept: str = 'default') -> bytes:
        """
        Encode l'image ENTIÈRE dans le bitstream — autonome, pas de dictionnaire
        requis côté décodeur. Chaque patch est compressé avec Delta-H + zstd.

        C'est le mode de démonstration : l'image complète est dans le bitstream.
        """
        t0 = time.perf_counter()
        img = np.asarray(image, dtype=np.uint8)
        H, W = img.shape[:2]
        ps = self.ps
        st = ps

        n_h = max(1, (H + st - 1) // st)
        n_w = max(1, (W + st - 1) // st)

        header = struct.pack(
            '<4sBHHHBB3s',
            MAGIC, VERSION, ps, n_h, n_w,
            2,  # flags bit 1: mode full
            self.db.K,
            b'\x00\x00\x00',
        )

        # Encoder chaque patch séparément
        patch_payloads = []
        for i in range(n_h):
            for j in range(n_w):
                y0, x0 = i * st, j * st
                y1, x1 = min(y0 + ps, H), min(x0 + ps, W)
                patch = np.zeros((ps, ps, 3), dtype=np.uint8)
                ph, pw = y1 - y0, x1 - x0
                patch[:ph, :pw] = img[y0:y1, x0:x1]

                # Compresser le patch avec Delta-H + quantification + zstd par canal
                parts = []
                for c in range(3):
                    channel = patch[:, :, c].astype(np.int32)
                    delta = channel.copy()
                    delta[:, 1:] -= channel[:, :-1]
                    # 🆕 Quantification si qualité < 100
                    # On stocke le quotient (delta // step), pas delta*step
                    if self._quant_step > 0:
                        delta = (delta / self._quant_step).astype(np.int32)
                    packed = self._pack_and_compress(delta)
                    parts.append(struct.pack('<I', len(packed)) + packed)
                patch_data = b''.join(parts)
                patch_payloads.append(struct.pack('<I', len(patch_data)) + patch_data)

        bitstream = header + b''.join(patch_payloads)
        self.encode_time = time.perf_counter() - t0
        raw_bytes = H * W * 3
        self.last_ratio = raw_bytes / len(bitstream) if len(bitstream) > 0 else 0
        return bitstream

    def decode_full(self, data: bytes) -> Tuple[np.ndarray, dict]:
        """
        Décode un bitstream full (mode autonome, pas de dictionnaire requis).
        """
        t0 = time.perf_counter()
        dctx = self._zstd_dctx

        if len(data) < HEADER_SIZE:
            raise ValueError(f"Bitstream trop court: {len(data)} bytes")

        magic, version, ps, n_h, n_w, flags, K, reserved = struct.unpack(
            '<4sBHHHBB3s', data[:HEADER_SIZE]
        )
        if magic != MAGIC:
            raise ValueError(f"Magic invalide: {magic!r}")

        final_h = n_h * ps
        final_w = n_w * ps
        image = np.zeros((final_h, final_w, 3), dtype=np.float32)
        weight = np.zeros((final_h, final_w, 1), dtype=np.float32)

        offset = HEADER_SIZE

        for i in range(n_h):
            for j in range(n_w):
                if offset + 4 > len(data):
                    break
                patch_len = struct.unpack('<I', data[offset:offset + 4])[0]
                offset += 4

                if offset + patch_len > len(data):
                    break
                patch_data = data[offset:offset + patch_len]
                offset += patch_len

                # Décompresser les 3 canaux
                patch = np.zeros((ps, ps, 3), dtype=np.uint8)
                poff = 0
                for c in range(3):
                    if poff + 4 > len(patch_data):
                        break
                    chunk_len = struct.unpack('<I', patch_data[poff:poff + 4])[0]
                    poff += 4
                    compressed = patch_data[poff:poff + chunk_len]
                    poff += chunk_len

                    raw = dctx.decompress(compressed)
                    delta = np.frombuffer(raw, dtype=np.int32).reshape(ps, ps).copy()
                    # 🆕 Déquantification pour qualité < 100
                    if self._quant_step > 0:
                        delta = delta.astype(np.float64) * self._quant_step
                    # Delta-H inverse : cumsum horizontal
                    channel = delta.copy()
                    for col in range(1, ps):
                        channel[:, col] = channel[:, col - 1] + delta[:, col]
                    patch[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)

                # Assemblage avec blend (ou pas si pas de recouvrement)
                y0, x0 = i * ps, j * ps
                y1, x1 = min(y0 + ps, final_h), min(x0 + ps, final_w)
                ph, pw = y1 - y0, x1 - x0

                # Pas de blend si le patch est entier (pas de bordure)
                if ph == ps and pw == ps:
                    image[y0:y1, x0:x1] += patch[:ph, :pw].astype(np.float32)
                    weight[y0:y1, x0:x1] += 1.0
                else:
                    wy = HarmonicCodec._blend_window(ph)[:, None].astype(np.float32)
                    wx = HarmonicCodec._blend_window(pw)[None, :].astype(np.float32)
                    w = wy * wx
                    image[y0:y1, x0:x1] += patch[:ph, :pw].astype(np.float32) * w[:, :, None]
                    weight[y0:y1, x0:x1] += w[:, :, None]

        weight[weight < 1e-15] = 1.0
        image = image / weight
        image = np.clip(image, 0, 255).astype(np.uint8)

        self.decode_time = time.perf_counter() - t0
        meta = {'patch_size': ps, 'grid': (n_h, n_w), 'version': version}
        return image, meta

    # ═══════════════════════════════════════════════════════════════════════
    # BENCHMARK
    # ═══════════════════════════════════════════════════════════════════════

    def benchmark(self, image: np.ndarray, concept: str = 'default') -> dict:
        """
        Encode → decode → mesure PSNR, ratio, temps.

        Returns:
            dict avec psnr_db, ratio, encode_ms, decode_ms, taille_bitstream
        """
        data = self.encode_full(image, concept)
        reconstructed, meta = self.decode_full(data)

        psnr_val = self._psnr(image[:reconstructed.shape[0], :reconstructed.shape[1]],
                              reconstructed)
        raw_bytes = image.shape[0] * image.shape[1] * 3

        return {
            'psnr_db': round(psnr_val, 2),
            'ratio': round(self.last_ratio, 1),
            'encode_ms': round(self.encode_time * 1000, 2),
            'decode_ms': round(self.decode_time * 1000, 2),
            'bitstream_bytes': len(data),
            'raw_bytes': raw_bytes,
            'hcv_available': self.hcv_available,
            'patch_size': self.ps,
        }

    @staticmethod
    def _psnr(a: np.ndarray, b: np.ndarray) -> float:
        """PSNR entre deux images uint8."""
        a = a.astype(np.float64)
        b = b.astype(np.float64)
        mse = np.mean((a - b) ** 2)
        if mse < 1e-15:
            return 100.0
        return 20.0 * math.log10(255.0 / math.sqrt(mse))

    @staticmethod
    def _blend_window(n: int) -> np.ndarray:
        if n <= 1:
            return np.ones(1, dtype=np.float32)
        x = np.arange(n, dtype=np.float32)
        return (0.5 * (1.0 - np.cos(2.0 * math.pi * x / max(n - 1, 1)))).astype(np.float32)

    # ═══════════════════════════════════════════════════════════════════════
    # VIDÉO : I/P frames avec conditional replenishment
    # ═══════════════════════════════════════════════════════════════════════

    FRAME_I = 0x01  # I-frame (tous les patches, encodage DCT+zstd)
    FRAME_P = 0x02  # P-frame (seulement les patches modifiés)
    FRAME_I_HCV = 0x03  # 🆕 I-frame encodée avec HCV Pro (mode hybride)
    FRAME_I_BEST = 0x04  # I-frame encodée par encode_best (V2 DICT / FULL)
    END_MARKER = 0xFFFFFFFF
    
    # Motion compensation flags (bitstream)
    MC_SKIP = 0x02   # motion-compensated skip (copy from reference at offset)
    MC_DICT = 0x03   # motion-compensated dict match (dict ID + offset)
    MC_RESIDUAL = 0x04  # motion-compensated + résidu (exact — supprime le plancher d'erreur du MC-SKIP)

    def encode_video(self, frames: list, concept: str = 'default',
                     skip_threshold: float = 5.0,
                     motion_invariant: bool = False,
                     motion_search_range: int = 8,
                     iframe_min_psnr: float = None,
                     gop_size: int = 0) -> bytes:
        """
        Encode une séquence vidéo en I/P frames.
        
        🆕 Mode HYBRIDE (use_hcv=True) :
          - I-frame encodée avec HCV Pro (24:1 au lieu de 1.2:1)
          - P-frames inchangées (skip + motion compensation)
          - Gain: 30:1 → 55:1 sur vidéo avec mouvement modéré
        
        Frame 0 = I-frame. P-frames comparent contre FRAME 0 (pas la précédente)
        pour éviter l'accumulation d'erreurs.
        """
        if not frames:
            return b''

        t0 = time.perf_counter()
        ps = self.ps
        H, W = frames[0].shape[:2]
        # 🆕 Grid must cover the FULL image (ceil division)
        n_h = (H + ps - 1) // ps
        n_w = (W + ps - 1) // ps

        chunks = []
        reference = frames[0]

        for frame_idx, frame in enumerate(frames):
            img = np.asarray(frame, dtype=np.uint8)

            if frame_idx == 0 or (gop_size and frame_idx % gop_size == 0):
                # 🆕 I-frame (ou GOP : réinsérée tous les gop_size frames —
                # la référence se rafraîchit, la dérive des frames lointaines
                # est bornée ; l'I-frame coûte peu : ~246× exacte)
                # Sélecteur (V2 DICT / FULL / MODAL si iframe_min_psnr fixé)
                if self.use_hcv and len(self.db._shards) > 0:
                    iframe_data, _ = self.encode_select(img, min_psnr=iframe_min_psnr)
                    header = struct.pack('<HHI', H, W, len(iframe_data))
                    chunks.append(bytes([self.FRAME_I_BEST]) + header + iframe_data)
                elif self.use_hcv and self._hcv is not None:
                    iframe_data = self._encode_iframe_hcv(img)
                    chunks.append(bytes([self.FRAME_I_HCV]) + iframe_data)
                else:
                    iframe_data = self._encode_iframe(img, n_h, n_w)
                    chunks.append(bytes([self.FRAME_I]) + iframe_data)
            else:
                # P-frame vs la frame précédente RECONSTRUITE (encode-décode) —
                # la référence exacte que le décodeur aura : comparer à
                # l'originale divergeait (erreurs de skip recopiées → accumulation).
                # Le MÊME sélecteur que l'I-frame (sinon l'encodeur comparerait
                # à l'exacte et le décodeur aurait la lossy)
                ref_prev = self._reconstruct_frame(frames[frame_idx - 1],
                                                   iframe_min_psnr)
                pframe_data = self._encode_pframe(img, ref_prev, n_h, n_w,
                                                   skip_threshold, motion_invariant,
                                                   motion_search_range)
                chunks.append(bytes([self.FRAME_P]) + pframe_data)

        bitstream = b''.join(chunks)
        self.encode_time = time.perf_counter() - t0

        raw_bytes = sum(f.shape[0] * f.shape[1] * 3 for f in frames)
        self.last_ratio = raw_bytes / len(bitstream) if len(bitstream) > 0 else 0
        return bitstream

    def _reconstruct_frame(self, img: np.ndarray,
                           iframe_min_psnr: float = None) -> np.ndarray:
        """Encode-décode une image → la référence que le décodeur aura
        (encode_select + décodage par magic, recadrage aux dimensions
        originales). Utilisée comme référence des P-frames : le MÊME
        sélecteur que l'I-frame (min_psnr) pour que l'encodeur compare à
        ce que le décodeur reconstruira — sinon, avec une I-frame MODAL
        (lossy), l'encodeur comparerait à l'exacte et les erreurs de
        l'I-frame se propageraient via les skips."""
        data, _ = self.encode_select(img, min_psnr=iframe_min_psnr)
        if data[:4] == self.MODAL_MAGIC:
            m = self._modal_helpers()
            rec = m.decode(data[4:])
        elif data[:4] == self.V2_MAGIC:
            rec, _ = self.decode_v2(data, database=self.db)
        else:
            rec, _ = self.decode_full(data)
        return rec[:img.shape[0], :img.shape[1]]

    def _encode_iframe_hcv(self, img: np.ndarray) -> bytes:
        """Encode une I-frame avec HCV Pro (mode hybride).
        
        L'image est paddée aux dimensions de la grille (multiple de ps)
        pour que les P-frames puissent référencer des patches alignés.
        """
        H, W = img.shape[:2]
        ps = self.ps
        # Calculer les dimensions alignées sur la grille (ceil division)
        grid_h = ((H + ps - 1) // ps) * ps
        grid_w = ((W + ps - 1) // ps) * ps
        
        # Pad si nécessaire
        if H != grid_h or W != grid_w:
            padded = np.zeros((grid_h, grid_w, 3), dtype=np.uint8)
            padded[:H, :W] = img
            img_to_encode = padded
        else:
            img_to_encode = img
        
        enc_result = self._hcv.encode_frame(img_to_encode)
        hcv_data = enc_result[0] if isinstance(enc_result, tuple) else enc_result
        # Header: dimensions originales + taille HCV
        header = struct.pack('<HHI', H, W, len(hcv_data))
        return header + hcv_data

    def _encode_iframe(self, img: np.ndarray, n_h: int, n_w: int) -> bytes:
        """Encode une I-frame : tous les patches."""
        ps = self.ps
        payloads = [struct.pack('<HH', n_h, n_w)]  # grid dimensions

        for i in range(n_h):
            for j in range(n_w):
                y0, x0 = i * ps, j * ps
                y1, x1 = min(y0 + ps, img.shape[0]), min(x0 + ps, img.shape[1])
                patch = np.zeros((ps, ps, 3), dtype=np.uint8)
                ph, pw = y1 - y0, x1 - x0
                patch[:ph, :pw] = img[y0:y1, x0:x1]

                # Compresser le patch
                patch_data = self._compress_patch(patch)
                payloads.append(struct.pack('<I', len(patch_data)) + patch_data)

        return b''.join(payloads)

    def _encode_pframe(self, img: np.ndarray, prev: np.ndarray,
                       n_h: int, n_w: int, threshold: float,
                       motion_invariant: bool = False,
                       motion_search_range: int = 8) -> bytes:
        """
        Encode une P-frame V3 : motion compensation + dictionnaire + skip.
        
        Pour chaque patch :
        1. Recherche du meilleur match dans la référence (motion compensation)
        2. Si match trouvé à (dx,dy) avec diff < threshold :
           - (dx,dy) == (0,0) → skip implicite (0 octet)
           - (dx,dy) != (0,0) → MC-SKIP : [idx:4B][0x02][dx:1B][dy:1B] (7 octets)
        3. Sinon, dictionnaire → [idx:4B][0x01][shard:2B][patch:4B][residual_len:4B][data]
        4. Fallback raw → [idx:4B][0x00][raw_len:4B][raw_data]
        """
        ps = self.ps
        parts = [struct.pack('<HH', n_h, n_w)]
        n_changed = 0
        n_dict = 0
        n_exact = 0
        n_mc_skip = 0
        n_mc_res = 0
        n_total = 0
        n_skip_static = 0
        
        H_ref, W_ref = prev.shape[:2]
        sr = motion_search_range  # search radius in pixels
        
        for i in range(n_h):
            for j in range(n_w):
                n_total += 1
                y0, x0 = i * ps, j * ps
                y1, x1 = min(y0 + ps, img.shape[0]), min(x0 + ps, img.shape[1])
                ph, pw = y1 - y0, x1 - x0
                curr = np.zeros((ps, ps, 3), dtype=np.uint8)
                curr[:ph, :pw] = img[y0:y1, x0:x1]
                
                # ── Motion Search ──
                # Search in reference frame for best matching patch
                best_dx, best_dy = 0, 0
                best_diff = float('inf')
                
                # First, check exact position (0,0) — fast path
                ref_patch_00 = np.zeros((ps, ps, 3), dtype=np.uint8)
                if y0 < H_ref and x0 < W_ref:
                    ry1 = min(y0 + ps, H_ref)
                    rx1 = min(x0 + ps, W_ref)
                    ref_patch_00[:ry1-y0, :rx1-x0] = prev[y0:ry1, x0:rx1]
                diff_00 = np.sqrt(np.mean((curr.astype(float) - ref_patch_00.astype(float)) ** 2))
                best_diff = diff_00
                best_dx, best_dy = 0, 0
                
                # If exact position is good enough, skip search
                if diff_00 >= threshold and sr > 0:
                    # Search window around expected position
                    for dy in range(-sr, sr + 1):
                        for dx in range(-sr, sr + 1):
                            if dx == 0 and dy == 0:
                                continue  # already checked
                            
                            ref_y0 = y0 + dy
                            ref_x0 = x0 + dx
                            
                            # Clamp to reference frame bounds
                            if ref_y0 < 0 or ref_x0 < 0:
                                continue
                            if ref_y0 + ps > H_ref or ref_x0 + ps > W_ref:
                                continue
                            
                            ref_patch = prev[ref_y0:ref_y0 + ps, ref_x0:ref_x0 + ps]
                            diff = np.sqrt(np.mean((curr.astype(float) - ref_patch.astype(float)) ** 2))
                            
                            if diff < best_diff:
                                best_diff = diff
                                best_dx, best_dy = dx, dy
                                
                                # Early exit if we found a very good match
                                if diff < threshold * 0.5:
                                    break
                        else:
                            continue
                        break  # break outer loop too if early exit
                
                # ── Decision ──
                grid_idx = i * n_w + j
                
                if best_diff < threshold:
                    if best_dx == 0 and best_dy == 0:
                        # Static skip — patch unchanged
                        n_skip_static += 1
                        continue
                    else:
                        # Motion-compensated skip
                        # Store as signed byte (clamp to [-128, 127])
                        dx_byte = max(-128, min(127, best_dx))
                        dy_byte = max(-128, min(127, best_dy))
                        pkt = struct.pack('<IBbb', grid_idx, self.MC_SKIP, dx_byte, dy_byte)
                        parts.append(pkt)
                        n_mc_skip += 1
                        n_changed += 1
                        continue
                
                # ── MC avec résidu (exact) ──
                # La compensation est bonne sans être parfaite
                # (threshold ≤ diff < 1,5·threshold) : patch déplacé + résidu —
                # supprime le plancher d'erreur du MC-SKIP. Plage volontairement
                # étroite : au-delà, le dict matche mieux (résidu ~0)
                if (best_dx != 0 or best_dy != 0) and best_diff < threshold * 2.0:
                    dx_byte = max(-128, min(127, best_dx))
                    dy_byte = max(-128, min(127, best_dy))
                    ref_patch = prev[y0 + best_dy:y0 + best_dy + ps,
                                     x0 + best_dx:x0 + best_dx + ps]
                    residual = curr.astype(np.int16) - ref_patch.astype(np.int16)
                    residual_data = self._compress_residual(residual)
                    pkt = struct.pack('<IBbbI', grid_idx, self.MC_RESIDUAL,
                                      dx_byte, dy_byte, len(residual_data))
                    pkt += residual_data
                    parts.append(pkt)
                    n_mc_res += 1
                    n_changed += 1
                    continue

                # ── No good motion match → dictionary or raw ──
                id_result = self.db.retrieve_with_id('default', curr)

                if id_result is not None and id_result[2] >= 0:
                    matched, shard_id, patch_idx, dist = id_result
                    if dist < self.match_threshold:
                        # Dictionary match → résiduel
                        residual = curr.astype(np.int16) - matched.astype(np.int16)
                        if np.all(residual == 0):
                            n_exact += 1
                            continue  # exact match → skip
                        residual_data = self._compress_residual(residual)
                        pkt = struct.pack('<IBHII', grid_idx, 0x01,
                                          shard_id & 0xFFFF, patch_idx,
                                          len(residual_data))
                        pkt += residual_data
                        parts.append(pkt)
                        n_dict += 1
                        n_changed += 1
                        continue

                # Fallback: raw patch
                patch_data = self._compress_patch(curr)
                pkt = struct.pack('<IBI', grid_idx, 0x00, len(patch_data))
                pkt += patch_data
                parts.append(pkt)
                n_changed += 1

        # Update video-specific stats
        self._last_video_match_rate = (n_dict + n_exact) / max(n_total, 1)
        self._last_video_skip_rate = (n_skip_static + n_mc_skip) / max(n_total, 1)
        self._last_video_mc_rate = n_mc_skip / max(n_total, 1)
        self._last_video_mc_res_rate = n_mc_res / max(n_total, 1)

        parts.append(struct.pack('<I', self.END_MARKER))
        return b''.join(parts)

    def _compress_patch(self, patch: np.ndarray) -> bytes:
        """Compresse un patch (ps, ps, 3) uint8 avec DCT 2D + quantification + RLE + zstd."""
        cctx = self._zstd_cctx
        ps = patch.shape[0]
        N = ps
        q = max(1, self._quant_step)
        zigzag = self._zigzag_indices(N)
        parts = []
        
        for c in range(3):
            channel = patch[:, :, c].astype(np.float64) - 128.0  # centrer autour de 0
            dct_coeffs = self._dct_2d(channel)
            dct_q = np.round(dct_coeffs / q).astype(np.int32)
            
            # RLE zigzag
            symbols = []
            run = 0
            for idx_i, idx_j in zigzag:
                val = int(dct_q[idx_i, idx_j])
                if val == 0:
                    run += 1
                else:
                    symbols.append((run, val))
                    run = 0
            
            buf = bytearray()
            buf.extend(struct.pack('<H', len(symbols)))
            for run_len, val in symbols:
                run_byte = min(run_len, 255)
                buf.extend(struct.pack('<Bh', run_byte, val))
                extra = run_len - 255
                while extra > 0:
                    buf.extend(struct.pack('<Bh', min(extra, 255), 0))
                    extra -= 255
            
            compressed = cctx.compress(bytes(buf))
            parts.append(struct.pack('<I', len(compressed)) + compressed)
        
        return b''.join(parts)
    
    def _decompress_patch(self, patch_data: bytes, ps: int, dctx) -> np.ndarray:
        """Décompresse un patch → (ps, ps, 3) uint8 (DCT + IQ + IDCT)."""
        N = ps
        q = max(1, self._quant_step)
        zigzag = self._zigzag_indices(N)
        patch = np.zeros((ps, ps, 3), dtype=np.uint8)
        poff = 0
        
        for c in range(3):
            if poff + 4 > len(patch_data):
                break
            chunk_len = struct.unpack('<I', patch_data[poff:poff + 4])[0]
            poff += 4
            compressed = patch_data[poff:poff + chunk_len]
            poff += chunk_len
            raw = dctx.decompress(compressed)
            
            if len(raw) < 2:
                continue
            n_symbols = struct.unpack('<H', raw[:2])[0]
            offset = 2
            symbols = []
            for _ in range(n_symbols):
                if offset + 3 > len(raw):
                    break
                run_len, val = struct.unpack('<Bh', raw[offset:offset + 3])
                offset += 3
                symbols.append((run_len, val))
            
            dct_q = np.zeros((N, N), dtype=np.int32)
            sym_idx = 0
            zig_idx = 0
            while zig_idx < N * N and sym_idx < len(symbols):
                run_len, val = symbols[sym_idx]
                zig_idx += run_len
                if zig_idx >= N * N:
                    break
                i, j = zigzag[zig_idx]
                dct_q[i, j] = val
                zig_idx += 1
                sym_idx += 1
            
            dct_deq = dct_q.astype(np.float64) * q
            channel = self._idct_2d(dct_deq)
            patch[:, :, c] = np.clip(np.round(channel + 128.0), 0, 255).astype(np.uint8)
        
        return patch

    def _compress_patch_direct(self, patch: np.ndarray) -> bytes:
        """Alias pour _compress_patch (compatibilité V2)."""
        return self._compress_patch(patch)

    def decode_video(self, data: bytes) -> Tuple[list, dict]:
        """
        Décode un bitstream vidéo HHDC en liste de frames.

        Returns:
            (frames, metadata)
            frames: liste de (H, W, 3) uint8
            metadata: dict avec n_frames, n_iframes, n_pframes, skip_rate
        """
        t0 = time.perf_counter()
        dctx = self._zstd_dctx

        frames = []
        offset = 0
        n_iframes = 0
        n_pframes = 0
        total_patches = 0
        skipped_patches = 0

        # La première frame donne les dimensions
        current_frame = None
        iframe_reference = None

        while offset < len(data):
            if offset >= len(data):
                break

            frame_type = data[offset]
            offset += 1

            # Lire les dimensions de la grille (sauf pour HCV I-frame qui a son propre header)
            if frame_type == self.FRAME_I_BEST:
                # 🆕 I-frame encodée par encode_best (HHD2 ou HHDC)
                n_iframes += 1
                H_orig, W_orig, best_len = struct.unpack(
                    '<HHI', data[offset:offset + 8])
                offset += 8
                best_data = data[offset:offset + best_len]
                offset += best_len
                if best_data[:4] == self.MODAL_MAGIC:
                    m = self._modal_helpers()
                    image = m.decode(best_data[4:])
                elif best_data[:4] == self.V2_MAGIC:
                    image, _ = self.decode_v2(best_data, database=self.db)
                else:
                    image, _ = self.decode_full(best_data)
                image = image[:H_orig, :W_orig]
                final_h, final_w = image.shape[:2]
                n_h = max(1, final_h // self.ps)
                n_w = max(1, final_w // self.ps)
                total_patches += n_h * n_w
                frames.append(image.astype(np.uint8))
                iframe_reference = image.astype(np.uint8).copy()
                continue

            if frame_type == self.FRAME_I_HCV:
                # 🆕 Mode hybride: I-frame HCV Pro
                n_iframes += 1
                H_orig, W_orig, hcv_len = struct.unpack(
                    '<HHI', data[offset:offset + 8])
                offset += 8
                hcv_data = data[offset:offset + hcv_len]
                offset += hcv_len
                if self._hcv is not None:
                    image = self._hcv.decode_frame(hcv_data)
                else:
                    image = np.zeros((H_orig, W_orig, 3), dtype=np.uint8)
                if image is None:
                    image = np.zeros((H_orig, W_orig, 3), dtype=np.uint8)
                # Recadrer aux dimensions originales (le HCV a encodé l'image paddée)
                image = image[:H_orig, :W_orig]
                final_h, final_w = image.shape[:2]
                n_h = max(1, final_h // self.ps)
                n_w = max(1, final_w // self.ps)
                total_patches += n_h * n_w
                frames.append(image.astype(np.uint8))
                iframe_reference = image.astype(np.uint8).copy()
                continue

            # Lire les dimensions de la grille (mode standard)
            n_h, n_w = struct.unpack('<HH', data[offset:offset + 4])
            offset += 4
            ps = self.ps
            final_h, final_w = n_h * ps, n_w * ps

            image = np.zeros((final_h, final_w, 3), dtype=np.float32)
            weight = np.zeros((final_h, final_w, 1), dtype=np.float32)

            if frame_type == self.FRAME_I:
                n_iframes += 1
                # Lire tous les patches
                for i in range(n_h):
                    for j in range(n_w):
                        if offset + 4 > len(data):
                            break
                        patch_len = struct.unpack('<I', data[offset:offset + 4])[0]
                        offset += 4
                        patch_data = data[offset:offset + patch_len]
                        offset += patch_len

                        patch = self._decompress_patch(patch_data, ps, dctx)
                        y0, x0 = i * ps, j * ps
                        y1, x1 = min(y0 + ps, final_h), min(x0 + ps, final_w)
                        image[y0:y1, x0:x1] += patch[:y1-y0, :x1-x0].astype(np.float32)
                        weight[y0:y1, x0:x1] += 1.0
                total_patches += n_h * n_w

            elif frame_type == self.FRAME_P:
                n_pframes += 1
                frame_patches = 0
                # Repartir de la frame PRÉCÉDENTE décodée (mise à jour après
                # chaque frame — cohérent avec l'encodeur, qui compare à la
                # frame précédente : le mouvement cumulé vs frame 0 écrasait
                # le ratio)
                if iframe_reference is not None:
                    H_ref, W_ref = iframe_reference.shape[:2]
                    # 🆕 Utiliser les dimensions réelles de la référence
                    final_h, final_w = H_ref, W_ref
                    image = iframe_reference.astype(np.float32)
                    weight = np.ones((final_h, final_w, 1), dtype=np.float32)
                else:
                    H_ref, W_ref = final_h, final_w

                while offset + 4 <= len(data):
                    patch_idx = struct.unpack('<I', data[offset:offset + 4])[0]
                    offset += 4

                    if patch_idx == self.END_MARKER:
                        break

                    if offset >= len(data):
                        break
                    flags = data[offset]
                    offset += 1
                    
                    # Compute grid position early (needed by MC-SKIP)
                    i = patch_idx // n_w
                    j = patch_idx % n_w
                    y0, x0 = i * ps, j * ps
                    y1, x1 = min(y0 + ps, final_h), min(x0 + ps, final_w)

                    if flags == 0x01:
                        # Dictionary-based residual
                        if offset + 10 > len(data):
                            break
                        shard_id, dict_idx, residual_len = struct.unpack(
                            '<HII', data[offset:offset + 10])
                        if shard_id > 32767:
                            shard_id = shard_id - 65536
                        offset += 10

                        if residual_len == 0:
                            # Exact match → look up from dictionary
                            if self.db:
                                matched = self.db.get_patch_by_id(shard_id, dict_idx)
                                patch = matched if matched is not None else np.zeros((ps, ps, 3), dtype=np.uint8)
                            else:
                                patch = np.zeros((ps, ps, 3), dtype=np.uint8)
                        else:
                            if offset + residual_len > len(data):
                                break
                            residual_data = data[offset:offset + residual_len]
                            offset += residual_len
                            residual = self._decompress_residual(residual_data, ps, dctx)
                            if self.db:
                                matched = self.db.get_patch_by_id(shard_id, dict_idx)
                                if matched is not None:
                                    patch = np.clip(matched.astype(np.int16) + residual, 0, 255).astype(np.uint8)
                                else:
                                    patch = np.clip(residual, 0, 255).astype(np.uint8)
                            else:
                                patch = np.clip(residual, 0, 255).astype(np.uint8)
                    
                    elif flags == 0x02:
                        # MC-SKIP: motion-compensated skip — copy patch from reference at offset
                        # dx, dy are in PIXELS (not grid units)
                        if offset + 2 > len(data):
                            break
                        dx, dy = struct.unpack('<bb', data[offset:offset + 2])
                        offset += 2
                        
                        # Source position in reference frame (pixel coordinates)
                        ref_y0 = max(0, min(H_ref - ps, y0 + dy))
                        ref_x0 = max(0, min(W_ref - ps, x0 + dx))
                        
                        patch = np.zeros((ps, ps, 3), dtype=np.uint8)
                        ry1 = min(ref_y0 + ps, H_ref)
                        rx1 = min(ref_x0 + ps, W_ref)
                        patch[:ry1-ref_y0, :rx1-ref_x0] = iframe_reference[ref_y0:ry1, ref_x0:rx1]
                    
                    elif flags == 0x04:
                        # MC-RESIDUAL: patch = référence déplacée + résidu (exact)
                        if offset + 6 > len(data):
                            break
                        dx, dy = struct.unpack('<bb', data[offset:offset + 2])
                        offset += 2
                        residual_len = struct.unpack('<I', data[offset:offset + 4])[0]
                        offset += 4
                        # Clamp comme le MC-SKIP (dy → y, dx → x)
                        ref_y0 = max(0, min(H_ref - ps, y0 + dy))
                        ref_x0 = max(0, min(W_ref - ps, x0 + dx))
                        ref_patch = np.zeros((ps, ps, 3), dtype=np.uint8)
                        ry1 = min(ref_y0 + ps, H_ref)
                        rx1 = min(ref_x0 + ps, W_ref)
                        ref_patch[:ry1 - ref_y0, :rx1 - ref_x0] = \
                            iframe_reference[ref_y0:ry1, ref_x0:rx1]
                        residual = self._decompress_residual(
                            data[offset:offset + residual_len], ps, dctx)
                        offset += residual_len
                        patch = np.clip(ref_patch.astype(np.int16) + residual,
                                        0, 255).astype(np.uint8)

                    elif flags == 0x03:
                        # MC-DICT: motion-compensated dict match (not yet implemented)
                        # Fall through to raw
                        if offset + 4 > len(data):
                            break
                        patch_len = struct.unpack('<I', data[offset:offset + 4])[0]
                        offset += 4
                        patch_data = data[offset:offset + patch_len]
                        offset += patch_len
                        patch = self._decompress_patch(patch_data, ps, dctx)
                    
                    else:
                        # Raw patch (flags == 0x00 or unknown)
                        if offset + 4 > len(data):
                            break
                        patch_len = struct.unpack('<I', data[offset:offset + 4])[0]
                        offset += 4
                        patch_data = data[offset:offset + patch_len]
                        offset += patch_len
                        patch = self._decompress_patch(patch_data, ps, dctx)

                    i = patch_idx // n_w
                    j = patch_idx % n_w
                    # y0, x0, y1, x1 already computed above
                    image[y0:y1, x0:x1] = patch[:y1-y0, :x1-x0].astype(np.float32)
                    weight[y0:y1, x0:x1] = 1.0
                    frame_patches += 1

                skipped = (n_h * n_w) - frame_patches
                skipped_patches += skipped
                total_patches += n_h * n_w

            # Normaliser
            weight[weight < 1e-15] = 1.0
            image = image / weight
            image = np.clip(image, 0, 255).astype(np.uint8)
            frames.append(image)
            current_frame = image
            # Référence des P-frames suivantes : la frame PRÉCÉDENTE décodée
            iframe_reference = image.copy()

        self.decode_time = time.perf_counter() - t0

        meta = {
            'n_frames': len(frames),
            'n_iframes': n_iframes,
            'n_pframes': n_pframes,
            'total_patches': total_patches,
            'skipped_patches': skipped_patches,
            'skip_rate': skipped_patches / max(total_patches, 1),
        }
        return frames, meta

    # ═══════════════════════════════════════════════════════════════════════
    # V2 : CODEC AVEC DICTIONNAIRE PARTAGÉ
    # ═══════════════════════════════════════════════════════════════════════

    V2_MAGIC = b'HHD2'  # Version 2 du bitstream (avec IDs de patches)

    def encode_v2(self, image: np.ndarray, concept: str = 'default') -> bytes:
        """
        Encode V2 — dictionnaire partagé avec batch retrieval.
        Toutes les signatures sont calculées en une FFT batch,
        puis chaque shard est requêté en une seule opération KD-tree.
        """
        t0 = time.perf_counter()
        img = np.asarray(image, dtype=np.uint8)
        H, W = img.shape[:2]
        ps = self.ps
        st = ps

        n_h = max(1, (H + st - 1) // st)
        n_w = max(1, (W + st - 1) // st)
        total_patches = n_h * n_w

        # Extraire tous les patches
        all_patches = np.zeros((total_patches, ps, ps, 3), dtype=np.uint8)
        patch_idx = 0
        for i in range(n_h):
            for j in range(n_w):
                y0, x0 = i * st, j * st
                y1, x1 = min(y0 + ps, H), min(x0 + ps, W)
                ph, pw = y1 - y0, x1 - x0
                all_patches[patch_idx, :ph, :pw] = img[y0:y1, x0:x1]
                patch_idx += 1

        # Calculer toutes les signatures en batch
        all_sigs = self.db._compute_signatures_batch(all_patches)

        # Pour chaque patch: [shard_id, patch_idx, dist]
        best_shard = np.full(total_patches, -1, dtype=np.int32)
        best_idx = np.zeros(total_patches, dtype=np.int32)
        best_dist = np.full(total_patches, float('inf'), dtype=np.float32)
        best_pixels = np.zeros_like(all_patches)

        # Requêter TOUS les shards via mmap + matrice de distances vectorisée
        for shard_idx in range(len(self.db._shards)):
            shard = self.db._shards[shard_idx]
            sig_file = shard._path / 'signatures.npy' if shard._path else None
            sigs = None
            if sig_file and sig_file.exists():
                sigs = np.load(str(sig_file), mmap_mode='r')
            elif shard.signatures is not None:
                sigs = shard.signatures
            if sigs is None or sigs.shape[0] == 0:
                continue

            # Distance L2 vectorisée: ||sigs[i] - q[j]||² pour tous i,j
            # = |sigs|²_row + |q|²_col - 2·sigs·q^T
            s = sigs.astype(np.float32)           # (M, D)
            q_all = all_sigs.astype(np.float32)   # (N, D)
            s_norm = np.sum(s**2, axis=1)         # (M,)
            q_norm = np.sum(q_all**2, axis=1)     # (N,)

            # Retrieval PAR BLOCS de requêtes : les matrices (M, N) complètes
            # explosent en mémoire (640 Mo par shard en 4K → 1,3 Go pour 2
            # shards). Un bloc (M, B=1024) = ~160 Mo, borné quelle que soit
            # la résolution (le goulot de l'encode 4K : 457 s pour 8 frames).
            BLOCK_Q = 1024
            for start in range(0, total_patches, BLOCK_Q):
                end = min(start + BLOCK_Q, total_patches)
                qb = q_all[start:end]                        # (B, D)
                cross = s @ qb.T                             # (M, B)
                dists = (s_norm[:, None] + q_norm[start:end][None, :]
                         - 2.0 * cross)                      # (M, B)

                min_idx_b = np.argmin(dists, axis=0)         # (B,)
                min_dist_b = dists[min_idx_b, np.arange(end - start)]  # (B,)

                better = min_dist_b < best_dist[start:end]
                best_dist[start:end][better] = min_dist_b[better]
                best_shard[start:end][better] = shard_idx
                best_idx[start:end][better] = min_idx_b[better]

        # Charger les pixels des meilleurs matchs (batch par shard)
        for sid in set(best_shard[best_shard >= 0]):
            mask = best_shard == sid
            shard = self.db._shards[int(sid)]
            pix_file = shard._path / 'pixels.npy' if shard._path else None
            pixels = None
            if pix_file and pix_file.exists():
                pixels = np.load(str(pix_file), mmap_mode='r')
            elif shard.pixels is not None:
                pixels = shard.pixels
            if pixels is not None:
                idxs = best_idx[mask]
                valid = (idxs >= 0) & (idxs < len(pixels))
                best_pixels[np.where(mask)[0][valid]] = pixels[idxs[valid]]

        # Header V2
        header = struct.pack(
            '<4sBHHHBB3s',
            self.V2_MAGIC, 2, ps, n_h, n_w,
            1, self.db.K, b'\x00\x00\x00',
        )

        # Encoder chaque patch
        payloads = []
        n_matched = 0
        for p in range(total_patches):
            patch = all_patches[p]
            dist = best_dist[p]

            if best_shard[p] < 0 or dist > self.match_threshold:
                # Pas de bon match → encoder directement
                raw_data = self._compress_patch_direct(patch)
                pkt = struct.pack('<HII', 0xFFFF, 0, len(raw_data)) + raw_data
            else:
                n_matched += 1
                matched = best_pixels[p]
                residual = patch.astype(np.int16) - matched.astype(np.int16)

                if np.all(residual == 0):
                    pkt = struct.pack('<HII', best_shard[p] & 0xFFFF, int(best_idx[p]), 0)
                else:
                    residual_data = self._compress_residual(residual)
                    pkt = struct.pack('<HII', best_shard[p] & 0xFFFF, int(best_idx[p]),
                                      len(residual_data))
                    pkt += residual_data
            payloads.append(pkt)

        bitstream = header + b''.join(payloads)
        self.encode_time = time.perf_counter() - t0
        raw_bytes = H * W * 3
        self.last_ratio = raw_bytes / len(bitstream) if len(bitstream) > 0 else 0
        self._last_match_rate = n_matched / max(total_patches, 1)
        return bitstream

    def encode_best(self, image: np.ndarray, concept: str = 'default',
                    measure: bool = True) -> Tuple[bytes, str]:
        """
        Sélecteur optimal par image : encode en V2 DICT et en FULL, garde
        le bitstream le plus petit (le mode le meilleur gagne, zéro perte).

        Le décodeur existant détecte le format par magic (HHD2 vs HHDC) —
        aucun changement de format, le bitstream choisi se décode tel quel
        avec decode_v2 / decode_full.

        Returns:
            (bitstream, mode) — mode ∈ {'V2_DICT', 'FULL'}
        """
        data_v2 = self.encode_v2(image, concept)
        data_full = self.encode_full(image, concept)
        if len(data_v2) <= len(data_full):
            return data_v2, 'V2_DICT'
        return data_full, 'FULL'

    def encode_select(self, image: np.ndarray, min_psnr: float = None,
                      concept: str = 'default') -> Tuple[bytes, str]:
        """
        Sélecteur à 3 modes : V2 DICT / FULL (bit-exact, PSNR ∞) + MODAL
        (troncature dorée P1, `hcv2_modal_codec`) — le MODAL n'est candidat
        que si son PSNR mesuré ≥ min_psnr (curseur de qualité ; None → exact
        uniquement, comportement d'encode_best). Le plus petit gagne.

        Returns:
            (bitstream, mode) — mode ∈ {'V2_DICT', 'FULL', 'MODAL'}
        """
        data_v2 = self.encode_v2(image, concept)
        data_full = self.encode_full(image, concept)
        best, mode = (data_v2, 'V2_DICT') if len(data_v2) <= len(data_full) \
            else (data_full, 'FULL')
        if min_psnr is not None:
            m = self._modal_helpers()
            try:
                blob = m.encode(image)['blob']
                rec = m.decode(blob)
                if m.psnr(image, rec) >= min_psnr and len(blob) + 4 < len(best):
                    return self.MODAL_MAGIC + blob, 'MODAL'
            except Exception:
                pass  # échec modal → exact (publié, jamais bloquant)
        return best, mode

    def decode_select(self, data: bytes, database=None) -> Tuple[np.ndarray, dict]:
        """Décode un bitstream du sélecteur (routage par magic :
        HCVM → modal, HHD2 → V2, sinon FULL)."""
        if data[:4] == self.MODAL_MAGIC:
            m = self._modal_helpers()
            return m.decode(data[4:]), {}
        if data[:4] == self.V2_MAGIC:
            return self.decode_v2(data, database=database)
        return self.decode_full(data)

    MODAL_MAGIC = b'HCVM'  # préfixe du mode MODAL (troncature dorée, P1)

    def decode_v2(self, data: bytes, database=None) -> Tuple[np.ndarray, dict]:
        """
        Décode un bitstream HHD2 avec dictionnaire partagé.

        Args:
            data: bytes — bitstream HHD2
            database: HarmonicDatabase (optionnel) — si None, fallback residual-only
        Returns:
            (image_rgb, metadata)
        """
        t0 = time.perf_counter()
        dctx = self._zstd_dctx

        if len(data) < HEADER_SIZE:
            raise ValueError(f"Bitstream trop court: {len(data)} bytes")

        magic, version, ps, n_h, n_w, flags, K, reserved = struct.unpack(
            '<4sBHHHBB3s', data[:HEADER_SIZE]
        )

        if magic != self.V2_MAGIC:
            raise ValueError(f"Magic V2 invalide: {magic!r}, attendu {self.V2_MAGIC!r}")

        final_h = n_h * ps
        final_w = n_w * ps
        image = np.zeros((final_h, final_w, 3), dtype=np.float32)
        weight = np.zeros((final_h, final_w, 1), dtype=np.float32)

        offset = HEADER_SIZE
        has_db = database is not None

        # Pass 1: collecter tous les patchs groupés par shard_id
        patches_by_shard = {}  # shard_id → [(i, j, patch_idx, residual_data_or_None)]
        
        for i in range(n_h):
            for j in range(n_w):
                if offset + 10 > len(data):
                    break
                shard_id, patch_idx, residual_len = struct.unpack(
                    '<HII', data[offset:offset + 10]
                )
                if shard_id > 32767:
                    shard_id = shard_id - 65536
                offset += 10

                if shard_id == -1:
                    # Raw patch: lire les données directement
                    if residual_len > 0:
                        if offset + residual_len > len(data):
                            break
                        raw_data = data[offset:offset + residual_len]
                        offset += residual_len
                        patch = self._decompress_patch(raw_data, ps, self._zstd_dctx)
                    else:
                        patch = np.zeros((ps, ps, 3), dtype=np.uint8)
                    # Appliquer immédiatement (pas de dépendance shard)
                    y0, x0 = i * ps, j * ps
                    image[y0:y0+ps, x0:x0+ps] = patch.astype(np.float32)
                    weight[y0:y0+ps, x0:x0+ps] = 1.0
                elif residual_len == 0:
                    # Exact match: besoin du shard pour lookup
                    patches_by_shard.setdefault(shard_id, []).append((i, j, patch_idx, None))
                else:
                    # Residual: lire les données
                    if offset + residual_len > len(data):
                        break
                    residual_data = data[offset:offset + residual_len]
                    offset += residual_len
                    patches_by_shard.setdefault(shard_id, []).append((i, j, patch_idx, residual_data))

        # Pass 2: pour chaque shard unique, charger une fois, traiter tous les patchs
        if has_db:
            for shard_id, patch_list in patches_by_shard.items():
                # Charger le shard une seule fois
                shard = database._shards[shard_id] if shard_id < len(database._shards) else None
                if shard is None:
                    continue
                was_loaded = shard.is_loaded
                if not was_loaded and shard._path:
                    shard.load(shard._path, mmap_pixels=True)

                for i, j, patch_idx, residual_data in patch_list:
                    if patch_idx >= len(shard.pixels):
                        continue
                    matched = shard.pixels[patch_idx]
                    if residual_data is None:
                        patch = matched
                    else:
                        residual = self._decompress_residual(residual_data, ps, dctx)
                        patch = np.clip(matched.astype(np.int16) + residual, 0, 255).astype(np.uint8)
                    y0, x0 = i * ps, j * ps
                    image[y0:y0+ps, x0:x0+ps] = patch.astype(np.float32)
                    weight[y0:y0+ps, x0:x0+ps] = 1.0

                if not was_loaded:
                    shard.unload()

        weight[weight < 1e-15] = 1.0
        image = image / weight
        image = np.clip(image, 0, 255).astype(np.uint8)

        self.decode_time = time.perf_counter() - t0
        meta = {
            'version': version,
            'patch_size': ps,
            'grid': (n_h, n_w),
            'shared_dict': has_db,
            'format': 'HHD2',
        }
        return image, meta

    # ── DCT helpers ──
    
    _dct_matrix_cache = {}  # {ps: (C, Ct)}
    
    @classmethod
    def _get_dct_matrix(cls, N: int):
        """Retourne la matrice DCT-II orthonormale N×N (cache)."""
        if N in cls._dct_matrix_cache:
            return cls._dct_matrix_cache[N]
        C = np.zeros((N, N), dtype=np.float64)
        for k in range(N):
            for i in range(N):
                C[k, i] = np.cos(np.pi * k * (2 * i + 1) / (2 * N))
        # Orthonormalisation
        C[0, :] *= np.sqrt(1.0 / N)
        C[1:, :] *= np.sqrt(2.0 / N)
        cls._dct_matrix_cache[N] = (C, C.T.copy())
        return cls._dct_matrix_cache[N]
    
    @classmethod
    def _dct_2d(cls, block: np.ndarray) -> np.ndarray:
        """DCT-II 2D orthonormale sur un bloc N×N."""
        N = block.shape[0]
        C, Ct = cls._get_dct_matrix(N)
        return C @ block.astype(np.float64) @ Ct
    
    @classmethod
    def _idct_2d(cls, coeffs: np.ndarray) -> np.ndarray:
        """DCT inverse 2D."""
        N = coeffs.shape[0]
        C, Ct = cls._get_dct_matrix(N)
        return Ct @ coeffs.astype(np.float64) @ C
    
    # ── Zigzag order (precomputed) ──
    
    _zigzag_cache = {}
    
    @classmethod
    def _zigzag_indices(cls, N: int):
        """Retourne les indices (i,j) en ordre zigzag pour une matrice N×N."""
        if N in cls._zigzag_cache:
            return cls._zigzag_cache[N]
        indices = []
        for s in range(2 * N - 1):
            if s % 2 == 0:
                for i in range(min(s, N - 1), max(-1, s - N), -1):
                    indices.append((i, s - i))
            else:
                for i in range(max(0, s - N + 1), min(s + 1, N)):
                    indices.append((i, s - i))
        cls._zigzag_cache[N] = indices
        return indices

    def _compress_residual(self, residual: np.ndarray) -> bytes:
        """Compresse un residual (ps, ps, 3) int16.

        Deux chemins, distingués par le premier octet du payload :
          mode 0x01 (quality ≥ 92 → _quant_step == 0) : Delta-H int32 + zstd
                 — EXACT (bit-à-bit, pas de DCT arrondie) ;
          mode 0x00 : DCT 2D + quantification + zigzag + RLE + zstd
                 — lossy (les arrondis de la DCT float64→int16 perdent ~1 LSB) ;
          mode 0x02 (golden_residual=True) : diffract + troncature dorée
                 1/(φ·m) + float16 + varint + zstd — lossy, zéro paramètre (P1).

        Format payload : [mode:1B] + 3 chunks [len:4B][zstd] (par canal).
        """
        if self._quant_step == 0:
            return self._encode_residual_exact(residual)
        if self.golden_residual:
            return self._encode_residual_golden(residual)

        cctx = self._zstd_cctx
        ps = residual.shape[0]
        N = ps

        # Quantification step
        # Pour residuals: step plus petit que pour les patches (le résidu est déjà petit)
        q = self._quant_step if self._quant_step > 0 else 1

        # Zigzag order
        zigzag = self._zigzag_indices(N)

        all_coeffs = []  # liste de int16 pour chaque canal

        for c in range(3):
            channel = residual[:, :, c].astype(np.float64)

            # DCT 2D
            dct_coeffs = self._dct_2d(channel)

            # Quantification
            dct_q = np.round(dct_coeffs / q).astype(np.int32)

            # Zigzag → supprimer les zéros avec RLE
            symbols = []  # (run_length, value)
            run = 0
            for idx_i, idx_j in zigzag:
                val = int(dct_q[idx_i, idx_j])
                if val == 0:
                    run += 1
                else:
                    symbols.append((run, val))
                    run = 0
            # End-of-block implicite: les derniers zéros sont omis

            # Encoder les symboles en bytes
            # Format: [n_symbols:2B][sym0_run:1B][sym0_val:2B signed]...
            buf = bytearray()
            buf.extend(struct.pack('<H', len(symbols)))
            for run_len, val in symbols:
                # Clamp run_length to 0-255
                run_byte = min(run_len, 255)
                # Store value as int16 (signed)
                buf.extend(struct.pack('<Bh', run_byte, val))
                # Si run > 255, on émet des (255, 0) supplémentaires
                extra_runs = run_len - 255
                while extra_runs > 0:
                    buf.extend(struct.pack('<Bh', min(extra_runs, 255), 0))
                    extra_runs -= 255

            # Compresser le buffer avec zstd
            compressed = cctx.compress(bytes(buf))
            all_coeffs.append(struct.pack('<I', len(compressed)) + compressed)

        return b'\x00' + b''.join(all_coeffs)

    def _encode_residual_exact(self, residual: np.ndarray) -> bytes:
        """Encode un residual SANS perte : Delta-H (différences horizontales)
        int32 + zstd par canal — bit-à-bit exact (aucune DCT arrondie).

        Format : [mode:1B = 0x01] + 3 chunks [len:4B][zstd].
        """
        cctx = self._zstd_cctx
        parts = [b'\x01']
        for c in range(3):
            channel = residual[:, :, c].astype(np.int32)
            delta = channel.copy()
            delta[:, 1:] -= channel[:, :-1]
            compressed = cctx.compress(delta.tobytes())
            parts.append(struct.pack('<I', len(compressed)) + compressed)
        return b''.join(parts)

    def _decode_residual_exact(self, data: bytes, ps: int, dctx) -> np.ndarray:
        """Décode un residual exact (mode 0x01) → (ps, ps, 3) int16."""
        residual = np.zeros((ps, ps, 3), dtype=np.int16)
        poff = 0
        for c in range(3):
            if poff + 4 > len(data):
                break
            chunk_len = struct.unpack('<I', data[poff:poff + 4])[0]
            poff += 4
            raw = dctx.decompress(data[poff:poff + chunk_len])
            poff += chunk_len
            delta = np.frombuffer(raw, dtype=np.int32).reshape(ps, ps).copy()
            np.cumsum(delta, axis=1, out=delta)  # Delta-H inverse (cumsum inplace)
            residual[:, :, c] = delta.astype(np.int16)
        return residual

    # ── helpers du codec modal HCV2 (P1 — réutilisés, pas réimplémentés) ──
    @staticmethod
    def _modal_helpers():
        """Import paresseux du codec modal (troncature dorée + varint)."""
        import sys as _sys
        from pathlib import Path as _Path
        _p = _Path(__file__).resolve().parent.parent / 'vital-ka' / 'core' / 'python'
        if str(_p) not in _sys.path:
            _sys.path.insert(0, str(_p))
        import hcv2_modal_codec as _m
        return _m

    def _encode_residual_golden(self, residual: np.ndarray) -> bytes:
        """Mode 0x02 — la troncature dorée (P1) sur le résidu du dictionnaire :
        diffract (FFT 2D) → poids de Parseval → seuil doré p > 1/(φ·m) →
        amplitudes float16 normalisées + phases float16 + varint (deltas
        d'index) → zstd. Lossy par construction (masse retenue ~0,87 —
        le théorème, zéro paramètre)."""
        m = self._modal_helpers()
        PHI = m.PHI
        parts = [b'\x02']
        for c in range(3):
            ch = residual[:, :, c].astype(np.float64)
            energy = float(np.sum(ch ** 2))
            if energy == 0.0:
                # Résidu nul (match exact) → chunk vide (le décodeur met 0)
                parts.append(struct.pack('<I', 0))
                continue
            Hf = np.fft.fft2(ch)
            mm = Hf.size
            p = np.abs(Hf) ** 2
            pn = p / p.sum()
            keep = pn > 1.0 / (PHI * mm)          # ← LE SEUIL DORÉ
            idx = np.nonzero(keep.ravel())[0]
            vals = Hf.ravel()[idx]
            mag = np.abs(vals)
            max_mag = float(mag.max()) if mag.size else 0.0
            blob = bytearray()
            blob += np.packbits(keep.ravel()).tobytes()
            if idx.size:
                deltas = np.diff(np.concatenate(([idx[0]], idx))).astype(np.uint32)
                blob += m._varint_encode(deltas)
            if mag.size:
                blob += (mag / max_mag).astype(np.float16).tobytes()
                blob += np.angle(vals).astype(np.float16).tobytes()
            blob += np.float64(max_mag).tobytes()
            comp = self._zstd_cctx.compress(bytes(blob))
            parts.append(struct.pack('<I', len(comp)) + comp)
        return b''.join(parts)

    def _decode_residual_golden(self, data: bytes, ps: int, dctx) -> np.ndarray:
        """Décode un residual doré (mode 0x02) → (ps, ps, 3) int16."""
        m = self._modal_helpers()
        residual = np.zeros((ps, ps, 3), dtype=np.int16)
        poff = 0
        for c in range(3):
            if poff + 4 > len(data):
                break
            chunk_len = struct.unpack('<I', data[poff:poff + 4])[0]
            poff += 4
            if chunk_len == 0:
                continue  # résidu nul (match exact) — canal à zéro
            raw = dctx.decompress(data[poff:poff + chunk_len])
            poff += chunk_len
            n = ps * ps
            mask = np.frombuffer(raw[:(n + 7) // 8], np.uint8)
            off = (n + 7) // 8
            n_keep = np.count_nonzero(np.unpackbits(mask)[:n])
            idx = np.zeros(0, np.uint32)
            if n_keep:
                deltas, used = m._varint_decode(raw[off:], n_keep)
                off += used
                idx = np.cumsum(deltas).astype(np.uint32)
            mags = np.frombuffer(raw[off:off + n_keep * 2], np.float16); off += n_keep * 2
            phases = np.frombuffer(raw[off:off + n_keep * 2], np.float16); off += n_keep * 2
            max_mag = float(np.frombuffer(raw[off:off + 8], np.float64)[0])
            H = np.zeros(n, complex)
            if n_keep:
                H[idx] = (mags.astype(np.float64) * max_mag) * \
                         np.exp(1j * phases.astype(np.float64))
            ch = np.fft.ifft2(H.reshape(ps, ps)).real
            residual[:, :, c] = np.clip(ch, -32768, 32767).astype(np.int16)
        return residual
    
    def _decompress_residual(self, data: bytes, ps: int, dctx) -> np.ndarray:
        """Décompresse un residual → (ps, ps, 3) int16.

        Le premier octet du payload indique le mode (voir _compress_residual) :
        0x01 → Delta-H exact (bit-à-bit), 0x02 → troncature dorée (P1),
        0x00 → DCT lossy.
        """
        if data and data[0] == 0x01:
            return self._decode_residual_exact(data[1:], ps, dctx)
        if data and data[0] == 0x02:
            return self._decode_residual_golden(data[1:], ps, dctx)
        data = data[1:] if data else data

        N = ps
        q = self._quant_step if self._quant_step > 0 else 1
        zigzag = self._zigzag_indices(N)
        residual = np.zeros((ps, ps, 3), dtype=np.int16)
        poff = 0
        
        for c in range(3):
            if poff + 4 > len(data):
                break
            chunk_len = struct.unpack('<I', data[poff:poff + 4])[0]
            poff += 4
            compressed = data[poff:poff + chunk_len]
            poff += chunk_len
            
            # Décompresser zstd
            raw = dctx.decompress(compressed)
            
            # Décoder les symboles RLE
            if len(raw) < 2:
                continue
            n_symbols = struct.unpack('<H', raw[:2])[0]
            offset = 2
            symbols = []
            for _ in range(n_symbols):
                if offset + 3 > len(raw):
                    break
                run_len, val = struct.unpack('<Bh', raw[offset:offset + 3])
                offset += 3
                symbols.append((run_len, val))
            
            # Reconstruire les coefficients DCT quantifiés
            dct_q = np.zeros((N, N), dtype=np.int32)
            sym_idx = 0
            zig_idx = 0
            while zig_idx < N * N and sym_idx < len(symbols):
                run_len, val = symbols[sym_idx]
                # Avancer de run_len zéros
                zig_idx += run_len
                if zig_idx >= N * N:
                    break
                # Placer la valeur
                i, j = zigzag[zig_idx]
                dct_q[i, j] = val
                zig_idx += 1
                sym_idx += 1
            
            # Déquantification
            dct_deq = dct_q.astype(np.float64) * q
            
            # IDCT 2D
            channel = self._idct_2d(dct_deq)
            
            # Clamp et stocker
            residual[:, :, c] = np.clip(np.round(channel), -32768, 32767).astype(np.int16)
        
        return residual
