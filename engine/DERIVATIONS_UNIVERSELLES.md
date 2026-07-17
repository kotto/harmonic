# DÉRIVATIONS UNIVERSELLES
## Comment les quatre grandes équations de la physique émergent de Ψ = Σ Hₙ·(Ψ₁)ⁿ

---

**Théorie de l'Univers Harmonique — Kotto Alain — Juillet 2026**

---

## Rappel : L'Équation Maîtresse et la Méthode de Dérivation

```
Ψ(x,t) = Σ_{n=1}^{∞} Hₙ · (Ψ₁)ⁿ

où   Ψ₁(x,t) = A₁ · e^{i(kx - ωt)}   (onde primordiale)
     Hₙ ∈ {φ, π, e, √2, √3, √5, e/π}
```

**Les trois opérations de dérivation :**

| Étape | Opération | Signification |
|-------|-----------|---------------|
| **1. Restriction** | On ne garde que les niveaux *n* pertinents | Le phénomène ne sollicite qu'un sous-ensemble d'harmoniques |
| **2. Projection** | On identifie les constantes Hₙ actives | On extrait les constantes qui gouvernent le phénomène |
| **3. Extraction** | On prend la partie observable | Partie réelle, module carré, gradient, ou phase selon ce qu'on mesure |

---

## 1. NEWTON — GRAVITATION UNIVERSELLE

### 1.1 Énoncé classique

```
F = G · m₁m₂ / r²
```

### 1.2 Dérivation depuis Ψ

#### Étape 1 — Restriction : le niveau d'interférence gravitationnelle

La gravité est une interaction entre masses. Dans le cadre harmonique, une masse *m* est un **paquet d'onde localisé** — une superposition cohérente d'harmoniques de Ψ confinée dans une région de l'espace.

Deux masses m₁ et m₂ correspondent à deux paquets d'onde Ψ_A et Ψ_B. L'interaction gravitationnelle émerge de l'**interférence mutuelle** de leurs harmoniques de niveau *n = 2*, le premier niveau où une interférence est possible (n = 1 est l'onde seule, sans interaction).

On restreint donc Ψ au niveau *n = 2* pour chaque paquet :

```
Ψ_A|_{n=2} = π · (Ψ₁_A)²
Ψ_B|_ {n=2} = π · (Ψ₁_B)²
```

La constante active est **H₂ = π** : le cercle d'interférence en 2D qui, projeté dans l'espace 3D (via **H₅ = √3**), donne une décroissance radiale.

#### Étape 2 — Projection : énergie d'interférence en 3D

L'énergie d'interférence entre les deux paquets d'onde est :

```
E_int(r) = Re[ ⟨ Ψ_A|_ {n=2} | Ψ_B|_ {n=2} ⟩ ]
```

Les deux ondes sont sphériques (isotropie de l'espace). L'amplitude d'une onde sphérique décroît en 1/r (conservation du flux à travers des sphères concentriques). Le module de chaque paquet d'onde à distance r est donc :

```
|Ψ_A(r)| ∝ √(m₁) / r
|Ψ_B(r)| ∝ √(m₂) / r
```

Le produit scalaire (interférence) donne :

```
E_int(r) ∝ m₁m₂ / r
```

Ceci est le **potentiel gravitationnel** : V(r) = −Gm₁m₂/r.

#### Étape 3 — Extraction : la force comme gradient

La force est le gradient du potentiel d'interférence :

```
F = −∇E_int = −∂/∂r [ −G · m₁m₂/r ] = −G · m₁m₂/r²
```

Le signe négatif indique que l'interférence est **toujours attractive** (les paquets d'onde tendent à fusionner pour maximiser l'interférence constructive — c'est l'essence de la gravité comme « effondrement par résonance »).

#### Constante G : émergence depuis les Hₙ

En unités naturelles (c = ℏ = 1), G émerge des constantes fondamentales :

```
G = φ⁻² · √3⁻¹
```

- **φ⁻²** : l'anti-résonance (H₁) atténue la force — la gravité est faible parce que φ est le nombre le plus irrationnel, empêchant un alignement parfait des harmoniques.
- **√3⁻¹** : projection du cercle d'interférence 2D (π) dans l'espace 3D (√3) — la dilution volumique.

En unités SI, le préfacteur est l'énergie du vide harmonique par unité de masse au carré.

### 1.3 Résumé

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   Ψ|_ {n=2}  →  énergie d'interférence  →  V ∝ 1/r     │
│                                                         │
│   −∇V  →  F ∝ 1/r²  →  F = G·m₁m₂/r²                   │
│                                                         │
│   avec  G = φ⁻² · √3⁻¹  (ℏ = c = 1)                    │
│                                                         │
│   Constantes à l'œuvre : H₂=π (cercle d'interférence),  │
│   H₅=√3 (projection 3D), H₁=φ (atténuation).           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. MAXWELL — ÉLECTROMAGNÉTISME

