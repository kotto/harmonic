#!/usr/bin/env python3
"""
KA PHONE SERVER v4 — Harmonic AI Engine (Conscience + Calculateur + Fallback LLM)
==================================================================================
Remplacement du moteur Qwen 2.5-3B + Hologramme par le moteur Harmonique v3.0

Architecture :
    Question → GuideHarmonique (domaine) → Retrieval Direct (concepts)
    → CalculateurHarmonique (SymPy si applicable) → DHF (vérification)
    → Templates + Correcteur FR → Réponse avec score de confiance

    Si confiance nulle → Fallback LLM (Ollama local ou API DeepSeek)

Différences avec l'ancien serveur (v3) :
    - Plus de Qwen GGUF local (2 Go) → remplacé par retrieval harmonique (50 Mo)
    - Plus de MGH (bigrammes) → remplacé par cache de cohérence (998 tokens)
    - Plus de "mode hybride LLM+hologramme" → remplacé par ConscienceHarmonique
    - AJOUT : score de confiance par réponse (0-1)
    - AJOUT : calcul mathématique exact (SymPy)
    - AJOUT : Fallback LLM (DeepSeek API cloud)

Usage :
    python ka_phone_harmonic_server.py --port 8900
"""

import os, sys, time, json, logging
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = BASE_DIR.parent
PROJET_DIR = PROJECT_ROOT / "projet" / "cerveau_harmonique_v1"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJET_DIR))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# =========================================================================
# CONFIGURATION
# =========================================================================

with open(BASE_DIR / "config.json") as f:
    CONFIG = json.load(f)

PORT = CONFIG.get("server", {}).get("port", 8900)
HOST = CONFIG.get("server", {}).get("host", "0.0.0.0")

# Statistics counter
stats = {
    "total_questions": 0,
    "total_sympy_calls": 0,
    "total_fallbacks": 0,
    "coherence_sum": 0.0,
    "times_ms": [],
}

# =========================================================================
# INITIALISATION DU MOTEUR HARMONIQUE (lazy loading)
# =========================================================================

_engine = {}
_interface = None
_calculateur = None
_fallback_llm = None

def _init_harmonic_engine():
    """Initialise le moteur harmonique complet."""
    global _interface, _calculateur, _fallback_llm, _engine

    if "ready" in _engine:
        return

    logging.info("Initialisation du moteur Harmonique v3.0...")

    # 1. Tokenizer + Vocabulaire
    import importlib.util as iu

    def _importer(n, c):
        s = iu.spec_from_file_location(n, c)
        m = iu.module_from_spec(s)
        s.loader.exec_module(m)
        return m

    vmath = _importer("vmath", str(PROJECT_ROOT / "harmonic_training" / "model" / "vocabulaire_math.py"))
    hrg = _importer("hrg", str(PROJECT_ROOT / "harmonic_training" / "model" / "harmonic_resonance_generator.py"))
    tok = hrg.TokeniseurOndes(vmath.VOCABULAIRE_MATH, use_pi_over_6=True)

    # Fréquences
    fp = PROJECT_ROOT / "ka_knowledge_base" / "frequences_math_final.npz"
    if fp.exists():
        d = np.load(str(fp))
        tok._kx = d["kx"]
        tok._ky = d["ky"]

    # 2. GuideHarmonique
    from engine.table_equivalence_harmonique import GuideHarmonique
    guide = GuideHarmonique(tok)

    # 3. Cache de cohérence
    cache_path = PROJET_DIR / "data" / "coherence_cache_massif.npz"
    cache = {}
    if cache_path.exists():
        data = np.load(str(cache_path), allow_pickle=True)
        cache = {str(data["tokens"][i]): float(data["scores_indiv"][i]) for i in range(len(data["tokens"]))}
        logging.info(f"Cache de cohérence chargé : {len(cache)} tokens")
    else:
        logging.warning("Cache de cohérence non trouvé, utilisation du mode dégradé")

    # 4. Templates
    try:
        from scripts import templates_phrases_fr
        templates = templates_phrases_fr
    except ImportError:
        templates = None

    # 5. Interface Harmonique (habillage humain)
    from engine.interface_harmonique import InterfaceHarmonique
    _interface = InterfaceHarmonique()
    _interface.initialiser(langue="fr")

    # Remplacer les composants par les nôtres (plus récents)
    _interface.guide = guide
    _interface.cache = cache
    _interface.templates = templates
    _interface.cerveau.guide = guide
    _interface.cerveau.cache = cache
    _interface.cerveau.tok = tok

    # 6. Calculateur Harmonique (SymPy)
    from engine.calculateur_harmonique import CalculateurHarmonique
    _calculateur = CalculateurHarmonique()
    _calculateur.initialiser(guide=guide, cache=cache, templates=templates)

    # 7. Fallback LLM (DeepSeek API cloud)
    try:
        from engine.fallback_llm import FallbackLLM
        _fallback_llm = FallbackLLM(mode="cloud", modele="deepseek-chat", timeout=30)
        logging.info("Fallback LLM (DeepSeek API) initialisé")
    except Exception as e:
        logging.warning(f"Fallback LLM indisponible : {e}")
        _fallback_llm = None

    _engine["ready"] = True
    _engine["guide"] = guide
    _engine["cache"] = cache
    _engine["tok"] = tok
    _engine["templates"] = templates

    logging.info(f"Moteur Harmonique v3.0 prêt — {len(cache)} tokens, guide={len(guide._tous_ids_math)} domaines")

