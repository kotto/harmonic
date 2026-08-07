#!/usr/bin/env python
"""Construit le dictionnaire visuel à partir d'un corpus d'images."""
import sys, os, argparse
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from core.dictionary import HarmonicDatabase

def main():
    p = argparse.ArgumentParser(description='Build Visual Dictionary')
    p.add_argument('corpus', help='Répertoire contenant les images')
    p.add_argument('--output', '-o', default='data/dictionary', help='Répertoire de sortie')
    p.add_argument('--max', type=int, default=500, help='Max images par catégorie')
    args = p.parse_args()
    print(f'📚 Construction du dictionnaire depuis {args.corpus}...')
    db = HarmonicDatabase()
    db.ingest_directory(args.corpus, max_per_category=args.max)
    db.save(args.output)
    print(f'✓ Dictionnaire sauvegardé dans {args.output}/')

if __name__ == '__main__': main()
