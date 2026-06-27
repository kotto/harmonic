#!/usr/bin/env python3
"""Quick debug des requêtes holographiques."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from ia_holographique_unifiee import IAHarmoniqueUnifiee

ia = IAHarmoniqueUnifiee(taille_hologramme=64)
corpus = ["la constante de Planck h vaut 6.626e-34 J.s",
          "le nombre d'or phi est egal a 1.618034",
          "le principe holographique encode l'information 3D en 2D"]

ia.apprendre_corpus(corpus)
print(f"Connaissances stockees: {ia.hologramme.n_connaissances}")
print(f"IDs stockes: {[c['id'] for c in ia.hologramme.connaissances_stockees]}")

# Test direct de la requete hologramme
resultats = ia.hologramme.requete("constante de Planck", top_k=3)
print(f"\nRequete hologramme directe: {resultats}")

# Test via predire
pred = ia.predire("constante de Planck")
print(f"\nPredire: {[(p['type'], p.get('texte','')) for p in pred['predictions'][:3]]}")