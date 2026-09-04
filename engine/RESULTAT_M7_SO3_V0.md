# RÉSULTAT F12 — MORT 7 / SO(3) ADJOINT : LA ROTATION GÉOMÉTRIQUE SORT DU TRIPLE NATIF — V0

**Date : 2026-09-04. Verdict machine : `V+ M7_SO3_ADJOINT_FERME` — exit 0.**

Exécution de `verif_m7_so3_v0.py` sur la frontière gelée
`FRONTIERE_M7_SO3_V0.md` (commit **0c6e762**, dépôt-d'abord — C0a OK :
frontière 07:56:19 < exécution 08:07:48). Sortie : `resultat_m7_so3_v0.json`
(déterministe, aucune graine, machinerie verbatim des dépôts : Bateman
R(θ)=[[c,s],[−s,c]] (M1 C3), 2θ=πα bit-exact (M1 C0b), triple natif
{S, −iJ, J·S}={σ_x, σ_y, σ_z} fermé bit-exact (M6 1dc6fcf/717edee),
exp(iφH) fermé depuis l'algèbre native H²=I ; grille gelée identique aux
sondes : GRID=720, ANGLES_EULER=[0.3, 0.7, 1.1, 2.3] (4³=64 composés
Euler), mp.dps=40).

**Objet M7 : la rotation géométrique n'est plus importée — elle sort du
triple.** Thèse gelée : l'application adjointe R(U)_ij = ½·tr(H_i U H_j U†)
n'utilise QUE le triple déposé M6 ; aucune formule de Rodrigues importée,
aucune bibliothèque de rotation importée, aucune exponentielle de matrice
importée. Son image est une isométrie directe de R³ (l'espace des trois
axes natifs) : la rotation sort du lien.

---

## 1. LE VERDICT — V+ M7_SO3_ADJOINT_FERME, exit 0

**C0a–C7 tous passés ET D1 ET D2 ET D3 passées** :

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 07:56:19 < 08:07:48 |
| C1 filiation M6/M1 | **OK** \| H_a²−I \| = **0.0 bit-exact** (triple natif) ; \|exp(iφH2)−bateman(φ)\| = **0.0 bit-exact** (720 pts) — la famille déposée M1 EST le sous-groupe à un paramètre du triple M6 |
| C2 adjoint réelle | **OK** | max\|R.imag\| = **1.1102230246251565e-16** (famille 720 pts ET 64 composés) |
| C3 image et axes | **OK** | \|R[1,1]−1\| 2.220446049250313e-16 ; hors bloc = **0.0 bit-exact** ; \|bloc − [[cos2φ,−sin2φ],[sin2φ,cos2φ]]\| 2.220446049250313e-16 (convention native UσU† gelée §0) ; \|R·e_2−e_2\| 2.22e-16 ; 3 axes natifs 2.22e-16 |
| C4 noyau | **OK** | \|R(bateman(π))−I₃\| 2.4492935982947064e-16 ; \|R(−U)−R(U)\| = **0.0 bit-exact** (64 composés) ; \|bateman(φ+π)+bateman(φ)\| 5.689893001203927e-16 (fibre {U,−U} visible DANS la famille déposée) |
| C5 homomorphisme et SO(3) | **OK** | \|R(UV)−R(U)R(V)\| 3.342213888644167e-16 ; \|R·Rᵀ−I₃\| : famille 4.44e-16 / composés 1.2212453270876722e-15 (barre 1e-14) ; \|det R−1\| : famille 6.66e-16 / composés 1.5543122344752192e-15 (barre 1e-14) |
| C6 angle doublé | **OK** | \|tr R(U(φ))−(1+2cos 2φ)\| 8.881784197001252e-16 (720 pts) ; 2θ−πα = **0.0 bit-exact** (M1 C0b) ; tr R(U(θ)) = **0.27525021983904013** = 1+2cos(πα), écart 5.551115123125783e-17 ; mpmath dps40 : \|R₁₁(U(θ))−cos(πα)\| = **5.73971850987445072250359637316e-42** (barre 1e-35) ; témoin tr(UU†)/2 = 1.0 |
| C7 géométrie préservée | **OK** | \|‖Rv‖²−‖v‖²\| = \|((Rv)·(Rw)−v·w)\| = **7.105427357601002e-15** (témoins gelés §0, U ∈ {bateman(θ), composés 0, 21, 63}) |

