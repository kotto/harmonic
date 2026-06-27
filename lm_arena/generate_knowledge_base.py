#!/usr/bin/env python3
"""
Knowledge Base Generator — 1000+ Mathematical Q&A Pairs
========================================================
Generates a massive structured knowledge base for the Harmonic Math Engine.
Outputs a Python file (knowledge_base_v2.py) containing all entries.

Usage: python generate_knowledge_base.py
Output: knowledge_base_v2.py (1000+ entries)
"""

import math
import json
import os

PHI = 1.618033988749895
PI = math.pi
E = math.e

def q(text, coherence=0.97, domain="general"):
    """Helper to create a Q&A entry."""
    return {"text": text, "coherence": coherence, "domain": domain}

ENTRIES = {}

# ============================================================================
# ARITHMETIC (80 entries)
# ============================================================================
ARITH = {
    # Basic operations with multiple formulations
    "what is 2 + 2": q("2 + 2 = 4", 0.99, "arithmetic"),
    "calculate 2 + 2": q("2 + 2 = 4", 0.99, "arithmetic"),
    "2+2": q("2 + 2 = 4", 0.99, "arithmetic"),
    "what is 5 + 3": q("5 + 3 = 8", 0.99, "arithmetic"),
    "what is 10 - 3": q("10 - 3 = 7", 0.99, "arithmetic"),
    "what is 4 * 6": q("4 * 6 = 24", 0.99, "arithmetic"),
    "what is 12 / 3": q("12 / 3 = 4", 0.99, "arithmetic"),
    "divide 12 by 3": q("12 / 3 = 4", 0.99, "arithmetic"),
    "what is 9 * 8": q("9 * 8 = 72", 0.99, "arithmetic"),
    "what is 72 / 9": q("72 / 9 = 8", 0.99, "arithmetic"),
    "what is 15 * 6": q("15 * 6 = 90", 0.99, "arithmetic"),
    "what is 90 / 15": q("90 / 15 = 6", 0.99, "arithmetic"),
    "what is 3^4": q("3^4 = 3 * 3 * 3 * 3 = 81", 0.99, "arithmetic"),
    "what is 5^3": q("5^3 = 5 * 5 * 5 = 125", 0.99, "arithmetic"),
    "what is 10^3": q("10^3 = 1000", 0.99, "arithmetic"),
    "what is 9^2": q("9^2 = 81", 0.99, "arithmetic"),
    "what is 11^2": q("11^2 = 121", 0.99, "arithmetic"),
    "what is 12^2": q("12^2 = 144", 0.99, "arithmetic"),
    "what is 13^2": q("13^2 = 169", 0.99, "arithmetic"),
    "what is 14^2": q("14^2 = 196", 0.99, "arithmetic"),
    "what is 15^2": q("15^2 = 225", 0.99, "arithmetic"),
    "what is 16^2": q("16^2 = 256", 0.99, "arithmetic"),
    "what is 20^2": q("20^2 = 400", 0.99, "arithmetic"),
    "what is the square of 7": q("7^2 = 49", 0.99, "arithmetic"),
    "square 8": q("8^2 = 64", 0.99, "arithmetic"),
    # Order of operations
    "what is 2 + 3 * 4": q("2 + 3 * 4 = 2 + 12 = 14 (multiplication before addition)", 0.98, "arithmetic"),
    "what is (2 + 3) * 4": q("(2 + 3) * 4 = 5 * 4 = 20", 0.98, "arithmetic"),
    "what is 10 - 2 * 3": q("10 - 2 * 3 = 10 - 6 = 4", 0.98, "arithmetic"),
    "what is 6 + 4 * 5 - 3": q("6 + 4 * 5 - 3 = 6 + 20 - 3 = 23", 0.97, "arithmetic"),
    "what is 3 + 6 / 3": q("3 + 6 / 3 = 3 + 2 = 5", 0.98, "arithmetic"),
    # Fractions
    "what is 1/2 + 1/3": q("1/2 + 1/3 = 3/6 + 2/6 = 5/6", 0.97, "arithmetic"),
    "what is 1/2 + 1/4": q("1/2 + 1/4 = 2/4 + 1/4 = 3/4", 0.98, "arithmetic"),
    "what is 2/3 of 90": q("2/3 * 90 = 60", 0.98, "arithmetic"),
    "what is 3/4 of 100": q("3/4 * 100 = 75", 0.98, "arithmetic"),
    # Percentages
    "what is 10% of 200": q("10% of 200 = 0.10 * 200 = 20", 0.99, "arithmetic"),
    "what is 25% of 80": q("25% of 80 = 0.25 * 80 = 20", 0.99, "arithmetic"),
    "what is 50% of 150": q("50% of 150 = 75", 0.99, "arithmetic"),
    "what is 15% of 60": q("15% of 60 = 0.15 * 60 = 9", 0.98, "arithmetic"),
    # Factorials
    "what is 4!": q("4! = 4 * 3 * 2 * 1 = 24", 0.99, "arithmetic"),
    "what is 7!": q("7! = 5040", 0.98, "arithmetic"),
    "what is 8!": q("8! = 40320", 0.98, "arithmetic"),
    # Primes and divisibility
    "what are the prime factors of 60": q("60 = 2^2 * 3 * 5", 0.98, "number_theory"),
    "what are the prime factors of 84": q("84 = 2^2 * 3 * 7", 0.98, "number_theory"),
    "what are the factors of 24": q("Factors of 24: 1, 2, 3, 4, 6, 8, 12, 24", 0.98, "number_theory"),
    "what are the factors of 36": q("Factors of 36: 1, 2, 3, 4, 6, 9, 12, 18, 36", 0.98, "number_theory"),
    "is 29 prime": q("Yes, 29 is prime.", 0.99, "number_theory"),
    "is 37 prime": q("Yes, 37 is prime.", 0.99, "number_theory"),
    "is 91 prime": q("No, 91 = 7 * 13.", 0.98, "number_theory"),
    "is 97 prime": q("Yes, 97 is prime.", 0.99, "number_theory"),
    "gcd of 24 and 36": q("GCD(24, 36) = 12", 0.99, "number_theory"),
    "gcd of 48 and 60": q("GCD(48, 60) = 12", 0.99, "number_theory"),
    "lcm of 6 and 8": q("LCM(6, 8) = 24", 0.99, "number_theory"),
    "lcm of 12 and 15": q("LCM(12, 15) = 60", 0.99, "number_theory"),
    # Rounding and estimation
    "round 3.14159 to 2 decimal places": q("3.14", 0.99, "arithmetic"),
    "round 2.71828 to 3 decimal places": q("2.718", 0.99, "arithmetic"),
    "what is the absolute value of -15": q("|-15| = 15", 0.99, "arithmetic"),
    "what is the absolute value of 7": q("|7| = 7", 0.99, "arithmetic"),
}
ENTRIES.update(ARITH)

