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


# ══════════════════════════════════════════════════════════════════
# STYLE VOCAL — les réponses doivent être lisibles par un synthétiseur
# ══════════════════════════════════════════════════════════════════
TESTS_VOCAL = [
    ("7 × 8",                    "CALC"),      # phrase modèle conversationnelle
    ("c'est quoi le diabète ?",  "MEDICAL"),   # ≥, g/L, mmol/L, %, HbA1c
    ("que faire en cas d'avc ?", "CONDUITE"),  # ⚠️, —, URGENCE VITALE
    ("chat",                     "FAIT"),      # phrase modèle conversationnelle
    ("quasar",                   "REFUS"),     # refus honnête sans « — »
    ("qui es-tu ?",              "IDENTITE"),  # (Knowledge Amplifier), « — »
]

# Symboles qu'aucun synthétiseur ne doit recevoir (style vocal)
_SYMBOLES_NON_PARLES = ["—", "–", "→", "≥", "≤", "±", "⚠", "✅", "❌", "(", ")", "**"]


def executer_vocal():
    """Le protocole vocal : type correct + audit ok + zéro symbole non parlé."""
    pont = PontHybride(utiliser_ollama=False)
    resultats = []
    for question, attendu in TESTS_VOCAL:
        r = pont.traiter(question, style="vocal")
        mauvais = [s for s in _SYMBOLES_NON_PARLES if s in r["response"]]
        ok = (r["type"] == attendu and r["audit"] is True and not mauvais)
        resultats.append({
            "question": question, "attendu": attendu, "obtenu": r["type"],
            "ok": ok, "reponse": r["response"][:80], "audit": r["audit"],
            "symboles_restants": mauvais,
        })
    return resultats


_CORPUS_VOCAL = ("⚠️ URGENCE VITALE — Appeler le 15 IMMÉDIATEMENT. "
                 "Glycémie ≥ 1,26 g/L (7,0 mmol/L) ; HbA1c ≥ 6,5 % ; "
                 "pression 140/90 mmHg ; 40-60 insufflations/min ; 2x/j ; "
                 "fièvre > 38,5 °C. → Hospitalisation. 24h/24, 7j/7.")


def verifier_vocalisation():
    """Les symboles RÉELS du corpus deviennent des mots parlés."""
    from pont_hybride import vocaliser
    v = vocaliser(_CORPUS_VOCAL)
    exigences = [
        "supérieur ou égal à", "grammes par litre", "millimoles par litre",
        "hémoglobine glyquée", "pour cent", "sur 90", "millimètres de mercure",
        "de 40 à 60", "fois par jour", "plus de 38,5", "degrés",
        "24 heures sur 24", "7 jours sur 7", "Hospitalisation",
    ]
    manquants = [e for e in exigences if e not in v]
    restants = [s for s in ["≥", "→", "—", "⚠", "(", ")", "g/L", "%", "/", "°", "**"]
                if s in v]
    return v, manquants, restants


# ══════════════════════════════════════════════════════════════════
# LES STYLES DU PHRASEUR INTERNE (étage 3) — déterminisme + contraintes
# ══════════════════════════════════════════════════════════════════
STYLES_A_TESTER = ["conversationnel", "vocal", "bref", "pédagogique"]


def executer_styles():
    """Les 4 styles × le protocole vocal : type + audit + contraintes de style."""
    pont = PontHybride(utiliser_ollama=False)
    resultats, reps = [], {}
    for style in STYLES_A_TESTER:
        for question, attendu in TESTS_VOCAL:
            r = pont.traiter(question, style=style)
            reps[(style, question)] = r["response"]
            mauvais = ([s for s in _SYMBOLES_NON_PARLES if s in r["response"]]
                       if style == "vocal" else [])
            ok = r["type"] == attendu and r["audit"] is True and not mauvais
            resultats.append({
                "style": style, "question": question, "attendu": attendu,
                "obtenu": r["type"], "ok": ok, "reponse": r["response"][:70],
                "symboles_restants": mauvais,
            })
    # Contraintes croisées — la spécialisation de chaque style
    q_med, q_calc, q_refus = "c'est quoi le diabète ?", "7 × 8", "quasar"
    contraintes = [
        ("MEDICAL bref = corpus exact (pas de résumé)",
         reps[("bref", q_med)] == reps[("conversationnel", q_med)]),
        ("MEDICAL pédagogique = corpus exact",
         reps[("pédagogique", q_med)] == reps[("conversationnel", q_med)]),
        ("MEDICAL vocal = symboles devenus mots parlés",
         "supérieur ou égal à" in reps[("vocal", q_med)]),
        ("CALC bref plus court que conversationnel",
         len(reps[("bref", q_calc)]) < len(reps[("conversationnel", q_calc)])),
        ("CALC pédagogique plus long que bref",
         len(reps[("pédagogique", q_calc)]) > len(reps[("bref", q_calc)])),
        ("REFUS bref plus court que conversationnel",
         len(reps[("bref", q_refus)]) < len(reps[("conversationnel", q_refus)])),
    ]
    # Déterminisme total : la même entrée → la même sortie
    r1 = pont.traiter(q_calc, style="bref")
    r2 = pont.traiter(q_calc, style="bref")
    contraintes.append(("Déterminisme : même entrée → même sortie",
                        r1["response"] == r2["response"]))
    return resultats, contraintes


