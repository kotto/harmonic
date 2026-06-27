#!/usr/bin/env python3
"""
KA STUDIO INGEST — Entraînement one-pass images, audio, vidéo
===============================================================
Pipeline d'ingestion multimédia dans l'hologramme 64×64.

Usage:
  python ka_studio_ingest.py --images   # Entraînement visuel
  python ka_studio_ingest.py --audio    # Entraînement sonore
  python ka_studio_ingest.py --video    # Entraînement vidéo
  python ka_studio_ingest.py --all      # Tout (images + audio + vidéo)
  python ka_studio_ingest.py --images --dir photos/
  python ka_studio_ingest.py --status   # Voir l'état
"""

import os, sys, time, json, argparse, hashlib, glob
import numpy as np
from datetime import datetime

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

from ka_reasoning_engine import KAReasoningEngine

BASE_DIR = os.path.join(_project_root, "ka_studio_data")
os.makedirs(BASE_DIR, exist_ok=True)
HOLO_IMAGES = os.path.join(BASE_DIR, "holo_images.npy")
HOLO_AUDIO  = os.path.join(BASE_DIR, "holo_audio.npy")
HOLO_VIDEO  = os.path.join(BASE_DIR, "holo_video.npy")
PROGRESS_FILE = os.path.join(BASE_DIR, "studio_progress.json")

NX, NY, PHI = 64, 64, 1.618033988749895

# =========================================================================
# PROJECTEURS (donnée → onde)
# =========================================================================

