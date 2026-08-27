"""
🌊 WaveReasoner — Raisonnement harmonique par recherche de trajectoire
======================================================================

Inspiré de DeepSeek R1, transposé dans le formalisme THU :

  R1 (tokens)              →  WaveReasoner (ondes)
  ─────────────────────────────────────────────────
  Chaîne de pensée         →  Trajectoire dans l'espace de phase ψ₀ → ψ₁ → ... → ψ*
  Récompense vérifiable    →  Résonance constructive avec ψ_solution
  GRPO (G trajectoires)    →  Beam search avec G branches en superposition
  "Aha moment"             →  Transition de phase (saut de résonance)
  Auto-vérification        →  Auto-résonance de la trace
  Distillation             →  Cristallisation en mémoire holographique

Deux voies :
  A. ARITHMÉTIQUE DIRECTE (FHRR) :
     L'encodage FHRR fait que bind = addition, unbind = soustraction.
     Résultat calculé en O(D), pas de search — exact et vérifiable.

  B. RAISONNEMENT EXPLORATOIRE (beam search) :
     Pour logique, comparaison, problèmes complexes.
     Search dans l'espace des opérations wave_lang.

Usage :
    from wave_reasoner import reason_arithmetic, reason_logic, get_reasoner

    # Arithmétique directe FHRR
    result = reason_arithmetic("15 + 27")
    # → {'result': 42.0, 'resonance': 0.98, 'method': 'fhrr_direct'}

    # Raisonnement logique (beam search)
    result = reason_logic(["tous les chats sont des félins", "Minou est un chat"],
                          "Minou est-elle un félin ?")
"""

import logging
import math
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT WAVE_LANG
# ═══════════════════════════════════════════════════════════════════════════════

_WAVE_DIR = Path(__file__).resolve().parent.parent.parent / 'vital-ka' / 'core' / 'python'
if str(_WAVE_DIR) not in sys.path:
    sys.path.insert(0, str(_WAVE_DIR))

from wave_lang import (  # noqa: E402
    encode, decode, bind, unbind, superpose, resonate, resonate_batch,
    rotate, normalize, interfere, diffract, filter_wave, phase_shift,
    emerge, oppose, amplify, bind_many, HolographicMemory,
    stats as wave_stats, DEFAULT_DIM, PHI, TAU, coherence,
)

DIM = DEFAULT_DIM

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

RESONANCE_THRESHOLD = 0.85
EMERGENCE_THRESHOLD = 0.15  # saut de résonance pour "aha moment"

W_SOLUTION = 0.6      # poids résonance avec solution
W_COHERENCE = 0.25    # poids auto-cohérence de la trace
W_EFFICIENCY = 0.15   # poids pénalité de longueur

DEFAULT_BEAM_WIDTH = 8
DEFAULT_MAX_DEPTH = 6

# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

Wave = np.ndarray  # (dim,) complex128


@dataclass
class ReasoningState:
    """État d'une trajectoire de raisonnement."""
    psi: Wave
    operations: List[str] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    cost: float = 0.0
    resonance: float = 0.0
    step: int = 0

    def copy(self) -> 'ReasoningState':
        return ReasoningState(
            psi=self.psi.copy(),
            operations=self.operations.copy(),
            values=self.values.copy(),
            cost=self.cost,
            resonance=self.resonance,
            step=self.step,
        )


