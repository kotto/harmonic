#!/usr/bin/env python3
"""Knowledge Base Full — 503 entries"""
import math
PHI = 1.618033988749895
PI = math.pi
E = math.e

PRE_COMPUTED = {
    "100 - 37": {
        "text": "100 - 37 = 63",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "12 + 5": {
        "text": "12 + 5 = 17",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "144 / 12": {
        "text": "144 / 12 = 12",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "2+2": {
        "text": "2 + 2 = 4",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "2^10": {
        "text": "2^10 = 1024",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "8 * 7": {
        "text": "8 * 7 = 56",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "a rectangle has length 3 more than width. perimeter is 22. find dimensions": {
        "text": "Let w = width, l = w + 3\nPerimeter = 2(w + l) = 2(w + w + 3) = 4w + 6 = 22\n4w = 16, w = 4\nLength = 7, Width = 4",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "are all squares rectangles": {
        "text": "Yes, all squares are rectangles. A square is a rectangle with all sides equal.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "calculate 2 + 2": {
        "text": "2 + 2 = 4",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "convert 180 degrees to radians": {
        "text": "180 degrees = pi radians",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "convert 30 degrees to radians": {
        "text": "30 degrees = pi/6 radians",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "convert 45 degrees to radians": {
        "text": "45 degrees = pi/4 radians",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "convert 60 degrees to radians": {
        "text": "60 degrees = pi/3 radians",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "convert 90 degrees to radians": {
        "text": "90 degrees = pi/2 radians",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "cos(120 degrees)": {
        "text": "cos(120deg) = -1/2",
        "coherence": 0.97,
        "domain": "trigonometry"
    },
    "cos(135 degrees)": {
        "text": "cos(135deg) = -sqrt(2)/2",
        "coherence": 0.97,
        "domain": "trigonometry"
    },
    "cos(150 degrees)": {
        "text": "cos(150deg) = -sqrt(3)/2",
        "coherence": 0.97,
        "domain": "trigonometry"
    },
    "cos(30 degrees)": {
        "text": "cos(30deg) = sqrt(3)/2",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "cos(30)": {
        "text": "cos(30deg) = sqrt(3)/2",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "derivative of (x+1)/(x-1)": {
        "text": "d/dx((x+1)/(x-1)) = -2/(x-1)^2 (quotient rule)",
        "coherence": 0.94,
        "domain": "calculus"
    },
    "derivative of 3x^2": {
        "text": "d/dx(3x^2) = 6x",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "derivative of 4x^3": {
        "text": "d/dx(4x^3) = 12x^2",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "derivative of arccos(x)": {
        "text": "d/dx(arccos(x)) = -1/sqrt(1-x^2)",
        "coherence": 0.95,
        "domain": "calculus"
    },
    "derivative of cos(3x)": {
        "text": "d/dx(cos(3x)) = -3 sin(3x)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "derivative of cot(x)": {
        "text": "d/dx(cot(x)) = -csc^2(x)",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "derivative of csc(x)": {
        "text": "d/dx(csc(x)) = -csc(x) cot(x)",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "derivative of e^(2x)": {
        "text": "d/dx(e^(2x)) = 2 e^(2x)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "derivative of e^(3x)": {
        "text": "d/dx(e^(3x)) = 3 e^(3x)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "derivative of ln(2x)": {
        "text": "d/dx(ln(2x)) = 1/x",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "derivative of ln(sin(x))": {
        "text": "d/dx(ln(sin(x))) = cos(x)/sin(x) = cot(x)",
        "coherence": 0.94,
        "domain": "calculus"
    },
    "derivative of ln(x^2)": {
        "text": "d/dx(ln(x^2)) = 2/x",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "derivative of sec(x)": {
        "text": "d/dx(sec(x)) = sec(x) tan(x)",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "derivative of sin(2x)": {
        "text": "d/dx(sin(2x)) = 2 cos(2x) (chain rule)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "derivative of sqrt(x^2+1)": {
        "text": "d/dx(sqrt(x^2+1)) = x/sqrt(x^2+1)",
        "coherence": 0.94,
        "domain": "calculus"
    },
    "derivative of tan(x)": {
        "text": "d/dx(tan(x)) = sec^2(x)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "derivative of x e^x": {
        "text": "d/dx(x e^x) = e^x + x e^x = e^x(x + 1) (product rule)",
        "coherence": 0.95,
        "domain": "calculus"
    },
    "derivative of x^(1/2)": {
        "text": "d/dx(sqrt(x)) = 1/(2 sqrt(x))",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "derivative of x^2 sin(x)": {
        "text": "d/dx(x^2 sin(x)) = 2x sin(x) + x^2 cos(x)",
        "coherence": 0.95,
        "domain": "calculus"
    },
    "derivative of x^6": {
        "text": "d/dx(x^6) = 6x^5",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "diagonals of a rhombus are perpendicular": {
        "text": "Yes, diagonals of a rhombus are perpendicular bisectors of each other.",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "differentiate 5x": {
        "text": "d/dx(5x) = 5",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "divide 12 by 3": {
        "text": "12 / 3 = 4",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "expand (2x-1)^2": {
        "text": "(2x-1)^2 = 4x^2 - 4x + 1",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "expand (x+3)^2": {
        "text": "(x+3)^2 = x^2 + 6x + 9",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "find x if x + 3 = 7": {
        "text": "x = 4",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "gcd of 12 and 18": {
        "text": "GCD(12, 18) = 6. Factors of 12: 1,2,3,4,6,12. Factors of 18: 1,2,3,6,9,18. Common: 1,2,3,6. Largest: 6.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "gcd of 24 and 36": {
        "text": "GCD(24, 36) = 12",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "gcd of 48 and 60": {
        "text": "GCD(48, 60) = 12",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "how many 3-digit numbers can be formed from digits 1-5 with repetition": {
        "text": "5^3 = 125 numbers",
        "coherence": 0.97,
        "domain": "combinatorics"
    },
    "how many 3-digit numbers from 1-5 without repetition": {
        "text": "P(5,3) = 5*4*3 = 60 numbers",
        "coherence": 0.97,
        "domain": "combinatorics"
    },
    "how many degrees in a circle": {
        "text": "A full circle has 360 degrees (2π radians).",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "how many diagonals does an n-sided polygon have": {
        "text": "n(n-3)/2 diagonals.",
        "coherence": 0.96,
        "domain": "combinatorics"
    },
    "how many diagonals in a hexagon": {
        "text": "6(6-3)/2 = 9 diagonals",
        "coherence": 0.97,
        "domain": "combinatorics"
    },
    "how many diagonals in a pentagon": {
        "text": "5(5-3)/2 = 5 diagonals",
        "coherence": 0.97,
        "domain": "combinatorics"
    },
    "how many radians in a circle": {
        "text": "A full circle has 2π radians ≈ 6.283 radians.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "how many ways to arrange 3 books on a shelf": {
        "text": "3! = 3 * 2 * 1 = 6 ways.",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "how many ways to arrange 4 books": {
        "text": "4! = 24 ways",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "how many ways to arrange 5 people in a line": {
        "text": "5! = 120 ways",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "how many ways to choose 2 from 5": {
        "text": "C(5,2) = 10 ways",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "how many ways to choose 3 from 7": {
        "text": "C(7,3) = 35 ways",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "if all birds have wings and a penguin is a bird, does a penguin have wings": {
        "text": "Yes, a penguin has wings. By syllogism: All birds have wings. A penguin is a bird. Therefore, a penguin has wings. (Penguins do have wings, modified as flippers.)",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "if all cats are mammals and no mammals are fish, are cats fish": {
        "text": "No, cats are not fish. All cats are mammals, and no mammals are fish. Therefore, no cats are fish.",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "if it is snowing, the temperature is below freezing. the temperature is 40 degrees F": {
        "text": "Since 40°F > 32°F (above freezing), it cannot be snowing. This is modus tollens: If P (snowing) -> Q (below freezing). Not Q (above freezing). Therefore, not P (not snowing).",
        "coherence": 0.96,
        "domain": "reasoning"
    },
    "if x = 2 and y = x + 1, what is y": {
        "text": "y = x + 1 = 2 + 1 = 3. This is a simple substitution.",
        "coherence": 0.99,
        "domain": "reasoning"
    },
    "if x > 5 and y < 3, can x < y": {
        "text": "No. If x > 5 and y < 3, then x > 5 > 3 > y, so x > y. By transitivity of inequality, x > y.",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "integral from 0 to 1 of x dx": {
        "text": "int_0^1 x dx = [x^2/2]_0^1 = 1/2",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "integral from 0 to 1 of x^2 dx": {
        "text": "int_0^1 x^2 dx = [x^3/3]_0^1 = 1/3",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "integral from 0 to pi of sin(x) dx": {
        "text": "int_0^pi sin(x) dx = [-cos(x)]_0^pi = -(-1) - (-1) = 2",
        "coherence": 0.95,
        "domain": "calculus"
    },
    "integral from 1 to e of 1/x dx": {
        "text": "int_1^e 1/x dx = [ln|x|]_1^e = 1 - 0 = 1",
        "coherence": 0.95,
        "domain": "calculus"
    },
    "integral of 1/(x+1)": {
        "text": "int(1/(x+1) dx) = ln|x+1| + C",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "integral of 1/x^2": {
        "text": "int(1/x^2 dx) = -1/x + C",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "integral of 2x": {
        "text": "int(2x dx) = x^2 + C",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "integral of 3x^2": {
        "text": "int(3x^2 dx) = x^3 + C",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "integral of 5": {
        "text": "int(5 dx) = 5x + C",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "integral of cos(2x)": {
        "text": "int(cos(2x) dx) = (1/2) sin(2x) + C",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "integral of e^(2x)": {
        "text": "int(e^(2x) dx) = (1/2) e^(2x) + C",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "integral of ln(x)": {
        "text": "int(ln(x) dx) = x ln(x) - x + C",
        "coherence": 0.94,
        "domain": "calculus"
    },
    "integral of sec^2(x)": {
        "text": "int(sec^2(x) dx) = tan(x) + C",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "integral of sin(3x)": {
        "text": "int(sin(3x) dx) = -(1/3) cos(3x) + C",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "integral of tan(x)": {
        "text": "int(tan(x) dx) = -ln|cos(x)| + C = ln|sec(x)| + C",
        "coherence": 0.95,
        "domain": "calculus"
    },
    "integral of x e^x": {
        "text": "int(x e^x dx) = (x-1) e^x + C (integration by parts)",
        "coherence": 0.94,
        "domain": "calculus"
    },
    "integral of x^4": {
        "text": "int(x^4 dx) = x^5/5 + C",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "is 1 prime": {
        "text": "No, 1 is not prime. A prime number has exactly two distinct positive divisors. The number 1 has only one divisor.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "is 17 prime": {
        "text": "Yes, 17 is prime. Its only divisors are 1 and 17.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "is 2 prime": {
        "text": "Yes, 2 is prime. It is the only even prime number.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "is 29 prime": {
        "text": "Yes, 29 is prime.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "is 37 prime": {
        "text": "Yes, 37 is prime.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "is 51 prime": {
        "text": "No, 51 is not prime. 51 = 3 * 17.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "is 91 prime": {
        "text": "No, 91 = 7 * 13.",
        "coherence": 0.98,
        "domain": "number_theory"
    },
    "is 97 prime": {
        "text": "Yes, 97 is prime.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "lcm of 12 and 15": {
        "text": "LCM(12, 15) = 60",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "lcm of 4 and 6": {
        "text": "LCM(4, 6) = 12. Multiples of 4: 4,8,12,... Multiples of 6: 6,12,... First common: 12.",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "lcm of 6 and 8": {
        "text": "LCM(6, 8) = 24",
        "coherence": 0.99,
        "domain": "number_theory"
    },
    "limit of (1+1/n)^n as n goes to infinity": {
        "text": "lim(n->inf) (1+1/n)^n = e",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "limit of (x^2-1)/(x-1) as x goes to 1": {
        "text": "lim(x->1) (x^2-1)/(x-1) = lim(x->1) (x+1) = 2",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "limit of ln(x)/x as x goes to infinity": {
        "text": "lim(x->inf) ln(x)/x = 0",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "limit of sin(2x)/x as x goes to 0": {
        "text": "lim(x->0) sin(2x)/x = 2 * lim(x->0) sin(2x)/(2x) = 2 * 1 = 2",
        "coherence": 0.95,
        "domain": "calculus"
    },
    "limit of x/e^x as x goes to infinity": {
        "text": "lim(x->inf) x/e^x = 0 (exponential growth dominates)",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "number of subsets of a set of size n": {
        "text": "2^n subsets. For n=3, there are 2^3 = 8 subsets.",
        "coherence": 0.97,
        "domain": "combinatorics"
    },
    "probability of drawing two aces without replacement": {
        "text": "P(two aces) = (4/52)*(3/51) = 12/2652 = 1/221 = 0.45%",
        "coherence": 0.95,
        "domain": "probability"
    },
    "probability of heads twice in a row": {
        "text": "P(HH) = (1/2) * (1/2) = 1/4 = 25%",
        "coherence": 0.97,
        "domain": "probability"
    },
    "probability of not rolling a 6": {
        "text": "P(not 6) = 5/6 = 83.3%",
        "coherence": 0.98,
        "domain": "probability"
    },
    "probability of rolling a 6": {
        "text": "P(6) = 1/6 = 16.7%",
        "coherence": 0.99,
        "domain": "probability"
    },
    "probability of rolling at least one 6 in two dice": {
        "text": "P(at least one 6) = 1 - P(no 6) = 1 - (5/6)^2 = 1 - 25/36 = 11/36 = 30.6%",
        "coherence": 0.95,
        "domain": "probability"
    },
    "prove that sqrt(2) is irrational": {
        "text": "Proof by contradiction: Assume √2 = p/q in lowest terms. Then 2 = p^2/q^2, so p^2 = 2q^2. Thus p^2 is even, so p is even. Let p = 2k. Then (2k)^2 = 2q^2, so 4k^2 = 2q^2, so q^2 = 2k^2. Thus q^2 is even, so q is even. But then p and q are both even, contradicting that p/q is in lowest terms. Therefore, √2 is irrational.",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "round 2.71828 to 3 decimal places": {
        "text": "2.718",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "round 3.14159 to 2 decimal places": {
        "text": "3.14",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "second derivative of e^x": {
        "text": "f''(x) = e^x",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "second derivative of sin(x)": {
        "text": "f''(x) = -sin(x)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "second derivative of x^3": {
        "text": "f''(x) = 6x",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "simplify (x^2 - 1)/(x - 1)": {
        "text": "= (x+1)(x-1)/(x-1) = x + 1, for x not equal to 1",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "simplify (x^2 - 4)/(x + 2)": {
        "text": "= (x-2)(x+2)/(x+2) = x - 2, for x not equal to -2",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "sin(120 degrees)": {
        "text": "sin(120deg) = sin(60deg) = sqrt(3)/2",
        "coherence": 0.97,
        "domain": "trigonometry"
    },
    "sin(135 degrees)": {
        "text": "sin(135deg) = sqrt(2)/2",
        "coherence": 0.97,
        "domain": "trigonometry"
    },
    "sin(150 degrees)": {
        "text": "sin(150deg) = sin(30deg) = 1/2",
        "coherence": 0.97,
        "domain": "trigonometry"
    },
    "sin(30 degrees)": {
        "text": "sin(30deg) = 1/2",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "sin(60 degrees)": {
        "text": "sin(60deg) = sqrt(3)/2",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "solve -2x < 6": {
        "text": "x > -3 (inequality reverses when dividing by negative)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve 2(x - 1) = 8": {
        "text": "2x - 2 = 8\n2x = 10\nx = 5",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve 2^x = 16": {
        "text": "2^x = 2^4, x = 4",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve 2^x = 8": {
        "text": "2^x = 2^3, x = 3",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve 2x + 3 = 11": {
        "text": "Solving 2x + 3 = 11:\n2x = 8\nx = 4",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve 2x + 5 = 3x - 2": {
        "text": "2x + 5 = 3x - 2\n5 + 2 = 3x - 2x\nx = 7",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve 2x - 5 < 3": {
        "text": "2x < 8, x < 4",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve 2x - 5 = 7": {
        "text": "2x = 12, x = 6",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve 2x = 10": {
        "text": "Solving 2x = 10:\nx = 10 / 2\nx = 5",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve 2x^2 + 5x + 2 = 0": {
        "text": "(2x+1)(x+2) = 0, x = -1/2 or x = -2",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "solve 2x^2 - 4x - 6 = 0": {
        "text": "x = (4 + sqrt(16+48))/4 = (4+8)/4 = 3 or x = (4-8)/4 = -1",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "solve 3(x + 2) = 15": {
        "text": "3x + 6 = 15\n3x = 9\nx = 3",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve 3^x = 27": {
        "text": "3^x = 3^3, x = 3",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve 3x + 4 = 19": {
        "text": "3x = 15, x = 5",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve 3x + 7 = 22": {
        "text": "Solving 3x + 7 = 22:\n3x = 15\nx = 5",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve 4x - 2 = 10": {
        "text": "4x = 12, x = 3",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve 4x - 8 = 0": {
        "text": "Solving 4x - 8 = 0:\n4x = 8\nx = 2",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve 5^x = 125": {
        "text": "5^x = 5^3, x = 3",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve 5x - 3 = 2x + 9": {
        "text": "Solving 5x - 3 = 2x + 9:\n3x = 12\nx = 4",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve log_2(8)": {
        "text": "log_2(8) = 3 since 2^3 = 8",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve the system: 2x + y = 7, x - y = 2": {
        "text": "Adding: 3x = 9, x = 3\nThen y = 7 - 2(3) = 1\nSolution: (3, 1)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve the system: x + 2y = 5, 3x - y = 1": {
        "text": "From eq1: x = 5 - 2y\nSub into eq2: 3(5-2y) - y = 1\n15 - 6y - y = 1\n-7y = -14\ny = 2\nx = 5 - 2(2) = 1\nSolution: (1, 2)",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "solve the system: x + y = 5, x - y = 1": {
        "text": "Adding: 2x = 6, x = 3\nSubtracting: 2y = 4, y = 2\nSolution: (3, 2)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x + 3 = 7": {
        "text": "x = 4",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x + 3 > 7": {
        "text": "x > 4",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve x + 5 = 10": {
        "text": "Solving x + 5 = 10:\nx = 10 - 5\nx = 5",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x/2 = 5": {
        "text": "x = 10",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x/3 = 4": {
        "text": "x = 12",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x^2 + 2x + 1 = 0": {
        "text": "Solving x^2 + 2x + 1 = 0:\nFactor: (x+1)^2 = 0\nx = -1 (double root)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 + 4x + 4 = 0": {
        "text": "(x+2)^2 = 0, x = -2 (double root)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 + 7x + 12 = 0": {
        "text": "Solving x^2 + 7x + 12 = 0:\nFactor: (x+3)(x+4) = 0\nx = -3 or x = -4",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 + x - 1 = 0": {
        "text": "x = (-1 + sqrt(5))/2 or x = (-1 - sqrt(5))/2\nx = 0.618... or x = -1.618... (the golden ratio and its negative)",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "solve x^2 + x - 12 = 0": {
        "text": "(x+4)(x-3) = 0, x = -4 or x = 3",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 + x - 2 = 0": {
        "text": "Solving x^2 + x - 2 = 0:\nFactor: (x+2)(x-1) = 0\nx = -2 or x = 1",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 1 = 0": {
        "text": "Solving x^2 - 1 = 0:\nx^2 = 1\nx = ±1",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x^2 - 10x + 25 = 0": {
        "text": "(x-5)^2 = 0, x = 5 (double root)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 25 = 0": {
        "text": "Solving x^2 - 25 = 0:\nx^2 = 25\nx = ±5",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x^2 - 2x + 1 = 0": {
        "text": "Solving x^2 - 2x + 1 = 0:\nFactor: (x-1)^2 = 0\nx = 1 (double root)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 2x - 8 = 0": {
        "text": "(x-4)(x+2) = 0, x = 4 or x = -2",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 36 = 0": {
        "text": "x^2 = 36, x = 6 or x = -6",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x^2 - 4 = 0": {
        "text": "Solving x^2 - 4 = 0:\nx^2 = 4\nx = ±2",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x^2 - 49 = 0": {
        "text": "x^2 = 49, x = 7 or x = -7",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x^2 - 4x + 4 = 0": {
        "text": "Solving x^2 - 4x + 4 = 0:\nFactor: (x-2)^2 = 0\nx = 2 (double root)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 5x + 6 = 0": {
        "text": "Solving x^2 - 5x + 6 = 0:\nFactor: (x-2)(x-3) = 0\nx = 2 or x = 3",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 6x + 9 = 0": {
        "text": "Solving x^2 - 6x + 9 = 0:\nFactor: (x-3)^2 = 0\nx = 3 (double root)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 7x + 10 = 0": {
        "text": "Solving x^2 - 7x + 10 = 0:\nFactor: (x-2)(x-5) = 0\nx = 2 or x = 5",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 8x + 16 = 0": {
        "text": "Solving x^2 - 8x + 16 = 0:\nFactor: (x-4)^2 = 0\nx = 4 (double root)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - 9 = 0": {
        "text": "Solving x^2 - 9 = 0:\nx^2 = 9\nx = ±3",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x^2 - 9x + 20 = 0": {
        "text": "(x-4)(x-5) = 0, x = 4 or x = 5",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 - x - 6 = 0": {
        "text": "(x-3)(x+2) = 0, x = 3 or x = -2",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve x^2 < 4": {
        "text": "-2 < x < 2",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "solve x^2 = 16": {
        "text": "Solving x^2 = 16:\nx = ±4",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve x^2 = 9": {
        "text": "x = 3 or x = -3",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "solve z^2 + 1 = 0": {
        "text": "z = i or z = -i",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve z^2 = -1": {
        "text": "z = i or z = -i",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve |2x + 1| = 3": {
        "text": "2x + 1 = 3 or 2x + 1 = -3\n2x = 2 or 2x = -4\nx = 1 or x = -2",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "solve |x - 2| = 5": {
        "text": "x - 2 = 5 or x - 2 = -5\nx = 7 or x = -3",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve |x - 3| = 7": {
        "text": "Solving |x - 3| = 7:\nx - 3 = 7 → x = 10   OR   x - 3 = -7 → x = -4",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "solve |x| = 5": {
        "text": "Solving |x| = 5:\nx = 5 or x = -5",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "square 8": {
        "text": "8^2 = 64",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "square root of 144": {
        "text": "√144 = 12",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "square root of 2": {
        "text": "√2 ≈ 1.4142135623730951",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "square root of 64": {
        "text": "√64 = 8",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "sum of 1+3+5+...+99": {
        "text": "Sum of first 50 odd numbers = 50^2 = 2500",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "sum of arithmetic series": {
        "text": "S_n = n/2 * (a_1 + a_n) = n/2 * (2a_1 + (n-1)d)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "sum of first n cubes": {
        "text": "1^3+2^3+...+n^3 = (n(n+1)/2)^2",
        "coherence": 0.95,
        "domain": "arithmetic"
    },
    "sum of first n natural numbers": {
        "text": "1+2+...+n = n(n+1)/2",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "sum of first n squares": {
        "text": "1^2+2^2+...+n^2 = n(n+1)(2n+1)/6",
        "coherence": 0.95,
        "domain": "arithmetic"
    },
    "sum of infinite geometric series": {
        "text": "S = a_1/(1-r) for |r| < 1",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "tan(30 degrees)": {
        "text": "tan(30deg) = 1/sqrt(3) = sqrt(3)/3",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "tan(60 degrees)": {
        "text": "tan(60deg) = sqrt(3)",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "the sum of two consecutive integers is 15. find them": {
        "text": "x + (x+1) = 15\n2x = 14\nx = 7\nThe numbers are 7 and 8.",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "third derivative of x^4": {
        "text": "f'''(x) = 24x",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "twice a number plus 5 equals 15. find the number": {
        "text": "2x + 5 = 15\n2x = 10\nx = 5",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "what are complementary angles": {
        "text": "Two angles that sum to 90 degrees.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what are eigenvalues and eigenvectors": {
        "text": "For matrix A, if Av = lambda*v, then lambda is an eigenvalue and v is its eigenvector.",
        "coherence": 0.95,
        "domain": "linear_algebra"
    },
    "what are supplementary angles": {
        "text": "Two angles that sum to 180 degrees.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what are the factors of 24": {
        "text": "Factors of 24: 1, 2, 3, 4, 6, 8, 12, 24",
        "coherence": 0.98,
        "domain": "number_theory"
    },
    "what are the factors of 36": {
        "text": "Factors of 36: 1, 2, 3, 4, 6, 9, 12, 18, 36",
        "coherence": 0.98,
        "domain": "number_theory"
    },
    "what are the prime factors of 60": {
        "text": "60 = 2^2 * 3 * 5",
        "coherence": 0.98,
        "domain": "number_theory"
    },
    "what are the prime factors of 84": {
        "text": "84 = 2^2 * 3 * 7",
        "coherence": 0.98,
        "domain": "number_theory"
    },
    "what is (1+i)^2": {
        "text": "(1+i)^2 = 1 + 2i + i^2 = 1 + 2i - 1 = 2i",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "what is (2 + 3) * 4": {
        "text": "(2 + 3) * 4 = 5 * 4 = 20",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is (a+b)^2": {
        "text": "(a+b)^2 = a^2 + 2ab + b^2",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is (a+b)^3": {
        "text": "(a+b)^3 = a^3 + 3a^2b + 3ab^2 + b^3",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is (a-b)^2": {
        "text": "(a-b)^2 = a^2 - 2ab + b^2",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is (x+1)(x+4)": {
        "text": "(x+1)(x+4) = x^2 + 5x + 4",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is (x+2)(x-3)": {
        "text": "(x+2)(x-3) = x^2 - x - 6",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is (x-5)(x+5)": {
        "text": "(x-5)(x+5) = x^2 - 25 (difference of squares)",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is 0!": {
        "text": "0! = 1 (by convention and the Gamma function)",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 0.999... equal to": {
        "text": "0.999... = 1. This is a mathematical fact, not an approximation. Proof: Let x=0.999... Then 10x=9.999... Subtract: 9x=9, so x=1.",
        "coherence": 0.98,
        "domain": "analysis"
    },
    "what is 1 + cot^2(x)": {
        "text": "1 + cot^2(x) = csc^2(x)",
        "coherence": 0.97,
        "domain": "trigonometry"
    },
    "what is 1 + tan^2(x)": {
        "text": "1 + tan^2(x) = sec^2(x)",
        "coherence": 0.97,
        "domain": "trigonometry"
    },
    "what is 1/2 + 1/3": {
        "text": "1/2 + 1/3 = 3/6 + 2/6 = 5/6",
        "coherence": 0.97,
        "domain": "arithmetic"
    },
    "what is 1/2 + 1/4": {
        "text": "1/2 + 1/4 = 2/4 + 1/4 = 3/4",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 10 - 2 * 3": {
        "text": "10 - 2 * 3 = 10 - 6 = 4",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 10 - 3": {
        "text": "10 - 3 = 7",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 10!": {
        "text": "10! = 10 * 9 * 8 * 7 * 6 * 5 * 4 * 3 * 2 * 1 = 3,628,800",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 10% of 200": {
        "text": "10% of 200 = 0.10 * 200 = 20",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 1000 - 567": {
        "text": "1000 - 567 = 433",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 1000 / 8": {
        "text": "1000 / 8 = 125",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 10^3": {
        "text": "10^3 = 1000",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 11^2": {
        "text": "11^2 = 121",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 12 / 3": {
        "text": "12 / 3 = 4",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 12^2": {
        "text": "12^2 = 144",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 13^2": {
        "text": "13^2 = 169",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 14^2": {
        "text": "14^2 = 196",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 15 * 6": {
        "text": "15 * 6 = 90",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 15 + 27": {
        "text": "15 + 27 = 42",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 15% of 60": {
        "text": "15% of 60 = 0.15 * 60 = 9",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 15^2": {
        "text": "15^2 = 225",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 16^2": {
        "text": "16^2 = 256",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 2 + 2": {
        "text": "2 + 2 = 4",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 2 + 3 * 4": {
        "text": "2 + 3 * 4 = 2 + 12 = 14 (multiplication before addition)",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 2/3 of 90": {
        "text": "2/3 * 90 = 60",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 20^2": {
        "text": "20^2 = 400",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 25 * 4": {
        "text": "25 * 4 = 100",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 25% of 80": {
        "text": "25% of 80 = 0.25 * 80 = 20",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 2^6": {
        "text": "2^6 = 64",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 2^8": {
        "text": "2^8 = 256",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 3 + 6 / 3": {
        "text": "3 + 6 / 3 = 3 + 2 = 5",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 3/4 of 100": {
        "text": "3/4 * 100 = 75",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 3^3": {
        "text": "3^3 = 27",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 3^4": {
        "text": "3^4 = 3 * 3 * 3 * 3 = 81",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 4 * 6": {
        "text": "4 * 6 = 24",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 4!": {
        "text": "4! = 4 * 3 * 2 * 1 = 24",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 5 + 3": {
        "text": "5 + 3 = 8",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 5!": {
        "text": "5! = 5 * 4 * 3 * 2 * 1 = 120",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 50% of 150": {
        "text": "50% of 150 = 75",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 5^3": {
        "text": "5^3 = 5 * 5 * 5 = 125",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 6 + 4 * 5 - 3": {
        "text": "6 + 4 * 5 - 3 = 6 + 20 - 3 = 23",
        "coherence": 0.97,
        "domain": "arithmetic"
    },
    "what is 6!": {
        "text": "6! = 6 * 5 * 4 * 3 * 2 * 1 = 720",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 7!": {
        "text": "7! = 5040",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 72 / 9": {
        "text": "72 / 9 = 8",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 7^2": {
        "text": "7^2 = 49",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 8!": {
        "text": "8! = 40320",
        "coherence": 0.98,
        "domain": "arithmetic"
    },
    "what is 9 * 8": {
        "text": "9 * 8 = 72",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 90 / 15": {
        "text": "90 / 15 = 6",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 99 * 99": {
        "text": "99 * 99 = 9801",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is 9^2": {
        "text": "9^2 = 81",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is Bayes' theorem": {
        "text": "Bayes' theorem: P(A|B) = P(B|A) * P(A) / P(B).",
        "coherence": 0.98,
        "domain": "probability"
    },
    "what is De Moivre's theorem": {
        "text": "(cos x + i sin x)^n = cos(nx) + i sin(nx)",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "what is De Morgan's law": {
        "text": "De Morgan's laws:\nnot(A and B) = not A or not B\nnot(A or B) = not A and not B",
        "coherence": 0.99,
        "domain": "reasoning"
    },
    "what is L'Hopital's rule": {
        "text": "If lim f(x)/g(x) gives 0/0 or inf/inf, then lim f(x)/g(x) = lim f'(x)/g'(x), provided the limit exists.",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is Occam's razor": {
        "text": "Occam's razor: Among competing hypotheses, the simplest one with the fewest assumptions should be preferred.",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "what is a box plot": {
        "text": "A box plot shows min, Q1, median, Q3, and max of a dataset. Outliers are plotted as individual points.",
        "coherence": 0.96,
        "domain": "statistics"
    },
    "what is a combination": {
        "text": "A combination is a selection of objects where order does not matter. C(n,r) = n!/(r!(n-r)!).",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "what is a complex number": {
        "text": "A complex number has the form a + bi, where a and b are real numbers and i^2 = -1.",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is a confidence interval": {
        "text": "A confidence interval gives a range of plausible values for a population parameter. A 95% CI means: if we repeated the experiment many times, 95% of CIs would contain the true parameter.",
        "coherence": 0.95,
        "domain": "statistics"
    },
    "what is a contradiction": {
        "text": "A contradiction is a statement that is always false.\nExample: P and not P.",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is a counterexample": {
        "text": "A counterexample is a specific case that disproves a universal claim. To disprove 'All primes are odd', the counterexample is 2 (which is prime and even).",
        "coherence": 0.99,
        "domain": "reasoning"
    },
    "what is a critical point": {
        "text": "A critical point of f occurs where f'(x) = 0 or f'(x) does not exist. Critical points are candidates for local maxima/minima.",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is a derivative": {
        "text": "The derivative f'(x) = lim(h->0) [f(x+h)-f(x)]/h represents the instantaneous rate of change of f at x, or the slope of the tangent line.",
        "coherence": 0.99,
        "domain": "calculus"
    },
    "what is a function": {
        "text": "A function f is a relation that assigns exactly one output to each input. Denoted f: X -> Y or y = f(x).",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is a geometric sequence": {
        "text": "A sequence where the ratio between consecutive terms is constant. a_n = a_1 * r^(n-1)",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is a limit": {
        "text": "A limit lim(x->a) f(x) = L means that f(x) approaches L as x approaches a. Limits are the foundation of calculus.",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is a linear transformation": {
        "text": "A function T: V -> W that preserves vector addition and scalar multiplication: T(u+v) = T(u)+T(v) and T(cv) = cT(v).",
        "coherence": 0.96,
        "domain": "linear_algebra"
    },
    "what is a logical equivalence": {
        "text": "Two statements are logically equivalent if they have the same truth value in every possible scenario. Denoted by <->.",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "what is a matrix": {
        "text": "A matrix is a rectangular array of numbers arranged in rows and columns.",
        "coherence": 0.98,
        "domain": "linear_algebra"
    },
    "what is a necessary condition": {
        "text": "P is a necessary condition for Q if Q cannot be true without P being true. Q -> P.",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "what is a one-to-one function": {
        "text": "A function f is one-to-one (injective) if f(a) = f(b) implies a = b. Each output comes from exactly one input.",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is a p-value": {
        "text": "The p-value is the probability of obtaining results at least as extreme as observed, assuming the null hypothesis is true. A small p-value (< 0.05 typically) suggests rejecting the null hypothesis.",
        "coherence": 0.96,
        "domain": "statistics"
    },
    "what is a permutation": {
        "text": "A permutation is an arrangement of objects in a specific order. P(n,r) = n!/(n-r)!.",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "what is a random variable": {
        "text": "A random variable is a function that assigns a numerical value to each outcome of a random experiment.",
        "coherence": 0.97,
        "domain": "probability"
    },
    "what is a right angle": {
        "text": "A right angle is exactly 90 degrees (π/2 radians).",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is a sufficient and necessary condition": {
        "text": "P is a sufficient and necessary condition for Q if P <-> Q (P if and only if Q). P is true exactly when Q is true.",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "what is a sufficient condition": {
        "text": "P is a sufficient condition for Q if P being true guarantees Q is true. P -> Q.",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "what is a syllogism": {
        "text": "A syllogism is a logical argument with two premises and a conclusion.\nExample: All A are B, all B are C, therefore all A are C.",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is a tautology": {
        "text": "A tautology is a statement that is always true, regardless of the truth values of its components.\nExample: P or not P (law of excluded middle).",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is a taylor series": {
        "text": "Taylor series: f(x) = f(a) + f'(a)(x-a)/1! + f''(a)(x-a)^2/2! + ... + f^(n)(a)(x-a)^n/n! + ...",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is a telescoping series": {
        "text": "A series where intermediate terms cancel, leaving only the first and last terms.",
        "coherence": 0.95,
        "domain": "analysis"
    },
    "what is a unit vector": {
        "text": "A vector with length (magnitude) equal to 1.",
        "coherence": 0.98,
        "domain": "linear_algebra"
    },
    "what is a z-score": {
        "text": "z = (x - mu) / sigma, measures how many standard deviations x is from the mean.",
        "coherence": 0.97,
        "domain": "statistics"
    },
    "what is a^2 - b^2": {
        "text": "a^2 - b^2 = (a+b)(a-b) — difference of squares",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is affirming the consequent": {
        "text": "A logical fallacy: P->Q, Q, therefore P. (If it's raining, the ground is wet. The ground is wet, therefore it's raining. This is invalid.)",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "what is an acute angle": {
        "text": "An acute angle is less than 90 degrees.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is an arithmetic sequence": {
        "text": "A sequence where the difference between consecutive terms is constant. a_n = a_1 + (n-1)d",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is an inflection point": {
        "text": "An inflection point is where the concavity of f changes (f''(x) changes sign). f''(x) = 0 or undefined at the point.",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is an integral": {
        "text": "The definite integral ∫[a,b] f(x)dx represents the signed area under the curve f(x) from a to b. The indefinite integral ∫f(x)dx = F(x) + C is the antiderivative.",
        "coherence": 0.99,
        "domain": "calculus"
    },
    "what is an isosceles triangle": {
        "text": "A triangle with at least two equal sides and two equal base angles.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is an obtuse angle": {
        "text": "An obtuse angle is greater than 90 degrees but less than 180 degrees.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is completing the square": {
        "text": "Completing the square converts ax^2 + bx + c to a(x + b/(2a))^2 + (c - b^2/(4a)).\nExample: x^2 + 6x + 5 = (x+3)^2 - 4.",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is conditional probability": {
        "text": "P(A|B) = P(A ∩ B) / P(B). The probability of A given that B has occurred.",
        "coherence": 0.98,
        "domain": "probability"
    },
    "what is correlation": {
        "text": "Correlation measures the strength and direction of a linear relationship between two variables. It ranges from -1 (perfect negative) to +1 (perfect positive). Correlation does not imply causation.",
        "coherence": 0.97,
        "domain": "statistics"
    },
    "what is cos(0)": {
        "text": "cos(0) = 1",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is cos(180)": {
        "text": "cos(180°) = -1",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is cos(2x)": {
        "text": "cos(2x) = cos^2(x) - sin^2(x) = 2cos^2(x) - 1 = 1 - 2sin^2(x).",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is cos(60)": {
        "text": "cos(60°) = 1/2 = 0.5",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is cos(90)": {
        "text": "cos(90°) = 0",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is cos(a+b)": {
        "text": "cos(a+b) = cos(a)cos(b) - sin(a)sin(b).",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is cos(pi)": {
        "text": "cos(pi) = -1",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is cos(pi/2)": {
        "text": "cos(pi/2) = 0",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is cos(pi/3)": {
        "text": "cos(pi/3) = 1/2",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is cos(pi/4)": {
        "text": "cos(pi/4) = sqrt(2)/2",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is cos(pi/6)": {
        "text": "cos(pi/6) = sqrt(3)/2",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is cot(x)": {
        "text": "cot(x) = 1/tan(x) = cos(x)/sin(x).",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is csc(x)": {
        "text": "csc(x) = 1/sin(x).",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is denying the antecedent": {
        "text": "A logical fallacy: P->Q, not P, therefore not Q. (If it's raining, the ground is wet. It's not raining, therefore the ground is not wet. Invalid — sprinklers could have wet the ground.)",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "what is e": {
        "text": "e = 2.718281828459045 is Euler's number, the base of the natural logarithm. It is the limit of (1+1/n)^n as n approaches infinity.",
        "coherence": 0.99,
        "domain": "analysis"
    },
    "what is euler's identity": {
        "text": "e^(iπ) + 1 = 0. Considered the most beautiful equation in mathematics. It connects five fundamental constants (e, i, π, 1, 0) through addition, multiplication, and exponentiation.",
        "coherence": 0.99,
        "domain": "analysis"
    },
    "what is expected value": {
        "text": "Expected value E[X] = Σ x * P(X=x) is the weighted average of all possible values of X.",
        "coherence": 0.98,
        "domain": "probability"
    },
    "what is i": {
        "text": "i = √(-1) is the imaginary unit. i^2 = -1. Complex numbers have the form a + bi.",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is i^2": {
        "text": "i^2 = -1",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is i^3": {
        "text": "i^3 = i^2 * i = -i",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is i^4": {
        "text": "i^4 = (i^2)^2 = 1",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is infinity": {
        "text": "Infinity (∞) is not a number but a concept representing unboundedness. lim(x->inf) 1/x = 0.",
        "coherence": 0.97,
        "domain": "analysis"
    },
    "what is ln(e^2)": {
        "text": "ln(e^2) = 2",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is log_10(1000)": {
        "text": "log_10(1000) = 3 since 10^3 = 1000",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is matrix addition": {
        "text": "Add corresponding entries: (A+B)_{ij} = A_{ij} + B_{ij}. Both matrices must have same dimensions.",
        "coherence": 0.97,
        "domain": "linear_algebra"
    },
    "what is matrix multiplication": {
        "text": "(AB)_{ij} = sum_k A_{ik} * B_{kj}. The number of columns of A must equal the number of rows of B.",
        "coherence": 0.96,
        "domain": "linear_algebra"
    },
    "what is modus ponens": {
        "text": "Modus Ponens: If P implies Q, and P is true, then Q is true.\nP -> Q, P |- Q",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is modus tollens": {
        "text": "Modus Tollens: If P implies Q, and Q is false, then P is false.\nP -> Q, not Q |- not P",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is pascal's triangle": {
        "text": "Pascal's triangle: each number is the sum of the two above it. Row n gives binomial coefficients C(n,k). Rows: 1; 1,1; 1,2,1; 1,3,3,1; ...",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "what is pi": {
        "text": "π ≈ 3.14159 is the ratio of a circle's circumference to its diameter. It is an irrational and transcendental number.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is proof by contradiction": {
        "text": "Proof by contradiction: Assume the negation of what you want to prove, derive a contradiction, conclude the original statement must be true.",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is proof by induction": {
        "text": "Mathematical induction: 1) Base case: prove P(1). 2) Inductive step: prove P(k) -> P(k+1) for all k >= 1. Then P(n) is true for all n.",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is scalar multiplication of a matrix": {
        "text": "Multiply every entry of the matrix by the scalar.",
        "coherence": 0.97,
        "domain": "linear_algebra"
    },
    "what is sec(x)": {
        "text": "sec(x) = 1/cos(x).",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is sin(0)": {
        "text": "sin(0) = 0",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is sin(180)": {
        "text": "sin(180°) = 0",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is sin(2x)": {
        "text": "sin(2x) = 2 sin(x) cos(x). Double-angle formula.",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is sin(30)": {
        "text": "sin(30°) = 1/2 = 0.5",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is sin(45)": {
        "text": "sin(45°) = √2/2 ≈ 0.7071",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is sin(90)": {
        "text": "sin(90°) = 1",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is sin(a+b)": {
        "text": "sin(a+b) = sin(a)cos(b) + cos(a)sin(b).",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is sin(pi)": {
        "text": "sin(pi) = 0",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is sin(pi/2)": {
        "text": "sin(pi/2) = 1",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is sin(pi/3)": {
        "text": "sin(pi/3) = sqrt(3)/2",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is sin(pi/4)": {
        "text": "sin(pi/4) = sqrt(2)/2",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is sin(pi/6)": {
        "text": "sin(pi/6) = 1/2",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is sin^2(x) + cos^2(x)": {
        "text": "sin^2(x) + cos^2(x) = 1. This is the Pythagorean identity.",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is standard deviation": {
        "text": "Standard deviation measures the spread of data around the mean. SD = sqrt(variance).",
        "coherence": 0.97,
        "domain": "statistics"
    },
    "what is tan(45)": {
        "text": "tan(45°) = 1",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is tan(x)": {
        "text": "tan(x) = sin(x)/cos(x).",
        "coherence": 0.99,
        "domain": "trigonometry"
    },
    "what is the Riemann hypothesis": {
        "text": "The Riemann hypothesis conjectures that all non-trivial zeros of the Riemann zeta function have real part 1/2. It is one of the most important unsolved problems in mathematics.",
        "coherence": 0.96,
        "domain": "number_theory"
    },
    "what is the absolute value of -15": {
        "text": "|-15| = 15",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is the absolute value of 7": {
        "text": "|7| = 7",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is the arc length of a circle": {
        "text": "Arc length = (theta/360) * 2 pi r (degrees) or r * theta (radians)",
        "coherence": 0.96,
        "domain": "geometry"
    },
    "what is the area of a circle": {
        "text": "A = pi r^2",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is the area of a circle with radius 3": {
        "text": "Area = πr^2 = π * 9 = 9π ≈ 28.27 square units.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the area of a rectangle 5 by 3": {
        "text": "Area = length * width = 5 * 3 = 15 square units.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the area of a rectangle with length l and width w": {
        "text": "Area = l * w",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the area of a sector of a circle": {
        "text": "Area = (theta/360) * pi r^2 (theta in degrees) or (1/2) r^2 theta (theta in radians)",
        "coherence": 0.96,
        "domain": "geometry"
    },
    "what is the area of a square with side 4": {
        "text": "Area = side^2 = 4^2 = 16 square units.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the area of a square with side s": {
        "text": "Area = s^2",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the area of a trapezoid": {
        "text": "Area = (1/2)(b1 + b2)h, where b1,b2 are parallel bases and h is height",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the area of a trapezoid with bases 4 and 6 height 3": {
        "text": "Area = (1/2)(b1+b2)h = (1/2)(4+6)*3 = 15 square units.",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the area of a triangle with base 6 and height 4": {
        "text": "Area = (1/2) * base * height = (1/2) * 6 * 4 = 12 square units.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the area of a triangle with base b and height h": {
        "text": "Area = (1/2) b h",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the area of an equilateral triangle with side 4": {
        "text": "Area = (√3/4) * side^2 = (√3/4) * 16 = 4√3 ≈ 6.928 square units.",
        "coherence": 0.96,
        "domain": "geometry"
    },
    "what is the area of an equilateral triangle with side a": {
        "text": "Area = (sqrt(3)/4) a^2",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the argument of a complex number": {
        "text": "arg(a+bi) = arctan(b/a), the angle from the positive real axis.",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "what is the binomial coefficient": {
        "text": "C(n,k) = n!/(k!(n-k)!) counts the number of ways to choose k items from n (order doesn't matter).",
        "coherence": 0.98,
        "domain": "combinatorics"
    },
    "what is the binomial theorem": {
        "text": "(a+b)^n = C(n,0)a^n + C(n,1)a^(n-1)b + ... + C(n,k)a^(n-k)b^k + ... + C(n,n)b^n\nwhere C(n,k) = n! / (k!(n-k)!).",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is the cardinality of the set of real numbers": {
        "text": "The cardinality of R is c (the continuum), which is strictly greater than aleph-0 (countable infinity). This is Cantor's theorem.",
        "coherence": 0.95,
        "domain": "set_theory"
    },
    "what is the central limit theorem": {
        "text": "The Central Limit Theorem states that the sum (or mean) of a large number of independent random variables, regardless of their distribution, is approximately normally distributed.",
        "coherence": 0.97,
        "domain": "statistics"
    },
    "what is the chain rule": {
        "text": "Chain rule: d/dx[f(g(x))] = f'(g(x)) * g'(x).\nExample: d/dx(sin(x^2)) = cos(x^2) * 2x.",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the circumference of a circle": {
        "text": "C = 2 pi r = pi d",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is the circumference of a circle with radius 7": {
        "text": "Circumference = 2πr = 2π * 7 = 14π ≈ 43.98 units.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the common ratio in 2, 4, 8, 16": {
        "text": "r = 2 (each term is doubled)",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is the conjugate of a+bi": {
        "text": "The conjugate is a - bi.",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is the cross product": {
        "text": "For 3D vectors, u x v = (u_2*v_3 - u_3*v_2, u_3*v_1 - u_1*v_3, u_1*v_2 - u_2*v_1). Result is perpendicular to both u and v.",
        "coherence": 0.96,
        "domain": "linear_algebra"
    },
    "what is the cube root of 27": {
        "text": "The cube root of 27 is 3 (since 3^3 = 27).",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is the cube root of 8": {
        "text": "The cube root of 8 is 2 (since 2^3 = 8).",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is the degree of 3x^4 + 2x^2 - x + 5": {
        "text": "The degree is 4 (highest power of x).",
        "coherence": 0.97,
        "domain": "algebra"
    },
    "what is the derivative of 1/x": {
        "text": "d/dx(1/x) = -1/x^2",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the derivative of 5x": {
        "text": "d/dx(5x) = 5",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the derivative of a^x": {
        "text": "d/dx(a^x) = a^x * ln(a)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is the derivative of arcsin(x)": {
        "text": "d/dx(arcsin(x)) = 1/√(1-x^2)",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "what is the derivative of arctan(x)": {
        "text": "d/dx(arctan(x)) = 1/(1+x^2)",
        "coherence": 0.96,
        "domain": "calculus"
    },
    "what is the derivative of cos(x)": {
        "text": "d/dx(cos(x)) = -sin(x)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is the derivative of e^x": {
        "text": "d/dx(e^x) = e^x. The exponential function is its own derivative.",
        "coherence": 0.99,
        "domain": "calculus"
    },
    "what is the derivative of ln(x)": {
        "text": "d/dx(ln(x)) = 1/x for x > 0",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the derivative of sqrt(x)": {
        "text": "d/dx(√x) = 1/(2√x) for x > 0",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is the derivative of tan(x)": {
        "text": "d/dx(tan(x)) = sec^2(x)",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is the derivative of x^3": {
        "text": "d/dx(x^3) = 3x^2",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the derivative of x^4": {
        "text": "d/dx(x^4) = 4x^3",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the derivative of x^5": {
        "text": "d/dx(x^5) = 5x^4",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the derivative of x^n": {
        "text": "d/dx(x^n) = n * x^(n-1). This is the power rule.",
        "coherence": 0.99,
        "domain": "calculus"
    },
    "what is the determinant of a 2x2 matrix": {
        "text": "det([[a,b],[c,d]]) = ad - bc",
        "coherence": 0.97,
        "domain": "linear_algebra"
    },
    "what is the determinant of a 3x3 matrix": {
        "text": "det(A) = a(ei-fh) - b(di-fg) + c(dh-eg) for A = [[a,b,c],[d,e,f],[g,h,i]]",
        "coherence": 0.95,
        "domain": "linear_algebra"
    },
    "what is the difference between population and sample": {
        "text": "Population is the entire group. Sample is a subset. Use mu/sigma for population, x-bar/s for sample.",
        "coherence": 0.97,
        "domain": "statistics"
    },
    "what is the difference between validity and soundness": {
        "text": "A valid argument has correct logical form (conclusion follows from premises). A sound argument is valid AND has true premises. All sound arguments are valid, but not all valid arguments are sound.",
        "coherence": 0.97,
        "domain": "reasoning"
    },
    "what is the discriminant": {
        "text": "The discriminant is D = b^2 - 4ac.\nIf D > 0: two distinct real roots\nIf D = 0: one real double root\nIf D < 0: two complex conjugate roots",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is the distance between (0,0) and (3,4)": {
        "text": "Distance = √((3-0)^2 + (4-0)^2) = √(9+16) = √25 = 5.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the distance formula": {
        "text": "d = sqrt((x2-x1)^2 + (y2-y1)^2)",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the domain of f(x) = 1/(x-3)": {
        "text": "All real numbers except x = 3. Domain: (-inf, 3) U (3, inf)",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "what is the dot product": {
        "text": "u · v = u_1*v_1 + u_2*v_2 + ... + u_n*v_n",
        "coherence": 0.98,
        "domain": "linear_algebra"
    },
    "what is the empirical rule": {
        "text": "68-95-99.7 rule: In a normal distribution, 68% of data within 1 SD of mean, 95% within 2 SD, 99.7% within 3 SD.",
        "coherence": 0.96,
        "domain": "statistics"
    },
    "what is the equation of a circle with center (2,3) radius 4": {
        "text": "(x-2)^2 + (y-3)^2 = 16",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the equation of a line with slope 2 passing through (1,3)": {
        "text": "y - y1 = m(x - x1)\ny - 3 = 2(x - 1)\ny = 2x + 1",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the fibonacci sequence": {
        "text": "F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2). First terms: 0,1,1,2,3,5,8,13,21,34,55... The ratio F(n+1)/F(n) approaches φ.",
        "coherence": 0.98,
        "domain": "number_theory"
    },
    "what is the fundamental theorem of calculus": {
        "text": "FTC Part 1: If F(x) = ∫[a,x] f(t)dt, then F'(x) = f(x).\nFTC Part 2: ∫[a,b] f(x)dx = F(b) - F(a) where F' = f.",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the golden ratio": {
        "text": "The golden ratio φ = 1.618033988749895. It is defined by φ = (1+√5)/2. It appears in nature (phyllotaxis, spirals), art, architecture, and now in harmonic AI.",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is the heron's formula": {
        "text": "Heron's formula: Area = √(s(s-a)(s-b)(s-c)) where s = (a+b+c)/2 is the semiperimeter of a triangle with sides a,b,c.",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the identity matrix": {
        "text": "I_n is an n x n matrix with 1s on the diagonal and 0s elsewhere. AI = IA = A.",
        "coherence": 0.97,
        "domain": "linear_algebra"
    },
    "what is the imaginary part of 3-4i": {
        "text": "Im(3-4i) = -4",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is the integral of 1/x": {
        "text": "∫1/x dx = ln|x| + C",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the integral of cos(x)": {
        "text": "∫cos(x) dx = sin(x) + C",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the integral of e^x": {
        "text": "∫e^x dx = e^x + C",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the integral of sin(x)": {
        "text": "∫sin(x) dx = -cos(x) + C",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the integral of x^2": {
        "text": "∫x^2 dx = x^3/3 + C",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the integral of x^3": {
        "text": "∫x^3 dx = x^4/4 + C",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the interquartile range": {
        "text": "IQR = Q3 - Q1, the range of the middle 50% of data.",
        "coherence": 0.97,
        "domain": "statistics"
    },
    "what is the inverse of a matrix": {
        "text": "A^(-1) * A = A * A^(-1) = I. Only square matrices with non-zero determinant are invertible.",
        "coherence": 0.96,
        "domain": "linear_algebra"
    },
    "what is the inverse of f(x) = 2x + 1": {
        "text": "y = 2x + 1\nx = 2y + 1\n2y = x - 1\nf^(-1)(x) = (x-1)/2",
        "coherence": 0.94,
        "domain": "algebra"
    },
    "what is the inverse of f(x) = x^3": {
        "text": "f^(-1)(x) = cube root of x",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "what is the law of cosines": {
        "text": "Law of cosines: c^2 = a^2 + b^2 - 2ab cos(C).",
        "coherence": 0.98,
        "domain": "trigonometry"
    },
    "what is the law of excluded middle": {
        "text": "The law of excluded middle states that for any proposition P, either P is true or not-P is true. There is no third option.",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is the law of large numbers": {
        "text": "As the number of trials increases, the sample average converges to the expected value.",
        "coherence": 0.97,
        "domain": "statistics"
    },
    "what is the law of non-contradiction": {
        "text": "The law of non-contradiction states that a proposition P and its negation not-P cannot both be true at the same time.",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is the length of the hypotenuse of a 3-4-5 triangle": {
        "text": "By Pythagorean theorem: c = √(3^2 + 4^2) = √25 = 5.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is the limit of 1/x as x approaches infinity": {
        "text": "lim(x->inf) 1/x = 0",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the limit of sin(x)/x as x approaches 0": {
        "text": "lim(x->0) sin(x)/x = 1. This is a fundamental limit in calculus.",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the maclaurin series of cos(x)": {
        "text": "Maclaurin series of cos(x) = 1 - x^2/2! + x^4/4! - x^6/6! + ... = Σ (-1)^n * x^(2n)/(2n)!",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is the maclaurin series of e^x": {
        "text": "Maclaurin series of e^x = 1 + x + x^2/2! + x^3/3! + ... = Σ x^n/n!",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is the maclaurin series of sin(x)": {
        "text": "Maclaurin series of sin(x) = x - x^3/3! + x^5/5! - x^7/7! + ... = Σ (-1)^n * x^(2n+1)/(2n+1)!",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is the magnitude of a vector": {
        "text": "||v|| = sqrt(v_1^2 + v_2^2 + ... + v_n^2)",
        "coherence": 0.98,
        "domain": "linear_algebra"
    },
    "what is the mean of 2, 4, 6, 8": {
        "text": "Mean = (2+4+6+8)/4 = 20/4 = 5.",
        "coherence": 0.99,
        "domain": "statistics"
    },
    "what is the mean of numbers": {
        "text": "Mean = sum of all values / number of values",
        "coherence": 0.99,
        "domain": "statistics"
    },
    "what is the median": {
        "text": "Median is the middle value when data is ordered. If even number of values, median is average of two middle values.",
        "coherence": 0.98,
        "domain": "statistics"
    },
    "what is the median of 1, 3, 5, 7, 9": {
        "text": "Median = middle value = 5.",
        "coherence": 0.99,
        "domain": "statistics"
    },
    "what is the median of 2, 4, 6, 8": {
        "text": "Median = average of middle two = (4+6)/2 = 5.",
        "coherence": 0.99,
        "domain": "statistics"
    },
    "what is the midpoint formula": {
        "text": "Midpoint = ((x1+x2)/2, (y1+y2)/2)",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the midpoint of (2,4) and (6,8)": {
        "text": "Midpoint = ((2+6)/2, (4+8)/2) = (4, 6).",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the mode": {
        "text": "Mode is the value that appears most frequently in a dataset.",
        "coherence": 0.99,
        "domain": "statistics"
    },
    "what is the mode of 1, 2, 2, 3, 4": {
        "text": "Mode = 2 (appears most frequently — twice).",
        "coherence": 0.99,
        "domain": "statistics"
    },
    "what is the modulus of a complex number": {
        "text": "|a+bi| = sqrt(a^2 + b^2)",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is the next term in 1, 1, 2, 3, 5, 8": {
        "text": "13 (Fibonacci sequence)",
        "coherence": 0.97,
        "domain": "number_theory"
    },
    "what is the normal distribution": {
        "text": "The normal distribution N(μ,σ) has PDF f(x) = (1/(σ√(2π))) * e^(-(x-μ)^2/(2σ^2)). It is bell-shaped and symmetric about μ.",
        "coherence": 0.97,
        "domain": "statistics"
    },
    "what is the nth term of 3, 7, 11, 15": {
        "text": "a_n = 3 + (n-1)*4 = 4n - 1",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "what is the null hypothesis": {
        "text": "The null hypothesis (H0) is the default assumption that there is no effect or no difference. We test against it.",
        "coherence": 0.96,
        "domain": "statistics"
    },
    "what is the parallel postulate": {
        "text": "Through a point not on a given line, there is exactly one line parallel to the given line. (Euclidean geometry)",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the perimeter of a rectangle length l width w": {
        "text": "Perimeter = 2(l + w)",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the perimeter of a square with side 4": {
        "text": "Perimeter = 4 * side = 4 * 4 = 16 units.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the perimeter of a square with side s": {
        "text": "Perimeter = 4s",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the pigeonhole principle": {
        "text": "If n items are placed into m containers and n > m, then at least one container contains more than one item.",
        "coherence": 0.98,
        "domain": "reasoning"
    },
    "what is the point-slope form": {
        "text": "y - y1 = m(x - x1)",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the polar form of a complex number": {
        "text": "z = r(cos theta + i sin theta) = r e^(i theta), where r = |z|.",
        "coherence": 0.96,
        "domain": "algebra"
    },
    "what is the probability of drawing a face card": {
        "text": "P(face) = 12/52 = 3/13 = 23.1%. 12 face cards (J,Q,K of each suit).",
        "coherence": 0.97,
        "domain": "probability"
    },
    "what is the probability of drawing a heart from a deck": {
        "text": "P(heart) = 13/52 = 1/4 = 25%",
        "coherence": 0.98,
        "domain": "probability"
    },
    "what is the probability of drawing an ace from a deck of cards": {
        "text": "P(ace) = 4/52 = 1/13 ≈ 7.69%. There are 4 aces in a standard 52-card deck.",
        "coherence": 0.98,
        "domain": "probability"
    },
    "what is the probability of getting heads in one coin flip": {
        "text": "P(heads) = 1/2 = 0.5 = 50%",
        "coherence": 0.99,
        "domain": "probability"
    },
    "what is the probability of rolling a 3 on a six-sided die": {
        "text": "P(3) = 1/6 ≈ 0.167 = 16.7%",
        "coherence": 0.99,
        "domain": "probability"
    },
    "what is the probability of rolling a sum of 8 with two dice": {
        "text": "P(sum=8) = 5/36 ≈ 13.9%. Pairs: (2,6),(3,5),(4,4),(5,3),(6,2).",
        "coherence": 0.97,
        "domain": "probability"
    },
    "what is the probability of rolling an even number on a die": {
        "text": "P(even) = 3/6 = 1/2 = 0.5 = 50%. The even numbers are 2, 4, 6.",
        "coherence": 0.98,
        "domain": "probability"
    },
    "what is the probability of two heads in two coin flips": {
        "text": "P(HH) = (1/2) * (1/2) = 1/4 = 0.25 = 25%.",
        "coherence": 0.98,
        "domain": "probability"
    },
    "what is the product of roots of x^2 - 5x + 6 = 0": {
        "text": "For ax^2 + bx + c = 0, product of roots = c/a = 6/1 = 6.",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "what is the product rule": {
        "text": "Product rule: d/dx[f(x) * g(x)] = f'(x)g(x) + f(x)g'(x).",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the quadratic formula": {
        "text": "The quadratic formula: x = (-b ± √(b^2 - 4ac)) / 2a\nUsed to solve ax^2 + bx + c = 0.",
        "coherence": 0.99,
        "domain": "algebra"
    },
    "what is the quotient rule": {
        "text": "Quotient rule: d/dx[f(x)/g(x)] = (f'(x)g(x) - f(x)g'(x)) / g(x)^2.",
        "coherence": 0.98,
        "domain": "calculus"
    },
    "what is the range": {
        "text": "Range = maximum value - minimum value",
        "coherence": 0.99,
        "domain": "statistics"
    },
    "what is the range of 3, 7, 2, 9, 5": {
        "text": "Range = max - min = 9 - 2 = 7.",
        "coherence": 0.99,
        "domain": "statistics"
    },
    "what is the range of f(x) = x^2": {
        "text": "Range: [0, inf). All non-negative real numbers.",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "what is the rank of a matrix": {
        "text": "The rank is the maximum number of linearly independent rows or columns.",
        "coherence": 0.96,
        "domain": "linear_algebra"
    },
    "what is the real part of 2+5i": {
        "text": "Re(2+5i) = 2",
        "coherence": 0.98,
        "domain": "algebra"
    },
    "what is the second derivative of x^3": {
        "text": "f(x) = x^3, f'(x) = 3x^2, f''(x) = 6x.",
        "coherence": 0.97,
        "domain": "calculus"
    },
    "what is the slope formula": {
        "text": "m = (y2-y1)/(x2-x1)",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the slope of the line through (1,2) and (4,8)": {
        "text": "Slope = (y2-y1)/(x2-x1) = (8-2)/(4-1) = 6/3 = 2.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the slope-intercept form": {
        "text": "y = mx + b, where m is slope and b is y-intercept",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the square of 7": {
        "text": "7^2 = 49",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is the square root of 81": {
        "text": "√81 = 9",
        "coherence": 0.99,
        "domain": "arithmetic"
    },
    "what is the standard deviation of 1, 2, 3": {
        "text": "SD = √variance = √(2/3) ≈ 0.816.",
        "coherence": 0.96,
        "domain": "statistics"
    },
    "what is the sum of angles in a quadrilateral": {
        "text": "360 degrees",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the sum of angles in a triangle": {
        "text": "180 degrees",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is the sum of interior angles of a hexagon": {
        "text": "Sum = (n-2) * 180 = (6-2) * 180 = 720 degrees.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the sum of interior angles of a pentagon": {
        "text": "Sum = (n-2) * 180 = (5-2) * 180 = 540 degrees.",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the sum of roots of x^2 - 5x + 6 = 0": {
        "text": "For ax^2 + bx + c = 0, sum of roots = -b/a = -(-5)/1 = 5.",
        "coherence": 0.95,
        "domain": "algebra"
    },
    "what is the surface area of a cone": {
        "text": "SA = pi r^2 + pi r l (where l is slant height)",
        "coherence": 0.96,
        "domain": "geometry"
    },
    "what is the surface area of a cylinder": {
        "text": "SA = 2 pi r^2 + 2 pi r h (2 bases + lateral)",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the surface area of a sphere": {
        "text": "SA = 4 pi r^2",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the surface area of a sphere with radius 1": {
        "text": "Surface area = 4πr^2 = 4π ≈ 12.566 square units.",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the transitive property": {
        "text": "If A = B and B = C, then A = C. (Equality is transitive.)\nIf A > B and B > C, then A > C. (Inequality is transitive.)",
        "coherence": 0.99,
        "domain": "reasoning"
    },
    "what is the transpose of a matrix": {
        "text": "(A^T)_{ij} = A_{ji}. Rows become columns and vice versa.",
        "coherence": 0.97,
        "domain": "linear_algebra"
    },
    "what is the variance of 1, 2, 3": {
        "text": "Mean = 2. Deviations: -1,0,1. Squared: 1,0,1. Variance = (1+0+1)/3 ≈ 0.667.",
        "coherence": 0.96,
        "domain": "statistics"
    },
    "what is the vertex of y = x^2 - 4x + 3": {
        "text": "Vertex: x = -b/(2a) = 4/2 = 2. y = 2^2 - 4(2) + 3 = 4 - 8 + 3 = -1.\nVertex: (2, -1)",
        "coherence": 0.94,
        "domain": "algebra"
    },
    "what is the volume of a cone": {
        "text": "V = (1/3) pi r^2 h",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the volume of a cone radius 3 height 4": {
        "text": "Volume = (1/3)πr^2h = (1/3)π * 9 * 4 = 12π ≈ 37.70 cubic units.",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the volume of a cube with side 3": {
        "text": "Volume = side^3 = 27 cubic units.",
        "coherence": 0.99,
        "domain": "geometry"
    },
    "what is the volume of a cylinder": {
        "text": "V = pi r^2 h",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the volume of a cylinder radius 2 height 5": {
        "text": "Volume = πr^2h = π * 4 * 5 = 20π ≈ 62.83 cubic units.",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the volume of a pyramid": {
        "text": "V = (1/3) * base_area * height",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is the volume of a rectangular prism": {
        "text": "V = l * w * h",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the volume of a sphere": {
        "text": "V = (4/3) pi r^3",
        "coherence": 0.98,
        "domain": "geometry"
    },
    "what is the volume of a sphere with radius 1": {
        "text": "Volume = (4/3)πr^3 = (4/3)π ≈ 4.189 cubic units.",
        "coherence": 0.97,
        "domain": "geometry"
    },
    "what is variance": {
        "text": "Variance = average of squared deviations from the mean. Var = (1/n) * sum((x_i - mean)^2)",
        "coherence": 0.96,
        "domain": "statistics"
    },
}

PRE_COMPUTED_NORMALIZED = {k.lower().strip(): v for k, v in PRE_COMPUTED.items()}
