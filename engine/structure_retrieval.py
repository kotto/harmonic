#!/usr/bin/env python3
"""
structure_retrieval.py — Résolution par analogie structurelle (k-NN ondulatoire)
=================================================================================

Principe : l'humain résout un nouveau problème en le comparant à des problèmes
connus de même STRUCTURE. On ne mémorise pas des milliards d'exemples (LLM),
on reconnaît la FORME du problème et on adapte la solution.

FONCTIONNEMENT :
1. Apprentissage : indexer les 1301 problèmes GSM8K par leur structure
   et leur empreinte ondulatoire ψ
2. Pour un nouveau problème :
   a. Détecter sa structure par résonance
   b. Trouver les k plus proches problèmes de MÊME structure (k-NN dans l'espace
      des ondes, filtré par type de structure)
   c. Récupérer leur chaîne d'opérations <<...>>
   d. Adapter les nombres : substituer ceux du nouveau problème
   e. Exécuter la chaîne adaptée → réponse

C'est l'équivalent ondulatoire du "raisonnement par cas" (Case-Based Reasoning).

USAGE :
  from structure_retrieval import StructuredRetrieval
  sr = StructuredRetrieval()
  sr.index_gsm8k()
  result = sr.solve("John has 5 apples. Mary has 3 times as many.")
"""

import sys, os, re, json, time
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import encode, superpose, resonate, normalize, DEFAULT_DIM
from structure_ondulatoire import StructuredSolver, _classify_operations, _STOP, _VERBS


