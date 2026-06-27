#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COEFFICIENT SAMPLER — Génération photoréaliste par échantillonnage SVD
=========================================================================
Chaînon manquant final : apprendre P(coeffs) sur des photos réelles
et échantillonner pour générer des images de haute qualité.

Pipeline :
  1. Corpus → SVD → signatures (hologrammes K×64 + coefficients N_blocs×K)
  2. ACP sur les coefficients → espace latent réduit (32-dim)
  3. GMM (Gaussian Mixture Model) sur l'espace latent → 50 composantes
  4. Échantillonnage : tirer une composante GMM → échantillonner → inverse ACP → coeffs
  5. Reconstruction SVD → image brute
  6. Post-processing : HF Transfert + Détails 1/f² + Sharpener → image finale

Usage :
  python coefficient_sampler.py --build-corpus    # Extraire SVD de tout le dataset
  python coefficient_sampler.py --train           # Apprendre ACP + GMM
  python coefficient_sampler.py --generate 10     # Générer 10 images
  python coefficient_sampler.py --demo            # Pipeline complet
"""

import sys, os, numpy as np, math, time, glob, pickle, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image
from scipy.ndimage import laplace as lap_func
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture

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
# EXTRACTION DU CORPUS SVD
# ==============================================================================

class SVDCorpus:
    """
    Corpus de signatures SVD extraites de photos réelles.

    Structure :
      - holograms_R/G/B : (N, K, 64) — bases de projection par canal
      - coefficients : (N, M, K*3) — projections concaténées R+G+B
      - means, stds : statistiques par canal
    """

    def __init__(self):
        self.holograms_R: list = []
        self.holograms_G: list = []
        self.holograms_B: list = []
        self.coefficients: list = []  # (N, 256, K*3) concaténés R+G+B
        self.means_R: list = []; self.means_G: list = []; self.means_B: list = []
        self.stds_R: list = []; self.stds_G: list = []; self.stds_B: list = []
        self.source_paths: list = []
        self.K: int = 16
        self.is_rgb: bool = False

    def build(self, dataset_dir: str, max_images: int = 500,
              K: int = 16, max_size: int = 256, use_rgb: bool = True):
        """Extrait SVD de toutes les images du corpus (RGB si use_rgb=True)."""
        self.K = K
        self.is_rgb = use_rgb

        all_files = sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpg'), recursive=True))
        all_files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpeg'), recursive=True))
        all_files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.png'), recursive=True))

        n = min(len(all_files), max_images)
        mode_str = "RGB (3 canaux)" if use_rgb else "Luminance"
        print(f"Extraction SVD de {n} images (K={K}, {mode_str})...")
        t0 = time.time()

        for i, fpath in enumerate(all_files[:n]):
            try:
                if use_rgb:
                    img = np.array(Image.open(fpath).convert('RGB'), dtype=np.float64) / 255.0
                else:
                    img = np.array(Image.open(fpath).convert('L'), dtype=np.float64) / 255.0
                h, w = img.shape[:2]

                # Redimensionner
                scale = max_size / max(h, w)
                nh, nw = int(h*scale), int(w*scale)
                if nh != h or nw != w:
                    if use_rgb:
                        img = np.array(Image.fromarray((img*255).astype(np.uint8)).resize(
                            (nw, nh), Image.LANCZOS), dtype=np.float64) / 255.0
                    else:
                        img = np.array(Image.fromarray((img*255).astype(np.uint8)).resize(
                            (nw, nh), Image.LANCZOS), dtype=np.float64) / 255.0

                max_blocks = 256

                if use_rgb:
                    # Extraire 3 signatures SVD (R, G, B)
                    sigs = HolographicTrainer.train_image_rgb(img, K=K)
                    # Concaténer les coefficients des 3 canaux
                    coeffs_r = sigs['R'].coefficients[:max_blocks].astype(np.float32)
                    coeffs_g = sigs['G'].coefficients[:max_blocks].astype(np.float32)
                    coeffs_b = sigs['B'].coefficients[:max_blocks].astype(np.float32)
                    # Pad si nécessaire
                    for arr in [coeffs_r, coeffs_g, coeffs_b]:
                        if arr.shape[0] < max_blocks:
                            p = np.zeros((max_blocks, K), dtype=np.float32)
                            p[:arr.shape[0]] = arr
                            arr = p
                    coeffs_concat = np.concatenate([coeffs_r, coeffs_g, coeffs_b], axis=1)  # (256, K*3)
                    self.coefficients.append(coeffs_concat)
                    self.holograms_R.append(sigs['R'].hologram.astype(np.float32))
                    self.holograms_G.append(sigs['G'].hologram.astype(np.float32))
                    self.holograms_B.append(sigs['B'].hologram.astype(np.float32))
                    self.means_R.append(float(sigs['R'].mean))
                    self.means_G.append(float(sigs['G'].mean))
                    self.means_B.append(float(sigs['B'].mean))
                    self.stds_R.append(float(sigs['R'].std))
                    self.stds_G.append(float(sigs['G'].std))
                    self.stds_B.append(float(sigs['B'].std))
                else:
                    sig = HolographicTrainer.train_image(img, K=K)
                    self.holograms_R.append(sig.hologram.astype(np.float32))
                    coeffs = sig.coefficients[:max_blocks].astype(np.float32)
                    if coeffs.shape[0] < max_blocks:
                        padded = np.zeros((max_blocks, K), dtype=np.float32)
                        padded[:coeffs.shape[0]] = coeffs
                        coeffs = padded
                    self.coefficients.append(coeffs)
                    self.means_R.append(float(sig.mean))
                    self.stds_R.append(float(sig.std))

                self.source_paths.append(fpath)
                if (i+1) % 100 == 0:
                    print(f"  {i+1}/{n}...")
            except Exception as e:
                continue

        print(f"  Corpus SVD prêt : {len(self.holograms_R)} signatures en {time.time()-t0:.1f}s")

    def save(self, path: str):
        """Sauvegarde le corpus."""
        data = {
            'holograms_R': np.array(self.holograms_R),
            'coefficients': np.array(self.coefficients),
            'means_R': np.array(self.means_R, dtype=np.float32),
            'stds_R': np.array(self.stds_R, dtype=np.float32),
            'K': self.K,
            'is_rgb': self.is_rgb,
            'source_paths': self.source_paths,
        }
        if self.is_rgb:
            data['holograms_G'] = np.array(self.holograms_G)
            data['holograms_B'] = np.array(self.holograms_B)
            data['means_G'] = np.array(self.means_G, dtype=np.float32)
            data['means_B'] = np.array(self.means_B, dtype=np.float32)
            data['stds_G'] = np.array(self.stds_G, dtype=np.float32)
            data['stds_B'] = np.array(self.stds_B, dtype=np.float32)
        np.savez_compressed(path, **data)
        print(f"Corpus sauvegardé : {path} ({os.path.getsize(path)//1024} Ko)")

    def load(self, path: str):
        """Charge le corpus."""
        data = np.load(path, allow_pickle=True)
        self.holograms_R = list(data['holograms_R'])
        self.coefficients = list(data['coefficients'])
        self.means_R = list(data['means_R'])
        self.stds_R = list(data['stds_R'])
        self.K = int(data['K'])
        self.is_rgb = bool(data.get('is_rgb', False))
        self.source_paths = list(data['source_paths'])
        if self.is_rgb:
            self.holograms_G = list(data['holograms_G'])
            self.holograms_B = list(data['holograms_B'])
            self.means_G = list(data['means_G'])
            self.means_B = list(data['means_B'])
            self.stds_G = list(data['stds_G'])
            self.stds_B = list(data['stds_B'])
        print(f"Corpus chargé : {len(self.holograms_R)} signatures (RGB={self.is_rgb})")

    def __len__(self):
        return len(self.holograms_R)


# ==============================================================================
# ÉCHANTILLONNEUR DE COEFFICIENTS
# ==============================================================================

class CoefficientSampler:
    """
    Apprend P(coeffs) et échantillonne de nouveaux coefficients.

    Modèle : ACP (réduction de dimension) + GMM (modèle de densité).

    Pour chaque signature :
      coeffs (256, 16) → flatten → (4096,) → ACP → latent (32,) → GMM
    """

    def __init__(self, corpus: SVDCorpus = None):
        self.corpus = corpus
        self.pca: PCA = None
        self.gmm: GaussianMixture = None
        self.latent_dim: int = 32
        self.n_components: int = 50
        self.X_latent: np.ndarray = None  # Projections ACP du corpus pour matching hologramme</parameter>

    def train(self, latent_dim: int = 32, n_components: int = 50):
        """Apprend ACP + GMM sur le corpus."""
        if self.corpus is None or len(self.corpus) == 0:
            raise ValueError("Corpus vide. Lancer build() d'abord.")

        self.latent_dim = latent_dim
        self.n_components = n_components

        # Flatten les coefficients : (N, 256*K)
        N = len(self.corpus.coefficients)
        K = self.corpus.K
        X = np.array(self.corpus.coefficients).reshape(N, -1)  # (N, 256*K)

        print(f"Apprentissage ACP ({X.shape[1]} → {latent_dim})...")
        t0 = time.time()

        # ACP
        self.pca = PCA(n_components=latent_dim, svd_solver='randomized', random_state=42)
        self.X_latent = self.pca.fit_transform(X).astype(np.float64)  # Conserver pour matching
        explained = self.pca.explained_variance_ratio_.sum()
        print(f"  ACP : {explained*100:.1f}% variance expliquée en {latent_dim} dim")

        # GMM — composantes réduites pour stabilité numérique
        actual_components = min(n_components, N // 10, 15)
        print(f"Apprentissage GMM ({actual_components} composantes)...")
        self.n_components = actual_components
        self.gmm = GaussianMixture(
            n_components=actual_components,
            covariance_type='diag',
            reg_covar=1e-3,
            max_iter=200,
            n_init=3,
            random_state=42,
            verbose=1,
        )
        self.gmm.fit(self.X_latent)
        print(f"  GMM entraîné en {time.time()-t0:.1f}s")
        print(f"  BIC: {self.gmm.bic(self.X_latent):.1f}")

    def sample(self, n_samples: int = 1, random_state: int = None) -> list:
        """
        Échantillonne N nouveaux jeux de coefficients.

        Returns:
            Liste de (coefficients_256xK, mean, std, hologram_idx)
        """
        if self.gmm is None or self.pca is None:
            raise ValueError("Modèle non entraîné. Lancer train() d'abord.")

        if random_state is not None:
            np.random.seed(random_state)

        # Échantillonner depuis la GMM
        latent_samples, component_indices = self.gmm.sample(n_samples)

        # Inverse ACP : latent → coefficients flatten
        coeffs_flat = self.pca.inverse_transform(latent_samples)  # (n_samples, D)

        K = self.corpus.K
        results = []
        for i in range(n_samples):
            latent_sample = latent_samples[i].reshape(1, -1)
            distances = np.linalg.norm(self.X_latent - latent_sample, axis=1)
            nearest_idx = int(np.argmin(distances))
            
            sample_data = {
                'holo_idx': nearest_idx,
                'gmm_component': int(component_indices[i]) if hasattr(component_indices, '__getitem__') else 0,
            }
            
            if self.corpus.is_rgb:
                # RGB : 256 × (K*3) = 12288 dimensions
                coeffs_3ch = coeffs_flat[i].reshape(256, K * 3)
                sample_data['coefficients_R'] = coeffs_3ch[:, :K].astype(np.float64)
                sample_data['coefficients_G'] = coeffs_3ch[:, K:2*K].astype(np.float64)
                sample_data['coefficients_B'] = coeffs_3ch[:, 2*K:].astype(np.float64)
                sample_data['hologram_R'] = np.array(self.corpus.holograms_R[nearest_idx], dtype=np.float64)
                sample_data['hologram_G'] = np.array(self.corpus.holograms_G[nearest_idx], dtype=np.float64)
                sample_data['hologram_B'] = np.array(self.corpus.holograms_B[nearest_idx], dtype=np.float64)
                sample_data['mean_R'] = float(self.corpus.means_R[nearest_idx])
                sample_data['mean_G'] = float(self.corpus.means_G[nearest_idx])
                sample_data['mean_B'] = float(self.corpus.means_B[nearest_idx])
                sample_data['std_R'] = float(self.corpus.stds_R[nearest_idx])
                sample_data['std_G'] = float(self.corpus.stds_G[nearest_idx])
                sample_data['std_B'] = float(self.corpus.stds_B[nearest_idx])
            else:
                # Niveaux de gris : 256 × K = 4096 dimensions
                coeffs_1ch = coeffs_flat[i].reshape(256, K)
                sample_data['coefficients'] = coeffs_1ch.astype(np.float64)
                sample_data['hologram'] = np.array(self.corpus.holograms_R[nearest_idx], dtype=np.float64)
                sample_data['mean'] = float(self.corpus.means_R[nearest_idx])
                sample_data['std'] = float(self.corpus.stds_R[nearest_idx])
            
            results.append(sample_data)

        return results

    def save(self, path: str):
        """Sauvegarde le modèle entraîné."""
        import pickle
        with open(path, 'wb') as f:
            pickle.dump({
                'pca': self.pca,
                'gmm': self.gmm,
                'latent_dim': self.latent_dim,
                'n_components': self.n_components,
                'X_latent': self.X_latent,
            }, f)
        print(f"Modèle sauvegardé : {path}")

    def load(self, path: str):
        """Charge le modèle entraîné."""
        import pickle
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.pca = data['pca']
        self.gmm = data['gmm']
        self.latent_dim = data['latent_dim']
        self.n_components = data['n_components']
        self.X_latent = data.get('X_latent', None)
        print(f"Modèle chargé : PCA {self.pca.n_components_}d, GMM {self.gmm.n_components} composantes")


# ==============================================================================
# PIPELINE DE GÉNÉRATION COMPLET
# ==============================================================================

class PhotorealisticGenerator:
    """
    Générateur photoréaliste complet.

    Pipeline :
      GMM → coefficients → reconstruction SVD → HF Transfert → Détails 1/f² → Sharpener → RGB
    """

    def __init__(self, sampler: CoefficientSampler = None,
                 hf_transfer=None, detail_strength: float = 1.0):
        self.sampler = sampler
        self.hf_transfer = hf_transfer
        self.detail_strength = detail_strength

    def generate(self, width: int = 512, height: int = 512,
                 style: str = 'cosmique', seed: int = None) -> dict:
        """
        Génère une image photoréaliste (RGB ou niveaux de gris).

        Returns:
            dict avec 'image' (PIL), 'rgb', 'grayscale', 'metadata'
        """
        if seed is not None:
            np.random.seed(seed)

        samples = self.sampler.sample(n_samples=1, random_state=seed)
        sample = samples[0]

        if self.sampler.corpus.is_rgb:
            # Reconstruction RGB : 3 canaux indépendants
            channels = []
            for ch in ['R', 'G', 'B']:
                sig = HolographicSignature(
                    hologram=sample[f'hologram_{ch}'],
                    coefficients=sample[f'coefficients_{ch}'],
                    mean=sample[f'mean_{ch}'],
                    std=sample[f'std_{ch}'],
                    source_shape=(height, width),
                    K=sample[f'hologram_{ch}'].shape[0],
                )
                ch_img = HolographicGenerator.reconstruct(sig, width=width, height=height)
                channels.append(np.clip(ch_img, 0, 1))
            
            rgb_native = np.stack(channels, axis=-1)  # (H, W, 3)
            pil_image = Image.fromarray((rgb_native * 255).astype(np.uint8), 'RGB')
            
            # Grayscale pour métriques
            grayscale = 0.299 * channels[0] + 0.587 * channels[1] + 0.114 * channels[2]
            
            from harmonic_detail_synthesizer import enhance_existing_pipeline
            enhanced = enhance_existing_pipeline(grayscale, strength=self.detail_strength,
                                                  detail_seed=(seed or 42) + 1000)
        else:
            # Niveaux de gris
            sig = HolographicSignature(
                hologram=sample['hologram'],
                coefficients=sample['coefficients'],
                mean=sample['mean'],
                std=sample['std'],
                source_shape=(height, width),
                K=sample['hologram'].shape[0],
            )
            base_image = HolographicGenerator.reconstruct(sig, width=width, height=height)
            base_image = np.clip(base_image, 0, 1)

            from harmonic_detail_synthesizer import enhance_existing_pipeline
            enhanced = enhance_existing_pipeline(base_image, strength=self.detail_strength,
                                                  detail_seed=(seed or 42) + 1000)

            field = enhanced * 2 - 1
            rgb = HarmonicColorMapper.harmonic_hsl(field, palette=style)
            pil_image = Image.fromarray(rgb, 'RGB')
            grayscale = enhanced
            rgb_native = rgb

        return {
            'image': pil_image,
            'rgb': rgb_native if 'rgb_native' in dir() else rgb,
            'grayscale': grayscale,
            'metadata': {
                'mode': 'gmm_sampling_rgb' if self.sampler.corpus.is_rgb else 'gmm_sampling',
                'width': width,
                'height': height,
                'style': style,
                'seed': seed,
            },
        }


# ==============================================================================
# DÉMO COMPLÈTE
# ==============================================================================

def demo_pipeline():
    """Démonstration du pipeline complet."""
    print("=" * 80)
    print("  COEFFICIENT SAMPLER — Génération Photoréaliste")
    print("=" * 80)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'photorealistic')
    os.makedirs(out_dir, exist_ok=True)

    # Dataset
    dataset_dirs = [
        os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'unified', 'dataset'),
        os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'massive_dataset'),
    ]
    dataset_dir = None
    for d in dataset_dirs:
        if os.path.isdir(d):
            dataset_dir = d
            break

    if not dataset_dir:
        print("Aucun dataset. Impossible de continuer.")
        return

    # Phase 1 : Corpus SVD
    corpus_path = os.path.join(out_dir, 'svd_corpus.npz')
    if os.path.exists(corpus_path):
        print("\n[Phase 1] Chargement du corpus existant...")
        corpus = SVDCorpus()
        corpus.load(corpus_path)
    else:
        print("\n[Phase 1] Extraction du corpus SVD...")
        corpus = SVDCorpus()
        corpus.build(dataset_dir, max_images=300, K=16, max_size=256)
        corpus.save(corpus_path)

    # Phase 2 : Entraînement ACP + GMM
    model_path = os.path.join(out_dir, 'coefficient_model.pkl')
    sampler = CoefficientSampler(corpus=corpus)
    if os.path.exists(model_path):
        print("\n[Phase 2] Chargement du modèle existant...")
        sampler.load(model_path)
    else:
        print("\n[Phase 2] Apprentissage ACP + GMM...")
        sampler.train(latent_dim=32, n_components=50)
        sampler.save(model_path)

    # Phase 3 : Génération
    print("\n[Phase 3] Génération d'images photoréalistes...")
    generator = PhotorealisticGenerator(sampler=sampler, detail_strength=1.0)

    styles = ['cosmique', 'solaire', 'forest', 'ocean', 'aurore']
    results_q_hf = []

    for i in range(10):
        style = styles[i % len(styles)]
        seed = 42 + i * 137

        result = generator.generate(width=512, height=512, style=style, seed=seed)

        # Sauvegarder
        img_path = os.path.join(out_dir, f'generated_{i+1:02d}_{style}.png')
        result['image'].save(img_path)

        # Métriques
        q = compute_q_hf(result['grayscale'])
        results_q_hf.append(q['q_hf'])

        print(f"  [{i+1:02d}] {style:<10s} | Q_HF={q['q_hf']:.4f} | "
              f"LapStd={q['lap_std']:.4f} | → {img_path}")

    # Rapport
    print(f"\n{'='*80}")
    print("  RAPPORT — Qualité des images générées")
    print(f"{'='*80}")
    print(f"  Q_HF moyen     : {np.mean(results_q_hf):.4f}")
    print(f"  Q_HF médian    : {np.median(results_q_hf):.4f}")
    print(f"  Q_HF min/max   : {np.min(results_q_hf):.4f} / {np.max(results_q_hf):.4f}")
    print(f"\n  Fichiers dans : {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        print(f"    {f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Coefficient Sampler — Génération Photoréaliste')
    parser.add_argument('--build-corpus', action='store_true', help='Extraire SVD du dataset')
    parser.add_argument('--train', action='store_true', help='Apprendre ACP + GMM')
    parser.add_argument('--generate', type=int, default=0, help='Générer N images')
    parser.add_argument('--demo', action='store_true', help='Pipeline complet')
    parser.add_argument('--dataset', type=str, default=None, help='Dossier dataset')
    parser.add_argument('--max-images', type=int, default=300, help='Nb max images corpus')
    parser.add_argument('--style', type=str, default='cosmique', help='Palette de couleur')

    args = parser.parse_args()

    # Résoudre le dataset
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

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'photorealistic')
    os.makedirs(out_dir, exist_ok=True)
    corpus_path = os.path.join(out_dir, 'svd_corpus.npz')
    model_path = os.path.join(out_dir, 'coefficient_model.pkl')

    if args.build_corpus:
        if not dataset_dir:
            print("Aucun dataset trouvé.")
            sys.exit(1)
        corpus = SVDCorpus()
        corpus.build(dataset_dir, max_images=args.max_images, K=16, max_size=256)
        corpus.save(corpus_path)

    elif args.train:
        corpus = SVDCorpus()
        if os.path.exists(corpus_path):
            corpus.load(corpus_path)
        elif dataset_dir:
            corpus.build(dataset_dir, max_images=args.max_images, K=16, max_size=256)
            corpus.save(corpus_path)
        else:
            print("Corpus non trouvé. Lancer --build-corpus d'abord.")
            sys.exit(1)

        sampler = CoefficientSampler(corpus=corpus)
        sampler.train(latent_dim=32, n_components=50)
        sampler.save(model_path)

    elif args.generate > 0:
        corpus = SVDCorpus()
        corpus.load(corpus_path)
        sampler = CoefficientSampler(corpus=corpus)
        sampler.load(model_path)
        generator = PhotorealisticGenerator(sampler=sampler, detail_strength=1.0)

        for i in range(args.generate):
            result = generator.generate(width=512, height=512, style=args.style, seed=42+i*137)
            img_path = os.path.join(out_dir, f'generated_{i+1:02d}.png')
            result['image'].save(img_path)
            q = compute_q_hf(result['grayscale'])
            print(f"[{i+1:02d}] Q_HF={q['q_hf']:.4f} LapStd={q['lap_std']:.4f} → {img_path}")

    else:
        demo_pipeline()