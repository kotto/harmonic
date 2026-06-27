#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HARMONIC PHOTO RETRIEVAL v2 — Compression SVD RGB + Stockage + Retrieval + Upscaling
=====================================================================================
Pipeline complet — CORRIGÉ pour RGB natif (train_image_rgb) :

  1. Télécharger/charger des photos HD
  2. Compresser via SVD RGB (3 signatures R, G, B indépendantes — hcv_svd_codec)
  3. Assigner signature harmonique (embedding sémantique)
  4. Stocker dans l'index FAISS
  5. Prompt → Embedding → FAISS → Image la plus proche
  6. Décompression SVD → Image RGB native
  7. Upscaling 4K (SVD 2× → Lanczos → Hₙ sharpen)
  8. generate_variation() — interférence Hₙ sur les 3 canaux

Corrections vs v1 :
  - .convert('L') → .convert('RGB') (couleurs restaurées)
  - train_image_rgb() branché dans compress_photo()
  - decode_photo() reconstruit RGB à partir des 3 signatures
  - UpscalePipeline adapté pour 3 canaux
  - CLI --generate pour tester la génération par prompt

Usage :
  python harmonic_photo_retrieval.py --build-index     # Compresser tout le dataset
  python harmonic_photo_retrieval.py --prompt "sunset"  # Retrieval + affichage
  python harmonic_photo_retrieval.py --generate "sunset over mountains"  # Génération
  python harmonic_photo_retrieval.py --demo             # Pipeline complet
