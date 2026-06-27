#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HF RESIDUE TRANSFER — Transfert de Résidu HF depuis le Corpus
================================================================
Implémente la solution au gap HF : au lieu de synthétiser du bruit 1/f²,
on EXTRAIT le vrai résidu SVD des images du corpus et on le TRANSFÈRE.

Mécanisme (identique à harmonic_creativity_engine.remix_style) :
  1. Corpus → SVD K=16 → reconstruction → résidu = original - reconstruction
  2. Stocker les résidus + embeddings dans une banque
  3. Image générée → embedding → K plus proches résidus du corpus
  4. Fusion Hₙ-pondérée + conditionnement spatial (edge/variance maps)
  5. Injection : enhanced = base + résidu_transféré × gain_spatial

Pourquoi ça marche :
  - Le résidu SVD d'une photo réelle contient de VRAIS bords, textures, grain
  - Le transfert de résidu = transfert de la "signature HF" d'une image naturelle
  - C'est l'équivalent exact du transfert de style mais pour les hautes fréquences

Architecture inspirée de :
  - harmonic_creativity_engine.py:remix_style() (transfert d'hologramme)
  - harmonic_detail_synthesizer.py (injection de résidu + amplification Hₙ)
  - steerable_sharpener.py (gain spatial adaptatif)

Usage :
  python hf_residue_transfer.py --build-bank    # Construire la banque de résidus
  python hf_residue_transfer.py --demo          # Test avec benchmark Q_HF
"""

import sys, os, numpy as np, math, time, glob, argparse, pickle
from typing import Dict, Any, List, Optional, Tuple
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image
from scipy.ndimage import laplace as lap_func
from harmonic_generator_core import (
    HarmonicField, HarmonicColorMapper, normalize_field,
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, H_CONSTANTS, SeedManager,
)
from holographic_one_shot import (
    HolographicTrainer, HolographicSignature, HolographicGenerator,
    BLOCK_SIZE, BLOCK_DIM,
)
from harmonic_image_generator import save_as_png
from quality_benchmark import compute_q_hf


# ==============================================================================
# BANQUE DE RÉSIDUS HF
# ==============================================================================

class HFResidueBank:
    """
    Banque de résidus SVD extraits du corpus.

    Chaque entrée :
      - residue : np.ndarray (H, W) — le vrai résidu SVD de l'image
      - embedding : np.ndarray (384,) — vecteur sémantique
      - source_path : str — chemin de l'image source
      - metrics : dict — métriques du résidu (std, energy, q_hf)
    """

    def __init__(self):
        self.residues: list = []          # Liste de np.ndarray
        self.embeddings: list = []        # Liste de np.ndarray
        self.source_paths: list = []
        self.metrics_list: list = []
        self.faiss_index = None
        self.encoder = None
        self._encoder_loaded = False

    def _load_encoder(self):
        if self._encoder_loaded:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            pass
        self._encoder_loaded = True

    def encode_text(self, text: str) -> np.ndarray:
        if self.encoder is not None:
            vec = self.encoder.encode([text], normalize_embeddings=True)[0].astype(np.float32)
            return vec / (np.linalg.norm(vec) + 1e-12)
        else:
            seed = SeedManager.text_to_seed(text)
            rng = np.random.RandomState(seed)
            vec = np.zeros(384, dtype=np.float32)
            for i in range(384):
                h = H_CONSTANTS[i % 7]
                vec[i] = np.sin(seed * (i+1) * h / PHI) * np.cos(seed * (i+1) * PI / E)
            return vec / (np.linalg.norm(vec) + 1e-12)

    def extract_residue(self, image: np.ndarray, K: int = 16) -> Tuple[np.ndarray, dict]:
        """
        Extrait le résidu SVD d'une image.

        Returns:
            (residue, metrics_dict)
        """
        sig = HolographicTrainer.train_image(image, K=K)
        h, w = image.shape
        recon = HolographicGenerator.reconstruct(sig, width=w, height=h)

        if recon.shape != image.shape:
            recon = np.array(Image.fromarray(
                (recon*255).astype(np.uint8)
            ).resize((w, h), Image.LANCZOS), dtype=np.float64) / 255.0

        residue = image - recon

        metrics = {
            'std': float(np.std(residue)),
            'max_abs': float(np.max(np.abs(residue))),
            'energy_ratio': float(np.sum(residue**2) / (np.sum(image**2) + 1e-12)),
            'q_hf': compute_q_hf(image)['q_hf'],
        }

        return residue, metrics

    def build_from_dataset(self, dataset_dir: str, max_images: int = 500,
                            residue_size: int = 256):
        """
        Construit la banque de résidus à partir du corpus.

        Pour chaque image :
          1. Redimensionner à residue_size
          2. SVD K=16 → reconstruction
          3. Résidu = original - reconstruction
          4. Embedding sémantique basé sur le chemin
          5. Stocker
        """
        self._load_encoder()

        all_files = sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpg'), recursive=True))
        all_files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpeg'), recursive=True))
        all_files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.png'), recursive=True))

        n = min(len(all_files), max_images)
        print(f"Construction banque de résidus HF : {n} images...")
        t0 = time.time()

        for i, fpath in enumerate(all_files[:n]):
            try:
                img = np.array(Image.open(fpath).convert('L'), dtype=np.float64) / 255.0
                h, w = img.shape

                # Redimensionner à taille standard
                if h != residue_size or w != residue_size:
                    scale = residue_size / max(h, w)
                    nh, nw = int(h*scale), int(w*scale)
                    img = np.array(Image.fromarray((img*255).astype(np.uint8)).resize(
                        (nw, nh), Image.LANCZOS), dtype=np.float64) / 255.0
                    # Pad to square
                    if nh != residue_size or nw != residue_size:
                        padded = np.zeros((residue_size, residue_size), dtype=np.float64)
                        y0, x0 = (residue_size-nh)//2, (residue_size-nw)//2
                        padded[y0:y0+nh, x0:x0+nw] = img
                        img = padded

                # Extraire le résidu
                residue, metrics = self.extract_residue(img, K=16)

                # Embedding sémantique
                rel_path = os.path.relpath(fpath, dataset_dir)
                text_desc = rel_path.replace('\\', '/').replace('_', ' ').replace('.jpg', '').replace('.png', '')
                emb = self.encode_text(text_desc)

                self.residues.append(residue.astype(np.float32))
                self.embeddings.append(emb.astype(np.float32))
                self.source_paths.append(fpath)
                self.metrics_list.append(metrics)

                if (i+1) % 50 == 0:
                    print(f"  {i+1}/{n}...")
            except Exception as e:
                continue

        self._build_faiss()
        print(f"  Banque prête : {len(self.residues)} résidus en {time.time()-t0:.1f}s")

    def _build_faiss(self):
        if len(self.embeddings) < 2:
            return
        try:
            import faiss
            embs = np.array(self.embeddings, dtype=np.float32)
            faiss.normalize_L2(embs)
            self.faiss_index = faiss.IndexFlatIP(embs.shape[1])
            self.faiss_index.add(embs)
        except ImportError:
            self.faiss_index = None

    def search(self, query_embedding: np.ndarray, k: int = 7) -> List[Tuple[int, float]]:
        """Recherche les K résidus les plus proches sémantiquement."""
        if self.faiss_index is not None:
            import faiss
            q = query_embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(q)
            scores, indices = self.faiss_index.search(q, min(k, len(self.residues)))
            return [(int(indices[0][i]), float(scores[0][i])) for i in range(len(indices[0]))]
        else:
            embs = np.array(self.embeddings)
            scores = np.dot(embs, query_embedding.flatten())
            top = np.argsort(scores)[::-1][:k]
            return [(int(i), float(scores[i])) for i in top]

    def get_residue(self, idx: int) -> np.ndarray:
        return np.array(self.residues[idx], dtype=np.float64)

    def __len__(self):
        return len(self.residues)


# ==============================================================================
# MOTEUR DE TRANSFERT DE RÉSIDU HF
# ==============================================================================

class HFResidueTransfer:
    """
    Transfère le résidu HF du corpus vers une image générée.

    Pipeline :
      1. Image de base → embedding sémantique
      2. Recherche des K résidus les plus proches
      3. Fusion Hₙ-pondérée des résidus
      4. Conditionnement spatial (edge-aware, variance-aware)
      5. Injection : enhanced = base + résidu × gain × strength
    """

    def __init__(self, bank: HFResidueBank = None):
        self.bank = bank

    def transfer(self, base_image: np.ndarray, prompt: str = "",
                 n_sources: int = 7, strength: float = 1.0,
                 detail_seed: int = None) -> np.ndarray:
        """
        Transfère le résidu HF du corpus vers l'image de base.

        Args:
            base_image: Image générée [0, 1] (H, W)
            prompt: Texte pour l'interférence sémantique
            n_sources: Nombre de résidus à fusionner
            strength: Force du transfert (1.0 = standard)
            detail_seed: Seed pour la reproductibilité

        Returns:
            Image enrichie [0, 1]
        """
        H, W = base_image.shape

        if self.bank is None or len(self.bank) == 0:
            # Fallback : synthèse procédurale
            from harmonic_detail_synthesizer import enhance_existing_pipeline
            return enhance_existing_pipeline(base_image, strength=strength, detail_seed=detail_seed)

        # 1. Embedding de la base
        if prompt:
            query_emb = self.bank.encode_text(prompt)
        else:
            # Fallback : embedding basé sur l'image elle-même
            query_emb = self.bank.encode_text("natural image texture details")
            rng = np.random.RandomState(detail_seed or 42)
            query_emb += rng.randn(len(query_emb)) * 0.01
            query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-12)

        # 2. Recherche des K résidus les plus proches
        matches = self.bank.search(query_emb, k=n_sources * 2)

        if not matches:
            from harmonic_detail_synthesizer import enhance_existing_pipeline
            return enhance_existing_pipeline(base_image, strength=strength, detail_seed=detail_seed)

        top_matches = matches[:min(n_sources, len(matches))]
        n_selected = len(top_matches)

        # 3. Fusion Hₙ-pondérée des résidus
        fused_residue = np.zeros((H, W), dtype=np.float64)
        total_weight = 0.0

        for i, (idx, score) in enumerate(top_matches):
            residue = self.bank.get_residue(idx)

            # Redimensionner le résidu à la taille de l'image de base
            if residue.shape[0] != H or residue.shape[1] != W:
                residue = np.array(Image.fromarray(
                    ((residue - residue.min()) / (residue.max() - residue.min() + 1e-12) * 255).astype(np.uint8)
                ).resize((W, H), Image.LANCZOS), dtype=np.float64) / 255.0
                # Recentrer (le résidu doit avoir moyenne ~0)
                residue = residue - np.mean(residue)

            # Poids = Hₙ × score d'interférence
            h_weight = H_CONSTANTS[min(i, 6)] / PHI
            weight = h_weight * max(0.01, score)

            fused_residue += residue * weight
            total_weight += weight

        fused_residue /= max(1e-12, total_weight)

        # 4. Conditionnement spatial du gain
        # Edge map
        gy, gx = np.gradient(base_image)
        edge_map = np.sqrt(gx**2 + gy**2)
        edge_map = edge_map / (np.max(edge_map) + 1e-12)

        # Variance locale
        var_map = np.zeros_like(base_image)
        bs = 16
        for y in range(0, H, bs):
            for x in range(0, W, bs):
                ye, xe = min(y+bs, H), min(x+bs, W)
                var_map[y:ye, x:xe] = np.var(base_image[y:ye, x:xe])
        var_map = var_map / (np.max(var_map) + 1e-12)

        # Carte de gain spatial
        spatial_gain = np.ones_like(base_image)
        # Bords : gain √5 dans zones de fort gradient
        spatial_gain += edge_map * (SQRT5 - 1) * 2.0 * strength
        # Textures : gain e dans zones de variance moyenne
        spatial_gain += var_map * (E - 1) * 1.0 * strength
        # Anti-ringing
        damping = 1.0 - edge_map * 0.6 * strength
        damping = np.clip(damping, 0.25, 1.0)
        spatial_gain *= damping
        spatial_gain = np.clip(spatial_gain, 0.3, 5.0)

        # 5. Ajuster l'amplitude
        base_std = np.std(base_image)
        residue_std = np.std(fused_residue)
        if residue_std > 1e-12:
            target_std = base_std * 0.15 * strength  # 15% de l'amplitude image
            fused_residue = fused_residue * (target_std / residue_std)

        # Injection
        enhanced = base_image + fused_residue * spatial_gain * 0.6

        # Clipping sigmoïde
        enhanced = np.clip(enhanced, -0.05, 1.05)
        enhanced = 1.0 / (1.0 + np.exp(-(enhanced - 0.5) * 12))

        return enhanced


# ==============================================================================
# BENCHMARK HF TRANSFERT vs MÉTHODES PRÉCÉDENTES
# ==============================================================================

def benchmark_hf_transfer():
    print("=" * 80)
    print("  BENCHMARK — Transfert de Résidu HF depuis le Corpus")
    print("=" * 80)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'hf_transfer')
    os.makedirs(out_dir, exist_ok=True)

    # Chercher dataset
    dataset_dirs = [
        os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'unified', 'dataset'),
        os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'massive_dataset'),
    ]
    dataset_dir = None
    for d in dataset_dirs:
        if os.path.isdir(d):
            dataset_dir = d
            break

    # Construire la banque de résidus
    print("\n[Étape 1] Construction de la banque de résidus HF...")
    bank = HFResidueBank()
    if dataset_dir:
        bank.build_from_dataset(dataset_dir, max_images=200, residue_size=256)
    else:
        print("  Aucun dataset. Test impossible.")
        return

    transfer_engine = HFResidueTransfer(bank=bank)

    # Importer les autres méthodes pour comparaison
    from harmonic_detail_synthesizer import enhance_existing_pipeline
    from quality_benchmark import enhance_with_hf_boost

    # Test sur plusieurs configurations
    configs = [
        (256, 256, 42, 'cosmique', "cosmic texture"),
        (256, 256, 12345, 'solaire', "sunlight pattern"),
        (512, 512, 7777, 'forest', "forest vegetation"),
        (512, 512, 99999, 'aurore', "aurora borealis"),
        (256, 256, 11111, 'galactique', "galaxy stars"),
    ]

    results = {'base': [], 'old_detail': [], 'hf_boost': [], 'hf_transfer': []}

    print(f"\n[Étape 2] Comparaison des méthodes sur {len(configs)} images...")

    for width, height, seed, style, prompt in configs:
        field = HarmonicField(width=width, height=height, seed=seed)
        psi = field.get_psi_total()
        base_img = (psi + 1) / 2

        # Base
        q_base = compute_q_hf(base_img)
        results['base'].append(q_base['q_hf'])

        # Old detail
        old_d = enhance_existing_pipeline(base_img, strength=1.0, detail_seed=seed+1000)
        q_old = compute_q_hf(old_d)
        results['old_detail'].append(q_old['q_hf'])

        # HF boost
        new_d = enhance_with_hf_boost(base_img, strength=1.0, detail_seed=seed+1000)
        q_new = compute_q_hf(new_d)
        results['hf_boost'].append(q_new['q_hf'])

        # HF TRANSFER (nouveau)
        transferred = transfer_engine.transfer(
            base_img, prompt=prompt, n_sources=7, strength=1.0, detail_seed=seed+1000
        )
        q_trans = compute_q_hf(transferred)
        results['hf_transfer'].append(q_trans['q_hf'])

        # Sauver
        base_rgb = HarmonicColorMapper.harmonic_hsl(psi, palette=style)
        save_as_png(base_rgb, os.path.join(out_dir, f'base_{seed}_{style}.png'))

        trans_field = transferred * 2 - 1
        trans_rgb = HarmonicColorMapper.harmonic_hsl(trans_field, palette=style)
        save_as_png(trans_rgb, os.path.join(out_dir, f'transfer_{seed}_{style}.png'))

    # Rapport
    print(f"\n{'='*80}")
    print("  RÉSULTATS — Q_HF par méthode")
    print(f"{'='*80}")

    corpus_stats = compute_q_hf((bank.get_residue(0) - bank.get_residue(0).min()) / (bank.get_residue(0).max() - bank.get_residue(0).min() + 1e-12))
    q_ref = bank.metrics_list[0]['q_hf'] if bank.metrics_list else 0.12

    print(f"  Q_HF référence corpus : {q_ref:.4f}")
    print()

    for label, vals in [('Base (Ψ seul)', results['base']),
                          ('Ancien Detail Synth', results['old_detail']),
                          ('HF Boost (bruit filtré)', results['hf_boost']),
                          ('HF TRANSFERT (corpus)', results['hf_transfer'])]:
        m = np.mean(vals)
        pct = m / max(1e-12, q_ref) * 100
        bar = '█' * int(pct / 5)
        print(f"  {label:<30s} : Q_HF = {m:.4f} ({pct:.0f}% réf) {bar}")

    gain_transfer_vs_base = np.mean(results['hf_transfer']) / max(1e-12, np.mean(results['base']))
    gain_transfer_vs_old = np.mean(results['hf_transfer']) / max(1e-12, np.mean(results['old_detail']))

    print(f"\n  Gain Transfert vs Base      : ×{gain_transfer_vs_base:.1f}")
    print(f"  Gain Transfert vs Old Detail : ×{gain_transfer_vs_old:.1f}")

    # Analyse détaillée
    print(f"\n{'='*80}")
    print("  ANALYSE DÉTAILLÉE — 512×512 forest")
    print(f"{'='*80}")

    field = HarmonicField(width=512, height=512, seed=7777)
    psi = field.get_psi_total()
    base = (psi + 1) / 2
    transferred = transfer_engine.transfer(base, prompt="forest vegetation", n_sources=7, strength=1.0)

    for label, img in [('Base', base), ('HF Transfert', transferred)]:
        q = compute_q_hf(img)
        print(f"\n  {label}:")
        print(f"    Q_HF       = {q['q_hf']:.4f}")
        print(f"    Q_pente    = {q['q_pente']:.4f}  (pente = {q['slope']})")
        print(f"    Q_bords    = {q['q_edges']:.4f}  (e = {q['e_edges']:.6f})")
        print(f"    Q_textures = {q['q_textures']:.4f}  (e = {q['e_textures']:.6f})")
        print(f"    Q_grain    = {q['q_grain']:.4f}  (e = {q['e_grain']:.6f})")
        print(f"    LapStd     = {q['lap_std']:.6f}")

    # Visualiser un résidu transféré
    sample_residue = bank.get_residue(0)
    residue_viz = np.abs(sample_residue) * 15
    residue_viz = np.clip(residue_viz, 0, 1)
    u8 = (residue_viz * 255).astype(np.uint8)
    Image.fromarray(np.stack([u8]*3, axis=-1), 'RGB').save(
        os.path.join(out_dir, 'sample_corpus_residue.png'))

    print(f"\n  Fichiers dans : {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        print(f"    {f}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HF Residue Transfer Engine')
    parser.add_argument('--build-bank', action='store_true', help='Construire la banque de résidus')
    parser.add_argument('--demo', action='store_true', help='Benchmark comparatif complet')
    parser.add_argument('--dataset', type=str, default=None, help='Dossier dataset')
    parser.add_argument('--max-images', type=int, default=200, help='Nombre max images')

    args = parser.parse_args()

    if args.build_bank:
        bank = HFResidueBank()
        dataset_dirs = [
            os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'unified', 'dataset'),
            os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'massive_dataset'),
        ]
        dataset_dir = args.dataset
        if not dataset_dir:
            for d in dataset_dirs:
                if os.path.isdir(d):
                    dataset_dir = d
                    break
        if dataset_dir:
            bank.build_from_dataset(dataset_dir, max_images=args.max_images)
            # Sauvegarder
            out_path = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'hf_residue_bank.npz')
            residues_arr = np.array([r.flatten() for r in bank.residues])
            embs_arr = np.array(bank.embeddings)
            np.savez_compressed(out_path, residues=residues_arr, embeddings=embs_arr)
            print(f"Banque sauvegardée : {out_path}")
        else:
            print("Aucun dataset trouvé.")
    else:
        benchmark_hf_transfer()