# RÉSULTAT F12 — MORT 10 / SINGULETS DE COUPLAGE : PSEUDORÉALITÉ 2̄ ≅ 2 ET RÈGLES DE SÉLECTION DES MASSES — V0

**Date : 2026-09-04. Verdict machine : `V+ M10_SINGULETS_FERME` — exit 0.**

Exécution de `verif_m10_singulets_v0.py` sur la frontière gelée
`FRONTIERE_M10_SINGULETS_V0.md` (commit **fe3ba9a**, dépôt-d'abord — C0a
OK : frontière 19:38:34 < exécution 19:40:07). Sortie :
`resultat_m10_singulets_v0.json` (déterministe, aucune graine, machinerie
verbatim des dépôts : triple natif M6 {σ_x, σ_y, σ_z} et ε = JM
(1dc6fcf/717edee), Casimir complet et sommes de Kronecker M8 (ff39bec),
produits M9 (b502e88), famille Bateman et composés d'Euler aux angles M7
[0.3, 0.7, 1.1, 2.3]).

**Objet M10 : le squelette de sélection du secteur type-Higgs/Yukawa est
COMPTÉ par la machine** — quels couplages scalaires sont permis, combien
d'invariants indépendants, avec quelles structures tensorielles. Aucune
bibliothèque de théorie des champs, aucune table CG importée.

---

## 1. LE VERDICT — V+ M10_SINGULETS_FERME, exit 0

**C0a–C7 tous passés ET D1 ET D2 ET D3 passées** :

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 19:38:34 < 19:40:07 |
| C1 filiation ε | **OK** | \|ε−JM\|, \|ε²+I\|, \|ε^T+ε\|, \|Im ε\| = **0.0 bit-exact** — ε EST l'objet natif M6 |
| C2 pseudoréalité | **OK** | max \|ε·Ū − U·ε\| = **5.373833866861023e-17** (96 θ × 3 générateurs) ; **1.1102230246251565e-16** (composés Euler/Bateman) — 2̄ ≅ 2 |
| C3 Inv(2⊗2) | **OK** | clusters {8:3, 0:1} dév 0.0 ; **dim Inv == 1** ; tr(P_1·Sym²) = **0.0** ; tr(P_1·(I−Sym²)) = 0.9999999999999998 |
| C4 Catalan | **OK** | singulets 2^{⊗n} == **[0, 1, 0, 2, 0, 5, 0, 14, 0, 42]** — écart entier **0** |
| C5 sélection | **OK** | 2⊗(2l+1) : **[0,0,0,0,0,0,0]** (l=0..6) ; 3⊗3 = {0:1, 8:3, 24:5} dév 4.440892098500626e-15 |
| C6 Weinberg 2^{⊗4} | **OK** | invariance \|J_a·v\| = **0.0** ; Gram ⟨v1,v1⟩ = 4.0, ⟨v2,v2⟩ = 4.0, ⟨v1,v2⟩ = 2.0, **det = 12.0** (rang 2) |
| C7 CG ½⊗½ | **OK** | eigen-vecteurs **0.0 ×8** (λ = 8,8,8,0 ; m = 2,0,−2,0) ; orthonormalité 2.220446049250313e-16 ; tr(P_triplet·Sym²) = **3.0** |

| Conséquence | Résultat | Valeur machine |
|---|---|---|
| **D1** comptage Catalan | **OK** | le nombre de couplages invariants indépendants à n doublets est un théorème machine : 0 si n impair, Catalan [1, 2, 5, 14, 42] si pair |
| **D2** sélection scalaire | **OK** | 2⊗entier : JAMAIS de singulet ; 2⊗2 : exactement 1, via ε antisymétrique ; 3⊗3 : exactement 1 — le doublet ne se couple au scalaire qu'avec un autre doublet |
| **D3** Weinberg + CG | **OK** | DEUX invariants ε indépendants (det 12.0) ; CG ½⊗½ uniques gelés bit-exact — le seul mélange verrouillable sans générations |

Un seul contrôle en échec aurait déclenché `V4_REFUTE` exit 1 sans
sauvetage — précédents M6 (717edee), M7 (ef67f8a), M8 (ff39bec), M9
(b502e88). Aucun. Hygiène consignée (leçon FORCE V1.2) : deux fonctions
mortes de la sonde (vestiges de conception, jamais exécutés) purgées
AVANT la première exécution ; une ligne résiduelle du verif purgée avant
toute exécution. Aucun arbitrage machine n'a porté sur du code défectueux.

## 2. CE QUE M10 ÉTABLIT MAINTENANT

1. **La pseudoréalité est un fait machine (T1/C2).** ε = JM natif
   intertwine la conjugaison : ε·Ū == U·ε à 5.4e-17 sur la grille et
   1.1e-16 sur les composés d'Euler/Bateman. Le doublet conjugué 2̄ EST le
   doublet — la conjugaison n'introduit aucune représentation nouvelle.
   C'est la racine native de la structure pseudoréelle de SU(2).

