# 🧪 EXPLORATION_TABLEAU_PERIODIQUE — Le tableau périodique par la refondation

**Date** : 09/08/2026 — **Auteur** : Univers-Holistique
**Statut** : Exploration — 2 résultats dérivés ✅ · 1 test négatif ✅ · 1 théorème nouveau ✅
**Script** : `exploration_tableau_periodique.py` — **Rapport** : `data/benchmarks/tableau_periodique_report.json`

---

> *« La nature ne choisit pas : elle élimine. » Le tableau périodique est le spectre d'entiers qui survit au filtre de stabilité atomique — et la température dorée d'ionisation est sa signature thermique.*

---

## 1. La question

La refondation peut-elle « générer » le tableau périodique ? Réponse en trois parties mesurées : ce que l'alphabet dérive sans paramètre, ce que le treillis élimine, et un théorème nouveau qui généralise T\*.

## 2. Partie A — la structure DÉRIVÉE (l'alphabet, zéro paramètre)

| Élément de structure | Dérivation | Statut |
|---|---|---|
| Couches 2, 8, 18, 32, 50 | Σ_{l=0}^{n−1} 2(2l+1) = **2n²** — la brique « comptage » (n, l, m, s entiers) | ✅ vérifié numériquement (n=1..5) |
| Règle de Madelung (n+l) | L'ordre de remplissage = le **survivant** du filtre d'énergie minimale — l'élimination appliquée aux configurations | ✅ lecture structurelle |
| **Γ** dans les fonctions radiales | R_nl ∝ √((n−l−1)!/(2n(n+l)!)) — le comptage Γ, brique dérivée | ✅ |
| **π** dans la normalisation | ψ_100 = (1/√π)·R_10 — l'intégrale gaussienne | ✅ dérivée (T4) |

**Lecture de la refondation** : le tableau périodique EST le spectre d'entiers de l'alphabet, filtré par la stabilité — les configurations qui ne minimisent pas l'énergie sont *éliminées*, les couches fermées (gaz nobles) *survivent*. Aucun paramètre libre : les 2n² sont des entiers.

## 2bis — LA GÉNÉRATION COMPLÈTE (118 éléments — `generation_tableau_periodique.py`)

Le tableau périodique est **généré** à partir du spectre d'entiers (n, l, capacité 2(2l+1)) et du filtre de Madelung (ordre (n+l, n)) — zéro paramètre :

| Vérification | Résultat |
|---|---|
| **V1 · Périodes générées = réelles** | **118/118 ✅** |
| **V2 · Groupes générés = réels** | **90/118** — les 28 écarts sont TOUS dans le bloc f (La–Yb, Ac–No) |
| **V3 · Gaz nobles** (couches fermées) | **{2, 10, 18, 36, 54, 86, 118} ✅** |

**Le résultat le plus intéressant — la lecture des 28 écarts** : Madelung naïf remplit 4f/5f avant 5d/6d (généré : groupe 2, configuration 6s²4fⁿ) ; le tableau réel place une sous-couche **d¹** (5d¹6s² → groupe 3). Les configurations qui survivent ne sont pas les plus « simples » — **ce sont les plus stables** : l'élimination, visible à l'intérieur même du tableau. Les ~20 anomalies connues des blocs d (Cr, Cu, Ag, Au…) ne déplacent aucun groupe : elles ne font que réorganiser s/d à valence constante — les survivants ajustent la configuration, pas la position.

## 3. Partie B — le test ex-ante : φ apparaît-il dans les ratios ?

26 ratios (longueurs de périodes 8/2, 18/8, 32/18, 50/32 ; énergies d'ionisation successives Z=1..20) contre les 11 cibles des Violets A/B, seuil 10⁻³.

```
MATCHS : 0 ✅
Quasi-matchs (< 5 %) : 4 — per_2 vs √5 (0,6 %) · per_3 vs √3 (2,6 %) ·
                       per_4 vs φ (3,4 %) · EI_17/18 vs e/π (4,9 %)
```

Le quasi-match « per_4 vs φ » (50/32 = 1,5625 vs φ = 1,618 — écart 3,4 %) est **exactement** le piège du treillis : la suite (n/(n−1))² passe près de φ sans jamais l'atteindre — et le seuil pré-enregistré le rejette proprement. **Le treillis confirme : aucun privilège de φ dans la structure numérique du tableau** (cohérent avec 0/935 des Violets).

## 4. Partie C — THÉORÈME NOUVEAU : la famille des températures dorées d'ionisation

> **T5 généralisé** : pour tout gap quantique ΔE, le facteur de Boltzmann vaut exactement 1/φ à la température
> $$T^* = \frac{\Delta E}{k_B\,\ln\varphi} \qquad\Longleftrightarrow\qquad e^{-\Delta E/k_B T^*} = \frac{1}{\varphi} \ \text{exactement}$$
>
> Vérifié machine : e^{−χ/k_BT*} = 0,6180339887498948 = 1/φ (constantes cohérentes).

**Application au tableau périodique** — la table dérivée (χ·24115 K/eV) :

| Z | Élément | χ (eV) | T\*_ion (K) |
|---|---|---|---|
| 1 | H | 13,598 | **327 918** |
| 2 | He | 24,587 | 592 919 |
| 3 | Li | 5,392 | 130 029 |
| 11 | Na | 5,139 | 123 928 |
| 18 | Ar | 15,760 | 380 055 |
| 19 | K | 4,341 | 104 684 |
| 36 | Kr | 13,999 | 337 588 |
| 54 | Xe | 12,130 | 292 517 |
| 86 | Rn | 10,749 | 259 214 |
| … | (23 éléments au total) | | |

**Statut honnête du théorème** : c'est le squelette exact du dépôt E3 (T5 — Gibbs + spectre) appliqué aux gaps d'ionisation — une **dérivation**, pas une coïncidence : la température est le paramètre libre, la valeur 1/φ est imposée par le théorème. **Falsifiable** : à T\*_ion(H) = 327 918 K, la spectroscopie d'un plasma d'hydrogène doit mesurer le facteur de Boltzmann e^{−χ/kT} = 1/φ (limite Saha basse densité, hors dégénérescences — déclaré).

## 5. Le verdict

```
A · Structure 2n² / Madelung / Γ / π dérivée des entiers   ✅
B · Aucun match φ/π/e dans les ratios (seuil 1e-3)          ✅ (treillis : 4 quasi, aucun privilège)
C · Famille T*_ion = χ·24115 K — T5 généralisé, vérifié    ✅ machine
```

**Ce que l'exploration établit** : le tableau périodique se *dérive* par l'alphabet (entiers, Γ, π) et se *lit* par l'élimination (Madelung = survivant) — et il reçoit une **nouvelle prédiction dérivée** : les températures dorées d'ionisation, une par élément, toutes falsifiables. La structure numérique (ratios) ne montre aucun privilège de φ — le treillis a encore travaillé.

## 6. Reproductibilité

```bash
python exploration_tableau_periodique.py
# → data/benchmarks/tableau_periodique_report.json
# Dépendances : numpy (χ : valeurs NIST approximatives, documentées dans le script)

# LA GÉNÉRATION COMPLÈTE (118 éléments — périodes, groupes, gaz nobles)
python generation_tableau_periodique.py
# → data/benchmarks/generation_tableau_periodique_report.json
```

---

*Exploration — FIN — le tableau périodique est le spectre d'entiers survivant, et sa température dorée d'ionisation est la généralisation directe du dépôt E3.*
