#!/usr/bin/env python3
"""
KA PHONE SERVER v3 — LLM Qwen 2.5-3B (2 Go) + Hologramme + MGH (67k bigrammes)
================================================================================
Mode hybride : Qwen 2.5-3B génère la réponse, l'hologramme enrichit le contexte.
Si le LLM n'est pas disponible → fallback harmonique + MGH.

Usage : python ka_phone_server.py --port 8900
"""

import os, sys, time, json, logging, re
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
import numpy as np

BASE_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = BASE_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

with open(BASE_DIR / "config.json") as f:
    CONFIG = json.load(f)

app = Flask(__name__, static_folder=".", static_url_path="")
logging.basicConfig(level=logging.INFO)

_engines = {}

def get_engine():
    if "ka" not in _engines:
        from bridge_harmonic_deepseek_gguf import BridgeHarmoniqueGGUF
        modele = BASE_DIR / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"
        try:
            if modele.exists():
                bridge = BridgeHarmoniqueGGUF(
                    chemin_modele=str(modele), n_lecteurs=8,
                    n_ctx=2048, n_threads=4, n_gpu_layers=0, mode="hybrid"
                )
                logging.info("Mode HYBRIDE (Qwen 2.5-3B + hologramme)")
            else:
                raise FileNotFoundError(f"Modele introuvable: {modele}")
        except Exception as e:
            logging.warning(f"LLM indisponible ({e}), mode harmonique pur")
            bridge = BridgeHarmoniqueGGUF(mode="harmonic", n_lecteurs=8)
        holo_path = PROJECT_ROOT / "ka_knowledge_base" / "hologramme.npy"
        if holo_path.exists():
            bridge.monde.H = np.load(str(holo_path))
        _engines["ka"] = bridge
    return _engines["ka"]

def get_mgh():
    if "mgh" not in _engines:
        from mgh_generation import MGH
        _engines["mgh"] = MGH()
    return _engines["mgh"]

# =========================================================================
# GÉNÉRATION
# =========================================================================

def _reponse_identite(engine, mgh):
    return (f"Je suis KA, assistant holographique 64x64 (32 Ko). "
            f"J'encode {engine.monde.n_experiences} connaissances par superposition d'ondes. "
            f"Mon module de langage MGH a {len(mgh.bigram_index):,} bigrammes "
            f"appris sur 6 millions de phrases. Energie: {engine.monde.energie():.0f}.")

def _reponse_capacites(engine, mgh):
    return (f"Je peux repondre en utilisant mon hologramme de savoir "
            f"({engine.monde.n_experiences} experiences, 12M tokens) "
            f"et mon module de langage ({len(mgh.bigram_index):,} bigrammes). "
            f"64 Ko au total, CPU uniquement, 100% hors-ligne.")

def _extraire_mots_cles(prompt: str) -> list:
    p = prompt.lower().rstrip('?.!')
    stop = {"c'est","quoi","que","est","une","pour","dans","avec","des","les","pas","qui",
            "sur","fait","sont","aux","ces","ses","leur","nos","votre","cette","cet","tout",
            "tous","plus","moins","tres","bien","alors","donc","mais","aussi","meme","comme",
            "quand","comment","peux","peut","peuvent","doit","apres","avant","pendant",
            "entre","sans","sous","vers","depuis","signifie","veut","dire","explique",
            "quel","quelle","quels","quelles","cela","ceci","dela"}
    mots = []
    for mot in p.replace('?','').replace('.','').replace(',','').replace("'"," ").split():
        mot = mot.strip('"«»()[]')
        if len(mot) > 2 and mot not in stop:
            mots.append(mot)
    return mots

