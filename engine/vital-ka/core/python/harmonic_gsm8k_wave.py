#!/usr/bin/env python3
"""
harmonic_gsm8k_wave.py — Solveur GSM8K natif via Langage Ondulatoire
=====================================================================

Architecture officielle (Document Fondateur §8, §9) :
1. WaveCodeGenerator détecte intention 'reason' → génère AST Wave IR
   ENCODE → QUERY → SUPERPOSE → EMERGE → DECODE
2. WaveCompiler optimise (4 passes) et exécute
3. HolographicMemory (wave_bridge) stocke faits numériques + vocabulaire
4. Détection d'opération par résonance (pas de règles if/else)

Ce module REMPLACE harmonic_gsm8k_kuramoto.py et word_problem_state.py
pour la partie "raisonnement harmonique pur".
"""

import sys
import os
import re
import numpy as np
from typing import Optional, List, Tuple, Dict, Any

# ─── Imports officiels (Document Fondateur §A.1) ──────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'core', 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'backend', 'hologram'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'backend', 'inference'))

# Modules officiels du langage ondulatoire
from wave_code_generator import WaveCodeGenerator, WaveIntentDetector
from wave_ir import parse, validate, to_json
from wave_compiler import WaveCompiler
from wave_bridge import HolographicMemory, encode, bind, superpose, resonate, emerge, decode, phase_shift, rotate, normalize
from wave_lang import encode as lang_encode, decode as lang_decode


