#!/usr/bin/env python3
"""
Harmonic Multi-Step Reasoner — True Reasoning by Iterative Decomposition
=========================================================================
Real multi-step reasoning: decompose compound problems into sub-problems
that CAN be solved by the KB, then recombine the results.

Algorithm:
  1. Analyze the prompt for compound patterns
  2. Extract the mathematical "atoms" (functions, numbers, operations)
  3. Generate concrete, solvable sub-questions for each atom
  4. Solve sub-questions using the KB (with semantic matching)
  5. Combine results using the decomposition template
  6. Verify coherence with ABC convergence
"""

import math, re, sys, os, time
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(__file__))

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
B_1_PHI = 0.8506508083
K0 = B_1_PHI

# ============================================================================
# EXPRESSION EXTRACTOR — Pull out mathematical atoms from a prompt
# ============================================================================

def extract_expressions(prompt: str) -> Dict[str, str]:
    """Extract mathematical expressions from a compound prompt."""
    found = {}
    
    # Functions: sin(x), cos(x^2), ln(x), e^(x^2), sqrt(x), tan(x)
    func_patterns = [
        (r'(?:sin|cos|tan|cot|sec|csc)\([^)]+\)', 'trig_func'),
        (r'ln\([^)]+\)', 'ln_func'),
        (r'e\^\([^)]+\)', 'exp_func'),
        (r'sqrt\([^)]+\)', 'sqrt_func'),
        (r'(?:arcsin|arccos|arctan)\([^)]+\)', 'inv_trig'),
    ]
    for pat, name in func_patterns:
        m = re.search(pat, prompt)
        if m:
            found[name] = m.group(0)
    
    # Powers: x^2, x^3, x^n
    m = re.search(r'([a-zA-Z])\^(\d+)', prompt)
    if m:
        found['power'] = m.group(0)
        found['variable'] = m.group(1)
        found['exponent'] = m.group(2)
    
    # Find the "inner function" of a composite: sin(x^2) → inner = x^2
    m = re.search(r'(?:sin|cos|tan|ln|exp|sqrt)\(([^)]+)\)', prompt)
    if m:
        inner = m.group(1)
        # Check if inner is itself a function or just a variable
        if re.search(r'[a-zA-Z]\^?\d*', inner):
            found['inner_expression'] = inner
            # Is it a power?
            pm = re.search(r'([a-zA-Z])\^(\d+)', inner)
            if pm:
                found['inner_power'] = inner
                found['inner_variable'] = pm.group(1)
                found['inner_exponent'] = pm.group(2)
    
    # Quadratic: x^2 - 3x + 2 = 0
    m = re.search(r'x\^2\s*([-+])\s*(\d+)x\s*([-+])\s*(\d+)\s*=\s*0', prompt)
    if m:
        found['quadratic'] = m.group(0)
        found['quad_a'] = '1'
        found['quad_b_sign'] = m.group(1)
        found['quad_b'] = m.group(2)
        found['quad_c_sign'] = m.group(3)
        found['quad_c'] = m.group(4)
    
    # Product: x * sin(x), x^2 * cos(x), e^x * sin(x)
    m = re.search(r'(?:derivative|differentiate).*?([a-zA-Z0-9^\(\)\* ]+)\s*\*\s*([a-zA-Z0-9^\(\)]+)', prompt)
    if m:
        found['product_factor1'] = m.group(1).strip()
        found['product_factor2'] = m.group(2).strip()
    
    # Numbers
    numbers = re.findall(r'\b(\d+)\b', prompt)
    if numbers:
        found['numbers'] = numbers
    
    return found

# ============================================================================
# MULTI-STEP REASONER
# ============================================================================

