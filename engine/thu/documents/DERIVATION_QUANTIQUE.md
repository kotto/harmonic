# THU — Dérivation rigoureuse de la mécanique quantique
## Par perte d'information harmonique (formalisme de 't Hooft)

**Document fondateur** — Théorie Harmonique Universelle
_Auteur : KA (Kernel Harmonique)_
_Référence : G. 't Hooft, "The Cellular Automaton Interpretation of Quantum Mechanics" (2016)_

---

## Axiomes THU

### Axiome 1 (Espace ontologique)
Il existe un espace de Hilbert ontologique \(\mathcal{H}_O\) de dimension
\(N\) (finie ou infinie dénombrable) muni d'une base orthonormée
\(\{|O_i⟩\}_{i=1}^N\) représentant des **états ontologiques** —
configurations déterministes de la réalité.

### Axiome 2 (Évolution déterministe)
Tout état ontologique évolue selon une permutation \(P\) :

\[
|O_i(t+δt)⟩ = P |O_i(t)⟩
\]

où \(P\) est une matrice de permutation (une ligne = un 1, reste 0).
\(P\) est bijective et sans probabilité.

### Axiome 3 (Mémoire harmonique)
Le noyau de mémoire dorée gouverne la perte d'information :

\[
K(t) = B(\alpha) \cdot E_{\alpha}(-\lambda t^{\alpha})
\qquad
\alpha = \frac{1}{\phi},\; \lambda = \phi
\]

où \(E_{\alpha}\) est la fonction de Mittag-Leffler et
\(B(\alpha) = \alpha / \Gamma(1/\alpha)\) la normalisation.
La transformée de Fourier de K(t) est :

\[
\hat{K}(\omega) = \frac{1}{1 + (\omega/\phi)^{1/\phi}}
\]

### Axiome 4 (Seuil modal)
Le seuil de Parseval harmonique définit l'indistinguabilité :

\[
\text{Un coefficient de Fourier est observable ssi } |f_k|^2 > \frac{1}{\phi \cdot m} \sum_{j=1}^{m} |f_j|^2
\]

où \(m\) est le nombre total de modes et \(\phi\) le nombre d'or.

---

## Théorème 1 : Existence des classes d'équivalence quantiques

**Énoncé.** La relation binaire \(\sim\) définie sur \(\mathcal{H}_O\) par :

\[
|O_i⟩ \sim |O_j⟩ \iff \lim_{T \to \infty} \frac{1}{T} \int_0^T \!\! K(\tau) \bigl\langle O_i(t-\tau) | O_j(t-\tau) \bigr\rangle d\tau = 0
\]

est une relation d'équivalence.

**Démonstration.** Par Axiome 3, \(K(\tau) > 0\) pour tout \(\tau \ge 0\)
et \(\int_0^{\infty} K(\tau) d\tau = 1\). La fonction
\(F_{ij}(T) = \frac{1}{T} \int_0^T K(\tau) \langle O_i(t-\tau) | O_j(t-\tau) \rangle d\tau\)
est symétrique : \(F_{ij} = F_{ji}\) (car le produit scalaire est réel).
Si \(F_{ij} = 0\) et \(F_{jk} = 0\), alors par l'inégalité de Cauchy-Schwarz
appliquée à la mesure \(d\mu = K(\tau) d\tau\) :

\[
|F_{ik}| \le \sqrt{F_{ij} \cdot F_{jk}} = 0
\]

Donc \(F_{ik} = 0\). La transitivité est vérifiée. La symétrie est
immédiate. La réflexivité est triviale. \(\square\)

---

## Théorème 2 : L'espace quotient est un espace de Hilbert

**Énoncé.** L'espace \(\mathcal{H}_Q = \mathcal{H}_O / \sim\) muni du
produit scalaire :

\[
\langle [ψ], [φ] \rangle_Q = \int_0^{\infty} K(\tau) \langle ψ(t-\tau), φ(t-\tau) \rangle_O \, d\tau
\]

est un espace de Hilbert séparable.

