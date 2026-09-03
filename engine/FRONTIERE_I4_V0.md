# FRONTIÈRE I4 V0 — la montée vers le terme continu −¼F² : le facteur ¼ sort des identités de Bessel, jamais écrit à la main

## Montée vers −¼F² — le facteur ¼ émerge de la famille de résonance paire (j=2), ou la campagne consigne non-émérgé

**Auteur :** Alain Kotto (Univers-Holistique)
**Version :** I4-1.0
**Statut :** Frontière ouverte — cahier des charges déposé AVANT tout script (contrôle C0a ; mtime faisant foi)
**Références :** `OUVERTURE_D3_DYNAMIQUE_V0.md` §6.2 (I4 = campagne séparée, critère de réfutation),
`DEPOT_INTERACTION_D3_V0.md` §5 + §104-110 (la graine n'est PAS −¼F² ; règle de consignation de la
fuite), `RESULTAT_INTERACTION_D3_V0.md` (forme close I₁₂ = Re[i^{−j}Z_j]/N, V2 exit 0),
`FRONTIERE_D3_DYNAMIQUE_V0.md` (P36–P38, propagation coulée, V+ exit 0, commit 20d8b22),
`DEPOT_F13_MERE_V0.md` §5 (terme continu −¼F² dérivé : **non établi** — pas de −¼F² dérivé, pas de
dictionnaire μ↔ω), `DEPOT_JAUGAGE_V0.md` (V3 = COVARIANCE_LOCALE_DERIVEE_FORCE_SANS_NOM ; I4 sans
empiètement), `BREVET_THEORIE_HARMONIQUE_UNIVERS_V5.md` l.399 (I₁₂ = Re⟨δ₁,δ₂⟩ « prémisse d'une loi
d'interaction du type −¼F² »)

---

## 0. POSITION — ce que cette campagne attaque (et ce qu'elle n'attaque pas)

Trois dépôts nomment la même dette : INTERACTION D3 V0 (§5) — *la graine n'est pas −¼F² ; le terme
continu est une campagne séparée* ; D3 DYNAMIQUE (frontière §6.2) — *−¼F² reste campagne séparée (I4)* ;
F13 §5 — *pas de −¼F² dérivé*. Le 03/09, la chaîne noyau → interaction → propagation est bit-exact
continue, et le couplage I₁₂ = Re⟨δ₁,δ₂⟩ est déposé comme prémisse d'une loi du type −¼F². **Il reste
le trou** : la **montée** de la graine discrète vers le terme continu −¼F² (intégration sur les modes,
limite adiabatique, facteur ¼).

**La question du chantier (une phrase)** : le facteur ¼ du terme continu sort-il des identités de
Bessel de la graine déposée — sans jamais être écrit à la main — ou faut-il l'injecter ?

**Périmètre précis :** la structure du couplage I₁₂ entre deux porteurs jaugés au niveau spectral et
discret (grille O3, opérateurs machine), dans la limite adiabatique k→0 et à la tranche α=1 du poids
unique. Pas la dérivation d'un lagrangien continu (fonctionnelle), pas la quantification, pas le
dictionnaire μ↔ω (D4), pas le système 3+1D covariant avec sources.

## 0-bis. ANNULE/REMPLACE (explicite)

| Objet | Statut F13 §5 / D3 §0-bis | Statut I4 V0 |
|---|---|---|
| Terme continu −¼F² dérivé | interdit / campagne séparée (I4) | **ATTAQUÉ dans le seul périmètre : structure du couplage discret en limite adiabatique à la tranche α=1** — c'est le chantier |
| Dérivation d'un lagrangien continu (intégrale fonctionnelle) | interdit | **MAINTENU interdit** — I4 teste la montée de la graine, pas un lagrangien continu |
| D4 (dictionnaire μ↔ω) | ouvert, non attaqué | **MAINTENU hors périmètre** |
| Quantification, spin ½, électrofaible, P4, dérivation d'α | hors périmètre | **MAINTENUS hors périmètre** |

**Critère de réfutation (verbatim OUVERTURE §6.2)** : si l'évolution/couplage nécessite un terme
−¼F² **écrit à la main** (ingrédient du code), la campagne consigne *non-émérgé* → REFUTE du niveau
visé. Inversement, si le facteur ¼ sort des identités de Bessel mesurées, la montée est fermée au
niveau visé.

## 1. LA THÈSE (Q1–Q5) — falsifiable, une seule source spectrale

- **Q1 (identités exactes — le ¼ vit dans la famille paire)** — les sommes de Bessel de la graine,
  machine (série O7, parité J₋ₙ = (−1)ⁿJₙ), satisfont **exactement** :
  S₂(a) = Σₘ m(m+2)·J_{m+2}(a)·J_m(a) = **a²/4** ; A₂ = Σₘ m²(m+2)·JJ = **−a²/4** ;
  V₂ = Σₘ m(m+2)²·JJ = **a²/4** ; W₂ = Σₘ m²(m+2)²·JJ = **(a⁴−a²)/4** ;
  S₁ = S₃ = W₁ = **0**. Le facteur ¼ de la famille paire j=2 est une **identité de Bessel**, pas un
  choix. (Sondes 03/09 : écarts ≤ 1.7e-16 sur a ∈ {0.1, 0.3, 0.5, 1.0, 1.3}.)
- **Q2 (à α=1, le formulaire polynomial est exact pour tout k)** — à α=1, Δₙ^loop(ω) =
  λ_loop(ω+nk) − λ_loop(ω) = **−(ω+nk)² + ω² = −2ωnk − (nk)²** : polynôme **exact**, aucun reste de
  Taylor. Le défaut de couplage de la famille paire j=2 (résonance n−m=2, collisions de bins exactes)
  prend alors la forme close
  **Z₂ = k²·[4ω₁ω₂·S₂ + 2k·(ω₁A₂ + ω₂V₂) + k²W₂] = (a²k²/4)·[4ω₁ω₂ + 2k(ω₂−ω₁) + k²(a²−1)]**,
  exacte pour tout k (pas seulement adiabatique), et **I₁₂^réseau = Re⟨d₁,d₂⟩ = −Re Z₂/N** (parité
  INTERACTION §0-bis, pont norme /N — leçon V1.2, troisième occurrence, structurelle).
  Sur la famille adiabatique ω₂ = ω₁+2k : **I₁₂ = −(a²k²/4N)·[4ω₁ω₂ + k²(a²+3)]**.
- **Q3 (structure paire — les familles impaires sont exactement muettes à α=1)** — à α=1 tous les Δ
  sont réels ⟹ Z_j réel ⟹ le canal impair I₁₂(j impair) = Re[i^{−j}Z_j]/N = ±Im Z_j/N = **0 exactement**.
  Le couplage est **purement quadratique (pair)** dans la structure de jauge : c'est la signature
  −¼F² (quadratique), pas −F (linéaire). (Sondes : |Re I₁₂(j=1,3)| ≤ 6.6e-20 sur réseau, contre
  Re Z_j ≠ 0 — la partie Im⟨d₁,d₂⟩ = −Re Z_j/N est non-observable, consignée [OBS].)
- **Q4 (montée adiabatique — la forme continue −¼F²)** — avec 𝔽_i := a·k·ω_i (force du mode de jauge
  a,k agissant sur le porteur ω_i) : **I₁₂/(−𝔽₁𝔽₂/N) = 1 + k²(a²+3)/(4ω₁ω₂)** — exact (corollaire de
  Q2). Dans la limite adiabatique k→0, le couplage tend vers **−𝔽₁𝔽₂/N = −4·S₂·k²ω₁ω₂/N** : le facteur
  ¼ est sorti de l'identité Q1, jamais écrit dans la machine.
- **Q5 (hors α=1, montée générique seulement)** — aux niveaux noyau (K̂) et boucle α=1/φ, les Δ ne
  sont pas polynomiaux : seule la structure adiabatique générique tient,
  I₁₂ ≈ −k²·S₂·Re[conj(W′(ω₁))·W′(ω₂)] (conjugaison sur canal 1), ratio → 1 quand k→0, **sans
  formulaire polynomial** : la fermeture continue −¼F² est la tranche **α=1** du poids unique ;
  le régime mémoire α=1/φ ne se réduit pas à −¼F² (consigné, pas réfuté).

**Critère anti-rétro-ingénierie (verbatim OUVERTURE §5)** : *A doit sortir de l'identité mère
(conséquence), jamais y entrer (ingrédient).* Le formulaire (a²k²/4)[…] est l'objet **falsifié**,
jamais un ingrédient : la route machine (zj_loop, couple réseau) est construite uniquement sur
lambda_weight (poids unique), loop_weight = λ², j_signed et les normes O5 — les sommes S₂, A₂, V₂, W₂
du formulaire sont **mesurées** par la machine, et leur identité à a²/4, −a²/4, a²/4, (a⁴−a²)/4 est un
**contrôle séparé** (C3). Aucun ¼ codé en dur dans la route machine. Le code contient un seul poids
spectral ; tout terme −¼F² écrit comme ingrédient rend la campagne non-émérgée → REFUTE.

## 2. CONVENTIONS (verbatim héritées)

1D : N = 512, L = 20π, Δω = 0.1, Nyquist 25.6, porteur e^{iωx}/√N, norme ‖ψ‖² = Σ|ψₙ|²/N,
⟨u,v⟩ = vdot/N (forme close comparée au niveau **norme**, facteur 1/N). Boucle L = D_α∘D_α, poids
λ_loop = λ_kernel² (site unique de mise au carré) ; à α=1 : λ_loop(ω) = −ω². Jauges : famille
χ = a·cos(kx). Sommes de Bessel : série log-sûre + parité J₋ₙ = (−1)ⁿJₙ ; TRUNC_I4 = 20 (sommes Z_j),
M_id = 40 (identités). **Grille I4 gelée** : a ∈ {0.1, 0.5, 1.0, 1.3} ; k ∈ {0.1, 0.2, 0.5, 1.0} ;
ω₁ ∈ {0.5, 1.0, 2.0} ; famille j=2 : ω₂ = ω₁+2k (résonance n−m=2, tous modes sur grille Δω=0.1) ;
familles impaires j∈{1,3} : ω₂ = ω₁+j·k, (a,k) ∈ {0.1,1.0}×{0.1,0.5}, ω₁=1.0.

## 3. CONTRÔLES BLOQUANTS (gelés avant exécution)

| # | Contrôle | Barre |
|---|---|---|
| C0a | mtime(`FRONTIERE_I4_V0.md`) < heure d'exécution (horodatages au JSON) | — |
| C0b | φ² = φ+1 | 1e-15 |
| C1 | K̂ double route (complexe vs réelle), grille O3 + {½, 1/φ, 1, 2} ; branche K̂(−ω)=conj | 1e-12 |
| C2 | Bessel double route : série×récurrence ; identité paire J₀+2ΣJ₂ₖ=1 | 1e-12 / 1e-9 |
| C3 | **identités Q1** : S₂=a²/4, A₂=−a²/4, V₂=a²/4, W₂=(a⁴−a²)/4, S₁=S₃=W₁=0 — mesures vs valeurs closes, 5 valeurs de a | 1e-15 abs |
| C4 | **formulaire Q2** : Z₂^zj(loop α=1) vs forme k²[4ω₁ω₂S₂+2k(ω₁A₂+ω₂V₂)+k²W₂] (sommes **mesurées**), 48 lignes de grille | 1e-12 rel |
| C5 | **réseau vs forme** : Re⟨d₁,d₂⟩ (route FFT, LG1) = −forme/N, 48 lignes | 1e-12 rel |
| C6 | **silence impaire Q3** : \|Re I₁₂(j=1,3)\| ≤ barre, 8 lignes | 1e-15 abs |
| C7 | **adiabatique noyau Q5** : ratio I₁₂/(−k²S₂Re[conj K̂′(ω₁)]K̂′(ω₂)) ∈ [0.95, 1.05], (ω₁,k) ∈ {1,2}×{0.1,0.2,0.3} | [0.95, 1.05] |
| C8 | **adiabatique boucle 1/φ Q5** : ratio I₁₂/(−k²S₂Re[conj L′(ω₁)]L′(ω₂)) ∈ [0.95, 1.05], mêmes 6 lignes | [0.95, 1.05] |
| C9 | no-wrap \|ω±nk\| ≤ 25.6 pour toute lecture (max 24.0 sur la grille I4) | — |
| C10 | **filiation** : λ_loop = λ_kernel² bit-exact sur la grille O3 ; un seul poids spectral dans le code (structurel, anti-rétro-ingénierie) | 0 (bit-exact) |

**Règle unique : UN SEUL contrôle en échec ⟹ REFUTE, exit 1, aucun sauvetage.**

## 4. CONSÉQUENCES FALSIFIABLES (barres gelées avant exécution)

### D1 — le facteur ¼ émerge (montée vers −¼F², famille j=2)

| # | Conséquence | Barre |
|---|---|---|
| D1a | **montée exacte** : I₁₂^réseau/(−𝔽₁𝔽₂/N) = 1 + k²(a²+3)/(4ω₁ω₂) sur 8 lignes (a∈{0.1,1.0}, k∈{0.1,0.2}, ω₁∈{0.5,1.0}) — le ratio tend vers 1 et son écart suit la forme close | 1e-12 |
| D1b | **forme famille** : I₁₂ = −(a²k²/4N)·[4ω₁ω₂ + k²(a²+3)] sur la même grille — le ¼ devant le crochet vient de S₂ = a²/4 (C3), pas du code | 1e-12 rel |
| D1c | **limite adiabatique** : à k→0, I₁₂ → −𝔽₁𝔽₂/N avec 𝔽_i = a·k·ω_i — ratio ∈ [0.95, 1.10] à k ≤ 0.2 sur la grille D1a (l'écart maximal mesuré est 8.9e-2 à k=0.2, ω₁=0.5) | [0.95, 1.10] |

### D2 — structure quadratique (le −¼F² est pair)

| # | Conséquence | Barre |
|---|---|---|
| D2a | les familles impaires (j=1, j=3) sont exactement muettes à α=1 (C6) : le couplage est purement quadratique dans la structure de jauge — signature −¼F², pas −F | = C6 |
| D2b | les parties Im⟨d₁,d₂⟩ des familles impaires valent −Re Z_j/N ≠ 0 (canal orthogonal, non-observable I₁₂) — consigné sans pouvoir de verdict | [OBS] |

### D3 — hors α=1 : montée générique, pas de fermeture

| # | Conséquence | Barre |
|---|---|---|
| D3a | noyau et boucle α=1/φ : ratio adiabatique → 1 quand k→0 (C7/C8 : 0.988–1.009 mesuré) — la structure conj(W′₁)W′₂ tient | = C7/C8 |
| D3b | **pas de formulaire polynomial hors α=1** : le ratio C7/C8 s'écarte de 1 à k fini (≥ 5e-3 à k=0.3) — la fermeture −¼F² continue est la tranche α=1, pas la mémoire | [OBS] |

## 5. VERDICTS (échelle gelée avant exécution)

- **V+ I4_MONTEE_QUART_FERMEE** — exit 0 — contrôles OK ET D1(a–c) ET D2a ET D3a
- **V2 I4_QUART_SEUL** — exit 0 — contrôles OK, D1 OK, (D2a ou D3a) hors barre
- **V3 REFUTE_I4_SANS_QUART** — exit 1 — contrôles OK, ≥1 de D1 hors barre (le ¼ n'émerge pas)
- **V4 REFUTE** — exit 1 — tout contrôle bloquant en échec

Un seul échec (contrôle OU conséquence) ⟹ REFUTE — aucun sauvetage. Tout estimateur est bugable :
un bug d'estimateur consigné n'est pas une physique réfutée (barres gelées inchangées — leçon FORCE
V1.1/V1.2/V1.3). Lectures [OBS] : consignées, sans pouvoir de verdict.

## 6. HONNÊTETÉ — ce que I4 V0 ne prouve pas

1. **Pas de lagrangien continu dérivé** : I4 ferme la structure du couplage **discret** en limite
   adiabatique à la tranche α=1 — pas la dérivation d'un terme −¼F² d'un lagrangien continu sur un
   champ A(x) continu (intégrale sur les modes complète, système 3+1D covariant avec sources : hors
   périmètre, D4/JAUGAGE).
2. **La lecture « Maxwell » reste structurelle** : I₁₂ = −(a²k²/4N)[…] est une loi de couplage
   entre porteurs jaugés sur treillis ; l'identification au terme de Maxwell −¼F_{μν}F^{μν} est une
   analogie de forme (quadraticité, facteur ¼, limite adiabatique), déposée comme telle — pas une
   identification d'équations.
3. **Le régime mémoire α=1/φ ne ferme pas** : seul le lead adiabatique générique tient (C7/C8) ;
   consigné — c'est le discriminant mémoire/Maxwell vu depuis le couplage.
4. **La partie impaire Im⟨d₁,d₂⟩ ≠ 0** est non-observable dans I₁₂ (consignée D2b) ; son statut
   physique éventuel est hors campagne.
5. **Les ancres restent internes** (a, k, ω de la famille fermée) — I4 ne produit pas de mesure de
   laboratoire ; auto-cohérence, pas yet physique (leçon de la conclusion D3, hors protocole).

## 7. REPRODUCTIBILITÉ (spécifiée avant exécution)

- Script : `verif_i4_v0.py` (autonome, verbatim O1–O7 hérité + sections I4), exécution
  `python verif_i4_v0.py`, sortie `resultat_i4_v0.json`. Aucune graine aléatoire — tout est
  déterministe (FFT, séries, sommes).
- Ordre C0a : frontière commitée AVANT création du script (mtime faisant foi, antériorité au JSON).
- Environnement : Python + NumPy, horodatés au JSON. Durée cible < 120 s.
- Chaîne de dépôts : OUVERTURE_D3_DYNAMIQUE_V0.md (§6.2) → DEPOT_INTERACTION_D3_V0.md (§5) →
  FRONTIERE_I4_V0.md (ce document) → verif_i4_v0.py → RESULTAT_I4_V0.md + resultat_i4_v0.json.

---

*Barres gelées avant exécution. Le facteur ¼ doit sortir des identités — jamais y entrer.*