import math

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)

print("=" * 60)
print("VERIFICATION DES CONSTANTES HARMONIQUES")
print("=" * 60)

# --- Constante de structure fine alpha ---
print("\n1) CONSTANTE DE STRUCTURE FINE (alpha)")
alpha_harm = pi**4 * e**-4 * phi**-5 * sqrt2**-1 * sqrt3**-5
alpha_codata = 1 / 137.035999084
print(f"   Formule   : pi^4 * e^-4 * phi^-5 * sq2^-1 * sq3^-5")
print(f"   1/alpha harm   = {1/alpha_harm:.10f}")
print(f"   1/alpha CODATA = {1/alpha_codata:.10f}")
print(f"   Erreur rel.    = {abs(alpha_harm - alpha_codata)/alpha_codata * 100:.8f} %  <- EXCELLENT")

# --- Constante de Planck h ---
print("\n2) CONSTANTE DE PLANCK h")
print("   Formule proposee : phi^-23 * pi^-9 * e^-18")
phi_part = phi**-23
pi_part = pi**-9
e_part = e**-18
h_harm = phi_part * pi_part * e_part
h_codata = 6.62607015e-34

print(f"   phi^-23     = {phi_part:.6e}")
print(f"   pi^-9       = {pi_part:.6e}")
print(f"   e^-18       = {e_part:.6e}")
print(f"   PRODUIT     = {h_harm:.6e}")
print(f"   h CODATA    = {h_codata:.6e}")
print(f"   Ecart       = {abs(h_harm - h_codata):.2e}")
print(f"   Ratio harm/CODATA = {h_harm / h_codata:.6e}")
print(f"   -> Ecart de {math.log10(h_harm/h_codata):.1f} ordres de grandeur !")

# Recherche d'un facteur manquant
missing_factor = h_codata / h_harm
print(f"\n   Facteur manquant pour obtenir h : {missing_factor:.6e}")

print("\n" + "=" * 60)
print("RESUME")
print("=" * 60)
print(f"  alpha harmonique  : ERREUR = {abs(alpha_harm - alpha_codata)/alpha_codata * 100:.6f} %  <- VALIDE")
print(f"  h harmonique      : ERREUR = {abs(h_harm - h_codata)/h_codata * 100:.2e} %  <- NON VALIDE")
print(f"  -> La formule phi^-23 * pi^-9 * e^-18 ne donne PAS h.")
print(f"  -> Il manque un facteur ~{missing_factor:.2e}")
print(f"  -> h est dimensionnee (J.s), pas un nombre pur comme alpha.")
print(f"  -> Il faut probablement inclure c, G, ou l'echelle de Planck.")