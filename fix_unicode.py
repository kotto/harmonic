#!/usr/bin/env python3
"""
Script pour corriger les caractères Unicode dans les fichiers Python
"""

import os
import re

def fix_unicode_in_file(filepath):
    """Corrige les caractères Unicode dans un fichier"""
    print(f"Traitement de: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacement des caractères Unicode problématiques
    replacements = {
        '🚀': 'DEMARRAGE',
        '📄': 'DOCUMENT',
        '🎉': 'CELEBRATION',
        '📊': 'STATISTIQUES',
        '⚡': 'PERFORMANCES',
        '🔧': 'OUTIL',
        '🔑': 'CLE',
        '👤': 'UTILISATEUR',
        '✅': 'SUCCES',
        '⚠️': 'ATTENTION',
        '❌': 'ECHEC',
        '🔍': 'RECHERCHE',
        '🧪': 'TEST',
        '🎧': 'AUDIO',
        '🏆': 'TROPHEE',
        '📈': 'PROGRESSION',
        '📋': 'RAPPORT',
        '🤖': 'ROBOT',
        '⏱️': 'TEMPS',
        '📄': 'FICHIER'
    }
    
    # Appliquer les remplacements
    for unicode_char, replacement in replacements.items():
        content = content.replace(unicode_char, replacement)
    
    # Écrire le fichier corrigé
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  -> Fichier corrigé")

def main():
    """Fonction principale"""
    files_to_fix = [
        "harmonic_audio_service.py",
        "test_harmonic_audio_api.py"
    ]
    
    for filename in files_to_fix:
        if os.path.exists(filename):
            fix_unicode_in_file(filename)
        else:
            print(f"Fichier non trouvé: {filename}")

if __name__ == "__main__":
    main()