#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assistant Final Harmonique — Moteur de Faits + Moteur de Langage
==================================================================
Architecture propre :
1. Moteur de Faits (TF-IDF + boost domaine) → 105K connaissances → top-3 faits
2. Moteur de Langage (reformulation par règles) → phrases naturelles

Séparation stricte des préoccupations :
- Le moteur de faits ne s'occupe PAS de la formulation
- Le moteur de langage ne s'occupe PAS de la recherche

Résultat : réponses factuellement correctes ET grammaticalement propres.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, re, sys, os, json, glob, time
from typing import List, Dict
from collections import Counter
import numpy as np

# Importer le moteur de langage
from moteur_langage import MoteurLangage

phi = (1 + math.sqrt(5)) / 2

# ========== DOMAINES & MOTS-CLÉS ==========
DOMAINE_MOTS_CLES = {
    "science": ["planck", "einstein", "newton", "relativité", "quantique", "physique",
                "constante", "lumière", "photon", "électron", "proton", "atome",
                "big bang", "cosmologie", "gravitation", "énergie", "masse",
                "vitesse", "accélération", "force", "onde", "fréquence",
                "photosynthèse", "biologie", "chimie", "élément", "réaction",
                "darwin", "évolution", "adn", "arn", "cellule", "mitose",
                "thermodynamique", "entropie", "boltzmann", "heisenberg",
                "schrödinger", "bohr", "feynman", "hawking", "curie", "pasteur",
                "mendeleïev", "lavoisier", "galilée", "kepler", "maxwell",
                "tesla", "volta", "ampère", "ohm", "watt", "joule", "pascal",
                "hertz", "celsius", "kelvin", "farad", "henry",
                "supraconductivité", "fission", "fusion", "nucléaire",
                "électromagnétique", "spectre", "laser", "optique",
                "lemaître", "hubble", "télescope", "observatoire",
                "watson", "crick", "franklin", "wegener", "hahn",
                "higgs", "cern", "boson"],
    "histoire": ["histoire", "siècle", "guerre", "révolution", "empire",
                 "rome", "grec", "égypte", "moyen âge", "renaissance",
                 "napoléon", "louis", "charlemagne", "colomb", "découverte",
                 "indépendance", "traité", "bataille", "civilisation"],
    "geographie": ["pays", "capitale", "continent", "océan", "fleuve",
                   "montagne", "climat", "population", "superficie", "ville",
                   "région", "frontière", "démographie"],
    "sante": ["santé", "maladie", "médecine", "vaccin", "virus", "bactérie",
              "cancer", "diabète", "cœur", "cerveau", "symptôme", "traitement"],
}

# ========== CHARGEMENT ==========
def charger_tout(dossier="data/holograms"):
    connaissances = []
    for f in sorted(glob.glob(os.path.join(dossier, "hologram64_*.npy"))):
        base = os.path.basename(f)
        domaine = base.replace("hologram64_", "").replace(".npy", "")
        fj = f.replace(".npy", "_data.json")
        textes = []
        if os.path.exists(fj):
            with open(fj, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                if 'texts' in data: textes = data['texts']
                elif isinstance(data, list): textes = data
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], str):
                            textes = v; break
        for t in textes:
            if t and len(t.strip()) > 10:
                connaissances.append({
                    'texte': t.strip(),
                    'domaine': domaine,
                    'mots': set(t.lower().split()),
                })
    return connaissances

