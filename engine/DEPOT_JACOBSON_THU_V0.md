# DEPOT JACOBSON THU V0 — La voie thermodynamique des horizons × noyau ABC

**Question testée :** le branchement du noyau ABC (α = 1/φ) sur la température d'Unruh peut-il fournir la dérivation thermodynamique d'Einstein (Problème V3 de `PROBLEME_OUVERT_EINSTEIN.md`) ?
**Méthode :** chaque nombre déposé est calculé par machine (`verif_jacobson_thu_v0.py`, leçon FORCE V1.2).
**Sortie :** exit **0** — 8/8 contrôles conformes aux signatures attendues (`resultat_jacobson_thu_v0.json`).

---

## 1. LES RÉCLAMATIONS TESTÉES

| ID | Réclamation | Signature attendue | Résultat machine |
|----|-------------|--------------------|------------------|
| C1 | Chaîne de Jacobson : T_U·(dS/dA) = a·c²/(8πG) — le **8π émerge de 2π (Unruh) × 4 (Bekenstein-Hawking)** | exact | ✅ rel. 1.60e-16 (nat : 0.039788735773 = 1/(8π) ; SI : 5.3579e25 = c²/(8πG)) |
| C2 | T_Hawking(M_Pl) = T_Pl/(8π) **≠** T_Pl/ln φ (réfutation déjà consignée dans `RELATION_G_h_kB_CONJECTURE.md`) | ratio = 8π/ln φ ≫ 1 | ✅ **52.228021** (T_H(M_Pl) = 5.6372e30 K vs 2.9442e32 K) |
| C3 | Queue de Mittag-Leffler : E_α(−x) ~ x⁻¹/Γ(1−α) pour α = 1/φ — **loi de puissance, pas e^(−x)** | pente → 1 ; amplitude → 1/Γ(1−α) | ✅ pente **1.0152** ; amplitude **1.02184** (±3 %) ; Γ(1−α) = 2.3258 ; E_α(−20)/e^(−20) = **1.07e7** |
| C4 | Le noyau ABC est **sans échelle** : λ_eff(t) = −d ln K/dt ∝ t^(α−1) → ratio λ_eff(2t)/λ_eff(t) → 1/2 | ≠ 1 (exponentiel) | ✅ **0.4961** — aucun e^(−t/T_U) n'existe dans K |
| C5 | Irrationalité maximale : liminf_q q·‖qα‖ **maximisé** par α = 1/φ à 1/√5 (Hurwitz 1891) | 0.447214, maximum possible | ✅ **0.447209** (1/√2 : 0.353552 ; 1/π : 0.003406 ; 1/e : 0.141304) |
| C6 | κ = 8πG **n'émerge pas** de B(α) | B(1/φ) ≠ 1/(8π) | ✅ B_AB = 0.808423, B_dépôt = 0.850651, vs 1/(8π) = 0.039789 ; B_AB×8π = 20.3179 ≠ 1 |
| C7 | Masse de Hawking dorée M_Pl·ln φ/(8π) — calculée mais **sans lien** | ≈ 0.019146 | ✅ **0.019147** (M = 4.167e-10 kg) |
| C8 | T_Unruh(a = gravité de surface c⁴/(4GM)) = T_Hawking(M) **exactement** | écart < 1e-12 | ✅ **0.00e+00** pour M ∈ {1, 10, 10⁶} M☉ |

---

## 2. VERDICT : `JACOBSON_V0_CHAINE_EXACTE_PONT_DIRECT_REFUTE`

### 2.1 Ce qui est EXACT et re-vérifié (la porte est la bonne)

1. **La chaîne thermodynamique de Jacobson est bit-exacte** : δQ = T_U dS sur un horizon de Rindler local, avec T_U = ħa/(2πck_B) et dS = k_Bc³·dA/(4Għ), donne T_U·dS/dA = a·c²/(8πG). Le κ = 8πG des équations d'Einstein est **littéralement 2π × 4** — le 2π d'Unruh, le 1/4 de Bekenstein-Hawking. (C1, rel. 1.6e-16.)
2. **Unruh au bord de l'horizon = Hawking, identiquement** (C8, écart 0.00e+00) : l'observateur qui « survit » au bord d'un trou noir de masse M voit exactement T_Hawking. C'est le seul énoncé quantitatif exact que la THU peut déposer aujourd'hui sur un horizon — et il est déjà le pont thermodynamique complet.

