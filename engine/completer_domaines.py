#!/usr/bin/env python3
"""
COMPLÉTER LES DOMAINES REFUSÉ → V2 (étape 3 de la porte d'intégration)
======================================================================
Les domaines economie / sciences / histoire / nature sont REFUSÉs faute
de VOLUME et de DENSITÉ (sujets répétés < 30 %). Ce script les complète
avec la matière première officielle du KB enrichi
(data/bootstrapper_output/knowledge_base_enriched.npz, 358 090 faits
sectorisés : HISTOIRE 73k, ECONOMIE 42k, MATHS_PURES 34k, BIOLOGIE 1,4k,
ECOLOGIE 277...).

Stratégie (mesure 10/08/2026 — c'est la DENSITÉ qui manque, pas le
volume brut) :
    1. extraire les faits du KB par SECTEURS ciblés (cfg.completion_source)
    2. ne garder que les faits dont le SUJET est un sujet EXISTANT du
       domaine converti, ou un sujet FRÉQUENT du KB (≥ 3 faits), plafonné
       à max_sujets sujets (le volume est borné naturellement)
    3. assainir avec le pipeline du cahier des charges (artefacts,
       relations parasites, vocabulaire contrôlé, objets-pays, vote
       majoritaire — 0 FAUX prime)
    4. écrire data/completions/<domaine>.json (format v2) et référencer
       dans cfg.completions → re-convertir (--force) → mesurer

Usage :
    python completer_domaines.py [--domaine official_economie] [--force]
"""

import os, sys, json, time
from collections import Counter

_ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE)

import numpy as np
import convertir_domaine_v2 as cdv

KB_ENRICHED = os.path.join(_ENGINE, "data", "bootstrapper_output",
                           "knowledge_base_enriched.npz")
CONFIG = os.path.join(_ENGINE, "data", "corrections_domaines.json")
COMPLETIONS = os.path.join(_ENGINE, "data", "completions")

DOMAINES = ["official_economie", "official_sciences",
            "official_histoire", "official_nature",
            "official_culture", "official_technologie"]


def charger_kb():
    """Charge le KB enrichi : liste de (s, r, o, secteur)."""
    with np.load(KB_ENRICHED, allow_pickle=True) as data:
        sujets = data["subjects"] if "subjects" in data else data["facts"][:, 0]
        relations = data["relations"] if "relations" in data else data["facts"][:, 1]
        objets = data["objects"] if "objects" in data else data["facts"][:, 2]
        secteurs = data["sectors"] if "sectors" in data else data["facts"][:, 3]
    return [(str(s), str(r), str(o), str(sec))
            for s, r, o, sec in zip(sujets, relations, objets, secteurs)]


def sujets_actuels(domaine):
    """Sujets du domaine converti (cache) — ceux à compléter en priorité."""
    chemin = os.path.join(_ENGINE, "data", f"domaine_converti_{domaine}",
                          "faits.json")
    if not os.path.exists(chemin):
        return set()
    with open(chemin, encoding="utf-8") as f:
        data = json.load(f)
    return {cdv._norm_entite(d["sujet"]) for d in data["faits"]}


def completer(domaine, cfg, force=False):
    """Extrait + assainit + fusionne les complétions d'un domaine."""
    t0 = time.time()
    src = cfg.get("completion_source")
    if not src:
        return None
    secteurs_cibles = {s.upper() for s in src["secteurs"]}
    max_sujets = int(src.get("max_sujets", 200))

    # 1. Extraire du KB par secteurs ciblés
    faits_kb = [f for f in charger_kb()
                if str(f[3]).upper() in secteurs_cibles]
    print(f"  {domaine}: {len(faits_kb):,} faits KB dans les secteurs "
          f"{sorted(secteurs_cibles)[:4]}...")

    # 2. Sélection des sujets : existants du domaine + fréquents du KB
    actuels = sujets_actuels(domaine)
    freq = Counter(cdv._norm_entite(s) for s, r, o, sec in faits_kb)
    fréquents = {s for s, c in freq.items() if c >= 3 and s not in actuels}
    sélection = set(actuels) | set(sorted(fréquents,
                                          key=lambda s: -freq[s])[:max_sujets])
    faits_filtrés = [(s, r, o, sec) for s, r, o, sec in faits_kb
                     if cdv._norm_entite(s) in sélection]
    print(f"  sujets sélectionnés : {len(sélection)} (actuels {len(actuels)} "
          f"+ fréquents KB {len(sélection) - len(actuels)}) → "
          f"{len(faits_filtrés):,} faits candidats")

    # 3. Assainissement (pipeline 0 FAUX prime)
    conservés, écartés, appliquées = cdv.assainir(faits_filtrés, cfg)
    print(f"  assainis : {len(conservés):,} conservés, {len(écartés):,} écartés, "
          f"{len(appliquées)} corrections")

    # 4. Écriture du fichier de complétion (format v2)
    os.makedirs(COMPLETIONS, exist_ok=True)
    out = os.path.join(COMPLETIONS, f"{domaine}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"faits": [{"sujet": s, "relation": r, "objet": o,
                              "secteur": sec} for s, r, o, sec in conservés]},
                  f, ensure_ascii=False, indent=1)

    # Référencer dans la config
    with open(CONFIG, encoding="utf-8") as f:
        tables = json.load(f)
    tables[domaine]["completions"] = [os.path.relpath(out, _ENGINE)
                                      .replace("\\", "/")]
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(tables, f, ensure_ascii=False, indent=2)

    print(f"  complétion écrite : {out} ({len(conservés):,} faits, "
          f"{time.time()-t0:.0f}s)")
    return out


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compléter les domaines REFUSÉ")
    parser.add_argument("--domaine", choices=DOMAINES, help="un seul domaine")
    parser.add_argument("--force", action="store_true",
                        help="reconvertir (--force) après complétion")
    args = parser.parse_args()

    with open(CONFIG, encoding="utf-8") as f:
        tables = json.load(f)

    domaines = [args.domaine] if args.domaine else DOMAINES
    for domaine in domaines:
        print("=" * 74)
        print(f"COMPLÉTION {domaine}")
        print("=" * 74)
        out = completer(domaine, tables[domaine], force=args.force)
        if out is None:
            print("  pas de source de complétion (completion_source absent)")
            continue
        # Re-conversion AVEC les complétions : recharger la config écrite
        # sur disque (completer() la modifie — la variable locale du main
        # n'est plus à jour).
        with open(CONFIG, encoding="utf-8") as f:
            cfg_a_jour = json.load(f)[domaine]
        from hologram_store import HologramStore
        store = HologramStore()
        statut, rapport, out_dir = cdv.convertir(store, domaine,
                                                 cfg_a_jour,
                                                 force=args.force)
        cdv.afficher_rapport(domaine, statut, rapport, out_dir)
        print()


if __name__ == "__main__":
    main()
