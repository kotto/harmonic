#!/usr/bin/env python3
"""
kaggle_gsm8k_pipeline.ipynb → Script autonome pour Kaggle GPU
===============================================================

Pipeline complet : T5-small + LoRA → annotations GSM8K → codec ψ

Usage sur Kaggle :
  1. New Notebook → Language: Python → Accelerator: GPU T4 x2
  2. Copier-coller ce script dans une cellule, ou uploader le .py
  3. Run All (~30 min)
  4. Le modèle final est dans /kaggle/working/t5_gsm8k_final/
  5. Télécharger pour l'inférence locale

Ce script est AUTONOME : toutes les dépendances sont installées
via pip dans la première cellule, et les modules du codec ψ
sont inclus inline.
"""

# ═══════════════════════════════════════════════════════════════════════════
# CELLULE 1 : Installation des dépendances
# ═══════════════════════════════════════════════════════════════════════════

# %pip install -q torch transformers datasets peft accelerate sentencepiece

# ═══════════════════════════════════════════════════════════════════════════
# CELLULE 2 : Imports et codec ψ inline
# ═══════════════════════════════════════════════════════════════════════════

import sys, os, re, json, math, time
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import Counter

# ── Codec ψ (codec_trajectoire.py) ──
PHI = (1 + math.sqrt(5)) / 2
HALF_PI = math.pi / 2
PI = math.pi
ZERO = 0.0

CODE_MAP = {'ADD': 3, 'SUBTRACT': 1, 'MULTIPLY': 2,
            'DIVIDE': 5, 'FRACTION': 6, 'CROSS_MULT': 2, 'RATE': 2}

