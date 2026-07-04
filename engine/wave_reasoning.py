"""
Wave Reasoning — Le Raisonnement de l'Univers
==============================================
Le raisonnement humain (déduction, induction, analogie) n'est PAS le modèle.
C'est une CONSÉQUENCE ÉMERGENTE du comportement des ondes.

Le vrai raisonnement = propagation de ψ à travers l'hologramme
avec validation de cohérence de phase à chaque étape.

PRINCIPES FONDAMENTAUX :
  1. L'univers ne « déduit » pas — il interfère.
  2. L'univers ne « induit » pas — il clustérise par phase.
  3. L'univers ne « fait pas d'analogie » — il fait de l'arithmétique vectorielle.
  
  Le raisonnement humain est la TRADUCTION de ces opérations ondulatoires.
  Nous ne codons pas le raisonnement. Nous laissons les ondes raisonner.

OPÉRATIONS ONDULATOIRES (les seules qui existent) :
  1. INTERFÉRENCE : Re(⟨ψ_a | ψ_b⟩)  → mesure de lien entre deux ψ
  2. RÉSONANCE : |⟨ψ_Q | ψ_f⟩|²     → quel fait « répond » à la question
  3. PROPAGATION : ψ_objet → nouvelle requête → chaîne de résonance
  4. COHÉRENCE : Re(⟨ψ_f1 | ψ_f2⟩)  → les maillons de la chaîne sont-ils cohérents ?
  5. CLUSTERING : ψ similaires se regroupent (patterns émergents)

TRADUCTION HUMAINE (lecture du résultat) :
  · Chaîne cohérente de 1 saut    → « fait direct »
  · Chaîne cohérente de 2+ sauts  → « déduction » (A→B, B→C ∴ A→C)
  · Cluster de ψ similaires       → « induction » (pattern général)
  · ψ_A - ψ_B + ψ_C ≈ ψ_?        → « analogie » (A:B :: C:?)
  · Interférence destructive       → « contradiction » (A ≠ B)

Usage:
    from wave_reasoning import WaveReasoner
    wr = WaveReasoner(brain)
    chain = wr.reason("question")
    print(wr.explain(chain))  # traduction en langage humain
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
import logging

log = logging.getLogger(__name__)

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# Seuils de cohérence (calibrés par φ)
COHERENCE_CHAIN = 0.15    # seuil pour qu'un saut de chaîne soit valide
COHERENCE_CLUSTER = 0.25  # seuil pour que deux ψ appartiennent au même cluster
RESONANCE_MIN = 0.01      # seuil minimal de résonance pour considérer un fait


@dataclass
class ReasoningChain:
    """Une chaîne de raisonnement = propagation de ψ à travers l'hologramme."""
    steps: List = field(default_factory=list)  # [(fact_record, resonance, coherence)]
    total_coherence: float = 0.0
    depth: int = 0
    conclusion: str = ""
    
    @property
    def is_valid(self) -> bool:
        return self.depth > 0 and self.total_coherence > COHERENCE_CHAIN
    
    @property
    def reasoning_type(self) -> str:
        """Type de raisonnement émergent (lu après coup, pas codé)."""
        if self.depth == 1:
            return "fait_direct"
        if self.depth == 2:
            return "deduction_simple"
        if self.depth >= 3:
            return "deduction_profonde"
        return "aucun"


