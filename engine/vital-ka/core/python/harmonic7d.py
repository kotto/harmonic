"""
Harmonic7D Retriever — Projection sur l'espace des 7 constantes
=================================================================
Chaque concept se projette sur les 7 constantes fondamentales :
{π: cyclicité, φ: croissance, e: décroissance, √2: dualité,
 √3: 3D, √5: pentagonale, i: phase}

Le secteur d'un fait détermine sa « signature fréquentielle ».
Deux concepts interfèrent constructivement s'ils partagent
les mêmes constantes actives.

Usage:
    from harmonic7d import Harmonic7DRetriever
    h7 = Harmonic7DRetriever(kb)
    facts = h7.retrieve("capitale du japon")
"""

import math
from collections import defaultdict, Counter
from typing import List, Tuple, Dict

Fact = Tuple[str, str, str, str]

# Mapping secteur → constantes actives
SECTOR_CONSTANTS = {
    'PHYSIQUE_FOND':  {'π': 0.8, 'e': 0.6, 'φ': 0.4, '√2': 0.3, '√3': 0.3},
    'PHYSIQUE_APPLI': {'π': 0.7, 'e': 0.5, 'φ': 0.3, '√3': 0.4},
    'MATHS_PURES':    {'π': 0.9, '√2': 0.5, 'φ': 0.4, 'i': 0.3},
    'BIOLOGIE':       {'√5': 0.8, 'φ': 0.6, 'e': 0.4, '√3': 0.3},
    'CHIMIE':         {'√3': 0.6, 'e': 0.5, 'φ': 0.3, '√2': 0.3},
    'GEOGRAPHIE':     {'π': 0.7, '√3': 0.5, 'φ': 0.2},
    'GEOGRAPHY':      {'π': 0.7, '√3': 0.5, 'φ': 0.2},
    'HISTOIRE':       {'π': 0.6, 'e': 0.5, 'φ': 0.3},
    'HISTORY':        {'π': 0.6, 'e': 0.5, 'φ': 0.3},
    'LITTERATURE':    {'√5': 0.6, 'φ': 0.5, 'i': 0.3},
    'ART':            {'√5': 0.8, 'φ': 0.5, 'i': 0.3},
    'MUSIQUE':        {'π': 0.5, '√5': 0.7, 'φ': 0.4},
    'PHILOSOPHIE':    {'i': 0.7, '√2': 0.5, 'φ': 0.4},
    'CONSCIENCE':     {'i': 0.9, 'φ': 0.4, '√2': 0.3},
    'SPIRITUALITE':   {'i': 0.8, 'φ': 0.4, '√2': 0.3},
    'EMOTION_POS':    {'√2': 0.7, 'φ': 0.4, 'i': 0.3},
    'CULTURE_G':      {'π': 0.4, 'φ': 0.3, '√5': 0.3, 'i': 0.2},
    'CULTURE':        {'π': 0.4, 'φ': 0.3, '√5': 0.3},
    'TECHNOLOGIE':    {'√3': 0.5, 'e': 0.5, 'φ': 0.3},
    'ECONOMIE':       {'e': 0.6, 'φ': 0.5, 'π': 0.3},
    'POLITIQUE':      {'√2': 0.6, 'φ': 0.4, 'π': 0.3},
    'SANTE':          {'e': 0.5, '√5': 0.4, 'φ': 0.3},
    'SCIENCE':        {'π': 0.6, 'e': 0.5, 'φ': 0.3},
    'GENERAL':        {'π': 0.3, 'φ': 0.3, 'e': 0.3},
    'SYNONYME':       {'i': 0.5, '√2': 0.5},
}

CONSTANTS_ORDER = ['π', 'φ', 'e', '√2', '√3', '√5', 'i']
C7 = len(CONSTANTS_ORDER)

