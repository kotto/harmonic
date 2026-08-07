# -*- coding: utf-8 -*-
"""Exp 5 — CHAMP DE RÉSONANCE : la solution = le mode synchronisé.

« Une onde ne connaît pas la logique, elle connaît la phase. »
Raisonner = mettre progressivement en phase des représentations
compatibles :
  1. chaque phrase excite TOUTES ses interprétations (amplitude) ;
  2. les actions compatibles (opérande présent) propagent des mondes ;
  3. les mondes qui convergent vers le même état s'additionnent EN
     PHASE (interférence constructive) ;
  4. les chemins incompatibles ne contribuent pas (opposition = 0) ;
  5. la conclusion n'est pas déduite : c'est le mode de support
     maximal qui subsiste ; deux modes en opposition → refus calibré.

Zéro retrieval, zéro squelette : uniquement de la synchronisation.
"""
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

from collections import Counter

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import _extract_final
from word_problem_state import (normalize, _split_sentences, detect_actions,
                                _clean_obj, _persons, _PRONOUNS)

_Q_RE = re.compile(r'\b(how many|how much|what is|what are|how far|how long|'
                   r'what was|what did|how old|how often)\b')
_MONEY_RE = re.compile(r'\b(how much|spend|spent|cost|pay|paid|raise|earn|'
                       r'make|revenue|worth|money|dollars)\b')

# Amplitude (spécificité) de chaque opération
_W = {'set_mult': 1.0, 'each_has': 1.0, 'items_at': 0.9, 'sell_at': 0.9,
      'buy_at': 0.9, 'frac_of': 0.9, 'rate_each': 0.8, 'pack': 0.8,
      'rate': 0.7, 'init': 0.8, 'set_plus': 0.9, 'set_minus': 0.9,
      'add': 0.5, 'sub': 0.5}


def _apply(state, rates, money, act):
    """Applique une action locale à un monde. Retourne (new_state, new_rates,
    new_money, amp). Opérande manquant → hypothèse FAIBLE (amp réduite) :
    elle contribue peu au mode, ne le bloque pas (opposition de phase
    douce plutôt que silence)."""
    op = act['op']
    person = act.get('person')
    obj = act.get('obj')
    val = act.get('val', 0.0)
    amp = _W.get(op, 1.0)
    st = dict(state)
    rt = list(rates)
    if op == 'init' and obj:
        st[(person, obj)] = val
    elif op in ('add', 'set_plus') and obj:
        key = (person, obj)
        weak = 1.0 if key in st else 0.2      # opérande absent → hypothèse faible
        st[key] = st.get(key, 0.0) + val
        amp *= weak
    elif op in ('sub', 'set_minus') and obj:
        key = (person, obj)
        weak = 1.0 if key in st else 0.2
        st[key] = st.get(key, 0.0) - val
        amp *= weak
    elif op == 'set_mult':
        ref = act.get('obj2')
        base_obj = act.get('ref_obj') or obj
        base = st.get((ref, base_obj))
        weak = 1.0 if base is not None else 0.2
        st[(person, obj)] = (base if base is not None else 0.0) * val
        amp *= weak
    elif op == 'each_has':
        src = act.get('obj2')
        base = st.get((None, src)) or st.get((person, src))
        weak = 1.0 if base is not None else 0.2
        st[(person, obj)] = (base if base is not None else 0.0) * val
        amp *= weak
    elif op == 'frac_of':
        st[(person, obj)] = val * act.get('amt', 0.0)
    elif op == 'items_at':
        st[(person, obj)] = val
        money += val * act.get('prix', 0.0)
    elif op in ('sell_at', 'buy_at'):
        st[(person, obj)] = val
        money += val * act.get('prix', 0.0)
    elif op == 'pack':
        st[(person, obj)] = val
        rt.append((act.get('prix', 0.0) / val, 'each'))
    elif op == 'rate':
        rt.append((val, act.get('unit', '')))
    elif op == 'rate_each':
        rt.append((val, 'each'))
    else:
        return None
    return st, rt, money, amp


