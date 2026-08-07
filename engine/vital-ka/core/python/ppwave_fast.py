"""
PPWave Fast — Retrieval PPMI optimisé pour 41K+ faits
=======================================================
Version optimisée du PPWaveRetriever. Build < 30s, query < 100ms.

Optimisations :
- PPMI sparse (top-20 voisins par mot, pas matrice complète)
- Vocabulaire limité aux mots discriminants (fréquence 2..5000)
- Structures de données plates (dict d'int → float)
- Aucune allocation de matrice numpy
"""

import re
import math
import time
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Set

Fact = Tuple[str, str, str, str]

class PPWaveFast:
    """Retrieval PPMI ultra-rapide."""

    STOPWORDS = {'the','a','an','is','are','was','were','of','in','on','at','to',
                 'for','with','by','from','and','or','it','its','that','this',
                 'le','la','les','un','une','des','de','du','d','l','est','sont',
                 'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
                 'avec','et','il','elle','ils','elles','ce','cet','cette','ces',
                 'what','when','where','why','how','who','which','whom','whose',
                 'explain','describe','tell','give','say','make','explique',
                 'decris','parle','donne','dis','comment','pourquoi','quand'}

    def __init__(self, kb: List[Fact], vocab_size: int = 4000, top_neighbors: int = 15):
        t0 = time.time()
        self.kb = kb
        self.N = len(kb)

        # ─── 1. Tokenisation + index inversé ───
        word_docs = defaultdict(set)       # word → set of fact IDs
        word_counts = Counter()            # word → total frequency
        fact_words_list = []               # fact ID → set of words
        
        for fid, (s, r, o, sec) in enumerate(kb):
            text = s + ' ' + r + ' ' + o
            words = {w for w in text.lower().split() if len(w) >= 2 and w not in self.STOPWORDS}
            fact_words_list.append(words)
            for w in words:
                word_docs[w].add(fid)
                word_counts[w] += 1

        # ─── 2. Vocabulaire discriminant (ni trop rare, ni trop fréquent) ───
        min_df, max_df = 2, max(3, self.N // 3)
        self.vocab = [w for w, c in word_counts.most_common(vocab_size * 2)
                      if min_df <= len(word_docs[w]) <= max_df][:vocab_size]
        self.vocab_idx = {w: i for i, w in enumerate(self.vocab)}
        
        # ─── 3. IDF ───
        self.idf = {}
        for w in self.vocab:
            df = len(word_docs[w])
            self.idf[w] = math.log(self.N / max(df, 1)) + 1

        # ─── 4. Co-occurrence sparse ───
        co = Counter()
        for fid, words in enumerate(fact_words_list):
            word_list = [w for w in words if w in self.vocab_idx]
            for i, w1 in enumerate(word_list):
                for w2 in word_list[i+1:]:
                    co[(w1, w2)] += 1
                    co[(w2, w1)] += 1
        
        # ─── 5. PPMI → top-N neighbors ───
        total_pairs = sum(co.values()) // 2 + 1
        total_unigrams = sum(word_counts[w] for w in self.vocab)
        
        self.neighbors: Dict[str, List[Tuple[str, float]]] = {}
        
        for (w1, w2), c in co.items():
            if w1 not in self.vocab_idx or w2 not in self.vocab_idx:
                continue
            p_xy = c / total_pairs
            p_x = word_counts[w1] / total_unigrams
            p_y = word_counts[w2] / total_unigrams
            pmi = math.log(p_xy / (p_x * p_y) + 1e-12)
            if pmi > 0:
                self.neighbors.setdefault(w1, []).append((w2, pmi))
        
        # Garder top-N voisins par mot
        for w in self.neighbors:
            self.neighbors[w].sort(key=lambda x: -x[1])
            self.neighbors[w] = self.neighbors[w][:top_neighbors]

        # ─── 6. Vecteurs de triplets (bag-of-words pondéré IDF) ───
        self.triplet_vecs: Dict[int, Dict[int, float]] = {}
        for fid, words in enumerate(fact_words_list):
            vec = {}
            total = 0.0
            for w in words:
                if w in self.vocab_idx:
                    val = self.idf[w]
                    vec[self.vocab_idx[w]] = val
                    total += val * val
            if total > 0:
                norm = math.sqrt(total)
                vec = {k: v/norm for k, v in vec.items()}
            self.triplet_vecs[fid] = vec

        self._build_time = time.time() - t0
        print(f"PPWaveFast: {len(self.vocab)} mots, {sum(len(v) for v in self.neighbors.values())} liens PPMI, build {self._build_time:.1f}s")

    def _tokenize(self, text: str) -> List[str]:
        return [w.strip('.,!?;:()[]{}') for w in text.lower().split()
                if len(w) >= 2 and w not in self.STOPWORDS]

    def retrieve(self, question: str, max_results: int = 5, expand: bool = True) -> List[Fact]:
        # Extraire les tokens
        q_lower = question.lower().strip()
        # Retirer les préfixes
        for p in ['what is the ','what is ','who is ','who wrote ','who painted ',
                  'who discovered ','when did ','when was ','when ','where is ',
                  'where ','why is ','why ','how ','explain ','capitale de ',
                  'capital of ','quelle est la capitale de ']:
            if q_lower.startswith(p): q_lower = q_lower[len(p):]; break
        q_lower = q_lower.strip('?.,!;:')
        tokens = self._tokenize(q_lower)

        # Expansion PPMI (top 3 voisins par token)
        expanded = list(tokens)
        if expand:
            for t in tokens:
                if t in self.neighbors:
                    for n, ppmi in self.neighbors[t][:3]:
                        if ppmi > 0.5 and n not in expanded:
                            expanded.append(n)

        # Scorer les triplets
        scores: Dict[int, float] = {}
        for t in expanded:
            tidx = self.vocab_idx.get(t, -1)
            if tidx < 0:
                continue
            t_idf = self.idf.get(t, 1.0)
            for fid, vec in self.triplet_vecs.items():
                if tidx in vec:
                    scores[fid] = scores.get(fid, 0.0) + vec[tidx] * t_idf

        if not scores:
            # Fallback sans expansion
            return self.retrieve(question, max_results, expand=False) if expand else []

        # Trier + bonus sujet dans le fait
        final = []
        for fid, score in scores.items():
            s, r, o, sec = self.kb[fid]
            sl, ol = s.lower(), o.lower()
            bonus = sum(2.0 for t in tokens if t in sl) + sum(1.0 for t in tokens if t in ol)
            final.append((score + bonus * 2.0, fid))
        final.sort(key=lambda x: -x[0])

        # Dédupliquer
        results, seen = [], set()
        for _, fid in final:
            if self.kb[fid][0] not in seen:
                results.append(self.kb[fid])
                seen.add(self.kb[fid][0])
            if len(results) >= max_results: break
        return results
