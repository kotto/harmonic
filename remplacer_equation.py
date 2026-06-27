#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remplacement massif : équation simplifiee Ψ = Σ Hₙ · fⁿ
dans tous les fichiers HTML de symphonie_cosmique.
"""

import os
import glob
import re

DIR = r"e:\SAAS - Copie\symphonie_cosmique"

# Liste des remplacements (ancien -> nouveau)
REPLS = [
    # Equation principale : Σ₁^∞ → Σ₁^{n(R)}
    (r'Σ<sub>n=1</sub><sup>∞</sup>', r'Σ<sub>n=1</sub><sup>n(R)</sup>'),
    # "somme infinie" -> "somme finie"
    (r'somme infinie', r'somme finie'),
    # "série infinie" -> "série finie"
    (r'série infinie', r'série finie'),
    # "à l'infini." -> "jusqu'à la borne holographique."
    (r'à l\'infini\.', r'jusqu\'à la borne holographique.'),
    # "et ainsi de suite à l'infini" -> version holographique
    (r'et ainsi de suite à l\'infini', r'et ainsi de suite jusqu\'à la borne holographique'),
    # "une infinité de" -> "des couches de"
    (r'une infinité de « couches » vibratoires', r'des « couches » vibratoires en nombre fini'),
    # "somme infinie de l'onde" -> version courte
    (r'somme infinie de l\'onde', r'somme finie de l\'onde'),
]

def traiter_fichier(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        for old, new in REPLS:
            if re.search(old, content):
                content = re.sub(old, new, content)
                modified = True
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Erreur sur {filepath}: {e}")
        return False

print("=" * 80)
print("REMPLACEMENT MASSIF — Équation simplifiée Ψ = Σ Hₙ · fⁿ")
print("=" * 80)
print()

count = 0
for filepath in glob.glob(os.path.join(DIR, "*.html")):
    if traiter_fichier(filepath):
        print(f"  ✓ {os.path.basename(filepath)}")
        count += 1

print()
print(f"{count} fichiers modifiés.")
print("Terminé.")