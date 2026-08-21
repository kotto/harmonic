#!/usr/bin/env python3
"""
solveur_structure.py — Pipeline complet : extraction de structure par
transverticalité + post-processing + codec ψ
======================================================================

Pipeline :
  1. Transvertical V2 (modèle pré-entraîné) → prédit 2-3 ops
  2. Post-processing : garde 2 ops, convertit %, corrige le rôle
  3. Codec ψ → exécute la chaîne
  4. Résultat final

Usage :
  from solveur_structure import resoudre
  resultat = resoudre(question_texte)
  # ou benchmark complet
  python solveur_structure.py --benchmark
"""

import sys, os, re, torch, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Modèle
_MODEL = None
_TOK = None

NUM_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(%)?', re.IGNORECASE)
OM = {'MUL': 'MULTIPLY', 'SUB': 'SUBTRACT', 'ADD': 'ADD', 'DIV': 'DIVIDE', 'INIT': 'INIT'}


def charger_modele():
    """Charge le modèle transvertical V2 (une fois)."""
    global _MODEL, _TOK
    if _MODEL is not None:
        return
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from peft import PeftModel
    _TOK = AutoTokenizer.from_pretrained('google/flan-t5-small')
    base = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small',
                                                  low_cpu_mem_usage=True)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'data/t5_transvertical_v2/final')
    _MODEL = PeftModel.from_pretrained(base, path)
    _MODEL.eval()


def corriger_role(op, question, est_pct):
    """Corrige le type d'opération selon le contexte du 2e nombre."""
    if est_pct:
        return 'MUL'
    nums = list(NUM_RE.finditer(question))
    if len(nums) < 2:
        return op
    ctx = question[max(0, nums[1].start() - 80):nums[1].start() + 20].lower()

    # DIV : partage, répartition
    for m in ['shared equally', 'divided by', 'bags of', 'packs of',
              'split among', 'shared between', 'bottles of', 'boxes of']:
        if m in ctx:
            return 'DIV'

    # per + personne → DIV, per + unité → MUL
    for m in ['per person', 'per student', 'per child', 'per guest', 'per player']:
        if m in ctx:
            return 'DIV'
    for m in ['per hour', 'per day', 'per mile', 'per second', 'per minute',
              'per week', 'per kg', 'per g', 'per l', 'per meter']:
        if m in ctx:
            return 'MUL'

    # SUB : diminution, dépense, perte
    for m in ['gives away', 'loses', 'sells', 'bought', 'purchased',
              'spent on', 'bought something', 'did not buy', 'remaining',
              'left over', 'are used', 'is used', 'consumed', 'drinks',
              'eats', 'breaks', 'removes', 'throws', 'donates', 'pays']:
        if m in ctx:
            return 'SUB'

    # ADD : augmentation, gain
    for m in ['buys', 'gains', 'finds', 'receives', 'earns', 'collects',
              'adds', 'gets', 'acquires', 'picks up', 'invites more',
              'gathers', 'harvests', 'wins']:
        if m in ctx:
            return 'ADD'

    # MUL : multiplication, répétition
    for m in ['each', 'every', 'apiece', 'doubles', 'triples', 'times',
              'twice', 'for each', 'of the', 'per']:
        if m in ctx:
            return 'MUL'

    return op


def post_process(pred, question):
    """Post-processe la prédiction du modèle : 2 ops, %, correction rôle."""
    pcts = [float(m.group(1)) / 100.0
            for m in NUM_RE.finditer(question) if m.group(2)]
    ops = []
    n = 0
    for token in pred.replace('\n', ' ').split():
        if n >= 2:
            break
        m = re.match(r'(INIT|MUL|SUB|ADD|DIV)\(([^)]+)\)', token.strip())
        if not m:
            continue
        op, v = m.group(1), m.group(2)
        try:
            v = float(v)
        except ValueError:
            continue

        # Conversion pourcentage : 60% dans le texte → 0.6 dans l'op
        ep = False
        for p in pcts:
            if abs(v - p * 100) < 1e-6:
                v = p
                op = 'MUL'
                ep = True
                break

        # Correction de rôle pour la 2e opération
        if n == 1:
            op = corriger_role(op, question, ep)

        mapped = OM.get(op)
        if not mapped:
            continue
        n += 1
        if mapped == 'INIT':
            ops.append({'op': 'INIT', 'value': v})
        elif mapped == 'MULTIPLY':
            ops.append({'op': 'MULTIPLY', 'multiplier': v})
        elif mapped == 'DIVIDE':
            ops.append({'op': 'DIVIDE', 'divisor': v})
        elif mapped == 'SUBTRACT':
            ops.append({'op': 'SUBTRACT', 'value': v})
        elif mapped == 'ADD':
            ops.append({'op': 'ADD', 'value': v})

    return ops


def resoudre(question: str) -> float:
    """Résout un problème GSM8K : transvertical → post-process → codec.

    Args:
        question: Le texte du problème.

    Returns:
        La réponse numérique, ou None si échec.
    """
    from codec_binding import encoder_operations_v2, decoder_trames

    charger_modele()

    inp = _TOK('translate to operations: ' + question, return_tensors='pt',
               max_length=256, truncation=True)
    with torch.no_grad():
        out = _MODEL.generate(**inp, max_new_tokens=64, num_beams=1)
    pred = _TOK.decode(out[0], skip_special_tokens=True)

    ops = post_process(pred, question)
    if not ops:
        return None

    try:
        return decoder_trames(encoder_operations_v2(
            ops, True, True, False, True))
    except Exception:
        return None


def benchmark():
    """Évalue le pipeline sur l'ensemble du test GSM8K."""
    from datasets import load_dataset
    from parseur_annotations import reponse_finale

    print("📊 Benchmark GSM8K — pipeline transvertical + post-processing")
    print("=" * 60)

    test = load_dataset('gsm8k', 'main', split='test')
    ok, n = 0, 0
    for item in test:
        exp = reponse_finale(item['answer'])
        if exp is None:
            continue
        n += 1
        got = resoudre(item['question'])
        if got is not None and abs(got - exp) < 1e-6:
            ok += 1
        if n % 100 == 0:
            print(f"  {n}/{len(test)} : {ok}/{n} ({100*ok/n:.1f}%)")

    print(f"\n  ✓ Score final : {ok}/{n} ({100*ok/n:.1f}%)")
    return ok / n if n else 0


if __name__ == '__main__':
    # Test rapide
    tests = [
        ('John has 20 apples. He gives 8 away.', 12.0),
        ('There are 5 boxes. Each box has 12 eggs.', 60.0),
        ('A store has 150 customers. 60% buy something.', 90.0),
        ('A tank has 120 liters. 90 liters are used.', 30.0),
    ]
    for q, exp in tests:
        got = resoudre(q)
        ok = got is not None and abs(got - exp) < 1e-6
        print(f'  {"✅" if ok else "❌"} got={got:.2f} exp={exp:.2f}')

    if '--benchmark' in sys.argv:
        benchmark()