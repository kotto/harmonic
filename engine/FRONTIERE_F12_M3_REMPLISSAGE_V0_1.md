# FRONTIÈRE F12 — MORT 3 : LE REMPLISSAGE — V0.1

**Date : 2026-09-03 — dépôt-d'abord : ce document est gelé AVANT tout script de vérification V0.1 (C0a).**
**Statut : V0 exécutée et REFUTÉE (verdict machine `V4_REFUTE` exit 1, commit 508ab5c — registre intouché). V0.1 change le PROTOCOLE, pas la thèse.**

---

## 0. CE QUE V0 A ÉTABLI (registre, commit 508ab5c)

Exécution de `verif_f12_m3_remplissage_v0.py` sur la frontière 71d92e4. Résultats
machine (154 s, graine 1234, grille gelée) :

- **C0a, C1, C2, C3, C5, C6, C7, C8 : tous passés** (C1 err 4.732e-04 ≤ 5e-4 ;
  C5 aucun β × θ ne produit [2,10,18] ; C6 permutation graine 1234 sans effet et
  motifs interdits absents ; Z=5 conv=False comme consigné d'avance).
- **D1 passée — 20/20 configurations fondamentales == aufbau réel** (y compris
  2p¹ bore, 4s¹ K, 4s² Ca) **sans règle de Madelung dans la route**.
- **D2 passée — fermetures == {3, 11, 19}** (ratios 0.172 / 0.253 / 0.289 ;
  aucun autre Z < 0.4).
- **D3 passée — inversion ε(4s)−ε(3d) des deux côtés** (Δ(10)=+2.17e-06,
  Δ(19)=−8.97e-03, Δ(20)=−2.26e-02).
- **C4 en échec — V4_REFUTE exit 1, sans sauvetage** : E(He) = −1.9421 hors de la
  fenêtre gelée [−2.88, −2.83].
- Défauts estimateur consignés : **n°9** (clé d'affichage `'config'`, deux runs
  avortés avant le run de verdict, corrigé — code) et **n°10** (barre C4 — frontière).

**Le diagnostic n°10, quantifié machine** : la fenêtre gelée [−2.88, −2.83] est le
témoin Hartree **sans auto-interaction** — la valeur produite par la convention
« champs par sous-couche » que la V0 §5.2 **rejetait elle-même** (défaut n°8).
Sous la convention brute mandatée, E(He) = −1.9421 ; la correction J mesurée sur
grille (J = 0.791169) donne E−J = −2.7333, encore hors fenêtre : la convention
brute délocalise l'orbitale auto-cohérente elle-même. La fenêtre est inaccessible
par toute correction à posteriori — la barre était inconsistante avec la
convention mandatée (§5.1 de V0 interdisait pourtant les barres d'énergie absolue).

## 0.1 CE QUE V0.1 CHANGE (et ce qu'elle ne change pas)

**Change — uniquement l'estimateur du témoin C4** : le témoin He à deux corps est
exécuté sous la convention **champs par sous-couche** (chaque électron voit
V_i = V_n + V_H[ρ_tot] − V_H[ρ_sous-couche]) — c'est, pour UN SEUL sous-shell
doublement occupé, exactement le Hartree propre (chaque électron voit l'autre,
pas lui-même). Justification déposée : le défaut n°8 (non variationnel,
sur-correction I(Z)<0) concerne les systèmes **multi-sous-couches** (Z≥6) — il ne
s'applique pas au témoin He, qui n'a qu'un sous-shell. La fenêtre **[−2.88, −2.83]
reste bit-identique** à V0 ; conv=True et stable=True exigés comme en V0.

**Ne change pas** : la thèse (§1), les barres C1-C3/C5-C8 (§2), les conséquences
D1–D7 (§3), l'échelle de verdict (§4), la grille gelée (§2), la convention brute
mandatée pour tout le balayage Z (le témoin He est le SEUL objet exécuté sous la
convention par sous-couche). Aucun relâchement : la barre C4 garde sa valeur V0.

---

## 1. LES QUESTIONS FALSIFIABLES (inchangées — V0 §1)

- **T1** : la configuration fondamentale de tout Z ∈ [1,20] émerge du triplet
  {lien boucle α=1 = Coulomb −1/r (déposé b249526), capacité 2(2l+1) de M1
  (d0f714a), minimisation d'énergie à chaque pas de SCF} — sans règle de Madelung
  importée.
- **T2** : fermeture ⟺ I(Z)/I(Z−1) < 0.4 ; cible {3, 11, 19} exactement.
- **T3** : ε(4s)−ε(3d) < 0 à Z=19,20 et > 0 à Z=10 — les deux côtés émergent.
- **T4** (négatif, doit tenir) : aucun β du balayage gelé ne reproduit {2,10,18}
  à un corps.
- **T5** (témoin) : E(H)=−0.5 à ≤5e-4 (un corps — C1) ; **E(He) ∈ [−2.88, −2.83]**
  sous la convention propre du témoin (V0.1 — le seul changement de V0).

## 2. CONTRÔLES (gelés — identiques à V0 sauf C4)

| # | Contrôle | Barre gelée |
|---|---|---|
| C0a | antériorité : getmtime(FRONTIERE_F12_M3_REMPLISSAGE_V0_1.md) < début d'exécution | strict |
| C1 | solveur Coulomb α=1 : E_{n,l} = −1/(2n²), n≤6, l≤min(3,n−1) | err rel max ≤ 5e-4 ; dégénérescence-l ≤ 1e-4 |
| C2 | normalisation orbitale ∫u²dr = 1 (tous blocs, tous Z) | écart ≤ 1e-8 |
| C3 | charge intégrée ∫ρ d³r = N_e (tous systèmes) | écart ≤ 1e-6 |
| **C4** | **témoin He sous la convention propre (champs par sous-couche — V0.1 §0)** : E ∈ [−2.88, −2.83] **bit-identique à V0** ; conv=True ; stable=True | conforme |
| C5 | contrôle négatif one-body : couches one-body[:3] ≠ [2,10,18] pour tout β | tous les β |
| C6 | anti-rétro-ingénierie : permutation des étiquettes (n,l) (graine 1234) ne change AUCUNE occupation ; chaînes « n+l »/Madelung/noble/aufbau absentes de la route | invariant bit-près |
| C7 | convergence SCF : conv=True pour tout Z sauf Z=5 (consigné d'avance) | conforme |
| C8 | stabilité du remplissage au point fixe (refill == config) | stable=True tout Z |

**Grille gelée (identique V0)** : N_GRID=800, r∈[1e-4, 400] log, L_MAX=2,
N_KEEP=10, IT_FREEZE=60, MAX_ITER=400, MIX=0.3, Z∈[1,20],
BETA_SWEEP=(1.0, 1.2, 1.4, 3−2/φ, 1.9, 2.2, 2.5), θ=(0.02, 0.05, 0.10),
CLOSURE_RATIO=0.4, graine permutation=1234. Aucun chiffre calculé à la main
(leçon V1.2) — tout est diagonalisé/intégré.

## 3. CONSÉQUENCES (gelées — identiques V0)

| # | Conséquence | Barre gelée |
|---|---|---|
| D1 | configurations Z=1..20 == aufbau réel (route sans lecture de cible) | 20/20 exactes, stable=True |
| D2 | fermetures (ratio < 0.4) == {3, 11, 19} exactement | ensemble égal |
| D3 | ε(4s)−ε(3d) < 0 à Z=19 ET 20 ; > 0 à Z=10 | signes gelés |
| D4 | one-body != {2,10,18} pour tout β | tous |
| D5 | [OBS] tension β=4−√5 one-body consignée | consignation |
| D6 | [OBS] table nucléaire hors portée | consignation (C-P6 par table) |
| D7 | [OBS] anomalies Cr/Cu/lanthanides hors fenêtre | consignation |

## 4. ÉCHELLE DE VERDICT (gelée — identique V0)

- **V+_M3_REMPLISSAGE_THEOREME_DU_CHAMP** : C1–C8 tous passés ET D1 ET D2 ET D3.
- **V2_REMPLISSAGE_PARTIEL** : contrôles OK, D1 OK, D2 ou D3 en échec partiel.
- **V3_REMPLISSAGE_INCOMPLET** : couches détectées mais configurations incorrectes.
- **V4_REFUTE** : un contrôle en échec — un seul ⟹ exit 1, sans sauvetage.

## 5. HONNÊTETÉ (V0.1)

1. **V0 reste REFUTÉE dans le registre** (508ab5c) — V0.1 est un nouveau dépôt,
   pas un correctif rétroactif. Le verdict de V0.1 est le sien propre.
2. **Échange omis** partout (Hartree, pas Hartree-Fock) — barres sur ORDRES et
   RATIOS ; C1 (un corps exact) et C4 (témoin He propre) sont les seules barres
   d'énergie absolue, toutes deux portées par des valeurs exactes/connues.
3. Le témoin C4 sous convention propre est **exactement Hartree** pour He (un
   seul sous-shell) — le défaut n°8 ne s'y applique pas ; il reste prohibé pour
   le balayage Z (où il sur-corrige).
4. **Z=5** conv=False attendu (consigné depuis les sondes, config correcte).
5. Périmètre Z≤20 ; noyau ponctuel ; échange omis — consignés, pas sauvés.
6. Défauts estimateur : registre n°1-10 (n°9 code, n°10 frontière V0) — V0.1
   n'en corrige qu'un : le témoin C4 (n°10). Les autres restent consignés.

## 6. LA PORTÉE

Si V0.1 tient, M3 ferme F12 au niveau visé : l'ordre de remplissage Z≤20 est le
théorème de survie du champ construit sur le seul lien dérivé et l'exclusion
dérivée — avec un témoin à deux corps cohérent avec sa propre convention. Si
V0.1 meurt, l'échec sera localisé (témoin, champ, ou fermetures) et consigné
sans sauvetage. La table nucléaire reste la cible suivante (C-P6 par table).

> **V0 a tranché : la thèse passe, le témoin était cassé. V0.1 regèle le témoin
> dans la convention qui lui convient — dépôt-d'abord, barres inchangées, la
> machine re-tranche.**
