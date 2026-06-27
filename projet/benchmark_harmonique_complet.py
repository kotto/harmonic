#!/usr/bin/env python3
"""
BENCHMARK COMPLET — Performances du système harmonique
=======================================================
Mesure les performances réelles de :
  1. GGUFHarmonizer (injection, sampling, scoring, mémoire ABC)
  2. Moteur Harmonique (signatures 9D, ABC kernel, harmonic engine)
  3. Pipeline complet (prompt → classification → injection → scoring)

Tests unitaires + benchmarks de performance + comparaison harmonique vs non-harmonique
"""

import sys, os, time, math, json, random
from typing import Dict, List, Any
from collections import Counter
from datetime import datetime

# Ajouter le chemin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ===========================================================================
# IMPORT DES COMPOSANTS
# ===========================================================================

HARMONIK_AVAILABLE = True
HARMONIC_ENGINE_AVAILABLE = True

try:
    from engine.llm.gguf_harmonizer import (
        GGUFHarmonicProxy, GGUFHarmonicInjector, GGUFHarmonicSampler,
        ABCMemory, GGUFHarmonicProxyConfig, GGUFHarmonicClassifier,
        PHI, PHI_INV, HARMONIC_FREQUENCIES, HARMONIC_WEIGHTS_9D
    )
    print("[OK] GGUFHarmonizer importe")
except ImportError as e:
    print(f"[!] GGUFHarmonizer non disponible: {e}")
    HARMONIK_AVAILABLE = False

try:
    from engine.harmonic_engine import HarmonicEngine
    from engine.abc_kernel import ABCKernel
    from engine.signatures_9d import SignatureGenerator
    HARMONIC_ENGINE_AVAILABLE = True
    print("[OK] HarmonicEngine importe")
except ImportError as e:
    print(f"[!] HarmonicEngine non disponible: {e}")
    HARMONIC_ENGINE_AVAILABLE = False

# ===========================================================================
# BENCHMARK 1: LATENCE DU SYSTEME COMPLET
# ===========================================================================

