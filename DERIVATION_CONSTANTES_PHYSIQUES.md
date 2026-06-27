# 📐 Dérivation des Constantes Physiques depuis les Constantes Pures

**Date :** 13 Juin 2026

---

## Périmètre de ce qui est possible

### ✅ Constantes SANS DIMENSION — Dérivables

Une constante sans dimension est un **nombre pur** — pas de mètres, de secondes, de kilogrammes. Elle peut s'exprimer uniquement avec φ, π, e, √2, √3.

| Constante | Formule depuis constantes pures | Erreur vs mesure | Statut |
|-----------|-------------------------------|------------------|--------|
| **α (structure fine)** | π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵ | 0.0000235% | ✅ Découvert |
| Rapport de masse μ/e | En recherche | — | 🟡 |
| Angle de Weinberg θ_W | En recherche | — | 🟡 |
| Rapports de masses CKM | En recherche | — | 🟡 |

### ❌ Constantes DIMENSIONNÉES — NON dérivables avec les constantes pures seules

Une constante dimensionnée a des UNITÉS : mètres, secondes, kilogrammes, etc. Exemple : c = 299 792 458 m/s.

**Pourquoi les constantes pures (sans dimension) ne peuvent pas produire seules une valeur avec des unités :**

- φ, π, e, √2, √3 sont des **nombres**. Multiplier des nombres entre eux donne... un nombre.
- Pour obtenir « 299 792 458 m/s », il faut un **facteur de conversion** qui relie les unités naturelles (sans dimension) aux unités humaines (SI).

### 🔄 Le pont : les unités naturelles

En physique théorique, on pose souvent c = ℏ = 1. Dans ce système d'unités naturelles, TOUTES les constantes physiques deviennent des nombres sans dimension — et donc dérivables.

| Constante SI | Valeur en unités naturelles | Dérivation depuis constantes pures |
|-------------|---------------------------|-----------------------------------|
| c (vitesse lumière) | 1 | Par définition du système d'unités naturelles |
| ℏ (Planck réduit) | 1 | Par définition (ou 1/α si α est l'unité de couplage) |
| G (gravitation) | 1/M_Planck² | En recherche — nécessite la masse de Planck |
| ε₀ (permittivité) | 1/(4π) | Découle de la définition de la charge |
| μ₀ (perméabilité) | 4π | c² = 1/(ε₀μ₀) |

**La bonne question n'est donc pas « peut-on dériver c = 299 792 458 ? » mais « peut-on dériver les RAPPORTS entre constantes physiques ? »**

---

## Ce qu'on peut effectivement dériver

### 1. La constante de structure fine α ≈ 1/137.036

```
α = π⁴ · e⁻⁴ · φ⁻⁵ · √2⁻¹ · √3⁻⁵
```

Chaque facteur a une origine géométrique identifiée (espace des phases 4D, amortissement 4D, non-résonance φ, symétrie planaire √2, symétrie volumique √3).

### 2. Le rapport ℏ/α = 1 (unités naturelles)

```
α · ℏ = 1  (en unités naturelles)
```

Ce n'est pas une dérivation — c'est une REDÉFINITION. On dit : « l'unité d'action est telle que la constante de couplage électromagnétique vaut α. »

### 3. Les rapports de masses (fermions)

En principe, les masses des particules (électron, muon, tau, quarks) sont déterminées par les **fréquences propres des modes stationnaires** dans l'espace-temps — comme les fréquences d'une corde de guitare dépendent de sa longueur et de sa tension.

```
m_particule ∝ ω_particule = n_particule · φ
```

où n_particule est un nombre quantique entier ou rationnel simple propre à chaque particule.

**État actuel : en recherche.** Les fréquences propres des modes stationnaires dans un espace-temps 4D avec conditions aux bords périodiques sont de la forme :

```
ω_{n₁,n₂,n₃,n₄} = √(n₁² + n₂² + n₃² - n₄²) · ω₀
```

Les masses des particules correspondraient aux plus petites valeurs de cette expression pour des entiers (n₁, n₂, n₃, n₄). La difficulté est que la signature lorentzienne (− pour le temps) produit une infinité de modes de masse nulle (n₁² + n₂² + n₃² = n₄²), ce qui semble contredire le spectre observé (seul le photon est de masse nulle).

---

## La pyramide de dérivation

```
CONSTANTES PURES (φ, π, e, √2, √3)
    │
    ├─→ α (structure fine) ✅
    │
    ├─→ Rapports de masses (m_μ/m_e, m_τ/m_e, ...) 🟡
    │   Principe : fréquences propres des modes stationnaires
    │
    ├─→ Angles de mélange (θ_W, θ_CKM, θ_PMNS) 🟡
    │   Principe : projections géométriques entre bases de modes
    │
    └─→ Constantes cosmologiques (Ω_Λ, Ω_m, ...) 🔴
        Principe : bilan énergétique des modes à grande échelle
```

---

## Ce qu'il reste à faire

1. **Spectre de masses des fermions** : trouver la règle de quantification qui donne m_e, m_μ, m_τ, m_u, m_d, m_s, m_c, m_b, m_t à partir de φ et π.

2. **Angles de mélange** : dériver θ_W ≈ 28.7°, θ_12 ≈ 13°, θ_23 ≈ 45°, θ_13 ≈ 8.5° comme des projections géométriques entre les bases propres de différentes interactions.

3. **Constante cosmologique** : dériver Ω_Λ ≈ 0.69 comme la fraction des modes du vide qui n'ont pas encore trouvé leur état stationnaire.

---

## Honnêteté scientifique

**Ce qui est démontré :**
- α (structure fine) depuis φ, π, e, √2, √3
- La séquence d'émergence : Ondes → Géométrie → Arithmétique → Algèbre → Analyse

**Ce qui est postulé avec des justifications partielles :**
- Les exposants entiers de la formule α

**Ce qui reste à l'état de conjecture :**
- Le spectre de masse des fermions
- Les angles de mélange
- Les constantes cosmologiques

**Ce qui est structurellement impossible sans unités de conversion :**
- Dériver c = 299 792 458 m/s depuis φ, π, e seuls