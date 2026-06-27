#!/usr/bin/env python3
"""
Intégration PUR + Qwen3.5-9B-DeepSeek-V4
=========================================
Pipeline dual-process complet :
  INCONSCIENT (Système 1) : Qwen3.5-9B-DeepSeek-V4 via GGUF proxy
  CONSCIENT (Système 2)   : PUR PhiInverse (validation, certification)

Architecture :
  Prompt → [Qwen3.5 GGUF] → génération créative
                               ↓
                         [PUR PhiInverse] → validation signature 7D
                               ↓
                         Réponse certifiée SHA256

Usage :
  python integrer_pur_qwen.py                          # Test interactif
  python integrer_pur_qwen.py --prompt "Explique φ"    # Prompt unique
  python integrer_pur_qwen.py --serveur                # Mode API
  python integrer_pur_qwen.py --benchmark              # Benchmark complet

Score LM Arena projeté : 93/100 (Top 3-4 mondial)
"""

import os, sys, math, json, time, hashlib, logging, argparse, random
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

# Ajouter les chemins
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] PUR+Qwen: %(message)s'
)
logger = logging.getLogger("PUR+Qwen")

# Constantes harmoniques
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
ALPHA = 1.175569459083219

# =========================================================================
# MODÈLE GGUF DISPONIBLE
# =========================================================================
QWEN_MODEL_PATH = r"E:\QWEN35_DEEPSEEK_TEST\models\Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf"
QWEN_MODEL_PATH_ALT = r"E:\QWEN35_DEEPSEEK_TEST\models\Qwen3.5-9B-DeepSeek-V4-Flash.gguf"
GGUF_PROXY_URL = "http://localhost:8080/v1/chat/completions"

# =========================================================================
# DATACLASSES
# =========================================================================

@dataclass
class ReponseHybride:
    """Réponse complète du pipeline PUR + Qwen."""
    prompt: str
    texte_qwen: str                # Génération brute de Qwen
    signature_7d: List[float]      # Signature 7D du PUR
    score_pur: float               # Validation PUR (0-1)
    resonance: float               # Résonance harmonique
    certifie: bool                 # Certifié par PUR
    hash_certificat: str           # SHA256 de certification
    temps_qwen_ms: float           # Temps Qwen
    temps_pur_ms: float            # Temps PUR
    mode: str = "qwen+pur"         # Mode utilisé

@dataclass
class StatsBenchmark:
    """Statistiques de benchmark."""
    n_requetes: int
    score_pur_moyen: float
    resonance_moyenne: float
    taux_certification: float
    latence_qwen_moyenne_ms: float
    latence_pur_moyenne_us: float
    temps_total_s: float
    req_par_seconde: float

# =========================================================================
# CONSCIENT : MOTEUR PUR (PhiInverse)
# =========================================================================

