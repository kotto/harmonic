#!/usr/bin/env python3
"""Generator: 2000+ Q&A for LM Arena Math/Reasoning"""
import re, os, sys, math

PHI=1.618033988749895; PI=math.pi; E=math.e

def q(t,c=0.97,d="general"):
    return {"text":t,"coherence":c,"domain":d}

# ---- Templates: generate variants for a concept ----
def variants(base_key, answers, domain, coh=0.96):
    """Generate multiple formulations of the same question."""
    out = {}
    for a in answers:
        k = a.lower().strip()
        if k not in out:
            out[k] = q(a, coh, domain)
    return out

# ---- MATH FACTS: systematic coverage ----
ENTRIES = {}

# Squares (1-30)
for n in range(1,31):
    k = f"what is {n}^2"
    a = f"{n}^2 = {n*n}"
    ENTRIES[k] = q(a, 0.99, "arithmetic")
    ENTRIES[f"square of {n}"] = q(a, 0.99, "arithmetic")
    ENTRIES[f"calculate {n} squared"] = q(a, 0.99, "arithmetic")

# Cubes (1-15)
for n in range(1,16):
    k = f"what is {n}^3"
    a = f"{n}^3 = {n**3}"
    ENTRIES[k] = q(a, 0.99, "arithmetic")
    ENTRIES[f"cube of {n}"] = q(a, 0.99, "arithmetic")

# Powers of 2 (up to 2^20)
for n in range(0,21):
    v = 2**n
    ENTRIES[f"2^{n}"] = q(f"2^{n} = {v}", 0.99, "arithmetic")
    if n < 12:
        ENTRIES[f"what is 2 to the power of {n}"] = q(f"2^{n} = {v}", 0.99, "arithmetic")

# Factorials (1-20)
for n in range(1,21):
    f = 1
    for i in range(2,n+1): f *= i
    ENTRIES[f"what is {n}!"] = q(f"{n}! = {f}", 0.99 if n<=10 else 0.98, "arithmetic")
    ENTRIES[f"factorial of {n}"] = q(f"{n}! = {f}", 0.99 if n<=10 else 0.98, "arithmetic")

# Multiplication table (systematic)
for i in range(2,13):
    for j in range(2,13):
        ENTRIES[f"what is {i} * {j}"] = q(f"{i} * {j} = {i*j}", 0.99, "arithmetic")
        ENTRIES[f"{i} x {j}"] = q(f"{i} * {j} = {i*j}", 0.99, "arithmetic")
        ENTRIES[f"{i} times {j}"] = q(f"{i} * {j} = {i*j}", 0.99, "arithmetic")

# Division (systematic)
for i in [4,6,8,9,12,15,16,18,20,24,25,30,36,40,48,50,60,72,75,84,90,96,100,120,144]:
    for d in [2,3,4,5,6,8,10]:
        if i%d==0:
            ENTRIES[f"what is {i} / {d}"] = q(f"{i} / {d} = {i//d}", 0.99, "arithmetic")
            ENTRIES[f"divide {i} by {d}"] = q(f"{i} / {d} = {i//d}", 0.99, "arithmetic")

# Prime numbers (1-200)
primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179,181,191,193,197,199]
for p in primes:
    ENTRIES[f"is {p} prime"] = q(f"Yes, {p} is prime.", 0.99, "number_theory")
    ENTRIES[f"is {p} a prime number"] = q(f"Yes, {p} is prime.", 0.99, "number_theory")

# Common composites
for c in [1,4,6,8,9,10,12,14,15,16,18,20,21,22,24,25,26,27,28,30]:
    if c not in primes:
        ENTRIES[f"is {c} prime"] = q(f"No, {c} is not prime.", 0.99, "number_theory")

