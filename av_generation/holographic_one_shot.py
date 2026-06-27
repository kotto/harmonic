#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENTRAÎNEMENT ONE-SHOT HOLOGRAPHIQUE — Génération Photoréaliste
================================================================
Inspiré du modèle Harmonic AI intégré dans KA PHONE avec hologrammes SVD.

Principe fondamental :
  Plutôt que générer procéduralement (Ψ = Σ Hₙ (Ψ₁)ⁿ),
  on ENTRAÎNE un hologramme SVD sur une ou plusieurs images réelles,
  puis on GÉNÈRE de nouvelles images par manipulation des coefficients
  dans l'espace holographique.

Pipeline One-Shot :
  1. Prendre 1 image source (photographie, artwork)
  2. Décomposer en blocs 8×8 → matrice N×64
  3. SVD → hologramme K×64 (K bases apprises sur le contenu)
  4. Extraire les coefficients spectraux (signature holographique)
  5. Manipuler les coefficients (interpolation, extrapolation, bruit)
  6. Reconstruire → nouvelle image dans le même "style holographique"

Pour l'audio :
  Même principe sur des segments temporels → spectrogramme → SVD → hologramme temporel

Pour la vidéo :
  Entraînement inter-frame → hologramme spatio-temporel 3D

Author: Système Harmonique
Version: 2.0 — One-Shot Photorealistic
"""

import numpy as np
import math
import sys
import os
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from PIL import Image
import wave
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES,
    SeedManager, normalize_field
)

# ==============================================================================
# HOLOGRAMME SVD — Même architecture que HCV PRO / KA PHONE
# ==============================================================================

BLOCK_SIZE = 8
BLOCK_DIM = BLOCK_SIZE * BLOCK_SIZE  # 64


@dataclass
class HolographicSignature:
    """
    Signature holographique extraite d'une image/audio/vidéo.
    
    Contient :
      - hologram: la base apprise (K × 64 pour image, K × N pour audio)
      - coefficients: la projection du contenu sur la base
      - mean, std: statistiques de normalisation
      - singular_values: valeurs singulières (énergie par composante)
    """
    hologram: np.ndarray          # K × BLOCK_DIM
    coefficients: np.ndarray      # N_blocks × K
    mean: float = 0.0
    std: float = 1.0
    singular_values: Optional[np.ndarray] = None
    source_shape: Tuple = (0, 0)
    K: int = 8
    content_hash: str = ""
    
    def energy_spectrum(self) -> np.ndarray:
        """Distribution d'énergie par composante holographique."""
        if self.singular_values is not None:
            sv = self.singular_values
            return sv**2 / (np.sum(sv**2) + 1e-12)
        return np.ones(self.K) / self.K
    
    def coherence_score(self) -> float:
        """
        Score de cohérence : à quel point l'hologramme capture le contenu.
        1.0 = reconstruction parfaite avec K composantes.
        """
        energy = self.energy_spectrum()
        return float(np.sum(energy[:min(self.K, 4)]))


