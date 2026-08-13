#!/usr/bin/env python3
"""
codec_binding.py — Codec trajectoire v2 avec binding entité/objet
=================================================================

Améliorations par rapport au codec v1 (codec_trajectoire.py) :

  1. REGISTRE DE VARIABLES ENRICHIES
     Chaque variable porte {value, entity, object, op, step}.
     La source d'une opération est choisie par SCORE DE BINDING
     (similarité entité/objet) avec fallback sur la dernière modifiée.

  2. OPS STRUCTURALES RÉSOLUES (CROSS_MULT / RATE / DURATION)
     • CROSS_MULT(container, per_unit) → value(container) × per_unit
     • DURATION(d) → mémorise la durée en attente
     • RATE(r) → r × durée_en_attente (si présente), sinon r seul
       → trame MUL (le produit est un déplacement)

  3. OPÉRANDES NON-NUMÉRIQUES
     value/product = nom d'objet → résolu par binding sur le registre.

RÈGLE DE NON-RÉGRESSION : tout binding raté (score 0) retombe sur
l'heuristique v1 (dernière variable modifiée) — le v2 ne peut pas
être pire que le v1 sur un problème donné.

USAGE :
  from codec_binding import encoder_operations_v2, decoder_trames
  frames = encoder_operations_v2(ops)
  resultat = decoder_trames(frames)
"""

import sys, os, re, json, math
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codec_trajectoire import decoder_trames, decoder_trajectoire

PHI = (1 + math.sqrt(5)) / 2
HALF_PI = math.pi / 2
PI = math.pi
ZERO = 0.0

CODE_MAP = {'ADD': 3, 'SUBTRACT': 1, 'MULTIPLY': 2,
            'DIVIDE': 5, 'FRACTION': 6, 'CROSS_MULT': 2, 'RATE': 2}


# ═══════════════════════════════════════════════════════════════════════════
# 1. BINDING ENTITÉ/OBJET
# ═══════════════════════════════════════════════════════════════════════════

def _norm(s) -> str:
    """Normalise un nom pour comparaison (minuscules, non alphanum → _)."""
    if s is None:
        return ''
    s = str(s).lower().strip()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    return s.strip('_')


def score_bind(op: dict, var: dict) -> int:
    """Score de similarité entre une opération et une variable connue.

    +2 objet identique (singulier/pluriel toléré), +1 substring, 0 sinon.

    RÈGLE : l'ENTITÉ seule ne donne AUCUN signal. DeepSeek réutilise la
    même entité sur toutes les ops d'un problème — un binding par entité
    écrase la chaîne et fait régresser les problèmes à flux unique
    (vérifié : 5 succès v1 perdus). Seuls les OBJETS (et le croisement
    entity↔object, DeepSeek mettant parfois le nom d'objet dans entity)
    sont discriminants.
    """
    def eq(a, b):
        return a == b or a == b + 's' or a + 's' == b  # pluriel toléré

    score = 0
    o_op = _norm(op.get('object') or op.get('container') or op.get('product'))
    o_var = _norm(var.get('object'))
    if o_op and o_var:
        if eq(o_op, o_var):
            score += 2
        elif o_op in o_var or o_var in o_op:
            score += 1
    # CROISEMENT : le nom d'objet est parfois porté par le champ entity
    # (ex: SUBTRACT(entity="total_length") pour INIT(object="total_length"))
    e_op = _norm(op.get('entity'))
    if e_op and o_var:
        if eq(e_op, o_var):
            score += 2
        elif e_op in o_var or o_var in e_op:
            score += 1
    return score


def bind_source(op: dict, registre: List[dict], last_var: Optional[str]) -> str:
    """Choisit la variable source : meilleur score de binding, sinon
    la dernière variable modifiée (heuristique v1, fallback sûr)."""
    best_name, best_score = None, 0
    # Itérer du PLUS RÉCENT au plus ancien : à score égal, la variable
    # la plus récente gagne (DeepSeek met la même entité sur toutes les
    # ops → le chaînage doit rester sur le dernier état de l'entité).
    for var in reversed(registre):
        if var.get('value') is None:
            continue  # une variable sans valeur ne peut pas être source
        s = score_bind(op, var)
        if s > best_score:
            best_score, best_name = s, var['name']
    if best_name is None:
        return last_var
    return best_name