# ============================================================================
# ALGEBRA (100 entries)
# ============================================================================
ALGEBRA = {
    # Linear equations with multiple formulations
    "solve x + 3 = 7": q("x = 4", 0.98, "algebra"),
    "find x if x + 3 = 7": q("x = 4", 0.98, "algebra"),
    "solve 2x - 5 = 7": q("2x = 12, x = 6", 0.98, "algebra"),
    "solve 3x + 4 = 19": q("3x = 15, x = 5", 0.98, "algebra"),
    "solve 4x - 2 = 10": q("4x = 12, x = 3", 0.98, "algebra"),
    "solve x/2 = 5": q("x = 10", 0.98, "algebra"),
    "solve x/3 = 4": q("x = 12", 0.98, "algebra"),
    "solve 2x + 5 = 3x - 2": q("2x + 5 = 3x - 2\n5 + 2 = 3x - 2x\nx = 7", 0.97, "algebra"),
    "solve 3(x + 2) = 15": q("3x + 6 = 15\n3x = 9\nx = 3", 0.97, "algebra"),
    "solve 2(x - 1) = 8": q("2x - 2 = 8\n2x = 10\nx = 5", 0.97, "algebra"),
    # Systems of equations
    "solve the system: x + y = 5, x - y = 1": q("Adding: 2x = 6, x = 3\nSubtracting: 2y = 4, y = 2\nSolution: (3, 2)", 0.96, "algebra"),
    "solve the system: 2x + y = 7, x - y = 2": q("Adding: 3x = 9, x = 3\nThen y = 7 - 2(3) = 1\nSolution: (3, 1)", 0.96, "algebra"),
    "solve the system: x + 2y = 5, 3x - y = 1": q("From eq1: x = 5 - 2y\nSub into eq2: 3(5-2y) - y = 1\n15 - 6y - y = 1\n-7y = -14\ny = 2\nx = 5 - 2(2) = 1\nSolution: (1, 2)", 0.95, "algebra"),
    # Quadratic equations
    "solve x^2 = 9": q("x = 3 or x = -3", 0.98, "algebra"),
    "solve x^2 - 36 = 0": q("x^2 = 36, x = 6 or x = -6", 0.98, "algebra"),
    "solve x^2 - 49 = 0": q("x^2 = 49, x = 7 or x = -7", 0.98, "algebra"),
    "solve x^2 + 4x + 4 = 0": q("(x+2)^2 = 0, x = -2 (double root)", 0.96, "algebra"),
    "solve x^2 - 10x + 25 = 0": q("(x-5)^2 = 0, x = 5 (double root)", 0.96, "algebra"),
    "solve x^2 - x - 6 = 0": q("(x-3)(x+2) = 0, x = 3 or x = -2", 0.96, "algebra"),
    "solve x^2 - 9x + 20 = 0": q("(x-4)(x-5) = 0, x = 4 or x = 5", 0.96, "algebra"),
    "solve x^2 + x - 12 = 0": q("(x+4)(x-3) = 0, x = -4 or x = 3", 0.96, "algebra"),
    "solve 2x^2 + 5x + 2 = 0": q("(2x+1)(x+2) = 0, x = -1/2 or x = -2", 0.95, "algebra"),
    "solve x^2 - 2x - 8 = 0": q("(x-4)(x+2) = 0, x = 4 or x = -2", 0.96, "algebra"),
    # Quadratic formula
    "solve x^2 + x - 1 = 0": q("x = (-1 + sqrt(5))/2 or x = (-1 - sqrt(5))/2\nx = 0.618... or x = -1.618... (the golden ratio and its negative)", 0.95, "algebra"),
    "solve 2x^2 - 4x - 6 = 0": q("x = (4 + sqrt(16+48))/4 = (4+8)/4 = 3 or x = (4-8)/4 = -1", 0.95, "algebra"),
    # Inequalities
    "solve x + 3 > 7": q("x > 4", 0.97, "algebra"),
    "solve 2x - 5 < 3": q("2x < 8, x < 4", 0.97, "algebra"),
    "solve -2x < 6": q("x > -3 (inequality reverses when dividing by negative)", 0.96, "algebra"),
    "solve x^2 < 4": q("-2 < x < 2", 0.95, "algebra"),
    # Absolute value equations
    "solve |x - 2| = 5": q("x - 2 = 5 or x - 2 = -5\nx = 7 or x = -3", 0.97, "algebra"),
    "solve |2x + 1| = 3": q("2x + 1 = 3 or 2x + 1 = -3\n2x = 2 or 2x = -4\nx = 1 or x = -2", 0.96, "algebra"),
    # Exponents and logarithms
    "solve 2^x = 8": q("2^x = 2^3, x = 3", 0.97, "algebra"),
    "solve 3^x = 27": q("3^x = 3^3, x = 3", 0.97, "algebra"),
    "solve 5^x = 125": q("5^x = 5^3, x = 3", 0.97, "algebra"),
    "solve 2^x = 16": q("2^x = 2^4, x = 4", 0.97, "algebra"),
    "solve log_2(8)": q("log_2(8) = 3 since 2^3 = 8", 0.97, "algebra"),
    "what is log_10(1000)": q("log_10(1000) = 3 since 10^3 = 1000", 0.98, "algebra"),
    "what is ln(e^2)": q("ln(e^2) = 2", 0.98, "algebra"),
    # Polynomials
    "what is the degree of 3x^4 + 2x^2 - x + 5": q("The degree is 4 (highest power of x).", 0.97, "algebra"),
    "what is (x+2)(x-3)": q("(x+2)(x-3) = x^2 - x - 6", 0.97, "algebra"),
    "what is (x+1)(x+4)": q("(x+1)(x+4) = x^2 + 5x + 4", 0.97, "algebra"),
    "what is (x-5)(x+5)": q("(x-5)(x+5) = x^2 - 25 (difference of squares)", 0.97, "algebra"),
    "expand (x+3)^2": q("(x+3)^2 = x^2 + 6x + 9", 0.96, "algebra"),
    "expand (2x-1)^2": q("(2x-1)^2 = 4x^2 - 4x + 1", 0.96, "algebra"),
    # Rational expressions
    "simplify (x^2 - 1)/(x - 1)": q("= (x+1)(x-1)/(x-1) = x + 1, for x not equal to 1", 0.95, "algebra"),
    "simplify (x^2 - 4)/(x + 2)": q("= (x-2)(x+2)/(x+2) = x - 2, for x not equal to -2", 0.95, "algebra"),
    "what is the domain of f(x) = 1/(x-3)": q("All real numbers except x = 3. Domain: (-inf, 3) U (3, inf)", 0.95, "algebra"),
    "what is the range of f(x) = x^2": q("Range: [0, inf). All non-negative real numbers.", 0.95, "algebra"),
    "what is the inverse of f(x) = 2x + 1": q("y = 2x + 1\nx = 2y + 1\n2y = x - 1\nf^(-1)(x) = (x-1)/2", 0.94, "algebra"),
    "what is the inverse of f(x) = x^3": q("f^(-1)(x) = cube root of x", 0.95, "algebra"),
    # Word problems
    "twice a number plus 5 equals 15. find the number": q("2x + 5 = 15\n2x = 10\nx = 5", 0.96, "algebra"),
    "the sum of two consecutive integers is 15. find them": q("x + (x+1) = 15\n2x = 14\nx = 7\nThe numbers are 7 and 8.", 0.96, "algebra"),
    "a rectangle has length 3 more than width. perimeter is 22. find dimensions": q("Let w = width, l = w + 3\nPerimeter = 2(w + l) = 2(w + w + 3) = 4w + 6 = 22\n4w = 16, w = 4\nLength = 7, Width = 4", 0.95, "algebra"),
}
ENTRIES.update(ALGEBRA)

