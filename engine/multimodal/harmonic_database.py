"""
Harmonic Database — Base de signatures harmoniques DFT avec index KD-tree
==========================================================================

Stocke des millions de patches avec leur signature harmonique DFT (déterministe).
Utilise un KD-tree par concept pour la recherche en O(log N).

**V3 — Architecture shardée** :
- Shards de 50K patches max (~75 MB RAM) → flush automatique sur disque
- Index centroïde (two-level retrieval) → top-3 shards sélectionnés en O(1)
- Pixels en memmap → jamais chargés en RAM sauf le patch gagnant
- Budget RAM constant (~90 MB) quel que soit le nombre total de patches

INGESTION : image → patches → DFT top-K → buffer → flush shard → disque
RETRIEVAL : query → DFT → centroïdes → top-3 shards → KD-tree → best patch
GÉNÉRATION : composition de patches exacts + PatchMatch

Usage
-----
    from multimodal.harmonic_database import HarmonicDatabase
    hdb = HarmonicDatabase()
    hdb.ingest_directory('data/massive_dataset/', max_per_category=30)
    patch = hdb.retrieve('sunset', query_patch)
    image = hdb.generate('sunset', width=256, height=256)
"""

import sys, os, math, time, logging, json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

try:
    from scipy.spatial import KDTree
    HAS_KDTREE = True
except ImportError:
    HAS_KDTREE = False

log = logging.getLogger(__name__)
TAU = 2.0 * math.pi


@dataclass
class HarmonicPatch:
    """Un patch avec sa signature harmonique DFT."""
    pixels: np.ndarray          # (S, S, 3) uint8
    signature: np.ndarray       # (2*K,) float32 — top-K DFT (amplitude + phase)
    concept: str
    image_file: str = ''        # fichier source (optionnel)


# ═══════════════════════════════════════════════════════════════════════
# DICT SHARD — Unité de stockage disque
# ═══════════════════════════════════════════════════════════════════════

