"""
🌊 Wave Pipeline — Intégration verticale NL → AST → Optimisé → Exécution
=========================================================================

Chaîne complète en un seul appel :

    Question NL
      → WaveIntentDetector (10 intentions)
      → wave-code-generator (AST wave_ir)
      → wave-ir-compiler validate() (conformité AST)
      → wave-compiler (4 passes d'optimisation)
      → wave_lang (exécution sur les 13 primitives)
      → Résultat + métriques

Chaque étape est un maillon vérifié : l'AST est validé avant compilation,
le programme est optimisé avant exécution, les métriques sont mesurées.

Usage :
    from wave_pipeline import WavePipeline

    pipeline = WavePipeline()
    result = pipeline.run("Qu'est-ce que la lumière ?")
    print(result.synthesized)          # réponse en langage naturel
    print(result.stats)                # timings par étape
"""

from __future__ import annotations

import sys
import os
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# ── Chemin : les modules vivent dans vital-ka/core/python + racine ──
# NOTE : vital-ka/core/python est la source CANONIQUE (copies racine obsolètes).
#        Il doit passer DEVANT la racine dans sys.path, même s'il est déjà
#        présent (cwd) — d'où la suppression des doublons puis ré-insertion.
_PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_PYTHON_DIR)))
for _p in (_PYTHON_DIR, _PROJECT_ROOT):
    while _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, _PROJECT_ROOT)
sys.path.insert(0, _PYTHON_DIR)

from wave_code_generator import WaveCodeGenerator, WaveIntentDetector, wave_to_python
from wave_ir import Program, validate, to_json, parse
from wave_compiler import WaveCompiler, CompileResult
from wave_lang import (encode, decode, resonate, coherence, superpose,
                       HolographicMemory, DEFAULT_DIM)

# Constantes du pipeline (4 passes du compilateur)
PASSES = ['constant_folding', 'dead_code_elimination', 'fusion', 'memory_pool']


@dataclass
class PipelineStep:
    """Une étape du pipeline avec son timing."""
    name: str
    duration_ms: float
    detail: str = ""


@dataclass
class PipelineResult:
    """Résultat complet d'un passage dans le pipeline."""
    question: str
    intent: str = "query"
    intent_confidence: float = 0.0
    program: Optional[Program] = None
    validation_warnings: List[str] = field(default_factory=list)
    optimized_program: Optional[Program] = None
    compile_stats: Dict = field(default_factory=dict)
    python_code: str = ""
    env: Dict[str, Any] = field(default_factory=dict)
    synthesized: str = ""
    steps: List[PipelineStep] = field(default_factory=list)

    @property
    def total_time_ms(self) -> float:
        return sum(s.duration_ms for s in self.steps)

    @property
    def is_valid(self) -> bool:
        """Le pipeline a produit un AST valide et exécutable."""
        return (self.program is not None and
                not self.validation_warnings and
                self.env is not None)

    def stats(self) -> Dict:
        """Métriques par étape + globales."""
        return {
            'intent': self.intent,
            'intent_confidence': round(self.intent_confidence, 3),
            'n_statements': len(self.program.statements) if self.program else 0,
            'n_optimized': len(self.optimized_program.statements) if self.optimized_program else 0,
            'compile_passes': self.compile_stats,
            'total_time_ms': round(self.total_time_ms, 1),
            'steps': {s.name: round(s.duration_ms, 1) for s in self.steps},
            'valid': self.is_valid,
        }