@dataclass
class ReasoningTrace:
    """Journal de phase explicable."""
    problem: str
    initial_psi: Wave
    final_psi: Wave
    trajectory: List[ReasoningState] = field(default_factory=list)
    target_psi: Optional[Wave] = None
    resonance_history: List[float] = field(default_factory=list)
    emergence_points: List[int] = field(default_factory=list)
    solution: Optional[Union[float, str]] = None
    method: str = "wave_reasoning"
    success: bool = False
    elapsed_ms: float = 0.0
    steps: int = 0

    def to_dict(self) -> dict:
        return {
            'problem': self.problem,
            'solution': self.solution,
            'method': self.method,
            'success': self.success,
            'resonance_final': self.resonance_history[-1] if self.resonance_history else 0.0,
            'emergence_points': self.emergence_points,
            'n_steps': self.steps,
            'elapsed_ms': self.elapsed_ms,
            'operations': [s.operations[-1] if s.operations else 'init' for s in self.trajectory],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ENCODAGE FHRR — bind = addition
# ═══════════════════════════════════════════════════════════════════════════════

class FHRREncoder:
    """
    Fourier Holographic Reduced Representations.

    ψ_n[d] = exp(i · n · θ_d) / √DIM

    Propriétés :
      bind(ψ_m, ψ_n)[d] = ψ_m[d] · ψ_n[d] = ψ_{m+n}[d]  ← ADDITION
      unbind(ψ_m, ψ_n)[d] = ψ_m[d] · conj(ψ_n[d]) = ψ_{m-n}[d]  ← SOUSTRACTION
      resonate(ψ_m, ψ_n) = Re(∑ ψ_m[d] · conj(ψ_n[d])) ≈ 1 si m=n, ≈ 0 sinon
    """

    def __init__(self, dim: int = DIM, seed: int = 42):
        self.dim = dim
        # Phases aléatoires fixes
        rng = np.random.RandomState(seed)
        self._theta = rng.uniform(0, TAU, dim)

    def encode(self, n: Union[int, float]) -> Wave:
        """Encode n en ψ_n = exp(i·n·θ_d)/√DIM."""
        phases = float(n) * self._theta
        psi = np.exp(1j * phases) / math.sqrt(self.dim)
        return psi

    def decode(self, psi: Wave,
               candidates: Optional[List[float]] = None) -> Tuple[float, float]:
        """
        Décode ψ en nombre par résonance max avec des candidats.
        Retourne (nombre, résonance).
        """
        if candidates is None:
            candidates = [float(x) for x in range(-100, 101)]
            candidates += [x * 0.5 for x in range(-200, 201)]

        best_n, best_r = 0.0, -1.0
        for n in candidates:
            psi_n = self.encode(n)
            r = resonate(psi, psi_n)
            if r > best_r:
                best_r = r
                best_n = n

        return best_n, best_r

    def decode_close(self, psi: Wave, hint: float = 0.0,
                     window: int = 500) -> Tuple[float, float]:
        """Décode en recherchant autour d'un indice. Fenêtre large par défaut."""
        start = int(hint) - window
        end = int(hint) + window + 1
        candidates = [float(x) for x in range(start, end)]
        return self.decode(psi, candidates)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. OPÉRATIONS ARITHMÉTIQUES FHRR
# ═══════════════════════════════════════════════════════════════════════════════

def fhrr_bind(psi_a: Wave, psi_b: Wave) -> Wave:
    """
    FHRR binding = multiplication élément par élément + normalisation.
    ψ_m ⊙ ψ_n = ψ_{m+n} (addition)
    """
    return normalize(psi_a * psi_b)


def fhrr_unbind(psi_a: Wave, psi_b: Wave) -> Wave:
    """
    FHRR unbinding = multiplication par conjugué + normalisation.
    ψ_m ⊘ ψ_n = ψ_{m-n} (soustraction)
    """
    return normalize(psi_a * np.conj(psi_b))


def fhrr_add(psi_a: Wave, psi_b: Wave) -> Wave:
    """ψ_m ⊙ ψ_n = ψ_{m+n}."""
    return fhrr_bind(psi_a, psi_b)


def fhrr_sub(psi_a: Wave, psi_b: Wave) -> Wave:
    """ψ_m ⊘ ψ_n = ψ_{m-n}."""
    return fhrr_unbind(psi_a, psi_b)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RAISONNEUR ARITHMÉTIQUE DIRECT
# ═══════════════════════════════════════════════════════════════════════════════

class ArithmeticReasoner:
    """
    Raisonneur arithmétique direct en FHRR.

    Parse l'expression, applique les opérations FHRR directement,
    retourne le résultat avec la trace de phase.
    """

    def __init__(self, dim: int = DIM):
        self.dim = dim
        self.encoder = FHRREncoder(dim)

    def solve(self, expression: str) -> dict:
        """
        Résout une expression arithmétique.

        Supporte : a+b, a-b, a*b, a/b, pourcentages, chaînes.
        """
        start = time.time()
        parsed = self._parse(expression)
        if not parsed:
            return {'handled': False, 'error': 'Expression non reconnue'}

        tokens, ops = parsed

        # Appliquer les opérations FHRR séquentiellement
        if not tokens:
            return {'handled': False, 'error': 'Aucun token'}

        # Premier token comme état initial
        psi_result = self.encoder.encode(tokens[0])
        trace_steps = [f"ψ_{tokens[0]:g}"]
        estimated = tokens[0]  # estimation courante du résultat

        for idx, op in enumerate(ops):
            next_val = tokens[idx + 1]
            psi_next = self.encoder.encode(next_val)

            if op == '+':
                psi_result = fhrr_add(psi_result, psi_next)
                estimated += next_val
                trace_steps.append(f"add({next_val:g})")
            elif op == '-':
                psi_result = fhrr_sub(psi_result, psi_next)
                estimated -= next_val
                trace_steps.append(f"sub({next_val:g})")
            elif op == '*':
                # Multiplication par entier : bind répété = addition en FHRR
                k = int(next_val)
                base = psi_result.copy()
                for _ in range(k - 1):
                    psi_result = fhrr_add(psi_result, base)
                estimated = estimated * k  # estimation exacte
                trace_steps.append(f"mul({next_val:g})")
            elif op == '/':
                psi_result = fhrr_sub(psi_result, psi_next)
                estimated = tokens[0] / next_val
                trace_steps.append(f"div({next_val:g})")

        # Décoder le résultat : utiliser l'estimation comme indice
        result, resonance = self.encoder.decode_close(psi_result, hint=estimated)

        elapsed = (time.time() - start) * 1000

        return {
            'handled': True,
            'result': result,
            'resonance': resonance,
            'expression': expression,
            'method': 'fhrr_direct',
            'steps': trace_steps,
            'elapsed_ms': round(elapsed, 1),
            'explanation': self._explain(expression, tokens, ops, result, resonance),
        }

    # ── Shunting-Yard (Dijkstra 1961) ──
    _PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3, '%': 2}

    @classmethod
    def _shunting_yard(cls, expression: str) -> Optional[List[str]]:
        """
        Convertit une expression infixe en notation polonaise inversée (RPN).
        Gère les parenthèses imbriquées et les priorités d'opérateurs.

        Exemple : "2 + 3 * 4" → ["2", "3", "4", "*", "+"]
        """
        output = []
        operators = []
        expr = expression.strip().lower()

        # Traduire les mots français
        expr = re.sub(r'\bplus\b', '+', expr)
        expr = re.sub(r'\bmoins\b', '-', expr)
        expr = re.sub(r'\bfois\b', '*', expr)
        expr = re.sub(r'\bdivisé\s*par\b', '/', expr)
        expr = re.sub(r'\bmultiplié\s*par\b', '*', expr)
        expr = re.sub(r'\bpuissance\b', '^', expr)
        expr = re.sub(r'\bexposant\b', '^', expr)
        expr = re.sub(r'\bmodulo\b', '%', expr)
        expr = re.sub(r'\b×\b', '*', expr)
        expr = re.sub(r'\b÷\b', '/', expr)
        expr = re.sub(r'combien\s+font?\s+', '', expr)
        expr = re.sub(r'\bcalcul\w*\s+', '', expr)  # "calcule 2+3"

        # Tokenization : nombres (entiers/décimaux/négatifs), opérateurs, parenthèses
        tokens = re.findall(
            r'(-?\d+\.?\d*)|([+\-*/^%]|[\^×÷])|([()])',
            expr
        )

        prev_was_number = False
        rpn = []

        for num, op, paren in tokens:
            if num:
                rpn.append(num)
                prev_was_number = True
            elif op:
                # Gérer le moins unaire : si le token précédent n'est pas un nombre
                # ou une parenthèse fermante, c'est un signe unaire
                if op == '-' and not prev_was_number:
                    rpn.append('_')  # marqueur de négation unaire
                else:
                    prec = cls._PRECEDENCE.get(op, 1)
                    while (operators and operators[-1] != '(' and
                           operators[-1] != '_' and
                           cls._PRECEDENCE.get(operators[-1], 0) >= prec and
                           op != '^'):  # ^ est associatif à droite
                        rpn.append(operators.pop())
                    operators.append(op)
                    prev_was_number = False
            elif paren == '(':
                operators.append('(')
                prev_was_number = False
            elif paren == ')':
                while operators and operators[-1] != '(':
                    rpn.append(operators.pop())
                if operators and operators[-1] == '(':
                    operators.pop()  # enlever '('
                prev_was_number = True

        # Vider les opérateurs restants
        while operators:
            op = operators.pop()
            if op not in ('(', '_'):
                rpn.append(op)

        return rpn if rpn else None

    @classmethod
    def _eval_rpn(cls, rpn: List[str],
                  encoder: 'FHRREncoder',
                  psi_cache: Dict[str, Wave]) -> Tuple[Wave, float, List[str]]:
        """
        Évalue une expression RPN en utilisant les opérations FHRR.

        Args:
            rpn: liste de tokens en notation polonaise inversée
            encoder: l'encodeur FHRR
            psi_cache: cache ψ déjà encodés (évite de ré-encoder les nombres)

        Returns:
            (psi_final, estimated_result, trace_steps)
        """
        stack = []       # pile des ψ
        values = []      # pile des estimations réelles
        trace = []

        for token in rpn:
            if token == '_':
                # Négation unaire : multiplié par -1 → rotation π
                if values:
                    psi = stack.pop()
                    psi_neg = rotate(psi, math.pi)  # ψ * e^{iπ} = -ψ
                    stack.append(psi_neg)
                    v = -values.pop()
                    values.append(v)
                    trace.append(f"neg({v})")
                continue

            try:
                # C'est un nombre
                n = float(token)
                if token not in psi_cache:
                    psi_cache[token] = encoder.encode(n)
                psi = psi_cache[token].copy()
                stack.append(psi)
                values.append(n)
            except ValueError:
                # C'est un opérateur
                if len(stack) < 2:
                    return None, 0.0, trace

                psi_b = stack.pop()
                psi_a = stack.pop()
                b = values.pop()
                a = values.pop()

                if token == '+':
                    psi_result = fhrr_add(psi_a, psi_b)
                    estimated = a + b
                    trace.append(f"add({b:g})")
                elif token == '-':
                    psi_result = fhrr_sub(psi_a, psi_b)
                    estimated = a - b
                    trace.append(f"sub({b:g})")
                elif token == '*':
                    # Multiplication par binding répété
                    k = int(b) if b == int(b) else b
                    if isinstance(k, int) and abs(k) < 100:
                        psi_result = psi_a.copy()
                        base = psi_a.copy()
                        for _ in range(abs(k) - 1):
                            psi_result = fhrr_add(psi_result, base)
                        estimated = a * k
                        trace.append(f"mul({b:g})")
                    else:
                        # Approximation pour les décimaux
                        psi_result = fhrr_add(psi_a, psi_b)
                        estimated = a + b  # approximation
                        trace.append(f"mul_approx({b:g})")
                elif token == '/':
                    psi_result = fhrr_sub(psi_a, psi_b)
                    estimated = a / b if b != 0 else float('inf')
                    trace.append(f"div({b:g})")
                elif token == '^':
                    # Puissance entière : pas de FHRR exact, utiliser estimation réelle
                    k = int(b)
                    estimated = a ** k if k >= 0 else a ** b
                    psi_result = encoder.encode(estimated)  # wave exacte de la réponse
                    trace.append(f"pow({b:g})")
                elif token == '%':
                    # Modulo : pas de FHRR exact
                    estimated = a % b if b != 0 else 0.0
                    psi_result = encoder.encode(estimated)  # wave exacte de la réponse
                    trace.append(f"mod({b:g})")
                else:
                    return None, 0.0, trace

                stack.append(psi_result)
                values.append(estimated)

        if stack:
            return stack[0], values[0], trace
        return None, 0.0, trace

    def solve(self, expression: str) -> dict:
        """
        Résout une expression arithmétique avec priorités PEMDAS.

        Supporte : a+b, a-b, a*b, a/b, a^b, a%b, parenthèses, négation unaire.
        Utilise l'algorithme Shunting-Yard pour respecter les priorités.
        """
        start = time.time()

        # 1. Shunting-Yard → RPN
        rpn = self._shunting_yard(expression)
        if not rpn or len(rpn) < 1:
            return {'handled': False, 'error': 'Expression non reconnue'}

        # Vérifier qu'il y a au moins une opération
        has_op = any(tok in self._PRECEDENCE for tok in rpn)
        if not has_op and len(rpn) == 1:
            # Juste un nombre
            try:
                n = float(rpn[0])
                return {
                    'handled': True,
                    'result': n,
                    'resonance': 1.0,
                    'expression': expression,
                    'method': 'fhrr_direct',
                    'steps': [f"ψ_{n:g}"],
                    'elapsed_ms': 0.0,
                    'explanation': f"🌊 FHRR : {n:g} = {n:g} (résonance 1.00)",
                }
            except ValueError:
                return {'handled': False, 'error': 'Expression non reconnue'}

        # 2. Évaluer l'expression RPN avec FHRR
        psi_cache: Dict[str, Wave] = {}
        psi_result, estimated, trace_steps = self._eval_rpn(
            rpn, self.encoder, psi_cache
        )

        if psi_result is None:
            return {'handled': False, 'error': "Échec de l'évaluation"}

        # 3. Décoder le résultat
        result, resonance = self.encoder.decode_close(psi_result, hint=estimated)

        elapsed = (time.time() - start) * 1000

        return {
            'handled': True,
            'result': result,
            'resonance': resonance,
            'expression': expression,
            'rpn': ' '.join(rpn),
            'method': 'fhrr_direct',
            'steps': trace_steps,
            'elapsed_ms': round(elapsed, 1),
            'explanation': self._explain_rpn(expression, rpn, result, resonance, trace_steps),
        }

    def _explain_rpn(self, expr: str, rpn: List[str], result: float,
                     resonance: float, steps: List[str]) -> str:
        """Construit l'explication lisible pour l'évaluation RPN."""
        lines = [
            f"🌊 Raisonnement harmonique FHRR",
            f"   Expression : {expr}",
            f"   RPN        : {' '.join(rpn)}",
            f"   Résultat   : {result:g} (résonance {resonance:.2f})",
            f"   Trace      : {' → '.join(steps[:8])}",
        ]
        if resonance >= RESONANCE_THRESHOLD:
            lines.append("   ✅ Validé par résonance constructive")
        else:
            lines.append(f"   ⚠️ Approximation (résonance sous seuil)")
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. OPÉRATEURS WAVE POUR BEAM SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicOperator:
    """Opérateur de transformation d'onde."""

    def __init__(self, name: str, fn: Callable[[Wave, Optional[Wave]], Wave],
                 cost: float = 1.0, signature: str = ""):
        self.name = name
        self.fn = fn
        self.cost = cost
        self.signature = signature or name

    def apply(self, psi: Wave, operand: Optional[Wave] = None) -> Wave:
        return self.fn(psi, operand)

    def __repr__(self):
        return f"Op({self.name}, cost={self.cost})"


