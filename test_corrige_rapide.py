#!/usr/bin/env python3
"""Test rapide de l'IA corrigée — sous-ensemble de 15K connaissances."""
import math, cmath, time, sys, os, json, glob, numpy as np
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from ia_holographique_corrigee import (IAHarmoniqueCorrigee, H, H_complex, H_sum,
                                        H_names, phi, pi, e)

def charger_rapide(ia, dossier="data/holograms", max_total=15000):
    """Charge un sous-ensemble équilibré de connaissances."""
    total = 0
    domaines_prioritaires = ["science", "general", "history", "geography", "philosophy"]
    
    for fichier_npy in sorted(glob.glob(os.path.join(dossier, "hologram64_*.npy"))):
        if total >= max_total:
            break
        base = os.path.basename(fichier_npy)
        domaine = base.replace("hologram64_","").replace(".npy","")
        fichier_json = fichier_npy.replace(".npy","_data.json")
        
        textes = []
        if os.path.exists(fichier_json):
            with open(fichier_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'texts' in data:
                    textes = data['texts']
                elif isinstance(data, list):
                    textes = data
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list) and len(v)>0 and isinstance(v[0], str):
                            textes = v; break
        
        # Limiter par domaine
        max_domaine = 5000 if domaine in domaines_prioritaires else 500
        textes = textes[:max_domaine]
        
        n_avant = ia.hologramme.n_connaissances
        for texte in textes:
            if texte and len(texte.strip()) > 10:
                ia.apprendre(texte.strip(), domaine)
                total += 1
                if total >= max_total:
                    break
        
        n_injecte = ia.hologramme.n_connaissances - n_avant
        print(f"    {domaine:<20s} : {n_injecte} connaissances")
    
    return total

print("="*70)
print("TEST RAPIDE — IA Corrigée (TF-IDF + Cosinus 7D)")
print("Sous-ensemble 15K connaissances")
print("="*70)
print()

print("Chargement rapide...")
ia = IAHarmoniqueCorrigee(taille_hologramme=128)
n = charger_rapide(ia)
ia.finaliser()
print(f"  TOTAL : {n} connaissances, {len(ia.vocabulaire)} mots, IDF sur {len(ia.hologramme.idf)} mots")
print()

requetes = [
    "quelle est la constante de Planck",
    "qui a decouvert la relativite",
    "quelle est la vitesse de la lumiere",
    "quelle est la masse de l electron",
    "qu est ce que le Big Bang",
    "qui est Einstein",
    "quelle est la constante gravitationnelle",
    "comment fonctionne la photosynthese",
    "qu est ce que la resonance de Schumann",
    "qu est ce que le principe holographique",
]

print("Test de requêtes :")
print()
ok = 0
for req in requetes:
    debut = time.time()
    reponse = ia.repondre(req)
    duree = (time.time()-debut)*1000
    print(f"  Q: \"{req}\"")
    print(f"  R: {reponse[:130]}")
    print(f"     ({duree:.1f}ms)")
    
    # Évaluation heuristique
    bons_mots = {
        "Planck": ["planck", "6.626"],
        "relativite": ["einstein", "relativite"],
        "lumiere": ["lumiere", "299", "300"],
        "electron": ["electron", "9.109"],
        "Big Bang": ["big bang", "13.8"],
        "Einstein": ["einstein", "relativite", "physicien", "photoelectrique"],
        "gravitationnelle": ["gravitation", "6.674", "newton"],
        "photosynthese": ["photosynthese", "plante", "co2", "lumiere solaire"],
        "Schumann": ["schumann", "7.83"],
        "holographique": ["holographique", "hologramme", "surface"],
    }
    for cle, mots_attendus in bons_mots.items():
        if cle.lower() in req.lower():
            if any(m in reponse.lower() for m in mots_attendus):
                ok += 1
            break
    print()

print(f"  Score : {ok}/10")
print()
print("="*70)
print("TERMINÉ")
print("="*70)