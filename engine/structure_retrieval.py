#!/usr/bin/env python3
"""
structure_retrieval.py - Resolution par analogie structurelle (k-NN ondulatoire)

V2: Split train/test propre + adaptation SEMANTIQUE des nombres par contexte.
"""

import sys, os, re, json, time, random
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import encode, superpose, resonate, normalize, DEFAULT_DIM
from structure_ondulatoire import StructuredSolver, _classify_operations, _STOP, _VERBS


# ============================================================
# 1. ADAPTATION SEMANTIQUE DES NOMBRES
# ============================================================

def _extract_number_contexts(text):
    """Extrait les nombres avec leur contexte (mots environnants)."""
    results = []
    words = text.lower().split()
    for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', text):
        val = float(m.group(1))
        if val <= 0:
            continue
        char_pos = m.start()
        prefix = text[:char_pos]
        word_pos = len(prefix.split())
        start = max(0, word_pos - 4)
        end = min(len(words), word_pos + 5)
        context_words = []
        for i in range(start, end):
            w = words[i].strip('.,;:!?()"\'')
            if w and not re.match(r'^\d+(?:\.\d+)?$', w) and len(w) >= 2:
                context_words.append(w.lower())
        results.append((val, context_words, word_pos))
    return results


def _context_wave(context_words, dim=DEFAULT_DIM):
    """Encode un contexte en onde."""
    if not context_words:
        return np.zeros(dim, dtype=np.complex128)
    waves = []
    for w in context_words:
        try:
            waves.append(encode(w, dim=dim))
        except Exception:
            pass
    if not waves:
        return np.zeros(dim, dtype=np.complex128)
    return normalize(superpose(*waves))


def _semantic_number_mapping(src_contexts, target_numbers, target_text, dim=DEFAULT_DIM):
    """Cree un mapping semantique entre nombres source et cible."""
    target_contexts = _extract_number_contexts(target_text)
    mapping = {}
    used_targets = set()

    for src_val, src_ctx, src_pos in src_contexts:
        if not src_ctx:
            continue
        psi_src = _context_wave(src_ctx, dim)
        best_target_val = None
        best_score = -1.0
        for tgt_val, tgt_ctx, tgt_pos in target_contexts:
            if tgt_val in used_targets:
                continue
            if not tgt_ctx:
                continue
            psi_tgt = _context_wave(tgt_ctx, dim)
            score = float(resonate(psi_src, psi_tgt))
            pos_sim = 1.0 / (1.0 + abs(src_pos - tgt_pos) * 0.1)
            score *= (0.7 + 0.3 * pos_sim)
            if score > best_score:
                best_score = score
                best_target_val = tgt_val
        if best_target_val is not None:
            mapping[src_val] = best_target_val
            used_targets.add(best_target_val)

    # Fallback positionnel pour les nombres restants
    unused_targets = [t for t, _, _ in target_contexts if t not in used_targets]
    unmapped_src = [v for v, _, _ in src_contexts if v not in mapping]
    for i, sv in enumerate(unmapped_src):
        if i < len(unused_targets):
            mapping[sv] = unused_targets[i]

    return mapping


def _apply_mapping_to_operations(raw_ops, mapping):
    """Remplace les nombres dans les operations selon le mapping."""
    adapted = []
    for op in raw_ops:
        new_op = op.strip()
        for src_val in sorted(mapping.keys(), reverse=True):
            tgt_val = mapping[src_val]
            if src_val == int(src_val):
                src_str = str(int(src_val))
            else:
                src_str = f"{src_val:g}"
            if tgt_val == int(tgt_val):
                tgt_str = str(int(tgt_val))
            else:
                tgt_str = f"{tgt_val:g}"
            new_op = re.sub(
                r'(?<!\d)' + re.escape(src_str) + r'(?!\d)',
                tgt_str, new_op)
        adapted.append(new_op)
    return adapted


def _execute_chain(adapted_ops):
    """Execute une chaine d'operations et retourne le resultat final."""
    results = []
    for raw in adapted_ops:
        clean = raw.strip()
        nums = [float(x) for x in re.findall(r'[\d.]+', clean)]
        ops = re.findall(r'[+\-*/]', clean)
        if len(nums) >= 2 and len(ops) >= 1:
            current = nums[0]
            for i, op in enumerate(ops):
                if i + 1 < len(nums):
                    b = nums[i + 1]
                    if op == '+':
                        current = current + b
                    elif op == '-':
                        current = current - b
                    elif op == '*':
                        current = current * b
                    elif op == '/':
                        current = current / b if b != 0 else 0
            results.append(current)
    return results[-1] if results else None