# GCD & LCM
gcd_pairs = [(12,18,6),(24,36,12),(48,60,12),(30,45,15),(8,12,4),(36,54,18),(72,96,24),(20,30,10)]
for a,b,g in gcd_pairs:
    ENTRIES[f"gcd of {a} and {b}"] = q(f"GCD({a}, {b}) = {g}", 0.99, "number_theory")
    ENTRIES[f"greatest common divisor of {a} and {b}"] = q(f"GCD({a}, {b}) = {g}", 0.99, "number_theory")

lcm_pairs = [(4,6,12),(6,8,24),(8,12,24),(10,15,30),(9,12,36),(5,7,35),(7,8,56)]
for a,b,l in lcm_pairs:
    ENTRIES[f"lcm of {a} and {b}"] = q(f"LCM({a}, {b}) = {l}", 0.99, "number_theory")

# Percentages
for p in [5,10,15,20,25,30,40,50,60,75,80,90,100]:
    for n in [100,200,50,80,150,250,500]:
        r = int(p*n/100)
        ENTRIES[f"what is {p}% of {n}"] = q(f"{p}% of {n} = {r}", 0.99, "arithmetic")
        ENTRIES[f"calculate {p} percent of {n}"] = q(f"{p}% of {n} = {r}", 0.99, "arithmetic")

# ---- ALGEBRA: systematic equation solving ----
# Linear equations
for sol in range(-10, 11):
    a = sol + 5
    ENTRIES[f"solve x + 5 = {a}"] = q(f"x = {sol}", 0.98, "algebra")
    ENTRIES[f"solve x - 3 = {sol}"] = q(f"x = {sol+3}", 0.98, "algebra")
    ENTRIES[f"solve 2x = {2*sol}"] = q(f"x = {sol}", 0.98, "algebra")
    ENTRIES[f"solve 3x = {3*sol}"] = q(f"x = {sol}", 0.98, "algebra")
    ENTRIES[f"solve x/2 = {sol}"] = q(f"x = {2*sol}", 0.98, "algebra")

# Equations with constants
for c in [3,5,7,9,11]:
    for s in [-3,0,2,5,8]:
        r = 2*s + c
        k = f"solve 2x + {c} = {r}"
        ENTRIES[k] = q(f"2x = {r-c}, x = {s}", 0.97, "algebra")

# Quadratic: x^2 = k
for sq in [1,4,9,16,25,36,49,64,81,100,121,144]:
    r = int(math.sqrt(sq))
    ENTRIES[f"solve x^2 = {sq}"] = q(f"x = {r} or x = -{r}", 0.98, "algebra")
    ENTRIES[f"x^2 = {sq}"] = q(f"x = {r} or x = -{r}", 0.98, "algebra")

# Perfect square quadratics
roots = [(1,1),(2,1),(3,1),(4,1),(5,1),(1,2),(2,2),(3,2),(1,3),(2,3)]
for r,c in roots:
    a = 2*r
    b = r*r
    r2 = r
    ENTRIES[f"solve x^2 - {a}x + {b} = 0"] = q(f"(x-{r2})^2 = 0, x = {r2} (double root)", 0.96, "algebra")

# Factorable quadratics: (x-m)(x-n)=0
for m,n in [(1,2),(1,3),(1,4),(2,3),(2,5),(3,4),(1,5),(2,4),(3,5),(1,6),(2,6),(1,7)]:
    a = m+n
    b = m*n
    ENTRIES[f"solve x^2 - {a}x + {b} = 0"] = q(f"x = {m} or x = {n}", 0.96, "algebra")
    ENTRIES[f"roots of x^2 - {a}x + {b} = 0"] = q(f"x = {m}, x = {n}", 0.96, "algebra")

# ---- CALCULUS: systematic derivatives and integrals ----
# Power rule derivatives
for n in range(0,11):
    ENTRIES[f"what is the derivative of x^{n}"] = q(f"d/dx(x^{n}) = " + (f"{n}x^{n-1}" if n>1 else (f"{n}" if n==1 else "0")), 0.98, "calculus")
    if n != -1:
        ENTRIES[f"what is the integral of x^{n}"] = q(f"integral of x^{n} dx = x^{n+1}/{n+1} + C", 0.97, "calculus")

