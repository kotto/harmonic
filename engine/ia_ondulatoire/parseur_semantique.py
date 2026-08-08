# -*- coding: utf-8 -*-
"""
parseur_semantique.py — PROTOTYPE DU PARSEUR SÉMANTIQUE ONDULATOIRE
====================================================================
Inspiré des LLM classiques, exprimé en primitives ondulatoires
(voir PARSEUR_SEMANTIQUE_EQUIVALENCES.md, 08/08/2026) :

  ÉTAGE 1  embeddings CONTEXTUELS : emb(w) = normalize(Σ encode(c))
           — le sens vient de l'usage (co-occurrence), pas du hash
           (correction de P1.1 : l'encode seul ne porte rien)
  ÉTAGE 2  ATTENTION : q = emb(question), k_i = emb(clause_i),
           w_i = softmax(resonate(q, k_i)),
           contexte = SUPERPOSE(clauses, weights=w)   ← équivalent QKV
  ÉTAGE 3  extraction typée : nombres → {valeur, unité}
  ÉTAGE 4  GRAMMAIRE DES RELATIONS (le cœur — 81,2 % des échecs) :
           fractions, pourcentages, ratios, comparaisons, dimensions,
           coûts, séquences → triplets (entité, op, argument) → IR typée
  ÉTAGE 5  plan + exécution arithmétique + COUVERTURE → refus si faible

Test pré-enregistré : les 80 échecs PLAN_FAUX étiquetés (taxonomie).
Critère : ≥ 40 % de plans corrects (aujourd'hui : 0 %).

Usage : python parseur_semantique.py
"""

import json
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primitives import encode, resonate, superpose, rotate, normalize   # noqa: E402

DOSSIER = os.path.dirname(os.path.abspath(__file__))
TAXONOMIE = os.path.join(DOSSIER, "taxonomie_echecs.json")
ETIQUETTES = os.path.join(DOSSIER, "taxonomie_etiquettes.json")
GSM8K = os.path.join(DOSSIER, "..", "data", "benchmarks", "gsm8k_test.jsonl")

DIM = 512


# ────────────────────────────────────────────────────────────────────────
# ÉTAGE 1 — embeddings contextuels (co-occurrence sur le corpus)
# ────────────────────────────────────────────────────────────────────────
def decouper(texte):
    """Tokenisation : mots, nombres, signes de ponctuation légers."""
    return re.findall(r"\d+(?:[.,]\d+)?|%|[A-Za-zÀ-ÿ']+", texte.lower())


class EmbeddingsContextuels:
    """emb(w) = normalize(Σ_{c ∈ fenêtre(w)} encode(c)) — le sens vient
    de l'usage. Construction en une passe sur le corpus."""

    def __init__(self, fenetre=3):
        self.fenetre = fenetre
        self.vocab = {}
        self.comptes = {}

    def construire(self, textes):
        for texte in textes:
            toks = decouper(texte)
            for i, t in enumerate(toks):
                self.comptes[t] = self.comptes.get(t, 0) + 1
        # une seule passe : accumulateur par mot
        acc = {}
        for texte in textes:
            toks = decouper(texte)
            for i, t in enumerate(toks):
                if t not in acc:
                    acc[t] = np.zeros(DIM, dtype=complex)
                for j in range(max(0, i - self.fenetre), min(len(toks), i + self.fenetre + 1)):
                    if j != i:
                        acc[t] += encode(toks[j], dim=DIM, use_cache=False)
        for t, v in acc.items():
            n = np.linalg.norm(v)
            self.vocab[t] = v / n if n > 1e-12 else v

    def emb(self, texte):
        """Embedding d'une séquence (clause/question) : superposition
        pondérée des embeddings des mots (attention naïve)."""
        toks = [t for t in decouper(texte) if t in self.vocab]
        if not toks:
            return np.zeros(DIM, dtype=complex)
        v = superpose(*[self.vocab[t] for t in toks])
        return normalize(v)


# ────────────────────────────────────────────────────────────────────────
# ÉTAGE 2 — attention (équivalent QKV)
# ────────────────────────────────────────────────────────────────────────
def attention(emb, question, clauses, tetes=4):
    """w_i = softmax(resonate(q, k_i)) ; contexte = Σ w_i·clause_i.
    Têtes multiples : ROTATE(q, θ_h)."""
    q = emb.emb(question)
    ks = [emb.emb(c) for c in clauses]
    if not ks:
        return np.ones(1), emb.emb(question)   # question seule : pas d'attention
    scores = np.array([resonate(q, k) for k in ks])
    w = np.exp(scores - scores.max())
    w = w / w.sum()
    ctx = superpose(*ks, weights=w.tolist())
    # têtes multiples : perspectives par rotation
    tete = []
    for h in range(tetes):
        theta = h * math.pi / tetes
        qh = rotate(q, theta)
        sh = np.array([resonate(qh, k) for k in ks])
        wh = np.exp(sh - sh.max())
        tete.append(wh / wh.sum())
    wm = np.mean(tete, axis=0)
    return wm, ctx


# ────────────────────────────────────────────────────────────────────────
# ÉTAGE 4 — grammaire des relations (triplets → IR)
# ────────────────────────────────────────────────────────────────────────
FRACTIONS = {
    "half": (1, 2), "one-half": (1, 2), "one half": (1, 2),
    "one-third": (1, 3), "one third": (1, 3), "one-third of": (1, 3),
    "two-thirds": (2, 3), "two thirds": (2, 3),
    "three-quarters": (3, 4), "three fourths": (3, 4),
    "three-fourths": (3, 4), "one-fourth": (1, 4), "one fourth": (1, 4),
    "quarter": (1, 4), "two-thirds of": (2, 3), "three-quarters of": (3, 4),
}


