# -*- coding: utf-8 -*-
"""
machine_etats.py — Machine à états sémantique pour les problèmes de mots.

Un énoncé narratif = une suite d'ACTIONS sur un ÉTAT de compteurs d'objets
comptés (œufs, dollars, moutons, kilomètres…). Chaque NOMBRE est traité avec
sa fenêtre de contexte locale :

    avoir/posséder/poser     → initialiser le compteur de l'objet
    manger/donner/vendre     → retirer du compteur (momentum si objet implicite)
    acheter/gagner/recevoir  → ajouter au compteur
    « N X per Y » / « M boîtes » → conversion d'unité (densité de conteneur)
    partager également       → division du compteur
    « X% »                   → fraction du compteur
    « A a k fois plus de Y que B » → équation relative A = k·B (propagation)

La question finale désigne l'objet cible (« How many eggs… », « in dollars »).
Si l'analyse sémantique échoue (aucun objet reconnu), le pipeline par résonance
de gsm8k.py sert de fallback.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from gsm8k import _numeriser

# ────────────────────────────────────────────────────────────────────────
# Objets comptés (EN/FR) — ce que les énoncés comptent
# ────────────────────────────────────────────────────────────────────────

OBJETS = [
    "egg", "apple", "dollar", "muffin", "mile", "hour", "minute", "day", "week",
    "month", "year", "box", "pencil", "book", "chicken", "sheep", "cup", "child",
    "person", "student", "glass", "cookie", "cake", "franc", "euro", "km",
    "gallon", "liter", "litre", "tree", "flower", "card", "stamp", "bird", "fish",
    "dog", "cat", "page", "song", "picture", "shirt", "sock", "shoe", "bag",
    "bottle", "slice", "piece", "group", "team", "basket", "tray", "crate", "bar",
    "can", "jar", "loaf", "bucket", "packet", "car", "bike", "meter", "metre",
    "foot", "inch", "pound", "cent", "quarter", "nickel", "dime", "peach",
    "orange", "banana", "gumdrop", "candy", "lollipop", "pizza", "sandwich",
    "burger", "hot dog", "taco", "marble", "toy", "ball", "bat", "doll", "teddy",
    "class", "lesson", "problem", "question", "test", "quiz", "score", "point",
    "run", "hit", "strike", "inning", "game", "match", "set", "ticket", "seat",
    "row", "chair", "table", "floor", "room", "window", "door", "step", "block",
    "brick", "nail", "screw", "bolt", "fiber", "ribbon", "bow", "gift", "present",
    "pack", "package", "parcel", "envelope", "letter", "postcard", "photo",
    "painting", "drawing", "sketch", "portrait", "film", "movie", "video", "clip",
    "episode", "season", "chapter", "paragraph", "word", "line", "sentence",
    "digit", "number", "penny", "bus", "truck", "van", "train", "boat", "plane",
    "dozen", "pair", "bunch", "bundle", "sheet", "slice", "loaf", "piece",
    "cahier", "crayon", "stylo", "pomme", "orange", "kilomètre", "kilometre",
    "kilomètres", "kilometres", "élève", "eleve", "élèves", "eleves", "pain",
    "sprint", "lap", "house", "apartment", "ticket", "flight", "meter", "meter",
    "meter", "centimeter", "centimetre", "kilometer", "kilogram", "gram", "ounce",
    "pound", "cup", "tablespoon", "teaspoon", "quart", "pint", "glass", "pie",
    "candle", "candle", "beeswax", "unit", "building", "floor", "brick", "plank",
]
OBJETS = sorted(set(OBJETS), key=len, reverse=True)

CONTENEURS = {"box", "bag", "basket", "pack", "crate", "jar", "bottle", "can",
              "tray", "bundle", "bunch", "pair", "set", "dozen", "loaf", "sheet",
              "sprint", "lap", "flight", "trip", "round", "day"}
# conteneurs temporels : « 60 miles per hour for 3 hours » → × 3
TEMPS = {"hour", "minute", "second", "day", "week", "month", "year", "heure",
         "minute", "jour", "semaine", "mois", "an"}
# pluriels irréguliers → singulier
PLURIELS_IRREGULIERS = {"children": "child", "people": "person", "mice": "mouse",
                        "feet": "foot", "teeth": "tooth", "women": "woman",
                        "men": "man", "geese": "goose"}


def _trouver_objet(texte: str, debut: int = 0, fin: Optional[int] = None) -> Optional[str]:
    """Objet compté le PLUS PROCHE du début de la fenêtre (position minimale),
    pluriels réguliers (-s, -es) et irréguliers gérés."""
    t = texte.lower()
    if fin is None:
        fin = len(t)
    fen = t[debut:fin]
    meilleur, meilleure_pos = None, 10 ** 9
    for objet in OBJETS:
        m = re.search(rf"\b{objet}(?:es|s)?\b", fen)
        if m and m.start() < meilleure_pos:
            meilleur, meilleure_pos = objet, m.start()
    for pluriel, singulier in PLURIELS_IRREGULIERS.items():
        m = re.search(rf"\b{pluriel}\b", fen)
        if m and m.start() < meilleure_pos:
            meilleur, meilleure_pos = singulier, m.start()
    return meilleur


def _objet_de(texte: str) -> Optional[str]:
    """Premier objet compté présent dans le texte."""
    return _trouver_objet(texte)


def _objet_apres(texte: str, fin_nombre: int) -> Optional[str]:
    """Objet le plus proche dans les 18 caractères suivant un nombre."""
    return _trouver_objet(texte, fin_nombre, fin_nombre + 18)


def _derniere_phrase(q: str) -> str:
    """La question finale : la phrase après le dernier séparateur.
    « …luncheon. How many pieces were eaten? » → « How many pieces were eaten »."""
    partie = q[:-1] if q.endswith("?") else q
    sep = max(partie.rfind(". "), partie.rfind("! "), partie.rfind(".\n"),
              partie.rfind("? "))
    return partie[sep + 2:] if sep >= 0 else partie

# actions → transitions
_RETRAIT = r"\b(eats?|ate|gives?|gave|away|sells?|sold|spends?|spent|loses?|lost|" \
           r"removes?|removed|takes?|took|breaks?|broke|drops?|dropped|donates?|" \
           r"donated|donne|mange|manges?|vend|vendus?|dépense|depense|dépensé|donné|" \
           r"cède|cede|uses?|used|wastes?|wasted|pays?|paid)\b"
_AJOUT = r"\b(buys?|bought|purchased?|gets?|got|gains?|gained|receives?|received|" \
         r"earns?|earned|makes?|made|collects?|collected|picks?|picked|finds?|" \
         r"found|achète|achete|achète|gagne|gagné|reçoit|recu|collecte)\b"
_PARTAGE = r"\b(equally|among|split|between|divided by|shared by|partagé|partage|" \
           r"réparti|reparti)\b"
_POURCENT = r"%|percent"
_RESTE = r"\b(left|remainder|remaining|rest|reste|restant)\b"
_MOMENTUM_ACTION = ["soustraction", "addition"]   # actions à rejouer si objet implicite


class MachineEtatsSemantique:
    """Analyse sémantique → compteurs par objet → réponse ciblée."""

    def __init__(self):
        self.compteurs: Dict[str, float] = {}
        self.densites: Dict[str, float] = {}       # objet → quantité par conteneur
        self.etapes: List[str] = []
        self.derniere_action: Optional[str] = None

    # ── le résolveur principal ──────────────────────────────────────────
    def resoudre(self, question: str) -> Optional[Dict[str, Any]]:
        """Retourne None si l'analyse échoue (fallback ondulatoire)."""
        q = _numeriser(question)
        self.compteurs = {}
        self.densites = {}
        self.etapes = []
        self.derniere_action = None

        # passe 0 : équations relatives (« A has k times as many X as B »)
        relatif = self._equations_relatives(q)
        if relatif is not None:
            return relatif

        # passe 1 : chaque nombre avec sa fenêtre locale (40 avant / 30 après,
        # tronquée au séparateur de phrase précédent) — fractions « 3/4 » incluses
        matches = list(re.finditer(r"-?\d+(?:[.,]\d+)?(?:/\d+)?", q))
        if not matches:
            return None
        traites = 0

        # passe 0b : densités pré-analyse — « 60 meters each sprint », « 16 eggs
        # per day » (le conteneur peut précéder la quantité dans l'énoncé)
        densites_skippees = set()
        for m_d in re.finditer(r"(\d+(?:[.,]\d+)?)\s+([a-zà-ü]+)\s+(?:each|per)\s+([a-zà-ü]+)",
                               q, re.IGNORECASE):
            n_d = float(m_d.group(1).replace(",", "."))
            objet_d = _objet_de(m_d.group(2))
            if objet_d is not None:
                self.compteurs.setdefault(objet_d, n_d)
                self.densites[objet_d] = n_d
                densites_skippees.add(m_d.start())
                self.etapes.append(f"« densité » → {n_d:g} {objet_d}/unité")

        for m in matches:
            if m.start() in densites_skippees:
                continue                     # déjà traité par la pré-analyse
            m_frac = re.match(r"(\d+)/(\d+)$", m.group())
            if m_frac:
                n = float(m_frac.group(1)) / float(m_frac.group(2))
            else:
                n = float(m.group().replace(",", "."))
            debut_ctx = max(0, m.start() - 40)
            avant = q[:m.start()]
            sep = max(avant.rfind(". "), avant.rfind("! "), avant.rfind("? "))
            if sep > debut_ctx:
                debut_ctx = sep + 2
            # fenêtre après : tronquée au séparateur de phrase suivant — seule
            # l'intention locale du nombre doit parler
            apres = q[m.end(): m.end() + 30]
            positions = [apres.find(s) for s in (". ", "! ", "? ", ".\n") if s in apres]
            sep_apres = min(positions) if positions else -1
            if sep_apres > 0:
                apres = apres[:sep_apres + 1]
            ctx = (q[debut_ctx: m.end()] + apres).replace("\n", " ")
            objet = _objet_apres(q, m.end()) or _objet_de(apres) or _objet_de(ctx)
            if objet is None:
                # action sans objet local (« eats 3 », « gives 2 ») : l'objet est
                # implicite — mono-compteur → l'action s'applique au compteur unique
                if len(self.compteurs) == 1 and (
                        re.search(_RETRAIT, ctx) or re.search(_AJOUT, ctx)):
                    objet = next(iter(self.compteurs))
                else:
                    continue
            # règle mono-objet : un seul compteur → les objets implicites s'y appliquent
            cible = objet if objet in self.compteurs else (
                next(iter(self.compteurs)) if len(self.compteurs) == 1 else None)
            if cible is None and objet not in self.compteurs:
                cible = objet

            # 0. fraction : « 3/4 of the cookies » → × 3/4 ; « gives away 3/4 » → × (1−3/4)
            if m_frac and cible is not None and cible in self.compteurs \
                    and re.search(r"\bof\b", ctx):
                if re.search(_RETRAIT, ctx):
                    self.compteurs[cible] *= 1 - n
                else:
                    self.compteurs[cible] *= n
                self.etapes.append(f"« {ctx.strip()[-40:]} » → ×{n:g} (fraction) = "
                                   f"{self.compteurs[cible]:g}")
                continue

            # 0b. « N were left » après un état → retrait (« 14 pieces were left »)
            if re.search(r"\b(?:were\s+\d+(?:[.,]\d+)?\s+[a-zà-ü]+\s+left|"
                         r"\d+(?:[.,]\d+)?\s+[a-zà-ü]+\s+were\s+left)\b", ctx) \
                    and cible is not None and cible in self.compteurs \
                    and not re.search(r"\bleft\b", _derniere_phrase(q)):
                self.compteurs[cible] -= n
                self.etapes.append(f"« {ctx.strip()[-40:]} » → −{n:g} (restant) = "
                                   f"{self.compteurs[cible]:g}")
                continue

            # 0b. conversion interne : « cut each pie into 8 pieces » → 5×8
            m_cut = re.search(
                r"\b(cut|divided|split|broke)\s+(?:each|the)\s+([a-zà-ü]+)\s+into\s+"
                r"(\d+(?:[.,]\d+)?)\s+([a-zà-ü]+)", ctx, re.IGNORECASE)
            if m_cut:
                source = _objet_de(m_cut.group(2))
                cible_cut = _objet_de(m_cut.group(4))
                if source is not None and source not in self.compteurs \
                        and len(self.compteurs) == 1:
                    source = next(iter(self.compteurs))   # « 5 apple pies » → pie
                if source is not None and source in self.compteurs and cible_cut:
                    self.compteurs[cible_cut] = self.compteurs[source] \
                        * float(m_cut.group(3))
                    self.etapes.append(f"« {ctx.strip()[-40:]} » → {source} ×"
                                       f"{m_cut.group(3)} = "
                                       f"{self.compteurs[cible_cut]:g}")
                    continue

            # 1. pourcentage sur le compteur courant
            if re.search(_POURCENT, ctx) and cible is not None \
                    and cible in self.compteurs:
                if re.search(r"\b(increase|gain|profit|earn|gagne|augmente|markup)\b",
                             ctx, re.IGNORECASE):
                    self.compteurs[cible] *= 1 + n / 100
                elif re.search(r"\b(decrease|lose|discount|off|baisse|perd|reduces?)\b"
                               + "|" + _RETRAIT, ctx, re.IGNORECASE):
                    self.compteurs[cible] *= 1 - n / 100
                else:
                    self.compteurs[cible] *= n / 100
                self.etapes.append(f"« {ctx.strip()[-40:]} » → % = "
                                   f"{self.compteurs[cible]:g}")
                continue

            # 2a. conversion d'unité : « for $2 per egg » → compteur × 2
            m_conv = re.search(
                r"\b(?:for|at|costs?|coûte|coute)\s+\$?\s*(\d+(?:[.,]\d+)?)\s*"
                r"(?:per|each|chaque|par)\s+([a-zà-ü]+(?:\s+[a-zà-ü]+){0,3})",
                ctx, re.IGNORECASE)
            if m_conv and cible is not None and cible in self.compteurs:
                prix = float(m_conv.group(1).replace(",", "."))
                self.compteurs[cible] *= prix
                self.etapes.append(f"« {ctx.strip()[-40:]} » → ×{prix:g} = "
                                   f"{self.compteurs[cible]:g}")
                continue

            # 2b. coût total : « combien coûtent 4 cahiers » → prix unitaire × 4
            if re.search(r"\b(combien coûtent|combien coutent|how much do|"
                         r"how much does|cost in total)\b", ctx, re.IGNORECASE) \
                    and cible is not None and cible in self.compteurs:
                self.compteurs[cible] *= n
                self.etapes.append(f"« {ctx.strip()[-40:]} » → ×{n:g} (coût) = "
                                   f"{self.compteurs[cible]:g}")
                continue

            # 2c. conteneur : « buys 5 boxes » / « runs 3 sprints » avec
            # « 12 pencils in a box » / « 60 meters each sprint » → densité × n
            conteneur = _objet_apres(q, m.end()) or _objet_de(apres)
            if conteneur in CONTENEURS and self.densites \
                    and not re.search(_RETRAIT, ctx):
                contenu = next(iter(self.densites))
                if contenu in self.compteurs:
                    self.compteurs[contenu] *= n        # compteur déjà amorcé
                else:
                    self.compteurs[contenu] = self.densites[contenu] * n
                self.etapes.append(f"« {ctx.strip()[-40:]} » → densité ×{n:g} "
                                   f"= {self.compteurs[contenu]:g}")
                continue

            # 2d. conteneur temporel : « 60 miles per hour for 3 hours » → × 3
            if conteneur in TEMPS and self.densites:
                contenu = next(iter(self.densites))
                if contenu in self.compteurs:
                    self.compteurs[contenu] *= n
                else:
                    self.compteurs[contenu] = self.densites[contenu] * n
                self.etapes.append(f"« {ctx.strip()[-40:]} » → ×{n:g} ({conteneur}s) "
                                   f"= {self.compteurs[contenu]:g}")
                continue

            # 2e. vitesse moyenne : « Quelle est sa vitesse moyenne ? » → ÷ n
            # (le marqueur peut vivre dans la question entière, après le point)
            if (re.search(r"\b(vitesse moyenne|average speed)\b", ctx, re.IGNORECASE)
                    or re.search(r"\b(vitesse moyenne|average speed)\b", q, re.IGNORECASE)) \
                    and cible is not None and cible in self.compteurs \
                    and not re.search(_RETRAIT + "|" + _AJOUT + "|" + _PARTAGE, ctx):
                self.compteurs[cible] /= n
                self.etapes.append(f"« {ctx.strip()[-40:]} » → ÷{n:g} (vitesse) = "
                                   f"{self.compteurs[cible]:g}")
                continue

            # 3. partage : « equally among N children » → division
            if re.search(_PARTAGE, ctx) and cible is not None \
                    and cible in self.compteurs:
                self.compteurs[cible] /= n
                self.etapes.append(f"« {ctx.strip()[-40:]} » → ÷{n:g} = "
                                   f"{self.compteurs[cible]:g}")
                continue

            # 4. retrait / ajout / initialisation (avec momentum).
            # Les actions ne s'appliquent à un compteur NON initialisé que si
            # le verbe est PROCHE du nombre (« bakes 24 cookies and gives away
            # 3/4 » : le « gives away » du 3/4 ne doit pas toucher le 24).
            ctx_proche = q[max(0, m.start() - 25): m.end() + 15]
            retrait_proche = re.search(_RETRAIT, ctx_proche)
            ajout_proche = re.search(_AJOUT, ctx_proche)
            if retrait_proche or (re.search(_RETRAIT, ctx) and cible is not None
                                  and cible in self.compteurs):
                if cible is not None and cible in self.compteurs:
                    self.compteurs[cible] -= n
                    self.derniere_action = "soustraction"
                    self.etapes.append(f"« {ctx.strip()[-40:]} » → −{n:g} = "
                                       f"{self.compteurs[cible]:g}")
                elif cible is None and self.derniere_action == "soustraction" \
                        and len(self.compteurs) == 1:
                    cle = next(iter(self.compteurs))
                    self.compteurs[cle] -= n
                    self.etapes.append(f"« {ctx.strip()[-40:]} » → −{n:g} (momentum) = "
                                       f"{self.compteurs[cle]:g}")
            elif ajout_proche or (re.search(_AJOUT, ctx) and cible is not None
                                  and cible in self.compteurs):
                self.compteurs[cible] = self.compteurs.get(cible, 0.0) + n
                self.derniere_action = "addition"
                self.etapes.append(f"« {ctx.strip()[-40:]} » → +{n:g} = "
                                   f"{self.compteurs[cible]:g}")
            elif cible is not None and cible in self.compteurs \
                    and self.derniere_action:
                # momentum : objet implicite, dernière action rejouée (Janet « with 4 »)
                if self.derniere_action == "soustraction":
                    self.compteurs[cible] -= n
                    self.etapes.append(f"« {ctx.strip()[-40:]} » → −{n:g} (momentum) = "
                                       f"{self.compteurs[cible]:g}")
                else:
                    self.compteurs[cible] += n
                    self.etapes.append(f"« {ctx.strip()[-40:]} » → +{n:g} (momentum) = "
                                       f"{self.compteurs[cible]:g}")
            else:
                # initialisation : « lay 16 eggs per day », « there are 12 pencils in a box »
                # (jamais d'écrasement : un compteur existant sans action = distracteur)
                if objet in self.compteurs:
                    continue
                self.compteurs[objet] = n
                self.etapes.append(f"« {ctx.strip()[-40:]} » → {objet} = {n:g}")
                if re.search(r"\bin a|in each|per\b", ctx):
                    self.densites[objet] = n     # contenu d'un conteneur

        if not self.compteurs:
            return None
        # garde-fou de confiance (strict) : la machine ne répond que si elle a
        # compris TOUS les nombres à traiter (les nombres hors densité skip sont
        # exclus) — sinon elle rend la main au pipeline par résonance
        a_traiter = len(matches) - len(densites_skippees)
        if len(self.etapes) < a_traiter:
            return None

        # réponse : l'objet interrogé dans la question finale
        derniere_phrase = _derniere_phrase(q)
        cible_finale = _objet_de(derniere_phrase)
        if cible_finale is not None and cible_finale in self.compteurs:
            valeur = self.compteurs[cible_finale]
        else:
            cle = list(self.compteurs.keys())[-1]
            valeur = self.compteurs[cle]
        return self._paquet(question, valeur, "machine_etats")

    # ── équations relatives ─────────────────────────────────────────────
    def _equations_relatives(self, q: str) -> Optional[Dict[str, Any]]:
        """« A has twice as many X as B » / « A has k times as many X as B »,
        base « if C has n X » → propager et répondre (somme si « together »)."""
        relations: Dict[str, Tuple[str, float]] = {}
        objet_rel: Optional[str] = None
        for m in re.finditer(
                r"([A-Z]\w*)\s+has\s+(twice|half)\s+as\s+many\s+([a-z]+)\s+as\s+([A-Z]\w*)",
                q):
            a, k, obj, b = m.group(1), m.group(2), m.group(3), m.group(4)
            relations[a] = (b, 2.0 if k == "twice" else 0.5)
            objet_rel = obj
        for m in re.finditer(
                r"([A-Z]\w*)\s+has\s+(\d+)\s+times\s+as\s+many\s+([a-z]+)\s+as\s+([A-Z]\w*)",
                q):
            relations[m.group(1)] = (m.group(4), float(m.group(2)))
            objet_rel = m.group(3)
        if not relations:
            return None
        bases: Dict[str, float] = {}
        for m in re.finditer(r"\bif\s+([A-Z]\w*)\s+has\s+(\d+(?:[.,]\d+)?)\s+([a-z]+)",
                             q):
            bases[m.group(1)] = float(m.group(2).replace(",", "."))
        if not bases:
            return None
        valeurs = dict(bases)
        for _ in range(len(relations) + 1):
            for a, (b, k) in relations.items():
                if b in valeurs and a not in valeurs:
                    valeurs[a] = valeurs[b] * k
        # réponse : somme des entités si « together », sinon l'entité demandée
        if re.search(r"\b(together|ensemble|total)\b", q, re.IGNORECASE):
            connues = [v for v in valeurs.values()]
        else:
            fin = q.rstrip("? ").split("?")[-1]
            entites_fin = [m.group(1) for m in
                           re.finditer(r"\b([A-Z]\w*)\b", fin)]
            connues = [valeurs[nom] for nom in entites_fin if nom in valeurs]
        if not connues:
            return None
        total = sum(connues)
        self.etapes = [f"{nom} = {v:g} {objet_rel}" for nom, v in valeurs.items()]
        self.etapes.append(f"total = {total:g}")
        return self._paquet(q, total, "équations relatives")

    # ── aide ────────────────────────────────────────────────────────────
    @staticmethod
    def _paquet(question: str, valeur: float, mode: str) -> Dict[str, Any]:
        affichage = f"{round(valeur):g}" if abs(valeur - round(valeur)) < 1e-9 \
            else f"{round(valeur, 3):g}"
        return {"question": question, "reponse": affichage, "reponse_num": float(valeur),
                "etapes": [], "operations": [mode], "confiances": [1.0],
                "temps_ms": 0, "modele": "langage-ondulatoire-v1 (0 LLM)",
                "moteur": "machine_etats_semantique"}