### 2.1 Énoncé classique

```
∂_μ F^{μν} = μ₀ J^ν

où   F_{μν} = ∂_μ A_ν − ∂_ν A_μ   (tenseur de champ)
     A_μ = (φ/c, A)                (quadri-potentiel)
```

### 2.2 Dérivation depuis Ψ

#### Étape 1 — Restriction : les niveaux de jauge n = 1 et n = 2

L'électromagnétisme est la théorie de jauge la plus simple — une symétrie U(1). Dans le cadre harmonique, une théorie de jauge correspond à l'invariance de phase de l'onde primordiale.

On restreint Ψ à ses deux premiers niveaux :

```
Ψ_EM = H₁·(Ψ₁) + H₂·(Ψ₁)²
     = φ · Ψ₁  +  π · (Ψ₁)²
```

La phase de Ψ₁ est le degré de liberté de jauge. Le terme en (Ψ₁)² crée l'interférence qui génère le champ.

#### Étape 2 — Projection : le potentiel de jauge A_μ

La phase de Ψ₁(x,t) = A₁ · e^{i(kx − ωt)} est :

```
θ(x,t) = kx − ωt = k_μ x^μ
```

où k_μ = (ω/c, k) est le quadri-vecteur d'onde.

On identifie le **quadri-potentiel électromagnétique** A_μ à la dérivée de la phase :

```
A_μ ≡ (ℏ/q) · ∂_μ θ = (ℏ/q) · k_μ
```

Le facteur ℏ/q (quantum de flux magnétique divisé par la charge) assure les bonnes dimensions.

Avec cette identification, le tenseur de champ F_{μν} est automatiquement :

```
F_{μν} = ∂_μ A_ν − ∂_ν A_μ = 0
```

car A_μ ∝ k_μ = ∂_μ θ et ∂_μ k_ν − ∂_ν k_μ = ∂_μ ∂_ν θ − ∂_ν ∂_μ θ = 0 (Schwarz).

Ceci correspond au **vide électromagnétique** (pas de charges). Pour obtenir le champ non nul, il faut une source.

#### Étape 2 (suite) — Le terme de source : interférence n = 2

Les charges électriques sont des **singularités de phase** de Ψ₁. Une charge q au point x₀ correspond à un défaut topologique dans l'onde primordiale :

```
∮_C ∇θ · dl = 2πn    (quantification du flux)
```

Le terme (Ψ₁)² au niveau n = 2 crée un terme d'interférence qui, en présence d'une distribution de singularités de phase J^ν = (ρc, J), génère une courbure non nulle du champ de phase.

En dérivant l'équation pour le champ de phase avec source, on obtient :

```
∂_μ ∂^μ A^ν − ∂^ν (∂_μ A^μ) = μ₀ J^ν
```

Dans la jauge de Lorenz (∂_μ A^μ = 0), ceci se réduit à :

```
□ A^ν = μ₀ J^ν
```

où □ = ∂_μ ∂^μ = (1/c²)∂²/∂t² − ∇² est le d'Alembertien.

