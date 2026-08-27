"""
TEST L3 — PHASE 3 : Résonance avec Mémoire (Noyau ABC)
========================================================
Mesure DIRECTE de l'atténuation par canal via resonate_abc().

Hypothèses testées :
  H1 : resonate_abc(ψ, ψ) / resonate(ψ, ψ) ≈ 1/φ pour UN canal
  H2 : Pour C = n+D canaux indépendants, le rapport total ≈ (1/φ)^C
  H3 : La factorisation tient : Π_k r_k ≈ r_total pour des canaux orthogonaux
  H4 : Les canaux interagissent-ils ? (test de non-linéarité)

Si H1-H3 sont vérifiés → L3 est validé NUMÉRIQUEMENT.
Si H4 montre une interaction → la factorisation nécessite une correction.

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vital-ka", "core", "python"))
from wave_lang import (encode, bind, resonate, resonate_abc, superpose,
                       diffract, spectrum, normalize, PHI, ALPHA, clear_encode_cache)
from abc_kernel import mittag_leffler, abc_kernel_np, B_1_PHI

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

DIM = 512
TOLERANCE = 1e-6
PHI_INV = ALPHA  # = 1/φ ≈ 0.618

# Modes photon (n=1, D=4 → C=5 canaux)
PHOTON_MODES = [
    "photon_helicite_+1_TE",
    "photon_helicite_-1_TM",
    "photon_longitudinal_virtuel",
    "photon_coulomb_instantane",
    "photon_echange_croise",
]

# Modes scalaire (n=0, D=4 → C=4)
SCALAR_MODES = [
    "scalaire_mode_x",
    "scalaire_mode_y",
    "scalaire_mode_z",
    "scalaire_mode_t",
]

# Modes graviton (n=2, D=4 → C=6)
GRAVITON_MODES = [
    "graviton_helicite_+2",
    "graviton_helicite_-2",
    "graviton_vecteur_x",
    "graviton_vecteur_y",
    "graviton_vecteur_z",
    "graviton_scalaire",
]

ELECTRON = "electron_spin_1/2_Dirac"


# ═══════════════════════════════════════════════════════════════════
# OUTILS DE MESURE
# ═══════════════════════════════════════════════════════════════════

def measure_canal_ratio(psi_canal):
    """
    Mesure le rapport resonate_abc / resonate pour un canal donné.
    
    Retourne :
        r_abc   : resonate_abc(ψ, ψ) — auto-résonance avec mémoire
        r_bare  : resonate(ψ, ψ)     — auto-résonance sans mémoire (= 1.0)
        ratio   : r_abc / r_bare
    """
    r_bare = resonate(psi_canal, psi_canal)
    r_abc = resonate_abc(psi_canal, psi_canal)
    return r_abc, r_bare, r_abc / max(r_bare, 1e-15)


def measure_canal_cross(psi_a, psi_b):
    """
    Mesure la résonance croisée (inter-canal) avec et sans mémoire.
    
    Une bonne orthogonalité → resonate(ψ_a, ψ_b) ≈ 0.
    """
    r_bare = resonate(psi_a, psi_b)
    r_abc = resonate_abc(psi_a, psi_b)
    return r_bare, r_abc


def build_vertex_set(boson_modes, electron_label=ELECTRON):
    """Construit les vertex ψ_e ⊛ ψ_boson pour chaque mode."""
    psi_e = encode(electron_label, dim=DIM)
    return [bind(psi_e, encode(m, dim=DIM)) for m in boson_modes]


def combined_vertex(vertices):
    """Superpose tous les vertex en un seul (mémoire holographique)."""
    return superpose(*vertices)


# ═══════════════════════════════════════════════════════════════════
# PRÉDICTIONS THÉORIQUES
# ═══════════════════════════════════════════════════════════════════

def predict(n_spin, n_space=4):
    """
    Prédiction THU : atténuation totale = (1/φ)^{n+D} = φ^{-(n+D)}.
    """
    C = n_spin + n_space
    return PHI_INV ** C, C


# ═══════════════════════════════════════════════════════════════════
# TEST PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def test_boson(name, n_spin, modes):
    """Test complet pour un boson donné."""
    print("─" * 70)
    print(f"  BOSON : {name} (spin n={n_spin}, D=4 → C={n_spin+4} canaux)")
    print("─" * 70)

    vertices = build_vertex_set(modes)
    C = len(vertices)

    # — 1. Ratios individuels par canal —
    print(f"\n  {'Canal':<30s} {'resonate_abc':>12s} {'resonate':>12s} {'ratio':>10s}")
    print(f"  {'─'*30} {'─'*12} {'─'*12} {'─'*10}")
    
    ratios = []
    for i, v in enumerate(vertices):
        r_abc, r_bare, ratio = measure_canal_ratio(v)
        ratios.append(ratio)
        label = modes[i][:28]
        print(f"  {label:<30s} {r_abc:>12.6f} {r_bare:>12.6f} {ratio:>10.6f}")

    mean_ratio = np.mean(ratios)
    std_ratio = np.std(ratios)
    
    print(f"\n  Ratio moyen par canal : {mean_ratio:.6f} ± {std_ratio:.6f}")
    print(f"  Prédit (1/φ = {PHI_INV:.6f}) : {PHI_INV:.6f}")
    print(f"  Écart : {(mean_ratio - PHI_INV) / PHI_INV * 100:+.2f}%")

    # — 2. Test de factorisation : produit des ratios vs ratio du combiné —
    product_ratios = np.prod(ratios)
    
    psi_combined = combined_vertex(vertices)
    _, _, ratio_combined = measure_canal_ratio(psi_combined)
    
    print(f"\n  Produit des {C} ratios : {product_ratios:.10f}")
    print(f"  Ratio du vertex combiné : {ratio_combined:.10f}")
    print(f"  Rapport (produit / combiné) : {product_ratios / max(ratio_combined, 1e-15):.6f}")
    
    # — 3. Prédiction théorique —
    pred_val, pred_C = predict(n_spin)
    print(f"\n  Prédiction THU (1/φ)^{C} = ({PHI_INV:.6f})^{C} = {pred_val:.10f}")
    print(f"  Mesuré (ratio combiné)            = {ratio_combined:.10f}")
    print(f"  Mesuré (produit des ratios)       = {product_ratios:.10f}")
    
    delta_product = abs(product_ratios - pred_val) / pred_val * 100
    delta_combined = abs(ratio_combined - pred_val) / pred_val * 100
    print(f"  Écart produit vs prédit : {delta_product:.2f}%")
    print(f"  Écart combiné vs prédit : {delta_combined:.2f}%")

    # — 4. Orthogonalité inter-canaux —
    print(f"\n  Matrice de résonance inter-canaux (bare | abc) :")
    print(f"  {'':>8s}", end="")
    for j in range(C):
        print(f"{'c'+str(j):>10s}", end="")
    print()
    for i in range(C):
        print(f"  {'c'+str(i):>8s}", end="")
        for j in range(C):
            if i == j:
                print(f"{'1.000':>10s}", end="")
            else:
                r_bare, r_abc = measure_canal_cross(vertices[i], vertices[j])
                print(f"{r_bare:>5.3f}|{r_abc:>4.3f}", end="")
        print()

    return {
        "name": name,
        "n_spin": n_spin,
        "C": C,
        "ratios": ratios,
        "mean_ratio": mean_ratio,
        "product_ratios": product_ratios,
        "ratio_combined": ratio_combined,
        "predicted": pred_val,
        "delta_combined": delta_combined,
        "delta_product": delta_product,
    }


# ═══════════════════════════════════════════════════════════════════
# TEST ABC KERNEL CHARACTERIZATION
# ═══════════════════════════════════════════════════════════════════

def characterize_abc_kernel():
    """Caractérise le noyau ABC : puissance spectrale, décroissance."""
    print("═" * 70)
    print("  CARACTÉRISATION DU NOYAU ABC")
    print("═" * 70)
    print()

    # Constantes
    print(f"  PHI       = {PHI:.15f}")
    print(f"  ALPHA     = {ALPHA:.15f}")
    print(f"  B(1/φ)    = {B_1_PHI:.10f}")
    print()

    # Noyau temporel
    K = abc_kernel_np(128).astype(np.float64)
    print(f"  Noyau ABC [0:128] :")
    print(f"    K(0)    = {K[0]:.10f}")
    print(f"    K(1)    = {K[1]:.10f}")
    print(f"    K(10)   = {K[10]:.10f}")
    print(f"    K(100)  = {K[100]:.10f}")
    print(f"    ΣK      = {K.sum():.10f}")
    print()

    # Réponse spectrale
    K_padded = np.zeros(DIM, dtype=np.float64)
    K_padded[:128] = K
    K_spec = np.fft.fft(K_padded)
    K_power = np.abs(K_spec) ** 2
    K_power_norm = K_power / K_power.sum()

    print(f"  Réponse spectrale (dim={DIM}) :")
    print(f"    max |K̃|²      = {K_power.max():.6e}")
    print(f"    min |K̃|²      = {K_power.min():.6e}")
    print(f"    Σ |K̃|²        = {K_power.sum():.6e}")
    print()

    # Analyse par bandes : diviser le spectre en C bandes égales (log)
    for C in [4, 5, 6, 10]:
        # Bandes de même largeur dans le domaine de Fourier
        band_width = DIM // 2 // C
        band_powers = []
        for c in range(C):
            start = c * band_width
            end = (c + 1) * band_width if c < C - 1 else DIM // 2
            power = K_power_norm[start:end].sum() + K_power_norm[DIM-end:DIM-start].sum()
            band_powers.append(power)

        print(f"  Puissance par bande (C={C} bandes égales) :")
        for c, p in enumerate(band_powers):
            print(f"    Bande {c+1} : {p:.6f}  ({p*100:.1f}%)")
        print(f"    Total      : {sum(band_powers):.6f}")
        print(f"    φ⁻¹ = {PHI_INV:.6f} — {'proche' if any(abs(p-PHI_INV)<0.1 for p in band_powers) else 'pas proche'}")
        print()

    # Fraction cumulée : où tombe φ⁻¹ ?
    cumsum = np.cumsum(K_power_norm[:DIM//2])
    # À quelle fraction du spectre atteint-on φ⁻¹ ?
    idx_phi = np.argmin(np.abs(cumsum - PHI_INV))
    print(f"  Fraction cumulée du spectre :")
    print(f"    φ⁻¹ = {PHI_INV:.6f} est atteint à l'index spectral {idx_phi}/{DIM//2}")
    print(f"    Soit {idx_phi/(DIM//2)*100:.1f}% du demi-spectre")
    print()

    return K_power_norm


# ═══════════════════════════════════════════════════════════════════
# TEST DE NON-LINÉARITÉ : les canaux interagissent-ils ?
# ═══════════════════════════════════════════════════════════════════

def test_nonlinearity(vertices):
    """
    Teste si resonate_abc est linéaire (factorisable) sur les canaux.
    
    Si OUI : resonate_abc(Σ v_k, Σ v_k) ≈ Σ resonate_abc(v_k, v_k)
             (les termes croisés sont négligeables)
    Si NON : des interférences inter-canaux modifient le résultat.
    """
    C = len(vertices)
    
    # Somme des auto-résonances ABC
    sum_auto = sum(resonate_abc(v, v) for v in vertices)
    
    # Résonance ABC du combiné
    psi_combined = combined_vertex(vertices)
    combined_abc = resonate_abc(psi_combined, psi_combined)
    
    # Somme des résonances croisées ABC (termes d'interférence)
    cross_sum = 0.0
    for i in range(C):
        for j in range(C):
            if i != j:
                cross_sum += resonate_abc(vertices[i], vertices[j])

    print(f"\n  Test de non-linéarité (interférence inter-canaux) :")
    print(f"    Σ auto-résonances ABC     = {sum_auto:.6f}")
    print(f"    Σ cross-résonances ABC    = {cross_sum:.6f}")
    print(f"    Résonance ABC du combiné  = {combined_abc:.6f}")
    print(f"    Σ auto + Σ cross          = {sum_auto + cross_sum:.6f}")
    print(f"    Rapport (Σauto+Σcross)/combined = {(sum_auto + cross_sum) / max(combined_abc, 1e-15):.6f}")
    print(f"    Fraction cross / auto     = {cross_sum / max(sum_auto, 1e-15):.6f}")

    # Si cross ≈ 0 : les canaux sont indépendants, la factorisation tient.
    # Si cross ≠ 0 : il faut tenir compte des interférences.
    return cross_sum, sum_auto


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t0 = time.time()
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  TEST L3 — PHASE 3 : RÉSONANCE AVEC MÉMOIRE                 ║")
    print("║  Mesure de l'atténuation φ⁻¹ par canal via resonate_abc()   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"  Dimension : {DIM}")
    print(f"  PHI       : {PHI:.15f}")
    print(f"  1/φ       : {PHI_INV:.15f}")
    print()

    # — CARACTÉRISATION —
    K_spec = characterize_abc_kernel()

    # — TESTS —
    results = {}

    # Photon (n=1, C=5)
    results["photon"] = test_boson("PHOTON", n_spin=1, modes=PHOTON_MODES)

    # Scalaire (n=0, C=4)
    results["scalaire"] = test_boson("SCALAIRE", n_spin=0, modes=SCALAR_MODES)

    # Graviton (n=2, C=6)
    results["graviton"] = test_boson("GRAVITON", n_spin=2, modes=GRAVITON_MODES)

    # — NON-LINÉARITÉ —
    print("═" * 70)
    print("  TEST DE NON-LINÉARITÉ (INTERFÉRENCES INTER-CANAUX)")
    print("═" * 70)

    for name in ["photon", "scalaire", "graviton"]:
        r = results[name]
        vertices = build_vertex_set(
            PHOTON_MODES if name == "photon" else
            SCALAR_MODES if name == "scalaire" else
            GRAVITON_MODES
        )
        print(f"\n  ── {name.upper()} ──")
        test_nonlinearity(vertices)

    # — SYNTHÈSE —
    print()
    print("═" * 70)
    print("  SYNTHÈSE L3 — PHASE 3")
    print("═" * 70)
    print()

    print(f"  {'Boson':<12s} {'C=n+D':>6s} {'Ratio/moy':>10s} {'Ratio/comb':>10s} {'Prédit':>10s} {'Écart':>8s}")
    print(f"  {'─'*12} {'─'*6} {'─'*10} {'─'*10} {'─'*10} {'─'*8}")
    
    all_close = True
    for name, r in results.items():
        delta = r["delta_combined"]
        close = delta < 5.0  # moins de 5% d'écart
        all_close = all_close and close
        status = "✅" if close else "❌"
        print(f"  {status} {r['name']:<10s} {r['C']:>6d} {r['mean_ratio']:>10.6f} {r['ratio_combined']:>10.6f} {r['predicted']:>10.6f} {delta:>7.2f}%")

    print()

    if all_close:
        print("  ✅ TOUS LES TESTS PASSENT : le rapport resonate_abc/resonate")
        print(f"     est cohérent avec (1/φ)^{{n+D}} pour n=0,1,2.")
        print()
        print("  ⚠️  NOTE : Ceci valide L3 NUMÉRIQUEMENT, dans le cadre")
        print("     de l'implémentation actuelle. La preuve algébrique")
        print("     (pourquoi exactement 1/φ par canal) reste à formaliser.")
    else:
        print("  ❌ ÉCART SIGNIFICATIF détecté. Plusieurs hypothèses :")
        print("     1. Les canaux ne sont pas vraiment indépendants")
        print("     2. La formule (1/φ)^C n'est pas la bonne")
        print("     3. L'implémentation de resonate_abc() doit être corrigée")
        print("     4. encode() ne capture pas la physique du vertex")

    print()
    print(f"  Temps : {time.time() - t0:.2f}s")
    print()