# RÉSULTAT F12 — MORT 9 / SPIN-ORBITE : j = l ± ½ SORT DE LA LADDER M8 ET DU DOUBLET NATIF — V0

**Date : 2026-09-04. Verdict machine : `V+ M9_SPIN_ORBITE_FERME` — exit 0.**

Exécution de `verif_m9_spin_orbite_v0.py` sur la frontière gelée
`FRONTIERE_M9_SPIN_ORBITE_V0.md` (commit **18f76d3**, dépôt-d'abord — C0a
OK : frontière 18:10:56 < exécution 18:15:59). Sortie :
`resultat_m9_spin_orbite_v0.json` (déterministe, aucune graine, machinerie
verbatim des dépôts : gabarit M8 convention native pour la part l (barreaux
n = 2l, ff39bec), triple natif M6 {σ_x, σ_y, σ_z} pour la part ½
(1dc6fcf/717edee), construction J_k^{prod} = J_k^{(l)}⊗I₂ + I_{2l+1}⊗H_k
sur dim 2(2l+1), l = 0..6).

**Objet M9 : la décomposition spin-orbite l ⊗ ½ = (l+½) ⊕ (l−½) n'est plus
une formule de Clebsch-Gordan lue — elle est comptée par la machine depuis
la ladder M8 et le doublet natif seuls.** Aucune bibliothèque de moment
angulaire, aucun package CG importé comme construction.

---

## 1. LE VERDICT — V+ M9_SPIN_ORBITE_FERME, exit 0

**C0a–C8 tous passés ET D1 ET D2 ET D3 passées** :

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 18:10:56 < 18:15:59 |
| C1 filiation | **OK** | gabarit n=1 == triple natif **0.0 bit-exact** ; **l=0 : J_prod == triple natif 0.0 BIT-EXACT ×3** — à l=0 le produit EST le doublet |
| C2 algèbre produit | **OK** | \|J−J†\| = 0.0 ; \|[J,J]−2iεJ\| = 1.5987211554602254e-14 ; \|[J²,J_k]\| = 2.2737367544323206e-13 |
| C3 clusters J² | **OK** | multiplicités == [2l+2, 2l] exactes tout l ({3:2} → {195:14, 143:12}) ; dév au round = 2.842170943040401e-14 ; **enlacement λ₊(l−1)==λ₋(l) OK** |
| C4 J₃ | **OK** | \|diag − (n−2k±1)\| = **0.0** ; histogramme m (mult 2 si \|2m\|≤n−1, 1 si \|2m\|=n+1 ; distinct n+2 ; total 4l+2) OK tout l ; \|diag − union gabarits n±1\| = **0.0** |
| C5 blocs | **OK** | \|J_−J_+ − h.c.\| = **0.0** ; dim P_j == 2j+1 entières ; \|spectre de bloc − {p²+2p−q²−2q}\| = **5.684341886080802e-14** |
| C6 bornage | **OK** | p = √(1+λ)−1 = [1],[3,1],[5,3],[7,5],[9,7],[11,9],[13,11] — **impairs ∈ {n−1, n+1}**, dév √ = 0.0 ; distance à 4l(l+1) = 3..25 (hypothèse j=l rejetée par gaps entiers) |
| C7 doublet⊗doublet | **OK** | clusters {8: 3, 0: 1} (dév 0.0) ; bloc j=1 [0, 8, 8] (1.7763568394002505e-15) ; bloc j=0 [0.0] ; **tr(P_top·P_sym) = 3.0** ; tr(P_bot·(I−P_sym)) = 0.9999999999999998 ; traces croisées 0.0 |
| C8 capacité | **OK** | (2j₊+1)+(2j₋+1) == 2(2l+1) == **[2, 6, 10, 14, 18, 22, 26]** |

