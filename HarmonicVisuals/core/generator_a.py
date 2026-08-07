"""
MODE A — Geometric Generator: ψ → IFFT 2D → patterns ondulatoires
===================================================================

Génération purement mathématique : le vecteur ψ est transformé en grille 2D
via une IFFT 2D. Chaque pixel = interférence des ondes ψ.
Esthétique géométrique/ondulatoire, 100% déterministe, 0 donnée externe.
"""

import math
import numpy as np

PHI = 1.618033988749895
TAU = 2.0 * math.pi


class GeometricGenerator:
    """Générateur géométrique par interférence ψ → IFFT 2D."""
    
    def __init__(self, dim: int = 512):
        self.dim = dim
    
    def generate(self, psi: np.ndarray, width: int = 1024, height: int = 1024) -> np.ndarray:
        """
        Génère une image par interférence ondulatoire.
        
        Args:
            psi: [dim] complex128 — vecteur du prompt
            width, height: dimensions de sortie
            
        Returns:
            [H, W, 3] uint8
        """
        dim = len(psi)
        
        # 1. Redimensionner ψ en grille 2D carrée
        grid_size = int(math.sqrt(dim))
        if grid_size * grid_size > dim:
            grid_size -= 1
        n = grid_size * grid_size
        
        psi_2d = psi[:n].reshape(grid_size, grid_size)
        
        # 2. IFFT 2D → domaine spatial
        spatial = np.fft.ifft2(psi_2d, s=(height, width))
        
        # 3. Extraire magnitude et phase
        magnitude = np.abs(spatial)
        phase = np.angle(spatial)
        
        # 4. Normalisation φ de la magnitude (meilleur contraste)
        mag_flat = magnitude.flatten()
        p_low = np.percentile(mag_flat, 5)
        p_high = np.percentile(mag_flat, 95)
        magnitude = np.clip((magnitude - p_low) / (p_high - p_low + 1e-10), 0, 1)
        
        # 5. Générer 3 canaux (R, G, B) avec rotation de phase φ
        # Canal R : phase originale
        # Canal G : phase décalée de 120° (2π/3)
        # Canal B : phase décalée de 240° (4π/3)
        
        channels = []
        for offset in [0, TAU/3, 2*TAU/3]:
            shifted_phase = (phase + offset) % TAU
            # Mapping phase → intensité avec harmoniques φ
            channel = np.sin(shifted_phase) * 0.5 + 0.5  # [-1, 1] → [0, 1]
            channel = channel * magnitude  # Moduler par la magnitude
            channels.append(channel)
        
        # 6. Assemblage RGB
        img = np.stack(channels, axis=-1)  # [H, W, 3]
        
        # 7. Correction gamma φ (perceptuellement plus naturel)
        img = np.power(np.clip(img, 0, 1), 1.0 / PHI)
        
        # 8. Conversion uint8
        img = (img * 255).astype(np.uint8)
        
        return img
    
    def generate_variations(self, psi: np.ndarray, width: int = 512, height: int = 512,
                           n_variations: int = 4) -> list:
        """Génère des variations par rotation de phase φ."""
        variations = []
        for i in range(n_variations):
            # Rotation du ψ par multiples de φ
            rotated = psi * np.exp(1j * PHI * i)
            variations.append(self.generate(rotated, width, height))
        return variations
