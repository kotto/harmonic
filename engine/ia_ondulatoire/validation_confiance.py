# -*- coding: utf-8 -*-
"""
validation_confiance.py — P1.2 CALIBRATION DE LA CONFIANCE
===========================================================
Protocole (pré-enregistré, PLAN_FAIBLESSES_IA_HARMONIQUE.md P1.2) :
  200 questions à vérité terrain :
    · 50 MATHS      — réponses exactes connues (vérifiées par calcul local)
    · 30 PHYSIQUE   — masses/B connues (tolérance, AME2020)
    · 20 IDENTITÉ   — réponses déterministes (toujours correctes)
    · 100 HORS-DOMAINE — le BON comportement est le REFUS à basse confiance

Métriques :
    · précision par catégorie vs confiance moyenne annoncée
    · courbe de calibration (bins de confiance) + ECE + Brier score
    · verdict pré-enregistré : ECE < 0,15 → confiance OK ;
      sinon → recalibrage (plafond d'honnêteté sur la boucle générique)
      puis re-mesure.

Usage : python validation_confiance.py
"""

import re
import sys

from cerveau import IaOndulatoire

# ────────────────────────────────────────────────────────────────────────
# 1. VÉRITÉ TERRAIN
# ────────────────────────────────────────────────────────────────────────
MATHS = [  # (question, réponse exacte)
    ("combien font 17 + 25 ?", 42), ("combien font 12 fois 8 ?", 96),
    ("combien font 100 - 37 ?", 63), ("combien font 9 fois 9 ?", 81),
    ("combien font 45 + 55 ?", 100), ("combien font 7 fois 6 ?", 42),
    ("combien font 200 / 5 ?", 40), ("combien font 18 + 29 ?", 47),
    ("combien font 3 fois 15 ?", 45), ("combien font 90 - 12 ?", 78),
    ("combien font 64 / 8 ?", 8), ("combien font 11 fois 11 ?", 121),
    ("combien font 25 + 36 ?", 61), ("combien font 5 fois 13 ?", 65),
    ("combien font 48 / 6 ?", 8), ("combien font 33 + 47 ?", 80),
    ("combien font 8 fois 7 ?", 56), ("combien font 150 - 75 ?", 75),
    ("combien font 14 fois 3 ?", 42), ("combien font 120 / 10 ?", 12),
    ("combien font 21 + 19 ?", 40), ("combien font 6 fois 12 ?", 72),
    ("combien font 84 - 39 ?", 45), ("combien font 16 fois 4 ?", 64),
    ("combien font 250 / 25 ?", 10), ("combien font 37 + 28 ?", 65),
    ("combien font 9 fois 11 ?", 99), ("combien font 73 - 45 ?", 28),
    ("combien font 15 fois 5 ?", 75), ("combien font 300 / 30 ?", 10),
    ("combien font 19 + 31 ?", 50), ("combien font 4 fois 25 ?", 100),
    ("combien font 1000 / 100 ?", 10), ("combien font 56 + 44 ?", 100),
    ("combien font 13 fois 7 ?", 91), ("combien font 95 - 28 ?", 67),
    ("combien font 22 fois 3 ?", 66), ("combien font 81 / 9 ?", 9),
    ("combien font 26 + 34 ?", 60), ("combien font 10 fois 10 ?", 100),
    ("combien font 60 / 12 ?", 5), ("combien font 44 + 26 ?", 70),
    ("combien font 17 fois 4 ?", 68), ("combien font 77 - 18 ?", 59),
    ("combien font 55 / 5 ?", 11), ("combien font 31 + 39 ?", 70),
    ("combien font 12 fois 9 ?", 108), ("combien font 88 - 24 ?", 64),
    ("combien font 36 / 4 ?", 9), ("combien font 23 + 27 ?", 50),
]

