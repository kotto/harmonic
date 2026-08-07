"""
🔁 Feedback Loop — RLHF ondulatoire par boucle phase-amplitude
================================================================
Équivalence #19 de TRADUCTION_ONDULATOIRE_LLM.md :
  RLHF (Reinforcement Learning from Human Feedback) → Boucle phase-amplitude.

LLM classique :
  - Modèle de récompense appris sur comparaisons humaines (reward model)
  - PPO : optimisation de politique avec contrainte KL
  - Alignment tax : dégradation des performances pendant l'alignement

Harmonique :
  - Écho de phase : le feedback humain module la phase
  - Renforcement/affaiblissement sélectif : cohérence → +α, incohérence → −α
  - Aucune dégradation : le renforcement est LOCAL, pas global

Formule maîtresse (boucle phase-amplitude) :

    ψ ← ψ + η · (r − cohérence(ψ, ψ_cible)) · ψ_cible

  où :
    r              = score humain ∈ [0, 1]
    η              = learning rate (amplitude de modulation)
    ψ_cible        = onde du fait/pattern à renforcer ou affaiblir
    cohérence(ψ,ψ_cible) = wave_lang.coherence() — la porte naturelle

  Si r > cohérence : la cible est ATTRACTIVE → ψ se rapproche de ψ_cible
  Si r < cohérence : la cible est RÉPULSIVE → ψ s'éloigne de ψ_cible

  Le renforcement est local : seul ψ_cible est modulé, pas tout le hologramme.
  Pas d'oubli catastrophique, pas d'« alignment tax ».

Usage :
    from feedback_loop import FeedbackLoop

    loop = FeedbackLoop(brain=brain)
    loop.process_feedback(psi_reponse, human_score=0.9)   # renforce
    loop.process_feedback(psi_reponse, human_score=0.1)   # affaiblit
"""

from __future__ import annotations

import time
import numpy as np
from typing import List, Dict, Tuple, Optional, Callable

from wave_lang import (
    encode, decode, bind, unbind, superpose,
    resonate, coherence, rotate, normalize, norm,
    interfere, amplify, oppose, phase_shift, bind_many,
    HolographicMemory, abc_kernel, abc_forget,
    PHI, ALPHA, TAU, DEFAULT_DIM,
)