class HolographicTrainer:
    """
    Entraîneur One-Shot : extrait une signature holographique d'un seul exemple.
    
    C'est le cœur du modèle Harmonic AI / KA PHONE :
    - Pas besoin de milliers d'exemples
    - Un seul exemple suffit pour capturer la "signature" du contenu
    - La base SVD est l'équivalent mathématique d'un "hologramme" du contenu
    """
    
    @staticmethod
    def train_image(image: np.ndarray, K: int = 8) -> HolographicSignature:
        """
        Extrait la signature holographique d'une image (one-shot).
        
        Args:
            image: Array (H, W) ou (H, W, 3) en uint8 ou float
            K: Nombre de composantes holographiques (qualité)
        
        Returns:
            HolographicSignature avec hologramme et coefficients
        """
        # Convertir en float et normaliser
        if image.dtype == np.uint8:
            img_float = image.astype(np.float64) / 255.0
        elif image.dtype == np.uint16:
            img_float = image.astype(np.float64) / 65535.0
        else:
            img_float = image.astype(np.float64)
        
        # Travailler en luminance si couleur
        if img_float.ndim == 3:
            # luminance = 0.299R + 0.587G + 0.114B
            lum = 0.299 * img_float[:,:,0] + 0.587 * img_float[:,:,1] + 0.114 * img_float[:,:,2]
        else:
            lum = img_float
        
        H, W = lum.shape
        
        # Découpage en blocs 8×8
        n_h = H // BLOCK_SIZE
        n_w = W // BLOCK_SIZE
        H_effective = n_h * BLOCK_SIZE
        W_effective = n_w * BLOCK_SIZE
        
        blocks = []
        for i in range(n_h):
            for j in range(n_w):
                block = lum[i*BLOCK_SIZE:(i+1)*BLOCK_SIZE, j*BLOCK_SIZE:(j+1)*BLOCK_SIZE]
                blocks.append(block.flatten())
        
        blocks_matrix = np.array(blocks)  # (N_blocks, 64)
        
        # Statistiques
        mean = float(np.mean(blocks_matrix))
        std = float(np.std(blocks_matrix)) + 1e-12
        
        # Centrer-réduire
        centered = (blocks_matrix - mean) / std
        
        # SVD — le cœur de l'entraînement holographique
        try:
            U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        except np.linalg.LinAlgError:
            # Fallback DCT si SVD échoue
            Vt = np.zeros((min(len(blocks), 64), 64))
            for k in range(min(len(blocks), 64)):
                Vt[k] = np.cos((k + 1) * PI * np.arange(64) / 64)
                Vt[k] /= np.linalg.norm(Vt[k]) + 1e-12
            S = np.ones(min(len(blocks), 64))
        
        # Extraire les K premières composantes (l'hologramme)
        K_actual = min(K, Vt.shape[0])
        hologram = Vt[:K_actual, :].copy()
        
        # Normaliser les vecteurs de l'hologramme
        for k in range(K_actual):
            n = np.linalg.norm(hologram[k])
            if n > 1e-12:
                hologram[k] /= n
        
        # Projeter les blocs sur l'hologramme → coefficients
        coeffs = np.dot(centered, hologram.T)  # (N_blocks, K)
        
        # Hash du contenu
        content_hash = hashlib.sha256(lum.tobytes()).hexdigest()[:16]
        
        return HolographicSignature(
            hologram=hologram,
            coefficients=coeffs,
            mean=mean,
            std=std,
            singular_values=S[:K_actual] if len(S) >= K_actual else S,
            source_shape=(H_effective, W_effective),
            K=K_actual,
            content_hash=content_hash,
        )
    
    @staticmethod
    def train_image_rgb(image: np.ndarray, K: int = 8) -> Dict[str, HolographicSignature]:
        """
        Extrait 3 signatures holographiques (R, G, B) d'une image couleur.
        
        Chaque canal est traité indépendamment — même architecture que train_image().
        
        Args:
            image: Array (H, W, 3) en uint8 ou float
            K: Nombre de composantes holographiques par canal
        
        Returns:
            dict avec les 3 HolographicSignature : {'R': ..., 'G': ..., 'B': ...}
        """
        if image.ndim != 3 or image.shape[2] < 3:
            raise ValueError("train_image_rgb nécessite une image (H, W, 3)")
        
        signatures = {}
        for idx, channel in enumerate(['R', 'G', 'B']):
            # Extraire le canal
            channel_data = image[:, :, idx].astype(np.float64)
            if image.dtype == np.uint8:
                channel_data /= 255.0
            elif image.dtype == np.uint16:
                channel_data /= 65535.0
            
            # Même logique SVD que train_image() mais sur un seul canal
            H, W = channel_data.shape
            n_h = H // BLOCK_SIZE
            n_w = W // BLOCK_SIZE
            
            blocks = []
            for i in range(n_h):
                for j in range(n_w):
                    block = channel_data[i*BLOCK_SIZE:(i+1)*BLOCK_SIZE, j*BLOCK_SIZE:(j+1)*BLOCK_SIZE]
                    blocks.append(block.flatten())
            
            blocks_matrix = np.array(blocks)
            mean_c = float(np.mean(blocks_matrix))
            std_c = float(np.std(blocks_matrix)) + 1e-12
            centered = (blocks_matrix - mean_c) / std_c
            
            try:
                U, S, Vt = np.linalg.svd(centered, full_matrices=False)
            except np.linalg.LinAlgError:
                Vt = np.zeros((min(len(blocks), 64), 64))
                for k in range(min(len(blocks), 64)):
                    Vt[k] = np.cos((k+1)*PI*np.arange(64)/64)
                    Vt[k] /= np.linalg.norm(Vt[k]) + 1e-12
                S = np.ones(min(len(blocks), 64))
            
            K_actual = min(K, Vt.shape[0])
            hologram = Vt[:K_actual, :].copy()
            for k in range(K_actual):
                n = np.linalg.norm(hologram[k])
                if n > 1e-12:
                    hologram[k] /= n
            
            coeffs = np.dot(centered, hologram.T)
            
            signatures[channel] = HolographicSignature(
                hologram=hologram,
                coefficients=coeffs,
                mean=mean_c,
                std=std_c,
                singular_values=S[:K_actual] if len(S) >= K_actual else S,
                source_shape=(n_h*BLOCK_SIZE, n_w*BLOCK_SIZE),
                K=K_actual,
                content_hash=hashlib.sha256(channel_data.tobytes()).hexdigest()[:16],
            )
        
        return signatures
    
    @staticmethod
    def train_audio(audio: np.ndarray, sample_rate: int = 44100,
                    segment_ms: float = 50.0, K: int = 8) -> HolographicSignature:
        """
        Extrait la signature holographique d'un signal audio (one-shot).
        
        Découpe l'audio en segments temporels, applique SVD sur les segments.
        """
        segment_samples = int(sample_rate * segment_ms / 1000.0)
        
        # Découpage en segments
        n_segments = len(audio) // segment_samples
        if n_segments < 2:
            # Adapter la taille des segments
            segment_samples = len(audio) // 8
            n_segments = 8
        
        segments = []
        for i in range(n_segments):
            start = i * segment_samples
            end = start + segment_samples
            if end <= len(audio):
                seg = audio[start:end]
                # Spectre simplifié (FFT)
                fft = np.abs(np.fft.rfft(seg))[:BLOCK_DIM]
                if len(fft) < BLOCK_DIM:
                    fft = np.pad(fft, (0, BLOCK_DIM - len(fft)))
                segments.append(fft[:BLOCK_DIM])
        
        segments_matrix = np.array(segments)
        
        mean = float(np.mean(segments_matrix))
        std = float(np.std(segments_matrix)) + 1e-12
        centered = (segments_matrix - mean) / std
        
        # SVD
        try:
            U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        except np.linalg.LinAlgError:
            Vt = np.zeros((min(n_segments, BLOCK_DIM), BLOCK_DIM))
            for k in range(min(n_segments, BLOCK_DIM)):
                Vt[k] = np.sin((k + 1) * PI * np.arange(BLOCK_DIM) / BLOCK_DIM)
                Vt[k] /= np.linalg.norm(Vt[k]) + 1e-12
            S = np.ones(min(n_segments, BLOCK_DIM))
        
        K_actual = min(K, Vt.shape[0])
        hologram = Vt[:K_actual, :].copy()
        for k in range(K_actual):
            n = np.linalg.norm(hologram[k])
            if n > 1e-12:
                hologram[k] /= n
        
        coeffs = np.dot(centered, hologram.T)
        
        return HolographicSignature(
            hologram=hologram,
            coefficients=coeffs,
            mean=mean,
            std=std,
            singular_values=S[:K_actual],
            source_shape=(len(audio),),
            K=K_actual,
        )
    
    @staticmethod
    def train_video(frames: List[np.ndarray], K_spatial: int = 8,
                    K_temporal: int = 4) -> Dict[str, Any]:
        """
        Extrait la signature holographique d'une vidéo (one-shot).
        
        Combine SVD spatial (par frame) + SVD temporel (entre frames).
        """
        if not frames:
            return {}
        
        # 1. SVD spatial sur la première frame (hologramme spatial)
        spatial_sig = HolographicTrainer.train_image(frames[0], K=K_spatial)
        
        # 2. SVD temporel : évolution des coefficients dans le temps
        all_coeffs = []
        for frame in frames:
            sig = HolographicTrainer.train_image(frame, K=K_spatial)
            all_coeffs.append(np.mean(sig.coefficients, axis=0))  # Moyenne par frame
        
        temporal_matrix = np.array(all_coeffs)  # (N_frames, K)
        
        # SVD temporel
        mean_t = float(np.mean(temporal_matrix))
        std_t = float(np.std(temporal_matrix)) + 1e-12
        centered_t = (temporal_matrix - mean_t) / std_t
        
        try:
            Ut, St, Vtt = np.linalg.svd(centered_t, full_matrices=False)
        except np.linalg.LinAlgError:
            St = np.ones(min(len(frames), K_spatial))
            Vtt = np.eye(K_spatial)
        
        K_t = min(K_temporal, Vtt.shape[0])
        temporal_basis = Vtt[:K_t, :].copy()
        
        return {
            'spatial_signature': spatial_sig,
            'temporal_coeffs': centered_t,
            'temporal_basis': temporal_basis,
            'temporal_singular_values': St[:K_t],
            'n_frames': len(frames),
        }


