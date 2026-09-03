# D3 DYNAMIQUE V0 — V+ : la propagation est COULÉE — Maxwell émerge à α=1, la mémoire se propage à α=1/φ

**Campagne du 3 septembre 2026 — étape 3 de l'OUVERTURE D3 DYNAMIQUE (frontière gelée avant tout script)**

| | |
|---|---|
| Frontière | `FRONTIERE_D3_DYNAMIQUE_V0.md` (gelée, commit **c9b428d**, mtime **2026-09-03 09:23:32**, avant tout script) |
| Script | `verif_d3_dynamique_v0.py` (écrit le 03/09 après la frontière ; trois défauts d'estimateur corrigés AVANT le verdict déposé, consignés §4) |
| Journal | `resultat_d3_dynamique_v0.json` (consignation intégrale, exécution 10:08:13) |
| C0a | **OK** — frontière (09:23:32) < exécution (10:08:13), antériorité 2 680 s, provenance commit c9b428d |
| Contrôles | **15/15 ✅** (C0a, C0b, C1, C2′a/b/c, C3, C4, C5r×3, C6r, C7, C8, C9, C10) |
| **Verdict** | **V+ — D3D_PROPAGATION_COULEE — exit 0** (échelle §5 gelée appliquée telle quelle) |

> **L'équation d'évolution de A sort de l'identité mère.** À α=1, le poids de boucle λ_loop = λ_kernel² = (iω)² = −|k|² est exactement le propagateur de Maxwell massif zéro : dispersion linéaire ω_t = |k|, avance de phase e^{−i|k|t}, rang transverse 2 — l'onde COULE, Maxwell n'a pas été postulé, il a coulé de la filiation P36 par simple carré du poids mère. À α=1/φ, le même poids devient |ω|^{2/φ}·e^{iπ/φ} : la mémoire déforme la propagation (phase fractionnaire, PT brisé, amortissement qui taxe sans détruire). Aucun ingrédient n'est entré dans l'identité mère — A en est SORTI comme conséquence.

---

## 1. Contrôles bloquants — 15/15 ✅

| Contrôle | Mesure | Barre |
|---|---|---|
| C0a frontière < exécution | 09:23:32 < 10:08:13 (commit c9b428d) | — |
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
| C8 covariance boucle α=1 : D_A²[e^{iχ}ψ] = e^{iχ}D²ψ | 1.09e-11 (6 profils, dense 512², alignement F13 C2e) | 1e-10 |
| C9 commutateur = courbure | jauge pure 5.7e-16 ; vortex F−close 6.7e-16, ‖F‖ = 2.0 ; comm bas-k 3.6e-15 | 1e-12 |
| C10 filiation λ_loop = λ_kernel², site unique | carré bit-exact **0.00e+00** sur le set ; LG ≡ WG² (un seul poids) | 0 (bit-exact) |

Le registre est intact : **G\* = 0.3232880100102466, D_REG = 0.032328801001024664, ancre CHSH ρ(0) = 0.9396370575958052 reproduits** — la continuité FORCE V1.3 → INTERACTION D3 → D3 DYNAMIQUE est démontrée avant toute conséquence.

**C8 — l'opérateur de boucle est covariant.** D_A² commute avec la jauge locale à α=1 sur 6 profils (a ∈ {1, 1.3, 0.5}, k ∈ {1, 1.3, 2}) à 1.09e-11, sous la barre 1e-10 gelée — la route dense alignée sur F13 C2e.

**C9 — le commutateur lit la courbure.** En jauge pure (χ constant par plaques), F = 0 et [D_x, D_y] = 0 simultanément (5.7e-16 / 3.6e-15) ; le vortex Ω=1, σ=5 donne ‖F‖ = 2.0 exact (forme close à 6.7e-16). La structure de Maxwell est lue, pas imposée. (Queue spectrale (5,−3) : 4.3e-15, consigné [OBS].)

**C10 — la filiation est bit-exacte et le site est unique.** LG ≡ WG² par multiplication (`loop_weight = lambda_weight * lambda_weight`, un seul site de carrage dans tout le code) ; le carré complexe est bit-exact (0.0) sur le set déposé. (Doublement d'argument à 1 ulp — 2.2e-16 — et route directe (iω)^{2α} à 2.6e-16 : consignés [OBS], l'arrondi atan2/puissance n'entame pas la filiation des valeurs.)

## 2. Conséquences — D1, D2, D3 ✅

### D1 — à α=1, l'onde coule (Maxwell émerge, massif zéro)

| # | Conséquence | Mesuré | Barre | Statut |
|---|---|---|---|---|
| D1a | λ_loop(α=1) = −\|k\|² sur {±20, ±50, ±100, ±200} (réel, phase π) | poids **1.22e-16** ; dense (F13 C5d) 9.7e-14 ; phase/π 3.3e-16 | 1e-12 | ✅ |
| D1b | massif zéro λ_loop(0) = 0 | **0.00e+00** (route poids, exact) | 1e-15 abs | ✅ |
| D1c | H = √(−λ) réel ≥ 0, ω_t = \|k\|, avance de phase e^{−i\|k\|t} | Im H 1.6e-15 ; ω_t 1.2e-15 ; phase 3.0e-15 | 1e-12 | ✅ |
| D1d | rang transverse = 2 (P²−P, 5 modes, graine 27) | **1.67e-16** ; rang 2 pour 5/5 modes | 1e-15 | ✅ |

**D1a — le propagateur de Maxwell sort du carré du poids mère.** Sur les huit modes déposés, λ_loop = −|k|² à 1.2e-16 relatif par le poids (route FFT, frontière §7) et à 9.7e-14 par l'opérateur dense B = DMAT@DMAT (route croisée F13 C5d). La phase est π (cercle : ±π même point — le branchement atan2 de Im λ < 0 rend −π, consigné §4).

**D1c — la lumière du treillis.** H = √(−λ_loop) est réel positif à 1.6e-15 ; la dispersion ω_t = |k| tient à 1.2e-15 ; l'avance de phase e^{−iω_t t} sur t ∈ {0.25, 0.5, 1.0} colle à 3.0e-15 (route FFT-diagonale, poids unique). La route eigh pleine matrice (512²) accumule 1.8e-12 d'arrondi [OBS] — limite d'estimateur, barre inchangée.

### D2 — à α=1/φ, la mémoire se propage (le système ouvert)

| # | Conséquence | Mesuré | Barre | Statut |
|---|---|---|---|---|
| D2a | arg λ_loop/π = 1/φ et module \|ω\|^{2/φ} sur le set {0.1…2.0} | arg/π **1.11e-16** ; module 4.44e-16 | 1e-15 / 1e-12 | ✅ |
| D2b | Im λ ≠ 0 strict (PT brisé) | **0.0541** (min sur le set) | > 0 strict | ✅ |
| D2c | recoupement FV : arg λ_loop = 2·arg λ_kernel (mod 2π) | **0.00e+00 bit-exact** sur tout le set | 0 (bit-exact) | ✅ |
| D2d | ancre ρ(0), forme close ρ(t), S_max(t), horizon strict | ancre **0.00e+00** ; forme 3.3e-16 ; S_max 0.0 ; horizon OK | 1e-12 / strict | ✅ |

**D2a/D2c — la phase fractionnaire est la signature de la mémoire.** arg λ_loop(ω) = π/φ à 1.11e-16 près sur tout le set — soit 2 × 55.62°, la demi-phase de boucle dont la frange FV 90/φ° est le double. Le recoupement FV (D2c) est **bit-exact** : la boucle est littéralement le carré du noyau, phase comprise.

**D2d — l'amortissement déposé taxe sans détruire.** Canaux ω₁=1, ω₂=2, graine c_i(0) = K̂(ω_i)² (pont /N, §4) :

| t | ρ(t) machine | S_max(t) |
|---|---|---|
| 0.0 | 0.9396370575958052 (= ancre CHSH, bit-exact) | 2.74438903948205 |
| 0.5 | 0.8425707784 | 2.61528240665859 |
| 1.0 | 0.7239016310656413 | 2.46903509206289 |
| 2.0 | 0.4905205806269144 | 2.22765386900081 |
| 5.0 | 0.1196599293476231 | 2.01426760753528 |

L'horizon tient strictement à tout t déposé : **2 + 1e-9 < S_max(t) ≤ 2√2 + 1e-9** — la mémoire amortit la corrélation (ρ → 0.12 à t=5) sans jamais refermer l'inégalité. Prédiction ex ante confirmée : le système ouvert n'efface pas la non-localité, il la taxe. La dérive de phase Δarg(t) = Δarg(0) + (Im λ₂ − Im λ₁)t colle à 1e-16 aux t = 0, 0.5, 1.0, 5.0 (t = 2.0 : wrap 2π d'atan2, consigné [OBS]).

### D3 — la source est la graine d'interaction (sans −¼F², I4)

| # | Conséquence | Mesuré | Barre | Statut |
|---|---|---|---|---|
| D3a | identité norme D_pair^loop = ½(D₁^loop+D₂^loop) + I₁₂^loop (3 couples) | pire **2.17e-15** rel | 1e-12 rel | ✅ |
| D3b | forme close I₁₂^loop = Re[i^{−j}Z_j^loop]/N | A_j1 4.5e-11 ; A_j2 **3.3e-16** ; B 2.0e-15 | 1e-9 rel | ✅ |
| D3c | rapport I₁₂^loop/I₁₂^kernel | −0.0159 / 197.27 / 6.81 | lecture [OBS] | consigné |

**D3b — la forme close de l'interaction se transpose au niveau boucle.** I₁₂^loop = Re[i^{−j}Z_j^loop]/N avec Δₙ^loop(ω) = (i(ω+nk))^{2/φ} − (iω)^{2/φ} : exact à 3.3e-16 rel (j=2, 21 paires résonnantes) et 4.5e-11 rel (j=1, 22 paires — I₁₂^loop ≈ −4.65e-11, dix fois sous la barre 1e-9). La résonance latérale (−1,−1) de la famille B colle à 2.0e-15 ; la fuite (12,9) est résonnante sur la grille mais invisible (poids J₁₂J₉ = 0.0 sous la troncature). **La graine d'interaction INTERACTION D3 V0 est la source de la dynamique boucle — même forme close, même structure de paires, un cran de puissance au-dessus.**

## 3. Lectures déposées (registre, sans pouvoir de verdict)

- **D3c — rapports I₁₂^loop/I₁₂^kernel [OBS]** : A_j1 −0.0159, A_j2 197.27, B 6.81. La boucle ne porte pas la même interaction que le noyau en proportion simple — la montée au terme continu −¼F² (facteur ¼, intégration des modes) reste la campagne I4, verbatim frontière §6.2.
- **défaut d'absorption de la boucle à α=1/φ [OBS]** : ‖L[e^{iχ}ψ] − e^{iχ}L[ψ]‖/‖L[ψ]‖ de 0.0087 (a=0.1, k=0.1) à 0.847 (a=1.0, k=1.0) — à α=1 le compensateur absorbe exactement (F13 exit 0), à α=1/φ le défaut est réel et croissant : c'est la mesure de la frontière entre les deux régimes, déposée sans barre (§6.6).
- **d1c_route_eigh [OBS]** : route pleine matrice, propagation pire 3.3e-14 (mode −200, t=1.0) — arrondi d'accumulation eigh, la barre porte sur la route FFT-diagonale.
- **d1b_route_operateur [OBS]** : Rayleigh B@1 = −4.45e-13 + 1.6e-15 i — l'estimateur dense, au niveau des autres arrondis d'accumulation ; la barre (1e-15 abs) porte sur le poids, exactement 0.
- **c9_queue_spectrale [OBS]** : (5,−3) à 4.3e-15 — même statut que le contrôle principal, marge 230×.

## 4. Histoire des runs — trois défauts d'estimateur corrigés avant le verdict déposé (leçon V1.2, barres inchangées, physique inchangée)

Le texte gelé de la frontière (commit c9b428d) est l'autorité ; le premier run a produit un **faux V4_REFUTE** par deux lectures d'estimateur plus strictes que le gel, corrigées avant tout dépôt :

| # | Défaut | Nature | Correction |
|---|---|---|---|
| 1 | C10 exigeait le doublement d'argument bit-exact **sur les tableaux grille** (atan2 des arrays WG/LG) | estimateur — la barre gelée C10 porte la **filiation des valeurs** (λ_loop = λ_kernel² bit-exact), le bit-exact d'angle est la barre de D2c (route scalaire, passe 0.0) | C10 aligné sur le texte gelé : LG ≡ WG² + carré bit-exact sur le set ; angle 1 ulp consigné [OBS] |
| 2 | D1a mesurait la phase π via `angle(λ)/π = 1` brut | estimateur — atan2 rend **−π** quand Im λ < 0 (λ = −ω² + iε) ; ±π est le même point du cercle | phase mesurée \|angle(λ)\|/π |
| 3 | sonde graine D2d comparait la route machine (niveau norme : ⟨carrier, K̂²·carrier⟩ = K̂²·\|carrier\|² = **K̂²/N**) à la forme close au niveau amplitude (K̂²) | **pont d'échelle amplitudes/normes — leçon V1.2 point 6, une deuxième fois** (rel mesuré 1 − 1/512 = 0.998, soit exactement N=512) | comparaison après pont /N → **1.15e-16** ; les deux routes de D2d vivent maintenant au même niveau norme |

Runs : 1 (C10+D1a mal alignés → faux V4, jamais déposé) → 2 (V+ exit 0, graine affichée 1.0e+00 = pont manquant, repéré avant DEPOT) → 3 (final, **V+ exit 0, JSON déposé**, graine 1.1e-16). **Aucune barre n'a bougé ; aucune physique retouchée — trois alignements d'estimateur sur le texte gelé et le pont de convention déposé.**

## 5. Établi / non établi (échelle §5 gelée, répète la frontière, n'ajoute rien)

**Établi au V0 (exit 0, verdict V+)** :
1. **À α=1, l'onde coule** : λ_loop = −|k|², massif zéro exact, H = √(−λ) réel, dispersion ω_t = |k|, rang transverse 2 — **Maxwell est sorti de l'identité mère par filiation (P36), sans jamais y entrer**. C8 (covariance) et C9 (commutateur=courbure) ferment la structure de jauge ; D1a–d la peuplent.
2. **À α=1/φ, la mémoire se propage** : phase fractionnaire exacte (arg/π = 1/φ à 1.1e-16, recoupement FV bit-exact), PT brisé structurellement, amortissement ρ(t) qui suit la forme close à 3.3e-16 et respecte l'horizon **2 < S_max(t) ≤ 2√2 strictement à tout t déposé** — la prédiction ex ante (taxer sans détruire) est confirmée ex post.
3. **La source est la graine** : la forme close d'INTERACTION D3 (I₁₂ = Re[i^{−j}Z_j]/N) se transpose au niveau boucle à ≤ 4.5e-11 rel sur les trois familles — l'identité norme tient (2.2e-15), la boucle est le carré du noyau **jusque dans son interaction**.

**Non établi (consigné)** :
1. **La montée continue −¼F²** (intégration des modes, limite adiabatique, facteur ¼) : campagne I4 séparée, verbatim. Les rapports D3c sont des lectures, pas des résultats.
2. **L'absorption fractionnaire exacte du défaut de boucle à α=1/φ** : mesurée (0.0087→0.847), déposée sans barre — aucune hypothèse n'est faite.
3. Pas de nom pour G* (φ/5 reste [OBS]), pas de D4, pas d'électrofaible, pas de spin ½, pas de P4, pas de dérivation de α — hors périmètre, verbatim frontière §6.

## 6. Reproductibilité

```
python verif_d3_dynamique_v0.py    # python 3.11.8, numpy 1.26.4, win32 ; 0,45 s ; exit 0
```
Sortie : `resultat_d3_dynamique_v0.json` (horodatages C0a, 15 contrôles, 10 conséquences + obs, verdict V+).
Entrées : `FRONTIERE_D3_DYNAMIQUE_V0.md` (autorité, commit c9b428d), `DEPOT_FORCE_V1.md` (machinerie O1–O9), registre G* = 0.3232880100102466, D_REG = 0.032328801001024664, ancre CHSH ρ(0) = 0.9396370575958052. Routes : FFT (poids (iω)^α, branche principale) pour D_α et la boucle ; dense 512×512 pour C8/D1 ; 2D spectral (ifft2) pour C9 ; projecteur 3×3 graine 27 pour D1d ; série de Bessel O7 (double route C2′) ; un seul poids spectral dans le code (C10).

## 7. Ce que ferme ce verdict

La chaîne est maintenant : **noyau (FORCE V1.3) → interaction (V2) → propagation (V+)**. Le compensateur absorbe (F13), l'interaction est la résonance de Bessel déposée (V2), et cette graine **se propage** : à α=1 elle engendre exactement le propagateur de Maxwell massif zéro, à α=1/φ elle déforme la propagation en système amorti non unitaire dont l'horizon CHSH tient strictement. La question D3 de l'OUVERTURE — *l'équation d'évolution de A peut-elle être dérivée du noyau sans y être injectée ?* — reçoit une réponse machine : **oui, par carré du poids, à un ulp près, zéro paramètre libre**. La boucle ouverte reste I4 (−¼F²) : la campagne suivante devra faire monter la graine discrète vers le terme continu, ou consigner l'écart.

---

*« Trois lectures ont failli renverser ce que le texte gelé portait : un cercle qu'on parcourait dans le mauvais sens (−π), une barre qu'on durcissait par excès de zèle (l'angle des tableaux), un facteur 512 entre deux niveaux d'écriture. Le verdict n'a pas bougé d'un iota — c'est la marque des barres posées avant les nombres : elles ne doivent rien au chemin pris pour les lire. »*

*Consigné le 3 septembre 2026, 10:08 — machine ZCode, protocole frontière-d'abord (C0a : commit c9b428d, antériorité 2 680 s), aucun sauvetage.*