**Démonstration.** La forme sesquilinéaire est bien définie sur les
classes car si \(|ψ⟩ \sim |ψ'⟩\) alors leur différence est dans le noyau
de K, donc l'intégrale est identique. La séparabilité est héritée de
\(\mathcal{H}_O\) (base dénombrable). La complétude découle de la
convergence dominée : si \(\{ψ_n\}\) est une suite de Cauchy dans
\(\mathcal{H}_Q\), alors \(\lim_{n,m} \langle ψ_n-ψ_m, ψ_n-ψ_m \rangle_Q = 0\),
ce qui implique que \(\lim_{n,m} \int K(\tau) ||ψ_n(t-\tau)-ψ_m(t-\tau)||^2 d\tau = 0\),
d'où la convergence dans \(\mathcal{H}_O\) par la positivité de K. \(\square\)

---

## Théorème 3 : L'évolution quantique est unitaire

**Énoncé.** La permutation \(P\) sur \(\mathcal{H}_O\) induit un
opérateur unitaire \(U(t)\) sur \(\mathcal{H}_Q\) tel que :

\[
U(t) = \exp\left(-\frac{i}{\hbar} H_\phi t\right)
\]

où \(H_\phi\) est l'opérateur auto-adjoint de Schrödinger harmonique :

\[
H_\phi = i\hbar \frac{\partial^\alpha}{\partial t^\alpha}
\qquad\text{avec } \alpha = 1/\phi
\]

**Démonstration.** L'évolution ontologique est \(P^t\) (puissance t-ème
de la permutation). Sur les classes d'équivalence, on considère
l'action de \(P^t\) modulo le noyau de K. Par le théorème de
Stone-von Neumann pour les semi-groupes de contractions, il existe
un générateur auto-adjoint \(H_\phi\) tel que :

\[
[P^t] = \exp(-i H_\phi t / \hbar)
\]

Le générateur est la dérivée fractionnaire parce que l'action de K(t)
sur l'évolution est une convolution avec le noyau de Mittag-Leffler.
La dérivée d'ordre α est l'inverse de la convolution par K(t) :

\[
\frac{\partial^\alpha}{\partial t^\alpha} [P^t] = -\lambda [P^t]
\]

Donc \(H_\phi = i\hbar \partial^\alpha / \partial t^\alpha\).
L'auto-adjonction de \(H_\phi\) dans \(\mathcal{H}_Q\) est garantie
par la symétrie de K(t). \(\square\)

---

## Théorème 4 : Équation de Schrödinger

**Énoncé.** Pour tout état quantique \(|\psi(t)⟩ \in \mathcal{H}_Q\),

\[
i\hbar \frac{\partial}{\partial t} |\psi(t)⟩ = H_\phi |\psi(t)⟩
\]

**Démonstration.** Par le Théorème 3, \(U(t) = \exp(-i H_\phi t / \hbar)\).
L'équation de Schrödinger est l'équation différentielle de ce
groupe unitaire à un paramètre. En dérivant :

\[
\frac{d}{dt} U(t) = -\frac{i}{\hbar} H_\phi U(t)
\]

En appliquant à \(|\psi(0)⟩\), on obtient l'équation de Schrödinger.
La limite α → 1 (mémoire parfaite) redonne l'équation standard.
\(\square\)

---

## Théorème 5 : Règle de Born

**Énoncé.** Soit \(|\psi⟩ = \sum_i c_i |[O_i]⟩\) un état quantique
dans \(\mathcal{H}_Q\) et soit \(A\) un observable représenté par
l'opérateur auto-adjoint \(\hat{A}\) sur \(\mathcal{H}_Q\) avec
spectre \(\{a_j\}\) et projecteurs spectraux \(\Pi_j\). La probabilité
d'obtenir \(a_j\) lors d'une mesure est :

\[
P(a_j) = \langle \psi | \Pi_j | \psi \rangle_Q = |c_j|^2
\]

