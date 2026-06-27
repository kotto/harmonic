#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IA Harmono-Holographique Réelle
================================
Charge les hologrammes préexistants (data/holograms/) et les indexe
avec LSH O(1) pour des requêtes sur des connaissances réelles.

Sources :
- data/holograms/hologram64_*.npy (12 hologrammes 64×64)
- data/holograms/hologram64_*_data.json (textes associés)

Intégration :
1. Charge chaque hologramme (64×64)
2. Extrait les textes du JSON
3. Encode dans l'IA unifiée avec LSH
4. Permet des requêtes naturelles sur Wikipedia, science, etc.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, cmath, time, sys, os, json, glob
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from ia_holographique_unifiee import IAHarmoniqueUnifiee

# ==============================================================================
# CHARGEUR D'HOLOGRAMMES PRÉEXISTANTS
# ==============================================================================

def charger_hologrammes_existants(dossier: str = "data/holograms") -> list:
    """
    Charge tous les hologrammes 64×64 et leurs textes associés.
    
    Returns:
        Liste de (matrice_holographique, liste_de_textes, nom_domaine)
    """
    hologrammes = []
    
    pattern_npy = os.path.join(dossier, "hologram64_*.npy")
    for fichier_npy in sorted(glob.glob(pattern_npy)):
        # Nom du domaine (ex: "science" depuis "hologram64_science.npy")
        base = os.path.basename(fichier_npy)
        domaine = base.replace("hologram64_", "").replace(".npy", "")
        
        # Fichier JSON associé
        fichier_json = fichier_npy.replace(".npy", "_data.json")
        
        # Charger la matrice
        matrice = np.load(fichier_npy)  # (64, 64) ou (64, 64, 7)
        
        # Charger les textes
        textes = []
        if os.path.exists(fichier_json):
            with open(fichier_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'texts' in data:
                    textes = data['texts']
                elif isinstance(data, list):
                    textes = data
                elif isinstance(data, dict):
                    # Chercher la première clé qui contient une liste de strings
                    for key, val in data.items():
                        if isinstance(val, list) and len(val) > 0 and isinstance(val[0], str):
                            textes = val
                            break
        else:
            # Pas de JSON : utiliser le domaine comme texte par défaut
            textes = [f"Connaissance du domaine {domaine}"]
        
        hologrammes.append({
            'domaine': domaine,
            'matrice': matrice,
            'textes': textes,
            'n_textes': len(textes),
        })
    
    return hologrammes


def injecter_dans_ia(ia: IAHarmoniqueUnifiee, hologrammes: list, max_par_domaine: int = 1000):
    """
    Injecte les connaissances des hologrammes existants dans l'IA.
    
    Args:
        ia: instance de IAHarmoniqueUnifiee
        hologrammes: liste retournée par charger_hologrammes_existants()
        max_par_domaine: nombre max de textes à injecter par domaine
    """
    total_injecte = 0
    
    for holo in hologrammes:
        textes = holo['textes'][:max_par_domaine]
        for texte in textes:
            if texte and len(texte.strip()) > 10:  # Ignorer les textes trop courts
                ia.apprendre(texte.strip())
                total_injecte += 1
    
    return total_injecte


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================

def demo_ia_reelle():
    print("=" * 70)
    print("IA HARMONO-HOLOGRAPHIQUE RÉELLE")
    print("Hologrammes préexistants + LSH O(1)")
    print("=" * 70)
    print()
    
    # 1. Charger les hologrammes existants
    print("Chargement des hologrammes existants...")
    hologrammes = charger_hologrammes_existants("data/holograms")
    
    if not hologrammes:
        print("  Aucun hologramme trouvé dans data/holograms/")
        print("  Utilisation du corpus synthétique par défaut...")
        ia = IAHarmoniqueUnifiee(taille_hologramme=128)
        corpus_test = [
            "la constante de Planck h vaut 6.626e-34 J.s",
            "la vitesse de la lumiere est 299792458 m/s",
            "le nombre d'or phi est egal a 1.618034",
            "la resonance de Schumann est a 7.83 Hz",
            "le principe holographique encode l'information 3D en 2D",
        ]
        ia.apprendre_corpus(corpus_test)
        print(f"  Corpus synthétique : {len(corpus_test)} connaissances")
    else:
        print(f"  {len(hologrammes)} hologrammes trouvés :")
        for h in hologrammes:
            print(f"    - {h['domaine']:<20s} : {h['n_textes']} textes, "
                  f"matrice {h['matrice'].shape}")
        print()
        
        # 2. Créer l'IA et injecter les connaissances
        print("Création de l'IA unifiée (hologramme 128×128×7 + LSH)...")
        ia = IAHarmoniqueUnifiee(taille_hologramme=128)
        
        print("Injection des connaissances réelles...")
        n = injecter_dans_ia(ia, hologrammes, max_par_domaine=500)
        print(f"  {n} connaissances injectées dans l'hologramme")
        print(f"  Vocabulaire : {len(ia.vocabulaire)} mots")
        print()
    
    # 3. Test de requêtes
    print("Test de requêtes :")
    print()
    
    requetes = [
        "quelle est la constante de Planck",
        "qui a decouvert la relativite",
        "qu'est-ce que le principe holographique",
        "quelle est la vitesse de la lumiere",
        "qu'est-ce que la resonance de Schumann",
        "comment fonctionne la photosynthese",
        "quelle est la masse de l'electron",
        "qu'est-ce que le Big Bang",
        "qui est Einstein",
        "quelle est la constante gravitationnelle",
    ]
    
    for req in requetes:
        reponse = ia.repondre(req)
        print(f"  Q: \"{req}\"")
        print(f"  R: {reponse[:120]}")
        print()
    
    print("=" * 70)
    print("TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    demo_ia_reelle()