class HarmonicGSM8KWaveSolver:
    """
    Solveur GSM8K par architecture officielle du Langage Ondulatoire.
    
    Pipeline :
    1. Détection intention 'reason' (tout GSM8K = raisonnement multi-étapes)
    2. Génération programme : ENCODE → QUERY → SUPERPOSE → EMERGE → DECODE
    3. HolographicMemory : faits numériques + vocabulaire opérations
    4. Compilation + exécution via WaveCompiler
    5. Décodage réponse numérique
    """
    
    def __init__(self, dim: int = 512):
        self.dim = dim
        self.compiler = WaveCompiler(dim=dim)
        self.generator = WaveCodeGenerator()
        self.detector = WaveIntentDetector()
        
        # Mémoire holographique unifiée (wave_bridge)
        self.memory = HolographicMemory(dim=dim)
        self._init_gsm8k_knowledge()
    
    def _init_gsm8k_knowledge(self):
        """Initialise la mémoire avec faits GSM8K : vocabulaire opérations + entités."""
        # Vocabulaire opérations arithmétiques (résonance pour détection)
        ops = [
            ("add", "signifie", "somme"),
            ("plus", "signifie", "addition"),
            ("more", "signifie", "addition"),
            ("total", "signifie", "addition"),
            ("altogether", "signifie", "addition"),
            ("sum", "signifie", "addition"),
            ("sub", "signifie", "difference"),
            ("less", "signifie", "soustraction"),
            ("fewer", "signifie", "soustraction"),
            ("left", "signifie", "soustraction"),
            ("remain", "signifie", "soustraction"),
            ("ate", "signifie", "soustraction"),
            ("gave", "signifie", "soustraction"),
            ("mul", "signifie", "multiplication"),
            ("times", "signifie", "multiplication"),
            ("each", "signifie", "multiplication"),
            ("per", "signifie", "multiplication"),
            ("product", "signifie", "multiplication"),
            ("div", "signifie", "division"),
            ("shared", "signifie", "division"),
            ("percent", "signifie", "pourcentage"),
            ("%", "signifie", "pourcentage"),
            ("of", "signifie", "multiplication"),  # "20% of 150" = mul
        ]
        for s, r, o in ops:
            self.memory.store(lang_encode(s), lang_encode(r), lang_encode(o))
        
        # Entités GSM8K courantes (pour résonance)
        entities = [
            "person", "apple", "cookie", "box", "pencil", "dollar", "cent",
            "hour", "minute", "day", "week", "mile", "car", "speed",
            "area", "perimeter", "circle", "radius", "diameter",
            "dozen", "pair", "box", "pack", "bag",
        ]
        for e in entities:
            psi = lang_encode(e)
            self.memory.store(psi, psi, psi)  # auto-résonance pour reconnaissance
    
    def solve(self, question: str) -> Tuple[Optional[float], List[str]]:
        """
        Résout un problème GSM8K par approche harmonique native.
        
        Returns:
            (réponse numérique, étapes de raisonnement)
        """
        try:
            # 1. Détection intention (GSM8K → toujours 'reason')
            intent, confidence = self.detector.detect_wave_intent(question)
            if intent != "reason":
                intent = "reason"  # Forcer pour GSM8K
            
            # 2. Génération programme ondulatoire natif
            program = self.generator.generate(question, lang='en')
            
            # 3. Validation AST
            errors = validate(program)
            if errors:
                return None, [f"Validation errors: {errors}"]
            
            # 4. Exécution via WaveCompiler (pas d'hologramme externe requis pour calcul pur)
            # Le programme généré contient QUERY FROM H_connaissances
            # On fournit notre mémoire GSM8K comme H_connaissances
            env = self.compiler.execute(program, holograms={"H_connaissances": self.memory})
            
            # 5. Extraction réponse
            answer = self._extract_numeric_answer(env, question)
            
            steps = [
                f"Intent: {intent} (conf={confidence:.2f})",
                f"Program: {program.to_wave().replace('ψ', 'psi')}",
                f"Env keys: {list(env.keys())}",
            ]
            
            if answer is not None:
                steps.append(f"→ ANSWER: {answer}")
                return answer, steps
            
            return None, steps + ["Aucune réponse numérique extraite"]
            
        except Exception as e:
            return None, [f"Error: {e}"]
    
    def _extract_numeric_answer(self, env: Dict, question: str) -> Optional[float]:
        """Extrait la réponse numérique de l'environnement d'exécution."""
        # Chercher variable retournée (généralement 'reponse' ou 'resultat' ou 'answer')
        for key in ['reponse', 'resultat', 'answer', 'result', 'output']:
            if key in env:
                val = env[key]
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, np.ndarray):
                    return self._decode_numeric_array(val)
        
        # Fallback : prendre la première valeur numérique non-triviale
        for key, val in env.items():
            if isinstance(val, (int, float)) and abs(val) > 1e-6:
                return float(val)
            if isinstance(val, np.ndarray) and val.ndim == 1:
                decoded = self._decode_numeric_array(val)
                if decoded is not None:
                    return decoded
        
        return None
    
    def _decode_numeric_array(self, psi: np.ndarray) -> Optional[float]:
        """Décode un vecteur d'onde vers valeur numérique par résonance avec vocabulaire 0-100."""
        # Vocabulaire numérique pré-codé
        best_score = -1
        best_val = None
        for n in range(0, 1001):
            psi_n = lang_encode(str(n))
            score = float(np.real(np.vdot(psi_n, psi)))
            if score > best_score:
                best_score = score
                best_val = n
        return float(best_val) if best_score > 0.1 else None


# ─── Point d'entrée simple ────────────────────────────────────────────────────

def solve_gsm8k_wave(question: str) -> Tuple[Optional[float], List[str]]:
    """Point d'entrée pour benchmark."""
    solver = HarmonicGSM8KWaveSolver()
    return solver.solve(question)


# ─── Auto-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("HARMONIC GSM8K WAVE SOLVER — Architecture Officielle")
    print("=" * 60)
    
    test_cases = [
        ("John has 5 apples. He buys 3 more. How many apples does John have?", 8),
        ("Mary had 10 cookies. She ate 4. How many cookies does Mary have left?", 6),
        ("John has 5 apples. He gives 2 to Mary. How many apples does John have?", 3),
        ("There are 6 boxes. Each box has 5 pencils. How many pencils in total?", 30),
        ("A car drives at 60 mph for 2 hours. How far does it go?", 120),
        ("What is 20% of 150?", 30),
        ("100 dollars with 20% off. What is the final price?", 80),
    ]
    
    for q, expected in test_cases:
        answer, steps = solve_gsm8k_wave(q)
        status = "OK" if answer == expected else "KO"
        print(f"\n{status} Q: {q[:65]}...")
        print(f"     Expected: {expected}, Got: {answer}")
        for s in steps[-3:]:
            print(f"     {s}")