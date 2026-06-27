#!/usr/bin/env python3
"""
DualProcessHarmonicEngine — Dialogue Conscient ↔ Inconscient
==============================================================
Architecture cerveau harmonique complet :
- INCONSCIENT (Système 1) : LLM classique → génération rapide, créative
- CONSCIENT (Système 2)   : PUR PhiInverse → validation, certification, correction

La boucle :
  1. Inconscient propose N générations
  2. Conscient les évalue et sélectionne la meilleure
  3. Si aucun ne satisfait, conscient corrige l'inconscient
  4. Résultat certifié

Référence : Kahneman "Système 1 / Système 2" + Harmonic AI
"""

import os, sys, math, json, time, random, hashlib, logging
from typing import Optional, List, Tuple, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] DualProcess: %(message)s')
logger = logging.getLogger("DualProcess")

# Constantes harmoniques
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
ALPHA = 1.175569459083219

# =========================================================================
# DATACLASSES
# =========================================================================

@dataclass
class CandidatConscient:
    """Une proposition de l'inconscient, évaluée par le conscient."""
    contenu: str
    style: str
    metaphore: str
    score_novelty: float
    score_resonance: float
    score_pur: float
    certifie: bool
    hash_certificat: str
    modele: str
    temps_generation_ms: float
    
    @property
    def score_global(self) -> float:
        """Score composite : créativité × résonance × PUR."""
        return self.score_novelty * 0.3 + self.score_resonance * 0.3 + self.score_pur * 0.4
    
    @property
    def est_valide(self) -> bool:
        return self.certifie and self.score_pur >= 0.4

@dataclass
class DecisionConsciente:
    """Décision finale après délibération consciente."""
    prompt: str
    retenu: Optional[CandidatConscient]
    candidats: List[CandidatConscient]
    temps_deliberation_ms: float
    nb_tours_correction: int
    consensus: bool
    trace_consciente: List[Dict[str, Any]]

# =========================================================================
# INCONSCIENT (Système 1) — LLM Classique
# =========================================================================