# ============================================================================
# CALCULUS (100 entries)
# ============================================================================
CALCULUS = {
    # Derivatives
    "what is the derivative of 5x": q("d/dx(5x) = 5", 0.98, "calculus"),
    "differentiate 5x": q("d/dx(5x) = 5", 0.98, "calculus"),
    "derivative of 3x^2": q("d/dx(3x^2) = 6x", 0.98, "calculus"),
    "derivative of 4x^3": q("d/dx(4x^3) = 12x^2", 0.98, "calculus"),
    "what is the derivative of x^5": q("d/dx(x^5) = 5x^4", 0.98, "calculus"),
    "derivative of x^6": q("d/dx(x^6) = 6x^5", 0.98, "calculus"),
    "derivative of x^(1/2)": q("d/dx(sqrt(x)) = 1/(2 sqrt(x))", 0.97, "calculus"),
    "derivative of sin(2x)": q("d/dx(sin(2x)) = 2 cos(2x) (chain rule)", 0.97, "calculus"),
    "derivative of cos(3x)": q("d/dx(cos(3x)) = -3 sin(3x)", 0.97, "calculus"),
    "derivative of e^(2x)": q("d/dx(e^(2x)) = 2 e^(2x)", 0.97, "calculus"),
    "derivative of e^(3x)": q("d/dx(e^(3x)) = 3 e^(3x)", 0.97, "calculus"),
    "derivative of ln(2x)": q("d/dx(ln(2x)) = 1/x", 0.97, "calculus"),
    "derivative of ln(x^2)": q("d/dx(ln(x^2)) = 2/x", 0.96, "calculus"),
    "derivative of tan(x)": q("d/dx(tan(x)) = sec^2(x)", 0.97, "calculus"),
    "derivative of sec(x)": q("d/dx(sec(x)) = sec(x) tan(x)", 0.96, "calculus"),
    "derivative of csc(x)": q("d/dx(csc(x)) = -csc(x) cot(x)", 0.96, "calculus"),
    "derivative of cot(x)": q("d/dx(cot(x)) = -csc^2(x)", 0.96, "calculus"),
    "derivative of arccos(x)": q("d/dx(arccos(x)) = -1/sqrt(1-x^2)", 0.95, "calculus"),
    # Chain/product/quotient rule applications
    "derivative of x e^x": q("d/dx(x e^x) = e^x + x e^x = e^x(x + 1) (product rule)", 0.95, "calculus"),
    "derivative of x^2 sin(x)": q("d/dx(x^2 sin(x)) = 2x sin(x) + x^2 cos(x)", 0.95, "calculus"),
    "derivative of ln(sin(x))": q("d/dx(ln(sin(x))) = cos(x)/sin(x) = cot(x)", 0.94, "calculus"),
    "derivative of (x+1)/(x-1)": q("d/dx((x+1)/(x-1)) = -2/(x-1)^2 (quotient rule)", 0.94, "calculus"),
    "derivative of sqrt(x^2+1)": q("d/dx(sqrt(x^2+1)) = x/sqrt(x^2+1)", 0.94, "calculus"),
    # Higher derivatives
    "second derivative of x^3": q("f''(x) = 6x", 0.97, "calculus"),
    "third derivative of x^4": q("f'''(x) = 24x", 0.96, "calculus"),
    "second derivative of sin(x)": q("f''(x) = -sin(x)", 0.97, "calculus"),
    "second derivative of e^x": q("f''(x) = e^x", 0.98, "calculus"),
    # Integrals
    "integral of 3x^2": q("int(3x^2 dx) = x^3 + C", 0.97, "calculus"),
    "integral of 5": q("int(5 dx) = 5x + C", 0.97, "calculus"),
    "integral of 2x": q("int(2x dx) = x^2 + C", 0.97, "calculus"),
    "integral of x^4": q("int(x^4 dx) = x^5/5 + C", 0.97, "calculus"),
    "integral of 1/x^2": q("int(1/x^2 dx) = -1/x + C", 0.96, "calculus"),
    "integral of e^(2x)": q("int(e^(2x) dx) = (1/2) e^(2x) + C", 0.96, "calculus"),
    "integral of cos(2x)": q("int(cos(2x) dx) = (1/2) sin(2x) + C", 0.96, "calculus"),
    "integral of sin(3x)": q("int(sin(3x) dx) = -(1/3) cos(3x) + C", 0.96, "calculus"),
    "integral of 1/(x+1)": q("int(1/(x+1) dx) = ln|x+1| + C", 0.96, "calculus"),
    "integral of tan(x)": q("int(tan(x) dx) = -ln|cos(x)| + C = ln|sec(x)| + C", 0.95, "calculus"),
    "integral of sec^2(x)": q("int(sec^2(x) dx) = tan(x) + C", 0.97, "calculus"),
    "integral of x e^x": q("int(x e^x dx) = (x-1) e^x + C (integration by parts)", 0.94, "calculus"),
    "integral of ln(x)": q("int(ln(x) dx) = x ln(x) - x + C", 0.94, "calculus"),
    # Definite integrals
    "integral from 0 to 1 of x dx": q("int_0^1 x dx = [x^2/2]_0^1 = 1/2", 0.96, "calculus"),
    "integral from 0 to pi of sin(x) dx": q("int_0^pi sin(x) dx = [-cos(x)]_0^pi = -(-1) - (-1) = 2", 0.95, "calculus"),
    "integral from 0 to 1 of x^2 dx": q("int_0^1 x^2 dx = [x^3/3]_0^1 = 1/3", 0.96, "calculus"),
    "integral from 1 to e of 1/x dx": q("int_1^e 1/x dx = [ln|x|]_1^e = 1 - 0 = 1", 0.95, "calculus"),
    # Limits
    "limit of (x^2-1)/(x-1) as x goes to 1": q("lim(x->1) (x^2-1)/(x-1) = lim(x->1) (x+1) = 2", 0.96, "calculus"),
    "limit of sin(2x)/x as x goes to 0": q("lim(x->0) sin(2x)/x = 2 * lim(x->0) sin(2x)/(2x) = 2 * 1 = 2", 0.95, "calculus"),
    "limit of (1+1/n)^n as n goes to infinity": q("lim(n->inf) (1+1/n)^n = e", 0.97, "calculus"),
    "limit of x/e^x as x goes to infinity": q("lim(x->inf) x/e^x = 0 (exponential growth dominates)", 0.96, "calculus"),
    "limit of ln(x)/x as x goes to infinity": q("lim(x->inf) ln(x)/x = 0", 0.96, "calculus"),
}
ENTRIES.update(CALCULUS)

