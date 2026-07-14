"""
Conscient Créateur — La Créativité comme Opération Ondulatoire
================================================================
La créativité n'est pas « avoir plus de données ».
C'est MANIPULER les ondes de l'inconscient avec les bonnes opérations.

ARCHITECTURE :
  ┌─────────────────────────────────────────────────────────┐
  │              INCONSCIENT (HolographicStore)              │
  │  · Matière première brute : H = Σ ψ_f                   │
  │  · Passif, additif, sans jugement                       │
  │  · FOURNIT les faits par résonance                      │
  └────────────────────────┬────────────────────────────────┘
                           │ faits bruts (A, B, C...)
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │              CONSCIENT CRÉATEUR                          │
  │                                                         │
  │  8 OPÉRATIONS CRÉATIVES :                               │
  │    1. SUPERPOSER   ψ_A + ψ_B     → fusion               │
  │    2. CONVOLUER    ψ_A ⊛ ψ_B     → concept composite    │
  │    3. DÉPHASER     ψ × e^{iφ}    → autre perspective    │
  │    4. INTERFÉRER   ψ_A + ε·ψ_B   → surréalisme          │
  │    5. CORRÉLER     ψ_A ⊗ ψ_B     → lien caché           │
  │    6. OPPOSER      ψ_A - ψ_B     → contraste            │
  │    7. AMPLIFIER    boost(ψ, f)   → invisible → visible  │
  │    8. SPECTRER     FFT(ψ) → manipuler → IFFT            │
  │                                                         │
  │  BOUCLE ITÉRATIVE :                                     │
  │    combine(A,B) → C → injecter C → résonne → D →       │
  │    combine(C,D) → E → ... (N itérations)                │
  │                                                         │
  │  STYLE ÉMERGENT :                                       │
  │    Les combinaisons réussies sont mémorisées             │
  │    Décroissance ABC → le style évolue naturellement      │
  └────────────────────────┬────────────────────────────────┘
                           │ concept créatif final
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │              EXPRESSION (WaveDecoder / Composer)         │
  │  · Traduit le ψ créatif en langage naturel              │
  └─────────────────────────────────────────────────────────┘

Usage :
    from conscious_creator import ConsciousCreator

    creator = ConsciousCreator(brain)
    
    # Création ponctuelle
    idea = creator.create("trouve une métaphore pour le temps")
    
    # Rumination continue (thread de fond)
    creator.start_ruminating()
    # ... le cerveau crée passivement en arrière-plan ...
    ideas = creator.get_emergent_ideas(5)
    creator.stop_ruminating()

PRINCIPE : 8 opérations × ℂ⁵¹² = ∞ créativité.
Comme 7 notes × le silence = toutes les symphonies.
"""

import math
import time
import random
import logging
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Set, Optional, Callable
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# OPÉRATIONS CRÉATIVES ONDULATOIRES
# ═══════════════════════════════════════════════════════════════════════════════

