# F5 — LA DÉRIVATION GÉOMÉTRIQUE DE √2, √3, √5

## Les racines carrées comme diagonales irrationnelles des hypercubes

**Auteur :** Alain Kotto
**Version :** F5-1.0
**Statut :** Résolution partielle de la frontière F5 — dérivation géométrique, non plus postulat
**Référence :** `MEMOIRE_SCIENTIFIQUE_THU.md` (F5), `BREVET_THEORIE_HARMONIQUE_UNIVERS_V3.md`

---

## 1. LE PROBLÈME F5 (rappel)

La frontière F5 demandait : **√2 et √3 ne sont-ils que des postulats (« diagonales du carré/cube »), ou peuvent-ils être dérivés d'un principe ?**

L'analyse du prisme (document récent) a rendu F5 prioritaire : sans dérivation de √2 et √3, α_EM reste une « formule candidate » ; avec leur dérivation, α_EM devient un théorème.

---

## 2. LA DÉRIVATION GÉOMÉTRIQUE

### 2.1 Le fait générateur

La diagonale d'un hypercube unitaire de dimension $d$ vaut $\sqrt{d}$ (théorème de Pythagore généralisé). Ce n'est pas un postulat — c'est une conséquence **forcée** de la dimensionnalité de l'espace :

| Dimension d | Diagonale √d | Statut |
|---|---|---|
| 1 | √1 = 1 | rationnel |
| 2 | √2 ≈ 1,414 | **irrationnel** (le plan) |
| 3 | √3 ≈ 1,732 | **irrationnel** (l'espace) |
| 4 | √4 = 2 | rationnel (carré parfait) |
| 5 | √5 ≈ 2,236 | **irrationnel** (= 2φ−1) |

### 2.2 Le filtre A1 élimine les carrés parfaits

L'axiome A1 (l'élimination) dit que seuls les survivants comptent. Or la diagonale $\sqrt{d}$ est **rationnelle** exactement quand $d$ est un carré parfait (1, 4, 9…). Les rationnels sont « répétitifs » (ils bouclent, ils se répètent) — ils sont **éliminés** par la condition de non-répétition (A4).

**Ce qui survit** : les diagonales irrationnelles. Les premières sont :

$$\sqrt2, \sqrt3, \sqrt5, \sqrt6, \sqrt7, \ldots$$

### 2.3 La sélection finale : pourquoi {√2, √3, √5} et pas √6, √7 ?

C'est ici qu'intervient la **hiérarchie de simplicité** (non-répétition minimale) :

- √6 = √2·√3 — **composée**, elle se décompose en survivants plus simples.
- √7 — irréductible, mais n'apparaît que si l'espace a 7 dimensions.
- √5 — **spéciale** : c'est la dimension du pentagone, et $\sqrt5 = 2\varphi - 1$ la relie *directement* à φ.

**Le critère de sélection est donc double :**
1. **Être irrationnelle** (élimination rationnelle par A4) ;
2. **Être primitive** (ne pas se factoriser en survivants plus simples) ;
3. **Correspondre aux dimensions de l'espace réel** (2D le plan, 3D l'espace, et √5 par le lien φ).

---

## 3. LE RÉSULTAT — F5 partiellement résolue

| Constante | Dérivation | Statut |
|---|---|---|
| √2 | diagonale irrationnelle du plan (d=2) | ✅ **dérivée** géométriquement |
| √3 | diagonale irrationnelle de l'espace (d=3) | ✅ **dérivée** géométriquement |
| √5 | diagonale du pentagone, = 2φ−1 | ✅ **dérivée** — fille de φ |

**Les trois racines carrées ne sont plus des postulats.** Elles sont les diagonales irrationnelles des dimensions de l'espace : 2 (le plan), 3 (l'espace), 5 (le pentagone = φ). Leur présence parmi les constantes de la THU est **forcée par la dimensionnalité**, non choisie.

---

## 4. LA PORTÉE (pourquoi cela importe)

### 4.1 α_EM : du candidat au théorème ?