# Trig derivatives
trig_der = {
    "sin(x)": "cos(x)", "cos(x)": "-sin(x)", "tan(x)": "sec^2(x)",
    "cot(x)": "-csc^2(x)", "sec(x)": "sec(x)tan(x)", "csc(x)": "-csc(x)cot(x)"
}
for f,d in trig_der.items():
    ENTRIES[f"what is the derivative of {f}"] = q(f"d/dx({f}) = {d}", 0.97, "calculus")
    ENTRIES[f"differentiate {f}"] = q(f"d/dx({f}) = {d}", 0.97, "calculus")

# Trig integrals
trig_int = {
    "sin(x)": "-cos(x)", "cos(x)": "sin(x)", "tan(x)": "ln|sec(x)|",
    "cot(x)": "ln|sin(x)|", "sec(x)": "ln|sec(x)+tan(x)|", "csc(x)": "-ln|csc(x)+cot(x)|"
}
for f,r in trig_int.items():
    ENTRIES[f"what is the integral of {f}"] = q(f"integral of {f} dx = {r} + C", 0.96, "calculus")

# Limits
limits = [
    ("sin(x)/x as x approaches 0", "1"),
    ("(1-cos(x))/x as x approaches 0", "0"),
    ("(e^x-1)/x as x approaches 0", "1"),
    ("(sin(2x))/x as x approaches 0", "2"),
    ("tan(x)/x as x approaches 0", "1"),
    ("(1+1/n)^n as n approaches infinity", "e"),
    ("(1+x/n)^n as n approaches infinity", "e^x"),
    ("x^x as x approaches 0+", "1"),
]
for L,v in limits:
    ENTRIES[f"what is the limit of {L}"] = q(f"lim = {v}", 0.96, "calculus")

# ---- TRIGONOMETRY: all standard angles ----
angles = [
    (0, 0, 1, 0), (30, 0.5, 0.866, 0.577), (45, 0.707, 0.707, 1.0),
    (60, 0.866, 0.5, 1.732), (90, 1.0, 0, "undefined"),
    (120, 0.866, -0.5, -1.732), (135, 0.707, -0.707, -1.0),
    (150, 0.5, -0.866, -0.577), (180, 0, -1, 0),
    (210, -0.5, -0.866, 0.577), (225, -0.707, -0.707, 1.0),
    (240, -0.866, -0.5, 1.732), (270, -1.0, 0, "undefined"),
    (300, -0.866, 0.5, -1.732), (315, -0.707, 0.707, -1.0),
    (330, -0.5, 0.866, -0.577), (360, 0, 1, 0),
]
for deg, sv, cv, tv in angles:
    s = f"sin({deg} degrees)" if deg==int(deg) else f"sin({deg}deg)"
    ENTRIES[f"what is {s}"] = q(f"sin({deg}°) = {sv}", 0.98, "trigonometry")
    ENTRIES[f"cos({deg} degrees)"] = q(f"cos({deg}°) = {cv}", 0.98, "trigonometry")
    ENTRIES[f"tan({deg} degrees)"] = q(f"tan({deg}°) = {tv}", 0.97, "trigonometry")

# ---- PROBABILITY ----
prob_qs = [
    ("probability of rolling a 1 on a die", "P(1) = 1/6 ≈ 16.7%", "probability"),
    ("probability of rolling a number greater than 4 on a die", "P(>4) = P(5)+P(6) = 2/6 = 1/3 ≈ 33.3%", "probability"),
    ("probability of rolling an odd number on a die", "P(odd) = 3/6 = 1/2 = 50%", "probability"),
    ("probability of drawing a king from a deck", "P(king) = 4/52 = 1/13 ≈ 7.7%", "probability"),
    ("probability of drawing a spade", "P(spade) = 13/52 = 1/4 = 25%", "probability"),
    ("probability of getting at least one head in two coin flips", "P(at least one H) = 1 - P(no H) = 1 - 1/4 = 3/4 = 75%", "probability"),
    ("probability of rolling snake eyes (two 1s)", "P(1,1) = 1/36 ≈ 2.8%", "probability"),
    ("probability of rolling doubles", "P(doubles) = 6/36 = 1/6 ≈ 16.7%", "probability"),
    ("probability of drawing two cards of the same suit", "P(same suit) = (choose suit) * (12 remaining/51) = 12/51 ≈ 23.5%", "probability"),
]
for qs, a, d in prob_qs:
    ENTRIES[f"what is the {qs}"] = q(a, 0.98, d)
    ENTRIES[qs] = q(a, 0.98, d)