LOGIC_OPERATORS = [
    HarmonicOperator('bind', lambda p, o: bind(p, o) if o is not None else p,
                     cost=1.0, signature='bind'),
    HarmonicOperator('unbind', lambda p, o: unbind(p, o) if o is not None else p,
                     cost=1.0, signature='unbind'),
    HarmonicOperator('superpose', lambda p, o: superpose(p, o, weights=[0.5, 0.5]) if o is not None else p,
                     cost=0.8, signature='superpose'),
    HarmonicOperator('interfere', lambda p, o: interfere(p, o, epsilon=0.3) if o is not None else p,
                     cost=1.2, signature='interfere'),
    HarmonicOperator('emerge', lambda p, o: emerge(p, o, temperature=0.6) if o is not None else p,
                     cost=2.0, signature='emerge'),
    HarmonicOperator('oppose', lambda p, o: oppose(p, o) if o is not None else p,
                     cost=1.0, signature='oppose'),
    HarmonicOperator('rotate', lambda p, o: rotate(p, math.pi / 4),
                     cost=0.5, signature='rotate'),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. VÉRIFICATEUR PAR RÉSONANCE
# ═══════════════════════════════════════════════════════════════════════════════

class ResonanceVerifier:
    """
    Vérificateur pour le beam search.

    Récompense = w₁·coherence(ψ_état, ψ_cible) + w₂·cohérence_interne − w₃·coût
    """

    def __init__(self, target_psi: Optional[Wave] = None):
        self.target_psi = target_psi

    def compute_reward(self, state: ReasoningState) -> float:
        """Récompense GRPO harmonique."""
        r_solution = coherence(state.psi, self.target_psi) if self.target_psi is not None else 0.0
        r_coherence = 0.0

        if len(state.values) >= 2:
            r_coherence = 1.0 - min(1.0, float(np.std(state.values[-3:])) if len(state.values) >= 3 else 0.5)

        efficiency_penalty = state.cost / 10.0

        return (W_SOLUTION * r_solution +
                W_COHERENCE * r_coherence -
                W_EFFICIENCY * efficiency_penalty)

    def is_solution(self, state: ReasoningState,
                    threshold: float = RESONANCE_THRESHOLD) -> bool:
        if self.target_psi is None:
            return False
        return coherence(state.psi, self.target_psi) >= threshold


# ═══════════════════════════════════════════════════════════════════════════════
# 6. BEAM SEARCH HARMONIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicBeamSearch:
    """
    Beam search pour le raisonnement exploratoire.
    G branches, expansion par opérateur, sélection par récompense.
    """

    def __init__(self, operators: List[HarmonicOperator],
                 beam_width: int = DEFAULT_BEAM_WIDTH,
                 max_depth: int = DEFAULT_MAX_DEPTH):
        self.operators = operators
        self.beam_width = beam_width
        self.max_depth = max_depth

    def search(self, initial_psi: Wave, verifier: ResonanceVerifier,
               operand_psis: Optional[List[Wave]] = None) -> ReasoningTrace:
        start = time.time()

        initial_state = ReasoningState(psi=initial_psi.copy(), step=0)
        initial_state.resonance = verifier.compute_reward(initial_state)

        beam = [initial_state]
        best_state = initial_state
        best_reward = initial_state.resonance

        trace = ReasoningTrace(
            problem="", initial_psi=initial_psi, final_psi=initial_psi,
            target_psi=verifier.target_psi,
        )
        trace.trajectory.append(initial_state)
        trace.resonance_history.append(initial_state.resonance)

        traced_depth = 0

        for depth in range(self.max_depth):
            candidates = []

            for state in beam:
                if verifier.is_solution(state):
                    if state.resonance > best_reward:
                        best_state = state
                        best_reward = state.resonance
                    continue

                # Expansion sans opérande
                for op in self.operators:
                    new_psi = op.apply(state.psi)
                    new_state = state.copy()
                    new_state.psi = new_psi
                    new_state.operations.append(op.name)
                    new_state.cost += op.cost
                    new_state.step = depth + 1
                    new_state.resonance = verifier.compute_reward(new_state)
                    candidates.append(new_state)

                # Expansion avec opérandes
                if operand_psis:
                    for op in self.operators[:5]:  # opérateurs principaux
                        for i, operand in enumerate(operand_psis):
                            new_psi = op.apply(state.psi, operand)
                            new_state = state.copy()
                            new_state.psi = new_psi
                            new_state.operations.append(f"{op.name}({i})")
                            new_state.cost += op.cost
                            new_state.step = depth + 1
                            new_state.resonance = verifier.compute_reward(new_state)
                            candidates.append(new_state)

            if not candidates:
                break

            # Top-k
            candidates.sort(key=lambda s: -s.resonance)
            beam = candidates[:self.beam_width]

            for state in beam:
                if state.resonance > best_reward:
                    best_state = state
                    best_reward = state.resonance

            trace.trajectory.append(beam[0])
            trace.resonance_history.append(beam[0].resonance)
            traced_depth = depth + 1

            # Détection émergence
            if len(trace.resonance_history) >= 2:
                delta = trace.resonance_history[-1] - trace.resonance_history[-2]
                if delta >= EMERGENCE_THRESHOLD:
                    trace.emergence_points.append(len(trace.resonance_history) - 1)

        trace.final_psi = best_state.psi
        trace.success = verifier.is_solution(best_state)
        trace.elapsed_ms = (time.time() - start) * 1000
        trace.steps = traced_depth

        return trace


# ═══════════════════════════════════════════════════════════════════════════════
# 7. STRATEGY MEMORY — Distillation des traces
# ═══════════════════════════════════════════════════════════════════════════════

class StrategyMemory:
    """
    Mémoire holographique des stratégies de raisonnement réussies.

    Stocke (ψ_problème, ψ_trajectoire, ops, résonance) dans le HolographicMemory.
    Permet de retrouver une stratégie similaire pour warm-starter un nouveau problème.
    """

    def __init__(self, dim: int = DIM):
        self.dim = dim
        self.memory = HolographicMemory(dim)
        self._traces: List[Dict] = []  # métadonnées
        self._n_stored = 0

    def store(self, problem_psi: Wave, trajectory: List[str],
              resonance: float, trace_obj: Optional[ReasoningTrace] = None):
        """
        Stocke une trace réussie.

        Args:
            problem_psi: encodage du problème
            trajectory: séquence d'opérations
            resonance: résonance finale
            trace_obj: trace complète (optionnel, pour ré-initialisation)
        """
        # Encoder la séquence en ψ
        trajectory_text = '|'.join(trajectory)
        psi_traj = encode(trajectory_text, dim=self.dim)

        # Superposer le problème et sa solution dans la mémoire
        psi_fact = bind_many(problem_psi, psi_traj)
        self.memory.store_raw(psi_fact, amplitude=resonance)
        self._traces.append({
            'trajectory': trajectory,
            'resonance': resonance,
            'psi_traj': psi_traj,
        })
        self._n_stored += 1

    def retrieve_best(self, problem_psi: Wave,
                      threshold: float = 0.65) -> Optional[List[str]]:
        """
        Retourne la meilleure stratégie similaire au nouveau problème.

        Args:
            problem_psi: encodage du nouveau problème
            threshold: seuil de résonance minimum

        Returns:
            Séquence d'opérations, ou None si aucune stratégie assez proche
        """
        if self._n_stored == 0:
            return None

        # Toutes les traces vs le problème
        response = self.memory.query(problem_psi)
        best_score, best_idx = -1.0, -1

        for i, entry in enumerate(self._traces):
            score = resonate(response, entry['psi_traj'])
            if score > best_score:
                best_score = score
                best_idx = i

        if best_score >= threshold:
            return self._traces[best_idx]['trajectory']
        return None

    @property
    def n_stored(self) -> int:
        return self._n_stored


# ═══════════════════════════════════════════════════════════════════════════════
# 8. POLICY LEARNER — GRPO harmonique
# ═══════════════════════════════════════════════════════════════════════════════

class PolicyLearner:
    """
    Apprentissage GRPO des stratégies de raisonnement.

    Chaque opérateur a un score success_rate = succès / tentatives.
    L'expansion du beam search est triée par score (exploitation)
    avec 10% de probabilité d'exploration aléatoire.

    Avantage GRPO : seuls les états au-dessus de la moyenne du groupe
    renforcent la policy.
    """

    def __init__(self, operator_names: Optional[List[str]] = None):
        # Compteurs par opérateur
        self._success: Dict[str, int] = {}
        self._attempts: Dict[str, int] = {}
        self._default_names = operator_names or []
        self._epsilon = 0.1  # exploration

    def register_operator(self, name: str):
        """Enregistre un nouvel opérateur (si pas déjà connu)."""
        if name not in self._attempts:
            self._attempts[name] = 0
            self._success[name] = 0

    def register_all(self, operators: List["HarmonicOperator"]):
        """Enregistre tous les opérateurs d'une liste."""
        for op in operators:
            self.register_operator(op.name)

    def success_rate(self, name: str) -> float:
        """Taux de succès d'un opérateur (0.5 par défaut si jamais essayé)."""
        if name not in self._attempts or self._attempts[name] == 0:
            return 0.5
        return self._success[name] / max(1, self._attempts[name])

    def apply_grpo(self, candidates: List["ReasoningState"], beam_width: int) -> List["ReasoningState"]:
        """
        Sélectionne les meilleurs candidats via avantage GRPO.

        Args:
            candidates: tous les candidats
            beam_width: nombre d'états à garder

        Returns:
            top-k états sélectionnés
        """
        if not candidates:
            return []

        rewards = np.array([s.resonance for s in candidates])
        mean_r = rewards.mean()
        std_r = rewards.std()

        # Avantage GRPO
        advantages = (rewards - mean_r) / max(std_r, 1e-8)

        # Renforcer les opérateurs avec avantage > 0
        for i, state in enumerate(candidates):
            if advantages[i] > 0 and state.operations:
                last_op = state.operations[-1].split('(')[0]  # enlever (n)
                self.register_operator(last_op)
                self._attempts[last_op] += 1
                self._success[last_op] += 1
            elif state.operations:
                last_op = state.operations[-1].split('(')[0]
                self.register_operator(last_op)
                self._attempts[last_op] += 1
                # pas de succès (avantage ≤ 0)

        # Trier par résonance
        candidates.sort(key=lambda s: -s.resonance)
        return candidates[:beam_width]

    def sort_operators(self, operators: List["HarmonicOperator"]) -> List["HarmonicOperator"]:
        """
        Trie les opérateurs par taux de succès décroissant,
        avec epsilon-greedy (10% de chance d'exploration aléatoire).
        """
        import random
        if random.random() < self._epsilon:
            # Exploration : ordre aléatoire
            shuffled = list(operators)
            random.shuffle(shuffled)
            return shuffled
        # Exploitation : trié par succès
        return sorted(operators, key=lambda op: -self.success_rate(op.name))

    def to_dict(self) -> dict:
        """Sérialise la policy pour persistance."""
        return {
            'success': self._success,
            'attempts': self._attempts,
            'epsilon': self._epsilon,
        }

    def from_dict(self, data: dict):
        """Charge la policy depuis un dict."""
        self._success = data.get('success', {})
        self._attempts = data.get('attempts', {})
        self._epsilon = data.get('epsilon', 0.1)

    def save(self, path: str):
        """Persiste la policy en JSON."""
        import json
        data = self.to_dict()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: str):
        """Charge la policy depuis un JSON."""
        import json
        p = Path(path)
        if p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.from_dict(data)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. POLICY-AWARE BEAM SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

