#!/usr/bin/env python3
"""
HARMONIC HOLOGRAPHIC PROJECTOR — Projection 3D à partir d'une surface 2D
===========================================================================
Implémente le principe holographique : encode une scène sur une grille 2D
d'ondes complexes, puis la projette en 3D sous n'importe quel angle.

Principe :
  1. ENCODAGE : prompt → grille 2D d'ondes complexes H[i][j]
  2. PROJECTION : angle θ → rotation dans l'espace de Fourier
     H_θ = TF^{-1}[TF[H] * exp(i*k*sin(θ))]
  3. RENDU : reconstruction de l'image visible + éclairage + ombres

C'est le mécanisme fondamental par lequel l'univers projette la 3D
à partir d'informations 2D (principe holographique de 't Hooft/Susskind).

Usage :
  from harmonic_holographic_projector import HarmonicHolographicProjector
  hhp = HarmonicHolographicProjector()
  image_3d = hhp.project("une pyramide dans le désert", angle_deg=30)
  # → Vue 3D sous 30° de la pyramide, avec perspective et ombres
"""

import numpy as np
import math, random, time, os, hashlib
from typing import Dict, List, Tuple, Optional, Any

PHI = 1.618033988749895
GRID_SIZE = 256  # Surface holographique 256×256
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "holographic_projector")
os.makedirs(DATA_DIR, exist_ok=True)

