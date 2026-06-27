#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HarmonicSignatureExtractor - Extraction de la signature harmonique 512D
=======================================================================
Transforme une image (numpy array) en vecteur harmonique 512D qui encode :

  Dim   0- 63 : Frequences de Fourier-Phi (decomposition harmonique)
  Dim  64-127 : Profil chromatique YCbCr + HSV normalise phi
  Dim 128-191 : Coefficients DCT harmoniques 8x8 (texture)
  Dim 192-255 : Gradients spatiaux phi (structure et bords)
  Dim 256-319 : Signature temporelle (pour video, zero pour image)
  Dim 320-383 : Relations spectrales inter-canaux (contexte global)
  Dim 384-447 : Statistiques harmoniques d'ordre superieur
  Dim 448-511 : Hash harmonique unique (empreinte de l'image)

Ce vecteur est compact (2KB), deterministe, et permet la reconstruction
partielle de l'image par synthese harmonique inverse.
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

# Tentative scipy pour DCT
try:
    from scipy.fftpack import dctn, dct
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False
    logger.warning("scipy non disponible, DCT approxime par FFT")


def _to_float32_normalized(image: np.ndarray) -> np.ndarray:
    """Convertit image en float32 [0,1] quel que soit le type d'entree."""
    img = np.asarray(image, dtype=np.float32)
    if img.max() > 1.0:
        img = img / 255.0
    return np.clip(img, 0.0, 1.0)


def _rgb_to_ycbcr(img: np.ndarray) -> np.ndarray:
    """Conversion RGB float32 [0,1] -> YCbCr float32."""
    R, G, B = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    Y  =  0.299  * R + 0.587  * G + 0.114  * B
    Cb = -0.1687 * R - 0.3313 * G + 0.5000 * B + 0.5
    Cr =  0.5000 * R - 0.4187 * G - 0.0813 * B + 0.5
    return np.stack([Y, Cb, Cr], axis=-1)


def _rgb_to_hsv(img: np.ndarray) -> np.ndarray:
    """Conversion RGB float32 [0,1] -> HSV float32."""
    R, G, B = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    Cmax = np.maximum(np.maximum(R, G), B)
    Cmin = np.minimum(np.minimum(R, G), B)
    delta = Cmax - Cmin + 1e-10

    H = np.where(Cmax == R, (G - B) / delta % 6,
        np.where(Cmax == G, (B - R) / delta + 2,
                             (R - G) / delta + 4)) / 6.0
    H = H % 1.0
    S = np.where(Cmax > 0, delta / Cmax, 0.0)
    V = Cmax
    return np.stack([H, S, V], axis=-1)


class HarmonicSignatureExtractor:
    """
    Extracteur de signature harmonique 512D depuis une image.

    Usage:
        extractor = HarmonicSignatureExtractor()
        sig, meta = extractor.extract(image_uint8_rgb)
        # sig.shape == (512,), dtype float32, norme 1.0
    """

    def __init__(self, block_size: int = 8, n_fourier: int = 64):
        """
        Args:
            block_size: taille des blocs DCT (defaut 8)
            n_fourier: nombre de frequences Fourier-Phi (defaut 64)
        """
        self.block_size = block_size
        self.n_fourier = n_fourier
        # Frequences harmoniques basees sur phi
        self._phi_freqs = np.array([PHI ** (k / n_fourier) for k in range(n_fourier)],
                                   dtype=np.float32)

    # ------------------------------------------------------------------
    # Methode principale
    # ------------------------------------------------------------------

    def extract(
        self,
        image: np.ndarray,
        video_delta: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Extrait la signature harmonique 512D d'une image.

        Args:
            image: image RGB uint8 [0,255] ou float32 [0,1], shape (H,W,3)
            video_delta: image delta pour video (meme shape), ou None

        Returns:
            (signature 512D float32 normalisee, metadonnees dict)
        """
        t0 = time.time()

        # Normalisation
        img = _to_float32_normalized(image)
        if img.ndim == 2:
            img = np.stack([img, img, img], axis=-1)
        if img.shape[2] == 4:
            img = img[:, :, :3]  # Ignore alpha

        H, W = img.shape[:2]

        # --- Bloc 0-63 : Frequences Fourier-Phi ---
        block0 = self._extract_fourier_phi(img)           # (64,)

        # --- Bloc 64-127 : Profil chromatique ---
        block1 = self._extract_chromatic_profile(img)     # (64,)

        # --- Bloc 128-191 : Coefficients DCT harmoniques ---
        block2 = self._extract_dct_harmonics(img)         # (64,)

        # --- Bloc 192-255 : Gradients spatiaux phi ---
        block3 = self._extract_spatial_phi_gradients(img) # (64,)

        # --- Bloc 256-319 : Signature temporelle ---
        block4 = self._extract_temporal_signature(video_delta, (H, W))  # (64,)

        # --- Bloc 320-383 : Relations spectrales inter-canaux ---
        block5 = self._extract_spectral_relations(img)    # (64,)

        # --- Bloc 384-447 : Statistiques harmoniques superieur ---
        block6 = self._extract_higher_order_stats(img)    # (64,)

        # --- Bloc 448-511 : Hash harmonique unique ---
        block7 = self._extract_harmonic_hash(img)         # (64,)

        # Assemblage du vecteur 512D
        signature = np.concatenate([
            block0, block1, block2, block3,
            block4, block5, block6, block7
        ]).astype(np.float32)

        # Renormalisation L2
        norm = np.linalg.norm(signature)
        if norm > 1e-8:
            signature = signature / norm

        # Metadonnees qualite
        elapsed = time.time() - t0
        meta = self._compute_quality_meta(img, signature, elapsed)

        return signature, meta

    # ------------------------------------------------------------------
    # Blocs d'extraction
    # ------------------------------------------------------------------

    def _extract_fourier_phi(self, img: np.ndarray) -> np.ndarray:
        """
        Bloc 0-63 : Decomposition frequentielle harmonique Fourier-Phi.
        Capture les structures periodiques dominantes de l'image.
        """
        # Luminance
        lum = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]

        # FFT 2D sur luminance
        F = np.fft.fft2(lum)
        F_shift = np.fft.fftshift(F)
        magnitude = np.abs(F_shift)

        # Echantillonnage sur des cercles de rayon phi^k
        H, W = lum.shape
        cx, cy = H // 2, W // 2
        result = np.zeros(64, dtype=np.float32)

        for k in range(64):
            # Rayon harmonique phi^(k/8)
            radius = max(1.0, (PHI ** (k / 8.0)) * min(H, W) / (2.0 * 8))
            # Angle harmonique
            angle = k * 2 * np.pi * PHI / 64.0

            x = int(np.clip(cx + radius * np.cos(angle), 0, H - 1))
            y = int(np.clip(cy + radius * np.sin(angle), 0, W - 1))
            result[k] = float(magnitude[x, y])

        # Normalisation
        rmax = result.max()
        if rmax > 1e-8:
            result = result / rmax

        return result

    def _extract_chromatic_profile(self, img: np.ndarray) -> np.ndarray:
        """
        Bloc 64-127 : Profil chromatique complet YCbCr + HSV.
        Encode la palette de couleurs et sa distribution.
        """
        ycbcr = _rgb_to_ycbcr(img)
        hsv = _rgb_to_hsv(img)

        result = np.zeros(64, dtype=np.float32)

        # YCbCr : stats par canal (mean, std, skewness) = 9 valeurs
        for c in range(3):
            chan = ycbcr[:, :, c].ravel()
            result[c * 3]     = float(chan.mean())
            result[c * 3 + 1] = float(chan.std())
            result[c * 3 + 2] = float(np.mean((chan - chan.mean()) ** 3) / (chan.std() ** 3 + 1e-8))

        # HSV : stats par canal = 9 valeurs
        for c in range(3):
            chan = hsv[:, :, c].ravel()
            result[9 + c * 3]     = float(chan.mean())
            result[9 + c * 3 + 1] = float(chan.std())
            result[9 + c * 3 + 2] = float(np.percentile(chan, 75) - np.percentile(chan, 25))

        # Histogramme HSV simplifie : 8 bins hue + 4 bins sat + 4 bins val = 16
        hue = hsv[:, :, 0].ravel()
        sat = hsv[:, :, 1].ravel()
        val = hsv[:, :, 2].ravel()
        h_hist, _ = np.histogram(hue, bins=8, range=(0, 1))
        s_hist, _ = np.histogram(sat, bins=4, range=(0, 1))
        v_hist, _ = np.histogram(val, bins=4, range=(0, 1))

        result[18:26] = (h_hist / (h_hist.sum() + 1e-8)).astype(np.float32)
        result[26:30] = (s_hist / (s_hist.sum() + 1e-8)).astype(np.float32)
        result[30:34] = (v_hist / (v_hist.sum() + 1e-8)).astype(np.float32)

        # Constante harmonique dominante : rapport phi des canaux
        mean_rgb = np.mean(img, axis=(0, 1))
        result[34] = float(mean_rgb[0])
        result[35] = float(mean_rgb[1])
        result[36] = float(mean_rgb[2])
        result[37] = float(mean_rgb[0] / (mean_rgb[1] + 1e-8))  # rapport R/G
        result[38] = float(mean_rgb[1] / (mean_rgb[2] + 1e-8))  # rapport G/B
        result[39] = float(mean_rgb[0] / (mean_rgb[2] + 1e-8))  # rapport R/B

        # Ecart-types RGB
        std_rgb = np.std(img, axis=(0, 1))
        result[40:43] = std_rgb.astype(np.float32)

        # Padding restant (43-63) : zeros (reserve)
        return result

    def _extract_dct_harmonics(self, img: np.ndarray) -> np.ndarray:
        """
        Bloc 128-191 : Coefficients DCT harmoniques sur blocs 8x8.
        Encode la texture et les frequences spatiales.
        """
        lum = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]

        H, W = lum.shape
        bs = self.block_size

        # Redimensionnement pour avoir des blocs entiers
        pH = (H // bs) * bs
        pW = (W // bs) * bs
        if pH == 0 or pW == 0:
            return np.zeros(64, dtype=np.float32)

        lum_crop = lum[:pH, :pW]
        n_bh = pH // bs
        n_bw = pW // bs

        # Reshape en blocs
        blocks = lum_crop.reshape(n_bh, bs, n_bw, bs).transpose(0, 2, 1, 3)

        # DCT sur chaque bloc
        if SCIPY_OK:
            dct_blocks = dctn(blocks, axes=[2, 3], norm="ortho")
        else:
            # Approximation FFT
            dct_blocks = np.abs(np.fft.rfft2(blocks))[:, :, :bs, :bs]

        # Coefficients harmoniques : ponderation 1/n sur les frequences
        n_blocks = n_bh * n_bw
        dct_flat = dct_blocks.reshape(n_blocks, bs * bs)

        # Ponderation harmonique : coeff[k] * (1/(k+1)^PHI)
        k_vals = np.arange(bs * bs, dtype=np.float32)
        harmonic_weights = 1.0 / ((k_vals + 1) ** PHI)
        harmonic_weights /= harmonic_weights.sum()

        # Statistiques des coefficients ponderes sur tous les blocs
        weighted = dct_flat * harmonic_weights  # (N, 64)

        result = np.zeros(64, dtype=np.float32)
        # 32 premieres stats : moyenne par coeff des 32 premiers
        n_stats = min(32, bs * bs)
        result[:n_stats] = np.mean(np.abs(weighted[:, :n_stats]), axis=0)
        # 32 suivantes : ecart-type
        result[32:32 + n_stats] = np.std(weighted[:, :n_stats], axis=0)

        # Normalisation
        mx = np.abs(result).max()
        if mx > 1e-8:
            result = result / mx

        return result

    def _extract_spatial_phi_gradients(self, img: np.ndarray) -> np.ndarray:
        """
        Bloc 192-255 : Gradients spatiaux sur grille phi.
        Encode la structure et les contours selon la grille harmonique.
        """
        lum = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
        H, W = lum.shape

        result = np.zeros(64, dtype=np.float32)

        # Gradients Sobel simplifies (via differences finies)
        if H > 1 and W > 1:
            grad_y = np.diff(lum, axis=0)    # (H-1, W)
            grad_x = np.diff(lum, axis=1)    # (H, W-1)

            # Magnitude
            # Alignement minimal
            min_h = min(grad_y.shape[0], grad_x.shape[0])
            min_w = min(grad_y.shape[1], grad_x.shape[1])
            mag = np.sqrt(grad_y[:min_h, :min_w] ** 2 + grad_x[:min_h, :min_w] ** 2)
        else:
            mag = np.zeros_like(lum)

        # Echantillonnage sur grille phi 8x8 = 64 points
        grid_h = np.linspace(0, mag.shape[0] - 1, 8).astype(int)
        grid_w = np.linspace(0, mag.shape[1] - 1, 8).astype(int)

        idx = 0
        for i in grid_h:
            for j in grid_w:
                result[idx] = float(mag[i, j])
                idx += 1

        # Stats globales de gradient
        result[60] = float(mag.mean())
        result[61] = float(mag.std())
        result[62] = float(mag.max())
        result[63] = float(np.percentile(mag, 90))

        # Normalisation
        mx = result.max()
        if mx > 1e-8:
            result = result / mx

        return result

    def _extract_temporal_signature(
        self, video_delta: Optional[np.ndarray], shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Bloc 256-319 : Signature temporelle pour video.
        Pour une image statique, retourne zeros.
        """
        result = np.zeros(64, dtype=np.float32)

        if video_delta is None:
            return result

        # Delta harmonique entre frames consecutives
        delta = _to_float32_normalized(video_delta)
        if delta.ndim == 2:
            delta = np.stack([delta, delta, delta], axis=-1)
        if delta.shape[2] > 3:
            delta = delta[:, :, :3]

        # Stats du delta
        delta_lum = 0.299 * delta[:, :, 0] + 0.587 * delta[:, :, 1] + 0.114 * delta[:, :, 2]

        result[0] = float(delta_lum.mean())
        result[1] = float(delta_lum.std())
        result[2] = float(delta_lum.max())
        result[3] = float(np.percentile(delta_lum, 95))

        # Flux optique simplifie : energie du mouvement
        H, W = delta_lum.shape
        if H > 2 and W > 2:
            motion_energy = np.mean(delta_lum ** 2) * PHI2
            result[4] = float(motion_energy)

        # Coherence temporelle harmonique
        coherence = 1.0 - float(delta_lum.mean())
        result[5] = max(0.0, min(1.0, coherence))

        # Frequences temporelles (FFT 1D sur diagonale)
        diag_len = min(H, W)
        diag = np.array([delta_lum[i, i] for i in range(diag_len)])
        if len(diag) >= 8:
            fft_diag = np.abs(np.fft.rfft(diag))[:32]
            result[6:6 + len(fft_diag)] = (fft_diag / (fft_diag.max() + 1e-8)).astype(np.float32)

        return result

    def _extract_spectral_relations(self, img: np.ndarray) -> np.ndarray:
        """
        Bloc 320-383 : Relations spectrales inter-canaux.
        Encode le contexte global et les correlations chromatiques.
        """
        result = np.zeros(64, dtype=np.float32)

        # Correlations inter-canaux
        R = img[:, :, 0].ravel()
        G = img[:, :, 1].ravel()
        B = img[:, :, 2].ravel()

        result[0] = float(np.corrcoef(R, G)[0, 1])
        result[1] = float(np.corrcoef(G, B)[0, 1])
        result[2] = float(np.corrcoef(R, B)[0, 1])

        # Entropie de Shannon par canal
        for c, chan in enumerate([R, G, B]):
            hist, _ = np.histogram(chan, bins=32, range=(0, 1))
            hist = hist / (hist.sum() + 1e-10)
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            result[3 + c] = float(entropy / 5.0)  # Normalise sur 5 bits max

        # FFT 1D sur chaque canal (profil horizontal moyen)
        for c in range(3):
            row_mean = img[:, :, c].mean(axis=0)  # (W,)
            fft_row = np.abs(np.fft.rfft(row_mean))
            n_keep = min(18, len(fft_row))
            result[6 + c * 18:6 + c * 18 + n_keep] = (
                fft_row[:n_keep] / (fft_row[:n_keep].max() + 1e-8)
            ).astype(np.float32)

        # Symmetrie phi de l'image
        H, W = img.shape[:2]
        half_h = H // 2
        if half_h > 0:
            top = img[:half_h, :, :]
            bot = img[half_h:2 * half_h, :, :]
            if top.shape == bot.shape:
                sym_score = 1.0 - float(np.mean(np.abs(top - bot[::-1, :, :])))
                result[60] = sym_score

        half_w = W // 2
        if half_w > 0:
            left = img[:, :half_w, :]
            right = img[:, half_w:2 * half_w, :]
            if left.shape == right.shape:
                sym_score = 1.0 - float(np.mean(np.abs(left - right[:, ::-1, :])))
                result[61] = sym_score

        return result

    def _extract_higher_order_stats(self, img: np.ndarray) -> np.ndarray:
        """
        Bloc 384-447 : Statistiques d'ordre superieur harmoniques.
        """
        result = np.zeros(64, dtype=np.float32)

        lum = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
        lum_flat = lum.ravel()

        mean = lum_flat.mean()
        std = lum_flat.std() + 1e-8

        # Moments statistiques d'ordre 1-8
        for order in range(1, 9):
            moment = np.mean(((lum_flat - mean) / std) ** order)
            result[order - 1] = float(np.clip(moment / (PHI ** order), -1, 1))

        # Quantiles harmoniques (percentiles bases sur phi)
        phi_percentiles = [p * 100 for p in [1.0 / PHI3, 1.0 / PHI2, 1.0 / PHI, 0.5,
                                               PHI / PHI2, 1.0 - 1.0 / PHI2, 1.0 - 1.0 / PHI3]]
        for i, p in enumerate(phi_percentiles):
            result[8 + i] = float(np.percentile(lum_flat, p))

        # Covariance spatiale locale (texture)
        H, W = lum.shape
        if H > 1 and W > 1:
            cov_h = float(np.mean(lum[:-1, :] * lum[1:, :]) - mean ** 2)
            cov_v = float(np.mean(lum[:, :-1] * lum[:, 1:]) - mean ** 2)
            result[15] = float(np.clip(cov_h / (std ** 2), -1, 1))
            result[16] = float(np.clip(cov_v / (std ** 2), -1, 1))

        # Score d'harmonie global (mesure de la periodicite phi)
        fft_lum = np.abs(np.fft.rfft2(lum))
        H2, W2 = fft_lum.shape
        phi_freq_h = int(H2 / PHI) % H2
        phi_freq_w = int(W2 / PHI) % W2
        energy_at_phi = float(fft_lum[phi_freq_h, phi_freq_w])
        total_energy = float(fft_lum.sum() + 1e-8)
        result[17] = min(1.0, energy_at_phi / total_energy * 100)

        return result

    def _extract_harmonic_hash(self, img: np.ndarray) -> np.ndarray:
        """
        Bloc 448-511 : Hash harmonique unique de l'image.
        Empreinte unique reproductible.
        """
        result = np.zeros(64, dtype=np.float32)

        # Redimensionnement harmonique : 8x8 = 64 pixels -> hash visuel
        H, W = img.shape[:2]
        step_h = max(1, H // 8)
        step_w = max(1, W // 8)

        idx = 0
        for i in range(8):
            for j in range(8):
                y = min(i * step_h, H - 1)
                x = min(j * step_w, W - 1)
                # Luminance du pixel sous-echantillonne
                r, g, b = img[y, x, 0], img[y, x, 1], img[y, x, 2]
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                result[idx] = float(lum)
                idx += 1

        # Application de la transformation harmonique phi sur le hash
        result = np.sin(result * np.pi * PHI).astype(np.float32)

        return result

    # ------------------------------------------------------------------
    # Metadonnees qualite
    # ------------------------------------------------------------------

    def _compute_quality_meta(
        self, img: np.ndarray, signature: np.ndarray, elapsed: float
    ) -> Dict[str, Any]:
        """Calcule les metadonnees de qualite de la signature."""
        H, W = img.shape[:2]

        # Score d'harmonie : energie sur les frequences phi
        harmony_score = float(np.clip(np.std(signature[:64]) * PHI2, 0, 1))

        # Coherence chromatique : correlation inter-canaux
        chromatic_slice = signature[64:128]
        chromatic_consistency = float(np.clip(1.0 - np.std(chromatic_slice[:9:3]), 0, 1))

        # Richesse texture : energie DCT
        dct_slice = signature[128:192]
        texture_richness = float(np.clip(np.mean(np.abs(dct_slice)) * PHI, 0, 1))

        # Coherence spatiale : regularite des gradients
        grad_slice = signature[192:256]
        spatial_coherence = float(np.clip(1.0 - np.std(grad_slice), 0, 1))

        # Score global
        overall = (harmony_score * 0.3 + chromatic_consistency * 0.25 +
                   texture_richness * 0.25 + spatial_coherence * 0.20)

        return {
            "harmony_score": harmony_score,
            "chromatic_consistency": chromatic_consistency,
            "texture_richness": texture_richness,
            "spatial_coherence": spatial_coherence,
            "overall_quality": float(overall),
            "signature_norm": float(np.linalg.norm(signature)),
            "extraction_time_ms": elapsed * 1000,
            "image_resolution": (W, H),
        }

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def extract_from_video_frames(
        self,
        frames: List[np.ndarray],
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Extrait une signature video depuis une liste de frames.
        Integre la dimension temporelle (deltas).
        """
        if not frames:
            return np.zeros(SIGNATURE_DIM, dtype=np.float32), {}

        if len(frames) == 1:
            return self.extract(frames[0])

        # Signature de la frame cle (mediane temporellement)
        key_frame_idx = len(frames) // 2
        key_frame = frames[key_frame_idx]

        # Delta avec la frame precedente
        prev_frame = frames[key_frame_idx - 1] if key_frame_idx > 0 else key_frame
        delta = _to_float32_normalized(key_frame) - _to_float32_normalized(prev_frame)
        delta = np.abs(delta)

        sig, meta = self.extract(key_frame, video_delta=delta)

        # Enrichir les metadonnees avec info video
        meta["is_video"] = True
        meta["n_frames"] = len(frames)
        meta["key_frame_idx"] = key_frame_idx

        return sig, meta

    def compute_similarity(
        self, sig1: np.ndarray, sig2: np.ndarray
    ) -> float:
        """
        Calcule la similarite cosinus entre deux signatures harmoniques.
        
        Returns:
            float [0, 1] : 1.0 = identiques, 0.0 = orthogonaux
        """
        dot = float(np.dot(sig1, sig2))
        n1 = float(np.linalg.norm(sig1))
        n2 = float(np.linalg.norm(sig2))
        if n1 < 1e-8 or n2 < 1e-8:
            return 0.0
        cosine = dot / (n1 * n2)
        # Mapping cosine [-1,1] -> [0,1]
        return float((cosine + 1.0) / 2.0)


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== Test HarmonicSignatureExtractor ===")

    extractor = HarmonicSignatureExtractor()

    # Image de test synthétique
    np.random.seed(42)
    test_img = (np.random.rand(256, 256, 3) * 255).astype(np.uint8)
    # Ajouter un motif phi pour la rendre plus harmonique
    for i in range(256):
        for j in range(0, 256, int(256 / PHI)):
            test_img[i, j:j+2, :] = 200

    sig, meta = extractor.extract(test_img)

    print(f"Signature extraite:")
    print(f"  Shape  : {sig.shape}")
    print(f"  Norme  : {sig.norm() if hasattr(sig, 'norm') else np.linalg.norm(sig):.6f}")
    print(f"  Min/Max: {sig.min():.4f} / {sig.max():.4f}")
    print(f"\nMetadonnees qualite:")
    for k, v in meta.items():
        print(f"  {k}: {v}")

    # Test similarite
    sig2, _ = extractor.extract(test_img)  # Meme image = identique
    sim = extractor.compute_similarity(sig, sig2)
    print(f"\nSimilarite (image identique): {sim:.6f} (attendu ~1.0)")

    # Image aleatoire differente
    other_img = (np.random.rand(256, 256, 3) * 255).astype(np.uint8)
    sig3, _ = extractor.extract(other_img)
    sim2 = extractor.compute_similarity(sig, sig3)
    print(f"Similarite (image differente): {sim2:.6f} (attendu < {sim:.3f})")

    print("\n=== Test termine avec succes ===")
