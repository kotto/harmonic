import numpy as np
phi = (1 + np.sqrt(5)) / 2

print("=== Probleme 3 : S/D = 1/phi (cardiologie, depot E6, 0.8%) ===")
print()

# E6 : rapport diastolique/systolique = 1/phi
# Donc S/D = phi pour une tension optimale
# Ex : 130/80 donne 80/130 = 0.615 = 1/phi - 0.5%
# Ex : 120/74 donne 74/120 = 0.617 = 1/phi - 0.2%

# Physique : onde de pression dans un tube elastique
# Le rapport d'onde stationnaire (SWR) = (1 + |Gamma|)/(1 - |Gamma|)
# Si S/D = phi, alors SWR = phi, donc :
# phi = (1 + |Gamma|) / (1 - |Gamma|)
# => |Gamma| = (phi - 1)/(phi + 1) = (1/phi)/(phi**2) = 1/phi**3

phi_inv_3 = 1.0 / phi**3
print("=== Reflection coefficient (coefficient de reflexion) ===")
print(f"|Gamma| = 1/phi**3 = {phi_inv_3:.6f}")
print()

# Impedance ratio : Z2/Z1 = (1 + |Gamma|)/(1 - |Gamma|)
Z_ratio = (1 + phi_inv_3) / (1 - phi_inv_3)
print(f"Rapport d'impedance Z2/Z1 = (1+|Gamma|)/(1-|Gamma|) = {Z_ratio:.6f}")
print(f"phi = {phi:.6f}")
print(f"Difference = {abs(Z_ratio - phi):.6e}")
print()

# Murray's law : r_p**3 = r_d1**3 + r_d2**3
# Pour bifurcation symetrique : r_d = r_p / 2**(1/3) = r_p / 1.260
# Notre prediction : rapport d'impedance = phi
# En supposant Z ~ 1/r**2 (loi de Poiseuille) :
# Z2/Z1 = (r1/r2)**2 = phi => r1/r2 = sqrt(phi) = 1.272
# Comparaison avec Murray : 2**(1/3) = 1.260
r_murray = 2**(1/3)
r_phi = np.sqrt(phi)
print("=== Comparaison avec la loi de Murray ===")
print(f"Murray (loi de Poiseuille)  : r_parent/r_daughter = 2^(1/3) = {r_murray:.4f}")
print(f"Prediction harmonique        : r_parent/r_daughter = sqrt(phi) = {r_phi:.4f}")
print(f"Ecart = {abs(r_phi - r_murray):.4f} ({abs(r_phi/r_murray - 1)*100:.2f}%)")
print()

# Verification : loi de Murray optimale = 1.26, notre prediction = 1.272
# Soit 0.95% d'ecart -- remarquablement proche !
# Murray minimise l'energie de pompage
# La prediction harmonique donne une valeur quasi-identique
# Mais avec une signification physique supplementaire : 
# le rapport des rayons suit sqrt(phi) = sqrt(1.618) = 1.272

print("=== Prediction E6bis (reverse transvertality) ===")
print("  Le coefficient de reflexion aux bifurcations arterielles")
print("  est |Gamma| = 1/phi^3 = 0.236")
print("  Le rapport d'impedance caracteristique Z_d/Z_p = phi")
print("  Le rapport des rayons r_p/r_d = sqrt(phi) = 1.272")
print("  (a comparer a la loi de Murray : 2^(1/3) = 1.260)")
print()
print("  Test : echodoppler pulsatile aux bifurcations")
print("    (aorte-iliaque, carotide-externe/interne)")
print("    Mesure du rapport des impedances a chaque bifurcation")
print("    A bifurcation saine, Z_d/Z_p = phi ± 0.02")
print("    En pathologie (hypertension, stenose), le rapport s'ecarte de phi")