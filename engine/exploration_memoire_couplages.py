# -*- coding: utf-8 -*-
"""
EXPLORATION — LA MÉMOIRE SÉPARE-T-ELLE LES COUPLAGES ?
=======================================================
Question : la mémoire d'or (φ, noyau K(t) = E_{1/φ}(−φ·t^{1/φ})) est-elle
ce qui sépare α_EM du couple (α_W, α_S) ?

Script d'EXPLORATION (non bloquant sur les issues physiques, bloquant sur
la cohérence interne T0). S'appuie sur la machinerie validée de
verif_alpha_vertex.py (contrôles C1/C3/C3b du 27/08).

Sortie : resultat_exploration_memoire.json
"""

import json
import math
import os
import sys
from datetime import datetime

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI

# cibles corpus / PDG
CODATA_ALPHA_INV = 137.035999177          # CODATA-2022
ALPHA_5F_CANONIQUE = 137.036031356        # valeur canonique corpus (DERIVATION_ALPHA_EM.md)
ALPHA_EM_MZ_INV = 127.950                 # α^-1(m_Z), scheme MS-bar
SIN2W_PDG = 0.23122                       # sin²θ_W (MS-bar, m_Z)
ALPHA_W_MZ_REELLE = 0.03391               # g²/4π avec g = 0.6530 (PDG)

TOL_ID = 1e-12

resultats = []   # chaque test : dict(nom, statut, detail)


def note(nom, statut, detail):
    resultats.append({"nom": nom, "statut": statut, "detail": detail})
    print(f"  [{statut:>3}] {nom} : {detail}")


# ---------------------------------------------------------------- noyau (pipeline validé par l'assaut)
def Ktilde2(omega, alpha=ALPHA):
    """|K~(w)|² — forme réelle développée (validée C3b à 2.8e-17 par l'assaut)."""
    num = omega ** (2.0 * alpha - 2.0)
    den = omega ** (2.0 * alpha) + 2.0 * PHI * math.cos(math.pi * alpha / 2.0) * omega ** alpha + PHI ** 2
    return num / den


# ================================================================== T0 — cohérence du corpus
print("=" * 74)
print("  EXPLORATION — LA MÉMOIRE SÉPARE-T-ELLE LES COUPLAGES ?")
print("=" * 74)
print(datetime.now().isoformat(timespec="seconds"))
print()
print("[T0 — cohérence interne du corpus]")

ok_interne = True

alpha_W = 1.0 / 30.0
f_W = (math.sqrt(2.0) * math.sqrt(3.0) * math.sqrt(5.0)) ** -2
ok_T0a = abs(f_W - alpha_W) < TOL_ID
ok_interne &= ok_T0a
note("T0a α_W = (√2·√3·√5)⁻² = 1/30", "OK" if ok_T0a else "FAIL", f"écart {abs(f_W - alpha_W):.2e}")

alpha_S = 1.0 / (2.0 * PHI ** 3)
note("T0b α_S = 1/(2φ³)", "OK", f"= {alpha_S:.6f} (PDG m_Z : 0.118 ± 0.001)")

alpha_5f = math.pi ** 4 * math.exp(-4.0) * PHI ** (-5.0) * 2.0 ** (-0.5) * 3.0 ** (-2.5)
inv5f = 1.0 / alpha_5f
ec_canon = abs(inv5f - ALPHA_5F_CANONIQUE) / ALPHA_5F_CANONIQUE
ec_codata = abs(inv5f - CODATA_ALPHA_INV) / CODATA_ALPHA_INV
ok_T0c = ec_canon < 1e-6
ok_interne &= ok_T0c
note("T0c formule 5-facteurs du registre", "OK" if ok_T0c else "FAIL",
     f"α⁻¹ = {inv5f:.9f} ; vs canonique 137.036031356 ({ec_canon:.2e}) ; vs CODATA ({ec_codata:.2e})")

alpha_EM = 1.0 / CODATA_ALPHA_INV

# ---------------------------------------------------------------- T1 — tripartition par rapport à φ
print()
print("[T1 — tripartition : quelle place pour φ (la mémoire) dans chaque couplage ?]")
# α⁻¹_W = 30            : aucun facteur φ              -> mémoire absente
# α⁻¹_EM = π⁴e⁻⁴φ⁻⁵√2⁻¹√3⁻⁵ : φ⁻⁵ (la mémoire AMPLIFIE le couplage EM)
# α⁻¹_S  = 2φ³          : φ³ pur (la mémoire EST le contenu)
ln_phi = math.log(PHI)
frac_W = 0.0
frac_EM = (-5.0 * ln_phi) / math.log(inv5f)
frac_S = (3.0 * ln_phi) / math.log(2.0 * PHI ** 3)
trip = {"alpha_W": {"phi_dans_alpha_inv": "absent", "fraction_ln": frac_W},
        "alpha_EM": {"phi_dans_alpha_inv": "φ⁻⁵ (signe −)", "fraction_ln": frac_EM},
        "alpha_S": {"phi_dans_alpha_inv": "φ⁺³ (pur)", "fraction_ln": frac_S}}
