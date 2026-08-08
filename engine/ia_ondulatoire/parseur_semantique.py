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


class ParseurSemantique:
    def __init__(self, emb: EmbeddingsContextuels):
        self.emb = emb

    def clauses(self, texte):
        return [c.strip() for c in re.split(r"[.?!;]", texte) if c.strip()]

    def nombres(self, clause):
        return [float(n.replace(",", "")) for n in
                re.findall(r"\d+(?:[.,]\d+)?", clause)]

    def relations(self, clause):
        """Extrait (entite, op, args) de la clause — grammaire explicite."""
        c = clause.lower()
        rels = []
        # ── pourcentage : « X% of N » / « X% more/less than N »
        m = re.search(r"(\d+(?:[.,]\d+)?)%\s*(more|less)?\s*than\s+(\d+(?:[.,]\d+)?)", c)
        if m:
            p, sens, n = float(m.group(1)), m.group(2), float(m.group(3))
            rels.append(("pct_compare", n, p, 1 + p / 100 if sens == "more"
                         else 1 - p / 100))
        m = re.search(r"(\d+(?:[.,]\d+)?)%\s*of\s+(\d+(?:[.,]\d+)?)", c)
        if m:
            rels.append(("pct_of", float(m.group(2)), float(m.group(1)), None))
        # ── fraction : « one-third of N », « 2/3 of N », « 2/3 of that »
        m = re.search(r"(\d+)\s*/\s*(\d+)\s*of\s+(\d+(?:[.,]\d+)?)", c)
        if m:
            rels.append(("frac_of", float(m.group(3)),
                         float(m.group(1)) / float(m.group(2)), None))
        m = re.search(r"(\d+)\s*/\s*(\d+)(?:rd|th|nd|st)?\s+of\s+"
                      r"(?:that|the\s+[a-z]+)", c)
        if m:
            rels.append(("frac_of", None,
                         float(m.group(1)) / float(m.group(2)), None))
        for mot, (num, den) in FRACTIONS.items():
            m = re.search(rf"{re.escape(mot)}\s+of\s+(\d+(?:[.,]\d+)?)", c)
            if m:
                rels.append(("frac_of", float(m.group(1)), num / den, None))
                break
            m = re.search(rf"{re.escape(mot)}\s+of\s+(?:that|the\s+[a-z]+)", c)
            if m:
                rels.append(("frac_of", None, num / den, None))
                break
        # ── ratio : « k times as many », « twice as many », « half as many »
        m = re.search(r"(twice|(\d+(?:[.,]\d+)?)\s*(?:times)?)\s+as\s+(many|much)"
                      r"\s+as\s+(?:the\s+)?([a-z]+)", c)
        if m:
            k = 2.0 if m.group(1) == "twice" else float(m.group(2))
            rels.append(("ratio", m.group(4), k, None))
        # ── comparaison : « X more than N » / « X less than N »
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+(more|less|fewer)\s+than\s+"
                      r"(\d+(?:[.,]\d+)?)", c)
        if m:
            x, sens, n = float(m.group(1)), m.group(2), float(m.group(3))
            rels.append(("cmp", n, x, sens))
        # ── ACHAT : « N objets for/at $P each/per » — quantité et prix
        # appariés par proximité (plusieurs achats possibles). « for $P »
        # SANS each/per est un TOTAL (pas un prix unitaire) → non traité
        # ici (REFUS plutôt qu'une mauvaise assertion).
        for m in re.finditer(
                r"(\d+(?:[.,]\d+)?)\s+[a-z]+(?:\s+[a-z]+)*\s+(?:for|at)\s+\$?\s*"
                r"(\d+(?:[.,]\d+)?)\s*(?:each|per\s+[a-z]+|apiece)", c):
            rels.append(("achat", float(m.group(2)), float(m.group(1)), None))
        m = re.search(r"\$?\s*(\d+(?:[.,]\d+)?)\s*(?:each|apiece)", c)
        if m:
            rels.append(("prix_unitaire", float(m.group(1)), None, None))
        # ── coût total / change
        if "change" in c or "left" in c or "remainder" in c:
            rels.append(("solde", None, None, None))
        # ── taux : « N per month/day/week », « N a day » (flux)
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+(?:per|a|an)\s+(day|week|month|"
                      r"year|hour|minute)", c)
        if m:
            rels.append(("taux", float(m.group(1)), m.group(2), None))
        # ── durée : « in N days/weeks/months », « for N days »
        m = re.search(r"(?:in|for|after|over)\s+(\d+)\s+(day|days|week|weeks|"
                      r"month|months|year|years)", c)
        if m:
            rels.append(("duree", float(m.group(1)), m.group(2), None))
        # ── pourcentage isolé « X% » avec sujet implicite
        m = re.search(r"(\d+(?:[.,]\d+)?)%", c)
        if m and not any(r[0] in ("pct_of", "pct_compare") for r in rels):
            rels.append(("pct_iso", float(m.group(1)), None, None))
        return rels

    def decomposer(self, question):
        """Retourne {ok, etapes, couverture, relations}."""
        cls = self.clauses(question)
        if not cls:
            return {"ok": False, "etapes": [], "couverture": 0.0, "relations": []}
        question_txt = cls[-1]
        corps = cls[:-1]
        # attention : poids des clauses vs la question (multi-têtes)
        wm, _ = attention(self.emb, question_txt, corps)
        # exécution : état à DEUX variables — courant (dernière valeur) et
        # total (accumulateur) ; la question détermine laquelle répondre
        etat = {"courant": None, "total": None}
        ordre = []
        couv = 0.0
        nb_relations = 0
        for c, w in zip(corps, wm):
            rels = self.relations(c)
            nums = self.nombres(c)
            nb_relations += len(rels)
            if rels:
                couv += 1
            for r in rels:
                typ, arg1, arg2, arg3 = r
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
                    etat["courant"] = etat.get("courant", 0) * arg2
                    ordre.append(f"ratio ×{arg2:g} = {etat['courant']:g}")
                elif typ == "cmp":
                    if arg3 == "more":
                        etat["courant"] = arg1 + arg2
                    else:
                        etat["courant"] = arg1 - arg2
                    ordre.append(f"{arg1:g} {arg3} {arg2:g} = {etat['courant']:g}")
                elif typ == "achat":
                    # « N objets for $P each » → total += N×P
                    etat["total"] = (etat["total"] or 0) + arg2 * arg1
                    ordre.append(f"total += {arg2:g}×{arg1:g} = "
                                 f"{etat['total']:g}")
                elif typ == "prix_unitaire":
                    # « $P each » sans quantité dans la clause : appliqué
                    # au nombre précédent si unique
                    qtes = [n for n in nums if abs(n - arg1) > 1e-9]
                    if len(qtes) == 1:
                        etat["total"] = (etat["total"] or 0) + qtes[0] * arg1
                        ordre.append(f"total += {qtes[0]:g}×{arg1:g} = "
                                     f"{etat['total']:g}")
                elif typ == "duree":
                    etat["courant"] = (etat["courant"] or 1) * arg1
                    ordre.append(f"durée ×{arg1:g} = {etat['courant']:g}")
                elif typ == "taux":
                    # « N per X » : courant = taux × durée (si connue),
                    # sinon mémorisé pour la clause suivante
                    if etat.get("courant") is not None:
                        etat["courant"] = etat["courant"] * arg1
                        ordre.append(f"taux ×{arg1:g} = {etat['courant']:g}")
                    else:
                        etat["taux"] = arg1
                elif typ == "solde":
                    etat["total"] = (etat["total"] or 0) - (etat["courant"] or 0)
                    ordre.append(f"solde : total − courant = {etat['total']:g}")
        couverture = couv / max(1, len(corps))
        # la réponse : total si la question parle d'argent/total/coût,
        # sinon courant
        q = question_txt.lower()
        reponse = etat["total"] if etat["total"] is not None else etat["courant"]
        if reponse is None and etat["total"] is not None:
            reponse = etat["total"]
        if "courant" in q or "remaining" in q or "left" in q:
            reponse = etat.get("courant")
        return {"ok": bool(ordre), "etapes": ordre,
                "couverture": couverture, "relations": nb_relations,
                "courant": reponse}


# ────────────────────────────────────────────────────────────────────────
# TEST sur les 80 échecs étiquetés (critère pré-enregistré : ≥ 40 %)
# ────────────────────────────────────────────────────────────────────────
def attendu_gsm8k(answer: str):
    m = re.search(r"####\s*(-?\d+(?:[.,]\d+)?)", answer or "")
    return float(m.group(1).replace(",", ".")) if m else None


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
