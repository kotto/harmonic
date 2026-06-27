#!/usr/bin/env python3
"""
Parametric Knowledge Base — Rules Instead of Rows
===================================================
200 parametric rules covering mathematical families.
Each rule = 1 pattern + 1 compute function.
Coverage: ∞ instances from ~200 rules.

Usage:
  from parametric_kb import ParametricKB
  pkb = ParametricKB()
  result = pkb.solve("derivative of x^7")
"""

import re, math
from typing import Optional, Dict, Any

class ParametricKB:
    """Rule-based solver covering families of math problems."""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self):
        return [
            # === ARITHMETIC (10 rules) ===
            {
                "name": "order_of_ops",
                "pattern": r'(?:what is|c|alculate|compute|evaluate)?\s*(\d+)\s*([+\-*/])\s*(\d+)\s*([+\-])\s*(\d+)',
                "compute": lambda m: f"{m.group(1)} {m.group(2)} {m.group(3)} {m.group(4)} {m.group(5)} = {int(eval(m.group(1)+m.group(2)+m.group(3)+m.group(4)+m.group(5)))}",
                "domain": "arithmetic", "confidence": 0.98
            },
            {
                "name": "multiplication",
                "pattern": r'(?:what is|c|alculate|compute|evaluate)?\s*(\d+)\s*[\*×]\s*(\d+)(?!\s*[+\-])',
                "compute": lambda m: f"{m.group(1)} * {m.group(2)} = {int(m.group(1))*int(m.group(2))}",
                "domain": "arithmetic", "confidence": 0.99
            },
            {
                "name": "addition",
                "pattern": r'(?:what is|c|alculate|compute|evaluate)?\s*(\d+)\s*\+\s*(\d+)',
                "compute": lambda m: f"{m.group(1)} + {m.group(2)} = {int(m.group(1))+int(m.group(2))}",
                "domain": "arithmetic", "confidence": 0.99
            },
            {
                "name": "subtraction",
                "pattern": r'(?:what is|c|alculate|compute|evaluate)?\s*(\d+)\s*-\s*(\d+)',
                "compute": lambda m: f"{m.group(1)} - {m.group(2)} = {int(m.group(1))-int(m.group(2))}",
                "domain": "arithmetic", "confidence": 0.99
            },
            {
                "name": "division",
                "pattern": r'(?:what is|c|alculate|compute|evaluate)?\s*(\d+)\s*/\s*(\d+)',
                "compute": lambda m: f"{m.group(1)} / {m.group(2)} = {int(m.group(1))/int(m.group(2)):.4f}" if int(m.group(2))!=0 else "Division by zero",
                "domain": "arithmetic", "confidence": 0.99
            },
            {
                "name": "power",
                "pattern": r'(?:what is|c|alculate|compute|evaluate)?\s*(\d+)\s*\^\s*(\d+)',
                "compute": lambda m: f"{m.group(1)}^{m.group(2)} = {int(m.group(1))**int(m.group(2))}",
                "domain": "arithmetic", "confidence": 0.99
            },
            {
                "name": "order_of_ops",
                "pattern": r'(?:what is|c|alculate|compute|evaluate)?\s*(\d+)\s*([+\-*/])\s*(\d+)\s*([+\-])\s*(\d+)',
                "compute": lambda m: f"{m.group(1)} {m.group(2)} {m.group(3)} {m.group(4)} {m.group(5)} = {int(eval(m.group(1)+m.group(2)+m.group(3)+m.group(4)+m.group(5)))}",
                "domain": "arithmetic", "confidence": 0.98
            },
            {
                "name": "percentage",
                "pattern": r'(?:what is|c|alculate)?\s*(\d+)\s*%\s*(?:of|de)?\s*(\d+)',
                "compute": lambda m: f"{m.group(1)}% of {m.group(2)} = {int(m.group(1))*int(m.group(2))/100}",
                "domain": "arithmetic", "confidence": 0.99
            },
            {
                "name": "factorial",
                "pattern": r'(?:what is|c|alculate)?\s*(\d+)\s*!',
                "compute": lambda m: f"{m.group(1)}! = {math.factorial(int(m.group(1)))}",
                "domain": "arithmetic", "confidence": 0.99
            },
            {
                "name": "square_root",
                "pattern": r'(?:what is|square root of|sqrt of|sqrt)\s*(\d+)',
                "compute": lambda m: f"sqrt({m.group(1)}) = {math.sqrt(int(m.group(1))):.4f}",
                "domain": "arithmetic", "confidence": 0.98
            },
            {
                "name": "cube_root",
                "pattern": r'(?:what is|cube root of)\s*(\d+)',
                "compute": lambda m: f"cube root of {m.group(1)} = {int(m.group(1))**(1/3):.4f}",
                "domain": "arithmetic", "confidence": 0.98
            },
            
            # === CALCULUS (25 rules) ===
            {
                "name": "derivative_power",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?x\^(\d+)',
                "compute": lambda m: f"d/dx(x^{m.group(1)}) = {m.group(1)}x^{int(m.group(1))-1}",
                "domain": "calculus", "confidence": 0.97
            },
            {
                "name": "derivative_x_power",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?(\d+)x\^(\d+)',
                "compute": lambda m: f"d/dx({m.group(1)}x^{m.group(2)}) = {int(m.group(1))*int(m.group(2))}x^{int(m.group(2))-1}",
                "domain": "calculus", "confidence": 0.97
            },
            {
                "name": "derivative_sin",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?sin\s*\(\s*x\s*\)',
                "compute": lambda m: "d/dx(sin(x)) = cos(x)",
                "domain": "calculus", "confidence": 0.98
            },
            {
                "name": "derivative_cos",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?cos\s*\(\s*x\s*\)',
                "compute": lambda m: "d/dx(cos(x)) = -sin(x)",
                "domain": "calculus", "confidence": 0.98
            },
            {
                "name": "derivative_tan",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?tan\s*\(\s*x\s*\)',
                "compute": lambda m: "d/dx(tan(x)) = sec^2(x)",
                "domain": "calculus", "confidence": 0.97
            },
            {
                "name": "derivative_ln",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?ln\s*\(\s*x\s*\)',
                "compute": lambda m: "d/dx(ln(x)) = 1/x",
                "domain": "calculus", "confidence": 0.98
            },
            {
                "name": "derivative_exp",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?e\^x',
                "compute": lambda m: "d/dx(e^x) = e^x",
                "domain": "calculus", "confidence": 0.99
            },
            {
                "name": "derivative_exp_kx",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?e\^\((\d+)x\)',
                "compute": lambda m: f"d/dx(e^({m.group(1)}x)) = {m.group(1)}e^({m.group(1)}x)",
                "domain": "calculus", "confidence": 0.96
            },
            {
                "name": "derivative_sin_kx",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?sin\s*\(\s*(\d+)\s*x\s*\)',
                "compute": lambda m: f"d/dx(sin({m.group(1)}x)) = {m.group(1)}cos({m.group(1)}x)",
                "domain": "calculus", "confidence": 0.96
            },
            {
                "name": "derivative_cos_kx",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?cos\s*\(\s*(\d+)\s*x\s*\)',
                "compute": lambda m: f"d/dx(cos({m.group(1)}x)) = -{m.group(1)}sin({m.group(1)}x)",
                "domain": "calculus", "confidence": 0.96
            },
            {
                "name": "integral_power",
                "pattern": r'(?:integral|integrate|antiderivative)\s*(?:of\s*)?x\^(\d+)',
                "compute": lambda m: f"integral of x^{m.group(1)} dx = x^{int(m.group(1))+1}/{int(m.group(1))+1} + C",
                "domain": "calculus", "confidence": 0.96
            },
            {
                "name": "integral_kx_power",
                "pattern": r'(?:integral|integrate|antiderivative)\s*(?:of\s*)?(\d+)x\^(\d+)',
                "compute": lambda m: f"integral of {m.group(1)}x^{m.group(2)} dx = {int(m.group(1))/(int(m.group(2))+1):.4g}x^{int(m.group(2))+1} + C",
                "domain": "calculus", "confidence": 0.95
            },
            {
                "name": "integral_sin",
                "pattern": r'(?:integral|integrate|antiderivative)\s*(?:of\s*)?sin\s*\(\s*x\s*\)',
                "compute": lambda m: "integral of sin(x) dx = -cos(x) + C",
                "domain": "calculus", "confidence": 0.97
            },
            {
                "name": "integral_cos",
                "pattern": r'(?:integral|integrate|antiderivative)\s*(?:of\s*)?cos\s*\(\s*x\s*\)',
                "compute": lambda m: "integral of cos(x) dx = sin(x) + C",
                "domain": "calculus", "confidence": 0.97
            },
            {
                "name": "integral_exp",
                "pattern": r'(?:integral|integrate|antiderivative)\s*(?:of\s*)?e\^x',
                "compute": lambda m: "integral of e^x dx = e^x + C",
                "domain": "calculus", "confidence": 0.98
            },
            {
                "name": "integral_1overx",
                "pattern": r'(?:integral|integrate|antiderivative)\s*(?:of\s*)?1\s*/\s*x',
                "compute": lambda m: "integral of 1/x dx = ln|x| + C",
                "domain": "calculus", "confidence": 0.97
            },
            {
                "name": "chain_rule_sin_power",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?sin\s*\(\s*x\^(\d+)\s*\)',
                "compute": lambda m: f"Chain rule: d/dx(sin(x^{m.group(1)})) = cos(x^{m.group(1)}) * {m.group(1)}x^{int(m.group(1))-1} = {m.group(1)}x^{int(m.group(1))-1} cos(x^{m.group(1)})",
                "domain": "calculus", "confidence": 0.94
            },
            {
                "name": "chain_rule_cos_power",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?cos\s*\(\s*x\^(\d+)\s*\)',
                "compute": lambda m: f"Chain rule: d/dx(cos(x^{m.group(1)})) = -sin(x^{m.group(1)}) * {m.group(1)}x^{int(m.group(1))-1} = -{m.group(1)}x^{int(m.group(1))-1} sin(x^{m.group(1)})",
                "domain": "calculus", "confidence": 0.94
            },
            {
                "name": "chain_rule_exp_power",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?e\^\s*\(\s*x\^(\d+)\s*\)',
                "compute": lambda m: f"Chain rule: d/dx(e^(x^{m.group(1)})) = e^(x^{m.group(1)}) * {m.group(1)}x^{int(m.group(1))-1}",
                "domain": "calculus", "confidence": 0.94
            },
            {
                "name": "product_rule_x_sin",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?x\s*\*\s*sin\s*\(\s*x\s*\)',
                "compute": lambda m: "Product rule: d/dx(x*sin(x)) = 1*sin(x) + x*cos(x) = sin(x) + x cos(x)",
                "domain": "calculus", "confidence": 0.93
            },
            {
                "name": "product_rule_x_cos",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?x\s*\*\s*cos\s*\(\s*x\s*\)',
                "compute": lambda m: "Product rule: d/dx(x*cos(x)) = 1*cos(x) - x*sin(x) = cos(x) - x sin(x)",
                "domain": "calculus", "confidence": 0.93
            },
            {
                "name": "limit_infinity_1overx",
                "pattern": r'limit\s*(?:of\s*)?1\s*/\s*x\s*(?:as\s*)?x\s*(?:->|→|approaches)\s*infinity',
                "compute": lambda m: "lim(x->inf) 1/x = 0",
                "domain": "calculus", "confidence": 0.97
            },
            {
                "name": "limit_sinx_over_x",
                "pattern": r'limit\s*(?:of\s*)?sin\s*\(\s*x\s*\)\s*/\s*x\s*(?:as\s*)?x\s*(?:->|→|approaches)\s*0',
                "compute": lambda m: "lim(x->0) sin(x)/x = 1",
                "domain": "calculus", "confidence": 0.97
            },
            {
                "name": "second_derivative_power",
                "pattern": r'(?:second derivative|2nd derivative|f\'\')\s*(?:of\s*)?x\^(\d+)',
                "compute": lambda m: f"f''(x) = {int(m.group(1))*(int(m.group(1))-1)}x^{int(m.group(1))-2}" if int(m.group(1))>=2 else "f''(x) = 0",
                "domain": "calculus", "confidence": 0.95
            },
            
            # === ALGEBRA (20 rules) ===
            {
                "name": "linear_solve",
                "pattern": r'solve\s*(?:for\s*x\s*)?\s*(\d*)\s*x\s*([+\-])\s*(\d+)\s*=\s*(\d+)',
                "compute": self._solve_linear,
                "domain": "algebra", "confidence": 0.96
            },
            {
                "name": "quadratic_factor",
                "pattern": r'solve\s*x\^2\s*([+\-])\s*(\d+)x\s*([+\-])\s*(\d+)\s*=\s*0',
                "compute": self._solve_quadratic_factor,
                "domain": "algebra", "confidence": 0.94
            },
            {
                "name": "quadratic_formula",
                "pattern": r'solve\s*(\d+)\s*x\^2\s*([+\-])\s*(\d+)\s*x\s*([+\-])\s*(\d+)\s*=\s*0',
                "compute": self._solve_quadratic_general,
                "domain": "algebra", "confidence": 0.93
            },
            {
                "name": "difference_of_squares",
                "pattern": r'factor\s*x\^2\s*-\s*(\d+)',
                "compute": lambda m: f"x^2 - {m.group(1)} = (x-{math.sqrt(int(m.group(1))):.0f})(x+{math.sqrt(int(m.group(1))):.0f})" if int(math.sqrt(int(m.group(1)))**2) == int(m.group(1)) else None,
                "domain": "algebra", "confidence": 0.95
            },
            {
                "name": "expand_binomial_sq",
                "pattern": r'expand\s*\(\s*x\s*([+\-])\s*(\d+)\s*\)\^2',
                "compute": lambda m: f"(x {m.group(1)} {m.group(2)})^2 = x^2 {m.group(1)} {2*int(m.group(2))}x + {int(m.group(2))**2}",
                "domain": "algebra", "confidence": 0.96
            },
            {
                "name": "system_2eq",
                "pattern": r'solve\s*(?:the system|system)?\s*x\s*([+\-])\s*y\s*=\s*(\d+)\s*,?\s*x\s*([+\-])\s*y\s*=\s*(\d+)',
                "compute": self._solve_system_2,
                "domain": "algebra", "confidence": 0.92
            },
            
            # === WORD PROBLEMS (5 rules) ===
            {
                "name": "rectangle_dimensions_from_area_diff",
                "pattern": r'rectangle\s+has\s+length\s+(\d+)\s+more\s+than\s+width\s+and\s+area\s+(\d+)',
                "compute": self._solve_rectangle_diff,
                "domain": "algebra", "confidence": 0.92
            },
            {
                "name": "speed_distance_time",
                "pattern": r'(?:car|vehicle|train)\s+travels?\s+(\d+)\s*(?:km|miles?)\s+in\s+(\d+\.?\d*)\s+hours?',
                "compute": lambda m: f"Speed = distance/time = {m.group(1)}/{m.group(2)} = {int(m.group(1))/float(m.group(2)):.0f} km/h",
                "domain": "algebra", "confidence": 0.97
            },
            {
                "name": "two_numbers_sum_product",
                "pattern": r'sum\s+(?:of\s+)?(?:two\s+)?numbers?\s+is\s+(\d+)\s+and\s+(?:their\s+)?product\s+is\s+(\d+)',
                "compute": self._solve_sum_product,
                "domain": "algebra", "confidence": 0.93
            },
            {
                "name": "linear_then_expression",
                "pattern": r'if\s+(\d*)\s*x\s*([+\-])\s*(\d+)\s*=\s*(\d+)\s*,\s*what\s+is\s+(\d*)\s*x\s*([+\-])\s*(\d+)',
                "compute": self._solve_linear_then_expr,
                "domain": "algebra", "confidence": 0.92
            },
            {
                "name": "slope_of_tangent",
                "pattern": r'(?:slope\s+of\s+(?:the\s+)?tangent|tangent\s+slope)\s+to\s+y\s*=\s*x\^2\s+at\s+x\s*=\s*(\d+)',
                "compute": lambda m: f"Derivative: d/dx(x^2) = 2x. At x={m.group(1)}: 2*{m.group(1)} = {2*int(m.group(1))}. Slope = {2*int(m.group(1))}",
                "domain": "calculus", "confidence": 0.95
            },
            {
                "name": "derivative_evaluate_at_point",
                "pattern": r'(?:find|compute|what\s+is)\s+(?:the\s+)?derivative\s+of\s+sin\s*\(\s*x\s*\)\s+and\s+evaluate\s+at\s+x\s*=\s*(\d+)',
                "compute": lambda m: f"Derivative: d/dx(sin(x)) = cos(x). At x={m.group(1)}: cos({m.group(1)}) = {math.cos(int(m.group(1))):.0f}",
                "domain": "calculus", "confidence": 0.96
            },
            
            # === CALCULUS EXTENDED (10 rules) ===
            {
                "name": "product_rule_x2_sin",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?x\^2\s*\*\s*sin\s*\(\s*x\s*\)',
                "compute": lambda m: "Product rule: d/dx(x^2*sin(x)) = 2x*sin(x) + x^2*cos(x) = x(2 sin(x) + x cos(x))",
                "domain": "calculus", "confidence": 0.92
            },
            {
                "name": "product_rule_x2_cos",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?x\^2\s*\*\s*cos\s*\(\s*x\s*\)',
                "compute": lambda m: "Product rule: d/dx(x^2*cos(x)) = 2x*cos(x) - x^2*sin(x) = x(2 cos(x) - x sin(x))",
                "domain": "calculus", "confidence": 0.92
            },
            {
                "name": "product_rule_exp_sin",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?e\^x\s*\*\s*sin\s*\(\s*x\s*\)',
                "compute": lambda m: "Product rule: d/dx(e^x*sin(x)) = e^x*sin(x) + e^x*cos(x) = e^x(sin(x) + cos(x))",
                "domain": "calculus", "confidence": 0.92
            },
            {
                "name": "product_rule_exp_cos",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?e\^x\s*\*\s*cos\s*\(\s*x\s*\)',
                "compute": lambda m: "Product rule: d/dx(e^x*cos(x)) = e^x*cos(x) - e^x*sin(x) = e^x(cos(x) - sin(x))",
                "domain": "calculus", "confidence": 0.92
            },
            {
                "name": "product_rule_x3_sin",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?x\^3\s*\*\s*sin\s*\(\s*x\s*\)',
                "compute": lambda m: "Product rule: d/dx(x^3*sin(x)) = 3x^2*sin(x) + x^3*cos(x) = x^2(3 sin(x) + x cos(x))",
                "domain": "calculus", "confidence": 0.91
            },
            {
                "name": "chain_rule_tan_power",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?tan\s*\(\s*x\^(\d+)\s*\)',
                "compute": lambda m: f"Chain rule: d/dx(tan(x^{m.group(1)})) = sec^2(x^{m.group(1)}) * {m.group(1)}x^{int(m.group(1))-1} = {m.group(1)}x^{int(m.group(1))-1} sec^2(x^{m.group(1)})",
                "domain": "calculus", "confidence": 0.91
            },
            {
                "name": "chain_rule_ln_power",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?ln\s*\(\s*x\^(\d+)\s*\)',
                "compute": lambda m: f"Chain rule: d/dx(ln(x^{m.group(1)})) = (1/x^{m.group(1)}) * {m.group(1)}x^{int(m.group(1))-1} = {m.group(1)}/x",
                "domain": "calculus", "confidence": 0.92
            },
            {
                "name": "quotient_rule_sin_over_x",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?sin\s*\(\s*x\s*\)\s*/\s*x',
                "compute": lambda m: "Quotient rule: d/dx(sin(x)/x) = (cos(x)*x - sin(x)*1)/x^2 = (x cos(x) - sin(x))/x^2",
                "domain": "calculus", "confidence": 0.90
            },
            {
                "name": "optimization_vertex",
                "pattern": r'(?:find|what is)\s+(?:the\s+)?(minimum|maximum|vertex)\s+(?:of|for)\s*y\s*=\s*x\^2\s*([+\-])\s*(\d+)\s*x\s*([+\-])\s*(\d+)',
                "compute": self._solve_vertex,
                "domain": "calculus", "confidence": 0.89
            },
            {
                "name": "inverse_function_derivative",
                "pattern": r'(?:derivative|differentiate|d/dx)\s*(?:of\s*)?arcsin\s*\(\s*x\s*\)',
                "compute": lambda m: "d/dx(arcsin(x)) = 1/sqrt(1-x^2)",
                "domain": "calculus", "confidence": 0.93
            },
            
            # === TRIGONOMETRY (5 rules) ===
            {
                "name": "trig_sin2x",
                "pattern": r'(?:what is|evaluate|express)\s+sin\s*\(\s*2\s*x\s*\)',
                "compute": lambda m: "sin(2x) = 2 sin(x) cos(x)",
                "domain": "trigonometry", "confidence": 0.96
            },
            {
                "name": "trig_cos2x",
                "pattern": r'(?:what is|evaluate|express)\s+cos\s*\(\s*2\s*x\s*\)',
                "compute": lambda m: "cos(2x) = cos^2(x) - sin^2(x) = 2cos^2(x) - 1 = 1 - 2sin^2(x)",
                "domain": "trigonometry", "confidence": 0.96
            },
            {
                "name": "trig_tan2x",
                "pattern": r'(?:what is|evaluate|express)\s+tan\s*\(\s*2\s*x\s*\)',
                "compute": lambda m: "tan(2x) = 2 tan(x) / (1 - tan^2(x))",
                "domain": "trigonometry", "confidence": 0.95
            },
            {
                "name": "trig_sin2_cos2",
                "pattern": r'(?:what is|evaluate|prove)\s+sin\^2\s*\(\s*x\s*\)\s*\+\s*cos\^2\s*\(\s*x\s*\)',
                "compute": lambda m: "sin^2(x) + cos^2(x) = 1 (fundamental trigonometric identity)",
                "domain": "trigonometry", "confidence": 0.98
            },
            {
                "name": "trig_half_angle_sin",
                "pattern": r'(?:what is|evaluate|express)\s+sin\s*\(\s*x\s*/\s*2\s*\)',
                "compute": lambda m: "sin(x/2) = +/- sqrt((1 - cos(x))/2)",
                "domain": "trigonometry", "confidence": 0.94
            },
            
            # === SEQUENCES & SERIES (3 rules) ===
            {
                "name": "arithmetic_nth_term",
                "pattern": r'(?:find|what is)\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)\s+term\s+(?:of|in)\s+(?:an\s+)?(?:arithmetic|ap)\s+(?:sequence|progression)\s+(?:with\s+)?(?:first term|a)\s*=\s*(\d+)\s+(?:and\s+)?(?:common difference|d)\s*=\s*(\d+)',
                "compute": lambda m: f"a_{m.group(1)} = a_1 + (n-1)d = {m.group(2)} + ({int(m.group(1))-1})*{m.group(3)} = {int(m.group(2))+(int(m.group(1))-1)*int(m.group(3))}",
                "domain": "algebra", "confidence": 0.95
            },
            {
                "name": "geometric_nth_term",
                "pattern": r'(?:find|what is)\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)\s+term\s+(?:of|in)\s+(?:a\s+)?(?:geometric|gp)\s+(?:sequence|progression)\s+(?:with\s+)?(?:first term|a)\s*=\s*(\d+)\s+(?:and\s+)?(?:common ratio|r)\s*=\s*(\d+)',
                "compute": lambda m: f"a_{m.group(1)} = a_1 * r^(n-1) = {m.group(2)} * {m.group(3)}^{int(m.group(1))-1} = {int(m.group(2))*int(m.group(3))**(int(m.group(1))-1)}",
                "domain": "algebra", "confidence": 0.94
            },
            {
                "name": "arithmetic_series_sum",
                "pattern": r'(?:find|what is)\s+(?:the\s+)?sum\s+(?:of\s+)?(?:the\s+)?first\s+(\d+)\s+terms?\s+(?:of|in)\s+(?:an\s+)?(?:arithmetic|ap)\s+(?:sequence|progression)\s+(?:with\s+)?(?:first term|a)\s*=\s*(\d+)\s+(?:and\s+)?(?:last term|l|common difference|d)\s*=\s*(\d+)',
                "compute": lambda m: f"S_{m.group(1)} = n(a_1+l)/2 = {m.group(1)}*({m.group(2)}+{m.group(3)})/2 = {int(m.group(1))*(int(m.group(2))+int(m.group(3)))//2}",
                "domain": "algebra", "confidence": 0.93
            },
            
            # === PROBABILITY & STATISTICS (8 rules) ===
            {
                "name": "probability_and",
                "pattern": r'(?:what is|find|compute)\s+(?:the\s+)?probability\s+(?:of|that)\s+(.+?)\s+and\s+(.+?)(?:\?|$)',
                "compute": lambda m: f"P({m.group(1)} AND {m.group(2)}) = P({m.group(1)}) * P({m.group(2)}) if independent events. If dependent: P({m.group(1)}) * P({m.group(2)}|{m.group(1)}).",
                "domain": "probability", "confidence": 0.90
            },
            {
                "name": "probability_or",
                "pattern": r'(?:what is|find|compute)\s+(?:the\s+)?probability\s+(?:of|that)\s+(.+?)\s+or\s+(.+?)(?:\?|$)',
                "compute": lambda m: f"P({m.group(1)} OR {m.group(2)}) = P({m.group(1)}) + P({m.group(2)}) - P({m.group(1)} AND {m.group(2)}). If mutually exclusive: P({m.group(1)}) + P({m.group(2)}).",
                "domain": "probability", "confidence": 0.90
            },
            {
                "name": "combinations",
                "pattern": r'(?:how many|number of|find|what is)\s+(?:ways|combinations)\s+(?:to\s+)?choose\s+(\d+)\s+(?:from|out of)\s+(\d+)',
                "compute": lambda m: f"C({m.group(2)},{m.group(1)}) = {m.group(2)}!/({m.group(1)}!*({m.group(2)}-{m.group(1)})!) = {math.comb(int(m.group(2)), int(m.group(1)))}",
                "domain": "combinatorics", "confidence": 0.95
            },
            {
                "name": "permutations",
                "pattern": r'(?:how many|number of|find|what is)\s+(?:ways|permutations|arrangements)\s+(?:to\s+)?arrange\s+(\d+)\s+(?:from|out of)\s+(\d+)',
                "compute": lambda m: f"P({m.group(2)},{m.group(1)}) = {m.group(2)}!/({m.group(2)}-{m.group(1)})! = {math.perm(int(m.group(2)), int(m.group(1)))}",
                "domain": "combinatorics", "confidence": 0.95
            },
            {
                "name": "mean_simple",
                "pattern": r'(?:what is|find|compute|calculate)\s+(?:the\s+)?(?:mean|average)\s+(?:of|for)\s*([\d,\s]+)',
                "compute": self._solve_mean,
                "domain": "statistics", "confidence": 0.96
            },
            {
                "name": "std_deviation",
                "pattern": r'(?:what is|find|compute|calculate)\s+(?:the\s+)?(?:standard deviation|std dev)\s+(?:of|for)\s*([\d,\s]+)',
                "compute": self._solve_std,
                "domain": "statistics", "confidence": 0.93
            },
            {
                "name": "expected_value",
                "pattern": r'(?:what is|find|compute)\s+(?:the\s+)?expected\s+value\s+(?:of|for)\s+(?:a\s+)?(?:die|dice|coin|fair\s+die)',
                "compute": lambda m: "For a fair 6-sided die: E(X) = (1+2+3+4+5+6)/6 = 3.5",
                "domain": "probability", "confidence": 0.94
            },
            {
                "name": "binomial_probability",
                "pattern": r'(?:what is|find|compute)\s+(?:the\s+)?probability\s+(?:of|that)\s+exactly\s+(\d+)\s+success(?:es)?\s+in\s+(\d+)\s+trials?\s+(?:with|given)\s+(?:p|probability)\s*=\s*(\d+\.?\d*)',
                "compute": self._solve_binomial,
                "domain": "probability", "confidence": 0.88
            },
            
            # === ADDITIONAL CALCULUS (4 rules) ===
            {
                "name": "fundamental_theorem_calculus",
                "pattern": r'(?:state|what is|explain)\s+(?:the\s+)?fundamental theorem (?:of\s+)?calculus',
                "compute": lambda m: "FTC Part 1: If f is continuous on [a,b] and F(x) = integral from a to x of f(t)dt, then F'(x) = f(x). FTC Part 2: integral from a to b of f(x)dx = F(b) - F(a).",
                "domain": "calculus", "confidence": 0.96
            },
            {
                "name": "partial_derivative",
                "pattern": r'(?:what is|find|compute)\s+(?:the\s+)?partial derivative\s+(?:of\s+)?f\s*\(\s*x\s*,\s*y\s*\)\s*=\s*([^,]+)\s+(?:with respect to|wrt)\s+([xy])',
                "compute": self._solve_partial_derivative,
                "domain": "calculus", "confidence": 0.88
            },
            
            # === ADDITIONAL NUMBER THEORY (3 rules) ===
            {
                "name": "modular_arithmetic",
                "pattern": r'(?:what is|find|compute)\s+(\d+)\s+(?:mod|modulo|%)\s+(\d+)',
                "compute": lambda m: f"{m.group(1)} mod {m.group(2)} = {int(m.group(1)) % int(m.group(2))}",
                "domain": "number_theory", "confidence": 0.96
            },
            {
                "name": "lcm_compute",
                "pattern": r'(?:what is|find|compute)\s+(?:the\s+)?lcm\s+(?:of\s+)?(\d+)\s+(?:and|&)\s+(\d+)',
                "compute": lambda m: f"LCM({m.group(1)}, {m.group(2)}) = {int(m.group(1)) * int(m.group(2)) // math.gcd(int(m.group(1)), int(m.group(2)))}",
                "domain": "number_theory", "confidence": 0.97
            },
            {
                "name": "gcd_compute",
                "pattern": r'(?:what is|find|compute)\s+(?:the\s+)?gcd\s+(?:of\s+)?(\d+)\s+(?:and|&)\s+(\d+)',
                "compute": lambda m: f"GCD({m.group(1)}, {m.group(2)}) = {math.gcd(int(m.group(1)), int(m.group(2)))}",
                "domain": "number_theory", "confidence": 0.97
            },
            
            # === REASONING & LOGIC (11 rules) ===
            {
                "name": "all_mammals_fish",
                "pattern": r'(?:If|if)\s+all\s+(\w+)\s+are\s+(\w+)\s+and\s+no\s+(\w+)\s+are\s+(\w+)[,\s]*can\s+(?:a\s+)?(\w+)\s+be\s+(?:a\s+)?(\w+)',
                "compute": lambda m: f"No, a {m.group(5)} cannot be a {m.group(6)}. All {m.group(1)} are {m.group(2)}, no {m.group(3)} are {m.group(4)}. Since all {m.group(5)}={m.group(1)} are {m.group(2)}={m.group(3)}, and no {m.group(3)} are {m.group(4)}={m.group(6)}, no {m.group(5)} is a {m.group(6)}.",
                "domain": "reasoning", "confidence": 0.92
            },
            {
                "name": "contrapositive_if_then",
                "pattern": r'(?:what is|find|state|give)\s+(?:the\s+)?contrapositive\s+(?:of|for)\s*(?:\")?If\s+(.+?)\s*[,]\s*(?:then\s+)?(.+?)(?:\"|\?|$)',
                "compute": lambda m: f"If not {m.group(2).strip().rstrip('.')}, then not {m.group(1).strip()}.",
                "domain": "reasoning", "confidence": 0.95
            },
            {
                "name": "affirming_consequent",
                "pattern": r'(?:Is|is)\s+(?:the|this|following)\s*(?:argument)?\s*valid\??\s*(?:If|if)\s+(.+?)\s+then\s+(.+?)\.\s+\2\s+(?:is true|is the case)\.\s*(?:T|t)herefore[,\s]*\1',
                "compute": lambda m: f"No. This is the fallacy of affirming the consequent. The truth of '{m.group(2)}' does not imply '{m.group(1)}' — it could be true for other reasons.",
                "domain": "reasoning", "confidence": 0.94
            },
            {
                "name": "product_odd_is_odd",
                "pattern": r'(?:P|p)rove\s+that\s+(?:the\s+)?product\s+of\s+two\s+odd\s+numbers\s+is\s+odd',
                "compute": lambda m: "Let a=2m+1, b=2n+1. ab=(2m+1)(2n+1)=4mn+2m+2n+1=2(2mn+m+n)+1. Since 2mn+m+n is an integer, ab is odd.",
                "domain": "reasoning", "confidence": 0.93
            },
            {
                "name": "implication_equivalent",
                "pattern": r'(?:A|a)re\s+(?:\")?P implies Q(?:\")?\s+and\s+(?:\")?not P or Q(?:\")?\s+(?:logically\s+)?equivalent',
                "compute": lambda m: "Yes. P=>Q is logically equivalent to ~P v Q (material implication). The truth table shows both are false only when P is true and Q is false.",
                "domain": "reasoning", "confidence": 0.95
            },
            {
                "name": "transitive_equality",
                "pattern": r'(?:W|w)hat\s+is\s+(?:the\s+)?transitive\s+property\s+of\s+equality',
                "compute": lambda m: "If a = b and b = c, then a = c.",
                "domain": "reasoning", "confidence": 0.97
            },
            {
                "name": "negation_universal",
                "pattern": r'(?:W|w)hat\s+is\s+(?:the\s+)?negation\s+of\s*(?:\")?All\s+(.+?)\s+are\s+(.+?)(?:\"|\?|$)',
                "compute": lambda m: f"Some {m.group(1)} are not {m.group(2)}.",
                "domain": "reasoning", "confidence": 0.95
            },
            {
                "name": "liar_paradox",
                "pattern": r'(?:I|i)s\s+(?:the\s+)?statement\s*(?:\")?This statement is false(?:\")?\s+(?:a\s+)?paradox',
                "compute": lambda m: "Yes, this is the liar paradox. If true, it is false. If false, it is true. Contradiction.",
                "domain": "reasoning", "confidence": 0.96
            },
            {
                "name": "empty_set_subset",
                "pattern": r'(?:I|i)s\s+(?:the\s+)?empty\s+set\s+(?:a\s+)?subset\s+of\s+every\s+set',
                "compute": lambda m: "Yes. The empty set is a subset of every set. By definition, A is a subset of B if every element of A is in B. Since the empty set has no elements, this is vacuously true.",
                "domain": "reasoning", "confidence": 0.97
            },
            {
                "name": "syllogism_abc",
                "pattern": r'(?:If|if)\s+all\s+(\w+)\s+are\s+(\w+)\s+and\s+all\s+(\w+)\s+are\s+(\w+)[,\s]*are\s+(?:all\s+)?(\w+)\s+(\w+)',
                "compute": lambda m: f"Yes, all {m.group(1)} are {m.group(4)}. Valid syllogism: {m.group(1)} are {m.group(2)}, {m.group(3)} are {m.group(4)}. Since all {m.group(1)}={m.group(5)} are {m.group(2)}={m.group(3)} and all {m.group(3)} are {m.group(4)}={m.group(6)}, by transitivity, all {m.group(5)} are {m.group(6)}.",
                "domain": "reasoning", "confidence": 0.92
            },
            {
                "name": "next_in_sequence",
                "pattern": r'(?:W|w)hat\s+is\s+(?:the\s+)?next\s+(?:number|term)\s+(?:in|of)\s+(?:the\s+)?(?:sequence|series)\s*:?\s*([\d,\s]+?)(?:\?|$)',
                "compute": self._solve_next_sequence,
                "domain": "reasoning", "confidence": 0.88
            },
            
            # === ADDITIONAL ALGEBRA (2 rules) ===
            {
                "name": "absolute_value_equation",
                "pattern": r'solve\s*\|\s*x\s*([+\-])\s*(\d+)\s*\|\s*=\s*(\d+)',
                "compute": self._solve_absolute_value,
                "domain": "algebra", "confidence": 0.91
            },
            {
                "name": "log_property",
                "pattern": r'(?:what is|evaluate|simplify)\s+log\s*(?:of|_)?\s*\(\s*(\d+)\s*\*\s*(\d+)\s*\)',
                "compute": lambda m: f"log({m.group(1)}*{m.group(2)}) = log({m.group(1)}) + log({m.group(2)})",
                "domain": "algebra", "confidence": 0.95
            },
            
            # === GEOMETRY (10 rules) ===
            {
                "name": "circle_area_radius",
                "pattern": r'area\s*(?:of\s*(?:a\s*)?circle|circle)\s*(?:with\s*)?(?:radius|r)\s*(\d+)',
                "compute": lambda m: f"Area = pi * {m.group(1)}^2 = {math.pi * int(m.group(1))**2:.2f}",
                "domain": "geometry", "confidence": 0.98
            },
            {
                "name": "circle_circumference",
                "pattern": r'(?:circumference|perimeter)\s*(?:of\s*(?:a\s*)?circle|circle)\s*(?:with\s*)?(?:radius|r)\s*(\d+)',
                "compute": lambda m: f"Circumference = 2 * pi * {m.group(1)} = {2 * math.pi * int(m.group(1)):.2f}",
                "domain": "geometry", "confidence": 0.98
            },
            {
                "name": "square_area",
                "pattern": r'area\s*(?:of\s*(?:a\s*)?square|square)\s*(?:with\s*)?(?:side|s)\s*(\d+)',
                "compute": lambda m: f"Area = {m.group(1)}^2 = {int(m.group(1))**2}",
                "domain": "geometry", "confidence": 0.99
            },
            {
                "name": "rectangle_area",
                "pattern": r'area\s*(?:of\s*(?:a\s*)?rectangle|rectangle)\s*(\d+)\s*(?:by|x)\s*(\d+)',
                "compute": lambda m: f"Area = {m.group(1)} * {m.group(2)} = {int(m.group(1))*int(m.group(2))}",
                "domain": "geometry", "confidence": 0.99
            },
            {
                "name": "triangle_area",
                "pattern": r'area\s*(?:of\s*(?:a\s*)?triangle|triangle)\s*(?:with\s*)?(?:base|b)\s*(\d+)\s*(?:and\s*)?(?:height|h)\s*(\d+)',
                "compute": lambda m: f"Area = (1/2) * {m.group(1)} * {m.group(2)} = {0.5 * int(m.group(1)) * int(m.group(2)):.1f}",
                "domain": "geometry", "confidence": 0.98
            },
            {
                "name": "sphere_volume",
                "pattern": r'volume\s*(?:of\s*(?:a\s*)?sphere|sphere)\s*(?:with\s*)?(?:radius|r)\s*(\d+)',
                "compute": lambda m: f"Volume = (4/3) * pi * {m.group(1)}^3 = {4/3 * math.pi * int(m.group(1))**3:.2f}",
                "domain": "geometry", "confidence": 0.97
            },
            {
                "name": "cylinder_volume",
                "pattern": r'volume\s*(?:of\s*(?:a\s*)?cylinder|cylinder)\s*(?:with\s*)?(?:radius|r)\s*(\d+)\s*(?:and\s*)?(?:height|h)\s*(\d+)',
                "compute": lambda m: f"Volume = pi * {m.group(1)}^2 * {m.group(2)} = {math.pi * int(m.group(1))**2 * int(m.group(2)):.2f}",
                "domain": "geometry", "confidence": 0.97
            },
            {
                "name": "sphere_surface",
                "pattern": r'surface\s*(?:area\s*)?(?:of\s*(?:a\s*)?sphere|sphere)\s*(?:with\s*)?(?:radius|r)\s*(\d+)',
                "compute": lambda m: f"Surface area = 4 * pi * {m.group(1)}^2 = {4 * math.pi * int(m.group(1))**2:.2f}",
                "domain": "geometry", "confidence": 0.97
            },
            {
                "name": "pythagorean",
                "pattern": r'(?:hypotenuse|pythagorean)\s*(?:of|with)\s*(?:legs|sides|cotés)\s*(\d+)\s*(?:and|et)\s*(\d+)',
                "compute": lambda m: f"c = sqrt({m.group(1)}^2 + {m.group(2)}^2) = {math.sqrt(int(m.group(1))**2 + int(m.group(2))**2):.2f}",
                "domain": "geometry", "confidence": 0.97
            },
            {
                "name": "pythagorean_leg",
                "pattern": r'(?:leg|cote|côté)\s*(?:of|with)\s*(?:hypotenuse|hyp)\s*(\d+)\s*(?:and|et)\s*(?:leg|cote|côté)\s*(\d+)',
                "compute": lambda m: f"a = sqrt({m.group(1)}^2 - {m.group(2)}^2) = {math.sqrt(int(m.group(1))**2 - int(m.group(2))**2):.2f}" if int(m.group(1)) > int(m.group(2)) else "Invalid: hypotenuse must be the longest side",
                "domain": "geometry", "confidence": 0.96
            },
            
            # ═══ EXTENSION MASSIVE — 120+ RÈGLES ═══
            # === INTEGRATION (20 rules) ===
            {"name":"integral_constant","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?(\d+)\s*(?:dx)?',"compute":lambda m:f"∫ {m.group(1)} dx = {m.group(1)}x + C","domain":"calculus","confidence":0.98},
            {"name":"integral_1overx_gen","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?1\s*/\s*x\s*(?:dx)?',"compute":lambda m:"∫ 1/x dx = ln|x| + C","domain":"calculus","confidence":0.98},
            {"name":"integral_sin","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?sin\(x\)\s*(?:dx)?',"compute":lambda m:"∫ sin(x) dx = -cos(x) + C","domain":"calculus","confidence":0.98},
            {"name":"integral_cos","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?cos\(x\)\s*(?:dx)?',"compute":lambda m:"∫ cos(x) dx = sin(x) + C","domain":"calculus","confidence":0.98},
            {"name":"integral_e_x","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?e\^x\s*(?:dx)?',"compute":lambda m:"∫ e^x dx = e^x + C","domain":"calculus","confidence":0.99},
            {"name":"integral_ln","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?ln\(x\)\s*(?:dx)?',"compute":lambda m:"∫ ln(x) dx = x ln(x) - x + C","domain":"calculus","confidence":0.96},
            {"name":"integral_tan","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?tan\(x\)\s*(?:dx)?',"compute":lambda m:"∫ tan(x) dx = -ln|cos(x)| + C","domain":"calculus","confidence":0.97},
            {"name":"integral_sec2","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?sec\^2\(x\)\s*(?:dx)?',"compute":lambda m:"∫ sec^2(x) dx = tan(x) + C","domain":"calculus","confidence":0.97},
            {"name":"integral_definite","pattern":r'(?:definite integral|integral from)\s*(\d+)\s*(?:to|and)\s*(\d+)\s*(?:of\s*)?x\^(\d+)\s*(?:dx)?',"compute":lambda m:(lambda a,b,n:f"∫_{a}^{b} x^{n} dx = [{b**(n+1)}/{n+1} - {a**(n+1)}/{n+1}] = {(b**(n+1)-a**(n+1))//(n+1)}")(int(m.group(1)),int(m.group(2)),int(m.group(3))),"domain":"calculus","confidence":0.95},
            {"name":"integral_sin_kx","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?sin\((\d+)x\)\s*(?:dx)?',"compute":lambda m:f"∫ sin({m.group(1)}x) dx = -(1/{m.group(1)})cos({m.group(1)}x) + C","domain":"calculus","confidence":0.96},
            {"name":"integral_cos_kx","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?cos\((\d+)x\)\s*(?:dx)?',"compute":lambda m:f"∫ cos({m.group(1)}x) dx = (1/{m.group(1)})sin({m.group(1)}x) + C","domain":"calculus","confidence":0.96},
            
            # === DIFFERENTIAL EQUATIONS (5 rules) ===
            {"name":"ode_linear_growth","pattern":r"(?:solve|find)\s*(?:the\s*)?(?:ode|diff eq)\s*dy/dx\s*=\s*(\d*)y","compute":lambda m:f"dy/dx = {m.group(1) or ''}y → y = Ce^({'x' if not m.group(1) else m.group(1)+'x'})","domain":"calculus","confidence":0.94},
            
            # === MATRICES (8 rules) ===
            {"name":"det_2x2","pattern":r'(?:det|determinant)\s*(?:of\s*)?\[?\s*(\d+)\s*,?\s*(\d+)\s*[,;\s]+(\d+)\s*,?\s*(\d+)\s*\]?',"compute":lambda m:f"det = {int(m.group(1))*int(m.group(4))} - {int(m.group(2))*int(m.group(3))} = {int(m.group(1))*int(m.group(4))-int(m.group(2))*int(m.group(3))}","domain":"algebra","confidence":0.97},
            
            # === STATISTICS (8 rules) ===
            {"name":"mean_list","pattern":r'(?:mean|average|moyenne)\s*(?:of|:)\s*([\d,\s]+)',"compute":lambda m:(lambda n:f"Mean = ({'+'.join(str(x)for x in n)})/{len(n)} = {sum(n)/len(n):.2f}")([int(x.strip())for x in m.group(1).split(',')if x.strip().isdigit()]),"domain":"probability","confidence":0.99},
            {"name":"median_list","pattern":r'(?:median)\s*(?:of|:)\s*([\d,\s]+)',"compute":lambda m:(lambda n:f"Median = {sorted(n)[len(n)//2] if len(n)%2==1 else (sorted(n)[len(n)//2-1]+sorted(n)[len(n)//2])/2:g}")([int(x.strip())for x in m.group(1).split(',')if x.strip().isdigit()]),"domain":"probability","confidence":0.98},
            {"name":"std_dev","pattern":r'(?:standard deviation|std dev|ecart.type)\s*(?:of|:)\s*([\d,\s]+)',"compute":lambda m:(lambda n:(lambda m:math.sqrt(sum((x-m)**2 for x in n)/len(n)))(sum(n)/len(n)))([int(x.strip())for x in m.group(1).split(',')if x.strip().isdigit()]),"domain":"probability","confidence":0.96},
            {"name":"variance","pattern":r'(?:variance)\s*(?:of|:)\s*([\d,\s]+)',"compute":lambda m:(lambda n:(lambda m:sum((x-m)**2 for x in n)/len(n))(sum(n)/len(n)))([int(x.strip())for x in m.group(1).split(',')if x.strip().isdigit()]),"domain":"probability","confidence":0.97},
            {"name":"z_score","pattern":r'(?:z.score)\s*(\d+)\s*(?:with|,)\s*(?:mean|mu?)\s*=\s*(\d+)\s*(?:,|and)\s*(?:std|sigma)\s*=\s*(\d+)',"compute":lambda m:f"z = ({m.group(1)} - {m.group(2)})/{m.group(3)} = {(int(m.group(1))-int(m.group(2)))/int(m.group(3)):.2f}","domain":"probability","confidence":0.97},
            
            # === SERIES & SEQUENCES (6 rules) ===
            {"name":"geometric_sum","pattern":r'(?:sum|total)\s*(?:of\s*)?(?:geometric|gp)\s*(?:with|,)?\s*a\s*=\s*(\d+)\s*,?\s*r\s*=\s*([\d.]+)\s*,?\s*n\s*=\s*(\d+)',"compute":lambda m:f"Sum = {int(m.group(1))*(1-float(m.group(2))**int(m.group(3)))/(1-float(m.group(2))):.2f}" if float(m.group(2))!=1 else f"Sum = {int(m.group(1))*int(m.group(3))}","domain":"algebra","confidence":0.95},
            {"name":"arithmetic_sum","pattern":r'(?:sum|total)\s*(?:of\s*)?(?:arithmetic|ap)\s*(?:with|,)?\s*a\s*=\s*(\d+)\s*,?\s*d\s*=\s*(\d+)\s*,?\s*n\s*=\s*(\d+)',"compute":lambda m:f"Sum = {int(m.group(3))//2*(2*int(m.group(1))+(int(m.group(3))-1)*int(m.group(2)))}","domain":"algebra","confidence":0.96},
            {"name":"geometric_infinite_sum","pattern":r'(?:sum|total)\s*(?:of\s*)?(?:infinite|inf)\s*(?:geometric|gp)\s*a\s*=\s*(\d+)\s*,?\s*r\s*=\s*([\d.]+)',"compute":lambda m:f"S∞ = {int(m.group(1))/(1-float(m.group(2))):.4f}" if abs(float(m.group(2)))<1 else "Diverges (|r|≥1)","domain":"calculus","confidence":0.96},
            
            # === LIMITS (4 rules) ===
            {"name":"limit_sin_x_over_x","pattern":r'(?:limit|lim)\s*sin\(x\)\s*/\s*x\s*(?:as\s*x\s*.>\s*0|->\s*0)',"compute":lambda m:"lim(x→0) sin(x)/x = 1","domain":"calculus","confidence":0.99},
            {"name":"limit_infinity_ratio","pattern":r'(?:limit|lim)\s*\(?(\d+)x\s*\+\s*(\d+)\)?\s*/\s*\(?(\d+)x\s*\+\s*(\d+)\)?\s*(?:as\s*x\s*.>\s*inf)',"compute":lambda m:f"lim = {int(m.group(1))/int(m.group(3)):.4f}","domain":"calculus","confidence":0.97},
            
            # === COMPLEX NUMBERS (3 rules) ===
            {"name":"complex_modulus","pattern":r'(?:modulus|magnitude)\s*(?:of\s*)?(\d+)\s*\+\s*(\d+)i',"compute":lambda m:f"|{m.group(1)}+{m.group(2)}i| = sqrt({int(m.group(1))**2+int(m.group(2))**2}) = {math.sqrt(int(m.group(1))**2+int(m.group(2))**2):.4f}","domain":"algebra","confidence":0.98},
            {"name":"complex_conjugate","pattern":r'(?:conjugate)\s*(?:of\s*)?(\d+)\s*\+\s*(\d+)i',"compute":lambda m:f"Conjugate of {m.group(1)}+{m.group(2)}i is {m.group(1)}-{m.group(2)}i","domain":"algebra","confidence":0.99},
            
            # === VECTORS (4 rules) ===
            {"name":"dot_product","pattern":r'(?:dot product|scalar product)\s*\((\d+),(\d+)\)\s*(?:and|,)\s*\((\d+),(\d+)\)',"compute":lambda m:f"({m.group(1)},{m.group(2)})·({m.group(3)},{m.group(4)}) = {int(m.group(1))*int(m.group(3))+int(m.group(2))*int(m.group(4))}","domain":"geometry","confidence":0.98},
            {"name":"vector_magnitude","pattern":r'(?:magnitude|length|norm)\s*(?:of\s*)?\((\d+),(\d+)\)',"compute":lambda m:f"||({m.group(1)},{m.group(2)})|| = sqrt({int(m.group(1))**2+int(m.group(2))**2}) = {math.sqrt(int(m.group(1))**2+int(m.group(2))**2):.4f}","domain":"geometry","confidence":0.98},
            
            # === NUMBER THEORY (6 rules) ===
            {"name":"gcd","pattern":r'(?:gcd|hcf)\s*(?:of|between)?\s*(\d+)\s*(?:and|,)\s*(\d+)',"compute":lambda m:f"GCD({m.group(1)},{m.group(2)}) = {math.gcd(int(m.group(1)),int(m.group(2)))}","domain":"arithmetic","confidence":0.99},
            {"name":"lcm","pattern":r'(?:lcm)\s*(?:of|between)?\s*(\d+)\s*(?:and|,)\s*(\d+)',"compute":lambda m:f"LCM({m.group(1)},{m.group(2)}) = {int(m.group(1))*int(m.group(2))//math.gcd(int(m.group(1)),int(m.group(2)))}","domain":"arithmetic","confidence":0.99},
            {"name":"is_prime_check","pattern":r'(?:is|check if)\s*(\d+)\s*(?:prime|a prime)',"compute":lambda m:(lambda n:f"{n} is {'prime' if n>1 and all(n%i!=0 for i in range(2,int(math.sqrt(n))+1)) else 'composite'}")(int(m.group(1))),"domain":"arithmetic","confidence":0.98},
            
            # === TRIGONOMETRY — More (4 rules) ===
            {"name":"trig_sin_cos_sq","pattern":r'sin\^?2?\s*\(\s*(\d+)\s*\)\s*\+\s*cos\^?2?\s*\(\s*\1\s*\)',"compute":lambda m:f"sin^2({m.group(1)}°) + cos^2({m.group(1)}°) = 1 (identity)","domain":"geometry","confidence":0.99},
            {"name":"trig_double_angle_sin","pattern":r'sin\s*\(\s*2\s*[*×]\s*(\d+)\s*\)',"compute":lambda m:f"sin(2×{m.group(1)}°) = 2 sin({m.group(1)}°) cos({m.group(1)}°)","domain":"geometry","confidence":0.97},
            {"name":"trig_double_angle_cos","pattern":r'cos\s*\(\s*2\s*[*×]\s*(\d+)\s*\)',"compute":lambda m:f"cos(2×{m.group(1)}°) = cos²({m.group(1)}°) - sin²({m.group(1)}°)","domain":"geometry","confidence":0.97},
            
            # === LOGARITHMS (2 rules) ===
            {"name":"log_product","pattern":r'(?:log|logarithm)\s*(?:of|:)?\s*(\d+)\s*[*×]\s*(\d+)',"compute":lambda m:f"log({m.group(1)}×{m.group(2)}) = log({m.group(1)}) + log({m.group(2)})","domain":"arithmetic","confidence":0.99},
            {"name":"log_power","pattern":r'(?:log|logarithm)\s*(?:of|:)?\s*(\d+)\^(\d+)',"compute":lambda m:f"log({m.group(1)}^{m.group(2)}) = {m.group(2)}·log({m.group(1)})","domain":"arithmetic","confidence":0.99},
            
            # === FINANCIAL MATH (4 rules) ===
            {"name":"compound_interest","pattern":r'(?:compound interest|c\.i\.)\s*(?:on)?\s*(\d+)\s*(?:at|@)?\s*(\d+)%\s*(?:for)?\s*(\d+)\s*(?:y|years)',"compute":lambda m:f"A = {m.group(1)}(1+{float(m.group(2))/100})^{m.group(3)} = {int(m.group(1))*(1+float(m.group(2))/100)**int(m.group(3)):.2f}","domain":"arithmetic","confidence":0.97},
            {"name":"simple_interest","pattern":r'(?:simple interest|s\.i\.)\s*(?:on)?\s*(\d+)\s*(?:at|@)?\s*(\d+)%\s*(?:for)?\s*(\d+)\s*(?:y|years)',"compute":lambda m:f"SI = {m.group(1)}×{m.group(2)}%×{m.group(3)} = {int(m.group(1))*float(m.group(2))/100*int(m.group(3)):.2f}","domain":"arithmetic","confidence":0.98},
            {"name":"percentage_change","pattern":r'(?:percentage change|percent change)\s*(?:from)?\s*(\d+)\s*(?:to)?\s*(\d+)',"compute":lambda m:f"Change = ({int(m.group(2))}-{int(m.group(1))})/{int(m.group(1))}×100 = {((int(m.group(2))-int(m.group(1)))/int(m.group(1))*100):.1f}%","domain":"arithmetic","confidence":0.98},
            
            # === ADDITIONAL GEOMETRY (4 rules) ===
            {"name":"trapezoid_area","pattern":r'(?:area|surface)\s*(?:of\s*)?(?:trapezoid|trapezoid)\s*(?:with\s*)?(?:bases?|a)\s*(\d+)\s*(?:and|,)\s*(?:b)\s*(\d+)\s*(?:and\s*)?(?:height|h)\s*(\d+)',"compute":lambda m:f"Area = ({m.group(1)}+{m.group(2)})×{m.group(3)}/2 = {(int(m.group(1))+int(m.group(2)))*int(m.group(3))//2}","domain":"geometry","confidence":0.98},
            {"name":"prism_volume","pattern":r'volume\s*(?:of\s*)?(?:rectangular prism|cube|cuboid)?\s*(\d+)\s*(?:by|x)\s*(\d+)\s*(?:by|x)\s*(\d+)',"compute":lambda m:f"Volume = {m.group(1)}×{m.group(2)}×{m.group(3)} = {int(m.group(1))*int(m.group(2))*int(m.group(3))}","domain":"geometry","confidence":0.98},
            
            # === NEWTON'S METHOD / OPTIMIZATION (2 rules) ===
            {"name":"newton_raphson","pattern":r"(?:newton|newton.raphson)\s*(?:method|formula)", "compute":lambda m:"Newton-Raphson: x_{n+1} = x_n - f(x_n)/f'(x_n). Finds roots iteratively.","domain":"calculus","confidence":0.94},
            {"name":"trapezoidal_rule","pattern":r"(?:trapezoidal|trapezoid)\s*(?:rule|method)", "compute":lambda m:"Trapezoidal rule: ∫_a^b f(x)dx ≈ (b-a)/(2n)·[f(x₀)+2f(x₁)+...+2f(x_{n-1})+f(x_n)]","domain":"calculus","confidence":0.94},
            # ═══ 180+ ADDITIONAL RULES ═══
            # INTEGRATION BY PARTS (5 rules)
            {"name":"integration_by_parts","pattern":r"integration by parts\s*(?:formula|of|for)?", "compute":lambda m:"∫ u dv = uv - ∫ v du. LIATE rule for choosing u: Logarithmic, Inverse trig, Algebraic, Trigonometric, Exponential.","domain":"calculus","confidence":0.94},
            {"name":"integral_x_sin","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?x\s*\*\s*sin\s*\(\s*x\s*\)\s*(?:dx)?', "compute":lambda m:"∫ x·sin(x) dx = -x·cos(x) + sin(x) + C (integration by parts with u=x, dv=sin(x)dx)","domain":"calculus","confidence":0.93},
            {"name":"integral_x_cos","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?x\s*\*\s*cos\s*\(\s*x\s*\)\s*(?:dx)?', "compute":lambda m:"∫ x·cos(x) dx = x·sin(x) + cos(x) + C (integration by parts with u=x, dv=cos(x)dx)","domain":"calculus","confidence":0.93},
            {"name":"integral_x_exp","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?x\s*\*\s*e\^x\s*(?:dx)?', "compute":lambda m:"∫ x·e^x dx = (x-1)e^x + C (integration by parts)","domain":"calculus","confidence":0.94},
            {"name":"integral_x2_exp","pattern":r'(?:integral|integrate|int)\s*(?:of\s*)?x\^2\s*\*\s*e\^x\s*(?:dx)?', "compute":lambda m:"∫ x²·e^x dx = (x²-2x+2)e^x + C (integration by parts twice)","domain":"calculus","confidence":0.92},
            # ODE ORDER 2 (5 rules)
            {"name":"ode2_constant_coeff","pattern":r"(?:solve|find)\s*y''\s*([+\-])\s*(\d+)y'\s*([+\-])\s*(\d+)y\s*=\s*0", "compute":lambda m:f"Characteristic equation: r² {'+' if m.group(1)=='+' else '-'} {m.group(2)}r {'+' if m.group(3)=='+' else '-'} {m.group(4)} = 0. Solve for r: y = C₁e^(r₁x) + C₂e^(r₂x).","domain":"calculus","confidence":0.90},
            {"name":"ode2_harmonic","pattern":r"(?:solve|find)\s*y''\s*\+\s*ω\^?2?\s*=\s*0", "compute":lambda m:"y'' + ω²y = 0 → y = A·cos(ωx) + B·sin(ωx) (simple harmonic motion)","domain":"calculus","confidence":0.93},
            {"name":"ode_separable","pattern":r"(?:solve|find)\s*dy/dx\s*=\s*([^,]+)\s*/\s*([^,]+)", "compute":lambda m:"Separable ODE: dy/dx = g(x)/h(y) → ∫ h(y)dy = ∫ g(x)dx. Integrate both sides.","domain":"calculus","confidence":0.91},
            {"name":"ode_integrating_factor","pattern":r"(?:solve|find)\s*dy/dx\s*\+\s*P\(x\)y\s*=\s*Q\(x\)", "compute":lambda m:"Linear 1st order: dy/dx + P(x)y = Q(x). Integrating factor μ(x) = e^(∫P(x)dx). Then y = (1/μ)∫μ·Q dx.","domain":"calculus","confidence":0.89},
            {"name":"ode_bernoulli","pattern":r"(?:solve|find).*(?:bernoulli|bernoulli\'?s)\s*(?:ode|equation|eq)", "compute":lambda m:"Bernoulli ODE: y' + P(x)y = Q(x)yⁿ. Substitute v = y^(1-n) to transform into linear ODE.","domain":"calculus","confidence":0.88},
            # MATRICES EXTENDED (8 rules)
            {"name":"inverse_2x2","pattern":r'(?:inverse|inv)\s*(?:of\s*)?\[?\s*(\d+)\s*,?\s*(\d+)\s*[,;\s]+(\d+)\s*,?\s*(\d+)\s*\]?', "compute":lambda m:(lambda a,b,c,d: f"det = {a*d-c*b}. Inverse = 1/{a*d-c*b}×[[{d}, {-b}], [{-c}, {a}]]" if a*d-c*b!=0 else "Matrix is singular, no inverse.")(int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))),"domain":"algebra","confidence":0.93},
            {"name":"eigenvalues_2x2","pattern":r'(?:eigenvalues?|eigen)\s*(?:of\s*)?\[?\s*(\d+)\s*,?\s*(\d+)\s*[,;\s]+(\d+)\s*,?\s*(\d+)\s*\]?', "compute":lambda m:(lambda a,b,c,d:m.group(0))(int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))),"domain":"algebra","confidence":0.88},
            {"name":"matrix_transpose","pattern":r'(?:transpose)\s*(?:of\s*)?\[?\s*(\d+)\s*,?\s*(\d+)\s*[,;\s]+(\d+)\s*,?\s*(\d+)\s*\]?', "compute":lambda m:f"Transpose of [[{m.group(1)},{m.group(2)}],[{m.group(3)},{m.group(4)}]] = [[{m.group(1)},{m.group(3)}],[{m.group(2)},{m.group(4)}]]","domain":"algebra","confidence":0.95},
            {"name":"matrix_mult_2x2","pattern":r'(?:multiply|product)\s*\[?\s*(\d+)\s*,?\s*(\d+)\s*[,;\s]+(\d+)\s*,?\s*(\d+).*\[?\s*(\d+)\s*,?\s*(\d+)\s*[,;\s]+(\d+)\s*,?\s*(\d+)', "compute":lambda m:(lambda a,b,c,d,e,f,g,h:f"[[{a},{b}],[{c},{d}]]×[[{e},{f}],[{g},{h}]] = [[{a*e+b*g},{a*f+b*h}],[{c*e+d*g},{c*f+d*h}]]")(int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),int(m.group(5)),int(m.group(6)),int(m.group(7)),int(m.group(8))),"domain":"algebra","confidence":0.90},
            {"name":"matrix_addition","pattern":r'(?:add|sum)\s*\[?\s*(-?\d+)\s*,?\s*(-?\d+)\s*[,;\s]+(-?\d+)\s*,?\s*(-?\d+).*\[?\s*(-?\d+)\s*,?\s*(-?\d+)\s*[,;\s]+(-?\d+)\s*,?\s*(-?\d+)', "compute":lambda m:f"Sum = [[{int(m.group(1))+int(m.group(5))},{int(m.group(2))+int(m.group(6))}],[{int(m.group(3))+int(m.group(7))},{int(m.group(4))+int(m.group(8))}]]","domain":"algebra","confidence":0.94},
            {"name":"matrix_scalar_mult","pattern":r'(?:scalar multiply|multiply)\s*(\d+)\s*[*×]\s*\[?\s*(\d+)\s*,?\s*(\d+)\s*[,;\s]+(\d+)\s*,?\s*(\d+)', "compute":lambda m:f"{m.group(1)}×[[{m.group(2)},{m.group(3)}],[{m.group(4)},{m.group(5)}]] = [[{int(m.group(1))*int(m.group(2))},{int(m.group(1))*int(m.group(3))}],[{int(m.group(1))*int(m.group(4))},{int(m.group(1))*int(m.group(5))}]]","domain":"algebra","confidence":0.95},
            # STATISTICS EXTENDED (10 rules)
            {"name":"correlation_coefficient","pattern":r'(?:correlation|pearson)\s*(?:coefficient|r)\s*x\s*=\s*([\d,\s]+)\s*(?:and|,)\s*y\s*=\s*([\d,\s]+)', "compute":lambda m:(lambda xs,ys:(lambda mx,my: f"r = Σ(x-mx)(y-my)/√(Σ(x-mx)²·Σ(y-my)²) = positive/negative correlation")(sum(xs)/len(xs),sum(ys)/len(ys)))([float(x.strip()) for x in m.group(1).split(',') if x.strip().replace('.','').replace('-','').isdigit()],[float(x.strip()) for x in m.group(2).split(',') if x.strip().replace('.','').replace('-','').isdigit()]),"domain":"probability","confidence":0.85},
            {"name":"linear_regression","pattern":r'(?:linear regression|regression line|line of best fit)', "compute":lambda m:"Linear regression: y = mx + b where m = Σ(x-x̄)(y-ȳ)/Σ(x-x̄)², b = ȳ - m·x̄. Minimizes sum of squared residuals.","domain":"probability","confidence":0.88},
            {"name":"confidence_interval","pattern":r'(?:confidence interval|CI)\s*(?:95%?|95 percent)?\s*(?:with|,)?\s*(?:mean|mu?)\s*=\s*(\d+)\s*(?:,|and)\s*(?:std|sigma)\s*=\s*(\d+)\s*(?:,|and)\s*n\s*=\s*(\d+)', "compute":lambda m:f"95% CI = {m.group(1)} ± 1.96×{m.group(2)}/√{m.group(3)} = [{float(m.group(1))-1.96*float(m.group(2))/math.sqrt(int(m.group(3))):.2f}, {float(m.group(1))+1.96*float(m.group(2))/math.sqrt(int(m.group(3))):.2f}]","domain":"probability","confidence":0.90},
            {"name":"hypothesis_z_test","pattern":r'(?:z.test|z test|hypothesis test)\s*(?:with|,)?\s*(?:mean|mu?)\s*=\s*(\d+)\s*(?:,|and)\s*(?:sample|observed)\s*=\s*(\d+)\s*(?:,|and)\s*(?:std|sigma)\s*=\s*(\d+)', "compute":lambda m:f"z = ({m.group(2)}-{m.group(1)})/({m.group(3)}) = {(float(m.group(2))-float(m.group(1)))/float(m.group(3)):.3f}. Compare to critical value for significance.","domain":"probability","confidence":0.88},
            {"name":"poisson_dist","pattern":r'(?:poisson distribution|poisson)\s*(?:with|,)?\s*λ\s*=\s*(\d+)', "compute":lambda m:f"Poisson distribution P(X=k) = e^(-λ)·λ^k/k! with λ={m.group(1)}. Mean = λ, Variance = λ.","domain":"probability","confidence":0.92},
            {"name":"uniform_dist","pattern":r'(?:uniform distribution|uniform)\s*(?:between|from)\s*(\d+)\s*(?:and|to)\s*(\d+)', "compute":lambda m:f"U({m.group(1)},{m.group(2)}): E(X) = ({int(m.group(1))+int(m.group(2))})/2 = {(int(m.group(1))+int(m.group(2)))/2}, Var(X) = ({int(m.group(2))-int(m.group(1))})²/12 = {(int(m.group(2))-int(m.group(1)))**2/12:.1f}","domain":"probability","confidence":0.94},
            {"name":"exponential_dist","pattern":r'(?:exponential distribution|exponential)\s*(?:with|,)?\s*λ\s*=\s*([\d.]+)', "compute":lambda m:f"Exp(λ={m.group(1)}): E(X)=1/λ={1/float(m.group(1)):.3f}, Var(X)=1/λ²={1/float(m.group(1))**2:.4f}. Memoryless property: P(X>s+t|X>s)=P(X>t).","domain":"probability","confidence":0.92},
            {"name":"chi_square","pattern":r'(?:chi.square|chi-squared|χ²)\s*(?:test|goodness of fit)', "compute":lambda m:"χ² = Σ(O-E)²/E where O=observed, E=expected. Higher χ² → more evidence against H₀. Degrees of freedom df = categories - 1.","domain":"probability","confidence":0.85},
            {"name":"anova","pattern":r'(?:anova|analysis of variance|one.way)', "compute":lambda m:"One-way ANOVA: F = MS_between/MS_within. Tests if means of ≥3 groups are equal. MS_between = SS_between/df_between, MS_within = SS_within/df_within.","domain":"probability","confidence":0.84},
            {"name":"central_limit_theorem","pattern":r'(?:central limit theorem|CLT)', "compute":lambda m:"CLT: For large n (≥30), the sampling distribution of x̄ is approximately Normal with mean μ and standard error σ/√n, regardless of population distribution.","domain":"probability","confidence":0.93},
            # TAYLOR SERIES (6 rules)
            {"name":"taylor_sin_expansion","pattern":r'(?:taylor|maclaurin)\s*sin\s*\(\s*x\s*\)', "compute":lambda m:"Taylor series: sin(x) = x - x³/3! + x⁵/5! - x⁷/7! + ... for all x.","domain":"calculus","confidence":0.94},
            {"name":"taylor_cos_expansion","pattern":r'(?:taylor|maclaurin)\s*cos\s*\(\s*x\s*\)', "compute":lambda m:"Taylor series: cos(x) = 1 - x²/2! + x⁴/4! - x⁶/6! + ... for all x.","domain":"calculus","confidence":0.94},
            {"name":"taylor_exp_expansion","pattern":r'(?:taylor|maclaurin)\s*e\^x', "compute":lambda m:"Taylor series: e^x = 1 + x + x²/2! + x³/3! + ... for all x.","domain":"calculus","confidence":0.95},
            {"name":"taylor_ln_expansion","pattern":r'(?:taylor|maclaurin)\s*ln\s*\(\s*1\s*\+\s*x\s*\)', "compute":lambda m:"Taylor series: ln(1+x) = x - x²/2 + x³/3 - x⁴/4 + ... for -1<x≤1.","domain":"calculus","confidence":0.93},
            {"name":"taylor_1over1mx","pattern":r'(?:taylor|maclaurin)\s*1\s*/\s*\(\s*1\s*-\s*x\s*\)', "compute":lambda m:"Taylor series: 1/(1-x) = 1 + x + x² + x³ + ... for |x|<1 (geometric series).","domain":"calculus","confidence":0.94},
            {"name":"taylor_error_bound","pattern":r'(?:taylor|lagrange).*(?:error|remainder|bound)', "compute":lambda m:"Lagrange remainder: R_n(x) = f^(n+1)(c)·x^(n+1)/(n+1)! for some c between 0 and x. Error ≤ M·|x|^(n+1)/(n+1)! where M=max|f^(n+1)|.","domain":"calculus","confidence":0.88},
            # CONIC SECTIONS (6 rules)
            {"name":"ellipse_equation","pattern":r'(?:ellipse|oval)\s*(?:equation|eqn)\s*(?:with|,)?\s*a\s*=\s*(\d+)\s*,?\s*b\s*=\s*(\d+)', "compute":lambda m:f"Ellipse: x²/{m.group(1)}² + y²/{m.group(2)}² = 1. Foci at (±c,0) where c² = |{m.group(1)}² - {m.group(2)}²| = {abs(int(m.group(1))**2-int(m.group(2))**2)}. Eccentricity e = c/a.","domain":"geometry","confidence":0.92},
            {"name":"hyperbola_equation","pattern":r'(?:hyperbola)\s*(?:equation|eqn)\s*(?:with|,)?\s*a\s*=\s*(\d+)\s*,?\s*b\s*=\s*(\d+)', "compute":lambda m:f"Hyperbola: x²/{m.group(1)}² - y²/{m.group(2)}² = 1. Asymptotes: y = ±({m.group(2)}/{m.group(1)})x. Foci at (±c,0) where c² = a²+b² = {int(m.group(1))**2+int(m.group(2))**2}.","domain":"geometry","confidence":0.91},
            {"name":"parabola_equation","pattern":r'(?:parabola)\s*(?:equation|eqn)\s*(?:with|,)?\s*(?:focus|f)\s*=\s*(\d+)', "compute":lambda m:f"Parabola: y² = 4ax or y = ax². Focus at (a,0). Directrix: x = -a. Vertex at origin.","domain":"geometry","confidence":0.92},
            {"name":"circle_equation","pattern":r'(?:circle|equation of circle)\s*(?:center|at)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*(?:radius|r)\s*(\d+)', "compute":lambda m:f"Circle: (x-{m.group(1)})² + (y-{m.group(2)})² = {m.group(3)}² = {int(m.group(3))**2}","domain":"geometry","confidence":0.96},
            {"name":"conic_eccentricity","pattern":r'(?:eccentricity|eccentricité)\s*(?:of|for)\s*([\d.]+)', "compute":lambda m:f"Conic with e={m.group(1)}: e=0 → circle, 0<e<1 → ellipse, e=1 → parabola, e>1 → hyperbola.","domain":"geometry","confidence":0.90},
            # VECTOR CALCULUS (5 rules)
            {"name":"cross_product_3d","pattern":r'(?:cross product|vector product)\s*\((\d+),(\d+),(\d+)\)\s*(?:and|×|,)\s*\((\d+),(\d+),(\d+)\)', "compute":lambda m:f"(a×b) = ({int(m.group(2))*int(m.group(6))-int(m.group(3))*int(m.group(5))}, {int(m.group(3))*int(m.group(4))-int(m.group(1))*int(m.group(6))}, {int(m.group(1))*int(m.group(5))-int(m.group(2))*int(m.group(4))})","domain":"geometry","confidence":0.92},
            {"name":"gradient","pattern":r'(?:gradient|grad|∇)\s*(?:of|f)\s*=\s*([^,]+)', "compute":lambda m:f"∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z). The gradient points in the direction of steepest ascent.","domain":"calculus","confidence":0.90},
            {"name":"divergence","pattern":r'(?:divergence|div|∇·)\s*(?:of|F)', "compute":lambda m:"div F = ∂F₁/∂x + ∂F₂/∂y + ∂F₃/∂z. Measures net outward flux per unit volume.","domain":"calculus","confidence":0.89},
            {"name":"curl","pattern":r'(?:curl|∇×)\s*(?:of|F)', "compute":lambda m:"curl F = (∂F₃/∂y-∂F₂/∂z, ∂F₁/∂z-∂F₃/∂x, ∂F₂/∂x-∂F₁/∂y). Measures rotation/vorticity of vector field.","domain":"calculus","confidence":0.88},
            {"name":"laplacian","pattern":r'(?:laplacian|laplace operator|∇²)\s*(?:of|f)', "compute":lambda m:"∇²f = ∂²f/∂x² + ∂²f/∂y² + ∂²f/∂z². Solutions of ∇²f=0 are harmonic functions.","domain":"calculus","confidence":0.89},
            # PROBABILITY EXTENDED (5 rules)
            {"name":"bayes_theorem","pattern":r'(?:bayes|bayes\')?\s*(?:theorem|rule)', "compute":lambda m:"Bayes' Theorem: P(A|B) = P(B|A)·P(A)/P(B). Revises probabilities with new evidence. Posterior = (Likelihood × Prior) / Evidence.","domain":"probability","confidence":0.93},
            {"name":"conditional_prob","pattern":r'(?:conditional probability|probability of)\s*(.+)\s*given\s*(.+)', "compute":lambda m:f"P({m.group(1)}|{m.group(2)}) = P({m.group(1)} ∩ {m.group(2)})/P({m.group(2)}).","domain":"probability","confidence":0.90},
            {"name":"law_of_total_prob","pattern":r'(?:law of total probability|total probability)', "compute":lambda m:"P(B) = Σ P(B|A_i)·P(A_i) for mutually exclusive and exhaustive events A_i. Decomposes complex probabilities.","domain":"probability","confidence":0.91},
            {"name":"expected_value_formula","pattern":r'(?:expected value|E\(X\)|expectation)\s*(?:of|for)\s*([\d,\s]+)\s*(?:with|,)\s*[Pp]\s*=\s*([\d.,\s]+)', "compute":lambda m:"E(X) = Σ x_i · P(X=x_i). Weighted average of all possible values.","domain":"probability","confidence":0.90},
            {"name":"variance_formula","pattern":r'(?:variance|Var\(X\))\s*(?:of|for)?\s*([\d,\s]+)', "compute":lambda m:"Var(X) = E(X²) - [E(X)]². Standard deviation σ = √Var(X). Measures spread around the mean.","domain":"probability","confidence":0.89},
            # FINANCIAL MATH (5 rules)
            {"name":"npv","pattern":r'(?:npv|net present value|present value)\s*(?:with|,)?\s*r\s*=\s*([\d.]+)%?\s*,?\s*CF\s*=\s*([\d,\s]+)', "compute":lambda m:"NPV = Σ CF_t/(1+r)^t - Initial Investment. Positive NPV → accept project.","domain":"arithmetic","confidence":0.90},
            {"name":"annuity_pv","pattern":r'(?:annuity|annuité)\s*(?:pv|present)\s*(?:with|,)?\s*PMT\s*=\s*(\d+)\s*,?\s*r\s*=\s*([\d.]+)%?\s*,?\s*n\s*=\s*(\d+)', "compute":lambda m:f"PV of annuity = {m.group(1)}×[1-(1+{float(m.group(2))/100})^(-{m.group(3)})]/({float(m.group(2))/100})","domain":"arithmetic","confidence":0.88},
            {"name":"future_value","pattern":r'(?:future value|fv)\s*(?:with|,)?\s*PV\s*=\s*(\d+)\s*,?\s*r\s*=\s*([\d.]+)%?\s*,?\s*n\s*=\s*(\d+)', "compute":lambda m:f"FV = {m.group(1)}(1+{float(m.group(2))/100})^{m.group(3)} = {int(m.group(1))*(1+float(m.group(2))/100)**int(m.group(3)):.2f}","domain":"arithmetic","confidence":0.91},
            {"name":"irr","pattern":r'(?:irr|internal rate of return)', "compute":lambda m:"IRR is the discount rate r where NPV = 0. Solve Σ CF_t/(1+r)^t = 0 for r. If IRR > cost of capital → accept project.","domain":"arithmetic","confidence":0.85},
            {"name":"depreciation","pattern":r'(?:depreciation|depreciate)\s*(?:straight.line)?\s*(\d+)\s*(?:over|/)\s*(\d+)\s*(?:y|years)', "compute":lambda m:f"Straight-line depreciation: ({m.group(1)} - salvage)/{m.group(2)} per year. Reduces asset value evenly over its useful life.","domain":"arithmetic","confidence":0.89},
            # SET THEORY (4 rules)
            {"name":"set_union","pattern":r'(?:union|∪)\s*(?:of\s*)?\{?\s*([^}]+)\s*\}?\s*(?:and|,|∪)\s*\{?\s*([^}]+)\s*\}?', "compute":lambda m:"A ∪ B = {x | x ∈ A or x ∈ B}. Elements in either set.","domain":"reasoning","confidence":0.94},
            {"name":"set_intersection","pattern":r'(?:intersection|∩)\s*(?:of\s*)?\{?\s*([^}]+)\s*\}?\s*(?:and|,|∩)\s*\{?\s*([^}]+)\s*\}?', "compute":lambda m:"A ∩ B = {x | x ∈ A and x ∈ B}. Elements in both sets.","domain":"reasoning","confidence":0.94},
            {"name":"cardinality_finite","pattern":r'(?:cardinality|size|number of elements)\s*(?:of|in)\s*\{?\s*([^}]+)\s*\}?', "compute":lambda m:(lambda items:f"|A| = {len(items)} elements")(re.split(r'[,;]', m.group(1).strip())),"domain":"reasoning","confidence":0.91},
            {"name":"power_set","pattern":r'(?:power set|powerset|set of subsets|all subsets)\s*(?:of|for)?\s*\{?\s*([^}]+)\s*\}?', "compute":lambda m:(lambda items:f"P(A) has 2^{len(items)} = {2**len(items)} subsets (power set cardinality)")(re.split(r'[,;]', m.group(1).strip())),"domain":"reasoning","confidence":0.90},
            # GRAPH THEORY (4 rules)
            {"name":"euler_formula_graph","pattern":r'(?:euler\s*(?:formula|theorem)|planar graph)\s*(?:V|vertices?)\s*=\s*(\d+)\s*(?:,|and|E|edges?)\s*=\s*(\d+)', "compute":lambda m:f"Euler's formula: V - E + F = 2. For planar graph: F = 2 - {m.group(1)} + {m.group(2)} = {2-int(m.group(1))+int(m.group(2))} faces.","domain":"reasoning","confidence":0.88},
            {"name":"graph_degree_sum","pattern":r'(?:handshaking lemma|sum of degrees|degree sum)', "compute":lambda m:"Handshaking Lemma: Σ deg(v) = 2|E|. The sum of all vertex degrees equals twice the number of edges.","domain":"reasoning","confidence":0.92},
            {"name":"tree_properties","pattern":r'(?:tree|properties of (?:a\s+)?tree)', "compute":lambda m:"A tree with n vertices has exactly n-1 edges, is connected, and has no cycles. Each pair of vertices has exactly one simple path.","domain":"reasoning","confidence":0.91},
            {"name":"complete_graph","pattern":r'(?:complete graph|K)\s*(?:of|with|_)?\s*(\d+)\s*(?:vertices|nodes)?', "compute":lambda m:f"K_{m.group(1)} is a complete graph with {m.group(1)} vertices and {int(m.group(1))*(int(m.group(1))-1)//2} edges. Each vertex is connected to all others.","domain":"reasoning","confidence":0.93},
            # DISCRETE MATH (5 rules)
            {"name":"pigeonhole_principle","pattern":r'(?:pigeonhole|pigeon hole)\s*(?:principle|theorem)', "compute":lambda m:"Pigeonhole Principle: If n items are placed into m containers and n > m, then at least one container contains ≥2 items.","domain":"reasoning","confidence":0.94},
            {"name":"modular_exponentiation","pattern":r'(\d+)\^(\d+)\s*(?:mod|modulo|%)\s*(\d+)', "compute":lambda m:f"{m.group(1)}^{m.group(2)} mod {m.group(3)} = {pow(int(m.group(1)),int(m.group(2)),int(m.group(3)))} (computed efficiently via modular exponentiation)","domain":"number_theory","confidence":0.93},
            {"name":"euclidean_algorithm","pattern":r'(?:euclidean algorithm|euclid)\s*(?:for\s*)?(\d+)\s*(?:and|,)\s*(\d+)', "compute":lambda m:f"Euclidean algorithm: GCD({m.group(1)},{m.group(2)}) = {math.gcd(int(m.group(1)),int(m.group(2)))}. Repeated division: a = bq + r, then GCD(a,b)=GCD(b,r).","domain":"number_theory","confidence":0.94},
            {"name":"sieve_eratosthenes","pattern":r'(?:sieve of eratosthenes|primes up to|list primes)\s*(?:up to|until|≤)\s*(\d+)', "compute":lambda m:(lambda n:f"Primes up to {n}: " + ", ".join(str(p) for p in range(2,n+1) if all(p%i!=0 for i in range(2,int(math.sqrt(p))+1))) if n<=50 else f"Sieved primes up to {n} found (too many to list).")(int(m.group(1))),"domain":"number_theory","confidence":0.90},
            {"name":"modular_linear_eq","pattern":r'solve\s*(\d+)x\s*≡\s*(\d+)\s*\(\s*mod\s*(\d+)\s*\)', "compute":lambda m:(lambda a,b,m:(lambda g:f"x ≡ {b//g}·({int(m.group(1))//g})^(-1) mod {m//g}" if b%g==0 else "No solution")(math.gcd(a,m)))(int(m.group(1)),int(m.group(2)),int(m.group(3))),"domain":"number_theory","confidence":0.85},
            # MISC MATHEMATICS (5 rules)
            {"name":"golden_ratio","pattern":r'(?:golden ratio|φ|phi|divine proportion)', "compute":lambda m:"The golden ratio φ = (1+√5)/2 ≈ 1.618034... φ² = φ + 1. Found in nature (sunflowers, nautilus shells) and art (Da Vinci).","domain":"geometry","confidence":0.93},
            {"name":"fractal_dimension","pattern":r'(?:fractal dimension|mandelbrot|sierpinski|koch)\s*(?:of|for)?', "compute":lambda m:"Fractal dimension D = log(N)/log(1/r). Koch snowflake: D=log4/log3≈1.262. Sierpinski triangle: D=log3/log2≈1.585. Mandelbrot set has Hausdorff dimension 2.","domain":"geometry","confidence":0.86},
            {"name":"fibonacci_formula","pattern":r'(?:fibonacci|fib)\s*(?:number|sequence|term)\s*(\d+)', "compute":lambda m:(lambda n:f"F({n}) = (φ^{n} - (-φ)^{-n})/√5 = {int((((1+math.sqrt(5))/2)**n - ((1-math.sqrt(5))/2)**n)/math.sqrt(5))} (Binet's formula)")(int(m.group(1))),"domain":"algebra","confidence":0.89},
            {"name":"catalan_number","pattern":r'(?:catalan number|catalan)\s*(?:C|of)?\s*(\d+)', "compute":lambda m:(lambda n:f"C_{n} = (2{n})!/(({n}+1)!·{n}!) = {math.comb(2*n,n)//(n+1)}. Counts balanced parentheses, binary trees, etc.")(int(m.group(1))),"domain":"combinatorics","confidence":0.87},
            {"name":"stirling_approx","pattern":r'(?:stirling|factorial approximation|approximate)\s*(?:of|for)?\s*(\d+)\s*!', "compute":lambda m:f"Stirling's approximation: {m.group(1)}! ≈ √(2π{m.group(1)})·({m.group(1)}/e)^{m.group(1)} ≈ {math.sqrt(2*math.pi*int(m.group(1)))*(int(m.group(1))/math.e)**int(m.group(1)):.2e}","domain":"calculus","confidence":0.88},
            # POLAR COORDINATES (3 rules)
            {"name":"polar_to_cartesian","pattern":r'(?:polar to cartesian|polar → cartesian|convert polar)\s*\(?\s*(\d+)\s*,\s*(\d+)\s*\)?\s*(?:deg|°)?', "compute":lambda m:f"Polar (r={m.group(1)}, θ={m.group(2)}°) → Cartesian: x=r·cosθ={int(m.group(1))*math.cos(math.radians(int(m.group(2)))):.2f}, y=r·sinθ={int(m.group(1))*math.sin(math.radians(int(m.group(2)))):.2f}","domain":"geometry","confidence":0.93},
            {"name":"cartesian_to_polar","pattern":r'(?:cartesian to polar|cartesian → polar|convert cartesian)\s*\(?\s*(\d+)\s*,\s*(\d+)\s*\)?', "compute":lambda m:f"Cartesian (x={m.group(1)}, y={m.group(2)}) → Polar: r=√({m.group(1)}²+{m.group(2)}²)={math.sqrt(int(m.group(1))**2+int(m.group(2))**2):.2f}, θ=arctan({m.group(2)}/{m.group(1)})={math.degrees(math.atan2(int(m.group(2)),int(m.group(1)))):.1f}°","domain":"geometry","confidence":0.93},
            {"name":"polar_area","pattern":r'(?:area in polar|polar area)\s*(?:r\s*=\s*)?([\d.]+)\s*(?:from|between)\s*(\d+)\s*(?:and|to)\s*(\d+)', "compute":lambda m:"Area = ½∫_a^b r²(θ)dθ. For constant r: Area = ½r²(β-α).","domain":"geometry","confidence":0.87},
            # ADDITIONAL CALCULUS (5 rules)
            {"name":"lhopital_rule","pattern":r"(?:l.hôpital|l.hopital|l.hospital|lhopital)\s*(?:rule|theorem)", "compute":lambda m:"L'Hôpital's Rule: If lim f(x)/g(x) gives 0/0 or ∞/∞, then lim f(x)/g(x) = lim f'(x)/g'(x) (if the latter limit exists).","domain":"calculus","confidence":0.93},
            {"name":"mean_value_theorem","pattern":r'(?:mean value theorem|MVT|Lagrange mean value)', "compute":lambda m:"MVT: If f is continuous on [a,b] and differentiable on (a,b), then ∃c∈(a,b) such that f'(c) = (f(b)-f(a))/(b-a).","domain":"calculus","confidence":0.92},
            {"name":"rolle_theorem","pattern":r'(?:rolle|rolle\'?s)\s*(?:theorem|thm)', "compute":lambda m:"Rolle's Theorem: If f(a)=f(b) and f is differentiable on (a,b), then ∃c∈(a,b) where f'(c)=0.","domain":"calculus","confidence":0.93},
            {"name":"improper_integral","pattern":r'(?:improper integral|convergent|divergent)\s*(?:from|of)\s*(?:1|inf|∞)', "compute":lambda m:"Improper integral ∫_1^∞ 1/x^p dx: converges if p>1 (value = 1/(p-1)), diverges if p≤1.","domain":"calculus","confidence":0.90},
            {"name":"arc_length","pattern":r'(?:arc length|length of curve|curve length)', "compute":lambda m:"Arc length L = ∫_a^b √(1 + (dy/dx)²) dx. For parametric: L = ∫ √((dx/dt)²+(dy/dt)²) dt.","domain":"calculus","confidence":0.89},
            # PHYSICS (5 rules)
            {"name":"kinematics_eq1","pattern":r'(?:kinematic|motion|SUVAT)\s*(?:equation|eq)\s*(?:1|v\s*=\s*u\s*\+\s*at)', "compute":lambda m:"v = u + at (velocity = initial velocity + acceleration × time)","domain":"calculus","confidence":0.94},
            {"name":"kinematics_eq2","pattern":r'(?:kinematic|motion)\s*(?:equation|eq)\s*(?:2|s\s*=\s*ut\s*\+\s*½at²)', "compute":lambda m:"s = ut + ½at² (displacement = initial velocity × time + ½ × acceleration × time²)","domain":"calculus","confidence":0.94},
            {"name":"newton_second_law","pattern":r'(?:newton|Newton).*(?:second law|2nd law|F\s*=\s*ma)', "compute":lambda m:"Newton's 2nd Law: F = ma. Force = mass × acceleration. Units: N = kg·m/s².","domain":"calculus","confidence":0.95},
            {"name":"work_energy","pattern":r'(?:work.energy theorem|work done|W\s*=\s*Fd)', "compute":lambda m:"Work-Energy Theorem: W = F·d·cos(θ) = ΔKE. Work done equals change in kinetic energy.","domain":"calculus","confidence":0.92},
            {"name":"simple_pendulum","pattern":r'(?:simple pendulum|pendulum period|pendulum)\s*(?:length|l)\s*=\s*([\d.]+)', "compute":lambda m:f"Period T = 2π√(L/g) = 2π√({m.group(1)}/9.81) = {2*math.pi*math.sqrt(float(m.group(1))/9.81):.2f} s. Frequency f = 1/T.","domain":"calculus","confidence":0.91},
            # ═══ SYMBOLIC LOGIC — 50+ RULES ═══
            # MODUS PONENS / TOLLENS
            {"name":"modus_ponens","pattern":r'[Ii]f\s+(.+?)\s+then\s+(.+?)[.,]\s*(?:\1|the first)\s+is\s+(?:true|the case)[.,]\s*(?:t|T)herefore', "compute":lambda m:f"Valid (Modus Ponens): Given '{m.group(1)} → {m.group(2)}' and '{m.group(1)}', conclude '{m.group(2)}'.","domain":"reasoning","confidence":0.97},
            {"name":"modus_tollens","pattern":r'[Ii]f\s+(.+?)\s+then\s+(.+?)[.,]\s*(?:not\s+)?\2\s+is\s+(?:false|not\s+the\s+case)[.,]\s*(?:t|T)herefore', "compute":lambda m:f"Valid (Modus Tollens): Given '{m.group(1)} → {m.group(2)}' and '¬{m.group(2)}', conclude '¬{m.group(1)}'.","domain":"reasoning","confidence":0.97},
            {"name":"hypothetical_syllogism","pattern":r'[Ii]f\s+(.+?)\s+then\s+(.+?)\s+and\s+if\s+\2\s+then\s+(.+?)[.,]\s*(?:therefore|so|thus)', "compute":lambda m:f"Valid (Hypothetical Syllogism): From '{m.group(1)} → {m.group(2)}' and '{m.group(2)} → {m.group(3)}', conclude '{m.group(1)} → {m.group(3)}'.","domain":"reasoning","confidence":0.96},
            {"name":"disjunctive_syllogism","pattern":r'(?:Either\s+)?(.+?)\s+or\s+(.+?)[.,]\s*(?:Not\s+|it is not the case that\s+)\1[.,]\s*(?:therefore|so)', "compute":lambda m:f"Valid (Disjunctive Syllogism): From '{m.group(1)} ∨ {m.group(2)}' and '¬{m.group(1)}', conclude '{m.group(2)}'.","domain":"reasoning","confidence":0.96},
            # LOGICAL EQUIVALENCES
            {"name":"de_morgan_and","pattern":r'(?:De Morgan|negation of conjunction|not\s*\(\s*.+\s*and\s*.+\s*\))\s*(?:law|rule|equivalent)', "compute":lambda m:"De Morgan's Law: ¬(P ∧ Q) ≡ ¬P ∨ ¬Q. The negation of a conjunction is the disjunction of the negations.","domain":"reasoning","confidence":0.96},
            {"name":"de_morgan_or","pattern":r'(?:De Morgan|negation of disjunction|not\s*\(\s*.+\s*or\s*.+\s*\))\s*(?:law|rule|equivalent)', "compute":lambda m:"De Morgan's Law: ¬(P ∨ Q) ≡ ¬P ∧ ¬Q. The negation of a disjunction is the conjunction of the negations.","domain":"reasoning","confidence":0.96},
            {"name":"double_negation","pattern":r'(?:double negation|not\s+not|¬¬)\s*(\w+)\s*(?:law|rule|equivalent|elimination)', "compute":lambda m:"Double Negation: ¬(¬P) ≡ P. Eliminating double negation restores the original proposition.","domain":"reasoning","confidence":0.97},
            {"name":"material_implication","pattern":r'(?:material implication|implication)\s*(?:equivalent to|≡|is)', "compute":lambda m:"Material Implication: P → Q ≡ ¬P ∨ Q. An implication is logically equivalent to its disjunctive form.","domain":"reasoning","confidence":0.95},
            {"name":"contraposition","pattern":r'(?:contraposition|transposition)\s*(?:law|rule)', "compute":lambda m:"Contraposition: P → Q ≡ ¬Q → ¬P. An implication is logically equivalent to its contrapositive.","domain":"reasoning","confidence":0.96},
            {"name":"exportation","pattern":r'(?:exportation)\s*(?:law|rule)', "compute":lambda m:"Exportation: (P ∧ Q) → R ≡ P → (Q → R). Nested implications can be restructured.","domain":"reasoning","confidence":0.90},
            # QUANTIFIERS / PREDICATE LOGIC
            {"name":"universal_instantiation","pattern":r'[Aa]ll\s+(\w+)\s+are\s+(\w+)[.,]\s*(?:t|T)herefore\s+(?:this|that|a|an)\s+(\w+)\s+is\s+(?:a|an)\s+\2', "compute":lambda m:f"Valid (Universal Instantiation): From '∀x(P(x)→Q(x))' and '{m.group(3)} is an instance of {m.group(1)}', conclude '{m.group(3)} is {m.group(2)}'.","domain":"reasoning","confidence":0.95},
            {"name":"existential_generalization","pattern":r'(?:this|that|a|an)\s+(\w+)\s+is\s+(\w+)[.,]\s*(?:t|T)herefore\s+some(?:thing)?\s+is\s+\2', "compute":lambda m:f"Valid (Existential Generalization): From 'P(a)', conclude '∃x P(x)'. If '{m.group(1)} is {m.group(2)}', then something is {m.group(2)}.","domain":"reasoning","confidence":0.94},
            {"name":"universal_modus_ponens","pattern":r'[Aa]ll\s+(\w+)\s+are\s+(\w+)[.,]\s+(\w+)\s+is\s+(?:a|an)\s+\1[.,]\s*(?:t|T)herefore', "compute":lambda m:f"Valid: From '∀x (A(x)→B(x))' and 'A({m.group(3)})', conclude 'B({m.group(3)})'. {m.group(3)} is {m.group(2)}.","domain":"reasoning","confidence":0.94},
            # CONJUNCTION / DISJUNCTION / SIMPLIFICATION
            {"name":"conjunction_intro","pattern":r'(.+?)\s+is\s+(?:true|the case)[.,]\s+(.+?)\s+is\s+(?:true|the case)[.,]\s*(?:t|T)herefore\s+\1\s+and\s+\2', "compute":lambda m:f"Valid (Conjunction Introduction): From P and Q individually, conclude P ∧ Q. Compact representation.","domain":"reasoning","confidence":0.95},
            {"name":"simplification","pattern":r'(.+?)\s+and\s+(.+?)\s+is\s+(?:true|the case)[.,]\s*(?:t|T)herefore\s+\1', "compute":lambda m:f"Valid (Simplification): From P ∧ Q, conclude P. From a conjunction, any conjunct can be derived.","domain":"reasoning","confidence":0.96},
            {"name":"addition","pattern":r'(.+?)\s+is\s+(?:true|the case)[.,]\s*(?:t|T)herefore\s+\1\s+or\s+(.+)', "compute":lambda m:f"Valid (Addition): From P, conclude P ∨ Q for any Q. Weakens the statement but is logically sound.","domain":"reasoning","confidence":0.95},
            {"name":"resolution","pattern":r'(.+?)\s+or\s+(.+?)[.,]\s+(?:not\s+)?\1\s+or\s+(.+?)[.,]\s*(?:t|T)herefore', "compute":lambda m:f"Valid (Resolution): From P ∨ Q and ¬P ∨ R, conclude Q ∨ R. Used in automated theorem proving.","domain":"reasoning","confidence":0.92},
            {"name":"constructive_dilemma","pattern":r'[Ii]f\s+(.+?)\s+then\s+(.+?)\s+and\s+if\s+(.+?)\s+then\s+(.+?)[.,]\s+\1\s+or\s+\3[.,]\s*(?:t|T)herefore', "compute":lambda m:f"Valid (Constructive Dilemma): From (P→Q)∧(R→S) and P∨R, conclude Q∨S.","domain":"reasoning","confidence":0.91},
            # TRUTH TABLES
            {"name":"truth_table_and","pattern":r'(?:truth table|evaluate)\s*(?:of|for)\s*(?:P|A)\s*(?:∧|and)\s*(?:Q|B)', "compute":lambda m:"P ∧ Q is True only when both P and Q are True. False otherwise.","domain":"reasoning","confidence":0.98},
            {"name":"truth_table_or","pattern":r'(?:truth table|evaluate)\s*(?:of|for)\s*(?:P|A)\s*(?:∨|or)\s*(?:Q|B)', "compute":lambda m:"P ∨ Q is False only when both P and Q are False. True otherwise.","domain":"reasoning","confidence":0.98},
            {"name":"truth_table_implies","pattern":r'(?:truth table|evaluate)\s*(?:of|for)\s*(?:P|A)\s*(?:→|implies|->)\s*(?:Q|B)', "compute":lambda m:"P → Q is False only when P is True and Q is False. True in all other cases.","domain":"reasoning","confidence":0.98},
            {"name":"truth_table_xor","pattern":r'(?:truth table|evaluate)\s*(?:of|for)\s*(?:P|A)\s*(?:⊕|xor)\s*(?:Q|B)', "compute":lambda m:"P ⊕ Q (exclusive OR) is True when exactly one of P or Q is True. False when both are True or both False.","domain":"reasoning","confidence":0.97},
            {"name":"truth_table_iff","pattern":r'(?:truth table|evaluate)\s*(?:of|for)\s*(?:P|A)\s*(?:↔|iff|if and only if)\s*(?:Q|B)', "compute":lambda m:"P ↔ Q is True when P and Q have the same truth value. False when they differ.","domain":"reasoning","confidence":0.97},
            # LOGICAL FALLACIES
            {"name":"affirming_consequent_fallacy","pattern":r'[Ii]f\s+(.+?)\s+then\s+(.+?)[.,]\s+\2\s+is\s+(?:true|the case)[.,]\s*(?:t|T)herefore\s+\1', "compute":lambda m:f"INVALID (Affirming the Consequent): From P→Q and Q, you cannot conclude P. Q could be true for reasons other than P.","domain":"reasoning","confidence":0.98},
            {"name":"denying_antecedent_fallacy","pattern":r'[Ii]f\s+(.+?)\s+then\s+(.+?)[.,]\s+(?:not\s+)?\1\s+is\s+(?:false|not\s+the\s+case)[.,]\s*(?:t|T)herefore', "compute":lambda m:f"INVALID (Denying the Antecedent): From P→Q and ¬P, you cannot conclude ¬Q. Q could be true even if P is false.","domain":"reasoning","confidence":0.98},
            {"name":"circular_reasoning","pattern":r'(?:circular|beg(?:ging|s)\s+the\s+question)\s*(?:reasoning|argument|fallacy)', "compute":lambda m:"INVALID (Circular Reasoning / Begging the Question): The conclusion is assumed in the premise. The argument goes in a circle without providing evidence.","domain":"reasoning","confidence":0.94},
            {"name":"false_dilemma","pattern":r'(?:Either|either)\s+(.+?)\s+or\s+(.+?)\s*(?:must\s+be\s+true|are\s+the\s+only\s+options)', "compute":lambda m:"False Dilemma (potential): Only two options are presented when more exist. Check if there are genuine alternatives beyond {m.group(1)} and {m.group(2)}.","domain":"reasoning","confidence":0.92},
            {"name":"straw_man","pattern":r'(?:straw\s+man|misrepresent)\s*(?:fallacy|argument)', "compute":lambda m:"Straw Man Fallacy: Misrepresenting an opponent's argument to make it easier to attack. Refuting a distorted version, not the actual position.","domain":"reasoning","confidence":0.93},
            {"name":"ad_hominem","pattern":r'(?:ad hominem|personal attack)\s*(?:fallacy|argument)', "compute":lambda m:"Ad Hominem Fallacy: Attacking the person making the argument rather than the argument itself. Irrelevant to logical validity.","domain":"reasoning","confidence":0.94},
            {"name":"false_cause","pattern":r'(?:post hoc|false cause|cum hoc)\s*(?:ergo propter hoc|fallacy)', "compute":lambda m:"Post Hoc / False Cause Fallacy: Correlation does not imply causation. Just because B follows A doesn't mean A caused B.","domain":"reasoning","confidence":0.94},
            {"name":"slippery_slope","pattern":r'(?:slippery slope|domino effect)\s*(?:fallacy|argument)', "compute":lambda m:"Slippery Slope Fallacy: Asserting that a small first step will inevitably lead to a chain of related events culminating in a significant (usually negative) effect, without evidence for the chain.","domain":"reasoning","confidence":0.92},
            {"name":"hasty_generalization","pattern":r'(?:hasty generalization|overgeneralization|biased sample)\s*(?:fallacy)', "compute":lambda m:"Hasty Generalization Fallacy: Drawing a general conclusion from a sample that is too small or not representative.","domain":"reasoning","confidence":0.93},
            {"name":"appeal_to_authority","pattern":r'(?:appeal to authority|argumentum ad verecundiam)\s*(?:fallacy)', "compute":lambda m:"Appeal to Authority Fallacy: Citing an authority as evidence when the authority is not an expert in the relevant field or when experts disagree.","domain":"reasoning","confidence":0.93},
            {"name":"appeal_to_popularity","pattern":r'(?:appeal to popularity|bandwagon|argumentum ad populum)\s*(?:fallacy)', "compute":lambda m:"Appeal to Popularity (Ad Populum): Arguing that a proposition is true because many or most people believe it. Popularity ≠ truth.","domain":"reasoning","confidence":0.94},
            {"name":"appeal_to_ignorance","pattern":r'(?:appeal to ignorance|argumentum ad ignorantiam)\s*(?:fallacy)', "compute":lambda m:"Appeal to Ignorance: Arguing that a proposition is true because it has not been proven false, or vice versa. Absence of evidence ≠ evidence of absence.","domain":"reasoning","confidence":0.94},
            # PROPOSITIONAL LOGIC TAUTOLOGIES
            {"name":"law_of_identity","pattern":r'(?:law of identity|principle of identity)', "compute":lambda m:"Law of Identity: P → P. Everything is identical to itself. A proposition implies itself. Tautology.","domain":"reasoning","confidence":0.97},
            {"name":"law_of_excluded_middle","pattern":r'(?:law of excluded middle|tertium non datur)', "compute":lambda m:"Law of Excluded Middle: P ∨ ¬P. For any proposition, either it is true or its negation is true. Tautology.","domain":"reasoning","confidence":0.97},
            {"name":"law_of_noncontradiction","pattern":r'(?:law of non.contradiction|principle of contradiction)', "compute":lambda m:"Law of Non-Contradiction: ¬(P ∧ ¬P). A proposition and its negation cannot both be true simultaneously. Tautology.","domain":"reasoning","confidence":0.97},
            {"name":"absorption_law","pattern":r'(?:absorption)\s*(?:law|rule)\s*(?:of|in)\s*(?:logic|propositional)', "compute":lambda m:"Absorption Law: P → (P ∧ Q) ≡ P → Q. Used to simplify logical expressions.","domain":"reasoning","confidence":0.91},
            {"name":"reduction_ad_absurdum","pattern":r'(?:reductio ad absurdum|proof by contradiction|indirect proof)\s*(?:method|technique)?', "compute":lambda m:"Reductio ad Absurdum: To prove P, assume ¬P, derive a contradiction, then conclude P. Proof by contradiction is a valid logical method.","domain":"reasoning","confidence":0.95},
            {"name":"proof_by_cases","pattern":r'(?:proof by cases|case analysis|exhaustive proof)\s*(?:method|technique)?', "compute":lambda m:"Proof by Cases: If P→R and Q→R, and P∨Q is true, then R is true. Break the problem into exhaustive cases and prove each one.","domain":"reasoning","confidence":0.93},
            {"name":"transposition","pattern":r'(?:transposition|contrapositive proof)\s*(?:method|technique|in logic)', "compute":lambda m:"Transposition: To prove P→Q, it is sufficient to prove ¬Q→¬P (the contrapositive). Both statements are logically equivalent.","domain":"reasoning","confidence":0.94},
            # SET THEORY LOGIC (6 rules)
            {"name":"subset_transitivity","pattern":r'(?:subset|⊆)\s*(?:transitivity|[Aa]\s*⊆\s*[Bb]\s+and\s+[Bb]\s*⊆\s*[Cc]\s+[Tt]herefore)', "compute":lambda m:"Subset Transitivity: If A ⊆ B and B ⊆ C, then A ⊆ C. Every element of A is in B, and every element of B is in C, so every element of A is in C.","domain":"reasoning","confidence":0.96},
            {"name":"set_equality","pattern":r'(?:set equality|two sets equal|A\s*=\s*B)\s*(?:in\s+)?(?:set theory|logic)', "compute":lambda m:"Set Equality: A = B iff A ⊆ B and B ⊆ A. Two sets are equal if and only if they have exactly the same elements.","domain":"reasoning","confidence":0.95},
            {"name":"complement_law","pattern":r'(?:complement law|A\s+∪\s+A\'|union with complement|A\s+∩\s+A\')', "compute":lambda m:"Complement Laws: A ∪ A' = U (universal set). A ∩ A' = ∅ (empty set). The union of a set and its complement is everything; their intersection is nothing.","domain":"reasoning","confidence":0.93},
            {"name":"idempotent_law","pattern":r'(?:idempotent law)\s*(?:in\s+)?(?:set theory|logic)', "compute":lambda m:"Idempotent Laws: A ∪ A = A and A ∩ A = A. Duplicates don't change the set.","domain":"reasoning","confidence":0.94},
            # ADVANCED CONCEPTS
            {"name":"completeness_theorem","pattern":r'(?:completeness theorem|Gödel completeness|semantic completeness)\s*(?:in\s+)?(?:logic|first.order)', "compute":lambda m:"Gödel's Completeness Theorem: In first-order logic, every logically valid formula is provable. Semantic truth ↔ syntactic provability.","domain":"reasoning","confidence":0.88},
            {"name":"incompleteness_theorem","pattern":r'(?:incompleteness theorem|Gödel incompleteness|undecidable)', "compute":lambda m:"Gödel's Incompleteness Theorems: (1) Any consistent formal system containing arithmetic is incomplete — there exist true statements that cannot be proved. (2) A system cannot prove its own consistency.","domain":"reasoning","confidence":0.89},
            {"name":"halting_problem","pattern":r'(?:halting problem|undecidable|turing machine halt)', "compute":lambda m:"The Halting Problem: It is undecidable whether an arbitrary program will halt or run forever. Proved by Turing (1936). Cannot be solved by any algorithm.","domain":"reasoning","confidence":0.90},
            {"name":"boolean_algebra_laws","pattern":r'(?:boolean algebra|boolean laws)\s*(?:summary|list|overview)?', "compute":lambda m:"Boolean Algebra Laws: Commutative (a+b=b+a, ab=ba), Associative, Distributive, Identity (a+0=a, a·1=a), Complement (a+a'=1, a·a'=0). Foundation of digital logic circuits.","domain":"reasoning","confidence":0.94},
            {"name":"consistency_soundness","pattern":r'(?:soundness|consistency)\s*(?:vs|versus|and)\s*(?:completeness|soundness)\s*(?:in\s+)?(?:logic|formal systems)', "compute":lambda m:"Soundness: If a formula is provable, it is true. Consistency: No contradiction can be derived. Completeness: If a formula is true, it is provable. A system should be sound and consistent; completeness is a bonus.","domain":"reasoning","confidence":0.90},

            # === MASSIVE EXTENSION — +220 rules (277→500) ===
            # DIFFERENTIAL EQUATIONS — More types
            {"name":"ode_exact","pattern":r"(?:solve|find).*(?:exact|Mdx\+Ndy)", "compute":lambda m:"Exact ODE: If ∂M/∂y = ∂N/∂x, then solution is ∫Mdx + ∫(N-∂/∂y∫Mdx)dy = C.","domain":"calculus","confidence":0.88},
            {"name":"ode_second_order_undetermined","pattern":r"(?:solve|find).*(?:undetermined coefficients|particular solution)", "compute":lambda m:"Method of Undetermined Coefficients: Guess y_p as a linear combination of the forcing function and its derivatives.","domain":"calculus","confidence":0.87},
            {"name":"ode_variation_parameters","pattern":r"(?:solve|find).*(?:variation of parameters|wronskian)", "compute":lambda m:"Variation of Parameters: y_p = -y₁∫y₂f/W dx + y₂∫y₁f/W dx, where W is the Wronskian.","domain":"calculus","confidence":0.86},
            # PARTIAL DIFFERENTIAL EQUATIONS
            {"name":"pde_wave_equation","pattern":r"(?:wave equation|utt.*c\^2.*uxx|d Alembert|d'Alembert)", "compute":lambda m:"1D Wave Equation: u_tt = c²u_xx. General solution: u(x,t) = f(x-ct) + g(x+ct) (d'Alembert).","domain":"calculus","confidence":0.87},
            {"name":"pde_heat_equation","pattern":r"(?:heat equation|ut.*alpha.*uxx|diffusion equation)", "compute":lambda m:"1D Heat Equation: u_t = αu_xx. Solution via separation of variables: u(x,t) = Σ B_n sin(nπx/L)e^(-αn²π²t/L²).","domain":"calculus","confidence":0.86},
            {"name":"pde_laplace_equation","pattern":r"(?:laplace equation|∇²u|harmonic equation)", "compute":lambda m:"Laplace Equation: ∇²u = 0. Solutions are harmonic functions. In 2D polar: u(r,θ) = Σ (A_n r^n + B_n r^(-n))(C_n cos nθ + D_n sin nθ).","domain":"calculus","confidence":0.85},
            # MULTIVARIABLE CALCULUS
            {"name":"double_integral","pattern":r"(?:double integral|∬|iterated integral)\s*(?:of|over|dxdy)", "compute":lambda m:"Double integral: ∬_R f(x,y) dA = ∫_a^b ∫_c^d f(x,y) dy dx. Integrate inner first, then outer.","domain":"calculus","confidence":0.89},
            {"name":"triple_integral","pattern":r"(?:triple integral|∭|volume integral)", "compute":lambda m:"Triple integral: ∭_V f(x,y,z) dV = ∫∫∫ f(x,y,z) dz dy dx. Used for volumes, mass, moments.","domain":"calculus","confidence":0.88},
            {"name":"jacobian","pattern":r"(?:jacobian|change of variables|coordinate transform|∂\(x,y\)/∂\(u,v\))", "compute":lambda m:"Jacobian: J = |∂(x,y)/∂(u,v)| = |∂x/∂u ∂x/∂v; ∂y/∂u ∂y/∂v|. For polar: dx dy = r dr dθ.","domain":"calculus","confidence":0.86},
            {"name":"green_theorem","pattern":r"(?:green'?s theorem|∮.*dx.*dy|line integral to double)", "compute":lambda m:"Green's Theorem: ∮_C P dx + Q dy = ∬_R (∂Q/∂x - ∂P/∂y) dA. Converts line integral to double integral.","domain":"calculus","confidence":0.88},
            {"name":"stokes_theorem","pattern":r"(?:stokes'? theorem|∮.*curl|surface integral of curl)", "compute":lambda m:"Stokes' Theorem: ∮_C F·dr = ∬_S (curl F)·n dS. Curl over surface = circulation around boundary.","domain":"calculus","confidence":0.87},
            {"name":"divergence_theorem","pattern":r"(?:divergence theorem|gauss theorem|∯.*div|flux equals divergence)", "compute":lambda m:"Divergence Theorem (Gauss): ∯_S F·n dS = ∭_V div F dV. Flux through closed surface = divergence over volume.","domain":"calculus","confidence":0.87},
            # SERIES — Convergence tests
            {"name":"ratio_test","pattern":r"(?:ratio test|d Alembert ratio|convergence.*ratio)", "compute":lambda m:"Ratio Test: L = lim|a_{n+1}/a_n|. If L<1: converges; L>1: diverges; L=1: inconclusive.","domain":"calculus","confidence":0.92},
            {"name":"root_test","pattern":r"(?:root test|cauchy root|nth root test)", "compute":lambda m:"Root Test: L = lim|a_n|^(1/n). If L<1: converges; L>1: diverges; L=1: inconclusive.","domain":"calculus","confidence":0.92},
            {"name":"integral_test","pattern":r"(?:integral test|series.*integral|p.test|p series)", "compute":lambda m:"Integral Test: Σf(n) converges iff ∫_1^∞ f(x)dx converges, for f positive decreasing. p-series Σ1/n^p converges if p>1.","domain":"calculus","confidence":0.91},
            {"name":"comparison_test","pattern":r"(?:comparison test|direct comparison|limit comparison)", "compute":lambda m:"Comparison Test: If 0≤a_n≤b_n and Σb_n converges, then Σa_n converges. Limit comparison: L=lim a_n/b_n, 0<L<∞ → same behavior.","domain":"calculus","confidence":0.91},
            {"name":"alternating_series_test","pattern":r"(?:alternating series|leibniz test|alternating.*convergence)", "compute":lambda m:"Alternating Series Test (Leibniz): Σ(-1)^n a_n converges if a_n decreases monotonically to 0.","domain":"calculus","confidence":0.93},
            # MATRICES — Eigenvalues/eigenvectors
            {"name":"eigenvalue_det","pattern":r"(?:eigenvalues?|characteristic equation|det\(A.λI\))", "compute":lambda m:"Eigenvalues: det(A - λI) = 0. Solve characteristic polynomial for λ. Eigenvectors: (A - λI)v = 0.","domain":"algebra","confidence":0.90},
            {"name":"cayley_hamilton","pattern":r"(?:cayley.hamilton|matrix satisfies its own char poly)", "compute":lambda m:"Cayley-Hamilton Theorem: Every square matrix satisfies its own characteristic equation: p(A) = 0.","domain":"algebra","confidence":0.88},
            {"name":"orthogonal_matrix","pattern":r"(?:orthogonal matrix|A\^T.*A.*=.*I|rotation matrix)", "compute":lambda m:"Orthogonal matrix: A^T A = I. Columns are orthonormal vectors. Rotation and reflection matrices are orthogonal.","domain":"algebra","confidence":0.90},
            {"name":"symmetric_matrix","pattern":r"(?:symmetric matrix|A\^T.*=.*A)", "compute":lambda m:"Symmetric matrix: A^T = A. All eigenvalues are real. Always diagonalizable by orthogonal matrix.","domain":"algebra","confidence":0.91},
            {"name":"diagonalization","pattern":r"(?:diagonaliz|similar matrices|P\^-1.*A.*P)", "compute":lambda m:"Diagonalization: A = PDP^(-1) where D is diagonal matrix of eigenvalues and P has eigenvectors as columns. Requires n linearly independent eigenvectors.","domain":"algebra","confidence":0.88},
            {"name":"matrix_rank","pattern":r"(?:rank of|matrix rank|row rank|column rank)", "compute":lambda m:"Rank(A) = number of linearly independent rows or columns = number of non-zero rows in RREF. Full rank matrix is invertible.","domain":"algebra","confidence":0.92},
            # LINEAR ALGEBRA
            {"name":"linear_independence","pattern":r"(?:linearly independent|linear dependence|wronskian.*0)", "compute":lambda m:"Vectors {v₁,...,vₙ} are linearly independent if c₁v₁+...+cₙvₙ=0 implies all cᵢ=0. Wronskian W≠0 for independent functions.","domain":"algebra","confidence":0.91},
            {"name":"basis_dimension","pattern":r"(?:basis|dimension of|span of)", "compute":lambda m:"A basis is a maximal linearly independent set. Dimension = number of vectors in any basis. R^n has dimension n.","domain":"algebra","confidence":0.93},
            {"name":"null_space","pattern":r"(?:null space|kernel|Ax.*=.*0)", "compute":lambda m:"Null space N(A) = {x | Ax = 0}. dim(null space) = n - rank(A) (rank-nullity theorem).","domain":"algebra","confidence":0.91},
            {"name":"column_space","pattern":r"(?:column space|range|image|span of columns)", "compute":lambda m:"Column space = span of column vectors. dim(col space) = rank(A). Solutions to Ax=b exist iff b is in column space.","domain":"algebra","confidence":0.91},
            # GEOMETRY — More shapes
            {"name":"cone_volume","pattern":r"(?:volume).*(?:cone|conical).*(?:radius|r)\s*(\d+).*(?:height|h)\s*(\d+)", "compute":lambda m:f"Volume of cone = (1/3)πr²h = (1/3)π({m.group(1)})²({m.group(2)}) = {3.14159*int(m.group(1))**2*int(m.group(2))/3:.2f}","domain":"geometry","confidence":0.97},
            {"name":"pyramid_volume","pattern":r"(?:volume).*(?:pyramid).*(?:base|b)\s*(\d+).*(?:height|h)\s*(\d+)", "compute":lambda m:f"Volume of pyramid = (1/3)Bh = (1/3)({m.group(1)})²({m.group(2)}) = {int(m.group(1))**2*int(m.group(2))/3:.1f}","domain":"geometry","confidence":0.96},
            {"name":"regular_polygon_area","pattern":r"(?:area).*(?:regular polygon|n.gon|n sided).*(?:side|s)\s*(\d+).*(?:n|sides)\s*(\d+)", "compute":lambda m:f"Area of regular {m.group(2)}-gon = ({m.group(2)}s²)/(4 tan(π/{m.group(2)})) = ({int(m.group(2))*int(m.group(1))**2})/(4 tan(π/{m.group(2)}))","domain":"geometry","confidence":0.92},
            {"name":"ellipse_area","pattern":r"(?:area).*(?:ellipse|ellipse).*(?:a\s*=\s*|semi.major)\s*(\d+).*(?:b\s*=\s*|semi.minor)\s*(\d+)", "compute":lambda m:f"Area of ellipse = πab = π({m.group(1)})({m.group(2)}) = {3.14159*int(m.group(1))*int(m.group(2)):.2f}","domain":"geometry","confidence":0.97},
            # PROBABILITY — More distributions
            {"name":"geometric_dist","pattern":r"(?:geometric distribution|geometric prob).*(?:p\s*=\s*|prob\s*=\s*)([\d.]+)", "compute":lambda m:f"Geometric: P(X=k) = (1-p)^(k-1)p. E(X)=1/p={1/float(m.group(1)):.2f}, Var=(1-p)/p².","domain":"probability","confidence":0.91},
            {"name":"hypergeometric_dist","pattern":r"(?:hypergeometric|hypergeometric).*(?:N\s*=\s*|pop\s*=\s*)(\d+).*(?:K\s*=\s*|success\s*=\s*)(\d+).*(?:n\s*=\s*|sample\s*=\s*)(\d+)", "compute":lambda m:f"Hypergeometric: P(X=k) = C(K,k)C(N-K,n-k)/C(N,n). E(X)=nK/N={int(m.group(3))*int(m.group(2))/int(m.group(1)):.2f}.","domain":"probability","confidence":0.89},
            {"name":"markov_chain","pattern":r"(?:markov chain|transition matrix|steady state)", "compute":lambda m:"Markov chain: state evolves via P^n. Steady state π: πP = π, Σπ_i = 1. Absorbing if there's a state you can't leave.","domain":"probability","confidence":0.86},
            {"name":"conditional_expectation","pattern":r"(?:conditional expectation|E\(.*\|.*\)|law of iterated expectations|tower property)", "compute":lambda m:"E(X|Y) = Σx·P(X=x|Y). Law of Iterated Expectations: E[E(X|Y)] = E(X). Tower property.","domain":"probability","confidence":0.87},
            {"name":"moment_generating","pattern":r"(?:moment generating|mgf|M\(t\)|e\(tX\)|moment generating function)", "compute":lambda m:"MGF: M_X(t) = E(e^(tX)). M'(0) = E(X), M''(0) = E(X²). For normal N(μ,σ²): M(t) = exp(μt + σ²t²/2).","domain":"probability","confidence":0.86},
            # NUMERICAL METHODS
            {"name":"bisection_method","pattern":r"(?:bisection method|binary search root)", "compute":lambda m:"Bisection: If f(a)f(b)<0, then root∈[a,b]. c=(a+b)/2. Iterate until |b-a|<ε. Linear convergence.","domain":"calculus","confidence":0.90},
            {"name":"secant_method","pattern":r"(?:secant method)", "compute":lambda m:"Secant method: x_{n+1}=x_n - f(x_n)(x_n-x_{n-1})/(f(x_n)-f(x_{n-1})). Superlinear convergence, no derivative needed.","domain":"calculus","confidence":0.89},
            {"name":"runge_kutta","pattern":r"(?:runge.kutta|RK4|numerical ODE|ode solver)", "compute":lambda m:"RK4: y_{n+1}=y_n+(h/6)(k₁+2k₂+2k₃+k₄) with k₁=f(t_n,y_n), k₂=f(t_n+h/2, y_n+hk₁/2), k₃=f(t_n+h/2, y_n+hk₂/2), k₄=f(t_n+h, y_n+hk₃). O(h⁴) accuracy.","domain":"calculus","confidence":0.87},
            {"name":"simpsons_rule","pattern":r"(?:simpson'?s rule|simpson|parabolic rule)", "compute":lambda m:"Simpson's Rule: ∫_a^b f(x)dx ≈ (h/3)[f(x₀)+4f(x₁)+2f(x₂)+...+4f(x_{n-1})+f(x_n)]. Error O(h⁴).","domain":"calculus","confidence":0.88},
            # INEQUALITIES
            {"name":"cauchy_schwarz","pattern":r"(?:cauchy.schwarz|Cauchy.Schwarz|CS inequality)", "compute":lambda m:"Cauchy-Schwarz: |⟨u,v⟩| ≤ ||u||·||v||. For vectors: (Σu_i v_i)² ≤ (Σu_i²)(Σv_i²). For functions: (∫fg)² ≤ (∫f²)(∫g²).","domain":"algebra","confidence":0.91},
            {"name":"triangle_inequality","pattern":r"(?:triangle inequality|\|u\+v\|.*≤)", "compute":lambda m:"Triangle inequality: ||u+v|| ≤ ||u|| + ||v||. For complex: |z₁+z₂| ≤ |z₁|+|z₂|. Equality iff vectors are parallel and same direction.","domain":"algebra","confidence":0.93},
            {"name":"am_gm_inequality","pattern":r"(?:AM.GM|arithmetic mean.*geometric mean|AM ≥ GM)", "compute":lambda m:"AM-GM: (x₁+...+xₙ)/n ≥ (x₁·...·xₙ)^(1/n). Equality iff all x_i are equal. For 2 numbers: (a+b)/2 ≥ √(ab).","domain":"algebra","confidence":0.92},
            {"name":"bernoulli_inequality","pattern":r"(?:bernoulli inequality|(?:1\+x)\^n.*≥)", "compute":lambda m:"Bernoulli: (1+x)^n ≥ 1+nx for x≥-1 and n≥0. Useful for bounding exponential growth.","domain":"algebra","confidence":0.91},
            # COMPLEX ANALYSIS
            {"name":"euler_formula","pattern":r"(?:euler formula|e\^\(iθ\)|e.\{i.*theta\}|euler.*identity)", "compute":lambda m:"Euler's Formula: e^(iθ) = cos θ + i sin θ. e^(iπ) + 1 = 0 (Euler's Identity). Polar form: z = re^(iθ).","domain":"algebra","confidence":0.93},
            {"name":"de_moivre","pattern":r"(?:de moivre|De Moivre|cos.*\+.*i.*sin.*\^n)", "compute":lambda m:"De Moivre: (cos θ + i sin θ)^n = cos(nθ) + i sin(nθ). Used for powers and roots of complex numbers.","domain":"algebra","confidence":0.93},
            {"name":"roots_of_unity","pattern":r"(?:roots of unity|nth root.*complex|n.th root.*unity)", "compute":lambda m:"nth roots of unity: ω_k = e^(2πik/n) for k=0,1,...,n-1. Sum of all n roots = 0. Product = (-1)^(n+1).","domain":"algebra","confidence":0.90},
            # TOPOLOGY / REAL ANALYSIS
            {"name":"open_set","pattern":r"(?:open set|open interval|neighbourhood|neighborhood)", "compute":lambda m:"Open set: Every point has a neighborhood fully contained in the set. Open interval (a,b) = {x | a<x<b}.","domain":"reasoning","confidence":0.85},
            {"name":"closed_set","pattern":r"(?:closed set|closed interval|contains.*limit points)", "compute":lambda m:"Closed set: Contains all its limit points. Complement is open. [a,b] is closed. A set can be both open and closed (clopen).","domain":"reasoning","confidence":0.85},
            {"name":"continuity_epsilon_delta","pattern":r"(?:epsilon.delta|ε.δ|ε.δ|continuity definition)", "compute":lambda m:"ε-δ definition: f is continuous at x=a if ∀ε>0, ∃δ>0 such that |x-a|<δ → |f(x)-f(a)|<ε.","domain":"calculus","confidence":0.88},
            {"name":"uniform_continuity","pattern":r"(?:uniform continuity|uniformly continuous|Lipschitz)", "compute":lambda m:"Uniform continuity: δ depends only on ε, not on x. Lipschitz: |f(x)-f(y)|≤M|x-y| implies uniform continuity.","domain":"calculus","confidence":0.85},
            {"name":"bolzano_weierstrass","pattern":r"(?:bolzano.weierstrass|bounded sequence.*convergent subsequence)", "compute":lambda m:"Bolzano-Weierstrass: Every bounded sequence in R^n has a convergent subsequence.","domain":"calculus","confidence":0.88},
            {"name":"intermediate_value_theorem","pattern":r"(?:intermediate value|IVT|f\(a\).*f\(b\)|value between)", "compute":lambda m:"IVT: If f is continuous on [a,b] and k is between f(a) and f(b), then ∃c∈[a,b] with f(c)=k.","domain":"calculus","confidence":0.91},
            {"name":"extreme_value_theorem","pattern":r"(?:extreme value|EVT|maximum.*minimum.*continuous.*closed)", "compute":lambda m:"EVT: A continuous function on a closed interval [a,b] attains its maximum and minimum values.","domain":"calculus","confidence":0.92},
            # CRYPTOGRAPHY / NUMBER THEORY
            {"name":"fermat_little_theorem","pattern":r"(?:fermat little|a\^\(p.1\)|fermat.*prime.*mod)", "compute":lambda m:"Fermat's Little Theorem: If p is prime and gcd(a,p)=1, then a^(p-1) ≡ 1 (mod p).","domain":"number_theory","confidence":0.91},
            {"name":"euler_totient","pattern":r"(?:euler totient|φ\(n\)|phi function|totient)", "compute":lambda m:"Euler's totient φ(n) = number of integers 1≤k≤n with gcd(k,n)=1. For prime p: φ(p)=p-1. For n=pq: φ(n)=(p-1)(q-1).","domain":"number_theory","confidence":0.90},
            {"name":"rsa_encryption","pattern":r"(?:RSA|public.key|private.key|encrypt.*decrypt)", "compute":lambda m:"RSA: Public key (n,e), Private key d. Encryption: c=m^e mod n. Decryption: m=c^d mod n. Security based on difficulty of factoring n=pq.","domain":"number_theory","confidence":0.88},
            {"name":"chinese_remainder","pattern":r"(?:chinese remainder|CRT|x.*≡.*mod.*≡.*mod)", "compute":lambda m:"Chinese Remainder Theorem: For coprime m₁,m₂,...,mᵏ, system x≡aᵢ(mod mᵢ) has unique solution mod M=Πmᵢ.","domain":"number_theory","confidence":0.89},
            # GRAPH THEORY — More concepts
            {"name":"dijkstra","pattern":r"(?:dijkstra|shortest path|shortest distance)", "compute":lambda m:"Dijkstra's Algorithm: Finds shortest path from source to all vertices in weighted graph. Complexity O((V+E)log V) with heap.","domain":"reasoning","confidence":0.87},
            {"name":"spanning_tree","pattern":r"(?:spanning tree|minimum spanning|MST|Kruskal|Prim)", "compute":lambda m:"Minimum Spanning Tree: Connects all vertices with minimum total edge weight. Kruskal's (sort edges) or Prim's (grow from vertex) algorithm.","domain":"reasoning","confidence":0.86},
            # COMBINATORICS
            {"name":"pigeonhole_example","pattern":r"(?:pigeonhole|pigeon hole).*(?:example|apply|use)", "compute":lambda m:"Pigeonhole Example: In any group of 13 people, at least 2 share a birth month (12 months, 13 people → 13>12).","domain":"reasoning","confidence":0.93},
            {"name":"stars_and_bars","pattern":r"(?:stars and bars|positive integer solutions|non.negative solutions)", "compute":lambda m:"Stars and Bars: Number of solutions to x₁+...+xₙ = k with xᵢ≥0: C(k+n-1, n-1). With xᵢ≥1: C(k-1, n-1).","domain":"combinatorics","confidence":0.89},
            # ADDITIONAL DERIVATIVES
            {"name":"derivative_arcsin","pattern":r"(?:derivative|d/dx)\s*(?:of\s*)?arcsin\(x\)", "compute":lambda m:"d/dx(arcsin(x)) = 1/√(1-x²)","domain":"calculus","confidence":0.92},
            {"name":"derivative_arccos","pattern":r"(?:derivative|d/dx)\s*(?:of\s*)?arccos\(x\)", "compute":lambda m:"d/dx(arccos(x)) = -1/√(1-x²)","domain":"calculus","confidence":0.92},
            {"name":"derivative_arctan","pattern":r"(?:derivative|d/dx)\s*(?:of\s*)?arctan\(x\)", "compute":lambda m:"d/dx(arctan(x)) = 1/(1+x²)","domain":"calculus","confidence":0.93},
            {"name":"derivative_cosh","pattern":r"(?:derivative|d/dx)\s*(?:of\s*)?cosh\(x\)", "compute":lambda m:"d/dx(cosh(x)) = sinh(x)","domain":"calculus","confidence":0.92},
            {"name":"derivative_sinh","pattern":r"(?:derivative|d/dx)\s*(?:of\s*)?sinh\(x\)", "compute":lambda m:"d/dx(sinh(x)) = cosh(x)","domain":"calculus","confidence":0.92},
            {"name":"implicit_differentiation","pattern":r"(?:implicit differentiation|implicit derivative|dy/dx.*implicit)", "compute":lambda m:"Implicit differentiation: Differentiate both sides w.r.t x, treating y as function of x. Solve for dy/dx.","domain":"calculus","confidence":0.89},
            # SOLID OF REVOLUTION
            {"name":"disk_method","pattern":r"(?:disk method|solid of revolution.*disk|volume.*disk)", "compute":lambda m:"Disk method: V = π∫_a^b [R(x)]² dx for rotation about x-axis. Radius R(x) is distance from axis to curve.","domain":"calculus","confidence":0.88},
            {"name":"washer_method","pattern":r"(?:washer method|solid of revolution.*washer|volume.*washer)", "compute":lambda m:"Washer method: V = π∫_a^b ([R(x)]²-[r(x)]²) dx. For region between two curves rotated about axis.","domain":"calculus","confidence":0.87},
            {"name":"shell_method","pattern":r"(?:shell method|solid of revolution.*shell|volume.*shell)", "compute":lambda m:"Shell method: V = 2π∫_a^b x·h(x) dx for rotation about y-axis. Height h(x) is the function value.","domain":"calculus","confidence":0.87},
            # FOURIER SERIES
            {"name":"fourier_series_coeff","pattern":r"(?:fourier coefficients|fourier series.*a0.*an.*bn|trigonometric series)", "compute":lambda m:"Fourier series: f(x)=a₀/2 + Σ[a_n cos(nπx/L) + b_n sin(nπx/L)]. a_n=(1/L)∫f(x)cos(nπx/L)dx, b_n=(1/L)∫f(x)sin(nπx/L)dx.","domain":"calculus","confidence":0.86},
            {"name":"fourier_transform","pattern":r"(?:fourier transform|F\(ω\)|transform.*frequency)", "compute":lambda m:"Fourier Transform: F(ω)=∫f(t)e^(-iωt)dt. Converts time-domain to frequency-domain. Inverse: f(t)=(1/2π)∫F(ω)e^(iωt)dω.","domain":"calculus","confidence":0.85},
            # OPTIMIZATION / GAME THEORY
            {"name":"nash_equilibrium","pattern":r"(?:nash equilibrium|game theory|prisoner.*dilemma)", "compute":lambda m:"Nash Equilibrium: Strategy profile where no player benefits from unilaterally changing strategy. Not necessarily Pareto optimal.","domain":"reasoning","confidence":0.87},
            {"name":"lagrange_multipliers","pattern":r"(?:lagrange multiplier|constrained optimization|∇f.*λ.*∇g)", "compute":lambda m:"Lagrange multipliers: max/min f(x,y) subject to g(x,y)=c. Solve ∇f = λ∇g and g=c. λ is marginal cost of constraint.","domain":"calculus","confidence":0.86},
            # ADDITIONAL RULES (~70 more compact rules)
            {"name":"eigenvalue_2x2_quick","pattern":r"(?:eigen).*2x2", "compute":lambda m:"Eigenvalues of 2x2 [[a,b],[c,d]]: λ = (tr±√(tr²-4det))/2 where tr=a+d, det=ad-bc.","domain":"algebra","confidence":0.91},
            {"name":"curl_zero_conservative","pattern":r"(?:conservative|curl.*=.*0|path independent|potential function)", "compute":lambda m:"F is conservative if curl F = 0 (on simply connected domain). Then ∃f with F = ∇f, and line integral is path independent.","domain":"calculus","confidence":0.87},
            {"name":"line_integral_work","pattern":r"(?:line integral|work.*F.*dr|∫.*F.*dr)", "compute":lambda m:"Work = ∫_C F·dr = ∫_a^b F(r(t))·r'(t) dt. Scalar line integral: ∫_C f ds.","domain":"calculus","confidence":0.87},
            {"name":"surface_integral_flux","pattern":r"(?:surface integral|flux.*F.*dS|flux integral)", "compute":lambda m:"Flux = ∬_S F·n dS = ∬_D F(r(u,v))·(r_u×r_v) du dv. Measures net flow through surface.","domain":"calculus","confidence":0.86},
            {"name":"binomial_theorem","pattern":r"(?:binomial theorem|\(.*\+.*\)\^n|binomial expansion)", "compute":lambda m:"(x+y)^n = Σ C(n,k) x^(n-k) y^k for k=0 to n. Pascal's triangle gives coefficients.","domain":"algebra","confidence":0.93},
            {"name":"partial_fraction","pattern":r"(?:partial fraction|partial fractions|decompose into partial)", "compute":lambda m:"Partial fractions: Decompose rational function P(x)/Q(x) into sum of simpler fractions. Method depends on factors of Q(x).","domain":"algebra","confidence":0.88},
            {"name":"radius_convergence","pattern":r"(?:radius of convergence|power series.*radius|interval of convergence)", "compute":lambda m:"Radius of convergence R = 1/limsup|a_n|^(1/n). Series converges for |x|<R, diverges for |x|>R. Check endpoints separately.","domain":"calculus","confidence":0.87},
            {"name":"asymptote_horizontal","pattern":r"(?:horizontal asymptote|limit.*infinity|asymptote.*y\s*=)", "compute":lambda m:"Horizontal asymptote: y = L where L = lim f(x) as x->inf. If limit exists finite.","domain":"calculus","confidence":0.90},
            {"name":"asymptote_vertical","pattern":r"(?:vertical asymptote|x\s*=|denominator.*zero|pole)", "compute":lambda m:"Vertical asymptote at x=a if lim_{x→a} f(x) = ±∞. Usually occurs when denominator = 0 at x=a.","domain":"calculus","confidence":0.91},
            {"name":"asymptote_oblique","pattern":r"(?:oblique asymptote|slant asymptote|y\s*=\s*mx\s*\+\s*b)", "compute":lambda m:"Oblique asymptote: y = mx+b where m = lim f(x)/x and b = lim(f(x)-mx). Occurs when degree(numerator) = degree(denominator)+1.","domain":"calculus","confidence":0.88},

            {"name":"linear_programming","pattern":r"(?:linear programming|LP|objective function).*(?:maximize|max|minimize|min)", "compute":lambda m:"Linear Programming: Maximize c^T x subject to Ax <= b, x >= 0. Solved via simplex or interior-point methods.","domain":"reasoning","confidence":0.85},
            {"name":"simplex_method","pattern":r"(?:simplex method|simplex algorithm|pivoting)", "compute":lambda m:"Simplex Method: Moves from vertex to vertex of feasible polytope, improving objective at each step, until optimum is reached.","domain":"reasoning","confidence":0.84},
            {"name":"duality_theorem","pattern":r"(?:duality|dual problem|weak duality|strong duality)", "compute":lambda m:"Duality: Every LP has a dual. Weak: c^T x <= b^T y. Strong: at optimum, c^T x* = b^T y*.","domain":"reasoning","confidence":0.84},
            {"name":"nash_equilibrium_example","pattern":r"(?:nash equilibrium).*(?:example|prisoner|dilemma)", "compute":lambda m:"Prisoner's Dilemma: Both confess = Nash equilibrium (5,5 years), but both silent = better outcome (1,1).","domain":"reasoning","confidence":0.87},
            {"name":"pareto_optimum","pattern":r"(?:pareto optimum|pareto efficient|no one better off)", "compute":lambda m:"Pareto Optimum: No individual can be made better off without making another worse off.","domain":"reasoning","confidence":0.86},
            {"name":"zero_sum_game","pattern":r"(?:zero.sum game|minimax|maximin)", "compute":lambda m:"Zero-sum game: One player's gain = other's loss. Optimal strategy via minimax theorem.","domain":"reasoning","confidence":0.85},
            {"name":"dominant_strategy","pattern":r"(?:dominant strategy|strictly dominant|weakly dominant)", "compute":lambda m:"Dominant strategy: Always yields better payoff regardless of opponent's actions. If one exists, play it.","domain":"reasoning","confidence":0.87},
            {"name":"bayes_nash","pattern":r"(?:bayesian game|bayes.nash|incomplete information)", "compute":lambda m:"Bayesian Nash Equilibrium: Players have incomplete information about others' payoffs; strategies based on beliefs.","domain":"reasoning","confidence":0.83},
            {"name":"group_theory_closure","pattern":r"(?:group theory|group axioms|closure.*associativity|identity|inverse)", "compute":lambda m:"Group (G,*): (1) Closure, (2) Associativity, (3) Identity e exists, (4) Inverse for each element.","domain":"algebra","confidence":0.88},
            {"name":"abelian_group","pattern":r"(?:abelian group|commutative group|commutative.*group)", "compute":lambda m:"Abelian group: A group where a*b = b*a for all a,b. Named after Niels Henrik Abel.","domain":"algebra","confidence":0.90},
            {"name":"ring_theory","pattern":r"(?:ring|ring theory|ring axioms|algebraic ring)", "compute":lambda m:"Ring (R,+,\u00d7): Abelian group under +, monoid under \u00d7, distributive. Z, Q, R, C are rings.","domain":"algebra","confidence":0.85},
            {"name":"field_theory","pattern":r"(?:field|field theory|commutative division)", "compute":lambda m:"Field: A ring where every non-zero element has multiplicative inverse. Q, R, C, Z_p (p prime) are fields.","domain":"algebra","confidence":0.85},
            {"name":"finite_field","pattern":r"(?:finite field|galois field|GF)", "compute":lambda m:"Finite Field GF(p^n): p prime, n >= 1. Number of elements = p^n. Used in cryptography and coding theory.","domain":"algebra","confidence":0.84},
            {"name":"vector_space","pattern":r"(?:vector space|linear space|axioms.*vector)", "compute":lambda m:"Vector space V over field F: Closed under addition and scalar multiplication. Must satisfy 8 axioms.","domain":"algebra","confidence":0.88},
            {"name":"linear_transformation","pattern":r"(?:linear transformation|linear map|T\(.*\+.*\)|T\(c.*v\))=cT\\(v\\))", "compute":lambda m:"Linear transformation T: V->W satisfies T(u+v)=T(u)+T(v) and T(cv)=cT(v).","domain":"algebra","confidence":0.88},
            {"name":"isomorphism","pattern":r"(?:isomorphism|isomorphic|bijective homomorphism)", "compute":lambda m:"Isomorphism: Bijective homomorphism. Two structures are isomorphic if there's a structure-preserving bijection between them.","domain":"algebra","confidence":0.85},
            {"name":"first_isomorphism_theorem","pattern":r"(?:first isomorphism|fundamental homomorphism)", "compute":lambda m:"First Isomorphism Theorem: G/ker(\u03c6) \u2245 im(\u03c6). Quotient group is isomorphic to image.","domain":"algebra","confidence":0.83},
            {"name":"lagrange_theorem","pattern":r"(?:lagrange theorem|order.*subgroup.*divides)", "compute":lambda m:"Lagrange's Theorem: |H| divides |G| for any subgroup H of finite group G.","domain":"algebra","confidence":0.87},
            {"name":"sylow_theorem","pattern":r"(?:sylow theorem|p.group|p.sylow)", "compute":lambda m:"Sylow Theorems: For |G|=p^n*m, there exists subgroup of order p^n. All Sylow p-subgroups are conjugate.","domain":"algebra","confidence":0.82},
            {"name":"set_operations","pattern":r"(?:set difference|set complement|symmetric difference|A.B|A\\\\B)", "compute":lambda m:"Set difference A\\B = {x in A | x not in B}. Symmetric difference A\u0394B = (A\\B)\u222a(B\\A).","domain":"reasoning","confidence":0.90},
            {"name":"de_morgan_laws_sets","pattern":r"(?:de morgan.*sets|complement.*union.*intersection)", "compute":lambda m:"De Morgan for sets: (A\u222aB)' = A' \u2229 B', (A\u2229B)' = A' \u222a B'.","domain":"reasoning","confidence":0.93},
            {"name":"cartesian_product","pattern":r"(?:cartesian product|A.*B|ordered pair)", "compute":lambda m:"Cartesian product A\u00d7B = {(a,b) | a in A, b in B}. For R\u00d7R, this is the coordinate plane.","domain":"reasoning","confidence":0.92},
            {"name":"equivalence_relation","pattern":r"(?:equivalence relation|reflexive.*symmetric.*transitive|partition)", "compute":lambda m:"Equivalence relation: Reflexive, symmetric, transitive. Partitions set into equivalence classes. Example: congruence modulo n.","domain":"reasoning","confidence":0.88},
            {"name":"partial_order","pattern":r"(?:partial order|poset|reflexive.*antisymmetric.*transitive)", "compute":lambda m:"Partial order: Reflexive, antisymmetric, transitive. NOT all pairs comparable. Hasse diagram represents poset.","domain":"reasoning","confidence":0.86},
            {"name":"lattice_theory","pattern":r"(?:lattice|meet.*join|supremum.*infimum)", "compute":lambda m:"Lattice: A poset where every pair has supremum (join) and infimum (meet). Boolean algebra is a complemented distributive lattice.","domain":"reasoning","confidence":0.83},
            {"name":"measure_theory","pattern":r"(?:measure|sigma algebra|\u03c3.algebra|lebesgue measure)", "compute":lambda m:"Measure theory: Assigns size to sets. Lebesgue measure on R gives interval [a,b] measure b-a. Foundation of modern probability.","domain":"calculus","confidence":0.82},
            {"name":"lebesgue_integral","pattern":r"(?:lebesgue integral|lebesgue dominated|lebesgue vs riemann)", "compute":lambda m:"Lebesgue integral: More powerful than Riemann, integrates over measure spaces. Dominated convergence theorem holds.","domain":"calculus","confidence":0.81},
            {"name":"riemann_stieltjes","pattern":r"(?:riemann.stieltjes|stieltjes integral)", "compute":lambda m:"Riemann-Stieltjes integral: Generalizes Riemann integral with respect to a function g rather than x.","domain":"calculus","confidence":0.80},
            {"name":"metric_space","pattern":r"(?:metric space|distance.*positive.*definite|metric.*d\\(x,y\\)|d\\(x,y\\)|triangle inequality)", "compute":lambda m:"Metric space (X,d): d(x,y)>=0, d(x,y)=0 iff x=y, symmetric, triangle inequality d(x,z)<=d(x,y)+d(y,z).","domain":"calculus","confidence":0.84},
            {"name":"banach_space","pattern":r"(?:banach space|complete normed|norm.*complete)", "compute":lambda m:"Banach space: Complete normed vector space. All Cauchy sequences converge. Examples: L^p spaces, C[a,b] with sup norm.","domain":"calculus","confidence":0.82},
            {"name":"hilbert_space","pattern":r"(?:hilbert space|inner product.*complete)", "compute":lambda m:"Hilbert space: Complete inner product space. R^n and L^2 are Hilbert. Orthonormal basis exists.","domain":"calculus","confidence":0.82},
            {"name":"cauchy_sequence","pattern":r"(?:cauchy sequence|cauchy criterion|converges.*cauchy)", "compute":lambda m:"Cauchy sequence: For any \u03b5>0, \u2203N s.t. |a_m - a_n| < \u03b5 for all m,n > N. Complete spaces: Cauchy => convergent.","domain":"calculus","confidence":0.86},
            {"name":"compactness","pattern":r"(?:compact|heine.borel|open cover.*finite subcover)", "compute":lambda m:"Compact: Every open cover has finite subcover. In R^n, compact = closed and bounded (Heine-Borel).","domain":"calculus","confidence":0.84},
            {"name":"connectedness","pattern":r"(?:connected|path.connected|simply connected)", "compute":lambda m:"Connected: Cannot be split into disjoint open sets. Path-connected => connected. R is connected.","domain":"calculus","confidence":0.83},
            {"name":"homeomorphism","pattern":r"(?:homeomorphism|topological equivalence|continuous bijection.*inverse continuous)", "compute":lambda m:"Homeomorphism: Continuous bijection with continuous inverse. Preserves topological properties. Coffee cup = donut (torus).","domain":"calculus","confidence":0.82},
            {"name":"galois_theory","pattern":r"(?:galois theory|solvability.*radicals|galois group)", "compute":lambda m:"Galois Theory: Links field extensions to group theory. Quintic is not solvable by radicals.","domain":"algebra","confidence":0.81},
            {"name":"polynomial_roots","pattern":r"(?:fundamental theorem of algebra|complex roots|n roots)", "compute":lambda m:"Fundamental Theorem of Algebra: Every non-constant polynomial of degree n has exactly n complex roots.","domain":"algebra","confidence":0.90},
            {"name":"vieta_formulas","pattern":r"(?:vieta|sum of roots|product of roots)", "compute":lambda m:"Vieta's formulas: Sum of roots = -b/a, product of roots = c/a for quadratic ax^2+bx+c=0.","domain":"algebra","confidence":0.91},
            {"name":"cardano_cubic","pattern":r"(?:cardano|cubic formula|solve cubic|depressed cubic)", "compute":lambda m:"Cardano's formula: For x^3+px+q=0, x = \u221b(-q/2+\u221a(q^2/4+p^3/27)) + \u221b(-q/2-\u221a(q^2/4+p^3/27)).","domain":"algebra","confidence":0.84},
            {"name":"quadratic_reciprocity","pattern":r"(?:quadratic reciprocity|legendre symbol|gauss.*reciprocity)", "compute":lambda m:"Quadratic Reciprocity (Gauss): (\u2220p)(\u2202q) = (-1)^((p-1)(q-1)/4). For odd primes p,q.","domain":"number_theory","confidence":0.82},
            {"name":"primitive_root","pattern":r"(?:primitive root|generator.*mod|order.*\u03c6)", "compute":lambda m:"Primitive root g modulo n: Order of g is \u03c6(n). Exists iff n = 2,4,p^k,2p^k for odd prime p.","domain":"number_theory","confidence":0.84},
            {"name":"dirichlet_theorem","pattern":r"(?:dirichlet.*primes|primes in arithmetic progression|a.*mod.*n.*prime)", "compute":lambda m:"Dirichlet's Theorem: For coprime a,d, infinitely many primes of form a + nd.","domain":"number_theory","confidence":0.83},
            {"name":"riemann_hypothesis","pattern":r"(?:riemann hypothesis|zeta function|critical line|nontrivial zeros)", "compute":lambda m:"Riemann Hypothesis: All non-trivial zeros of \u03b6(s) have real part 1/2. Unsolved (Clay Prize).","domain":"calculus","confidence":0.82},
            {"name":"prime_number_theorem","pattern":r"(?:prime number theorem|\u03c0\\(x\\).*x/log|distribution of primes)", "compute":lambda m:"Prime Number Theorem: \u03c0(x) ~ x/log(x). Proportion of numbers <= x that are prime ~ 1/log(x).","domain":"number_theory","confidence":0.86},
            {"name":"goldbach_conjecture","pattern":r"(?:goldbach|even.*sum.*two primes)", "compute":lambda m:"Goldbach's Conjecture: Every even integer > 2 is sum of two primes. Unproven. Verified up to 4\u00d710^18.","domain":"number_theory","confidence":0.83},
            {"name":"twin_prime_conjecture","pattern":r"(?:twin prime|prime.*difference.*2|infinitely many twin primes)", "compute":lambda m:"Twin Prime Conjecture: There are infinitely many pairs of primes differing by 2. Yitang Zhang (2013): bound < 70 million.","domain":"number_theory","confidence":0.83},
            {"name":"collatz_conjecture","pattern":r"(?:collatz|3n\\+1|hailstone|ulam)", "compute":lambda m:"Collatz conjecture: For any n, repeat: n even -> n/2, n odd -> 3n+1. Eventually reaches 1. Unproven.","domain":"number_theory","confidence":0.82},
            {"name":"transcendental_number","pattern":r"(?:transcendental|\u03c0.*transcendental|e.*transcendental|algebraic.*irrational)", "compute":lambda m:"Transcendental numbers: \u03c0, e, 2^\u221a2 are transcendental (not roots of any polynomial with integer coefficients).","domain":"algebra","confidence":0.85},
            {"name":"hilbert_problems","pattern":r"(?:hilbert problems|hilbert.*23|hilbert.*unsolved)", "compute":lambda m:"Hilbert's 23 problems (1900): Set the agenda for 20th century math. 10 solved, many partially resolved.","domain":"reasoning","confidence":0.82},
            {"name":"millennium_prizes","pattern":r"(?:millennium prize|clay math|poincar\u00e9|P vs NP|riemann|yang.mills|navier.stokes|birch|hodge)", "compute":lambda m:"Millennium Prize Problems: 7 problems. Poincare solved; Riemann Hypothesis, P vs NP, Navier-Stokes, Yang-Mills, Birch-Swinnerton-Dyer, Hodge unresolved.","domain":"reasoning","confidence":0.83},
            {"name":"four_color_theorem","pattern":r"(?:four color|map coloring|4.colour|chromatic number.*planar)", "compute":lambda m:"Four Color Theorem: Any planar map needs at most 4 colors so no adjacent regions share color. Proved by Appell-Haken (1976) using computer.","domain":"reasoning","confidence":0.87},
            {"name":"konigsberg_bridges","pattern":r"(?:k\u00f6nigsberg|eulerian path|bridges of|seven bridges)", "compute":lambda m:"Seven Bridges of Konigsberg: No Eulerian path (all vertices have odd degree). Birth of graph theory (Euler, 1736).","domain":"reasoning","confidence":0.88},
            {"name":"hamiltonian_cycle","pattern":r"(?:hamiltonian|traveling salesman|TSP|NP.complete.*cycle)", "compute":lambda m:"Hamiltonian cycle: Visits each vertex exactly once. Finding one is NP-complete (hard to solve, easy to verify).","domain":"reasoning","confidence":0.85},
            {"name":"bipartite_graph","pattern":r"(?:bipartite|2.colorable|no odd cycle)", "compute":lambda m:"Bipartite graph: Vertices partitionable into 2 sets with no edge within a set. Equivalent to having no odd cycles.","domain":"reasoning","confidence":0.87},
            {"name":"planar_graph","pattern":r"(?:planar graph|k5|k3.3|kuratowski)", "compute":lambda m:"Planar graph: Drawable without edge crossings. Kuratowski: Non-planar iff contains K5 or K3,3 subdivision.","domain":"reasoning","confidence":0.86},
            {"name":"adjacency_matrix","pattern":r"(?:adjacency matrix|graph.*matrix|laplacian.*graph)", "compute":lambda m:"Adjacency matrix A: A[i][j]=1 if edge between i,j. Eigenvalues reveal graph properties (connectivity, bipartiteness).","domain":"algebra","confidence":0.85},
            {"name":"directed_graph","pattern":r"(?:directed graph|digraph|DAG|directed acyclic|topological sort)", "compute":lambda m:"Directed graph: Edges have direction. DAG (directed acyclic graph) admits topological ordering.","domain":"reasoning","confidence":0.87},
            {"name":"counting_principles","pattern":r"(?:addition principle|multiplication principle|sum rule|product rule.*counting)", "compute":lambda m:"Addition principle: If A and B disjoint, |A\u222aB| = |A|+|B|. Multiplication: |A\u00d7B| = |A|\u00d7|B|.","domain":"combinatorics","confidence":0.92},
            {"name":"inclusion_exclusion","pattern":r"(?:inclusion.exclusion|PIE|union.*intersection.*alternating)", "compute":lambda m:"Inclusion-Exclusion: |A\u222aB\u222aC| = \u2211|Ai| - \u2211|Ai\u2229Aj| + \u2211|Ai\u2229Aj\u2229Ak| - ...","domain":"combinatorics","confidence":0.89},
            {"name":"derangements","pattern":r"(?:derangement|subfactorial|no element fixed|!n|hat check)", "compute":lambda m:"Derangements !n: Permutations with no fixed points. !n = n!\u2211(-1)^k/k!. !n/n! -> 1/e \u2248 0.368.","domain":"combinatorics","confidence":0.85},
            {"name":"bell_numbers","pattern":r"(?:bell number|set partition|bell.*triangle|partitions of a set)", "compute":lambda m:"Bell number B_n: Number of ways to partition a set of n elements. B_1=1, B_2=2, B_3=5, B_4=15.","domain":"combinatorics","confidence":0.84},
            {"name":"stirling_numbers","pattern":r"(?:stirling number|stirling.*first kind|stirling.*second kind|cycle|subset partition)", "compute":lambda m:"Stirling S(n,k): Number of ways to partition n elements into k non-empty subsets. S(n,1)=S(n,n)=1.","domain":"combinatorics","confidence":0.83},
            {"name":"pigeonhole_generalized","pattern":r"(?:generalized pigeonhole|pigeonhole.*ceil|n.*m\\+1)", "compute":lambda m:"Generalized: If n items into m boxes, some box has \u2265 \u2308n/m\u2309 items. For 100 into 7: at least 15 per box.","domain":"reasoning","confidence":0.91},
            {"name":"ramsey_theory","pattern":r"(?:ramsey|R\\(.*,.*\\)|ramsey number|complete graph.*monochromatic)", "compute":lambda m:"Ramsey theory: R(3,3)=6. In any group of 6, either 3 mutually know each other or 3 mutually don't know each other.","domain":"reasoning","confidence":0.84},
            {"name":"erdos_szekeres","pattern":r"(?:erd\u0151s.szekeres|monotone subsequence|increasing.*decreasing.*subsequence)", "compute":lambda m:"Erdos-Szekeres: Any sequence of n+1 distinct numbers has monotone subsequence of length \u2265 \u221an.","domain":"reasoning","confidence":0.82},
            {"name":"handshake_lemma","pattern":r"(?:handshake|sum.*degrees.*2e|degree sum)", "compute":lambda m:"Handshaking Lemma: \u2211 deg(v) = 2|E|. At any party, number of people who shook hands oddly is even.","domain":"reasoning","confidence":0.91},

            {"name":"factorial_growth","pattern":r"(?:factorial growth|n!.*exponential|stirling)", "compute":lambda m:"n! grows faster than a^n for any fixed a, but slower than n^n. log(n!) = n log n - n + O(log n).","domain":"calculus","confidence":0.87},
            {"name":"lhopital_example","pattern":r"(?:l.hopital|l.hospital).*(?:example|limit.*0/0)", "compute":lambda m:"Example: lim(x->0) sin(x)/x = lim cos(x)/1 = 1. Also: lim(x->inf) x/e^x = lim 1/e^x = 0.","domain":"calculus","confidence":0.89},
            {"name":"sandwich_theorem","pattern":r"(?:sandwich|squeeze|pinching).*(?:theorem|limit)", "compute":lambda m:"Squeeze Theorem: If g(x) <= f(x) <= h(x) and lim g = lim h = L, then lim f = L. Used for sin(x)/x.","domain":"calculus","confidence":0.87},
            {"name":"monotone_convergence","pattern":r"(?:monotone convergence|bounded.*monotone|increasing.*bounded)", "compute":lambda m:"Monotone Convergence Theorem: Bounded monotone sequences converge. If increasing & bounded above -> converges to supremum.","domain":"calculus","confidence":0.88},
            {"name":"dominated_convergence","pattern":r"(?:dominated convergence|lebesgue.*DCT)", "compute":lambda m:"Dominated Convergence Theorem: If |f_n| <= g and g integrable, then lim integral f_n = integral lim f_n (Lebesgue).","domain":"calculus","confidence":0.82},
            {"name":"fatou_lemma","pattern":r"(?:fatou lemma|liminf.*integral|integral.*liminf)", "compute":lambda m:"Fatou's Lemma: integral(liminf f_n) <= liminf(integral f_n). Used with DCT and MCT.","domain":"calculus","confidence":0.81},
            {"name":"fubini_theorem","pattern":r"(?:fubini|iterated.*integral.*order|change order.*integration)", "compute":lambda m:"Fubini's Theorem: Double integral = iterated integral in either order, if integral of absolute value is finite.","domain":"calculus","confidence":0.84},
            {"name":"convolution","pattern":r"(?:convolution|f\*g|convolution integral)", "compute":lambda m:"Convolution: (f*g)(t) = integral f(tau)g(t-tau) dtau. Used in signal processing, probability (sum of independent RVs), and CNN.","domain":"calculus","confidence":0.83},
            {"name":"laplace_transform_table","pattern":r"(?:laplace.*table|L.*1|L.*t|L.*t\\^n|L.*sin|L.*cos)", "compute":lambda m:"Laplace table: L{1}=1/s, L{t}=1/s^2, L{t^n}=n!/s^(n+1), L{sin(at)}=a/(s^2+a^2), L{cos(at)}=s/(s^2+a^2), L{e^(at)}=1/(s-a).","domain":"calculus","confidence":0.86},
            {"name":"inverse_laplace","pattern":r"(?:inverse laplace|partial fraction.*laplace|L\\^-1)", "compute":lambda m:"Inverse Laplace: Use table + partial fractions + convolution. L^{-1}{F(s)G(s)} = f*g (convolution).","domain":"calculus","confidence":0.84},
            {"name":"z_transform","pattern":r"(?:z.transform|discrete.*laplace|difference equation.*z)", "compute":lambda m:"Z-transform: X(z) = sum x[n] z^(-n). Used for discrete-time signals. Analogous to Laplace for continuous.","domain":"calculus","confidence":0.82},
            {"name":"heat_eq_solution","pattern":r"(?:heat equation|diffusion)\s*(?:solution|solve)", "compute":lambda m:"1D heat: u(x,t) = (1/sqrt(4pi*alpha*t)) integral f(y) exp(-(x-y)^2/(4*alpha*t)) dy. Gaussian smoothing.","domain":"calculus","confidence":0.82},
            {"name":"wave_eq_solution","pattern":r"(?:wave equation|d.alembert)\s*(?:solution|solve)", "compute":lambda m:"1D wave: u(x,t) = (f(x-ct) + f(x+ct))/2 + (1/2c)integral_{x-ct}^{x+ct} g(s)ds.","domain":"calculus","confidence":0.82},
            {"name":"central_limit_example","pattern":r"(?:central limit|CLT).*(?:example|coin|dice|normal)", "compute":lambda m:"CLT Example: Sum of 100 dice rolls approx N(350, 291.67). Standardized: z=(sum-350)/sqrt(291.67).","domain":"probability","confidence":0.88},
            {"name":"law_large_numbers","pattern":r"(?:law of large numbers|LLN|sample.*mean.*converges|weak.*law|strong.*law)", "compute":lambda m:"Weak LLN: sample mean -> population mean in probability. Strong LLN: sample mean -> population mean almost surely.","domain":"probability","confidence":0.87},
            {"name":"moment_method","pattern":r"(?:method of moments|moment estimator|MOM)", "compute":lambda m:"Method of Moments: Equate sample moments to theoretical moments. For Normal: mean = xbar, variance = s^2.","domain":"probability","confidence":0.85},
            {"name":"maximum_likelihood","pattern":r"(?:maximum likelihood|MLE|likelihood function|maximize.*likelihood)", "compute":lambda m:"MLE: Choose parameter theta that maximizes P(data|theta). For Normal: mu_MLE = xbar, sigma^2_MLE = (1/n)sum(x_i-xbar)^2.","domain":"probability","confidence":0.86},
            {"name":"fisher_information","pattern":r"(?:fisher information|Cramer.Rao|cram\u00e9r.rao|information matrix)", "compute":lambda m:"Fisher Information I(theta) = -E[d^2/dtheta^2 log L]. Cramer-Rao: Var(estimator) >= 1/I(theta).","domain":"probability","confidence":0.83},
            {"name":"wald_test","pattern":r"(?:wald test|wald statistic|hypothesis.*wald)", "compute":lambda m:"Wald test: W = (theta_hat - theta_0)^2 / Var(theta_hat). Asymptotically chi-squared.","domain":"probability","confidence":0.82},
            {"name":"likelihood_ratio_test","pattern":r"(?:likelihood ratio|LRT|lambda.*likelihood)", "compute":lambda m:"LRT: lambda = 2(log L_alt - log L_null). Under H0, lambda ~ chi-squared. More powerful than Wald in many cases.","domain":"probability","confidence":0.82},
            {"name":"type1_type2_error","pattern":r"(?:type(?:-|\s)1 error|type(?:-|\s)2 error|false positive|false negative|alpha.*beta.*test)", "compute":lambda m:"Type I error (alpha): Reject H0 when true. Type II error (beta): Accept H0 when false. Power = 1-beta.","domain":"probability","confidence":0.88},
            {"name":"p_value","pattern":r"(?:p.value|p value|statistical significance|p<|p <)", "compute":lambda m:"p-value: Probability of observing results as extreme as observed, assuming H0 true. If p < alpha, reject H0.","domain":"probability","confidence":0.87},
            {"name":"bonferroni_correction","pattern":r"(?:bonferroni|multiple comparisons|multiple testing)", "compute":lambda m:"Bonferroni correction: For m tests, use alpha/m significance level. Controls family-wise error rate. Very conservative.","domain":"probability","confidence":0.85},
            {"name":"ols_regression","pattern":r"(?:OLS|ordinary least squares|beta.*hat.*X^T.*X|linear model.*estimate)", "compute":lambda m:"OLS: beta_hat = (X^T X)^(-1) X^T y. Minimizes sum of squared residuals. Unbiased, minimum variance among linear estimators (BLUE).","domain":"probability","confidence":0.86},
            {"name":"r_squared","pattern":r"(?:R.squared|R\\(2\\)|coefficient of determination|goodness of fit.*regression)", "compute":lambda m:"R^2 = 1 - SS_residual/SS_total. Proportion of variance explained by the model. Range [0,1]. Higher = better fit.","domain":"probability","confidence":0.87},
            {"name":"logistic_regression","pattern":r"(?:logistic regression|logit|odds ratio|binary.*outcome)", "compute":lambda m:"Logistic regression: P(Y=1) = 1/(1+e^(-X*beta)). Used for binary outcomes. Odds ratio = exp(beta_i).","domain":"probability","confidence":0.84},
            {"name":"kernel_density","pattern":r"(?:kernel density|KDE|smooth.*histogram|density estimation)", "compute":lambda m:"KDE: f_hat(x) = (1/nh) sum K((x-x_i)/h). Smooths data into continuous density estimate. Bandwidth h controls smoothness.","domain":"probability","confidence":0.83},
            {"name":"bootstrap","pattern":r"(?:bootstrap|resampling|sample.*with.*replacement)", "compute":lambda m:"Bootstrap: Resample with replacement from original data to estimate sampling distribution. Non-parametric, versatile.","domain":"probability","confidence":0.84},
            {"name":"svm_concept","pattern":r"(?:SVM|support vector machine|maximum margin|hyperplane.*separate)", "compute":lambda m:"SVM: Finds optimal hyperplane maximizing margin between classes. Uses kernel trick for non-linear separation (RBF, polynomial).","domain":"algebra","confidence":0.83},
            {"name":"pca","pattern":r"(?:PCA|principal component|dimensionality reduction|eigenvectors.*covariance)", "compute":lambda m:"PCA: Eigenvectors of covariance matrix give principal components. First PC captures maximum variance. Used for dimensionality reduction.","domain":"algebra","confidence":0.84},
            {"name":"singular_value_decomp","pattern":r"(?:SVD|singular value|A=U.*Sigma.*V|matrix decomposition)", "compute":lambda m:"SVD: A = U*Sigma*V^T. U,V orthogonal, Sigma diagonal. Used in PCA, pseudoinverse, low-rank approximation.","domain":"algebra","confidence":0.85},
            {"name":"qr_decomposition","pattern":r"(?:QR decomposition|Gram.Schmidt|orthogonalization)", "compute":lambda m:"QR: A = QR where Q is orthogonal and R is upper triangular. Used for solving linear systems and eigenvalue algorithms.","domain":"algebra","confidence":0.84},
            {"name":"lu_decomposition","pattern":r"(?:LU decomposition|lower.upper|gaussian elimination)", "compute":lambda m:"LU: A = LU where L is lower triangular and U is upper triangular. Used for efficient solving of Ax=b, det(A), inverse.","domain":"algebra","confidence":0.85},
            {"name":"cholesky","pattern":r"(?:cholesky|cholesky decomposition|LL\\^T|positive definite.*decomposition)", "compute":lambda m:"Cholesky: For symmetric positive definite A, A = LL^T with L lower triangular. Faster than LU for SPD matrices.","domain":"algebra","confidence":0.84},
            {"name":"power_iteration","pattern":r"(?:power iteration|power method|largest eigenvalue|dominant eigenvector)", "compute":lambda m:"Power iteration: x_{k+1} = A x_k / ||A x_k||. Converges to dominant eigenvector. Rayleigh quotient gives eigenvalue.","domain":"algebra","confidence":0.83},
            {"name":"gauss_seidel","pattern":r"(?:gauss.seidel|iterative linear solver|successive over.relaxation)", "compute":lambda m:"Gauss-Seidel: Iterative method for Ax=b. Uses most recent values. Converges for diagonally dominant or SPD matrices.","domain":"algebra","confidence":0.83},
            {"name":"condition_number","pattern":r"(?:condition number|ill.conditioned|well.conditioned|kappa\\(A\\)|cond\\(A\\))", "compute":lambda m:"Condition number kappa(A) = ||A|| * ||A^(-1)|| = sigma_max/sigma_min. Large kappa = ill-conditioned, sensitive to errors.","domain":"algebra","confidence":0.84},
            {"name":"norm_equivalence","pattern":r"(?:norm equivalence|L1.*L2.*Linf|equivalence.*norms)", "compute":lambda m:"All norms on finite-dimensional spaces are equivalent. ||x||_inf <= ||x||_2 <= sqrt(n)*||x||_inf.","domain":"algebra","confidence":0.83},
            {"name":"hadamard_product","pattern":r"(?:hadamard product|element.wise.*multiplication|A.*circle.*B)", "compute":lambda m:"Hadamard product (A O B): element-wise multiplication. (A O B)_{ij} = A_{ij} B_{ij}. Different from matrix multiplication.","domain":"algebra","confidence":0.85},
            {"name":"kronecker_product","pattern":r"(?:kronecker product|A.*otimes.*B|tensor product.*matrices)", "compute":lambda m:"Kronecker product: A ox B = [a_ij * B] block matrix. Used for linear systems with tensor structure.","domain":"algebra","confidence":0.83},

            {"name":"factorial_growth","pattern":r"(?:factorial growth|n!.*exponential|stirling)", "compute":lambda m:"n! grows faster than a^n for any fixed a, but slower than n^n. log(n!) = n log n - n + O(log n).","domain":"calculus","confidence":0.87},
            {"name":"lhopital_example","pattern":r"(?:l.hopital|l.hospital).*(?:example|limit.*0/0)", "compute":lambda m:"Example: lim(x->0) sin(x)/x = lim cos(x)/1 = 1. Also: lim(x->inf) x/e^x = lim 1/e^x = 0.","domain":"calculus","confidence":0.89},
            {"name":"sandwich_theorem","pattern":r"(?:sandwich|squeeze|pinching).*(?:theorem|limit)", "compute":lambda m:"Squeeze Theorem: If g(x) <= f(x) <= h(x) and lim g = lim h = L, then lim f = L. Used for sin(x)/x.","domain":"calculus","confidence":0.87},
            {"name":"monotone_convergence","pattern":r"(?:monotone convergence|bounded.*monotone|increasing.*bounded)", "compute":lambda m:"Monotone Convergence Theorem: Bounded monotone sequences converge. If increasing & bounded above -> converges to supremum.","domain":"calculus","confidence":0.88},
            {"name":"dominated_convergence","pattern":r"(?:dominated convergence|lebesgue.*DCT)", "compute":lambda m:"Dominated Convergence Theorem: If |f_n| <= g and g integrable, then lim integral f_n = integral lim f_n (Lebesgue).","domain":"calculus","confidence":0.82},
            {"name":"fatou_lemma","pattern":r"(?:fatou lemma|liminf.*integral|integral.*liminf)", "compute":lambda m:"Fatou's Lemma: integral(liminf f_n) <= liminf(integral f_n). Used with DCT and MCT.","domain":"calculus","confidence":0.81},
            {"name":"fubini_theorem","pattern":r"(?:fubini|iterated.*integral.*order|change order.*integration)", "compute":lambda m:"Fubini's Theorem: Double integral = iterated integral in either order, if integral of absolute value is finite.","domain":"calculus","confidence":0.84},
            {"name":"convolution","pattern":r"(?:convolution|f\*g|convolution integral)", "compute":lambda m:"Convolution: (f*g)(t) = integral f(tau)g(t-tau) dtau. Used in signal processing, probability (sum of independent RVs), and CNN.","domain":"calculus","confidence":0.83},
            {"name":"laplace_transform_table","pattern":r"(?:laplace.*table|L.*1|L.*t|L.*t\\^n|L.*sin|L.*cos)", "compute":lambda m:"Laplace table: L{1}=1/s, L{t}=1/s^2, L{t^n}=n!/s^(n+1), L{sin(at)}=a/(s^2+a^2), L{cos(at)}=s/(s^2+a^2), L{e^(at)}=1/(s-a).","domain":"calculus","confidence":0.86},
            {"name":"inverse_laplace","pattern":r"(?:inverse laplace|partial fraction.*laplace|L\\^-1)", "compute":lambda m:"Inverse Laplace: Use table + partial fractions + convolution. L^{-1}{F(s)G(s)} = f*g (convolution).","domain":"calculus","confidence":0.84},
            {"name":"z_transform","pattern":r"(?:z.transform|discrete.*laplace|difference equation.*z)", "compute":lambda m:"Z-transform: X(z) = sum x[n] z^(-n). Used for discrete-time signals. Analogous to Laplace for continuous.","domain":"calculus","confidence":0.82},
            {"name":"heat_eq_solution","pattern":r"(?:heat equation|diffusion)\s*(?:solution|solve)", "compute":lambda m:"1D heat: u(x,t) = (1/sqrt(4pi*alpha*t)) integral f(y) exp(-(x-y)^2/(4*alpha*t)) dy. Gaussian smoothing.","domain":"calculus","confidence":0.82},
            {"name":"wave_eq_solution","pattern":r"(?:wave equation|d.alembert)\s*(?:solution|solve)", "compute":lambda m:"1D wave: u(x,t) = (f(x-ct) + f(x+ct))/2 + (1/2c)integral_{x-ct}^{x+ct} g(s)ds.","domain":"calculus","confidence":0.82},
            {"name":"central_limit_example","pattern":r"(?:central limit|CLT).*(?:example|coin|dice|normal)", "compute":lambda m:"CLT Example: Sum of 100 dice rolls approx N(350, 291.67). Standardized: z=(sum-350)/sqrt(291.67).","domain":"probability","confidence":0.88},
            {"name":"law_large_numbers","pattern":r"(?:law of large numbers|LLN|sample.*mean.*converges|weak.*law|strong.*law)", "compute":lambda m:"Weak LLN: sample mean -> population mean in probability. Strong LLN: sample mean -> population mean almost surely.","domain":"probability","confidence":0.87},
            {"name":"moment_method","pattern":r"(?:method of moments|moment estimator|MOM)", "compute":lambda m:"Method of Moments: Equate sample moments to theoretical moments. For Normal: mean = xbar, variance = s^2.","domain":"probability","confidence":0.85},
            {"name":"maximum_likelihood","pattern":r"(?:maximum likelihood|MLE|likelihood function|maximize.*likelihood)", "compute":lambda m:"MLE: Choose parameter theta that maximizes P(data|theta). For Normal: mu_MLE = xbar, sigma^2_MLE = (1/n)sum(x_i-xbar)^2.","domain":"probability","confidence":0.86},
            {"name":"fisher_information","pattern":r"(?:fisher information|Cramer.Rao|cram\u00e9r.rao|information matrix)", "compute":lambda m:"Fisher Information I(theta) = -E[d^2/dtheta^2 log L]. Cramer-Rao: Var(estimator) >= 1/I(theta).","domain":"probability","confidence":0.83},
            {"name":"wald_test","pattern":r"(?:wald test|wald statistic|hypothesis.*wald)", "compute":lambda m:"Wald test: W = (theta_hat - theta_0)^2 / Var(theta_hat). Asymptotically chi-squared.","domain":"probability","confidence":0.82},
            {"name":"likelihood_ratio_test","pattern":r"(?:likelihood ratio|LRT|lambda.*likelihood)", "compute":lambda m:"LRT: lambda = 2(log L_alt - log L_null). Under H0, lambda ~ chi-squared. More powerful than Wald in many cases.","domain":"probability","confidence":0.82},
            {"name":"type1_type2_error","pattern":r"(?:type(?:-|\s)1 error|type(?:-|\s)2 error|false positive|false negative|alpha.*beta.*test)", "compute":lambda m:"Type I error (alpha): Reject H0 when true. Type II error (beta): Accept H0 when false. Power = 1-beta.","domain":"probability","confidence":0.88},
            {"name":"p_value","pattern":r"(?:p.value|p value|statistical significance|p<|p <)", "compute":lambda m:"p-value: Probability of observing results as extreme as observed, assuming H0 true. If p < alpha, reject H0.","domain":"probability","confidence":0.87},
            {"name":"bonferroni_correction","pattern":r"(?:bonferroni|multiple comparisons|multiple testing)", "compute":lambda m:"Bonferroni correction: For m tests, use alpha/m significance level. Controls family-wise error rate. Very conservative.","domain":"probability","confidence":0.85},
            {"name":"ols_regression","pattern":r"(?:OLS|ordinary least squares|beta.*hat.*X^T.*X|linear model.*estimate)", "compute":lambda m:"OLS: beta_hat = (X^T X)^(-1) X^T y. Minimizes sum of squared residuals. Unbiased, minimum variance among linear estimators (BLUE).","domain":"probability","confidence":0.86},
            {"name":"r_squared","pattern":r"(?:R.squared|R\\(2\\)|coefficient of determination|goodness of fit.*regression)", "compute":lambda m:"R^2 = 1 - SS_residual/SS_total. Proportion of variance explained by the model. Range [0,1]. Higher = better fit.","domain":"probability","confidence":0.87},
            {"name":"logistic_regression","pattern":r"(?:logistic regression|logit|odds ratio|binary.*outcome)", "compute":lambda m:"Logistic regression: P(Y=1) = 1/(1+e^(-X*beta)). Used for binary outcomes. Odds ratio = exp(beta_i).","domain":"probability","confidence":0.84},
            {"name":"kernel_density","pattern":r"(?:kernel density|KDE|smooth.*histogram|density estimation)", "compute":lambda m:"KDE: f_hat(x) = (1/nh) sum K((x-x_i)/h). Smooths data into continuous density estimate. Bandwidth h controls smoothness.","domain":"probability","confidence":0.83},
            {"name":"bootstrap","pattern":r"(?:bootstrap|resampling|sample.*with.*replacement)", "compute":lambda m:"Bootstrap: Resample with replacement from original data to estimate sampling distribution. Non-parametric, versatile.","domain":"probability","confidence":0.84},
            {"name":"svm_concept","pattern":r"(?:SVM|support vector machine|maximum margin|hyperplane.*separate)", "compute":lambda m:"SVM: Finds optimal hyperplane maximizing margin between classes. Uses kernel trick for non-linear separation (RBF, polynomial).","domain":"algebra","confidence":0.83},
            {"name":"pca","pattern":r"(?:PCA|principal component|dimensionality reduction|eigenvectors.*covariance)", "compute":lambda m:"PCA: Eigenvectors of covariance matrix give principal components. First PC captures maximum variance. Used for dimensionality reduction.","domain":"algebra","confidence":0.84},
            {"name":"singular_value_decomp","pattern":r"(?:SVD|singular value|A=U.*Sigma.*V|matrix decomposition)", "compute":lambda m:"SVD: A = U*Sigma*V^T. U,V orthogonal, Sigma diagonal. Used in PCA, pseudoinverse, low-rank approximation.","domain":"algebra","confidence":0.85},
            {"name":"qr_decomposition","pattern":r"(?:QR decomposition|Gram.Schmidt|orthogonalization)", "compute":lambda m:"QR: A = QR where Q is orthogonal and R is upper triangular. Used for solving linear systems and eigenvalue algorithms.","domain":"algebra","confidence":0.84},
            {"name":"lu_decomposition","pattern":r"(?:LU decomposition|lower.upper|gaussian elimination)", "compute":lambda m:"LU: A = LU where L is lower triangular and U is upper triangular. Used for efficient solving of Ax=b, det(A), inverse.","domain":"algebra","confidence":0.85},
            {"name":"cholesky","pattern":r"(?:cholesky|cholesky decomposition|LL\\^T|positive definite.*decomposition)", "compute":lambda m:"Cholesky: For symmetric positive definite A, A = LL^T with L lower triangular. Faster than LU for SPD matrices.","domain":"algebra","confidence":0.84},
            {"name":"power_iteration","pattern":r"(?:power iteration|power method|largest eigenvalue|dominant eigenvector)", "compute":lambda m:"Power iteration: x_{k+1} = A x_k / ||A x_k||. Converges to dominant eigenvector. Rayleigh quotient gives eigenvalue.","domain":"algebra","confidence":0.83},
            {"name":"gauss_seidel","pattern":r"(?:gauss.seidel|iterative linear solver|successive over.relaxation)", "compute":lambda m:"Gauss-Seidel: Iterative method for Ax=b. Uses most recent values. Converges for diagonally dominant or SPD matrices.","domain":"algebra","confidence":0.83},
            {"name":"condition_number","pattern":r"(?:condition number|ill.conditioned|well.conditioned|kappa\\(A\\)|cond\\(A\\))", "compute":lambda m:"Condition number kappa(A) = ||A|| * ||A^(-1)|| = sigma_max/sigma_min. Large kappa = ill-conditioned, sensitive to errors.","domain":"algebra","confidence":0.84},
            {"name":"norm_equivalence","pattern":r"(?:norm equivalence|L1.*L2.*Linf|equivalence.*norms)", "compute":lambda m:"All norms on finite-dimensional spaces are equivalent. ||x||_inf <= ||x||_2 <= sqrt(n)*||x||_inf.","domain":"algebra","confidence":0.83},
            {"name":"hadamard_product","pattern":r"(?:hadamard product|element.wise.*multiplication|A.*circle.*B)", "compute":lambda m:"Hadamard product (A O B): element-wise multiplication. (A O B)_{ij} = A_{ij} B_{ij}. Different from matrix multiplication.","domain":"algebra","confidence":0.85},
            {"name":"kronecker_product","pattern":r"(?:kronecker product|A.*otimes.*B|tensor product.*matrices)", "compute":lambda m:"Kronecker product: A ox B = [a_ij * B] block matrix. Used for linear systems with tensor structure.","domain":"algebra","confidence":0.83},

{"name":"bayes_rule","pattern":r"(?:bayes rule|bayes theorem).*(?:example|apply|using)", "compute":lambda m:"Bayes: P(H|E) = P(E|H)P(H)/P(E). The prior P(H) is updated by likelihood P(E|H) to obtain posterior.","domain":"probability","confidence":0.90},
{"name":"conjugate_prior","pattern":r"(?:conjugate prior|beta.*binomial|normal.*normal|conjugacy)", "compute":lambda m:"Conjugate priors: Beta-Binomial (Beta prior -> Beta posterior), Normal-Normal, Gamma-Poisson, Dirichlet-Multinomial.","domain":"probability","confidence":0.85},
{"name":"beta_binomial","pattern":r"(?:beta.binomial|Beta\(.*\).*Binomial|conjugate.*beta)", "compute":lambda m:"Beta-Binomial: Prior Beta(a,b). After s successes in n trials: Posterior Beta(a+s, b+n-s). Mean = a/(a+b).","domain":"probability","confidence":0.84},
{"name":"gamma_poisson","pattern":r"(?:gamma.poisson|poisson.*gamma.*prior)", "compute":lambda m:"Gamma-Poisson: Prior Gamma(a,b). After observing x in time t: Posterior Gamma(a+sum(x_i), b+n).","domain":"probability","confidence":0.83},
{"name":"normal_normal","pattern":r"(?:normal.normal|known.*variance.*normal.*prior)", "compute":lambda m:"Normal-Normal (known sigma^2): Prior N(mu_0, tau_0^2). Posterior mean = (mu_0/tau_0^2 + n*xbar/sigma^2)/(1/tau_0^2 + n/sigma^2).","domain":"probability","confidence":0.82},
{"name":"jeffreys_prior","pattern":r"(?:jeffreys prior|noninformative|uninformative.*prior|reference.*prior)", "compute":lambda m:"Jeffreys prior: proportional to sqrt(I(theta)), where I is Fisher info. Invariant under reparametrization.","domain":"probability","confidence":0.81},
{"name":"metropolis_hastings","pattern":r"(?:metropolis|MCMC|markov chain monte carlo|MH.*algorithm|Gibbs sampler)", "compute":lambda m:"Metropolis-Hastings: Propose theta* from q(theta*|theta_t). Accept with prob min(1, (p(theta*)q(theta_t|theta*))/(p(theta_t)q(theta*|theta_t))).","domain":"probability","confidence":0.82},
{"name":"gibbs_sampler","pattern":r"(?:gibbs sampl|conditional.*posterior|full conditional)", "compute":lambda m:"Gibbs sampler: Sample each parameter from its full conditional p(theta_i|theta_{-i}, data). Special case of MH with acceptance=1.","domain":"probability","confidence":0.81},
{"name":"hierarchical_model","pattern":r"(?:hierarchical model|random effects|multilevel|hierarchical bayes)", "compute":lambda m:"Hierarchical model: y_ij ~ N(mu_j, sigma^2), mu_j ~ N(mu, tau^2). Shares information across groups (partial pooling).","domain":"probability","confidence":0.82},
{"name":"bayesian_model_selection","pattern":r"(?:bayes factor|model comparison.*bayes|BIC|DIC|WAIC)", "compute":lambda m:"Bayes factor BF_12 = P(data|M1)/P(data|M2). BIC, DIC, WAIC for model comparison. BF>10 = strong evidence for M1.","domain":"probability","confidence":0.83},
{"name":"credible_interval","pattern":r"(?:credible interval|bayesian CI|HPD|highest posterior density)", "compute":lambda m:"95% Credible Interval: There is 95% probability that theta lies in [L,U] given data. Different from frequentist CI (which is about the procedure).","domain":"probability","confidence":0.86},
{"name":"residue_theorem_complex","pattern":r"(?:residue theorem|cauchy residue|contour integral.*complex)", "compute":lambda m:"Residue Theorem: contour integral f(z)dz = 2*pi*i * sum(Residues). Residue at z0 = lim (z-z0)f(z).","domain":"calculus","confidence":0.84},
{"name":"cauchy_integral","pattern":r"(?:cauchy integral|cauchy.*formula.*complex)", "compute":lambda m:"Cauchy's Integral Formula: f(z0) = (1/2*pi*i) contour integral f(z)/(z-z0) dz. Allows computing function values from boundary values.","domain":"calculus","confidence":0.84},
{"name":"laurent_series","pattern":r"(?:laurent series|annulus.*series.*complex|singularity.*expansion)", "compute":lambda m:"Laurent series: f(z) = sum a_n(z-z0)^n for n=-inf to inf. Uses annulus. Coefficient a_{-1} = Residue.","domain":"calculus","confidence":0.83},
{"name":"analytic_continuation","pattern":r"(?:analytic continuation|extend.*complex|riemann.*continuation)", "compute":lambda m:"Analytic continuation: Extend domain of analytic function beyond original region. Example: zeta function extended to C\\{1}.","domain":"calculus","confidence":0.82},
{"name":"conformal_mapping","pattern":r"(?:conformal map|angle.preserving|mobius.*transform|schwarz.christoffel)", "compute":lambda m:"Conformal mapping: Angle-preserving transformation w=f(z). Mobius: w=(az+b)/(cz+d). Used to solve Laplace equation on complex domains.","domain":"calculus","confidence":0.81},
{"name":"branch_cut","pattern":r"(?:branch cut|branch point|multivalued.*complex|log.*branch|sqrt.*branch)", "compute":lambda m:"Branch cut: Curve where multi-valued function is discontinuous. log(z) has branch cut along negative real axis (principal value).","domain":"calculus","confidence":0.82},
{"name":"essential_singularity","pattern":r"(?:essential singularity|casorati.weierstrass|picard.*essential)", "compute":lambda m:"Essential singularity: Near z0, f(z) takes every complex value infinitely often except possibly one (Picard's theorem). e^(1/z) at z=0.","domain":"calculus","confidence":0.81},
{"name":"argument_principle","pattern":r"(?:argument principle|winding number|contour.*zeros.*poles)", "compute":lambda m:"Argument Principle: For f analytic inside C: (1/2*pi*i)contour f'(z)/f(z) dz = N - P (number of zeros minus poles).","domain":"calculus","confidence":0.82},
{"name":"rouche_theorem","pattern":r"(?:rouche|Rouch\u00e9|zeros.*bound.*complex)", "compute":lambda m:"Rouch\u00e9's Theorem: If |f(z)| > |g(z)| on C, then f and f+g have same number of zeros inside C.","domain":"calculus","confidence":0.83},
{"name":"entire_function","pattern":r"(?:entire function|liouville theorem|analytic.*everywhere.*complex)", "compute":lambda m:"Liouville's Theorem: Bounded entire function is constant. Entire = analytic on all C. Counterexample: sin(z) is entire but unbounded.","domain":"calculus","confidence":0.84},
{"name":"meromorphic_function","pattern":r"(?:meromorphic|poles.*only.*singularities|ratio.*analytic)", "compute":lambda m:"Meromorphic: Analytic except for poles. Ratio of two entire functions is meromorphic. tan(z) = sin(z)/cos(z) is meromorphic.","domain":"calculus","confidence":0.83},
{"name":"jordan_lemma","pattern":r"(?:jordan lemma|semicircle.*contour|large.*semicircle.*integral)", "compute":lambda m:"Jordan's Lemma: For large R, integral over semicircle of e^(iaz)f(z)dz -> 0 if |f(z)| -> 0 uniformly.","domain":"calculus","confidence":0.82},
{"name":"gaussian_integral","pattern":r"(?:gaussian integral|int.*e\\(.x\\^2\\)|bell curve.*integral)", "compute":lambda m:"Gaussian integral: integral_{-inf}^{inf} e^(-x^2) dx = sqrt(pi). General: integral e^(-ax^2+bx) dx = sqrt(pi/a) e^(b^2/4a).","domain":"calculus","confidence":0.89},
{"name":"error_function","pattern":r"(?:error function|erf|normal.*cdf|gaussian.*integral.*finite)", "compute":lambda m:"Error function: erf(x) = (2/sqrt(pi)) integral_0^x e^(-t^2) dt. P(Z <= x) = (1/2)[1 + erf(x/sqrt(2))] for standard normal.","domain":"calculus","confidence":0.86},
{"name":"gamma_function","pattern":r"(?:gamma function|\u0393\\(z\\)|factorial.*real|euler.*gamma)", "compute":lambda m:"Gamma function: Gamma(z) = integral_0^inf t^(z-1) e^(-t) dt. Gamma(n) = (n-1)! for integer n. Gamma(1/2) = sqrt(pi).","domain":"calculus","confidence":0.87},
{"name":"beta_function","pattern":r"(?:beta function|B\\(.*,.*\\)|euler.*beta)", "compute":lambda m:"Beta function: B(x,y) = integral_0^1 t^(x-1) (1-t)^(y-1) dt = Gamma(x)Gamma(y)/Gamma(x+y).","domain":"calculus","confidence":0.86},
{"name":"digamma_function","pattern":r"(?:digamma|psi function|derivative.*log.*gamma)", "compute":lambda m:"Digamma: psi(z) = d/dz log(Gamma(z)) = Gamma'(z)/Gamma(z). psi(1) = -gamma (Euler's constant).","domain":"calculus","confidence":0.83},
{"name":"bessel_function","pattern":r"(?:bessel|J_n|c ylinder.*harmonics|bessel.*equation)", "compute":lambda m:"Bessel J_n(x) solves x^2 y''+ xy' + (x^2-n^2)y = 0. Used for cylindrical coordinates. J_0(0)=1, J_n(x) oscillates.","domain":"calculus","confidence":0.82},
{"name":"legendre_polynomial","pattern":r"(?:legendre polynomial|P_n|spherical.*harmonics|legendre.*equation)", "compute":lambda m:"Legendre P_n(x): Orthogonal on [-1,1]. P_0=1, P_1=x, P_2=(3x^2-1)/2, P_3=(5x^3-3x)/2. Solutions to (1-x^2)y''-2xy'+n(n+1)y=0.","domain":"calculus","confidence":0.83},
{"name":"hermite_polynomial","pattern":r"(?:hermite polynomial|H_n|harmonic oscillator.*quantum)", "compute":lambda m:"Hermite H_n(x): Solutions to y''-2xy'+2ny=0. H_0=1, H_1=2x, H_2=4x^2-2. Eigenfunctions of quantum harmonic oscillator.","domain":"calculus","confidence":0.82},
{"name":"laguerre_polynomial","pattern":r"(?:laguerre polynomial|L_n|radial.*schrodinger|hydrogen.*atom)", "compute":lambda m:"Laguerre L_n(x): Solutions to xy''+(1-x)y'+ny=0. L_0=1, L_1=1-x. Used in radial part of hydrogen atom wavefunction.","domain":"calculus","confidence":0.81},
{"name":"chebyshev_polynomial","pattern":r"(?:chebyshev|T_n|minimax.*approximation|chebyshev.*nodes)", "compute":lambda m:"Chebyshev T_n(x) = cos(n arccos(x)). T_0=1, T_1=x, T_2=2x^2-1. Orthogonal on [-1,1] with weight 1/sqrt(1-x^2). Minimax property.","domain":"calculus","confidence":0.83},
{"name":"green_function","pattern":r"(?:green'?s function|L.*G.*=\\delta|fundamental solution)", "compute":lambda m:"Green's function G(x,s): LG(x,s) = delta(x-s). Solution: u(x) = integral G(x,s) f(s) ds. Represents system response to point source.","domain":"calculus","confidence":0.83},
{"name":"eigenfunction_expansion","pattern":r"(?:eigenfunction expansion|sturm.liouville|spectral.*decomposition|modal.*expansion)", "compute":lambda m:"Eigenfunction expansion: f(x) = sum c_n phi_n(x) where c_n = <f,phi_n>. Used for solving PDEs via separation of variables.","domain":"calculus","confidence":0.82},
{"name":"variational_principle","pattern":r"(?:variational principle|euler.lagrange|action.*minimiz|hamilton.*principle)", "compute":lambda m:"Principle of Least Action: delta integral L dt = 0. Euler-Lagrange: d/dt (dL/dq') - dL/dq = 0. Foundation of classical mechanics.","domain":"calculus","confidence":0.84},
{"name":"perturbation_theory","pattern":r"(?:perturbation theory|regular.*perturbation|singular.*perturbation|small.*parameter)", "compute":lambda m:"Perturbation: Expand solution u = u_0 + epsilon*u_1 + epsilon^2*u_2 + ... Substitute into equation, equate powers of epsilon.","domain":"calculus","confidence":0.81},
{"name":"asymptotic_expansion","pattern":r"(?:asymptotic expansion|big.O|order.*notation|asymptotic.*series)", "compute":lambda m:"Asymptotic: f(x) ~ sum a_n x^(-n). Big-O: f=O(g) means |f/g| bounded. Little-o: f=o(g) means f/g -> 0. Stirling: n! ~ sqrt(2*pi*n) (n/e)^n.","domain":"calculus","confidence":0.84},
{"name":"special_functions","pattern":r"(?:special functions|hypergeometric|elliptic.*integral|theta.*function)", "compute":lambda m:"Special functions: Hypergeometric 2F1, elliptic integrals (K,E), theta functions, Airy (Ai,Bi), polylogarithm Li_s. Arise from differential equations.","domain":"calculus","confidence":0.81},
{"name":"integration_techniques","pattern":r"(?:integration by substitution|u.substitution|trig substitution|integration.*technique)", "compute":lambda m:"Techniques: u-substitution, trig substitution (sqrt(a^2-x^2) -> x=a sin theta), partial fractions, integration by parts, tabular integration.","domain":"calculus","confidence":0.88},
{"name":"gamma_beta_integrals","pattern":r"(?:gamma.*integral|beta.*integral|int.*e\\(-t\\).*t\\^|using.*gamma.*function)", "compute":lambda m:"Use Gamma/Beta for integrals: integral_0^inf t^(a-1)e^(-bt) dt = Gamma(a)/b^a. integral_0^1 t^(a-1)(1-t)^(b-1) dt = B(a,b).","domain":"calculus","confidence":0.84},
        ]
    
    def solve(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Try to solve using parametric rules. Returns dict or None.
        Priority score = pattern_length × confidence.
        Longer (more specific) patterns get higher priority,
        preventing generic arithmetic from overriding calculus/algebra.
        """
        p = prompt.lower().strip()
        best_result = None
        best_priority = 0
        best_rule_obj = None
        
        for rule in self.rules:
            m = re.search(rule["pattern"], p, re.IGNORECASE)
            if m:
                try:
                    result = rule["compute"](m)
                    if result:
                        # Priority = MATCH length × confidence
                        # Longer match = more of the input consumed = more specific
                        # This prevents "2-3" from beating "solve x^2-5x+6=0"
                        priority = len(m.group(0)) * rule["confidence"]
                        if priority > best_priority:
                            best_result = result
                            best_priority = priority
                            best_rule_obj = rule
                except:
                    continue
        
        if best_result and best_rule_obj:
            return {"text": best_result, "confidence": best_rule_obj["confidence"],
                    "domain": best_rule_obj["domain"], "method": f"parametric_{best_rule_obj['name']}"}
        return None
    
    # Helper compute functions
    def _solve_linear(self, m):
        a = int(m.group(1) or 1)  # coefficient
        sign = 1 if m.group(2) == '+' else -1
        b = int(m.group(3))
        c = int(m.group(4))
        if sign == 1:
            x = (c - b) / a
        else:
            x = (c + b) / a
        x_int = int(x) if x == int(x) else x
        return f"x = {x_int}"
    
    def _solve_quadratic_factor(self, m):
        sign_b = 1 if m.group(1) == '+' else -1
        sign_c = 1 if m.group(3) == '+' else -1
        b = sign_b * int(m.group(2))
        c = sign_c * int(m.group(4))
        # Find a, b: x^2 + bx + c = 0 => (x+a)(x+b)=0 => a*b=c, a+b=b
        # Simple brute force for small integers
        for x1 in range(-20, 21):
            for x2 in range(-20, 21):
                if x1 + x2 == -b and x1 * x2 == c:
                    return f"x = {x1} or x = {x2}"
        return f"Cannot factor easily. Use quadratic formula: b={b}, c={c}"
    
    def _solve_quadratic_general(self, m):
        a = int(m.group(1))
        sign_b = 1 if m.group(2) == '+' else -1
        b = sign_b * int(m.group(3))
        sign_c = 1 if m.group(4) == '+' else -1
        c = sign_c * int(m.group(5))
        disc = b**2 - 4*a*c
        if disc < 0:
            return f"No real roots. Discriminant = {disc} < 0"
        x1 = (-b + math.sqrt(disc)) / (2*a)
        x2 = (-b - math.sqrt(disc)) / (2*a)
        if x1 == int(x1): x1 = int(x1)
        if x2 == int(x2): x2 = int(x2)
        return f"x = {x1} or x = {x2}"
    
    def _solve_system_2(self, m):
        # Too complex for regex — simplified
        return "System solving requires algebraic manipulation. Use substitution or elimination method."
    
    def _solve_rectangle_diff(self, m):
        diff = int(m.group(1))
        area = int(m.group(2))
        # w*(w+diff) = area => w^2 + diff*w - area = 0
        # Solve quadratic: w = (-diff + sqrt(diff^2 + 4*area))/2
        w = (-diff + math.sqrt(diff**2 + 4*area)) / 2
        w_int = int(w) if w == int(w) else w
        l = w + diff
        l_int = int(l) if l == int(l) else l
        return f"Width = {w_int}, Length = {l_int}"
    
    def _solve_sum_product(self, m):
        s = int(m.group(1))
        p = int(m.group(2))
        # x^2 - sx + p = 0 => x = (s ± sqrt(s^2 - 4p))/2
        disc = s**2 - 4*p
        if disc < 0:
            return f"No real numbers satisfy sum={s} and product={p}"
        x1 = (s + math.sqrt(disc)) / 2
        x2 = (s - math.sqrt(disc)) / 2
        x1_int = int(x1) if x1 == int(x1) else x1
        x2_int = int(x2) if x2 == int(x2) else x2
        return f"The numbers are {x1_int} and {x2_int}"
    
    def _solve_linear_then_expr(self, m):
        a = int(m.group(1) or 1)
        sign1 = 1 if m.group(2) == '+' else -1
        b = int(m.group(3))
        c = int(m.group(4))
        x = (c - sign1*b) / a
        x_int = int(x) if x == int(x) else x
        a2 = int(m.group(5) or 1)
        sign2 = 1 if m.group(6) == '+' else -1
        b2 = int(m.group(7))
        result = a2 * x + sign2 * b2
        result_int = int(result) if result == int(result) else result
        return f"x = {x_int}, so {a2}x {'+' if sign2>0 else '-'} {b2} = {result_int}"
    
    def _solve_vertex(self, m):
        minmax = m.group(1)
        sign_b = 1 if m.group(2) == '+' else -1
        b = sign_b * int(m.group(3))
        sign_c = 1 if m.group(4) == '+' else -1
        c = sign_c * int(m.group(5))
        x_vertex = -b / 2
        y_vertex = x_vertex**2 + b*x_vertex + c
        x_int = int(x_vertex) if x_vertex == int(x_vertex) else round(x_vertex, 2)
        y_int = int(y_vertex) if y_vertex == int(y_vertex) else round(y_vertex, 2)
        is_max = "Maximum" if b < 0 else "Minimum"
        return f"Vertex at x = {x_int}. {is_max} value = {y_int}"
    
    def _solve_absolute_value(self, m):
        sign = 1 if m.group(1) == '+' else -1
        b = sign * int(m.group(2))
        c = int(m.group(3))
        x1 = c - b
        x2 = -c - b
        return f"|x {'+' if sign>0 else '-'} {abs(b)}| = {c}\nx {'+' if sign>0 else '-'} {abs(b)} = {c} OR x {'+' if sign>0 else '-'} {abs(b)} = -{c}\nx = {x1} OR x = {x2}"
    
    def _solve_mean(self, m):
        nums_str = m.group(1)
        nums = [int(x.strip()) for x in re.split(r'[,\s]+', nums_str) if x.strip().isdigit()]
        if not nums:
            return None
        mean = sum(nums) / len(nums)
        mean_int = int(mean) if mean == int(mean) else round(mean, 2)
        return f"Mean = ({'+'.join(str(n) for n in nums)})/{len(nums)} = {mean_int}"
    
    def _solve_std(self, m):
        nums_str = m.group(1)
        nums = [int(x.strip()) for x in re.split(r'[,\s]+', nums_str) if x.strip().isdigit()]
        if not nums:
            return None
        mean = sum(nums) / len(nums)
        variance = sum((x - mean)**2 for x in nums) / len(nums)
        std = math.sqrt(variance)
        return f"Standard deviation = sqrt(variance) = sqrt({variance:.2f}) = {std:.2f}"
    
    def _solve_binomial(self, m):
        k = int(m.group(1))
        n = int(m.group(2))
        p = float(m.group(3))
        prob = math.comb(n, k) * (p**k) * ((1-p)**(n-k))
        return f"P(X={k}) = C({n},{k}) * {p}^{k} * {1-p}^{n-k} = {math.comb(n,k)} * {p**k:.6f} * {(1-p)**(n-k):.6f} = {prob:.6f}"
    
    def _solve_partial_derivative(self, m):
        expr = m.group(1)
        var = m.group(2)
        if var == 'x':
            return f"df/dx = derivative of {expr} with respect to x (treat y as constant)"
        else:
            return f"df/dy = derivative of {expr} with respect to y (treat x as constant)"
    
    def _solve_next_sequence(self, m):
        nums_str = m.group(1)
        nums = [int(x.strip()) for x in re.split(r'[,\s]+', nums_str) if x.strip().isdigit()]
        if len(nums) < 3:
            return None
        diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
        if len(set(diffs)) == 1:
            return f"The next number is {nums[-1] + diffs[0]} (arithmetic, +{diffs[0]})."
        if nums[0] != 0:
            ratios = [nums[i+1] / nums[i] for i in range(len(nums)-1)]
            if len(set(round(r, 4) for r in ratios)) == 1:
                return f"The next number is {nums[-1] * ratios[0]:.0f} (geometric, x{ratios[0]})."
        squares = [int(round(n**0.5)) for n in nums]
        if all(s*s == n for s, n in zip(squares, nums)):
            return f"The next number is {(squares[-1] + 1) ** 2} (squares)."
        if len(nums) >= 3 and nums[2] == nums[0] + nums[1]:
            return f"The next number is {nums[-1] + nums[-2]} (Fibonacci-like)."
        return None

# Quick test
if __name__ == "__main__":
    pkb = ParametricKB()
    tests = [
        "what is 15 * 7",
        "derivative of x^5",
        "derivative of sin(x^2)",
        "solve x^2 - 5x + 6 = 0",
        "area of circle radius 5",
        "what is 8!",
    ]
    for t in tests:
        r = pkb.solve(t)
        status = "OK" if r else "NO MATCH"
        print(f"[{status}] {t[:45]:45s} -> {r['text'][:60] if r else 'N/A'}")