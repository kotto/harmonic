# FRONTIÈRE M9 — SPIN-ORBITE : j = l ± ½ SORT DE LA LADDER M8 ET DU DOUBLET NATIF — V0

**Dépôt-d'abord (C0a)** : cette frontière est committée AVANT l'écriture de
tout script de vérification M9. Date : 2026-09-04. Filiation : M1 d0f714a →
M2 b249526 → M3 a1048a1 → M4 a73c116 → M5 963693c/f970108 → M6
1dc6fcf/717edee → M7 0c6e762/ef67f8a → M8 8c432c9/ff39bec → **ce dépôt**.

## 0. TÉMOINS PRÉ-GEL (sonde_m9_spin_orbite_v0, sortie témoin NON committée, règle maison)

Toutes les valeurs ci-dessous sont des sorties machine de la sonde exécutée
avant le présent dépôt (deux exécutions : la première a révélé des défauts
estimateur, corrigés et re-exécutés proprement **exit 0, tous témoins OK**
AVANT le gel — leçon FORCE V1.2). Déterministe, aucune graine, machinerie
verbatim des dépôts : gabarit M8 (convention native tranchée, ff39bec) pour
la part l, triple natif M6 {σ_x, σ_y, σ_z} (1dc6fcf) pour la part ½ —
le spin ½ est l'objet natif, pas une importation. Construction : sur
l'espace produit dim 2(2l+1) (l entier 0..6, n = 2l),

  J_k^{prod} = J_k^{(l)} ⊗ I₂ + I_{2l+1} ⊗ H_k.

Aucune bibliothèque de moment angulaire, aucun package Clebsch-Gordan : la
décomposition l ⊗ ½ est COMPTÉE par la machine et comparée aux formules
fermées dérivées à la main AVANT exécution (comparaison, pas construction).

**Défauts estimateur corrigés AVANT gel (leçon FORCE V1.2)** : (i) la
première exécution testait l'histogramme m avec |2m| ≤ n−1 sur des valeurs
propres qui SONT déjà 2m en normalisation native (double doublement ⟹ 6
ÉCHEC alors que les données elles-mêmes étaient exactes : |diag J₃ −
attendu| = 0.0 partout) — corrigé : le test porte sur la valeur propre v,
mult 2 si |v| ≤ n−1, mult 1 si |v| = n+1 ; (ii) une erreur de format
d'affichage en S8 (ValueError, cosmétique, sonde uniquement) ; (iii) à la
conception, le maximum du spectre de bloc avait été dérivé 4p — ERREUR : le
minimum de q²+2q sur q = −p..p pas 2 est en q = −1 (sommet de la parabole),
le max vaut (p+1)² — corrigé avant exécution, la forme close triée
{p²+2p−q²−2q} est l'objet de comparaison ; (iv) défaut M8 re-consigné : la
base eigenvectors de `eigh` est arbitraire — seuls des INVARIANTS de base
sont utilisés (dimensions de clusters entières, spectres de restrictions
V†BV, traces de produits de projecteurs).

- **S0** filiation : |J_gabarit(1) − triple natif M6| = **0.0 bit-exact**
  (re-témoin M8) ; **l=0 : |J_prod − triple natif| = 0.0 BIT-EXACT ×3** —
  à l=0 le produit EST le doublet natif (kron avec 1×1 exact).
- **S1** algèbre produit (l=0..6) : hermiticité |J−J†| = **0.0** partout ;
  max |[J_i,J_j] − 2iε_ijk J_k| = **1.5987211554602254e-14** ; max
  |[J²,J_k]| = **2.2737367544323206e-13** (J² commute avec les trois
  générateurs produits).
- **S2** clusters J² (valeurs propres arrondies à l'entier, dév max
  **2.842170943040401e-14**) : l=0 : {3: 2} ; l=1 : {3: 2, 15: 4} ; l=2 :
  {15: 4, 35: 6} ; l=3 : {35: 6, 63: 8} ; l=4 : {63: 8, 99: 10} ; l=5 :
  {99: 10, 143: 12} ; l=6 : {143: 12, 195: 14} — multiplicités [2l+2, 2l]
  EXACTES ; écarts entre clusters 12/20/28/36/44/52 = 4(n+1) ; ENLACEMENT :
  λ₊(l−1) == λ₋(l) pour tout l≥1 (chaque j ∈ {½, 3/2, 5/2, …} apparaît
  exactement deux fois : j₊ de l et j₋ de l+1).
