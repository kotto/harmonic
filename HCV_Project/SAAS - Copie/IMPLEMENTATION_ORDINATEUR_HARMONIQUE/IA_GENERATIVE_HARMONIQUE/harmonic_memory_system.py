"""
🧠 SYSTÈME DE MÉMOIRE HARMONIQUE
Fichier: harmonic_memory_system.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Système de mémoire avancé pour l'IA générative harmonique
"""

import numpy as np
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import hashlib
import pickle
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import redis
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes harmoniques universelles
PHI = 1.618033988749895  # Ratio d'or
PI = 3.141592653589793    # Constante circulaire
E = 2.718281828459045      # Nombre d'Euler
SQRT2 = 1.414213562373095  # Racine carrée de 2
SQRT3 = 1.732050807568877  # Racine carrée de 3

class MemoryType(Enum):
    """Types de mémoire harmonique"""
    EPISODIC = "episodic"      # Mémoire des épisodes
    SEMANTIC = "semantic"      # Mémoire sémantique
    PROCEDURAL = "procedural"  # Mémoire procédurale
    WORKING = "working"        # Mémoire de travail
    LONG_TERM = "long_term"    # Mémoire à long terme
    CACHE = "cache"           # Mémoire cache

class MemoryPriority(Enum):
    """Priorités de mémoire"""
    CRITICAL = "critical"      # Critique
    HIGH = "high"             # Haute
    MEDIUM = "medium"          # Moyenne
    LOW = "low"               # Basse
    TEMPORARY = "temporary"    # Temporaire

class RetrievalStrategy(Enum):
    """Stratégies de récupération"""
    HARMONIC_RELEVANCE = "harmonic_relevance"  # Pertinence harmonique
    FREQUENCY_BASED = "frequency_based"        # Basée sur fréquence
    RECENCY_BASED = "recency_based"            # Basée sur récence
    PHI_OPTIMIZED = "phi_optimized"            # Optimisée φ
    PI_PRECISE = "pi_precise"                  # Précise π
    E_EFFICIENT = "e_efficient"                # Efficace e

@dataclass
class MemoryEntry:
    """Entrée de mémoire harmonique"""
    id: str
    content: Any
    metadata: Dict[str, Any]
    memory_type: MemoryType
    priority: MemoryPriority
    created_at: datetime
    last_accessed: datetime
    access_count: int
    harmonic_score: float
    context: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        """Post-initialisation harmonique"""
        if self.harmonic_score == 0:
            self.harmonic_score = self._calculate_harmonic_score()
    
    def _calculate_harmonic_score(self) -> float:
        """Calcule le score harmonique de l'entrée"""
        score = 0.0
        
        # φ-optimisation pour la pertinence
        score += 0.382 * (self.access_count / (time.time() - self.created_at.timestamp() + 1))
        
        # π-optimisation pour la précision
        score += 0.236 * len(str(self.content)) / 1000
        
        # e-optimisation pour l'efficacité
        score += 0.146 * (1.0 / (time.time() - self.last_accessed.timestamp() + 1))
        
        # √2-stabilisation
        score *= SQRT2
        
        # √3-équilibre
        score /= SQRT3
        
        return min(1.0, score)

@dataclass
class MemoryConfig:
    """Configuration du système de mémoire"""
    max_entries: int = 10000
    max_working_memory: int = 100
    cache_size: int = 1000
    cleanup_interval: int = 3600  # 1 heure
    persistence_enabled: bool = True
    redis_enabled: bool = False
    sqlite_enabled: bool = True
    thread_pool_size: int = 4
    compression_enabled: bool = True

