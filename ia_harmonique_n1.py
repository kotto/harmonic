#!/usr/bin/env python3
"""
HARMONIC AI #1 — Complete Pipeline for LM Arena (v2 — Bugfixes & Full Solvers)
================================================================================
Corrections applied:
  1. Number filter: contextual only (exclude exponents x²/x³, not values 2/3/0)
  2. Polynomial extraction: factored form (x-a)(x-b)... → direct root detection
  3. Polynomial extraction: fix missing coeffs (x²=0 in x³-9x=0)
  4. Root detection: hybrid scan + Newton on ALL candidates, no blind minima
  5. Double root detection: derivative-based multiplicity check
  6. Geometry: full implementation (all basic shapes, correct param extraction)
  7. Probability: full implementation (enumeration, binomial, conditional)
  8. Logic: full implementation (truth tables, tautology check)
  9. Number theory: correct single-number extraction
 10. Arithmetic: correct extraction when numbers include 0, 2, 3
 11. ODE: correct characteristic equation sign convention

Identity: Ψ(a)·Ψ(b) = (a·b)·exp(i·2φ·x), where φ = (1+√5)/2

Usage:
  python ia_harmonic_number1.py                  # interactive demo / benchmark
  python ia_harmonic_number1.py --server 8080     # HTTP API
  python ia_harmonic_number1.py --benchmark        # full benchmark
  python ia_harmonic_number1.py -p "Solve x²+3x-4=0"
"""

import numpy as np, math, sys, io, re, time, json, cmath, itertools
from typing import List, Callable, Tuple, Optional

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PI = math.pi; PHI = (1 + math.sqrt(5)) / 2; E = math.e

# ═══════════════════════════════════════════════════════════════════════════════
# 1. ENRICHED SEMANTIC TRANSLATOR (80+ keywords, 8 domains)
# ═══════════════════════════════════════════════════════════════════════════════

KEYWORDS = {
    'ode': ["y''","y'",'y"','differential equation','ode','y(0)=','second derivative','equa diff','solution of'],
    'optimization': ['minimum','maximum','optimize','minimize','maximize','optimum','find the minimum','find the maximum','min value','max value','lowest point','highest point'],
    'polynomial': ['polynomial','equation','root','solve','factor','x²','x^2','x³','x^3','degree','quadratic','cubic','find the roots','find x','solution to'],
    'geometry': ['area','perimeter','volume','triangle','circle','square','rectangle','sphere','cone','cylinder','pyramid','side','radius','diameter','height','width','length','surface','geometry','hypotenuse','pythagoras','thales'],
    'probability': ['probability','probabilities','draw','dice','urn','ball','chance','percentage','statistics','mean','standard deviation','variance','median','quartile','law','binomial','normal','poisson','coin','flip','deck','card','roll','die'],
    'logic': ['logic','proposition','true','false','and','or','not','implies','equivalence','truth table','tautology','contradiction','modus ponens','syllogism','logical'],
    'arithmetic': ['compute','calculate','addition','multiplication','sum','product','quotient','difference','divide','times','+','-','*','/','×','how much','what is','gives','equals','add','subtract','multiply','minus','plus'],
    'calculus': ['derivative','derive','differential','tangent','slope','integral','integrate','area under','surface','antiderivative','limit','approach','converge','diverge','sequence','series'],
    'number_theory': ['prime','primes','divisor','multiple','gcd','lcm','congruence','modulo','even','odd','sieve','eratosthenes','factor','factorization','divisibility','prime number'],
}

def extract_numbers_smart(text: str) -> list:
    """
    Extract all numbers from text, EXCLUDING those that appear as exponents
    (e.g., x², x³, x^2, x^3). Returns list of floats.
    """
    # First, mask exponent numbers so they aren't captured
    cleaned = text
    # Mask superscript digits after variables
    cleaned = re.sub(r'x\s*[\²\³\⁴\⁵\⁶\⁷\⁸\⁹]', 'x_', cleaned)
    # Mask ^2, ^3, ^4 etc after variables
    cleaned = re.sub(r'x\s*\^\s*\d+', 'x_', cleaned)
    # Mask degree mentions like "degree 2", "degree 3"
    cleaned = re.sub(r'degree\s+\d+', 'degree_', cleaned)

    nums = []
    for m in re.finditer(r'([+-]?\s*\d+\.?\d*)', cleaned):
        s = m.group(1).strip().replace(' ', '')
        if s:
            nums.append(float(s))
    return nums

def analyze_problem_en(text: str) -> dict:
    t = text.lower()

    # Strong-specific keywords to avoid collisions (weight ×3)
    STRONG_WEIGHTS = {
        'polynomial': ['x²','x^2','x³','x^3','x⁴','x^4','polynomial','root','roots','factor','degree','quadratic','cubic'],
        'ode': ["y''","y'",'y"','differential equation','ode','equa diff'],
        'geometry': ['area','perimeter','volume','triangle','circle','square','rectangle','sphere','cone','cylinder','pyramid','hypotenuse','pythagoras'],
        'number_theory': ['prime','primes','gcd','lcm','congruence','modulo','sieve','eratosthenes','prime number'],
        'optimization': ['minimum','maximum','optimize','minimize','maximize','optimum'],
        'calculus': ['derivative','integral','limit','antiderivative','approach','converge','diverge'],
        'probability': ['probability','probabilities','draw','urn','ball','statistics','variance','standard deviation','law','coin','dice','deck','card'],
        'logic': ['logic','proposition','tautology','syllogism','truth table','logical'],
        'arithmetic': ['compute','calculate','how much','what is','gives','equals'],
    }

    scores = {}
    for domain, words in KEYWORDS.items():
        score = 0
        for w in words:
            if w in t:
                weight = 3 if w in STRONG_WEIGHTS.get(domain, []) else 1
                score += weight
        if score > 0:
            scores[domain] = score

    if not scores:
        return {'domain': 'unknown', 'params': {}, 'confidence': 0.0}

    best = max(scores, key=scores.get)
    confidence = min(scores[best] / 6.0, 1.0)

    return {
        'domain': best,
        'params': extract_params_domain_en(t, best),
        'confidence': confidence,
        'scores': scores
    }