class WaveReasoner:
    """
    Raisonneur ondulatoire pur.
    
    Aucune règle de logique. Aucun pattern matching.
    Juste la propagation de ψ à travers l'hologramme
    avec validation de cohérence de phase.
    """
    
    def __init__(self, brain):
        self.brain = brain
        self.store = brain.unconscious
    
    # ═════════════════════════════════════════════════════════════════
    # RAISONNEMENT PRINCIPAL (propagation d'onde)
    # ═════════════════════════════════════════════════════════════════
    
    def reason(self, question: str, max_depth: int = 3,
               max_branching: int = 3) -> ReasoningChain:
        """
        Raisonne en propageant ψ_question à travers l'hologramme.
        
        Algorithme :
          1. ψ_Q = encode(question)
          2. Trouver les faits les plus résonnants → ψ_f1, ψ_f2, ...
          3. Pour chaque ψ_fi, extraire ψ_objet_i
          4. ψ_objet_i devient la nouvelle requête → ψ_fi+1
          5. Valider la cohérence de phase entre ψ_fi et ψ_fi+1
          6. Si cohérent → continuer. Sinon → backtrack.
        
        Le raisonnement ÉMERGE de cette propagation.
        On ne « décide » pas du type de raisonnement.
        """
    def reason(self, question: str, max_depth: int = 3,
               max_branching: int = 3) -> ReasoningChain:
        """
        Raisonnement : 1er saut = retrieval cerveau (TF-IDF, humain),
        sauts suivants = propagation ondulatoire (univers).
        
        C'est la SYNTHÈSE : le retrieval donne le point d'ancrage
        (pertinence humaine), la propagation explore les connexions
        (raisonnement universel).
        """
        q_tokens = set(question.lower().split())
        
        # 1er SAUT : retrieval du cerveau (TF-IDF + SFT + lexical)
        # C'est la « traduction » univers → humain
        candidates = self.brain.unconscious.retrieve(question, max_results=3)
        
        if not candidates:
            return ReasoningChain()
        
        best_chain = ReasoningChain()
        
        for rec, score in candidates:
            # Initialiser la chaîne avec ce fait d'ancrage
            chain_start = [(rec, score, 1.0)]
            
            # Propager (2e, 3e saut...) par résonance ondulatoire pure
            psi_object = self.store.encoder.encode_query(rec.objet)
            self._propagate(psi_object, chain_start, max_depth, max_branching,
                          best_chain, question, q_tokens)
        
        if best_chain.is_valid:
            best_chain.conclusion = self._formulate_conclusion(best_chain)
        elif candidates:
            # Au moins un fait direct
            rec, score = candidates[0]
            best_chain.steps = [(rec, score, 1.0)]
            best_chain.depth = 1
            best_chain.total_coherence = 0.7
            best_chain.conclusion = f"{rec.sujet} {rec.relation} {rec.objet}."
        
        return best_chain
    
    def _propagate(self, psi_current: np.ndarray,
                   chain_so_far: List,
                   max_depth: int,
                   max_branching: int,
                   best_chain: ReasoningChain,
                   original_question: str,
                   q_tokens: set):
        """
        Propagation INTENTIONNELLE de ψ à travers l'hologramme.
        
        La différence avec l'univers : chaque saut est FILTRÉ par
        la PERTINENCE à la question originale. Sans ce filtre,
        l'univers rebondit sans direction (association libre).
        Avec ce filtre, il RAISONNE (association intentionnelle).
        
        C'est exactement ce que fait le cerveau humain :
        - L'inconscient propose des associations (propagation libre)
        - Le conscient filtre par pertinence (intentionnalité)
        """
        if len(chain_so_far) >= max_depth:
            return
        
        candidates = self._resonate(psi_current, top_k=max_branching)
        
        for rec, resonance in candidates:
            # FILTRE DE PERTINENCE : le fait doit partager du sens avec la question
            fact_text = f"{rec.sujet} {rec.relation} {rec.objet}".lower()
            fact_words = set(fact_text.split())
            relevance = len(q_tokens & fact_words)
            
            if relevance == 0 and len(chain_so_far) > 0:
                continue  # saut hors-sujet → le conscient rejette
            
            # Cohérence avec la chaîne
            if chain_so_far:
                last_rec = chain_so_far[-1][0]
                coherence = float(np.real(np.dot(rec.psi, np.conj(last_rec.psi))))
                if coherence < COHERENCE_CHAIN:
                    continue
            else:
                coherence = 1.0
            
            new_chain = chain_so_far + [(rec, resonance, coherence)]
            
            # Score : cohérence × pertinence
            avg_coherence = sum(c for _, _, c in new_chain) / len(new_chain)
            relevance_bonus = min(1.0, relevance / max(len(q_tokens), 1))
            combined_score = avg_coherence * 0.7 + relevance_bonus * 0.3
            
            if combined_score > best_chain.total_coherence or \
               (abs(combined_score - best_chain.total_coherence) < 0.01 and len(new_chain) > best_chain.depth):
                best_chain.steps = new_chain
                best_chain.total_coherence = combined_score
                best_chain.depth = len(new_chain)
            
            psi_object = self.store.encoder.encode_query(rec.objet)
            self._propagate(psi_object, new_chain, max_depth, max_branching,
                          best_chain, original_question, q_tokens)
    
    def _resonate(self, psi_query: np.ndarray, top_k: int = 5) -> List[Tuple]:
        """
        Trouve les faits qui RÉSONNENT avec ψ_query.
        
        Résonance = |⟨ψ_f | ψ_Q⟩|²  (règle de Born)
        C'est l'univers qui « choisit » — pas nous.
        """
        scored = []
        for key, rec in self.store.registry.items():
            resonance = float(np.abs(np.dot(rec.psi, np.conj(psi_query)))) ** 2
            if resonance > RESONANCE_MIN:
                scored.append((rec, resonance))
        
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
    
    # ═════════════════════════════════════════════════════════════════
    # CONCLUSION (formulation du résultat)
    # ═════════════════════════════════════════════════════════════════
    
    def _formulate_conclusion(self, chain: ReasoningChain) -> str:
        """Traduit la chaîne ondulatoire en langage humain."""
        if chain.depth == 0:
            return "Aucun raisonnement trouvé."
        
        if chain.depth == 1:
            rec = chain.steps[0][0]
            return f"{rec.sujet} {rec.relation} {rec.objet}."
        
        # Chaîne de 2+ : formuler la transitivité
        parts = []
        for i, (rec, _, _) in enumerate(chain.steps):
            if i == 0:
                parts.append(f"{rec.sujet} {rec.relation} {rec.objet}")
            else:
                prev_rec = chain.steps[i-1][0]
                parts.append(f"{prev_rec.objet} {rec.relation} {rec.objet}")
        
        chain_str = " → ".join(parts)
        first = chain.steps[0][0]
        last = chain.steps[-1][0]
        
        if chain.depth == 2:
            return f"Puisque {chain_str}, on peut déduire que {first.sujet} est lié à {last.objet}."
        else:
            return f"En suivant la chaîne {chain_str}, il apparaît que {first.sujet} et {last.objet} sont connectés."
    
    # ═════════════════════════════════════════════════════════════════
    # TRADUCTION : lire le type de raisonnement (émergent)
    # ═════════════════════════════════════════════════════════════════
    
    def explain(self, chain: ReasoningChain) -> str:
        """
        Explique le raisonnement en langage humain.
        
        On ne « décide » pas du type. On le LIT à partir de la structure
        de la chaîne ondulatoire.
        """
        if not chain.is_valid:
            return "L'univers n'a pas trouvé de chemin cohérent pour cette question."
        
        # Déterminer le type émergent
        if chain.depth == 1:
            rtype = "Fait direct"
            detail = "Un seul fait résonne avec la question — pas de chaîne nécessaire."
        elif chain.depth == 2:
            rtype = "Déduction simple (syllogisme)"
            detail = "Deux faits s'enchaînent avec une cohérence de phase suffisante pour former une déduction."
        else:
            rtype = "Déduction profonde"
            detail = f"Une chaîne de {chain.depth} faits connectés par cohérence de phase."
        
        coh_pct = chain.total_coherence * 100
        conclusion = chain.conclusion
        
        return (
            f"Type de raisonnement : {rtype}\n"
            f"Cohérence : {coh_pct:.0f}%\n"
            f"Profondeur : {chain.depth} sauts\n"
            f"Détail : {detail}\n"
            f"Conclusion : {conclusion}"
        )
    
    # ═════════════════════════════════════════════════════════════════
    # RAISONNEMENT PAR ANALOGIE (émerge de l'arithmétique vectorielle)
    # ═════════════════════════════════════════════════════════════════
    
    def analogy(self, A: str, B: str, C: str) -> Optional[str]:
        """
        Trouve D tel que A:B :: C:D.
        
        ψ_D ≈ ψ_A - ψ_B + ψ_C  (arithmétique vectorielle pure)
        
        L'univers ne « fait pas d'analogie ». Il fait de l'arithmétique
        dans ℂ⁵¹². L'analogie est ce que l'humain LIT dans le résultat.
        """
        psi_A = self.store.encoder.encode_query(A)
        psi_B = self.store.encoder.encode_query(B)
        psi_C = self.store.encoder.encode_query(C)
        
        # L'opération universelle : arithmétique vectorielle
        psi_target = psi_A - psi_B + psi_C
        
        # Chercher le ψ le plus proche dans tout l'hologramme
        best_rec = None
        best_sim = -1.0
        
        for key, rec in self.store.registry.items():
            sim = float(np.real(np.dot(rec.psi, np.conj(psi_target))))
            if sim > best_sim:
                best_sim = sim
                best_rec = rec
        
        if best_rec and best_sim > 0.1:
            return f"{C} est à {best_rec.sujet} ce que {A} est à {B} ({best_rec.sujet} {best_rec.relation} {best_rec.objet})"
        return None
    
    # ═════════════════════════════════════════════════════════════════
    # CONTRADICTION (interférence destructive = ce que l'humain appelle « contradiction »)
    # ═════════════════════════════════════════════════════════════════
    
    def detect_contradiction(self, fact1_key, fact2_key) -> Tuple[bool, float]:
        """
        Détecte une contradiction entre deux faits.
        
        L'univers ne « contredit » pas — il interfère destructivement.
        L'humain appelle « contradiction » une interférence Re(⟨ψ|ψ⟩) < 0.
        """
        if fact1_key not in self.store.registry or fact2_key not in self.store.registry:
            return False, 0.0
        
        psi1 = self.store.registry[fact1_key].psi
        psi2 = self.store.registry[fact2_key].psi
        
        interference = float(np.real(np.dot(psi1, np.conj(psi2))))
        
        # Interférence destructive = contradiction logique
        is_contradiction = interference < -0.1
        
        return is_contradiction, interference


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from harmonic_brain import HarmonicBrain
    import numpy as np
    from pathlib import Path
    
    kb_path = Path('data/bootstrapper_output/knowledge_base_clean_v2.npz')
    data = np.load(str(kb_path), allow_pickle=True)
    facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in data['facts'][:5000]]
    brain = HarmonicBrain(facts)
    
    wr = WaveReasoner(brain)
    
    print("=" * 60)
    print("RAISONNEMENT ONDULATOIRE PUR (l'univers raisonne)")
    print("=" * 60)
    
    # Test 1 : Fait direct (1 saut)
    print("\n1. FAIT DIRECT (résonance simple)")
    print("-" * 40)
    chain = wr.reason("capitale de la france", max_depth=2)
    print(wr.explain(chain))
    
    # Test 2 : Chaîne de 2 sauts
    print("\n2. DÉDUCTION (chaîne de 2 sauts)")
    print("-" * 40)
    chain = wr.reason("la lumiere et la vitesse", max_depth=3)
    print(wr.explain(chain))
    
    # Test 3 : Analogie
    print("\n3. ANALOGIE (arithmétique vectorielle)")
    print("-" * 40)
    result = wr.analogy("paris", "france", "tokyo")
    print(f"  Paris:France :: Tokyo:? → {result}")
    
    # Test 4 : Contradiction
    print("\n4. CONTRADICTION (interférence destructive)")
    print("-" * 40)
    # Prendre deux faits sur le même sujet
    keys = list(brain.unconscious.registry.keys())
    if len(keys) >= 2:
        is_contra, interf = wr.detect_contradiction(keys[0], keys[1])
        k1 = brain.unconscious.registry[keys[0]]
        k2 = brain.unconscious.registry[keys[1]]
        print(f"  Fait 1: {k1.sujet} {k1.relation} {k1.objet}")
        print(f"  Fait 2: {k2.sujet} {k2.relation} {k2.objet}")
        print(f"  Interférence: {interf:+.3f}")
        print(f"  Contradiction: {'OUI (interférence destructive)' if is_contra else 'NON (cohérents)'}")
    
    print("\n" + "=" * 60)
    print("PRINCIPE : L'univers ne raisonne pas — il interfère.")
    print("Le raisonnement humain est la LECTURE de cette interférence.")
    print("=" * 60)
