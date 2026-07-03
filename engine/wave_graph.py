"""
WaveGraph Retriever — Interférence ondulatoire par Personalized PageRank
==========================================================================
"Les mots de la question sont des sources d'énergie simultanées.
 L'énergie se propage dans le graphe mot↔fait.
 Là où les fronts d'onde convergent = le fait pertinent."

PRINCIPE :
  1. Graphe biparti : mots ↔ faits (triplets)
  2. La question injecte de l'énergie dans les nœuds-mots correspondants
  3. L'énergie diffuse (Personalized PageRank)
  4. Les faits recevant le plus d'énergie sont les plus pertinents

C'est EXACTEMENT le principe des interférences :
  "largest" seul → bruit (tenth, huge, country, city...)
  "largest" + "country" simultanés → Russie (convergence des deux fronts)

Usage:
    from wave_graph import WaveGraphRetriever
    wg = WaveGraphRetriever(kb)
    facts = wg.retrieve("what is the largest country")
"""

import re, math, time
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Set

Fact = Tuple[str, str, str, str]

class WaveGraphRetriever:
    """Retrieval par propagation d'énergie simultanée."""

    STOPWORDS = {'the','a','an','is','are','was','were','of','in','on','at','to',
                 'for','with','by','from','and','or','it','its','that','this',
                 'le','la','les','un','une','des','de','du','d','l','est','sont',
                 'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
                 'avec','et','il','elle','ils','elles','ce','cet','cette','ces',
                 'what','when','where','why','how','who','which','explain','explique'}

    def __init__(self, kb: List[Fact], max_words: int = 5000):
        t0 = time.time()
        self.kb = kb
        self.N_facts = len(kb)

        # ─── 1. Graphe biparti mots ↔ faits ───
        word_to_facts = defaultdict(set)
        fact_to_words = []
        word_counts = Counter()

        for fid, (s, r, o, sec) in enumerate(kb):
            words = [w for w in (s + ' ' + r + ' ' + o).lower().split()
                     if len(w) >= 2 and w not in self.STOPWORDS]
            unique_words = set(words)
            fact_to_words.append(unique_words)
            for w in unique_words:
                word_to_facts[w].add(fid)
                word_counts[w] += 1

        # Vocabulaire (mots assez fréquents)
        self.vocab = [w for w, _ in word_counts.most_common(max_words) if word_counts[w] >= 2]
        self.word_idx = {w: i for i, w in enumerate(self.vocab)}
        V = len(self.vocab)
        self.V = V
        self.F = self.N_facts
        self.T = V + self.F  # total nodes

        # ─── 2. Matrice de transition sparse (dict de dict) ───
        # P(word → fact) : uniforme sur les faits contenant le mot
        # P(fact → word) : uniforme sur les mots du fait
        self.P_word_to_fact = {}  # word_idx → {fact_offset: weight}
        self.P_fact_to_word = {}  # fact_idx → {word_idx: weight}

        for i, w in enumerate(self.vocab):
            facts = word_to_facts.get(w, set())
            if facts:
                wgt = 1.0 / len(facts)
                self.P_word_to_fact[i] = {fid: wgt for fid in facts}

        for fid, words in enumerate(fact_to_words):
            wrds = [self.word_idx[w] for w in words if w in self.word_idx]
            if wrds:
                wgt = 1.0 / len(wrds)
                self.P_fact_to_word[fid] = {wi: wgt for wi in wrds}

        # IDF pour scoring final
        self.idf = {}
        for w in self.vocab:
            df = len(word_to_facts[w])
            self.idf[w] = math.log(self.N_facts / max(df, 1)) + 1

        self._build_time = time.time() - t0
        print(f"WaveGraph: {V} mots + {self.F} faits = {self.T} nœuds, "
              f"build {self._build_time:.1f}s")

    def _tokenize(self, text: str) -> List[str]:
        q = text.lower().strip()
        for p in ['what is the ','what is ','who is ','who wrote ','who painted ',
                  'who discovered ','when did ','when was ','when ','where is ',
                  'where ','why is ','why ','how ','explain ','capitale de ',
                  'capital of ','quelle est la capitale de ']:
            if q.startswith(p): q = q[len(p):]; break
        return [w.strip('.,!?') for w in q.strip('?.,!;:').split()
                if len(w) >= 2 and w not in self.STOPWORDS]

    def retrieve(self, question: str, max_results: int = 5,
                 alpha: float = 0.15, n_iter: int = 10) -> List[Fact]:
        """
        Personalized PageRank depuis les mots de la question.

        alpha = probabilité de téléport (rester proche des seeds)
        n_iter = nombre d'itérations de diffusion
        """
        tokens = self._tokenize(question)
        if not tokens:
            return []

        # Seeds = mots de la question présents dans le vocabulaire
        seed_idxs = [self.word_idx[t] for t in tokens if t in self.word_idx]
        if not seed_idxs:
            return []

        # ─── PPR : Personalized PageRank ───
        # r = vecteur de scores sur TOUS les nœuds (mots + faits)
        # r_mots  = V premières composantes
        # r_faits = F suivantes

        # Initialisation : distribution uniforme sur les seeds (mots)
        r = [0.0] * self.T
        seed_weight = 1.0 / len(seed_idxs)
        for si in seed_idxs:
            r[si] = seed_weight

        # Vecteur de téléportation personnalisé
        p = list(r)  # copie

        for _ in range(n_iter):
            new_r = [0.0] * self.T

            # Téléportation
            for i in range(self.T):
                new_r[i] = alpha * p[i]

            # Diffusion depuis les mots vers les faits
            for wi, wgt in enumerate(r[:self.V]):
                if wgt > 0 and wi in self.P_word_to_fact:
                    delta = (1 - alpha) * wgt
                    for fid, fwgt in self.P_word_to_fact[wi].items():
                        new_r[self.V + fid] += delta * fwgt

            # Diffusion depuis les faits vers les mots
            for fi in range(self.F):
                wgt = r[self.V + fi]
                if wgt > 0 and fi in self.P_fact_to_word:
                    delta = (1 - alpha) * wgt
                    for wi, wwgt in self.P_fact_to_word[fi].items():
                        new_r[wi] += delta * wwgt

            r = new_r

        # ─── Scores des faits ───
        # Un fait est pertinent si :
        # 1. Il a reçu beaucoup d'énergie (score PPR direct)
        # 2. Ses mots ont reçu beaucoup d'énergie (score indirect)

        fact_scores = []
        for fid in range(self.F):
            # Score direct = énergie reçue par le nœud-fait
            direct = r[self.V + fid]

            # Score indirect = somme de l'énergie des mots du fait
            s, r_word, o, sec = self.kb[fid]
            indirect = 0.0
            for w in self._tokenize(s + ' ' + r_word + ' ' + o):
                if w in self.word_idx:
                    indirect += r[self.word_idx[w]]

            # Bonus sujet : si le fait contient les mots exacts de la question
            sl = s.lower()
            ol = o.lower()
            exact_bonus = sum(2.0 for t in tokens if t in sl) + sum(1.0 for t in tokens if t in ol)

            score = direct * 3.0 + indirect + exact_bonus
            if score > 0.001:
                fact_scores.append((score, fid))

        fact_scores.sort(key=lambda x: -x[0])

        # Dédupliquer
        results, seen = [], set()
        for score, fid in fact_scores:
            fact = self.kb[fid]
            if fact[0] not in seen:
                results.append(fact)
                seen.add(fact[0])
            if len(results) >= max_results:
                break

        return results
