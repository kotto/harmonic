# -*- coding: utf-8 -*-
"""
VERIF OYIBO CONSERVATION V0 — la chaîne GAGUT déroulée maillon par maillon.

Dépôt fermé ex ante : DEPOT_OYIBO_CONSERVATION_V0.md (chaîne CH-G1..CH-G6,
objets O1..O8, barres O8, contrôles bloquants §3, échelle de verdicts §4 — gelés).

Sortie : resultat_oyibo_conservation_v0.json — toutes les lectures (I3),
y compris les quasi-échecs ; verdict selon l'échelle gelée ; exit code.

Règle unique (§3) : UN SEUL contrôle en échec ⟹ V4 REFUTE, exit 1, aucun sauvetage.
I5 : aucune modification du dépôt ni du registre après exécution.
"""
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone

import mpmath
from mpmath import mp, mpf, mpc, workdps

# Précision ambiante fixée AVANT toute construction de constante : sinon PHI et le
# registre O6 sont bâtis au défaut (15 chiffres) et les candidats se retrouvent
# rationalisés (la CF du flottement termine ⟹ ν = 0, lecture fausse). Les routes
# gelées O7 re-wrapent chacune leur propre workdps (260/120/80).
mp.dps = 50

BASE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.join(BASE, "DEPOT_OYIBO_CONSERVATION_V0.md")
SORTIE = os.path.join(BASE, "resultat_oyibo_conservation_v0.json")

# ============================================================================
# O1..O8 — objets fermés (hérités, non modifiables — I2 : zéro paramètre libre)
# ============================================================================
SQRT5 = mp.sqrt(5)
PHI = (1 + SQRT5) / 2                        # O1
ALPHA = 1 / PHI                              # O1 : α = 1/φ
LAMBDA_PHI = PHI                             # O3 : λ = α/(1−α) = φ (Violet A)

DPS_ML = 260                                 # O7 : série de Mittag-Leffler
DPS_WIMAN = 120                              # O7 : série de Wiman
DPS_CF = 80                                  # O7 : fractions continues
N_CONV = 50                                  # O7 : convergents
T_RATIO = [mpf(10) ** 3, mpf(3) * 10 ** 4]   # O7 : fenêtres de ratio (B3)
LAMBDAS_B3 = [mpf(2), PHI]                   # O7 : λ ∈ {2, φ} (B3)
LAMBDAS_B1 = [mpf(2), PHI, mpf(10)]          # B1 : λ ∈ {2, φ, 10}
S_B1 = [mpf("0.3"), ALPHA, mpf(1), mpf("1.7")]   # B1 : s ∈ {0.3, 1/φ, 1, 1.7}
X_B1 = [mpf("0.5"), mpf(1), mpf(2), mpf(4)]      # B1 : x ∈ {0.5, 1, 2, 4}
X_B2 = [mpf("0.5"), mpf(2), mpf(4)]              # B2 : témoin négatif
OMEGA_C2 = [mpf("0.1"), mpf("0.5"), mpf(1), 1 / PHI, mpf(2), mpf(10)]  # C2
Z_C6 = [mpf(31), mpf(33)]                    # C6 : points de recouvrement

# Registre O6 — 9 candidats, tous irrationnels ; rationnels exclus (CF termine)
REGISTRE = [
    ("1/phi", 1 / PHI),
    ("1/sqrt2", 1 / mp.sqrt(2)),
    ("1/pi", 1 / mp.pi),
    ("1/e", 1 / mp.e),
    ("1/sqrt3", 1 / mp.sqrt(3)),
    ("1/sqrt5", 1 / mp.sqrt(5)),
    ("frac_sqrt101", mp.sqrt(101) - 10),
    ("frac_sqrt103", mp.sqrt(103) - 10),
    ("frac_sqrt107", mp.sqrt(107) - 10),
]

