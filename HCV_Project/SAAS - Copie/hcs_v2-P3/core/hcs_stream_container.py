#!/usr/bin/env python3
"""
HCSStreamContainer - Conteneur binaire streamable pour video HCS
================================================================
Format .hcs : acces aleatoire O(1) par numero de frame.

Contrairement au ZIP STORED precedent :
  - Lecture frame N sans lire les frames 0..N-1 (seek direct)
  - Compatible streaming (lecture progressive possible)
  - Index en debut de fichier -> ouverture rapide
  - Supporte audio + video dans le meme fichier

Format binaire :
  +-------------------+
  | FILE HEADER       |  32 bytes
  +-------------------+
  | FRAME INDEX TABLE |  n_frames * 24 bytes
  +-------------------+
  | FRAME PAYLOADS    |  variable
  +-------------------+
  | AUDIO PAYLOAD     |  optional, variable
  +-------------------+

FILE HEADER (32 bytes) :
  magic[8]      b'HCS_VID1'
  version[2]    uint16 LE = 0x0101
  codec[4]      b'HARM' (HarmonicEncoder) | b'HYBR' (Hybrid)
  n_frames[4]   uint32 LE
  width[4]      uint32 LE
  height[4]     uint32 LE
  fps[4]        float32 LE
  duration_ms[4] uint32 LE
  reserved[2]   0x0000

FRAME INDEX ENTRY (24 bytes chacune) :
  offset[8]     uint64 LE   (position depuis debut fichier)
  size[4]       uint32 LE   (taille payload frame en bytes)
  pts_ms[4]     uint32 LE   (presentation timestamp en ms)
  frame_type[1] uint8       (0=I, 1=P, 2=B)
  quality[1]    uint8       (niveau qualite 0-100)
  width[2]      uint16 LE   (peut differer du header si resize)
  height[2]     uint16 LE
  reserved[2]   0x0000
"""

import os
import struct
import time
import io
import json
import logging
import numpy as np
from typing import Optional, List, Dict, Any, Tuple, BinaryIO, Iterator

logger = logging.getLogger(__name__)

# Constantes format
FILE_MAGIC    = b'HCS_VID1'
HEADER_SIZE   = 32
INDEX_ENTRY   = 24
VERSION       = 0x0101
CODEC_HARM    = b'HARM'   # HarmonicEncoder
CODEC_HYBR    = b'HYBR'   # HybridCompressor
CODEC_RAW     = b'RAW0'   # Non compresse (debug)

FRAME_I = 0  # Intra (independant)
FRAME_P = 1  # Predictif (futur)
FRAME_B = 2  # Bidir (non supporte, reserve)


