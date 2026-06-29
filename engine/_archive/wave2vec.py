"""
Wave2Vec — Entrainement des vecteurs d'onde par co-occurrence
===============================================================
Principe : Ψₐ · Ψ_b = Ψ_{a+b} exige que les mots qui apparaissent
ensemble aient des ondes proches (interference constructive).

Contrairement a word2vec qui apprend des vecteurs denses (300D),
wave2vec apprend des ANGLES dans le plan 2D (kx, ky).
Chaque mot = une direction. La similarite = cos(angle).

Entrainement :
  loss = Σ (1 - cos(θ_a - θ_b))²  pour paires co-occurrentes
       + Σ cos(θ_a - θ_c)²        pour paires negatives (repulsion)

Usage:
  python wave2vec.py --epochs 50 --lr 0.01
"""

import sys
import os
import re
import math
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
import numpy as np

# Constantes
PHI = (1 + math.sqrt(5)) / 2

# Imports locaux
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_HARMONIC_TRAINING = _PROJECT_ROOT / "harmonic_training"
_CORPUS_DIR = _PROJECT_ROOT / "data" / "corpus"
sys.path.insert(0, str(_HARMONIC_TRAINING))
from model.harmonic_resonance_generator import VOCABULAIRE_BASE


class Wave2Vec:
    """
    Entraineur de vecteurs d'onde par co-occurrence.
    
    Chaque mot w recoit un angle θ_w ∈ [0, 2π).
    Les paires co-occurrentes sont attirees (θ proches).
    Les paires negatives sont repoussees (θ opposees).
    
    Apres entrainement, kx = r × cos(θ), ky = r × sin(θ)
    ou r est le rayon preserve de la spirale π/6.
    """
    
    def __init__(self, vocab: List[str]):
        self.vocab = vocab
        self.vocab_size = len(vocab)
        self.w2i = {w: i for i, w in enumerate(vocab)}
        
        # Initialiser les angles sur le cercle uniformement
        # (pas la spirale π/6 — on part de zero et on laisse l'entrainement faire)
        self.theta = np.linspace(0, 2 * np.pi, self.vocab_size, endpoint=False)
        np.random.seed(42)
        np.random.shuffle(self.theta)
        
        # Rayons preserves de la spirale (pour l'amplitude frequentielle)
        AREA_UNIT = (2.0 * np.pi) ** 2 / self.vocab_size
        self.radius = np.array([
            math.sqrt((i + 0.5) * AREA_UNIT / math.pi)
            for i in range(self.vocab_size)
        ])
    
    def build_pairs(self, phrases: List[str], window: int = 8,
                     max_pairs: int = 100000) -> Tuple[List, List]:
        """
        Construit les paires co-occurrentes et negatives.
        
        Args:
            phrases: liste de textes
            window: fenetre de co-occurrence (mots avant/apres)
            max_pairs: nombre max de paires
        
        Returns:
            (paires_positives, paires_negatives)
        """
        print(f"Building pairs from {len(phrases)} phrases (window={window})...")
        
        # Compter les co-occurrences
        pair_counts = Counter()
        total_pairs = 0
        
        for phrase in phrases:
            words = re.findall(r'\b[a-zA-ZÀ-ÿ]{2,}\b', phrase.lower())
            words = [w for w in words if w in self.w2i]
            
            for i, w1 in enumerate(words):
                for j in range(i + 1, min(i + window + 1, len(words))):
                    w2 = words[j]
                    if w1 != w2:
                        pair = (self.w2i[w1], self.w2i[w2])
                        pair_counts[pair] += 1
                        total_pairs += 1
                        if total_pairs >= max_pairs:
                            break
                if total_pairs >= max_pairs:
                    break
            if total_pairs >= max_pairs:
                break
        
        # Top paires positives (les plus frequentes)
        top_pairs = pair_counts.most_common(max_pairs)
        positive = [(a, b) for (a, b), _ in top_pairs]
        pos_set = set(positive)
        
        # Paires negatives (paires aleatoires NON co-occurrentes)
        negative = []
        np.random.seed(42)
        while len(negative) < len(positive):
            a = np.random.randint(0, self.vocab_size)
            b = np.random.randint(0, self.vocab_size)
            if a != b and (a, b) not in pos_set and (b, a) not in pos_set:
                negative.append((a, b))
        
        print(f"  Positive pairs: {len(positive)}")
        print(f"  Negative pairs: {len(negative)}")
        return positive, negative
    
    def train(self, positive_pairs: List[Tuple], negative_pairs: List[Tuple],
              epochs: int = 50, lr: float = 0.01, verbose: bool = True):
        """
        Entraine les angles par SGD (paire par paire).
        
        Chaque paire positive attire, chaque paire negative repousse.
        Le SGD evite les annulations de gradients conflictuels
        qui se produisent en batch avec beaucoup de paires.
        """
        pos = np.array(positive_pairs)
        neg = np.array(negative_pairs)
        n_pos = len(pos)
        n_neg = len(neg)
        
        for epoch in range(epochs):
            total_loss = 0.0
            
            # Melanger les paires
            idx_pos = np.random.permutation(n_pos)
            idx_neg = np.random.permutation(n_neg)
            
            # SGD sur paires positives (attraction)
            for i in idx_pos:
                a, b = pos[i]
                delta = self.theta[a] - self.theta[b]
                cos_d = np.cos(delta)
                sin_d = np.sin(delta)
                
                # Loss = (1 - cos)²
                loss = (1.0 - cos_d) ** 2
                total_loss += loss
                
                # Gradient: dLoss/dθ_a = 2(1-cos)sin
                grad = 2.0 * (1.0 - cos_d) * sin_d
                self.theta[a] -= lr * grad
                self.theta[b] += lr * grad
            
            # SGD sur paires negatives (repulsion)
            for i in idx_neg:
                c, d = neg[i]
                delta = self.theta[c] - self.theta[d]
                cos_d = np.cos(delta)
                sin_d = np.sin(delta)
                
                # Loss = (cos + 1)² / 4  →  min quand cos=-1
                loss = (cos_d + 1.0) ** 2 / 4.0
                total_loss += loss
                
                # Gradient: dLoss/dθ_c = (cos+1)sin/2
                grad = (cos_d + 1.0) * sin_d / 2.0
                self.theta[c] -= lr * grad
                self.theta[d] += lr * grad
            
            self.theta = self.theta % (2 * np.pi)
            total_loss /= (n_pos + n_neg)
            
            if verbose and (epoch + 1) % 10 == 0:
                # Mesurer la qualite
                a_idx, b_idx = pos[:, 0], pos[:, 1]
                cos_pos_mean = np.mean(np.cos(self.theta[a_idx] - self.theta[b_idx]))
                c_idx, d_idx = neg[:, 0], neg[:, 1]
                cos_neg_mean = np.mean(np.cos(self.theta[c_idx] - self.theta[d_idx]))
                print(f"  Epoch {epoch+1}/{epochs}: loss={total_loss:.4f}, "
                      f"cos_pos={cos_pos_mean:.3f}, cos_neg={cos_neg_mean:.3f}")
        
        return total_loss
    
    def get_wave_vectors(self) -> Tuple[np.ndarray, np.ndarray]:
        """Retourne les (kx, ky) entraines."""
        kx = self.radius * np.cos(self.theta)
        ky = self.radius * np.sin(self.theta)
        return kx, ky
    
    def inject_into_tokenizer(self, tokenizer):
        """
        Injecte les vecteurs d'onde entraines dans un tokenizer.
        
        Le tokenizer doit avoir _kx et _ky comme attributs numpy
        de taille vocab_size (ou vocab_size + 256 pour les caracteres).
        """
        kx, ky = self.get_wave_vectors()
        vs = min(len(kx), len(tokenizer._kx))
        tokenizer._kx[:vs] = kx[:vs]
        tokenizer._ky[:vs] = ky[:vs]
    
    def show_neighbors(self, word: str, top_k: int = 8):
        """Affiche les plus proches voisins d'un mot (par similarite cosinus d'angle)."""
        if word not in self.w2i:
            print(f"  '{word}' not in vocabulary")
            return
        
        idx = self.w2i[word]
        theta_w = self.theta[idx]
        
        similarities = np.cos(theta_w - self.theta)
        # Exclure le mot lui-meme
        similarities[idx] = -2.0
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        print(f"  Neighbors of '{word}':")
        for i in top_indices:
            print(f"    {self.vocab[i]:20s} (cos={similarities[i]:.3f})")