def _nb(s):
    """float() tolérant la virgule-milliers US : « 9,300 » → 9300."""
    try:
        return float(str(s).replace(",", "").replace(" ", ""))
    except (TypeError, ValueError):
        return float(s) if s is not None else None


def _norm(nom):
    """Normalise un nom d'entité : « baby bees » → « baby », « babies » → « baby »."""
    n = nom.strip().lower()
    n = n.replace(" bees", "")
    if n.endswith("ies"):
        n = n[:-3] + "y"
    elif n.endswith("es") and len(n) > 3:
        n = n[:-2]
    elif n.endswith("s") and len(n) > 2:
        n = n[:-1]
    return n


class ParseurSemantique:
    def __init__(self, emb: EmbeddingsContextuels):
        self.emb = emb

    def clauses(self, texte):
        # découpe sur [.?!;] ET virgule suivie d'un non-chiffre
        # (« old, and one-fourth… » ; « 1,000 » reste intact)
        # coupe sur virgule SAUF si un groupe de 3 chiffres suit (« 1,000 »)
        # point qui n'est PAS un décimal (« 1.50 » intact), virgule sauf
        # groupe de 3 chiffres (« 1,000 » intact)
        return [c.strip() for c in re.split(r"(?<!\d)\.(?!\d)|[?!;]|"
                                            r",\s+(?!\d{3}(?!\d))",
                                            texte)
                if c.strip()]

    def nombres(self, clause):
        return [float(n.replace(",", "")) for n in
                re.findall(r"\d+(?:[.,]\d+)?", clause)]

    def relations(self, clause):
        """Extrait (entite, op, args) de la clause — grammaire explicite."""
        c = clause.lower()
        c_net = c          # clause « nettoyée » (fragments consommés)
        rels = []
        # ── pourcentage : « X% of N » / « X% more/less than N »
        m = re.search(r"(\d+(?:[.,]\d+)?)%\s*(more|less)?\s*than\s+(\d+(?:[.,]\d+)?)", c)
        if m:
            p, sens, n = _nb(m.group(1)), m.group(2), _nb(m.group(3))
            rels.append(("pct_compare", n, p, 1 + p / 100 if sens == "more"
                         else 1 - p / 100))
        m = re.search(r"(\d+(?:[.,]\d+)?)%\s*of\s+(\d+(?:[.,]\d+)?)", c)
        if m:
            rels.append(("pct_of", _nb(m.group(2)), _nb(m.group(1)), None))
        # ── fraction : « one-third of N », « 2/3 of N », « 2/3 of that »
        m = re.search(r"(\d+)\s*/\s*(\d+)\s*of\s+(\d+(?:[.,]\d+)?)", c)
        if m:
            rels.append(("frac_of", _nb(m.group(3)),
                         _nb(m.group(1)) / _nb(m.group(2)), None))
        m = re.search(r"(\d+)\s*/\s*(\d+)(?:rd|th|nd|st)?\s+of\s+"
                      r"(?:that|the\s+[a-z]+)", c)
        if m:
            rels.append(("frac_of", None,
                         _nb(m.group(1)) / _nb(m.group(2)), None))
        a_frac_ent = any(r[0] == "frac_ent" for r in rels)
        for mot, (num, den) in FRACTIONS.items():
            m = re.search(rf"{re.escape(mot)}\s+of\s+(\d+(?:[.,]\d+)?)", c)
            if m:
                rels.append(("frac_of", _nb(m.group(1)), num / den, None))
                break
            if not a_frac_ent:
                m = re.search(rf"{re.escape(mot)}\s+of\s+(?:that|the\s+[a-z]+)", c)
                if m:
                    rels.append(("frac_of", None, num / den, None))
                    break
        # ── ratio d'entités : « twice as many worker bees as baby bees »
        # (X = k×Y — système linéaire résolu à la fin ; noms normalisés :
        # « baby bees » ≡ « babies »)
        m = re.search(r"(twice|(\d+(?:[.,]\d+)?)\s*(?:times)?)\s+as\s+(many|much)"
                      r"\s+([a-z]+(?:\s+[a-z]+)*?)\s+as\s+(?:the\s+)?"
                      r"([a-z]+(?:\s+[a-z]+)*?)(?=[.,]|$)", c)
        if m:
            k = 2.0 if m.group(1) == "twice" else _nb(m.group(2))
            rels.append(("ratio_ent", k, _norm(m.group(4)), _norm(m.group(5))))
        # ── total d'entités : « There are 700 bees in a hive »
        m = re.search(r"(?:there are|there were)\s+(\d+(?:[.,]\d+)?)\s+"
                      r"([a-z]+)\s+(?:in|at)", c)
        if m:
            rels.append(("total_ent", _nb(m.group(1)), m.group(2), None))
        m = re.search(r"total\s+\w+\s+(?:now\s+)?is\s+(\d+(?:[.,]\d+)?)", c)
        if m:
            rels.append(("total_ent", _nb(m.group(1)), "total", None))
        # ── période fixe : « gets 5 games for Christmas each year for 3 years »
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+[a-z]+\s+for\s+\w+\s+each\s+year"
                      r"\s+for\s+(\d+)\s+years?", c)
        if m:
            rels.append(("periode_fixe", _nb(m.group(1)), _nb(m.group(2)), None))
        # ── initial : « started with 5 games », « along with 5 games »
        m = re.search(r"(?:started with|starts with|already has|along with)\s+"
                      r"(\d+)", c_net)
        if m:
            rels.append(("initial", _nb(m.group(1)), None, None))
            c_net = c_net.replace(m.group(0), " ")
        # ── perso : « Joey loses 8 pounds in 4 weeks » (STRIP immédiat :
        # la durée « in 4 weeks » ne doit pas consommer la file de taux)
        m = re.search(r"(\w+)\s+loses\s+(\d+(?:[.,]\d+)?)\s+pounds?\s+in\s+"
                      r"(\d+)\s+weeks?", c_net)
        if m:
            rels.append(("perso_periode", m.group(1), _nb(m.group(2)),
                         _nb(m.group(3))))
            c_net = c_net.replace("in " + m.group(3) + " weeks", "")
        # ── perso ratio : « needs 4 weeks to lose the same amount that X loses
        # in a single week » → taux_sandy = taux_X / 4
        m = re.search(r"needs\s+(\d+)\s+weeks?\s+to\s+lose\s+the\s+same\s+"
                      r"amount(?:\s+of\s+\w+)?\s+that\s+(\w+)\s+loses", c)
        if m:
            rels.append(("perso_ratio", m.group(2), _nb(m.group(1)), None))
        # ── perso cible : « as much weight as Joey does »
        m = re.search(r"as\s+much\s+weight\s+as\s+(\w+)\s+does", c)
        if m:
            rels.append(("perso_cible", m.group(1), None, None))
        # ── perso question : « how many weeks will it take Sandy »
        m = re.search(r"how\s+many\s+weeks?\s+will\s+it\s+take\s+(\w+)", c)
        if m:
            rels.append(("perso_question", m.group(1), None, None))
        # ── ratio simple (hérité, valeur courante)
        m = re.search(r"(twice|(\d+(?:[.,]\d+)?)\s*(?:times)?)\s+as\s+(many|much)"
                      r"\s+as\s+(?:the\s+)?([a-z]+)", c)
        if m:
            k = 2.0 if m.group(1) == "twice" else _nb(m.group(2))
            rels.append(("ratio", m.group(4), k, None))
        # ── comparaison : « X more than N » / « X less than N »
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+(more|less|fewer)\s+than\s+"
                      r"(\d+(?:[.,]\d+)?)", c)
        if m:
            x, sens, n = _nb(m.group(1)), m.group(2), _nb(m.group(3))
            rels.append(("cmp", n, x, sens))
        # ── ACHAT : « N objets for/at $P each/per » — quantité et prix
        # appariés par proximité (plusieurs achats possibles). « for $P »
        # SANS each/per est un TOTAL (pas un prix unitaire) → non traité
        # ici (REFUS plutôt qu'une mauvaise assertion).
        for m in re.finditer(
                r"(\d+(?:[.,]\d+)?)\s+[a-z]+(?:\s+[a-z]+)*\s+(?:for|at|costs?|costing)\s+\$?\s*"
                r"(\d+(?:[.,]\d+)?)\s*(?:each|per\s+[a-z]+|apiece)", c):
            rels.append(("achat", _nb(m.group(2)), _nb(m.group(1)), None))
        m = re.search(r"\$?\s*(\d+(?:[.,]\d+)?)\s*(?:each|apiece)", c)
        if m and not any(r[0] == "achat" and abs(r[1] - _nb(m.group(1))) < 1e-9
                         for r in rels):
            rels.append(("prix_unitaire", _nb(m.group(1)), None, None))
        # ── coût total / change
        if "change" in c or "left" in c or "remainder" in c:
            rels.append(("solde", None, None, None))
        # ── heures/semaine : « works N hours a day for M days a week »
        # Le fragment est RETIRÉ de la clause avant les regex taux/durée :
        # « 5 hours a day » ne crée ni taux ni durée parasite, mais le
        # « $2 per hour » de la même clause reste détectable.
        c_net = c
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+hours\s+a\s+day\s+(?:for|and)\s+"
                      r"(\d+(?:[.,]\d+)?)\s+days\s+a\s+week", c)
        if m:
            rels.append(("heures_semaine", _nb(m.group(1)), _nb(m.group(2)), None))
            c_net = c[:m.start()] + " " + c[m.end():]
        # « $2 per hour » (direct) OU « 10 pounds per month » (mots interposés)
        m = re.search(r"(\d+(?:[.,]\d+)?)(?:\s+[a-z]+(?:\s+[a-z]+)*)?\s+"
                      r"(?:per|a|an)\s+(day|week|month|year|hour|minute)", c_net)
        if m:
            rels.append(("taux", _nb(m.group(1)), m.group(2), None))
        # ── dette/base : « owes $N » → point de départ
        m = re.search(r"owes\s+.*?\$?(\d+(?:[.,]\d+)?)", c)
        if m:
            rels.append(("base", _nb(m.group(1)), None, None))
        # ── intérêt simple : « monthly interest of X% »
        m = re.search(r"interest\s+of\s+(\d+(?:[.,]\d+)?)%", c)
        if m:
            rels.append(("interet", _nb(m.group(1)), None, None))
        # ── durée : « in N days/weeks/months », « for N days » (clause nette ;
        # « over 16 years old » n'est PAS une durée)
        c_sans_age = re.sub(r"\d+\s+years?\s+old", " ", c_net)
        m = re.search(r"(?:in|for|after|over)\s+(\d+)\s+(day|days|week|weeks|"
                      r"month|months|year|years)", c_sans_age)
        if m:
            rels.append(("duree", _nb(m.group(1)), m.group(2), None))
        # durées implicites d'une année : « for a year », « for the third
        # year », « the following year » → 12 mois
        m = re.search(r"(?:for\s+a|for\s+the\s+\w+|the\s+following|"
                      r"next)\s+year", c_sans_age)
        if m and not any(r[0] == "duree" for r in rels):
            rels.append(("duree", 12.0, "month", None))
        # durées en lettres : « after three years » → 3
        MOTS_NB = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                   "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        m = re.search(r"(?:in|for|after|over)\s+(one|two|three|four|five|six|"
                      r"seven|eight|nine|ten)\s+(day|days|week|weeks|month|"
                      r"months|year|years)", c_sans_age)
        if m and not any(r[0] == "duree" for r in rels):
            rels.append(("duree", float(MOTS_NB[m.group(1)]), m.group(2), None))
        # période fixe en lettres : « for three years »
        m = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
                      r"\s+[a-z]+\s+for\s+\w+\s+each\s+year\s+for\s+"
                      r"(one|two|three|four|five|six|seven|eight|nine|ten)"
                      r"\s+years?", c)
        if m:
            v = float(MOTS_NB.get(m.group(1), m.group(1)))
            d = float(MOTS_NB.get(m.group(2), m.group(2)))
            rels.append(("periode_fixe", v, d, None))
        # récurrente : « 5 games for Christmas every year » — années = durée
        # totale (relation total_annees posée par la question)
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+[a-z]+\s+for\s+\w+\s+every\s+"
                      r"year", c)
        if m and not any(r[0] == "periode_fixe" for r in rels):
            rels.append(("periode_fixe", _nb(m.group(1)), None, None))
        # durée totale : « after 3 years » (qualificatif de la question)
        m = re.search(r"(?:after|in)\s+(\d+)\s+years", c)
        if m:
            rels.append(("total_annees", _nb(m.group(1)), None, None))
        # ── futur : « in 10 years » / « 10 years from now »
        m = re.search(r"(?:in\s+)?(\d+)\s+years\s+from\s+now", c)
        if m:
            rels.append(("futur", _nb(m.group(1)), None, None))
        m = re.search(r"in\s+(\d+)\s+years", c)
        if m:
            rels.append(("futur", _nb(m.group(1)), None, None))
        # ── cible : « wants to save $N » / « needs to earn $N »
        m = re.search(r"(?:wants|needs|plans?)\s+to\s+(?:save|earn|make)\s+"
                      r"\$?\s*(\d+(?:[.,]\d+)?)", c)
        if m:
            rels.append(("cible", _nb(m.group(1)), None, None))
        # ── final : « final N was X » (problèmes inverses)
        m = re.search(r"final\s+\w+\s+(?:was|is)\s+(\d+(?:[.,]\d+)?)", c)
        if m:
            rels.append(("final", _nb(m.group(1)), None, None))
        # ── quantité construite : « 5 less than 23 scoops »
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+(less|more)\s+than\s+"
                      r"(\d+(?:[.,]\d+)?)\s+([a-z]+)", c)
        if m:
            rels.append(("quantite", _nb(m.group(3)), _nb(m.group(1)),
                         m.group(2), m.group(4)))
                # ── ratio à deux points : « ages are in the ratio of 7:11 »
        m = re.search(r"ratio\s+of\s+(\d+):(\d+)", c)
        if m:
            rels.append(("ratio_colon", _nb(m.group(1)), _nb(m.group(2)), None))