def encoder_operations_v2(ops: List[dict],
                          resolve_cross: bool = True,
                          resolve_rate: bool = True,
                          init_chain: bool = False,
                          cross_fallback: bool = True,
                          texte_nums: Optional[List[float]] = None) -> List[dict]:
    """Encode une séquence d'opérations en trames ondulatoires (v2)."""
    frames = []
    registre: List[dict] = []
    last_var = None
    pending_duration = None
    pending_rate = None
    chain_entity, chain_obj = None, None
    chain_started = False

    def _norm(s):
        if s is None: return ''
        return re.sub(r'[^a-z0-9]+', '_', str(s).lower().strip()).strip('_')

    def eq(a, b):
        return a == b or a == b + 's' or a + 's' == b

    def score_bind(op, var):
        score = 0
        o_op = _norm(op.get('object') or op.get('container') or op.get('product'))
        o_var = _norm(var.get('object'))
        if o_op and o_var:
            if eq(o_op, o_var): score += 2
            elif o_op in o_var or o_var in o_op: score += 1
        e_op = _norm(op.get('entity'))
        if e_op and o_var:
            if eq(e_op, o_var): score += 2
            elif e_op in o_var or o_var in e_op: score += 1
        return score

    def bind_source(op, registre, last_var):
        best_name, best_score = None, 0
        for var in reversed(registre):
            if var.get('value') is None: continue
            s = score_bind(op, var)
            if s > best_score:
                best_score, best_name = s, var['name']
        if best_name is None: return last_var
        return best_name

    def resolve_numeric(op, registre, last_var):
        for key in ('value', 'multiplier', 'per_unit', 'rate', 'duration', 'divisor'):
            raw = op.get(key)
            if raw is None: continue
            if isinstance(raw, (int, float)): return float(raw), key
            if isinstance(raw, str) and raw.strip():
                target = _norm(raw)
                for var in registre:
                    if _norm(var.get('object')) == target or _norm(var.get('entity')) == target:
                        return float(var['value']), key
                for var in registre:
                    o = _norm(var.get('object'))
                    if o and (target in o or o in target):
                        return float(var['value']), key
            return None, key
        return None, None

    def new_var(val, op, name=None, update_chain=True, parent=None):
        nonlocal last_var
        vname = name or f"e{len(registre) + 1}"
        entry = {'name': vname, 'value': val,
                 'entity': op.get('entity'), 'object': op.get('object'),
                 'op': op.get('op', '').upper(),
                 'parent': parent if parent is not None else last_var}
        registre.append(entry)
        if val is not None and update_chain:
            last_var = vname
        return vname

    def prochaine_arith(idx):
        for nxt in ops[idx + 1:]:
            if nxt.get('op', '').upper() in ('ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'CROSS_MULT'):
                return nxt
        return None

    def resoudre_taux(rate, d, op, nxt=None):
        product = rate * d
        if nxt is not None:
            nxt_op = nxt.get('op', '').upper()
            try:
                nxt_val = float(nxt.get('value') if nxt_op in ('ADD', 'SUBTRACT') else nxt.get('multiplier'))
            except (TypeError, ValueError):
                nxt_val = None
            if nxt_op in ('ADD', 'SUBTRACT') and nxt_val is not None and abs(nxt_val - product) < 1e-9:
                return
            if nxt_op == 'MULTIPLY' and nxt_val is not None and abs(nxt_val - d) < 1e-9:
                return
        src_name = bind_source(op, registre, last_var)
        src_val = next((v['value'] for v in registre if v['name'] == src_name), 0.0)
        if src_val is None: src_val = 0.0
        if abs(rate - src_val) < 1e-9: return
        if src_val == 0.0: new_val = product
        else: new_val = src_val * product
        vname = new_var(new_val, op, parent=src_name)
        frames.append({'code': 2, 'amp': 1.0, 'phase': HALF_PI,
                       'op': 'MULTIPLY', 'var': vname, 'value': None})
        delta = abs(new_val - src_val)
        frames.append({'code': 2, 'amp': delta if delta > 1e-9 else 1.0,
                       'phase': ZERO, 'op': 'MULTIPLY', 'var': vname, 'value': new_val})

    # R2 : comptage de consommation
    t_counts = {}
    used_counts = {}
    if texte_nums is not None:
        t_counts = Counter(round(v, 6) for v in texte_nums)

    def consomme(v):
        key = round(v, 6)
        used_counts[key] = used_counts.get(key, 0) + 1

    def sur_utilise(v):
        key = round(v, 6)
        if key not in t_counts: return False
        return used_counts.get(key, 0) >= t_counts[key]

    for idx, op in enumerate(ops):
        op_name = op.get('op', '').upper()

        if op_name == 'INIT':
            try: value = float(op.get('value', 0))
            except: value = 0.0
            consomme(value)
            e_init, o_init = _norm(op.get('entity')), _norm(op.get('object'))
            if not init_chain or not chain_started:
                chain_started = True
                chain_entity, chain_obj = e_init, o_init
                vname = new_var(value, op)
            elif e_init == chain_entity and o_init == chain_obj:
                vname = new_var(value, op)
            else:
                vname = new_var(value, op, update_chain=False)
            frames.append({'code': 4, 'amp': abs(value), 'phase': 0.0 if value >= 0 else PI,
                           'op': 'INIT', 'var': vname, 'value': value})
            continue

        if op_name == 'QUERY':
            vname = new_var(None, op)
            frames.append({'code': 0, 'amp': 0.0, 'phase': 0.0,
                           'op': 'QUERY', 'var': vname, 'value': None})
            continue

        # Source bindée
        src_name = bind_source(op, registre, last_var)
        src_val = next((v['value'] for v in registre if v['name'] == src_name), 0.0)
        if src_val is None: src_val = 0.0

        if op_name == 'DURATION':
            try: d = float(op.get('duration', 0))
            except: d = None
            vname = new_var(None, op)
            frames.append({'code': 0, 'amp': 0.0, 'phase': 0.0,
                           'op': 'DURATION', 'var': vname, 'value': None})
            if pending_rate is not None and d is not None:
                resoudre_taux(pending_rate, d, op, prochaine_arith(idx))
                pending_rate = None
            else: pending_duration = d
            continue

        if op_name == 'CROSS_MULT' and resolve_cross:
            operand, key = resolve_numeric(op, registre, last_var)
            cont = _norm(op.get('container'))
            bound = False
            if cont:
                for var in reversed(registre):
                    o = _norm(var.get('object'))
                    e = _norm(var.get('entity'))
                    if o and (o == cont or o == cont + 's' or o + 's' == cont):
                        bound = True; break
                    if e and (e == cont or e == cont + 's' or e + 's' == cont):
                        bound = True; break
            if operand is not None and (bound or cross_fallback):
                new_val = src_val * operand
                vname = new_var(new_val, op)
                frames.append({'code': 2, 'amp': 1.0, 'phase': HALF_PI,
                               'op': 'MULTIPLY', 'var': vname, 'value': None})
                delta = abs(new_val - src_val)
                frames.append({'code': 2, 'amp': delta if delta > 1e-9 else 1.0,
                               'phase': ZERO, 'op': 'MULTIPLY', 'var': vname, 'value': new_val})
                continue
            vname = new_var(src_val, op)
            frames.append({'code': 0, 'amp': 0.0, 'phase': 0.0,
                           'op': op_name, 'var': vname, 'value': src_val})
            continue

        if op_name == 'RATE' and resolve_rate:
            try: rate = float(op.get('rate', 0))
            except: rate = None
            if rate is not None and pending_duration is not None:
                resoudre_taux(rate, pending_duration, op, prochaine_arith(idx))
                pending_duration = None
                continue
            pending_rate = rate
            vname = new_var(src_val, op)
            frames.append({'code': 0, 'amp': 0.0, 'phase': 0.0,
                           'op': op_name, 'var': vname, 'value': src_val})
            continue

        # Opérations arithmétiques
        if op_name in ('ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'FRACTION'):
            code = CODE_MAP.get(op_name, 3)
            operand, key = resolve_numeric(op, registre, last_var)
            if operand is None:
                vname = new_var(src_val, op)
                frames.append({'code': code, 'amp': 0.0, 'phase': 0.0,
                               'op': op_name, 'var': vname, 'value': src_val})
                continue
            if op_name == 'FRACTION':
                try:
                    num = float(op.get('numerator', 2))
                    den = float(op.get('denominator', 5))
                    operand = num / den if den != 0 else 0.5
                except: operand = 0.5

            # R2 : ADD/SUBTRACT consécutif identique
            if texte_nums is not None and op_name in ('ADD', 'SUBTRACT'):
                prev = None
                for p_op in reversed(ops[:idx]):
                    if p_op.get('op', '').upper() in ('ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'CROSS_MULT', 'RATE'):
                        prev = p_op; break
                if prev is not None and prev.get('op', '').upper() == op_name:
                    try: pv = float(prev.get('value', 0) or 0)
                    except: pv = None
                    if pv is not None and abs(pv - operand) < 1e-9 and sur_utilise(operand):
                        vname = new_var(src_val, op)
                        frames.append({'code': code, 'amp': 0.0, 'phase': 0.0,
                                       'op': op_name, 'var': vname, 'value': src_val})
                        continue
            consomme(operand)

            # Motif pourcentage
            src_var = src_name
            src_v = src_val
            if op_name == 'SUBTRACT':
                src_entry = next((v for v in registre if v['name'] == src_var), None)
                if src_entry and src_entry.get('op') == 'MULTIPLY':
                    d = src_entry.get('value')
                    parent = src_entry.get('parent')
                    p_entry = next((v for v in registre if v['name'] == parent), None) if parent else None
                    p = p_entry.get('value') if p_entry else None
                    if d is not None and p is not None:
                        if operand == d or operand == p - d:
                            src_var, src_v, operand = parent, p, d
                elif d is not None and 0 < operand < 1:
                    new_val = src_v * (1 - operand)
                    phase = ZERO
                    vname = new_var(new_val, op, parent=src_var)
                    frames.append({'code': code, 'amp': 1.0, 'phase': HALF_PI,
                                   'op': op_name, 'var': vname, 'value': None})
                    delta = abs(new_val - src_v)
                    frames.append({'code': code, 'amp': delta if delta > 1e-9 else 1.0,
                                   'phase': phase, 'op': op_name, 'var': vname, 'value': new_val})
                    continue

            pending_rate = None
            pending_duration = None

            if op_name == 'ADD': new_val = src_v + operand; phase = ZERO
            elif op_name == 'SUBTRACT': new_val = src_v - operand; phase = PI
            elif op_name == 'MULTIPLY': new_val = src_v * operand; phase = ZERO
            elif op_name == 'DIVIDE': new_val = src_v / operand if operand != 0 else src_v; phase = -HALF_PI
            else: new_val = src_v * operand; phase = ZERO

            vname = new_var(new_val, op, parent=src_var)
            frames.append({'code': code, 'amp': 1.0, 'phase': HALF_PI,
                           'op': op_name, 'var': vname, 'value': None})
            delta = abs(new_val - src_v)
            frames.append({'code': code, 'amp': delta if delta > 1e-9 else 1.0,
                           'phase': phase, 'op': op_name, 'var': vname, 'value': new_val})
            continue

        # Op inconnue
        vname = new_var(src_val, op)
        frames.append({'code': 0, 'amp': 0.0, 'phase': 0.0,
                       'op': op_name, 'var': vname, 'value': src_val})

    return frames


def decoder_trames(frames: List[dict]) -> float:
    """Décode la trajectoire par somme cumulative."""
    z = 0.0 + 0.0j
    final_value = None
    for frame in frames:
        z += frame['amp'] * np.exp(1j * frame['phase'])
        if frame.get('value') is not None:
            final_value = frame['value']
    return float(z.real) if final_value is None else final_value


# ═══════════════════════════════════════════════════════════════════════════
# CELLULE 3 : Parseur d'annotations GSM8K
# ═══════════════════════════════════════════════════════════════════════════

ANOT_RE = re.compile(r'<<([^>]+)>>')
OP_MAP = {'+': 'ADD', '-': 'SUBTRACT', '*': 'MULTIPLY', '/': 'DIVIDE'}

def _nettoyer(expr: str) -> str:
    s = expr.replace('(', '').replace(')', '')
    s = re.sub(r'--', '+', s)
    s = re.sub(r'\+-', '-', s)
    s = re.sub(r'-\+', '-', s)
    s = re.sub(r'\+\+', '+', s)
    return s

def anot2ops(answer: str) -> list:
    ops = []
    chain = None
    for m in ANOT_RE.finditer(answer):
        expr = m.group(1)
        if '=' not in expr: continue
        chain_expr, result_str = expr.split('=', 1)
        try: result = float(result_str)
        except: continue
        clean = _nettoyer(chain_expr)
        if clean.startswith('+'):
            clean = clean[1:]
            if chain is None: chain = 0.0
        neg = 1.0
        if clean.startswith('-'):
            clean = clean[1:]
            neg = -1.0
        tokens = re.findall(r'[\+\-\*\/]|\d+(?:\.\d+)?', clean)
        if not tokens: continue
        try: cur = float(tokens[0]) * neg
        except: continue
        if chain is None or abs(cur - chain) > 1e-9:
            ops.append({'op': 'INIT', 'value': cur})
            chain = cur
        i = 1
        while i + 1 <= len(tokens) - 1:
            if i + 1 >= len(tokens): break
            op = tokens[i]; nxt_str = tokens[i + 1]
            if op not in OP_MAP: break
            try: nxt = float(nxt_str)
            except: break
            mapped = OP_MAP[op]
            if mapped == 'ADD': ops.append({'op': 'ADD', 'value': nxt}); cur += nxt
            elif mapped == 'SUBTRACT': ops.append({'op': 'SUBTRACT', 'value': nxt}); cur -= nxt
            elif mapped == 'MULTIPLY': ops.append({'op': 'MULTIPLY', 'multiplier': nxt}); cur *= nxt
            elif mapped == 'DIVIDE': ops.append({'op': 'DIVIDE', 'divisor': nxt}); cur = cur / nxt if nxt else cur
            i += 2
        chain = result
    return ops

def reponse_finale(answer: str) -> Optional[float]:
    m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', answer)
    return float(m.group(1)) if m else None

def ops2texte(ops: list) -> str:
    parts = []
    for o in ops:
        op = o['op']
        if op == 'INIT': parts.append(f'INIT({o["value"]})')
        elif op == 'ADD': parts.append(f'ADD({o["value"]})')
        elif op == 'SUBTRACT': parts.append(f'SUB({o["value"]})')
        elif op == 'MULTIPLY': parts.append(f'MUL({o["multiplier"]})')
        elif op == 'DIVIDE': parts.append(f'DIV({o["divisor"]})')
    return ' '.join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# CELLULE 4 : Construction du dataset
# ═══════════════════════════════════════════════════════════════════════════

print("📦 Construction du dataset d'entraînement...")

from datasets import load_dataset
train = load_dataset('gsm8k', 'main', split='train')
test = load_dataset('gsm8k', 'main', split='test')

exemples = []
for item in train:
    exp = reponse_finale(item['answer'])
    if exp is None: continue
    ops = anot2ops(item['answer'])
    if not ops: continue
    try:
        got = decoder_trames(encoder_operations_v2(ops, True, True, False, True))
        if got is None or abs(got - exp) > 1e-6: continue
    except: continue
    exemples.append({'input': item['question'], 'target': ops2texte(ops)})

print(f"  Dataset : {len(exemples)} paires (question → ops)")
print(f"  Exemple : {exemples[0]['target'][:60]}...")

# Sauvegarder
import json
with open('/kaggle/working/gsm8k_ops_train.jsonl', 'w') as f:
    for ex in exemples:
        f.write(json.dumps(ex) + '\n')

# Évaluation rapide des annotations gold
print("\n🔍 Validation des annotations gold sur le test set...")
ok_gold = 0
for item in test:
    exp = reponse_finale(item['answer'])
    if exp is None: continue
    ops = anot2ops(item['answer'])
    if not ops: continue
    try:
        got = decoder_trames(encoder_operations_v2(ops, True, True, False, True))
        ok_gold += got is not None and abs(got - exp) < 1e-6
    except: continue
print(f"  Score gold (codec ψ + annotations) : {ok_gold}/{len(test)} ({100*ok_gold/len(test):.1f}%)")


# ═══════════════════════════════════════════════════════════════════════════
# CELLULE 5 : Entraînement T5-small + LoRA
# ═══════════════════════════════════════════════════════════════════════════

print("\n🚀 Démarrage de l'entraînement...")

import torch
from transformers import (
    AutoTokenizer, AutoModelForSeq2SeqLM,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

# Dataset HuggingFace
ds = Dataset.from_list(exemples)
split = ds.train_test_split(test_size=0.05, seed=42)
train_ds, val_ds = split['train'], split['test']
print(f"  Train : {len(train_ds)}, Validation : {len(val_ds)}")

# Tokenizer
tokenizer = AutoTokenizer.from_pretrained('google/flan-t5-small')

def tokenize(batch):
    inputs = tokenizer(
        ['translate to operations: ' + t for t in batch['input']],
        max_length=384, truncation=True, padding=False)
    targets = tokenizer(
        batch['target'], max_length=128, truncation=True, padding=False)
    inputs['labels'] = targets['input_ids']
    return inputs

cols = train_ds.column_names
train_tok = train_ds.map(tokenize, batched=True, remove_columns=cols)
val_tok = val_ds.map(tokenize, batched=True, remove_columns=cols)

# Modèle
model = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small')
lora_config = LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM, r=16, lora_alpha=32,
    lora_dropout=0.1, target_modules=['q', 'v'])
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Entraînement
training_args = TrainingArguments(
    output_dir='/kaggle/working/t5_gsm8k',
    num_train_epochs=5,
    per_device_train_batch_size=16,
    gradient_accumulation_steps=2,
    learning_rate=3e-4,
    warmup_ratio=0.1,
    logging_steps=50,
    eval_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True,
    fp16=True,
    report_to='none',
    dataloader_num_workers=2,
    remove_unused_columns=False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_tok,
    eval_dataset=val_tok,
    data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True),
    tokenizer=tokenizer,
)

t0 = time.time()
trainer.train()
dt = (time.time() - t0) / 60
print(f"  ✓ Entraînement terminé en {dt:.1f} min")

# Sauvegarder
final_path = '/kaggle/working/t5_gsm8k_final'
model.save_pretrained(final_path)
tokenizer.save_pretrained(final_path)
print(f"  ✓ Modèle sauvegardé : {final_path}")


# ═══════════════════════════════════════════════════════════════════════════
# CELLULE 6 : Évaluation complète
# ═══════════════════════════════════════════════════════════════════════════

print("\n📊 Évaluation du modèle entraîné...")

from peft import PeftModel
model.eval()
if torch.cuda.is_available():
    model = model.cuda()

def ops2seq(ops_text: str) -> list:
    OM = {'MUL': 'MULTIPLY', 'SUB': 'SUBTRACT', 'ADD': 'ADD',
          'DIV': 'DIVIDE', 'INIT': 'INIT'}
    ops = []
    for token in ops_text.replace('\n', ' ').split():
        token = token.strip()
        m = re.match(r'(INIT|MUL|SUB|ADD|DIV)\s*\(([^)]+)\)', token)
        if not m: continue
        op, val = m.group(1), m.group(2)
        try: val = float(val)
        except: continue
        mapped = OM.get(op)
        if not mapped: continue
        if mapped == 'INIT': ops.append({'op': 'INIT', 'value': val})
        elif mapped == 'MULTIPLY': ops.append({'op': 'MULTIPLY', 'multiplier': val})
        elif mapped == 'DIVIDE': ops.append({'op': 'DIVIDE', 'divisor': val})
        elif mapped == 'SUBTRACT': ops.append({'op': 'SUBTRACT', 'value': val})
        elif mapped == 'ADD': ops.append({'op': 'ADD', 'value': val})
    return ops

ok_model = 0
for item in test:
    exp = reponse_finale(item['answer'])
    if exp is None: continue
    inp = 'translate to operations: ' + item['question']
    inputs = tokenizer(inp, return_tensors='pt', max_length=384, truncation=True)
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=128, num_beams=2, early_stopping=True)
    pred = tokenizer.decode(out[0], skip_special_tokens=True)
    ops = ops2seq(pred)
    if not ops: continue
    try:
        got = decoder_trames(encoder_operations_v2(ops, True, True, False, True))
        if got is not None and abs(got - exp) < 1e-6:
            ok_model += 1
    except: continue

print(f"  Score T5 + codec ψ : {ok_model}/{len(test)} ({100*ok_model/len(test):.1f}%)")

# Rapport final
print(f"\n{'='*60}")
print(f"  RAPPORT FINAL")
print(f"{'='*60}")
print(f"  Annotations gold (codec ψ seul) : {ok_gold}/{len(test)} ({100*ok_gold/len(test):.1f}%)")
print(f"  T5 prédit + codec ψ             : {ok_model}/{len(test)} ({100*ok_model/len(test):.1f}%)")
print(f"  Dataset d'entraînement           : {len(exemples)} paires")
print(f"  Modèle                           : {final_path}")
print(f"{'='*60}")

# Sauvegarder les résultats
with open('/kaggle/working/results.json', 'w') as f:
    json.dump({'gold_score': ok_gold/len(test), 'model_score': ok_model/len(test),
               'train_size': len(exemples)}, f)