def load_clean_corpus(max_phrases: int = 2000) -> List[str]:
    """Charge le corpus nettoye (Wikipedia uniquement)."""
    phrases = []
    for path in sorted(_CORPUS_DIR.glob("*.txt")):
        name = path.name.lower()
        if '_rejected' in str(path) or path.stat().st_size < 500:
            continue
        # Skipper les fichiers de geographie (dominent le signal)
        if 'geograph' in name:
            continue
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if 20 < len(line) < 300 and len(line.split()) > 3:
                    phrases.append(line)
                    if len(phrases) >= max_phrases:
                        break
        if len(phrases) >= max_phrases:
            break
    return phrases


def build_vocab(phrases: List[str], max_words: int = 1500) -> List[str]:
    """Construit le vocabulaire etendu — TOUS les mots du corpus en premier."""
    word_counts = Counter()
    for p in phrases:
        for w in re.findall(r'\b[a-z]{3,}\b', p.lower()):
            word_counts[w] += 1
    
    # Prendre les mots les plus frequents du corpus
    vocab = [w for w, _ in word_counts.most_common(max_words)]
    # Ajouter VOCABULAIRE_BASE en dessous si pas deja presents
    for w in VOCABULAIRE_BASE:
        if w not in vocab and len(vocab) < max_words + 300:
            vocab.append(w)
    return vocab[:max_words]


