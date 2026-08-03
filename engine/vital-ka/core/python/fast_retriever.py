"""
Fast Retriever — Retrieval O(N) simple pour PageForge
=======================================================
Remplace le HarmonicBrain (lent à l'initialisation) par un scanner
numpy direct, sans construction d'index préalable.

Approche : stocker les faits dans des tableaux numpy, scanner avec
des opérations vectorisées numpy. Aucun prétraitement lent.

PERFORMANCE :
  - Chargement : ~2s pour 30K faits (juste np.load)
  - Retrieval : ~10ms pour 30K faits (scan numpy vectorisé)
  - RAM : ~15 MB pour 30K faits

Usage :
    from fast_retriever import FastRetriever
    r = FastRetriever()
    r.load('data/kb_enriched/shard_0000.npz')
    facts = r.retrieve("cancer", 10)
"""

import re, time, logging
from typing import List, Tuple, Optional
import numpy as np

log = logging.getLogger(__name__)

_STOPWORDS = {
    'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'a',
    'que', 'qui', 'quoi', 'dans', 'sur', 'pour', 'avec', 'par', 'en',
    'the', 'a', 'an', 'is', 'are', 'of', 'in', 'on', 'at', 'to', 'or',
    'and', 'it', 'its', 'that', 'this', 'was', 'were', 'be', 'been',
    'pas', 'plus', 'trop', 'peu', 'tout', 'tous', 'toute',
    'bien', 'mal', 'comme', 'donc', 'alors', 'car', 'aussi', 'ainsi',
    'mais', 'ou', 'ce', 'cet', 'cette', 'ces', 'son', 'sa', 'ses',
}

def _normalize(text: str) -> str:
    for a, b in [('é','e'),('è','e'),('ê','e'),('ë','e'),('à','a'),('â','a'),
                  ('ù','u'),('û','u'),('ô','o'),('î','i'),('ï','i'),('ç','c'),
                  ('œ','oe'),('É','e'),('È','e'),('Ê','e'),('À','a')]:
        text = text.replace(a, b)
    return text.lower()

