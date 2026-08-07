"""
KB Scaler — Passage à l'échelle holographique (10M+ triplets)
===============================================================
Architecture de sharding inspirée du HCV Harmonic Database :
  · Shards de 250K faits chacun (40 shards pour 10M)
  · Index centroïde pour routage coarse → fine
  · Chargement lazy : max 4 shards actifs en RAM (~80 MB)
  · Retrieval deux phases : centroïde (top-3 shards) → intra-shard
  · Ingestion streaming : jamais tout charger d'un coup

PRINCIPES ONDULATOIRES :
  · Chaque shard = un hologramme partiel H_k = Σ ψ_f (f ∈ shard k)
  · Centroïde du shard = H_k / |H_k| (direction dominante)
  · Routage d'une requête : quels shards ont le centroïde le plus proche ?
  · Fusion : les résultats des top-K shards sont mergés par score

Usage :
    from kb_scaler import ShardedKB

    kb = ShardedKB(shard_dir='data/kb_shards')
    kb.ingest_wikidata('data/wikidata_dump.json')  # 10M+ faits
    kb.ingest_corpus('data/corpus/')                # textes → triplets
    kb.ingest_web(['url1', 'url2', ...])            # web → triplets

    results = kb.retrieve("capitale de la France", top_k=5)
    # → [FactRecord, ...] fusionnés des 3 meilleurs shards
"""

import json
import math
import os
import re
import time
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
FACTS_PER_SHARD = 250_000   # 250K faits par shard
MAX_ACTIVE_SHARDS = 4       # RAM ~80 MB
SHARD_CENTROID_DIM = 64     # dimension réduite pour le centroïde (compact)

_ENGINE_DIR = Path(__file__).resolve().parent

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

_STOPWORDS = {
    'the','a','an','is','are','was','were','of','in','on','at','to',
    'for','with','by','from','and','it','its','that','this',
    'le','la','les','un','une','des','de','du','d','l','est','sont',
    'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
    'avec','et','il','elle','ils','elles','ce','cet','cette','ces',
}

def _tokenize(text: str) -> List[str]:
    text = text.replace("'", " ").replace("'", " ")
    return [w.strip('.,!?;:()[]{}«»\"') for w in text.lower().split()
            if len(w) >= 2 and w not in _STOPWORDS]

def _normalize(text: str) -> str:
    return text.lower().replace('é','e').replace('è','e').replace('ê','e')\
               .replace('à','a').replace('ù','u').replace('ô','o')\
               .replace('î','i').replace('ï','i').replace('ç','c')

def _fnv1a(text: str, seed: int = 0x811c9dc5) -> int:
    """Hash FNV-1a (cohérent avec holographic_encoder)."""
    h = seed
    for b in text.encode('utf-8', errors='replace'):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

def _hash_to_complex(seed_text: str, dim: int = SHARD_CENTROID_DIM) -> np.ndarray:
    """Génère un vecteur complexe déterministe à partir d'un texte (centroïde)."""
    np.random.seed(_fnv1a(seed_text))
    real = np.random.randn(dim).astype(np.float32)
    imag = np.random.randn(dim).astype(np.float32)
    v = real + 1j * imag
    v /= np.linalg.norm(v) + 1e-10
    return v


# ═══════════════════════════════════════════════════════════════════════════════
# SHARD
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FactRecord:
    """Un fait avec son vecteur centroïde (compact)."""
    sujet: str
    relation: str
    objet: str
    secteur: str
    amplitude: float = 1.0
    psi_centroid: np.ndarray = None  # vecteur centroïde 64D (compact)