# ==============================================================================
# GÉNÉRATEUR HOLOGRAPHIQUE — Création à partir des signatures
# ==============================================================================

class HolographicGenerator:
    """
    Générateur photoréaliste basé sur les signatures holographiques.
    
    Modes de génération :
      - 'reconstruct' : Reconstruction fidèle (vérification)
      - 'interpolate' : Interpolation entre deux signatures
      - 'extrapolate' : Extrapolation créative (éloignement du centroïde)
      - 'mutate'      : Mutation aléatoire contrôlée des coefficients
      - 'remix'       : Mélange de deux hologrammes (transfert de style)
    """
    
    @staticmethod
    def reconstruct(signature: HolographicSignature,
                    width: int = None, height: int = None) -> np.ndarray:
        """
        Reconstruit l'image à partir de sa signature holographique.
        Vérification : doit être quasi-identique à l'original.
        """
        hologram = signature.hologram
        coeffs = signature.coefficients
        mean = signature.mean
        std = signature.std
        
        H, W = signature.source_shape if len(signature.source_shape) == 2 else (width, height)
        if width and height:
            H, W = height, width
        
        n_h = H // BLOCK_SIZE
        n_w = W // BLOCK_SIZE
        
        # Reconstruction
        reconstructed_blocks = np.dot(coeffs, hologram)  # (N, 64)
        reconstructed_blocks = reconstructed_blocks * std + mean
        
        # Réassemblage
        image = np.zeros((H, W), dtype=np.float64)
        for idx in range(min(len(reconstructed_blocks), n_h * n_w)):
            i = idx // n_w
            j = idx % n_w
            block = reconstructed_blocks[idx].reshape(BLOCK_SIZE, BLOCK_SIZE)
            image[i*BLOCK_SIZE:(i+1)*BLOCK_SIZE, j*BLOCK_SIZE:(j+1)*BLOCK_SIZE] = block
        
        return np.clip(image, 0, 1)
    
    @staticmethod
    def interpolate(sig_a: HolographicSignature, sig_b: HolographicSignature,
                    alpha: float = 0.5, width: int = None, height: int = None) -> np.ndarray:
        """
        Interpole entre deux signatures holographiques.
        
        alpha=0 → image A, alpha=1 → image B, alpha=0.5 → mélange harmonique.
        L'interpolation se fait dans l'espace des coefficients, pas dans l'espace des pixels.
        """
        # Utiliser le plus grand hologramme comme base
        if sig_a.K >= sig_b.K:
            base_sig = sig_a
            other_sig = sig_b
        else:
            base_sig = sig_b
            other_sig = sig_a
            alpha = 1 - alpha
        
        # Nombre minimum de blocs
        n_blocks = min(len(base_sig.coefficients), len(other_sig.coefficients))
        
        # Interpolation des coefficients (pas des pixels !)
        coeffs_a = base_sig.coefficients[:n_blocks]
        coeffs_b = other_sig.coefficients[:n_blocks]
        
        # Adapter la dimension si K différent
        if coeffs_a.shape[1] != coeffs_b.shape[1]:
            min_k = min(coeffs_a.shape[1], coeffs_b.shape[1])
            coeffs_a = coeffs_a[:, :min_k]
            coeffs_b = coeffs_b[:, :min_k]
        
        # Interpolation non-linéaire φ-basée (plus naturelle)
        alpha_phi = 1.0 / (1.0 + np.exp(-(alpha - 0.5) * PHI * 4))
        coeffs_interp = alpha_phi * coeffs_a + (1 - alpha_phi) * coeffs_b
        
        # Créer une signature interpolée
        sig_interp = HolographicSignature(
            hologram=base_sig.hologram[:coeffs_interp.shape[1]],
            coefficients=coeffs_interp,
            mean=alpha * base_sig.mean + (1 - alpha) * other_sig.mean,
            std=alpha * base_sig.std + (1 - alpha) * other_sig.std,
            source_shape=base_sig.source_shape,
            K=coeffs_interp.shape[1],
        )
        
        return HolographicGenerator.reconstruct(sig_interp, width, height)
    
    @staticmethod
    def extrapolate(signature: HolographicSignature,
                    strength: float = 1.5, width: int = None, height: int = None) -> np.ndarray:
        """
        Extrapolation créative : pousse les coefficients au-delà de leur plage naturelle.
        
        strength=1.0 → reconstruction fidèle
        strength=1.5 → légèrement exagéré
        strength=3.0 → très créatif/abstrait
        """
        # Amplifier les coefficients en s'éloignant de la moyenne
        coeffs_mean = np.mean(signature.coefficients, axis=0)
        coeffs_extrapolated = coeffs_mean + (signature.coefficients - coeffs_mean) * strength
        
        # Limiter l'extrapolation (éviter l'explosion)
        max_val = np.max(np.abs(signature.coefficients)) * 3
        coeffs_extrapolated = np.clip(coeffs_extrapolated, -max_val, max_val)
        
        sig_ext = HolographicSignature(
            hologram=signature.hologram,
            coefficients=coeffs_extrapolated,
            mean=signature.mean,
            std=signature.std,
            source_shape=signature.source_shape,
            K=signature.K,
        )
        
        return HolographicGenerator.reconstruct(sig_ext, width, height)
    
    @staticmethod
    def mutate(signature: HolographicSignature,
               mutation_rate: float = 0.1,
               preserve_structure: float = 0.8,
               width: int = None, height: int = None) -> np.ndarray:
        """
        Mutation contrôlée : ajoute du bruit harmonique aux coefficients.
        
        - mutation_rate : intensité de la mutation (0 = identique, 1 = très modifié)
        - preserve_structure : préservation de l'énergie des composantes principales
        """
        np.random.seed(int(time.time() * 1000) % (2**31))
        
        coeffs = signature.coefficients.copy()
        
        # Bruit gaussien pondéré par l'énergie des valeurs singulières
        energy = signature.energy_spectrum()
        
        for k in range(signature.K):
            noise = np.random.randn(len(coeffs)) * mutation_rate * 0.3
            # Préserver les composantes principales (forte énergie)
            preservation = preserve_structure * energy[k] * 5
            coeffs[:, k] = coeffs[:, k] * preservation + noise * (1 - preservation)
        
        sig_mutated = HolographicSignature(
            hologram=signature.hologram,
            coefficients=coeffs,
            mean=signature.mean,
            std=signature.std,
            source_shape=signature.source_shape,
            K=signature.K,
        )
        
        return HolographicGenerator.reconstruct(sig_mutated, width, height)
    
    @staticmethod
    def remix_style(content_sig: HolographicSignature,
                    style_sig: HolographicSignature,
                    style_strength: float = 0.5,
                    width: int = None, height: int = None) -> np.ndarray:
        """
        Transfert de style harmonique : applique l'hologramme du style
        au contenu de l'image source.
        
        Méthode : remplacer les composantes de basse énergie du contenu
        par celles du style (transfert spectral).
        """
        # L'hologramme du style gouverne la "texture"
        # Les coefficients du contenu gouvernent la "structure"
        
        n_blocks = min(len(content_sig.coefficients), 64)
        
        # Hybridation des hologrammes
        # - Hautes composantes (K/2 premières) : contenu (structure)
        # - Basses composantes (K/2 dernières) : style (texture)
        K_content = max(1, content_sig.K // 2)
        K_style = style_sig.K
        
        hybrid_hologram = np.zeros((K_content + K_style, BLOCK_DIM), dtype=np.float64)
        
        # Composantes de contenu (préservées)
        for k in range(min(K_content, content_sig.hologram.shape[0])):
            hybrid_hologram[k] = content_sig.hologram[k]
        
        # Composantes de style (transférées)
        for k in range(min(K_style, style_sig.hologram.shape[0])):
            hybrid_hologram[K_content + k] = style_sig.hologram[k]
        
        # Normaliser l'hologramme hybride
        for k in range(hybrid_hologram.shape[0]):
            n = np.linalg.norm(hybrid_hologram[k])
            if n > 1e-12:
                hybrid_hologram[k] /= n
        
        # Projeter le contenu sur l'hologramme hybride
        content_centered = (content_sig.coefficients[:n_blocks, :content_sig.K] @ content_sig.hologram[:content_sig.K])
        content_blocks = content_centered * content_sig.std + content_sig.mean
        content_blocks_centered = (content_blocks - content_sig.mean) / content_sig.std
        
        hybrid_coeffs = np.dot(content_blocks_centered, hybrid_hologram.T)
        
        sig_hybrid = HolographicSignature(
            hologram=hybrid_hologram,
            coefficients=hybrid_coeffs,
            mean=content_sig.mean,
            std=content_sig.std,
            source_shape=content_sig.source_shape,
            K=hybrid_hologram.shape[0],
        )
        
        result = HolographicGenerator.reconstruct(sig_hybrid, width, height)
        
        # Mixer avec l'original selon la force du style
        if style_strength < 1.0:
            original = HolographicGenerator.reconstruct(content_sig, width, height)
            result = original * (1 - style_strength) + result * style_strength
        
        return np.clip(result, 0, 1)
    
    @staticmethod
    def generate_variations(signature: HolographicSignature,
                            n_variations: int = 7,
                            variation_strength: float = 0.3,
                            width: int = None, height: int = None) -> List[np.ndarray]:
        """
        Génère N variations d'une même signature holographique.
        
        Chaque variation est une mutation différente basée sur les harmoniques Hₙ.
        """
        variations = []
        
        for n in range(n_variations):
            h = H_CONSTANTS[min(n, 6)]
            # Chaque variation utilise un taux de mutation différent basé sur Hₙ
            rate = variation_strength * h / PHI
            preserve = 0.5 + 0.5 * (1.0 / h) if h > 0 else 0.8
            
            np.random.seed(42 + n * 137)
            mutated = HolographicGenerator.mutate(
                signature,
                mutation_rate=rate,
                preserve_structure=preserve,
                width=width, height=height
            )
            variations.append(mutated)
        
        return variations
    
    @staticmethod
    def super_resolve(signature: HolographicSignature,
                      scale_factor: int = 2) -> HolographicSignature:
        """
        Super-résolution holographique : crée une signature à plus haute résolution
        en extrapolant l'hologramme dans l'espace spectral.
        """
        # Upsampling spectral : ajouter des hautes fréquences harmoniques
        K_high = signature.K * scale_factor
        
        highres_hologram = np.zeros((K_high, BLOCK_DIM), dtype=np.float64)
        
        # Copier les composantes existantes
        highres_hologram[:signature.K] = signature.hologram
        
        # Générer les nouvelles composantes par modulation harmonique
        for k in range(signature.K, K_high):
            base_idx = k % signature.K
            # Modulation par les constantes harmoniques
            modulation = np.sin(np.arange(BLOCK_DIM) * H_CONSTANTS[k % 7] * PI / BLOCK_DIM)
            highres_hologram[k] = signature.hologram[base_idx] * modulation
            n = np.linalg.norm(highres_hologram[k])
            if n > 1e-12:
                highres_hologram[k] /= n
        
        # Projeter sur le nouvel hologramme (approximation)
        centered = (np.dot(signature.coefficients, signature.hologram))
        highres_coeffs = np.dot(centered, highres_hologram.T)
        
        return HolographicSignature(
            hologram=highres_hologram,
            coefficients=highres_coeffs,
            mean=signature.mean,
            std=signature.std,
            source_shape=(signature.source_shape[0] * scale_factor,
                         signature.source_shape[1] * scale_factor if len(signature.source_shape) > 1 else 0),
            K=K_high,
        )


# ==============================================================================
# UTILITAIRES DE SAUVEGARDE
# ==============================================================================

def array_to_image(arr: np.ndarray, colormap: str = 'grey') -> np.ndarray:
    """Convertit un array float [0,1] en image RGB uint8."""
    arr_clipped = np.clip(arr, 0, 1)
    
    if colormap == 'grey':
        grey = (arr_clipped * 255).astype(np.uint8)
        return np.stack([grey, grey, grey], axis=-1)
    elif colormap == 'cosmic':
        # Appliquer la palette cosmique
        from harmonic_generator_core import HarmonicColorMapper
        arr_norm = arr_clipped * 2 - 1  # [-1, 1]
        return HarmonicColorMapper.harmonic_hsl(arr_norm, palette='cosmique')
    else:
        grey = (arr_clipped * 255).astype(np.uint8)
        return np.stack([grey, grey, grey], axis=-1)


def save_holographic_image(arr: np.ndarray, filepath: str, colormap: str = 'grey'):
    """Sauvegarde une image holographique."""
    rgb = array_to_image(arr, colormap)
    img = Image.fromarray(rgb, 'RGB')
    img.save(filepath)
    return filepath


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================

def demo_one_shot():
    """Démonstration du générateur one-shot."""
    print("=" * 70)
    print("  ENTRAÎNEMENT ONE-SHOT HOLOGRAPHIQUE")
    print("  Modele Harmonic AI / KA PHONE — Generation Photorealiste")
    print("=" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'one_shot')
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Créer une image source réaliste (simulation photo)
    print("\n  [1] Création image source simulée (512×512)...")
    from harmonic_generator_core import HarmonicField
    from harmonic_image_generator import save_as_png
    
    # Générer une image de base avec détails haute fréquence
    field = HarmonicField(width=512, height=512, seed=12345)
    psi = field.get_psi_total()
    
    # Simuler une photo : ajouter des détails photoréalistes
    # Combiner le champ harmonique avec des structures géométriques
    H, W = psi.shape
    x = np.linspace(-1, 1, W)
    y = np.linspace(-1, 1, H)
    X_norm, Y_norm = np.meshgrid(x, y)
    R = np.sqrt(X_norm**2 + Y_norm**2)
    
    # Simuler un paysage : ciel en haut, sol en bas
    photo_sim = np.zeros_like(psi)
    photo_sim += psi * 0.5  # Base harmonique
    
    # Ciel texturé (haut)
    sky_mask = Y_norm < 0.1
    photo_sim[sky_mask] += 0.3 * np.sin(X_norm[sky_mask] * 15) * np.cos(X_norm[sky_mask] * 7)
    
    # Montagnes (milieu)
    mountain_mask = (Y_norm >= 0.1) & (Y_norm < 0.4)
    mountain_noise = np.sin(X_norm * 8 + np.sin(X_norm * 3) * 2)
    photo_sim[mountain_mask] += mountain_noise[mountain_mask] * 0.4
    
    # Sol texturé (bas)
    ground_mask = Y_norm >= 0.4
    photo_sim[ground_mask] += np.sin(X_norm[ground_mask] * 20) * 0.2
    
    photo_sim = np.clip(photo_sim, -1, 1)
    
    # Sauvegarder l'image source
    from harmonic_generator_core import HarmonicColorMapper
    rgb_source = HarmonicColorMapper.harmonic_hsl(photo_sim, palette='forest')
    source_path = os.path.join(output_dir, '01_source.png')
    save_as_png(rgb_source, source_path)
    print(f"    ✓ Source : {source_path}")
    
    # 2. Entraînement One-Shot
    print("\n  [2] Entraînement One-Shot (extraction hologramme SVD)...")
    # Convertir en [0,1] pour l'entraînement
    img_for_training = (photo_sim + 1) / 2  # [-1,1] → [0,1]
    
    t0 = time.time()
    signature = HolographicTrainer.train_image(img_for_training, K=16)
    train_time = (time.time() - t0) * 1000
    
    print(f"    ✓ Entraîné en {train_time:.1f}ms")
    print(f"    Hologramme : {signature.hologram.shape}")
    print(f"    Coefficients : {signature.coefficients.shape}")
    print(f"    Énergie capturée (K=4) : {signature.coherence_score():.1%}")
    print(f"    Énergie capturée (K=8) : {sum(signature.energy_spectrum()[:8]):.1%}")
    
    # 3. Reconstruction fidèle
    print("\n  [3] Vérification : reconstruction fidèle...")
    reconstructed = HolographicGenerator.reconstruct(signature, width=512, height=512)
    mse = np.mean((img_for_training - reconstructed)**2)
    psnr = 10 * math.log10(1.0 / (mse + 1e-12))
    
    rec_rgb = array_to_image(reconstructed, colormap='cosmic')
    rec_path = os.path.join(output_dir, '02_reconstruction.png')
    save_as_png(rec_rgb, rec_path)
    print(f"    ✓ Reconstruction : {rec_path}")
    print(f"    MSE : {mse:.6f} | PSNR : {psnr:.1f} dB")
    
    # 4. Variations (7 mutations)
    print("\n  [4] Génération de 7 variations (mutations harmoniques)...")
    variations = HolographicGenerator.generate_variations(
        signature, n_variations=7, variation_strength=0.3, width=512, height=512
    )
    
    for i, var in enumerate(variations):
        var_rgb = array_to_image(var, colormap='cosmic')
        var_path = os.path.join(output_dir, f'03_variation_{i+1}.png')
        save_as_png(var_rgb, var_path)
        var_mse = np.mean((img_for_training - var)**2)
        print(f"    ✓ Variation {i+1} : {var_path} (MSE: {var_mse:.4f})")
    
    # 5. Extrapolation créative
    print("\n  [5] Extrapolation créative (strength=2.0)...")
    extrapolated = HolographicGenerator.extrapolate(
        signature, strength=2.0, width=512, height=512
    )
    ext_rgb = array_to_image(extrapolated, colormap='cosmic')
    ext_path = os.path.join(output_dir, '04_extrapolated.png')
    save_as_png(ext_rgb, ext_path)
    print(f"    ✓ Extrapolé : {ext_path}")
    
    # 6. Interpolation entre deux seeds
    print("\n  [6] Interpolation entre deux signatures...")
    field2 = HarmonicField(width=512, height=512, seed=99999)
    psi2 = field2.get_psi_total()
    img2 = (psi2 + 1) / 2
    sig2 = HolographicTrainer.train_image(img2, K=16)
    
    for alpha in [0.25, 0.5, 0.75]:
        interp = HolographicGenerator.interpolate(
            signature, sig2, alpha=alpha, width=512, height=512
        )
        interp_rgb = array_to_image(interp, colormap='cosmic')
        interp_path = os.path.join(output_dir, f'05_interp_{int(alpha*100):02d}.png')
        save_as_png(interp_rgb, interp_path)
        print(f"    ✓ Interpolation α={alpha:.2f} : {interp_path}")
    
    print(f"\n{'='*70}")
    print("  RAPPORT ONE-SHOT HOLOGRAPHIQUE")
    print(f"{'='*70}")
    print(f"\n  Fichiers générés dans : {output_dir}")
    print(f"  Temps d'entraînement   : {train_time:.1f}ms (1 seule image)")
    print(f"  PSNR reconstruction    : {psnr:.1f} dB")
    print(f"  Taille hologramme      : {signature.hologram.nbytes} octets")
    print(f"  Taille coefficients    : {signature.coefficients.nbytes} octets")
    print(f"  Total signature       : {signature.hologram.nbytes + signature.coefficients.nbytes} octets")
    print(f"\n  ✅ Générateur one-shot photoréaliste opérationnel.")


def demo_one_shot_from_file(image_path: str, output_dir: str = None):
    """Démo avec une vraie image."""
    print("=" * 70)
    print("  ONE-SHOT HOLOGRAPHIQUE — Image Réelle")
    print("=" * 70)
    
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'one_shot_real')
    os.makedirs(output_dir, exist_ok=True)
    
    # Charger l'image
    img = Image.open(image_path).convert('L')  # Convertir en niveaux de gris
    img_array = np.array(img, dtype=np.float64) / 255.0
    
    print(f"\n  Image source : {image_path}")
    print(f"  Dimensions : {img_array.shape}")
    
    # Entraînement
    print(f"\n  Entraînement One-Shot...")
    t0 = time.time()
    signature = HolographicTrainer.train_image(img_array, K=16)
    train_time = (time.time() - t0) * 1000
    
    print(f"  ✓ Entraîné en {train_time:.1f}ms")
    print(f"  Énergie K=4 : {signature.coherence_score():.1%}")
    
    # Reconstruction
    reconstructed = HolographicGenerator.reconstruct(signature)
    mse = np.mean((img_array[:reconstructed.shape[0], :reconstructed.shape[1]] - reconstructed)**2)
    psnr = 10 * math.log10(1.0 / (mse + 1e-12))
    
    rec_path = os.path.join(output_dir, 'reconstruction.png')
    save_holographic_image(reconstructed, rec_path)
    print(f"  ✓ Reconstruction PSNR: {psnr:.1f} dB → {rec_path}")
    
    # Variations
    print(f"\n  Génération de variations...")
    variations = HolographicGenerator.generate_variations(signature, n_variations=5, variation_strength=0.25)
    for i, var in enumerate(variations):
        var_path = os.path.join(output_dir, f'variation_{i+1}.png')
        save_holographic_image(var, var_path)
        print(f"  ✓ Variation {i+1} → {var_path}")
    
    print(f"\n  ✅ Tous les fichiers dans : {output_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Générateur One-Shot Holographique')
    parser.add_argument('--demo', action='store_true', help='Démo avec image synthétique')
    parser.add_argument('--image', type=str, default=None, help='Chemin vers une image réelle')
    parser.add_argument('--output', type=str, default=None, help='Dossier de sortie')
    args = parser.parse_args()
    
    if args.image:
        demo_one_shot_from_file(args.image, args.output)
    else:
        demo_one_shot()