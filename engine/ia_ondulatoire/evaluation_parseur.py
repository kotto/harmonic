# -*- coding: utf-8 -*-
"""
evaluation_parseur.py — LES DEUX TESTS DÉCISIFS (08/08/2026)
==============================================================
  TEST A — TRANSFERT : le parseur sur SVAMP (300 items anglais,
           distribution différente). Décide : méthode générique ou
           artefact taillé sur les 1260 échecs ?
  TEST B — ABLATION DE L'ATTENTION : trois variantes mesurées sur les 80
           étiquetés ET sur SVAMP :
             B0 : attention calculée mais non utilisée (état actuel)
             B1 : attention supprimée (aucun appel)
             B2 : attention UTILISÉE comme filtre — clauses à faible
                  poids (< seuil × max) exclues de l'exécution
           Répond : l'équivalent ondulatoire de QKV apporte-t-il quelque
           chose, ou est-il un ornement ?

Usage : python evaluation_parseur.py
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parseur_semantique as P   # noqa: E402

DOSSIER = os.path.dirname(os.path.abspath(__file__))


def construire_parseur():
    echecs = json.load(open(os.path.join(DOSSIER, "taxonomie_echecs.json"),
                            encoding="utf-8"))
    textes = [e["question"] for e in echecs]
    with open(os.path.join(DOSSIER, "..", "data", "benchmarks",
                           "gsm8k_test.jsonl"), encoding="utf-8") as f:
        for i, l in enumerate(f):
            if i >= 300:
                break
            textes.append(json.loads(l)["question"])
    emb = P.EmbeddingsContextuels()
    emb.construire(textes)
    return P.ParseurSemantique(emb), echecs


def mesurer(parseur, questions, attendus, seuil_attention=0.0):
    bons = faux = refus = 0
    for q, a in zip(questions, attendus):
        r = parseur.decomposer(q, seuil_attention=seuil_attention)
        c = r["courant"]
        if c is None:
            refus += 1
        elif abs(c - a) < 1e-6:
            bons += 1
        else:
            faux += 1
    n = len(questions)
    return {"bons": bons, "faux": faux, "refus": refus, "n": n,
            "bons_pct": bons / n * 100}


def ic_bootstrap(resultats, n_rep=5000, graine=3):
    """IC 95 % de la proportion de bons (bootstrap per-item)."""
    rng = np.random.default_rng(graine)
    n = len(resultats)
    dist = np.array([np.mean(resultats[rng.integers(0, n, n)])
                     for _ in range(n_rep)])
    return float(np.percentile(dist, 2.5)), float(np.percentile(dist, 97.5))


print("=" * 70)
print("ÉVALUATION DU PARSEUR — transfert SVAMP + ablation attention")
print("=" * 70)

parseur, echecs = construire_parseur()

# ── données des 80 étiquetés ───────────────────────────────────────────
etiq = json.load(open(os.path.join(DOSSIER, "taxonomie_etiquettes.json"),
                      encoding="utf-8"))
labels = {int(k) for k in etiq["labels"]}
ech80 = [e for e in echecs if e["idx"] in labels]
q80 = [e["question"] for e in ech80]
a80 = [e["attendu"] for e in ech80]
print(f"[données] 80 étiquetés : {len(ech80)} items")

# ── TEST B — ablation attention (sur les 80) ───────────────────────────
print("\n[TEST B] ABLATION DE L'ATTENTION (80 étiquetés)")
variantes = [
    ("B0 attention calculée, NON utilisée", 0.0, False),
    ("B1 attention supprimée (aucun appel)", 0.0, True),
    ("B2 attention UTILISÉE (filtre seuil=0.3)", 0.3, False),
    ("B2 attention UTILISÉE (filtre seuil=0.6)", 0.6, False),
]
for nom, seuil, sans_attention in variantes:
    if sans_attention:
        orig = P.attention
        P.attention = lambda emb, q, cls: (np.ones(len(cls)) if cls else np.ones(1),
                                           None)
    try:
        res = mesurer(parseur, q80, a80, seuil_attention=seuil)
    finally:
        if sans_attention:
            P.attention = orig
    lo, hi = ic_bootstrap(
        np.array([1 if abs((parseur.decomposer(q, seuil_attention=seuil)
                            ["courant"] or -1e30) - a) < 1e-6 else 0
                  for q, a in zip(q80, a80)]))
    print(f"  {nom:44s}: bons {res['bons']:2d} · faux {res['faux']:2d} · "
          f"refus {res['refus']:2d}  ({res['bons_pct']:.1f} %  IC95 "
          f"[{lo * 100:.1f}, {hi * 100:.1f}])")

# ── TEST A — transfert SVAMP ───────────────────────────────────────────
print("\n[TEST A] TRANSFERT SVAMP (300 items anglais, distribution différente)")
svamp = json.load(open(os.path.join(DOSSIER, "..", "data", "benchmarks",
                                    "SVAMP.json"), encoding="utf-8"))
rng = np.random.default_rng(42)
ech = list(rng.choice(len(svamp), size=300, replace=False))
qs = [svamp[i]["Body"] + " " + svamp[i]["Question"] for i in ech]
as_ = [float(svamp[i]["Answer"]) for i in ech]
res = mesurer(parseur, qs, as_)
print(f"  SVAMP : bons {res['bons']} · faux {res['faux']} · refus {res['refus']}"
      f"  ({res['bons_pct']:.1f} %)")
# SVAMP avec filtre attention
res2 = mesurer(parseur, qs, as_, seuil_attention=0.3)
print(f"  SVAMP + filtre attention 0.3 : bons {res2['bons']} · faux {res2['faux']}"
      f" · refus {res2['refus']}  ({res2['bons_pct']:.1f} %)")

print("\n" + "=" * 70)
print("LECTURE :")
print("  · B0 == B1 → l'attention est un ornement (non utilisée par l'exécution)")
print("  · B2 ≠ B0 → l'attention FILTRE change le comportement — mesurable")
print("  · SVAMP : si ≈ 0 % → la grammaire est un artefact in-sample ;")
print("    si > 10 % → généricité réelle à documenter")
print("=" * 70)