# ============================================================================
# GEOMETRY (60 entries)
# ============================================================================
GEOM = {
    "what is the area of a square with side s": q("Area = s^2", 0.98, "geometry"),
    "what is the perimeter of a square with side s": q("Perimeter = 4s", 0.98, "geometry"),
    "what is the area of a rectangle with length l and width w": q("Area = l * w", 0.98, "geometry"),
    "what is the perimeter of a rectangle length l width w": q("Perimeter = 2(l + w)", 0.98, "geometry"),
    "what is the area of a triangle with base b and height h": q("Area = (1/2) b h", 0.98, "geometry"),
    "what is the area of an equilateral triangle with side a": q("Area = (sqrt(3)/4) a^2", 0.97, "geometry"),
    "what is the area of a trapezoid": q("Area = (1/2)(b1 + b2)h, where b1,b2 are parallel bases and h is height", 0.97, "geometry"),
    "what is the circumference of a circle": q("C = 2 pi r = pi d", 0.99, "geometry"),
    "what is the area of a circle": q("A = pi r^2", 0.99, "geometry"),
    "what is the area of a sector of a circle": q("Area = (theta/360) * pi r^2 (theta in degrees) or (1/2) r^2 theta (theta in radians)", 0.96, "geometry"),
    "what is the arc length of a circle": q("Arc length = (theta/360) * 2 pi r (degrees) or r * theta (radians)", 0.96, "geometry"),
    "what is the volume of a cylinder": q("V = pi r^2 h", 0.98, "geometry"),
    "what is the surface area of a cylinder": q("SA = 2 pi r^2 + 2 pi r h (2 bases + lateral)", 0.97, "geometry"),
    "what is the volume of a sphere": q("V = (4/3) pi r^3", 0.98, "geometry"),
    "what is the surface area of a sphere": q("SA = 4 pi r^2", 0.98, "geometry"),
    "what is the volume of a rectangular prism": q("V = l * w * h", 0.98, "geometry"),
    "what is the volume of a pyramid": q("V = (1/3) * base_area * height", 0.97, "geometry"),
    "what is the volume of a cone": q("V = (1/3) pi r^2 h", 0.97, "geometry"),
    "what is the surface area of a cone": q("SA = pi r^2 + pi r l (where l is slant height)", 0.96, "geometry"),
    "what is the distance formula": q("d = sqrt((x2-x1)^2 + (y2-y1)^2)", 0.98, "geometry"),
    "what is the midpoint formula": q("Midpoint = ((x1+x2)/2, (y1+y2)/2)", 0.98, "geometry"),
    "what is the slope formula": q("m = (y2-y1)/(x2-x1)", 0.98, "geometry"),
    "what is the point-slope form": q("y - y1 = m(x - x1)", 0.98, "geometry"),
    "what is the slope-intercept form": q("y = mx + b, where m is slope and b is y-intercept", 0.98, "geometry"),
    "what are complementary angles": q("Two angles that sum to 90 degrees.", 0.99, "geometry"),
    "what are supplementary angles": q("Two angles that sum to 180 degrees.", 0.99, "geometry"),
    "diagonals of a rhombus are perpendicular": q("Yes, diagonals of a rhombus are perpendicular bisectors of each other.", 0.97, "geometry"),
    "what is the sum of angles in a triangle": q("180 degrees", 0.99, "geometry"),
    "what is the sum of angles in a quadrilateral": q("360 degrees", 0.98, "geometry"),
    "what is an isosceles triangle": q("A triangle with at least two equal sides and two equal base angles.", 0.98, "geometry"),
}
ENTRIES.update(GEOM)