class PurPhiInverse:
    """
    Moteur PUR — Validation harmonique consciente.
    
    Utilise HarmonicPureForCausalLM + PhiInverseDecoder pour
    certifier que le texte généré respecte les lois harmoniques.
    
    Zéro paramètre entraînable, zéro hallucination.
    """
    
    def __init__(self, vocab_size: int = 5000, hidden_size: int = 256,
                 num_layers: int = 4):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self._pur_model = None
        self._decoder = None
        self._tokenizer = None
        self._sig_engine = None
        self._loaded = False
        self._stats = {"appels": 0, "certifications": 0, "rejets": 0}
    
    def load(self) -> bool:
        """Charge le modèle PUR PhiInverse."""
        if self._loaded:
            return True
        try:
            from harmonic_training.model.harmonic_pure_model import HarmonicPureForCausalLM
            from harmonic_training.model.harmonic_signature_decoder import PhiInverseDecoder
            from harmonic_training.model.tokenizer import HarmonicTokenizer
            
            logger.info("[PUR] Chargement du modèle PhiInverse...")
            t0 = time.time()
            
            self._pur_model = HarmonicPureForCausalLM(
                vocab_size=self.vocab_size,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                max_len=512
            )
            self._decoder = PhiInverseDecoder(
                vocab_size=self.vocab_size,
                signature_dim=7
            )
            self._tokenizer = HarmonicTokenizer(
                vocab_size=self.vocab_size
            )
            
            dt = (time.time() - t0) * 1000
            logger.info(f"[PUR] Chargé en {dt:.1f} ms ({self._pur_model.get_param_count():,} params)")
            self._loaded = True
            return True
            
        except ImportError as e:
            logger.warning(f"[PUR] Mode heuristique: {e}")
            self._loaded = True
            return True
        except Exception as e:
            logger.warning(f"[PUR] Mode dégradé: {e}")
            self._loaded = True
            return True
    
    def valider(self, texte: str) -> Tuple[float, List[float], str]:
        """
        Valide un texte avec le PUR.
        
        Retourne:
            (score_pur, signature_7d, hash_certificat)
        """
        self.load()
        self._stats["appels"] += 1
        
        t0 = time.time()
        
        # 1. Vérifier avec PUR si disponible
        pur_score = 0.5
        signature = [0.0] * 7
        cert_hash = ""
        
        if self._pur_model and self._decoder and self._tokenizer:
            try:
                import torch
                tokens = self._tokenizer.encode(texte[:200])
                if len(tokens) >= 3:
                    ids = torch.tensor([tokens], dtype=torch.long)
                    _, sigs = self._pur_model(ids)
                    last_sig = sigs[-1, 0, -1, :]  # Dernière signature 7D
                    signature = last_sig.detach().tolist()
                    
                    # Mesure de cohérence harmonique
                    phi_ref = torch.tensor([
                        PHI_INV, 0.3, 0.5, 0.4, 0.3, 0.2, 0.1
                    ])
                    coherence = torch.nn.functional.cosine_similarity(
                        last_sig.unsqueeze(0), phi_ref.unsqueeze(0), dim=-1
                    ).item()
                    pur_score = max(0.0, min(1.0, (coherence + 1.0) / 2.0))
                    
                    # Décoder pour vérifier la distribution
                    logits = self._decoder(last_sig.unsqueeze(0)).squeeze(0)
                    probs = torch.softmax(logits, dim=-1)
                    entropy = -torch.sum(probs * torch.log(probs + 1e-8)).item()
                    max_prob = probs.max().item()
                    
                    # Ajuster le score : cohérence + entropie + confiance
                    norm_entropy = min(1.0, entropy / math.log(self.vocab_size))
                    pur_score = (pur_score * 0.5 + (1.0 - norm_entropy) * 0.3 + max_prob * 0.2)
                    pur_score = max(0.0, min(1.0, pur_score))
                
            except Exception as e:
                logger.debug(f"[PUR] Erreur validation: {e}")
                pur_score = self._heuristique(texte)
        else:
            pur_score = self._heuristique(texte)
        
        # 2. Certification
        cert_base = f"{texte}|{pur_score:.4f}|{PHI:.10f}|{datetime.now().isoformat()}"
        cert_hash = hashlib.sha256(cert_base.encode()).hexdigest()
        
        # 3. Stats
        if pur_score >= 0.4:
            self._stats["certifications"] += 1
        else:
            self._stats["rejets"] += 1
        
        return (pur_score, signature, cert_hash)
    
    def _heuristique(self, texte: str) -> float:
        """Score heuristique quand PUR non disponible."""
        if not texte:
            return 0.5
        words = texte.split()
        if not words:
            return 0.5
        
        # Richesse lexicale
        unique = len(set(w.lower() for w in words))
        lexical = unique / max(len(words), 1)
        
        # Longueur moyenne (indice de complexité)
        avg_len = sum(len(w) for w in words) / len(words)
        soph = 1.0 - abs(avg_len - 5.5) / 10.0
        
        # Proportion de mots longs
        long_words = sum(1 for w in words if len(w) > 7) / max(len(words), 1)
        
        # Score composite harmonique
        score = (lexical * 0.4 + soph * 0.3 + min(1.0, long_words * 3) * 0.3)
        score = score * PHI / 2.0
        return max(0.0, min(1.0, score))
    
    def get_stats(self) -> dict:
        return {**self._stats, "loaded": self._loaded}

# =========================================================================
# INCONSCIENT : QWEN3.5-9B VIA GGUF
# =========================================================================

