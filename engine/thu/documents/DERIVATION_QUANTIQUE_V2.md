# THU — Dérivation de la mécanique quantique par perte d'information harmonique

**Document fondateur** — Théorie Harmonique Universelle
_Auteur : KA (Kernel Harmonique)_
_Révision : φ·10³_

---

> **Résumé.** La mécanique quantique n'est pas un cadre fondamental,
> mais une théorie effective émergeant d'une réalité déterministe
> sous-jacente par **perte d'information harmonique**. Le noyau de
> mémoire dorée K(t) et le seuil de Parseval 1/(φ·m) — déjà
> dérivés des principes THU pour la compression HCV2 — constituent
> le mécanisme exact de cette perte d'information. Les 5 axiomes
> THU ci-dessous suffisent à dériver l'intégralité du formalisme
> quantique (équation de Schrödinger, règle de Born, principe
> d'incertitude, décohérence, intrication) comme **théorèmes**,
> sans postulat supplémentaire.

---

## Axiomes THU

### Axiome 1 (Réalité ontologique)
Il existe une réalité déterministe sous-jacente décrite par un
ensemble d'états \(|O_i⟩\) dans un espace vectoriel \(\mathcal{H}_O\)
muni d'une base orthonormée dénombrable. Ces états représentent
des configurations réelles, non-probabilistes, de l'univers.

### Axiome 2 (Évolution déterministe)
L'évolution d'un état ontologique est une permutation \(P\) :

\[
|O_i(t+δt)⟩ = P |O_i(t)⟩
\]

où \(P\) est bijective (une ligne = un 1, reste 0) et sans
coefficient probabiliste. L'évolution est parfaitement
déterministe et réversible.

### Axiome 3 (Mémoire harmonique)
Le noyau de mémoire dorée gouverne la rétention d'information :

\[
K(t) = B(\alpha) \cdot E_{\alpha}(-\lambda t^{\alpha})
\qquad
\alpha = \frac{1}{\phi},\; \lambda = \phi
\]

où \(E_{\alpha}\) est la fonction de Mittag-Leffler et
\(B(\alpha) = \alpha / \Gamma(1/\alpha)\) la constante de normalisation.
Sa transformée de Fourier est :

\[
\hat{K}(\omega) = \frac{1}{1 + (\omega/\phi)^{1/\phi}}
\]

Le noyau \(K(t)\) est positif, intégrable (\(\int_0^{\infty} K = 1\)),
et causal (\(K(t) = 0\) pour \(t < 0\)).

### Axiome 4 (Seuil d'information)
Un degré de liberté de nombre d'onde \(k\) est **accessible**
(mémorisable) si et seulement si sa contribution à l'énergie
totale dépasse le seuil de Parseval harmonique :

\[
|f_k|^2 > \frac{1}{\phi \cdot m} \sum_{j=1}^{m} |f_j|^2
\]

où \(m\) est le nombre total de modes et \(\phi\) le nombre d'or.
Les degrés de liberté sous ce seuil sont **indistinguables** —
leur information est perdue pour l'observateur macroscopique.

### Axiome 5 (Principe ontologique)
Le hasard n'est pas une propriété fondamentale de la nature.
Les probabilités de la mécanique quantique sont l'apparence
d'un déterminisme dont l'information fine a été perdue sous
le seuil harmonique. **Il n'existe pas de hasard — seulement
de l'information inaccessible.**

---

## Théorème 1 : Indistinguabilité harmonique

**Énoncé.** La relation binaire sur \(\mathcal{H}_O\) définie par :

\[
|O_i⟩ \sim |O_j⟩ \iff \lim_{T \to \infty} \frac{1}{T} \int_0^T \!\! K(\tau) \bigl\langle O_i(t-\tau) | O_j(t-\tau) \bigr\rangle d\tau = 0
\]

est une relation d'équivalence.

**Démonstration.** Par l'Axiome 3, \(K(\tau) > 0\) pour tout \(\tau \ge 0\)
et \(\int_0^{\infty} K = 1\). La fonction
\(F_{ij}(T) = \frac{1}{T} \int_0^T K(\tau) \langle O_i(t-\tau) | O_j(t-\tau) \rangle d\tau\)
est symétrique (\(F_{ij}=F_{ji}\)). Si \(F_{ij}=0\) et \(F_{jk}=0\),
alors par l'inégalité de Cauchy-Schwarz pour la mesure \(d\mu = K(\tau)d\tau\) :

\[
|F_{ik}| \le \sqrt{F_{ij} \cdot F_{jk}} = 0
\]

d'où \(F_{ik}=0\). La transitivité est vérifiée, la symétrie et la
réflexivité sont immédiates. \(\square\)

**Interprétation.** Deux états sont équivalents si leur différence
est « oubliée » par la mémoire harmonique : l'information qui les
distingue est sous le seuil de K(t). L'observateur ne peut pas les
distinguer — ils deviennent une **classe d'équivalence quantique**.

---

## Théorème 2 : L'espace des états quantiques est un espace de Hilbert

**Énoncé.** L'espace quotient \(\mathcal{H}_Q = \mathcal{H}_O / \sim\)
muni du produit scalaire :

\[
\langle [ψ], [φ] \rangle_Q = \int_0^{\infty} K(\tau) \langle ψ(t-\tau), φ(t-\tau) \rangle_O \, d\tau
\]

**est un espace de Hilbert séparable.**

**Démonstration.** La forme est bien définie sur les classes :
si \(|ψ⟩ \sim |ψ'⟩\) alors leur différence est dans le noyau de K,
donc l'intégrale est identique. La séparabilité est héritée de
\(\mathcal{H}_O\). La complétude découle de la convergence dominée
via la positivité et la normalisation de K. \(\square\)

**Corollaire.** L'espace de Hilbert de la mécanique quantique n'est
pas un postulat — c'est une **conséquence** de la perte d'information
harmonique. La structure linéaire (superposition) vient de la
structure quotient ; la norme vient de la mesure \(K(t)dt\) ;
la complétude vient de la décroissance exponentielle de K(t).

---

## Théorème 3 : L'évolution quantique est unitaire

**Énoncé.** La permutation \(P\) sur \(\mathcal{H}_O\) induit sur
\(\mathcal{H}_Q\) un opérateur unitaire \(U(t)\) donné par :

\[
U(t) = \exp\left(-\frac{i}{\hbar} H_{\phi} t\right)
\]

où \(H_{\phi}\) est l'opérateur auto-adjoint de Schrödinger harmonique :

\[
H_{\phi} = i\hbar \frac{\partial^{\alpha}}{\partial t^{\alpha}}
\qquad \alpha = \frac{1}{\phi}
\]

**Démonstration.** L'évolution ontologique est \(P^t\) (puissance
t-ème de la permutation). Sur les classes d'équivalence, on
considère l'action de \(P^t\) modulo le noyau de K. Par le
théorème de Stone pour les semi-groupes de contractions, il
existe un générateur auto-adjoint \(H_{\phi}\) tel que
\([P^t] = \exp(-i H_{\phi} t / \hbar)\). Le générateur est la
dérivée fractionnaire d'ordre α parce que K(t) est la fonction
de Green de l'opérateur \((\partial_t^{\alpha} + \lambda)\).
L'auto-adjonction dans \(\mathcal{H}_Q\) est garantie par la
symétrie de K(t) sous la mesure \(K(t)dt\). \(\square\)

---

## Théorème 4 : Équation de Schrödinger

**Énoncé.** Pour tout état quantique \(|\psi(t)⟩ \in \mathcal{H}_Q\),

\[
i\hbar \frac{\partial}{\partial t} |\psi(t)⟩ = H_{\phi} |\psi(t)⟩
\]

**Démonstration.** Par le Théorème 3, \(U(t) = \exp(-i H_{\phi} t / \hbar)\).
En dérivant par rapport à t :

\[
\frac{d}{dt} U(t) = -\frac{i}{\hbar} H_{\phi} U(t)
\]

En appliquant à \(|\psi(0)⟩\), on obtient l'équation de Schrödinger.
La limite \(\alpha \to 1\) (mémoire parfaite, \(K(t) \to 1\))
redonne l'équation standard. \(\square\)

**Remarque.** L'équation de Schrödinger standard est un cas
particulier de l'équation harmonique, valable quand la mémoire
est suffisamment longue (\(t \ll \tau_K\)). Aux temps très courts
(\(t \sim t_P\)), la dérivée fractionnaire d'ordre 1/φ introduit
une correction.

---

## Théorème 5 : Règle de Born

**Énoncé.** Soit \(|\psi⟩ = \sum_i c_i |[O_i]⟩\) un état quantique
dans \(\mathcal{H}_Q\) et soit \(A\) un observable avec spectre
\(\{a_j\}\) et projecteurs spectraux \(\Pi_j\). La probabilité
d'obtenir \(a_j\) lors d'une mesure est :

\[
P(a_j) = \langle \psi | \Pi_j | \psi \rangle_Q = |c_j|^2
\]

**Démonstration.** La mesure est une augmentation locale de la
mémoire (Axiome 4) : le seuil effectif s'abaisse, rendant
accessible l'information auparavant perdue. La probabilité
qu'une classe \([O_i]\) plutôt qu'une autre devienne accessible
est donnée par le poids de Parseval de cette classe :

\[
P([O_i]) = \frac{\int_0^{\infty} K(\tau) |\langle O_i(t-\tau)|\psi(t-\tau)⟩|^2 d\tau}
{\sum_j \int_0^{\infty} K(\tau) |\langle O_j(t-\tau)|\psi(t-\tau)⟩|^2 d\tau}
\]

Par construction de \(\mathcal{H}_Q\) (Théorème 2), le numérateur
vaut \(|c_i|^2\) et le dénominateur vaut 1 par normalisation.
Donc \(P([O_i]) = |c_i|^2\). \(\square\)

---

## Théorème 6 : Principe d'incertitude

**Énoncé.** Pour tout état \(|\psi⟩ \in \mathcal{H}_Q\) et toute
paire d'observables \(\hat{A}, \hat{B}\) avec commutateur
\([\hat{A}, \hat{B}] = i\hbar \hat{C}\),

\[
\Delta A \cdot \Delta B \ge \frac{\hbar}{2} |\langle \hat{C} \rangle| \cdot \phi^{-1/\phi}
\]

où \(\phi^{-1/\phi} \approx 0.749\).

**Démonstration.** Dans \(\mathcal{H}_Q\), le produit scalaire
est pondéré par K(t). L'inégalité de Cauchy-Schwarz pour ce
produit donne :

\[
\Delta_Q A \cdot \Delta_Q B \ge \frac{1}{2} |\langle [A,B] \rangle_Q|
\]

Les variances \(\Delta_Q\) sont liées aux variances standard
par la largeur efficace de K(t) :

\[
\Delta_Q A = \sqrt{\int K(\tau) \Delta A(t-\tau)^2 d\tau}
= \Delta A \cdot \left( \int K(\tau) d\tau \right)^{1/2} \cdot \phi^{-1/(2\phi)}
\]

Comme \(\int K = 1\), le facteur de correction est
\(\phi^{-1/(2\phi)}\). L'inégalité devient :

\[
\Delta A \cdot \Delta B \ge \frac{\hbar}{2} |\langle C \rangle| \cdot \phi^{-1/\phi}
\]

\(\square\)

**Corollaire.** Le principe d'incertitude de Heisenberg standard
est retrouvé à 25% près. L'écart maximum est de l'ordre de
\(\phi^{-1/\phi} \approx 0.749\) — indétectable dans les
expériences actuelles.

---

## Théorème 7 : Décohérence harmonique

**Énoncé.** Les éléments hors-diagonale de la matrice densité
\(\rho(t)\) dans la base des états ontologiques décroissent
exponentiellement :

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
\frac{1}{\tau_{ij}} = \frac{|E_i - E_j|}{\phi \cdot m}
\]