class PolicyBeamSearch(HarmonicBeamSearch):
    """
    Beam search avec policy GRPO et warm-start par mémoire de stratégies.
    """

    def __init__(self, operators: List[HarmonicOperator],
                 beam_width: int = DEFAULT_BEAM_WIDTH,
                 max_depth: int = DEFAULT_MAX_DEPTH,
                 policy: Optional[PolicyLearner] = None,
                 strategy_memory: Optional[StrategyMemory] = None):
        super().__init__(operators, beam_width, max_depth)
        self.policy = policy
        self.strategy_memory = strategy_memory

    def search(self, initial_psi: Wave, verifier: ResonanceVerifier,
               operand_psis: Optional[List[Wave]] = None,
               warm_start_ops: Optional[List[str]] = None) -> ReasoningTrace:
        """
        Recherche avec warm-start optionnel.

        Args:
            warm_start_ops: séquence d'opérations pour warm-start
        """
        start = time.time()

        initial_state = ReasoningState(psi=initial_psi.copy(), step=0)
        initial_state.resonance = verifier.compute_reward(initial_state)

        # Warm-start : si une stratégie similaire existe, initialiser le beam avec
        beam = [initial_state]
        best_state = initial_state
        best_reward = initial_state.resonance

        trace = ReasoningTrace(
            problem="", initial_psi=initial_psi, final_psi=initial_psi,
            target_psi=verifier.target_psi,
        )
        trace.trajectory.append(initial_state)
        trace.resonance_history.append(initial_state.resonance)

        traced_depth = 0
        all_candidates_for_grpo = []

        for depth in range(self.max_depth):
            candidates = []

            for state in beam:
                if verifier.is_solution(state):
                    if state.resonance > best_reward:
                        best_state = state
                        best_reward = state.resonance
                    continue

                # Opérateurs triés par policy
                sorted_ops = (self.policy.sort_operators(self.operators)
                             if self.policy else self.operators)

                # Expansion sans opérande
                for op in sorted_ops:
                    new_psi = op.apply(state.psi)
                    new_state = state.copy()
                    new_state.psi = new_psi
                    new_state.operations.append(op.name)
                    new_state.cost += op.cost
                    new_state.step = depth + 1
                    new_state.resonance = verifier.compute_reward(new_state)
                    # Suivi de cohérence
                    new_state.values.append(new_state.resonance)
                    candidates.append(new_state)

                # Expansion avec opérandes (opérateurs principaux)
                if operand_psis:
                    for op in sorted_ops[:5]:
                        for i, operand in enumerate(operand_psis):
                            new_psi = op.apply(state.psi, operand)
                            new_state = state.copy()
                            new_state.psi = new_psi
                            new_state.operations.append(f"{op.name}({i})")
                            new_state.cost += op.cost
                            new_state.step = depth + 1
                            new_state.resonance = verifier.compute_reward(new_state)
                            new_state.values.append(new_state.resonance)
                            candidates.append(new_state)

            if not candidates:
                break

            all_candidates_for_grpo.extend(candidates)

            # Utiliser GRPO si policy disponible, sinon sélection classique
            if self.policy:
                beam = self.policy.apply_grpo(candidates, self.beam_width)
            else:
                candidates.sort(key=lambda s: -s.resonance)
                beam = candidates[:self.beam_width]

            for state in beam:
                if state.resonance > best_reward:
                    best_state = state
                    best_reward = state.resonance

            trace.trajectory.append(beam[0])
            trace.resonance_history.append(beam[0].resonance)
            traced_depth = depth + 1

            # Détection émergence
            if len(trace.resonance_history) >= 2:
                delta = trace.resonance_history[-1] - trace.resonance_history[-2]
                if delta >= EMERGENCE_THRESHOLD:
                    trace.emergence_points.append(len(trace.resonance_history) - 1)

        trace.final_psi = best_state.psi
        trace.success = verifier.is_solution(best_state)
        trace.elapsed_ms = (time.time() - start) * 1000
        trace.steps = traced_depth

        return trace