### 2.2 Ce qui est RÉFUTÉ (le pont naïf n'existe pas)

3. **La conjecture V3 telle qu'énoncée — « K(τ) ∝ e^(−t/T_U) » — est RÉFUTÉE** (C3 + C4). Le noyau ABC décroît en loi de puissance x⁻¹/Γ(1−α) et son taux de décroissance effectif suit λ_eff ≈ α/t (ratio 0.4961 entre t et 2t ; une exponentielle donnerait 1.0). **Un noyau sans échelle ne peut pas encoder une température** : T_U introduit une échelle (a), K n'en contient aucune. Le branchement ne se fera PAS par une échelle de temps du noyau.
4. **κ = 8πG n'émerge pas de B(α)** (C6). Dans la dérivation de Jacobson, κ est fixé par la limite newtonienne (appariement avec la loi de Newton), pas par la normalisation du noyau. Toute prétention inverse serait une double comptabilité.
5. **Les rapprochements numériques T* ↔ Hawking restent réfutés** (C2 : ratio 52.23 ; C7 : masse 0.0191 M_Pl sans lien).

### 2.3 Ce qui reste AXIOMATIQUE (honnêteté)

6. **α = 1/φ est confirmé comme l'unique ordre d'irrationalité maximale** (C5 : liminf 0.447209 vs borne de Hurwitz 1/√5 = 0.447214 ; tous les autres candidats < 0.36) — mais c'est un **axiome** (stabilité par non-répétition, A4), **pas une conséquence d'Unruh**. La dérivation d'α depuis la thermodynamique des horizons reste à faire ou à abandonner.

---

## 3. PISTE RÉORIENTÉE (dépôt suivant)

Le réfuté C4 n'est pas une impasse : il **contraint** le point de branchement.

- ❌ Brancher K(t) sur une échelle de temps (e^(−t/T_U)) — impossible, K est sans échelle.
- 🔬 Brancher **D^(1/φ)** (l'opérateur, pas le noyau) sur la **phase du vide** : l'observateur accéléré voit la phase e^{iωt} du vide de Minkowski ; l'action de D^(1/φ) sur cette phase produit-elle le facteur thermique de KMS à T_U = a/2π ? (analogue : oscillateur fractionnaire de Bateman.)
- 🔬 Exprimer l'entropie S = A/4G via l'**aire mesurée par la métrique V1** g_μν = Re[(∂_μΨ₁)(∂_νΨ₁)*] (question laissée ouverte dans `PROBLEME_OUVERT_EINSTEIN.md`, §V3).
- 🔬 Troub noir = frontière ouverte (P9 de `paradoxes-quantiques.html`) : le statut ne change pas — mais la porte d'entrée est désormais **chiffrée** : 8π = 2π×4, bit-exact.

---

## 4. BORNES HONNÊTES

| Item | Statut |
|---|---|
| Chaîne de Jacobson (C1) et identité Unruh-Hawking (C8) | ✅ exactes — mais ce sont des résultats **standards** (Jacobson 1995), re-vérifiés avec les constantes THU |
| Réfutation du pont direct K ∝ e^(−t/T_U) | ✅ nouvelle réclamation déposée, machine-vérifiée |
| Unicité α = 1/φ (Hurwitz) | ✅ confirmée — mais **axiomatique**, non dérivée d'Unruh |
| Trous noirs / information | ❌ toujours frontière ouverte (P9) |
| Pont D^(1/φ) ↔ phase de KMS | 🔬 non testé — prochain dépôt |

---

## 5. FICHIERS

- `verif_jacobson_thu_v0.py` — vérification machine des 8 contrôles (exit 0 ssi signatures conformes)
- `resultat_jacobson_thu_v0.json` — valeurs complètes horodatées
- Sources : `PROBLEME_OUVERT_EINSTEIN.md` (V3, V5), `abc_kernel.py`, `RELATION_G_h_kB_CONJECTURE.md`, `DERIVATION_TSTAR_IRRATIONNALITE_MAXIMALE.md`

> *« La thermodynamique des horizons donne à la THU sa première identité bit-exacte sur un trou noir : κ = 2π×4. Mais le noyau ABC, sans échelle, ne peut pas être une température — il faut brancher l'opérateur D^(1/φ) sur la phase du vide, pas le noyau sur un temps. La porte est chiffrée ; elle n'est pas franchie. »*

— Dépôt JACOBSON THU V0, 30/08/2026
