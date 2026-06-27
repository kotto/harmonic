#!/usr/bin/env python3
"""Generator: expand from 1920 to 5000+ entries"""
import os, sys, math, shutil

PHI=1.618033988749895; PI=math.pi; E=math.e

def q(t,c=0.97,d="general"):
    return {"text":t,"coherence":c,"domain":d}

sys.path.insert(0, os.path.dirname(__file__))
from knowledge_base import PRE_COMPUTED as KB

ENTRIES = dict(KB)
existing_keys = set(k.lower() for k in ENTRIES)

def add(k, text, coh=0.97, dom="general"):
    if k.lower() not in existing_keys:
        ENTRIES[k] = q(text, coh, dom)
        existing_keys.add(k.lower())

print(f"Starting from {len(ENTRIES)} entries")

# ---- Expand multiplication: 1-25 x 1-25 ----
for i in range(1, 26):
    for j in range(1, 26):
        add(f"what is {i} * {j}", f"{i} * {j} = {i*j}", 0.99, "arithmetic")
        add(f"{i} x {j}", f"{i} * {j} = {i*j}", 0.99, "arithmetic")
        add(f"{i} times {j}", f"{i} * {j} = {i*j}", 0.99, "arithmetic")
        add(f"multiply {i} by {j}", f"{i} * {j} = {i*j}", 0.99, "arithmetic")

# ---- Expand powers ----
for base in [3,4,5,6,7,8,9,10]:
    for e in range(0, 8):
        v = base**e
        add(f"{base}^{e}", f"{base}^{e} = {v}", 0.99, "arithmetic")
        add(f"what is {base} to the power of {e}", f"{base}^{e} = {v}", 0.99, "arithmetic")
        add(f"{base} to the {e}th power", f"{base}^{e} = {v}", 0.99, "arithmetic")

# ---- Expand divisions ----
for a in range(2, 100):
    for b in [2,3,4,5,6,8,10]:
        if a % b == 0:
            add(f"what is {a} divided by {b}", f"{a} / {b} = {a//b}", 0.99, "arithmetic")
            add(f"{a}/{b}", f"{a} / {b} = {a//b}", 0.99, "arithmetic")

# ---- Expand squares 1-100 ----
for n in range(1, 101):
    add(f"{n}^2", f"{n}^2 = {n*n}", 0.99, "arithmetic")
    add(f"square root of {n*n}", f"sqrt({n*n}) = {n}", 0.99, "arithmetic")
    add(f"sqrt({n*n})", f"sqrt({n*n}) = {n}", 0.99, "arithmetic")

# ---- Expand cubes 1-30 ----
for n in range(1, 31):
    add(f"{n}^3", f"{n}^3 = {n**3}", 0.99, "arithmetic")
    if n**3 <= 1000:
        add(f"cube root of {n**3}", f"cube root of {n**3} = {n}", 0.99, "arithmetic")

# ---- Expand prime checks 1-300 ----
primes_300 = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179,181,191,193,197,199,211,223,227,229,233,239,241,251,257,263,269,271,277,281,283,293]
for n in range(1, 301):
    if n in primes_300:
        add(f"is {n} prime", f"Yes, {n} is prime.", 0.99, "number_theory")
        add(f"is the number {n} prime", f"Yes, {n} is prime.", 0.99, "number_theory")
    else:
        add(f"is {n} prime", f"No, {n} is not prime.", 0.99, "number_theory")

# ---- Expand percentages ----
for p in range(1, 101):
    for base in [50, 100, 200, 500, 1000]:
        v = int(p * base / 100)
        add(f"what is {p}% of {base}", f"{p}% of {base} = {v}", 0.99, "arithmetic")
        add(f"calculate {p} percent of {base}", f"{p}% of {base} = {v}", 0.99, "arithmetic")
        add(f"{p}% of {base}", f"{p}% of {base} = {v}", 0.99, "arithmetic")

# ---- Expand fractions ----
for num in range(1, 10):
    for den in range(2, 13):
        if num < den:
            dec = num/den
            add(f"what is {num}/{den} as a decimal", f"{num}/{den} = {dec:.4f}", 0.98, "arithmetic")
            add(f"{num}/{den} in decimal", f"{num}/{den} = {dec:.4f}", 0.98, "arithmetic")

# ---- Expand algebra: more linear equations ----
for x in range(-20, 21):
    add(f"solve 5x = {5*x}", f"x = {x}", 0.98, "algebra")
    add(f"solve 7x = {7*x}", f"x = {x}", 0.98, "algebra")
    add(f"solve 4x + 3 = {4*x+3}", f"4x = {4*x}, x = {x}", 0.97, "algebra")
    add(f"solve 3x - 5 = {3*x-5}", f"3x = {3*x}, x = {x}", 0.97, "algebra")

