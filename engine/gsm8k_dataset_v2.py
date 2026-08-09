#!/usr/bin/env python3
"""
gsm8k_dataset_v2.py — Dataset enrichi avec CONTEXTE (état du raisonneur)
=========================================================================
Pour chaque opération annotée, on capture l'ÉTAT du raisonneur HRR
au moment où l'opération est appliquée : quelles entités existent,
quels objets, leurs quantités. Cet état est encodé en onde et concaténé
aux features de la phrase.

Le classifieur verra DONC :
  [ ψ_phrase (512×2) | ψ_contexte (512×2) ] → 2048 features
au lieu de seulement ψ_phrase → 1024 features.

USAGE :
  python gsm8k_dataset_v2.py --build   # construire le dataset enrichi
  python gsm8k_dataset_v2.py --stats   # statistiques
"""

import sys, os, json, re
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wave_lang import encode, superpose, DEFAULT_DIM
from gsm8k_dataset import (
    load_gsm8k, parse_operations, find_best_sentence, encode_sentence_wave
)
from raisonneur_ondulatoire import OndulatoireReasoner, _extract_numbers, _STOP


def build_context_wave(reasoner: OndulatoireReasoner,
                       entity: Optional[str], obj: Optional[str]) -> np.ndarray:
    """
    Encode l'état courant du raisonneur en onde.

    L'état = superpose de tous les faits connus.
    On encode aussi les entités/objets résolus pour cette phrase.
    """
    dim = reasoner.dim
    psi = np.zeros(dim, dtype=np.complex128)

    # Tous les faits connus
    for (e, o), q in reasoner._registry.items():
        psi_e = encode(e, dim=dim)
        psi_o = encode(o, dim=dim)
        psi_q = encode("q" + str(int(q)), dim=dim)
        psi += 0.5 * (psi_e + psi_o + psi_q) / 3.0

    # Entité et objet résolus
    if entity:
        psi += 0.3 * encode(entity, dim=dim)
    if obj:
        psi += 0.3 * encode(obj, dim=dim)

    return psi / (np.linalg.norm(psi) + 1e-9)


