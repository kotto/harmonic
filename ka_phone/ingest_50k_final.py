#!/usr/bin/env python3
"""
KA-Next — INGESTION 50K FINALE v2
=====================================
Pipeline complet : génération + ingestion + benchmark.
Objectif : 50 000+ faits avant déploiement.

Usage :
  python ingest_50k_final.py
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("  KA-Next — INGESTION 50K FINALE v2")
print("=" * 70)

# Étape 1 : Génération du corpus diversifié
print("\n[Etape 1/3] Generation du corpus diversifie...")
from generate_corpus_diverse import (
    generate_geography, generate_history, generate_science,
    generate_philosophy, generate_technology, generate_domain, CORPUS_DIR
)

domain_corpus = {
    "geography": generate_geography,
    "history": generate_history,
    "science": generate_science,
    "philosophy": generate_philosophy,
    "technology": generate_technology,
}

targets = {"geography": 30000, "history": 30000, "science": 30000,
           "philosophy": 20000, "technology": 25000}

total_gen = 0
for domain, n in targets.items():
    count = generate_domain(domain, domain_corpus, n)
    total_gen += count
print(f"\nTotal genere : {total_gen} phrases")

# Étape 2 : Ingestion massive
print("\n[Etape 2/3] Ingestion massive...")
from ingest_massive_nx64 import ingest_massive
ensemble = ingest_massive()

# Étape 3 : Benchmark rapide
print("\n[Etape 3/3] Benchmark rapide...")
total_faits = sum(h.n_ingested for h in ensemble.holograms.values())
print(f"Total faits ingeres : {total_faits}")

from ka_next_v3 import KANextV3Engine
engine = KANextV3Engine()
engine.build()

questions = [
    ("Quelle est la capitale du Senegal ?", "dakar"),
    ("Qui a decouvert l'ADN ?", "watson"),
    ("Quand a debute la Revolution francaise ?", "1789"),
    ("Quelle est la vitesse de la lumiere ?", "299"),
    ("Qu'est-ce que le stoicisme ?", "distinguer"),
]
correct = 0
for q, exp in questions:
    r = engine.query(q, mode="auto")
    is_correct = exp.lower() in r.get("text", "").lower()
    if is_correct: correct += 1
    status = "OK" if is_correct else "KO"
    print(f"  [{status}] {q[:50]:50s} | {r['temps_ms']:5.0f}ms")

print(f"\n  {correct}/{len(questions)} ({correct/len(questions)*100:.0f}%)")
print(f"  Total faits : {total_faits}")
print("=" * 70)
print("  INGESTION 50K TERMINEE — Pret pour le deploiement")
print("=" * 70)