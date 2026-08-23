# -*- coding: utf-8 -*-
"""
generateur.py — L'IA génératrice : question en langage naturel → programme ondulatoire.

Conforme au DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md §8.2 : les 7 intentions
reconnues (query, reason, creative, store_fact, compare, analogize, classify),
chacune avec son pattern ENCODE → MANIPULER → DÉCODER.

    Question : "Quelle est la différence entre l'amour et l'amitié ?"
    → intention compare
    →    ψ_a = ENCODE "amour"
         ψ_b = ENCODE "amitié"
         similarite = RESONANCE(ψ_a, ψ_b)
         ψ_diff = OPPOSE(ψ_a, ψ_b)
         analyse = DECODE(ψ_diff)
         RETURN analyse
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import ir
from primitives import DEFAULT_DIM, encode

# ────────────────────────────────────────────────────────────────────────
# Les 7 intentions (§8.2) — marqueurs français
# ────────────────────────────────────────────────────────────────────────

INTENTIONS = ("query", "reason", "creative", "store_fact", "compare", "analogize", "classify")

MARQUEURS: Dict[str, List[str]] = {
    "query": ["qu'est-ce que", "qui est", "explique", "définis", "definis", "c'est quoi",
              "que sais-tu", "parle-moi de", "dis-moi", "definition", "définition",
              "que veux dire", "que veut dire", "connais-tu", "sais-tu ce"],
    "reason": ["pourquoi", "déduis", "deduis", "donc", "raisonne", "calcule", "combien",
               "résous", "resous", "prouve", "si ", "alors", "logique", "conséquence",
               "consequence", "addition", "multiplie", "soustrais", "divise"],
    "creative": ["imagine", "crée", "cree", "invente", "et si", "écris un poème",
                 "ecris un poeme", "poème", "poeme", "surréaliste", "surrealiste",
                 "rêve", "reve", "compose", "métaphore", "metaphore"],
    "store_fact": ["souviens-toi", "mémorise", "memorise", "retiens", "apprends",
                   "note que", "retenu", "souviens-toi que"],
    "compare": ["différence", "difference", "versus", "vs ", "comparer", "compare",
                "comparaison", "meilleur entre", "lequel est", "plus grand que",
                "plus petit que", "oppose"],
    "analogize": ["comme", "analogie", "ressemble à", "ressemble a", "est à", "métaphore de",
                  "analogue", "semblable"],
    "classify": ["catégorise", "categorise", "classe", "quel type", "quel genre",
                 "classifie", "dans quelle catégorie", "typologie", "type de"],
}

MOTS_VIDES = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d'", "et", "ou", "est", "sont",
    "ce", "cette", "ces", "que", "qui", "quoi", "quel", "quelle", "quels", "quelles",
    "en", "au", "aux", "pour", "avec", "dans", "sur", "par", "mais", "donc", "si",
    "the", "a", "an", "of", "to", "in", "for", "with", "on", "at", "by", "etre", "avoir",
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles", "me", "te", "se",
    "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "notre", "votre",
    "moi", "toi", "lui", "elle", "nous", "vous", "eux", "quelqu'un", "quelqu un",
    "est-ce", "sais", "dis", "entre", "différence", "difference", "differente",
}


def _normaliser(texte: str) -> str:
    return texte.lower().strip().strip("?¿!.…,;:()[]{}\"'")


def _pseudo_mots(texte: str) -> List[str]:
    """Mots pleins de la question, triés par longueur décroissante."""
    mots = [m for m in re.findall(r"[a-zàâäéèêëîïôöùûüç'-]+", _normaliser(texte)) if m]
    mots = [m for m in mots if m not in MOTS_VIDES and len(m) > 1]
    vus: List[str] = []
    for m in mots:
        if m not in vus:
            vus.append(m)
    vus.sort(key=len, reverse=True)
    return vus


class GenerateurOndulatoire:
    """Détection d'intention + génération de programmes ondulatoires natifs."""

    def __init__(self, dim: int = DEFAULT_DIM, hologramme_connaissances: str = "H_connaissances"):
        self.dim = dim
        self.holo_connu = hologramme_connaissances

    # ── intention (§8.2) ────────────────────────────────────────────────
    def detecter_intention(self, question: str) -> Tuple[str, float]:
        """Retourne (intention, confiance). Priorité : marqueur le plus long trouvé."""
        q = _normaliser(question)
        meilleur = ("query", 0.35)
        for intention, marqueurs in MARQUEURS.items():
            for marqueur in marqueurs:
                if marqueur in q:
                    confiance = min(0.99, 0.55 + 0.06 * len(marqueur))
                    if confiance > meilleur[1]:
                        meilleur = (intention, confiance)
        if meilleur[0] == "query" and meilleur[1] <= 0.35 and q.endswith("?"):
            meilleur = ("query", 0.60)
        return meilleur

    # ── génération (§8.2) ───────────────────────────────────────────────
    def generer(self, question: str) -> Tuple[ir.Program, str]:
        """Question → (Programme ondulatoire, intention)."""
        intention, _ = self.detecter_intention(question)
        programme = self._programme_pour(intention, question)
        return programme, intention

    def _programme_pour(self, intention: str, question: str) -> ir.Program:
        q = question.strip()
        entites = _pseudo_mots(question)
        if intention == "store_fact":
            return self._faire_store_fact(question, entites)
        if intention == "creative":
            declencheurs = {m.strip() for m in MARQUEURS["creative"]}
            entites = [e for e in entites if e not in declencheurs]
            a = entites[0] if len(entites) > 0 else "univers"
            b = entites[1] if len(entites) > 1 else "conscience"
            return self._pattern_creative(a, b)
        if intention == "compare":
            a, b = self._deux_concepts(question, entites)
            return self._pattern_compare(a, b)
        if intention == "analogize":
            a, b = self._deux_concepts(question, entites)
            return self._pattern_analogie(a, b)
        if intention == "reason":
            return self._pattern_raisonnement(q)
        if intention == "classify":
            return self._pattern_classifier(q, entites)
        return self._pattern_query(q)

    # ── patterns ENCODE → MANIPULER → DÉCODER (§8.2) ────────────────────
    def _pattern_query(self, q: str) -> ir.Program:
        return ir.Program([
            ir.Assign("psi_q", ir.Encode(q)),
            ir.Query("psi_r", ir.Var("psi_q"), self.holo_connu),
            ir.Assign("reponse", ir.Decode(ir.Var("psi_r"))),
            ir.Return(ir.Var("reponse")),
        ])

    def _pattern_raisonnement(self, q: str) -> ir.Program:
        return ir.Program([
            ir.Assign("psi_q", ir.Encode(q)),
            ir.Query("psi_r", ir.Var("psi_q"), self.holo_connu),
            ir.Assign("psi_s", ir.Superpose([ir.Var("psi_q"), ir.Var("psi_r")])),
            ir.Assign("psi_e", ir.Emerge([ir.Var("psi_s"), ir.Var("psi_r")], 0.5)),
            ir.Assign("analyse", ir.Decode(ir.Var("psi_e"))),
            ir.Return(ir.Var("analyse")),
        ])

    def _pattern_creative(self, a: str, b: str) -> ir.Program:
        return ir.Program([
            ir.Assign("psi_a", ir.Encode(a)),
            ir.Assign("psi_b", ir.Encode(b)),
            ir.Assign("psi_m", ir.Interfere(ir.Var("psi_a"), ir.Var("psi_b"), 0.15)),
            ir.Assign("resultat", ir.Decode(ir.Var("psi_m"))),
            ir.Return(ir.Var("resultat")),
        ])

    def _pattern_compare(self, a: str, b: str) -> ir.Program:
        return ir.Program([
            ir.Assign("psi_a", ir.Encode(a)),
            ir.Assign("psi_b", ir.Encode(b)),
            ir.Assign("similarite", ir.Resonance(ir.Var("psi_a"), ir.Var("psi_b"))),
            ir.Assign("psi_diff", ir.Oppose(ir.Var("psi_a"), ir.Var("psi_b"))),
            ir.Assign("analyse", ir.Decode(ir.Var("psi_diff"))),
            ir.Return(ir.Var("analyse")),
        ])

    def _pattern_analogie(self, a: str, b: str) -> ir.Program:
        return ir.Program([
            ir.Assign("psi_a", ir.Encode(a)),
            ir.Assign("psi_b", ir.Encode(b)),
            ir.Assign("psi_lien", ir.Bind(ir.Var("psi_a"), ir.Var("psi_b"))),
            ir.Assign("psi_revele", ir.Unbind(ir.Var("psi_lien"), ir.Var("psi_b"))),
            ir.Assign("resultat", ir.Decode(ir.Var("psi_revele"))),
            ir.Return(ir.Var("resultat")),
        ])

    def _pattern_classifier(self, q: str, entites: List[str]) -> ir.Program:
        sujet = entites[0] if entites else q
        return ir.Program([
            ir.Assign("psi_q", ir.Encode(sujet)),
            ir.Query("psi_r", ir.Var("psi_q"), self.holo_connu),
            ir.Assign("psi_proto", ir.Emerge([ir.Var("psi_q"), ir.Var("psi_r")], 0.35)),
            ir.Assign("categorie", ir.Decode(ir.Var("psi_proto"))),
            ir.Return(ir.Var("categorie")),
        ])

    def _faire_store_fact(self, question: str, entites: List[str]) -> ir.Program:
        """« souviens-toi que X relation Y » → BIND_MANY → STORE IN H_faits."""
        sujet, relation, objet = self._extraire_triplet(question, entites)
        return ir.Program([
            ir.Assign("psi_s", ir.Encode(sujet)),
            ir.Assign("psi_r", ir.Encode(relation)),
            ir.Assign("psi_o", ir.Encode(objet)),
            ir.Assign("psi_f", ir.BindMany([ir.Var("psi_s"), ir.Var("psi_r"), ir.Var("psi_o")])),
            ir.Store("psi_f", ir.Var("psi_f"), "H_faits"),
            ir.Return(ir.Var("psi_f")),
        ])

    # ── extraction de concepts ──────────────────────────────────────────
    def _deux_concepts(self, question: str, entites: List[str]) -> Tuple[str, str]:
        q = _normaliser(question)
        m = re.search(r"(?:entre|différence\s+entre|comparer)\s+(.+?)\s+(?:et|vs\.?|versus)\s+(.+)", q)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            a = a.split()[0] if a else a
            b = b.split()[0] if b else b
            if a and b:
                return a, b
        if len(entites) >= 2:
            return entites[0], entites[1]
        if len(entites) == 1:
            return entites[0], "l'ombre de " + entites[0]
        return "ciel", "terre"

    def _extraire_triplet(self, question: str, entites: List[str]) -> Tuple[str, str, str]:
        """« souviens-toi que la lumière est une onde » → (lumière, est, onde)."""
        q = _normaliser(question)
        for mot_cle in ("souviens-toi que", "mémorise que", "memorise que", "retiens que",
                        "apprends que", "note que", "souviens-toi"):
            if mot_cle in q:
                q = q.split(mot_cle, 1)[1].strip()
                break
        m = re.match(r"^(?:que\s+)?(.+?)\s+(est|sont|sera|seront|vaut|a|ont|peut|croit|sait|"
                     r"fait|contient|produit|entraîne|entraine|signifie|désigne|designe|bout|"
                     r"gèle|gele|fond|s'évapore|s'evapore|se transforme|se change|devient|"
                     r"reste|mesure|pèse|pese|coute|coûte|donne|fournit|mange|boit|voit|"
                     r"entend|aime|craint|veut)\s+(?:à\s+|de\s+|du\s+|des\s+|la\s+|le\s+)?(.+)$", q)
        if m:
            return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        # fallback : mots pleins dans l'ordre original (la syntaxe compte)
        declencheurs = {"souviens-toi", "memorise", "mémorise", "retiens", "apprends",
                        "note", "que", "qui"}
        mots_ordre = [mo for mo in re.findall(r"[a-zàâäéèêëîïôöùûüç]+", q)
                      if mo not in MOTS_VIDES and mo not in declencheurs]
        if len(mots_ordre) >= 2:
            return mots_ordre[0], "est", " ".join(mots_ordre[1:3])
        if mots_ordre:
            return mots_ordre[0], "est", "inconnu"
        return "je", "sais que", q


# ────────────────────────────────────────────────────────────────────────
# Aide : vocabulaire d'une question (pour le décodage)
# ────────────────────────────────────────────────────────────────────────

def vocabulaire_de(texte: str, dim: int = DEFAULT_DIM) -> Dict[str, "Wave"]:
    """Construit un vocabulaire {mot: ψ} depuis une phrase (mots + texte entier)."""
    vocab: Dict[str, "Wave"] = {}
    for mot in re.findall(r"[a-zàâäéèêëîïôöùûüç'-]+", _normaliser(texte)):
        if len(mot) > 1 and mot not in vocab:
            vocab[mot] = encode(mot, dim)
    if texte.strip() not in vocab:
        vocab[texte.strip()] = encode(texte.strip(), dim)
    return vocab
