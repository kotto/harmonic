"""
HarmonicVisuals — Générateur d'Images et Vidéos Harmonique
=============================================================

Projet unifié de génération visuelle basé sur l'architecture ondulatoire.

Deux modes de génération :
  MODE A (Géométrique) : ψ → IFFT 2D → patterns ondulatoires
  MODE B (Photoréaliste) : ψ → HarmonicDatabase → retrieval de patches réels

Usage rapide :
  from harmonic_visuals import HarmonicVisuals

  hv = HarmonicVisuals()

  # Mode A : Art géométrique
  img = hv.generate_geometric("coucher de soleil", 1024, 1024)

  # Mode B : Photoréaliste (après entraînement du dictionnaire)
  img = hv.generate_realistic("sunset over ocean", 1024, 1024)

  # Mode Hybride : Structure A + Texture B
  img = hv.generate_hybrid("a dragon flying over mountains")

  # Vidéo
  video = hv.generate_video("sunrise time-lapse", duration_s=10, fps=24)

  # Pipeline complet
  result = hv.pipeline("forest in autumn", upscale=4, compress=True)
  # → image 4K, ~200 Ko

Auteur : Équipe HarmoniqLLM
Date   : 2026-07-25
"""
__version__ = "1.0.0"
__author__ = "HarmoniqLLM"

import math
import time
import io
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Union
import numpy as np

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ── Imports des modules core ──────────────────────────────────────────────────

from core.encoder import HarmonicEncoder
from core.generator_a import GeometricGenerator
from core.generator_b import RealisticGenerator
from core.upscaler import PhiUpscaler
from core.compressor import HCVCompressor
from core.postfilter import PhiPostFilter
from core.hologram_store import ImageHologramStore

# ── Imports optionnels ─────────────────────────────────────────────────────────

try:
    from core.dictionary import HarmonicDatabase
    HAS_DICT = True
except ImportError:
    HAS_DICT = False

try:
    from video.generator import VideoGenerator
    HAS_VIDEO = True
except ImportError:
    HAS_VIDEO = False


