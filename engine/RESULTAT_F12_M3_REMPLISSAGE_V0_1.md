# RÉSULTAT F12 — MORT 3 : LE REMPLISSAGE — V0.1

**Date : 2026-09-03. Verdict machine : `V+_M3_REMPLISSAGE_THEOREME_DU_CHAMP` — exit 0.**

Exécution de `verif_f12_m3_remplissage_v0_1.py` sur la frontière gelée
`FRONTIERE_F12_M3_REMPLISSAGE_V0_1.md` (commit **0ae4a58**, dépôt-d'abord — C0a OK :
frontière 19:22:07 < exécution 19:24:05). Sortie :
`resultat_f12_m3_remplissage_v0_1.json` (152.5 s, graine 1234, grille gelée
identique V0 : N=800, r∈[1e-4,400] log, L_MAX=2, N_KEEP=10, IT_FREEZE=60,
MAX_ITER=400, MIX=0.3).

**Précédent : V0 exécutée et REFUTÉE (`V4_REFUTE` exit 1, commit 508ab5c — registre
intouché). V0.1 change le protocole, pas la thèse (précédent M2) : unique
changement = estimateur du témoin C4, exécuté sous la convention propre
champs-par-sous-couche (pour He, un seul sous-shell doublement occupé, c'est
exactement le Hartree sans auto-interaction ; le défaut n°8 ne s'applique qu'aux
multi-sous-couches). Fenêtre [−2.88, −2.83] BIT-IDENTIQUE à V0 — aucun
relâchement.**

---

## 1. LE VERDICT — V+_M3_REMPLISSAGE_THEOREME_DU_CHAMP, exit 0

**C1–C8 tous passés ET D1 ET D2 ET D3 passées** (échelle gelée §4) :

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 19:22:07 < 19:24:05 |
| C1 solveur Coulomb −1/(2n²) + dégén. l | **OK** | err 4.732e-04 (barre 5e-4) ; dégén. 1.930e-05 (barre 1e-4) |
| C2 normalisation ∫u²dr = 1 | **OK** | 3.33e-15 |
| C3 charge ∫ρ d³r = N_e | **OK** | 1.42e-14 |
| C4 témoin He (convention propre, fenêtre inchangée) | **OK** | **E(He) = −2.853876** ∈ [−2.88, −2.83] ; conv=True, stable=True |
| C5 one-body négatif (7 β × 3 θ) | **OK** | aucun β ne produit [2,10,18] |
| C6 anti-rétro-ingénierie (graine 1234) | **OK** | 0 système sensible ; motifs interdits : aucun |
| C7 convergence (tout Z sauf Z=5) | **OK** | Z=5 conv=False comme consigné d'avance |
| C8 stabilité refill == config | **OK** | aucun Z instable |

| Conséquence | Résultat | Valeur machine |
|---|---|---|
| **D1** configurations == aufbau réel | **OK 20/20** | 1s¹→…→2p¹ (bore)→…→**4s¹ (K)**→**4s² (Ca)** — la règle (n+l,n) n'existe nulle part dans la route |
| **D2** fermetures == {3, 11, 19} | **OK** | ratios 0.172 / 0.253 / 0.289 (< 0.4) ; aucun autre Z sous le seuil |
| **D3** inversion ε(4s)−ε(3d) des deux côtés | **OK** | Δ(10) = +2.17e-06 ; Δ(19) = −8.97e-03 ; Δ(20) = −2.26e-02 |
| **D4** one-body != {2,10,18} | **OK** | 7 β × 3 θ : aucun triplet (Coulomb {2,10,28,46} ; β=4−√5 → [2,4,6,12]) |

Témoins : E(H) un corps = −0.4998135932 (|E+0.5| = 1.864e-04 ≤ 5e-4) ;
E(He) propre = −2.853876 vs Hartree exact sans échange −2.9037 (échange omis —
consigné). [OBS] D5–D7 consignés comme gelés (tension β=4−√5 : s:5, p:3, d:0
liés, E(1s)=−401.3 ; nucléaire hors portée C-P6 ; anomalies hors fenêtre).

## 2. CE QUE M3 ÉTABLIT MAINTENANT

**La mort 3 de F12 est fermée au niveau visé (fenêtre atomique Z ≤ 20)** : la
séquence des couches électroniques — 1s→2s→2p→3s→3p→**4s** (K)→4s² (Ca) — est un
**théorème du champ auto-cohérent** construit uniquement sur :

1. le **lien boucle dérivé** (M2, b249526 : α=1 ⟹ Coulomb −1/r, préfacteur
   c(1)=1/(4π) — tout préfacteur global re-échelle E uniformément : configs et
   ratios de I invariants d'échelle) ;
2. la **capacité 2(2l+1)** de l'exclusion dérivée (M1, d0f714a) ;
3. la **minimisation d'énergie** à chaque pas de SCF.

La règle (n+l, n) de Madelung **n'existe nulle part dans la route machine**
(C6 : inspection de source + permutation des étiquettes, graine 1234, sans effet
bit-près). Elle cesse d'être un postulat importé (MEMOIRE §6.5) : c'est une
**conséquence** — l'ordre de remplissage est le théorème de survie du champ. Le
contrôle négatif C5 établit la nécessité : aucune loi de puissance à un corps ne
produit la séquence (si un β le faisait, le champ serait superflu).

## 3. HONNÊTETÉ (frontière §5 — ce que M3 V0.1 n'établit pas)

1. **V0 reste REFUTÉE au registre** (508ab5c) — son verdict est le sien propre ;
   V0.1 change l'estimateur d'un témoin, déposé avant exécution, fenêtre
   inchangée. Défauts n°9 (code) et n°10 (barre de frontière) consignés.
2. **Échange omis** (Hartree, pas Hartree-Fock) : barres sur ORDRES et RATIOS ;
   I(2) = 0.515 vs 0.904 exact — consigné.
3. Convention brute (auto-interaction incluse) pour tout le balayage Z — les
   énergies absolues du balayage ne sont pas des ancrages (E(H) SCF = −0.243) ;
   l'ancre −0.5 est portée par le témoin à un corps (C1), l'ancre −2.86 par le
   témoin propre (C4).
4. **Z=5** conv=False (consigné d'avance) — config correcte et stable.
5. **Périmètre Z≤20** : les longues périodes (d, f), les anomalies (Cr 3d⁵4s¹,
   Cu 3d¹⁰4s¹), la table nucléaire {2,8,20,28,50,82,126} (D6) et Z>20 ne sont
   pas tranchés ici — C-P6 se tranche par table.
6. Noyau ponctuel, pas d'écran fini — consignés, pas sauvés.

## 4. LA PORTÉE (frontière §6)

F12 est fermée au niveau visé : **Pauli (M1, d0f714a), potentiel (M2, b249526),
remplissage (M3, ce dépôt)** — la structure de la matière émerge des trois morts
sans postulat combinatoire importé dans la fenêtre atomique Z≤20. La table
nucléaire reste la cible suivante — son échec éventuel sera consigné par table
conformément à C-P6.

> **Le tableau périodique atomique Z≤20 sort du champ des paires du lien :
> la machine l'a tranché — barres gelées, témoin cohérent, verdict sans
> sauvetage. MORT 3 FERMÉE.**
