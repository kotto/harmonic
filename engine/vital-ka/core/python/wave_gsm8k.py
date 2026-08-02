"""
🌊 Wave GSM8K — Chaînes de calcul & mémoire par résonance
===========================================================

Découverte (analyse des 1319 réponses officielles GSM8K) :

  Les réponses GSM8K sont des DÉRIVATIONS : 4282 lignes annotées
  « X op Y = <<X op Y = Z>>Z ». Les 4282 annotations ne contiennent
  QUE de l'arithmétique pure (+ - * / parenthèses, chiffres) — aucun
  autre symbole.

  → GSM8K est un LANGAGE DE CHAÎNES DE CALCUL.

    Parse → Wave IR (Program + MathOp) → exécution harmonique
    (WaveCompiler) → valeur finale, vérifiée contre ####.

  La mémoire de patterns indexe chaque problème par ψ(question) et
  ψ(squelette de chaîne). La récupération est une RÉSONANCE ; la
  généralisation est une INSTANCIATION DU SQUELETTE :

    - opérande liée à l'énoncé  (Q) → rebindée sur la nouvelle question
    - résultat intermédiaire   (S) → reste structurel (étape j)
    - constante structurelle   (C) → reste telle quelle (2, 100, 0.5…)

  C'est la lecture ondulatoire du raisonnement arithmétique :
  chaque problème = un programme harmonique ; chaque réponse = le
  résultat de ce programme ; chaque nouvelle question = la résonance
  d'un squelette connu + instanciation.

Modes (benchmark_gsm8k_chain.py) :
  M0  annotations      — 4282 vérifications auto (parseur prouvé)
  M1  couverture       — la chaîne seule reproduit-elle #### ?
  M2  mémoire fermée   — récupération par résonance puis exécution
  M3  généralisation   — leave-one-out : squelette d'autrui, lié
                         aux nombres de la question, exécuté

Usage :
    from wave_gsm8k import GSM8KChainMemory
    mem = GSM8KChainMemory()                # charge les 1319 problèmes
    val, idx, score, skel = mem.solve_transfer(42)   # généralisation
"""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from wave_lang import encode, coherence
from wave_ir import Program, Assign, Return, MathOp, Literal, Var
from wave_compiler import WaveCompiler
from wave_word_problems import _normalize_numbers


# ═══════════════════════════════════════════════════════════════════════════════
# EXTENSIONS DU LANGAGE : PROSE FINALE & ÉQUATIONS LINÉAIRES
# ═══════════════════════════════════════════════════════════════════════════════

# La prose finale (après le dernier <<…>>) porte les étapes manquantes :
#   « 99 + 5 = $104 », « 54 − 37 = 17 », « 60g * 4/5 = 48 »,
#   « 12/20 x 100% = 60% », « 25 total cars – 20 cars … = 5 »,
#   « .75X = $19.50 → X = 26 », « 7x=700 → x=100 », « 3 1/2 »…

_MIXED_FRAC = re.compile(r'(\d+(?:\.\d+)?)[ \t]+(\d+)\s*/\s*(\d+)')  # 3 1/2 → (3+1/2)
_NUM_UNIT = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*'
    r'(?:[a-wy-zA-WY-Z]{2,12}(?:/[a-wy-zA-WY-Z]{1,12})?\b'
    r'|[a-wy-zA-WY-Z]\b(?![\s=]*(?:=|$)))'
    # « 7 puppies », « 240g/5 », « 10 feet * 100% » → strippés ;
    # « 2V = », « 11h = », « 4x » → variables
)
_VAR_EQ = re.compile(r'(?:\b([a-zA-Z])\b|\d\s*([a-zA-Z])\b)\s*(?==|$)')
_SPACE_THOUS = re.compile(r'(\d)\s+(\d{3})\b')                     # 400 000 → 400000
_COMMA_THOUS = re.compile(r'(\d),(\d{3})(?:\.\d+)?')               # 88,000 → 88000
_X_MULT = re.compile(r'(?<=\d)\s*[xX]\s*(?=[\d(])')                # 12/20 x 100% → *
_IMPL_MULT = re.compile(r'(\d+(?:\.\d+)?)\s*\(')                    # 2(60) → 2*(60)
_IMPL_MULT2 = re.compile(r'\)\s*(\d+(?:\.\d+)?)')                   # (1/4)24 → (1/4)*24
_FRAC_WRAP = re.compile(r'(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)')         # 1/2 → (1/2)
_PCT_OP = re.compile(r'(\d+(?:\.\d+)?)\s*%')                        # opérande % → /100

_TIER1 = re.compile(
    r'([-.\d(][0-9.,+\-*/()\s]*?)\s*=\s*([-.\d(][0-9.,+\-*/()\s]*?)'
    r'(?=\s|[.,;!?]|$)')                                           # « 99 + 5 = 104 », « -6 + 3 = -3 »
_TIER2 = re.compile(
    r'(\d+(?:\.\d+)?)[^=\n(]{1,60}?([+\-])\s*[^=\n(]{0,60}?'
    r'(\d+(?:\.\d+)?)[^=\n(]{0,60}?=\s*(\d+(?:\.\d+)?)')            # « 25 … – 20 … = 5 » (sans parens)
_TIER3 = re.compile(
    r'(\d+(?:\.\d+)?)\s+(plus|minus|times|divided by|multiplied by)\s+'
    r'(\d+(?:\.\d+)?)\s+equals\s+(\d+(?:\.\d+)?)', re.IGNORECASE)  # « 200 minus 174 equals 26 »
_ROUNDS = re.compile(
    r'round\s+(\d+(?:\.\d+)?)\s+up(?:\s+to the next highest whole number)?\s*,?\s*(\d+(?:\.\d+)?)?'
    r'|round\s+(\d+(?:\.\d+)?)\s+down(?:\s+to the nearest whole number)?\s*,?\s*(\d+(?:\.\d+)?)?'
    r'|rounds?\s+(down|up)\s+to\s+(\d+(?:\.\d+)?)',
    re.IGNORECASE)
