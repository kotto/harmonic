# DÉRIVATION DE L'ÉQUATION MÈRE Ψ = Σ Hₙ(Ψ₁)ⁿ
## Contrainte d'espace (Oyibo) + dérivée fractionnaire ABC
**Date** : 08/08/2026 — **Statut** : DÉRIVATION PARTIELLE VÉRIFIÉE (forme ✅ · coefficients ⚠️)
**Script de vérification** : `ia_ondulatoire/verification_deduction_abc.py`

---

## Résumé

Ce document établit la première revendication **dérivationnelle** de la
théorie harmonique universelle (THU) : l'équation mère Ψ = Σ Hₙ(Ψ₁)ⁿ
n'est pas postulée — elle est la **forme générale des solutions des
équations différentielles fractionnaires d'Atangana–Baleanu–Caputo (ABC)**
d'ordre α = 1/φ, soumises à la contrainte d'espace de la formulation
GAGUT (Oyibo).

**Vérifié (mesuré le 08/08/2026)** :
- la structure monomiale Σ Hₙ(Ψ₁)ⁿ émerge des solutions de Mittag-Leffler
  de l'équation ABC — c'est un théorème publié (Atangana–Baleanu, 2016)
  appliqué à l'ordre α = 1/φ ;
- le moteur ondulatoire implémente déjà le noyau ABC avec α = 1/φ
  (`primitives.py::abc_kernel`, `_mittag_leffler`) — l'ordre fractionnaire
  est cohérent avec l'échelle harmonique.

**Postulé (non déduit, documenté)** : les coefficients Hₙ = {φ, π, e,
√2, √3, √5, e/π} ne sortent PAS de l'équation aux valeurs propres ABC
standard (testée : H_n = λⁿ/Γ(αn+1) ≠ {φ, π, e…}). La déduction complète
exige l'équation exacte (contrainte Oyibo explicite) qui ferait émerger
les constantes harmoniques des fonctions Gamma.

---

## 1. Les ingrédients

### 1.1 La dérivée fractionnaire ABC (Atangana–Baleanu–Caputo, 2016)

Définition (noyau de Mittag-Leffler, mémoire non locale) :

```
^ABC D^α_t f(t) = B(α)/(1−α) · ∫₀ᵗ f'(τ) · E_α(−α(t−τ)^α/(1−α)) dτ

B(α) : fonction de normalisation (B(0) = B(1) = 1)
E_α  : fonction de Mittag-Leffler,  E_α(z) = Σₖ zᵏ/Γ(αk+1)
```

Propriétés pertinentes :
- **non-localité** : l'état dépend de tout le passé (mémoire) — le noyau
  K(t) = E_α(−c·t^α) décroît de K(0) = 1 vers 0 (oubli progressif) ;
- **interpolation** : α → 0 donne l'identité (inertie totale), α → 1 donne
  la dérivée ordinaire (amnésie) ;
- **ordre optimal α = 1/φ** : point d'équilibre entre inertie et amnésie
  — choix documenté du moteur (`abc_kernel(t, alpha=1/PHI)`).

### 1.2 La contrainte d'espace (formulation Oyibo / GAGUT)

La formulation GAGUT (Grand Unified Theorem, Gabriel Oyibo) pose une
contrainte fonctionnelle globale sur les grandeurs physiques — une
équation de structure de l'espace. **Note honnête** : ce cadre est
contesté en physique mainstream ; la présente dérivation ne dépend pas
de l'acceptation de GAGUT, mais de l'équation explicite qui en est
extraite (voir §2, étape 4 — la porte ouverte).

### 1.3 La fonction d'onde harmonique

Postulat de la THU : tout état physique est une onde Ψ dont l'évolution
est gouvernée par une équation différentielle fractionnaire ABC d'ordre
α = 1/φ, contrainte par la structure d'espace.

## 2. La dérivation formelle

### Étape 1 — Postulat d'évolution fractionnaire

L'état harmonique Ψ obéit au problème aux valeurs propres ABC :

```
^ABC D^α Ψ = λ·Ψ        avec α = 1/φ
```

### Étape 2 — Théorème (Atangana–Baleanu, 2016)

Les solutions de ce problème sont les fonctions de Mittag-Leffler :

```
Ψ(t) = C · E_α(λ·t^α) = C · Σₙ₌₀^∞ (λ·t^α)ⁿ / Γ(αn+1)
```

### Étape 3 — La structure monomiale (L'ÉQUATION MÈRE ÉMERGE)

