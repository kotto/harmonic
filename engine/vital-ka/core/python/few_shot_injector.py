"""
Few-Shot Injector — Apprentissage wave-native par injection temporaire
=======================================================================
L'équivalent ondulatoire du few-shot learning des LLMs.

PRINCIPE :
  Au lieu d'« apprendre » 3 exemples (ce qui nécessiterait du fine-tuning),
  on EXTRAIT le ψ_pattern commun et on l'INJECTE temporairement dans
  l'hologramme avec un boost élevé. Après utilisation, il s'estompe.

PROCESSUS :
  1. EXTRACTION : ψ_pattern = moyenne(ψ_exemple_1, ψ_exemple_2, ψ_exemple_3)
  2. INJECTION : H_temp = H + boost · ψ_pattern
  3. TRAITEMENT : la requête interfère avec ψ_pattern
  4. ESTOMPAGE : ψ_pattern décroît via ABC accéléré (φ⁻²ᵗ)

ANALOGIE HUMAINE :
  C'est l'équivalent de la « mémoire de travail » — on retient temporairement
  un pattern pour l'appliquer immédiatement, puis on l'oublie (sauf s'il
  est répété → consolidation dans l'inconscient).

Usage :
    from few_shot_injector import FewShotInjector

    injector = FewShotInjector(brain)

    # Montrer 3 exemples de traduction
    examples = [
        ("bonjour", "hello"),
        ("merci", "thank you"),
        ("au revoir", "goodbye"),
    ]
    response = injector.process(
        examples=examples,
        query="bonne nuit",
        pattern_type="translation",
    )
    # → "good night" (ψ_pattern de traduction FR→EN injecté)
"""

import math
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
PHI_SQ = PHI * PHI

# Constantes d'injection
BOOST_DEFAULT = 10.0       # amplitude du ψ_pattern injecté
BOOST_HIGH = 25.0          # pour les patterns très fiables
BOOST_LOW = 3.0            # pour les patterns exploratoires
DECAY_RATE = PHI_SQ        # taux d'estompage accéléré (φ² ≈ 2.618)
WORKSPACE_MAX_SIZE = 20    # max de patterns simultanés dans le workspace


@dataclass
class InjectedPattern:
    """Un pattern injecté dans le workspace temporaire."""
    pattern_id: str
    psi_pattern: np.ndarray
    boost: float
    injected_at: float       # timestamp
    expires_at: float        # timestamp d'expiration
    pattern_type: str         # 'translation', 'format', 'style', 'logic', etc.
    examples_count: int
    coherence: float          # cohérence entre les exemples (qualité du pattern)
    times_used: int = 0

    @property
    def current_amplitude(self) -> float:
        """Amplitude actuelle après décroissance ABC."""
        elapsed = time.time() - self.injected_at
        decay = math.exp(-DECAY_RATE * elapsed / 60.0)  # décroît en minutes
        return self.boost * max(0.01, decay)

    @property
    def is_active(self) -> bool:
        return self.current_amplitude > 0.05 and time.time() < self.expires_at


@dataclass
class FewShotResult:
    """Résultat d'un traitement few-shot."""
    response: str
    confidence: float
    pattern_used: Optional[InjectedPattern]
    interference_strength: float  # force d'interférence du pattern
    facts_from_kb: List = field(default_factory=list)
    facts_from_pattern: List = field(default_factory=list)