| Conséquence | Résultat | Valeur machine |
|---|---|---|
| **D1** décomposition COMP TÉE pas lue | **OK** | clusters 4j(j+1) = (n±1)(n∓1) entiers, multiplicités [2l+2, 2l], J₃ diagonal n−2k±1, enlacement λ₊(l−1)==λ₋(l) — chaque j ∈ {½, 3/2, …} apparaît exactement deux fois à travers l |
| **D2** identité de capacité | **OK** | (2j₊+1)+(2j₋+1) == 2(2l+1) : découpe (2,0),(4,2),(6,4),(8,6),(10,8),(12,10),(14,12) de la table M8 — matière M3/M4, rang 4 nucléaire reste consigné |
| **D3** structure de bloc + témoin ½⊗½ | **OK** | [J²,J_±] = 0 (2.27e-13) ; spectres de ladder entiers par bloc (5.68e-14) ; **½⊗½ = 1⊕0 avec le bloc j=1 EST Sym²** (tr = 3.0) — l'adjointe M7/Sym² M8 réapparaît comme bloc de couplage |

Un seul contrôle en échec aurait déclenché `V4_REFUTE` exit 1 sans
sauvetage — précédents M6 (717edee), M7 (ef67f8a), M8 (ff39bec). Un défaut
d'implémentation du VERIF (initialisation de l'enlacement C3 à l=0) a été
détecté à la première exécution post-gel : le témoin pré-gel de la sonde
était correct, le verif a été corrigé pour fidélité au témoin gelé
(aucune barre ni frontière modifiée), re-exécution propre — consigné ici et
dans le JSON (leçon FORCE V1.2, aucun silencieux).

## 2. CE QUE M9 ÉTABLIT MAINTENANT

1. **La décomposition spin-orbite est un objet machine (T1/D1).** Elle
   sort par PURE addition de Kronecker J_k^{prod} = J_k^{(l)}⊗I₂ +
   I_{2l+1}⊗H_k : la part l est le gabarit M8 (barreaux n = 2l), la part ½
   est le doublet natif M6. Aucune formule de Clebsch-Gordan importée —
   la décomposition l⊗½ = (l+½)⊕(l−½) est comptée.

2. **Le comptage est exact (T2/C3/C4).** J² a exactement deux clusters aux
   entiers λ₊ = (n+1)(n+3) (mult n+2) et λ₋ = (n−1)(n+1) (mult n) —
   dev au round 2.84e-14, multiplicités [2l+2, 2l] exactes. J₃ est
   diagonal explicite n−2k±1 (0.0) et son spectre == union des gabarits
   M8 n±1 (0.0). L'enlacement λ₊(l−1) == λ₋(l) tisse chaque
   j ∈ {½, 3/2, 5/2, …} exactement deux fois à travers l.

3. **Les blocs j SONT les barreaux M8 (T3/S6).** λ == n'(n'+2) à n' = n±1
   — la décomposition spin-orbite est la ladder M8 vue en couplé. L'identité
   de capacité (2j₊+1)+(2j₋+1) == 2(2l+1) découpe chaque couche de la table
   M8 en deux sous-couches — matière première directe du rang 4 nucléaire
   de M4 (consigné).

4. **La structure de bloc est entière et le bornage tranche (T4/C5/C6).**
   [J²,J_±] = 0 (2.28e-13) ; le spectre de J_−J_+ dans chaque bloc vaut
   {p²+2p−q²−2q} — entiers exacts (5.68e-14), p = 2j impair ; le maximum
   est (p+1)² (sommet en q = −1), pas 4p. Le discriminant rejette
   l'hypothèse non couplée j=l par gaps entiers 3..25 — la machine tranche
   le couplage, pas une convention.

5. **½⊗½ = 1⊕0 et le liant M7/M8 (T5/C7/D3).** Le produit de DEUX objets
   natifs donne j=1 (mult 3) ⊕ j=0 (mult 1) — le comptage M8 n=2
   réapparaît ; le bloc j=1 EST le sous-espace symétrique Sym²
   (tr(P_top·P_sym) = 3.0, traces croisées 0.0), le singulet j=0 EST
   antisymétrique (0.9999999999999998) — l'adjointe M7/Sym² M8 est un bloc
   de couplage, et la marque antisymétrique/symétrique du couple 0/1 livre
   la matière première de l'ouverture statistique d'échange (consignée).

