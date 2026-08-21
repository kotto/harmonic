#!/usr/bin/env python3
"""fine_tune_phraseur.py — LORe A PHRASEUR (SmolLM2-135M, CPU fp32 natif)
====================================================================
Entraîne le phraseur INTERNE spécialisé : un petit modèle qui n'a appris
QUE la tâche « <CORE>+style → phrase française auditable ».

POURQUOI 135M et pas 0,5B (mesures de cette machine) :
  · RAM totale 5,9 Go, ~1 Go libre : Qwen2.5-0.5B bf16 (1 Go) + ému-
    lation bf16 sur Zen 2 → 113 s/pas ; fp32 (2 Go) → pagination, OOM.
  · SmolLM2-135M fp32 = 540 Mo : tient EN RAM → vitesse native AVX2.
  · La tâche est ÉTROITE (gabarits de phrasage) : 135M suffit, et
    l'AUDIT + le fallback PhraseurInterne protègent la qualité.
  · Format d'invite COMPACT (~40 tokens) : <CORE>…<STYLE> — le modèle
    est spécialisé, pas besoin des 6 règles du prompt générique.

Usage :
  python fine_tune_phraseur.py                 # entraînement complet
  python fine_tune_phraseur.py --limit 32 --epochs 1   # fumée
"""
import argparse, json, os, random, sys, time

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

_ICI = os.path.dirname(os.path.abspath(__file__))
_DONNEES = os.path.join(_ICI, "data", "phraseur")
_SORTIE = os.path.join(_DONNEES, "lora")
_BASE = "HuggingFaceTB/SmolLM2-135M-Instruct"
MAX_LEN = 96
SEED = 1337


class DatasetPhraseur(Dataset):
    def __init__(self, chemin, tokenizer, max_len):
        self.entrees = []
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                e = json.loads(ligne)
                enc = tokenizer(e["prompt"], add_special_tokens=False)["input_ids"]
                dec = tokenizer(e["response"], add_special_tokens=False)["input_ids"]
                ids = enc + dec + [tokenizer.eos_token_id]
                ids = ids[:max_len]
                self.entrees.append({"input_ids": ids, "labels": ids,
                                     "n_prompt": len(enc)})

    def __len__(self):
        return len(self.entrees)

    def __getitem__(self, i):
        return self.entrees[i]


def coller(batch, tokenizer, max_len):
    ids, labels = [], []
    for e in batch:
        ids.append(e["input_ids"])
        labels.append([-100] * e["n_prompt"] + e["input_ids"][e["n_prompt"]:])
    L = min(max_len, max(len(x) for x in ids))
    ids_t = torch.full((len(batch), L), tokenizer.pad_token_id, dtype=torch.long)
    lab_t = torch.full((len(batch), L), -100, dtype=torch.long)
    for k, (i, l) in enumerate(zip(ids, labels)):
        ids_t[k, :len(i)] = torch.tensor(i[:L])
        lab_t[k, :len(l)] = torch.tensor(l[:L])
    return {"input_ids": ids_t, "labels": lab_t}


def evaluer(model, lote):
    model.eval()
    total, n = 0.0, 0
    with torch.no_grad():
        for lot in lote:
            out = model(input_ids=lot["input_ids"], labels=lot["labels"])
            total += out.loss.item() * len(lot["input_ids"])
            n += len(lot["input_ids"])
    model.train()
    return total / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="0 = tout (fumée sinon)")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--accum", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--r", type=int, default=16)
    ap.add_argument("--base", default=_BASE)
    ap.add_argument("--sortie", default=_SORTIE)
    args = ap.parse_args()

    torch.manual_seed(SEED)
    random.seed(SEED)
    torch.set_num_threads(12)
    t0 = time.time()

    print(f"⚙️  Base : {args.base} · LoRA r={args.r} · fp32 CPU · seed {SEED}",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    modele = AutoModelForCausalLM.from_pretrained(
        args.base, low_cpu_mem_usage=True)

    lora = LoraConfig(r=args.r, lora_alpha=32, lora_dropout=0.05,
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_up_proj", "down_proj"],
                      task_type="CAUSAL_LM")
    modele = get_peft_model(modele, lora)
    modele.print_trainable_parameters()

    ds_train = DatasetPhraseur(os.path.join(_DONNEES, "dataset_train.jsonl"),
                               tokenizer, MAX_LEN)
    ds_val = DatasetPhraseur(os.path.join(_DONNEES, "dataset_val.jsonl"),
                             tokenizer, MAX_LEN)
    if args.limit:
        ds_train.entrees = ds_train.entrees[:args.limit]
        ds_val.entrees = ds_val.entrees[:max(1, args.limit // 8)]
    dl_train = DataLoader(ds_train, batch_size=1, shuffle=True,
                          collate_fn=lambda b: coller(b, tokenizer, MAX_LEN))
    dl_val = DataLoader(ds_val, batch_size=4, shuffle=False,
                        collate_fn=lambda b: coller(b, tokenizer, MAX_LEN))
    dl_val_rapide = [lot for i, lot in enumerate(dl_val) if i < 10]
    print(f"  Train {len(ds_train)} · Val {len(ds_val)} · époques {args.epochs}",
          flush=True)

    opt = torch.optim.AdamW([p for p in modele.parameters() if p.requires_grad],
                            lr=args.lr, weight_decay=0.01)
    steps_tot = len(dl_train) // args.accum * args.epochs
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps_tot)
    grad_accum = 0
    meilleur = float("inf")

    print(f"  Démarrage — RAM libre {_libre()} Go", flush=True)
    for ep in range(1, args.epochs + 1):
        t_ep = time.time()
        for i, lot in enumerate(dl_train, 1):
            out = modele(input_ids=lot["input_ids"], labels=lot["labels"])
            out.loss.backward()
            grad_accum += 1
            if grad_accum >= args.accum:
                torch.nn.utils.clip_grad_norm_(
                    [p for p in modele.parameters() if p.requires_grad], 1.0)
                opt.step(); opt.zero_grad(set_to_none=True); sched.step()
                grad_accum = 0
            if i % 400 == 0 or i == len(dl_train):
                loss_v = evaluer(modele, dl_val_rapide)
                if loss_v < meilleur:
                    meilleur = loss_v
                    modele.save_pretrained(args.sortie + "_best")
                print(f"    épo {ep}/{args.epochs} · pas {i}/{len(dl_train)} · "
                      f"val {loss_v:.4f} · meilleur {meilleur:.4f} · "
                      f"libre {_libre()} Go", flush=True)
        print(f"  Époque {ep} terminée en {int(time.time()-t_ep)}s", flush=True)
    modele.save_pretrained(args.sortie)
    with open(os.path.join(args.sortie, "infos.json"), "w", encoding="utf-8") as f:
        json.dump({"base": args.base, "seed": SEED, "epochs": args.epochs,
                   "r": args.r, "exemples_train": len(ds_train),
                   "exemples_val": len(ds_val), "meilleure_val": meilleur,
                   "duree_s": int(time.time() - t0)}, f, indent=1)
    print(f"✅ Adapter sauvegardé : {args.sortie} (+ _best) · durée "
          f"{int((time.time()-t0)//60)} min", flush=True)


def _libre():
    try:
        import psutil
        return round(psutil.virtual_memory().available / 2**30, 1)
    except Exception:
        return -1


if __name__ == "__main__":
    main()
