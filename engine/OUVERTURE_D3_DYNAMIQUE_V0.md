# OUVERTURE D3 DYNAMIQUE — document d'entrée de chantier

**Rédigé le 03/09/2026** · objectif : permettre à une session neuve de commencer D3
(dynamique) sans ré-exploiter tout l'historique. Ce document ne gèle AUCUNE barre
nouvelle — il cartographie le terrain et l'ordre d'exécution. Les barres de D3
dynamique seront gelées dans `FRONTIERE_D3_DYNAMIQUE_V0.md`, AVANT tout script (C0a).

---

## 1. La carte des trous — où vit D3

Carte héritée de la campagne JAUGAGE (28/08, `DEPOT_JAUGAGE_V0.md` §6) :

| Trou | Objet | Statut |
|---|---|---|
| D1 — localisation | liberté locale ψ↦e^{iα(x)}ψ | **fermé structurellement** : U(1) exact 1,1e−16, défaut gradient-porté, linéaire (A3, V3 exit 0) |
| D2 — la force | nom du défaut | **FERMÉ** : G* = χ(1,0,1,1) = 0,32328801 = diffusion fréquentielle du noyau (FORCE V1.3, V+ exit 0, 17/17 ≤ 3,15e−15 ; 17ᵉ objet fermé) |
| **D3 — compensateur dynamique** | A se propage | **statique FERMÉ (F13 exit 0) / dynamique OUVERT** ← LE CHANTIER |
| D4 — dictionnaire μ↔ω | relier ω aux échelles physiques | ouvert (β_pred = −0,4655 consigné sans verdict) |

## 2. Ce que D3-dynamique hérite (tout déjà machine-vérifié)

1. **F13 MÈRE V0** (`DEPOT_F13_MERE_V0.md`, verdict F13_MERE_COMPENSATEUR_EXACT exit 0,
   21/21 contrôles, run du 02/09) :
   - P30 identité mère φ·K̂⁻¹−φ=(iω)^α ; P31 Schrödinger assemblé (Bateman, Stone, station ω₀=1) ;
   - **P32 compensateur exact** K̂_A = φ·(D_A+φ)⁻¹, D_A = D−iA, A=∇χ : absorption
     EXACTE de la jauge, triple route (dérivée 4,7e−13 / noyau 2,4e−14 / boucle 1,1e−11) ;
   - P35 **spectre du connecteur** : rang transverse = 2 par mode k≠0 ; eigenvalue de
     boucle à α=1 : λ = −|k|² (massif zéro), phase πα = π ;
   - **C6b ex ante** : arg(iω)^{2/φ}/π = 1/φ **bit-exact** aux 5 fréquences — la
     statistique continue en α ; dépôt mpmath i^{2/φ} = −0,36237489… + 0,93203242…j.
2. **FORCE V1.3** (`RESULTAT_FORCE_V1_3.md`, V+ exit 0) : le défaut de rephasage modulé
   EST la diffusion fréquentielle de Bessel χ(ω₀,a,k) — la force a une forme close.
3. **INTERACTION D3 V0** (`DEPOT_INTERACTION_D3_V0.md`, déposé le 28/08 17:20 —
   **JAMAIS EXÉCUTÉ** : absence de `verif_interaction_d3_v0.py` et
   `resultat_interaction_d3_v0.json` vérifiée le 03/09) : résonance n−m=j,
   I₁₂ = Re[i^{−j}Z_j], parité alternée i^{−j} = **graine antisymétrique type-F²**,
   amendement §0-bis (bandes latérales, paire (−1,−1) résonnante pour la famille B).
   **Échelle de verdicts §3 déjà gelée — C0a déjà satisfait** (mtime 28/08 17:20 < toute
   exécution future).
4. **HAMILTONIEN ABC V0** (`DEPOT_HAMILTONIEN_ABC_THU_V0.md`, exit 0 6/6) : la mémoire
   est un **système ouvert** (λ=(iω)^α non-hermitien, PT brisé) — le seul branchement
   quantique possible est la **phase d'influence Feynman-Vernon** ; Bateman double ;
   **franges décalées de 90/φ degrés, indépendantes de T** (signature falsifiable).
5. **CHSH V0** (`RESULTAT_CHSH_THU_V0.md`, V+ exit 0) : Tsirelson 2√2 (1,33e−15) ;
   amortissement mémoire **S_max = 2√(1+ρ²) < 2√2** (8,9e−16) — la seule prédiction
   discriminante du programme.
6. **GENERALISATION_D1PHI_GAUGE_5_DOMAINES** : D^{1/φ}[Ψ]=G[Ψ] prouvé spin-2 à 1e−15 —
   le mécanisme « mémoire = contrainte spatiale » existe déjà (face gravitation).

