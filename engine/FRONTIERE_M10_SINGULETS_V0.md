# FRONTIÈRE M10 — SINGULETS DE COUPLAGE : PSEUDORÉALITÉ 2̄ ≅ 2 ET RÈGLES DE SÉLECTION DES MASSES — V0

**Dépôt-d'abord (C0a)** : cette frontière est committée AVANT l'écriture de
tout script de vérification M10. Date : 2026-09-04. Filiation : M1 d0f714a →
M2 b249526 → M3 a1048a1 → M4 a73c116 → M5 963693c/f970108 → M6
1dc6fcf/717edee → M7 0c6e762/ef67f8a → M8 8c432c9/ff39bec → M9
18f76d3/b502e88 → **ce dépôt**.

## 0. TÉMOINS PRÉ-GEL (sonde_m10_singulets_v0, sortie témoin NON committée, règle maison)

Toutes les valeurs ci-dessous sont des sorties machine de la sonde exécutée
avant le présent dépôt — **première exécution propre : exit 0, tous
témoins OK, aucun défaut estimateur détecté à l'exécution**. Hygiène
consignée (leçon FORCE V1.2) : deux fonctions mortes de la première version
du fichier sonde (vestiges de conception, jamais exécutées) ont été
purgées AVANT la première exécution — aucun arbitrage machine n'a porté
sur du code défectueux. Machinerie verbatim des dépôts : triple natif M6
{σ_x, σ_y, σ_z} (1dc6fcf), ε = JM (l'antisymétrique natif), sommes de
Kronecker et Casimir complet M8 (ff39bec), gabarit M8 et produit M9
(b502e88), famille Bateman exp(iφH₂) et composés d'Euler aux angles M7
[0.3, 0.7, 1.1, 2.3]. Aucune bibliothèque de théorie des champs, aucune
table de Clebsch-Gordan importée : les espaces d'invariants sont COMPTÉS
par la machine.

- **S0** filiation ε : |ε−JM| = **0.0 bit-exact** ; ε² = −I, ε^T = −ε,
  ε réel — **0.0 bit-exact ×3**. ε EST l'objet natif M6 (JM), pas une
  importation.
- **S1** PSEUDORÉALITÉ : max |ε·Ū − U·ε| = **5.373833866861023e-17** sur
  exp(iθH_k), grille 96 θ × 3 générateurs ; **1.1102230246251565e-16** sur
  les composés d'Euler (angles M7) et Bateman(ALPHA) — **2̄ ≅ 2** : la
  conjugaison du doublet natif n'introduit aucune représentation nouvelle ;
  ε est l'intertwiner.
- **S2** Inv(2⊗2) re-witness (M9) : clusters {0: 1, 8: 3} (dév **0.0**) ;
  **dim Inv(2⊗2) = 1** ; tr(P_1·Sym²) = **0.0** — le singulet est
  ANTISYMÉTRIQUE ; tr(P_1·(I−Sym²)) = 0.9999999999999998 — le couplage de
  deux doublets EST la contraction ε ; conséquence structurelle : PAS de
  jauge invariante ψψ pour UN doublet seul (le couplage exige DEUX
  doublets distincts appariés par ε).
- **S3** comptage Catalan (machinerie M8 S4, n=1..10) : multiplicité du
  singulet (n'=0) dans 2^{⊗n} == **[0, 1, 0, 2, 0, 5, 0, 14, 0, 42]** —
  0 si n impair, C(n,n/2)−C(n,n/2−1) si pair (Catalan) — **écart entier
  0** sur toute la grille : l'espace des couplages invariants à n doublets
  est compté, pas postulé.
- **S4** sélection : 2⊗(2l+1) ne contient **AUCUN singulet** (l=0..6,
  clusters {3:2} → {143:12, 195:14}, zéro fois la valeur 0) — un doublet
  ne se couple jamais au scalaire avec une représentation entière ;
  3⊗3 = 1⊕3⊕5 : clusters **{0: 1, 8: 3, 24: 5}** (dév
  4.440892098500626e-15) — EXACTEMENT 1 singulet (structure scalaire type
  H†H / L·S).
- **S5** opérateur de Weinberg (2^{⊗4}) : les deux vecteurs ε-appariés
  v1 (appariement 12|34) et v2 (13|24) — **invariance |J_a·v| = 0.0
  bit-exact ×2 ×3 générateurs** ; Gram : ⟨v1,v1⟩ = **4.0**, ⟨v2,v2⟩ =
  **4.0**, ⟨v1,v2⟩ = **2.0**, det = **12.0** — rang 2 EXACT == comptage
  Catalan(2) == 2 : DEUX couplages invariants indépendants (Fierz non
  dégénéré).
- **S6** CG ½⊗½ gelés (multiplicité 1 ⟹ uniques) : les quatre vecteurs
  explicites |3,±1⟩ = |↑↑⟩, |↓↓⟩, |3,0⟩ = (|↑↓⟩+|↓↑⟩)/√2, |0,0⟩ =
  (|↑↓⟩−|↓↑⟩)/√2 sont eigen-vecteurs **exact 0.0 ×8** de J² (λ = 8, 8, 8,
  0) et J₃ (m = 2, 0, −2, 0) du produit natif ; orthonormalité max
  |⟨v_a,v_b⟩−δ| = **2.220446049250313e-16** ; tr(P_triplet·Sym²) =
  **3.0** — le triplet EST Sym² (liant M7/M8/M9).

## 1. THÈSES

- **T1 (pseudoréalité)** : 2̄ ≅ 2 par ε natif (5.4e-17 / 1.1e-16) — la
  représentation conjuguée du doublet est le doublet lui-même ;
  l'intertwiner est l'objet M6, pas une structure importée.
- **T2 (unicité du couplage doublet-doublet)** : dim Inv(2⊗2) = 1 et le
  singulet est antisymétrique (tr(P_1·Sym²) = 0.0) — la contraction
  ε^{ij} du couplage de Yukaua EST le singulet M9 ; un doublet seul n'a
  pas de couplage scalaire ψψ.
- **T3 (comptage Catalan)** : l'espace des invariants de 2^{⊗n} vaut 0
  (impair) ou C(n,n/2)−C(n,n/2−1) (pair) — [1, 2, 5, 14, 42] — compté
  machine (écart entier 0) ; à quatre doublets, DEUX couplages
  indépendants (les deux appariements ε, Gram rang 2, det 12.0) : la
  structure de l'opérateur de Weinberg est native.
- **T4 (sélection scalaire)** : 2⊗(2l+1) ne contient aucun singulet
  (l=0..6) — un doublet ne se couple au scalaire qu'avec un AUTRE
  doublet ; 3⊗3 ⊇ exactement 1 singulet — la paire d'adjoints porte une
  et une seule jauge invariante (structure type H†H / L·S, déjà aperçue
  en M9 D3).
- **T5 (CG uniques à ½⊗½)** : multiplicité 1 ⟹ les coefficients de
  mélange ½⊗½ sont UNIQUEMENT déterminés — gelés bit-exact — le seul
  « mélange » que la machinerie puisse verrouiller sans générations.

## 2. CONTRÔLES GELÉS

- **C0a** antériorité : mtime(FRONTIERE_M10_SINGULETS_V0.md) < début
  d'exécution du verif (exigé bit : strictement avant).
- **C1** filiation ε : |ε−JM| = **0.0 bit-exact exigé** ; ε² = −I,
  ε^T = −ε, |Im ε| = **0.0 bit-exact exigés**.
- **C2** pseudoréalité : max |ε·Ū − U·ε| ≤ **1e-15** sur exp(iθH_k)
  (grille 96 × 3) ET sur les composés d'Euler/Bateman (mesuré 5.37e-17 /
  1.11e-16).
- **C3** Inv(2⊗2) : clusters {8: 3, 0: 1} **exigés**, dév ≤ 1e-9 (mesuré
  0.0) ; dim Inv == 1 **exigé** ; tr(P_1·Sym²) ≤ **1e-12** (mesuré 0.0) ;
  tr(P_1·(I−Sym²)) ≤ **1e-12** (mesuré 0.9999999999999998).
- **C4** Catalan (n=1..10) : suite == **[0, 1, 0, 2, 0, 5, 0, 14, 0, 42]**
  (écart entier **0 exigé**).
- **C5** sélection : singulets 2⊗(2l+1) == 0 pour l=0..6 **exigé** ;
  3⊗3 clusters == {0: 1, 8: 3, 24: 5} **exigés**, dév ≤ 1e-9 (mesuré
  4.440892098500626e-15).
- **C6** Weinberg 2^{⊗4} : |J_a·v1|, |J_a·v2| ≤ **1e-13** (mesuré 0.0) ;
  Gram == (4.0, 4.0, 2.0), det == 12.0 **exigés** (rang 2) ; singulets
  comptés == 2 **exigé**.
- **C7** CG ½⊗½ : |J²v−λv|, |J₃v−mv| ≤ **1e-13** (mesuré 0.0 ×8) ;
  orthonormalité ≤ **1e-15** (mesuré 2.220446049250313e-16) ;
  tr(P_triplet·Sym²) == 3.0 (M9 C7 re-witness).

**Échelle des verdicts** : V+ M10_SINGULETS_FERME (tous C0a–C7 OK et
D1–D3 OK) / V2 (C0a–C7 OK, une conséquence en échec) / V3 (un contrôle en
échec non critique) / **V4_REFUTE exit 1** (un seul contrôle critique en
échec — AUCUN sauvetage, I1).

## 3. CONSÉQUENCES GELÉES

- **D1** table Catalan des espaces d'invariants (n=1..10) :
  [0, 1, 0, 2, 0, 5, 0, 14, 0, 42] — le nombre de couplages invariants
  indépendants à n doublets est un théorème machine — gelée.
- **D2** table de sélection : dim Inv == 0 pour 2⊗(2l+1) (l=0..6), == 1
  pour 2⊗2 (via ε) et pour 3⊗3 — le squelette de sélection des couplages
  scalaires du secteur type-Higgs est fermé — gelée.
- **D3** Weinberg : Gram (4.0, 4.0, 2.0), det 12.0, invariance 0.0 — les
  DEUX appariements ε indépendants ; CG ½⊗½ gelés exacts — gelés.

## 4. CONSIGNATION AVANT GEL (honnêteté)

- **U(1)_Y absent** : sans hypercharge, pas de distinction up/down (H vs
  H̃ = iσ₂H*) ni de règles complètes du MS ; ce que M10 compte est le
  contenu SU(2) SEUL. Toute énoncé de type « interdiction de masse » est
  au niveau SU(2) — l'énoncé physique complet exige les hypercharges
  (consigné).
- **Générations absentes** : les angles de mélange (CKM/PMNS) exigent au
  moins trois copies des représentations ; rien ici ne les contraint.
  Consigné.
- **AUCUNE valeur** : v (échelle de Brout-Englert), y_i, masses — aucune
  dynamique déposée ; M10 ferme les RÈGLES DE SÉLECTION (quels couplages
  sont permis, combien d'invariants indépendants), pas leurs valeurs.
  Consigné.
- **Identification interprétative** : « le doublet scalaire H » — la
  machine construit des espaces d'invariants de doublets ; l'identification
  au champ de Brout-Englert-Higgs est une interprétation, pas un dépôt.
- **Spin-statistiques toujours consigné** : la marque symétrique/
  antisymétrique (M9, M10 C3) est la matière première ; le théorème
  (localité relativiste) exige Lorentz (consigné).
- **Normalisation** : ħ = 1, convention native J = 2×physique.
- **Hygiène sonde** : deux fonctions mortes purgées AVANT première
  exécution (leçon FORCE V1.2 — jamais exécutées, consigné par
  transparence).

## 5. PORTÉE

Ce qui est dérivé : la pseudoréalité du doublet natif (2̄ ≅ 2, ε
intertwiner) ; l'unicité du couplage doublet-doublet (ε, antisymétrique) ;
le comptage Catalan des invariants de 2^{⊗n} ; la règle de sélection
scalaire (2⊗entier : jamais de singulet ; 3⊗3 : un seul) ; la structure
double de l'opérateur de Weinberg ; les CG uniques ½⊗½.

Ce qui reste ouvert (consigné) : hypercharges, générations et angles de
mélange, valeurs des couplages et masses, dynamique (potentiel scalaire,
v), spin-statistiques, identification physique du scalaire.
