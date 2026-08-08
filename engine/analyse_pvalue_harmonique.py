# -*- coding: utf-8 -*-
"""
analyse_pvalue_harmonique.py — P-VALEUR ANTI-NUMEROLOGIE pour alpha et GAGUT
============================================================================
Question : la formule alpha = pi^4.e^-4.phi^-5.(sqrt2)^-1.(sqrt3)^-5
(ecart 2.35e-7 relatif au CODATA) et GAGUT = 6.pi^5 ~ m_p/m_e (ecart
1.88e-5) sont-elles des coincidences du treillis harmonique, ou des
signaux ?

Deux tests complementaires :
  T1 — CALIBRATION (test principal) : on tire des cibles aleatoires
       log-uniformes dans le domaine couvert par le treillis, et on
       mesure la MEILLEURE approximation de chacune par le treillis.
       p = fraction des cibles aleatoires dont la meilleure
       approximation est AUSSI BONNE que celle de alpha / GAGUT.
       (robuste au choix de l'espace ; repond directement a :
       "quelle chance qu'une constante quelconque tombe si pres ?")
  T2 — DECOMPTE DIRECT : k/N expressions du treillis dans la fenetre
       |ecart| <= ecart_observe autour de la cible.

Espaces (sensibilite) :
  A : |exp| <= 8 (phi,pi,e), <= 6 (sqrt2,sqrt3,sqrt5)  — contient la
      formule alpha (poids 19)
  B : |exp| <= 6 (phi,pi,e), <= 4 (radicaux), poids <= 12 — "formes
      simples" (la formule alpha n'y est PAS ; GAGUT (poids 9) oui)
"""

import itertools
import math
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
L = {"phi": math.log(PHI), "pi": math.log(math.pi), "e": 1.0,
     "s2": math.log(math.sqrt(2)), "s3": math.log(math.sqrt(3)),
     "s5": math.log(math.sqrt(5))}

ALPHA_CODATA = 0.0072973525693
ALPHA_FORMULE = math.pi ** 4 * math.e ** -4 * PHI ** -5 * math.sqrt(2) ** -1 * math.sqrt(3) ** -5
ERR_ALPHA = abs(ALPHA_FORMULE - ALPHA_CODATA) / ALPHA_CODATA

MPME_CODATA = 1836.15267343
GAGUT = 6 * math.pi ** 5
ERR_GAGUT = abs(GAGUT - MPME_CODATA) / MPME_CODATA

print("=" * 78)
print("P-VALEUR ANTI-NUMEROLOGIE — treillis harmonique (phi, pi, e, s2, s3, s5)")
print(f"  alpha formule = {ALPHA_FORMULE:.12f} | CODATA {ALPHA_CODATA:.12f}"
      f" | ecart relatif {ERR_ALPHA:.3e}")
print(f"  GAGUT 6.pi^5  = {GAGUT:.6f}      | m_p/m_e {MPME_CODATA:.6f}"
      f" | ecart relatif {ERR_GAGUT:.3e}")
print("=" * 78)


def construire_treillis(max_exp, max_r, poids_max=None, exclure_poids_0=True):
    """Toutes les valeurs phi^a pi^b e^c s2^d s3^e s5^f -> (log, poids) tries."""
    a = np.arange(-max_exp, max_exp + 1)
    b = np.arange(-max_exp, max_exp + 1)
    c = np.arange(-max_exp, max_exp + 1)
    d = np.arange(-max_r, max_r + 1)
    e = np.arange(-max_r, max_r + 1)
    f = np.arange(-max_r, max_r + 1)
    A, B, C, D, E, F = np.meshgrid(a, b, c, d, e, f, indexing="ij")
    poids = np.abs(A) + np.abs(B) + np.abs(C) + np.abs(D) + np.abs(E) + np.abs(F)
    mask = poids >= (1 if exclure_poids_0 else 0)
    if poids_max is not None:
        mask &= poids <= poids_max
    logs = (A * L["phi"] + B * L["pi"] + C * L["e"]
            + D * L["s2"] + E * L["s3"] + F * L["s5"])
    p = poids[mask]
    lo = logs[mask]
    idx = np.argsort(lo)
    return lo[idx], p[idx]


def meilleure_approximation(logs, cible):
    """Distance log minimale du treillis a la cible."""
    lt = math.log(cible)
    i = np.searchsorted(logs, lt)
    best = 1e300
    for j in (i - 1, i, i + 1):
        if 0 <= j < len(logs):
            best = min(best, abs(logs[j] - lt))
    return best


