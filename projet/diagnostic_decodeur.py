#!/usr/bin/env python3
"""Diagnostic complet du décodeur PhiInverse."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training', 'model'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training'))

import numpy as np
from harmonic_generator import PhiInverseDecoderNumpy, TokenizerSimple, _TOP_MOTS, PHI

print("=" * 70)
print("DIAGNOSTIC COMPLET DECODEUR PhiInverse")
print("=" * 70)

# 1. Vocabulaire
tok = TokenizerSimple(_TOP_MOTS[:500])
print(f"\n1. VOCABULAIRE: {tok.vocab_size} tokens")
unk = sum(1 for i in range(tok.vocab_size) if '<UNK>' in tok.decode([i]))
print(f"   Tokens <UNK>: {unk}/{tok.vocab_size}")

# 2. Décodeur
dec = PhiInverseDecoderNumpy(500)
print(f"\n2. MATRICE: {dec.weight.shape}")
print(f"   Fréquences [0..4]: {[f'{f:.4f}' for f in dec.freq[:5]]}")
print(f"   Fréquences [495..499]: {[f'{f:.4f}' for f in dec.freq[-5:]]}")
print(f"   Poids min: {dec.weight.min():.6f}, max: {dec.weight.max():.6f}")

# 3. Test avec signatures types
for label, sig in [
    ("SIG=0", np.zeros(7, dtype=np.float32)),
    ("SIG=0.5", np.ones(7, dtype=np.float32) * 0.5),
    ("SIG=1.0     ", np.ones(7, dtype=np.float32)),
    ("SIG=[1,0,1,0,1,0,1]", np.array([1,0,1,0,1,0,1], dtype=np.float32)),
    ("SIG=[0,1,0,1,0,1,0]", np.array([0,1,0,1,0,1,0], dtype=np.float32)),
    ("SIG=PHI", np.ones(7, dtype=np.float32) * (1/PHI)),
]:
    logits = dec.decode(sig)
    top5 = np.argsort(logits)[-5:][::-1]
    bot5 = np.argsort(logits)[:5]
    top_words = [tok.decode([t]) for t in top5]
    bot_words = [tok.decode([t]) for t in bot5]
    print(f"\n3. {label}:")
    print(f"   Range: [{logits.min():.6f}, {logits.max():.6f}]")
    print(f"   Mean: {logits.mean():.6f}, Std: {logits.std():.6f}")
    print(f"   Top-5: {top_words}")
    print(f"   Bot-5: {bot_words}")
    print(f"   Logits(top): {[f'{logits[t]:.6f}' for t in top5]}")

# 4. Test de projection 16D -> 7D
from harmonic_generator import AnalyseurLinguistique, Fusion16D
al = AnalyseurLinguistique()
fus = Fusion16D()

tests_prompts = [
    "Le nombre d or est une proportion fondamentale",
    "Je t aime de tout mon coeur",
    "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)",
    "Explique la mecanique quantique en detail",
]

for p in tests_prompts:
    s9 = al.projeter(p)
    s16 = fus.fusionner(s9)
    s7 = np.zeros(7, dtype=np.float32)
    s7[0] = s16[0]; s7[1] = s16[1]
    s7[2] = s16[2]*0.7 + s16[14]*0.3
    s7[3] = s16[3]*0.6 + s16[10]*0.4
    s7[4] = s16[4]*0.6 + s16[11]*0.4
    s7[5] = s16[5]
    s7[6] = s16[6]*0.7 + s16[9]*0.3
    
    logits = dec.decode(s7)
    top5 = np.argsort(logits)[-5:][::-1]
    top_words = [tok.decode([t]) for t in top5]
    print(f"\n4. PROMPT: \"{p}\"")
    print(f"   S7: {[f'{v:.3f}' for v in s7]}")
    print(f"   Top-5: {top_words}")
    print(f"   Logits: {[f'{logits[t]:.4f}' for t in top5]}")

print("\n" + "=" * 70)
print("DIAGNOSTIC TERMINE")
print("=" * 70)