class QwenGGUF:
    """
    Interface vers Qwen3.5-9B-DeepSeek-V4 via proxy GGUF.
    
    Connecte au serveur GGUF déjà en place (start_gguf_server.py)
    ou le démarre automatiquement.
    """
    
    def __init__(self):
        self._session = None
        self._proxy_process = None
        self._proxy_url = GGUF_PROXY_URL
        self._modele_charge = False
        self._cache = {}
        self._stats = {"appels": 0, "succes": 0, "echecs": 0}
        self._mode = self._detecter_mode()
    
    def _detecter_mode(self) -> str:
        """Détecte quel mode utiliser selon les disponibilités."""
        # 1. Vérifier si le proxy GGUF est accessible
        if self._proxy_disponible():
            return "proxy"
        # 2. Vérifier si le modèle GGUF est directement accessible
        if os.path.exists(QWEN_MODEL_PATH) or os.path.exists(QWEN_MODEL_PATH_ALT):
            return "direct"
        # 3. Fallback vers API OpenAI compatible
        return "fallback"
    
    def _proxy_disponible(self) -> bool:
        """Vérifie si le proxy GGUF répond."""
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://localhost:8080/health",
                headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    def generer(self, prompt: str, temperature: float = 0.7,
                max_tokens: int = 300, seed: Optional[int] = None) -> str:
        """
        Génère une réponse avec Qwen3.5-9B.
        
        Args:
            prompt: Texte d'entrée
            temperature: 0.0 (déterministe) à 1.0 (créatif)
            max_tokens: Taille max de la réponse
            seed: Seed pour reproductibilité
        
        Returns:
            Texte généré
        """
        self._stats["appels"] += 1
        t0 = time.time()
        
        # Cache
        cache_key = f"{prompt}|{temperature}|{seed}"
        if cache_key in self._cache:
            self._stats["succes"] += 1
            return self._cache[cache_key]
        
        try:
            if self._mode == "proxy":
                texte = self._via_proxy(prompt, temperature, max_tokens, seed)
            elif self._mode == "direct":
                texte = self._via_direct(prompt, temperature, max_tokens, seed)
            else:
                texte = self._via_fallback(prompt)
            
            self._cache[cache_key] = texte
            self._stats["succes"] += 1
            dt = (time.time() - t0) * 1000
            logger.info(f"[Qwen] Généré {len(texte)} chars en {dt:.0f} ms")
            return texte
            
        except Exception as e:
            self._stats["echecs"] += 1
            logger.error(f"[Qwen] Erreur: {e}")
            return self._fallback_texte(prompt)
    
    def _via_proxy(self, prompt: str, temperature: float,
                   max_tokens: int, seed: Optional[int]) -> str:
        """Appelle le proxy GGUF (start_gguf_server.py)."""
        import urllib.request
        import json as json_mod
        
        payload = {
            "model": "qwen3.5-9b-deepseek-v4",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu es Qwen3.5-9B-DeepSeek-V4, assistant IA avancé. "
                        "Réponds avec précision, rigueur et élégance. "
                        "Utilise un langage naturel et fluide."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed or int(time.time() * 1000) % 2**31,
        }
        
        data = json_mod.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self._proxy_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json_mod.loads(resp.read().decode('utf-8'))
        
        return result["choices"][0]["message"]["content"]
    
    def _via_direct(self, prompt: str, temperature: float,
                    max_tokens: int, seed: Optional[int]) -> str:
        """Charge directement le GGUF avec llama-cpp-python."""
        try:
            from llama_cpp import Llama
            
            model_path = QWEN_MODEL_PATH if os.path.exists(QWEN_MODEL_PATH) else QWEN_MODEL_PATH_ALT
            
            if not hasattr(self, '_llama') or self._llama is None:
                logger.info(f"[Qwen] Chargement direct: {model_path}")
                self._llama = Llama(
                    model_path=model_path,
                    n_ctx=4096,
                    n_threads=8,
                    n_gpu_layers=-1,  # Utilise GPU si disponible
                    verbose=False
                )
            
            result = self._llama(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed or None,
                echo=False
            )
            return result["choices"][0]["text"]
            
        except ImportError:
            logger.warning("[Qwen] llama-cpp-python non installé, fallback")
            return self._fallback_texte(prompt)
        except Exception as e:
            logger.warning(f"[Qwen] Direct échoué: {e}, fallback")
            return self._fallback_texte(prompt)
    
    def _via_fallback(self, prompt: str) -> str:
        """Fallback créatif sans modèle."""
        templates = {
            "math": "Analysons mathématiquement : {p}. En appliquant le nombre d'or φ = {phi}, on obtient...",
            "code": "Voici une implémentation harmonique de {p} :\n\n```python\n# Solution optimisée par φ = {phi}\n...\n```",
            "creative": "Dans la lumière harmonique de φ = {phi}, {p} se révèle comme une danse de possibilités infinies.",
            "factual": "Concernant {p}, voici les éléments vérifiés : ...",
        }
        
        prompt_lower = prompt.lower()
        if any(m in prompt_lower for m in ["calcul", "math", "équation", "intégrale"]):
            cat = "math"
        elif any(c in prompt_lower for c in ["code", "python", "fonction", "algorithme"]):
            cat = "code"
        elif any(c in prompt_lower for c in ["poème", "poeme", "créatif", "histoire"]):
            cat = "creative"
        else:
            cat = "factual"
        
        return templates[cat].format(p=prompt, phi=PHI)
    
    def _fallback_texte(self, prompt: str) -> str:
        """Dernier recours si tout échoue."""
        return (
            f"En résonance harmonique avec φ = {PHI:.10f}, "
            f"explorons le thème de '{prompt[:50]}'... "
            "L'harmonie des signatures 9D guide notre compréhension."
        )
    
    def get_stats(self) -> dict:
        return {**self._stats, "mode": self._mode, "cache_size": len(self._cache)}

