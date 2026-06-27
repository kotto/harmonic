#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embeddings Sémantiques Harmoniques (Phase A)
==============================================
Test crucial : les 7 harmoniques PEUVENT-elles encoder le sens ?

Méthode : LSA (co-occurrence → SVD → 7D)
Comparaison : ord(c) mod 7 vs LSA/7D

Si cos("einstein", "relativité") >> cos("einstein", "table") après LSA,
alors les 7 harmoniques sont SUFFISANTES pour capturer la sémantique.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, time, sys, os, json, glob
from collections import Counter
import numpy as np

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
H = np.array([phi, pi, e, math.sqrt(2), math.sqrt(3), math.sqrt(5), e/pi], dtype=np.float64)
H_sum = H.sum()

def charger_corpus(dossier="data/holograms", max_textes=50000):
    textes = []
    for f in sorted(glob.glob(os.path.join(dossier, "hologram64_*.npy"))):
        fj = f.replace(".npy", "_data.json")
        if os.path.exists(fj):
            with open(fj, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                if 'texts' in data: ts = data['texts']
                elif isinstance(data, list): ts = data
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], str):
                            ts = v; break
                else: ts = []
            for t in ts:
                if t and len(t.strip()) > 10:
                    textes.append(t.strip().lower())
                    if len(textes) >= max_textes: return textes
    return textes

# === BASELINE : ord(c) mod 7 ===
def mot_vers_7d_baseline(mot):
    v = np.zeros(7, dtype=np.float64)
    for i, c in enumerate(mot):
        v[(ord(c) + i) % 7] += H[(ord(c) + i) % 7] / H_sum
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

def cos_sim(v1, v2):
    d = np.dot(v1, v2)
    n1 = np.linalg.norm(v1); n2 = np.linalg.norm(v2)
    return float(d / (n1 * n2 + 1e-10))

# === LSA ===
class LSAEmbeddings:
    def __init__(self, vocab_size=5000, window=5):
        self.V = vocab_size; self.w = window
        self.vocab = {}; self.inv = {}; self.emb = {}
    
    def entrainer(self, corpus):
        # Vocab
        cnt = Counter()
        for t in corpus:
            for m in t.lower().split():
                if len(m) >= 2: cnt[m] += 1
        mots = [m for m, _ in cnt.most_common(self.V)]
        self.vocab = {m: i for i, m in enumerate(mots)}
        self.inv = {i: m for i, m in enumerate(mots)}
        V = len(self.vocab)
        # Co-occurrence
        cooc = np.zeros((V, V), dtype=np.float64)
        for t in corpus:
            ms = [m for m in t.lower().split() if m in self.vocab]
            for i, mi in enumerate(ms):
                ii = self.vocab[mi]
                lo = max(0, i - self.w); hi = min(len(ms), i + self.w + 1)
                for j in range(lo, hi):
                    if i != j and ms[j] in self.vocab:
                        cooc[ii, self.vocab[ms[j]]] += 1.0 / abs(i - j)
        # PPMI simplifié avec lissage
        total = cooc.sum()
        lissage = 1e-3  # Évite les divisions par zéro
        if total > 0:
            # Probabilités marginales lissées
            marg_i = cooc.sum(axis=1, keepdims=True) + lissage
            marg_j = cooc.sum(axis=0, keepdims=True) + lissage
            # PMI = log( P(x,y) / (P(x)*P(y)) )
            # avec lissage additif
            p_xy = (cooc + lissage) / (total + lissage * V * V)
            p_x = marg_i / (total + lissage * V)
            p_y = marg_j / (total + lissage * V)
            pmi = np.log(np.maximum(p_xy, 1e-12) / np.maximum(p_x * p_y, 1e-12))
            pmi = np.maximum(pmi, 0)  # PPMI
            M = pmi
        else:
            M = cooc
        
        # Vérifier que la matrice n'est pas toute nulle
        if np.allclose(M, 0):
            print("    ⚠️  PPMI entièrement nulle, utilisation de la co-occurrence brute")
            M = cooc / (total + 1e-10)
        # SVD → 7D (randomisée, plus efficace en mémoire)
        k = min(7, V)
        # SVD randomisée : M ≈ Q @ (Q.T @ M) où Q est une base orthonormale aléatoire
        n_oversamples = 10
        n_random = k + n_oversamples
        Omega = np.random.randn(V, n_random)
        Y = M @ Omega
        Q, _ = np.linalg.qr(Y)
        # Projeter M sur Q
        B = Q.T @ M
        Ub, Sb, Vtb = np.linalg.svd(B, full_matrices=False)
        U = Q @ Ub
        S = Sb
        Uk = U[:, :k]; Sk = np.diag(S[:k])
        emb = Uk @ np.sqrt(Sk)
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb /= norms
        for mot, idx in self.vocab.items():
            self.emb[mot] = emb[idx]
        self.unk = emb.mean(axis=0) if V > 0 else np.zeros(7)
        return V, S[:k].sum() / S.sum() * 100

    def mot_vers_7d(self, mot):
        mot = mot.lower()
        return self.emb.get(mot, self.unk).copy()