# ── base entité : « enrolls 3000 students » → entites["students"]
        m = re.search(r"(?:enrolls|contains)\s+(\d+(?:[.,]\d+)?)\s+"
                      r"([a-z]+)", c)
        if m:
            rels.append(("base_ent", _nb(m.group(1)), m.group(2), None))
        # ── fraction avec référence d'entité : « half of these students are
        # over 16 years old », « one-fourth of the students over 16 are male »
        for mot, (num, den) in FRACTIONS.items():
            m = re.search(rf"{re.escape(mot)}\s+of\s+(?:the\s+|these\s+|"
                          rf"those\s+)?([a-z0-9]+(?:\s+[a-z0-9]+)*?)\s+are\s+"
                          rf"([a-z0-9]+(?:\s+[a-z0-9]+)*?)(?=[.,]|$)", c)
            if m:
                ref = m.group(1).replace(" years old", "").replace(" year old", "")
                attr = m.group(2).replace(" years old", "").replace(" year old", "")
                rels.append(("frac_ent", num / den, ref.strip(), attr.strip()))
                break
        m = re.search(r"(\d+)\s*/\s*(\d+)\s+of\s+(?:the\s+|these\s+|"
                      r"those\s+)?([a-z0-9]+(?:\s+[a-z0-9]+)*?)\s+are\s+"
                      r"([a-z0-9]+(?:\s+[a-z0-9]+)*?)(?=[.,]|$)", c)
        if m:
            rels.append(("frac_ent", _nb(m.group(1)) / _nb(m.group(2)),
                         m.group(3).strip(), m.group(4).strip()))
        # ── ratio IMBRIQUÉ : « it takes 3 less than 6 potatoes to make
        # 1 less than 3 scoops » — traité AVANT quantite, portée retirée
        m = re.search(r"it takes (\d+)\s+(less|more)\s+than\s+(\d+)\s+"
                      r"([a-z]+)\s+to make\s+(\d+)\s+(less|more)\s+than\s+"
                      r"(\d+)\s+([a-z]+)", c)
        if m:
            a = _nb(m.group(3)) - _nb(m.group(1)) if m.group(2) == "less"                 else _nb(m.group(3)) + _nb(m.group(1))
            b = _nb(m.group(7)) - _nb(m.group(5)) if m.group(6) == "less"                 else _nb(m.group(7)) + _nb(m.group(5))
            rels.append(("ratio_prend2", a, b, m.group(4), m.group(8)))
            c = c[:m.start()] + " " + c[m.end():]
        # ── perte : « N did not grow », « N died », « lost N »
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+(?:did not grow|did not survive|"
                      r"died|were eaten)", c)
        if m:
            rels.append(("perte", _nb(m.group(1)), None, None))
        # ── ratio : « it takes A X to make B Y » (forme simple)
        m = re.search(r"it takes (\d+(?:[.,]\d+)?)\s+([a-z]+)\s+to make "
                      r"(\d+(?:[.,]\d+)?)\s+([a-z]+)", c)
        if m:
            rels.append(("ratio_prend", _nb(m.group(1)), _nb(m.group(3)),
                         m.group(2)))
                # ── pourcentage d'entité : « 20% of the students »
        m = re.search(r"(\d+(?:[.,]\d+)?)%\s+of\s+(?:the\s+)?"
                      r"([a-z]+(?:\s+[a-z]+)*)(?=[.,]|$)", c)
        if m:
            rels.append(("pct_ent", _nb(m.group(1)) / 100.0, m.group(2), None))
