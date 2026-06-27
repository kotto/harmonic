#!/usr/bin/env python3
"""Diagnostic : vocabulaire vs tokens stockes dans l'hologramme."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from harmonic_training.model.harmonic_resonance_generator import (
    VOCABULAIRE_BASE, TokeniseurOndes
)

# 1. Taille du vocabulaire
print(f"=== VOCABULAIRE ===")
print(f"VOCABULAIRE_BASE: {len(VOCABULAIRE_BASE)} tokens")
print(f"Mots significatifs: {len(VOCABULAIRE_BASE) - 4} (hors <PAD>,<UNK>,<BOS>,<EOS>)")

# 2. Hologramme
H = np.load("ka_knowledge_base/hologramme.npy")
print(f"\n=== HOLOGRAMME ===")
print(f"Shape: {H.shape} ({H.size} valeurs complexes)")
print(f"Energie: {np.sum(np.abs(H)**2):.2e}")

# 3. Tokenisation test
tokenizer = TokeniseurOndes(VOCABULAIRE_BASE)
mots_test = ['dix', 'creation', 'science', 'ghana', 'empire', 
             'relativite', 'infarctus', 'conscience', 'afrique',
             'hypertension', 'algorithme', 'fibrillation']
print(f"\n=== TEST TOKENISATION ===")
for mot in mots_test:
    tokens = tokenizer.tokeniser(mot)
    noms = [tokenizer.i2w.get(t, '<UNK>') for t in tokens]
    signal = "⚠️ <UNK>" if 1 in tokens else "✅ connu"
    print(f"  '{mot:15s}' -> {str(noms):30s} {signal}")

# 4. Mots uniques dans VOCABULAIRE_BASE vs ce qui est stocke
token_set = set(VOCABULAIRE_BASE[4:])  # Skip special tokens
print(f"\n=== ANALYSE ===")
print(f"Mots uniques dans VOCABULAIRE_BASE: {len(token_set)}")

# 5. Progress.json
with open("ka_knowledge_base/progress.json") as f:
    progress = json.load(f)
print(f"\n=== PROGRESS.JSON ===")
print(f"Total tokens stored: {progress.get('total_tokens', 'N/A')}")
print(f"Sources: {progress.get('sources_completes', 'N/A')}")
print(f"Energie: {progress.get('energie_hologramme', 'N/A')}")

# 6. Combien de tokens peut-on stocker theoriquement ?
# 64x64 = 4096 valeurs complexes. Chaque token = onde plane.
# The capacity depends on interference patterns, not on vocabulary size.
print(f"\n=== CAPACITE ===")
print(f"Taille matrice: {H.size} valeurs complexes = {H.size * 16} bytes (128 bytes per complex128)")
print(f"Experiences (n_experiences): ~172872")
print(f"Mais seulement {len(VOCABULAIRE_BASE)} signatures d'onde distinctes lisibles")
print(f"Probleme: TOUT mot hors vocabulaire -> <UNK> (id=1)")
print(f"Solution: Etendre VOCABULAIRE_BASE avec les termes des connaissances injectees")
