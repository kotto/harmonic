"""
Conscient Critique — Le Jugement Esthétique Ondulatoire
=========================================================
La beauté n'est pas subjective — c'est une HARMONIQUE.

PRINCIPE FONDATEUR :
  Une création est « belle » quand :
    cohérence / nouveauté → φ (1.618...)

  · Trop cohérent → banal, prévisible, déjà-vu
  · Trop nouveau → inintelligible, chaos, bruit
  · φ-équilibré → SUBLIME : à la fois reconnaissable ET surprenant

  C'est le nombre d'or — la proportion la plus esthétique de l'univers.
  On le retrouve dans les coquillages, les galaxies, les symphonies,
  les tableaux de la Renaissance. Pourquoi ? Parce que φ est le rapport
  d'onde qui maximise l'interférence constructive SANS créer de motif
  répétitif (c'est le « plus irrationnel » des nombres).

5 AXES D'ÉVALUATION :
  1. COHÉRENCE : l'idée résonne-t-elle avec l'inconscient ?
  2. NOUVEAUTÉ : l'idée est-elle différente de tout ce qui existe ?
  3. φ-BALANCE : |cohérence/nouveauté - φ| → distance au ratio d'or
  4. ÉLÉGANCE : impact / complexité (rasoir d'Occam ondulatoire)
  5. SURPRISE : dérivée de la nouveauté (l'idée s'améliore-t-elle ?)

RAFFINEMENT :
  Si une idée n'est pas au φ, le Critique suggère comment l'ajuster :
    · Trop cohérent → opération plus « sauvage » (convoluer, déphaser)
    · Trop nouveau → opération plus « sage » (superposer, corréler)
    · Itération jusqu'à convergence vers φ

Usage :
    from conscious_critic import ConsciousCritic

    critic = ConsciousCritic(brain)
    score = critic.evaluate(idea)
    # → {beauty: 0.87, coherence: 0.62, novelty: 0.38, phi_balance: 0.95, ...}
    
    if score['beauty'] < 0.7:
        refined = critic.refine(idea, max_iterations=3)
"""

import math
import time
import random
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # 0.618

# Seuils esthétiques
BEAUTY_THRESHOLD = 0.70      # en dessous → banal ou chaos
SUBLIME_THRESHOLD = 0.88     # au-dessus → exceptionnel
PHI_TOLERANCE = 0.15         # marge acceptable autour de φ
ELEGANCE_SIMPLICITY_WEIGHT = 0.3  # poids de la simplicité dans l'élégance


@dataclass
class AestheticScore:
    """Score esthétique complet d'une idée créative."""
    beauty: float              # score global (0-1), combinant tous les axes
    coherence: float           # résonance avec l'inconscient (0-1)
    novelty: float             # distance aux créations existantes (0-1)
    phi_balance: float         # proximité au ratio d'or (1.0 = parfait)
    elegance: float            # impact / complexité (0-1)
    surprise: float            # variation de nouveauté (0-1)
    
    # Diagnostic
    verdict: str = ""          # "sublime", "beau", "banal", "chaotique"
    suggestion: str = ""       # que faire pour améliorer ?
    phi_ratio: float = 0.0     # cohérence / nouveauté (brut)
    
    def __repr__(self):
        return (f"AestheticScore(beauty={self.beauty:.3f}, φ={self.phi_balance:.3f}, "
                f"coh={self.coherence:.3f}, nov={self.novelty:.3f}, "
                f"verdict={self.verdict})")


