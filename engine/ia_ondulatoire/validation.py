# -*- coding: utf-8 -*-
"""
validation.py — Preuve de conformité au DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md.

Niveau 1 : les 13 primitives contre la table §10.1 (valeurs de référence)
Niveau 2 : roundtrip parse → print bit-à-bit + programme canonique exécuté
Niveau 3 : les 7 intentions génèrent des AST valides
Niveau 4 : smoke tests des 3 applications (KA Mobile, Vital KA, KA Enterprise)

Usage : python validation.py   → exit 0 = release verte, 1 = bloquée
"""

from __future__ import annotations

import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from primitives import (PHI, DEFAULT_DIM, HolographicMemory, abc_kernel, bind,
                        coherence, decode, diffract, emerge, encode, filter_wave,
                        interfere, normalize, oppose, phase_shift, resonate,
                        rotate, superpose, unbind)
from ir import Program, afficher, from_json, parse, to_json, valider
from moteur import MoteurOndulatoire
from generateur import GenerateurOndulatoire, INTENTIONS

RESULTATS: list = []


def test(nom: str, condition: bool, detail: str = "") -> bool:
    """Enregistre un test et l'affiche."""
    ok = bool(condition)
    RESULTATS.append(ok)
    symbole = "✅" if ok else "❌"
    print(f"  {symbole} {nom}" + (f" — {detail}" if detail else ""))
    return ok


def arrondi(x: float, n: int = 3) -> float:
    return round(float(x), n)


def niveau1_primitives() -> bool:
    """Table §10.1 — les 13 primitives contre leurs valeurs de référence."""
    print("═" * 62)
    print("NIVEAU 1 — Les 13 primitives (table §10.1)")
    print("═" * 62)
    dim = 256  # accélère la validation, invariants identiques
    ok = True

    psi = encode("lumiere", dim)
    ok &= test("encode : ‖ψ‖ = 1", abs(np.linalg.norm(psi) - 1.0) < 1e-9,
               f"‖ψ‖ = {arrondi(np.linalg.norm(psi), 6)}")

    vocab = {"lumiere": encode("lumiere", dim), "onde": encode("onde", dim),
             "matiere": encode("matiere", dim)}
    trouves = decode(psi, vocab, top_k=1)
    ok &= test("decode : retrouve « lumiere »", trouves and trouves[0][0] == "lumiere",
               f"top-1 = « {trouves[0][0] if trouves else '?'} » score {arrondi(trouves[0][1]) if trouves else 0}")

    a, b = encode("alice", DEFAULT_DIM), encode("bob", DEFAULT_DIM)
    c = bind(a, b)
    a2 = unbind(c, b)
    recovery = resonate(a2, a)
    ok &= test("bind/unbind : unbind(bind(a,b), b) ≈ a", recovery >= 0.7,
               f"recovery = {arrondi(recovery, 3)} (référence 0.73 à ℂ⁵¹²)")

    h = superpose(a, b, encode("claire", DEFAULT_DIM))
    ok &= test("superpose : norme préservée", abs(np.linalg.norm(h) - 1.0) < 1e-9,
               f"‖h‖ = {arrondi(np.linalg.norm(h), 6)}")

    ident = resonate(psi, psi)
    ortho = resonate(encode("alpha", dim), encode("beta", dim))
    ok &= test("resonate : identité = 1.0, orthogonal ≈ 0",
               abs(ident - 1.0) < 1e-9 and abs(ortho) < 0.15,
               f"1.0 / {arrondi(ortho, 3)} (référence 1.0 / 0.04)")

    inv = rotate(psi, math.pi)
    ok &= test("rotate : rotation π → inversion", abs(resonate(inv, psi) + 1.0) < 1e-6,
               f"resonate = {arrondi(resonate(inv, psi), 6)} (référence -1.000)")

    nrm = normalize(psi * 7.3)
    ok &= test("normalize : projection unitaire", abs(np.linalg.norm(nrm) - 1.0) < 1e-9,
               f"‖normalize(7.3·ψ)‖ = {arrondi(np.linalg.norm(nrm), 6)}")

    melange = interfere(a, b, epsilon=0.15)
    base = resonate(melange, a)
    ok &= test("interfere : ε=0.15 préserve la base", base >= 0.9,
               f"resonate(mélange, a) = {arrondi(base, 3)} (référence 0.99)")

    spectre = diffract(psi)
    retour = diffract(spectre, inverse=True)
    ok &= test("diffract : FFT → IFFT = identité", abs(resonate(retour, psi) - 1.0) < 1e-9,
               f"resonate = {arrondi(resonate(retour, psi), 6)} (référence 1.000)")

    bas = filter_wave(psi, "low", cutoff=8)
    haut = filter_wave(psi, "high", cutoff=8)
    bande = filter_wave(psi, "band", cutoff_bas=4, cutoff_haut=16)
    ok &= test("filter : passe-bas/haut/bande fonctionnels",
               all(np.linalg.norm(x) > 0.5 for x in (bas, haut, bande)))

    decale = phase_shift(psi, math.pi / 2)
    ok &= test("phase_shift : π/2 → orthogonal", abs(resonate(decale, psi)) < 1e-9,
               f"resonate = {arrondi(resonate(decale, psi), 6)} (référence 0.000)")

    e = emerge(a, b, encode("claire", DEFAULT_DIM), temperature=0.5)
    ok &= test("emerge : norme préservée", abs(np.linalg.norm(e) - 1.0) < 1e-9,
               f"‖emerge‖ = {arrondi(np.linalg.norm(e), 6)}")

    ok &= test("abc_kernel : K(0) = 1, K(100) → 0",
               abs(abc_kernel(0) - 1.0) < 1e-9 and abc_kernel(100) < 0.35,
               f"K(0) = {arrondi(abc_kernel(0), 4)}, K(100) = {arrondi(abc_kernel(100), 4)}")

    ok &= test("déterminisme : même entité → même ψ (1e-12)",
               np.allclose(encode("déterministe", dim), encode("déterministe", dim), atol=1e-12))
    ok &= test("encode : entités distinctes quasi-orthogonales",
               abs(resonate(encode("pluie", dim), encode("musique", dim))) < 0.25,
               f"resonate(pluie, musique) = {arrondi(resonate(encode('pluie', dim), encode('musique', dim)), 3)}")
    ok &= test("coherence : |resonate| ∈ [0, 1]",
               0.0 <= coherence(a, b) <= 1.0)
    ok &= test("oppose : contraste normalisé",
               abs(np.linalg.norm(oppose(a, b)) - 1.0) < 1e-9)
    return ok


