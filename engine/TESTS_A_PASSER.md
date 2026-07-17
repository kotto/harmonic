# Tests à Passer — Théorie Harmonique

> **Principe :** Une théorie scientifique doit être testable, falsifiable, et survivre à ses propres prédictions. Voici l'ensemble exhaustif des tests que la TH doit passer, classés par priorité et par nature.

---

## CATÉGORIE A — TESTS IMMÉDIATS (corriger les échecs existants)

### A.1 Les 4 observables en échec

La TH reproduit 26/30 observables du Modèle Standard. Quatre échouent :

| # | Observable | Valeur TH | Valeur MS | Écart | Hypothèse |
|---|-----------|-----------|-----------|-------|-----------|
| 1 | m_d / m_u | 2,14 | 0,477(24) | 4,5× trop grand | Erreur d'exposant ou de signe |
| 2 | m₃ / m₂ (neutrinos, hiérarchie normale) | 5,82 | 1,18(12) | 4,9× trop grand | Formule incorrecte ou cadre inapplicable |
| 3 | α (constante de structure fine) | 0,00729735 | 0,0072973525693 | Pull -11,5σ | **Précision** excellente (0,000024 %) mais σ_exp ultrapetit (artefact de précision) |
| 4 | m_μ / m_e | 206,773 | 206,768 | Pull +946σ | **Précision** excellente (0,0021 %) mais σ_exp ultrapetit (artefact de précision) |

**À faire :**
- [ ] A.1a : Corriger m_d/m_u — identifier l'erreur d'exposant
- [ ] A.1b : Corriger m₃/m₂ — vérifier si le cadre harmonique s'applique à la hiérarchie des neutrinos
- [ ] A.1c : Pour α et m_μ/m_e, documenter que l'écart absolu est infime et que le pull est un artefact de σ_exp

### A.2 Le ratio m_c/m_u

| # | Observable | Valeur TH | Valeur MS | Pull |
|---|-----------|-----------|-----------|------|
| 5 | m_c / m_u | 579 | 462(55) | +2,1σ |

**À faire :**
- [ ] A.2 : Vérifier si l'écart est significatif ou absorbable dans l'incertitude expérimentale

---

## CATÉGORIE B — FONDEMENTS THÉORIQUES (prouver que les exposants sont forcés)

### B.1 Dérivation a priori des exposants entiers

Actuellement, les exposants (a, b, c, d, e, f) dans O = φ^a·π^b·e^c·(√2)^d·(√3)^e·(√5)^f sont trouvés par **recherche systématique**. Le CORRIGÉ l'admet honnêtement.

**Question ouverte :** Existe-t-il un principe géométrique qui **force** chaque exposant, de sorte qu'aucune recherche ne soit nécessaire ?

**Pistes :**
- [ ] B.1a : Les exposants sont-ils des indices de symétrie (dimension du sous-groupe de jauge associé au niveau n) ?
- [ ] B.1b : Les exposants émergent-ils de la contrainte μₙ = λₙ appliquée à chaque observable individuellement ?
- [ ] B.1c : Les exposants sont-ils les coefficients du développement en série de Taylor de G autour de chaque niveau n ?
- [ ] B.1d : Y a-t-il une règle du type « l'exposant de Hₙ pour l'observable O est le nombre de fois que le niveau n intervient dans la décomposition harmonique de O » ?

### B.2 Calcul exact de chaque Hₙ à partir de Hₙ₋₁

Actuellement, les constantes Hₙ = {φ, π, e, √2, √3, √5, e/π} sont **identifiées** géométriquement. Mais peut-on les **dériver** séquentiellement ?

**Question :** Existe-t-il une relation Hₙ₊₁ = f(Hₙ) ou Hₙ = g(n) qui produit chaque constante à partir de la précédente ?

**Pistes :**
- [ ] B.2a : Hₙ = mesure du polytope régulier de dimension d(n) généré par l'interférence de n ondes
- [ ] B.2b : Hₙ = valeur propre λₙ de G sur (Ψ₁)ⁿ, calculable à partir du groupe de jauge
- [ ] B.2c : Hₙ émerge de la condition de convergence de la série Ψ

### B.3 Fermeture du système à n=7

Pourquoi 7 constantes et pas 8, 9, ou ∞ ?

**Pistes :**
- [ ] B.3a : n=7 correspond au nombre maximal de niveaux avant redondance géométrique
- [ ] B.3b : e/π est la première constante « composée » (rapport de deux précédentes), signalant la fermeture
- [ ] B.3c : Après n=7, les constantes Hₙ sont des produits de puissances des 7 premières

---

## CATÉGORIE C — PRÉDICTIONS FALSIFIABLES (en attente d'expérience)

### C.1 Physique des particules