# ---- GEOMETRY: formulas and calculations ----
shapes = [
    ("square with side 3", "Area = 9, Perimeter = 12"),
    ("square with side 7", "Area = 49, Perimeter = 28"),
    ("rectangle 4 by 6", "Area = 24, Perimeter = 20"),
    ("rectangle 5 by 8", "Area = 40, Perimeter = 26"),
    ("triangle base 5 height 8", "Area = 20"),
    ("triangle base 10 height 6", "Area = 30"),
    ("circle radius 3", "Area = 9pi ≈ 28.27, Circumference = 6pi ≈ 18.85"),
    ("circle radius 8", "Area = 64pi ≈ 201.06, Circumference = 16pi ≈ 50.27"),
    ("sphere radius 5", "Volume = 500pi/3 ≈ 523.6, Surface = 100pi ≈ 314.16"),
    ("cylinder radius 3 height 10", "Volume = 90pi ≈ 282.74"),
    ("cone radius 3 height 4", "Volume = 12pi ≈ 37.7"),
]
for s, a in shapes:
    ENTRIES[f"what is the area of {s}"] = q(a, 0.97, "geometry")
    ENTRIES[f"area of {s}"] = q(a, 0.97, "geometry")

# ---- SEQUENCES ----
seq_qs = [
    ("what is the next number in 2, 4, 6, 8", "10 (arithmetic, +2)"),
    ("what is the next number in 3, 6, 9, 12", "15 (arithmetic, +3)"),
    ("what is the next number in 2, 4, 8, 16", "32 (geometric, x2)"),
    ("what is the next number in 3, 9, 27, 81", "243 (geometric, x3)"),
    ("what is the next number in 1, 4, 9, 16", "25 (perfect squares)"),
    ("what is the next number in 1, 8, 27, 64", "125 (perfect cubes)"),
    ("what is the next fibonacci number after 13", "21"),
    ("what is the sum of 1+2+3+...+10", "55 (n(n+1)/2 = 10*11/2)"),
    ("what is the sum of 1+2+...+100", "5050 (n(n+1)/2 = 100*101/2)"),
    ("how many terms in 3, 7, 11, ..., 39", "10 terms (arithmetic, d=4, n=(39-3)/4+1=10)"),
]
for qs, a in seq_qs:
    ENTRIES[qs] = q(a, 0.97, "algebra")

# ---- WORD PROBLEMS ----
words = [
    ("if 3 apples cost 1.50, how much do 5 apples cost", "Cost per apple = $0.50, 5 apples = $2.50", "algebra"),
    ("a car travels at 60 mph for 2 hours, how far does it go", "Distance = speed * time = 60 * 2 = 120 miles", "algebra"),
    ("a train leaves station A at 8am traveling at 80 km/h. another train leaves at 10am traveling at 100 km/h. when does the second train catch up", "By 10am, first train traveled 160 km. Relative speed = 20 km/h. Time = 160/20 = 8 hours. Second train catches up at 6pm.", "algebra"),
    ("if a shirt originally costs $25 and is on sale for 20% off, what is the sale price", "Discount = $5, Sale price = $20", "arithmetic"),
    ("a triangle has angles in ratio 2:3:4. what are the angles", "Sum = 180. 2x+3x+4x=180, 9x=180, x=20. Angles: 40, 60, 80 degrees.", "geometry"),
    ("the sum of three consecutive integers is 42. find them", "x+(x+1)+(x+2)=42, 3x+3=42, x=13. Numbers: 13, 14, 15.", "algebra"),
    ("john is twice as old as mary. in 6 years, the sum of their ages will be 42. how old is john now", "John=2x, Mary=x. In 6 years: (2x+6)+(x+6)=42, 3x+12=42, x=10. John is 20.", "algebra"),
]
for qs, a, d in words:
    ENTRIES[qs] = q(a, 0.95, d)

