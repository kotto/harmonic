#!/usr/bin/env python3
"""
Script pour corriger les caractères Unicode dans les noms de test
"""

import json

def fix_test_names():
    """Corrige les caractères Unicode dans les noms de test"""
    
    # Lire le fichier
    with open("test_harmonic_audio_api.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remplacer les caractères Unicode problématiques dans les noms de test
    replacements = {
        "→": "->",
        "–": "-",
        "—": "-",
        "…": "...",
        "“": "\"",
        "”": "\"",
        "‘": "'",
        "’": "'"
    }
    
    # Appliquer les remplacements
    for unicode_char, ascii_char in replacements.items():
        content = content.replace(unicode_char, ascii_char)
    
    # Écrire le fichier corrigé
    with open("test_harmonic_audio_api.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("Noms de test corrigés avec succès")

if __name__ == "__main__":
    fix_test_names()