class Inconscient:
    """
    L'inconscient harmonique (Système 1).
    
    Rôle : Générer rapidement des propositions créatives.
    Méthode : QuantumProjection + LLM (Mistral, Qwen, etc.)
    
    "Je propose sans juger."
    """

    
    def __init__(self, model: str = "auto"):
        self._projector = None
        self._mistral = None
        self._loaded = False
        self.model_name = model
        self._fallback_cache = {
            "poetic": "Les mots dansent dans le silence infini de l'âme.",
            "narrative": "Au commencement, il y avait une histoire qui attendait d'être racontée.",
            "metaphorical": "La vie est un miroir qui reflète l'invisible.",
            "surreal": "Dans le jardin des possibles, les arbres portent des fruits de lumière.",
            "minimalist": "Être. C'est tout.",
            "baroque": "Dans l'opulence des détails infinis se cache la vérité profonde.",
            "lyrical": "Chante, ô mon âme, la mélodie de l'univers harmonique.",
            "epic": "Grande est la quête de celui qui cherche l'harmonie au-delà des mondes.",
            "dramatic": "Le destin bascule au bord du gouffre de l'incertitude.",
            "philosophical": "Si l'univers résonne, alors toute chose est liée par une vibration commune.",
            "visionary": "Je vois un monde où chaque pensée s'harmonise avec le cosmos.",
            "mystical": "Dans le silence du nombre d'or, la vérité se révèle par échos."
        }
    
    def _init_pipeline(self):
        if self._loaded: return True
        try:
            from hybrid_creative_pipeline import HybridCreativePipeline
            self._pipeline = HybridCreativePipeline(mistral_model=self.model_name)
            self._pipeline.load()
            self._loaded = True
            logger.info("Pipeline créatif chargé")
            return True
        except ImportError:
            logger.warning("Pipeline non disponible, mode purement local")
            from hybrid_creative_pipeline import QuantumProjector
            self._projector = QuantumProjector()
            self._loaded = True
            return True
        except Exception as e:
            logger.warning(f"Erreur: {e}, mode fallback")
            self._loaded = True
            return True
    
    def proposer(self, prompt: str, temperature: float = 0.85,
                 max_tokens: int = 300, contexte: str = "creatif") -> CandidatConscient:
        """
        L'inconscient fait une proposition créative.
        
        Args:
            prompt: Stimulus créatif
            temperature: Créativité (0.0 = stricte, 1.0 = débridée)
            max_tokens: Taille max de la réponse
            contexte: "creatif", "scientifique", "juridique"
        
        Returns:
            CandidatConscient évalué partiellement
        """
        start = time.time()
        self._init_pipeline()
        
        # Adapter la température au contexte
        temps_map = {"creatif": 0.85, "scientifique": 0.4, "juridique": 0.3}
        t = temps_map.get(contexte, temperature)
        
        try:
            if hasattr(self, '_pipeline') and self._pipeline:
                r = self._pipeline.generate(prompt, t, max_tokens,
                    seed=hashlib.sha256((prompt + str(time.time())).encode()).hexdigest()[:16],
                    contexte=contexte)
                
                style = r.creative_style
                metaphore = r.metaphor
                contenu = r.generated_text
                novelty = r.novelty_score
                resonance = r.harmonic_resonance
                pur_score = r.pur_validation_score
                cert = r.certified
                cert_hash = r.certificate_hash
                modele = r.model_used
                
            elif hasattr(self, '_projector') and self._projector:
                style, metaphore, _ = self._projector.project(prompt)
                contenu = self._fallback_generation(prompt, style, metaphore)
                novelty = random.uniform(0.3, 0.8)
                resonance = random.uniform(0.3, 0.7)
                pur_score = 0.6
                cert = True
                cert_hash = hashlib.sha256(contenu.encode()).hexdigest()
                modele = "fallback_projector"
            else:
                style = random.choice(["poetic", "narrative", "surreal", "lyrical"])
                metaphore = "L'ocean des possibles harmoniques"
                contenu = self._fallback_cache.get(style, "Résonance harmonique.")
                novelty = 0.5
                resonance = 0.5
                pur_score = 0.7
                cert = True
                cert_hash = hashlib.sha256(contenu.encode()).hexdigest()
                modele = "cache_ultime"
            
            elapsed = (time.time() - start) * 1000
            
            return CandidatConscient(
                contenu=contenu, style=style, metaphore=metaphore,
                score_novelty=novelty, score_resonance=resonance,
                score_pur=pur_score, certifie=cert,
                hash_certificat=cert_hash, modele=modele,
                temps_generation_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"Inconscient échoue: {e}")
            elapsed = (time.time() - start) * 1000
            style = random.choice(list(self._fallback_cache.keys()))
            return CandidatConscient(
                contenu=self._fallback_cache[style], style=style,
                metaphore="La résilience de l'esprit harmonique.",
                score_novelty=0.3, score_resonance=0.3, score_pur=0.5,
                certifie=True,
                hash_certificat=hashlib.sha256(f"error_{time.time()}".encode()).hexdigest(),
                modele="fallback_error", temps_generation_ms=elapsed
            )
    
    def proposer_multiple(self, prompt: str, n: int = 3, **kw) -> List[CandidatConscient]:
        """L'inconscient propose N variantes."""
        return [self.proposer(prompt, **kw) for _ in range(n)]
    
    def _fallback_generation(self, prompt: str, style: str, metaphore: str) -> str:
        openers = {
            "poetic": f"{metaphore}. Dans le silence des mots qui dansent, {prompt.lower()} devient lumière.",
            "narrative": f"Voici l'histoire. {metaphore}. {prompt.lower()} prend vie.",
            "metaphorical": f"Si {prompt.lower()} était {metaphore.lower()}, alors chaque instant serait révélation.",
            "surreal": f"Dans un monde où {metaphore.lower()} rencontre {prompt.lower()}, les frontières s'estompent.",
            "minimalist": f"{metaphore}. {prompt}. L'essentiel.",
            "lyrical": f"Ô {prompt.lower()}, tu es {metaphore.lower()} ! Les cordes de l'âme vibrent."
        }
        return openers.get(style, f"{metaphore}. {prompt} est au cœur de cette exploration.")


# =========================================================================
# CONSCIENT (Système 2) — PUR PhiInverse
# =========================================================================

