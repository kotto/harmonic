#!/usr/bin/env python3
"""
gsm8k_dataset.py — Extraction du dataset supervisé GSM8K
=========================================================
Parse les 4282 opérations annotées <<a op b = c>> des réponses GSM8K,
associe chaque opération à la phrase de l'énoncé la plus pertinente,
et produit un dataset (phrase, opération, a, b, expected).

Format GSM8K :
  « Janet's ducks lay 16 eggs per day. She eats three for breakfast
    every morning and bakes muffins for her friends. She sells the
    remainder at the farmer's market for $2 each. How much does she
    make per day? »
  Réponse: « 16-3-4=<<16-3-4=9>>9 eggs. 9*2=<<9*2=18>>18 dollars. #### 18 »

Chaque <<...>> donne : opération, opérandes, résultat attendu.
L'ordre des annotations correspond à l'ordre de résolution.

USAGE :
  python gsm8k_dataset.py           # extraire les 4282 exemples
  python gsm8k_dataset.py --stats   # statistiques
"""

import sys, os, json, re
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wave_lang import encode, superpose, DEFAULT_DIM
from encodage_phase import PhaseEncoder


def load_gsm8k(path: str = None) -> List[Dict]:
    if path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f]


def parse_operations(answer_text: str) -> List[Dict]:
    """
    Extrait les opérations des annotations <<a op b = c>>.

    Retourne une liste de {op, a, b, expected, raw}
    """
    ops = []
    for m in re.finditer(r'<<\s*(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)\s*=\s*(-?\d+(?:\.\d+)?)\s*>>', answer_text):
        ops.append({
            'a': float(m.group(1)),
            'b': float(m.group(3)),
            'op': m.group(2),
            'expected': float(m.group(4)),
            'raw': m.group(0),
        })
    return ops


def find_best_sentence(question: str, op: Dict) -> str:
    """
    Associe une opération à la phrase de l'énoncé la plus pertinente.

    Stratégie : chercher la phrase contenant l'opérande 'a' ou 'b',
    ou la dernière phrase avant la question.
    """
    sentences = re.split(r'(?<=[.;!?])\s+', question)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Chercher une phrase contenant l'opérande a ou b
    a_str = str(int(op['a'])) if op['a'] == int(op['a']) else str(op['a'])
    b_str = str(int(op['b'])) if op['b'] == int(op['b']) else str(op['b'])

    for sent in sentences:
        if a_str in sent or b_str in sent:
            return sent

    # Fallback : dernière phrase déclarative
    for sent in reversed(sentences):
        if 'how many' not in sent.lower() and 'how much' not in sent.lower() and 'what is' not in sent.lower():
            return sent

    return sentences[-1] if sentences else question


def extract_dataset(sample: int = None) -> List[Dict]:
    """
    Extrait le dataset complet : pour chaque problème GSM8K,
    parse les opérations annotées et les associe aux phrases.

    Retourne [{question, sentence, op, a, b, expected, op_index, problem_index}]
    """
    problems = load_gsm8k()
    if sample:
        import random
        random.seed(42)
        problems = random.sample(problems, min(sample, len(problems)))

    dataset = []
    for pi, p in enumerate(problems):
        question = p['question']
        ops = parse_operations(p['answer'])
        for oi, op in enumerate(ops):
            sent = find_best_sentence(question, op)
            dataset.append({
                'question': question,
                'sentence': sent,
                'op': op['op'],
                'a': op['a'],
                'b': op['b'],
                'expected': op['expected'],
                'op_index': oi,
                'problem_index': pi,
            })
    return dataset


def encode_sentence_wave(sentence: str, dim: int = DEFAULT_DIM) -> np.ndarray:
    """Encode une phrase en onde (superposition des mots)."""
    words = [w for w in re.findall(r'[a-zà-ÿ]+', sentence.lower()) if len(w) > 1]
    if not words:
        return np.zeros(dim, dtype=np.complex128)
    psi = superpose(*[encode(w, dim=dim) for w in words])
    return psi / (np.linalg.norm(psi) + 1e-9)


def build_feature_matrix(dataset: List[Dict], dim: int = DEFAULT_DIM) -> Tuple[np.ndarray, np.ndarray, List]:
    """
    Construit la matrice de features (ondes) et les labels.

    X : (n_samples, dim*2) — partie réelle + imaginaire concaténées
    y : indices d'opération (0=+, 1=−, 2=×, 3=÷)
    """
    op_to_idx = {'+': 0, '-': 1, '*': 2, '/': 3}
    X = np.zeros((len(dataset), dim * 2), dtype=np.float64)
    y = np.zeros(len(dataset), dtype=np.int32)
    meta = []

    for i, d in enumerate(dataset):
        psi = encode_sentence_wave(d['sentence'], dim=dim)
        X[i, :dim] = np.real(psi)
        X[i, dim:] = np.imag(psi)
        y[i] = op_to_idx.get(d['op'], 0)
        meta.append(d)

    return X, y, meta


# ═══════════════════════════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════════════════════════

def print_stats():
    dataset = extract_dataset()
    print(f"═══ STATS DATASET GSM8K ═══")
    print(f"  Opérations totales : {len(dataset)}")
    op_counts = Counter(d['op'] for d in dataset)
    for op, c in sorted(op_counts.items()):
        print(f"    {op} : {c} ({100*c/len(dataset):.1f}%)")
    print(f"  Problèmes couverts : {len(set(d['problem_index'] for d in dataset))}")
    # Vérification : quelques exemples
    print(f"\n  5 exemples :")
    for d in dataset[:5]:
        print(f"    [{d['op']}] {d['a']} {d['op']} {d['b']} = {d['expected']}")
        print(f"      phrase: {d['sentence'][:80]}...")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--stats', action='store_true')
    args = parser.parse_args()

    if args.stats:
        print_stats()
    else:
        ds = extract_dataset()
        X, y, meta = build_feature_matrix(ds)
        print(f"Dataset extrait : {len(ds)} exemples, X.shape={X.shape}, classes={len(set(y))}")
        # Sauvegarder (optionnel)
        # np.savez_compressed('gsm8k_dataset.npz', X=X, y=y)
        print(f"Classes : {Counter(y.tolist())}")