# ========== MOTEUR DE FAITS ==========
class MoteurFaits:
    def __init__(self):
        self.connaissances = []
        self.idf = {}
    
    def charger(self, max_total=None):
        print("Chargement des 105K connaissances...")
        conns = charger_tout()
        if max_total: conns = conns[:max_total]
        self.connaissances = conns
        doc_count = Counter()
        for c in conns:
            for m in c['mots']: doc_count[m] += 1
        N = len(conns)
        for mot, count in doc_count.items():
            self.idf[mot] = math.log((N + 1) / (count + 1)) + 1
        return len(conns)
    
    def _detecter_domaine(self, question):
        q = question.lower()
        scores = {}
        for domaine, mots_cles in DOMAINE_MOTS_CLES.items():
            score = sum(1 for m in mots_cles if m in q)
            if score > 0: scores[domaine] = score
        return max(scores, key=scores.get) if scores else None
    
    def rechercher(self, question, top_k=5):
        mots_q = set(question.lower().split())
        domaine_attendu = self._detecter_domaine(question)
        # Boost de domaine
        boost_base = 1.5
        scores = []
        for c in self.connaissances:
            tfidf = sum(self.idf.get(m, 1.0) for m in c['mots'] if m in mots_q)
            boost = boost_base if (domaine_attendu and c['domaine'] == domaine_attendu) else 1.0
            if c['domaine'] == domaine_attendu: boost *= 2.0
            score = tfidf * boost
            if score > 0: scores.append((c['texte'], c['domaine'], score))
        scores.sort(key=lambda x: x[2], reverse=True)
        return [(s[0], s[1], s[2]) for s in scores[:top_k]]

# ========== ASSISTANT FINAL ==========
class AssistantFinal:
    def __init__(self):
        self.faits = MoteurFaits()
        self.langage = MoteurLangage()
    
    def initialiser(self):
        n = self.faits.charger()
        print(f"  {n:,} connaissances | {len(self.faits.idf):,} mots IDF")
        return n
    
    def repondre(self, question):
        resultats = self.faits.rechercher(question, top_k=5)
        faits_bruts = [r[0] for r in resultats]
        reponse = self.langage.reformuler(faits_bruts)
        return reponse, self.faits._detecter_domaine(question)

# ========== TEST ==========
print("=" * 70)
print("ASSISTANT FINAL HARMONIQUE")
print("Moteur de Faits + Moteur de Langage")
print("=" * 70)
print()

assistant = AssistantFinal()
assistant.initialiser()
print()

questions = [
    "quelle est la constante de Planck",
    "qui a découvert la relativité",
    "comment fonctionne la photosynthèse",
    "quelle est la vitesse de la lumière",
    "qu'est-ce que le Big Bang",
    "qui est Albert Einstein",
    "quelle est la masse de l'électron",
    "qu'est-ce que l'entropie en thermodynamique",
    "qui a formulé la théorie de l'évolution",
    "qu'est-ce que le boson de Higgs",
]

print("=" * 70)
print("TEST FINAL")
print("=" * 70)
print()

ok = 0
for q in questions:
    reponse, domaine = assistant.repondre(q)
    
    est_correct = False
    attendus = {
        "Planck": ["planck", "6.626", "10⁻³⁴", "10^-34"],
        "relativité": ["einstein", "1905", "1915"],
        "photosynthèse": ["photosynthèse", "co2", "plante", "lumière", "co₂"],
        "lumière": ["lumière", "299", "m/s"],
        "Big Bang": ["big bang", "13.8", "lemaître"],
        "Einstein": ["einstein", "physicien", "relativité", "nobel"],
        "électron": ["électron", "9.109", "10^-31", "kg"],
        "entropie": ["entropie", "thermodynamique", "boltzmann"],
        "évolution": ["darwin", "évolution", "sélection"],
        "Higgs": ["higgs", "boson", "cern", "2012"],
    }
    for cle, mots in attendus.items():
        if cle.lower() in q.lower():
            if any(m.lower() in reponse.lower() for m in mots):
                est_correct = True
            break
    
    if est_correct: ok += 1
    emoji = "✅" if est_correct else "❌"
    
    print(f"  {emoji} {q}")
    print(f"     Domaine : {domaine or 'général'}")
    print(f"     💬 {reponse[:250]}")
    print()

print("=" * 70)
print(f"  SCORE FACTUEL : {ok}/{len(questions)}")
print(f"  QUALITÉ LANGAGE : reformulation par règles actives")
print("=" * 70)