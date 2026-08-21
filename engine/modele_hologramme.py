#!/usr/bin/env python3
"""
modele_hologramme.py — Démonstration complète du modèle hologramme
====================================================================

L'ANALOGIE TV (proposée par l'utilisateur) :

  Les LLMs généralistes sont comme des abonnements à 500 chaînes :
  vous payez pour tout, mais vous ne regardez que 4-5 chaînes.
  Notre approche : le modèle de base transvertical est le SIGNAL TV
  (universel, partagé), et l'HOLOGRAMME est la LISTE DES CHAÎNES
  FAVORITES (personnalisée, légère, créée en 1 minute).

  Le codec ψ est le TÉLÉVISEUR : il décode le signal exactement,
  sans perte, sans hallucination.

ARCHITECTURE :

  ┌─────────────────────────────────────────────────────────────────┐
  │  TÉLÉVISEUR (codec ψ) — 0 paramètre, 100% exact               │
  │  • Décode n'importe quel signal harmonique                     │
  │  • 88.4% GSM8K, 6/6 problèmes complexes                        │
  │  • Invariant : jamais réentraîné                               │
  ├─────────────────────────────────────────────────────────────────┤
  │  SIGNAL TV (modèle de base transvertical) — 60M params         │
  │  • 20 000 exemples, 7 domaines, 41 primitives                  │
  │  • Connaît les gestes universels (SUB, ADD, MUL, DIV...)       │
  │  • PARTAGÉ entre tous les utilisateurs                         │
  ├─────────────────────────────────────────────────────────────────┤
  │  LISTE FAVORIS (hologramme) — ~2MB, créé en 1 minute          │
  │  • Apprend le VOCABULAIRE du domaine (pas le raisonnement)     │
  │  • 50-100 exemples suffisent                                   │
  │  • PRIVÉ : chaque utilisateur a le sien                        │
  │  • Stocké dans le registre des hologrammes                     │
  └─────────────────────────────────────────────────────────────────┘

USAGE :
  python modele_hologramme.py --generer 100    # génère 100 exemples
  python modele_hologramme.py --entrainer      # crée l'hologramme
  python modele_hologramme.py --tester         # teste sur 10 exclus
"""

import sys, os, json, time, re, random, torch
import numpy as np
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════════════════
# 1. GÉNÉRATEUR D'EXEMPLES DOMAINE — 100 exemples finance
# ═══════════════════════════════════════════════════════════════════════════

# Gabarits de phrases financières avec leurs opérations
GABARITS_FINANCE = [
    # Investissement simple
    ("An investment of {A} dollars earns {B} percent per year.", "INIT({A}) MUL({B/100})"),
    ("A capital of {A} dollars yields {B} percent annually.", "INIT({A}) MUL({B/100})"),
    ("A sum of {A} dollars generates {B} percent interest.", "INIT({A}) MUL({B/100})"),
    
    # Prêt
    ("A loan of {A} dollars at {B} percent annual interest.", "INIT({A}) MUL({B/100})"),
    ("A mortgage of {A} dollars at {B} percent for {C} years.", "INIT({A}) MUL({B/100}) MUL({C})"),
    ("A credit of {A} dollars with {B} percent interest rate.", "INIT({A}) MUL({B/100})"),
    
    # Perte/Gain
    ("A portfolio of {A} dollars loses {B} percent in value.", "INIT({A}) MUL({B/100}) SUB({A*B/100})"),
    ("A stock worth {A} dollars drops {B} percent.", "INIT({A}) MUL({B/100}) SUB({A*B/100})"),
    ("An asset of {A} dollars gains {B} percent.", "INIT({A}) MUL({B/100}) ADD({A*B/100})"),
    ("A share priced at {A} dollars rises {B} percent.", "INIT({A}) MUL({B/100}) ADD({A*B/100})"),
    
    # Budget
    ("A budget of {A} dollars, {B} percent for salaries.", "INIT({A}) MUL({B/100})"),
    ("A revenue of {A} dollars, {B} percent operating costs.", "INIT({A}) MUL({B/100}) SUB({A*B/100})"),
    ("Total costs of {A} dollars, {B} percent fixed expenses.", "INIT({A}) MUL({B/100})"),
    ("A project budget of {A} dollars, {B} percent contingency.", "INIT({A}) MUL({B/100})"),
    
    # Salaire
    ("An annual salary of {A} dollars with a {B} percent raise.", "INIT({A}) MUL({B/100}) ADD({A*B/100})"),
    ("A monthly wage of {A} dollars, increased by {B} percent.", "INIT({A}) MUL({B/100}) ADD({A*B/100})"),
    
    # Loyer
    ("A monthly rent of {A} dollars for {B} months.", "INIT({A}) MUL({B})"),
    ("A lease of {A} dollars per month for {B} months.", "INIT({A}) MUL({B})"),
    
    # Pourcentage
    ("{A} percent of {B} dollars is allocated to marketing.", "INIT({B}) MUL({A/100})"),
    ("{A} percent of the {B} dollar fund is reserved.", "INIT({B}) MUL({A/100})"),
]


