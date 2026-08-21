#!/usr/bin/env python3
"""
wave_gsm8k_solver.py — Solveur GSM8K natif ondulatoire (version complète)
=======================================================================

Utilise WaveGSM8KGenerator + WaveCompiler pour résoudre les problèmes GSM8K
par calcul harmonique pur (pas de QUERY hologramme).
"""

import sys
import os
import numpy as np
from typing import Optional, Tuple, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'core', 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'backend', 'hologram'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'backend', 'inference'))

from wave_gsm8k_generator import WaveGSM8KGenerator
from wave_ir import parse, validate
from wave_compiler import WaveCompiler
from wave_lang import HolographicMemory, encode, decode as wave_decode


class WaveGSM8KSolver:
    """
    Solveur GSM8K par approche harmonique native.
    
    Pipeline :
    1. WaveGSM8KGenerator génère programme ENCODE → OP → EMERGE → DECODE
    2. Compiler exécute le programme (pas d'hologramme requis pour calcul pur)
    3. Extraire le nombre depuis le résultat DECODE
    """

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.compiler = WaveCompiler(dim=dim)
        self.generator = WaveGSM8KGenerator(dim=dim)

    def solve(self, question: str) -> Optional[float]:
        """Résout un problème GSM8K, retourne le résultat numérique."""
        try:
            # 1. Générer programme ondulatoire
            program = self.generator.generate(question)
            
            # 2. Valider
            errors = validate(program)
            if errors:
                return None
            
            # 3. Compiler et exécuter
            # Pour calcul pur (pas de QUERY), pas besoin d'hologramme
            env = self.compiler.execute(program)
            
            # 4. Extraire la réponse
            return self._extract_answer(env)
            
        except Exception:
            return None

    def solve_with_steps(self, question: str) -> Optional[Tuple[float, List[str]]]:
        """Résout avec les étapes de raisonnement."""
        try:
            program = self.generator.generate(question)
            errors = validate(program)
            if errors:
                return None, [f"Validation errors: {errors}"]
            
            env = self.compiler.execute(program)
            steps = [f"Program: {program.to_wave().replace(chr(0x03c8), 'psi')}"]
            
            for var_name, value in env.items():
                steps.append(f"{var_name} = {value}")
            
            answer = self._extract_answer(env)
            if answer is not None:
                steps.append(f"→ ANSWER: {answer}")
                return answer, steps
            
            return None, steps
            
        except Exception as e:
            return None, [f"Error: {e}"]

    def _extract_answer(self, env: dict) -> Optional[float]:
        """Extrait la réponse numérique de l'environnement d'exécution."""
        # La variable 'answer' contient le résultat du DECODE
        # DECODE retourne un vecteur de similarités avec le vocabulaire
        # Le max correspond au nombre décodé
        
        if 'answer' in env:
            val = env['answer']
            if isinstance(val, np.ndarray):
                # Vecteur de similarités → argmax = index dans vocabulaire
                idx = int(np.argmax(val))
                return float(idx)
            elif isinstance(val, (int, float)):
                return float(val)
            elif isinstance(val, list) and val:
                return float(val[0])
        
        # Fallback : chercher toute variable numérique
        for var_name, value in env.items():
            if isinstance(value, (int, float)) and value > 0:
                return float(value)
            if isinstance(value, np.ndarray) and value.ndim == 1:
                idx = int(np.argmax(value))
                if 0 <= idx <= 10000:
                    return float(idx)
        
        return None


def solve_gsm8k_wave(question: str) -> Optional[float]:
    """Point d'entrée simple pour le benchmark."""
    solver = WaveGSM8KSolver()
    return solver.solve(question)


def solve_gsm8k_wave_with_steps(question: str) -> Optional[Tuple[float, List[str]]]:
    """Point d'entrée avec étapes."""
    solver = WaveGSM8KSolver()
    return solver.solve_with_steps(question)


if __name__ == "__main__":
    # Auto-test
    test_questions = [
        ("John has 5 apples. He buys 3 more. How many apples does he have?", 8.0),
        ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6.0),
        ("There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?", 30.0),
        ("A car drives at 60 mph for 2 hours. How far does it go?", 120.0),
        ("What is 20% of 150?", 30.0),
        ("100 dollars with 20% off. What is the final price?", 80.0),
        ("A rectangle has width 5 and height 10. What is the area?", 50.0),
    ]
    
    print("=" * 60)
    print("WAVE GSM8K SOLVER - AUTO-TEST")
    print("=" * 60)
    
    ok = 0
    for q, exp in test_questions:
        result, steps = solve_gsm8k_wave_with_steps(q)
        good = result is not None and abs(result - exp) < 1.0
        ok += good
        status = "OK" if good else "KO"
        print(f"{status} Q: {q[:65]}")
        print(f"     → Got: {result}, Expected: {exp}")
        if not good and steps:
            print(f"     Steps: {steps[-3:]}")
        print()
    
    print(f"Score: {ok}/{len(test_questions)}")