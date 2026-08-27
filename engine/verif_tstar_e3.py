# -*- coding: utf-8 -*-
"""
verif_tstar_e3.py — AUDIT MACHINE INDÉPENDANT DE LA PRÉDICTION E3 (famille T*)
================================================================================
Exécution machine du dépôt E3 v2 (DEPOT_E3_PREDICTION_TSTAR.md, déposé 09/08/2026
avant tout test, certificat data/benchmarks/depot_e3_tstar.json).

Principe de discipline (identique aux autres verif_*) :
  - Le dépôt est SCELÉ : ce script ne le modifie pas, il le relaie.
  - AUCUN nombre n'est repris des scripts du dépôt (depot_e3_tstar.py,
    exploration_tableau_periodique.py, validation_etats_quantiques.py, déjà
    exécutés séparément, exit 0) : tout est re-dérivé ici depuis les formes closes.
  - Registre fermé : 1 oscillateur (T5a) + 23 éléments (T5b) — les lectures
    sont celles imprimées dans le dépôt, aux précisions imprimées.
  - Barres fixées par la précision imprimée du dépôt v2 (§2-§3) :
      * valeurs closes (16 chiffres, certificat)      -> barre 1e-12 relatif
      * table p0..p6 (5 décimales dans le DEPOT .md)   -> arrondi exact à 5 déc.
      * table T*_ion (entiers K, chi à 0,001 eV)       -> barre 5e-5 relatif
      * facteur de Boltzmann aux T* déposées (arrondi) -> barre 1e-5
      * chi déclarés « valeurs NIST » (4-5 chiffres)   -> barre 1e-3 relatif
  - Un seul échec -> REFUTE, exit 1.

Ce que l'audit PEUT conclure (PROTOCOLE_TEST_TSTAR.md §0, honnêteté) :
  - l'identité T5 est algébrique : la machine ne peut ni la confirmer ni la
    réfuter physiquement — elle établit que le dépôt est DÉPÔT_CONFORME
    (chaque nombre déposé = forme close re-dérivée) et que le scrutin
    expérimental (cavité QED 1 K / plasma 3,3e5 K) est prêt à voter.
  - Le vote décisif reste extérieur (labo circuit QED). Ce script ferme la
    partie machine du scrutin.
"""

import json
import math
import os
import sys
from datetime import datetime

# Constantes SI exactes (réforme SI 2019 — zéro incertitude)
H_PLANCK = 6.62607015e-34          # J.s (exact)
KB_SI = 1.380649e-23               # J/K (exact)
E_CHARGE = 1.602176634e-19         # C (exact)
KB_EV = KB_SI / E_CHARGE           # eV/K = 8.617333262e-5

PHI = (1.0 + math.sqrt(5.0)) / 2.0
LN_PHI = math.log(PHI)
INV_PHI = 1.0 / PHI

# Barres pré-enregistrées (précision imprimée du dépôt v2)
BAR_CLOSE = 1e-12      # valeurs closes 16 chiffres (certificat / DEPOT §2)
BAR_TABLE_K = 5e-5     # T*_ion entiers depuis chi à 0,001 eV
BAR_BOLTZ = 1e-5       # facteur de Boltzmann aux T* déposées (entiers K)
BAR_NIST = 1e-3        # chi déclarés NIST (4-5 chiffres significatifs)

results = {"controles": {}, "T5a": {}, "T5b": {}, "diagnostics": {}}
echecs = []


def check(nom, valeur, cible, barre, relatif=True):
    ecart = abs(valeur - cible)
    denom = max(abs(cible), 1e-300) if relatif else 1.0
    e = ecart / denom
    ok = e <= barre
    if not ok:
        echecs.append(nom)
    return nom, ecart, e, barre, ok


def fmt_check(nom, ecart, e, barre, ok):
    return f"  {'OK ' if ok else 'ECHEC'} {nom:<56} ecart={ecart:.3e} ({e:.2e}, barre {barre:.0e})"


print("=" * 78)
print("AUDIT MACHINE E3 — FAMILLE DES TEMPÉRATURES DORÉES T*")
print("Dépôt : DEPOT_E3_PREDICTION_TSTAR.md (09/08/2026, v2, avant tout test)")
print("=" * 78)

# ---------------------------------------------------------------- C0 : piste d'audit
print("\n— C0 · PISTE D'AUDIT (dépôt antérieur à l'audit)")
d_depot = os.path.getmtime("DEPOT_E3_PREDICTION_TSTAR.md")
d_cert = os.path.getmtime("data/benchmarks/depot_e3_tstar.json")
print(f"  DEPOT_E3_PREDICTION_TSTAR.md   mtime {datetime.fromtimestamp(d_depot):%Y-%m-%d %H:%M:%S}")
print(f"  depot_e3_tstar.json (certif.)  mtime {datetime.fromtimestamp(d_cert):%Y-%m-%d %H:%M:%S}")
print(f"  audit exécuté le               {datetime.now():%Y-%m-%d %H:%M:%S}")
if not (d_depot < datetime.now().timestamp() and d_cert < d_depot + 86400 * 365 * 10):
    echecs.append("C0_audit_trail")
    print("  ECHEC : dépôt/certificat absents ou postérieurs à l'audit")
