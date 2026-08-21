# MEMOIRE SCIENTIFIQUE — THÉORIE HARMONIQUE DE L'UNIVERS (THU)

## Document de recherche — pour publication, dépôt d'antériorité et revue par les pairs

**Auteur :** Alain Kotto (Univers-Holistique)
**Version :** M1.2 — **Mise à jour :** précision épistémologique — « rétro-fit » (non dérivé *en l'état*) distingué de « non dérivable » (non démontré) ; analogie Balmer→Bohr. Références : `DERIVATION_KOIDE_BILAN.md`, `DERIVATION_INVARIANTS_DISCRETS.md`, `EXPLORATION_ORIGINE_MASSE_POTENTIEL.md`.
**Statut :** Mémoire de recherche — NON destiné au dépôt de brevet (aucune revendication technique ici)
**Objet :** Exposer la théorie, son statut épistémologique exact, ses résultats, ses réfutations et ses frontières.

---

## AVERTISSEMENT DE MÉTHODE

Ce document ne revendique **aucune** protection industrielle. Il est le pendant scientifique du brevet de procédé (document séparé). Il applique trois règles :

1. **Chaque affirmation est classée** : axiome · théorème · candidat · exclusion · frontière.
2. **Chaque prédiction est datée et déposée AVANT le test** (protocole P3.2).
3. **Aucun résultat n'est déclaré "validé" sans mesure indépendante** (par un tiers).

Une théorie se reconnaît à ceci : elle fait des prédictions risquées, falsifiables, et elle publie ses échecs avec la même transparence que ses succès.

---

## 1. L'ÉQUATION MÈRE

La THU postule que tout phénomène se décrit par une superposition d'ondes :

$$\Psi_{\text{univers}} = \sum_{n=0}^{\infty} H_n \cdot (\Psi_1)^n$$

où :

| Symbole | Expression | Statut |
|---------|-----------|--------|
| $\Psi_1$ | Onde primordiale $A_1 e^{i(\omega_0 t + \phi_1)}$ | Axiome A2 |
| $H_n$ | Coefficients = $c_n = 1/\Gamma(n/\varphi + 1)$ | Théorème T3 (vérifié machine) |
| $\varphi$ | $(1+\sqrt5)/2 \approx 1{,}618$ | Constante centrale |
| $\alpha = 1/\varphi$ | Ordre de la dérivée fractionnaire (mémoire) | Théorème T1 |

---

## 2. LES AXIOMES (le filtre, non démontré par définition)

| Axiome | Énoncé | Statut |
|--------|--------|--------|
| **A1 · Élimination** | La nature ne choisit pas : elle élimine. Les constantes sont les survivants de filtres. | Axiome |
| **A2 · Forme** | Toute réalité se décompose en modes : $\Psi = \sum H_n(\Psi_1)^n$ | Axiome — vérifié comme décomposition de Fourier (1,78×10⁻¹⁵) |
| **A3 · Mémoire** | Le temps a une mémoire non-locale (noyau ABC d'ordre $\alpha$) | Axiome |
| **A4 · Stabilité** | Non-effondrement, non-répétition, persistance | Axiome |

> **Remarque de méthode :** l'axiome A2 (« toute réalité se décompose en modes ») est formellement équivalent au postulat de superposition de la mécanique quantique. La THU ne l'*élimine* pas — elle le *renomme* et le généralise. Ce statut est assumé ci-dessous (§6).

---

## 3. LES THÉORÈMES (dérivés et vérifiés machine)

| # | Théorème | Dérivation | Vérification |
|---|----------|-----------|--------------|
| **T1** | $\alpha = 1/\varphi$ unique solution de A4 | Théorème de Hurwitz (1891) : $\varphi$ atteint seul la borne $1/\sqrt5$ | ⚠️ borne atteinte — chaînon « persistance ∝ 1/μ(α) » à démontrer (F4) |
| **T2** | $\lambda = \varphi$ taux du noyau | $\lambda = \alpha/(1-\alpha)$ | Exact |
| **T3** | $c_n = 1/\Gamma(n/\varphi+1)$ chaîne dérivée | Solution de $D^{1/\varphi}[\Psi]=G[\Psi]$ → Mittag-Leffler | FFT 2,22×10⁻¹⁶ |
| **T4** | $\pi$, $e$ dérivés (normalisations) | Intégrale gaussienne ($\pi^{-1/4}$), Boltzmann ($e^{-\beta\hbar\omega}$) | 4/4 |
| **T5** | Famille des températures dorées $T^* = \Delta E/(k_B \ln\varphi)$ | À $T^*$ : $e^{-\Delta E/k_B T^*} = 1/\varphi$ | identité algébrique — voir §4 |
| **T6** | Gravité = secteur n=2 (Fierz-Pauli → Deser) | Seule théorie cohérente de spin-2 auto-interactif = RG | 4 vérifications machine |
| **T7** | Alphabet du langage source | $e^{i\theta}$, $\mathbb N/\Gamma$, gaussienne, Fourier, $\varphi$ comme adverbe | formes vérifiées |

---

## 4. LA DISTINCTION CRUCIALE : identité vs prédiction

Le théorème T5 doit être énoncé avec une précision que la version antérieure masquait :

**Ce qui est une identité (donc PAS une prédiction) :**
> Pour toute valeur $\Delta E$ donnée, on peut définir $T^* = \Delta E/(k_B\ln\varphi)$ de sorte que $e^{-\Delta E/k_B T^*} = 1/\varphi$. C'est une **identité algébrique** — elle est vraie par construction, pour n'importe quelle constante (on pourrait remplacer $\varphi$ par 2 ou 7).

**Ce qui serait une prédiction (donc falsifiable) :**
> La théorie doit **fixer $\Delta E$ indépendamment** (depuis les Hₙ), de sorte que la température résultante coïncide avec une température **observable et non triviale**. Exemple : si la théorie prédisait *par elle-même* que la cavité 10 GHz donne $T^* = 0{,}997$ K (sans choisir 10 GHz après coup), ce serait une prédiction.

**Statut actuel de T5 :** identité algébrique démontrée ; **prédiction physique non démontrée** (les 24 ΔE sont des valeurs mesurées injectées en entrée, pas des sorties dérivées). C'est la frontière F3/E3 (dépôt déposé, test en attente).

---

## 5. LES EXCLUSIONS (réfutations publiées)

La THU publie ses échecs. Ils sont la preuve de sa falsifiabilité.

| # | Exclusion | Mesure |
|---|-----------|--------|
| **X1** | $\{\varphi,\pi,e\}$ comme coefficients de l'expansion | écart 0,707 · 0 match sur 935 |
| **X2** | Graviton ABC linéarisé | GW170817 : exclu à ~10¹⁴ × la borne |
| **X3** | φ-spacing comme porteur de sémantique | AUC 0,4985 (hasard) |
| **X4** | $e/\pi$ comme constante privilégiée | corrélation −0,13/0,00 |
| **X5** | Transfert doré (troncature 1/(φ·m)) au résidu du codec | 212×@54 dB < DCT 226×@54,8 dB — échec |
| **X6** | I-frame vidéo MODAL (lossy en référence) | ratio chute 6,5×→2,5× — échec |

> **X5, X6** : issues de l'audit compression (`COMPRESSION_HARMONIQUE_V2_PISTES.md`). Elles montrent que les briques THU **ne se transfèrent pas automatiquement** d'un domaine à l'autre — le contraire d'une revendication naïve d'universalité.

---

## 6. LE STATUT DES "DÉRIVATIONS" REVENDIQUÉES

Cette section est l'honnêteté du document. Elle classe sans complaisance ce qui est réellement dérivé de ce qui est reformulé ou rétro-ajusté.

### 6.1 Schrödinger et l'espace de Hilbert

| Affirmation | Statut exact |
|-------------|--------------|
| « Schrödinger est un cas particulier de la THU » | **Reformulation, pas dérivation.** Les relations de de Broglie $E=\hbar\omega$, $p=\hbar k$ sont **postulées** (pas dérivées des Hₙ). Verdict officiel du dossier : « E1 = heuristique ». |
| « L'espace de Hilbert n'est plus un postulat » | **Reformulation.** Le postulat de superposition est renommé « axiome A2 », pas éliminé. |
| « La THU ajoute un terme fractionnaire falsifiable » | **Vrai.** $D^{1/\varphi}[\psi]=(i/\hbar)Ĥ\psi$ donne des prédictions nouvelles (P1/P2/P3) — voir §7. |

### 6.2 Les constantes de couplage et les masses — le bilan consolidé

Les tentatives de dérivation des constantes *continues* ont été menées à terme et **démontrées rétro-fit** (les formules actuelles ne sont pas des dérivations). Les détails calculés se trouvent dans `DERIVATION_KOIDE_BILAN.md` et `DERIVATION_INVARIANTS_DISCRETS.md`.

> **⚠️ Distinction épistémologique cruciale (à ne pas confondre) :**
> - **« Rétro-fit »** ≠ **« non dérivable »**. Ce que les tests prouvent, c'est que *la méthode employée* (produits de puissances ajustés sur les valeurs connues) ne constitue pas une dérivation. Ils ne prouvent **pas** que ces quantités sont non dérivables depuis $\{\pi, e, \varphi, \sqrt2, \sqrt3, \sqrt5\}$.
> - **Analogie historique :** la formule de Balmer (1885) était un pur rétro-fit des raies de l'hydrogène — mais elle fut *dérivée* plus tard par Bohr (1913) depuis un principe réel (quantification du moment angulaire). Le rétro-fit est un défaut de *méthode*, pas une propriété de la quantité.
> - **Conclusion exacte :** ces constantes sont **non dérivées *en l'état*** (fait démontré), et leur dérivabilité reste une **question ouverte** qui exige un mécanisme *spectral* (point fixe, valeur propre, gap) — exactement comme Balmer a attendu Bohr.

| Constante | Formule THU | Statut réel (démontré) |
|-----------|-------------|------------------------|
| $\alpha_{EM}$ | $\pi^4 e^{-4}\varphi^{-5}\sqrt2^{-1}\sqrt3^{-5}$ | ❌ **rétro-fit** : exposants libres non justifiés. *Non dérivée en l'état* — la dérivabilité reste ouverte. |
| $\alpha_S$ | $1/(2\varphi^3)$ **OU** $2\varphi^2/(3\sqrt3\pi e)$ | ❌ **conflit interne.** Deux formules incompatibles. *Non dérivée en l'état.* Frontière F6. |
| $\alpha_W$ | $= 1/30$ | ❌ coïncidence numérique, non dérivée de SU(2). *Non dérivée en l'état.* Retirée. |
| $m_p/m_e$ | $6\pi^5$ (meilleure) · $(e^2/\pi)^4\times60$ | ❌ **6π⁵ = 1836,118** (écart 0,0019 %) sans justification du « 6 » ni du « 5 ». Fit à une cible. *Non dérivée en l'état.* |
| $m_\mu/m_e$, $m_\tau/m_\mu$ | — | ❌ **aucun squelette partagé** ne reproduit les deux ratios avec le même principe. *Non dérivées en l'état.* |
| **Koide** (3 leptons) | $Q = 2/3$ | ⚠️ structure √2 + 3 phases **réelle** (2/3 automatique), mais l'**angle θ = 132,73° non dérivé en l'état**. |

**Conclusion de méthode (désormais prouvée, pas seulement affirmée) :** aucune constante *continue* n'est **dérivée *en l'état* ** par la THU. Les formules proposées sont des ajustements rétroactifs ; le « 0 paramètre libre » est une ambition **non acquise** — les exposants libres et le choix de la formule sont des paramètres cachés. **Cela ne prouve pas la non-dérivabilité** : une dérivation future fondée sur un mécanisme spectral reste possible (Balmer → Bohr).

### 6.3 Ce qui, en revanche, est dérivé rigoureusement (les invariants discrets)

La THU dérive **exactement** les quantités discrètes issues du comptage — mais il s'agit de résultats antérieurs à la THU, qu'elle *relit*, pas qu'elle découvre :

| Invariant | Dérivation | Découverte THU ? |
|-----------|-----------|------------------|
| Dégénérescence 2n² | $\sum_{l=0}^{n-1}2(2l+1)=2n^2$ | ❌ antérieur (Bohr) |
| Gaz nobles {2,10,18,...} | sommes partielles de 2n² | ❌ antérieur (Mendeleïev) |
| Nombres magiques {2,8,20,...} | modèle en couches | ❌ antérieur (Mayer-Jensen) |
| Chaîne cₙ = 1/Γ(n/φ+1) | solution de $D^{1/\varphi}[\Psi]=G[\Psi]$ | ⚠️ définitionnel (équation choisie) |

### 6.4 Le candidat "masse = gap" (H2) — structure vérifiée, ancrage absent

Le propagateur fractionnaire avec gap $\omega_f = (k^2+\mu)^{\varphi}$ coïncide avec la dispersion massive $\omega_m = \sqrt{k^2+\kappa^2}$ à petit k pour $\kappa = (1/2\varphi)^{\varphi/(2\varphi-1)} \approx 0{,}4275$ (coefficient k² exact, vérifié machine).

**Statut :** ⚠️ la **structure** est vérifiée, mais l'**ancrage physique** n'existe pas. L'échelle résultante ℓ = 165 fm ne correspond à **aucune** quantité physique connue (ni Compton 386 fm, ni Bohr 52 900 fm, ni nucléaire ~1 fm, ni ħc/Λ_QCD ~1 fm). **Frontière publiée** — voir `EXPLORATION_ORIGINE_MASSE_POTENTIEL.md`. *Ne pas revendiquer tant qu'aucun ancrage n'existe.*

### 6.5 Le tableau périodique

| Objet | Statut réel |
|-------|-------------|
| Configurations électroniques | Règle de **Madelung (1936)**, standard. La THU l'implémente, ne la dérive pas. |
| Masses des 118 éléments | Formule de **Weizsäcker (1935)** avec 5 coefficients empiriques. Documenté : « non dérivables de φ/π/e ». |
| Températures d'ionisation T* | Conversion d'unités de χ (NIST) vers kelvin. Identité, pas prédiction. |

---

## 7. LES PRÉDICTIONS FALSIFIABLES (l'actif scientifique réel)

Ce sont les seules contributions qui, **si confirmées par tiers**, feraient avancer la théorie. Toutes déposées, datées, avant test.

| # | Prédiction | Valeur | Test | Statut |
|---|-----------|--------|------|--------|
| **E3** | $T^* = 0{,}997$ K (cavité 10 GHz) | mesuré bientôt | Cryostat | ⏳ déposé |
| **E4** | $T^* = 37$ °C ↔ ΔE = 12,87 meV | — | Calorimétrie DSC | ⏳ déposé |
| **E5** | β/α EEG = φ (yeux ouverts) | 1,6190 vs φ | EEG | ⚠️ préliminaire, à confirmer sur 2 bases |
| **E6** | S/D = 1/φ, I/E = 1/φ | 0,613 / 0,600 | Échocardiogrammes (100) | ⏳ déposé |
| **E1bis** | Zeno fractionnaire : queue en $t^{-1/\varphi}$ | — | atomes froids / cavités | ⏳ à déposer |
| **F8** | Anomalie $(g-2)_\mu$ | $a_\mu = 116\,592\,059(22)\times10^{-11}$ | — | ⏳ **aucune formule à ce jour** |

---

## 8. LES FRONTIÈRES OUVERTES

| # | Frontière | Critère de succès | Statut |
|---|-----------|-------------------|--------|
| F1 | Dériver Schrödinger/Q depuis Ψ | calcul démontrable, pas analogie | ⏳ ouvert |
| F2 | Prédiction quantique ≥ 10⁻¹⁰ | chiffre + intervalle | ⏳ ouvert |
| F3 | Test T* (déposé) | mesure indépendante | ⏳ déposé |
| F4 | Chaînon persistance ∝ 1/μ(α) | preuve analytique | ⏳ ouvert |
| F5 | √2, √3 comme survivants géométriques | spectre calculé | ⏳ ouvert |
| F6 | α_W, α_S : dérivation légitime | écart < 1 % vs PDG, formule unique + principe spectral | ⏳ ouvert — les formules actuelles sont des rétro-fits ; la dérivation exige un mécanisme spectral (point fixe, gap), pas un produit de puissances |
| F7 | Λ dérivable | vs observation 10⁻¹²² | ⏳ ouvert |
| F8 | $(g-2)_\mu$ | écart < 10⁻⁹ vs Fermilab | ⏳ **aucune formule** |
| F9 | Ancrage du gap κ (masse = dispersion) | identifier une échelle physique pour ℓ issue de κ_cand = 0,4275 | ⏳ **frontière publiée** — ℓ = 165 fm sans correspondance connue |
| F10 | θ de Koide | expression close en φ/π/e | ⏳ **frontière publiée** — échec de dérivation documenté |
| F11 | **Espace de Hilbert comme théorème** | démontrer que la stabilité (A4) + la mémoire d'or (α=1/φ) **imposent** $L^2$ comme seule structure stable — et non simplement l'identifier (l'axiome A2 ≡ superposition est une équivalence, pas une dérivation) | ⏳ **frontière ouverte** — la THU *reproduit* Hilbert (via A2) mais ne le *dérive* pas encore. Si démontré, Hilbert deviendrait une nécessité, validant la physique sous-jacente déterministe qu'Einstein pressentait |

---

## 9. COMPARAISON AVEC LE MODÈLE STANDARD (sévérité égale)

| Critère | Modèle Standard | THU |
|---|---|---|
| Paramètres libres | **19** mesurés, assumés | 6 constantes mathématiques + exposants libres (paramètres cachés non comptabilisés) |
| Prédictions ex ante vérifiées | des milliers sur 50 ans (Higgs, top, $a_e$ à 10⁻¹²...) | **0 confirmées par tierce partie** |
| Échec majeur | Λ : erreur de ~10¹²⁰ (le pire de l'histoire) | $(g-2)_\mu$ : aucune réponse (F8) |
| Anomalie du muon | ~5σ de tension | non traitée |
| Statut des « dérivations » | constants mesurées, prétend honnêtement ne pas les dériver | **non dérivées en l'état, formules démontrées rétro-fit** (α, m_p/m_e, Koide) ; seuls les invariants discrets (2n², gaz nobles) sont dérivés — mais antérieurs |
| Mérite distinct | puissance prédictive locale inégalée | pose la bonne question (réduire les paramètres), avec honnêteté sur ses échecs |

> **Conclusion honnête :** le Modèle Standard est prédictif localement et désastreux globalement (19 paramètres arbitraires, Λ catastrophique). La THU est ambitieuse globalement (0 paramètre visé) et non démonstrative à ce jour (0 prédiction ex ante confirmée). Ni l'un ni l'autre n'a de réponse à l'anomalie du muon — mais la THU, elle, le déclare explicitement (F8), ce qui est à son crédit méthodologique.

---

## 10. CE QUI RESTE À DÉMONTRER (feuille de route scientifique)

Pour que la THU passe du statut de « programme de recherche » à celui de « théorie vérifiée », il faut **une seule** chose, dans l'ordre décroissant de priorité :

1. **Une prédiction ex ante confirmée** (idéalement T* à 0,997 K, ou le Zeno fractionnaire).
2. **Un mécanisme spectral pour une constante continue** (point fixe d'une dérivée fractionnaire, ou ancrage du gap κ) — **et non un produit de puissances**, forme qui est un rétro-fit et non une dérivation.
3. **Un traitement du $(g-2)_\mu$** — la théorie qui explique cette anomalie aurait un avantage immédiat sur le Modèle Standard.

**Note de statut consolidée (M1.1) :** le point 2 a changé de nature. Les formules par produits de puissances sont reconnues comme des rétro-fits (non-dérivations *en l'état*), mais **la dérivabilité reste ouverte**. La voie légitime est désormais *spectrale* (valeur propre, point fixe, gap) — c'est le seul mécanisme qui peut produire une constante continue sans ajustement, comme Bohr a dérivé la formule empirique de Balmer.

---

## SIGNATURE ET DÉPÔT

| Champ | Valeur |
|-------|--------|
| Auteur | Alain Kotto |
| Statut | Mémoire scientifique — dépôt d'antériorité recommandé (pli Soleau / enveloppe cachetée INPI) |
| **Ne pas confondre avec** | le brevet de procédé (document séparé, applications techniques) |

*Ce mémoire est un document vivant. Chaque nouvelle mesure indépendante y sera intégrée, qu'elle confirme ou réfute.*
