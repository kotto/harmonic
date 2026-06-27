#!/usr/bin/env python3
"""
Script pour corriger les caractères Unicode dans le fichier de comparaison
"""

import re

def fix_unicode_in_file(file_path):
    """Corriger les caractères Unicode dans un fichier"""
    
    # Définir les remplacements
    replacements = {
        # Émojis
        '✨': 'AVANTAGES',
        '⚡': 'BORDS COMPETITIFS',
        '🎯': 'POTENTIEL',
        '📋': 'RECOMMANDATIONS',
        '🔴': '[HAUTE]',
        '🟡': '[MOYENNE]',
        '🟢': '[BASSE]',
        '📊': 'RESUME',
        
        # Caractères accentués
        'é': 'e',
        'è': 'e',
        'ê': 'e',
        'ë': 'e',
        'à': 'a',
        'â': 'a',
        'ä': 'a',
        'î': 'i',
        'ï': 'i',
        'ô': 'o',
        'ö': 'o',
        'ù': 'u',
        'û': 'u',
        'ü': 'u',
        'ç': 'c',
        'É': 'E',
        'È': 'E',
        'Ê': 'E',
        'Ë': 'E',
        'À': 'A',
        'Â': 'A',
        'Ä': 'A',
        'Î': 'I',
        'Ï': 'I',
        'Ô': 'O',
        'Ö': 'O',
        'Ù': 'U',
        'Û': 'U',
        'Ü': 'U',
        'Ç': 'C',
    }
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Appliquer les remplacements
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Écrire le fichier corrigé
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fichier {file_path} corrige avec succes")
    return True

if __name__ == "__main__":
    file_path = "comparaison_modeles_recents.py"
    fix_unicode_in_file(file_path)