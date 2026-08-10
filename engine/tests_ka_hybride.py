#!/usr/bin/env python3
"""tests_ka_hybride.py — SUITE DE TESTS DU PONT HYBRIDE KA
================================================================
Protocole pré-enregistré : chaque question a un type attendu.
La suite est exécutée contre le pont serveur (pont_hybride.py) et
le noyau mobile (ka_hybrid.js via test_mobile_kernel.js, node).
Le protocole est partagé : data/benchmarks/protocole_ka.json.

Catégories (50 questions) :
  IDENTITE  — qui es-tu ? ton nom ? (5 questions)
  CALC      — calculs exacts par les ondes (13 : négatifs, décimaux,
              typos x/*, virgule française)
  MEDICAL   — définitions du corpus (12 : + fièvre, convulsions
              fébriles, gastro, covid)
  CONDUITE  — conduites d'urgence du corpus (7 : AVC, infarctus,
              appendicite, dengue, covid, rhume, gastro)
  FAIT      — concepts appris par résonance (4 questions)
  REFUS     — hors domaine : refus calibré (9 : + anglais)

Critère : 100 % — chaque question doit produire le type attendu.
Les échecs sont corrigés jusqu'à passage complet.
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pont_hybride import PontHybride

# ══════════════════════════════════════════════════════════════════
# LE PROTOCOLE — 50 questions pré-enregistrées
# ══════════════════════════════════════════════════════════════════
TESTS = [
    # ── IDENTITÉ (5) ──
    ("qui es-tu ?",                        "IDENTITE"),
    ("ton nom ?",                          "IDENTITE"),
    ("qu'est-ce que tu es ?",              "IDENTITE"),
    ("comment tu t'appelles ?",            "IDENTITE"),
    ("what are you ?",                     "IDENTITE"),
    # ── CALCULS (13) ──
    ("7 × 8",                              "CALC"),
    ("12 + 34",                            "CALC"),
    ("3,5 ÷ 0,5",                          "CALC"),
    ("100 - 37",                           "CALC"),
    ("6,5 × 4",                            "CALC"),
    ("0,5 + 0,25",                         "CALC"),
    ("-3 + 8",                             "CALC"),
    ("12 × 12",                            "CALC"),
    ("7 ÷ 2",                              "CALC"),
    ("2,5 × 2,5",                          "CALC"),
    ("8x8",                                "CALC"),   # typo x sans espaces
    ("-12 × -2",                           "CALC"),   # négatif × négatif
    ("0,1 × 0,1",                          "CALC"),   # décimaux → 0,01
    # ── MÉDICAL (12) ──
    ("c'est quoi le diabète ?",            "MEDICAL"),
    ("c'est quoi l'hypertension ?",        "MEDICAL"),
    ("c'est quoi l'asthme ?",              "MEDICAL"),
    ("c'est quoi l'épilepsie ?",           "MEDICAL"),
    ("c'est quoi la drépanocytose ?",      "MEDICAL"),
    ("c'est quoi l'insuffisance cardiaque ?", "MEDICAL"),
    ("c'est quoi le paludisme ?",          "MEDICAL"),
    ("qu'est-ce que le diabète de type 2 ?", "MEDICAL"),
    ("c'est quoi la fièvre ?",             "MEDICAL"),
    ("c'est quoi des convulsions fébriles ?", "MEDICAL"),
    ("c'est quoi une gastro ?",            "MEDICAL"),
    ("c'est quoi le covid ?",              "MEDICAL"),
    # ── CONDUITES D'URGENCE (7) ──
    ("que faire en cas d'avc ?",           "CONDUITE"),
    ("que faire si j'ai un infarctus ?",   "CONDUITE"),
    ("conduite à tenir pour une appendicite ?", "CONDUITE"),
    ("que faire en cas de dengue ?",       "CONDUITE"),
    ("en cas de covid, que faire ?",       "CONDUITE"),
    ("que faire si j'ai un rhume ?",       "CONDUITE"),
    ("que faire pour une gastro ?",        "CONDUITE"),
    # ── FAITS APPRIS (4) ──
    ("chat",                               "FAIT"),
    ("lumière",                            "FAIT"),
    ("eau",                                "FAIT"),
    ("amour",                              "FAIT"),
    # ── REFUS HORS DOMAINE (9) ──
    ("quasar",                             "REFUS"),
    ("quelle est la météo à Paris ?",      "REFUS"),
    ("donne-moi une recette de couscous",  "REFUS"),
    ("qui a gagné le match hier ?",        "REFUS"),
    ("explique la cryptomonnaie",          "REFUS"),
    ("raconte une blague",                 "REFUS"),
    ("c'est quoi la philosophie ?",        "REFUS"),
    ("parle-moi de politique",             "REFUS"),
    ("what is 7 + 8 ?",                    "REFUS"),  # l'anglais : refus honnête
]

# ══════════════════════════════════════════════════════════════════
# PROTOCOLE PARTAGÉ — le noyau mobile (node) exécute la même liste
# ══════════════════════════════════════════════════════════════════
_PROTOCOLE_PATH = os.path.join("data", "benchmarks", "protocole_ka.json")


def _dumper_protocole():
    os.makedirs(os.path.dirname(_PROTOCOLE_PATH), exist_ok=True)
    with open(_PROTOCOLE_PATH, "w", encoding="utf-8") as f:
        json.dump(TESTS, f, ensure_ascii=False, indent=1)


# ══════════════════════════════════════════════════════════════════
# EXÉCUTION
# ══════════════════════════════════════════════════════════════════
def executer(modele=None, avec_llm=False):
    pont = PontHybride(utiliser_ollama=avec_llm)
    resultats = []
    for question, attendu in TESTS:
        r = pont.traiter(question)
        ok = r["type"] == attendu
        resultats.append({
            "question": question, "attendu": attendu, "obtenu": r["type"],
            "ok": ok, "reponse": r["response"][:60], "audit": r["audit"],
        })
    return resultats


def rapport(resultats, titre):
    ok = sum(1 for r in resultats if r["ok"])
    total = len(resultats)
    print(f"\n{'═'*66}\n{titre}\n{'═'*66}")
    print(f"  RÉSULTAT : {ok}/{total}  {'✅' if ok == total else '❌'}")
    print(f"\n  {'Question':40s} {'Attendu':10s} {'Obtenu':10s} {'Statut'}")
    print("  " + "─" * 72)
    for r in resultats:
        mark = "✅" if r["ok"] else "❌"
        print(f"  {r['question'][:38]:40s} {r['attendu']:10s} {r['obtenu']:10s} {mark}")
    echecs = [r for r in resultats if not r["ok"]]
    if echecs:
        print(f"\n  ⚠️ {len(echecs)} ÉCHECS :")
        for r in echecs:
            print(f"    · « {r['question']} » → attendu {r['attendu']}, obtenu {r['obtenu']}")
    return ok == total


def main():
    print("=" * 66)
    print("SUITE DE TESTS KA HYBRIDE — protocole pré-enregistré")
    print("=" * 66)
    print(f"  {len(TESTS)} questions · 6 catégories · critère : 100 %")

    _dumper_protocole()
    print(f"  Protocole partagé : {_PROTOCOLE_PATH}")

    # 1. Serveur (sans LLM — déterministe)
    t0 = time.time()
    resultats = executer(avec_llm=False)
    dt = time.time() - t0
    print(f"\n  Mode : NOYAU SEUL (déterministe) — {dt:.1f}s")
    ok1 = rapport(resultats, "TEST 1 · PONT SERVEUR — NOYAU SEUL")

    # 2. Sauvegarde du rapport
    dep = {
        "protocole": f"{len(TESTS)} questions pré-enregistrées, critère 100 %",
        "resultats": resultats,
        "ok": sum(1 for r in resultats if r["ok"]),
        "total": len(resultats),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    p = os.path.join("data", "benchmarks", "tests_ka_hybride_report.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dep, f, indent=2, ensure_ascii=False)
    print(f"\nRapport : {p}")

    if not ok1:
        print("\n❌ SUITE NON PASSÉE — corriger les échecs avant validation.")
        sys.exit(1)
    print("\n✅ SUITE PASSÉE — le pont serveur est validé sur 50 questions.")
    print("   → Exécuter aussi : node test_mobile_kernel.js (noyau mobile)")


if __name__ == "__main__":
    main()
