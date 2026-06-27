#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark Grande Échelle — IA Harmono-Holographique
===================================================
Test de performance à 5000, 10000, 20000+ connaissances.
Mesures : temps, énergie, saturation, précision, robustesse.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, time, sys, os, gc
import numpy as np
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from ia_holographique_unifiee import IAHarmoniqueUnifiee

# ==============================================================================
# GÉNÉRATION DE CORPUS MASSIF
# ==============================================================================
BASES_PHYSIQUE = [
    "la constante de Planck h vaut {:.6e} J.s",
    "la vitesse de la lumiere c est {:.0f} m/s",
    "la constante gravitationnelle G vaut {:.5e}",
    "la constante de structure fine alpha vaut 1/{:.3f}",
    "le magneton de Bohr vaut {:.3e} J/T",
    "la masse de l'electron est {:.3e} kg",
    "la masse du proton est {:.3e} kg",
    "le rayon de Bohr est {:.3e} m",
    "la longueur de Planck est {:.3e} m",
    "la masse de Planck est {:.3e} kg",
    "le temps de Planck est {:.3e} s",
    "la temperature de Planck est {:.3e} K",
    "la constante de Boltzmann vaut {:.3e} J/K",
    "le nombre d'Avogadro est {:.3e} par mole",
    "la charge elementaire e vaut {:.3e} C",
    "la permittivite du vide epsilon0 vaut {:.3e} F/m",
    "la permeabilite du vide mu0 vaut {:.3e} N/A2",
    "l'impedance du vide Z0 vaut {:.2f} ohms",
    "la constante de Rydberg vaut {:.3e} par metre",
    "l'energie de Hartree vaut {:.3e} J",
]

BASES_MATHS = [
    "le nombre d'or phi est egal a {:.6f}",
    "pi est approximativement {:.6f}",
    "le nombre e vaut {:.6f}",
    "la racine carree de 2 est {:.6f}",
    "la racine carree de 3 est {:.6f}",
    "la racine carree de 5 est {:.6f}",
    "la constante d'Euler-Mascheroni gamma vaut {:.6f}",
    "le rapport circonference/diametre est pi soit {:.6f}",
    "phi au carre vaut {:.6f}",
    "pi au carre vaut {:.6f}",
]

BASES_IA = [
    "la theorie harmonique utilise l'equation Psi = somme Hn fois f puissance n",
    "les coefficients spectraux Hn sont phi pi e sqrt2 sqrt3 sqrt5 et e/pi",
    "l'onde fondamentale Psi1 vaut 7.83 Hz pour la Terre",
    "le principe holographique NPSU vaut 4R2 divise par lP2",
    "la compression harmonique projette sur les 7 constantes fondamentales",
    "l'hologramme de connaissance stocke l'information par interference d'ondes",
    "la robustesse holographique preserve l'information meme a 90% de destruction",
    "le filtre anti-hallucination verifie la coherence harmonique des predictions",
    "la generation d'images utilise la superposition des 7 harmoniques spatiales",
    "le quantificateur Lloyd-Max optimise les niveaux de quantification non-uniforme",
]


