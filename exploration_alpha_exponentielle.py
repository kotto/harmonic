import math

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)

alpha_exp = 1 / 137.035999084

print("=" * 70)
print("EXPLORATION: VARIANTES EXPONENTIELLES POUR alpha")
print("=" * 70)

print("\nFormule proposee: alpha = 2*pi*phi * exp(-pi*(sqrt3 - sqrt2/sqrt5))")
alpha_test = 2 * pi * phi * math.exp(-pi * (sqrt3 - sqrt2 / sqrt5))
print(f"  -> alpha = {alpha_test:.4f}  (1/alpha = {1/alpha_test:.2f})")
print(f"  -> Erreur = {abs(alpha_test - alpha_exp)/alpha_exp*100:.2f}%")
print(f"  -> COMPLETEMENT FAUX (facteur 44)")

# What X would give the right answer?
# alpha_exp = 2*pi*phi * exp(-pi*X)
# X = -ln(alpha_exp/(2*pi*phi)) / pi
X_target = -math.log(alpha_exp / (2 * pi * phi)) / pi
print(f"\nPour que alpha = alpha_exp, il faut X = {X_target:.6f}")
print(f"  sqrt3 - sqrt2/sqrt5 = {sqrt3 - sqrt2/sqrt5:.10f}  (trop petit, facteur ~4)")

print(f"\nL'exposant doit etre environ pi*{X_target:.4f}")
print(f"Combinaisons possibles pour atteindre ~{X_target:.4f}:")

# Test various combos
combos = [
    ("sqrt3 + sqrt5", sqrt3 + sqrt5, "+"),
    ("sqrt3 * sqrt5 / sqrt2", sqrt3 * sqrt5 / sqrt2, "+"),
    ("pi * sqrt3 / phi", pi * sqrt3 / phi, ""),
    ("pi * phi / sqrt2", pi * phi / sqrt2, ""),
    ("pi * sqrt5 / e", pi * sqrt5 / e, ""),
    ("phi * pi", phi * pi, ""),
    ("e * pi / phi", e * pi / phi, ""),
    ("pi * sqrt2", pi * sqrt2, ""),
    ("sqrt3 * pi / sqrt2", sqrt3 * pi / sqrt2, ""),
    ("phi * sqrt3 * sqrt2", phi * sqrt3 * sqrt2, ""),
    ("e * sqrt5", e * sqrt5, ""),
    ("4 * sqrt3", 4 * sqrt3, ""),
    ("5 * sqrt2", 5 * sqrt2, ""),
    ("3 * phi", 3 * phi, ""),
    ("pi * sqrt3", pi * sqrt3, ""),
    ("(sqrt3 - sqrt2/sqrt5) * 4", (sqrt3 - sqrt2/sqrt5) * 4, "+"),
    ("(sqrt3 - sqrt2/sqrt5) * pi", (sqrt3 - sqrt2/sqrt5) * pi, "+"),
]

print(f"\nTests (X cible = {X_target:.6f}):")
for name, val, flag in combos:
    alpha_val = 2 * pi * phi * math.exp(-pi * val)
    err = abs(alpha_val - alpha_exp) / alpha_exp * 100
    marker = " <--" if err < 5 else ""
    print(f"  X={name:35s} ={val:10.6f}  -> 1/alpha={1/alpha_val:9.4f}  err={err:6.2f}%{marker}")

print(f"\n--- Peut-etre la formule est-elle: 1/alpha = 2*pi*phi * exp(+pi*X) ? ---")
for name, val, flag in combos:
    inv_alpha = 2 * pi * phi * math.exp(pi * val)
    alpha_val = 1 / inv_alpha
    err = abs(alpha_val - alpha_exp) / alpha_exp * 100
    marker = " <--" if err < 5 else ""
    print(f"  X={name:35s} ={val:10.6f}  -> 1/alpha={inv_alpha:9.4f}  err={err:6.2f}%{marker}")

# Check if sqrt3 - sqrt2/sqrt5 appears in another context
print(f"\n--- Autres observations ---")
print(f"  sqrt3 - sqrt2/sqrt5 = {sqrt3 - sqrt2/sqrt5:.10f}")
print(f"  1/(sqrt3 - sqrt2/sqrt5) = {1/(sqrt3 - sqrt2/sqrt5):.10f}")
print(f"  C'est proche de 1/phi ? 1/phi = {1/phi:.10f}  (non)")
print(f"  C'est proche de ln(phi) ? ln(phi) = {math.log(phi):.10f}  (non)")
print(f"  C'est proche de pi/e ? pi/e = {pi/e:.10f}  (non)")
print(f"  C'est proche de ln(3) ? ln(3) = {math.log(3):.10f}  (oui! err={(abs(math.log(3)-(sqrt3-sqrt2/sqrt5))/(sqrt3-sqrt2/sqrt5)*100):.4f}%)")

print(f"\n=== CONCLUSION ===")
print(f"La formule alpha = 2*pi*phi * exp(-pi*(sqrt3 - sqrt2/sqrt5))")
print(f"donne alpha = 0.321 (1/alpha = 3.11), erreur de 4300%.")
print(f"C'est completement faux pour alpha.")
print(f"La formule correcte restante est: alpha = pi^4 * e^-4 * phi^-5 * sqrt2^-1 * sqrt3^-5")
print(f"avec une erreur de 0.000024%.")