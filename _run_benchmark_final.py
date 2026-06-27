#!/usr/bin/env python3
"""Script temporaire pour exécuter le benchmark de compression et capturer l'erreur."""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Importer le module
from benchmark_context_compression import CompressionBenchmark
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

benchmark = CompressionBenchmark()

# Test 1: Ratio
print("=" * 70)
print("TEST 1 : RATIOS DE COMPRESSION PAR NIVEAU")
print("=" * 70)

test_levels = [
    (32000, 1, "32K (actuel)"),
    (64000, 3, "64K (phi2)"),
    (128000, 4, "128K (phi4) - PHASE 1"),
    (256000, 5, "256K (phi8)"),
    (512000, 6, "512K (phi16)"),
    (1000000, 7, "1M (phi31) - OBJECTIF"),
]

ratio_results = []
for size, level, name in test_levels:
    try:
        tokens = [1] * size
        result = benchmark.test_compression_ratio(tokens, level)
        ratio_results.append(result)
        status = "OK" if result["success"] else "FAIL"
        print(f"  {status} {name}: {result['actual_ratio']}x (theo {result['theoretical_ratio']}x) phi={result['phi_efficiency']:.2%} temps={result['processing_time_ms']:.0f}ms")
    except Exception as e:
        print(f"  FAIL {name}: ERREUR - {type(e).__name__}: {e}")
        traceback.print_exc()

# Test 2: Qualite
print()
print("=" * 70)
print("TEST 2 : QUALITE DE COMPRESSION")
print("=" * 70)

quality_results = []
for size, level, name in test_levels:
    try:
        tokens = [1] * size
        result = benchmark.test_compression_quality(tokens, level)
        quality_results.append(result)
        status = "OK" if result["success"] else "FAIL"
        print(f"  {status} {name}: score={result['quality_score']:.2%} chunks={result['all_chunks_valid']} hash={result['all_hashes_unique']} decomp={result['decompression_works']}")
    except Exception as e:
        print(f"  FAIL {name}: ERREUR - {type(e).__name__}: {e}")
        traceback.print_exc()

# Test 3: Pipeline
print()
print("=" * 70)
print("TEST 3 : PIPELINE 128K -> 32K")
print("=" * 70)

try:
    pipeline_result = benchmark.test_pipeline_128k_to_32k()
    status = "OK" if pipeline_result["success"] else "FAIL"
    print(f"  {status} 128K -> {pipeline_result['compressed_size']} tokens ({pipeline_result['compression_ratio']}x)")
    print(f"  Temps: {pipeline_result['pipeline_time_ms']}ms")
    print(f"  Tient dans 32K: {pipeline_result['fits_in_32k_context']}")
except Exception as e:
    print(f"  FAIL Pipeline: ERREUR - {type(e).__name__}: {e}")
    traceback.print_exc()

# Resume
print()
print("=" * 70)
print("RESUME FINAL")
print("=" * 70)
total = len(ratio_results) + len(quality_results) + (1 if 'pipeline_result' in dir() else 0)
passed = sum(1 for r in ratio_results if r["success"]) + sum(1 for r in quality_results if r["success"])
if 'pipeline_result' in dir() and pipeline_result["success"]:
    passed += 1
print(f"  Tests: {passed}/{total}")
print(f"  Statut: {'SUCCES' if passed == total else 'ECHEC'}")
print("=" * 70)
