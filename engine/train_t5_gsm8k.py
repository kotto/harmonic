#!/usr/bin/env python3
"""
train_t5_gsm8k.py - Fine-tuning T5-small sur GSM8K avec LoRA
=============================================================

Apprend le mapping: texte du probleme -> chaine d'operations.

Dataset: 1079 train / 191 val
Modele: google/flan-t5-small (80M params, LoRA ~300K trainable)
Duree estimee: ~30-45 min sur CPU

USAGE:
  python train_t5_gsm8k.py            # entrainement complet
  python train_t5_gsm8k.py --test     # test rapide du modele sauvegarde
"""

import sys, os, json, re, time
import numpy as np

# Verifier les dependances
try:
    import torch
    from transformers import (
        AutoTokenizer,
        AutoModelForSeq2SeqLM,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq,
        EarlyStoppingCallback,
    )
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, TaskType
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Installation des dependances...")
    os.system(f"{sys.executable} -m pip install transformers[torch] datasets peft accelerate -q")
    import torch
    from transformers import (
        AutoTokenizer, AutoModelForSeq2SeqLM, TrainingArguments, Trainer,
        DataCollatorForSeq2Seq, EarlyStoppingCallback,
    )
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, TaskType


# ============================================================
# 1. CHARGEMENT DES DONNEES
# ============================================================

def load_dataset(data_dir="data/t5_gsm8k"):
    """Charge les donnees d'entrainement et validation."""
    with open(os.path.join(data_dir, 'train.json'), encoding='utf-8') as f:
        train_data = json.load(f)
    with open(os.path.join(data_dir, 'val.json'), encoding='utf-8') as f:
        val_data = json.load(f)

    print(f"Train: {len(train_data)} exemples")
    print(f"Val:   {len(val_data)} exemples")

    # Afficher quelques exemples
    for i in range(min(3, len(train_data))):
        d = train_data[i]
        print(f"\n  Exemple {i+1}:")
        print(f"  Input  ({len(d['input'])} chars): {d['input'][:100]}...")
        print(f"  Output ({len(d['output'])} chars): {d['output'][:100]}")

    return train_data, val_data


# ============================================================
# 2. PREPARATION DU MODELE T5
# ============================================================

PREFIX = "extract operations: "


def preprocess_function(examples, tokenizer, max_input_length=512, max_output_length=128):
    """Tokenize les exemples pour T5."""
    inputs = [PREFIX + text for text in examples["input"]]
    model_inputs = tokenizer(
        inputs, max_length=max_input_length, truncation=True, padding=False)

    labels = tokenizer(
        text_target=examples["output"],
        max_length=max_output_length,
        truncation=True,
        padding=False,
    )

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


def create_model(model_name="google/flan-t5-small", lora_r=8):
    """Cree le modele T5 avec adaptateurs LoRA."""
    print(f"\nChargement du modele {model_name}...")
    t0 = time.time()

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # Configuration LoRA
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        r=lora_r,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=["q", "v"],  # modules d'attention de T5
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print(f"Modele charge en {time.time() - t0:.1f}s")
    return model, tokenizer


# ============================================================
# 3. ENTRAINEMENT
# ============================================================

def train(model, tokenizer, train_data, val_data, output_dir="data/t5_gsm8k_model",
          num_epochs=5, batch_size=2, lr=3e-4):
    """Fine-tuning du modele T5 avec LoRA."""

    # Preparer les datasets HuggingFace
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)

    # Tokenizer
    train_dataset = train_dataset.map(
        lambda x: preprocess_function(x, tokenizer),
        batched=True,
        remove_columns=train_dataset.column_names,
    )
    val_dataset = val_dataset.map(
        lambda x: preprocess_function(x, tokenizer),
        batched=True,
        remove_columns=val_dataset.column_names,
    )

    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        padding=True,
    )

    # Arguments d'entrainement
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4,  # batch effectif = 2*4 = 8
        learning_rate=lr,
        warmup_ratio=0.1,
        weight_decay=0.01,
        logging_dir=os.path.join(output_dir, 'logs'),
        logging_steps=20,
        eval_strategy="steps",
        eval_steps=100,
        save_strategy="steps",
        save_steps=200,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=False,  # CPU
        dataloader_num_workers=0,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    print(f"\nDemarrage de l'entrainement...")
    print(f"  Epoques: {num_epochs}")
    print(f"  Batch size effectif: {batch_size * 4}")
    print(f"  Steps par epoque: ~{len(train_dataset) // (batch_size * 4)}")
    print(f"  Duree estimee: ~30-60 min (CPU)")

    t0 = time.time()
    trainer.train()
    duration = time.time() - t0

    print(f"\nEntrainement termine en {duration/60:.1f} min")

    # Sauvegarder le modele final
    final_path = os.path.join(output_dir, 'final')
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)
    print(f"Modele sauvegarde dans {final_path}")

    # Evaluer
    metrics = trainer.evaluate()
    print(f"Perte finale eval: {metrics.get('eval_loss', 'N/A'):.4f}")

    return model, tokenizer, trainer


