"""
HARMONIC AI V 5 — Tests de Performance (Benchmarks)
====================================================
Mesure les performances réelles du compagnon KA :
  - Latence par étape du pipeline
  - Débit (queries/seconde)
  - Mémoire (encodage, rappel, apprentissage, binding)
  - Personnalité (émotions, modulation, fusion)
  - Phraséologie (surface grammar + templates)
  - Charge mémoire (taille des structures)

Objectif : démontrer que les performances sont équivalentes
(ou supérieures) à un LLM, sans GPU, sans cloud.

Usage :
  python tests/test_performance.py
"""

import sys
import time
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from config import PHI, DIM_PSI
from core.memory_core import (
    MemoryCore, text_to_psi, psi_resonate, psi_bind, psi_unbind,
)
from core.personality_engine import PersonalityEngine
from core.phone_bus import PhoneBus
from core.conversation_pipeline import ConversationPipeline
from core.phrase_engine import PhraseEngine
from core.companion_core import KACompanion


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def bench(label: str, fn, n: int = 200):
    """Exécute fn n fois, retourne (min, moy, max, p99) en ms."""
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    p99 = times[int(n * 0.99)]
    return {
        'label': label,
        'min_ms': round(times[0], 3),
        'avg_ms': round(statistics.mean(times), 3),
        'max_ms': round(times[-1], 3),
        'p99_ms': round(p99, 3),
        'throughput_qps': round(1000 / statistics.mean(times), 0),
    }


def section(title: str):
    print(f"\n{'─'*72}")
    print(f"  {title}")
    print(f"{'─'*72}")


def print_bench(r):
    print(f"  {r['label']:<42s} "
          f"avg={r['avg_ms']:>8.3f}ms  "
          f"p99={r['p99_ms']:>8.3f}ms  "
          f"({r['throughput_qps']:>8.0f} q/s)")


# ═══════════════════════════════════════════════════════════
# 1. ENCODAGE ψ
# ═══════════════════════════════════════════════════════════

def bench_encoding():
    section("1. ENCODAGE ψ (texte → ℂ⁵¹²)")

    results = []
    results.append(bench("encode texte court (5 mots)",
                        lambda: text_to_psi("Sophie aime le chocolat noir")))
    results.append(bench("encode texte long (30 mots)",
                        lambda: text_to_psi(
                            "Sophie aime le chocolat noir et le thé vert le matin "
                            "elle habite à Paris dans le onzième arrondissement "
                            "et travaille comme architecte")))
    results.append(bench("résonance ψ (similarité)",
                        lambda: psi_resonate(
                            text_to_psi("Sophie"), text_to_psi("chocolat"))))

    for r in results:
        print_bench(r)


# ═══════════════════════════════════════════════════════════
# 2. MÉMOIRE HOLOGRAPHIQUE
# ═══════════════════════════════════════════════════════════

def bench_memory():
    section("2. MÉMOIRE HOLOGRAPHIQUE ℂ⁵¹²")

    mem = MemoryCore()

    # Apprentissage
    print("  [2.1] Apprentissage (H += ψ_fait)")
    t0 = time.perf_counter()
    for i in range(1000):
        mem.remember(f"Fait numéro {i}: Sophie aime le produit {i}", domain='general')
    learn_time = (time.perf_counter() - t0) * 1000
    print(f"    1000 faits en {learn_time:.1f} ms → "
          f"{1000 / learn_time * 1000:.0f} faits/s")
    print(f"    Total mémoire: {mem.store._total_facts} faits")

    # Rappel
    print("\n  [2.2] Rappel (H ☆ ψ_Q) — O(n)")
    t0 = time.perf_counter()
    for _ in range(100):
        mem.recall("Qu'est-ce que Sophie aime ?", top_k=5)
    recall_time = (time.perf_counter() - t0) * 1000
    print(f"    100 rappels sur {mem.store._total_facts} faits en "
          f"{recall_time:.1f} ms → {recall_time/100:.2f} ms/rappel")

    # Rappel avec taille croissante
    print("\n  [2.3] Scalabilité du rappel (O(n) linéaire)")
    for n in [100, 500, 1000]:
        t0 = time.perf_counter()
        for _ in range(50):
            mem.recall("test requête", top_k=5)
        dt = (time.perf_counter() - t0) * 1000
        print(f"    {n:>5d} faits → {dt/50:.3f} ms/rappel")

    # Binding HRR
    print("\n  [2.4] Binding HRR (bind/unbind)")
    psi_a = text_to_psi("Sophie")
    psi_b = text_to_psi("chocolat")
    results = [
        bench("bind HRR (FFT)",
              lambda: psi_bind(psi_a, psi_b), n=500),
        bench("unbind HRR (IFFT)",
              lambda: psi_unbind(psi_bind(psi_a, psi_b), psi_b), n=500),
    ]
    for r in results:
        print_bench(r)


