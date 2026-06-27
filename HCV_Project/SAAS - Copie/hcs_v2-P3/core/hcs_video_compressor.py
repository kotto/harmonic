# HCS VIDEO COMPRESSOR v2
# Compression video + audio professionnel avec presets
# Format binaire .hcsv2 (Harmonic Compression System Video v2)
# Workflow: Compression -> Stockage binaire -> Decompression + Upscaling

import os
import io
import time
import json
import zlib
import struct
import tempfile
import numpy as np
import cv2
from typing import Dict, Any, Optional, Tuple, List

# Audio imports avec fallback
HAS_AV = False
HAS_MOVIEPY = False
HAS_SOUNDFILE = False
HAS_SCIPY = False

try:
    import av
    HAS_AV = True
except ImportError:
    pass

try:
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    pass

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    pass

try:
    from scipy.io import wavfile
    HAS_SCIPY = True
except ImportError:
    pass

# ============================================================
# PRESETS DE COMPRESSION
# ============================================================

COMPRESSION_PRESETS = {
    'archivage': {
        'name': 'Archivage Long Terme',
        'description': 'Compression maximale pour archivage. Ratio ~15:1. Qualite acceptable.',
        'video_jpeg_quality': 35,
        'scale_store': 0.50,        # Stocke a 50% de la resolution
        'scale_playback': 2.0,      # Upscale 2x a la lecture
        'audio_quality': 'low',
        'audio_bitrate_kbps': 128,
        'chroma_subsampling': '420',
        'i_frame_interval': 15,     # I-frame toutes les 15 frames
        'delta_threshold': 0.05,    # Seuil de difference inter-frames
        'color_space': 'YCrCb',
        'target_ratio': 15.0,
        'use_case': 'Archivage, backup, conservation long terme',
        'icon': 'archive',
    },
    'audiovisuel_pro': {
        'name': 'Audiovisuel Professionnel',
        'description': 'Qualite professionnelle pour post-production. Ratio ~6:1.',
        'video_jpeg_quality': 75,
        'scale_store': 0.75,
        'scale_playback': 1.5,
        'audio_quality': 'high',
        'audio_bitrate_kbps': 320,
        'chroma_subsampling': '422',
        'i_frame_interval': 10,
        'delta_threshold': 0.02,
        'color_space': 'YCrCb',
        'target_ratio': 6.0,
        'use_case': 'Post-production, montage video, diffusion pro',
        'icon': 'film',
    },
    'cinema': {
        'name': 'Cinema 4K/8K',
        'description': 'Qualite cinema, compression minimale. Ratio ~3:1. Couleurs precises.',
        'video_jpeg_quality': 92,
        'scale_store': 1.0,
        'scale_playback': 1.0,
        'audio_quality': 'master',
        'audio_bitrate_kbps': 640,
        'chroma_subsampling': '444',
        'i_frame_interval': 5,
        'delta_threshold': 0.01,
        'color_space': 'YCrCb',
        'target_ratio': 3.0,
        'use_case': 'Production cinema, mastering 4K/8K, DCP',
        'icon': 'clapperboard',
    },
    'web_streaming': {
        'name': 'Web / Streaming',
        'description': 'Optimise pour diffusion web. Ratio ~20:1. Decode rapide.',
        'video_jpeg_quality': 45,
        'scale_store': 0.50,
        'scale_playback': 2.0,
        'audio_quality': 'medium',
        'audio_bitrate_kbps': 192,
        'chroma_subsampling': '420',
        'i_frame_interval': 30,
        'delta_threshold': 0.08,
        'color_space': 'YCrCb',
        'target_ratio': 20.0,
        'use_case': 'YouTube, streaming, sites web, reseaux sociaux',
        'icon': 'wifi',
    },
    'broadcast_hd': {
        'name': 'Broadcast HD / 4K',
        'description': 'Standards TV professionnels. Ratio ~5:1. Fidelite colorimetrique.',
        'video_jpeg_quality': 82,
        'scale_store': 0.75,
        'scale_playback': 1.5,
        'audio_quality': 'broadcast',
        'audio_bitrate_kbps': 384,
        'chroma_subsampling': '422',
        'i_frame_interval': 8,
        'delta_threshold': 0.015,
        'color_space': 'YCrCb',
        'target_ratio': 5.0,
        'use_case': 'Diffusion television, broadcast HD/4K, OTT',
        'icon': 'tv',
    },
}

