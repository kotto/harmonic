#!/usr/bin/env python3
"""Mise à jour du notebook Kaggle v2 avec transvertical."""
import json

with open('kaggle_gsm8k_pipeline.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

# Cellule transvertical à insérer après la cellule 3 (parser)
tv_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {'id': 'transvertical'},
    'source': [
        '# Cellule 4a : Générateur transvertical V2\n',
        'print("🌍 Génération du dataset transvertical (7 domaines, 15 gabarits)...")\n',
        'import random; random.seed(42)\n',
        'DOMAINES = ["maths","droit","medecine","logique","eco","physique","quotidien"]\n',
        'MOTIFS = {\n',
        '  "INIT": {"maths":["has","starts with","buys","collects","receives","finds","owns"],\n',
        '           "droit":["files","claims","demands","seeks","requests","receives","holds"],\n',
        '           "medecine":["presents with","has","weighs","measures","shows","exhibits"],\n',
        '           "logique":["assumes","posits","states","defines","proposes","asserts"],\n',
        '           "eco":["invests","spends","budgets","allocates","earns","reports","projects"],\n',
        '           "physique":["measures","records","observes","calculates","reads","detects"],\n',
        '           "quotidien":["has","buys","prepares","makes","bakes","cooks","grows"]},\n',
        '  "SUB": {"maths":["gives away","loses","spends","sells","removes","eats","breaks","drops","lends","donates"],\n',
        '          "droit":["deducts","excludes","subtracts","waives","reduces by","lowers by","decreases by"],\n',
        '          "medecine":["the fever drops by","the patient loses","the count decreases by","symptoms improve by","inflammation reduces by"],\n',
        '          "logique":["is not the case","excludes","contradicts","negates","refutes","invalidates","falsifies"],\n',
        '          "eco":["loses","spends","incurs","pays","depreciates by","writes off","suffers a loss of"],\n',
        '          "physique":["loses","dissipates","decays by","decreases by","cools by","slows by","drops by"],\n',
        '          "quotidien":["gives away","eats","drinks","uses","spends","breaks","loses","forgets","burns"]},\n',
        '  "ADD": {"maths":["buys","gains","finds","receives","earns","collects","adds","gets","acquires"],\n',
        '          "droit":["adds to the settlement","includes","compensates","awards additional","grants","imposes","adds a penalty of"],\n',
        '          "medecine":["gains weight","the count increases by","the heart rate rises by","symptoms worsen by","fever increases by"],\n',
        '          "logique":["and additionally","combined with","together with","in conjunction with","alongside","furthermore","moreover"],\n',
        '          "eco":["earns","gains","receives","adds","accrues","generates revenue of","collects","accumulates"],\n',
        '          "physique":["gains","absorbs","increases by","accumulates","stores","charges","heats up by","speeds up by"],\n',
        '          "quotidien":["buys","finds","receives","adds","picks up","gathers","collects","grows","harvests"]},\n',
        '  "MUL": {"maths":["each has","times","per","for every","twice","three times","each of the","every","apiece","doubles"],\n',
        '          "droit":["for each violation","multiplied by the penalty","per article","for every instance","per defendant","each offense carries"],\n',
        '          "medecine":["per dose","for each kilogram","per day","per patient","per session","for every hour","per treatment"],\n',
        '          "logique":["for every instance","in all cases","for each","applies to all","universally","for any","per case"],\n',
        '          "eco":["times the rate","per unit","for each item","per share","each unit costs","per transaction","per customer"],\n',
        '          "physique":["per second","per meter","per kilogram","per hour","per unit volume","per degree","per mole"],\n',
        '          "quotidien":["each","per","for every","per person","each of the","every","apiece","doubles","triples"]},\n',
        '  "DIV": {"maths":["split among","divided by","per person","each of","shared between","divided equally","half of","quarter of","percent of"],\n',
        '          "droit":["divided among the heirs","shared between parties","apportioned","split between plaintiffs","divided equally among","per capita"],\n',
        '          "medecine":["per patient","divided in doses","per session","split into","divided by body weight","per kilogram","per administration"],\n',
        '          "logique":["applies to each","distributed over","divided among","per instance","for each case","half of","third of","per proposition"],\n',
        '          "eco":["divided among","per share","per unit","split between","each investor gets","per partner","per capita"],\n',
        '          "physique":["per unit","per meter","per kilogram","divided by","per second","per hour","per degree","per liter"],\n',
        '          "quotidien":["split among","divided by","per person","each of","shared between","each gets","half of","quarter of","per"]},\n',
        '}\n',
        'NOMS = {\n',
        '  "maths":["apples","books","dollars","candies","pencils","oranges","tickets","cards"],\n',
        '  "droit":["damages","penalties","clauses","claims","fees","fines","settlements","compensations"],\n',
        '  "medecine":["milliliters","beats","milligrams","degrees","units","cells","drops","liters","grams","doses"],\n',
        '  "logique":["premises","inferences","propositions","cases","instances","arguments","deductions","conclusions"],\n',
        '  "eco":["dollars","euros","shares","bonds","assets","liabilities","revenues","costs","profits","dividends"],\n',
        '  "physique":["meters","seconds","grams","liters","joules","watts","volts","amperes","newtons","pascals"],\n',
        '  "quotidien":["apples","cookies","cups","eggs","flowers","liters","meters","tickets","books","slices"],\n',
        '}\n',
        'GABARITS = [\n',
        '  [["INIT","A"],["SUBTRACT","B"]],\n',
        '  [["INIT","A"],["ADD","B"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"]],\n',
        '  [["INIT","A"],["DIVIDE","B"]],\n',
        '  [["INIT","A"],["ADD","B"],["SUBTRACT","C"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"],["ADD","C"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"],["SUBTRACT","C"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"],["ADD","C"],["DIVIDE","D"]],\n',
        '  [["INIT","A"],["SUBTRACT","B"],["MULTIPLY","C"],["SUBTRACT","D"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"],["DIVIDE","C"],["MULTIPLY","D"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"],["SUBTRACT","C"],["DIVIDE","D"],["MULTIPLY","E"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"],["INIT","C"],["SUBTRACT","D"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"],["INIT","C"],["MULTIPLY","D"],["ADD","E"]],\n',
        '  [["INIT","A"],["ADD","B"],["MULTIPLY","C"],["SUBTRACT","D"],["DIVIDE","E"]],\n',
        '  [["INIT","A"],["MULTIPLY","B"],["ADD","C"],["MULTIPLY","D"],["SUBTRACT","E"],["DIVIDE","F"]],\n',
        ']\n',
        'OP_NAMES = {"INIT":"INIT","SUBTRACT":"SUB","ADD":"ADD","MULTIPLY":"MUL","DIVIDE":"DIV"}\n',
        'tv_exemples = []\n',
        'for _ in range(10000):\n',
        '  g = random.choice(GABARITS)\n',
        '  d = random.choice(DOMAINES)\n',
        '  vals = {"A":random.randint(1,100),"B":random.randint(1,20),"C":random.randint(1,15),"D":random.randint(1,10),"E":random.randint(1,8),"F":random.randint(1,6)}\n',
        '  phrases = [random.choice(["In the","At the","During"]) + " " + random.choice(["shop","market","office","lab","clinic","court","kitchen","field"]) + ","]\n',
        '  for op, var in g:\n',
        '    v = vals[var]\n',
        '    if op == "INIT":\n',
        '      m = random.choice(MOTIFS["INIT"][d]); n = random.choice(NOMS[d])\n',
        '      phrases.append(f"{m} {v} {n}")\n',
        '    elif op == "SUBTRACT":\n',
        '      m = random.choice(MOTIFS["SUB"][d]); n = random.choice(NOMS[d])\n',
        '      phrases.append(f"{m} {v} {n}")\n',
        '    elif op == "ADD":\n',
        '      m = random.choice(MOTIFS["ADD"][d]); n = random.choice(NOMS[d])\n',
        '      phrases.append(f"{m} {v} {n}")\n',
        '    elif op == "MULTIPLY":\n',
        '      m = random.choice(MOTIFS["MUL"][d]); n = random.choice(NOMS[d])\n',
        '      phrases.append(f"{m} {v} {n}")\n',
        '    elif op == "DIVIDE":\n',
        '      m = random.choice(MOTIFS["DIV"][d]); n = random.choice(NOMS[d])\n',
        '      phrases.append(f"{m} {v} {n}")\n',
        '  texte = ", ".join(phrases) + "."\n',
        '  cible = []\n',
        '  for op, var in g:\n',
        '    cible.append(f"{OP_NAMES[op]}({vals[var]})")\n',
        '  tv_exemples.append({"input": texte, "target": " ".join(cible)})\n',
        'with open("/kaggle/working/transvertical_train.jsonl","w") as f:\n',
        '  for ex in tv_exemples:\n',
        '    f.write(json.dumps(ex) + "\\n")\n',
        'print(f"  ✓ {len(tv_exemples)} exemples transvertiaux générés")\n',
    ],
}