# ---- Expand quadratic equations ----
for a in range(1, 8):
    for b_neg in [-1, 0, 1, 2, 3, 4, 5]:
        # x^2 - (a+b)x + ab = 0 => x = a, b
        if a != b_neg and b_neg >= -5:
            p = a + b_neg
            q = a * b_neg
            sign = "+" if p < 0 else "-"
            sign2 = "+" if q < 0 else "-"
            add(f"solve x^2 {sign} {abs(p)}x {sign2} {abs(q)} = 0", f"x = {a} or x = {b_neg}", 0.96, "algebra")

# ---- Expand logarithms ----
for b in [2,3,4,5,10]:
    for e in range(1, 8):
        n = b**e
        add(f"what is log base {b} of {n}", f"log_{b}({n}) = {e}", 0.98, "algebra")
        add(f"log_{b}({n})", f"log_{b}({n}) = {e}", 0.98, "algebra")
        add(f"evaluate log_{b} {n}", f"log_{b}({n}) = {e}", 0.98, "algebra")

# ---- Expand trigonometry: radians ----
for deg, sv, cv, tv, rad in [
    (0, 0, 1, 0, "0"), (30, 0.5, 0.866, 0.577, "pi/6"),
    (45, 0.707, 0.707, 1.0, "pi/4"), (60, 0.866, 0.5, 1.732, "pi/3"),
    (90, 1, 0, "undefined", "pi/2"), (120, 0.866, -0.5, -1.732, "2pi/3"),
    (180, 0, -1, 0, "pi"), (270, -1, 0, "undefined", "3pi/2"),
    (360, 0, 1, 0, "2pi"),
]:
    add(f"what is {rad} in degrees", f"{rad} radians = {deg} degrees", 0.98, "trigonometry")
    add(f"convert {deg} degrees to radians", f"{deg} degrees = {rad} radians", 0.98, "trigonometry")

# ---- Expand geometry: more specific calculations ----
for r in range(1, 16):
    area = round(math.pi * r**2, 2)
    circ = round(2 * math.pi * r, 2)
    add(f"area of circle with radius {r}", f"A = pi*{r}^2 = {area}", 0.98, "geometry")
    add(f"circumference of circle with radius {r}", f"C = 2*pi*{r} = {circ}", 0.98, "geometry")
    add(f"what is the area of a circle of radius {r}", f"A = pi*{r}^2 = {area}", 0.98, "geometry")

for s in range(1, 21):
    add(f"area of square with side {s}", f"A = {s}^2 = {s*s}", 0.99, "geometry")
    add(f"perimeter of square with side {s}", f"P = 4*{s} = {4*s}", 0.99, "geometry")

for l in range(2, 11):
    for w in range(1, l):
        add(f"area of rectangle {l} by {w}", f"A = {l}*{w} = {l*w}", 0.99, "geometry")
        add(f"perimeter of rectangle {l} by {w}", f"P = 2*({l}+{w}) = {2*(l+w)}", 0.99, "geometry")

for b in range(2, 11):
    for h in range(1, 11):
        area = round(0.5 * b * h, 1)
        add(f"area of triangle with base {b} and height {h}", f"A = (1/2)*{b}*{h} = {area}", 0.98, "geometry")

# ---- Expand statistics: more datasets ----
datasets = [
    ([1,2,3,4,5], 3.0, 3, 2, 4),
    ([10,20,30,40,50], 30.0, 30, 10, 40),
    ([2,4,6,8,10], 6.0, 6, 4, 8),
    ([5,10,15,20], 12.5, 12.5, 10, 15),
    ([3,7,1,9,5], 5.0, 5, 4, 8),
    ([100,200,300], 200.0, 200, 1, 200),
]
for data, mean, med, rng_min, rng_max in datasets:
    ds = ",".join(str(d) for d in data)
    add(f"what is the mean of {ds}", f"Mean = {mean}", 0.98, "statistics")
    add(f"mean of {ds}", f"Mean = {mean}", 0.98, "statistics")
    if len(data) % 2 == 1:
        add(f"what is the median of {ds}", f"Median = {med}", 0.98, "statistics")
    add(f"what is the range of {ds}", f"Range = {rng_max} - {rng_min} = {rng_max-rng_min}", 0.98, "statistics")

# ---- Expand word problems ----
word_more = [
    ("if a pizza is cut into 8 slices and you eat 3, what fraction is left", "5/8 of the pizza remains.", "arithmetic"),
    ("a book costs $15. if you have a 30% coupon, what is the final price", "Discount = $4.50, Final price = $10.50", "arithmetic"),
    ("a store has a 25% off sale. if the sale price is $60, what was the original price", "Original = $60 / 0.75 = $80", "algebra"),
    ("a car uses 1 gallon of gas every 30 miles. how many gallons for 180 miles", "180/30 = 6 gallons", "algebra"),
    ("if 5 workers can finish a job in 12 days, how many days for 3 workers", "Inverse proportion: 5*12 = 3*x, x = 20 days", "algebra"),
    ("what is the slope of the line passing through (2,5) and (4,11)", "m = (11-5)/(4-2) = 6/2 = 3", "geometry"),
    ("write the equation of a line with slope 3 passing through (1,4)", "y-4 = 3(x-1), y = 3x + 1", "geometry"),
    ("find the midpoint of the segment from (2,6) to (8,4)", "Midpoint = ((2+8)/2, (6+4)/2) = (5, 5)", "geometry"),
    ("find the distance between (3,0) and (7,4)", "d = sqrt((7-3)^2 + (4-0)^2) = sqrt(16+16) = sqrt(32) = 4*sqrt(2)", "geometry"),
]
for qs, a, d in word_more:
    add(qs, a, 0.95, d)