2. **Le couplage de Yukawa a une racine native (T2/C3).** Inv(2⊗2) = 1 et
   le singulet est ANTISYMÉTRIQUE (tr(P_1·Sym²) = 0.0) : la contraction
   ε^{ij} des couplages de type Yukawa EST l'objet natif M6, et un doublet
   SEUL n'a pas de couplage scalaire ψψ — le couplage exige deux doublets
   distincts appariés par ε.

3. **L'espace des invariants est compté, pas postulé (T3/C4/D1).** À n
   doublets : [0, 1, 0, 2, 0, 5, 0, 14, 0, 42] — écart entier 0. En
   particulier l'opérateur de Weinberg (quatre doublets) porte EXACTEMENT
   deux invariants indépendants, et la machine les exhibe : les deux
   appariements ε (12|34 et 13|24), invariants bit-exact (|J_a·v| = 0.0),
   Gram (4, 4, 2), det 12.0 — indépendants, non dégénérés.

4. **La règle de sélection scalaire est fermée (T4/C5/D2).** Un doublet ne
   se couple JAMAIS au scalaire avec une représentation entière
   (2⊗(2l+1) : zéro singulet, l=0..6 — re-witness M9) ; le couplage
   scalaire d'un doublet exige un AUTRE doublet (via ε), et le canal
   3⊗3 porte exactement une jauge invariante — la structure type H†H / L·S
   aperçue en M9 D3.

5. **Le seul « mélange » verrouillable est gelé (T5/C7).** La multiplicité
   1 de chaque bloc de ½⊗½ rend les CG uniques : les quatre vecteurs
   explicites sont eigen-vecteurs exacts (0.0 ×8) — le triplet EST Sym²
   (tr = 3.0, liant M7/M8/M9). Toute matrice de mélange PHYSIQUE (CKM/
   PMNS) exige des générations : consigné.

6. **Le protocole a tenu sans accroc (leçon FORCE V1.2).** Première
   exécution de la sonde propre ; purges d'hygiène (fonctions mortes de
   conception, ligne résiduelle) faites AVANT toute exécution et
   consignées par transparence. Aucun défaut estimateur, aucun sauvetage.

## 3. HONNÊTETÉ (frontière §4 — ce que M10 V0 n'établit pas)

1. **U(1)_Y absent** : sans hypercharge, pas de distinction up/down (H vs
   H̃ = iσ₂H*), pas de règles complètes du MS ; tout énoncé de type
   « interdiction de masse » est au niveau SU(2) seul — l'énoncé physique
   complet exige les hypercharges (consigné).
2. **Générations absentes** : les angles de mélange (CKM/PMNS) exigent au
   moins trois copies des représentations ; rien ici ne les contraint.
3. **AUCUNE valeur** : v (échelle de Brout-Englert), y_i, masses — aucune
   dynamique déposée ; M10 ferme les RÈGLES DE SÉLECTION (quels couplages
   sont permis, combien d'invariants indépendants), pas leurs valeurs.
4. **Identification interprétative** : « le doublet scalaire H » — la
   machine construit des espaces d'invariants de doublets ; l'appellation
   Higgs/Brout-Englert est une interprétation, pas un dépôt.
5. **Spin-statistiques toujours consigné** : la marque symétrique/
   antisymétrique (M9 C7, M10 C3) est la matière première ; le théorème
   (localité relativiste) exige Lorentz (consigné).
6. **Normalisation** : ħ = 1, convention native J = 2×physique.

## 4. LA PORTÉE (frontière §5)

M10 ferme la dixième mort de la chaîne : **le squelette de sélection du
secteur type-Higgs/Yukawa est un objet machine** — pseudoréalité 2̄ ≅ 2,
unicité du couplage ε, comptage Catalan des invariants, règle de sélection
scalaire, structure double de l'opérateur de Weinberg, CG uniques ½⊗½.
La chaîne F12 tient : Pauli (M1, d0f714a), potentiel (M2, b249526),
remplissage (M3, a1048a1), nombres magiques (M4, a73c116), spin
demi-angle (M5, 963693c/f970108), SU(2) native (M6, 1dc6fcf/717edee),
SO(3) adjoint (M7, 0c6e762/ef67f8a), échelle angulaire (M8,
8c432c9/ff39bec), spin-orbite (M9, 18f76d3/b502e88), **singulets de
couplage (ce dépôt)**. Restent consignés hors portée : hypercharges,
générations et angles de mélange, valeurs des couplages et masses,
dynamique (potentiel scalaire, v), spin-statistiques, identification
physique du scalaire, g=2. Toute extension devra sortir du même protocole :
dépôt-d'abord, barres gelées, verdict sans sauvetage.

> **Le couplage n'est plus une règle lue : ε est l'objet natif, l'espace
> des invariants à n doublets est compté [0, 1, 0, 2, 0, 5, 0, 14, 0, 42],
> le doublet ne se couple au scalaire qu'avec un autre doublet, l'opérateur
> de Weinberg porte exactement deux invariants ε indépendants, et les CG
> ½⊗½ sont gelés bit-exact — le squelette de sélection du secteur des
> masses est un théorème de la machinerie, pas une importation.**