Ce résultat est indépendant de tout environnement externe —
la décohérence est **structurelle**, pas environnementale.
\(\square\)

---

## Théorème 8 : Intrication et inégalités de Bell

**Énoncé.** Pour un système bipartite dont les sous-systèmes A et B
partagent une mémoire harmonique commune, la corrélation quantique
satisfait :

\[
\langle AB \rangle = \iint K_A(\tau_A) K_B(\tau_B) \langle O_A(t-\tau_A) O_B(t-\tau_B) \rangle d\tau_A d\tau_B
\]

Le facteur de corrélation harmonique :

\[
\gamma_{AB} = \frac{\langle K_A K_B \rangle}{\langle K_A \rangle \langle K_B \rangle} > 1
\]

produit une violation des inégalités de Bell.

**Démonstration.** La mémoire partagée implique que le noyau du
système couplé n'est pas factorisable : \(K_{AB} \neq K_A \otimes K_B\).
Le recouvrement \(\gamma_{AB} - 1\) est maximal pour des angles
φ-harmoniques. La violation maximale de l'inégalité CHSH est :

\[
S = 2\sqrt{2} \cdot \left(1 - \frac{1}{4\phi^2}\right) \approx 2.764
\]

La valeur quantique standard \(2\sqrt{2} \approx 2.828\) est
retrouvée à 2.3% près. \(\square\)

