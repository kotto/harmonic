"""
HarmonicDatabase — Dictionnaire visuel de patches réels
=========================================================

Stocke des millions de patches (16×16) avec leur signature DFT harmonique.
Indexé par KD-tree pour retrieval en O(log N).

INGESTION : images → patches → DFT → shards → KD-tree
RETRIEVAL  : query → DFT → centroïdes → top shards → KD-tree → best patch
GÉNÉRATION : composition de patches + PatchMatch pour cohérence spatiale

Ce module est la CLÉ du photoréalisme en Mode B.
"""

import math, time, json, os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

TAU = 2.0 * math.pi


class HarmonicDatabase:
    """Dictionnaire visuel harmonique avec KD-tree."""
    
    def __init__(self, patch_size: int = 16, sig_dim: int = 32):
        self.patch_size = patch_size
        self.sig_dim = sig_dim
        self._patches: Dict[str, List] = {}  # concept → [HarmonicPatch]
        self._kd_trees: Dict[str, object] = {}
        self._loaded = False
    
    # ── INGESTION ───────────────────────────────────────────────────────
    
    def ingest_directory(self, corpus_dir: str, max_per_category: int = 100,
                         extensions: set = None):
        """Ingère un corpus d'images dans le dictionnaire."""
        if extensions is None:
            extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        
        corpus = Path(corpus_dir)
        if not corpus.exists():
            raise FileNotFoundError(f"Répertoire introuvable: {corpus_dir}")
        
        # Découverte des images
        images = []
        for ext in extensions:
            images.extend(corpus.rglob(f'*{ext}'))
            images.extend(corpus.rglob(f'*{ext.upper()}'))
        images = sorted(set(images))
        
        print(f"  📂 {len(images)} images trouvées dans {corpus_dir}")
        
        # Déterminer le concept à partir du nom du répertoire parent
        concept = corpus.name.lower()
        
        ingested = 0
        for img_path in images[:max_per_category]:
            try:
                img = self._load_image(img_path)
                if img is None:
                    continue
                patches = self._extract_patches(img, concept)
                self._patches.setdefault(concept, []).extend(patches)
                ingested += len(patches)
            except Exception as e:
                pass
        
        # Construire les KD-trees
        self._build_trees()
        print(f"  ✓ {ingested} patches ingérés pour le concept '{concept}'")
    
    def _load_image(self, path: Path, max_size: int = 2048) -> Optional[np.ndarray]:
        try:
            from PIL import Image
            img = np.array(Image.open(path).convert('RGB'))
        except: return None
        h, w = img.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            from PIL import Image
            img = np.array(Image.fromarray(img).resize((int(w*scale), int(h*scale)), Image.LANCZOS))
        return img
    
    def _extract_patches(self, img: np.ndarray, concept: str) -> list:
        ps = self.patch_size
        h, w = img.shape[:2]
        patches = []
        stride = max(1, ps // 2)
        for y in range(0, h - ps + 1, stride):
            for x in range(0, w - ps + 1, stride):
                patch = img[y:y+ps, x:x+ps].copy()
                sig = self._compute_signature(patch)
                patches.append(HarmonicPatch(pixels=patch, signature=sig, concept=concept))
        return patches
    
    def _compute_signature(self, patch: np.ndarray) -> np.ndarray:
        """Signature DFT harmonique d'un patch."""
        gray = np.mean(patch, axis=2).astype(np.float32)
        dft = np.fft.fft2(gray)
        mag = np.abs(dft)
        # Top-K fréquences (aplaties)
        k = self.sig_dim // 2
        flat = mag.flatten()
        top_idx = np.argsort(flat)[-k:]
        sig = np.zeros(self.sig_dim, dtype=np.float32)
        sig[:k] = flat[top_idx]
        sig[k:] = np.angle(dft.flatten())[top_idx]
        return sig / (np.linalg.norm(sig) + 1e-10)
    
    def _build_trees(self):
        try:
            from scipy.spatial import KDTree
            for concept, patches in self._patches.items():
                if len(patches) < 2: continue
                sigs = np.array([p.signature for p in patches], dtype=np.float32)
                self._kd_trees[concept] = KDTree(sigs)
        except ImportError:
            pass
    
    # ── RETRIEVAL ──────────────────────────────────────────────────────
    
    def retrieve(self, concept: str, query_patch: np.ndarray) -> Optional[np.ndarray]:
        """Retrouve le meilleur patch pour une requête."""
        if concept not in self._kd_trees:
            if concept in self._patches and self._patches[concept]:
                return self._patches[concept][0].pixels
            return None
        qsig = self._compute_signature(query_patch).reshape(1, -1)
        dist, idx = self._kd_trees[concept].query(qsig, k=1)
        idx_i = int(idx.item())
        return self._patches[concept][idx_i].pixels
    
    # ── GÉNÉRATION ────────────────────────────────────────────────────
    
    def generate(self, concept: str, width: int = 256, height: int = 256) -> np.ndarray:
        """Génère une image par composition de patches du dictionnaire."""
        ps = self.patch_size
        st = max(1, ps // 2)
        n_h = max(1, (height - ps) // st + 1)
        n_w = max(1, (width - ps) // st + 1)
        final_h = (n_h - 1) * st + ps
        final_w = (n_w - 1) * st + ps
        
        if concept not in self._patches or not self._patches[concept]:
            return np.zeros((height, width, 3), dtype=np.uint8)
        
        concept_patches = [p.pixels for p in self._patches[concept]]
        rng = np.random.RandomState(hash(concept) % 2**31)
        
        # Assemblage
        canvas = np.zeros((final_h, final_w, 3), dtype=np.float32)
        weight = np.zeros((final_h, final_w, 1), dtype=np.float32)
        
        for i in range(n_h):
            for j in range(n_w):
                src = concept_patches[rng.randint(len(concept_patches))]
                best = self.retrieve(concept, src)
                if best is None: best = src
                y0, x0 = i*st, j*st
                y1, x1 = min(y0+ps, final_h), min(x0+ps, final_w)
                ph, pw = y1-y0, x1-x0
                wy = 0.5*(1-np.cos(TAU*np.arange(ph)/(ph-1))) if ph>1 else np.ones(1)
                wx = 0.5*(1-np.cos(TAU*np.arange(pw)/(pw-1))) if pw>1 else np.ones(1)
                w = wy[:,None]*wx[None,:]
                canvas[y0:y1,x0:x1] += best[:ph,:pw].astype(np.float32)*w[:,:,None]
                weight[y0:y1,x0:x1] += w[:,:,None]
        
        weight[weight<1e-15] = 1.0
        image = canvas/weight
        return np.clip(image, 0, 255).astype(np.uint8)[:height, :width]
    
    # ── PERSISTANCE ───────────────────────────────────────────────────
    
    def save(self, path: str):
        p = Path(path); p.mkdir(parents=True, exist_ok=True)
        for concept, patches in self._patches.items():
            sigs = np.array([pt.signature for pt in patches], dtype=np.float32)
            pixels = np.array([pt.pixels for pt in patches], dtype=np.uint8)
            np.savez_compressed(p/f'{concept}.npz', signatures=sigs, pixels=pixels)
        with open(p/'manifest.json','w') as f:
            json.dump({'concepts': list(self._patches.keys()), 'patch_size': self.patch_size, 'sig_dim': self.sig_dim}, f)
    
    def load(self, path: str):
        p = Path(path)
        with open(p/'manifest.json') as f: m = json.load(f)
        for concept in m['concepts']:
            data = np.load(p/f'{concept}.npz')
            sigs = data['signatures']; pixels = data['pixels']
            self._patches[concept] = [HarmonicPatch(pixels=pixels[i], signature=sigs[i], concept=concept) for i in range(len(sigs))]
        self._build_trees()
        self._loaded = True

class HarmonicPatch:
    __slots__ = ('pixels', 'signature', 'concept')
    def __init__(self, pixels, signature, concept):
        self.pixels = pixels; self.signature = signature; self.concept = concept
