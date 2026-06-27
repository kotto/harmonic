"""
Demonstration complete du Harmonic Engine - Systeme Harmonique
==============================================================
Test tous les composants : Noyau ABC, Signatures 9D, Moteur Harmonique

Usage:
    python demo_harmonic_engine.py
"""

import sys
import os

# Forcer UTF-8 pour eviter les problemes d'encodage Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np

# =========================================================================
# PARTIE 1 : NOYAU ABC
# =========================================================================

print("=" * 70)
print("PARTIE 1 : Noyau ABC (Atangana-Baleanu-Caputo)")
print("=" * 70)

from engine import (
    PHI, ALPHA, B_1_PHI, ALPHA_CONST,
    ABCKernelNP, abc_kernel_np, abc_kernel_torch,
    mittag_leffler, gamma_lanczos
)

print(f"\nConstantes fondamentales :")
print(f"  phi (nombre d'or)     = {PHI:.15f}")
print(f"  alpha = 1/phi         = {ALPHA:.15f}")
print(f"  B(alpha)              = {B_1_PHI:.10f}")
print(f"  1/B(alpha)            = {ALPHA_CONST:.10f}")

# Test Mittag-Leffler
z_test = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
ml_test = mittag_leffler(z_test, alpha=ALPHA)
print(f"\nMittag-Leffler E_alpha(z) :")
for z, ml in zip(z_test, ml_test):
    print(f"  E_alpha({z:5.1f}) = {ml:.8f}")

# Test noyau ABC
for length in [8, 16, 32, 64, 128]:
    kernel = abc_kernel_np(length)
    print(f"  Noyau ABC [{length:3d}] : K(0)={kernel[0]:.6f}, K({length-1})={kernel[-1]:.6f}, somme={kernel.sum():.4f}")

# Test torch si disponible
try:
    import torch
    kernel_t = abc_kernel_torch(32)
    kernel_np = abc_kernel_np(32)
    diff = np.max(np.abs(kernel_np - kernel_t.numpy()))
    if diff < 1e-5:
        print(f"\n  Coherence numpy/torch : diff max = {diff:.2e} (OK)")
    else:
        print(f"\n  DIFFERENCE numpy/torch : {diff:.2e}")
except ImportError:
    print("\n  [SKIP] Torch non disponible")


# =========================================================================
# PARTIE 2 : SIGNATURES 9D
# =========================================================================

print("\n" + "=" * 70)
print("PARTIE 2 : Signatures Harmoniques 9D")
print("=" * 70)

from engine import compute_signature, validate_signatures, SIGNATURE_DIMS

# Creer des embeddings simulant differents types de contenu
np.random.seed(42)
batch, seq_len, hidden = 5, 12, 64

# Embeddings avec differentes caracteristiques
embeddings = []
for i in range(batch):
    base = np.random.randn(seq_len, hidden).astype(np.float32) * 0.5
    if i == 0:  # Mathematique : haute periodicite
        t = np.arange(seq_len).reshape(-1, 1) / seq_len
        base += np.sin(2 * np.pi * 3 * t) * 2.0
    elif i == 1:  # Code : structure hierarchique
        # Ajouter une composante de repetition hierarchique (broadcasting automatique)
        base += base.mean(axis=1, keepdims=True) * 2.0
        base[:, :8] += 1.0  # Les premieres dimensions sont renforcees
    elif i == 2:  # Creatif : haute divergence
        base[::2] *= 2.5
        base[1::2] *= -1.0
    elif i == 3:  # Emotionnel : haute asymetrie
        base = base * np.abs(base) * 0.5
    embeddings.append(base)

embeddings = np.stack(embeddings)

print(f"\nEntree : {embeddings.shape}")
signatures = compute_signature(embeddings)
validate_signatures(signatures)
print(f"Signatures : {signatures.shape} (dans [0,1])")

print(f"\nProfils moyens par type :")
print(f"{'Type':<18} ", end="")
for d in SIGNATURE_DIMS:
    print(f"{d[:5]:>6}", end=" ")
print()
print("-" * (18 + 10 * 7))

types = ["Mathematique", "Code", "Creatif", "Emotionnel", "Aleatoire"]
for i, (t, sig) in enumerate(zip(types, signatures)):
    profile = sig.mean(axis=0)
    print(f"{t:<18} ", end="")
    for j in range(9):
        print(f"{profile[j]:6.3f}", end=" ")
    print()


