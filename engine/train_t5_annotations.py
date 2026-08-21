#!/usr/bin/env python3
"""
train_t5_annotations.py — Fine-tune T5-small sur (question → annotations gold)

Entraîne un T5-small à générer les annotations <<...>> directement depuis
la question. À l'inférence, les annotations sont parsées et exécutées par
le codec v2 pour produire la réponse finale.

Utilisation :
  python train_t5_annotations.py --train data/gsm8k_annotations_train.jsonl
  python train_t5_annotations.py --eval
"""

import sys, os, re, json, time, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parseur_annotations import anot2ops, reponse_finale
from codec_binding import encoder_operations_v2, decoder_trames


def preparer_dataset(train_path: str,
                     test_path: str = None,
                     val_split: float = 0.05) -> dict:
    """Charge et prépare le dataset pour l'entraînement."""
    import json
    from datasets import Dataset, DatasetDict
    
    with open(train_path, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f if line.strip()]
    print(f"  Dataset chargé : {len(data)} exemples")
    
    # Format pour T5
    for d in data:
        d['input_text'] = 'translate to annotations: ' + d['input']
        d['target_text'] = d['target']
    
    dataset = Dataset.from_list(data)
    split = dataset.train_test_split(test_size=val_split, seed=42)
    result = {'train': split['train'], 'validation': split['test']}
    
    if test_path:
        with open(test_path, 'r', encoding='utf-8') as f:
            test_data = [json.loads(line) for line in f if line.strip()]
        for d in test_data:
            d['input_text'] = 'translate to annotations: ' + d['input']
            d['target_text'] = d['target']
        result['test'] = Dataset.from_list(test_data)
    
    return result


def entrainer(
    dataset_path: str = 'data/gsm8k_annotations_train.jsonl',
    output_dir: str = 'data/t5_annotations',
    model_name: str = 'google/flan-t5-small',
    epochs: int = 3,
    batch_size: int = 2,
    lora_r: int = 8,
    max_length: int = 384,
    max_target_length: int = 256,
):
    """Fine-tune T5-small sur (question → annotations)."""
    import torch
    from transformers import (
        AutoTokenizer, AutoModelForSeq2SeqLM,
        TrainingArguments, Trainer, DataCollatorForSeq2Seq,
    )
    from peft import LoraConfig, get_peft_model, TaskType
    
    # Verrou mémoire
    torch.set_num_threads(1)
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    
    # Charger les données
    data = preparer_dataset(dataset_path)
    train_dataset = data['train']
    val_dataset = data['validation']
    print(f"  Train : {len(train_dataset)}, Validation : {len(val_dataset)}")
    
    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def tokenize(batch):
        inputs = tokenizer(
            batch['input_text'], max_length=max_length,
            truncation=True, padding=False)
        targets = tokenizer(
            batch['target_text'], max_length=max_target_length,
            truncation=True, padding=False)
        inputs['labels'] = targets['input_ids']
        return inputs
    
    train_dataset = train_dataset.map(tokenize, batched=True,
                                      remove_columns=train_dataset.column_names)
    val_dataset = val_dataset.map(tokenize, batched=True,
                                  remove_columns=val_dataset.column_names)
    
    # Modèle avec LoRA
    print(f"  Chargement du modèle {model_name}...")
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name, low_cpu_mem_usage=True)
    
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        r=lora_r,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q", "v"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    model = model.to('cpu')
    
    # Entraînement
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=3e-4,
        warmup_ratio=0.1,
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        fp16=False,
        report_to="none",
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True),
        tokenizer=tokenizer,
    )
    
    print(f"\n  Démarrage entraînement ({epochs} époques)...")
    t0 = time.time()
    trainer.train()
    print(f"  ✓ Entraînement terminé en {(time.time()-t0)/60:.1f} min")
    
    # Sauvegarder
    final_path = os.path.join(output_dir, 'final')
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)
    print(f"  ✓ Modèle sauvegardé : {final_path}")
    
    return final_path


def evaluer(
    model_path: str = 'data/t5_annotations/final',
    test_path: str = 'data/gsm8k_annotations_train.jsonl',
    use_gold: bool = False,
    verbose: bool = False,
):
    """Évalue le modèle : génère annotations → parse → codec → score."""
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from peft import PeftModel
    
    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    print(f"  Chargement du modèle depuis {model_path}...")
    base_model = AutoModelForSeq2SeqLM.from_pretrained(
        'google/flan-t5-small', low_cpu_mem_usage=True)
    model = PeftModel.from_pretrained(base_model, model_path)
    model = model.to('cpu')
    model.eval()
    
    # Données de test (GSM8K officiel)
    from datasets import load_dataset
    test = load_dataset('gsm8k', 'main')['test']
    
    ok = n = 0
    gsm8k_test = test
    for item in gsm8k_test:
        question = item['question']
        answer = item['answer']
        exp = reponse_finale(answer)
        if exp is None: continue
        n += 1
        
        if use_gold:
            # Utiliser les annotations gold (oracle)
            annotation_str = ' '.join('<<' + a + '>>'
                                      for a in re.findall(r'<<([^>]+)>>', answer))
        else:
            # Générer avec le modèle
            input_text = 'translate to annotations: ' + question
            inputs = tokenizer(input_text, return_tensors='pt',
                               max_length=384, truncation=True).to('cpu')
            output_ids = model.generate(
                **inputs, max_new_tokens=256,
                num_beams=2, early_stopping=True)
            annotation_str = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        # Parser et exécuter
        ops = anot2ops(annotation_str)
        if len(ops) == 0: continue
        try:
            got = decoder_trames(encoder_operations_v2(
                ops, True, True, False, True))
        except:
            continue
        good = got is not None and abs(got - exp) < 1e-6
        ok += good
        if verbose and not good and n < 10:
            print(f'  [E] pred={got} exp={exp}')
            print(f'      target={annotation_str[:100]}')
            print(f'      ops={[o["op"] for o in ops[:6]]}')
    
    print(f'\n  Score : {ok}/{n} ({100*ok/n:.1f}%)')
    return ok / n if n else 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', action='store_true', help='Entraîner')
    parser.add_argument('--eval', action='store_true', help='Évaluer')
    parser.add_argument('--gold', action='store_true', help='Évaluer avec gold (oracle)')
    parser.add_argument('--dataset', default='data/gsm8k_annotations_train.jsonl')
    parser.add_argument('--output', default='data/t5_annotations')
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--batch', type=int, default=2)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    
    if args.train:
        entrainer(
            dataset_path=args.dataset,
            output_dir=args.output,
            epochs=args.epochs,
            batch_size=args.batch,
        )
    
    if args.eval:
        evaluer(
            model_path=args.output + '/final',
            use_gold=args.gold,
            verbose=args.verbose,
        )