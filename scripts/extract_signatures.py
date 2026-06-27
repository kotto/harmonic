#!/usr/bin/env python3
"""
Extraction des signatures 11D depuis un corpus audio
=====================================================
Parcourt récursivement les fichiers WAV/MP3/FLAC, extrait
les 11 dimensions harmoniques via Parselmouth, et sauvegarde
en JSON incrémental (toutes les 100 signatures).

Usage :
    python scripts/extract_signatures.py data/corpus/ljspeech/LJSpeech-1.1/wavs
    python scripts/extract_signatures.py data/corpus --output data/voice_signatures/corpus_signatures.json
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List

# Ajouter le répertoire racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    parser = argparse.ArgumentParser(description="Extraction signatures vocales 11D")
    parser.add_argument('input_dir', type=str, help='Repertoire de fichiers audio')
    parser.add_argument('--output', type=str, default='data/voice_signatures/corpus_signatures.json',
                        help='Fichier JSON de sortie')
    parser.add_argument('--max', type=int, default=0, help='Max fichiers (0=tous)')
    parser.add_argument('--batch-save', type=int, default=100,
                        help='Sauvegarde toutes les N signatures')
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Trouver tous les fichiers audio (avec déduplication)
    audio_exts = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac'}
    audio_files_set = set()
    for ext in audio_exts:
        for f in input_path.rglob(f'*{ext}'):
            audio_files_set.add(f)
        for f in input_path.rglob(f'*{ext.upper()}'):
            audio_files_set.add(f)
    audio_files = sorted(audio_files_set)

    if args.max > 0:
        audio_files = audio_files[:args.max]

    total = len(audio_files)
    print(f"Fichiers trouves: {total}")
    print(f"Sortie: {output_path}")
    print(f"Demarrage extraction...")

    # Initialiser l'extracteur
    from engine.voice_signature_extractor import VoiceSignatureExtractor
    extractor = VoiceSignatureExtractor()

    signatures = []
    errors = 0
    t_start = time.time()

    for i, f in enumerate(audio_files):
        try:
            sig = extractor.extract(str(f))
            signatures.append({
                'file': str(f),
                'filename': f.name,
                'signature_11d': sig.to_dict(),
                'raw_values': sig.raw_values,
                'duration': sig.duration_seconds,
            })
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  [ERROR] {f.name}: {e}")

        # Sauvegarde incrémentale
        if (i + 1) % args.batch_save == 0:
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate if rate > 0 else 0
            print(f"  [{i+1}/{total}] {i+1-total*errors/total:.0f} ok, "
                  f"{errors} err, {elapsed:.0f}s, ETA {eta:.0f}s...")

            with open(output_path, 'w', encoding='utf-8') as out:
                json.dump(signatures, out, indent=2, ensure_ascii=False)

    # Sauvegarde finale
    with open(output_path, 'w', encoding='utf-8') as out:
        json.dump(signatures, out, indent=2, ensure_ascii=False)

    elapsed = time.time() - t_start
    print(f"\nTermine: {len(signatures)}/{total} signatures, {errors} erreurs")
    print(f"Temps: {elapsed:.0f}s ({elapsed/total*1000:.0f}ms/fichier)")
    print(f"Sauvegarde: {output_path}")

if __name__ == "__main__":
    main()