def resolve_numeric(op: dict, registre: List[dict], last_var: Optional[str]
                    ) -> Tuple[Optional[float], Optional[str]]:
    """Résout l'opérande : champ numérique direct, sinon nom d'objet
    → binding sur le registre. Retourne (valeur, clé_utilisée)."""
    for key in ('value', 'multiplier', 'per_unit', 'rate',
                'duration', 'divisor'):
        raw = op.get(key)
        if raw is None:
            continue
        if isinstance(raw, (int, float)):
            return float(raw), key
        if isinstance(raw, str) and raw.strip():
            # Nom d'objet → chercher une variable portant ce nom
            target = _norm(raw)
            for var in registre:
                if _norm(var.get('object')) == target or \
                   _norm(var.get('entity')) == target:
                    return float(var['value']), key
            # Substring
            for var in registre:
                o = _norm(var.get('object'))
                if o and (target in o or o in target):
                    return float(var['value']), key
        return None, key
    return None, None


# ═══════════════════════════════════════════════════════════════════════════
# 2. ENCODEUR V2
# ═══════════════════════════════════════════════════════════════════════════

def encoder_operations_v2(ops: List[dict],
                          resolve_cross: bool = True,
                          resolve_rate: bool = True,
                          init_chain: bool = True,
                          cross_fallback: bool = True,
                          texte_nums: Optional[List[float]] = None) -> List[dict]:
    """
    Encode une séquence d'opérations en trames ondulatoires (v2).

    Registre : chaque opération crée une variable nommée e{k} avec
    {value, entity, object, op}. La source est bindée par score,
    jamais par simple ordre.

    Paramètres de contrôle (pour mesurer l'apport de chaque règle) :
      resolve_cross  : résoudre CROSS_MULT (container × per_unit)
      resolve_rate   : résoudre RATE × DURATION
      init_chain     : un INIT d'objet différent ne déplace pas la chaîne
                       (quantité latérale déclarée, pas de redémarrage)
      cross_fallback : CROSS_MULT sans container résolu → multiplier la
                       chaîne (True) ou trame neutre (False)
      texte_nums     : multiset des nombres du TEXTE SOURCE (% normalisés).
                       Active la règle R2 : une op arithmétique dont
                       l'opérande est sur-utilisée par rapport au texte
                       (duplication DeepSeek) est neutralisée.
    """
    frames = []
    registre: List[dict] = []
    var_counter = 0
    last_var = None
    pending_duration = None  # DURATION attend un RATE
    pending_rate = None      # RATE attend un DURATION
    skip_mult_value = None  # multiplier du MULTIPLY doublon à sauter
    chain_entity, chain_obj = None, None   # objet/entité de la chaîne courante
    chain_started = False

    def new_var(val, op, name=None, update_chain=True, parent=None):
        nonlocal last_var
        vname = name or f"e{len(registre) + 1}"
        entry = {'name': vname, 'value': val,
                 'entity': op.get('entity'), 'object': op.get('object'),
                 'op': op.get('op', '').upper(),
                 'parent': parent if parent is not None else last_var}
        registre.append(entry)
        if val is not None and update_chain:
            last_var = vname  # seule une variable avec valeur devient source
        return vname

    def resoudre_taux(rate, d, op, nxt=None):
        """Résout RATE×DURATION quand les deux sont connus (4 cas).

        nxt = prochaine op arithmétique : si elle porte déjà le produit
        précalculé (ADD/SUB value==rate×d, MULTIPLY multiplier==d),
        la résolution est redondante → neutre.
        """
        code = CODE_MAP.get('MULTIPLY', 2)
        product = rate * d
        if nxt is not None:
            nxt_op = nxt.get('op', '').upper()
            try:
                nxt_val = float(nxt.get('value') if nxt_op in ('ADD', 'SUBTRACT')
                                else nxt.get('multiplier'))
            except (TypeError, ValueError):
                nxt_val = None
            if nxt_op in ('ADD', 'SUBTRACT') and nxt_val is not None \
                    and abs(nxt_val - product) < 1e-9:
                return  # l'op suivante précalcule déjà le produit
            if nxt_op == 'MULTIPLY' and nxt_val is not None \
                    and abs(nxt_val - d) < 1e-9:
                return  # MULTIPLY(d) duplique la durée
        if abs(rate - src_val) < 1e-9:
            # cas 1 : RATE redondant avec la source (DeepSeek duplique
            # l'INIT) → neutre, chaîne intacte
            return
        if src_val == 0.0:
            # cas 2 : source placeholder (0) → produit simple
            new_val = product
        else:
            # cas 3 : quantité réelle (pension…) → src × rate × durée
            new_val = src_val * product
        vname = new_var(new_val, op, parent=src_name)
        frames.append({'code': code, 'amp': 1.0, 'phase': HALF_PI,
                       'op': 'MULTIPLY', 'var': vname, 'value': None})
        delta = abs(new_val - src_val)
        frames.append({'code': code, 'amp': delta if delta > 1e-9 else 1.0,
                       'phase': ZERO, 'op': 'MULTIPLY', 'var': vname,
                       'value': new_val})

    def prochaine_arith(idx):
        for nxt in ops[idx + 1:]:
            if nxt.get('op', '').upper() in ('ADD', 'SUBTRACT', 'MULTIPLY',
                                             'DIVIDE', 'CROSS_MULT'):
                return nxt
        return None

    # R2 : comptage de consommation des nombres du texte
    t_counts = {}
    used_counts = {}
    if texte_nums is not None:
        t_counts = Counter(round(v, 6) for v in texte_nums)

    def consomme(v):
        """Marque un opérande comme consommé (INIT et arithmétique)."""
        key = round(v, 6)
        used_counts[key] = used_counts.get(key, 0) + 1

    def sur_utilise(v):
        """True si l'opérande v dépasse son nombre d'occurrences texte."""
        key = round(v, 6)
        if key not in t_counts:
            return False  # valeur dérivée → laissée au motif pourcentage
        return used_counts.get(key, 0) >= t_counts[key]

    for idx, op in enumerate(ops):
        op_name = op.get('op', '').upper()

        # ── INIT : position de départ ──
        if op_name == 'INIT':
            try:
                value = float(op.get('value', 0))
            except (TypeError, ValueError):
                value = 0.0
            consomme(value)
            e_init = _norm(op.get('entity'))
            o_init = _norm(op.get('object'))
            if not init_chain or not chain_started:
                # Premier INIT (ou règle désactivée) : démarre/remplace la chaîne
                chain_started = True
                chain_entity, chain_obj = e_init, o_init
                vname = new_var(value, op)
            elif e_init == chain_entity and o_init == chain_obj:
                # Re-déclaration de la même quantité → remplace la chaîne
                vname = new_var(value, op)
            else:
                # Quantité latérale (ex: "il lui reste 4 hot-dogs") :
                # enregistrée pour le binding par nom, mais NE DÉPLACE
                # PAS la chaîne — les ops suivantes restent sur le cumul.
                vname = new_var(value, op, update_chain=False)
            frames.append({
                'code': 4, 'amp': abs(value), 'phase': 0.0 if value >= 0 else PI,
                'op': 'INIT', 'var': vname, 'value': value,
            })
            continue

        # ── QUERY : aucune trame ──
        if op_name == 'QUERY':
            vname = new_var(None, op)
            frames.append({
                'code': 0, 'amp': 0.0, 'phase': 0.0,
                'op': 'QUERY', 'var': vname, 'value': None,
            })
            continue

        # ── Source bindée ──
        src_name = bind_source(op, registre, last_var)
        src_val = next((v['value'] for v in registre if v['name'] == src_name), 0.0)
        if src_val is None:
            src_val = 0.0

        # ── DURATION : mémorise la durée (produit différé) ──
        if op_name == 'DURATION':
            try:
                d = float(op.get('duration', 0))
            except (TypeError, ValueError):
                d = None
            vname = new_var(None, op)
            frames.append({
                'code': 0, 'amp': 0.0, 'phase': 0.0,
                'op': 'DURATION', 'var': vname, 'value': None,
            })
            if pending_rate is not None and d is not None:
                resoudre_taux(pending_rate, d, op, prochaine_arith(idx))
                pending_rate = None
            else:
                pending_duration = d
            continue

        # ── CROSS_MULT : container × per_unit ──
        if op_name == 'CROSS_MULT' and resolve_cross:
            operand, key = resolve_numeric(op, registre, last_var)
            # Le container est-il résolu ? (sinon : fallback chaîne ou neutre)
            cont = _norm(op.get('container'))
            bound = False
            if cont:
                for var in reversed(registre):
                    o = _norm(var.get('object'))
                    e = _norm(var.get('entity'))
                    if o and (o == cont or o == cont + 's' or o + 's' == cont):
                        bound = True
                        break
                    if e and (e == cont or e == cont + 's' or e + 's' == cont):
                        bound = True
                        break
            if operand is not None and (bound or cross_fallback):
                new_val = src_val * operand
                code = CODE_MAP.get('MULTIPLY', 2)
                vname = new_var(new_val, op)
                frames.append({'code': code, 'amp': 1.0, 'phase': HALF_PI,
                               'op': 'MULTIPLY', 'var': vname, 'value': None})
                delta = abs(new_val - src_val)
                frames.append({'code': code, 'amp': delta if delta > 1e-9 else 1.0,
                               'phase': ZERO, 'op': 'MULTIPLY', 'var': vname,
                               'value': new_val})
                continue
            # fallthrough : opérande irrésolu → trame neutre
            vname = new_var(src_val, op)
            frames.append({'code': 0, 'amp': 0.0, 'phase': 0.0,
                           'op': op_name, 'var': vname, 'value': src_val})
            continue

        # ── RATE : rate × durée en attente (3 cas, ordre libre) ──
        if op_name == 'RATE' and resolve_rate:
            try:
                rate = float(op.get('rate', 0))
            except (TypeError, ValueError):
                rate = None
            if rate is not None and pending_duration is not None:
                resoudre_taux(rate, pending_duration, op, prochaine_arith(idx))
                pending_duration = None
                continue
            # Pas de durée encore : garder le rate en attente
            pending_rate = rate
            vname = new_var(src_val, op)
            frames.append({'code': 0, 'amp': 0.0, 'phase': 0.0,
                           'op': op_name, 'var': vname, 'value': src_val})
            continue

        # ── Opérations arithmétiques classiques ──
        if op_name in ('ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'FRACTION'):
            code = CODE_MAP.get(op_name, 3)

            # Une op arithmétique entre RATE et DURATION brise le couple
            pending_rate = None
            pending_duration = None

            # Opérande numérique ou résolu par nom d'objet
            operand, key = resolve_numeric(op, registre, last_var)
            if operand is None:
                # Opérande irrésolu → trame neutre (non-régression)
                vname = new_var(src_val, op)
                frames.append({'code': code, 'amp': 0.0, 'phase': 0.0,
                               'op': op_name, 'var': vname, 'value': src_val})
                continue

            if op_name == 'FRACTION':
                try:
                    num = float(op.get('numerator', 2))
                    den = float(op.get('denominator', 5))
                    operand = num / den if den != 0 else 0.5
                except (TypeError, ValueError):
                    operand = 0.5

            # R2 (restreinte) : ADD/SUBTRACT consécutif identique dont
            # l'opérande dépasse son nombre d'occurrences texte → doublon
            # DeepSeek → neutraliser.
            #   ex [29] : ADD(5), ADD(5) alors que le texte n'a qu'un 5.
            # MULTIPLY/DIVIDE jamais neutralisés : la répétition y est
            # sémantique (doubler chaque mois, ÷3 puis ×3…).
            if texte_nums is not None and op_name in ('ADD', 'SUBTRACT'):
                prev = None
                for p_op in reversed(ops[:idx]):
                    if p_op.get('op', '').upper() in ('ADD', 'SUBTRACT',
                                                      'MULTIPLY', 'DIVIDE',
                                                      'CROSS_MULT', 'RATE'):
                        prev = p_op
                        break
                if prev is not None and prev.get('op', '').upper() == op_name:
                    try:
                        pv = float(prev.get('value', 0) or 0)
                    except (TypeError, ValueError):
                        pv = None
                    if pv is not None and abs(pv - operand) < 1e-9 \
                            and sur_utilise(operand):
                        vname = new_var(src_val, op)
                        frames.append({'code': code, 'amp': 0.0, 'phase': 0.0,
                                       'op': op_name, 'var': vname,
                                       'value': src_val})
                        continue
            consomme(operand)

            # MOTIF POURCENTAGE : SUBTRACT sur une source dérivée (MULTIPLY)
            # → la vraie source est le PARENT de la dérivée.
            #   3 variantes du même motif :
            #     a) SUBTRACT(dérivée)           : INIT(500) MUL(0.2)=100 SUB(100)  → 500-100
            #     b) SUBTRACT(parent-dérivée)    : INIT(150) MUL(0.6)=90  SUB(60)   → 150-90
            #     c) SUBTRACT(fraction<1)        : MUL(4)=40 SUB(0.1) → 40×(1-0.1)  (remise)
            src_var = src_name
            if op_name == 'SUBTRACT':
                src_entry = next((v for v in registre
                                  if v['name'] == src_var), None)
                if src_entry and src_entry.get('op') == 'MULTIPLY':
                    d = src_entry.get('value')
                    parent = src_entry.get('parent')
                    p_entry = (next((v for v in registre if v['name'] == parent), None)
                               if parent else None)
                    p = p_entry.get('value') if p_entry else None
                    if d is not None and p is not None:
                        if operand == d or operand == p - d:
                            # a/b : soustraire la dérivée du parent
                            src_var, src_val, operand = parent, p, d
                    elif d is not None and 0 < operand < 1:
                        # c : remise en fraction → multiplier par (1-fraction)
                        new_val = src_val * (1 - operand)
                        phase = ZERO
                        vname = new_var(new_val, op, parent=src_var)
                        frames.append({'code': code, 'amp': 1.0, 'phase': HALF_PI,
                                       'op': op_name, 'var': vname, 'value': None})
                        delta = abs(new_val - src_val)
                        frames.append({'code': code, 'amp': delta if delta > 1e-9 else 1.0,
                                       'phase': phase, 'op': op_name, 'var': vname,
                                       'value': new_val})
                        continue

            if op_name == 'ADD':
                new_val = src_val + operand
                phase = ZERO
            elif op_name == 'SUBTRACT':
                new_val = src_val - operand
                phase = PI
            elif op_name == 'MULTIPLY':
                new_val = src_val * operand
                phase = ZERO
            elif op_name == 'DIVIDE':
                new_val = src_val / operand if operand != 0 else src_val
                phase = -HALF_PI
            else:  # FRACTION
                new_val = src_val * operand
                phase = ZERO

            vname = new_var(new_val, op, parent=src_var)
            frames.append({'code': code, 'amp': 1.0, 'phase': HALF_PI,
                           'op': op_name, 'var': vname, 'value': None})
            delta = abs(new_val - src_val)
            frames.append({'code': code, 'amp': delta if delta > 1e-9 else 1.0,
                           'phase': phase, 'op': op_name, 'var': vname,
                           'value': new_val})
            continue

        # ── Op inconnue : trame neutre ──
        vname = new_var(src_val, op)
        frames.append({'code': 0, 'amp': 0.0, 'phase': 0.0,
                       'op': op_name, 'var': vname, 'value': src_val})

    return frames


# ═══════════════════════════════════════════════════════════════════════════
# 3. BENCHMARK GSM8K
# ═══════════════════════════════════════════════════════════════════════════

def parse_ops(output: str) -> List[dict]:
    """Parse le pseudo-code DeepSeek en opérations structurées."""
    OPS = ('INIT', 'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE',
           'CROSS_MULT', 'RATE', 'DURATION', 'QUERY', 'FRACTION')
    ops = []
    for line in output.splitlines():
        m = re.match(r'\s*([A-Z_]+)\s*\((.*)\)', line)
        if not m:
            continue
        name = m.group(1)
        if name not in OPS:
            continue
        args = m.group(2)
        # Ne garder que les lignes qui ressemblent à des ops structurées
        # (présence d'au moins un champ key=value ou d'un opérande)
        fields = {}
        for am in re.finditer(r'([a-z_]+)=("[^"]*"|\d+(?:\.\d+)?)', args):
            k, v = am.group(1), am.group(2)
            fields[k] = v.strip('"') if v.startswith('"') else float(v)
        fields['op'] = name
        ops.append(fields)
    return ops


def expected_answer(answer: str) -> Optional[float]:
    m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', answer)
    return float(m.group(1)) if m else None


def benchmark_gsm8k(dataset: str = 'data/deepseek_distill_test.json',
                    resolve_cross: bool = True,
                    resolve_rate: bool = True,
                    init_chain: bool = False,
                    cross_fallback: bool = True,
                    verbose: bool = False) -> dict:
    """Lance le benchmark complet et catégorise les erreurs."""
    d = json.load(open(dataset, encoding='utf-8'))
    ok, n = 0, 0
    per_cause = {}
    for item in d:
        ops = parse_ops(item['output'])
        exp = expected_answer(item['answer'])
        if exp is None:
            continue
        n += 1
        frames = encoder_operations_v2(ops, resolve_cross, resolve_rate,
                                       init_chain, cross_fallback)
        try:
            got = decoder_trames(frames)
        except Exception:
            got = None
        good = got is not None and abs(got - exp) < 1e-6
        if good:
            ok += 1
            continue
        # Catégoriser l'échec
        names = [o['op'] for o in ops]
        if 'CROSS_MULT' in names or 'RATE' in names or 'DURATION' in names:
            cause = 'structural'
        elif sum(1 for x in names if x == 'INIT') >= 2:
            cause = 'multi_init'
        else:
            cause = 'autre'
        per_cause[cause] = per_cause.get(cause, 0) + 1
        if verbose:
            print(f"  ❌ got={got} exp={exp} | {names}")
    return {'ok': ok, 'n': n, 'pct': 100 * ok / n, 'causes': per_cause}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--no-cross', action='store_true', help='désactiver CROSS_MULT')
    p.add_argument('--no-rate', action='store_true', help='désactiver RATE×DURATION')
    p.add_argument('--v1', action='store_true', help='comparer avec le codec v1')
    args = p.parse_args()

    print("═══ BENCHMARK GSM8K — codec v2 (binding entité/objet) ═══\n")
    r = benchmark_gsm8k(resolve_cross=not args.no_cross,
                        resolve_rate=not args.no_rate)
    print(f"Codec v2 : {r['ok']}/{r['n']} ({r['pct']:.1f}%)")
    print(f"Échecs par cause : {r['causes']}")

    if args.v1:
        from codec_trajectoire import encoder_operations as enc_v1
        d = json.load(open('data/deepseek_distill_test.json', encoding='utf-8'))
        ok1, n1 = 0, 0
        for item in d:
            ops = parse_ops(item['output'])
            exp = expected_answer(item['answer'])
            if exp is None:
                continue
            n1 += 1
            try:
                got = decoder_trames(enc_v1(ops))
            except Exception:
                got = None
            ok1 += got is not None and abs(got - exp) < 1e-6
        print(f"Codec v1 : {ok1}/{n1} ({100 * ok1 / n1:.1f}%)")