# =========================================================================
# ENDPOINTS API
# =========================================================================

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Endpoint principal — question mathématique avec réponse harmonique."""
    _init_harmonic_engine()
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    langue = data.get("lang", "fr")

    if not prompt:
        return jsonify({"error": "Prompt vide"}), 400

    t0 = time.time()
    stats["total_questions"] += 1

    # === Étape 1 : Conscience Harmonique (retrieval + vérification) ===
    resultat = _interface.posser_question(prompt, langue=langue)

    # Variables de réponse
    reponse = resultat.get("reponse", "")
    confiance = resultat.get("confiance", "nulle")
    coherence = resultat.get("score", 0.0)
    domaine = resultat.get("domaine", "general")
    concepts = resultat.get("concepts", [])
    scores_concepts = resultat.get("scores_concepts", [])
    source = resultat.get("source", "harmonique")
    phrase = resultat.get("phrase", reponse)

    # === Étape 2 : Si confiance nulle, tenter le Fallback LLM ===
    if confiance == "nulle" and _fallback_llm:
        resp_llm = _fallback_llm.generer(prompt, concepts, domaine, langue)
        if resp_llm.get("accepte"):
            reponse = resp_llm["reponse"]
            coherence = resp_llm["coherence"]
            source = "fallback_llm"
            stats["total_fallbacks"] += 1

    elapsed_ms = round((time.time() - t0) * 1000, 1)
    stats["coherence_sum"] += coherence
    stats["times_ms"].append(elapsed_ms)

    return jsonify({
        "question": prompt,
        "reponse": reponse,
        "phrase": phrase,
        "domaine": domaine,
        "concepts": concepts[:8],
        "scores_concepts": scores_concepts[:8],
        "coherence": round(coherence, 3),
        "confiance": confiance,
        "source": source,
        "temps_ms": elapsed_ms,
        "hors_ligne": source == "harmonique",  # True si pas de LLM
    })

@app.route("/api/solve", methods=["POST"])
def api_solve():
    """Endpoint de calcul mathématique exact (SymPy)."""
    _init_harmonic_engine()
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    langue = data.get("lang", "fr")

    if not question:
        return jsonify({"error": "Question vide"}), 400

    t0 = time.time()
    stats["total_questions"] += 1
    stats["total_sympy_calls"] += 1

    resultat = _calculateur.resoudre(question, langue=langue)

    elapsed_ms = round((time.time() - t0) * 1000, 1)
    stats["coherence_sum"] += resultat.get("coherence", 0.5)
    stats["times_ms"].append(elapsed_ms)

    return jsonify({
        "question": question,
        "domaine": resultat.get("domaine", ""),
        "type_calcul": resultat.get("type_calcul", ""),
        "expression": resultat.get("expression", ""),
        "resultat_sympy": resultat.get("resultat_sympy"),
        "concepts": resultat.get("concepts_dhf", [])[:8],
        "coherence": resultat.get("coherence", 0.5),
        "confiance": resultat.get("confiance", "nulle"),
        "phrase": resultat.get("phrase", ""),
        "source": resultat.get("source", "harmonique"),
        "temps_ms": elapsed_ms,
        "hors_ligne": resultat.get("source") != "fallback_llm",
    })

@app.route("/api/stats")
def api_stats():
    """Statistiques du serveur harmonique."""
    _init_harmonic_engine()
    n = max(stats["total_questions"], 1)
    avg_coherence = stats["coherence_sum"] / n
    avg_time = sum(stats["times_ms"]) / n if stats["times_ms"] else 0

    return jsonify({
        "status": "online",
        "version": "4.0",
        "engine": "Harmonic AI v3.0 (Conscience + Calculateur + DHF + Fallback LLM)",
        "total_questions": stats["total_questions"],
        "avg_coherence": round(avg_coherence, 3),
        "avg_latency_ms": round(avg_time, 1),
        "total_sympy_calls": stats["total_sympy_calls"],
        "total_fallbacks": stats["total_fallbacks"],
        "fallback_rate": f"{stats['total_fallbacks']/n:.1%}",
        "cache_tokens": len(_engine.get("cache", {})),
        "domains": 11,
        "hologram_size": "256x256",
        "offline_capable": True,
    })

@app.route("/api/health")
def api_health():
    """Healthcheck rapide."""
    return jsonify({"status": "ok", "version": "4.0"})

# =========================================================================
# ROUTE STATIQUE (UI mobile existante)
# =========================================================================

@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "index.html")

@app.route("/www/<path:filename>")
def serve_www(filename):
    return send_from_directory(str(BASE_DIR / "www"), filename)

# =========================================================================
# MAIN
# =========================================================================

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="KA Phone v4 — Harmonic AI Engine")
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--host", type=str, default=HOST)
    args = p.parse_args()

    print(f"\n{'='*60}")
    print(f"KA PHONE SERVER v4 — Harmonic AI Engine")
    print(f"{'='*60}")
    print(f"  URL       : http://localhost:{args.port}")
    print(f"  Moteur    : ConscienceHarmonique + Calculateur + DHF")
    print(f"  Fallback  : DeepSeek API (cloud)")
    print(f"  SymPy     : Calcul exact intégré")
    print(f"  Confiance : Score 0-1 par réponse")
    print(f"{'='*60}\n")

    _init_harmonic_engine()
    app.run(host=args.host, port=args.port, debug=False)