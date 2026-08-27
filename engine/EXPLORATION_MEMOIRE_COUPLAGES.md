# 🔍 EXPLORATION — LA MÉMOIRE SÉPARE-T-ELLE LES COUPLAGES ?

**Date** : 2026-08-27 · **Script** : `exploration_memoire_couplages.py` (exit 0, cohérence interne T0 OK) · **Données** : `resultat_exploration_memoire.json`
**Amont** : `DEPOT_ALPHA_VERTEX.md` + `verif_alpha_vertex.py` (assaut vertex, piste v1 réfutée) · **Statut** : exploration [P]/[OBS] — aucun verdict d'assaut, aucune revendication numérique.

---

## 0. La question

L'assaut vertex du 27/08 a laissé un fait brut : la lecture géométrique pure reproduit
**α_W = 1/30 exactement** pendant qu'α_EM résiste aux 15 lectures. Si la mémoire d'or
est ce qui sépare les deux couplages, cela doit apparaître dans la structure même des
trois formules du registre — et dans les impédances du noyau mesurées par l'assaut.

## 1. L'hypothèse triadique (ancrage corpus)

| Couplage | Groupe | Relation à la mémoire | Formule corpus | Mesure |
|---|---|---|---|---|
| α_W | SU(2) — dyade, double-cover géométrique (`THEOREME_DYADE_SU2.md`) | **Aucune** — vertex géométrique pur | (√2·√3·√5)⁻² | 1/30 **exacte** |
| α_EM | U(1) — **la phase de la projection à mémoire elle-même** (`MAILLON3_PROJECTION.md` §7 : la liberté résiduelle de la projection *est* la jauge U(1)) | **Le porteur** — mixte | π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵ (dans α⁻¹) | 1/137.036 |
| α_S | SU(3)/spin-2 — la dynamique de mémoire pure (`R3_QUANTIFICATION_FRACTIONNAIRE.md`) | **Totale** — confinement = mémoire infinie | 1/(2φ³) | 0.118034 (PDG m_Z) |

**Lecture** : les trois couplages sont trois relations au noyau de mémoire —
sans mémoire (W), la ligne de mémoire (EM), la mémoire comme contenu (S).
L'identification U(1) = ligne de mémoire n'est pas une analogie : c'est le
théorème de projection du Maillon 3 (la phase résiduelle est la jauge).

## 2. Ce que la machine a mesuré

| Test | Résultat | Statut |
|---|---|---|
| T0 Formules du registre recalculées | 5-facteurs = 137.036031356 (3.1×10⁻¹² vs canonique ; 2.35×10⁻⁷ vs CODATA) | ✅ cohérence |
| T1 place de φ | α_W : **absente** (0.000) · α_EM : φ⁻⁵ → fraction **−0.489** de ln α⁻¹ · α_S : φ⁺³ pur → **+0.676** | 📊 tripartition, pas échelle |
| T2a impédance continue au vertex | \|K̃(ω₀/2)\|² = **0.401152** (pipeline validé C3 à 1.1×10⁻⁸) | 📏 |
| T2b mode ½ discret | transparent : φ+φ⁻¹ = √5 (0.0e+00) → réponse 1 | ✅ |
| T2c séparation quantitative | α_W/α_EM = 4.568 vs impédance 1/0.4012 = 2.493 → **facteur 1.832** | ⚠️ qualitatif seul |
| T3 règle produit α_EM = α_W·α_S·K | K* = 1.854725 ; meilleur de la famille fermée : **e^(1/φ) = 1.855277, écart 2.98×10⁻⁴** ; 0 hit à 1e-4 | ❌ rien à revendiquer |
| T4 mélange d'échelles | sin²θ_W implicite : 0.2189 (Thomson, écart **5.32 %**) → 0.2345 (m_Z, écart **1.40 %**) ; α_W registre = 1.70 % de α_W(m_Z) réelle | 🔧 correction registre |
| T5 résidus indépendants | F₁₀ : 5.04×10⁻⁴ vs e^(1/φ) : 2.98×10⁻⁴ → **distincts** (2.06×10⁻⁴ d'écart) | pas de piste commune |

## 3. Ce que l'hypothèse explique

1. **L'exactitude d'α_W s'explique structurellement** [P] : c'est le seul couplage
   sans φ — un vertex qui ne traverse pas la ligne de mémoire. L'assaut vertex
   l'avait déjà montré operationnellement : lecture (c,30) exacte avec la patte
   temps transparente. Le faible oublie ; l'électromagnétisme se souvient.
2. **α_EM est le couplage de la mémoire elle-même** [P] : seul couplage dont
   l'inverse porte φ avec signe négatif (φ⁻⁵ dans α⁻¹ — la mémoire amplifie EM).
   Cohérent avec U(1) = liberté de phase résiduelle de la projection à mémoire.
3. **α_S est fait de la mémoire** [P] : φ³ pur, aucune constante géométrique ;
   le confinement = le noyau qui n'oublie rien (R3 : propagateur adouci, mémoire cumulée).
4. **Le mélange d'échelles est réel et corrigeable** [OBS] : à échelle m_Z
   appariée, les écarts tombent de 5.3 % à 1.4 % (sin²θ_W) et 1.7 % (α_W).

## 4. Ce que l'hypothèse n'explique PAS (honnêteté)

- L'impédance mesurée ne chiffre pas le rapport : α_W/α_EM = 4.568 =
  (1/0.401152) × **1.832** — le facteur 1.832 reste sans nom dans le corpus.
- La règle produit α_EM = α_W·α_S·e^(1/φ) résiste à 2.98×10⁻⁴ — au-dessus de la
  barre 1e-4 du dépôt vertex ; aucun membre de la famille fermée ne passe.
- Les deux résidus ~10⁻⁴ indépendants (F₁₀ et e^(1/φ)) sont **distincts** :
  il n'y a pas une correction commune à traquer, il y a (au moins) deux trous.

## 5. Prochaine question quantifiée

Si la tripartition est vraie, le facteur résiduel **1.832** (= (α_W/α_EM)/impédance)
doit être une quantité géométrique nommée — c'est le seul reste entre la
transparence du vertex faible et le coût de mémoire du vertex EM.
Toute tentative d'identification passera par un dépôt daté (protocole du 27/08).

## 6. Actions registre

- Ligne α_W (V.5) : l'exactitude reçoit son explication structurelle [P] — vertex
  sans mémoire, mode ½ transparent (exploration 27/08).
- Ligne α_EM (V.5) : la tripartition et le mélange d'échelles sont consignés ;
  l'assaut vertex reste [F], l'exploration ajoute le *pourquoi* de la résistance.

---

> *Trois couplages, trois relations à la même mémoire : oublier, porter, être.*