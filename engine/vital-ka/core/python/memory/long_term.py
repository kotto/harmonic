"""
Long Term Memory — Memoire persistante avec oubli harmonique base sur le noyau ABC.
====================================================================================
Les souvenirs importants persistent, les autres s'eteignent progressivement
selon la loi de memoire non-locale d'Atangana-Baleanu.
"""

import json
import time
import logging
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..abc_kernel import abc_kernel_np, PHI, ALPHA

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Un element de memoire a long terme."""
    id: str
    content: str
    category: str = "general"
    importance: float = 0.5  # 0.0 (oubliable) a 1.0 (important)
    access_count: int = 0
    resonance_score: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: Optional[str] = None
    
    @property
    def age_hours(self) -> float:
        """Age en heures."""
        created = datetime.fromisoformat(self.created_at)
        delta = datetime.now() - created
        return delta.total_seconds() / 3600
    
    @property
    def decay_factor(self) -> float:
        """Facteur d'oubli harmonique selon le noyau ABC."""
        age = self.age_hours
        if age < 1:
            return 1.0
        # Utiliser le noyau ABC comme facteur d'oubli
        kernel = abc_kernel_np(int(age) + 1)
        return float(kernel[min(int(age), len(kernel) - 1)])
    
    @property
    def recall_score(self) -> float:
        """Score de rappel combine (importance * resonance * decay)."""
        return self.importance * (1.0 + self.resonance_score) * self.decay_factor * (1.0 + 0.1 * self.access_count)


