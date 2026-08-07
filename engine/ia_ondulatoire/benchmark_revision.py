# -*- coding: utf-8 -*-
"""
benchmark_revision.py — Benchmark GSM8K officiel AVEC révision LLM sélective.

Mesure la politique réelle (résoudre + révision des moteurs faibles par
DeepSeek) sur les 1 319 problèmes officiels. Le script est robuste :
checkpoint après chaque problème → reprise automatique en cas d'interruption.

Usage :
    python benchmark_revision.py            # complet (≈ 1 h)
    python benchmark_revision.py --sample 30   # essai rapide
    python benchmark_revision.py --reprendre   # reprendre le checkpoint

Rapport → data/ia_ondulatoire/benchmark_revision.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gsm8k import GSM8KOndulatoire      # noqa: E402
from revision import RevisionLLM        # noqa: E402

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "data", "ia_ondulatoire")
DATASET = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "data", "benchmarks", "gsm8k_test.jsonl")
CHEMIN_CKPT = os.path.join(DOSSIER, "benchmark_revision_ckpt.json")
CHEMIN_RAPPORT = os.path.join(DOSSIER, "benchmark_revision.json")


def attendu(answer: str):
    m = re.search(r"####\s*(-?\d+(?:[.,]\d+)?)", answer or "")
    return float(m.group(1).replace(",", ".")) if m else None


def _ok(valeur, a) -> bool:
    return valeur is not None and a is not None and abs(valeur - a) < 1e-6


def lancer(sample: int = 0, reprendre: bool = True) -> dict:
    s = GSM8KOndulatoire()
    rev = RevisionLLM(timeout=90)
    print(f"Réviseur disponible : {rev.disponible()}")

    resultats = []
    if reprendre and os.path.exists(CHEMIN_CKPT):
        try:
            with open(CHEMIN_CKPT, encoding="utf-8") as f:
                resultats = json.load(f).get("resultats", [])
            print(f"Checkpoint repris : {len(resultats)} problèmes déjà traités")
        except Exception:
            resultats = []
    faits = {r["idx"] for r in resultats}

    debut = time.time()
    appels_llm = sum(1 for r in resultats if r.get("plan"))
    with open(DATASET, encoding="utf-8") as f:
        for idx, ligne in enumerate(f):
            if sample and idx >= sample:
                break
            if idx in faits:
                continue
            d = json.loads(ligne)
            a = attendu(d.get("answer", ""))
            r0 = s.resoudre(d["question"])
            entree = {"idx": idx, "attendu": a,
                      "sans": r0["reponse_num"],
                      "moteur": str(r0.get("moteur") or "resonance"),
                      "ok_sans": _ok(r0["reponse_num"], a)}
            r1 = s.resoudre(d["question"], reviser=True, revision=rev)
            entree["avec"] = r1["reponse_num"]
            entree["ok_avec"] = _ok(r1["reponse_num"], a)
            entree["plan"] = r1.get("plan_llm")
            if entree["plan"]:
                appels_llm += 1
            resultats.append(entree)

            if len(resultats) % 10 == 0:
                ckpt = {"resultats": resultats,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
                with open(CHEMIN_CKPT, "w", encoding="utf-8") as fw:
                    json.dump(ckpt, fw, ensure_ascii=False)
                ok0 = sum(1 for r in resultats if r["ok_sans"])
                ok1 = sum(1 for r in resultats if r["ok_avec"])
                print(f"[{len(resultats)} traités · {time.time()-debut:.0f}s · "
                      f"{appels_llm} appels LLM] sans : {ok0} → avec : {ok1}")

    # ── rapport final ───────────────────────────────────────────────────
    n = len(resultats)
    ok0 = sum(1 for r in resultats if r["ok_sans"])
    ok1 = sum(1 for r in resultats if r["ok_avec"])
    gagnes = sum(1 for r in resultats if r["ok_avec"] and not r["ok_sans"])
    perdus = sum(1 for r in resultats if r["ok_sans"] and not r["ok_avec"])
    par_moteur = {}
    for r in resultats:
        cle = "resonance" if r["moteur"] == "resonance" else \
            r["moteur"].split("(")[0].strip()
        par_moteur.setdefault(cle, [0, 0])
        par_moteur[cle][0] += 1
        if r["ok_avec"]:
            par_moteur[cle][1] += 1

    rapport = {
        "benchmark": "gsm8k_test.jsonl (complet) + révision LLM sélective",
        "echantillon": n,
        "correct_sans_revision": ok0,
        "precision_sans_revision": round(ok0 / n, 4) if n else 0,
        "correct_avec_revision": ok1,
        "precision_avec_revision": round(ok1 / n, 4) if n else 0,
        "gagnes": gagnes, "perdus": perdus,
        "appels_llm": appels_llm,
        "duree_s": round(time.time() - debut, 1),
        "moteur": "langage-ondulatoire-v1 + DeepSeek (révision sélective)",
        "par_moteur": {k: {"n": v[0], "bons": v[1]} for k, v in par_moteur.items()},
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    os.makedirs(DOSSIER, exist_ok=True)
    with open(CHEMIN_RAPPORT, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=1)
    if os.path.exists(CHEMIN_CKPT) and n >= (sample or 1319):
        os.remove(CHEMIN_CKPT)          # benchmark terminé → checkpoint purgé
    print("═" * 62)
    print("BENCHMARK GSM8K + RÉVISION LLM SÉLECTIVE")
    print("═" * 62)
    print(f"Échantillon      : {n} problèmes")
    print(f"Sans révision    : {ok0}/{n} = {ok0/max(1,n)*100:.2f} %")
    print(f"Avec révision    : {ok1}/{n} = {ok1/max(1,n)*100:.2f} %  (+{gagnes} gagnés, −{perdus} perdus)")
    print(f"Appels LLM       : {appels_llm} · durée {rapport['duree_s']:.0f} s")
    print("═" * 62)
    return rapport


if __name__ == "__main__":
    analyseur = argparse.ArgumentParser()
    analyseur.add_argument("--sample", type=int, default=0)
    analyseur.add_argument("--reprendre", action="store_true", default=True)
    args = analyseur.parse_args()
    lancer(sample=args.sample, reprendre=args.reprendre)
