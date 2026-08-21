#!/usr/bin/env python3
"""
harmonic_gsm8k_generator.py — Générateur GSM8K spécialisé pour Langage Ondulatoire
==================================================================================

Génère des programmes ondulatoires de CALCUL (pas QA) pour GSM8K :
ENCODE(n1) → ENCODE(n2) → OPÉRATION_HARMONIQUE → EMERGE → DECODE(vocab_numerique)

Opérations harmoniques :
- ADD : superpose(ψ_n1, ψ_n2) + phase_shift pour retenues
- SUB : interfere(ψ_n1, ψ_n2, ε=-1) 
- MUL : bind(ψ_n1, ψ_n2) → décalage harmonique (positionnel)
- DIV : unbind / résonance inverse
- PCT : mul + div par 100
"""

import sys
import os
import re
import numpy as np
from typing import List, Tuple, Optional, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'core', 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'backend', 'hologram'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'backend', 'inference'))

from wave_ir import Program, Assign, Encode, Decode, Return, Var, Bind, Superpose, Emerge, Interfere, Oppose, BindMany, PhaseShift, Resonance, Literal, Unbind
from wave_code_generator import WaveCodeGenerator, WaveIntentDetector
from wave_lang import encode as lang_encode, decode as lang_decode


class WaveGSM8KGenerator(WaveCodeGenerator):
    """
    Générateur de programmes ondulatoires pour problèmes GSM8K.
    
    Pattern GSM8K 'reason' → calcul harmonique :
    1. Extraire nombres et opération de la question
    2. ENCODE chaque nombre → ψ_n
    3. Appliquer opération harmonique (ADD/SUB/MUL/DIV/PCT)
    4. EMERGE pour consolidation
    5. DECODE vers vocabulaire numérique (0-10000)
    """
    
    # Vocabulaire numérique pour DECODE final
    NUMERIC_VOCAB_MAX = 10000
    
    # Patterns de détection d'opération (ordre = priorité)
    OP_PATTERNS = [
        # Pourcentage
        (r'\b(?:percent|%)\b.*\bof\b', 'pct_of'),
        (r'\b(?:percent|%)\s*(?:off|discount|sale)', 'pct_off'),
        (r'\b(?:plus|with)\s+\d+\s*(?:percent|%)\s*(?:tax|tip)', 'pct_add'),
        
        # Multiplication
        (r'\beach\b.*\b(?:has|have|costs?)\b', 'mul_each'),
        (r'\btimes\b|\btwice\b|\bdouble\b|\btriple\b', 'mul'),
        (r'\barea\b|\bperimeter\b|\bcircumference\b', 'geometry'),
        
        # Division
        (r'\bshared\s+(?:equally|among)\b', 'div_share'),
        (r'\bper\b', 'div_per'),
        
        # Soustraction
        (r'\b(?:left|remain|fewer|less|ate|gave|spent|used)\b', 'sub'),
        
        # Addition (défaut)
        (r'\b(?:more|plus|add|total|altogether|sum|in all|together)\b', 'add'),
    ]
    
    def __init__(self, dim: int = 512):
        super().__init__()
        self.dim = dim
        self.detector = WaveIntentDetector()
    
    def generate_gsm8k(self, question: str) -> 'Program':
        """
        Génère un programme de CALCUL harmonique pour GSM8K.
        """
        # 1. Extraire nombres
        numbers = self._extract_numbers(question)
        if len(numbers) < 2:
            # Fallback : générateur standard
            return super().generate(question, lang='en')
        
        # 2. Détecter opération
        op_type, op_params = self._detect_operation(question, numbers)
        
        # 3. Construire programme selon opération
        return self._build_program(numbers, op_type, op_params, question)
    
    def _extract_numbers(self, question: str) -> List[float]:
        """Extrait tous les nombres de la question."""
        nums = []
        # Entiers et décimaux
        for m in re.finditer(r'\b\d+(?:[.,]\d+)?\b', question):
            val = float(m.group(0).replace(',', '.'))
            nums.append(val)
        # Fractions textuelles
        frac_map = {'half': 0.5, 'one-third': 1/3, 'two-thirds': 2/3, 'quarter': 0.25, 'three-quarters': 0.75}
        for word, val in frac_map.items():
            if word in question.lower():
                nums.append(val)
        return nums
    
    def _detect_operation(self, question: str, numbers: List[float]) -> Tuple[str, Dict]:
        """Détecte le type d'opération et paramètres."""
        q = question.lower()
        
        for pattern, op_type in self.OP_PATTERNS:
            if re.search(pattern, q):
                return op_type, {'numbers': numbers}
        
        return 'add', {'numbers': numbers}  # défaut
    
    def _build_program(self, numbers: List[float], op_type: str, params: Dict, question: str) -> 'Program':
        """Construit le programme harmonique selon l'opération."""
        stmts = []
        
        # 0. Constante 1.0 pour opérations de pourcentage
        stmts.append(Assign(name='psi_one', value=Encode(text='1.0')))
        
        # 1. ENCODE chaque nombre
        psi_vars = []
        for i, n in enumerate(numbers[:4]):  # max 4 nombres
            var_name = f'psi_n{i}'
            stmts.append(Assign(name=var_name, value=Encode(text=str(n))))
            psi_vars.append(var_name)
        
        # 2. Appliquer opération harmonique
        result_var = self._apply_operation(stmts, psi_vars, op_type, params, numbers)
        
        # 3. EMERGE pour consolidation
        stmts.append(Assign(name='psi_final', value=Emerge(psis=[Var(name=result_var)], temperature=0.5)))
        
        # 4. DECODE vers vocabulaire numérique
        # Créer référence vocabulaire numérique
        vocab_text = ' '.join(str(i) for i in range(0, min(1001, self.NUMERIC_VOCAB_MAX + 1)))
        stmts.append(Assign(name='psi_numvocab', value=Encode(text=vocab_text)))
        stmts.append(Assign(name='answer', value=Decode(psi=Var(name='psi_final'), top_k=1)))
        
        # 5. RETURN
        stmts.append(Return(value=Var(name='answer')))
        
        return Program(stmts)
    
    def _apply_operation(self, stmts: List, psi_vars: List[str], op_type: str, params: Dict, numbers: List[float]) -> str:
        """Ajoute les statements pour l'opération harmonique, retourne nom variable résultat."""
        if len(psi_vars) < 2:
            return psi_vars[0] if psi_vars else 'psi_n0'
        
        a, b = psi_vars[0], psi_vars[1]
        
        if op_type in ('add', 'mul_each'):
            # Addition : SUPERPOSE + retenues gérées par EMERGE
            stmts.append(Assign(name='psi_sum', value=Superpose(psis=[Var(name=a), Var(name=b)])))
            return 'psi_sum'
        
        elif op_type == 'sub':
            # Soustraction : INTERFERE destructif (ε = -1)
            stmts.append(Assign(name='psi_diff', value=Interfere(base=Var(name=a), other=Var(name=b), epsilon=-1.0)))
            return 'psi_diff'
        
        elif op_type == 'mul':
            # Multiplication : BIND (produit tensoriel → décalage harmonique)
            stmts.append(Assign(name='psi_prod', value=Bind(left=Var(name=a), right=Var(name=b))))
            return 'psi_prod'
        
        elif op_type == 'div_share' or op_type == 'div_per':
            # Division : UNBIND / Résonance inverse
            stmts.append(Assign(name='psi_quot', value=Unbind(left=Var(name=a), right=Var(name=b))))
            return 'psi_quot'
        
        elif op_type == 'pct_of':
            # "X% of Y" = X/100 * Y
            # psi_pct = PhaseShift(psi_X, shift=-2π*2) ≈ division par 100
            # psi_result = Bind(psi_pct, psi_Y)
            stmts.append(Assign(name='psi_pct', value=PhaseShift(psi=Var(name=a), shift=-2 * 3.14159265359 * 2)))
            stmts.append(Assign(name='psi_result', value=Bind(left=Var(name='psi_pct'), right=Var(name=b))))
            return 'psi_result'
        
        elif op_type == 'pct_off':
            # "X with Y% off" = X * (1 - Y/100)
            stmts.append(Assign(name='psi_pct', value=PhaseShift(psi=Var(name=b), shift=-2 * 3.14159265359 * 2)))
            stmts.append(Assign(name='psi_one_minus_pct', value=Interfere(base=Var(name='psi_one'), other=Var(name='psi_pct'), epsilon=-1.0)))
            stmts.append(Assign(name='psi_result', value=Bind(left=Var(name=a), right=Var(name='psi_one_minus_pct'))))
            return 'psi_result'
        
        elif op_type == 'geometry':
            # Géométrie simplifiée : déléguer à calcul symbolique
            # Pour l'instant : multiplication pour aire
            stmts.append(Assign(name='psi_prod', value=Bind(left=Var(name=a), right=Var(name=b))))
            return 'psi_prod'
        
        else:
            # Défaut : addition
            stmts.append(Assign(name='psi_sum', value=Superpose(psis=[Var(name=a), Var(name=b)])))
            return 'psi_sum'
    
    def generate(self, question: str, lang: str = 'en') -> 'Program':
        """Point d'entrée : détecte GSM8K et génère programme approprié."""
        if self._is_gsm8k(question):
            return self.generate_gsm8k(question)
        else:
            return super().generate(question, lang=lang)
    
    def _is_gsm8k(self, question: str) -> bool:
        """Heuristique pour détecter problème style GSM8K."""
        q = question.lower()
        indicators = [
            r'\bhow many\b', r'\bhow much\b', r'\bhow old\b', r'\bhow far\b',
            r'\btotal\b', r'\bprofit\b', r'\bcost\b', r'\bprice\b',
            r'\bper\b', r'\beach\b', r'\btimes\b', r'\bpercent\b', r'\%',
            r'\bdollar\b', r'\bcent\b', r'\bhour\b', r'\bminute\b',
            r'\bday\b', r'\bweek\b', r'\bmonth\b', r'\byear\b',
        ]
        score = sum(1 for pat in indicators if re.search(pat, q))
        return score >= 1


def generate_gsm8k_program(question: str) -> 'Program':
    """Fonction utilitaire."""
    gen = WaveGSM8KGenerator()
    return gen.generate(question)


if __name__ == "__main__":
    print("=" * 60)
    print("WAVE GSM8K GENERATOR — TEST")
    print("=" * 60)
    
    test_questions = [
        "John has 5 apples. He buys 3 more. How many apples does John have?",
        "Mary had 10 cookies. She ate 4. How many cookies does Mary have left?",
        "There are 6 boxes. Each box has 5 pencils. How many pencils in total?",
        "A car drives at 60 mph for 2 hours. How far does it go?",
        "What is 20% of 150?",
        "100 dollars with 20% off. What is the final price?",
    ]
    
    gen = WaveGSM8KGenerator()
    
    for q in test_questions:
        print(f"\nQ: {q}")
        prog = gen.generate(q)
        print(f"  Program: {prog.to_wave().replace('ψ', 'psi')[:200]}...")