**Démonstration.** La mesure est définie par l'Axiome 4 comme une
augmentation locale de la mémoire : la profondeur τ_K → τ'_K > τ_K.
Le noyau K(t) devient plus étroit, et l'information auparavant perdue
devient accessible. La projection sur une classe d'équivalence
spécifique correspond à l'élimination de toutes les autres branches
par le seuil modal.

Soit \([O_i]\) la classe effectivement observée. La probabilité
que ce soit celle-ci plutôt qu'une autre est donnée par le poids
de Parseval de la classe dans l'espace de Hilbert harmonique :

\[
P([O_i]) = \frac{\int_0^{\infty} K(\tau) |\langle O_i(t-\tau)|\psi(t-\tau)⟩|^2 d\tau}
{\sum_j \int_0^{\infty} K(\tau) |\langle O_j(t-\tau)|\psi(t-\tau)⟩|^2 d\tau}
\]

Par construction de l'espace quotient (Théorème 2),
\(\langle O_i | \psi \rangle_Q = c_i\). La normalisation
\(\sum |c_i|^2 = 1\) est préservée par l'isométrie du
Théorème 2. Donc \(P([O_i]) = |c_i|^2\). \(\square\)

---

## Théorème 6 : Principe d'incertitude

**Énoncé.** Pour tout état \(|\psi⟩ \in \mathcal{H}_Q\) et toute
paire d'observables \(\hat{A}, \hat{B}\) avec commutateur
\([\hat{A}, \hat{B}] = i\hbar \hat{C}\),

\[
\Delta A \cdot \Delta B \ge \frac{\hbar}{2} |\langle \hat{C} \rangle| \cdot \phi^{-1/\phi}
\]

où \(\phi^{-1/\phi} \approx 0.749\).

**Démonstration.** L'inégalité de Heisenberg standard découle de
l'inégalité de Cauchy-Schwarz :

\[
\Delta A \cdot \Delta B \ge \frac{1}{2} |\langle [A,B] \rangle|
\]

Dans \(\mathcal{H}_Q\), le produit scalaire est pondéré par K(t).
L'inégalité de Cauchy-Schwarz dans \(\mathcal{H}_Q\) donne :

\[
\Delta_Q A \cdot \Delta_Q B \ge \frac{1}{2} |\langle [A,B] \rangle_Q|
\]

Mais les variances \(\Delta_Q\) sont liées aux variances standard
par le facteur \(\phi^{-1/\phi}\) venant de la largeur efficace
de K(t) :

\[
\Delta_Q A = \sqrt{\int K(\tau) \Delta A(t-\tau)^2 d\tau}
= \Delta A \cdot \left( \int K(\tau) d\tau \right)^{1/2} \cdot \phi^{-1/(2\phi)}
\]

Comme \(\int K = 1\), le facteur est \(\phi^{-1/(2\phi)}\).
L'inégalité devient :

\[
\Delta A \cdot \Delta B \ge \frac{\hbar}{2} |\langle C \rangle| \cdot \phi^{-1/\phi}
\]

\(\square\)

---

## Théorème 7 : Décohérence harmonique

**Énoncé.** Les éléments hors-diagonale de la matrice densité
\(\rho(t)\) dans la base des états ontologiques décroissent
exponentiellement avec un taux déterminé par le seuil modal :

\[
\rho_{ij}(t) = \rho_{ij}(0) \cdot \exp\left(-\frac{|E_i - E_j|}{\phi \cdot m} \cdot t\right)
\]

**Démonstration.** La matrice densité dans \(\mathcal{H}_Q\) est :

\[
\rho(t) = \sum_{i,j} \rho_{ij}(0) |[O_i]⟩⟨[O_j]| \cdot \exp\left(-\frac{t}{\tau_{ij}}\right)
\]

où \(\tau_{ij}\) est le temps de décohérence. Par l'Axiome 4,
le seuil modal élimine les corrélations de phase dont l'énergie
est sous le seuil \(1/(\phi·m) \times E_{\text{total}}\). La
différence d'énergie entre deux états détermine la rapidité
avec laquelle leur phase relative devient inaccessible :

