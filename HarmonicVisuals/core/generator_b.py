"""
MODE B — Realistic Generator: ψ → HarmonicDatabase → composition de patches réels
===================================================================================

Photoréalisme par retrieval de patches dans un dictionnaire visuel.
Chaque patch est un fragment de vraie photo, indexé par sa signature DFT.
La composition utilise PatchMatch pour la cohérence spatiale.
"""

import math
import numpy as np
from pathlib import Path


class RealisticGenerator:
    """Générateur photoréaliste par dictionnaire de patches."""
    
    def __init__(self, dim: int = 512, patch_size: int = 16):
        self.dim = dim
        self.patch_size = patch_size
        self._db = None  # HarmonicDatabase (chargé à la demande)
    
    def set_database(self, db):
        """Attache une HarmonicDatabase au générateur."""
        self._db = db
    
    def load(self, path: str):
        """Charge un dictionnaire depuis le disque."""
        try:
            from .dictionary import HarmonicDatabase
            self._db = HarmonicDatabase()
            self._db.load(path)
        except ImportError:
            pass
    
    def generate(self, psi: np.ndarray, width: int = 1024, height: int = 1024) -> np.ndarray:
        """
        Génère une image par composition de patches réels.
        
        Args:
            psi: [dim] complex128
            width, height: dimensions de sortie
            
        Returns:
            [H, W, 3] uint8
        """
        if self._db is None:
            raise RuntimeError("Aucun dictionnaire chargé. Utilisez .load(path) ou .set_database(db)")
        
        # Mapper ψ → concept visuel
        concept = self._psi_to_concept(psi)
        
        # Générer via le dictionnaire
        image = self._db.generate(concept, width=width, height=height)

        if image is None or image.size == 0:
            # Fallback geometrique
            from .generator_a import GeometricGenerator
            return GeometricGenerator(dim=self.dim).generate(psi, width, height)
        
        return image
    
    def _psi_to_concept(self, psi: np.ndarray) -> str:
        """Mappe ψ → concept visuel par plus proche voisin dans l'espace ψ."""
        concepts = {
            'sunset': ['sunset', 'dusk', 'coucher', 'soleil', 'couchant', 'crépuscule'],
            'ocean': ['ocean', 'sea', 'mer', 'océan', 'wave', 'vague', 'beach', 'plage'],
            'forest': ['forest', 'tree', 'forêt', 'arbre', 'wood', 'bois', 'jungle'],
            'mountain': ['mountain', 'montagne', 'peak', 'pic', 'snow', 'neige', 'alps'],
            'city': ['city', 'ville', 'urban', 'building', 'immeuble', 'street', 'rue'],
            'sky': ['sky', 'ciel', 'cloud', 'nuage', 'star', 'étoile', 'night', 'nuit'],
            'flower': ['flower', 'fleur', 'petal', 'pétale', 'garden', 'jardin', 'rose'],
            'abstract': ['abstract', 'pattern', 'texture', 'geometric', 'color', 'couleur'],
        }
        
        # Encodage rapide de chaque concept
        from .encoder import HarmonicEncoder
        encoder = HarmonicEncoder(dim=self.dim)
        
        best_concept = 'abstract'
        best_score = -1
        
        # Comparer ψ avec chaque concept
        psi_flat = np.abs(psi)
        for concept, keywords in concepts.items():
            concept_psi = encoder.encode(' '.join(keywords))
            # Similarité cosinus
            score = np.dot(psi_flat, np.abs(concept_psi))
            score /= (np.linalg.norm(psi_flat) * np.linalg.norm(np.abs(concept_psi)) + 1e-10)
            if score > best_score:
                best_score = score
                best_concept = concept
        
        return best_concept