def _generer_reponse(prompt: str, engine, mgh) -> tuple:
    p = prompt.lower().strip()
    
    if any(m in p for m in ["qui es tu","presente toi","ton nom","c est quoi ka"]):
        return _reponse_identite(engine, mgh), "Identity"
    
    if any(m in p for m in ["que fais tu","que sais tu","tes capacites"]):
        return _reponse_capacites(engine, mgh), "Capabilities"
    
    mots_cles = _extraire_mots_cles(prompt)
    
    # Essayer chaque mot-clé dans MGH
    for mot in mots_cles:
        if mot in mgh.vocab:
            n_conn = sum(1 for k in mgh.bigram_index if k.startswith(f"{mot}|"))
            if n_conn >= 5:
                try:
                    fluide = mgh.generer_avec_savoir(
                        mot, contexte_savoir=mots_cles[:8], max_mots=30, temperature=0.35
                    )
                    if len(fluide.split()) >= 4:
                        return (
                            f"A propos de '{mot}' ({n_conn} connexions linguistiques) : "
                            f"{fluide.capitalize()}.",
                            f"MGH ({n_conn} bigrammes)"
                        )
                except:
                    pass
    
    # Concepts trouves dans MGH
    connus = [c for c in mots_cles if c in mgh.vocab]
    if connus:
        return (
            f"Mots identifies dans MGH : {', '.join(connus[:6])}. "
            f"({len(mgh.bigram_index):,} bigrammes, {len(mgh.vocab)} mots). "
            f"Ces concepts sont relies a des milliers de connexions linguistiques.",
            "MGH Analyse"
        )
    
    return (
        f"MGH ne connait pas encore ces mots ({len(mgh.bigram_index):,} bigrammes, "
        f"{len(mgh.vocab)} mots). L'hologramme de savoir continue d'apprendre.",
        "Fallback"
    )

# =========================================================================
# API
# =========================================================================

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt: return jsonify({"error": "Prompt vide"}), 400
    
    t0 = time.time()
    engine = get_engine()
    mgh = get_mgh()
    
    # Essayer le mode hybride (LLM + hologramme)
    if engine.mode == "hybrid" and engine.llm is not None:
        try:
            resultat = engine.generer(prompt=prompt, max_tokens=256, temperature=0.7)
            reponse = resultat.get("texte_genere", "").strip()
            if reponse and len(reponse) >= 15:
                engine.apprendre(reponse, amplitude=0.15)
                return jsonify({
                    "reponse": reponse,
                    "mode_generation": "Qwen 2.5-3B + hologramme",
                    "temps_ms": round((time.time()-t0)*1000, 1),
                    "hors_ligne": True,
                })
        except Exception as e:
            logging.warning(f"LLM error, fallback MGH: {e}")
    
    # Fallback MGH
    reponse, gen_mode = _generer_reponse(prompt, engine, mgh)
    engine.apprendre(reponse, amplitude=0.15)
    
    return jsonify({
        "reponse": reponse,
        "mode_generation": gen_mode,
        "temps_ms": round((time.time()-t0)*1000, 1),
        "hors_ligne": True,
        "mgh_bigrams": len(mgh.bigram_index),
        "mgh_vocab": len(mgh.vocab),
    })

@app.route("/api/system/status")
def api_status():
    mgh = get_mgh()
    engine = get_engine()
    return jsonify({
        "status": "online",
        "mgh_bigrams": len(mgh.bigram_index),
        "mgh_vocab": len(mgh.vocab),
        "llm_loaded": engine.llm is not None if engine else False,
        "mode": engine.mode if engine else "harmonic",
    })

@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "index.html")

# =========================================================================
# MAIN
# =========================================================================
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8900)
    p.add_argument("--host", type=str, default="0.0.0.0")
    args = p.parse_args()
    
    mgh = get_mgh()
    modele = BASE_DIR / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"
    
    print(f"\n{'='*60}")
    print(f"KA PHONE SERVER v3")
    print(f"{'='*60}")
    print(f"  URL      : http://localhost:{args.port}")
    print(f"  LLM      : {'Qwen 2.5-3B (2 Go)' if modele.exists() else 'Non trouve'}")
    print(f"  MGH      : {len(mgh.bigram_index):,} bigrammes, {len(mgh.vocab)} mots")
    print(f"  Savoir   : 12M tokens, 32 Ko")
    print(f"{'='*60}\n")
    
    app.run(host=args.host, port=args.port, debug=False)