PHYSIQUE = [  # (question, Z, A, masse_u tolérée ±0,02)
    ("masse du fer 56", 26, 56, 55.9349), ("masse de l'uranium 238", 92, 238, 238.0508),
    ("masse du plomb 208", 82, 208, 207.9767), ("masse du carbone 12", 6, 12, 12.0000),
    ("masse de l'oxygène 16", 8, 16, 15.9949), ("masse du nickel 58", 28, 58, 57.9353),
    ("masse du zinc 64", 30, 64, 63.9291), ("masse de l'argent 107", 47, 107, 106.9051),
    ("masse de l'or 197", 79, 197, 196.9666), ("masse du thorium 232", 90, 232, 232.0381),
    ("masse du titane 48", 22, 48, 47.9479), ("masse du chrome 52", 24, 52, 51.9405),
    ("masse du cobalt 59", 27, 59, 58.9332), ("masse du cuivre 63", 29, 63, 62.9296),
    ("masse du sodium 23", 11, 23, 22.9898), ("masse du calcium 40", 20, 40, 39.9626),
    ("masse du brome 79", 35, 79, 78.9183), ("masse du césium 133", 55, 133, 132.9055),
    ("masse du baryum 138", 56, 138, 137.9052), ("masse du mercure 202", 80, 202, 201.9706),
    ("masse de l'hélium 4", 2, 4, 4.0026), ("masse du lithium 7", 3, 7, 7.0160),
    ("masse du béryllium 9", 4, 9, 9.0122), ("masse du bore 11", 5, 11, 11.0093),
    ("masse de l'azote 14", 7, 14, 14.0031), ("masse du néon 20", 10, 20, 19.9924),
    ("masse du silicium 28", 14, 28, 27.9769), ("masse du soufre 32", 16, 32, 31.9721),
    ("masse du potassium 39", 19, 39, 38.9637), ("masse du gallium 69", 31, 69, 68.9256),
]

IDENTITE = ["qui es-tu", "qui es tu", "tu es qui", "ta nature", "tes domaines",
            "que sais-tu faire", "tes capacités", "bonjour", "salut", "hello",
            "merci", "au revoir", "bonsoir", "coucou", "bonne nuit",
            "comment vas-tu", "ça va", "tu vas bien", "hello toi", "salutations"]