- **S3** J₃ diagonal explicite : J₃^{prod} = diag(n−2k±1, k=0..n) —
  |diag − attendu| = **0.0** pour tout l ; histogramme m compté :
  multiplicité 2 si |2m| ≤ n−1, multiplicité 1 si |2m| = n+1, valeurs
  distinctes n+2, total 4l+2 — **OK pour tout l** ; |diag − union des
  spectres gabarit (n+1) ⊕ (n−1)| = **0.0** pour tout l.
- **S4** blocs : |J_−J_+ − h.c.| = **0.0** partout (J_−J_+ = J₁²+J₂²−2J₃
  hermitien) ; dim P_j == 2j+1 ∈ {n+2, n} EXACT pour tout cluster ; spectre
  de bloc de J_−J_+ restreint (V†BV, invariant de base) == forme close
  {p²+2p−q²−2q : q = −p..p pas 2} (p = 2j, q = 2m — entiers exacts) :
  **max |spectre − forme close| = 5.684341886080802e-14** (l=5, λ=143).
- **S5** bornage : p = √(1+λ) − 1 = [1], [3,1], [5,3], [7,5], [9,7],
  [11,9], [13,11] pour l=0..6 — **entiers IMPAIRS ∈ {n−1, n+1}, dév √ =
  0.0** → 2j impair → j = l±½ ; discriminant : distance des clusters à
  4l(l+1) (hypothèse non couplée j=l, un seul bloc) = 3/5/9/13/17/21/25
  (impairs) — rejetée par gaps entiers.
- **S6** croisement M8 : λ₊ == (n+1)(n+1+2) et λ₋ == (n−1)(n−1+2)
  (identités arithmétiques entières, l≥1) — **les deux blocs j SONT les
  barreaux M8 n±1** ; capacité : (2j₊+1)+(2j₋+1) == 2(2l+1) == (2l+1)·2
  pour tout l.
- **S7** témoin doublet⊗doublet (l=½ : produit de DEUX objets natifs,
  hors boucle l entier) : clusters J² = {8: 3, 0: 1} (dév round **0.0**)
  == formule dégénérescence M8 n=2 (mult(2)=3, mult(0)=1) → **j=1 (mult 3)
  ⊕ j=0 (mult 1)** ; bloc j=1 : dim 3, spectre [0.0, 7.999999999999998,
  8.0] vs forme close p=2 [0, 8, 8] (écart **1.7763568394002505e-15**) ;
  bloc j=0 : dim 1, spectre [0.0] (écart **0.0**) ; **tr(P_top·P_sym) =
  3.0** (P_sym = symétriseur exact M8, tr = 3.0) — le bloc j=1 EST le
  sous-espace Sym² ; tr(P_bot·(I−P_sym)) = 0.9999999999999998 — le
  singulet j=0 EST antisymétrique ; traces croisées = **0.0**.
- **S8** table de capacité (découpe spin-orbite des couches, matière M3/M4)
  : 2(2l+1) = (2j₊+1) + (2j₋+1) : l=0 : 2 = 2 ; l=1 : 6 = 4+2 ; l=2 : 10 =
  6+4 ; l=3 : 14 = 8+6 ; l=4 : 18 = 10+8 ; l=5 : 22 = 12+10 ; l=6 : 26 =
  14+12.

## 1. THÈSES

- **T1 (construction spin-orbite)** : la décomposition l ⊗ ½ sort par PURE
  addition de Kronecker des générateurs natifs J_k^{prod} = J_k^{(l)}⊗I₂ +
  I_{2l+1}⊗H_k sur l'espace dim 2(2l+1) — la part l est le gabarit M8
  (barreaux n = 2l), la part ½ est le doublet natif M6 ; aucune
  bibliothèque de représentations, aucune formule de Clebsch-Gordan
  importée comme construction.
