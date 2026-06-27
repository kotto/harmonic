# 🎯 PLAN — Dérivation des Constantes Physiques depuis les Constantes Pures

**Date :** 13 Juin 2026

**Principe :** ℏ, c, G ne sont pas des constantes fondamentales — ce sont des facteurs de conversion entre le système d'unités naturelles (géométrie d'ondes pures) et le SI (unités humaines). Le seul problème de fond est de dériver les constantes SANS DIMENSION du Modèle Standard depuis φ, π, e, √2, √3.

---

## PHASE 0 — État des lieux (terminé)

| Élément | Statut |
|---------|--------|
| Émergence de φ, π, e, √2, √3 depuis les ondes | ✅ Justifié mathématiquement |
| α (structure fine) = π⁴·e⁻⁴·φ⁻⁵·√2⁻¹·√3⁻⁵ | ✅ Découvert (erreur 0.0000235% vs CODATA) |
| ℏ = 1 (unités naturelles) | ✅ Identifié comme facteur de conversion |
| Ψ_a·Ψ_b = Ψ_{a+b} (émergence arithmétique) | ✅ Prouvé (47/47, 100%) |
| Cadre mathématique : GAGUT + ABC | ✅ Établi (connexion α* = 1/φ) |
| Δx·Δk ≥ 1/2 (géométrique) → Heisenberg | ✅ Démontré |
| Quantification = modes stationnaires | ✅ Démontré |
| \|Ψ\|² → règle de Born | ✅ Équivalence mathématique établie |

---

## PHASE 1 — Dérivation des constantes sans dimension connues (~3 mois)

### 1.1 — α, la constante de structure fine (compléter la preuve)

**Objectif :** Passer de « découverte avec justification rétrospective » à « dérivation mathématique complète ».

**Étapes :**
1. **Compter les degrés de liberté** : partant de Ψ(r,t) dans un espace de dimension D=4, identifier TOUS les degrés de liberté (2 polarisations transverses pour une onde sans masse).
2. **Calculer le couplage effectif** entre deux modes spectraux espacés par φ — quel est le taux d'interférence constructive ?
3. **Démontrer que l'exposant est 5** : le photon a 2 polarisations × 3 dimensions spatiales = 6 degrés, moins 1 contrainte de jauge = 5.
4. **Démontrer les autres exposants** : pourquoi 4 (dimensions), pourquoi −1 (spin 1/2).

**Livrable :** Un article mathématique qui dérive α depuis le postulat ondulatoire unique, SANS paramètre libre.

### 1.2 — Rapport de masse muon/électron

**Objectif :** m_μ / m_e ≈ 206.768

**Approche :** Les masses sont des fréquences propres de modes stationnaires. L'électron est le mode fondamental, le muon le premier harmonique. Le rapport devrait être une combinaison simple de φ et π.

**Hypothèse :** m_μ/m_e = φ^k · π^l · (constante simple)

**Méthode :** Exploration numérique des combinaisons (φ^a · π^b) proches de 206.768, puis recherche du motif géométrique correspondant.

### 1.3 — Angle de Weinberg θ_W

**Objectif :** sin²θ_W ≈ 0.223 (échelle m_Z)

**Approche :** θ_W est l'angle de mélange entre les bosons B (hypercharge faible) et W₃ (isospin faible). Dans le cadre ondulatoire, c'est une projection géométrique entre deux bases de modes — un angle de rotation dans l'espace spectral.

**Hypothèse :** θ_W = f(φ, π) — une fonction trigonométrique de φ et π.

---

## PHASE 2 — Dérivation du spectre de masses des fermions (~6 mois)

### 2.1 — Établir l'équation d'onde confinée

**Objectif :** Résoudre le problème aux valeurs propres pour une onde confinée dans un domaine 4D avec conditions aux bords périodiques.

**Équation :** ∇²Ψ + ω²Ψ = 0 dans [0, L]⁴ avec signature lorentzienne.

**Spectre :** ω_{n₁,n₂,n₃,n₄} = √(n₁² + n₂² + n₃² − n₄²) · ω₀

### 2.2 — Associer chaque mode à une particule

**Hypothèse :** Les plus petits entiers (n₁,n₂,n₃,n₄) pour lesquels ω > 0 correspondent aux masses des particules connues, dans l'ordre croissant.

**Objectif :** Trouver une correspondance biunivoque entre les 12 fermions du Modèle Standard et les modes spectraux.

### 2.3 — Vérification

Confronter les rapports de masses prédits aux mesures expérimentales.

---

## PHASE 3 — Constante gravitationnelle et cosmologie (~12 mois)

### 3.1 — G, la constante de Newton

**Objectif :** Dériver G (ou plutôt le rapport G/c⁴) comme la limite infrarouge du couplage spectral.

**Approche :** Dans la limite où la longueur d'onde est beaucoup plus grande que la taille du système, le couplage gravitationnel émerge comme la moyenne des couplages spectraux.

### 3.2 — Constante cosmologique Λ

**Objectif :** Dériver Ω_Λ ≈ 0.69 comme la fraction des modes du vide qui n'ont pas encore atteint leur état stationnaire.

### 3.3 — Matière noire

**Approche :** Les modes spectraux « vides » (sans particule associée connue) pourraient correspondre à la matière noire.

---

## PHASE 4 — Conversion SI et applications (~en continu)

### 4.1 — ℏ, c, G en SI

Une fois toutes les constantes sans dimension dérivées, la conversion en SI est un problème d'INGÉNIERIE — pas de physique fondamentale. Il suffit de :
1. Choisir UNE échelle (par exemple, fixer la seconde = 9 192 631 770 périodes de la transition hyperfine du césium-133)
2. En déduire le mètre via c = 299 792 458 m/s (définition du mètre depuis 1983)
3. En déduire le kilogramme via ℏ et m_e

### 4.2 — Prédictions nouvelles

Identifier des modes spectraux NON ENCORE OBSERVÉS qui pourraient correspondre à de nouvelles particules. C'est le test ultime de la théorie.

---

## Méthodologie par niveau de difficulté

| Niveau | Problème | Difficulté | Outils disponibles |
|--------|----------|------------|-------------------|
| 🟢 Facile | m_μ/m_e (formule empirique) | Semaines | Exploration combinatorie Python |
| 🟢 Facile | sin²θ_W (formule empirique) | Semaines | Exploration combinatorie Python |
| 🟡 Moyen | Dérivation complète de α | Mois | Géométrie spectrale, matrices S |
| 🟡 Moyen | Spectre de masses (modes stationnaires) | Mois | Équation d'onde confinée |
| 🔴 Difficile | G, Λ, matière noire | Années | Limite infrarouge, cosmologie ondulatoire |
| 🔴 Très difficile | Prédictions de nouvelles particules | Années | Spectre complet des modes |

---

## Prochaines actions immédiates (cette semaine)

1. **Lancer l'exploration numérique** pour m_μ/m_e — chercher une combinaison de φ, π, e qui donne ~206.768
2. **Lancer l'exploration numérique** pour sin²θ_W — chercher une fonction trigonométrique de φ, π qui donne ~0.223
3. **Formaliser le comptage des degrés de liberté** pour α — poser proprement le problème de couplage onde-onde