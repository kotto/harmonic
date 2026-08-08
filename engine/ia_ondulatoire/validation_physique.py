# -*- coding: utf-8 -*-
"""
validation_physique.py — CERTIFICAT REPRODUCTIBLE du Module Physique Harmonique
===============================================================================
Vérifie que le module `physique.py` reproduit les résultats validés de la
session (08/08/2026) : constantes, masses, certificat vallée, prédiction.

Usage : python validation_physique.py   (sortie non nulle en cas d'échec)
"""

import sys

from physique import (PhysiqueHarmonique, ALPHA_HARMONIQUE, ALPHA_CODATA,
                      GAGUT, MPME_CODATA, M_P_U, masse_atomique,
                      energie_liaison, est_question_physique)

PH = PhysiqueHarmonique()

TESTS = []


def test(nom, condition, detail=""):
    TESTS.append((nom, bool(condition), detail))
    print(f"  {'OK ' if condition else 'KO '} {nom}" + (f" — {detail}" if detail else ""))


print("CERTIFICAT MODULE PHYSIQUE HARMONIQUE")
print("=" * 70)

# ── 1. constantes vérifiées ───────────────────────────────────────────
err_alpha = abs(ALPHA_HARMONIQUE - ALPHA_CODATA) / ALPHA_CODATA
test("alpha : précision >= 99,9999 %", err_alpha < 1e-6,
     f"prec={1 - err_alpha:.8f}")
err_gagut = abs(GAGUT - MPME_CODATA) / MPME_CODATA
test("GAGUT m_p/m_e : écart <= 0,002 %", err_gagut < 2e-5,
     f"ecart={err_gagut:.2e}")
err_mp = abs(M_P_U - 1.0072764666) / 1.0072764666
test("m_p = m_e·6π⁵ : écart <= 0,002 %", err_mp < 2e-5,
     f"m_p={M_P_U:.6f} u")

# ── 2. masses connues (AME2020) ────────────────────────────────────────
for z, a, tol in ((26, 56, 0.01), (92, 238, 0.01), (82, 208, 0.01),
                  (50, 118, 0.01), (6, 12, 0.5)):
    m_pred = masse_atomique(z, a)
    m_reel = PH.masses_ames.get((z, a))
    if m_reel is None:
        test(f"masse Z={z} A={a} : donnée AME présente", False)
        continue
    ec = abs(m_pred - m_reel) / m_reel * 100
    test(f"masse {z}/{a} : écart <= {tol} %", ec <= tol, f"pred={m_pred:.4f} "
         f"reel={m_reel:.4f} ecart={ec:.4f} %")

# ── 3. certificat vallée (536 noyaux, 0,004 %) ─────────────────────────
v = PH.verification()
test("certificat : 536 noyaux vallée", v["vallee_noyaux"] == 536,
     f"n={v['vallee_noyaux']}")
test("certificat : écart moyen <= 0,005 %",
     v["vallee_ecart_moyen_pct"] is not None and v["vallee_ecart_moyen_pct"] <= 0.005,
     f"ecart={v['vallee_ecart_moyen_pct']:.5f} %")
test("certificat : 0 paramètre ajusté", v["parametres_ajustes"] == 0)

# ── 4. cohérence physique ──────────────────────────────────────────────
b_fe = energie_liaison(26, 56)
test("Fe-56 : B/A dans [8,5 ; 9,0] MeV (pic de liaison)", 8.5 <= b_fe / 56 <= 9.0,
     f"B/A={b_fe / 56:.3f}")
b_pb = energie_liaison(82, 208)
test("Pb-208 : B dans [1620 ; 1650] MeV", 1620 <= b_pb <= 1650,
     f"B={b_pb:.1f}")

# ── 5. prédiction ex-ante île de stabilité ─────────────────────────────
il = PH.ile_stabilite()
z119 = [e for e in il["elements"] if e["z"] == 119][0]
test("île : Z=119 prédit, pas de fermeture forte à N=184",
     z119["s2n_184"] < z119["s2n_max"] and z119["s2n_max"] > 10,
     f"S_2n max={z119['s2n_max']} (N={z119['n_max_s2n']}) vs S_2n(184)={z119['s2n_184']}")
test("île : 23 éléments (Z=104..126) prédits", len(il["elements"]) == 23)

# ── 6. routage cerveau ─────────────────────────────────────────────────
test("routage : 'combien vaut la masse du fer 56' → physique",
     est_question_physique("combien vaut la masse du fer 56"))
test("routage : 'calcule 3 + 5' → pas physique",
     not est_question_physique("calcule 3 + 5"))
test("routage : 'si x vaut 2, combien vaut x fois 3' → pas physique",
     not est_question_physique("si x vaut 2, combien vaut x fois 3"))

# ── 6b. régressions P1.2 (08/08/2026) : pas de pollution de sous-chaînes ─
for q in ("quelle est la vitesse de la lumière en miles",
          "que signifie E=mc2",
          "combien d'étoiles dans la Voie lactée",
          "quelle est la plus grande île du monde",
          "combien de chevaux a une Formule 1",
          "qui a écrit les Misérables"):
    test(f"régression : '{q[:38]}…' → pas physique",
         not est_question_physique(q))
test("régression : 'prédis l'île de stabilité pour Z=119' → physique",
     est_question_physique("prédis l'île de stabilité pour Z=119"))
r_ile = PH.repondre("prédis l'île de stabilité pour Z=119")
test("régression : réponse île = prédiction ex-ante",
     r_ile is not None and r_ile["type"] == "ile_stabilite")

# ── 7. réponses françaises ─────────────────────────────────────────────
r1 = PH.repondre("masse de l'uranium 238")
test("réponse : masse U-238 structurée",
     r1 is not None and r1["type"] == "isotope" and "0.006" in r1["texte"])
r2 = PH.repondre("donne les constantes harmoniques")
test("réponse : constantes", r2 is not None and "α" in r2["texte"])

# ── bilan ──────────────────────────────────────────────────────────────
n_ok = sum(1 for _, ok, _ in TESTS if ok)
print("=" * 70)
print(f"BILAN : {n_ok}/{len(TESTS)} tests OK")
sys.exit(0 if n_ok == len(TESTS) else 1)