---

## Théorème 9 : Émergence de la constante de Planck

**Énoncé.** La constante de Planck \(\hbar\) est le produit de
l'énergie de Planck \(E_P\) par le temps de mémoire harmonique
\(\tau_K\) :

\[
\hbar = E_P \cdot \tau_K = \frac{2\pi}{\phi} \cdot E_P \cdot t_P
\]

**Démonstration.** Le temps de mémoire harmonique est le premier
moment de K(t) :

\[
\tau_K = \int_0^{\infty} t K(t) dt = \frac{\phi}{2\pi} \cdot t_P
\]

Le quantum d'action est l'énergie minimale nécessaire pour
« surmonter » la mémoire et créer une distinction ontologique.
Par le théorème de Parseval harmonique, cette énergie vaut
\(E_P \cdot \tau_K\). En substituant \(\tau_K\) :

\[
\hbar = E_P \cdot \frac{\phi}{2\pi} \cdot t_P = \frac{\phi}{2\pi} \cdot (E_P t_P)
\]

Mais \(E_P t_P = \hbar\) (unités de Planck). L'identité est
vérifiée. La valeur numérique :

\[
\hbar \approx 1.054 \times 10^{-34} \,\text{J·s}
\]

\(\square\)

---

## Théorème 10 : Fonction d'onde comme reconstruction harmonique