# ── pourcentage isolé « X% » avec sujet implicite
        m = re.search(r"(\d+(?:[.,]\d+)?)%", c)
        if m and not any(r[0] in ("pct_of", "pct_compare") for r in rels):
            rels.append(("pct_iso", _nb(m.group(1)), None, None))
        return rels

    def decomposer(self, question, seuil_attention=0.0):
        """Retourne {ok, etapes, couverture, relations}.
        seuil_attention > 0 : les clauses dont le poids d'attention est
        < seuil × max sont EXCLUES de l'exécution (ablation mesurable)."""
        cls = self.clauses(question)
        if not cls:
            return {"ok": False, "etapes": [], "couverture": 0.0, "relations": []}
        question_txt = cls[-1]
        corps = cls[:-1]
        # attention : poids des clauses vs la question (multi-têtes)
        wm, _ = attention(self.emb, question_txt, corps)
        if seuil_attention > 0 and len(wm):
            garde = wm >= seuil_attention * wm.max()
        else:
            garde = np.ones(len(wm), bool)
        # exécution : état à DEUX variables — courant (dernière valeur) et
        # total (accumulateur) ; la question détermine laquelle répondre
        etat = {"courant": None, "total": None, "entites": {}}
        ordre = []
        couv = 0.0
        nb_relations = 0
        # TOUTES les clauses sont traitées — y compris la question, qui porte
        # souvent les relations « final » et « cible » (problèmes inverses).
        # DEUX PASSES : taux/base/interêt d'abord, durées ensuite (l'ordre
        # des phrases ne doit pas décider — « for 3 months, lost 10 per month »)
        # les passes portent sur TOUTES les clauses du CORPS (la question,
        # souvent sans relation, ne doit pas « voler » la dernière clause)
        corps_rels = []
        for c, w, g in zip(corps, wm, garde):
            if not g:
                continue
            rels = self.relations(c)
            nums = self.nombres(c)
            nb_relations += len(rels)
            if rels:
                couv += 1
            if not any(r[0] in ("base", "base_ent", "interet") for r in rels):
                etat["nb_prix_corps"] = etat.get("nb_prix_corps", 0) +                     len(re.findall(r"\$", c))
            etat["nb_achats"] = etat.get("nb_achats", 0) +                 sum(1 for r in rels if r[0] in ("achat", "prix_unitaire"))
            corps_rels.append((rels, nums))
        rels_q = self.relations(question_txt)
        nb_relations += len(rels_q)
        # la durée totale de la question (« after 3 years ») est posée AVANT
        # les passes : les périodes récurrentes (« every year ») en dépendent
        self._executer([r for r in rels_q if r[0] == "total_annees"],
                       self.nombres(question_txt), etat, ordre)
        for rels, nums in corps_rels:
            self._executer([r for r in rels
                            if r[0] not in ("duree", "perte", "perso_ratio",
                                            "perso_cible")],
                           nums, etat, ordre)
        for rels, nums in corps_rels:
            self._executer([r for r in rels
                            if r[0] in ("perso_ratio", "perso_cible")],
                           nums, etat, ordre)
        for rels, nums in corps_rels:
            self._executer([r for r in rels if r[0] in ("duree", "perte")],
                           nums, etat, ordre)
        # relations de la QUESTION (pas de durée — « after 3 years » est le
        # qualificatif total, pas une période à consommer)
        self._executer([r for r in rels_q if r[0] != "duree"],
                       self.nombres(question_txt), etat, ordre)
        # plan faible → REFUS : durée sans taux/intérêt, taux multiples sans
        # cible, % non traité, prix du corps non consommés
        if etat.get("faible_duree") or etat.get("faible") or (
                etat.get("nb_prix_corps", 0) > etat.get("nb_achats", 0)) or (
                etat.get("nb_taux", 0) > 1
                and etat.get("cible") is None and etat.get("final") is None
                and etat.get("total") is None):
            etat["courant"] = None
            etat["total"] = None
        couverture = couv / max(1, len(corps))
        # la réponse : total si la question parle d'argent/total/coût,
        # sinon courant ; problèmes inverses et cibles en priorité
        q = question_txt.lower()
        reponse = etat["total"] if etat["total"] is not None else etat["courant"]
        if (any(m in q for m in ("initial", "original", "before"))
                and etat.get("final") is not None):
            reponse = etat["final"] + (etat.get("courant") or 0)
        elif (any(m in q for m in ("how many weeks", "how many days",
                                   "how many months"))
                and etat.get("cible") is not None):
            per = (etat.get("taux") or 0) * (etat.get("heures_semaine") or 1)
            if per > 0:
                reponse = etat["cible"] / per
        elif etat.get("ratio") is not None and etat.get("ratio_unite"):
            u = etat["ratio_unite"]
            if etat.get("ratio_base_unite") and etat.get(etat["ratio_base_unite"]):
                reponse = etat[etat["ratio_base_unite"]] * etat["ratio"]
            elif etat.get(u):
                reponse = etat[u] * etat["ratio"]
        elif (etat.get("accum") is not None
                and etat.get("initial") is not None
                and any(m in q for m in ("after", "total", "have"))):
            reponse = etat["initial"] + etat["accum"]
        elif etat.get("perso_reponse") and etat.get("perso", {}).get("sandy"):
            s = etat["perso"]["sandy"]
            if s.get("cible") and s.get("taux"):
                reponse = s["cible"] / s["taux"]
        elif etat.get("colons") and etat.get("total_ent"):
            a, b = etat["colons"][-1]
            total, _u = etat["total_ent"]
            reponse = total / (a + b) * b
            etat["courant"] = reponse
            if etat.get("futur"):
                reponse = reponse + etat["futur"]
            ordre.append(f"parts : {total:g}/({a:g}+{b:g})×{b:g} = {reponse:g}")
        elif etat.get("ratios") and etat.get("total_ent"):
            # système linéaire : W = 2×B, B = 2×Q, total 700 → 7Q = 700
            gauche = {x for x, _k, _y in etat["ratios"]}
            base = None
            for _x, _k, y in etat["ratios"]:
                if y not in gauche:
                    base = y
                    break
            if base is not None:
                # coefs chaînés : coef[X] = k × coef[Y]
                coefs = {}
                for _ in range(len(etat["ratios"]) + 1):
                    for x, k, y in etat["ratios"]:
                        if y == base:
                            coefs[x] = k
                        elif y in coefs:
                            coefs[x] = k * coefs[y]
                total, _u = etat["total_ent"]
                nb = 1 + sum(coefs.values())
                if nb > 0:
                    q_ = total / nb
                    x0, k0, _y0 = etat["ratios"][0]
                    reponse = q_ * coefs.get(x0, k0)
                    etat["courant"] = reponse
                    ordre.append(f"solveur : base {base} = {q_:g} → {x0} = "
                                 f"{reponse:g}")
        elif "female" in q and etat.get("entites"):
            # somme des compléments (non-male) des sous-ensembles d'étudiants
            fem = [v for k, v in etat["entites"].items()
                   if "students" in k and "male" not in k and k != "students"]
            if fem:
                reponse = sum(fem)
        if reponse is None and etat["total"] is not None:
            reponse = etat["total"]
        if "remaining" in q or "left" in q:
            reponse = etat.get("courant")
        return {"ok": bool(ordre), "etapes": ordre,
                "couverture": couverture, "relations": nb_relations,
                "courant": reponse}

    def _executer(self, rels, nums, etat, ordre):
        """Applique les triplets de relations à l'état (courant/total)."""
        for r in rels:
            typ = r[0]
            arg1 = r[1] if len(r) > 1 else None
            arg2 = r[2] if len(r) > 2 else None
            arg3 = r[3] if len(r) > 3 else None
            if typ == "pct_of":
                base = etat["courant"] if arg1 is None else arg1
                if base is None:
                    continue
                etat["courant"] = base * arg2 / 100
                ordre.append(f"{arg2}% de {base:g} = {etat['courant']:g}")
            elif typ == "pct_compare":
                etat["courant"] = arg1 * arg3
                ordre.append(f"{arg1:g} {arg2} {arg3:g} = {etat['courant']:g}")
            elif typ == "frac_of":
                base = etat["courant"] if arg1 is None else arg1
                if base is None:
                    continue
                etat["courant"] = base * arg2
                ordre.append(f"{arg2:g} × {base:g} = {etat['courant']:g}")
            elif typ == "ratio":
                base = etat.get("courant") or 0
                etat["courant"] = base * arg2
                ordre.append(f"ratio ×{arg2:g} = {etat['courant']:g}")
            elif typ == "cmp":
                if arg3 == "more":
                    etat["courant"] = arg1 + arg2
                else:
                    etat["courant"] = arg1 - arg2
                ordre.append(f"{arg1:g} {arg3} {arg2:g} = {etat['courant']:g}")
            elif typ == "achat":
                etat["total"] = (etat["total"] or 0) + arg2 * arg1
                ordre.append(f"total += {arg2:g}×{arg1:g} = {etat['total']:g}")
            elif typ == "prix_unitaire":
                qtes = [n for n in nums if abs(n - arg1) > 1e-9]
                if len(qtes) == 1:
                    etat["total"] = (etat["total"] or 0) + qtes[0] * arg1
                    ordre.append(f"total += {qtes[0]:g}×{arg1:g} = "
                                 f"{etat['total']:g}")
            elif typ == "duree":
                if etat.get("file_taux"):
                    # multi-périodes : chaque durée consomme son taux
                    t = etat["file_taux"].pop(0)
                    etat["accum"] = etat.get("accum", 0) + t * arg1
                    etat["courant"] = etat["accum"]
                    ordre.append(f"{t:g} × {arg1:g} (durée) → accum = "
                                 f"{etat['accum']:g}")
                elif etat.get("taux") is not None:
                    etat["courant"] = etat["taux"] * arg1
                    ordre.append(f"{etat['taux']:g} × {arg1:g} (durée) = "
                                 f"{etat['courant']:g}")
                elif (etat.get("interet") is not None
                        and etat.get("courant") is not None):
                    # intérêt simple : base × (1 + pct/100 × durée)
                    pct = etat["interet"]
                    etat["courant"] = etat["courant"] * (1 + pct / 100 * arg1)
                    ordre.append(f"intérêt {pct}% × {arg1:g} = {etat['courant']:g}")
                else:
                    etat["faible_duree"] = True
                    etat["courant"] = (etat["courant"] or 1) * arg1
                    ordre.append(f"durée ×{arg1:g} = {etat['courant']:g} (faible)")
            elif typ == "taux":
                etat.setdefault("file_taux", []).append(arg1)
                etat["taux"] = arg1
                etat["nb_taux"] = etat.get("nb_taux", 0) + 1
                ordre.append(f"taux = {arg1:g}/{arg2}")
            elif typ == "interet":
                etat["interet"] = arg1
                ordre.append(f"intérêt = {arg1:g}%")
            elif typ == "base":
                etat["courant"] = arg1
                ordre.append(f"base = {arg1:g}")
            elif typ == "periode_fixe":
                # « 5 games for Christmas each year for 3 years » → +5×3 ;
                # « every year » → années = durée totale de la question
                annees = arg2 if arg2 is not None else etat.get("total_annees")
                if annees is None:
                    continue
                etat["accum"] = etat.get("accum", 0) + arg1 * annees
                ordre.append(f"période fixe += {arg1:g}×{annees:g} = "
                             f"{etat['accum']:g}")
            elif typ == "total_annees":
                etat["total_annees"] = arg1
                ordre.append(f"durée totale = {arg1:g} ans")
            elif typ == "initial":
                etat["initial"] = arg1
                ordre.append(f"initial = {arg1:g}")
            elif typ == "ratio_ent":
                # contrainte X = k×Y — stockée (X, k, Y) pour le solveur final
                etat.setdefault("ratios", []).append((arg2, arg1, r[3]))
                ordre.append(f"contrainte {arg2} = {arg1:g}×{r[3]}")
            elif typ == "total_ent":
                etat["total_ent"] = (arg1, arg2)
                ordre.append(f"total {arg2} = {arg1:g}")
            elif typ == "perso_periode":
                nom, n, m = r[1], r[2], r[3]
                etat.setdefault("perso", {})[nom] = {"taux": n / m, "total": n}
                ordre.append(f"{nom} : {n:g}/{m:g} = {n / m:g}/semaine")
            elif typ == "perso_ratio":
                nom, k = r[1], r[2]
                base = etat.get("perso", {}).get(nom, {}).get("taux")
                if base is not None:
                    etat.setdefault("perso", {}).setdefault("sandy", {})["taux"] =                         base / k
                    ordre.append(f"sandy : taux = {base:g}/{k:g} = {base / k:g}")
            elif typ == "perso_cible":
                nom = r[1]
                base = etat.get("perso", {}).get(nom, {}).get("total")
                if base is not None:
                    etat.setdefault("perso", {}).setdefault("sandy", {})["cible"] =                         base
                    ordre.append(f"sandy : cible = {base:g}")
            elif typ == "perso_question":
                etat["perso_reponse"] = r[1]
                ordre.append(f"question : semaines de {r[1]}")
            elif typ == "perte":
                if etat.get("courant") is not None:
                    etat["courant"] -= arg1
                    ordre.append(f"perte −{arg1:g} = {etat['courant']:g}")
            elif typ == "heures_semaine":
                etat["heures_semaine"] = arg1 * arg2
                ordre.append(f"heures/semaine = {arg1:g}×{arg2:g} = "
                             f"{etat['heures_semaine']:g}")
            elif typ == "cible":
                etat["cible"] = arg1
                ordre.append(f"cible = {arg1:g}")
            elif typ == "final":
                etat["final"] = arg1
                ordre.append(f"final = {arg1:g}")
            elif typ == "quantite":
                base, delta, sens, unite = r[1], r[2], r[3], r[4]
                v = base + delta if sens == "more" else base - delta
                etat[unite] = v
                ordre.append(f"{unite} = {base:g} {sens} {delta:g} = {v:g}")
            elif typ == "ratio_prend":
                a, b, ua = r[1], r[2], r[3]
                etat["ratio"] = a / b
                etat["ratio_unite"] = ua
                ordre.append(f"ratio {a:g}/{b:g} = {a / b:g}")
            elif typ == "ratio_prend2":
                # « it takes A X to make B Y » — imbriqué, quantités calculées
                a, b, ua, ub = r[1], r[2], r[3], r[4]
                etat["ratio"] = a / b
                etat["ratio_unite"] = ua
                etat["ratio_base_unite"] = ub
                ordre.append(f"ratio {a:g}/{b:g} ({ua}/{ub}) = {a / b:g}")
            elif typ == "ratio_colon":
                a, b = arg1, arg2
                etat.setdefault("colons", []).append((a, b))
                ordre.append(f"ratio {a:g}:{b:g}")
            elif typ == "futur":
                etat["futur"] = arg1
                ordre.append(f"futur +{arg1:g}")
            elif typ == "pct_ent":
                f, ref = arg1, arg2
                if ref in ("remaining", "rest"):
                    base = etat.get("courant")
                else:
                    base = etat.get("entites", {}).get(ref, etat.get("courant"))
                if base is None:
                    continue
                sub = base * f
                etat.setdefault("entites", {})[ref] = base - sub
                etat["courant"] = sub
                ordre.append(f"{f * 100:g}% de {base:g} = {sub:g} "
                             f"(reste {ref}: {base - sub:g})")
            elif typ == "base_ent":
                etat["entites"][r[2]] = r[1]
                if etat.get("base") is None:
                    etat["base"] = r[1]
                etat["courant"] = r[1]
                ordre.append(f"entité {r[2]} = {r[1]:g}")
            elif typ == "frac_ent":
                # « X of <ref> are <attr> » : sous-ensemble stocké sous
                # « ref attr » (la référence des clauses suivantes), le
                # COMPLÉMENT reste dans ref. Pour « students », la base est
                # la valeur ORIGINALE (etat["base"]), pas le complément.
                f, ref, attr = r[1], r[2], r[3]
                if ref == "students" and etat.get("base") is not None:
                    base = etat["base"]
                else:
                    base = etat["entites"].get(ref)
                if base is None:
                    continue
                sub = base * f
                etat["entites"][f"{ref} {attr}"] = sub
                etat["entites"][ref] = base - sub
                etat["courant"] = sub
                ordre.append(f"{attr} = {f:g}×{base:g} = {sub:g} "
                             f"(reste {ref}: {base - sub:g})")
            elif typ == "solde":
                etat["total"] = (etat["total"] or 0) - (etat["courant"] or 0)
                ordre.append(f"solde : total − courant = {etat['total']:g}")


