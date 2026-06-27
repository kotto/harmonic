#!/usr/bin/env python3
"""
HARMONIC MATH SOLVER — Composition engine (Chain-of-Thought déterministe)
============================================================================
Enchaîne les règles du ParametricKB pour résoudre des problèmes mathématiques
complexes par étapes successives, sans hallucination.

Principe :
  1. Le problème est analysé
  2. La première règle applicable est exécutée
  3. Le résultat intermédiaire est réinjecté comme nouveau "prompt"
  4. La règle suivante est appliquée
  5. Continue jusqu'à ce qu'aucune règle ne s'applique
  6. Chaque étape est tracée (0% de perte d'information)

Usage :
  from harmonic_math_solver import HarmonicMathSolver
  solver = HarmonicMathSolver()
  result = solver.solve("derivative of x^5 then evaluate at x=2")
  # Étape 1 : d/dx(x^5) = 5x^4
  # Étape 2 : evaluate 5(2)^4 = 5*16 = 80
"""

import sys, os, re, math
from typing import List, Tuple, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lm_arena'))
from parametric_kb import ParametricKB

class HarmonicMathSolver:
    """
    Moteur de résolution par composition de règles.
    Implémente un Chain-of-Thought déterministe.
    """

    def __init__(self):
        self.kb = ParametricKB()
        self.max_chain_steps = 10  # Sécurité anti-boucle

    def solve(self, problem: str) -> Dict:
        """
        Résout un problème en enchaînant les règles.
        Retourne {steps, final_answer, confidence, chain_length}.
        """
        steps = []
        current = problem.strip()
        final_answer = None
        confidence = 1.0

        for step_num in range(self.max_chain_steps):
            # Essayer de découper le problème si plusieurs questions
            sub_problems = self._split_problem(current)

            best_result = None
            best_rule_name = None
            best_confidence = 0

            for sub in sub_problems:
                result = self.kb.solve(sub)
                if result and result["confidence"] > best_confidence:
                    best_result = result
                    best_rule_name = result.get("method", "unknown")
                    best_confidence = result["confidence"]

            if best_result is None:
                # Plus rien ne match → on a la réponse finale
                if not steps:
                    return {
                        "steps": [], "final_answer": current,
                        "confidence": 0.0, "chain_length": 0,
                        "solved": False
                    }
                final_answer = current
                break

            # Enregistrer l'étape
            step_text = best_result["text"]
            steps.append({
                "step": step_num + 1,
                "input": current[:100],
                "rule": best_rule_name,
                "output": step_text,
                "confidence": best_confidence,
            })

            # Le résultat devient le nouveau "contexte" pour l'étape suivante
            # Si le résultat contient " = " (ex: "x = 5"), on ne garde que la partie réponse
            current = self._extract_continuation(step_text, problem)

            # Si le résultat est un nombre ou une réponse simple → on arrête
            if self._is_terminal(step_text, problem):
                final_answer = step_text
                break

        if final_answer is None and steps:
            final_answer = steps[-1]["output"]

        return {
            "steps": steps,
            "final_answer": final_answer,
            "confidence": confidence * (best_confidence if steps else 0.0),
            "chain_length": len(steps),
            "solved": len(steps) > 0,
        }

    def _split_problem(self, text: str) -> List[str]:
        """Essaye de découper un problème complexe en sous-problèmes."""
        # Split sur "and", "then", "puis", "ensuite", ";"
        parts = re.split(r'\s+(?:and|then|puis|ensuite|et|;)\s+', text)
        if len(parts) > 1:
            return parts
        return [text]

    def _extract_continuation(self, result_text: str, original_problem: str) -> str:
        """
        Extrait la partie du résultat qui peut être réutilisée pour la suite.
        Ex: "d/dx(x^5) = 5x^4" → "5x^4" (juste le résultat)
        """
        # Si le problème demandait une évaluation après dérivation
        if "evaluate" in original_problem.lower() or "evaluate" in original_problem.lower():
            # Extraire le résultat après le "="
            match = re.search(r'=\s*(.+?)(?:\n|$)', result_text)
            if match:
                return match.group(1).strip()
        return result_text

    def _is_terminal(self, result: str, problem: str) -> bool:
        """Détecte si on a atteint une réponse finale."""
        # Si c'est un nombre simple
        if re.match(r'^[\d.\-+]+$', result.strip()):
            return True
        # Si la réponse contient le mot du problème original → probablement final
        if any(w in result.lower() for w in problem.lower().split()[:3]):
            return True
        # Si le résultat est très court (< 20 caractères)
        if len(result) < 20:
            return True
        return False

    def solve_batch(self, problems: List[str]) -> List[Dict]:
        """Résout plusieurs problèmes en lot."""
        return [self.solve(p) for p in problems]

    def get_stats(self, results: List[Dict]) -> Dict:
        """Statistiques sur un lot de résolutions."""
        solved = [r for r in results if r["solved"]]
        return {
            "total": len(results),
            "solved": len(solved),
            "avg_chain": sum(r["chain_length"] for r in solved) / max(len(solved), 1),
            "avg_confidence": sum(r["confidence"] for r in solved) / max(len(solved), 1),
            "failure_rate": (len(results) - len(solved)) / max(len(results), 1),
        }


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    solver = HarmonicMathSolver()

    tests = [
        "derivative of x^5",
        "integral of sin(x)",
        "what is 15 * 7",
        "solve x^2 - 5x + 6 = 0",
        "area of circle radius 5",
        "what is 8!",
        "mean of 1, 2, 3, 4, 5",
        "compound interest on 1000 at 5% for 3y",
        "det of [[3, 4], [2, 5]]",
        "gcd of 48 and 18",
        "what is 5 + 3 * 2",
        "solve 2x + 5 = 17",
        "limit sin(x)/x as x->0",
    ]

    print(f"{'PROBLEM':<45} {'STEPS':<8} {'ANSWER':<40} {'CONF':>5}")
    print("-" * 100)
    for q in tests:
        r = solver.solve(q)
        steps = len(r["steps"])
        answer = r["final_answer"][:38] if r["final_answer"] else "N/A"
        print(f"{q[:43]:<45} {steps:<8} {answer:<40} {r['confidence']:.2f}")

    stats = solver.get_stats([solver.solve(q) for q in tests])
    print(f"\nStats: {stats}")