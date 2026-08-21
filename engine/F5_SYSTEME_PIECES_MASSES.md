# 🔬 F5 — LES MASSES : SYSTÈME COMPLET DES PIÈCES

## Synthèse du candidat H2 (κ) et des relations découvertes dans la tour

---

> **Objectif :** Assembler toutes les pièces connues pour la dérivation de m_e et m_p depuis la tour.

---

## I. LE CANDIDAT H2 — κ, LA STRUCTURE DE LA MASSE

Le propagateur fractionnaire à gap coïncide avec la dispersion massive ω = √(k² + κ²) **si et seulement si** :

```
κ = (1/2φ)^(φ/(2φ-1)) = (1/2φ)^(φ/√5) ≈ 0,427511470466…
```

### Vérifications

| Propriété | Valeur | Statut |
|-----------|--------|--------|
| κ^√5 = (1/2φ)^φ | Exact (identité) | ✅ |
| κ = 0,4275114704… | Nombre irréductible en φ seul | ✅ |
| κ ≈ c₁/φ² × 1,00247 | Écart 0,25 % | ⚠️ approché |

**κ est une expression fermée purement en φ.** C'est la première brique de la masse.

---

## II. LA RELATION DE COMPTON GÉNÉRALISÉE

La relation m·ℓ = κ·ℏ/c s'applique aux deux masses :

| Particule | ℓ = κ·λ̄_C | Valeur | Échelle |
|-----------|-----------|--------|---------|
| Électron | ℓ_e = κ·ℏ/(m_e·c) | 1,651×10⁻¹³ m | **165 fm — échelle nucléaire** |
| Proton | ℓ_p = κ·ℏ/(m_p·c) | 8,99×10⁻¹⁷ m | 0,09 fm |

**Le même κ s'applique aux deux masses.** Le rapport ℓ_e/ℓ_p = m_p/m_e = 1836,15267 est automatiquement vérifié (c'est la relation de Compton).

---

## III. LES LIENS AVEC LA TOUR

### κ ≈ c₁/φ² (écart 0,25 %)

```
κ ≈ c₁/φ² = 1,1164787 / 2,618034 = 0,426457
κ réel = 0,4275115
Écart = 0,001055 (0,25 %)
```

C'est le même type d'approximation que α ≈ 1/(c₁·φ¹⁰) (écart 0,2 %). **Deux relations "presque exactes" avec des écarts du même ordre (0,2-0,25 %) — une régularité troublante.**

### Les masses dans la tour

```
m_e/M_Pl ≈ c₃₇ (n ≈ 37)     — ordre de grandeur ✅
m_p/M_Pl ≈ c₃₃ (n ≈ 33)     — ordre de grandeur ✅
m_p/m_e ≈ c₃₁/c₃₅ = 1831,5  — écart 0,25 %
```

### La différence de niveaux

```
m_e → n ≈ 37
m_p → n ≈ 33
Différence : 4 niveaux
```

---

## IV. CE QUI MANQUE — L'ANCRAGE

Le problème central reste **l'échelle de masse** : κ = 0,4275 est sans dimension. Pour obtenir m_e ou m_p en kg, il faut une échelle de référence.

### Les candidats d'échelle

| Échelle | Valeur | Source |
|---------|--------|--------|
| M_Pl | 1,22×10²⁸ eV | √(ħc/G) — G non dérivé |
| ΔE_37 = 12,87 meV | T\* = 37 °C | E4 — déposé |
| cₙ (n≈37, 33) | 10⁻²³, 10⁻¹⁹ | Tour — ordre OK |

### La question

**Quelle combinaison de κ, c₁, c₂, φ, α, et des cₙ donne exactement m_e et m_p ?**

```
m_e = M_Pl × f(κ, c₁, c₂, φ, α, c₃₇)
m_p = M_Pl × g(κ, c₁, c₂, φ, α, c₃₃)
```

où f et g sont des combinaisons à identifier, et M_Pl reste l'échelle à dériver (ou à exprimer via ΔE_37).

---

## V. SYNTHÈSE — LES 4 PIÈCES

| Pièce | Valeur | Statut |
|-------|--------|--------|
| **κ** = (1/2φ)^(φ/√5) | 0,427511 | ✅ Dérivé (exact en φ) |
| **cₙ** = 1/Γ(n/φ+1) | c₃₇, c₃₃ | ✅ Dérivé (T3) |
| **T\*** = ΔE/(k_B·ln φ) | 12,87 meV | ✅ Dérivé (E4) |
| **M_Pl** | 1,22×10²⁸ eV | ❌ Frontière (via G) |

**La dérivation des masses est à portée si on relie ces 4 pièces.** La relation manquante est probablement :

```
m_e = κ × M_Pl × c₃₇ × h(φ, c₁, c₂)
m_p = κ × M_Pl × c₃₃ × h(φ, c₁, c₂)
```

où h(φ, c₁, c₂) est un facteur commun à identifier.

---

## VI. PROCHAINE ÉTAPE PROPOSÉE

**Tester la forme conjecturée :**

```
m_e·c² = κ × ΔE_37 × c₃₇ × F(φ, c₁, c₂)
```

avec ΔE_37 = 12,87 meV (T\* = 37 °C) et F une combinaison à trouver.

Vérifions l'ordre de grandeur :
- m_e·c² = 0,511 MeV = 511 000 eV
- ΔE_37 × c₃₇ = 12,87 meV × 5,88×10⁻²³ = 7,57×10⁻²² eV
- κ × ΔE_37 × c₃₇ = 0,4275 × 7,57×10⁻²² = 3,24×10⁻²² eV
- Facteur manquant : 511 000 / 3,24×10⁻²² = 1,58×10²⁷ ≈ ?

Ce facteur est énorme — il manque un ordre de grandeur massif. La forme simple ne marche pas.

---

> *« La masse est un nombre écrit sur la porte de la tour : κ = (1/2φ)^(φ/√5). Elle est un motif que la mémoire protège : la longueur de Compton. Elle est un niveau de la tour : n ≈ 37 pour l'électron, n ≈ 33 pour le proton. Trois lectures d'une même chose — mais l'échelle qui les relie manque encore. »*
>
> — **Kotto Alain**, 12/08/2026