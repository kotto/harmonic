#!/usr/bin/env python3
"""serveur_phraseur_ft.py — LE PHRASEUR FINE-TUNÉ EN SERVICE
============================================================
Micro-serveur HTTP local qui sert le phraseur spécialisé (SmolLM2-135M +
LoRA entraînée par fine_tune_phraseur.py) en inférence DÉTERMINISTE :
température 0, greedy, seed fixe → la même entrée donne toujours la même
sortie. Privé : aucune donnée ne quitte la machine.

NOTE HONNÊTE : le GGUF (llama.cpp) n'a pas pu être compilé sur cette
machine (pas de chaîne MSVC) — on sert le modèle via transformers.
Mêmes garanties (déterminisme, privauté), format de service différent.

Le modèle est spécialisé : format d'invite COMPACT (sans les 6 règles) —
<CORE> … </CORE> <HIST> … </HIST> <STYLE> … </STYLE>

API :
  GET  /health        → { "ok": true, "modele": "...", "duree_chargement_s": N }
  POST /phrase        → { "prompt": "...", "response": "..." }
        body: { "prompt": "...", "max_tokens": 100 }

Usage : python serveur_phraseur_ft.py [--port 11439]
"""
import argparse, json, os, sys, time

_ICI = os.path.dirname(os.path.abspath(__file__))
_DONNEES = os.path.join(_ICI, "data", "phraseur")
_BASE = "HuggingFaceTB/SmolLM2-135M-Instruct"
_LORA = os.path.join(_DONNEES, "lora", "best")  # ou "lora" si pas de best

import torch
from flask import Flask, jsonify, request
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

app = Flask(__name__)
MODELE = None
TOKENIZER = None
T0 = None


def charger():
    global MODELE, TOKENIZER, T0
    T0 = time.time()
    torch.set_num_threads(12)
    TOKENIZER = AutoTokenizer.from_pretrained(_BASE)
    if TOKENIZER.pad_token is None:
        TOKENIZER.pad_token = TOKENIZER.eos_token
    base = AutoModelForCausalLM.from_pretrained(_BASE, low_cpu_mem_usage=True)
    # Le meilleur adapter, sinon l'adapter final
    chemin = _LORA if os.path.isdir(_LORA) else os.path.join(_DONNEES, "lora")
    MODELE = PeftModel.from_pretrained(base, chemin)
    MODELE.eval()
    return f"{MODELE.num_parameters()/1e6:.0f}M (base + LoRA)"


@app.route("/health")
def health():
    return jsonify({"ok": MODELE is not None,
                    "modele": MODELE is not None and "SmolLM2-135M+LoRA",
                    "duree_chargement_s": int(time.time() - T0)})


@app.route("/phrase", methods=["POST"])
def phrase():
    data = request.get_json(force=True, silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "prompt requis"}), 400
    max_tokens = int(data.get("max_tokens") or 100)
    # Greedy strict : température 0, pas d'échantillonnage → déterministe
    ids = TOKENIZER(prompt, add_special_tokens=False, return_tensors="pt")
    with torch.no_grad():
        out = MODELE.generate(
            input_ids=ids["input_ids"],
            max_new_tokens=max_tokens,
            do_sample=False,
            temperature=None,
            top_k=None,
            top_p=None,
            pad_token_id=TOKENIZER.pad_token_id,
            eos_token_id=TOKENIZER.eos_token_id,
        )
    reponse = TOKENIZER.decode(out[0][ids["input_ids"].shape[1]:],
                               skip_special_tokens=True).strip()
    return jsonify({"prompt": prompt, "response": reponse})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=11439)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    print(f"[PHRASEUR_FT] Chargement du modèle...", flush=True)
    nom = charger()
    print(f"[PHRASEUR_FT] ✅ {nom} · http://{args.host}:{args.port} "
          f"(déterministe, greedy)", flush=True)
    app.run(host=args.host, port=args.port, threaded=True)