class BenchmarkLatence:
    """Mesure la latence de chaque composant."""

    def __init__(self):
        self.results = {}
        self.sampler = GGUFHarmonicSampler() if HARMONIK_AVAILABLE else None
        self.injector = GGUFHarmonicInjector() if HARMONIK_AVAILABLE else None
        self.proxy = GGUFHarmonicProxy(GGUFHarmonicProxyConfig(
            model_path='', model_alias='benchmark', use_memory=True
        )) if HARMONIK_AVAILABLE else None
        self.engine = HarmonicEngine() if HARMONIC_ENGINE_AVAILABLE else None
        self.abc = ABCKernel(max_len=8192) if HARMONIC_ENGINE_AVAILABLE else None
        self.sig_gen = SignatureGenerator() if HARMONIC_ENGINE_AVAILABLE else None

    def run(self, iterations: int = 100):
        """Execute tous les sous-benchmarks."""
        print(f"\n{'='*60}")
        print(f"BENCHMARK 1: LATENCE ({iterations} iterations)")
        print(f"{'='*60}")

        # Prompts de test
        prompts = [
            "Calcule l'integrale de x^2 de 0 a 1",
            "Ecris un poeme sur l'ocean et les vagues",
            "Explique le principe de relativite generale",
            "Ecris une fonction Python qui trie une liste",
            "Qui a decouvert l'Amerique et en quelle annee",
            "Analyse les causes de la premiere guerre mondiale",
            "Resous l'equation differentielle y' = y",
            "Decris un paysage de montagne au coucher du soleil",
            "Compare les algorithmes de tri rapide et fusion",
            "Quelle est la capitale du Bresil",
        ]

        # 1. Detection de categorie
        print("\n  1.1 Detection de categorie...")
        times = []
        for _ in range(iterations):
            prompt = random.choice(prompts)
            t0 = time.perf_counter_ns()
            cat = self.injector._detect_category(prompt)
            elapsed = (time.perf_counter_ns() - t0) / 1000
            times.append(elapsed)
        self.results["detection_categorie"] = {
            "avg_us": round(sum(times) / len(times), 1),
            "min_us": round(min(times), 1),
            "max_us": round(max(times), 1),
            "ops_per_sec": round(1_000_000 / (sum(times) / len(times)), 0),
        }
        avg = self.results["detection_categorie"]["avg_us"]
        print(f"    Moyenne: {avg:.1f} us  ({self.results['detection_categorie']['ops_per_sec']:.0f} ops/s)")

        # 2. Signature 9D rapide
        print("\n  1.2 Signature 9D rapide...")
        times = []
        for _ in range(iterations):
            prompt = random.choice(prompts)
            t0 = time.perf_counter_ns()
            sig = self.injector._quick_signature_9d(prompt)
            elapsed = (time.perf_counter_ns() - t0) / 1000
            times.append(elapsed)
        self.results["signature_9d"] = {
            "avg_us": round(sum(times) / len(times), 1),
            "min_us": round(min(times), 1),
            "max_us": round(max(times), 1),
            "ops_per_sec": round(1_000_000 / (sum(times) / len(times)), 0),
        }
        avg = self.results["signature_9d"]["avg_us"]
        print(f"    Moyenne: {avg:.1f} us  ({self.results['signature_9d']['ops_per_sec']:.0f} ops/s)")

        # 3. Construction du prompt harmonique
        print("\n  1.3 Construction du prompt harmonique...")
        times = []
        for _ in range(iterations):
            prompt = random.choice(prompts)
            cat = self.injector._detect_category(prompt)
            t0 = time.perf_counter_ns()
            built = self.injector.build(prompt, category=cat)
            elapsed = (time.perf_counter_ns() - t0) / 1000
            times.append(elapsed)
        self.results["construction_prompt"] = {
            "avg_us": round(sum(times) / len(times), 1),
            "min_us": round(min(times), 1),
            "max_us": round(max(times), 1),
            "ops_per_sec": round(1_000_000 / (sum(times) / len(times)), 0),
        }
        avg = self.results["construction_prompt"]["avg_us"]
        print(f"    Moyenne: {avg:.1f} us  ({self.results['construction_prompt']['ops_per_sec']:.0f} ops/s)")

        # 4. Scoring de resonance
        print("\n  1.4 Scoring de resonance...")
        texts = [
            "Le ciel est bleu a cause de la diffusion Rayleigh. La lumiere du soleil "
            "interagit avec les molecules de l'atmosphere et diffuse davantage les "
            "longueurs d'onde courtes (bleu) que les longues (rouge). C'est pourquoi "
            "le ciel nous parait bleu pendant la journee.",
            "Pour resoudre l'equation x^2 - 5x + 6 = 0, on utilise la formule du "
            "discriminant: Delta = b^2 - 4ac = 25 - 24 = 1. Donc x = (5 +/- 1)/2, "
            "soit x = 3 ou x = 2.",
            "def trier_liste(liste): return sorted(liste)  # Tri ascendant",
        ]
        times = []
        for _ in range(iterations):
            text = random.choice(texts)
            t0 = time.perf_counter_ns()
            score = self.sampler.score_resonance(text)
            elapsed = (time.perf_counter_ns() - t0) / 1000
            times.append(elapsed)
        self.results["scoring_resonance"] = {
            "avg_us": round(sum(times) / len(times), 1),
            "min_us": round(min(times), 1),
            "max_us": round(max(times), 1),
            "ops_per_sec": round(1_000_000 / (sum(times) / len(times)), 0),
        }
        avg = self.results["scoring_resonance"]["avg_us"]
        print(f"    Moyenne: {avg:.1f} us  ({self.results['scoring_resonance']['ops_per_sec']:.0f} ops/s)")

        # 5. Memoire ABC (add + recall)
        print("\n  1.5 Memoire ABC...")
        memory = ABCMemory(max_tokens=100000)
        times_add = []
        times_recall = []
        for i in range(iterations):
            text = f"Element memoire #{i}: {random.choice(texts)[:50]}"
            importance = random.random()
            t0 = time.perf_counter_ns()
            memory.add(text, importance=importance, category="general")
            elapsed = (time.perf_counter_ns() - t0) / 1000
            times_add.append(elapsed)

            t0 = time.perf_counter_ns()
            results = memory.recall("ciel bleu", top_k=3)
            elapsed = (time.perf_counter_ns() - t0) / 1000
            times_recall.append(elapsed)

        self.results["memoire_abc_add"] = {
            "avg_us": round(sum(times_add) / len(times_add), 1),
            "min_us": round(min(times_add), 1),
            "max_us": round(max(times_add), 1),
            "ops_per_sec": round(1_000_000 / (sum(times_add) / len(times_add)), 0),
        }
        self.results["memoire_abc_recall"] = {
            "avg_us": round(sum(times_recall) / len(times_recall), 1),
            "min_us": round(min(times_recall), 1),
            "max_us": round(max(times_recall), 1),
            "ops_per_sec": round(1_000_000 / (sum(times_recall) / len(times_recall)), 0),
        }
        avg_add = self.results["memoire_abc_add"]["avg_us"]
        avg_recall = self.results["memoire_abc_recall"]["avg_us"]
        print(f"    Add:    {avg_add:.1f} us  ({self.results['memoire_abc_add']['ops_per_sec']:.0f} ops/s)")
        print(f"    Recall: {avg_recall:.1f} us  ({self.results['memoire_abc_recall']['ops_per_sec']:.0f} ops/s)")

        # 6. Pipeline complet (categorisation + signature + construction prompt)
        print("\n  1.6 Pipeline complet (categorisation + signature + prompt)...")
        times = []
        for _ in range(iterations):
            prompt = random.choice(prompts)
            t0 = time.perf_counter_ns()
            cat = self.injector._detect_category(prompt)
            sig = self.injector._quick_signature_9d(prompt)
            built = self.injector.build(prompt, category=cat)
            elapsed = (time.perf_counter_ns() - t0) / 1000
            times.append(elapsed)
        self.results["pipeline_complet"] = {
            "avg_us": round(sum(times) / len(times), 1),
            "min_us": round(min(times), 1),
            "max_us": round(max(times), 1),
            "ops_per_sec": round(1_000_000 / (sum(times) / len(times)), 0),
        }
        avg = self.results["pipeline_complet"]["avg_us"]
        print(f"    Moyenne: {avg:.1f} us  ({self.results['pipeline_complet']['ops_per_sec']:.0f} ops/s)")

        return self.results


