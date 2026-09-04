# FRONTIÈRE M6 — SU(2) NATIVE : L'ALGÈBRE DE PAULI SORT DES OBJETS DÉPOSÉS — V0

**Dépôt-d'abord (C0a)** : ce fichier est committé AVANT l'écriture de tout
script de vérification M6. Toutes les valeurs ci-dessous ont été calculées par
`sonde_m6_su2_v0.py` (fichier non committé, règle maison) AVANT le gel, et la
sortie témoin est `sonde_m6_su2_v0_output.txt`. Un seul contrôle en échec
⟹ V4_REFUTE exit 1, sans sauvetage (I1).

Machinerie verbatim des dépôts : Bateman R(θ)=[[c,s],[−s,c]] (M1 C3),
σ(α)=e^{iπα} (M1 C4), tension (M1 C5), λ(ω)=(iω)^α branche principale
(D3D db00e3b O2/C10), deck z↦−z et fibre {+i|ω|, −i|ω|} (M5 963693c/f970108).
Aucune matrice de Pauli importée, aucune algèbre de Lie importée.

**Défauts estimateurs corrigés AVANT gel (leçon FORCE V1.2), consignés :**
1. label du contrôle commutateurs (S2) : « [H2,H3] − 2i·H1, [H3,H1] − 2i·H1 »
   — faute de frappe d'affichage, corrigée en « [H3,H1] − 2i·H2 » ; les valeurs
   machine étaient déjà correctes (0.0).
2. compteur de fibres (S6) : inégalité stricte |λ(r)−λ(−r)| > 1.0 rejetait
   r=0.5 (écart exactement 1.0) → 4/5 affiché ; corrigée en ≥ 1.0 avant gel,
   re-exécuté : **5/5** (la fibre était bit-exacte 5/5, seul le compteur
   tranchait mal). Corrigé AVANT le commit de cette frontière.

---

## 0. TÉMOINS PRÉ-GEL (sonde, sortie brute reproductible)

Grille : φ = π·k/720, k=0..719 ; RS=[0.5, 1.0, 2.0, 3.0, 25.6] ; N=512,
L=20π, D_OMEGA=0.1, W0=1.0 ; h(diff. finie)=1e-5 ; mp.dps=40. Déterministe,
aucune graine.

- S0 filiation : R(0)−I = **0.0** (bit-exact) ; |det R(φ)−1| max = **2.220446049250313e-16** ;
  |tr R(φ)−2cosφ| max = **0.0** (bit-exact) ; |R†R−I| max = **2.220446049250313e-16** (720 pts).
- S1 générateurs : deck S=[[0,1],[1,0]] (échange de feuillets M5) ;
  J=[[0,1],[−1,0]] ; J numérique (diff. centrée h=1e-5 sur R déposée) écart max
  = **1.6666779067975313e-11** ; P=J·S=[[1,0],[0,−1]] ; S²−I = **0.0**, J²+I = **0.0**,
  P²−I = **0.0** (tous bit-exacts) ; tr(S)=tr(J)=tr(P)=**0.0**.
- S2 triple de Pauli natif {S, −iJ, J·S} : hermiticité |H−H†| max = **0.0** ;
  |H_a²−I| max = **0.0** ; [H1,H2]−2i·H3, [H2,H3]−2i·H1, [H3,H1]−2i·H2 : écart max
  = **0.0** (bit-exact) ; {H_a,H_a}−2I = **0.0** ; {H_a,H_b} (a≠b) max = **0.0** ;
  |tr H_a| max = **0.0**.
- S3 lift demi-angle : |bateman(φ)²−bateman(2φ)| max sur 720 pts = **2.220446049250313e-16** ;
  |bateman(π)−(−I)| = **1.2246467991473532e-16** (sin(π) flottant = 1.2246467991473532e-16) ;
  |bateman(2π)−I| = **2.4492935982947064e-16** ; centralité [−I,{S,J,P}] = **0.0** (bit-exact).
- S4 appartenance SU(2) : |U†U−I| max = 2.220446049250313e-16 ; |det U−1| max =
  2.220446049250313e-16 ; |U(0.7)†−U(−0.7)| = **0.0** (bit-exact) ;
  |(−U(0.3))·(−U(1.1))−U(1.4)| = **1.6653345369377348e-16** (groupe {±U(φ)} fermé).
- S5 Casimir : |(H1²+H2²+H3²)/4 − (3/4)I| = **0.0** (bit-exact) ; racine mpmath
  dps40 de s(s+1)=3/4 : **s = 0.5** ; eig(S_z) = **{−0.5, +0.5}**, écart **0.0**
  (S_z = P/2).
