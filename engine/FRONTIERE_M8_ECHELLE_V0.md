# FRONTIÈRE M8 — ÉCHELLE ANGULAIRE : (2l+1) SORT DU DOUBLET NATIF — V0

**Dépôt-d'abord (C0a)** : cette frontière est committée AVANT l'écriture de
tout script de vérification M8. Date : 2026-09-04. Filiation : M1 d0f714a →
M2 b249526 → M3 a1048a1 → M4 a73c116 → M5 963693c/f970108 → M6
1dc6fcf/717edee → M7 0c6e762/ef67f8a → **ce dépôt**.

## 0. TÉMOINS PRÉ-GEL (sonde_m8_echelle_v0, sortie témoin NON committée, règle maison)

Toutes les valeurs ci-dessous sont des sorties machine de la sonde exécutée
avant le présent dépôt. Déterministe, aucune graine, machinerie verbatim des
dépôts : triple natif M6 {S, −iJ, J·S}={σ_x, σ_y, σ_z} (1dc6fcf), sommes de
Kronecker J_k^{full} = Σ_a I⊗..⊗H_k⊗..⊗I, grille n=1..10 (route A) et
n=0..12 (route B), mp non requis (tous les témoins sont des invariants
réels/entiers).

**Défauts estimateur corrigés AVANT gel (leçon FORCE V1.2)** : la première
exécution de la sonde avait DEUX défauts — (i) le signe de J_2 du gabarit
inversé (convention importée), (ii) la base du sous-espace symétrique prise
dans `eigh` (base LAPACK arbitraire, comparaison élément-à-élément invalide
⟹ échecs 8.0/14.0/48.0). Corrections : base de Poids explicite (colonne k =
somme normalisée des bit-strings à k uns, orthonormée par construction,
déterministe, SANS eigh) et signe arbitré par la machine : |J_2^(A)(n=1) −
(−iJ)| = **0.0** (convention native), |J_2^(A)(n=1) − (+iJ)| = 2.0 (rejeté).
Après correction, re-exécution propre : **exit 0, tous témoins OK**.

- **S0** filiation : à n=1, |J_A − triple natif M6| = **0.0 bit-exact ×3** ;
  témoin symétriseur S_n = (1/n!)Σ_π P_π (construit exactement, sans boucle
  sur n!) : max |S_n·W − W| = 1.1102230246251565e-16, max |tr(S_n)−(n+1)| =
  0.0 (n=1..10) — W est bien la base du sous-espace symétrique.
- **S1** convention du gabarit : la machine tranche J_2_{k+1,k} = +i√((k+1)
  (n−k)), J_2_{k,k+1} = −i√((k+1)(n−k)) — à n=1 le gabarit == triple M6
  **0.0 BIT-EXACT** ; l'autre signe donne 2.0.
- **S2** dimensions route A (n=1..10) : dim W = n+1 pour les dix valeurs
  (2,3,4,5,6,7,8,9,10,11) — witness trace : |tr J3 − Σ(n−2k)| = 0.0 (max
  8.88e-16 à n=6).
- **S3** route A, algèbre et Casimir projetés (n=1..10) : max
  |[J_i,J_j] − 2iε_ijk J_k| = **5.46229728115577e-14** ; max |C/4 −
  l(l+1)I| = **2.1316282072803006e-14**.
- **S4** DÉGÉNÉRESCENCE comptée (n=1..10, valeurs propres de J²_full) :
  multiplicité de chaque n' == (n'+1)·(C(n,(n−n')/2) − C(n,(n−n')/2−1)) —
  **max |comptage − formule binomiale| = 0 (entiers)** ; ex. n=10 : 42/270/
  375/245/81/11 pour n'=0,2,4,6,8,10 ; Σ multiplicités = 2^n (2..1024).
- **S5** route A vs gabarit (n=1..10) : max |J_A − gabarit| =
  **3.552713678800501e-15** — la ladder mécanique EST le gabarit.
- **S6** route B (n=0..12) : n=1 == triple natif **0.0 BIT-EXACT** ; max
  |[J,J]−2iεJ| = 1.5987211554602254e-14 ; max |J² − n(n+2)I| =
  2.842170943040401e-14 ; max |J²/4 − l(l+1)I| = **7.105427357601002e-15**
  (le /4 de M6 C6 généralisé) ; max |eig(J_1,J_2) − {n, n−2, …, −n}| =
  1.2434497875801753e-14 ; n=0 : J=0, J²=0 (singulet) ; l(l+1) = 0, 0.75,
  2, 3.75, 6, 8.75, 12, 15.75, 20, 24.75, 30, 35.75, 42.
