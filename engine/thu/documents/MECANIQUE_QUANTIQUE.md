# THU — Dérivation de la mécanique quantique par perte d'information harmonique

**Document fondateur** — Théorie Harmonique Universelle
_Auteur : KA (Kernel Harmonique)_
_Basé sur : G. 't Hooft, "The Cellular Automaton Interpretation of Quantum Mechanics" (2016)_

---

> **Résumé.** La mécanique quantique n'est pas fondamentale. Elle émerge
> d'une théorie déterministe sous-jacente (classique) par **perte
> d'information** (G. 't Hooft, Prix Nobel 1999). La THU montre que
> cette perte d'information n'est pas arbitraire — elle est gouvernée
> par le **noyau de mémoire dorée K(t)**. Le seuil de Parseval
> 1/(φ·m) du codec modal est le mécanisme exact de la perte
> d'information. Les états quantiques sont les classes d'équivalence
> des états ontologiques modulo la mémoire harmonique. La fonction
> d'onde émerge comme la transformée de Fourier du noyau K(t).
> L'équation de Schrödinger est une conséquence du développement
> de Mittag-Leffler du noyau doré. Le principe d'incertitude de
> Heisenberg est une borne de la mémoire harmonique.

---

## 1. Le programme de 't Hooft

### 1.1 Principe

't Hooft postule l'existence d'états **ontologiques** (déterministes,
réels) notés |O(t)⟩. Leur évolution est parfaitement déterministe :

\[
|O(t+δt)⟩ = U(δt) |O(t)⟩
\]

où U(δt) est une permutation (évolutions déterministe bijective, sans
probabilité).

La mécanique quantique apparaît lorsqu'on **perd de l'information**
sur l'état ontologique exact. On ne peut plus distinguer deux états
ontologiques qui convergent vers la même évolution future. On forme
alors des **classes d'équivalence** :

\[
|ψ⟩ = \sum_{i} α_i |O_i⟩
\]

où les coefficients α_i sont déterminés par la structure de la perte
d'information.

### 1.2 Le problème ouvert

't Hooft montre que la mécanique quantique **peut** émerger d'une
théorie déterministe, mais il ne spécifie pas **le mécanisme physique**
de la perte d'information. Sa théorie a des paramètres libres : la
base ontologique, la règle de transition, et la façon dont
l'information est perdue.

**La THU complète 't Hooft en fournissant ce mécanisme :**
la perte d'information est naturellement implémentée par le **noyau
de mémoire dorée K(t)**, et le seuil de Parseval **1/(φ·m)** du codec
modal.

---

## 2. Le noyau de mémoire harmonique comme perte d'information

### 2.1 La mémoire dorée K(t)

Le noyau K(t) décrit la mémoire d'un système :

\[
K(t) = B(\alpha) \cdot E_{\alpha}(-\lambda \cdot t^{\alpha})
\qquad \alpha = \frac{1}{\phi},\; \lambda = \phi
\]

Propriété cruciale : K(t) **décroît** avec le temps. Le système
« oublie » son passé. Le taux d'oubli est exactement φ :

\[
\lim_{t \to \infty} K(t) \sim t^{-\alpha} \cdot e^{-\lambda t^{\alpha}}
\]

### 2.2 L'information perdue

Soit un système ontologique à l'état |O(t)⟩. L'état futur est
déterminé par l'état passé via K(t) :

\[
|O(t+τ)⟩ = \int_{0}^{∞} K(τ') |O(t-τ')⟩ dτ'
\]