- **T2 (décomposition comptée)** : l ⊗ ½ = (l+½) ⊕ (l−½) est comptée par
  la machine : J² a exactement deux clusters aux entiers λ₊ = (n+1)(n+3)
  (mult n+2 = 2l+2) et λ₋ = (n−1)(n+1) (mult n = 2l, absent à l=0) ;
  J₃^{prod} est diagonal explicite n−2k±1 ; l'enlacement λ₊(l) == λ₋(l+1)
  tisse chaque j ∈ {½, 3/2, 5/2, …} exactement deux fois à travers l.
- **T3 (blocs = barreaux M8)** : les deux blocs j de chaque produit SONT
  les barreaux de la ladder M8 : λ == n'(n'+2) à n' = n±1 ; l'identité de
  capacité (2j₊+1)+(2j₋+1) == 2(2l+1) découpe chaque couche M8 en deux
  sous-couches spin-orbite — matière première directe de l'ouverture M4
  rang 4 nucléaire (consignée).
- **T4 (structure de bloc et bornage)** : [J²,J_±] = 0 (≤ 2.28e-13) ; dans
  chaque bloc, le spectre de J_−J_+ == {p²+2p−q²−2q : q = −p..p pas 2} —
  entiers exacts (max 5.68e-14), p = 2j IMPAIR ; le bornage 2j impair
  exclude j = l (distances entières impaires 3..25 à 4l(l+1)) — la machine
  tranche contre l'hypothèse non couplée.
- **T5 (doublet⊗doublet = 1⊕0, liant M7/M8)** : le produit de DEUX objets
  natifs donne j=1 (mult 3) ⊕ j=0 (mult 1) ; le bloc j=1 EST le
  sous-espace symétrique Sym² (tr(P_top·P_sym) = 3.0, traces croisées 0.0)
  — l'adjointe M7/Sym² M8 réapparaît comme bloc de couplage ; le singulet
  j=0 EST antisymétrique (tr(P_bot·(I−P_sym)) ≈ 1) — matière première de
  l'ouverture statistique d'échange (consignée).

## 2. CONTRÔLES GELÉS

- **C0a** antériorité : mtime(FRONTIERE_M9_SPIN_ORBITE_V0.md) < début
  d'exécution du verif (exigé bit : strictement avant).
- **C1** filiation : |J_gabarit(1) − triple natif| = **0.0 bit-exact
  exigé** ; **l=0 : |J_prod − triple natif| = 0.0 bit-exact exigé** (×3).
- **C2** algèbre produit (l=0..6) : |J−J†| ≤ **1e-15** (mesuré 0.0) ;
  |[J_i,J_j]−2iεJ_k| ≤ **1e-13** (mesuré 1.60e-14) ; |[J²,J_k]| ≤ **1e-12**
  (mesuré 2.27e-13).
- **C3** clusters J² (l=0..6) : dév au round ≤ **1e-9** (mesuré 2.84e-14)
  ; multiplicités == [2l+2, 2l] entières **exigées** ({3: 2} à l=0) ;
  enlacement λ₊(l−1) == λ₋(l) **exigée** (entiers, l≥1).
- **C4** J₃ (l=0..6) : |diag − attendu n−2k±1| ≤ **1e-13** (mesuré 0.0) ;
  histogramme (mult 2 si |2m| ≤ n−1, 1 si |2m| = n+1 ; distinct n+2 ; total
  4l+2) **exigé entier** ; |diag − union gabarits n±1| ≤ **1e-13**
  (mesuré 0.0).
- **C5** blocs (l=0..6) : |J_−J_+ − h.c.| ≤ **1e-15** (mesuré 0.0) ; dim
  P_j == 2j+1 **exigé entier** ; |spectre de bloc − {p²+2p−q²−2q}| ≤
  **1e-12** (mesuré 5.68e-14).
- **C6** bornage (l=0..6) : p = √(1+λ)−1 entier impair ∈ {n−1, n+1}
  **exigé** ; dév √ ≤ **1e-12** (mesuré 0.0) ; distance à 4l(l+1) ≥ 3
  **exigée** (discriminant j=l rejeté).
