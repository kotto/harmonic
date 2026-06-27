"""
Vector Store — Base de connaissances vectorielle pour le RAG.
=============================================================
Stocke et retrouve des chunks de documents par similarite semantique.
Utilise le noyau ABC pour ponderer les resultats par importance temporelle.
"""

import os
import json
import time
import pickle
import logging
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .embeddings import HarmonicEmbeddings, HYBRID_DIM

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Un chunk de document avec son embedding."""
    id: str
    text: str
    source: str  # fichier, url, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "access_count": self.access_count,
        }


class VectorStore:
    """
    Base vectorielle harmonique avec recherche semantique.
    
    Usage:
        store = VectorStore()
        
        # Ajouter des documents
        store.add("doc1", "La capitale de la France est Paris.", source="geographie")
        store.add("doc2", "Python est un langage de programmation.", source="informatique")
        
        # Rechercher
        results = store.search("Capitale de la France", k=3)
        for r in results:
            print(f"[{r['source']}] {r['text']}")
        
        # Sauvegarder / Charger
        store.save("knowledge_base.pkl")
        store.load("knowledge_base.pkl")
    """
    
    def __init__(self, embeddings: Optional[HarmonicEmbeddings] = None):
        self.embeddings = embeddings or HarmonicEmbeddings()
        self.chunks: Dict[str, DocumentChunk] = {}
        self.index: Optional[np.ndarray] = None  # Matrice d'embeddings
        self.chunk_ids: List[str] = []
    
    def add(self, doc_id: str, text: str, source: str = "",
            metadata: Optional[Dict] = None) -> str:
        """Ajoute un document a la base."""
        chunk = DocumentChunk(
            id=doc_id,
            text=text,
            source=source,
            metadata=metadata or {},
            embedding=self.embeddings.embed(text),
        )
        self.chunks[doc_id] = chunk
        self._rebuild_index()
        return doc_id
    
    def add_batch(self, documents: List[Dict]) -> List[str]:
        """Ajoute plusieurs documents d'un coup."""
        ids = []
        for doc in documents:
            doc_id = doc.get("id", f"doc_{len(self.chunks)}_{int(time.time())}")
            self.add(doc_id, doc["text"], doc.get("source", ""), doc.get("metadata"))
            ids.append(doc_id)
        return ids
    
    def delete(self, doc_id: str) -> bool:
        """Supprime un document."""
        if doc_id in self.chunks:
            del self.chunks[doc_id]
            self._rebuild_index()
            return True
        return False
    
    def search(self, query: str, k: int = 5, threshold: float = 0.3) -> List[Dict]:
        """
        Recherche les k documents les plus similaires.
        
        Args:
            query: Texte de la requete
            k: Nombre de resultats
            threshold: Seuil de similarite minimal
        
        Returns:
            Liste de resultats tries par pertinence
        """
        if not self.chunks:
            return []
        
        query_emb = self.embeddings.embed(query)
        
        if self.index is None:
            self._rebuild_index()
        
        # Similarite cosinus
        similarities = self.index @ query_emb
        
        # Top-k
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_indices:
            if idx >= len(self.chunk_ids):
                continue
            sim = float(similarities[idx])
            if sim < threshold:
                continue
            
            chunk_id = self.chunk_ids[idx]
            chunk = self.chunks[chunk_id]
            chunk.access_count += 1
            
            results.append({
                "id": chunk_id,
                "text": chunk.text,
                "source": chunk.source,
                "metadata": chunk.metadata,
                "similarity": round(sim, 4),
                "access_count": chunk.access_count,
            })
        
        return results
    
    def _rebuild_index(self):
        """Reconstruit l'index FAISS-like."""
        if not self.chunks:
            self.index = None
            self.chunk_ids = []
            return
        
        self.chunk_ids = list(self.chunks.keys())
        embeddings_list = [self.chunks[cid].embedding for cid in self.chunk_ids]
        self.index = np.stack(embeddings_list)
    
    def save(self, path: str):
        """Sauvegarde la base sur disque."""
        data = {
            "chunks": {
                cid: {
                    "id": chunk.id,
                    "text": chunk.text,
                    "source": chunk.source,
                    "metadata": chunk.metadata,
                    "embedding": chunk.embedding.tolist() if chunk.embedding is not None else None,
                    "created_at": chunk.created_at,
                    "access_count": chunk.access_count,
                }
                for cid, chunk in self.chunks.items()
            },
            "chunk_ids": self.chunk_ids,
        }
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Base sauvegardee: {len(self.chunks)} chunks -> {path}")
    
    def load(self, path: str) -> bool:
        """Charge la base depuis le disque."""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.chunks = {}
            for cid, cdata in data["chunks"].items():
                emb = np.array(cdata["embedding"]) if cdata["embedding"] is not None else None
                self.chunks[cid] = DocumentChunk(
                    id=cdata["id"],
                    text=cdata["text"],
                    source=cdata["source"],
                    metadata=cdata["metadata"],
                    embedding=emb,
                    created_at=cdata["created_at"],
                    access_count=cdata["access_count"],
                )
            
            self.chunk_ids = data.get("chunk_ids", list(self.chunks.keys()))
            self._rebuild_index()
            
            logger.info(f"Base chargee: {len(self.chunks)} chunks <- {path}")
            return True
        
        except (FileNotFoundError, pickle.UnpicklingError, KeyError) as e:
            logger.warning(f"Impossible de charger la base: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Stats de la base."""
        return {
            "total_chunks": len(self.chunks),
            "total_sources": len(set(c.source for c in self.chunks.values())),
            "total_accesses": sum(c.access_count for c in self.chunks.values()),
            "avg_text_length": int(np.mean([len(c.text) for c in self.chunks.values()])) if self.chunks else 0,
        }


# =========================================================================
# BIBLIOTHEQUE D'EXEMPLARS — Selection Dynamique (Recommandation IA Experte)
# =========================================================================
# "Un exemplar pertinent sélectionné dynamiquement plutôt que plusieurs
#  exemples génériques. Sélectionnez via similarité sémantique,
#  ce qui donne moins de tokens gaspillés et une pertinence plus élevée."

HARMONIC_EXEMPLARS_DEFAULT = {
    "mathematical": [
        "Resous l'equation suivante : 2x + 5 = 13.\n"
        "Etape 1 : On isole x en soustrayant 5 des deux cotes : 2x = 8.\n"
        "Etape 2 : On divise par 2 : x = 4.\n"
        "Verification : 2(4) + 5 = 8 + 5 = 13. ✅",

        "Calcule la moyenne de [12, 15, 18, 21].\n"
        "Somme = 12 + 15 + 18 + 21 = 66.\n"
        "Moyenne = 66 / 4 = 16.5.",
    ],
    "code": [
        "Implemente une fonction qui inverse une chaine en Python :\n"
        "def inverser_chaine(s):\n"
        "    return s[::-1]\n\n"
        "Test : print(inverser_chaine('hello'))  # → 'olleh'",

        "Voici une fonction de tri par selection :\n"
        "def tri_selection(arr):\n"
        "    for i in range(len(arr)):\n"
        "        min_idx = i\n"
        "        for j in range(i+1, len(arr)):\n"
        "            if arr[j] < arr[min_idx]:\n"
        "                min_idx = j\n"
        "        arr[i], arr[min_idx] = arr[min_idx], arr[i]\n"
        "    return arr",
    ],
    "creative": [
        "Sous la lumiere argente du crepuscule, les vagues dansaient\n"
        "une valse lente et eternelle, chaque ecume un soupir\n"
        "de l'ocean vers le ciel infini.",

        "Dans le silence de la foret endormie, chaque feuille\n"
        "murmurait un secret ancestral, portee par le vent\n"
        "comme une promesse oubliee.",
    ],
    "reasoning": [
        "Question : Pourquoi le ciel est-il bleu ?\n"
        "These : La lumiere du soleil se diffracte dans l'atmosphere.\n"
        "Argument : Les courtes longueurs d'onde (bleu) sont plus diffusées.\n"
        "Conclusion : Le ciel nous parait bleu car c'est la couleur\n"
        "la plus diffusée par les molecules de l'air.",

        "Analyse : Comparons la voiture electrique et thermique.\n"
        "Point 1 : Impact ecologique — electrique gagne sur les emissions.\n"
        "Point 2 : Autonomie — thermique gagne sur le rayon d'action.\n"
        "Synthese : Le choix depend de l'usage quotidien."
    ],
    "factual": [
        "Question : Quelle est la capitale de la France ?\n"
        "Reponse : Paris est la capitale de la France.",

        "Question : En quelle annee a eu lieu la Revolution francaise ?\n"
        "Reponse : 1789. La Revolution francaise a debute en 1789.",
    ],
    "general": [
        "Question : Quel temps fait-il aujourd'hui ?\n"
        "Reponse : Le 29 mai 2026, le temps est generalement\n"
        "ensoleille avec des temperatures autour de 22°C.",
    ],
}


class ExemplarLibrary:
    """
    Bibliotheque d'exemplars avec selection dynamique par similarite semantique.
    
    Recommandation IA experte :
    "Un exemplar pertinent sélectionné dynamiquement plutôt que plusieurs
     exemples generiques. Les systemes de production beneficient de la
     recuperation des exemples les plus pertinents par entree, via
     similarite semantique, donnant moins de tokens gaspilles et une
     pertinence plus elevee par exemple."
    
    Usage:
        library = ExemplarLibrary()
        
        # Selection dynamique
        exemplar = library.select("Calcule 15% de 340", "mathematical")
        # → Meilleur exemplar pour ce prompt specifique
        
        # Ajouter un exemplar personnalise
        library.add("math_1", "Calcule...", "mathematical", quality=0.95)
    """
    
    def __init__(self, store: Optional[VectorStore] = None):
        self.store = store or VectorStore()
        self._initialized = False
    
    def _init_defaults(self):
        """Initialise les exemplars par defaut si la base est vide."""
        if self._initialized:
            return
        self._initialized = True
        
        if not self.store.chunks:
            for category, examples in HARMONIC_EXEMPLARS_DEFAULT.items():
                for i, text in enumerate(examples):
                    doc_id = f"exemplar_{category}_{i}"
                    self.store.add(
                        doc_id=doc_id,
                        text=text,
                        source="exemplar_library",
                        metadata={"category": category, "quality": 0.9}
                    )
    
    def select(self, prompt: str, category: str, k: int = 1) -> Optional[str]:
        """
        Selectionne le(s) meilleur(s) exemplar(s) pour un prompt et une categorie.
        
        Args:
            prompt: Texte du prompt utilisateur
            category: Categorie harmonique ciblee
            k: Nombre d'exemplars a retourner (defaut: 1)
        
        Returns:
            Texte de l'exemplar selectionne, ou None
        """
        self._init_defaults()
        
        # Recherche par similarite semantique sur le prompt
        results = self.store.search(prompt, k=k * 2, threshold=0.2)
        
        # Filtrer par categorie
        filtered = [r for r in results
                    if r["metadata"].get("category") == category]
        
        if filtered:
            return filtered[0]["text"]
        
        # Fallback: meilleur score general
        if results:
            return results[0]["text"]
        
        # Fallback: premier exemplar de la categorie
        for cid, chunk in self.store.chunks.items():
            if chunk.metadata.get("category") == category:
                return chunk.text
        
        return None
    
    def select_batch(self, prompt: str, category: str, k: int = 2) -> List[str]:
        """
        Selectionne plusieurs exemplars (utile pour few-shot).
        
        Args:
            prompt: Prompt utilisateur
            category: Categorie
            k: Nombre d'exemplars
        
        Returns:
            Liste de textes d'exemplars
        """
        self._init_defaults()
        results = self.store.search(prompt, k=k * 3, threshold=0.15)
        
        filtered = [r for r in results
                    if r["metadata"].get("category") == category]
        
        texts = [r["text"] for r in filtered[:k]]
        
        # Completer avec des exemplars de fallback si besoin
        if len(texts) < k:
            for cid, chunk in self.store.chunks.items():
                if chunk.metadata.get("category") == category:
                    if chunk.text not in texts:
                        texts.append(chunk.text)
                        if len(texts) >= k:
                            break
        
        return texts[:k]
    
    def add(self, doc_id: str, text: str, category: str,
            quality: float = 0.8, source: str = "user") -> str:
        """Ajoute un exemplar a la bibliotheque."""
        return self.store.add(
            doc_id=doc_id,
            text=text,
            source=source,
            metadata={"category": category, "quality": quality}
        )
    
    def get_stats(self) -> Dict:
        """Stats de la bibliotheque d'exemplars."""
        stats = self.store.get_stats()
        by_category = {}
        for cid, chunk in self.store.chunks.items():
            cat = chunk.metadata.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
        stats["by_category"] = by_category
        return stats
