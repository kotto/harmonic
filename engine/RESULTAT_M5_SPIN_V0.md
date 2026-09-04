# RÉSULTAT F12 — MORT 5 / LE SPIN : L'OBJET DEMI-ANGLE DU LIEN — V0

**Date : 2026-09-04. Verdict machine : `V+ M5_SPIN_DEMI_ANGLE_FERME` — exit 0.**

Exécution de `verif_m5_spin_v0.py` sur la frontière gelée
`FRONTIERE_M5_SPIN_V0.md` (commit **963693c**, dépôt-d'abord — C0a OK :
frontière 06:55:25 < exécution 07:02:11, écart 6 min 46 s). Sortie :
`resultat_m5_spin_v0.json` (sub-seconde, déterministe, aucune graine,
machinerie verbatim des dépôts : poids mère λ(ω)=(iω)^α branche principale
(D3D db00e3b O2/C10), boucle = multiplication site unique (jamais (iω)^{2α}),
Bateman R(θ) (M1 C3), σ(α)=e^{iπα} quadruple route (M1 C4), zéro |1+σ|
balayage 720 (M1 C2), tension |1+σ|² (M1 C5) ; grille gelée identique aux
sondes : N=512, L=20π, D_OMEGA=0.1, W0=1.0, GRID=720,
RS=[0.5, 1.0, 2.0, 3.0, 25.6], mp.dps=40).

**Objet M5 : le facteur 2 de la capacité 2(2l+1) (postulé M1 d0f714a) et la
signature fermionique.** Thèse gelée : le spin est l'objet demi-angle du lien —
le poids mère λ(ω)=(iω)^α est un revêtement DOUBLE de la boucle
λ_loop=λ² via l'application carrée z↦z², de deck z↦−z ; à α=1 la fibre est
{+i|ω|, −i|ω|} (Z₂ pur, rapport −1 = signe fermionique) ;
arg(boucle)=2·arg(noyau) bit-exact ; le revêtement double n'est une base bien
définie QU'À α=1.

---

## 1. LE VERDICT — V+ M5_SPIN_DEMI_ANGLE_FERME, exit 0

**C0a–C7 tous passés ET D1 ET D2 ET D3 passées** :

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 06:55:25 < 07:02:11 |
| C1 filiation C10 : forme close −ω² + boucle aveugle au signe | **OK** | forme close 8.025845262892095e-14 ; aveugle 1.5926531622911327e-13 (barre 1e-12) |
| C2 fibre du carré z↦z² à α=1 sur RS | **OK** | \|λ(−r)+λ(r)\| max 3.1350958058172244e-15 (barre 1e-14) ; \|λ(−r)²−λ(r)²\| max 1.605169052578419e-13 (barre 1e-12) ; rapport = −1+1.22e-16 (barre 1e-15) |
| C3 coïncidence Bateman + quadruple σ | **OK** | eig(R(θ))==phase de feuillet **0.00e+00** ; σ (θ doublé, Bateman², directe, mpmath dps40) 2.29e-16 (barre 1e-15) |
| C4 demi-angle aux DEUX α | **OK** | \|arg(boucle)−2·arg(noyau)\| = 0.0 (α=1) et 0.0 (α=1/φ) ; 2θ−πα = **0.0 bit-exact** ; ratio de traversée = **0.5 bit-exact** |
| C5 contraste α=1/φ (doit tenir) | **OK** | \|LG(w)−LG(−w)\| max **102.1034208285483** (> 1) ; à \|ω\|=1 : 1.8640648476264556 vs fermé 2·sin(πα)=1.8640648476264554 (écart < 1e-15) ; \|σ²−1\|=1.864065 (>1) ; \|σ²+1\|=0.724750 (>0.5) ; tension \|1+σ(1/φ)\|²=1.2752502198390399 (>1) |
| C6 zéro d'interférence et secteurs | **OK** | balayage 720 : argmin=γ[360]=π, val 1.2246467991473532e-16, **1 seul zéro** ; σ(1)=−1 (1.22e-16) ; σ(1)²=+1 (2.45e-16) ; tension α=1 = **0.0 bit-exact** ; ‖Ψ_exclu‖=3.328925487086585e-17 ; ‖Ψ_boson‖=1.4142135623730951 (√2) |
| C7 consignation route morte (monodromie) | **OK** | \|e^{2πi}−1\|=2.45e-16 (trivial à α=1) ; \|e^{2πi/φ}+1\|=0.724750 (non spinoriel à α=1/φ) ; \|1/2−1/φ\|=0.11803398874989479 (α=1/2 hors points déposés) |