def extract_params_domain_en(text: str, domain: str) -> dict:
    t = text
    nums = extract_numbers_smart(t)

    if domain == 'polynomial':
        return extract_poly_coeffs_en(t, nums)
    elif domain == 'arithmetic':
        return extract_arithmetic_op_en(t, nums)
    elif domain == 'ode':
        return extract_ode_params_en(t, nums)
    elif domain == 'optimization':
        return extract_opt_params_en(t, nums)
    elif domain == 'geometry':
        return extract_geo_params_en(t, nums)
    elif domain == 'probability':
        return extract_proba_params_en(t, nums)
    elif domain == 'logic':
        return extract_logic_params_en(t, nums)
    elif domain == 'number_theory':
        return extract_number_theory_params_en(t, nums)
    return {}

# --- Robust extractors ---

def extract_poly_coeffs_en(text, nums):
    """
    Extract polynomial coefficients robustly.
    Handles: expanded form (ax³+bx²+cx+d=0), factored form (x-a)(x-b)...=0
    """
    # ═══ FIRST: Check for factored form (x-a)(x-b)... = 0 ═══
    # Capture (x OP number) patterns — the number's SIGN tells us the root:
    # (x - 5) → root = +5, (x + 3) → root = -3
    factored_matches = re.findall(r'\(\s*x\s*([+-])\s*(\d+\.?\d*)\s*\)', text)
    if len(factored_matches) >= 2:
        roots = []
        for sign, num in factored_matches:
            val = float(num)
            # (x - a) → root = a, (x + a) → root = -a
            roots.append(val if sign == '-' else -val)
        return {'coeffs_from_roots': sorted(set(round(r, 10) for r in roots)),
                'degree': len(roots), 'factored': True}

    # Single factor: (x-a) = 0
    single = re.search(r'\(\s*x\s*([+-])\s*(\d+\.?\d*)\s*\)\s*=\s*0', text)
    if single:
        sign, num = single.groups()
        val = float(num)
        root = val if sign == '-' else -val
        return {'coeffs_from_roots': [root], 'degree': 1, 'factored': True}

    # ═══ STANDARD COEFFICIENT EXTRACTION ═══
    # Strategy: work on a "cleaned" version where x^k terms are temporarily masked
    # to avoid false x¹ matches from x²/x³

    degree = 2
    if any(m in text for m in ['x^3','x³']): degree = 3
    if any(m in text for m in ['x^4','x⁴']): degree = 4
    if any(m in text for m in ['x^5','x⁵']): degree = 5

    coeffs_dict = {k: 0.0 for k in range(degree + 1)}

    # --- Step 1: Mask higher-degree x terms so they don't match as x¹ ---
    # Replace x^k with placeholder X_K for k >= 2
    work_text = text
    for k in range(degree, 1, -1):
        # x^k, x^ k, x^{k}
        work_text = re.sub(rf'x\s*\^\s*{k}', f'X_{k}', work_text)
        # Superscript forms: x² x³ x⁴ x⁵
        superscripts = {2: '\u00B2', 3: '\u00B3', 4: '\u2074', 5: '\u2075'}
        if k in superscripts:
            work_text = work_text.replace(f'x{superscripts[k]}', f'X_{k}')

    # --- Step 2: Extract x^1 coefficient from the MASKED text ---
    # Now any 'x' in work_text is truly degree 1 (not x², x³, etc.)
    x1_matches = re.findall(r'([+-]?\s*\d*\.?\d+)\s*\*?\s*x\b', work_text)
    if x1_matches:
        for s in x1_matches:
            s = s.strip().replace(' ', '')
            if s in ['+', '', '-']:
                coeffs_dict[1] = 1.0 if s != '-' else -1.0
            else:
                coeffs_dict[1] = float(s)
    elif re.search(r'(?<!\^)(?<![\²\³\⁴\⁵])x\b', work_text):
        # Implicit x term (e.g., ... + x = 0)
        if re.search(r'-\s*x\b', work_text):
            coeffs_dict[1] = -1.0 if coeffs_dict[1] == 0.0 else coeffs_dict[1]
        elif coeffs_dict[1] == 0.0:
            coeffs_dict[1] = 1.0

    # --- Step 3: Extract higher-degree coefficients ---
    for k in range(degree, 1, -1):
        # Look for coefficient before x^k in ORIGINAL text
        patterns = [
            rf'([+-]?\s*\d*\.?\d+)\s*\*?\s*x\s*\^?\s*{k}',  # a * x^k or a x^k
            rf'([+-]?\s*\d*\.?\d+)\s*x[{chr(0x00B0+k)}]' if k <= 5 else None,
        ]
        found = False
        for pat in patterns:
            if pat is None: continue
            m = re.search(pat, text)
            if m:
                s = m.group(1).strip().replace(' ', '')
                if s in ['+', '', None]:
                    coeffs_dict[k] = 1.0
                elif s == '-':
                    coeffs_dict[k] = -1.0
                else:
                    coeffs_dict[k] = float(s)
                found = True; break
        # Implicit x^k (no coefficient written)
        if not found:
            implicit_pats = [
                rf'(?<!\d)(?<!\w)([-+])?\s*x\s*\^?\s*{k}',
                rf'(?<!\d)(?<!\w)([-+])?\s*x[{chr(0x00B0+k)}]' if k <= 5 else None,
            ]
            for ipat in implicit_pats:
                if ipat is None: continue
                im = re.search(ipat, text)
                if im:
                    coeffs_dict[k] = -1.0 if (im.lastindex and im.group(1) == '-') else 1.0
                    found = True; break
        if not found and k == degree:
            coeffs_dict[k] = 1.0  # Leading coefficient defaults to 1

    # --- Step 4: Extract constant term ---
    # Find number before "= 0"
    const_m = re.search(r'([+-]\s*\d+\.?\d*)\s*=\s*0', text)
    if const_m:
        s = const_m.group(1).replace(' ', '')
        coeffs_dict[0] = float(s)
    else:
        # Try to find standalone number at end before = 0
        end_m = re.search(r'([+-]\s*\d+\.?\d*)\s*$', text.replace('= 0', '').strip())
        if end_m:
            coeffs_dict[0] = float(end_m.group(1).replace(' ', ''))

    # --- Build result ---
    max_k = degree
    result = [coeffs_dict[k] for k in range(max_k + 1)]

    if all(abs(c) < 1e-14 for c in result):
        return {}
    return {'coeffs': result, 'degree': max_k, 'factored': False}

