#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IA Harmonique LSA — Embeddings Sémantiques Intégrés
=====================================================
Utilise la LSA (co-occurrence → SVD → 7D) validée en Phase A,
et l'injecte dans le pipeline complet.

Test : comparer la qualité des réponses avant/après LSA.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, time, sys, os, json, glob, re, random
from collections import Counter
from typing import List, Dict, Optional
import numpy as np

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
H = np.array([phi, pi, e, math.sqrt(2), math.sqrt(3), math.sqrt(5), e/pi], dtype=np.float64)
H_sum = H.sum()

# ================================
# CHARGEMENT CORPUS
# ================================
def charger_tous_textes(dossier="data/holograms", max_textes=None):
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
                    if max_textes and len(textes) >= max_textes: return textes
    return textes

# ================================
# LSA EMBEDDINGS (SPARSE)
# ================================
class LSAEmbeddings:
    def __init__(self, vocab_size=3000, window=5):
        self.vocab_size = vocab_size; self.window = window
        self.vocab = {}; self.inv = {}; self.emb = {}
    
    def entrainer(self, corpus):
        cnt = Counter()
        for t in corpus:
            for m in t.lower().split():
                if len(m) >= 2: cnt[m] += 1
        mots = [m for m, _ in cnt.most_common(self.vocab_size)]
        self.vocab = {m: i for i, m in enumerate(mots)}
        self.inv = {i: m for i, m in enumerate(mots)}
        V = len(self.vocab)
        
        # Co-occurrence sparse (liste de listes)
        cooc = [Counter() for _ in range(V)]
        for t in corpus:
            ms = [m for m in t.lower().split() if m in self.vocab]
            for i, mi in enumerate(ms):
                ii = self.vocab[mi]
                lo = max(0, i - self.window); hi = min(len(ms), i + self.window + 1)
                for j in range(lo, hi):
                    if i != j and ms[j] in self.vocab:
                        cooc[ii][self.vocab[ms[j]]] += 1.0 / abs(i - j)
        
        # Convertir en matrice dense (V × 3000 tient en mémoire)
        M = np.zeros((V, V), dtype=np.float64)
        for i in range(V):
            for j, val in cooc[i].items():
                M[i, j] = val
        
        total = M.sum()
        
        # PPMI simplifié
        if total > 0:
            marg_i = M.sum(axis=1, keepdims=True) + 1e-3
            marg_j = M.sum(axis=0, keepdims=True) + 1e-3
            p_xy = (M + 1e-3) / (total + 1e-3 * V * V)
            p_x = marg_i / (total + 1e-3 * V)
            p_y = marg_j / (total + 1e-3 * V)
            pmi = np.log(np.maximum(p_xy, 1e-12) / np.maximum(p_x * p_y, 1e-12))
            pmi = np.maximum(pmi, 0)
            M = pmi
        
        # SVD randomisée → 7D
        k = min(7, V)
        n_random = k + 10
        Omega = np.random.randn(V, n_random)
        Y = M @ Omega
        Q, _ = np.linalg.qr(Y)
        B = Q.T @ M
        Ub, Sb, _ = np.linalg.svd(B, full_matrices=False)
        U = Q @ Ub
        Uk = U[:, :k]
        emb = Uk @ np.diag(np.sqrt(Sb[:k]))
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb /= norms
        
        for mot, idx in self.vocab.items():
            self.emb[mot] = emb[idx]
        self.unk = emb.mean(axis=0)
        
        var_explained = Sb[:k].sum() / Sb.sum() * 100 if Sb.sum() > 0 else 0
        nb_paires_remplies = sum(1 for i in range(V) if cooc[i])
        return V, var_explained, nb_paires_remplies
    
    def mot_vers_7d(self, mot):
        return self.emb.get(mot.lower(), self.unk).copy()
    
    def texte_vers_7d(self, texte):
        mots = [m for m in texte.lower().split() if m in self.emb]
        if not mots: return self.unk.copy()
        v = np.mean([self.emb[m] for m in mots], axis=0)
        n = np.linalg.norm(v)
        return v / n if n > 0 else v