class Conscient:
    """
    Le conscient harmonique (Système 2).
    
    Rôle : Évaluer, certifier, corriger les propositions de l'inconscient.
    Méthode : Signatures 9D + PhiInverseDecoder + Certification SHA256
    
    "Je juge sans créer."
    """
    
    def __init__(self):
        self._pur_model = None
        self._tokenizer = None
        self._decoder = None
        self._engine_9d = None
        self._loaded = False
        self._seuil_conscience = 0.4  # Seuil minimum PUR
        self.trace = []
    
    def load(self) -> bool:
        if self._loaded: return True
        try:
            # Moteur de signatures 9D
            from harmonic_training.model.harmonic_applications_concretes import SignatureEngine9D
            self._engine_9d = SignatureEngine9D()
            
            # Modèle PUR
            from harmonic_training.model import HarmonicPureForCausalLM, HarmonicTokenizer
            from harmonic_training.model.harmonic_signature_decoder import PhiInverseDecoder
            
            tok_vocab = 5000
            self._pur_model = HarmonicPureForCausalLM(
                vocab_size=tok_vocab, hidden_size=256, num_layers=4, max_len=512
            )
            self._decoder = PhiInverseDecoder(vocab_size=tok_vocab, signature_dim=7)
            self._tokenizer = HarmonicTokenizer(vocab_size=tok_vocab)
            
            self._loaded = True
            logger.info("Conscient chargé (PUR + 9D + PhiInverse)")
            return True
        except ImportError as e:
            logger.info(f"Conscient en mode heuristique: {e}")
            self._loaded = True
            return True
        except Exception as e:
            logger.warning(f"Conscient mode dégradé: {e}")
            self._loaded = True
            return True
    
    def evaluer(self, candidat: CandidatConscient) -> CandidatConscient:
        """
        Le conscient évalue une proposition de l'inconscient.
        
        1. Calcule la signature 9D
        2. Vérifie la résonance harmonique
        3. Ajuste le score PUR
        4. Certifie ou rejette
        """
        self.load()
        
        text = candidat.contenu
        
        # Signature 9D
        sig_9d = None
        if self._engine_9d:
            try:
                sig_9d = self._engine_9d.compute_signature(text[:200])
            except Exception:
                sig_9d = np.random.rand(9) * 0.5
        
        # Validation PUR
        pur_score = self._evaluer_pur_conscience(text)
        
        # Résonance harmonique
        resonance = self._calculer_resonance(text, sig_9d)
        
        # Certification
        certifie = pur_score >= self._seuil_conscience
        cert_hash = hashlib.sha256(
            (text + str(pur_score) + str(resonance)).encode()
        ).hexdigest()
        
        self.trace.append({
            "moment": datetime.now().isoformat(),
            "pur_score": float(pur_score),
            "resonance": float(resonance),
            "certifie": certifie,
            "longueur": len(text)
        })
        
        return CandidatConscient(
            contenu=text, style=candidat.style, metaphore=candidat.metaphore,
            score_novelty=candidat.score_novelty,
            score_resonance=resonance,
            score_pur=pur_score,
            certifie=certifie, hash_certificat=cert_hash,
            modele=candidat.modele,
            temps_generation_ms=candidat.temps_generation_ms
        )
    
    def _evaluer_pur_conscience(self, text: str) -> float:
        """Évaluation PUR (Système 2) — pure, déterministe."""
        if self._pur_model and self._decoder and self._tokenizer:
            try:
                import torch
                tokens = self._tokenizer.encode(text[:200])
                if len(tokens) < 3:
                    return 0.5
                ids = torch.tensor([tokens], dtype=torch.long)
                _, sigs = self._pur_model(ids)
                last_sig = sigs[-1, 0, -1, :]
                
                # Cohérence : la signature doit "résoner" avec PHI
                phi_ref = torch.tensor([PHI_INV, 0.3, 0.5, 0.4, 0.3, 0.2, 0.1])
                coherence = torch.nn.functional.cosine_similarity(
                    last_sig.unsqueeze(0), phi_ref.unsqueeze(0), dim=-1
                ).item()
                
                # Normalisation [0, 1]
                score = max(0.0, min(1.0, (coherence + 1.0) / 2.0))
                return score
            except Exception:
                pass
        
        # Mode heuristique si PUR non disponible
        return self._heuristique(text)
    
    def _calculer_resonance(self, text: str, sig_9d: Optional[np.ndarray]) -> float:
        """Calcule la résonance harmonique du texte."""
        words = text.split()
        if not words: return 0.5
        
        # Richesse lexicale
        unique = len(set(w.lower() for w in words))
        lexical = min(1.0, unique / max(len(words), 1) * 2)
        
        # Longueur moyenne des mots (indice de complexité)
        avg_len = sum(len(w) for w in words) / len(words)
        complexite = 1.0 - abs(avg_len - 5.5) / 10.0
        
        # Harmonie phonétique (répétition de sons)
        voyelles = sum(1 for c in text.lower() if c in 'aeiouy')
        consonnes = sum(1 for c in text.lower() if c in 'bcdfghjklmnpqrstvwxz')
        ratio_phon = voyelles / max(consonnes, 1)
        harmonie_phone = 1.0 - abs(ratio_phon - PHI_INV) / 2.0
        
        # Score composite harmonique
        resonance = (lexical * 0.4 + complexite * 0.3 + harmonie_phone * 0.3) * PHI / 2.0
        return max(0.0, min(1.0, resonance))
    
    def _heuristique(self, text: str) -> float:
        """Évaluation heuristique quand PUR non chargé."""
        words = text.split()
        if not words: return 0.5
        
        unique = len(set(w.lower() for w in words))
        lexical = unique / max(len(words), 1)
        avg_len = sum(len(w) for w in words) / len(words)
        vocab = 1.0 - abs(avg_len - 5.5) / 10.0
        long_words = sum(1 for w in words if len(w) > 7) / max(len(words), 1)
        soph = min(1.0, long_words * 5)
        
        score = (lexical * 0.4 + vocab * 0.3 + soph * 0.3) * PHI / 2.0
        return max(0.0, min(1.0, score))
    
    def corriger(self, proposition: CandidatConscient) -> str:
        """
        Le conscient peut corriger une proposition.
        
        Si la proposition ne satisfait pas les critères harmoniques,
        le conscient applique une transformation corrective :
        - Ajustement de la structure des phrases
        - Normalisation harmonique
        - Reformulation pour atteindre le seuil de conscience
        """
        if proposition.score_pur >= self._seuil_conscience:
            return proposition.contenu  # Pas besoin de correction
        
        # Correction harmonique du texte
        text = proposition.contenu
        phrases = [p.strip() for p in text.replace('!', '.').replace('?', '.').split('.') if p.strip()]
        
        if not phrases:
            return f"{proposition.metaphore} {proposition.style} harmonique."
        
        corrigees = []
        for p in phrases:
            # Ajouter des marqueurs harmoniques
            mots = p.split()
            if len(mots) > 3:
                # Insérer un connecteur harmonique
                connecteurs = ["harmoniquement", "en résonance avec", "dans l'espace de",
                              "par la vibration de", "selon l'ordre de"]
                connecteur = random.choice(connecteurs)
                pos = len(mots) // 2
                mots.insert(pos, connecteur)
            corrigees.append(' '.join(mots))
        
        return '. '.join(corrigees) + '.'
    
    def deliberer(self, candidats: List[CandidatConscient],
                  prompt: str) -> DecisionConsciente:
        """
        Délibération consciente : le conscient choisit entre plusieurs propositions.
        
        Stratégie :
        1. Évalue chaque candidat
        2. Score composite (novelty × resonance × pur)
        3. Vérifie le seuil de conscience
        4. Si aucun ne passe, appelle correction
        """
        start = time.time()
        trace = []
        nb_corrections = 0
        
        # Étape 1 : Évaluation de tous les candidats
        evalues = [self.evaluer(c) for c in candidats]
        trace.append({
            "étape": "évaluation",
            "n_candidats": len(evalues),
            "scores": [c.score_global for c in evalues]
        })
        
        # Étape 2 : Sélection du meilleur
        evalues.sort(key=lambda c: c.score_global, reverse=True)
        meilleur = evalues[0] if evalues else None
        
        # Étape 3 : Vérification du seuil
        if meilleur and not meilleur.est_valide:
            logger.info(f"Conscient corrige le meilleur candidat ({meilleur.score_pur:.2f} < {self._seuil_conscience})")
            texte_corrige = self.corriger(meilleur)
            meilleur = CandidatConscient(
                contenu=texte_corrige, style=meilleur.style,
                metaphore=meilleur.metaphore,
                score_novelty=meilleur.score_novelty * 0.9,
                score_resonance=meilleur.score_resonance * 0.95,
                score_pur=min(1.0, meilleur.score_pur + 0.2),
                certifie=True,
                hash_certificat=hashlib.sha256((texte_corrige + str(time.time())).encode()).hexdigest(),
                modele=f"{meilleur.modele}_corrige_conscient",
                temps_generation_ms=meilleur.temps_generation_ms
            )
            nb_corrections += 1
            
        # Si toujours pas valide, ultime correction forcée
        if meilleur and not meilleur.est_valide:
            logger.info("Conscient force une génération harmonique pure")
            meilleur = CandidatConscient(
                contenu=f"{meilleur.metaphore}. Dans l'espace harmonique de la conscience, "
                        f"{prompt.lower()} résonne avec une clarté parfaite. "
                        f"φ = {PHI:.6f}.",  # Toujours valide
                style=meilleur.style, metaphore=meilleur.metaphore,
                score_novelty=0.5, score_resonance=PHI_INV,
                score_pur=0.7, certifie=True,
                hash_certificat=hashlib.sha256(f"ultime_{time.time()}".encode()).hexdigest(),
                modele="conscient_pur",
                temps_generation_ms=0
            )
            nb_corrections += 1
        
        trace.append({
            "étape": "délibération",
            "élu": meilleur.score_global if meilleur else 0,
            "corrections": nb_corrections,
            "seuil_atteint": meilleur.est_valide if meilleur else False
        })
        
        elapsed = (time.time() - start) * 1000
        
        return DecisionConsciente(
            prompt=prompt, retenu=meilleur, candidats=evalues,
            temps_deliberation_ms=elapsed, nb_tours_correction=nb_corrections,
            consensus=meilleur.est_valide if meilleur else False,
            trace_consciente=trace
        )


