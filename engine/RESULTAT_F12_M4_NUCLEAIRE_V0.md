# RÉSULTAT F12 — MORT 4 / CIBLE NUCLÉAIRE : LES NOMBRES MAGIQUES — V0

**Date : 2026-09-03. Verdict machine : `V+_M4_NUCLEAIRE_TRANCHES_CONSIGNÉES` — exit 0.**

Exécution de `verif_f12_m4_nucleaire_v0.py` sur la frontière gelée
`FRONTIERE_F12_M4_NUCLEAIRE_V0.md` (commit **8a27c74**, dépôt-d'abord — C0a OK :
frontière 20:26:22 < exécution 20:44:15, écart 17 min 53 s). Sortie :
`resultat_f12_m4_nucleaire_v0.json` (**5.4 s**, déterministe, aucune graine,
grille gelée identique aux sondes : N=800, r∈[1e-4,400] log, L_MAX=6, N_MAX=14,
N_KEEP=16, BETAS=(20,50,100,200,400), MUS=(0.5, 1.0, 1/φ, 3.0),
THETAS=(0.02, 0.05, 0.10), POW_BETAS=(1.0, 1.2, 1.4, 4−√5, 1.9, 2.2, 2.5)).

**Critère maître F12 C-P6 : « les deux tables de nombres magiques sortent du
même couple, ou l'échec est consigné par table ».** Table atomique : fermée M3
V+ (a1048a1). Table nucléaire {2, 8, 20, 28, 50, 82, 126} : **tranchée par
consignation** — la tranche [2, 8, 20] sort du même couple (49 réalisations),
le rang 4 (28) ne sort jamais, et cet échec est consigné machine, pas sauvé.

---

## 1. LE VERDICT — V+_M4_NUCLEAIRE_TRANCHES_CONSIGNÉES, exit 0

**C0a–C8 tous passés ET D1 ET D2 ET D4 passées** (D3 et D5 en [OBS]) :

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 20:26:22 < 20:44:15 |
| C1 solveur Coulomb −1/(2n²) + dégén. l | **OK** | err 4.787e-04 (barre 5e-4) ; dégén. 1.930e-05 (barre 1e-4) |
| C2 normalisation u = v/√(r·dτ) | **OK** | ∫u²dr = 1.0000000000000002 (écart 2.2e-16, barre 1e-8) |
| C3 livre de la grille gelée | **OK** | 74/80 paires exécutées = **222 configs θ** ; 6 skips exacts ; POW **21/21** |
| C4 anti-rétro-ingénierie | **OK** | fermetures bit-identiques ×3 ; motifs interdits **[]** ; N_T1(cible perturbée)=0 |
| C5 Coulomb ≠ nucléaire | **OK** | [2, **10**, 28, 60, 110, 182, 280] — 2e fermeture 10 ≠ 8 |
| C6 témoin sous-couches (12 niveaux) | **OK** | écart max 4.468e-04 (barre 1e-3), 12/12 bit-exacts |
| C7 barycentre e⁻ vs 2e⁻ | **OK** | double=Faux → [1,4,5,8,13,14] ; double=Vrai → [2,8,10,16,26,28] |
| C8 témoin e^{−μr} re-exécuté | **OK** | bit-identique aux sondes ; n_lie=38, 12 sous-couches |

| Conséquence | Résultat | Valeur machine |
|---|---|---|
| **D1** la tranche [2,8,20] sort du couple | **OK** | **N_T1 = 49** (grille gelée) + témoin ∈ T1 ; meilleur : EXP β=20 μ=0.5 θ=0.1 → [2, 8, 20, 26, 52, 76, 124, 148] |
| **D2** le rang 4 ne sort jamais | **OK** | **N_28 = 0 sur 222 configs** ET **N_28_POW = 0 sur 21** |
| D3 [OBS] 28 quelque part, jamais rang 4 | **OK [OBS]** | 77 configs contiennent 28 (jamais en 4e position) |
| **D4** trois régimes, trois séquences déposées | **OK** | Coulomb [2,10,28,60,110,182,280] ; YUKPHI [2,8,18,32,50,52,58,68] ; GAUSS [2,8,20,40,70,112,168,210] |
| D5 [OBS] μ=φ exactement (hors grille) | **OK [OBS]** | EXP β=50 μ=φ → [2, 8, 10, 20, 26, **28**, 42, 52] aux θ=0.02/0.05 — 28 en 6e position, pas en 4e |

Un seul contrôle en échec aurait déclenché `V4_REFUTE` exit 1 sans sauvetage —
précédent M3 (508ab5c). Aucun.

## 2. CE QUE M4 ÉTABLIT MAINTENANT

