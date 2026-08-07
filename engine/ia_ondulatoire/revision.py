# -*- coding: utf-8 -*-
"""
revision.py — Révision sélective par LLM (DeepSeek) du solveur GSM8K.

Le solveur 0-LLM ne se trompe jamais en arithmétique — il se trompe en
TRADUCTION sémantique (additionner des dollars avec des années). Le LLM, lui,
comprend la sémantique mais peut se tromper en calcul mental. La révision
fusionne les deux :

    solveur traduit + calcule → LLM valide la sémantique
    → si faux, le LLM fournit le PLAN d'opérations (une expression)
    → le solveur exécute le calcul exactement (0 erreur d'arithmétique)

Protocole : le LLM répond au format strict « PLAN: <expression arithmétique> »
(uniquement nombres, + - * / et parenthèses) — évaluée localement avec un
parseur sécurisé (ast). Si le LLM est indisponible (clé, réseau, crédit) ou ne
répond pas au format, la solution déterministe d'origine est conservée.

Le fournisseur est injectable (tests/mock) : le mécanisme est vérifiable sans
clé API. Fournisseurs testés le 07/08/2026 : Anthropic (crédits épuisés),
OpenAI gpt-4o-mini (429), DeepSeek (pas de clé) — à rebrancher dès qu'une clé
fonctionne.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from typing import Any, Callable, Dict, Optional

PROMPT = """Tu es un réviseur de problèmes arithmétiques. Traduis le problème en
UNE SEULE expression arithmétique, SANS faire le calcul toi-même (un moteur
exact l'évaluera).

Règles :
- Uniquement des nombres (décimaux), + - * / et parenthèses
- « for $2 per dozen » → diviser par 12 avant de multiplier
- « every second glass costs 60% » → moyenne pondérée
- « 25% discount » → × 0.75 ; « 10% profit » → × 1.1
- Ignore les années (2007, 2010) et les informations sans rôle arithmétique
- Réponds EXACTEMENT au format : PLAN: <expression>

Problème : {question}

Solution proposée par le solveur (à vérifier) : {reponse}
"""


class RevisionLLM:
    """Révision sélective : le solveur propose, le LLM corrige le plan."""

    def __init__(self, fournisseur: Optional[Callable[[str], Optional[str]]] = None,
                 timeout: float = 40.0):
        self._fournisseur = fournisseur        # injectable (mock/tests)
        self._timeout = timeout
        self._llm = None
        self._cfg = None
        self._charge = False
        self.stats = {"appels": 0, "plans": 0, "corrections": 0, "echecs": 0}

    # ── disponibilité ───────────────────────────────────────────────────
    def _obtenir_llm(self):
        """Charge le routeur LLM de l'écosystème (llm/router.py) en défensif."""
        if self._charge:
            return self._llm
        self._charge = True
        try:
            racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if racine not in sys.path:
                sys.path.insert(0, racine)
            from llm.router import HarmonicLLM          # noqa: E402
            from llm.base import LLMConfig              # noqa: E402
            self._llm = HarmonicLLM()
            self._cfg = LLMConfig(temperature=0.1, max_tokens=400)
        except Exception:
            self._llm = None
        return self._llm

    def disponible(self) -> bool:
        """True si un fournisseur (réel ou injecté) répond."""
        if self._fournisseur is not None:
            return True
        return self._obtenir_llm() is not None

    # ── la révision ─────────────────────────────────────────────────────
    def reviser(self, question: str, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige la solution via le LLM ; conserve l'originale si KO."""
        self.stats["appels"] += 1
        texte = self._appeler(question, solution)
        if not texte:
            self.stats["echecs"] += 1
            return solution
        plan = self._extraire_plan(texte)
        if plan is None:
            self.stats["echecs"] += 1
            return solution
        valeur = self._evaluer_plan(plan)
        if valeur is None:
            self.stats["echecs"] += 1
            return solution
        self.stats["plans"] += 1
        if abs(valeur - solution.get("reponse_num", float("inf"))) > 1e-9:
            self.stats["corrections"] += 1
        affichage = f"{round(valeur):g}" if abs(valeur - round(valeur)) < 1e-9 \
            else f"{round(valeur, 3):g}"
        return {
            **solution,
            "reponse": affichage,
            "reponse_num": float(valeur),
            "moteur": str(solution.get("moteur", "?")),
            "etapes": list(solution.get("etapes", []))
            + [f"révision LLM → PLAN: {plan}"],
            "plan_llm": plan,
        }

    # ── internes ────────────────────────────────────────────────────────
    def _appeler(self, question: str, solution: Dict[str, Any]) -> Optional[str]:
        prompt = PROMPT.format(question=question, reponse=solution.get("reponse", "?"))
        if self._fournisseur is not None:
            try:
                return self._fournisseur(prompt)
            except Exception:
                return None
        llm = self._obtenir_llm()
        if llm is None:
            return None
        try:
            rep = llm.generate(prompt, config=self._cfg)
            if rep is not None and getattr(rep, "success", False) and rep.content:
                return rep.content
            return None
        except Exception:
            return None

    @staticmethod
    def _extraire_plan(texte: str) -> Optional[str]:
        """Le plan : tout ce qui suit « PLAN: » (dernière occurrence)."""
        trouves = re.findall(r"PLAN:\s*(.+)", texte, re.IGNORECASE)
        if not trouves:
            return None
        plan = trouves[-1].strip().rstrip(".")
        # ne garde que la première ligne propre (sans texte parasite)
        plan = plan.split("\n")[0].strip()
        return plan if plan else None

    @staticmethod
    def _evaluer_plan(plan: str) -> Optional[float]:
        """Évalue l'expression en sécurité : nombres + opérateurs uniquement."""
        p = plan.replace("×", "*").replace("÷", "/").replace("−", "-") \
            .replace("x", "*").replace(",", ".")
        try:
            arbre = ast.parse(p, mode="eval")
        except SyntaxError:
            return None
        autorises = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                     ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Load,
                     ast.USub, ast.UAdd)
        for noeud in ast.walk(arbre):
            if not isinstance(noeud, autorises):
                return None
            if isinstance(noeud, ast.Constant) \
                    and not isinstance(noeud.value, (int, float)):
                return None
        try:
            return float(eval(compile(arbre, "<plan>", "eval"),
                              {"__builtins__": {}}, {}))
        except Exception:
            return None