# ================================
# MOTEUR DE RECHERCHE LSA
# ================================
class MoteurRechercheLSA:
    def __init__(self, lsa: LSAEmbeddings, textes: List[str]):
        self.lsa = lsa
        self.textes = textes
        self.vecteurs = [lsa.texte_vers_7d(t) for t in textes]
    
    def rechercher(self, question, top_k=5):
        vq = self.lsa.texte_vers_7d(question)
        scores = []
        for i, vt in enumerate(self.vecteurs):
            d = np.dot(vq, vt)
            sim = d / (np.linalg.norm(vq) * np.linalg.norm(vt) + 1e-10)
            scores.append((self.textes[i], sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(s[0], s[1]) for s in scores[:top_k]]


# ================================
# PIPELINE SIMPLE (NER + Templates)
# ================================
SCIENTIFIQUES = {'einstein','newton','planck','darwin','curie','pasteur','galilée','kepler','maxwell','bohr','heisenberg','feynman','hawking','tesla','edison','marconi','mendeleïev','lavoisier','lemaître','hubble','watson','crick','franklin','wegener','boltzmann'}
MOIS = {'janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'}

TEMPLATES = {
    "valeur": ["La valeur de {sujet} est {valeur}.", "{sujet} vaut exactement {valeur}.", "{sujet} a pour valeur {valeur}."],
    "personne_decouverte": ["C'est {personne} qui a découvert {sujet}.", "La découverte de {sujet} est due à {personne}."],
    "personne_definition": ["{personne} est {definition}.", "{personne} était {definition}."],
    "explication": ["{sujet} fonctionne ainsi : {reponse}", "Le principe de {sujet} : {reponse}"],
    "definition": ["{sujet} est {reponse}", "On appelle {sujet} {reponse}"],
}

def extraire_entites(texte):
    t = texte.lower()
    personne = None
    for sci in sorted(SCIENTIFIQUES, key=len, reverse=True):
        if sci in t: personne = sci.capitalize(); break
    valeur = None
    m = re.search(r'\b(\d+[.,]\d+\s*[×xX]\s*10\^?[−-]?\d+\s*\S*)', texte)
    if m: valeur = m.group(1).strip()
    if not valeur:
        m = re.search(r'\b(\d+(?:\s+\d+){1,3}\s+(?:m/s|km/s|J·s|kg|Hz|W|K|°C))\b', texte, re.I)
        if m: valeur = m.group(1).strip()
    date = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', texte)
    return {'personne': personne, 'valeur': valeur, 'date': date.group(1) if date else None}

def extraire_sujet(question):
    q = question.lower().strip()
    for p in ["quelle est la valeur de ","quelle est la ","quel est le ","quel est l'","quelle est l'","quel est ","quelle est ","qui a découvert ","qui a inventé ","qui est ","qui était ","comment fonctionne ","comment ","qu'est-ce que ","qu'est-ce qu'","c'est quoi ","pourquoi "]:
        if q.startswith(p): q = q[len(p):]; break
    for a in ["la ","le ","l'","une ","un ","des ","les "]:
        if q.startswith(a): q = q[len(a):]; break
    q = q.strip()
    return q[0].upper() + q[1:] if q else "ce sujet"

def generer_reponse(question, faits):
    if not faits: return "Aucune information."
    fp = faits[0][0] if isinstance(faits[0], tuple) else faits[0]
    entites = extraire_entites(fp + ' ' + ' '.join(f[0] if isinstance(f, tuple) else f for f in faits[1:3] if faits[1:]))
    pers, val, dat = entites['personne'], entites['valeur'], entites['date']
    sujet = extraire_sujet(question)
    q = question.lower()
    
    if any(m in q for m in ['qui est','qui était','qui a']):
        if pers and any(m in q for m in ['a découvert','a inventé','découvert']):
            tpl = random.choice(TEMPLATES["personne_decouverte"])
            rep = tpl.format(personne=pers, sujet=sujet)
        elif pers:
            tpl = random.choice(TEMPLATES["personne_definition"])
            rep = tpl.format(personne=pers, definition=fp.rstrip('.'))
        else: rep = fp
    elif any(m in q for m in ['quelle est','quel est','valeur','vitesse','constante','masse']):
        if val:
            tpl = random.choice(TEMPLATES["valeur"]); rep = tpl.format(sujet=sujet, valeur=val)
        else:
            phrase = fp.split('.')[0].strip()
            if len(phrase) > 10:
                tpl = random.choice(TEMPLATES["valeur"]); rep = tpl.format(sujet=sujet, valeur=phrase)
            else: rep = fp
    elif any(m in q for m in ['comment','pourquoi','fonctionne']):
        tpl = random.choice(TEMPLATES["explication"]); rep = tpl.format(sujet=sujet, reponse=fp.rstrip('.'))
    elif any(m in q for m in ["qu'est-ce","c'est quoi","définition"]):
        tpl = random.choice(TEMPLATES["definition"]); rep = tpl.format(sujet=sujet, reponse=fp.rstrip('.'))
    else: rep = fp
    
    if dat and dat not in rep: rep += f" Cela remonte à {dat}."
    return rep

# ================================
# TEST
# ================================
print("=" * 70)
print("IA HARMONIQUE LSA — Embeddings Sémantiques Intégrés")
print("=" * 70)
print()
print("Chargement corpus complet...")
textes = charger_tous_textes(max_textes=30000)
print(f"  {len(textes):,} textes")
print()
print("Entraînement LSA (3000 mots, fenêtre 5)...")
t0 = time.time()
lsa = LSAEmbeddings(vocab_size=3000, window=5)
V, var, nb_paires = lsa.entrainer(textes)
print(f"  Vocabulaire : {V} mots")
print(f"  Variance 7D : {var:.1f}%")
print(f"  Paires cooc : {nb_paires}")
print(f"  Temps       : {time.time()-t0:.1f}s")
print()
print("Création du moteur de recherche LSA...")
moteur = MoteurRechercheLSA(lsa, textes)
print()
questions = [
    "quelle est la constante de Planck",
    "qui a découvert la relativité",
    "comment fonctionne la photosynthèse",
    "quelle est la vitesse de la lumière",
    "qu'est-ce que le Big Bang",
    "qui est Albert Einstein",
]
print("=" * 70)
print("TEST — RÉPONSES AVEC EMBEDDINGS SÉMANTIQUES")
print("=" * 70)
print()
for q in questions:
    print(f"  ❓ {q}")
    r = moteur.rechercher(q, top_k=3)
    rep = generer_reponse(q, r)
    print(f"  💬 {rep[:200]}")
    print(f"     Top-3 LSA : {', '.join(t[:60]+'...' for t,s in r[:2])}")
    print()
print("✅ TERMINÉ")