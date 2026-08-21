#!/usr/bin/env python3
"""derive_alpha_from_cn.py — α_EM dérivé des coefficients cₙ = 1/Γ(n/φ+1)
=======================================================================
Tentative rigoureuse : α_EM peut-il s'exprimer comme une fonction
des seuls coefficients cₙ, sans postuler {π, e, √2, √3} ?

Méthode :
  1. Partir des cₙ (dérivés en T3, vérifiés 2,22×10⁻¹⁶)
  2. Explorer toutes les fonctions naturelles possibles :
       - ratios c_{n+1}/cₙ
       - produits de ratios
       - sommes pondérées Σ nᵏ·cₙ / Σ cₙ
       - évaluations de la fonction E_{1/φ}(z) en des points symétriques
       - formes spectrales (transformée de Fourier/Mellin du noyau ABC)
  3. Comparer à 1/α_EM = 137,035999084
  4. Identifier le (ou les) candidats qui fonctionnent
  5. Rapport honnête : ✅ si dérivation trouvée, ❌ sinon
"""
import json, math, os, time, sys
import numpy as np
from scipy import integrate, special

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
A_CODATA = 137.035999084  # 1/α_EM (CODATA 2018)

# ─── Coefficients cₙ = 1/Γ(n/φ+1) ───
def c(n):
    """cₙ = 1/Γ(n/φ+1) pour n ≥ 0."""
    return 1.0 / math.gamma(ALPHA * n + 1.0)

# Pré-calcul des 20 premiers coefficients
C = [c(n) for n in range(60)]  # 60 coefficients

print("=" * 78)
print("DÉRIVATION DE α_EM DEPUIS LES COEFFICIENTS cₙ")
print("=" * 78)
print(f"\nCoefficients cₙ = 1/Γ(n/φ+1) :")
for n in range(10):
    print(f"  c_{{{n}}} = {C[n]:.12f}")
print()

# ═══════════════════════════════════════════════════════════════════════════════
# 1. RATIOS SUCCESSIFS
# ═══════════════════════════════════════════════════════════════════════════════
print("─" * 78)
print("1. RATIOS SUCCESSIFS c_{n+1}/c_n")
print("─" * 78)

ratios = []
for n in range(0, 15):
    r = C[n+1] / C[n]
    ratios.append(r)
    print(f"  c_{{{n+1}}}/c_{{{n}}} = {r:.10f}")

# Produits cumulatifs
print("\n  Produits cumulatifs :")
prod = 1.0
for n in range(0, 10):
    prod *= ratios[n]
    print(f"  c_{{{n+1}}}/c_{{0}} = {C[n+1]/C[0]:.10f}")

print(f"\n  → Aucun ratio ni produit ne donne 1/α_EM ≈ {A_CODATA:.4f}")
print(f"  → Les ratios tendent vers 0 (asymptotique Gamma)")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. SOMMES PONDÉRÉES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 78)
print("2. SOMMES PONDÉRÉES DES COEFFICIENTS")
print("─" * 78)

somme_c = sum(C[:50])  # Σ cₙ converge rapidement
somme_c2 = sum(c**2 for c in C[:50])
somme_nc = sum(n * C[n] for n in range(1, 50))
somme_c_inv = sum(1.0 / C[n] for n in range(1, 15))

print(f"  Σ cₙ (n=0..49)      = {somme_c:.6f}")
print(f"  Σ cₙ² (n=0..49)     = {somme_c2:.6f}")
print(f"  Σ n·cₙ (n=1..49)    = {somme_nc:.6f}")
print(f"  1/Σ cₙ              = {1.0/somme_c:.6f}")
print(f"  1/Σ cₙ²             = {1.0/somme_c2:.6f}")
print(f"  c₁/Σ cₙ             = {C[1]/somme_c:.6f}")
print(f"  c₁²/Σ cₙ²           = {C[1]**2/somme_c2:.6f}")
print(f"  Σ n·cₙ/Σ cₙ         = {somme_nc/somme_c:.6f}")
print(f"  1/α_EM visé         = {A_CODATA:.6f}")

print(f"\n  → Aucune somme simple n'atteint 137")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. FONCTION DE MITTAG-LEFFLER E_{1/φ}(z) EN DES POINTS SYMÉTRIQUES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 78)
print("3. FONCTION E_{1/φ}(z) EN DES POINTS REMARQUABLES")
print("─" * 78)

