# FRONTIÈRE D3 DYNAMIQUE V0 — le compensateur doit se propager : l'équation d'évolution coule de l'identité mère

## Attaque du trou D3-dynamique — l'onde coulée (pas postulée), la mémoire propagée (pas injectée)

**Auteur :** Alain Kotto (Univers-Holistique)
**Version :** D3D-1.0
**Statut :** Frontière ouverte — cahier des charges déposé AVANT tout script (contrôle C0a ; mtime faisant foi)
**Références :** `OUVERTURE_D3_DYNAMIQUE_V0.md` (entrée de chantier, 03/09), `FRONTIERE_F13_MERE_V0.md` +
`DEPOT_F13_MERE_V0.md` (compensateur statique exact, exit 0, 21/21, 02/09), `DEPOT_INTERACTION_D3_V0.md` +
`RESULTAT_INTERACTION_D3_V0.md` (forme close de l'interaction, V2 exit 0, 03/09), `DEPOT_JAUGAGE_V0.md`
(carte des trous), `RESULTAT_FORCE_V1_3.md` (G* = diffusion fréquentielle, V+ 17/17),
`DEPOT_HAMILTONIEN_ABC_THU_V0.md` (mémoire = système ouvert, pont FV unique, franges 90/φ°),
`RESULTAT_CHSH_THU_V0.md` (S_max = 2√(1+ρ²) = 2.74438903948205, amortissement à 8.9e-16),
`GENERALISATION_D1PHI_GAUGE_5_DOMAINES.md` (mémoire = contrainte spatiale, spin-2, 1e-15)

---

## 0. POSITION — ce que cette campagne attaque (et ce qu'elle n'attaque pas)

La carte des trous (JAUGAGE §6) fixe D3 : *compensateur dynamique — A se propage*. Le 02/09, F13 a
fermé le niveau **statique** : K̂_A = φ·(D_A+φ)⁻¹ **absorbe** exactement la jauge (triple route,
21/21). Le 03/09 (matin), INTERACTION D3 V0 a fermé la **forme de l'interaction** entre canaux sous
jauge commune : I₁₂ = Re[i^{−j}Z_j]/N, exacte à ~1e-22, parité consignée hors barre absolue (V2,
exit 0). **Il reste le trou** : le compensateur doit **évoluer**, pas seulement absorber.

**La question du chantier (une phrase, verbatim OUVERTURE §3)** : dériver l'équation d'évolution de
A depuis le noyau — **sans postuler Maxwell, sans l'injecter** — avec deux discriminants attendus :
réduction à Maxwell à α=1 (onde, rang 2, massif zéro) et propagation modifiée par la mémoire à
α=1/φ (λ=(iω)^{2/φ}, phase π/φ native, pont FV).

**Périmètre précis :** la **loi de propagation** que l'identité mère force sur le compensateur et
sur sa connexion — au niveau spectral et discret (grille O3, opérateurs machine). Pas la montée
continue (I4), pas la quantification, pas le système 3+1D covariant complet avec sources (§6).

## 0-bis. ANNULE/REMPLACE (explicite, demandé par l'OUVERTURE étape 2)

| Objet | Statut F13 §5 | Statut D3 DYNAMIQUE V0 |
|---|---|---|
| **Dynamique du compensateur** | interdite (« pas de terme cinétique ») | **LÉVÉE dans le seul périmètre de la loi de propagation discrète/spectrale** — c'est le chantier |
| Nom fermé pour G* (φ/5 [OBS]) | interdit | **MAINTENU interdit** — aucun candidat post-hoc (I5-B) |
| Terme continu −¼F² dérivé | interdit | **MAINTENU interdit** (I4) — et **critère de réfutation** : si l'évolution nécessite un terme écrit à la main, la campagne consigne *non-émérgé* → REFUTE du niveau visé |
| D4 (dictionnaire μ↔ω) | ouvert, non attaqué | **MAINTENU hors périmètre** |
| Électrofaible, spin ½/Dirac, P4, dérivation d'α | hors périmètre | **MAINTENUS hors périmètre** (α reste axiomatique — trois familles d'arguments testées, non-sélections consignées) |