class BrainMemoryAdapter:
    """
    Adaptateur HolographicMemory → store du brain (retrieval RAG réel).

    Le WaveCompiler.execute attend des hologrammes avec `query(psi)` et
    `store_raw(psi)`. Cet adaptateur les branche sur les CONNAISSANCES
    réelles du brain (HarmonicBrain.unconscious ou HolographicRAG) :

        query(psi)   → retrieve_resonance(texte_décodé) → superposition
        store_raw(ψ) → ingest(texte_décodé)

    La boucle est fermée : le pipeline AST interroge la VRAIE mémoire.
    """

    def __init__(self, brain, dim: int = DEFAULT_DIM,
                 max_results: int = 10):
        """
        Args:
            brain: HarmonicBrain (unconscious) ou HolographicRAG
            dim: dimension de l'espace des phases
            max_results: nombre de faits résonants par requête
        """
        self.brain = brain
        self.dim = dim
        self.max_results = max_results
        self._n_queries = 0
        self._n_stores = 0

    # ── API HolographicMemory (utilisée par WaveCompiler) ──

    def query(self, psi: np.ndarray) -> np.ndarray:
        """
        Requête RAG : décode le ψ en texte, retrouve les faits résonants,
        retourne la SUPERPOSITION de leurs ψ (mémoire holographique).

        Returns:
            ψ_résultat ∈ ℂᵈⁱᵐ (superposition des faits résonants)
        """
        self._n_queries += 1

        # 1. Décoder le ψ en texte de requête
        try:
            top = decode(psi, top_k=3)
            words = self._format_words(top)
            question = " ".join(words) if words else ""
        except Exception:
            question = ""

        if not question:
            return np.zeros(self.dim, dtype=np.complex128)

        # 2. Retrieval RAG sur le brain
        facts = self._retrieve(question)

        if not facts:
            return np.zeros(self.dim, dtype=np.complex128)

        # 3. Superposition des ψ des faits résonants
        psis = []
        for fact, score in facts[:self.max_results]:
            psi_fact = self._fact_psi(fact)
            if psi_fact is not None:
                # Pondéré par la résonance (interférence constructive)
                psis.append(score * psi_fact)

        if not psis:
            return np.zeros(self.dim, dtype=np.complex128)

        return superpose(*psis)

    def store_raw(self, psi: np.ndarray, amplitude: float = 1.0) -> None:
        """
        Stocke une onde dans le brain (ingest du texte décodé).

        Args:
            psi: onde à stocker
            amplitude: amplitude (ignorée pour le brain, 1.0)
        """
        self._n_stores += 1
        try:
            top = decode(psi, top_k=3)
            text = " ".join(self._format_words(top))
            if text and len(text) > 3:
                self._ingest(text)
        except Exception:
            pass

    def query_scores(self, psi: np.ndarray) -> List[Tuple[int, float]]:
        """Scores de résonance des faits (compatibilité HolographicMemory)."""
        try:
            top = decode(psi, top_k=3)
            question = " ".join(self._format_words(top))
            facts = self._retrieve(question, max_results=self.max_results)
            return [(i, float(score)) for i, (fact, score) in enumerate(facts)]
        except Exception:
            return []

    @property
    def energy(self) -> float:
        """Énergie approximative de la mémoire (nb de faits)."""
        try:
            return float(self._n_facts())
        except Exception:
            return 0.0

    @property
    def n_facts(self) -> int:
        """Nombre de faits dans le brain."""
        try:
            return int(self._n_facts())
        except Exception:
            return 0

    # ── Helpers : accès brain (HolographicRAG ou HarmonicBrain) ──

    def _store_obj(self):
        """Retourne le store du brain (RAG ou unconscious)."""
        if hasattr(self.brain, 'retrieve_resonance'):
            return self.brain  # HolographicRAG
        if hasattr(self.brain, 'unconscious'):
            return self.brain.unconscious  # HarmonicBrain
        return None

    def _retrieve(self, question: str, max_results: int = None) -> List:
        """Retrieval RAG avec tolérance aux deux types de store."""
        store = self._store_obj()
        if store is None:
            return []
        k = max_results or self.max_results
        try:
            return store.retrieve_resonance(question, max_results=k)
        except Exception:
            return []

    def _fact_psi(self, fact) -> Optional[np.ndarray]:
        """Extrait le ψ d'un fait (dict ou FactRecord)."""
        if isinstance(fact, dict):
            return fact.get('psi')
        return getattr(fact, 'psi', None)

    def _fact_text(self, fact) -> str:
        """Extrait le texte d'un fait (dict ou FactRecord)."""
        if isinstance(fact, dict):
            return f"{fact.get('sujet','')} {fact.get('relation','')} {fact.get('objet','')}"
        return f"{getattr(fact, 'sujet', '')} {getattr(fact, 'relation', '')} {getattr(fact, 'objet', '')}"

    def _ingest(self, text: str) -> None:
        """Ingère un texte dans le brain (découpage en fait simple)."""
        store = self._store_obj()
        if store is None:
            return
        words = text.split()
        if len(words) >= 3:
            try:
                store.ingest(words[0], words[1], " ".join(words[2:]), "PIPELINE")
            except Exception:
                pass

    def _n_facts(self) -> int:
        """Nombre de faits dans le brain."""
        store = self._store_obj()
        if store is None:
            return 0
        if hasattr(store, 'stats') and isinstance(store.stats, dict):
            return store.stats.get('n_facts', 0)
        if hasattr(store, 'registry'):
            return len(store.registry)
        return 0

    @staticmethod
    def _format_words(top) -> List[str]:
        """Formate le résultat d'un decode() en liste de mots."""
        try:
            if hasattr(top, 'ndim') and top.ndim == 2:
                return [str(w) for w in top[:, 0]]
            if isinstance(top, list) and top:
                words = []
                for it in top:
                    if isinstance(it, (list, tuple)) and len(it) >= 1:
                        words.append(str(it[0]))
                    else:
                        words.append(str(it))
                return words
            return []
        except Exception:
            return []