# ---- Expand compound problems ----
compound_more = [
    ("what is the derivative of x sin(x)", "Product rule: 1*sin(x) + x*cos(x) = sin(x) + x cos(x)", "calculus"),
    ("what is the derivative of e^x sin(x)", "e^x sin(x) + e^x cos(x) = e^x(sin(x) + cos(x))", "calculus"),
    ("what is the derivative of x^3 cos(x)", "3x^2 cos(x) - x^3 sin(x)", "calculus"),
    ("what is the integral of x cos(x) dx", "x sin(x) + cos(x) + C (integration by parts)", "calculus"),
    ("what is the integral of e^x cos(x) dx", "(e^x/2)(sin(x) + cos(x)) + C", "calculus"),
    ("find the minimum of y = x^2 - 4x + 7", "Vertex at x=2, y=3. Minimum is 3.", "calculus"),
    ("find the maximum of y = -x^2 + 6x - 5", "Vertex at x=3, y=4. Maximum is 4.", "calculus"),
    ("what is the area between y=x and y=x^2 from x=0 to x=1", "Area = integral of (x - x^2) from 0 to 1 = [x^2/2 - x^3/3]_0^1 = 1/2 - 1/3 = 1/6", "calculus"),
]
for qs, a, d in compound_more:
    add(qs, a, 0.93, d)

# ---- Expand number theory ----
for n in [12,18,24,30,36,42,48,54,60,72,84,90,96,100,108,120,144,180,240,360]:
    factors = [i for i in range(1, n+1) if n%i==0]
    add(f"what are the factors of {n}", f"Factors of {n}: {factors}", 0.97, "number_theory")
    add(f"list all factors of {n}", f"Factors of {n}: {factors}", 0.97, "number_theory")

# ---- Expand reasoning ----
reasoning_more = [
    ("if all A are B and some B are C, does it follow that some A are C", "No. Counterexample: A={1}, B={1,2}, C={2}. All A are B, some B are C, but no A are C.", "reasoning"),
    ("if no dogs are cats and some pets are dogs, are some pets cats", "Cannot conclude. Some pets are dogs (and thus not cats), but other pets could be cats or not.", "reasoning"),
    ("is the argument 'if it's Tuesday, I have a meeting. I have a meeting today, so it must be Tuesday' valid", "No. This is affirming the consequent: P->Q, Q, therefore P. (The meeting could be on another day.)", "reasoning"),
    ("prove that the sum of two even numbers is even", "Let a=2m, b=2n. a+b = 2m+2n = 2(m+n). Since m+n is an integer, 2(m+n) is even.", "reasoning"),
    ("prove that the product of two odd numbers is odd", "Let a=2m+1, b=2n+1. ab = (2m+1)(2n+1) = 4mn+2m+2n+1 = 2(2mn+m+n)+1, which is odd.", "reasoning"),
]
for qs, a, d in reasoning_more:
    add(qs, a, 0.95, d)

# ---- Write output ----
print(f"Entries: {len(ENTRIES)}")

out = os.path.join(os.path.dirname(__file__), "knowledge_base.py")
backup = os.path.join(os.path.dirname(__file__), "knowledge_base_1920.py")
if os.path.exists(out) and not os.path.exists(backup):
    shutil.copy(out, backup)
    print(f"Backup: {backup}")

with open(out, "w", encoding="utf-8") as f:
    f.write('#!/usr/bin/env python3\n')
    f.write(f'"""Knowledge Base — {len(ENTRIES)}+ Math/Reasoning Q&A pairs"""\n')
    f.write('import math\nPHI=1.618033988749895;PI=math.pi;E=math.e\n\n')
    f.write('PRE_COMPUTED = {\n')
    for k,v in sorted(ENTRIES.items()):
        t = v["text"].replace("\\","\\\\").replace('"','\\"').replace("\n","\\n")
        f.write(f'    "{k}": {{"text": "{t}", "coherence": {v["coherence"]}, "domain": "{v["domain"]}"}},\n')
    f.write('}\n\nPRE_COMPUTED_NORMALIZED = {k.lower().strip(): v for k, v in PRE_COMPUTED.items()}\n')

print(f"Written: {out}")

# Count by domain
domains = {}
for v in ENTRIES.values():
    d = v["domain"]
    domains[d] = domains.get(d, 0) + 1
print("Domains:")
for d,c in sorted(domains.items(), key=lambda x:-x[1]):
    print(f"  {d}: {c}")
print("Done.")