class Harmonic7DRetriever:
    """Retrieval par projection sur l'espace 7D des constantes."""

    STOPWORDS = {'the','a','an','is','are','was','were','of','in','on','at','to',
                 'for','with','by','from','and','or','it','its','that','this',
                 'le','la','les','un','une','des','de','du','d','l','est','sont',
                 'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
                 'avec','et','il','elle','ils','elles','ce','cet','cette','ces'}

    def __init__(self, kb: List[Fact]):
        self.kb = kb
        self.N = len(kb)

        # 1. Indexer les secteurs de chaque mot
        word_sectors = defaultdict(set)
        word_counts = Counter()
        for s, r, o, sec in kb:
            for w in set((s+' '+r+' '+o).lower().split()):
                w = w.strip('.,!?')
                if len(w) >= 2 and w not in self.STOPWORDS:
                    word_sectors[w].add(sec)
                    word_counts[w] += 1

        # 2. Vecteur 7D pour chaque mot (moyenne des constantes de ses secteurs)
        self.word_vecs: Dict[str, List[float]] = {}
        for w, sectors in word_sectors.items():
            vec = [0.0] * C7
            for sec in sectors:
                if sec in SECTOR_CONSTANTS:
                    for cname, cval in SECTOR_CONSTANTS[sec].items():
                        vec[CONSTANTS_ORDER.index(cname)] += cval
            # Normaliser
            norm = math.sqrt(sum(v*v for v in vec))
            if norm > 0:
                vec = [v/norm for v in vec]
            self.word_vecs[w] = vec

        # 3. Vecteur 7D pour chaque fait (somme des vecteurs de ses mots)
        self.fact_vecs = []
        self.fact_data = []
        for s, r, o, sec in kb:
            vec = [0.0] * C7
            count = 0
            for w in set((s+' '+r+' '+o).lower().split()):
                w = w.strip('.,!?')
                if w in self.word_vecs:
                    wv = self.word_vecs[w]
                    for i in range(C7):
                        vec[i] += wv[i]
                    count += 1
            if count > 0:
                norm = math.sqrt(sum(v*v for v in vec))
                vec = [v/norm for v in vec] if norm > 0 else vec
            self.fact_vecs.append(vec)
            self.fact_data.append((s, r, o, sec))

        print(f"Harmonic7D: {len(self.word_vecs)} mots dans l'espace 7D")

    def _tokenize(self, text: str) -> List[str]:
        q = text.lower().strip()
        for p in ['what is the ','what is ','who is ','who wrote ','who painted ',
                  'who discovered ','when did ','when was ','when ','where is ',
                  'where ','why is ','why ','how ','explain ','capitale de ',
                  'capital of ','quelle est la capitale de ']:
            if q.startswith(p): q = q[len(p):]; break
        return [w.strip('.,!?') for w in q.strip('?.,!;:').split()
                if len(w) >= 2 and w not in self.STOPWORDS]

    def retrieve(self, question: str, max_results: int = 5) -> List[Fact]:
        tokens = self._tokenize(question)
        if not tokens:
            return []

        # Vecteur question = somme des vecteurs de ses mots
        qvec = [0.0] * C7
        count = 0
        for t in tokens:
            if t in self.word_vecs:
                wv = self.word_vecs[t]
                for i in range(C7):
                    qvec[i] += wv[i]
                count += 1
        
        if count == 0:
            return []
        
        # Normaliser
        qnorm = math.sqrt(sum(v*v for v in qvec))
        if qnorm > 0:
            qvec = [v/qnorm for v in qvec]

        # Cosinus avec chaque fait
        scored = []
        for fid, fvec in enumerate(self.fact_vecs):
            dot = sum(qvec[i] * fvec[i] for i in range(C7))
            fnorm = math.sqrt(sum(v*v for v in fvec))
            if fnorm < 0.01:
                continue
            cosine = max(0.0, dot / (qnorm * fnorm))
            # Bonus mot-clé exact
            s, r, o, sec = self.kb[fid]
            sl, ol = s.lower(), o.lower()
            kw = sum(2.0 for t in tokens if t in sl) + sum(1.0 for t in tokens if t in ol)
            scored.append((cosine + kw * 0.5, fid))

        scored.sort(key=lambda x: -x[0])
        results, seen = [], set()
        for _, fid in scored:
            f = self.kb[fid]
            if f[0] not in seen:
                results.append(f); seen.add(f[0])
            if len(results) >= max_results: break
        return results
