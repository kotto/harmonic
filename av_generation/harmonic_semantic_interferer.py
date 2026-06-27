#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HARMONIC SEMANTIC INTERFERER — Interférence Sémantique des Signatures SVD
============================================================================
Assemblage final du mécanisme d'interférence ondulatoire appliqué aux images.

Principe (identique à Poetic Emergence v4, ConsciousHPU, Emoto Resonator) :
  Tout = interférence d'ondes Ψ_A avec Ψ_B

  Poésie    : ⟨Ψ_mot | Ψ_thème⟩ → mots qui résonnent → assemblage → critique
  Raisonnement : ⟨Ψ_question | Ψ_connaissance⟩ → réponse juste (47/47)
  Émotion   : ⟨Ψ(t) | Ψ(t−δt)⟩ → valence + gradient → joie/peur/...
  Image     : ⟨Ψ_prompt | Ψ_image⟩ → signatures SVD qui résonnent → fusion Hₙ → reconstruction

Pipeline complet :
  1. Encodage sémantique du prompt (sentence-transformers 384-dim)
  2. Interférence cosinus avec TOUTES les signatures SVD du dataset
  3. Sélection des K signatures qui résonnent le plus (⟨Ψ_prompt | Ψ_image⟩ max)
  4. FUSION CRÉATIVE par interférence Hₙ-pondérée des coefficients SVD
     (pas juste une moyenne — c'est Ψ_A × Ψ_B comme dans poetic_emergence)
  5. Reconstruction SVD
  6. Post-processing : Synthèse 1/f² + Adaptive Sharpener

Usage :
  python harmonic_semantic_interferer.py --demo
  python harmonic_semantic_interferer.py --prompt "sunset over mountains" --n-sources 7

Architecture inspirée de :
  - poetic_emergence_v4.py (interférence H-Bit + sélection + critique)
  - conscious_hpu.py (auto-interférence temporelle)
  - unified_superior_engine.py (pipeline FAISS + SVD)
"""

import numpy as np
import math
import sys
import os
import time
import hashlib
import json
import argparse
import glob
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, HarmonicField, HarmonicColorMapper,
    SeedManager, normalize_field, save_image,
)
from holographic_one_shot import (
    HolographicTrainer, HolographicSignature, HolographicGenerator,
    BLOCK_SIZE, BLOCK_DIM,
)
from harmonic_detail_synthesizer import enhance_existing_pipeline
from prompt_engine import analyze_prompt, RESOLUTIONS


# ==============================================================================
# SIGNATURE SVD ENRICHIE (avec embedding sémantique)
# ==============================================================================

@dataclass
class SemanticSignature:
    """
    Signature SVD + embedding sémantique.

    C'est l'équivalent exact du H-Bit poétique appliqué aux images :
      - hologram + coefficients = Ψ_image (l'onde propre de l'image)
      - embedding = encodage sémantique (pour l'interférence avec le prompt)
    """
    signature: HolographicSignature
    embedding: np.ndarray          # Vecteur sémantique (384-dim)
    source_path: str = ""
    semantic_description: str = ""  # Texte associé (nom de fichier, description)
    interference_score: float = 0.0  # Score d'interférence avec le prompt courant

    @property
    def K(self) -> int:
        return self.signature.K

    @property
    def coefficients(self) -> np.ndarray:
        return self.signature.coefficients

    @property
    def hologram(self) -> np.ndarray:
        return self.signature.hologram


# ==============================================================================
# ENCODEUR SÉMANTIQUE (pour l'interférence prompt↔image)
# ==============================================================================

class SemanticEncoder:
    """
    Encodeur sémantique pour l'interférence prompt↔image.

    Utilise sentence-transformers (384-dim) ou fallback harmonique.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.dimension = 384
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        try:
            from sentence_transformers import SentenceTransformer
            print(f"  Chargement encodeur : {self.model_name}...")
            t0 = time.time()
            self.model = SentenceTransformer(self.model_name)
            self._loaded = True
            print(f"  Modele charge en {time.time()-t0:.1f}s")
        except Exception:
            print(f"  Fallback encodage harmonique (sentence-transformers non disponible)")

    def encode(self, text: str) -> np.ndarray:
        """Encode un texte en vecteur sémantique normalisé."""
        if self._loaded and self.model:
            vec = self.model.encode([text], normalize_embeddings=True)[0].astype(np.float32)
            return vec / (np.linalg.norm(vec) + 1e-12)
        else:
            # Fallback harmonique : H-Bit 384-dim basé sur le seed texte
            seed = SeedManager.text_to_seed(text)
            rng = np.random.RandomState(seed)
            vec = np.zeros(self.dimension, dtype=np.float32)
            # Construire un vecteur avec structure spectrale harmonique
            for i in range(self.dimension):
                h = H_CONSTANTS[i % 7]
                vec[i] = np.sin(seed * (i + 1) * h / PHI) * np.cos(seed * (i + 1) * PI / E)
            return vec / (np.linalg.norm(vec) + 1e-12)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        if self._loaded and self.model:
            return self.model.encode(texts, normalize_embeddings=True,
                                      show_progress_bar=False).astype(np.float32)
        else:
            return np.array([self.encode(t) for t in texts])


# ==============================================================================
# INDEX DE SIGNATURES SVD (base de connaissance ondulatoire)
# ==============================================================================

class SVDIndex:
    """
    Index de signatures SVD + embeddings sémantiques.

    C'est l'équivalent du corpus de 10 000+ vers dans Poetic Emergence v3,
    mais pour les images :
      - Chaque image → 1 signature SVD + 1 embedding
      - L'index permet l'interférence rapide prompt↔image
    """
    def __init__(self, encoder: SemanticEncoder = None):
        self.signatures: List[SemanticSignature] = []
        self.embeddings: Optional[np.ndarray] = None  # Matrice (N, 384)
        self.faiss_index = None
        self.encoder = encoder or SemanticEncoder()
        self.encoder.load()

    def add_image(self, image: np.ndarray, source_path: str = "",
                  description: str = "", K: int = 16) -> SemanticSignature:
        """Extrait la signature SVD + embedding d'une image et l'ajoute à l'index."""
        # Extraire SVD
        sig = HolographicTrainer.train_image(image, K=K)

        # Embedding sémantique (basé sur le nom de fichier/description)
        text_for_embedding = description if description else os.path.basename(source_path)
        text_for_embedding = text_for_embedding.replace('_', ' ').replace('.jpg', '').replace('.png', '').replace('.jpeg', '')
        emb = self.encoder.encode(text_for_embedding)

        ss = SemanticSignature(
            signature=sig,
            embedding=emb,
            source_path=source_path,
            semantic_description=text_for_embedding,
        )
        self.signatures.append(ss)
        return ss

    def build_faiss_index(self):
        """Construit l'index FAISS pour recherche rapide par interférence cosinus."""
        if len(self.signatures) < 2:
            return

        self.embeddings = np.array([s.embedding for s in self.signatures], dtype=np.float32)

        try:
            import faiss
            faiss.normalize_L2(self.embeddings)
            self.faiss_index = faiss.IndexFlatIP(self.encoder.dimension)
            self.faiss_index.add(self.embeddings)
            print(f"  Index FAISS construit : {len(self.signatures)} signatures")
        except ImportError:
            print("  FAISS non disponible — recherche exacte")

    def search(self, query_embedding: np.ndarray, k: int = 7) -> List[Tuple[int, float]]:
        """
        Recherche les K signatures qui résonnent le plus avec le prompt.

        C'est l'équivalent de :
          poetic_emergence.py : interference_score = |⟨Ψ_mot | Ψ_thème⟩|²

        Ici : interference_score = cosine(query_embedding, image_embedding)
        """
        query = query_embedding.reshape(1, -1).astype(np.float32)

        if self.faiss_index is not None:
            import faiss
            faiss.normalize_L2(query)
            scores, indices = self.faiss_index.search(query, min(k, len(self.signatures)))
            return [(int(indices[0][i]), float(scores[0][i])) for i in range(len(indices[0]))]
        else:
            # Recherche exacte (petit index)
            scores = np.dot(self.embeddings, query.flatten())
            top_indices = np.argsort(scores)[::-1][:k]
            return [(int(i), float(scores[i])) for i in top_indices]

    def __len__(self):
        return len(self.signatures)


# ==============================================================================
# MOTEUR D'INTERFÉRENCE SÉMANTIQUE (le cœur de l'assemblage)
# ==============================================================================

class HarmonicSemanticInterferer:
    """
    Moteur d'interférence sémantique pour la génération d'images.

    Mécanisme UNIFIÉ (identique à tous les autres domaines) :
      1. ENCODAGE : prompt → embedding sémantique
      2. INTERFÉRENCE : ⟨Ψ_prompt | Ψ_image⟩ pour toutes les images
      3. SÉLECTION : top-K signatures qui résonnent
      4. FUSION CRÉATIVE : coefficients combinés par interférence Hₙ-pondérée
         (pas une moyenne — c'est Ψ_A × Ψ_B comme dans poetic_emergence)
      5. RECONSTRUCTION : SVD inverse
      6. POST-PROCESSING : synthèse 1/f² + sharpener
    """

    def __init__(self, dataset_dir: str = None):
        self.encoder = SemanticEncoder()
        self.index = SVDIndex(encoder=self.encoder)
        self.dataset_dir = dataset_dir
        self._index_built = False

    def build_index_from_dataset(self, image_dir: str = None, max_images: int = 500):
        """
        Indexe les images du dataset en signatures SVD + embeddings.

        C'est l'équivalent de charger le corpus de 10 000 vers dans Poetic Emergence.
        """
        if image_dir:
            self.dataset_dir = image_dir
        if not self.dataset_dir or not os.path.isdir(self.dataset_dir):
            print(f"  Dataset non trouve : {self.dataset_dir}")
            return

        all_files = sorted(glob.glob(os.path.join(self.dataset_dir, '**', '*.jpg'), recursive=True))
        all_files += sorted(glob.glob(os.path.join(self.dataset_dir, '**', '*.jpeg'), recursive=True))
        all_files += sorted(glob.glob(os.path.join(self.dataset_dir, '**', '*.png'), recursive=True))

        n_files = min(len(all_files), max_images)
        print(f"  Indexation de {n_files} images en signatures SVD + embeddings...")
        t0 = time.time()

        for i, fpath in enumerate(all_files[:n_files]):
            try:
                img = np.array(Image.open(fpath).convert('L'), dtype=np.float64) / 255.0
                # Limiter la taille pour performance
                h, w = img.shape
                if min(h, w) > 256:
                    scale = 256.0 / max(h, w)
                    nh, nw = int(h * scale), int(w * scale)
                    img = np.array(Image.fromarray((img*255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS),
                                   dtype=np.float64) / 255.0

                # Utiliser le chemin relatif comme description sémantique
                rel_path = os.path.relpath(fpath, self.dataset_dir)
                self.index.add_image(img, source_path=fpath, description=rel_path, K=16)

                if (i + 1) % 100 == 0:
                    print(f"    {i+1}/{n_files}...")
            except Exception as e:
                continue

        self.index.build_faiss_index()
        self._index_built = True
        print(f"  Index pret : {len(self.index)} signatures en {time.time()-t0:.1f}s")

    def generate(self, prompt: str, resolution: str = 'sd',
                 n_sources: int = 7, style: str = None,
                 strength_details: float = 1.0,
                 output_path: str = None) -> Dict[str, Any]:
        """
        Génère une image par interférence sémantique.

        Pipeline complet :
          Prompt → Embedding → Interférence avec index → Sélection top-K →
          Fusion Hₙ des coefficients → Reconstruction SVD →
          Synthèse 1/f² → Sharpener → RGB

        Args:
            prompt: Description textuelle de l'image souhaitée
            resolution: 'sd' (512²), 'hd' (1024²), '4k' (2048²)
            n_sources: Nombre de signatures à fusionner (7 par défaut, comme les 7Hₙ)
            style: Palette de couleur ('cosmique', 'solaire', etc.)
            strength_details: Force de la synthèse de détails 1/f²
            output_path: Chemin de sauvegarde optionnel

        Returns:
            dict avec 'image' (PIL), 'rgb', 'metadata'
        """
        analysis = analyze_prompt(prompt)
        if style is None:
            style = analysis.style

        width, height = RESOLUTIONS.get(resolution, RESOLUTIONS['sd'])
        t0 = time.time()

        # ÉTAPE 1 : Encodage sémantique du prompt
        prompt_embedding = self.encoder.encode(prompt)

        # ÉTAPE 2+3 : Interférence + Sélection des signatures qui résonnent
        if self._index_built and len(self.index) > 0:
            matches = self.index.search(prompt_embedding, k=n_sources * 2)
        else:
            matches = []

        # ÉTAPE 4 : FUSION CRÉATIVE des coefficients SVD
        creative_result = self._fuse_coefficients(
            prompt_embedding, matches, n_sources, width, height
        )

        # ÉTAPE 5 : Synthèse de détails 1/f²
        creative_result = enhance_existing_pipeline(
            creative_result, strength=strength_details,
            detail_seed=analysis.seed + 1000
        )

        # ÉTAPE 6 : Conversion RGB
        field = np.clip(creative_result, 0, 1) * 2 - 1
        rgb = HarmonicColorMapper.harmonic_hsl(field, palette=style)
        pil_image = Image.fromarray(rgb, 'RGB')

        gen_time = (time.time() - t0) * 1000
        if output_path:
            pil_image.save(output_path)

        return {
            'image': pil_image,
            'rgb': rgb,
            'metadata': {
                'prompt': prompt,
                'seed': analysis.seed,
                'resolution': f'{width}x{height}',
                'style': style,
                'mode': 'semantic_interference',
                'n_sources': len(matches),
                'generation_time_ms': round(gen_time, 1),
                'keywords': analysis.keywords_matched,
            },
        }

    def _fuse_coefficients(self, prompt_embedding: np.ndarray,
                            matches: List[Tuple[int, float]],
                            n_sources: int, width: int, height: int) -> np.ndarray:
        """
        FUSION CRÉATIVE des coefficients SVD par interférence Hₙ-pondérée.

        MÉCANISME (identique à poetic_emergence_v4) :
          1. Chaque signature a un score d'interférence avec le prompt
          2. On pondère par Hₙ (les constantes harmoniques) et par le score d'interférence
          3. On ajoute un terme CROISÉ (interférence entre les signatures elles-mêmes)
          4. On reconstruit

        Ce n'est PAS une moyenne pondérée. Le terme croisé crée de l'émergence.
        """
        if not matches:
            # Fallback : génération procédurale pure
            field = HarmonicField(width=min(width, 512), height=min(height, 512),
                                   seed=SeedManager.text_to_seed(prompt_embedding.tobytes()[:8].hex()))
            psi = field.get_psi_total()
            return (psi + 1) / 2

        # Limiter aux N meilleures signatures
        top_matches = matches[:min(n_sources, len(matches))]
        n_selected = len(top_matches)

        # 1. Collecter les signatures et leurs scores d'interférence
        selected_sigs: List[SemanticSignature] = []
        interference_scores = []

        for idx, score in top_matches:
            if idx < len(self.index.signatures):
                ss = self.index.signatures[idx]
                ss.interference_score = score
                selected_sigs.append(ss)
                interference_scores.append(score)

        if not selected_sigs:
            field = HarmonicField(width=min(width, 512), height=min(height, 512), seed=42)
            return (field.get_psi_total() + 1) / 2

        # 2. Aligner les dimensions (K minimum commun)
        min_K = min(s.K for s in selected_sigs)
        max_blocks = min(s.coefficients.shape[0] for s in selected_sigs)
        max_blocks = min(max_blocks, 256)  # Limiter pour performance

        # 3. FUSION Hₙ-PONDÉRÉE avec terme d'interférence croisée

        # 3a. Hologramme fusionné (base de projection)
        # L'hologramme de la signature la plus résonnante + contribution des autres
        best_sig = selected_sigs[0]
        fused_hologram = best_sig.hologram[:min_K].copy()

        # Mélanger les hologrammes : les signatures qui résonnent bien avec le prompt
        # contribuent davantage à la base de projection
        total_interference = sum(max(0.01, s) for s in interference_scores)
        for i in range(1, n_selected):
            weight_i = max(0.01, interference_scores[i]) / total_interference
            # L'hologramme est enrichi par les composantes des autres signatures
            contrib = selected_sigs[i].hologram[:min_K] * weight_i * PHI_INV
            fused_hologram += contrib

        # Normaliser l'hologramme fusionné
        for k in range(min_K):
            n = np.linalg.norm(fused_hologram[k])
            if n > 1e-12:
                fused_hologram[k] /= n

        # 3b. Coefficients fusionnés avec INTERFÉRENCE CROISÉE
        fused_coeffs = np.zeros((max_blocks, min_K), dtype=np.float64)

        # Pondération harmonique : chaque signature reçoit un poids basé sur :
        #   - Son score d'interférence avec le prompt (⟨Ψ_prompt | Ψ_image⟩)
        #   - Sa position dans le classement (Hₙ décroissant)
        for i in range(n_selected):
            # Poids = interférence × Hₙ
            h_weight = H_CONSTANTS[min(i, 6)] / PHI
            interference_weight = max(0.01, interference_scores[i])

            coeffs = selected_sigs[i].coefficients[:max_blocks, :min_K]
            weight = h_weight * interference_weight

            fused_coeffs += coeffs * weight

            # TERME CROISÉ : interférence entre les signatures i et i+1
            # (identique à poetic_emergence : le produit croisé crée de NOUVELLES corrélations)
            if i + 1 < n_selected:
                cross_weight = weight * interference_scores[i + 1] * 0.15
                coeffs_next = selected_sigs[i + 1].coefficients[:max_blocks, :min_K]
                # Produit de Hadamard (point-à-point) = interférence pure
                cross_term = coeffs * coeffs_next * cross_weight
                fused_coeffs += cross_term

        # Normaliser par la somme des poids
        total_weight = sum(
            H_CONSTANTS[min(i, 6)] / PHI * max(0.01, interference_scores[i])
            for i in range(n_selected)
        )
        fused_coeffs /= max(1e-12, total_weight)

        # 3c. Statistiques fusionnées (moyenne pondérée)
        fused_mean = sum(
            s.signature.mean * H_CONSTANTS[min(i, 6)] / PHI * max(0.01, interference_scores[i])
            for i, s in enumerate(selected_sigs)
        ) / max(1e-12, total_weight)

        fused_std = sum(
            s.signature.std * H_CONSTANTS[min(i, 6)] / PHI * max(0.01, interference_scores[i])
            for i, s in enumerate(selected_sigs)
        ) / max(1e-12, total_weight)

        # 4. Reconstruction
        fused_sig = HolographicSignature(
            hologram=fused_hologram,
            coefficients=fused_coeffs,
            mean=fused_mean,
            std=fused_std,
            source_shape=(height, width),
            K=min_K,
        )

        result = HolographicGenerator.reconstruct(fused_sig, width=width, height=height)
        return np.clip(result, 0, 1)


# ==============================================================================
# DÉMO
# ==============================================================================

def demo_semantic_interferer():
    """Démonstration du moteur d'interférence sémantique."""
    print("=" * 80)
    print("  HARMONIC SEMANTIC INTERFERER — Interférence SVD + Sémantique")
    print("  Mecanisme unifie : Poesie / Raisonnement / Emotion / Image")
    print("=" * 80)

    out_dir = os.path.join(os.path.dirname(__file__), '..',
                           'av_generation_output', 'semantic_interferer')
    os.makedirs(out_dir, exist_ok=True)

    # Chercher le dataset
    dataset_dirs = [
        os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'unified', 'dataset'),
        os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'massive_dataset'),
    ]

    dataset_dir = None
    for d in dataset_dirs:
        if os.path.isdir(d):
            dataset_dir = d
            break

    engine = HarmonicSemanticInterferer(dataset_dir=dataset_dir)

    if dataset_dir:
        engine.build_index_from_dataset(max_images=300)
    else:
        print("  Aucun dataset trouve. Generation sans index (fallback harmonique).")

    # Tests avec différents prompts
    test_prompts = [
        ("sunset over mountains with lake reflection", "cosmique", 7),
        ("cosmic spiral galaxy nebula deep space", "galactique", 7),
        ("green forest with morning fog", "forest", 7),
        ("golden light ocean waves at sunrise", "solaire", 5),
        ("abstract geometric patterns crystal", "aurore", 5),
    ]

    for prompt, style, n_sources in test_prompts:
        print(f"\n  Prompt: '{prompt}' [{style}]")
        result = engine.generate(
            prompt, resolution='sd', n_sources=n_sources,
            style=style, strength_details=1.0,
        )

        img_id = hashlib.md5(prompt.encode()).hexdigest()[:8]
        out_path = os.path.join(out_dir, f'semantic_{style}_{img_id}.png')
        result['image'].save(out_path)

        m = result['metadata']
        print(f"    Temps: {m['generation_time_ms']:.0f}ms | Sources: {m['n_sources']}")
        print(f"    Sauvegarde: {out_path}")

    print(f"\n{'='*80}")
    print(f"  Fichiers generes dans : {out_dir}/")
    print(f"{'='*80}")

    # Test comparatif : avec vs sans index
    if dataset_dir:
        print(f"\n  [TEST] Comparaison prompt avec/sans index semantique...")
        prompt_test = "mountain landscape with snow peaks"
        result = engine.generate(prompt_test, resolution='sd', n_sources=7, style='cosmique')
        out_path = os.path.join(out_dir, 'comparison_with_index.png')
        result['image'].save(out_path)
        print(f"    Avec index ({len(engine.index)} signatures): {out_path}")

        # Sans index (fallback)
        engine_no_index = HarmonicSemanticInterferer(dataset_dir=None)
        result_no = engine_no_index.generate(prompt_test, resolution='sd', n_sources=7, style='cosmique')
        out_path_no = os.path.join(out_dir, 'comparison_no_index.png')
        result_no['image'].save(out_path_no)
        print(f"    Sans index (procedural pur): {out_path_no}")

    print(f"\n  Assemblage termine.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Harmonic Semantic Interferer')
    parser.add_argument('--demo', action='store_true', help='Demonstration complete')
    parser.add_argument('--prompt', type=str, default=None, help='Prompt de generation')
    parser.add_argument('--dataset', type=str, default=None, help='Dossier dataset')
    parser.add_argument('--n-sources', type=int, default=7, help='Nb signatures a fusionner')
    parser.add_argument('--style', type=str, default=None, help='Palette de couleur')
    parser.add_argument('--output', type=str, default=None, help='Fichier de sortie')

    args = parser.parse_args()

    if args.prompt:
        engine = HarmonicSemanticInterferer(dataset_dir=args.dataset)
        if args.dataset:
            engine.build_index_from_dataset(max_images=500)
        result = engine.generate(
            args.prompt, n_sources=args.n_sources,
            style=args.style, output_path=args.output,
        )
        if not args.output:
            out = f"semantic_{hashlib.md5(args.prompt.encode()).hexdigest()[:8]}.png"
            result['image'].save(out)
            print(f"Image: {out}")
        print(json.dumps(result['metadata'], indent=2))
    else:
        demo_semantic_interferer()