| Conséquence | Résultat | Valeur machine |
|---|---|---|
| **D1** le noyau est le centre est le deck | **OK** | R(−U)=R(U) **0.0 bit-exact** (64 composés) ; R(bateman(π))=I₃ 2.45e-16 ; bateman(φ+π)=−bateman(φ) 5.69e-16 — la signature fermionique (σ(1)=−1, centre M6 D2) est EXACTEMENT la fibre du recouvrement SU(2)→SO(3) ; ruban de Dirac en forme machine |
| **D2** M1 et M6 sont le même objet | **OK** | exp(iφH2) = bateman(φ) **0.0 bit-exact** (720 pts) ; triple H_a²=I **0.0 bit-exact** — la machinerie n'a jamais contenu d'objet étranger |
| **D3** [MAPPING] le doublage est unique | **OK** | 2θ−πα = **0.0 bit-exact** (M1 C0b re-witness) ; tr R(U(θ)) = **0.27525021983904013** = 1+2cos(πα) ; mpmath dps40 confirmé (5.74e-42) ; doublage noyau→boucle (M5, ratio 0.5) = doublage spinor→rotation (M7), témoinné trois fois (M1 C0b, M5 C4, M7 S5) ; 2(2l+1) == [2, 6, 10, 14, 18, 22, 26], (2l+1) NON dérivé, consigné |

Un seul contrôle en échec aurait déclenché `V4_REFUTE` exit 1 sans sauvetage —
précédent M6 (717edee). Aucun.

## 2. CE QUE M7 ÉTABLIT MAINTENANT

**La rotation géométrique n'a pas été importée dans le dépôt : elle en sort.**

1. **L'application adjointe est native (T1).** R(U)_ij = ½·tr(H_i U H_j U†)
   ne contient que le triple déposé M6. Elle est réelle (imag 1.11e-16),
   orthogonale de déterminant 1 pour tous les U testés (famille 720 pts +
   64 composés Euler) : **R(U) ∈ SO(3)** — homomorphisme de groupes à
   3.34e-16.

2. **La famille Bateman déposée EST le sous-groupe natif (D2).**
   exp(iφH2) = bateman(φ) à **0.0 bit-exact** sur 720 pts : le sous-groupe
   à un paramètre du triple M6 est exactement la famille déposée en M1 C3
   (d0f714a). Les deux dépôts sont le même objet, sans le savoir alors —
   la machinerie n'a jamais contenu d'objet étranger.

3. **L'image est une rotation d'angle DOUBLÉ (T3).** R(bateman(φ)) fixe
   e_2 et a pour bloc [[cos2φ, −sin2φ],[sin2φ, cos2φ]] à 2.22e-16
   (convention native UσU†, hors bloc 0.0 bit-exact) : l'angle SO(3) vaut
   2φ. Au point déposé θ=πα/2 : l'angle vaut 2θ=**πα** — le doublage M1
   C0b EST le doublage du recouvrement, re-witness par la trace
   (1+2cos(πα) = 0.27525021983904013 à 5.55e-17) et par mpmath dps40
   (R₁₁(U(θ)) = cos(πα) = −0.362374890080480119958646637475 à 5.74e-42).

