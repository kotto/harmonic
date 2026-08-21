#!/usr/bin/env python3
"""Build combined transvertical+GSM8K notebook (no PEFT)."""
import json

with open('kaggle_gsm8k_nopeft.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

tv_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'source': [
        '# ── Génération transvertical + pré-entraînement ──\n',
        'print("🌍 Génération dataset transvertical...")\n',
        'import random; random.seed(42)\n',
        'DOMAINES = ["maths","droit","medecine","logique","eco","physique","quotidien"]\n',
        'NOMS = {"maths":["apples","books","dollars","candies","pencils","oranges","tickets"],\n',
        '  "droit":["damages","penalties","clauses","claims","fees","fines"],\n',
        '  "medecine":["milliliters","beats","milligrams","degrees","units","cells","drops","grams"],\n',
        '  "logique":["premises","inferences","propositions","cases","instances","arguments"],\n',
        '  "eco":["dollars","euros","shares","bonds","assets","revenues","costs"],\n',
        '  "physique":["meters","seconds","grams","liters","joules","watts","volts"],\n',
        '  "quotidien":["apples","cookies","cups","eggs","flowers","liters","tickets","books"]}\n',
        'MOTIFS = {\n',
        '  "INIT": {"maths":["has","starts with","buys","collects","receives","finds"],\n',
        '    "droit":["files","claims","demands","seeks","requests","receives"],\n',
        '    "medecine":["presents with","has","weighs","measures","shows","exhibits"],\n',
        '    "logique":["assumes","posits","states","defines","proposes","asserts"],\n',
        '    "eco":["invests","spends","budgets","allocates","earns","reports"],\n',
        '    "physique":["measures","records","observes","calculates","reads","detects"],\n',
        '    "quotidien":["has","buys","prepares","makes","bakes","cooks","grows"]},\n',
        '  "SUB": {"maths":["gives away","loses","spends","sells","removes","eats","breaks"],\n',
        '    "droit":["deducts","excludes","subtracts","waives","reduces by","lowers by"],\n',
        '    "medecine":["the fever drops by","the patient loses","the count decreases by","symptoms improve by"],\n',
        '    "logique":["is not the case","excludes","contradicts","negates","refutes","invalidates"],\n',
        '    "eco":["loses","spends","incurs","pays","depreciates by","writes off"],\n',
        '    "physique":["loses","dissipates","decays by","decreases by","cools by","slows by"],\n',
        '    "quotidien":["gives away","eats","drinks","uses","spends","breaks","loses"]},\n',
        '  "ADD": {"maths":["buys","gains","finds","receives","earns","collects","adds"],\n',
        '    "droit":["adds to the settlement","includes","compensates","awards additional","grants","imposes"],\n',
        '    "medecine":["gains weight","the count increases by","the heart rate rises by","symptoms worsen by"],\n',
        '    "logique":["and additionally","combined with","together with","in conjunction with","alongside"],\n',
        '    "eco":["earns","gains","receives","adds","accrues","generates revenue of","collects"],\n',
        '    "physique":["gains","absorbs","increases by","accumulates","stores","charges","heats up by"],\n',
        '    "quotidien":["buys","finds","receives","adds","picks up","gathers","collects","grows"]},\n',
        '  "MUL": {"maths":["each has","times","per","for every","twice","three times","each of"],\n',
        '    "droit":["for each violation","multiplied by the penalty","per article","for every instance","per defendant"],\n',
        '    "medecine":["per dose","for each kilogram","per day","per patient","per session","for every hour"],\n',
        '    "logique":["for every instance","in all cases","for each","applies to all","universally","for any"],\n',
        '    "eco":["times the rate","per unit","for each item","per share","each unit costs","per transaction"],\n',
        '    "physique":["per second","per meter","per kilogram","per hour","per unit volume","per degree"],\n',
        '    "quotidien":["each","per","for every","per person","each of the","every","apiece","doubles"]},\n',
        '  "DIV": {"maths":["split among","divided by","per person","each of","shared between","half of","quarter of"],\n',
        '    "droit":["divided among the heirs","shared between parties","apportioned","split between plaintiffs","per capita"],\n',
        '    "medecine":["per patient","divided in doses","per session","split into","divided by body weight","per kilogram"],\n',
        '    "logique":["applies to each","distributed over","divided among","per instance","for each case","half of","third of"],\n',
        '    "eco":["divided among","per share","per unit","split between","each investor gets","per partner","per capita"],\n',
        '    "physique":["per unit","per meter","per kilogram","divided by","per second","per hour","per degree"],\n',
        '    "quotidien":["split among","divided by","per person","each of","shared between","each gets","half of","quarter of"]},\n',
        '}\n',
        'GABARITS = [\n',
        '  ["INIT","A","SUBTRACT","B"],\n',
        '  ["INIT","A","ADD","B"],\n',
        '  ["INIT","A","MULTIPLY","B"],\n',
        '  ["INIT","A","DIVIDE","B"],\n',
        '  ["INIT","A","MULTIPLY","B","SUBTRACT","C"],\n',
        '  ["INIT","A","MULTIPLY","B","ADD","C"],\n',
        '  ["INIT","A","MULTIPLY","B","DIVIDE","C"],\n',
        '  ["INIT","A","MULTIPLY","B","ADD","C","DIVIDE","D"],\n',
        '  ["INIT","A","MULTIPLY","B","SUBTRACT","C","DIVIDE","D","MULTIPLY","E"],\n',
        '  ["INIT","A","MULTIPLY","B","INIT","C","SUBTRACT","D"],\n',
        '  ["INIT","A","MULTIPLY","B","INIT","C","MULTIPLY","D","ADD","E"],\n',
        ']\n',
        'OPNAMES = {"INIT":"INIT","SUBTRACT":"SUB","ADD":"ADD","MULTIPLY":"MUL","DIVIDE":"DIV"}\n',
        'tv_ex = []\n',
        'for _ in range(10000):\n',
        '  g = random.choice(GABARITS); d = random.choice(DOMAINES)\n',
        '  vals = {"A":random.randint(1,100),"B":random.randint(1,20),"C":random.randint(1,15),"D":random.randint(1,10),"E":random.randint(1,8)}\n',
        '  phrases = [random.choice(["In the","At the","During"])+" "+random.choice(["shop","market","lab","court","clinic","kitchen","field"])+","]\n',
        '  for i in range(0,len(g),2):\n',
        '    op, var = g[i], g[i+1]; v = vals[var]\n',
        '    if op=="INIT": m=random.choice(MOTIFS["INIT"][d]); n=random.choice(NOMS[d]); phrases.append(f"{m} {v} {n}")\n',
        '    elif op=="SUBTRACT": m=random.choice(MOTIFS["SUB"][d]); n=random.choice(NOMS[d]); phrases.append(f"{m} {v} {n}")\n',
        '    elif op=="ADD": m=random.choice(MOTIFS["ADD"][d]); n=random.choice(NOMS[d]); phrases.append(f"{m} {v} {n}")\n',
        '    elif op=="MULTIPLY": m=random.choice(MOTIFS["MUL"][d]); n=random.choice(NOMS[d]); phrases.append(f"{m} {v} {n}")\n',
        '    elif op=="DIVIDE": m=random.choice(MOTIFS["DIV"][d]); n=random.choice(NOMS[d]); phrases.append(f"{m} {v} {n}")\n',
        '  texte = ", ".join(phrases)+"."\n',
        '  cible = []\n',
        '  for i in range(0,len(g),2):\n',
        '    op, var = g[i], g[i+1]; cible.append(f"{OPNAMES[op]}({vals[var]})")\n',
        '  tv_ex.append({"input":texte,"target":" ".join(cible)})\n',
        'print(f"✓ {len(tv_ex)} exemples transvertiaux générés")\n',
        '\n',
        '# Pré-entraînement transvertical\n',
        'print("\\n🌍 1. Pré-entraînement transvertical (10k ex, 3 époques)...")\n',
        'tv_ds = Dataset.from_list(tv_ex)\n',
        'tv_split = tv_ds.train_test_split(test_size=0.05, seed=42)\n',
        'def tv_tok(b):\n',
        '  inp = tok(b["input"], max_length=256, truncation=True, padding=False)\n',
        '  tgt = tok(b["target"], max_length=64, truncation=True, padding=False)\n',
        '  inp["labels"] = tgt["input_ids"]; return inp\n',
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
        'tv_trainer = Trainer(model=model, args=tv_args, train_dataset=tv_train, eval_dataset=tv_val,\n',
        '  data_collator=DataCollatorForSeq2Seq(tok, model=model, padding=True), processing_class=tok)\n',
        'tv_trainer.train()\n',
        'print("✓ Pré-entraînement transvertical terminé")\n',
        'print("\\n📊 2. Fine-tuning sur GSM8K...")\n',
    ],
}

# Insérer après la cellule 5 (dataset) — index 5
nb['cells'].insert(6, tv_cell)

# Modifier la cellule d'entraînement (devenue 7)
train_cell = nb['cells'][7]
new_src = []
for line in train_cell['source']:
    if '🚀 Fine-tuning' in line:
        new_src.append('print("📊 2. Fine-tuning sur GSM8K (5 époques)...")\n')
    elif 'model = AutoModelForSeq2SeqLM.from_pretrained' in line:
        pass  # Skip — model already loaded from transvertical
    elif 'Params:' in line:
        pass  # Skip
    else:
        new_src.append(line)
train_cell['source'] = new_src

with open('kaggle_gsm8k_nopeft_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("✓ Notebook nopeft v2 créé : kaggle_gsm8k_nopeft_v2.ipynb")
print(f"  {len(nb['cells'])} cellules")