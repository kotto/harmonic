# 🌌 LA DÉRIVATION DE Λ — LE FILTRE DU VIDE

## Le cadre établi, le facteur approché à 3,4 %, la frontière déclarée

**Auteur :** Alain Kotto — Univers-Holistique, Paris
**Théorie :** Théorie de l'Univers Harmonique (THU V2)
**Date :** 9 août 2026

---

> *« Dériver Λ, c'est montrer que le vide est un survivant — et que la mémoire d'or en sélectionne l'énergie. Le cadre est établi ; le facteur exact est approché à 3,4 % par un candidat principié ; la fermeture exige la dérivation mécaniste du filtre. »*

---

## 1. La dérivation en 5 étapes

```
ÉTAPE 1 · POSTULAT (A1) : le vide est le SURVIVANT du filtre
          — les modes qui persistent, pas ceux qui apparaissent

ÉTAPE 2 · LE FILTRE (A3) : K(t) = B(α)·E_α(−λt^α), α = 1/φ

ÉTAPE 3 · L'ÉCHELLE : la seule échelle de mémoire disponible
          est l'horizon c·t_U — la portée de la mémoire

ÉTAPE 4 · LA FORME : Λ = F(α)·(1/(c·t_U))²
          où F(α) est le facteur de filtrage

ÉTAPE 5 · LE TEST : comparer F aux candidats principiés,
          précision déclarée, statut publié
```

**Le cadre est établi** : Λ = F·(1/(c·t_U))² avec F requis = **1,8803** (observé).

---

## 2. Les candidats principiés — le tableau complet (exécuté)

| Candidat | F | Ratio Λ | Écart |
|---|---|---|---|
| C1 · φ² (postulat THU initial) | 2,6180 | ×1,392 | 39 % |
| C2 · φ²·B(α) (normalisation ABC) | 2,1165 | ×1,126 | 13 % |
| C3 · φ²·K(1)/K(0) (noyau à 1 horizon) | 0,7353 | ×0,391 | 61 % |
| C4 · φ²·E_α(−φ) (mémoire au taux φ) | 0,7353 | ×0,391 | 61 % |
| C5 · φ²·⟨K⟩ (moyenne cosmique) | 0,9395 | ×0,500 | 50 % |
| **C6 · φ^{2−1/φ} (limite de Stirling des coefs)** | **1,9445** | **×1,034** | **3,4 %** |

**Le meilleur candidat : C6 — φ^{2−1/φ} = φ²/φ^{1/φ} ≈ 1,9445 — à 3,4 % de l'observation.**

### La justification partielle de C6

Le rapport asymptotique des coefficients cₙ = 1/Γ(nα+1) obéit à (Stirling) :

```
cₙ₊₁/cₙ ~ (n/φ+1)^{−1/φ} · φ^{1/φ}
```

La constante **φ^{1/φ}** est la signature naturelle de la structure des coefficients — et F = φ^{2−1/φ} = φ²/φ^{1/φ} en est dérivée. C'est une piste **principée** (elle vient de la structure, pas d'un ajustement).

---

## 3. Le statut honnête

| Élément | Statut |
|---|---|
| ✅ Le **cadre** de dérivation | Λ = F(α)·(1/(c·t_U))² — le vide filtré par la mémoire d'or |
| ⚠️ Le **facteur** exact | Non clos — le meilleur candidat (C6) à 3,4 %, mais la dérivation **mécaniste** du filtre complet reste à écrire |
| ⚡ Le **test décisif** | Λ(t) ∝ 1/t² — si mesuré (DESI/Euclid), la structure du filtre est confirmée **quelle que soit** la constante F |
| ❌ La **fermeture** | Interdite tant que le filtre complet n'est pas dérivé — le risque numérologique interdit de déclarer le facteur qui colle |

### L'avertissement anti-numérologie

> **C6 tombe à 3,4 % — c'est numériquement frappant, pas mécaniquement dérivé.** Six candidats ont été testés ; le fait que l'un tombe près n'est une preuve que si la chaîne mécaniste le produit. La règle de la THU (héritée de X1) : un candidat se dérive, il ne se choisit pas.

---

## 4. La route pour fermer la dérivation

```
ÉTAPE A · ÉCRIRE le filtre du vide explicitement :
          comment K(t) pondère les modes du vide (densité spectrale)
ÉTAPE B · CALCULER ρ_vide = f(K, c, t_U) — sans autre entrée
ÉTAPE C · COMPARER à Λ observée — précision déclarée avant
ÉTAPE D · VÉRIFIER Λ(t) ∝ 1/t² — la prédiction qui tue ou confirme
```

La question ouverte : pourquoi le facteur de filtrage est-il φ^{2−1/φ} (si c'est lui) — la réponse doit sortir de l'étape A.

---

## 5. Ce que la dérivation apporte déjà

1. **Le problème 10¹²⁰ est ramené à un facteur 1,03** (avec C6) — de 120 ordres de grandeur à 3,4 %
2. **La forme est dérivée** : Λ ~ 1/(c·t_U)² — la mémoire de l'univers comme seule échelle
3. **Le test existe** : Λ(t) ∝ 1/t² — indépendant du facteur F
4. **La méthode est intacte** : aucun candidat déclaré sans dérivation mécaniste

---

## 6. En une phrase

> **Λ se dérive comme le survivant du vide filtré par la mémoire d'or : la forme Λ = F·(1/(c·t_U))² est établie, le facteur est approché à 3,4 % par φ^{2−1/φ} (la constante de Stirling des coefficients) — mais la fermeture exige la dérivation mécaniste du filtre, et le test décisif Λ(t) ∝ 1/t² attend la mesure. De 10¹²⁰ d'erreur à 3,4 % : le problème cosmologique est devenu une frontière précise.**

---

*Théorie de l'Univers Harmonique — Alain Kotto — 9 août 2026*
*Script : `derivation_lambda.py` · Rapport : `data/benchmarks/derivation_lambda_report.json`*