# O8 — barres gelées
TOL_HURWITZ_HIT = mpf(10) ** -6
TOL_UNICITE = mpf(10) ** -3
TOL_SLOPE = mpf("5e-3")
TOL_RATE = mpf("0.1")            # 10 % rel (B3)
TOL_NOYAU = mpf(10) ** -12       # C2, D1
TOL_PUISSANCE = mpf(10) ** -12   # B1
TOL_ANCRE = mpf(10) ** -9        # énergies (Famille A)
TOL_CALIB = mpf(10) ** -12       # C6
TOL_C1 = mpf(10) ** -15          # C1
TOL_CK = mpf(10) ** -15          # D2 (c_k)
TOL_TEMOIN = mpf("0.1")          # B2 : déviation doit dépasser 0.1

MARKOV = 1 / mp.sqrt(5)              # O5 : 1/√5
MARKOV_SQRT2 = 1 / (2 * mp.sqrt(2))  # O5 : 1/(2√2)

# O4 — coefficients en forme close : a_k = (−1)^{k+1} φ^{−k} / Γ(1−αk) ; ρ_k = a_k/a₁
A1 = PHI ** (-1) / mp.gamma(1 - ALPHA)
A2 = -PHI ** (-2) / mp.gamma(1 - 2 * ALPHA)
RHO2 = A2 / A1


