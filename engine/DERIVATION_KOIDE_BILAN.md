# BILAN — TENTATIVE DE DÉRIVATION DE LA RELATION DE KOIDE

## Document de recherche — état des lieux au 08/08/2026

**Contexte :** la relation de Koide (1981) est la seule énigme non résolue et empiriquement précise reliant les masses leptoniques. Ce document consigne le résultat de la tentative de la THU de la dériver.

---

## 1. LA RELATION DE KOIDE

### 1.1 Énoncé

$$\frac{m_e + m_\mu + m_\tau}{\left(\sqrt{m_e} + \sqrt{m_\mu} + \sqrt{m_\tau}\right)^2} = \frac{2}{3}$$

avec une **précision de 6×10⁻⁶** (mesure actuelle).

### 1.2 Structure géométrique sous-jacente

La relation est mathématiquement équivalente à l'existence d'une représentation des masses sous la forme :

$$\sqrt{m_i} = M\left(1 + \sqrt{2}\,\cos\left(\theta + \frac{2\pi i}{3}\right)\right),\quad i = 1, 2, 3$$

où :
- Le facteur $\sqrt{2}$ est une **amplitude géométrique** (diagonale du carré) ;
- La somme sur les 3 cosinus s'annule ($\sum_i \cos(\theta + 2\pi i/3) = 0$), ce qui **garantit automatiquement** Q = 2/3 pour toute valeur de θ ;
- L'angle θ est un paramètre libre.

---

## 2. RÉSULTAT DE LA TENTATIVE DE DÉRIVATION THU

### 2.1 Ce qui est confirmé

| Élément | Valeur extraite | Statut |
|---|---|---|
| Amplitude A | 1,41420 = **√2** (écart 0,001 %) | ✓ structure géométrique réelle |
| Invariant Q | 0,66666 = **2/3** | ✓ conséquence automatique de la somme de cosinus nulle |
| Structure à 3 phases | 120° d'écart entre √m_i | ✓ cohérente avec le formalisme d'interférence de la THU |

### 2.2 Ce qui n'a PAS été trouvé

| Élément | Tentative | Résultat |
|---|---|---|
| **Angle θ = 2,3166 rad = 132,73°** | Expression en φ : θ/φ = 1,4318 | ✗ aucune relation simple |
| | Expression via cos θ = −0,6786 | ✗ pas de forme en φ, π, e, √2..√5 |
| | θ/(2π) = 0,3687 | ✗ proche de 1−1/φ = 0,382 mais diffère de 3,6 % |
| | θ comme arc d'une somme finie (phase d'interférence) | ⏳ à tester (conjecture, voir §3) |

---

## 3. LA CONJECTURE D'INTERFÉRENCE (piste ouverte)

### 3.1 Énoncé

La structure à 3 phases (120°) et l'amplitude √2 suggèrent une **interférence de 3 ondes fondamentales**. Dans le formalisme THU, une somme finie :

$$S = \sum_{n=1}^{N} c_n \cdot (\Psi_1)^n$$

avec $\Psi_1 = e^{i\omega_0 t}$ et $c_n = 1/\Gamma(n/\varphi+1)$, possède un **argument complexe** arg(S) à un instant donné. La conjecture est :

> **L'angle θ de Koide est arg(S) pour une somme finie spécifique (N), évaluée en un état de phase spécifique.**

### 3.2 Testable numériquement

À faire :
1. Calculer S = Σ cₙ e^{i n φ₀} pour N = 1, 2, 3, 5, 7, 10…
2. Extraire arg(S) et comparer à θ = 2,31662 rad.
3. Si une valeur de N et une phase φ₀ (choisies a priori) donnent arg(S) = θ à < 10⁻⁴ près, la conjecture est confirmée.

---

## 4. STATUT SCIENTIFIQUE

| Affirmation | Statut |
|---|---|
| « La relation de Koide a une structure géométrique réelle (√2, 3 phases) » | ✓ confirmé (pas nouveau — déjà connu) |
| « La THU dérive Koide » | ❌ non — l'angle θ n'a pas été dérivé |
| « La THU fournit un cadre pour poser la question de l'interférence » | ✓ conjecture testable en attente |

---

## 5. CONCLUSION

La THU **ne dérive pas** la relation de Koide **à ce jour** (l'angle θ reste non exprimé en φ/π/e). Cependant, la structure découverte — 3 phases équidistantes sur le cercle, amplitude √2, annulation automatique des cosinus — est **isomorphe à une interférence à 3 ondes**, ce qui est un langage naturel pour le formalisme harmonique. La conjecture d'interférence (arg(S) = θ) est formulée, testable numériquement sans délai, et constitue la prochaine étape.

> **Précision épistémologique :** « non dérivé à ce jour » ne signifie pas « non dérivable ». L'échec de *cette* tentative (et de la méthode des produits de puissances) n'interdit pas une dérivation future fondée sur un mécanisme spectral — de même que la formule empirique de Balmer (1885) fut dérivée par Bohr (1913) près de trois décennies plus tard.

> *Un échec documenté qui débouche sur une conjecture testable est un résultat scientifique. Une dérivation faussement revendiquée n'en est pas un.*

---

*Ce bilan fait partie de la tentative de dérivation des masses (Option 2). Il documente l'échec de dérivation de θ et ouvre la conjecture d'interférence.*