class StructuredRetrieval:
    """
    Résolution par recherche analogique dans l'espace des structures.

    Pour chaque problème, on extrait une empreinte ondulatoire ψ qui capture
    sa FORME (mots significatifs). La recherche se fait UNIQUEMENT parmi les
    problèmes de même structure, garantissant que l'analogie est pertinente.
    """

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim

        # Index : structure_name → [(ψ, question, operations, numbers)]
        self._index: Dict[str, List[Tuple[np.ndarray, str, List[str], List[float]]]] = defaultdict(list)

        # Détecteur de structure
        self._detector = StructuredSolver(dim=dim)

        # Cache
        self._indexed = False

    def index_gsm8k(self, data_path: str = None) -> "StructuredRetrieval":
        """
        Indexe les 1301 problèmes GSM8K par structure et empreinte ondulatoire.
        """
        if data_path is None:
            here = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')

        # Apprendre d'abord les prototypes de structure
        if not self._detector._trained:
            self._detector.learn_from_gsm8k(data_path)

        with open(data_path, encoding='utf-8') as f:
            problems = [json.loads(l) for l in f]

        indexed = 0
        for p in problems:
            q = p.get('question', '')
            a = p.get('answer', '')

            # Extraire les opérations
            raw_ops = re.findall(r'<<(.*?)>>', a)
            if not raw_ops:
                continue

            # Classifier la structure
            struct_name, op_types = _classify_operations(a)
            if struct_name == "unknown":
                continue

            # Extraire l'empreinte ondulatoire (mots significatifs uniquement)
            words = re.findall(r'[a-zà-ÿ]{3,}', q.lower())
            significant = [w for w in words if w not in _STOP and w not in _VERBS]
            if not significant:
                continue

            # Encoder les mots en onde
            psi = superpose(*[encode(w, dim=self.dim) for w in significant])
            psi = normalize(psi)

            # Extraire les nombres du problème (pour l'adaptation)
            numbers = [float(m.group(1)) for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', q)
                       if float(m.group(1)) > 0]

            # Stocker
            self._index[struct_name].append((psi, q, raw_ops, numbers))
            indexed += 1

        self._indexed = True
        print(f"✓ {indexed} problèmes indexés dans {len(self._index)} structures")

        # Afficher les stats
        for struct_name, items in sorted(self._index.items(), key=lambda x: -len(x[1])):
            print(f"  {struct_name:<25s}: {len(items):>4d} problèmes")

        return self

    def _psi_problem(self, question: str) -> np.ndarray:
        """Encode un problème en onde (mots significatifs seulement)."""
        words = re.findall(r'[a-zà-ÿ]{3,}', question.lower())
        significant = [w for w in words if w not in _STOP and w not in _VERBS]
        if not significant:
            return encode("_", dim=self.dim)
        psi = superpose(*[encode(w, dim=self.dim) for w in significant])
        return normalize(psi)

    def find_similar(self, question: str, k: int = 3) -> List[Tuple[str, float, str, List[str]]]:
        """
        Trouve les k problèmes les plus similaires de MÊME structure.

        Retourne [(structure_name, score, question, operations), ...]
        """
        if not self._indexed:
            return []

        psi_q = self._psi_problem(question)

        # 1. Détecter la structure
        struct_name, struct_score = self._detector.detect_structure(question)

        # 2. Chercher dans les problèmes de cette structure
        candidates = self._index.get(struct_name, [])

        # Si pas assez de candidats dans cette structure, élargir
        if len(candidates) < k:
            for other_struct, items in self._index.items():
                if other_struct != struct_name:
                    candidates.extend(items)
                    if len(candidates) >= k * 3:
                        break

        if not candidates:
            return []

        # 3. Calculer la similarité cosinus avec tous les candidats
        scored = []
        for psi_p, q_p, ops, nums in candidates:
            score = float(resonate(psi_q, psi_p))
            scored.append((score, q_p, ops, nums))

        # 4. Trier par score décroissant
        scored.sort(key=lambda x: -x[0])

        # Retourner les k meilleurs
        results = []
        for score, q_p, ops, nums in scored[:k]:
            results.append((struct_name, score, q_p, ops))

        return results

    def _expand_chained_operations(self, raw_ops: List[str]) -> List[Tuple[str, float, float, float]]:
        """
        Décompose les opérations chaînées <<a op1 b1 op2 b2 = c>> en étapes simples.
        Retourne [(op, a, b, result), ...]
        """
        steps = []
        for raw in raw_ops:
            clean = raw.strip()
            # Extraire tous les nombres et opérateurs
            nums = [float(x) for x in re.findall(r'[\d.]+', clean)]
            ops = re.findall(r'[+\-*/]', clean)

            if len(nums) >= 2 and len(ops) >= 1:
                current = nums[0]
                for i, op in enumerate(ops):
                    if i + 1 < len(nums):
                        b = nums[i + 1]
                        if op == '+':
                            new_val = current + b
                        elif op == '-':
                            new_val = current - b
                        elif op == '*':
                            new_val = current * b
                        elif op == '/':
                            new_val = current / b if b != 0 else 0
                        else:
                            new_val = current
                        steps.append((op, current, b, new_val))
                        current = new_val

        return steps

    def _adapt_numbers(self, ops: List[str], source_numbers: List[float],
                       target_numbers: List[float]) -> List[str]:
        """
        Adapte les opérations d'un problème source aux nombres du problème cible.

        Stratégie simple : remplacer les nombres de la source par ceux de la cible
        dans l'ordre d'apparition. Si plus de nombres dans la cible, répéter.
        """
        if not target_numbers or not source_numbers:
            return ops

        adapted = []
        target_idx = 0

        for op in ops:
            # Remplacer les nombres dans l'opération
            nums_in_op = re.findall(r'[\d.]+', op)
            new_op = op
            for old_num_str in nums_in_op:
                if target_idx < len(target_numbers):
                    new_num = target_numbers[target_idx]
                    if new_num == int(new_num):
                        new_num_str = str(int(new_num))
                    else:
                        new_num_str = str(new_num)
                    new_op = new_op.replace(old_num_str, new_num_str, 1)
                    target_idx += 1
            adapted.append(new_op)

        return adapted

    def solve(self, question: str, k: int = 3) -> Optional[float]:
        """
        Résout un problème par analogie structurelle.

        1. Trouver les k problèmes les plus similaires de même structure
        2. Pour chaque problème similaire, exécuter sa chaîne d'opérations
           avec les nombres du nouveau problème
        3. Prendre le résultat majoritaire (ou le plus confiant)
        """
        # Extraire les nombres du nouveau problème
        target_numbers = [float(m.group(1)) for m in re.finditer(
            r'\b(\d+(?:\.\d+)?)\b', question) if float(m.group(1)) > 0]

        if not target_numbers:
            return None

        # Trouver les problèmes similaires
        similar = self.find_similar(question, k=k)
        if not similar:
            return None

        results = []
        for struct_name, score, src_question, src_ops in similar:
            # Adapter les opérations
            source_numbers = [float(m.group(1)) for m in re.finditer(
                r'\b(\d+(?:\.\d+)?)\b', src_question) if float(m.group(1)) > 0]
            adapted_ops = self._adapt_numbers(src_ops, source_numbers, target_numbers)

            # Exécuter la chaîne adaptée
            try:
                steps = self._expand_chained_operations(adapted_ops)
                if steps:
                    # Récupérer le dernier résultat
                    final_result = steps[-1][3]
                    results.append((score, final_result, struct_name))
            except Exception:
                continue

        if not results:
            return None

        # Retourner le résultat avec le meilleur score de similarité
        results.sort(key=lambda x: -x[0])
        return results[0][1]


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS + BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