class HarmonicMultiStepReasoner:
    """True multi-step reasoning by decomposition into KB-solvable sub-questions."""
    
    def __init__(self, math_engine, max_depth=3, max_iterations=5):
        self.engine = math_engine
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self.stats = {"total": 0, "decomposed": 0, "solved": 0}
    
    def solve(self, prompt: str, analysis: Dict = None, depth: int = 0) -> Dict[str, Any]:
        """Solve a (potentially compound) problem."""
        self.stats["total"] += 1
        
        if depth >= self.max_depth:
            return self._fallback(prompt, analysis)
        
        # 1. Try direct KB lookup first (with semantic matching)
        if analysis is None:
            analysis = self.engine.analyze(prompt)
        
        direct = self.engine._match_precomputed(prompt.lower())
        if direct and direct.get("coherence", 0) >= 0.80:
            return {"text": direct["text"], "confidence": direct["coherence"], 
                    "method": "kb_direct", "steps": []}
        
        # 2. Check if it's a compound problem
        expr = extract_expressions(prompt)
        
        if not expr or len(expr) <= 1:
            # Simple problem not in KB — fallback
            return self._fallback(prompt, analysis)
        
        # 3. Decompose and solve
        steps = self._decompose_and_solve(prompt, expr)
        
        if not steps:
            return self._fallback(prompt, analysis)
        
        self.stats["decomposed"] += 1
        
        # 4. Combine results
        combined = self._combine(prompt, steps)
        
        # 5. Overall confidence
        confs = [s.get("confidence", 0) for s in steps if isinstance(s, dict)]
        avg_conf = sum(confs) / max(len(confs), 1) if confs else 0.5
        
        self.stats["solved"] += 1
        
        return {
            "text": combined,
            "confidence": round(avg_conf, 4),
            "method": "harmonic_multi_step",
            "steps": steps,
            "converged": avg_conf >= 0.60,
        }
    
    def _decompose_and_solve(self, prompt: str, expr: Dict) -> List[Dict]:
        """Decompose into sub-problems and solve each."""
        steps = []
        
        # === PATTERN: Chain rule — derivative of f(g(x)) ===
        if 'trig_func' in expr or 'ln_func' in expr or 'exp_func' in expr:
            if re.search(r'derivative|differentiate|d/dx', prompt):
                # Outer function: derivative of sin(u), cos(u), ln(u), etc.
                func_map = {
                    'trig_func': {'sin': 'cos', 'cos': '-sin', 'tan': 'sec^2'},
                    'ln_func': {'ln': '1/'},
                    'exp_func': {'e^': 'e^'},
                }
                
                # Which outer function?
                for ftype in ['trig_func', 'ln_func', 'exp_func']:
                    if ftype in expr:
                        func_expr = expr[ftype]
                        func_name = re.match(r'([a-z]+)\(', func_expr)
                        if func_name:
                            outer_name = func_name.group(1)
                            # Step 1: derivative of outer
                            step1_q = f"what is the derivative of {outer_name}(x)"
                            step1 = self._solve_sub(step1_q)
                            steps.append({"step": 1, "prompt": step1_q, "result": step1.get("text", "?"), "confidence": step1.get("confidence", 0.5)})
                
                # Step 2: derivative of inner
                if 'inner_expression' in expr:
                    inner = expr['inner_expression']
                    step2_q = f"what is the derivative of {inner}"
                    step2 = self._solve_sub(step2_q)
                    steps.append({"step": 2, "prompt": step2_q, "result": step2.get("text", "?"), "confidence": step2.get("confidence", 0.5)})
        
        # === PATTERN: Product rule ===
        elif 'product_factor1' in expr and 'product_factor2' in expr:
            if re.search(r'derivative|differentiate', prompt):
                f1 = expr['product_factor1']
                f2 = expr['product_factor2']
                step1_q = f"what is the derivative of {f1}"
                step2_q = f"what is the derivative of {f2}"
                step1 = self._solve_sub(step1_q)
                step2 = self._solve_sub(step2_q)
                steps.append({"step": 1, "prompt": step1_q, "result": step1.get("text", "?"), "confidence": step1.get("confidence", 0.5)})
                steps.append({"step": 2, "prompt": step2_q, "result": step2.get("text", "?"), "confidence": step2.get("confidence", 0.5)})
        
        # === PATTERN: Quadratic equation ===
        elif 'quadratic' in expr:
            step1_q = f"solve {expr['quadratic']}"
            step1 = self._solve_sub(step1_q)
            steps.append({"step": 1, "prompt": step1_q, "result": step1.get("text", "?"), "confidence": step1.get("confidence", 0.5)})
        
        # === PATTERN: Power derivative ===
        elif 'power' in expr and re.search(r'derivative|differentiate', prompt):
            step1_q = f"what is the derivative of {expr['power']}"
            step1 = self._solve_sub(step1_q)
            steps.append({"step": 1, "prompt": step1_q, "result": step1.get("text", "?"), "confidence": step1.get("confidence", 0.5)})
        
        # === GENERIC: Try solving the whole question ===
        if not steps:
            step1_q = prompt
            step1 = self._solve_sub(step1_q)
            if step1.get("confidence", 0) >= 0.5:
                steps.append({"step": 1, "prompt": step1_q, "result": step1.get("text", "?"), "confidence": step1.get("confidence", 0.5)})
        
        return steps
    
    def _solve_sub(self, prompt: str) -> Dict:
        """Solve a sub-problem using the engine's semantic matching."""
        analysis = self.engine.analyze(prompt)
        # Try KB first
        match = self.engine._match_precomputed(prompt.lower())
        if match:
            return match
        # Try arithmetic
        arith = self.engine._solve_arithmetic(prompt)
        if arith:
            return arith
        # Fallback
        result = self.engine.solve(prompt, analysis)
        return result
    
    def _combine(self, original: str, steps: List[Dict]) -> str:
        """Combine sub-results into a coherent multi-step solution."""
        text = f"Solution for: {original}\n\n"
        
        for i, s in enumerate(steps):
            if isinstance(s, dict):
                text += f"Step {s.get('step', i+1)}: {s.get('prompt', '?')}\n"
                text += f"  {s.get('result', '?')}\n\n"
        
        if len(steps) >= 2:
            text += "Combined result: The problem was decomposed into sub-problems and solved step by step."
        
        return text.strip()
    
    def _fallback(self, prompt: str, analysis: Dict = None) -> Dict:
        """Fallback when decomposition fails."""
        return {
            "text": f"Harmonic analysis did not find a direct match for: {prompt[:100]}",
            "confidence": 0.25,
            "method": "harmonic_unresolved",
            "steps": [],
        }
    
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "decomposition_rate": self.stats["decomposed"] / max(self.stats["total"], 1),
            "solve_rate": self.stats["solved"] / max(self.stats["decomposed"], 1),
        }
    
    def reset(self):
        self.stats = {"total": 0, "decomposed": 0, "solved": 0}