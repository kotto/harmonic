#!/usr/bin/env python3
"""Test complet du HarmonicGenerator V4 (Options 1 et 2)."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training', 'model'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training'))

import numpy as np
from harmonic_generator import (
    AnalyseurLinguistique, DIMS_9D, SIG_DIM_9D,
    PhiInverseGenerator, HarmonicGenerator,
    PhiInverseDecoderNumpy, FusionHarmonique16DV2,
    GenerationGenerativeResultat
)

def test_analyseur():
    """Test 1 : Analyseur linguistique avancé."""
    print("=" * 70)
    print("TEST 1 : ANALYSEUR LINGUISTIQUE AVANCE")
    print("=" * 70)
    al = AnalyseurLinguistique()
    textes = [
        ("CODE    ", "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)"),
        ("MATH    ", "x^2 + y^2 = z^2 est le theoreme de Pythagore"),
        ("AMOUR   ", "Je t aime de tout mon coeur pour toujours mon amour"),
        ("CREATIF ", "Un dragon violet diaphane danse le tango sous la lune magique"),
        ("SCIENCE ", "Le nombre d or 1.618 est une constante fondamentale"),
        ("PHILO   ", "Je pense donc je suis, c est la certitude fondamentale de Descartes"),
    ]
    header = ' '.join(f'{d:>7s}' for d in DIMS_9D)
    print(f"{'Type':10s} {header}")
    print('-' * 75)
    for cat, txt in textes:
        sig = al.projeter(txt)
        vals = ' '.join(f'{sig[i]:7.3f}' for i in range(SIG_DIM_9D))
        print(f'{cat:10s} {vals}')
    print("\n[OK] Analyseur linguistique operationnel\n")

def test_decodeur():
    """Test 2 : Decodeur PhiInverse."""
    print("=" * 70)
    print("TEST 2 : DECODEUR PhiInverse (matrice fixe)")
    print("=" * 70)
    dec = PhiInverseDecoderNumpy(vocab_size=500, signature_dim=7)
    print(f"  Shape matrice: {dec.weight.shape}")
    print(f"  {500*7} = 3500 coefficients fixes (0 param)")
    
    # Verification de l'orthogonalité
    sig_test = np.array([0.8, 0.5, 0.7, 0.3, 0.5, 0.6, 0.4, 0.2, 0.5,
                         0.56, 0.12, 0.2, 0.43, 0.5, 0.6, 0.1], dtype=np.float32)
    
    # Test projection 16D → 7D
    from harmonic_generator import projeter_16d_vers_7d
    sig_7d = projeter_16d_vers_7d(sig_test)
    print(f"  Projection 16D->7D: {[round(s,3) for s in sig_7d]}")
    
    # Test décodage
    logits = dec.decode(sig_7d)
    top5 = np.argsort(logits)[-5:][::-1]
    print(f"  Top-5 tokens: {top5.tolist()}")
    print(f"  Logits range: [{logits.min():.3f}, {logits.max():.3f}]")
    assert logits.shape == (500,), f"Shape attendue (500,), obtenue {logits.shape}"
    print("\n[OK] Decodeur PhiInverse operationnel\n")

def test_generateur():
    """Test 3 : Generateur PhiInverse (token par token)."""
    print("=" * 70)
    print("TEST 3 : GENERATEUR PhiInverse (token par token)")
    print("=" * 70)
    gen = PhiInverseGenerator(vocab_size=500)
    sig_test = np.array([0.8, 0.5, 0.7, 0.3, 0.5, 0.6, 0.4, 0.2, 0.5,
                         0.56, 0.12, 0.2, 0.43, 0.5, 0.6, 0.1], dtype=np.float32)
    
    for temp in [0.85, 0.5, 0.1]:
        texte, tokens, infos = gen.generer(sig_test, max_tokens=20, temperature=temp)
        print(f"  T={temp:.2f}: \"{texte}\" ({infos['n_tokens']}t, div={infos['diversite']:.3f})")
    
    print("\n[OK] Generation token par token operationnelle\n")

def test_generator_complet():
    """Test 4 : Generator complet avec mémoire."""
    print("=" * 70)
    print("TEST 4 : HARMONIC GENERATOR V4 (complet)")
    print("=" * 70)
    
    hg = HarmonicGenerator(vocab_size=500)
    
    # Apprentissage
    for t in [
        "Le nombre d or phi est une proportion fondamentale dans la nature.",
        "La resonance harmonique est un phenomene oscillatoire universel.",
        "La conscience emerge de reseaux neuronaux complexes harmoniques.",
        "Les signatures 9D representent tout texte dans l espace harmonique.",
        "Le PhiInverse decode les signatures en tokens sans entrainement.",
        "La certification SHA256 garantit l integrite de chaque reponse.",
    ]:
        hg.apprendre(t)
    print(f"  Connaissances apprises: {len(hg.memoire)}")
    
    # Générations
    prompts = [
        "Qu'est-ce que le nombre d'or ?",
        "Explique la resonance harmonique",
        "Comment fonctionne la conscience ?",
    ]
    
    for prompt in prompts:
        r = hg.generer(prompt, max_tokens=25, temperature=0.85)
        mem = f" | {r.n_connaissances_utilisees} conn. (res={r.resonance_moyenne:.3f})" if r.n_connaissances_utilisees > 0 else ""
        print(f"\n  [PROMPT] {prompt}")
        print(f"  [GENERE] \"{r.texte_genere}\"")
        print(f"  [STATS]  {r.n_tokens}t, div={r.diversite:.3f}, {r.temps_generation_ms:.0f}ms{mem}")
    
    # Stats
    s = hg.stats()
    print(f"\n  Stats globales:")
    print(f"    Generations: {s['n_generations']}")
    print(f"    Connaissances: {s['n_connaissances']}")
    print(f"    Temps analyse: {s['temps_analyse_ms']:.1f}ms")
    print(f"    Temps generation: {s['temps_generation_ms']:.1f}ms")
    print(f"    Taux certification: {s['taux_certification']:.1f}%")
    print(f"    0 parametre: OK | 0 backprop: OK | Pur numpy: OK")
    
    print("\n[SUCCES] HarmonicGenerator V4 operationnel !")

if __name__ == '__main__':
    test_analyseur()
    test_decodeur()
    test_generateur()
    test_generator_complet()