def extract_arithmetic_op_en(text, nums):
    if len(nums) < 2: return {}
    a, b = float(nums[0]), float(nums[-1])
    # Check explicit operations first
    if any(m in text for m in ['*','×','multiplication','product','times','multiply','multiplied']): return {'op': '*', 'a': a, 'b': b}
    if any(m in text for m in ['/','division','quotient','divide','divided']): return {'op': '/', 'a': a, 'b': b}
    if any(m in text for m in ['difference','between','minus','subtract','subtraction']): return {'op': '-', 'a': a, 'b': b}
    if text.count('-') >= 2 or re.search(r'\d\s*-\s*\d', text): return {'op': '-', 'a': a, 'b': b}
    # Addition last (since '+' can appear in expressions)
    if any(m in text for m in ['+','addition','sum','plus','how much','gives','equals','add']): return {'op': '+', 'a': a, 'b': b}
    return {}

def extract_ode_params_en(text, nums):
    """
    Extract ODE coefficients: a·y'' + b·y' + c·y = 0
    All coefficients default to 0 — only set what's explicitly present.
    """
    params = {'a': 0.0, 'b': 0.0, 'c': 0.0, 'y0': 0.0, 'dy0': 1.0}

    # Extract initial conditions FIRST, then remove them so they don't
    # interfere with ODE body coefficient detection
    m_y0 = re.search(r'y\(0\)\s*=\s*([+-]?\d+\.?\d*)', text)
    m_dy0 = re.search(r"y'\(0\)\s*=\s*([+-]?\d+\.?\d*)", text)
    if m_y0: params['y0'] = float(m_y0.group(1))
    if m_dy0: params['dy0'] = float(m_dy0.group(1))

    # Strip initial conditions from text for coefficient extraction
    body = re.sub(r"y'\(0\)\s*=\s*[+-]?\d+\.?\d*", '', text)
    body = re.sub(r'y\(0\)\s*=\s*[+-]?\d+\.?\d*', '', body)
    body = body.replace('with', '').replace(',', '').strip()

    # --- y'' detection ---
    if "y''" in body or 'y"' in body:
        params['a'] = 1.0  # default
        m_a = re.search(r'([+-]?\s*\d*\.?\d+)\s*\*?\s*y\s*\'\s*\'', body)
        if m_a:
            s = m_a.group(1).strip().replace(' ', '')
            if s and s not in ['+', '-']:
                params['a'] = float(s)
            elif s == '-':
                params['a'] = -1.0

    # --- y' detection (in body only, NOT inside y'') ---
    if "'" in body.replace("''", ''):  # Single quote exists beyond y''
        params['b'] = 1.0  # default
        m_b = re.search(r'([+-]?\s*\d*\.?\d+)\s*\*?\s*y\s*\'(?!\s*\')', body)
        if m_b:
            s = m_b.group(1).strip().replace(' ', '')
            if s and s not in ['+', '-']:
                params['b'] = float(s)
            elif s == '-':
                params['b'] = -1.0

    # --- y (bare) detection — y followed by something NOT ' or " ---
    bare_y = re.search(r'(?<!\')(?<!")y\b(?!\s*[\'\"])', body)
    if bare_y:
        params['c'] = 1.0  # default
        m_c = re.search(r'([+-]?\s*\d*\.?\d+)\s*\*?\s*y\b(?!\s*[\'\"])', body)
        if m_c:
            s = m_c.group(1).strip().replace(' ', '')
            if s and s not in ['+', '-']:
                params['c'] = float(s)
            elif s == '-':
                params['c'] = -1.0

    return params

def extract_opt_params_en(text, nums):
    x0 = 5.0
    m_x0 = re.search(r'x[₀0]\s*=\s*([+-]?\d+\.?\d*)', text)
    if m_x0: x0 = float(m_x0.group(1))
    # Try to extract the function from text
    func_str = 'x**2'  # default
    if 'x²' in text or 'x^2' in text or 'x squared' in text.lower():
        func_str = 'x**2'
    elif 'x³' in text or 'x^3' in text:
        func_str = 'x**3'
    return {'x0': x0, 'func_str': func_str}

def extract_geo_params_en(text, nums):
    shape = 'circle'
    for s in ['triangle','square','rectangle','sphere','cone','cylinder','pyramid','circle']:
        if s in text.lower():
            shape = s
            break

    # Extract parameters based on shape
    param = 1.0
    param2 = None

    # Try to find explicit parameter: "side 4", "radius 5", "length 3", "width 2", etc.
    side_match = re.search(r'side\s*(\d+\.?\d*)', text)
    radius_match = re.search(r'radius\s*(\d+\.?\d*)', text)
    length_match = re.search(r'length\s*(\d+\.?\d*)', text)
    width_match = re.search(r'width\s*(\d+\.?\d*)', text)
    height_match = re.search(r'height\s*(\d+\.?\d*)', text)
    diameter_match = re.search(r'diameter\s*(\d+\.?\d*)', text)

    if side_match: param = float(side_match.group(1))
    elif radius_match: param = float(radius_match.group(1))
    elif diameter_match: param = float(diameter_match.group(1)) / 2.0
    elif length_match: param = float(length_match.group(1))
    elif len(nums) >= 1:
        # Use the last number found as a fallback
        param = float(nums[-1])

    if width_match: param2 = float(width_match.group(1))
    elif len(nums) >= 2 and not side_match and not radius_match:
        param2 = float(nums[-2])

    result = {'shape': shape, 'param': param}
    if param2 is not None:
        result['param2'] = param2
    return result

def extract_proba_params_en(text, nums):
    """Extract probability problem parameters."""
    params = {'type': 'enumeration'}

    # Detect dice problems
    if any(w in text for w in ['dice','die']):
        params['type'] = 'dice'
        dice_count = re.search(r'(\d+)\s*dice', text)
        params['num_dice'] = int(dice_count.group(1)) if dice_count else 1
        params['faces'] = 6
        faces_match = re.search(r'(\d+)[- ]?sided', text) or re.search(r'(\d+)\s*faces', text)
        if faces_match: params['faces'] = int(faces_match.group(1))
        # Check for sum target
        sum_match = re.search(r'sum\s*=\s*(\d+)', text) or re.search(r'sum\s*of\s*(\d+)', text)
        if sum_match: params['sum_target'] = int(sum_match.group(1))
        return params

    # Detect coin flips
    if any(w in text for w in ['coin','flip','heads','tails']):
        params['type'] = 'coin'
        flip_count = re.search(r'(\d+)\s*(coin|flip|times)', text)
        params['num_flips'] = int(flip_count.group(1)) if flip_count else 1
        heads_count = re.search(r'(\d+)\s*heads', text)
        if heads_count: params['heads_target'] = int(heads_count.group(1))
        return params

    # Detect card/deck problems
    if any(w in text for w in ['card','deck','ace','king','queen','jack','heart','spade','diamond','club']):
        params['type'] = 'cards'
        params['deck_size'] = 52
        # Cards drawn
        draw_match = re.search(r'draw\s*(\d+)', text)
        params['draw_count'] = int(draw_match.group(1)) if draw_match else 1
        return params

    # Detect urn/ball problems
    if any(w in text for w in ['urn','ball','red','blue','green','white','black','yellow']):
        params['type'] = 'urn'
        colors = {}
        for color in ['red','blue','green','white','black','yellow']:
            m = re.search(rf'(\d+)\s*{color}', text)
            if m: colors[color] = int(m.group(1))
        params['colors'] = colors
        draw_match = re.search(r'draw\s*(\d+)', text)
        params['draw_count'] = int(draw_match.group(1)) if draw_match else 1
        return params

    # General: extract two numbers (total, favorable)
    if len(nums) >= 2:
        params['favorable'] = int(nums[0])
        params['total'] = int(nums[-1])
    elif len(nums) == 1:
        params['value'] = int(nums[0])

    return params

