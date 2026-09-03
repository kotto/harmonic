# INTERACTION D3 V0 — V2 : la forme close de l'interaction est ÉTABLIE (parité consignée hors barre absolue)

**Campagne du 3 septembre 2026 — exécution du dépôt du 28/08 (jamais exécuté, audit du 03/09)**

| | |
|---|---|
| Dépôt | `DEPOT_INTERACTION_D3_V0.md` (gelé, mtime **2026-08-28 17:20:19**, amendement §0-bis inclus) |
| Script | `verif_interaction_d3_v0.py` (écrit le 03/09 après audit d'absence ; bugs d'estimateur corrigés AVANT verdict, consignés §4) |
| Journal | `resultat_interaction_d3_v0.json` (consignation intégrale, exécution 08:55:06) |
| C0a | **OK** — dépôt (28/08 17:20:19) < exécution (03/09 08:55:06), antériorité 5,65 jours |
| Contrôles | **13/13 ✅** |
| **Verdict** | **V2 — INTERACTION_FORME_PARTIELLE — exit 0** (C4 parité hors barre absolue ; échelle §3 gelée appliquée telle quelle) |

> **L'interaction entre canaux de jauge sous connexion commune EST la résonance de Bessel déposée — exacte à la précision machine.** C2 (forme close) et C3 (résonance latérale) sont verifies à ~1e-22, deux ordres au-delà de la barre 1e-9 relative. La discrimination de parité (C4) est RÉELLE — 14 ordres de grandeur entre bonne et mauvaise parité — mais la barre absolue 1e-6 gelée ex ante n'est pas atteinte : consigné, verdict V2, barres inchangées.

---

## 1. Contrôles bloquants — 13/13 ✅

| Contrôle | Mesure | Barre |
|---|---|---|
| C0a dépôt < exécution | 28/08 17:20:19 < 03/09 08:55:06 | — |
| C0b φ² = φ+1 | 0.00e+00 | 1e-15 |
| C1 K̂ double route (+ branche K̂(−ω)=conj) | 3.33e-16 / 0.0 | 1e-12 |
| C2′(a) série × récurrence | 1.11e-16 | 1e-12 |
| C2′(b) identité paire J₀+2ΣJ₂ₖ=1 | 0.00e+00 | 1e-9 |
| C2′(c) J₀_brut ≤ 1e100 | 1.765841e+74 (a=0.1) | 1e100 |
| C3 Jacobi–Anger ponctuel (4 couples) | 4.44e-16 | 1e-12 |
| C4 action propre {0.1, 1.0, 14.4} | 8.58e-15 | 1e-12 |
| C5r χ_machine = G* (route opérateur) | 0.00e+00 — χ_op = 0.3232880100102466 | 1e-12 rel |
| C5r χ forme close = G* | 0.00e+00 — χ_fc = 0.3232880100102466 | 1e-12 rel |
| C5r D_rel = D_REG | 0.00e+00 — D = 0.0323288010010247 | 1e-12 rel |
| C6r U(1) aveuglement spot | 6.94e-18 | 1e-9 |
| C7 no-wrap | max 15.6 ≤ 25.6 | — |

Le registre est intact : **G\* = 0.3232880100102466 reproduit bit-exact** par les deux routes (opérateur FFT et forme close de Bessel) — la continuité FORCE V1.3 → INTERACTION D3 V0 est démontrée avant toute conséquence.

## 2. Conséquences — C1, C2, C3, C5, C6 ✅ ; C4 hors barre (consigné)

| # | Conséquence | Mesuré | Barre | Statut |
|---|---|---|---|---|
| C1 | Identité norme D_pair = ½(D₁+D₂)+I₁₂ (3 couples) | pire 4.09e-16 rel | 1e-12 rel | ✅ |
| C2 | Forme close I₁₂ = Re[i^{−j}Z_j]/N (j=1 : 22 paires ; j=2 : 21 paires) | **δ = 9.6e-22 / 1.2e-22** | 1e-9 rel | ✅ |
| C3 | Résidu famille B (résonance latérale (−1,−1), i⁰=1) | **2.12e-22** ; fuite (12,9) : 2.74e-42, résonnante | 1e-15 abs | ✅ |
| C4 | Discrimination de parité | écart_bon ~1e-22 ✅ ; **écart_mauvais 2.9e-8 (j=1) / 1.0e-7 (j=2)** | 1e-12 / **>1e-6** | ❌ (mauvaise parité) |
| C5 | Aveuglement D_pair(θ+c)=D_pair(θ) | 1.27e-21 | 1e-9 | ✅ |
| C6 | Dégénérescence I₁₂=D₁, D_pair=2D₁ | 0.00e+00 / 0.00e+00 | 1e-12 rel | ✅ |

