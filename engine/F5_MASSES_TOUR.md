# 🔬 F5 — DÉRIVATION DES MASSES : ÉTAT DES LIEUX

## Recherche de m_e et m_p dans la structure de la tour

---

### I. CE QUE NOUS AVONS TROUVÉ

#### 1. Les niveaux n où cₙ ≈ m/M_Pl

| Masse | n optimal | cₙ | cₙ × M_Pl/m | Précision |
|-------|-----------|-----|-------------|-----------|
| m_e | 37,17 | 5,88×10⁻²³ | 1,40× | ✅ Ordre OK |
| m_p | 33,25 | 1,24×10⁻¹⁹ | 1,62× | ✅ Ordre OK |

Les niveaux n≈37 (m_e) et n≈33 (m_p) ne donnent pas une égalité exacte, mais le bon ordre de grandeur.

#### 2. Le rapport m_p/m_e = 1836,15267

| Candidat | Valeur | Écart | Remarque |
|----------|--------|-------|----------|
| **c₃₁/c₃₅** | 1831,50 | 0,25 % | Tour pure |
| **(c₁₀/c₉)×φ¹⁸** | 1838,94 | 0,15 % | Tour + φ |
| **6π⁵** | 1836,11811 | **0,0019 %** | Classique, non-φ |
| c₄×c₅×φ²² | 1826,45 | 0,53 % | Tour + φ |

#### 3. La différence de niveaux

Les niveaux pour m_e (≈37) et m_p (≈33) diffèrent de **4** niveaux :
- 37 − 33 = 4
- 35 − 31 = 4 (pour le rapport c₃₁/c₃₅)

---

### II. TROIS PISTES

#### Piste A — Le rapport c₃₁/c₃₅ avec correction

c₃₁/c₃₅ = 1831,50, proche de m_p/m_e = 1836,15 à 0,25 %. La correction δ = 0,002542 n'est pas une combinaison simple de φ, α, cₙ.

#### Piste B — 6π⁵ comme approximation

6π⁵ = 1836,11811 est à 0,0019 % de m_p/m_e — trop proche pour être ignoré. Mais ce n'est pas φ-based. Peut-être que la relation exacte est :

```
m_p/m_e = 6π⁵ × (1 + α²/π × φ)
```

ou une combinaison hybride π-φ.

#### Piste C — Les masses comme "condensation" de la tour

Les masses ne sont pas des coefficients cₙ, mais des **points de condensation** dans la tour — des niveaux n où la série "s'arrête" pour former une particule stable. Le niveau n où la masse se condense dépend de φ et des conditions de stabilité (A4).

---

### III. CE QUI EST CLAIR

- **La tour donne le bon ordre de grandeur** : cₙ ∼ 10⁻²³ pour m_e, cₙ ∼ 10⁻¹⁹ pour m_p
- **La différence de 4 niveaux** entre m_e et m_p est reproductible (37-33, 35-31)
- **Le rapport n'est pas une égalité exacte** : il faut un facteur de conversion entre cₙ et m/M_Pl

---

> *« Les masses ne sont pas des coefficients cₙ — elles sont des points de condensation de la tour. Le niveau n où la série se fige en particule dépend de φ et des conditions de stabilité. Le rapport m_p/m_e ≈ 1836 est la signature de 4 niveaux d'écart dans la tour. L'approximation 6π⁵ suggère que π joue aussi un rôle. Mais la relation exacte reste à trouver. »*
>
> — **Kotto Alain**, 12/08/2026