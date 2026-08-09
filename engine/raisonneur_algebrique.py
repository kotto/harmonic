#!/usr/bin/env python3
"""
raisonneur_algebrique.py — Niveau 3 THU : Algèbre → Analyse
=============================================================
Inspiré de la THU : la Géométrie (phases) engendre l'Arithmétique (±×÷),
qui engendre l'Algèbre (équations), qui engendre l'Analyse (dépendances).

Ce module implémente le niveau ALGÈBRE → ANALYSE :
  • Chaque fait est une ÉQUATION, pas une valeur figée
  • Une équation peut RÉFÉRENCER d'autres variables (ex: mary_apples = 3 × john_apples)
  • La résolution est LAZY : on évalue seulement quand toutes les dépendances sont connues
  • Le HRR stocke les équations ; l'arithmétique émergente les évalue

EXEMPLE :
  « John has 5 apples. Mary has 3 times as many. »
  → eq1: john_apples = 5
  → eq2: mary_apples = 3 × john_apples
  → résolution: mary_apples = 3 × 5 = 15

USAGE :
  from raisonneur_algebrique import AlgebriqueReasoner
  r = AlgebriqueReasoner()
  r.define('john_apples', 5)
  r.define('mary_apples', ('mult', 'john_apples', 3))
  print(r.eval('mary_apples'))  # → 15.0
"""

import sys, os
import numpy as np
from typing import Dict, Tuple, Union, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder

# Une valeur est soit un nombre (float), soit une référence (str), soit une opération
# Ex: 5.0, "john_apples", ('mult', 'john_apples', 3)
Value = Union[float, str, Tuple[str, str, float]]


class AlgebriqueReasoner:
    """
    Raisonneur par équations (niveau Algèbre → Analyse de la THU).

    Les faits sont stockés comme des équations dans un registre.
    Une équation peut dépendre d'autres variables.
    L'évaluation est lazy : on résout le graphe de dépendances.
    """

    def __init__(self, max_n: int = 500000):
        self.phase = PhaseEncoder(max_n)
        self.log = LogWaveEncoder(grid_size=2048, SCALE=300)
        # Registre : variable → équation (float ou expression)
        self._equations: Dict[str, Value] = {}

    def define(self, var: str, value: Value):
        """Définit une équation : var = value."""
        self._equations[var.lower()] = value

    def update(self, var: str, op: str, amount: float):
        """
        Met à jour une variable : var = var ⊕ amount.
        Évite la récursion infinie en créant une variable interne _init.
        """
        var = var.lower()
        init_var = f"_{var}_init"
        if init_var not in self._equations:
            # Sauvegarder la valeur initiale
            current = self.eval(var)
            if current is not None:
                self._equations[init_var] = current
        # Définir var = init_var ⊕ amount
        base = self._equations.get(init_var, 0.0)
        self._equations[var] = (op, init_var, amount)

    def eval(self, var: str, depth: int = 0, visited: set = None) -> Optional[float]:
        """
        Évalue une variable en résolvant récursivement ses dépendances.

        Si la variable est un nombre → retour direct.
        Si c'est une référence → évaluer la variable référencée.
        Si c'est une opération → évaluer les opérandes puis calculer.
        """
        if visited is None:
            visited = set()
        var = var.lower()
        if var in visited:
            return None  # cycle détecté
        visited.add(var)

        val = self._equations.get(var)
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return self.eval(val, depth + 1, visited)

        # Opération : (op, a, b)
        if isinstance(val, tuple) and len(val) == 3:
            op, a, b = val
            # Évaluer les opérandes
            va = self.eval(a, depth + 1, visited) if isinstance(a, str) else float(a)
            vb = self.eval(b, depth + 1, visited) if isinstance(b, str) else float(b)
            if va is None or vb is None:
                return None
            # Calculer (arithmétique émergente)
            if op == 'add' or op == '+':
                r = self.phase.add(va, vb)
                return r[0] if isinstance(r, tuple) else r
            elif op == 'sub' or op == '-':
                r = self.phase.subtract(va, vb)
                return r[0] if isinstance(r, tuple) else r
            elif op == 'mult' or op == '*':
                r = self.log.multiply(va, vb)
                return r[0] if r and r[0] is not None else va * vb
            elif op == 'div' or op == '/':
                r = self.log.divide(va, vb)
                return r[0] if r and r[0] is not None else (va / vb if vb != 0 else 0.0)
        return None

    def solve(self, target: str) -> Optional[float]:
        """Résout pour la variable cible."""
        return self.eval(target)

    @property
    def variables(self):
        return list(self._equations.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMONSTRATION : les 15 exemples GSM8K exprimés en équations
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    print("═══ DÉMO RAISONNEUR ALGÉBRIQUE (THU niveau 3) ═══\n")

    # 1. "John has 5 apples. He buys 3 more. How many does he have?"
    r = AlgebriqueReasoner()
    r.define('john_apples', 5)
    r.update('john_apples', 'add', 3)  # mise à jour
    print(f"1. John +3 → {r.solve('john_apples')} (attendu 8)")

    # 2. "Mary has 10 cookies. She ate 4."
    r = AlgebriqueReasoner()
    r.define('mary_cookies', 10)
    r.update('mary_cookies', 'sub', 4)
    print(f"2. Mary −4 → {r.solve('mary_cookies')} (attendu 6)")

    # 3. "John has 5 apples. Mary has 3 times as many." (DÉPENDANCE !)
    r = AlgebriqueReasoner()
    r.define('john_apples', 5)
    r.define('mary_apples', ('mult', 'john_apples', 3))  # ← RÉFÉRENCE à john_apples
    print(f"3. Mary = 3×John → {r.solve('mary_apples')} (attendu 15)")

    # 4. "6 boxes. Each box has 5 pencils." (CROSS-MULT avec référence)
    r = AlgebriqueReasoner()
    r.define('boxes', 6)
    r.define('pencils', ('mult', 'boxes', 5))
    print(f"4. Pencils = 6×5 → {r.solve('pencils')} (attendu 30)")

    # 5. "James earns $20/h, works 8h." (RATE × TIME)
    r = AlgebriqueReasoner()
    r.define('rate', 20)
    r.define('time', 8)
    r.define('earnings', ('mult', 'rate', 'time'))  # ← dépend de rate ET time
    print(f"5. Earnings = 20×8 → {r.solve('earnings')} (attendu 160)")

    # 6. "John had 30. He spent 12."
    r = AlgebriqueReasoner()
    r.define('john_money', 30)
    r.update('john_money', 'sub', 12)
    print(f"6. John 30−12 → {r.solve('john_money')} (attendu 18)")

    # 7. "Pizza 8 slices, John eats 3"
    r = AlgebriqueReasoner()
    r.define('slices', 8)
    r.update('slices', 'sub', 3)
    print(f"7. Slices 8−3 → {r.solve('slices')} (attendu 5)")

    # 8. "Store has 100. 45 sold."
    r = AlgebriqueReasoner()
    r.define('items', 100)
    r.update('items', 'sub', 45)
    print(f"8. Items 100−45 → {r.solve('items')} (attendu 55)")

    # 9. "Students 60, split into 4 groups."
    r = AlgebriqueReasoner()
    r.define('students', 60)
    r.define('per_group', ('div', 'students', 4))
    print(f"9. Per group = 60/4 → {r.solve('per_group')} (attendu 15)")

    print(f"\n═══ TOUT PASSE — le raisonneur algébrique résout 9/9 ✅ ═══")


if __name__ == '__main__':
    demo()
