# -*- coding: utf-8 -*-
"""
VÉRIFICATION MACHINE — ASSAUT VERTEX SUR α (PISTE 1 : DENSITÉ SPECTRALE DU NOYAU DORÉ)
=====================================================================================
Dépôt daté AVANT exécution : DEPOT_ALPHA_VERTEX.md (2026-08-27)
Protocole : registre fermé de 15 lectures, zéro paramètre libre,
            un seul contrôle bloquant qui échoue ⇒ ALPHA_VERTEX_REFUTE (exit 1).

Sortie : resultat_alpha_vertex.json
"""

import cmath
import json
import math
import os
import sys
from datetime import datetime

# ------------------------------------------------------------------ constantes
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI
SQRT5 = math.sqrt(5.0)

ALPHA_INV_CODATA_2022 = 137.035999177   # cible principale (dépôt §3)
ALPHA_INV_CODATA_2018 = 137.035999084   # référence secondaire
TOL_HIT_PLUS = 2.355e-7                 # bat la formule 5-facteurs
TOL_HIT = 1.0e-4                        # barre pré-enregistrée du dépôt
TOL_ID = 1e-12
TOL_C2 = 1e-9
TOL_C3 = 1e-6

DEPOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DEPOT_ALPHA_VERTEX.md")

controles = []   # (nom, ok, detail)
lectures = []    # dict par lecture


def controle(nom, ok, detail):
    controles.append({"nom": nom, "ok": bool(ok), "detail": detail})
    print(("  [OK]  " if ok else "  [FAIL]") + f" {nom} : {detail}")
    return ok


# ------------------------------------------------------------------ noyau ML
def E_alpha_neg(x, alpha=ALPHA, kmax=400):
    """E_alpha(-x) par série entière (fiable ici : terme max O(1) pour x <= 8)."""
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
    """K~(omega) = (i omega)^{alpha-1} / ((i omega)^alpha + phi)  — branche principale."""
    z = 1j * omega
    return cmath.exp((alpha - 1.0) * cmath.log(z)) / (cmath.exp(alpha * cmath.log(z)) + PHI)


def Ktilde2_real(omega, alpha=ALPHA):
    """|K~(omega)|^2 forme réelle développée."""
    num = omega ** (2.0 * alpha - 2.0)
    den = omega ** (2.0 * alpha) + 2.0 * PHI * math.cos(math.pi * alpha / 2.0) * omega ** alpha + PHI ** 2
    return num / den


def L_num(sigma, alpha=ALPHA):
    """Intégrale directe int_0^oo e^{-sigma t} E_alpha(-phi t^alpha) dt, en 3 morceaux."""
    lam = PHI
    # morceau 1 : [0, 0.5] — double série (cusp t^alpha traité exactement)
    S1 = 0.0
    for j in range(45):
        aj = (-sigma) ** j / math.factorial(j)
        for k in range(140):
            ak = (-lam) ** k / math.gamma(alpha * k + 1.0)
            S1 += aj * ak * 0.5 ** (j + alpha * k + 1.0) / (j + alpha * k + 1.0)
    # morceau 2 : [0.5, 13.2] — Simpson direct (integrande lisse)
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


# ================================================================== PREAMBULE
print("=" * 74)
print("  ASSAUT VERTEX SUR alpha — PISTE 1 (densité spectrale du noyau doré)")
print("  Dépôt daté : DEPOT_ALPHA_VERTEX.md (2026-08-27) — avant exécution")
print("=" * 74)
print(datetime.now().isoformat(timespec="seconds"))
print()

ok_global = True

# -------------------------------------------------------------- C0 : dépôt + cibles
print("[CONTRÔLES BLOQUANTS]")
depot_ok = os.path.exists(DEPOT)
mtime = datetime.fromtimestamp(os.path.getmtime(DEPOT)).isoformat(timespec="seconds") if depot_ok else "absent"
ok_global &= controle("C0a dépôt présent", depot_ok, f"mtime = {mtime}")
ok_global &= controle("C0b identité d'or", abs(PHI * PHI - PHI - 1.0) < TOL_ID and abs(1.0 / PHI - (PHI - 1.0)) < 1e-15,
                      f"phi²=phi+1 ({abs(PHI * PHI - PHI - 1.0):.2e}) ; 1/phi = phi-1")

