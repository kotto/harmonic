# -*- coding: utf-8 -*-
"""
test_masses_118.py — LE TEST DE MENDELEÏEV.

Vérifie si une formule fermée reproduit les masses atomiques des 118 éléments
connus (références CODATA/IUPAC dans references_masses.json).

Critères d'évaluation (sans aucun paramètre ajusté) :
    écart moyen < 30 %  → ordre de grandeur correct (premier palier)
    écart moyen < 10 %  → comparable à Bethe-Weizsäcker (qui utilise 6
                          paramètres ajustés) — sans paramètres : historique
    écart moyen <  5 %  → très fort
    écart moyen <  1 %  → révolutionnaire

USAGE :
    1. Remplacez la fonction `masse_predite(Z)` ci-dessous par VOTRE formule
       (ou complétez computeH).
    2. Lancez :  python test_masses_118.py
    3. Le rapport complet (118 lignes + statistiques) est écrit dans
       rapport_masses_118.csv et affiché.

La normalisation doit être UNIQUE pour tous les Z (zéro paramètre libre).
"""

from __future__ import annotations

import json
import math
import os
import sys

DOSSIER = os.path.dirname(os.path.abspath(__file__))
PHI = (1 + math.sqrt(5)) / 2
PI, E = math.pi, math.e

with open(os.path.join(DOSSIER, "references_masses.json"), encoding="utf-8") as f:
    MASSES_REELLES = {int(k): float(v) for k, v in json.load(f).items()}


# ════════════════════════════════════════════════════════════════════════
# VOTRE FORMULE ICI — remplacez tout le bloc ci-dessous par la formule
# corrigée. Contrainte : AUCUN paramètre ajusté sur les 118 masses.
# ════════════════════════════════════════════════════════════════════════

# les 7 constantes harmoniques + dérivées (H₁..H₁₀ du tableau harmonique)
H = {1: PHI, 2: PI, 3: E, 4: math.sqrt(2), 5: math.sqrt(3), 6: math.sqrt(5),
     7: E / PI, 8: PHI * PHI, 9: PI * PI / PHI, 10: E * PHI}


def computeH(n: int) -> float:
    """Coefficient harmonique H_n par factorisation de Z en bases {2..10}
    (logique du tableau-periodique-harmonique.html — À CORRIGER si besoin)."""
    if n <= 10:
        return H[n]
    r, rem = 1.0, n
    for b in (10, 9, 8, 7, 6, 5, 4, 3, 2):
        while rem % b == 0:
            r *= H[b]
            rem //= b
    if rem > 1:
        a = min(rem - 1, 10)
        b2 = rem - a
        r *= (H[a] if a <= 10 else computeH(a)) * (H[b2] if b2 <= 10 else computeH(b2))
        if rem > 20:
            r /= PHI ** (rem - 20)          # amortissement (à revoir : cause de l'explosion)
    return r


# Normalisation unique : la masse de l'hydrogène (constante physique, pas un
# paramètre ajusté) — à adapter selon votre formulation.
M_H1 = 1.008


def masse_predite(Z: int) -> float:
    """LA formule de masse — à remplacer par votre version corrigée."""
    return M_H1 * (computeH(Z) / H[1]) * Z ** (PHI - 1)


# ════════════════════════════════════════════════════════════════════════
# LE PROTOCOLE — ne rien modifier en dessous
# ════════════════════════════════════════════════════════════════════════


def principal() -> None:
    lignes = []
    for Z in sorted(MASSES_REELLES):
        reelle = MASSES_REELLES[Z]
        predite = masse_predite(Z)
        ecart = abs(predite - reelle) / reelle if reelle else 0.0
        lignes.append((Z, reelle, predite, ecart))

    # rapport CSV complet
    chemin_csv = os.path.join(DOSSIER, "rapport_masses_118.csv")
    with open(chemin_csv, "w", encoding="utf-8") as f:
        f.write("Z,masse_reelle,masse_predite,ecart_pct\n")
        for Z, r_, p, ec in lignes:
            f.write(f"{Z},{r_:.6f},{p:.6f},{ec*100:.4f}\n")

    ecarts = [e[3] for e in lignes]
    ecarts.sort()
    moyen = sum(ecarts) / len(ecarts)
    median = ecarts[len(ecarts) // 2]
    pire = lignes[ecarts.index(ecarts[-1])]

    print("═" * 66)
    print("LE TEST DE MENDELEÏEV — masses prédites vs CODATA/IUPAC (118)")
    print("═" * 66)
    print(f"Écart moyen  : {moyen*100:7.2f} %")
    print(f"Écart médian : {median*100:7.2f} %")
    print(f"Pire cas     : Z={pire[0]} réel {pire[1]:.3f} · prédit {pire[2]:.3f} "
          f"· écart {pire[3]*100:.1f} %")
    print(f"≤ 30 % : {sum(1 for e in ecarts if e < 0.30)}/118 "
          f"· ≤ 10 % : {sum(1 for e in ecarts if e < 0.10)}/118 "
          f"· ≤ 5 % : {sum(1 for e in ecarts if e < 0.05)}/118 "
          f"· ≤ 1 % : {sum(1 for e in ecarts if e < 0.01)}/118")
    print("═" * 66)
    print(f"Rapport complet → {chemin_csv}")
    palier = ("RÉVOLUTIONNAIRE (< 1 %)" if moyen < 0.01
              else "TRÈS FORT (< 5 %)" if moyen < 0.05
              else "HISTORIQUE SANS PARAMÈTRES (< 10 %)" if moyen < 0.10
              else "ORDRE DE GRANDEUR (< 30 %)" if moyen < 0.30
              else "À CORRIGER (≥ 30 %)")
    print(f"VERDICT : {palier}")
    print("═" * 66)


if __name__ == "__main__":
    principal()