def now_iso(dt=None):
    d = dt or datetime.now(timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


LECTURES = {"controles": {}, "famille_A": {}, "famille_B": {}, "famille_C": {}, "famille_D": {}}


def fnum(x):
    return float(x)


# ============================================================================
# O2 — noyau projecteur K̂, double route (héritage jauge C1)
# ============================================================================
def khat_complexe(omega):
    """K̂(ω) = φ/((iω)^α + φ), branche principale : (iω)^α = ω^α·e^{i·sign(ω)·πα/2}."""
    w = mpf(omega)
    if w == 0:
        return mpf(1)
    phase = (1 if w > 0 else -1) * mp.pi * ALPHA / 2
    iw_alpha = w ** ALPHA * mpc(mp.cos(phase), mp.sin(phase))
    return PHI / (PHI + iw_alpha)


def khat2_reel(omega):
    """|K̂(ω)|² forme réelle : φ²/(φ² + 2φ·cos(πα/2)·ω^α + ω^{2α})."""
    w = mpf(omega)
    if w == 0:
        return mpf(1)
    wa = abs(w) ** ALPHA   # |ω|^α : la forme réelle est paire (ω^α signé donnerait
    return PHI ** 2 / (PHI ** 2 + 2 * PHI * mp.cos(mp.pi * ALPHA / 2) * wa + wa ** 2)


# ============================================================================
# O3/O4 — noyau mémoire ABC : K(t) = E_α(−λ·t^α), deux routes
# ============================================================================
def e_alpha_serie(alpha, z, dps=DPS_ML, kmax=3000):
    """E_α(−z) — série définissante de Mittag-Leffler Σ(−z)^k/Γ(αk+1), dps 260.

    Retourne (valeur, ordre de troncature, pic |terme|) — le pic consigné
    mesure la perte de chiffres par cancellation.
    """
    with workdps(dps + 20):
        s = mpf(1)
        peak = mpf(1)
        k_stop = 0
        for k in range(1, kmax + 1):
            terme = (-mpf(z)) ** k / mp.gamma(alpha * k + 1)
            if abs(terme) > peak:
                peak = abs(terme)
            s += terme
            k_stop = k
            if k > 30 and abs(terme) < mpf(10) ** (-(dps - 15)):
                break
        return +s, k_stop, float(peak)


def e_alpha_wiman(alpha, z, dps=DPS_WIMAN, kmax=6000):
    """E_α(−z) — série algébrique de Wiman Σ(−1)^{k+1} z^{−k}/Γ(1−αk), dps 120.

    Série asymptotique (même pour α > 1/2) : troncature optimale — arrêt dès
    que |t_k| recommence à croître, ou que |t_k| < 10^{−(dps−10)}.
    Route de réflexion : 1/Γ(1−x) = Γ(x)·sin(πx)/π.
    """
    with workdps(dps + 30):
        s = mpf(0)
        prev = None
        peak = mpf(0)
        k_stop = 0
        for k in range(1, kmax + 1):
            ak = alpha * k
            terme = (1 if k % 2 == 1 else -1) * mpf(z) ** (-k) * mp.gamma(ak) * mp.sin(mp.pi * ak) / mp.pi
            if abs(terme) > peak:
                peak = abs(terme)
            if k > 20 and abs(terme) > abs(prev):
                k_stop = k - 1
                break
            s += terme
            prev = terme
            k_stop = k
            if abs(terme) < mpf(10) ** (-(dps - 10)):
                break
        return +s, k_stop, float(peak)


def noyau_abc(t, alpha=ALPHA, lam=LAMBDA_PHI):
    """K(t) = E_α(−λ·t^α) — route Wiman (dps 120, troncature optimale)."""
    z = mpf(lam) * mpf(t) ** alpha
    return e_alpha_wiman(alpha, z, dps=DPS_WIMAN)


# ============================================================================
# O5 — discriminateur de Hurwitz : ν_n(x) = min sur les n premiers convergents
# ============================================================================
def convergents(x, n, dps=DPS_CF):
    """Convergents (p_k, q_k) de la fraction continue de x, k = 0..n−1, dps 80."""
    with workdps(dps):
        xv = mpf(x)
        cf = []
        for _ in range(n + 2):
            a = int(mp.floor(xv))
            cf.append(a)
            frac = xv - a
            if frac == 0:
                break
            xv = 1 / frac
        p_nm2, p_nm1 = 0, 1
        q_nm2, q_nm1 = 1, 0
        out = []
        for a in cf[:n]:
            p = a * p_nm1 + p_nm2
            q = a * q_nm1 + q_nm2
            out.append((p, q))
            p_nm2, p_nm1 = p_nm1, p
            q_nm2, q_nm1 = q_nm1, q
        return out


def nu_n(x, n=N_CONV):
    """ν_n(x) = min sur les n premiers convergents de q·|q·x − p|."""
    convs = convergents(x, n)
    xv = mpf(x)
    best = None
    for (p, q) in convs:
        if q == 0:
            continue
        val = mpf(q) * abs(mpf(q) * xv - mpf(p))
        if best is None or val < best:
            best = val
    return best, convs


# ============================================================================
# Famille A — RK4, l'ancre Noether (3 systèmes)
# ============================================================================
def rk4_step(x, v, dt, acc):
    k1x = v
    k1v = acc(x)
    k2x = v + dt / 2 * k1v
    k2v = acc(x + dt / 2 * k1x)
    k3x = v + dt / 2 * k2v
    k3v = acc(x + dt / 2 * k2x)
    k4x = v + dt * k3v
    k4v = acc(x + dt * k3x)
    return (x + dt / 6 * (k1x + 2 * k2x + 2 * k3x + k4x),
            v + dt / 6 * (k1v + 2 * k2v + 2 * k3v + k4v))


def run_oscillateur(T=mpf(50), dt=mpf("1e-3")):
    acc = lambda x: -x
    x, v = mpf(1), mpf(0)

    def E(x, v):
        return mpf("0.5") * v ** 2 + mpf("0.5") * x ** 2
    e0 = E(x, v)
    n = int(T / dt)
    x0 = x
    xr = mpf(0)
    for _ in range(n):
        x, v = rk4_step(x, v, dt, acc)
        xr = max(xr, abs(x - x0))
    return abs(E(x, v) - e0) / abs(e0), e0, xr


def run_pendule(T=mpf(50), dt=mpf("1e-3")):
    acc = lambda x: -mp.sin(x)
    x, v = mpf(1), mpf(0)

    def E(x, v):
        return mpf("0.5") * v ** 2 + 1 - mp.cos(x)
    e0 = E(x, v)
    n = int(T / dt)
    x0 = x
    xr = mpf(0)
    for _ in range(n):
        x, v = rk4_step(x, v, dt, acc)
        xr = max(xr, abs(x - x0))
    return abs(E(x, v) - e0) / abs(e0), e0, xr


def run_kepler(T=mpf(10), dt=mpf("1e-4")):
    # e = 0.6 : périhélie r0 = a(1−e) = 0.4, v0 = √(GM(1+e)/(a(1−e))) = 2 (GM=1, a=1)
    s = [mpf("0.4"), mpf(0), mpf(0), mpf(2)]

    def derivs(st):
        x, y, vx, vy = st
        r = mp.sqrt(x * x + y * y)
        a = -1 / (r ** 3)
        return [vx, vy, a * x, a * y]

    def E(st):
        x, y, vx, vy = st
        r = mp.sqrt(x * x + y * y)
        return mpf("0.5") * (vx * vx + vy * vy) - 1 / r

    def L(st):
        x, y, vx, vy = st
        return x * vy - y * vx
    e0, l0 = E(s), L(s)
    n = int(T / dt)
    r0 = mp.sqrt(s[0] ** 2 + s[1] ** 2)
    xr = mpf(0)
    for _ in range(n):
        k1 = derivs(s)
        s2 = [s[i] + dt / 2 * k1[i] for i in range(4)]
        k2 = derivs(s2)
        s3 = [s[i] + dt / 2 * k2[i] for i in range(4)]
        k3 = derivs(s3)
        s4 = [s[i] + dt * k3[i] for i in range(4)]
        k4 = derivs(s4)
        s = [s[i] + dt / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) for i in range(4)]
        r = mp.sqrt(s[0] ** 2 + s[1] ** 2)
        xr = max(xr, abs(r - r0))
    return abs(E(s) - e0) / abs(e0), abs(L(s) - l0) / abs(l0), e0, xr