_WORD_OP = {'plus': 'ADD', 'minus': 'SUB', 'times': 'MUL',
            'divided by': 'DIV', 'multiplied by': 'MUL'}


def _normalize_prose(s: str) -> str:
    """Normalise la prose arithmétique en expression standard.

    $, −(U+2212), –(U+2013), ×, ·, [ ] → ASCII ; fractions mixtes,
    unités, milliers, x-multiplication, multiplications implicites,
    %-opérandes.
    """
    s = s.replace('$', '').replace('−', '-').replace('–', '-')
    s = s.replace('—', '-').replace('×', '*').replace('·', '*')
    s = s.replace('[', '(').replace(']', ')')
    s = _MIXED_FRAC.sub(lambda m: f'({m.group(1)}+{m.group(2)}/{m.group(3)})', s)
    s = _NUM_UNIT.sub(r'\1', s)
    s = _SPACE_THOUS.sub(r'\1\2', s)
    s = _COMMA_THOUS.sub(r'\1\2', s)
    s = _X_MULT.sub('*', s)
    s = _IMPL_MULT.sub(r'\1*(', s)
    s = _IMPL_MULT2.sub(r')*\1', s)
    s = _FRAC_WRAP.sub(r'(\1/\2)', s)      # 1/2 → (1/2) : unité indivisible
    s = _PCT_OP.sub(r'(\1/100)', s)
    return s


def _eval_expr_text(s: str) -> Optional[float]:
    """Évalue une expression de prose normalisée → valeur ou None."""
    try:
        _steps, val = _ArithParser(s).parse()
        return val
    except (ChainParseError, ValueError):
        return None


class _LinearParser:
    """Parse une expression linéaire en une variable → (coef, const).

    x, 4x, (a/b)·x, x + 2x, (x+3)*3 - 1… — lève ChainParseError si
    l'expression n'est pas linéaire (quadratique, division par x…).
    """

    def __init__(self, s: str):
        self.toks = re.findall(r'(?:\.\d+|\d+\.?\d*)|[a-zA-Z()+\-*/]',
                               _normalize_prose(s))
        self.i = 0

    def _peek(self) -> Optional[str]:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def _next(self) -> Optional[str]:
        t = self._peek()
        self.i += 1
        return t

    def parse(self) -> Tuple:
        v = self._expr()
        if self.i != len(self.toks):
            raise ChainParseError("symbole inattendu")
        return v

    def _expr(self) -> Tuple:
        a = self._term()
        while self._peek() in ('+', '-'):
            op = self._next()
            b = self._term()
            if op == '+':
                a = (a[0] + b[0], a[1] + b[1])
            else:
                a = (a[0] - b[0], a[1] - b[1])
        return a

    def _term(self) -> Tuple:
        a = self._factor()
        while self._peek() in ('*', '/'):
            op = self._next()
            b = self._factor()
            if op == '*':
                if a[0] and b[0]:
                    raise ChainParseError("produit de deux inconnues")
                if a[0]:
                    a = (a[0] * b[1], a[1] * b[1])     # x·c
                else:
                    a = (b[0] * a[1], b[1] * a[1])     # c·x
            else:
                if b[0]:
                    raise ChainParseError("division par l'inconnue")
                a = (a[0] / b[1], a[1] / b[1])
        return a

    def _factor(self) -> Tuple:
        t = self._next()
        if t is None:
            raise ChainParseError("expression tronquée")
        if t == '(':
            v = self._expr()
            if self._next() != ')':
                raise ChainParseError("parenthèse non fermée")
            if self._peek() is not None and self._peek().isalpha():
                self._next()                       # (a/b)x → coefficient
                if v[0]:
                    raise ChainParseError("produit de deux inconnues")
                return (v[1], 0.0)
            return v
        if t in ('+', '-'):
            v = self._factor()
            return v if t == '+' else (-v[0], -v[1])
        if t.isalpha():
            return (1.0, 0.0)                      # l'inconnue
        v = float(t)
        if self._peek() is not None and self._peek().isalpha():
            self._next()                           # 3r, 11h, .75X → coef·x
            return (v, 0.0)
        return (0.0, v)


def _solve_equation(lhs: str, rhs: str) -> Optional[float]:
    """Résout a·x + b = c·x + d → x = (d − b) / (a − c)."""
    # « 12 x » ou « (2/3), x » (espace/virgule) n'est PAS un coefficient
    if re.search(r'\d[\s,]+[a-zA-Z]\b', lhs) or re.search(r'\d[\s,]+[a-zA-Z]\b', rhs):
        return None
    try:
        lc, lb = _LinearParser(lhs).parse()
        rc, rb = _LinearParser(rhs).parse()
    except (ChainParseError, ValueError):
        return None
    if abs(lc - rc) < 1e-12:
        return None                                    # pas d'inconnue
    return (rb - lb) / (lc - rc)


def _clean_words(s: str) -> str:
    """Retire les mots (lettres isolées de longueur ≥ 2) — garde les coefs."""
    return re.sub(r'[a-zA-Z]{2,}', ' ', s)


def _rhs_candidates(rhs: str) -> List[str]:
    """Candidats côté droit (du plus informatif au plus simple).

    Première expression → premier nombre → texte nettoyé complet.
    """
    c = _clean_words(rhs)
    nc = _normalize_prose(c)
    cands = []
    m2 = re.search(r'[\d(][0-9.,+\-*/()\s]*', nc)
    if m2:
        cands.append(m2.group(0).strip())
    m = re.match(r'\s*(\d+(?:\.\d+)?)', nc)
    if m and m.group(1) not in cands:
        cands.append(m.group(1))
    if c.strip() not in cands:
        cands.append(c)
    return cands