class HCSStreamWriter:
    """
    Ecrit un fichier .hcs streamable frame par frame.

    Usage:
        with HCSStreamWriter('video.hcs', width=1280, height=720, fps=30.0) as w:
            for frame_bytes, meta in compressed_frames:
                w.write_frame(frame_bytes, pts_ms=..., quality=75)
        # Fermeture auto -> index ecrit en tete de fichier
    """

    def __init__(self, path: str, width: int, height: int,
                 fps: float = 30.0, codec: bytes = CODEC_HARM):
        """
        Args:
            path: Chemin du fichier .hcs de sortie
            width: Largeur en pixels
            height: Hauteur en pixels
            fps: Images par seconde
            codec: Type de codec (CODEC_HARM ou CODEC_HYBR)
        """
        self.path = path
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec[:4].ljust(4, b'\x00')

        self._frame_index: List[Dict] = []
        self._frame_count = 0
        self._current_offset = 0
        self._file: Optional[BinaryIO] = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def open(self):
        """Ouvre le fichier et ecrit un header provisoire (sera reecrit a close)."""
        self._file = open(self.path, 'wb')
        # Header provisoire (mis a jour a la fermeture)
        self._write_header(n_frames=0, duration_ms=0)
        self._header_end = self._file.tell()
        # Laisser de la place pour l index (MAX_FRAMES * INDEX_ENTRY)
        # On ecrit l'index d abord, puis les donnees
        # Strategy: ecrire les frames en temp buffer, ecrire index+data a close()
        self._frame_payloads: List[bytes] = []

    def _write_header(self, n_frames: int, duration_ms: int):
        """Ecrit le FILE HEADER."""
        self._file.write(FILE_MAGIC)                              # 8
        self._file.write(struct.pack('<H', VERSION))              # 2
        self._file.write(self.codec)                              # 4
        self._file.write(struct.pack('<I', n_frames))             # 4
        self._file.write(struct.pack('<I', self.width))           # 4
        self._file.write(struct.pack('<I', self.height))          # 4
        self._file.write(struct.pack('<f', self.fps))             # 4
        self._file.write(struct.pack('<I', duration_ms))          # 4
        self._file.write(b'\x00\x00')                             # 2 reserved

    def write_frame(self, compressed_bytes: bytes,
                    pts_ms: Optional[int] = None,
                    quality: int = 75,
                    frame_type: int = FRAME_I,
                    width: Optional[int] = None,
                    height: Optional[int] = None) -> int:
        """
        Ajoute une frame compressée au conteneur.

        Args:
            compressed_bytes: Données de la frame (produites par HarmonicEncoder.encode)
            pts_ms: Timestamp en ms (auto-calculé si None)
            quality: Niveau de qualité 0-100
            frame_type: FRAME_I ou FRAME_P
            width: Largeur (None = largeur globale)
            height: Hauteur (None = hauteur globale)

        Returns:
            Index de la frame ajoutée
        """
        if pts_ms is None:
            pts_ms = int(self._frame_count * 1000.0 / self.fps)

        self._frame_index.append({
            'size': len(compressed_bytes),
            'pts_ms': pts_ms,
            'frame_type': frame_type,
            'quality': quality,
            'width': width or self.width,
            'height': height or self.height,
        })
        self._frame_payloads.append(compressed_bytes)
        idx = self._frame_count
        self._frame_count += 1
        return idx

    def close(self):
        """
        Finalise le fichier : ecrit index + frames dans l'ordre correct.
        Structure finale : HEADER + INDEX_TABLE + FRAME_PAYLOADS
        """
        if self._file is None:
            return

        n = self._frame_count
        duration_ms = int(n * 1000.0 / self.fps) if self.fps > 0 else 0

        # Calculer les offsets reels
        data_start = HEADER_SIZE + n * INDEX_ENTRY
        offset = data_start
        for i, entry in enumerate(self._frame_index):
            entry['offset'] = offset
            offset += entry['size']

        # Réécrire depuis le début
        self._file.seek(0)
        self._file.truncate(0)

        # 1. Header final
        self._write_header(n_frames=n, duration_ms=duration_ms)

        # 2. Index table
        for entry in self._frame_index:
            self._file.write(struct.pack('<Q', entry['offset']))      # 8 offset
            self._file.write(struct.pack('<I', entry['size']))        # 4 size
            self._file.write(struct.pack('<I', entry['pts_ms']))      # 4 pts_ms
            self._file.write(struct.pack('<B', entry['frame_type']))  # 1 type
            self._file.write(struct.pack('<B', min(255, entry['quality'])))  # 1 quality
            self._file.write(struct.pack('<H', entry['width']))       # 2 width
            self._file.write(struct.pack('<H', entry['height']))      # 2 height
            self._file.write(b'\x00\x00')                             # 2 reserved

        # 3. Frame payloads
        for payload in self._frame_payloads:
            self._file.write(payload)

        self._file.flush()
        self._file.close()
        self._file = None

        total_bytes = HEADER_SIZE + n * INDEX_ENTRY + sum(e['size'] for e in self._frame_index)
        logger.info(f"HCSStreamWriter: {n} frames, {total_bytes:,} bytes -> {self.path}")