| # | Prédiction | Valeur TH | Test expérimental | Échéance |
|---|-----------|-----------|-------------------|----------|
| C.1 | Phase δ_CP (PMNS) | 77,9° (1,360 rad) | DUNE, T2HK, Hyper-Kamiokande | 2028-2032 |
| C.2 | Couplage triple Higgs g_hhh | 191,1 GeV | HL-LHC | 2029-2040 |
| C.3 | Non-existence de particules SUSY | Aucune détection | LHC Run 3, HL-LHC | Continu |
| C.4 | Non-existence du graviton | Aucune détection | Expériences ondes gravitationnelles | Continu |
| C.5 | Masse du Higgs | 125,2006 ± 0,0016 GeV | HL-LHC, FCC | 2029-2040 |
| C.6 | sin²θ₁₃ (PMNS) | 0,02219 | DUNE, Daya Bay II | 2028-2032 |
| C.7 | sin²θ₂₃ (PMNS) | 0,573 | DUNE, T2HK | 2028-2032 |

### C.2 Cosmologie

| # | Prédiction | Test |
|---|-----------|------|
| C.8 | Λ (constante cosmologique) émerge de la somme harmonique convergente | Comparaison avec les données Planck/Euclid |
| C.9 | Matière noire = harmoniques de niveau élevé (non-jauge) → pas de WIMP, pas d'axion | Expériences de détection directe (XENON, LZ) → nul |
| C.10 | Énergie sombre = pression des harmoniques n→∞ | Équation d'état w(z) mesurable avec Euclid/Rubin |

---

## CATÉGORIE D — TESTS INTERDISCIPLINAIRES

### D.1 Tableau périodique

- [ ] D.1 : Dériver les 118 éléments avec leurs masses atomiques à partir des harmoniques sphériques de Ψ
- [ ] D.2 : Prédire la masse et les propriétés des éléments superlourds (119, 120...)

### D.2 Biologie

- [ ] D.3 : Dériver le ratio pas/largeur de l'ADN = φ à partir de Ψ
- [ ] D.4 : Dériver la suite de Fibonacci en botanique : F_n = (H₁^n - (-H₁)^{-n})/H₆
- [ ] D.5 : Prédire l'angle optimal de ramification des plantes = 2π/φ² ≈ 137,5°

### D.3 Archéologie

- [ ] D.6 : Vérifier la coudée royale = π/6 sur des mesures indépendantes de différents sites
- [ ] D.7 : Vocalisation Tonga → correspondances phonétiques systématiques à documenter

---

## CATÉGORIE E — REPRODUCTIBILITÉ

### E.1 Vérification indépendante

- [ ] E.1a : Un tiers recalcule les 30 observables avec les formules publiées
- [ ] E.1b : Un tiers reproduit le χ²/ν = 1,13
- [ ] E.1c : Un tiers vérifie que m_H/v = 2φ√2/9 donne bien 125,2006 GeV

### E.2 Code open source

- [ ] E.2a : Le code de calcul (chi2_calc.py, abc_kernel.py) est documenté et exécutable par un tiers
- [ ] E.2b : Les formules sont publiées intégralement (tous les exposants, toutes les constantes)

---

## CATÉGORIE F — TESTS QUI TUERAIENT LA THÉORIE (falsification)

| # | Ce qui tuerait la TH | Statut actuel |
|---|---------------------|---------------|
| F.1 | Détection d'une particule supersymétrique au LHC | En attente |
| F.2 | Détection d'un graviton | En attente |
| F.3 | δ_CP mesuré ≠ 77,9° ± précision expérimentale | En attente (2028) |
| F.4 | Découverte d'une nouvelle constante fondamentale qui n'appartient pas à {φ, π, e, √2, √3, √5, e/π} | Aucune à ce jour |
| F.5 | Détection de WIMP (matière noire particulaire) | Négatif à ce jour (XENON, LZ) |
| F.6 | Masse du Higgs mesurée ≠ 125,2006 GeV (hors incertitude) | Pour l'instant : confirmé (125,20 ± 0,14) |
| F.7 | Une 4ᵉ famille de particules découverte | Aucune à ce jour |

---

## SYNTHÈSE : Feuille de route

```
PHASE 1 — Immédiat (2026)
├── Corriger m_d/m_u et m₃/m₂
├── Documenter la vocalisation Tonga → hiéroglyphes
└── Publier le code de calcul

PHASE 2 — Court terme (2026-2027)
├── Dériver les exposants entiers a priori (géométrie de jauge)
├── Dériver chaque Hₙ à partir de G[(Ψ₁)ⁿ]
└── Vérification indépendante par un tiers

PHASE 3 — Moyen terme (2027-2030)
├── Résultats de DUNE/T2HK → δ_CP
├── Dérivation complète du tableau périodique
└── Prédictions botaniques vérifiables

PHASE 4 — Long terme (2030-2040)
├── HL-LHC → couplage triple Higgs
├── Euclid/Rubin → équation d'état de l'énergie sombre
└── Confirmation ou infirmation complète
```