- **C7** doublet⊗doublet : clusters {8: 3, 0: 1} **exigés entiers** ;
  |spectre bloc j=1 − [0,8,8]| ≤ 1e-12 ; |spectre bloc j=0 − [0]| ≤ 1e-12
  ; |tr(P_top·P_sym) − 3| ≤ **1e-12** (mesuré 0.0) ; |tr(P_bot·(I−P_sym))
  − 1| ≤ **1e-12** (mesuré 2.22e-16) ; |tr(P_bot·P_sym)|, |tr(P_top·
  (I−P_sym))| ≤ **1e-12** (mesuré 0.0) ; tr(P_sym) == 3.0 (M8).
- **C8** capacité (l=0..6) : (2j₊+1)+(2j₋+1) == 2(2l+1) **exigé entier** ;
  table == [2, 6, 10, 14, 18, 22, 26] **exigée**.

**Échelle des verdicts** : V+ M9_SPIN_ORBITE_FERME (tous C0a–C8 OK et
D1–D3 OK) / V2 (C0a–C8 OK, une conséquence en échec) / V3 (un contrôle en
échec non critique) / **V4_REFUTE exit 1** (un seul contrôle critique en
échec — AUCUN sauvetage, I1).

## 3. CONSÉQUENCES GELÉES

- **D1** table des clusters par l (l=0..6) : λ₊/mult et λ₋/mult mesurés ==
  [(3,2)] ; [(15,4),(3,2)] ; [(35,6),(15,4)] ; [(63,8),(35,6)] ;
  [(99,10),(63,8)] ; [(143,12),(99,10)] ; [(195,14),(143,12)] — gelés.
- **D2** table de capacité par l : (2j₊+1, 2j₋+1) == (2,0), (4,2), (6,4),
  (8,6), (10,8), (12,10), (14,12) — somme == [2, 6, 10, 14, 18, 22, 26]
  (la table M8 S8 découpée) — gelée.
- **D3** déviations de bloc max par l (spectre vs forme close, et J² au
  round) : gelées aux valeurs S4/S2 (max 5.68e-14 / 2.84e-14).

## 4. CONSIGNATION AVANT GEL (honnêteté)

- **Identification orbitale consignée** : la machine construit l ⊗ ½
  algébriquement ; l'identification de la part l à un degré de liberté
  ORBITAL spatial (et de la part ½ au spin) est une interprétation, pas un
  dépôt. Ce qui est dérivé : la structure de couplage d'une ladder M8 avec
  un doublet natif.
- **AUCUN ordre de niveaux** : l'effet spin-orbite physique exige un
  Hamiltonien (H ∝ L·S) qui n'est pas déposé — la machine donne la
  DÉCOMPOSITION (quels j, quelles multiplicités, quelles capacités), pas
  l'ÉNERGIE ni le signe du fractionnement. L'ordre j₊/j₋ reste consigné.
- **Coefficients de Clebsch-Gordan complets non construits** : seuls les
  projecteurs spectraux et leurs invariants (dims, spectres de
  restrictions, traces de produits) sont utilisés ; l'unitaire
  d'intertwining base-produit → base-j (les coefficients CG explicites) ne
  sort pas de ce dépôt. Consigné.
- **g = 2 reste hors portée** : aucun couplage électromagnétique dans les
  dépôts M1–M8 ; son importation serait un axiome nouveau. Consigné.
- **Normalisation** : ħ = 1, convention native J^nat = 2×physique (le /4
  de M6 C6, généralisé en M8) — 4j(j+1) natif == j(j+1) physique.
- **l=0** : la multiplicité j₋ (2l = 0) est absente — « deux blocs »
  dégénère en un bloc unique j = ½ (le doublet natif, C1 bit-exact).
- **Défauts estimateur** : consignés en §0 (leçon FORCE V1.2) — corrigés
  et re-exécutés AVANT le présent gel.

## 5. PORTÉE

Ce qui est dérivé : la décomposition spin-orbite complète pour l=0..6
(dims produit 2..26), comptée par la machine depuis la ladder M8 et le
doublet natif seuls ; l'identité de capacité additive des couches ; la
structure de bloc (projecteurs, spectres de ladder entiers par bloc) ; le
témoin ½⊗½ = 1⊕0 avec son liant Sym²/antisymétrique.

Ce qui reste ouvert (consigné) : ordre énergétique des niveaux
(Hamiltonien absent), coefficients CG complets, statistique d'échange,
rang 4 nucléaire de M4, g=2, identification orbitale physique.