class HarmonicVisuals:
    """
    Moteur principal de génération visuelle harmonique.
    
    Combine les deux modes de génération, l'upscaling, la compression,
    le stockage holographique, et la génération vidéo.
    """
    
    def __init__(self, dim: int = 512, dictionary_path: str = None):
        self.dim = dim
        
        # Modules core (toujours disponibles)
        self.encoder = HarmonicEncoder(dim=dim)
        self.generator_a = GeometricGenerator(dim=dim)
        self.upscaler = PhiUpscaler()
        self.compressor = HCVCompressor()
        self.postfilter = PhiPostFilter()
        self.store = ImageHologramStore(dim=dim)
        
        # Module B (nécessite un dictionnaire entraîné)
        self.generator_b = None
        if HAS_DICT:
            self.generator_b = RealisticGenerator(dim=dim)
            if dictionary_path:
                self.load_dictionary(dictionary_path)
        
        # Vidéo (optionnel)
        self.video_gen = None
        if HAS_VIDEO:
            self.video_gen = VideoGenerator(self)
        
        # Stats
        self.stats = {'generated': 0, 'upscaled': 0, 'compressed': 0, 'videos': 0}
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GÉNÉRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def generate_geometric(self, prompt: str, width: int = 1024, height: int = 1024,
                           iterations: int = 1) -> np.ndarray:
        """
        MODE A : Génération géométrique par interférence ψ → IFFT 2D.
        
        Args:
            prompt: description textuelle
            width, height: dimensions de sortie
            iterations: nombre d'itérations de raffinement (1-5)
            
        Returns:
            [H, W, 3] uint8
        """
        psi = self.encoder.encode(prompt)
        img = self.generator_a.generate(psi, width, height)
        
        for _ in range(iterations - 1):
            img = self.postfilter.apply(img)
        
        self.stats['generated'] += 1
        return img
    
    def generate_realistic(self, prompt: str, width: int = 1024, height: int = 1024) -> np.ndarray:
        """
        MODE B : Génération photoréaliste par dictionnaire de patches.
        
        Nécessite un dictionnaire entraîné (build_corpus.py).
        """
        if self.generator_b is None:
            raise RuntimeError(
                "Mode B non disponible. Installez le dictionnaire : "
                "hv.load_dictionary('data/dictionary/')"
            )
        
        psi = self.encoder.encode(prompt)
        img = self.generator_b.generate(psi, width, height)
        self.stats['generated'] += 1
        return img
    
    def generate_hybrid(self, prompt: str, width: int = 1024, height: int = 1024,
                        structure_weight: float = 0.4) -> np.ndarray:
        """
        MODE HYBRIDE : Structure géométrique (A) + Texture photoréaliste (B).
        
        Le Mode A fournit la composition, la palette, les proportions φ.
        Le Mode B fournit les détails de texture à partir de photos réelles.
        """
        if self.generator_b is None:
            # Fallback : Mode A pur
            return self.generate_geometric(prompt, width, height, iterations=3)
        
        psi = self.encoder.encode(prompt)
        
        # Structure (Mode A)
        structure = self.generator_a.generate(psi, width, height)
        
        # Texture (Mode B)
        texture = self.generator_b.generate(psi, width, height)
        
        # Fusion pondérée
        hybrid = (structure.astype(np.float32) * structure_weight + 
                  texture.astype(np.float32) * (1 - structure_weight))
        hybrid = self.postfilter.apply(np.clip(hybrid, 0, 255).astype(np.uint8))
        
        self.stats['generated'] += 1
        return hybrid
    
    # ═══════════════════════════════════════════════════════════════════════════
    # VIDÉO
    # ═══════════════════════════════════════════════════════════════════════════
    
    def generate_video(self, prompt: str, duration_s: float = 5.0, fps: int = 24,
                       width: int = 512, height: int = 512, mode: str = 'hybrid') -> List[np.ndarray]:
        """
        Génère une vidéo par séquence de frames avec interpolation φ.
        
        Args:
            prompt: description de la scène
            duration_s: durée en secondes
            fps: images par seconde
            width, height: résolution
            mode: 'geometric', 'realistic', 'hybrid'
            
        Returns:
            Liste de frames [H, W, 3] uint8
        """
        if self.video_gen is None:
            raise RuntimeError("Module vidéo non disponible")
        
        frames = self.video_gen.generate(prompt, duration_s, fps, width, height, mode)
        self.stats['videos'] += 1
        return frames
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE COMPLET
    # ═══════════════════════════════════════════════════════════════════════════
    
    def pipeline(self, prompt: str, mode: str = 'geometric',
                 width: int = 1024, height: int = 1024,
                 upscale: int = None, compress: bool = True,
                 quality: int = 80, store: bool = False) -> dict:
        """
        Pipeline complet : génération → post-filtre → upscale → compression.
        
        Args:
            prompt: description
            mode: 'geometric', 'realistic', 'hybrid'
            width, height: résolution initiale
            upscale: facteur (2, 4) ou None
            compress: appliquer la compression HCV
            quality: qualité de compression (1-100)
            store: stocker dans le HologramStore
            
        Returns:
            dict avec image, stats, et métadonnées
        """
        t0 = time.perf_counter()
        
        # 1. Génération
        if mode == 'geometric':
            img = self.generate_geometric(prompt, width, height, iterations=3)
        elif mode == 'realistic':
            img = self.generate_realistic(prompt, width, height)
        elif mode == 'hybrid':
            img = self.generate_hybrid(prompt, width, height)
        else:
            raise ValueError(f"Mode inconnu: {mode}")
        
        # 2. Post-filtre
        img = self.postfilter.apply(img)
        
        # 3. Upscale (optionnel)
        scale = 1
        if upscale and upscale > 1:
            img, scale = self.upscaler.upscale(img, factor=upscale)
            self.stats['upscaled'] += 1
        
        # 4. Compression (optionnelle)
        compressed_size = None
        ratio = 1.0
        if compress:
            img_bytes = self._image_to_bytes(img)
            compressed, stats = self.compressor.compress(img_bytes)
            compressed_size = len(compressed)
            original_size = len(img_bytes)
            ratio = original_size / max(compressed_size, 1)
            self.stats['compressed'] += 1
            # Recharger l'image depuis le buffer compressé
            from PIL import Image
            img = np.array(Image.open(io.BytesIO(compressed)))
        
        # 5. Stockage holographique (optionnel)
        hash_id = None
        if store:
            hash_id = self.store.add(img, prompt)
        
        elapsed = (time.perf_counter() - t0) * 1000
        
        return {
            'image': img,
            'prompt': prompt,
            'mode': mode,
            'resolution': f"{img.shape[1]}×{img.shape[0]}",
            'upscale_factor': scale,
            'compression_ratio': round(ratio, 1) if compress else None,
            'compressed_size': compressed_size,
            'elapsed_ms': round(elapsed, 1),
            'hologram_id': hash_id,
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DICTIONNAIRE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def load_dictionary(self, path: str):
        """Charge un dictionnaire de patches pour le Mode B."""
        if self.generator_b is None:
            from .core.generator_b import RealisticGenerator
            self.generator_b = RealisticGenerator(dim=self.dim)
        self.generator_b.load(path)
    
    def build_dictionary(self, corpus_dir: str, max_images: int = 1000):
        """Construit le dictionnaire à partir d'un corpus d'images."""
        from core.dictionary import HarmonicDatabase
        hdb = HarmonicDatabase()
        hdb.ingest_directory(corpus_dir, max_per_category=max_images)
        if self.generator_b:
            self.generator_b.set_database(hdb)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _image_to_bytes(self, img: np.ndarray, format: str = 'JPEG', quality: int = 95) -> bytes:
        from PIL import Image
        buf = io.BytesIO()
        Image.fromarray(img).save(buf, format=format, quality=quality)
        return buf.getvalue()
    
    @property
    def info(self) -> dict:
        return {
            'version': __version__,
            'dim': self.dim,
            'mode_a': True,
            'mode_b': self.generator_b is not None,
            'video': self.video_gen is not None,
            **self.stats,
        }
    
    def __repr__(self) -> str:
        modes = ['A']
        if self.generator_b: modes.append('B')
        if self.video_gen: modes.append('Vidéo')
        return f"HarmonicVisuals(modes={','.join(modes)}, dim={self.dim}, generated={self.stats['generated']})"
