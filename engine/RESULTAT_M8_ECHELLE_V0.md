# RÉSULTAT F12 — MORT 8 / ÉCHELLE ANGULAIRE : (2l+1) SORT DU DOUBLET NATIF — V0

**Date : 2026-09-04. Verdict machine : `V+ M8_ECHELLE_2L_PLUS_1_FERME` — exit 0.**

Exécution de `verif_m8_echelle_v0.py` sur la frontière gelée
`FRONTIERE_M8_ECHELLE_V0.md` (commit **8c432c9**, dépôt-d'abord — C0a OK :
frontière 10:27:46 < exécution 10:32:24). Sortie :
`resultat_m8_echelle_v0.json` (déterministe, aucune graine, machinerie
verbatim des dépôts : triple natif M6 {S, −iJ, J·S}={σ_x, σ_y, σ_z}
(1dc6fcf/717edee), sommes de Kronecker J_k^{full} = Σ_a I⊗..⊗H_k⊗..⊗I,
base de Poids exacte (colonne k = somme normalisée des bit-strings à k
uns — SANS eigh), symétriseur S_n = (1/n!)Σ_π P_π construit exactement,
gabarit orthonormé n=0..12 ; grilles gelées : route A n=1..10, route B
n=0..12, 120 pts pour l'échelon l=1).

**Objet M8 : la dimension (2l+1) n'est plus un gabarit lu — elle est
construite.** La table de capacité 2(2l+1), consignée depuis M6 D3 comme
NON dérivée, sort du doublet natif par puissances symétriques : aucune
bibliothèque de représentations, aucune formule de Clebsch-Gordan importée
comme construction.

---

## 1. LE VERDICT — V+ M8_ECHELLE_2L_PLUS_1_FERME, exit 0

**C0a–C8 tous passés ET D1 ET D2 ET D3 passées** :

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 10:27:46 < 10:32:24 |
| C1 filiation | **OK** | à n=1, \|J_A − triple natif M6\| = **0.0 bit-exact ×3** ; symétriseur max\|S_n·W−W\| = 1.11e-16, \|tr(S_n)−(n+1)\| = 0.0 (n=1..10) |
| C2 dimensions | **OK** | dim W == n+1 == 2l+1 == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11] (entiers) ; witness \|tr J3−Σ(n−2k)\| = 8.88e-16 |
| C3 algèbre/Casimir projetés | **OK** | \|[J,J]−2iεJ\| = 5.46229728115577e-14 ; \|C/4−l(l+1)I\| = 2.1316282072803006e-14 |
| C4 dégénérescence | **OK** | multiplicité de chaque n' == (n'+1)(C(n,(n−n')/2)−C(n,(n−n')/2−1)) — **écart ENTIER = 0** ; Σ = 2^n (n=1..10, ex. n=10 : 42/270/375/245/81/11) |
| C5 mécanique vs gabarit | **OK** | max \|J_A − gabarit\| = **3.552713678800501e-15** (n=1..10) |
| C6 route B | **OK** | n=1 == triple natif **0.0 BIT-EXACT** ; algèbre 1.6e-14 ; \|J²−n(n+2)I\| 2.84e-14 ; \|J²/4−l(l+1)I\| 7.11e-15 ; spectres 1.24e-14 ; n=0 singulet J=0, J²=0 bit-exact |
| C7 échelle | **OK** | \|‖J_±e_k‖²−cible\| = 2.84e-14 ; annihilations **0.0 bit-exact** |
| C8 échelon l=1 | **OK** | \|eig Sym²(bateman) − eig adjointe M7\| = **2.3089586524979977e-15** ; angle 2φ 2.31e-15 ; \|\|λ\|−1\| 2.22e-15 (120 pts) |

| Conséquence | Résultat | Valeur machine |
|---|---|---|
| **D1** (2l+1) CONSTRUIT pas lu | **OK** | dim du sous-espace symétrique = n+1 = 2l+1 machine (n=1..10) ; ladder mécanique == gabarit 3.55e-15 ; table 2(2l+1) == [2, 6, 10, 14, 18, 22, 26] (M6 D3 re-witnessée) — racine constructive |
| **D2** Casimir généralisé | **OK** | J²/4 = l(l+1)I sur TOUTE l'échelle n=0..12 (7.105427357601002e-15) — s=1/2 (M6 C6) est le premier échelon d'une famille fermée, pas un accident du doublet |
| **D3** [MAPPING] doublage à l'échelle l=1 | **OK** | Sym² du doublet = représentation adjointe M7 (spectre 2.31e-15, angle 2φ) — un MÊME doublage témoinné **QUATRE fois** (M1 C0b, M5 C4, M7 S5, M8 S9) |

Un seul contrôle en échec aurait déclenché `V4_REFUTE` exit 1 sans
sauvetage — précédents M6 (717edee), M7 (ef67f8a). Aucun.

## 2. CE QUE M8 ÉTABLIT MAINTENANT

1. **L'échelle (2l+1) est un objet machine (T1/D1).** La dimension du
   sous-espace symétrique de (C²)^{⊗n} vaut n+1 = 2l+1 — construite par la
   base de Poids exacte (sommes normalisées des bit-strings à k uns), pas
   lue dans un manuel. La table de capacité 2(2l+1) = [2, 6, 10, 14, 18,
   22, 26], consignée comme NON dérivée depuis M6 D3, a désormais une
   racine constructive dans le doublet natif.