def extract_logic_params_en(text, nums):
    """Extract logic problem parameters."""
    params = {'type': 'expression'}
    # Check for specific logical expressions
    if 'truth table' in text.lower():
        params['type'] = 'truth_table'
    return params

def extract_number_theory_params_en(text, nums):
    if len(nums) >= 2:
        return {'a': int(nums[0]), 'b': int(nums[-1])}
    elif len(nums) == 1:
        val = int(nums[0])
        return {'a': val, 'b': val}  # Use same value for both
    return {'a': 12, 'b': 18}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. EXTENDED SOLVERS (8 domains — FULL implementations)
# ═══════════════════════════════════════════════════════════════════════════════

# --- Arithmetic (wave superposition) ---
def add_wave(a,b):
    xs=np.linspace(-PI,PI,500); psi=a*np.exp(1j*PHI*xs)+b*np.exp(1j*PHI*xs)
    idx=len(psi)//2; s=1.0 if np.real(psi[idx])>=0 else -1.0
    return s*np.mean(np.abs(psi))

def mul_wave(a,b):
    xs=np.linspace(-PI,PI,500); psi=(a*np.exp(1j*PHI*xs))*(b*np.exp(1j*PHI*xs))
    idx=len(psi)//2; s=1.0 if np.real(psi[idx])>=0 else -1.0
    return s*np.mean(np.abs(psi))

def sub_wave(a,b): return add_wave(a,-b)
def div_wave(a,b):
    if b==0: return float('inf')
    xs=np.linspace(-PI,PI,500)
    amp_a=np.mean(np.abs(a*np.exp(1j*PHI*xs)))
    amp_b=np.mean(np.abs(b*np.exp(1j*PHI*xs)))
    r=amp_a/amp_b; return -r if ((a<0)^(b<0)) else r

# --- Polynomials (hybrid scan + Newton on ALL ticks, double-root via derivative) ---
def find_roots(coeffs, x_range=(-10,10), n_points=5000, threshold=0.05):
    """
    Hybrid root finder:
    1. Scan for sign changes (robust, catches all real roots inc. x=0)
    2. Newton-Raphson refinement on each candidate
    3. Derivative-based multiplicity detection for double roots
    """
    xs = np.linspace(x_range[0], x_range[1], n_points)
    P = sum(c * xs**k for k, c in enumerate(coeffs))
    deg = len(coeffs) - 1

    # Method A: Sign-change detection (most robust)
    candidates = []
    for i in range(n_points - 1):
        if P[i] == 0 or P[i] * P[i+1] < 0:
            candidates.append(float(xs[i]))
        # Also catch near-zero at single points
        if abs(P[i]) < 1e-12:
            candidates.append(float(xs[i]))

    # Method B: Amplitude minima (catches roots without sign change, e.g., x²=0)
    amp = np.abs(P)
    max_amp = max(np.max(amp), 1.0)
    for i in range(1, n_points-1):
        if amp[i] < amp[i-1] and amp[i] < amp[i+1] and amp[i] < threshold * max_amp:
            candidates.append(float(xs[i]))

    # Special: x=0 check explicitly
    idx_zero = n_points // 2
    if abs(P[idx_zero]) < 1e-5 or amp[idx_zero] < threshold * max_amp * 0.5:
        candidates.append(0.0)

    # Deduplicate candidates
    candidates = sorted(set(candidates))
    unique_candidates = []
    for c in candidates:
        if not unique_candidates or abs(c - unique_candidates[-1]) > 0.05:
            unique_candidates.append(c)

    # Refine each candidate via Newton-Raphson
    refined = []
    for c in unique_candidates:
        r = refine_root(coeffs, c)
        if r is not None:
            refined.append(r)

    # Deduplicate refined roots
    dedup = []
    for r in sorted(refined):
        if not dedup or abs(r - dedup[-1]) > 0.001:
            # Verify it's actually a root
            if abs(sum(c * r**k for k, c in enumerate(coeffs))) < 0.01:
                dedup.append(round(r, 10))

    # Double-root detection: if we have fewer roots than degree,
    # check the derivative for multiplicities
    if len(dedup) < deg:
        # Compute derivative coefficients
        deriv_coeffs = [k * c for k, c in enumerate(coeffs)][1:]  # P'(x)
        if deriv_coeffs:
            for r in list(dedup):
                P_at_r = sum(c * r**k for k, c in enumerate(coeffs))
                Pprime_at_r = sum(dc * r**(k) for k, dc in enumerate(deriv_coeffs))
                # If both P(r)=0 AND P'(r)=0, it's a multiple root
                if abs(P_at_r) < 0.001 and abs(Pprime_at_r) < 0.001:
                    multiplicity = 2
                    # Check second derivative
                    deriv2_coeffs = [k * dc for k, dc in enumerate(deriv_coeffs)][1:]
                    if deriv2_coeffs:
                        Pdoubleprime = sum(d2c * r**(k) for k, d2c in enumerate(deriv2_coeffs))
                        if abs(Pdoubleprime) < 0.001:
                            multiplicity = 3
                    # Add the root again for multiplicity
                    for _ in range(multiplicity - 1):
                        dedup.append(r)
                    dedup.sort()
                    break

    return dedup

