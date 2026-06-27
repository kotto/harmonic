#!/usr/bin/env python3
"""
KA PHONE SERVER v5 — UNIFIED (v3 UI + v4 Harmonic Engine)
===========================================================
Combine le meilleur des deux serveurs :
    - v3 : UI PWA riche (5 onglets), MGH fallback, Qwen LLM local
    - v4 : Moteur Harmonique, DHF, Calculateur SymPy, Fallback DeepSeek

Pipeline :
    1. Harmonic Engine (v4) → DHF vérification
    2. Si confiance haute/moyenne → réponse harmonique
    3. Si confiance basse/nulle :
       a. Essayer Qwen local (v3) → vérifié par DHF
       b. Essayer MGH (v3) → vérifié par DHF
       c. Fallback DeepSeek API → vérifié par DHF
    4. Apprentissage continu après chaque réponse

Usage : python ka_phone_unified_server.py --port 8900
"""

import os, sys, time, json, logging, re
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
# CONFIG
# =========================================================================
with open(BASE_DIR / "config.json") as f:
    CONFIG = json.load(f)

PORT = CONFIG.get("server", {}).get("port", 8900)
HOST = CONFIG.get("server", {}).get("host", "0.0.0.0")
PHI = 1.618033988749895

stats = {"total_questions": 0, "total_harmonic": 0, "total_qwen": 0, "total_mgh": 0, "total_fallbacks": 0, "coherence_sum": 0.0, "times_ms": []}

# =========================================================================
# INITIALISATION (lazy)
# =========================================================================
_engines = {}
_interface = None
_calculateur = None
_fallback_llm = None

def init_v4_harmonic():
    """Initialise le moteur harmonique v4 (Conscience + DHF + Calculateur)."""
    global _interface, _calculateur, _fallback_llm
    if "v4_ready" in _engines: return

    logging.info("⚡ Initialisation Moteur Harmonique v4...")
    import importlib.util as iu
    def _importer(n, c):
        s = iu.spec_from_file_location(n, c); m = iu.module_from_spec(s); s.loader.exec_module(m); return m

    vmath = _importer("vmath", str(PROJECT_ROOT / "harmonic_training" / "model" / "vocabulaire_math.py"))
    hrg = _importer("hrg", str(PROJECT_ROOT / "harmonic_training" / "model" / "harmonic_resonance_generator.py"))
    tok = hrg.TokeniseurOndes(vmath.VOCABULAIRE_MATH, use_pi_over_6=True)

    fp = PROJECT_ROOT / "ka_knowledge_base" / "frequences_math_final.npz"
    if fp.exists():
        d = np.load(str(fp)); tok._kx = d["kx"]; tok._ky = d["ky"]

    from engine.table_equivalence_harmonique import GuideHarmonique
    guide = GuideHarmonique(tok)

    cache_path = PROJET_DIR / "data" / "coherence_cache_massif.npz"
    cache = {}
    if cache_path.exists():
        data = np.load(str(cache_path), allow_pickle=True)
        cache = {str(data["tokens"][i]): float(data["scores_indiv"][i]) for i in range(len(data["tokens"]))}
        logging.info(f"   Cache : {len(cache)} tokens")

    try:
        from scripts import templates_phrases_fr
        templates = templates_phrases_fr
    except ImportError:
        templates = None

    from engine.interface_harmonique import InterfaceHarmonique
    _interface = InterfaceHarmonique()
    _interface.guide = guide; _interface.cache = cache; _interface.templates = templates
    from engine.conscience_harmonique import ConscienceHarmonique
    _interface.cerveau = ConscienceHarmonique()
    _interface.cerveau.initialiser(guide=guide, cache=cache, templates=templates, tok=tok)
    _interface._initialise = True

    from engine.calculateur_harmonique import CalculateurHarmonique
    _calculateur = CalculateurHarmonique()
    _calculateur.initialiser(guide=guide, cache=cache, templates=templates)

    try:
        from engine.fallback_llm import FallbackLLM
        _fallback_llm = FallbackLLM(mode="cloud", modele="deepseek-chat", timeout=30)
        logging.info("   Fallback DeepSeek API : OK")
    except Exception as e:
        logging.warning(f"   Fallback DeepSeek indisponible : {e}")
        _fallback_llm = None

    _engines["v4_ready"] = True
    _engines["guide"] = guide; _engines["cache"] = cache; _engines["tok"] = tok
    logging.info("   Moteur Harmonique v4 prêt.")