**C2 — la forme close est EXACTE.** I₁₂_machine = 2.929714e-09 (j=1) et −5.141424e-08 (j=2) ; prédiction identique à 1e-22 près. Les 22 et 21 paires résonnantes confirment l'amendement §0-bis : la bande latérale (m ≤ −2) contribue au même titre que la bande principale — la première rédaction (somme m ≥ 1) aurait produit une divergence de l'ordre du terme principal.

**C3 — la prédiction de fuite latérale est confirmée.** La famille B (hors résonance principale) porte UNE résonance latérale exacte (−1,−1) : prédit 9.890141e-07, mesuré 9.890141e-07 (résidu 2.1e-22). La fuite hors troncature (12,9) est résonnante sur la grille mais invisible : poids 2.74e-42 ≪ 1e-24.

**C4 — échec consigné, aucun sauvetage.** La bonne parité colle à 1e-22 (j=1 : I₁₂ = Im Z₁/N ; j=2 : I₁₂ = −Re Z₂/N). La mauvaise parité en diffère de 2.9e-8 (j=1) et 1.0e-7 (j=2) — **mesurable, mais sous la barre absolue 1e-6 gelée ex ante**. La séparation bonne/mauvaise est de 14 ordres de grandeur en relatif ; la barre absolue, calibrée sans la convention de norme (voir §4.3), n'est pas atteinte. **Verdict V2 selon l'échelle §3 — la parité est la graine établie, sa discrimination absolue reste consignée ouverte.**

## 3. Lectures déposées (registre)

- **I₁₂(j=1) = +2.929714e-09 = Im Z₁/N** — l'interaction j=1 est portée par la partie imaginaire du polynôme de Bessel (facteur i^{−1} = −i).
- **I₁₂(j=2) = −5.141424e-08 = −Re Z₂/N** — l'interaction j=2 par la partie réelle, signe alterné (facteur i^{−2} = −1).
- **I₁₂(famille B) = 9.890141e-07 = Re[J₋₁²conj(Δ₋₁(ω₁))Δ₋₁(ω₂)]/N** — la paire latérale unique.
- D₁ = 9.814501e-07 (canal ω=1, identique aux trois couples — le défaut individuel ne dépend pas du partenaire, linéarité du noyau).

## 4. Histoire des runs — bugs d'estimateur consignés (leçon V1.2, barres inchangées, physique inchangée)