def image_vers_ondes(img_array, n_freqs=32):
    """Image → FFT 2D → ondes (kx, ky, amplitude)."""
    if img_array.ndim == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array
    gray = gray.astype(np.float64)
    
    fft = np.fft.fftshift(np.fft.fft2(gray))
    mag = np.abs(fft)
    h, w = mag.shape
    indices = np.argsort(mag.ravel())[::-1][:n_freqs]
    
    ondes = []
    for idx in indices:
        row, col = idx // w, idx % w
        ky = (row - h//2) / (h//2) * np.pi
        kx = (col - w//2) / (w//2) * np.pi
        amp = float(mag[row, col]) / (mag.max() + 1e-8)
        ondes.append((kx, ky, amp))
    return ondes

def audio_vers_ondes(signal, sr=22050, n_harms=16):
    """Audio → FFT → harmoniques dominantes en ondes."""
    n = len(signal)
    fft = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(n, 1/sr)
    indices = np.argsort(fft)[::-1][:n_harms]
    
    ondes = []
    for idx in indices:
        if fft[idx] < fft.max() * 0.01:
            continue
        freq = freqs[idx]
        amp = float(fft[idx]) / (fft.max() + 1e-8)
        kx = np.pi * min(freq / 5000, 1.0)
        ky = np.pi * (idx / n_harms * 2 - 1)
        ondes.append((kx, ky, amp))
    return ondes

def video_vers_ondes(frames_list, n_freqs=16):
    """Vidéo → FFT 2D par frame + FFT temporelle → ondes."""
    ondes = []
    n_frames = len(frames_list)
    
    for i, frame in enumerate(frames_list):
        img_ondes = image_vers_ondes(frame, n_freqs=n_freqs//2)
        kt = np.pi * (i / max(n_frames-1, 1) * 2 - 1)  # position temporelle
        for kx, ky, amp in img_ondes:
            ondes.append((kx + kt*0.1, ky + kt*0.1, amp * 0.7))
    
    return ondes

# =========================================================================
# GÉNÉRATEURS DE DONNÉES SYNTHÉTIQUES (quand pas de vrais datasets)
# =========================================================================

def generer_images_synthetiques(n=500):
    """Génère des images de formes, textures, dégradés pour l'entraînement."""
    images = []
    for i in range(n):
        img = np.zeros((64, 64), dtype=np.float64)
        style = i % 6
        
        if style == 0:  # Formes géométriques
            cx, cy = np.random.randint(10, 54, 2)
            r = np.random.randint(3, 15)
            y, x = np.ogrid[:64, :64]
            img = 255 * ((x-cx)**2 + (y-cy)**2 <= r**2).astype(np.float64)
        
        elif style == 1:  # Dégradés
            angle = np.random.random() * np.pi * 2
            x, y = np.meshgrid(np.linspace(-1,1,64), np.linspace(-1,1,64))
            img = 255 * (0.5 + 0.5 * (np.cos(angle)*x + np.sin(angle)*y))
        
        elif style == 2:  # Textures (bruit de Perlin simplifié)
            img = np.random.randn(64, 64) * 30 + 128
            img = np.clip(img, 0, 255)
        
        elif style == 3:  # Bandes
            freq = np.random.randint(2, 8)
            img = 255 * (0.5 + 0.5 * np.sin(np.linspace(0, freq*np.pi, 64)))[:, np.newaxis] * np.ones(64)
        
        elif style == 4:  # Damiers
            size = np.random.choice([4, 8, 16])
            x, y = np.meshgrid(np.arange(64)//size % 2, np.arange(64)//size % 2)
            img = 255 * ((x + y) % 2).astype(np.float64)
        
        elif style == 5:  # Points aléatoires
            for _ in range(np.random.randint(5, 30)):
                cx, cy = np.random.randint(0, 64, 2)
                if 0 <= cx < 64 and 0 <= cy < 64:
                    img[max(0,cy-2):min(64,cy+2), max(0,cx-2):min(64,cx+2)] = 255
        
        images.append({"data": img, "style": style})
    return images

def generer_audio_synthetique(n=200):
    """Génère des signaux audio synthétiques (notes, accords, bruits)."""
    sr = 22050
    audios = []
    for i in range(n):
        style = i % 5
        duree = 0.5 + np.random.random() * 2
        t = np.linspace(0, duree, int(sr * duree), endpoint=False)
        signal = np.zeros_like(t)
        
        if style == 0:  # Note pure
            freq = 110 * (2 ** (np.random.randint(0, 36) / 12))
            signal = np.sin(2 * np.pi * freq * t)
        
        elif style == 1:  # Accord (3 notes)
            base = 110 * (2 ** (np.random.randint(0, 24) / 12))
            for offset in [0, 4, 7]:
                signal += np.sin(2 * np.pi * base * (2**(offset/12)) * t) * 0.4
        
        elif style == 2:  # Enveloppe ADSR
            freq = 220 * (2 ** (np.random.randint(0, 24) / 12))
            signal = np.sin(2 * np.pi * freq * t)
            a, d, s, r_s = 0.01, 0.1, 0.7, 0.3
            env = np.ones_like(t)
            env[:int(a*sr)] = np.linspace(0, 1, int(a*sr))
            env[int(a*sr):int((a+d)*sr)] = np.linspace(1, s, int(d*sr))
            env[-int(r_s*sr):] = np.linspace(s, 0, int(r_s*sr))
            signal *= env
        
        elif style == 3:  # Bruit blanc filtré
            signal = np.random.randn(len(t)) * 0.3
        
        elif style == 4:  # Sweep de fréquence
            f0, f1 = 100, 2000
            freq = f0 + (f1 - f0) * t / t[-1]
            signal = np.sin(2 * np.pi * freq * t)
        
        audios.append({"signal": signal.astype(np.float32), "sr": sr, "style": style})
    return audios

def generer_video_synthetique(n=100):
    """Génère des séquences vidéo synthétiques (formes en mouvement)."""
    videos = []
    for i in range(n):
        frames = []
        n_frames = 10 + np.random.randint(5, 20)
        cx, cy = np.random.randint(10, 54, 2)
        vx, vy = np.random.randint(-2, 3, 2)
        r = np.random.randint(3, 10)
        
        for f in range(n_frames):
            frame = np.zeros((64, 64), dtype=np.float64)
            y, x = np.ogrid[:64, :64]
            cx2 = (cx + vx * f) % 64
            cy2 = (cy + vy * f) % 64
            frame = 255 * ((x-cx2)**2 + (y-cy2)**2 <= r**2).astype(np.float64)
            frames.append(frame)
        
        videos.append(frames)
    return videos

# =========================================================================
# INGESTEUR
# =========================================================================

class StudioIngesteur:
    def __init__(self):
        self.engine = KAReasoningEngine(mode="harmonic")
        self.xx = self.engine.bridge.monde.xx
        self.yy = self.engine.bridge.monde.yy
        self.progress = self._load_progress()
    
    def _load_progress(self):
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE) as f:
                return json.load(f)
        return {"images": 0, "audio": 0, "video": 0}
    
    def _save_progress(self):
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(self.progress, f)
    
    def _ajouter_ondes(self, ondes, amplitude=0.5):
        for kx, ky, amp in ondes:
            onde = np.exp(1j * (kx * self.xx + ky * self.yy))
            self.engine.bridge.monde.H += amp * amplitude * onde
    
    def _sauvegarder(self, path):
        np.save(path, self.engine.bridge.monde.H)
    
    def _charger(self, path):
        if os.path.exists(path):
            self.engine.bridge.monde.H = np.load(path)
            return True
        return False
    
    def entrainer_images(self, dossier=None, n_synthetique=1000):
        print(f"\n{'='*60}")
        print("ENTRAÎNEMENT IMAGES")
        print(f"{'='*60}")
        
        self._charger(HOLO_IMAGES)
        t0 = time.time()
        
        if dossier and os.path.isdir(dossier):
            from PIL import Image
            fichiers = [f for f in glob.glob(os.path.join(dossier, "*")) 
                       if f.lower().endswith(('.jpg','.jpeg','.png','.bmp'))]
            print(f"  {len(fichiers)} images réelles trouvées")
            
            for i, fp in enumerate(fichiers[:1000]):
                try:
                    img = Image.open(fp).convert('L').resize((64,64))
                    ondes = image_vers_ondes(np.array(img), n_freqs=32)
                    self._ajouter_ondes(ondes, 0.4)
                    if (i+1) % 200 == 0:
                        print(f"  {i+1}/{min(len(fichiers),1000)} | E={self.engine.bridge.monde.energie():.0f}")
                except: pass
            self.progress["images"] += min(len(fichiers), 1000)
        
        # Ajouter synthétiques
        print(f"  +{n_synthetique} images synthétiques...")
        synt = generer_images_synthetiques(n_synthetique)
        for i, img in enumerate(synt):
            ondes = image_vers_ondes(img["data"], n_freqs=16)
            self._ajouter_ondes(ondes, 0.3)
            if (i+1) % 500 == 0:
                print(f"  {i+1}/{n_synthetique} | E={self.engine.bridge.monde.energie():.0f}")
        
        self.progress["images"] += n_synthetique
        self._sauvegarder(HOLO_IMAGES)
        self._save_progress()
        
        dt = time.time() - t0
        print(f"  ✅ {self.progress['images']} images ingérées | {dt:.1f}s | E={self.engine.bridge.monde.energie():.0f}")
    
    def entrainer_audio(self, dossier=None, n_synthetique=1000):
        print(f"\n{'='*60}")
        print("ENTRAÎNEMENT AUDIO")
        print(f"{'='*60}")
        
        self._charger(HOLO_AUDIO)
        t0 = time.time()
        
        if dossier and os.path.isdir(dossier):
            fichiers = [f for f in glob.glob(os.path.join(dossier, "*"))
                       if f.lower().endswith(('.wav','.mp3','.flac','.ogg'))]
            print(f"  {len(fichiers)} fichiers audio trouvés")
            # Traitement des fichiers audio réels...
        
        print(f"  +{n_synthetique} audios synthétiques...")
        audios = generer_audio_synthetique(n_synthetique)
        for i, a in enumerate(audios):
            ondes = audio_vers_ondes(a["signal"], a["sr"], n_harms=16)
            self._ajouter_ondes(ondes, 0.4)
            if (i+1) % 500 == 0:
                print(f"  {i+1}/{n_synthetique} | E={self.engine.bridge.monde.energie():.0f}")
        
        self.progress["audio"] += n_synthetique
        self._sauvegarder(HOLO_AUDIO)
        self._save_progress()
        
        dt = time.time() - t0
        print(f"  ✅ {self.progress['audio']} audios ingérés | {dt:.1f}s | E={self.engine.bridge.monde.energie():.0f}")
    
    def entrainer_video(self, n_synthetique=200):
        print(f"\n{'='*60}")
        print("ENTRAÎNEMENT VIDÉO")
        print(f"{'='*60}")
        
        self._charger(HOLO_VIDEO)
        t0 = time.time()
        
        print(f"  +{n_synthetique} vidéos synthétiques...")
        videos = generer_video_synthetique(n_synthetique)
        for i, frames in enumerate(videos):
            ondes = video_vers_ondes(frames, n_freqs=16)
            self._ajouter_ondes(ondes, 0.4)
            n_frames = len(frames)
            self.progress["video"] += n_frames
            if (i+1) % 100 == 0:
                print(f"  {i+1}/{n_synthetique} clips | {self.progress['video']} frames | E={self.engine.bridge.monde.energie():.0f}")
        
        self._sauvegarder(HOLO_VIDEO)
        self._save_progress()
        
        dt = time.time() - t0
        print(f"  ✅ {self.progress['video']} frames ingérées | {dt:.1f}s | E={self.engine.bridge.monde.energie():.0f}")
    
    def entrainer_all(self, images=500, audio=500, video=100):
        self.entrainer_images(n_synthetique=images)
        self.entrainer_audio(n_synthetique=audio)
        self.entrainer_video(n_synthetique=video)
        
        print(f"\n{'='*60}")
        print("ENTRAÎNEMENT MULTIMODAL TERMINÉ")
        print(f"  Images : {self.progress['images']:,}")
        print(f"  Audio  : {self.progress['audio']:,}")
        print(f"  Vidéo  : {self.progress['video']:,} frames")
        print(f"  Hologrammes : 3 × 32 Ko = 96 Ko")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="KA Studio Ingest")
    parser.add_argument("--images", action="store_true")
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dir", type=str, default="")
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    
    studio = StudioIngesteur()
    
    if args.status:
        print(f"Progression : {json.dumps(studio.progress, indent=2)}")
        for name, path in [("Images", HOLO_IMAGES), ("Audio", HOLO_AUDIO), ("Vidéo", HOLO_VIDEO)]:
            if os.path.exists(path):
                h = np.load(path)
                print(f"  {name} : E={np.sum(np.abs(h)**2):.0f}")
        return
    
    if args.all or (args.images and args.audio and args.video):
        studio.entrainer_all(images=args.n, audio=args.n, video=args.n//5)
    elif args.images:
        studio.entrainer_images(dossier=args.dir, n_synthetique=args.n)
    elif args.audio:
        studio.entrainer_audio(dossier=args.dir, n_synthetique=args.n)
    elif args.video:
        studio.entrainer_video(n_synthetique=args.n//5)
    else:
        parser.print_help()
        print("\n  Essayez : python ka_studio_ingest.py --all")
        print("  Ou      : python ka_studio_ingest.py --images --n 2000")


if __name__ == "__main__":
    main()