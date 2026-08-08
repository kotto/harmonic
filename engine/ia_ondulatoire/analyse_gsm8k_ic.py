# -*- coding: utf-8 -*-
"""
analyse_gsm8k_ic.py — P1.3 RE-MESURE HORS-ÉCHANTILLON AVEC INTERVALLE
=====================================================================
Ce que mesure ce script (pré-enregistré, PLAN_FAIBLESSES_IA_HARMONIQUE.md) :

  [1] IC bootstrap du chiffre publié 85,52 % (révision LLM TOUS) :
      block bootstrap sur les 140 blocs de 10 du log
      `benchmark_revision_tous.log` (les données par item du run LLM
      ne sont plus disponibles — le block bootstrap est conservateur).
  [2] Re-mesure PAR ITEM de la cascade 0-LLM sur les 1319 items du test :
      bootstrap per-item (5000) + analyse d'erreurs + stabilité
      (première vs seconde moitié).
  [3] TRANSFERT — le vrai hors-échantillon :
      · SVAMP (1000 problèmes anglais, distribution différente)
      · échantillon GSM8K TRAIN (60 items jamais mesurés)
      → la cascade 0-LLM sans aucun ajustement.

Usage : python analyse_gsm8k_ic.py            (tout)
        python analyse_gsm8k_ic.py --phase test|transfert|ic
"""

import argparse
import json
import os
import random
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsm8k import GSM8KOndulatoire      # noqa: E402

DOSSIER = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.join(DOSSIER, "..", "data", "benchmarks", "gsm8k_test.jsonl")
TRAIN = os.path.join(DOSSIER, "..", "data", "benchmarks", "gsm8k_train.jsonl")
SVAMP = os.path.join(DOSSIER, "..", "data", "benchmarks", "SVAMP.json")
LOG_TOUS = os.path.join(DOSSIER, "benchmark_revision_tous.log")
RAPPORT = os.path.join(DOSSIER, "..", "data", "ia_ondulatoire",
                       "benchmark_gsm8k_ic.json")


def attendu_gsm8k(answer: str):
    m = re.search(r"####\s*(-?\d+(?:[.,]\d+)?)", answer or "")
    return float(m.group(1).replace(",", ".")) if m else None


def ok(valeur, a):
    return valeur is not None and a is not None and abs(valeur - a) < 1e-6


def ic_bootstrap(corrects: np.ndarray, n_rep=5000, graine=3):
    """IC 95 % de l'accuracy par bootstrap per-item."""
    rng = np.random.default_rng(graine)
    n = len(corrects)
    acc = corrects.mean()
    dist = np.array([corrects[rng.integers(0, n, n)].mean()
                     for _ in range(n_rep)])
    return acc, float(np.percentile(dist, 2.5)), float(np.percentile(dist, 97.5))


def ic_block_bootstrap(blocs: np.ndarray, n_rep=5000, graine=3):
    """IC 95 % par bootstrap sur des blocs (conservateur)."""
    rng = np.random.default_rng(graine)
    n = len(blocs)
    dist = np.array([blocs[rng.integers(0, n, n)].mean()
                     for _ in range(n_rep)])
    return blocs.mean(), float(np.percentile(dist, 2.5)), float(np.percentile(dist, 97.5))


# ────────────────────────────────────────────────────────────────────────
def phase_ic():
    """[1] IC du 85,52 % depuis le log (blocs de 10)."""
    print("=" * 70)
    print("[1] IC bootstrap du chiffre publié (révision LLM TOUS)")
    print("=" * 70)
    sans_cum, avec_cum = [], []
    for ligne in open(LOG_TOUS, encoding="utf-8"):
        m = re.search(r"\[(\d+) traités.*\] sans : (\d+) → avec : (\d+)", ligne)
        if m:
            sans_cum.append(int(m.group(2)))
            avec_cum.append(int(m.group(3)))
    if not avec_cum:
        print("  log illisible")
        return None
    # blocs = différences des cumuls (10 items par bloc)
    avec_blocs = np.diff([0] + avec_cum) / 10.0
    sans_blocs = np.diff([0] + sans_cum) / 10.0
    a, lo, hi = ic_block_bootstrap(avec_blocs)
    s, slo, shi = ic_block_bootstrap(sans_blocs)
    print(f"  SANS révision : {s * 100:.2f} %  IC95 [{slo * 100:.2f}, {shi * 100:.2f}]")
    print(f"  AVEC révision : {a * 100:.2f} %  IC95 [{lo * 100:.2f}, {hi * 100:.2f}]"
          f"  (block bootstrap, {len(avec_blocs)} blocs de 10)")
    return {"avec_revision": a, "ic_avec": [lo, hi],
            "sans_revision": s, "ic_sans": [slo, shi]}


