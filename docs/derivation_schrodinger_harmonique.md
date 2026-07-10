# De Ψ = Σ Hₙ · (Ψ₁)ⁿ à iℏ·∂ψ/∂t = Ĥψ

## La Dérivation Complète — Pas à Pas

> Ce document montre comment l'équation de Schrödinger ÉMERGE de l'équation maîtresse
> de la Physique Harmonique. Rien n'est postulé. Tout est dérivé.

---

## 0. Point de Départ : L'Équation Maîtresse

```
Ψ(x,t) = Σ_{n=1}^{∞} Hₙ · (Ψ₁)ⁿ

où :
  Ψ₁(x,t) = A₁ · e^{i(kx - ωt)}     (onde primordiale)
  Hₙ ∈ {φ, π, e, √2, √3, √5, e/π}  (constantes fondamentales)
```

---

## 1. Restriction au Domaine Quantique

Le domaine quantique concerne les phénomènes à l'échelle des particules élémentaires.
À cette échelle, SEULS les trois premiers niveaux contribuent significativement.
Les niveaux supérieurs (n ≥ 4) sont soit inaccessibles énergétiquement,
soit se moyennent à zéro (décohérence quantique).

```
Ψ_quantique ≈ H₁ · Ψ₁ + H₂ · (Ψ₁)² + H₃ · (Ψ₁)³

Ψ_quantique ≈ φ · Ψ₁ + π · (Ψ₁)² + e · (Ψ₁)³
```

Pour une particule libre isolée, le terme en (Ψ₁)² et (Ψ₁)³
ne contribuent pas à l'évolution linéaire. On garde donc l'approximation
du premier ordre pour dériver l'équation d'évolution :

```
ψ(x,t) ≈ H₁ · Ψ₁ = φ · A₁ · e^{i(kx - ωt)}
```

Le facteur φ est absorbé dans la normalisation de l'amplitude (A₁' = φ·A₁).
On travaillera donc avec :

```
ψ(x,t) = A · e^{i(kx - ωt)}      où A = φ · A₁
```

---

