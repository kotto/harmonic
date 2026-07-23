# 🌊 Refonte — Harmonic Wavelet Attention Transformer (HWAT)

**Branche :** `feature/harmonic-transformer-refonte` (depuis `ka-care`)
**Date :** 23 juillet 2026
**Objectif :** Égaler la sélectivité d'un LLM classique avec un opérateur purement harmonique.

---

## 1. Diagnostic : pourquoi le modèle ondulatoire perd la sélectivité

### 1.1 Le théorème de Gabor (incertitude temps-fréquence)

$$\Delta t \cdot \Delta f \geq \frac{1}{4\pi}$$

L'architecture actuelle applique **une FFT globale** sur la séquence
(`harmonic_engine.py:246`). Conséquences directes :

| Grandeur | FFT globale | Attention (transformer) |
|---|---|---|
| Résolution fréquentielle `Δf` | `1/N` (maximale) | aucune |
| Résolution positionnelle `Δt` | `N` (nulle) | `1` (maximale) |
| Sélectivité token-à-token | ❌ perdue | ✅ préservée |

> **Une FFT globale confond deux tokens différents qui produisent le
> même spectre moyen.** C'est exactement la "perte de sélectivité"
> que vous observez. Ce n'est pas un bug d'implémentation : c'est une
> limite mathématique fondamentale (Gabor 1946).

### 1.2 L'encodeur HRR actuel aggrave le phénomène

`generative_encoder.py` et `holographic_encoder.py` encodent **tout dans
l'amplitude** par superposition additive `ψ = Σ ψ_i`. La phase n'est qu'un
sous-produit de la normalisation, elle ne porte aucune structure.

Or en physique ondulatoire :
- **Amplitude = énergie** → quantité, fréquence d'usage → *sémantique statistique*
- **Phase = position relative** → ordre, dépendance → *syntaxe*

En ignorant la phase comme canal syntaxique, le modèle actuel jette la
moitié de l'information disponible.

---

## 2. Analyse des 4 pistes

### Piste A — FFT multi-fenêtres (pseudo-ondelettes) ⭐⭐⭐⭐
`fft(1-64), fft(33-96), fft(65-128)`, fenêtres chevauchées.

- ✅ Récupère la localisation (chaque token apparaît dans plusieurs fenêtres)
- ✅ Implémentation triviale et réversible (ISTFT exacte)
- ⚠️ Fenêtres fixes = résolution d'échelle unique. Les vraies ondelettes
  (Morlet, Daubechies) font varier l'échelle dyadiquement.
- ⚠️ Seul, ne résout pas la sélectivité fine (une fenêtre reste globale en son sein)

### Piste B — Filtre adaptatif ⭐⭐⭐
Le filtre dépend du contenu de la phrase.

- ✅ Opérateur *appris* (équivalent convolutif spectral)
- ⚠️ Si calculé sur toute la phrase (pooling) → retombe dans le globalisme
- 💡 **Se combine naturellement avec A** : les poids des fenêtres deviennent
  contents-dépendants. C'est le pont entre ondelettes et attention.

### Piste C — Mémoire spectrale / attention compare les tokens ⭐⭐⭐⭐⭐
L'attention se fait directement, mais dans le domaine complexe.

- ✅ **C'est la clé de la sélectivité fine** (c'est ce que fait un transformer)
- ✅ `Q·K^T` → remplacé par cohérence de phase `cos(Δφ)` (zéro paramètre)
- ✅ Réutilise l'arsenal HRR existant (convolution circulaire, binding)
- 💡 **Référence** : FNet (Lee-Thorp 2021) prouve qu'on peut remplacer
  l'attention par FFT et garder 92 % de BERT — notre problème (sélectivité)
  est exactement leur point faible, et l'attention spectrale le résout.

### Piste D — Phase = syntaxe, Amplitude = sémantique ⭐⭐⭐⭐
Factorisation canonique de l'onde `ψ = A·e^{iφ}`.

- ✅ Insight physiquement exact, factorisation *naturelle*
- ✅ Répare la faille de l'encodeur actuel (qui jette la phase)
- ⚠️ Seul, ne suffit pas — il faut un mécanisme qui *exploite* la phase

---

## 3. Synthèse : aucune des 4 ne suffit seule

| Objectif | A | B | C | D | **Combinaison HWAT** |
|---|---|---|---|---|---|
| Localisation | ✅ | – | – | – | ✅ |
| Sélectivité fine | – | partielle | ✅ | – | ✅ |
| Syntaxe préservée | – | – | – | ✅ | ✅ |
| Opérateur appris | – | ✅ | ✅ | – | ✅ |
| Déterministe (vos contraintes) | ✅ | ⚠️ | ✅ | ✅ | ✅ |

**Conclusion : les 4 pistes sont les 4 faces d'une même pièce.**
Une solution complète les **combine en une seule architecture**.