def verifier_configuration_externe():
    """État honnête de la chaîne de fournisseurs (aucun appel réseau)."""
    try:
        from pont_phraseur_externe import PhraseurExterne
        p = PhraseurExterne()
        noms = [n for n, _ in p.fournisseurs]
        return noms
    except Exception as e:
        return [f"erreur: {e}"]


def verifier_style_elegan_deterministe():
    """Sans LLM, le style élégant = conversationnel (zéro cloud, déterministe).
    L'élégance par polish LLM est testée dans le test global (avec la vraie
    chaîne). Ici on vérifie la garantie de repli."""
    pont = PontHybride(utiliser_ollama=False)
    if "élégant" not in pont.STYLES:
        return False, "style élégant absent de STYLES"
    for q in ["7 × 8", "chat", "quasar", "c'est quoi le diabète ?"]:
        r1 = pont.traiter(q, style="élégant")
        r2 = pont.traiter(q, style="conversationnel")
        if r1["response"] != r2["response"]:
            return False, f"« {q} » : élégant ≠ conversationnel sans LLM"
    return True, ""


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

    # 2. STYLE VOCAL — ce que lira le synthétiseur
    t0 = time.time()
    resultats_vocal = executer_vocal()
    dt = time.time() - t0
    print(f"\n  Mode : STYLE VOCAL (zéro symbole non parlé) — {dt:.1f}s")
    ok2 = rapport(resultats_vocal, "TEST 2 · STYLE VOCAL — LISIBLE À VOIX HAUTE")

    # 3. Vocalisation pure : les symboles du corpus deviennent des mots
    v, manquants, restants = verifier_vocalisation()
    ok3 = not manquants and not restants
    print(f"\n  Vocalisation du corpus : {'✅' if ok3 else '❌'}")
    print(f"    → {v[:150]}…")
    if manquants:
        print(f"    ⚠️ lectures manquantes : {manquants}")
    if restants:
        print(f"    ⚠️ symboles restants : {restants}")

    # 4. LES STYLES DU PHRASEUR INTERNE (étage 3)
    t0 = time.time()
    resultats_styles, contraintes = executer_styles()
    dt = time.time() - t0
    print(f"\n  Mode : 4 STYLES × 6 questions (PhraseurInterne) — {dt:.1f}s")
    ok4 = rapport(resultats_styles, "TEST 3 · STYLES DU PHRASEUR INTERNE")
    ok_contraintes = sum(1 for _, c in contraintes if c)
    print(f"\n  Contraintes de style : {ok_contraintes}/{len(contraintes)}")
    for nom, c in contraintes:
        print(f"    {'✅' if c else '❌'} {nom}")
    ok4 = ok4 and ok_contraintes == len(contraintes)

    # 5. Style ÉLÉGANT sans LLM = conversationnel (garantie déterministe)
    ok_elegan, detail_elegan = verifier_style_elegan_deterministe()
    print(f"\n  Élégant sans LLM = conversationnel : {'✅' if ok_elegan else '❌ ' + detail_elegan}")

    # 6. État de la chaîne de fournisseurs (aucun appel réseau)
    fournisseurs = verifier_configuration_externe()
    print(f"\n  Chaîne de fournisseurs détectée : {fournisseurs or 'aucun → PhraseurInterne'}")

    # 7. Sauvegarde du rapport
    dep = {
        "protocole": f"{len(TESTS)} questions pré-enregistrées, critère 100 %",
        "resultats": resultats,
        "ok": sum(1 for r in resultats if r["ok"]),
        "total": len(resultats),
        "fournisseurs": fournisseurs,
        "style_elegan_sans_llm": ok_elegan,
        "vocal": {
            "ok": sum(1 for r in resultats_vocal if r["ok"]),
            "total": len(resultats_vocal),
            "resultats": resultats_vocal,
            "corpus_vocal_ok": ok3,
        },
        "styles": {
            "ok": sum(1 for r in resultats_styles if r["ok"]),
            "total": len(resultats_styles),
            "resultats": resultats_styles,
            "contraintes": [{"nom": n, "ok": c} for n, c in contraintes],
        },
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    p = os.path.join("data", "benchmarks", "tests_ka_hybride_report.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dep, f, indent=2, ensure_ascii=False)
    print(f"\nRapport : {p}")

    if not (ok1 and ok2 and ok3 and ok4 and ok_elegan):
        print("\n❌ SUITE NON PASSÉE — corriger les échecs avant validation.")
        sys.exit(1)
    print("\n✅ SUITE PASSÉE — 50 questions + style vocal + 4 styles + élégant déterministe.")
    print("   → Exécuter aussi : node test_mobile_kernel.js (noyau mobile)")


if __name__ == "__main__":
    main()