# -------------------------------------------------------------- C1 : transparence mode 1/2
ok_global &= controle("C1 phi + 1/phi = sqrt(5)",
                      abs(PHI + 1.0 / PHI - SQRT5) < TOL_ID,
                      f"écart = {abs(PHI + 1.0 / PHI - SQRT5):.2e}")

# -------------------------------------------------------------- C2 : coefficients mère vs corpus
c1 = 1.0 / math.gamma(1.0 + ALPHA)              # = 1/Gamma(phi)
c1_2 = 1.0 / math.gamma(1.0 + ALPHA / 2.0)      # = 1/Gamma(1 + 1/(2 phi))
c2_pub = 0.889630375                             # DETAIL_COEFFICIENTS_Cn.md (9 décimales)
c2_calc = 1.0 / math.gamma(2.0 / PHI + 1.0)
ok_global &= controle("C2 c2 = 1/Gamma(2/phi+1) = 0,889630375 (corpus)",
                      abs(c2_calc - c2_pub) < TOL_C2,
                      f"calc = {c2_calc:.9f} ; écart = {abs(c2_calc - c2_pub):.2e}")

# -------------------------------------------------------------- C3 : transformée de Laplace
c3_ok = True
c3_details = []
for sigma in (1.0, 2.0):
    ln, lf = L_num(sigma), L_closed(sigma)
    ec = abs(ln - lf)
    c3_ok &= ec < TOL_C3
    c3_details.append(f"sigma={sigma}: {ln:.12f} vs {lf:.12f} (écart {ec:.2e})")
ok_global &= controle("C3 Laplace formelle vs intégration temporelle directe", c3_ok, " ; ".join(c3_details))

# -------------------------------------------------------------- C3b : deux formes de |K~|²
c3b_ok = True
worst = 0.0
for om in (0.25, 0.5, 1.0, 2.0, 4.0):
    d = abs(abs(Ktilde_complex(om)) ** 2 - Ktilde2_real(om))
    worst = max(worst, d)
    c3b_ok &= d < TOL_ID
ok_global &= controle("C3b cohérence |K~(w)|² complexe vs réelle", c3b_ok, f"écart max = {worst:.2e}")

# ================================================================== LECTURES
print()
print("[LECTURES PRÉ-ENREGISTRÉES]  alpha^-1 = norme_espace / |amplitude_temps|²")
leg_a = abs(Ktilde_complex(0.5)) ** 2
leg_b = (c1_2 / c1) ** 2
leg_c = 1.0  # transparence du mode 1/2 (C1)
espaces = [
    ("(2pi)^4", (2.0 * math.pi) ** 4),
    ("pi^4", math.pi ** 4),
    ("8pi", 8.0 * math.pi),
    ("30 = (sqrt2.sqrt3.sqrt5)^2", 30.0),
    ("(2pi)^3", (2.0 * math.pi) ** 3),
]
for tname, amp in (("a ML B=1", leg_a), ("b mere c_{1/2}/c_1", leg_b), ("c transparence", leg_c)):
    for sname, norm in espaces:
        pred = norm / amp
        gap = abs(pred - ALPHA_INV_CODATA_2022) / ALPHA_INV_CODATA_2022
        lectures.append({"temps": tname, "espace": sname, "amplitude2": amp,
                         "norme": norm, "alpha_inv_pred": pred,
                         "ecart_rel": gap, "facteur": max(pred, ALPHA_INV_CODATA_2022) / min(pred, ALPHA_INV_CODATA_2022)})
        print(f"  ({tname[0]},{sname[:6]:6s}) |A|²={amp:.6f} norme={norm:10.4f} "
              f"-> alpha^-1 = {pred:13.6f}  écart = {gap:.3e}")