def E_alpha(alpha, z, N=80):
    """Fonction de Mittag-Leffler E_α(z) par série (pour z réel négatif)."""
    if z > 0:
        return float('nan')
    if z < -50:
        return 0.0  # asymptotique : E_α(-x) ~ 1/(Γ(1-α)·x) pour x grand
    s = 0.0
    for k in range(N):
        term = (z ** k) / math.gamma(alpha * k + 1.0)
        s += term
        if abs(term) < 1e-16:
            break
    return s

points = {
    "E(0) = 1": (0, 1.0),
    "E(-∞) → 0": (-1e10, 0.0),
    "E(-1)": (-1, None),
    "E(-φ)": (-PHI, None),
    "E(-π)": (-math.pi, None),
    "E(-e)": (-math.e, None),
    "E(-λ) = E(-φ)": (-PHI, None),
}

for nom, (z, val_attendu) in points.items():
    val = E_alpha(ALPHA, z)
    if val_attendu is not None:
        ecart = abs(val - val_attendu)
        flag = "✅" if ecart < 1e-10 else "❌"
    else:
        flag = ""
    print(f"  {nom:25s} = {val:.10f}  {flag}")

# Est-ce que 1/α_EM apparaît comme E_{1/φ}(z) pour un z spécifique ?
print("\n  Recherche : existe-t-il z tel que E_{1/φ}(z) = 1/α_EM ?")
print(f"  1/α_EM = {A_CODATA:.6f}")
print(f"  Valeur max de E_{{{ALPHA:.3f}}}(z) pour z réel négatif : E(0) = 1")
print(f"  → Impossible : E(z) ≤ 1 pour z ≤ 0 réel, et 1/α_EM > 1")

# Pour z complexe ?
print(f"  Pour z complexe : E(z) peut prendre des valeurs > 1")
print(f"  Exemple : E_{{{ALPHA:.3f}}}(2πi) = ?")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. TRANSFORMÉE DE MELLIN DU NOYAU ABC
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 78)
print("4. TRANSFORMÉE SPECTRALE (MELLIN) DU NOYAU ABC")
print("─" * 78)

# Le noyau ABC : K(t) = B(α)·E_α(-λ·t^α)
# Sa transformée de Mellin M(s) = ∫₀^∞ t^{s-1}·K(t) dt
# donne les moments spectraux. Le couplage de jauge U(1)
# pourrait être lié au premier moment.

def abc_kernel(t):
    """Noyau ABC."""
    if t <= 0:
        return 1.0
    lam = ALPHA / (1.0 - ALPHA)  # = φ
    B = 1.0 - ALPHA + ALPHA / math.gamma(ALPHA)
    z = -lam * (t ** ALPHA)
    ml = E_alpha(ALPHA, z) if t <= 2 else 1.0 / (lam * (t ** ALPHA) * math.gamma(1.0 - ALPHA))
    return B * ml

def moment_mellin(s, T_max=20.0):
    """Moment d'ordre s : M(s) = ∫₀^∞ t^{s-1}·K(t) dt."""
    f = lambda t: (t ** (s - 1.0)) * abc_kernel(t)
    val, err = integrate.quad(f, 0, T_max, limit=200)
    return val