note("T1 tripartition mémoire", "INFO",
     f"α_W : φ absent (fraction 0.000) · α_EM : φ⁻⁵ → fraction {frac_EM:+.3f} de ln α⁻¹ · α_S : φ⁺³ pur → fraction {frac_S:+.3f}")
note("T1 lecture", "INFO",
     "α_W = seul couplage SANS φ (exact) · α_EM = seul couplage où la mémoire AMPLIFIE (φ⁻⁵ dans l'inverse) · α_S = mémoire pure. Tripartition, pas échelle.")

# ---------------------------------------------------------------- T2 — impédances du noyau au vertex
print()
print("[T2 — l'impédance de mémoire au vertex 1↔½ : ce que chaque couplage paie]")
K_cont = Ktilde2(0.5)
# transparence du mode ½ (identité φ + φ⁻¹ = √5, contrôle C1 de l'assaut)
transp = abs(PHI + 1.0 / PHI - math.sqrt(5.0)) < TOL_ID
K_tour = 1.0 if transp else float("nan")
ratio_W_EM = alpha_W / alpha_EM
impedance = 1.0 / K_cont
facteur = ratio_W_EM * K_cont
note("T2a réponse du noyau continu à ω₀/2", "INFO", f"|K̃(1/2)|² = {K_cont:.6f} — l'impédance de mémoire")
note("T2b réponse du spectre de tour au mode ½", "OK" if transp else "FAIL",
     f"φ+φ⁻¹ = √5 (écart {abs(PHI + 1.0 / PHI - math.sqrt(5.0)):.1e}) → réponse unitaire : le mode ½ est transparent")
note("T2c séparation quantitative", "INFO",
     f"α_W/α_EM = {ratio_W_EM:.4f} vs impédance 1/|K̃|² = {impedance:.4f} → facteur {facteur:.3f} : "
     "la transparence QUALITATIVE sépare W de EM, mais l'impédance seule ne chiffre pas le rapport")

# ---------------------------------------------------------------- T3 — règle produit α_EM = α_W·α_S·K ?
print()
print("[T3 — règle produit : α_EM = α_W·α_S·K avec K du corpus ?]")
K_star = alpha_EM / (alpha_W * alpha_S)
famille = []
for k in range(-4, 5):
    famille.append((f"phi^{k}", PHI ** k))
for k in range(-3, 4):
    famille.append((f"e^{k}/phi", math.exp(k / PHI)))
    famille.append((f"e^{k}", math.exp(float(k))))
for n in range(2, 31):
    famille.append((f"{n}", float(n)))
    famille.append((f"sqrt({n})", math.sqrt(n)))
for p in (-2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0):
    famille.append((f"pi^{p}", math.pi ** p))
famille += [("2pi", 2.0 * math.pi), ("(2pi)^2", (2.0 * math.pi) ** 2), ("pi+phi", math.pi + PHI),
            ("pi*phi/2", math.pi * PHI / 2.0), ("phi^0.5", PHI ** 0.5), ("e^(1/phi)", math.exp(1.0 / PHI))]
classe = sorted(famille, key=lambda kv: abs(kv[1] - K_star))[:5]
hits = [kv for kv in famille if abs(kv[1] - K_star) / K_star < 1e-4]
top = ", ".join(f"{nom}={val:.6f} (écart {abs(val - K_star) / K_star:.2e})" for nom, val in classe)
note("T3 scan famille fermée", "INFO" if not hits else "HIT",
     f"K* = α_EM/(α_W·α_S) = {K_star:.6f} ; meilleurs : {top} ; hits à 1e-4 : {len(hits)}")
eps_e = abs(math.exp(1.0 / PHI) - K_star) / math.exp(1.0 / PHI)
note("T3 résidu du meilleur candidat", "INFO",
     f"meilleur candidat e^(1/φ) à {eps_e:.2e} — AU-DESSUS de la barre 1e-4 : rien à revendiquer")

