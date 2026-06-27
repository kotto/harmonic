#!/usr/bin/env python3
"""
BRIDGE HARMONIQUE ↔ DEEPSEEK-QWEN GGUF
========================================
Hybridation entre le systeme harmonique (HologrammeMonde, LecteursMultiples,
Resonance Inverse) et le LLM DeepSeek-Qwen GGUF installe sur H:.

Architecture :
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Hologramme       │    │ Lecteurs (8)     │    │ LLM GGUF         │
│ (memoire brute)  │ -> │ (resonance)      │ -> │ Qwen3.5-9B       │
│ 64x64 complexe   │    │ 8 perspectives   │    │ DeepSeek-V4      │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         |                       |                        |
         |   Feedback            |   Contexte enrichi     |   Generation
         +<----------------------+<-----------------------+

Modes d'utilisation :
  --mode harmonic : Moteur harmonique pur (sans LLM externe)
  --mode hybrid   : Hologramme enrichit le prompt, LLM genere, feedback
  --mode llm_only : LLM GGUF seul (sans hologramme)

Usage :
  python bridge_harmonic_deepseek_gguf.py --mode hybrid --prompt "explique la resonance"
  python bridge_harmonic_deepseek_gguf.py --serve --port 8081
"""

import os
import sys
import math
import time
import json
import hashlib
import argparse
import threading
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict

import numpy as np
import importlib.util