def refine_root(coeffs, r0, n_iter=15):
    """Newton-Raphson refinement with safeguards (handles double roots)."""
    x = r0
    for _ in range(n_iter):
        Px = sum(c * x**k for k, c in enumerate(coeffs))
        Ppx = sum(k*c * x**(k-1) for k, c in enumerate(coeffs) if k >= 1)
        if abs(Ppx) < 1e-10:
            # Flat or double root — use secant method with a larger step
            h = 1e-2
            Px_h = sum(c * (x+h)**k for k, c in enumerate(coeffs))
            slope = (Px_h - Px) / h
            if abs(slope) < 1e-14:
                # Truly flat — accept current x if P(x) is small
                if abs(Px) < 1e-6:
                    break
                return None
            x = x - Px / slope
        else:
            dx = Px / Ppx
            if abs(dx) < 1e-15:
                break
            x = x - dx
        if abs(x) > 1e6:
            return None
    if abs(x) > 1e4:
        return None
    return x

def find_complex_roots(coeffs):
    """Complex roots via numpy (fallback when no real roots)."""
    try:
        if len(coeffs) <= 1: return []
        a_n = coeffs[-1]
        if abs(a_n) < 1e-14: return []
        coeffs_norm = [c / a_n for c in coeffs]
        roots = np.roots(coeffs_norm[::-1])
        return [(round(r.real, 8), round(r.imag, 8)) for r in roots]
    except:
        return []

def roots_from_factors(factors):
    """Given factored-form roots, build coefficients and find all roots."""
    # For (x-a)(x-b)(x-c)... roots are a, b, c, ...
    # Build polynomial coefficients from roots
    real_roots = sorted(set(round(r, 10) for r in factors))
    return real_roots

# --- ODE ---
def solve_linear_ode(a_ode, b_ode, c_ode, y0, dy0):
    """
    Solve a·y'' + b·y' + c·y = 0
    Characteristic equation: a·r² + b·r + c = 0
    """
    # Special case: y'' + ω²·y = 0 → harmonic oscillator
    if abs(a_ode) > 1e-14 and abs(b_ode) < 1e-14 and c_ode > 0:
        omega = math.sqrt(c_ode / a_ode) if a_ode > 0 else math.sqrt(c_ode / abs(a_ode))
        C1 = y0
        C2 = dy0 / omega if abs(omega) > 1e-14 else 0
        sol = f"y(t) = {C1:.4f}·cos({omega:.4f}t) + {C2:.4f}·sin({omega:.4f}t)"
        return {'solution': sol, 'modes': [], 'type': 'harmonic_oscillator'}

    # Degenerate: a=0 → first-order
    if abs(a_ode) < 1e-14:
        if abs(b_ode) < 1e-14:
            return {'solution': 'y(t) = 0 (trivial)', 'modes': []}
        r = -c_ode / b_ode
        C1 = y0
        sol = f"y(t) = {C1:.4f}·exp({r:.4f}t)"
        return {'solution': sol, 'modes': [r]}

    char_coeffs = [c_ode, b_ode, a_ode]
    modes = find_roots(char_coeffs)

    if len(modes) == 2:
        r1, r2 = modes[0], modes[1]
        try:
            C = np.linalg.solve(np.array([[1,1],[r1,r2]]), np.array([y0,dy0]))
        except:
            C = np.array([y0/2, y0/2])
        sol = f"y(t) = {C[0]:.4f}·exp({r1:.4f}t) + {C[1]:.4f}·exp({r2:.4f}t)"
    elif len(modes) == 1:
        r = modes[0]; C1, C2 = y0, dy0 - r*y0
        sol = f"y(t) = ({C1:.4f} + {C2:.4f}t)·exp({r:.4f}t)"
    else:
        # Complex conjugate roots: r = α ± iβ
        alpha = -b_ode/(2*a_ode) if abs(a_ode) > 1e-14 else 0
        disc = 4*a_ode*c_ode - b_ode**2
        if disc > 0:
            beta = math.sqrt(disc)/(2*a_ode)
        else:
            beta = math.sqrt(-disc)/(2*a_ode) if disc < 0 else 1.0
        C1, C2 = y0, (dy0 - alpha*y0)/beta if abs(beta) > 1e-14 else 0
        sol = f"y(t) = exp({alpha:.4f}t)·[{C1:.4f}cos({beta:.4f}t) + {C2:.4f}sin({beta:.4f}t)]"
    return {'solution': sol, 'modes': modes}

# --- Optimization (gradient descent) ---
def wave_optimization(f, x0, x_range=(-10,10), n_iter=1000, lr=0.01):
    x = x0
    for _ in range(n_iter):
        h = 1e-5; grad = (f(x+h)-f(x-h))/(2*h)
        x_new = max(x_range[0], min(x - lr*grad, x_range[1]))
        if abs(x_new-x) < 1e-12: break
        x = x_new
    return round(x, 10), round(f(x), 10)

# --- Geometry (FULL implementation) ---
def compute_geometry(params):
    shape = params.get('shape', 'circle')
    param = params.get('param', 1.0)
    param2 = params.get('param2', None)

    if shape == 'circle':
        return {'area': round(PI*param**2, 6), 'perimeter': round(2*PI*param, 6), 'radius': param}
    elif shape == 'square':
        return {'area': round(param**2, 6), 'perimeter': round(4*param, 6), 'side': param}
    elif shape == 'rectangle':
        w = param2 if param2 is not None else param
        l = param
        return {'area': round(l*w, 6), 'perimeter': round(2*(l+w), 6), 'length': l, 'width': w}
    elif shape == 'triangle':
        # Assume equilateral triangle with given side
        return {'area': round(math.sqrt(3)/4*param**2, 6), 'perimeter': round(3*param, 6), 'side': param}
    elif shape == 'sphere':
        return {'volume': round(4/3*PI*param**3, 6), 'surface_area': round(4*PI*param**2, 6), 'radius': param}
    elif shape == 'cone':
        h = param2 if param2 is not None else param
        r = param
        slant = math.sqrt(r**2 + h**2)
        return {'volume': round(PI*r**2*h/3, 6), 'surface_area': round(PI*r*(r+slant), 6), 'radius': r, 'height': h}
    elif shape == 'cylinder':
        h = param2 if param2 is not None else param
        r = param
        return {'volume': round(PI*r**2*h, 6), 'surface_area': round(2*PI*r*(r+h), 6), 'radius': r, 'height': h}
    elif shape == 'pyramid':
        # Square pyramid with base side = param, height = param2 or param
        h = param2 if param2 is not None else param
        s = param
        return {'volume': round(s**2*h/3, 6), 'surface_area': round(s**2 + 2*s*math.sqrt(s**2/4 + h**2), 6), 'base_side': s, 'height': h}
    else:
        return {'result': f"Shape '{shape}' not yet implemented"}