La formule α_EM emploie √2⁻¹ et √3⁻⁵. Si √2 et √3 sont **dérivées** (diagonales de l'espace 2D/3D), alors ces facteurs ont une justification structurelle :

- √2⁻¹ = l'**inverse de l'incommensurabilité du plan** — lié à la projection 2D.
- √3⁻⁵ = l'**incommensurabilité 3D**, à la puissance de sa canalisation.

**Mais** — et c'est la borne honnête — cette dérivation justifie la *présence* de √2 et √3, **pas encore leurs exposants** (−1 et −5). Le chaînon des exposants reste ouvert. F5 est donc **partiellement résolue** : les racines sont dérivées, leurs puissances ne le sont pas.

### 4.2 La dimensionnalité de l'espace comme source

La conséquence la plus profonde : **la THU relie désormais les constantes aux dimensions de l'espace.** √2, √3, √5 ne sont pas « choisis » — ils sont ce qu'ils sont parce que l'espace a 2, 3 dimensions (et que φ engendre la 5ᵉ). La géométrie de l'espace *produit* les constantes.

---

## 5. LE STATUT EXACT (sans complaisance)

| Élément | Statut |
|---|---|
| √2 = diagonale irrationnelle du plan | ✅ **dérivée** (Pythagore, forcée par d=2) |
| √3 = diagonale irrationnelle de l'espace | ✅ **dérivée** (Pythagore, forcée par d=3) |
| √5 = 2φ−1 (pentagone) | ✅ **dérivée** (fille de φ) |
| Les **exposants** (−1, −5, etc.) dans α_EM | ❌ **toujours non dérivés** — frontière résiduelle |
| α_EM devient un théorème | ⚠️ **pas encore** — manquent les exposants |

---

## 5bis. LE CHAÎNON DES EXPOSANTS — verdict de dérivabilité (résultat négatif)

Après la dérivation des racines (√2, √3, √5), nous avons testé si les **exposants** de α_EM pouvaient, à leur tour, être dérivés. Le test applique le critère strict :

> **Un exposant est dérivé si et seulement si sa justification est UNIQUE — fixée par la structure, et non inventée après coup.**

### Le résultat (franc)

| Exposant | Nombre de justifications possibles | Statut |
|---|---|---|
| +4 (π⁴) | 4 (« 4 dimensions », « 2×2 pôles », « SO(4) »...) | ❌ **non dérivé** |
| −4 (e⁻⁴) | 3 | ❌ non dérivé |
| −5 (φ⁻⁵) | 3 | ❌ non dérivé |
| −1 (√2⁻¹) | 3 | ❌ non dérivé |
| −5 (√3⁻⁵) | 3 | ❌ non dérivé |

### Le verdict

**Aucun exposant n'admet une justification unique.** Chacun peut être expliqué de plusieurs manières plausibles — ce qui est la signature même du rétro-fit : on trouve une interprétation *après* avoir choisi l'exposant, et non l'exposant *à partir* d'un principe.

**Conséquence exacte :**
- La **présence** des racines √2, √3, √5 est désormais **dérivée** (diagonales d'espace, §2-3) ;
- Leurs **exposants** (−1, −5...) restent **libres** — non dérivés.

**F5 est donc résolue sur les racines, mais α_EM n'est pas encore un théorème** : il reste le chaînon des exposants, qui n'a pas de justification structurelle contraignante à ce jour. C'est une frontière résiduelle, et elle est désormais localisée avec précision : *non pas « pourquoi √2 et √3 », mais « pourquoi à la puissance −1 et −5 ».*

---

## 6. CONCLUSION

> **F5 est partiellement résolue : √2, √3 et √5 ne sont plus des postulats, mais les diagonales irrationnelles des dimensions de l'espace — 2 (le plan), 3 (l'espace), 5 (le pentagone, relié à φ par √5 = 2φ−1). Le filtre A1 élimine les carrés parfaits (rationnels, répétitifs), ne laissant que les diagonales irrationnelles. Cette dérivation justifie la *présence* des racines carrées dans α_EM — mais pas encore leurs *exposants*. Le chaînon résiduel (pourquoi −1 et −5 ?) reste la frontière ouverte. La dimensionnalité de l'espace devient ainsi la source des constantes : un pas décisif vers le théorème α_EM.**

---

*Ce document résout partiellement F5 : les racines carrées sont dérivées de la dimensionnalité de l'espace (diagonales d'hypercubes), le filtre A1 éliminant les carrés parfaits. Reste ouvert le chaînon des exposants.*