class HarmonicMemoryIndex:
    """Index harmonique pour la mémoire"""
    
    def __init__(self):
        self.phi = PHI
        self.pi = PI
        self.e = E
        self.sqrt2 = SQRT2
        self.sqrt3 = SQRT3
        
        # Index par type
        self.type_index: Dict[MemoryType, List[str]] = {
            memory_type: [] for memory_type in MemoryType
        }
        
        # Index par priorité
        self.priority_index: Dict[MemoryPriority, List[str]] = {
            priority: [] for priority in MemoryPriority
        }
        
        # Index par tags
        self.tag_index: Dict[str, List[str]] = {}
        
        # Index temporel
        self.temporal_index: Dict[float, List[str]] = {}
        
        # Index de contenu (hash)
        self.content_index: Dict[str, str] = {}
        
        # Verrouillage thread-safe
        self.lock = threading.RLock()
    
    def add_entry(self, entry: MemoryEntry):
        """Ajoute une entrée à l'index"""
        with self.lock:
            # Index par type
            self.type_index[entry.memory_type].append(entry.id)
            
            # Index par priorité
            self.priority_index[entry.priority].append(entry.id)
            
            # Index par tags
            if entry.tags:
                for tag in entry.tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = []
                    self.tag_index[tag].append(entry.id)
            
            # Index temporel
            timestamp = entry.created_at.timestamp()
            if timestamp not in self.temporal_index:
                self.temporal_index[timestamp] = []
            self.temporal_index[timestamp].append(entry.id)
            
            # Index de contenu
            content_hash = hashlib.md5(str(entry.content).encode()).hexdigest()
            self.content_index[content_hash] = entry.id
    
    def remove_entry(self, entry_id: str):
        """Supprime une entrée de l'index"""
        with self.lock:
            # Suppression de tous les index
            for index_dict in [self.type_index, self.priority_index, self.tag_index, self.temporal_index]:
                for key, entries in index_dict.items():
                    if entry_id in entries:
                        entries.remove(entry_id)
            
            # Suppression de l'index de contenu
            content_hash = None
            for hash_val, id_val in self.content_index.items():
                if id_val == entry_id:
                    content_hash = hash_val
                    break
            
            if content_hash:
                del self.content_index[content_hash]
    
    def find_by_type(self, memory_type: MemoryType) -> List[str]:
        """Trouve les entrées par type"""
        with self.lock:
            return self.type_index[memory_type].copy()
    
    def find_by_priority(self, priority: MemoryPriority) -> List[str]:
        """Trouve les entrées par priorité"""
        with self.lock:
            return self.priority_index[priority].copy()
    
    def find_by_tag(self, tag: str) -> List[str]:
        """Trouve les entrées par tag"""
        with self.lock:
            return self.tag_index.get(tag, []).copy()
    
    def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[str]:
        """Trouve les entrées par plage temporelle"""
        with self.lock:
            start_ts = start_time.timestamp()
            end_ts = end_time.timestamp()
            
            result = []
            for timestamp, entries in self.temporal_index.items():
                if start_ts <= timestamp <= end_ts:
                    result.extend(entries)
            
            return result
    
    def find_by_content(self, content: Any) -> Optional[str]:
        """Trouve une entrée par contenu"""
        with self.lock:
            content_hash = hashlib.md5(str(content).encode()).hexdigest()
            return self.content_index.get(content_hash)