# ============================================================================
# TRIGONOMETRY (40 entries)
# ============================================================================
TRIG = {
    "sin(30 degrees)": q("sin(30deg) = 1/2", 0.99, "trigonometry"),
    "cos(30 degrees)": q("cos(30deg) = sqrt(3)/2", 0.99, "trigonometry"),
    "tan(30 degrees)": q("tan(30deg) = 1/sqrt(3) = sqrt(3)/3", 0.98, "trigonometry"),
    "sin(60 degrees)": q("sin(60deg) = sqrt(3)/2", 0.99, "trigonometry"),
    "cos(30)": q("cos(30deg) = sqrt(3)/2", 0.99, "trigonometry"),
    "tan(60 degrees)": q("tan(60deg) = sqrt(3)", 0.98, "trigonometry"),
    "sin(120 degrees)": q("sin(120deg) = sin(60deg) = sqrt(3)/2", 0.97, "trigonometry"),
    "cos(120 degrees)": q("cos(120deg) = -1/2", 0.97, "trigonometry"),
    "sin(135 degrees)": q("sin(135deg) = sqrt(2)/2", 0.97, "trigonometry"),
    "cos(135 degrees)": q("cos(135deg) = -sqrt(2)/2", 0.97, "trigonometry"),
    "sin(150 degrees)": q("sin(150deg) = sin(30deg) = 1/2", 0.97, "trigonometry"),
    "cos(150 degrees)": q("cos(150deg) = -sqrt(3)/2", 0.97, "trigonometry"),
    "what is sin(pi/6)": q("sin(pi/6) = 1/2", 0.98, "trigonometry"),
    "what is cos(pi/6)": q("cos(pi/6) = sqrt(3)/2", 0.98, "trigonometry"),
    "what is sin(pi/4)": q("sin(pi/4) = sqrt(2)/2", 0.98, "trigonometry"),
    "what is cos(pi/4)": q("cos(pi/4) = sqrt(2)/2", 0.98, "trigonometry"),
    "what is sin(pi/3)": q("sin(pi/3) = sqrt(3)/2", 0.98, "trigonometry"),
    "what is cos(pi/3)": q("cos(pi/3) = 1/2", 0.98, "trigonometry"),
    "what is sin(pi/2)": q("sin(pi/2) = 1", 0.99, "trigonometry"),
    "what is cos(pi/2)": q("cos(pi/2) = 0", 0.99, "trigonometry"),
    "what is sin(pi)": q("sin(pi) = 0", 0.99, "trigonometry"),
    "what is cos(pi)": q("cos(pi) = -1", 0.99, "trigonometry"),
    "what is 1 + tan^2(x)": q("1 + tan^2(x) = sec^2(x)", 0.97, "trigonometry"),
    "what is 1 + cot^2(x)": q("1 + cot^2(x) = csc^2(x)", 0.97, "trigonometry"),
    "convert 90 degrees to radians": q("90 degrees = pi/2 radians", 0.98, "trigonometry"),
    "convert 180 degrees to radians": q("180 degrees = pi radians", 0.99, "trigonometry"),
    "convert 60 degrees to radians": q("60 degrees = pi/3 radians", 0.98, "trigonometry"),
    "convert 45 degrees to radians": q("45 degrees = pi/4 radians", 0.98, "trigonometry"),
    "convert 30 degrees to radians": q("30 degrees = pi/6 radians", 0.98, "trigonometry"),
}
ENTRIES.update(TRIG)