# ============================================================
# 4. INFERENCE
# ============================================================

def load_trained_model(model_path="data/t5_gsm8k_model/final",
                       base_model="google/flan-t5-small"):
    """Charge un modele T5 fine-tune."""
    from peft import PeftModel
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    base = AutoModelForSeq2SeqLM.from_pretrained(base_model)
    model = PeftModel.from_pretrained(base, model_path)
    model.eval()
    return model, tokenizer


def predict(model, tokenizer, question, max_length=128):
    """Predit la chaine d'operations pour un probleme."""
    input_text = PREFIX + question
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            num_beams=3,
            early_stopping=True,
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def evaluate_model(model, tokenizer, test_data, max_samples=None):
    """Evalue le modele sur des donnees de test."""
    correct = 0
    total = 0

    if max_samples:
        import random
        random.seed(42)
        test_data = random.sample(test_data, min(max_samples, len(test_data)))

    print(f"\nEvaluation sur {len(test_data)} exemples...")

    for i, d in enumerate(test_data):
        question = d['input']
        expected_chain = d['output']

        predicted = predict(model, tokenizer, question)

        # Extraire le dernier resultat de chaque chaine
        def last_number(chain):
            nums = re.findall(r'=\s*([\d.]+)', chain)
            return float(nums[-1]) if nums else None

        pred_val = last_number(predicted)
        exp_val = last_number(expected_chain)

        total += 1
        if pred_val is not None and exp_val is not None and abs(pred_val - exp_val) < 1e-6:
            correct += 1

        if (i + 1) % 25 == 0:
            acc = 100 * correct / (i + 1)
            print(f"  {i+1}/{len(test_data)} - {correct}/{i+1} ({acc:.1f}%)")

    accuracy = 100 * correct / total if total > 0 else 0
    print(f"\nAccuracy: {accuracy:.1f}% ({correct}/{total})")
    return accuracy


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', action='store_true', default=True,
                       help='Entrainer le modele')
    parser.add_argument('--test', action='store_true',
                       help='Tester le modele sauvegarde')
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--batch_size', type=int, default=2)
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--demo', action='store_true',
                       help='Demo rapide avec le modele sauvegarde')
    args = parser.parse_args()

    if args.demo:
        print("=== DEMO T5 GSM8K ===\n")
        model, tokenizer = load_trained_model()

        tests = [
            "John has 5 apples. He buys 3 more. How many apples does he have?",
            "Mary had 10 cookies. She ate 4. How many cookies does she have left?",
            "There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?",
            "James earns 20 dollars per hour. He works 8 hours. How much does he earn?",
        ]
        for q in tests:
            result = predict(model, tokenizer, q)
            print(f"Q: {q[:80]}...")
            print(f"R: {result}")
            print()

    elif args.test:
        print("=== TEST DU MODELE T5 SAUVEGARDE ===\n")
        model, tokenizer = load_trained_model()
        _, val_data = load_dataset()
        evaluate_model(model, tokenizer, val_data)

    elif args.train:
        print("=== FINE-TUNING T5-small SUR GSM8K ===\n")

        # Charger les donnees
        train_data, val_data = load_dataset()

        # Creer le modele
        model, tokenizer = create_model()

        # Entrainer
        model, tokenizer, trainer = train(
            model, tokenizer, train_data, val_data,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
        )

        # Tester
        print("\n=== TEST FINAL ===")
        evaluate_model(model, tokenizer, val_data)

        # Demo
        print("\n=== DEMO ===")
        tests = [
            "John has 5 apples. He buys 3 more. How many apples does he have?",
            "James earns 20 dollars per hour. He works 8 hours. How much does he earn?",
        ]
        for q in tests:
            result = predict(model, tokenizer, q)
            print(f"Q: {q}")
            print(f"R: {result}\n")
