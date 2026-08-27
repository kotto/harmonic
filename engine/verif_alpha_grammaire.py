# -*- coding: utf-8 -*-
"""
VÉRIFICATION MACHINE — ASSAUT « GRAMMAIRE ONDULATOIRE » SUR α (V0)
==================================================================
Dépôt daté AVANT exécution : DEPOT_ALPHA_GRAMMAIRE_V0.md (2026-08-27).
Ce script est une TRANSCRIPTION du dépôt : mêmes objets (§2), mêmes familles (§3),
mêmes barres (§4), mêmes contrôles (§5). Zéro paramètre libre, aucune graine.

Registre fermé : 239 lectures —
  Famille A : 15 lectures vertex rejouées comme TÉMOIN NÉGATIF
              (attendu déposé : 0/15 à 1e-4, meilleur (b, π⁴) = 97,5115 ;
               un hit ici = pipeline cassé ⇒ V4, pas de verdict physique)
  Famille B : D_p = (1/π)∫₀^∞ |K̃(ω)|^p dω, p ∈ {1,2,3,4} — convergence vérifiée
              machine AVANT verdict (dépôt §3) ; candidats {D_p, 1/D_p},
              8 lectures toutes rapportées
  Famille C : Route C1 (ratio)   α⁻¹_cand = (1/α_W)·(1/|K̃(½)|²)·φ^e·m
              Route C2 (produit) α⁻¹_cand = 1/(α_W·α_S·φ^e·m)
              e ∈ {0, ±1, ±2, ±3, ±4, ±1/φ, −5/2} (12 jauges)
              m ∈ {1, e^{1/φ}, e^{−1/φ}, F₁₀=55, L₁₀=123, Γ(2/φ+1), 2φ, φ², √5} (9 témoins)
              → 108 + 108 = 216 lectures

Verdicts figés (dépôt §4) :
  [T+] lecture ≤ 2,355e-7  ⇒ ALPHA_GRAMMAIRE_CONFIRME (exit 0)
  [T]  meilleur ≤ 1e-4     ⇒ admission (exit 0)
  [F]  0 hit à 1e-4        ⇒ ALPHA_HORS_GRAMMAIRE_STATIQUE (exit 1)
  V4   Famille A ≠ 0/15 ou meilleur ≠ 97,5115 ⇒ pipeline en échec, pas de verdict physique

Sortie : resultat_alpha_grammaire.json
"""

import cmath
import json
import math
import os
import sys
from datetime import datetime
from decimal import Decimal as D, getcontext

# ------------------------------------------------------------------ constantes (dépôt §2, §5)
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
SQRT5 = math.sqrt(5.0)

ALPHA_W = 1.0 / 30.0                    # α_W exact (corpus)
ALPHA_S = 0.118034                      # α_S corpus (dépôt §3, Route C2)
ALPHA_INV_CODATA_2022 = 137.035999177   # O7 — cible (dépôt §2.1)
ANCRE_5_FACTEURS = 137.036031356        # valeur corpus de la formule T0 (maintenance d'ancre, C4)
MEILLEURE_VERTEX_DEPOT = 97.5115        # attendu déposé, Famille A (dépôt §3)

TOL_HIT_PLUS = 2.355e-7                 # V+ (précision du corpus)
TOL_HIT = 1.0e-4                        # V2 / V3 — barre pré-enregistrée
TOL_ID = 1e-15
TOL_C1 = 1e-8                           # dépôt §5, contrôle C1
TOL_C2 = 1e-9                           # dépôt §5, contrôle C2
TOL_C4 = 1e-11                          # dépôt §5, contrôle C4 (relative — ancre publiée au 1e-9)
TOL_CONV = 1e-5                         # stabilité relative exigée des D_p (dépôt §3 : convergence machine)
TOL_V4 = 1e-3                           # reproduction de la meilleure lecture vertex (4 décimales déposées)

DEPOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DEPOT_ALPHA_GRAMMAIRE_V0.md")

controles = []      # (nom, ok, detail)
famille_A = []      # 15 lectures
famille_B = []      # 8 candidats avec statut de convergence
famille_C = []      # 216 lectures
journal_B = []      # journal de convergence D_p


def controle(nom, ok, detail):
    controles.append({"nom": nom, "ok": bool(ok), "detail": detail})
    print(("  [OK]  " if ok else "  [FAIL]") + f" {nom} : {detail}")
    return ok