# ================================================================== CRITÈRE
print()
print("[CRITÈRE — figé au dépôt §3]")
hits = [l for l in lectures if l["ecart_rel"] < TOL_HIT]
hits7 = [l for l in lectures if l["ecart_rel"] < TOL_HIT_PLUS]
meilleure = min(lectures, key=lambda l: l["facteur"])
print(f"  lectures à {TOL_HIT_PLUS:.1e} : {len(hits7)}   lectures à {TOL_HIT:.1e} : {len(hits)}")
print(f"  meilleure lecture : ({meilleure['temps'][0]},{meilleure['espace']}) "
      f"-> {meilleure['alpha_inv_pred']:.4f} (facteur d'écart {meilleure['facteur']:.3f})")

if len(hits7) == 1:
    verdict = "ALPHA_VERTEX_CONFIRME [T+]"
elif len(hits) == 1:
    verdict = "ALPHA_VERTEX_CONFIRME [T]"
elif len(hits) == 0:
    verdict = "ALPHA_VERTEX_REFUTE"
else:
    verdict = "ALPHA_VERTEX_REFUTE"

# ================================================================== DIAGNOSTIC (non bloquant)
print()
print("[DIAGNOSTIC — norme d'espace requise, voisinage Fibonacci/Lucas]")
fibs = [1, 1]
while fibs[-1] < 4000:
    fibs.append(fibs[-1] + fibs[-2])
lucs = [1, 3]
while lucs[-1] < 4000:
    lucs.append(lucs[-1] + lucs[-2])
diagnostics = []
for tname, amp in (("a", leg_a), ("b", leg_b), ("c", leg_c)):
    req = ALPHA_INV_CODATA_2022 * amp
    nf = min(fibs, key=lambda v: abs(v - req))
    nl = min(lucs, key=lambda v: abs(v - req))
    gf, gl = abs(nf - req) / nf, abs(nl - req) / nl
    diagnostics.append({"patte": tname, "norme_requise": req, "fib_proche": nf, "ecart_fib": gf,
                        "lucas_proche": nl, "ecart_lucas": gl})
    print(f"  patte ({tname}) : norme requise = {req:.4f}  -> Fib {nf} (écart {gf:.2e}) ; Lucas {nl} (écart {gl:.2e})")

# ================================================================== FRÈRES (annexe)
alpha_W = 1.0 / 30.0
alpha_S = 1.0 / (2.0 * PHI ** 3)
idx_c30 = 2 * 5 + 3  # 3e patte temps (c) x 5 espaces, 4e norme (30)
brothers = {
    "alpha_W_corpus": alpha_W,
    "lecture_c_iv_alpha_inv_pred": lectures[idx_c30]["alpha_inv_pred"],
    "alpha_W_match_exact": abs(lectures[idx_c30]["alpha_inv_pred"] - 1.0 / alpha_W) < 1e-12,
    "alpha_S_corpus": alpha_S,
}
print()
print("[FRÈRES — juges croisés (annexe du dépôt)]")
print(f"  alpha_W = 1/30 = {alpha_W:.6f} : lecture (c,30) predit alpha^-1 = {lectures[idx_c30]['alpha_inv_pred']:.6f}"
      f"  -> {'EXACT' if brothers['alpha_W_match_exact'] else 'non'}")
print(f"  alpha_S = 1/(2phi^3) = {alpha_S:.6f} : aucune lecture du registre (mémoire de forme, hors verdict)")

# ================================================================== VERDICT
if not ok_global:
    verdict = "ALPHA_VERTEX_REFUTE"
print()
print("=" * 74)
print(f"  VERDICT : {verdict}")
print("=" * 74)

resultat = {
    "date": datetime.now().isoformat(timespec="seconds"),
    "depot": "DEPOT_ALPHA_VERTEX.md",
    "verdict": verdict,
    "controles": controles,
    "lectures": lectures,
    "hits_1e-4": len(hits),
    "hits_2.355e-7": len(hits7),
    "meilleure": meilleure,
    "diagnostics": diagnostics,
    "freres": brothers,
    "cibles": {"codata_2022": ALPHA_INV_CODATA_2022, "codata_2018": ALPHA_INV_CODATA_2018},
    "tolerances": {"hit": TOL_HIT, "hit_plus": TOL_HIT_PLUS, "C2": TOL_C2, "C3": TOL_C3},
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultat_alpha_vertex.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=2)
print(f"  JSON : {out}")

sys.exit(0 if verdict.startswith("ALPHA_VERTEX_CONFIRME") else 1)