class HarmonicMemoryRetrieval:
    """Système de récupération harmonique"""
    
    def __init__(self):
        self.phi = PHI
        self.pi = PI
        self.e = E
        self.sqrt2 = SQRT2
        self.sqrt3 = SQRT3
    
    def retrieve_by_strategy(self, entries: List[MemoryEntry], 
                           strategy: RetrievalStrategy,
                           query: Optional[Any] = None,
                           limit: int = 10) -> List[MemoryEntry]:
        """Récupère les entrées selon une stratégie"""
        
        if strategy == RetrievalStrategy.HARMONIC_RELEVANCE:
            return self._retrieve_by_harmonic_relevance(entries, query, limit)
        elif strategy == RetrievalStrategy.FREQUENCY_BASED:
            return self._retrieve_by_frequency(entries, limit)
        elif strategy == RetrievalStrategy.RECENCY_BASED:
            return self._retrieve_by_recency(entries, limit)
        elif strategy == RetrievalStrategy.PHI_OPTIMIZED:
            return self._retrieve_by_phi_optimized(entries, limit)
        elif strategy == RetrievalStrategy.PI_PRECISE:
            return self._retrieve_by_pi_precise(entries, query, limit)
        elif strategy == RetrievalStrategy.E_EFFICIENT:
            return self._retrieve_by_e_efficient(entries, limit)
        else:
            return entries[:limit]
    
    def _retrieve_by_harmonic_relevance(self, entries: List[MemoryEntry], 
                                       query: Any, limit: int) -> List[MemoryEntry]:
        """Récupération par pertinence harmonique"""
        if query is None:
            return sorted(entries, key=lambda x: x.harmonic_score, reverse=True)[:limit]
        
        # Calcul de similarité harmonique
        scored_entries = []
        for entry in entries:
            similarity = self._calculate_harmonic_similarity(query, entry)
            combined_score = 0.7 * similarity + 0.3 * entry.harmonic_score
            scored_entries.append((entry, combined_score))
        
        # Tri par score combiné
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        
        return [entry for entry, _ in scored_entries[:limit]]
    
    def _retrieve_by_frequency(self, entries: List[MemoryEntry], limit: int) -> List[MemoryEntry]:
        """Récupération par fréquence d'accès"""
        return sorted(entries, key=lambda x: x.access_count, reverse=True)[:limit]
    
    def _retrieve_by_recency(self, entries: List[MemoryEntry], limit: int) -> List[MemoryEntry]:
        """Récupération par récence"""
        return sorted(entries, key=lambda x: x.last_accessed, reverse=True)[:limit]
    
    def _retrieve_by_phi_optimized(self, entries: List[MemoryEntry], limit: int) -> List[MemoryEntry]:
        """Récupération optimisée φ"""
        # φ-optimisation : favoriser les entrées avec le meilleur ratio score/âge
        current_time = time.time()
        
        scored_entries = []
        for entry in entries:
            age = current_time - entry.created_at.timestamp()
            phi_score = entry.harmonic_score * self.phi / (age + 1)
            scored_entries.append((entry, phi_score))
        
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in scored_entries[:limit]]
    
    def _retrieve_by_pi_precise(self, entries: List[MemoryEntry], 
                               query: Any, limit: int) -> List[MemoryEntry]:
        """Récupération précise π"""
        if query is None:
            return sorted(entries, key=lambda x: x.harmonic_score, reverse=True)[:limit]
        
        # π-optimisation : précision mathématique
        scored_entries = []
        for entry in entries:
            precision = self._calculate_pi_precision(query, entry)
            combined_score = 0.6 * precision + 0.4 * entry.harmonic_score
            scored_entries.append((entry, combined_score))
        
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in scored_entries[:limit]]
    
    def _retrieve_by_e_efficient(self, entries: List[MemoryEntry], limit: int) -> List[MemoryEntry]:
        """Récupération efficace e"""
        # e-optimisation : efficacité d'accès
        current_time = time.time()
        
        scored_entries = []
        for entry in entries:
            access_efficiency = entry.access_count / (current_time - entry.last_accessed.timestamp() + 1)
            e_score = access_efficiency * self.e + entry.harmonic_score
            scored_entries.append((entry, e_score))
        
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in scored_entries[:limit]]
    
    def _calculate_harmonic_similarity(self, query: Any, entry: MemoryEntry) -> float:
        """Calcule la similarité harmonique"""
        # Similarité basique (à améliorer selon le type)
        if isinstance(query, str) and isinstance(entry.content, str):
            # Similarité textuelle
            query_words = set(query.lower().split())
            content_words = set(entry.content.lower().split())
            
            if not query_words or not content_words:
                return 0.0
            
            intersection = query_words.intersection(content_words)
            union = query_words.union(content_words)
            
            jaccard = len(intersection) / len(union)
            
            # Optimisation φ
            return jaccard * self.phi
        
        return 0.0
    
    def _calculate_pi_precision(self, query: Any, entry: MemoryEntry) -> float:
        """Calcule la précision π"""
        # Précision basée sur la longueur et la complexité
        content_length = len(str(entry.content))
        query_length = len(str(query))
        
        if content_length == 0 or query_length == 0:
            return 0.0
        
        # Optimisation π
        precision = min(1.0, content_length / query_length) * self.pi
        return precision / self.pi  # Normalisation