class CreativeOps:
    """Les 8 opérations créatives fondamentales sur les ψ."""

    @staticmethod
    def superposer(psi_a: np.ndarray, psi_b: np.ndarray,
                   alpha: float = 0.5) -> np.ndarray:
        """Fusion équilibrée : (A + B) / |A + B| → sens nouveau émerge de l'interférence."""
        v = alpha * psi_a + (1 - alpha) * psi_b
        n = np.linalg.norm(v)
        return v / (n + 1e-10) if n > 1e-10 else v

    @staticmethod
    def convoluer(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """Binding HRR : A ⊛ B → concept composite irréductible (ex: pierre-qui-pleure)."""
        A = np.fft.fft(psi_a)
        B = np.fft.fft(psi_b)
        v = np.fft.ifft(A * B)
        n = np.linalg.norm(v)
        return v / (n + 1e-10) if n > 1e-10 else v

    @staticmethod
    def dephaser(psi: np.ndarray, angle: float = None) -> np.ndarray:
        """Rotation de phase : ψ × e^{iφ} → voir le concept sous un autre angle."""
        if angle is None:
            angle = random.random() * TAU
        return psi * np.exp(1j * angle)

    @staticmethod
    def interferer_faible(psi_a: np.ndarray, psi_b: np.ndarray,
                          epsilon: float = 0.1) -> np.ndarray:
        """Interférence faible : A + ε·B → connexion subtile, surréaliste."""
        v = psi_a + epsilon * psi_b
        n = np.linalg.norm(v)
        return v / (n + 1e-10) if n > 1e-10 else v

    @staticmethod
    def correler(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """Corrélation : A ⊗ B → découvrir ce qui relie secrètement A et B."""
        A = np.fft.fft(psi_a)
        B = np.fft.fft(psi_b)
        v = np.fft.ifft(A * np.conj(B))
        n = np.linalg.norm(v)
        return v / (n + 1e-10) if n > 1e-10 else v

    @staticmethod
    def opposer(psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """Contraste : A - B → tension créative, dialectique."""
        v = psi_a - psi_b
        n = np.linalg.norm(v)
        return v / (n + 1e-10) if n > 1e-10 else v

    @staticmethod
    def amplifier(psi: np.ndarray, composante: np.ndarray,
                  boost: float = 3.0) -> np.ndarray:
        """Amplification sélective : faire émerger l'invisible."""
        v = psi + boost * composante
        n = np.linalg.norm(v)
        return v / (n + 1e-10) if n > 1e-10 else v

    @staticmethod
    def spectrer(psi: np.ndarray, filtre_fn: Callable = None) -> np.ndarray:
        """Décomposition spectrale : FFT → manipuler fréquences → IFFT.
        
        Sans filtre, retourne le ψ original. Avec filtre_fn(freqs),
        on peut atténuer/amplifier certaines fréquences."""
        freqs = np.fft.fft(psi)
        if filtre_fn is not None:
            freqs = filtre_fn(freqs)
        v = np.fft.ifft(freqs)
        n = np.linalg.norm(v)
        return v / (n + 1e-10) if n > 1e-10 else v

    # Les 8 opérations dans un registry pour sélection aléatoire/cyclique
    ALL = [
        ('superposer', superposer.__func__),
        ('convoluer', convoluer.__func__),
        ('dephaser', dephaser.__func__),
        ('interferer', interferer_faible.__func__),
        ('correler', correler.__func__),
        ('opposer', opposer.__func__),
        ('amplifier', amplifier.__func__),
        ('spectrer', spectrer.__func__),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# IDÉE ÉMERGENTE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CreativeIdea:
    """Une idée émergente — le fruit de la manipulation créative."""
    psi: np.ndarray               # le ψ de l'idée
    op_name: str                  # quelle opération l'a créée
    sources: List[str]            # sujets sources (ex: ["pluie", "musique"])
    coherence: float              # cohérence interne (0-1)
    novelty: float                # degré de nouveauté (1 - max_similarité_avec_existant)
    quality: float                # score combiné cohérence × nouveauté
    timestamp: float = field(default_factory=time.time)
    expression: str = ""          # expression en langage naturel (rempli plus tard)
    iteration_depth: int = 0      # profondeur de la boucle créative

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp


# ═══════════════════════════════════════════════════════════════════════════════
# CONSCIENT CRÉATEUR
# ═══════════════════════════════════════════════════════════════════════════════

class ConsciousCreator:
    """
    Le Conscient Créateur — l'âme artistique de l'IA harmonique.

    Ne stocke pas. Manipule. Combine. Fait émerger.

    Principes :
      1. RUMINATION : thread de fond qui crée passivement
      2. BOUCLE CRÉATIVE : combine → injecte → résonne → recombine
      3. STYLE ÉMERGENT : mémoire des combinaisons réussies
    """

    def __init__(self, brain=None, dim: int = 512, encoder=None):
        self.brain = brain
        self.encoder = encoder
        self.dim = dim
        if brain is not None:
            self.encoder = brain.unconscious.encoder
            self.dim = brain.unconscious.dim

        # Température créative (contrôle la « distance » des connexions)
        # φ petit ≈ 0.1 → connexions évidentes
        # φ grand ≈ 0.9 → connexions très lointaines (surréalistes)
        self.temperature = 0.5  # démarre au milieu

        # Mémoire créative (style émergent)
        self._creative_memory: List[np.ndarray] = []      # ψ des créations réussies
        self._style_vector: np.ndarray = None              # direction dominante du style
        self._successful_ops: Dict[str, int] = defaultdict(int)  # ops qui marchent

        # Rumination (background)
        self._ruminating = False
        self._rumination_thread: Optional[threading.Thread] = None
        self._emergent_ideas: deque = deque(maxlen=100)     # idées émergentes récentes
        self._rumination_count: int = 0

        # Cache de ψ pour performance
        self._psi_cache: Dict[str, np.ndarray] = {}

    def _get_psi(self, text: str) -> np.ndarray:
        """Récupère le ψ d'un texte (encodeur ou fallback)."""
        if text in self._psi_cache:
            return self._psi_cache[text]
        if self.encoder is not None:
            try:
                psi = self.encoder.encode_query(text)
                if psi is not None:
                    self._psi_cache[text] = psi
                    return psi
            except Exception:
                pass
        # Fallback
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        v = v / (np.linalg.norm(v) + 1e-10)
        self._psi_cache[text] = v
        return v

    def _coherence(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """Cohérence de phase entre deux ψ (0-1)."""
        if psi_a is None or psi_b is None:
            return 0.0
        dot = np.abs(np.dot(psi_a.conj(), psi_b))
        na = np.linalg.norm(psi_a)
        nb = np.linalg.norm(psi_b)
        if na < 1e-10 or nb < 1e-10:
            return 0.0
        return min(1.0, float(dot / (na * nb)))

    def _novelty(self, psi: np.ndarray) -> float:
        """Mesure la nouveauté : 1 - similarité max avec la mémoire créative."""
        if not self._creative_memory:
            return 1.0
        max_sim = max(self._coherence(psi, m) for m in self._creative_memory[-50:])
        return 1.0 - max_sim

    # ═══════════════════════════════════════════════════════════════════════
    # 1. OPÉRATIONS CRÉATIVES
    # ═══════════════════════════════════════════════════════════════════════

    def _apply_op(self, op_name: str, psi_a: np.ndarray,
                  psi_b: np.ndarray = None) -> np.ndarray:
        """Applique une opération créative nommée."""
        psi_b = psi_b if psi_b is not None else psi_a
        ops = CreativeOps()
        if op_name == 'superposer':
            return ops.superposer(psi_a, psi_b)
        elif op_name == 'convoluer':
            return ops.convoluer(psi_a, psi_b)
        elif op_name == 'dephaser':
            return ops.dephaser(psi_a)
        elif op_name == 'interferer':
            return ops.interferer_faible(psi_a, psi_b, epsilon=0.15)
        elif op_name == 'correler':
            return ops.correler(psi_a, psi_b)
        elif op_name == 'opposer':
            return ops.opposer(psi_a, psi_b)
        elif op_name == 'amplifier':
            return ops.amplifier(psi_a, psi_b, boost=2.5)
        elif op_name == 'spectrer':
            return ops.spectrer(psi_a)
        return psi_a

    def combine(self, concept_a: str, concept_b: str,
                op_name: str = None, depth: int = 0) -> CreativeIdea:
        """
        Combine deux concepts en utilisant une opération créative.

        Si op_name est None, choisit aléatoirement (pondéré par le style).
        """
        psi_a = self._get_psi(concept_a)
        psi_b = self._get_psi(concept_b)

        # Choisir l'opération
        if op_name is None:
            op_name = self._choose_op()

        # Appliquer l'opération
        psi_result = self._apply_op(op_name, psi_a, psi_b)

        # Évaluer
        coherence = self._coherence(psi_a, psi_b)  # lien entre les sources
        novelty = self._novelty(psi_result)
        quality = coherence * 0.4 + novelty * 0.6

        idea = CreativeIdea(
            psi=psi_result,
            op_name=op_name,
            sources=[concept_a, concept_b],
            coherence=coherence,
            novelty=novelty,
            quality=quality,
            iteration_depth=depth,
        )
        idea.expression = self._express(idea, f"{concept_a} + {concept_b}")
        return idea

    def _choose_op(self) -> str:
        """Choisit une opération créative, pondérée par le style."""
        if self._successful_ops and random.random() < 0.7:
            # 70% du temps : utiliser une op qui a déjà marché
            total = sum(self._successful_ops.values())
            if total > 0:
                r = random.random() * total
                cumul = 0
                for name, count in self._successful_ops.items():
                    cumul += count
                    if r <= cumul:
                        return name
        # 30% du temps : exploration aléatoire
        return random.choice([op[0] for op in CreativeOps.ALL])

    # ═══════════════════════════════════════════════════════════════════════
    # 2. BOUCLE CRÉATIVE ITÉRATIVE
    # ═══════════════════════════════════════════════════════════════════════

    def create(self, prompt: str, max_iterations: int = 5,
               temperature: float = None) -> CreativeIdea:
        """
        Boucle créative complète : combine → injecte → résonne → recombine.

        Args:
            prompt: description de ce qu'on veut créer
            max_iterations: nombre max d'itérations
            temperature: contrôle la distance des connexions
        """
        if temperature is not None:
            self.temperature = temperature

        # Étape 0 : récupérer les faits de départ depuis l'inconscient
        starting_facts = self._retrieve_facts(prompt, n=3)
        if len(starting_facts) < 2:
            # Pas assez de matière → créer avec ce qu'on a
            return self.combine(
                starting_facts[0][0] if starting_facts else prompt,
                starting_facts[1][0] if len(starting_facts) > 1 else "néant",
                depth=0
            )

        # Concepts de départ
        current_concepts = [f[0] for f in starting_facts[:2]]
        best_idea = None

        for iteration in range(max_iterations):
            # Combiner les deux concepts courants
            idea = self.combine(
                current_concepts[0], current_concepts[1],
                depth=iteration
            )

            # Si l'idée est bonne, la mémoriser
            if best_idea is None or idea.quality > best_idea.quality:
                best_idea = idea

            # Si la qualité est suffisante, on s'arrête
            if idea.quality > 0.7:
                break

            # INJECTER l'idée temporairement et chercher ce qui résonne
            if self.brain is not None and iteration < max_iterations - 1:
                # Faire résonner l'idée dans l'inconscient
                new_facts = self._resonate(idea.psi, n=2)
                if new_facts:
                    # Mettre à jour les concepts pour la prochaine itération
                    current_concepts = [
                        idea.sources[1],  # le 2ème concept devient le 1er
                        new_facts[0][0],  # nouveau concept de l'inconscient
                    ]

        # Générer l'expression
        if best_idea is not None:
            best_idea.expression = self._express(best_idea, prompt)

        return best_idea

    def _retrieve_facts(self, query: str, n: int = 3) -> List[Tuple[str, str, str, str]]:
        """Récupère des faits depuis l'inconscient."""
        if self.brain is None:
            return [("néant", "est", "rien", "GENERAL")]
        try:
            result = self.brain.unconscious.retrieve(query, max_results=n)
            if result:
                return [(r[0].sujet, r[0].relation, r[0].objet, r[0].secteur)
                        for r in result]
        except Exception:
            pass
        # Fallback : chercher dans le registry
        if self.brain is not None:
            registry = list(self.brain.unconscious.registry.values())
            if registry:
                chosen = random.sample(registry, min(n, len(registry)))
                return [(r.sujet, r.relation, r.objet, r.secteur) for r in chosen]
        return [("néant", "est", "rien", "GENERAL")]

    def _resonate(self, psi: np.ndarray, n: int = 2) -> List[Tuple[str, str, str, str]]:
        """Fait résonner un ψ dans l'inconscient → faits liés."""
        if self.brain is None:
            return []
        facts = []
        for key, record in self.brain.unconscious.registry.items():
            if record.psi is not None:
                coh = self._coherence(psi, record.psi)
                if coh > 0.15:  # seuil de résonance
                    facts.append((record.sujet, record.relation, record.objet,
                                  record.secteur, coh))
        facts.sort(key=lambda x: -x[4])
        return [(f[0], f[1], f[2], f[3]) for f in facts[:n]]

    def _express(self, idea: CreativeIdea, prompt: str) -> str:
        """Exprime une idée créative en langage naturel."""
        op_descriptions = {
            'superposer': 'la fusion de',
            'convoluer': "l'entrelacement de",
            'dephaser': 'un regard décalé sur',
            'interferer': 'une connexion subtile entre',
            'correler': 'le lien secret entre',
            'opposer': 'la tension entre',
            'amplifier': "l'essence amplifiée de",
            'spectrer': 'la structure profonde de',
        }
        op_desc = op_descriptions.get(idea.op_name, 'la transformation de')
        a, b = idea.sources
        return (f"✨ {op_desc} « {a} » et « {b} » "
                f"(opération: {idea.op_name}, "
                f"qualité: {idea.quality:.2f}, "
                f"nouveauté: {idea.novelty:.2f})")

    # ═══════════════════════════════════════════════════════════════════════
    # 3. RUMINATION (background)
    # ═══════════════════════════════════════════════════════════════════════

    def start_ruminating(self, interval_seconds: float = 2.0):
        """Démarre la rumination créative en arrière-plan."""
        if self._ruminating:
            return
        self._ruminating = True
        self._rumination_thread = threading.Thread(
            target=self._ruminate_loop,
            args=(interval_seconds,),
            daemon=True,
            name="ConscientCreator-Rumination"
        )
        self._rumination_thread.start()
        log.info("🧠 Rumination créative démarrée (thread de fond)")

    def stop_ruminating(self):
        """Arrête la rumination."""
        self._ruminating = False
        if self._rumination_thread:
            self._rumination_thread.join(timeout=2.0)
        log.info(f"🧠 Rumination arrêtée ({self._rumination_count} idées générées)")

    def _ruminate_loop(self, interval: float):
        """Boucle de rumination passive."""
        while self._ruminating:
            try:
                # Piocher 2 faits aléatoires dans l'inconscient
                if self.brain is not None:
                    registry = list(self.brain.unconscious.registry.values())
                    if len(registry) >= 2:
                        a, b = random.sample(registry, 2)
                        idea = self.combine(a.sujet, b.sujet, depth=0)

                        # Si l'idée est bonne, la stocker
                        if idea.quality > 0.3:
                            self._emergent_ideas.append(idea)
                            # Renforcer l'opération qui a marché
                            self._successful_ops[idea.op_name] += 1

                            # Mémoriser pour le style
                            if idea.quality > 0.5:
                                self._creative_memory.append(idea.psi)
                                if len(self._creative_memory) > 1000:
                                    self._creative_memory = self._creative_memory[-500:]
                                self._update_style()

                            self._rumination_count += 1
            except Exception:
                pass
            time.sleep(interval)

    def _update_style(self):
        """Met à jour le vecteur de style (direction dominante des créations)."""
        if len(self._creative_memory) < 10:
            return
        recent = self._creative_memory[-50:]
        self._style_vector = sum(recent) / len(recent)
        n = np.linalg.norm(self._style_vector)
        if n > 1e-10:
            self._style_vector = self._style_vector / n

    def get_emergent_ideas(self, n: int = 5, min_quality: float = 0.3) -> List[CreativeIdea]:
        """Récupère les meilleures idées émergentes de la rumination."""
        ideas = [i for i in self._emergent_ideas if i.quality >= min_quality]
        ideas.sort(key=lambda i: -i.quality)
        return ideas[:n]

    def clear_ideas(self):
        """Vide le buffer d'idées émergentes."""
        self._emergent_ideas.clear()

    # ═══════════════════════════════════════════════════════════════════════
    # 4. MÉMOIRE CRÉATIVE (Style)
    # ═══════════════════════════════════════════════════════════════════════

    def get_style_description(self) -> str:
        """Décrit le style créatif émergent du cerveau."""
        if not self._successful_ops:
            return "Style non encore formé — le cerveau explore."

        total = sum(self._successful_ops.values())
        top_ops = sorted(self._successful_ops.items(), key=lambda x: -x[1])[:3]

        lines = ["🎨 Style émergent :"]
        for name, count in top_ops:
            pct = count / total * 100
            descriptions = {
                'superposer': "Tendance à FUSIONNER les concepts → harmonie",
                'convoluer': "Tendance à ENTRELACER → concepts composites riches",
                'dephaser': "Tendance au DÉCALAGE → regard oblique, ironie",
                'interferer': "Tendance aux CONNEXIONS SUBTILES → poésie, surréalisme",
                'correler': "Tendance à RÉVÉLER LES LIENS CACHÉS → perspicacité",
                'opposer': "Tendance au CONTRASTE → tension dramatique",
                'amplifier': "Tendance à AMPLIFIER L'ESSENCE → minimalisme puissant",
                'spectrer': "Tendance à EXPLORER LA STRUCTURE → abstraction",
            }
            desc = descriptions.get(name, name)
            lines.append(f"  {pct:.0f}% {desc}")
        lines.append(f"  Mémoire créative : {len(self._creative_memory)} créations")
        return "\n".join(lines)

    @property
    def stats(self) -> dict:
        return {
            'ruminating': self._ruminating,
            'rumination_count': self._rumination_count,
            'emergent_ideas': len(self._emergent_ideas),
            'creative_memory': len(self._creative_memory),
            'style_formed': self._style_vector is not None,
            'top_ops': dict(sorted(self._successful_ops.items(),
                                   key=lambda x: -x[1])[:3]),
            'temperature': self.temperature,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  CONSCIENT CRÉATEUR — Test")
    print("=" * 60)

    from harmonic_brain import HarmonicBrain

    # KB riche et variée
    kb = [
        ("pluie", "tombe sur", "la terre", "NATURE"),
        ("pluie", "fait pousser", "les fleurs", "NATURE"),
        ("musique", "est", "l art des sons", "CULTURE"),
        ("musique", "exprime", "les emotions", "CULTURE"),
        ("ocean", "est", "immense et profond", "NATURE"),
        ("ocean", "abrite", "des creatures mysterieuses", "NATURE"),
        ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
        ("lumiere", "eclaire", "le monde", "PHYSIQUE_FOND"),
        ("temps", "est", "la quatrieme dimension", "PHYSIQUE_FOND"),
        ("temps", "s ecoule", "inexorablement", "PHYSIQUE_FOND"),
        ("amour", "est", "la force fondamentale de l univers", "EMOTION_POS"),
        ("amour", "unit", "les etres", "EMOTION_POS"),
        ("silence", "est", "l absence de son", "CULTURE"),
        ("silence", "precede", "la musique", "CULTURE"),
        ("feu", "est", "une reaction chimique", "PHYSIQUE_FOND"),
        ("feu", "rechauffe", "les corps", "PHYSIQUE_FOND"),
    ]
    brain = HarmonicBrain(kb, dim=64, use_holographic=False)

    # Test 1 : Création ponctuelle
    print("\n── 1. Création ponctuelle ──")
    creator = ConsciousCreator(brain=brain, dim=64)

    ideas = []
    for _ in range(5):
        idea = creator.create("trouve une connexion creative")
        if idea:
            print(f"  {idea.expression}")
            ideas.append(idea)

    # Test 2 : Rumination
    print("\n── 2. Rumination (3 secondes) ──")
    creator.start_ruminating(interval_seconds=0.3)
    time.sleep(3)
    creator.stop_ruminating()

    emergent = creator.get_emergent_ideas(5)
    print(f"  Idées émergentes: {len(emergent)}")
    for idea in emergent:
        print(f"  🧠 {idea.expression}")

    # Test 3 : Style
    print(f"\n── 3. Style ──")
    print(creator.get_style_description())

    # Test 4 : Température créative
    print(f"\n── 4. Température ──")
    for temp in [0.2, 0.5, 0.8]:
        creator.temperature = temp
        idea = creator.create("connexion creative")
        if idea:
            print(f"  φ={temp}: {idea.op_name} (qualité={idea.quality:.2f}, "
                  f"nouveauté={idea.novelty:.2f})")

    print(f"\n✅ Conscious Creator — {creator.stats}")
