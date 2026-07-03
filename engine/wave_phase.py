"""
WavePhase Retriever — Retrieval par relaxation de phase ondulatoire (v2)
==========================================================================
Hybride : relaxation de phase pour expansion sémantique + index inversé.

PRINCIPE ONDULATOIRE :
  1. Les mots sont des oscillateurs avec phase θ
  2. Chaque fait (s,r,o) couple les phases → relaxation → convergence
  3. Après convergence : mots co-occurrents ont phases similaires
  4. Expansion de requête par similarité de phase (≠ PPMI statistique)
  5. Retrieval par index inversé sur les mots expandés

Usage:
    from wave_phase import WavePhaseRetriever
    wp = WavePhaseRetriever(kb, iterations=30)
    facts = wp.retrieve("capitale du japon")
"""
import math, random
from collections import defaultdict, Counter
from typing import List, Tuple, Dict

Fact = Tuple[str, str, str, str]

class WavePhaseRetriever:
    STOPWORDS = {'the','a','an','is','are','was','were','of','in','on','at','to',
                 'for','with','by','from','and','or','it','its','that','this',
                 'le','la','les','un','une','des','de','du','d','l','est','sont',
                 'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
                 'avec','et','il','elle','ils','elles','ce','cet','cette','ces'}

    def __init__(self, kb, iterations=30, alpha=0.3, max_vocab=5000):
        self.kb = kb; self.N = len(kb)
        # Tokenisation
        wc = Counter(); fwl = []
        for fid,(s,r,o,sec) in enumerate(kb):
            ws = [w for w in (s+' '+r+' '+o).lower().split() if len(w)>=2 and w not in self.STOPWORDS]
            fwl.append(ws)
            for w in ws: wc[w] += 1
        self.vocab = [w for w,_ in wc.most_common(max_vocab) if wc[w] >= 3]
        self.vidx = {w:i for i,w in enumerate(self.vocab)}; V = len(self.vocab)
        # Phases aléatoires
        self.phases = [random.random()*2*math.pi for _ in range(V)]
        # Relaxation
        for it in range(iterations):
            ds, dc = [0.0]*V, [0]*V
            for ws in fwl:
                idxs = [self.vidx[w] for w in ws if w in self.vidx]
                if len(idxs)<2: continue
                cx = sum(math.cos(self.phases[i]) for i in idxs)
                cy = sum(math.sin(self.phases[i]) for i in idxs)
                if cx==0 and cy==0: continue
                mp = math.atan2(cy,cx)
                for i in idxs:
                    d = mp - self.phases[i]; d = (d+math.pi)%(2*math.pi)-math.pi
                    ds[i] += d; dc[i] += 1
            ch = 0
            for i in range(V):
                if dc[i]>0: self.phases[i] = (self.phases[i]+alpha*ds[i]/dc[i])%(2*math.pi)
                ch += abs(ds[i]/max(dc[i],1))
            if it%10==0: print(f"  Iter {it}: change={ch:.1f}")
        # Voisins de phase
        self.neighbors = {}
        for i,w1 in enumerate(self.vocab):
            nb = []
            for j,w2 in enumerate(self.vocab):
                if i==j: continue
                d = abs(self.phases[i]-self.phases[j]); d = min(d,2*math.pi-d)
                s = 1.0 - d/math.pi
                if s > 0.5: nb.append((w2,s))
            nb.sort(key=lambda x:-x[1])
            self.neighbors[w1] = nb[:15]
        # Index inversé
        self.w2f = defaultdict(set)
        for fid,ws in enumerate(fwl):
            for w in set(ws): self.w2f[w].add(fid)
        print(f"  Done: {V} mots, {sum(len(v) for v in self.neighbors.values())} liens phase")

    def retrieve(self, question, max_results=5):
        q = question.lower().strip()
        for p in ['what is the ','what is ','who is ','who wrote ','who painted ',
                  'who discovered ','when did ','when ','where ','why ','how ',
                  'explain ','capitale de ','capital of ','quelle est la capitale de ']:
            if q.startswith(p): q = q[len(p):]; break
        tokens = [w.strip('.,!?') for w in q.strip('?.,!;:').split() if len(w)>=2]
        # Expansion phase
        expanded = list(tokens)
        for t in tokens:
            if t in self.neighbors:
                for n,s in self.neighbors[t][:3]:
                    if s>0.6 and n not in expanded: expanded.append(n)
        # Index lookup
        scores = defaultdict(float)
        for w in expanded:
            if w in self.w2f:
                df = len(self.w2f[w]); idf = math.log(self.N/max(df,1))+1
                for fid in self.w2f[w]: scores[fid] += idf
        if not scores:
            for w in tokens:
                if w in self.w2f:
                    for fid in self.w2f[w]: scores[fid] += 1.0
        if not scores: return []
        # Bonus + dedup
        final = []
        for fid,sc in sorted(scores.items(), key=lambda x:-x[1]):
            s,r,o,sec = self.kb[fid]
            sl,ol = s.lower(), o.lower()
            bonus = sum(2.0 for t in tokens if t in sl) + sum(1.0 for t in tokens if t in ol)
            final.append((sc+bonus, (s,r,o,sec)))
        seen=set(); results=[]
        for _,f in sorted(final, key=lambda x:-x[0]):
            if f[0] not in seen: results.append(f); seen.add(f[0])
            if len(results)>=max_results: break
        return results