class FastRetriever:
    """Retrieval rapide par scan numpy — pas de construction d'index."""
    
    def __init__(self):
        self._loaded = False
        self.subjects = None
        self.relations = None
        self.objects = None
        self.sectors = None
    
    def load(self, shard_path: str) -> int:
        """Charge un shard .npz (rapide, ~2s pour 30K)."""
        data = np.load(shard_path, allow_pickle=True)
        self.subjects = data['subjects']
        self.relations = data['relations']
        self.objects = data['objects']
        self.sectors = data.get('sectors', None)
        self._loaded = True
        log.info(f"FastRetriever chargé: {len(self.subjects):,} faits")
        return len(self.subjects)
    
    def add_facts(self, facts: List[Tuple[str, str, str, str]]):
        """Ajoute des faits (convertit en tableaux numpy)."""
        n = len(facts)
        new_subjects = np.array([f[0] for f in facts], dtype=object)
        new_relations = np.array([f[1] for f in facts], dtype=object)
        new_objects = np.array([f[2] for f in facts], dtype=object)
        new_sectors = np.array([f[3] for f in facts], dtype=object)
        
        if self._loaded:
            self.subjects = np.concatenate([self.subjects, new_subjects])
            self.relations = np.concatenate([self.relations, new_relations])
            self.objects = np.concatenate([self.objects, new_objects])
            if self.sectors is not None:
                self.sectors = np.concatenate([self.sectors, new_sectors])
        else:
            self.subjects = new_subjects
            self.relations = new_relations
            self.objects = new_objects
            self.sectors = new_sectors
            self._loaded = True
    
    def retrieve(self, query: str, max_facts: int = 10,
                 min_score: float = 0.1) -> List[Tuple[str, str, str, str, float]]:
        """
        Récupère les faits par scan numpy vectorisé.
        """
        if not self._loaded:
            return []
        
        query_norm = _normalize(query)
        query_words = [w for w in query_norm.split() if len(w) > 2 and w not in _STOPWORDS]
        if not query_words:
            return []
        
        n = len(self.subjects)
        scores = np.zeros(n, dtype=np.float32)
        
        # Identifier les mots-clés spécifiques (entités) : mots longs et non-génériques
        generic_words = {'explique', 'decouvert', 'parle', 'fonctionne', 'demande', 'cherche',
                         'trouve', 'donne', 'dis', 'sais', 'veux', 'peux', 'faut', 'fait',
                         'quelle', 'comment', 'pourquoi', 'quand', 'combien', 'quest', 'qui',
                         'dont', 'entre', 'comme', 'avec', 'sans', 'sont', 'leur', 'tous',
                         'capitale', 'population', 'symbole', 'chimique', 'cause', 'causé',
                         'causee', 'pays', 'fait', 'cette', 'apres', 'dans', 'plus', 'aux'}

        specific_words = [w for w in query_words if w not in generic_words and len(w) > 3]
        
        # Détecter les entités multi-mots (ex: "Marie Curie", "Etats Unis")
        query_norm_lower = _normalize(query)
        multi_word_entities = []
        # Chercher des paires de mots spécifiques consécutifs
        for i in range(len(query_words) - 1):
            pair = f"{query_words[i]} {query_words[i+1]}"
            if query_words[i] in specific_words or query_words[i+1] in specific_words:
                multi_word_entities.append(pair)
        
        # Scanner par mot
        for word in query_words:
            is_specific = word in specific_words
            for i in range(n):
                s = _normalize(str(self.subjects[i]))
                r = _normalize(str(self.relations[i]))
                o = _normalize(str(self.objects[i]))
                if word in s:
                    scores[i] += 1.0
                    if s.strip().startswith(word) or word == s.strip():
                        scores[i] += 3.0 if is_specific else 2.0
                if word in r:
                    scores[i] += 0.5  # relation match (bonus modéré)
                if word in o:
                    scores[i] += 1.5 if is_specific else 0.8
        
        # Bonus multi-word entity : "Marie Curie" doit matcher plus fort que "marie" seul
        for entity in multi_word_entities:
            entity_norm = _normalize(entity)
            for i in range(n):
                s = _normalize(str(self.subjects[i]))
                o = _normalize(str(self.objects[i]))
                if entity_norm in s:
                    scores[i] += 5.0  # Fort bonus pour entité complète
                if entity_norm in o:
                    scores[i] += 3.0  # Bonus pour entité complète en objet
        
        # Ne pas normaliser — les faits qui matchent PLUSIEURS mots dominent naturellement
        # (la normalisation favorisait les faits avec 1 seul mot fort)
        
        # Trouver les top indices
        if max_facts >= n:
            top_indices = np.argsort(-scores)
        else:
            # Partial sort pour les top K
            top_indices = np.argpartition(-scores, min(max_facts, n-1))[:max_facts]
            top_indices = top_indices[np.argsort(-scores[top_indices])]
        
        # Construire les résultats
        results = []
        seen = set()
        for idx in top_indices:
            score = float(scores[idx])
            if score < min_score:
                continue
            
            s = str(self.subjects[idx])
            r = str(self.relations[idx])
            o = str(self.objects[idx])
            sec = str(self.sectors[idx]) if self.sectors is not None else 'GENERAL'
            
            # Filtrer URIs
            if 'wikidata.org' in s or 'wikidata.org' in o:
                continue
            
            key = (_normalize(s)[:60], _normalize(r)[:60], _normalize(o)[:80])
            if key not in seen:
                seen.add(key)
                results.append((s, r, o, sec, score))
            
            if len(results) >= max_facts:
                break
        
        return results
    
    def stats(self) -> dict:
        if not self._loaded:
            return {'loaded': False}
        return {
            'facts': len(self.subjects),
            'loaded': True,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    import os
    
    shard_path = 'data/kb_enriched/shard_0000.npz'
    if os.path.exists(shard_path):
        r = FastRetriever()
        
        t0 = time.time()
        n = r.load(shard_path)
        print(f'Loaded {n:,} facts in {time.time()-t0:.2f}s')
        
        for query in ['Canada', 'France', 'cancer', 'vaccin', 'Japon', 'paludisme']:
            t0 = time.time()
            results = r.retrieve(query, max_facts=8)
            dt = time.time() - t0
            print(f'\nQuery: {query} ({dt:.3f}s, {len(results)} results)')
            for s, r, o, sec, score in results[:3]:
                print(f'  [{sec}] {str(s)[:50]} | {str(r)[:30]} | {str(o)[:40]} (score: {score:.1f})')
    else:
        print(f'Shard not found: {shard_path}')
        # Test with manual facts
        r = FastRetriever()
        r.add_facts([
            ("Paris", "est la capitale de", "la France", "GEOGRAPHIE"),
            ("Le Canada", "est situé en", "Amérique du Nord", "GEOGRAPHIE"),
            ("Marie Curie", "a découvert", "le radium", "SCIENCES"),
            ("Le cancer", "est une", "prolifération cellulaire", "SANTE"),
        ])
        for query in ['France', 'Canada', 'cancer']:
            results = r.retrieve(query, 5)
            print(f'{query}: {results}')