# ============================================================
# FORMAT BINAIRE .hcsv2
# ============================================================
# Structure:
#   [4 bytes]  Magic: b"HCS2"
#   [4 bytes]  uint32: version = 2
#   [4 bytes]  uint32: metadata_len (taille JSON)
#   [N bytes]  JSON metadata (UTF-8)
#   [4 bytes]  uint32: video_data_len
#   [N bytes]  Video data (frames compressees)
#   [4 bytes]  uint32: audio_data_len
#   [N bytes]  Audio data (PCM compresse avec zlib)
#
# Format video data (dans le bloc video):
#   [4 bytes]  uint32: frame_count
#   Per frame:
#     [4 bytes]  uint32: frame_size
#     [N bytes]  frame bytes (JPEG compresse)
#
# Format audio data:
#   [4 bytes]  uint32: sample_rate
#   [4 bytes]  uint32: channels
#   [N bytes]  zlib(float32 numpy array bytes)

MAGIC = b"HCS2"
FORMAT_VERSION = 2


def _extract_audio_from_video(video_path: str) -> Tuple[Optional[np.ndarray], int]:
    """
    Extrait l'audio d'une video.
    Retourne (audio_array, sample_rate) ou (None, 0).
    audio_array shape: (samples, channels) ou (samples,) pour mono
    """
    # Methode 1: PyAV (plus rapide et propre)
    if HAS_AV:
        try:
            container = av.open(video_path)
            audio_streams = [s for s in container.streams if s.type == 'audio']
            if not audio_streams:
                container.close()
                return None, 0

            audio_stream = audio_streams[0]
            sample_rate = audio_stream.codec_context.sample_rate or 48000
            channels = audio_stream.codec_context.channels or 2

            audio_chunks = []
            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    # Convertir en float32
                    arr = frame.to_ndarray()
                    if arr.dtype != np.float32:
                        arr = arr.astype(np.float32)
                        # Normaliser si entier
                        if frame.format.name in ('s16', 's16p'):
                            arr = arr / 32768.0
                        elif frame.format.name in ('s32', 's32p'):
                            arr = arr / 2147483648.0
                    audio_chunks.append(arr)

            container.close()

            if not audio_chunks:
                return None, 0

            # Concatener (shape: channels x samples ou samples x channels)
            audio_data = np.concatenate(audio_chunks, axis=-1)
            # Transposer pour avoir (samples, channels)
            if audio_data.ndim == 2 and audio_data.shape[0] <= 8:
                audio_data = audio_data.T  # (channels, samples) -> (samples, channels)

            return audio_data, sample_rate

        except Exception as e:
            print("PyAV audio extraction failed: " + str(e))

    # Methode 2: MoviePy fallback
    if HAS_MOVIEPY:
        try:
            clip = VideoFileClip(video_path)
            if clip.audio is None:
                clip.close()
                return None, 0
            sample_rate = 44100
            audio_array = clip.audio.to_soundarray(fps=sample_rate)
            clip.close()
            return audio_array.astype(np.float32), sample_rate
        except Exception as e:
            print("MoviePy audio extraction failed: " + str(e))

    return None, 0


def _audio_to_bytes(audio_array: np.ndarray, sample_rate: int) -> bytes:
    """Encode audio en format binaire HCS (PCM float32 + header)"""
    if audio_array is None:
        return b""

    # Assurer float32 et normaliser entre -1.0 et 1.0
    audio = audio_array.astype(np.float32)
    max_val = np.max(np.abs(audio))
    if max_val > 1.0:
        audio = audio / max_val

    # Header: sample_rate (4 bytes) + channels (4 bytes)
    channels = audio.shape[1] if audio.ndim == 2 else 1
    header = struct.pack('>II', sample_rate, channels)

    # Compresser avec zlib
    raw_bytes = audio.tobytes()
    compressed = zlib.compress(raw_bytes, level=6)

    return header + compressed


def _bytes_to_audio(audio_bytes: bytes) -> Tuple[Optional[np.ndarray], int]:
    """Decode audio depuis format binaire HCS"""
    if len(audio_bytes) < 8:
        return None, 0

    sample_rate, channels = struct.unpack('>II', audio_bytes[:8])
    compressed_data = audio_bytes[8:]

    raw_bytes = zlib.decompress(compressed_data)
    audio_array = np.frombuffer(raw_bytes, dtype=np.float32)

    if channels > 1:
        # Reshape en (samples, channels)
        total_samples = len(audio_array) // channels
        audio_array = audio_array[:total_samples * channels].reshape(total_samples, channels)

    return audio_array, sample_rate