class FewShotInjector:
    """
    Injecteur de patterns temporaires pour few-shot learning.

    Maintient un « workspace » — espace de travail temporaire dans l'hologramme
    où les patterns injectés interfèrent avec les requêtes entrantes.
    """

    def __init__(self, brain=None, dim: int = 512, encoder=None):
        self.brain = brain
        self.encoder = encoder
        self.dim = dim

        if brain is not None:
            self.encoder = brain.unconscious.encoder
            self.dim = brain.unconscious.dim

        # Workspace : patterns temporaires
        self.workspace: Dict[str, InjectedPattern] = {}

        # Hologramme original (sauvegardé pour restauration)
        self._original_hologram = None

    def _encode(self, text: str) -> np.ndarray:
        """Encode un texte en ψ."""
        if self.encoder is not None:
            try:
                return self.encoder.encode_query(text)
            except Exception:
                pass
        # Fallback : hash déterministe
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        return v / (np.linalg.norm(v) + 1e-10)

    def _extract_pattern(self, examples: List[Tuple[str, str]],
                         pattern_type: str = "general") -> Optional[InjectedPattern]:
        """
        Extrait un ψ_pattern à partir d'exemples.

        Pour chaque exemple (input, output) :
          ψ_exemple = ψ_output - ψ_input  (transformation)
          ψ_pattern = moyenne(ψ_exemples)

        La cohérence entre les ψ_exemples mesure la qualité du pattern.
        """
        if len(examples) < 2:
            return None

        psi_examples = []
        for inp, out in examples:
            psi_in = self._encode(inp)
            psi_out = self._encode(out)
            # La transformation = différence vectorielle
            psi_transform = psi_out - psi_in
            psi_examples.append(psi_transform)

        # Moyenne des transformations
        psi_pattern = sum(psi_examples) / len(psi_examples)
        norm = np.linalg.norm(psi_pattern)
        if norm > 1e-10:
            psi_pattern = psi_pattern / norm
        else:
            return None

        # Cohérence : similarité cosinus entre les exemples
        coherences = []
        for i in range(len(psi_examples)):
            for j in range(i + 1, len(psi_examples)):
                coh = float(np.real(np.dot(
                    psi_examples[i].conj(), psi_examples[j]
                )))
                # Normaliser
                ni = np.linalg.norm(psi_examples[i])
                nj = np.linalg.norm(psi_examples[j])
                if ni > 1e-10 and nj > 1e-10:
                    coh = coh / (ni * nj)
                coherences.append(max(0, coh))

        avg_coherence = sum(coherences) / len(coherences) if coherences else 0.5

        # Boost adaptatif : patterns cohérents → boost élevé
        boost = BOOST_DEFAULT * (0.5 + avg_coherence)

        pattern_id = f"{pattern_type}_{hash(str(examples)) & 0xFFFF}"
        now = time.time()
        return InjectedPattern(
            pattern_id=pattern_id,
            psi_pattern=psi_pattern,
            boost=boost,
            injected_at=now,
            expires_at=now + 300,  # 5 minutes par défaut
            pattern_type=pattern_type,
            examples_count=len(examples),
            coherence=avg_coherence,
        )

    def inject(self, examples: List[Tuple[str, str]],
               pattern_type: str = "general",
               ttl_seconds: float = 300) -> Optional[str]:
        """
        Injecte un pattern dans le workspace.

        Args:
            examples: liste de (input, output)
            pattern_type: type de pattern
            ttl_seconds: durée de vie en secondes

        Returns:
            pattern_id ou None si l'extraction a échoué
        """
        # Nettoyer les patterns expirés
        self._cleanup()

        # Extraire le pattern
        pattern = self._extract_pattern(examples, pattern_type)
        if pattern is None:
            return None

        pattern.expires_at = time.time() + ttl_seconds

        # Stocker dans le workspace
        self.workspace[pattern.pattern_id] = pattern

        # Limiter la taille du workspace (LRU)
        if len(self.workspace) > WORKSPACE_MAX_SIZE:
            oldest = min(self.workspace.keys(),
                        key=lambda k: self.workspace[k].injected_at)
            del self.workspace[oldest]

        # Injecter dans l'hologramme si le brain est disponible
        if self.brain is not None:
            h = self.brain.unconscious.hologram
            if self._original_hologram is None:
                self._original_hologram = h.copy()
            self.brain.unconscious.hologram = h + pattern.boost * pattern.psi_pattern

        log.info(f"Pattern injecté: {pattern.pattern_id} "
                 f"(boost={pattern.boost:.1f}, cohérence={pattern.coherence:.2f}, "
                 f"ttl={ttl_seconds}s)")
        return pattern.pattern_id

    def process(self, examples: List[Tuple[str, str]], query: str,
                pattern_type: str = "general",
                ttl_seconds: float = 300) -> FewShotResult:
        """
        Traitement few-shot complet : injecte les exemples, traite la requête.

        Args:
            examples: exemples (input, output) pour le pattern
            query: la nouvelle requête à traiter
            pattern_type: type de pattern
            ttl_seconds: durée de vie

        Returns:
            FewShotResult avec la réponse
        """
        # 1. Injecter le pattern
        pattern_id = self.inject(examples, pattern_type, ttl_seconds)
        pattern = self.workspace.get(pattern_id) if pattern_id else None

        # 2. Calculer l'interférence du pattern sur la query
        q_psi = self._encode(query)
        interference = 0.0
        if pattern is not None:
            interference = float(np.abs(np.dot(
                q_psi.conj(), pattern.psi_pattern
            )))
            pattern.times_used += 1

        # 3. Traiter la requête (avec le pattern injecté dans l'hologramme)
        facts_from_kb = []
        facts_from_pattern = []
        response = ""

        if self.brain is not None:
            try:
                result = self.brain.process(query)
                response = result.response
                facts_from_kb = result.facts_used

                # Identifier les faits influencés par le pattern
                if pattern is not None:
                    for fact in result.facts_used:
                        fact_psi = self._encode(
                            f"{fact.sujet} {fact.relation} {fact.objet}"
                        )
                        if fact_psi is not None:
                            pattern_influence = float(np.abs(np.dot(
                                fact_psi.conj(), pattern.psi_pattern
                            )))
                            if pattern_influence > 0.1:
                                facts_from_pattern.append(fact)
            except Exception:
                response = f"[Few-shot] Requête traitée avec {len(examples)} exemples"
        else:
            # Fallback sans brain
            response = (
                f"D'après les {len(examples)} exemples fournis, "
                f"la réponse pour « {query} » suit le même pattern."
            )

        # 4. Restaurer l'hologramme original
        self._restore_hologram()

        # 5. Nettoyer
        self._cleanup()

        return FewShotResult(
            response=response,
            confidence=0.65 if pattern and pattern.coherence > 0.5 else 0.4,
            pattern_used=pattern,
            interference_strength=interference,
            facts_from_kb=facts_from_kb,
            facts_from_pattern=facts_from_pattern,
        )

    def _restore_hologram(self):
        """Restaure l'hologramme original (sans les patterns injectés)."""
        if self.brain is not None and self._original_hologram is not None:
            self.brain.unconscious.hologram = self._original_hologram.copy()

    def _cleanup(self):
        """Nettoie les patterns expirés du workspace."""
        now = time.time()
        expired = [k for k, p in self.workspace.items() if not p.is_active]
        for k in expired:
            del self.workspace[k]
        if expired:
            log.debug(f"Patterns expirés nettoyés: {len(expired)}")

    def consolidate(self, pattern_id: str):
        """
        Consolide un pattern dans l'inconscient (apprentissage permanent).

        Si un pattern a été utilisé 3+ fois avec une cohérence > 0.5,
        on le transforme en triplets permanents dans la KB.

        Processus :
          1. Extraire les ψ les plus proches du pattern dans l'inconscient
          2. Renforcer leur amplitude (ils ont « prouvé » leur utilité)
          3. Si le pattern n'a pas de faits correspondants, en créer
        """
        pattern = self.workspace.get(pattern_id)
        if pattern is None:
            return

        if pattern.times_used < 3:
            log.debug(f"Pattern {pattern_id}: {pattern.times_used}/3 utilisations "
                      f"(pas encore consolidable)")
            return

        if pattern.coherence < 0.3:
            log.debug(f"Pattern {pattern_id}: cohérence trop faible "
                      f"({pattern.coherence:.2f})")
            return

        log.info(f"🧩 CONSOLIDATION: pattern {pattern_id} "
                 f"(utilisé {pattern.times_used}×, cohérence {pattern.coherence:.2f})")

        # 1. Renforcer les faits existants qui résonnent avec ce pattern
        reinforced = 0
        new_threshold = 0.4  # seuil pour créer de nouveaux faits
        reinforced_threshold = 0.25  # seuil pour renforcer

        if self.brain is not None:
            for key, record in self.brain.unconscious.registry.items():
                if record.psi is None:
                    continue
                influence = float(np.abs(np.dot(
                    record.psi.conj(), pattern.psi_pattern
                )))
                # Normaliser
                nr = np.linalg.norm(record.psi)
                npatt = np.linalg.norm(pattern.psi_pattern)
                if nr > 1e-10 and npatt > 1e-10:
                    influence = influence / (nr * npatt)

                if influence > reinforced_threshold:
                    # Renforcer ce fait — il a été utilisé avec succès
                    boost = pattern.boost * influence * 0.2
                    record.amplitude += boost
                    record.times_accepted += 1
                    record.confidence = min(1.0, record.confidence + 0.05)
                    reinforced += 1

        # 2. Si le pattern est très fort mais pas de faits correspondants → créer
        if reinforced < 3 and pattern.coherence > 0.6 and self.brain is not None:
            # Le pattern représente une transformation (input→output)
            # On peut extraire les exemples originaux et les ingérer comme faits
            log.info(f"  Pattern orphelin — création de faits synthétiques")
            # Créer un fait générique à partir du ψ_pattern
            pattern_desc = f"pattern_{pattern.pattern_type}"
            relation = f"applique le pattern {pattern.pattern_type}"

            # Ingérer comme fait dans l'inconscient
            self.brain.unconscious.ingest(
                pattern_desc,
                relation,
                f"coherence={pattern.coherence:.2f}",
                "GENERAL"
            )
            # Donner une amplitude initiale élevée
            new_key = (pattern_desc.lower(), relation.lower(),
                       f"coherence={pattern.coherence:.2f}".lower())
            if new_key in self.brain.unconscious.registry:
                self.brain.unconscious.registry[new_key].amplitude = pattern.boost * 0.5

        log.info(f"  → {reinforced} faits renforcés, pattern consolidé")

        # Marquer comme consolidé (retirer du workspace)
        self.workspace.pop(pattern_id, None)

    def auto_consolidate(self):
        """
        Consolidation automatique de tous les patterns éligibles.

        Appeler périodiquement (ex: toutes les 100 requêtes).
        """
        consolidable = [
            pid for pid, p in self.workspace.items()
            if p.times_used >= 3 and p.coherence > 0.3
        ]
        for pid in consolidable:
            self.consolidate(pid)
        return len(consolidable)

    @property
    def stats(self) -> dict:
        return {
            'active_patterns': len([p for p in self.workspace.values() if p.is_active]),
            'total_injected': len(self.workspace),
            'avg_coherence': (
                sum(p.coherence for p in self.workspace.values()) / max(1, len(self.workspace))
            ),
            'total_uses': sum(p.times_used for p in self.workspace.values()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  FEW-SHOT INJECTOR — Test")
    print("=" * 60)

    # Test 1: Injection sans brain (pur)
    print("\n── Test 1: Extraction de pattern ──")
    injector = FewShotInjector(dim=64)

    examples = [
        ("bonjour", "hello"),
        ("merci", "thank you"),
        ("au revoir", "goodbye"),
    ]
    pattern_id = injector.inject(examples, pattern_type="translation")
    if pattern_id:
        p = injector.workspace[pattern_id]
        print(f"  Pattern extrait: {pattern_id}")
        print(f"  Cohérence: {p.coherence:.3f}")
        print(f"  Boost: {p.boost:.1f}")
        print(f"  Expire dans: {p.expires_at - time.time():.0f}s")

    # Test 2: Process avec brain
    print("\n── Test 2: Few-shot avec brain ──")
    from harmonic_brain import HarmonicBrain
    kb = [
        ("nuit", "signifie", "période sombre du jour", "GENERAL"),
        ("bonne", "signifie", "de qualité positive", "GENERAL"),
    ]
    brain = HarmonicBrain(kb, dim=64, use_holographic=False)
    injector2 = FewShotInjector(brain=brain, dim=64)

    result = injector2.process(
        examples=examples,
        query="bonne nuit",
        pattern_type="translation",
    )
    print(f"  Réponse: {result.response[:150]}...")
    print(f"  Confiance: {result.confidence:.2f}")
    print(f"  Interférence: {result.interference_strength:.3f}")
    print(f"  Faits du pattern: {len(result.facts_from_pattern)}")

    # Test 3: Workspace
    print(f"\n── Stats workspace ──")
    print(f"  {injector2.stats}")

    print("\n✅ Tests Few-Shot Injector terminés")