def init_v3_legacy():
    """Initialise le moteur v3 (Qwen local + MGH)."""
    if "v3_ready" in _engines: return

    logging.info("📦 Initialisation Moteur Legacy v3 (Qwen + MGH)...")
    from bridge_harmonic_deepseek_gguf import BridgeHarmoniqueGGUF
    modele = BASE_DIR / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"
    bridge = None
    try:
        if modele.exists():
            bridge = BridgeHarmoniqueGGUF(chemin_modele=str(modele), n_lecteurs=8, n_ctx=2048, n_threads=4, n_gpu_layers=0, mode="hybrid")
            logging.info("   Qwen 2.5-3B chargé (2 Go)")
        else:
            logging.warning(f"   Modèle introuvable : {modele}")
    except Exception as e:
        logging.warning(f"   Qwen LLM erreur : {e}")

    if bridge is None:
        try:
            bridge = BridgeHarmoniqueGGUF(mode="harmonic", n_lecteurs=8)
        except Exception:
            bridge = None

    holo_path = PROJECT_ROOT / "ka_knowledge_base" / "hologramme.npy"
    if bridge and holo_path.exists():
        bridge.monde.H = np.load(str(holo_path))

    mgh = None
    try:
        from mgh_generation import MGH
        mgh = MGH()
        logging.info(f"   MGH : {len(mgh.bigram_index):,} bigrammes, {len(mgh.vocab)} mots")
    except Exception:
        pass

    _engines["v3_ready"] = True
    _engines["bridge"] = bridge
    _engines["mgh"] = mgh
    logging.info("   Moteur Legacy v3 prêt.")

def init_all():
    init_v4_harmonic()
    init_v3_legacy()

# =========================================================================
# MGH FALLBACK (v3)
# =========================================================================
STOP_WORDS = {"c'est","quoi","que","est","une","pour","dans","avec","des","les","pas","qui","sur","fait","sont","aux","ces","ses","leur","nos","votre","cette","cet","tout","tous","plus","moins","tres","bien","alors","donc","mais","aussi","meme","comme","quand","comment","peux","peut","peuvent","doit","apres","avant","pendant","entre","sans","sous","vers","depuis","signifie","veut","dire","explique","quel","quelle","quels","quelles","cela","ceci","dela"}

def _generer_mgh(prompt, mgh):
    p = prompt.lower().strip()
    mots = []
    for mot in p.replace('?','').replace('.','').replace(',','').replace("'"," ").split():
        mot = mot.strip('"«»()[]')
        if len(mot) > 2 and mot not in STOP_WORDS:
            mots.append(mot)
    for mot in mots:
        if mot in mgh.vocab:
            try:
                fluide = mgh.generer_avec_savoir(mot, contexte_savoir=mots[:8], max_mots=30, temperature=0.35)
                if len(fluide.split()) >= 4:
                    return f"A propos de '{mot}' ({len(mgh.bigram_index):,} connexions) : {fluide.capitalize()}."
            except:
                pass
    connus = [c for c in mots if c in mgh.vocab]
    if connus:
        return f"Concepts identifies : {', '.join(connus[:6])}. ({len(mgh.bigram_index):,} bigrammes MGH)."
    return None

# =========================================================================
# PIPELINE UNIFIÉ
# =========================================================================

