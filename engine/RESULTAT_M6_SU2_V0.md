# RÉSULTAT F12 — MORT 6 / SU(2) NATIVE : L'ALGÈBRE DE PAULI SORT DES OBJETS DÉPOSÉS — V0

**Date : 2026-09-04. Verdict machine : `V+ M6_SU2_NATIVE_PAULI_FERME` — exit 0.**

Exécution de `verif_m6_su2_v0.py` sur la frontière gelée
`FRONTIERE_M6_SU2_V0.md` (commit **1dc6fcf**, dépôt-d'abord — C0a OK :
frontière 07:23:01 < exécution 07:25:07, écart 2 min 6 s). Sortie :
`resultat_m6_su2_v0.json` (sub-seconde, déterministe, aucune graine,
machinerie verbatim des dépôts : Bateman R(θ)=[[c,s],[−s,c]] (M1 C3),
σ(α)=e^{iπα} (M1 C4), λ(ω)=(iω)^α branche principale (D3D db00e3b O2/C10),
deck z↦−z et fibre {+i|ω|, −i|ω|} (M5 963693c/f970108) ; grille gelée
identique aux sondes : GRID=720, RS=[0.5, 1.0, 2.0, 3.0, 25.6], h=1e-5,
mp.dps=40).

**Objet M6 : l'algèbre de spin n'est plus importée — elle sort du lien.**
Thèse gelée : DEUX objets déposés engendrent les trois matrices de Pauli —
σ_x = S (le deck : échange des feuillets de la fibre du carré),
σ_y = −i·J (la tangente Bateman J=dR/dθ|₀ ; le i est celui du noyau
λ(ω)=(iω)^α), σ_z = J·S (produit des deux). Aucune matrice de Pauli
importée, aucune algèbre de Lie importée.

---

## 1. LE VERDICT — V+ M6_SU2_NATIVE_PAULI_FERME, exit 0

**C0a–C7 tous passés ET D1 ET D2 ET D3 passées** :

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 07:23:01 < 07:25:07 |
| C1 filiation M1 C3 | **OK** | R(0)−I = **0.0 bit-exact** ; \|det R(φ)−1\| max 2.220446049250313e-16 ; \|tr R(φ)−2cosφ\| = **0.0** ; \|R†R−I\| 2.22e-16 (720 pts) |
| C2 générateurs natifs | **OK** | écart(J numérique h=1e-5, J analytique) 1.6666779067975313e-11 (barre 1e-10) ; S²−I = J²+I = P²−I = **0.0 bit-exact** ; tr = 0.0×3 ; P == diag(1,−1) **0.0** |
| C3 algèbre Pauli bit-exacte | **OK** | hermiticité **0.0** ; H_a²−I **0.0** ; [H1,H2]−2iH3 / [H2,H3]−2iH1 / [H3,H1]−2iH2 = **0.0 bit-exact** ; {H_a,H_a}−2I = **0.0** ; {H_a,H_b} a≠b = **0.0** ; tr = **0.0** |
| C4 lift demi-angle | **OK** | \|bateman(φ)²−bateman(2φ)\| 2.220446049250313e-16 (720 pts) ; \|bateman(π)+I\| 1.2246467991473532e-16 ; \|bateman(2π)−I\| 2.4492935982947064e-16 ; centralité −I = **0.0 bit-exact** |
| C5 appartenance SU(2) | **OK** | \|U†U−I\| 2.22e-16 ; \|det U−1\| 2.22e-16 ; \|U(0.7)†−U(−0.7)\| = **0.0** ; \|(−U(0.3))·(−U(1.1))−U(1.4)\| 1.6653345369377348e-16 (groupe {±U(φ)} fermé) |
| C6 Casimir | **OK** | \|(H1²+H2²+H3²)/4 − (3/4)I\| = **0.0 bit-exact** ; racine s(s+1)=3/4 : **s = 0.5** (écart 0.0, mpmath dps40) ; eig(S_z) = **{−1/2, +1/2}** écart **0.0** |
| C7 cohérence M5 + consignation | **OK** | fibre α=1 bit-exacte (λ(±r)=±i·r, écart **0.0**) ; fibres à 2 valeurs **5/5** ; \|σ(1)+1\| 1.2246467991473532e-16 ; eig(S) = **{−1, +1}** écart **0.0** |

| Conséquence | Résultat | Valeur machine |
|---|---|---|
| **D1** le spin du lien vaut UN DEMI | **OK** | Casimir (1/4)Σσ²=(3/4)I **0.0 bit-exact** ; racine s(s+1)=3/4 : **s=0.5** (mpmath dps40) ; eig(S_z) = **{−1/2, +1/2}** écart **0.0** |
| **D2** la signature d'échange EST le centre | **OK** | eig(S) = **{−1, +1}** ; σ(1) = **−1+1.22e-16j** ; −I central **0.0** ; U(π)=−I 1.22e-16 — Z₂ du revêtement = centre de SU(2) |
| **D3** [MAPPING] dimension | **OK** | dimension 2 = dimension de fibre M5 (5/5 ré-witness C7) ; 2(2l+1), l=0..6 == **[2, 6, 10, 14, 18, 22, 26]** ; (2l+1) NON dérivé, consigné |

Un seul contrôle en échec aurait déclenché `V4_REFUTE` exit 1 sans sauvetage —
précédent M5 (f970108). Aucun.

## 2. CE QUE M6 ÉTABLIT MAINTENANT

**L'algèbre de spin n'a pas été importée dans le dépôt : elle en sort.**