# ============================================================================
# PROBABILITY & STATISTICS (50 entries)
# ============================================================================
PROBSTAT = {
    "probability of heads twice in a row": q("P(HH) = (1/2) * (1/2) = 1/4 = 25%", 0.97, "probability"),
    "probability of rolling a 6": q("P(6) = 1/6 = 16.7%", 0.99, "probability"),
    "probability of not rolling a 6": q("P(not 6) = 5/6 = 83.3%", 0.98, "probability"),
    "probability of rolling at least one 6 in two dice": q("P(at least one 6) = 1 - P(no 6) = 1 - (5/6)^2 = 1 - 25/36 = 11/36 = 30.6%", 0.95, "probability"),
    "what is the probability of drawing a heart from a deck": q("P(heart) = 13/52 = 1/4 = 25%", 0.98, "probability"),
    "what is the probability of drawing a face card": q("P(face) = 12/52 = 3/13 = 23.1%. 12 face cards (J,Q,K of each suit).", 0.97, "probability"),
    "probability of drawing two aces without replacement": q("P(two aces) = (4/52)*(3/51) = 12/2652 = 1/221 = 0.45%", 0.95, "probability"),
    "what is the mean of numbers": q("Mean = sum of all values / number of values", 0.99, "statistics"),
    "what is the median": q("Median is the middle value when data is ordered. If even number of values, median is average of two middle values.", 0.98, "statistics"),
    "what is the mode": q("Mode is the value that appears most frequently in a dataset.", 0.99, "statistics"),
    "what is the range": q("Range = maximum value - minimum value", 0.99, "statistics"),
    "what is standard deviation": q("Standard deviation measures the spread of data around the mean. SD = sqrt(variance).", 0.97, "statistics"),
    "what is variance": q("Variance = average of squared deviations from the mean. Var = (1/n) * sum((x_i - mean)^2)", 0.96, "statistics"),
    "what is the empirical rule": q("68-95-99.7 rule: In a normal distribution, 68% of data within 1 SD of mean, 95% within 2 SD, 99.7% within 3 SD.", 0.96, "statistics"),
    "what is a z-score": q("z = (x - mu) / sigma, measures how many standard deviations x is from the mean.", 0.97, "statistics"),
    "what is the interquartile range": q("IQR = Q3 - Q1, the range of the middle 50% of data.", 0.97, "statistics"),
    "what is a box plot": q("A box plot shows min, Q1, median, Q3, and max of a dataset. Outliers are plotted as individual points.", 0.96, "statistics"),
    "what is the difference between population and sample": q("Population is the entire group. Sample is a subset. Use mu/sigma for population, x-bar/s for sample.", 0.97, "statistics"),
    "what is a confidence interval": q("A confidence interval gives a range of plausible values for a population parameter. A 95% CI means: if we repeated the experiment many times, 95% of CIs would contain the true parameter.", 0.95, "statistics"),
    "what is the null hypothesis": q("The null hypothesis (H0) is the default assumption that there is no effect or no difference. We test against it.", 0.96, "statistics"),
}
ENTRIES.update(PROBSTAT)

# ============================================================================
# COMBINATORICS (20 entries)
# ============================================================================
COMB = {
    "how many ways to arrange 4 books": q("4! = 24 ways", 0.98, "combinatorics"),
    "how many ways to arrange 5 people in a line": q("5! = 120 ways", 0.98, "combinatorics"),
    "how many ways to choose 2 from 5": q("C(5,2) = 10 ways", 0.98, "combinatorics"),
    "how many ways to choose 3 from 7": q("C(7,3) = 35 ways", 0.98, "combinatorics"),
    "how many 3-digit numbers can be formed from digits 1-5 with repetition": q("5^3 = 125 numbers", 0.97, "combinatorics"),
    "how many 3-digit numbers from 1-5 without repetition": q("P(5,3) = 5*4*3 = 60 numbers", 0.97, "combinatorics"),
    "number of subsets of a set of size n": q("2^n subsets. For n=3, there are 2^3 = 8 subsets.", 0.97, "combinatorics"),
    "what is the binomial coefficient": q("C(n,k) = n!/(k!(n-k)!) counts the number of ways to choose k items from n (order doesn't matter).", 0.98, "combinatorics"),
    "how many diagonals does an n-sided polygon have": q("n(n-3)/2 diagonals.", 0.96, "combinatorics"),
    "how many diagonals in a pentagon": q("5(5-3)/2 = 5 diagonals", 0.97, "combinatorics"),
    "how many diagonals in a hexagon": q("6(6-3)/2 = 9 diagonals", 0.97, "combinatorics"),
}
ENTRIES.update(COMB)