- **S7** échelle route B : max |‖J_±e_k‖² − 4·k(n−k+1)| / |·− 4·(k+1)(n−k)|
  = **2.842170943040401e-14** ; annihilations |J_+e_0|, |J_−e_n| =
  **0.0 bit-exact**.
- **S8** table : 2(2l+1) == **[2, 6, 10, 14, 18, 22, 26]** (l=0..6),
  cumuls == [2, 8, 18, 32, 50, 72, 98], (2l+1) = n+1 mesuré == [1, 3, 5, 7,
  9, 11, 13].
- **S9** échelon l=1 vs adjointe M7 : max |eig Sym²(bateman(φ)) − eig
  R_M7(bateman(φ))| = **2.3089586524979977e-15** (120 pts) ; max |eig
  Sym² − {1, e^(±2iφ)}| = 2.3089586524979977e-15 ; max ||λ|−1| =
  2.220446049250313e-15 — **le doublage réapparaît à l'échelon l=1**.

## 1. THÈSES

- **T1 (échelle native)** : les puissances symétriques du doublet natif M6
  portent la ladder complète des moments angulaires : dim du sous-espace
  symétrique de (C²)^{⊗n} = n+1 = 2l+1 (l=n/2), construite par base de
  Poids exacte — aucune bibliothèque de représentations, aucune formule de
  Clebsch-Gordan importée comme construction.
- **T2 (gabarit = mécanique)** : le gabarit orthonormé J_3 = diag(n−2k),
  J_1_{k±1,k} = √((k+1)(n−k)), J_2_{k+1,k} = +i√((k+1)(n−k)) — convention
  native tranchée par machine à n=1 (0.0 bit-exact) — coïncide avec la
  mécanique Kronecker+Poids à 3.55e-15 (n=1..10) et ferme l'algèbre
  ([J,J] = 2iεJ à 1.6e-14) et le Casimir J² = n(n+2)I = 4·l(l+1)I à
  2.84e-14 sur n=0..12.