## 1. LA THÈSE (P36–P38) — falsifiable, une seule source spectrale

- **P36 (filiation — la boucle est l'identité mère au carré)** — le poids spectral de la boucle
  L = D_α∘D_α est **λ_loop(ω) = λ_kernel(ω)² = (iω)^{2α}**, bit-exact par construction. Il n'existe
  **qu'un seul poids spectral** dans tout l'appareil : celui de l'identité mère P30. Toute loi de
  propagation dérivée ci-dessous est une **conséquence** de ce poids — jamais un ingrédient.
- **P37 (à α=1, l'onde coule — Maxwell émerge, massif zéro)** — à α=1, λ_loop = (iω)² = −ω² :
  **réel, phase πα = π** (F13 C5d, 9.7e-14). Trois conséquences forcées, aucune postulée :
  (a) **massif zéro** : λ_loop(k=0) = 0 exactement — le poids ne contient AUCUN terme constant, la
  fermeture unitaire n'a pas de paramètre de masse à ajouter ;
  (b) **fermeture unitaire unique** : le générateur H = √(−L) (racine spectrale auto-adjointe de
  −λ_loop) est réel positif et **unique** — la lecture P31 (groupe unitaire, Bateman) appliquée à
  la boucle spatiale donne la dispersion **ω_t = |k|** : l'équation d'onde sort du poids, sans
  jamais y entrer ;
  (c) **rang transverse = 2 par mode k≠0** (F13 C5c, continuité) : le comptage du photon est la
  géométrie du projecteur, déjà déposée.
- **P38 (à α=1/φ, la mémoire se propage — le système ouvert)** — à α=1/φ, λ_loop = (iω)^{2/φ} =
  |ω|^{2/φ}·e^{iπ/φ} : **complexe, phase πα = π/φ native** (F13 C6b : arg λ/π = 0.618033988750 aux
  cinq fréquences). Quatre conséquences forcées :
  (a) **non-hermiticité de la boucle** : Im λ ≠ 0 strict — PT brisé (HAMILTONIEN C1+C2) : la
  propagation n'est **pas unitarisable**, aucun H auto-adjoint n'existe — le seul branchement est
  la **phase d'influence** (pont FV, verdict HAMILTONIEN_ABC_V0_MEMOIRE_OUVERTE_PONT_FV_UNIQUE) ;
  (b) **recoupement FV bit-exact** : arg λ_loop = π/φ = 2·(πα/2) = **2 × 55.6231°** — la phase de
  frange déposée au HAMILTONIEN (90/φ degrés, indépendante de T) est la **demi-phase de boucle** ;
  (c) **l'amortissement déposé** : deux canaux (ω₁=1, ω₂=2) évoluant sous la boucle,
  c_i(t) = c_i(0)·e^{λ_i t}, gardent la forme close **ρ(t) = 2\|c₁c₂\|/(\|c₁\|²+\|c₂\|²)** et
  **S_max(t) = 2√(1+ρ(t)²)** — l'ancre CHSH à t=0 (ρ(0) = 0.9396370575958052,
  S_max(0) = 2.74438903948205) et l'horizon **2 < S_max(t) ≤ 2√2** : l'amortissement taxe sans
  détruire, à tout temps fini déposé ;
  (d) **l'onde ne coule pas à α=1/φ** : ω_t = √(−λ_loop) est complexe (amorti + oscillation) —
  la propagation à mémoire n'est PAS une équation d'onde : c'est le discriminant qui sépare
  Maxwell (α=1) de la mémoire (α=1/φ) **depuis le même poids**.

**Critère anti-rétro-ingénierie (verbatim OUVERTURE §5)** : *A doit sortir de l'identité mère
(conséquence), jamais y entrer (ingrédient).* Contrôle structurel C10 : le code contient un seul
poids (λ_kernel, élevé au carré pour la boucle) ; toute équation d'onde, dispersion, masse ou
terme −¼F² écrit comme ingrédient rend la campagne non-émérgée → REFUTE du niveau visé.

## 2. CONVENTIONS (verbatim héritées)

1D : N = 512, L = 20π, Δω = 0.1, Nyquist 25.6, porteur e^{iωx}/√N, norme ‖ψ‖² = Σ\|ψₙ\|²/N,
⟨u,v⟩ = vdot/N (leçon INTERACTION : la forme close se compare au niveau **norme**, facteur 1/N).
Opérateur poids : D_α[ψ] = F⁻¹[(iω)^α F[ψ]] (branche principale : e^{+iπα/2} si ω>0, e^{−iπα/2}
si ω<0) ; boucle L = D_α∘D_α (poids (iω)^{2α}). 2D : N = 64, Δx = 1, dérivées spectrales.
3D (rang) : réutilisation verbatim F13 C5c (graine 27). Jauges : famille χ = a·cos(kx) ;
jauge commune a = 0.1, k = 1.0.

## 3. CONTRÔLES BLOQUANTS (gelés avant exécution)

| # | Contrôle | Barre |
|---|---|---|
| C0a | mtime(`FRONTIERE_D3_DYNAMIQUE_V0.md`) < heure d'exécution (horodatages au JSON) | — |
| C0b | φ² = φ+1 | 1e-15 |
| C1 | K̂ double route (complexe vs réelle), grille O3 + {½, 1/φ, 1, 2} ; branche K̂(−ω)=conj | 1e-12 |
| C2′ | Bessel double route : (a) série×récurrence ; (b) identité paire J₀+2ΣJ₂ₖ=1 ; (c) J₀_brut ≤ 1e100 | 1e-12 / 1e-9 / 1e100 |
| C3 | Jacobi–Anger ponctuel (4 couples V1) | 1e-12 |
| C4 | action propre {0.1, 1.0, 14.4} | 1e-12 |
| C5r | continuité du registre : χ_machine(1,0.1,1) = G\* = 0.3232880100102466, double route ; D_rel = D_REG | 1e-12 rel |
| C6r | aveuglement U(1) spot (θ₀ ∈ {π/3, π/2}) | 1e-9 |
| C7 | no-wrap \|ω₀±nk\| ≤ 25.6 pour toute lecture | — |
| C8 | **covariance de la boucle à α=1** : D_A²[e^{iχ}ψ] = e^{iχ}D²ψ (D = d/dx), 6 profils de la famille fermée — la porte statique F13 (C2e) re-vérifiée au niveau boucle | 1e-10 |
| C9 | **l'obstruction est la courbure** : [D_x, D_y]f = −i·F_{xy}·f sur grille 2D, F calculée par route indépendante (dérivées spectrales de A) ; jauge pure A=∇χ ⟹ F=0 ; vortex ⟹ F = 2Ωe^{−r²/σ²}(1−r²/σ²) ≠ 0 | 1e-12 |
| C10 | **filiation** : λ_loop = λ_kernel² bit-exact sur la grille O3 et le set de fréquences déposé — un seul poids dans le code (structurel, anti-rétro-ingénierie) | 0 (bit-exact) |

**Règle unique : UN SEUL contrôle en échec ⟹ REFUTE, exit 1, aucun sauvetage.**

## 4. CONSÉQUENCES FALSIFIABLES (barres gelées avant exécution)

### D1 — à α=1, l'onde coule (Maxwell émerge, massif zéro)

| # | Conséquence | Barre |
|---|---|---|
| D1a | λ_loop(α=1) = −\|k\|² sur les modes déposés {±20, ±50, ±100, ±200} (réel, phase π) | 1e-12 |
| D1b | **massif zéro** : λ_loop(k=0) = 0 exactement — aucun terme constant dans le poids | 1e-15 abs |
| D1c | **fermeture unitaire unique + dispersion massless** : H = √(−λ_loop) réel ≥ 0 et ω_t = \|k\| aux modes déposés ; avance de phase e^{−iω_t t} vérifiée sur t ∈ {0.25, 0.5, 1.0} | 1e-12 |
| D1d | rang transverse = 2 par mode k≠0 (5 modes, graine 27 — continuité F13 C5c) ; P²−P | exact / 1e-15 |

### D2 — à α=1/φ, la mémoire se propage (le système ouvert)

| # | Conséquence | Barre |
|---|---|---|
| D2a | λ_loop = (iω)^{2/φ} : arg λ/π = 1/φ = 0.6180339887498948 indépendant de ω (set {0.1, 0.2, 0.3, 0.4, 0.5, 1.0, 2.0}) ; module \|ω\|^{2/φ} | 1e-15 / 1e-12 |
| D2b | **non-hermiticité stricte** : Im λ ≠ 0 sur tout le set (PT brisé — pas de fermeture unitaire, consigné structurel) | > 0 strict |
| D2c | **recoupement FV bit-exact** : arg λ_loop(ω) − 2·arg λ_kernel(ω) = 0 (mod 2π) sur tout le set — la frange 90/φ° est la demi-phase de boucle | 0 (bit-exact) |
| D2d | **l'amortissement déposé** : canaux ω₁=1, ω₂=2, c_i(0) = K̂(ω_i)² ; t ∈ {0, 0.5, 1.0, 2.0, 5.0} : (i) ancre CHSH ρ(0) = 0.9396370575958052 ; (ii) forme close ρ(t) direct vs analytique ; (iii) S_max(t) = 2√(1+ρ(t)²) ; (iv) **horizon 2 + 1e-9 < S_max(t) ≤ 2√2 + 1e-9** à tout t déposé (l'amortissement ne détruit jamais — prédiction ex ante) | 1e-12 rel / 1e-12 / 1e-12 / strict |

