#!/usr/bin/env python3
r"""
INGESTION MASSIVE — Corpus mathématique pour raisonnement multi-sauts
=======================================================================
Génère un corpus structuré de relations mathématiques pour le PPMI.

Types de relations :
  - Arithmétique : "3 + 4 = 7", "7 est la somme de 3 et 4"
  - Carrés/Racines : "9 est le carre de 3", "3 est la racine de 9"
  - Pythagore : "5 est l'hypotenuse du triangle 3-4"
  - Algèbre : "4 est la solution de x + 3 = 7"
  - Géométrie : "le triangle 3-4-5 est rectangle"

Volume cible : ~10 000 - 50 000 phrases pour un PPMI riche.

Usage :
  python ingestion_corpus_mathematique.py
  → génère corpus_mathematique.json
"""

import json, math, os, time

PHI = (1 + math.sqrt(5)) / 2

def generer_corpus_mathematique(n_max=100):
    """
    Génère un corpus massif de relations mathématiques.
    
    Pour chaque nombre et paire de nombres, génère TOUTES les
    formulations textuelles possibles de leurs relations.
    """
    corpus = []
    
    for a in range(0, n_max + 1):
        # ═══════════════════════════════════════════════════════════════
        # Relations unaires (carrés, racines, identités)
        # ═══════════════════════════════════════════════════════════════
        carre = a * a
        
        corpus.append(f"{carre} est le carre de {a}")
        corpus.append(f"le carre de {a} est {carre}")
        corpus.append(f"{a} au carre donne {carre}")
        corpus.append(f"{a}² = {carre}")
        corpus.append(f"{a} multiplie par lui-meme donne {carre}")
        
        corpus.append(f"{a} est la racine carree de {carre}")
        corpus.append(f"la racine de {carre} est {a}")
        corpus.append(f"√({carre}) = {a}")
        corpus.append(f"le nombre dont le carre est {carre} est {a}")
        
        # Identités remarquables
        if a > 0:
            corpus.append(f"{a} plus 0 egale {a}")
            corpus.append(f"{a} fois 1 egale {a}")
            corpus.append(f"{a} est egal a lui-meme")
        
        for b in range(0, n_max + 1):
            # ═══════════════════════════════════════════════════════════
            # Addition
            # ═══════════════════════════════════════════════════════════
            somme = a + b
            corpus.append(f"{a} plus {b} egale {somme}")
            corpus.append(f"{a} + {b} = {somme}")
            corpus.append(f"la somme de {a} et {b} est {somme}")
            corpus.append(f"{somme} est la somme de {a} et {b}")
            corpus.append(f"si on ajoute {b} a {a}, on obtient {somme}")
            corpus.append(f"{a} augmente de {b} donne {somme}")
            
            # ═══════════════════════════════════════════════════════════
            # Soustraction
            # ═══════════════════════════════════════════════════════════
            if a >= b:
                diff = a - b
                corpus.append(f"{a} moins {b} egale {diff}")
                corpus.append(f"{a} - {b} = {diff}")
                corpus.append(f"la difference entre {a} et {b} est {diff}")
                corpus.append(f"{diff} est la difference de {a} et {b}")
                corpus.append(f"si on retire {b} de {a}, il reste {diff}")
            
            # ═══════════════════════════════════════════════════════════
            # Multiplication (limitée pour éviter explosion)
            # ═══════════════════════════════════════════════════════════
            if a <= 30 and b <= 30:
                prod = a * b
                corpus.append(f"{a} fois {b} egale {prod}")
                corpus.append(f"{a} x {b} = {prod}")
                corpus.append(f"le produit de {a} et {b} est {prod}")
                corpus.append(f"{prod} est le produit de {a} par {b}")
                corpus.append(f"{a} multiplie par {b} donne {prod}")
            
            # ═══════════════════════════════════════════════════════════
            # Division (résultats entiers)
            # ═══════════════════════════════════════════════════════════
            if b > 0 and a % b == 0 and b <= 30:
                div = a // b
                corpus.append(f"{a} divise par {b} egale {div}")
                corpus.append(f"{a} / {b} = {div}")
                corpus.append(f"le quotient de {a} par {b} est {div}")
                corpus.append(f"{div} est le resultat de {a} divise par {b}")
    
    # ═══════════════════════════════════════════════════════════════════
    # Triplets pythagoriciens
    # ═══════════════════════════════════════════════════════════════════
    triplets = [
        (3, 4, 5), (5, 12, 13), (6, 8, 10), (7, 24, 25),
        (8, 15, 17), (9, 12, 15), (9, 40, 41), (10, 24, 26),
        (11, 60, 61), (12, 16, 20), (12, 35, 37), (13, 84, 85),
        (14, 48, 50), (15, 20, 25), (15, 36, 39), (16, 30, 34),
        (16, 63, 65), (18, 24, 30), (18, 80, 82), (20, 21, 29),
        (20, 48, 52), (21, 28, 35), (21, 72, 75), (24, 32, 40),
        (24, 45, 51), (24, 70, 74), (25, 60, 65), (27, 36, 45),
        (28, 45, 53), (30, 40, 50), (30, 72, 78), (32, 60, 68),
        (33, 44, 55), (33, 56, 65), (35, 84, 91), (36, 48, 60),
        (36, 77, 85), (39, 52, 65), (39, 80, 89), (40, 42, 58),
        (40, 75, 85), (42, 56, 70), (45, 60, 75), (48, 55, 73),
        (48, 64, 80), (51, 68, 85), (54, 72, 90), (57, 76, 95),
        (60, 63, 87), (65, 72, 97),
    ]
    
    for a, b, c in triplets:
        if a <= n_max and b <= n_max and c <= n_max * 2:
            corpus.append(f"{c} est l'hypotenuse du triangle rectangle {a}-{b}")
            corpus.append(f"le triangle {a}-{b}-{c} est rectangle")
            corpus.append(f"{a}² + {b}² = {c}²")
            corpus.append(f"le triplet {a} {b} {c} est pythagoricien")
            corpus.append(f"dans le triangle {a}-{b}-{c}, l'hypotenuse mesure {c}")
            corpus.append(f"si un triangle a des cotes {a} et {b}, l'hypotenuse est {c}")
            corpus.append(f"le carre de {a} plus le carre de {b} egale le carre de {c}")
    
    # ═══════════════════════════════════════════════════════════════════
    # Relations algébriques (équations)
    # ═══════════════════════════════════════════════════════════════════
    for x in range(1, 31):
        for b in range(1, 11):
            c = x + b
            corpus.append(f"{x} est la solution de l'equation x + {b} = {c}")
            corpus.append(f"si x + {b} = {c}, alors x = {x}")
            corpus.append(f"l'equation x + {b} = {c} a pour solution {x}")
        
        for b in range(1, 11):
            c = x * b
            if c <= n_max * 3:
                corpus.append(f"l'equation {b} * x = {c} a pour solution {x}")
                corpus.append(f"si {b} x = {c}, alors x = {x}")
    
    # ═══════════════════════════════════════════════════════════════════
    # Propriétés des nombres
    # ═══════════════════════════════════════════════════════════════════
    proprietes = [
        "0 est l'element neutre de l'addition",
        "1 est l'element neutre de la multiplication",
        "2 est le plus petit nombre premier",
        "3 est le premier nombre premier impair",
        "l'addition est commutative",
        "la multiplication est commutative",
        "la soustraction n'est pas commutative",
        "la division n'est pas commutative",
    ]
    corpus.extend(proprietes)
    
    return corpus