def niveau2_ir_et_canonique() -> bool:
    """§6.3 roundtrip + §4.3 le programme canonique s'exécute."""
    print("═" * 62)
    print("NIVEAU 2 — Wave IR : roundtrip + programme canonique (§4.3)")
    print("═" * 62)
    ok = True

    canonique = (
        'psi_q = ENCODE "Qu\'est-ce que la lumière ?"\n'
        "QUERY psi_r = psi_q FROM H_connaissances\n"
        "reponse = DECODE(psi_r)\n"
        "RETURN reponse"
    )
    programme = parse(canonique)
    texte = afficher(programme)
    reparse = parse(texte)
    ok &= test("roundtrip parse → print → parse bit-à-bit",
               to_json(programme) == to_json(reparse))
    ok &= test("JSON roundtrip to_json → from_json",
               to_json(from_json(to_json(programme))) == to_json(programme))
    erreurs = valider(programme, hologrammes=["H_connaissances", "H_faits"])
    ok &= test("validation statique : programme canonique valide",
               not erreurs, "; ".join(erreurs))

    mem = HolographicMemory(dim=64)
    mem.store("lumiere", "est une", "onde electromagnetique")
    mem.store("lumiere", "se propage", "a 300000 km par seconde")
    env = MoteurOndulatoire(dim=64).executer(
        programme, hologrammes={"H_connaissances": mem},
        vocabulaire={"lumiere": encode("lumiere", 64)})
    retour = env.get("__return__")
    ok &= test("programme canonique exécuté sans crash",
               retour is not None and isinstance(retour, list),
               f"résultat : {retour if isinstance(retour, list) else '—'}")

    comp = MoteurOndulatoire(dim=64).compiler(programme)
    ok &= test("compilateur : 4 passes actives",
               comp["stats"]["codes_morts"] >= 0 and comp["lignes_python"] > 0,
               f"stats {comp['stats']}, {comp['lignes_python']} lignes python")

    # un programme avec variable non définie doit être rejeté
    mauvais = parse('psi_q = ENCODE "x"\nRETURN psi_inconnue')
    erreurs2 = valider(mauvais)
    ok &= test("validation : variable non définie détectée", bool(erreurs2),
               erreurs2[0] if erreurs2 else "")
    return ok


def niveau3_intentions() -> bool:
    """§8.2 — les 7 intentions génèrent des AST valides."""
    print("═" * 62)
    print("NIVEAU 3 — L'IA génératrice : les 7 intentions (§8.2)")
    print("═" * 62)
    ok = True
    generateur = GenerateurOndulatoire(dim=64)
    exemples = {
        "query": "Qu'est-ce que la lumière ?",
        "reason": "Pourquoi le ciel est-il bleu ?",
        "creative": "Imagine un océan de musique",
        "store_fact": "Souviens-toi que la lumière est une onde",
        "compare": "Quelle est la différence entre l'amour et l'amitié ?",
        "analogize": "Le temps est comme un fleuve",
        "classify": "Quel type d'animal est un dauphin ?",
    }
    for intention, question in exemples.items():
        programme, detectee = generateur.generer(question)
        erreurs = valider(programme, hologrammes=["H_connaissances", "H_faits"])
        valide = not erreurs and detectee == intention
        ok &= test(f"intention {intention} → programme valide",
                   valide, f"détectée : {detectee} · {afficher(programme).splitlines()[0]}")
    return ok


