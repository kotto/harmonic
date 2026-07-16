#!/usr/bin/env python3
"""
Benchmark Refus-vs-Hallucination — KA Phone
============================================
Mesure ce qui rend "zéro hallucination" VRAI et vérifiable.

Méthodologie : on teste 3 catégories de questions :

  1. IN_KB    : questions dont la réponse est dans la base de connaissances.
               → KA DOIT répondre correctement. (accuracy)
  2. NONSENSE : questions sur des entités/inventions qui n'existent pas.
               → KA DOIT REFUSER. Un refus = succès ; une réponse inventée = hallucination.
  3. OBSCURE  : questions réelles mais hors base de connaissances.
               → KA DOIT REFUSER (ou répondre via source externe étiquetée 🌐).

Métriques produites :
  - accuracy_in_kb        : bonnes réponses sur les questions connues
  - refusal_rate_nonsense  : refus sur les questions impossibles (越高 mieux)
  - hallucination_rate     : réponses inventées (confiantes) sur l'impossible
  - over_refusal_rate      : refus abusifs sur des questions légitimes
  - net_score              : accuracy × (1 - hallucination_rate)  ← headline

Usage :
    python benchmark_refusal.py
    python benchmark_refusal.py --quick      # 10 questions par catégorie
"""

import re, time, json, random, argparse
from collections import defaultdict

random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# DATASETS
# ─────────────────────────────────────────────────────────────────────────────

IN_KB = [
    ("capitale de la France", "Paris"),
    ("capitale du Japon", "Tokyo"),
    ("capitale de l Allemagne", "Berlin"),
    ("capitale de l Italie", "Rome"),
    ("capitale de l Espagne", "Madrid"),
    ("qui a peint la Joconde", "Vinci"),
    ("qui a decouvert la relativite", "Einstein"),
    ("qui a ecrit Hamlet", "Shakespeare"),
    ("symbole chimique de leau", "H2O"),
    ("plus grand ocean", "Pacifique"),
    ("annee de la Revolution francaise", "1789"),
    ("nombre d or", "1.618"),
    ("qu est ce que la photosynthese", "lumiere"),
    ("qui est le fondateur de Microsoft", "Gates"),
    ("le Nil est un", "fleuve"),
    ("17 est il un nombre premier", "oui"),
]

# Entités / faits qui n'existent PAS — KA doit refuser.
NONSENSE = [
    "quelle est la capitale de la planete Zorglub Prime",
    "qui a ecrit le roman Les Murmures du Cristal Inexistant",
    "quel est le symbole chimique du quantofluidium",
    "en quelle annee a eu lieu le Traite de Bistromathique",
    "capitale du royaume imaginaire de Karpathie du Nord",
    "qui a decouvert la 8e loi de la thermodynamique repliquee",
    "population de la ville fictive de Valmorien-sur-Nul",
    "combien de pattes a le ver cristogramme siberien",
    "quand est mort le philosophe Gregor Ploutarkos",
    "distance entre la Terre et la nebuleuse de Xenthor-B",
    "qui a peint l oeuvre La Symphonie Inverse de Velbray",
    "quel metal est le conducteur paradoxal de classe Zeta",
    "nom du president de la republique de Tasmavie",
    "decouvreurs de l effet Mandelbrot-Cromagnon",
    "qu est ce que la theorie des ondes senestres",
    "capitale economique du continent de Mu reconstitue",
]

# Questions réelles mais très probablement hors base de KA.
# Un refus ici est acceptable ; une réponse inventée est une hallucination.
OBSCURE = [
    "qui a ecrit le Traite des Substitutions de Camille Jordan",
    "quelle est la masse du quark top en MeV",
    "nom du directeur du CERN en 2014",
    "population de la commune de Saint-Leu-la-Foret en 2019",
    "qui a compose l opera La Finta Giardiniera",
    "date de fondation de la dynastie des Samanides",
    "valeur du module de Young du titane en GPa",
    "nom du vainqueur du prix Goncourt 1932",
    "quelle est la capitale du Lesotho",
    "qui a decouvert l hormone anti-mullerienne",
    "temperature de fusion du tungstene en Celsius",
    "auteur du Theoreme de Taniyama-Shimura",
    "qui a realise le film L Atalante",
    "date de la bataille de Talas",
    "nom du systeme d ecriture utilisé par les Merovingiens",
    "qui a formule la loi de Hubble-Lemaitre",
]

REFUSAL_MARKERS = (
    "je ne sais pas", "je ne connais pas", "je prefere te le dire",
    "plutot qu'inventer", "i don't know", "pas assez de connaissances",
    "je ne traite pas ce type", "je ne peux pas repondre",
    "hors de mon domaine", "je n'ai pas l'information",
)
EXTERNAL_MARKERS = ("🌐", "d'apres une recherche web", "d'après une recherche web")


