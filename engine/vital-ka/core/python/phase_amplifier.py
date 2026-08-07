"""
Phase Amplifier — Propagation ψ stable au-delà de 3 sauts
===========================================================
Problème : La propagation ψ simple (ψ_objet → nouvelle requête)
perd sa cohérence après 3 sauts. Le signal s'atténue, le bruit domine.

Solution : Amplification de phase par interférence constructive.
À chaque saut, on combine le ψ_courant avec le ψ_contexte_accumulé :
    ψ_next = normalize(ψ_objet + α · ψ_contexte)

PRINCIPE ONDULATOIRE :
  · Interférence constructive : deux ondes en phase s'amplifient
  · Le ψ_contexte accumulé agit comme une « mémoire de phase »
  · α = φ⁻¹ (0.618) — facteur d'amplification optimal
  · La normalisation empêche l'explosion de la norme
  · Résultat : chaînes stables à 5, 10, 20+ sauts

TRADUCTION HUMAINE :
  · Chaîne 1-3 sauts → « fait direct / déduction simple »
  · Chaîne 4-7 sauts → « raisonnement profond »
  · Chaîne 8-15 sauts → « théorisation »
  · Chaîne 16+ sauts → « sagesse émergente »

Usage :
    from phase_amplifier import PhaseAmplifier
    amp = PhaseAmplifier(brain)
    chain = amp.propagate("question initiale", max_depth=10)
    explanation = amp.explain(chain)
"""

import math
import time
import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # 0.618 — amplification optimale
ALPHA_AMPLIFY = PHI_INV  # facteur de mélange avec le contexte
COHERENCE_MIN = 0.08     # seuil minimal pour accepter un saut
SATURATION_NORM = 5.0    # norme max avant saturation


@dataclass
class PropagationStep:
    """Un saut dans la chaîne de propagation."""
    depth: int
    query_psi: np.ndarray      # ψ utilisé pour ce saut
    fact_found: tuple           # (sujet, relation, objet, secteur)
    resonance: float            # force de résonance (0-1)
    coherence: float            # cohérence avec le contexte
    context_accumulated: np.ndarray  # ψ_contexte après ce saut
    amplification_factor: float  # combien on a amplifié

@dataclass
class PropagationChain:
    """Chaîne de propagation amplifiée."""
    steps: List[PropagationStep] = field(default_factory=list)
    initial_question: str = ""
    final_conclusion: str = ""
    total_coherence: float = 0.0
    stopped_reason: str = ""  # 'max_depth', 'no_resonance', 'coherence_lost'

    @property
    def depth(self) -> int:
        return len(self.steps)

    @property
    def is_valid(self) -> bool:
        return self.depth > 0 and self.total_coherence > COHERENCE_MIN

    @property
    def reasoning_type(self) -> str:
        if self.depth <= 1:
            return "fait_direct"
        elif self.depth <= 3:
            return "deduction_simple"
        elif self.depth <= 7:
            return "raisonnement_profond"
        elif self.depth <= 15:
            return "theorisation"
        else:
            return "sagesse_emergente"


@dataclass
class Branch:
    """Une branche dans la propagation multi-chemin."""
    question: str = ""
    current_text: str = ""
    context_psi: np.ndarray = None
    steps: List[PropagationStep] = field(default_factory=list)
    score: float = 0.0
    is_dead: bool = False
    stop_reason: str = ""

    def fork(self) -> 'Branch':
        """Crée une copie indépendante de cette branche."""
        return Branch(
            question=self.question,
            current_text=self.current_text,
            context_psi=self.context_psi.copy() if self.context_psi is not None else None,
            steps=list(self.steps),
            score=self.score,
            is_dead=False,
            stop_reason="",
        )