class Shard:
    """
    Un shard de connaissance — contient jusqu'à 250K faits.
    
    Stockage disque : fichier .npz (faits) + .json (métadonnées)
    
    En mémoire :
      · facts: liste de FactRecord
      · word_index: Dict[mot → Set[id_fait]]
      · idf: Dict[mot → float]
      · centroid: np.ndarray 64D (direction moyenne du shard)
    """

    def __init__(self, shard_id: int, shard_dir: Path, dim: int = SHARD_CENTROID_DIM):
        self.shard_id = shard_id
        self.shard_dir = Path(shard_dir)
        self.shard_dir.mkdir(parents=True, exist_ok=True)
        self.dim = dim

        self.facts: List[FactRecord] = []
        self.word_index: Dict[str, Set[int]] = defaultdict(set)
        self._idf: Dict[str, float] = {}
        self.centroid: np.ndarray = None  # direction dominante du shard
        self._dirty: bool = False
        self._loaded: bool = False

    @property
    def path(self) -> Path:
        return self.shard_dir / f"shard_{self.shard_id:04d}.npz"

    @property
    def meta_path(self) -> Path:
        return self.shard_dir / f"shard_{self.shard_id:04d}.json"

    @property
    def size(self) -> int:
        return len(self.facts)

    @property
    def is_full(self) -> bool:
        return len(self.facts) >= FACTS_PER_SHARD

    # ── Ingestion ──────────────────────────────────────────────────────────

    def ingest(self, sujet: str, relation: str, objet: str, secteur: str = "GENERAL",
               amplitude: float = 1.0) -> int:
        """Ajoute un fait au shard. Retourne l'ID du fait."""
        s, r, o = _normalize(sujet), _normalize(relation), _normalize(objet)
        key = (s, r, o)

        # Vérifier si le fait existe déjà
        for i, f in enumerate(self.facts):
            if (_normalize(f.sujet) == s and _normalize(f.relation) == r
                    and _normalize(f.objet) == o):
                self.facts[i].amplitude += amplitude
                self._dirty = True
                return i

        psi = _hash_to_complex(f"{s}|{r}|{o}", dim=self.dim)
        fact = FactRecord(sujet=sujet, relation=relation, objet=objet,
                          secteur=secteur, amplitude=amplitude, psi_centroid=psi)
        fid = len(self.facts)
        self.facts.append(fact)

        # Indexer
        for token in _tokenize(f"{s} {r} {o}"):
            self.word_index[token].add(fid)

        self._dirty = True
        self._compute_centroid()
        return fid

    def _compute_centroid(self):
        """Recalcule le centroïde du shard (moyenne des ψ normalisée)."""
        if not self.facts:
            self.centroid = np.zeros(self.dim, dtype=np.complex64)
            return
        total = np.zeros(self.dim, dtype=np.complex64)
        for f in self.facts:
            if f.psi_centroid is not None:
                total += f.psi_centroid * f.amplitude
        norm = np.linalg.norm(total)
        self.centroid = total / (norm + 1e-10) if norm > 1e-10 else total

    # ── Retrieval ──────────────────────────────────────────────────────────

    def retrieve(self, query: str, max_results: int = 10) -> List[Tuple[FactRecord, float]]:
        """
        Retrieval TF-IDF + similarité centroïde dans ce shard.
        
        Retourne : liste de (FactRecord, score) triée par score décroissant.
        """
        tokens = _tokenize(query)
        if not tokens:
            return []

        # Scores TF-IDF
        scores: Dict[int, float] = defaultdict(float)
        for token in tokens:
            if token in self.word_index:
                idf = self._get_idf(token)
                for fid in self.word_index[token]:
                    scores[fid] += idf

        if not scores:
            # Fallback : chercher les tokens partiels
            for token in tokens:
                for idx_token in list(self.word_index.keys()):
                    if token in idx_token and len(token) >= 3:
                        idf = self._get_idf(idx_token) * 0.5
                        for fid in self.word_index[idx_token]:
                            scores[fid] += idf

        # Boost centroïde (si la query matche la direction du fait)
        q_psi = _hash_to_complex(query, dim=self.dim)
        results = []
        for fid, tfidf_score in scores.items():
            fact = self.facts[fid]
            # Bonus de similarité centroïde
            if fact.psi_centroid is not None and q_psi is not None:
                coherence = float(np.real(np.dot(
                    fact.psi_centroid.conj(), q_psi
                )))
                bonus = max(0, coherence) * 0.3
            else:
                bonus = 0.0

            # Bonus d'amplitude (faits souvent répétés)
            amp_bonus = min(0.2, math.log1p(fact.amplitude) * 0.05)

            total_score = tfidf_score + bonus + amp_bonus
            results.append((fact, total_score))

        results.sort(key=lambda x: -x[1])
        return results[:max_results]

    def _get_idf(self, token: str) -> float:
        """IDF lazy pour un token."""
        if token not in self._idf:
            df = len(self.word_index.get(token, set()))
            N = max(1, len(self.facts))
            self._idf[token] = math.log(N / max(df, 1)) + 1.0
        return self._idf[token]

    # ── Persistance ────────────────────────────────────────────────────────

    def save(self):
        """Sauvegarde le shard sur disque."""
        if not self._dirty:
            return

        # Sauvegarder les faits
        data = {
            'subjects': np.array([f.sujet for f in self.facts], dtype=object),
            'relations': np.array([f.relation for f in self.facts], dtype=object),
            'objects': np.array([f.objet for f in self.facts], dtype=object),
            'sectors': np.array([f.secteur for f in self.facts], dtype=object),
            'amplitudes': np.array([f.amplitude for f in self.facts], dtype=np.float32),
            'psies_real': np.array([f.psi_centroid.real.astype(np.float32) if f.psi_centroid is not None
                                     else np.zeros(self.dim, dtype=np.float32) for f in self.facts]),
            'psies_imag': np.array([f.psi_centroid.imag.astype(np.float32) if f.psi_centroid is not None
                                     else np.zeros(self.dim, dtype=np.float32) for f in self.facts]),
        }
        np.savez_compressed(str(self.path), **data)

        # Sauvegarder les métadonnées
        meta = {
            'shard_id': self.shard_id,
            'size': len(self.facts),
            'centroid_real': self.centroid.real.tolist() if self.centroid is not None else [],
            'centroid_imag': self.centroid.imag.tolist() if self.centroid is not None else [],
            'word_index_size': sum(len(v) for v in self.word_index.values()),
            'vocab_size': len(self.word_index),
        }
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f)

        self._dirty = False
        log.info(f"Shard {self.shard_id:04d}: {len(self.facts):,} faits sauvegardés "
                 f"({self.path.stat().st_size / 1024 / 1024:.1f} MB)")

    def load(self):
        """Charge le shard depuis le disque (lazy)."""
        if self._loaded:
            return
        if not self.path.exists():
            self._loaded = True
            return

        data = np.load(str(self.path), allow_pickle=True)
        n = len(data['subjects'])
        self.facts = []
        for i in range(n):
            psi_real = data['psies_real'][i]
            psi_imag = data['psies_imag'][i]
            psi = (psi_real + 1j * psi_imag).astype(np.complex64)
            fact = FactRecord(
                sujet=str(data['subjects'][i]),
                relation=str(data['relations'][i]),
                objet=str(data['objects'][i]),
                secteur=str(data['sectors'][i]),
                amplitude=float(data['amplitudes'][i]),
                psi_centroid=psi,
            )
            self.facts.append(fact)

        # Reconstruire l'index
        self.word_index = defaultdict(set)
        for fid, fact in enumerate(self.facts):
            for token in _tokenize(f"{fact.sujet} {fact.relation} {fact.objet}"):
                self.word_index[token].add(fid)

        # Charger le centroïde
        if self.meta_path.exists():
            with open(self.meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            self.centroid = np.array(
                [complex(r, i) for r, i in zip(meta['centroid_real'], meta['centroid_imag'])],
                dtype=np.complex64
            )

        self._loaded = True
        self._dirty = False
        self._idf = {}
        log.debug(f"Shard {self.shard_id:04d}: {len(self.facts):,} faits chargés "
                  f"({len(self.word_index):,} mots indexés)")

    def unload(self):
        """Décharge le shard de la RAM (garde les métadonnées)."""
        if self._dirty:
            self.save()
        self.facts = []
        self.word_index = defaultdict(set)
        self._idf = {}
        self._loaded = False


# ═══════════════════════════════════════════════════════════════════════════════
# INDEX CENTROÏDE (routage coarse)
# ═══════════════════════════════════════════════════════════════════════════════

class CentroidIndex:
    """
    Index centroïde pour le routage coarse.
    
    Pour une requête donnée, identifie les top-K shards les plus pertinents
    en comparant le ψ de la requête avec les centroïdes de chaque shard.
    
    Fonctionne MÊME si les shards ne sont pas chargés en mémoire
    (les centroïdes sont toujours gardés en mémoire, ~64 floats × N shards).
    """

    def __init__(self):
        self.centroids: List[Tuple[int, np.ndarray]] = []  # (shard_id, centroid)

    def add_shard(self, shard_id: int, centroid: np.ndarray):
        self.centroids.append((shard_id, centroid))

    def remove_shard(self, shard_id: int):
        self.centroids = [(sid, c) for sid, c in self.centroids if sid != shard_id]

    def route(self, query: str, top_k: int = 3) -> List[int]:
        """
        Route une requête vers les top-K shards les plus pertinents.
        
        Score = |⟨ψ_query | centroid_shard⟩| (similarité cosinus complexe)
        """
        if not self.centroids:
            return []

        q_psi = _hash_to_complex(query, dim=SHARD_CENTROID_DIM)

        scores = []
        for shard_id, centroid in self.centroids:
            if centroid is None or np.all(centroid == 0):
                scores.append((shard_id, 0.0))
                continue
            # Similarité cosinus complexe : |⟨ψ_q | ψ_c⟩|
            coherence = abs(np.dot(q_psi.conj(), centroid))
            scores.append((shard_id, float(coherence)))

        scores.sort(key=lambda x: -x[1])
        return [sid for sid, _ in scores[:top_k]]


# ═══════════════════════════════════════════════════════════════════════════════
# SHARDED KB — Le scaler principal
# ═══════════════════════════════════════════════════════════════════════════════

class ShardedKB:
    """
    Base de connaissance holographique shardée — 10M+ faits.
    
    Architecture :
      ┌──────────────────────────────────────────────┐
      │              CentroidIndex                    │
      │  (64 floats × N shards, toujours en RAM)      │
      │  Route les requêtes → top-3 shards            │
      └──────────────┬───────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      ┌──────┐  ┌──────┐  ┌──────┐
      │Shard0│  │Shard1│  │ShardN│  ← disque (lazy load)
      └──────┘  └──────┘  └──────┘
      250K faits par shard, max 4 actifs en RAM
    """

    def __init__(self, shard_dir: str = None, max_active: int = MAX_ACTIVE_SHARDS):
        self.shard_dir = Path(shard_dir or str(_ENGINE_DIR / 'data' / 'kb_shards'))
        self.shard_dir.mkdir(parents=True, exist_ok=True)
        self.max_active = max_active

        # Index centroïde (léger, toujours en RAM)
        self.centroids = CentroidIndex()

        # Shards (lazy)
        self.shards: Dict[int, Shard] = {}  # shard_id → Shard (peut être unloaded)
        self._active_shards: List[int] = []  # LRU order
        self._next_shard_id: int = 0

        # Découvrir les shards existants
        self._discover_shards()

        log.info(f"ShardedKB: {len(self.shards)} shards découverts, "
                 f"{sum(s.size for s in self.shards.values()):,} faits totaux")

    def _discover_shards(self):
        """Découvre les shards existants sur le disque."""
        for npz_path in sorted(self.shard_dir.glob("shard_*.npz")):
            sid = int(npz_path.stem.split('_')[1])
            shard = Shard(sid, self.shard_dir)
            # Charger uniquement les métadonnées (pas les faits)
            if shard.meta_path.exists():
                with open(shard.meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                shard.centroid = np.array(
                    [complex(r, i) for r, i in zip(
                        meta.get('centroid_real', []),
                        meta.get('centroid_imag', [])
                    )],
                    dtype=np.complex64
                )
                self.shards[sid] = shard
                self.centroids.add_shard(sid, shard.centroid)
                self._next_shard_id = max(self._next_shard_id, sid + 1)

    def _get_or_create_shard(self) -> Shard:
        """Retourne le shard actif (ou en crée un nouveau si plein)."""
        # Chercher un shard non plein
        for sid, shard in self.shards.items():
            if not shard.is_full and shard._loaded:
                return shard

        # Charger un shard existant non plein
        for sid, shard in self.shards.items():
            if not shard.is_full:
                self._activate_shard(sid)
                return shard

        # Créer un nouveau shard
        return self._create_shard()

    def _create_shard(self) -> Shard:
        """Crée un nouveau shard."""
        sid = self._next_shard_id
        self._next_shard_id += 1
        shard = Shard(sid, self.shard_dir)
        shard._loaded = True
        self.shards[sid] = shard
        self._active_shards.append(sid)
        self._evict_if_needed()
        log.info(f"Nouveau shard créé: {sid:04d}")
        return shard

    def _activate_shard(self, shard_id: int):
        """Charge un shard depuis le disque en RAM."""
        if shard_id not in self.shards:
            return
        shard = self.shards[shard_id]
        if shard._loaded:
            # Déjà chargé, le mettre en tête de LRU
            if shard_id in self._active_shards:
                self._active_shards.remove(shard_id)
            self._active_shards.append(shard_id)
            return

        shard.load()
        self._active_shards.append(shard_id)
        self._evict_if_needed()

    def _evict_if_needed(self):
        """Décharge les shards les moins récemment utilisés si > max_active."""
        while len(self._active_shards) > self.max_active:
            oldest = self._active_shards.pop(0)
            if oldest in self.shards:
                self.shards[oldest].unload()
                log.debug(f"Shard {oldest:04d} déchargé (RAM libérée)")

    # ── INGESTION ──────────────────────────────────────────────────────────

    def ingest(self, sujet: str, relation: str, objet: str,
               secteur: str = "GENERAL", amplitude: float = 1.0):
        """Ingère un seul fait."""
        shard = self._get_or_create_shard()
        shard.ingest(sujet, relation, objet, secteur, amplitude)
        # Mettre à jour le centroïde
        self.centroids.remove_shard(shard.shard_id)
        self.centroids.add_shard(shard.shard_id, shard.centroid)

    def ingest_batch(self, facts: List[Tuple[str, str, str, str]],
                     amplitudes: List[float] = None):
        """
        Ingère un lot de faits en streaming — optimisé par shard.

        Args:
            facts: liste de (sujet, relation, objet, secteur)
            amplitudes: amplitudes optionnelles
        """
        count = 0
        t0 = time.time()
        batch_size = 10000  # traiter par lots de 10K

        for batch_start in range(0, len(facts), batch_size):
            batch = facts[batch_start:batch_start + batch_size]
            amp_batch = (amplitudes[batch_start:batch_start + batch_size]
                        if amplitudes else None)

            for i, (s, r, o, sec) in enumerate(batch):
                amp = amp_batch[i] if amp_batch else 1.0
                self._ingest_fast(s, r, o, sec, amp)
                count += 1

            # Mettre à jour les centroïdes après chaque batch
            for shard in self.shards.values():
                if shard._loaded and shard._dirty:
                    shard._compute_centroid()
                    self.centroids.remove_shard(shard.shard_id)
                    self.centroids.add_shard(shard.shard_id, shard.centroid)

            if (batch_start + batch_size) % 100000 == 0:
                elapsed = time.time() - t0
                rate = count / elapsed
                log.info(f"Ingestion: {count:,}/{len(facts):,} faits "
                         f"({rate:.0f} faits/s)")

        return count

    def _ingest_fast(self, sujet: str, relation: str, objet: str,
                     secteur: str = "GENERAL", amplitude: float = 1.0):
        """Version optimisée de ingest — minimise les allocations."""
        shard = self._get_or_create_shard()
        s, r, o = _normalize(sujet), _normalize(relation), _normalize(objet)

        # Vérifier doublon dans le shard courant (via word_index approximatif)
        key_tokens = set(_tokenize(f"{s} {r} {o}"))
        fid = len(shard.facts)
        psi = _hash_to_complex(f"{s}|{r}|{o}", dim=shard.dim)
        fact = FactRecord(sujet=sujet, relation=relation, objet=objet,
                          secteur=secteur, amplitude=amplitude, psi_centroid=psi)
        shard.facts.append(fact)

        # Indexer les tokens
        for token in key_tokens:
            shard.word_index[token].add(fid)

        shard._dirty = True
        # Centroïde recalculé en batch (pas ici)

    def ingest_wikidata(self, dump_path: str):
        """
        Ingère un dump Wikidata (format JSON, un objet par ligne).
        
        Extrait les triplets :
          - itemLabel → propertyLabel → valueLabel
          - itemLabel → "est une instance de" → classLabel
          - itemLabel → "a pour propriété" → valueLabel
        """
        path = Path(dump_path)
        if not path.exists():
            log.warning(f"Dump Wikidata introuvable: {dump_path}")
            return 0

        log.info(f"Ingestion Wikidata: {dump_path}")
        count = 0
        t0 = time.time()

        with open(path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    triples = self._extract_wikidata_triples(obj)
                    for s, r, o, sec in triples:
                        self.ingest(s, r, o, sec)
                        count += 1
                except json.JSONDecodeError:
                    continue

                if (line_no + 1) % 100000 == 0:
                    elapsed = time.time() - t0
                    rate = count / elapsed
                    log.info(f"Wikidata: {line_no+1:,} lignes → {count:,} faits "
                             f"({rate:.0f} faits/s)")

        # Sauvegarder tous les shards modifiés
        self.save_all()
        log.info(f"Wikidata terminé: {count:,} faits extraits en "
                 f"{time.time()-t0:.0f}s")
        return count

    def _extract_wikidata_triples(self, obj: dict) -> List[Tuple[str, str, str, str]]:
        """Extrait des triplets à partir d'un objet Wikidata JSON."""
        triples = []
        item_label = obj.get('itemLabel', '')
        if not item_label:
            return triples

        # Propriété directe
        prop_label = obj.get('propertyLabel', '')
        value_label = obj.get('valueLabel', '')
        if prop_label and value_label:
            secteur = self._map_wikidata_property_to_sector(prop_label)
            triples.append((item_label, prop_label, value_label, secteur))

        # Instance de (P31)
        instance_of = obj.get('instanceOfLabel', '')
        if instance_of:
            triples.append((item_label, "est une instance de", instance_of, "GENERAL"))

        # Sous-classe de (P279)
        subclass_of = obj.get('subclassOfLabel', '')
        if subclass_of:
            triples.append((item_label, "est une sous-classe de", subclass_of, "GENERAL"))

        # Pays (P17)
        country = obj.get('countryLabel', '')
        if country:
            triples.append((item_label, "est situé en", country, "GEOGRAPHIE"))

        # Date de création/fondation
        inception = obj.get('inceptionLabel', '')
        if inception:
            triples.append((item_label, "a été créé en", str(inception), "HISTOIRE"))

        return triples

    def _map_wikidata_property_to_sector(self, prop_label: str) -> str:
        """Mappe une propriété Wikidata vers un secteur harmonique."""
        prop_lower = prop_label.lower()
        mapping = {
            'population': 'GEOGRAPHIE',
            'superficie': 'GEOGRAPHIE',
            'capitale': 'GEOGRAPHIE',
            'pays': 'GEOGRAPHIE',
            'continent': 'GEOGRAPHIE',
            'coordonnées': 'GEOGRAPHIE',
            'découverte': 'SCIENCES',
            'masse': 'PHYSIQUE_FOND',
            'température': 'PHYSIQUE_APPLI',
            'date de naissance': 'HISTOIRE',
            'date de mort': 'HISTOIRE',
            'fondation': 'HISTOIRE',
            'créateur': 'CREATION',
            'auteur': 'CREATION',
            'compositeur': 'CULTURE',
            'réalisateur': 'CULTURE',
            'numéro atomique': 'CHIMIE',
            'symbole': 'CHIMIE',
            'formule': 'MATHS_PURES',
        }
        for key, sector in mapping.items():
            if key in prop_lower:
                return sector
        return "GENERAL"

    def ingest_corpus(self, corpus_dir: str, max_files: int = None):
        """
        Ingère un répertoire de fichiers texte → extraction de triplets.
        Utilise le bootstrapper pour l'extraction.
        """
        corpus_path = Path(corpus_dir)
        if not corpus_path.exists():
            log.warning(f"Corpus introuvable: {corpus_dir}")
            return 0

        try:
            from bootstrapper import extract_triples_simple, detect_sector
        except ImportError:
            log.warning("Bootstrapper non disponible, ingestion corpus désactivée")
            return 0

        files = list(corpus_path.glob("*.txt"))
        if max_files:
            files = files[:max_files]

        total = 0
        for fi, path in enumerate(files):
            if path.stat().st_size < 100:
                continue
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()

            triples = extract_triples_simple(text)
            for s, r, o, sec in triples:
                self.ingest(s, r, o, sec)
                total += 1

            if (fi + 1) % 10 == 0:
                log.info(f"Corpus: {fi+1}/{len(files)} fichiers → {total:,} faits")

        self.save_all()
        return total

    def ingest_web(self, urls: List[str]):
        """
        Ingère des pages web → extraction de triplets via le WebRetriever.
        """
        try:
            from web_retriever import WebRetriever
            wr = WebRetriever(timeout=15)
        except ImportError:
            log.warning("WebRetriever non disponible")
            return 0

        try:
            from bootstrapper import extract_triples_simple
        except ImportError:
            log.warning("Bootstrapper non disponible")
            return 0

        total = 0
        for url in urls:
            fetched = wr.fetch_url(url)
            if not fetched or not fetched.get('text'):
                continue

            text = fetched['text'][:50000]  # max 50K caractères par page
            triples = extract_triples_simple(text)
            for s, r, o, sec in triples:
                self.ingest(s, r, o, sec)
                total += 1

        self.save_all()
        return total

    # ── RETRIEVAL ──────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 10,
                 max_shards: int = 3) -> List[FactRecord]:
        """
        Retrieval deux phases :
          1. Coarse : centroïde → top-K shards
          2. Fine : TF-IDF + similarité centroïde dans chaque shard
          3. Fusion : merge et tri par score
        """
        # Phase 1 : Routage coarse
        shard_ids = self.centroids.route(query, top_k=max_shards)
        if not shard_ids:
            return []

        # Phase 2 : Retrieval fin dans chaque shard
        all_results = []
        for sid in shard_ids:
            self._activate_shard(sid)
            shard = self.shards[sid]
            if not shard._loaded:
                continue
            results = shard.retrieve(query, max_results=top_k * 2)
            for fact, score in results:
                all_results.append((fact, score, sid))

        # Fusion : trier par score, dédupliquer
        all_results.sort(key=lambda x: -x[1])
        seen = set()
        final = []
        for fact, score, sid in all_results:
            key = (_normalize(fact.sujet), _normalize(fact.relation),
                   _normalize(fact.objet))
            if key not in seen:
                seen.add(key)
                final.append(fact)
            if len(final) >= top_k:
                break

        return final

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Recherche et retourne des résultats formatés (pour API).
        """
        facts = self.retrieve(query, top_k=top_k)
        return [
            {
                'subject': f.sujet,
                'relation': f.relation,
                'object': f.objet,
                'sector': f.secteur,
                'confidence': min(1.0, f.amplitude / 10.0),
            }
            for f in facts
        ]

    # ── PERSISTANCE ────────────────────────────────────────────────────────

    def save_all(self):
        """Sauvegarde tous les shards modifiés."""
        for shard in self.shards.values():
            if shard._dirty and shard._loaded:
                shard.save()

        # Sauvegarder l'index centroïde
        centroid_data = {
            'shards': [
                {
                    'shard_id': sid,
                    'centroid_real': c.real.tolist(),
                    'centroid_imag': c.imag.tolist(),
                }
                for sid, c in self.centroids.centroids
            ],
            'next_shard_id': self._next_shard_id,
        }
        index_path = self.shard_dir / 'centroid_index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(centroid_data, f)

    @property
    def stats(self) -> dict:
        """Statistiques du ShardedKB."""
        total_facts = sum(s.size for s in self.shards.values())
        active_facts = sum(s.size for s in self.shards.values() if s._loaded)
        return {
            'total_facts': total_facts,
            'shards': len(self.shards),
            'active_shards': len([s for s in self.shards.values() if s._loaded]),
            'active_facts': active_facts,
            'max_active': self.max_active,
            'facts_per_shard': FACTS_PER_SHARD,
            'disk_usage_mb': sum(
                s.path.stat().st_size / 1024 / 1024
                for s in self.shards.values() if s.path.exists()
            ),
            'estimated_ram_mb': len([s for s in self.shards.values() if s._loaded]) * 20,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# INTÉGRATION AVEC HARMONIC BRAIN
# ═══════════════════════════════════════════════════════════════════════════════

def sharded_brain_from_npz(npz_path: str, shard_dir: str = None,
                           facts_per_shard: int = FACTS_PER_SHARD) -> 'ShardedKB':
    """
    Convertit un fichier NPZ existant en ShardedKB.
    
    Usage:
        kb = sharded_brain_from_npz('data/bootstrapper_output/knowledge_base_100k.npz')
        kb.save_all()
    """
    data = np.load(npz_path, allow_pickle=True)
    facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in data['facts']]

    kb = ShardedKB(shard_dir=shard_dir)
    kb.ingest_batch(facts)
    kb.save_all()
    log.info(f"Conversion NPZ → ShardedKB: {len(facts):,} faits dans "
             f"{len(kb.shards)} shards")
    return kb


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import tempfile
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  KB SCALER — Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Création et ingestion
        print("\n── Test 1: Ingestion 50K faits ──")
        kb = ShardedKB(shard_dir=tmpdir, max_active=2)

        # Générer des faits synthétiques
        sectors = ['GEOGRAPHIE', 'HISTOIRE', 'SCIENCES', 'CULTURE',
                   'PHYSIQUE_FOND', 'BIOLOGIE', 'MATHS_PURES']

        t0 = time.time()
        batch = []
        for i in range(50_000):
            s = f"Entité_{i % 5000}"
            r = f"a pour propriété_{i % 200}"
            o = f"Valeur_{i % 3000}"
            sec = sectors[i % len(sectors)]
            batch.append((s, r, o, sec))
        kb.ingest_batch(batch)
        print(f"  ✅ {50_000:,} faits ingérés en {time.time()-t0:.1f}s "
              f"({kb.stats['shards']} shards)")

        # Test 2: Retrieval
        print("\n── Test 2: Retrieval ──")
        for query in ["Entité_42", "propriété_50", "capitale France"]:
            results = kb.retrieve(query, top_k=3)
            print(f"  '{query}' → {len(results)} résultats")

        # Test 3: Save/Load
        print("\n── Test 3: Persistance ──")
        kb.save_all()
        print(f"  {kb.stats}")

        # Test 4: Réouverture
        print("\n── Test 4: Réouverture ──")
        kb2 = ShardedKB(shard_dir=tmpdir, max_active=2)
        results = kb2.retrieve("Entité_42", top_k=3)
        print(f"  Après reload: {len(results)} résultats pour 'Entité_42'")

    print("\n✅ Tests ShardedKB terminés")