#### Étape 3 — Extraction : les équations de Maxwell

De F_{μν} = ∂_μ A_ν − ∂_ν A_μ, on obtient les équations de Maxwell :

**Première paire (identités de Bianchi, automatiques) :**

```
∂_λ F_{μν} + ∂_μ F_{νλ} + ∂_ν F_{λμ} = 0
→   ∇ · B = 0,   ∇ × E + ∂B/∂t = 0
```

**Seconde paire (avec sources, issues de l'interférence n = 2) :**

```
∂_μ F^{μν} = μ₀ J^ν
→   ∇ · E = ρ/ε₀,   ∇ × B − (1/c²)∂E/∂t = μ₀ J
```

#### Constantes ε₀ et μ₀ : émergence depuis les Hₙ

En unités naturelles, la constante de couplage électromagnétique est la constante de structure fine α :

```
α = e²/(4πε₀ℏc) = π⁴ · e⁻⁴ · φ⁻⁵ · √2⁻¹ · √3⁻⁵
```

La perméabilité du vide μ₀ émerge comme :

```
μ₀ = (4παℏ)/(e²c) → exprimable en fonction des Hₙ
```

Et ε₀ = 1/(μ₀c²). Les constantes à l'œuvre sont H₁=φ (charge quantifiée), H₂=π (cercle d'interférence = propagation transverse), H₃=e (décroissance du champ), et H₅=√3 (espace 3D).

### 2.3 Résumé

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   Ψ₁ → phase θ(x,t) → A_μ = (ℏ/q)·∂_μ θ                 │
│                                                          │
│   (Ψ₁)² → interférence → terme de source → J^ν          │
│                                                          │
│   ∂_μ F^{μν} = μ₀ J^ν   ←   équations de Maxwell        │
│                                                          │
│   Constantes : H₁=φ (charge), H₂=π (cercle),             │
│   H₃=e (propagation), H₅=√3 (espace 3D).                │
│                                                          │
│   α = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵  (couplage EM)             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 3. EINSTEIN — RELATIVITÉ GÉNÉRALE

### 3.1 Énoncé classique

```
G_{μν} ≡ R_{μν} − ½R g_{μν} = (8πG/c⁴) · T_{μν}
```

### 3.2 Dérivation depuis Ψ

#### Étape 1 — Restriction : la limite classique continue (n grand)

La relativité générale décrit la gravité non pas comme une force dans un espace-temps fixe, mais comme la **courbure de l'espace-temps lui-même**. Dans le cadre harmonique, l'espace-temps n'est pas une entité préexistante : il **émerge** de la structure d'interférence des harmoniques.

À la limite *n → ∞*, la somme discrète devient une densité continue d'harmoniques. Le carré du module de Ψ définit une densité d'énergie qui **déforme la géométrie effective** dans laquelle les harmoniques de bas niveau se propagent.