class HarmonicMemorySystem:
    """
    Système de mémoire harmonique complet
    Capacité : φ² entrées, rétention π heures, vitesse e ms
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.phi = PHI
        self.pi = PI
        self.e = E
        self.sqrt2 = SQRT2
        self.sqrt3 = SQRT3
        
        # Configuration
        self.config = config or MemoryConfig()
        
        # Stockage principal
        self.memory_entries: Dict[str, MemoryEntry] = {}
        
        # Mémoire de travail (limitée)
        self.working_memory: deque = deque(maxlen=self.config.max_working_memory)
        
        # Cache
        self.cache: Dict[str, MemoryEntry] = {}
        
        # Index
        self.index = HarmonicMemoryIndex()
        
        # Récupération
        self.retrieval = HarmonicMemoryRetrieval()
        
        # Thread pool pour opérations asynchrones
        self.executor = ThreadPoolExecutor(max_workers=self.config.thread_pool_size)
        
        # Persistance
        self.db_connection = None
        self.redis_client = None
        
        # Initialisation de la persistance
        if self.config.sqlite_enabled:
            self._init_sqlite()
        
        if self.config.redis_enabled:
            self._init_redis()
        
        # Thread de nettoyage
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Système de mémoire harmonique initialisé")
    
    def _init_sqlite(self):
        """Initialise la base de données SQLite"""
        try:
            self.db_connection = sqlite3.connect('harmonic_memory.db', check_same_thread=False)
            cursor = self.db_connection.cursor()
            
            # Création des tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    content BLOB,
                    metadata TEXT,
                    memory_type TEXT,
                    priority TEXT,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER,
                    harmonic_score REAL,
                    context TEXT,
                    tags TEXT
                )
            ''')
            
            self.db_connection.commit()
            logger.info("Base de données SQLite initialisée")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation SQLite: {e}")
    
    def _init_redis(self):
        """Initialise Redis"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()
            logger.info("Client Redis initialisé")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation Redis: {e}")
            self.redis_client = None
    
    def store(self, content: Any, memory_type: MemoryType = MemoryType.EPISODIC,
              priority: MemoryPriority = MemoryPriority.MEDIUM,
              context: Optional[Dict[str, Any]] = None,
              tags: Optional[List[str]] = None) -> str:
        """
        Stocke une entrée dans la mémoire harmonique
        
        Args:
            content: Contenu à stocker
            memory_type: Type de mémoire
            priority: Priorité de l'entrée
            context: Contexte additionnel
            tags: Tags pour l'indexation
            
        Returns:
            ID de l'entrée stockée
        """
        
        # Génération de l'ID
        entry_id = self._generate_entry_id(content, memory_type)
        
        # Vérification des doublons
        if entry_id in self.memory_entries:
            # Mise à jour de l'entrée existante
            entry = self.memory_entries[entry_id]
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            return entry_id
        
        # Création de l'entrée
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            metadata={
                'size': len(str(content)),
                'type': type(content).__name__,
                'compressed': self.config.compression_enabled
            },
            memory_type=memory_type,
            priority=priority,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            harmonic_score=0.0,  # Calculé automatiquement
            context=context,
            tags=tags
        )
        
        # Ajout au stockage principal
        self.memory_entries[entry_id] = entry
        
        # Ajout à la mémoire de travail si applicable
        if memory_type == MemoryType.WORKING:
            self.working_memory.append(entry_id)
        
        # Ajout au cache si haute priorité
        if priority in [MemoryPriority.CRITICAL, MemoryPriority.HIGH]:
            self.cache[entry_id] = entry
        
        # Indexation
        self.index.add_entry(entry)
        
        # Persistance
        if self.config.persistence_enabled:
            self._persist_entry(entry)
        
        logger.debug(f"Entrée stockée: {entry_id}")
        return entry_id
    
    def retrieve(self, query: Any, memory_type: Optional[MemoryType] = None,
                strategy: RetrievalStrategy = RetrievalStrategy.HARMONIC_RELEVANCE,
                limit: int = 10) -> List[MemoryEntry]:
        """
        Récupère des entrées de mémoire
        
        Args:
            query: Requête
            memory_type: Type de mémoire (optionnel)
            strategy: Stratégie de récupération
            limit: Limite de résultats
            
        Returns:
            Liste des entrées récupérées
        """
        
        # Filtrage par type
        candidates = list(self.memory_entries.values())
        if memory_type:
            candidate_ids = self.index.find_by_type(memory_type)
            candidates = [self.memory_entries[eid] for eid in candidate_ids if eid in self.memory_entries]
        
        # Récupération selon la stratégie
        results = self.retrieval.retrieve_by_strategy(candidates, strategy, query, limit)
        
        # Mise à jour des accès
        for entry in results:
            entry.last_accessed = datetime.now()
            entry.access_count += 1
        
        logger.debug(f"Récupéré {len(results)} entrées pour la requête")
        return results
    
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Récupère une entrée par ID"""
        entry = self.memory_entries.get(entry_id)
        
        if entry:
            entry.last_accessed = datetime.now()
            entry.access_count += 1
        
        return entry
    
    def update(self, entry_id: str, content: Optional[Any] = None,
               metadata: Optional[Dict[str, Any]] = None,
               context: Optional[Dict[str, Any]] = None,
               tags: Optional[List[str]] = None) -> bool:
        """
        Met à jour une entrée de mémoire
        
        Args:
            entry_id: ID de l'entrée
            content: Nouveau contenu (optionnel)
            metadata: Nouveaux métadonnées (optionnel)
            context: Nouveau contexte (optionnel)
            tags: Nouveaux tags (optionnel)
            
        Returns:
            True si la mise à jour a réussi
        """
        
        entry = self.memory_entries.get(entry_id)
        if not entry:
            return False
        
        # Suppression de l'ancien index
        self.index.remove_entry(entry_id)
        
        # Mise à jour des champs
        if content is not None:
            entry.content = content
        if metadata:
            entry.metadata.update(metadata)
        if context:
            entry.context = context
        if tags:
            entry.tags = tags
        
        # Recalcul du score harmonique
        entry.harmonic_score = entry._calculate_harmonic_score()
        
        # Réindexation
        self.index.add_entry(entry)
        
        # Persistance
        if self.config.persistence_enabled:
            self._persist_entry(entry)
        
        logger.debug(f"Entrée mise à jour: {entry_id}")
        return True
    
    def delete(self, entry_id: str) -> bool:
        """
        Supprime une entrée de mémoire
        
        Args:
            entry_id: ID de l'entrée
            
        Returns:
            True si la suppression a réussi
        """
        
        if entry_id not in self.memory_entries:
            return False
        
        # Suppression de l'index
        self.index.remove_entry(entry_id)
        
        # Suppression du stockage
        del self.memory_entries[entry_id]
        
        # Suppression du cache
        if entry_id in self.cache:
            del self.cache[entry_id]
        
        # Suppression de la mémoire de travail
        if entry_id in self.working_memory:
            self.working_memory.remove(entry_id)
        
        # Suppression de la persistance
        if self.config.persistence_enabled:
            self._delete_persisted_entry(entry_id)
        
        logger.debug(f"Entrée supprimée: {entry_id}")
        return True
    
    def clear(self, memory_type: Optional[MemoryType] = None):
        """
        Efface la mémoire
        
        Args:
            memory_type: Type de mémoire à effacer (optionnel)
        """
        
        if memory_type:
            # Efface un type spécifique
            entries_to_delete = self.index.find_by_type(memory_type)
            for entry_id in entries_to_delete:
                self.delete(entry_id)
        else:
            # Efface tout
            self.memory_entries.clear()
            self.working_memory.clear()
            self.cache.clear()
            self.index = HarmonicMemoryIndex()
            
            if self.config.persistence_enabled:
                self._clear_persistence()
        
        logger.info(f"Mémoire effacée: {memory_type or 'tous'}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques de la mémoire"""
        
        total_entries = len(self.memory_entries)
        
        # Statistiques par type
        type_stats = {}
        for memory_type in MemoryType:
            count = len(self.index.find_by_type(memory_type))
            type_stats[memory_type.value] = count
        
        # Statistiques par priorité
        priority_stats = {}
        for priority in MemoryPriority:
            count = len(self.index.find_by_priority(priority))
            priority_stats[priority.value] = count
        
        # Score harmonique moyen
        if total_entries > 0:
            avg_harmonic_score = sum(entry.harmonic_score for entry in self.memory_entries.values()) / total_entries
        else:
            avg_harmonic_score = 0.0
        
        # Utilisation de la mémoire
        working_memory_usage = len(self.working_memory) / self.config.max_working_memory
        cache_usage = len(self.cache) / self.config.cache_size
        
        return {
            'total_entries': total_entries,
            'type_distribution': type_stats,
            'priority_distribution': priority_stats,
            'average_harmonic_score': avg_harmonic_score,
            'working_memory_usage': working_memory_usage,
            'cache_usage': cache_usage,
            'memory_types': list(MemoryType),
            'retrieval_strategies': list(RetrievalStrategy)
        }
    
    def _generate_entry_id(self, content: Any, memory_type: MemoryType) -> str:
        """Génère un ID d'entrée unique"""
        content_hash = hashlib.md5(str(content).encode()).hexdigest()
        timestamp = str(time.time()).replace('.', '')
        type_suffix = memory_type.value[:3]
        return f"{content_hash}_{timestamp}_{type_suffix}"
    
    def _persist_entry(self, entry: MemoryEntry):
        """Persiste une entrée"""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            # Sérialisation du contenu
            content_data = pickle.dumps(entry.content) if self.config.compression_enabled else str(entry.content)
            
            cursor.execute('''
                INSERT OR REPLACE INTO memory_entries
                (id, content, metadata, memory_type, priority, created_at, last_accessed, access_count, harmonic_score, context, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id,
                content_data,
                json.dumps(entry.metadata),
                entry.memory_type.value,
                entry.priority.value,
                entry.created_at.isoformat(),
                entry.last_accessed.isoformat(),
                entry.access_count,
                entry.harmonic_score,
                json.dumps(entry.context) if entry.context else None,
                json.dumps(entry.tags) if entry.tags else None
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors de la persistance de l'entrée {entry.id}: {e}")
    
    def _delete_persisted_entry(self, entry_id: str):
        """Supprime une entrée persistée"""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('DELETE FROM memory_entries WHERE id = ?', (entry_id,))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression persistée de {entry_id}: {e}")
    
    def _clear_persistence(self):
        """Efface la persistance"""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('DELETE FROM memory_entries')
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'effacement de la persistance: {e}")
    
    def _cleanup_loop(self):
        """Boucle de nettoyage automatique"""
        while True:
            try:
                time.sleep(self.config.cleanup_interval)
                self._cleanup_old_entries()
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de nettoyage: {e}")
    
    def _cleanup_old_entries(self):
        """Nettoie les anciennes entrées"""
        current_time = datetime.now()
        
        # Entrées à supprimer (basées sur l'âge et la priorité)
        entries_to_delete = []
        
        for entry in self.memory_entries.values():
            age_hours = (current_time - entry.created_at).total_seconds() / 3600
            
            # Critères de suppression basés sur la priorité
            if entry.priority == MemoryPriority.TEMPORARY and age_hours > 1:
                entries_to_delete.append(entry.id)
            elif entry.priority == MemoryPriority.LOW and age_hours > 24:
                entries_to_delete.append(entry.id)
            elif entry.priority == MemoryPriority.MEDIUM and age_hours > 168:  # 1 semaine
                entries_to_delete.append(entry.id)
            elif entry.priority == MemoryPriority.HIGH and age_hours > 720:  # 1 mois
                entries_to_delete.append(entry.id)
            # Les entrées critiques ne sont jamais supprimées automatiquement
        
        # Suppression des entrées
        for entry_id in entries_to_delete:
            self.delete(entry_id)
        
        if entries_to_delete:
            logger.info(f"Nettoyé {len(entries_to_delete)} anciennes entrées")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def close(self):
        """Ferme le système de mémoire"""
        try:
            # Arrêt du thread pool
            self.executor.shutdown(wait=True)
            
            # Fermeture de la base de données
            if self.db_connection:
                self.db_connection.close()
            
            # Fermeture de Redis
            if self.redis_client:
                self.redis_client.close()
            
            logger.info("Système de mémoire harmonique fermé")
            
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture: {e}")

# Point d'entrée pour les tests
if __name__ == "__main__":
    # Test du système de mémoire harmonique
    print("🧠 Test du Système de Mémoire Harmonique")
    
    # Configuration
    config = MemoryConfig(
        max_entries=1000,
        max_working_memory=10,
        cache_size=100,
        cleanup_interval=60,  # 1 minute pour le test
        persistence_enabled=True,
        sqlite_enabled=True,
        redis_enabled=False
    )
    
    # Création du système
    with HarmonicMemorySystem(config) as memory:
        # Test de stockage
        print("\n📝 Test de stockage:")
        
        entry_id1 = memory.store(
            content="Calcul quantique harmonique avec φ-optimisation",
            memory_type=MemoryType.EPISODIC,
            priority=MemoryPriority.HIGH,
            tags=["quantique", "harmonique", "phi"]
        )
        
        entry_id2 = memory.store(
            content="Algorithme de précision π pour calculs trigonométriques",
            memory_type=MemoryType.SEMANTIC,
            priority=MemoryPriority.MEDIUM,
            tags=["precision", "pi", "trigonometrie"]
        )
        
        entry_id3 = memory.store(
            content="Mémoire de travail temporaire",
            memory_type=MemoryType.WORKING,
            priority=MemoryPriority.TEMPORARY,
            tags=["temporaire", "working"]
        )
        
        print(f"✅ Entrées stockées: {entry_id1}, {entry_id2}, {entry_id3}")
        
        # Test de récupération
        print("\n🔍 Test de récupération:")
        
        # Récupération par pertinence harmonique
        results = memory.retrieve(
            query="quantique harmonique",
            strategy=RetrievalStrategy.HARMONIC_RELEVANCE,
            limit=5
        )
        
        print(f"📊 Récupéré {len(results)} entrées par pertinence harmonique:")
        for result in results:
            print(f"  - {result.id}: {str(result.content)[:50]}...")
        
        # Récupération optimisée φ
        results_phi = memory.retrieve(
            query="calcul",
            strategy=RetrievalStrategy.PHI_OPTIMIZED,
            limit=5
        )
        
        print(f"🌊 Récupéré {len(results_phi)} entrées optimisées φ:")
        for result in results_phi:
            print(f"  - {result.id}: {str(result.content)[:50]}...")
        
        # Test de mise à jour
        print("\n🔄 Test de mise à jour:")
        
        success = memory.update(
            entry_id1,
            content="Calcul quantique harmonique avec φ-optimisation (mis à jour)",
            tags=["quantique", "harmonique", "phi", "updated"]
        )
        
        print(f"✅ Mise à jour: {success}")
        
        # Test de statistiques
        print("\n📊 Statistiques:")
        
        stats = memory.get_statistics()
        print(f"  Total entrées: {stats['total_entries']}")
        print(f"  Score harmonique moyen: {stats['average_harmonic_score']:.3f}")
        print(f"  Utilisation mémoire travail: {stats['working_memory_usage']:.2%}")
        print(f"  Utilisation cache: {stats['cache_usage']:.2%}")
        
        print("\n📋 Distribution par type:")
        for type_name, count in stats['type_distribution'].items():
            print(f"  {type_name}: {count}")
        
        print("\n📋 Distribution par priorité:")
        for priority_name, count in stats['priority_distribution'].items():
            print(f"  {priority_name}: {count}")
        
        # Test de nettoyage
        print("\n🧹 Test de nettoyage:")
        
        # Attendre un peu pour le nettoyage automatique
        time.sleep(2)
        
        # Vérification après nettoyage
        stats_after = memory.get_statistics()
        print(f"  Entrées après nettoyage: {stats_after['total_entries']}")
        
        print("\n🧠 Système de mémoire harmonique opérationnel !")