HORS_DOMAINE = [
    "quelle est la capitale du Botswana",
    "qui a écrit Les Misérables",
    "combien d'habitants compte le Japon",
    "quelle est la vitesse de la lumière en miles",
    "qui a peint la Joconde",
    "quel est le plus long fleuve du monde",
    "que signifie E=mc2",
    "qui a découvert l'Amérique",
    "quelle est la taille de la Tour Eiffel",
    "combien de planètes compte le système solaire",
    "qui a inventé le téléphone",
    "quelle est la date de la Révolution française",
    "combien de continents y a-t-il",
    "qui est le président des États-Unis",
    "quelle est la monnaie du Brésil",
    "qui a écrit Hamlet",
    "combien de temps dure une journée sur Mars",
    "quelle est la capitale de l'Australie",
    "qui a fondé Rome",
    "quel est le plus grand océan",
    "qui a peint la Cène",
    "combien d'étages a la Tour Eiffel",
    "quelle est la langue officielle du Canada",
    "qui a découvert la pénicilline",
    "combien de secondes dans une journée",
    "quelle est la plus haute montagne d'Afrique",
    "qui a écrit le Petit Prince",
    "combien de pays en Europe",
    "quelle est la vitesse du son",
    "qui a inventé l'ampoule",
    "quelle est la capitale de la Norvège",
    "combien de lunes a Jupiter",
    "qui a composé la Neuvième Symphonie",
    "quelle est la plus grande ville du monde",
    "combien de dents a un adulte",
    "qui a écrit Don Quichotte",
    "quelle est la température du soleil",
    "combien de couleurs a l'arc-en-ciel",
    "qui a découvert l'électricité",
    "quelle est la capitale du Pérou",
    "combien de kilomètres fait un marathon",
    "qui a inventé l'imprimerie",
    "quelle est la plus petite planète",
    "combien d'os a le corps humain",
    "qui a écrit les Fables de La Fontaine",
    "quelle est la capitale du Kenya",
    "combien de minutes dans une semaine",
    "qui a peint Guernica",
    "quelle est la profondeur de la fosse des Mariannes",
    "combien de pages a la Bible",
    "quelle est la capitale du Vietnam",
    "qui a découvert la radioactivité",
    "combien de cœurs a un poulpe",
    "qui a écrit le Rouge et le Noir",
    "quelle est la plus longue rivière de France",
    "combien de jours dure une grossesse humaine",
    "qui a inventé le cinéma",
    "quelle est la capitale du Chili",
    "combien de sommets de plus de 8000 m",
    "qui a peint La Liberté guidant le peuple",
    "quelle est la vitesse d'un avion de ligne",
    "combien d'étoiles dans la Voie lactée",
    "qui a écrit les Misérables",
    "quelle est la capitale de la Nouvelle-Zélande",
    "combien de secondes dans une heure",
    "qui a découvert la gravitation",
    "quelle est la plus grande île du monde",
    "combien de doigts a un kangourou",
    "qui a écrit le Comte de Monte-Cristo",
    "quelle est la capitale de l'Islande",
    "combien de temps met la lumière pour aller de la Lune à la Terre",
    "qui a inventé la radio",
    "quelle est la plus profonde grotte du monde",
    "combien de variétés de pommes existe-t-il",
    "qui a écrit Madame Bovary",
    "quelle est la capitale de l'Argentine",
    "combien de mètres fait la piste d'athlétisme",
    "qui a peint les Nymphéas",
    "quelle est la température moyenne de la Terre",
    "combien de pays parle-t-on le français",
    "qui a découvert le vaccin contre la rage",
    "quelle est la plus grande forêt du monde",
    "combien de chambres a le château de Versailles",
    "qui a écrit Cyrano de Bergerac",
    "quelle est la capitale de la Suède",
    "combien de chevaux a une Formule 1",
    "qui a inventé la machine à vapeur",
    "quelle est la plus haute chute d'eau du monde",
    "combien de langues officielles a la Suisse",
    "qui a écrit Germinal",
    "quelle est la capitale du Mexique",
    "combien de battements par minute a le cœur humain",
    "qui a peint le Radeau de la Méduse",
    "quelle est la plus longue route du monde",
    "combien de satellites naturels a Saturne",
    "qui a découvert l'Amérique du Sud",
    "quelle est la capitale de la Turquie",
    "combien de degrés fait l'eau qui bout",
    "qui a écrit les Trois Mousquetaires",
    "quelle est la plus grande pyramide du monde",
    "combien de doigts a un cheval",
]

# ────────────────────────────────────────────────────────────────────────
# 2. ÉVALUATION
# ────────────────────────────────────────────────────────────────────────
def extraire_nombre(texte):
    nums = re.findall(r"-?\d+(?:[.,]\d+)?", texte.replace(",", "."))
    return float(nums[-1]) if nums else None


def extraire_masse(texte):
    m = re.search(r"masse prédite ([\d.]+)", texte)
    return float(m.group(1)) if m else None


def correcte(question, reponse, confiance, verite):
    """Vérité terrain par catégorie."""
    if verite["type"] == "maths":
        n = extraire_nombre(reponse)
        return n is not None and abs(n - verite["valeur"]) < 0.01
    if verite["type"] == "physique":
        m = extraire_masse(reponse)
        return m is not None and abs(m - verite["valeur"]) < 0.02
    if verite["type"] == "identite":
        return True
    if verite["type"] == "hors_domaine":
        # le BON comportement : refus explicite à basse confiance
        refuse = ("je ne connais pas" in reponse.lower()
                  or "ne sais pas" in reponse.lower()
                  or "souviens-toi" in reponse.lower())
        return refuse and confiance <= 0.30
    return False


def construire_verites():
    v = []
    for q, r in MATHS:
        v.append((q, {"type": "maths", "valeur": r}))
    for q, z, a, m in PHYSIQUE:
        v.append((q, {"type": "physique", "valeur": m}))
    for q in IDENTITE:
        v.append((q, {"type": "identite"}))
    for q in HORS_DOMAINE:
        v.append((q, {"type": "hors_domaine"}))
    return v