# ===========================================================================
# BENCHMARK 2: PRECISION DE LA CLASSIFICATION
# ===========================================================================

class BenchmarkPrecision:
    """Mesure la precision de la classification 9D."""

    def __init__(self):
        self.injector = GGUFHarmonicInjector() if HARMONIK_AVAILABLE else None

    def run(self):
        print(f"\n{'='*60}")
        print("BENCHMARK 2: PRECISION CLASSIFICATION")
        print(f"{'='*60}")

        test_cases = [
            # (prompt, categorie_attendue, dimensions_fortertes)
            ("Calcule 15% de 340", "mathematical", ["math"]),
            ("Ecris une fonction Python de tri", "code", ["code"]),
            ("Ecris un poeme sur la beaute de l'ocean", "creative", ["creative", "emotion"]),
            ("Explique pourquoi le ciel est bleu", "reasoning", ["reasoning", "factual"]),
            ("Qui a decouvert l'Amerique", "factual", ["factual"]),
            ("Resous l'equation x^2 - 5x + 6 = 0", "mathematical", ["math", "reasoning"]),
            ("Analyse les causes du changement climatique", "reasoning", ["reasoning", "factual"]),
            ("Imaginer un monde sans gravite", "creative", ["creative"]),
            ("Ecris un algorithme de recherche binaire", "code", ["code", "reasoning"]),
            ("Quelle est la definition de la conscience", "factual", ["factual"]),
            ("Compare les avantages du Python et du JavaScript", "reasoning", ["reasoning", "code"]),
            ("Calcule l'aire d'un cercle de rayon 5", "mathematical", ["math"]),
            ("Decris un coucher de soleil sur la plage", "creative", ["creative", "emotion"]),
            ("Quand a eu lieu la revolution francaise", "factual", ["factual", "temporal"]),
            ("Debug cette fonction: def add(a,b): return a-b", "code", ["code"]),
        ]

        correct = 0
        total = len(test_cases)
        dim_results = Counter()

        for prompt, expected_cat, expected_dims in test_cases:
            detected_cat = self.injector._detect_category(prompt)
            sig = self.injector._quick_signature_9d(prompt)

            # Map dimension names to indices
            dim_map = {
                "phi": 0, "alpha": 1, "reasoning": 2, "creative": 3,
                "math": 4, "factual": 5, "code": 6, "emotion": 7, "temporal": 8
            }

            dim_names_map = {
                "math": "mathematical",
                "code": "code",
                "creative": "creative",
                "reasoning": "reasoning",
                "factual": "factual",
                "emotion": "emotion",
                "temporal": "temporal",
                "phi": "phi",
                "alpha": "alpha",
            }

            # Verifier la categorie
            cat_ok = detected_cat == expected_cat

            # Verifier les dimensions fortes (> 0.3 pour mathematiques, > 0.2 pour les autres)
            dims_ok = all(sig[dim_map[d]] > 0.2 for d in expected_dims)

            if cat_ok and dims_ok:
                correct += 1
            elif cat_ok:
                # Au moins la categorie est bonne
                correct += 0.5

            # Debug pour les echecs
            if not cat_ok:
                print(f"  [!] {prompt[:40]}... attendu={expected_cat}, detecte={detected_cat}")

        precision = correct / total * 100
        print(f"\n  Precision classification: {correct:.0f}/{total} = {precision:.1f}%")
        self.results = {
            "correct": correct,
            "total": total,
            "precision_pct": round(precision, 1),
        }
        return self.results