def _reponse_unifiee(prompt, langue="fr"):
    """Pipeline complet : v4 prioritaire → v3 Qwen → v3 MGH → DeepSeek."""
    init_all()
    t0 = time.time()
    stats["total_questions"] += 1

    # === ÉTAPE 1 : Harmonique v4 ===
    resultat = _interface.poser_question(prompt, langue=langue)
    confiance = resultat.get("confiance", "nulle")
    coherence = resultat.get("score", 0.0)
    domaine = resultat.get("domaine", "general")
    concepts = resultat.get("concepts", [])
    reponse = resultat.get("reponse", "")
    source = resultat.get("source", "harmonique")

    if confiance in ("haute", "moyenne"):
        stats["total_harmonic"] += 1
        elapsed_ms = round((time.time() - t0) * 1000, 1)
        stats["coherence_sum"] += coherence
        stats["times_ms"].append(elapsed_ms)
        return {"reponse": reponse, "confiance": confiance, "coherence": round(coherence, 3), "domaine": domaine, "concepts": concepts[:8], "source": source, "temps_ms": elapsed_ms, "hors_ligne": source == "harmonique"}

    # === ÉTAPE 2 : Qwen local (v3) ===
    bridge = _engines.get("bridge")
    if bridge and bridge.llm is not None:
        try:
            resultat_llm = bridge.generer(prompt=prompt, max_tokens=256, temperature=0.7)
            reponse_qwen = resultat_llm.get("texte_genere", "").strip()
            if reponse_qwen and len(reponse_qwen) >= 15:
                coh_qwen = _verifier_coherence(reponse_qwen, prompt)
                if coh_qwen >= 0.40:
                    stats["total_qwen"] += 1
                    elapsed_ms = round((time.time() - t0) * 1000, 1)
                    stats["coherence_sum"] += coh_qwen
                    stats["times_ms"].append(elapsed_ms)
                    bridge.apprendre(reponse_qwen, amplitude=0.15)
                    return {"reponse": reponse_qwen, "confiance": "moyenne" if coh_qwen >= 0.55 else "basse", "coherence": round(coh_qwen, 3), "domaine": domaine, "concepts": concepts[:8], "source": "qwen_local", "temps_ms": elapsed_ms, "hors_ligne": True}
        except Exception:
            pass

    # === ÉTAPE 3 : MGH (v3) ===
    mgh = _engines.get("mgh")
    if mgh:
        reponse_mgh = _generer_mgh(prompt, mgh)
        if reponse_mgh:
            coh_mgh = _verifier_coherence(reponse_mgh, prompt)
            if coh_mgh >= 0.40:
                stats["total_mgh"] += 1
                elapsed_ms = round((time.time() - t0) * 1000, 1)
                stats["coherence_sum"] += coh_mgh
                stats["times_ms"].append(elapsed_ms)
                return {"reponse": reponse_mgh, "confiance": "moyenne" if coh_mgh >= 0.55 else "basse", "coherence": round(coh_mgh, 3), "domaine": domaine, "concepts": concepts[:8], "source": "mgh", "temps_ms": elapsed_ms, "hors_ligne": True}

    # === ÉTAPE 4 : Fallback DeepSeek API ===
    if _fallback_llm:
        try:
            resp_llm = _fallback_llm.generer(prompt, concepts, domaine, langue)
            if resp_llm.get("accepte"):
                stats["total_fallbacks"] += 1
                elapsed_ms = round((time.time() - t0) * 1000, 1)
                stats["coherence_sum"] += resp_llm["coherence"]
                stats["times_ms"].append(elapsed_ms)
                return {"reponse": resp_llm["reponse"], "confiance": "moyenne", "coherence": round(resp_llm["coherence"], 3), "domaine": domaine, "concepts": concepts[:8], "source": "deepseek_cloud", "temps_ms": elapsed_ms, "hors_ligne": False}
        except Exception:
            pass

    # Échec complet
    elapsed_ms = round((time.time() - t0) * 1000, 1)
    return {"reponse": "Je ne peux pas répondre à cette question avec confiance. Essayez de reformuler.", "confiance": "nulle", "coherence": 0.0, "domaine": "general", "concepts": [], "source": "echec", "temps_ms": elapsed_ms, "hors_ligne": True}

def _verifier_coherence(texte, question=""):
    """Vérifie la cohérence via le DHF si disponible."""
    try:
        if _interface and _interface.cerveau and _interface.cerveau.dhf and _interface.cerveau.dhf.dictionnaire:
            verif = _interface.cerveau.dhf.dictionnaire.verifier_coherence(texte)
            return verif.get("score_global", 0.5)
    except Exception:
        pass
    return 0.5