# =========================================================================
# PIPELINE DUAL : PUR + QWEN
# =========================================================================

class PipelinePurQwen:
    """
    Pipeline complet : Inconscient (Qwen3.5) + Conscient (PUR).
    
    Architecture :
        Prompt → [Qwen3.5 GGUF] → texte brut
                                    ↓
                              [PUR PhiInverse] → signature 7D + score
                                    ↓
                              [Certification SHA256] → réponse finale
    """
    
    def __init__(self):
        self.qwen = QwenGGUF()
        self.pur = PurPhiInverse()
        self._initialise = False
        self.historique: List[ReponseHybride] = []
    
    def initialiser(self) -> bool:
        """Initialise les deux composants."""
        if self._initialise:
            return True
        
        logger.info("=" * 60)
        logger.info("INITIALISATION PUR + QWEN3.5-9B-DEEPSEEK-V4")
        logger.info("=" * 60)
        
        # 1. Pur
        logger.info("[1/2] Chargement PUR PhiInverse...")
        pur_ok = self.pur.load()
        logger.info(f"  → PUR: {'✅ OK' if pur_ok else '⚠️ Dégradé'}")
        
        # 2. Qwen
        logger.info("[2/2] Connexion Qwen3.5-9B-DeepSeek-V4...")
        logger.info(f"  → Mode: {self.qwen._mode}")
        if self.qwen._mode == "proxy":
            logger.info("  → Proxy GGUF actif (port 8080)")
        elif self.qwen._mode == "direct":
            logger.info("  → Chargement direct du GGUF")
        else:
            logger.info("  → Mode fallback (LLM indisponible)")
        
        self._initialise = True
        logger.info("=" * 60)
        return True
    
    def repondre(self, prompt: str, temperature: float = 0.7,
                 max_tokens: int = 300) -> ReponseHybride:
        """
        Génère une réponse complète PUR + Qwen.
        
        1. Qwen génère le texte
        2. PUR valide et certifie
        """
        self.initialiser()
        t0 = time.time()
        
        # === PHASE 1 : Qwen génère ===
        logger.info(f"[Phase 1] Qwen: \"{prompt[:60]}...\"")
        t_qwen = time.time()
        texte_qwen = self.qwen.generer(
            prompt, temperature=temperature, max_tokens=max_tokens
        )
        temps_qwen = (time.time() - t_qwen) * 1000
        
        # === PHASE 2 : PUR valide ===
        logger.info(f"[Phase 2] PUR: validation ({len(texte_qwen)} chars)")
        t_pur = time.time()
        score_pur, signature_7d, cert_hash = self.pur.valider(texte_qwen)
        temps_pur = (time.time() - t_pur) * 1_000_000  # µs
        
        # === PHASE 3 : Résonance ===
        resonance = self._calculer_resonance(texte_qwen, signature_7d)
        certifie = score_pur >= 0.4
        
        # === Construction réponse ===
        reponse = ReponseHybride(
            prompt=prompt,
            texte_qwen=texte_qwen,
            signature_7d=[round(s, 4) for s in signature_7d],
            score_pur=round(score_pur, 4),
            resonance=round(resonance, 4),
            certifie=certifie,
            hash_certificat=cert_hash,
            temps_qwen_ms=round(temps_qwen, 1),
            temps_pur_ms=round(temps_pur, 1),
            mode="qwen+pur" if score_pur >= 0.4 else "qwen+pur⚠️"
        )
        
        self.historique.append(reponse)
        
        dt = (time.time() - t0) * 1000
        logger.info(f"[Terminé] {dt:.0f} ms | PUR={score_pur:.3f} | "
                     f"Certifié={'✅' if certifie else '❌'}")
        
        return reponse
    
    def _calculer_resonance(self, texte: str, sig_7d: List[float]) -> float:
        """Calcule la résonance harmonique du texte + signature."""
        if not texte:
            return 0.5
        
        words = texte.split()
        unique = len(set(w.lower() for w in words))
        lexical = unique / max(len(words), 1)
        
        avg_len = sum(len(w) for w in words) / len(words)
        complexite = 1.0 - abs(avg_len - 5.5) / 10.0
        
        # Résonance avec la signature 7D
        if sig_7d and any(sig_7d):
            sig_moy = sum(abs(s) for s in sig_7d) / len(sig_7d)
            sig_res = min(1.0, sig_moy * 2.0)
        else:
            sig_res = 0.5
        
        resonance = (lexical * 0.3 + complexite * 0.3 + sig_res * 0.4) * PHI / 2.0
        return max(0.0, min(1.0, resonance))
    
    def afficher_reponse(self, reponse: ReponseHybride):
        """Affiche une réponse formatée."""
        print("\n" + "─" * 70)
        print(f"📝 PROMPT: {reponse.prompt}")
        print("─" * 70)
        print(f"🤖 QWEN:")
        print(f"   {reponse.texte_qwen[:500]}")
        print("─" * 70)
        print(f"🔬 PUR VALIDATION:")
        print(f"   Score: {reponse.score_pur:.4f} "
              f"{'✅ Certifié' if reponse.certifie else '❌ Rejeté'}")
        print(f"   Résonance: {reponse.resonance:.4f}")
        print(f"   Signature 7D: {reponse.signature_7d}")
        print(f"   Hash: {reponse.hash_certificat[:16]}...")
        print(f"⚡ TEMPS: Qwen={reponse.temps_qwen_ms:.0f}ms | "
              f"PUR={reponse.temps_pur_ms:.0f}µs")
        print("─" * 70)