# Ajouter le projet au path
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# Import DIRECT du module de resonance (bypass __init__.py qui necessite torch)
# harmonic_resonance_generator.py est pur numpy - pas de dependance torch
def _import_module_direct(module_name, file_path):
    """Importe un module directement sans passer par __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

_resonance_path = os.path.join(
    _project_root, "harmonic_training", "model", "harmonic_resonance_generator.py"
)
_harmonic_resonance = _import_module_direct(
    "harmonic_training.model.harmonic_resonance_generator",
    _resonance_path
)

# Extraire les classes et constantes
HologrammeMonde = _harmonic_resonance.HologrammeMonde
TokeniseurOndes = _harmonic_resonance.TokeniseurOndes
LecteurResonantMultiple = _harmonic_resonance.LecteurResonantMultiple
GenerateurResonance = _harmonic_resonance.GenerateurResonance
VOCABULAIRE_BASE = _harmonic_resonance.VOCABULAIRE_BASE
SystemeHarmoniqueComplet = _harmonic_resonance.SystemeHarmoniqueComplet
NX = _harmonic_resonance.NX
NY = _harmonic_resonance.NY
PHI = _harmonic_resonance.PHI
ALPHA = _harmonic_resonance.ALPHA

# =========================================================================
# CONFIGURATION
# =========================================================================

# Chemin du modele GGUF sur le disque H:
GGUF_MODEL_PATH = os.environ.get(
    "GGUF_MODEL_PATH",
    r"H:\TELECHARGEMENT-18-20AOUT\Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf"
)

# Parametres d'inference GGUF
GGUF_N_CTX = int(os.environ.get("GGUF_N_CTX", "4096"))
GGUF_N_THREADS = int(os.environ.get("GGUF_N_THREADS", "8"))
GGUF_N_GPU_LAYERS = int(os.environ.get("GGUF_N_GPU_LAYERS", "0"))
GGUF_TEMPERATURE = float(os.environ.get("GGUF_TEMPERATURE", "0.7"))
GGUF_TOP_P = float(os.environ.get("GGUF_TOP_P", "0.9"))
GGUF_TOP_K = int(os.environ.get("GGUF_TOP_K", "40"))

# Parametres harmoniques
N_LECTEURS = int(os.environ.get("N_LECTEURS", "8"))
N_REP_LECTURE = int(os.environ.get("N_REP_LECTURE", "30"))
CONTEXTE_TOKENS_TOP = int(os.environ.get("CONTEXTE_TOKENS_TOP", "30"))

# Cache
CACHE_MAX_ENTRIES = int(os.environ.get("CACHE_MAX_ENTRIES", "512"))
CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() == "true"


# =========================================================================
# DETECTION ET CHARGEMENT DU MODELE GGUF
# =========================================================================

def detecter_modele_gguf(chemin: str = None) -> Tuple[str, Dict]:
    """
    Detecte et verifie le fichier GGUF.
    
    Returns:
        Tuple[chemin_valide, infos_modele]
    """
    if chemin is None:
        chemin = GGUF_MODEL_PATH
    
    if not os.path.exists(chemin):
        # Essayer de trouver le fichier automatiquement
        base_dir = r"H:\TELECHARGEMENT-18-20AOUT"
        if os.path.exists(base_dir):
            for f in os.listdir(base_dir):
                if f.lower().endswith('.gguf'):
                    chemin = os.path.join(base_dir, f)
                    break
    
    if not os.path.exists(chemin):
        raise FileNotFoundError(
            f"Modele GGUF introuvable : {chemin}\n"
            f"Verifiez le chemin ou definissez GGUF_MODEL_PATH"
        )
    
    taille_go = os.path.getsize(chemin) / (1024**3)
    
    infos = {
        "chemin": chemin,
        "nom_fichier": os.path.basename(chemin),
        "taille_go": round(taille_go, 2),
        "existe": True,
        "est_gguf": chemin.lower().endswith('.gguf'),
    }
    
    print(f"\n{'='*70}")
    print(f"MODELE GGUF DETECTE")
    print(f"{'='*70}")
    print(f"  Fichier : {infos['nom_fichier']}")
    print(f"  Taille  : {infos['taille_go']:.2f} Go")
    print(f"  Format  : GGUF OK")
    print(f"  Chemin  : {chemin}")
    
    return chemin, infos


def charger_llm_gguf(chemin: str, n_ctx: int = GGUF_N_CTX,
                     n_threads: int = GGUF_N_THREADS,
                     n_gpu_layers: int = GGUF_N_GPU_LAYERS):
    """
    Charge le modele GGUF avec llama-cpp-python.
    Retourne l'objet Llama pret pour l'inference.
    """
    try:
        from llama_cpp import Llama
    except ImportError:
        print("\n[ERREUR] llama-cpp-python n'est pas installe.")
        print("  Installation : pip install llama-cpp-python")
        print("\n  Pour GPU CUDA :")
        print("  CMAKE_ARGS=\"-DGGML_CUDA=on\" pip install llama-cpp-python --force-reinstall --no-cache-dir")
        print("\n  Pour CPU uniquement (recommandé pour test) :")
        print("  pip install llama-cpp-python")
        raise
    
    print(f"\n  Chargement du modele GGUF...")
    print(f"  n_ctx={n_ctx}, n_threads={n_threads}, n_gpu_layers={n_gpu_layers}")
    
    t0 = time.time()
    
    llm = Llama(
        model_path=chemin,
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )
    
    dt = time.time() - t0
    print(f"  Modele charge en {dt:.1f}s")
    print(f"  Pret pour l'inference.")
    
    return llm


# =========================================================================
# CACHE RESEAU HARMONIQUE (SHA256)
# =========================================================================

class CacheReseauHarmonique:
    """
    Cache deterministe pour eviter les appels LLM redondants.
    
    Cle = SHA256(prompt + etat_hologramme + top_tokens + temperature)
    Valeur = texte genere
    
    L'etat de l'hologramme est resume par son energie + signature des lecteurs.
    """
    
    def __init__(self, max_entries: int = CACHE_MAX_ENTRIES):
        self.max_entries = max_entries
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def _signature_etat(self, prompt: str, monde: HologrammeMonde,
                        lecteurs: LecteurResonantMultiple,
                        top_tokens: List[str],
                        temperature: float) -> str:
        """Genere une signature unique de l'etat complet."""
        etat = (
            f"{prompt}|"
            f"E={monde.energie():.4f}|"
            f"N={monde.n_experiences}|"
            f"T={'|'.join(top_tokens[:20])}|"
            f"temp={temperature:.3f}"
        )
        return hashlib.sha256(etat.encode('utf-8', errors='replace')).hexdigest()[:32]
    
    def get(self, prompt: str, monde: HologrammeMonde,
            lecteurs: LecteurResonantMultiple,
            top_tokens: List[str],
            temperature: float) -> Optional[str]:
        """Recupere une reponse du cache si elle existe."""
        if not CACHE_ENABLED:
            return None
        
        cle = self._signature_etat(prompt, monde, lecteurs, top_tokens, temperature)
        
        if cle in self.cache:
            # LRU : deplacer en fin
            valeur = self.cache.pop(cle)
            self.cache[cle] = valeur
            self.hits += 1
            return valeur
        
        self.misses += 1
        return None
    
    def put(self, prompt: str, monde: HologrammeMonde,
            lecteurs: LecteurResonantMultiple,
            top_tokens: List[str],
            temperature: float, reponse: str):
        """Stocke une reponse dans le cache."""
        if not CACHE_ENABLED:
            return
        
        cle = self._signature_etat(prompt, monde, lecteurs, top_tokens, temperature)
        
        if cle in self.cache:
            self.cache.pop(cle)
        
        self.cache[cle] = reponse
        
        while len(self.cache) > self.max_entries:
            self.cache.popitem(last=False)
    
    def stats(self) -> Dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": round(self.hits / max(total, 1), 3),
            "entries": len(self.cache),
            "max_entries": self.max_entries,
        }


