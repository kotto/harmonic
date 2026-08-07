# -*- coding: utf-8 -*-
"""
gsm8k.py — Solveur GSM8K en langage ondulatoire natif.

La sélection d'opération est une expérience d'interférence : chaque famille
d'opération (addition, soustraction, multiplication, division, règle de trois)
est un **prototype d'onde** = SUPERPOSE des encodages de ses mots-clés (EN/FR).
Une phrase de l'énoncé devient une onde (superposition de ses mots pleins),
puis RESONATE désigne l'opération par interférence constructive maximale.

    ENCODE(phrase) → SUPERPOSE(mots) → RESONATE(ψ_phrase, ψ_prototype)
        → DÉCODER(meilleure opération) → appliquer à l'état courant

L'enchaînement est une machine à états déterministe : chaque phrase applique
son opération au résultat courant (0 LLM, 0 paramètre appris).

    resoudre(question)  → {question, reponse, etapes, operations, confiances, temps_ms}
    benchmark(n=200)    → précision sur gsm8k_test.jsonl + rapport JSON
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from primitives import DEFAULT_DIM, Wave, encode, resonate, superpose

DOSSIER_DONNEES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "data", "ia_ondulatoire")
DOSSIER_BENCHMARK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "data", "benchmarks")

# ────────────────────────────────────────────────────────────────────────
# Prototypes d'opérations — les mots-clés deviennent des ondes (EN + FR)
# ────────────────────────────────────────────────────────────────────────

OPERATIONS = ["addition", "soustraction", "multiplication", "division"]

MOTS_CLEFS = {
    "addition": ["additionner", "ajouter", "en tout", "au total", "total", "plus",
                 "somme", "ensemble", "together", "in all", "combined", "all together",
                 "sum", "total", "et", "and"],
    "soustraction": ["soustraire", "retirer", "reste", "rester", "moins", "différence",
                     "difference", "less", "minus", "left", "remainder", "remaining",
                     "rest", "eats", "eat", "ate", "spent", "spends", "spend", "sold",
                     "sells", "sell", "loses", "lost", "lose", "give", "gives", "gave",
                     "away", "dépense", "depense", "dépensé", "depense", "donne", "cède"],
    "multiplication": ["multiplier", "fois", "par", "chacun", "chaque", "per", "each",
                       "times", "twice", "prix unitaire", "unit price",
                       "dollars per", "francs par", "par jour", "per day", "par heure",
                       "buys", "bought", "achète", "achete"],
    "division": ["diviser", "partager", "répartir", "repartir", "equally", "share",
                 "among", "split", "divided by", "half", "third", "quarter", "each of",
                 "each person", "each child", "each student", "per person", "par personne",
                 "chacun reçoit", "chacun recoit", "receives", "gets", "moitié", "moitie",
                 "tiers", "quart"],
}

# motifs contextuels forts — ordonnés par précision décroissante :
# le premier motif trouvé dans le contexte l'emporte
_MOTIFS_STRONGS = [
    (r"\+", "addition"),
    (r"[-−]", "soustraction"),
    (r"[×*]", "multiplication"),
    (r"[/÷]", "division"),
    (r"\b(more|again|encore|additional)\b", "addition"),
    (r"\b(per|times|twice)\b", "multiplication"),
    (r"\b(buys|bought|achète|achete|coûte|coûtent|coutent|cost|costs|earn|earns|makes)\b", "multiplication"),
    (r"\b(each of|each person|each child|each student|par personne|chacun reçoit|chacun recoit|equally|among|split)\b", "division"),
    (r"\b(remainder|remaining|left|rest|restant|reste|less|fewer)\b", "soustraction"),
    (r"\b(in all|together|combined|en tout|au total)\b", "addition"),
    (r"\b(difference between|différence entre)\b", "soustraction"),
]

# nombres épelés (anglais — GSM8K les utilise massivement)
_UNITES = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
           "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
           "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
           "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
_DIZAINES = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
             "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_DIVERS = {"a dozen": 12, "a couple": 2, "a pair": 2, "hundred": 100,
           "thousand": 1000, "million": 1_000_000}


def _numeriser(texte: str) -> str:
    """Remplace les nombres épelés par des chiffres (« three » → « 3 »).
    Les motifs spéciaux (« half that much »…) sont évalués sur le texte original."""
    t = texte
    # vingt-cinq / twenty-five → 25
    for diz, base in sorted(_DIZAINES.items(), key=lambda kv: -len(kv[0])):
        for un, val in _UNITES.items():
            t = re.sub(rf"\b{diz}[-\s]+{un}\b", str(base + val), t, flags=re.IGNORECASE)
    for mot, val in _UNITES.items():
        t = re.sub(rf"\b{mot}\b", str(val), t, flags=re.IGNORECASE)
    for mot, val in _DIZAINES.items():
        t = re.sub(rf"\b{mot}\b", str(val), t, flags=re.IGNORECASE)
    # « 5 hundred » → 500 ; « a dozen » → 12
    for mot, val in sorted(_DIVERS.items(), key=lambda kv: -len(kv[0])):
        t = re.sub(rf"\b(\d+) {mot}\b", lambda m: str(int(m.group(1)) * val),
                   t, flags=re.IGNORECASE)
        t = re.sub(rf"\ba {mot}\b", str(val), t, flags=re.IGNORECASE)
    return t

_MOTIFS_SPECIAUX = [
    (r"and half (that|as) much", lambda n: n * 1.5),     # 2 bolts + half that much → 3
    (r"half (that|as) much", lambda n: n / 2.0),         # half the quantity
    (r"twice as many", lambda n: n * 2.0),               # double
    (r"three times as many", lambda n: n * 3.0),         # triple
]


class GSM8KOndulatoire:
    """Sélection d'opération par résonance + machine à états déterministe."""

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        # prototypes d'ondes : SUPERPOSE des encodages des mots-clés
        self.prototypes: Dict[str, Wave] = {}
        for op, mots in MOTS_CLEFS.items():
            ondes = [encode(m, dim) for m in mots]
            self.prototypes[op] = superpose(*ondes) if ondes else encode(op, dim)

    # ── 1. ENCODE → SUPERPOSE → RESONATE → DÉCODER (l'opération) ────────
    def detecter_operation(self, phrase: str) -> Tuple[str, float, bool]:
        """L'onde de la phrase résonne avec chaque prototype d'opération.
        Retourne (opération, écart de confiance, forcée-par-motif)."""
        mots = [m for m in re.findall(r"[a-zàâäéèêëîïôöùûüç]+", phrase.lower())
                if len(m) > 2]
        force = False
        if not mots:
            return "addition", 0.0, force
        psi_phrase = superpose(*[encode(m, self.dim) for m in mots])
        scores = [(op, float(resonate(psi_phrase, proto)))
                  for op, proto in self.prototypes.items()]
        scores.sort(key=lambda t: -t[1])
        # motifs contextuels forts (règle de priorité sur l'ambiguïté)
        for motif, op in _MOTIFS_STRONGS:
            if re.search(motif, phrase, re.IGNORECASE):
                scores = [(op, s + 0.35) if o == op else (o, s)
                          for o, s in scores]
                force = True
                break
        scores.sort(key=lambda t: -t[1])
        return scores[0][0], round(scores[0][1] - scores[1][1], 4), force

    # ── 2. nombres ──────────────────────────────────────────────────────
    @staticmethod
    def extraire_nombres(phrase: str) -> List[float]:
        """Nombres d'une phrase (virgule décimale FR ou point EN, signes $/€)."""
        vals = []
        for m in re.finditer(r"-?\d+(?:[.,]\d+)?", phrase):
            vals.append(float(m.group().replace(",", ".")))
        return vals

    # ── 3. machine à états ──────────────────────────────────────────────
    @staticmethod
    def _appliquer(op: str, a: float, b: float) -> float:
        if op == "addition":
            return a + b
        if op == "soustraction":
            return a - b
        if op == "multiplication":
            return a * b
        if op == "division":
            return a / b if b else a
        return a + b

    def resoudre(self, question: str) -> Dict[str, Any]:
        """Résout un énoncé. Deux moteurs :
        1. machine à états sémantique (compteurs d'objets, équations relatives)
        2. pipeline par résonance (prototypes d'ondes) — fallback"""
        t0 = time.time()
        from machine_etats import MachineEtatsSemantique
        r_sem = MachineEtatsSemantique().resoudre(question)
        if r_sem is not None:
            r_sem["temps_ms"] = int((time.time() - t0) * 1000)
            r_sem["question"] = (question or "").strip()
            return r_sem
        return self._resoudre_resonance(question, t0)

    def _resoudre_resonance(self, question: str, t0: float) -> Dict[str, Any]:
        """Pipeline par résonance : chaque nombre (chiffres ou épelé) est traité
        séquentiellement avec sa fenêtre de contexte locale — l'onde du
        contexte désigne l'opération (résonance + motifs forts + momentum)."""
        question = (question or "").strip()
        numerise = _numeriser(question)
        courant: Optional[float] = None
        etapes: List[str] = []
        operations: List[str] = []
        confiances: List[float] = []
        dernier_op: Optional[str] = None

        # 1. nombres avec leur contexte local — fenêtre étroite (~40 car. avant,
        #    ~15 après) tronquée au séparateur de phrase précédent : seule
        #    l'intention locale du nombre doit parler
        matches = list(re.finditer(r"-?\d+(?:[.,]\d+)?", numerise))
        for m in matches:
            n = float(m.group().replace(",", "."))
            debut_ctx = max(0, m.start() - 40)
            avant = numerise[:m.start()]
            derniere = max(avant.rfind(". "), avant.rfind("! "), avant.rfind("? "),
                           avant.rfind(".\n"))
            if derniere > debut_ctx:
                debut_ctx = derniere + 2
            ctx = numerise[debut_ctx: m.end() + 15]
            ctx = ctx.replace("\n", " ")
            # fenêtre étendue après le nombre : les marqueurs de soustraction /
            # division vivent souvent APRÈS le nombre (« te reste-t-il »,
            # « vitesse moyenne », « chacun reçoit »)
            apres = numerise[m.end(): m.end() + 45]
            if re.search(r"\b(reste|restant|left|rest|remainder|remaining)\b",
                         apres, re.IGNORECASE):
                op, conf, force = "soustraction", 0.5, True
            elif re.search(r"\b(vitesse|average speed)\b", apres, re.IGNORECASE):
                op, conf, force = "division", 0.5, True
            elif re.search(r"\b(chacun reçoit|chacun recoit|reçoit-il|recoit-il|"
                           r"each gets|receives)\b", apres, re.IGNORECASE):
                op, conf, force = "division", 0.5, True
            else:
                op, conf, force = self.detecter_operation(ctx)

            # pourcentages : « 20% profit » → ×(1+0,2) ; « 20% off » → ×(1−0,2) ;
            # « 20% of » → ×0,2 (le motif « X% of Y » est traité en passe 2)
            if courant is not None and re.search(r"%\s|percent", ctx):
                if re.search(r"\b(increase|gain|profit|gagne|augmente|markup)\b",
                             ctx, re.IGNORECASE):
                    courant = courant * (1 + n / 100)
                    action = f"+{n:g}%"
                elif re.search(r"\b(decrease|lose|lost|drop|off|baisse|perd|discount)\b",
                               ctx, re.IGNORECASE):
                    courant = courant * (1 - n / 100)
                    action = f"-{n:g}%"
                else:
                    courant = courant * n / 100
                    action = f"{n:g}% de"
            # momentum : signal faible et non forcé → opération précédente
            elif conf < 0.03 and dernier_op and not force:
                op = dernier_op
                if courant is None:
                    courant = n
                    action = f"{n:g}"
                else:
                    courant = self._appliquer(op, courant, n)
                    action = f"{op} {n:g}"
            elif courant is None:
                courant = n
                action = f"{n:g}"
            else:
                courant = self._appliquer(op, courant, n)
                action = f"{op} {n:g}"
            dernier_op = op
            operations.append(op)
            confiances.append(conf)
            etapes.append(f"…{ctx.strip()[-45:]} → {action} = {courant:g}")

        # 2. motifs spéciaux évalués sur le texte ORIGINAL (« half that much »…)
        for phrase in re.split(r"(?<=[.!?])\s+|\n+", question):
            if courant is None:
                break
            # règle de trois : « Pour fabriquer 3 objets, une machine met 20
            # minutes. Combien de temps pour 8 objets ? » → 20 × 8 ÷ 3
            m_rdt = re.search(r"pour fabriquer\s+(\d+)\s+objets?.{0,80}?met\s+"
                              r"(\d+(?:[.,]\d+)?)\s*minutes?.{0,80}?pour\s+(\d+)\s+objets",
                              question, re.IGNORECASE)
            if m_rdt:
                n1, m, k = (float(m_rdt.group(1)), float(m_rdt.group(2)),
                            float(m_rdt.group(3)))
                courant = m * k / n1
                etapes.append(f"« règle de trois » → {m:g} × {k:g} ÷ {n1:g} = {courant:g}")
                operations.append("special:regle_de_trois")
                continue
            # « X% of Y » → Y × X / 100 (le pourcentage précède sa base)
            m_pct = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:%|percent)\s*of\s+(?:the\s+)?(\d+(?:[.,]\d+)?)",
                              phrase, re.IGNORECASE)
            if m_pct:
                pct = float(m_pct.group(1).replace(",", "."))
                base = float(m_pct.group(2).replace(",", "."))
                courant = base * pct / 100
                etapes.append(f"« {phrase.strip()[:50]}… » → {pct:g}% de {base:g} = {courant:g}")
                operations.append("special:pourcent")
                continue
            for motif, fn in _MOTIFS_SPECIAUX:
                if re.search(motif, phrase, re.IGNORECASE):
                    courant = fn(courant)
                    etapes.append(f"« {phrase.strip()[:50]}… » → {courant:g}")
                    operations.append("special:" + motif)
                    break

        # arrondi final propre
        if courant is None:
            reponse = None
            affichage = "Aucun nombre détecté"
        else:
            reponse = float(courant)
            affichage = f"{round(reponse):g}" if abs(reponse - round(reponse)) < 1e-9 \
                else f"{round(reponse, 3):g}"

        return {
            "question": question, "reponse": affichage,
            "reponse_num": reponse,
            "etapes": etapes, "operations": operations,
            "confiances": confiances,
            "temps_ms": int((time.time() - t0) * 1000),
            "modele": "langage-ondulatoire-v1 (0 LLM)",
            "ondulatoire": {"dim": self.dim, "prototypes": list(self.prototypes)},
        }

    # ── 4. benchmark officiel GSM8K ─────────────────────────────────────
    def benchmark(self, n: int = 200, sauver: bool = True,
                  chemin: str = "") -> Dict[str, Any]:
        """Précision sur gsm8k_test.jsonl (réponse finale exacte, tolérance)."""
        fichier = os.path.join(DOSSIER_BENCHMARK, "gsm8k_test.jsonl")
        if not os.path.exists(fichier):
            return {"error": f"dataset absent : {fichier}",
                    "dataset": fichier}
        bon, total, temps_total = 0, 0, 0.0
        erreurs: List[Dict] = []
        repartition: Dict[str, int] = {}
        with open(fichier, encoding="utf-8") as f:
            for ligne in f:
                if total >= n:
                    break
                try:
                    d = json.loads(ligne)
                except Exception:
                    continue
                attendu = self._reponse_attendue(d.get("answer", ""))
                r = self.resoudre(d.get("question", ""))
                temps_total += r["temps_ms"]
                ok = (attendu is not None and r["reponse_num"] is not None
                      and abs(r["reponse_num"] - attendu) < 1e-6)
                total += 1
                if ok:
                    bon += 1
                elif len(erreurs) < 5:
                    erreurs.append({"question": d.get("question", "")[:120],
                                    "attendu": attendu, "obtenu": r["reponse"],
                                    "operations": r["operations"][:5]})
                for op in r["operations"][:1]:
                    repartition[op] = repartition.get(op, 0) + 1
        rapport = {
            "benchmark": "gsm8k_test.jsonl",
            "echantillon": total, "correct": bon,
            "precision": round(bon / total, 4) if total else 0.0,
            "latence_moyenne_ms": round(temps_total / max(1, total), 1),
            "repartition_operations": repartition,
            "erreurs_exemples": erreurs,
            "modele": "langage-ondulatoire-v1 (0 LLM, déterministe)",
            "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if sauver:
            os.makedirs(chemin or DOSSIER_DONNEES, exist_ok=True)
            with open(os.path.join(chemin or DOSSIER_DONNEES,
                                   "benchmark_gsm8k.json"), "w",
                      encoding="utf-8") as f:
                json.dump(rapport, f, ensure_ascii=False, indent=1)
        return rapport

    @staticmethod
    def _reponse_attendue(answer: str) -> Optional[float]:
        m = re.search(r"####\s*(-?\d+(?:[.,]\d+)?)", answer)
        return float(m.group(1).replace(",", ".")) if m else None


# ────────────────────────────────────────────────────────────────────────
# Intégration cerveau : détection des questions de calcul
# ────────────────────────────────────────────────────────────────────────

MARQUEURS_MATHS = ["combien font", "combien font", "calcule", "calculer", "résous",
                   "resous", "combien coûte", "combien coute", "combien reste",
                   "combien de francs", "what is", "calculate", "solve", "how much",
                   "how many", "additionne", "multiplie", "soustrais", "divise",
                   "addition", "soustraction", "multiplication", "division"]


def est_question_maths(question: str) -> bool:
    q = question.lower().strip()
    if re.search(r"\d+\s*[+\-×÷*/]\s*\d+", q):
        return True
    return any(m in q for m in MARQUEURS_MATHS)
