#!/usr/bin/env python3
"""
KA-Next — BENCHMARK LM ARENA (Ensemble Holographique 7×64×64)
===============================================================
Évalue l'architecture multi-hologrammes sur un benchmark de
50 questions couvrant 5 catégories LM Arena.

Comparaison : Ensemble 7×64×64 vs Pipeline 1024×1024 vs QuickFacts seul.
"""

import sys, os, time, json, math
sys.path.insert(0, os.path.dirname(__file__))

PHI = (1 + math.sqrt(5)) / 2

BENCHMARK = [
    # ── GÉOGRAPHIE (10 questions) ──
    # (question, réponse_attendue, catégorie)
    ("Quelle est la capitale du Sénégal ?", "dakar", "geography"),
    ("Quelle est la capitale de l'Éthiopie ?", "addis-abeba", "geography"),
    ("Quelle est la capitale du Japon ?", "tokyo", "geography"),
    ("Quelle est la capitale de l'Égypte ?", "caire", "geography"),
    ("Quelle est la capitale du Brésil ?", "brasilia", "geography"),
    ("Quelle est la capitale du Ghana ?", "accra", "geography"),
    ("Quel est le plus long fleuve du monde ?", "nil", "geography"),
    ("Quel est le plus haut sommet du monde ?", "everest", "geography"),
    ("Combien de pays compte l'Afrique ?", "54", "geography"),
    ("Sur quel continent se situe la France ?", "europe", "geography"),

    # ── HISTOIRE (10 questions) ──
    ("Quand a débuté la Révolution française ?", "1789", "history"),
    ("En quelle année Christophe Colomb a-t-il atteint les Amériques ?", "1492", "history"),
    ("Qui a fondé l'Empire du Mali ?", "soundiata", "history"),
    ("En quelle année l'Éthiopie a-t-elle vaincu l'Italie à Adoua ?", "1896", "history"),
    ("Quel pays africain fut le premier indépendant en Afrique subsaharienne ?", "ghana", "history"),
    ("En quelle année la conférence de Berlin a-t-elle partagé l'Afrique ?", "1884", "history"),
    ("Combien de manuscrits compte Tombouctou environ ?", "700", "history"),
    ("Quelle civilisation est née dans la vallée du Nil vers -3150 ?", "égypte", "history"),
    ("Quel empire fut dirigé par Mansa Moussa ?", "mali", "history"),
    ("En quelle année la Seconde Guerre mondiale a-t-elle débuté ?", "1939", "history"),

    # ── SCIENCES (10 questions) ──
    ("Quelle est la vitesse de la lumière ?", "299", "science"),
    ("Qui a découvert l'ADN avec Crick en 1953 ?", "watson", "science"),
    ("Qui a publié la relativité générale en 1915 ?", "einstein", "science"),
    ("Qui a publié L'Origine des espèces en 1859 ?", "darwin", "science"),
    ("Quel est le solvant universel de la vie ?", "eau", "science"),
    ("Qui a introduit le quantum d'action h en 1900 ?", "planck", "science"),
    ("Combien d'éléments contient le tableau périodique ?", "118", "science"),
    ("Quel pourcentage de l'univers est constitué d'énergie noire ?", "68", "science"),
    ("Quel âge a la Terre ?", "4.54", "science"),
    ("Quelle théorie explique la dérive des continents ?", "tectonique", "science"),

    # ── PHILOSOPHIE & SAGESSES (10 questions) ──
    ("Qu'est-ce que le stoïcisme ?", "distinguer", "philosophy"),
    ("Qu'est-ce que l'Ubuntu ?", "je suis parce que nous sommes", "philosophy"),
    ("Qu'est-ce que la Maât ?", "ordre", "philosophy"),
    ("Qui a dit 'Je sais que je ne sais rien' ?", "socrate", "philosophy"),
    ("Qui a dit 'Je pense, donc je suis' ?", "descartes", "philosophy"),
    ("Qu'est-ce que les Lumières ?", "sapere aude", "philosophy"),
    ("Qui a dit 'Ne fais pas à autrui ce que tu ne voudrais pas qu'on te fasse' ?", "confucius", "philosophy"),
    ("Combien de lois compte la Maât ?", "42", "philosophy"),
    ("D'où vient le mot philosophie ?", "amour", "philosophy"),
    ("Qui a dit 'Ce qui ne me détruit pas me renforce' ?", "aurele", "philosophy"),

    # ── TECHNOLOGIE & IA (10 questions) ──
    ("Qui a défini le calcul universel en 1936 ?", "turing", "technology"),
    ("En quelle année le protocole TCP/IP a-t-il été créé ?", "1974", "technology"),
    ("Qui a inventé le Web en 1989 ?", "tim berners-lee", "technology"),
    ("Qui a créé le langage Python ?", "guido van rossum", "technology"),
    ("Qui a créé le langage JavaScript ?", "brendan eich", "technology"),
    ("En quelle année les transformers ont-ils été publiés ?", "2017", "technology"),
    ("Sur quoi repose le chiffrement RSA ?", "factoriser", "technology"),
    ("Qui a créé Git ?", "linus torvalds", "technology"),
    ("Qui a créé Linux ?", "linus torvalds", "technology"),
    ("Qu'est-ce que le DNS traduit ?", "nom", "technology"),
]