class WavePipeline:
    """
    Pipeline vertical complet : question NL → réponse ondulatoire.

    Usage :
        pipeline = WavePipeline()
        r = pipeline.run("Qu'est-ce que la lumière ?")
        r.synthesized  # → réponse lisible
    """

    def __init__(self, brain=None, hologram_name: str = "H_connaissances",
                 dim: int = 512):
        """
        Args:
            brain: HarmonicBrain (optionnel, pour retrieval)
            hologram_name: nom de l'hologramme principal
            dim: dimension de l'espace des phases
        """
        self.dim = dim
        self.generator = WaveCodeGenerator(brain=brain, hologram_name=hologram_name)
        self.detector = WaveIntentDetector()
        self.compiler = WaveCompiler(dim=dim)
        self.hologram_name = hologram_name
        self.brain = brain

    # ═══════════════════════════════════════════════════════════════════
    # PIPELINE COMPLET
    # ═══════════════════════════════════════════════════════════════════

    def run(self, question: str, lang: str = 'fr') -> PipelineResult:
        """
        Exécute le pipeline complet sur une question.

        Étapes :
          1. DÉTECTION — intention ondulatoire (WaveIntentDetector)
          2. GÉNÉRATION — AST wave_ir (WaveCodeGenerator)
          3. VALIDATION — conformité AST (wave_ir.validate)
          4. COMPILATION — 4 passes d'optimisation (WaveCompiler)
          5. EXÉCUTION — sur les primitives wave_lang (WaveCompiler.execute)
          6. SYNTHÈSE — décodage de la réponse en langage naturel

        Args:
            question: question en langage naturel
            lang: langue ('fr' ou 'en')

        Returns:
            PipelineResult avec env (variables exécutées) et synthesized
        """
        result = PipelineResult(question=question)

        # ── 1. Détection d'intention ──
        t0 = time.perf_counter()
        intent, confidence = self.detector.detect_wave_intent(question)
        if confidence <= 0.15:
            intent = 'query'
            confidence = 0.5
        result.intent = intent
        result.intent_confidence = confidence
        result.steps.append(PipelineStep('detection',
                                         (time.perf_counter() - t0) * 1000,
                                         f"intent={intent}, conf={confidence:.2f}"))

        # ── 2. Génération AST ──
        t0 = time.perf_counter()
        try:
            program = self.generator.generate(question, lang=lang)
        except Exception as e:
            # Fallback : programme de requête minimal
            program = self._fallback_program(question)
        result.program = program
        result.steps.append(PipelineStep('generation',
                                         (time.perf_counter() - t0) * 1000,
                                         f"{len(program.statements)} statements"))

        # ── 3. Validation AST ──
        t0 = time.perf_counter()
        warnings = validate(program)
        result.validation_warnings = warnings
        result.steps.append(PipelineStep('validation',
                                         (time.perf_counter() - t0) * 1000,
                                         f"{len(warnings)} warnings"))

        # ── 4. Compilation (4 passes) ──
        t0 = time.perf_counter()
        try:
            compile_result = self.compiler.compile(program)
            result.optimized_program = compile_result.optimized_program
            result.compile_stats = compile_result.stats
            result.python_code = compile_result.python_code
        except Exception as e:
            result.compile_stats = {'error': str(e)}
            result.optimized_program = program
        result.steps.append(PipelineStep('compilation',
                                         (time.perf_counter() - t0) * 1000,
                                         f"{len(compile_result.optimized_program.statements) if result.optimized_program else 0} statements optimisés"))

        # ── 5. Exécution ──
        t0 = time.perf_counter()
        try:
            # Hologrammes : brain réel si fourni, sinon HolographicMemory vide
            if self.brain is not None:
                holograms = {self.hologram_name:
                             BrainMemoryAdapter(self.brain, dim=self.dim)}
            else:
                holograms = {self.hologram_name:
                             HolographicMemory(dim=self.dim)}
            env = self.compiler.execute(result.optimized_program or program,
                                        holograms=holograms)
            result.env = env
        except Exception as e:
            result.env = {'_error': str(e)}
        result.steps.append(PipelineStep('execution',
                                         (time.perf_counter() - t0) * 1000,
                                         f"{len(result.env)} variables"))

        # ── 6. Synthèse de la réponse ──
        t0 = time.perf_counter()
        try:
            from wave_response import WaveResponse
            result.synthesized = WaveResponse().synthesize(result)
        except ImportError:
            result.synthesized = self._synthesize(result)
        result.steps.append(PipelineStep('synthesis',
                                         (time.perf_counter() - t0) * 1000,
                                         f"'{result.synthesized[:40]}...'"))

        return result

    # ═══════════════════════════════════════════════════════════════════
    # INTERFACES SIMPLIFIÉES
    # ═══════════════════════════════════════════════════════════════════

    def run_and_synthesize(self, question: str, lang: str = 'fr') -> str:
        """
        Interface la plus simple : retourne uniquement la réponse finale.

        Args:
            question: question en langage naturel
            lang: langue

        Returns:
            réponse synthétisée en langage naturel
        """
        return self.run(question, lang=lang).synthesized

    def benchmark(self, questions: List[str], lang: str = 'fr') -> Dict:
        """
        Benchmark du pipeline sur une liste de questions.

        Args:
            questions: liste de questions
            lang: langue

        Returns:
            dict avec les métriques par question et le résumé global
        """
        results = [self.run(q, lang=lang) for q in questions]
        total_ms = sum(r.total_time_ms for r in results)

        return {
            'n_questions': len(questions),
            'total_time_ms': round(total_ms, 1),
            'mean_time_ms': round(total_ms / max(1, len(questions)), 1),
            'valid_count': sum(1 for r in results if r.is_valid),
            'intents': {r.intent: sum(1 for x in results if x.intent == r.intent)
                        for r in results},
            'per_question': [
                {
                    'question': r.question[:50],
                    'intent': r.intent,
                    'time_ms': round(r.total_time_ms, 1),
                    'valid': r.is_valid,
                    'synthesized': r.synthesized[:60],
                }
                for r in results
            ],
        }

    # ═══════════════════════════════════════════════════════════════════
    # UTILITAIRES INTERNES
    # ═══════════════════════════════════════════════════════════════════

    def _synthesize(self, result: PipelineResult) -> str:
        """Décode la dernière variable du programme en langage naturel."""
        env = result.env
        if not env or '_error' in env:
            return f"⚠️ Échec : {env.get('_error', 'env vide')}"

        # Chercher la variable de retour (Return) ou la dernière assignée
        return_var = None
        if result.program:
            for stmt in reversed(result.program.statements):
                if hasattr(stmt, 'name') and stmt.name in env:
                    return_var = stmt.name
                    break

        if return_var is None and env:
            # Dernière variable non-underscore
            candidates = [k for k in env if not k.startswith('_')]
            return_var = candidates[-1] if candidates else None

        if return_var is None:
            return ""

        value = env[return_var]

        # Si c'est un tableau complexe → décoder
        if hasattr(value, 'shape') and value.dtype.kind == 'c':
            try:
                top = decode(value, top_k=3)
                return self._format_decode(top)
            except Exception:
                return f"[ψ {value.shape}]"

        # Array numpy 2D de (mot, score) — sortie du compilateur
        if hasattr(value, 'ndim') and value.ndim == 2 and value.shape[1] == 2:
            return self._format_decode(value)

        # Sinon → chaîne ou nombre
        if isinstance(value, (str, int, float)):
            return str(value)

        return str(value)

    @staticmethod
    def _format_decode(top) -> str:
        """
        Formate le résultat d'un decode() en texte lisible.

        Gère : liste de tuples [(mot, score)], array numpy 2D [mot, score].
        """
        try:
            if hasattr(top, 'ndim') and top.ndim == 2:
                # Array numpy : [[mot, score], ...]
                words = [str(w) for w in top[:, 0]]
                return " ".join(words)
            if isinstance(top, list) and top:
                items = top[0] if isinstance(top[0], (list, tuple)) else top
                words = [str(it[0]) for it in top if isinstance(it, (list, tuple))]
                if words:
                    return " ".join(words)
                return str(top[0][0]) if isinstance(top[0], (list, tuple)) else str(top[0])
            return str(top)
        except Exception:
            return str(top)

    def _fallback_program(self, question: str) -> Program:
        """Programme minimal si la génération échoue."""
        from wave_ir import Assign, Return, Encode, Decode, Var
        return Program([
            Assign("psi_q", Encode(question)),
            Assign("reponse", Decode(Var("psi_q"), top_k=3)),
            Return(Var("reponse")),
        ])


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 WAVE PIPELINE — Intégration verticale")
    print("=" * 65)

    pipeline = WavePipeline()

    questions = [
        "Qu'est-ce que la lumière ?",
        "Pourquoi le ciel est-il bleu ?",
        "Souviens-toi que la Terre tourne autour du Soleil",
        "Quelle est la différence entre l'amour et l'amitié ?",
        "Imagine un mélange entre la pluie et la musique",
        "Échantillonne avec température 0.8 sur le concept de créativité",
        "Évalue la qualité de la réponse : le ciel est bleu",
    ]

    for q in questions:
        print(f"\n{'─' * 60}")
        print(f"  ❓ {q}")

        r = pipeline.run(q)

        print(f"  🎯 Intent: {r.intent} (confiance {r.intent_confidence:.0%})")
        print(f"  📜 AST: {len(r.program.statements)} statements"
              f" → {len(r.optimized_program.statements) if r.optimized_program else '?'} optimisés")
        if r.validation_warnings:
            for w in r.validation_warnings:
                print(f"  ⚠️  {w}")
        print(f"  ⚙️  Compile: {r.compile_stats}")
        print(f"  🧠 Env: {len(r.env)} variables")
        print(f"  💬 Réponse: '{r.synthesized}'")
        print(f"  ⏱️  {r.total_time_ms:.1f} ms "
              f"({', '.join(f'{s.name}:{s.duration_ms:.0f}ms' for s in r.steps)})")

    # Benchmark
    print(f"\n{'=' * 65}")
    bench = pipeline.benchmark(questions)
    print(f"  📊 BENCHMARK: {bench['n_questions']} questions, "
          f"moyenne {bench['mean_time_ms']:.1f} ms/question, "
          f"{bench['valid_count']}/{bench['n_questions']} valides")
    print(f"  🎯 Intentions: {bench['intents']}")

    # ── Pipeline avec BRAIN RÉEL (retrieval RAG) ──
    print(f"\n{'=' * 65}")
    print("  🧠 TEST BRAIN RÉEL (retrieval RAG)")
    print(f"{'=' * 65}")

    from wave_bridge import HolographicRAG

    brain = HolographicRAG(dim=512)
    brain.ingest("Terre", "orbite_autour_de", "Soleil", "ASTRONOMIE")
    brain.ingest("Lune", "orbite_autour_de", "Terre", "ASTRONOMIE")
    brain.ingest("Soleil", "est", "étoile", "ASTRONOMIE")
    brain.ingest("eau", "gèle_à", "0 degré", "PHYSIQUE")
    brain.ingest("eau", "bout_à", "100 degrés", "PHYSIQUE")

    pipeline_brain = WavePipeline(brain=brain)

    for q in ["Qu'est-ce que le Soleil ?", "À quelle température l'eau bout-elle ?"]:
        r = pipeline_brain.run(q)
        print(f"\n  ❓ {q}")
        print(f"  🎯 Intent: {r.intent} | 💬 Réponse: '{r.synthesized[:80]}'")
        print(f"  ⏱️  {r.total_time_ms:.1f} ms, valid={r.is_valid}")

    print("\n" + "=" * 65)
    print("  ✅ Wave Pipeline — Brain réel branché sur l'AST.")
    print("=" * 65)