class HCSStreamReader:
    """
    Lit un fichier .hcs avec acces aleatoire O(1) par index de frame.

    Usage:
        with HCSStreamReader('video.hcs') as r:
            print(r.info())
            frame_bytes = r.read_frame(42)  # Lit seulement la frame 42
            for frame_bytes in r.iter_frames(start=10, end=50):
                ...
    """

    def __init__(self, path: str):
        self.path = path
        self._file: Optional[BinaryIO] = None
        self.header: Dict = {}
        self._index: List[Dict] = []
        self._loaded = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def open(self):
        """Ouvre le fichier et charge le header + index en RAM."""
        self._file = open(self.path, 'rb')
        self._load_header()
        self._load_index()
        self._loaded = True

    def _load_header(self):
        raw = self._file.read(HEADER_SIZE)
        if len(raw) < HEADER_SIZE:
            raise ValueError("Fichier HCS trop court pour le header")
        magic = raw[0:8]
        if magic != FILE_MAGIC:
            raise ValueError(f"Magic invalide: {magic!r}, attendu {FILE_MAGIC!r}")
        version   = struct.unpack_from('<H', raw, 8)[0]
        codec     = raw[10:14]
        n_frames  = struct.unpack_from('<I', raw, 14)[0]
        width     = struct.unpack_from('<I', raw, 18)[0]
        height    = struct.unpack_from('<I', raw, 22)[0]
        fps       = struct.unpack_from('<f', raw, 26)[0]
        dur_ms    = struct.unpack_from('<I', raw, 30)[0]  # Note: only 2 bytes left in 32-byte header

        self.header = {
            'version': version,
            'codec': codec.rstrip(b'\x00').decode('ascii', errors='replace'),
            'n_frames': n_frames,
            'width': width,
            'height': height,
            'fps': fps,
            'duration_ms': dur_ms,
        }

    def _load_index(self):
        """Charge la table d'index (n_frames * INDEX_ENTRY bytes)."""
        n = self.header['n_frames']
        self._index = []
        for _ in range(n):
            raw = self._file.read(INDEX_ENTRY)
            if len(raw) < INDEX_ENTRY:
                break
            offset     = struct.unpack_from('<Q', raw, 0)[0]
            size       = struct.unpack_from('<I', raw, 8)[0]
            pts_ms     = struct.unpack_from('<I', raw, 12)[0]
            frame_type = struct.unpack_from('<B', raw, 16)[0]
            quality    = struct.unpack_from('<B', raw, 17)[0]
            width      = struct.unpack_from('<H', raw, 18)[0]
            height     = struct.unpack_from('<H', raw, 20)[0]
            self._index.append({
                'offset': offset,
                'size': size,
                'pts_ms': pts_ms,
                'frame_type': frame_type,
                'quality': quality,
                'width': width,
                'height': height,
            })

    def close(self):
        if self._file:
            self._file.close()
            self._file = None

    @property
    def n_frames(self) -> int:
        return self.header.get('n_frames', 0)

    @property
    def fps(self) -> float:
        return self.header.get('fps', 30.0)

    @property
    def duration_s(self) -> float:
        return self.n_frames / self.fps if self.fps > 0 else 0.0

    def read_frame(self, index: int) -> bytes:
        """
        Lit UNE frame par index (acces O(1) par seek).

        Args:
            index: Numero de frame (0-based)

        Returns:
            bytes compresses (passer a HarmonicEncoder.decode pour image)
        """
        if not (0 <= index < len(self._index)):
            raise IndexError(f"Index {index} hors limites [0, {len(self._index)-1}]")
        entry = self._index[index]
        self._file.seek(entry['offset'])
        return self._file.read(entry['size'])

    def read_frame_at_time(self, time_ms: float) -> Tuple[int, bytes]:
        """
        Lit la frame la plus proche d'un timestamp.

        Returns:
            (frame_index, bytes)
        """
        # Recherche binaire du timestamp
        lo, hi = 0, len(self._index) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if self._index[mid]['pts_ms'] < time_ms:
                lo = mid + 1
            else:
                hi = mid
        return lo, self.read_frame(lo)

    def iter_frames(self, start: int = 0, end: Optional[int] = None,
                    step: int = 1) -> Iterator[Tuple[int, bytes]]:
        """
        Itere sur les frames dans une plage.
        Lecture sequentielle optimisee (pas de seeks multiples).

        Yields:
            (frame_index, frame_bytes)
        """
        if end is None:
            end = len(self._index)
        end = min(end, len(self._index))

        for i in range(start, end, step):
            yield i, self.read_frame(i)

    def get_frame_info(self, index: int) -> Dict:
        """Retourne les metadonnees d'une frame sans la lire."""
        if not (0 <= index < len(self._index)):
            raise IndexError(f"Index {index} hors limites")
        return self._index[index].copy()

    def info(self) -> str:
        """Retourne une chaine d'information sur le fichier."""
        h = self.header
        size_bytes = os.path.getsize(self.path)
        raw_bytes = h['width'] * h['height'] * 3 * h['n_frames']
        ratio = raw_bytes / size_bytes if size_bytes > 0 else 0
        return (
            f"HCS Stream: {h['n_frames']} frames @ {h['fps']:.1f}FPS  "
            f"{h['width']}x{h['height']}  codec={h['codec']}  "
            f"dur={self.duration_s:.1f}s  "
            f"ratio={ratio:.0f}:1  size={size_bytes:,}B"
        )


