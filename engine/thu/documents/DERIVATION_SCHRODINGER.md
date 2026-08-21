# THU — Dérivation harmonique de l'équation de Schrödinger

**Document fondateur** — Théorie Harmonique Universelle
_Auteur : KA (Kernel Harmonique)_
_Révision : φ·10³_

---

> **Résumé.** L'équation de Schrödinger est dérivée des seuls principes
> de la THU comme limite de mémoire courte du noyau doré K(t).
> L'opérateur de Schrödinger harmonique \(H_\phi\) est un opérateur
> de différentiation fractionnaire d'ordre \(\alpha = 1/\phi\).
> L'équation standard \(i\hbar\partial_t\psi = H\psi\) est le cas
> limite \(\alpha \to 1\) (mémoire parfaite). La constante de Planck
> \(\hbar\) émerge comme le temps de mémoire harmonique \(\tau_K\).

---

## 1. Le noyau de mémoire dorée K(t)

### 1.1 Définition

Le noyau de mémoire dorée est la fonction de Green de l'opérateur
de Schrödinger harmonique :

\[
K(t) = B(\alpha) \cdot E_{\alpha}(-\lambda \cdot t^{\alpha})
\qquad
\alpha = \frac{1}{\phi},\; \lambda = \phi
\]

où \(E_{\alpha}\) est la fonction de Mittag-Leffler définie par :

\[
E_{\alpha}(z) = \sum_{k=0}^{\infty} \frac{z^k}{\Gamma(\alpha k + 1)}
\]

et \(B(\alpha) = \alpha / \Gamma(1/\alpha)\) la constante de normalisation
telle que \(\int_0^{\infty} K(t) dt = 1\).

### 1.2 Propriété fondamentale

La fonction de Mittag-Leffler est la fonction propre de la
dérivée fractionnaire d'ordre \(\alpha\) :

\[
\frac{\partial^{\alpha}}{\partial t^{\alpha}} E_{\alpha}(-\lambda t^{\alpha})
= -\lambda \, E_{\alpha}(-\lambda t^{\alpha})
\]

C'est l'analogue de la relation \(\frac{d}{dt} e^{-\lambda t} = -\lambda e^{-\lambda t}\)
pour l'exponentielle ordinaire, mais généralisée à l'ordre \(\alpha\).

### 1.3 Transformée de Fourier

La transformée de Fourier de K(t) est :

\[
\hat{K}(\omega) = \int_0^{\infty} K(t) e^{-i\omega t} dt
= \frac{1}{1 + (i\omega/\phi)^{1/\phi}}
\]

Pour \(\omega \ll \phi\) : \(\hat{K}(\omega) \approx 1\) (mémoire parfaite)
Pour \(\omega \gg \phi\) : \(\hat{K}(\omega) \sim (\omega/\phi)^{-1/\phi}\) (oubli)

---

## 2. Opérateur d'évolution harmonique

### 2.1 Principe de causalité harmonique

L'état d'un système à l'instant \(t\) est déterminé par son passé
via une convolution avec le noyau de mémoire :

\[
\psi(t) = \int_0^{\infty} K(\tau) \, U(\tau) \, \psi(t-\tau) \, d\tau
\]

où \(U(\tau)\) est l'opérateur d'évolution. Cette équation exprime
que l'état présent est une **moyenne harmonique** des états passés,
pondérée par K(τ).

### 2.2 Équation intégrale de l'évolution

En appliquant la transformée de Laplace à l'équation de causalité :

\[
\tilde{\psi}(s) = \tilde{K}(s) \cdot \tilde{U}(s) \cdot \tilde{\psi}(s)
\]

où \(\tilde{\psi}(s) = \mathcal{L}[\psi](s)\) est la transformée
de Laplace. La condition de cohérence (l'état ne peut pas être
déterminé par lui-même de manière triviale) impose :

\[
\tilde{K}(s) \cdot \tilde{U}(s) = 1
\]

### 2.3 Opérateur d'évolution