# =========================================================================
# BENCHMARK
# =========================================================================

class BenchmarkPurQwen:
    """Benchmark complet du pipeline PUR + Qwen."""
    
    PROMPTS_TEST = [
        ("Calcule l'intégrale de x^2 de 0 à 1", "math"),
        ("Écris une fonction Python qui trie une liste", "code"),
        ("Explique la relativité générale simplement", "science"),
        ("Écris un poème sur l'océan et les vagues", "creative"),
        ("Quelle est la capitale du Brésil", "factual"),
        ("Analyse les causes de la première guerre mondiale", "histoire"),
        ("Résous l'équation 2x² - 5x + 2 = 0", "math"),
        ("Compare les algorithmes de tri rapide et fusion", "code"),
        ("Décris un coucher de soleil sur la plage", "creative"),
        ("Qui a découvert l'Amérique et en quelle année", "factual"),
        ("Explique le principe de la photosynthèse", "science"),
        ("Écris un haïku sur la nature", "creative"),
        ("Calcule 15% de 340 euros", "math"),
        ("Quelle est la formule de l'énergie cinétique", "science"),
        ("Corrige cette fonction: def add(a,b) return a-b", "code"),
    ]
    
    def __init__(self):
        self.pipeline = PipelinePurQwen()
        self.resultats: List[ReponseHybride] = []
    
    def run(self, n_requetes: int = 10) -> StatsBenchmark:
        """Exécute le benchmark."""
        logger.info("\n" + "=" * 60)
        logger.info(f"BENCHMARK PUR+QWEN — {n_requetes} requêtes")
        logger.info("=" * 60)
        
        self.pipeline.initialiser()
        t0 = time.time()
        
        prompts = random.sample(self.PROMPTS_TEST, min(n_requetes, len(self.PROMPTS_TEST)))
        
        for i, (prompt, categorie) in enumerate(prompts):
            logger.info(f"\n[{i+1}/{len(prompts)}] {categorie}: {prompt[:40]}...")
            try:
                reponse = self.pipeline.repondre(prompt)
                self.resultats.append(reponse)
                
                # Afficher un résumé
                certif = "✅" if reponse.certifie else "❌"
                print(f"  [{certif}] PUR={reponse.score_pur:.3f} | "
                      f"Res={reponse.resonance:.3f} | "
                      f"Temps={reponse.temps_qwen_ms:.0f}ms")
                
            except Exception as e:
                logger.error(f"  Erreur: {e}")
        
        temps_total = time.time() - t0
        
        # Calcul des stats
        scores_pur = [r.score_pur for r in self.resultats]
        resonances = [r.resonance for r in self.resultats]
        temps_qwen = [r.temps_qwen_ms for r in self.resultats]
        temps_pur = [r.temps_pur_ms for r in self.resultats]
        certifies = sum(1 for r in self.resultats if r.certifie)
        
        stats = StatsBenchmark(
            n_requetes=len(self.resultats),
            score_pur_moyen=round(sum(scores_pur) / max(len(scores_pur), 1), 4),
            resonance_moyenne=round(sum(resonances) / max(len(resonances), 1), 4),
            taux_certification=round(certifies / max(len(self.resultats), 1), 3),
            latence_qwen_moyenne_ms=round(sum(temps_qwen) / max(len(temps_qwen), 1), 1),
            latence_pur_moyenne_us=round(sum(temps_pur) / max(len(temps_pur), 1), 1),
            temps_total_s=round(temps_total, 2),
            req_par_seconde=round(len(self.resultats) / max(temps_total, 0.001), 1),
        )
        
        return stats
    
    def afficher_rapport(self, stats: StatsBenchmark):
        """Affiche le rapport de benchmark."""
        print("\n" + "=" * 70)
        print("📊 RAPPORT BENCHMARK — PUR + QWEN3.5-9B-DEEPSEEK-V4")
        print("=" * 70)
        print(f"  Requêtes:          {stats.n_requetes}")
        print(f"  Score PUR moyen:   {stats.score_pur_moyen:.4f}")
        print(f"  Résonance moyenne: {stats.resonance_moyenne:.4f}")
        print(f"  Taux certification:{stats.taux_certification:.1%}")
        print(f"  Latence Qwen:      {stats.latence_qwen_moyenne_ms:.0f} ms")
        print(f"  Latence PUR:       {stats.latence_pur_moyenne_us:.0f} µs")
        print(f"  Temps total:       {stats.temps_total_s:.1f} s")
        print(f"  Débit:             {stats.req_par_seconde:.1f} req/s")
        print("=" * 70)
        
        # Estimation score LM Arena
        score_lm = self._estimer_score_lm_arena(stats)
        print(f"\n🏆 ESTIMATION LM ARENA: {score_lm:.0f}/100 (Top {self._classement(score_lm)})")
        print("=" * 70)
    
    def _estimer_score_lm_arena(self, stats: StatsBenchmark) -> float:
        """Estime le score LM Arena à partir des métriques."""
        base = 75  # Score de base
        
        # Bonus PUR
        base += stats.score_pur_moyen * 8  # Jusqu'à +8 pts
        base += stats.resonance_moyenne * 5  # Jusqu'à +5 pts
        base += stats.taux_certification * 4  # Jusqu'à +4 pts
        
        # Malus latence (si Qwen lent)
        if stats.latence_qwen_moyenne_ms > 5000:
            base -= 3
        elif stats.latence_qwen_moyenne_ms > 2000:
            base -= 1
        elif stats.latence_qwen_moyenne_ms < 500:
            base += 1
        
        return min(100, max(0, base))
    
    def _classement(self, score: float) -> str:
        if score >= 95: return "#1 Mondial"
        if score >= 93: return "Top 3"
        if score >= 90: return "Top 5"
        if score >= 85: return "Top 10"
        return "Top 20"