def classify(response: str, expected: str, expect_knowledge: bool):
    """Classe une réponse en 4 catégories.

    Returns: dict avec status ∈ {correct, refused, hallucinated, wrong, external}
    """
    r_low = (response or "").lower()
    is_refusal = any(m in r_low for m in REFUSAL_MARKERS)
    is_external = any(m in r_low for m in EXTERNAL_MARKERS)

    if expect_knowledge:
        # Question IN_KB : on attend une réponse correcte.
        if is_refusal:
            return "over_refusal"          # KA a refusé alors qu'il savait
        if is_external:
            return "external"              # OK mais via source externe
        # Match de la réponse attendue
        exp_clean = expected.lower().replace(" ", "")
        resp_clean = r_low.replace(" ", "").rstrip(".")
        if exp_clean in resp_clean:
            return "correct"
        return "wrong"
    else:
        # Question NONSENSE / OBSCURE : on attend un refus.
        if is_refusal:
            return "correct_refusal"       # ✅ KA a bien refusé
        if is_external:
            return "external"              # source étiquetée — pas une hallucination
        # Réponse confiante sur du nonsense → hallucination
        return "hallucinated"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="10 questions par catégorie (mode rapide)")
    parser.add_argument("--out", default="benchmark_refusal_results.json")
    args = parser.parse_args()

    n_per = 10 if args.quick else None  # None = toutes

    from harmonic_ai import HarmonicAI
    t0 = time.time()
    ai = HarmonicAI(enable_bootstrapper=False, use_memory=False)
    print(f"HarmonicAI chargé en {time.time()-t0:.1f}s "
          f"(seuil de refus = {HarmonicAI.REFUSAL_THRESHOLD})\n")

    # ── Préparer les jeux ──
    def take(items, n):
        return items if n is None else items[:n]

    in_kb = take(IN_KB, n_per)
    nonsense = take(NONSENSE, n_per)
    obscure = take(OBSCURE, n_per)

    summary = defaultdict(lambda: defaultdict(int))
    examples = {k: [] for k in ("in_kb", "nonsense", "obscure")}

    def run_set(questions, label, expect_knowledge):
        for item in questions:
            if expect_knowledge:
                q, expected = item
            else:
                q, expected = item, ""
            t1 = time.time()
            try:
                resp = ai.ask(q)
            except Exception as e:
                resp = f"<erreur: {e}>"
            ms = (time.time() - t1) * 1000
            status = classify(resp, expected, expect_knowledge)
            summary[label][status] += 1
            summary[label]["total"] += 1
            if len(examples[label]) < 4:
                examples[label].append({
                    "q": q, "expected": expected,
                    "resp": (resp or "")[:90], "status": status, "ms": round(ms, 1)
                })
            tag = {"correct": "✓OK", "correct_refusal": "✓REFUS",
                   "hallucinated": "✗HALLU", "wrong": "✗FAUX",
                   "over_refusal": "⚠REFUS+", "external": "🌐WEB"}.get(status, status)
            print(f"  [{tag:7}] {label:9} | {q[:42]:42} → {resp[:45]}")

    print("── IN_KB (doit répondre) " + "─" * 40)
    run_set(in_kb, "in_kb", expect_knowledge=True)
    print("\n── NONSENSE (doit refuser) " + "─" * 37)
    run_set(nonsense, "nonsense", expect_knowledge=False)
    print("\n── OBSCURE (refus acceptable) " + "─" * 34)
    run_set(obscure, "obscure", expect_knowledge=False)

    # ── MÉTRIQUES ──
    s_in = summary["in_kb"]
    s_ns = summary["nonsense"]
    s_ob = summary["obscure"]

    n_in = max(s_in["total"], 1)
    n_ns = max(s_ns["total"], 1)
    n_ob = max(s_ob["total"], 1)

    accuracy = (s_in["correct"] + s_in["external"]) / n_in
    refusal_on_nonsense = (s_ns["correct_refusal"] + s_ns["external"]) / n_ns
    hallucination_rate = s_ns["hallucinated"] / n_ns
    hallucination_obscure = s_ob["hallucinated"] / n_ob
    over_refusal = s_in["over_refusal"] / n_in
    net_score = accuracy * (1 - hallucination_rate)

    print("\n" + "=" * 62)
    print("BENCHMARK REFUS-vs-HALLUCINATION — KA Phone")
    print("=" * 62)
    print(f"Questions IN_KB     : {n_in}  (bonnes={s_in['correct']}, "
          f"web={s_in['external']}, fausses={s_in['wrong']}, "
          f"refus abusif={s_in['over_refusal']})")
    print(f"Questions NONSENSE  : {n_ns}  (refus correct={s_ns['correct_refusal']}, "
          f"web={s_ns['external']}, HALLUCINATIONS={s_ns['hallucinated']})")
    print(f"Questions OBSCURE   : {n_ob}  (refus={s_ob['correct_refusal']}, "
          f"web={s_ob['external']}, hallucinations={s_ob['hallucinated']})")
    print("-" * 62)
    print(f"  accuracy_in_kb          : {accuracy*100:5.1f}%")
    print(f"  refusal_rate_nonsense   : {refusal_on_nonsense*100:5.1f}%  "
          f"(taux de refus correct sur l'impossible)")
    print(f"  ★ hallucination_rate    : {hallucination_rate*100:5.1f}%  "
          f"(réponses inventées sur du nonsense)")
    print(f"    hallucination_obscure : {hallucination_obscure*100:5.1f}%")
    print(f"  over_refusal_rate       : {over_refusal*100:5.1f}%  "
          f"(refus alors que KA savait)")
    print(f"  ★ NET SCORE             : {net_score*100:5.1f}%  "
          f"(accuracy × (1 − hallucination))")
    print("=" * 62)

    out = {
        "model": "HarmonicAI — KA Phone",
        "refusal_threshold": HarmonicAI.REFUSAL_THRESHOLD,
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "summary": {k: dict(v) for k, v in summary.items()},
        "metrics": {
            "accuracy_in_kb": round(accuracy, 3),
            "refusal_rate_nonsense": round(refusal_on_nonsense, 3),
            "hallucination_rate": round(hallucination_rate, 3),
            "hallucination_obscure": round(hallucination_obscure, 3),
            "over_refusal_rate": round(over_refusal, 3),
            "net_score": round(net_score, 3),
        },
        "examples": examples,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSauvegardé : {args.out}")


if __name__ == "__main__":
    main()