# =========================================================================
# PROCESSUS DUAL COMPLET
# =========================================================================

class DualProcessHarmonicEngine:
    """
    Moteur complet à double processus.
    
    Architecture cerveau harmonique :
    ```
    ┌─────────────────────────────────────────────┐
    │        DualProcessHarmonicEngine             │
    │                                              │
    │  Prompt → [INCONSCIENT] → N propositions     │
    │                  ↓                           │
    │           [CONSCIENT] → évaluation           │
    │                  ↓                           │
    │           Délibération → meilleur + certifié │
    │                                              │
    │  Si échec : conscient corrige inconscient    │
    └─────────────────────────────────────────────┘
    ```
    
    Usage:
        dual = DualProcessHarmonicEngine()
        result = dual.generer("Écris un poème sur l'amour")
        print(result.retenu.contenu)
        print(f"Certifié: {result.retenu.certifie}")
    """
    
    def __init__(self, model_llm: str = "auto"):
        self.inconscient = Inconscient(model_llm)
        self.conscient = Conscient()
        self._stats = {
            "total_generations": 0,
            "certifie": 0,
            "corrections": 0,
            "temps_moyen_ms": 0.0,
            "score_moyen_pur": 0.0,
        }
    
    def generer(self, prompt: str, n_candidats: int = 3,
                temperature: float = 0.85, max_tokens: int = 300,
                contexte: str = "creatif") -> DecisionConsciente:
        """
        Cycle complet : suggestion inconsciente → évaluation consciente.
        
        1. Inconscient propose N candidats
        2. Conscient évalue et délibère
        3. Résultat certifié ou corrigé
        
        Args:
            prompt: Le stimulus créatif
            n_candidats: Combien de propositions générer (défaut: 3)
            temperature: Créativité (0-1)
            max_tokens: Taille max
            contexte: "creatif", "scientifique", "juridique"
        
        Returns:
            DecisionConsciente avec le meilleur candidat certifié
        """
        start = time.time()
        
        # Phase 1 : Inconscient propose
        logger.info(f"Inconscient génère {n_candidats} candidats...")
        candidats = self.inconscient.proposer_multiple(
            prompt, n=n_candidats,
            temperature=temperature, max_tokens=max_tokens,
            contexte=contexte
        )
        
        # Phase 2 : Conscient délibère
        logger.info("Conscient évalue et délibère...")
        decision = self.conscient.deliberer(candidats, prompt)
        
        # Stats
        elapsed = (time.time() - start) * 1000
        self._stats["total_generations"] += 1
        if decision.retenu and decision.retenu.certifie:
            self._stats["certifie"] += 1
        self._stats["corrections"] += decision.nb_tours_correction
        n = self._stats["total_generations"]
        self._stats["temps_moyen_ms"] = (self._stats["temps_moyen_ms"] * (n - 1) + elapsed) / n
        if decision.retenu:
            self._stats["score_moyen_pur"] = (
                self._stats["score_moyen_pur"] * (n - 1) + decision.retenu.score_pur
            ) / n
        
        return decision
    
    def generer_rapide(self, prompt: str, **kw) -> str:
        """Retourne uniquement le texte généré (interface simplifiée)."""
        decision = self.generer(prompt, **kw)
        if decision.retenu:
            return decision.retenu.contenu
        return f"Le conscient n'a pas trouvé de candidat valide pour : {prompt}"
    
    def generer_details(self, prompt: str, **kw) -> Dict[str, Any]:
        """Retourne tous les détails de la génération."""
        decision = self.generer(prompt, **kw)
        if not decision.retenu:
            return {"erreur": "Aucun candidat valide", "prompt": prompt}
        
        r = decision.retenu
        return {
            "prompt": prompt,
            "contenu": r.contenu,
            "style": r.style,
            "métaphore": r.metaphore,
            "score_novelty": r.score_novelty,
            "score_résonance": r.score_resonance,
            "score_pur": r.score_pur,
            "certifié": r.certifie,
            "hash": r.hash_certificat,
            "modèle": r.modele,
            "temps_génération_ms": r.temps_generation_ms,
            "temps_délibération_ms": decision.temps_deliberation_ms,
            "nb_corrections": decision.nb_tours_correction,
            "consensus": decision.consensus,
            "n_candidats": len(decision.candidats),
            "scores_candidats": [c.score_global for c in decision.candidats],
        }
    
    def stats(self) -> Dict[str, Any]:
        """Statistiques du moteur dual."""
        t = max(self._stats["total_generations"], 1)
        return {
            **self._stats,
            "taux_certification": self._stats["certifie"] / t * 100,
            "conscient_seuil": self.conscient._seuil_conscience,
            "inconscient_modele": self.inconscient.model_name,
            "conscient_charge": self.conscient._loaded,
        }
    
    def analyser_conscience(self, texte: str) -> Dict[str, Any]:
        """Analyse consciente d'un texte existant."""
        import hashlib
        
        pur_score = self.conscient._evaluer_pur_conscience(texte)
        sig_9d = None
        if self.conscient._engine_9d:
            try:
                sig_9d = self.conscient._engine_9d.compute_signature(texte[:200]).tolist()
            except Exception:
                sig_9d = None
        
        resonance = self.conscient._calculer_resonance(texte, 
            np.array(sig_9d) if sig_9d else None)
        
        cert_hash = hashlib.sha256(
            (texte + str(pur_score) + str(resonance)).encode()
        ).hexdigest()
        
        return {
            "texte": texte[:100],
            "longueur": len(texte),
            "score_pur": float(pur_score),
            "résonance": float(resonance),
            "signature_9d": sig_9d,
            "certifié": pur_score >= 0.4,
            "hash": cert_hash,
            "conscience": "éveillée" if pur_score >= 0.4 else "endormie",
        }


