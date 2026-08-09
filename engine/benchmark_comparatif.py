#!/usr/bin/env python3
"""
benchmark_comparatif.py - Comparaison systematique des 3 approches
===================================================================
1. Pipeline heuristique (raisonneur_ondulatoire)
2. k-NN structurel (structure_retrieval)
3. T5 fine-tune (train_t5_gsm8k)

Sur le MEME split train/test (1101/200) pour une comparaison equitable.
"""

import sys, os, re, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_test_data():
    """Charge le test set depuis le split de structure_retrieval."""
    from structure_retrieval import StructuredRetrieval
    from structure_ondulatoire import StructuredSolver

    # Construire le split
    sr = StructuredRetrieval()
    sr.split_and_index()

    return sr._test_problems, sr


def benchmark_heuristic(test_problems):
    """Pipeline heuristique (raisonneur_ondulatoire)."""
    from raisonneur_ondulatoire import solve_gsm8k, OndulatoireReasoner

    correct, no_sol, total = 0, 0, len(test_problems)
    times = []

    print(f"1. PIPELINE HEURISTIQUE ({total} problemes)")
    for i, p in enumerate(test_problems):
        q = p.get('question', '')
        ans_str = p.get('answer', '')
        expected = None
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
        if m:
            expected = float(m.group(1))

        t0 = time.time()
        try:
            result = solve_gsm8k(q)
        except Exception:
            result = None
        dt = (time.time() - t0) * 1000
        times.append(dt)

        if result is None:
            no_sol += 1
        elif expected is not None and abs(result - expected) < 1e-6:
            correct += 1

        if (i + 1) % 50 == 0:
            print(f"  {i+1:>4d}/{total} - {correct}/{i+1} "
                  f"({100*correct/(i+1):.1f}%)")

    acc = 100 * correct / total if total > 0 else 0
    avg_ms = np.mean(times) if times else 0
    print(f"  -> Accuracy: {acc:.1f}% ({correct}/{total}), "
          f"Sans sol: {no_sol}, Temps: {avg_ms:.1f} ms\n")
    return {'name': 'Heuristique', 'accuracy': acc, 'correct': correct,
            'total': total, 'no_solution': no_sol, 'avg_ms': avg_ms}


def benchmark_knn(test_problems, sr):
    """k-NN structurel avec adaptation semantique."""
    correct, no_sol, total = 0, 0, len(test_problems)
    times = []

    print(f"2. K-NN STRUCTUREL ({total} problemes)")
    for i, p in enumerate(test_problems):
        q = p.get('question', '')
        ans_str = p.get('answer', '')
        expected = None
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
        if m:
            expected = float(m.group(1))

        t0 = time.time()
        try:
            result = sr.solve(q, k=3, semantic=True)
        except Exception:
            result = None
        dt = (time.time() - t0) * 1000
        times.append(dt)

        if result is None:
            no_sol += 1
        elif expected is not None and abs(result - expected) < 1e-6:
            correct += 1

        if (i + 1) % 50 == 0:
            print(f"  {i+1:>4d}/{total} - {correct}/{i+1} "
                  f"({100*correct/(i+1):.1f}%)")

    acc = 100 * correct / total if total > 0 else 0
    avg_ms = np.mean(times) if times else 0
    print(f"  -> Accuracy: {acc:.1f}% ({correct}/{total}), "
          f"Sans sol: {no_sol}, Temps: {avg_ms:.1f} ms\n")
    return {'name': 'k-NN structurel', 'accuracy': acc, 'correct': correct,
            'total': total, 'no_solution': no_sol, 'avg_ms': avg_ms}


def benchmark_t5(test_problems, model_path="data/t5_gsm8k_model/final"):
    """Modele T5 fine-tune."""
    if not os.path.exists(os.path.join(model_path, 'adapter_model.safetensors')):
        if not os.path.exists(os.path.join(model_path, 'adapter_model.bin')):
            print(f"2. T5 FINE-TUNE - Modele non trouve dans {model_path}")
            return {'name': 'T5 fine-tune', 'accuracy': 0, 'correct': 0,
                    'total': 0, 'no_solution': 0, 'avg_ms': 0}

    from train_t5_gsm8k import load_trained_model, predict

    try:
        model, tokenizer = load_trained_model(model_path)
    except Exception as e:
        print(f"2. T5 FINE-TUNE - Erreur chargement: {e}")
        return {'name': 'T5 fine-tune', 'accuracy': 0, 'correct': 0,
                'total': 0, 'no_solution': 0, 'avg_ms': 0}

    correct, no_sol, total = 0, 0, len(test_problems)
    times = []

    print(f"3. T5 FINE-TUNE ({total} problemes)")
    for i, p in enumerate(test_problems):
        q = p.get('question', '')
        ans_str = p.get('answer', '')
        expected = None
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
        if m:
            expected = float(m.group(1))

        t0 = time.time()
        try:
            chain = predict(model, tokenizer, q)
            # Extraire le dernier resultat
            nums = re.findall(r'=\s*([\d.]+)', chain)
            result = float(nums[-1]) if nums else None
        except Exception:
            result = None
        dt = (time.time() - t0) * 1000
        times.append(dt)

        if result is None:
            no_sol += 1
        elif expected is not None and abs(result - expected) < 1e-6:
            correct += 1

        if (i + 1) % 50 == 0:
            print(f"  {i+1:>4d}/{total} - {correct}/{i+1} "
                  f"({100*correct/(i+1):.1f}%)")

    acc = 100 * correct / total if total > 0 else 0
    avg_ms = np.mean(times) if times else 0
    print(f"  -> Accuracy: {acc:.1f}% ({correct}/{total}), "
          f"Sans sol: {no_sol}, Temps: {avg_ms:.1f} ms\n")
    return {'name': 'T5 fine-tune', 'accuracy': acc, 'correct': correct,
            'total': total, 'no_solution': no_sol, 'avg_ms': avg_ms}


if __name__ == '__main__':
    print("=" * 60)
    print("BENCHMARK COMPARATIF GSM8K")
    print("=" * 60)
    print()

    # Charger le test set
    test_problems, sr = load_test_data()
    print(f"Test set: {len(test_problems)} problemes")
    print()

    # 1. Pipeline heuristique
    r1 = benchmark_heuristic(test_problems)

    # 2. k-NN structurel
    r2 = benchmark_knn(test_problems, sr)

    # 3. T5 (si disponible)
    r3 = benchmark_t5(test_problems)

    # Comparatif
    print("=" * 60)
    print("RESULTATS COMPARATIFS")
    print("=" * 60)
    print(f"{'Approche':<25s} {'Accuracy':>10s} {'Corrects':>10s} {'Sans sol':>10s} {'Temps':>10s}")
    print("-" * 65)
    for r in [r1, r2, r3]:
        if r['total'] > 0:
            print(f"{r['name']:<25s} {r['accuracy']:>8.1f}% {r['correct']:>7d}/{r['total']:<4d} "
                  f"{r['no_solution']:>7d} {r['avg_ms']:>7.1f} ms")
        else:
            print(f"{r['name']:<25s} {'N/A (non disponible)':>35s}")

    # Meilleure approche
    best = max([r for r in [r1, r2, r3] if r['total'] > 0],
               key=lambda x: x['accuracy'])
    print(f"\nMEILLEURE APPROCHE: {best['name']} ({best['accuracy']:.1f}%)")