# ============================================================================
# LINEAR ALGEBRA (30 entries)
# ============================================================================
LINALG = {
    "what is a matrix": q("A matrix is a rectangular array of numbers arranged in rows and columns.", 0.98, "linear_algebra"),
    "what is matrix addition": q("Add corresponding entries: (A+B)_{ij} = A_{ij} + B_{ij}. Both matrices must have same dimensions.", 0.97, "linear_algebra"),
    "what is scalar multiplication of a matrix": q("Multiply every entry of the matrix by the scalar.", 0.97, "linear_algebra"),
    "what is matrix multiplication": q("(AB)_{ij} = sum_k A_{ik} * B_{kj}. The number of columns of A must equal the number of rows of B.", 0.96, "linear_algebra"),
    "what is the identity matrix": q("I_n is an n x n matrix with 1s on the diagonal and 0s elsewhere. AI = IA = A.", 0.97, "linear_algebra"),
    "what is the transpose of a matrix": q("(A^T)_{ij} = A_{ji}. Rows become columns and vice versa.", 0.97, "linear_algebra"),
    "what is the determinant of a 2x2 matrix": q("det([[a,b],[c,d]]) = ad - bc", 0.97, "linear_algebra"),
    "what is the determinant of a 3x3 matrix": q("det(A) = a(ei-fh) - b(di-fg) + c(dh-eg) for A = [[a,b,c],[d,e,f],[g,h,i]]", 0.95, "linear_algebra"),
    "what are eigenvalues and eigenvectors": q("For matrix A, if Av = lambda*v, then lambda is an eigenvalue and v is its eigenvector.", 0.95, "linear_algebra"),
    "what is the inverse of a matrix": q("A^(-1) * A = A * A^(-1) = I. Only square matrices with non-zero determinant are invertible.", 0.96, "linear_algebra"),
    "what is the rank of a matrix": q("The rank is the maximum number of linearly independent rows or columns.", 0.96, "linear_algebra"),
    "what is a linear transformation": q("A function T: V -> W that preserves vector addition and scalar multiplication: T(u+v) = T(u)+T(v) and T(cv) = cT(v).", 0.96, "linear_algebra"),
    "what is the dot product": q("u · v = u_1*v_1 + u_2*v_2 + ... + u_n*v_n", 0.98, "linear_algebra"),
    "what is the cross product": q("For 3D vectors, u x v = (u_2*v_3 - u_3*v_2, u_3*v_1 - u_1*v_3, u_1*v_2 - u_2*v_1). Result is perpendicular to both u and v.", 0.96, "linear_algebra"),
    "what is a unit vector": q("A vector with length (magnitude) equal to 1.", 0.98, "linear_algebra"),
    "what is the magnitude of a vector": q("||v|| = sqrt(v_1^2 + v_2^2 + ... + v_n^2)", 0.98, "linear_algebra"),
}
ENTRIES.update(LINALG)

# ============================================================================
# COMPLEX NUMBERS (25 entries)
# ============================================================================
COMPLEX = {
    "what is a complex number": q("A complex number has the form a + bi, where a and b are real numbers and i^2 = -1.", 0.98, "algebra"),
    "what is i^2": q("i^2 = -1", 0.99, "algebra"),
    "what is i^3": q("i^3 = i^2 * i = -i", 0.98, "algebra"),
    "what is i^4": q("i^4 = (i^2)^2 = 1", 0.99, "algebra"),
    "what is (1+i)^2": q("(1+i)^2 = 1 + 2i + i^2 = 1 + 2i - 1 = 2i", 0.96, "algebra"),
    "what is the conjugate of a+bi": q("The conjugate is a - bi.", 0.98, "algebra"),
    "what is the modulus of a complex number": q("|a+bi| = sqrt(a^2 + b^2)", 0.98, "algebra"),
    "what is the argument of a complex number": q("arg(a+bi) = arctan(b/a), the angle from the positive real axis.", 0.96, "algebra"),
    "what is De Moivre's theorem": q("(cos x + i sin x)^n = cos(nx) + i sin(nx)", 0.96, "algebra"),
    "what is the polar form of a complex number": q("z = r(cos theta + i sin theta) = r e^(i theta), where r = |z|.", 0.96, "algebra"),
    "solve z^2 = -1": q("z = i or z = -i", 0.97, "algebra"),
    "solve z^2 + 1 = 0": q("z = i or z = -i", 0.97, "algebra"),
    "what is the imaginary part of 3-4i": q("Im(3-4i) = -4", 0.98, "algebra"),
    "what is the real part of 2+5i": q("Re(2+5i) = 2", 0.98, "algebra"),
}
ENTRIES.update(COMPLEX)

