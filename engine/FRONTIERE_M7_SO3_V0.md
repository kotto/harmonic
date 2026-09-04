# FRONTIÈRE M7 — SO(3) ADJOINT : LA ROTATION GÉOMÉTRIQUE SORT DU TRIPLE NATIF — V0

**Dépôt-d'abord (C0a)** : ce fichier est committé AVANT l'écriture de tout
script de vérification M7. Toutes les valeurs ci-dessous ont été calculées par
`sonde_m7_so3_v0.py` (fichier non committé, règle maison) AVANT le gel, et la
sortie témoin est `sonde_m7_so3_v0_output.txt`. Un seul contrôle en échec
⟹ V4_REFUTE exit 1, sans sauvetage (I1).

Machinerie verbatim des dépôts : Bateman R(θ)=[[c,s],[−s,c]] (M1 C3),
2θ=πα bit-exact (M1 C0b), triple natif {S, −iJ, J·S}={σ_x, σ_y, σ_z} fermé
bit-exact (M6 1dc6fcf/717edee), ratio demi-angle 0.5 (M5 C4). Aucune formule
de Rodrigues importée, aucune bibliothèque de rotation importée, aucune
exponentielle de matrice importée : exp(iφH) est fermé depuis l'algèbre
native H²=I (cosφ·I + i·sinφ·H).

**Défaut estimateur corrigé AVANT gel (leçon FORCE V1.2), consigné :**
le bloc 2×2 de S2 était comparé à [[cos2φ, sin2φ],[−sin2φ, cos2φ]] (convention
active standard) ; la machine donne la convention native UσU† :
**[[cos2φ, −sin2φ],[sin2φ, cos2φ]]** (transposée — le sens de rotation est
porté par le signe). Référentiel corrigé et re-exécuté AVANT le commit de
cette frontière : écart 2.220446049250313e-16. La machine est l'arbitre du
signe, pas la convention importée.

---

## 0. TÉMOINS PRÉ-GEL (sonde, sortie brute reproductible)

Grille : φ = π·k/720, k=0..719 ; ANGLES_EULER=[0.3, 0.7, 1.1, 2.3] (4³=64
composés U = exp(iαH1)·exp(iβH2)·exp(iγH3)) ; θ=πα/2 ; mp.dps=40.
Déterministe, aucune graine.

- S0 filiation : |H_a²−I| max = **0.0** (bit-exact, M6 C3) ;
  |exp(iφH2) − bateman(φ)| max sur 720 pts = **0.0** (**BIT-EXACT : la famille
  Bateman déposée EST le sous-groupe à un paramètre du triple natif**).
- S1 adjoint réelle : R(U)_ij = ½·tr(H_i U H_j U†) ; max|R.imag| = **1.1102230246251565e-16**
  (famille 720 pts ET 64 composés).
- S2 image de la famille : R(bateman(φ))[1,1]−1 max = **2.220446049250313e-16** ;
  coefficients hors bloc max = **0.0** (bit-exact) ;
  |bloc 2×2 − [[cos2φ, −sin2φ],[sin2φ, cos2φ]]| max = **2.220446049250313e-16**
  (convention native UσU†) ; |R(φ)·e_2 − e_2| max = **2.220446049250313e-16** ;
  les 3 axes natifs |R(exp(iφH_a))·e_a − e_a| max = **2.220446049250313e-16**.
- S3 noyau : |R(bateman(π)) − I₃| = **2.4492935982947064e-16** (bateman(π)=−I
  à 1.22e-16, M6 C4) ; |R(−U) − R(U)| max sur 64 composés = **0.0** (BIT-EXACT) ;
  |bateman(φ+π) + bateman(φ)| max = **5.689893001203927e-16** (la fibre du
  carré {U, −U} est visible DANS la famille déposée).
- S4 homomorphisme et SO(3) : |R(UV) − R(U)R(V)| max = **3.342213888644167e-16** ;
  |R·Rᵀ − I₃| max : famille **4.440892098500626e-16**, composés **1.2212453270876722e-15** ;
  |det R − 1| max : famille **6.661338147750939e-16**, composés **1.5543122344752192e-15**.
- S5 angle doublé : |tr R(U(φ)) − (1+2cos 2φ)| max sur 720 pts = **8.881784197001252e-16** ;
  2θ − πα = **0.0** (bit-exact, M1 C0b verbatim) ; tr R(U(θ)) = **0.27525021983904013**,
  écart à 1+2cos(πα) = **5.551115123125783e-17**.