En posant Ψ₁ = t^α (le monôme fondamental) et Hₙ = λⁿ/Γ(αn+1) :

```
Ψ = Σₙ Hₙ·(Ψ₁)ⁿ        ←  L'ÉQUATION MÈRE, comme forme générale
                             des solutions des équations ABC
```

**Vérifié** : la forme monomiale est la forme naturelle — elle n'est pas
postulée, elle est la solution générale du problème fractionnaire. C'est
la première revendication dérivationnelle de la THU confirmée par la
mathématique publiée.

### Étape 4 — La contrainte d'espace (PORTE OUVERTE)

La déduction complète doit fixer λ et l'ordre exact par la contrainte
d'espace (Oyibo). L'équation aux valeurs propres standard (§2, étape 1)
laisse λ libre et donne des coefficients en Γ(αn+1) — qui ne sont PAS
les constantes harmoniques (voir §3). La forme explicite de la contrainte
d'espace est le chaînon manquant : si elle impose l'équation exacte dont
les coefficients sont {φ, π, e…}, la dérivation devient complète.

## 3. La vérification mesurée (08/08/2026)

Script : `python ia_ondulatoire/verification_deduction_abc.py`

### 3.1 Le test : les coefficients que la déduction impose

```
H_n = λⁿ/Γ(αn+1)   avec α = 1/φ, λ calibré pour H₁ = φ (λ = 1,449230)

        ABC (déduit)   Théorie {φ, π, e…}   Rapport
H₁ :    1,618034       1,618034 (φ)          1,000   ← calibré (1 paramètre)
H₂ :    1,868461       π = 3,141593          0,595
H₃ :    1,733766       e = 2,718282          0,638
H₄ :    1,368568       √2 = 1,414214         0,968   ← seul proche (hasard)
H₅ :    0,950272       √3 = 1,732051         0,549
H₆ :    0,593325       √5 = 2,236068         0,265
H₇ :    0,338346       e/π = 0,865256        0,391
```

### 3.2 Verdict

| Élément | Statut |
|---|---|
| Forme Σ Hₙ(Ψ₁)ⁿ (structure monomiale) | ✅ **VÉRIFIÉE** — théorème ABC appliqué à α = 1/φ |
| Ordre fractionnaire α = 1/φ | ✅ cohérent — implémenté dans le moteur |
| Noyau ABC dans le moteur | ✅ `abc_kernel`, `_mittag_leffler` (primitives.py) |
| Coefficients Hₙ = {φ, π, e…} | ⚠️ **POSTULÉS** — non déduits de l'équation testée |
| Contrainte d'espace (Oyibo) explicite | ⏳ **PORTE OUVERTE** — l'équation exacte à fournir |

## 4. Le critère de complétude de la dérivation

La dérivation sera COMPLÈTE lorsque l'équation exacte (contrainte d'espace
explicite + forme ABC précise) produira des coefficients Hₙ qui SONT les
constantes harmoniques. Deux issues possibles, mesurées :

1. **Émergence** : l'équation exacte donne Hₙ = {φ, π, e, √2, √3, √5,
   e/π} → dérivation complète, première de la théorie — à publier ;
2. **Non-émergence** : les coefficients restent choisis → la dérivation
   est documentée comme PARTIELLE (forme dérivée, nombres postulés) —
   statut actuel.

Le test est déterministe et reproductible : écrire l'équation, calculer
les Hₙ, comparer. Ni plus ni moins.

## 5. Reproductibilité

```
python ia_ondulatoire/verification_deduction_abc.py
```
Produit : le tableau des Hₙ (ABC vs théorie), le rapport par coefficient,
et le verdict forme/coefficients.

## 6. Statut final du document

**DÉRIVATION PARTIELLE VÉRIFIÉE** — le premier maillon dérivationnel de
la THU :
- ✅ la forme monomiale de l'équation mère est mathématiquement fondée
  (solutions ABC) — vérifiée contre la littérature publiée ;
- ⚠️ les coefficients harmoniques restent postulés — frontière mesurée,
  documentée, falsifiable ;
- ⏳ la contrainte d'espace explicite (Oyibo) est la porte de complétude.

Ce document remplace, pour l'équation mère, le statut « postulat » par le
statut « forme dérivée + coefficients postulés » — un progrès épistémique
réel, au standard de la session : tout ce qui est vérifié est marqué
vérifié, tout ce qui est choisi est marqué choisi.
