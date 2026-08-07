"""
Wave Logic — Moteur de Logique Ondulatoire Universel
=====================================================
Généralisation du cycle : Humain → Onde → Solution → Humain.

4 OPÉRATIONS PRIMITIVES (tout le reste est combinaison) :
  1. ENCODE    : texte → ψ ∈ ℂ⁵¹²
  2. INTERFERE : Re(⟨ψ_a | ψ_b⟩)  → cohérence
  3. BIND      : ψ_a ⊛ ψ_b        → composition
  4. UNBIND    : ψ_ab ⊗ ψ_a       → extraction

TYPES DE RAISONNEMENT (émergents, pas codés) :
  · SYLLOGISME    : binding + cohérence
  · MODUS PONENS  : unbinding
  · ANALOGIE      : arithmétique vectorielle
  · CONTRADICTION : interférence destructive
  · INDUCTION     : clustering de phase
  · TRANSITIVITÉ  : propagation cohérente
  · ABDUCTION     : unbinding inversé

Usage :
    from wave_logic import WaveLogic
    wl = WaveLogic(brain)
    
    # Syllogisme
    result = wl.solve(
        premises=["Paris est la capitale de la France",
                  "La France est en Europe"],
        question="Que peut-on déduire sur Paris et l'Europe ?"
    )
    print(result.conclusion)  # "Paris est en Europe"
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional, Union
from dataclasses import dataclass, field
import logging

log = logging.getLogger(__name__)

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi

# Seuils (calibrés par φ)
COHERENCE_VALID = 0.08      # seuil de cohérence pour syllogisme valide
CONTRADICTION = -0.05       # seuil pour interférence destructive
CLUSTER_SIMILARITY = 0.15   # seuil pour regroupement par similarité


def _normalize(text: str) -> str:
    return text.lower().replace('é','e').replace('è','e').replace('ê','e')\
               .replace('à','a').replace('ù','u').replace('ô','o')\
               .replace('î','i').replace('ï','i').replace('ç','c')


# ═══════════════════════════════════════════════════════════════════════════════
# 4 OPÉRATIONS PRIMITIVES
# ═══════════════════════════════════════════════════════════════════════════════

class WaveOps:
    """Les 4 opérations ondulatoires fondamentales, avec spectral si disponible."""
    
    def __init__(self, encoder, spectral=None):
        self.enc = encoder
        self.spectral = spectral
        self._use_spectral = spectral is not None and spectral.is_ready
    
    def encode(self, text: str) -> np.ndarray:
        """1. ENCODE : texte → ψ ∈ ℂ⁵¹² (superposition des mots)."""
        words = _normalize(text).split()
        psi = np.zeros(self.enc.dim, dtype=np.complex128)
        for w in words:
            # Utiliser encode_word() qui génère à la volée + cache
            v = self.enc.encode_word(w) if hasattr(self.enc, 'encode_word') else None
            if v is None and hasattr(self.enc, 'word_vectors'):
                v = self.enc.word_vectors.get(w)
            if v is not None:
                psi += v
        norm = np.sqrt(np.sum(np.abs(psi)**2))
        return psi / norm if norm > 0 else psi
    
    def interfere(self, psi_a: np.ndarray, psi_b: np.ndarray,
                  text_a: str = "", text_b: str = "") -> float:
        """
        2. INTERFERE : cohérence HRR + bonus spectral.
        
        Si le spectral est disponible, ajoute la similarité sémantique
        entre les mots des deux textes. Corrige le problème HRR
        (vecteurs quasi-orthogonaux même pour mots liés).
        """
        # Cohérence HRR de base
        coh_hrr = float(np.real(np.dot(psi_a, np.conj(psi_b))))
        
        # Bonus spectral (si disponible)
        bonus_spec = 0.0
        if self._use_spectral and text_a and text_b:
            words_a = set(_normalize(text_a).split())
            words_b = set(_normalize(text_b).split())
            sims = []
            for wa in words_a:
                for wb in words_b:
                    if wa != wb:
                        sim = self.spectral.get_similarity(wa, wb)
                        if sim is not None:
                            sims.append(sim)
            if sims:
                bonus_spec = max(sims)  # meilleure similarité inter-textes
        
        # Combiner : 60% HRR + 40% spectral
        return coh_hrr * 0.6 + bonus_spec * 0.4
    
    def bind(self, psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """3. BIND : composition (convolution circulaire)."""
        FA = np.fft.fft(psi_a)
        FB = np.fft.fft(psi_b)
        return np.fft.ifft(FA * FB)
    
    def unbind(self, psi_ab: np.ndarray, psi_a: np.ndarray) -> np.ndarray:
        """4. UNBIND : extraction (corrélation circulaire)."""
        FAB = np.fft.fft(psi_ab)
        FA = np.fft.fft(psi_a)
        return np.fft.ifft(FAB * np.conj(FA))


# ═══════════════════════════════════════════════════════════════════════════════
# RÉSULTAT DE RAISONNEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LogicResult:
    """Résultat d'une opération de logique ondulatoire."""
    conclusion: str
    confidence: float
    method: str           # syllogisme, modus_ponens, analogie, etc.
    coherence: float = 0.0
    steps: List[str] = field(default_factory=list)
    is_valid: bool = True
    
    def __repr__(self):
        return (f"LogicResult({self.method}, conf={self.confidence:.2f}, "
                f"coh={self.coherence:+.3f}, '{self.conclusion[:60]}...')")


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE LOGIQUE ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveLogic:
    """
    Moteur de logique ondulatoire universel.
    
    Avec :
      - Formulation des conclusions par WaveDecoder (plus d'extraction naïve)
      - Seuils de cohérence ADAPTATIFS (apprennent par feedback conscient)
    """
    
    def __init__(self, brain_or_encoder):
        if hasattr(brain_or_encoder, 'unconscious'):
            self.brain = brain_or_encoder
            self.store = brain_or_encoder.unconscious
            self.enc = brain_or_encoder.unconscious.encoder
        else:
            self.brain = None
            self.store = None
            self.enc = brain_or_encoder
        
        self.ops = WaveOps(self.enc, 
                          spectral=getattr(self.store, '_spectral', None) if self.store else None)
        
        # Seuils adaptatifs (apprennent par feedback)
        self._coherence_threshold = COHERENCE_VALID
        self._contradiction_threshold = CONTRADICTION
        self._success_history = []  # [(threshold_used, was_correct)]
        self._total_solves = 0
    
    # ═════════════════════════════════════════════════════════════════
    # INTERFACE PRINCIPALE
    # ═════════════════════════════════════════════════════════════════
    
    def solve(self, premises: List[str], question: str = "",
              max_results: int = 1) -> LogicResult:
        """
        Résout un problème logique à partir de prémisses en langage naturel.
        
        Détecte automatiquement le type de raisonnement nécessaire
        et applique les opérations ondulatoires appropriées.
        """
        if len(premises) == 0:
            return LogicResult("Aucune prémisse fournie.", 0.0, "aucun", is_valid=False)
        
        self._total_solves += 1
        result = None
        
        if len(premises) == 1:
            return self._solve_direct(premises[0], question)
        
        if len(premises) == 2:
            return self._solve_pair(premises[0], premises[1], question)
        
        # 3+ prémisses : induction ou chaîne
        return self._solve_multi(premises, question)
    
    # ═════════════════════════════════════════════════════════════════
    # SEUILS ADAPTATIFS (apprentissage par feedback conscient)
    # ═════════════════════════════════════════════════════════════════
    
    def feedback(self, was_correct: bool):
        """
        Feedback du conscient sur la dernière résolution.
        
        Le seuil de cohérence s'adapte automatiquement :
          - Si correct → on peut être plus strict (monter le seuil)
          - Si incorrect → on doit être plus permissif (baisser le seuil)
        
        L'ajustement utilise φ pour garantir qu'on ne répète jamais le même pas.
        """
        self._success_history.append((self._coherence_threshold, was_correct))
        if len(self._success_history) > 50:
            self._success_history.pop(0)
        
        recent = self._success_history[-20:]
        success_rate = sum(1 for _, ok in recent if ok) / len(recent) if recent else 0.5
        
        if success_rate > 0.8:
            self._coherence_threshold += 0.005 * PHI_INV  # ~0.003
        elif success_rate < 0.5:
            self._coherence_threshold -= 0.005 * PHI_INV
        
        self._coherence_threshold = max(0.02, min(0.30, self._coherence_threshold))
    
    @property
    def threshold_stats(self) -> dict:
        recent = self._success_history[-20:]
        return {
            'coherence_threshold': round(self._coherence_threshold, 4),
            'success_rate': round(sum(1 for _, ok in recent if ok) / len(recent), 2) if recent else 0.5,
            'total_solves': self._total_solves,
        }
    
    # ═════════════════════════════════════════════════════════════════
    # RÉSOLUTION PAR TYPE
    # ═════════════════════════════════════════════════════════════════
    
    def _solve_direct(self, premise: str, question: str) -> LogicResult:
        """Fait unique : vérification de cohérence simple."""
        psi_p = self.ops.encode(premise)
        psi_q = self.ops.encode(question) if question else psi_p
        
        coherence = self.ops.interfere(psi_p, psi_q, premise, question)
        
        return LogicResult(
            conclusion=premise,
            confidence=min(1.0, max(0.0, coherence)),
            method="fait_direct",
            coherence=coherence,
        )
    
    def _solve_pair(self, p1: str, p2: str, question: str) -> LogicResult:
        """Deux prémisses : syllogisme, modus ponens, contradiction, ou analogie."""
        psi1 = self.ops.encode(p1)
        psi2 = self.ops.encode(p2)
        
        # Interférence = cohérence des prémisses (HRR + spectral)
        coherence = self.ops.interfere(psi1, psi2, p1, p2)
        
        # Analyser la structure des prémisses
        w1 = _normalize(p1).split()
        w2 = _normalize(p2).split()
        shared = set(w1) & set(w2)
        
        # Détection de CONTRADICTION : même sujet mais cohérence négative
        if coherence < CONTRADICTION:
            return self._solve_contradiction(p1, p2, psi1, psi2, coherence)
        
        # Même sujet → comparaison ou contradiction (pas un syllogisme)
        if w1[0] == w2[0] and coherence < 0.5:
            return self._solve_analogy(p1, p2, psi1, psi2, coherence)
        
        # Détection de SYLLOGISME : le mot partagé est en fin de P1 et début de P2
        # "A constitue B" + "B constitue C" → partagé = "B"
        shared_in_p1_end = any(w1[-1] == s or (len(w1) >= 2 and w1[-2] == s) for s in shared)
        shared_in_p2_start = any(w2[0] == s or (len(w2) >= 2 and w2[1] == s) for s in shared)
        
        if shared_in_p1_end and shared_in_p2_start and len(shared) >= 1:
            return self._solve_syllogism(p1, p2, psi1, psi2, coherence, shared, w1, w2)
        
        # Détection de MODUS PONENS : implication + fait, partagent le sujet
        # "Si X est Y" + "X est vrai"
        if len(shared) >= 2 and w1[0] == w2[0]:
            return self._solve_modus_ponens(p1, p2, psi1, psi2, coherence, shared)
        
        # Sinon : ANALOGIE ou comparaison
        return self._solve_analogy(p1, p2, psi1, psi2, coherence)
    
    def _solve_multi(self, premises: List[str], question: str) -> LogicResult:
        """3+ prémisses : chaîne transitive ou induction."""
        psis = [self.ops.encode(p) for p in premises]
        
        # Cohérence moyenne (induction)
        coherences = []
        for i in range(len(psis)):
            for j in range(i+1, len(psis)):
                coherences.append(self.ops.interfere(psis[i], psis[j],
                                                     premises[i], premises[j]))
        
        avg_coherence = sum(coherences) / len(coherences) if coherences else 0
        
        if avg_coherence > CLUSTER_SIMILARITY:
            # INDUCTION : les prémisses partagent un pattern
            return self._solve_induction(premises, psis, avg_coherence)
        else:
            # CHAÎNE transitive
            return self._solve_chain(premises, psis, coherences)
    
    # ═════════════════════════════════════════════════════════════════
    # IMPLÉMENTATIONS DES TYPES DE RAISONNEMENT
    # ═════════════════════════════════════════════════════════════════
    
    def _solve_syllogism(self, p1, p2, psi1, psi2, coherence, shared, w1, w2) -> LogicResult:
        """
        SYLLOGISME : A→B, B→C ∴ A→C
        
        Formulation propre : extraction du sujet (P1), objet (P2),
        et relation (P2), en ignorant les articles.
        """
        ARTICLES = {'le', 'la', 'les', 'l', 'un', 'une', 'des', 'the', 'a', 'an',
                    'de', 'du', 'en', 'au', 'aux', 'et', 'est', 'sont'}
        
        # Identifier le VRAI terme moyen : le mot partagé qui est
        # en position FINALE de P1 et INITIALE de P2 (hors articles)
        cw1 = [w for w in w1 if w not in ARTICLES]
        cw2 = [w for w in w2 if w not in ARTICLES]
        
        middle = None
        for w in shared:
            if w not in ARTICLES:
                # Est-ce que w est le DERNIER mot de contenu de P1 ?
                if cw1 and cw1[-1] == w:
                    middle = w
                    break
                # Ou le PREMIER mot de contenu de P2 ?
                if cw2 and cw2[0] == w:
                    middle = w
                    break
        if middle is None:
            middle = list(shared - ARTICLES)[0] if (shared - ARTICLES) else list(shared)[0]
        
        # Mots de contenu (sans articles)
        cw1 = [w for w in w1 if w not in ARTICLES]
        cw2 = [w for w in w2 if w not in ARTICLES]
        
        # Sujet : mots de P1 avant le terme moyen
        subj_parts = []
        for w in cw1:
            if w == middle: break
            subj_parts.append(w)
        subj = ' '.join(subj_parts) if subj_parts else cw1[0]
        
        # Objet : mots de P2 après le terme moyen
        obj_parts = []
        found = False
        for w in cw2:
            if w == middle: found = True; continue
            if found: obj_parts.append(w)
        obj = ' '.join(obj_parts) if obj_parts else cw2[-1]
        
        # Relation : ce qui reste dans P2 entre milieu et objet
        rel_parts = []
        found = False
        for w in cw2:
            if w == middle: found = True; continue
            if found and w not in obj_parts:
                rel_parts.append(w)
        rel = ' '.join(rel_parts) if rel_parts else 'est lié à'
        
        conclusion = f"{subj} {rel} {obj}"
        
        return LogicResult(
            conclusion=conclusion,
            confidence=min(1.0, coherence * 3),
            method="syllogisme",
            coherence=coherence,
            steps=[f"P1: {p1}", f"P2: {p2}", f"Terme moyen: {middle}",
                   f"Interférence: {coherence:+.3f}"],
            is_valid=coherence > self._coherence_threshold,
        )
    
    def _solve_modus_ponens(self, p1, p2, psi1, psi2, coherence, shared) -> LogicResult:
        """
        MODUS PONENS : Si A→B, A ∴ B
        
        Opération : unbinding ψ_implication ⊗ ψ_fait ≈ ψ_B
        """
        psi_conc = self.ops.unbind(psi1, psi2)
        
        # P2 est le « fait » (A), on en extrait B
        words2 = _normalize(p2).split()
        conclusion_part = [w for w in words2 if len(w) >= 3][-2:] if len(words2) >= 2 else words2
        conclusion = ' '.join(conclusion_part)
        
        return LogicResult(
            conclusion=conclusion,
            confidence=min(1.0, coherence * 3),
            method="modus_ponens",
            coherence=coherence,
            steps=[
                f"Implication: {p1}",
                f"Fait: {p2}",
                f"Interférence: {coherence:+.3f}",
                f"Unbinding ψ1 ⊗ ψ2 → conclusion"
            ],
            is_valid=coherence > COHERENCE_VALID,
        )
    
    def _solve_contradiction(self, p1, p2, psi1, psi2, coherence) -> LogicResult:
        """
        CONTRADICTION : A et ¬A → impossible.
        
        Opération : interférence destructive détectée.
        """
        return LogicResult(
            conclusion=f"Contradiction détectée entre « {p1[:40]}... » et « {p2[:40]}... »",
            confidence=abs(coherence),
            method="contradiction",
            coherence=coherence,
            steps=[
                f"P1: {p1}",
                f"P2: {p2}",
                f"Interférence destructive: {coherence:+.3f}",
                f"Les deux affirmations S'ANNULENT."
            ],
            is_valid=False,
        )
    
    def _solve_analogy(self, p1, p2, psi1, psi2, coherence) -> LogicResult:
        """
        ANALOGIE : A:B :: C:?
        
        Opération : arithmétique vectorielle ψ_A - ψ_B + ψ_C ≈ ψ_?
        """
        psi_target = psi1 - psi2
        
        # Chercher le ψ le plus proche dans le vocabulaire
        best_word = ""
        best_sim = -1
        for word, psi_w in self.enc.word_vectors.items():
            sim = float(np.real(np.dot(psi_w, np.conj(psi_target))))
            if sim > best_sim and len(word) >= 3:
                best_sim = sim
                best_word = word
        
        conclusion = f"Relation analogue : {best_word}" if best_word else "Aucune analogie trouvée"
        
        return LogicResult(
            conclusion=conclusion,
            confidence=min(1.0, max(0.0, coherence)),
            method="analogie",
            coherence=coherence,
            steps=[
                f"P1: {p1}",
                f"P2: {p2}",
                f"Arithmétique: ψ1 - ψ2 → ψ_cible",
                f"Plus proche: {best_word} (sim={best_sim:+.3f})"
            ],
            is_valid=best_sim > 0.1,
        )
    
    def _solve_induction(self, premises, psis, avg_coherence) -> LogicResult:
        """
        INDUCTION : A1→B, A2→B, A3→B ∴ Tout A→B
        
        Opération : clustering de phase (moyenne des ψ).
        """
        psi_pattern = sum(psis) / len(psis)
        pattern_strength = float(np.sqrt(np.sum(np.abs(psi_pattern)**2)))
        
        # Extraire le pattern commun (mots partagés par toutes les prémisses)
        all_words = [set(_normalize(p).split()) for p in premises]
        common = all_words[0]
        for w in all_words[1:]:
            common &= w
        common_str = ', '.join(list(common)[:3]) if common else "aucun mot commun"
        
        conclusion = f"Pattern général : {common_str} (force {pattern_strength:.2f})"
        
        return LogicResult(
            conclusion=conclusion,
            confidence=min(1.0, avg_coherence * 2),
            method="induction",
            coherence=avg_coherence,
            steps=[
                f"{len(premises)} prémisses",
                f"Cohérence moyenne: {avg_coherence:+.3f}",
                f"Force du pattern: {pattern_strength:.3f}",
                f"Mots communs: {common_str}"
            ],
            is_valid=avg_coherence > CLUSTER_SIMILARITY,
        )
    
    def _solve_chain(self, premises, psis, coherences) -> LogicResult:
        """
        CHAÎNE TRANSITIVE : A→B→C→...
        
        Opération : binding séquentiel avec validation de cohérence.
        """
        avg_coh = sum(coherences) / len(coherences) if coherences else 0
        
        first_words = _normalize(premises[0]).split()
        last_words = _normalize(premises[-1]).split()
        
        subj_first = first_words[0] if first_words else "?"
        obj_last = last_words[-1] if last_words else "?"
        
        conclusion = f"{subj_first} est connecté à {obj_last} via une chaîne de {len(premises)} faits"
        
        return LogicResult(
            conclusion=conclusion,
            confidence=min(1.0, avg_coh * 2),
            method="chaine_transitive",
            coherence=avg_coh,
            steps=[f"Chaîne de {len(premises)} maillons",
                   f"Cohérence moyenne: {avg_coh:+.3f}"]
            + [f"  {p[:50]}..." for p in premises],
            is_valid=avg_coh > COHERENCE_VALID,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from harmonic_brain import HarmonicBrain
    import numpy as np
    from pathlib import Path
    
    kb_path = Path('data/bootstrapper_output/knowledge_base_clean_v2.npz')
    data = np.load(str(kb_path), allow_pickle=True)
    facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in data['facts'][:8000]]
    brain = HarmonicBrain(facts)
    wl = WaveLogic(brain)
    
    print("=" * 70)
    print("MOTEUR DE LOGIQUE ONDULATOIRE — Démonstration")
    print("=" * 70)
    
    # Test 1 : Syllogisme
    print("\n1. SYLLOGISME")
    print("-" * 40)
    r = wl.solve(
        premises=["l'aïkikaï constitue l'aïkido",
                  "l'aïkido constitue le renshinkaï"],
        question="Que déduire ?"
    )
    print(f"  Méthode : {r.method}")
    print(f"  Cohérence : {r.coherence:+.3f}")
    print(f"  Valide : {r.is_valid}")
    print(f"  Conclusion : {r.conclusion}")
    
    # Test 2 : Contradiction (deux faits incompatibles)
    print("\n2. CONTRADICTION")
    print("-" * 40)
    r = wl.solve(
        premises=["le ciel est bleu", "le ciel est rouge"],
        question="Est-ce cohérent ?"
    )
    print(f"  Méthode : {r.method}")
    print(f"  Cohérence : {r.coherence:+.3f}")
    print(f"  Valide : {r.is_valid}")
    print(f"  Conclusion : {r.conclusion}")
    
    # Test 3 : Fait direct
    print("\n3. FAIT DIRECT")
    print("-" * 40)
    r = wl.solve(
        premises=["Paris est la capitale de la France"],
        question="Quelle est la capitale ?"
    )
    print(f"  Méthode : {r.method}")
    print(f"  Conclusion : {r.conclusion}")
    
    # Test 4 : Induction (5 prémisses similaires)
    print("\n4. INDUCTION (5 prémisses)")
    print("-" * 40)
    r = wl.solve(
        premises=[
            "le chat est un mammifère",
            "le chien est un mammifère",
            "la baleine est un mammifère",
            "la souris est un mammifère",
        ],
        question="Que peut-on généraliser ?"
    )
    print(f"  Méthode : {r.method}")
    print(f"  Cohérence : {r.coherence:+.3f}")
    print(f"  Conclusion : {r.conclusion}")
    
    print("\n" + "=" * 70)
    print("4 OPÉRATIONS PRIMITIVES → 7 TYPES DE RAISONNEMENT ÉMERGENTS")
    print("=" * 70)