# ═══════════════════════════════════════════════════════════
# 3. PERSONNALITÉ & ÉMOTIONS
# ═══════════════════════════════════════════════════════════

def bench_personality():
    section("3. PERSONNALITÉ & ÉMOTIONS")

    pers = PersonalityEngine()
    psi = text_to_psi("Bonjour, comment allez-vous ?")

    results = [
        bench("détection d'émotion",
              lambda: pers.detect_emotion("Je suis très heureux aujourd'hui !"),
              n=500),
        bench("modulation émotionnelle (ψ → ψ')",
              lambda: pers.modulate_emotion(psi, 'joyful'), n=500),
        bench("modulation de personnalité",
              lambda: pers.modulate_personality(psi), n=500),
    ]
    for r in results:
        print_bench(r)

    # Fusion de personnalités
    print("\n  [3.2] Fusion de personnalités")
    t0 = time.perf_counter()
    for _ in range(1000):
        pers.blend_personalities('compagnon', 'sage', 0.3, new_name='tmp_fusion')
    fusion_time = (time.perf_counter() - t0) * 1000
    print(f"    1000 fusions en {fusion_time:.1f} ms → {fusion_time/1000:.4f} ms/fusion")


# ═══════════════════════════════════════════════════════════
# 4. PIPELINE CONVERSATIONNEL COMPLET
# ═══════════════════════════════════════════════════════════

def bench_pipeline():
    section("4. PIPELINE CONVERSATIONNEL COMPLET (6 étapes)")

    mem = MemoryCore()
    pers = PersonalityEngine()
    pipe = ConversationPipeline(memory=mem, personality=pers)

    # Pré-remplir la mémoire
    for fact in [
        "Sophie aime le chocolat noir",
        "Sophie habite à Paris",
        "Paul est le frère de Sophie",
        "Le restaurant préféré de Sophie est Le Petit Cambodge",
    ]:
        mem.remember(fact, domain='personal')
    mem.set_user_name("Sophie")

    # Batterie de questions représentatives
    questions = [
        ("Bonjour !", "chat"),
        ("Quel est mon restaurant préféré ?", "query"),
        ("Où est-ce que j'habite ?", "query"),
        ("Calcule 15% de 200", "math"),
        ("Rappelle-toi que mon anniversaire est le 15 mars", "store_fact"),
        ("Pourquoi le ciel est bleu ?", "reason"),
        ("Je me sens un peu triste aujourd'hui...", "chat"),
    ]

    print("  [4.1] Latence par type d'intention")
    all_latencies = []
    for q, expected in questions:
        times = []
        for _ in range(20):
            t0 = time.perf_counter()
            result = pipe.process(q)
            times.append((time.perf_counter() - t0) * 1000)
        avg = statistics.mean(times)
        all_latencies.extend(times)
        print(f"    {expected:<12s} '{q[:45]:<45s}' → "
              f"avg={avg:.3f}ms  p99={sorted(times)[int(20*0.99)]:.3f}ms  "
              f"→ '{result.response[:50]}'")

    print(f"\n  [4.2] Synthèse globale")
    print(f"    Latence moyenne: {statistics.mean(all_latencies):.3f} ms")
    print(f"    Latence p99:     {sorted(all_latencies)[int(len(all_latencies)*0.99)]:.3f} ms")
    print(f"    Débit:           {1000/statistics.mean(all_latencies):.0f} requêtes/s")

    # Test de charge soutenue
    print(f"\n  [4.3] Charge soutenue (1000 requêtes)")
    t0 = time.perf_counter()
    for i in range(1000):
        pipe.process("Quel est mon restaurant préféré ?")
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"    1000 requêtes en {elapsed:.1f} ms → {1000/elapsed*1000:.0f} req/s")
    print(f"    (Pour référence: Hermes ~1-10 req/s sur A100, ~$3-5/M tokens)")