# =========================================================================
# BRIDGE HARMONIQUE ↔ LLM GGUF
# =========================================================================

class BridgeHarmoniqueGGUF:
    """
    BRIDGE PRINCIPAL : Hologramme Harmonique ↔ DeepSeek-Qwen GGUF.
    
    Processus complet :
    1. APPRENDRE : Le texte est enregistre dans l'hologramme (inconscient)
    2. LIRE : 8 lecteurs resonnent sur l'hologramme (conscience)
    3. ENRICHIR : Les top tokens resonants enrichissent le prompt
    4. GENERER : Le LLM GGUF genere avec le contexte harmonique
    5. FEEDBACK : La reponse est reinjectee dans l'hologramme
    
    C'est la boucle fermee : le systeme interagit avec lui-meme.
    """
    
    def __init__(self, chemin_modele: str = None,
                 n_lecteurs: int = N_LECTEURS,
                 n_ctx: int = GGUF_N_CTX,
                 n_threads: int = GGUF_N_THREADS,
                 n_gpu_layers: int = GGUF_N_GPU_LAYERS,
                 mode: str = "hybrid"):
        """
        Args:
            chemin_modele: Chemin du fichier GGUF
            n_lecteurs: Nombre de lecteurs resonants
            n_ctx: Taille du contexte LLM
            n_threads: Threads CPU pour l'inference
            n_gpu_layers: Couches GPU (0 = CPU only)
            mode: "harmonic", "hybrid", "llm_only"
        """
        self.mode = mode
        
        # --- Systeme harmonique ---
        print(f"\n[1/3] Initialisation du systeme harmonique...")
        self.systeme = SystemeHarmoniqueComplet(
            VOCABULAIRE_BASE,
            nx=NX, ny=NY,
            n_lecteurs=n_lecteurs,
            n_niveaux=3
        )
        self.tokenizer = self.systeme.tokenizer
        self.monde = self.systeme.monde
        self.lecteurs = self.systeme.lecteurs
        self.generateur = self.systeme.generateur
        print(f"  Hologramme : {self.monde.nx}x{self.monde.ny}")
        print(f"  Lecteurs   : {n_lecteurs}")
        print(f"  Vocabulaire: {self.tokenizer.vocab_size} tokens")
        print(f"  Energie    : {self.monde.energie():.2f}")
        
        # --- LLM GGUF ---
        self.llm = None
        if mode in ("hybrid", "llm_only"):
            print(f"\n[2/3] Chargement du LLM GGUF...")
            chemin, infos = detecter_modele_gguf(chemin_modele)
            self.llm = charger_llm_gguf(chemin, n_ctx, n_threads, n_gpu_layers)
            self.chemin_modele = chemin
            self.infos_modele = infos
        else:
            self.chemin_modele = None
            self.infos_modele = {"existe": False}
            print(f"\n[2/3] Mode harmonique pur (pas de LLM externe)")
        
        # --- Cache ---
        print(f"\n[3/3] Initialisation du cache...")
        self.cache = CacheReseauHarmonique()
        print(f"  Cache : {CACHE_MAX_ENTRIES} entrees max")
        
        # --- Statistiques ---
        self.stats = {
            "n_apprentissages": 0,
            "n_generations": 0,
            "n_tokens_gen": 0,
            "temps_total_ms": 0.0,
            "mode": mode,
        }
        
        print(f"\n{'='*70}")
        print(f"BRIDGE HARMONIQUE <-> DEEPSEEK-QWEN GGUF - PRET")
        print(f"Mode : {mode}")
        print(f"{'='*70}")
    
    def apprendre(self, texte: str, amplitude: float = 0.8):
        """Enregistre un texte dans l'hologramme."""
        self.systeme.apprendre(texte)
        self.stats["n_apprentissages"] += 1
    
    def apprendre_batch(self, textes: List[str]):
        """Enregistre plusieurs textes."""
        for t in textes:
            self.apprendre(t)
    
    def _extraire_contexte_harmonique(self, prompt: str,
                                      n_rep: int = N_REP_LECTURE,
                                      top_k: int = CONTEXTE_TOKENS_TOP
                                      ) -> Tuple[List[str], np.ndarray]:
        """
        Extrait le contexte harmonique a partir de l'hologramme.
        
        1. Apprendre le prompt dans l'hologramme
        2. Faire resonner les 8 lecteurs
        3. Extraire les top tokens par consensus
        """
        # Enregistrer le prompt
        prompt_tokens = self.tokenizer.tokeniser(prompt)
        for idx in prompt_tokens:
            kx, ky = self.tokenizer.vecteur_onde(idx)
            self.monde.enregistrer_onde(kx, ky, 0.5)
        
        # Reinitialiser les lecteurs
        self.lecteurs = LecteurResonantMultiple(
            self.monde, self.lecteurs.n_lecteurs,
            seed=int(time.time() * 1000) % 10000
        )
        
        # Apprentissage des lecteurs
        self.lecteurs.apprendre(n_rep, lr=0.03)
        
        # Extraire les activations
        activations = self.lecteurs.activations_tokens(self.tokenizer)
        
        # Fusion par consensus (moyenne + max)
        act_moy = activations.mean(axis=0)
        act_max = activations.max(axis=0)
        act_fusion = act_moy * 0.6 + act_max * 0.4
        
        # Top tokens
        indices = np.argsort(act_fusion)[::-1][:top_k]
        top_tokens = [self.tokenizer.i2w.get(int(i), '<UNK>') for i in indices]
        
        # Filtrer les tokens speciaux
        top_tokens = [t for t in top_tokens
                      if t not in ('<PAD>', '<UNK>', '<BOS>', '<EOS>')]
        
        return top_tokens, act_fusion
    
    def _construire_prompt_enrichi(self, prompt: str,
                                   top_tokens: List[str]) -> str:
        """
        Construit un prompt enrichi avec le contexte harmonique.
        
        Format :
        [Memoire harmonique: token1 token2 ... tokenN]
        Question de l'utilisateur
        """
        contexte = ' '.join(top_tokens[:20])
        
        # Prompt systeme pour guider le LLM
        system_prompt = (
            "Tu es Harmonic AI, un assistant IA hybride combinant un moteur "
            "harmonique (memoire holographique) et le modele DeepSeek-Qwen. "
            "Utilise le contexte harmonique fourni entre crochets comme source "
            "d'inspiration conceptuelle, mais reponds de maniere coherente et "
            "naturelle a la question. Le contexte harmonique reflete des motifs "
            "de resonance conceptuelle - utilise-le pour enrichir ta reponse "
            "sans le citer textuellement."
        )
        
        prompt_enrichi = (
            f"{system_prompt}\n\n"
            f"[Contexte harmonique resonant: {contexte}]\n\n"
            f"Question: {prompt}\n\n"
            f"Reponse:"
        )
        
        return prompt_enrichi
    
    def _generer_llm(self, prompt: str,
                     max_tokens: int = 512,
                     temperature: float = GGUF_TEMPERATURE,
                     top_p: float = GGUF_TOP_P,
                     top_k: int = GGUF_TOP_K) -> Tuple[str, Dict]:
        """
        Genere avec le LLM GGUF.
        """
        if self.llm is None:
            return "", {"erreur": "LLM non charge"}
        
        t0 = time.time()
        
        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop=["<|end▁of▁sentence｜>", "<|begin▁of▁sentence｜>",
                  "\n\nQuestion:", "\n\n[Contexte"],
            echo=False,
        )
        
        dt = time.time() - t0
        
        texte = output.get("choices", [{}])[0].get("text", "")
        usage = output.get("usage", {})
        
        infos = {
            "temps_ms": round(dt * 1000, 1),
            "tokens_gen": usage.get("completion_tokens", len(texte.split())),
            "tokens_prompt": usage.get("prompt_tokens", 0),
            "tok_s": round(usage.get("completion_tokens", 0) / max(dt, 0.001), 1),
        }
        
        return texte.strip(), infos
    
    def generer(self, prompt: str,
                max_tokens: int = 256,
                temperature: float = 0.7,
                n_rep: int = N_REP_LECTURE,
                top_k_harmonic: int = CONTEXTE_TOKENS_TOP,
                feedback: bool = True) -> Dict:
        """
        GENERE une reponse en mode hybride.
        
        Processus complet :
        1. Extraction du contexte harmonique (resonance)
        2. Enrichissement du prompt
        3. Generation LLM (avec cache)
        4. Feedback dans l'hologramme
        """
        t0 = time.time()
        
        energie_avant = self.monde.energie()
        
        # === MODE HARMONIQUE PUR ===
        if self.mode == "harmonic":
            resultat = self.generateur.generer(
                prompt, max_tokens=max_tokens,
                temperature=temperature,
                n_rep_lecture=n_rep
            )
            resultat["mode"] = "harmonic"
            resultat["contexte_harmonique"] = []
            self.stats["n_generations"] += 1
            return resultat
        
        # === ETAPE 1 : Contexte harmonique ===
        top_tokens, activations = self._extraire_contexte_harmonique(
            prompt, n_rep=n_rep, top_k=top_k_harmonic
        )
        
        # === ETAPE 2 : Verifier le cache ===
        reponse_cachee = self.cache.get(
            prompt, self.monde, self.lecteurs, top_tokens, temperature
        )
        
        if reponse_cachee is not None:
            dt = time.time() - t0
            self.stats["n_generations"] += 1
            return {
                "prompt": prompt,
                "texte_genere": reponse_cachee,
                "mode": self.mode,
                "cache_hit": True,
                "contexte_harmonique": top_tokens[:20],
                "n_tokens": len(reponse_cachee.split()),
                "temps_ms": round(dt * 1000, 1),
                "energie_hologramme": round(self.monde.energie(), 1),
                "n_experiences": self.monde.n_experiences,
            }
        
        # === MODE LLM ONLY ===
        if self.mode == "llm_only":
            texte, infos_llm = self._generer_llm(
                prompt, max_tokens, temperature
            )
            reponse_finale = texte
            llm_infos = infos_llm
        
        # === MODE HYBRIDE ===
        else:
            # ETAPE 3 : Construire le prompt enrichi
            prompt_enrichi = self._construire_prompt_enrichi(prompt, top_tokens)
            
            # ETAPE 4 : Generer avec le LLM
            texte, infos_llm = self._generer_llm(
                prompt_enrichi, max_tokens, temperature
            )
            reponse_finale = texte
            llm_infos = infos_llm
        
        # === ETAPE 5 : Mettre en cache ===
        self.cache.put(
            prompt, self.monde, self.lecteurs, top_tokens,
            temperature, reponse_finale
        )
        
        # === ETAPE 6 : Feedback dans l'hologramme ===
        if feedback and reponse_finale and len(reponse_finale.split()) >= 3:
            self.monde.enregistrer_texte(reponse_finale, self.tokenizer, 0.3)
        
        # === Stats ===
        dt = time.time() - t0
        energie_apres = self.monde.energie()
        
        self.stats["n_generations"] += 1
        self.stats["n_tokens_gen"] += len(reponse_finale.split())
        self.stats["temps_total_ms"] += dt * 1000
        
        return {
            "prompt": prompt,
            "texte_genere": reponse_finale,
            "mode": self.mode,
            "cache_hit": False,
            "contexte_harmonique": top_tokens[:20],
            "tokens_harmoniques_actifs": len(top_tokens),
            "n_tokens": len(reponse_finale.split()),
            "temps_ms": round(dt * 1000, 1),
            "temps_llm_ms": llm_infos.get("temps_ms", dt * 1000),
            "tokens_gen_llm": llm_infos.get("tokens_gen", 0),
            "tok_s_llm": llm_infos.get("tok_s", 0),
            "energie_hologramme": round(self.monde.energie(), 1),
            "delta_energie": round(energie_apres - energie_avant, 1),
            "n_experiences": self.monde.n_experiences,
            "n_lecteurs": self.lecteurs.n_lecteurs,
        }
    
    def diagnostiquer(self) -> Dict:
        """Diagnostic complet du bridge."""
        diag = self.systeme.diagnostiquer()
        
        # Stats du cache
        cache_stats = self.cache.stats()
        
        # Stats des lecteurs (diversite)
        top_lecteurs = self.lecteurs.top_tokens_par_lecteur(self.tokenizer, top_k=5)
        diversite = len(set(
            tuple([t for t, _ in top[:3]]) for top in top_lecteurs
        ))
        
        return {
            **diag,
            "bridge": {
                "mode": self.mode,
                "modele_gguf": self.infos_modele,
                "cache": cache_stats,
                "diversite_lecteurs": f"{diversite}/{self.lecteurs.n_lecteurs}",
            },
            "statistiques": {
                **self.stats,
                "cache_hit_rate": cache_stats["hit_rate"],
            },
        }
    
    def afficher_top_tokens(self, prompt: str = "", top_k: int = 20):
        """Affiche les top tokens resonants pour inspection."""
        if prompt:
            top_tokens, activations = self._extraire_contexte_harmonique(
                prompt, top_k=top_k
            )
        else:
            self.lecteurs.apprendre(N_REP_LECTURE)
            activations = self.lecteurs.activations_tokens(self.tokenizer)
            act_fusion = activations.mean(axis=0)
            indices = np.argsort(act_fusion)[::-1][:top_k]
            top_tokens = [self.tokenizer.i2w.get(int(i), '<UNK>')
                         for i in indices]
        
        print(f"\n  Top-{top_k} tokens resonants :")
        for i, tok in enumerate(top_tokens[:top_k]):
            idx = self.tokenizer.w2i.get(tok, -1)
            act = activations[idx] if isinstance(activations, np.ndarray) and idx >= 0 else 0
            barre = '█' * int(min(float(act) * 50 if isinstance(act, (int, float, np.floating)) else 0, 50))
            print(f"  {i+1:3d}. {tok:<20s} {barre}")