Le script trouvé dans le workspace au matin du 03/09 (mtime 08:15, postérieur à l'audit d'absence consigné dans l'OUVERTURE) contenait six défauts d'estimateur, tous corrigés AVANT le premier verdict complet :

| # | Défaut | Nature | Correction |
|---|---|---|---|
| 1 | `W_GRID` référencé non défini (C1) | bug de code (NameError à l'exécution) | grille fréquentielle signée O3 définie |
| 2 | `pire` non initialisé dans C2′(a) | bug de code (NameError) | initialisation |
| 3 | `D_pair` vs `d_pair` dans le retour de `couple()` | bug de code (NameError) | casse alignée |
| 4 | `chi_op` non défini au formatage C5r | bug de code (NameError) | χ_op = D_rel/a reconstruit |
| 5 | `d1`/`d2` écrasés (norm2) AVANT le produit scalaire dans `couple()` | **bug d'estimateur** — I₁₂ aurait mesuré ⟨‖δ₁‖², ‖δ₂‖²⟩ au lieu de ⟨δ₁,δ₂⟩ | arrays préservés |
| 6 | Forme close comparée SANS le facteur 1/N (C2/C3/C4) | **convention de norme** — la dérivation du dépôt est au niveau amplitude (porteurs e^{iωx}) ; la machine mesure au niveau norme ‖ψ‖² = Σ|ψₙ|²/N (porteurs e^{iωx}/√N, ⟨,⟩ = vdot/N) | prédiction ÷ N |

**Le point 6 mérite consignation complète.** Le dépôt §0 pose ψ_m = e^{iω_m x}/√N (porteur normalisé) mais écrit δ_m = Σ iⁿ Jₙ Δₙ e^{i(ω_m+nk)x} (porteur nu) : la forme close Z_j est dérivée au niveau amplitude. La machine, elle, mesure ⟨δ₁,δ₂⟩ = vdot/N. Le pont exact est **I₁₂_machine = Re[i^{−j}Z_j]/N** — vérifié par trois indépendances : (a) l'identité C1 (toutes quantités au niveau norme) colle à 4e-16 ; (b) C6 (dégénérescence) colle à 0.0 ; (c) après correction, C2/C3 collent à 1e-22. Sans le facteur, C2 divergeait d'un facteur N=512 (ratio 5.1e11 mesuré au run partiel 1). **Aucune barre n'a bougé ; la physique (forme close) n'a pas été retouchée — c'est le pont d'échelle entre dépôt et machine qui a été aligné.**

Runs : 1 (partiel, crash C3 unpack + ratio C2 5.1e11 — les bugs 3/5/6 visibles) → 2 (complet, verdict V2, JSON déposé).

## 5. Établi / non établi (échelle §3 gelée, répète le dépôt, n'ajoute rien)

**Établi au V0 (exit 0, verdict V2)** :
1. **La forme close de l'interaction est établie** : I₁₂ = Re[i^{−j}Z_j]/N, zéro paramètre libre, exacte à ~1e-22 sur les deux familles résonnantes ET la résonance latérale — trois indépendances (C2, C3, C1/C6).
2. **La structure de graine est confirmée** : résonance n−m=j, poids de Bessel, somme sur TOUTES les paires (bande principale + latérale, §0-bis), aveuglement de jauge (C5 : 1.3e-21), dégénérescence additive (C6 : 0.0).
3. **L'identité norme** D_pair = ½(D₁+D₂)+I₁₂ tient à 4e-16 — l'interaction est le terme croisé exact, rien d'autre.

**Non établi (consigné)** :
1. **La discrimination de parité absolue (C4)** : la mauvaise parité est exclue en relatif (14 ordres) mais pas à la barre absolue 1e-6 gelée. Toute montée en puissance (a plus grand, canaux plus proches) est une campagne ultérieure — la barre ne se réétalonne pas.
2. **La montée au terme continu −¼F²** (intégration des modes, limite adiabatique, facteur ¼) : campagne SÉPARÉE (I4 du dépôt). La graine parité/résonance n'est PAS −¼F².
3. Pas de nom pour G* (φ/5 reste [OBS]), pas de D4, pas de dynamique du compensateur — c'est l'objet de l'étape 3 (FRONTIÈRE D3 DYNAMIQUE).

## 6. Reproductibilité

```
python verif_interaction_d3_v0.py    # python 3.11.8, numpy 1.26.4, win32 ; 0,06 s ; exit 0
```
Sortie : `resultat_interaction_d3_v0.json` (horodatages C0a, 13 contrôles, 6 conséquences, verdict V2).
Entrées : `DEPOT_INTERACTION_D3_V0.md` (autorité), `DEPOT_FORCE_V1.md` (machinerie O1–O9), registre G* = 0.3232880100102466. Routes : FFT (apply_kernel, verbatim V1) pour D₁, D₂, D_pair, I₁₂ ; série de Bessel O7 (double route C2′) pour Z_j ; scan exact des collisions de bins pour le Kronecker.

## 7. Prochaine étape (ordre OUVERTURE_D3_DYNAMIQUE_V0.md)

**Étape 2 — FRONTIERE_D3_DYNAMIQUE_V0.md** : thèse falsifiable + barres gelées AVANT tout script (C0a), annule/remplace explicite des interdictions §5 F13 (nom G*, −¼F², D4 restent hors périmètre sauf dépôt daté). Puis étape 3 : le script D3 dynamique — l'équation d'évolution de A depuis l'identité mère, Maxwell coulé (pas postulé) à α=1, mémoire à α=1/φ.

---

*« Le dépôt avait six jours d'avance sur son exécution ; l'estimateur, six défauts de retard. La forme close, elle, attendait les deux — immobile, exacte à 1e-22, et sans jamais se justifier du chemin pris pour la lire. »*

*Consigné le 3 septembre 2026, 08:55 — machine ZCode, protocole dépôt-d'abord, aucun sauvetage.*