1. **Deux objets natifs engendrent le triple de Pauli.** Le deck S
   (échange des feuillets de la fibre du carré, M5 C2/D2) et la tangente
   Bateman J=dR/dθ|₀ (famille déposée M1 C3) donnent σ_x=S, σ_y=−i·J
   (le i est celui du noyau λ(ω)=(iω)^α — aucun i importé), σ_z=J·S.
   Aucun des trois n'est postulé : deux sont des objets du lien, le
   troisième est leur produit.

2. **L'algèbre se ferme BIT-EXACT (C3, tout à 0.0).** Hermiticité, carrés
   unité, commutateurs [σ_a,σ_b]=2iε_abc·σ_c, anticommuteurs
   {σ_a,σ_b}=2δ_ab·I, traces nulles — chaque relation est satisfaite à
   0.0, pas « à tolérance près » : l'algèbre de Pauli est une identité
   machine du triple natif.

3. **Le lift demi-angle est la même structure que M5.** bateman(φ)²=
   bateman(2φ) à 2.22e-16 sur 720 pts (C4) : le sous-groupe exp(φJ)
   double-couvre la famille Bateman, exactement comme le noyau
   double-couvre la boucle (ratio 0.5 bit-exact, M5 C4). Un tour de
   boucle (2π) → −I, deux tours (4π) → +I : le feuillet du noyau est un
   spineur, et le deck EST sa monodromie.

4. **La valeur du spin sort — elle n'est plus postulée.** Le Casimir du
   triple natif vaut (σ_x²+σ_y²+σ_z²)/4 = (3/4)·I **bit-exact** (C6/D1)
   ⟹ s(s+1)=3/4 ⟹ **s=1/2** (racine mpmath dps40), spectre de S_z :
   {−1/2, +1/2} écart 0.0. La valeur 1/2 postulée en M1 (d0f714a) est
   désormais un théorème du lien — et elle EST le ratio demi-angle 0.5
   de M5 C4.

5. **La signature fermionique est l'élément central.** σ(1)=−1 (M1 C4,
   ré-witness M5) est valeur propre du deck (eig(S)={−1,+1}, écart 0.0) ;
   −I est central à 0.0 (C4) et U(π)=−I (C4) : le signe qui exclut
   (‖Ψ_exclu‖=3.33e-17, M5 C6) est le centre de la structure SU(2)
   native. Le Z₂ du revêtement carré EST le centre de SU(2) (D2).

6. **Le groupe {±U(φ)} est fermé (C5).** Unitarité et det=1 à 2.22e-16
   sur 720 pts, U(φ)†=U(−φ) bit-exact, (−U(φ₁))·(−U(φ₂))=U(φ₁+φ₂) à
   1.67e-16 : le sous-groupe spinoriel natif est un vrai groupe.

## 3. HONNÊTETÉ (frontière §5 — ce que M6 V0 n'établit pas)

1. **SO(3) n'est pas construite** : un seul axe à un paramètre est natif
   (exp(φJ), famille Bateman) ; les axes σ_x et σ_z viennent du deck par
   produits, pas d'une dérivation géométrique de la rotation d'espace.
   SU(2) comme GROUPE complet n'est pas construite — le sous-groupe
   {±U(φ)} et l'ALGÈBRE su(2) sont natifs.
2. **g=2 hors portée** : aucun couplage électromagnétique dans les dépôts.
3. **j (spin-orbite) non dérivé** : le rang 4 nucléaire de M4 (a73c116)
   reste consigné.
4. **sl(2,R) vs su(2)** : la forme réelle {S,J,P} est split (sl(2,R)) ; la
   fermeture hermitienne {S, −iJ, P}=su(2) passe par le i du noyau. Le
   compactage est porté par la machinerie déposée, pas démontré unique.
5. **ħ=1** partout (convention déposée M1) ; pas de L_i orbital, pas de
   couplage [L,S].
6. **(2l+1) non dérivé** : M6 ne ferme ni la dégénérescence des modes de
   boucle, ni la capacité totale — uniquement s=1/2 et l'algèbre.
7. **Défauts estimateurs corrigés avant gel** (frontière §0, leçon FORCE
   V1.2) : label du contrôle commutateurs (S2) et compteur de fibres (S6,
   inégalité stricte rejetait r=0.5 → 4/5 affiché ; corrigée en ≥, re-
   exécuté 5/5, la fibre était bit-exacte). Consignés dans 1dc6fcf.

## 4. LA PORTÉE (frontière §5)

M6 ferme la sixième mort de la chaîne : **la valeur du spin (1/2) et son
algèbre (su(2)) sont désormais des objets machine** — engendrés par le deck
et la tangente Bateman, fermés bit-exact, double recouvrement natif,
Casimir (3/4)I bit-exact, signe d'échange = centre. La chaîne F12 tient :
Pauli (M1, d0f714a), potentiel (M2, b249526), remplissage (M3, a1048a1),
nombres magiques (M4, a73c116), spin demi-angle (M5, 963693c/f970108),
**SU(2) native (M6, ce dépôt)**. Restent consignés hors portée : SO(3)
géométrique complète, g=2, spin-orbite j, (2l+1). Toute extension devra
sortir du même protocole : dépôt-d'abord, barres gelées, verdict sans
sauvetage.

> **Les matrices de Pauli ne sont plus un axiome : σ_x est le deck du
> revêtement carré, σ_y est la tangente Bateman multipliée par le i du
> noyau, σ_z est leur produit — l'algèbre se ferme bit-exact et le Casimir
> rend s=1/2. La valeur postulée en M1 est un théorème du lien. MORT 6 FERMÉE.**
