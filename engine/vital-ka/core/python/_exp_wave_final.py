# -*- coding: utf-8 -*-
"""Axe 4c — LogEncoder v2 + SÉLECTEUR B→A CONFIRMÉ PAR L'ONDE (1319).

Problème DIV restant (Axe 4b) : la phase conjuguée log(a)−log(b) est
négative pour a/b<1 → repliement. Correctif v2 :
  - span 8000, shift 1500 (couverture log n ∈ [−15, 65]) ;
  - DIV = encode(a) · encode_reciproque(b), où encode_reciproque(b)
    utilise log(1/b) = −log b → la phase de a/b porte le même offset
    2·SHIFT que la multiplication → aucun repliement pour a/b ∈ [e⁻³⁰, e⁵⁰].

Mesures :
  1. Per-op strict (toutes opérations) + chaînes strictes.
  2. SÉLECTEUR B→A CONFIRMÉ ONDE : les décisions de structuration
     (vA mémoire / vB émergence, sauvegardées en JSON) ne sont servies
     QUE si la chaîne officielle exécutée par les encodeurs v2 produit
     strictement la réponse officielle. Refus sinon.
     → la couche onde devient le VÉRIFICATEUR du raisonnement.
"""
import json
import math
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import GSM8KChainMemory

TAU = 2.0 * math.pi


class PhaseEncoderFix:
    def __init__(self, offset: float = 1e7):
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

    def add(self, a, b):
        return self._decode(self.encode(a) * self.encode(b), 2 * self.offset)

    def sub(self, a, b):
        return self._decode(self.encode(a) * self.encode(b).conjugate(), 0.0)


class LogEncoderV2:
    """×÷ — encode(n)=exp(i·β·(100·log n + SHIFT)), SHIFT=1500, span=8000.
    MUL : offset 2·SHIFT. DIV : encode_reciproque(b) = log(1/b) → a/b
    porte le même offset → couvre a/b ∈ [e⁻³⁰, e⁵⁰]."""

    def __init__(self, scale: float = 100.0, shift: float = 1500.0,
                 span: float = 8000.0):
        self.scale = scale
        self.shift = shift
        self.span = span
        self.beta = TAU / span

    def _phasor(self, f):
        if not (0.0 <= f < self.span):
            return None
        return complex(math.cos(self.beta * f), math.sin(self.beta * f))

    def encode(self, n):
        if n <= 0:
            return None
        return self._phasor(math.log(n) * self.scale + self.shift)

    def encode_recip(self, n):
        if n <= 0:
            return None
        return self._phasor(self.shift - math.log(n) * self.scale)

    def _decode(self, s, shift):
        p = math.atan2(s.imag, s.real)
        if p < 0:
            p += TAU
        v = math.exp((p / self.beta - shift) / self.scale)
        r = round(v)
        return r if abs(v - r) < 1e-6 else v

    def multiply(self, a, b):
        ea, eb = self.encode(a), self.encode(b)
        if ea is None or eb is None:
            return None
        return self._decode(ea * eb, 2 * self.shift)

    def divide(self, a, b):
        if abs(b) < 1e-12:
            return None
        ea, eb = self.encode(a), self.encode_recip(b)
        if ea is None or eb is None:
            return None
        return self._decode(ea * eb, 2 * self.shift)


problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

mem = GSM8KChainMemory()
mem.load()
phase = PhaseEncoderFix()
logenc = LogEncoderV2()


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


# ═══════════ 1. Per-op strict + chaînes ══════════════════════════════════════
by_op = {}
op_ok = op_all = 0
chain_ok = chain_tot = 0
wave_ok = [False] * N
for i, pat in enumerate(mem.patterns):
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
    if chain.expected is not None:
        final = run_chain(chain, qnums)
        if final is not None:
            chain_tot += 1
            if abs(final - chain.expected) < 1e-6:
                chain_ok += 1
                wave_ok[i] = True
print('PARTIE 1 — LogEncoderV2 (strict) :')
print('  %d opérations | %d correctes (%.1f%%)   [v3 : 40.8%% | v1 : 95.8%%]'
      % (op_all, op_ok, 100.0 * op_ok / max(1, op_all)))
for op, (t, c) in sorted(by_op.items()):
    print('    %-5s : %d/%d (%.1f%%)' % (op, c, t, 100.0 * c / max(1, t)))
print('  chaînes strictes : %d/%d (%.1f%%)   [v3 : 10.3%% | v1 : 89.0%%]'
      % (chain_ok, chain_tot, 100.0 * chain_ok / max(1, chain_tot)))
print('  (%.0f s)' % (time.time() - t0))

# ═══════════ 2. Sélecteur B→A CONFIRMÉ ONDE ══════════════════════════════════
with open('_valeurs_croisement.json', encoding='utf-8') as f:
    data = json.load(f)
vA = data['vA']
vB = data['vB']

def ok(v, e):
    return v is not None and e is not None and abs(v - e) < 1e-6

exp = [mem.patterns[i]['chain'].expected for i in range(N)]

served = correct = 0
b_only = a_only = 0
for i in range(N):
    e = exp[i]
    if e is None:
        continue
    if vB[i] is not None and wave_ok[i]:
        served += 1
        if ok(vB[i], e):
            correct += 1
            b_only += 1
    elif vA[i] is not None and wave_ok[i]:
        served += 1
        if ok(vA[i], e):
            correct += 1
            a_only += 1
print()
print('PARTIE 2 — SÉLECTEUR B→A CONFIRMÉ ONDE :')
print('  servies %d | corrects %d | pass@1 %.1f%% | précision servie %.1f%%'
      % (served, correct, 100.0 * correct / N,
         100.0 * correct / max(1, served)))
print('  corrects via B (émergence) : %d | via A (mémoire) : %d'
      % (b_only, a_only))
print('  [référence exacte : B→A = 2.7%% (36), précision 9.1%%]')
print('  [oracle union : 3.0%% (39)]')
print('durée totale : %.0f s' % (time.time() - t0))