"""

import sys, os, numpy as np, math, time, glob, json, argparse, io, hashlib
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, H_CONSTANTS,
    HarmonicColorMapper, SeedManager,
)
from holographic_one_shot import (
    HolographicTrainer, HolographicSignature, HolographicGenerator,
    BLOCK_SIZE, BLOCK_DIM,
)
from optimized_svd_codec import OptimizedSVDCodec, create_harmonic_q_table, quantize_coeffs, dequantize_coeffs
from prompt_engine import analyze_prompt, RESOLUTIONS


# ==============================================================================
# ENCODEUR SÉMANTIQUE
# ==============================================================================

class SemanticEncoder:
    """Encodeur sémantique — sentence-transformers ou fallback harmonique."""
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = None
        self.dimension = 384
        self._loaded = False
        self.model_name = model_name

    def load(self):
        if self._loaded: return
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self._loaded = True
            print(f"  Encodeur chargé : {self.model_name}")
        except Exception:
            print("  Fallback encodage harmonique")

    def encode(self, text: str) -> np.ndarray:
        if self._loaded and self.model:
            vec = self.model.encode([text], normalize_embeddings=True)[0].astype(np.float32)
            return vec / (np.linalg.norm(vec) + 1e-12)
        else:
            seed = SeedManager.text_to_seed(text)
            rng = np.random.RandomState(seed)
            vec = np.zeros(self.dimension, dtype=np.float32)
            for i in range(self.dimension):
                h = H_CONSTANTS[i % 7]
                vec[i] = np.sin(seed * (i+1) * h / PHI) * np.cos(seed * (i+1) * PI / E)
            return vec / (np.linalg.norm(vec) + 1e-12)


# ==============================================================================
# ENCODEUR CLIP — Embedding visuel sémantique (alternative à l'embedding SVD seul)
# ==============================================================================

class CLIPEncoder:
    """Encodeur CLIP via sentence-transformers (clip-ViT-B-32) — pas de dépendance open_clip."""
    def __init__(self):
        self.model = None
        self.dimension = 512
        self._loaded = False

    def load(self):
        if self._loaded: return
        try:
            from sentence_transformers import SentenceTransformer
            # Utiliser le modèle CLIP multilingue via sentence-transformers
            self.model = SentenceTransformer('clip-ViT-B-32')
            self.dimension = self.model.get_sentence_embedding_dimension()
            self._loaded = True
            print(f"  CLIP chargé : clip-ViT-B-32 (dim={self.dimension})")
        except Exception as e:
            print(f"  CLIP non disponible : {e}")

    def encode_image(self, image: np.ndarray) -> np.ndarray:
        """Encode une image RGB uint8 → embedding normalisé."""
        if not self._loaded or self.model is None:
            return np.zeros(self.dimension, dtype=np.float32)
        try:
            from PIL import Image as PILImage
            pil_img = PILImage.fromarray(image.astype(np.uint8))
            vec = self.model.encode(pil_img, normalize_embeddings=True)
            return vec.astype(np.float32)
        except Exception:
            return np.zeros(self.dimension, dtype=np.float32)

    def encode_text(self, text: str) -> np.ndarray:
        """Encode un texte → embedding normalisé."""
        if not self._loaded or self.model is None:
            return np.zeros(self.dimension, dtype=np.float32)
        try:
            vec = self.model.encode([text], normalize_embeddings=True)[0]
            return vec.astype(np.float32)
        except Exception:
            return np.zeros(self.dimension, dtype=np.float32)


# ==============================================================================
# INDEX DE PHOTOS COMPRESSÉES (RGB natif — 3 signatures SVD)
# ==============================================================================

class HarmonicPhotoIndex:
    """
    Index de photos compressées en SVD RGB + embeddings sémantiques.

    Chaque entrée :
      - encoded_R, encoded_G, encoded_B : dict (signature + données compressées par canal)
      - compressed_data : bytes (concaténation RGB compressée zstd)
      - encoded_info : dict (mean, std, source_shape, K, etc.)
      - embedding : np.ndarray (384,) — vecteur sémantique
      - source_path : str
      - thumbnail : np.ndarray (petite vignette RGB pour prévisualisation)
    """

    def __init__(self, use_clip: bool = True):
        self.entries: list = []          # Liste de dict
        self.embeddings: list = []       # Liste de np.ndarray
        self.faiss_index = None
        self.encoder = SemanticEncoder()
        self.encoder.load()
        # CLIP pour embeddings sémantiques (image + texte)
        self.clip_encoder = None
        self.use_clip = False
        if use_clip:
            self.clip_encoder = CLIPEncoder()
            self.clip_encoder.load()
            if self.clip_encoder._loaded:
                self.use_clip = True
                # Redéfinir la dimension de l'encodeur pour FAISS
                self.encoder.dimension = self.clip_encoder.dimension  # 512
                print(f"  Mode CLIP activé — retrieval sémantique image/texte (dim={self.clip_encoder.dimension})")
            else:
                print("  CLIP indisponible — fallback embedding SVD 144-dim")
                self.clip_encoder = None

    def compress_photo(self, image: np.ndarray, source_path: str = "",
                       K: int = 16, quality: float = 1.0) -> dict:
        """
        Compresse une photo via SVD RGB optimisé (3 signatures indépendantes).

        Args:
            image: Array (H, W, 3), uint8
            source_path: Chemin source
            K: Nombre de composantes SVD par canal
            quality: Qualité de quantification (1.0 = standard)

        Returns:
            dict avec compressed_data, encoded_info, thumbnail
        """
        if image.ndim != 3 or image.shape[2] < 3:
            raise ValueError("compress_photo nécessite une image RGB (H, W, 3)")

        H, W = image.shape[:2]
        channels = ['R', 'G', 'B']
        encoded_channels = {}
        decoded_channels = {}
        total_bytes = 0

        import zstandard as zstd_module
        cctx = zstd_module.ZstdCompressor(level=19)

        # Extraire les 3 signatures SVD RGB
        rgb_sigs = HolographicTrainer.train_image_rgb(image, K=K)

        for idx, ch in enumerate(channels):
            sig = rgb_sigs[ch]
            N_blocks = sig.coefficients.shape[0]

            # === PIPELINE HCV PRO : DPCM spatial + uint8 + zstd ===
            # 1. DPCM spatial : prédire chaque bloc depuis le bloc précédent
            residuals = np.zeros_like(sig.coefficients, dtype=np.float64)
            residuals[0, :] = sig.coefficients[0, :]
            for bi in range(1, N_blocks):
                residuals[bi, :] = sig.coefficients[bi, :] - sig.coefficients[bi - 1, :]

            # 2. Quantification uint8 (256 niveaux) — beaucoup plus compact que int16
            r_min, r_max = float(residuals.min()), float(residuals.max())
            if r_max - r_min < 1e-12:
                r_max = r_min + 1.0
            residuals_norm = (residuals - r_min) / (r_max - r_min)
            residuals_u8 = np.clip(np.round(residuals_norm * 255), 0, 255).astype(np.uint8)

            # 3. Format binaire compact (compatible HCV PRO) :
            #   K(uint32) + N_blocks(uint32) + mean(float64) + std(float64)
            #   + r_min(float64) + r_max(float64)  — range dequantization
            #   + hologram(float64, K×64)
            #   + residuals_u8 zstd-compressed
            import struct
            payload_header = struct.pack('<IIdddd', K, N_blocks,
                                         float(sig.mean), float(sig.std),
                                         r_min, r_max)
            holo_bytes = sig.hologram.astype(np.float64).tobytes()
            payload_zstd_input = residuals_u8.tobytes()
            try:
                compressed_data = struct.pack('<I', len(payload_zstd_input)) + cctx.compress(payload_zstd_input)
            except Exception:
                compressed_data = struct.pack('<I', len(payload_zstd_input)) + payload_zstd_input

            total_bytes += len(payload_header) + len(holo_bytes) + len(compressed_data)

            # Combiner header + hologram + compressed payload
            full_payload = payload_header + holo_bytes + compressed_data

            encoded_channels[ch] = {
                'signature': sig,
                'compressed_data': full_payload,
                'mean': sig.mean,
                'std': sig.std,
                'source_shape': (H, W),
                'coeffs_quantized': sig.coefficients,
                'is_raw_signature': True,
                'use_dpcm_uint8': True,  # flag pour decode_photo
                'r_min': r_min,
                'r_max': r_max,
            }

            # Décode pour vignette
            decoded_channels[ch] = HolographicGenerator.reconstruct(sig, width=W, height=H)
            if decoded_channels[ch].shape != (H, W):
                decoded_channels[ch] = np.array(
                    Image.fromarray((decoded_channels[ch]*255).astype(np.uint8)).resize((W, H), Image.LANCZOS),
                    dtype=np.float64
                ) / 255.0

        # Assemblage RGB décodé pour vignette
        decoded_rgb = np.stack([
            np.clip(decoded_channels.get('R', np.zeros((H, W))), 0, 1),
            np.clip(decoded_channels.get('G', np.zeros((H, W))), 0, 1),
            np.clip(decoded_channels.get('B', np.zeros((H, W))), 0, 1),
        ], axis=-1)

        # Vignette (128px max)
        thumb_scale = 128.0 / max(H, W)
        th, tw = int(H * thumb_scale), int(W * thumb_scale)
        thumbnail = np.array(
            Image.fromarray((decoded_rgb * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS),
            dtype=np.float64
        ) / 255.0

        original_bytes = H * W * 3  # RGB
        ratio = original_bytes / max(1, total_bytes) if total_bytes > 0 else 0

        return {
            'encoded_R': encoded_channels['R'],
            'encoded_G': encoded_channels['G'],
            'encoded_B': encoded_channels['B'],
            'encoded': encoded_channels,  # dict R/G/B pour compatibilité
            'total_bytes': total_bytes,
            'ratio': ratio,
            'thumbnail': thumbnail,
            'source_shape': (H, W),
            'K': K,
        }

    def build_from_dataset(self, dataset_dir: str, max_images: int = 500,
                           K: int = 16):
        """
        Compresse toutes les photos du dataset en RGB et construit l'index FAISS.
        """
        all_files = sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpg'), recursive=True))
        all_files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpeg'), recursive=True))
        all_files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.png'), recursive=True))

        n = min(len(all_files), max_images)
        print(f"Compression + Indexation RGB de {n} photos (SVD K={K})...")
        t0 = time.time()
        total_original = 0
        total_compressed = 0

        for i, fpath in enumerate(all_files[:n]):
            try:
                # === CORRECTION : .convert('RGB') au lieu de .convert('L') ===
                img = np.array(Image.open(fpath).convert('RGB'), dtype=np.uint8)
                h, w = img.shape[:2]

                # Limiter taille max pour performance
                max_dim = 512
                if max(h, w) > max_dim:
                    scale = max_dim / max(h, w)
                    nh, nw = int(h * scale), int(w * scale)
                    img = np.array(
                        Image.fromarray(img).resize((nw, nh), Image.LANCZOS),
                        dtype=np.uint8
                    )
                    h, w = nh, nw

                # Compresser en RGB
                entry = self.compress_photo(img, source_path=fpath, K=K)

                rel_path = os.path.relpath(fpath, dataset_dir).replace('\\', '/')
                text_desc = rel_path.replace('_', ' ').replace('.jpg', '').replace('.png', '').replace('.jpeg', '')

                # === EMBEDDING : CLIP si disponible, sinon SVD 144-dim ===
                if self.use_clip and self.clip_encoder is not None:
                    # Embedding CLIP sémantique (image → texte aligné)
                    img_small = img  # déjà en uint8
                    emb_clip = self.clip_encoder.encode_image(img_small)  # (512,)
                    emb = emb_clip  # déjà normalisé
                    # Stocker aussi l'embedding SVD pour la résonance harmonique
                    self.store_coeff_vector(entry)
                else:
                    # Fallback : embedding SVD 144-dim
                    self.store_coeff_vector(entry)
                    emb_visual = entry['coeff_mean'].copy()
                    emb_visual = emb_visual / (np.linalg.norm(emb_visual) + 1e-12)
                    if len(emb_visual) < self.encoder.dimension:
                        emb_padded = np.zeros(self.encoder.dimension, dtype=np.float32)
                        emb_padded[:len(emb_visual)] = emb_visual
                        emb = emb_padded
                    else:
                        emb = emb_visual[:self.encoder.dimension].astype(np.float32)

                # Stocker
                entry['embedding'] = emb.astype(np.float32)
                entry['source_path'] = fpath
                entry['description'] = text_desc
                self.entries.append(entry)
                self.embeddings.append(emb.astype(np.float32))

                total_original += h * w * 3
                total_compressed += entry['total_bytes']

                if (i + 1) % 100 == 0:
                    ratio_avg = total_original / max(1, total_compressed)
                    print(f"  {i+1}/{n}... (ratio moyen: {ratio_avg:.0f}x)")

            except Exception as e:
                if (i + 1) % 50 == 0:
                    print(f"  [{i+1}] Erreur sur {os.path.basename(fpath)}: {e}")
                continue

        # Construire FAISS
        self._build_faiss()

        ratio_avg = total_original / max(1, total_compressed)
        print(f"  Index RGB prêt : {len(self.entries)} photos en {time.time()-t0:.1f}s")
        print(f"  Ratio de compression moyen : {ratio_avg:.0f}x")
        print(f"  Stockage total : {total_compressed//1024} Ko (vs {total_original//1024} Ko original)")

    def _build_faiss(self):
        if len(self.embeddings) < 2:
            return
        try:
            import faiss
            embs = np.array(self.embeddings, dtype=np.float32)
            faiss.normalize_L2(embs)
            self.faiss_index = faiss.IndexFlatIP(self.encoder.dimension)
            self.faiss_index.add(embs)
        except ImportError:
            self.faiss_index = None

    def store_coeff_vector(self, entry: dict):
        """
        Extrait et stocke le vecteur de signature holographique complet (144 dims).
        Combine : valeurs singulières (16×3) + coeffs moyens (16×3) + hologramme
        réduit par SVD (16×3) = 144 dimensions.

        Pour la résonance harmonique : ⟨Ψ_prompt | Ψ_image⟩ sur l'espace complet.
        """
        encoded = entry.get('encoded', {})
        if not isinstance(encoded, dict):
            encoded = {'R': encoded, 'G': encoded, 'B': encoded}

        signature_parts = []
        K = entry.get('K', 16)
        for ch in ['R', 'G', 'B']:
            enc_ch = encoded.get(ch, {})
            sig = enc_ch.get('signature')
            if sig is not None:
                # 1. Valeurs singulières (distribution d'énergie) — (K,)
                sv = sig.singular_values if sig.singular_values is not None else np.ones(K)
                sv_norm = sv[:K] / (np.sum(sv[:K]) + 1e-12)
                signature_parts.append(sv_norm.astype(np.float32))
                # 2. Coefficients moyennés (texture globale) — (K,)
                coeff_mean = np.mean(sig.coefficients, axis=0).astype(np.float32)
                coeff_mean = coeff_mean / (np.linalg.norm(coeff_mean) + 1e-12)
                signature_parts.append(coeff_mean)
                # 3. Hologramme réduit (base de projection) — (K,)
                holo_reduced = np.mean(sig.hologram[:K, :], axis=1).astype(np.float32)
                holo_reduced = holo_reduced / (np.linalg.norm(holo_reduced) + 1e-12)
                signature_parts.append(holo_reduced)
            else:
                signature_parts.extend([np.zeros(K, dtype=np.float32)] * 3)

        entry['coeff_mean'] = np.concatenate(signature_parts).astype(np.float32)  # (9*K,)

    def harmonic_resonance_search(self, prompt: str, k: int = 5) -> list:
        """
        Recherche par RÉSONANCE HARMONIQUE : ⟨Ψ_prompt | Ψ_image⟩.

        Le prompt est encodé en H-Bit harmonique (onde Ψ_prompt).
        Chaque image est représentée par son vecteur de coefficients SVD concaténé R+G+B.
        L'interférence = produit scalaire entre les deux ondes.

        C'est le MÊME mécanisme que Poetic Emergence v4 :
          interference_score = |⟨Ψ_prompt | Ψ_image⟩|²

        Returns:
            Liste de (idx, score_de_résonance)
        """
        # 1. Encodage harmonique du prompt (H-Bit)
        prompt_emb = self.encoder.encode(prompt)

        # 2. Pour chaque image, calculer l'interférence avec les coefficients SVD
        scores = []
        for idx, entry in enumerate(self.entries):
            coeff_mean = entry.get('coeff_mean')
            if coeff_mean is None or len(coeff_mean) == 0:
                scores.append(0.0)
                continue

            # Normaliser le vecteur de coefficients (3*K dims)
            coeff_norm = coeff_mean / (np.linalg.norm(coeff_mean) + 1e-12)

            # Projeter le prompt embedding dans l'espace des coefficients concaténés
            K_total = len(coeff_norm)
            prompt_vec = prompt_emb[:K_total] / (np.linalg.norm(prompt_emb[:K_total]) + 1e-12)

            # INTERFÉRENCE HARMONIQUE : ⟨Ψ_prompt | Ψ_image⟩
            interference = float(np.abs(np.dot(prompt_vec, coeff_norm)))

            # Pondération Hₙ : les 7 constantes répétées pour K_total dimensions
            h_repeated = np.tile(H_CONSTANTS, (K_total + 6) // 7)[:K_total]
            h_weights = h_repeated / np.sum(h_repeated)
            weighted_interference = float(np.abs(np.dot(prompt_vec * h_weights, coeff_norm * h_weights)))

            # Score final = combinaison des deux
            score = 0.5 * interference + 0.5 * weighted_interference
            scores.append(score)

        # 3. Trier par score de résonance décroissant
        top_indices = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in top_indices]

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list:
        """
        Recherche les K photos les plus proches sémantiquement (fallback FAISS).

        Returns:
            Liste de (idx, score)
        """
        if self.faiss_index is not None:
            import faiss
            q = query_embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(q)
            scores, indices = self.faiss_index.search(q, min(k, len(self.entries)))
            return [(int(indices[0][i]), float(scores[0][i])) for i in range(len(indices[0]))]
        else:
            embs = np.array(self.embeddings)
            scores = np.dot(embs, query_embedding.flatten())
            top = np.argsort(scores)[::-1][:k]
            return [(int(i), float(scores[i])) for i in top]

    def _get_channel_signature(self, entry: dict, channel: str) -> Optional[HolographicSignature]:
        """Récupère la HolographicSignature pour un canal donné."""
        encoded_ch = entry.get(f'encoded_{channel}') or entry.get('encoded', {}).get(channel, {})
        sig = encoded_ch.get('signature')
        if sig is not None:
            return sig
        # Fallback : reconstruire depuis les données quantifiées
        if 'coeffs_quantized' in encoded_ch:
            cq = encoded_ch['coeffs_quantized']
            h, w = entry['source_shape']
            # Créer un hologramme de base
            dummy = np.zeros((min(h // BLOCK_SIZE, 4), min(w // BLOCK_SIZE, 4)), dtype=np.float64)
            holo_sig = HolographicTrainer.train_image(dummy, K=entry['K'])
            return HolographicSignature(
                hologram=holo_sig.hologram[:entry['K']],
                coefficients=cq.astype(np.float64),
                mean=encoded_ch.get('mean', 0.0),
                std=encoded_ch.get('std', 1.0),
                source_shape=entry['source_shape'],
                K=entry['K'],
            )
        return None

    def decode_photo(self, idx: int) -> np.ndarray:
        """
        Décompresse une photo depuis l'index — retourne une image RGB (H, W, 3).

        Returns:
            Image RGB [0, 1] (H, W, 3)
        """
        import struct, zstandard as zstd_module
        dctx = zstd_module.ZstdDecompressor()

        entry = self.entries[idx]
        H, W = entry['source_shape']
        channels_rgb = []

        for ch in ['R', 'G', 'B']:
            encoded_ch = entry.get(f'encoded_{ch}') or entry.get('encoded', {}).get(ch, {})

            if not encoded_ch:
                channels_rgb.append(np.zeros((H, W), dtype=np.float64))
                continue

            # 1. Essayer la reconstruction directe via signature (stockée dans le dict)
            sig = encoded_ch.get('signature')
            if sig is not None:
                decoded_ch = HolographicGenerator.reconstruct(sig, width=W, height=H)
                channels_rgb.append(np.clip(decoded_ch, 0, 1))
                continue

            # 2. DPCM+uint8 format (use_dpcm_uint8=True) — nouvel encodeur HCV PRO
            if encoded_ch.get('use_dpcm_uint8') and encoded_ch.get('compressed_data'):
                data = encoded_ch['compressed_data']
                # Parse header: K(uint32) + N(uint32) + mean(float64) + std(float64) + r_min(float64) + r_max(float64)
                header_fmt_dpcm = '<IIdddd'
                header_size_dpcm = struct.calcsize(header_fmt_dpcm)
                K_ch, N_blocks, mean_val, std_val, r_min, r_max = struct.unpack(header_fmt_dpcm, data[:header_size_dpcm])
                holo_size = K_ch * 64 * 8
                holo_bytes = data[header_size_dpcm:header_size_dpcm + holo_size]
                hologram = np.frombuffer(holo_bytes, dtype=np.float64).reshape(K_ch, 64)

                # zstd payload
                zstd_offset = header_size_dpcm + holo_size
                payload_len = struct.unpack('<I', data[zstd_offset:zstd_offset + 4])[0]
                zstd_data = data[zstd_offset + 4:zstd_offset + 4 + payload_len]
                try:
                    residuals_u8 = np.frombuffer(dctx.decompress(zstd_data), dtype=np.uint8)
                except Exception:
                    residuals_u8 = np.frombuffer(zstd_data, dtype=np.uint8)

                # Dequantize uint8 → float64 residuals
                residuals_norm = residuals_u8.astype(np.float64) / 255.0
                residuals = residuals_norm * (r_max - r_min) + r_min
                residuals = residuals.reshape(N_blocks, K_ch)

                # DPCM inverse
                coeffs = np.zeros_like(residuals, dtype=np.float64)
                coeffs[0, :] = residuals[0, :]
                for bi in range(1, N_blocks):
                    coeffs[bi, :] = residuals[bi, :] + coeffs[bi - 1, :]

                # Reconstruire vectorisé
                n_h = H // BLOCK_SIZE
                n_w = W // BLOCK_SIZE
                n_valid = min(N_blocks, n_h * n_w)
                blocks = np.dot(coeffs[:n_valid], hologram) * std_val + mean_val
                blocks = blocks[:n_h * n_w].reshape(n_h, n_w, BLOCK_SIZE, BLOCK_SIZE)
                image = np.zeros((H, W), dtype=np.float64)
                image[:, :] = blocks.transpose(0, 2, 1, 3).reshape(n_h * BLOCK_SIZE, n_w * BLOCK_SIZE)
                channels_rgb.append(np.clip(image, 0, 1))
                continue

            # 3. Essayer le format zstd brut legacy (is_raw_signature, int16+q_vec ou float64)
            if encoded_ch.get('is_raw_signature') and encoded_ch.get('compressed_data'):
                compressed_data = encoded_ch['compressed_data']
                try:
                    payload = dctx.decompress(compressed_data, max_output_size=100_000_000)
                except Exception:
                    payload = compressed_data

                header_fmt = '<IIdd'
                header_size = struct.calcsize(header_fmt)
                K_ch, N_blocks, mean_val, std_val = struct.unpack(header_fmt, payload[:header_size])
                holo_size = K_ch * 64 * 8
                q_vec_offset = header_size + holo_size
                q_vec_size = K_ch * 4
                coeffs_int16_size = N_blocks * K_ch * 2
                coeffs_float64_size = N_blocks * K_ch * 8
                remaining = len(payload) - q_vec_offset

                if remaining >= q_vec_size + coeffs_int16_size and remaining < q_vec_size + coeffs_float64_size + 256:
                    q_vec = np.frombuffer(payload[q_vec_offset:q_vec_offset + q_vec_size], dtype=np.float32)
                    coeffs_int16_offset = q_vec_offset + q_vec_size
                    coeffs_q = np.frombuffer(
                        payload[coeffs_int16_offset:coeffs_int16_offset + coeffs_int16_size],
                        dtype=np.int16
                    ).reshape(N_blocks, K_ch)
                    coeffs = dequantize_coeffs(coeffs_q.astype(np.float64), q_vec)
                else:
                    coeff_bytes = payload[q_vec_offset:q_vec_offset + coeffs_float64_size]
                    coeffs = np.frombuffer(coeff_bytes, dtype=np.float64).reshape(N_blocks, K_ch)

                holo_bytes = payload[header_size:header_size + holo_size]
                hologram = np.frombuffer(holo_bytes, dtype=np.float64).reshape(K_ch, 64)

                n_h = H // BLOCK_SIZE
                n_w = W // BLOCK_SIZE
                n_valid = min(N_blocks, n_h * n_w)
                blocks = np.dot(coeffs[:n_valid], hologram) * std_val + mean_val
                blocks = blocks[:n_h * n_w].reshape(n_h, n_w, BLOCK_SIZE, BLOCK_SIZE)
                image = np.zeros((H, W), dtype=np.float64)
                image[:, :] = blocks.transpose(0, 2, 1, 3).reshape(n_h * BLOCK_SIZE, n_w * BLOCK_SIZE)
                channels_rgb.append(np.clip(image, 0, 1))
                continue

            # 3. Fallback : tenter codec SVD (ancien format)
            codec = OptimizedSVDCodec(K=entry['K'], quality=1.0, zstd_level=19,
                                       use_adaptive_q=True, use_bit_allocation=True)
            try:
                decoded_ch = codec.decode(encoded_ch)
            except Exception:
                decoded_ch = np.zeros((H, W), dtype=np.float64)
            channels_rgb.append(np.clip(decoded_ch, 0, 1))

        return np.stack(channels_rgb, axis=-1)  # (H, W, 3)

    def get_thumbnail(self, idx: int) -> np.ndarray:
        return self.entries[idx]['thumbnail']

    def __len__(self):
        return len(self.entries)


# ==============================================================================
# UPSCALING 4K (adapté RGB)
# ==============================================================================

class UpscalePipeline:
    """Pipeline d'upscaling RGB : SVD 2× → Lanczos → Hₙ sharpen → 4K."""

    @staticmethod
    def svd_upscale(image: np.ndarray, K: int = 16) -> np.ndarray:
        """Upscale 2× via SVD super-resolution (par canal)."""
        if image.ndim == 3:
            channels = []
            for c in range(3):
                ch = image[:, :, c]
                sig = HolographicTrainer.train_image(ch, K=K)
                hires_sig = HolographicGenerator.super_resolve(sig, scale_factor=2)
                h, w = ch.shape
                channels.append(HolographicGenerator.reconstruct(hires_sig, width=w * 2, height=h * 2))
            return np.stack(channels, axis=-1)
        else:
            sig = HolographicTrainer.train_image(image, K=K)
            hires_sig = HolographicGenerator.super_resolve(sig, scale_factor=2)
            h, w = image.shape
            return HolographicGenerator.reconstruct(hires_sig, width=w * 2, height=h * 2)

    @staticmethod
    def lanczos_upscale(image: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
        """Upscale via Lanczos (RGB-aware)."""
        if image.ndim == 3:
            pil_img = Image.fromarray((np.clip(image, 0, 1) * 255).astype(np.uint8), 'RGB')
        else:
            pil_img = Image.fromarray((np.clip(image, 0, 1) * 255).astype(np.uint8))
        resized = pil_img.resize((target_w, target_h), Image.LANCZOS)
        return np.array(resized, dtype=np.float64) / 255.0

    @staticmethod
    def harmonic_sharpen(image: np.ndarray) -> np.ndarray:
        """Post-processing Hₙ sharpen (RGB-aware)."""
        from scipy.ndimage import gaussian_filter

        if image.ndim == 3:
            channels = []
            for c in range(3):
                ch = image[:, :, c]
                ch = np.clip(ch, 0, 1).astype(np.float64)
                mean_val = np.mean(ch)
                ch = mean_val + (ch - mean_val) * PHI * 0.85
                ch_smooth = gaussian_filter(ch, sigma=0.4)
                ch = ch * 0.9 + ch_smooth * 0.1
                ch_blur = gaussian_filter(ch, sigma=1.2)
                detail = ch - ch_blur
                ch = ch + detail * (SQRT5 / 4)
                h, w = ch.shape
                Y, X = np.ogrid[:h, :w]
                X_norm = X / w * 2 - 1
                Y_norm = Y / h * 2 - 1
                R = np.sqrt(X_norm ** 2 + Y_norm ** 2)
                theta = np.arctan2(Y_norm, X_norm)
                grain = np.sin(R * 40 * E_PI + theta * 7) * 0.003
                ch = ch + grain
                channels.append(np.clip(ch, 0, 1))
            return np.stack(channels, axis=-1)
        else:
            img = np.clip(image, 0, 1).astype(np.float64)
            mean_val = np.mean(img)
            img = mean_val + (img - mean_val) * PHI * 0.85
            img_smooth = gaussian_filter(img, sigma=0.4)
            img = img * 0.9 + img_smooth * 0.1
            img_blur = gaussian_filter(img, sigma=1.2)
            detail = img - img_blur
            img = img + detail * (SQRT5 / 4)
            h, w = img.shape
            Y, X = np.ogrid[:h, :w]
            X_norm = X / w * 2 - 1
            Y_norm = Y / h * 2 - 1
            R = np.sqrt(X_norm ** 2 + Y_norm ** 2)
            theta = np.arctan2(Y_norm, X_norm)
            grain = np.sin(R * 40 * E_PI + theta * 7) * 0.003
            img = img + grain
            return np.clip(img, 0, 1)

    @classmethod
    def upscale_to(cls, image: np.ndarray, target_res: str = '4k') -> np.ndarray:
        """Upscale vers une résolution cible."""
        target_w, target_h = RESOLUTIONS.get(target_res, RESOLUTIONS.get('sd', (512, 512)))
        h = image.shape[0]
        w = image.shape[1]
        if w < target_w // 2:
            image = cls.svd_upscale(image, K=16)
        if image.shape[1] != target_w or image.shape[0] != target_h:
            image = cls.lanczos_upscale(image, target_w, target_h)
        image = cls.harmonic_sharpen(image)
        return image


# ==============================================================================
# MOTEUR DE RETRIEVAL + UPSCALING (RGB natif)
# ==============================================================================

class HarmonicPhotoRetrieval:
    """
    Moteur complet : Index → Retrieval → Décompression → Upscaling → RGB natif.
    """

    def __init__(self, index: HarmonicPhotoIndex = None):
        self.index = index
        self.upscaler = UpscalePipeline()

    def retrieve(self, prompt: str, top_k: int = 1,
                 upscale: str = None,
                 style: str = None,
                 use_harmonic_resonance: bool = False) -> dict:
        """
        Retrieval d'une photo par prompt.

        Args:
            prompt: Texte de recherche
            top_k: Nombre de résultats
            upscale: None, 'hd', ou '4k'
            style: Palette de couleur (si None, RGB natif)
            use_harmonic_resonance: utilise ⟨Ψ_prompt|Ψ_image⟩ (défaut False)

        Returns:
            dict avec 'images', 'scores', 'paths', 'metadata'
        """
        # 1. Recherche :
        #    - CLIP : texte → embedding CLIP → FAISS (aligné sémantiquement)
        #    - Resonance : ⟨Ψ_prompt|Ψ_image⟩ (mathématique, pas sémantique)
        #    - Fallback : FAISS sur embeddings spectraux SVD
        if self.index.use_clip and self.index.clip_encoder is not None:
            query_emb = self.index.clip_encoder.encode_text(prompt)
            matches = self.index.search(query_emb, k=top_k)
        elif use_harmonic_resonance and len(self.index) >= 2:
            matches = self.index.harmonic_resonance_search(prompt, k=top_k)
        else:
            query_emb = self.index.encoder.encode(prompt)
            matches = self.index.search(query_emb, k=top_k)

        results = []
        for idx, score in matches:
            # 3. Décompression RGB native
            rgb_native = self.index.decode_photo(idx)

            # 4. Upscaling (RGB-aware)
            if upscale:
                rgb_native = self.upscaler.upscale_to(rgb_native, upscale)

            # 5. Application du style si demandé (sinon RGB natif)
            if style and rgb_native.ndim == 3:
                # Conversion via HarmonicColorMapper (nécessite conversion en field)
                gray = np.mean(rgb_native, axis=2)
                field = gray * 2 - 1
                rgb_styled = HarmonicColorMapper.harmonic_hsl(field, palette=style)
                rgb = rgb_styled
            elif style:
                field = rgb_native * 2 - 1
                rgb = HarmonicColorMapper.harmonic_hsl(field, palette=style)
            else:
                # RGB natif — directement utilisable
                rgb = rgb_native

            pil_image = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), 'RGB' if rgb.ndim == 3 else 'L')

            results.append({
                'image': pil_image,
                'rgb': rgb if rgb.ndim == 3 else np.stack([rgb, rgb, rgb], axis=-1),
                'grayscale': np.mean(rgb_native, axis=2) if rgb_native.ndim == 3 else rgb_native,
                'score': score,
                'source_path': self.index.entries[idx].get('source_path', ''),
                'description': self.index.entries[idx].get('description', ''),
                'compression_ratio': self.index.entries[idx].get('ratio', 0),
            })

        return {
            'images': [r['image'] for r in results],
            'scores': [r['score'] for r in results],
            'paths': [r['source_path'] for r in results],
            'results': results,
            'metadata': {
                'prompt': prompt,
                'top_k': top_k,
                'upscale': upscale,
                'index_size': len(self.index),
                'mode': 'retrieval',
            },
        }

    def generate_variation(self, prompt: str, n_sources: int = 7,
                           width: int = 512, height: int = 512,
                           upscale: str = None, style: str = None) -> dict:
        """
        GÉNÉRATION par INTERFÉRENCE HARMONIQUE RGB — Crée une NOUVELLE image.

        Mécanisme (identique à Poetic Emergence v4, étendu RGB) :
          1. Prompt → Embedding → K signatures SVD qui résonnent le plus
          2. FUSION des coefficients SVD par interférence Hₙ-pondérée
             (Ψ_A × Ψ_B → Ψ_AB — le produit croisé crée de l'émergence)
          3. Fusion indépendante sur chaque canal (R, G, B)
          4. Reconstruction → Image RGB qui n'existe dans AUCUNE des K sources

        Args:
            prompt: Texte décrivant l'image souhaitée
            n_sources: Nombre de signatures SVD à fusionner (défaut 7, comme les 7Hₙ)
            width, height: Dimensions de sortie
            upscale: Optionnel — 'hd' ou '4k'
            style: Palette de couleur

        Returns:
            dict avec l'image générée et les métadonnées
        """
        # 1. Trouver les K signatures qui résonnent le plus avec le prompt
        matches = self.index.harmonic_resonance_search(prompt, k=n_sources * 2)

        if not matches:
            return {'error': 'Aucune signature trouvée'}

        top_matches = matches[:min(n_sources, len(matches))]
        n_selected = len(top_matches)

        channels_rgb = []
        for ch_name in ['R', 'G', 'B']:
            # 2. Récupérer les signatures SVD pour ce canal
            selected_sigs = []
            interference_scores = []
            for idx_match, score in top_matches:
                entry = self.index.entries[idx_match]
                sig = self.index._get_channel_signature(entry, ch_name)
                if sig is not None:
                    selected_sigs.append(sig)
                    interference_scores.append(score)

            if not selected_sigs:
                # Fallback : canvas gris pour ce canal
                channels_rgb.append(np.ones((height, width), dtype=np.float64) * 0.5)
                continue

            # 3. FUSION CRÉATIVE par interférence Hₙ-pondérée
            min_K = min(s.K for s in selected_sigs)
            max_blocks = min(s.coefficients.shape[0] for s in selected_sigs)
            max_blocks = min(max_blocks, 256)

            # Hologramme fusionné (base de projection)
            fused_hologram = selected_sigs[0].hologram[:min_K].copy()
            total_interference = sum(max(0.01, s) for s in interference_scores)
            for i in range(1, n_selected):
                weight_i = max(0.01, interference_scores[i]) / total_interference
                contrib = selected_sigs[i].hologram[:min_K] * weight_i * (1.0 / PHI)
                fused_hologram += contrib
            for k in range(min_K):
                n = np.linalg.norm(fused_hologram[k])
                if n > 1e-12:
                    fused_hologram[k] /= n

            # Coefficients fusionnés avec INTERFÉRENCE CROISÉE
            fused_coeffs = np.zeros((max_blocks, min_K), dtype=np.float64)
            for i in range(n_selected):
                h_weight = H_CONSTANTS[min(i, 6)] / PHI
                interference_weight = max(0.01, interference_scores[i])
                coeffs = selected_sigs[i].coefficients[:max_blocks, :min_K]
                weight = h_weight * interference_weight
                fused_coeffs += coeffs * weight

                # TERME CROISÉ : Ψ_A × Ψ_B → émergence
                if i + 1 < n_selected:
                    cross_weight = weight * interference_scores[i + 1] * 0.15
                    coeffs_next = selected_sigs[i + 1].coefficients[:max_blocks, :min_K]
                    cross_term = coeffs * coeffs_next * cross_weight
                    fused_coeffs += cross_term

            total_weight = sum(
                H_CONSTANTS[min(i, 6)] / PHI * max(0.01, interference_scores[i])
                for i in range(n_selected)
            )
            fused_coeffs /= max(1e-12, total_weight)

            # Statistiques fusionnées
            fused_mean = sum(
                s.mean * H_CONSTANTS[min(i, 6)] / PHI * max(0.01, interference_scores[i])
                for i, s in enumerate(selected_sigs)
            ) / max(1e-12, total_weight)
            fused_std = sum(
                s.std * H_CONSTANTS[min(i, 6)] / PHI * max(0.01, interference_scores[i])
                for i, s in enumerate(selected_sigs)
            ) / max(1e-12, total_weight)

            # 4. Reconstruction du canal
            fused_sig = HolographicSignature(
                hologram=fused_hologram,
                coefficients=fused_coeffs,
                mean=fused_mean,
                std=fused_std,
                source_shape=(height, width),
                K=min_K,
            )
            ch_image = HolographicGenerator.reconstruct(fused_sig, width=width, height=height)
            channels_rgb.append(np.clip(ch_image, 0, 1))

        # Assemblage RGB
        base_image = np.stack(channels_rgb, axis=-1)  # (H, W, 3)

        # 5. Post-processing (sur le canal luminance pour la synthèse de détails)
        from harmonic_detail_synthesizer import enhance_existing_pipeline
        gray_base = np.mean(base_image, axis=2)
        enhanced_gray = enhance_existing_pipeline(gray_base, strength=1.0,
                                                   detail_seed=hash(prompt) % (2 ** 31))
        # Réinjecter la chrominance
        gray_diff = enhanced_gray - gray_base
        enhanced = base_image + gray_diff[:, :, np.newaxis]
        enhanced = np.clip(enhanced, 0, 1)

        # 6. Upscaling
        if upscale:
            enhanced = self.upscaler.upscale_to(enhanced, upscale)

        # 7. Application du style
        if style and enhanced.ndim == 3:
            gray_enhanced = np.mean(enhanced, axis=2)
            field = gray_enhanced * 2 - 1
            rgb = HarmonicColorMapper.harmonic_hsl(field, palette=style)
        elif style:
            field = enhanced * 2 - 1
            rgb = HarmonicColorMapper.harmonic_hsl(field, palette=style)
        else:
            rgb = enhanced

        pil_image = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), 'RGB' if rgb.ndim == 3 else 'L')

        # Score d'émergence (distance aux sources)
        emergence_score = np.std([s for _, s in top_matches]) * 100

        return {
            'image': pil_image,
            'rgb': rgb if rgb.ndim == 3 else np.stack([rgb, rgb, rgb], axis=-1),
            'grayscale': np.mean(enhanced, axis=2) if enhanced.ndim == 3 else enhanced,
            'base_grayscale': np.mean(base_image, axis=2),
            'emergence_score': emergence_score,
            'n_sources': n_selected,
            'sources': [self.index.entries[idx].get('description', '')[:30] for idx, _ in top_matches],
            'metadata': {
                'prompt': prompt,
                'n_sources': n_selected,
                'upscale': upscale,
                'style': style,
                'mode': 'harmonic_interference_rgb',
                'emergence_score': emergence_score,
            },
        }


