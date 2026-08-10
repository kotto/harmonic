#!/usr/bin/env python3
"""
VÉRIFICATION DE BOUT EN BOUT — serveur KA + 7 domaines v2 (10/08/2026)
======================================================================
Charge le serveur (ka_server.py), puis teste en conditions réelles :
    1. POST /api/store/convert/<holo_id> — conversion dynamique
       (déjà v2 → 200/v2 ; inconnu → 404)
    2. POST /api/store/recall — résonance ondulatoire sur les 7 domaines
       (questions de contrôle : capitale du bresil → brasilia, etc.)
    3. POST /api/chat — consensus multi-domaines (les faits v2 sont
       utilisés dans la réponse)

Usage :
    python verifier_bout_en_bout.py [--silencieux]
Code retour : 0 si tout passe, 2 sinon.
"""

import os, sys, importlib.util, json

_ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE)

QUESTIONS_CONTROLE = [
    # (holo_id, question, attendu_dans_reponses)
    ("official_geographie", "quelle est la capitale du bresil", "brasilia"),
    ("official_technologie", "quel est le type du forum sur la gouvernance de l internet",
     "organisation internationale"),
    ("official_sciences", "que vaut la vitesse de la lumiere", "299 792 458"),
    ("official_economie", "quelle banque a son siege a paris", None),
]


def main():
    silencieux = "--silencieux" in sys.argv
    spec = importlib.util.spec_from_file_location(
        "ka_server_file", os.path.join(_ENGINE, "ka_server.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    client = mod.app.test_client()

    ok = True

    # 1. Conversion dynamique
    for hid, attendu in (("official_geographie", "v2"),
                         ("official_zzz_inexistant", "404")):
        r = client.post(f"/api/store/convert/{hid}", json={})
        d = r.get_json() or {}
        statut = d.get("status", "")
        passe = (attendu == "v2" and statut == "v2") or \
                (attendu == "404" and r.status_code == 404)
        ok &= passe
        print(f"[{'✓' if passe else '✗'}] convert {hid:<28} "
              f"HTTP {r.status_code} status={statut}")

    # 2. Recall ondulatoire (7 domaines, questions de contrôle)
    for hid, q, attendu in QUESTIONS_CONTROLE:
        r = client.post("/api/store/recall",
                        json={"holo_id": hid, "query": q, "top_k": 5})
        d = r.get_json() or {}
        results = d.get("results", [])
        textes = " ".join(f"{res.get('sujet', '')} {res.get('relation', '')} "
                          f"{res.get('objet', '')}" for res in results)
        passe = r.status_code == 200 and len(results) > 0 and \
                (attendu is None or attendu in textes)
        ok &= passe
        top = results[0] if results else {}
        print(f"[{'✓' if passe else '✗'}] recall {hid:<24} "
              f"top: {str(top.get('sujet', ''))[:25]} | "
              f"{str(top.get('objet', ''))[:35]}")

    # 3. Chat (consensus multi-domaines)
    r = client.post("/api/chat", json={"message": "quelle est la capitale du bresil"})
    d = r.get_json() or {}
    resp = str(d.get("response", d.get("reponse", "")))
    passe = r.status_code == 200 and "brasilia" in resp
    ok &= passe
    print(f"[{'✓' if passe else '✗'}] chat « capitale du bresil » → "
          f"{'contient brasilia' if 'brasilia' in resp else 'AUTRE réponse'}")

    print(f"\nRÉSULTAT : {'TOUT PASSE ✓' if ok else 'ÉCHECS DÉTECTÉS'}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