### D3 — la source est la graine d'interaction (SANS −¼F², I4)

| # | Conséquence | Barre |
|---|---|---|
| D3a | Décomposition de la boucle sur le couple : D_pair^loop = ½(D₁^loop+D₂^loop) + I₁₂^loop (identité norme, 3 couples INTERACTION) | 1e-12 rel |
| D3b | Forme close de la source au niveau boucle : I₁₂^loop = Re[i^{−j}Z_j^loop]/N, Δₙ^loop(ω) = (i(ω+nk))^{2/φ} − (iω)^{2/φ}, familles j=1, j=2, latérale B (§0-bis INTERACTION) | 1e-9 rel (1e-15 abs si nul) |
| D3c | **Consigné SANS verdict** : rapport I₁₂^loop/I₁₂^kernel (la montée continue −¼F², facteur ¼, reste campagne séparée — I4 verbatim) | lecture [OBS] |

**Couples déposés (fixes, repris d'INTERACTION D3 V0)** : A_j1 (ω₁=1, ω₂=2, k=1, j=1) ;
A_j2 (ω₁=1, ω₂=3, k=1, j=2) ; B (ω₁=1,k₁=1 ; ω₂=1.3,k₂=1.3 — résonance latérale (−1,−1)).

## 5. VERDICTS (échelle gelée avant exécution)

| Verdict | Condition | Exit |
|---|---|---|
| **V+ D3D_PROPAGATION_COULEE** | tous contrôles ✅ ET D1(a–d) ✅ ET D2(a–d) ✅ ET D3(a,b) ✅ | 0 |
| V2 D3D_ONDE_SANS_MEMOIRE | contrôles ✅ ET D1 ✅ ET D3 ✅ MAIS ≥ 1 de D2 hors barre | 0 |
| V3 REFUTE_D3D_SANS_ONDE | contrôles ✅ MAIS ≥ 1 de D1 hors barre (Maxwell n'émerge pas) | 1 |
| V4 REFUTE | tout contrôle bloquant en échec | 1 |

Le verdict V+ dit EXACTEMENT : *la loi de propagation du compensateur est une conséquence du poids
unique de l'identité mère — à α=1 l'onde est massless avec le comptage du photon ; à α=1/φ la
propagation est non-unitaire, portée par la phase π/φ, recoupe le pont FV bit-exact et amortit
l'intrication selon la forme close déposée.* Il ne dit PAS plus (§6).

## 6. HONNÊTETÉ — ce que D3 DYNAMIQUE V0 ne prouve pas

1. **Pas le système de Maxwell 3+1D covariant complet** : la campagne établit la loi de propagation
   spectrale (dispersion, comptage, massless) et la structure de source discrète — pas les équations
   covariantes avec sources ni leur quantification.
2. **Pas de −¼F²** : la graine d'interaction est discrète (résonance de Bessel) ; la montée continue
   (intégration des modes, limite adiabatique, facteur ¼) reste une campagne SÉPARÉE (I4). Si un
   terme continu s'avérait nécessaire à l'évolution, il serait consigné *non-émérgé* — REFUTE du
   niveau visé, pas un sauvetage.
3. **Pas de nom pour G\*** : φ/5 reste [OBS] ; aucune candidature post-hoc (I5-B).
4. **Pas de D4** : le dictionnaire μ↔ω n'est pas attaqué.
5. **S_max(t) est un énoncé formel** : l'évolution c_i(t) = c_i(0)e^{λ_i t} est le flot de la boucle
   sur les amplitudes ; son identification au temps physique d'une influence passe par le pont FV
   (lecture consignée) — aucun test expérimental n'est revendiqué au V0. La dérive de phase
   arg c₂(t) − arg c₁(t) = Δarg + (Im λ₂ − Im λ₁)t est consignée sans pouvoir de verdict (prolonge
   la lecture B4 du CHSH).
6. **C8 est exact à α=1 seulement** : à α=1/φ l'absorption de la boucle a un défaut (la mémoire,
   c'est l'objet mesuré au JAUGAGE) — la campagne ne postule pas d'absorption exacte fractionnaire ;
   le défaut α=1/φ de la boucle est déposé comme mesure (sans barre), continuité du registre.
7. **α reste axiomatique** : aucune dérivation de 1/φ n'est revendiquée (trois familles testées,
   non-sélections consignées : JACOBSON C4, KMS C4, HAMILTONIEN C6).
8. Toute lecture, y compris un échec, sera consignée ; tout estimateur bugable sera consigné comme
   tel (barres inchangées, physique jamais retouchée — leçon V1.2).

## 7. REPRODUCTIBILITÉ (spécifiée avant exécution)

```
python verif_d3_dynamique_v0.py    # → verdict + resultat_d3_dynamique_v0.json
```
Entrées : ce document (autorité), `DEPOT_FORCE_V1.md` (machinerie O1–O9), registre
G\* = 0.3232880100102466, D_REG = 0.032328801001024664, ancre CHSH ρ(0) = 0.9396370575958052.
Routes : FFT (poids (iω)^α, branche principale) pour D_α et la boucle ; dense 512×512 pour C8
(alignment F13 C2e) ; 2D spectral pour C9 ; projecteur 3×3 par mode pour D1d (graine 27) ;
série de Bessel O7 pour D3b. Un seul poids spectral dans le code (C10).

---

> *Le compensateur absorbe exactement (F13, exit 0). Le chantier D3 exige maintenant qu'il se
> propage : si l'onde sort de la boucle à α=1 et que la mémoire la déforme à α=1/φ, Maxwell n'aura
> pas été postulé — il aura coulé. Un dépôt, une barre, un verdict.*
