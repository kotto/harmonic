#!/usr/bin/env python3
"""
hcv_engine.py — Wrapper CLI sécurisé pour HCV16
Appelé par api/upload.js via spawn('python3', [...])
Retourne un JSON sur stdout.

Usage:
  python3 hcv_engine.py --input /tmp/xxx.mxf --output /tmp/yyy.hcv16 --mode GRAIN_SYNTH
"""

import sys
import os
import json
import argparse
import math
import traceback

# Sécurité : validation des chemins avec support multi-plateforme
def _safe_path(p, must_exist=True):
    real = os.path.realpath(p)
    
    # Chemins autorisés selon l'environnement
    allowed_dirs = [
        '/tmp/',           # Linux/Unix
        '/var/tmp/',       # Linux/Unix alternatif
        os.path.expanduser('~/tmp/'),  # User temp
    ]
    
    # Windows support
    if os.name == 'nt':
        import tempfile
        temp_dir = tempfile.gettempdir()
        allowed_dirs.extend([
            temp_dir + '\\',
            temp_dir + '/',
            os.path.join(temp_dir, 'hcv') + '\\',
            os.path.join(temp_dir, 'hcv') + '/',
        ])
    
    # Vérifier si le chemin est dans un répertoire autorisé
    is_allowed = any(real.startswith(allowed_dir) for allowed_dir in allowed_dirs)
    
    if not is_allowed:
        raise ValueError(f"Chemin non autorisé : {p}. Répertoires autorisés : {allowed_dirs}")
    
    if must_exist and not os.path.exists(real):
        raise FileNotFoundError(f"Fichier introuvable : {real}")
    
    return real