- S6 géométrie : |‖Rv‖² − ‖v‖²| max = **7.105427357601002e-15** ;
  |(Rv)·(Rw) − v·w| max = **7.105427357601002e-15** (témoins v=(1,2,3)/√14,
  (φ,1,1/φ)/√(φ²+1+φ⁻²), (0.7,−1.3,2.2) ; U ∈ {bateman(θ), composés 0, 21, 63}).
- S7 mpmath dps40 : R₁₁(U(θ)) = **−0.362374890080480119958646637475** =
  cos(πα) = **−0.362374890080480119958646637475**, écart **5.73971850987445072250359637316e-42** ;
  contrôle tr(UU†)/2 = **1.0**.

**M — CONSIGNATION (avant gel) :** formule de Rodrigues NON importée (l'angle
SO(3) est témoinné par le bloc 2×2 natif et par la trace) ; quaternions réels
NON construits (autre réalisation du même double recouvrement — consigné, pas
résolu) ; surjectivité topologique SU(2)→SO(3) NON démontrée (testée sur la
grille d'Euler 4³=64, produits des trois sous-groupes natifs) ; l'étiquetage
des axes (H1↔e_1, H2↔e_2, H3↔e_3) est la convention du triple natif M6 —
aucun axe externe ; ħ=1 (convention M1).

---

## 1. THÈSES GELÉES

**T1 — l'application adjointe est native.** R(U)_ij = ½·tr(H_i U H_j U†)
n'utilise QUE le triple déposé M6. Elle est réelle (imag 1.11e-16), et pour
tous U testés (famille 720 pts + 64 composés Euler) elle est orthogonale de
déterminant 1 : **R(U) ∈ SO(3)**.

**T2 — la famille Bateman déposée EST le sous-groupe natif.**
exp(iφH2) = bateman(φ) à **0.0 bit-exact** sur 720 pts : M1 C3 (d0f714a) est
le sous-groupe à un paramètre du triple M6 — les deux dépôts sont le même
objet, sans le savoir alors.

**T3 — l'image est une rotation d'angle DOUBLÉ.** R(bateman(φ)) fixe e_2 et
a pour bloc [[cos2φ, −sin2φ],[sin2φ, cos2φ]] (convention UσU†, écart 2.22e-16)
: l'angle SO(3) vaut 2φ. Au point déposé θ=πα/2 : l'angle vaut 2θ=πα —
**le doublage M1 C0b EST le doublage du recouvrement** ; tr R(U(θ)) = 1+2cos(πα)
= 0.27525021983904013 à 5.55e-17, confirmé mpmath dps40 (5.74e-42).

**T4 — le noyau de U ↦ R(U) est {±I} = le centre = le deck.** R(−I)=I₃ à
2.45e-16, R(−U)=R(U) BIT-EXACT sur 64 composés, et bateman(φ+π)=−bateman(φ)
à 5.69e-16 : la fibre du recouvrement SU(2)→SO(3) est exactement {U, −U} —
le Z₂ du revêtement carré (M5), devenu centre (M6 D2), est le noyau de
l'image géométrique.

**T5 — la géométrie est préservée.** Normes et produits scalaires conservés
à 7.11e-15 sur les témoins : l'image adjointe est une isométrie directe de
R³ — la rotation géométrique sort du lien sans aucune importation.

---

## 2. CONTRÔLES GELÉS (un seul échec ⟹ V4_REFUTE exit 1)

- **C0a antériorité** : mtime(FRONTIERE_M7_SO3_V0.md) < début d'exécution du verif.
- **C1 filiation M6/M1** : |H_a²−I| = 0.0 (bit-exact exigé) ;
  |exp(iφH2) − bateman(φ)| = 0.0 (bit-exact exigé, 720 pts).
- **C2 adjoint réelle** : max|R.imag| ≤ 1e-15 (1.11e-16 mesuré) sur famille
  720 pts ET 64 composés.
- **C3 image de la famille et axes** : R[1,1]−1 ≤ 1e-15 (2.22e-16) ; hors
  bloc = 0.0 (bit-exact exigé) ; |bloc − [[cos2φ, −sin2φ],[sin2φ, cos2φ]]| ≤ 1e-15
  (2.22e-16, convention UσU† gelée §0) ; |R·e_2 − e_2| ≤ 1e-15 (2.22e-16) ;
  les 3 axes fixes ≤ 1e-15 (2.22e-16).
- **C4 noyau** : |R(bateman(π)) − I₃| ≤ 1e-15 (2.45e-16) ; |R(−U) − R(U)| = 0.0
  (bit-exact exigé, 64 composés) ; |bateman(φ+π) + bateman(φ)| ≤ 1e-15 (5.69e-16).
- **C5 homomorphisme et appartenance SO(3)** : |R(UV) − R(U)R(V)| ≤ 1e-15
  (3.34e-16) ; |R·Rᵀ − I₃| ≤ 1e-15 famille (4.44e-16) ET ≤ 1e-14 composés
  (1.22e-15) ; |det R − 1| ≤ 1e-15 famille (6.66e-16) ET ≤ 1e-14 composés
  (1.55e-15).
- **C6 angle doublé** : |tr R(U(φ)) − (1+2cos 2φ)| ≤ 1e-15 sur 720 pts
  (8.88e-16) ; 2θ − πα = 0.0 (bit-exact exigé) ; |tr R(U(θ)) − (1+2cos πα)| ≤ 1e-15
  (5.55e-17) ; mpmath dps40 : |R₁₁(U(θ)) − cos(πα)| ≤ 1e-35 (5.74e-42).
- **C7 géométrie préservée** : |‖Rv‖² − ‖v‖²| ≤ 1e-14 (7.11e-15) ;
  |(Rv)·(Rw) − v·w| ≤ 1e-14 (7.11e-15) sur les témoins gelés §0.

---

## 3. CONSÉQUENCES GELÉES

- **D1 — le noyau est le centre est le deck.** R(−U)=R(U) bit-exact et
  R(bateman(π))=I₃ : la signature fermionique (σ(1)=−1, M1 C4 ; centre, M6 D2)
  est EXACTEMENT la fibre du recouvrement SU(2)→SO(3). Deux tours du spinor
  = un tour de l'espace : 2π → −I (persiste dans SU(2)), 4π → +I — le ruban
  de Dirac en forme machine.
- **D2 — M1 et M6 sont le même objet.** exp(iφH2) = bateman(φ) bit-exact :
  la famille déposée en M1 C3 est le sous-groupe à un paramètre du triple
  natif M6 ; la machinerie n'a jamais contenu d'objet étranger.
- **D3 — [MAPPING] le doublage est unique.** L'angle SO(3) à θ=πα/2 vaut
  2θ=πα (M1 C0b bit-exact re-witness) : le doublage noyau→boucle (M5, ratio
  0.5) et le doublage spinor→rotation (M7) sont le MÊME doublage, témoinné
  trois fois (M1 C0b, M5 C4, M7 S5). Table 2(2l+1) inchangée, (2l+1) toujours
  non dérivé.

---

## 4. ÉCHELLE DE VERDICT (gelée)

- **V+ M7_SO3_ADJOINT_FERME** : C0a–C7 tous OK ET D1 ET D2 ET D3 OK.
- **V2** : C0a–C7 OK mais au moins une conséquence en échec.
- **V3** : tous les contrôles sauf C0a OK (antériorité seule défaillante).
- **V4_REFUTE exit 1** : tout autre cas. Un seul échec ⟹ sortie immédiate,
  aucun sauvetage, aucune re-normalisation, aucun ajustement.

---

## 5. HONNÊTETÉ ET PORTÉE (gelées)

1. **Rodrigues non importé** — mais l'identité trace-angle (tr R = 1+2cosα)
   est utilisée comme témoin ; elle est vérifiée machine sur la famille
   entière (C6), pas démontrée ici.
2. **Surjectivité topologique non démontrée** : la couverture de SO(3) est
   testée sur la grille d'Euler 4³=64 ; le théorème de recouvrement complet
   n'est pas démontré dans le dépôt — le comportement machine est témoinné
   sur la grille.
3. **Quaternions réels non construits** (autre réalisation du même double
   recouvrement) — consigné, pas résolu.
4. **Pas de vecteur physique tournant** : R³ ici est l'espace du triple
   natif (les trois axes H_a), pas un espace physique déposé ; le lien avec
   les rotations d'espace réelles reste l'identification consignée, non
   dérivée.
5. **(2l+1) non dérivé, g=2 hors portée, j non dérivé** (M4 a73c116) —
   inchangés.
6. **ħ=1** partout (convention déposée M1).
7. **Défaut estimateur corrigé avant gel** (§0) : signe du bloc 2×2 (la
   machine a tranché la convention UσU† contre la convention active importée).

**Chaîne de filiation** : M1 Pauli/échange (d0f714a) → M2 potentiel mémoire
(b249526) → M3 remplissage (a1048a1) → M4 nombres magiques (a73c116) → M5
spin demi-angle (963693c/f970108) → M6 SU(2) native (1dc6fcf/717edee) →
M7 SO(3) adjoint (ce dépôt, frontière gelée avant verif — C0a).