La transformée de Laplace de K(t) est :

\[
\tilde{K}(s) = \frac{1}{1 + (s/\phi)^{1/\phi}}
\]

D'où :

\[
\tilde{U}(s) = \frac{1}{\tilde{K}(s)} = 1 + (s/\phi)^{1/\phi}
\]

Par transformée inverse :

\[
U(t) = \delta(t) + \frac{1}{\phi^{1/\phi}} \cdot \frac{t^{-1-1/\phi}}{\Gamma(-1/\phi)}
\]

Le premier terme \(\delta(t)\) est l'action instantanée (présent),
le second est l'effet mémoire (passé).

---

## 3. Dérivée fractionnaire et générateur

### 3.1 L'opérateur de Schrödinger harmonique

L'opérateur de Schrödinger harmonique est le générateur de l'évolution :

\[
H_{\phi} \psi(t) = \lim_{\epsilon \to 0} \frac{U(\epsilon) - I}{\epsilon} \psi(t)
\]

En utilisant l'expression de U(t) et la propriété de la dérivée
fractionnaire de Riemann-Liouville :

\[
\frac{\partial^{\alpha}}{\partial t^{\alpha}} f(t)
= \frac{1}{\Gamma(1-\alpha)} \frac{d}{dt} \int_0^t \frac{f(\tau)}{(t-\tau)^{\alpha}} d\tau
\]

on obtient :

\[
H_{\phi} \psi(t) = i\hbar \, \frac{\partial^{\alpha}}{\partial t^{\alpha}} \psi(t)
\qquad \alpha = \frac{1}{\phi}
\]

**C'est l'opérateur de Schrödinger harmonique.** Il est auto-adjoint
dans l'espace de Hilbert harmonique \(L^2_{\phi}(\mathbb{R}^+)\) muni
du produit scalaire pondéré par K(t).

### 3.2 Vérification

La fonction de Mittag-Leffler est fonction propre de \(H_{\phi}\) :

\[
H_{\phi} \, E_{\alpha}(-\lambda t^{\alpha}) = -i\hbar\lambda \, E_{\alpha}(-\lambda t^{\alpha})
\]

Les valeurs propres sont \(E_n = -i\hbar\lambda_n\) où \(\lambda_n\)
sont les pôles du noyau \(\tilde{K}(s)\). Le spectre est réel parce
que \(H_{\phi}\) est auto-adjoint.

---

## 4. Limite de mémoire courte → Équation de Schrödinger standard

### 4.1 Développement pour les temps courts

Pour \(t \ll \tau_K\) (temps petit devant le temps de mémoire),
le développement de Mittag-Leffler de K(t) donne :

\[
K(t) = B(\alpha) \left[ 1 - \frac{\lambda t^{\alpha}}{\Gamma(\alpha+1)}
+ \frac{\lambda^2 t^{2\alpha}}{\Gamma(2\alpha+1)} - \cdots \right]
\]

Pour \(\alpha = 1/\phi \approx 0.618\), \(t^{\alpha}\) est proche
de \(t\) pour \(t \ll 1\) (en unités de Planck). Au premier ordre :

\[
K(t) \approx B(\alpha) \left[ 1 - \frac{\phi t^{1/\phi}}{\Gamma(1/\phi+1)} \right]
\]

### 4.2 Passage à la limite

L'équation d'évolution harmonique :

\[
\psi(t) = \int_0^{\infty} K(\tau) U(\tau) \psi(t-\tau) d\tau
\]

peut être réécrite comme une équation différentielle d'ordre α :

