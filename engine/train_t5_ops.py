#!/usr/bin/env python3
"""
train_t5_ops.py — Fine-tune T5-small sur (question → ops du codec)

Cible : INIT(20) MUL(2) SUB(4) DIV(6) MUL(2)
→ directement exécutable par le codec, pas de parsing d'annotations.

Usage :
  python train_t5_ops.py --train --data data/gsm8k_ops_subset.jsonl --epochs 1
  python train_t5_ops.py --train --data data/gsm8k_ops_train.jsonl --epochs 5
  python train_t5_ops.py --eval --model data/t5_ops/final
"""

import sys, os, re, json, time, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codec_binding import encoder_operations_v2, decoder_trames


def ops2seq(ops_text: str) -> list:
    """Convertit la sortie du modèle en liste d'ops.
    Ex : 'INIT(20) MUL(2) SUB(4) DIV(6) MUL(2)' → liste d'opérations.
    """
    OM = {'MUL': 'MULTIPLY', 'SUB': 'SUBTRACT', 'ADD': 'ADD',
          'DIV': 'DIVIDE', 'INIT': 'INIT'}
    ops = []
    for token in ops_text.replace('\n', ' ').split():
        token = token.strip()
        m = re.match(r'(INIT|MUL|SUB|ADD|DIV)\s*\(([^)]+)\)', token)
        if not m:
            continue
        op, val = m.group(1), m.group(2)
        try:
            val = float(val)
        except ValueError:
            continue
        mapped = OM.get(op)
        if not mapped:
            continue
        if mapped == 'INIT':
            ops.append({'op': 'INIT', 'value': val})
        elif mapped == 'MULTIPLY':
            ops.append({'op': 'MULTIPLY', 'multiplier': val})
        elif mapped == 'DIVIDE':
            ops.append({'op': 'DIVIDE', 'divisor': val})
        elif mapped == 'SUBTRACT':
            ops.append({'op': 'SUBTRACT', 'value': val})
        elif mapped == 'ADD':
            ops.append({'op': 'ADD', 'value': val})
    return ops


def charger_ops_dataset(data_path: str, val_split: float = 0.05):
    """Charge et convertit le dataset (question → target ops)."""
    from datasets import Dataset
    with open(data_path, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f if line.strip()]
    for d in data:
        d['input_text'] = 'translate to operations: ' + d['input']
        d['target_text'] = d['target']
    ds = Dataset.from_list(data)
    if val_split:
        split = ds.train_test_split(test_size=val_split, seed=42)
        return split['train'], split['test']
    return ds, None


def entrainer(
    data_path: str,
    output_dir: str = 'data/t5_ops',
    model_name: str = 'google/flan-t5-small',
    epochs: int = 3,
    batch_size: int = 2,
    lora_r: int = 8,
    max_length: int = 384,
):
    import torch
    from transformers import (
        AutoTokenizer, AutoModelForSeq2SeqLM,
        TrainingArguments, Trainer, DataCollatorForSeq2Seq,
    )
    from peft import LoraConfig, get_peft_model, TaskType
    
    torch.set_num_threads(1)
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    
    train_ds, val_ds = charger_ops_dataset(data_path)
    print(f"  Train : {len(train_ds)}", end="")
    if val_ds:
        print(f", Validation : {len(val_ds)}", end="")
    print()
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def tokenize(batch):
        inputs = tokenizer(batch['input_text'], max_length=max_length,
                           truncation=True, padding=False)
        targets = tokenizer(batch['target_text'], max_length=128,
                            truncation=True, padding=False)
        inputs['labels'] = targets['input_ids']
        return inputs
    
    cols = train_ds.column_names
    train_ds = train_ds.map(tokenize, batched=True, remove_columns=cols)
    if val_ds:
        val_ds = val_ds.map(tokenize, batched=True, remove_columns=cols)
    
    print(f"  Chargement du modèle {model_name}...")
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name,
                                                  low_cpu_mem_usage=True)
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        r=lora_r, lora_alpha=32, lora_dropout=0.1,
        target_modules=["q", "v"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    eval_kw = {}
    if val_ds:
        eval_kw = {'eval_strategy': 'epoch',
                   'load_best_model_at_end': True,
                   'metric_for_best_model': 'eval_loss'}
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=3e-4,
        warmup_ratio=0.1,
        logging_steps=50,
        save_strategy='epoch',
        fp16=False,
        report_to='none',
        dataloader_num_workers=0,
        remove_unused_columns=False,
        **eval_kw,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True),
        tokenizer=tokenizer,
    )
    
    print(f"\n  Démarrage ({epochs} époques, batch eff.={batch_size*4})...")
    t0 = time.time()
    trainer.train()
    dt = (time.time() - t0) / 60
    print(f"  ✓ Terminé en {dt:.1f} min")
    
    final_path = os.path.join(output_dir, 'final')
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)
    print(f"  ✓ Modèle : {final_path}")
    return final_path


def evaluer(
    model_path: str,
    model_name: str = 'google/flan-t5-small',
    sample: int = 0,
    verbose: bool = False,
):
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from peft import PeftModel
    from datasets import load_dataset
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    base = AutoModelForSeq2SeqLM.from_pretrained(model_name,
                                                 low_cpu_mem_usage=True)
    model = PeftModel.from_pretrained(base, model_path)
    model.eval()
    
    test = load_dataset('gsm8k', 'main')['test']
    if sample > 0 and sample < len(test):
        indices = list(range(0, len(test), len(test) // sample))
        test_sub = [test[i] for i in indices[:sample]]
    else:
        test_sub = test
    
    ok = n = 0
    for item in test_sub:
        answer = item['answer']
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', answer)
        exp = float(m.group(1)) if m else None
        if exp is None:
            continue
        n += 1
        
        inp = 'translate to operations: ' + item['question']
        inputs = tokenizer(inp, return_tensors='pt', max_length=384,
                           truncation=True)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=128,
                                 num_beams=2, early_stopping=True)
        pred = tokenizer.decode(out[0], skip_special_tokens=True)
        
        ops = ops2seq(pred)
        if not ops:
            if verbose:
                print(f'  ❌ génération invalide: {pred[:80]}')
            continue
        try:
            got = decoder_trames(encoder_operations_v2(
                ops, True, True, False, True))
        except Exception as e:
            if verbose:
                print(f'  ❌ codec error: {e}')
            continue
        good = got is not None and abs(got - exp) < 1e-6
        ok += good
        if verbose and not good:
            print(f'  ❌ got={got} exp={exp} | pred={pred[:100]}')
    
    print(f'\n  Score : {ok}/{n} ({100*ok/n:.1f}%)')
    return ok / n if n else 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', action='store_true')
    parser.add_argument('--eval', action='store_true')
    parser.add_argument('--data', default='data/gsm8k_ops_train.jsonl')
    parser.add_argument('--model', default='data/t5_ops/final')
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--batch', type=int, default=2)
    parser.add_argument('--sample', type=int, default=0,
                        help="Nb d'échantillons pour l'éval (0=tout)")
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    
    if args.train:
        entrainer(
            data_path=args.data,
            output_dir=args.model.replace('/final', ''),
            epochs=args.epochs,
            batch_size=args.batch,
        )
    if args.eval:
        evaluer(
            model_path=args.model,
            sample=args.sample,
            verbose=args.verbose,
        )