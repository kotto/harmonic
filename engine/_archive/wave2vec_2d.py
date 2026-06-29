"""
Wave2Vec 2D — Entrainement des positions (kx, ky) 2D par SGD
================================================================
Ajoute a qualitative_knowledge.py
"""
import numpy as np
import math

def wave2vec_2d(epochs=200, lr=0.05, verbose=True):
    from qualitative_knowledge import build_natural_waves, KNOWLEDGE_BASE
    
    kx0, ky0, w2i = build_natural_waves()
    n = len(kx0)
    
    pos = np.zeros((n, 2))
    for i in range(n):
        pos[i, 0] = kx0[i]
        pos[i, 1] = ky0[i]
    
    # Positive pairs: words in same fact (excluant les stopwords)
    stopwords = {'le','la','les','de','des','du','un','une','et','est','a','dans',
                 'que','qui','pas','ne','sur','pour','avec','ce','cette','par',
                 'au','aux','en','plus','moins','tout','tous','son','sa','ses'}
    positive_pairs = set()
    for sujet, rel, objet, _ in KNOWLEDGE_BASE:
        fact_words = set()
        for mot in sujet.split() + rel.split() + objet.split():
            mot = mot.strip('.,!?;:')
            if len(mot) >= 2 and mot in w2i and mot not in stopwords:
                fact_words.add(w2i[mot])
        fact_words = list(fact_words)
        for i in range(len(fact_words)):
            for j in range(i+1, len(fact_words)):
                a, b = fact_words[i], fact_words[j]
                if a != b:
                    positive_pairs.add((min(a,b), max(a,b)))
    
    pos_pairs = list(positive_pairs)
    np.random.seed(42)
    
    neg_pairs = set()
    while len(neg_pairs) < len(pos_pairs):
        a = np.random.randint(0, n)
        b = np.random.randint(0, n)
        if a != b:
            pair = (min(a,b), max(a,b))
            if pair not in positive_pairs:
                neg_pairs.add(pair)
    neg_pairs = list(neg_pairs)
    
    if verbose:
        print(f'Wave2Vec 2D: {len(pos_pairs)} pos, {len(neg_pairs)} neg, {n} words')
    
    for epoch in range(epochs):
        np.random.shuffle(pos_pairs)
        np.random.shuffle(neg_pairs)
        total_loss = 0.0
        n_pos = len(pos_pairs)
        n_neg = len(neg_pairs)
        
        for i in range(n_pos):
            a, b = pos_pairs[i]
            delta = pos[a] - pos[b]
            dist2 = np.dot(delta, delta) + 1e-10
            total_loss += dist2
            grad = lr * delta / (n_pos + 1e-10)
            pos[a] -= grad
            pos[b] += grad
        
        min_dist = 0.5
        for i in range(n_neg):
            c, d = neg_pairs[i]
            delta = pos[c] - pos[d]
            dist = np.sqrt(np.dot(delta, delta) + 1e-10)
            if dist < min_dist:
                loss_rep = (min_dist - dist) ** 2
                total_loss += loss_rep
                grad_factor = lr * (min_dist - dist) / (dist * n_neg + 1e-10)
                grad = grad_factor * delta
                pos[c] += grad
                pos[d] -= grad
        
        max_norm = np.max(np.sqrt(pos[:,0]**2 + pos[:,1]**2))
        if max_norm > 10.0:
            pos /= max_norm / 5.0
        
        if verbose and (epoch+1) % 50 == 0:
            cos_pos_vals = []
            for a, b in pos_pairs[:500]:
                na = np.sqrt(pos[a,0]**2 + pos[a,1]**2) + 1e-10
                nb = np.sqrt(pos[b,0]**2 + pos[b,1]**2) + 1e-10
                cos_pos_vals.append(np.dot(pos[a], pos[b]) / (na*nb))
            print(f'  Epoch {epoch+1}/{epochs}: loss={total_loss:.0f}, cos_pos={np.mean(cos_pos_vals):.3f}')
    
    kx_out = pos[:, 0].copy()
    ky_out = pos[:, 1].copy()
    return kx_out, ky_out, w2i
