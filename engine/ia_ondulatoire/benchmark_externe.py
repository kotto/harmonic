# -*- coding: utf-8 -*-
"""
benchmark_externe.py — P3.1 ÉCHANTILLONS DE BENCHMARKS EXTERNES
================================================================
Premiers chiffres du moteur face au MONDE (aucun ajustement, scores bruts) :

  · MMLU-fr style : 30 questions à choix multiples (raisonnement, logique,
    arithmétique, sciences) — construites maison, format MMLU (4 choix)
  · MATH : 10 problèmes de type olympiade (réponses exactes connues)
  · HumanEval : 5 exercices de code Python (from data/benchmarks/HumanEval.jsonl.gz)

Protocole : chaque item passe par le cerveau complet (ia.poser) — le
comportement REFUS (honnête, calibré P1.2) est compté à part : l'IA ne
devine pas. Métriques par benchmark : correct / faux / refus.

Usage : python benchmark_externe.py
"""

import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cerveau import IaOndulatoire       # noqa: E402

DOSSIER = os.path.dirname(os.path.abspath(__file__))

# ────────────────────────────────────────────────────────────────────────
# MMLU-fr style — 30 questions à choix multiples (vérité terrain)
# ────────────────────────────────────────────────────────────────────────
MMLU_FR = [
    ("Si tous les A sont des B, et qu'aucun C n'est un B, alors :",
     ["tous les C sont des A", "aucun C n'est un A", "tous les A sont des C",
      "certains C sont des A"], 1),
    ("Un train parcourt 240 km en 3 heures. Sa vitesse moyenne est :",
     ["60 km/h", "70 km/h", "80 km/h", "90 km/h"], 2),
    ("Quelle est la prochaine valeur de la suite 2, 6, 12, 20, 30, … ?",
     ["40", "42", "44", "46"], 1),
    ("Si x + 2y = 10 et x − y = 1, alors y vaut :",
     ["2", "3", "4", "5"], 1),
    ("Un article coûte 80 € avec une remise de 25 %. Son prix initial est :",
     ["100 €", "105 €", "106,67 €", "120 €"], 2),
    ("La somme des angles d'un pentagone est :",
     ["360°", "450°", "540°", "720°"], 2),
    ("Si 5 machines produisent 5 objets en 5 minutes, 100 machines produisent "
     "100 objets en :", ["5 minutes", "20 minutes", "100 minutes", "500 minutes"], 0),
    ("Un nombre premier est divisible par :",
     ["1 et lui-même uniquement", "2 et 3 uniquement", "tous les entiers",
      "aucun entier"], 0),
    ("7⁰ vaut :", ["0", "1", "7", "indéfini"], 1),
    ("Le plus petit entier strictement positif divisible par 2, 3 et 4 est :",
     ["6", "8", "12", "24"], 2),
    ("Si un carré a un périmètre de 20 cm, son aire est :",
     ["16 cm²", "20 cm²", "25 cm²", "40 cm²"], 2),
    ("2/3 + 1/6 vaut :", ["1/2", "3/9", "5/6", "3/6"], 2),
    ("Un père a 3 fois l'âge de son fils. Dans 12 ans, il aura 2 fois son âge. "
     "Le fils a :", ["10 ans", "12 ans", "14 ans", "16 ans"], 1),
    ("Lequel de ces nombres est un carré parfait ?",
     ["50", "64", "72", "84"], 1),
    ("Si une montre avance de 5 minutes par heure, en 6 heures elle avance de :",
     ["20 min", "25 min", "30 min", "35 min"], 2),
    ("Combien de diagonales possède un hexagone ?",
     ["6", "9", "12", "15"], 1),
    ("L'équation 2x − 6 = 0 a pour solution x = :",
     ["−3", "2", "3", "6"], 2),
    ("Un cycliste monte à 10 km/h et redescend à 30 km/h. Sur un aller-retour "
     "de 30 km (15 km chaque sens), sa vitesse moyenne est :",
     ["20 km/h", "15 km/h", "25 km/h", "18 km/h"], 1),
    ("Le 5e terme de la suite définie par u₁ = 1, uₙ₊₁ = 2·uₙ + 1 est :",
     ["15", "31", "17", "33"], 1),
    ("Si 3 cartons contiennent 48 bouteilles, 7 cartons en contiennent :",
     ["96", "104", "112", "120"], 2),
    ("Un angle droit mesure :", ["45°", "90°", "180°", "360°"], 1),
    ("Le produit de deux nombres impairs est :",
     ["toujours pair", "toujours impair", "parfois pair", "multiple de 4"], 1),
    ("0,25 × 0,4 vaut :", ["0,1", "0,01", "1", "10"], 0),
    ("Si un jardin rectangulaire fait 12 m sur 8 m, sa surface est :",
     ["40 m²", "80 m²", "96 m²", "100 m²"], 2),
    ("La moyenne de 12, 14, 16 et 18 est :",
     ["14", "15", "16", "17"], 1),
    ("Quel est le reste de la division de 47 par 5 ?",
     ["2", "3", "4", "5"], 0),
    ("Un robinet remplit un bassin de 120 L en 10 minutes. Le débit est :",
     ["10 L/min", "12 L/min", "15 L/min", "20 L/min"], 1),
    ("Le double de la moitié de 36 est :", ["9", "18", "36", "72"], 2),
    ("Si a = 2 et b = 3, alors a² + b² vaut :",
     ["10", "13", "25", "36"], 1),
    ("Une échelle de 5 m est appuyée contre un mur, le pied à 3 m du mur. "
     "Le sommet touche le mur à :", ["3 m", "4 m", "5 m", "6 m"], 1),
]

