#!/usr/bin/env python3
"""generer_dataset_phraseur.py — LE DATASET D'ENTRAÎNEMENT DU PHRASEUR
=====================================================================
Correct PAR CONSTRUCTION : le noyau décide (mémoire + émulation), le
PhraseurInterne (audité par design) fournit la cible. Le modèle fine-tuné
n'apprend QUE des paires <CORE>+style → phrase que le système a déjà
validées — zéro invention possible dans les données.

Format d'entrée (identique à l'inférence, via construire_prompt) :
  PROMPT_PHRASEUR + <CORE> … </CORE> <HIST> question </HIST> + bloc STYLE
Format de sortie : la phrase seule (continuation, pas de chat template).

~2000 exemples : protocole 50 × 4 styles · arithmétique générée × 4 styles
· concepts × 4 · refus × 4 · identité × 4 · corpus médical × 4 (le modèle
apprend à CITER le corpus, jamais à le reformuler).
Format compact : <CORE> … </CORE> <HIST> … </HIST> <STYLE> … </STYLE>
"""
import json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pont_hybride import NoyauHybride
from pont_phraseur_interne import PhraseurInterne, STYLES

_ICI = os.path.dirname(os.path.abspath(__file__))
_SORTIE = os.path.join(_ICI, "data", "phraseur")
_QUESTION_PROTOCOLE = [
    ("qui es-tu ?", "IDENTITE"), ("ton nom ?", "IDENTITE"),
    ("qu'est-ce que tu es ?", "IDENTITE"), ("comment tu t'appelles ?", "IDENTITE"),
    ("what are you ?", "IDENTITE"),
    ("7 × 8", "CALC"), ("12 + 34", "CALC"), ("3,5 ÷ 0,5", "CALC"),
    ("100 - 37", "CALC"), ("6,5 × 4", "CALC"), ("0,5 + 0,25", "CALC"),
    ("-3 + 8", "CALC"), ("12 × 12", "CALC"), ("7 ÷ 2", "CALC"),
    ("2,5 × 2,5", "CALC"), ("8x8", "CALC"), ("-12 × -2", "CALC"),
    ("0,1 × 0,1", "CALC"),
    ("c'est quoi le diabète ?", "MEDICAL"),
    ("c'est quoi l'hypertension ?", "MEDICAL"),
    ("c'est quoi l'asthme ?", "MEDICAL"), ("c'est quoi l'épilepsie ?", "MEDICAL"),
    ("c'est quoi la drépanocytose ?", "MEDICAL"),
    ("c'est quoi l'insuffisance cardiaque ?", "MEDICAL"),
    ("c'est quoi le paludisme ?", "MEDICAL"),
    ("qu'est-ce que le diabète de type 2 ?", "MEDICAL"),
    ("c'est quoi la fièvre ?", "MEDICAL"),
    ("c'est quoi des convulsions fébriles ?", "MEDICAL"),
    ("c'est quoi une gastro ?", "MEDICAL"), ("c'est quoi le covid ?", "MEDICAL"),
    ("que faire en cas d'avc ?", "CONDUITE"),
    ("que faire si j'ai un infarctus ?", "CONDUITE"),
    ("conduite à tenir pour une appendicite ?", "CONDUITE"),
    ("que faire en cas de dengue ?", "CONDUITE"),
    ("en cas de covid, que faire ?", "CONDUITE"),
    ("que faire si j'ai un rhume ?", "CONDUITE"),
    ("que faire pour une gastro ?", "CONDUITE"),
    ("chat", "FAIT"), ("lumière", "FAIT"), ("eau", "FAIT"), ("amour", "FAIT"),
    ("quasar", "REFUS"), ("quelle est la météo à Paris ?", "REFUS"),
    ("donne-moi une recette de couscous", "REFUS"),
    ("qui a gagné le match hier ?", "REFUS"),
    ("explique la cryptomonnaie", "REFUS"), ("raconte une blague", "REFUS"),
    ("c'est quoi la philosophie ?", "REFUS"), ("parle-moi de politique", "REFUS"),
    ("what is 7 + 8 ?", "REFUS"),
]

_REFUS_EXTRA = [
    "prédiction astrologique du jour", "combien de kilomètres jusqu'à la lune en marchant ?",
    "écris une chanson d'amour", "traduis ce texte en chinois",
    "combien gagne le président ?", "qui va gagner la prochaine élection ?",
    "donne-moi le code de la carte", "raconte l'histoire de la Tour Eiffel",
    "quelle est la recette du meilleur gâteau ?", "parle-moi de tes sentiments",
    "combien de temps pour apprendre le piano ?", "fais mes devoirs de maths",
]
_IDENTITE_EXTRA = [
    "qui es-tu exactement ?", "tu es quoi ?", "présente-toi", "c'est quoi KA ?",
    "tu es une IA ?", "qu'est-ce que tu sais faire ?",
]
_CONCEPTS_EXTRA = ["feu", "vent", "terre", "ciel", "étoile", "lune", "soleil",
                   "pluie", "forêt", "océan", "montagne", "rivière", "fleur",
                   "arbre", "poisson", "guérison", "paix", "vérité", "savoir",
                   "harmonie", "respiration", "cœur", "hiver", "printemps"]