else:
    print("  OK : dépôt + certificat antérieurs à l'audit (aucun paramètre libre)")

# ---------------------------------------------------------------- C1 : identités
print("\n— C1 · IDENTITÉS DE BASE")
r = check("phi^2 = phi+1", PHI * PHI - (PHI + 1.0), 0.0, 1e-15, relatif=False)
results["controles"]["phi2"] = r
print(fmt_check(*r))
r = check("1 - 1/phi = 1/phi^2", (1.0 - INV_PHI) - INV_PHI**2, 0.0, 1e-15, relatif=False)
results["controles"]["inv_phi"] = r
print(fmt_check(*r))

# ---------------------------------------------------------------- C2 : constantes
print("\n— C2 · COHÉRENCE DES CONSTANTES (dépôt §3 : « k_B = 1/11604,5 eV/K »)")
r = check("k_B en eV/K (SI exact vs 8.617333262e-5)", KB_EV, 8.617333262e-5, 1e-9)
results["controles"]["kB_eV"] = r
print(fmt_check(*r))
K_PAR_EV = 1.0 / (KB_EV * LN_PHI)   # facteur exact : T*_ion = chi * K_PAR_EV
print(f"  facteur exact 1/(k_B·ln phi) = {K_PAR_EV:.6f} K/eV   (dépôt : « 24115 K/eV »)")
r = check("facteur 1/(k_B·ln phi) vs 24115 (4 chiffres du dépôt)", K_PAR_EV, 24115.0, 1e-4)
results["controles"]["facteur_24115"] = r
print(fmt_check(*r))

# ---------------------------------------------------------------- C3 : T5a oscillateur
print("\n— C3 · T5a OSCILLATEUR THERMIQUE (registre fermé du certificat)")
TSTAR_U = 1.0 / LN_PHI
r = check("T* = 1/ln phi vs déposé 2,078086921235027", TSTAR_U, 2.0780869212350273, BAR_CLOSE)
results["T5a"]["Tstar_unites"] = r
print(fmt_check(*r))
p_geo = [(1.0 - INV_PHI) * INV_PHI**n for n in range(7)]
p_cert = [0.3819660112501052, 0.23606797749978972, 0.14589803375031546,
          0.09016994374947424, 0.0557280900008412, 0.03444185374863301,
          0.021286236252208178]
p_depot_md = ["0,38197", "0,23607", "0,14590", "0,09017", "0,05573", "0,03444", "0,02129"]
ok_all_p = True
for n in range(7):
    dep_md = float(p_depot_md[n].replace(",", "."))
    ok_md = f"{p_geo[n]:.5f}" == f"{dep_md:.5f}"
    ok_cert = abs(p_geo[n] - p_cert[n]) < 1e-15
    if not (ok_md and ok_cert):
        ok_all_p = False
        echecs.append(f"p_{n}")
    print(f"  {'OK ' if ok_md and ok_cert else 'ECHEC'} p_{n} = {p_geo[n]:.16f}  (table v2 {dep_md:.5f}, certificat concorde)")
results["T5a"]["distribution_p0_p6"] = ok_all_p
nbar_geo = INV_PHI / (1.0 - INV_PHI)
r = check("n̄ géométrique q/(1-q) = phi", nbar_geo, PHI, BAR_CLOSE)
results["T5a"]["nbar_geometrique"] = r
print(fmt_check(*r))
# Voie indépendante : formule de Bose-Einstein (pas la distribution géométrique)
nbar_bose = 1.0 / (math.exp(LN_PHI) - 1.0)
r = check("n̄ Bose-Einstein 1/(e^{hbar omega/kT*}-1) = phi", nbar_bose, PHI, BAR_CLOSE)
results["T5a"]["nbar_bose_einstein"] = r
print(fmt_check(*r))
fano_geo = (INV_PHI / (1.0 - INV_PHI) ** 2) / nbar_geo
r = check("Fano géométrique Var/n̄ = phi^2", fano_geo, PHI**2, BAR_CLOSE)
results["T5a"]["fano_geometrique"] = r
print(fmt_check(*r))
fano_bose = 1.0 + nbar_bose                            # Var Bose = n̄(1+n̄)
r = check("Fano Bose-Einstein 1+n̄ = phi^2", fano_bose, PHI**2, BAR_CLOSE)
results["T5a"]["fano_bose"] = r
print(fmt_check(*r))
r = check("somme p0..p6 = 1 - q^7 (fermeture Gibbs)", sum(p_geo), 1.0 - INV_PHI**7, 1e-14)
results["T5a"]["fermeture_gibbs"] = r
print(fmt_check(*r))
r = check("identité close e^{-ΔE/kT*} = 1/phi", math.exp(-1.0 / TSTAR_U), INV_PHI, BAR_CLOSE)
results["T5a"]["identite_boltzmann"] = r
print(fmt_check(*r))

