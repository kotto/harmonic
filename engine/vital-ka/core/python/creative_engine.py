#!/usr/bin/env python3
"""
Creative Engine — Moteur de Créativité Ondulatoire
=====================================================
Utilise les 6 opérations créatives fondées sur la convolution ⊛
pour générer des concepts nouveaux, des analogies, et des découvertes.

PRINCIPE :
  La convolution ⊛ est l'opérateur de CRÉATION.
  ψ_nouveau = ψ_A ⊛ ψ_B  → combine deux concepts en un troisième.
  ψ_relation = ψ_o ⊗ ψ_s  → découvre le lien entre deux concepts.

OPÉRATIONS :
  1. ANALOGIE     : A:B :: C:?  → ψ_? = ψ_C ⊗ ψ_B ⊛ ψ_A
  2. DÉCOUVERTE   : S ⊛ ? ≈ O   → ψ_rel = ψ_O ⊗ ψ_S
  3. GÉNÉRATION   : A ⊛ B → C  → ψ_nouveau = ψ_A ⊛ ψ_B
  4. INTERPOLATION: A → B       → ψ_milieu = (ψ_A + ψ_B) / 2
  5. EXTRAPOLATION: A → futur   → ψ_futur = ψ_A ⊛ ψ_tendance
  6. INVERSION    : O → S,R     → ψ_sujet = ψ_O ⊗ ψ_rel

USAGE :
  from creative_engine import CreativeEngine
  ce = CreativeEngine(encoder)
  result = ce.analogy('paris', 'france', 'tokyo')
  print(result.best_match)  # 'japon'
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field

PHI = 1.618033988749895


@dataclass
class CreativeResult:
    """Résultat d'une opération créative."""
    operation: str           # 'analogy', 'discovery', 'generation', etc.
    query: str               # description de l'opération
    best_match: str          # meilleur concept trouvé
    confidence: float        # score de cohérence [0, 1]
    candidates: List[Tuple[str, float]] = field(default_factory=list)
    psi_result: Optional[np.ndarray] = None  # le ψ généré

    def __repr__(self):
        return (f"CreativeResult({self.operation}, "
                f"'{self.best_match}', conf={self.confidence:.3f})")


