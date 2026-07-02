"""
Engines — Moteurs Ondulatoires Harmoniques
============================================
Quatre moteurs unifiés par le même principe : tout est onde.

Chaque moteur est indépendant mais partage le noyau ondulatoire commun :
  - Noyau ABC (mémoire non-locale à l'ordre 1/φ)
  - HRR holographique (binding par convolution circulaire)
  - SpectralEmbedding (phases S¹ par Laplacian Eigenmaps)
  - Convergence vers un point fixe stable

Les quatre moteurs :
  arithmetic  — Calcul émergent (Ψ_a·Ψ_b = Ψ_{a+b})
  benchmark   — Métriques de performance vs LLM/CPU/GPU
  quantum     — Simulation quantique par interférence d'ondes
  folding     — Repliement protéique par point fixe spectral

Usage :
  from engines import arithmetic, benchmark, quantum, folding
  
  # Calcul
  result = arithmetic.ArithmeticEngine().compute("3 + 4")
  
  # Simulation quantique
  qe = quantum.QuantumEngine(n_qubits=8)
  qe.run_grover(target=42)
  
  # Repliement
  fe = folding.FoldingEngine(grid_size=32)
  structure, energies = fe.fold("MVLSPAD...")
"""

from pathlib import Path
import sys

# Rendre les sous-moteurs importables
_ENGINES_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINES_DIR))
sys.path.insert(0, str(_ENGINES_DIR / '..' / 'engine'))  # accès au noyau commun

from . import arithmetic
from . import benchmark
from . import quantum
from . import folding

__all__ = ['arithmetic', 'benchmark', 'quantum', 'folding']


def run_all_engines():
    """Exécute les 4 moteurs et affiche un rapport."""
    print("=" * 65)
    print("║        ENGINES — Moteurs Ondulatoires Harmoniques        ║")
    print("=" * 65)
    
    # 1. Arithmetic
    print("\n  [ARITHMETIC]")
    engine = arithmetic.ArithmeticEngine()
    for expr in ["3 + 4", "7 - 2", "6 × 8", "2^5"]:
        try:
            r = engine.compute(expr)
            print(f"    {expr:12s} → {r}")
        except Exception as e:
            print(f"    {expr:12s} → {e}")
    
    # 2. Benchmark
    print("\n  [BENCHMARK]")
    engine2 = benchmark.BenchmarkEngine()
    engine2.report()
    
    # 3. Quantum
    print("\n  [QUANTUM]")
    qe = quantum.QuantumEngine(n_qubits=6)
    t0 = __import__('time').time()
    result = qe.run_grover(target=21, iterations=5)
    dt = __import__('time').time() - t0
    print(f"    Grover 6 qubits → {result} (cible=21) en {dt*1000:.1f} ms")
    
    # 4. Folding
    print("\n  [FOLDING]")
    fe = folding.FoldingEngine(grid_size=16)
    structure, energies = fe.fold("MVLSPA", max_iter=20)
    print(f"    Repliement 6 AA → {len(energies)} itérations, énergie finale={energies[-1]:.2f}")


if __name__ == '__main__':
    run_all_engines()
