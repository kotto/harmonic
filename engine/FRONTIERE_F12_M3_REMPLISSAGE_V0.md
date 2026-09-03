# FRONTIÈRE F12 — MORT 3 : LE REMPLISSAGE — V0

**Date : 2026-09-03 — dépôt-d'abord : ce document est gelé AVANT tout script de vérification (C0a).**
**Statut sondes : closes. 8 défauts estimateur consignés (§7). Le script verif n'existe pas encore.**

---

## 0. OÙ ON EN EST (héritage et sondes)

F12 a trois morts. M1 Pauli est FERMÉE (d0f714a : σ(α)=e^{iπα}, signe fermionique −1 recouvré à α=1, zéro unique de la famille (1+σ)). M2 le potentiel est FERMIÉE (b249526 : V ∝ r^{2α−3}, r⁻¹ recouvré à α=1, préfacteur c(1)=1/(4π), exposant √5−4 à α=1/φ). M3 le remplissage est OUVERTE — c'est la cible de cette frontière. Honnêteté d'entrée : dans MEMOIRE §6.5, Madelung est aujourd'hui **implémenté, pas dérivé** — le tableau sort d'un ordre (n+l, n) importé. EXPLORATION_TABLEAU_PERIODIQUE le confirme (118/118 périodes générées, mais l'ordre est un postulat structurel).

**Sondes M3 (pré-gel, 3 vagues, 8 défauts estimateur consignés — n°1 FD parasite, n°2 métrique Bessel r²dr, n°3 terme cinétique manquant, n°4 scipy eigh_tridiagonal select='i' corrompu, n°5-6 étiquetage bloc l, n°7 mesure J_i, n°8 sur-correction sans auto-interaction) :**

1. **La route « potentiel central seul » est MORTE — fait structural.** Solveur log symétrisé validé sur Coulomb (err 4.5e-5, dégénérescence-l 2e-6). Balayage β ∈ {1.0, 1.2, 1.4, 1.7639(=4−√5), 1.9, 2.2, 2.5}, cinétique standard ET p^{2/φ} : **aucun** β ne donne la séquence des gaz nobles {2,10,18,36,54,86} par trous d'énergie one-body (max 2/7, jamais le triplet). Coulomb nu donne les couches 2n² {2,10,28,60,…} — l'échec connu dès Z=18. À β=4−√5 le spectre lié s'effondre (s seuls profondément liés, E(1s)≈−819, p/d/f non liés ou au bord) — pas de table possible. Le lien boucle M2 est un lien **entre deux charges** ; l'atome n'est pas un problème à un corps.
2. **La route « champ auto-cohérent du lien » est VIVANTE.** Lien universel appliqué paire à paire (Hartree sphérique, échange omis — consigné) + capacité 2(2l+1) (M1 fermée) + remplissage = minimisation d'énergie : les configurations Z=1..20 sortent **toutes correctes** (1s→2s→2p→3s→3p→**4s**, y compris 2p¹ au bore, 4s¹ au potassium, 4s² au calcium), les fermetures émergent comme chutes massives de I(Z) (facteur 3.5–6) à Z=3, 11, 19, et l'inversion ε(4s)<ε(3d) à Z=19-20 **émerge du champ** (elle se retourne à Z≤10 comme dans les atomes réels). Témoins : E(H)≈−0.5 (convention sans auto-interaction), E(He) Hartree = −2.8539 (exact −2.9037, échange omis).

**La thèse n'est PAS « Madelung est vrai »** — c'est : la séquence des couches est un **théorème du champ auto-cohérent construit uniquement sur le lien dérivé M2 et l'exclusion dérivée M1**. La règle (n+l, n) n'existe nulle part dans la route machine.

---

## 1. LES QUESTIONS FALSIFIABLES

- **T1** : le remplissage (config électronique fondamentale) de tout Z ∈ [1,20] émerge du triplet {lien boucle α=1 = Coulomb −1/r (déposé b249526, préfacteur c(1)=1/(4π) — tout préfacteur global re-échelle E uniformément : configs et ratios de I sont invariants d'échelle), capacité 2(2l+1) de M1, minimisation d'énergie à chaque pas de SCF} — sans règle de Madelung importée.
- **T2** : les couches fermées = chutes de I(Z) = E(Z, Z−1) − E(Z, Z). Fermeture ⟺ I(Z)/I(Z−1) < 0.4. Cible : {3, 11, 19} dans la fenêtre (soit couches fermées à Z = 2, 10, 18 = He, Ne, Ar) et aucun autre Z de la fenêtre sous le seuil.
- **T3** : l'inversion ε(4s)<ε(3d) à Z=19, 20 (qui fonde K, Ca et la première longue période) émerge du champ ; à Z≤10 le signe est inverse (ε(3d)<ε(4s)) — le champ donne les DEUX côtés, comme les atomes réels.
- **T4** (contrôle négatif, doit tenir) : la route one-body est morte — pour tout β de la grille gelée, les couches détectées par trous d'énergie sur le spectre à un corps ne reproduisent JAMAIS le triplet {2,10,18}. Si un β le fait, T1 s'effondre (le champ serait superflu).
- **T5** (témoin) : la machinerie reproduit la physique à un corps : E(H)=−0.5 à ≤5e-4 (un électron : pas de paire, champ nul), E(He) ∈ [−2.88, −2.83] (Hartree sans échange).

---

## 2. CONTRÔLES (gelés)

| # | Contrôle | Barre gelée |
|---|---|---|
| C0a | antériorité : getmtime(FRONTIERE_F12_M3_REMPLISSAGE_V0.md) < début d'exécution | strict |
| C1 | solveur Coulomb α=1 : E_{n,l} = −1/(2n²), n≤6, l≤min(3,n−1) | err rel max ≤ 5e-4 ; dégénérescence-l ≤ 1e-4 |
| C2 | normalisation orbitale ∫u²dr = 1 (tous blocs, tous Z) | écart ≤ 1e-8 |
| C3 | charge intégrée ∫ρ d³r = N_e (tous systèmes) | écart ≤ 1e-6 |
| C4 | témoin He (Hartree, échange omis) | E(He) ∈ [−2.88, −2.83] ; conv=True ; stable=True |
| C5 | contrôle négatif one-body : pour tout β de BETAS, couches one-body[:3] ≠ [2,10,18] | tous les β |
| C6 | anti-rétro-ingénierie : permutation des étiquettes (n,l) des ε (graine 1234) ne change AUCUN nombre d'occupation ; la chaîne « n+l » absente de la route de remplissage | invariant bit-près |
| C7 | convergence SCF : conv=True pour tout Z sauf Z=5 (consigné d'avance depuis les sondes : config correcte et stable malgré conv=False) | conforme |
| C8 | stabilité du remplissage au point fixe (refill == config) | stable=True pour tout Z |

**Grille gelée** : N_GRID=800, r∈[1e-4, 400] log, L_MAX=2, N_KEEP=10, IT_FREEZE=60, MAX_ITER=400, MIX=0.3, Z∈[1,20], BETA_SWEEP=(1.0, 1.2, 1.4, 3−2/φ, 1.9, 2.2, 2.5), θ=(0.02, 0.05, 0.10) pour one-body, CLOSURE_RATIO=0.4, graine permutation=1234. Aucun chiffre calculé à la main (leçon V1.2) — tout est diagonalisé/intégré.

---

## 3. CONSÉQUENCES (gelées)

| # | Conséquence | Barre gelée |
|---|---|---|
| D1 | configurations fondamentales Z=1..20 == aufbau réel (1s ; 1s² ; …2p⁶ ; 3s²3p⁶ ; **4s¹ K ; 4s² Ca**) — la cible est importée (objet falsifié), la route ne la lit JAMAIS | 20/20 exactes, stable=True |
| D2 | fermetures détectées (ratio < 0.4) == {3, 11, 19} exactement dans la fenêtre | ensemble égal |
| D3 | inversion ε(4s)−ε(3d) : < 0 à Z=19 ET Z=20 ; > 0 à Z=10 (les deux côtés émergent) | signes gelés |
| D4 | one-body (contrôle C5 étendu en conséquence) : couches one-body != {2,10,18} pour tout β du balayage gelé | tous |
| D5 | [OBS] tension consignée : à α=1/φ (β=4−√5), le spectre one-body n'a que des s profonds (pas de table) — la tranche mémoire ne ferme pas la table au niveau à un corps ; miroir de la tension P15 | consignation, pas sauvetage |
| D6 | [OBS] table nucléaire {2,8,20,28,50,82,126} : hors portée de cette V0 (pas de noyau central dans la voie atomique) — consignée OUVERTE (C-P6 se tranche par table) | consignation |
| D7 | [OBS] anomalies (Cr 3d⁵4s¹, Cu 3d¹⁰4s¹, lanthanides, Z=79) hors fenêtre Z≤20 — non testées ici, échange omis | consignation |

---

## 4. ÉCHELLE DE VERDICT (gelée)

- **V+_M3_REMPLISSAGE_THEOREME_DU_CHAMP** : C1–C8 tous passés ET D1 ET D2 ET D3 passés.
- **V2_REMPLISSAGE_PARTIEL** : contrôles OK, D1 OK, mais D2 ou D3 en échec partiel.
- **V3_REMPLISSAGE_INCOMPLET** : couches détectées mais configurations incorrectes.
- **V4_REFUTE** : un contrôle en échec (C5 compté comme échec si un β reproduit le triplet) — un seul contrôle en échec ⟹ REFUTE exit 1, sans sauvetage.

---

## 5. HONNÊTETÉ (§5 — ce que V0 n'établit pas)

1. **Échange omis** (Hartree, pas Hartree-Fock) : les valeurs absolues de I(Z) sont biaisées ; I(2)=0.515 vs 0.904 exact. Les barres portent sur des ORDRES et des RATIOS, jamais des énergies absolues — seuls C1/C5 portent des valeurs exactes connues.
2. **Auto-interaction** : la convention brute inclut la répulsion de chaque électron avec lui-même (E(H)=−0.243 au lieu de −0.5 ; l'ancre exacte −0.5 est portée par le témoin à un corps). La tentative sans auto-interaction (champs par sous-couche) est NON variationnelle et sur-corrige (I(Z)<0 à Z=6-10) — rejetée et consignée (défaut n°8).
3. **Z=5** ne converge pas (conv=False) à IT_FREEZE=60 — consigné d'AVANT le gel ; sa config est correcte et stable. La barre C7 le prévoit explicitement — l'échec de Z=5 n'est pas un sauvetage, il est l'objet d'une consignation.
4. **Périmètre** : fenêtre Z≤20. Les longues périodes (d, f), les anomalies (D7), la table nucléaire (D6) et le Z>20 ne sont pas tranchés ici.
5. **Écran** : pas d'écran nucléaire fini (noyau ponctuel) ; l'échange électron-électron est omis — ces omissions sont consignées, pas sauvées.
6. Le remplissage machine = minimisation des ε (potentiel commun) à chaque pas, occupations gelées après IT_FREEZE (anti-clignotement quasi-dégénéré) et stabilité testée au point fixe — la règle (n+l, n) et les listes de gaz nobles ne vivent QUE dans les cibles de falsification, jamais dans la route.

---

## 6. LA PORTÉE

Si M3 tient, la mort 3 ferme F12 au niveau visé : le tableau périodique (fenêtre atomique Z≤20) cesse d'être la conséquence d'un postulat combinatoire — l'ordre de remplissage est le **théorème de survie du champ** construit sur le seul lien dérivé et l'exclusion dérivée. Si M3 meurt, l'échec sera localisé (solveur, champ, ou fermetures) et consigné sans sauvetage. La table nucléaire reste la cible suivante — et son échec éventuel sera consigné par table conformément à C-P6.

> **F12 attaque la dernière mort : la structure. Pauli est fermée, le potentiel est fermé — reste le remplissage. La frontière dit : si les couches ne sortent pas du champ des paires du lien, la dérivation de la matière est incomplète — et chaque écart sera chiffré. Les sondes ont tué la route à un corps (aucun β ne donne la séquence) et montré le champ vivant (20/20 configurations, fermetures à facteur 3.5–6, inversion 4s/3d des deux côtés). La V0 tranche machine : barres gelées, verdict sans sauvetage.**