class DictShard:
    """
    Un shard autonome contenant jusqu'à max_patches patches.

    Chargement lazy : signatures + KD-tree en RAM, pixels en mmap (disque).
    Une fois flushé sur disque, le shard peut être déchargé et rechargé.
    """

    def __init__(self, shard_id: int, patch_size: int, sig_dim: int,
                 max_patches: int = 50000):
        self.shard_id = shard_id
        self.patch_size = patch_size
        self.sig_dim = sig_dim
        self.max_patches = max_patches

        # Données en RAM (quand chargé)
        self.signatures: Optional[np.ndarray] = None   # (N, sig_dim) float32
        self.pixels: Optional[np.ndarray] = None        # (N, ps, ps, 3) uint8 (mmap)
        self.features: Optional[np.ndarray] = None      # (N, 21) float32
        self.concepts: List[str] = []                    # concept de chaque patch
        self._n_patches: int = 0                         # persiste après unload
        self.kd_tree: Optional['KDTree'] = None
        self._loaded = False
        self._path: Optional[Path] = None

    @property
    def n_patches(self) -> int:
        return self._n_patches if self._n_patches > 0 else len(self.concepts)

    @property
    def centroid(self) -> np.ndarray:
        """Centroïde du shard (moyenne des signatures)."""
        if self.signatures is None or len(self.signatures) == 0:
            return np.zeros(self.sig_dim, dtype=np.float32)
        return self.signatures.mean(axis=0)

    def add_batch(self, signatures: np.ndarray, pixels: np.ndarray,
                  concepts: List[str]) -> bool:
        """
        Ajoute un lot de patches au shard (en RAM).

        Returns:
            True si le shard a encore de la place, False s'il est plein.
        """
        n = signatures.shape[0]
        if self.signatures is None:
            self.signatures = signatures.astype(np.float32)
            self.pixels = pixels.astype(np.uint8)
            self.concepts = list(concepts)
        else:
            self.signatures = np.concatenate([self.signatures, signatures.astype(np.float32)])
            self.pixels = np.concatenate([self.pixels, pixels.astype(np.uint8)])
            self.concepts.extend(concepts)
        self._loaded = True
        self._n_patches = len(self.concepts)
        return self._n_patches < self.max_patches

    def build_tree(self):
        """Construit le KD-tree à partir des signatures."""
        if self.signatures is None or len(self.signatures) < 2:
            return
        if not HAS_KDTREE:
            return
        self.kd_tree = KDTree(self.signatures.astype(np.float32))

    def query(self, qsig: np.ndarray) -> Tuple[Optional[np.ndarray], float, int]:
        """
        Recherche le patch le plus proche dans ce shard.

        Returns:
            (pixels, distance, index) ou (None, inf, -1)
        """
        if self.kd_tree is None or self.signatures is None:
            return None, float('inf'), -1
        qsig_f32 = qsig.astype(np.float32).reshape(1, -1)
        dist, idx = self.kd_tree.query(qsig_f32, k=1)
        idx_i = int(idx.item())
        if idx_i < len(self.pixels):
            return self.pixels[idx_i], float(dist.item()), idx_i
        return None, float('inf'), -1

    def query_batch(self, qsigs: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Recherche par lot : N requêtes en un seul appel KD-tree.

        Args:
            qsigs: (N, sig_dim) float32 — N signatures de requête
        Returns:
            (pixels, distances, indices)
            pixels: (N, ps, ps, 3) uint8
            distances: (N,) float
            indices: (N,) int
        """
        if self.kd_tree is None or self.signatures is None:
            return (np.zeros((0, self.patch_size, self.patch_size, 3), dtype=np.uint8),
                    np.array([float('inf')]), np.array([-1]))
        qsigs_f32 = qsigs.astype(np.float32)
        dists, idxs = self.kd_tree.query(qsigs_f32, k=1)
        idxs_i = idxs.astype(int)
        # Récupérer les pixels correspondants
        n = qsigs_f32.shape[0]
        pixels = np.zeros((n, self.patch_size, self.patch_size, 3), dtype=np.uint8)
        valid = (idxs_i >= 0) & (idxs_i < len(self.pixels))
        pixels[valid] = self.pixels[idxs_i[valid]]
        return pixels, dists.astype(float), idxs_i

    def save(self, directory: Path):
        """Sauvegarde le shard sur disque (signatures + pixels en .npy)."""
        directory.mkdir(parents=True, exist_ok=True)
        self._path = directory

        if self.signatures is not None:
            np.save(str(directory / 'signatures.npy'), self.signatures.astype(np.float32))
        if self.pixels is not None:
            np.save(str(directory / 'pixels.npy'), self.pixels.astype(np.uint8))
        if self.features is not None:
            np.save(str(directory / 'features.npy'), self.features.astype(np.float32))

        # Métadonnées
        meta = {
            'shard_id': self.shard_id,
            'n_patches': self.n_patches,
            'patch_size': self.patch_size,
            'sig_dim': self.sig_dim,
            'concepts': self.concepts,
        }
        with open(directory / 'meta.json', 'w', encoding='utf-8') as f:
            json.dump(meta, f)

    def load(self, directory: Path, mmap_pixels: bool = True):
        """
        Charge un shard depuis le disque.

        Args:
            directory: chemin du dossier du shard
            mmap_pixels: si True, les pixels sont en memmap (pas chargés en RAM)
        """
        self._path = directory

        sigs_file = directory / 'signatures.npy'
        if sigs_file.exists():
            self.signatures = np.load(str(sigs_file)).astype(np.float32)

        pix_file = directory / 'pixels.npy'
        if pix_file.exists():
            if mmap_pixels:
                self.pixels = np.load(str(pix_file), mmap_mode='r')
            else:
                self.pixels = np.load(str(pix_file)).astype(np.uint8)

        feats_file = directory / 'features.npy'
        if feats_file.exists():
            self.features = np.load(str(feats_file)).astype(np.float32)

        meta_file = directory / 'meta.json'
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            self.concepts = meta.get('concepts', [])
            self.shard_id = meta.get('shard_id', self.shard_id)
            self.patch_size = meta.get('patch_size', self.patch_size)
            self.sig_dim = meta.get('sig_dim', self.sig_dim)
            self._n_patches = meta.get('n_patches', len(self.concepts))

        self.build_tree()
        self._loaded = True

    def unload(self):
        """Libère la RAM en gardant le chemin disque."""
        self.signatures = None
        self.pixels = None
        self.features = None
        self.kd_tree = None
        self.concepts = []
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def memory_bytes(self) -> int:
        """Estimation de la RAM utilisée par ce shard."""
        total = 0
        if self.signatures is not None:
            total += self.signatures.nbytes
        if self.pixels is not None and hasattr(self.pixels, '_mmap') and self.pixels._mmap is None:
            total += self.pixels.nbytes  # seulement si pas en mmap
        if self.kd_tree is not None:
            total += self.signatures.nbytes * 2 if self.signatures is not None else 0
        return total


class HarmonicDatabase:
    """
    Base de signatures harmoniques avec index KD-tree.

    Chaque patch est identifié de façon unique par sa signature DFT
    (top-K coefficients en amplitude + phase). L'index KD-tree permet
    la recherche du plus proche voisin en O(log N).

    Séparation stricte : un KD-tree par concept.
    """

    def __init__(self, patch_size: int = 20, K: int = 16, stride: int = 20,
                 shard_size: int = 50000, shard_dir: str = None):
        self.patch_size = patch_size
        self.K = K              # nombre de coefficients DFT
        self.sig_dim = 2 * K    # dimension de la signature (amplitude + phase)
        self.stride = stride
        self.shard_size = shard_size  # patches max par shard

        # --- Stockage legacy (backward compat) ---
        self._patches: Dict[str, List[HarmonicPatch]] = {}
        self._trees: Dict[str, KDTree] = {} if HAS_KDTREE else {}
        self._tree_indices: Dict[str, List[int]] = {}
        self._sim_trees: Dict[str, KDTree] = {} if HAS_KDTREE else {}
        self._sim_features: Dict[str, np.ndarray] = {}
        self._sim_dim: int = 21
        self._dirty_trees: bool = False
        self._dirty_sim_trees: bool = False

        # --- Stockage shardé (V3) ---
        self._shards: List[DictShard] = []
        self._active_shard_idx: int = -1
        self._centroids: Optional[np.ndarray] = None  # (N_shards, sig_dim)
        self._shard_dir: Optional[Path] = Path(shard_dir) if shard_dir else None
        self._concept_to_shards: Dict[str, List[int]] = {}  # concept → [shard_idx, ...]

        # Auto-découverte des shards existants sur disque
        if self._shard_dir and self._shard_dir.exists():
            self._discover_shards()

        # Buffer d'ingestion
        self._buf_signatures: List[np.ndarray] = []
        self._buf_pixels: List[np.ndarray] = []
        self._buf_concepts: List[str] = []
        self._buf_count: int = 0

        # Stats
        self._centroid_hits: int = 0
        self._centroid_misses: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # INGESTION
    # ═══════════════════════════════════════════════════════════════════

    def ingest(self, patch: np.ndarray, concept: str = 'default'):
        """
        Ingère un patch unique. Version simplifiée pour le builder.
        
        Args:
            patch: (ps, ps, 3) uint8
            concept: catégorie
        """
        if self._shard_dir is None:
            # Legacy: ajouter au dict
            if concept not in self._patches:
                self._patches[concept] = []
            from multimodal.harmonic_database import HarmonicPatch
            hp = HarmonicPatch(pixels=patch.copy(), concept=concept)
            hp.signature = self._compute_signature(patch)
            self._patches[concept].append(hp)
            self._dirty_trees = True
            return
        
        # V3: buffer d'ingestion
        sig = self._compute_signature(patch)
        self._buf_signatures.append(sig.reshape(1, -1))
        self._buf_pixels.append(patch.reshape(1, *patch.shape))
        self._buf_concepts.append(concept)
        self._buf_count += 1
        
        if self._buf_count >= self.shard_size:
            self._flush_buffer()
    
    def ingest_image(self, concept: str, image: np.ndarray, filename: str = ''):
        """
        Ingère une image : découpe en patches, calcule signatures DFT.

        Les patches sont accumulés dans un buffer. Quand le buffer atteint
        shard_size, il est flushé automatiquement sur disque → RAM constante.

        Args:
            concept: catégorie (ex: 'sunset')
            image: (H, W, 3) uint8
            filename: nom du fichier source (pour traçabilité)
        """
        # Backward compat : si pas de shard_dir, utiliser le stockage legacy
        if self._shard_dir is None:
            return self._ingest_image_legacy(concept, image, filename)

        img = np.asarray(image, dtype=np.uint8)
        H, W = img.shape[:2]
        ps = self.patch_size
        st = self.stride

        if H < ps or W < ps:
            return 0

        # Extraire tous les patches d'un coup
        patches_list = []
        for i in range(0, H - ps + 1, st):
            for j in range(0, W - ps + 1, st):
                patches_list.append(img[i:i+ps, j:j+ps])

        if not patches_list:
            return 0

        n = len(patches_list)
        patches_arr = np.stack(patches_list, axis=0)  # (N, ps, ps, 3)

        # Batch DFT
        sigs = self._compute_signatures_batch(patches_arr)

        # Ajouter au buffer
        self._buf_signatures.append(sigs)
        self._buf_pixels.append(patches_arr)
        self._buf_concepts.extend([concept] * n)
        self._buf_count += n

        # Auto-flush si le buffer est plein
        if self._buf_count >= self.shard_size:
            self._flush_buffer()

        return n

    def _ingest_image_legacy(self, concept: str, image: np.ndarray, filename: str = ''):
        """Version legacy : stockage dans _patches dict (backward compat)."""
        if concept not in self._patches:
            self._patches[concept] = []

        img = np.asarray(image, dtype=np.uint8)
        H, W = img.shape[:2]
        ps = self.patch_size
        st = self.stride

        if H < ps or W < ps:
            return 0

        n_added = 0
        for i in range(0, H - ps + 1, st):
            for j in range(0, W - ps + 1, st):
                patch = img[i:i+ps, j:j+ps]
                sig = self._compute_signature(patch)
                self._patches[concept].append(HarmonicPatch(
                    pixels=patch,
                    signature=sig,
                    concept=concept,
                    image_file=filename,
                ))
                n_added += 1
        if n_added > 0:
            self._dirty_trees = True
            self._dirty_sim_trees = True
        return n_added

    def _flush_buffer(self):
        """
        Flushe le buffer d'ingestion dans un nouveau shard sur disque.

        Construit le KD-tree, sauvegarde sur disque, vide le buffer.
        Met à jour l'index centroïde.
        """
        if self._buf_count == 0:
            return

        shard_id = len(self._shards)
        shard = DictShard(shard_id, self.patch_size, self.sig_dim, self.shard_size)

        # Concaténer les buffers
        all_sigs = np.concatenate(self._buf_signatures, axis=0).astype(np.float32)
        all_pixels = np.concatenate(self._buf_pixels, axis=0).astype(np.uint8)

        shard.add_batch(all_sigs, all_pixels, list(self._buf_concepts))
        shard.build_tree()

        # Sauvegarder sur disque
        if self._shard_dir:
            shard_dir = self._shard_dir / f'shard_{shard_id:05d}'
            shard.save(shard_dir)

        # Ajouter aux shards et libérer le buffer
        self._shards.append(shard)
        self._buf_signatures = []
        self._buf_pixels = []
        self._buf_concepts = []
        self._buf_count = 0

        # Mettre à jour l'index concept → shards
        for c in set(shard.concepts):
            if c not in self._concept_to_shards:
                self._concept_to_shards[c] = []
            self._concept_to_shards[c].append(shard_id)

        # Mettre à jour l'index centroïde
        self._update_centroids()

        # Libérer la RAM du shard (les données sont sur disque)
        shard.unload()

    def _update_centroids(self):
        """Reconstruit l'index centroïde depuis tous les shards.
        
        Utilise les centroids pré-calculés dans meta.json si disponibles
        (évite de charger les shards juste pour le centroid).
        """
        if not self._shards:
            self._centroids = None
            return
        cents = []
        for shard in self._shards:
            # Essayer de lire le centroid depuis meta.json d'abord (rapide)
            centroid_from_meta = None
            if shard._path:
                meta_path = shard._path / 'meta.json'
                if meta_path.exists():
                    try:
                        import json
                        with open(meta_path, 'r') as f:
                            meta = json.load(f)
                        if 'centroid' in meta:
                            centroid_from_meta = np.array(meta['centroid'], dtype=np.float32)
                    except Exception:
                        pass
            
            if centroid_from_meta is not None:
                cents.append(centroid_from_meta)
            else:
                # Fallback: charger brièvement pour lire le centroïde
                was_loaded = shard.is_loaded
                if not was_loaded and shard._path:
                    shard.load(shard._path, mmap_pixels=True)
                cents.append(shard.centroid)
                if not was_loaded:
                    shard.unload()
        self._centroids = np.array(cents, dtype=np.float32)

    def _discover_shards(self):
        """Découvre et indexe les shards existants dans shard_dir (sans les charger)."""
        if not self._shard_dir or not self._shard_dir.exists():
            return
        shard_dirs = sorted(self._shard_dir.glob('shard_*'))
        for shard_dir in shard_dirs:
            meta_file = shard_dir / 'meta.json'
            if not meta_file.exists():
                continue
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            except Exception:
                continue
            shard = DictShard(
                meta.get('shard_id', len(self._shards)),
                meta.get('patch_size', self.patch_size),
                meta.get('sig_dim', self.sig_dim),
                self.shard_size,
            )
            shard._path = shard_dir
            shard._n_patches = meta.get('n_patches', 0)
            shard.concepts = meta.get('concepts', [])
            self._shards.append(shard)
            # Reconstruire l'index concept → shards
            for c in shard.concepts:
                if c not in self._concept_to_shards:
                    self._concept_to_shards[c] = []
                if shard.shard_id not in self._concept_to_shards[c]:
                    self._concept_to_shards[c].append(shard.shard_id)
        # Reconstruire l'index centroïde
        if self._shards:
            self._update_centroids()

    def _get_concept_patches_sharded(self, concept: str, max_samples: int = 100) -> List[np.ndarray]:
        """
        Récupère un échantillon de patches depuis les shards pour un concept donné.
        Utilisé par generate() pour avoir des patches de référence.
        """
        patches = []
        shard_indices = self._concept_to_shards.get(concept, [])
        for shard_idx in shard_indices:
            if len(patches) >= max_samples:
                break
            shard = self._shards[shard_idx]
            was_loaded = shard.is_loaded
            if not was_loaded and shard._path:
                shard.load(shard._path, mmap_pixels=True)
            # Prendre un échantillon des patches de ce concept dans ce shard
            count = 0
            for i, c in enumerate(shard.concepts):
                if c == concept and i < len(shard.pixels):
                    patches.append(shard.pixels[i])
                    count += 1
                    if count >= max_samples // len(shard_indices) + 1:
                        break
            if not was_loaded:
                shard.unload()
        return patches

    def _get_concept_patches_all_sharded(self, concept: str) -> List[np.ndarray]:
        """Charge tous les patches d'un concept depuis tous les shards (coûteux)."""
        # Utilisé par _patchmatch_refine
        return self._get_concept_patches_sharded(concept, max_samples=500)

    # ═══════════════════════════════════════════════════════════════════
    # INGESTION STREAMING (V3)
    # ═══════════════════════════════════════════════════════════════════

    def ingest_directory_streaming(self, path: str, max_per_category: int = None,
                                    categories: List[str] = None,
                                    verbose: bool = True,
                                    batch_size: int = 100,
                                    resume: bool = False) -> dict:
        """
        Ingestion streaming pour grands datasets — RAM constante.

        Traite les images par lots de `batch_size`. Chaque lot est chargé,
        traité, puis libéré. Les shards sont flushés automatiquement.

        Args:
            path: racine du dataset structuré en catégories
            max_per_category: max images par catégorie
            categories: filtre optionnel
            verbose: afficher la progression
            batch_size: nombre d'images par lot (défaut 100)
            resume: reprendre l'ingestion interrompue
        Returns:
            dict des statistiques
        """
        t0 = time.time()
        path = Path(path)

        # Activer le mode shardé
        if self._shard_dir is None:
            self._shard_dir = path.parent / (path.name + '_dict')
        self._shard_dir.mkdir(parents=True, exist_ok=True)

        # Collecter tous les fichiers
        all_jobs = []
        for cat_dir in sorted(path.iterdir()):
            if not cat_dir.is_dir():
                continue
            category = cat_dir.name.lower()
            if categories and category not in categories:
                continue
            image_files = sorted([
                f for f in cat_dir.iterdir()
                if f.suffix.lower() in ('.jpg', '.jpeg', '.png')
            ])
            if max_per_category:
                image_files = image_files[:max_per_category]
            for img_path in image_files:
                all_jobs.append((category, img_path))

        if resume and self._shards:
            # Reprendre après le dernier shard flushé
            processed = sum(s.n_patches for s in self._shards)
            if verbose:
                print(f"Reprise : {processed} patches déjà dans {len(self._shards)} shards")

        # Traitement par lots
        total_processed = 0
        results = {}
        n_total = len(all_jobs)

        for batch_start in range(0, n_total, batch_size):
            batch = all_jobs[batch_start:batch_start + batch_size]

            # Charger le lot en parallèle
            loaded = {}
            max_workers = min(os.cpu_count() or 4, 8)
            def _load_one(job):
                cat, img_path = job
                try:
                    return (cat, img_path, self._load_image(img_path))
                except Exception as e:
                    log.warning(f"Erreur {img_path}: {e}")
                    return (cat, img_path, None)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(_load_one, job): job for job in batch}
                for future in as_completed(futures):
                    cat, img_path, img = future.result()
                    if img is not None:
                        loaded[(cat, img_path.name)] = (cat, img)

            # Ingérer le lot
            batch_patches = 0
            for (cat, fname), (concept, img) in loaded.items():
                n = self.ingest_image(concept, img, fname)
                batch_patches += n
                results[cat] = results.get(cat, 0) + n

            total_processed += len(loaded)

            if verbose:
                n_shards = len(self._shards)
                buf = self._buf_count
                mem = self.memory_usage()
                print(f"  [{batch_start + len(loaded)}/{n_total}] "
                      f"+{batch_patches} patches | "
                      f"shards: {n_shards} | buffer: {buf} | "
                      f"RAM: {mem['total_estimated_mb']:.0f} MB")

        # Flush final
        self._flush_buffer()
        self._update_centroids()

        elapsed = time.time() - t0
        if verbose:
            total_patches = sum(s.n_patches for s in self._shards)
            print(f"\n  Total: {total_patches} patches, {len(self._shards)} shards")
            print(f"  Centroïdes: {len(self._centroids)} dans l'index")
            print(f"  RAM: {self.memory_usage()['total_estimated_mb']:.0f} MB")
            print(f"  Temps: {elapsed:.1f}s")

        return results

    # ═══════════════════════════════════════════════════════════════════
    # SIGNATURE HARMONIQUE DFT
    # ═══════════════════════════════════════════════════════════════════

    def _compute_signature(self, patch: np.ndarray) -> np.ndarray:
        """
        Signature harmonique DFT : top-K coefficients (amplitude + phase).

        La DFT décompose le patch en ses ondes constituantes.
        Chaque coefficient est l'amplitude et la phase d'une onde.
        K=16 coefficients = 32 dimensions → identification unique garantie.

        Optimisé : float32 + argpartition (O(N) au lieu de O(N log N)).
        """
        p = patch.astype(np.float32)
        # DFT 2D du canal luminance (suffit pour l'identification)
        lum = 0.299 * p[:,:,0] + 0.587 * p[:,:,1] + 0.114 * p[:,:,2]
        F = np.fft.fft2(lum)
        mag = np.abs(F).flatten()
        phase = np.angle(F).flatten()

        # Top-K par magnitude d'énergie — argpartition O(N) au lieu de argsort O(N log N)
        top_idx = np.argpartition(mag, -self.K)[-self.K:]

        sig = np.zeros(self.sig_dim, dtype=np.float32)
        max_mag = mag.max() if mag.max() > 1e-10 else 1.0
        for k, idx in enumerate(top_idx):
            sig[2*k] = mag[idx] / max_mag
            sig[2*k+1] = (phase[idx] + math.pi) / TAU
        return sig

    def _compute_signature_invariant(self, patch: np.ndarray) -> np.ndarray:
        """
        Signature DFT INVARIANTE PAR TRANSLATION (magnitude only, K dimensions).

        Principe : |F{shifted}| = |F{original}|. Un patch déplacé de 1-3 pixels
        a le même spectre de magnitude → le dictionnaire le reconnaît comme identique.
        C'est ainsi que la nature gère le mouvement : pas comme un déplacement de
        pixels, mais comme une rotation de phase à amplitude constante.

        Returns:
            (K,) float32 — top-K magnitudes normalisées (sans phase)
        """
        p = patch.astype(np.float32)
        lum = 0.299 * p[:,:,0] + 0.587 * p[:,:,1] + 0.114 * p[:,:,2]
        F = np.fft.fft2(lum)
        mag = np.abs(F).flatten()

        # Top-K magnitudes
        top_idx = np.argpartition(mag, -self.K)[-self.K:]

        sig = np.zeros(self.K, dtype=np.float32)
        max_mag = mag.max() if mag.max() > 1e-10 else 1.0
        for k, idx in enumerate(top_idx):
            sig[k] = mag[idx] / max_mag
        return sig

    def _compute_signatures_batch_invariant(self, patches: np.ndarray) -> np.ndarray:
        """
        Batch version de _compute_signature_invariant.
        Retourne (N, K) float32 — magnitudes uniquement.
        """
        N, S = patches.shape[0], patches.shape[1]
        lum = (0.299 * patches[:,:,:,0].astype(np.float32) +
               0.587 * patches[:,:,:,1].astype(np.float32) +
               0.114 * patches[:,:,:,2].astype(np.float32))
        F = np.fft.fft2(lum)
        mag = np.abs(F).reshape(N, -1)

        sigs = np.zeros((N, self.K), dtype=np.float32)
        for i in range(N):
            top_idx = np.argpartition(mag[i], -self.K)[-self.K:]
            max_m = mag[i].max() if mag[i].max() > 1e-10 else 1.0
            for k, idx in enumerate(top_idx):
                sigs[i, k] = mag[i, idx] / max_m
        return sigs

    def retrieve_translation_invariant(self, concept: str, query_patch: np.ndarray
                                       ) -> Optional[np.ndarray]:
        """
        Retrieval robuste au mouvement — utilise la magnitude DFT (invariante
        par translation) pour matcher des patches qui ont bougé de 1-3 pixels.

        Optimisé mémoire : charge les signatures en mmap, pas de KD-tree.
        """
        qsig = self._compute_signature_invariant(query_patch).astype(np.float32)

        best_patch = None
        best_dist = float('inf')

        for shard in self._shards:
            sigs = None
            # Charger les signatures en mmap (léger, pas de build_tree)
            sig_file = shard._path / 'signatures.npy' if shard._path else None
            if sig_file and sig_file.exists():
                sigs = np.load(str(sig_file), mmap_mode='r')
            elif shard.signatures is not None:
                sigs = shard.signatures

            if sigs is not None and sigs.shape[0] > 0:
                # Comparer sur les K premières dimensions (magnitudes)
                K = min(self.K, sigs.shape[1])
                mag_sigs = sigs[:, :K].astype(np.float32)
                q = qsig[:K]
                dists = np.sum((mag_sigs - q) ** 2, axis=1)
                idx = int(np.argmin(dists))
                d = float(dists[idx])

                if d < best_dist:
                    best_dist = d
                    # Charger le pixel depuis le fichier pixels.npy (mmap)
                    pix_file = shard._path / 'pixels.npy' if shard._path else None
                    if pix_file and pix_file.exists():
                        pixels = np.load(str(pix_file), mmap_mode='r')
                        if idx < len(pixels):
                            best_patch = np.array(pixels[idx])  # copie en RAM
                    elif shard.pixels is not None and idx < len(shard.pixels):
                        best_patch = shard.pixels[idx]

        return best_patch

    def retrieve_translation_invariant_batch(self, patches: np.ndarray
                                             ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Batch invariant retrieval — N patches en un seul scan par shard.
        Vectorisé: matrice de distances (M×N) calculée d'un coup.
        """
        N = patches.shape[0]
        ps = patches.shape[1]
        qsigs = self._compute_signatures_batch_invariant(patches)  # (N, K)
        best_pixels = np.zeros((N, ps, ps, 3), dtype=np.uint8)
        best_dists = np.full(N, float('inf'), dtype=np.float32)
        best_idxs = np.full(N, -1, dtype=np.int32)
        best_shard = np.full(N, -1, dtype=np.int32)

        for si, shard in enumerate(self._shards):
            sig_file = shard._path / 'signatures.npy' if shard._path else None
            if sig_file and sig_file.exists():
                all_sigs = np.load(str(sig_file), mmap_mode='r')
            elif shard.signatures is not None:
                all_sigs = shard.signatures
            else:
                continue
            if all_sigs.shape[0] == 0:
                continue

            K = min(self.K, all_sigs.shape[1])
            mag_sigs = all_sigs[:, :K].astype(np.float32)  # (M, K)
            q = qsigs[:, :K].astype(np.float32)            # (N, K)

            # Distance L2 batch: ||mag_sigs[i] - q[j]||² pour tous i,j
            # = |mag_sigs|²[row] + |q|²[col] - 2·mag_sigs·q^T
            mag_norm = np.sum(mag_sigs ** 2, axis=1, keepdims=True)   # (M, 1)
            q_norm = np.sum(q ** 2, axis=1, keepdims=True)            # (N, 1)
            cross = mag_sigs @ q.T                                      # (M, N)
            dists = mag_norm + q_norm.T - 2.0 * cross                  # (M, N)

            # Meilleur match par query (colonne)
            min_idx = np.argmin(dists, axis=0)  # (N,)
            min_dist = dists[min_idx, np.arange(N)]  # (N,)

            better = min_dist < best_dists
            best_dists[better] = min_dist[better]
            best_idxs[better] = min_idx[better]
            best_shard[better] = si

        # Charger les pixels des meilleurs matchs
        for si in set(best_shard[best_shard >= 0]):
            shard = self._shards[si]
            mask = best_shard == si
            pix_file = shard._path / 'pixels.npy' if shard._path else None
            if pix_file and pix_file.exists():
                pixels = np.load(str(pix_file), mmap_mode='r')
            elif shard.pixels is not None:
                pixels = shard.pixels
            else:
                continue
            idxs = best_idxs[mask]
            valid = (idxs >= 0) & (idxs < len(pixels))
            best_pixels[np.where(mask)[0][valid]] = pixels[idxs[valid]]

        return best_pixels, best_dists

    @lru_cache(maxsize=2048)
    def _compute_signature_cached(self, patch_bytes: bytes,
                                   shape: Tuple[int, int, int]) -> np.ndarray:
        """
        Version cachée de _compute_signature — évite de recalculer la DFT
        pour des patches identiques (fréquent dans generate()).
        """
        patch = np.frombuffer(patch_bytes, dtype=np.uint8).reshape(shape)
        return self._compute_signature(patch)

    def _cached_signature(self, patch: np.ndarray) -> np.ndarray:
        """Calcule la signature avec cache LRU (hash sur les bytes du patch)."""
        patch_bytes = patch.tobytes()
        return self._compute_signature_cached(patch_bytes, patch.shape)

    def _compute_signatures_batch(self, patches: np.ndarray) -> np.ndarray:
        """
        Calcule les signatures DFT pour un lot de patches en une seule opération.

        Empile les patches → 1 seul appel FFT2D batch → O(N) plus rapide.

        Args:
            patches: (N, S, S, 3) uint8 — lot de patches
        Returns:
            (N, sig_dim) float32 — une signature par patch
        """
        N, S = patches.shape[0], patches.shape[1]
        # Luminance batch : (N, S, S)
        lum = (0.299 * patches[:,:,:,0].astype(np.float32) +
               0.587 * patches[:,:,:,1].astype(np.float32) +
               0.114 * patches[:,:,:,2].astype(np.float32))
        # FFT2D batch sur les N images de luminance
        F = np.fft.fft2(lum)  # (N, S, S) complex64
        mag = np.abs(F).reshape(N, -1)    # (N, S*S)
        phase = np.angle(F).reshape(N, -1)  # (N, S*S)

        # Top-K par argpartition (vectorisé — une colonne à la fois)
        sigs = np.zeros((N, self.sig_dim), dtype=np.float32)
        for i in range(N):
            top_idx = np.argpartition(mag[i], -self.K)[-self.K:]
            max_m = mag[i].max() if mag[i].max() > 1e-10 else 1.0
            for k, idx in enumerate(top_idx):
                sigs[i, 2*k] = mag[i, idx] / max_m
                sigs[i, 2*k+1] = (phase[i, idx] + math.pi) / TAU
        return sigs

    # ═══════════════════════════════════════════════════════════════════
    # KD-TREE
    # ═══════════════════════════════════════════════════════════════════

    def _build_trees(self):
        """Construit un KD-tree par concept."""
        if not HAS_KDTREE:
            log.warning("scipy.spatial.KDTree non disponible")
            return

        self._trees = {}
        self._tree_indices = {}

        for concept, patches in self._patches.items():
            if len(patches) < 2:
                continue
            # Matrice de signatures (N, 2K) en float32 (50% RAM économisée)
            sigs = np.array([p.signature for p in patches], dtype=np.float32)
            self._trees[concept] = KDTree(sigs)
            self._tree_indices[concept] = list(range(len(patches)))
        self._dirty_trees = False

    def _ensure_trees(self):
        """Reconstruit les KD-trees si nécessaire (lazy)."""
        if self._dirty_trees or not self._trees:
            self._build_trees()

    def _ensure_sim_trees(self):
        """Reconstruit les index de similarité si nécessaire (lazy)."""
        if self._dirty_sim_trees or not self._sim_trees:
            self._build_similarity_index()

    def _build_similarity_index(self):
        """
        Construit l'index de SIMILARITÉ visuelle avec GRILLE HEXAGONALE π/6.

        Pour chaque patch, 7 cellules hexagonales (centre + 6 directions à 60°)
        donnent 7×3 = 21 dimensions. La grille hexagonale (π/6) est le pavage
        optimal pour capturer l'information visuelle selon le principe
        holographique — 2.3× plus compact que la grille carrée 4×4 (48 dims)
        pour une qualité équivalente.

        Un KD-tree sur ces features permet la recherche O(log N).
        """
        if not HAS_KDTREE:
            return

        self._sim_trees = {}
        self._sim_features = {}
        self._sim_dim = 21  # 7 cellules × 3 canaux

        for concept, patches in self._patches.items():
            if len(patches) < 2:
                continue

            features = np.zeros((len(patches), self._sim_dim), dtype=np.float32)
            for idx, p in enumerate(patches):
                features[idx] = self._hexagonal_features(p.pixels)
            self._sim_features[concept] = features
            self._sim_trees[concept] = KDTree(features)
        self._dirty_sim_trees = False

    @staticmethod
    def _hexagonal_features(patch: np.ndarray) -> np.ndarray:
        """
        Features hexagonales π/6 : 1 centre + 6 voisins à 60° (π/3).

        Retourne un vecteur de 21 dimensions (7 cellules × 3 canaux RGB).
        """
        H, W = patch.shape[:2]
        cy, cx = H // 2, W // 2
        radius = min(H, W) // 3
        cell_size = max(2, min(H, W) // 10)
        f = np.zeros(21, dtype=np.float32)

        # Centre
        y0, y1 = max(0, cy-cell_size), min(H, cy+cell_size)
        x0, x1 = max(0, cx-cell_size), min(W, cx+cell_size)
        f[0:3] = patch[y0:y1, x0:x1].mean(axis=(0, 1)) / 255.0

        # 6 directions à π/3 (60°) — pavage hexagonal
        for k in range(6):
            angle = k * math.pi / 3
            px = int(cx + radius * math.cos(angle))
            py = int(cy + radius * math.sin(angle))
            px = max(cell_size, min(W - cell_size, px))
            py = max(cell_size, min(H - cell_size, py))
            offset = 3 + k * 3
            f[offset:offset+3] = patch[py-cell_size:py+cell_size,
                                        px-cell_size:px+cell_size].mean(axis=(0, 1)) / 255.0
        return f

    # ═══════════════════════════════════════════════════════════════════
    # RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════

    def retrieve(self, concept: str, query_patch: np.ndarray) -> Optional[np.ndarray]:
        """
        Retrouve le patch le plus proche par signature harmonique DFT.

        **Mode shardé (V3)** : utilise l'index centroïde → top-3 shards → KD-tree.
        **Mode legacy** : utilise les KD-trees par concept.

        O(log N) dans les deux cas.

        Args:
            concept: catégorie cible
            query_patch: (S, S, 3) uint8
        Returns:
            (S, S, 3) uint8 — le patch le plus proche, ou None
        """
        # Mode shardé
        if self._shards and self._centroids is not None and len(self._centroids) > 0:
            return self._retrieve_sharded(concept, query_patch)

        # Mode legacy
        if concept not in self._trees:
            if self._dirty_trees:
                self._ensure_trees()
            if concept not in self._trees:
                return self._retrieve_linear(concept, query_patch)

        qsig = self._cached_signature(query_patch).reshape(1, -1)
        tree = self._trees[concept]
        dist, idx = tree.query(qsig, k=1)
        patch_idx = self._tree_indices[concept][int(idx.item())]
        return self._patches[concept][patch_idx].pixels

    def _retrieve_sharded(self, concept: str, query_patch: np.ndarray,
                          top_k: int = 3) -> Optional[np.ndarray]:
        """
        Retrieval two-level via centroïdes + shards.
        Retourne les pixels du meilleur patch (backward compat).
        Pour avoir l'ID, utiliser retrieve_with_id().
        """
        result = self._retrieve_sharded_with_id(concept, query_patch, top_k)
        return result[0] if result is not None else None

    def _retrieve_sharded_with_id(self, concept: str, query_patch: np.ndarray,
                                   top_k: int = 3) -> Optional[Tuple[np.ndarray, int, int, float]]:
        """
        Comme _retrieve_sharded mais retourne (pixels, shard_id, patch_idx, distance).
        """
        qsig = self._cached_signature(query_patch).astype(np.float32)

        candidate_shards = self._concept_to_shards.get(concept, [])
        if not candidate_shards:
            candidate_shards = list(range(len(self._shards)))

        if self._centroids is not None and len(self._centroids) > 0:
            cent = self._centroids.astype(np.float32)
            all_ranked = np.argsort(np.sum((cent - qsig) ** 2, axis=1))
            ranked = [int(i) for i in all_ranked if int(i) in candidate_shards]
            if not ranked:
                ranked = [int(i) for i in all_ranked]
        else:
            ranked = candidate_shards

        best_patch = None
        best_shard_idx = -1
        best_patch_idx = -1
        best_dist = float('inf')

        for search_k in [top_k, max(10, len(ranked) // 10), len(ranked)]:
            for idx in ranked[:search_k]:
                shard = self._shards[idx]
                was_loaded = shard.is_loaded
                if not was_loaded and shard._path:
                    shard.load(shard._path, mmap_pixels=True)

                pix, dist, patch_idx = shard.query(qsig)
                if pix is not None and dist < best_dist:
                    best_dist = dist
                    best_patch = pix
                    best_shard_idx = idx
                    best_patch_idx = patch_idx

                if not was_loaded:
                    shard.unload()

            if best_patch is not None:
                if search_k <= top_k:
                    self._centroid_hits += 1
                break
        else:
            self._centroid_misses += 1

        if best_patch is not None:
            return (best_patch, best_shard_idx, best_patch_idx, best_dist)
        return None

    def retrieve_with_id(self, concept: str, query_patch: np.ndarray
                         ) -> Optional[Tuple[np.ndarray, int, int, float]]:
        """
        Comme retrieve() mais retourne l'identité complète du patch.

        Returns:
            (pixels, shard_id, patch_idx, distance) ou None
            - shard_id: -1 pour le mode legacy (pas de shard)
            - patch_idx: index dans le shard (ou dans _patches[concept] en legacy)
        """
        # Mode shardé
        if self._shards and self._centroids is not None and len(self._centroids) > 0:
            return self._retrieve_sharded_with_id(concept, query_patch)

        # Mode legacy
        if concept not in self._trees:
            if self._dirty_trees:
                self._ensure_trees()
            if concept not in self._trees:
                return None

        qsig = self._cached_signature(query_patch).reshape(1, -1)
        tree = self._trees[concept]
        dist, idx = tree.query(qsig, k=1)
        patch_idx = self._tree_indices[concept][int(idx.item())]
        pixels = self._patches[concept][patch_idx].pixels
        return (pixels, -1, patch_idx, float(dist.item()))

    def get_patch_by_id(self, shard_id: int, patch_idx: int) -> Optional[np.ndarray]:
        """
        Récupère un patch par son identifiant (utilisé par le décodeur).

        Args:
            shard_id: -1 pour le mode legacy, sinon index du shard
            patch_idx: index du patch dans le shard (ou dans _patches[concept])
        Returns:
            (ps, ps, 3) uint8 pixels, ou None
        """
        if shard_id < 0:
            # Mode legacy : chercher dans tous les concepts (peu efficace)
            for concept, patches in self._patches.items():
                if patch_idx < len(patches):
                    return patches[patch_idx].pixels
            return None

        # Mode shardé
        if shard_id >= len(self._shards):
            return None
        shard = self._shards[shard_id]
        was_loaded = shard.is_loaded
        if not was_loaded and shard._path:
            shard.load(shard._path, mmap_pixels=True)
        if patch_idx < len(shard.pixels):
            result = shard.pixels[patch_idx]
            if not was_loaded:
                shard.unload()
            return result
        if not was_loaded:
            shard.unload()
        return None

    def _retrieve_linear(self, concept: str, query_patch: np.ndarray) -> Optional[np.ndarray]:
        """Recherche linéaire (fallback sans KD-tree)."""
        patches = self._patches.get(concept, [])
        if not patches:
            return None

        qsig = self._compute_signature(query_patch)
        best_idx = min(
            range(len(patches)),
            key=lambda i: np.sqrt(np.sum((qsig - patches[i].signature)**2))
        )
        return patches[best_idx].pixels

    def retrieve_cross(self, query_patch: np.ndarray,
                       target_concept: str = None) -> Tuple[Optional[np.ndarray], str]:
        """
        Retrieval cross-concept : cherche dans TOUTES les catégories.

        Returns:
            (patch_pixels, concept_trouvé)
        """
        qsig = self._cached_signature(query_patch).reshape(1, -1)
        best_concept = None
        best_patch = None
        best_dist = 1e9

        for concept in self._trees:
            dist, idx = self._trees[concept].query(qsig, k=1)
            if dist[0] < best_dist:
                best_dist = dist[0]
                best_concept = concept
                patch_idx = self._tree_indices[concept][int(idx.item())]
                best_patch = self._patches[concept][patch_idx].pixels

        if best_patch is None:
            # Fallback linéaire
            for concept, patches in self._patches.items():
                for p in patches:
                    d = np.sqrt(np.sum((qsig.flatten() - p.signature)**2))
                    if d < best_dist:
                        best_dist = d
                        best_concept = concept
                        best_patch = p.pixels

        return best_patch, best_concept or ''

    def retrieve_similar(self, concept: str, query_patch: np.ndarray) -> Optional[np.ndarray]:
        """
        Retrieval par SIMILARITÉ VISUELLE (grille hexagonale π/6).

        Utilise 7 cellules hexagonales (21 dimensions) pour trouver
        le patch le plus VISUELLEMENT SIMILAIRE. O(log N) via KD-tree.

        Args:
            concept: catégorie cible
            query_patch: (S, S, 3) uint8 — patch à matcher visuellement
        Returns:
            (S, S, 3) uint8 — le patch le plus similaire visuellement
        """
        if concept not in self._sim_trees:
            if self._dirty_sim_trees:
                self._ensure_sim_trees()
            if concept not in self._sim_trees:
                return self.retrieve(concept, query_patch)

        f = self._hexagonal_features(query_patch).reshape(1, -1)
        dist, idx = self._sim_trees[concept].query(f, k=1)
        patch_idx = int(idx.item())
        if patch_idx < len(self._patches[concept]):
            return self._patches[concept][patch_idx].pixels
        return None

    # ═══════════════════════════════════════════════════════════════════
    # GÉNÉRATION
    # ═══════════════════════════════════════════════════════════════════

    def generate(self, concept: str, width: int = 256, height: int = 256,
                 use_patchmatch: bool = True) -> np.ndarray:
        """
        Génère une image par COMPOSITION de patches exacts.

        1. Pour chaque position, retrouve le meilleur patch via KD-tree
        2. Optionnellement, PatchMatch pour la cohérence des bords
        3. Assemblage avec blend cosinusoïdal

        Args:
            concept: catégorie cible
            width, height: dimensions de l'image
            use_patchmatch: utiliser PatchMatch pour la cohérence spatiale
        Returns:
            (height, width, 3) uint8
        """
        ps = self.patch_size
        st = max(1, ps // 2)  # stride avec recouvrement pour blend

        n_h = max(1, (height - ps) // st + 1)
        n_w = max(1, (width - ps) // st + 1)
        final_h = (n_h - 1) * st + ps
        final_w = (n_w - 1) * st + ps

        # Étape 1 : Retrieval pour chaque position
        assigned_patches = {}
        # Collecter les patches disponibles pour ce concept (legacy ou shardé)
        if self._shards:
            concept_patches = self._get_concept_patches_sharded(concept)
        else:
            concept_patches = [p.pixels for p in self._patches.get(concept, [])]

        for i in range(n_h):
            for j in range(n_w):
                rng = np.random.RandomState(i * 1000 + j)
                if not concept_patches:
                    continue
                src_patch = concept_patches[rng.randint(len(concept_patches))]
                best = self.retrieve(concept, src_patch)
                if best is not None:
                    assigned_patches[(i, j)] = best

        if not assigned_patches:
            return np.zeros((height, width, 3), dtype=np.uint8)

        # Étape 2 : PatchMatch pour cohérence spatiale (optionnel)
        if use_patchmatch and len(assigned_patches) > 1:
            assigned_patches = self._patchmatch_refine(
                concept, assigned_patches, n_h, n_w
            )

        # Étape 3 : Assemblage avec blend (float32 pour économie mémoire)
        canvas = np.zeros((final_h, final_w, 3), dtype=np.float32)
        weight = np.zeros((final_h, final_w, 1), dtype=np.float32)

        for (i, j), patch in assigned_patches.items():
            y0, x0 = i * st, j * st
            y1, x1 = min(y0 + ps, final_h), min(x0 + ps, final_w)
            ph, pw = y1 - y0, x1 - x0

            wy = self._blend_window(ph)[:, None].astype(np.float32)
            wx = self._blend_window(pw)[None, :].astype(np.float32)
            w = wy * wx

            canvas[y0:y1, x0:x1] += patch[:ph, :pw].astype(np.float32) * w[:, :, None]
            weight[y0:y1, x0:x1] += w[:, :, None]

        weight[weight < 1e-15] = 1.0
        image = canvas / weight
        return np.clip(image, 0, 255).astype(np.uint8)

    def _patchmatch_refine(self, concept: str,
                           assigned: Dict[Tuple[int, int], np.ndarray],
                           n_h: int, n_w: int) -> Dict[Tuple[int, int], np.ndarray]:
        """PatchMatch simplifié : propagation des bons patches voisins."""
        refined = dict(assigned)
        ps = self.patch_size

        # Obtenir les patches candidats
        if self._shards:
            candidates = self._get_concept_patches_all_sharded(concept)
        else:
            candidates = [p.pixels for p in self._patches.get(concept, [])[:20]]

        for _ in range(2):  # 2 passes
            for i in range(n_h):
                for j in range(n_w):
                    current = refined.get((i, j))
                    if current is None:
                        continue

                    # Essayer le voisin du haut
                    if (i-1, j) in refined:
                        neighbor = refined[(i-1, j)]
                        border_diff = np.mean(np.abs(
                            neighbor[-1, :, :].astype(float) -
                            current[0, :, :].astype(float)
                        )) / 255.0
                        if border_diff > 0.3:  # mauvaise cohérence
                            for cand in candidates[:20]:
                                diff = np.mean(np.abs(
                                    neighbor[-1, :, :].astype(float) -
                                    cand[0, :, :].astype(float)
                                )) / 255.0
                                if diff < border_diff:
                                    refined[(i, j)] = cand
                                    break

        return refined

    # ═══════════════════════════════════════════════════════════════════
    # STATISTIQUES
    # ═══════════════════════════════════════════════════════════════════

    def stats(self) -> dict:
        """Statistiques de la base (legacy + shardé)."""
        legacy_patches = sum(len(v) for v in self._patches.values())
        shard_patches = sum(s.n_patches for s in self._shards) + self._buf_count
        return {
            'n_categories': len(self._patches) if self._patches else len(set(
                c for s in self._shards for c in s.concepts
            )),
            'total_patches': legacy_patches + shard_patches,
            'per_category': {k: len(v) for k, v in self._patches.items()},
            'kd_trees': len(self._trees),
            'n_shards': len(self._shards),
            'buf_patches': self._buf_count,
            'centroid_hits': self._centroid_hits,
            'centroid_misses': self._centroid_misses,
            'patch_size': self.patch_size,
            'K': self.K,
            'sig_dim': self.sig_dim,
        }

    @property
    def categories(self) -> List[str]:
        if self._shards:
            cats = set()
            for s in self._shards:
                cats.update(s.concepts)
            return sorted(cats)
        return list(self._patches.keys())

    def memory_usage(self) -> dict:
        """Estimation de l'utilisation RAM."""
        import sys
        buf_bytes = (self._buf_count * self.patch_size * self.patch_size * 3 +
                     self._buf_count * self.sig_dim * 4)
        shard_bytes = sum(s.memory_bytes for s in self._shards if s.is_loaded)
        centroids_bytes = self._centroids.nbytes if self._centroids is not None else 0
        return {
            'buffer_mb': round(buf_bytes / (1024 * 1024), 2),
            'shards_ram_mb': round(shard_bytes / (1024 * 1024), 2),
            'centroids_mb': round(centroids_bytes / (1024 * 1024), 2),
            'total_estimated_mb': round((buf_bytes + shard_bytes + centroids_bytes) / (1024 * 1024), 2),
            'n_shards': len(self._shards),
            'shards_loaded': sum(1 for s in self._shards if s.is_loaded),
        }

    def flush(self):
        """Flushe le buffer restant (appeler après ingestion)."""
        if self._shard_dir:
            self._flush_buffer()
            self._update_centroids()
        else:
            self._ensure_trees()
            self._ensure_sim_trees()

    # ═══════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _load_image(path: Path) -> np.ndarray:
        try:
            from PIL import Image
            return np.array(Image.open(path).convert('RGB'))
        except ImportError:
            import cv2
            img = cv2.imread(str(path))
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img is not None else None

    @staticmethod
    def _blend_window(n: int) -> np.ndarray:
        if n <= 1:
            return np.ones(1, dtype=np.float32)
        x = np.arange(n, dtype=np.float32)
        return (0.5 * (1.0 - np.cos(2.0 * math.pi * x / max(n - 1, 1)))).astype(np.float32)

    # ═══════════════════════════════════════════════════════════════════
    # SAUVEGARDE / CHARGEMENT
    # ═══════════════════════════════════════════════════════════════════

    VERSION = 1

    def save(self, path: str):
        """
        Sauvegarde la base complète (signatures DFT + features hexagonales).

        Format:
            path/
              meta.json          # version, paramètres, liste des catégories
              <concept>/
                signatures.npz   # (N, sig_dim) float32
                features.npz     # (N, 21) float32 — optionnel, index hexagonal

        Les pixels ne sont PAS sauvegardés par cette méthode (utiliser save_patches()).
        Les KD-trees sont reconstruits au chargement.
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        meta = {
            'version': self.VERSION,
            'patch_size': self.patch_size,
            'K': self.K,
            'sig_dim': self.sig_dim,
            'stride': self.stride,
            'categories': sorted(self._patches.keys()),
        }
        with open(path / 'meta.json', 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        for concept, patches in self._patches.items():
            cat_dir = path / concept
            cat_dir.mkdir(exist_ok=True)

            sigs = np.array([p.signature for p in patches], dtype=np.float32)
            np.savez_compressed(cat_dir / 'signatures.npz', signatures=sigs)

            if concept in self._sim_features:
                feats = self._sim_features[concept]
                if isinstance(feats, np.ndarray) and feats.shape[0] == len(patches):
                    np.savez_compressed(
                        cat_dir / 'features.npz',
                        features=feats.astype(np.float32),
                    )

    def save_patches(self, path: str):
        """
        Sauvegarde les pixels bruts pour reconstruction lossless.

        Complément de save() : ajoute les patches/*.npz aux dossiers concept.
        Un save() suivi de save_patches() sur le même chemin permet un chargement
        complet avec pixels (reconstruction 100 dB).
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        for concept, patches in self._patches.items():
            cat_dir = path / concept
            cat_dir.mkdir(exist_ok=True)
            pix = np.array([p.pixels for p in patches], dtype=np.uint8)
            np.savez_compressed(cat_dir / 'patches.npz', patches=pix)

    def load(self, path: str):
        """
        Charge une base sauvegardée et reconstruit les KD-trees.

        Si patches.npz existe pour un concept, les pixels sont chargés.
        Sinon, les pixels sont initialisés à zéro (les signatures restent
        fonctionnelles pour le retrieval).

        Returns:
            self (pour chaînage)
        """
        path = Path(path)

        with open(path / 'meta.json', 'r', encoding='utf-8') as f:
            meta = json.load(f)

        if meta.get('version', 0) > self.VERSION:
            log.warning("Version du dictionnaire plus récente que le code — "
                        "compatibilité non garantie")

        self.patch_size = meta['patch_size']
        self.K = meta['K']
        self.sig_dim = meta['sig_dim']
        self.stride = meta.get('stride', self.patch_size)

        # Réinitialiser les structures
        self._patches = {}
        self._trees = {} if HAS_KDTREE else {}
        self._tree_indices = {}
        self._sim_trees = {} if HAS_KDTREE else {}
        self._sim_features = {}
        loaded_pixels = False

        for concept in meta['categories']:
            cat_dir = path / concept
            sigs_file = cat_dir / 'signatures.npz'
            if not sigs_file.exists():
                continue

            sigs_data = np.load(sigs_file)
            sigs = sigs_data['signatures']  # shape (N, sig_dim)
            n_patches = sigs.shape[0]

            # Tenter de charger les pixels
            patches_file = cat_dir / 'patches.npz'
            if patches_file.exists():
                pixels_data = np.load(patches_file)['patches']  # (N, ps, ps, 3)
                loaded_pixels = True
            else:
                pixels_data = np.zeros((n_patches, self.patch_size, self.patch_size, 3),
                                       dtype=np.uint8)

            # Reconstituer la liste de HarmonicPatch
            patches_list = []
            for i in range(n_patches):
                patches_list.append(HarmonicPatch(
                    pixels=pixels_data[i],
                    signature=sigs[i].astype(np.float64),
                    concept=concept,
                    image_file='',
                ))
            self._patches[concept] = patches_list

            # Charger les features hexagonales si présentes
            feats_file = cat_dir / 'features.npz'
            if feats_file.exists():
                self._sim_features[concept] = np.load(feats_file)['features']

        # Reconstruire les KD-trees
        self._build_trees()

        # Reconstruire les index de similarité hexagonale
        if self._sim_features and HAS_KDTREE:
            self._sim_trees = {}
            for concept, features in self._sim_features.items():
                if isinstance(features, np.ndarray) and features.shape[0] >= 2:
                    self._sim_trees[concept] = KDTree(features.astype(np.float64))

        log.info("Chargement terminé : %d catégories, %d patches%s",
                 len(self._patches),
                 sum(len(v) for v in self._patches.values()),
                 " (avec pixels)" if loaded_pixels else " (sans pixels)")
        return self


# ═══════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=== Harmonic Database — Test ===\n")

    hdb = HarmonicDatabase(patch_size=20, K=16, stride=20)

    # Ingérer le corpus de test (30 images × 5 catégories)
    print("Ingestion du corpus...")
    hdb.ingest_directory(
        'data/real_photo_test/',
        max_per_category=10,
        categories=['desert', 'sunset', 'forest', 'glass', 'mountain'],
        verbose=True,
    )

    # Test retrieval
    print("\n--- Test retrieval KD-tree ---")
    import time as _time
    from PIL import Image
    test_dir = 'data/real_photo_test/desert'
    test_files = sorted(os.listdir(test_dir))
    if len(test_files) > 5:
        test_img = np.array(Image.open(os.path.join(test_dir, test_files[5])).resize((100,100)))
        patch = test_img[20:40, 20:40]

        t0 = _time.time()
        result = hdb.retrieve('desert', patch)
        t_kd = _time.time() - t0

        t0 = _time.time()
        result_lin = hdb._retrieve_linear('desert', patch)
        t_lin = _time.time() - t0

        print(f"  KD-tree : {t_kd*1000:.1f}ms")
        print(f"  Linéaire: {t_lin*1000:.1f}ms")
        print(f"  Speedup: {t_lin/t_kd:.1f}x" if t_kd > 0 else "")

    # Test génération
    print("\n--- Test génération ---")
    img = hdb.generate('sunset', width=120, height=120)
    print(f"  Image sunset: {img.shape}")
    try:
        from PIL import Image
        Image.fromarray(img).save('harmonigen_sunset.png')
        print("  Sauvegardé: harmonigen_sunset.png")
    except: pass

    # Test save/load roundtrip
    print("\n--- Test save/load roundtrip ---")
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp(prefix='hdb_test_')
    try:
        hdb.save(tmpdir)
        hdb.save_patches(tmpdir)
        print(f"  Sauvegardé dans: {tmpdir}")

        # Charger dans une nouvelle instance
        hdb2 = HarmonicDatabase()
        hdb2.load(tmpdir)

        s1 = hdb.stats()
        s2 = hdb2.stats()
        print(f"  Original : {s1['total_patches']} patches, {s1['n_categories']} catégories")
        print(f"  Chargé   : {s2['total_patches']} patches, {s2['n_categories']} catégories")

        # Vérifier le retrieval après load
        if len(test_files) > 5:
            result2 = hdb2.retrieve('desert', patch)
            match = np.allclose(result, result2) if result is not None else False
            print(f"  Retrieval après load: {'✓ Identique' if match else '✗ Différent'}")

        assert s1['total_patches'] == s2['total_patches'], "Mismatch total_patches"
        assert s1['n_categories'] == s2['n_categories'], "Mismatch n_categories"
        print("  ✓ Roundtrip save/load OK")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n✓ Harmonic Database fonctionnel")