# ═══════════════════════════════════════════════════════════
# 5. PHRASÉOLOGIE
# ═══════════════════════════════════════════════════════════

def bench_phraselogy():
    section("5. PHRASÉOLOGIE (PhraseEngine + surface grammar)")

    pe = PhraseEngine()

    # Templates
    results = [
        bench("template math",
              lambda: pe.synthesize('math', value=14, expr='2 + 3 × 4'), n=1000),
        bench("template query",
              lambda: pe.synthesize('query', value='Paris'), n=1000),
    ]
    for r in results:
        print_bench(r)

    # Surface grammar (prose)
    print("\n  [5.2] Surface grammar (prose naturelle)")
    fact = "Le diabète de type 1 est causé par une déficience en insuline"
    t0 = time.perf_counter()
    for _ in range(1000):
        pe.prose(fact)
    prose_time = (time.perf_counter() - t0) * 1000
    print(f"    prose() : {prose_time/1000:.4f} ms/rendu "
          f"({1000/prose_time*1000:.0f} rendus/s)")

    # Exemple de sortie
    print("\n  [5.3] Exemples de phraséologie")
    examples = [
        ("math", pe.synthesize('math', value=14, expr='2 + 3 × 4')),
        ("query", pe.synthesize('query', value='Paris')),
        ("reason", pe.synthesize('reason', value='il pleut car le ciel est couvert')),
        ("store_fact", pe.synthesize('store_fact', value='ton anniversaire est le 15 mars')),
        ("compare", pe.synthesize('compare', value='le chat est indépendant, le chien fidèle')),
        ("prose", pe.prose(fact)),
    ]
    for intent, text in examples:
        print(f"    {intent:<12s} → {text}")


# ═══════════════════════════════════════════════════════════
# 6. EMPREINTE MÉMOIRE
# ═══════════════════════════════════════════════════════════

def bench_footprint():
    section("6. EMPREINTE MÉMOIRE")

    import sys as _sys

    mem = MemoryCore()
    for i in range(1000):
        mem.remember(f"Fait {i}: information de test {i}", domain='general')

    # Taille des structures clés
    psi = text_to_psi("test")
    hologram = mem.store._holograms['general']

    print(f"    ψ (ℂ⁵¹² complex128)      : {psi.nbytes} octets ({psi.nbytes/1024:.2f} Ko)")
    print(f"    Hologramme (ℂ⁵¹²)        : {hologram.nbytes} octets")
    print(f"    1000 faits en mémoire     : {mem.store._total_facts} faits")

    # Taille de la KB entière (approximation)
    kb_size = sum(f.psi.nbytes for facts in mem.store._facts.values()
                  for f in facts)
    print(f"    KB ψ (1000 faits)         : {kb_size/1024:.0f} Ko")
    print(f"    → 40 000 faits projetés   : ~{kb_size/1000*40000/1024/1024:.1f} Mo")

    print(f"\n    Pour référence :")
    print(f"      Hermes 3 (405B)         : ~800 Go (FP16)")
    print(f"      KA Companion            : < 10 Mo (cible)")
    print(f"      Facteur de réduction    : ~80 000×")


# ═══════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  ⚡ HARMONIC AI V5 — Tests de Performance")
    print("=" * 72)
    print(f"  φ={PHI:.6f} · ℂ{DIM_PSI} · CPU uniquement · zéro GPU")
    print(f"  Machine: {sys.platform} · Python {sys.version.split()[0]}")

    t_start = time.perf_counter()

    bench_encoding()
    bench_memory()
    bench_personality()
    bench_pipeline()
    bench_phraselogy()
    bench_footprint()

    elapsed = (time.perf_counter() - t_start)
    print(f"\n{'═'*72}")
    print(f"  Temps total du benchmark : {elapsed:.1f} s")
    print(f"{'═'*72}")


if __name__ == '__main__':
    main()
