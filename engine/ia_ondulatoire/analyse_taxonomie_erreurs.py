# -*- coding: utf-8 -*-
"""
analyse_taxonomie_erreurs.py — TAXONOMIE DES 1260 ÉCHECS 0-LLM (P1.3bis)
=======================================================================
Hypothèse de l'utilisateur (08/08/2026) : « si nous ne décomposons pas
correctement le problème (traduction), tout le reste sera faux ».

Trois niveaux de classification :

  [AUTO — plein corpus] pour chaque échec :
    · AUCUN PLAN : pas d'étape arithmétique produite (décomposition nulle)
    · EXÉCUTION   : une étape « X op Y = Z » est FAUSSE localement
                    (Z ≠ X op Y calculé) — le moteur a mal calculé SA structure
    · PLAN FAUX   : toutes les étapes sont arithmétiquement correctes mais le
                    résultat final ≠ attendu — la STRUCTURE (nombres,
                    opérations) était fausse. Sous-classifié manuellement.

  [MANUEL — échantillon de 80] pour les « PLAN FAUX » :
    · EXTRACTION  : nombres/dimensions mal extraits (mauvais nombre, parasite,
                    mauvaise unité)
    · RELATION    : nombres bons mais opération/relation fausse
    · MIXTE       : les deux
    · EXÉCUTION   : structure bonne, erreur d'arithmétique (si le verdict auto
                    l'a ratée)

Usage : python analyse_taxonomie_erreurs.py --collecte
        python analyse_taxonomie_erreurs.py --echantillon   (80 à étiqueter)
        python analyse_taxonomie_erreurs.py --bilan         (après étiquetage)
"""

import argparse
import json
import os
import random
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsm8k import GSM8KOndulatoire       # noqa: E402

DOSSIER = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.join(DOSSIER, "..", "data", "benchmarks", "gsm8k_test.jsonl")
ECHECS = os.path.join(DOSSIER, "taxonomie_echecs.json")
ETIQUETTES = os.path.join(DOSSIER, "taxonomie_etiquettes.json")


def attendu_gsm8k(answer: str):
    m = re.search(r"####\s*(-?\d+(?:[.,]\d+)?)", answer or "")
    return float(m.group(1).replace(",", ".")) if m else None


def ok(valeur, a):
    return valeur is not None and a is not None and abs(valeur - a) < 1e-6


OP = {"+": lambda a, b: a + b, "−": lambda a, b: a - b,
      "×": lambda a, b: a * b, "÷": lambda a, b: a / b,
      "-": lambda a, b: a - b, "*": lambda a, b: a * b,
      "/": lambda a, b: a / b}

MOTS_OP = ("addition", "soustraction", "multiplication", "division")


def verifier_etapes(etapes):
    """(n_plan, n_arithm_fausses) — détecte les étapes de plan PARTOUT
    (pas seulement en début de chaîne) et vérifie « X op Y = Z » localement."""
    n, faux = 0, 0
    for e in etapes:
        if not any(m in e for m in MOTS_OP) and "=" not in e and not re.search(
                r"[+\-−×÷*/]", e):
            continue
        n += 1
        for m in re.finditer(r"(-?\d+(?:\.\d+)?)\s*([+\-−×÷*/])\s*"
                             r"(-?\d+(?:\.\d+)?)\s*=\s*(-?\d+(?:\.\d+)?)", e):
            x, op, y, z = float(m.group(1)), m.group(2), float(m.group(3)), float(m.group(4))
            try:
                if abs(OP[op](x, y) - z) > 1e-6:
                    faux += 1
            except ZeroDivisionError:
                faux += 1
    return n, faux


