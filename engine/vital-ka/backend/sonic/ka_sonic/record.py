"""
Enregistreur vocal — capture micro → WAV pour clonage harmonique.

Usage :
    python ka_sonic/record.py                    # 5 minutes, micro par défaut
    python ka_sonic/record.py -d 120             # 2 minutes
    python ka_sonic/record.py -d 30 -o voix.wav  # 30 secondes, nom perso
    python ka_sonic/record.py --list             # lister les périphériques

Sortie : WAV 22 kHz mono 16-bit, prêt pour le clonage.
"""

import sys
import os
import time
import threading
import argparse
import wave
import numpy as np

try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False
    print("⚠️  sounddevice non installé. pip install sounddevice")
    sys.exit(1)

DEFAULT_SR = 22050
DEFAULT_DURATION = 300  # 5 minutes
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "voice_samples")


def list_devices():
    """Affiche les périphériques d'entrée disponibles."""
    print("\n🎤 Périphériques d'entrée :")
    print("-" * 70)
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"  [{i:2d}] {d['name'][:50]:50s} "
                  f"canaux={d['max_input_channels']} "
                  f"sr={d['default_samplerate']:.0f}Hz")
    print(f"\n  Défaut: device {sd.default.device[0]}")


def record(output_path: str, duration_s: float, sr: int = DEFAULT_SR, device: int = None):
    """Enregistre depuis le micro et sauvegarde en WAV.

    Args:
        output_path : chemin du fichier WAV de sortie
        duration_s : durée en secondes
        sr : sample rate (défaut 22050 Hz)
        device : index du périphérique (None = défaut)
    """
    print(f"\n🔴 ENREGISTREMENT — {duration_s:.0f}s")
    print(f"   Fichier : {output_path}")
    print(f"   Sample rate : {sr} Hz")
    print(f"   Appuyez sur Ctrl+C pour arrêter plus tôt\n")

    # Buffer pour accumuler l'audio
    n_channels = 1
    n_samples = int(duration_s * sr)
    audio_buffer = np.zeros(n_samples, dtype=np.float32)
    pos = [0]  # mutable pour le callback
    done = threading.Event()

    def callback(indata, frames, timing, status):
        if status:
            print(f"  ⚠️ {status}", file=sys.stderr)
        remaining = n_samples - pos[0]
        n_copy = min(frames, remaining)
        if n_copy > 0:
            # Mono : prendre le premier canal ou moyenner
            if indata.shape[1] == 1:
                chunk = indata[:n_copy, 0]
            else:
                chunk = indata[:n_copy].mean(axis=1)
            audio_buffer[pos[0]:pos[0] + n_copy] = chunk[:, 0] if chunk.ndim > 1 else chunk
            pos[0] += n_copy
        if pos[0] >= n_samples:
            done.set()
            raise sd.CallbackStop()

    # Démarrer le stream
    stream = sd.InputStream(
        samplerate=sr,
        device=device,
        channels=n_channels,
        callback=callback,
        dtype='float32',
    )

    t_start = time.time()
    try:
        with stream:
            while not done.is_set():
                elapsed = time.time() - t_start
                remaining = max(0, duration_s - elapsed)
                pos_current = min(pos[0], n_samples)
                pct = pos_current / n_samples * 100
                bar_len = 40
                filled = int(bar_len * pos_current / n_samples)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"\r  [{bar}] {pct:5.1f}%  "
                      f"{elapsed:.0f}s / {duration_s:.0f}s  "
                      f"restant: {remaining:.0f}s  "
                      f"Ctrl+C = stop", end="", flush=True)
                time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n\n  ⏹️  Arrêt manuel")
    finally:
        stream.close()

    # Sauvegarder
    actual_samples = pos[0]
    if actual_samples == 0:
        print("  ⚠️  Aucun échantillon enregistré")
        return None

    audio = audio_buffer[:actual_samples]
    
    # Normaliser
    peak = np.max(np.abs(audio)) + 1e-10
    audio = audio / peak * 0.95
    
    # Sauver WAV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pcm = (audio * 32767.0).astype("<i2")
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())

    duration = actual_samples / sr
    file_size_mb = os.path.getsize(output_path) / 1024 / 1024
    
    print(f"\n  ✅ Enregistrement terminé !")
    print(f"     Durée   : {duration:.1f}s")
    print(f"     Fichier : {output_path}")
    print(f"     Taille  : {file_size_mb:.2f} MB")
    print(f"     Peak    : {np.max(np.abs(audio)):.3f}")
    print(f"\n  → Prêt pour le clonage :")
    print(f"     bridge.clone_voice('{output_path}', 'ma_voix')")
    
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enregistreur vocal pour clonage KA Sonic")
    parser.add_argument("-d", "--duration", type=float, default=DEFAULT_DURATION,
                        help=f"Durée en secondes (défaut: {DEFAULT_DURATION}s = 5 min)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Chemin du fichier WAV de sortie")
    parser.add_argument("-s", "--samplerate", type=int, default=DEFAULT_SR,
                        help=f"Sample rate (défaut: {DEFAULT_SR} Hz)")
    parser.add_argument("--device", type=int, default=None,
                        help="Index du périphérique d'entrée")
    parser.add_argument("--list", action="store_true",
                        help="Lister les périphériques et quitter")
    args = parser.parse_args()

    if args.list:
        list_devices()
        sys.exit(0)

    # Nom du fichier
    if args.output:
        output_path = args.output
    else:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"voice_{timestamp}.wav")

    print(f"🎙️  KA Sonic Recorder")
    print(f"   Périphérique : {'défaut' if args.device is None else str(args.device)}")
    
    record(output_path, args.duration, sr=args.samplerate, device=args.device)