# ===========================================================================
# BENCHMARK 3: PERFORMANCE MEMOIRE ABC
# ===========================================================================

class BenchmarkMemoire:
    """Mesure les performances de la memoire ABC."""

    def __init__(self):
        pass

    def run(self):
        print(f"\n{'='*60}")
        print("BENCHMARK 3: PERFORMANCE MEMOIRE ABC")
        print(f"{'='*60}")

        memory = ABCMemory(max_tokens=50000)
        n_items = 500

        # Insertion en masse
        print(f"\n  3.1 Insertion de {n_items} elements...")
        t0 = time.time()
        for i in range(n_items):
            text = f"Element #{i}: " + "mots " * random.randint(5, 20)
            memory.add(text, importance=random.random(), category=random.choice(
                ["factual", "mathematical", "creative", "code", "general"]
            ))
        elapsed = time.time() - t0
        ops_per_sec = n_items / elapsed
        print(f"    {n_items} insertions en {elapsed:.2f}s = {ops_per_sec:.0f} ops/s")

        # Rappel
        print(f"\n  3.2 Rappel de 500 requetes...")
        t0 = time.time()
        n_recall = 500
        for i in range(n_recall):
            query = f"Element #{random.randint(0, n_items-1)}"
            results = memory.recall(query, top_k=5)
        elapsed_recall = time.time() - t0
        recall_ops = n_recall / elapsed_recall
        print(f"    {n_recall} rappels en {elapsed_recall:.2f}s = {recall_ops:.0f} ops/s")

        # Stats de la memoire
        stats = memory.stats()
        print(f"\n  3.3 Etat final de la memoire:")
        print(f"    Items: {stats['total_items']}")
        print(f"    Tokens: {stats['total_tokens']}")
        print(f"    Utilisation: {stats['utilization']}%")
        print(f"    Resonance moyenne: {stats['avg_resonance']}")
        print(f"    Categories: {stats['categories']}")

        self.results = {
            "insertion_ops": round(ops_per_sec, 0),
            "recall_ops": round(recall_ops, 0),
            "items_finaux": stats['total_items'],
            "tokens_finaux": stats['total_tokens'],
            "resonance_moyenne": stats['avg_resonance'],
            "categories": stats['categories'],
        }
        return self.results


# ===========================================================================
# BENCHMARK 4: COMPARAISON HARMONIQUE vs NON-HARMONIQUE
# ===========================================================================

