# -*- coding: utf-8 -*-
"""
typeur.py — Le typeur de nombres : la traduction texte → modèle typé.

Le diagnostic des échecs GSM8K a montré que le problème principal n'est pas le
calcul mais la TRADUCTION : les nombres du texte ne sont pas typés, et la machine
additionne des pommes, des dollars, des années et des douzaines.

Ce module attribue à chaque nombre une DIMENSION (ce qu'il mesure) et un RÔLE
(ce qu'il fait dans le calcul) :

    « 252 eggs per day … $2 per dozen »
      → 252 : QUANTITE eggs, taux /day
      → 2   : MONTANT dollars, prix /dozen  (conversion ÷12 requise)
    « he bought a car for $20000 in 2007 »
      → 20000 : MONTANT
      → 2007  : ANNEE → IGNORÉE

Dimensions : monnaie · durée · longueur · masse · volume · température ·
vitesse · surface · fraction · année · objet (compté)
Rôles      : quantite · taux (/unité) · prix_unitaire · increment · compteur ·
             fraction · annee · montant

Usage :
    typer("He earns 50 dollars an hour for 6 hours.")
    → [NombreType(valeur=50, dimension='monnaie', role='taux', unite='heure'),
       NombreType(valeur=6, dimension='duree', role='duree', unite='heure')]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from gsm8k import _numeriser
from machine_etats import OBJETS, PLURIELS_IRREGULIERS

# ────────────────────────────────────────────────────────────────────────
# Unités → dimensions
# ────────────────────────────────────────────────────────────────────────

UNITE_DIMENSION = {
    # monnaie
    "dollar": "monnaie", "dollars": "monnaie", "cent": "monnaie", "cents": "monnaie",
    "franc": "monnaie", "francs": "monnaie", "euro": "monnaie", "euros": "monnaie",
    "pound": "monnaie", "penny": "monnaie", "pennies": "monnaie", "quarter": "monnaie",
    "dime": "monnaie", "nickel": "monnaie", "money": "monnaie", "buck": "monnaie",
    # durée
    "hour": "duree", "hours": "duree", "minute": "duree", "minutes": "duree",
    "second": "duree", "seconds": "duree", "day": "duree", "days": "duree",
    "week": "duree", "weeks": "duree", "month": "duree", "months": "duree",
    "year": "duree", "years": "duree", "decade": "duree", "decades": "duree",
    "heure": "duree", "heures": "duree", "jour": "duree", "jours": "duree",
    "semaine": "duree", "semaines": "duree", "mois": "duree", "an": "duree", "ans": "duree",
    # longueur
    "mile": "longueur", "miles": "longueur", "km": "longueur", "kilometer": "longueur",
    "kilometers": "longueur", "kilometre": "longueur", "meter": "longueur",
    "meters": "longueur", "metre": "longueur", "metres": "longueur", "foot": "longueur",
    "feet": "longueur", "yard": "longueur", "yards": "longueur", "inch": "longueur",
    "inches": "longueur",
    # masse
    "kg": "masse", "kilogram": "masse", "kilograms": "masse", "gram": "masse",
    "grams": "masse", "ounce": "masse", "ounces": "masse", "pound": "masse",
    "pounds": "masse", "ton": "masse", "tons": "masse",
    # volume
    "gallon": "volume", "gallons": "volume", "liter": "volume", "liters": "volume",
    "litre": "volume", "litres": "volume", "quart": "volume", "pint": "volume",
    "cup": "volume", "cups": "volume", "tablespoon": "volume", "teaspoon": "volume",
    # température
    "degree": "temperature", "degrees": "temperature", "fahrenheit": "temperature",
    "celsius": "temperature",
    # vitesse
    "mph": "vitesse", "km/h": "vitesse", "mph": "vitesse",
    # surface
    "square": "surface", "acre": "surface", "acres": "surface",
    # proportion
    "percent": "fraction", "percentage": "fraction", "%": "fraction",
    "dozen": "douzaine", "dozens": "douzaine",
}

# valeurs des pièces de monnaie US (en cents) — conversion requise
PIECES = {"quarter": 25, "dime": 10, "nickel": 5, "penny": 1, "cent": 1}
# conversions d'unités (vers l'unité canonique de la dimension)
CONVERSIONS = {
    "dozen": 12.0, "dozens": 12.0,
    "quarter": 0.25, "dime": 0.10, "nickel": 0.05, "penny": 0.01,   # en dollars
    "foot": 0.3333333333333333, "feet": 0.3333333333333333,         # en yards
    "minute": 1 / 60.0, "second": 1 / 3600.0,                       # en heures
    "day": 24.0, "days": 24.0, "week": 168.0, "weeks": 168.0,       # en heures
    "month": 720.0, "year": 8760.0,                                 # en heures
}
CONVERSIONS_MONNAIE = {"quarter": 0.25, "dime": 0.10, "nickel": 0.05, "penny": 0.01,
                       "cent": 0.01, "cents": 0.01, "buck": 1.0, "dollar": 1.0}

# motifs de rôle (fenêtre de contexte autour du nombre)
ROLE_TAUX = r"\bper\s+([a-zà-ü]+)|each\b|/hour|/day|/week|/month|/year"
ROLE_PRIX = (r"\$\s*|dollars?\s+(?:each|per)|costs?\s+|\$|coûte|coute|"
             r"francs?\s+(?:each|par|chacun)|spends?|spent|pays?|paid|earns?|"
             r"earned|receives?|received|saves?|costs?|an?\s+(?:hour|day|week|"
             r"month|year)\b")
ROLE_ANNEE = r"\bin\s+1[89]\d\d\b|\bin\s+20\d\d\b|born in|year\s+1[89]\d\d"
ROLE_FRACTION_MOT = r"third|quarter|half|fifth|sixth|seventh|eighth|ninth|tenth"
ROLE_INCREMENT = r"(?:every|each|per)\s+(?:hour|minute|day|week|month|year)\s+"
FRACTIONS_ORALES = {"one-third": 1/3, "two-thirds": 2/3, "one-fourth": 0.25,
                    "three-fourths": 0.75, "one-half": 0.5, "two-fifths": 0.4,
                    "three-fifths": 0.6, "one-fifth": 0.2, "one-quarter": 0.25,
                    "three-quarters": 0.75, "four-fifths": 0.8}


@dataclass
class NombreType:
    """Un nombre du texte, typé pour la traduction."""
    valeur: float
    dimension: str                 # monnaie, duree, longueur, objet, année…
    role: str                      # quantite, taux, prix_unitaire, duree, annee…
    unite: str = ""                # egg, dollar, hour…
    objet: str = ""                # pour la dimension objet : l'objet compté
    contexte: str = ""             # fenêtre locale (pour le débogage)
    position: int = 0              # position dans le texte numérisé
    ignore: bool = False           # True = nombre sans rôle calculable (année…)

    def __repr__(self):  # pragma: no cover
        return (f"NombreType({self.valeur:g}, {self.dimension}/{self.role}"
                + (f", {self.unite}" if self.unite else "") + ")")


def _unite_apres(texte: str, fin: int) -> str:
    """L'unité dans les 20 caractères suivant le nombre. Les objets comptés
    priment sur les unités physiques : « 252 eggs per day » → eggs,
    « 7 lemons each year » → lemons (pas day/year)."""
    fen = texte[fin: fin + 20].lower()
    mots = re.findall(r"[a-zà-ü]+", fen)
    for mot in mots[:3]:
        # 1. objets comptés (le nom qui suit le nombre)
        for objet in OBJETS:
            if re.search(rf"\b{objet}(?:es|s)?\b", mot):
                return objet
        for pluriel, singulier in PLURIELS_IRREGULIERS.items():
            if mot == pluriel:
                return singulier
    for mot in mots[:3]:
        # 2. unités physiques
        if mot in UNITE_DIMENSION:
            return mot
        base = mot[:-1] if mot.endswith("s") else mot
        if base in UNITE_DIMENSION:
            return base
    return ""


def _dimension_de(unite: str) -> str:
    if not unite:
        return "inconnue"
    if unite in UNITE_DIMENSION:
        return UNITE_DIMENSION[unite]
    if re.search(rf"\b{re.escape(unite)}(?:es|s)?\b", " ".join(OBJETS)):
        return "objet"
    return "objet"


def _trouver_objet_texte(texte: str) -> Optional[str]:
    """Objet compté le plus proche (réutilise la logique de machine_etats)."""
    from machine_etats import _objet_de
    return _objet_de(texte)


def typer(question: str) -> List[NombreType]:
    """Convertit le texte en nombres typés (dimension + rôle)."""
    q = _numeriser(question)
    resultats: List[NombreType] = []

    # fractions orales : « one-third », « three-fourths » → converties d'abord
    for mot, val in FRACTIONS_ORALES.items():
        q = re.sub(rf"\b{re.escape(mot)}\b", str(val), q, flags=re.IGNORECASE)

    for m in re.finditer(r"-?\d+(?:[.,]\d+)?(?:/\d+)?", q):
        groupe = m.group()
        # contexte local commun (fenêtre ~30 avant / 35 après), tronqué au
        # séparateur de phrase suivant : l'intention du nombre est locale
        ctx = q[max(0, m.start() - 30): m.end() + 35]
        sep_ctx = ctx.find(". ")
        if sep_ctx > 0:
            ctx = ctx[:sep_ctx + 1]
        if "/" in groupe:
            a, b = groupe.split("/")
            valeur = float(a) / float(b) if float(b) else 0.0
            dimension, role, unite = "fraction", "fraction", ""
        elif "%" in q[max(0, m.start() - 2): m.end() + 2] \
                or "percent" in q[m.end(): m.end() + 10].lower():
            valeur = float(groupe.replace(",", ".")) / 100.0   # 25% → 0.25
            dimension, role, unite = "fraction", "fraction", "percent"
        else:
            valeur = float(groupe.replace(",", "."))
            unite = _unite_apres(q, m.end())
            dimension = _dimension_de(unite)
            role = "quantite"

            # rôles contextuels — la monnaie ne se décide que LOCALEMENT
            apres = q[m.end(): m.end() + 25]
            fen_monnaie = q[max(0, m.start() - 15): m.end() + 10]
            fen_verbe = q[max(0, m.start() - 12): m.end()]
            if re.search(ROLE_ANNEE, ctx) and 1800 <= valeur <= 2200:
                role, dimension = "annee", "annee"
            elif re.search(r"\bper\s+[a-zà-ü]+|/hour|/day|/week|/month|/year", apres) \
                    and dimension != "monnaie":
                # TAUX : « 60 miles per hour », « 252 eggs per day » (per APRÈS)
                role = "taux"
                mm = re.search(r"\bper\s+([a-zà-ü]+)", apres)
                if mm:
                    unite = unite or mm.group(1)
            elif re.search(r"\btimes?\b", apres):
                role = "facteur"                    # « 3 times a week » → ×3
            elif re.search(r"\ban?\s+(?:hour|day|week|month|year)\b", apres) \
                    and (dimension == "monnaie" or "$" in fen_monnaie):
                role = "prix_unitaire"              # « 50 dollars an hour »
                dimension = "monnaie"
            elif dimension == "monnaie" \
                    or re.search(r"\$|dollars?|francs?|euros?|cents?", fen_monnaie):
                role = "prix_unitaire" if re.search(r"each|per|par\b|chacun", ctx) \
                    or re.search(r"\b(coûte|coute|costs?|coutent|coûtent)\b",
                                 fen_verbe, re.IGNORECASE) else "montant"
                dimension = "monnaie"
            elif re.search(r"\b(spends?|spent|pays?|paid|earns?|earned|receives?|"
                           r"received|costs?|saves?|coûte|coute|coutent|coûtent)\b",
                           fen_verbe, re.IGNORECASE):
                role = "prix_unitaire" if re.search(r"\b(coûte|coute|costs?|coutent|"
                                                    r"coûtent)\b", fen_verbe,
                                                    re.IGNORECASE) else "montant"
                dimension = "monnaie"   # « spends nine » / « coûte 300 francs »
            elif re.search(ROLE_INCREMENT, ctx):
                role = "increment"
            elif dimension == "duree":
                role = "duree"
            elif dimension == "annee":
                role = "annee"
            elif dimension == "fraction":
                role = "fraction"

        # objet compté pour les dimensions non physiques (cherché APRÈS le
        # nombre d'abord — « set the 5 pies » → pie, pas set)
        objet = ""
        if dimension == "objet" or (dimension == "inconnue" and role == "quantite"):
            fen_apres = q[m.end(): m.end() + 22]
            objet = _trouver_objet_texte(fen_apres) or ""
            if not objet:
                fen = q[max(0, m.start() - 10): m.end() + 22]
                objet = _trouver_objet_texte(fen) or ""
            if objet:
                dimension = "objet"
                unite = objet

        # années et compteurs purs → à ignorer
        ignorer = role in ("annee",)
        resultats.append(NombreType(
            valeur=valeur, dimension=dimension, role=role, unite=unite,
            objet=objet, contexte=ctx.strip(), position=m.start(), ignore=ignorer))
    return resultats