- **T3 (dégénérescence)** : la décomposition de (C²)^{⊗n} en irréductibles
  est comptée par la machine : chaque n' apparaît avec multiplicité
  (n'+1)(C(n,(n−n')/2) − C(n,(n−n')/2−1)) — écart ENTIER 0 sur n=1..10.
- **T4 (échelle fermionique/bosonique)** : l'échelle (2l+1) [1,3,5,…] et
  la table de capacité 2(2l+1) [2,6,10,14,18,22,26] sortent du doublet ;
  le singulet n=0 (J=0, J²=0) existe nativement.
- **T5 (doublage universel)** : à l'échelon l=1, Sym²(bateman(φ)) a le
  même spectre que l'adjointe M7 R(bateman(φ)) (2.31e-15) et l'angle vaut
  2φ — le doublage M1 C0b / M5 C4 / M7 S5 se prolonge à l'échelle
  supérieure.

## 2. CONTRÔLES GELÉS

- **C0a** antériorité : mtime(FRONTIERE_M8_ECHELLE_V0.md) < début
  d'exécution du verif (exigé bit : strictement avant).
- **C1** filiation (route A, n=1) : |J_A − triple natif M6| = **0.0
  bit-exact ×3** (barre : == 0.0) ; symétriseur témoin |S_n·W − W| ≤ 1e-15
  et |tr(S_n)−(n+1)| = 0.0 bit-exact (n=1..10).
- **C2** dimensions (route A, n=1..10) : dim W == n+1 == 2l+1 (comptage
  exact par construction, exigé entier) ; witness |tr J3 − Σ(n−2k)| ≤ 1e-15.
- **C3** algèbre et Casimir projetés (route A, n=1..10) :
  |[J_i,J_j]−2iε_ijk J_k| ≤ **1e-13** ; |C/4 − l(l+1)I| ≤ **1e-13**.
- **C4** dégénérescence (route A, n=1..10) : multiplicité de chaque n' ==
  formule binomiale, **écart entier == 0 exigé** ; Σ multiplicités == 2^n.
- **C5** mécanique vs gabarit (route A, n=1..10) : |J_A − gabarit| ≤
  **1e-14**.
- **C6** route B (n=0..12) : n=1 == triple natif **0.0 bit-exact exigé** ;
  |[J,J]−2iεJ| ≤ 1e-13 ; |J²−n(n+2)I| ≤ 1e-13 ; |J²/4−l(l+1)I| ≤ 1e-13 ;
  |eig(J_1,J_2)−grille| ≤ 1e-13 ; n=0 : J=0 et J²=0 bit-exact.
- **C7** échelle (route B, n=0..12) : |‖J_±e_k‖² − cible| ≤ 1e-13 ;
  annihilations |J_+e_0|, |J_−e_n| = **0.0 bit-exact exigé**.
- **C8** échelon l=1 (S9) : |eig Sym²(bateman) − eig adjointe M7| ≤ 1e-14
  (120 pts) ; |eig Sym² − {1, e^(±2iφ)}| ≤ 1e-14 ; ||λ|−1| ≤ 1e-14.

**Échelle des verdicts** : V+ M8_ECHELLE_2L_PLUS_1_FERME (tous C0a–C8 OK et
D1–D3 OK) / V2 (C0a–C8 OK, une conséquence en échec) / V3 (un contrôle en
échec non critique) / **V4_REFUTE exit 1** (un seul contrôle critique en
échec — AUCUN sauvetage, I1).

## 3. CONSÉQUENCES GELÉES

- **D1** : (2l+1) n'est plus un gabarit lu — il est **construit** : la
  dimension du sous-espace symétrique du doubleut natif puissance n vaut
  n+1 = 2l+1, machine (C2), et la ladder mécanique coïncide avec le
  gabarit à 3.55e-15 (C5). La table de capacité 2(2l+1) de M6 D3
  (réé-temoinnée [2,6,10,14,18,22,26]) a désormais une racine constructive.
- **D2** : le Casimir généralisé J²/4 = l(l+1)I (le /4 de M6 C6) vaut sur
  TOUTE l'échelle n=0..12 à 7.11e-15 — la valeur s=1/2 fermée en M6 C6 est
  le premier échelon d'une famille fermée, pas un accident du doublet.
- **D3** : [MAPPING] le doublage est identifié à l'échelle l=1 : Sym² du
  doublet = représentation adjointe M7 (spectre 2.31e-15, angle 2φ) — un
  MÊME doublage témoinné maintenant QUATRE fois (M1 C0b, M5 C4, M7 S5, M8
  S9). (2l+1) dérivé ; reste consigné : (2l+1) ne donne pas les
  COEFFICIENTS physiques de mélange, ni la dégénérescence (2l+1)(2s+1)
  hydrogénoïde, ni le spectre de l'hamiltonien.

## 4. CONSIGNATION AVANT GEL (honnêteté)

- La base de Poids W est une construction (pas un objet déposé M1–M7) —
  mais elle n'utilise que le doublet et l'arithmétique ; toute la machinerie
  reste sans import externe de représentations.
- Le gabarit route B est une CONVENTION arbitrée par la machine (S1) — le
  signe de J_2 opposé est aussi une algèbre valide isomorphe ; seul
  l'ancrage au triple natif M6 tranche.
- (C²)^{⊗n} symétrique = secteur bosonique des moments angulaires ; les
  représentations mi-entières (n impair) y sont incluses comme échelons
  (l = n/2), la distinction boson/fermion par statistique d'échange reste
  hors portée (consignée M6/M7).
- Pas d'hamiltonien, pas de couplage EM, pas de Clebsch-Gordan complets
  (seule la décomposition symétrique est comptée — les multiplicités de
  l'autre route sont dans la formule binomiale de C4).
- ħ=1 (convention M1). Aucune graine, aucun aléa.
- Défauts estimateur corrigés AVANT gel, consignés §0 (leçon FORCE V1.2).

## 5. PORTÉE

Si C0a–C8 et D1–D3 passent : M8 ferme la huitième mort — **l'échelle
(2l+1) est un objet machine** construit depuis le doublet natif, la table
2(2l+1) consignée depuis M6 D3 a une racine constructive, et le doublage
est étendu à l'échelle l=1. La chaîne F12 tient : Pauli (M1, d0f714a),
potentiel (M2, b249526), remplissage (M3, a1048a1), nombres magiques (M4,
a73c116), spin demi-angle (M5, 963693c/f970108), SU(2) native (M6,
1dc6fcf/717edee), SO(3) adjoint (M7, 0c6e762/ef67f8a), **échelle angulaire
(ce dépôt)**. Toute extension (Clebsch-Gordan complets, hydrogénoïde,
statistique d'échange) devra sortir du même protocole : dépôt-d'abord,
barres gelées, verdict sans sauvetage.