# ============================================================
# 2. RESOLVEUR K-NN STRUCTUREL (V2)
# ============================================================

class StructuredRetrieval:
    """Resolution par analogie structurelle avec split train/test propre."""

    def __init__(self, dim=DEFAULT_DIM):
        self.dim = dim
        self._index = defaultdict(list)
        self._detector = StructuredSolver(dim=dim)
        self._train_problems = []
        self._test_problems = []
        self._indexed = False

    def split_and_index(self, data_path=None, train_ratio=0.85, seed=42):
        """Split 85/15 stratifie par structure et indexe le train set."""
        if data_path is None:
            here = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')

        with open(data_path, encoding='utf-8') as f:
            all_problems = [json.loads(l) for l in f]

        if not self._detector._trained:
            self._detector.learn_from_gsm8k(data_path)

        # Bucketiser par structure
        struct_buckets = defaultdict(list)
        for p in all_problems:
            a = p.get('answer', '')
            struct_name, _ = _classify_operations(a)
            if struct_name == "unknown":
                continue
            if not re.findall(r'<<(.*?)>>', a):
                continue
            struct_buckets[struct_name].append(p)

        # Split stratifie
        random.seed(seed)
        self._train_problems = []
        self._test_problems = []
        for struct_name, problems in struct_buckets.items():
            random.shuffle(problems)
            split_idx = max(1, int(len(problems) * train_ratio))
            self._train_problems.extend(problems[:split_idx])
            self._test_problems.extend(problems[split_idx:])

        # Indexer le train set
        indexed = 0
        for p in self._train_problems:
            q = p.get('question', '')
            a = p.get('answer', '')
            raw_ops = re.findall(r'<<(.*?)>>', a)
            if not raw_ops:
                continue
            struct_name, _ = _classify_operations(a)
            words = re.findall(r'[a-z]{3,}', q.lower())
            significant = [w for w in words if w not in _STOP and w not in _VERBS]
            if not significant:
                continue
            psi = superpose(*[encode(w, dim=self.dim) for w in significant])
            psi = normalize(psi)
            num_contexts = _extract_number_contexts(q)
            self._index[struct_name].append((psi, q, raw_ops, num_contexts))
            indexed += 1

        self._indexed = True
        print(f"Split: {len(self._train_problems)} train / {len(self._test_problems)} test")
        print(f"Index: {indexed} problemes dans {len(self._index)} structures")
        for s in sorted(self._index.keys(), key=lambda s: -len(self._index[s])):
            n_tr = len(self._index[s])
            n_te = sum(1 for p in self._test_problems
                       if _classify_operations(p.get('answer', ''))[0] == s)
            print(f"  {s:<25s}: {n_tr:>4d} train, {n_te:>4d} test")
        return self

    def _psi_problem(self, question):
        words = re.findall(r'[a-z]{3,}', question.lower())
        significant = [w for w in words if w not in _STOP and w not in _VERBS]
        if not significant:
            return encode("_", dim=self.dim)
        return normalize(superpose(*[encode(w, dim=self.dim) for w in significant]))

    def find_similar(self, question, k=3):
        """Trouve les k problemes train les plus similaires de meme structure."""
        if not self._indexed:
            return []
        psi_q = self._psi_problem(question)
        struct_name, _ = self._detector.detect_structure(question)
        candidates = list(self._index.get(struct_name, []))
        if len(candidates) < k:
            for other_s, items in self._index.items():
                if other_s != struct_name:
                    candidates.extend(items)
                    if len(candidates) >= k * 3:
                        break
        if not candidates:
            return []
        scored = []
        for psi_p, q_p, ops, num_ctx in candidates:
            score = float(resonate(psi_q, psi_p))
            scored.append((score, q_p, ops, num_ctx))
        scored.sort(key=lambda x: -x[0])
        return [(struct_name, s, q, ops, ctx) for s, q, ops, ctx in scored[:k]]

    def solve(self, question, k=3, semantic=True):
        """Resout un probleme par analogie structurelle."""
        if not self._indexed:
            return None
        similar = self.find_similar(question, k=k)
        if not similar:
            return None
        target_numbers = [float(m.group(1)) for m in re.finditer(
            r'\b(\d+(?:\.\d+)?)\b', question) if float(m.group(1)) > 0]
        results = []
        for struct_name, score, src_q, src_ops, src_ctxs in similar:
            if semantic:
                mapping = _semantic_number_mapping(
                    src_ctxs, target_numbers, question, self.dim)
            else:
                src_nums = [v for v, _, _ in src_ctxs]
                mapping = {}
                for i, sv in enumerate(src_nums):
                    if i < len(target_numbers):
                        mapping[sv] = target_numbers[i]
            adapted = _apply_mapping_to_operations(src_ops, mapping)
            try:
                result = _execute_chain(adapted)
                if result is not None:
                    results.append((score, result, struct_name))
            except Exception:
                continue
        if not results:
            return None
        results.sort(key=lambda x: -x[0])
        return results[0][1]

    def benchmark(self, semantic=True):
        """Evalue sur le test set (jamais vu a l'indexation)."""
        if not self._test_problems:
            print("Pas de test set. Lancer split_and_index() d'abord.")
            return {}
        correct, no_sol, total = 0, 0, len(self._test_problems)
        times = []
        mode = "SEMANTIQUE" if semantic else "POSITIONNELLE"
        print(f"BENCHMARK SUR {total} PROBLEMES TEST - Adaptation {mode}")
        for i, p in enumerate(self._test_problems):
            q = p.get('question', '')
            ans_str = p.get('answer', '')
            expected = None
            m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
            if m:
                expected = float(m.group(1))
            t0 = time.time()
            result = self.solve(q, k=3, semantic=semantic)
            dt = (time.time() - t0) * 1000
            times.append(dt)
            if result is None:
                no_sol += 1
            elif expected is not None and abs(result - expected) < 1e-6:
                correct += 1
            if (i + 1) % 25 == 0:
                acc = 100 * correct / (i + 1)
                print(f"  {i+1:>4d}/{total} - {correct:>3d}/{i+1} ({acc:.1f}%) - {no_sol} ss")
        accuracy = 100 * correct / total if total > 0 else 0.0
        avg_ms = np.mean(times) if times else 0
        print(f"\nRESULTATS:")
        print(f"  Problemes: {total}")
        print(f"  Corrects:  {correct}")
        print(f"  Accuracy:  {accuracy:.1f}%")
        print(f"  Sans sol:  {no_sol}")
        print(f"  Temps moy: {avg_ms:.1f} ms")
        return {'accuracy': round(accuracy, 1), 'correct': correct,
                'total': total, 'no_solution': no_sol, 'avg_ms': round(avg_ms, 1)}