def _lhs_candidates(lhs: str) -> List[str]:
    """Candidats côté gauche (du plus large au plus ciblé).

    Texte nettoyé complet (si non ambigu) → coefficient parenthésé
    (« (7/2)x ») → coefficient (« 8r », « .75X ») → variable seule.
    """
    c = _clean_words(lhs)
    # lettres de prose devant un nombre (« X be … 24-5-10-2+x »)
    c = re.sub(r'(?<!\d)[a-zA-Z](?=\s*[0-9(])', ' ', c)
    cands = []
    if not re.search(r'\d\s+\(', c):               # « 105 (7/2) » ambigu
        cands.append(c)
    m = re.findall(r'\([^)]*\)\s*[a-zA-Z]', c)     # « (7/2)x »
    if m:
        idx = c.rfind(m[-1])
        cands.append(c[idx:])
    m2 = re.findall(r'[\d.][0-9.]*\s*[a-zA-Z]', c) # « 8r », « .75X »…
    if m2:
        idx = c.rfind(m2[-1])
        cands.append(c[idx:])
    m3 = re.findall(r'[a-zA-Z]', c)                # variable seule
    if m3:
        idx = c.rfind(m3[-1])
        cands.append(c[idx:])
    return cands


def _prose_steps(post: str) -> List[Tuple[float, str]]:
    """Étapes manquantes de la prose finale.

    Ordre des événements (le dernier fixe la valeur finale) — par
    position dans le texte : équations linéaires → arithmétique en
    mots (tier-3) → expressions compactes (tier-1) → pas gappés
    (tier-2) → arrondi.
    """
    events: List[Tuple[float, str]] = []

    # 1) équations linéaires — LIGNE PAR LIGNE (les segments ne doivent
    #    pas absorber le début de l'équation suivante : « x+x+(1/2)x \n250 »)
    for _line in post.split('\n'):
        segs = _line.split('=')
        for i in range(len(segs) - 1):
            lhs, rhs = segs[i][-90:], segs[i + 1][:90]
            lc, rc = _clean_words(lhs), _clean_words(rhs)
            mv = (_VAR_EQ.search(lc) or _VAR_EQ.search(rc))
            if mv is None:
                continue
            var = mv.group(1) if mv.group(1) is not None else mv.group(2)
            val = None

            # assignation : l'inconnue est seule à gauche (« x = expr »)
            try:
                lcoef, lconst = _LinearParser(lc).parse()
                if abs(lcoef - 1.0) < 1e-12 and abs(lconst) < 1e-12:
                    val = _eval_expr_text(_normalize_prose(rhs))
            except ChainParseError:
                pass

            # équation linéaire : candidates nettoyés, puis queues
            if val is None:
                for l in _lhs_candidates(lhs):
                    if val is not None:
                        break
                    for r in _rhs_candidates(rhs):
                        val = _solve_equation(l, r)
                        if val is not None:
                            break

            if val is None:
                continue
            events.append((val,
                           f"équation : {lhs.strip()} = {rhs.strip()} "
                           f"→ {var} = {_fmt(val)}"))

    # 2) arithmétique en mots : « 200 minus 174 equals 26 »
    for m in _TIER3.finditer(post):
        a, word, b, r = m.groups()
        val = _OP_FN[_WORD_OP[word.lower()]](float(a), float(b))
        if abs(val - float(r)) < 1e-6:
            events.append((val, f"prose : {a} {word} {b} = {r} → {_fmt(val)}"))

    # 3) expressions compactes « lhs = rhs » sur le texte normalisé
    #    (boucle avec reprise : les chaînes « a = b = c » forcent la
    #    recherche d'un autre ancrage quand la vérification échoue)
    norm = _normalize_prose(post)
    spans: List[Tuple[int, int]] = []
    pos = 0
    while True:
        m = _TIER1.search(norm, pos)
        if m is None:
            break
        if any(s < m.end() and m.start() < e for s, e in spans[:-1]):
            pos = m.end()
            continue
        lhs, rhs = m.group(1).strip(), m.group(2).strip()
        if not lhs or not rhs:
            pos = m.end()
            continue
        a = _eval_expr_text(lhs)
        if a is None and re.search(r'[+\-*/]\s*$', lhs):   # « 30*=90 »
            a = _eval_expr_text(rhs)
            if a is None:
                pos = m.start() + 1
                continue
            events.append((a, f"prose : {lhs} = {rhs} → {_fmt(a)}"))
            spans.append(m.span())
            pos = m.end()
            continue
        if a is None:
            pos = m.start() + 1
            continue
        rhs_pct = rhs.rstrip().endswith('%') or '/100)' in rhs[-8:]
        b = _eval_expr_text(rhs)
        if b is None:
            pos = m.start() + 1
            continue
        if rhs_pct:
            # lhs ≈ rhs (fractions : « 3/6 = 50% ») → ×100 ;
            # lhs ≈ rhs×100 (déjà le nombre : « 94 = 94% ») → tel quel
            if abs(a - b) < 1e-6:
                value = a * 100.0
            elif abs(a - b * 100.0) < 1e-6:
                value = a
            else:
                pos = m.start() + 1
                continue
        else:
            if abs(a - b) > 1e-6:
                pos = m.start() + 1
                continue
            value = a
        events.append((value, f"prose : {lhs} = {rhs} → {_fmt(value)}"))
        spans.append(m.span())
        # chaîne « a = b = c » : si le rhs est suivi d'un opérateur, le
        # calcul continue (« 2/4 = .5 * 100% = 50% ») → autre ancrage
        after = norm[m.end():].lstrip()[:1]
        pos = m.start() + 1 if after in ('*', '/') else m.end()

    # 4) pas gappés « a … op … b = r » (mots intercalés)
    pos = 0
    while True:
        m = _TIER2.search(norm, pos)
        if m is None:
            break
        if any(s < m.end() and m.start() < e for s, e in spans[:-1]):
            pos = m.end()
            continue
        a, op, b, r = m.groups()
        val = _OP_FN['ADD' if op == '+' else 'SUB'](float(a), float(b))
        if abs(val - float(r)) < 1e-6:
            events.append((val, f"prose : {a} {op} {b} = {r} → {_fmt(val)}"))
            spans.append(m.span())
            pos = m.end()
        else:
            pos = m.start() + 1                    # autre liaison de b
            continue

    # 5) arrondi explicite (« rounds down to 33 », « round 6.75 up … 7 »)
    m = _ROUNDS.search(post)
    if m:
        if m.group(1) is not None:       # round N up → arrondi supérieur
            val = math.ceil(float(m.group(1)))
            events.append((float(val), f"arrondi : round {m.group(1)} up → {val}"))
        elif m.group(3) is not None:     # round N down → arrondi inférieur
            val = math.floor(float(m.group(3)))
            events.append((float(val), f"arrondi : round {m.group(3)} down → {val}"))
        elif m.group(6) is not None:     # rounds (down|up) to N
            events.append((float(m.group(6)),
                           f"arrondi : rounds {m.group(5)} to {m.group(6)}"))

    return events


