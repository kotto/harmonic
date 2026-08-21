import numpy as np

phi = (1 + np.sqrt(5)) / 2
kB_eV = 8.617333262e-5
delta_E = 0.012861  # meV -> eV

print("=== Connexion A : Eau x Cerveau ===")
print("Prediction : beta/alpha(T) = phi * exp(-delta_E/kB * (1/T - 1/T*))")
print()

T_star = 273.15 + 37.0  # 310.15 K
T_range = [306.15, 308.15, 310.15, 312.15, 314.15]

print("  T(C)  T(K)     1/T-1/T*        exp(-X)    beta/alpha  ecart a phi")
print("  ----  ------   ------------    -------    ----------  -----------")
for T_K in T_range:
    T_C = T_K - 273.15
    diff = 1/T_K - 1/T_star
    exponent = delta_E / kB_eV * diff
    factor = np.exp(-exponent)
    ratio = phi * factor
    ecart = (ratio/phi - 1) * 100
    print(f"  {T_C:3.0f}   {T_K:.2f}   {diff:+.8e}   {factor:.6f}   {ratio:.6f}   {ecart:+.3f}%")

print()
print(f"Delta_E = {delta_E*1000:.3f} meV (gap LDL/HDL de l'eau)")
print(f"T*       = {T_star:.2f} K = 37.0 C")
print()

# Valeurs pour protocole
print("=== Protocole de test ===")
print("  1. Enregistrer EEG (64 canaux) a 37C (temoins)")
print("  2. Enregistrer EEG en hypothermie therapeutique (33C)")
print("  3. Enregistrer EEG en fievre (39C)")
print("  4. Mesurer beta/alpha sur canaux P3, Pz, O1 (memes que depot E5)")
print("  5. Comparer a la prediction : ratio = phi * exp(-delta_E/kB * (1/T - 1/T*))")
print()
print("  6. Si les points tombent sur la courbe -> connexion EauxCerveau etablie")
print("  7. Si la courbe ne colle pas -> la connexion est infirmee")
print()

# Calcul : prediction pour 33C
T33 = 273.15 + 33
diff33 = 1/T33 - 1/T_star
exp33 = delta_E/kB_eV * diff33
ratio33 = phi * np.exp(-exp33)
print(f"Prediction a 33C : beta/alpha = {ratio33:.4f} (ecart {(ratio33/phi-1)*100:+.3f}%)")
print(f"vs phi exact : {phi:.6f}")
print(f"Difference mesurable : oui (precision E5 = 0.06%)")

# Test de l'hypothese : le gap 12.86 meV est-il le bon ?
# Si on laisse delta_E libre, on peut verifier qu'il vaut exactement 12.86 meV
print()
print("=== Test d'identite du gap ===")
print("Si les mesures donnent beta/alpha a differentes temperatures,")
print("on peut extraire delta_E experimentalement :")
print("  delta_E_exp = kB * ln(phi/ratio) / (1/T - 1/T*)")
print("Si delta_E_exp = 12.86 meV -> confirmation du gap LDL/HDL")
print("Si delta_E_exp differe -> autre mecanisme")