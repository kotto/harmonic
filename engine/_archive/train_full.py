"""
Pipeline complet : wave2vec + hologramme + generation
======================================================
1. Charge tout le corpus propre (27k lignes)
2. Entraine wave2vec (5000 mots, early stopping)
3. Amorçe l'hologramme avec le corpus
4. Injecte les vecteurs entraines
5. Teste la generation

Usage: python train_full.py
"""

import sys, os, re, math, time, json
from pathlib import Path
from collections import Counter
import numpy as np

# Chemins
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_HARMONIC_TRAINING = _PROJECT_ROOT / "harmonic_training"
_CORPUS_DIR = _PROJECT_ROOT / "data" / "corpus"
_OUTPUT_DIR = _PROJECT_ROOT / "data" / "hologram_output"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_HARMONIC_TRAINING))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model.harmonic_resonance_generator import VOCABULAIRE_BASE, HologrammeMonde, TokeniseurOndes
from wave2vec import Wave2Vec
from fast_resonance_generator import FastResonanceGenerator

PHI = (1 + math.sqrt(5)) / 2


def load_all_corpus(max_phrases: int = 50000) -> list:
    """Charge toutes les phrases du corpus propre."""
    phrases = []
    for path in sorted(_CORPUS_DIR.glob("*.txt")):
        name = path.name.lower()
        if '_rejected' in str(path) or path.stat().st_size < 500:
            continue
        if 'geograph' in name:  # skip geography to avoid domination
            continue
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if 15 < len(line) < 300 and len(line.split()) > 2:
                    phrases.append(line)
                    if len(phrases) >= max_phrases:
                        break
        if len(phrases) >= max_phrases:
            break
    return phrases


def build_large_vocab(phrases: list, max_words: int = 5000) -> list:
    """Vocabulaire large : mots frequents du corpus + base harmonique."""
    word_counts = Counter()
    for p in phrases:
        for w in re.findall(r'\b[a-z]{3,}\b', p.lower()):
            word_counts[w] += 1
    
    # Top mots du corpus
    vocab = [w for w, _ in word_counts.most_common(max_words)]
    
    # Ajouter la base harmonique si absente
    for w in VOCABULAIRE_BASE:
        if w not in vocab:
            vocab.append(w)
    
    return vocab[:max_words]