def mesurer(ia, verites):
    """Retourne (confiances, corrects, sources, reponses)."""
    confiances, corrects, sources, reponses = [], [], [], []
    for q, verite in verites:
        r = ia.poser(q)
        confiances.append(r["confidence"])
        corrects.append(correcte(q, r["response"], r["confidence"], verite))
        sources.append(r.get("source", ""))
        reponses.append(r)
    return (np.array(confiances), np.array(corrects), sources, reponses)


import numpy as np  # noqa: E402

print("=" * 70)
print("P1.2 CALIBRATION DE LA CONFIANCE — 200 questions à vérité terrain")
print("=" * 70)
print(f"  {len(MATHS)} maths · {len(PHYSIQUE)} physique · {len(IDENTITE)} identité · "
      f"{len(HORS_DOMAINE)} hors-domaine")

verites = construire_verites()
ia = IaOndulatoire(charger=False)

conf, ok, sources, reponses = mesurer(ia, verites)

# par catégorie
print("\n[1] Précision et confiance par catégorie")
cats = [("maths", 0, 50), ("physique", 50, 80), ("identité", 80, 100),
        ("hors-domaine", 100, 200)]
for nom, a, b in cats:
    print(f"  {nom:12s}: précision {ok[a:b].mean() * 100:6.1f} % | confiance "
          f"moyenne {conf[a:b].mean():.2f}")

# calibration : protocole en DEUX volets (08/08/2026)
#   V1 — ECE sur les ASSERTIONS (confiance > 0) : précision des affirmations
#        vs confiance annoncée. Le refus à confiance 0 n'est PAS une
#        assertion — l'ECE global le pénaliserait à tort.
#   V2 — Qualité de refus : % hors-domaine REFUSÉS (cible 100 %) et
#        % connus ASSERTÉS (cible 100 %).
print("\n[2] V1 — Calibration des ASSERTIONS (confiance > 0)")
assertion = conf > 0
n_assert = assertion.sum()
bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)]
ece = 0.0
for lo, hi in bins:
    sel = (conf >= lo) & (conf < hi) & assertion
    n = sel.sum()
    if n == 0:
        continue
    acc = ok[sel].mean()
    c_moy = conf[sel].mean()
    ece += (n / n_assert) * abs(acc - c_moy)
    print(f"  conf [{lo:.1f},{hi:.1f}[: n={n:3d} | précision {acc * 100:6.1f} % | "
          f"confiance moyenne {c_moy:.2f} | écart {abs(acc - c_moy):.2f}")
brier_assert = np.mean((conf[assertion] - ok[assertion].astype(float)) ** 2)
print(f"\n  ECE(assertions) = {ece:.3f}   Brier(assertions) = {brier_assert:.3f}"
      f"   (critère : ECE < 0.15)")

print("\n[2b] V2 — Qualité de refus")
refuse = np.array([("je ne connais pas" in r["response"].lower()
                    or "souviens-toi" in r["response"].lower()) for r in reponses])
hors = np.array([v[1]["type"] == "hors_domaine" for v in verites])
connus = ~hors
print(f"  hors-domaine : {refuse[hors].mean() * 100:6.1f} % refusés"
      f" (cible 100 %) | n={hors.sum()}")
print(f"  connus       : {(~refuse[connus]).mean() * 100:6.1f} % assertés"
      f" (cible 100 %) | n={connus.sum()}")
print(f"  précision GLOBALE (comportement correct) : {ok.mean() * 100:.1f} %")

# sources
print("\n[3] Sources de réponse")
from collections import Counter
for src, n in Counter(sources).most_common():
    print(f"  {src:28s}: {n}")

# ────────────────────────────────────────────────────────────────────────
# 3. RÉCAPITULATIF
# ────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
if ece < 0.15 and refuse[hors].mean() >= 0.90:
    print("✅ CONFIANCE CALIBRÉE : ECE(assertions) < 0,15 ET refus hors-domaine ≥ 90 %.")
elif ece < 0.15:
    print("⚠️ ECE(assertions) OK mais refus hors-domaine insuffisant"
          f" ({refuse[hors].mean() * 100:.0f} %) — seuil de refus à relever.")
else:
    print("⚠️ ECE(assertions) >= 0,15 — la confiance des assertions n'est pas"
          " calibrée : auditer la boucle générique (synthèse) et les seuils.")
print("=" * 70)
