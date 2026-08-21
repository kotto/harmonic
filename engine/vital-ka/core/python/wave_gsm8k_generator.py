#!/usr/bin/env python3
"""
wave_gsm8k_generator.py — Générateur ondulatoire spécialisé GSM8K
=================================================================

Étend WaveCodeGenerator pour l'intention 'reason' avec pattern GSM8K :
- Extrait les nombres et l'opération implicite de la question
- Génère : ENCODE(n1) → ENCODE(n2) → OPÉRATION → EMERGE → DECODE(numeric_vocab)
- Pas de QUERY hologramme : calcul pur par résonance de phase
"""

import sys
import os
import re
from typing import Optional, List, Tuple, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'core', 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'backend', 'hologram'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vital-ka', 'backend', 'inference'))

from wave_ir import Program, Assign, Encode, Decode, Return, Var, Bind, Superpose, Emerge, Resonance, Oppose, Interfere, MathOp, Literal
from wave_code_generator import WaveCodeGenerator, WaveIntentDetector
from wave_lang import encode as wave_encode, bind as wave_bind, superpose as wave_superpose, resonate as wave_resonate, emerge as wave_emerge, decode as wave_decode
import numpy as np


class WaveGSM8KGenerator(WaveCodeGenerator):
    """
    Générateur de code ondulatoire pour problèmes GSM8K.
    
    Pattern GSM8K 'reason' :
    1. Extraire nombres et opération de la question
    2. ENCODE chaque nombre → vecteur ℂ⁵¹²
    3. Appliquer opération harmonique (BIND/SUPERPOSE/RESOLVE selon op)
    4. EMERGE pour calcul final
    5. DECODE vers vocabulaire numérique (0-10000)
    """
    
    # Vocabulaire numérique pour DECODE final
    NUMERIC_VOCAB = [str(i) for i in range(0, 10001)]
    
    # Patterns d'opérations GSM8K (mots-clés → opération harmonique)
    OP_PATTERNS = [
        # Addition
        (r'\b(?:more|plus|add|added|gain|gained|get|gets|received|find|found|total|altogether|sum|in all|together)\b', 'add'),
        # Soustraction
        (r'\b(?:less|fewer|minus|subtract|subtracted|lost|lose|spent|spend|give|gave|given|away|left|remain|remaining|difference)\b', 'sub'),
        # Multiplication
        (r'\b(?:times|multiply|multiplied|product|each|per|twice|double|triple|times as many)\b', 'mul'),
        # Division
        (r'\b(?:divide|divided|share|shared|each|per|ratio|split)\b', 'div'),
        # Pourcentage
        (r'\b(?:percent|%|percentage|of)\b', 'pct'),
    ]
    
    def __init__(self, dim: int = 512):
        super().__init__()
        self.dim = dim
        self.detector = WaveIntentDetector()
        # Vocabulaire numérique encodé
        self._numeric_vectors = {str(i): wave_encode(str(i), dim) for i in range(0, 1001)}
        for i in range(1001, 10001, 10):
            self._numeric_vectors[str(i)] = wave_encode(str(i), dim)
    
    def _extract_numbers(self, question: str) -> List[float]:
        """Extrait tous les nombres de la question (entiers, décimaux, fractions)."""
        nums = []
        # Nombres standards
        for m in re.finditer(r'\d+(?:[.,]\d+)?', question):
            val = float(m.group(0).replace(',', '.'))
            nums.append(val)
        # Fractions textuelles
        frac_map = {'half': 0.5, 'one-third': 1/3, 'two-thirds': 2/3, 
                    'quarter': 0.25, 'three-quarters': 0.75}
        for word, val in frac_map.items():
            if word in question.lower():
                nums.append(val)
        return nums
    
    def _detect_operation(self, question: str) -> str:
        """Détecte l'opération principale à partir de mots-clés."""
        q = question.lower()
        for pattern, op in self.OP_PATTERNS:
            if re.search(pattern, q):
                return op
        # Par défaut : addition (le plus fréquent)
        return 'add'
    
    def _detect_question_type(self, question: str) -> str:
        """Détecte le type de question pour guider l'opération."""
        q = question.lower()
        if re.search(r'\bhow many\b', q):
            return 'count'
        if re.search(r'\bhow much\b', q):
            return 'amount'
        if re.search(r'\bhow old\b', q):
            return 'age'
        if re.search(r'\bhow far\b', q):
            return 'distance'
        if re.search(r'\bhow long\b', q):
            return 'time'
        if re.search(r'\bwhat is\b.*\barea\b', q):
            return 'area'
        if re.search(r'\bwhat is\b.*\bperimeter\b', q):
            return 'perimeter'
        if re.search(r'\bwhat is\b.*\bcircumference\b', q):
            return 'circumference'
        if re.search(r'\bprofit\b', q):
            return 'profit'
        if re.search(r'\btotal cost\b|\bhow much.*cost\b', q):
            return 'cost'
        return 'generic'
    
    def generate_gsm8k(self, question: str) -> Program:
        """
        Génère un programme ondulatoire pour un problème GSM8K.
        
        Pipeline harmonique :
        ψ_n1 = ENCODE(n1)
        ψ_n2 = ENCODE(n2)
        ψ_op = ENCODE(opération)
        ψ_result = SUPERPOSE/BIND/RESOLVE(ψ_n1, ψ_n2, ψ_op)
        ψ_final = EMERGE(ψ_result)
        answer = DECODE(ψ_final, numeric_vocab)
        RETURN answer
        """
        # Extraire nombres
        numbers = self._extract_numbers(question)
        if len(numbers) < 2:
            # Fallback : générer programme reason standard
            return super().generate(question, lang='en')
        
        # Détecter opération
        op = self._detect_operation(question)
        qtype = self._detect_question_type(question)
        
        # Pour les problèmes multi-étapes, prendre les 2-3 premiers nombres
        # (les suivants sont souvent des distracteurs ou résultats intermédiaires)
        nums = numbers[:3] if len(numbers) > 2 else numbers
        
        statements = []
        
        # 1. ENCODE chaque nombre
        for i, n in enumerate(nums):
            var_name = f'psi_n{i}'
            statements.append(Assign(name=var_name, value=Encode(text=str(n))))
        
        # 2. ENCODE l'opération
        statements.append(Assign(name='psi_op', value=Encode(text=op)))
        