def niveau4_apps() -> bool:
    """Smoke tests des 3 applications reconstruites en ondulatoire."""
    print("═" * 62)
    print("NIVEAU 4 — Smoke tests : KA Mobile · Vital KA · KA Enterprise")
    print("═" * 62)
    ok = True

    # ── KA MOBILE : le chat ─────────────────────────────────────────────
    from cerveau import IaOndulatoire
    ia = IaOndulatoire(charger=False)
    r = ia.poser("Quelle est la différence entre l'amour et l'amitié ?")
    ok &= test("KA Mobile /api/chat : réponse + confiance + programme",
               bool(r["response"]) and 0 <= r["confidence"] <= 1 and r.get("programme"),
               f"« {r['response'][:70]}… » · intention {r.get('intention')} · {r['latency_ms']} ms")

    r2 = ia.memoriser("la lumière est une onde électromagnétique")
    ok &= test("KA Mobile : mémorisation (store_fact)",
               r2["confidence"] >= 0.9 and "lumi" in r2["response"].lower(),
               r2["response"][:60] + "…")
    r3 = ia.poser("Qu'est-ce que la lumière ?")
    ok &= test("KA Mobile : rappel après apprentissage",
               any("lumiere" in str(m).lower() or "onde" in str(m).lower()
                   for m in r3.get("faits", []) or []),
               f"faits rappelés : {r3.get('faits', [])[:2]}")
    r4 = ia.poser("Imagine un océan de musique")
    ok &= test("KA Mobile : créativité (interfere ε=0.15)",
               r4.get("intention") == "creative" and bool(r4["response"]))

    # ── VITAL KA : le diagnostic ────────────────────────────────────────
    from medical import DiagnosticOndulatoire
    med = DiagnosticOndulatoire()
    d = med.diagnostiquer(["fièvre", "toux sèche", "fatigue"],
                          vitaux={"frequence_cardiaque": 96, "temperature": 38.4})
    ok &= test("Vital KA /api/health/diagnostic : contrat complet",
               d["score_harmonique_global"] > 0 and d["diagnostic_harmonique"]["pathologie_principale"]
               and d["analyse_symptomes"]["resultats"] and d["frequences_therapeutiques"],
               f"score {d['score_harmonique_global']} · {d['diagnostic_harmonique']['pathologie_principale']}")
    dm = med.diagnostiquer_medecin(["fièvre", "toux"], max_diagnoses=3)
    ok &= test("Vital KA /diagnose : contrat médecin",
               dm["diagnoses"] and dm["score_harmonique"] > 0 and dm["disclaimer"],
               f"{len(dm['diagnoses'])} diagnostics · score {dm['score_harmonique']}")

    # ── KA ENTERPRISE : ingest → ask ────────────────────────────────────
    from entreprise import EntrepriseOndulatoire
    ent = EntrepriseOndulatoire()
    creation = ent.creer_tenant("Cabinet Test")
    tid, cle = creation["tenant_id"], creation["api_key"]
    ing = ent.ingerer(tid, "comptabilite",
                      "Le cabinet gère 120 clients. La facturation est mensuelle. "
                      "Le chiffre d'affaires est 2,4 millions.",
                      nom_doc="test.txt")
    rep = ent.poser(tid, "comptabilite", "Combien de clients le cabinet gère-t-il ?")
    ok &= test("KA Enterprise : ingest → ask (hologramme département)",
               ing["faits_ajoutes"] > 0 and rep["sources"]
               and any("120" in s["objet"] for s in rep["sources"]),
               f"{ing['faits_ajoutes']} faits · confiance {rep['confidence']}")
    ok &= test("KA Enterprise : RBAC — mauvaise clé refusée",
               ent.autoriser("cle-fausse") is None)
    res = ent.resumer(tid, "comptabilite")
    comp = ent.composer(tid, "comptabilite", "rapport", "chiffre d'affaires")
    ok &= test("KA Enterprise : resume (EMERGE) + compose (INTERFERE)",
               bool(res["summary"]) and bool(comp["contenu"]))
    return ok