# === TEST ===
print("=" * 70)
print("TEST CRUCIAL : Les 7 harmoniques peuvent-elles encoder le sens ?")
print("=" * 70)
print()

corpus = charger_corpus(max_textes=15000)
print(f"Corpus : {len(corpus):,} textes\n")

print("Entraînement LSA (co-occurrence → SVD → 7D)...")
t0 = time.time()
lsa = LSAEmbeddings(vocab_size=1500, window=5)
V, var = lsa.entrainer(corpus)
print(f"  Vocabulaire : {V} mots | Variance 7D : {var:.1f}%")
print(f"  Temps : {time.time()-t0:.1f}s\n")

print("=" * 70)
print("COMPARAISON : ord(c) mod 7  vs  LSA/7D")
print("=" * 70)
print()

paires = [
    ("einstein", "relativité"),
    ("einstein", "table"),
    ("planck", "constante"),
    ("planck", "fromage"),
    ("lumière", "photon"),
    ("lumière", "chaise"),
    ("photosynthèse", "plante"),
    ("photosynthèse", "avion"),
    ("big", "bang"),
    ("big", "petit"),
]

print(f"{'Paire':<35s} {'ord(c)%7':>10s} {'LSA/7D':>10s} {'Delta':>10s} {'Verdict'}")
print("-" * 70)
ok = 0
for m1, m2 in paires:
    bl = cos_sim(mot_vers_7d_baseline(m1), mot_vers_7d_baseline(m2))
    ls = cos_sim(lsa.mot_vers_7d(m1), lsa.mot_vers_7d(m2))
    delta = ls - bl
    verdict = "✅" if delta > 0 else "❌"
    if delta > 0: ok += 1
    print(f"{m1+' ↔ '+m2:<35s} {bl:>10.4f} {ls:>10.4f} {delta:>+10.4f} {verdict}")

print()
print(f"  LSA meilleur que baseline : {ok}/{len(paires)}")
print()

# Test contextuel
print("=" * 70)
print("TEST CONTEXTUEL : Les mots proches sont-ils sémantiques ?")
print("=" * 70)
print()
for mot in ["einstein", "planck", "lumière", "photosynthèse", "big"]:
    if mot in lsa.emb:
        v = lsa.emb[mot]
        scores = []
        for m2, v2 in lsa.emb.items():
            if m2 != mot:
                scores.append((m2, cos_sim(v, v2)))
        scores.sort(key=lambda x: x[1], reverse=True)
        print(f"  \"{mot}\" → {', '.join(f'{m}({s:.2f})' for m, s in scores[:8])}")
    else:
        print(f"  \"{mot}\" → [hors vocabulaire]")
    print()

print("=" * 70)
print("VERDICT")
print("=" * 70)
if ok >= 8:
    print("✅ Les 7 harmoniques PEUVENT encoder le sens via LSA.")
    print("   → Embeddings sémantiques validés.")
    print("   → Raisonnement ondulatoire maintenant possible.")
else:
    print("⚠️  La LSA/7D n'est pas strictement meilleure que ord(c) mod 7.")
    print("   → Investiguer : corpus insuffisant ? fenêtre trop petite ?")
print("=" * 70)