#!/usr/bin/env python3
"""
EXTRACTION DU VOCABULAIRE DES INJECTIONS HOLOGRAPHIQUES.

Scanne les scripts d'injection pour extraire tous les mots uniques
avec leur frequence. Produit une liste triee utilisable pour
construire VOCABULAIRE_ETENDU.

Usage :
    python scripts/extraire_vocabulaire.py
"""
import re
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =========================================================================
# CONFIGURATION : fichiers a scanner
# =========================================================================

FICHIERS_INJECTION = [
    "injecter_histoire_afrique.py",
    "injecter_medecine_pubmed.py",
]

FICHIERS_ADDITIONNELS = [
    "ka_reasoning_engine.py",
    "ka_studio_ingest.py",
]

FONCTIONS_INJECTION = [
    'apprendre(',   # injecter_histoire_afrique
    'a(',           # injecter_medecine_pubmed
]


def extraire_chaines(fichier: str) -> list:
    """
    Extrait toutes les chaines de caracteres contenues dans
    les appels aux fonctions d'injection.
    
    Cherche les motifs : fonction("texte") ou fonction('texte')
    """
    with open(fichier, 'r', encoding='utf-8', errors='replace') as f:
        contenu = f.read()
    
    chaines = []
    
    # Regex pour trouver les chaines apres les noms de fonctions d'injection
    # Capture le contenu entre guillemets apres le nom de la fonction
    for nom_fonction in FONCTIONS_INJECTION:
        # Pattern: apprendre("...") ou a('...')
        pattern = re.escape(nom_fonction) + r'''
            \s*         # espaces eventuels
            ["']        # guillemet ouvrant
            (           # capture group
                (?:        # non-capture group
                    [^"']     # tout sauf guillemet
                    |         # OU
                    \\(?=["']) # echappement
                )*
            )
            ["']        # guillemet fermant
        '''
        matches = re.finditer(pattern, contenu, re.VERBOSE)
        for m in matches:
            chaine = m.group(1).strip()
            if len(chaine) > 10:  # Ignorer les chaines trop courtes
                chaines.append(chaine)
    
    return chaines


def nettoyer_mot(mot: str) -> str:
    """Nettoie un mot : lowercase, enleve ponctuation laterale, garde accents."""
    mot = mot.lower().strip()
    # Enlever la ponctuation au debut et a la fin
    mot = mot.strip('.,!?;:()[]{}"\'-_<>/\'«»')
    # Garder les mots avec accents, chiffres et tirets internes
    if len(mot) < 2:
        return ''
    if re.match(r'^[\d\s]+$', mot):
        return ''  # Que des chiffres
    return mot


def tokeniser_texte(texte: str) -> list:
    """Tokenise un texte en mots nettoyes."""
    mots = texte.split()
    return [nettoyer_mot(m) for m in mots if nettoyer_mot(m)]


def main():
    print("=" * 60)
    print("EXTRACTION DU VOCABULAIRE DES INJECTIONS HOLOGRAPHIQUES")
    print("=" * 60)
    
    tous_les_mots = Counter()
    
    # 1. Scanner les fichiers d'injection principaux
    print("\n--- Fichiers d'injection ---")
    for fichier in FICHIERS_INJECTION:
        chemin = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), fichier)
        if not os.path.exists(chemin):
            print(f"  [!] {fichier} introuvable")
            continue
        
        chaines = extraire_chaines(chemin)
        print(f"  [{'OK' if chaines else '??'}] {fichier}: {len(chaines)} textes extraits")
        
        for texte in chaines:
            mots = tokeniser_texte(texte)
            for mot in mots:
                if mot:
                    tous_les_mots[mot] += 1
    
    # 2. Scanner les fichiers additionnels (pour les mots generiques)
    print("\n--- Fichiers additionnels ---")
    for fichier in FICHIERS_ADDITIONNELS:
        chemin = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), fichier)
        if not os.path.exists(chemin):
            print(f"  [!] {fichier} introuvable")
            continue
        
        chaines = extraire_chaines(chemin)
        print(f"  [{'OK' if chaines else '??'}] {fichier}: {len(chaines)} textes extraits")
        
        for texte in chaines:
            mots = tokeniser_texte(texte)
            for mot in mots:
                if mot:
                    tous_les_mots[mot] += 1
    
    # 3. Statistiques
    print(f"\n{'='*60}")
    print(f"Mots uniques extraits : {len(tous_les_mots)}")
    print(f"Total occurrences     : {sum(tous_les_mots.values())}")
    print(f"{'='*60}")
    
    # 4. Afficher le top 80 par frequence
    print("\n--- Top 80 mots (par frequence) ---")
    for i, (mot, freq) in enumerate(tous_les_mots.most_common(80)):
        print(f"  {i+1:4d}. '{mot:30s}' freq={freq}")
    
    # 5. Sauvegarder au format Python
    output_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))),
        "harmonic_training", "model", "vocabulaire_extrait.py")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write('"""\n')
        f.write("VOCABULAIRE EXTRAIT DES INJECTIONS HOLOGRAPHIQUES.\n")
        f.write(f"Genere par scripts/extraire_vocabulaire.py\n")
        f.write(f"Total mots uniques : {len(tous_les_mots)}\n")
        f.write('"""\n\n')
        f.write("MOTS_PAR_FREQUENCE = [\n")
        for mot, freq in tous_les_mots.most_common():
            f.write(f"    ('{mot}', {freq}),\n")
        f.write("]\n\n")
        f.write(f"MOTS_UNIQUES = [m for m, f in MOTS_PAR_FREQUENCE]\n")
    
    print(f"\n  -> Sauvegarde : {output_path}")
    print(f"  -> {len(tous_les_mots)} mots uniques sauvegardes")
    print(f"\nPour construire VOCABULAIRE_ETENDU :")
    print(f"  from vocabulaire_extrait import MOTS_UNIQUES")
    print(f"  VOCABULAIRE_ETENDU = VOCABULAIRE_BASE + MOTS_UNIQUES")
    
    return tous_les_mots


if __name__ == '__main__':
    main()
