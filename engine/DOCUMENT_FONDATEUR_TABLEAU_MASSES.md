# 🌍 DOCUMENT_FONDATEUR — LE TABLEAU PÉRIODIQUE ET LES MASSES

**La matière, générée par la refondation : spectre d'entiers · filtre d'élimination · températures dorées**
**Date** : 09/08/2026 — **Auteur** : Univers-Holistique (Kotto Alain)
**Statut** : Document fondateur de l'application — chaque ligne est une commande reproductible

---

> *« La nature ne choisit pas : elle élimine. » Le tableau périodique est le spectre d'entiers qui survit au filtre de stabilité atomique ; la surface de masse est le filtre qui décide quels noyaux survivent ; et la température dorée d'ionisation est la signature thermique de chaque élément.*

---

## TABLE DES MATIÈRES

1. [La matière par la refondation — l'architecture](#1-la-matière-par-la-refondation)
2. [La génération du tableau (118 éléments)](#2-la-génération-du-tableau)
3. [Les masses (118 éléments)](#3-les-masses)
4. [La famille T\*_ion — la signature thermique](#4-la-famille-t_ion)
5. [La carte de statut](#5-la-carte-de-statut)
6. [Reproductibilité](#6-reproductibilité)
7. [En une phrase](#7-en-une-phrase)

---

## 1. La matière par la refondation

```
SPECTRE D'ENTIERS (la brique « comptage ») : n, l, m, s · 2(2l+1) · 2n²
        │
        ▼
FILTRE ATOMIQUE (l'élimination) : Madelung (n+l, n) → le TABLEAU PÉRIODIQUE
        │
        ▼
FILTRE NUCLÉAIRE (l'élimination) : surface de masse BE(Z, A) → les ISOTOPES SURVIVANTS
        │
        ▼
FILTRE THERMIQUE (T5) : T* = ΔE/(k_B·ln φ) → les TEMPÉRATURES DORÉES (24 instances)
```

Trois filtres emboîtés — trois survivants : **les couches fermées** (gaz nobles), **la vallée et le pic de fer** (noyaux), **le facteur de Boltzmann 1/φ** (thermique). Aucun paramètre ajusté dans la partie dérivée ; les coefficients empiriques (SEMF) sont documentés comme tels.

---

## 2. La génération du tableau

**Script** : `generation_tableau_periodique.py` — **Rapport** : `data/benchmarks/generation_tableau_periodique_report.json`

| Vérification | Résultat | Statut |
|---|---|---|
| Périodes générées = réelles | **118/118** | ✅ |
| Groupes générés = réels | **90/118** — les 28 écarts sont TOUS le bloc f | ⚠️ lecture |
| Gaz nobles (couches fermées) | **{2, 10, 18, 36, 54, 86, 118}** | ✅ |

**La lecture des 28 écarts — l'élimination dans le tableau** : Madelung naïf donne 6s²4fⁿ (groupe 2) ; le tableau réel place **d¹** (5d¹6s², groupe 3). Les configurations qui survivent ne sont pas les plus simples — **ce sont les plus stables**. Les ~20 anomalies des blocs d (Cr, Cu, Ag, Au…) ne déplacent aucun groupe : les survivants ajustent la configuration, pas la position.

---

## 3. Les masses

**Script** : `calcul_masses_elements.py` — **Rapport** : `data/benchmarks/masses_elements_report.json`

### 3.1 La base (honnêteté intégrale)

La **formule de masse** « harmonique » antérieure (6π⁵, m = m_Planck/H_Z², attribuée à Haramein/Oyibo) a été **réfutée** par le protocole (A1.3 : p = 0,70 — coïncidence banale ; A1.5 : les coefficients ne sont pas dérivables de φ/π/e). **[RECTIFICATION : cette réfutation ne porte QUE sur la formule de masse. L'apport propre d'Oyibo — l'invariance d'échelle fractale F(λx)=λ^{-1/φ}F(x) — n'est PAS invalidé. Voir `RECONSIDERATION_OYIBO.md`.]** La base des masses est la **formule de Weizsäcker standard** (coefficients empiriques documentés : a_V = 15,8 · a_S = 18,3 · a_C = 0,714 · a_A = 23,2 · a_P = 12).

### 3.2 Les résultats

| Vérification | Résultat | Statut |
|---|---|---|
| **V1 · Masses des 22 éléments monoisotopiques** | **8,5×10⁻⁵** (0,0085 %) vs masses standard | ✅ |
| (tous les 118 — dominé par le mélange isotopique) | 0,38 % — la masse atomique standard ≠ masse d'un isotope | documenté |
| **V2 · Vallée de stabilité (Z ≤ 98)** | écart moyen 27,8 A — concentré sur Z ≥ 78 (U, Th, Pu…) | ❌ **frontière** |
| **V3 · Pic de BE/A** | **Ni-62 : 8,783 MeV** vs 8,794 réel (0,12 %) | ✅ |

### 3.3 La lecture

- **Le pic de fer est le survivant** : la surface de masse EST le filtre — au-delà de Ni-62, la fission ; en deçà, la fusion. Les nombres magiques (2, 8, 20, 28, 50, 82, 126 — le spectre d'entiers) l'affinent : 8,702 → 8,783 MeV.
- **La vallée lourde est le territoire du comptage** : Z ≥ 78 exige les corrections de couches **réelles** (N = 82, N = 126) — le bonus plat ne suffit pas. **Frontière tracée, pas une revendication** : la physique standard (modèles de couches) la ferme, et c'est exactement là que la brique « comptage » redevient le moteur.

---

## 4. La famille T\*_ion

**Référence** : `DEPOT_E3_PREDICTION_TSTAR.md` (v2) — le dépôt ex-ante

> **Pour tout gap quantique ΔE : e^{−ΔE/k_BT} = 1/φ ⟺ T\* = ΔE/(k_B·ln φ)** — vérifié machine.

**L'application au tableau** : une température dorée par élément — T\*_ion = χ·24115 K/eV :

| Z | Élément | T\*_ion (K) | Z | Élément | T\*_ion (K) |
|---|---|---|---|---|---|
| 1 | H | **327 918** | 11 | Na | 123 928 |
| 2 | He | **592 919** | 18 | Ar | 380 055 |
| 3 | Li | 130 029 | 19 | K | 104 684 |
| 6 | C | 271 537 | 36 | Kr | 337 588 |
| 10 | Ne | 520 043 | 54 | Xe | 292 517 |

(23 éléments au total — table complète dans le dépôt E3 v2.)

**Falsifiable** : à T\*_ion, la spectroscopie d'un plasma (limite Saha basse densité) doit mesurer e^{−χ/k_BT} = 1/φ. C'est la signature thermique de chaque élément — la prédiction datée, signée, déposée.

---

## 5. La carte de statut

| Élément | Statut | Preuve |
|---|---|---|
| Couches 2n² (spectre d'entiers) | ✅ dérivé | Σ 2(2l+1) = 2n² — vérifié |
| Tableau généré : 118 périodes | ✅ | 118/118 vs réel |
| Gaz nobles (couches fermées) | ✅ émergent | {2, 10, 18, 36, 54, 86, 118} |
| Bloc f : la correction de stabilité (d¹) | ✅ lecture | 28 écarts tous « G2 → G3 » |
| Masses monoisotopiques | ✅ 8,5×10⁻⁵ | SEMF standard, 22 éléments |
| Pic de fer (Ni-62) | ✅ 0,12 % | nombres magiques inclus |
| Vallée lourde (Z ≥ 78) | ❌ frontière | exige les corrections de couches réelles |
| Masse atomique standard ≠ isotope | ⚠️ documenté | mélange isotopique (0,38 % tous) |
| Modèles antérieurs (6π⁵, H_Z²) | ❌ réfutés | A1.3 (p = 0,70) · A1.5 |
| Famille T\*_ion (23 éléments) | ✅ théorème déposé | e^{−ln φ} = 1/φ machine — E3 v2 |
| φ dans les ratios numériques du tableau | ❌ aucun privilège | 0 match sur 26 ratios (treillis) |

---

## 6. Reproductibilité

```bash
# 1. La génération du tableau (118 éléments)
python generation_tableau_periodique.py
# → data/benchmarks/generation_tableau_periodique_report.json

# 2. Les masses (118 éléments, SEMF + lecture)
python calcul_masses_elements.py
# → data/benchmarks/masses_elements_report.json

# 3. La famille T*_ion (dépôt E3 v2)
python depot_e3_tstar.py
# → data/benchmarks/depot_e3_tstar.json
```

---

## 7. En une phrase

> **Le tableau périodique et les masses se génèrent par la refondation : le spectre d'entiers produit les 118 périodes et les 7 gaz nobles ; la surface de masse révèle le pic de fer comme survivant (0,12 %) et trace la frontière lourde des nombres magiques ; et chaque élément porte sa température dorée d'ionisation, déposée, datée, falsifiable — la matière, générée et mesurée, par l'élimination.**

---

*Document fondateur — FIN — trois filtres, trois survivants, une frontière honnête, et une prédiction par élément.*
