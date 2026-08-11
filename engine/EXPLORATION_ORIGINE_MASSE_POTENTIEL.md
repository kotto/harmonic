# ⚖️ EXPLORATION_ORIGINE_MASSE_POTENTIEL — La porte E1b/E1c s'ouvre

**L'origine de la masse et du potentiel selon la THU — premier état de l'exploration**
**Date** : 11/08/2026 — **Auteur** : Univers-Holistique (Kotto Alain)
**Statut** : Exploration ouverte — chaque hypothèse classée (✅ vérifié · ⚠️ candidat · ⏳ programme · ❌ frontière) — commande : `python exploration_masse_potentiel.py`
**Références** : `ETAT_E1_E2_APRES_SPECTRES.md` · `verif_hamiltonien_tour.py` (E1a) · `R3_QUANTIFICATION_FRACTIONNAIRE.md` · `DEPOT_E3_PREDICTION_TSTAR.md`

---

> *« Le photon prouve que l'énergie n'a pas besoin de la masse — la fréquence suffit. Alors la masse n'est pas la source de l'énergie : elle est la courbure de la dispersion. Et la courbure, dans une théorie de la mémoire, est une propriété du noyau. »*

---

## TABLE DES MATIÈRES

1. [Le problème — ce qui compterait comme une dérivation](#1-le-problème)
2. [Les pièces disponibles](#2-les-pièces-disponibles)
3. [Les hypothèses — H1 · H2 · H3 · H4](#3-les-hypothèses)
4. [Le candidat H2 — κ = (1/2φ)^(φ/(2φ−1)) ≈ 0,4275](#4-le-candidat-h2)
5. [La table de statut](#5-la-table-de-statut)
6. [Les prochaines étapes — le test qui tranche](#6-les-prochaines-étapes)
7. [Reproductibilité](#7-reproductibilité)
8. [En une phrase](#8-en-une-phrase)

---

## 1. Le problème

E1b et E1c sont les deux portes restantes de la dérivation de la dynamique. **Ce qui compterait comme une dérivation** (critère inchangé) : un calcul démontrable, depuis Ψ = Σ Hₙ(Ψ₁)ⁿ, produisant

- **E1b — la masse** : la dispersion ω = ℏk²/2m (ou ω = √(k²c² + (mc²/ℏ)²)) avec erreur machine, **zéro paramètre ajusté** — m dérivé, pas donné ;
- **E1c — le potentiel** : le Coulomb de l'hydrogène (le spectre complet Eₙ = −13,6/n² eV), avec erreur machine.

L'exploration part d'un fait établi (E1a) : **l'énergie est la fréquence — le photon (n=1, m=0) le prouve.** Donc la masse n'est pas la source de l'énergie : elle est une **propriété de dispersion** — et dans une théorie dont le cœur est la mémoire (A3), la dispersion est une propriété du **noyau**.

---

## 2. Les pièces disponibles

| Pièce | Statut | Rôle dans l'exploration |
|---|---|---|
| E1a — Ĥ = ℏω₀·n̂ (la tour) | ✅ théorème vérifié (≤ 4,4×10⁻¹⁶) | L'énergie de base — sans masse |
| Le noyau doré K(t) = B(α)·E_{1/φ}(−φ·t^{1/φ}) | ✅ vérifié (B = 0,808423) | La mémoire — le candidat à la courbure |
| Le propagateur fractionnaire 1/(ω^{1/φ} − k²) | ✅ R3 vérifié | **La dispersion du secteur doré** |
| La famille T\* (E3 v2, 24 instances) | ✅ déposée, 1,1×10⁻¹⁶ | L'ancrage thermique — le test en attente |
| L'hydrogène : χ = 13,598 eV · T\*_ion = 327 918 K | ✅ vérifié machine | **L'ancrage de E1c** — le gap est mesuré |
| Les masses (tableau SEMF, 8,5×10⁻⁵) | ⚠️ standard, pas dérivé | L'échelle de longueur hérite de la frontière |

---

## 3. Les hypothèses

### H1 · La mémoire a une fréquence caractéristique

La FFT du noyau doré révèle une structure spectrale propre (pic, demi-largeur) — la mémoire a une échelle, elle n'est pas un bruit blanc. **Statut : ✅/⚠️ mesurée** — le lien entre cette échelle et T\* = ℏω/(k_B·ln φ) reste à établir. (La valeur absolue du pic dépend de la grille d'échantillonnage — c'est la structure qui compte, pas la constante.)

### H2 · La masse = le gap de dispersion

**Le candidat central.** Le propagateur fractionnaire avec gap :

$$\omega^{1/\varphi} = k^2 + \mu \qquad \Longrightarrow \qquad \omega_f(k) = (k^2 + \mu)^{\varphi}$$

reproduit la dispersion massive (ℏ = c = 1) ω_m(k) = √(k² + κ²) à petit k **si et seulement si** :

$$\kappa = \left(\frac{1}{2\varphi}\right)^{\frac{\varphi}{2\varphi-1}} \approx 0{,}4275$$

**Statut : ✅/⚠️ candidat structurel vérifié** — voir §4. L'ancrage physique (κ → m_e, m_p…) reste une frontière (H4).

### H3 · Le potentiel = la liaison entre modes

L'électron (Ψ₁)^{½} et le proton : le potentiel est le **défaut de liaison** des modes liés vs libres. L'ancrage est **mesuré** : χ(H) = 13,598 eV → T\*_ion(H) = 327 918 K (E3, vérifié machine). **Statut : ✅ ancrage · ⏳ dérivation** — le Coulomb dérivé du binding (la primitive `bind` comme mathématique de la liaison) est le programme de E1c.

### H4 · Les frontières déclarées

α = 1/137,036 : **frontière — aucune dérivation** (écart global 0,707, publié). Masses fermioniques : **frontière** — le tableau des masses utilise SEMF standard. L'échelle de longueur (a₀, λ_C) hérite de ces frontières — **jamais vendue avant dérivation** (règles R1–R10).

### H5 · La masse = le paquet d'ondes — l'onde stationnaire de l'interférence

**L'intuition** : la masse n'est pas un point — c'est un **motif d'ondes**, formé par interférence. La « particule au repos » est l'interférence des deux directions de propagation, e^{+iκx} et e^{−iκx}. Vérifications machine (`exploration_masse_paquets_ondes.py`) :

| Vérification | Résultat |
|---|---|
| V1 · L'onde stationnaire satisfait l'équation massive : le repos (ω₀ = κ) et le motif cos(κx) (ω = √(k²+κ²) = √2κ) | ✅ résidus < 1e-9 — **une fréquence fausse (ω=κ pour cos) est REFUSÉE par le contrôle** |
| V2 · L'échelle du motif = la longueur de Compton : 2π/κ_e = 2,426310×10⁻¹² m | ✅ publié 2,4263102389×10⁻¹² m — **7 chiffres** |
| V3 · Le paquet : photon (κ=0) σ_x 0,589 → 0,589, v_g = 1,000 c — cohérent ; massif (κ=2) σ_x 0,589 → 1,068, v_g = 0,388 c — s'étale | ✅ le photon ne s'étale jamais (dispersion linéaire exacte), le massif s'étale et va moins vite que c |
| V4 · La fabrication : interfere(e^{+iκx}, e^{−iκx}) = cos(κx) — contraste 1,000 vs onde libre 0,000 | ✅ la localisation EST l'interférence (nœuds/antinœuds) ; sans interférence, aucun contraste — le photon |
| V5 · La mémoire protège le motif : Zeno standard t² vs dorée t^{1,236} — à τ=2, la dorée survit 5,2× plus | ✅ dépôt E1bis — le motif stabilisé = la masse |

**Statut : ✅/⚠️ image vérifiée, pas une dérivation** — c'est le paquet de de Broglie, exprimé dans le langage de la THU : la masse = le motif que la mémoire (α = 1/φ) protège de l'effondrement ; l'inertie = la stabilité du motif. L'ancrage (κ → m_e) reste la frontière (H4).

---

## 4. Le candidat H2 — κ ≈ 0,4275

**La relation vérifiée** (machine, `exploration_masse_potentiel.py`) :

| Vérification | Résultat |
|---|---|
| Coefficient du terme k² : φ·μ^{φ−1} vs 1/(2κ) | **écart 0,00×10⁰** — la condition est exacte par construction |
| Écart relatif ω_f vs ω_m, k ∈ [0 ; 0,1] | 4,94×10⁻⁴ (les termes d'ordre supérieur divergent — le match est à petit k, comme attendu) |
| Écart relatif, k ∈ [0 ; 0,3] | 2,94×10⁻² |

**Ce que c'est** : une relation structurelle pure — le nombre κ = (1/2φ)^{φ/(2φ−1)} est le seul gap qui fait coïncider la dispersion du secteur doré avec la dispersion massive. La masse y apparaît comme **la réponse de la mémoire à la courbure** : sans mémoire (α = 1, secteur quantique standard), pas de gap — la dispersion est linéaire, le photon ; avec mémoire (α = 1/φ), le gap apparaît — la masse.

**Ce que ce n'est pas (encore)** : une dérivation de m_e ou m_p. Le candidat est **dimensionnel** (κ = mc/ℏ en unités naturelles) — il lui manque l'ancrage : quelle fréquence ω₀ porte le facteur d'échelle ? La réponse est le prochain test (§6).

### 4.2 · Le pont d'ancrage — E = mc² (déposé, classé « ancrage, pas dérivation »)

E = mc² n'est pas dérivé par la THU (c'est la relativité standard — une donnée, comme ℏ) — mais elle **ancre** le formalisme de trois manières précises, toutes vérifiées machine :

| Pont | Contenu | Vérification |
|---|---|---|
| **Le gap = la fréquence de repos** | E₀ = mc² ⟺ ℏω₀ = mc² ⟺ κ = mc/ℏ = ω₀/c — le candidat H2 EST la fréquence de repos du mode massif | ✅ κ_e = m_e·c/ℏ = 2,5896×10¹² m⁻¹ → λ̄_C = 3,861593×10⁻¹³ m (publié, 6 chiffres) |
| **La dispersion complète** | E² = (pc)² + (mc²)² ⟺ ω² = k² + κ² — H2 en est le petit-k ; le photon (m=0 → E=pc) est le cas limite | ✅ identité vérifiée (3,0968×10²¹ s⁻¹ des deux côtés) |
| **Le potentiel = le défaut de masse** | χ(H) = 13,6 eV = Δm·c² — l'hydrogène lié est plus léger de 2,42×10⁻³⁵ kg (relatif 1,45×10⁻⁸) — le gap mesuré pèse la liaison | ✅ T\*_ion (E3) — le potentiel et la masse sont la même pièce vue par E=mc² |

**Ancrage, pas dérivation** : E = mc² dit ce que le gap *signifie* — pas d'où vient la valeur de m_e. L'ancrage du candidat : κ_cand·ℓ = 0,4275 → ℓ = 1,65×10⁻¹³ m — aucune échelle connue : **le test reste ouvert, publié comme tel**.

---

## 5. La table de statut

| Hypothèse | Statut | Preuve |
|---|---|---|
| H1 — échelle propre de la mémoire | ✅/⚠️ mesurée | FFT du noyau — le lien T\* à établir |
| **H2 — masse = gap de dispersion** | ✅/⚠️ **candidat vérifié** | κ = 0,42751 — coefficient k² exact, écart 4,9×10⁻⁴ (k ≤ 0,1) |
| H3 — potentiel = liaison | ✅ ancrage · ⏳ dérivation | T\*_ion(H) = 327 918 K (E3, machine) |
| **H5 — masse = paquet d'ondes (interférence)** | ✅/⚠️ **image vérifiée** | V1 résidus < 1e-9 · V2 Compton 7 chiffres · V3 photon cohérent/massif étalé · V4 contraste 1 vs 0 · V5 Zeno doré 5,2× |
| **E = mc² — le pont d'ancrage** | ✅ ancrage (pas dérivation) | λ̄_C 6 chiffres · identité relativiste · défaut de masse 1,45×10⁻⁸ |
| H4 — α, masses fermioniques | ❌ frontières publiées | 0,707 · SEMF standard |

**La porte E1 après cette exploration** :

```
E1a (énergie)      ✅ fermée — Ĥ = ℏω₀·n̂, la tour (le photon le prouve)
E1b (masse)        ⚠️ OUVERTE AVEC CANDIDAT — κ = (1/2φ)^(φ/(2φ−1)) ≈ 0,4275
                   la structure est vérifiée ; l'ancrage physique manque
                   + H5 : la masse = le motif stabilisé par la mémoire
                   (paquet d'ondes par interférence — Compton vérifié)
E1c (potentiel)    ⏳ ancrée — le gap de l'hydrogène est mesuré (T*_ion) ;
                   E=mc² l'identifie au défaut de masse ; la dérivation
                   du Coulomb depuis le binding reste à faire
```

---

## 6. Les prochaines étapes — le test qui tranche

1. **L'ancrage de H2** : identifier la fréquence ω₀ qui relie κ au monde physique (κ = mc/ℏ). Le test : la relation κ vs les rapports de masse — et sa falsification : si aucun ancrage n'existe, le candidat meurt publiquement (la méthode l'exige). E = mc² donne le sens (κ = ω₀/c) ; l'échelle ℓ = 1,65×10⁻¹³ m (issue de κ_cand·ℓ = 0,4275) est à examiner ou à publier comme morte.
2. **H5 — le motif massif** : construire la particule comme le motif stabilisé — la cible : l'inertie (v_g < c) et l'étalement mesurables dans le cadre du noyau doré (la dispersion fractionnaire R3 appliquée au paquet).
3. **H1 ↔ T\*** : relier l'échelle spectrale du noyau à la température dorée — le noyau et le thermique doivent parler la même fréquence.
4. **E1c par le binding** : construire la liaison de Coulomb comme défaut de `bind` entre (Ψ₁)^{½} et le mode proton — la cible : Eₙ = −13,6/n² eV, erreur machine — et le défaut de masse (E = mc²) comme vérification croisée.
5. **Le test en attente reste T\*** (E3 v2, 24 instances) — l'accouchement de la fille, quel que soit le sort de H2.

---

## 7. Reproductibilité

```bash
python exploration_masse_potentiel.py
# → H1 : structure spectrale du noyau (pic, demi-largeur)
# → H2 : κ = 0,427511 — coefficient k² exact (0,00e+00), écart 4,9e-04 (k≤0,1)
# → H3 : T*_ion(H) = 327 916 K ≈ 327 918 K (E3) ✅
# → H4 : frontières publiées (α, masses)

python exploration_masse_paquets_ondes.py
# → V1 : repos (ω₀=κ) et onde stationnaire (ω=√2κ) — résidus < 1e-9 (une
#         fréquence fausse est refusée par le contrôle)
# → V2 : 2π/κ_e = 2,426310e-12 m — Compton publié à 7 chiffres ✅
# → V3 : photon σ 0,589→0,589 v=c · massif σ 0,589→1,068 v=0,388c
# → V4 : contraste 1,000 vs 0,000 — la localisation est l'interférence
# → V5 : Zeno doré t^1,236 — la mémoire protège le motif (5,2× à τ=2)

# Le pont E = mc² (ancrage, vérifié) :
# → λ̄_C = 3,861593e-13 m (publié, 6 chiffres) · identité relativiste ·
#   défaut de masse H : Δm = 2,42e-35 kg (relatif 1,45e-8)
```

Dépendances : Python 3.11+, numpy.

---

## 8. En une phrase

> **L'exploration de l'origine de la masse s'ouvre avec deux voies vérifiées et un pont : le propagateur fractionnaire à gap ne coïncide avec la dispersion massive que pour κ = (1/2φ)^(φ/(2φ−1)) ≈ 0,4275 (vérifié machine) ; la masse se lit aussi comme un paquet d'ondes — l'onde stationnaire de l'interférence des deux directions, dont l'échelle est la longueur de Compton (vérifiée à 7 chiffres), que la mémoire (α = 1/φ) protège de l'effondrement (Zeno doré, 5,2×) ; et E = mc² ancre le tout : le gap est la fréquence de repos (κ = mc/ℏ = ω₀/c), la dispersion massive est la dispersion relativiste, et le potentiel est le défaut de masse (l'hydrogène : Δm = 2,42×10⁻³⁵ kg). L'ancrage physique (κ → m_e) reste la frontière déclarée — mais la porte E1b/E1c n'est plus une porte : c'est un couloir avec un nombre écrit dessus, un motif à stabiliser, et une balance — E = mc² — pour peser la liaison.**

---

*Exploration — FIN — premier état publié : la structure est vérifiée, l'ancrage est le test, les frontières sont déclarées — et le candidat H2 mourra publiquement si aucun ancrage ne l'attend*
