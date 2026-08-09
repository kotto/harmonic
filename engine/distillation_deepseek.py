#!/usr/bin/env python3
"""
distillation_deepseek.py — Distille DeepSeek vers un petit modèle local
========================================================================

Étape 1 : DeepSeek traduit les 1101 problèmes d'entraînement (une fois)
Étape 2 : Fine-tune T5-small sur les paires (problème → opérations)
Étape 3 : Le modèle distillé traduit LOCALEMENT, sans API

Le modèle appris est le TRADUCTEUR. Le noyau THU est l'EXÉCUTEUR.
"""

import sys, os, re, json, time, pickle
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════════════
# 1. GÉNÉRATION DU DATASET DE DISTILLATION (DeepSeek → opérations)
# ═══════════════════════════════════════════════════════════════════════════

PROMPT_DISTILL = """Tu es un traducteur de problèmes mathématiques. Traduis le problème en une séquence d'opérations. Tu ne fais AUCUN calcul. Tu ne remplaces PAS les nombres par leurs résultats. Tu traduis juste la structure.

OPÉRATIONS (une par ligne) :
  INIT(entity="nom", object="nom", value=N)
  ADD(entity="nom", value=N)
  SUBTRACT(entity="nom", value=N)
  MULTIPLY(entity="nom", multiplier=N)
  CROSS_MULT(container="nom", per_unit=N, product="nom")
  RATE(entity="nom", rate=N)
  DURATION(duration=N)
  DIVIDE(divisor=N)
  FRACTION(entity="nom", numerator=N, denominator=N)
  QUERY(entity="nom", object="nom")

RÈGLES :
- entity = qui possède (minuscules). "_" si pas de propriétaire.
- object = ce qui est compté (minuscules)
- N = le nombre EXACT du problème, jamais calculé
- FRACTION pour "2/5 of", "25% of", "half of"
- Ne mets PAS de commentaires. Une opération par ligne.

EXEMPLES :

Problème : "John has 5 apples. He buys 3 more. How many apples does he have?"
INIT(entity="john", object="apples", value=5)
ADD(entity="john", value=3)
QUERY(entity="john", object="apples")

Problème : "Walter bought 60 apples. He ate 2/5 of them and gave his sister 25% of the remaining. He sold the rest at $3 each. How much did he earn?"
INIT(entity="walter", object="apples", value=60)
FRACTION(entity="walter", numerator=2, denominator=5)
FRACTION(entity="walter", numerator=25, denominator=100)
MULTIPLY(entity="walter", multiplier=3)
QUERY(entity="walter", object="money")

Problème : "{problem}"
"""


def generer_dataset_distillation(train_problems, api_key, max_problems=None, out_path=None):
    """Génère le dataset de distillation via DeepSeek."""
    import requests

    if max_problems:
        train_problems = train_problems[:max_problems]

    dataset = []
    ok = 0
    t0 = time.time()

    for i, p in enumerate(train_problems):
        q = p['question']
        prompt = PROMPT_DISTILL.replace('{problem}', q)

        try:
            resp = requests.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'},
                json={'model': 'deepseek-chat',
                      'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.0, 'max_tokens': 400},
                timeout=30)
            data = resp.json()
            if 'choices' in data:
                texte = data['choices'][0]['message']['content'].strip()
                # Nettoyer les commentaires HTML
                texte = re.sub(r'<!--.*?-->', '', texte)
                texte = re.sub(r'\n\s*\n', '\n', texte)
                dataset.append({"input": q, "output": texte})
                ok += 1
            else:
                dataset.append({"input": q, "output": ""})
        except Exception as e:
            print(f"  ⚠ [{i+1}] {e}")
            dataset.append({"input": q, "output": ""})

        if (i+1) % 25 == 0:
            elapsed = time.time() - t0
            eta = (elapsed / (i+1)) * (len(train_problems) - i - 1)
            print(f"  {i+1:>4d}/{len(train_problems)} — {ok} OK — {elapsed:.0f}s, ~{eta:.0f}s restantes")

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f"  ✓ Sauvegardé : {out_path}")

    print(f"  ✓ {ok}/{len(train_problems)} traductions")
    return dataset


# ═══════════════════════════════════════════════════════════════════════════
# 2. FINE-TUNING T5-SMALL SUR LE DATASET DISTILLÉ
# ═══════════════════════════════════════════════════════════════════════════

def entrainer_t5_distille(dataset_path, output_dir="data/t5_distilled",
                          epochs=4, batch_size=2):
    """
    Fine-tune T5-small sur le dataset de distillation.

    Le modèle apprend : problème → séquence d'opérations.
    """
    import torch
    from transformers import (
        AutoTokenizer, AutoModelForSeq2SeqLM,
        TrainingArguments, Trainer, DataCollatorForSeq2Seq,
    )
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, TaskType

    # Charger les données
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filtrer les entrées vides
    data = [d for d in data if d['output'].strip()]
    print(f"  Données : {len(data)} paires problème→opérations")

    # Tokenizer
    model_name = 'google/flan-t5-small'
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def preprocess(examples):
        inputs = ["translate to operations: " + t for t in examples["input"]]
        model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding=False)
        labels = tokenizer(text_target=examples["output"], max_length=256,
                          truncation=True, padding=False)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    # Dataset HuggingFace
    hf_dataset = Dataset.from_list(data)
    hf_dataset = hf_dataset.map(preprocess, batched=True,
                                remove_columns=hf_dataset.column_names)

    # Modèle avec LoRA
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM, r=8, lora_alpha=16,
        lora_dropout=0.1, target_modules=["q", "v"])
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Entraînement
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=3e-4,
        warmup_ratio=0.1,
        logging_steps=10,
        save_strategy="epoch",
        fp16=False,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=hf_dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True),
    )

    print(f"\n  Démarrage entraînement ({epochs} époques, batch effectif={batch_size*4})...")
    t0 = time.time()
    trainer.train()
    print(f"  ✓ Entraînement terminé en {(time.time()-t0)/60:.1f} min")

    # Sauvegarder
    final_path = os.path.join(output_dir, 'final')
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)
    print(f"  ✓ Modèle sauvegardé : {final_path}")

    return model, tokenizer


