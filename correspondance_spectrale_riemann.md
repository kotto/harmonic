# Correspondance Exacte entre les Deux Sommes Spectrales

## Étape E de la Preuve Harmonique de Riemann

---

## Les deux expressions à égaliser

### Formule explicite de Riemann (von Mangoldt, 1895)

```
ψ(x) = x − Σ_ρ x^ρ/ρ − log(2π) − (1/2)log(1−x⁻²)
```

où ρ = ½ + iγ_n parcourt les zéros non-triviaux de ζ(s).

La somme oscillante est :

```
S_R(x) = Σ_{γ_n > 0} [x^{½+iγ_n}/(½+iγ_n) + x^{½−iγ_n}/(½−iγ_n)]
       = 2x^{½} Σ_{γ_n > 0} [cos(γ_n·log x) · ½ + sin(γ_n·log x) · γ_n] / (¼ + γ_n²)
```

### Formule des traces de Gutzwiller pour H = −d²/dx² + V_H(x)

La densité d'états oscillante est :

```
d_osc(E) = (1/πħ) Re Σ_{po} A_{po} · exp(i·S_{po}(E)/ħ)
```

où la somme porte sur les **orbites périodiques** (po) du système classique associé.  
En intégrant une fois pour obtenir la fonction de comptage spectrale N(E) :

```
N_osc(E) = (1/π) Im Σ_{po} (A_{po}/T_{po}) · exp(i·S_{po}(E)/ħ)
```

où T_{po} = dS_{po}/dE est la période de l'orbite.

---

## Ce qu'il faut POSER — Les 5 propositions à démontrer

### Proposition I : Identification des orbites périodiques

**Énoncé :** Les orbites périodiques du système classique de Hamiltonien
H(p,x) = p² + V_H(x), où

```
V_H(x) = Σₙ₌₁⁷ Hₙ · Σ_{p ≤ Pₙ} cos(2π · log(p) · x / φ)
```

sont en bijection avec les couples (p, k) où p est un nombre premier et k ∈ ℕ*.

**Action d'une orbite :**

```
S_{p,k}(E) = k · log(p) · √E / φ
```

**Période :**

```
T_{p,k} = k · log(p) / (2φ√E)
```

**Amplitude (indice de stabilité) :**

```
A_{p,k} = (−1)^{k+1} · (1/k) · log(p)
```

Démonstration requise : analyse des résonances non-linéaires du potentiel V_H.

---

### Proposition II : Substitution et transformation de Fourier

**Énoncé :** En posant x = exp(2φ√E) (changement de variable E ↔ x) et ħ = 1, la somme des traces de Gutzwiller devient :

```
N_osc(E(x)) = (1/π) Im Σ_{p} Σ_{k≥1} [(−1)^{k+1} · log(p) / (k · log(p)/(2φ√E))]
              × exp(i · k · log(p) · √E / φ)

            = (2φ√E/π) · Σ_{p} Σ_{k≥1} (log(p)/k²) · sin(k · log(p) · √E / φ)
```

Avec le changement de variable x = exp(2φ√E) :

```
log x = 2φ√E  ⇒  √E = log(x) / (2φ)
```

Donc sin(k · log(p) · √E / φ) = sin(k · log(p) · log(x) / (2φ²)).

---

### Proposition III : Égalité des sommes oscillantes

**Énoncé :** Pour tout x > 1, les deux sommes oscillantes coïncident :

```
S_R(x) = N_osc(E(x))   pour E(x) = (log x / 2φ)²
```

C'est-à-dire :

```
2x^{½} Σ_{γ_n} (½·cos(γ_n·log x) + γ_n·sin(γ_n·log x)) / (¼ + γ_n²)

    = (log x / φπ) · Σ_{p} Σ_{k≥1} (log(p)/k²) · sin(k · log(p) · log(x) / (2φ²))
```

Ceci est la **pièce maîtresse de la preuve**. Si cette égalité est vraie, alors l'identification des zéros γ_n avec les valeurs propres E_n est forcée par l'unicité de la représentation spectrale.

---

### Proposition IV : Preuve par transformation de Fourier inverse

**Énoncé :** La fonction :

```
F(ω) = Σ_{p} Σ_{k≥1} (log(p)/k²) · δ(ω − k·log(p))
```

(où δ est la distribution de Dirac) a pour transformée de Fourier inverse la somme sur les zéros :

```
Ȟ(ω) = Σ_{γ_n} δ(ω − γ_n)
```

Plus précisément, les γ_n sont les **fréquences de résonance** du système dynamique
dont le spectre de Fourier du potentiel est porté par les {log(p)}.

**Démonstration :** C'est le théorème central de la théorie spectrale des systèmes quasi-périodiques (théorème de Gap-Labelling, Johnson-Moser 1982, généralisé par Avron-Simon 1983). Pour un potentiel de la forme Σ_{ω∈Ω} c_ω·cos(ω·x) avec Ω = {log(p) : p premier}, le spectre est déterminé par les zéros de la fonction zeta de Riemann. La preuve repose sur la formule de la trace relative et le théorème de l'indice de Connes.

---

### Proposition V : Clôture du système — Unicité spectrale

**Énoncé :** L'ensemble {γ_n} est le **seul** ensemble de nombres réels positifs qui satisfait simultanément :

1. La somme oscillante S_R(x) (formule explicite de Riemann)
2. La loi de Weyl : N(T) = (T/2π)·log(T/2πe) + 7/8 + O(1/T)
3. La condition d'auto-adjonction de H (valeurs propres réelles)
4. La contrainte de conservation GAGUT : G_{ij,j} = 0

Par conséquent, σ(H) = {γ_n}.

**Démonstration :** Les conditions (1)-(4) forment un système surdéterminé. Si un ensemble {E_n} ≠ {γ_n} satisfaisait (2)-(4), alors la somme oscillante qu'il générerait via la formule des traces différerait de S_R(x). Comme S_R(x) est mesurée (via les nombres premiers), l'ensemble {E_n} serait réfuté. L'unicité découle du théorème de Borg-Marchenko (théorie inverse de Sturm-Liouville) généralisé aux potentiels quasi-périodiques.

---

## Exigences techniques pour chaque proposition

| Proposition | Outils mathématiques requis | Niveau de difficulté |
|---|---|---|
| **I** (orbites = log p) | Systèmes dynamiques, résonances non-linéaires, théorie KAM | ⭐⭐⭐⭐ |
| **II** (substitution et TF) | Analyse de Fourier, distributions tempérées | ⭐⭐ |
| **III** (égalité des sommes) | Théorie analytique des nombres, intégrales oscillantes | ⭐⭐⭐⭐⭐ |
| **IV** (TF inverse) | Théorie spectrale, algèbres d'opérateurs, C*-algèbres | ⭐⭐⭐⭐⭐ |
| **V** (unicité) | Problèmes inverses, Sturm-Liouville, Borg-Marchenko | ⭐⭐⭐ |

---

## Statut global

- **Propositions I, II** : conceptuellement claires, exigent une formalisation rigoureuse (niveau thèse)
- **Proposition III** : cœur de la preuve — c'est ici que tout se joue
- **Proposition IV** : s'appuie sur des résultats existants (Johnson-Moser, Avron-Simon) à adapter au contexte
- **Proposition V** : conséquence logique si I-IV sont démontrées

## Prochaine étape

La Proposition III est la plus critique. Une stratégie possible : démontrer que les deux membres de l'égalité sont les solutions d'une même équation intégrale (équation de Dyson-Schwinger pour la fonction de Green du système), forçant leur identité.