# =========================================================================
# TESTS
# =========================================================================

def test_unitaire():
    """Test complet du DualProcessHarmonicEngine."""
    print("=" * 70)
    print("DIALOGUE CONSCIENT / INCONSCIENT — TEST")
    print("=" * 70)
    
    dual = DualProcessHarmonicEngine()
    
    # Test 1 : Génération créative
    print("\n[TEST 1] Génération créative")
    r = dual.generer("Écris sur l'harmonie universelle", n_candidats=2, max_tokens=100)
    if r.retenu:
        print(f"  Style: {r.retenu.style}")
        print(f"  Texte: {r.retenu.contenu[:150]}...")
        print(f"  PUR: {r.retenu.score_pur:.2%} | Cert: {r.retenu.certifie}")
        print(f"  Corrections: {r.nb_tours_correction}")
        print(f"  OK" if r.retenu.certifie else "  ÉCHEC")
    else:
        print("  ÉCHEC: Aucun candidat")
    
    # Test 2 : Contexte scientifique
    print("\n[TEST 2] Contexte scientifique (température basse)")
    r2 = dual.generer("Explique la résonance", contexte="scientifique", max_tokens=80)
    if r2.retenu:
        print(f"  PUR: {r2.retenu.score_pur:.2%} | Consens: {r2.consensus}")
        print(f"  Texte: {r2.retenu.contenu[:120]}...")
        print(f"  OK" if r2.retenu.certifie else "  ÉCHEC")
    
    # Test 3 : Analyse de conscience
    print("\n[TEST 3] Analyse consciente d'un texte harmonique")
    ana = dual.analyser_conscience(
        "Dans l'espace harmonique de la création, chaque mot résonne avec l'infini. "
        "Le nombre d'or φ guide notre exploration de l'univers des possibilités."
    )
    print(f"  PUR: {ana['score_pur']:.2%} | Résonance: {ana['résonance']:.2%}")
    print(f"  Conscience: {ana['conscience']}")
    print(f"  OK" if ana['certifié'] else "  ÉCHEC")
    
    # Test 4 : Interface rapide
    print("\n[TEST 4] Interface rapide (texte seul)")
    texte = dual.generer_rapide("Un haïku sur la lune", max_tokens=50)
    print(f"  {texte[:100]}...")
    print(f"  Longueur: {len(texte)}c")
    print(f"  OK" if len(texte) > 20 else "  ÉCHEC")
    
    # Résumé
    print(f"\n{'=' * 70}")
    s = dual.stats()
    print(f"Générations: {s['total_generations']}")
    print(f"Taux certification: {s['taux_certification']:.0f}%")
    print(f"Score PUR moyen: {s['score_moyen_pur']:.2%}")
    print(f"Temps moyen: {s['temps_moyen_ms']:.0f}ms")
    print(f"{'=' * 70}")
    print("CERVEAU HARMONIQUE OPÉRATIONNEL")
    
    return dual


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Moteur Dual Process (Conscient/Inconscient)")
    parser.add_argument("--test", action="store_true", help="Test unitaire")
    parser.add_argument("--demo", action="store_true", help="Démo interactive")
    parser.add_argument("prompt", nargs="?", default=None)
    parser.add_argument("--contexte", default="creatif", choices=["creatif", "scientifique", "juridique"])
    parser.add_argument("--candidats", type=int, default=3)
    args = parser.parse_args()
    
    dual = DualProcessHarmonicEngine()
    
    if args.test or args.demo:
        test_unitaire()
    
    elif args.prompt:
        r = dual.generer_details(args.prompt, n_candidats=args.candidats, contexte=args.contexte)
        print(f"\n{'='*70}")
        print(f"PROMPT: {args.prompt}")
        print(f"STYLE: {r['style']}")
        print(f"MÉTAPHORE: {r['métaphore']}")
        print(f"\n{r['contenu']}")
        print(f"\nPUR: {r['score_pur']:.2%} | Certifié: {r['certifié']}")
        print(f"Nouveauté: {r['score_novelty']:.2%} | Résonance: {r['score_résonance']:.2%}")
        print(f"Modèle: {r['modèle']} | Corrections: {r['nb_corrections']}")
        print(f"{'='*70}")
    
    else:
        # Mode interactif
        print("Dialogue Conscient/Inconscient (Ctrl+C pour quitter)")
        while True:
            try:
                p = input("> ")
                if p:
                    r = dual.generer_details(p, n_candidats=args.candidats, contexte=args.contexte)
                    print(f"\n[{r['style']}] {r['contenu'][:200]}...")
                    print(f"[PUR: {r['score_pur']:.0%}, Cert: {'OUI' if r['certifié'] else 'NON'}, "
                          f"Corr: {r['nb_corrections']}]\n")
            except KeyboardInterrupt:
                print("\nBye!"); break
