#!/usr/bin/env python3
"""
RE-VALIDER UN CACHE DE CONVERSION APRÈS ÉVOLUTION DES RÈGLES
============================================================
Purge les faits du cache (data/domaine_converti_<id>/faits.json) qui
violent les règles d'artefact actuelles (suffixe chiffré, Point(, dates
tronquées, numériques sur relations non-numériques...), re-valide les 3
règles et re-benchmarke. Évite le cycle « re-convertir depuis le NPZ »
(qui assainirait les faits déjà convertis).

Usage :
    python valider_cache_v2.py <holo_id> [--forcer-benchmark]
"""

import os, sys, json, time, argparse

_ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE)

import convertir_domaine_v2 as cdv


def main():
    parser = argparse.ArgumentParser(description="Re-valider un cache de conversion")
    parser.add_argument("holo_id")
    args = parser.parse_args()

    out_dir = os.path.join(_ENGINE, "data", f"domaine_converti_{args.holo_id}")
    chemin = os.path.join(out_dir, "faits.json")
    if not os.path.exists(chemin):
        print(f"cache introuvable : {chemin}")
        return 2

    with open(chemin, encoding="utf-8") as f:
        data = json.load(f)
    faits_cache = [(d["sujet"], d["relation"], d["objet"], d["secteur"])
                   for d in data["faits"]]
    cfg = cdv.charger_config().get(args.holo_id, {})

    t0 = time.time()
    conservés, écartés, appliquées = cdv.assainir(faits_cache, cfg)
    val = cdv.valider(conservés, cfg)
    secteurs, n_refus, n_gate = cdv.benchmarker(conservés, cfg)
    secteurs_ok = all(s["critere"] for s in secteurs) if secteurs else False
    gate_ok = n_refus == n_gate
    statut = "ACCEPTÉ" if (val["statut"] == "VALIDE" and secteurs_ok and gate_ok) \
             else "REFUSÉ"

    print(f"RE-VALIDATION {args.holo_id} : {statut}")
    print(f"  cache : {len(faits_cache)} → {len(conservés)} faits "
          f"(purge {len(écartés)}) | {len(appliquées)} corrections")
    print(f"  validation : {val}")
    print(f"  secteurs : {sum(1 for s in secteurs if s['critere'])}/"
          f"{len(secteurs)} ≥ 50 % | gate {n_refus}/{n_gate}")
    for s in secteurs:
        if not s["critere"]:
            print(f"    ✗ {s['secteur']:<40} n={s['n_faits']:>4} "
                  f"rappel@5({s['metrique']})={s['rappel_at_5']:.0%}")

    # Écriture (purge) + rapport
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"faits": [{"sujet": s, "relation": r, "objet": o, "secteur": sec}
                             for s, r, o, sec in conservés]},
                  f, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "validation.json"), "w", encoding="utf-8") as f:
        json.dump(val, f, ensure_ascii=False, indent=2)
    rapport_path = os.path.join(out_dir, "rapport_conversion.json")
    rapport = {
        "domaine_v1": args.holo_id,
        "revalidation": "purge des artefacts selon les règles du 10/08/2026",
        "corrections_expertes": appliquées,
        "ecartes": écartés,
        "n_ecartes": len(écartés),
        "n_faits_v2": len(conservés),
        "validation": val,
        "benchmark_secteurs": secteurs,
        "secteurs_ok": sum(1 for s in secteurs if s["critere"]),
        "secteurs_total": len(secteurs),
        "gate_refus": n_refus,
        "gate_total": n_gate,
        "statut": statut,
        "temps_total_s": round(time.time() - t0, 1),
    }
    with open(rapport_path, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print(f"  → {out_dir}/ ({time.time()-t0:.0f}s)")
    return 0 if statut == "ACCEPTÉ" else 2


if __name__ == "__main__":
    sys.exit(main())