def calibration(logs, cibles, err_obs):
    """Fraction des cibles aleatoires avec meilleure approx <= err_obs."""
    dl_obs = abs(math.log(1 + err_obs)) if False else math.log1p(err_obs)
    # approx requise en distance log : |log(v/cible)| <= log1p(err)
    bests = np.array([meilleure_approximation(logs, t) for t in cibles])
    p = (bests <= dl_obs).mean()
    return p, bests


for nom, max_exp, max_r, poids_max in (("A (large : exp<=8/6, sans cap)",
                                        8, 6, None),
                                       ("B (simple : exp<=6/4, poids<=12)",
                                        6, 4, 12)):
    logs, poids = construire_treillis(max_exp, max_r, poids_max)
    print(f"\n--- Espace {nom} : N = {len(logs):,d} expressions ---")

    # meilleure approximation observee pour alpha et GAGUT
    ba = meilleure_approximation(logs, ALPHA_CODATA)
    bg = meilleure_approximation(logs, MPME_CODATA)
    print(f"  meilleure approx du treillis : alpha : {ba:.3e} (log)"
          f" | m_p/m_e : {bg:.3e} (log)")
    print(f"  formule alpha (poids 19)     : {abs(math.log(ALPHA_FORMULE / ALPHA_CODATA)):.3e} (log)")
    print(f"  GAGUT 6.pi^5 (poids 9)       : {abs(math.log(GAGUT / MPME_CODATA)):.3e} (log)")

    # T1 : calibration 2000 cibles log-uniformes sur le domaine du treillis
    rng = np.random.default_rng(2026)
    lo, hi = logs[0], logs[-1]
    cibles = np.exp(rng.uniform(lo, hi, 2000))
    p_a, bests_a = calibration(logs, cibles, ERR_ALPHA)
    p_g, bests_g = calibration(logs, cibles, ERR_GAGUT)
    print(f"\n  [T1 CALIBRATION] 2000 cibles aleatoires log-uniformes")
    print(f"    p(alpha) = {p_a:.4f}   (fraction des cibles aleatoires aussi"
          f" bien approximees que la formule alpha)")
    print(f"    p(GAGUT) = {p_g:.4f}   (idem pour 6.pi^5)")
    print(f"    distribution des meilleures approx des cibles aleatoires :")
    for q in (10, 50, 90, 99, 99.9):
        print(f"      quantile {q:5.1f}% : {np.percentile(bests_a, q):.3e}")

    # T2 : decompte direct k/N
    k_a = int((np.abs(logs - math.log(ALPHA_CODATA)) <= math.log1p(ERR_ALPHA)).sum())
    k_g = int((np.abs(logs - math.log(MPME_CODATA)) <= math.log1p(ERR_GAGUT)).sum())
    print(f"\n  [T2 DECOMPTE] expressions dans la fenetre de l'ecart observe :")
    print(f"    alpha : k = {k_a} / {len(logs):,d}  -> p = {k_a / len(logs):.3e}")
    print(f"    GAGUT : k = {k_g} / {len(logs):,d}  -> p = {k_g / len(logs):.3e}")

    # top-5 meilleures approximations de alpha dans cet espace (avec poids)
    idx = np.argsort(np.abs(logs - math.log(ALPHA_CODATA)))[:5]
    print(f"\n  Top-5 approximations de alpha par le treillis :")
    for i in idx:
        p_ = poids[i]
        print(f"    log-ecart {abs(logs[i] - math.log(ALPHA_CODATA)):.3e}"
              f" (poids {p_}) valeur {math.exp(logs[i]):.12f}")

# ----------------------------------------------------------------------
print("\n" + "=" * 78)
print("CORRECTION DE COMPARAISONS MULTIPLES (le facteur decisif)")
print("=" * 78)
print("""
Le DOCUMENT_FONDATEUR_THEORIE_HARMONIQUE.md revendique ~30 observables
(alpha, m_mu/m_e, sin^2(theta_W), ...). Si la formule de alpha a ete
CHERCHEE parmi ~30 cibles (post-hoc), la p-valeur effective est :

    p_eff = 1 - (1 - p_alpha)^30

avec p_alpha = 0.0785 (espace large) :
""")
p_eff = 1 - (1 - 0.0785) ** 30
print(f"    p_eff = 1-(1-0.0785)^30 = {p_eff:.2f}")
print("""
Seuil de Bonferroni pour une revendication significative parmi 30 essais :
p < 0.05/30 = 0.00167. p_alpha = 0.0785 >> 0.00167 -> NON significatif.

NOTA : si la formule de alpha a ete PREDITE AVANT la mesure (pre-
enregistree, derivee a priori), alors p_alpha = 0.0785 s'applique telle
quelle — c'est un signal faible (sous le seuil de 5 %), pas une preuve.
Ce point ne peut pas etre tranche par le calcul : il depend de l'historique
de la decouverte de la formule.
""")