class ConsciousCritic:
    """
    Le Critique Esthétique — juge de la beauté des créations.
    
    N'émet pas d'opinion — mesure des harmoniques.
    La beauté = cohérence de phase équilibrée par φ.
    """

    def __init__(self, brain=None, dim: int = 512, encoder=None):
        self.brain = brain
        self.encoder = encoder
        self.dim = dim
        if brain is not None:
            self.encoder = brain.unconscious.encoder
            self.dim = brain.unconscious.dim

        # Historique d'évaluation (pour calculer la surprise)
        self._eval_history: List[AestheticScore] = []
        self._novelty_history: List[float] = []

        # Cache des ψ de l'inconscient (pour calculer la cohérence globale)
        self._unconscious_sample: List[np.ndarray] = []
        self._sample_size = 200
        self._creative_memory: List[np.ndarray] = []  # injecté par le Creator
        self._refresh_sample()

    def _get_psi(self, text: str) -> np.ndarray:
        """Récupère/crée un ψ avec cache."""
        if not hasattr(self, '_psi_cache'):
            self._psi_cache = {}
        if text in self._psi_cache:
            return self._psi_cache[text]
        # Fallback déterministe
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        v = v / (np.linalg.norm(v) + 1e-10)
        self._psi_cache[text] = v
        return v

    def _coherence(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """Cohérence de phase entre deux ψ."""
        if psi_a is None or psi_b is None:
            return 0.0
        dot = np.abs(np.dot(psi_a.conj(), psi_b))
        na = np.linalg.norm(psi_a)
        nb = np.linalg.norm(psi_b)
        return min(1.0, float(dot / (na * nb + 1e-10)))

    def _refresh_sample(self):
        """Rafraîchit l'échantillon de l'inconscient — utilise les MOTS individuels."""
        if self.brain is None:
            self._unconscious_sample = [self._get_psi(f"concept_{i}") for i in range(50)]
            return
        registry = list(self.brain.unconscious.registry.values())
        if registry:
            chosen = random.sample(registry, min(self._sample_size, len(registry)))
            self._unconscious_sample = []
            for r in chosen:
                if r.psi is not None:
                    self._unconscious_sample.append(r.psi)
                else:
                    for word in [r.sujet, r.relation, r.objet]:
                        if len(word) >= 2:
                            self._unconscious_sample.append(self._get_psi(word))
        if not self._unconscious_sample:
            self._unconscious_sample = [self._get_psi(f"concept_{i}") for i in range(50)]

    def inject_creative_memory(self, memory: List[np.ndarray]):
        """Injecte la mémoire créative depuis le ConsciousCreator."""
        self._creative_memory = memory

    # ═══════════════════════════════════════════════════════════════════════
    # 1. MESURES ESTHÉTIQUES
    # ═══════════════════════════════════════════════════════════════════════

    def _measure_coherence(self, psi: np.ndarray) -> float:
        """
        Cohérence globale : à quel point l'idée résonne avec l'inconscient.

        Mesure : similarité cosinus moyenne avec un échantillon de l'inconscient.
        · Proche de 1.0 → l'idée est « évidente » (tout le monde y aurait pensé)
        · Proche de 0.0 → l'idée est « déconnectée » (ne fait aucun sens)
        · ~0.5 → zone intéressante
        """
        if not self._unconscious_sample:
            return 0.5
        coherences = [self._coherence(psi, s) for s in self._unconscious_sample]
        return float(np.mean(coherences)) if coherences else 0.5

    def _measure_novelty(self, psi: np.ndarray) -> float:
        """
        Nouveauté : à quel point l'idée est DIFFÉRENTE de tout ce qui existe.

        Mesure : 1 - similarité max avec l'échantillon de l'inconscient.
        · Proche de 1.0 → radicalement nouveau (jamais vu)
        · Proche de 0.0 → déjà connu (cliché)
        · ~0.4 → zone intéressante
        """
        if not self._unconscious_sample:
            return 1.0
        max_sim = max(self._coherence(psi, s) for s in self._unconscious_sample)
        return 1.0 - max_sim

    def _measure_phi_balance(self, coherence: float, novelty: float) -> float:
        """
        φ-balance : proximité au nombre d'or.

        Idéalement : cohérence / nouveauté = φ
        (φ ≈ 1.618 → cohérence ~0.62, nouveauté ~0.38)

        Retourne un score (0-1) où 1.0 = ratio parfait.
        """
        if novelty < 1e-6:
            return 0.0
        ratio = coherence / novelty
        # Distance logarithmique au φ (pour que 2× ou ½× soient également distants)
        if ratio > 0 and PHI > 0:
            log_ratio = math.log(ratio)
            log_phi = math.log(PHI)
            distance = abs(log_ratio - log_phi) / log_phi  # normalisé
            return max(0.0, 1.0 - distance)
        return 0.0

    def _measure_elegance(self, psi: np.ndarray, coherence: float,
                          novelty: float) -> float:
        """
        Élégance : impact / complexité.

        Une idée élégante a un grand impact (nouveauté) pour une
        faible complexité (entropie du ψ).

        Mesure : novelty / entropie_normalisée(ψ)
        Pondéré par la simplicité (nombre de composantes spectrales dominantes).
        """
        # Entropie spectrale (combien de fréquences sont actives)
        freqs = np.fft.fft(psi)
        power = np.abs(freqs) ** 2
        total_power = np.sum(power) + 1e-10
        probs = power / total_power
        # Éviter log(0)
        probs = probs[probs > 1e-10]
        entropy = -np.sum(probs * np.log(probs))
        max_entropy = math.log(len(power))
        normalized_entropy = entropy / (max_entropy + 1e-10)

        # Simplicité = 1 - entropie normalisée (faible entropie = simple)
        simplicity = 1.0 - normalized_entropy

        # Élégance = nouveauté × simplicité
        elegance = novelty * (ELEGANCE_SIMPLICITY_WEIGHT + 
                             (1 - ELEGANCE_SIMPLICITY_WEIGHT) * simplicity)
        return float(elegance)

    def _measure_surprise(self, novelty: float) -> float:
        """
        Surprise : la nouveauté augmente-t-elle ?

        Dérivée de la nouveauté sur les dernières évaluations.
        Positive → l'idée devient plus intéressante.
        """
        self._novelty_history.append(novelty)
        if len(self._novelty_history) > 20:
            self._novelty_history = self._novelty_history[-20:]
        if len(self._novelty_history) < 3:
            return 0.5
        # Tendance récente
        recent = self._novelty_history[-5:]
        if len(recent) >= 2:
            trend = recent[-1] - recent[0]
            return 0.5 + trend * 2.0  # centré sur 0.5
        return 0.5

    # ═══════════════════════════════════════════════════════════════════════
    # 2. ÉVALUATION
    # ═══════════════════════════════════════════════════════════════════════

    def evaluate(self, psi: np.ndarray, sources: List[str] = None,
                 op_name: str = "") -> AestheticScore:
        """
        Évalue la beauté d'une idée créative.

        Args:
            psi: le ψ de l'idée
            sources: concepts sources (pour le diagnostic)
            op_name: opération créative utilisée

        Returns:
            AestheticScore complet
        """
        # Mesurer les 5 axes
        coherence = self._measure_coherence(psi)
        novelty = self._measure_novelty(psi)
        phi_balance = self._measure_phi_balance(coherence, novelty)
        elegance = self._measure_elegance(psi, coherence, novelty)
        surprise = self._measure_surprise(novelty)

        # Beauty = moyenne pondérée avec φ au centre
        beauty = (
            phi_balance * 0.35 +     # φ-balance est le critère principal
            elegance * 0.25 +        # l'élégance compte
            surprise * 0.15 +        # la surprise aussi
            (1.0 - abs(coherence - 0.5) * 2.0) * 0.15 +  # cohérence modérée = bonne
            novelty * 0.10           # nouveauté pure
        )
        beauty = min(1.0, max(0.0, beauty))

        # Diagnostic
        phi_ratio = coherence / (novelty + 1e-10)
        verdict, suggestion = self._diagnose(coherence, novelty, phi_balance,
                                              elegance, sources, op_name)

        score = AestheticScore(
            beauty=beauty,
            coherence=coherence,
            novelty=novelty,
            phi_balance=phi_balance,
            elegance=elegance,
            surprise=surprise,
            verdict=verdict,
            suggestion=suggestion,
            phi_ratio=phi_ratio,
        )

        self._eval_history.append(score)
        if len(self._eval_history) > 100:
            self._eval_history = self._eval_history[-100:]

        return score

    def _diagnose(self, coherence: float, novelty: float, phi_balance: float,
                  elegance: float, sources: List[str] = None,
                  op_name: str = "") -> Tuple[str, str]:
        """Diagnostique ce qui va ou ne va pas."""
        if phi_balance > SUBLIME_THRESHOLD:
            return ("sublime 🌟", "L'équilibre φ est parfait. Ne touchez à rien.")
        elif phi_balance > BEAUTY_THRESHOLD:
            return ("beau ✨", "Proche du φ. De légers ajustements suffiraient.")
        elif coherence > 0.7 and novelty < 0.3:
            suggestion = ("Trop prévisible. Essayez une opération plus audacieuse : "
                         "convoluer, déphaser, ou augmenter la température créative.")
            return ("banal 😐", suggestion)
        elif novelty > 0.7 and coherence < 0.3:
            suggestion = ("Trop chaotique. Essayez une opération plus sage : "
                         "superposer, corréler, ou réduire la température.")
            return ("chaotique 🌪️", suggestion)
        elif coherence < 0.3 and novelty < 0.3:
            return ("faible 💤", "L'idée ne résonne ni ne surprend. Changez de concepts sources.")
        else:
            return ("prometteur 🌱", "En bonne voie. Ajustez l'équilibre cohérence/nouveauté.")

    # ═══════════════════════════════════════════════════════════════════════
    # 3. RAFFINEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def refine(self, psi: np.ndarray, sources: List[str] = None,
               max_iterations: int = 5, target_beauty: float = BEAUTY_THRESHOLD,
               creator=None) -> Tuple[np.ndarray, List[AestheticScore]]:
        """
        Raffine une idée créative jusqu'à ce qu'elle atteigne la beauté cible.

        Le raffinement ajuste le ψ par petites perturbations guidées
        par le gradient esthétique.

        Args:
            psi: ψ initial de l'idée
            sources: concepts sources
            max_iterations: max d'itérations
            target_beauty: seuil de beauté à atteindre
            creator: ConsciousCreator optionnel pour ré-appliquer des opérations

        Returns:
            (ψ raffiné, historique des scores)
        """
        history = []
        current_psi = psi.copy()
        best_psi = psi.copy()
        best_score = None

        for iteration in range(max_iterations):
            score = self.evaluate(current_psi, sources)
            history.append(score)

            if best_score is None or score.beauty > best_score.beauty:
                best_score = score
                best_psi = current_psi.copy()

            if score.beauty >= target_beauty:
                break

            # Ajuster le ψ selon le diagnostic
            if score.verdict == "banal 😐":
                # Injecter du « bruit créatif » — petite rotation de phase aléatoire
                perturbation = np.random.randn(self.dim) + 1j * np.random.randn(self.dim)
                perturbation = perturbation / (np.linalg.norm(perturbation) + 1e-10)
                current_psi = current_psi + 0.2 * perturbation
            elif score.verdict == "chaotique 🌪️":
                # Ramener vers le centre de l'inconscient (moyenne des ψ existants)
                if self._unconscious_sample:
                    center = sum(self._unconscious_sample) / len(self._unconscious_sample)
                    center = center / (np.linalg.norm(center) + 1e-10)
                    current_psi = current_psi + 0.2 * center
            else:
                # Perturbation aléatoire légère (exploration)
                perturbation = np.random.randn(self.dim) + 1j * np.random.randn(self.dim)
                perturbation = perturbation / (np.linalg.norm(perturbation) + 1e-10)
                current_psi = current_psi + 0.05 * perturbation

            # Normaliser
            n = np.linalg.norm(current_psi)
            if n > 1e-10:
                current_psi = current_psi / n

            # Si on a un creator, essayer une opération différente
            if creator is not None and iteration % 2 == 0 and sources and len(sources) >= 2:
                try:
                    # Essayer une opération aléatoire
                    ops = ['superposer', 'convoluer', 'dephaser', 'interferer',
                           'correler', 'opposer', 'amplifier', 'spectrer']
                    op = random.choice(ops)
                    new_idea = creator.combine(sources[0], sources[1], op_name=op)
                    new_score = self.evaluate(new_idea.psi, sources, op)
                    if new_score.beauty > (best_score.beauty if best_score else 0):
                        best_psi = new_idea.psi.copy()
                        best_score = new_score
                        current_psi = new_idea.psi.copy()
                except Exception:
                    pass

        return best_psi, history

    # ═══════════════════════════════════════════════════════════════════════
    # 4. FILTRAGE
    # ═══════════════════════════════════════════════════════════════════════

    def filter_ideas(self, ideas: list, min_beauty: float = BEAUTY_THRESHOLD,
                     keep_best: int = 5) -> list:
        """
        Filtre et trie les idées par beauté.

        Ne garde que celles qui atteignent le seuil minimal.
        """
        scored = []
        for idea in ideas:
            psi = getattr(idea, 'psi', None)
            if psi is None:
                continue
            score = self.evaluate(psi, getattr(idea, 'sources', None),
                                 getattr(idea, 'op_name', ''))
            scored.append((idea, score))

        # Trier par beauté décroissante
        scored.sort(key=lambda x: -x[1].beauty)
        
        # Filtrer
        beautiful = [(idea, score) for idea, score in scored
                     if score.beauty >= min_beauty]
        
        return beautiful[:keep_best]

    def select_best(self, ideas: list) -> Tuple[any, AestheticScore]:
        """Sélectionne la plus belle idée parmi plusieurs."""
        filtered = self.filter_ideas(ideas, min_beauty=0.0, keep_best=1)
        if filtered:
            return filtered[0]
        return None, None

    # ═══════════════════════════════════════════════════════════════════════
    # 5. RAPPORT
    # ═══════════════════════════════════════════════════════════════════════

    def report(self, score: AestheticScore) -> str:
        """Génère un rapport esthétique en langage naturel."""
        lines = [
            f"🎨 RAPPORT ESTHÉTIQUE",
            f"   Beauté globale : {score.beauty:.3f} ({score.verdict})",
            f"   Cohérence     : {score.coherence:.3f} "
            f"{'← résonne bien' if 0.3 < score.coherence < 0.7 else '← extrême'}",
            f"   Nouveauté     : {score.novelty:.3f} "
            f"{'← surprenant' if score.novelty > 0.4 else '← déjà-vu'}",
            f"   φ-balance     : {score.phi_balance:.3f} "
            f"(ratio={score.phi_ratio:.2f}, cible φ={PHI:.2f})",
            f"   Élégance      : {score.elegance:.3f}",
            f"   Surprise      : {score.surprise:.3f}",
        ]
        if score.suggestion:
            lines.append(f"   💡 {score.suggestion}")
        return "\n".join(lines)

    @property
    def stats(self) -> dict:
        recent = self._eval_history[-20:] if self._eval_history else []
        avg_beauty = float(np.mean([s.beauty for s in recent])) if recent else 0.0
        return {
            'evaluations': len(self._eval_history),
            'avg_beauty': round(avg_beauty, 3),
            'sublime_count': sum(1 for s in recent if s.verdict.startswith('sublime')),
            'beautiful_count': sum(1 for s in recent if s.verdict in ('sublime 🌟', 'beau ✨')),
            'phi_mean': float(np.mean([s.phi_balance for s in recent])) if recent else 0.0,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  CONSCIENT CRITIQUE — Test")
    print("=" * 60)

    from harmonic_brain import HarmonicBrain
    from conscious_creator import ConsciousCreator

    kb = [
        ("pluie", "tombe sur", "la terre", "NATURE"),
        ("pluie", "fait pousser", "les fleurs", "NATURE"),
        ("musique", "est", "l art des sons", "CULTURE"),
        ("musique", "exprime", "les emotions", "CULTURE"),
        ("ocean", "est", "immense et profond", "NATURE"),
        ("ocean", "abrite", "des creatures mysterieuses", "NATURE"),
        ("silence", "precede", "la musique", "CULTURE"),
        ("silence", "est", "l absence de son", "CULTURE"),
        ("feu", "rechauffe", "les corps", "PHYSIQUE_FOND"),
        ("feu", "est", "une reaction chimique", "PHYSIQUE_FOND"),
        ("amour", "unit", "les etres", "EMOTION_POS"),
        ("temps", "s ecoule", "inexorablement", "PHYSIQUE_FOND"),
    ]
    brain = HarmonicBrain(kb, dim=64, use_holographic=False)
    creator = ConsciousCreator(brain=brain, dim=64)
    critic = ConsciousCritic(brain=brain, dim=64)

    # Test 1 : Évaluation d'idées
    print("\n── 1. Évaluation ──")
    for _ in range(3):
        idea = creator.combine(
            random.choice([f[0] for f in kb]),
            random.choice([f[0] for f in kb])
        )
        score = critic.evaluate(idea.psi, idea.sources, idea.op_name)
        print(f"  {idea.op_name}({idea.sources[0][:10]}, {idea.sources[1][:10]})")
        print(f"  → {score.verdict} (beauté={score.beauty:.3f}, φ={score.phi_balance:.3f})")

    # Test 2 : Raffinement
    print("\n── 2. Raffinement ──")
    idea = creator.combine("pluie", "musique", op_name="interferer")
    score_before = critic.evaluate(idea.psi, idea.sources, idea.op_name)
    print(f"  Avant : {score_before.verdict} (beauté={score_before.beauty:.3f})")
    
    refined_psi, history = critic.refine(idea.psi, idea.sources, max_iterations=5)
    score_after = critic.evaluate(refined_psi, idea.sources, idea.op_name)
    print(f"  Après : {score_after.verdict} (beauté={score_after.beauty:.3f})")
    print(f"  Évolution : {score_before.beauty:.3f} → {score_after.beauty:.3f}")

    # Test 3 : Rapport complet
    print(f"\n── 3. Rapport ──")
    print(critic.report(score_after))

    # Test 4 : Filtrage
    print(f"\n── 4. Filtrage ──")
    ideas = [creator.combine(
        random.choice([f[0] for f in kb]),
        random.choice([f[0] for f in kb])
    ) for _ in range(10)]
    best = critic.filter_ideas(ideas, min_beauty=0.4, keep_best=3)
    for idea, score in best:
        print(f"  {score.verdict} (beauté={score.beauty:.3f}) — "
              f"{idea.op_name}({idea.sources[0][:10]}, {idea.sources[1][:10]})")

    print(f"\n✅ Conscient Critique — {critic.stats}")
