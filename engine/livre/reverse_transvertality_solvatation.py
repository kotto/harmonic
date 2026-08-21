import numpy as np
from math import gamma

phi = (1 + np.sqrt(5)) / 2

# Coefficients harmoniques T3 : c_k = 1/Gamma(k/phi+1)
def c_k(k):
    return 1.0 / gamma(k/phi + 1)

print("=== Serie harmonique T3 : c_k = 1/Gamma(k/phi+1) ===")
print()
for k in range(20):
    print(f"  c_{k:2d} = {c_k(k):.6f}")
print()

# Kyte-Doolittle hydrophobicity scale (1982)
# Plus le score est eleve, plus l'acide amine est hydrophobe
# Ordonnes du plus hydrophobe (k_candidate=0) au moins hydrophobe (k_candidate=19)
aa_order = [
    ("Ile", 4.5), ("Val", 4.2), ("Leu", 3.8), ("Phe", 2.8),
    ("Cys", 2.5), ("Met", 1.9), ("Ala", 1.8),
    ("Gly", -0.4), ("Thr", -0.7), ("Ser", -0.8), ("Trp", -0.9),
    ("Tyr", -1.3), ("Pro", -1.6),
    ("His", -3.2), ("Glu", -3.5), ("Gln", -3.5), ("Asp", -3.5),
    ("Asn", -3.5), ("Lys", -3.9), ("Arg", -4.5)
]

print("=== Acides amines classes par hydrophobie (Kyte-Doolittle) ===")
print()

# Normaliser les scores entre 0 et 1
scores = np.array([s for _, s in aa_order])
scores_norm = (scores - scores.min()) / (scores.max() - scores.min())

# Coefficients harmoniques pour k=0..19
harmoniques = np.array([c_k(k) for k in range(20)])

# Tracer la comparaison
print("  k  AA       Score   Norme    c_k     Ecart")
print("  -- -------- ------- ------- ------- -------")
for k, (aa, score) in enumerate(aa_order):
    norm = scores_norm[k]
    print(f"  {k:2d}  {aa:8s} {score:7.1f} {norm:7.4f} {harmoniques[k]:7.4f} {abs(norm-harmoniques[k]):7.4f}")

# Correlation lineaire simple : scores_norm vs harmoniques
corr = np.corrcoef(scores_norm, harmoniques)[0,1]
print()
print(f"Correlation scores_norm vs c_k = {corr:.4f}")

# Ajustement lineaire : scores_norm = a * c_k + b
A = np.vstack([harmoniques, np.ones_like(harmoniques)]).T
a, b = np.linalg.lstsq(A, scores_norm, rcond=None)[0]
print(f"Ajustement lineaire : pred = {a:.4f} * c_k + {b:.4f}")

# Erreur quadratique moyenne
pred = a * harmoniques + b
rmse = np.sqrt(np.mean((scores_norm - pred)**2))
print(f"RMSE = {rmse:.4f}")

# Voir combien de points tombent dans l'intervalle +/- 2*RMSE (95%)
dans_intervalle = sum(abs(scores_norm - pred) < 2*rmse)
print(f"Points dans intervalle +/-2*RMSE : {dans_intervalle}/20")

print()
print("=== HarmoFold : energie de contact = resonance entre spectres harmoniques ===")
print()
print("Dans HarmoFold, chaque paire d'acides amines voisins")
print("a une energie de contact E_ij = -resonance(psi_i, psi_j)")
print("ou psi_i = ENCODE(aa_i) dans le langage ondulatoire")
print()
print("La solvatation (interaction avec l'eau) s'ajoute comme :")
print("  E_solv = lambda * H(k)  ou H(k) suit c_k")
print("  lambda = (1/phi) * (k_B * T) = (1/phi) * 12.86 meV")
print("  = 0.618 * 12.86 = 7.95 meV par unite d'hydrophobie")
print()

# Verification du scalaire
lambda_pred = (1/phi) * 12.86  # meV
print(f"lambda_pred = (1/phi) * 12.86 meV = {lambda_pred:.3f} meV")
print()
print("Prediction : la pente a de l'ajustement lineaire")
print("entre hydrophobie normalisee et c_k doit etre")
print("compatible avec le rapport (1/phi) determine par T*")
print()

# Exporter les donnees pour HarmoFold
print("=== Donnees pour integration dans HarmoFold ===")
for k, (aa, score) in enumerate(aa_order):
    print(f"  {aa}: k={k}, c_k={harmoniques[k]:.6f}, KD_score={score:.1f}")