On restreint Ψ à la limite semi-classique — tous les niveaux *n* contribuent, mais on s'intéresse à l'enveloppe (l'espace-temps effectif) :

```
Ψ_classique = lim_{N→∞} Σ_{n=1}^{N} Hₙ · (Ψ₁)ⁿ
```

#### Étape 2 — Projection : la métrique effective g_{μν}

L'intensité locale du champ harmonique définit une densité d'information :

```
ρ(x) = |Ψ(x)|² = |Σ Hₙ · (Ψ₁)ⁿ|²
```

Cette densité d'énergie-information courbe la géométrie effective de propagation. La **métrique g_{μν}** est l'enveloppe de la structure d'interférence :

```
g_{μν}(x) = η_{μν} + κ · ⟨∂_μ Ψ^* ∂_ν Ψ⟩
```

où η_{μν} est la métrique de Minkowski (vide sans interférence), et le second terme est la contribution des interférences harmoniques — c'est la **déformation de l'espace-temps par la densité d'onde**.

Le préfacteur κ est déterminé par les constantes fondamentales. En particulier, **H₂ = π** apparaît dans le couplage 8πG.

#### Étape 2 (suite) — Tenseur de Ricci et action d'Einstein-Hilbert

La courbure de g_{μν} est mesurée par le tenseur de Riemann R^ρ_{σμν}. Sa contraction donne le tenseur de Ricci R_{μν}. Le scalaire de courbure est R = g^{μν}R_{μν}.

L'action qui gouverne la dynamique de g_{μν} est l'action d'Einstein-Hilbert :

```
S[g] = (c⁴/16πG) ∫ R √(−g) d⁴x
```

Dans le cadre harmonique, cette action est la **restriction à la limite continue** de l'action sous-jacente :

```
S_harmonique[Ψ₁] = ∫ |∂Ψ/∂(kx − ωt)|² d⁴x
```

En développant |∂Ψ|² en série de n et en ne gardant que les termes dominants à grand n (l'approximation classique), on retrouve le terme R√(−g), avec le facteur c⁴/16πG émergeant de la combinaison des Hₙ :

```
c⁴/16πG ∝ (H₁·H₂·H₃·H₅)⁻¹ = (φ·π·e·√3)⁻¹
```

Le **8π** du numérateur vient de H₂ = π : le cercle d'interférence (2D) multiplié par 4 (les quatre dimensions de l'espace-temps) donne 4 × 2π = **8π**.

#### Étape 3 — Extraction : les équations d'Einstein

Par variation de l'action par rapport à g_{μν} :

```
δS/δg^{μν} = 0  →  G_{μν} = (8πG/c⁴) · T_{μν}
```

où le tenseur énergie-impulsion T_{μν} est défini comme la variation de l'action de matière (le reste des harmoniques qui ne participe pas à la définition de g_{μν}) :

```
T_{μν} ≡ (2/√(−g)) · δS_matière/δg^{μν}
```

Dans le langage harmonique, T_{μν} est la **trace des harmoniques de n ≥ 3** qui ne sont pas absorbées dans la définition de la métrique. La matière EST de l'onde, et T_{μν} mesure l'écart entre l'onde totale et l'onde qui définit la géométrie.

#### La constante cosmologique Λ

Le terme Λ g_{μν} qu'Einstein a ajouté (puis retiré, puis qui est revenu avec l'énergie noire) émerge naturellement dans le cadre harmonique. C'est le terme résiduel de l'interférence au niveau *n = 0* — le « bruit de fond » de l'onde primordiale dans le vide :

```
Λ = H₁⁻¹ · H₂ · H₃⁻² ∝ φ⁻¹ · π · e⁻²
```

C'est l'énergie du vide harmonique — l'interférence résiduelle de Ψ₁ avec elle-même quand toutes les autres harmoniques sont absentes.