class BenchmarkComparaison:
    """Compare les performances avec et sans resonance harmonique."""

    def __init__(self):
        self.injector = GGUFHarmonicInjector() if HARMONIK_AVAILABLE else None
        self.sampler = GGUFHarmonicSampler() if HARMONIK_AVAILABLE else None

    def run(self):
        print(f"\n{'='*60}")
        print("BENCHMARK 4: COMPARAISON HARMONIQUE vs STANDARD")
        print(f"{'='*60}")

        test_prompts = [
            "Calcule 15% de 340 euros",
            "Explique la difference entre RNA et ADN",
            "Ecris une classe Python BankAccount",
            "Analyse les causes de la guerre froide",
            "Ecris un haiku sur la nature",
            "Resous 2x + 5 = 13",
            "Compare les ecosystemes marins et terrestres",
            "Quelle est la formule de l'energie cinetique",
            "Decris le processus de photosynthese",
            "Corrige cette fonction: def sum(a,b) return a+b",
        ]

        # 1. Overhead du prompt harmonique
        print("\n  4.1 Overhead du prompt harmonique...")
        standard_len = []
        harmonique_len = []
        for prompt in test_prompts:
            std = len(prompt)
            cat = self.injector._detect_category(prompt)
            harm = len(self.injector.build(prompt, category=cat))
            standard_len.append(std)
            harmonique_len.append(harm)

        avg_std = sum(standard_len) / len(standard_len)
        avg_harm = sum(harmonique_len) / len(harmonique_len)
        ratio = avg_harm / avg_std
        print(f"    Prompt standard:  {avg_std:.0f} caracteres")
        print(f"    Prompt harmonique: {avg_harm:.0f} caracteres")
        print(f"    Overhead: x{ratio:.1f} ({ratio*100-100:.0f}% plus long)")

        # 2. Comparaison des parametres de sampling
        print("\n  4.2 Comparaison des parametres de sampling...")
        print(f"    {'Categorie':<15} {'Standard':>12} {'Harmonique':>20}")
        print(f"    {'-'*47}")
        standard_params = {"temperature": 0.7, "top_p": 0.95, "top_k": 50}
        for cat in ["mathematical", "code", "creative", "reasoning", "factual", "general"]:
            harm = self.sampler.get_params(cat)
            print(f"    {cat:<15} T={standard_params['temperature']:.1f}, "
                  f"p={standard_params['top_p']:.2f}, k={standard_params['top_k']:<3}  "
                  f"T={harm['temperature']:.1f}, p={harm['top_p']:.2f}, k={harm['top_k']}")

        # 3. Distribution des scores de resonance
        print("\n  4.3 Distribution des scores de resonance...")
        scores_par_categorie = {}
        for cat in ["mathematical", "code", "creative", "reasoning", "factual", "general"]:
            sample_texts = {
                "mathematical": "Pour resoudre cette equation, calculons d'abord le discriminant. "
                               "Delta = b^2 - 4ac. Puis appliquons la formule quadratique. "
                               "Les racines sont x1 = (-b + sqrt(Delta)) / 2a.",
                "code": "def binary_search(arr, x): low = 0; high = len(arr) - 1; "
                       "while low <= high: mid = (low + high) // 2; "
                       "if arr[mid] < x: low = mid + 1; elif arr[mid] > x: high = mid - 1; "
                       "else: return mid; return -1",
                "creative": "Dans le silence de l'aube, les vagues dansent doucement "
                           "sur le sable dore. Le vent murmure des secrets oublies, "
                           "tandis que le soleil embrasse l'horizon de ses rayons ardents.",
                "reasoning": "Si A implique B, et B implique C, alors par transitivite, "
                           "A implique C. Cependant, si non-C est vrai, alors par "
                           "contraposition, non-A est necessairement vrai.",
                "factual": "La capitale de la France est Paris. La France a 67 millions "
                          "d'habitants. La langue officielle est le francais. "
                          "Le pays est membre de l'Union europeenne depuis 1957.",
                "general": "Bonjour, comment allez-vous aujourd'hui? "
                          "J'espere que tout va bien. Merci de votre question.",
            }
            text = sample_texts.get(cat, sample_texts["general"])
            score = self.sampler.score_resonance(text)
            scores_par_categorie[cat] = score["resonance"]
            print(f"    {cat:<15} resonance = {score['resonance']:.3f} "
                  f"(entropy={score['entropy']:.2f}, diversity={score['diversity']:.2f})")

        self.results = {
            "overhead_ratio": round(ratio, 2),
            "avg_standard_len": round(avg_std, 0),
            "avg_harmonique_len": round(avg_harm, 0),
            "scores_resonance_par_categorie": scores_par_categorie,
        }
        return self.results


# ===========================================================================
# BENCHMARK 5: CAPACITE DU SYSTEME COMPLET
# ===========================================================================