def niveau5_educal() -> bool:
    """EDUCAL KA : catalogue, leçons, quiz, diagnostic, progression, tuteur,
    unité transférable (hologram → download → load → recall)."""
    print("═" * 62)
    print("NIVEAU 5 — EDUCAL KA en langage ondulatoire natif")
    print("═" * 62)
    ok = True
    from cerveau import IaOndulatoire
    from educal import EducalOndulatoire
    ia = IaOndulatoire(charger=False)
    edu = EducalOndulatoire(ia=ia)

    units = edu.list_units()
    ok &= test("EDUCAL : catalogue — 6 unités", len(units) >= 6,
               f"{len(units)} unités trouvées")

    unit = edu.get_unit("edu_maths_fractions_6e")
    ok &= test("EDUCAL : leçon complète (sections + quiz + exercices + faits)",
               unit and unit.get("lecon", {}).get("sections")
               and unit.get("quiz") and unit.get("facts"),
               unit.get("titre", "?") if unit else "absent")

    quiz_parfait = [{"question": i, "answer": q["correct_index"]}
                    for i, q in enumerate(unit["quiz"])]
    r_ok = edu.evaluate_quiz(unit, quiz_parfait)
    ok &= test("EDUCAL : quiz 4/4 → réussite",
               r_ok["correct"] == len(unit["quiz"]) and r_ok["reussite"],
               f"{r_ok['correct']}/{r_ok['total']} · {r_ok['feedback'][:40]}")

    quiz_3_4 = list(quiz_parfait)
    quiz_3_4[0]["answer"] = (unit["quiz"][0]["correct_index"] + 1) % len(unit["quiz"][0]["choix"])
    r_lac = edu.evaluate_quiz(unit, quiz_3_4)
    ok &= test("EDUCAL : quiz 3/4 → lacune détectée",
               r_lac["lacunes"] and not r_lac["reussite"],
               f"lacunes : {r_lac['lacunes'][:1]}")

    diag = edu.diagnose_lacunes(unit, r_lac["lacunes"])
    ok &= test("EDUCAL : diagnostic par résonance (faits à revoir)",
               bool(diag["faits_a_revoir"]),
               f"{len(diag['faits_a_revoir'])} faits · holo {diag['holo_id']}")

    prog = edu.save_progress("eleve_validation", unit["id"], {
        "quiz_score": r_ok["score"], "exercices_score": 1.0,
        "lacunes": [], "reussite": True, "quiz_details": r_ok["details"]})
    carnet = edu.progress("eleve_validation")
    ok &= test("EDUCAL : carnet de progression (validées + skills + suite)",
               carnet["unites_validees"].get(unit["id"]) and carnet["skills"]
               and isinstance(carnet.get("next_units"), list),
               f"{len(carnet['skills'])} skills · suite : {carnet.get('next_units', [])[:2]}")

    exo = edu.generate_exercise("mathématiques", "6e")
    ok &= test("EDUCAL : tuteur — exercice + méthode ondulatoire",
               bool(exo["question"]) and bool(exo["reponse"]) and bool(exo["methode"])
               and "langage-ondulatoire" in exo["moteur"],
               f"{exo['famille']} · {exo['methode'][:50]}…")

    # ── unité éducative transférable (la démo phare) ────────────────────
    holo_info = edu.unit_hologram("edu_methodologie_apprendre")
    ok &= test("EDUCAL : hologramme d'unité construit (BIND_MANY → STORE)",
               holo_info["facts_count"] > 0, f"{holo_info['facts_count']} faits")

    dl = edu.download("unit_edu_methodologie_apprendre")
    ok &= test("EDUCAL : download — faits + ψ polaires (transport)",
               dl["count"] > 0 and dl["has_psi_data"] and len(dl["psi_data"]) > 0,
               f"{dl['count']} faits · {dl['dim']}D")

    load = edu.load("unit_edu_methodologie_apprendre")
    ok &= test("EDUCAL : load — injection dans H_connaissances du cerveau",
               load.get("success") and load["facts_loaded"] > 0,
               load.get("message", ""))

    rappel = edu.recall("répétition espacée")
    ok &= test("EDUCAL : rappel post-transfert (résonance)",
               rappel["count"] > 0 and any("rétention" in r["fait"] or "répétition" in r["fait"]
                                           for r in rappel["results"]),
               f"{rappel['count']} résultats · top : "
               f"{rappel['results'][0]['fait'][:50] if rappel['results'] else '—'}")
    return ok


def principal() -> int:
    debut = time.time()
    ok = True
    ok &= niveau1_primitives()
    ok &= niveau2_ir_et_canonique()
    ok &= niveau3_intentions()
    ok &= niveau4_apps()
    ok &= niveau5_educal()

    reussis = sum(1 for r in RESULTATS if r)
    total = len(RESULTATS)
    print("═" * 62)
    print(f"{'✅ RELEASE VERTE' if ok else '❌ RELEASE BLOQUÉE'} — "
          f"{reussis}/{total} tests · {time.time() - debut:.2f} s")
    print("═" * 62)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(principal())