# ==============================================================================
# DÉMO
# ==============================================================================

def demo_retrieval():
    """Démonstration du pipeline complet RGB."""
    print("=" * 80)
    print("  HARMONIC PHOTO RETRIEVAL v2 — Compression RGB + Retrieval + Upscaling")
    print("=" * 80)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'retrieval')
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
        print("Aucun dataset trouvé. Création d'un mini dataset de test...")
        dataset_dir = os.path.join(out_dir, 'test_dataset')
        os.makedirs(dataset_dir, exist_ok=True)
        # Créer quelques images de test
        for i in range(10):
            img = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
            Image.fromarray(img).save(os.path.join(dataset_dir, f'test_{i:03d}.jpg'))

    # Phase 1 : Construire l'index
    index_path = os.path.join(out_dir, 'photo_index_rgb.npz')
    if os.path.exists(index_path):
        print("\n[Phase 1] Chargement de l'index RGB existant...")
        index = HarmonicPhotoIndex()
        data = np.load(index_path, allow_pickle=True)
        index.entries = list(data['entries'])
        index.embeddings = list(data['embeddings'])
        index._build_faiss()
        print(f"  Index chargé : {len(index)} photos")
    else:
        print("\n[Phase 1] Construction de l'index RGB (compression SVD 3 canaux)...")
        index = HarmonicPhotoIndex()
        index.build_from_dataset(dataset_dir, max_images=50, K=16)
        # Sauvegarder
        np.savez_compressed(index_path,
                           entries=np.array(index.entries, dtype=object),
                           embeddings=np.array(index.embeddings))
        print(f"  Index sauvegardé : {index_path}")

    # Phase 2 : Retrieval
    print("\n[Phase 2] Retrieval par prompts...")
    engine = HarmonicPhotoRetrieval(index=index)

    test_prompts = [
        ("sunset over mountains", "hd", "solaire"),
        ("green forest nature", None, "forest"),
        ("ocean waves beach", "4k", "ocean"),
        ("night sky stars galaxy", None, "galactique"),
        ("city building architecture", "hd", None),
    ]

    for prompt, upscale, style in test_prompts:
        print(f"\n  Prompt: '{prompt}' (upscale={upscale or 'none'}, style={style or 'RGB natif'})")
        result = engine.retrieve(prompt, top_k=1, upscale=upscale, style=style)

        img_id = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        res_str = upscale or 'sd'
        img_path = os.path.join(out_dir, f'retrieved_rgb_{res_str}_{img_id}.png')
        result['results'][0]['image'].save(img_path)

        r = result['results'][0]
        print(f"    Score: {r['score']:.4f} | Ratio: {r['compression_ratio']:.0f}x")
        print(f"    Source: {os.path.basename(r['source_path'])[:40]}")
        print(f"    Sauvegardé: {img_path}")

    # Phase 3 : Génération par variation
    print(f"\n{'='*80}")
    print("  GÉNÉRATION PAR INTERFÉRENCE HARMONIQUE RGB")
    print(f"{'='*80}")
    gen_prompts = ["sunset over mountains", "forest at dawn", "cosmic nebula"]

    for prompt in gen_prompts:
        print(f"\n  Génération: '{prompt}'...")
        gen_result = engine.generate_variation(prompt, n_sources=7, width=512, height=512)

        if 'error' not in gen_result:
            img_id = hashlib.sha256(f"gen_{prompt}".encode()).hexdigest()[:8]
            gen_path = os.path.join(out_dir, f'generated_rgb_{img_id}.png')
            gen_result['image'].save(gen_path)
            print(f"    Émergence: {gen_result['emergence_score']:.1f} | Sauvegardé: {gen_path}")
        else:
            print(f"    Erreur: {gen_result['error']}")

    # Phase 4 : Métriques
    print(f"\n{'='*80}")
    print("  RAPPORT")
    print(f"{'='*80}")
    print(f"  Photos indexées : {len(index)}")
    ratios = [e.get('ratio', 0) for e in index.entries if e.get('ratio', 0) > 0]
    if ratios:
        print(f"  Ratio compression moyen : {np.mean(ratios):.0f}x")
        print(f"  Ratio min/max : {np.min(ratios):.0f}x / {np.max(ratios):.0f}x")
    print(f"  Fichiers dans : {out_dir}/")
    for f in sorted(os.listdir(out_dir)):
        sz = os.path.getsize(os.path.join(out_dir, f))
        print(f"    {f:<50s} ({sz//1024} Ko)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Harmonic Photo Retrieval v2 — RGB natif')
    parser.add_argument('--build-index', action='store_true', help='Compresser tout le dataset en RGB')
    parser.add_argument('--prompt', type=str, default=None, help='Prompt de recherche')
    parser.add_argument('--generate', type=str, default=None, help='Prompt de génération par variation')
    parser.add_argument('--top-k', type=int, default=1, help='Nombre de résultats')
    parser.add_argument('--n-sources', type=int, default=7, help='Nb signatures pour génération')
    parser.add_argument('--upscale', type=str, default=None, choices=[None, 'hd', '4k'], help='Upscaling')
    parser.add_argument('--style', type=str, default=None, help='Palette couleur (sinon RGB natif)')
    parser.add_argument('--width', type=int, default=512, help='Largeur de sortie (génération)')
    parser.add_argument('--height', type=int, default=512, help='Hauteur de sortie (génération)')
    parser.add_argument('--output', type=str, default=None, help='Fichier de sortie')
    parser.add_argument('--dataset', type=str, default=None, help='Dossier dataset')
    parser.add_argument('--demo', action='store_true', help='Pipeline complet')

    args = parser.parse_args()

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'retrieval')
    os.makedirs(out_dir, exist_ok=True)
    index_path = os.path.join(out_dir, 'photo_index_rgb.npz')

    # Résoudre dataset
    if args.dataset:
        dataset_dir = args.dataset
    else:
        dataset_dirs = [
            os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'unified', 'dataset'),
            os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'massive_dataset'),
        ]
        dataset_dir = None
        for d in dataset_dirs:
            if os.path.isdir(d):
                dataset_dir = d
                break

    if args.build_index:
        if not dataset_dir:
            print("Aucun dataset trouvé. Spécifiez --dataset ou créez un dataset.")
            sys.exit(1)
        index = HarmonicPhotoIndex()
        index.build_from_dataset(dataset_dir, max_images=300, K=16)
        np.savez_compressed(index_path,
                           entries=np.array(index.entries, dtype=object),
                           embeddings=np.array(index.embeddings))
        print(f"Index RGB sauvegardé : {index_path}")

    elif args.generate:
        # Mode GÉNÉRATION par variation
        if not os.path.exists(index_path):
            print("Index non trouvé. Lancer --build-index d'abord.")
            sys.exit(1)

        index = HarmonicPhotoIndex()
        data = np.load(index_path, allow_pickle=True)
        index.entries = list(data['entries'])
        index.embeddings = list(data['embeddings'])
        index._build_faiss()
        print(f"Index chargé : {len(index)} photos")

        engine = HarmonicPhotoRetrieval(index=index)
        gen_result = engine.generate_variation(
            args.generate,
            n_sources=args.n_sources,
            width=args.width,
            height=args.height,
            upscale=args.upscale,
            style=args.style,
        )

        if 'error' in gen_result:
            print(f"Erreur: {gen_result['error']}")
            sys.exit(1)

        if args.output:
            out_path = args.output
        else:
            img_id = hashlib.sha256(f"gen_{args.generate}".encode()).hexdigest()[:8]
            out_path = os.path.join(out_dir, f'generated_{img_id}.png')
        gen_result['image'].save(out_path)
        print(f"Image générée : émergence={gen_result['emergence_score']:.1f} → {out_path}")
        print(f"  Sources : {gen_result['sources']}")

    elif args.prompt:
        # Mode RETRIEVAL
        if not os.path.exists(index_path):
            print("Index non trouvé. Lancer --build-index d'abord.")
            sys.exit(1)

        index = HarmonicPhotoIndex()
        data = np.load(index_path, allow_pickle=True)
        index.entries = list(data['entries'])
        index.embeddings = list(data['embeddings'])
        index._build_faiss()
        print(f"Index chargé : {len(index)} photos")

        engine = HarmonicPhotoRetrieval(index=index)
        result = engine.retrieve(args.prompt, top_k=args.top_k,
                                  upscale=args.upscale, style=args.style)

        for i, img in enumerate(result['images']):
            if args.output:
                out_path = args.output if args.top_k == 1 else args.output.replace('.png', f'_{i+1}.png')
            else:
                img_id = hashlib.sha256(f"{args.prompt}_{i}".encode()).hexdigest()[:8]
                out_path = os.path.join(out_dir, f'result_{img_id}.png')
            img.save(out_path)
            print(f"Résultat {i+1}: score={result['scores'][i]:.4f} → {out_path}")

    elif args.demo:
        demo_retrieval()

    else:
        demo_retrieval()