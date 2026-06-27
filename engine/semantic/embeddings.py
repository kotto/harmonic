"""
Embeddings harmoniques — Vecteurs semantiques enrichis des signatures 9D.
=========================================================================
Combine les embeddings classiques (sentence-transformers) avec les
signatures harmoniques 9D pour un vecteur hybride unique.
"""

import os
import time
import logging
import numpy as np
from typing import Optional, List

logger = logging.getLogger(__name__)

# Dimensions
HARMONIC_DIM = 9       # Dimensions harmoniques (signatures 9D)
TRANSFORMER_DIM = 512  # Dimensions du transformer (par defaut)
HYBRID_DIM = HARMONIC_DIM + TRANSFORMER_DIM  # Vecteur total


class HarmonicEmbeddings:
    """
    Embeddings harmoniques hybrides.
    
    Combine:
        1. Signatures harmoniques 9D (phi, alpha, reasoning, ...)
        2. Embeddings semantiques classiques (sentence-transformers)
    
    Usage:
        emb = HarmonicEmbeddings()
        vector = emb.embed("Quelle est la capitale de la France ?")
        # vector.shape == (521,)  # 9 harmoniques + 512 semantiques
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._harmonic_engine = None
    
    def _load_model(self):
        """Charge le modele sentence-transformers (lazy)."""
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Modele embeddings charge: {self.model_name}")
        except ImportError:
            logger.warning(
                "sentence-transformers non installe. "
                "Fallback: embeddings aleatoires"
            )
            self._model = None
    
    def _connect_harmonic(self):
        """Connecte les signatures harmoniques 9D."""
        if self._harmonic_engine is not None:
            return
        try:
            from ..harmonic_engine import HarmonicResonanceEngine
            from ..signatures_9d import compute_signature_9d
            self._harmonic_engine = HarmonicResonanceEngine()
            self._compute_9d = compute_signature_9d
        except ImportError:
            self._harmonic_engine = None
    
    def embed(self, text: str) -> np.ndarray:
        """
        Calcule l'embedding harmonique hybride d'un texte.
        
        Returns:
            np.ndarray [HYBRID_DIM] = 9 + 512 dimensions
        """
        # 1. Embedding semantique
        self._load_model()
        if self._model is not None:
            semantic = self._model.encode(text, normalize_embeddings=True)
        else:
            # Fallback: vecteur aleatoire normalise
            semantic = np.random.randn(TRANSFORMER_DIM)
            semantic = semantic / np.linalg.norm(semantic)
        
        # 2. Signature harmonique 9D
        self._connect_harmonic()
        if self._harmonic_engine is not None:
            signature = self._harmonic_engine.analyze(text)
            harmonic = np.array(signature.vector_7d + [0.0, 0.0])  # 7D -> 9D
        else:
            harmonic = np.zeros(HARMONIC_DIM)
        
        # 3. Hybridation
        hybrid = np.concatenate([harmonic, semantic])
        hybrid = hybrid / np.linalg.norm(hybrid)
        
        return hybrid
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Calcule les embeddings d'un batch de textes."""
        embeddings = []
        for text in texts:
            emb = self.embed(text)
            embeddings.append(emb)
        return np.stack(embeddings)
    
    def similarity(self, a: str, b: str) -> float:
        """Similarite cosinus entre deux textes."""
        emb_a = self.embed(a)
        emb_b = self.embed(b)
        return float(np.dot(emb_a, emb_b))


# Fonction simplifiee
def compute_text_embedding(text: str) -> np.ndarray:
    """Fonction rapide pour un embedding."""
    emb = HarmonicEmbeddings()
    return emb.embed(text)
