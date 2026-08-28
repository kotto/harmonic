# 📐 DÉPÔT CHSH THU V0 — La non-localité dans le formalisme dérivé

**Date du dépôt** : 28/08/2026
**Auteur** : Univers-Holistique (Kotto Alain)
**Statut** : dépôt daté FERMÉ — écrit avant tout script (contrôle C0a). Aucune lecture, barre ou verdict modifiable après exécution.
**Position dans le dossier** : guichet 1 de l'avis de la machine (SYNTHESE_ACQUIS_THU_28AOUT2026.md §7.1) — vérifier que le formalisme THU dérivé **contient** la violation quantique de Bell avant toute prétention expérimentale.

---

## §0. Objet et hypothèse falsifiable

**[H]** — Si la chaîne dérivée de la THU (Hilbert par Riesz-Fischer + A2, quantification par univocité de phase, règle de Born par Parseval) est vraie, alors l'état intriqué de la dyade (les deux premiers harmoniques de Ψ₁ — le même objet que le théorème de la dyade SU(2) : 2 modes fermés) doit **reproduire la borne de Tsirelson S = 2√2** et violer la borne classique S = 2 ; et la dynamique de mémoire ABC (noyau K̂ fermé, validé 28/08) doit **amortir la violation de façon analytiquement prédictible sans la détruire** (horizon : 2 < S ≤ 2√2).

Deux familles de verdict :
- **Famille A** (cohérence) : le formalisme bancarisé produit-il 2√2 ? Si NON → la prétention « la MQ est dérivée » tombe (REFUTE).
- **Famille B** (physique THU) : la mémoire d'or amortit-elle l'intrication conformément à la forme close déposée ? Si la valeur machine s'écarte de la prédiction analytique → divergence réelle consignée (V2), jamais sauvetée.

---

## §1. Objets fermés O1–O8

