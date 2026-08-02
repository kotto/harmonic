"""
🌊 Benchmark GSM8K à la chaîne — 1319 problèmes officiels
==========================================================

Les réponses GSM8K sont des dérivations : chaque ligne porte une
étape annotée « X op Y = <<X op Y = Z>>Z ». Ce benchmark mesure le
moteur à chaînes (wave_gsm8k.py) selon 4 modes :

  M0  annotations     — les 4282 « =Z » officiels sont-ils reproduits
                        par le parseur ? (preuve du langage chaîne)
  M1  couverture      — la chaîne seule reproduit-elle #### ?
                        (le langage chaîne couvre-t-il GSM8K ?)
  M2  mémoire fermée  — récupération par résonance (top-1) puis
                        exécution harmonique (WaveCompiler)
  M3  généralisation  — leave-one-out : squelette d'un AUTRE problème,
                        instancié avec les nombres de la question

Usage :
    python benchmark_gsm8k_chain.py [--sample N] [--mode M0|M1|M2|M3|all]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_gsm8k import (GSM8KChainMemory, parse_answer_chain, execute_chain,
                        _extract_final, _fmt)
from benchmark_gsm8k import load_gsm8k


def fmt_pct(p: float, t: int) -> str:
    return f"{p}/{t} ({100.0 * p / t:.1f}%)" if t else "0/0 (—)"


# ═══════════════════════════════════════════════════════════════════════════════
# M0 — VÉRIFICATION DES ANNOTATIONS (parseur prouvé sur 4282 lignes)
# ═══════════════════════════════════════════════════════════════════════════════

def mode_annotations(problems, verbose=True):
    n_annot = n_verify_ok = n_parse_fail = n_skipped = 0
    for p in problems:
        chain = parse_answer_chain(p['answer'])
        n_annot += chain.n_annot
        n_verify_ok += chain.verified_count
        n_parse_fail += chain.parse_fail_count
        n_skipped += len(re.findall(r'<<([^=<>]*)>>', p['answer']))
    return {'annotations': n_annot, 'verify_ok': n_verify_ok,
            'parse_fail': n_parse_fail, 'skipped': n_skipped}


# ═══════════════════════════════════════════════════════════════════════════════
# M1 — COUVERTURE DU LANGAGE CHAÎNE
# ═══════════════════════════════════════════════════════════════════════════════

def mode_coverage(problems, mem, verbose=True, sample_show=3):
    derivable = no_chain = exec_fail = mismatch = final_ok = 0
    shown = 0
    t0 = time.perf_counter()
    for p in problems:
        chain = parse_answer_chain(p['answer'])
        final_ok += int(chain.derivable)          # texte : dernier =Z == ####
        if not chain.steps:
            no_chain += 1
            continue
        val = execute_chain(chain, None, mem.compiler)
        if val is None:
            exec_fail += 1
            continue
        if val is not None and abs(val - chain.expected) < 1e-6:
            derivable += 1
        else:
            mismatch += 1
        if verbose and shown < sample_show:
            shown += 1
            print(f"\n  ── {p['question'][:80]}")
            print(f"     chaîne : {chain.skeleton}")
            for line in chain.exprs:
                print(f"       {line}")
            print(f"     exécution → {val} | #### → {_fmt(chain.expected)} "
                  f"{'✅' if chain.derivable else '❌'}")
    return {'derivable': derivable, 'no_chain': no_chain,
            'exec_fail': exec_fail, 'mismatch': mismatch,
            'final_ok': final_ok, 'total': len(problems)}


# ═══════════════════════════════════════════════════════════════════════════════
# M2 — MÉMOIRE FERMÉE (résonance top-1 → exécution)
# ═══════════════════════════════════════════════════════════════════════════════

def mode_memory(problems, mem, verbose=True):
    passed = retrieval_ok = total = 0
    for i, p in enumerate(problems):
        expected = _extract_final(p['answer'])
        if expected is None:
            continue
        total += 1
        val, j, score = mem.solve_memory(i)
        retrieval_ok += (j == i)
        ok = val is not None and abs(val - expected) < 1e-6
        passed += ok
    return {'passed': passed, 'total': total,
            'retrieval_self': retrieval_ok}


# ═══════════════════════════════════════════════════════════════════════════════
# M3 — GÉNÉRALISATION (leave-one-out, squelette d'autrui)
# ═══════════════════════════════════════════════════════════════════════════════

def mode_transfer(problems, mem, verbose=True, top_k=3):
    """Généralisation leave-one-out — modes question et combiné."""
    rows = {}
    for by in ('question', 'combined'):
        pass1 = pass3 = total = 0
        skel_matches = 0
        for i, p in enumerate(problems):
            expected = _extract_final(p['answer'])
            if expected is None:
                continue
            total += 1
            target_skeleton = parse_answer_chain(p['answer']).skeleton
            cands = mem.transfer_candidates(i, top_k=top_k, by=by)
            if not cands:
                continue

            # top-1 : statistiques (squelette exact retrouvé ?)
            val1, j1, _s1, skel1 = cands[0]
            if j1 is not None:
                skel_matches += (skel1 == target_skeleton)
                if val1 is not None and abs(val1 - expected) < 1e-6:
                    pass1 += 1

            # pass@k : premier candidat qui réussit parmi les top-k
            for val, j, _s, _sk in cands:
                if j is not None and val is not None \
                        and abs(val - expected) < 1e-6:
                    pass3 += 1
                    break
        rows[by] = {'pass1': pass1, 'pass3': pass3, 'total': total,
                    'skel_match': skel_matches}
    return rows


def mode_semantic(problems, mem, top_k=20, verbose=True):
    """M4 — classement sémantique des candidats (top-k résonance).

    pass1_sem : top-1 par score sémantique pur
    pass1_con : top-1 par consensus pondéré (self-consistency) + sémantique
    pass_k    : oracle — le bon candidat est-il dans le top-k ?
    """
    pass1_sem = pass1_con = pass_k = total = 0
    for i, p in enumerate(problems):
        expected = _extract_final(p['answer'])
        if expected is None:
            continue
        total += 1
        cands = mem.semantic_scores(i, top_k=top_k)
        if not cands:
            continue
        val, _j, _sem, _rs, _sk = cands[0]
        if val is not None and abs(val - expected) < 1e-6:
            pass1_sem += 1
        vc, _jc, _sc, _kc = mem.solve_transfer_consensus(i, top_k=top_k)
        if vc is not None and abs(vc - expected) < 1e-6:
            pass1_con += 1
        for val, j, _s, _rs, _sk in cands:
            if j is not None and val is not None \
                    and abs(val - expected) < 1e-6:
                pass_k += 1
                break
    return {'pass1_sem': pass1_sem, 'pass1_con': pass1_con,
            'pass_k': pass_k, 'total': total}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sample', type=int, default=None)
    ap.add_argument('--mode', default='all',
                    choices=['M0', 'M1', 'M2', 'M3', 'M4', 'all'])
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--topk', type=int, default=20)
    ap.add_argument('--lam', type=float, default=0.5)
    args = ap.parse_args()

    problems = load_gsm8k()
    if args.sample:
        problems = problems[:args.sample]

    print("=" * 70)
    print("  🌊 BENCHMARK GSM8K À LA CHAÎNE — "
          f"{len(problems)} problèmes officiels")
    print("=" * 70)

    mem = GSM8KChainMemory()
    n = mem.load()
    print(f"  Mémoire : {n} patterns | {mem.stats['annotations']} annotations")
    t0 = time.perf_counter()

    if args.mode in ('M0', 'all'):
        r = mode_annotations(problems, verbose=not args.quiet)
        print(f"\n  M0 ANNOTATIONS      : "
              f"{fmt_pct(r['verify_ok'], r['annotations'])} vérifiées "
              f"(parseur prouvé sur les =Z officiels)")

    if args.mode in ('M1', 'all'):
        r = mode_coverage(problems, mem, verbose=not args.quiet)
        print(f"\n  M1 COUVERTURE       : "
              f"{fmt_pct(r['derivable'], r['total'])} dérivables par chaîne "
              f"| sans chaîne: {r['no_chain']} | exécution: {r['exec_fail']} "
              f"| final≠####: {r['mismatch']} "
              f"| (texte dernier=Z==####: {fmt_pct(r['final_ok'], r['total'])})")

    if args.mode in ('M2', 'all'):
        r = mode_memory(problems, mem, verbose=not args.quiet)
        print(f"\n  M2 MÉMOIRE FERMÉE   : "
              f"{fmt_pct(r['passed'], r['total'])} par résonance "
              f"(top-1 = soi : {fmt_pct(r['retrieval_self'], r['total'])})")

    if args.mode in ('M3', 'all'):
        rows = mode_transfer(problems, mem, verbose=not args.quiet)
        for by in ('question', 'combined'):
            r = rows[by]
            label = 'M3 CONTENU   ' if by == 'question' else 'M3 CONTENU+STRUCTURE'
            print(f"\n  {label} : pass@1 {fmt_pct(r['pass1'], r['total'])}"
                  f" | pass@3 {fmt_pct(r['pass3'], r['total'])}"
                  f" (squelette exact retrouvé : "
                  f"{fmt_pct(r['skel_match'], r['total'])})")

    if args.mode in ('M4', 'all'):
        r = mode_semantic(problems, mem, top_k=args.topk,
                          verbose=not args.quiet)
        print(f"\n  M4 SÉMANTIQUE (top-{args.topk}) :")
        print(f"     pass@1 sémantique pur : "
              f"{fmt_pct(r['pass1_sem'], r['total'])}")
        print(f"     pass@1 consensus pondéré : "
              f"{fmt_pct(r['pass1_con'], r['total'])}")
        print(f"     oracle top-{args.topk} (le bon candidat y est) : "
              f"{fmt_pct(r['pass_k'], r['total'])}")

    elapsed = time.perf_counter() - t0
    print(f"\n  ⏱ {elapsed:.1f}s")
    print("=" * 70)
    print("  Rappel — moteur à règles (wave_word_problems) : ~1%")
    print("=" * 70)


if __name__ == "__main__":
    main()