def run_benchmark_ka_next():
    """Benchmark via le moteur unifié KA-Next (ensemble + fallbacks)."""
    from ka_next_core import KANextEngine
    
    engine = KANextEngine()
    engine.build()
    
    print("=" * 70)
    print("  BENCHMARK LM ARENA — KA-Next (Ensemble 7×64×64)")
    print("=" * 70)
    
    results = {"correct": 0, "total": 0, "by_category": {}, "times": []}
    
    for question, expected, category in BENCHMARK:
        t0 = time.time()
        result = engine.query(question, mode="auto")
        dt = (time.time() - t0) * 1000
        
        text = result.get("text", "").lower()
        is_correct = expected.lower() in text
        source = result.get("source", "?")
        
        if is_correct:
            results["correct"] += 1
        results["total"] += 1
        results["times"].append(dt)
        
        if category not in results["by_category"]:
            results["by_category"][category] = {"correct": 0, "total": 0}
        results["by_category"][category]["total"] += 1
        if is_correct:
            results["by_category"][category]["correct"] += 1
        
        status = "OK" if is_correct else "KO"
        print(f"  [{status}] [{category:12s}] {question[:55]:55s} | {source:25s} | {dt:.0f}ms")
    
    return results


def run_benchmark_ensemble_only():
    """Benchmark via l'ensemble holographique seul."""
    from holographic_ensemble import HolographicEnsemble
    
    ensemble = HolographicEnsemble()
    ensemble.build_all(force_rebuild=False)
    
    print("\n" + "=" * 70)
    print("  BENCHMARK LM ARENA — Ensemble Holographique Seul")
    print("=" * 70)
    
    results = {"correct": 0, "total": 0, "by_category": {}, "times": []}
    
    for question, expected, category in BENCHMARK:
        t0 = time.time()
        result = ensemble.query(question, top_k_holos=3, facts_per_holo=5)
        dt = (time.time() - t0) * 1000
        
        text = result.get("text", "").lower()
        is_correct = expected.lower() in text
        
        if is_correct:
            results["correct"] += 1
        results["total"] += 1
        results["times"].append(dt)
        
        if category not in results["by_category"]:
            results["by_category"][category] = {"correct": 0, "total": 0}
        results["by_category"][category]["total"] += 1
        if is_correct:
            results["by_category"][category]["correct"] += 1
        
        status = "OK" if is_correct else "KO"
        domain_info = ""
        if result.get("domains_activated"):
            domains = [d["domain"] for d in result["domains_activated"] if d["resonance"] > 0.1]
            domain_info = "[" + ",".join(domains) + "]"
        print(f"  [{status}] [{category:12s}] {question[:55]:55s} | {domain_info:18s} | {dt:.0f}ms")
    
    return results


def print_summary(results, name):
    """Affiche le résumé du benchmark."""
    acc = results["correct"] / max(results["total"], 1) * 100
    avg_time = sum(results["times"]) / max(len(results["times"]), 1)
    elo = int(800 + acc * 5)
    
    print(f"\n{'=' * 70}")
    print(f"  RÉSULTATS — {name}")
    print(f"{'=' * 70}")
    print(f"  Total        : {results['correct']}/{results['total']} ({acc:.1f}%)")
    print(f"  ELO estimé   : ~{elo}")
    print(f"  Temps moyen  : {avg_time:.1f}ms")
    print(f"  Temps total  : {sum(results['times']):.0f}ms")
    print()
    
    for cat, data in sorted(results["by_category"].items()):
        cat_acc = data["correct"] / max(data["total"], 1) * 100
        bar = "█" * int(cat_acc / 5) + "░" * (20 - int(cat_acc / 5))
        print(f"  {cat:12s} [{bar}] {data['correct']}/{data['total']} ({cat_acc:.0f}%)")
    
    print(f"{'=' * 70}")
    
    return {"name": name, "accuracy": round(acc, 1), "elo": elo, 
            "avg_time_ms": round(avg_time, 1), "total": results["total"],
            "correct": results["correct"]}


if __name__ == "__main__":
    # Test 1 : Ensemble seul
    r1 = run_benchmark_ensemble_only()
    s1 = print_summary(r1, "Ensemble Holographique 7×64×64")
    
    # Test 2 : KA-Next complet (ensemble + QuickFacts + ParametricKB + fallback)
    r2 = run_benchmark_ka_next()
    s2 = print_summary(r2, "KA-Next Complet (Ensemble + QuickFacts + ParametricKB)")
    
    # Comparatif
    print(f"\n{'=' * 70}")
    print(f"  COMPARAISON")
    print(f"{'=' * 70}")
    print(f"  {'Moteur':40s} {'Précision':>10s} {'ELO':>8s} {'Temps':>8s}")
    print(f"  {'-'*60}")
    for s in [s1, s2]:
        print(f"  {s['name']:40s} {s['accuracy']:>8.1f}% {s['elo']:>6d}  {s['avg_time_ms']:>5.0f}ms")
    print(f"{'=' * 70}")