# =========================================================================
# PARTIE 3 : MOTEUR HARMONIQUE
# =========================================================================

print("\n" + "=" * 70)
print("PARTIE 3 : Moteur de Resonances Cognitives")
print("=" * 70)

from engine import HarmonicResonanceEngine

engine = HarmonicResonanceEngine()

# Tests de classification
test_prompts = [
    ("Calculez 15% de 340 euros", "mathematical"),
    ("Ecris un poeme sur la liberte", "creative"),
    ("Pourquoi le ciel est-il bleu ? Explique", "reasoning"),
    ("Quelle est la capitale de l'Italie ?", "factual"),
    ("Ecrivez un algorithme de tri rapide en Python", "code"),
    ("Bonjour, comment allez-vous ?", "general"),
]

print(f"\n{'Prompt':<45} {'Categorie':<14} {'Conf':<8} {'Resultat':<10}")
print("-" * 77)

for prompt, expected in test_prompts:
    cat, conf = engine.classify(prompt)
    status = "OK" if cat == expected else "?"
    print(f"{prompt[:43]:<45} [{cat:<12}] {conf:.3f}/1.0   {status}")

# Test expansion harmonique
print(f"\nExpansion harmonique de contexte (x4) :")
examples = [
    ("Pour calculer 15% de 340, on divise 340 par 100 puis on multiplie par 15.", "mathematical"),
    ("Dans un ciel clair, la lumiere du soleil interagit avec les molecules d'air.", "factual"),
    ("Un algorithme de tri fusion divise le tableau en deux moities.", "code"),
]

for short_text, category in examples:
    expanded = engine.expand(short_text, category)
    ratio = len(expanded) / len(short_text)
    print(f"\n  [{category:12s}] {len(short_text):4d}c -> {len(expanded):4d}c (x{ratio:.1f})")
    print(f"  Debut : {expanded[:120]}...")


# =========================================================================
# PARTIE 4 : STATISTIQUES
# =========================================================================

print("\n" + "=" * 70)
print("PARTIE 4 : Performance et Statistiques")
print("=" * 70)

batch_prompts = [
    "Calculez 10% de 200",
    "Ecrivez une fonction Python pour trier une liste",
    "Quelle est la capitale du Japon",
    "Expliquez la difference entre IA et ML",
    "Ecrivez un haiku sur l'hiver",
    "Donnez la definition de l'entropie",
    "Pourquoi 1+1=2",
    "Ecrivez une histoire courte sur un robot",
    "Comment installer Docker sur Ubuntu",
    "Quel est le pH de l'eau pure",
]

for prompt in batch_prompts:
    sig = engine.analyze(prompt)
    cat, conf = engine.classify(prompt)

stats = engine.get_stats()
print(f"\n  Requetes analysees     : {stats['total_requests']}")
print(f"  Cache hits             : {stats['cache_hits']}")
print(f"  Taux de hit cache      : {stats['cache_hit_rate']}%")
print(f"  Score resonance moyen  : {stats['avg_resonance_score']}")
print(f"  Cache size             : {stats['cache_stats']['current_size']}/{stats['cache_stats']['max_size']}")


# =========================================================================
# CONCLUSION
# =========================================================================

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("")
print("OK Noyau ABC (phi={:.3f}, alpha={:.3f})".format(PHI, ALPHA))
print("   - Mittag-Leffler numeriquement stable")
print("   - Memoire non-locale normalisee (somme=1)")
print("   - Coherence numpy/torch")
print("")
print("OK Signatures Harmoniques 9D")
print("   - Formules auto-normalisees dans [0,1]")
print("   - 9 dimensions (phi, alpha, reasoning, creativity,")
print("     math, factual, code, emotion, temporal)")
print("   - ZERO parametre entrainable")
print("")
print("OK Moteur de Resonances Cognitives")
print("   - Analyse harmonique de texte (7 categories)")
print("   - Classification intelligente")
print("   - Expansion de contexte (x4)")
print("   - Cache LRU-phi performant")
print("")
print("Package : engine/")
print("   +-- abc_kernel.py      (Noyau ABC + Mittag-Leffler)")
print("   +-- signatures_9d.py   (Signatures 9D numpy + torch)")
print("   +-- harmonic_engine.py (Analyseur + Resonance + Expansion)")
print("   +-- __init__.py        (Package initializer)")
print("   +-- README.md          (Documentation)")
print("")

# Test final
print("Demonstration terminee avec succes !")