2. **La ladder complète est mécanique (T2/C5/C6/C7).** Sommes de Kronecker
   des trois générateurs natifs + projection Poids = le gabarit
   orthonormé (3.55e-15) : J_3 = diag(n−2k), ‖J_±e_k‖² = 4·k(n−k+1) /
   4·(k+1)(n−k), annihilations bit-exact. L'algèbre ferme ([J,J] = 2iεJ à
   1.6e-14), le Casimir vaut J² = n(n+2)I = 4·l(l+1)I à 2.84e-14 sur
   n=0..12, et les spectres tombent sur la grille {n, n−2, …, −n} à
   1.24e-14.

3. **La dégénérescence est comptée, pas postulée (T3/C4).** La
   décomposition de (C²)^{⊗n} en irréductibles de spin n' porte la
   multiplicité (n'+1)(C(n,(n−n')/2) − C(n,(n−n')/2−1)) — écart ENTIER 0
   sur toute la grille, Σ = 2^n. Le singulet n=0 existe nativement
   (J=0, J²=0 bit-exact).

4. **s=1/2 est le premier échelon d'une famille fermée (D2).** Le Casimir
   /4 de M6 C6 (qui fermait s(s+1)=3/4) se généralise : J²/4 = l(l+1)I
   pour tout l = n/2, entier OU mi-entier, sur toute l'échelle. La
   demi-unité de spin n'est pas un accident du doublet : c'est le premier
   terme de la suite fermée par la même machinerie.

5. **Le doublage est universel (T5/D3).** À l'échelon l=1, Sym² de la
   famille Bateman a le même spectre que l'adjointe M7 (2.31e-15) et l'angle
   y vaut 2φ. Un MÊME doublage est témoinné quatre fois : noyau→boucle (M1
   C0b), monodromie (M5 C4), spinor→rotation (M7 S5), doublet→échelon
   l=1 (M8 S9).

6. **Les défauts estimateur ont été corrigés AVANT le gel (leçon FORCE
   V1.2).** La première exécution de la sonde portait deux défauts : le
   signe de J_2 du gabarit (convention importée inversée) et la base
   `eigh` arbitraire (comparaison élément-à-élément invalide, échecs
   8.0/14.0/48.0). La machine a tranché la convention NATIVE (|J_2^(A)(n=1)
   − (−iJ)| = 0.0 bit-exact ; l'autre signe donne 2.0) et la base de Poids
   exacte a remplacé eigh. Corrigé, re-exécuté propre, consigné dans
   8c432c9 §0.

## 3. HONNÊTETÉ (frontière §4 — ce que M8 V0 n'établit pas)

1. **La base de Poids est une construction** — elle n'utilise que le
   doublet et l'arithmétique, mais elle n'est pas un objet déposé M1–M7 ;
   son statut est consigné.
2. **La convention J_2 est arbitrée par la machine** — le signe opposé est
   aussi une algèbre valide isomorphe ; seul l'ancrage au triple natif M6
   tranche.
3. **Pas de statistique d'échange** : le secteur symétrique porte les
   échelons l = n/2 entiers ET mi-entiers ; la distinction boson/fermion
   par statistique reste hors portée (consignée M6/M7).
4. **Pas de Clebsch-Gordan complets** : seule la décomposition symétrique
   est comptée (les multiplicités de l'autre secteur sont dans la formule
   binomiale de C4) ; les coefficients de mélange physique ne sont pas
   dérivés.
5. **Pas d'hamiltonien, pas de dégénérescence hydrogénoïde** :
   (2l+1)(2s+1) et le spectre de l'hamiltonien restent hors portée.
6. **ħ=1** partout (convention déposée M1).

## 4. LA PORTÉE (frontière §5)

M8 ferme la huitième mort de la chaîne : **l'échelle angulaire est un
objet machine** — (2l+1) construit depuis le doublet natif, la table
2(2l+1) de M6 D3 enracinée, le Casimir généralisé fermé sur toute
l'échelle, la dégénérescence comptée avec un écart entier nul, et le
doublage étendu à l'échelle l=1. La chaîne F12 tient : Pauli (M1,
d0f714a), potentiel (M2, b249526), remplissage (M3, a1048a1), nombres
magiques (M4, a73c116), spin demi-angle (M5, 963693c/f970108), SU(2)
native (M6, 1dc6fcf/717edee), SO(3) adjoint (M7, 0c6e762/ef67f8a),
**échelle angulaire (ce dépôt)**. Restent consignés hors portée :
statistique d'échange, Clebsch-Gordan complets, hydrogénoïde, g=2,
spin-orbite j. Toute extension devra sortir du même protocole :
dépôt-d'abord, barres gelées, verdict sans sauvetage.

> **La dimension n'est plus un gabarit : le sous-espace symétrique du
> doublet natif puissance n vaut n+1 = 2l+1, la ladder y tombe du Kronecker
> (mécanique == gabarit à 3.55e-15), la dégénérescence est comptée à un
> écart entier nul, le Casimir J²/4 = l(l+1)I ferme toute l'échelle —
> s=1/2 est le premier échelon, pas un accident — et le doublage 2φ
> remonte à l'échelon l=1 : témoinné quatre fois. MORT 8 FERMÉE.**