# ═══════════════════════════════════════════════════════════════════════════
# 3. INFÉRENCE AVEC LE MODÈLE DISTILLÉ
# ═══════════════════════════════════════════════════════════════════════════

class DistilledSolver:
    """Solveur utilisant le modèle distillé comme traducteur."""

    def __init__(self, model_path="data/t5_distilled/final"):
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        from peft import PeftModel

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        base = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small')
        self.model = PeftModel.from_pretrained(base, model_path)
        self.model.eval()

        from traducteur_deepseek import parser_operations, executer_operations
        self.parser = parser_operations
        self.executer = executer_operations

    def solve(self, problem):
        import torch
        inputs = self.tokenizer("translate to operations: " + problem,
                               return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=256,
                                         num_beams=3, early_stopping=True)
        texte = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        ops = self.parser(texte)
        if not ops:
            return None
        return self.executer(ops)


# ═══════════════════════════════════════════════════════════════════════════
# 4. MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--generate', type=int, default=0,
                   help='Générer le dataset avec N problèmes (via DeepSeek)')
    p.add_argument('--train', action='store_true',
                   help='Fine-tuner T5 sur le dataset distillé')
    p.add_argument('--test', action='store_true',
                   help='Tester le modèle distillé sur les 15 exemples')
    p.add_argument('--benchmark', type=int, default=0,
                   help='Benchmarker sur N problèmes')
    args = p.parse_args()

    # Charger l'API key
    from traducteur_deepseek import _load_api_key
    api_key = _load_api_key()

    if args.generate:
        from structure_retrieval import StructuredRetrieval
        sr = StructuredRetrieval()
        sr.split_and_index()
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'data/deepseek_distill_train.json')
        generer_dataset_distillation(sr._train_problems, api_key,
                                     max_problems=args.generate, out_path=out)

    elif args.train:
        dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'data/deepseek_distill_train.json')
        if not os.path.exists(dataset_path):
            print(f"⚠ Dataset non trouvé : {dataset_path}")
            print("  Lancer d'abord : python distillation_deepseek.py --generate 100")
        else:
            entrainer_t5_distille(dataset_path)

    elif args.test:
        _SAMPLES = [
            ("John has 5 apples. He buys 3 more. How many apples does he have?", 8.0),
            ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6.0),
            ("There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?", 30.0),
            ("John has 5 apples. Mary has 3 times as many. How many apples does Mary have?", 15.0),
            ("James earns 20 dollars per hour. He works 8 hours. How much does he earn?", 160.0),
        ]
        print("═══ TEST MODÈLE DISTILLÉ ═══")
        solver = DistilledSolver()
        ok = 0
        for q, expected in _SAMPLES:
            result = solver.solve(q)
            good = result is not None and abs(result - expected) < 1e-6
            ok += good
            print(f"  {'✅' if good else '❌'} {q[:52]:<54} → {result} ({expected})")
        print(f"\n  SCORE : {ok}/{len(_SAMPLES)}")

    elif args.benchmark:
        from structure_retrieval import StructuredRetrieval
        sr = StructuredRetrieval()
        sr.split_and_index()
        test = sr._test_problems[:args.benchmark]
        solver = DistilledSolver()
        correct, no_sol, total = 0, 0, len(test)
        times = []
        print(f"═══ BENCHMARK MODÈLE DISTILLÉ ({total} problèmes) ═══")
        for i, prob in enumerate(test):
            q = prob['question']
            m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', prob['answer'])
            expected = float(m.group(1)) if m else None
            t0 = time.time()
            result = solver.solve(q)
            dt = (time.time()-t0)*1000
            times.append(dt)
            if result is None: no_sol += 1
            elif expected and abs(result-expected) < 1e-6: correct += 1
            if (i+1) % 25 == 0:
                print(f"  {i+1:>4d}/{total} — {correct}/{i+1} ({100*correct/(i+1):.1f}%)")
        acc = 100*correct/total if total > 0 else 0
        print(f"\n═══ RÉSULTATS ═══")
        print(f"  Accuracy : {acc:.1f}% ({correct}/{total})")
        print(f"  Sans sol.: {no_sol}")
        print(f"  Temps    : {np.mean(times):.1f} ms")

    else:
        print("═══ DISTILLATION DEEPSEEK → T5 ═══")
        print("Usage :")
        print("  python distillation_deepseek.py --generate 100  # Générer dataset")
        print("  python distillation_deepseek.py --train         # Fine-tuner T5")
        print("  python distillation_deepseek.py --test          # Tester")
        print("  python distillation_deepseek.py --benchmark 200 # Benchmark")