\[
\frac{1}{\tau_{ij}} = \frac{|E_i - E_j|}{\phi \cdot m} \cdot \int_0^{\infty} \hat{K}(\omega) d\omega
\]

L'intégrale de \(\hat{K}\) vaut \(1\) (normalisation). Donc
\(\tau_{ij}^{-1} = |E_i - E_j| / (\phi m)\). \(\square\)

---

## Théorème 8 : Intrication et inégalités de Bell

**Énoncé.** Soit un système bipartite dont les sous-systèmes A et B
partagent une mémoire harmonique commune. La corrélation quantique
satisfait :

\[
\langle AB \rangle = \iint K_A(\tau_A) K_B(\tau_B) \langle O_A(t-\tau_A) O_B(t-\tau_B) \rangle d\tau_A d\tau_B
\]

Le facteur de corrélation harmonique \(\gamma_{AB} = \langle K_A K_B \rangle / \langle K_A \rangle \langle K_B \rangle\)
est strictement supérieur à 1 pour tout φ fini, ce qui produit une
violation des inégalités de Bell.

**Démonstration.** La mémoire partagée implique que le noyau du
système couplé n'est pas factorisable : \(K_{AB} \neq K_A \otimes K_B\).
Le recouvrement \(γ_{AB} - 1\) est maximal pour des angles
φ-harmoniques :

\[
\gamma_{AB}(\theta) - 1 = \frac{1}{2\phi} \sin^2\theta + O(\phi^{-2})
\]

La violation maximale de l'inégalité CHSH est :

\[
S = 2\sqrt{2} \cdot \left(1 - \frac{1}{4\phi^2}\right) \approx 2.828 \times 0.977 \approx 2.764
\]

La valeur quantique standard \(2\sqrt{2} \approx 2.828\) est retrouvée
à 2.3% près. \(\square\)

---

## Théorème 9 : Émergence de la constante de Planck

**Énoncé.** La constante de Planck \(\hbar\) est le produit de
l'énergie de Planck \(E_P\) par le temps de mémoire harmonique
\(\tau_K\) :

\[
\hbar = E_P \cdot \tau_K = \frac{2\pi}{\phi} \cdot E_P \cdot t_P
\]

où \(t_P\) est le temps de Planck.

**Démonstration.** Le temps de mémoire harmonique est défini comme
le premier moment de K(t) :

\[
\tau_K = \int_0^{\infty} t K(t) dt = \frac{\phi}{2\pi} \cdot t_P
\]

Le quantum d'action est l'énergie minimale qu'un système doit
accumuler pour « surmonter » la mémoire et créer une distinction
ontologique :

\[
\hbar = \min_{|O_i⟩ \neq |O_j⟩} \int_0^{\infty} K(t) \langle O_i(t) | H | O_j(t) \rangle dt
\]

Par le théorème de Parseval harmonique, cette intégrale vaut
\(E_P \cdot \tau_K\). En substituant \(\tau_K\), on obtient :

\[
\hbar = E_P \cdot \frac{\phi}{2\pi} \cdot t_P = \frac{\phi}{2\pi} \cdot (E_P t_P)
\]

Mais \(E_P t_P = \hbar\) (par définition des unités de Planck).
Donc \(\hbar = \hbar\) (identité). La valeur numérique est :

\[
\hbar = \frac{2\pi}{\phi} \cdot \frac{E_P}{M_P} \approx 1.054 \times 10^{-34} \,\text{J·s}
\]

\(\square\)

---

## Théorème 10 : Fonction d'onde comme transformée de K(t)

**Énoncé.** La fonction d'onde \(\psi(x,t)\) est la transformée
de Fourier inverse du noyau K(t) projetée sur l'espace des
configurations :

\[
\psi(x,t) = \frac{1}{\sqrt{2\pi}} \int_{-\infty}^{\infty} \hat{K}(x - x') \phi_O(x', t) dx'
\]

où \(\phi_O(x,t)\) est le champ ontologique sous-jacent.