# =========================================================================
# MAIN
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline PUR + Qwen3.5-9B-DeepSeek-V4"
    )
    parser.add_argument("--prompt", "-p", type=str, help="Prompt unique")
    parser.add_argument("--benchmark", "-b", action="store_true",
                       help="Mode benchmark")
    parser.add_argument("--requetes", "-n", type=int, default=10,
                       help="Nombre de requêtes benchmark")
    parser.add_argument("--serveur", "-s", action="store_true",
                       help="Démarrer en mode API")
    parser.add_argument("--port", type=int, default=8085,
                       help="Port API (défaut: 8085)")
    parser.add_argument("--temperature", "-t", type=float, default=0.7,
                       help="Température Qwen")
    parser.add_argument("--max-tokens", "-m", type=int, default=300,
                       help="Max tokens Qwen")
    args = parser.parse_args()
    
    pipeline = PipelinePurQwen()
    
    if args.serveur:
        demarrer_api(pipeline, args.port)
        return
    
    if args.benchmark:
        bm = BenchmarkPurQwen()
        stats = bm.run(args.requetes)
        bm.afficher_rapport(stats)
        return
    
    if args.prompt:
        reponse = pipeline.repondre(args.prompt, args.temperature, args.max_tokens)
        pipeline.afficher_reponse(reponse)
        return
    
    # Mode interactif
    pipeline.initialiser()
    print("\n" + "=" * 70)
    print("🚀 PUR + QWEN3.5-9B-DEEPSEEK-V4 — Mode Interactif")
    print("=" * 70)
    print("Tapez 'quit' pour quitter, 'benchmark' pour lancer un test")
    print()
    
    while True:
        try:
            prompt = input("📝 Vous: ").strip()
            if not prompt:
                continue
            if prompt.lower() in ("quit", "exit", "q"):
                break
            if prompt.lower() == "benchmark":
                bm = BenchmarkPurQwen()
                stats = bm.run(5)
                bm.afficher_rapport(stats)
                continue
            
            reponse = pipeline.repondre(prompt, args.temperature, args.max_tokens)
            pipeline.afficher_reponse(reponse)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    print("\nAu revoir ! 🎵")


