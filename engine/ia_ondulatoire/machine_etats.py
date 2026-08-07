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
    "lemon", "lemons", "glue stick", "video game", "lego set", "badge", "stick",
    "cube", "selfie", "like", "like", "lollipop", "egg", "degree", "hour",
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
    """Analyse sémantique typée → compteurs par objet → réponse ciblée.

    v3 : chaque nombre est d'abord TYPÉ (typeur.py : dimension + rôle), puis
    les transitions sont dimension-aware — un taux × une durée multiplie, un
    prix unitaire × une quantité produit un montant, une année est ignorée.
    """

    def __init__(self):
        self.compteurs: Dict[str, float] = {}
        self.densites: Dict[str, float] = {}       # objet → quantité par unité
        self.prix: Dict[str, float] = {}           # objet → prix unitaire (monnaie)
        self.montant = 0.0                         # compteur monétaire courant
        self.etapes: List[str] = []
        self.derniere_action: Optional[str] = None

    # ── le résolveur principal ──────────────────────────────────────────
    def resoudre(self, question: str) -> Optional[Dict[str, Any]]:
        """Retourne None si l'analyse échoue (fallback ondulatoire)."""
        from typeur import typer, CONVERSIONS_MONNAIE
        q = _numeriser(question)
        self.compteurs = {}
        self.densites = {}
        self.prix = {}
        self.montant = 0.0
        self.etapes = []
        self.derniere_action = None

        # passe 0 : équations relatives (« A has k times as many X as B »)
        relatif = self._equations_relatives(q)
        if relatif is not None:
            return relatif

        # passe 0b : nénuphar — croissance géométrique « double chaque jour,
        # couvre en N jours, quand la moitié ? » → N − 1 (la veille)
        if re.search(r"\b(doubles?|double)\b", q, re.IGNORECASE):
            m_jours = re.search(r"\b(?:en|in)\s+(\d+)\s+(?:jours?|days?)\b",
                                q, re.IGNORECASE)
            if m_jours and re.search(r"\b(moitié|moitie|half)\b", q, re.IGNORECASE):
                self.etapes = [f"« double chaque jour » → moitié la veille : "
                               f"{m_jours.group(1)} − 1"]
                return self._paquet(q, float(m_jours.group(1)) - 1,
                                    "machine_etats:nénuphar")

        # passe 1 : le TYPEUR traduit le texte en nombres typés
        nombres = [n for n in typer(question) if not n.ignore]
        if not nombres:
            return None
        traites = 0

        for n in nombres:
            ctx = n.contexte or ""
            # ── fraction : « 3/4 of the cookies », « 25% discount » ──────
            if n.role == "fraction":
                cible = self._cible(n.objet)
                if cible is not None and cible in self.compteurs:
                    if re.search(_RETRAIT, ctx):
                        self.compteurs[cible] *= 1 - n.valeur
                    elif re.search(r"\b(increase|gain|profit|earn|gagne|augmente)\b",
                                   ctx, re.IGNORECASE):
                        self.compteurs[cible] *= 1 + n.valeur
                    else:
                        self.compteurs[cible] *= n.valeur
                    self.etapes.append(f"« {ctx.strip()[-38:]} » → ×{n.valeur:g} = "
                                       f"{self.compteurs[cible]:g}")
                    traites += 1
                elif self.montant:               # « costs 40$ with a 25% discount »
                    if re.search(r"\b(discount|off|baisse|perd|decrease|reduces?)\b",
                                 ctx, re.IGNORECASE):
                        self.montant *= 1 - n.valeur
                    else:
                        self.montant *= n.valeur
                    self.etapes.append(f"« {ctx.strip()[-38:]} » → ×{n.valeur:g} "
                                       f"(montant) = {self.montant:g} $")
                    traites += 1
                continue

            # ── taux : « 16 eggs per day », « 60 miles per hour » ────────
            if n.role == "taux":
                if n.dimension == "monnaie":
                    self.prix["default"] = n.valeur * CONVERSIONS_MONNAIE.get(n.unite, 1.0)
                else:
                    objet = n.objet or (n.unite if n.dimension == "objet" else "")
                    if objet:
                        self.densites[objet] = n.valeur
                        self.compteurs.setdefault(objet, n.valeur)
                        self.etapes.append(f"« densité » → {n.valeur:g} {objet}/unité")
                traites += 1
                continue

            # ── durée / incrément : « for 3 hours » → densité × durée ;
            #    avec un taux horaire (« earns 50$/hour, 6 hours ») → montant
            if n.role in ("duree", "increment"):
                if self.prix:
                    self.montant += self.prix.get("default", 0.0) * n.valeur
                    self.etapes.append(f"« {ctx.strip()[-38:]} » → {n.valeur:g} h × "
                                       f"{self.prix.get('default', 0):g} $ = "
                                       f"{self.montant:g} $")
                    traites += 1
                elif self.densites:
                    contenu = next(iter(self.densites))
                    if contenu in self.compteurs:
                        self.compteurs[contenu] *= n.valeur
                    else:
                        self.compteurs[contenu] = self.densites[contenu] * n.valeur
                    self.etapes.append(f"« {ctx.strip()[-38:]} » → ×{n.valeur:g} "
                                       f"({n.unite}) = {self.compteurs[contenu]:g}")
                    traites += 1
                continue

            # ── facteur : « 3 times », « 3 sprints » → multiplie ─────────
            if n.role == "facteur":
                if self.densites:
                    contenu = next(iter(self.densites))
                    self.compteurs[contenu] = self.compteurs.get(
                        contenu, self.densites[contenu]) * n.valeur
                    self.etapes.append(f"« {ctx.strip()[-38:]} » → ×{n.valeur:g} "
                                       f"(facteur) = {self.compteurs[contenu]:g}")
                    traites += 1
                elif len(self.compteurs) == 1:
                    cle = next(iter(self.compteurs))
                    self.compteurs[cle] *= n.valeur
                    traites += 1
                continue

            # ── prix unitaire : « for $2 each » → prix[objet] ────────────
            if n.role == "prix_unitaire":
                self.prix[n.objet or "default"] = n.valeur \
                    * CONVERSIONS_MONNAIE.get(n.unite, 1.0)
                self.etapes.append(f"« {ctx.strip()[-38:]} » → prix {n.valeur:g} $")
                traites += 1
                continue

            # ── montant : « earns 50 dollars », « 5 quarters », « $20000 » ─
            if n.role == "montant":
                v = n.valeur * CONVERSIONS_MONNAIE.get(n.unite, 1.0)
                # la dépense/le gain se décide dans la PHRASE du nombre
                # (« buys a can for 55 cents » = retrait ; « has 5 quarters » = ajout)
                phrase_n = q[:n.position].rpartition(". ")[2] + q[n.position:]
                phrase_n = phrase_n.split(".")[0] if "." in phrase_n else phrase_n
                if re.search(r"\b(buys?|bought|pays?|paid|spends?|spent|"
                             r"saves?|save|dépense|depense|dépensé|withheld|"
                             r"withdraws?|donates?)\b", phrase_n, re.IGNORECASE):
                    self.montant -= v
                    action = "−"
                else:
                    self.montant += v
                    action = "+"
                self.etapes.append(f"« {ctx.strip()[-38:]} » → {action}{v:g} $ "
                                   f"= {self.montant:g} $")
                traites += 1
                continue

            # ── quantite : init / retrait / ajout / momentum ─────────────
            phrase_n = q[:n.position].rpartition(". ")[2] + q[n.position:]
            if re.search(_PARTAGE, ctx + " " + phrase_n) and self.montant:
                self.montant /= n.valeur          # « partage 500 francs entre 4 »
                self.etapes.append(f"« {ctx.strip()[-38:]} » → ÷{n.valeur:g} = "
                                   f"{self.montant:g} $")
                traites += 1
            elif self._transition_quantite(q, n, ctx):
                traites += 1

        # motifs spéciaux sans nombre : « half that much », « twice as many »
        if self.compteurs or self.montant:
            for phrase in re.split(r"(?<=[.!?])\s+|\n+", q):
                if re.search(r"\bhalf (that|as) much\b", phrase, re.IGNORECASE):
                    if self.compteurs:
                        cle = next(iter(self.compteurs))
                        self.compteurs[cle] *= 1.5
                        self.etapes.append("« half that much » → ×1.5 = "
                                           f"{self.compteurs[cle]:g}")
                    else:
                        self.montant *= 1.5
                        self.etapes.append("« half that much » → ×1.5 = "
                                           f"{self.montant:g} $")
                    break
                if re.search(r"\btwice as many\b", phrase, re.IGNORECASE) \
                        and self.compteurs:
                    cle = next(iter(self.compteurs))
                    self.compteurs[cle] *= 2
                    self.etapes.append("« twice as many » → ×2 = "
                                       f"{self.compteurs[cle]:g}")
                    break

        # garde-fou de confiance : la machine ne répond que si elle a compris
        # TOUS les nombres de l'énoncé (sinon → fallback résonance)
        if traites < len(nombres):
            return None

        # réponse finale : montant ou objet demandé
        reponse = self._reponse_finale(q)
        if reponse is None:
            return None
        return self._paquet(question, reponse, "machine_etats")

    # ── transition d'une quantité (comportement v2 conservé) ────────────
    def _transition_quantite(self, q: str, n, ctx: str) -> bool:
        """Retourne True si la transition a été appliquée (compréhension)."""
        # ── conteneur : « buys 5 boxes » avec « 12 pencils in a box » → densité × n
        if n.objet in CONTENEURS and self.densites \
                and not re.search(_RETRAIT, ctx):
            contenu = next(iter(self.densites))
            if contenu in self.compteurs:
                self.compteurs[contenu] *= n.valeur
            else:
                self.compteurs[contenu] = self.densites[contenu] * n.valeur
            self.etapes.append(f"« {ctx.strip()[-38:]} » → densité ×{n.valeur:g} "
                               f"= {self.compteurs[contenu]:g}")
            return True
        # ── partage : « equally among 5 children » → division ────────────
        if re.search(_PARTAGE, ctx) and len(self.compteurs) == 1:
            cle = next(iter(self.compteurs))
            self.compteurs[cle] /= n.valeur
            self.etapes.append(f"« {ctx.strip()[-38:]} » → ÷{n.valeur:g} = "
                               f"{self.compteurs[cle]:g}")
            return True
        # ── coût total : « combien coûtent 4 cahiers » → prix × 4 ───────
        if re.search(r"\b(combien coûtent|combien coutent|how much do|"
                     r"how much does|cost in total)\b", ctx, re.IGNORECASE):
            if self.prix:
                self.montant = n.valeur * self.prix.get("default", 0.0)
                self.etapes.append(f"« {ctx.strip()[-38:]} » → {n.valeur:g} × "
                                   f"{self.prix.get('default', 0):g} $ = "
                                   f"{self.montant:g} $")
                return True
            if len(self.compteurs) == 1:
                cle = next(iter(self.compteurs))
                self.compteurs[cle] *= n.valeur
                self.etapes.append(f"« {ctx.strip()[-38:]} » → ×{n.valeur:g} (coût) = "
                                   f"{self.compteurs[cle]:g}")
                return True
        # ── conversion interne : « cut each pie into 8 pieces » → 5×8 ───
        m_cut = re.search(
            r"\b(cut|divided|split|broke)\s+(?:each|the)\s+([a-zà-ü]+)\s+into\s+"
            r"(\d+(?:[.,]\d+)?)\s+([a-zà-ü]+)", ctx, re.IGNORECASE)
        if m_cut:
            from typeur import _trouver_objet_texte
            source = _objet_de(m_cut.group(2))
            cible_cut = _objet_de(m_cut.group(4))
            if source is not None and source not in self.compteurs \
                    and len(self.compteurs) == 1:
                source = next(iter(self.compteurs))   # « 5 apple pies » → pie
            if source is not None and source in self.compteurs and cible_cut:
                self.compteurs[cible_cut] = self.compteurs[source] \
                    * float(m_cut.group(3))
                self.etapes.append(f"« {ctx.strip()[-38:]} » → {source} ×"
                                   f"{m_cut.group(3)} = {self.compteurs[cible_cut]:g}")
                return True
        # ── distribution : « give each student 2 glue sticks » → 27×2 ───
        m_dist = re.search(
            r"\b(give|gives|bought|buys|needs)\s+(?:each|every)\s+([a-zà-ü]+)\s+"
            r"(\d+(?:[.,]\d+)?)\s+([a-zà-ü]+(?:\s+[a-zà-ü]+)?)", ctx, re.IGNORECASE)
        if m_dist:
            donne = _objet_de(m_dist.group(2))
            recu = _objet_de(m_dist.group(4))
            if donne is not None and donne in self.compteurs and recu is not None:
                self.compteurs[recu] = self.compteurs[donne] * float(m_dist.group(3))
                self.etapes.append(f"« {ctx.strip()[-38:]} » → {donne} ×"
                                   f"{m_dist.group(3)} = {self.compteurs[recu]:g}")
                return True
        # ── « N were left » après un état → retrait (« 14 pieces were left »)
        if re.search(r"\b(?:were\s+\d+(?:[.,]\d+)?\s+[a-zà-ü]+\s+left|"
                     r"\d+(?:[.,]\d+)?\s+[a-zà-ü]+\s+were\s+left)\b", ctx) \
                and (len(self.compteurs) == 1
                     or (n.objet is not None and n.objet in self.compteurs)) \
                and not re.search(r"\bleft\b", _derniere_phrase(q)):
            cle = n.objet if n.objet in self.compteurs else next(iter(self.compteurs))
            self.compteurs[cle] -= n.valeur
            self.etapes.append(f"« {ctx.strip()[-38:]} » → −{n.valeur:g} (restant) = "
                               f"{self.compteurs[cle]:g}")
            return True
        # ── paquets : « come in packs of 8 » → ceil(quantité / 8) ───────
        if re.search(r"\bin packs?\s+of\b", ctx):
            import math as _math
            objets = {k: v for k, v in self.compteurs.items() if k != "pack"}
            if objets:
                cle = max(objets, key=objets.get)
                self.compteurs["pack"] = _math.ceil(objets[cle] / n.valeur)
                self.etapes.append(f"« {ctx.strip()[-38:]} » → packs = ceil("
                                   f"{objets[cle]:g} ÷ {n.valeur:g}) = "
                                   f"{self.compteurs['pack']:g}")
                return True
        objet = n.objet or None
        if objet is None:
            objet = self._objet_implicite(ctx)
            if objet is None:
                return False
        cible = objet if objet in self.compteurs else (
            next(iter(self.compteurs)) if len(self.compteurs) == 1 else None)
        if cible is None and objet not in self.compteurs:
            cible = objet
        retrait_proche = re.search(_RETRAIT, ctx)
        ajout_proche = re.search(_AJOUT, ctx)
        if retrait_proche and cible is not None and cible in self.compteurs:
            self.compteurs[cible] -= n.valeur
            self.derniere_action = "soustraction"
            self.etapes.append(f"« {ctx.strip()[-38:]} » → −{n.valeur:g} = "
                               f"{self.compteurs[cible]:g}")
            return True
        if ajout_proche:
            self.compteurs[cible] = self.compteurs.get(cible, 0.0) + n.valeur
            self.derniere_action = "addition"
            self.etapes.append(f"« {ctx.strip()[-38:]} » → +{n.valeur:g} = "
                               f"{self.compteurs[cible]:g}")
            return True
        if cible is not None and cible in self.compteurs and self.derniere_action:
            if self.derniere_action == "soustraction":
                self.compteurs[cible] -= n.valeur
                self.etapes.append(f"« {ctx.strip()[-38:]} » → −{n.valeur:g} (momentum) = "
                                   f"{self.compteurs[cible]:g}")
            else:
                self.compteurs[cible] += n.valeur
                self.etapes.append(f"« {ctx.strip()[-38:]} » → +{n.valeur:g} (momentum) = "
                                   f"{self.compteurs[cible]:g}")
            return True
        if objet not in self.compteurs:
            self.compteurs[objet] = n.valeur
            self.etapes.append(f"« {ctx.strip()[-38:]} » → {objet} = {n.valeur:g}")
            if re.search(r"\bin a|in each|per\b", ctx):
                self.densites[objet] = n.valeur
            return True
        return False

    def _objet_implicite(self, ctx: str) -> Optional[str]:
        """Action sans objet local (« eats 3 ») : mono-compteur → l'objet unique."""
        if len(self.compteurs) == 1 and (re.search(_RETRAIT, ctx)
                                         or re.search(_AJOUT, ctx)):
            return next(iter(self.compteurs))
        return None

    def _cible(self, objet: Optional[str]) -> Optional[str]:
        """Objet cible d'une opération : le compteur de l'objet, ou le mono-compteur."""
        if objet is not None and objet in self.compteurs:
            return objet
        if len(self.compteurs) == 1:
            return next(iter(self.compteurs))
        return None

    def _reponse_finale(self, q: str) -> Optional[float]:
        """Montant (si demandé) ou compteur de l'objet de la question finale."""
        from typeur import CONVERSIONS_MONNAIE
        derniere = _derniere_phrase(q)
        # 1. demande monétaire → montant (objet × prix unitaire, sinon compteur $)
        if re.search(r"\b(in dollars|dollars|cents|money|pay|profit|earn|make|"
                     r"cost|francs|euros|net|coûtent|coutent|value|worth)\b",
                     derniere, re.IGNORECASE) \
                or (self.montant and self.prix):
            # unité monétaire demandée (« cents » → ×100)
            for unite, facteur in CONVERSIONS_MONNAIE.items():
                if unite and re.search(rf"\b{unite}s?\b", derniere):
                    return self.montant / facteur if self.montant else None
            if self.prix:
                for objet, prix in self.prix.items():
                    if objet in self.compteurs:
                        return self.compteurs[objet] * prix
            return self.montant if self.montant else None
        # 2. objet de la question finale (détection directe)
        objet_final = _objet_de(derniere)
        if objet_final is not None and objet_final in self.compteurs:
            return self.compteurs[objet_final]
        # 3. dernier compteur
        if self.compteurs:
            return self.compteurs[list(self.compteurs.keys())[-1]]
        return None

    # ── le résolveur principal ──────────────────────────────────────────
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