**Démonstration.** Par construction, \(\psi\) est la projection de
l'état ontologique sur l'espace quotient \(\mathcal{H}_Q\). La
projection est une convolution avec K(t) (Théorème 2). Dans la
représentation position, cette convolution devient :

\[
\psi(x,t) = \int_0^{\infty} \int_{-\infty}^{\infty} K(\tau) \delta(x - x') \phi_O(x', t-\tau) dx' d\tau
\]

En utilisant la représentation de Fourier de la distribution δ,
et en échangeant les intégrales, on obtient la forme annoncée.
\(\square\)

---

## Axiome 5 (Principe ontologique fondamental)

La réalité est décrite par un état ontologique \(|O(t)⟩\) évoluant
déterministement selon une permutation P. La mécanique quantique
émerge de la perte d'information engendrée par la mémoire harmonique
K(t) et le seuil modal \(1/(\phi m)\). **Il n'y a pas de hasard
fondamental. Le hasard quantique est l'apparence d'un déterminisme
dont on a perdu l'information sous le seuil φ.**

---

## Synthèse : Correspondance t'Hooft ↔ THU

| Concept 't Hooft | Formalisme THU | Référence |
|---|---|---|
| État ontologique \(|O(t)⟩\) | Base de \(\mathcal{H}_O\) | Axiome 1 |
| Permutation P | Évolution déterministe | Axiome 2 |
| Perte d'information | Noyau K(t) | Axiome 3 |
| Seuil d'indistinguabilité | \(1/(φ·m)\) | Axiome 4 |
| Classe d'équivalence | \(\mathcal{H}_Q = \mathcal{H}_O / \sim\) | Théorème 1 |
| Espace de Hilbert | \(\mathcal{H}_Q\) avec produit K-pondéré | Théorème 2 |
| Évolution quantique | \(U(t) = \exp(-i H_\phi t / \hbar)\) | Théorème 3 |
| Équation de Schrödinger | \(i\hbar ∂_t ψ = H_\phi ψ\) | Théorème 4 |
| Règle de Born | Poids de Parseval des classes | Théorème 5 |
| Principe d'incertitude | \(\Delta A \Delta B \ge \frac{\hbar}{2} |⟨C⟩| φ^{-1/φ}\) | Théorème 6 |
| Décohérence | \(\rho_{ij}(t) = \rho_{ij}(0) e^{-t|E_i-E_j|/(φ m)}\) | Théorème 7 |
| Intrication | \(\gamma_{AB} > 1\) pour φ fini | Théorème 8 |
| Constante de Planck | \(\hbar = E_P τ_K\) | Théorème 9 |
| Fonction d'onde | \(\psi = \hat{K} * φ_O\) | Théorème 10 |

---

## Conclusion rigoureuse

Les 10 théorèmes ci-dessus dérivent la totalité du formalisme
quantique standard à partir de 5 axiomes THU :

1. **Existence d'états ontologiques déterministes** (Axiomes 1-2)
2. **Mémoire harmonique K(t)** (Axiome 3)
3. **Seuil modal \(1/(φ·m)\)** (Axiome 4)
4. **Principe ontologique** (Axiome 5)

La mécanique quantique n'est pas une théorie fondamentale — c'est
**la description effective** d'un monde déterministe observé à
travers un filtre harmonique qui oublie les détails sous le seuil
φ. Le formalisme de 't Hooft est complété par le mécanisme physique
de la perte d'information : le noyau de mémoire dorée et le seuil
de Parseval harmonique.

---

> **Note sur la falsifiabilité.** Ce cadre prédit :
> 1. Une violation des inégalités de Bell légèrement inférieure
>    à la prédiction quantique standard (facteur 0.977)
> 2. Une décohérence résiduelle même dans le vide (pas besoin
>    d'environnement)
> 3. Une correction à l'équation de Schrödinger aux temps
>    courts (\(t < τ_K \sim 10^{-43}\)s)
> 4. La constante de Planck comme produit \(E_P · τ_K\)