class LongTermMemory:
    """
    Memoire a long terme avec oubli harmonique.
    
    Le noyau ABC determine naturellement quels souvenirs
    doivent etre conserves ou oublies.
    
    Usage:
        mem = LongTermMemory()
        
        # Ajouter un souvenir
        mem.remember("La capitale de la France est Paris", 
                     category="factual", importance=0.9)
        
        # Recuperer les souvenirs pertinents
        results = mem.recall("capitale", k=5)
        for r in results:
            print(f"[{r['importance']:.1f}] {r['content']}")
        
        # Nettoyage automatique (souvenirs oublies)
        mem.forget_old(similarity_threshold=0.3)
    """
    
    def __init__(self, max_items: int = 10000):
        self.max_items = max_items
        self.items: Dict[str, MemoryItem] = {}
        self._abc_kernel_cache = {}
    
    def remember(self, content: str, category: str = "general",
                 importance: float = 0.5, resonance_score: float = 0.0,
                 context: Optional[Dict] = None) -> str:
        """
        Ajoute un element en memoire.
        
        Args:
            content: Contenu a memoriser
            category: Categorie harmonique
            importance: 0.0 (oubliable) a 1.0 (tres important)
            resonance_score: Score de resonance harmonique
            context: Contexte additionnel
        
        Returns:
            ID du souvenir
        """
        memory_id = f"mem_{int(time.time() * 1000)}_{len(self.items)}"
        
        item = MemoryItem(
            id=memory_id,
            content=content,
            category=category,
            importance=importance,
            resonance_score=resonance_score,
            context=context or {},
        )
        
        self.items[memory_id] = item
        
        # Eviction si trop d'elements
        if len(self.items) > self.max_items:
            self._evict_lowest_recall()
        
        return memory_id
    
    def recall(self, query: str = "", category: Optional[str] = None,
               k: int = 10, min_score: float = 0.1) -> List[Dict]:
        """
        Recupere les souvenirs les plus pertinents.
        
        Args:
            query: Texte de recherche (simple matching)
            category: Filtrer par categorie
            k: Nombre maximum de resultats
            min_score: Score de rappel minimal
        
        Returns:
            Liste de souvenirs tries par pertinence
        """
        results = []
        query_lower = query.lower() if query else ""
        
        for item in self.items.values():
            # Filtrer par categorie
            if category and item.category != category:
                continue
            
            # Filtrer par requete
            if query_lower and query_lower not in item.content.lower():
                continue
            
            score = item.recall_score
            
            if score < min_score:
                continue
            
            # Incrementer l'acces
            item.access_count += 1
            item.last_accessed = datetime.now().isoformat()
            
            results.append({
                "id": item.id,
                "content": item.content,
                "category": item.category,
                "importance": round(item.importance, 3),
                "resonance_score": round(item.resonance_score, 3),
                "recall_score": round(score, 3),
                "age_hours": round(item.age_hours, 1),
                "access_count": item.access_count,
                "created_at": item.created_at,
            })
        
        # Trier par score de rappel
        results.sort(key=lambda r: r["recall_score"], reverse=True)
        
        return results[:k]
    
    def recall_by_category(self, category: str, k: int = 5) -> List[Dict]:
        """Recupere les meilleurs souvenirs d'une categorie."""
        return self.recall(category=category, k=k)
    
    def update_importance(self, memory_id: str, importance: float) -> bool:
        """Met a jour l'importance d'un souvenir."""
        if memory_id in self.items:
            self.items[memory_id].importance = max(0.0, min(1.0, importance))
            return True
        return False
    
    def forget(self, memory_id: str) -> bool:
        """Oublie (supprime) un souvenir specifique."""
        if memory_id in self.items:
            del self.items[memory_id]
            return True
        return False
    
    def forget_old(self, min_recall_score: float = 0.3):
        """Oublie les souvenirs les moins importants (scores bas)."""
        to_forget = [
            mid for mid, item in self.items.items()
            if item.recall_score < min_recall_score and item.age_hours > 24
        ]
        
        for mid in to_forget:
            del self.items[mid]
        
        if to_forget:
            logger.info(f"Oubli harmonique: {len(to_forget)} souvenirs effaces")
        
        return len(to_forget)
    
    def _evict_lowest_recall(self):
        """Eviction des souvenirs les moins importants."""
        if not self.items:
            return
        
        worst = min(self.items.items(), key=lambda x: x[1].recall_score)
        del self.items[worst[0]]
    
    def get_stats(self) -> Dict:
        """Stats de la memoire."""
        if not self.items:
            return {"total_items": 0, "avg_importance": 0, "avg_recall": 0}
        
        importances = [item.importance for item in self.items.values()]
        recalls = [item.recall_score for item in self.items.values()]
        
        categories = {}
        for item in self.items.values():
            categories[item.category] = categories.get(item.category, 0) + 1
        
        return {
            "total_items": len(self.items),
            "avg_importance": round(np.mean(importances), 3),
            "avg_recall_score": round(np.mean(recalls), 3),
            "categories": categories,
            "max_items": self.max_items,
        }
    
    def save(self, path: str):
        """Sauvegarde la memoire sur disque."""
        import pickle
        data = {
            "items": {
                mid: {
                    "id": item.id,
                    "content": item.content,
                    "category": item.category,
                    "importance": item.importance,
                    "access_count": item.access_count,
                    "resonance_score": item.resonance_score,
                    "context": item.context,
                    "created_at": item.created_at,
                    "last_accessed": item.last_accessed,
                }
                for mid, item in self.items.items()
            },
            "max_items": self.max_items,
        }
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Memoire sauvegardee: {len(self.items)} items -> {path}")
    
    def load(self, path: str) -> bool:
        """Charge la memoire depuis le disque."""
        import pickle
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.items = {}
            for mid, mdata in data["items"].items():
                self.items[mid] = MemoryItem(
                    id=mdata["id"],
                    content=mdata["content"],
                    category=mdata.get("category", "general"),
                    importance=mdata.get("importance", 0.5),
                    access_count=mdata.get("access_count", 0),
                    resonance_score=mdata.get("resonance_score", 0.0),
                    context=mdata.get("context", {}),
                    created_at=mdata.get("created_at", datetime.now().isoformat()),
                    last_accessed=mdata.get("last_accessed"),
                )
            
            self.max_items = data.get("max_items", 10000)
            
            logger.info(f"Memoire chargee: {len(self.items)} items <- {path}")
            return True
        
        except Exception as e:
            logger.warning(f"Impossible de charger la memoire: {e}")
            return False
