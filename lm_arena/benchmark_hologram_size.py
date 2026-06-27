#!/usr/bin/env python3
"""
Hologram Size Benchmark — Find the maximum viable grid size
=============================================================
Tests encoding/reading speeds for N×N grids from 64 to 16K.
Reports the largest size that stays under 1ms per operation.

Usage: python benchmark_hologram_size.py
"""

import numpy as np
import time
import math
import sys, os

PHI = 1.618033988749895

def benchmark_size(n: int, n_tokens: int = 500, n_reads: int = 100):
    """Benchmark encode + read for an N×N hologram."""
    # Create hologram
    t0 = time.time()
    H = np.zeros((n, n), dtype=np.complex128) + 1j * np.random.randn(n, n) * 0.01
    x = np.linspace(-math.pi, math.pi, n)
    y = np.linspace(-math.pi, math.pi, n)
    xx, yy = np.meshgrid(x, y, indexing='ij')
    mem_mb = H.nbytes / (1024 * 1024)
    
    # Encode random tokens
    t1 = time.time()
    for i in range(n_tokens):
        kx = PHI * (1 + i * 0.05)
        ky = 1.0 / PHI * (1 + i * 0.03)
        onde = np.exp(1j * (kx * xx + ky * yy))
        H += 1.5 * onde
    t2 = time.time()
    encode_ms = (t2 - t1) * 1000 / n_tokens
    
    # Read random tokens
    t3 = time.time()
    for i in range(n_reads):
        kx = PHI * (1 + i * 0.05)
        ky = 1.0 / PHI * (1 + i * 0.03)
        onde_ref = np.exp(-1j * (kx * xx + ky * yy))
        corr = np.abs(np.sum(H * onde_ref)) / (n * n)
    t4 = time.time()
    read_ms = (t4 - t3) * 1000 / n_reads
    
    return {
        "n": n, "pixels": n*n, "mem_mb": round(mem_mb, 1),
        "encode_ms": round(encode_ms, 3),
        "read_ms": round(read_ms, 3),
        "total_ms": round(encode_ms + read_ms, 3),
    }

def run_benchmark():
    sizes = [64, 128, 256, 512, 1024, 2048, 4096, 8192]
    results = []
    
    print("=" * 65)
    print("  HOLOGRAM SIZE BENCHMARK")
    print("=" * 65)
    print(f"  {'Size':>5s}  {'Pixels':>10s}  {'Memory':>8s}  {'Encode':>8s}  {'Read':>8s}  {'Total':>8s}  {'Status':>10s}")
    print(f"  {'-'*5}  {'-'*10}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*10}")
    
    for n in sizes:
        try:
            r = benchmark_size(n)
            viable = r["total_ms"] < 1.0 and r["mem_mb"] < 4000  # < 1ms and < 4GB
            status = "OK" if viable else ("SLOW" if r["total_ms"] < 10 else "HEAVY")
            
            print(f"  {r['n']:5d}  {r['pixels']:>10,d}  {r['mem_mb']:>7.1f}MB  {r['encode_ms']:>7.3f}ms  {r['read_ms']:>7.3f}ms  {r['total_ms']:>7.3f}ms  {status:>10s}")
            results.append(r)
        except MemoryError:
            print(f"  {n:5d}  {'N/A':>10s}  {'N/A':>8s}  MEMORY ERROR")
            break
        except Exception as e:
            print(f"  {n:5d}  {'N/A':>10s}  {'N/A':>8s}  ERROR: {e}")
            break
    
    # Find the best size
    viable = [r for r in results if r["total_ms"] < 1.0]
    if viable:
        best = max(viable, key=lambda r: r["n"])
        print(f"\n  RECOMMENDED: {best['n']}x{best['n']} ({best['pixels']:,} pixels, {best['mem_mb']} MB, {best['total_ms']}ms/op)")
    else:
        # Find the fastest
        fastest = min(results, key=lambda r: r["total_ms"])
        print(f"\n  FASTEST: {fastest['n']}x{fastest['n']} ({fastest['pixels']:,} pixels, {fastest['mem_mb']} MB, {fastest['total_ms']}ms/op)")
    
    print(f"\n  Note: 1Mx1M = 1,000,000,000,000 pixels would require ~16 TB of RAM.")
    print(f"  Even 16Kx16K = 268M pixels requires ~4 GB — feasible on high-end machines.")
    
    return results

if __name__ == "__main__":
    run_benchmark()