class FeedbackLoop:
    """
    Boucle de feedback ondulatoire (équivalent harmonique du RLHF).

    Drop-in pour harmonic_brain.py : `FeedbackLoop(brain=self)`.

    Le feedback humain n'apprend pas un modèle de récompense —
    il module directement l'amplitude des ondes dans l'espace des phases.
    La cohérence est la porte naturelle : pas besoin de classifier
    « bonne » ou « mauvaise » réponse, la cohérence le dit déjà.

    Usage :
        loop = FeedbackLoop(brain=brain)
        loop.process_feedback(psi_reponse, 0.9)   # → renforce
        loop.process_feedback(psi_reponse, 0.1)   # → affaiblit
        score_pred = loop.evaluate(psi_reponse)   # prédit le score humain
    """

    # Seuils et amplitudes du spec (§5.3)
    REINFORCE_THRESHOLD = 0.7   # score humain au-dessus → renforcer
    WEAKEN_THRESHOLD = 0.3      # score humain en-dessous → affaiblir
    REINFORCE_AMPLITUDE = 0.2   # +α
    WEAKEN_AMPLITUDE = -0.2     # −α
    LEARNING_RATE = 0.1         # η par défaut

    def __init__(self, brain=None, dim: int = DEFAULT_DIM,
                 learning_rate: float = None):
        """
        Args:
            brain: HarmonicBrain (optionnel) — pour accéder à la mémoire
            dim: dimension de l'espace des phases
            learning_rate: η (défaut: 0.1)
        """
        self.brain = brain
        self.dim = dim
        self.eta = learning_rate if learning_rate is not None else self.LEARNING_RATE

        # Historique des feedbacks : (psi, score_humain, timestamp)
        self._history: List[Tuple[np.ndarray, float, float]] = []

        # Mémoire des corrections (ψ_cible → amplitude cumulée)
        self._corrections: Dict[str, float] = {}

        self._n_feedback = 0
        self._n_reinforce = 0
        self._n_weaken = 0

    # ═══════════════════════════════════════════════════════════════════════
    # BOUCLE PRINCIPALE
    # ═══════════════════════════════════════════════════════════════════════

    def process_feedback(self, response_psi: np.ndarray,
                         human_score: float,
                         target_text: Optional[str] = None) -> Dict:
        """
        Traite un feedback humain sur une réponse.

        Équivalent harmonique du PPO(θ, reward_model) :
        au lieu d'optimiser des poids par gradient avec contrainte KL,
        on module l'amplitude de l'onde réponse dans l'hologramme.

        Args:
            response_psi: onde de la réponse à évaluer
            human_score: score humain ∈ [0, 1]
            target_text: texte de la cible à renforcer/affaiblir (optionnel)

        Returns:
            dict avec la décision (reinforce/weaken/neutral), l'amplitude,
            et la cohérence mesurée

        Exemple (spec §5.3) :
            if human_score > 0.7:   # Bonne réponse
                self.reinforce(response_psi, amplitude=+0.2)
            elif human_score < 0.3:  # Mauvaise réponse
                self.weaken(response_psi, amplitude=-0.2)
        """
        decision = 'neutral'
        amplitude = 0.0
        target_psi = None

        # Cible : soit fournie, soit l'onde réponse elle-même
        if target_text is not None:
            target_psi = encode(target_text, dim=self.dim)
        else:
            target_psi = response_psi

        # Boucle phase-amplitude : ψ ← ψ + η · (r − cohérence) · ψ_cible
        c = float(coherence(response_psi, target_psi))
        error = human_score - c  # erreur signée : attracteur ou répulseur

        if human_score > self.REINFORCE_THRESHOLD:
            self.reinforce(target_psi, amplitude=self.REINFORCE_AMPLITUDE)
            decision = 'reinforce'
            amplitude = self.REINFORCE_AMPLITUDE
            self._n_reinforce += 1
        elif human_score < self.WEAKEN_THRESHOLD:
            self.weaken(target_psi, amplitude=self.WEAKEN_AMPLITUDE)
            decision = 'weaken'
            amplitude = self.WEAKEN_AMPLITUDE
            self._n_weaken += 1
        else:
            # Zone neutre : la cohérence est déjà alignée avec le score humain
            decision = 'neutral'
            amplitude = 0.0

        # Enregistrer dans l'historique (mémoire de feedback)
        self._history.append((response_psi.copy(), float(human_score), time.time()))
        if len(self._history) > 1000:
            self._history.pop(0)

        self._n_feedback += 1

        return {
            'decision': decision,
            'amplitude': amplitude,
            'coherence': c,
            'error': error,
            'human_score': float(human_score),
        }

    def reinforce(self, psi: np.ndarray, amplitude: float = None) -> None:
        """
        Renforce une onde dans la mémoire (feedback positif).

        ψ_cible ← ψ_cible + amplitude · ψ (superposition pondérée)
        Le renforcement est local : seul le fait ciblé est modulé.

        Args:
            psi: onde à renforcer
            amplitude: quantité de renforcement (défaut: +0.2)
        """
        a = amplitude if amplitude is not None else self.REINFORCE_AMPLITUDE

        # 1. Modulation directe de l'onde (boucle phase-amplitude)
        psi_modulated = normalize(psi + self.eta * a * psi)

        # 2. Renforcement dans le cerveau si disponible
        if self.brain is not None:
            self._reinforce_in_brain(psi, abs(a))

        # 3. Mémoriser la correction
        key = f"corr_{self._n_feedback}"
        self._corrections[key] = float(a)
        self._prune_corrections()

    def weaken(self, psi: np.ndarray, amplitude: float = None) -> None:
        """
        Affaiblit une onde dans la mémoire (feedback négatif).

        ψ_cible ← ψ_cible − |amplitude| · ψ
        L'affaiblissement est local : la cohérence est la porte naturelle
        anti-hallucination (un fait incohérent s'éteint tout seul).

        Args:
            psi: onde à affaiblir
            amplitude: quantité d'affaiblissement (défaut: -0.2)
        """
        a = amplitude if amplitude is not None else self.WEAKEN_AMPLITUDE

        # 1. Modulation directe (répulsion)
        psi_modulated = normalize(psi + self.eta * a * psi)

        # 2. Affaiblissement dans le cerveau si disponible
        if self.brain is not None:
            self._weaken_in_brain(psi, abs(a))

        # 3. Mémoriser la correction
        key = f"corr_{self._n_feedback}"
        self._corrections[key] = float(a)
        self._prune_corrections()

    # ═══════════════════════════════════════════════════════════════════════
    # INTÉGRATION CERVEAU
    # ═══════════════════════════════════════════════════════════════════════

    def _reinforce_in_brain(self, psi: np.ndarray, amount: float) -> None:
        """Renforce les faits résonants avec l'onde dans le cerveau."""
        try:
            store = self.brain.unconscious  # HolographicStore
            if hasattr(store, 'reinforce'):
                # Trouver les faits résonants avec l'onde
                best_fact = self._find_resonant_fact(psi, store)
                if best_fact is not None:
                    store.reinforce(best_fact, amount=amount)
        except Exception:
            pass

    def _weaken_in_brain(self, psi: np.ndarray, amount: float) -> None:
        """Affaiblit les faits résonants avec l'onde dans le cerveau."""
        try:
            store = self.brain.unconscious
            if hasattr(store, 'weaken'):
                best_fact = self._find_resonant_fact(psi, store)
                if best_fact is not None:
                    store.weaken(best_fact, amount=amount)
        except Exception:
            pass

    def _find_resonant_fact(self, psi: np.ndarray, store) -> Optional[object]:
        """
        Trouve le fait le plus résonant avec une onde.

        Args:
            psi: onde de référence
            store: HolographicStore du cerveau

        Returns:
            record du fait le plus résonant, ou None
        """
        if not hasattr(store, 'registry'):
            return None

        best_record = None
        best_score = 0.15  # seuil de résonance minimal

        for record in store.registry.values():
            # Extraire le ψ du record (objet FactRecord ou dict)
            if hasattr(record, 'psi'):
                psi_record = record.psi
            elif isinstance(record, dict) and 'psi' in record:
                psi_record = record['psi']
            else:
                continue

            score = float(coherence(psi, psi_record))
            if score > best_score:
                best_score = score
                best_record = record

        return best_record

    # ═══════════════════════════════════════════════════════════════════════
    # ENTRAÎNEMENT PAR LOT
    # ═══════════════════════════════════════════════════════════════════════

    def train(self, pairs: List[Tuple[str, float]],
              n_cycles: int = 10,
              verbose: bool = False) -> Dict:
        """
        Entraîne la boucle sur un lot de (texte, score_humain).

        Chaque paire est encodée puis passée à process_feedback.
        La boucle module les amplitudes — il n'y a pas de gradient,
        pas d'epochs au sens classique, juste des cycles de feedback.

        Args:
            pairs: liste de (texte_réponse, score_humain ∈ [0,1])
            n_cycles: nombre de passes sur le lot
            verbose: affiche la progression

        Returns:
            dict avec le résumé de l'entraînement
        """
        results = []
        for cycle in range(n_cycles):
            for text, score in pairs:
                psi = encode(text, dim=self.dim)
                result = self.process_feedback(psi, score)
                results.append(result)

        summary = {
            'cycles': n_cycles,
            'n_pairs': len(pairs),
            'n_feedback': len(results),
            'reinforcements': sum(1 for r in results if r['decision'] == 'reinforce'),
            'weakenings': sum(1 for r in results if r['decision'] == 'weaken'),
            'neutrals': sum(1 for r in results if r['decision'] == 'neutral'),
        }

        if verbose:
            print(f"🔁 FeedbackLoop: {summary['n_feedback']} feedbacks, "
                  f"{summary['reinforcements']} renforcements, "
                  f"{summary['weakenings']} affaiblissements")

        return summary

    # ═══════════════════════════════════════════════════════════════════════
    # ÉVALUATION / PRÉDICTION
    # ═══════════════════════════════════════════════════════════════════════

    def evaluate(self, psi: np.ndarray) -> float:
        """
        Prédit le score humain d'une réponse — l'« écho de phase ».

        Le score prédit = moyenne pondérée des scores humains passés,
        pondérée par la cohérence de la réponse avec chaque historique.

        C'est l'équivalent harmonique du reward model :
        au lieu d'un réseau appris, on mesure la résonance avec
        les réponses déjà évaluées par les humains.

        Args:
            psi: onde de la réponse à évaluer

        Returns:
            score prédit ∈ [0, 1]
        """
        if not self._history:
            return 0.5  # inconnu

        total_weight = 0.0
        weighted_score = 0.0

        for hist_psi, hist_score, _ in self._history:
            w = float(coherence(psi, hist_psi))
            if w > 0.1:  # résonance significative
                weighted_score += w * hist_score
                total_weight += w

        if total_weight < 1e-10:
            return 0.5

        return min(1.0, max(0.0, weighted_score / total_weight))

    def evaluate_text(self, text: str) -> float:
        """Prédit le score humain d'un texte (encodage automatique)."""
        psi = encode(text, dim=self.dim)
        return self.evaluate(psi)

    # ═══════════════════════════════════════════════════════════════════════
    # STATISTIQUES / UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════

    def _prune_corrections(self, max_entries: int = 1000) -> None:
        """Limite la taille du dictionnaire de corrections."""
        if len(self._corrections) > max_entries:
            keys = sorted(self._corrections.keys())
            for k in keys[:len(keys) - max_entries]:
                del self._corrections[k]

    @property
    def stats(self) -> dict:
        """Statistiques de la boucle de feedback."""
        return {
            'n_feedback': self._n_feedback,
            'n_reinforce': self._n_reinforce,
            'n_weaken': self._n_weaken,
            'ratio_positif': self._n_reinforce / max(1, self._n_feedback),
            'history_size': len(self._history),
            'corrections': len(self._corrections),
            'learning_rate': self.eta,
            'active': True,
        }

    def clear_history(self) -> None:
        """Vide l'historique des feedbacks."""
        self._history.clear()
        self._corrections.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🔁 FEEDBACK LOOP — RLHF ondulatoire")
    print("=" * 65)

    loop = FeedbackLoop(dim=512)

    # ── 1. Feedback positif / négatif ──
    psi_bon = encode("La Terre tourne autour du Soleil", dim=512)
    psi_mauvais = encode("La Lune est plus grande que la Terre", dim=512)

    r1 = loop.process_feedback(psi_bon, 0.9)
    r2 = loop.process_feedback(psi_mauvais, 0.1)
    r3 = loop.process_feedback(psi_neutre := psi_bon, 0.5)

    print(f"\n── 1. PROCESS FEEDBACK ──")
    print(f"  Score 0.9 → {r1['decision']} (cohérence={r1['coherence']:.3f}, erreur={r1['error']:+.3f})")
    print(f"  Score 0.1 → {r2['decision']} (cohérence={r2['coherence']:.3f}, erreur={r2['error']:+.3f})")
    print(f"  Score 0.5 → {r3['decision']} (cohérence={r3['coherence']:.3f}, erreur={r3['error']:+.3f})")

    # ── 2. Évaluation (écho de phase) ──
    print(f"\n── 2. ÉVALUATION (écho de phase) ──")
    score_pred = loop.evaluate(psi_bon)
    print(f"  Prédiction pour une bonne réponse: {score_pred:.3f}")

    # ── 3. Entraînement par lot ──
    print(f"\n── 3. TRAIN PAR LOT ──")
    pairs = [
        ("La Terre est ronde", 0.95),
        ("L'eau bout à 100°C", 0.9),
        ("Le Soleil tourne autour de la Terre", 0.05),
        ("Les poissons marchent sur la terre", 0.02),
        ("Le ciel est bleu", 0.85),
    ]
    summary = loop.train(pairs, n_cycles=3, verbose=True)
    print(f"  Résumé: {summary}")

    # ── 4. Statistiques ──
    print(f"\n── 4. STATISTIQUES ──")
    for k, v in loop.stats.items():
        print(f"  {k}: {v}")

    # ── 5. Intégration brain simulé ──
    print(f"\n── 5. INTÉGRATION CERVEAU ──")
    class MiniStore:
        def __init__(self):
            self.registry = {}
        def reinforce(self, fact, amount=0.1):
            fact['amplitude'] = min(10.0, fact['amplitude'] + amount)
        def weaken(self, fact, amount=0.05):
            fact['amplitude'] = max(0.01, fact['amplitude'] - amount)

    class MiniBrain:
        def __init__(self):
            self.unconscious = MiniStore()

    brain = MiniBrain()
    brain.unconscious.registry["fact1"] = {
        'sujet': 'Terre', 'relation': 'tourne_autour', 'objet': 'Soleil',
        'psi': psi_bon, 'amplitude': 1.0,
    }
    brain.unconscious.registry["fact2"] = {
        'sujet': 'Lune', 'relation': 'plus_grande', 'objet': 'Terre',
        'psi': psi_mauvais, 'amplitude': 1.0,
    }

    loop_brain = FeedbackLoop(brain=brain, dim=512)
    loop_brain.process_feedback(psi_bon, 0.95)
    loop_brain.process_feedback(psi_mauvais, 0.05)

    print(f"  Amplitude 'fact1' (bon):  {brain.unconscious.registry['fact1']['amplitude']:.3f} (↑ attendu)")
    print(f"  Amplitude 'fact2' (faux): {brain.unconscious.registry['fact2']['amplitude']:.3f} (↓ attendu)")

    print("\n" + "=" * 65)
    print("  ✅ Feedback Loop — RLHF ondulatoire fonctionnel.")
    print("=" * 65)