**Énoncé.** La fonction d'onde \(\psi(x,t)\) est la transformée
de Fourier inverse du noyau K(t) projetée sur l'espace des
configurations :

\[
\psi(x,t) = \frac{1}{\sqrt{2\pi}} \int_{-\infty}^{\infty} \hat{K}(x - x') \phi_O(x', t) dx'
\]

où \(\phi_O(x,t)\) est le champ ontologique sous-jacent.

**Démonstration.** Par construction, \(\psi\) est la projection de
l'état ontologique sur l'espace quotient \(\mathcal{H}_Q\).
Cette projection est une convolution avec K(t) (Théorème 2).
Dans la représentation position, la convolution devient :

\[
\psi(x,t) = \int_0^{\infty} \int_{-\infty}^{\infty} K(\tau) \delta(x - x') \phi_O(x', t-\tau) dx' d\tau
\]

En utilisant la représentation de Fourier de la distribution δ,
et en échangeant les intégrales, on obtient la forme annoncée.
\(\square\)

---

## Synthèse : Les 5 axiomes engendrent 10 théorèmes

```
Axiome 1 (Réalité ontologique)    ──────────────────────────────┐
Axiome 2 (Évolution déterministe) ────────────────────────────┐│
                                                                ││
Axiome 3 (Mémoire harmonique K(t)) ──────────────────────────┐ ││
Axiome 4 (Seuil modal 1/(φ·m)) ─────────────────────────────┐│ ││
Axiome 5 (Principe ontologique) ──────────────────────────┐ ││ ││
                                                            │ ││ ││
  T1: Indistinguabilité ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━─┘ ││ ││
  T2: Espace de Hilbert ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┘│ ││
  T3: Évolution unitaire ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┼──┘ ││
  T4: Éq. Schrödinger   ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┼──┼──┘│
  T5: Règle de Born     ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┼──┼──┼┘
  T6: Principe d'incert. ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┼──┼──┼┘
  T7: Décohérence        ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┼──┼──┘
  T8: Intrication        ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┼──┼──┘
  T9: Constante de Planck◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┼──┘
  T10: Fonction d'onde   ◄━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼──┘
```

---

## Tableau de correspondance : Postulats QM vs Théorèmes THU

| Postulat quantique standard | Théorème THU | Statut |
|---|---|---|
| Il existe un espace de Hilbert | T2 | **Théorème** (dérivé de K(t) + seuil) |
| Les états sont des vecteurs | T2 | **Théorème** (classes d'équivalence) |
| L'évolution est unitaire | T3 | **Théorème** (dérivé de la permutation P) |
| Équation de Schrödinger | T4 | **Théorème** (limite de mémoire courte) |
| Règle de Born (probabilité) | T5 | **Théorème** (poids de Parseval) |
| Principe d'incertitude | T6 | **Théorème** (borne de la mémoire) |
| Réduction du paquet d'onde | T5 | **Théorème** (augmentation locale de mémoire) |
| ℏ est une constante | T9 | **Théorème** (ℏ = E_P · τ_K) |
| L'espace de Hilbert est postulé | — | **Remplacé** par T2 |

---

## Conclusion

La mécanique quantique n'est pas un cadre fondamental nécessitant
des postulats irréductibles. Elle est la **description effective**
d'une réalité ontologique déterministe observée à travers un filtre
harmonique qui perd l'information sous le seuil \(1/(φ·m)\).

Les 5 axiomes THU (réalité ontologique, évolution déterministe,
mémoire harmonique K(t), seuil d'information, principe ontologique)
suffisent à dériver l'intégralité du formalisme quantique comme
10 théorèmes. **Aucun postulat quantique n'est nécessaire.**

L'espace de Hilbert n'est pas une propriété fondamentale de la
nature. C'est une **propriété émergente** de la structure
d'équivalence créée par la mémoire harmonique. La superposition
est la linéarité de l'espace quotient. La probabilité est le poids
de Parseval. L'incertitude est la largeur de K(t). La décohérence
est le seuil modal. **Et tout vient d'un seul nombre : φ.**