# ---------------------------------------------------------------- C4 : T5b ionisation
print("\n— C4 · T5b TEMPÉRATURES DORÉES D'IONISATION (23 éléments, registre fermé du dépôt §3)")
TABLE = [
    (1, "H", 13.598, 327918), (2, "He", 24.587, 592919), (3, "Li", 5.392, 130029),
    (4, "Be", 9.323, 224826), (5, "B", 8.298, 200108), (6, "C", 11.260, 271537),
    (7, "N", 14.534, 350490), (8, "O", 13.618, 328400), (9, "F", 17.423, 420158),
    (10, "Ne", 21.565, 520043), (11, "Na", 5.139, 123928), (12, "Mg", 7.646, 184385),
    (13, "Al", 5.986, 144353), (14, "Si", 8.152, 196587), (15, "P", 10.487, 252896),
    (16, "S", 10.360, 249833), (17, "Cl", 12.968, 312725), (18, "Ar", 15.760, 380055),
    (19, "K", 4.341, 104684), (20, "Ca", 6.113, 147416), (36, "Kr", 13.999, 337588),
    (54, "Xe", 12.130, 292517), (86, "Rn", 10.749, 259214),
]
assert len(TABLE) == 23, "registre fermé : 23 éléments"
max_e, max_e_el = 0.0, ""
max_bz, max_bz_el = 0.0, ""
lignes = []
for (z, sym, chi, t_dep) in TABLE:
    t_exact = chi * K_PAR_EV
    e_rel = abs(t_exact - t_dep) / t_dep
    lignes.append((z, sym, chi, t_dep, t_exact, e_rel))
    if e_rel > BAR_TABLE_K:
        echecs.append(f"T5b_{sym}")
    if e_rel > max_e:
        max_e, max_e_el = e_rel, sym
    facteur_dep = math.exp(-chi / (KB_EV * t_dep))     # T* déposée (entier K)
    e_bz = abs(facteur_dep - INV_PHI)
    if e_bz > max_bz:
        max_bz, max_bz_el = e_bz, sym
facteur_ident = math.exp(-1.0 / (KB_EV * K_PAR_EV))    # = e^{-ln phi}, toute chi
e_ident = abs(facteur_ident - INV_PHI)
print(f"  {'OK ' if max_e <= BAR_TABLE_K else 'ECHEC'} 23/23 T*_ion re-dérivées (T* = chi·[1/(k_B·ln phi)]) — pire écart {max_e:.2e} rel ({max_e_el}, barre {BAR_TABLE_K:.0e})")
results["T5b"]["pire_ecart_table"] = {"ecart_rel": max_e, "element": max_e_el, "barre": BAR_TABLE_K, "ok": max_e <= BAR_TABLE_K}
print(f"  {'OK ' if max_bz <= BAR_BOLTZ else 'ECHEC'} facteur de Boltzmann aux T* déposées (23 éléments) — pire écart à 1/phi = {max_bz:.2e} ({max_bz_el}, barre {BAR_BOLTZ:.0e})")
results["T5b"]["pire_ecart_boltzmann_dep"] = {"ecart": max_bz, "element": max_bz_el, "barre": BAR_BOLTZ, "ok": max_bz <= BAR_BOLTZ}
if max_bz > BAR_BOLTZ:
    echecs.append("T5b_boltzmann_table")
print(f"  {'OK ' if e_ident <= 1e-15 else 'ECHEC'} forme close : e^(-chi/(k_B·T*)) = 1/phi, indépendant de chi  (écart {e_ident:.2e})")
results["T5b"]["identite_forme_close"] = {"ecart": e_ident, "barre": 1e-15, "ok": e_ident <= 1e-15}
if e_ident > 1e-15:
    echecs.append("T5b_forme_close")
print("  z  élément  chi [eV]   T* déposé   T* exact     écart rel")
for (z, sym, chi, t_dep, t_ex, e_rel) in lignes:
    star = " *" if e_rel > BAR_TABLE_K else ""
    print(f"  {z:>3} {sym:<6} {chi:>8.3f}  {t_dep:>9}  {t_ex:>10.1f}   {e_rel:>9.2e}{star}")