| Conséquence | Résultat | Valeur machine |
|---|---|---|
| **D1** fibres à 2 valeurs (facteur 2 = dimension de fibre) | **OK** | **10/10** (5/5 aux deux α) |
| **D2** le rapport d'échange déposé EST le deck | **OK** | deck(α=1) = **−1+1.22e-16j** (Z₂ fermionique) ; deck(1/φ) = σ(1/φ) = (−0.362374890080479905574151189285 + 0.932032423813227706155259966181j) (hors Z₂, braisage ouvert consigné) |
| **D3** [MAPPING] 2(2l+1), l=0..6 | **OK** | **[2, 6, 10, 14, 18, 22, 26]** — le facteur 2 vient de la dimension de fibre (D1, machine) ; (2l+1) NON dérivé, consigné |

Un seul contrôle en échec aurait déclenché `V4_REFUTE` exit 1 sans sauvetage —
précédent Oyibo V0 (f2a2953). Aucun.

## 2. CE QUE M5 ÉTABLIT MAINTENANT

**Le spin, dans ce dépôt, est l'objet demi-angle du lien — et c'est machine :**

1. **Le poids mère est un revêtement double de la boucle.** λ(ω)=(iω)^α,
   bouclé par multiplication site unique (C10), donne λ_loop=λ² :
   l'application z↦z² identifie les deux feuillets z et −z. La fibre du carré
   à α=1 est exactement {+i|ω|, −i|ω|} (C2 : somme nulle à 3.14e-15,
   carrés égaux à 1.61e-13, rapport −1 à 1.22e-16) — une fibre à DEUX valeurs
   (D1 : 10/10).

2. **La signature fermionique est le deck.** Le rapport d'échange déposé (M1
   d0f714a, σ(α)=e^{iπα}) est le deck z↦−z du revêtement (D2) : à α=1,
   σ(1)=−1 à 1.22e-16 — le signe qui annule l'amplitude d'échange, et qui
   rend Ψ_exclu nul (‖Ψ_exclu‖=3.33e-17, C6) tout en laissant Ψ_boson=√2
   exactement. σ(1)²=+1 à 2.45e-16 : le Z₂ est fermé. Le zéro d'interférence
   |1+σ| tombe au point unique γ=π du balayage 720 (val 1.22e-16, un seul
   zéro) et la tension |1+σ|²=2+2cos(πα) vaut **0.0 bit-exact à α=1**.

3. **Le demi-angle est bit-exact.** arg(boucle)=2·arg(noyau) aux DEUX α à
   0.0 (C4), 2θ−πα=0.0 bit-exact (C0b M1 verbatim), ratio de traversée 0.5
   bit-exact : la boucle tourne deux fois plus vite que le noyau — le noyau
   est la racine carrée de la boucle, c'est l'objet demi-angle.