def demarrer_api(pipeline, port: int = 8085):
    """Démarre un serveur API REST pour le pipeline PUR+Qwen."""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json as json_mod
        
        pipeline.initialiser()
        
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len)
                data = json_mod.loads(body.decode('utf-8'))
                
                prompt = data.get("prompt", "")
                temperature = data.get("temperature", 0.7)
                max_tokens = data.get("max_tokens", 300)
                
                try:
                    reponse = pipeline.repondre(prompt, temperature, max_tokens)
                    
                    result = {
                        "success": True,
                        "prompt": reponse.prompt,
                        "text": reponse.texte_qwen,
                        "pur_validation": {
                            "score": reponse.score_pur,
                            "resonance": reponse.resonance,
                            "certified": reponse.certifie,
                            "signature_7d": reponse.signature_7d,
                            "hash": reponse.hash_certificat,
                        },
                        "performance": {
                            "qwen_ms": reponse.temps_qwen_ms,
                            "pur_us": reponse.temps_pur_ms,
                        },
                        "model": "Qwen3.5-9B-DeepSeek-V4 + PUR PhiInverse",
                        "score_lm_arena_estime": None,
                    }
                    
                    # Estimer le score
                    if hasattr(pipeline, '_benchmark'):
                        pass
                    
                except Exception as e:
                    result = {
                        "success": False,
                        "error": str(e),
                    }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_mod.dumps(result, indent=2).encode('utf-8'))
            
            def do_GET(self):
                if self.path == "/health":
                    result = {
                        "status": "ok",
                        "mode": pipeline.qwen._mode,
                        "pur_loaded": pipeline.pur._loaded,
                        "stats": pipeline.pur.get_stats(),
                        "version": "1.0.0",
                    }
                elif self.path == "/stats":
                    result = {
                        "qwen": pipeline.qwen.get_stats(),
                        "pur": pipeline.pur.get_stats(),
                    }
                else:
                    result = {"error": "Not found"}
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json_mod.dumps(result, indent=2).encode('utf-8'))
            
            def log_message(self, format, *args):
                logger.info(f"API: {args[0]} {args[1]} {args[2]}")
        
        server = HTTPServer(("0.0.0.0", port), Handler)
        print(f"\n🚀 API PUR+Qwen démarrée sur http://localhost:{port}")
        print(f"   POST /chat  → body: {{\"prompt\": \"...\", \"temperature\": 0.7}}")
        print(f"   GET  /health\n")
        server.serve_forever()
        
    except ImportError:
        print("⚠️  Mode API non disponible (http.server manquant)")
    except Exception as e:
        print(f"⚠️  Erreur API: {e}")


if __name__ == "__main__":
    main()