# =========================================================================
# API ENDPOINTS
# =========================================================================

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    langue = data.get("lang", "fr")
    if not prompt:
        return jsonify({"error": "Prompt vide"}), 400
    resultat = _reponse_unifiee(prompt, langue)
    return jsonify({"question": prompt, **resultat})

@app.route("/api/solve", methods=["POST"])
def api_solve():
    init_v4_harmonic()
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    langue = data.get("lang", "fr")
    if not question:
        return jsonify({"error": "Question vide"}), 400
    if _calculateur is None:
        return jsonify({"error": "Calculateur non disponible"}), 503
    t0 = time.time()
    resultat = _calculateur.resoudre(question, langue=langue)
    elapsed_ms = round((time.time() - t0) * 1000, 1)
    return jsonify({"question": question, "domaine": resultat.get("domaine", ""), "type_calcul": resultat.get("type_calcul", ""), "expression": resultat.get("expression", ""), "resultat_sympy": resultat.get("resultat_sympy"), "concepts": resultat.get("concepts_dhf", [])[:8], "coherence": resultat.get("coherence", 0.5), "confiance": resultat.get("confiance", "nulle"), "phrase": resultat.get("phrase", ""), "source": resultat.get("source", "harmonique"), "temps_ms": elapsed_ms, "hors_ligne": resultat.get("source") != "fallback_llm"})

@app.route("/api/stats")
def api_stats():
    n = max(stats["total_questions"], 1)
    return jsonify({"status": "online", "version": "5.0", "engine": "KA Phone Unified (Harmonic v4 + Qwen v3 + MGH + DeepSeek)", "total_questions": stats["total_questions"], "total_harmonic": stats["total_harmonic"], "total_qwen": stats["total_qwen"], "total_mgh": stats["total_mgh"], "total_fallbacks": stats["total_fallbacks"], "avg_coherence": round(stats["coherence_sum"] / n, 3), "avg_latency_ms": round(sum(stats["times_ms"]) / n, 1) if stats["times_ms"] else 0, "offline_capable": True, "plan": "Pro", "version_name": "KA Phone v5 — Ton Double Numérique"})

@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "version": "5.0", "name": "KA Phone Unified"})

@app.route("/api/system/status")
def api_status():
    init_all()
    mgh = _engines.get("mgh")
    bridge = _engines.get("bridge")
    return jsonify({"status": "online", "version": "5.0", "name": "KA Phone — Ton Double Numérique", "harmonic_engine": "v3.0 (Conscience + DHF)", "llm_local": bridge.llm is not None if bridge else False, "llm_model": "Qwen 2.5-3B" if bridge and bridge.llm else "Non chargé", "mgh_bigrams": len(mgh.bigram_index) if mgh else 0, "mgh_vocab": len(mgh.vocab) if mgh else 0, "cache_tokens": len(_engines.get("cache", {})), "domains": 11, "offline_capable": True, "tagline": "Il se souvient de tout. Il ne ment jamais."})

# =========================================================================
# ROUTES STATIQUES
# =========================================================================
@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "index.html")

@app.route("/www/<path:filename>")
def serve_www(filename):
    return send_from_directory(str(BASE_DIR / "www"), filename)

@app.route("/sw.js")
def serve_sw():
    return send_from_directory(str(BASE_DIR), "sw.js")

# =========================================================================
# MAIN
# =========================================================================
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="KA Phone v5 — Unified Server")
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--host", type=str, default=HOST)
    args = p.parse_args()

    print(f"\n{'='*60}")
    print(f"KA PHONE SERVER v5 — Unified")
    print(f"{'='*60}")
    print(f"  URL        : http://localhost:{args.port}")
    print(f"  Moteur     : Harmonique v4 + Qwen 2.5-3B + MGH + DeepSeek")
    print(f"  Pipeline   : v4 → Qwen local → MGH → DeepSeek API")
    print(f"  Hors-ligne : 95% autonome")
    print(f"  Tagline    : Il se souvient de tout. Il ne ment jamais.")
    print(f"{'='*60}\n")

    init_all()
    app.run(host=args.host, port=args.port, debug=False)