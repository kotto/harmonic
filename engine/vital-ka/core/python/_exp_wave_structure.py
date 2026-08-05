# -*- coding: utf-8 -*-
"""Axe 4 — STRUCTURATION (solveur d'état) + EXÉCUTION ONDULATOIRE (v3).

La couche arithmétique d'harmonicAI v3 est substituée à l'arithmétique
exacte DANS un pipeline de raisonnement réel, sur les 1319 :

  PARTIE 1 — M0-full STRICT : les encodeurs onde (Phase/Log) sur TOUTES
             les opérations annotées des 1319 chaînes, sans biais de
             sélection (le « 90,2 % » de v3 n'en testait que 193/200)
             et sans tolérance (v3 utilisait ±1 / 1 %).
  PARTIE 2 — Chaînes complètes : chaque chaîne entière exécutée en onde,
             résultat final strictement comparé à la réponse officielle.
  PARTIE 3 — Pipeline combiné : le consensus du solveur d'état (la
             structuration) sert une valeur ; l'onde doit exécuter la
             chaîne officielle sans erreur. Pass@1 combiné.
"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import GSM8KChainMemory
from word_problem_state import solve_consensus
from harmonic_ai_v3 import PhaseEncoder, LogEncoder

problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

mem = GSM8KChainMemory()
mem.load()

phase = PhaseEncoder(max_n=200000)
logenc = LogEncoder(grid_size=4096, L=2.0, SCALE=100.0)


def _resolve(o, qnums, results):
    k = o[0]
    if k == 'Q':
        return qnums[o[1]][0]
    if k == 'C':
        return o[1]
    if k == 'S':
        return results[o[1]]
    return None


def run_chain(chain, qnums, wave: bool):
    """Exécute la chaîne (exact ou onde). Retourne (final, erreurs)."""
    results = []
    errors = 0
    total = 0
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
        total += 1
        if not wave:
            if st.op == 'ADD':
                r = av + bv
            elif st.op == 'SUB':
                r = av - bv
            elif st.op == 'MUL':
                r = av * bv
            elif st.op == 'DIV':
                r = av / bv if abs(bv) > 1e-12 else None
            else:
                r = None
        else:
            if st.op == 'ADD':
                r = phase.add(av, bv)
            elif st.op == 'SUB':
                r = phase.sub(av, bv)
            elif st.op == 'MUL':
                r, _c = logenc.multiply(av, bv)
            elif st.op == 'DIV':
                r, _c = logenc.divide(av, bv)
            else:
                r = None
        if r is None:
            return None, total, total
        # vérification stricte : le résultat onde doit valoir l'exact
        if not wave:
            results.append(r)
            continue
        exact = av + bv if st.op == 'ADD' else \
            (av - bv if st.op == 'SUB' else
             (av * bv if st.op == 'MUL' else
              (av / bv if abs(bv) > 1e-12 else None)))
        if exact is None or abs(r - exact) > 1e-6:
            errors += 1
        results.append(r)
    return (results[-1] if results else None), total, errors


# ═══════════ PARTIE 1 + 2 : M0-full strict + chaînes complètes ═══════════════
by_op = {}
chains_ok_strict = chains_ok_loose = chains_total = 0
ops_ok = ops_total = 0
for i, pat in enumerate(mem.patterns):
    chain = pat['chain']
    qnums = pat['qnums']
    exp = chain.expected
    if exp is None:
        continue
    final, total, errors = run_chain(chain, qnums, wave=True)
    if final is None:
        continue
    chains_total += 1
    if abs(final - exp) < 1e-6:
        chains_ok_strict += 1
    if abs(final - exp) < max(1.0, abs(exp) * 0.01):
        chains_ok_loose += 1
    # stats par op (résultats intermédiaires exacts vs onde)
    _f2, _t2, _e2 = run_chain(chain, qnums, wave=True)
    # (errors déjà comptés : cumulons par op dans une seconde passe)
print('PARTIE 1 — opérations annotées (toutes) :')
op_ok_total = 0
op_all_total = 0
# seconde passe pour les erreurs par op
for i, pat in enumerate(mem.patterns):
    chain = pat['chain']
    qnums = pat['qnums']
    results = []
    for st in chain.steps:
        if st.op in ('ADD', 'SUB', 'MUL', 'DIV'):
            by_op.setdefault(st.op, [0, 0])
            by_op[st.op][0] += 1
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
                r, _ = logenc.multiply(av, bv); exact = av * bv
            else:
                r, _ = logenc.divide(av, bv)
                exact = av / bv if abs(bv) > 1e-12 else None
            ok = exact is not None and abs(r - exact) < 1e-6
            by_op[st.op][1] += 1 if ok else 0
            op_ok_total += 1 if ok else 0
            op_all_total += 1
            results.append(r)
        else:
            results.append(None)
print('  opérations : %d | correctes (strict) : %d (%.1f%%)'
      % (op_all_total, op_ok_total, 100.0 * op_ok_total / max(1, op_all_total)))
for op, (t, c) in sorted(by_op.items()):
    print('    %-5s : %d/%d (%.1f%%)' % (op, c, t, 100.0 * c / max(1, t)))

print('PARTIE 2 — chaînes complètes (strict / tolérance v3) :')
print('  strict : %d/%d (%.1f%%) | tolérance v3 : %d/%d (%.1f%%)'
      % (chains_ok_strict, chains_total, 100.0 * chains_ok_strict / max(1, chains_total),
         chains_ok_loose, chains_total, 100.0 * chains_ok_loose / max(1, chains_total)))
print('  (%.0f s)' % (time.time() - t0))

# ═══════════ PARTIE 3 : pipeline combiné structuration + onde ═══════════════
served = combined_ok = structure_ok = chains_ok_served = 0
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
    final, _t2, _e2 = run_chain(mem.patterns[i]['chain'],
                                mem.patterns[i]['qnums'], wave=True)
    if final is not None and abs(final - exp) < 1e-6:
        chains_ok_served += 1
    if abs(vB - exp) < 1e-6 and final is not None and abs(final - exp) < 1e-6:
        combined_ok += 1
print('PARTIE 3 — combiné structuration + onde (%d servies, %.0f s) :'
      % (served, time.time() - t))
print('  structuration seule (exact)  : %d corrects (%.1f%%)'
      % (structure_ok, 100.0 * structure_ok / N))
print('  chaînes en onde (strict)     : %d corrects (%.1f%%)'
      % (chains_ok_served, 100.0 * chains_ok_served / N))
print('  COMBINÉ (struct + onde)      : %d corrects (%.1f%%)'
      % (combined_ok, 100.0 * combined_ok / N))
print('  survie des servies en onde   : %d/%d (%.1f%%)'
      % (chains_ok_served, served, 100.0 * chains_ok_served / max(1, served)))
print('durée totale : %.0f s' % (time.time() - t0))
