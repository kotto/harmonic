#!/usr/bin/env python3
"""
kaggle_train_annotations.py — Entraînement T5-small sur annotations gold GSM8K
================================================================================

À exécuter sur Kaggle (GPU T4, ~30 min) :
  1. Uploader data/gsm8k_annotations_train.jsonl
  2. Lancer ce script
  3. Récupérer le modèle dans data/t5_annotations_kaggle/final

Usage :
  python kaggle_train_annotations.py --data gsm8k_annotations_train.jsonl
  python kaggle_train_annotations.py --eval --model data/t5_annotations_kaggle/final
"""

import sys, os, re, json, time, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def preparer_dataset(data_path: str, val_split: float = 0.05):
    from datasets import Dataset
    with open(data_path, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f if line.strip()]
    for d in data:
        d['input_text'] = 'translate to annotations: ' + d['input']
        d['target_text'] = d['target']
    ds = Dataset.from_list(data)
    split = ds.train_test_split(test_size=val_split, seed=42)
    return split['train'], split['test']


def entrainer(data_path: str, output_dir: str = 'data/t5_annotations_kaggle',
              model_name: str = 'google/flan-t5-small',
              epochs: int = 5, batch_size: int = 16, max_length: int = 384):
    """Fine-tune avec batch_size 16 sur GPU Kaggle."""
    import torch
    from transformers import (
        AutoTokenizer, AutoModelForSeq2SeqLM,
        TrainingArguments, Trainer, DataCollatorForSeq2Seq,
    )
    from peft import LoraConfig, get_peft_model, TaskType

    train_ds, val_ds = preparer_dataset(data_path)
    print(f"  Train : {len(train_ds)}, Validation : {len(val_ds)}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize(batch):
        inputs = tokenizer(batch['input_text'], max_length=max_length,
                           truncation=True, padding=False)
        targets = tokenizer(batch['target_text'], max_length=256,
                            truncation=True, padding=False)
        inputs['labels'] = targets['input_ids']
        return inputs

    train_ds = train_ds.map(tokenize, batched=True, remove_columns=train_ds.column_names)
    val_ds = val_ds.map(tokenize, batched=True, remove_columns=val_ds.column_names)

    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM, r=16, lora_alpha=32,
        lora_dropout=0.1, target_modules=["q", "v"])
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=2,
        learning_rate=3e-4,
        warmup_ratio=0.1,
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        fp16=True,
        report_to="none",
        dataloader_num_workers=2,
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True),
        tokenizer=tokenizer,
    )

    print(f"\n  Démarrage entraînement ({epochs} époques, batch eff.={batch_size*2})...")
    t0 = time.time()
    trainer.train()
    print(f"  ✓ Terminé en {(time.time()-t0)/60:.1f} min")

    final_path = os.path.join(output_dir, 'final')
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)
    print(f"  ✓ Modèle : {final_path}")
    return final_path


def evaluer(model_path: str, verbose: bool = False):
    """Évalue le modèle : génère annotations → parse → codec → score GSM8K."""
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from peft import PeftModel
    from datasets import load_dataset
    from parseur_annotations import anot2ops, reponse_finale
    from codec_binding import encoder_operations_v2, decoder_trames

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    base = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small',
                                                  low_cpu_mem_usage=True)
    model = PeftModel.from_pretrained(base, model_path)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()

    test = load_dataset('gsm8k', 'main')['test']
    ok = n = 0
    for item in test:
        exp = reponse_finale(item['answer'])
        if exp is None: continue
        n += 1
        inp = 'translate to annotations: ' + item['question']
        inputs = tokenizer(inp, return_tensors='pt', max_length=384, truncation=True)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=256,
                                 num_beams=2, early_stopping=True)
        pred = tokenizer.decode(out[0], skip_special_tokens=True)
        ops = anot2ops(pred)
        if not ops: continue
        try:
            got = decoder_trames(encoder_operations_v2(ops, True, True, False, True))
        except: continue
        good = got is not None and abs(got - exp) < 1e-6
        ok += good
        if verbose and not good and ok < 5:
            print(f'  ❌ pred={got} exp={exp}  généré={pred[:100]}')

    print(f'\n  Score : {ok}/{n} ({100*ok/n:.1f}%)')
    return ok / n if n else 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', action='store_true')
    parser.add_argument('--eval', action='store_true')
    parser.add_argument('--data', default='data/gsm8k_annotations_train.jsonl')
    parser.add_argument('--model', default='data/t5_annotations_kaggle/final')
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    if args.train:
        entrainer(args.data, epochs=args.epochs)
    if args.eval:
        evaluer(args.model, verbose=args.verbose)