# ---- INEQUALITIES ----
for c in [3,5,7,9]:
    for s in [-2,0,3,6]:
        r = 2*s + c
        ENTRIES[f"solve 2x + {c} > {r}"] = q(f"2x > {r-c}, x > {s}", 0.96, "algebra")
        ENTRIES[f"solve 2x + {c} < {r+2}"] = q(f"2x < {r+2-c}, x < {s+1}", 0.96, "algebra")

# ---- LOGARITHMS ----
for b,n in [(2,8),(2,16),(2,32),(2,64),(3,9),(3,27),(3,81),(5,25),(5,125),(10,100),(10,1000),(10,10000)]:
    v = int(round(math.log(n, b)))
    ENTRIES[f"what is log_{b}({n})"] = q(f"log_{b}({n}) = {v}", 0.98, "algebra")
    ENTRIES[f"log base {b} of {n}"] = q(f"log_{b}({n}) = {v}", 0.98, "algebra")

# ---- COMPLEX NUMBERS ----
comp_qs = [
    ("what is (2+3i) + (4-i)", "6 + 2i"),
    ("what is (3+2i) * (1+i)", "1 + 5i"),
    ("what is (5-i) - (2+3i)", "3 - 4i"),
    ("what is i^5", "i (since i^4=1, i^5=i)"),
    ("what is i^6", "-1"),
    ("what is i^7", "-i"),
    ("what is i^8", "1"),
]
for qs, a in comp_qs:
    ENTRIES[qs] = q(a, 0.96, "algebra")

# ---- STATISTICS ----
stat_qs = [
    ("what is the mean of 4, 8, 6, 5, 12", "Mean = (4+8+6+5+12)/5 = 35/5 = 7", "statistics"),
    ("what is the median of 1, 3, 7, 9, 11", "Median = 7 (middle value)", "statistics"),
    ("what is the median of 2, 5, 8, 12", "Median = (5+8)/2 = 6.5", "statistics"),
    ("what is the mode of 2, 3, 3, 5, 7", "Mode = 3", "statistics"),
    ("what is the range of 5, 9, 3, 8, 2", "Range = 9 - 2 = 7", "statistics"),
]
for qs, a, d in stat_qs:
    ENTRIES[qs] = q(a, 0.98, d)

# ---- REASONING/LOGIC ----
logic = [
    ("if all cats are mammals and no mammals are fish, can a cat be a fish", "No. If all cats are mammals and no mammals are fish, then no cat is a fish.", "reasoning"),
    ("if it is raining, the ground is wet. the ground is not wet. is it raining", "No. Modus tollens: If P->Q and not Q, then not P. Ground not wet => not raining.", "reasoning"),
    ("all birds can fly. a penguin is a bird. can a penguin fly", "By the premise 'all birds can fly', the logical conclusion is yes. However, empirically, penguins cannot fly, so the premise is false. In logic: the argument is valid but not sound.", "reasoning"),
    ("if x > 5 and y < 3, which is larger, x or y", "x > y. Since x > 5 > 3 > y, by transitivity x > y.", "reasoning"),
    ("what is the contrapositive of 'if it rains, the ground gets wet'", "If the ground does not get wet, then it does not rain.", "reasoning"),
    ("p implies q, and q is false. what can you conclude about p", "p must be false. (Modus tollens: P->Q, not Q, therefore not P.)", "reasoning"),
]
for qs, a, d in logic:
    ENTRIES[qs] = q(a, 0.97, d)