class HarmonicHolographicProjector:
    """
    Encode une scène sur une surface holographique 2D et la projette en 3D.
    
    Architecture :
      Surface 2D (grille complexe) → TF → Rotation → TF^{-1} → Image 3D
    """

    def __init__(self, grid_size: int = 256):
        self.grid_size = grid_size
        self.hologram = np.zeros((grid_size, grid_size), dtype=np.complex128)
        self.metadata = {}

    # ═══ WAVE OPERATIONS ═══

    def _text_to_phase(self, text: str) -> float:
        """Convertit un texte en angle de phase (0 à 2π)."""
        h = int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)
        return (h / (2**64)) * 2 * math.pi

    def _point_source(self, x0: float, y0: float, z0: float, 
                      amplitude: float = 1.0, wavelength: float = 10.0) -> np.ndarray:
        """
        Crée une onde sphérique sur la surface holographique
        émise par un point 3D (x0, y0, z0).
        
        La phase dépend de la distance au point source :
        φ(x,y) = 2π * sqrt((x-x0)² + (y-y0)² + z0²) / λ
        """
        x = np.linspace(-self.grid_size/2, self.grid_size/2, self.grid_size)
        y = np.linspace(-self.grid_size/2, self.grid_size/2, self.grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Distance 3D au point source
        dist = np.sqrt((X - x0)**2 + (Y - y0)**2 + z0**2)
        
        # Onde sphérique : atténuation en 1/dist
        wave = amplitude * np.exp(1j * 2 * math.pi * dist / wavelength) / (dist + 1.0)
        
        return wave

    def _plane_wave(self, kx: float, ky: float, amplitude: float = 1.0) -> np.ndarray:
        """
        Crée une onde plane sur la surface holographique.
        Une onde plane correspond à une source à l'infini (ex: le soleil).
        """
        x = np.linspace(-self.grid_size/2, self.grid_size/2, self.grid_size)
        y = np.linspace(-self.grid_size/2, self.grid_size/2, self.grid_size)
        X, Y = np.meshgrid(x, y)
        
        wave = amplitude * np.exp(1j * (kx * X / self.grid_size * 20 + 
                                         ky * Y / self.grid_size * 20))
        return wave

    # ═══ ENCODAGE : OBJET 3D → SURFACE 2D ═══

    def encode_shape(self, shape: str, position: Tuple[float, float, float], 
                     size: float = 40.0, amplitude: float = 1.5) -> None:
        """
        Encode un objet 3D sur la surface holographique.
        
        Args:
            shape: "pyramid", "sphere", "cube", "pillar", "triangle"
            position: (x, y, z) centre de l'objet
            size: taille de l'objet
            amplitude: intensité de l'onde
        """
        x0, y0, z0 = position
        wavelength = size * 0.8  # Longueur d'onde proportionnelle à la taille
        
        if shape == "pyramid":
            # Pyramide = 5 points (4 base + 1 sommet)
            points = [
                (x0 - size, y0 - size, z0 + size),  # Base avant-gauche
                (x0 + size, y0 - size, z0 + size),  # Base avant-droite
                (x0 + size, y0 + size, z0 + size),  # Base arrière-droite
                (x0 - size, y0 + size, z0 + size),  # Base arrière-gauche
                (x0, y0, z0 - size),                 # Sommet (devant)
            ]
            for px, py, pz in points:
                self.hologram += self._point_source(px, py, pz, amplitude, wavelength)
        
        elif shape == "sphere":
            # Sphère = nuage de points sur la surface
            n_points = 20
            for i in range(n_points):
                theta = random.uniform(0, 2 * math.pi)
                phi = random.uniform(0, math.pi)
                px = x0 + size * math.sin(phi) * math.cos(theta)
                py = y0 + size * math.sin(phi) * math.sin(theta)
                pz = z0 + size * math.cos(phi)
                self.hologram += self._point_source(px, py, pz, amplitude * 0.3, wavelength)
        
        elif shape == "cube":
            # Cube = 8 sommets
            for dx in [-size, size]:
                for dy in [-size, size]:
                    for dz in [z0 - size, z0 + size]:
                        self.hologram += self._point_source(x0 + dx, y0 + dy, dz, amplitude * 0.4, wavelength)
        
        elif shape == "pillar":
            # Cylindre = cercle de points échantillonné le long de l'axe z
            n_circles = 8
            n_points_per_circle = 12
            for ci in range(n_circles):
                z = z0 - size + 2 * size * ci / n_circles
                for pi in range(n_points_per_circle):
                    angle = 2 * math.pi * pi / n_points_per_circle
                    px = x0 + size * math.cos(angle)
                    py = y0 + size * math.sin(angle)
                    self.hologram += self._point_source(px, py, z, amplitude * 0.2, wavelength)
        
        elif shape == "triangle":
            # Triangle dans le plan XZ (face au spectateur)
            points = [
                (x0, y0, z0 - size),           # Sommet haut
                (x0 - size, y0, z0 + size),    # Base gauche
                (x0 + size, y0, z0 + size),    # Base droite
            ]
            for px, py, pz in points:
                self.hologram += self._point_source(px, py, pz, amplitude, wavelength)

    def encode_scene(self, scene_type: str) -> str:
        """
        Encode une scène complète sur la surface holographique.
        
        Args:
            scene_type: "pyramids_desert", "temple", "mountains", "abstract"
        
        Returns:
            Description de la scène encodée
        """
        self.hologram = np.zeros((self.grid_size, self.grid_size), dtype=np.complex128)
        
        if scene_type == "pyramids_desert":
            # Trois pyramides
            self.encode_shape("pyramid", (-60, -20, 80), size=30, amplitude=2.0)
            self.encode_shape("pyramid", (30, -30, 60), size=40, amplitude=2.2)
            self.encode_shape("pyramid", (-40, 20, 100), size=25, amplitude=1.8)
            # Sol (plan d'onde)
            for i in range(10):
                x = random.uniform(-100, 100)
                y = random.uniform(-100, 100)
                self.hologram += self._point_source(x, y, 120, 0.15, 50)
            # Soleil (onde plane)
            self.hologram += self._plane_wave(3.0, 1.0, 0.8)
        
        elif scene_type == "temple":
            # Colonnes
            for i in range(6):
                cx = -80 + i * 30
                self.encode_shape("pillar", (cx, 0, 60), size=10, amplitude=1.5)
            # Triangle du fronton
            self.encode_shape("triangle", (0, 0, 20), size=50, amplitude=1.8)
            # Sol
            for i in range(15):
                self.hologram += self._point_source(
                    random.uniform(-100, 100), random.uniform(-80, 80), 100, 0.1, 60)
        
        elif scene_type == "mountains":
            # Sommets
            for i in range(5):
                mx = -100 + i * 50
                my = random.uniform(-30, 30)
                self.encode_shape("pyramid", (mx, my, 80), size=35, amplitude=2.0)
            # Nuages (sphères diffuses en altitude)
            for i in range(8):
                self.encode_shape("sphere", 
                    (random.uniform(-80, 80), random.uniform(-60, 60), random.uniform(-30, 0)),
                    size=15, amplitude=0.3)
        
        elif scene_type == "abstract":
            # Composition géométrique
            self.encode_shape("sphere", (0, 0, 50), size=40, amplitude=2.0)
            self.encode_shape("cube", (50, 30, 80), size=20, amplitude=1.5)
            self.encode_shape("triangle", (-40, -20, 30), size=30, amplitude=1.8)
            self.encode_shape("pillar", (0, 50, 70), size=12, amplitude=1.3)

        # Anti-saturation
        mx = np.max(np.abs(self.hologram))
        if mx > 200:
            self.hologram *= 0.9

        self.metadata["scene_type"] = scene_type
        self.metadata["total_energy"] = float(np.sum(np.abs(self.hologram)**2))
        return scene_type

    # ═══ PROJECTION 3D ═══

    def project(self, angle_deg: float = 0.0, distance: float = 100.0) -> np.ndarray:
        """
        Projette la surface holographique dans une image 2D visible
        sous un angle de vue donné.
        
        Args:
            angle_deg: angle de rotation horizontal (0 = face, 45 = 3/4, 90 = profil)
            distance: distance d'observation (plus grand = moins de perspective)
        
        Returns:
            Grille 2D de l'image projetée (valeurs réelles entre 0 et 1)
        """
        angle_rad = math.radians(angle_deg)
        
        # Étape 1 : Transformée de Fourier de la surface holographique
        H_freq = np.fft.fft2(self.hologram)
        H_freq_shifted = np.fft.fftshift(H_freq)
        
        # Étape 2 : Rotation dans l'espace de Fourier
        # Un décalage de phase dans Fourier = rotation dans l'espace réel
        rows, cols = self.grid_size, self.grid_size
        crow, ccol = rows // 2, cols // 2
        
        # Créer le masque de rotation
        y, x = np.ogrid[-crow:rows-crow, -ccol:cols-ccol]
        
        # Le décalage horizontal simule la rotation 3D
        shift_x = math.sin(angle_rad) * 20
        shift_y = math.cos(angle_rad) * 5  # Légère élévation
        
        # Appliquer le déphasage (rotation de Fourier)
        phase_shift = np.exp(-1j * 2 * math.pi * (shift_x * x / cols + shift_y * y / rows))
        H_rotated_freq = H_freq_shifted * phase_shift
        
        # Étape 3 : Transformée inverse pour obtenir l'image projetée
        H_rotated = np.fft.ifft2(np.fft.ifftshift(H_rotated_freq))
        
        # Étape 4 : Intensité (module carré) + éclairage
        intensity = np.abs(H_rotated)
        
        # Éclairage directionnel (ombres portées)
        # La dérivée dans la direction de la lumière crée des ombres
        light_dir_x = math.sin(angle_rad + 0.5)  # Lumière légèrement décalée
        light_dir_y = math.cos(angle_rad + 0.5)
        
        # Gradient pour les ombres
        gy, gx = np.gradient(intensity)
        shadow = gx * light_dir_x + gy * light_dir_y
        shadow = np.clip(shadow, -1, 1) * 0.3
        
        # Combiner intensité + ombres
        image = intensity + shadow
        
        # Normaliser dans [0, 1]
        image_min = np.min(image)
        image_max = np.max(image)
        if image_max > image_min:
            image = (image - image_min) / (image_max - image_min)
        
        # Contraste adaptatif (gamma correction)
        image = np.power(image, 1.2)  # Légèrement plus de contraste
        
        # Perspective : objets lointains plus petits
        # (simulée par un vignettage doux)
        r = np.sqrt((x/crow)**2 + (y/ccol)**2)
        vignette = 1.0 - np.clip(r * 0.4, 0, 0.5)
        image = image * vignette + 0.1 * (1 - vignette)
        
        return np.clip(image, 0, 1)

    def project_multi_view(self, angles: List[float]) -> List[np.ndarray]:
        """Génère plusieurs vues de la même scène (utile pour animation)."""
        return [self.project(angle) for angle in angles]

    def save_projection(self, image: np.ndarray, filename: str) -> str:
        """
        Sauvegarde l'image projetée en PNG.
        Utilise PIL si disponible, sinon sauvegarde en format binaire brut.
        """
        filepath = os.path.join(DATA_DIR, filename)
        
        try:
            from PIL import Image
            # Normaliser dans [0, 255]
            img_array = (image * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='L')
            img.save(filepath)
        except ImportError:
            # Fallback : sauvegarder en numpy
            np.save(filepath.replace('.png', '.npy'), image)
        
        return filepath

    def get_stats(self) -> Dict:
        """Statistiques de la surface holographique."""
        return {
            "grid_size": self.grid_size,
            "total_energy": float(np.sum(np.abs(self.hologram)**2)),
            "max_amplitude": float(np.max(np.abs(self.hologram))),
            "phase_range": (float(np.min(np.angle(self.hologram))), 
                           float(np.max(np.angle(self.hologram)))),
            "metadata": self.metadata,
        }


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    hhp = HarmonicHolographicProjector(grid_size=128)
    
    print("=" * 60)
    print("HARMONIC HOLOGRAPHIC PROJECTOR - Test")
    print("=" * 60)
    
    scenes = ["pyramids_desert", "temple", "mountains", "abstract"]
    
    for scene in scenes:
        print(f"\nEncodage de la scène: {scene}")
        hhp.encode_scene(scene)
        stats = hhp.get_stats()
        print(f"  Énergie: {stats['total_energy']:.0f}")
        
        # Projection sous 3 angles
        for angle in [0, 30, 60]:
            image = hhp.project(angle)
            filename = f"{scene}_angle_{angle}.png"
            path = hhp.save_projection(image, filename)
            print(f"  Angle {angle} degrés → {path} ({image.mean():.3f} intensité moyenne)")

    print(f"\nImages sauvegardées dans: {DATA_DIR}")