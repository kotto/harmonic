#!/usr/bin/env python3
"""
Wrapper CLI pour HCVPrecompressedCodec
Appelé par api/precompressed_handler.js via spawn('python3', [...])
Retourne un JSON sur stdout.

Usage:
  python3 precompressed_wrapper.py --input image.jpg --output image.hcp --strategy AUTO
"""

import sys
import os
import json
import argparse
import time
import traceback

def _safe_path(p, must_exist=True):
    """Valide les chemins pour éviter path traversal"""
    real = os.path.realpath(p)
    
    allowed_dirs = [
        '/tmp/',
        '/var/tmp/',
        os.path.expanduser('~/tmp/'),
    ]
    
    if os.name == 'nt':
        import tempfile
        temp_dir = tempfile.gettempdir()
        allowed_dirs.extend([temp_dir + '\\', temp_dir + '/'])
    
    is_allowed = any(real.startswith(allowed_dir) for allowed_dir in allowed_dirs)
    
    if not is_allowed:
        raise ValueError(f"Chemin non autorisé : {p}")
    
    if must_exist and not os.path.exists(real):
        raise FileNotFoundError(f"Fichier introuvable : {real}")
    
    return real

def _err(msg):
    """Affiche une erreur en JSON et quitte"""
    print(json.dumps({"error": msg}), flush=True)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--strategy', default='AUTO',
                        choices=['AUTO', 'DIRECT', 'HYBRID', 'TRANSCODE'])
    parser.add_argument('--zstd-level', type=int, default=22)
    args = parser.parse_args()

    try:
        input_path = _safe_path(args.input, must_exist=True)
        output_path = _safe_path(args.output, must_exist=False)
    except (ValueError, FileNotFoundError) as e:
        _err(str(e))

    # Import du codec
    codec_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, codec_dir)

    try:
        from COMPRESSION_CAMERA.METHOD_2_SDI_LIKE_IMAGE_COMPRESSION.hcv_precompressed_codec import HCVPrecompressedCodec
    except ImportError as e:
        _err(f"Import codec échoué : {e}")

    try:
        import numpy as np
        from PIL import Image
    except ImportError as e:
        _err(f"Dépendance manquante : {e}")

    # Créer le codec
    try:
        codec = HCVPrecompressedCodec(
            strategy=args.strategy,
            zstd_level=args.zstd_level
        )
    except Exception as e:
        _err(f"Création codec échouée : {e}")

    # Encoder l'image
    try:
        t0 = time.time()
        compressed_data, metadata = codec.encode(input_path)
        elapsed = time.time() - t0

        # Sauvegarder le fichier compressé
        with open(output_path, 'wb') as f:
            f.write(compressed_data)

        # Calculer les statistiques
        original_size = os.path.getsize(input_path)
        compressed_size = len(compressed_data)
        ratio = original_size / compressed_size if compressed_size > 0 else 0
        savings = 100 * (1 - compressed_size / original_size) if original_size > 0 else 0

        # Retourner les résultats
        result = {
            "ok": True,
            "strategy": args.strategy,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "ratio": ratio,
            "savings": savings,
            "time": elapsed,
            "metadata": metadata
        }

        print(json.dumps(result), flush=True)

    except Exception as e:
        _err(f"Encodage échoué : {e}\n{traceback.format_exc()}")

if __name__ == '__main__':
    main()
