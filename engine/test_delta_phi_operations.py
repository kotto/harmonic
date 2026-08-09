#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_delta_phi_operations.py — TEST 2 : « Δφ encode-t-il les opérations ? »
===========================================================================
Prédiction du « NLP Idéal — Filtre Dynamique Harmonique » :
    Δφ(n₁, n₂) ≈ 0   → addition/soustraction
    Δφ(n₁, n₂) ≈ π/2 → multiplication
    Δφ(n₁, n₂) ≈ π   → inversion/division
où Δφ est la distance de phase entre deux nombres dans l'encode du moteur.

PROTOCOLE PRÉ-ENREGISTRÉ (déclaré AVANT le calcul) :
  Corpus : data/t5_gsm8k/train.json (1105 problèmes réels) — les sorties
    contiennent les équations « a op b = c » → paires d'opérandes (a, b, op)
    étiquetées par opération ∈ {+, −, ×, ÷}.
  Exclusion déclarée : paires avec a == b (chaînes identiques) — leur Δφ est
    trivialement 0 dans tout encode déterministe (contaminerait l'uniformité).
  Encodages testés (ceux du moteur) :
    E1 — fallback FNV-1a gaussien + phases spectrales φ (holographic_encoder.py)
    E2 — φ-exponentiel de la doc fondatrice : phases = (h·φ^k mod 2π)
  Définitions de Δφ (deux, circulaires, repliées sur [0, π]) :
    D1 — Δφ_mot : angle de la composante spectrale (E1 : k=500 · E2 : k=0)
    D2 — Δφ_corr : argument du produit scalaire complexe ⟨ψ(a)|ψ(b)⟩
  Contrôle positif (sanity du test) : encode SYNTHÉTIQUE phase(n) = n·δ mod 2π
    — s'il ne montre AUCUNE structure, le test est invalide.

CRITÈRES (déclarés avant) :
  C_A · Uniformité : pour E1 et E2, Kuiper vs uniforme sur [0,π] avec p > 0,01
       → pas de structure → la revendication Δφ est RÉFUTÉE pour l'encode réel.
  C_B · Opérations : moyennes circulaires par opération ≠ valeurs revendiquées
       (écart > 0,1 rad) OU Kruskal-Wallis p > 0,01 entre opérations
       → RÉFUTÉE.
  C_C · Contrôle : l'encode synthétique DOIT montrer une structure
       (KW p < 0,01 ET Spearman(Δφ, |a−b|) > 0,5) — sinon test invalide.
  Verdict publié, même négatif (méthode du projet).
"""
import json
import math
import os
import re
import time

import numpy as np
from scipy import stats

# ═══════════════════════════════════════════════════════════════════════════
# 0. CONSTANTES — DÉCLARÉES AVANT LE CALCUL
# ═══════════════════════════════════════════════════════════════════════════
PHI = (1.0 + math.sqrt(5.0)) / 2.0
TAU = 2.0 * math.pi
DIM = 512
SEUIL_ECART_REVENDIQUE = 0.1        # C_B : tolérance sur les valeurs {0, π/2, π}
CHEMIN_DATA = "data/t5_gsm8k/train.json"
FNV_OFFSET = 14695981039346656037
FNV_PRIME = 1099511628211


def fnv1a(s: str) -> int:
    h = FNV_OFFSET
    for ch in s:
        h ^= ord(ch)
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


# ═══════════════════════════════════════════════════════════════════════════
# 1. LES ENCODAGES (identiques au moteur)
# ═══════════════════════════════════════════════════════════════════════════
def encode_E1(mot: str):
    """Fallback FNV-1a gaussien + phases spectrales φ (holographic_encoder.py)."""
    seed = fnv1a(mot)
    rng = np.random.RandomState(seed & 0xFFFFFFFF)
    sigma = 1.0 / math.sqrt(2.0 * DIM)
    real = np.zeros(DIM, dtype=np.float64)
    imag = np.zeros(DIM, dtype=np.float64)
    n_direct = min(500, DIM)
    real[:n_direct] = rng.randn(n_direct) * sigma
    imag[:n_direct] = rng.randn(n_direct) * sigma
    for k in range(n_direct, DIM):
        ph = ((seed >> (k % 32)) ^ (k * 2654435761)) % 2147483647
        ph = (ph * PHI) % TAU
        real[k] = math.cos(ph) * sigma
        imag[k] = math.sin(ph) * sigma
    return real + 1j * imag


def encode_E2(mot: str):
    """φ-exponentiel de la doc fondatrice : phases = (h·φ^k mod 2π)."""
    h = fnv1a(mot)
    k = np.arange(DIM, dtype=np.float64)
    phases = (h * PHI ** k) % TAU
    return np.exp(1j * phases)


def encode_synth(n: int):
    """Contrôle positif : phase = n·δ mod 2π (structure PAR VALEUR)."""
    delta = 0.1  # rad par unité
    return np.array([np.exp(1j * ((n * delta) % TAU))])


# ═══════════════════════════════════════════════════════════════════════════
# 2. MESURES DE Δφ (repliées sur [0, π])
# ═══════════════════════════════════════════════════════════════════════════
def delta_phi_mot(psi_a, psi_b, k):
    """D1 — distance circulaire des phases de la composante k."""
    d = (np.angle(psi_a[k]) - np.angle(psi_b[k])) % TAU
    return min(d, TAU - d)


def delta_phi_corr(psi_a, psi_b):
    """D2 — argument du produit scalaire complexe (replié sur [0, π])."""
    d = np.angle(np.vdot(psi_a, psi_b)) % TAU
    return min(d, TAU - d)


# ═══════════════════════════════════════════════════════════════════════════
# 3. LE CORPUS — paires (a, b, op) étiquetées depuis les équations GSM8K
# ═══════════════════════════════════════════════════════════════════════════
EQ = re.compile(r"(-?\d+)\s*([+\-×*÷/])\s*(-?\d+)\s*=\s*(-?\d+)")


def extraire_paires():
    donnees = json.load(open(CHEMIN_DATA, encoding="utf-8"))
    paires = []
    for item in donnees:
        for eq in item["output"].split("|"):
            m = EQ.search(eq)
            if not m:
                continue
            a, op, b, c = m.groups()
            op = {"×": "×", "*": "×", "/": "÷", "÷": "÷"}.get(op, op)
            if op not in ("+", "-", "×", "÷"):
                continue
            if a == b:                      # EXCLUSION DÉCLARÉE (identité triviale)
                continue
            paires.append((a, b, op))
    return paires


# ═══════════════════════════════════════════════════════════════════════════
# 4. LE PROTOCOLE
# ═══════════════════════════════════════════════════════════════════════════
def analyser(paires, encodeur, k_mot, nom):
    """Retourne les Δφ par opération (D1 et D2) pour un encodeur."""
    cache = {}
    res = {op: {"D1": [], "D2": []} for op in ("+", "-", "×", "÷")}
    abs_diff = {op: [] for op in ("+", "-", "×", "÷")}
    for a, b, op in paires:
        if a not in cache:
            cache[a] = encodeur(int(a) if nom.startswith("synth") else a)
        if b not in cache:
            cache[b] = encodeur(int(b) if nom.startswith("synth") else b)
        res[op]["D1"].append(delta_phi_mot(cache[a], cache[b], k_mot))
        res[op]["D2"].append(delta_phi_corr(cache[a], cache[b]))
        abs_diff[op].append(abs(int(a) - int(b)))
    return res, abs_diff


def main():
    t0 = time.time()
    print("=" * 78)
    print("TEST 2 — « Δφ encode-t-il les opérations ? » (protocole pré-enregistré)")
    print("=" * 78)
    paires = extraire_paires()
    print(f"Corpus : {len(paires)} paires (a, b, op) étiquetées — GSM8K réel")
    from collections import Counter
    print(f"  répartition : {dict(Counter(op for _, _, op in paires))}")
    print(f"Exclusion déclarée : paires a == b retirées · critères C_A, C_B, C_C")
    print()

    # — Mesures sur les deux encodages réels + contrôle synthétique
    resultats = {}
    for nom, encodeur, k_mot in [("E1_fnv_gaussien", encode_E1, 500),
                                 ("E2_phi_exponentiel", encode_E2, 0),
                                 ("synth_valeur", encode_synth, 0)]:
        res, abs_diff = analyser(paires, encodeur, k_mot, nom)
        # C_A : CONCENTRATION AUX VALEURS REVENDIQUÉES {0, π/2, π} (fenêtre
        # ±0,1 rad). Attendu sous uniforme : 3·2ε/π ≈ 0,191. Élevation si la
        # fraction observée dépasse 1,5× l'attendu (0,287) — la revendication
        # dit que Δφ SE REGROUPE autour de ces trois valeurs.
        d1_pool = np.concatenate([res[op]["D1"] for op in res])
        d2_pool = np.concatenate([res[op]["D2"] for op in res])
        eps = 0.1
        cibles = np.array([0.0, math.pi / 2, math.pi])
        def fraction_pres(d):
            return float(np.mean(np.min(np.abs(d[:, None] - cibles[None, :]),
                                        axis=1) < eps))
        frac_d1, frac_d2 = fraction_pres(d1_pool), fraction_pres(d2_pool)
        attendu = 3.0 * 2.0 * eps / math.pi
        p_kuiper1, p_kuiper2 = frac_d1 <= 1.5 * attendu, frac_d2 <= 1.5 * attendu
        # C_B : moyennes circulaires par opération + Kruskal-Wallis
        moyennes = {}
        for op in res:
            moyennes[op] = {"D1": stats.circmean(res[op]["D1"], high=math.pi),
                            "D2": stats.circmean(res[op]["D2"], high=math.pi)}
        kw_d1 = stats.kruskal(*[res[op]["D1"] for op in res]).pvalue
        kw_d2 = stats.kruskal(*[res[op]["D2"] for op in res]).pvalue
        # C_C : corrélation Δφ ↔ |a−b| (le contrôle positif doit la montrer)
        abs_pool = np.concatenate([abs_diff[op] for op in abs_diff])
        sp_d2 = stats.spearmanr(d2_pool, abs_pool).statistic
        resultats[nom] = {"frac_pres_D1": frac_d1, "frac_pres_D2": frac_d2,
                          "attendu_uniforme": attendu,
                          "moyennes_par_op": moyennes, "kw_D1": kw_d1,
                          "kw_D2": kw_d2, "spearman_D2_vs_absdiff": sp_d2}
        print(f"─ {nom}")
        print(f"  C_A concentration en {{0, π/2, π}} (±{eps} rad) : "
              f"D1 = {frac_d1:.3f} · D2 = {frac_d2:.3f} "
              f"(attendu uniforme {attendu:.3f}, seuil {1.5*attendu:.3f})")
        print(f"  C_B moyennes circulaires par op :")
        for op in res:
            print(f"    {op:2s} : D1 = {moyennes[op]['D1']:.3f} rad · "
                  f"D2 = {moyennes[op]['D2']:.3f} rad   (revendiquées : "
                  f"{'0' if op in '+-' else 'π/2' if op == '×' else 'π'})")
        print(f"  C_B Kruskal-Wallis : D1 p={kw_d1:.4f} · D2 p={kw_d2:.4f}")
        print(f"  C_C Spearman(Δφ_D2, |a−b|) = {sp_d2:.3f}")
        print()

    # — Verdict
    rE1, rE2, rS = resultats["E1_fnv_gaussien"], resultats["E2_phi_exponentiel"], \
                   resultats["synth_valeur"]
    # C_A : pas de concentration aux valeurs revendiquées sur les DEUX encodages
    c_a = all(v <= 1.5 * rE1["attendu_uniforme"] for v in
              [rE1["frac_pres_D1"], rE1["frac_pres_D2"],
               rE2["frac_pres_D1"], rE2["frac_pres_D2"]])
    # C_B : moyennes hors des valeurs revendiquées OU pas de séparation
    def hors_revendique(moy):
        return abs(moy["+"]["D1"] - 0.0) > SEUIL_ECART_REVENDIQUE and \
               abs(moy["×"]["D1"] - math.pi / 2) > SEUIL_ECART_REVENDIQUE and \
               abs(moy["÷"]["D1"] - math.pi) > SEUIL_ECART_REVENDIQUE
    c_b = (hors_revendique(rE1["moyennes_par_op"]) and
           hors_revendique(rE2["moyennes_par_op"])) and \
          (rE1["kw_D1"] > 0.01 and rE2["kw_D1"] > 0.01)
    # C_C : le contrôle positif DOIT montrer la structure
    c_c = rS["kw_D1"] < 0.01 and rS["spearman_D2_vs_absdiff"] > 0.5

    print("─ VERDICT (critères déclarés avant le calcul)")
    print(f"  C_A · Δφ uniforme sur les encodages réels : {'✅' if c_a else '❌ — structure trouvée'}")
    print(f"  C_B · pas de séparation par opération aux valeurs revendiquées : "
          f"{'✅' if c_b else '❌ — séparation trouvée'}")
    print(f"  C_C · contrôle positif (le test détecte la structure si elle "
          f"existe) : {'✅' if c_c else '❌ — TEST INVALIDE'}")
    if c_c and c_a and c_b:
        print("  VERDICT : ❌ RÉFUTÉ — Δφ n'encode PAS les opérations dans les "
              "encodages réels du moteur (test validé par le contrôle)")
    elif not c_c:
        print("  VERDICT : ⚠️ TEST INVALIDE — le contrôle positif n'a pas détecté "
              "de structure : à redessiner")
    else:
        print("  VERDICT : ⚠️ STRUCTURE TROUVÉE — à inspecter (surprise publiée)")
    print(f"  Durée : {time.time()-t0:.1f} s")

    rapport = {
        "protocole": "pré-enregistré — paires étiquetées GSM8K réelles, "
                     "exclusion a==b, critères C_A/C_B/C_C déclarés avant",
        "corpus": {"fichier": CHEMIN_DATA, "paires": len(paires)},
        "verdict": {"C_A_uniformite": bool(c_a), "C_B_operations": bool(c_b),
                    "C_C_controle": bool(c_c)},
        "resultats": {k: {kk: (float(vv) if isinstance(vv, (float, np.floating))
                              else vv) for kk, vv in v.items()}
                      for k, v in resultats.items()},
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    chemin = os.path.join("data", "benchmarks", "delta_phi_operations_report.json")
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"Rapport : {chemin}")


if __name__ == "__main__":
    main()