class PhaseAmplifier:
    """
    Amplificateur de phase pour propagation ψ profonde.

    Maintient un ψ_contexte ∈ ℂⁿ qui accumule l'information
    de TOUS les sauts précédents avec amplification constructive.
    """

    def __init__(self, brain=None, dim: int = 512, encoder=None):
        self.brain = brain
        self.dim = dim
        self.encoder = encoder
        if brain is not None:
            self.encoder = brain.unconscious.encoder
            self.dim = brain.unconscious.dim
        self._reset()

    def _reset(self):
        """Réinitialise l'état de propagation."""
        self._context_psi = None
        self._context_norm = 0.0

    def _encode(self, text: str) -> np.ndarray:
        """Encode un texte en ψ (utilise l'encodeur du brain ou fallback)."""
        if self.encoder is not None:
            try:
                return self.encoder.encode_query(text)
            except Exception:
                pass

        # Fallback : hash simple
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        return v / (np.linalg.norm(v) + 1e-10)

    def propagate(self, question: str, max_depth: int = 10,
                  coherence_threshold: float = COHERENCE_MIN) -> PropagationChain:
        """
        Propagation ψ amplifiée.

        À chaque saut :
          1. ψ_query = normalize(ψ_courant + α · ψ_contexte)
          2. Retrieval : trouver le fait le plus résonant
          3. Validation : cohérence du fait avec le contexte
          4. Amplification : ψ_contexte += ψ_fait_trouvé
          5. ψ_courant = ψ_objet_du_fait (pour le prochain saut)

        Args:
            question: question initiale
            max_depth: profondeur max de la chaîne
            coherence_threshold: seuil minimal de cohérence

        Returns:
            PropagationChain avec tous les sauts
        """
        self._reset()
        chain = PropagationChain(initial_question=question)

        # Étape 0 : encoder la question
        q_psi = self._encode(question)
        self._context_psi = q_psi.copy()
        self._context_norm = 1.0

        current_psi = q_psi
        current_text = question

        for depth in range(1, max_depth + 1):
            # 1. AMPLIFIER : mélanger avec le contexte accumulé
            amplified_psi = self._amplify(current_psi, self._context_psi, depth)

            # 2. RETRIEVE : trouver le fait le plus résonant
            fact, resonance = self._retrieve_best(amplified_psi, current_text)
            if fact is None:
                chain.stopped_reason = 'no_resonance'
                break

            # 3. VALIDATE : cohérence avec le contexte
            fact_psi = self._encode(f"{fact[0]} {fact[1]} {fact[2]}")
            coherence = self._compute_coherence(fact_psi, self._context_psi)

            if coherence < coherence_threshold and depth > 1:
                chain.stopped_reason = 'coherence_lost'
                break

            # 4. AMPLIFY CONTEXT : accumuler le ψ du fait trouvé
            amp_factor = 1.0 + (depth - 1) * PHI_INV * 0.3  # croît avec la profondeur
            self._context_psi = self._context_psi + amp_factor * fact_psi
            self._normalize_context()

            # 5. NEXT : l'objet devient la nouvelle question
            objet_text = fact[2]
            current_psi = self._encode(objet_text)
            current_text = objet_text

            # Enregistrer le saut
            step = PropagationStep(
                depth=depth,
                query_psi=amplified_psi,
                fact_found=fact,
                resonance=resonance,
                coherence=coherence,
                context_accumulated=self._context_psi.copy(),
                amplification_factor=amp_factor,
            )
            chain.steps.append(step)

        # Calculer la cohérence totale
        if chain.steps:
            chain.total_coherence = sum(s.coherence for s in chain.steps) / len(chain.steps)

        if chain.stopped_reason == '':
            chain.stopped_reason = 'max_depth'

        return chain

    def _amplify(self, current_psi: np.ndarray, context_psi: np.ndarray,
                 depth: int) -> np.ndarray:
        """
        Amplification de phase : mélange constructif courant + contexte.

        ψ_amplified = normalize(ψ_current + α · ψ_context · log(depth+1))
        """
        # Le facteur d'amplification augmente avec la profondeur
        # (plus on va loin, plus le contexte est important)
        depth_factor = math.log(depth + 1) * ALPHA_AMPLIFY
        amplified = current_psi + depth_factor * context_psi
        norm = np.linalg.norm(amplified)
        if norm > 1e-10:
            amplified = amplified / norm
        return amplified

    def _normalize_context(self):
        """Normalise le ψ_contexte pour éviter l'explosion."""
        norm = np.linalg.norm(self._context_psi)
        if norm > SATURATION_NORM:
            # Saturation douce : compresser au lieu de tronquer
            compression = SATURATION_NORM / norm
            self._context_psi *= compression

    def _compute_coherence(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """Cohérence de phase entre deux ψ."""
        if psi_a is None or psi_b is None:
            return 0.0
        return float(np.abs(np.dot(psi_a.conj(), psi_b)))

    def _retrieve_best(self, query_psi: np.ndarray, query_text: str) -> Tuple[Optional[tuple], float]:
        """
        Retrieval du meilleur fait par DIRECT SUBJECT LOOKUP.

        Pour la propagation de chaîne, on ne pose PAS une question —
        on cherche le fait dont le SUJET correspond au texte courant.
        
        Stratégie :
          1. Match exact : sujet_normalisé == query_normalisé
          2. Match partiel : query dans sujet (pour les sujets composés)
          3. Score = amplitude × cohérence_ψ × bonus_exact_match
        """
        if self.brain is None:
            return None, 0.0

        store = self.brain.unconscious
        q_norm = query_text.lower().strip()

        # Collecter tous les faits dont le sujet matche
        candidates = []
        for key, record in store.registry.items():
            sujet_norm = key[0].lower().strip()
            
            # Match exact : priorité maximale
            if sujet_norm == q_norm:
                score = 10.0
            # Match partiel : le sujet contient la query
            elif q_norm in sujet_norm and len(q_norm) >= 4:
                score = 5.0
            # Match partiel inverse : la query contient le sujet
            elif sujet_norm in q_norm and len(sujet_norm) >= 4:
                score = 3.0
            else:
                continue

            # Bonus d'amplitude (faits répétés = plus fiables)
            amp_bonus = min(5.0, math.log1p(record.amplitude))
            
            # Bonus de cohérence ψ avec le contexte
            if record.psi is not None and self._context_psi is not None:
                psi_coherence = float(np.abs(np.dot(
                    record.psi.conj(), self._context_psi
                )))
                # Normaliser
                norm_r = np.linalg.norm(record.psi)
                norm_c = np.linalg.norm(self._context_psi)
                if norm_r > 1e-10 and norm_c > 1e-10:
                    psi_coherence = psi_coherence / (norm_r * norm_c)
                psi_bonus = max(0, psi_coherence) * 5.0
            else:
                psi_bonus = 0.0

            # Bonus de confiance (conscient)
            conf_bonus = record.confidence * 2.0

            total_score = score + amp_bonus + psi_bonus + conf_bonus
            candidates.append((key, record, total_score))

        if not candidates:
            # Fallback élargi : chercher dans les objets aussi (la query pourrait être un objet)
            for key, record in store.registry.items():
                objet_norm = key[2].lower().strip()
                if q_norm in objet_norm and len(q_norm) >= 4:
                    candidates.append((key, record, 2.0))  # score faible

        if not candidates:
            return None, 0.0

        # Trier par score et retourner le meilleur
        candidates.sort(key=lambda x: -x[2])
        best_key, best_record, best_score = candidates[0]
        
        # Normaliser le score en résonance (0-1)
        max_possible = 10.0 + 5.0 + 5.0 + 2.0  # score_max théorique
        resonance = min(1.0, best_score / max_possible)

        return (
            (best_record.sujet, best_record.relation, best_record.objet, best_record.secteur),
            resonance
        )

    def explain(self, chain: PropagationChain) -> str:
        """
        Traduit une chaîne de propagation en langage humain.

        Le raisonnement ondulatoire N'EST PAS le raisonnement humain.
        C'est une TRADUCTION — on lit la chaîne et on l'explique.
        """
        if not chain.steps:
            return f"Je ne trouve pas de chemin de raisonnement pour : {chain.initial_question}"

        lines = []
        lines.append(f"🔍 Raisonnement {chain.reasoning_type} ({chain.depth} sauts) :")
        lines.append(f"   Question : {chain.initial_question}")
        lines.append("")

        for step in chain.steps:
            s, r, o, sec = step.fact_found
            resonance_pct = step.resonance * 100
            coherence_pct = step.coherence * 100
            lines.append(
                f"  {'  ' * (step.depth - 1)}├─ Saut {step.depth} : "
                f"« {s} → {r} → {o} » "
                f"[résonance: {resonance_pct:.0f}%, "
                f"cohérence: {coherence_pct:.0f}%, "
                f"ampl: ×{step.amplification_factor:.2f}]"
            )

        lines.append("")
        lines.append(f"   🛑 Arrêt : {chain.stopped_reason}")
        lines.append(f"   📊 Cohérence totale : {chain.total_coherence:.3f}")
        lines.append(f"   🏷️  Type : {chain.reasoning_type}")

        return "\n".join(lines)

    # ── MULTI-BRANCH PROPAGATION ──────────────────────────────────────────

    def propagate_multi(self, question: str, max_depth: int = 10,
                        beam_width: int = 3, branch_factor: int = 3,
                        coherence_threshold: float = COHERENCE_MIN) -> List[PropagationChain]:
        """
        Propagation ψ MULTI-BRANCHE par beam search.

        Au lieu de suivre un seul chemin, on explore `branch_factor` faits
        par saut et on garde les `beam_width` meilleures branches.

        Cela permet de :
          · Découvrir des connexions inattendues
          · Comparer plusieurs chemins de raisonnement
          · Ne pas rester bloqué sur un chemin sans issue

        Args:
            question: question initiale
            max_depth: profondeur max
            beam_width: nombre de branches parallèles
            branch_factor: nombre de faits explorés par saut par branche

        Returns:
            Liste des beam_width meilleures chaînes, triées par score
        """
        self._reset()

        # Encoder la question
        q_psi = self._encode(question)
        self._context_psi = q_psi.copy()

        # Initialiser le beam avec une seule branche
        branches = [Branch(question=question, current_text=question,
                          context_psi=q_psi.copy())]

        for depth in range(1, max_depth + 1):
            new_branches = []

            for branch in branches:
                if branch.is_dead:
                    new_branches.append(branch)
                    continue

                # Récupérer les top-K faits pour cette branche
                current_psi = self._encode(branch.current_text)
                amplified_psi = self._amplify(current_psi, branch.context_psi, depth)
                candidates = self._retrieve_top_k(branch.current_text, k=branch_factor)

                if not candidates:
                    branch.is_dead = True
                    branch.stop_reason = 'no_resonance'
                    new_branches.append(branch)
                    continue

                # Créer une nouvelle branche pour chaque candidat
                for fact, resonance in candidates:
                    new_branch = branch.fork()
                    s, r, o, sec = fact

                    # Cohérence
                    fact_psi = self._encode(f"{s} {r} {o}")
                    coherence = self._compute_coherence(fact_psi, new_branch.context_psi)

                    if coherence < coherence_threshold and depth > 1:
                        continue  # ce fait ne passe pas le seuil, on le skip

                    # Accumuler le contexte
                    amp_factor = 1.0 + (depth - 1) * PHI_INV * 0.3
                    new_branch.context_psi = new_branch.context_psi + amp_factor * fact_psi
                    self._normalize_branch_context(new_branch)

                    # Mettre à jour la branche
                    new_branch.current_text = o
                    new_branch.steps.append(PropagationStep(
                        depth=depth,
                        query_psi=amplified_psi,
                        fact_found=fact,
                        resonance=resonance,
                        coherence=coherence,
                        context_accumulated=new_branch.context_psi.copy(),
                        amplification_factor=amp_factor,
                    ))
                    new_branch.score += resonance * coherence
                    new_branches.append(new_branch)

            # Garder les beam_width meilleures
            branches = sorted(new_branches, key=lambda b: -b.score)[:beam_width]
            if not branches:
                break

        # Convertir en PropagationChain
        chains = []
        for branch in branches:
            chain = PropagationChain(
                steps=branch.steps,
                initial_question=question,
                total_coherence=(sum(s.coherence for s in branch.steps) /
                                 max(1, len(branch.steps))),
                stopped_reason=branch.stop_reason or 'max_depth',
            )
            chains.append(chain)

        return sorted(chains, key=lambda c: -c.total_coherence)

    def _retrieve_top_k(self, query_text: str, k: int = 3) -> List[Tuple[tuple, float]]:
        """Retrieval des top-K faits (pour multi-branche)."""
        if self.brain is None:
            return []

        store = self.brain.unconscious
        q_norm = query_text.lower().strip()
        candidates = []

        for key, record in store.registry.items():
            sujet_norm = key[0].lower().strip()
            score = 0.0

            if sujet_norm == q_norm:
                score = 10.0
            elif q_norm in sujet_norm and len(q_norm) >= 4:
                score = 5.0
            elif sujet_norm in q_norm and len(sujet_norm) >= 4:
                score = 3.0
            else:
                continue

            amp_bonus = min(5.0, math.log1p(record.amplitude))
            conf_bonus = record.confidence * 2.0
            score += amp_bonus + conf_bonus
            resonance = min(1.0, score / 17.0)
            candidates.append(((record.sujet, record.relation, record.objet,
                               record.secteur), resonance))

        candidates.sort(key=lambda x: -x[1])
        return candidates[:k]

    def _normalize_branch_context(self, branch: 'Branch'):
        """Normalise le ψ_contexte d'une branche."""
        norm = np.linalg.norm(branch.context_psi)
        if norm > SATURATION_NORM:
            branch.context_psi *= SATURATION_NORM / norm

    def reason_deep_multi(self, question: str, max_depth: int = 10,
                          beam_width: int = 3) -> str:
        """
        Raisonnement profond multi-branche — explore plusieurs chemins
        et synthétise le meilleur.
        """
        chains = self.propagate_multi(question, max_depth=max_depth,
                                      beam_width=beam_width)

        if not chains or not chains[0].steps:
            return f"Je ne peux pas raisonner sur : {question}"

        best = chains[0]
        last_fact = best.steps[-1].fact_found

        lines = [
            f"🔍 {best.depth} sauts (sur {len(chains)} branches explorées) :",
            f"   Meilleur chemin : {best.steps[0].fact_found[0]}",
        ]
        for s in best.steps:
            s, r, o, _ = s.fact_found
            lines.append(f"     → {r} → {o}")
        lines.append(f"   Cohérence: {best.total_coherence:.3f} | Type: {best.reasoning_type}")

        if len(chains) >= 2:
            alt = chains[1]
            if alt.steps:
                lines.append(f"   Chemin alternatif ({alt.depth} sauts, coh: {alt.total_coherence:.3f}):")
                lines.append(f"     {alt.steps[0].fact_found[0]} → ... → "
                           f"{alt.steps[-1].fact_found[2]}")

        return "\n".join(lines)

    def reason_deep(self, question: str, max_depth: int = 10) -> str:
        """
        Raisonnement profond — interface simplifiée.

        Retourne la conclusion en langage naturel.
        """
        chain = self.propagate(question, max_depth=max_depth)

        if not chain.steps:
            return f"Je ne peux pas raisonner sur : {question}"

        # Construire une réponse à partir de la chaîne
        last_fact = chain.steps[-1].fact_found
        conclusion = (
            f"En partant de « {chain.steps[0].fact_found[0]} » "
            f"et après {chain.depth} étapes de propagation, "
            f"j'arrive à : {last_fact[0]} {last_fact[1]} {last_fact[2]}. "
            f"(Cohérence: {chain.total_coherence:.2f}, "
            f"type: {chain.reasoning_type})"
        )
        return conclusion


# ═══════════════════════════════════════════════════════════════════════════════
# INTÉGRATION AVEC HARMONIC BRAIN
# ═══════════════════════════════════════════════════════════════════════════════

def deep_reason(brain, question: str, max_depth: int = 10) -> str:
    """
    Point d'entrée pour le raisonnement profond dans le brain.

    Usage dans harmonic_brain.py:
        from phase_amplifier import deep_reason
        result = deep_reason(self, question, max_depth=7)
    """
    amp = PhaseAmplifier(brain=brain)
    return amp.reason_deep(question, max_depth=max_depth)


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  PHASE AMPLIFIER — Test")
    print("=" * 60)

    # Test avec un mini-brain
    print("\n── Test : Propagation sur KB synthétique ──")
    from harmonic_brain import HarmonicBrain

    # KB avec une chaîne de 5 faits connectés
    kb = [
        ("pluie", "cause", "humidité du sol", "NATURE"),
        ("humidité du sol", "favorise", "croissance des plantes", "NATURE"),
        ("croissance des plantes", "produit", "oxygène", "NATURE"),
        ("oxygène", "est respiré par", "animaux", "NATURE"),
        ("animaux", "produisent", "CO2", "NATURE"),
        ("CO2", "est absorbé par", "plantes", "NATURE"),
        ("plantes", "utilisent", "photosynthèse", "NATURE"),
    ]
    brain = HarmonicBrain(kb, dim=64, use_holographic=False)

    amp = PhaseAmplifier(brain=brain, dim=64)

    # Test propagation
    chain = amp.propagate("pluie", max_depth=6)
    print(amp.explain(chain))

    print("\n✅ Test Phase Amplifier terminé")