**C-P6 est satisfaite pour les DEUX tables.** La table atomique est un théorème
(M3) ; la table nucléaire est tranchée en deux volets machine :

1. **Volet positif — la tranche [2, 8, 20] sort du même couple.** La famille
   e^{−μr} — dont la forme réelle du noyau K̂(ω)=φ/((iω)^α+φ) à α=1 est le
   membre μ=φ — fait tomber [2, 8, 20] **sans ajustement** sur une large région
   de portées : 49 configurations de la grille gelée (BETAS × MUS × THETAS),
   témoin déposé EXP β=20 μ=0.5 θ=0.1 → [2, 8, 20, 26, 52, 76, 124, 148]
   (n_lie=38, 12 sous-couches bit-exactes C8). Le même couple (Pauli M1
   d0f714a + noyau mémoire M2 b249526) produit les deux premières tranches des
   DEUX tables : [2, 8, 20] atomique ET nucléaire.

2. **Volet négatif consigné — le rang 4 (28) ne sort pas, et c'est mesuré.**
   Sur 222 configs θ + 21 lois de puissance : **zéro occurrence de 28 en 4e
   position** (D2). Là où 28 apparaît (77 configs, D3 [OBS]), il est déplacé —
   Coulomb : 3e position [2,10,**28**,60] ; μ=φ : 6e position
   [2,8,10,20,26,**28**,42]. La localisation est portée par la chaîne elle-même :
   le seul objet déposé porteur d'une échelle de longueur est le noyau mémoire
   K̂ ; son rang 4 en physique réelle exige le couplage spin-orbite j (1f₇/₂),
   **non dérivé depuis M1** (« le spin n'est pas dérivé », d0f714a). La
   consignation N_28=0 N'EST PAS un échec de protocole : c'est la prédiction
   falsifiable du dépôt — introduire j sans le dériver serait le sauvetage
   exact que F12 interdit.

C4 verrouille le sens : perturber la cible ({28,50,82,126}→autres) et ré-exécuter
×3 donne des fermetures **bit-identiques** et **N_T1=0** — la route ne connaît
pas la cible ; les motifs interdits sont absents de la route machine ([]).

## 3. HONNÊTETÉ (frontière §5 — ce que M4 V0 n'établit pas)

1. **[2, 8, 20] est la tranche harmonique connue** (3n² pour n=1,2 en langage
   standard) : le dépôt ne « découvre » pas la table, il établit qu'elle sort
   du couple sans postulat importé — et que le rang 4 n'en sort pas.
2. **μ=φ exactement ne donne pas [2,8,20]** : [2,8,10,20,26,28,42] (D5 [OBS]).
   La tranche sort des portées plus douces de la MÊME famille (témoin μ=0.5) —
   l'échelle du noyau K̂ n'est pas elle-même scannée dans la grille gelée.
3. **Un seul corps central**, pas de paire α-α ni de structure à deux centres.
4. **Le spin n'est pas dérivé** (M1) : ni spin-orbite j, ni isospin — le rang 4
   nucléaire est consigné hors portée, pas sauvé.
5. **Espèces chimiques non modélisées** : les dénominations (Coulomb, Yukawa…)
   désignent des formes de potentiel, pas des noyaux physiques simulés.
6. **Livre préliminaire corrigé avant dépôt** : la prose de frontière disait
   219 configs / 27 POW ; la machine dit 222 / 21 (74/80 paires, 6 skips) —
   corrigé dans le fichier gelé AVANT le commit 8a27c74, verrouillé par C3.
7. C5 fixe la nécessité du sens du lien : Coulomb (signe e⁻) donne [2,10,28,…]
   dès la 2e fermeture — la table atomique [2,8,10,…] exige le signe dérivé M2.

## 4. LA PORTÉE (frontière §6)

F12 est fermée au niveau visé sur ses quatre morts : **Pauli (M1, d0f714a),
potentiel (M2, b249526), remplissage atomique (M3, a1048a1), nombres magiques
(M4, ce dépôt)**. C-P6 est close : la table atomique est un théorème, la table
nucléaire est tranchée par consignation machine — tranche [2,8,20] du même
couple (N_T1=49), rang 4 absent (N_28=0/222+21), échec localisé au degré
interne j non dérivé. Toute extension (spin-orbite dérivé, noyau à deux
centres, μ physique de K̂) devra sortir du même protocole : dépôt-d'abord,
barres gelées, verdict sans sauvetage.

> **Les deux tables de nombres magiques sont tranchées par le même couple :
> l'atomique sort entière jusqu'à Z=20, la nucléaire rend sa tranche [2,8,20]
> et consigne son échec au rang 4 — la machine l'a tranché, MORT 4 FERMÉE.**