- S6 cohérence M5 : fibre à α=1 sur RS : λ(+r)=+i·r, λ(−r)=−i·r **bit-exact**
  (écart max **0.0**) ; fibres à 2 valeurs **5/5** ; σ(1)=e^{iπ}=(−1+1.2246467991473532e-16j),
  |σ(1)+1| = **1.2246467991473532e-16** ; eig(deck S) = **{−1, +1}**, écart **0.0**.
- S7 mpmath dps40 : θ = πα/2 = 0.970805519362733288673432814981 ;
  |bateman(θ)²₀₀−cos(2θ)| = **0.0** ; |bateman(θ)²₀₁−sin(2θ)| = **1.14794370197489014450071927463e-41**.

**M — CONSIGNATION (avant gel, C7) :** SO(3) géométrique NON construite (un
seul axe à un paramètre est natif — exp(φJ) de la famille Bateman ; les deux
autres axes du triple viennent du deck par produits, pas d'une rotation
d'espace dérivée) ; g=2 hors portée (aucun couplage électromagnétique déposé) ;
spin-orbite j non dérivé (M4 a73c116) ; forme réelle {S,J,P} ∈ sl(2,R) (split)
vs fermeture hermitienne {S, −iJ, P} = su(2) (compacte) : le i qui compactifie
est celui du noyau λ(ω)=(iω)^α — consigné, pas résolu ; ħ=1 (convention M1).

---

## 1. THÈSES GELÉES

**T1 — deux objets déposés engendrent les trois matrices de Pauli.**
σ_x = S (le deck : échange des feuillets de la fibre du carré, M5 C2/D2) ;
σ_y = −i·J (la tangente Bateman J=dR/dθ|_0, M1 C3 ; le i est celui du noyau
λ(ω)=(iω)^α, D3D db00e3b O2/C10) ; σ_z = J·S (produit des deux). Aucune
matrice importée : le triple est un objet du lien.

**T2 — l'algèbre se ferme bit-exact.** [σ_a,σ_b]=2iε_abcσ_c,
{σ_a,σ_b}=2δ_ab·I, σ_a²=I, tr(σ_a)=0, hermiticité — tout à 0.0 machine.

**T3 — le lift demi-angle est natif.** bateman(φ)²=bateman(2φ) à 2.22e-16 sur
720 pts : le sous-groupe exp(φJ) double-couvre la famille Bateman — même
structure que le revêtement noyau→boucle (M5 : ratio 0.5 bit-exact). Un tour
de boucle (2π) → −I ; deux tours (4π) → +I : le feuillet du noyau est un
spineur, le deck EST sa monodromie.

**T4 — le signe fermionique est le centre.** σ(1)=−1 (M1 C4, ré-witness M5)
est valeur propre du deck et −I est central (0.0) : la signature d'échange
déposée EST l'élément central de la structure SU(2) native.

**T5 — le Casimir sort nativement : le spin du lien vaut UN DEMI.**
(σ_x²+σ_y²+σ_z²)/4 = (3/4)·I bit-exact ⟹ s(s+1)=3/4 ⟹ s=1/2 (racine mpmath
dps40) ; S_z=σ_z/2 a pour spectre {−1/2, +1/2} bit-exact. La VALEUR du spin
n'est plus postulée : elle sort du triple natif.

---

## 2. CONTRÔLES GELÉS (un seul échec ⟹ V4_REFUTE exit 1)

- **C0a antériorité** : mtime(FRONTIERE_M6_SU2_V0.md) < début d'exécution du verif.
- **C1 filiation M1 C3** : R(0)=I à 0.0 (bit-exact exigé) ; |det R(φ)−1| ≤ 1e-15
  sur 720 pts ; |tr R(φ)−2cosφ| ≤ 1e-15 (0.0 mesuré) ; |R†R−I| ≤ 1e-15.
- **C2 générateurs natifs** : écart(J numérique, J analytique) ≤ 1e-10 (1.67e-11
  mesuré) ; S²−I = 0.0, J²+I = 0.0, P²−I = 0.0 bit-exacts ; tr(S)=tr(J)=tr(P)=0.0
  bit-exacts ; P == diag(1,−1) bit-exact.
- **C3 algèbre Pauli (fermeture bit-exacte)** : hermiticité max ≤ 1e-15 (0.0) ;
  H_a²−I ≤ 1e-15 (0.0) ; les trois relations [ , ]−2iε· ≤ 1e-15 (0.0) ;
  {H_a,H_a}−2I ≤ 1e-15 (0.0) ; {H_a,H_b} a≠b ≤ 1e-15 (0.0) ; |tr| ≤ 1e-15 (0.0).
- **C4 lift demi-angle** : |bateman(φ)²−bateman(2φ)| ≤ 1e-15 sur 720 pts
  (2.22e-16) ; |bateman(π)+I| ≤ 1e-15 (1.22e-16) ; |bateman(2π)−I| ≤ 1e-15
  (2.45e-16) ; centralité de −I = 0.0 bit-exacte.
- **C5 appartenance SU(2)** : |U†U−I| ≤ 1e-15 (2.22e-16) ; |det U−1| ≤ 1e-15
  (2.22e-16) ; |U(0.7)†−U(−0.7)| ≤ 1e-15 (0.0) ; fermeture {±U(φ)} ≤ 1e-15
  (1.67e-16).
- **C6 Casimir** : |(H1²+H2²+H3²)/4 − (3/4)I| ≤ 1e-15 (**0.0 bit-exact**) ;
  racine de s(s+1)=3/4 == 0.5 (mpmath dps40) ; eig(S_z) == {−1/2, +1/2} à
  ≤ 1e-15 (**0.0**).
- **C7 cohérence M5 + consignation** : fibre α=1 bit-exacte (|λ(r)−(±i·r)| = 0.0
  exigé) sur RS ; fibres à 2 valeurs == **5/5** (condition gelée post-correction :
  |λ(r)+λ(−r)| ≤ 1e-15 ET |λ(r)−λ(−r)| ≥ 1.0) ; |σ(1)+1| ≤ 1e-15 (1.22e-16) ;
  eig(S) == {−1,+1} à ≤ 1e-15 (0.0). La consignation M (SO(3) non construite,
  g=2 hors portée, j non dérivé, sl(2,R) vs su(2)) est partiellement témoinnée
  par C5 (un seul axe continu testé) et consignée ici avant gel.

---

## 3. CONSÉQUENCES GELÉES

- **D1 — le spin du lien vaut un demi, fermé par machine.** Casimir
  (1/4)Σσ² = (3/4)·I (0.0 bit-exact) ⟹ s(s+1)=3/4 ⟹ s=1/2 (racine mpmath) ;
  spectre de S_z = {−1/2, +1/2} (0.0). La valeur 1/2 n'est plus postulée (M1) :
  elle sort du triple natif — et elle EST le ratio demi-angle 0.5 de M5 C4.
- **D2 — la signature d'échange EST le centre.** eig(S)={−1,+1}, σ(1)=−1
  (M5), −I central, U(π)=−I : le signe qui exclut (M5 C6, ‖Ψ_exclu‖=3.33e-17)
  est l'élément central de la structure SU(2) native. Z₂ du revêtement = centre
  de SU(2).
- **D3 — [MAPPING] dimension.** L'espace du triple natif est de dimension 2 —
  la dimension de fibre de M5 D1 (5/5 ré-witness S6). La capacité 2(2l+1)
  garde son facteur 2 = dimension de fibre ; (2l+1) reste NON dérivé (consigné,
  pas sauvé). Table [2,6,10,14,18,22,26] inchangée.

---

## 4. ÉCHELLE DE VERDICT (gelée)

- **V+ M6_SU2_NATIVE_PAULI_FERME** : C0a–C7 tous OK ET D1 ET D2 ET D3 OK.
- **V2** : C0a–C7 OK mais au moins une conséquence en échec.
- **V3** : tous les contrôles sauf C0a OK (antériorité seule défaillante).
- **V4_REFUTE exit 1** : tout autre cas. Un seul échec ⟹ sortie immédiate,
  aucun sauvetage, aucune re-normalisation, aucun ajustement.

---

## 5. HONNÊTETÉ ET PORTÉE (gelées)

1. **SO(3) n'est pas construite** : un seul axe à un paramètre est natif
   (exp(φJ), famille Bateman). Les axes σ_x, σ_z viennent du deck (produits),
   pas d'une dérivation géométrique de la rotation d'espace. SU(2) comme
   GROUPE complet n'est pas construite — le sous-groupe {±U(φ)} et
   l'ALGÈBRE su(2) sont natifs.
2. **g=2 hors portée** : aucun couplage électromagnétique dans les dépôts.
3. **j (spin-orbite) non dérivé** : le rang 4 nucléaire de M4 (a73c116) reste
   consigné.
4. **sl(2,R) vs su(2)** : la forme réelle {S,J,P} est split (sl(2,R)) ; la
   fermeture hermitienne {S, −iJ, P}=su(2) passe par le i du noyau. Le
   compactage est porté par la machinerie déposée, pas démontré comme unique.
5. **ħ=1** partout (convention déposée M1). Pas de L_i orbital, pas de
   couplage [L,S].
6. **(2l+1) non dérivé** : M6 ne ferme ni la dégénérescence des modes de
   boucle, ni la capacité totale — uniquement la valeur s=1/2 et l'algèbre.
7. Défauts estimateurs corrigés avant gel (§0.1–0.2), consignés.

**Chaîne de filiation** : M1 Pauli/échange (d0f714a) → M2 potentiel mémoire
(b249526) → M3 remplissage (a1048a1) → M4 nombres magiques (a73c116) → M5
spin demi-angle (963693c/f970108) → M6 SU(2) native (ce dépôt, frontière gelée
avant verif — C0a).