def tokeniser_et_sauver(corpus, output_file="corpus_mathematique.json"):
    """Tokenise le corpus et sauvegarde."""
    tokenized = []
    for phrase in corpus:
        # Tokenisation simple : split par espaces, nettoyage basique
        tokens = []
        for mot in phrase.lower().split():
            mot = mot.strip('.,;:!?()[]{}"\'- ')
            if len(mot) > 1:
                tokens.append(mot)
        if tokens:
            tokenized.append(tokens)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tokenized, f, ensure_ascii=False)
    
    return tokenized


if __name__ == "__main__":
    print("=" * 74)
    print("  INGESTION MASSIVE — Corpus Mathématique")
    print("=" * 74)
    
    N_MAX = 100  # Générer pour a,b ∈ [0, 100]
    
    t0 = time.time()
    corpus = generer_corpus_mathematique(N_MAX)
    t1 = time.time()
    
    print(f"\n  Plage : [0, {N_MAX}]")
    print(f"  Phrases générées : {len(corpus)}")
    print(f"  Temps : {(t1-t0)*1000:.0f} ms")
    
    # Statistiques
    nb_mots = sum(len(p.split()) for p in corpus)
    print(f"  Mots totaux : {nb_mots}")
    print(f"  Mots/phrase : {nb_mots/len(corpus):.1f}")
    
    # Sauvegarde
    tokenized = tokeniser_et_sauver(corpus)
    print(f"\n  Sauvegardé : corpus_mathematique.json")
    print(f"  Phrases tokenisées : {len(tokenized)}")
    
    # Aperçu
    print(f"\n  Aperçu (10 premières phrases) :")
    for i, p in enumerate(corpus[:10]):
        print(f"    [{i}] {p[:80]}")
    
    print(f"\n  Aperçu (relations pythagoriciennes) :")
    for p in corpus:
        if "hypotenuse" in p and "3-4" in p:
            print(f"    {p[:80]}")
    
    print(f"\n  Aperçu (relations algébriques) :")
    for p in corpus:
        if "solution de l'equation" in p and "x + 3 = 7" in p:
            print(f"    {p[:80]}")
            break
    
    print(f"\n  Prêt pour PPMI + Laplacian Eigenmaps.")
    print(f"  Lancer : python ppmi_laplacian_encoder.py avec ce corpus.")