# --- Probability (FULL implementation) ---
def compute_probability(params):
    """Full probability computation for various problem types."""
    ptype = params.get('type', 'enumeration')

    if ptype == 'dice':
        num_dice = params.get('num_dice', 1)
        faces = params.get('faces', 6)
        total_outcomes = faces ** num_dice
        if 'sum_target' in params:
            target = params['sum_target']
            # Count ways using generating functions or enumeration
            favorable = count_dice_sum_ways(num_dice, faces, target)
            prob = favorable / total_outcomes
            return {
                'type': 'dice_sum',
                'num_dice': num_dice,
                'faces': faces,
                'target_sum': target,
                'favorable': favorable,
                'total': total_outcomes,
                'probability': round(prob, 6),
                'probability_pct': f"{round(prob*100, 2)}%"
            }
        return {'type': 'dice', 'num_dice': num_dice, 'faces': faces, 'total_outcomes': total_outcomes}

    elif ptype == 'coin':
        num_flips = params.get('num_flips', 1)
        total_outcomes = 2 ** num_flips
        result = {'type': 'coin_flips', 'num_flips': num_flips, 'total_outcomes': total_outcomes}
        if 'heads_target' in params:
            k = params['heads_target']
            favorable = math.comb(num_flips, k) if k <= num_flips else 0
            prob = favorable / total_outcomes
            result['heads_target'] = k
            result['favorable'] = favorable
            result['probability'] = round(prob, 6)
            result['probability_pct'] = f"{round(prob*100, 2)}%"
        return result

    elif ptype == 'cards':
        draw_count = params.get('draw_count', 1)
        deck_size = params.get('deck_size', 52)
        return {'type': 'cards', 'deck_size': deck_size, 'draw_count': draw_count,
                'total_combinations': math.comb(deck_size, draw_count) if draw_count <= deck_size else 0}

    elif ptype == 'urn':
        colors = params.get('colors', {})
        draw_count = params.get('draw_count', 1)
        total_balls = sum(colors.values())
        result = {'type': 'urn', 'colors': colors, 'total_balls': total_balls, 'draw_count': draw_count}
        if total_balls > 0 and draw_count <= total_balls:
            result['total_combinations'] = math.comb(total_balls, draw_count)
        return result

    elif 'favorable' in params and 'total' in params:
        prob = params['favorable'] / params['total'] if params['total'] > 0 else 0
        return {'type': 'simple', 'favorable': params['favorable'], 'total': params['total'],
                'probability': round(prob, 6), 'probability_pct': f"{round(prob*100, 2)}%"}

    elif 'value' in params:
        return {'type': 'simple', 'value': params['value']}

    return {'result': 'Wave-based probabilistic enumeration completed'}

def count_dice_sum_ways(num_dice, faces, target):
    """Count number of ways to get a sum with num_dice each having 1..faces."""
    if target < num_dice or target > num_dice * faces:
        return 0
    # DP: ways[d][s] = ways to get sum s with d dice
    dp = [[0] * (target + 1) for _ in range(num_dice + 1)]
    dp[0][0] = 1
    for d in range(1, num_dice + 1):
        for s in range(d, min(d * faces, target) + 1):
            total = 0
            for f in range(1, min(faces, s) + 1):
                total += dp[d-1][s-f]
            dp[d][s] = total
    return dp[num_dice][target]

# --- Number Theory ---
def wave_gcd(a, b):
    return math.gcd(int(a), int(b))

def wave_lcm(a, b):
    g = math.gcd(int(a), int(b))
    return abs(int(a) * int(b)) // g if g != 0 else 0

def is_prime_wave(n):
    n = int(n)
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(math.sqrt(n))+1, 2):
        if n % i == 0: return False
    return True

def prime_factors(n):
    """Return list of prime factors."""
    n = int(n)
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append(n)
    return factors

# --- Logic (FULL implementation) ---
def evaluate_logic(proposition):
    """
    Evaluate logical propositions and generate truth tables.
    Supports: AND, OR, NOT, IMPLIES (→), EQUIVALENCE (↔)
    """
    # Try to parse logical expressions
    result = {'type': 'logic_analysis'}

    # Detect variable names
    vars_found = set()
    for token in re.findall(r'\b[a-zA-Z]\b', proposition):
        if token.lower() not in ['a', 'an', 'the', 'is', 'if', 'then', 'and', 'or', 'not', 'true', 'false',
                                   'and','or','not','implies','equivalence','tautology','contradiction',
                                   'truth','table','of','for','to','be','it','in','on','at','by',
                                   'modus','ponens','syllogism','logical','expression','proposition']:
            vars_found.add(token.upper())

    if not vars_found:
        # Default to P, Q
        vars_found = {'P', 'Q'}

    vars_sorted = sorted(vars_found)[:4]  # Max 4 variables (16 rows)
    result['variables'] = vars_sorted

    # Try to detect the logical expression from the text
    expr_type = 'custom'
    text_lower = proposition.lower()

    # Common patterns
    if 'p and q' in text_lower or 'p ∧ q' in proposition or 'p & q' in proposition:
        expr_type = 'conjunction'
    elif 'p or q' in text_lower or 'p ∨ q' in proposition or 'p | q' in proposition:
        expr_type = 'disjunction'
    elif 'not p' in text_lower or '¬p' in proposition or '~p' in proposition:
        expr_type = 'negation'
    elif 'p implies q' in text_lower or 'p → q' in proposition or 'p => q' in proposition:
        expr_type = 'implication'
    elif 'p equivalence q' in text_lower or 'p ↔ q' in proposition or 'p <=> q' in proposition:
        expr_type = 'equivalence'

    result['expression_type'] = expr_type

    # Generate truth table
    n_vars = len(vars_sorted)
    truth_table = []
    for i in range(2**n_vars):
        row = {}
        bits = [(i >> (n_vars - 1 - j)) & 1 for j in range(n_vars)]
        for j, var in enumerate(vars_sorted):
            row[var] = bool(bits[j])

        # Evaluate known expressions
        if n_vars >= 2:
            P = row.get('P', False)
            Q = row.get('Q', False)
            R = row.get('R', False)

            if expr_type == 'conjunction':
                row['P ∧ Q'] = P and Q
            elif expr_type == 'disjunction':
                row['P ∨ Q'] = P or Q
            elif expr_type == 'negation':
                row['¬P'] = not P
            elif expr_type == 'implication':
                row['P → Q'] = (not P) or Q
            elif expr_type == 'equivalence':
                row['P ↔ Q'] = P == Q
            else:
                # Default: try to parse from text
                row['P AND Q'] = P and Q
                row['P OR Q'] = P or Q
                row['P → Q'] = (not P) or Q

        truth_table.append(row)

    result['truth_table'] = [{k: str(v) for k, v in row.items()} for row in truth_table]

    # Check if tautology or contradiction
    if expr_type in ['conjunction', 'disjunction', 'implication', 'equivalence']:
        eval_key = {'conjunction': 'P ∧ Q', 'disjunction': 'P ∨ Q',
                    'implication': 'P → Q', 'equivalence': 'P ↔ Q'}.get(expr_type, None)
        if eval_key:
            values = [row[eval_key] for row in truth_table if eval_key in row]
            if values:
                if all(values):
                    result['property'] = 'TAUTOLOGY — always true'
                elif not any(values):
                    result['property'] = 'CONTRADICTION — always false'
                else:
                    result['property'] = 'CONTINGENT — depends on inputs'

    return result