# ============================================================================
# EXÉCUTION
# ============================================================================
def main():
    t0_wall = time.time()
    t_exec_iso = now_iso()

    LECTURES["controles"].clear()
    LECTURES["famille_A"].clear()
    LECTURES["famille_B"].clear()
    LECTURES["famille_C"].clear()
    LECTURES["famille_D"].clear()

    # ---- C0a : mtime(dépôt) < heure d'exécution ----
    mtime_depot = os.path.getmtime(DEPOT)
    c0a_passe = mtime_depot < t0_wall
    LECTURES["controles"]["C0a"] = {
        "definition": "mtime(DEPOT_OYIBO_CONSERVATION_V0.md) < heure d'exécution",
        "mtime_depot_utc": now_iso(datetime.fromtimestamp(mtime_depot, tz=timezone.utc)),
        "heure_execution_utc": t_exec_iso,
        "passe": bool(c0a_passe),
    }

    # ---- C1 : fermeture algébrique (barre 1e-15) ----
    d1 = abs(PHI ** 2 - (PHI + 1))
    d2 = abs(PHI * (1 / PHI) - 1)
    LECTURES["controles"]["C1"] = {
        "definition": "φ² = φ+1 ; φ·φ⁻¹ = 1 (barre 1e-15)",
        "lectures": [
            {"nom": "phi^2 - (phi+1)", "valeur": fnum(d1), "barre": fnum(TOL_C1), "passe": bool(d1 <= TOL_C1)},
            {"nom": "phi*(1/phi) - 1", "valeur": fnum(d2), "barre": fnum(TOL_C1), "passe": bool(d2 <= TOL_C1)},
        ],
        "passe": bool(d1 <= TOL_C1 and d2 <= TOL_C1),
    }

    # ---- C2 : K̂ double route (barre 1e-12), ω ∈ {0.1, 0.5, 1, 1/φ, 2, 10} ± ----
    lec_c2 = []
    c2_ok = True
    for w in OMEGA_C2:
        for sgn in (1, -1):
            omega = sgn * w
            mod2_cplx = abs(khat_complexe(omega)) ** 2
            mod2_reel = khat2_reel(omega)
            dev = abs(mod2_cplx - mod2_reel)
            ok = dev <= TOL_NOYAU
            c2_ok = c2_ok and ok
            lec_c2.append({"omega": fnum(omega), "valeur": fnum(dev), "barre": fnum(TOL_NOYAU), "passe": bool(ok)})
    LECTURES["controles"]["C2"] = {
        "definition": "K̂ double route (héritage jauge C1) : module complexe vs forme réelle, barre 1e-12",
        "lectures": lec_c2,
        "passe": bool(c2_ok),
    }

    # ---- C5 : λ = α/(1−α) = φ ; c_k = 1/Γ(k/φ+1), k ≤ 6 (barres 1e-12 / 1e-15) ----
    # (identique à D1/D2 — évalué une fois, consigné dans les deux familles)
    lambda_calc = ALPHA / (1 - ALPHA)
    d1_lambda = abs(lambda_calc - PHI)
    lec_ck = []
    ck_ok = True
    for k in range(1, 7):
        x = mpf(k) * ALPHA
        c_direct = 1 / mp.gamma(x + 1)
        c_recur = 1 / (x * mp.gamma(x))          # Γ(x+1) = x·Γ(x) — route indépendante
        dev = abs(c_direct - c_recur)
        ok = dev <= TOL_CK
        ck_ok = ck_ok and ok
        lec_ck.append({"k": k, "c_k": fnum(c_direct), "dev_ecarts": fnum(dev), "barre": fnum(TOL_CK), "passe": bool(ok)})
    c5_ok = d1_lambda <= TOL_NOYAU and ck_ok
    LECTURES["controles"]["C5"] = {
        "definition": "λ = α/(1−α) = φ (barre 1e-12) ; c_k = 1/Γ(k/φ+1), k ≤ 6 (barre 1e-15)",
        "lambda_ecart": fnum(d1_lambda),
        "lectures": lec_ck,
        "passe": bool(c5_ok),
    }

    # ---- C6 : calibrage série ↔ Wiman aux points z ∈ {31, 33} (barre 1e-12) ----
    lec_c6 = []
    c6_ok = True
    for z in Z_C6:
        e_ml, k_ml, pic_ml = e_alpha_serie(ALPHA, z)
        e_w, k_w, pic_w = e_alpha_wiman(ALPHA, z, kmax=800)
        dev = abs(e_ml - e_w) / abs(e_ml)
        ok = dev <= TOL_CALIB
        c6_ok = c6_ok and ok
        lec_c6.append({"z": fnum(z), "valeur": fnum(dev), "barre": fnum(TOL_CALIB), "passe": bool(ok),
                       "E_serie_ml": fnum(e_ml), "E_wiman": fnum(e_w),
                       "ordre_troncature": {"ml": k_ml, "wiman": k_w}, "pic_terme_ml": pic_ml})
    LECTURES["controles"]["C6"] = {
        "definition": "calibrage série (ML, dps 260) ↔ Wiman (dps 120), z ∈ {31, 33}, barre 1e-12",
        "lectures": lec_c6,
        "passe": bool(c6_ok),
    }

    # ========================================================================
    # FAMILLE A — CH-G1, l'ancre Noether (barre 1e-9, impossibilité signal)
    # ========================================================================
    drift_o, e0_o, xr_o = run_oscillateur()
    drift_p, e0_p, xr_p = run_pendule()
    drift_k, drift_lk, e0_k, xr_k = run_kepler()
    a_ok = drift_o <= TOL_ANCRE and drift_p <= TOL_ANCRE and drift_k <= TOL_ANCRE
    LECTURES["famille_A"] = {
        "definition": "CH-G1 : 3 systèmes lagrangiens (RK4), dérive relative d'énergie ≤ 1e-9",
        "lectures": [
            {"nom": "A1 oscillateur x''=-x, T=50, dt=1e-3, x0=1, v0=0", "derive": fnum(drift_o),
             "E0": fnum(e0_o), "non_degenere": bool(xr_o > mpf("0.1")), "passe": bool(drift_o <= TOL_ANCRE)},
            {"nom": "A2 pendule x''=-sin x, T=50, dt=1e-3, x0=1, v0=0", "derive": fnum(drift_p),
             "E0": fnum(e0_p), "non_degenere": bool(xr_p > mpf("0.1")), "passe": bool(drift_p <= TOL_ANCRE)},
            {"nom": "A3 Kepler e=0.6, T=10, dt=1e-4, r0=0.4, v0=2 (GM=1)", "derive_energie": fnum(drift_k),
             "derive_moment": fnum(drift_lk), "E0": fnum(e0_k), "non_degenere": bool(xr_k > mpf("0.1")),
             "passe": bool(drift_k <= TOL_ANCRE)},
        ],
        "passe": bool(a_ok),
    }

    # ========================================================================
    # FAMILLE B — CH-G2/CH-G5 : l'échelle et sa réalisation (8 lectures)
    # ========================================================================
    # B1 — 48 lectures : F(x) = x^{−s} exacte
    lec_b1 = []
    b1_ok = True
    for s in S_B1:
        for x in X_B1:
            for lam in LAMBDAS_B1:
                F_x = mpf(x) ** (-s)
                dev = abs((mpf(lam) * mpf(x)) ** (-s) - mpf(lam) ** (-s) * F_x) / F_x
                ok = dev <= TOL_PUISSANCE
                b1_ok = b1_ok and ok
                lec_b1.append({"s": fnum(s), "x": fnum(x), "lambda": fnum(lam),
                               "valeur": fnum(dev), "barre": fnum(TOL_PUISSANCE), "passe": bool(ok)})
    LECTURES["famille_B"]["B1"] = {
        "definition": "48 lectures : |F(λx) − λ^{−s}F(x)|/F(x) ≤ 1e-12 (CH-G2)",
        "lectures": lec_b1,
        "passe": bool(b1_ok),
    }

    # B2 — témoin négatif : e^{−x} N'EST pas une loi de puissance (déviation > 0.1)
    F_exp = lambda x: mp.e ** (-mpf(x))
    s_star = -mp.log(F_exp(2) / F_exp(1)) / mp.log(2)      # ajustement ex ante, x=1, λ=2
    deux_pow = mpf(2) ** (-s_star)
    lec_b2 = []
    b2_ok = True
    for x in X_B2:
        dev = abs(F_exp(2 * x) / F_exp(x) - deux_pow)
        ok = dev > TOL_TEMOIN
        b2_ok = b2_ok and ok
        lec_b2.append({"x": fnum(x), "valeur": fnum(dev), "barre": "> 0.1", "passe": bool(ok)})
    LECTURES["famille_B"]["B2"] = {
        "definition": "témoin négatif e^{−x} : déviation > 0.1, sinon la lecture ne discrimine pas → V4",
        "s_etoile": fnum(s_star),
        "lectures": lec_b2,
        "passe": bool(b2_ok),
    }

    # B3 — la convergence déposée (le cœur) : r vs δ_pred, 10 % rel + décroissance
    lec_b3 = []
    b3_ok = True
    for lam in LAMBDAS_B3:
        r_vals = {}
        for t in T_RATIO:
            K_lt, k1, _ = noyau_abc(mpf(lam) * mpf(t))
            K_t, k2, _ = noyau_abc(mpf(t))
            r = K_lt / (mpf(lam) ** (-ALPHA) * K_t) - 1
            delta = RHO2 * (mpf(lam) ** (-ALPHA) - 1) * mpf(t) ** (-ALPHA)
            ecart = abs(r - delta) / abs(delta)
            ok = ecart <= TOL_RATE
            b3_ok = b3_ok and ok
            r_vals[fnum(t)] = fnum(r)
            lec_b3.append({"lambda": fnum(lam), "t": fnum(t), "r": fnum(r), "delta_pred": fnum(delta),
                           "ecart_rel": fnum(ecart), "barre": "10% rel", "passe": bool(ok),
                           "ordre_troncature": {"K(λt)": k1, "K(t)": k2}})
        dec = abs(r_vals[fnum(T_RATIO[1])]) < abs(r_vals[fnum(T_RATIO[0])])
        b3_ok = b3_ok and dec
        lec_b3.append({"lambda": fnum(lam), "lecture": "|r| décroît de t=1e3 à t=3e4",
                       "ratio": fnum(abs(r_vals[fnum(T_RATIO[1])]) / abs(r_vals[fnum(T_RATIO[0])])),
                       "passe": bool(dec)})
    LECTURES["famille_B"]["B3"] = {
        "definition": "|r − δ_pred| ≤ 0.1·|δ_pred| sur (λ,t) ∈ {2,φ}×{1e3,3e4} et |r| décroît",
        "lectures": lec_b3,
        "passe": bool(b3_ok),
    }

    # B4 — l'exposant lu : pente log-log de K sur [1e3, 3e4], 20 points
    ts = [mpf(10) ** 3 * (mpf(30) ** (mpf(i) / 19)) for i in range(20)]
    lts = [mp.log(t) for t in ts]
    lKs = [mp.log(noyau_abc(t)[0]) for t in ts]
    n = 20
    mx = sum(lts) / n
    my = sum(lKs) / n
    pente = sum((lts[i] - mx) * (lKs[i] - my) for i in range(n)) / sum((lts[i] - mx) ** 2 for i in range(n))
    ecart_pente = abs(pente + ALPHA)
    LECTURES["famille_B"]["B4"] = {
        "definition": "pente log-log de K sur [1e3, 3e4], 20 pts : |pente + 1/φ| ≤ 5e-3",
        "pente": fnum(pente), "ecart": fnum(ecart_pente), "barre": fnum(TOL_SLOPE), "passe": bool(ecart_pente <= TOL_SLOPE),
    }

    # ========================================================================
    # FAMILLE C — CH-G4, le discriminateur de Hurwitz (10 lectures)
    # ========================================================================
    table_nu = []
    nu_vals = {}
    for (nom, x) in REGISTRE:
        val, convs = nu_n(x)
        nu_vals[nom] = val
        table_nu.append({"candidat": nom, "nu50": fnum(val)})
    c3a_dev = abs(nu_vals["1/phi"] - MARKOV)
    c3a_ok = c3a_dev <= TOL_HURWITZ_HIT
    c3b_dev = abs(nu_vals["1/sqrt2"] - MARKOV_SQRT2)
    c3b_ok = c3b_dev <= TOL_HURWITZ_HIT
    max_rival = max(v for (k, v) in nu_vals.items() if k != "1/phi")
    c4_ok = max_rival < MARKOV - TOL_UNICITE
    LECTURES["famille_C"] = {
        "definition": "CH-G4 : table ν50 (9 candidats), hit doré 1/√5, ancre 1/(2√2), unicité",
        "table": table_nu,
        "C3a": {"nom": "|ν50(1/φ) − 1/√5|", "valeur": fnum(c3a_dev), "barre": fnum(TOL_HURWITZ_HIT), "passe": bool(c3a_ok)},
        "C3b": {"nom": "|ν50(1/√2) − 1/(2√2)|", "valeur": fnum(c3b_dev), "barre": fnum(TOL_HURWITZ_HIT), "passe": bool(c3b_ok)},
        "C4": {"nom": "max(non-dorés) < 1/√5 − 1e-3", "valeur": fnum(max_rival), "barre": fnum(MARKOV - TOL_UNICITE), "passe": bool(c4_ok)},
        "passe": bool(c3a_ok and c3b_ok and c4_ok),
    }

    # ========================================================================
    # FAMILLE D — CH-G5/CH-G6 : la boucle et le lignage (3 lectures)
    # ========================================================================
    LECTURES["famille_D"] = {
        "definition": "CH-G5/G6 : taux de mémoire (D1), coefficients (D2), couplage consigné (D3)",
        "D1": {"nom": "|α/(1−α) − φ|", "valeur": fnum(d1_lambda), "barre": fnum(TOL_NOYAU), "passe": bool(d1_lambda <= TOL_NOYAU)},
        "D2": {"nom": "c_k = 1/Γ(k/φ+1), k=1..6 (cohérence récurrence Γ(x+1)=xΓ(x))",
               "lectures": lec_ck, "passe": bool(ck_ok)},
        "D3": {"nom": "couplage D^{1/φ} = G", "statut": "[P] — appui machine, aucune revendication nouvelle (I4)", "passe": True},
        "passe": bool(d1_lambda <= TOL_NOYAU and ck_ok),
    }

    # ========================================================================
    # VERDICT (échelle gelée §4)
    # ========================================================================
    echecs = []
    for cid in ("C0a", "C1", "C2", "C5", "C6"):
        if not LECTURES["controles"][cid]["passe"]:
            echecs.append(f"controle:{cid}")
    if not LECTURES["famille_A"]["passe"]:
        echecs.append("famille_A:impossibilite_signal")
    for bid in ("B1", "B2"):
        if not LECTURES["famille_B"][bid]["passe"]:
            echecs.append(f"famille_B:{bid}")
    if not LECTURES["famille_C"]["passe"]:
        echecs.append("famille_C:C3a_C3b_C4")
    if not LECTURES["famille_D"]["passe"]:
        echecs.append("famille_D")
    b34 = (LECTURES["famille_B"]["B3"]["passe"], LECTURES["famille_B"]["B4"]["passe"])

    if echecs:
        verdict = {"code": "V4", "nom": "REFUTE",
                   "condition": "tout contrôle §3 en échec (un échec de C3/C4 est un impossibilité signal)",
                   "echecs": echecs, "exit_code": 1}
    elif not (b34[0] and b34[1]):
        manque = [b for (b, ok) in zip(("B3", "B4"), b34) if not ok]
        verdict = {"code": "V2", "nom": "CHAINE_CONFIRMEE_SANS_LA_REALISATION",
                   "condition": "contrôles §3 ✓ mais B3 ou B4 en échec : le noyau ABC ne porte pas l'invariance à ces barres",
                   "echecs": [f"famille_B:{m}" for m in manque], "exit_code": 0}
    else:
        verdict = {"code": "V+", "nom": "CHAINE_GAGUT_HURWITZ_CONFIRMEE",
                   "condition": "tous les contrôles §3 ✓, Famille A ✓, B3 ✓, B4 ✓ (CH-G3 consigné [P])",
                   "echecs": [], "exit_code": 0}

    resultat = {
        "meta": {
            "depot": "DEPOT_OYIBO_CONSERVATION_V0.md",
            "script": "verif_oyibo_conservation_v0.py",
            "sortie": "resultat_oyibo_conservation_v0.json",
            "python": sys.version.split()[0],
            "mpmath": mpmath.__version__,
            "plateforme": platform.platform(),
            "mtime_depot_utc": LECTURES["controles"]["C0a"]["mtime_depot_utc"],
            "debut_execution_utc": t_exec_iso,
            "fin_execution_utc": now_iso(),
            "duree_secondes": round(time.time() - t0_wall, 3),
        },
        "regle": "UN SEUL contrôle en échec ⟹ V4 REFUTE, exit 1, aucun sauvetage (I5)",
        "portee": ("V+ n'établit NI la vérité de Gij j = 0, NI la validité littérale du GAGUT, "
                   "NI le couplage D^{1/φ} = G. Il établit la chaîne de l'exposant : "
                   "Noether → échelle → puissance → Hurwitz → noyau ABC (I4). "
                   "CH-G3 (maillon propre d'Oyibo) reste [P] — corroboré, pas dérivé."),
        "lectures": LECTURES,
        "verdict": verdict,
        "exit_code": verdict["exit_code"],
    }
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=2)
    print(f"[OYIBO-CONSERVATION-V0] verdict {verdict['code']} — {verdict['nom']} (exit {verdict['exit_code']})")
    sys.exit(verdict["exit_code"])


if __name__ == "__main__":
    main()
