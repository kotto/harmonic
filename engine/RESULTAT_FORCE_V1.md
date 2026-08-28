# ⚡ FORCE V1 — G* expliqué : la forme close de diffusion fréquentielle du noyau

**Campagne du 28 août 2026 — guichet 2 (registre des forces)**

| | |
|---|---|
| Dépôt | `DEPOT_FORCE_V1.md` (gelé, mtime **2026-08-28 15:53:10**) |
| Script | `verif_force_v1.py` (mtime 2026-08-28 16:03:23 — écrit **après** le dépôt, **jamais modifié depuis l'exécution**, I5) |
| Journal | `resultat_force_v1.json` (consignation intégrale, écrit à l'exécution 16:03:39) |
| C0a | **OK** — dépôt (15:53:10) < exécution (16:03:39) |
| Contrôles | 8 ✅ / 1 ❌ (C2) |
| **Verdict** | **V4 — REFUTE — exit 1** (contrôle bloquant en échec : « aucun sauvetage », dépôt §4) |

> **Lecture honnête d'entrée.** Le verdict de campagne est V4 (REFUTE) et il est consigné tel quel — le protocole ne permet aucun sauvetage a posteriori (I5). Mais l'échec bloquant est le **témoin C2 ajouté par la machine** (double route de Bessel : série vs récurrence descendante de Miller), dont l'implémentation est défectueuse — **pas** la forme close déposée, qui tient à ≤ 3,15e-15 sur les 17 lectures, avec G\* bit-exact (0.00e+00) et la station ω₀ = 1 confirmée. Le script reste tel qu'exécuté ; toute correction passera par un nouveau dépôt daté (V1.1). Tout ce qui suit est la consignation intégrale, y compris l'échec.

---

## 1. Contrôles (dépôt §3)

| Contrôle | Statut | Mesure |
|---|---|---|
| C0a dépôt antérieur à l'exécution | ✅ | mtime dépôt 15:53:10 < exécution 16:03:39 |
| C0b fermeture algébrique φ² = φ+1 | ✅ | écart 0.0e+00 |
| C1 K̂ : route complexe vs forme réelle développée (grille O3 entière + {½, 1/φ, 1, 2}) | ✅ | écart max **1.24e-16** |
| **C2 Bessel double route : série vs récurrence descendante (a ∈ {0.1, 0.2}, n ≤ 11, \|J\| ≥ 1e-10)** | ❌ **ÉCHEC** | **écart max 1.00e+00** — cause racine en §5 |
| C3 Jacobi–Anger ponctuel sur le treillis (4 couples (a,k), résidu max sur 512 points chacun) | ✅ | écart max **2.29e-16** |
| C4 action propre du noyau sur 3 porteurs {0.1, 1.0, 14.4} | ✅ | max **3.79e-16** |
| C5 reproduction de la voie V0 : χ_machine(1, 0.1, 1) = G\* registre O9 | ✅ | écart relatif **0.00e+00** (bit-exact) |
| C6 U(1) aveuglement spot (θ₀ ∈ {π/3, π/2}, a=0.1, k=1, ω₀=1) | ✅ | dérive max **6.94e-18** |
| C7 no-wrap : \|ω₀ ± n·k\| ≤ Nyquist 25,6 pour toute lecture famille A | ✅ | max = 25,4 au porteur 14,4 — aucun mode wrapé |

---

## 2. Famille A — la forme close (17 lectures, barre 1e-9)

Hypothèse déposée [H] : la diffusion fréquentielle du noyau sur un mode de jauge e^{iω₀x} modulé par e^{ia·cos(kx)} donne, par Jacobi–Anger × action propre diagonale du noyau :

**χ(ω₀, a, k) = √( Σ_{n≥1} Jₙ(a)² · ( |K̂(ω₀+nk) − K̂(ω₀)|² + |K̂(ω₀−nk) − K̂(ω₀)|² ) ) / ( a·|K̂(ω₀)| )**

**17/17 lectures dans la barre. Pire écart : 3.15e-15 (porteur 14,4).**

| # | Lecture | χ_machine | χ_prédit | écart relatif |
|---|---|---|---|---|
| 1 | χ(0.1, 0.1, 1) | 0.2867645699087312 | 0.2867645699087312 | 1.94e-16 |
| 2 | χ(0.2, 0.1, 1) | 0.2836114397313612 | 0.2836114397313611 | 3.91e-16 |
| 3 | χ(0.3, 0.1, 1) | 0.2836049455803730 | 0.2836049455803729 | 3.91e-16 |
| 4 | χ(0.5, 0.1, 1) | 0.2886909006920941 | 0.2886909006920941 | **0.00e+00** |
| 5 | χ(0.8, 0.1, 1) | 0.3051745037448039 | 0.3051745037448039 | 1.82e-16 |
| 6 | **χ(1, 0.1, 1) = G\*** | 0.3232880100102466 | 0.3232880100102466 | **0.00e+00** |
| 7 | χ(1.3, 0.1, 1) | 0.2009386458414141 | 0.2009386458414140 | 4.14e-16 |
| 8 | χ(2, 0.1, 1) | 0.1340112861700273 | 0.1340112861700273 | 6.21e-16 |
| 9 | χ(2.1, 0.1, 1) | 0.1283926730650206 | 0.1283926730650207 | 6.49e-16 |
| 10 | χ(3.4, 0.1, 1) | 0.0861163237398250 | 0.0861163237398250 | 1.61e-16 |
| 11 | χ(5.5, 0.1, 1) | 0.0579675704520180 | 0.0579675704520180 | 1.20e-16 |
| 12 | χ(8.9, 0.1, 1) | 0.0385769856066765 | 0.0385769856066765 | 8.99e-16 |
| 13 | χ(10, 0.1, 1) | 0.0348802164044730 | 0.0348802164044730 | 2.59e-15 |
| 14 | χ(14.4, 0.1, 1) | 0.0253115414684661 | 0.0253115414684660 | **3.15e-15** (pire) |
| 15 | χ(1, 0.2, 1) — A2 | 0.3225067397099395 | 0.3225067397099396 | 3.44e-16 |
| 16 | χ(1, 0.1, 0.5) — A3 | 0.1013641298985957 | 0.1013641298985956 | 5.48e-16 |
| 17 | χ(1, 0.1, 2) — A3 | 0.3849844383150536 | 0.3849844383150536 | **0.00e+00** |

### A4 — G\* devient le 17ᵉ objet fermé **expliqué** (dépôt §2, conséquence C2)

Le balayage 14 porteurs donne χ_machine(1, 0.1, 1) = **0.3232880100102466**, et le registre O9 porte G\* = **0.3232880100102466** : écart relatif **0.00e+00**, bit-exact. Le nombre mesuré au jaugage V0 n'est plus un isolat : **c'est la diffusion fréquentielle du noyau sur le mode mère (ω₀ = 1, a = 0.1, k = 1)**, fermée ex ante par Jacobi–Anger × Bessel × action propre. Zéro paramètre libre — la seule entrée est le registre lui-même.

### A2 — la « dérive 5 % » du jaugage V0 était de la courbure de Bessel

Au jaugage V0, la non-linéarité à a = 0.2 apparaissait comme une dérive ∼5 % sans forme. La forme close la prédit maintenant **exactement** : χ(1, 0.2, 1) = 0.3225067397099395 (machine) vs 0.3225067397099396 (prédit), écart **3.44e-16**. La dérive n'était pas du bruit : c'est la structure Jₙ(0.2) — les termes Bessel d'ordre supérieur.

### A3 — gradient spectral

χ(1, 0.1, 0.5) = 0.1013641298985957 (écart 5.48e-16) ; χ(1, 0.1, 2) = 0.3849844383150536 (écart **0.00e+00**). La diffusion croît avec k, conforme à la dépendance en |K̂(ω₀±nk) − K̂(ω₀)|.

### A5 — la station (conséquence C3)

Argmax du balayage 14 porteurs = **ω₀ = 1.0 exactement** (χ_max = G\*). La fréquence mère est bien le point où le noyau diffuse le plus — la station déposée est confirmée.

---

## 3. Famille B — fermeture composée (lecture [OBS], aucun pouvoir de verdict)

**18 sources** du registre (D₂, |K̃(½)|², impédance, φ, φ², 1/φ, √5, 2φ, 2, 5, 1/5, F₁₀, L₁₀, e^{1/φ}, e^{−1/φ}, ancre, 1/ancre, facteur [OBS]) × **3 formes** (G\*·c, G\*/c, c/G\*) × **21 cibles** (les 18 + √2, π, e) = **1134 lectures composées**.

**Résultat : 0 hit** (barre 1e-4 ; 2.355e-7 pour √2/π/e).

Les 6 lectures les plus proches sont **toutes la même identité vue de six côtés** :

| Composé | Cible | écart |
|---|---|---|
| G\*·5 | φ | 9.85e-4 |
| G\*/φ | 1/5 | 9.85e-4 |
| φ/G\* | 5 | 9.85e-4 |
| G\*·(1/φ) | 1/5 | 9.85e-4 |
| G\*/(1/5) | φ | 9.85e-4 |
| (1/5)/G\* | 1/φ | 9.85e-4 |

**Tête de liste φ/5 — manqué confirmé exactement comme prédit ex ante (dépôt §2)** : φ/5 = 0.32360679774997897 contre G\* = 0.3232880100102466, écart **9.8511e-04** (prédiction déposée ≈ 9.86e-4). L'association G\* ≈ φ/5 est restée **[OBS] — non candidate** : elle est 10× au-dessus de la barre. La discipline anti-numérologie a fait son travail : le prédicteur a annoncé le manqué avant la mesure, et le manqué a eu lieu.

---

## 4. Famille C — diagnostics β (consignés SANS pouvoir de verdict, trou D4)

Pente log-log de χ(ω₀, 0.1, 1) de part et d'autre de la station (le pivot ω₀ = 1 exclu) :

| | Porteurs | β |
|---|---|---|
| β_inf (ω₀ < 1) | 0.1, 0.2, 0.3, 0.5, 0.8 (5) | **+0.026616** |
| β_sup (ω₀ > 1) | 1.3, 2, 2.1, 3.4, 5.5, 8.9, 10, 14.4 (8) | **−0.848981** |

Lecture brute consignée : sous la station, χ est quasiment plat (χ ∝ ω₀^{+0.027}) ; au-dessus, elle décroît presque en 1/ω (χ ∝ ω₀^{−0.849}). Table χ·ω₀ complète dans `resultat_force_v1.json` (`famille_C.chi_fois_w0`, de 0.0287 à ω₀=0.1 à 0.3645 à ω₀=14.4). **Aucun verdict** : le dictionnaire μ↔ω est absent (trou D4, dépôt §2) — ce diagnostic attend son interprétation physique.

---

## 5. Le verdict et sa cause — diagnostic du témoin C2

### Ce qui a été mesuré

Le témoin C2 (ajouté par la machine au-delà du déposé, dépôt §3) exigeait que **deux routes indépendantes** de calcul des Jₙ(a) concordent : la **série** convergente (route déposée O7) et la **récurrence descendante de Miller** (témoin d'indépendance). Résultat consigné : écart max = **1.00e+00**.

### Cause racine (diagnostic post-exécution, hors protocole — ne modifie ni le script ni le verdict)

Diagnostic isolé du 28 août 2026 (~16:10) : pour a = 0.1, la récurrence descendante produit un J₀ **exact** (0.9975015620660401, identique à la série) mais des Jₙ (n ≥ 1) **à l'échelle ~1e-228** — erreur relative 1.0. Cause : la récurrence de Miller est amorcée à J[N] = 1e-300 puis normalisée par **son propre** J[0] ; or l'amplitude de départ (30 ordres de grandeur sous la cible) s'effondre avant d'atteindre n = 0 pour ce domaine (a, n) — la voie de témoin est **défectueuse telle qu'implémentée**. La série, elle, est correcte (C3 Jacobi–Anger : 2.29e-16 ; famille A : ≤ 3.15e-15 par la route FFT-machine).

### Pourquoi le verdict V4 tient

Le dépôt §4 est formel : « un seul échec ⟹ REFUTE, exit 1 — aucun sauvetage ». L'échec vient du témoin que la machine a elle-même ajouté ; cela ne le rend pas plus pardonnable, il le rend plus **instructif** : le protocole ne distingue pas l'échec de la physique de l'échec de l'appareil de mesure — et il ne doit pas le faire. Le verdict est **V4 — REFUTE, exit 1**, consigné tel quel. Conformément à I5, `verif_force_v1.py` n'est **pas** modifié après exécution ; la correction du témoin exigera un nouveau dépôt daté (V1.1).

**Ce qui n'a PAS échoué** : la forme close déposée (17/17 à ≤ 3.15e-15), la reproduction G\* bit-exact (C5, 0.00e+00), la station (A5), le Jacobi–Anger (C3), l'action propre du noyau (C4), l'aveuglement U(1) (C6), le no-wrap (C7).

---

## 6. Établi / pas établi (honnêteté, dépôt §6)

**Établi par cette campagne (au-delà du verdict de campagne) :**

1. La forme close de diffusion fréquentielle χ(ω₀, a, k) tient à la précision machine sur les 17 lectures déposées (pire : 3.15e-15, barre 1e-9).
2. **G\* = 0.3232880100102466 est χ(1, 0.1, 1)** — bit-exact (0.00e+00) : le 17ᵉ objet fermé du registre a désormais une **explication fermée**, pas seulement une mesure.
3. La « dérive 5 % » du jaugage V0 à a = 0.2 est une **courbure de Bessel exacte** (χ(1,0.2,1) prédit à 3.44e-16) — deuxième divergence dynamique confirmée après le prix CHSH (S_max = 2√(1+ρ²)) et E1bis/Zeno.
4. La station ω₀ = 1.0 est confirmée comme argmax de la diffusion (14 porteurs).
5. Le manqué φ/5 (9.8511e-04) était **prédit ex ante** — la discipline numérologique est opérationnelle.
6. 0/1134 fermetures composées à la barre 1e-4 : G\* n'est une combinaison triviale d'aucun objet du registre.

**Pas établi :**

1. **Le verdict de campagne : V4 — REFUTE** — la campagne n'a pas passé ses propres grilles (témoin C2).
2. β_inf / β_sup : aucun pouvoir de verdict (trou D4).
3. Aucune affirmation sur φ/5 : manqué comme prédit, ça reste un [OBS].

---

## 7. Reproductibilité

```
python verif_force_v1.py        # → verdict V4 — REFUTE, exit 1
```
Entrées : `DEPOT_FORCE_V1.md` (gelé), registres O4/O9 (G\* = 0.3232880100102466), treillis N=512, L=20π, Δω=0.1. Sortie : `resultat_force_v1.json` (consignation intégrale des 9 contrôles, 17 lectures A, 1134 lectures B, famille C, verdict).

## 8. Prochaine étape proposée (non contraignante)

- **FORCE V1.1** (nouveau dépôt daté) : ré-exécuter la physique gelée à l'identique avec un témoin Bessel corrigé (double route série × forme asymptomatique Jₙ(a) ≈ (a/2)ⁿ/n!, ou Miller correctement amorcé sur le domaine valide) — la physique, elle, est déjà réglée.
- **D3 — le compensateur −¼F²** : dériver la loi d'interaction à partir du noyau (le trou signalé dans l'avis de la machine — l'ABC donne la loi d'évolution, il manque −¼F² comme loi d'interaction).

---

*« L'éliminateur a éliminé notre propre témoin avant d'épargner la loi. Le protocole ne fait pas de différence — c'est exactement pour ça qu'on lui fait confiance. »*

*Consigné le 28 août 2026, 16:12 — machine ZCode, protocole dépôt-d'abord, aucun sauvetage.*