class BenchmarkCapacite:
    """Mesure la capacite du systeme a gerer un grand nombre de requetes."""

    def __init__(self):
        self.proxy = GGUFHarmonicProxy(GGUFHarmonicProxyConfig(
            model_path='', model_alias='benchmark-capacite',
            use_memory=True, max_memory_tokens=20000
        )) if HARMONIK_AVAILABLE else None

    def run(self):
        print(f"\n{'='*60}")
        print("BENCHMARK 5: CAPACITE ET STRESS TEST")
        print(f"{'='*60}")

        n_requetes = 500
        prompts = [
            "Calcule l'integrale de x^2",
            "Ecris un poeme",
            "Explique la relativite",
            "Fonction Python de tri",
            "Capitale du Bresil",
            "Causes de la guerre",
            "Resous 2x + 5 = 13",
            "Coucher de soleil",
            "Comparaison algorithmes",
            "Definition de la conscience",
        ]

        # Execution en rafale
        print(f"\n  5.1 Execution de {n_requetes} requetes en rafale...")
        t0 = time.time()
        for i in range(n_requetes):
            prompt = random.choice(prompts)
            result = self.proxy.generate_auto(prompt, max_tokens=50)
        elapsed = time.time() - t0
        ops = n_requetes / elapsed
        print(f"    {n_requetes} requetes en {elapsed:.2f}s = {ops:.1f} req/s")
        print(f"    Latence moyenne: {elapsed/n_requetes*1000:.1f} ms/req")

        # Stats apres stress
        stats = self.proxy.get_stats()
        print(f"\n  5.2 Stats apres stress test:")
        print(f"    Total appels: {stats['total_calls']}")
        print(f"    Resonance moyenne: {stats['avg_resonance']:.4f}")
        print(f"    Fallbacks: {stats['fallbacks']}")
        print(f"    Memoire: {stats['memory_items']} items, "
              f"util={stats['memory_utilization']}%")

        self.results = {
            "requetes": n_requetes,
            "temps_total": round(elapsed, 2),
            "req_par_seconde": round(ops, 1),
            "latence_moyenne_ms": round(elapsed / n_requetes * 1000, 1),
            "resonance_moyenne": stats['avg_resonance'],
            "fallbacks": stats['fallbacks'],
            "memoire_items": stats['memory_items'],
        }
        return self.results


# ===========================================================================
# RAPPORT FINAL
# ===========================================================================