# ------------------------------------------------------------------ noyau ML (transcription du registre vertex validé)
def E_alpha_neg(x, alpha=ALPHA, kmax=400):
    """E_alpha(-x) par série entière (fiable pour x <= 8 en flottant... plancher d'annulation voir E_alpha_dec)."""
    s = 0.0
    for k in range(kmax):
        t = (-x) ** k / math.gamma(alpha * k + 1.0)
        s += t
        if 10 < k < kmax - 1 and abs(t) < 1e-18:
            break
    return s


def asym4(x, alpha=ALPHA):
    """E_alpha(-x) asymptotique 4 termes (x grand)."""
    s = 0.0
    for m in range(1, 5):
        s += (-1) ** (m + 1) / (x ** m * math.gamma(1.0 - m * alpha))
    return s


def Ktilde_complex(omega, alpha=ALPHA):
    """K~(omega) = (i omega)^{alpha-1} / ((i omega)^alpha + phi) — branche principale."""
    z = 1j * omega
    return cmath.exp((alpha - 1.0) * cmath.log(z)) / (cmath.exp(alpha * cmath.log(z)) + PHI)


def Ktilde2_real(omega, alpha=ALPHA):
    """|K~(omega)|^2 forme réelle développée."""
    num = omega ** (2.0 * alpha - 2.0)
    den = omega ** (2.0 * alpha) + 2.0 * PHI * math.cos(math.pi * alpha / 2.0) * omega ** alpha + PHI ** 2
    return num / den