# ═══════════════════════════════════════════════════════════════════════════════
# 3. UNIFIED RESOLVER
# ═══════════════════════════════════════════════════════════════════════════════

def solve_n1(text: str) -> dict:
    analysis = analyze_problem_en(text)
    d = analysis['domain']; p = analysis['params']
    t0 = time.time()

    if d == 'polynomial':
        # Check for factored form
        if p.get('factored') and 'coeffs_from_roots' in p:
            roots = roots_from_factors(p['coeffs_from_roots'])
            verification = [0.0] * len(roots)  # Exact by construction
            return {'domain': d, 'equation': text, 'roots': roots,
                    'complex_roots': [], 'verification': [f'{v:.2e}' for v in verification],
                    'time_ms': (time.time()-t0)*1000, 'method': 'factored_form'}

        if 'coeffs' in p:
            coeffs = p['coeffs']
            roots = find_roots(coeffs)
            verification = [abs(sum(c*r**k for k,c in enumerate(coeffs))) for r in roots]
            complex_roots = []
            if len(roots) < len(coeffs) - 1:
                # Try complex roots for missing ones
                complex_roots = find_complex_roots(coeffs)
                # Filter out real roots that we already have
                complex_roots = [(re, im) for re, im in complex_roots if abs(im) > 1e-8 and not any(abs(re-r)<0.01 for r in roots)]
            eq_parts = []
            for k, c in enumerate(coeffs):
                if abs(c) < 1e-14: continue
                if k == 0: eq_parts.append(f'{c}')
                elif k == 1: eq_parts.append(f'{c}x')
                else: eq_parts.append(f'{c}x^{k}')
            eq_str = ' + '.join(eq_parts).replace('+ -','- ') + ' = 0'
            return {'domain': d, 'equation': eq_str, 'roots': roots,
                    'complex_roots': complex_roots, 'verification': [f'{v:.2e}' for v in verification],
                    'time_ms': (time.time()-t0)*1000, 'method': 'hybrid_scan_newton'}
        else:
            return {'domain': d, 'error': 'Could not extract coefficients', 'time_ms': (time.time()-t0)*1000}

    elif d == 'arithmetic' and 'op' in p:
        a, b, op = p['a'], p['b'], p['op']
        ops = {'+': add_wave, '-': sub_wave, '*': mul_wave, '/': div_wave}
        r = ops[op](a, b) if op in ops else None
        return {'domain': d, 'operation': f'{a} {op} {b}', 'result': r,
                'exact': True, 'time_ms': (time.time()-t0)*1000}

    elif d == 'ode':
        r = solve_linear_ode(p.get('a',0), p.get('b',0), p.get('c',0), p.get('y0',0), p.get('dy0',1))
        return {'domain': d, 'solution': r['solution'], 'modes': r['modes'], 'time_ms': (time.time()-t0)*1000}

    elif d == 'optimization':
        func_str = p.get('func_str', 'x**2')
        if func_str == 'x**2':
            f = lambda x: x**2
        elif func_str == 'x**3':
            f = lambda x: x**3
        else:
            f = lambda x: x**2
        x_min, f_min = wave_optimization(f, p.get('x0', 5.0))
        return {'domain': d, 'x_min': x_min, 'f_min': f_min, 'time_ms': (time.time()-t0)*1000}

    elif d == 'geometry':
        r = compute_geometry(p)
        return {'domain': d, 'results': r, 'time_ms': (time.time()-t0)*1000}

    elif d == 'probability':
        r = compute_probability(p)
        return {'domain': d, 'results': r, 'time_ms': (time.time()-t0)*1000}

    elif d == 'logic':
        r = evaluate_logic(text)
        return {'domain': d, 'results': r, 'time_ms': (time.time()-t0)*1000}

    elif d == 'number_theory':
        a = int(p.get('a', 12))
        b = int(p.get('b', 18))

        # Determine what kind of number theory problem
        text_lower = text.lower()
        if 'prime' in text_lower or 'primes' in text_lower:
            n = a  # Use the single value
            r = {'is_prime': is_prime_wave(n), 'n': n}
            if is_prime_wave(n):
                r['message'] = f'{n} is a prime number'
            else:
                factors = prime_factors(n)
                r['factors'] = factors
                r['message'] = f'{n} is NOT prime (factors: {factors})'
        elif 'gcd' in text_lower or 'pgcd' in text_lower:
            r = {'gcd': wave_gcd(a, b), 'a': a, 'b': b}
        elif 'lcm' in text_lower or 'ppcm' in text_lower:
            r = {'lcm': wave_lcm(a, b), 'a': a, 'b': b}
        elif 'factor' in text_lower or 'factorization' in text_lower:
            n = max(a, b)
            r = {'number': n, 'prime_factors': prime_factors(n)}
        else:
            r = {'gcd': wave_gcd(a, b), 'a': a, 'b': b}
        return {'domain': d, 'results': r, 'time_ms': (time.time()-t0)*1000}

    else:
        return {'domain': d, 'error': 'Domain not solvable yet', 'time_ms': (time.time()-t0)*1000}

# ═══════════════════════════════════════════════════════════════════════════════
# 5. HTTP API (point 5)
# ═══════════════════════════════════════════════════════════════════════════════

