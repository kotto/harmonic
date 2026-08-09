#!/usr/bin/env python3
"""
Benchmark + analyse du pipeline structure-aware sur le test set GSM8K.
Itere structure par structure pour ameliorer le score.
"""
import sys, os, re, json, time
import numpy as np
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from raisonneur_ondulatoire import (
    OndulatoireReasoner, _extract_numbers, _best_object_from_sentence,
    _detect_mult_div, _detect_comparison, _hybrid_action, _STOP, MOTS_ACTION
)
from raisonneur_algebrique import AlgebriqueReasoner
from structure_ondulatoire import StructuredSolver

# Charger le detecteur de structures
print("Chargement du detecteur de structures...")
detector = StructuredSolver()
detector.learn_from_gsm8k()

# Charger le test set
from structure_retrieval import StructuredRetrieval
sr = StructuredRetrieval()
sr.split_and_index()
test_problems = sr._test_problems
print(f"Test set: {len(test_problems)} problemes\n")


def solve_gsm8k_structured(question, detector=detector):
    """Pipeline structure-aware + algebrique."""
    r_alg = AlgebriqueReasoner()
    r_hrr = OndulatoireReasoner()
    struct_name, struct_score = detector.detect_structure(question)

    q = question.strip()
    q = re.sub(r'\s+', ' ', q)
    sentences = re.split(r'(?<=[.;!?])\s+', q)
    sentences = [s.strip() for s in sentences if s.strip()]

    last_entity, last_obj = None, None
    for sent in sentences:
        is_question = bool(re.search(r'\b(how many|how much|what is|what are|'
                                      r'how far|how long|how old)\b', sent.lower()))
        if is_question:
            break

        nums = _extract_numbers(sent)
        if not nums:
            continue

        entity, obj = _best_object_from_sentence(sent, r_hrr)
        entity = entity or last_entity
        if entity is None:
            caps = re.findall(r'\b([A-Z][a-z]{2,})\b', sent)
            _pronouns = {'she', 'he', 'they', 'his', 'her', 'their', 'its',
                        'who', 'how', 'what', 'when', 'where', 'there', 'each', 'every'}
            caps = [c for c in caps if c.lower() not in _pronouns]
            if caps: entity = caps[0].lower()
            elif not r_hrr._registry: entity = 'someone'

        if obj is not None and last_obj is not None and obj not in r_hrr.object_names:
            obj = last_obj
        if obj is None and last_obj:
            obj = last_obj
        if obj is None:
            words = [w for w in re.findall(r'[a-z]{3,}', sent.lower()) if w not in _STOP]
            if words: obj = words[-1]

        # Detection d'action
        comparison = _detect_comparison(sent, nums)
        implicit_op = _detect_mult_div(sent)
        rate_mode = bool(re.search(r'\b(per\s+(hour|day|week|month)|a\s+(day|week|month)|'
                                    r'earns?\s+\d+\s+(dollars?\s+)?per)\b', sent.lower()))
        has_init_pattern = bool(re.search(
            r'\b(?:has|had|have|there\s+are|there\s+were|owns?|bought|collected|found|'
            r'bakes?|makes?|produces?|started\s+with|purchased|packed)\s+\d+',
            sent.lower()))
        is_init = (not r_hrr._registry or has_init_pattern)
        if is_init and (comparison or implicit_op):
            is_init = False

        # Ajustement par structure
        if struct_name in ('add_then_multiply', 'subtract_then_multiply',
                          'complex', 'multiplication', 'multiply_and_divide'):
            if implicit_op is None and rate_mode is None and not comparison:
                if re.search(r'\b(each|every|per|costs?|apiece|price)\b', sent.lower()):
                    implicit_op = 'mult'

        # ---- PRIORITY 1: Comparison ----
        if comparison:
            action, comp_val = comparison
            if entity and obj:
                all_ents = set()
                for e_name in list(r_hrr.entity_names):
                    if e_name in sent.lower():
                        all_ents.add(e_name)
                other = (all_ents - {entity}).pop() if len(all_ents - {entity}) > 0 else None
                if other is None:
                    for (k_e, k_o), k_q in list(r_hrr._registry.items()):
                        if k_o == obj and k_e != entity:
                            other = k_e; break
                if other:
                    ref_var = f"{other}_{obj}"
                    var_name = f"{entity}_{obj}"
                    if ref_var not in r_alg._equations:
                        base_val = r_hrr.query(other, obj)
                        if base_val is not None:
                            r_alg.define(ref_var, base_val)
                    r_alg.define(var_name, (action, ref_var, comp_val))
                    if ref_var in r_alg._equations:
                        base = r_alg.eval(ref_var)
                        if base is not None:
                            r_hrr.learn_fact(entity, obj, base * comp_val)
                    last_entity, last_obj = entity, obj
                    continue
                r_hrr.apply_action(entity, obj, action, comp_val)
                r_alg.update(f"{entity}_{obj}", action, comp_val)
                last_entity, last_obj = entity, obj
                continue
            continue

        # ---- PRIORITY 2: Implicit op ----
        if implicit_op:
            action = implicit_op
            if action == 'mult' and entity and obj and len(nums) >= 1:
                key = (entity.lower(), obj.lower())
                if key and key in r_hrr._registry:
                    mult_val = nums[0] if len(nums) == 1 else nums[1]
                    r_hrr.apply_action(entity, obj, 'mult', mult_val)
                    r_alg.update(f"{entity}_{obj}", 'mult', mult_val)
                    last_entity, last_obj = entity, obj
                    continue
                sent_words = set(re.findall(r'[a-z]{3,}', sent.lower()))
                found_cross = False
                for (k_e, k_o), k_q in list(r_hrr._registry.items()):
                    if k_o in sent_words and k_e != entity:
                        ref_var = f"{k_e}_{k_o}"
                        var_name = f"{entity}_{obj}"
                        if ref_var not in r_alg._equations:
                            r_alg.define(ref_var, k_q)
                        mult_val = nums[0] if len(nums) == 1 else nums[1]
                        r_alg.define(var_name, ('mult', ref_var, mult_val))
                        r_hrr.learn_fact(entity, obj, float(k_q) * mult_val)
                        last_entity, last_obj = entity, obj
                        found_cross = True
                        break
                if found_cross:
                    continue
                if entity and obj:
                    r_alg.define(f"{entity}_{obj}", float(nums[0]))
                    r_hrr.learn_fact(entity, obj, float(nums[0]))
                    last_entity, last_obj = entity, obj
                continue
            if action == 'div':
                if entity and obj and len(nums) >= 2:
                    r_alg.define(f"{entity}_{obj}", ('div', float(nums[0]), float(nums[1])))
                    r_hrr.learn_fact(entity, obj, float(nums[0]) / float(nums[1]) if float(nums[1]) != 0 else 0.0)
                    last_entity, last_obj = entity, obj
                    continue
                elif entity and obj and len(nums) == 1:
                    key = (entity.lower(), obj.lower())
                    if key in r_hrr._registry:
                        r_alg.update(f"{entity}_{obj}", 'div', float(nums[0]))
                        r_hrr.apply_action(entity, obj, 'div', float(nums[0]))
                        last_entity, last_obj = entity, obj
                        continue
                    else:
                        r_alg.define(f"{entity}_{obj}", float(nums[0]))
                        r_hrr.learn_fact(entity, obj, float(nums[0]))
                        last_entity, last_obj = entity, obj
                        continue
                continue
            if entity and obj and nums:
                r_alg.define(f"{entity}_{obj}", float(nums[0]))
                r_hrr.learn_fact(entity, obj, float(nums[0]))
                last_entity, last_obj = entity, obj
                continue
            continue

        # ---- PRIORITY 3: Rate ----
        if rate_mode:
            if len(nums) >= 2:
                r_alg.define(f"{entity or 'someone'}_rate", nums[0])
                r_alg.define(f"{entity or 'someone'}_money",
                            ('mult', f"{entity or 'someone'}_rate", nums[1]))
                r_hrr.learn_fact(entity or 'someone', 'money', nums[0] * nums[1])
                last_entity, last_obj = entity, 'money'
                continue
            else:
                if entity and obj:
                    r_alg.define(f"{entity}_{obj}", float(nums[0]))
                    r_hrr.learn_fact(entity, obj, float(nums[0]))
                    last_entity, last_obj = entity, obj
                continue

        # ---- PRIORITY 4: Duration after rate ----
        dur_match = re.search(r'(\d+(?:\.\d+)?)\s+(hours?|days?|weeks?|months?)', sent.lower())
        if dur_match and r_hrr._registry:
            dur_val = float(dur_match.group(1))
            found_rate = False
            for (k_e, k_o), k_q in list(r_hrr._registry.items()):
                is_rate_obj = k_o in ('money', 'dollars', 'salary', 'wages', 'rate',
                                      'hour', 'hours', 'day', 'days')
                if is_rate_obj:
                    total = float(k_q) * dur_val
                    rate_var = f"{k_e}_{k_o}"
                    earnings_var = f"{entity or k_e}_money"
                    if rate_var not in r_alg._equations:
                        r_alg.define(rate_var, float(k_q))
                    if earnings_var != rate_var:
                        r_alg.define(earnings_var, ('mult', rate_var, dur_val))
                    else:
                        base_var = f"_rate_{k_e}_{k_o}"
                        r_alg.define(base_var, float(k_q))
                        r_alg.define(earnings_var, ('mult', base_var, dur_val))
                    r_hrr.learn_fact(entity or k_e, 'money', total)
                    last_entity, last_obj = entity or k_e, 'money'
                    found_rate = True
                    break
            if found_rate:
                continue

        # ---- PRIORITY 5: Init ----
        if is_init:
            if entity and obj:
                var_name = f"{entity}_{obj}"
                r_alg.define(var_name, float(nums[0]))
                r_hrr.learn_fact(entity, obj, float(nums[0]))
                last_entity, last_obj = entity, obj
                continue
            continue

        # ---- PRIORITY 6: Classifier fallback ----
        action = _hybrid_action(sent, r_hrr)
        if entity and obj and nums:
            var_name = f"{entity}_{obj}"
            op_map = {'add': 'add', 'sub': 'sub', 'mult': 'mult', 'div': 'div',
                      '+': 'add', '-': 'sub', '*': 'mult', '/': 'div'}
            op = op_map.get(action, 'add')
            if action == 'init' or not r_alg._equations:
                r_alg.define(var_name, float(nums[0]))
            else:
                r_alg.update(var_name, op, float(nums[0]))
            if action == 'init' or not r_hrr._registry:
                r_hrr.learn_fact(entity, obj, float(nums[0]))
            else:
                r_hrr.apply_action(entity, obj, op, float(nums[0]))
            last_entity, last_obj = entity, obj

    # Resoudre la cible
    target_entity, target_obj = last_entity, last_obj
    question_sent = sentences[-1] if sentences else ''
    if '?' in question_sent or 'how many' in question_sent.lower():
        q_entity, q_obj = _best_object_from_sentence(question_sent, r_hrr)
        target_entity = q_entity or target_entity
        if q_obj:
            action_verbs_flat = {v for vals in MOTS_ACTION.values() for v in vals}
            extra_verbs = {'earn', 'work', 'make', 'get', 'give', 'take', 'use', 'pay', 'cost'}
            if q_obj.lower() not in action_verbs_flat and q_obj.lower() not in extra_verbs:
                target_obj = q_obj

    if target_entity and target_obj:
        target_var = f"{target_entity}_{target_obj}"
        result = r_alg.solve(target_var)
        if result is not None:
            return result
        best_var, best_result = None, None
        for var_name in r_alg._equations:
            if var_name.startswith(f"{target_entity}_"):
                val = r_alg.solve(var_name)
                if val is not None:
                    best_var, best_result = var_name, val
        if best_result is not None:
            return best_result
    if r_alg._equations:
        return r_alg.solve(list(r_alg._equations.keys())[-1])
    return None