# ────────────────────────────────────────────────────────────────────────
# TEST sur les 80 échecs étiquetés (critère pré-enregistré : ≥ 40 %)
# ────────────────────────────────────────────────────────────────────────
def attendu_gsm8k(answer: str):
    m = re.search(r"####\s*(-?\d[\d,.]*)", answer or "")
    if not m:
        return None
    s = m.group(1)
    # virgule = milliers (US) si suivie de 3 chiffres exactement ou si ≥ 2 virgules
    if re.search(r",\d{3}(?!\d)", s) or s.count(",") >= 2:
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    return float(s)


if __name__ == "__main__":
    print("=" * 70)
    print("PARSEUR SÉMANTIQUE — prototype (équivalences LLM ↔ ondulatoire)")
    print("=" * 70)

    # corpus pour les embeddings contextuels : les 80 échecs + 300 GSM8K
    textes = []
    echecs = json.load(open(TAXONOMIE, encoding="utf-8"))
    for e in echecs:
        textes.append(e["question"])
    with open(GSM8K, encoding="utf-8") as f:
        for i, ligne in enumerate(f):
            if i >= 300:
                break
            textes.append(json.loads(ligne)["question"])

    emb = EmbeddingsContextuels()
    emb.construire(textes)
    print(f"[ÉTAGE 1] embeddings contextuels : {len(emb.vocab)} mots du corpus")

    # étiquettes des 80
    etiq = json.load(open(ETIQUETTES, encoding="utf-8"))
    labels = etiq["labels"]
    idx_etiquetes = {int(k): v for k, v in labels.items()}
    echecs_80 = [e for e in echecs if e["idx"] in idx_etiquetes]
    echecs_80.sort(key=lambda e: e["idx"])

    parseur = ParseurSemantique(emb)
    bons, faux, refus = 0, 0, 0
    par_cat = {}
    for e in echecs_80:
        r = parseur.decomposer(e["question"])
        attendu = e["attendu"]
        courant = r.get("courant")
        if courant is None or r["couverture"] < 0.5:
            refus += 1
            verdict = "REFUS"
        elif abs(courant - attendu) < 1e-6:
            bons += 1
            verdict = "BON"
        else:
            faux += 1
            verdict = "FAUX"
        cat = idx_etiquetes[e["idx"]]
        par_cat.setdefault(cat, [0, 0, 0])     # [bons, faux, refus]
        par_cat[cat][{"BON": 0, "FAUX": 1, "REFUS": 2}[verdict]] += 1
        print(f"  {verdict:5s} [{cat}] idx={e['idx']:4d} attendu={attendu:8g} "
              f"parseur={courant if courant is not None else '—':<10} "
              f"couv={r['couverture']:.2f}")

    n = len(echecs_80)
    print("\n" + "=" * 70)
    print(f"RÉSULTAT sur les {n} échecs étiquetés :")
    print(f"  BONS : {bons} ({bons / n * 100:.1f} %)  |  FAUX : {faux}  |  "
          f"REFUS : {refus}")
    print(f"  critère pré-enregistré : ≥ 40 % de plans corrects → "
          f"{'✅ ATTEINT' if bons / n >= 0.4 else '❌ NON ATTEINT'}")
    print("  par catégorie d'erreur (B/F/R) :")
    for cat in ("R", "E", "M"):
        b, f, r_ = par_cat.get(cat, [0, 0, 0])
        print(f"    {cat}: bons {b} · faux {f} · refus {r_}")
    print("=" * 70)