def collecte():
    s = GSM8KOndulatoire()
    echecs = []
    with open(TEST, encoding="utf-8") as f:
        for idx, ligne in enumerate(f):
            d = json.loads(ligne)
            a = attendu_gsm8k(d["answer"])
            r = s.resoudre(d["question"])
            if not ok(r["reponse_num"], a):
                n_et, n_faux = verifier_etapes(r.get("etapes") or [])
                if r["reponse_num"] is None or n_et == 0:
                    classe = "AUCUN_PLAN"
                elif n_faux > 0:
                    classe = "EXECUTION"
                else:
                    classe = "PLAN_FAUX"
                nums_q = re.findall(r"-?\d+(?:[.,]\d+)?", d["question"].replace(",", ""))
                echecs.append({
                    "idx": idx, "question": d["question"], "attendu": a,
                    "reponse": r["reponse_num"], "moteur": str(r.get("moteur")),
                    "etapes": r.get("etapes") or [],
                    "classe_auto": classe,
                    "nombres_question": [float(x) for x in nums_q],
                })
            if (idx + 1) % 300 == 0:
                print(f"  {idx + 1}/1319")
    with open(ECHECS, "w", encoding="utf-8") as f:
        json.dump(echecs, f, ensure_ascii=False)
    from collections import Counter
    print("\nClassification AUTO sur", len(echecs), "échecs :")
    for c, n in Counter(e["classe_auto"] for e in echecs).most_common():
        print(f"  {c:12s}: {n:5d}  ({n / len(echecs) * 100:.1f} %)")


def echantillon(n=80, graine=7):
    echecs = json.load(open(ECHECS, encoding="utf-8"))
    plans = [e for e in echecs if e["classe_auto"] == "PLAN_FAUX"]
    rng = random.Random(graine)
    sel = rng.sample(plans, min(n, len(plans)))
    print(f"Échantillon : {len(sel)} échecs PLAN_FAUX à étiqueter (E/R/M/X)")
    for i, e in enumerate(sel):
        print(f"\n[{i}] idx={e['idx']} attendu={e['attendu']} reponse={e['reponse']}")
        print(f"    Q: {e['question'][:220]}")
        print(f"    étapes: {' | '.join(e['etapes'][:6])[:200]}")
    with open(ETIQUETTES, "w", encoding="utf-8") as f:
        json.dump({"graine": graine, "items": [{"idx": e["idx"]} for e in sel]},
                  f, ensure_ascii=False, indent=1)


def bilan():
    ech = json.load(open(ECHECS, encoding="utf-8"))
    etiq = json.load(open(ETIQUETTES, encoding="utf-8"))
    from collections import Counter
    auto = Counter(e["classe_auto"] for e in ech)
    n = len(ech)
    print(f"Classification AUTO (n={n}) :")
    for c, k in auto.most_common():
        print(f"  {c:12s}: {k:5d}  ({k / n * 100:.1f} %)")
    # étiquettes manuelles
    labels = etiq.get("labels", {})
    if not labels:
        print("\nAucune étiquette manuelle — lancer --echantillon puis"
              " renseigner taxonomie_etiquettes.json → labels: {idx: 'E'|'R'|'M'|'X'}")
        return
    # report des classes manuelles sur tout le corpus (proportionnel)
    dist = Counter(labels.values())
    n_lab = len(labels)
    print(f"\nÉtiquetage manuel (n={n_lab}) :")
    for c in ("E", "R", "M", "X"):
        print(f"  {c:3s}: {dist.get(c, 0):3d}  ({dist.get(c, 0) / n_lab * 100:.1f} %)")
    # projection : part des PLAN_FAUX dans le total
    pf = auto["PLAN_FAUX"]
    print(f"\nProjection sur le corpus :")
    for c, k in dist.items():
        est = k / n_lab * pf
        print(f"  {c:3s} (dans PLAN_FAUX) : ~{est:.0f} échecs"
              f" ({est / n * 100:.1f} % du total)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="collecte",
                    choices=["collecte", "echantillon", "bilan"])
    args = ap.parse_args()
    if args.phase == "collecte":
        collecte()
    elif args.phase == "echantillon":
        echantillon()
    else:
        bilan()
