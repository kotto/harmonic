"""
Spectral Hop — Raisonnement multi-sauts par propagation d'onde
================================================================
Implémente le raisonnement ondulatoire du Niveau 4 (Analyse) :
  Raisonner = faire évoluer un état ondulatoire vers un point fixe.

Le principe :
  Partant de Ψ_0 (la question), on fait "sauter" l'onde de fait en fait :
    Ψ_{k+1} = Ψ_k + decay^k · ψ_{meilleur_fait}
  
  À chaque saut, on mesure le SCORE DE RÉSOLUTION :
    score = local^α × global^(1-α)
  
  où :
    local  = interférence(Ψ_k, candidat)  — pertinence locale
    global = interférence(Ψ_0, candidat)  — ancrage à la question
  
  Quand le score dépasse le seuil → la réponse est trouvée.

Ce module remplace find_paths() qui utilisait l'overlap lexical.
Ici, c'est l'onde qui se propage — pas de matching de mots.

Usage :
  from spectral_hop import SpectralHopper
  hopper = SpectralHopper(encoder, memory)
  result = hopper.reason("quelle est la capitale du pays ou se trouve tombouctou")
"""

import sys, math, logging
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
log = logging.getLogger(__name__)


def _interference(psi_a: np.ndarray, psi_b: np.ndarray) -> float:
    """
    Interférence entre deux ondes = cos(θ) normalisé.
    
    Re(⟨ψ_a | ψ_b⟩) / (|ψ_a| · |ψ_b|) ∈ [-1, 1]
    """
    dot = np.real(np.sum(psi_a * np.conj(psi_b)))
    na = np.sqrt(np.real(np.sum(psi_a * np.conj(psi_a))))
    nb = np.sqrt(np.real(np.sum(psi_b * np.conj(psi_b))))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


# ═══════════════════════════════════════════════════════════════════════════════
# RÉSULTAT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HopResult:
    """Résultat d'un raisonnement spectral."""
    answer: Optional[str]               # réponse trouvée (ou None)
    score: float                        # score de résolution
    trajectory: List[Tuple]             # parcours des sauts
    n_hops: int                         # nombre de sauts effectués
    converged: bool                     # convergence atteinte ?
    facts_visited: List[str]            # faits parcourus


# ═══════════════════════════════════════════════════════════════════════════════
# SAUTEUR SPECTRAL
# ═══════════════════════════════════════════════════════════════════════════════