# ═══════════════════════════════════════════════════════════════════════════════
# PARSEUR DE CHAÎNES DE CALCUL
# ═══════════════════════════════════════════════════════════════════════════════

class ChainParseError(Exception):
    """Expression de chaîne illisible."""


# Opérande : ('V', valeur) → à lier ; après liage : ('Q', idx, repli) |
#            ('S', idx) | ('C', valeur) | ('R', idx)
@dataclass
class Step:
    """Une étape de calcul en forme 3-adresses (Wave IR : MathOp)."""
    op: str                            # ADD | SUB | MUL | DIV | CONST
    a: Optional[Tuple] = None
    b: Optional[Tuple] = None

    @property
    def symbol(self) -> str:
        return {'ADD': '+', 'SUB': '-', 'MUL': '×', 'DIV': '÷',
                'CONST': '='}.get(self.op, self.op)


@dataclass
class Chain:
    """Dérivation complète d'un problème : étapes + valeur finale."""
    steps: List[Step] = field(default_factory=list)
    exprs: List[str] = field(default_factory=list)   # texte lisible/étape
    final: Optional[float] = None       # valeur annoncée (dernier =Z)
    expected: Optional[float] = None    # #### N
    n_annot: int = 0
    verified_count: int = 0             # =Z reproduits par le parseur
    parse_fail_count: int = 0           # annotations illisibles
    all_verified: bool = True           # chaque =Z vérifié par le parseur

    @property
    def derivable(self) -> bool:
        return (self.final is not None and self.expected is not None
                and abs(self.final - self.expected) < 1e-6)

    @property
    def skeleton(self) -> str:
        return ' '.join(s.op for s in self.steps)


class _ArithParser:
    """Descente récursive : + - * / ( ) — associativité gauche."""

    _TOK = re.compile(r'(?:\d+\.?\d*|\.\d+)|[()+\-*/]')

    def __init__(self, s: str):
        self.toks = self._TOK.findall(s)
        self.i = 0

    def _peek(self) -> Optional[str]:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def _next(self) -> Optional[str]:
        t = self._peek()
        self.i += 1
        return t

    @staticmethod
    def _emit(op: str, a: Tuple, b: Tuple,
              steps: List[Step]) -> Tuple:
        """Émet une étape binaire ; retourne une référence de résultat."""
        steps.append(Step(op, a, b))
        return ('R', len(steps) - 1)

    def parse(self) -> Tuple[List[Step], float]:
        """Retourne (étapes, valeur) ; lève ChainParseError si illisible."""
        steps: List[Step] = []
        top = self._expr(steps)
        if self.i != len(self.toks):
            raise ChainParseError(f"symbole inattendu {self._peek()!r}")
        if top[0] == 'V':
            return steps, top[1]
        value = eval_steps(steps)
        if value is None:
            raise ChainParseError("évaluation impossible")
        return steps, value

    def _expr(self, steps: List[Step]) -> Tuple:
        v = self._term(steps)
        while self._peek() in ('+', '-'):
            op = self._next()
            rhs = self._term(steps)
            v = self._emit({'+': 'ADD', '-': 'SUB'}[op], v, rhs, steps)
        return v

    def _term(self, steps: List[Step]) -> Tuple:
        v = self._factor(steps)
        while self._peek() in ('*', '/'):
            op = self._next()
            rhs = self._factor(steps)
            v = self._emit({'*': 'MUL', '/': 'DIV'}[op], v, rhs, steps)
        return v

    def _factor(self, steps: List[Step]) -> Tuple:
        t = self._next()
        if t is None:
            raise ChainParseError("expression tronquée")
        if t == '(':
            v = self._expr(steps)
            if self._next() != ')':
                raise ChainParseError("parenthèse non fermée")
            return v
        if t in ('+', '-'):
            val = self._factor(steps)
            if val[0] != 'V':
                raise ChainParseError("signe d'une sous-expression")
            return ('V', val[1] if t == '+' else -val[1])
        return ('V', float(t))


_OP_FN = {'ADD': lambda a, b: a + b, 'SUB': lambda a, b: a - b,
          'MUL': lambda a, b: a * b, 'DIV': lambda a, b: a / b}


def _operand_value(o: Tuple, vals: List[float],
                   qnums: Optional[List[Tuple[float, bool]]]) -> float:
    """Résout un opérande : constante, lien énoncé ou résultat d'étape."""
    kind = o[0]
    if kind in ('C', 'V'):
        return o[1]
    if kind == 'Q':                      # lié à l'énoncé (repli si absent)
        idx, fallback = o[1], o[2]
        if qnums is not None and idx < len(qnums):
            return qnums[idx][0]
        return fallback
    return vals[o[1]]                    # 'S' / 'R' → étape précédente


