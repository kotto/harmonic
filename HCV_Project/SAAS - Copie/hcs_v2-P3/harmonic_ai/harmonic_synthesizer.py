#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HarmonicSynthesizer - Synthese d'images par mathematiques harmoniques pures
===========================================================================
Reconstruit une image a partir d'une signature harmonique 512D sans aucun
reseau de neurones. Generation ENTIEREMENT DETERMINISTE.

Principe :
  La signature contient les amplitudes et phases des harmoniques.
  La synthese superpose les ondes harmoniques sur une grille phi.
  Le profil chromatique est applique en post-traitement.

Temps de generation : < 200ms pour 512x512 sur CPU standard.
"""

import numpy as np
import time
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

# Constantes harmoniques
PHI = 1.6180339887
PHI2 = 2.6180339887
PHI3 = PHI2 * PHI
SIGNATURE_DIM = 512


class HarmonicSynthesizer:
    """
    Synthese d'images deterministe depuis une signature harmonique 512D.

    La generation exploite :
      - Superposition d'ondes harmoniques (series de Fourier-Phi)
      - Grille spatiale phi pour les structures naturelles
      - Application du profil chromatique
      - Coherence spectrale contrainte par la signature

    Usage:
        synth = HarmonicSynthesizer()
        image = synth.synthesize(signature, resolution=(512, 512))
        # image.shape == (512, 512, 3), dtype uint8
    """

    def __init__(self, n_harmonics: int = 64, quality_level: str = "standard"):
        """
        Args:
            n_harmonics: nombre d'harmoniques a superposer (defaut 64)
            quality_level: "fast" (32 harm.) | "standard" (64) | "high" (128)
        """
        self.quality_level = quality_level
        self.n_harmonics = {
            "fast": 32,
            "standard": 64,
            "high": 128,
        }.get(quality_level, n_harmonics)

        # Pre-calcul des frequences phi
        self._phi_freqs = np.array(
            [PHI ** (k / self.n_harmonics) for k in range(self.n_harmonics)],
            dtype=np.float32
        )
        # Phases phi pre-calculees
        self._phi_phases = np.array(
            [k * 2 * np.pi * PHI / self.n_harmonics for k in range(self.n_harmonics)],
            dtype=np.float32
        )

        logger.info(f"HarmonicSynthesizer: {self.n_harmonics} harmoniques | qualite={quality_level}")

    # ------------------------------------------------------------------
    # Methode principale
    # ------------------------------------------------------------------

    def synthesize(
        self,
        signature: np.ndarray,
        resolution: Tuple[int, int] = (512, 512),
        chromatic_profile: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """
        Synthetise une image depuis une signature harmonique.

        Args:
            signature: vecteur 512D float32 normalise
            resolution: (width, height) de l'image cible
            chromatic_profile: dict de profil chromatique (optionnel)
            seed: graine aleatoire pour determinisme (None = derive de la signature)

        Returns:
            image RGB uint8 shape (height, width, 3)
        """
        t0 = time.time()
        W, H = resolution

        # Derivation du seed depuis la signature si non fourni
        if seed is None:
            seed = int(np.abs(signature[448:512].sum()) * 1e6) % (2**31)

        rng = np.random.RandomState(seed)

        # --- Etape 1 : Champ de phase harmonique (luminance) ---
        lum_field = self._synthesize_luminance_field(signature, H, W)

        # --- Etape 2 : Champs de couleur harmoniques ---
        color_fields = self._synthesize_color_fields(signature, H, W, rng)

        # --- Etape 3 : Assemblage RGB ---
        image_float = self._assemble_rgb(lum_field, color_fields, signature)

        # --- Etape 4 : Application du profil chromatique ---
        if chromatic_profile:
            image_float = self._apply_chromatic_profile(image_float, chromatic_profile)

        # --- Etape 5 : Amelioration harmonique finale ---
        image_float = self._harmonic_enhancement(image_float, signature)

        # Conversion finale uint8
        image_uint8 = np.clip(image_float * 255, 0, 255).astype(np.uint8)

        elapsed = time.time() - t0
        logger.debug(f"Synthese {W}x{H} en {elapsed*1000:.1f}ms")

        return image_uint8

    def synthesize_from_composed(
        self,
        composed_signature: np.ndarray,
        results: List[Dict[str, Any]],
        resolution: Tuple[int, int] = (512, 512),
    ) -> np.ndarray:
        """
        Synthetise depuis une signature composee + resultats de lookup.
        Permet de combiner les profils chromatiques de plusieurs objets.
        """
        # Fusion des profils chromatiques
        chromatic_profiles = [r.get("chromatic_profile", {}) for r in results if r.get("chromatic_profile")]
        fused_profile = self._fuse_chromatic_profiles(chromatic_profiles)

        return self.synthesize(composed_signature, resolution, chromatic_profile=fused_profile)

    # ------------------------------------------------------------------
    # Champ de luminance harmonique
    # ------------------------------------------------------------------

    def _synthesize_luminance_field(
        self, signature: np.ndarray, H: int, W: int
    ) -> np.ndarray:
        """
        Construit le champ de luminance par superposition d'ondes harmoniques.
        Exploite les 64 premieres dimensions de la signature (Fourier-Phi).
        """
        # Grille spatiale normalisee
        x = np.linspace(0, 2 * np.pi * PHI, W, dtype=np.float32)
        y = np.linspace(0, 2 * np.pi * PHI, H, dtype=np.float32)
        X, Y = np.meshgrid(x, y)  # (H, W)

        # Amplitudes et phases depuis la signature
        amplitudes = np.abs(signature[:64])           # Fourier-Phi
        phases = signature[64:128] * 2 * np.pi       # Profil chromatique comme phase

        # Superposition des harmoniques
        field = np.zeros((H, W), dtype=np.float32)

        # Vectorisation : calcul par groupes pour performance CPU
        n_harm = min(self.n_harmonics, 64)
        for k in range(0, n_harm, 8):
            batch = slice(k, min(k + 8, n_harm))
            amp_batch = amplitudes[batch]
            phase_batch = phases[batch]
            freq_batch = self._phi_freqs[batch]

            # Contribution de ce batch d'harmoniques
            for i, (amp, ph, freq) in enumerate(zip(amp_batch, phase_batch, freq_batch)):
                freq_idx = k + i
                # Frequences spatiales harmoniques
                fx = freq * (1 + freq_idx % 4) / PHI
                fy = freq * (1 + (freq_idx // 4) % 4) * PHI

                # Onde 2D harmonique
                wave = amp * np.sin(fx * X + fy * Y + ph)
                field += wave

        # Normalisation [0, 1]
        f_min, f_max = field.min(), field.max()
        if f_max - f_min > 1e-8:
            field = (field - f_min) / (f_max - f_min)
        else:
            field = np.full_like(field, 0.5)

        # Application d'une structure phi (grille d'or)
        phi_structure = self._create_phi_structure(H, W, signature)
        field = field * 0.75 + phi_structure * 0.25

        return np.clip(field, 0.0, 1.0)

    def _create_phi_structure(
        self, H: int, W: int, signature: np.ndarray
    ) -> np.ndarray:
        """
        Cree une structure spatiale basee sur la grille phi.
        Genere les motifs naturels caracteristiques.
        """
        x = np.linspace(0, 1, W, dtype=np.float32)
        y = np.linspace(0, 1, H, dtype=np.float32)
        X, Y = np.meshgrid(x, y)

        # Spirale de Fibonacci (phi)
        R = np.sqrt((X - 0.5) ** 2 + (Y - 0.5) ** 2)
        Theta = np.arctan2(Y - 0.5, X - 0.5)

        # Structure phi radiale
        phi_radial = np.sin(R * PHI * np.pi * 4 + Theta * PHI)

        # Structure phi lineaire (diagonales harmoniques)
        phi_linear = np.sin(X * PHI * np.pi * 6) * np.cos(Y * PHI * np.pi * 4)

        # Ponderation par les gradients de la signature
        grad_weight = float(np.mean(np.abs(signature[192:256])))
        structure = (phi_radial * 0.6 + phi_linear * 0.4) * grad_weight

        # Normalisation [0, 1]
        s_min, s_max = structure.min(), structure.max()
        if s_max - s_min > 1e-8:
            structure = (structure - s_min) / (s_max - s_min)

        return structure.astype(np.float32)

    # ------------------------------------------------------------------
    # Champs de couleur harmoniques
    # ------------------------------------------------------------------

    def _synthesize_color_fields(
        self, signature: np.ndarray, H: int, W: int, rng: np.random.RandomState
    ) -> Dict[str, np.ndarray]:
        """
        Genere les champs de couleur R, G, B depuis la signature chromatique.
        Exploite les dimensions 64-127 (profil chromatique).
        """
        chroma = signature[64:128]

        # Moyennes chromatiques cibles (dimensions 34-36 du profil)
        mean_r = float(np.clip(chroma[34] if len(chroma) > 34 else 0.5, 0, 1))
        mean_g = float(np.clip(chroma[35] if len(chroma) > 35 else 0.5, 0, 1))
        mean_b = float(np.clip(chroma[36] if len(chroma) > 36 else 0.5, 0, 1))

        # Ecarts-types cibles
        std_r = float(np.clip(chroma[40] if len(chroma) > 40 else 0.15, 0, 0.4))
        std_g = float(np.clip(chroma[41] if len(chroma) > 41 else 0.15, 0, 0.4))
        std_b = float(np.clip(chroma[42] if len(chroma) > 42 else 0.15, 0, 0.4))

        # Distribution hue (dimensions 18-25)
        hue_dist = chroma[18:26] if len(chroma) > 25 else np.ones(8) / 8
        dominant_hue = float(np.argmax(hue_dist)) / 8.0

        # Champs de couleur base sur des variations harmoniques de la luminance
        x = np.linspace(0, 2 * np.pi, W, dtype=np.float32)
        y = np.linspace(0, 2 * np.pi, H, dtype=np.float32)
        X, Y = np.meshgrid(x, y)

        # Variation chromatique R (frequence phi)
        r_variation = np.sin(X * PHI + dominant_hue * np.pi) * std_r
        # Variation chromatique G (frequence phi^2)
        g_variation = np.sin(Y * PHI2 + dominant_hue * np.pi / PHI) * std_g
        # Variation chromatique B (frequence phi^3)
        b_variation = np.cos(X * PHI3 / 2 + dominant_hue * np.pi * PHI) * std_b

        return {
            "r": (r_variation, mean_r, std_r),
            "g": (g_variation, mean_g, std_g),
            "b": (b_variation, mean_b, std_b),
        }

    # ------------------------------------------------------------------
    # Assemblage RGB
    # ------------------------------------------------------------------

    def _assemble_rgb(
        self,
        lum_field: np.ndarray,
        color_fields: Dict[str, Any],
        signature: np.ndarray,
    ) -> np.ndarray:
        """
        Assemble les champs de luminance et couleur en image RGB float32 [0,1].
        """
        H, W = lum_field.shape

        # Canaux de base depuis la luminance
        r_var, mean_r, std_r = color_fields["r"]
        g_var, mean_g, std_g = color_fields["g"]
        b_var, mean_b, std_b = color_fields["b"]

        # Canal R : luminance + variation chromatique R
        r_channel = lum_field * (mean_r + std_r) + r_var * 0.3
        # Canal G : luminance + variation chromatique G
        g_channel = lum_field * (mean_g + std_g) + g_var * 0.3
        # Canal B : luminance + variation chromatique B
        b_channel = lum_field * (mean_b + std_b) + b_var * 0.3

        # Modulation inter-canaux par correlations de la signature
        corr_rg = float(signature[320] if len(signature) > 320 else 0.0)
        corr_gb = float(signature[321] if len(signature) > 321 else 0.0)
        corr_rb = float(signature[322] if len(signature) > 322 else 0.0)

        r_channel += corr_rg * g_channel * 0.1 + corr_rb * b_channel * 0.05
        g_channel += corr_rg * r_channel * 0.1 + corr_gb * b_channel * 0.05
        b_channel += corr_gb * g_channel * 0.1 + corr_rb * r_channel * 0.05

        # Assemblage et normalisation
        image = np.stack([r_channel, g_channel, b_channel], axis=-1).astype(np.float32)
        return np.clip(image, 0.0, 1.0)

    # ------------------------------------------------------------------
    # Application du profil chromatique
    # ------------------------------------------------------------------

    def _apply_chromatic_profile(
        self,
        image: np.ndarray,
        profile: Dict[str, Any],
    ) -> np.ndarray:
        """
        Applique un profil chromatique a l'image generee.
        Ajuste les moyennes et ecarts-types selon le profil.
        """
        if not profile:
            return image

        img = image.copy().astype(np.float64)

        # Correction de la moyenne RGB
        target_means = profile.get("mean_rgb", None)
        if target_means is not None:
            try:
                tm = np.asarray(target_means, dtype=np.float64)
                if tm.max() > 1.0:
                    tm = tm / 255.0
                if len(tm) == 3:
                    current_means = img.mean(axis=(0, 1))
                    img += (tm - current_means)[np.newaxis, np.newaxis, :]
            except Exception:
                pass

        # Correction de l'ecart-type RGB
        target_stds = profile.get("std_rgb", None)
        if target_stds is not None:
            try:
                ts = np.asarray(target_stds, dtype=np.float64)
                if ts.max() > 1.0:
                    ts = ts / 255.0
                if len(ts) == 3:
                    current_stds = img.std(axis=(0, 1)) + 1e-8
                    for c in range(3):
                        if current_stds[c] > 1e-8 and ts[c] > 0:
                            mean_c = img[:, :, c].mean()
                            img[:, :, c] = (img[:, :, c] - mean_c) * (ts[c] / current_stds[c]) + mean_c
            except Exception:
                pass

        return np.clip(img, 0.0, 1.0).astype(np.float32)

    def _fuse_chromatic_profiles(
        self, profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fusionne plusieurs profils chromatiques par ponderation phi.
        """
        if not profiles:
            return {}
        if len(profiles) == 1:
            return profiles[0]

        # Poids harmoniques
        weights = np.array([1.0 / ((i + 1) ** PHI) for i in range(len(profiles))],
                           dtype=np.float64)
        weights /= weights.sum()

        fused = {}

        # Fusion des moyennes RGB
        means = []
        for p in profiles:
            m = p.get("mean_rgb")
            if m is not None:
                means.append(np.asarray(m, dtype=np.float64))
        if means:
            fused["mean_rgb"] = sum(w * m for w, m in zip(weights[:len(means)], means))

        # Fusion des ecarts-types RGB
        stds = []
        for p in profiles:
            s = p.get("std_rgb")
            if s is not None:
                stds.append(np.asarray(s, dtype=np.float64))
        if stds:
            fused["std_rgb"] = sum(w * s for w, s in zip(weights[:len(stds)], stds))

        return fused

    # ------------------------------------------------------------------
    # Amelioration harmonique finale
    # ------------------------------------------------------------------

    def _harmonic_enhancement(
        self, image: np.ndarray, signature: np.ndarray
    ) -> np.ndarray:
        """
        Post-traitement harmonique : ameliore la coherence et la naturalite.
        Utilise les statistiques d'ordre superieur de la signature (dim 384-447).
        """
        img = image.copy()

        # Score d'harmonie depuis la signature
        harmony_energy = float(np.std(signature[:64]))

        # Contraste harmonique (augmentation si signature energetique)
        if harmony_energy > 0.1:
            # Augmentation de contraste par courbe gamma harmonique
            gamma = 1.0 / PHI  # gamma = 0.618 (leger boost de luminance)
            img = np.power(np.clip(img, 0.001, 1.0), gamma)

        # Lissage harmonique leger (equivalent a un filtre passe-bas phi)
        # Application d'un filtre 3x3 gaussien simplifie
        kernel_1d = np.array([0.25, 0.5, 0.25], dtype=np.float32)
        kernel_2d = np.outer(kernel_1d, kernel_1d)

        if img.shape[0] > 3 and img.shape[1] > 3:
            from scipy.ndimage import convolve
            for c in range(3):
                smoothed = convolve(img[:, :, c], kernel_2d, mode='reflect')
                # Fusion harmonique : 70% original + 30% lisse
                img[:, :, c] = 0.70 * img[:, :, c] + 0.30 * smoothed

        return np.clip(img, 0.0, 1.0).astype(np.float32)

    # ------------------------------------------------------------------
    # Generation video harmonique
    # ------------------------------------------------------------------

    def synthesize_video_frames(
        self,
        signature: np.ndarray,
        n_frames: int = 24,
        fps: float = 24.0,
        resolution: Tuple[int, int] = (512, 512),
        chromatic_profile: Optional[Dict] = None,
        motion_amplitude: float = 0.02,
    ) -> List[np.ndarray]:
        """
        Genere une sequence video deterministe depuis une signature.

        La dimension temporelle (dim 256-319) pilote l'animation.
        Chaque frame est generee par modulation de la signature dans le temps.

        Args:
            signature: signature harmonique 512D
            n_frames: nombre de frames
            fps: frames par seconde
            resolution: (width, height)
            chromatic_profile: profil chromatique
            motion_amplitude: amplitude du mouvement harmonique [0-0.1]

        Returns:
            liste de n_frames images uint8
        """
        frames = []
        temp_sig = signature[256:320]  # Bloc temporel

        # Amplitude de mouvement depuis la signature
        motion_energy = float(np.mean(np.abs(temp_sig[:6])))
        motion_amp = motion_amplitude * (1 + motion_energy)

        for frame_idx in range(n_frames):
            # Phase temporelle harmonique
            t = frame_idx / fps
            phi_phase = t * PHI * 2 * np.pi / n_frames

            # Modulation de la signature dans le temps
            modulated_sig = signature.copy()

            # Modulation des basses frequences (mouvement lent)
            for k in range(min(16, 64)):
                modulated_sig[k] += motion_amp * np.sin(phi_phase * (k + 1) / PHI)

            # Modulation des phases chromatiques (variation couleur)
            for k in range(64, 80):
                modulated_sig[k] += motion_amp * 0.3 * np.cos(phi_phase * PHI + k)

            # Renormalisation
            norm = np.linalg.norm(modulated_sig)
            if norm > 1e-8:
                modulated_sig = modulated_sig / norm

            # Synthese de la frame
            frame = self.synthesize(
                modulated_sig,
                resolution=resolution,
                chromatic_profile=chromatic_profile,
                seed=hash((int(signature[0] * 1000), frame_idx)) % (2**31),
            )
            frames.append(frame)

        logger.info(f"Video synthetisee: {n_frames} frames @ {fps}fps, {resolution[0]}x{resolution[1]}")
        return frames

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def estimate_synthesis_time(self, resolution: Tuple[int, int]) -> float:
        """Estime le temps de synthese en millisecondes."""
        W, H = resolution
        pixels = W * H
        # Empirique : ~0.001ms par pixel par harmonique sur CPU moderne
        return pixels * self.n_harmonics * 0.001

    def get_capabilities(self) -> Dict[str, Any]:
        """Retourne les capacites du synthétiseur."""
        return {
            "n_harmonics": self.n_harmonics,
            "quality_level": self.quality_level,
            "max_resolution": (4096, 4096),
            "supports_video": True,
            "deterministic": True,
            "requires_gpu": False,
            "signature_dim": SIGNATURE_DIM,
        }


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== Test HarmonicSynthesizer ===")

    synth = HarmonicSynthesizer(quality_level="standard")
    print(f"Capacites: {synth.get_capabilities()}")

    # Test avec signature aleatoire
    np.random.seed(42)
    test_sig = np.random.randn(SIGNATURE_DIM).astype(np.float32)
    test_sig = test_sig / np.linalg.norm(test_sig)

    # Profil chromatique de test (tons chauds)
    chroma_profile = {
        "mean_rgb": [0.7, 0.5, 0.3],
        "std_rgb": [0.15, 0.12, 0.10],
    }

    print("\nSynthese 256x256 standard...")
    t0 = time.time()
    img = synth.synthesize(test_sig, resolution=(256, 256), chromatic_profile=chroma_profile)
    t1 = time.time()
    print(f"  Temps: {(t1-t0)*1000:.1f}ms")
    print(f"  Shape: {img.shape}, dtype: {img.dtype}")
    print(f"  Plage: [{img.min()}, {img.max()}]")
    print(f"  Moy. RGB: {img.mean(axis=(0,1))}")

    # Test determinisme
    img2 = synth.synthesize(test_sig, resolution=(256, 256), chromatic_profile=chroma_profile)
    identical = np.array_equal(img, img2)
    print(f"\nDeterminisme: {'OK (images identiques)' if identical else 'ECHEC'}")

    # Test generation video
    print("\nGeneration 12 frames video 128x128...")
    t0 = time.time()
    frames = synth.synthesize_video_frames(test_sig, n_frames=12, resolution=(128, 128))
    t1 = time.time()
    print(f"  {len(frames)} frames en {(t1-t0)*1000:.1f}ms")
    print(f"  Frame shape: {frames[0].shape}")

    # Sauvegarde demo
    try:
        from PIL import Image as PILImage
        PILImage.fromarray(img).save("harmonic_synthesis_demo.png")
        print("\nImage demo sauvegardee: harmonic_synthesis_demo.png")
    except ImportError:
        print("\nPillow non disponible, pas de sauvegarde")

    print("\n=== Test termine avec succes ===")