# Insérer après la cellule 3 (parser) — index 3
nb['cells'].insert(4, tv_cell)

# Ajouter le pré-entraînement transvertical dans la cellule d'entraînement
# C'est maintenant la cellule 6 (après insertion)
train_idx = 6 if len(nb['cells']) > 6 else 5
train_cell = nb['cells'][train_idx]

# On ajoute le pré-entraînement AVANT l'entraînement GSM8K
pre_train = [
    '# ── Étape 1 : Pré-entraînement transvertical ──\n',
    'print("\\n🌍 Étape 1 : Pré-entraînement transvertical (10k ex, 7 domaines, 3 époques)...")\n',
    'from datasets import Dataset\n',
    'tv_ds = Dataset.from_list(tv_exemples)\n',
    'tv_split = tv_ds.train_test_split(test_size=0.05, seed=42)\n',
    'def tv_tok(batch):\n',
    '  inputs = tokenizer(batch["input"], max_length=256, truncation=True, padding=False)\n',
    '  targets = tokenizer(batch["target"], max_length=64, truncation=True, padding=False)\n',
    '  inputs["labels"] = targets["input_ids"]\n',
    '  return inputs\n',
    'cols = tv_split["train"].column_names\n',
    'tv_train = tv_split["train"].map(tv_tok, batched=True, remove_columns=cols)\n',
    'tv_val = tv_split["test"].map(tv_tok, batched=True, remove_columns=cols)\n',
    'tv_args = TrainingArguments(\n',
    '  output_dir="/kaggle/working/t5_tv",\n',
    '  num_train_epochs=3,\n',
    '  per_device_train_batch_size=16,\n',
    '  gradient_accumulation_steps=2,\n',
    '  learning_rate=3e-4, warmup_ratio=0.1,\n',
    '  logging_steps=50, eval_strategy="epoch", save_strategy="epoch",\n',
    '  load_best_model_at_end=True, fp16=True, report_to="none",\n',
    '  dataloader_num_workers=2, remove_unused_columns=False,\n',
    ')\n',
    'tv_trainer = Trainer(\n',
    '  model=model, args=tv_args,\n',
    '  train_dataset=tv_train, eval_dataset=tv_val,\n',
    '  data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True),\n',
    '  tokenizer=tokenizer,\n',
    ')\n',
    'tv_trainer.train()\n',
    'print("  ✓ Pré-entraînement transvertical terminé. Passage au GSM8K...")\n',
    'print("\\n📊 Étape 2 : Fine-tuning sur GSM8K...")\n',
]

# Remplacer le début de la cellule d'entraînement
new_source = []
replaced = False
for line in train_cell['source']:
    if not replaced and 'Entraînement' in line and 'Démarrage' not in line:
        new_source.extend(pre_train)
        replaced = True
    else:
        new_source.append(line)
train_cell['source'] = new_source

# Ajuster le nom de la variable 'exemples' pour éviter le conflit
# Dans la cellule 5 (dataset), les exemples sont dans 'exemples'
# Dans la cellule transvertical, ils sont dans 'tv_exemples' — OK

# Sauvegarder
with open('kaggle_gsm8k_pipeline_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("✓ Notebook v2 créé : kaggle_gsm8k_pipeline_v2.ipynb")
print(f"  {len(nb['cells'])} cellules")