def demo():
    """Demonstration complete."""
    print("=" * 60)
    print("WAVE2VEC — Entrainement des vecteurs d'onde")
    print("=" * 60)
    print()
    
    # Charger corpus
    print("Loading corpus...")
    phrases = load_clean_corpus(3000)
    print(f"  {len(phrases)} phrases")
    
    # Vocabulaire
    vocab = build_vocab(phrases, 1500)
    print(f"  {len(vocab)} words")
    
    # Entrainer
    w2v = Wave2Vec(vocab)
    pos, neg = w2v.build_pairs(phrases, window=8, max_pairs=50000)
    
    print("\nTraining...")
    t0 = time.time()
    loss = w2v.train(pos, neg, epochs=30, lr=0.1)
    print(f"  Done in {time.time()-t0:.0f}s, final loss={loss:.4f}")
    
    # Visualiser
    print()
    for word in ['relativite', 'resonance', 'philosophie', 'conscience', 'ondes', 'einstein', 'physique']:
        w2v.show_neighbors(word)
    
    # Tester la generation avec vecteurs entraines
    print("\n" + "=" * 60)
    print("Testing generation with trained wave vectors...")
    print("=" * 60)
    
    from fast_resonance_generator import FastResonanceGenerator
    gen = FastResonanceGenerator(vocab, nx=128, ny=128, n_lecteurs=2)
    
    # Injecter les vecteurs entraines dans le tokenizer du generateur
    w2v.inject_into_tokenizer(gen._gen.tokenizer)
    
    # Amorcer avec les memes phrases
    for p in phrases[:50]:
        gen.apprendre(p, amplitude=0.6)
    print(f"Seeded: {gen.experience_count} exp")
    
    for q in [
        'explique la theorie de la relativite',
        'comment fonctionne la resonance des ondes',
        'qu est ce que la conscience',
    ]:
        r = gen.generer(q, max_tokens=12, temperature=0.7, top_k=20)
        print(f"\n>> {q}")
        print(f"<< {r['texte_genere']}")
        print(f"   ({r['n_tokens']}t, {r['temps_ms']:.0f}ms)")


if __name__ == '__main__':
    demo()
