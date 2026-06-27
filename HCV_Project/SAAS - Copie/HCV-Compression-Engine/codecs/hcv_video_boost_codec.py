#!/usr/bin/env python3
"""
HCV Video Boost — Compression Vidéo via Downscale Lanczos + H264 Re-encode
===========================================================================

Pipeline Vidéo:
  Source → Downscale Lanczos → H264 CRF → .hcvb

Pipeline Audio (CONSERVÉ NATIF):
  Source audio → Détection codec → stream copy si AAC/MP3/AC3
                                 → transcode AAC-LC 192k sinon
  L'audio est TOUJOURS préservé si présent dans la source.

Décompression:
  .hcvb vidéo → Upscale Lanczos → MP4 restauré (+ audio remuxé sans perte)

Champs retournés (encode + decode):
  has_audio, audio_codec, audio_bitrate, audio_channels, audio_method
  ('copy' = stream copy 0 perte | 'transcode' = AAC-LC 192k | 'none' = pas d'audio)
"""

import os
import subprocess
import time
import math
import struct
import json
import re
import tempfile
from typing import Tuple, Dict, Optional
from pathlib import Path


# ─── Trouver ffmpeg / ffprobe ──────────────────────────────────────────────

def _find_ffmpeg() -> Tuple[str, str]:
    """Trouve les chemins de ffmpeg et ffprobe."""
    # 1. imageio-ffmpeg (embarqué)
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ff):
            fp = ff.replace('ffmpeg', 'ffprobe')
            if os.path.exists(fp):
                return ff, fp
            return ff, ff  # fallback : on parsera stderr de ffmpeg -i
    except ImportError:
        pass

    # 2. PATH système + chemins absolus courants
    candidates = ['ffmpeg', 'ffmpeg.exe',
                  '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg',
                  '/opt/homebrew/bin/ffmpeg']
    for name in candidates:
        if not os.path.exists(name) and os.sep in name:
            continue
        try:
            r = subprocess.run([name, '-version'], capture_output=True, timeout=5)
            if r.returncode == 0:
                probe = name.replace('ffmpeg', 'ffprobe')
                try:
                    r2 = subprocess.run([probe, '-version'], capture_output=True, timeout=5)
                    if r2.returncode == 0:
                        return name, probe
                except FileNotFoundError:
                    pass
                return name, name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    raise RuntimeError("ffmpeg non trouvé. Installer: apt install ffmpeg  ou  pip install imageio-ffmpeg")


FFMPEG, FFPROBE = _find_ffmpeg()

# ─── Quality Presets ───────────────────────────────────────────────────────

QUALITY_PRESETS = {
    'ultra':    {'scale': 0.9,  'crf': 18, 'desc': 'Quasi-transparent'},
    'high':     {'scale': 0.75, 'crf': 23, 'desc': 'Haute qualité'},
    'balanced': {'scale': 0.6,  'crf': 26, 'desc': 'Equilibre ratio/qualité'},
    'compact':  {'scale': 0.5,  'crf': 28, 'desc': 'Compression maximale'},
}

# Codecs audio qui peuvent être stream-copié dans un container MP4 sans re-encodage
_COPY_COMPATIBLE_CODECS = {'aac', 'mp3', 'ac3', 'eac3', 'opus', 'alac', 'flac'}


# ─── Video + Audio Info ────────────────────────────────────────────────────

