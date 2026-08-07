# -*- coding: utf-8 -*-
"""Axe 4b — ENCODEURS CORRIGÉS (négatifs, décimales, fractions, n<1).

Bugs v3 constatés (Axe 4) :
  - PhaseEncoder : sommes > max_n et NÉGATIFS → repliement de phase.
  - LogEncoder   : log(n)<0 pour n<1 → fréquence négative → 0.

Correctifs (cohérents avec la DFT Harmonique du document fondateur :
fréquences EXACTES, pas de bins FFT) :
  - PhaseEncoderFix : encode(n)=exp(i·α·(n+OFFSET)). L'addition
    décale la phase de 2·OFFSET (connu : on sait qu'on additionne) ;
    la soustraction annule l'offset. → négatifs et grandes sommes OK.
  - LogEncoderFix   : encode(n)=exp(i·β·(log(n)·SCALE+SHIFT)).
    Multiplication → offset 2·SHIFT ; division → offset 0.
    → fractions et n<1 OK, extraction exacte par la phase.

Mesure identique à l'Axe 4 (per-op strict / chaînes strictes /
pipeline combiné structuration + onde), pour comparaison directe.
"""
import sys
import time
import math
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import GSM8KChainMemory
from word_problem_state import solve_consensus

TAU = 2.0 * math.pi


class PhaseEncoderFix:
    """± : encode(n)=exp(i·α·(n+OFFSET)). Add → shift 2·OFFSET ; sub → 0."""

    def __init__(self, offset: float = 1e7):
        # α doit couvrir la phase du PRODUIT (a+b+2·OFFSET ≤ 4·OFFSET) :
        # α = TAU/(4·OFFSET+1) → ni l'encodage (2·OFFSET) ni le produit
        # (4·OFFSET) ne replient.
        self.offset = offset
        self.alpha = TAU / (4 * offset + 1)

    def encode(self, n: float):
        return complex(math.cos(self.alpha * (n + self.offset)),
                       math.sin(self.alpha * (n + self.offset)))

    def _decode(self, s, shift: float) -> float:
        p = math.atan2(s.imag, s.real)
        if p < 0:
            p += TAU
        n = p / self.alpha - shift
        r = round(n)
        return r if abs(n - r) < 1e-6 else n

    def add(self, a: float, b: float) -> float:
        return self._decode(self.encode(a) * self.encode(b), 2 * self.offset)

    def sub(self, a: float, b: float) -> float:
        return self._decode(self.encode(a) * self.encode(b).conjugate(), 0.0)


class LogEncoderFix:
    """×÷ : encode(n)=exp(i·β·(log(n)·SCALE+SHIFT)), n>0. Mul → 2·SHIFT."""

    def __init__(self, scale: float = 100.0, shift: float = 700.0,
                 span: float = 2600.0):
        self.scale = scale
        self.shift = shift
        self.span = span
        self.beta = TAU / span

    def encode(self, n: float):
        if n <= 0:
            return None
        f = math.log(n) * self.scale + self.shift
        if not (0.0 <= f < self.span):
            return None
        return complex(math.cos(self.beta * f), math.sin(self.beta * f))

    def _decode(self, s, shift: float):
        p = math.atan2(s.imag, s.real)
        if p < 0:
            p += TAU
        raw = p / self.beta - shift
        v = math.exp(raw / self.scale)
        r = round(v)
        return r if abs(v - r) < 1e-6 else v

    def multiply(self, a: float, b: float):
        ea = self.encode(a)
        eb = self.encode(b)
        if ea is None or eb is None:
            return None
        return self._decode(ea * eb, 2 * self.shift)

    def divide(self, a: float, b: float):
        if abs(b) < 1e-12:
            return None
        ea = self.encode(a)
        eb = self.encode(b)
        if ea is None or eb is None:
            return None
        return self._decode(ea * eb.conjugate(), 0.0)


# ═══════════ MÊME HARNESS QUE L'AXE 4 ════════════════════════════════════════
problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

mem = GSM8KChainMemory()
mem.load()

phase = PhaseEncoderFix()
logenc = LogEncoderFix()


def _resolve(o, qnums, results):
    k = o[0]
    if k == 'Q':
        return qnums[o[1]][0]
    if k == 'C':
        return o[1]
    if k == 'S':
        return results[o[1]]
    return None