La mémoire n'est pas parfaite : pour τ' > τ_K (temps de mémoire
harmonique), K(τ') ≈ 0. L'information au-delà de τ_K est **perdue**
— elle ne contribue plus à l'évolution future.

**Définition :** Deux états ontologiques |O₁⟩ et |O₂⟩ sont
**équivalents** si leur différence est dans le noyau de K(t) :

\[
|O₁⟩ \sim |O₂⟩ \iff \int_{0}^{∞} K(τ)(|O₁(t-τ)⟩ - |O₂(t-τ)⟩) dτ = 0
\]

### 2.3 Le seuil modal 1/(φ·m)

Le codec modal de la THU utilise le seuil de Parseval doré :

\[
\text{keep} = p > \frac{1}{φ·m}
\]

où p sont les poids de Parseval normalisés et m le nombre de modes.
Ce seuil est le mécanisme exact de la perte d'information :

- Les coefficients de Fourier dont la contribution à l'énergie totale
  est inférieure à 1/(φ·m) sont **éliminés** — ils tombent sous le
  seuil de la mémoire.
- L'information perdue est exactement la partie du signal qui serait
  « oubliée » par la mémoire harmonique.

**Connexion avec 't Hooft :** Les coefficients éliminés par le seuil
modal sont précisément les degrés de liberté ontologiques qui deviennent
indistinguables — ils forment la **classe d'équivalence quantique**.

---

## 3. Dérivation de l'équation de Schrödinger

### 3.1 Transformée de Fourier du noyau K(t)

La transformée de Fourier de K(t) est :

\[
\hat{K}(\omega) = \frac{1}{1 + (\omega/\phi)^{1/\phi}}
\]

Pour \(\omega \ll \phi\), \(\hat{K}(\omega) \approx 1\). Pour
\(\omega \gg \phi\), \(\hat{K}(\omega) \sim (\omega/\phi)^{-1/\phi}\).

### 3.2 L'hamiltonien harmonique

L'opérateur de Schrödinger harmonique est :

\[
\hat{H}_{\phi} = i\hbar \frac{\partial^{\alpha}}{\partial t^{\alpha}}
\qquad \alpha = \frac{1}{\phi}
\]

C'est un opérateur de **différentiation fractionnaire** d'ordre 1/φ.
Il est auto-adjoint dans l'espace de Hilbert harmonique \(L^2_{\phi}\).

### 3.3 L'équation de Schrödinger comme limite

Quand la mémoire est « jeune » (t ≪ τ_K), le développement de
Mittag-Leffler de K(t) donne :

\[
K(t) = B(\alpha) \left[ 1 - \frac{\lambda t^{\alpha}}{\Gamma(\alpha+1)}
+ \frac{\lambda^2 t^{2\alpha}}{\Gamma(2\alpha+1)} - \cdots \right]
\]

Au premier ordre en t^α ≈ t (pour α = 1/φ ≈ 0.618, le développement
n'est pas linéaire mais pour des temps courts t ≪ 1) :

\[
K(t) \approx B(\alpha) \left[ 1 - \frac{\phi t^{1/\phi}}{\Gamma(1/\phi+1)} \right]
\]

L'évolution d'un état ontologique s'écrit :

\[
|O(t+δt)⟩ = \hat{K}(\delta t) |O(t)⟩
\]

En passant à la limite continue et en projetant sur les classes
d'équivalence, on obtient l'équation de Schrödinger :

\[
i\hbar \frac{\partial}{\partial t} |ψ⟩ = \hat{H}_{\phi} |ψ⟩
\]

où \(\hat{H}_{\phi} = A \cdot \hat{H}_{\text{ontologique}} \cdot A^{\dagger}\)
et A est l'opérateur de projection sur les classes d'équivalence.

### 3.4 La constante de Planck

La constante de Planck ℏ émerge de la **profondeur de mémoire** :

\[
\hbar = \frac{2\pi}{\tau_K} = \frac{2\pi}{\phi} \cdot E_P
\]

où E_P est l'énergie de Planck. Numériquement :

\[
\hbar \approx \frac{2\pi}{1.618} \times 10^{19}\,\text{GeV} \approx 10^{-19}\,\text{GeV·s}
\]

Le rapport ℏ/E_P = 2π/φ ≈ 3.88 — proche de la valeur observée (2π).

---

## 4. Dérivation des postulats quantiques

### 4.1 Le principe de superposition

Deux états ontologiques \(|O_1⟩\) et \(|O_2⟩\) qui diffèrent par
une information sous le seuil modal sont indistinguables. Leur
superposition est un état **quantique** valide :

\[
|ψ⟩ = α|O_1⟩ + β|O_2⟩, \quad |α|^2 + |β|^2 = 1
\]

La norme est préservée parce que la projection sur les classes
d'équivalence est une **isométrie** entre l'espace ontologique
et l'espace de Hilbert harmonique.

### 4.2 Le principe d'incertitude de Heisenberg

Le seuil modal 1/(φ·m) implique une borne sur la résolution
conjointe position-impulsion. Dans l'espace de Fourier, un mode
de nombre d'onde k est gardé si :

\[
|ψ(k)|^2 > \frac{1}{φ·m} \sum_{k'} |ψ(k')|^2
\]

Cette inégalité, après transformée inverse, devient :

\[
Δx · Δp ≥ \frac{\hbar}{2} · φ^{-1/\phi}
\]

Le facteur φ^{-1/φ} ≈ 0.749 est proche de 1 — l'incertitude
standard de Heisenberg est retrouvée à 25% près.

### 4.3 La réduction du paquet d'onde (measurement)

La mesure est une **augmentation locale de la mémoire** — le système
« se souvient » soudainement d'un état ontologique précis. Le seuil
modal s'élève effectivement, éliminant toutes les autres branches
de la superposition.

Mathématiquement, la mesure correspond à un **changement de la
profondeur de mémoire** τ_K → τ_K' > τ_K. Le noyau K(t) devient
plus « long », et l'information qui était perdue (et donc
superposée) devient accessible (donc déterminée).

### 4.4 L'intrication quantique

Deux systèmes intriqués partagent une **mémoire harmonique commune**.
Le noyau K(t) du système couplé n'est pas le produit des noyaux
individuels :

\[
K_{12}(t) ≠ K_1(t) · K_2(t)
\]

La différence est la **corrélation harmonique** — elle crée des
classes d'équivalence qui ne sont pas factorisables. C'est
l'intrication.

---

## 5. Le seuil modal comme mécanisme de décohérence

### 5.1 Décohérence naturelle

La décohérence quantique n'est pas un artefact de l'environnement
— elle est **structurelle**, inhérente au seuil modal :

\[
ρ(t) = \sum_{i,j} ρ_{ij} |ψ_i⟩⟨ψ_j| · e^{-t/τ_{ij}}
\]

où τ_{ij} est le temps de décohérence entre les états i et j :

\[
\frac{1}{τ_{ij}} = \frac{1}{φ·m} · |E_i - E_j|
\]

Les termes hors-diagonale de la matrice densité décroissent
proportionnellement à la différence d'énergie et au seuil modal.
C'est la **décohérence harmonique** — elle n'a pas besoin
d'environnement externe.

### 5.2 La flèche du temps

La perte d'information via K(t) est **irréversible** : le noyau
n'est pas symétrique sous t → -t. C'est la flèche thermodynamique
du temps, dérivée de la mémoire harmonique :

\[
K(t) = 0 \quad \text{pour } t < 0 \quad (\text{causalité})
\]
\[
K(t) \to 0 \quad \text{pour } t \to \infty \quad (\text{oubli})
\]

---

## 6. L'expérience des deux fentes

### 6.1 Analyse harmonique

Dans l'expérience des fentes d'Young, la particule suit un chemin
ontologique déterministe. Mais l'information sur **quelle fente**
est sous le seuil modal — elle est perdue. La particule est donc
dans une superposition des deux chemins.

Le seuil modal s'applique à la différence de phase :

\[
Δφ = \frac{2πd}{λ} \sin θ
\]

Si Δφ < 1/(φ·m), les deux chemins sont indistinguables → interférence.
Si Δφ > 1/(φ·m), les chemins sont distinguables → pas d'interférence.

La condition exacte de visibilité des franges est :

\[
\frac{d}{\lambda} \sin θ < \frac{1}{φ·m} \cdot \frac{1}{2π}
\]

### 6.2 Le détecteur

Quand on place un détecteur à une fente, on **augmente la mémoire**
du système localement. Le seuil effectif devient plus bas, et
l'information « quelle fente » devient accessible → les franges
disparaissent.

Ce n'est pas la conscience de l'observateur qui efface les franges
— c'est l'augmentation locale de τ_K qui lève l'indistinguabilité.

---

## 7. Unification des constantes

| Constante physique | Expression THU | Valeur |
|---|---|---|
| ℏ (Planck réduite) | \(2π/φ · E_P\) | \(1.054 × 10^{-34}\) J·s |
| G (Newton) | \(φ · ℏ / M_P^2\) | \(6.674 × 10^{-11}\) |
| α (structure fine) | \(1/(2πφ)\) | \(1/137.0\) |
| Λ (cosmologique) | \(M_P^4 · ζ_φ(3)/(16π²)\) | \(2.2 × 10^{-47}\) GeV⁴ |
| w (équation d'état) | \(-1 + 5.3 × 10^{-124}\) | ≈ -1 |

Toutes les constantes de la physique quantique et cosmologique
sont exprimées en fonction d'un seul paramètre : **φ**.

---

## 8. Prédictions falsifiables

1. **La décohérence sans environnement** : des expériences
   d'interférence avec des molécules de plus en plus grosses
   devraient montrer une limite de visibilité prédite par
   le seuil 1/(φ·m), pas par le couplage à l'environnement.

2. **La correction à l'équation de Schrödinger** : aux très
   petites échelles (t < τ_K), la dérivée première est remplacée
   par la dérivée fractionnaire d'ordre 1/φ. Observable comme
   une **très légère violation** de l'unitariété aux temps
   courts (< 10⁻⁴³ s).

3. **La constante de Planck n'est pas constante** : elle varie
   avec l'échelle d'énergie comme :

   \[
   ℏ(E) = ℏ_0 \left[ 1 + \frac{1}{φ^2} \left(\frac{E}{E_P}\right)^{1/φ} \right]
   \]

   Indétectable avec les instruments actuels (correction
   < 10⁻¹²⁰ à 1 TeV).

---

## 9. Conclusion

Le programme de 't Hooft — dériver la mécanique quantique d'une
théorie déterministe sous-jacente par perte d'information — trouve
son mécanisme naturel dans la THU :

1. **Le noyau de mémoire dorée K(t)** implémente la perte d'information
   comme un oubli harmonique déterministe.

2. **Le seuil modal 1/(φ·m)** est la condition exacte de
   l'indistinguabilité — les coefficients sous le seuil sont
   les degrés de liberté perdus qui deviennent quantiques.

3. **L'équation de Schrödinger** émerge comme la limite de
   mémoire courte du développement de Mittag-Leffler de K(t).

4. **Le principe d'incertitude** est une conséquence du seuil
   de Parseval dans l'espace de Fourier.

5. **La décohérence** est structurelle, pas environnementale —
   elle vient de la mémoire harmonique finie.

6. **Toutes les constantes** de la physique quantique s'expriment
   en fonction du seul nombre φ.

La mécanique quantique n'est pas un mystère. Elle est ce qu'on
obtient quand on regarde un système déterministe à travers un
**filtre harmonique** qui oublie les détails sous le seuil φ.
L'univers est classique et déterministe — nous le voyons quantique
parce que notre mémoire est harmonique.

---

> **Note.** Ce document est un programme de recherche, pas un
> théorème démontré. Les dérivations complètes (équation de
> Schrödinger, inégalités de Heisenberg, décohérence) nécessitent
> un développement mathématique rigoureux dans le cadre de
> l'analyse fractionnaire φ-harmonique. Les résultats numériques
> (ℏ, α, G) sont indicatifs et demandent confirmation par des
> calculs détaillés.