# ============================================================
# 3. MAIN
# ============================================================

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--benchmark', action='store_true')
    p.add_argument('--positional', action='store_true')
    p.add_argument('--compare', action='store_true')
    args = p.parse_args()

    if args.compare:
        print("COMPARAISON: Positionnelle vs Semantique\n")
        sr = StructuredRetrieval()
        sr.split_and_index()
        print("\n1. Adaptation POSITIONNELLE:")
        rp = sr.benchmark(semantic=False)
        print("\n2. Adaptation SEMANTIQUE:")
        rs = sr.benchmark(semantic=True)
        print(f"\nCOMPARAISON:")
        print(f"  Positionnelle: {rp['accuracy']:.1f}% ({rp['correct']}/{rp['total']})")
        print(f"  Semantique:    {rs['accuracy']:.1f}% ({rs['correct']}/{rs['total']})")
        if rs['accuracy'] > rp['accuracy']:
            print(f"  -> L'adaptation semantique gagne +{rs['accuracy']-rp['accuracy']:.1f} pts!")

    elif args.benchmark:
        sr = StructuredRetrieval()
        sr.split_and_index()
        sr.benchmark(semantic=not args.positional)

    else:
        print("DEMO STRUCTURED RETRIEVAL V2\n")
        sr = StructuredRetrieval()
        sr.split_and_index()
        print("\nEXEMPLES DE RESOLUTION (test set):")
        for i, prob in enumerate(sr._test_problems[:5]):
            q = prob.get('question', '')[:100]
            ans_str = prob.get('answer', '')
            m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
            expected = float(m.group(1)) if m else None
            result = sr.solve(prob.get('question', ''), k=3, semantic=True)
            status = 'OK' if result and expected and abs(result - expected) < 1e-6 else 'KO'
            print(f"{status} [{i+1}] {q}...")
            print(f"     Attendu: {expected}, Obtenu: {result}")