def main():
    print("=" * 60)
    print("PIPELINE COMPLET : wave2vec + hologramme + generation")
    print("=" * 60)
    print()
    
    # ============================================================
    # 1. CHARGER LE CORPUS
    # ============================================================
    print("[1/5] Loading corpus...")
    t0 = time.time()
    phrases = load_all_corpus()
    print(f"  {len(phrases)} phrases ({time.time()-t0:.0f}s)")
    
    # ============================================================
    # 2. VOCABULAIRE
    # ============================================================
    print("\n[2/5] Building vocabulary...")
    vocab = build_large_vocab(phrases, 5000)
    print(f"  {len(vocab)} words (top: {vocab[:10]})")
    
    # ============================================================
    # 3. WAVE2VEC
    # ============================================================
    print("\n[3/5] Training wave2vec...")
    w2v = Wave2Vec(vocab)
    pos, neg = w2v.build_pairs(phrases, window=5, max_pairs=30000)
    print(f"  Pairs: {len(pos)} positive, {len(neg)} negative")
    
    # Entrainer avec early stopping
    best_cos = 0.0
    patience = 0
    
    # Mini-batch training (SGD is slow for many pairs)
    for epoch in range(30):
        # Shuffle
        idx = np.random.permutation(len(pos))
        losses = []
        
        for i in idx[:10000]:  # 10k paires par epoch
            a, b = pos[i]
            delta = w2v.theta[a] - w2v.theta[b]
            cos_d = np.cos(delta)
            sin_d = np.sin(delta)
            
            # Attraction: loss = (1-cos)², grad = 2(1-cos)sin
            grad = 0.05 * 2.0 * (1.0 - cos_d) * sin_d
            w2v.theta[a] -= grad
            w2v.theta[b] += grad
            
            losses.append((1.0 - cos_d) ** 2)
        
        # Repulsion (moins de paires)
        idx_neg = np.random.permutation(len(neg))
        for i in idx_neg[:3000]:
            c, d = neg[i]
            delta = w2v.theta[c] - w2v.theta[d]
            cos_d = np.cos(delta)
            sin_d = np.sin(delta)
            
            # Repulsion: loss = (cos+1)²/4, grad = (cos+1)sin/2
            grad = 0.03 * (cos_d + 1.0) * sin_d / 2.0
            w2v.theta[c] -= grad
            w2v.theta[d] += grad
        
        w2v.theta = w2v.theta % (2 * np.pi)
        
        # Evaluer
        a_idx = np.array([p[0] for p in pos[:1000]])
        b_idx = np.array([p[1] for p in pos[:1000]])
        cos_pos = float(np.mean(np.cos(w2v.theta[a_idx] - w2v.theta[b_idx])))
        
        avg_loss = float(np.mean(losses))
        
        if epoch % 5 == 0 or cos_pos > best_cos:
            print(f"  Epoch {epoch+1:2d}/30: loss={avg_loss:.4f}, cos_pos={cos_pos:.3f}")
        
        # Early stopping: entre 0.6 et 0.8 c'est bon
        if 0.6 < cos_pos < 0.85:
            if cos_pos > best_cos:
                best_cos = cos_pos
                patience = 0
            else:
                patience += 1
            if cos_pos > 0.75 or patience > 8:
                print(f"  Early stop: cos_pos={cos_pos:.3f}")
                break
        elif cos_pos >= 0.85:
            print(f"  Collapse detected (cos_pos={cos_pos:.3f}), reducing LR...")
            break
    
    # Sauvegarder les vecteurs
    kx, ky = w2v.get_wave_vectors()
    np.savez(str(_OUTPUT_DIR / "wave2vec_vectors.npz"), kx=kx, ky=ky)
    print(f"  Vectors saved (cos_pos={cos_pos:.3f})")
    
    # ============================================================
    # 4. AMORCER L'HOLOGRAMME
    # ============================================================
    print("\n[4/5] Seeding hologram...")
    gen = FastResonanceGenerator(vocab, nx=256, ny=256, n_lecteurs=4)
    
    # Injecter les vecteurs entraines dans le tokenizer
    vs = min(len(kx), len(gen._gen.tokenizer._kx))
    gen._gen.tokenizer._kx[:vs] = kx[:vs]
    gen._gen.tokenizer._ky[:vs] = ky[:vs]
    print(f"  Wave vectors injected into tokenizer")
    
    # Amorcer par batches
    batch_size = 200
    for i in range(0, len(phrases), batch_size):
        batch = phrases[i:i+batch_size]
        for p in batch:
            gen.apprendre(p, amplitude=0.3)
        if (i + batch_size) % 2000 == 0:
            print(f"  [{i+batch_size}/{len(phrases)}] energy={gen.energy:.0f}")
    
    print(f"  Seeded: {gen.experience_count} exp, Energy: {gen.energy:.0f}")
    
    # ============================================================
    # 5. TESTER LA GENERATION
    # ============================================================
    print("\n[5/5] Testing generation...")
    print("=" * 60)
    
    tests = [
        "explique la theorie de la relativite",
        "comment fonctionne la resonance des ondes",
        "qu est ce que la philosophie",
        "decris le principe de la mecanique quantique",
        "quelle est la nature de la conscience",
    ]
    
    for q in tests:
        r = gen.generer(q, max_tokens=15, temperature=0.7, top_k=20)
        print(f"\n>> {q}")
        print(f"<< {r['texte_genere']}")
        print(f"   ({r['n_tokens']}t, {r['temps_ms']:.0f}ms, div={r['diversite']:.2f})")
    
    # ============================================================
    # SAUVEGARDE
    # ============================================================
    print(f"\n{'='*60}")
    elapsed = time.time() - t0
    print(f"Pipeline complete in {elapsed:.0f}s ({elapsed/60:.1f}min)")
    
    # Sauvegarder l'hologramme
    np.save(str(_OUTPUT_DIR / "hologram_trained.npy"), gen._gen.monde.H)
    print(f"Hologram saved: {_OUTPUT_DIR / 'hologram_trained.npy'}")
    print(f"Vectors saved: {_OUTPUT_DIR / 'wave2vec_vectors.npz'}")
    print(f"Energy: {gen.energy:.0f}")


if __name__ == '__main__':
    main()