6. **Les défauts estimateur ont été corrigés et consignés (leçon FORCE
   V1.2).** Sonde, AVANT gel (frontière §0, 18f76d3) : double doublement
   2m dans le test histogramme ; max de spectre de bloc dérivé 4p (le max
   est (p+1)²) ; base eigh arbitraire (seuls invariants de base utilisés).
   Verif, APRÈS gel : initialisation de l'enlacement C3 à l=0 — témoin
   pré-gel correct, verif corrigé pour fidélité, re-exécution propre,
   consigné sans modification des barres.

## 3. HONNÊTETÉ (frontière §4 — ce que M9 V0 n'établit pas)

1. **L'identification orbitale est consignée** : la machine construit l⊗½
   algébriquement ; l'identification de la part l à un degré de liberté
   ORBITAL spatial (et de la part ½ au spin) est une interprétation, pas
   un dépôt.
2. **AUCUN ordre de niveaux** : l'effet spin-orbite physique exige un
   Hamiltonien (H ∝ L·S) qui n'est pas déposé — la machine donne la
   DÉCOMPOSITION (quels j, quelles multiplicités, quelles capacités), pas
   l'ÉNERGIE ni le signe du fractionnement.
3. **Les coefficients de Clebsch-Gordan complets ne sont pas construits** :
   seuls les projecteurs spectraux et leurs invariants (dims, spectres de
   restrictions, traces de produits) sont utilisés ; l'unitaire
   d'intertwining base-produit → base-j reste consigné.
4. **g = 2 reste hors portée** : aucun couplage électromagnétique dans les
   dépôts M1–M8 ; son importation serait un axiome nouveau.
5. **l=0** : la multiplicité j₋ (2l = 0) est absente — « deux blocs »
   dégénère en un bloc unique j = ½ (le doublet natif, C1 bit-exact).
6. **Normalisation** : ħ = 1, convention native J^nat = 2×physique —
   4j(j+1) natif == j(j+1) physique.

## 4. LA PORTÉE (frontière §5)

M9 ferme la neuvième mort de la chaîne : **le couplage spin-orbite est un
objet machine** — j = l±½ construit depuis la ladder M8 et le doublet
natif, la décomposition comptée à multiplicités exactes, les blocs
identifiés aux barreaux M8 n±1, l'identité de capacité additives des
couches, et le témoin ½⊗½ = 1⊕0 rattaché à M7/M8. La chaîne F12 tient :
Pauli (M1, d0f714a), potentiel (M2, b249526), remplissage (M3, a1048a1),
nombres magiques (M4, a73c116), spin demi-angle (M5, 963693c/f970108),
SU(2) native (M6, 1dc6fcf/717edee), SO(3) adjoint (M7, 0c6e762/ef67f8a),
échelle angulaire (M8, 8c432c9/ff39bec), **spin-orbite (ce dépôt)**.
Restent consignés hors portée : ordre énergétique des niveaux (aucun
Hamiltonien), coefficients CG complets, statistique d'échange, rang 4
nucléaire de M4, g=2, identification orbitale physique. Toute extension
devra sortir du même protocole : dépôt-d'abord, barres gelées, verdict
sans sauvetage.

> **Le couplage n'est plus une formule : l'addition de Kronecker du gabarit
> M8 et du doublet natif découpe chaque couche 2(2l+1) en j = l+½ (mult
> 2l+2) et j = l−½ (mult 2l), les blocs sont les barreaux M8 n±1, les
> spectres de ladder par bloc sont des entiers exacts, et le produit de
> deux doublets natifs donne 1⊕0 avec le triplet DANS Sym² — la décomposition
> spin-orbite est un théorème de la machinerie, pas une importation.**