# ────────────────────────────────────────────────────────────────────────
# MATH — 10 problèmes de type olympiade (réponses exactes)
# ────────────────────────────────────────────────────────────────────────
MATH_FR = [
    ("La somme de deux nombres est 20 et leur produit est 96. Quelle est la "
     "plus grande valeur possible de l'un des deux nombres ?", 12),
    ("Un nombre à deux chiffres est tel que la somme de ses chiffres vaut 9 "
     "et qu'en inversant ses chiffres on obtient un nombre de 27 de moins. "
     "Quel est ce nombre ?", 63),
    ("Dans une classe, chaque élève serre la main de tous les autres. Il y a "
     "en tout 66 poignées de main. Combien y a-t-il d'élèves ?", 12),
    ("Un fermier a des poules et des lapins : 35 têtes et 94 pattes. Combien "
     "de lapins ?", 12),
    ("Le produit de trois entiers consécutifs est 210. Quelle est la somme "
     "de ces trois entiers ?", 18),
    ("Une horloge sonne 1 coup à 1h, 2 coups à 2h… Combien de coups sonne-t-elle "
     "entre minuit et midi (midi compris, minuit exclu) ?", 78),
    ("Un rectangle a un périmètre de 40 cm. Si on augmente sa longueur de 2 cm "
     "et sa largeur de 2 cm, son aire augmente de 44 cm². Quelle était l'aire "
     "initiale ?", 96),
    ("La somme de 100 entiers consécutifs à partir de 1 est 5050. Quelle est "
     "la somme des 100 premiers entiers pairs ?", 10100),
    ("Trois amis se partagent 45 billes. Le deuxième en a deux fois plus que le "
     "premier, le troisième trois fois plus que le premier. Combien le premier "
     "a-t-il de billes ?", 7.5),
    ("Un train de 200 m de long traverse un tunnel de 800 m à 72 km/h. Combien "
     "de secondes met-il pour traverser complètement le tunnel ?", 50),
]

# ────────────────────────────────────────────────────────────────────────
def charger_humaneval(n=5):
    with gzip.open(os.path.join(DOSSIER, "..", "data", "benchmarks",
                                "HumanEval.jsonl.gz"), "rt", encoding="utf-8") as f:
        items = [json.loads(l) for l in f if l.strip()]
    return items[:n]


def est_refus(texte):
    return ("je ne connais pas" in texte.lower()
            or "souviens-toi" in texte.lower())


def extraire_choix(texte):
    """Cherche A/B/C/D ou la réponse dans le texte."""
    t = texte.upper()
    for lettre in ("A", "B", "C", "D"):
        if re.search(rf"\b{lettre}\b", t):
            return "ABCD".index(lettre)
    return None


def extraire_nombre(texte):
    nums = re.findall(r"-?\d+(?:[.,]\d+)?", texte.replace(",", "."))
    return float(nums[-1]) if nums else None


print("=" * 70)
print("P3.1 BENCHMARKS EXTERNES — scores bruts, aucun ajustement")
print("=" * 70)
ia = IaOndulatoire(charger=False)

# ── MMLU-fr ────────────────────────────────────────────────────────────
print("\n[1] MMLU-fr style — 30 questions à choix multiples")
n_c, n_f, n_r = 0, 0, 0
for q, choix, bonne in MMLU_FR:
    r = ia.poser(q)
    txt = r["response"]
    if est_refus(txt):
        n_r += 1
        continue
    rep = extraire_choix(txt)
    if rep == bonne:
        n_c += 1
    else:
        n_f += 1
print(f"  correct {n_c} · faux {n_f} · refus {n_r} (sur 30)")
print(f"  précision (hors refus) : {n_c / max(1, n_c + n_f) * 100:.1f} % | "
      f"taux de réponse : {(n_c + n_f) / 30 * 100:.1f} %")

# ── MATH ───────────────────────────────────────────────────────────────
print("\n[2] MATH — 10 problèmes de type olympiade")
n_c, n_f, n_r = 0, 0, 0
for q, bonne in MATH_FR:
    r = ia.poser(q)
    txt = r["response"]
    if est_refus(txt):
        n_r += 1
        continue
    rep = extraire_nombre(txt)
    if rep is not None and abs(rep - bonne) < 1e-6:
        n_c += 1
    else:
        n_f += 1
print(f"  correct {n_c} · faux {n_f} · refus {n_r} (sur 10)")
print(f"  précision (hors refus) : {n_c / max(1, n_c + n_f) * 100:.1f} %")

# ── HumanEval ──────────────────────────────────────────────────────────
print("\n[3] HumanEval — 5 exercices de code Python")
n_c, n_f, n_r = 0, 0, 0
for it in charger_humaneval(5):
    r = ia.poser("Écris une fonction Python : " + it["prompt"][:150])
    txt = r["response"]
    if est_refus(txt):
        n_r += 1
    else:
        n_f += 1
print(f"  correct 0 (le moteur n'exécute pas Python — capacité absente, "
      f"documentée) · faux {n_f} · refus {n_r} (sur 5)")
print(f"  → HumanEval : 0/5 attendu — le moteur 0-LLM n'a AUCUNE capacité "
      f"de code (frontière honnête)")

print("\n" + "=" * 70)
print("LECTURE : les refus sont le comportement calibré (P1.2) — l'IA ne "
      "devine pas. Les scores bruts sont ceux qu'un auditeur externe mesurerait.")
print("=" * 70)