4. **La base bien définie n'existe QU'À α=1 — mesuré, consigné (S0c/C5).**
   À α=1, la boucle est aveugle au signe (LG1(w)==LG1(−w) à 1.59e-13, C1) :
   le revêtement double est une base bien définie. À α=1/φ, la boucle
   DISTINGUE les feuillets : |LG(w)−LG(−w)| max 102.1034208285483, et à
   |ω|=1 l'écart vaut 2·sin(πα)=1.8640648476264556 (fermé 1.8640648476264554,
   écart < 1e-15) — le deck n'y est plus un automorphisme de la base
   (σ²(1/φ)=(−0.362374890080479905574151189285, 0.932032423813227706155259966181),
   ni +1 ni −1 : braisage ouvert, tension 1.2752502198390399). Le spin comme
   Z₂ bien défini EST la limite α=1 du lien.

5. **Le facteur 2 de la capacité est une dimension de fibre.** 2(2l+1)
   décomposé : le facteur 2 est la dimension de la fibre du revêtement (D1,
   machine 10/10), la table [2, 6, 10, 14, 18, 22, 26] sort verbatim (D3).
   La dégénérescence (2l+1) des modes de boucle reste NON dérivée — consignée,
   pas sauvée.

6. **Route monodromie MORTE, consignée avant gel (C7).** La voie
   e^{2πiα}=−1 (spinorité par monodromie du revêtement) est fermée sur les
   points déposés : e^{2πi}=1 trivial à α=1 (2.45e-16) ; e^{2πi/φ}+1=0.724750
   non spinoriel à α=1/φ ; e^{2πiα}=−1 ⟺ α=1/2, hors des points déposés
   (|1/2−1/φ|=0.11803398874989479 > 0.1). La signature fermionique ne vient
   PAS d'une monodromie de phase : elle vient du deck du revêtement carré.

## 3. HONNÊTETÉ (frontière §5 — ce que M5 V0 n'établit pas)

1. **(2l+1) n'est pas dérivé** : la dégénérescence des modes de boucle reste
   postulée (M1) ; M5 ne ferme que le facteur 2, par la dimension de fibre.
2. **Pas de SU(2), pas de matrices de Dirac, pas de g=2** : M5 établit la
   structure de revêtement double et le signe Z₂ dans la machinerie déposée
   (λ, Bateman, σ) — aucune algèbre de spin importée.
3. **Le braisage ouvert à α=1/φ est consigné, pas résolu** : σ²(1/φ) n'est ni
   +1 ni −1 (tension 1.2752502198390399) — c'est une prédiction falsifiable
   du dépôt, pas un défaut numérique.
4. **Le spin-orbite j reste non dérivé** : le rang 4 nucléaire consigné en M4
   (a73c116) n'est pas affecté par M5.
5. **Route monodromie morte ≠ route unique fermée** : C7 consigne qu'une voie
   de dérivation est fermée sur les points déposés ; consignation avant gel,
   jamais un ajustement a posteriori.
6. **Défaut estimateur corrigé avant gel** : les sondes affichaient les sauts
   et angles au bord du wrap (−π vs +π) ; corrigé avant le commit 963693c,
   consigné en §0 de la frontière.

## 4. LA PORTÉE (frontière §4)

M5 ferme la cinquième mort de la chaîne : **le facteur 2 du spin est désormais
un objet machine** — dimension de fibre du revêtement carré noyau→boucle
(D1 10/10), deck = rapport d'échange déposé (D2, −1 exactement à α=1),
demi-angle bit-exact (C4), base bien définie seulement à α=1 (C5, S0c),
route monodromie morte consignée (C7). La chaîne F12 tient : Pauli (M1,
d0f714a), potentiel (M2, b249526), remplissage (M3, a1048a1), nombres
magiques (M4, a73c116), **spin-demi-angle (M5, ce dépôt)**. Toute extension
(dérivation de (2l+1), algèbre SU(2) native, g=2) devra sortir du même
protocole : dépôt-d'abord, barres gelées, verdict sans sauvetage.

> **Le spin n'a pas été importé dans le dépôt : il en sort — la racine carrée
> du lien porte le signe d'échange, la boucle tourne deux fois plus vite, et
> le facteur 2 de 2(2l+1) est la dimension de la fibre. MORT 5 FERMÉE.**