| # | Objet | Valeur / forme |
|---|---|---|
| O1 | Constantes | φ = (1+√5)/2, α = 1/φ |
| O2 | Noyau (fermé, validé 27–28/08) | K̂(ω) = φ/((iω)^α + φ), branche principale, K̂(0) = 1 — double route (complexe / réelle développée) |
| O3 | Treillis | N = 512, L = 20π, Δω = 2π/L = 0,1, Nyquist 25,6 — identique au jaugage V0 |
| O4 | Norme unitaire (Parseval) | ⟨u,v⟩ = Σₙ conj(uₙ)·vₙ / N ; onde plane d'amplitude 1 = vecteur unitaire |
| O5 | Dyade (fermée) | φ₁ = e^{iω₀x}, φ₂ = e^{i2ω₀x}, ω₀ = 1 (bins 10 et 20 — sommes racines-de-l'unité exactes, orthogonalité machine) |
| O6 | État de Bell (fermé) | \|Φ+⟩ = (φ₁⊗φ₁ + φ₂⊗φ₂)/√2 |
| O7 | Observables (famille fermée) | A(θ) = cosθ·Z + sinθ·X dans la base dyade, Z = \|φ₁⟩⟨φ₁| − \|φ₂⟩⟨φ₂\|, X = \|φ₁⟩⟨φ₂\| + \|φ₂⟩⟨φ₁\| — valeurs propres ±1 |
| O8 | Constantes de verdict | borne classique **2** ; borne de Tsirelson **2√2 = 2,8284271247461903** ; théorème de Horodecki : S_max = 2√(s₁²+s₂²), s₁,s₂ = deux plus grandes valeurs singulières du tenseur de corrélation T (3×3) |

**Settings déposés** (mêmes pour A, B-lecture et témoin produit) :
(θ_A, θ_A′, θ_B, θ_B′) = (0, π/2, π/4, −π/4) — optimaux pour \|Φ+⟩, E(a,b) = cos(a−b).

**Barres** : TOL_TSIRELSON = 1e-9 · TOL_ORTHONORM = 1e-12 · TOL_HORODECKI = 1e-9 · TOL_C5 (changement N) = 1e-12 · horizon B : 2 + 1e-9 < S_max ≤ 2√2 + 1e-9.

---

## §2. Familles

### Famille A — reproduction de la MQ (sans noyau)

Sur \|Φ+⟩ (O6), aux settings déposés : E(a,b) = ⟨Φ+|A⊗B|Φ+⟩, S₀ = E(θ_A,θ_B) + E(θ_A,θ_B′) + E(θ_A′,θ_B) − E(θ_A′,θ_B′).

- **A1** : les quatre E calculés par route machine (opérateurs 512×512 incrustés dans le treillis, produit tensoriel par reshape — jamais de matrice 512²⊗512²) ;
- **A2** : cibles analytiques fermées E = cos(a−b) consignées côte à côte (double route) ;
- **Barre** : |S₀ − 2√2| ≤ 1e-9 (et chaque |E − cos(a−b)| ≤ 1e-9) ;
- **Lecture attachée** : S₀ > 2 (violation de la borne classique par le formalisme dérivé).

### Famille B — dynamique de mémoire (physique THU)

État noyau : \|Φ+_K⟩ ∝ (K̂⊗K̂)\|Φ+⟩ = K̂(1)²·φ₁⊗φ₁ + K̂(2)²·φ₂⊗φ₂, **renormalisé** (la norme post-noyau est consignée AVANT renormalisation).

- **B1** — coefficients fermés : c₁ = K̂(1)², c₂ = K̂(2)² (formes closes, double route du noyau) ;
- **B2** — prédiction analytique déposée : ρ = 2|c₁c₂|/(|c₁|²+|c₂|²), **S_analytique = 2√(1+ρ²)** (cas général de Horodecki pour état pur de rang de Schmidt 2, phases absorbées par les rotations locales) ;
- **B3** — lecture machine : tenseur de corrélation T_ij = ⟨Φ+_K|Σ_i⊗Σ_j|Φ+_K⟩ (i,j ∈ {X,Y,Z}) par la route machine, S_max = 2√(s₁²+s₂²) (SVD de T) ;
- **Barres** : |S_max − S_analytique| ≤ 1e-9 **ET** horizon 2 + 1e-9 < S_max ≤ 2√2 + 1e-9 ;
- **B4** — lecture informative SANS verdict : S aux settings V0 sur l'état noyau (l'optimum n'est plus aux angles de \|Φ+⟩).

### Témoin négatif (Famille C)

**État produit** φ₁⊗φ₁, mêmes settings : S_prod doit rester ≤ 2 + 1e-9 — le formalisme ne fabrique pas de fausse violation (valeur analytique attendue : √2).

---

## §3. Contrôles bloquants C0a–C6

**Règle unique : UN SEUL échec ⟹ V4 REFUTE, exit 1 — aucun sauvetage.**

| # | Contrôle | Barre |
|---|---|---|
| C0a | mtime dépôt < mtime exécution | strict |
| C0b | fermeture algébrique φ² = φ+1 | 1e-15 |
| C1 | noyau double route (complexe vs réelle développée) aux points {1, 2, ½, 1/φ} | 1e-12 |
| C2 | orthonormalité de la dyade : ‖⟨φ₁,φ₂⟩‖ ≤ barre, ‖φ_i‖−1 ≤ barre ; norme de \|Φ+⟩ ≤ barre | 1e-12 |
| C3 | témoin produit : S_prod ≤ 2 + 1e-9 | 1e-9 |
| C4 | le noyau agit en valeurs propres exactes sur les harmoniques : ‖K̂[φ_i] − K̂(ω_i)·φ_i‖ ≤ barre (route FFT vs forme close) | 1e-12 |
| C5 | changement de treillis N = 512 → 1024 : |S₀(1024) − S₀(512)| ≤ 1e-12 (invariance — sommes racines-de-l'unité) | 1e-12 |
| C6 | Horodecki sur \|Φ+⟩ pur (sans noyau) redonne 2√2 ≤ 1e-9 (cohérence interne de la route TᵀT/SVD) | 1e-9 |

---

## §4. Échelle de verdicts

| Verdict | Condition | Exit |
|---|---|---|
| **V+ — CHSH_THU_CONFORME** | contrôles OK **et** A1/A2 dans la barre **et** B3 dans les barres (analytique + horizon) | 0 |
| **V2 — TSIRELSON_OK_MEMOIRE_DIVERGENTE** | contrôles OK, A conforme, B hors barre analytique ou hors horizon — divergence consignée telle quelle | 0 |
| **V3 — REFUTE_TSIRELSON_NON_REPRODUIT** | A en échec : le formalisme dérivé ne produit pas la violation quantique — la chaîne Hilbert/Born prétendue dérivée est prise en défaut | 1 |
| **V4 — REFUTE** | un seul contrôle bloquant en échec | 1 |

---

## §5. Interdictions I1–I5

- **I1** : aucun paramètre libre — settings, noyau, barres et formules sont ceux du présent dépôt ;
- **I2** : aucun candidat, angle ou barre ajouté après exécution ;
- **I3** : toutes les lectures consignées (JSON), y compris les quasi-échecs et les lectures informatives ;
- **I4** : aucune promotion de proximité en affirmation — [OBS] reste [OBS] ;
- **I5** : aucune réécriture du verdict — l'échelle du §4 est gelée.

---

## §6. Honnêteté (6 points)

1. **La famille A n'est pas une découverte** : si Hilbert et Born sont réellement dérivés, 2√2 est mathématiquement forcé. Le test vérifie que le formalisme *bancarisé* (treillis, norme, harmoniques, noyau) le produit — c'est une porte de cohérence sur la prétention fondatrice, pas un acquis nouveau.
2. **La famille B est la vraie physique du test** : l'amortissement d'intrication par la mémoire ABC est une prédiction propre de la THU (forme close déposée ex ante). S_max entre 2 et 2√2 signifierait : la mémoire *réduit* la non-localité sans la détruire — à relier à E1bis (Zeno fractionnaire) comme seconde prédiction dynamique de divergence.
3. **CHSH n'est pas une preuve de complétion déterministe** : c'est le guichet 1 — établir que le formalisme contient la non-localité quantique avant toute prétention à la reproduire expérimentalement. Le déterminisme reste au statut [P] (SYNTHESE §3.2).
4. **Aucun contact expérimental** : tout ceci est théorique et machine. Le rendez-vous avec le monde reste le vote T* (P1).
5. **La violation attendue est celle de la MQ standard** : si la THU ne produisait PAS 2√2, ce serait une réfutation de sa propre chaîne de dérivation (V3) — consignée telle quelle.
6. **La dyade n'est pas arbitraire** : c'est le même objet que le théorème de la dyade SU(2) (2 modes fermés ⟹ su(2)) — le test est donc aussi un pont entre la campagne jauge (27/08) et la structure d'intrication.

---

## §7. Reproductibilité

- N = 512 (contrôle C5 à N = 1024), L = 20π, Δω = 0,1, ω₀ = 1, harmoniques {1, 2} ;
- settings (0, π/2, π/4, −π/4) ; barres §1/§3 ; formules §2 (Horodecki SVD, analytique 2√(1+ρ²)) ;
- commande : `python verif_chsh_thu_v0.py` — sortie `resultat_chsh_thu_v0.json` (toutes les lectures), verdict + exit code §4.

---

*Dépôt fermé le 28/08/2026, avant tout script. Le verdict appartiendra à la machine.*