class RapportBenchmark:
    """Genere le rapport final complet."""

    def __init__(self):
        self.all_results = {}

    def add(self, name: str, results: Dict):
        self.all_results[name] = results

    def generate(self):
        print(f"\n{'='*60}")
        print("RAPPORT FINAL — PERFORMANCES DU SYSTEME HARMONIQUE")
        print(f"{'='*60}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Composants: GGUFHarmonizer={HARMONIK_AVAILABLE}, "
              f"HarmonicEngine={HARMONIC_ENGINE_AVAILABLE}")

        # Section 1: Latence
        if "latence" in self.all_results:
            r = self.all_results["latence"]
            print(f"\n--- LATENCE ---")
            for component, metrics in r.items():
                print(f"  {component:<25} {metrics['avg_us']:>8.1f} us  "
                      f"({metrics['ops_per_sec']:>8.0f} ops/s)  "
                      f"[min={metrics['min_us']:.1f}, max={metrics['max_us']:.1f}]")

        # Section 2: Precision
        if "precision" in self.all_results:
            r = self.all_results["precision"]
            print(f"\n--- PRECISION ---")
            print(f"  Classification: {r['precision_pct']:.1f}% "
                  f"({r['correct']:.0f}/{r['total']})")

        # Section 3: Memoire
        if "memoire" in self.all_results:
            r = self.all_results["memoire"]
            print(f"\n--- MEMOIRE ABC ---")
            print(f"  Insertion: {r['insertion_ops']:.0f} ops/s")
            print(f"  Rappel:    {r['recall_ops']:.0f} ops/s")
            print(f"  Items finaux: {r['items_finaux']}, Tokens: {r['tokens_finaux']}")
            print(f"  Resonance moyenne: {r['resonance_moyenne']:.3f}")

        # Section 4: Comparaison
        if "comparaison" in self.all_results:
            r = self.all_results["comparaison"]
            print(f"\n--- COMPARAISON HARMONIQUE vs STANDARD ---")
            print(f"  Overhead prompt: x{r['overhead_ratio']:.1f} "
                  f"({r['avg_standard_len']:.0f} -> {r['avg_harmonique_len']:.0f} car.)")
            if "scores_resonance_par_categorie" in r:
                print(f"  Scores resonance par categorie:")
                for cat, score in r["scores_resonance_par_categorie"].items():
                    bar = "#" * int(score * 30)
                    print(f"    {cat:<15} {bar} {score:.3f}")

        # Section 5: Capacite
        if "capacite" in self.all_results:
            r = self.all_results["capacite"]
            print(f"\n--- CAPACITE ---")
            print(f"  Debit: {r['req_par_seconde']:.1f} req/s")
            print(f"  Latence: {r['latence_moyenne_ms']:.1f} ms/req")
            print(f"  Resonance moyenne apres {r['requetes']} req: {r['resonance_moyenne']:.4f}")
            print(f"  Fallbacks: {r['fallbacks']}")

        # Synthese
        print(f"\n{'='*60}")
        print("SYNTHESE")
        print(f"{'='*60}")
        if "latence" in self.all_results:
            lat = self.all_results["latence"]
            pipeline = lat.get("pipeline_complet", {})
            pipeline_ops = pipeline.get("ops_per_sec", 0)
            print(f"  Pipeline complet (classif + signature + prompt): "
                  f"{pipeline.get('avg_us', 0):.0f} us ({pipeline_ops:.0f} ops/s)")
            if pipeline_ops > 50000:
                print(f"  [OK] Le pipeline harmonique < 20 us — Excellent !")
            elif pipeline_ops > 10000:
                print(f"  [!] Le pipeline harmonique est rapide (quelques us)")
            else:
                print(f"  [WARN] Pipeline un peu lent")

        if "precision" in self.all_results:
            prec = self.all_results["precision"]["precision_pct"]
            if prec >= 90:
                print(f"  [OK] Classification: {prec:.0f}% — Excellent !")
            elif prec >= 75:
                print(f"  [!] Classification: {prec:.0f}% — Satisfaisant")
            else:
                print(f"  [WARN] Classification: {prec:.0f}% — A ameliorer")

        if "memoire" in self.all_results:
            mem = self.all_results["memoire"]
            if mem["insertion_ops"] > 5000:
                print(f"  [OK] Memoire ABC: {mem['insertion_ops']:.0f} insert/s — Excellent !")
            elif mem["insertion_ops"] > 1000:
                print(f"  [!] Memoire ABC performante")

        if "capacite" in self.all_results:
            cap = self.all_results["capacite"]
            if cap["req_par_seconde"] > 500:
                print(f"  [OK] Debit: {cap['req_par_seconde']:.0f} req/s — Excellent !")
            elif cap["req_par_seconde"] > 100:
                print(f"  [!] Debit correct")

        # Export JSON
        json_path = "benchmark_harmonique_resultats.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.all_results, f, indent=2, ensure_ascii=False)
        print(f"\n  Resultats exportes: {json_path}")
        print(f"{'='*60}")

        return self.all_results


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    print("=== BENCHMARK COMPLET DU SYSTEME HARMONIQUE ===")
    print(f"Python {sys.version}")
    print(f"PHI = {PHI:.10f}")
    print(f"PHI_INV = {PHI_INV:.10f}")
    print()

    rapport = RapportBenchmark()

    # Benchmark 1: Latence
    if HARMONIK_AVAILABLE:
        bl = BenchmarkLatence()
        results = bl.run(iterations=200)
        rapport.add("latence", results)

    # Benchmark 2: Precision
    if HARMONIK_AVAILABLE:
        bp = BenchmarkPrecision()
        results = bp.run()
        rapport.add("precision", results)

    # Benchmark 3: Memoire
    if HARMONIK_AVAILABLE:
        bm = BenchmarkMemoire()
        results = bm.run()
        rapport.add("memoire", results)

    # Benchmark 4: Comparaison
    if HARMONIK_AVAILABLE:
        bc = BenchmarkComparaison()
        results = bc.run()
        rapport.add("comparaison", results)

    # Benchmark 5: Capacite
    if HARMONIK_AVAILABLE:
        bcap = BenchmarkCapacite()
        results = bcap.run()
        rapport.add("capacite", results)

    # Rapport final
    rapport.generate()

    print("\nBenchmark termine.")


if __name__ == "__main__":
    main()