def run_chain(chain, qnums):
    """Chaîne complète exécutée avec les encodeurs CORRIGÉS."""
    results = []
    for st in chain.steps:
        if st.op == 'CONST':
            results.append(results[-1] if results else None)
            continue
        if st.a is None:
            continue
        av = _resolve(st.a, qnums, results)
        bv = _resolve(st.b, qnums, results) if st.b is not None else None
        if av is None or bv is None:
            results.append(None)
            continue
        if st.op == 'ADD':
            r = phase.add(av, bv)
        elif st.op == 'SUB':
            r = phase.sub(av, bv)
        elif st.op == 'MUL':
            r = logenc.multiply(av, bv)
        elif st.op == 'DIV':
            r = logenc.divide(av, bv)
        else:
            r = None
        results.append(r)
    return results[-1] if results else None


# ── PARTIE 1 : per-op strict (toutes les opérations annotées) ────────────────
by_op = {}
op_ok = op_all = 0
for pat in mem.patterns:
    chain = pat['chain']
    qnums = pat['qnums']
    results = []
    for st in chain.steps:
        if st.op not in ('ADD', 'SUB', 'MUL', 'DIV'):
            results.append(None)
            continue
        av = _resolve(st.a, qnums, results)
        bv = _resolve(st.b, qnums, results) if st.b is not None else None
        if av is None or bv is None:
            results.append(None)
            continue
        if st.op == 'ADD':
            r = phase.add(av, bv); exact = av + bv
        elif st.op == 'SUB':
            r = phase.sub(av, bv); exact = av - bv
        elif st.op == 'MUL':
            r = logenc.multiply(av, bv); exact = av * bv
        else:
            r = logenc.divide(av, bv)
            exact = av / bv if abs(bv) > 1e-12 else None
        ok = (r is not None and exact is not None and abs(r - exact) < 1e-6)
        by_op.setdefault(st.op, [0, 0])
        by_op[st.op][0] += 1
        by_op[st.op][1] += 1 if ok else 0
        op_ok += 1 if ok else 0
        op_all += 1
        results.append(r)
print('PARTIE 1 — encodeurs CORRIGÉS (strict) :')
print('  %d opérations | %d correctes (%.1f%%)   [v3 : 40.8%%]'
      % (op_all, op_ok, 100.0 * op_ok / max(1, op_all)))
for op, (t, c) in sorted(by_op.items()):
    before = {'ADD': '63.9', 'SUB': '69.2', 'MUL': '2.2', 'DIV': '1.1'}[op]
    print('    %-5s : %d/%d (%.1f%%)   [v3 : %s%%]'
          % (op, c, t, 100.0 * c / max(1, t), before))
print('  (%.0f s)' % (time.time() - t0))

# ── PARTIE 2 : chaînes complètes strict ──────────────────────────────────────
chains_ok = chains_total = 0
for pat in mem.patterns:
    chain = pat['chain']
    if chain.expected is None:
        continue
    final = run_chain(chain, pat['qnums'])
    if final is None:
        continue
    chains_total += 1
    if abs(final - chain.expected) < 1e-6:
        chains_ok += 1
print('PARTIE 2 — chaînes complètes (strict) :')
print('  %d/%d (%.1f%%)   [v3 : 10.3%%]'
      % (chains_ok, chains_total, 100.0 * chains_ok / max(1, chains_total)))
print('  (%.0f s)' % (time.time() - t0))

# ── PARTIE 3 : pipeline combiné structuration + onde corrigée ────────────────
served = combined_ok = structure_ok = 0
t = time.time()
for i, p in enumerate(problems):
    exp = mem.patterns[i]['chain'].expected
    if exp is None:
        continue
    r = solve_consensus(p['question'])
    if r is None:
        continue
    served += 1
    vB = r[0]
    if abs(vB - exp) < 1e-6:
        structure_ok += 1
    final = run_chain(mem.patterns[i]['chain'], mem.patterns[i]['qnums'])
    if final is not None and abs(vB - exp) < 1e-6 \
            and abs(final - exp) < 1e-6:
        combined_ok += 1
print('PARTIE 3 — combiné structuration + onde CORRIGÉE (%d servies, %.0f s) :'
      % (served, time.time() - t))
print('  structuration seule  : %d (%.1f%%)   [v3 combiné : 0]'
      % (structure_ok, 100.0 * structure_ok / N))
print('  COMBINÉ (corrigé)    : %d (%.1f%%)'
      % (combined_ok, 100.0 * combined_ok / N))
print('durée totale : %.0f s' % (time.time() - t0))