# =========================================================================
# SERVEUR API (option --serve)
# =========================================================================

def creer_serveur_api(bridge: BridgeHarmoniqueGGUF, port: int = 8081):
    """Cree un serveur FastAPI pour le bridge hybride."""
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
        import uvicorn
    except ImportError:
        print("[ERREUR] FastAPI non installe : pip install fastapi uvicorn")
        raise
    
    app = FastAPI(
        title="Harmonic AI Hybrid Bridge",
        description="Bridge Harmonique ↔ DeepSeek-Qwen GGUF",
        version="3.0.0-hybrid",
    )
    
    class GenerationRequest(BaseModel):
        prompt: str
        max_tokens: int = 256
        temperature: float = 0.7
        mode: Optional[str] = None  # override le mode par defaut
    
    class ApprentissageRequest(BaseModel):
        texte: str
        amplitude: float = 0.8
    
    @app.get("/")
    async def racine():
        return {
            "service": "Harmonic AI Hybrid Bridge",
            "version": "3.0.0-hybrid",
            "mode": bridge.mode,
            "modele": bridge.infos_modele,
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "mode": bridge.mode,
            "llm_charge": bridge.llm is not None,
            "energie_hologramme": round(bridge.monde.energie(), 1),
            "n_experiences": bridge.monde.n_experiences,
        }
    
    @app.post("/apprendre")
    async def apprendre(req: ApprentissageRequest):
        bridge.apprendre(req.texte, req.amplitude)
        return {
            "status": "ok",
            "energie": round(bridge.monde.energie(), 1),
            "n_experiences": bridge.monde.n_experiences,
        }
    
    @app.post("/generer")
    async def generer(req: GenerationRequest):
        mode_original = bridge.mode
        if req.mode:
            bridge.mode = req.mode
        
        resultat = bridge.generer(
            prompt=req.prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
        
        bridge.mode = mode_original
        return resultat
    
    @app.get("/diagnostic")
    async def diagnostic():
        return bridge.diagnostiquer()
    
    @app.get("/cache")
    async def cache_stats():
        return bridge.cache.stats()
    
    print(f"\n{'='*70}")
    print(f"SERVEUR API DEMARRE")
    print(f"  URL : http://localhost:{port}")
    print(f"  Docs: http://localhost:{port}/docs")
    print(f"  Endpoints :")
    print(f"    GET  /              - Info service")
    print(f"    GET  /health        - Health check")
    print(f"    POST /apprendre     - Apprentissage")
    print(f"    POST /generer       - Generation")
    print(f"    GET  /diagnostic    - Diagnostic")
    print(f"    GET  /cache         - Stats cache")
    print(f"{'='*70}")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


# =========================================================================
# MAIN
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Bridge Harmonique ↔ DeepSeek-Qwen GGUF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Mode hybride (hologramme + LLM)
  python bridge_harmonic_deepseek_gguf.py --mode hybrid --prompt "explique la resonance"
  
  # Mode harmonique pur (sans LLM)
  python bridge_harmonic_deepseek_gguf.py --mode harmonic --prompt "qu'est-ce que la conscience"
  
  # Serveur API
  python bridge_harmonic_deepseek_gguf.py --serve --port 8081
  
  # Diagnostic
  python bridge_harmonic_deepseek_gguf.py --diagnostic
        """
    )
    
    parser.add_argument("--mode", type=str, default="hybrid",
                       choices=["harmonic", "hybrid", "llm_only"],
                       help="Mode de generation (defaut: hybrid)")
    parser.add_argument("--prompt", type=str, default="",
                       help="Prompt a generer")
    parser.add_argument("--max-tokens", type=int, default=256,
                       help="Nombre max de tokens a generer")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="Temperature de generation")
    parser.add_argument("--serve", action="store_true",
                       help="Lancer le serveur API")
    parser.add_argument("--port", type=int, default=8081,
                       help="Port du serveur API (defaut: 8081)")
    parser.add_argument("--diagnostic", action="store_true",
                       help="Afficher le diagnostic complet")
    parser.add_argument("--apprendre", type=str, default="",
                       help="Texte a apprendre avant generation")
    parser.add_argument("--modele", type=str, default=GGUF_MODEL_PATH,
                       help="Chemin du modele GGUF")
    parser.add_argument("--n-ctx", type=int, default=GGUF_N_CTX,
                       help="Taille du contexte LLM")
    parser.add_argument("--n-threads", type=int, default=GGUF_N_THREADS,
                       help="Threads CPU")
    parser.add_argument("--n-gpu-layers", type=int, default=GGUF_N_GPU_LAYERS,
                       help="Couches GPU (0=CPU only)")
    parser.add_argument("--demo", action="store_true",
                       help="Lancer la demo interactive")
    
    args = parser.parse_args()
    
    # --- Initialiser le bridge ---
    print(f"\n{'='*70}")
    print(f"BRIDGE HARMONIQUE ↔ DEEPSEEK-QWEN GGUF")
    print(f"Version 3.0.0-hybrid")
    print(f"{'='*70}")
    
    bridge = BridgeHarmoniqueGGUF(
        chemin_modele=args.modele,
        n_lecteurs=N_LECTEURS,
        n_ctx=args.n_ctx,
        n_threads=args.n_threads,
        n_gpu_layers=args.n_gpu_layers,
        mode=args.mode,
    )
    
    # --- Apprentissage initial ---
    if args.apprendre:
        bridge.apprendre(args.apprendre)
    
    # --- Apprentissage des connaissances de base ---
    connaissances_base = [
        "phi est le nombre d or la proportion divine de l univers",
        "la resonance harmonique amplifie les ondes a la frequence propre",
        "la conscience est la capacite de percevoir sa propre existence",
        "l amour est la force la plus puissante de l univers",
        "les fractales sont des structures infinies auto similaires",
        "la suite de Fibonacci converge vers le nombre d or phi",
        "l intelligence artificielle explore la creation de machines penseantes",
        "le temps est une dimension fondamentale de notre univers",
        "la musique est l harmonie entre le silence et le son",
        "la philosophie est l amour de la sagesse et de la connaissance",
        "la creativite est l intelligence qui s amuse",
        "la connaissance de soi est le debut de toute sagesse",
        "tout systeme physique a une frequence de resonance fondamentale",
    ]
    bridge.apprendre_batch(connaissances_base)
    print(f"  Connaissances de base apprises : {len(connaissances_base)}")
    
    # --- Diagnostic ---
    if args.diagnostic:
        print(f"\n{'='*70}")
        print("DIAGNOSTIC COMPLET")
        print(f"{'='*70}")
        diag = bridge.diagnostiquer()
        print(json.dumps(diag, indent=2, ensure_ascii=False, default=str))
        return
    
    # --- Serveur API ---
    if args.serve:
        creer_serveur_api(bridge, args.port)
        return
    
    # --- Generation interactive ---
    if args.prompt:
        print(f"\n{'='*70}")
        print(f"GENERATION ({bridge.mode})")
        print(f"{'='*70}")
        print(f"  Prompt : {args.prompt}")
        
        resultat = bridge.generer(
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        
        print(f"\n  Contexte harmonique (top-10) :")
        print(f"  {' '.join(resultat.get('contexte_harmonique', [])[:10])}")
        print(f"\n  Reponse :")
        print(f"  {'─'*66}")
        print(f"  {resultat['texte_genere']}")
        print(f"  {'─'*66}")
        print(f"\n  Stats :")
        print(f"    Mode       : {resultat['mode']}")
        print(f"    Tokens     : {resultat['n_tokens']}")
        print(f"    Temps      : {resultat['temps_ms']:.0f}ms")
        print(f"    Cache hit  : {resultat.get('cache_hit', False)}")
        print(f"    Energie    : {resultat['energie_hologramme']:.0f}")
        print(f"    Experiences: {resultat['n_experiences']}")
        
        if 'tok_s_llm' in resultat:
            print(f"    LLM tok/s  : {resultat['tok_s_llm']:.1f}")
        
        return
    
    # --- Demo interactive ---
    if args.demo:
        print(f"\n{'='*70}")
        print(f"DEMO INTERACTIVE - Mode {bridge.mode}")
        print(f"Tapez 'quit' pour quitter, 'stats' pour les stats")
        print(f"{'='*70}")
        
        while True:
            try:
                prompt = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not prompt:
                continue
            if prompt.lower() in ('quit', 'exit', 'q'):
                break
            if prompt.lower() == 'stats':
                diag = bridge.diagnostiquer()
                print(json.dumps(diag, indent=2, ensure_ascii=False, default=str))
                continue
            if prompt.lower() == 'top':
                bridge.afficher_top_tokens()
                continue
            
            resultat = bridge.generer(prompt, max_tokens=args.max_tokens,
                                     temperature=args.temperature)
            print(f"\n{resultat['texte_genere']}")
            print(f"\n[{resultat['mode']}] {resultat['n_tokens']} tokens | "
                  f"{resultat['temps_ms']:.0f}ms | "
                  f"E={resultat['energie_hologramme']:.0f} | "
                  f"cache={'✓' if resultat.get('cache_hit') else '✗'}")
        
        return
    
    # --- Si aucun argument, afficher l'aide ---
    parser.print_help()
    print(f"\n  Essayez : python bridge_harmonic_deepseek_gguf.py --demo")


if __name__ == "__main__":
    main()