## 3. La question du chantier (une phrase)

**Le compensateur doit évoluer, pas seulement absorber** : dériver l'équation
d'évolution de A depuis le noyau — sans postuler Maxwell, sans l'injecter — avec deux
discriminants attendus : **réduction à Maxwell à α=1** (onde, rang 2, massif zéro) et
**propagation modifiée par la mémoire à α=1/φ** (λ=(iω)^{2/φ}, phase π/φ native, pont FV).

## 4. Ordre d'exécution proposé

| Étape | Contenu | Statut |
|---|---|---|
| **1** | **Exécuter INTERACTION D3 V0** — écrire `verif_interaction_d3_v0.py` (contrôles C0a–C7 du dépôt §1, conséquences C1–C6 §0, verdicts §3 gelés) ; compile-check ; run ; verdict ; `DEPOT/RESULTAT` ; commit | dépôt déjà fermé, prêt |
| **2** | **FRONTIERE_D3_DYNAMIQUE_V0.md** — thèse falsifiable + barres gelées AVANT exécution (C0a) ; annule/remplace explicitement ce que §5 F13 interdisait (nom G*, −¼F², D4 restent hors périmètre sauf dépôt daté) | à faire |
| **3** | Script D3 dynamique → run → verdict exit 0/1 → DEPOT → commit fichiers de tâche uniquement | à faire |

## 5. Thèse candidate à geler en étape 2 (direction, pas engagement)

Forme falsifiable proposée : l'identité mère doit **forcer** l'évolution de A —
à α=1, le spectre transverse du connecteur (rang 2, λ=−|k|², phase π) doit produire
l'équation d'onde (Maxwell émerge, massif zéro) ; à α=1/φ, λ=(iω)^{2/φ} produit une
propagation à mémoire (dérivée fractionnaire, phase π/φ) qui doit recouper le pont
Feynman-Vernon et l'amortissement S_max = 2√(1+ρ²). **Critère anti-rétro-ingénierie** :
A doit sortir de l'identité mère (conséquence), jamais y entrer (ingrédient). Si
l'équation d'évolution nécessite un terme « mangé » (−¼F² écrit à la main), la
campagne le consigne comme non-émérgé — REFUTE du niveau visé.

## 6. Interdictions et honnêteté (verbatim héritées)

- **C0a** — FRONTIÈRE avant script (mtime faisant foi) ; un seul contrôle en échec
  ⟹ REFUTE exit 1, aucun sauvetage.
- **Leçon V1.2** — tout nombre déposé est calculé par machine avant gel ; tout
  estimateur est bugable : bugs consignés, barres inchangées, physique jamais retouchée.
- **I4 INTERACTION D3** — la graine parité/résonance n'est PAS −¼F² ; la montée au
  terme continu (intégration des modes, limite adiabatique, facteur ¼) est une
  campagne SÉPARÉE.
- Restent hors périmètre : nom fermé pour G* (φ/5 reste [OBS]), D4, électrofaible,
  spin ½/Dirac, P4 (lecture probabiliste de Born), dérivation d'α (axiome — trois
  familles d'arguments testées, non-sélections consignées : JACOBSON C4, KMS C4,
  HAMILTONIEN C6).

## 7. Fichiers d'entrée de session

- `OUVERTURE_D3_DYNAMIQUE_V0.md` — ce document.
- `DEPOT_INTERACTION_D3_V0.md` — dépôt fermé **en attente d'exécution** (étape 1).
- `FRONTIERE_F13_MERE_V0.md` / `DEPOT_F13_MERE_V0.md` / `resultat_f13_mere_v0.json` —
  l'état statique D3 (P30–P35, 21/21).
- `DEPOT_JAUGAGE_V0.md` + `RESULTAT_JAUGAGE_V0.md` — la carte des trous, G* sans nom.
- `DEPOT_FORCE_V1_3.md` + `RESULTAT_FORCE_V1_3.md` — la force fermée (Bessel).
- `DEPOT_HAMILTONIEN_ABC_THU_V0.md` — mémoire = ouvert, pont FV, franges 90/φ°.
- `RESULTAT_CHSH_THU_V0.md` — S_max = 2√(1+ρ²), prédiction discriminante.

---

> *Le compensateur absorbe exactement (F13 exit 0). Le chantier D3 exige maintenant
> qu'il se propage : si l'onde sort de la boucle à α=1 et que la mémoire la déforme
> à α=1/φ, Maxwell n'aura pas été postulé — il aura coulé. Un dépôt, une barre, un verdict.*