# ────────────────────────────────────────────────────────────────────────
def phase_test():
    """[2] Re-mesure 0-LLM par item sur le test + erreurs + stabilité."""
    print("=" * 70)
    print("[2] Re-mesure 0-LLM par item — gsm8k_test.jsonl (1319)")
    print("=" * 70)
    s = GSM8KOndulatoire()
    corrects, moteurs, erreurs = [], [], []
    debut = time.time()
    with open(TEST, encoding="utf-8") as f:
        for idx, ligne in enumerate(f):
            d = json.loads(ligne)
            a = attendu_gsm8k(d["answer"])
            r = s.resoudre(d["question"])
            bon = ok(r["reponse_num"], a)
            corrects.append(bon)
            moteurs.append(str(r.get("moteur") or "resonance"))
            if not bon:
                erreurs.append((idx, r["reponse_num"], a, d["question"][:60]))
            if (idx + 1) % 200 == 0:
                print(f"  {idx + 1}/1319 traités · {time.time() - debut:.0f}s")
    corrects = np.array(corrects)
    acc, lo, hi = ic_bootstrap(corrects)
    print(f"\n  ACCURACY 0-LLM : {acc * 100:.2f} %  IC95 [{lo * 100:.2f}, {hi * 100:.2f}]"
          f"  (bootstrap per-item 5000, n=1319)")
    # stabilité temporelle
    n2 = len(corrects) // 2
    acc1 = corrects[:n2].mean()
    acc2 = corrects[n2:].mean()
    print(f"  Stabilité : 1ère moitié {acc1 * 100:.2f} % | 2e moitié {acc2 * 100:.2f} %")
    # analyse d'erreurs
    from collections import Counter
    print("  Répartition par moteur interne :")
    for moteur, n in Counter(moteurs).most_common():
        idx_m = np.array([i for i, m in enumerate(moteurs) if m == moteur])
        print(f"    {moteur:24s}: n={len(idx_m):4d} | précision {corrects[idx_m].mean() * 100:5.1f} %")
    n_none = sum(1 for _, rn, _, _ in erreurs if rn is None)
    n_faux = len(erreurs) - n_none
    print(f"  Échecs 0-LLM : {len(erreurs)} dont {n_none} sans détection "
          f"({n_none / len(erreurs) * 100:.0f} %) et {n_faux} valeur fausse")
    return {"accuracy": acc, "ic": [lo, hi], "moitie1": acc1, "moitie2": acc2,
            "echecs": len(erreurs), "sans_detection": n_none}


# ────────────────────────────────────────────────────────────────────────
def phase_transfert():
    """[3] Transfert : SVAMP (1000, anglais) + GSM8K train (60)."""
    print("=" * 70)
    print("[3] TRANSFERT hors-échantillon — cascade 0-LLM sans ajustement")
    print("=" * 70)
    s = GSM8KOndulatoire()

    # SVAMP
    svamp = json.load(open(SVAMP, encoding="utf-8"))
    rng = random.Random(42)
    ech = rng.sample(svamp, 300)          # 300 items (temps raisonnable)
    corrects = []
    for i, it in enumerate(ech):
        question = it["Question"]
        a = float(it["Answer"])
        r = s.resoudre(question)
        corrects.append(ok(r["reponse_num"], a))
        if (i + 1) % 100 == 0:
            print(f"  SVAMP {i + 1}/300")
    c = np.array(corrects)
    acc, lo, hi = ic_bootstrap(c)
    print(f"  SVAMP (300 items, anglais) : {acc * 100:.2f} %  "
          f"IC95 [{lo * 100:.2f}, {hi * 100:.2f}]")

    # GSM8K train (60)
    train = []
    with open(TRAIN, encoding="utf-8") as f:
        for ligne in f:
            train.append(json.loads(ligne))
    ech = rng.sample(train, 60)
    corrects = []
    for it in ech:
        a = attendu_gsm8k(it["answer"])
        r = s.resoudre(it["question"])
        corrects.append(ok(r["reponse_num"], a))
    c = np.array(corrects)
    acc2, lo2, hi2 = ic_bootstrap(c)
    print(f"  GSM8K TRAIN (60 items) : {acc2 * 100:.2f} %  "
          f"IC95 [{lo2 * 100:.2f}, {hi2 * 100:.2f}]")
    return {"svamp": acc, "ic_svamp": [lo, hi],
            "train": acc2, "ic_train": [lo2, hi2]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="tout",
                    choices=["tout", "ic", "test", "transfert"])
    args = ap.parse_args()
    rapport = {}
    if args.phase in ("tout", "ic"):
        rapport["ic_85_52"] = phase_ic()
    if args.phase in ("tout", "test"):
        rapport["test_0llm"] = phase_test()
    if args.phase in ("tout", "transfert"):
        rapport["transfert"] = phase_transfert()
    if args.phase == "tout":
        with open(RAPPORT, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=1)
        print(f"\nRapport → {RAPPORT}")