class CreativeEngine:
    """
    Moteur de créativité par opérations ondulatoires.
    """

    def __init__(self, encoder, knowledge_base=None):
        self.encoder = encoder
        self.dim = encoder.dim
        # Index inversé : mot → ψ (pour lookup rapide)
        self.vocab = set(encoder.word_vectors.keys())
        # Filtrer les stopwords et mots courts
        self._stopwords = {'est', 'sont', 'a', 'de', 'du', 'des', 'le', 'la', 'les',
                          'un', 'une', 'et', 'ou', 'donc', 'car', 'ni', 'que', 'qui',
                          'dans', 'sur', 'pour', 'par', 'avec', 'sans', 'pas', 'ne',
                          'the', 'is', 'are', 'of', 'in', 'on', 'at', 'to', 'for'}
        self.vocab_content = {w for w in self.vocab 
                             if len(w) >= 3 and w not in self._stopwords
                             and not w.startswith('__char_')}

    def _encode(self, word: str) -> Optional[np.ndarray]:
        """Récupère le ψ d'un mot, ou l'encode s'il est inconnu."""
        w = word.lower().strip()
        if w in self.encoder.word_vectors:
            return self.encoder.word_vectors[w].copy()
        # Encoder à la volée
        try:
            return self.encoder.encode_query(w)
        except Exception:
            return None

    def _nearest(self, psi: np.ndarray, k: int = 5,
                 exclude: set = None) -> List[Tuple[str, float]]:
        """Trouve les k mots les plus proches de ψ par cohérence."""
        results = []
        exclude = exclude or set()
        for word in self.vocab_content:
            if word in exclude:
                continue
            v = self.encoder.word_vectors.get(word)
            if v is None:
                continue
            coh = float(np.real(np.dot(psi, np.conj(v))))
            results.append((word, coh))
        results.sort(key=lambda x: -x[1])
        return results[:k]

    # ═══════════════════════════════════════════════════════════════
    # OPÉRATION 1 : ANALOGIE (A:B :: C:?)
    # ═══════════════════════════════════════════════════════════════

    def analogy(self, a: str, b: str, c: str, k: int = 5) -> CreativeResult:
        """
        A:B :: C:?
        
        ψ_? ≈ ψ_C ⊗ ψ_B ⊛ ψ_A
        On extrait la relation (ψ_B ⊗ ψ_A), puis on l'applique à ψ_C.
        
        Exemple: Paris:France :: Tokyo:? → Japon
        """
        psi_a = self._encode(a)
        psi_b = self._encode(b)
        psi_c = self._encode(c)

        if psi_a is None or psi_b is None or psi_c is None:
            return CreativeResult('analogy', f'{a}:{b}::{c}:?', '', 0.0)

        # Extraire la relation : ψ_rel = ψ_B ⊗ ψ_A (unbind)
        psi_rel = self._unbind(psi_b, psi_a)

        # Appliquer à C : ψ_? = ψ_C ⊛ ψ_rel
        psi_result = self._bind(psi_c, psi_rel)
        psi_result = self._normalize(psi_result)

        # Trouver le mot le plus proche
        candidates = self._nearest(psi_result, k=k, exclude={a, b, c})
        best = candidates[0] if candidates else ('?', 0.0)

        return CreativeResult(
            operation='analogy',
            query=f'{a}:{b}::{c}:?',
            best_match=best[0],
            confidence=(best[1] + 1) / 2,
            candidates=candidates,
            psi_result=psi_result,
        )

    # ═══════════════════════════════════════════════════════════════
    # OPÉRATION 2 : DÉCOUVERTE (S ⊛ ? ≈ O → trouver la relation)
    # ═══════════════════════════════════════════════════════════════

    def discover_relation(self, subject: str, object_: str,
                          k: int = 5) -> CreativeResult:
        """
        Étant donné un sujet et un objet, découvre la relation qui les lie.
        
        ψ_rel ≈ ψ_O ⊗ ψ_S
        """
        psi_s = self._encode(subject)
        psi_o = self._encode(object_)

        if psi_s is None or psi_o is None:
            return CreativeResult('discovery', f'{subject} → ? → {object_}', '', 0.0)

        psi_rel = self._unbind(psi_o, psi_s)
        psi_rel = self._normalize(psi_rel)

        # Chercher les relations connues les plus proches
        candidates = self._nearest(psi_rel, k=k, exclude={subject, object_})
        best = candidates[0] if candidates else ('?', 0.0)

        return CreativeResult(
            operation='discovery',
            query=f'{subject} → ? → {object_}',
            best_match=best[0],
            confidence=(best[1] + 1) / 2,
            candidates=candidates,
            psi_result=psi_rel,
        )

    # ═══════════════════════════════════════════════════════════════
    # OPÉRATION 3 : GÉNÉRATION (A ⊛ B → concept nouveau)
    # ═══════════════════════════════════════════════════════════════

    def generate(self, a: str, b: str, k: int = 5) -> CreativeResult:
        """
        Crée un nouveau concept par binding de deux existants.
        
        ψ_nouveau = ψ_A ⊛ ψ_B
        """
        psi_a = self._encode(a)
        psi_b = self._encode(b)

        if psi_a is None or psi_b is None:
            return CreativeResult('generation', f'{a} ⊛ {b} → ?', '', 0.0)

        psi_new = self._bind(psi_a, psi_b)
        psi_new = self._normalize(psi_new)

        candidates = self._nearest(psi_new, k=k, exclude={a, b})
        best = candidates[0] if candidates else ('?', 0.0)

        return CreativeResult(
            operation='generation',
            query=f'{a} ⊛ {b} → ?',
            best_match=best[0],
            confidence=(best[1] + 1) / 2,
            candidates=candidates,
            psi_result=psi_new,
        )

    # ═══════════════════════════════════════════════════════════════
    # OPÉRATION 4 : INTERPOLATION (A → milieu → B)
    # ═══════════════════════════════════════════════════════════════

    def interpolate(self, a: str, b: str, k: int = 5) -> CreativeResult:
        """
        Trouve le concept « entre » A et B.
        
        ψ_milieu = (ψ_A + ψ_B) / 2  (superposition)
        """
        psi_a = self._encode(a)
        psi_b = self._encode(b)

        if psi_a is None or psi_b is None:
            return CreativeResult('interpolation', f'{a} ↔ {b}', '', 0.0)

        psi_mid = self._normalize(psi_a + psi_b)

        candidates = self._nearest(psi_mid, k=k, exclude={a, b})
        best = candidates[0] if candidates else ('?', 0.0)

        return CreativeResult(
            operation='interpolation',
            query=f'{a} ↔ {b}',
            best_match=best[0],
            confidence=(best[1] + 1) / 2,
            candidates=candidates,
            psi_result=psi_mid,
        )

    # ═══════════════════════════════════════════════════════════════
    # OPÉRATION 5 : EXTRAPOLATION (A → tendance → futur)
    # ═══════════════════════════════════════════════════════════════

    def extrapolate(self, present: str, trend: str, k: int = 5) -> CreativeResult:
        """
        Projette un concept dans le futur selon une tendance.
        
        ψ_futur = ψ_present ⊛ ψ_tendance
        """
        return self.generate(present, trend)

    # ═══════════════════════════════════════════════════════════════
    # OPÉRATION 6 : INVERSION (O → S, R)
    # ═══════════════════════════════════════════════════════════════

    def invert(self, object_: str, relation: str, k: int = 5) -> CreativeResult:
        """
        Remonte de l'effet à la cause.
        
        ψ_sujet = ψ_O ⊗ ψ_rel
        """
        psi_o = self._encode(object_)
        psi_r = self._encode(relation)

        if psi_o is None or psi_r is None:
            return CreativeResult('inversion', f'? ⊛ {relation} ≈ {object_}', '', 0.0)

        psi_s = self._unbind(psi_o, psi_r)
        psi_s = self._normalize(psi_s)

        candidates = self._nearest(psi_s, k=k, exclude={object_, relation})
        best = candidates[0] if candidates else ('?', 0.0)

        return CreativeResult(
            operation='inversion',
            query=f'? ⊛ {relation} ≈ {object_}',
            best_match=best[0],
            confidence=(best[1] + 1) / 2,
            candidates=candidates,
            psi_result=psi_s,
        )

    # ═══════════════════════════════════════════════════════════════
    # OPÉRATIONS DE BASE (binding/unbinding)
    # ═══════════════════════════════════════════════════════════════

    def _bind(self, psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """ψ_a ⊛ ψ_b = IFFT(FFT(ψ_a) · FFT(ψ_b))"""
        return np.fft.ifft(np.fft.fft(psi_a) * np.fft.fft(psi_b))

    def _unbind(self, psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """ψ_a ⊗ ψ_b = IFFT(FFT(ψ_a) · conj(FFT(ψ_b)))"""
        return np.fft.ifft(np.fft.fft(psi_a) * np.conj(np.fft.fft(psi_b)))

    def _normalize(self, psi: np.ndarray) -> np.ndarray:
        norm = np.sqrt(np.sum(np.abs(psi) ** 2))
        if norm > 1e-15:
            return psi / norm
        return psi


# ═══════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════

def demo(encoder, kb):
    """Démonstration des 6 opérations créatives."""
    print("=" * 65)
    print("  CREATIVE ENGINE — Moteur de Créativité Ondulatoire")
    print("=" * 65)

    ce = CreativeEngine(encoder)

    # 1. ANALOGIE
    print("\n1. ANALOGIE (A:B :: C:?)")
    for a, b, c in [
        ('paris', 'france', 'tokyo'),
        ('lumiere', 'onde', 'son'),
        ('terre', 'gravite', 'lumiere'),
    ]:
        r = ce.analogy(a, b, c)
        print(f"  {a}:{b} :: {c}:?  →  {r.best_match} (conf={r.confidence:.2f})")
        if r.candidates:
            print(f"    autres: {[c[0] for c in r.candidates[1:4]]}")

    # 2. DÉCOUVERTE
    print("\n2. DÉCOUVERTE (Sujet → ? → Objet)")
    for s, o in [
        ('photosynthese', 'oxygene'),
        ('eau', 'H2O'),
        ('paris', 'france'),
    ]:
        r = ce.discover_relation(s, o)
        print(f"  {s} → ? → {o}  →  relation = {r.best_match} (conf={r.confidence:.2f})")

    # 3. GÉNÉRATION
    print("\n3. GÉNÉRATION (A ⊛ B → concept nouveau)")
    for a, b in [
        ('lumiere', 'energie'),
        ('terre', 'eau'),
        ('chaleur', 'mouvement'),
    ]:
        r = ce.generate(a, b)
        print(f"  {a} ⊛ {b}  →  {r.best_match} (conf={r.confidence:.2f})")
        if r.candidates:
            print(f"    autres: {[c[0] for c in r.candidates[1:4]]}")

    # 4. INTERPOLATION
    print("\n4. INTERPOLATION (A ↔ B)")
    for a, b in [
        ('particule', 'onde'),
        ('vivant', 'non-vivant'),
        ('lumiere', 'matiere'),
    ]:
        r = ce.interpolate(a, b)
        print(f"  {a} ↔ {b}  →  {r.best_match} (conf={r.confidence:.2f})")

    # 5. EXTRAPOLATION
    print("\n5. EXTRAPOLATION (Présent ⊛ Tendance → Futur)")
    for p, t in [
        ('energie', 'propre'),
        ('intelligence', 'artificielle'),
        ('matiere', 'noire'),
    ]:
        r = ce.extrapolate(p, t)
        print(f"  {p} ⊛ {t}  →  {r.best_match} (conf={r.confidence:.2f})")

    # 6. INVERSION
    print("\n6. INVERSION (? → cause → effet)")
    for o, rel in [
        ('oxygene', 'produit'),
        ('H2O', 'symbole'),
        ('japon', 'capitale'),
    ]:
        r = ce.invert(o, rel)
        print(f"  ? ⊛ {rel} ≈ {o}  →  sujet = {r.best_match} (conf={r.confidence:.2f})")

    print("\n" + "=" * 65)
    print("  6 opérations. Un seul opérateur : ⊛. Créativité infinie.")
    print("=" * 65)


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    from harmonic_brain import HarmonicBrain
    from harmonic_model import KNOWLEDGE_BASE

    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]
    brain = HarmonicBrain(facts[:500])

    # Fine-tune rapide pour activer la contrainte ⊛
    from wave_fine_tune import WaveFineTuner
    tuner = WaveFineTuner(brain.unconscious.encoder, lambda_reg=2.0)
    tuner.fine_tune(facts[:500], epochs=3, verbose=False)

    demo(brain.unconscious.encoder, facts[:500])