_OP = ["+", "-", "×", "÷"]
_OP_MOTS = ["+", "moins", "fois", "divisé par", "+"]


def _arithmetique(rng, n):
    """n expressions pures parsables par le noyau (formats « a op b »)."""
    qs = []
    for _ in range(n):
        op = rng.choice(_OP)
        if op == "÷":
            b = rng.randint(1, 12)
            a = rng.randint(1, 50) * b
        else:
            a = rng.choice([rng.randint(-99, 99), round(rng.uniform(-20, 20), 2)])
            b = rng.choice([rng.randint(-99, 99), round(rng.uniform(-20, 20), 2)])
        a_s = str(a).replace(".", ",")
        b_s = str(b).replace(".", ",")
        # Formes que calculer() parse (espace, sans espace, x minuscule)
        forme = rng.choice([f"{a_s} {op} {b_s}", f"{a_s}{op}{b_s}",
                            f"{a_s}x{b_s}" if op == "×" else f"{a_s} {op} {b_s}"])
        qs.append(forme)
    return qs


def _prompt_ft(core, question, style):
    """Format COMPACT du phraseur fine-tuné : le modèle est spécialisé, il
    n'a pas besoin des 6 règles — juste <CORE> + <HIST> + <STYLE> (~40 tokens
    au lieu de 250 : indispensable sur une machine à 5,9 Go de RAM)."""
    contenu = _contenu(core)
    return (f"<CORE> {contenu} </CORE> "
            f"<HIST> {question.replace(chr(34), chr(39))} </HIST> "
            f"<STYLE> {style} </STYLE>")


def main():
    rng = random.Random(1337)
    noyau = NoyauHybride()
    for c in (["chat", "chien", "oiseau", "lumière", "amour", "eau", "musique",
               "santé"] + _CONCEPTS_EXTRA):
        noyau.apprendre(c)
    phraseur = PhraseurInterne()

    questions = (list(_QUESTION_PROTOCOLE) +
                 [(q, "CALC") for q in _arithmetique(rng, 500)] +
                 [(q, "REFUS") for q in _REFUS_EXTRA] +
                 [(q, "IDENTITE") for q in _IDENTITE_EXTRA] +
                 [(c, "FAIT") for c in _CONCEPTS_EXTRA] +
                 [(c, "FAIT") for c in noyau.concepts.keys()])
    print(f"Questions générées : {len(questions)}")

    exemples, sautes = [], 0
    for question, attendu in questions:
        core = noyau.repondre(question)
        if core["type"] != attendu:
            sautes += 1
            continue
        for style in STYLES:
            cible = phraseur.phraser(core, style)
            prompt = _prompt_ft(core, question, style)
            exemples.append({"prompt": prompt, "response": cible,
                             "type": core["type"], "style": style,
                             "question": question})
    rng.shuffle(exemples)
    n_val = max(1, len(exemples) // 20)
    train, val = exemples[n_val:], exemples[:n_val]
    os.makedirs(_SORTIE, exist_ok=True)
    for nom, liste in [("dataset_train.jsonl", train), ("dataset_val.jsonl", val)]:
        with open(os.path.join(_SORTIE, nom), "w", encoding="utf-8") as f:
            for e in liste:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"Exemples : {len(exemples)} (train {len(train)} · val {len(val)})")
    print(f"Types : { {t: sum(1 for e in exemples if e['type']==t) for t in set(e['type'] for e in exemples)} }")
    print(f"Question non routée : {sautes} · Sortie : {_SORTIE}")
    print("\nExemple :")
    print(exemples[0]["prompt"][:200].replace("\n", " ¶ ") + "\n  → " + exemples[0]["response"])


def _contenu(core):
    """<CORE> texte minimal (sans dépendre de NoyauHybride._contenu_core)."""
    if core["type"] == "CALC":
        v = core["valeur"]
        return str(int(v)) if v == int(v) else f"{v:.6f}".rstrip("0").rstrip(".")
    if core["type"] == "FAIT":
        return f"FAIT: {core['concept']}"
    if core["type"] in ("MEDICAL", "CONDUITE"):
        return "FAIT: " + core["valeur"]
    if core["type"] == "IDENTITE":
        return "FAIT: KA est une IA harmonique — zéro hallucination"
    return "REFUS"


if __name__ == "__main__":
    main()