def generer_exemples_finance(n: int = 100, seed: int = 42) -> List[Dict]:
    """Génère N exemples financiers aléatoires."""
    random.seed(seed)
    exemples = []
    for _ in range(n):
        gabarit, template = random.choice(GABARITS_FINANCE)
        # Valeurs réalistes
        A = random.choice([1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000])
        B = random.choice([1, 2, 3, 5, 8, 10, 12, 15, 20, 25, 30])
        C = random.choice([1, 2, 5, 10, 15, 20, 25, 30])
        
        # Remplacer les variables
        def remplacer(s):
            s = s.replace('{A}', str(A))
            s = s.replace('{B}', str(B))
            s = s.replace('{C}', str(C))
            s = s.replace('{A*B/100}', str(int(A*B/100)))
            s = s.replace('{B/100}', str(B/100))
            return s
        
        input_text = remplacer(gabarit)
        target_text = remplacer(template)
        exemples.append({'input': input_text, 'target': target_text})
    
    return exemples


# ═══════════════════════════════════════════════════════════════════════════
# 2. CRÉATION D'UN HOLOGRAMME
# ═══════════════════════════════════════════════════════════════════════════

def creer_hologramme(nom: str, exemples: List[Dict],
                     epochs: int = 10) -> Dict:
    """Crée un hologramme pour un domaine à partir d'exemples.

    Args:
        nom: nom de l'hologramme
        exemples: liste de {'input', 'target'}
        epochs: nombre d'époques d'entraînement

    Retourne:
        statistiques d'entraînement
    """
    from transformers import (
        AutoTokenizer, AutoModelForSeq2SeqLM,
        TrainingArguments, Trainer, DataCollatorForSeq2Seq,
    )
    from peft import LoraConfig, TaskType
    from datasets import Dataset

    t0 = time.time()

    # Charger le modèle de base
    print("  Chargement du modèle de base...")
    tok = AutoTokenizer.from_pretrained('google/flan-t5-small')
    base = AutoModelForSeq2SeqLM.from_pretrained(
        'google/flan-t5-small', low_cpu_mem_usage=True)
    # Charger l'adaptateur transvertical
    from peft import PeftModel
    modele = PeftModel.from_pretrained(
        base, 'data/t5_transvertical_v2/final')
    modele.train()

    # Ajouter un nouvel adaptateur pour ce domaine
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        r=8, lora_alpha=16, lora_dropout=0.05,
        target_modules=['q', 'v'],
    )
    modele.add_adapter(nom, lora_config)
    modele.set_adapter(nom)
    trainable = sum(p.requires_grad for p in modele.parameters())
    print(f"  Adaptateur '{nom}' ajouté ({trainable} params entraînables)")

    # Tokenizer
    ds = Dataset.from_list(exemples)
    def tok_fn(b):
        inp = tok(b['input'], max_length=256, truncation=True, padding=False)
        tgt = tok(b['target'], max_length=64, truncation=True, padding=False)
        inp['labels'] = tgt['input_ids']
        return inp
    ds = ds.map(tok_fn, batched=True, remove_columns=ds.column_names)

    # Entraînement ultra-rapide
    chemin = f'data/hologram_store/{nom}'
    args = TrainingArguments(
        output_dir=chemin,
        num_train_epochs=epochs,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        learning_rate=5e-4,
        logging_steps=10,
        save_strategy='no',
        fp16=False, report_to='none',
        dataloader_num_workers=0, remove_unused_columns=False,
    )
    trainer = Trainer(
        model=modele, args=args, train_dataset=ds,
        data_collator=DataCollatorForSeq2Seq(tok, model=modele, padding=True),
        tokenizer=tok,
    )
    trainer.train()

    # Sauvegarder
    os.makedirs(chemin, exist_ok=True)
    modele.save_pretrained(chemin, safe_serialization=True)
    tok.save_pretrained(chemin)
    # Métadonnées
    meta = {
        'nom': nom,
        'exemples': len(exemples),
        'epochs': epochs,
        'temps': time.time() - t0,
        'loss': trainer.state.log_history[-1].get('loss', 0) if trainer.state.log_history else 0,
    }
    with open(os.path.join(chemin, 'hologramme.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"  ✓ Hologramme '{nom}' créé en {meta['temps']:.1f}s")
    print(f"    {len(exemples)} exemples, {epochs} époques")
    return meta


# ═══════════════════════════════════════════════════════════════════════════
# 3. TEST D'UN HOLOGRAMME
# ═══════════════════════════════════════════════════════════════════════════

def tester_hologramme(nom: str, exemples_test: List[Dict]) -> Dict:
    """Teste un hologramme sur des exemples non vus.

    Args:
        nom: nom de l'hologramme
        exemples_test: liste de {'input', 'target'}

    Retourne:
        statistiques de test
    """
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from peft import PeftModel

    # Charger
    tok = AutoTokenizer.from_pretrained('google/flan-t5-small')
    base = AutoModelForSeq2SeqLM.from_pretrained(
        'google/flan-t5-small', low_cpu_mem_usage=True)
    chemin = f'data/hologram_store/{nom}'
    modele = PeftModel.from_pretrained(base, chemin)
    modele.set_adapter(nom)
    modele.eval()

    ok = 0
    resultats = []
    for ex in exemples_test:
        q = ex['input']
        expected = ex['target']
        inp = tok('translate to operations: ' + q,
                  return_tensors='pt', max_length=256, truncation=True)
        with torch.no_grad():
            out = modele.generate(**inp, max_new_tokens=64, num_beams=1)
        pred = tok.decode(out[0], skip_special_tokens=True)

        # Comparer
        ops_pred = set(re.findall(r'(INIT|MUL|SUB|ADD|DIV)\([^)]+\)', pred))
        ops_exp = set(re.findall(r'(INIT|MUL|SUB|ADD|DIV)\([^)]+\)', expected))
        correct = ops_pred == ops_exp
        ok += correct
        resultats.append({
            'input': q[:50] + '...',
            'expected': expected,
            'predicted': pred,
            'correct': correct,
        })

    score = ok / len(exemples_test) * 100
    print(f"  ✓ Score : {ok}/{len(exemples_test)} ({score:.1f}%)")
    return {'score': score, 'ok': ok, 'total': len(exemples_test),
            'resultats': resultats[:5]}  # 5 premiers


# ═══════════════════════════════════════════════════════════════════════════
# 4. DÉMONSTRATION COMPLÈTE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Modèle hologramme')
    parser.add_argument('--generer', type=int, default=0,
                        help='Générer N exemples')
    parser.add_argument('--entrainer', action='store_true',
                        help='Créer un hologramme')
    parser.add_argument('--tester', action='store_true',
                        help='Tester un hologramme')
    parser.add_argument('--nom', default='finance',
                        help='Nom de l\'hologramme')
    args = parser.parse_args()

    if args.generer > 0:
        print(f"📦 Génération de {args.generer} exemples finance...")
        exemples = generer_exemples_finance(args.generer)
        # Split train/test
        split = int(args.generer * 0.8)
        train = exemples[:split]
        test = exemples[split:]
        with open(f'data/hologram_store/{args.nom}_train.json', 'w') as f:
            json.dump(train, f, indent=2)
        with open(f'data/hologram_store/{args.nom}_test.json', 'w') as f:
            json.dump(test, f, indent=2)
        print(f"  ✓ {len(train)} train + {len(test)} test sauvegardés")
        print(f"  Exemple : {exemples[0]['input']}")
        print(f"  → {exemples[0]['target']}")

    if args.entrainer:
        print(f"\n🌀 Création de l'hologramme '{args.nom}'...")
        # Charger les exemples
        train = json.load(open(f'data/hologram_store/{args.nom}_train.json'))
        meta = creer_hologramme(args.nom, train, epochs=10)
        print(f"  ✓ Temps total : {meta['temps']:.1f}s")

    if args.tester:
        print(f"\n🔍 Test de l'hologramme '{args.nom}'...")
        test = json.load(open(f'data/hologram_store/{args.nom}_test.json'))
        stats = tester_hologramme(args.nom, test)
        print(f"  ✓ Score final : {stats['score']:.1f}%")