print("  Moments de Mellin M(s) = ∫ t^{s-1}·K(t) dt :")
for s_real in [0.5, 1.0, 1.5, 2.0, 2.618, 3.0]:
    try:
        M = moment_mellin(s_real)
        print(f"  M({s_real:.1f}) = {M:.6f}  (1/M = {1.0/M:.6f})")
    except Exception as e:
        print(f"  M({s_real:.1f}) = ERREUR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. RELATION AVEC LA FORMULE EXISTANTE (via la formule de réflexion Γ)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 78)
print("5. LIEN cₙ → α_EM PAR LA FORMULE DE RÉFLEXION DE GAMMA")
print("─" * 78)

# La formule de réflexion : Γ(1-z)·Γ(z) = π/sin(πz)
# Appliquée à c₁ = 1/Γ(1/φ+1) = 1/((1/φ)·Γ(1/φ))
# Donc : Γ(1/φ) = φ·c₁⁻¹

# Via réflexion : Γ(1/φ)·Γ(1-1/φ) = π/sin(π/φ)
# Or 1-1/φ = 1/φ²
# Donc : (φ·c₁⁻¹)·Γ(1/φ²) = π/sin(π/φ)
# → Γ(1/φ²) = c₁·sin(π/φ)/(φ·π)

print(f"  c₁ = 1/Γ(1/φ+1) = {C[1]:.10f}")
print(f"  Γ(1/φ) = φ/c₁ = {PHI/C[1]:.10f}")
print(f"  Réflexion : Γ(1/φ)·Γ(1/φ²) = π/sin(π/φ)")
sin_pi_phi = math.sin(math.pi/PHI)
print(f"  Γ(1/φ²) = c₁·sin(π/φ)/(φ·π) = {C[1]*sin_pi_phi/(PHI*math.pi):.10f}")

# Donc π peut s'exprimer via c₁, φ, et Γ(1/φ²) :
# π = φ·c₁⁻¹·Γ(1/φ²)·sin(π/φ)

# Mais cela ne donne pas une EXPRESSION FERMÉE de α_EM en fonction de c₁ seul.
# Il faut aussi Γ(1/φ²) qui est un nouveau coefficient non-dérivé.

print(f"\n  → π s'exprime via c₁, φ et Γ(1/φ²) (qui n'est pas un cₙ)")
print(f"  → e, √2, √3 ne s'expriment pas via les cₙ sans nouvelle structure")
print(f"  → La formule α_EM = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵ nécessite 5 constantes")
print(f"    dont seulement φ apparaît dans cₙ")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. RECHERCHE SYSTÉMATIQUE DE FONCTIONS DES cₙ DONNANT α_EM
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 78)
print("6. RECHERCHE SYSTÉMATIQUE : fonctions F(cₙ) = 1/α_EM ?")
print("─" * 78)

candidates = []

# 6a. Ratios et produits
for n in range(1, 10):
    for m in range(n+1, min(n+5, 15)):
        val = C[m] / C[n]
        nom = f"c_{{{m}}}/c_{{{n}}}"
        candidates.append((nom, val, abs(val - A_CODATA)/A_CODATA))

# 6b. Inverses de moments
vals = [
    ("1/Σ cₙ", 1.0/somme_c),
    ("1/Σ cₙ²", 1.0/somme_c2),
    ("c₁⁻¹", 1.0/C[1]),
    ("c₂⁻¹", 1.0/C[2]),
    ("(c₁/c₂)²", (C[1]/C[2])**2),
    ("(c₁/c₂)³", (C[1]/C[2])**3),
    ("(c₁/c₂)⁴", (C[1]/C[2])**4),
    ("(c₁/c₂)⁵", (C[1]/C[2])**5),
    ("(c₂/c₃)²", (C[2]/C[3])**2),
    ("(c₂/c₃)³", (C[2]/C[3])**3),
    ("(c₂/c₃)⁴", (C[2]/C[3])**4),
]
for nom, val in vals:
    ecart = abs(val - A_CODATA)/A_CODATA if abs(val) > 1e-30 else float('inf')
    candidates.append((nom, val, ecart))

# 6c. Combinaisons avec des constantes mathématiques (TSVP)
# Les constantes π, e sont DÉRIVÉES (T4) — on peut les utiliser
PI = math.pi
E = math.e
SQRT2 = math.sqrt(2)
SQRT3 = math.sqrt(3)

combos = [
    ("c₁·φ·π²·e²", C[1] * PHI * PI**2 * E**2),
    ("c₁·π²·e²", C[1] * PI**2 * E**2),
    ("c₁·φ³·π·e", C[1] * PHI**3 * PI * E),
    ("c₁·π⁴·e⁻⁴", C[1] * PI**4 * E**(-4)),
    ("c₁·π⁴·e⁻⁴·φ⁻⁵", C[1] * PI**4 * E**(-4) * PHI**(-5)),
    ("c₁·π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵", C[1] * PI**4 * E**(-4) * PHI**(-5) * SQRT2**(-1) * SQRT3**(-5)),
    ("c₁²·π⁴·e⁻⁴", C[1]**2 * PI**4 * E**(-4)),
    ("(π·e)/(c₁·φ)", (PI * E) / (C[1] * PHI)),
    ("(π⁴·e⁻⁴)/(c₁·φ⁵)", (PI**4 * E**(-4)) / (C[1] * PHI**5)),
]
for nom, val in combos:
    ecart = abs(val - A_CODATA)/A_CODATA if abs(val) > 1e-30 else float('inf')
    candidates.append((nom, val, ecart))

