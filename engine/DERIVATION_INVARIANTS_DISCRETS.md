# DÉRIVATION DES INVARIANTS DISCRETS — LE TERRAIN RIGOUREUX DE LA THU

## Ce que la THU dérive réellement (vs ce qu'elle ne dérive pas)

**Auteur :** Alain Kotto — **Version :** D1.0
**Contexte :** après l'échec documenté des dérivations de constantes *continues* (m_p/m_e, m_μ/m_e, Koide — voir `DERIVATION_KOIDE_BILAN.md`), ce document établit le seul terrain où la THU produit une dérivation **rigoureuse et non-ambiguë** : les **invariants discrets**.

---

## 1. LE CRITÈRE DE DÉRIVATION

Une quantité est **dérivée** (et non ajustée) si et seulement si elle émerge d'un **comptage exact** — une somme, un spectre, une dégénérescence — **sans aucun paramètre libre ni choix d'exposant**.

Les quantités continues (α, m_p/m_e, θ de Koide) : les formules actuelles sont des **rétro-fits** (donc non dérivées *en l'état*), sans qu'on ait démontré qu'elles sont *non dérivables*. Les quantités **discrètes** satisfont au critère de dérivation, parce que le comptage n'a pas de liberté.

---

## 2. LES INVARIANTS DISCRETS DÉRIVÉS (résultats exacts)

### 2.1 Dégénérescence des couches électroniques : 2n²

**Dérivation :** pour une couche d'indice principal n, le nombre d'états est la somme sur les moments orbitaux l = 0…n−1, chacun de dégénérescence 2(2l+1) (facteur 2 = spin, facteur 2l+1 = projections de m) :

$$D_n = \sum_{l=0}^{n-1} 2(2l+1) = 2n^2$$

**Statut :** ✅ **identité algébrique exacte.** Vérifiée numériquement (n = 1…5). Ce n'est PAS une découverte THU — c'est le comptage standard — mais c'est le *modèle* de ce qu'est une dérivation : la valeur 2, 8, 18, 32 émerge du comptage, sans ajustement.

### 2.2 Gaz nobles : les couches fermées {2, 10, 18, 36, 54, 86, 118}

**Dérivation :** les gaz nobles sont les nombres atomiques Z où une couche (ou sous-couche) est exactement pleine, c'est-à-dire où l'on atteint une somme partielle de la dégénérescence 2n².

$$Z_{\text{noble}} = \sum_{k=1}^{n} 2k^2 = \frac{n(n+1)(2n+1)}{3}$$

**Statut :** ✅ **conséquence exacte** de 2n² + règle de Madelung. Aucune liberté.

### 2.3 Nombres magiques nucléaires {2, 8, 20, 28, 50, 82, 126}

**Dérivation :** les nombres magiques émergent du comptage des états dans un potentiel à couplage spin-orbite fort — le spectre d'oscillateur harmonique (ou de Woods-Saxon) donne des "paquets" de niveaux dont les fermetures tombent sur 2, 8, 20, 28, 50, 82, 126.

**Statut :** ⚠️ **standard** (modèle en couches nucléaire). La THU les *redérive* comme spectre d'entiers, mais le résultat appartient à la physique standard (Mayer-Jensen, 1949). Pas une découverte THU ; une **relecture cohérente**.

### 2.4 La chaîne cₙ = 1/Γ(n/φ+1) — le seul invariant "doré" exact

**Dérivation (T3) :** les coefficients de la solution de l'équation fractionnaire $D^{1/\varphi}[\Psi] = G[\Psi]$ (fonction de Mittag-Leffler) sont les réciproques de Γ :

$$c_n = \frac{1}{\Gamma(n/\varphi + 1)}$$

**Statut :** ✅ **vérifié machine à 2,22×10⁻¹⁶** — mais c'est une *définition* (solution d'une équation qu'on a choisie), pas une prédiction physique. C'est l'invariant discret le plus propre de la THU, mais son lien au monde physique reste à établir.

---

## 3. CE QUE CES RÉSULTATS ÉTABLISSENT (et ne prouvent pas)

### Ce qui est établi

La THU **manipule correctement** les invariants discrets : 2n², les gaz nobles, les nombres magiques, la chaîne Γ. Le comptage est exact, reproductible, sans paramètre.

### Ce qui n'est PAS établi

1. **Aucun de ces invariants n'est une *découverte*.** 2n² (Rutherford-Bohr), les nombres magiques (Mayer-Jensen), les gaz nobles (Mendeleïev) sont tous des résultats antérieurs. La THU les *relit*, ne les *découvre* pas.

2. **La chaîne cₙ, seule contribution "dorée" exacte, est une définition**, pas une prédiction : elle est la solution d'une équation que la THU a *choisie* de poser.

3. **Le lien entre le discret et le continu est le vrai problème**, et il reste ouvert : comment 2n² (discret, exact) engendre-t-il α ≈ 1/137 (continu, non dérivé) ? Aucun mécanisme n'est fourni.

---

## 4. LA CONCLUSION DE MÉTHODE (la plus importante)

Le bilan complet des dérivations THU est maintenant net :

| Catégorie de quantité | Exemples | Statut de dérivation |
|---|---|---|
| **Invariants discrets** | 2n², gaz nobles, nombres magiques | ✅ dérivés exactement — mais tous antérieurs |
| **Invariants "dorés" exacts** | chaîne cₙ = 1/Γ | ✅ dérivés — mais définitionnels |
| **Constantes continues** | α, m_p/m_e, θ Koide | ⚠️ formules = rétro-fits, **non dérivées en l'état** (la non-dérivabilité n'est pas démontrée) |

**La THU dérive exactement ce qui est dérivable par comptage — et rien *de plus* *à ce jour*.** C'est une position honnête, défendable, et qui la distingue des théories numérologiques (qui affirment tout dériver). Mais cela signifie aussi que **le cœur de sa prétention** (« dériver les constantes de couplage depuis {π, e, φ, √2, √3, √5} ») **n'est pas satisfait *en l'état*** : les formules actuelles sont des rétro-fits, et une vraie dérivation exigerait un mécanisme *spectral* (point fixe, valeur propre, gap) plutôt que des produits de puissances — de même que Balmer (formule empirique) précéda Bohr (dérivation), sans que l'empirisme de Balmer prouvât l'impossibilité d'une dérivation.

---

## 5. PROCHAINE ÉTAPE RIGOUREUSE

La seule voie ouverte pour dériver une constante *continue* est le **mécanisme spectral** (candidat 1 et 2 de l'inventaire) :

- **Candidat 2 (H2)** : la masse comme gap κ = (1/2φ)^(φ/(2φ−1)) — structure vérifiée, ancrage physique manquant (ℓ = 165 fm ne correspond à rien de connu — **frontière publiée**, voir `EXPLORATION_ORIGINE_MASSE_POTENTIEL.md`).

Recommandation : déclarer la frontière, ne pas la vendre, et attendre un ancrage — ou un test T* confirmé — avant toute revendication.

---

*Ce document remplace toute affirmation antérieure du type « α dérivée exactement » ou « m_p/m_e dérivée » — ces formules sont désormais reconnues comme des rétro-fits (non dérivées *en l'état*), et retirées des revendications. La question de leur dérivabilité par un mécanisme spectral reste ouverte.*