class SpectralHopper:
    """
    Raisonnement multi-sauts par propagation d'onde.
    
    L'onde de la question se propage de fait en fait dans la mémoire
    holographique, accumulant de l'information à chaque saut.
    La réponse émerge quand le score de résolution dépasse le seuil.
    """
    
    def __init__(self, encoder, memory=None,
                 alpha: float = 0.6,
                 stop_threshold: float = 0.15,
                 max_hops: int = 8,
                 min_hops: int = 1,
                 decay_base: float = 0.7):
        self.encoder = encoder
        self.memory = memory
        self.alpha = alpha
        self.stop_threshold = stop_threshold
        self.max_hops = max_hops
        self.min_hops = min_hops
        self.decay_base = decay_base
    
    def reason(self, question: str,
               knowledge_base: List[Tuple] = None,
               answer_candidates: List[str] = None) -> HopResult:
        """
        Raisonnement spectral complet.
        
        Args:
            question: question utilisateur
            knowledge_base: KB (utilise self.memory si None)
            answer_candidates: liste de mots candidats-réponses
                              (si None, tous les mots sont candidats)
        
        Returns:
            HopResult avec la réponse et la trajectoire
        """
        kb = knowledge_base or (self.memory.kb if self.memory else [])
        if not kb:
            return HopResult(None, 0.0, [], 0, False, [])
        
        # 1. Encoder la question → Ψ_0
        psi_0 = self.encoder.encode_query(question)
        if np.sum(np.abs(psi_0)) < 1e-10:
            return HopResult(None, 0.0, [], 0, False, [])
        
        # 2. Préparer les ondes de faits
        fact_waves = self._prepare_facts(kb)
        if not fact_waves:
            return HopResult(None, 0.0, [], 0, False, [])
        
        # 3. Préparer les candidats-réponses
        if answer_candidates is None:
            answer_candidates = self._extract_candidates(kb, psi_0)
        
        if not answer_candidates:
            # Pas de candidats → retourner le meilleur fait
            best = max(fact_waves, key=lambda x: x[2])
            return HopResult(best[0], best[2], [(0, best[0], best[2])], 1, True, [best[0]])
        
        # 4. Propagation d'onde
        return self._hop(psi_0, fact_waves, answer_candidates)
    
    def _prepare_facts(self, kb: List[Tuple]) -> List[Tuple[str, np.ndarray, float]]:
        """
        Encode chaque fait comme onde et calcule son interférence initiale.
        
        Retourne [(label, ψ_fait, interférence_avec_Ψ_0)]
        """
        facts = []
        for s, r, o, *rest in kb:
            sec = rest[0] if rest else 'GENERAL'
            label = f"{s} {r} {o}"
            psi_fact = self.encoder.encode_query(f"{s} {r} {o}")
            # Score initial = résonance avec une question générique sur le sujet
            facts.append((label, psi_fact, 0.0))
        return facts
    
    def _extract_candidates(self, kb: List[Tuple],
                             psi_q: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """
        Extrait les candidats-réponses = objets des faits.
        
        Chaque objet est un candidat potentiel.
        """
        candidates = []
        seen = set()
        for s, r, o, *rest in kb:
            if o not in seen:
                seen.add(o)
                v_o = self.encoder.encode_word(o)
                candidates.append((o, v_o))
        return candidates
    
    def _hop(self, psi_0: np.ndarray,
             fact_waves: List[Tuple[str, np.ndarray, float]],
             candidates: List[Tuple[str, np.ndarray]]) -> HopResult:
        """
        Propagation d'onde multi-sauts.
        
        À chaque saut :
          1. Trouver le fait le plus interférant avec Ψ_k (non vu)
          2. Calculer le score de résolution pour chaque candidat
          3. Si score > seuil → arrêt, retourner la réponse
          4. Sinon : Ψ_{k+1} = Ψ_k + decay^k · ψ_fait
        """
        current_wave = psi_0.copy()
        seen_facts = set()
        trajectory = []
        facts_visited = []
        
        for k in range(self.max_hops):
            # ── 1. Trouver le fait le plus interférant ──
            best_label, best_wave, best_local = None, None, -1.0
            for label, psi_fact, _ in fact_waves:
                if label in seen_facts:
                    continue
                score = _interference(psi_fact, current_wave)
                if score > best_local:
                    best_local = score
                    best_label = label
                    best_wave = psi_fact
            
            if best_label is None:
                trajectory.append((k, None, 0.0, 0.0, 0.0, "épuisement"))
                break
            
            seen_facts.add(best_label)
            facts_visited.append(best_label)
            
            # ── 2. Score de résolution ──
            global_anchor = _interference(best_wave, psi_0)
            res_score = (max(0, best_local) ** self.alpha) * \
                        (max(0, global_anchor) ** (1 - self.alpha))
            
            # ── 3. Évaluer les candidats ──
            if k >= self.min_hops:
                best_answer, best_res = None, 0.0
                for cand_label, cand_wave in candidates:
                    local_c = _interference(cand_wave, current_wave)
                    global_c = _interference(cand_wave, psi_0)
                    res = (max(0, local_c) ** self.alpha) * \
                          (max(0, global_c) ** (1 - self.alpha))
                    if res > best_res:
                        best_res = res
                        best_answer = cand_label
                
                if best_res > self.stop_threshold:
                    trajectory.append((k, best_label, best_local,
                                       global_anchor, best_res, "✓ STOP"))
                    return HopResult(
                        answer=best_answer,
                        score=best_res,
                        trajectory=trajectory,
                        n_hops=k + 1,
                        converged=True,
                        facts_visited=facts_visited,
                    )
            
            trajectory.append((k, best_label, best_local,
                               global_anchor, res_score, ""))
            
            # ── 4. Mise à jour de l'onde ──
            decay = self.decay_base ** k
            current_wave = current_wave + decay * best_wave
            norm = np.linalg.norm(current_wave)
            if norm > 1e-12:
                current_wave = current_wave / norm
        
        # Fallback : meilleur candidat
        best_answer, best_score = None, 0.0
        for cand_label, cand_wave in candidates:
            local_c = _interference(cand_wave, current_wave)
            global_c = _interference(cand_wave, psi_0)
            res = (max(0, local_c) ** self.alpha) * \
                  (max(0, global_c) ** (1 - self.alpha))
            if res > best_score:
                best_score = res
                best_answer = cand_label
        
        return HopResult(
            answer=best_answer,
            score=best_score,
            trajectory=trajectory,
            n_hops=len(trajectory),
            converged=False,
            facts_visited=facts_visited,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from holographic_encoder import HolographicEncoder
    
    print("=" * 65)
    print("SPECTRAL HOP — Raisonnement multi-sauts par propagation d'onde")
    print("=" * 65)
    
    kb = [
        ("tombouctou", "est une ville du", "mali", "GEOGRAPHIE"),
        ("tombouctou", "se trouve au", "mali", "GEOGRAPHIE"),
        ("bamako", "est la capitale du", "mali", "GEOGRAPHIE"),
        ("dakar", "est la capitale du", "senegal", "GEOGRAPHIE"),
        ("paris", "est la capitale de la", "france", "GEOGRAPHIE"),
        ("mali", "est un pays d", "afrique", "GEOGRAPHIE"),
        
        ("lumiere", "est une", "onde", "PHYSIQUE_FOND"),
        ("lumiere", "est composee de", "photons", "PHYSIQUE_FOND"),
        ("photons", "sont des particules sans", "masse", "PHYSIQUE_FOND"),
        
        ("coeur", "pompe le", "sang", "BIOLOGIE"),
        ("sang", "transporte l", "oxygene", "BIOLOGIE"),
    ]
    
    encoder = HolographicEncoder(dim=256)
    hopper = SpectralHopper(encoder, alpha=0.6, stop_threshold=0.05, max_hops=6)
    
    questions = [
        "quelle est la capitale du pays ou se trouve tombouctou",
        "explique la lumiere",
        "comment fonctionne le coeur",
        "qu est ce que la lumiere",
    ]
    
    for q in questions:
        print(f"\n  Q: {q}")
        result = hopper.reason(q, knowledge_base=kb)
        
        if result.converged:
            print(f"  ✅ RÉPONSE: {result.answer}  (score={result.score:.4f}, hops={result.n_hops})")
        else:
            print(f"  ⚠️ Meilleur candidat: {result.answer}  (score={result.score:.4f}, hops={result.n_hops})")
        
        print(f"  Trajectoire:")
        for hop in result.trajectory:
            k, label, local, global_, res, status = hop
            star = " ← " + status if status else ""
            if label:
                print(f"    hop {k}: {label[:40]:40s}  local={local:+.3f}  global={global_:+.3f}  res={res:.3f}{star}")
            else:
                print(f"    hop {k}: (épuisement){star}")


if __name__ == '__main__':
    demo()