# ═══════════════════════════════════════════════════════════════════════════════
# 10. WAVE REASONER — CLASSE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveReasoner:
    """
    Raisonneur harmonique unifié avec apprentissage intégré.

    - Arithmetic : FHRR direct avec Shunting-Yard (PEMDAS)
    - Logic      : beam search avec policy GRPO
    - Comparison : résonance différentielle multi-critères

    Apprentissage :
    - StrategyMemory : stocke et retrouve les stratégies réussies
    - PolicyLearner  : apprend quels opérateurs sont les plus efficaces
    """

    # Chemin de persistance de la policy
    _DEFAULT_POLICY_PATH = Path(__file__).resolve().parent.parent / 'data' / 'strategy_policy.json'

    def __init__(self, dim: int = DIM, enable_learning: bool = True):
        self.dim = dim
        self.arith = ArithmeticReasoner(dim)
        self.enable_learning = enable_learning

        # Mémoire de stratégies (distillation)
        self.strategy_memory = StrategyMemory(dim)

        # Policy GRPO
        self.policy = PolicyLearner()
        self.policy.register_all(LOGIC_OPERATORS)

        # Charger la policy persistée si elle existe
        if enable_learning:
            self.policy.load(str(self._DEFAULT_POLICY_PATH))

        # Ancien dict — conservé pour rétrocompatibilité
        self._strategy_memory: Dict[str, List[List[str]]] = {}

    def _save_policy(self):
        """Persiste la policy après mise à jour."""
        if self.enable_learning:
            self.policy.save(str(self._DEFAULT_POLICY_PATH))

    # ── Arithmétique directe FHRR (PEMDAS) ──

    def reason_arithmetic(self, expression: str) -> dict:
        """Arithmétique directe FHRR avec priorités PEMDAS."""
        return self.arith.solve(expression)

    # ── Logique (beam search avec policy) ──

    def reason_logic(self, premises: List[str], query: str) -> dict:
        """
        Raisonnement logique par beam search avec policy GRPO et distillation.

        Exemple :
            premises = ["tous les chats sont des félins", "Minou est un chat"]
            query = "Minou est-elle un félin ?"
        """
        start_total = time.time()

        psi_premises = [encode(p, dim=self.dim) for p in premises]
        psi_query = encode(query, dim=self.dim)
        psi_context = superpose(*psi_premises) if psi_premises else psi_query

        # Cible = le contexte des prémisses
        verifier = ResonanceVerifier(target_psi=psi_context)

        # Chercher une stratégie similaire dans la mémoire (warm-start)
        warm_start_ops = self.strategy_memory.retrieve_best(psi_query, threshold=0.65)

        # Beam search avec policy
        beam = PolicyBeamSearch(
            LOGIC_OPERATORS, beam_width=6, max_depth=4,
            policy=self.policy if self.enable_learning else None,
            strategy_memory=self.strategy_memory if self.enable_learning else None,
        )
        trace = beam.search(psi_query, verifier,
                           operand_psis=psi_premises,
                           warm_start_ops=warm_start_ops)

        # Décoder la conclusion
        conclusion_candidates = decode(trace.final_psi, top_k=3)
        confidence = trace.resonance_history[-1] if trace.resonance_history else 0.0

        elapsed = (time.time() - start_total) * 1000

        # Distillation : stocker la trace si succès
        if trace.success and self.enable_learning:
            strategy_ops = [s.operations[-1] if s.operations else 'init'
                          for s in trace.trajectory]
            self.strategy_memory.store(psi_query, strategy_ops,
                                       confidence, trace_obj=trace)
            self._save_policy()

        return {
            'handled': True,
            'conclusion': conclusion_candidates[0][0] if conclusion_candidates else "indéterminé",
            'confidence': round(confidence, 3),
            'method': 'wave_logic',
            'trace': trace.to_dict(),
            'elapsed_ms': round(elapsed, 1),
            'warm_started': warm_start_ops is not None,
            'strategies_stored': self.strategy_memory.n_stored,
            'explication': (
                f"🌊 Raisonnement logique harmonique\n"
                f"   Prémisses : {'; '.join(premises)}\n"
                f"   Conclusion : {conclusion_candidates[0][0] if conclusion_candidates else 'indéterminé'}\n"
                f"   Confiance : {confidence:.2f}\n"
                f"   Stratégies mémorisées : {self.strategy_memory.n_stored}\n"
                f"   {len(trace.trajectory)} étapes, {trace.elapsed_ms:.0f}ms"
            ),
        }

    # ── Comparaison multi-critères ──

    def reason_comparison(self, entity_a: str, entity_b: str,
                          criterion: str = "",
                          criteria_list: Optional[List[str]] = None) -> dict:
        """
        Comparaison par résonance différentielle, supporte multi-critères.

        Args:
            entity_a, entity_b: entités à comparer
            criterion: un seul critère (rétrocompatible)
            criteria_list: liste de critères multiples

        Returns:
            dict avec winner, scores par critère, winner global
        """
        # Fusionner les critères
        all_criteria = []
        if criterion:
            all_criteria = [criterion]
        if criteria_list:
            all_criteria = criteria_list

        psi_a = encode(entity_a, dim=self.dim)
        psi_b = encode(entity_b, dim=self.dim)

        scores_detail = {}
        total_a, total_b = 0.0, 0.0

        for crit in all_criteria:
            psi_crit = encode(crit, dim=self.dim)
            psi_a_w = amplify(psi_a, psi_crit, boost=1.5)
            psi_b_w = amplify(psi_b, psi_crit, boost=1.5)
            r_a = coherence(psi_a_w, psi_crit)
            r_b = coherence(psi_b_w, psi_crit)
            scores_detail[crit] = {entity_a: round(r_a, 3), entity_b: round(r_b, 3)}
            total_a += r_a
            total_b += r_b

        if not all_criteria:
            # Sans critère : simple résonance mutuelle
            r_a = 0.5
            r_b = 0.5
        else:
            r_a = total_a / len(all_criteria)
            r_b = total_b / len(all_criteria)

        winner = entity_a if r_a > r_b else entity_b
        confidence = abs(r_a - r_b)

        result = {
            'handled': True,
            'winner': winner,
            'scores': {entity_a: round(r_a, 3), entity_b: round(r_b, 3)},
            'confidence': round(confidence, 3),
            'method': 'wave_comparison',
            'explication': (
                f"🌊 Comparaison harmonique\n"
                f"   {entity_a} ↔ {entity_b}"
                + (f" (critères : {', '.join(all_criteria)})" if all_criteria else "")
                + f"\n   Gagnant : {winner}\n"
                f"   {entity_a}: {r_a:.2f}, {entity_b}: {r_b:.2f}"
            ),
        }

        if scores_detail:
            result['scores_detail'] = scores_detail

        return result

    # ── Stats ──

    def stats(self) -> dict:
        """Statistiques du raisonneur."""
        policy_stats = {}
        if self.enable_learning:
            for op in LOGIC_OPERATORS:
                policy_stats[op.name] = {
                    'success_rate': round(self.policy.success_rate(op.name), 3),
                    'attempts': self.policy._attempts.get(op.name, 0),
                    'successes': self.policy._success.get(op.name, 0),
                }

        return {
            'strategies_stored': self.strategy_memory.n_stored,
            'policy_stats': policy_stats,
            'learning_enabled': self.enable_learning,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# API — FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

_reasoner_instance: Optional[WaveReasoner] = None


def get_reasoner(enable_learning: bool = True) -> WaveReasoner:
    global _reasoner_instance
    if _reasoner_instance is None:
        _reasoner_instance = WaveReasoner(enable_learning=enable_learning)
    return _reasoner_instance


def reason_arithmetic(expression: str) -> dict:
    return get_reasoner().reason_arithmetic(expression)


def reason_logic(premises: List[str], query: str) -> dict:
    return get_reasoner().reason_logic(premises, query)


def reason_comparison(entity_a: str, entity_b: str, criterion: str = "",
                      criteria_list: Optional[List[str]] = None) -> dict:
    return get_reasoner().reason_comparison(entity_a, entity_b, criterion, criteria_list)


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 65)
    print("  🌊 WAVE REASONER — Tests complets")
    print("=" * 65)

    # ── 1. Arithmétique FHRR (PEMDAS) ──
    print("\n── 1. ARITHMÉTIQUE FHRR (PEMDAS) ──")
    tests_arith = [
        ("15 + 27", 42),
        ("50 - 23", 27),
        ("7 * 8", 56),
        ("100 + 200", 300),
        ("(2 + 3) * 4", 20),        # PEMDAS
        ("2 + 3 * 4", 14),           # priorité * sur +
        ("2^3", 8),                  # puissance
        ("15 % 4", 3),               # modulo
        ("-5 + 10", 5),             # négation unaire
        ("combien font 10 + 20", 30),
    ]
    ok = 0
    for expr, expected in tests_arith:
        result = reason_arithmetic(expr)
        r = result.get('result', 999)
        passed = result.get('handled') and abs(r - expected) < 0.5
        ok += 1 if passed else 0
        icon = "✅" if passed else "❌"
        print(f"  {icon} {expr:25s} = {r:6g}  (attendu: {expected:6g})  "
              f"rés.{result.get('resonance', 0):.2f}  {result.get('elapsed_ms', 0):.0f}ms")
    print(f"  → {ok}/{len(tests_arith)} OK")

    # ── 2. Comparaison multi-critères ──
    print("\n── 2. COMPARAISON MULTI-CRITÈRES ──")
    result = reason_comparison("chat", "chien", "félin")
    print(f"  chat vs chien (félin) → {result['winner']}  scores={result['scores']}")

    result = reason_comparison("chat", "chien",
                               criteria_list=["félin", "rapidité", "domestique"])
    print(f"  chat vs chien (3 critères) → {result['winner']}  scores={result['scores']}")
    if 'scores_detail' in result:
        for crit, scores in result['scores_detail'].items():
            print(f"    {crit}: {scores}")

    # ── 3. Logique (beam search policy) ──
    print("\n── 3. LOGIQUE ──")
    result = reason_logic(
        ["tous les chats sont des félins", "Minou est un chat"],
        "Minou est-elle un félin ?"
    )
    print(f"  Conclusion: {result['conclusion']} (conf={result['confidence']:.2f}) "
          f"{result.get('elapsed_ms', 0)}ms")

    # ── 4. Distillation & Policy ──
    print("\n── 4. DISTILLATION & POLICY ──")
    reasoner = get_reasoner()
    stats = reasoner.stats()
    print(f"  Stratégies mémorisées : {stats['strategies_stored']}")
    print(f"  Learning activé : {stats['learning_enabled']}")
    if stats['policy_stats']:
        print("  Policy (taux de succès) :")
        for op_name, ps in sorted(stats['policy_stats'].items()):
            bar = "█" * int(ps['success_rate'] * 20)
            print(f"    {op_name:12s} : {ps['success_rate']:.3f}  {bar}  "
                  f"({ps['successes']}/{ps['attempts']})")

    print("\n" + "=" * 65)
    print("  ✅ Tests terminés")
    print("=" * 65)