4. **Le noyau de U ↦ R(U) est {±I} = le centre = le deck (D1).**
   R(−I)=I₃ à 2.45e-16, R(−U)=R(U) **bit-exact** sur les 64 composés,
   bateman(φ+π)=−bateman(φ) à 5.69e-16 : la fibre du recouvrement
   SU(2)→SO(3) est exactement {U, −U}. Le Z₂ du revêtement carré (M5),
   devenu centre de SU(2) (M6 D2), est le noyau de l'image géométrique.
   2π→−I persiste dans SU(2), 4π→+I : **le ruban de Dirac en forme
   machine.**

5. **La géométrie est préservée (T5/C7).** Normes et produits scalaires
   conservés à 7.11e-15 sur les témoins gelés : l'image adjointe est une
   isométrie directe de R³ — les trois axes natifs H_a fixent les e_a
   (2.22e-16), l'axe de la famille Bateman est e_2.

6. **Le défaut estimateur a été tranché par la machine avant gel.** Le
   bloc 2×2 fut d'abord comparé à la convention active importée
   [[cos2φ, sin2φ],[−sin2φ, cos2φ]] (échec 2.0) ; la convention native
   UσU† [[cos2φ, −sin2φ],[sin2φ, cos2φ]] est la bonne (2.22e-16) — le
   sens de rotation est porté par le signe. Corrigé et re-exécuté AVANT le
   gel (leçon FORCE V1.2), consigné dans 0c6e762.

## 3. HONNÊTETÉ (frontière §5 — ce que M7 V0 n'établit pas)

1. **Rodrigues non importé** — mais l'identité trace-angle (tr R = 1+2cosα)
   est utilisée comme témoin ; elle est vérifiée machine sur la famille
   entière (C6), pas démontrée ici.
2. **Surjectivité topologique non démontrée** : la couverture de SO(3) est
   testée sur la grille d'Euler 4³=64 ; le théorème de recouvrement
   complet n'est pas démontré dans le dépôt.
3. **Quaternions réels non construits** (autre réalisation du même double
   recouvrement) — consigné, pas résolu.
4. **Pas de vecteur physique tournant** : R³ ici est l'espace du triple
   natif (les trois axes H_a), pas un espace physique déposé ; le lien
   avec les rotations d'espace réelles reste l'identification consignée,
   non dérivée.
5. **(2l+1) non dérivé, g=2 hors portée, j non dérivé** (M4 a73c116) —
   inchangés.
6. **ħ=1** partout (convention déposée M1).
7. **Défaut estimateur corrigé avant gel** (frontière §0) : signe du bloc
   2×2 — la machine a tranché la convention UσU† contre la convention
   active importée.

## 4. LA PORTÉE (frontière §5)

M7 ferme la septième mort de la chaîne : **SO(3) est désormais un objet
machine** — construite par l'adjointe du triple natif, sans Rodrigues, sans
quaternions, sans bibliothèque de rotation ; la famille Bateman en est le
sous-groupe bit-exact, l'angle y est doublé (2θ=πα, même doublage que M1
C0b et M5 C4), le noyau y est le centre est le deck, et la géométrie est
conservée. La chaîne F12 tient : Pauli (M1, d0f714a), potentiel (M2,
b249526), remplissage (M3, a1048a1), nombres magiques (M4, a73c116), spin
demi-angle (M5, 963693c/f970108), SU(2) native (M6, 1dc6fcf/717edee),
**SO(3) adjoint (M7, ce dépôt)**. Restent consignés hors portée :
surjectivité topologique complète, quaternions réels, g=2, spin-orbite j,
(2l+1). Toute extension devra sortir du même protocole : dépôt-d'abord,
barres gelées, verdict sans sauvetage.

> **La rotation n'est plus un axiome : R(U)_ij = ½·tr(H_i U H_j U†) la
> construit depuis le triple natif, la famille Bateman y entre bit-exact,
> l'angle y vaut le double (2θ=πα — le même doublage, témoinné trois fois),
> et le noyau {±I} — le centre — est le deck. Deux tours du spinor = un
> tour de l'espace : le ruban de Dirac est en forme machine. MORT 7 FERMÉE.**