def generer_corpus_massif(n: int) -> list:
    """Génère un corpus de n connaissances synthétiques uniques."""
    corpus = set()
    seed = 42
    
    templates = BASES_PHYSIQUE + BASES_MATHS + BASES_IA
    valeurs = [1.054571817e-34, 2.99792458e8, 6.67430e-11, 137.036, 9.274009994e-24,
               9.1093837015e-31, 1.67262192369e-27, 5.29177210903e-11,
               1.616255e-35, 2.176434e-8, 5.391247e-44, 1.416784e32,
               1.380649e-23, 6.02214076e23, 1.602176634e-19,
               8.8541878128e-12, 1.25663706212e-6, 376.73, 1.0973731568160e7, 4.3597447222071e-18,
               1.618034, 3.141593, 2.718282, 1.414214, 1.732051, 2.236068, 0.577216]
    
    i = 0
    while len(corpus) < n:
        tmpl = templates[i % len(templates)]
        val = valeurs[i % len(valeurs)]
        # Variation pour unicité
        texte = tmpl.format(val * (1 + 0.001 * (i // len(templates))))
        corpus.add(texte)
        i += 1
        if i > n * 10:  # Sécurité
            break
    
    return list(corpus)[:n]


# ==============================================================================
# BENCHMARK
# ==============================================================================
def benchmark_echelle_large():
    print("=" * 80)
    print("BENCHMARK GRANDE ÉCHELLE — IA Harmono-Holographique")
    print("Test à 5000, 10000, 20000 connaissances")
    print("=" * 80)
    print()
    
    ia = IAHarmoniqueUnifiee(taille_hologramme=128)  # Taille augmentée pour plus de capacité
    print(f"  IA créée : hologramme 128×128×7 = {128**2*7:,} cellules")
    print(f"  Mémoire        : {128**2*7*16:,} octets ({128**2*7*16/1024/1024:.1f} Mo)")
    print()
    
    tailles_test = [1000, 2000, 5000, 10000, 20000]
    corpus = generer_corpus_massif(max(tailles_test))
    print(f"  Corpus maximal généré : {len(corpus)} connaissances")
    print()
    
    # Injection progressive
    print("  Injection progressive :")
    print(f"  {'Connaissances':>15s}  {'Temps (s)':>10s}  {'Énergie':>12s}  {'Saturation':>11s}  {'Vocabulaire':>12s}  {'µs/conn.':>10s}")
    print(f"  {'-'*15}  {'-'*10}  {'-'*12}  {'-'*11}  {'-'*12}  {'-'*10}")
    
    dernier_lot = 0
    for n_total in tailles_test:
        if n_total > len(corpus):
            break
        
        debut = time.time()
        for i in range(dernier_lot, n_total):
            ia.apprendre(corpus[i])
        duree = time.time() - debut
        
        n_ajoutes = n_total - dernier_lot
        us_par_conn = (duree / n_ajoutes) * 1e6 if n_ajoutes > 0 else 0
        
        etat = ia.hologramme.hologramme
        energie = float(np.sum(np.abs(etat)**2))
        saturation = float(np.max(np.abs(etat)))
        
        print(f"  {n_total:15d}  {duree:>9.3f}s  {energie:>12.2e}  {saturation:>11.4f}  {len(ia.vocabulaire):>12d}  {us_par_conn:>9.1f}")
        dernier_lot = n_total
    
    n_final = dernier_lot
    print()
    
    # Test de précision à grande échelle
    print(f"  Test de précision sur {n_final} connaissances :")
    print()
    
    requetes_test = [
        ("constante de Planck valeur", 0),
        ("equation harmonique fondamentale", 0),
        ("principe holographique NPSU", 0),
        ("nombre d'or phi valeur exacte", 0),
        ("filtre anti hallucination coherence", 0),
        ("compression projection spectrale", 0),
        ("racine carree de 5 valeur", 0),
        ("temperature de Planck", 0),
        ("generation images harmoniques", 0),
        ("coefficients spectraux liste", 0),
    ]
    
    top1_correct = 0
    top3_correct = 0
    
    for requete, _ in requetes_test:
        resultat = ia.predire(requete)
        holographiques = [p for p in resultat['predictions'] if p['type'] == 'holographique']
        
        if holographiques:
            best = holographiques[0]
            texte = best['texte'][:70] if best['texte'] else "(vide)"
            score = best['score']
            print(f"  Q: \"{requete}\"")
            print(f"  R: [{best['id']}] {texte}")
            print(f"     score={score:.4f}")
            if len(holographiques) > 1:
                autres = [f"{p['id']}({p['score']:.2f})" for p in holographiques[1:4]]
                print(f"     aussi: {', '.join(autres)}")
            print()
    
    # Test de robustesse à grande échelle
    print(f"  Test de robustesse holographique ({n_final} connaissances) :")
    print()
    
    requete_test = "constante de Planck"
    for fraction in [0.1, 0.3, 0.5, 0.7, 0.9]:
        if hasattr(ia.hologramme, 'test_robustesse'):
            # Pas de test_robustesse dans V2, on le fait manuellement
            orig = ia.hologramme.hologramme.copy()
            
            scores_avant = ia.hologramme.requete(requete_test, top_k=3)
            
            masque = np.random.random(ia.hologramme.hologramme.shape) > fraction
            ia.hologramme.hologramme *= masque
            
            scores_apres = ia.hologramme.requete(requete_test, top_k=3)
            
            ia.hologramme.hologramme = orig
            
            if scores_avant and scores_apres:
                degradation = (scores_avant[0][1] - scores_apres[0][1]) / max(scores_avant[0][1], 1e-10) * 100
                same = scores_avant[0][0] == scores_apres[0][0]
                status = "✅" if same else "❌"
                print(f"    Destruction {fraction*100:3.0f}% : "
                      f"score {scores_avant[0][1]:.4f} → {scores_apres[0][1]:.4f} "
                      f"({degradation:5.1f}% dégradation) "
                      f"top-1: {status}")
    
    print()
    print("=" * 80)
    print("TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    benchmark_echelle_large()