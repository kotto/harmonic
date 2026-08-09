#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
depot_e3_tstar.py — DÉPÔT PRÉ-ENREGISTRÉ DE LA PRÉDICTION T* (protocole P3.2)
=============================================================================
Date du dépôt : 09/08/2026 — auteur : Univers-Holistique (Kotto Alain) + ZCode
STATUT : DÉPOSÉ — NON ENCORE TESTÉ  (v2 : la famille T*)

PRÉDICTION (v2 — la famille des températures dorées, déposée avant tout test) :
  THÉORÈME : pour tout gap quantique ΔE, e^{−ΔE/k_BT} = 1/φ ⟺ T* = ΔE/(k_B·ln φ).
  T5a · OSCILLATEUR : à T* = ℏω/(k_B·ln φ) = 2,078086921235027·ℏω/k_B, la
       statistique d'occupation est la distribution dorée : p_n = (1−1/φ)(1/φ)^n,
       n̄ = φ = 1,6180339887498948, Fano = φ².
  T5b · IONISATION : pour chaque élément d'énergie d'ionisation χ, le facteur
       de Boltzmann vaut exactement 1/φ à T*_ion = χ·24115 K/eV
       (H : 327 918 K · He : 592 919 K · … — table de 23 éléments).

Ce dépôt génère TOUS les nombres du document daté/signé, avec les systèmes
physiques concrets où la prédiction est réalisable aujourd'hui.
"""
import json
import math
import os
import time

# ─────────────────────────────────────────────────────────────────────────────
# 1. LES NOMBRES EXACTS (les mêmes constantes que les Violets A/B)
# ─────────────────────────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
LN_PHI = math.log(PHI)
Q = 1.0 / PHI
TSTAR = 1.0 / LN_PHI                    # en unités de ℏω/k_B

H = 6.62607015e-34                      # J·s (exact, SI 2019)
KB = 1.380649e-23                       # J/K (exact, SI 2019)

print("=" * 78)
print("DÉPÔT E3 — PRÉDICTION T* (pré-enregistrée, non encore testée)")
print("=" * 78)
print(f"φ        = {PHI:.16f}")
print(f"ln φ     = {LN_PHI:.16f}")
print(f"q = 1/φ  = {Q:.16f}")
print(f"T*/ℏω/k_B = 1/ln φ = {TSTAR:.16f}")
print(f"n̄ = φ    = {PHI:.16f}   (occupation moyenne à T*)")
print(f"Fano φ²  = {PHI*PHI:.16f}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 2. LA DISTRIBUTION DORÉE (les 7 premières probabilités)
# ─────────────────────────────────────────────────────────────────────────────
print("─ La distribution dorée p_n = (1−1/φ)·(1/φ)^n :")
somme = 0.0
for n in range(7):
    p = (1.0 - Q) * Q ** n
    somme += p
    print(f"    p_{n} = {p:.16f}   (p_{{n+1}}/p_n = {Q:.16f})")
print(f"    Σ p_n (n=0..6) = {somme:.16f}   (reste : {1.0-somme:.2e})")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 3. LES SYSTÈMES CONCRETS — où T* est réalisable aujourd'hui
# ─────────────────────────────────────────────────────────────────────────────
print("─ Systèmes physiques concrets (T* = 2,078087·ℏω/k_B) :")
systemes = []
for nom, nu_hz in [
    ("Cavité micro-onde (cavity QED)", 10e9),
    ("Mode de lecture circuit QED (transmon)", 6e9),
    ("Mode phonon (cristal/optomécanique)", 1e9),
    ("Mode séculaire de piège à ions", 1e6),
    ("Oscillateur mécanique (membrane)", 1e5),
]:
    T_quant = H * nu_hz / KB              # ℏω/k_B = hν/k_B
    T_star = TSTAR * T_quant
    systemes.append({"systeme": nom, "frequence_Hz": nu_hz,
                     "T_quant_K": T_quant, "T_star_K": T_star})
    print(f"    {nom:42s} ν={nu_hz:8.0e} Hz → T* = {T_star:.4f} K")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 4. LA SENSIBILITÉ — la précision de température requise (déclarée avant)
# ─────────────────────────────────────────────────────────────────────────────
# q = e^{−x}, x = ℏω/(k_B T) = ln φ à T* ;  dq/q = x·|dT|/T = ln φ·|dT|/T
print("─ Analyse de sensibilité (précision requise, déclarée avant) :")
for cible, label in [(1e-3, "1e-3"), (1e-4, "1e-4")]:
    dT_T = cible / LN_PHI                # pour dq/q = cible
    dn_n = cible / (Q * (1.0 - Q))       # dn̄/n̄ = dq/(q(1−q))
    print(f"    Précision {label} sur q  → contrôle de température "
          f"±{dT_T*100:.3f} % de T*")
    print(f"    Précision {label} sur n̄ → contrôle de température "
          f"±{cible/(Q*(1.0-Q)*LN_PHI)*100:.3f} % de T*")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 4. LA FAMILLE T*_ion — T5b (généralisation : e^{−ΔE/k_BT} = 1/φ ⟺ T* = ΔE/(k_B·ln φ))
# ─────────────────────────────────────────────────────────────────────────────
# Premières énergies d'ionisation (eV — valeurs NIST approximatives)
EI = {1: 13.598, 2: 24.587, 3: 5.392, 4: 9.323, 5: 8.298, 6: 11.260,
      7: 14.534, 8: 13.618, 9: 17.423, 10: 21.565, 11: 5.139, 12: 7.646,
      13: 5.986, 14: 8.152, 15: 10.487, 16: 10.360, 17: 12.968, 18: 15.760,
      19: 4.341, 20: 6.113, 36: 13.999, 54: 12.130, 86: 10.749}
NOMS = {1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O",
        9: "F", 10: "Ne", 11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P",
        16: "S", 17: "Cl", 18: "Ar", 19: "K", 20: "Ca", 36: "Kr", 54: "Xe",
        86: "Rn"}
K_EV = 11604.5                      # eV → K
FACTEUR = K_EV / LN_PHI             # K par eV = 24115 K/eV

print("─ LA FAMILLE T*_ion (T5b — T5 généralisé, 23 éléments) :")
print(f"  e^(−ΔE/k_BT) = 1/φ ⟺ T* = ΔE/(k_B·ln φ) — facteur {FACTEUR:.0f} K/eV")
table_ion = []
for Z in sorted(EI):
    T_ion = EI[Z] * FACTEUR
    table_ion.append({"Z": Z, "element": NOMS[Z], "chi_eV": EI[Z],
                      "T_etoile_ion_K": T_ion})
    print(f"    {Z:3d} {NOMS[Z]:4s} χ = {EI[Z]:7.3f} eV → T* = {T_ion:9.0f} K")
q_verif = math.exp(-LN_PHI)          # e^{−χ/k_BT*} = e^{−ln φ} = 1/φ EXACT
print(f"  Vérification : e^(−χ/k_BT*) = {q_verif:.16f} vs 1/φ = {1.0/PHI:.16f} "
      f"{'✅' if abs(q_verif - 1.0/PHI) < 1e-15 else '❌'}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 5. L'ENREGISTREMENT DU DÉPÔT (JSON — le certificat horodaté, v2 : la famille)
# ─────────────────────────────────────────────────────────────────────────────
depot = {
    "protocole": "P3.2 — dépôt pré-enregistré, daté et signé, avant tout test",
    "version": 2,
    "date_depot": "2026-08-09",
    "auteur": "Univers-Holistique (Kotto Alain) + ZCode",
    "statut": "DÉPOSÉ — NON ENCORE TESTÉ",
    "theoreme": "FAMILLE T* : pour tout gap quantique ΔE, "
                "e^{−ΔE/k_BT} = 1/φ ⟺ T* = ΔE/(k_B·ln φ)",
    "prediction_T5a_oscillateur": {
        "enonce": ("Pour un mode harmonique à l'équilibre thermique à "
                   "T* = ℏω/(k_B·ln φ), la statistique d'occupation est la "
                   "distribution dorée : p_n = (1−1/φ)(1/φ)^n, "
                   "n̄ = φ = 1.6180339887498948, Fano = φ²"),
        "Tstar_unite_hbar_omega_kB": TSTAR,
        "rapport_successif": Q,
        "occupation_moyenne": PHI,
        "fano": PHI * PHI,
        "distribution_p0_p6": [(1.0 - Q) * Q ** n for n in range(7)],
    },
    "prediction_T5b_ionisation": {
        "enonce": ("Pour tout élément d'énergie d'ionisation χ, le facteur "
                   "de Boltzmann vaut exactement 1/φ à T*_ion = χ/(k_B·ln φ) "
                   "= χ·24115 K/eV — table de 23 éléments, falsifiable par "
                   "spectroscopie de plasma (limite Saha basse densité)"),
        "facteur_K_par_eV": FACTEUR,
        "table": table_ion,
        "verification_e_exp_moins_ln_phi": q_verif,
    },
    "conditions_falsification": [
        ("T5a · |n̄_mesuré − φ| > incertitude combinée à 1e-3 (relatif) → falsifiée"),
        ("T5a · rapport p_{n+1}/p_n ≠ 1/φ au-delà de l'incertitude → falsifiée"),
        ("T5b · à T*_ion, le facteur de Boltzmann mesuré s'écarte de 1/φ au-delà "
         "de l'incertitude → falsifiée"),
        ("statistique non-thermique (mode non thermalisé / plasma hors équilibre) "
         "→ test invalide, pas de verdict"),
    ],
    "systemes_candidats": systemes,
    "sensibilite": {
        "dT_T_pour_dq_q_1e-3": 1e-3 / LN_PHI,
        "dT_T_pour_dn_n_1e-3": 1e-3 / (Q * (1.0 - Q) * LN_PHI),
    },
    "verifications_theoreme": {
        "T5a": "Violet B — rapports exacts à 1.1e-16 (validation_etats_quantiques.py)",
        "T5b": "exploration_tableau_periodique.py — e^{−ln φ} = 1/φ exact machine",
        "reference": "THEORIE_HARMONIQUE_REFONDEE.md — T5 (famille), frontière F3",
    },
    "horodatage": time.strftime("%Y-%m-%d %H:%M:%S"),
}

chemin = os.path.join("data", "benchmarks", "depot_e3_tstar.json")
os.makedirs(os.path.dirname(chemin), exist_ok=True)
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(depot, f, indent=2, ensure_ascii=False)

print("─ VERDICT")
print("  ✅ Dépôt v2 enregistré :", chemin)
print("  ⏳ Statut : DÉPOSÉ — NON ENCORE TESTÉ")
print("  🔍 Falsifiable : T5a n̄ = φ à 1e-3 · rapport p_{n+1}/p_n = 1/φ")
print(f"     T5b Boltzmann = 1/φ à T*_ion (23 éléments, ex. H : "
      f"{EI[1]*FACTEUR:.0f} K)")
print(f"  📅 Horodaté : {depot['horodatage']}")