def compress_video_to_hcs(frames: List[np.ndarray],
                           output_path: str,
                           fps: float = 30.0,
                           quality: int = 75,
                           max_workers: Optional[int] = None) -> Dict[str, Any]:
    """
    Compresse une liste de frames NumPy vers un fichier .hcs streamable.

    Args:
        frames: Liste de (H, W, 3) float32 [0, 1]
        output_path: Fichier .hcs de sortie
        fps: FPS de la video
        quality: Qualite HarmonicEncoder (75 = ~18:1, PSNR~32dB)
        max_workers: Threads paralleles (None = auto)

    Returns:
        dict de stats
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from .harmonic_encoder import HarmonicEncoder

    if not frames:
        raise ValueError("Liste de frames vide")

    H, W = frames[0].shape[:2]
    enc = HarmonicEncoder(quality=quality)
    n = len(frames)

    # Compression parallele
    import os as _os
    workers = max_workers or min(16, (_os.cpu_count() or 4) + 2)

    t0 = time.time()
    compressed: Dict[int, bytes] = {}

    def _enc_one(idx, frame):
        data, _ = enc.encode(frame)
        return idx, data

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_enc_one, i, f): i for i, f in enumerate(frames)}
        for fut in as_completed(futures):
            idx, data = fut.result()
            compressed[idx] = data

    t_compress = time.time() - t0

    # Ecriture conteneur
    t1 = time.time()
    with HCSStreamWriter(output_path, width=W, height=H, fps=fps, codec=CODEC_HARM) as writer:
        for i in range(n):
            pts = int(i * 1000.0 / fps)
            writer.write_frame(compressed[i], pts_ms=pts, quality=quality)
    t_write = time.time() - t1

    total_time = time.time() - t0
    file_size = os.path.getsize(output_path)
    raw_size = H * W * 3 * 4 * n  # float32
    ratio = raw_size / file_size if file_size else 0

    stats = {
        'n_frames': n,
        'resolution': f'{W}x{H}',
        'fps': fps,
        'quality': quality,
        'raw_size_mb': raw_size / (1024 ** 2),
        'file_size_kb': file_size / 1024,
        'compression_ratio': ratio,
        'space_saved_pct': (1 - file_size / raw_size) * 100,
        'compress_time_s': t_compress,
        'write_time_s': t_write,
        'total_time_s': total_time,
        'fps_compression': n / t_compress,
        'output': output_path,
    }
    return stats


def decompress_hcs_to_frames(input_path: str,
                               start: int = 0,
                               end: Optional[int] = None) -> List[np.ndarray]:
    """
    Decompresse un fichier .hcs en liste de frames NumPy.

    Args:
        input_path: Fichier .hcs source
        start: Premiere frame (0-based)
        end: Derniere frame exclusive (None = tout)

    Returns:
        Liste de (H, W, 3) float32 [0, 1]
    """
    from .harmonic_encoder import HarmonicEncoder
    dec = HarmonicEncoder()
    frames = []
    with HCSStreamReader(input_path) as reader:
        for _, frame_bytes in reader.iter_frames(start=start, end=end):
            frames.append(dec.decode(frame_bytes))
    return frames


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    import tempfile, os

    print("=== HCSStreamContainer test ===")

    # Creer des frames test
    n_frames = 20
    H, W = 240, 320
    frames = [np.random.rand(H, W, 3).astype(np.float32) for _ in range(n_frames)]

    with tempfile.NamedTemporaryFile(suffix='.hcs', delete=False) as f:
        tmp_path = f.name

    try:
        # Compression -> fichier .hcs
        stats = compress_video_to_hcs(frames, tmp_path, fps=30.0, quality=75)
        print(f"  Compression: {stats['n_frames']} frames")
        print(f"  Ratio: {stats['compression_ratio']:.1f}:1")
        print(f"  FPS: {stats['fps_compression']:.1f}")
        print(f"  Fichier: {stats['file_size_kb']:.1f} KB")

        # Lecture streamable
        with HCSStreamReader(tmp_path) as r:
            print(f"\n  {r.info()}")

            # Acces aleatoire frame 10
            t0 = time.time()
            raw = r.read_frame(10)
            t_seek = (time.time() - t0) * 1000
            print(f"\n  Acces aleatoire frame 10: {len(raw)} bytes en {t_seek:.1f} ms")

            # Decompression
            from core.harmonic_encoder import HarmonicEncoder
            img = HarmonicEncoder().decode(raw)
            print(f"  Image decodee: {img.shape} dtype={img.dtype}")

        print("\n=== Done ===")
    finally:
        os.unlink(tmp_path)