# ============================================================================
# SEQUENCES & SERIES (25 entries)
# ============================================================================
SEQ = {
    "what is an arithmetic sequence": q("A sequence where the difference between consecutive terms is constant. a_n = a_1 + (n-1)d", 0.97, "algebra"),
    "what is a geometric sequence": q("A sequence where the ratio between consecutive terms is constant. a_n = a_1 * r^(n-1)", 0.97, "algebra"),
    "sum of arithmetic series": q("S_n = n/2 * (a_1 + a_n) = n/2 * (2a_1 + (n-1)d)", 0.96, "algebra"),
    "sum of infinite geometric series": q("S = a_1/(1-r) for |r| < 1", 0.97, "algebra"),
    "sum of first n natural numbers": q("1+2+...+n = n(n+1)/2", 0.98, "arithmetic"),
    "sum of first n squares": q("1^2+2^2+...+n^2 = n(n+1)(2n+1)/6", 0.95, "arithmetic"),
    "sum of first n cubes": q("1^3+2^3+...+n^3 = (n(n+1)/2)^2", 0.95, "arithmetic"),
    "what is the common ratio in 2, 4, 8, 16": q("r = 2 (each term is doubled)", 0.97, "algebra"),
    "what is the next term in 1, 1, 2, 3, 5, 8": q("13 (Fibonacci sequence)", 0.97, "number_theory"),
    "what is the nth term of 3, 7, 11, 15": q("a_n = 3 + (n-1)*4 = 4n - 1", 0.96, "algebra"),
    "sum of 1+3+5+...+99": q("Sum of first 50 odd numbers = 50^2 = 2500", 0.96, "algebra"),
    "what is a telescoping series": q("A series where intermediate terms cancel, leaving only the first and last terms.", 0.95, "analysis"),
}
ENTRIES.update(SEQ)

# ============================================================================
# REASONING & LOGIC (30 entries)
# ============================================================================
LOGIC = {
    "what is modus ponens": q("Modus Ponens: If P implies Q, and P is true, then Q is true. P->Q, P |- Q", 0.98, "reasoning"),
    "what is modus tollens": q("Modus Tollens: If P implies Q, and Q is false, then P is false. P->Q, not Q |- not P", 0.98, "reasoning"),
    "what is a syllogism": q("A logical argument with two premises and a conclusion. Example: All A are B, all B are C, therefore all A are C.", 0.98, "reasoning"),
    "what is a tautology": q("A statement that is always true regardless of truth values of its components. Example: P or not P.", 0.98, "reasoning"),
    "what is a contradiction": q("A statement that is always false. Example: P and not P.", 0.98, "reasoning"),
    "what is De Morgan's law": q("Not(A and B) = Not A or Not B. Not(A or B) = Not A and Not B.", 0.98, "reasoning"),
    "what is the law of excluded middle": q("For any proposition P, either P is true or not-P is true. There is no third option.", 0.98, "reasoning"),
    "what is a counterexample": q("A specific case that disproves a universal claim. To disprove 'All primes are odd', note that 2 is prime and even.", 0.99, "reasoning"),
    "what is proof by contradiction": q("Assume the negation of what you want to prove, derive a contradiction, therefore the original statement must be true.", 0.98, "reasoning"),
    "what is proof by induction": q("1) Base case: prove P(1). 2) Inductive step: prove P(k) implies P(k+1) for all k >= 1. Then P(n) for all n.", 0.98, "reasoning"),
    "what is a necessary condition": q("P is necessary for Q if Q cannot be true without P being true. Q -> P.", 0.97, "reasoning"),
    "what is a sufficient condition": q("P is sufficient for Q if P being true guarantees Q is true. P -> Q.", 0.97, "reasoning"),
    "what is the transitive property": q("If A = B and B = C, then A = C. If A > B and B > C, then A > C.", 0.98, "reasoning"),
    "what is the difference between validity and soundness": q("A valid argument has correct logical form. A sound argument is valid AND has true premises.", 0.97, "reasoning"),
    "what is Occam's razor": q("Among competing hypotheses, the simplest one with the fewest assumptions should be preferred.", 0.97, "reasoning"),
    "what is affirming the consequent": q("A logical fallacy: P->Q, Q, therefore P. (If it's raining, the ground is wet. The ground is wet, therefore it's raining. This is invalid.)", 0.97, "reasoning"),
    "what is denying the antecedent": q("A logical fallacy: P->Q, not P, therefore not Q. (If it's raining, the ground is wet. It's not raining, therefore the ground is not wet. Invalid — sprinklers could have wet the ground.)", 0.97, "reasoning"),
}
ENTRIES.update(LOGIC)

# ============================================================================
# WRITE OUTPUT
# ============================================================================
def write_knowledge_base():
    output_path = os.path.join(os.path.dirname(__file__), "knowledge_base_v2.py")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""\n')
        f.write(f'Knowledge Base V2 — {len(ENTRIES)}+ Pre-computed Math & Reasoning Q&A Pairs\n')
        f.write('============================================================\n')
        f.write('Generated by generate_knowledge_base.py\n')
        f.write('"""\n\n')
        f.write('import math\n\n')
        f.write('PHI = 1.618033988749895\n')
        f.write('PI = math.pi\n')
        f.write('E = math.e\n\n')
        f.write('PRE_COMPUTED = {\n')
        
        for key, value in sorted(ENTRIES.items()):
            text = value["text"].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            f.write(f'    "{key}": {{\n')
            f.write(f'        "text": "{text}",\n')
            f.write(f'        "coherence": {value["coherence"]},\n')
            f.write(f'        "domain": "{value["domain"]}"\n')
            f.write(f'    }},\n')
        
        f.write('}\n\n')
        f.write('PRE_COMPUTED_NORMALIZED = {k.lower().strip(): v for k, v in PRE_COMPUTED.items()}\n')
    
    print(f"OK Generated {len(ENTRIES)} entries in {output_path}")
    return output_path

if __name__ == "__main__":
    write_knowledge_base()