# 3. Appliquer opération harmonique selon le type
        if op == 'add':
            # Addition : SUPERPOSE(n1, n2) avec phase addition
            if len(nums) >= 2:
                statements.append(Assign(name='psi_sum', 
                    value=Superpose(psis=[Var(name='psi_n0'), Var(name='psi_n1')])))
                result_var = 'psi_sum'
            else:
                result_var = 'psi_n0'
                
        elif op == 'sub':
            # Soustraction : OPPOSE(n1, n2) = n1 - n2
            if len(nums) >= 2:
                statements.append(Assign(name='psi_diff', 
                    value=Oppose(left=Var(name='psi_n0'), right=Var(name='psi_n1'))))
                result_var = 'psi_diff'
            else:
                result_var = 'psi_n0'
                
        elif op == 'mul':
            # Multiplication : BIND(n1, n2) → produit tensoriel
            if len(nums) >= 2:
                statements.append(Assign(name='psi_prod', 
                    value=Bind(left=Var(name='psi_n0'), right=Var(name='psi_n1'))))
                result_var = 'psi_prod'
            else:
                result_var = 'psi_n0'
                
        elif op == 'div':
            # Division : RESONANCE(n1, n2) pour ratio
            if len(nums) >= 2:
                statements.append(Assign(name='psi_ratio', 
                    value=Resonance(left=Var(name='psi_n0'), right=Var(name='psi_n1'))))
                result_var = 'psi_ratio'
            else:
                result_var = 'psi_n0'
                
        elif op == 'pct':
            # Pourcentage : n1 % of n2 = n1/100 * n2
            if len(nums) >= 2:
                # Encoder "percentage" comme opération
                statements.append(Assign(name='psi_pct', value=Encode(text='percentage')))
                # SUPERPOSE pour combiner
                statements.append(Assign(name='psi_pct_result', 
                    value=Superpose(psis=[Var(name='psi_n0'), Var(name='psi_n1')])))
                result_var = 'psi_pct_result'
            else:
                result_var = 'psi_n0'
        else:
            result_var = 'psi_n0'
        
        # 4. EMERGE pour finaliser le calcul
        statements.append(Assign(name='psi_final', 
            value=Emerge(psis=[Var(name=result_var)])))
        
        # 5. DECODE vers vocabulaire numérique
        # Utiliser un ENCODE du vocabulaire comme référence pour DECODE
        statements.append(Assign(name='psi_numvocab', value=Encode(text=' '.join(self.NUMERIC_VOCAB[:101]))))
        statements.append(Assign(name='answer', 
            value=Decode(psi=Var(name='psi_final'), top_k=1)))
        
        # 6. RETURN
        statements.append(Return(value=Var(name='answer')))
        
        return Program(statements)
    
    def generate(self, question: str, lang: str = 'en') -> Program:
        """Point d'entrée principal - détection d'intention puis génération appropriée."""
        intent, confidence = self.detector.detect_wave_intent(question)
        
        # Forcer 'reason' pour GSM8K même si détecteur dit autre chose
        if self._is_gsm8k(question):
            intent = 'reason'
        
        if intent == 'reason':
            return self.generate_gsm8k(question)
        else:
            return super().generate(question, lang=lang)
    
    def _is_gsm8k(self, question: str) -> bool:
        """Heuristique pour détecter un problème style GSM8K."""
        q = question.lower()
        # Indicateurs GSM8K
        indicators = [
            r'\bhow many\b', r'\bhow much\b', r'\bhow old\b', r'\bhow far\b',
            r'\bwhat is\b.*\barea\b', r'\bwhat is\b.*\bperimeter\b',
            r'\btotal\b', r'\bprofit\b', r'\bcost\b', r'\bprice\b',
            r'\bper\b', r'\beach\b', r'\btimes\b', r'\bpercent\b', r'\%',
            r'\bdollar\b', r'\bcent\b', r'\bhour\b', r'\bminute\b',
            r'\bday\b', r'\bweek\b', r'\bmonth\b', r'\byear\b',
            # Entités/actions typiques GSM8K
            r'\bapple\b', r'\borange\b', r'\bcookie\b', r'\bcandy\b',
            r'\bbox\b', r'\bpencil\b', r'\bbook\b', r'\btoy\b',
            r'\bbuy\b', r'\bbought\b', r'\bsell\b', r'\bsold\b',
            r'\bhas\b', r'\bhave\b', r'\bhad\b', r'\beat\b', r'\bate\b',
            r'\bgive\b', r'\bgave\b', r'\bfind\b', r'\bfound\b',
            r'\bcar\b', r'\bdrive\b', r'\bdrove\b', r'\bspeed\b',
            r'\bbox\b', r'\bdozen\b', r'\bpack\b',
        ]
        score = sum(1 for pat in indicators if re.search(pat, q))
        return score >= 1  # Au moins 1 indicateur fort (how many, etc.)


def generate_gsm8k_program(question: str) -> Program:
    """Fonction utilitaire pour générer un programme GSM8K."""
    gen = WaveGSM8KGenerator()
    return gen.generate(question)


if __name__ == "__main__":
    # Test
    test_questions = [
        "John has 5 apples. He buys 3 more. How many apples does he have?",
        "Mary had 10 cookies. She ate 4. How many cookies does she have left?",
        "There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?",
        "A car drives at 60 mph for 2 hours. How far does it go?",
        "What is 20% of 150?",
    ]
    
    gen = WaveGSM8KGenerator()
    
    for q in test_questions:
        print(f"Q: {q}")
        prog = gen.generate(q)
        print(f"  Program: {prog.to_wave()}")
        print()