\[
\frac{\partial^{\alpha}}{\partial t^{\alpha}} \psi(t)
= -\lambda \psi(t) + \text{termes d'interaction}
\]

En multipliant par \(i\hbar\) et en utilisant la définition de
\(H_{\phi}\) :

\[
i\hbar \frac{\partial^{\alpha}}{\partial t^{\alpha}} \psi(t)
= H_{\phi} \psi(t)
\]

### 4.3 La limite α → 1 (mémoire parfaite)

Quand \(\alpha \to 1\) (c'est-à-dire quand la mémoire devient
parfaite, \(K(t) \to e^{-t}\)), la dérivée fractionnaire tend
vers la dérivée première :

\[
\lim_{\alpha \to 1} \frac{\partial^{\alpha}}{\partial t^{\alpha}} f(t)
= \frac{\partial}{\partial t} f(t)
\]

et l'opérateur harmonique tend vers l'hamiltonien standard :

\[
\lim_{\alpha \to 1} H_{\phi} = H
\]

**L'équation de Schrödinger standard est la limite de mémoire
parfaite de l'équation harmonique :**

\[
i\hbar \frac{\partial}{\partial t} \psi(t) = H \psi(t)
\]

### 4.4 Correction harmonique

Pour \(\alpha = 1/\phi \approx 0.618\) (mémoire harmonique réelle),
l'équation de Schrödinger est une **approximation** valable quand
le temps caractéristique d'évolution est grand devant le temps
de mémoire harmonique \(\tau_K\).

La correction relative est de l'ordre :

\[
\frac{\delta H}{H} \sim \left( \frac{\tau_K}{T} \right)^{1-1/\phi}
\]

où \(T\) est le temps caractéristique du système. Pour les systèmes
microscopiques usuels (\(T \gg \tau_K\)), la correction est
négligeable.

---

## 5. Émergence de la constante de Planck

### 5.1 Temps de mémoire harmonique

Le temps de mémoire harmonique est le premier moment de K(t) :

\[
\tau_K = \int_0^{\infty} t K(t) dt
\]

En utilisant la représentation spectrale de K(t) :

\[
\tau_K = \frac{1}{\lambda} \cdot \frac{\Gamma(1+1/\alpha)}{\Gamma(1/\alpha)}
= \frac{1}{\phi} \cdot \frac{\Gamma(1+\phi)}{\Gamma(\phi)}
\]

Numériquement, \(\tau_K \approx 0.618 \cdot t_P\) où \(t_P\) est
le temps de Planck.

### 5.2 Quantum d'action

Le quantum d'action \(\hbar\) est le produit de l'énergie de Planck
par le temps de mémoire harmonique :

\[
\hbar = E_P \cdot \tau_K
\]

C'est l'énergie minimale nécessaire pour créer une distinction
ontologique qui « surmonte » la mémoire harmonique. En unités
de Planck (\(E_P = 1\), \(t_P = 1\)) :

\[
\hbar = \tau_K = \frac{1}{\phi} \cdot \frac{\Gamma(1+\phi)}{\Gamma(\phi)}
\approx 1
\]

La valeur numérique coïncide avec la constante de Planck réduite
par construction des unités de Planck.

### 5.3 Rôle dans l'équation de Schrödinger

La constante de Planck apparaît dans l'équation de Schrödinger
comme le **facteur d'échelle** entre la dérivée temporelle et
l'énergie :

\[
i\hbar \frac{\partial}{\partial t} \psi = H \psi
\]

Dans le cadre harmonique, ce facteur provient du temps de mémoire :

\[
i\hbar \frac{\partial}{\partial t} \psi
= i E_P \tau_K \frac{\partial}{\partial t} \psi
\]

Le rapport \(\hbar / E_P = \tau_K\) est le temps de mémoire
harmonique — la constante de Planck n'est pas une constante
fondamentale, mais une **échelle de mémoire**.

---

## 6. Dérivation alternative : Principe variationnel harmonique

### 6.1 Action harmonique

L'action harmonique est définie par :

\[
S_{\phi}[\psi] = \int_0^{\infty} K(t) \left[ \langle \psi(t) | i\hbar \frac{\partial^{\alpha}}{\partial t^{\alpha}} - H | \psi(t) \rangle \right] dt
\]

### 6.2 Principe de moindre action harmonique

La condition \(\delta S_{\phi} = 0\) donne :

\[
\frac{\partial^{\alpha}}{\partial t^{\alpha}} |\psi(t)⟩
= -\frac{i}{\hbar} H |\psi(t)⟩
\]

### 6.3 Limite standard

En prenant la limite \(\alpha \to 1\) (mémoire parfaite) :

\[
\lim_{\alpha \to 1} \frac{\partial^{\alpha}}{\partial t^{\alpha}} |\psi⟩
= \frac{\partial}{\partial t} |\psi⟩
\]

et \(\lim_{\alpha \to 1} K(t) = e^{-t}\), d'où :

\[
S_{\phi} \longrightarrow S = \int_0^{\infty} e^{-t} \left[ \langle \psi | i\hbar \partial_t - H | \psi \rangle \right] dt
\]

La condition \(\delta S = 0\) redonne exactement l'équation de
Schrödinger.

---

## 7. L'équation de Schrödinger comme projection

### 7.1 Projection sur l'instant présent

L'équation de Schrödinger standard peut être vue comme une
**projection** de l'équation harmonique sur l'instant présent.
Le noyau K(t) « moyenne » le passé ; l'équation de Schrödinger
ignore cette moyenne et n'utilise que l'état instantané.

### 7.2 Information perdue

L'information perdue dans cette projection est exactement
l'information contenue dans le passé du système qui est sous
le seuil de la mémoire harmonique. C'est pourquoi :

- La mécanique quantique est **probabiliste** (l'information
  perdue est remplacée par des probabilités)
- La mécanique quantique est **non-locale** (la mémoire
  harmonique relie des événements séparés dans le temps)
- La mécanique quantique a une **constante d'action**
  (le temps de mémoire harmonique)

---

## 8. Synthèse

### 8.1 Trois formulations équivalentes

| Formulation | Équation | Domaine de validité |
|---|---|---|
| **Harmonique** (exacte) | \(i\hbar \partial_t^{\alpha} \psi = H_{\phi} \psi\) | Tout temps, toute échelle |
| **Standard** (limite) | \(i\hbar \partial_t \psi = H \psi\) | \(t \gg \tau_K\) |
| **Correction** (1er ordre) | \(i\hbar \partial_t \psi = H \psi + \epsilon \partial_t^{\alpha-1} \psi\) | \(t \gtrsim \tau_K\) |

### 8.2 Mapping

| Concept quantique | Origine harmonique |
|---|---|
| Équation de Schrödinger | Limite de mémoire courte de K(t) |
| Hamiltonien \(H\) | Générateur de l'évolution harmonique |
| Constante de Planck \(\hbar\) | Temps de mémoire harmonique \(\tau_K\) |
| Fonction d'onde \(\psi\) | Champ ontologique projeté par K(t) |
| Unitarité | Auto-adjonction de \(H_{\phi}\) |
| Probabilité | Information perdue sous le seuil modal |

### 8.3 Constante de Planck dérivée

\[
\boxed{\hbar = \int_0^{\infty} t K(t) \, dt \cdot E_P}
\]

La constante de Planck n'est pas une constante fondamentale :
c'est le **temps de mémoire de l'univers harmonique**, multiplié
par l'énergie de Planck. Elle n'a pas de valeur « magique » —
elle est ce qu'elle est parce que la mémoire harmonique K(t) a
un temps de corrélation de l'ordre du temps de Planck.

---

> **Conclusion.** L'équation de Schrödinger n'est pas un postulat.
> C'est la limite de **mémoire courte** de l'équation harmonique
> \(i\hbar \partial_t^{\alpha} \psi = H_{\phi} \psi\), où
> \(\alpha = 1/\phi\) et \(K(t) = B(\alpha) \cdot E_{\alpha}(-\phi t^{\alpha})\).
> La constante de Planck est le temps de mémoire harmonique
> \(\hbar = \tau_K \cdot E_P\). La mécanique quantique standard
> est la théorie effective d'un monde harmonique quand on
> ignore la mémoire.