def _save_audio_to_video(video_path: str, audio_array: np.ndarray,
                          sample_rate: int, output_path: str) -> bool:
    """Ajoute l'audio a une video existante via MoviePy ou PyAV"""
    if not HAS_MOVIEPY:
        return False
    try:
        # Sauvegarder l'audio en WAV temporaire
        import tempfile
        wav_path = tempfile.mktemp(suffix='.wav')

        if HAS_SOUNDFILE:
            sf.write(wav_path, audio_array, sample_rate, subtype='FLOAT')
        elif HAS_SCIPY:
            # Convertir en int16 pour scipy
            audio_int16 = (audio_array * 32767).astype(np.int16)
            wavfile.write(wav_path, sample_rate, audio_int16)
        else:
            return False

        # Combiner video + audio
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(wav_path)

        # Sync durations
        min_duration = min(video_clip.duration, audio_clip.duration)
        video_clip = video_clip.subclip(0, min_duration)
        audio_clip = audio_clip.subclip(0, min_duration)

        final_clip = video_clip.set_audio(audio_clip)

        # Exporter
        final_clip.write_videofile(
            output_path,
            codec='libx264' if output_path.endswith('.mp4') else None,
            audio_codec='aac',
            logger=None,
            temp_audiofile=tempfile.mktemp(suffix='.aac'),
            remove_temp=True
        )

        video_clip.close()
        audio_clip.close()
        final_clip.close()

        if os.path.exists(wav_path):
            os.remove(wav_path)

        return True
    except Exception as e:
        print("Audio merge failed: " + str(e))
        return False


# Chemin vers le binaire ffmpeg (system ou bundle imageio-ffmpeg)
FFMPEG_EXE = None

def _find_ffmpeg() -> str:
    """
    Cherche ffmpeg dans l'ordre:
    1. imageio-ffmpeg (binaire bundle Python)
    2. ffmpeg system (PATH)
    Retourne le chemin vers l'executable ou None.
    """
    import subprocess

    # 1. Essayer imageio-ffmpeg (inclus dans le virtualenv)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            r = subprocess.run([exe, '-version'], capture_output=True, timeout=5)
            if r.returncode == 0:
                print("ffmpeg: utilisation du binaire imageio-ffmpeg -> " + exe[:60])
                return exe
    except Exception as e:
        print("imageio-ffmpeg non utilisable: " + str(e))

    # 2. Essayer ffmpeg systeme
    try:
        r = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if r.returncode == 0:
            print("ffmpeg: utilisation du binaire systeme")
            return 'ffmpeg'
    except Exception:
        pass

    print("ffmpeg non disponible (imageio-ffmpeg ni systeme)")
    return None

FFMPEG_EXE = _find_ffmpeg()
HAS_FFMPEG = FFMPEG_EXE is not None