def get_video_info(path: str) -> Dict:
    """
    Récupère les infos vidéo ET audio via ffprobe (ou fallback ffmpeg -i).

    Retourne:
        width, height, fps, duration, size,
        has_audio, audio_codec, audio_bitrate_kbps, audio_channels,
        audio_sample_rate, audio_copy_safe
    """
    result = {
        'width': 0, 'height': 0, 'fps': 30.0, 'duration': 0.0,
        'size': os.path.getsize(path),
        'has_audio': False,
        'audio_codec': None,
        'audio_bitrate_kbps': None,
        'audio_channels': None,
        'audio_sample_rate': None,
        'audio_copy_safe': False,
    }

    # ── Essai 1: ffprobe JSON ──
    try:
        r = subprocess.run(
            [FFPROBE, '-v', 'quiet', '-print_format', 'json',
             '-show_format', '-show_streams', path],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            streams = data.get('streams', [])
            fmt = data.get('format', {})

            # Vidéo
            vs = next((s for s in streams if s.get('codec_type') == 'video'), {})
            if vs:
                result['width'] = int(vs.get('width', 0))
                result['height'] = int(vs.get('height', 0))
                rfr = vs.get('r_frame_rate', '30/1')
                try:
                    num, den = rfr.split('/')
                    result['fps'] = float(num) / float(den) if float(den) else 30.0
                except Exception:
                    result['fps'] = 30.0
            result['duration'] = float(fmt.get('duration', 0))

            # Audio
            as_ = next((s for s in streams if s.get('codec_type') == 'audio'), None)
            if as_:
                codec = as_.get('codec_name', '').lower()
                result['has_audio'] = True
                result['audio_codec'] = codec
                result['audio_channels'] = int(as_.get('channels', 2))
                result['audio_sample_rate'] = int(as_.get('sample_rate', 44100))
                # Bitrate: depuis le stream ou le format global
                br = as_.get('bit_rate') or fmt.get('bit_rate')
                if br:
                    try:
                        result['audio_bitrate_kbps'] = round(int(br) / 1000)
                    except Exception:
                        pass
                # copy safe = codec compatible MP4 sans re-encodage
                result['audio_copy_safe'] = codec in _COPY_COMPATIBLE_CODECS
            return result
    except Exception:
        pass

    # ── Fallback 2: parse stderr de ffmpeg -i ──
    try:
        r = subprocess.run([FFMPEG, '-i', path],
                           capture_output=True, text=True, timeout=10)
        info = r.stderr

        m = re.search(r'(\d{2,5})x(\d{2,5})', info)
        if m:
            result['width'] = int(m.group(1))
            result['height'] = int(m.group(2))
        m = re.search(r'(\d+\.?\d*)\s*(?:fps|tbr)', info)
        if m:
            result['fps'] = float(m.group(1))
        m = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', info)
        if m:
            result['duration'] = (int(m.group(1)) * 3600 + int(m.group(2)) * 60
                                  + int(m.group(3)) + int(m.group(4)) / 100)

        # Audio depuis stderr
        m = re.search(r'Audio:\s*(\w+)', info)
        if m:
            codec = m.group(1).lower()
            result['has_audio'] = True
            result['audio_codec'] = codec
            result['audio_copy_safe'] = codec in _COPY_COMPATIBLE_CODECS
            m2 = re.search(r'Audio:.*?(\d+)\s*Hz', info)
            if m2:
                result['audio_sample_rate'] = int(m2.group(1))
            m2 = re.search(r'Audio:.*?(\d+)\s*kb/s', info)
            if m2:
                result['audio_bitrate_kbps'] = int(m2.group(1))
    except Exception:
        pass

    return result


# ─── Audio encoding strategy ──────────────────────────────────────────────

def _audio_args(has_audio: bool, copy_safe: bool, bitrate: int = 96) -> list:
    """
    Retourne les arguments ffmpeg pour l'audio selon la stratégie.

    copy_safe=True  → '-c:a copy'         (stream copy, 0 perte, plus rapide)
    copy_safe=False → '-c:a aac -b:a Xk'  (transcode AAC, bitrate configurable)
    has_audio=False → '-an'               (pas d'audio, ne pas créer de piste vide)
    
    bitrate: bitrate AAC en kbps (défaut 96 pour bon compromis qualité/taille)
    """
    if not has_audio:
        return ['-an']
    if copy_safe:
        return ['-c:a', 'copy']
    return ['-c:a', 'aac', '-b:a', f'{bitrate}k', '-ar', '48000']


def _audio_method(has_audio: bool, copy_safe: bool) -> str:
    if not has_audio:
        return 'none'
    return 'copy' if copy_safe else 'transcode'


# ─── Core: Encode/Decode ──────────────────────────────────────────────────

class HCVVideoBoost:
    """
    Codec vidéo: Downscale Lanczos + H264 re-encode via ffmpeg.

    Encode: source.mp4 → downscale → H264 CRF → output.hcvb
    Decode: output.hcvb → upscale Lanczos → restored.mp4

    Audio: conservé natif (stream copy si possible, sinon AAC-LC 192k).

    Le fichier .hcvb est un MP4 standard précédé d'un header de 32 bytes
    contenant les métadonnées de restauration.
    """

    MAGIC = b'HCVB'
    # <4s B B H H H H I I 2s>
    # magic  ver qi  ow oh nw nh fps100 cmp_size reserved(2)
    _HEADER_FMT = '<4sBBHHHHII2s'
    HEADER_SIZE = struct.calcsize(_HEADER_FMT)  # = 26 bytes → padded to 32

    # On utilise un header fixe 32 bytes pour simplicité
    HEADER_PADDED = 32

    def __init__(self, quality: str = 'high', audio_bitrate: int = 96):
        assert quality in QUALITY_PRESETS, f"Quality: {list(QUALITY_PRESETS)}"
        self.quality = quality
        self.preset = QUALITY_PRESETS[quality]
        self.audio_bitrate = audio_bitrate  # kbps, défaut 96 pour bon compromis

    # ── helpers ──

    def _write_header(self, f_out, orig_w, orig_h, new_w, new_h, fps, compressed_video_size):
        qi = {'ultra': 0, 'high': 1, 'balanced': 2, 'compact': 3}[self.quality]
        hdr = struct.pack(self._HEADER_FMT,
                          self.MAGIC, 1, qi,
                          orig_w, orig_h, new_w, new_h,
                          int(fps * 100),
                          compressed_video_size,
                          b'\x00\x00')
        # Pad to 32 bytes
        f_out.write(hdr + b'\x00' * (self.HEADER_PADDED - len(hdr)))

    @staticmethod
    def _read_header(path: str) -> Dict:
        _FMT = '<4sBBHHHHII2s'
        _SZ = struct.calcsize(_FMT)
        with open(path, 'rb') as f:
            raw = f.read(32)
        magic, ver, qi, orig_w, orig_h, new_w, new_h, fps100, comp_size, _ = \
            struct.unpack(_FMT, raw[:_SZ])
        assert magic == b'HCVB', f"Not a .hcvb file (magic={magic})"
        quality = {0: 'ultra', 1: 'high', 2: 'balanced', 3: 'compact'}.get(qi, 'high')
        return {
            'orig_w': orig_w, 'orig_h': orig_h,
            'new_w': new_w, 'new_h': new_h,
            'fps': fps100 / 100.0,
            'comp_size': comp_size,
            'quality': quality,
        }

    @staticmethod
    def _calculate_target_resolution(orig_w: int, orig_h: int, max_w: int, max_h: int) -> Tuple[int, int]:
        """
        Calculate target resolution preserving original aspect ratio.
        
        Args:
            orig_w: Original video width
            orig_h: Original video height
            max_w: Maximum target width (e.g., 1920 for 1080p, 3840 for 4K)
            max_h: Maximum target height
            
        Returns:
            (target_w, target_h) preserving aspect ratio, clamped to max dimensions
        """
        # Calculate aspect ratios
        orig_ratio = orig_w / orig_h if orig_h > 0 else 1
        max_ratio = max_w / max_h if max_h > 0 else 1
        
        # Determine scaling factor to fit within max dimensions while preserving aspect ratio
        if orig_ratio > max_ratio:
            # Width is the limiting factor
            target_w = max_w
            target_h = int(max_w / orig_ratio)
        else:
            # Height is the limiting factor
            target_h = max_h
            target_w = int(max_h * orig_ratio)
        
        # Ensure dimensions are multiples of 2 (required by H.264)
        target_w = target_w - (target_w % 2)
        target_h = target_h - (target_h % 2)
        
        return (target_w, target_h)

    # ── encode ──

    def encode(self, input_path: str, output_path: str = None) -> Tuple[str, Dict]:
        """
        Encode une vidéo: downscale Lanczos + H264 re-encode.
        Audio: stream copy (si AAC/MP3/…) ou transcode AAC-LC 192k.

        Retourne (output_path, stats) avec stats incluant has_audio, audio_method, etc.
        """
        t0 = time.perf_counter()
        source_size = os.path.getsize(input_path)
        info = get_video_info(input_path)

        orig_w, orig_h = info['width'], info['height']
        scale = self.preset['scale']
        crf = self.preset['crf']

        new_w = max(16, int(orig_w * scale))
        new_h = max(16, int(orig_h * scale))
        new_w -= new_w % 2
        new_h -= new_h % 2

        if output_path is None:
            base = Path(input_path).stem
            output_path = f"{base}_hcvb_{self.quality}.hcvb"

        tmp_mp4 = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name

        # ── Stratégie: encoder vidéo seule d'abord, puis muxer l'audio séparément ──
        method = _audio_method(info['has_audio'], info['audio_copy_safe'])

        # Étape 1: encoder la vidéo sans audio (toujours fiable)
        tmp_video_only = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
        cmd_video = [
            FFMPEG, '-y', '-i', input_path,
            '-vf', f'scale={new_w}:{new_h}:flags=lanczos',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf),
            '-an',  # pas d'audio pour cette passe
            '-movflags', '+faststart', tmp_video_only
        ]
        r = subprocess.run(cmd_video, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            os.unlink(tmp_video_only)
            raise RuntimeError(f"ffmpeg video encode failed: {r.stderr[-500:]}")

        print(f"[ENCODE] Video-only pass OK: {os.path.getsize(tmp_video_only)} bytes")

        # Étape 2: transcoder l'audio vers le bitrate spécifié (toujours, même si source compatible)
        if info['has_audio']:
            print(f"[ENCODE] Transcoding audio to {self.audio_bitrate}k AAC...")
            cmd_mux = [
                FFMPEG, '-y',
                '-i', tmp_video_only,
                '-i', input_path,
                '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', f'{self.audio_bitrate}k', '-ar', '48000',
                '-movflags', '+faststart', tmp_mp4
            ]
            r = subprocess.run(cmd_mux, capture_output=True, text=True, timeout=120)

            if r.returncode != 0:
                # Fallback: vidéo sans audio
                print(f"[ENCODE] Audio transcode failed → video only (no audio)")
                print(f"[ENCODE] stderr: {r.stderr[-200:]}")
                import shutil
                shutil.copy2(tmp_video_only, tmp_mp4)
                method = 'none'
            else:
                print(f"[ENCODE] Audio transcoded OK to {self.audio_bitrate}k")
        else:
            # Pas d'audio: utiliser la vidéo seule
            import shutil
            shutil.copy2(tmp_video_only, tmp_mp4)
            method = 'none'

        try:
            os.unlink(tmp_video_only)
        except Exception:
            pass

        compressed_video_size = os.path.getsize(tmp_mp4)
        print(f"[ENCODE] tmp_mp4={tmp_mp4} size={compressed_video_size} audio_method={method}")

        # ── Écrire le container .hcvb: header(32B) + MP4 ──
        with open(output_path, 'wb') as f_out:
            self._write_header(f_out, orig_w, orig_h, new_w, new_h,
                               info['fps'], compressed_video_size)
            with open(tmp_mp4, 'rb') as src:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    f_out.write(chunk)

        os.unlink(tmp_mp4)

        final_size = os.path.getsize(output_path)
        elapsed = time.perf_counter() - t0

        # Audio bitrate pour les stats (si on a transcodé, utiliser self.audio_bitrate)
        audio_bitrate = info['audio_bitrate_kbps']
        if method == 'transcode':
            audio_bitrate = self.audio_bitrate
        elif method == 'none':
            audio_bitrate = None

        return output_path, {
            # Tailles
            'source_size': source_size,
            'compressed_size': final_size,
            'video_payload_size': compressed_video_size,
            'ratio_vs_source': round(source_size / final_size, 2) if final_size > 0 else 0,
            'savings_vs_source': round(100 * (1 - final_size / source_size), 1),
            # Vidéo
            'original_resolution': f'{orig_w}x{orig_h}',
            'compressed_resolution': f'{new_w}x{new_h}',
            'scale': scale,
            'crf': crf,
            'quality': self.quality,
            'fps': info['fps'],
            'duration': info['duration'],
            'encode_time': round(elapsed, 1),
            'smaller_than_source': final_size < source_size,
            # Audio ← NOUVEAUX CHAMPS pour le frontend
            'has_audio': method != 'none',
            'audio_present': method != 'none',
            'audio_method': method,                          # 'copy' | 'transcode' | 'none'
            'audio_codec': (info['audio_codec'] if method == 'copy'
                            else 'aac' if method == 'transcode' else None),
            'audio_codec_source': info['audio_codec'],       # codec original
            'audio_bitrate': audio_bitrate,
            'audio_channels': info['audio_channels'] if method != 'none' else None,
            'audio_sample_rate': info['audio_sample_rate'] if method != 'none' else None,
        }

    # ── decode ──

    def decode(self, input_path: str, output_path: str = None, target_resolution: str = None) -> Tuple[str, Dict]:
        """
        Décode un .hcvb: upscale Lanczos vers résolution cible (original, 1080p, 4K, 8K).
        Audio: remuxé depuis le container (stream copy, 0 re-encodage).

        Args:
            input_path: chemin du fichier .hcvb
            output_path: chemin du fichier MP4 de sortie (optionnel)
            target_resolution: 'original', '1080p', '4K', '8K', ou (w, h)

        Retourne (output_path, stats) avec infos audio complètes.
        """
        t0 = time.perf_counter()

        hdr = self._read_header(input_path)
        orig_w, orig_h = hdr['orig_w'], hdr['orig_h']
        quality = hdr['quality']

        # Extraire le MP4 embarqué
        tmp_mp4 = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
        with open(input_path, 'rb') as src:
            src.seek(self.HEADER_PADDED)
            with open(tmp_mp4, 'wb') as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)

        print(f"[DECODE] Extracted MP4={tmp_mp4} size={os.path.getsize(tmp_mp4)}")

        # Infos audio du MP4 extrait (conservé depuis l'encodage)
        tmp_info = get_video_info(tmp_mp4)

        if output_path is None:
            base = Path(input_path).stem
            output_path = f"{base}_restored.mp4"

        # Déterminer la résolution cible pour upscaling
        # IMPORTANT: préserver le format d'origine (aspect ratio)
        if target_resolution is None or target_resolution == 'original':
            target_w, target_h = orig_w, orig_h
        elif target_resolution == '1080p':
            # Calculer la résolution 1080p en conservant le ratio d'origine
            target_w, target_h = self._calculate_target_resolution(orig_w, orig_h, 1920, 1080)
        elif target_resolution == '4K':
            # Calculer la résolution 4K en conservant le ratio d'origine
            target_w, target_h = self._calculate_target_resolution(orig_w, orig_h, 3840, 2160)
        elif target_resolution == '8K':
            # Calculer la résolution 8K en conservant le ratio d'origine
            target_w, target_h = self._calculate_target_resolution(orig_w, orig_h, 7680, 4320)
        elif isinstance(target_resolution, (list, tuple)):
            target_w, target_h = target_resolution
        else:
            target_w, target_h = orig_w, orig_h

        # Dimensions de restauration (multiples de 2)
        rw = target_w - (target_w % 2)
        rh = target_h - (target_h % 2)

        # Stratégie audio pour la restauration:
        # L'audio dans tmp_mp4 est déjà AAC (ou copié depuis source).
        # On fait toujours stream copy ici → 0 re-encodage supplémentaire.
        has_audio = tmp_info['has_audio']
        audio_flags = _audio_args(has_audio, copy_safe=True)  # toujours copy au decode
        decode_audio_method = 'copy' if has_audio else 'none'

        # Optimisation: si aucun upscaling requis (résolution identique), stream copy vidéo
        stored_w = hdr['new_w']
        stored_h = hdr['new_h']
        needs_scale = (rw != stored_w or rh != stored_h)

        if not needs_scale:
            # Pas d'upscaling → stream copy vidéo (instantané)
            cmd = [
                FFMPEG, '-y', '-i', tmp_mp4,
                '-c:v', 'copy',
            ] + audio_flags + ['-movflags', '+faststart', output_path]
        else:
            # Upscaling requis: ultrafast (3-4× plus rapide que fast) + bicubic
            # -threads 0 = utiliser tous les CPU disponibles
            cmd = [
                FFMPEG, '-y', '-threads', '0', '-i', tmp_mp4,
                '-vf', f'scale={rw}:{rh}:flags=bicubic',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '17',
                '-threads', '0',
            ] + audio_flags + ['-movflags', '+faststart', output_path]

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if r.returncode != 0:
            print(f"[DECODE] Audio copy failed → AAC transcode")
            print(f"[DECODE] stderr: {r.stderr[-200:]}")
            decode_audio_method = 'transcode'
            if not needs_scale:
                cmd = [
                    FFMPEG, '-y', '-i', tmp_mp4,
                    '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart', output_path
                ]
            else:
                cmd = [
                    FFMPEG, '-y', '-threads', '0', '-i', tmp_mp4,
                    '-vf', f'scale={rw}:{rh}:flags=bicubic',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '17',
                    '-threads', '0',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart', output_path
                ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if r.returncode != 0:
            # Dernier recours: vidéo seule
            print(f"[DECODE] Audio failed → video only")
            decode_audio_method = 'none'
            if not needs_scale:
                cmd = [FFMPEG, '-y', '-i', tmp_mp4, '-c:v', 'copy', '-an',
                       '-movflags', '+faststart', output_path]
            else:
                cmd = [
                    FFMPEG, '-y', '-threads', '0', '-i', tmp_mp4,
                    '-vf', f'scale={rw}:{rh}:flags=bicubic',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '17',
                    '-threads', '0', '-an', '-movflags', '+faststart', output_path
                ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                os.unlink(tmp_mp4)
                raise RuntimeError(f"ffmpeg decode failed: {r.stderr[-500:]}")

        os.unlink(tmp_mp4)

        elapsed = time.perf_counter() - t0
        restored_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        return output_path, {
            'original_resolution': f'{orig_w}x{orig_h}',
            'target_resolution': f'{rw}x{rh}',
            'restored_resolution': f'{rw}x{rh}',
            'quality': quality,
            'restored_size': restored_size,
            'hcvb_size': os.path.getsize(input_path),
            'decode_time': round(elapsed, 1),
            # Audio ← NOUVEAUX CHAMPS
            'has_audio': decode_audio_method != 'none',
            'audio_present': decode_audio_method != 'none',
            'audio_method': decode_audio_method,
            'audio_codec': tmp_info['audio_codec'] if decode_audio_method != 'none' else None,
            'audio_bitrate': tmp_info['audio_bitrate_kbps'],
            'audio_channels': tmp_info['audio_channels'],
            'audio_sample_rate': tmp_info['audio_sample_rate'],
        }


# ─── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    print(f"ffmpeg:  {FFMPEG}")
    print(f"ffprobe: {FFPROBE}")
    print()

    video = 'B3.mp4'
    if not os.path.exists(video):
        print(f"Video {video} not found")
        sys.exit(1)

    source_size = os.path.getsize(video)
    info = get_video_info(video)
    print(f"Source: {video}")
    print(f"  Taille:        {source_size:,} bytes ({source_size/1024/1024:.2f} MB)")
    print(f"  Résolution:    {info['width']}x{info['height']}")
    print(f"  FPS:           {info['fps']:.2f}")
    print(f"  Durée:         {info['duration']:.1f}s")
    print(f"  Audio:         {'OUI' if info['has_audio'] else 'NON'}")
    if info['has_audio']:
        print(f"  Audio codec:   {info['audio_codec']}")
        print(f"  Audio bitrate: {info['audio_bitrate_kbps']} kbps")
        print(f"  Audio canaux:  {info['audio_channels']}")
        print(f"  Copy safe:     {'OUI' if info['audio_copy_safe'] else 'NON (transcode nécessaire)'}")
    print()

    for quality in ['ultra', 'high', 'balanced', 'compact']:
        preset = QUALITY_PRESETS[quality]
        print(f"--- {quality.upper()} (scale={preset['scale']}, crf={preset['crf']}) ---")

        codec = HCVVideoBoost(quality=quality)
        out_hcvb = f'_test_{Path(video).stem}_{quality}.hcvb'
        out_mp4  = f'_test_{Path(video).stem}_{quality}_restored.mp4'

        try:
            # Encode
            _, enc = codec.encode(video, out_hcvb)
            print(f"  Source:         {enc['source_size']:>12,} bytes")
            print(f"  Compressé:      {enc['compressed_size']:>12,} bytes")
            print(f"  Ratio:          {enc['ratio_vs_source']}:1")
            print(f"  Économie:       {enc['savings_vs_source']}%")
            print(f"  Résolution:     {enc['original_resolution']} → {enc['compressed_resolution']}")
            print(f"  Temps encode:   {enc['encode_time']}s")
            print(f"  Audio présent:  {enc['has_audio']}")
            print(f"  Audio méthode:  {enc['audio_method']}")
            print(f"  Audio codec:    {enc['audio_codec']}")
            print(f"  Audio bitrate:  {enc['audio_bitrate']} kbps")
            print(f"  Audio canaux:   {enc['audio_channels']}")

            # Decode
            _, dec = codec.decode(out_hcvb, out_mp4)
            print(f"  Restauré:       {dec['restored_size']:>12,} bytes")
            print(f"  Temps decode:   {dec['decode_time']}s")
            print(f"  Audio restauré: {dec['has_audio']}")
            print(f"  Audio méthode decode: {dec['audio_method']}")

            # Cleanup
            for p in [out_hcvb, out_mp4]:
                if os.path.exists(p):
                    os.unlink(p)

        except Exception as e:
            print(f"  ERREUR: {e}")
            import traceback; traceback.print_exc()

        print()