# ---------------------------------------------------------------- T4 — sin²θ_W : le test d'échelle
print()
print("[T4 — sin²θ_W : les échelles sont-elles mélangées dans le registre ?]")
sin2_thomson = alpha_EM * (1.0 / alpha_W)          # α_EM/α_W = 30/137.036
sin2_mz = (1.0 / ALPHA_EM_MZ_INV) / alpha_W        # α_EM(m_Z)/α_W = 30/127.950
g_thomson = abs(sin2_thomson - SIN2W_PDG) / SIN2W_PDG
g_mz = abs(sin2_mz - SIN2W_PDG) / SIN2W_PDG
g_w = abs(alpha_W - ALPHA_W_MZ_REELLE) / ALPHA_W_MZ_REELLE
note("T4a sin²θ_W implicite (α_EM de Thomson)", "INFO", f"{sin2_thomson:.6f} vs PDG {SIN2W_PDG} → écart {100 * g_thomson:.2f} %")
note("T4b sin²θ_W implicite (α_EM(m_Z))", "INFO", f"{sin2_mz:.6f} vs PDG {SIN2W_PDG} → écart {100 * g_mz:.2f} %")
note("T4c α_W du registre vs α_W(m_Z) réelle", "INFO", f"{alpha_W:.6f} vs {ALPHA_W_MZ_REELLE} → écart {100 * abs(alpha_W - ALPHA_W_MZ_REELLE) / ALPHA_W_MZ_REELLE:.2f} %")
note("T4 lecture", "OBS",
     f"à échelle appariée m_Z, les écarts tombent de {100 * g_thomson:.1f} % à {100 * g_mz:.1f} % / "
     f"{100 * abs(alpha_W - ALPHA_W_MZ_REELLE) / ALPHA_W_MZ_REELLE:.1f} % : le registre mélange l'échelle de Thomson et celle de m_Z — à corriger")

# ---------------------------------------------------------------- T5 — les deux résidus ~5×10⁻⁴ sont-ils le même ?
print()
print("[T5 — cohérence des résidus indépendants]")
req_norm = CODATA_ALPHA_INV * K_cont            # norme d'espace requise (diagnostic de l'assaut, patte a)
eps_F10 = abs(55.0 - req_norm) / 55.0
ec_res = abs(eps_e - eps_F10)
note("T5a résidu F₁₀ (assaut vertex)", "INFO", f"norme requise {req_norm:.4f} vs F₁₀=55 → {eps_F10:.2e}")
note("T5b résidu e^(1/φ) (règle produit)", "INFO", f"{eps_e:.2e}")
note("T5c résidus distincts ?", "NON" if ec_res >= 1e-5 else "OUI",
     f"|ε₁−ε₂| = {ec_res:.2e} → " + ("deux corrections indépendantes, pas de piste commune" if ec_res >= 1e-5
                                      else "correction commune possible — à creuser"))

# ---------------------------------------------------------------- synthèse
print()
print("=" * 74)
print("  SYNTHÈSE")
print("=" * 74)
print("  1. α_W est exact ET sans mémoire : son exactitude s'explique structurellement")
print("     (vertex géométrique pur, mode ½ transparent — cohérent avec l'assaut vertex).")
print("  2. α_EM est le SEUL couplage dont l'inverse porte φ avec signe − : la mémoire")
print("     amplifie l'électromagnétisme. EM = couplage de la ligne de mémoire elle-même")
print("     (U(1) = liberté de phase résiduelle de la projection à mémoire, Maillon 3 §7).")
print("  3. α_S est fait DE la mémoire (φ³ pur) : confinement = mémoire totale (R3).")
print("  4. Quantification manquante : l'impédance |K̃(1/2)|² = 0.4012 ne chiffre pas")
print("     α_W/α_EM (facteur 1.83) ; le produit α_W·α_S·e^(1/φ) reste à 3.6e-4.")
print("  5. Correction de registre à faire : α_W et α_EM du corpus sont à des échelles")
print("     différentes (Thomson vs m_Z) — à échelle appariée, 1.4 % au lieu de 5.3 %.")
print(f"  Cohérence interne T0 : {'OK' if ok_interne else 'ÉCHOUÉE'}")

synthese = {
    "date": datetime.now().isoformat(timespec="seconds"),
    "question": "la mémoire sépare-t-elle les couplages ?",
    "coherence_interne": ok_interne,
    "tests": resultats,
    "nombres_cles": {
        "K_cont": K_cont, "K_tour_mode_1_2": K_tour, "ratio_W_EM": ratio_W_EM,
        "K_star": K_star, "eps_e": eps_e, "eps_F10": eps_F10,
        "sin2_thomson": sin2_thomson, "sin2_mz": sin2_mz,
        "fractions_phi": {"W": frac_W, "EM": frac_EM, "S": frac_S},
    },
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultat_exploration_memoire.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(synthese, f, ensure_ascii=False, indent=2)
print(f"  JSON : {out}")

sys.exit(0 if ok_interne else 1)