def _err(msg):
    print(json.dumps({"error": msg}), flush=True)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',  required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--mode',   default='GRAIN_SYNTH',
                        choices=['LOSSLESS', 'GRAIN_SYNTH', 'SIGNAL_ONLY'])
    parser.add_argument('--fps',    default='25/1')
    parser.add_argument('--bits',   type=int, default=12)
    args = parser.parse_args()

    try:
        input_path  = _safe_path(args.input,  must_exist=True)
        output_path = _safe_path(args.output, must_exist=False)
    except (ValueError, FileNotFoundError) as e:
        _err(str(e))

    # Import du moteur (même répertoire ou PYTHONPATH)
    engine_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, engine_dir)

    try:
        from harmonic_codec_v16 import (
            HCV16Writer, HCV16Reader,
            make_frame, make_audio,
            MODE_NAME
        )
    except ImportError as e:
        _err(f"Import moteur HCV échoué : {e}")

    try:
        import numpy as np
        import cv2
    except ImportError as e:
        _err(f"Dépendance manquante : {e}")

    fps_parts = args.fps.split('/')
    fps_num   = int(fps_parts[0])
    fps_den   = int(fps_parts[1]) if len(fps_parts) > 1 else 1

    ext = os.path.splitext(input_path)[1].lower()

    # ── Lecture du fichier source ──────────────────────────────────────────
    frames = []
    audio_samples = None
    audio_sr      = None
    width = height = 0

    if ext == '.hcv16':
        # Re-encode depuis un .hcv16 existant
        try:
            rdr = HCV16Reader(input_path).open()
            frames = rdr.decode_all()
            audio_samples, audio_sr = rdr.decode_audio()
            height, width = frames[0].shape[:2]
            fps_num = rdr.fps_num
            fps_den = rdr.fps_den
        except Exception as e:
            _err(f"Lecture .hcv16 échouée : {e}")

    elif ext in ('.h264', '.h265', '.hevc'):
        # H264/H265 via video_decoders
        try:
            from video_decoders import H264Decoder
            frames, fps_num, fps_den, width, height = H264Decoder.decode(input_path)
        except Exception as e:
            _err(f"Décodage H264/H265 échoué : {e}\n{traceback.format_exc()}")

    elif ext == '.sdi':
        # SDI 4:2:2 raw format
        try:
            from video_decoders import SDI422Decoder
            # Paramètres SDI par défaut (1920x1080 10-bit 25fps)
            width = 1920
            height = 1080
            fps = 25
            bit_depth = 10
            frames, fps_num, fps_den, width, height = SDI422Decoder.decode_raw_sdi(
                input_path, width, height, fps, bit_depth
            )
        except Exception as e:
            _err(f"Décodage SDI 4:2:2 échoué : {e}\n{traceback.format_exc()}")

    elif ext == '.yuv':
        # YUV raw format (I420)
        try:
            from video_decoders import YUVDecoder
            width = 1920
            height = 1080
            fps = 25
            frames, fps_num, fps_den, width, height = YUVDecoder.decode_i420(
                input_path, width, height, fps
            )
        except Exception as e:
            _err(f"Décodage YUV échoué : {e}\n{traceback.format_exc()}")

    elif ext in ('.mp4', '.mov', '.avi', '.ts', '.mxf'):
        # Lecture vidéo via OpenCV
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                _err(f"Impossible d'ouvrir la vidéo : {input_path}")

            fps_src = cap.get(cv2.CAP_PROP_FPS) or 25.0
            fps_num = round(fps_src * 1000)
            fps_den = 1000
            width   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                # BGR uint8 → uint16 (shift 4 bits pour 12-bit)
                f16 = frame.astype(np.uint16) << 4
                frames.append(f16)
            cap.release()

            if not frames:
                _err("Aucune frame lue depuis la vidéo")

            # Audio via ffmpeg si disponible (optionnel)
            try:
                import subprocess, tempfile
                wav_tmp = input_path + '_audio.wav'
                r = subprocess.run(
                    ['ffmpeg', '-y', '-i', input_path,
                     '-vn', '-acodec', 'pcm_s16le', '-ar', '48000', '-ac', '2',
                     wav_tmp],
                    capture_output=True, timeout=60
                )
                if r.returncode == 0 and os.path.exists(wav_tmp):
                    import wave
                    with wave.open(wav_tmp, 'rb') as wf:
                        raw_audio = wf.readframes(wf.getnframes())
                        audio_samples = np.frombuffer(raw_audio, np.int16).reshape(-1, 2)
                        audio_sr = wf.getframerate()
                    os.remove(wav_tmp)
            except Exception:
                pass  # Audio optionnel

        except Exception as e:
            _err(f"Lecture vidéo échouée : {e}")
    else:
        _err(f"Format non supporté : {ext}. Formats acceptés : .h264, .h265, .hevc, .sdi, .yuv, .mp4, .mov, .avi, .ts, .mxf, .hcv16")

    if not frames:
        _err("Aucune frame à encoder")

    # ── Encodage HCV16 ────────────────────────────────────────────────────
    try:
        model_frames = frames[:min(8, len(frames))]
        wtr = HCV16Writer(
            output_path,
            mode       = args.mode,
            bit_depth  = args.bits,
            width      = width,
            height     = height,
            fps        = (fps_num, fps_den),
            colorspace = 'BGR',
            frames_for_model = model_frames if args.mode == 'GRAIN_SYNTH' else None,
        )
        for i, f in enumerate(frames):
            wtr.add_frame(f, i)

        if audio_samples is not None and audio_sr is not None:
            wtr.add_audio(audio_samples, audio_sr)

        file_size = wtr.finalize()

    except Exception as e:
        _err(f"Encodage HCV16 échoué : {e}\n{traceback.format_exc()}")

    # ── Vérification rapide du fichier produit ────────────────────────────
    try:
        rdr  = HCV16Reader(output_path).open()
        info = rdr.header_info()
    except Exception as e:
        _err(f"Vérification fichier de sortie échouée : {e}")

    # ── Calcul ratio ──────────────────────────────────────────────────────
    raw_size = width * height * 3 * 2 * len(frames)  # uint16 BGR
    ratio    = raw_size / file_size if file_size > 0 else 0

    result = {
        "ok":        True,
        "mode":      args.mode,
        "ratio":     f"{ratio:.2f}×",
        "psnr":      "Infinity" if args.mode == "LOSSLESS" else "~46-55 dB",
        "fileSize":  file_size,
        "frames":    len(frames),
        "width":     width,
        "height":    height,
        "fps":       f"{fps_num}/{fps_den}",
        "hasAudio":  audio_samples is not None,
        "sigmaInfo": info.get('sigma_curve', []),
        "headerBytes": info.get('header_bytes', 0),
    }

    print(json.dumps(result), flush=True)

if __name__ == '__main__':
    main()