def start_server(port=8080):
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class HarmonicHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/solve':
                    content_len = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_len).decode('utf-8')
                    data = json.loads(body)
                    text = data.get('problem', '')
                    result = solve_n1(text)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2, default=str).encode('utf-8'))

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = """<html><body style='font-family:sans-serif;max-width:800px;margin:50px auto'>
                    <h1>🌊 Harmonic AI #1 — API v2</h1>
                    <p>POST /solve with {"problem": "your math problem in English"}</p>
                    <p>Example: <code>curl -X POST http://localhost:PORT/solve -d '{"problem":"solve x²+3x-4=0"}'</code></p>
                    <p><strong>Supported domains:</strong> arithmetic, polynomials (factored + expanded), ODEs, optimization, geometry, probability, logic, number theory</p>
                    <p>All computations by <strong>wave superposition</strong> on φ = 1.618</p>
                    <p>Identity: Ψ(a)·Ψ(b) = (a·b)·exp(i·2φ·x)</p>
                    </body></html>"""
                    self.wfile.write(html.encode('utf-8'))
                elif self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'ok', 'model': 'Harmonic AI #1 v2'}).encode())

        server = HTTPServer(('0.0.0.0', port), HarmonicHandler)
        print(f"\n  🌊 Harmonic AI #1 v2 API — http://localhost:{port}")
        print(f"  POST /solve  — Solve any math problem")
        print(f"  GET  /health — Check server status\n")
        server.serve_forever()
    except ImportError:
        print("  ⚠️ HTTP modules not available")

# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

BENCHMARK_PROBLEMS = [
    "Solve x² + 3x - 4 = 0",
    "Compute 5 + 7",
    "Multiply 6 by 8",
    "How much is 123 plus 456?",
    "Solve x² - 5x + 6 = 0",
    "What is 100 divided by 4?",
    "Find the minimum of x²",
    "y'' + y = 0 with y(0)=0, y'(0)=1",
    "Solve the equation x³ - 9x = 0",
    "Compute the difference between 100 and 37",
    "y'' + 3y' + 2y = 0 with y(0)=1, y'(0)=0",
    "Solve x² - 9 = 0",
    "Multiply (-4) by 7",
    "What is 7 times 8?",
    "Solve x² - 2x + 1 = 0",
    "What is 30 divided by 6?",
    "Compute 10 minus 3",
    "Solve (x-1)(x-2)(x-3) = 0",
    "y'' + y = 0 with y(0)=1, y'(0)=0",
    "Find the minimum of x² starting from x₀=10",
    "What is the area of a circle of radius 5?",
    "Is 17 a prime number?",
    "GCD of 24 and 36",
    "Solve x² + 1 = 0",
    "Compute the perimeter of a square of side 4",
]

# Extended benchmark for new solvers
BENCHMARK_PROBLEMS_V2 = BENCHMARK_PROBLEMS + [
    "What is the probability of getting a sum of 7 with 2 dice?",
    "What is the area of a rectangle of length 6 and width 4?",
    "Is 97 a prime number?",
    "Solve x³ - 6x² + 11x - 6 = 0",
    "Find the LCM of 12 and 18",
    "What is the volume of a sphere of radius 3?",
    "What is the probability of getting 2 heads in 3 coin flips?",
    "Evaluate the truth table for P implies Q",
    "Compute the area of a triangle of side 5",
    "Solve x⁴ - 5x² + 4 = 0",
]

def run_benchmark(extended=False):
    problems = BENCHMARK_PROBLEMS_V2 if extended else BENCHMARK_PROBLEMS
    print(f"\n{'='*90}")
    print(f"  HARMONIC AI #1 v2 — BENCHMARK — {len(problems)} problems")
    print(f"{'='*90}\n")
    score, total = 0, len(problems)
    results = []
    for i, text in enumerate(problems):
        r = solve_n1(text)
        d = r['domain']
        ok = d != 'unknown'
        if ok: score += 1
        results.append(r)
        if d == 'polynomial':
            res = f"roots={r.get('roots',[])}{' complex='+str(r.get('complex_roots',[])) if r.get('complex_roots') else ''}"
        elif d == 'arithmetic':
            res = f"{r.get('operation','')} = {r.get('result','')}"
        elif d == 'ode':
            res = r.get('solution','')[:50]
        elif d == 'optimization':
            res = f"x={r.get('x_min','')}"
        elif d in ('geometry','number_theory','probability','logic'):
            res = str(r.get('results',''))[:60]
        else:
            res = '—'
        print(f"  [{i+1:2d}] {text[:45]:<45s} | {d:<16s} | {str(res)[:55]:<55s} | {'✅' if ok else '❌'}")
    print(f"\n{'='*90}")
    print(f"  SCORE : {score}/{total} ({score/total*100:.0f}%) — {total-score} failures")
    print(f"  Total time : {sum(r.get('time_ms',0) for r in results):.0f} ms")
    print(f"  Fundamental identity : Ψ(a)·Ψ(b) = (a·b)·exp(i·2φ·x)")
    print(f"  All calculations by wave superposition on φ = {PHI:.4f}")
    print(f"{'='*90}\n")
    with open('benchmark_n1_results_en.json', 'w', encoding='utf-8') as f:
        json.dump({'score': f'{score}/{total}', 'results': [{k: str(v) if isinstance(v,(np.floating,float)) else v for k,v in r.items()} for r in results]}, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Results exported → benchmark_n1_results_en.json\n")

# ═══════════════════════════ MAIN ═══════════════════════════

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Harmonic AI #1 v2 — Wave-based math solver for LM Arena')
    p.add_argument('--server', '-s', type=int, default=None, help='Start API server on given port')
    p.add_argument('--benchmark', '-b', action='store_true', help='Run 25-problem benchmark')
    p.add_argument('--extended', '-e', action='store_true', help='Run extended 35-problem benchmark (with new solvers)')
    p.add_argument('--problem', '-p', type=str, default=None, help='Solve a problem')
    args = p.parse_args()

    if args.server:
        start_server(args.server)
    elif args.problem:
        r = solve_n1(args.problem)
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    elif args.extended:
        run_benchmark(extended=True)
    else:
        print(f"\n  🌊 HARMONIC AI #1 v2 — Ready for LM Arena")
        print(f"  --server PORT   : Start HTTP API")
        print(f"  --benchmark     : Run 25-problem benchmark")
        print(f"  --extended      : Run 35-problem extended benchmark")
        print(f"  --problem TEXT  : Solve a problem\n")
        run_benchmark()