# ============================================================
# BENCHMARK + ANALYSE PAR STRUCTURE
# ============================================================

print("=" * 60)
print("BENCHMARK PIPELINE STRUCTURE-AWARE")
print("=" * 60)

# Stats par structure
struct_stats = defaultdict(lambda: {'correct': 0, 'total': 0, 'no_sol': 0})
correct, no_sol, total = 0, 0, len(test_problems)
times = []

for i, p in enumerate(test_problems):
    q = p.get('question', '')
    ans_str = p.get('answer', '')
    expected = None
    m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
    if m:
        expected = float(m.group(1))

    # Determiner la structure reelle
    from structure_ondulatoire import _classify_operations
    real_struct, _ = _classify_operations(ans_str)

    t0 = time.time()
    result = solve_gsm8k_structured(q)
    dt = (time.time() - t0) * 1000
    times.append(dt)

    struct_stats[real_struct]['total'] += 1
    if result is None:
        no_sol += 1
        struct_stats[real_struct]['no_sol'] += 1
    elif expected is not None and abs(result - expected) < 1e-6:
        correct += 1
        struct_stats[real_struct]['correct'] += 1

    if (i + 1) % 25 == 0:
        print(f"  {i+1:>4d}/{total} - {correct}/{i+1} ({100*correct/(i+1):.1f}%)")

accuracy = 100 * correct / total
avg_ms = np.mean(times)

print(f"\nRESULTAT GLOBAL:")
print(f"  Accuracy: {accuracy:.1f}% ({correct}/{total})")
print(f"  Sans sol: {no_sol}")
print(f"  Temps:    {avg_ms:.1f} ms")

print(f"\nPAR STRUCTURE:")
print(f"{'Structure':<25s} {'Score':>10s} {'Details':>20s}")
print("-" * 60)
for struct_name in sorted(struct_stats.keys(), key=lambda s: -struct_stats[s]['total']):
    s = struct_stats[struct_name]
    acc = 100 * s['correct'] / s['total'] if s['total'] > 0 else 0
    bar = '█' * int(acc / 5) + '░' * (20 - int(acc / 5))
    print(f"  {struct_name:<25s} {acc:>5.1f}%  {bar} {s['correct']:>3d}/{s['total']:<4d} "
          f"(ss:{s['no_sol']})")
