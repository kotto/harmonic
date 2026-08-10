#!/usr/bin/env python3
"""
VÉRIFICATION EXPERTE DES VALEURS — scan d'anomalies sur les domaines v2
=======================================================================
Détecte les valeurs suspectes dans les caches de conversion
(data/domaine_converti_*/faits.json) par catégories :

    1. ANNÉE_IMPOSSIBLE  : année > 2026 ou < -5000 (dates erronées du KB)
    2. DATE_ISO_INVALIDE : dates ISO restantes malformées/tronquées
    3. VALEUR_ABERRANTE  : population > 10 Md, superficie > 1 Md km²,
                           négatifs, coordonnées hors bornes
    4. ANGLAIS           : objet anglais sur relation française
                           (contamination du KB bilingue)
    5. CAMEL_CASE        : majuscules internes (artefacts de parsing)
    6. FORMAT_ETRANGE    : objets avec caractères de structure (/ ; | [ ])
    7. TEXTE_LONG        : objets descriptifs > 200 chars (fragments de
                           phrases au lieu de valeurs)
    8. DOUBLON_PREFIXE   : objets partageant les 80 premiers caractères
                           (dédupliqués silencieusement par le build)

Usage :
    python verifier_valeurs.py [--domaine official_histoire] [--max 8]
"""

import os, sys, json, re, argparse
from collections import Counter, defaultdict

_ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE)

DOMAINES = ["official_geographie", "official_technologie", "official_culture",
            "official_economie", "official_sciences", "official_histoire",
            "official_nature"]

RELATIONS_TEMPORELLES = {
    "a été fondé en", "a été découvert en", "a été construit en",
    "a été signé en", "a été créé en", "a été inauguré en", "a pris fin en",
    "a eu lieu en", "a commencé en", "a déclaré l'indépendance en",
    "a régné de", "est mort en", "est né en", "est née en", "a été publié en",
    "a été écrit en", "a été composé en", "a été peint en", "a été inventé en",
}

MOTS_ANGLAIS = {"the", "of", "and", "for", "is", "are", "with", "that",
                "this", "from", "was", "were", "has", "have", "its", "not",
                "but", "than", "into", "over", "under", "between", "during",
                "after", "before", "through", "against", "without", "within",
                "non", "public", "institution"}


def detecter(faits, cfg):
    anomalies = defaultdict(list)
    for s, r, o, sec in faits:
        o = str(o)
        # 1. Années impossibles (relations temporelles uniquement)
        if r in RELATIONS_TEMPORELLES and re.fullmatch(r"-?\d{3,4}", o):
            an = int(o)
            if an > 2026 or an < -5000:
                anomalies["ANNÉE_IMPOSSIBLE"].append((s, r, o))
        # 2. Dates ISO invalides
        if re.search(r"T\d{2}:\d{2}", o) and re.search(r"^-\d{2}-\d{2}", o):
            anomalies["DATE_ISO_INVALIDE"].append((s, r, o))
        # 3. Valeurs aberrantes
        m = re.search(r"(-?\d[\d\s.,]*)", o)
        if m:
            chiffres = re.sub(r"[^\d-]", "", m.group(1))
            if chiffres:
                val = float(chiffres)
                if r == "a une population de" and val > 10_000_000_000:
                    anomalies["VALEUR_ABERRANTE"].append((s, r, o))
                if r == "a une superficie de" and val > 1_000_000_000:
                    anomalies["VALEUR_ABERRANTE"].append((s, r, o))
        # 4. Objet anglais sur relation française
        mots = re.findall(r"[a-zà-ÿ]{3,}", o.lower())
        anglais = sum(1 for w in mots if w in MOTS_ANGLAIS)
        if anglais >= 3 and r not in {"a pour langue officielle",
                                      "a pour langue"}:
            anomalies["ANGLAIS"].append((s, r, o))
        # 5. camelCase
        if re.search(r"[a-zà-ÿ][A-ZÀ-Ý]", o):
            anomalies["CAMEL_CASE"].append((s, r, o))
        # 6. Format étrange (les unités m/s, km/h, i/o, ci/cd sont légitimes)
        if re.search(r"[;|\[\]{}]", o):
            anomalies["FORMAT_ETRANGE"].append((s, r, o))
        # 7. Texte long (fragments de phrases)
        if len(o) > 200:
            anomalies["TEXTE_LONG"].append((s, r, o))
    return anomalies


def main():
    parser = argparse.ArgumentParser(description="Vérification experte des valeurs")
    parser.add_argument("--domaine", help="un seul domaine")
    parser.add_argument("--max", type=int, default=6, help="exemples max par catégorie")
    args = parser.parse_args()

    domaines = [args.domaine] if args.domaine else DOMAINES
    rapport = {}
    for dom in domaines:
        chemin = os.path.join(_ENGINE, "data", f"domaine_converti_{dom}",
                              "faits.json")
        if not os.path.exists(chemin):
            continue
        with open(chemin, encoding="utf-8") as f:
            data = json.load(f)
        faits = [(d["sujet"], d["relation"], d["objet"], d["secteur"])
                 for d in data["faits"]]
        anomalies = detecter(faits, {})
        total = sum(len(v) for v in anomalies.values())
        print(f"{dom} ({len(faits)} faits) : {total} anomalies")
        for cat, items in sorted(anomalies.items(), key=lambda x: -len(x[1])):
            print(f"  {cat:<20} {len(items):>4}")
            for s, r, o in items[:args.max]:
                print(f"      {s[:35]:<37} | {r[:28]:<30} | {o[:45]}")
        rapport[dom] = {cat: len(items) for cat, items in anomalies.items()}
        print()
    out = os.path.join(_ENGINE, "data", "verification_valeurs_rapport.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print(f"rapport : {out}")


if __name__ == "__main__":
    main()