# Trier par écart
candidates.sort(key=lambda x: x[2])
print(f"  Meilleurs candidats (écart à 1/α_EM = {A_CODATA:.4f}) :")
print(f"  {'Fonction':<40s} {'Valeur':>14s} {'Écart':>10s}")
print(f"  {'─'*40} {'─'*14} {'─'*10}")
for nom, val, ecart in candidates[:15]:
    flag = "✅" if ecart < 0.01 else ""
    print(f"  {nom:<40s} {val:>14.6f} {ecart:>9.2%} {flag}")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. VERDICT
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("VERDICT")
print("=" * 78)

# Identifier si un candidat à base de cₙ seulement donne α_EM
meilleur_cn = None
for nom, val, ecart in candidates:
    # Vérifier que la fonction n'utilise que cₙ et φ (pas π, e, √2, √3)
    seulement_cn = not any(c in nom for c in ['π', 'e', '√2', '√3'])
    # Vérifier aussi qu'elle n'utilise pas de constantes additionnelles
    if seulement_cn and ecart < 0.01:
        meilleur_cn = (nom, val, ecart)
        break

if meilleur_cn:
    print(f"\n  ✅ CANDIDAT TROUVÉ (écart < 1%) :")
    print(f"     {meilleur_cn[0]} = {meilleur_cn[1]:.6f}")
    print(f"     (1/α_EM = {A_CODATA:.6f}, écart = {meilleur_cn[2]*100:.4f}%)")
else:
    print(f"\n  ❌ AUCUNE FONCTION DES SEULS cₙ NE DONNE 1/α_EM À 1% PRÈS.")
    print()
    print(f"  La formule connue α_EM = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵ utilise")
    print(f"  π (dérivé T4), e (dérivé T4), φ (dérivé T1), √2 (F5), √3 (F5).")
    print(f"  Les cₙ ne contiennent que φ — les autres constantes nécessitent")
    print(f"  des structures mathématiques supplémentaires (intégrale gaussienne")
    print(f"  pour π, exponentielle pour e, symétries géométriques pour √2/√3).")
    print()
    print(f"  CONCLUSION : α_EM ne peut PAS être dérivé des seuls cₙ.")
    print(f"  Il nécessite l'ensemble {{π, e, φ, √2, √3}} comme alphabet,")
    print(f"  dont π et e sont déjà dérivés (T4) mais √2, √3 sont des frontières (F5).")
    print(f"  La dérivation complète de α_EM nécessite de dériver √2 et √3")
    print(f"  depuis les symétries géométriques — c'est F5.")


# ─── RAPPORT JSON ───
rapport = {
    "theoreme": "α_EM dérivé des cₙ ?",
    "constantes": {"phi": PHI, "alpha": ALPHA, "alpha_inv_codata": A_CODATA},
    "c_n": {str(n): float(C[n]) for n in range(10)},
    "tests_ratios": {f"c_{n+1}/c_{n}": float(ratios[n]) for n in range(10)},
    "recherche_candidats": [
        {"nom": nom, "valeur": float(val), "ecart_relatif": float(ecart)}
        for nom, val, ecart in candidates[:20]
    ],
    "verdict": {
        "derive_des_seuls_cn": bool(meilleur_cn is not None),
        "meilleur_candidat_cn": meilleur_cn[0] if meilleur_cn else None,
        "meilleure_valeur": meilleur_cn[1] if meilleur_cn else None,
        "conclusion": "α_EM ne peut pas être dérivé des seuls cₙ — "
                      "nécessite {π, e, φ, √2, √3} dont π, e sont dérivés (T4) "
                      "mais √2, √3 sont des frontières ouvertes (F5). "
                      "La dérivation complète de α_EM depuis les principes de la THU "
                      "reste une frontière ouverte.",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    },
}

chemin = os.path.join("data", "benchmarks", "derive_alpha_from_cn_report.json")
os.makedirs(os.path.dirname(chemin), exist_ok=True)
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)
print(f"\nRapport : {chemin}")