---

## 4. Proposition : HWAT (Harmonic Wavelet Attention Transformer)

### 4.1 Principe unificateur

> **Un token est une ondelette complexe `(A, φ, position, échelle)`.**
> L'attention est une **cohérence de phase dans des fenêtres multi-échelles**.

La sélectivité ne vient **pas** de la FFT (qui reste globale par fenêtre),
mais de l'**attention spectrale** appliquée aux coefficients multi-fenêtres.
Un token apparaissant dans plusieurs fenêtres → sa signature multi-échelle
est **unique** → l'attention peut le distinguer.

### 4.2 Architecture

```
Token IDs (ordre fixe)
        │
        ▼
┌─────────────────────────────────────────────┐
│ 1. EMBEDDING HARMONIQUE DÉTERMINISTE         │
│   ψ = A · e^{iφ}                              │
│   A = amplitude sémantique (PPMI/SVD existant)│
│   φ = phase syntaxique (position + noyau ABC) │
│   → pas de bruit, pas de dropout              │
└──────────────────┬──────────────────────────┘
                   │ ψ ∈ ℂ^{L×D}
                   ▼
┌─────────────────────────────────────────────┐
│ 2. OPÉRATEUR SPECTRAL HARMONIQUE (×N blocs)   │
│   STFT multi-échelle dyadique                 │
│   (fenêtres 16/32/64, hop 50%, fenêtre Hann)  │
│   → coeffs [n_échelles × n_fenêtres × D]      │
│                                                │
│   + Attention spectrale (cohérence de phase)   │
│     att_{i,j} = softmax( cos(φ_i − φ_j) ⊙ A_i │A_j )│
│   → ramène la sélectivité token-à-token        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 3. MLP PAR TOKEN (zéro dropout)              │
│   y = W2·gelu(W1·x + b1) + b2                 │
│   non-linéarité + sélection                   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 4. TÊTE (LM / classification)                 │
│   logits = LayerNorm(x) @ E^T                 │
└─────────────────────────────────────────────┘
```

### 4.3 Conformité aux contraintes

| Contrainte | Implémentation HWAT |
|---|---|
| Poids déterministes | Seed = hash(token) via FNV-1a (déjà utilisé) |
| Opérateur spectral | STFT multi-échelle (numpy.fft) |
| MLP | `Linear → gelu → Linear` (zéro dropout) |
| Pas de dropout | Confirmé |
| Pas de bruit | Amplitude = PPMI exact, pas d'ε Gaussien |
| Pas d'augmentation | L'augmentation = identité |
| Ordre fixe | `for epoch: for sample in corpus:` (jamais shufflé) |

### 4.4 Apprentissage

L'apprentissage reste **ondulatoire** (cohérent avec l'existant) :
- **Non-supervisé** : mémoire holographique additive `H += ψ_fait` (déjà en place)
- **Supervisé** : cross-entropy sur la tête LM, SGD déterministe (lr fixe)
- Le gradient passe par l'ISTFT (différentiable nativement via numpy/torch)

### 4.5 Pourquoi ça devrait égaler un transformer classique

1. **Attention** = sélectivité fine token-à-token (piste C) ✅
2. **Ondelettes multi-échelles** = localisation (piste A) ✅
3. **Filtre adaptatif** = les fenêtres sont *contents-dépendantes*
   via l'attention de phase (piste B) ✅
4. **Phase syntaxique** = factorisation A/φ (piste D) ✅

Le coût computationnel est **O(L·log L)** par bloc (FFT) contre
`O(L²)` pour l'attention standard — c'est l'argument FNet.

### 4.6 Limites assumées (honnêteté)

- **L'apprentissage reste le défi principal** : un opérateur spectral
  pur n'apprend pas de représentations distribuées aussi riches qu'un
  transformer entraîné sur des téraoctets. HWAT est une **amélioration
  architecturale** sur l'existant, pas une promesse d'égaler GPT.
- La performance cible réaliste : **égaler un petit transformer**
  (≤ 125M params) sur des tâches de classification/sélectivité fine,
  pas un LLM de scale 70B.
- Le benchmark de validation (étape suivante) mesurera précisément
  la *récupération de sélectivité* par rapport à la FFT globale actuelle.

---

## 5. Plan d'implémentation

| Étape | Fichier | Description |
|---|---|---|
| 1 | `harmonic_transformer.py` | Classes : `HarmonicEmbedding`, `SpectralOperator`, `PhaseAttention`, `HarmonicBlock`, `HWAT` |
| 2 | `test_harmonic_transformer.py` | Test de l'invariant de Gabor : Δt·Δf + récupération de sélectivité |
| 3 | `benchmark_hwat.py` | Comparaison FFT-globale vs STFT-multi-échelle vs HWAT complet |

Voir `PLAN.md` pour le détail des étapes de code.