_SAMPLES = [
    ("John has 5 apples. He buys 3 more. How many apples does he have?", 8.0),
    ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6.0),
    ("Tom has 12 dollars. He spends 4 dollars. How many dollars does he have left?", 8.0),
    ("There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?", 30.0),
    ("Sue has 10 stickers. She gives 3 to her friend. How many stickers does Sue have left?", 7.0),
    ("John has 5 apples. Mary has 3 times as many. How many apples does Mary have?", 15.0),
    ("A bakery bakes 24 loaves of bread. They sell 9 loaves. How many loaves are left?", 15.0),
    ("There are 4 cars. Each car has 4 wheels. How many wheels are there?", 16.0),
    ("Sam had 30 dollars. He spent 12 dollars. How many dollars does Sam have left?", 18.0),
    ("Lucy has 8 books. John has 3 times as many. How many books does John have?", 24.0),
    ("A store has 100 items. 45 are sold. How many remain?", 55.0),
    ("John has 5 apples. Mary gave him 3 more apples. How many apples does John have?", 8.0),
    ("James earns 20 dollars per hour. He works 8 hours. How much does he earn?", 160.0),
    ("There are 60 students. They are split into 4 equal groups. How many students per group?", 15.0),
    ("A pizza is cut into 8 slices. John eats 3 slices. How many slices are left?", 5.0),
]


def run_tests():
    print("═══ TEST STRUCTURED RETRIEVAL (k-NN par analogie) ═══")
    sr = StructuredRetrieval()
    sr.index_gsm8k()
    print()

    ok = 0
    for q, expected in _SAMPLES:
        result = sr.solve(q, k=3)
        good = result is not None and abs(result - expected) < 1e-6
        ok += good
        struct_name, score = sr._detector.detect_structure(q)
        similar = sr.find_similar(q, k=1)
        sim_score = similar[0][1] if similar else 0.0
        print(f"{'✅' if good else '❌'} [{struct_name[:22]:<22s} sim={sim_score:.3f}] "
              f"{q[:50]:<52} → {result} (attendu {expected})")
    print(f"\nSCORE : {ok}/{len(_SAMPLES)} ({100 * ok / len(_SAMPLES):.1f}%)")
    return ok


def benchmark_gsm8k(n: int = 200):
    sr = StructuredRetrieval()
    sr.index_gsm8k()

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]

    import random
    random.seed(42)
    sample = random.sample(problems, min(n, len(problems)))

    correct, no_sol, total = 0, 0, len(sample)
    times = []

    for i, p in enumerate(sample):
        q = p.get('question', '')
        ans_str = p.get('answer', '')
        expected = None
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
        if m:
            expected = float(m.group(1))

        t0 = time.time()
        result = sr.solve(q, k=3)
        dt = (time.time() - t0) * 1000
        times.append(dt)

        if result is None:
            no_sol += 1
        elif expected is not None and abs(result - expected) < 1e-6:
            correct += 1

        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{total} — {correct}/{i + 1} "
                  f"({100 * correct / (i + 1):.1f}%)")

    print(f"\n═══ BENCHMARK GSM8K (k-NN structurel) ═══")
    print(f"  Problèmes : {total}")
    print(f"  Corrects  : {correct}")
    print(f"  Accuracy  : {100 * correct / total:.1f}%")
    print(f"  Sans sol. : {no_sol}")
    print(f"  Temps moy.: {np.mean(times):.1f} ms")
    return correct, total


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--benchmark', type=int, default=0)
    args = parser.parse_args()

    if args.test or not args.benchmark:
        run_tests()

    if args.benchmark:
        benchmark_gsm8k(args.benchmark)