def eval_steps(steps: List[Step],
               qnums: Optional[List[Tuple[float, bool]]] = None) -> Optional[float]:
    """Évaluation python pure (diagnostic / affichage pas à pas)."""
    vals: List[float] = []
    try:
        for st in steps:
            if st.op == 'CONST':
                vals.append(_operand_value(st.a, vals, qnums))
            else:
                a = _operand_value(st.a, vals, qnums)
                b = _operand_value(st.b, vals, qnums)
                vals.append(_OP_FN[st.op](a, b))
    except (ZeroDivisionError, IndexError, ValueError):
        return None
    return vals[-1] if vals else None


def _extract_final(answer: str) -> Optional[float]:
    """Extrait #### N (gère les milliers : 57,500 → 57500)."""
    m = re.search(r'####\s*(-?\d[\d,]*\.?\d*)', answer)
    if not m:
        return None
    s = m.group(1)
    if ',' in s and re.fullmatch(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', s):
        s = s.replace(',', '')
    else:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def parse_answer_chain(answer: str) -> Chain:
    """Parse une réponse GSM8K → chaîne de calcul exécutable.

    Chaque annotation « <<X op Y = Z>> » devient une ou plusieurs
    étapes 3-adresses ; « =Z » sert de PREUVE de parsing (all_verified).
    La prose finale (après le dernier <<…>>) est analysée par le
    langage étendu (prose arithmétique, équations linéaires, %, arrondi).
    """
    chain = Chain(expected=_extract_final(answer))
    last_ann = -1
    for m in re.finditer(r'<<(.+?)>>', answer):
        last_ann = m.end()
        ann = m.group(1)
        if '=' not in ann:
            continue                       # annotation sans résultat
        lhs, rhs = ann.split('=', 1)
        try:
            rhs_val = float(rhs.replace(',', ''))
        except ValueError:
            continue
        chain.n_annot += 1
        chain.final = rhs_val              # la dernière annotation = valeur finale
        if not re.search(r'[+\-*/]', lhs):
            chain.steps.append(Step('CONST', ('V', rhs_val)))
            chain.exprs.append(f"{_fmt(rhs_val)} (constante)")
            chain.verified_count += 1
            continue
        try:
            steps, val = _ArithParser(lhs.replace(',', '')).parse()
        except ChainParseError:
            chain.all_verified = False
            chain.parse_fail_count += 1
            continue
        ok = abs(val - rhs_val) < 1e-6
        chain.all_verified = chain.all_verified and ok
        chain.verified_count += int(ok)
        base = len(chain.steps)

        def _rebase(o: Optional[Tuple]) -> Optional[Tuple]:
            """Références locales ('R', j) → indices globaux (base + j)."""
            if o is not None and o[0] == 'R':
                return ('R', o[1] + base)
            return o

        for st in steps:
            st.a = _rebase(st.a)
            st.b = _rebase(st.b)
        chain.steps.extend(steps)
        chain.exprs.extend(_step_text(base + i, st, base)
                           for i, st in enumerate(steps))

    # Prose finale : les étapes manquantes vivent après le dernier <<…>>
    post = answer[last_ann:] if last_ann >= 0 else answer
    post = re.sub(r'####\s*.*$', '', post)
    if post.strip():
        for chunk in post.split('→'):        # « … = 12 → x = 18 »
            for value, text in _prose_steps(chunk):
                chain.steps.append(Step('CONST', ('V', value)))
                chain.exprs.append(text)
                chain.final = value
    return chain


def _step_text(i: int, st: Step, base: int = 0) -> str:
    """Texte lisible d'une étape (r2 = r0 ÷ 4) — indices globaux."""
    def op_str(o: Optional[Tuple]) -> str:
        if o is None:
            return '?'
        if o[0] in ('C', 'V'):
            return _fmt(o[1])
        if o[0] == 'Q':
            return _fmt(o[2]) + ' ←énoncé'
        return f"r{o[1]}"
    a = op_str(st.a)
    if st.op == 'CONST':
        return f"r{i} = {a}"
    return f"r{i} = {a} {st.symbol} {op_str(st.b)}"


def tag_chain(chain: Chain, question: str) -> Chain:
    """Lie les opérandes aux nombres de l'énoncé (en place).

    Ordre de résolution pour chaque opérande :
      1. résultat d'une étape précédente (S) — structure du calcul
      2. nombre de l'énoncé non encore utilisé (Q) — instanciation
      3. constante structurelle (C) — 2, 100, 0.5, 24 heures…
    """
    qvals = question_numbers(question)
    vals: List[float] = []
    used: set = set()
    for st in chain.steps:
        for slot in ('a', 'b'):
            o = getattr(st, slot)
            if o is None or o[0] != 'V':
                continue
            v = o[1]
            s_idx = next((j for j, rv in enumerate(vals)
                          if abs(rv - v) < 1e-9), None)
            if s_idx is not None:
                setattr(st, slot, ('S', s_idx))
                continue
            q_idx = next((j for j, (qv, _p) in enumerate(qvals)
                          if j not in used and abs(qv - v) < 1e-9), None)
            if q_idx is not None:
                used.add(q_idx)
                setattr(st, slot, ('Q', q_idx, v))
                continue
            setattr(st, slot, ('C', v))
        v_step = eval_steps(chain.steps[:len(vals) + 1], qvals)
        vals.append(v_step if v_step is not None else float('nan'))
    return chain


def question_numbers(q: str) -> List[Tuple[float, bool]]:
    """Nombres de l'énoncé, ordre d'apparition, avec drapeau %.

    « 80,000 » → 80000 ; « three » → 3 ; « 40% » → (40.0, True).
    """
    qn = _normalize_numbers(q.lower())
    qn = re.sub(r'(\d),(\d{3})(?:\.\d+)?', r'\1\2', qn)   # milliers
    out: List[Tuple[float, bool]] = []
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*%?', qn):
        out.append((float(m.group(1)), m.group(0).rstrip().endswith('%')))
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# EXÉCUTION HARMONIQUE (Wave IR → WaveCompiler)
# ═══════════════════════════════════════════════════════════════════════════════

def build_program(steps: List[Step],
                  qnums: Optional[List[Tuple[float, bool]]] = None) -> Optional[Program]:
    """Chaîne de calcul → programme harmonique (Program/MathOp)."""
    if not steps:
        return None

    def to_expr(o: Optional[Tuple]):
        if o is None:
            return Literal(0.0)
        kind = o[0]
        if kind == 'Q':
            idx, fallback = o[1], o[2]
            v = qnums[idx][0] if qnums is not None and idx < len(qnums) else fallback
            return Literal(v)
        if kind in ('C', 'V'):
            return Literal(o[1])
        return Var(f'r{o[1]}')           # 'S' / 'R'

    stmts = []
    for i, st in enumerate(steps):
        if st.op == 'CONST':
            stmts.append(Assign(f'r{i}', to_expr(st.a)))
        else:
            stmts.append(Assign(f'r{i}', MathOp(st.op, to_expr(st.a),
                                                to_expr(st.b))))
    stmts.append(Return(Var(f'r{len(steps) - 1}')))
    return Program(stmts)


def execute_chain(chain: Chain,
                  qnums: Optional[List[Tuple[float, bool]]] = None,
                  compiler: Optional[WaveCompiler] = None) -> Optional[float]:
    """Exécute la chaîne via l'interpréteur harmonique (WaveCompiler)."""
    if not chain or not chain.steps:
        return None
    if compiler is None:
        compiler = WaveCompiler(dim=64)
    prog = build_program(chain.steps, qnums)
    if prog is None:
        return None
    try:
        env = compiler.execute(prog)
        v = env.get('__return__')
        if v is None:
            return None
        return float(np.asarray(v).item())
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# MÉMOIRE DE PATTERNS PAR RÉSONANCE
# ═══════════════════════════════════════════════════════════════════════════════

class GSM8KChainMemory:
    """
    Mémoire des 1319 problèmes : chaîne de calcul + ψ(question) +
    ψ(squelette). Récupération = résonance vectorisée (top-k).

    solve_transfer(idx) → généralisation : squelette d'un AUTRE
    problème, instancié avec les nombres de la question cible.
    """

    def __init__(self, data_path: str = None, dim: int = 512):
        self.dim = dim
        self.compiler = WaveCompiler(dim=64)
        self.patterns: List[Dict] = []
        self._psi_q: List[np.ndarray] = []
        self._psi_s: List[np.ndarray] = []
        self._psi_c: List[np.ndarray] = []
        self._M_q: Optional[np.ndarray] = None
        self._M_s: Optional[np.ndarray] = None
        self._M_c: Optional[np.ndarray] = None

        if data_path is None:
            _d = os.path.dirname
            root = _d(_d(_d(_d(os.path.abspath(__file__)))))
            data_path = os.path.join(root, 'data', 'benchmarks',
                                     'gsm8k_test.jsonl')
        self.data_path = data_path

    # ── construction ─────────────────────────────────────────────────────────

    def load(self, path: str = None) -> int:
        """Charge les problèmes, parse les chaînes, lie, encode ψ."""
        path = path or self.data_path
        if not os.path.exists(path):
            return 0
        with open(path, encoding='utf-8') as f:
            problems = [json.loads(l) for l in f]

        for p in problems:
            chain = parse_answer_chain(p['answer'])
            tag_chain(chain, p['question'])
            self.patterns.append({
                'question': p['question'],
                'answer': p['answer'],
                'chain': chain,
                'qnums': question_numbers(p['question']),
            })
            self._psi_q.append(encode(self._signature(p['question']),
                                      dim=self.dim))
            self._psi_s.append(encode(chain.skeleton or '?',
                                      dim=self.dim))
            self._psi_c.append(encode(self._signature_combined(p['question']),
                                      dim=self.dim))
        self._M_q = np.stack(self._psi_q) if self._psi_q else None
        self._M_s = np.stack(self._psi_s) if self._psi_s else None
        self._M_c = np.stack(self._psi_c) if self._psi_c else None
        return len(self.patterns)

    @staticmethod
    def _signature(question: str) -> str:
        return _normalize_numbers(question.lower())[:260]

    @staticmethod
    def _sig_seq(question: str) -> str:
        """Signature structurelle : la séquence de nombres de l'énoncé.

        C'est la clé d'instanciation des opérandes liées (Q) — deux
        problèmes de même séquence ont les mêmes liaisons.
        """
        return ' '.join(f'{v:g}' + ('%' if f else '')
                        for v, f in question_numbers(question))

    @classmethod
    def _signature_combined(cls, question: str) -> str:
        """Contenu + structure : ψ(énoncé) ⊗ ψ(séquence de nombres)."""
        return f"{cls._signature(question)} § {cls._sig_seq(question)}"

    # ── récupération par résonance ───────────────────────────────────────────

    def retrieve(self, question: str, exclude: Optional[int] = None,
                 top_k: int = 3, by: str = 'combined') -> List[Tuple[int, float]]:
        """
        Top-k patterns par résonance (cohérence de phase |Re(⟨ψq|ψp⟩)|).

        by='question'  → ψ(énoncé) — voisinage sémantique
        by='combined'  → ψ(énoncé) ⊗ ψ(séquence de nombres) — structure
        by='skeleton'  → ψ(squelette de chaîne) — diagnostic
        """
        if self._M_q is None:
            return []
        if by == 'question':
            sig, M = self._signature(question), self._M_q
        elif by == 'skeleton':
            sig, M = self._signature(question), self._M_s
        else:
            sig, M = self._signature_combined(question), self._M_c
        psi = encode(sig, dim=self.dim)
        scores = np.abs(np.real(M @ np.conj(psi)))
        out: List[Tuple[int, float]] = []
        for i in np.argsort(-scores):
            if exclude is not None and i == exclude:
                continue
            out.append((int(i), float(scores[i])))
            if len(out) >= top_k:
                break
        return out

    # ── modes de résolution ──────────────────────────────────────────────────

    def solve_memory(self, idx: int) -> Tuple[Optional[float], int, float]:
        """M2 — mémoire fermée : récupère (top-1 = soi), exécute."""
        pat = self.patterns[idx]
        hits = self.retrieve(pat['question'], top_k=1)
        if not hits:
            return None, -1, 0.0
        j, score = hits[0]
        val = execute_chain(self.patterns[j]['chain'], None, self.compiler)
        return val, j, score

    def transfer_candidates(self, idx: int, top_k: int = 3,
                            by: str = 'combined') -> List[Tuple]:
        """
        Top-k instanciations d'un problème : pour chaque pattern résonant
        (leave-one-out), (valeur exécutée, index, score, squelette).
        """
        pat = self.patterns[idx]
        out: List[Tuple] = []
        for j, score in self.retrieve(pat['question'], exclude=idx,
                                      top_k=top_k, by=by):
            chain_j = self.patterns[j]['chain']
            val = execute_chain(chain_j, pat['qnums'], self.compiler)
            out.append((val, j, score, chain_j.skeleton))
        return out

    def solve_transfer(self, idx: int, top_k: int = 3,
                       by: str = 'combined') -> Tuple[Optional[float], Optional[int], float, str]:
        """
        M3 — généralisation leave-one-out.

        Résonance sur les AUTRES problèmes → squelette le plus proche →
        instanciation : les opérandes liées à l'énoncé (Q) sont rebindées
        sur les nombres de la question cible → exécution harmonique.
        """
        for val, j, score, skel in self.transfer_candidates(idx, top_k, by):
            if val is not None:
                return val, j, score, skel
        return None, None, 0.0, ""

    # ═══════════════════════════════════════════════════════════════════════
    # CLASSEMENT SÉMANTIQUE DES CANDIDATS (M4)
    # ═══════════════════════════════════════════════════════════════════════
    #
    # La résonance retrouve les squelettes voisins ; le classement sémantique
    # les RANGE sans oracle. Cinq signaux :
    #
    #   1. RÔLE des nombres liés (Q) : le contexte autour du nombre (sans les
    #      nombres) doit se ressembler entre la question source et la cible —
    #      similarité lexicale (Jaccard) des fenêtres masquées.
    #   2. COUVERTURE : fraction des nombres de la question cible liés par la
    #      chaîne (une chaîne correcte consomme les nombres de l'énoncé).
    #   3. PLAUSIBILITÉ des intermédiaires : entiers ou décimales courtes,
    #      bornés, finis.
    #   4. ORDRE DE GRANDEUR : les valeurs instanciées restent dans l'ordre
    #      de grandeur des valeurs du pattern source.
    #   5. FORME de la réponse : même nature que la source (entier, signe).
    #
    # Le CONSENSUS pondéré (self-consistency) domine : si plusieurs squelettes
    # indépendants convergent vers la même valeur, c'est probablement la bonne.

    _STOP = frozenset(
        'the a an of to in for and with is are was were she he it its her his '
        'they their this that on at by from has have had each every day per '
        'more than as so then how much many'.split())

    @classmethod
    def _jac(cls, a: str, b: str) -> float:
        """Similarité lexicale de deux fenêtres (nombres masqués)."""
        def toks(s: str) -> set:
            s = re.sub(r'\d+(?:\.\d+)?', '#', s.lower())
            return set(w for w in re.findall(r'[a-z#]+', s)
                       if w not in cls._STOP)
        A, B = toks(a), toks(b)
        if not A or not B:
            return 0.0
        return len(A & B) / len(A | B)

    @staticmethod
    def _ctx_window(question: str, idx: int, radius: int = 14) -> str:
        """Fenêtre de contexte autour du idx-ème nombre de l'énoncé."""
        qn = _normalize_numbers(question.lower())
        qn = re.sub(r'(\d),(\d{3})(?:\.\d+)?', r'\1\2', qn)
        pos = [(m.start(), m.end())
               for m in re.finditer(r'\d+(?:\.\d+)?', qn)]
        if idx >= len(pos):
            return ''
        s, e = pos[idx]
        return qn[max(0, s - radius):e + radius]

    @staticmethod
    def _step_values(steps: List[Step],
                     qnums: Optional[List[Tuple[float, bool]]]) -> Optional[List[float]]:
        """Valeurs de chaque étape (None si l'exécution déraille)."""
        vals: List[float] = []
        for i in range(len(steps)):
            v = eval_steps(steps[:i + 1], qnums)
            if v is None or not math.isfinite(v):
                return None
            vals.append(v)
        return vals

    def _role_score(self, j: int, question_cible: str,
                    qnums_cible: List[Tuple[float, bool]]) -> float:
        """Signal 1 — cohérence des rôles des nombres liés (Q)."""
        pat = self.patterns[j]
        scores: List[float] = []
        for st in pat['chain'].steps:
            for o in (st.a, st.b):
                if o is None or o[0] != 'Q':
                    continue
                idx = o[1]
                if idx >= len(pat['qnums']) or idx >= len(qnums_cible):
                    continue
                cs = self._ctx_window(pat['question'], idx)
                ct = self._ctx_window(question_cible, idx)
                if not cs or not ct:
                    continue
                scores.append(self._jac(cs, ct))
        return float(np.mean(scores)) if scores else 0.5

    @staticmethod
    def _plaus_score(vals: Optional[List[float]]) -> float:
        """Signal 3 — plausibilité des valeurs intermédiaires."""
        if not vals:
            return 0.0
        ok = 0
        for v in vals:
            if abs(v) > 1e8:
                continue
            r = round(v, 4)
            if abs(r - round(r)) < 1e-6:
                ok += 1
            elif len(f"{abs(r):.4f}".rstrip('0').split('.')[-1]) <= 2:
                ok += 1
        return ok / len(vals)

    @staticmethod
    def _magnitude_score(vs: Optional[List[float]],
                         vt: Optional[List[float]]) -> float:
        """Signal 4 — ordre de grandeur source vs instancié."""
        if not vs or not vt:
            return 0.0
        s, n = 0.0, 0
        for a, b in zip(vs, vt):
            if abs(a) < 1e-9 and abs(b) < 1e-9:
                s += 1.0
                n += 1
                continue
            if abs(a) < 1e-9 or abs(b) < 1e-9:
                continue
            d = abs(math.log10(abs(a)) - math.log10(abs(b)))
            s += max(0.0, 1.0 - d / 3.0)
            n += 1
        return s / n if n else 0.5

    @staticmethod
    def _form_score(vs: Optional[List[float]],
                    vt: Optional[List[float]]) -> float:
        """Signal 5 — forme de la réponse (signe, intégrité)."""
        if not vs or not vt:
            return 0.5
        a, b = vs[-1], vt[-1]
        s = 0.0
        if (a >= 0) == (b >= 0):
            s += 0.5
        if (abs(a - round(a)) < 1e-6) == (abs(b - round(b)) < 1e-6):
            s += 0.5
        return s

    def semantic_scores(self, idx: int, top_k: int = 20, by: str = 'combined',
                        w: Tuple = (0.0, 0.1, 0.3, 0.15, 0.45)) -> List[Tuple]:
        """
        Top-k candidats avec leur score sémantique (sans oracle).

        score = w[0]·rôle + w[1]·couverture + w[2]·plausibilité
                + w[3]·ordre + w[4]·forme.

        Returns:
            [(valeur, pattern_idx, score_sémantique, résonance, squelette)]
        """
        pat = self.patterns[idx]
        qc = pat['qnums']
        out: List[Tuple] = []
        for j, rs in self.retrieve(pat['question'], exclude=idx,
                                   top_k=top_k, by=by):
            chain_j = self.patterns[j]['chain']
            steps = chain_j.steps
            qs = self.patterns[j]['qnums']
            vs = self._step_values(steps, qs)      # valeurs du pattern source
            vt = self._step_values(steps, qc)      # valeurs instanciées
            n_q = sum(1 for st in steps
                      for o in (st.a, st.b) if o is not None and o[0] == 'Q')
            sem = (w[0] * self._role_score(j, pat['question'], qc)
                   + w[1] * min(1.0, n_q / max(1, len(qc)))
                   + w[2] * self._plaus_score(vt)
                   + w[3] * self._magnitude_score(vs, vt)
                   + w[4] * self._form_score(vs, vt))
            val = execute_chain(chain_j, qc, self.compiler)
            out.append((val, j, sem, rs, chain_j.skeleton))
        out.sort(key=lambda x: -x[2])
        return out

    @staticmethod
    def _consensus_weight(vals: List[Tuple[float, float]], v: float,
                          tol: float = 1e-3) -> float:
        """Poids de consensus : somme des résonances des candidats dont la
        valeur converge vers v (tolérance relative)."""
        return sum(rs for v2, rs in vals
                   if abs(v2 - v) <= tol * max(1.0, abs(v)))

    def solve_transfer_consensus(self, idx: int, top_k: int = 20,
                                 by: str = 'combined',
                                 w: Tuple = (0.0, 0.1, 0.3, 0.15, 0.45),
                                 tol: float = 1e-3) -> Tuple[Optional[float], Optional[int], float, str]:
        """
        M4 — généralisation par consensus pondéré (self-consistency).

        Résonance (top-k) → instanciation → score sémantique. Le classement
        combine le POIDS DE CONSENSUS (les squelettes indépendants qui
        convergent vers la même valeur se renforcent) puis le score
        sémantique en départage.
        """
        cands = self.semantic_scores(idx, top_k, by, w)
        if not cands:
            return None, None, 0.0, ""
        vals = [(round(c[0], 4), c[3]) for c in cands if c[0] is not None]
        if not vals:
            return None, None, 0.0, ""

        def key(c):
            v = round(c[0], 4) if c[0] is not None else None
            cons = self._consensus_weight(vals, v, tol) if v is not None else -1.0
            return (cons, c[2])

        cands.sort(key=key, reverse=True)
        val, j, sem, _rs, skel = cands[0]
        return val, j, sem, skel

    @property
    def stats(self) -> dict:
        return {
            'patterns': len(self.patterns),
            'annotations': sum(p['chain'].n_annot for p in self.patterns),
            'data': self.data_path,
        }


def _fmt(n: float) -> str:
    """Formate sans .0 inutile."""
    return str(int(n)) if float(n).is_integer() else str(round(n, 4))


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO / TESTS RAPIDES
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 WAVE GSM8K — chaînes de calcul (tests rapides)")
    print("=" * 65)

    # 3 réponses canoniques
    demo = [
        ("Janet vend 16 - 3 - 4 = 9 œufs.\nElle fait 9 * 2 = $<<9*2=18>>18.\n#### 18",
         18),
        ("Le coût est 80,000+50,000=$<<80000+50000=130000>>130,000\n"
         "La valeur augmente de 80,000*1.5=<<80000*1.5=120000>>120,000\n"
         "Profit : 200,000-130,000=$<<200000-130000=70000>>70,000\n#### 70000",
         70000),
        ("D'abord 5 * 2 = <<5*2=10>>10\nPuis 10 + 2 = <<10+2=12>>12\n"
         "2/3 * x = 12 → x = 18\n#### 18",
         18),
    ]
    for ans, expected in demo:
        c = parse_answer_chain(ans)
        tag_chain(c, "exemple")
        v = execute_chain(c)
        ok = v is not None and abs(v - expected) < 1e-6
        print(f"\n  attente: {expected} | chaîne: {v} | dérivable: "
              f"{c.derivable} | annotations vérifiées: {c.all_verified}"
              f" {'✅' if ok else '❌'}")
        for line in c.exprs:
            print(f"    {line}")

    mem = GSM8KChainMemory()
    n = mem.load()
    print(f"\n  Patterns chargés : {n} | annotations : "
          f"{mem.stats['annotations']}")
