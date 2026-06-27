#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark LSH 100K — Hologramme V4
====================================
Test rapide de l'index LSH O(1) avec 100 000 connaissances.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, cmath, time, sys, os
from typing import Dict, List, Tuple
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from hologramme_connaissance_v4 import (HologrammeConnaissanceV4, H_complex,
                                         H, H_sum, H_names, phi, pi, e,
                                         generer_corpus_1M)

def benchmark_100k():
    print("=" * 80)
    print("BENCHMARK LSH 100K — Hologramme V4 O(1)")
    print("=" * 80)
    print()
    
    # Hologramme 128×128 pour rapidité
    print("Création hologramme 128×128×7 + LSH (14 hyperplans × 3 tables)...")
    debut_total = time.time()
    holo = HologrammeConnaissanceV4(taille=128, n_hyperplans_lsh=14)
    print(f"  {128**2*7:,} cellules, {2**14:,} buckets/table, 3 tables")
    print()
    
    # Corpus 100K
    print("Génération corpus 100K...")
    corpus = generer_corpus_1M(100_000)
    print(f"  {len(corpus):,} connaissances")
    print()
    
    # Injection par lots
    print("Injection progressive :")
    print(f"  {'Connaissances':>15s}  {'Temps (s)':>10s}  {'Energie':>12s}  {'Saturation':>11s}  {'µs/conn':>10s}")
    print(f"  {'-'*15}  {'-'*10}  {'-'*12}  {'-'*11}  {'-'*10}")
    
    lots = [10_000, 25_000, 50_000, 75_000, 100_000]
    dernier = 0
    
    for n_total in lots:
        debut_lot = time.time()
        for i in range(dernier, n_total):
            holo.encoder(corpus[i])
        duree = time.time() - debut_lot
        
        n_ajoutes = n_total - dernier
        us = (duree / n_ajoutes) * 1e6
        
        energie = float(np.sum(np.abs(holo.hologramme)**2))
        saturation = float(np.max(np.abs(holo.hologramme)))
        
        print(f"  {n_total:>15,d}  {duree:>9.1f}s  {energie:>12.2e}  {saturation:>11.2f}  {us:>9.1f}")
        dernier = n_total
    
    duree_totale = time.time() - debut_total
    print()
    print(f"  Temps total : {duree_totale:.1f}s")
    print(f"  Injectées    : {holo.n_connaissances:,}")
    print()
    
    # Stats LSH
    stats = holo.stats()
    print("  Statistiques LSH :")
    for t_name, t_stats in stats['lsh'].items():
        print(f"    {t_name} : {t_stats['n_buckets']:,} buckets, "
              f"moy={t_stats['taille_moyenne']:.1f}, "
              f"max={t_stats['taille_max']:,}, "
              f"remplissage={t_stats['taux_remplissage']*100:.1f}%")
    print()
    
    # Tests de requête
    print("  Tests de requête :")
    print()
    
    requetes = [
        "constante physique 42",
        "parametre mathematique 500",
        "concept harmonique 1000",
        "propriete holographique 5000",
        "coefficient spectral 9999",
        "fait scientifique 77777",
        "information numero 12345",
    ]
    
    for req in requetes:
        debut = time.time()
        resultats = holo.requete(req, top_k=3)
        duree = (time.time() - debut) * 1000
        
        if resultats:
            best = resultats[0]
            print(f"  \"{req}\"")
            print(f"    → [{best[0]}] {best[2][:65]} (score={best[1]:.3f}, {duree:.2f}ms)")
        else:
            print(f"  \"{req}\" → aucun résultat ({duree:.2f}ms)")
    print()
    
    print("=" * 80)
    print("TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    benchmark_100k()