def _answer_of(state, rates, money, q_sent, person):
    """Décode le mode d'un monde : la valeur candidate pour la question."""
    if _MONEY_RE.search(q_sent):
        if money:
            return round(money, 6)
        price = next((v for v, u in rates if u == 'each'), None)
        if price is not None:
            m = re.search(r'how (?:much|many)\s+([a-z]+)\b', q_sent)
            obj = _clean_obj(m.group(1)) if m else None
            qty = sum(v for (p, o), v in state.items()
                      if (obj is None or o == obj))
            if qty:
                return round(price * qty, 6)
        return None
    m = re.search(r'how many\s+([a-z]+)\b', q_sent)
    if m:
        obj = _clean_obj(m.group(1))
        vals = [v for (p, o), v in state.items()
                if o == obj and (person is None or p == person)]
        if vals:
            if 'total' in q_sent or 'altogether' in q_sent:
                return round(sum(vals), 6)
            return round(vals[0], 6)
    return None


class ResonanceField:
    """Champ de résonance : monde × support, propagation par synchronisation."""

    def __init__(self, cap: int = 300):
        self.cap = cap

    def solve(self, question):
        q = normalize(question)
        sentences = _split_sentences(q)
        q_sent = next((s for s in sentences if _Q_RE.search(s)), q)

        worlds = {((), (), 0.0): 1.0}   # (state_items, rates_items, money) → support
        last_person = None
        for sent in sentences:
            if _Q_RE.search(sent):
                continue
            ps = _persons(sent)
            if ps:
                last_person = ps[0]
            acts = detect_actions(sent, last_person, None)
            if not acts:
                continue
            new = {}
            for key, sup in worlds.items():
                state = dict(key[0])
                rates = list(key[1])
                money = key[2]
                for act in acts:
                    r = _apply(state, rates, money, act)
                    if r is None:
                        continue
                    st, rt, mo, amp = r
                    nk = (tuple(sorted(st.items(), key=lambda kv: str(kv))),
                          tuple(sorted(rt)), mo)
                    new[nk] = new.get(nk, 0.0) + sup * amp
            if not new:
                continue
            if len(new) > self.cap:
                new = dict(sorted(new.items(), key=lambda kv: -kv[1])
                           [:self.cap])
            worlds = new

        # Question finale → personne cible
        qp = _persons(q_sent)
        person = qp[0] if qp else (
            last_person if any(p in q_sent for p in _PRONOUNS) else None)

        # Modes : valeur candidate → support (les chemins convergents s'additionnent)
        modes = Counter()
        for key, sup in worlds.items():
            v = _answer_of(dict(key[0]), list(key[1]), key[2], q_sent, person)
            if v is not None:
                modes[v] += sup
        if not modes:
            return None
        top = modes.most_common(2)
        # deux modes en opposition de phase → ambiguïté → refus calibré
        if len(top) >= 2 and abs(top[0][1] - top[1][1]) < 1e-9 \
                and top[0][0] != top[1][0]:
            return None
        return top[0][0]


# ═══════════════════════════════════════════════════════════════════════════════
# MESURES
# ═══════════════════════════════════════════════════════════════════════════════

def measure(label, fn, problems):
    served = correct = refused = 0
    ex = []
    for p in problems:
        exp = _extract_final(p['answer'])
        if exp is None:
            continue
        v = fn(p['question'])
        if v is None:
            refused += 1
            continue
        served += 1
        if abs(v - exp) < 1e-6:
            correct += 1
        elif len(ex) < 4:
            ex.append((p['question'][:70], v, exp))
    print('%-52s pass@1 %.1f%% (%d) | servies %d | précision servie %.1f%% | refus %d'
          % (label, 100.0 * correct / len(problems), correct, served,
             100.0 * correct / max(1, served), refused))
    for q, v, e in ex:
        print('    FAUX %s → %s (attendu %s)' % (q, v, e))
    return correct, served, refused


problems = load_gsm8k()[:100]
print('=== PASS@1 (100) — leave-one-out STRICT ===')
measure('CHAMP DE RÉSONANCE (multi-interprétation)',
        ResonanceField().solve, problems)

from word_problem_state import WordProblemStateSolver, solve_consensus
measure('état seul (simulation) [contrôle, mêmes règles]',
        lambda q: (lambda r: r[0] if r else None)(
            WordProblemStateSolver().solve(q, use_compounds=False)), problems)
measure('état + motifs composés [réf 4b]',
        lambda q: (lambda r: r[0] if r else None)(
            WordProblemStateSolver().solve(q, use_compounds=True)), problems)
measure('consensus multi-plans [réf]',
        lambda q: (lambda r: r[0] if r else None)(solve_consensus(q)), problems)