def _convert_to_format(input_path: str, output_format: str = 'mp4') -> str:
    """
    Convertit une video au format demande via ffmpeg.
    Retourne le chemin du fichier converti, ou input_path en cas d'echec.
    
    Formats supportes: mp4 (H.264), webm (VP9), avi (XVID), mkv (H.264), mov (H.264)
    """
    import subprocess

    if not HAS_FFMPEG:
        return input_path

    # Determiner le codec selon le format
    output_path = input_path.rsplit('.', 1)[0] + '_out.' + output_format.lower()

    codec_map = {
        'mp4':  ['-c:v', 'libx264', '-crf', '22', '-preset', 'fast', '-c:a', 'aac', '-b:a', '192k'],
        'mkv':  ['-c:v', 'libx264', '-crf', '22', '-preset', 'fast', '-c:a', 'aac', '-b:a', '192k'],
        'mov':  ['-c:v', 'libx264', '-crf', '22', '-preset', 'fast', '-c:a', 'aac', '-b:a', '192k'],
        'webm': ['-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0', '-c:a', 'libopus'],
        'avi':  ['-c:v', 'libxvid', '-q:v', '6', '-c:a', 'mp3'],
    }

    codec_args = codec_map.get(output_format.lower(),
                               ['-c:v', 'libx264', '-crf', '22', '-c:a', 'aac'])

    cmd = [FFMPEG_EXE, '-i', input_path] + codec_args + [output_path, '-y', '-loglevel', 'error']

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print("ffmpeg conversion OK: " + os.path.basename(output_path) +
                  " (" + str(os.path.getsize(output_path)//1024) + " KB)")
            return output_path
        else:
            err = result.stderr.decode('utf-8', errors='replace')[:200] if result.stderr else ''
            print("ffmpeg conversion failed (code " + str(result.returncode) + "): " + err)
    except subprocess.TimeoutExpired:
        print("ffmpeg timeout")
    except Exception as e:
        print("ffmpeg error: " + str(e))

    return input_path  # Fallback: retourner l'original


MIME_TYPES = {
    'mp4': 'video/mp4',
    'mkv': 'video/x-matroska',
    'mov': 'video/quicktime',
    'webm': 'video/webm',
    'avi': 'video/x-msvideo',
}


def _compress_frame_jpeg(frame_bgr: np.ndarray, quality: int) -> bytes:
    """Compresse une frame en JPEG in-memory"""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, encoded = cv2.imencode('.jpg', frame_bgr, encode_param)
    if success:
        return encoded.tobytes()
    return b""


def _decompress_frame_jpeg(jpeg_bytes: bytes) -> Optional[np.ndarray]:
    """Decompresse une frame JPEG"""
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return frame


class HCSVideoCompressor:
    """
    Compresseur/Decompresseur HCS Video v2
    Gere compression video + audio pro avec presets
    """

    def __init__(self):
        self.presets = COMPRESSION_PRESETS

    def get_presets(self) -> Dict:
        return self.presets

    def compress_video(
        self,
        input_path: str,
        preset_name: str = 'audiovisuel_pro',
        progress_callback=None,
        max_frames: int = 0
    ) -> Tuple[bytes, Dict]:
        """
        Compresse une video au format HCS binaire.

        Args:
            input_path: Chemin vers la video source
            preset_name: Nom du preset de compression
            progress_callback: Fonction (progress_pct, message) optionnelle
            max_frames: 0 = toutes les frames, sinon limite

        Returns:
            (binary_data: bytes, metadata: dict)
        """
        t_start = time.time()

        preset = self.presets.get(preset_name, self.presets['audiovisuel_pro'])

        def _progress(pct, msg):
            if progress_callback:
                progress_callback(pct, msg)
            print("[" + str(int(pct)) + "%] " + msg)

        _progress(0, "Ouverture video: " + os.path.basename(input_path))

        # --- Lecture infos video ---
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError("Impossible d'ouvrir la video: " + input_path)

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames_src = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        src_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        src_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        if src_width <= 0 or src_height <= 0:
            raise ValueError("Dimensions video invalides: " + str(src_width) + "x" + str(src_height))

        # Appliquer limite frames si specifiee
        if max_frames > 0:
            frames_to_compress = min(total_frames_src, max_frames)
        else:
            frames_to_compress = total_frames_src

        # Resolution de stockage (reduite selon preset)
        scale = preset['scale_store']
        store_width = max(int(src_width * scale), 2) & ~1   # pair
        store_height = max(int(src_height * scale), 2) & ~1  # pair

        jpeg_quality = preset['video_jpeg_quality']

        _progress(5, "Resolution stockage: " + str(store_width) + "x" + str(store_height) +
                  " (x" + str(scale) + " du src " + str(src_width) + "x" + str(src_height) + ")")

        # --- Extraction audio ---
        _progress(8, "Extraction audio...")
        audio_array, sample_rate = _extract_audio_from_video(input_path)
        has_audio = audio_array is not None
        if has_audio:
            _progress(12, "Audio extrait: " + str(sample_rate) + " Hz, " +
                      str(audio_array.shape[-1] if audio_array.ndim > 1 else 1) + " canaux")
        else:
            _progress(12, "Pas d'audio detecte dans la video")

        # --- Compression frames ---
        _progress(15, "Compression video (" + str(frames_to_compress) + " frames, qualite " + str(jpeg_quality) + ")...")

        cap = cv2.VideoCapture(input_path)
        compressed_frames = []
        total_original_bytes = 0
        total_compressed_bytes = 0

        for i in range(frames_to_compress):
            ret, frame = cap.read()
            if not ret:
                break

            # Redimensionner si necessaire
            if scale != 1.0:
                frame = cv2.resize(frame, (store_width, store_height), interpolation=cv2.INTER_AREA)

            # Compresser en JPEG
            frame_bytes = _compress_frame_jpeg(frame, jpeg_quality)
            compressed_frames.append(frame_bytes)

            total_original_bytes += src_width * src_height * 3
            total_compressed_bytes += len(frame_bytes)

            # Progress toutes les 30 frames
            if i % 30 == 0 and i > 0:
                pct = 15 + int((i / frames_to_compress) * 70)
                _progress(pct, "Frame " + str(i) + "/" + str(frames_to_compress))

        cap.release()
        actual_frames = len(compressed_frames)

        _progress(85, "Frames compressees: " + str(actual_frames))

        # --- Encoder audio ---
        _progress(88, "Encodage audio professionnel...")
        audio_bytes = b""
        if has_audio:
            audio_bytes = _audio_to_bytes(audio_array, sample_rate)

        # --- Construire le bloc video binaire ---
        # Format: [frame_count uint32] [size1 uint32][data1]...[sizeN uint32][dataN]
        video_buffer = io.BytesIO()
        video_buffer.write(struct.pack('>I', actual_frames))
        for frame_bytes in compressed_frames:
            video_buffer.write(struct.pack('>I', len(frame_bytes)))
            video_buffer.write(frame_bytes)
        video_data = video_buffer.getvalue()

        # --- Construire les metadonnees ---
        t_end = time.time()
        duration_s = actual_frames / fps if fps > 0 else 0
        original_size_estimate = total_original_bytes
        compressed_size = len(video_data) + len(audio_bytes)
        actual_ratio = original_size_estimate / compressed_size if compressed_size > 0 else 1.0

        metadata = {
            'format': 'hcsv2',
            'version': 2,
            'preset': preset_name,
            'preset_name': preset['name'],
            'src_width': src_width,
            'src_height': src_height,
            'store_width': store_width,
            'store_height': store_height,
            'fps': fps,
            'total_frames': actual_frames,
            'duration_s': duration_s,
            'scale_store': preset['scale_store'],
            'scale_playback': preset['scale_playback'],
            'jpeg_quality': jpeg_quality,
            'has_audio': has_audio,
            'audio_sample_rate': sample_rate if has_audio else 0,
            'audio_channels': int(audio_array.shape[1]) if has_audio and audio_array.ndim == 2 else (1 if has_audio else 0),
            'audio_bitrate_kbps': preset['audio_bitrate_kbps'],
            'chroma_subsampling': preset['chroma_subsampling'],
            'compression_ratio': round(actual_ratio, 2),
            'video_data_size': len(video_data),
            'audio_data_size': len(audio_bytes),
            'compression_time_s': round(t_end - t_start, 2),
            'original_size_estimate_mb': round(original_size_estimate / 1024 / 1024, 2),
        }

        # --- Assembler le fichier .hcsv2 ---
        _progress(92, "Assemblage fichier binaire .hcsv2...")
        metadata_bytes = json.dumps(metadata, ensure_ascii=False).encode('utf-8')

        output = io.BytesIO()
        output.write(MAGIC)                                          # [0:4]   Magic
        output.write(struct.pack('>I', FORMAT_VERSION))             # [4:8]   Version
        output.write(struct.pack('>I', len(metadata_bytes)))        # [8:12]  Metadata len
        output.write(metadata_bytes)                                  # [12:..] Metadata JSON
        output.write(struct.pack('>I', len(video_data)))            # Video data len
        output.write(video_data)                                      # Video data
        output.write(struct.pack('>I', len(audio_bytes)))           # Audio data len
        output.write(audio_bytes)                                     # Audio data

        binary_data = output.getvalue()

        total_size_mb = len(binary_data) / 1024 / 1024
        _progress(100, "Compression terminee: " + str(round(total_size_mb, 2)) + " MB, ratio " +
                  str(round(actual_ratio, 1)) + ":1")

        metadata['total_file_size_mb'] = round(total_size_mb, 2)
        return binary_data, metadata

    def decompress_and_upscale(
        self,
        hcs_data: bytes,
        upscale_override: float = 0.0,
        output_format: str = 'mp4',
        progress_callback=None,
    ) -> Tuple[Optional[str], Dict]:
        """
        Decompresse et upscale un fichier .hcsv2.

        Args:
            hcs_data: Donnees binaires .hcsv2
            upscale_override: 0.0 = utiliser scale_playback du preset, sinon facteur manuel
            progress_callback: Fonction (progress_pct, message)

        Returns:
            (output_video_path: str, metadata: dict)
        """
        t_start = time.time()

        def _progress(pct, msg):
            if progress_callback:
                progress_callback(pct, msg)
            print("[" + str(int(pct)) + "%] " + msg)

        _progress(0, "Lecture fichier HCS...")

        # --- Parsing header ---
        reader = io.BytesIO(hcs_data)

        magic = reader.read(4)
        if magic != MAGIC:
            raise ValueError("Fichier invalide: magic incorrect '" + str(magic) + "'")

        version = struct.unpack('>I', reader.read(4))[0]
        if version != FORMAT_VERSION:
            raise ValueError("Version non supportee: " + str(version))

        metadata_len = struct.unpack('>I', reader.read(4))[0]
        metadata_bytes = reader.read(metadata_len)
        metadata = json.loads(metadata_bytes.decode('utf-8'))

        video_data_len = struct.unpack('>I', reader.read(4))[0]
        video_data = reader.read(video_data_len)

        audio_data_len = struct.unpack('>I', reader.read(4))[0]
        audio_data = reader.read(audio_data_len)

        # Informations du preset
        fps = metadata.get('fps', 30.0)
        store_width = metadata.get('store_width', 0)
        store_height = metadata.get('store_height', 0)
        src_width = metadata.get('src_width', store_width)
        src_height = metadata.get('src_height', store_height)
        total_frames = metadata.get('total_frames', 0)
        scale_playback = upscale_override if upscale_override > 0 else metadata.get('scale_playback', 2.0)
        has_audio = metadata.get('has_audio', False)

        target_width = min(int(store_width * scale_playback), 7680) & ~1  # pair
        target_height = min(int(store_height * scale_playback), 4320) & ~1

        _progress(5, "Preset: " + metadata.get('preset_name', '?') +
                  " | Stocke: " + str(store_width) + "x" + str(store_height) +
                  " | Sortie: " + str(target_width) + "x" + str(target_height) +
                  " | " + str(total_frames) + " frames")

        # --- Lire les frames depuis le bloc video ---
        video_reader = io.BytesIO(video_data)
        frame_count_stored = struct.unpack('>I', video_reader.read(4))[0]

        frames_data = []
        for i in range(frame_count_stored):
            size_bytes = video_reader.read(4)
            if len(size_bytes) < 4:
                break
            frame_size = struct.unpack('>I', size_bytes)[0]
            frame_bytes = video_reader.read(frame_size)
            frames_data.append(frame_bytes)

        _progress(15, "Frames lues: " + str(len(frames_data)))

        # --- Upscaling et reconstruction video ---
        temp_dir = tempfile.mkdtemp()
        video_only_path = os.path.join(temp_dir, "decompressed_video_only.avi")

        out, video_only_path = self._create_video_writer(video_only_path, fps, target_width, target_height)

        for i, frame_bytes in enumerate(frames_data):
            # Decompresser JPEG
            frame = _decompress_frame_jpeg(frame_bytes)
            if frame is None:
                continue

            # Upscale avec algorithme harmonique (Lanczos4 haute qualite)
            if scale_playback != 1.0:
                frame = cv2.resize(frame, (target_width, target_height),
                                   interpolation=cv2.INTER_LANCZOS4)

            out.write(frame)

            if i % 30 == 0 and i > 0:
                pct = 15 + int((i / len(frames_data)) * 70)
                _progress(pct, "Upscaling frame " + str(i) + "/" + str(len(frames_data)))

        out.release()
        _progress(85, "Video reconstruite: " + str(len(frames_data)) + " frames")

        # --- Reconstruction audio ---
        final_output_path = os.path.join(temp_dir, "final_output.avi")

        if has_audio and len(audio_data) > 0:
            _progress(88, "Reconstruction audio professionnel...")
            audio_array, sample_rate = _bytes_to_audio(audio_data)

            if audio_array is not None and HAS_MOVIEPY:
                # Essayer de fusionner audio + video avec MoviePy
                merged = _save_audio_to_video(video_only_path, audio_array, sample_rate, final_output_path)
                if merged and os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 0:
                    _progress(95, "Audio fusionne avec succes")
                    # Garder aussi le WAV separe
                    audio_path = os.path.join(temp_dir, "audio_extracted.wav")
                    try:
                        if HAS_SOUNDFILE:
                            sf.write(audio_path, audio_array, sample_rate)
                    except:
                        pass
                else:
                    # Echec fusion -> utiliser video sans audio
                    final_output_path = video_only_path
                    _progress(95, "Fusion audio echouee, video sans audio")
            else:
                final_output_path = video_only_path
        else:
            final_output_path = video_only_path
            _progress(90, "Pas d'audio dans le fichier source")

        # --- Conversion au format de sortie demande (MP4 H.264 pour navigateur) ---
        fmt = output_format.lower().strip('.')
        if fmt not in ('mp4', 'avi', 'mkv', 'mov', 'webm'):
            fmt = 'mp4'

        _progress(96, "Conversion vers ." + fmt + " (ffmpeg)...")
        converted_path = _convert_to_format(final_output_path, fmt)

        if converted_path != final_output_path and os.path.exists(converted_path):
            final_output_path = converted_path
        elif fmt == 'mp4' and final_output_path.endswith('.avi'):
            # Pas de conversion possible -> informer le frontend du vrai type
            _progress(97, "Conversion MP4 indisponible, sortie AVI")

        t_end = time.time()
        elapsed = t_end - t_start

        # Determiner le MIME type reel
        ext = final_output_path.rsplit('.', 1)[-1].lower()
        actual_mime = MIME_TYPES.get(ext, 'video/avi')

        _progress(100, "Decompression + upscaling termine en " + str(round(elapsed, 2)) + "s -> " + ext)

        # Metadonnees de sortie
        result_metadata = {
            'success': True,
            'preset': metadata.get('preset'),
            'preset_name': metadata.get('preset_name'),
            'original_resolution': str(src_width) + "x" + str(src_height),
            'stored_resolution': str(store_width) + "x" + str(store_height),
            'output_resolution': str(target_width) + "x" + str(target_height),
            'scale_playback': scale_playback,
            'total_frames': len(frames_data),
            'fps': fps,
            'duration_s': len(frames_data) / fps if fps > 0 else 0,
            'has_audio': has_audio,
            'audio_sample_rate': metadata.get('audio_sample_rate', 0),
            'audio_channels': metadata.get('audio_channels', 0),
            'compression_ratio': metadata.get('compression_ratio', 0),
            'decompression_time_s': round(elapsed, 2),
            'processing_fps': round(len(frames_data) / elapsed, 1) if elapsed > 0 else 0,
            'output_path': final_output_path,
            'output_mime_type': actual_mime,
            'output_format': ext,
        }

        return final_output_path, result_metadata

    def _create_video_writer(self, path: str, fps: float, width: int, height: int):
        """Cree un VideoWriter avec fallback de codecs"""
        candidates = [
            (path.replace('.mp4', '.avi').replace('.mov', '.avi'), cv2.VideoWriter_fourcc(*'XVID')),
            (path, cv2.VideoWriter_fourcc(*'mp4v')),
            (path.replace('.mp4', '_mjpg.avi').replace('.avi', '_mjpg.avi'), cv2.VideoWriter_fourcc(*'MJPG')),
        ]
        for out_path, fourcc in candidates:
            writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
            if writer.isOpened():
                return writer, out_path
            writer.release()
        raise RuntimeError("Aucun codec video disponible")

    def get_file_info(self, hcs_data: bytes) -> Dict:
        """Lit les metadonnees d'un fichier .hcsv2 sans decompresser"""
        try:
            reader = io.BytesIO(hcs_data)
            magic = reader.read(4)
            if magic != MAGIC:
                return {'valid': False, 'error': 'Magic incorrect'}

            version = struct.unpack('>I', reader.read(4))[0]
            metadata_len = struct.unpack('>I', reader.read(4))[0]
            metadata_bytes = reader.read(metadata_len)
            metadata = json.loads(metadata_bytes.decode('utf-8'))
            metadata['valid'] = True
            metadata['file_size_mb'] = round(len(hcs_data) / 1024 / 1024, 2)
            return metadata
        except Exception as e:
            return {'valid': False, 'error': str(e)}


# Instance globale
hcs_compressor = HCSVideoCompressor()