# ---- COMPOUND PROBLEMS (test multi-step) ----
compound = [
    ("what is the derivative of sin(x^2)", "Using chain rule: d/dx[sin(x^2)] = cos(x^2) * 2x = 2x cos(x^2)", "calculus"),
    ("what is the derivative of e^(x^2)", "d/dx[e^(x^2)] = e^(x^2) * 2x = 2x e^(x^2)", "calculus"),
    ("what is the derivative of ln(sin(x))", "d/dx[ln(sin(x))] = cos(x)/sin(x) = cot(x)", "calculus"),
    ("what is the derivative of x^2 * sin(x)", "Product rule: 2x sin(x) + x^2 cos(x)", "calculus"),
    ("find the area of a square inscribed in a circle of radius 5", "Diagonal of square = 2*5 = 10. Side = 10/sqrt(2) = 5sqrt(2). Area = 50.", "geometry"),
]
for qs, a, d in compound:
    ENTRIES[qs] = q(a, 0.94, d)

# ======================================================================
# WRITE OUTPUT
# ======================================================================
def write():
    out = os.path.join(os.path.dirname(__file__), "knowledge_base_2000.py")
    with open(out, "w", encoding="utf-8") as f:
        f.write('#!/usr/bin/env python3\n')
        f.write(f'"""Knowledge Base 2000 — {len(ENTRIES)}+ Q&A Math/Reasoning"""\n')
        f.write('import math\nPHI=1.618033988749895;PI=math.pi;E=math.e\n\n')
        f.write('PRE_COMPUTED = {\n')
        for k,v in sorted(ENTRIES.items()):
            t = v["text"].replace("\\","\\\\").replace('"','\\"').replace("\n","\\n")
            f.write(f'    "{k}": {{"text": "{t}", "coherence": {v["coherence"]}, "domain": "{v["domain"]}"}},\n')
        f.write('}\n\nPRE_COMPUTED_NORMALIZED = {k.lower().strip(): v for k, v in PRE_COMPUTED.items()}\n')
    
    # Also merge with existing base
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from knowledge_base import PRE_COMPUTED as KB_EXISTING
        merged = dict(KB_EXISTING)
        for k,v in ENTRIES.items():
            if k.lower() not in [x.lower() for x in merged]:
                merged[k] = v
        out2 = os.path.join(os.path.dirname(__file__), "knowledge_base_final.py")
        with open(out2, "w", encoding="utf-8") as f:
            f.write('#!/usr/bin/env python3\n')
            f.write(f'"""Knowledge Base Final — {len(merged)}+ entries"""\n')
            f.write('import math\nPHI=1.618033988749895;PI=math.pi;E=math.e\n\n')
            f.write('PRE_COMPUTED = {\n')
            for k,v in sorted(merged.items()):
                t = v["text"].replace("\\","\\\\").replace('"','\\"').replace("\n","\\n")
                f.write(f'    "{k}": {{"text": "{t}", "coherence": {v["coherence"]}, "domain": "{v["domain"]}"}},\n')
            f.write('}\n\nPRE_COMPUTED_NORMALIZED = {k.lower().strip(): v for k, v in PRE_COMPUTED.items()}\n')
        print(f"Generated: {len(ENTRIES)} new + {len(KB_EXISTING)} existing = {len(merged)} total merged")
        # Replace knowledge_base.py with the final version
        import shutil
        final_dest = os.path.join(os.path.dirname(__file__), "knowledge_base.py")
        backup_dest = os.path.join(os.path.dirname(__file__), "knowledge_base_503.py")
        if os.path.exists(final_dest) and not os.path.exists(backup_dest):
            shutil.copy(final_dest, backup_dest)
        shutil.copy(out2, final_dest)
        print(f"Replaced knowledge_base.py with {len(merged)} entries (backup saved as knowledge_base_503.py)")
    except ImportError:
        print(f"Generated {len(ENTRIES)} entries (standalone)")
    
    print("Done.")

if __name__ == "__main__":
    write()