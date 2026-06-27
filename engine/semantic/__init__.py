"""
Semantic Engine — Embeddings vectoriels et RAG (Retrieval-Augmented Generation)
=================================================================================
Transforme le texte en vecteurs harmoniques pour la recherche semantique.

Composants:
    - HarmonicEmbeddings → Embeddings 9D + 512D (via sentence-transformers)
    - VectorStore        → Base vectorielle pour le RAG
    - SemanticSearch     → Recherche semantique harmonique
"""

from .embeddings import HarmonicEmbeddings, compute_text_embedding
from .vector_store import VectorStore, DocumentChunk

__all__ = [
    'HarmonicEmbeddings', 'compute_text_embedding',
    'VectorStore', 'DocumentChunk',
]
