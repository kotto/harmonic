#!/usr/bin/env python3
"""alpha_self_energy.py — SELF-ÉNERGIE DU PHOTON FRACTIONNAIRE → α"""
import math,os,time,json,numpy as np
PHI=(1+math.sqrt(5))/2;A=1/PHI;PI=math.pi

# ═══════════════════════════════════════════════════════════════════
# SELF-ÉNERGIE DU PHOTON À 1 BOUCLE AVEC PROPAGATEUR FRACTIONNAIRE
# ═══════════════════════════════════════════════════════════════════
# Standard QED : β₀ = 2/3 (1 boucle, 1 fermion)
# La self-énergie Σ(p) implique l'intégrale du propagateur photonique :
#   ∫ d⁴k / (k² · ((p−k)² − m²))
# Avec D^{1/φ} : le propagateur photonique est 1/(k₀^{1/φ} + k⃗²)
# → l'intégrale temporelle ∫ dk₀ / k₀^{1/φ} donne un facteur modifié.

# Facteur de modification de la self-énergie :
# F(α) = (1/α) · ∫₀^∞ dx / x^{1/α} · (terme angulaire)
# Pour α=1 (standard) : F(1) = 1
# Pour α=1/φ : F(1/φ) = ?

def facteur_modification(alpha,N=10000):
    """Calcule l'intégrale fractionnaire modifiant la self-énergie.
    ∫₀^∞ dω / (ω^{1/α} + 1) vs ∫₀^∞ dω / (ω² + 1) = π/2."""
    # Standard : ∫ dω/(ω²+1) = π/2
    # Fractionnaire : ∫ dω/(ω^{1/α}+1) 
    # Pour α=1 : ∫ dω/(ω²+1) = π/2
    # Pour α<1 : intégrale plus grande → self-énergie plus grande → α plus petit
    # Calcul numérique de l'intégrale adimensionnée
    I_std = PI/2  # ∫₀^∞ dx/(x²+1)
    w = np.linspace(0, 50, N)
    dw = w[1]-w[0]
    I_frac = np.sum(dw/(w**(1/alpha)+1))
    return I_frac/I_std  # rapport au standard

# Pour différents α
print("="*65)
print("SELF-ÉNERGIE DU PHOTON FRACTIONNAIRE → α")
print("="*65)
print(f"\n─ FACTEUR DE MODIFICATION DE LA SELF-ÉNERGIE:")
for a in [0.3,0.5,A,0.7,0.9,1.0]:
    F=facteur_modification(a)
    nom=f"1/φ" if abs(a-A)<1e-6 else f"{a:.2f}"
    print(f"  α={nom:5s} : F(α) = {F:.4f}")

# Le coefficient de la fonction beta est modifié : β_THU = β_std / F(1/φ)
F_thu=facteur_modification(A)
beta_thu=(2.0/3.0)/F_thu
print(f"\n─ FONCTION BETA MODIFIÉE:")
print(f"  β_std = 2/3 = 0.6667")
print(f"  F(1/φ) = {F_thu:.4f}")
print(f"  β_THU = β_std / F(1/φ) = {beta_thu:.4f}")

# Running de α avec la fonction beta modifiée
M_P=1.22e19;m_e=0.511e-3
logR=math.log(M_P/m_e)
alpha_inv_mp=25.0  # hypothèse : α(M_P) ~ O(1)
alpha_inv_me_std=alpha_inv_mp + (2.0/3.0)*logR/(2*PI)
alpha_inv_me_thu=alpha_inv_mp + beta_thu*logR/(2*PI)
alpha_obs=137.036

print(f"\n─ RUNNING DE α (M_P → m_e) :")
print(f"  α⁻¹(m_e) standard = {alpha_inv_me_std:.1f} (1/{1/alpha_inv_me_std:.0f})")
print(f"  α⁻¹(m_e) THU      = {alpha_inv_me_thu:.1f} (1/{1/alpha_inv_me_thu:.0f})")
print(f"  α⁻¹(m_e) CODATA   = 137.0")
ecart=abs(alpha_inv_me_thu-alpha_obs)/alpha_obs*100
print(f"  Écart THU/CODATA   = {ecart:.1f}%")

print(f"\n─ VERDICT")
signal=ecart<15
print(f"  {'✅' if signal else '❌'} Le propagateur fractionnaire modifie β d'un facteur {F_thu:.2f}.")
print(f"  → α⁻¹(m_e) THU ≈ {alpha_inv_me_thu:.0f} vs 137 (écart {ecart:.0f}%).")
if signal:print(f"  → La self-énergie fractionnaire EXPLIQUE l'ordre de grandeur de α.")
else:print(f"  → L'ordre de grandeur est proche mais α(M_P) est encore un paramètre libre.")
print(f"  → Le calcul COMPLET (2 boucles, vertex, Ward) est le programme.")

dep={"F_thu":F_thu,"beta_thu":beta_thu,"alpha_inv_thu":alpha_inv_me_thu,
     "ecart_pct":ecart,"statut":"EXPLORÉ · calcul complet à faire",
     "date":time.strftime("%Y-%m-%d %H:%M:%S")}
p=os.path.join("data","benchmarks","alpha_self_energy_report.json")
os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)
print(f"Rapport : {p}")
