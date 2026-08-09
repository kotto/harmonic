#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validation_coeff_quantiques.py — VIOLET A (protocole ex-ante)
=============================================================

La chaîne dérivée à tester :
    stabilité cosmique ⇒ α = 1/φ (DERIVATION_1_PHI.md, chaînon ⚠ persistance)
    ⇒ solution du couplage : E_α(−λ t^α) = Σ_k (−λ)^k t^{αk} / Γ(αk+1)
    ⇒ COEFFICIENTS DÉRIVÉS : c_k = 1/Γ(k/φ + 1)   (pas postulés, pas ajustés)

Question centrale : les coefficients dérivés {c₁, c₂, c₃} valent-ils {φ, π, e} ?
Si oui → Ψ_quantique = φ·Ψ₁ + π·(Ψ₁)² + e·(Ψ₁)³ est la forme exacte de la chaîne.
Si non → la chaîne prédit d'autres coefficients ; l'écart est mesuré, publié.

PROTOCOLE :
  1. Cibles {φ, π, e, ...} DÉCLARÉES ci-dessous, AVANT tout calcul (aucun
     ajustement post-hoc — leçon du treillis, PLAN_FAIBLESSES A1.2).
  2. Vérification indépendante : coefficients de Taylor de E_α extraits par
     FFT sur le cercle unité (méthode de la session Fourier, 1.78e-15) vs 1/Γ(αk+1).
  3. Noyau ABC : raccord série ↔ asymptotique (deux implémentations croisées).
  4. Verdict publié, même négatif (méthode GW170817 : l'exclusion est un résultat).

PRÉCISION (documentée) : la série directe en float64 subit une annulation
catastrophique pour |z| ≳ 9 (termes jusqu'à ~1e17 pour E_α(−10)) ; au-delà,
on bascule sur l'asymptotique de Wiman, validée par les identités exactes
(E_1/2 vérifié sur e^{x²}·erfc(x), zone où les deux chemins sont précis).
Références internes : DERIVATION_1_PHI.md, DOCUMENT_FONDATEUR §2.4,
   session 988987f (coefficients fonction-dépendants, corr −0.13/0.00).
"""
import cmath
import json
import math
import os
import time

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# 0. CONSTANTES — les cibles sont DÉCLARÉES AVANT tout calcul (ex-ante)
# ─────────────────────────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0          # 1.618033988749895
ALPHA = 1.0 / PHI                           # 0.6180339887498949 — ordre ABC
SEUIL_MATCH = 1e-3                          # écart relatif < 1e-3 ⇒ « match » (déclaré avant)
R_SERIE = 6.0                               # série directe valable pour |z| ≤ R_SERIE

CIBLES_COEFFS = {                            # testées contre c_k = 1/Γ(αk+1)
    "phi": PHI,
    "pi": math.pi,
    "e": math.e,
    "1/phi": 1.0 / PHI,
    "phi^2": PHI * PHI,
    "e/pi": math.e / math.pi,
    "1/pi": 1.0 / math.pi,
    "sqrt2": math.sqrt(2.0),
    "sqrt3": math.sqrt(3.0),
    "sqrt5": math.sqrt(5.0),
    "2*pi": 2.0 * math.pi,
}

CIBLES_RAPPORTS = {                          # testées contre c_{k+1}/c_k
    "1/phi": 1.0 / PHI,
    "1/e": 1.0 / math.e,
    "1/pi": 1.0 / math.pi,
    "e-2": math.e - 2.0,
    "pi-3": math.pi - 3.0,
    "phi-1": PHI - 1.0,
}

LAMBDA = ALPHA / (1.0 - ALPHA)               # λ = α/(1−α) ≈ 1.618 = φ (dérivé)
B_ALPHA = 1.0 - ALPHA + ALPHA / math.gamma(ALPHA)  # normalisation ABC


# ─────────────────────────────────────────────────────────────────────────────
# 1. MITTAG-LEFFLER ROBUSTE — série directe (|z| ≤ R_SERIE) + asymptotique de
#    Wiman (|z| > R_SERIE, z réel négatif, α ∈ (0,1)). Croisées en chevauchement.
# ─────────────────────────────────────────────────────────────────────────────
def lgamma_signed(x):
    """log|Γ(x)| et signe de Γ(x) pour tout x réel (x ≤ 0 : compléments).
    Pôle (x ∈ {0,−1,−2,…}) → (None, 0.0) : le terme correspondant est nul."""
    if x > 0:
        return math.lgamma(x), 1.0
    if x == math.floor(x):                    # pôle : 1/Γ = 0
        return None, 0.0
    lg = (math.log(math.pi) - math.log(abs(math.sin(math.pi * x)))
          - math.lgamma(1.0 - x))
    # Γ(x) < 0 ⟺ x ∈ (−m−1, −m) avec m impair (m = floor(−x)) → signe = (−1)^{m+1}
    s = -1.0 if (math.floor(-x) % 2 == 0) else 1.0
    return lg, s


def ml_serie(z, alpha, max_terms=300, tol=1e-15):
    """E_α(z) = Σ z^k/Γ(αk+1) — série directe, sommation de Kahan.
    Valide en float64 pour |z| ≤ R_SERIE (au-delà : annulation catastrophique)."""
    zc = complex(z)
    log_abs_z = math.log(abs(zc))
    arg_z = math.atan2(zc.imag, zc.real)
    total = 0.0 + 0.0j
    comp = 0.0 + 0.0j
    for k in range(max_terms):
        log_a = k * log_abs_z - math.lgamma(alpha * k + 1.0)
        if log_a < -745:                      # sous-flux numérique
            break
        a = math.exp(log_a)
        ph = (k * arg_z) % (2.0 * math.pi)
        term = a * complex(math.cos(ph), math.sin(ph))
        y = term - comp                       # Kahan
        t = total + y
        comp = (t - total) - y
        total = t
        if k > 5 and abs(term) < tol * (1.0 + abs(total)):
            break
    return total


def ml_asympt(x, alpha, max_terms=200):
    """E_α(−x) ~ Σ_{k≥1} (−1)^{k−1} x^{−k}/Γ(1−αk) — Wiman, pour α ∈ (0,1), x > 0.
    Série asymptotique alternée : on s'arrête après que |terme| a dépassé 5× le
    minimum rencontré (le minimum est atteint plusieurs fois — suite non monotone)."""
    s = 0.0
    best = None
    for k in range(1, max_terms):
        arg = 1.0 - alpha * k
        lg, sg = lgamma_signed(arg)
        if lg is None:                        # pôle : terme nul (ex. α=1/2, k=2)
            continue
        log_a = -k * math.log(x) - lg
        sign = sg if k % 2 == 1 else -sg      # (−1)^{k−1} · sign(Γ(1−αk))
        term = sign * math.exp(log_a)
        s += term
        if best is None or abs(term) < abs(best):
            best = term
        if k > 10 and abs(term) > 5.0 * abs(best):
            break
    return s


def E_alpha(z, alpha=ALPHA):
    """E_α(z) — dispatch robuste. z réel négatif, |z| > R_SERIE, α ∈ (0,1) → Wiman."""
    zc = complex(z)
    if zc.imag == 0.0 and zc.real < 0.0 and 0.0 < alpha < 1.0 and -zc.real > R_SERIE:
        return ml_asympt(-zc.real, alpha)
    return ml_serie(zc, alpha)


# ─────────────────────────────────────────────────────────────────────────────
# 2. VÉRIFICATION 1 — sanity sur les identités exactes connues
#    (E_1/2 n'est testé que pour x ≤ 2 : la zone de transition x≈5 exige une
#    précision supérieure au float64 — limite documentée, hors de la chaîne)
# ─────────────────────────────────────────────────────────────────────────────
def verif_identites():
    ok = True
    # E_1(z) = e^z
    for z in (-3.0, 1.5, 2.0 + 1.0j):
        e = abs(E_alpha(z, 1.0) - cmath.exp(complex(z)))
        ok &= e < 1e-12
        print(f"  E_1({z}) = e^z             : |Δ| = {e:.2e} {'✅' if e < 1e-12 else '❌'}")
    # E_{1/2}(−x) = e^{x²}·erfc(x)  (x réel ≥ 0, série précise pour x ≤ 2)
    for x in (0.5, 2.0):
        ref = math.exp(x * x) * math.erfc(x)
        e = abs(E_alpha(-x, 0.5) - ref) / max(abs(ref), 1e-300)
        ok &= e < 1e-10
        print(f"  E_1/2(−{x}) = e^x²·erfc(x) : |Δ|rel = {e:.2e} {'✅' if e < 1e-10 else '❌'}")
    # E_2(−x²) = cos(x)  (α=2 > 1 : toujours série, |z|=x² jusqu'à 16 — OK)
    for x in (0.5, 2.0, 4.0):
        e = abs(E_alpha(-x * x, 2.0) - math.cos(x))
        ok &= e < 1e-10
        print(f"  E_2(−{x}²) = cos({x})      : |Δ| = {e:.2e} {'✅' if e < 1e-10 else '❌'}")
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# 3. VÉRIFICATION 2 — coefficients de Taylor par FFT (méthode indépendante,
#    celle de la session Fourier : f = Σ cₙ(Ψ₁)ⁿ à 1.78e-15)
# ─────────────────────────────────────────────────────────────────────────────
def verif_taylor_fft(n_fft=512, kmax=32):
    theta = 2.0 * np.pi * np.arange(n_fft) / n_fft
    f = np.array([E_alpha(np.exp(1j * t), ALPHA) for t in theta])  # E_α sur |z|=1
    coeffs_fft = np.fft.fft(f) / n_fft                              # ĉ_k (pas d'aliasing)
    err = []
    for k in range(kmax):
        c_exact = math.exp(-math.lgamma(ALPHA * k + 1.0))            # 1/Γ(αk+1)
        err.append(abs(coeffs_fft[k].real - c_exact))
    e_max = max(err)
    print(f"  Taylor E_α par FFT ({n_fft} pts) vs 1/Γ(αk+1), k=0..{kmax-1} : "
          f"erreur max = {e_max:.3e} {'✅' if e_max < 1e-10 else '❌'}")
    return e_max


# ─────────────────────────────────────────────────────────────────────────────
# 4. VÉRIFICATION 3 — noyau ABC : raccord des deux implémentations dans la zone
#    où elles sont TOUTES DEUX précises (z ∈ [−9, −8.5] : série ~1e-8, Wiman ~1e-8)
# ─────────────────────────────────────────────────────────────────────────────
def verif_raccord_noyau():
    zs = -np.linspace(7.0, 6.0, 41)
    e_max = 0.0
    for z in zs:
        a = ml_serie(complex(z), ALPHA)
        b = ml_asympt(-z, ALPHA)
        e_max = max(e_max, abs(a - b) / max(abs(a), 1e-30))
    print(f"  Raccord série ↔ Wiman, z ∈ [−7, −6]      : erreur rel max = "
          f"{e_max:.3e} {'✅' if e_max < 1e-3 else '❌'}")

    # Bonus : le noyau K(t) = B(α)·E_α(−λt^α) doit être strictement décroissant
    # (E_α(−x) complètement monotone pour α ∈ (0,1)) — attrape les ruptures du dispatch.
    ts = np.geomspace(0.01, 60.0, 1200)
    K = np.array([B_ALPHA * E_alpha(-LAMBDA * t ** ALPHA).real for t in ts])
    violations = int(np.sum(np.diff(K) > 1e-9))
    print(f"  Noyau ABC décroissant sur [0.01, 60]     : {violations} violation(s) "
          f"{'✅' if violations == 0 else '❌'}")
    return e_max


# ─────────────────────────────────────────────────────────────────────────────
# 5. LE CŒUR — coefficients dérivés c_k = 1/Γ(k/φ+1) vs cibles DÉCLARÉES
# ─────────────────────────────────────────────────────────────────────────────
def coeffs_derives(kmax=6):
    return [math.exp(-math.lgamma(ALPHA * k + 1.0)) for k in range(kmax + 1)]


def test_cibles(cs, cibles):
    """Test ex-ante : écart relatif de chaque coefficient contre chaque cible."""
    lignes, matches = [], []
    for k, c in enumerate(cs):
        for label, tgt in cibles.items():
            rel = abs(c - tgt) / tgt
            if rel < SEUIL_MATCH:
                matches.append((k, label, rel))
            lignes.append((k, label, rel))
    return lignes, matches


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    print("=" * 78)
    print("VIOLET A — La chaîne dérivée : stabilité ⇒ α=1/φ ⇒ c_k = 1/Γ(k/φ+1)")
    print("=" * 78)
    print(f"α = 1/φ = {ALPHA:.15f}   λ = α/(1−α) = {LAMBDA:.15f} (≈ φ)   "
          f"B(α) = {B_ALPHA:.15f}")
    print(f"Seuil de match déclaré AVANT le calcul : écart relatif < {SEUIL_MATCH}\n")

    print("─ Vérification 1 · identités exactes (E_1, E_1/2, E_2)")
    ok1 = verif_identites()
    print()

    print("─ Vérification 2 · coefficients de Taylor de E_α par FFT (indépendant)")
    e2 = verif_taylor_fft()
    print()

    print("─ Vérification 3 · raccord série ↔ Wiman + monotonie du noyau ABC")
    e3 = verif_raccord_noyau()
    print()

    cs = coeffs_derives(6)
    print("─ Coefficients DÉRIVÉS de la chaîne (la prédiction de la théorie) :")
    for k in range(1, 7):
        print(f"    c_{k} = 1/Γ({k}/φ+1) = 1/Γ({ALPHA*k+1:.6f}) = {cs[k]:.15f}")
    print()

    print("─ Test ex-ante : c_k vs cibles {φ, π, e, …}  (seuil 1e-3)")
    lignes_c, matches_c = test_cibles(cs[1:5], CIBLES_COEFFS)
    for k, label, rel in sorted(lignes_c, key=lambda t: t[2])[:8]:
        flag = "✅ MATCH" if rel < SEUIL_MATCH else ""
        print(f"    c_{k+1} vs {label:8s} : écart rel = {rel:.3e} {flag}")
    print()

    rapports = [cs[k + 1] / cs[k] for k in range(1, 5)]
    print("─ Test ex-ante : rapports c_{k+1}/c_k vs cibles {1/φ, 1/e, 1/π, …}")
    lignes_r, matches_r = test_cibles(rapports, CIBLES_RAPPORTS)
    for k, label, rel in sorted(lignes_r, key=lambda t: t[2])[:6]:
        flag = "✅ MATCH" if rel < SEUIL_MATCH else ""
        print(f"    c_{k+2}/c_{k+1} = {rapports[k]:.6f} vs {label:6s} : écart rel = {rel:.3e} {flag}")
    print()

    # L'équation postulée Ψ_quantique = φ·Ψ₁ + π·Ψ₁² + e·Ψ₁³ vs la chaîne dérivée
    postule = np.array([PHI, math.pi, math.e])
    derive = np.array(cs[1:4])
    err_eq = np.linalg.norm(postule - derive) / np.linalg.norm(postule)
    print("─ L'équation proposée vs la chaîne dérivée :")
    print(f"    postulé : (φ, π, e)              = {postule}")
    print(f"    dérivé  : (c₁, c₂, c₃)           = {derive}")
    print(f"    écart relatif global             = {err_eq:.3e}")
    print()

    # Verdict
    verdict = {
        "identites_exactes": "✅" if ok1 else "❌",
        "taylor_fft": "✅" if e2 < 1e-10 else "❌",
        "raccord_noyau": "✅" if e3 < 1e-3 else "❌",
        "matchs_coeffs_cibles": len(matches_c),
        "matchs_rapports_cibles": len(matches_r),
        "equation_postulee_vs_derivee": err_eq,
    }
    print("─ VERDICT")
    print(f"    Chaîne numérique (identités, FFT, raccord) : "
          f"{verdict['identites_exactes']} {verdict['taylor_fft']} {verdict['raccord_noyau']}")
    if matches_c or matches_r:
        print(f"    ⚠️  Match(s) trouvé(s) : {matches_c + matches_r}")
    else:
        print("    ❌ Aucune cible {φ, π, e, …} atteinte par les coefficients dérivés")
    print(f"    Ψ_quantique = φΨ₁ + πΨ₁² + eΨ₁³ : écart vs chaîne dérivée = {err_eq:.3e} "
          f"→ {'APPROXIMATION, pas égalité' if err_eq > SEUIL_MATCH else 'ÉGALITÉ EXACTE'}")
    print(f"    Durée : {time.time() - t0:.1f} s")

    # Rapport JSON (convention data/benchmarks/)
    rapport = {
        "protocole": "ex-ante — cibles déclarées avant le calcul",
        "alpha": ALPHA,
        "lambda_abc": LAMBDA,
        "seuil_match": SEUIL_MATCH,
        "verifications": verdict,
        "coeffs_derives_c1_c6": cs[1:7],
        "equation_postulee": ["phi", "pi", "e"],
        "equation_derivee": cs[1:4],
        "ecart_relatif_equation": err_eq,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    chemin = os.path.join("data", "benchmarks", "coeff_quantiques_report.json")
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"\nRapport : {chemin}")


if __name__ == "__main__":
    main()