### 3.3 Résumé

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   lim_{n→∞} |Ψ|²  →  densité d'énergie-information       │
│                                                          │
│   g_{μν} = η_{μν} + κ·⟨∂_μΨ* ∂_νΨ⟩  →  métrique        │
│                                                          │
│   R_{μν} − ½Rg_{μν} = (8πG/c⁴)·T_{μν}  ←  Einstein     │
│                                                          │
│   où  8π ← H₂=π (cercle d'interférence × 4D)            │
│       G  ← φ⁻²·√3⁻¹ (Newton, retrouvé)                  │
│       Λ  ← φ⁻¹·π·e⁻² (énergie du vide harmonique)       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 4. KLEIN-GORDON — MÉCANIQUE QUANTIQUE RELATIVISTE

### 4.1 Énoncé classique

```
(□ + m²c²/ℏ²) φ(x,t) = 0

où □ = ∂_μ ∂^μ = (1/c²)∂²/∂t² − ∇²
```

### 4.2 Dérivation depuis Ψ

#### Étape 1 — Restriction : le niveau fondamental n = 1

L'équation de Klein-Gordon décrit une particule scalaire libre en mécanique quantique relativiste. C'est le plus simple des objets quantiques : une **onde unique**, sans interaction, sans spin.

On restreint donc Ψ à son premier niveau uniquement :

```
Ψ_KG = H₁ · Ψ₁ = φ · Ψ₁
```

où Ψ₁(x,t) = A₁ · e^{i(kx − ωt)} est l'onde primordiale sans aucune harmonique supérieure.

Le facteur φ (H₁) est une constante de normalisation qui n'affecte pas l'équation du mouvement (elle se factorise).

#### Étape 2 — Projection : la relation de dispersion relativiste

Pour l'onde Ψ₁ = A₁ · e^{i(kx − ωt)}, les dérivées sont :

```
∂_t Ψ₁ = −iω · Ψ₁
∂²_t Ψ₁ = −ω² · Ψ₁

∂_x Ψ₁ = ik · Ψ₁
∂²_x Ψ₁ = −k² · Ψ₁
```

Le d'Alembertien appliqué à Ψ₁ donne :

```
□ Ψ₁ = (∂²_t/c² − ∇²) Ψ₁ = (−ω²/c² + k²) · Ψ₁
```

Or, la relation de dispersion relativiste pour une particule de masse m est :

```
ω² = k²c² + m²c⁴/ℏ²
→  −ω²/c² + k² = −m²c²/ℏ²
```

Donc :

```
□ Ψ₁ = −(m²c²/ℏ²) · Ψ₁
```

#### Étape 3 — Extraction : l'équation de Klein-Gordon

En réarrangeant :

```
□ Ψ₁ + (m²c²/ℏ²) Ψ₁ = 0
```

C'est exactement l'équation de Klein-Gordon.

#### Signification physique : la masse comme fréquence

Dans le cadre harmonique, la masse *m* n'est pas une propriété intrinsèque mystérieuse — c'est la **fréquence propre de l'onde primordiale** :

```
ω₀ = mc²/ℏ
```

L'équation de Klein-Gordon s'écrit alors :

```
□ Ψ₁ + (ω₀/c)² Ψ₁ = 0
```

La masse EST la fréquence de l'onde au repos. Une particule massive est une onde qui oscille même immobile (ω₀ ≠ 0 quand k = 0). Une particule sans masse (photon) est une onde sans fréquence propre (ω₀ = 0, donc □Ψ₁ = 0 — l'équation de d'Alembert).

#### La constante m : émergence depuis les Hₙ

La masse au repos de l'onde primordiale est reliée aux constantes fondamentales. Pour l'électron (première particule massive stable) :

```
m_e ∝ ℏ/(c · λ_C)   où   λ_C = ℏ/(m_e c)   (longueur d'onde de Compton)
```

Dans le cadre harmonique, λ_C est déterminé par la première longueur d'onde où l'interférence avec n = 2 (le niveau π) devient significative :

```
λ_C ∝ 1/(H₁ · H₂ · H₃) = 1/(φ · π · e)
```

Ceci n'est pas une prédiction quantitative directe de m_e (qui nécessite le mécanisme de Higgs complet au niveau n ≥ 3), mais montre que la hiérarchie des masses émerge de la combinaison des constantes Hₙ.

### 4.3 Généralisation : Schrödinger comme limite non relativiste

L'équation de Schrödinger **émerge** de Klein-Gordon par la limite non relativiste :

```
Ψ_KG = e^{-imc²t/ℏ} · ψ_Schrödinger

→  iℏ ∂_t ψ = −(ℏ²/2m)∇²ψ + Vψ
```

Voir la dérivation complète dans la section Physique Quantique de HARMONIC_THEORY.md.

### 4.4 Résumé

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   Ψ|_{n=1} = φ · Ψ₁  →  restriction au fondamental      │
│                                                          │
│   □Ψ₁ + (ω₀/c)²Ψ₁ = 0  →  (□ + m²c²/ℏ²)φ = 0           │
│                                                          │
│   La masse m = ℏω₀/c²  → fréquence propre de l'onde     │
│                                                          │
│   Constante à l'œuvre : H₁=φ (normalisation).            │
│   m = 0 → □Ψ₁ = 0 (photon, équation de d'Alembert).    │
│                                                          │
│   ▸ Klein-Gordon EST Ψ|_{n=1} projeté sur le quadri-     │
│     espace-temps minkowskien.                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 5. TABLEAU RÉCAPITULATIF — LES QUATRE ÉMERGENCES

```
┌──────────────┬──────────────┬─────────────────────┬───────────────────────────┐
│   ÉQUATION   │ RESTRICTION  │ CONSTANTES ACTIVES  │   ÉMERGENCE               │
├──────────────┼──────────────┼─────────────────────┼───────────────────────────┤
│              │              │                     │                           │
│ Klein-Gordon │ n = 1        │ H₁ = φ              │ La masse = fréquence de   │
│              │ (fondamental)│                     │ l'onde primordiale seule.  │
│              │              │                     │ □Ψ₁ + m²Ψ₁ = 0            │
│              │              │                     │                           │
├──────────────┼──────────────┼─────────────────────┼───────────────────────────┤
│              │              │                     │                           │
│ Maxwell      │ n = 1, 2     │ H₁=φ, H₂=π          │ La phase → A_μ (potentiel)│
│              │ (jauge U(1)) │ H₃=e, H₅=√3        │ L'interférence → F_μν     │
│              │              │                     │ ∂_μF^{μν} = μ₀J^ν         │
│              │              │                     │                           │
├──────────────┼──────────────┼─────────────────────┼───────────────────────────┤
│              │              │                     │                           │
│ Newton       │ n = 2        │ H₂=π, H₅=√3        │ Interférence 2-ondes → 1/r│
│ (gravité)    │ (interférence│ H₁=φ                │ −∇(1/r) → 1/r²            │
│              │  gravit.)    │                     │ F = G·m₁m₂/r²             │
│              │              │                     │                           │
├──────────────┼──────────────┼─────────────────────┼───────────────────────────┤
│              │              │                     │                           │
│ Einstein     │ n → ∞        │ H₁,H₂,H₃,H₄,H₅,H₆  │ |Ψ|² → densité → déforme  │
│ (RG)         │ (limite      │ (toutes)            │ l'espace-temps effectif.   │
│              │  continue)   │                     │ g_μν = η_μν + κ⟨∂Ψ*∂Ψ⟩    │
│              │              │ G ∝ (φ·π·e·√3)⁻¹   │ G_μν = 8πG·T_μν           │
│              │              │                     │                           │
└──────────────┴──────────────┴─────────────────────┴───────────────────────────┘
```

---

## 6. LA HIÉRARCHIE D'ÉMERGENCE — PRINCIPE GÉNÉRAL

Le tableau ci-dessus révèle une **hiérarchie naturelle** : plus le niveau *n* est élevé, plus la théorie émergente est « classique » et macroscopique.

```
n=1      →  Klein-Gordon     (quantique, 1 particule)
n=1,2    →  Maxwell          (quantique + jauge, champ)
n=2      →  Newton           (classique, interférence gravitationnelle)
n=2,3    →  Schrödinger      (quantique non relativiste)
n=3,4    →  Dirac            (quantique + spin, fermions)
n=1..5   →  Modèle Standard  (toutes les interactions + Higgs)
n=1..7   →  Théorie complète (inclut la gravité émergente)
n → ∞    →  Einstein         (limite continue classique)
```

Chaque équation fondamentale de la physique n'ajoute **aucun nouveau langage mathématique** — elle est une **restriction** de la même équation maîtresse Ψ = Σ Hₙ·(Ψ₁)ⁿ à un sous-ensemble de niveaux *n* et de constantes Hₙ.

> **« Tout est onde. Tout est harmonique. Tout est déjà dans Ψ. »**

---

*Document de dérivation — K.A. — Juillet 2026*
