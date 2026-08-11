#!/usr/bin/env python3
"""test_global_hybride.py — LE TEST GLOBAL DE BOUT EN BOUT (DeepSeek)
====================================================================
La solution complète, EN RÉEL : noyau (mémoire + émulation, étages 1-2)
→ PhraseurInterne → chaîne externe (DeepSeek ici, Ollama sur les machines
qui l'ont) → AUDIT → fallback noyau (étage 3).

Protocole :
  A · Les 50 questions du protocole partagé, avec la vraie chaîne LLM ;
  B · 6 questions × 4 styles (conversationnel, vocal, bref, pédagogique).

Critères de réussite :
  · type exact + audit OK sur chaque réponse ;
  · MÉDICAL/CONDUITE : JAMAIS passés par le LLM (corpus exact) ;
  · style vocal : zéro symbole non parlé.

Statistiques honnêtes : fournisseur actif, taux de passage LLM, taux de
régénération stricte, taux de fallback interne, latences par type.
Rapport : data/benchmarks/test_global_hybride_report.json
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pont_hybride import PontHybride
from tests_ka_hybride import TESTS, TESTS_VOCAL, STYLES_A_TESTER, _SYMBOLES_NON_PARLES


def executer_protocole(pont):
    """A · Les 50 questions avec la vraie chaîne LLM."""
    resultats = []
    for question, attendu in TESTS:
        t0 = time.time()
        r = pont.traiter(question)
        dt = int((time.time() - t0) * 1000)
        etapes = r["etapes"]
        passe_llm = any(e.startswith("LLM (") for e in etapes)
        jamais_llm = any("pas de LLM" in e for e in etapes)
        medical = attendu in ("MEDICAL", "CONDUITE")
        # Critère : type exact + audit OK + le médical n'est JAMAIS passé au LLM
        ok = r["type"] == attendu and r["audit"] is True
        if medical:
            ok = ok and jamais_llm and not passe_llm
        resultats.append({
            "question": question, "attendu": attendu, "obtenu": r["type"],
            "ok": ok, "audit": r["audit"], "llm": passe_llm,
            "reponse": r["response"][:70], "etapes": etapes, "latence_ms": dt,
        })
    return resultats


def executer_styles_vivants(pont):
    """B · 6 questions × 4 styles avec la vraie chaîne LLM."""
    resultats = []
    for style in STYLES_A_TESTER:
        for question, attendu in TESTS_VOCAL:
            t0 = time.time()
            r = pont.traiter(question, style=style)
            dt = int((time.time() - t0) * 1000)
            mauvais = ([s for s in _SYMBOLES_NON_PARLES if s in r["response"]]
                       if style == "vocal" else [])
            ok = r["type"] == attendu and r["audit"] is True and not mauvais
            resultats.append({
                "style": style, "question": question, "attendu": attendu,
                "obtenu": r["type"], "ok": ok, "audit": r["audit"],
                "reponse": r["response"][:70], "latence_ms": dt,
                "symboles_restants": mauvais,
            })
    return resultats


def executer_elegan(pont):
    """C · Style ÉLÉGANT — demande EXCLUSIVE de style au LLM (polish DeepSeek).
    L'audit est re-vérifié APRÈS le polish ; le médical ne passe JAMAIS au
    polish (corpus exact)."""
    questions = [("7 × 8", "CALC"), ("chat", "FAIT"), ("quasar", "REFUS"),
                 ("qui es-tu ?", "IDENTITE"),
                 ("c'est quoi le diabète ?", "MEDICAL")]
    resultats = []
    for q, attendu in questions:
        t0 = time.time()
        r = pont.traiter(q, style="élégant")
        dt = int((time.time() - t0) * 1000)
        etapes = r["etapes"]
        polie = any(e.startswith("polish élégant:") for e in etapes)
        jamais_llm = any("pas de LLM" in e for e in etapes)
        medical = attendu == "MEDICAL"
        ok = r["type"] == attendu and r["audit"] is True
        if medical:
            ok = ok and not polie and jamais_llm
        else:
            ok = ok and polie
        resultats.append({
            "question": q, "attendu": attendu, "obtenu": r["type"], "ok": ok,
            "audit": r["audit"], "polish_applique": polie,
            "reponse": r["response"][:90], "etapes": etapes, "latence_ms": dt,
        })
    return resultats


def rapport_global(resultats_a, resultats_b, pont):
    ok_a = sum(1 for r in resultats_a if r["ok"])
    ok_b = sum(1 for r in resultats_b if r["ok"])
    llm = sum(1 for r in resultats_a if r["llm"])
    regen = sum(1 for r in resultats_a
                if any("régénéré" in e for e in r["etapes"]))
    fallback = sum(1 for r in resultats_a
                   if any("fallback" in e for e in r["etapes"]))
    lat = {t: [r["latence_ms"] for r in resultats_a
               if r["attendu"] == t] for t in
           ("IDENTITE", "CALC", "MEDICAL", "CONDUITE", "FAIT", "REFUS")}
    lat_moy = {t: (sum(v) // len(v) if v else 0) for t, v in lat.items()}
    lat_max = {t: (max(v) if v else 0) for t, v in lat.items()}
    return {
        "fournisseurs": [n for n, _ in pont.phraseur.fournisseurs]
        if pont.phraseur else [],
        "protocole": {"ok": ok_a, "total": len(resultats_a),
                      "passage_llm": f"{llm}/{len(resultats_a)}",
                      "regenerations_strictes": regen,
                      "fallbacks_internes": fallback},
        "styles": {"ok": ok_b, "total": len(resultats_b)},
        "latence_moyenne_ms_par_type": lat_moy,
        "latence_max_ms_par_type": lat_max,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def afficher(resultats, titre):
    ok = sum(1 for r in resultats if r["ok"])
    print(f"\n{'═'*66}\n{titre}\n{'═'*66}")
    print(f"  RÉSULTAT : {ok}/{len(resultats)}  {'✅' if ok == len(resultats) else '❌'}")
    for r in resultats:
        mark = "✅" if r["ok"] else "❌"
        extra = ""
        if "llm" in r:
            extra = f" · LLM={'oui' if r['llm'] else 'non'}"
        if "style" in r:
            extra = f" · style={r['style']}"
        print(f"  {mark} {r['question'][:38]:40s} [{r['obtenu']}] "
              f"({r['latence_ms']} ms){extra}")
        if not r["ok"]:
            print(f"      → {r['reponse']}")
            if r.get("symboles_restants"):
                print(f"      ⚠️ symboles : {r['symboles_restants']}")
    return ok == len(resultats)


def main():
    print("=" * 66)
    print("TEST GLOBAL — LA SOLUTION COMPLÈTE EN RÉEL (chaîne active détectée)")
    print("=" * 66)
    pont = PontHybride(utiliser_ollama=True)
    if not pont.phraseur or not pont.phraseur.disponible():
        print("  ❌ Aucun fournisseur LLM — le test global exige DeepSeek ou Ollama.")
        sys.exit(1)
    print(f"  Chaîne active : {[n for n, _ in pont.phraseur.fournisseurs]} "
          f"→ {pont.phraseur.actif}\n")

    t0 = time.time()
    resultats_a = executer_protocole(pont)
    ok_a = afficher(resultats_a, "A · LES 50 QUESTIONS — chaîne LLM réelle")
    dt = time.time() - t0
    print(f"  (durée {dt:.0f}s)")

    resultats_b = executer_styles_vivants(pont)
    ok_b = afficher(resultats_b, "B · 6 QUESTIONS × 4 STYLES — chaîne LLM réelle")

    resultats_c = executer_elegan(pont)
    ok_c = afficher(resultats_c, "C · STYLE ÉLÉGANT — polish exclusif LLM (audité)")

    stats = rapport_global(resultats_a, resultats_b, pont)
    print(f"\n  Statistiques : {json.dumps(stats['protocole'], ensure_ascii=False)}")
    print(f"  Latences moyennes (ms) : {stats['latence_moyenne_ms_par_type']}")
    print(f"  Latences max (ms)      : {stats['latence_max_ms_par_type']}")

    p = os.path.join("data", "benchmarks", "test_global_hybride_report.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"resultats_protocole": resultats_a,
                   "resultats_styles": resultats_b,
                   "resultats_elegan": resultats_c, "stats": stats},
                  f, indent=1, ensure_ascii=False)
    print(f"\nRapport : {p}")

    if not (ok_a and ok_b and ok_c):
        print("\n❌ TEST GLOBAL NON PASSÉ — voir les échecs ci-dessus.")
        sys.exit(1)
    print("\n✅ TEST GLOBAL PASSÉ — la solution complète fonctionne en réel "
          "(protocole + styles + élégant).")


if __name__ == "__main__":
    main()