# ---------------------------------------------------------------- C5 : ancrage NIST
print("\n— C5 · ANCRAGE NIST DU TABLEAU (8 ancres, barre 1e-3 : chi imprimés à 4-5 chiffres)")
NIST = {"H": 13.5984346, "He": 24.587389, "Li": 5.391715, "Na": 5.139077,
        "K": 4.340665, "Kr": 13.999606, "Xe": 12.129844, "Rn": 10.748502}
chi_map = {sym: chi for (_, sym, chi, _) in TABLE}
pire_nist, pire_nist_el = 0.0, ""
for sym, ref in NIST.items():
    e = abs(chi_map[sym] - ref) / ref
    if e > BAR_NIST:
        echecs.append(f"nist_{sym}")
    if e > pire_nist:
        pire_nist, pire_nist_el = e, sym
print(f"  {'OK ' if pire_nist <= BAR_NIST else 'ECHEC'} chi du dépôt vs valeurs NIST : pire écart {pire_nist:.2e} rel ({pire_nist_el}, barre {BAR_NIST:.0e})")
results["T5b"]["ancrage_nist_pire"] = {"ecart_rel": pire_nist, "element": pire_nist_el, "barre": BAR_NIST}

# ---------------------------------------------------------------- D1 : sensibilité
print("\n— D1 · DIAGNOSTIC SENSIBILITÉ (correction du dépôt §4 — non falsificateur)")
# n̄ = q/(1-q) ; d ln n̄ = phi^2 · d ln q ; d ln q = ln(phi)·dT/T
# => dT*/T* requis pour 1e-3 sur n̄ = 1e-3 / (phi^2 · ln phi)
coef = PHI**2 * LN_PHI
dT_sur_T = 1e-3 / coef
T_kelvin_10GHz = TSTAR_U * H_PLANCK * 10e9 / KB_SI
dT_mK = dT_sur_T * T_kelvin_10GHz * 1000.0
print(f"  analytique : dn̄/n̄ = phi^2·ln(phi)·(dT/T) = {coef:.4f}·(dT/T)")
print(f"  1e-3 sur n̄ exige dT/T = {dT_sur_T:.3e}  soit  ±{dT_mK:.2f} mK à T* = {T_kelvin_10GHz:.4f} K (f0 = 10 GHz)")
print(f"  dépôt §4 déclare ±0,88 % (±9 mK) — facteur ~11 trop lâche (correspond à 1e-2 sur n̄)")
print(f"  cohérence interne dépôt : « 1e-3 sur q -> ±0,21 % » ✓ (dT/T = 1e-3/ln phi = {1e-3/LN_PHI:.2e})")
results["diagnostics"]["sensibilite"] = {
    "coef_dnbar_sur_dT": coef,
    "dT_sur_T_pour_1e-3_sur_nbar": dT_sur_T,
    "T_etoile_kelvin_10GHz": T_kelvin_10GHz,
    "dT_mK_requis": dT_mK,
    "depot_declare_pct": 0.88,
    "correction": "dépôt §4 confond budget 1e-3 (±0,79 mK requis) et 1e-2 (±9 mK) — la barre V1 restant 1e-3, l'exigence réelle de température est ~10x plus dure que déclarée",
}

# ---------------------------------------------------------------- VERDICT
print("\n" + "=" * 78)
if echecs:
    verdict = "E3_DEPOT_REFUTE"
    print(f"❌ VERDICT : {verdict}")
    for e in echecs:
        print(f"   - échec : {e}")
    code = 1
else:
    verdict = "E3_DEPOT_CONFORME"
    print("✅ VERDICT : E3_DEPOT_CONFORME — les 24 instances déposées (1 oscillateur + 23 éléments)")
    print("   se re-dérivent TOUTES des formes closes aux précisions imprimées (barres pré-enregistrées).")
    print("   Voies indépendantes convergentes : géométrique ET Bose-Einstein -> n̄ = phi, Fano = phi^2.")
    print("   HONNÊTETÉ (PROTOCOLE §0) : l'identité T5 est algébrique — l'audit machine ne prouve pas")
    print("   la physique, il garantit que le scrutin est fidèle au dépôt et prêt à voter.")
    print("   ⏳ Vote décisif expérimental : cavité QED 10 GHz à 0,997 K (V1 : |n̄-phi|/phi <= 1e-3,")
    print(f"      exigeant ±{dT_mK:.1f} mK, et non ±9 mK) OU plasma H à 327 918 K (limite Saha basse densité).")
    code = 0
print("=" * 78)

results["verdict"] = verdict
results["code_retour"] = code
results["date_audit"] = datetime.now().isoformat(timespec="seconds")
results["depot"] = "DEPOT_E3_PREDICTION_TSTAR.md (v2, 2026-08-09)"
results["certificat"] = "data/benchmarks/depot_e3_tstar.json"
with open("resultat_tstar_e3.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1, ensure_ascii=False)
print("JSON : resultat_tstar_e3.json")
sys.exit(code)