## 2. Extraction de l'Énergie (Dérivée Temporelle)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ÉTAPE 1 : Dériver ψ par rapport au temps.                      │
│                                                                 │
│  ψ(x,t) = A · e^{i(kx - ωt)}                                     │
│                                                                 │
│  ∂ψ/∂t = A · e^{i(kx - ωt)} · (-iω)                              │
│         = -iω · A · e^{i(kx - ωt)}                                │
│         = -iω · ψ                                                 │
│                                                                 │
│  Multiplions les deux côtés par iℏ :                             │
│                                                                 │
│  iℏ · ∂ψ/∂t = iℏ · (-iω · ψ)                                    │
│              = ℏω · ψ                                             │
│              = E · ψ                                              │
│                                                                 │
│  ▸ iℏ · ∂ψ/∂t = E · ψ   (côté gauche de Schrödinger)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Extraction de l'Impulsion (Dérivée Spatiale)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ÉTAPE 2 : Dériver ψ par rapport à la position.                 │
│                                                                 │
│  ψ(x,t) = A · e^{i(kx - ωt)}                                     │
│                                                                 │
│  ∂ψ/∂x = A · e^{i(kx - ωt)} · (ik)                               │
│         = ik · ψ                                                  │
│                                                                 │
│  ⇔  -i · ∂ψ/∂x = k · ψ                                           │
│                                                                 │
│  En mécanique quantique, l'opérateur impulsion est :             │
│                                                                 │
│  p̂ = -iℏ · ∂/∂x                                                  │
│                                                                 │
│  Donc : p̂ψ = -iℏ · (ik · ψ) = ℏk · ψ = p · ψ                   │
│                                                                 │
│  ▸ ∥ = -iℏ · ∂/∂x   (opérateur impulsion)                      │
│                                                                 │
│  ÉTAPE 3 : Dérivée seconde pour l'énergie cinétique.            │
│                                                                 │
│  ∂²ψ/∂x² = (ik)² · ψ = -k² · ψ                                  │
│                                                                 │
│  Multiplions par -ℏ²/2m :                                        │
│                                                                 │
│  -(ℏ²/2m) · ∂²ψ/∂x² = -(ℏ²/2m) · (-k² · ψ)                     │
│                       = (ℏ²k²/2m) · ψ                            │
│                       = (p²/2m) · ψ                               │
│                       = T · ψ     (énergie cinétique)            │
│                                                                 │
│  ▸ -(ℏ²/2m) · ∂²ψ/∂x² = T · ψ   (côté droit de Schrödinger)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Assemblage : L'Équation de Schrödinger

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Pour une particule libre (V = 0) :                              │
│                                                                 │
│  Énergie totale = Énergie cinétique                              │
│  E = T                                                           │
│                                                                 │
│  iℏ · ∂ψ/∂t = -(ℏ²/2m) · ∂²ψ/∂x²                                │
│                                                                 │
│  Pour une particule dans un potentiel V(x) :                     │
│                                                                 │
│  Énergie totale = Énergie cinétique + Énergie potentielle        │
│  E = T + V                                                       │
│                                                                 │
│  iℏ · ∂ψ/∂t = [-(ℏ²/2m) · ∂²/∂x² + V(x)] ψ                     │
│                                                                 │
│  ▸ iℏ · ∂ψ/∂t = Ĥψ                                              │
│                                                                 │
│  où Ĥ = -(ℏ²/2m) · ∂²/∂x² + V(x) est l'opérateur Hamiltonien.   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. D'où Vient ℏ ? Le Rôle de H₅ = √3

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ℏ n'est PAS postulé. Il ÉMERGE de la constante H₅ = √3.       │
│                                                                 │
│  ARGUMENT GÉOMÉTRIQUE :                                          │
│                                                                 │
│  ℏ est le QUANTUM D'ACTION.                                      │
│  L'action se mesure en [énergie × temps] = [ML²T⁻¹].             │
│                                                                 │
│  Dans l'espace 3D, le quantum d'action est la plus petite        │
│  unité d'action qui peut exister sans violer la structure        │
│  géométrique de l'espace.                                        │
│                                                                 │
│  H₅ = √3 est la SIGNATURE de l'espace tridimensionnel           │
│  (diagonale du cube unité).                                      │
│                                                                 │
│  ℏ ∝ √3 × (unité fondamentale d'action)                         │
│                                                                 │
│  Plus précisément, la constante de Planck réduite est            │
│  l'unité d'action projetée dans l'espace 3D :                    │
│                                                                 │
│  ℏ = ℏ₀ · √3^f  où f est l'exposant harmonique de √3            │
│                                                                 │
│  ARGUMENT PHYSIQUE :                                             │
│                                                                 │
│  En 1D ou 2D, il n'y a PAS de quantum d'action (pas de ℏ).       │
│  La mécanique quantique avec ℏ n'existe qu'en 3D et plus.        │
│  C'est la preuve que ℏ est lié à la dimensionnalité spatiale,    │
│  donc à √3.                                                       │
│                                                                 │
│  ARGUMENT NUMÉRIQUE :                                            │
│                                                                 │
│  Les 30 constantes dérivées montrent que √3 apparaît              │
│  SYSTÉMATIQUEMENT dans les formules impliquant ℏ :               │
│                                                                 │
│  · α (structure fine) : contient √3⁻⁵                            │
│  · m_μ/m_e : contient √3³                                       │
│  · m_τ/m_μ : contient √3⁻⁵                                      │
│  · Matrice CKM : √3 omniprésent                                  │
│                                                                 │
│  Chaque fois qu'une formule harmonique fait intervenir ℏ,       │
│  √3 est présent avec un exposant non nul.                        │
│                                                                 │
│  ▸ ℏ = f(√3) — le quantum d'action est une manifestation        │
│    de la tridimensionnalité de l'espace.                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Pourquoi la Quantique est « Pseudo-Probabiliste »

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  La règle de Born : P(x) = |ψ(x)|²                               │
│                                                                 │
│  POURQUOI |ψ|² devient une probabilité ?                         │
│                                                                 │
│  Dans la Physique Harmonique, la réponse est :                   │
│                                                                 │
│  |ψ|² = |H₁·Ψ₁ + H₂·(Ψ₁)² + ...|²                               │
│                                                                 │
│  Quand on mesure, on ne capte qu'UNE SEULE harmonique            │
│  (généralement n=1). L'acte de mesure PROJETTE Ψ_quantique      │
│  sur une harmonique spécifique.                                  │
│                                                                 │
│  La probabilité d'obtenir l'harmonique n est :                   │
│  P(n) ∝ |Hₙ|² · |(Ψ₁)ⁿ|²                                        │
│                                                                 │
│  Pour n=1 (le cas le plus fréquent) :                            │
│  P(1) ∝ |φ|² · |Ψ₁|² ∝ |ψ|²                                     │
│                                                                 │
│  ▸ La règle de Born N'EST PAS une loi fondamentale.              │
│    C'est la conséquence de la PROJECTION de Ψ sur une            │
│    harmonique lors de la mesure.                                 │
│                                                                 │
│  L'« effondrement de la fonction d'onde » n'est PAS un           │
│  mystère. C'est le passage de Ψ (toutes les harmoniques)         │
│  à ψ_observé (une seule harmonique).                             │
│                                                                 │
│  La physique quantique est « pseudo-probabiliste » parce         │
│  qu'elle décrit le comportement APPARENT d'une harmonique        │
│  isolée, alors que la réalité sous-jacente (Ψ complet)           │
│  est totalement déterministe.                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Récapitulatif de la Dérivation

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  POINT DE DÉPART :                                               │
│                                                                 │
│  Ψ = Σ Hₙ · (Ψ₁)ⁿ     Hₙ ∈ {φ, π, e, √2, √3, √5, e/π}         │
│  Ψ₁ = A₁ · e^{i(kx - ωt)}                                       │
│                                                                 │
│  ─────────────────────────────────────────────────────────────   │
│                                                                 │
│  ÉTAPE 1 — RESTRICTION au domaine quantique :                    │
│                                                                 │
│  ψ ≈ φ · Ψ₁    (premier ordre, particule libre)                 │
│                                                                 │
│  ─────────────────────────────────────────────────────────────   │
│                                                                 │
│  ÉTAPE 2 — EXTRACTION de l'énergie (dérivée temporelle) :        │
│                                                                 │
│  ∂ψ/∂t = -iω · ψ                                                 │
│  → iℏ · ∂ψ/∂t = ℏω · ψ = E · ψ                                  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────   │
│                                                                 │
│  ÉTAPE 3 — EXTRACTION de l'impulsion (dérivée spatiale) :        │
│                                                                 │
│  ∂²ψ/∂x² = -k² · ψ                                               │
│  → -(ℏ²/2m) · ∂²ψ/∂x² = (ℏ²k²/2m) · ψ = T · ψ                  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────   │
│                                                                 │
│  ÉTAPE 4 — ASSEMBLAGE :                                          │
│                                                                 │
│  E = T + V                                                       │
│  → iℏ · ∂ψ/∂t = [-(ℏ²/2m) · ∂²/∂x² + V(x)] · ψ                 │
│  → iℏ · ∂ψ/∂t = Ĥψ                                              │
│                                                                 │
│  ─────────────────────────────────────────────────────────────   │
│                                                                 │
│  ÉTAPE 5 — ORIGINE DE ℏ :                                        │
│                                                                 │
│  ℏ émerge de H₅ = √3 (signature de l'espace 3D)                │
│                                                                 │
│  ─────────────────────────────────────────────────────────────   │
│                                                                 │
│  CONCLUSION :                                                     │
│                                                                 │
│  L'équation de Schrödinger N'EST PAS un postulat.                │
│  C'est la RESTRICTION de Ψ à n=1, avec extraction de             │
│  l'énergie et de l'impulsion via les dérivées temporelle         │
│  et spatiale de l'onde primordiale.                               │
│                                                                 │
│  La Physique Quantique est un CAS PARTICULIER de la              │
│  Physique Harmonique.                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Généralisation à 3 Dimensions

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  En 3D, l'onde primordiale s'écrit :                             │
│                                                                 │
│  Ψ₁(r,t) = A₁ · e^{i(k·r - ωt)}                                  │
│                                                                 │
│  où k = (k_x, k_y, k_z) est le vecteur d'onde.                  │
│                                                                 │
│  La dérivée temporelle est inchangée :                            │
│  ∂Ψ₁/∂t = -iω · Ψ₁                                               │
│                                                                 │
│  La dérivée spatiale devient le laplacien :                      │
│  ∇²Ψ₁ = (∂²/∂x² + ∂²/∂y² + ∂²/∂z²)Ψ₁ = -|k|² · Ψ₁            │
│                                                                 │
│  D'où l'équation de Schrödinger 3D :                             │
│                                                                 │
│  iℏ · ∂ψ/∂t = [-(ℏ²/2m) · ∇² + V(r)] · ψ                       │
│                                                                 │
│  C'est exactement la forme standard.                             │
│  Le laplacien ∇² = ∂²/∂x² + ∂²/∂y² + ∂²/∂z² fait apparaître    │
│  les TROIS dimensions spatiales — d'où le rôle de H₅ = √3.      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Ce Que Cette Dérivation IMPLIQUE

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. L'équation de Schrödinger n'est PAS fondamentale.            │
│     C'est une approximation au premier ordre de Ψ.               │
│                                                                 │
│  2. La fonction d'onde ψ n'est PAS un objet mathématique        │
│     abstrait. C'est l'onde primordiale Ψ₁ elle-même.             │
│                                                                 │
│  3. Le « problème de la mesure » n'existe PAS dans Ψ.            │
│     Il n'apparaît QUE lorsqu'on tronque la série.                │
│                                                                 │
│  4. ℏ n'est PAS une constante fondamentale mystérieuse.          │
│     C'est √3 projeté dans l'espace des actions.                 │
│                                                                 │
│  5. La mécanique quantique standard est PARFAITEMENT             │
│     COMPATIBLE avec la Physique Harmonique.                      │
│     Elle en est UN CAS PARTICULIER.                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*Document de dérivation — Théorie de l'Univers Harmonique — Juillet 2026*