def L_num(sigma, alpha=ALPHA):
    """Intégrale directe int_0^oo e^{-sigma t} E_alpha(-phi t^alpha) dt — pièces vertex exactes (flottant)."""
    lam = PHI
    # morceau 1 : [0, 0.5] — double série (cusp t^alpha traité exactement)
    S1 = 0.0
    for j in range(45):
        aj = (-sigma) ** j / math.factorial(j)
        for k in range(140):
            ak = (-lam) ** k / math.gamma(alpha * k + 1.0)
            S1 += aj * ak * 0.5 ** (j + alpha * k + 1.0) / (j + alpha * k + 1.0)
    # morceau 2 : [0.5, 13.2] — Simpson (integrande lisse)
    a, b, n = 0.5, 13.2, 6350
    h = (b - a) / n
    f = lambda t: math.exp(-sigma * t) * E_alpha_neg(lam * t ** alpha)
    I2 = f(a) + f(b) + 4.0 * sum(f(a + (2 * i - 1) * h) for i in range(1, n // 2 + 1)) \
         + 2.0 * sum(f(a + 2 * i * h) for i in range(1, n // 2))
    I2 *= h / 3.0
    # morceau 3 : [13.2, 45] — Simpson sur l'asymptotique 4 termes
    a, b, n = 13.2, 45.0, 636
    h = (b - a) / n
    g = lambda t: math.exp(-sigma * t) * asym4(lam * t ** alpha)
    I3 = g(a) + g(b) + 4.0 * sum(g(a + (2 * i - 1) * h) for i in range(1, n // 2 + 1)) \
         + 2.0 * sum(g(a + 2 * i * h) for i in range(1, n // 2))
    I3 *= h / 3.0
    return S1 + I2 + I3


def L_closed(sigma, alpha=ALPHA):
    """Formule formelle : L[E_alpha(-phi t^alpha)](s) = s^{alpha-1} / (s^alpha + phi)."""
    return sigma ** (alpha - 1.0) / (sigma ** alpha + PHI)


# --------------------------------------------- haute précision Decimal (contrôle C1, dépôt §5 barre 1e-8)
# La série alternée E_alpha(-x) en flottant souffre d'un plancher d'annulation catastrophe
# (termes ~1e10 pour x ~ 8) : elle fausse L_num de ~1.1e-8 à sigma=1, au-dessus de la barre
# du dépôt. Mêmes pièces, même grille — seule la PRÉCISION D'ÉVALUATION de E_alpha monte
# (Decimal 50 chiffres). Aucune liberté : l'intégrale converge vers la même valeur exacte.
getcontext().prec = 50
PHI_D = (1 + D(5).sqrt()) / 2
ALPHA_D = 1 / PHI_D


def ln_gamma_dec(z):
    """ln Gamma(z) en Decimal, z > 0 : récurrence pour z > 22 puis Stirling (8 termes)."""
    zf = D(z)
    n = 0
    while zf < 22:
        zf += 1
        n += 1
    lnz = zf.ln()
    s = D(0)
    coeffs = [D(1) / 12, D(-1) / 360, D(1) / 1260, D(-1) / 1680,
              D(1) / 1188, D(-691) / 360360, D(1) / 156, D(-3617) / 122400]
    zinv = 1 / zf
    p = zinv
    for c in coeffs:
        s += c * p
        p = p * zinv * zinv
    lnG = (zf - D("0.5")) * lnz - zf + D(2.0 * math.pi).ln() / 2 + s
    if n > 0:
        for i in range(n):
            lnG = lnG - (zf - 1 - i).ln()
    return lnG


C_DEC = [(-ln_gamma_dec(ALPHA_D * k + 1)).exp() for k in range(300)]   # c_k = 1/Gamma(alpha k + 1)


def E_alpha_dec(x, kmax=300):
    """E_alpha(-x) = somme (-x)^k / Gamma(alpha k + 1) en Decimal 50 chiffres."""
    xd = D(x)
    s = D(0)
    p = D(1)
    for k in range(kmax):
        t = p * C_DEC[k]
        s = s + t
        if 10 < k < kmax - 1 and abs(t) < D("1e-45"):
            break
        p = p * (-xd)
    return float(s)


def L_num_precis(sigma):
    """Mêmes pièces que le dépôt §6 : double série [0, 0.5], Simpson h=0.002 sur [0.5, 13.2]
    (E_alpha évalué en Decimal), asymptotique 4 termes sur [13.2, 60] (queue morte : e^{-60})."""
    lam = PHI
    # morceau 1 : [0, 0.5] — double série (identique vertex ; termes max O(1), pas d'annulation)
    S1 = 0.0
    for j in range(45):
        aj = (-sigma) ** j / math.factorial(j)
        for k in range(140):
            ak = (-lam) ** k / math.gamma(ALPHA * k + 1.0)
            S1 += aj * ak * 0.5 ** (j + ALPHA * k + 1.0) / (j + ALPHA * k + 1.0)
    # morceau 2 : [0.5, 13.2] — Simpson h = 0.002, E_alpha en Decimal 50 chiffres
    a, b, n = 0.5, 13.2, 6350
    h = (b - a) / n
    f = lambda t: math.exp(-sigma * t) * E_alpha_dec(lam * t ** ALPHA)
    I2 = f(a) + f(b) + 4.0 * sum(f(a + (2 * i - 1) * h) for i in range(1, n // 2 + 1)) \
         + 2.0 * sum(f(a + 2 * i * h) for i in range(1, n // 2))
    I2 *= h / 3.0
    # morceau 3 : [13.2, 60] — Simpson sur l'asymptotique 4 termes (le dépôt pose la pièce sur [13.2, ∞))
    a, b, n = 13.2, 60.0, 23400
    h = (b - a) / n
    g = lambda t: math.exp(-sigma * t) * asym4(lam * t ** ALPHA)
    I3 = g(a) + g(b) + 4.0 * sum(g(a + (2 * i - 1) * h) for i in range(1, n // 2 + 1)) \
         + 2.0 * sum(g(a + 2 * i * h) for i in range(1, n // 2))
    I3 *= h / 3.0
    return S1 + I2 + I3


# ================================================================== PRÉAMBULE
print("=" * 74)
print("  ASSAUT « GRAMMAIRE ONDULATOIRE » SUR alpha — V0")
print("  Dépôt daté : DEPOT_ALPHA_GRAMMAIRE_V0.md (2026-08-27) — avant exécution")
print("=" * 74)
print(datetime.now().isoformat(timespec="seconds"))
print()

ok_global = True

# ================================================================== CONTRÔLES BLOQUANTS (dépôt §5)
print("[CONTRÔLES BLOQUANTS — un échec ⇒ REFUTE, exit 1]")

depot_ok = os.path.exists(DEPOT)
mtime = datetime.fromtimestamp(os.path.getmtime(DEPOT)).isoformat(timespec="seconds") if depot_ok else "absent"
ok_global &= controle("C0a dépôt présent, mtime antérieur à l'exécution", depot_ok, f"mtime = {mtime}")

ok_global &= controle("C0b identité d'or phi² = phi + 1",
                      abs(PHI * PHI - PHI - 1.0) < TOL_ID and abs(1.0 / PHI - (PHI - 1.0)) < TOL_ID,
                      f"écart = {abs(PHI * PHI - PHI - 1.0):.2e} ; 1/phi = phi - 1")

c1_ok = True
c1_details = []
for sigma in (1.0, 2.0):
    lf = L_closed(sigma)
    ec = abs(L_num_precis(sigma) - lf)
    ec_leg = abs(L_num(sigma) - lf)
    c1_ok = c1_ok and ec < TOL_C1
    c1_details.append(f"sigma={sigma}: écart {ec:.2e} (legacy flottant: {ec_leg:.2e})")
c1_float = 1.0 / math.gamma(1.0 + ALPHA)
gval = abs(float(C_DEC[1]) - c1_float) / c1_float
c1_details.append(f"table Gamma décimale vs flottant: {gval:.1e}")
ok_global &= controle("C1 forme close du noyau vs intégration directe (Decimal 50 chiffres)",
                      c1_ok, " ; ".join(c1_details))

c2_calc = 1.0 / math.gamma(2.0 / PHI + 1.0)
ok_global &= controle("C2 c2 = 1/Gamma(2/phi+1) vs publié 0,889630375",
                      abs(c2_calc - 0.889630375) < TOL_C2,
                      f"calc = {c2_calc:.9f} ; écart = {abs(c2_calc - 0.889630375):.2e}")

ok_global &= controle("C3 ancre CODATA 2022", True,
                      f"alpha^-1 = {ALPHA_INV_CODATA_2022} (constante du monde)")

T0 = math.pi ** 4 * math.exp(-4.0) * PHI ** (-5.0) * 2.0 ** (-0.5) * 3.0 ** (-2.5)
T0_inv = 1.0 / T0
ec4 = abs(T0_inv - ANCRE_5_FACTEURS) / ANCRE_5_FACTEURS
gap_codata = abs(T0_inv - ALPHA_INV_CODATA_2022) / ALPHA_INV_CODATA_2022
ok_global &= controle("C4 recompute formule 5-facteurs (T0) — maintenance d'ancre",
                      ec4 < TOL_C4,
                      f"1/T0 = {T0_inv:.12f} ; écart ancre {ec4:.2e} (relatif) ; "
                      f"écart CODATA {gap_codata:.3e} (= précision du corpus, justifie TOL_HIT_PLUS)")

# ================================================================== FAMILLE A — TÉMOIN NÉGATIF
print()
print("[FAMILLE A — témoin négatif : registre vertex hérité (15 lectures, attendu 0/15 à 1e-4)]")
leg_a = abs(Ktilde_complex(0.5)) ** 2
c1_mere = 1.0 / math.gamma(1.0 + ALPHA)          # c_1 = 1/Gamma(1 + 1/phi)
c1_2 = 1.0 / math.gamma(1.0 + ALPHA / 2.0)       # c_{1/2}
leg_b = (c1_2 / c1_mere) ** 2
leg_c = 1.0                                       # transparence du mode 1/2
espaces = [
    ("(2pi)^4", (2.0 * math.pi) ** 4),
    ("pi^4", math.pi ** 4),
    ("8pi", 8.0 * math.pi),
    ("30", 30.0),
    ("(2pi)^3", (2.0 * math.pi) ** 3),
]
for tname, amp in (("a noyau ML B=1", leg_a), ("b mere c_{1/2}/c_1", leg_b), ("c transparence", leg_c)):
    for sname, norm in espaces:
        pred = norm / amp
        gap = abs(pred - ALPHA_INV_CODATA_2022) / ALPHA_INV_CODATA_2022
        fact = max(pred, ALPHA_INV_CODATA_2022) / min(pred, ALPHA_INV_CODATA_2022)
        famille_A.append({"famille": "A", "temps": tname, "espace": sname, "amplitude2": amp,
                          "norme": norm, "alpha_inv_pred": pred, "ecart_rel": gap, "facteur": fact})
        print(f"  ({tname[0]},{sname[:6]:6s}) |A|²={amp:.6f} norme={norm:10.4f} "
              f"-> alpha^-1 = {pred:13.6f}  écart = {gap:.3e}")

hits_A = [l for l in famille_A if l["ecart_rel"] < TOL_HIT]
best_A = min(famille_A, key=lambda l: l["facteur"])

c5_ok = (len(hits_A) == 0) and (abs(best_A["alpha_inv_pred"] - MEILLEURE_VERTEX_DEPOT) < TOL_V4)
ok_global &= controle("C5 reproduction du registre vertex (témoin négatif)",
                      c5_ok,
                      f"hits A = {len(hits_A)}/15 ; meilleur = ({best_A['temps'][0]},{best_A['espace']}) "
                      f"= {best_A['alpha_inv_pred']:.4f} (attendu 97,5115)")

# ================================================================== FAMILLE B — LECTURES INTÉGRALES
print()
print("[FAMILLE B — D_p = (1/pi)·int_0^oo |K~(w)|^p dw, p ∈ {1,2,3,4} — convergence machine d'abord]")


def Dp(p, xlo, xhi, n):
    """D_p par Simpson en espace ln (w = e^x) — intégrande |K~(w)|^p·w."""
    h = (xhi - xlo) / n
    s = 0.0
    for i in range(n + 1):
        x = xlo + i * h
        w = math.exp(x)
        val = (abs(Ktilde_complex(w)) ** p) * w
        if i == 0 or i == n:
            s += val
        elif i % 2 == 1:
            s += 4.0 * val
        else:
            s += 2.0 * val
    return s * h / 3.0 / math.pi


D_vals = {}
for p in (1, 2, 3, 4):
    v1 = Dp(p, -40.0, 40.0, 40000)
    v2 = Dp(p, -60.0, 60.0, 60000)
    v3 = Dp(p, -80.0, 80.0, 80000)
    rel = abs(v3 - v2) / max(1.0, abs(v3))
    conv = rel < TOL_CONV
    D_vals[p] = v3
    journal_B.append({"p": p, "domaine_40": v1, "domaine_60": v2, "domaine_80": v3,
                      "stabilite_relative": rel, "converge": conv})
    print(f"  D_{p}: [-40,40]={v1:.8f}  [-60,60]={v2:.8f}  [-80,80]={v3:.8f}  "
          f"stabilité={rel:.1e} -> {'CONVERGE' if conv else 'DIVERGENT'}")

print()
print("[FAMILLE B — les 8 candidats {D_p, 1/D_p}, tous rapportés]")
for p in (1, 2, 3, 4):
    conv = journal_B[p - 1]["converge"]
    for label, val in ((f"D_{p}", D_vals[p]), (f"1/D_{p}", 1.0 / D_vals[p])):
        gap = abs(val - ALPHA_INV_CODATA_2022) / ALPHA_INV_CODATA_2022
        fact = max(val, ALPHA_INV_CODATA_2022) / min(val, ALPHA_INV_CODATA_2022)
        famille_B.append({"famille": "B", "label": label, "p": p, "alpha_inv_pred": val,
                          "admissible": conv, "ecart_rel": gap, "facteur": fact,
                          "raison": "" if conv else "divergence démontrée machine (dépôt §3)"})
        print(f"  {label:6s} = {val:15.8f}  écart = {gap:.3e}  "
              f"{'ADMISSIBLE' if conv else 'écartée (divergence, dépôt §3)'}")

pool_B = [l for l in famille_B if l["admissible"]]

# ================================================================== FAMILLE C — CHAINE DÉRIVATIONNELLE
print()
print("[FAMILLE C — chaîne dérivationnelle : C1 ratio (108), C2 produit (108)]")

E_set = [
    (0.0, "0"), (1.0, "1"), (-1.0, "-1"), (2.0, "2"), (-2.0, "-2"),
    (3.0, "3"), (-3.0, "-3"), (4.0, "4"), (-4.0, "-4"),
    (1.0 / PHI, "1/phi"), (-1.0 / PHI, "-1/phi"), (-2.5, "-5/2"),
]
temoins = [
    (1.0, "1"),
    (math.exp(1.0 / PHI), "e^{1/phi}"),
    (math.exp(-1.0 / PHI), "e^{-1/phi}"),
    (55.0, "F10=55"),
    (123.0, "L10=123"),
    (1.0 / math.gamma(2.0 / PHI + 1.0), "Gamma(2/phi+1)"),
    (2.0 * PHI, "2phi"),
    (PHI ** 2, "phi^2"),
    (SQRT5, "sqrt5"),
]

inv_leg_a = 1.0 / leg_a
for route in ("C1", "C2"):
    print(f"  --- Route {route} ---")
    for ev, el in E_set:
        for mv, ml in temoins:
            f_val = PHI ** ev * mv
            if route == "C1":
                pred = (1.0 / ALPHA_W) * inv_leg_a * f_val
            else:
                pred = 1.0 / (ALPHA_W * ALPHA_S * f_val)
            gap = abs(pred - ALPHA_INV_CODATA_2022) / ALPHA_INV_CODATA_2022
            fact = max(pred, ALPHA_INV_CODATA_2022) / min(pred, ALPHA_INV_CODATA_2022)
            famille_C.append({"famille": route, "e": ev, "e_label": el, "m_label": ml, "f": f_val,
                              "alpha_inv_pred": pred, "ecart_rel": gap, "facteur": fact})
            print(f"  {route} e={el:6s} m={ml:15s} f={f_val:12.6f} -> "
                  f"alpha^-1 = {pred:12.6f}  écart = {gap:.3e}")

# ================================================================== CRITÈRE (figé au dépôt §4)
print()
print("[CRITÈRE — figé au dépôt §4]")

if (len(hits_A) != 0) or (abs(best_A["alpha_inv_pred"] - MEILLEURE_VERTEX_DEPOT) >= TOL_V4):
    verdict = "PIPELINE_EN_ECHEC [V4] — pas de verdict physique"
    exit_code = 1
else:
    pool = pool_B + famille_C
    hits7 = [l for l in pool if l["ecart_rel"] <= TOL_HIT_PLUS]
    hits = [l for l in pool if l["ecart_rel"] <= TOL_HIT]
    best = min(pool, key=lambda l: l["facteur"])
    best_label = best.get("label") or f"{best['famille']} e={best['e_label']} m={best['m_label']}"
    print(f"  pool de verdict (B admissibles + C) : {len(pool)} lectures")
    print(f"  lectures à {TOL_HIT_PLUS:.1e} : {len(hits7)}   lectures à {TOL_HIT:.1e} : {len(hits)}")
    print(f"  meilleure lecture : {best_label} -> {best['alpha_inv_pred']:.6f} "
          f"(facteur d'écart {best['facteur']:.4f})")

    # C6 — unicité (diagnostic, ne bloque jamais)
    if hits:
        ident = lambda l: json.dumps(l, sort_keys=True)
        hits_ids = {ident(l) for l in hits}
        twins = [l for l in pool
                 if ident(l) not in hits_ids
                 and min(abs(l["alpha_inv_pred"] - h["alpha_inv_pred"]) / h["alpha_inv_pred"]
                         for h in hits) < TOL_HIT]
        controle("C6 unicité (diagnostic)", True,
                 f"{len(hits)} hit(s) ; {len(twins)} jumeau(x) à < 1e-4 d'un hit")
    else:
        controle("C6 unicité (diagnostic)", True, "aucun hit → unicité non applicable")

    if hits7:
        verdict = "ALPHA_GRAMMAIRE_CONFIRME [T+]"
        exit_code = 0
    elif hits:
        verdict = "ALPHA_GRAMMAIRE_ADMISE [T]"
        exit_code = 0
    else:
        verdict = "ALPHA_HORS_GRAMMAIRE_STATIQUE [F]"
        exit_code = 1

# I5 — un seul contrôle bloquant en échec ⇒ REFUTE
if not ok_global and exit_code == 0:
    verdict = "REFUTE — contrôle bloquant en échec [I5]"
    exit_code = 1

print()
print("=" * 74)
print(f"  VERDICT : {verdict}")
print("=" * 74)

resultat = {
    "date_execution": datetime.now().isoformat(timespec="seconds"),
    "depot": {"fichier": "DEPOT_ALPHA_GRAMMAIRE_V0.md", "mtime": mtime},
    "controles": controles,
    "famille_A": famille_A,
    "famille_B_convergence": journal_B,
    "famille_B": famille_B,
    "famille_C": famille_C,
    "nb_lectures_total": len(famille_A) + len(famille_B) + len(famille_C),
    "verdict": verdict,
    "exit_code": exit_code,
}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "resultat_alpha_grammaire.json"), "w", encoding="utf-8") as fp:
    json.dump(resultat, fp, ensure_ascii=False, indent=1)
print("JSON consigné : resultat_alpha_grammaire.json")
sys.exit(exit_code)