def extract_enriched_dataset(sample: int = None) -> List[Dict]:
    """
    Extrait le dataset AVEC contexte.

    Pour chaque problème GSM8K :
      1. On simule le raisonneur HRR pas à pas
      2. À chaque opération annotée, on capture :
         - la phrase associée
         - l'état du raisonneur (contexte)
         - l'entité et l'objet résolus
         - l'opération réelle (label)
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
        if not ops:
            continue

        # Simuler le raisonneur pas à pas
        reasoner = OndulatoireReasoner()
        sentences = re.split(r'(?<=[.;!?])\s+', question)
        sentences = [s.strip() for s in sentences if s.strip()]

        last_entity, last_obj = None, None
        op_idx = 0

        for sent in sentences:
            if 'how many' in sent.lower() or 'how much' in sent.lower():
                break

            nums = _extract_numbers(sent)
            if not nums:
                continue

            # Résoudre entité/objet (comme dans le pipeline)
            entity = reasoner.resolve_entity(sent)
            obj = reasoner.resolve_object(sent)
            entity = entity or last_entity
            if obj is None:
                obj = last_obj
            if obj is None:
                words = [w for w in re.findall(r'[a-z]{3,}', sent.lower())
                         if w not in _STOP]
                obj = words[-1] if words else None
            if entity is None and not reasoner._registry:
                caps = re.findall(r'\b([A-Z][a-z]{2,})\b', sent)
                entity = caps[0].lower() if caps else 'someone'

            # Déterminer l'action réelle (depuis l'annotation)
            if op_idx < len(ops):
                real_op = ops[op_idx]['op']
                a_val = ops[op_idx]['a']
                b_val = ops[op_idx]['b']
            else:
                break

            # Capturer le CONTEXTE avant l'opération
            context_psi = build_context_wave(reasoner, entity, obj)

            # Enregistrer l'exemple
            dataset.append({
                'question': question,
                'sentence': sent,
                'context_entity': entity,
                'context_obj': obj,
                'context_num_facts': len(reasoner._registry),
                'op': real_op,
                'a': a_val,
                'b': b_val,
                'expected': ops[op_idx]['expected'],
                'sentence_wave': encode_sentence_wave(sent),
                'context_wave': context_psi,
                'op_index': op_idx,
                'problem_index': pi,
            })

            # Appliquer l'opération réelle (mise à jour du raisonneur)
            if entity and obj:
                if real_op == '+':
                    reasoner.apply_action(entity, obj, 'add', b_val)
                elif real_op == '-':
                    reasoner.apply_action(entity, obj, 'sub', b_val)
                elif real_op == '*':
                    reasoner.apply_action(entity, obj, 'mult', b_val)
                elif real_op == '/':
                    reasoner.apply_action(entity, obj, 'div', b_val)
                else:
                    reasoner.apply_action(entity, obj, 'init',
                                          ops[op_idx]['expected'])
                last_entity, last_obj = entity, obj

            op_idx += 1

    return dataset


def build_feature_matrix_v2(dataset: List[Dict],
                            dim: int = DEFAULT_DIM) -> Tuple[np.ndarray, np.ndarray, List]:
    """
    Construit X (phrase_wave + context_wave) et y (labels d'opération).
    """
    op_to_idx = {'+': 0, '-': 1, '*': 2, '/': 3}
    n = len(dataset)
    X = np.zeros((n, dim * 4), dtype=np.float64)  # phrase(2*dim) + context(2*dim)
    y = np.zeros(n, dtype=np.int32)
    meta = []

    for i, d in enumerate(dataset):
        psi_s = d.get('sentence_wave')
        if psi_s is None:
            psi_s = encode_sentence_wave(d['sentence'], dim=dim)
        psi_c = d.get('context_wave')
        if psi_c is None:
            psi_c = np.zeros(dim, dtype=np.complex128)

        X[i, :dim] = np.real(psi_s)
        X[i, dim:2 * dim] = np.imag(psi_s)
        X[i, 2 * dim:3 * dim] = np.real(psi_c)
        X[i, 3 * dim:4 * dim] = np.imag(psi_c)

        y[i] = op_to_idx.get(d['op'], 0)
        meta.append(d)

    return X, y, meta


# ═══════════════════════════════════════════════════════════════════════════════
# STATS + BUILD
# ═══════════════════════════════════════════════════════════════════════════════

def print_stats():
    ds = extract_enriched_dataset()
    print(f"═══ DATASET ENRICHI (avec contexte) ═══")
    print(f"  Exemples : {len(ds)}")
    op_counts = Counter(d['op'] for d in ds)
    for op, c in sorted(op_counts.items()):
        print(f"    {op} : {c} ({100 * c / len(ds):.1f}%)")
    ctx_facts = Counter(d['context_num_facts'] for d in ds)
    print(f"  Faits connus au moment de l'opération :")
    for n, c in sorted(ctx_facts.items()):
        print(f"    {n} fait(s) : {c} exemples")
    print(f"\n  3 exemples avec contexte :")
    for d in ds[:3]:
        print(f"    [{d['op']}] '{d['sentence'][:60]}...' entité={d['context_entity']} "
              f"objet={d['context_obj']} faits={d['context_num_facts']}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--stats', action='store_true')
    parser.add_argument('--build', action='store_true', help='Construire et sauvegarder')
    args = parser.parse_args()

    if args.stats or not args.build:
        print_stats()

    if args.build:
        print("  Construction dataset enrichi...")
        ds = extract_enriched_dataset()
        X, y, meta = build_feature_matrix_v2(ds)
        np.savez_compressed('gsm8k_enriched_dataset.npz', X=X, y=y)
        print(f"  Sauvegardé : {len(ds)} exemples, X.shape={X.shape}")
