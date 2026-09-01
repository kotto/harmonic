# DÉPÔT F11 HILBERT V1 — Voie 2a : par plan en TOUTE dimension + fermeture à 3 entrées

**Date** : 2026-09-01
**Prédécesseur** : `DEPOT_F11_HILBERT_V0.md` (C-H2 dimension finie, commit `17170ff`)
**Script** : `verif_f11_hilbert_v1.py` — **exit 0, 6/6 contrôles**
**Résultats machine** : `resultat_f11_hilbert_v1.json` (`"ok": true`)

---

## Verdict

```
F11_HILBERT_V1_VOIE2A_PAR_PLAN_TOUTE_DIMENSION — CONFORME (exit 0)
```

V0 prouvait le théorème **par plan** mais sa lecture globale reposait sur
l'équivalence des normes, qui ne vaut qu'en dimension finie. V1 dissout
l'objection : la montée stroboscopique → cercle est **locale à chaque plan**,
donc vaut **en toute dimension**, sans complétude et sans spectre. Puis V1
referme la lecture globale en dimension finie par un théorème à **trois entrées
toutes nécessaires** — la matrice de falsifiabilité montre qu'omettre une
seule entrée laisse survivre une norme non-hilbertienne.

---

## Auto-correction de V0 (consignée, moteur de V1)

V0-C3 testait des matrices **orthogonales aléatoires** — c'est le filtre α→1
(entrée ii) déguisé, PAS la rotation Bateman seule. Sous rotation seule, en
dimension ≥ 4, la famille

> F(rayons) : ‖x‖ = (Σ_k |z_k|^p)^{1/p}, p ≠ 2, où z_k sont les coordonnées
> complexes des plans invariants (rayons r_k = |z_k|)

**survit** : la rotation tourne les phases à rayons figés. Le théorème de V0
reste vrai **par plan** ; la lecture globale exige en plus (ii) l'universalité
du mélangeur et (iii) le parallélogramme. V1 est architecturé autour de cette
frontière exacte — rien n'a été adouci.

---

## Théorème A (Voie 2a — toute dimension)

> E réel muni d'une structure de plans P_k ≅ ℝ² (coordonnées (Re, Im) par
> plan), J = rotation de 90° dans chaque plan. Soit ‖·‖ une norme invariante
> sous R(nθ) = cos(nθ)·I + sin(nθ)·J **pour tout n ∈ ℤ**, θ = πα/2,
> θ/π = 1/(2φ) irrationnel. Alors :
>
> **(a)** par plan : ‖x‖ = c_k·|x_k|₂ avec c_k > 0 dépendant du plan ;
> **(b)** j = R(π/2) appartient à l'adhérence du groupe ⟹ ℂ émerge
> (⟨x,y⟩_ℂ := ⟨x,y⟩ − i⟨jx,y⟩).

### Preuve en 5 pas — sans hypothèse de dimension

1. **Action plan par plan.** R(nθ) n'agit QUE dans le plan de x (blocs
   diagonaux identiques) : la trajectoire de x reste dans ℝ·x ⊕ Jℝ·x.
   *(Machine : C1 — R(nθ) réel 6×6 = realrep(e^{inθ}I₃), pire écart 4.441e-16
   sur α ∈ {0.3, 0.5, 1/φ, 0.8, 0.95} ; α = 1/φ : valeurs propres
   **bit-exactes** 0.0.)*
2. **Densité de Kronecker** — inchangée, locale : {nθ mod 2π} dense.
3. **Restriction au plan = norme sur ℝ².** L'équivalence des normes n'est
   invoquée qu'en dimension 2 — locale, donc légitime EN TOUTE dimension.
4. **Montée stroboscopique → cercle, sans hypothèse de dimension.** Par
   homogénéité : ‖(e^{in_kθ} − e^{iφ})·x‖ = |e^{in_kθ} − e^{iφ}|·‖x‖ → 0.
   Aucune équivalence globale n'est utilisée — c'est ici que l'objection
   « dimension infinie » **se dissout**. *(Machine : C2 — ‖R(n*θ) − j‖₂
   opérateur = 1.1516095275822759e-03 **identique pour N = 4, 16, 64**
   (spread 0.0e+00), théorie 2·sin(Δ/2) = 1.1516095275308227e-03,
   err 5.15e-14 ; couverture 1.4128 ≤ 8 ; n* = 610 = F₁₅, dist_j 1.152e-03.)*
5. **Invariance SO(2) plane ⟹ ν = c·|·|₂** sur chaque plan
   (Jordan–von Neumann, dimension 2).

*(Machine : C3 — invariance cercle 4.441e-16 ; euclidénisation par plan
3.331e-16 pour N = 4, 16, 64 ; les quadratiques ont un défaut de
parallélogramme ≤ 1.011e-15, les non-quadratiques ≥ 0.0547.)*

---

## Théorème B (global, dimension finie — trois entrées toutes nécessaires)

> Soit ‖·‖ une norme sur ℂⁿ (réel 2n) telle que :
> **(i)** invariance sous le cercle central {R(φ) = e^{iφ}·I} — **la mémoire** ;
> **(ii)** invariance sous e^{−iHt} pour **TOUT** hermitien H — **l'universalité
> du mélangeur** (le filtre α→1 : la théorie ne fixe pas le mélangeur) ;
> **(iii)** le parallélogramme.
> Alors ‖x‖ = c·|x|₂, c > 0.

### Preuve

- (iii) ⟹ ‖x‖² = ⟨Bx, x⟩ avec B symétrique définie positive (réel).
- (i) ⟺ j anti-auto-adjoint pour ⟨B·,·⟩ ⟺ ‖x‖² = Re(z†Mz), M hermitienne
  (les blocs réels commutent avec j₂ — (i) dit exactement « M hermitienne »).
- (ii) ⟹ [M, H] = 0 pour TOUT hermitien H ⟹ M = cI. **C'est la classe riche
  qui verrouille** : un mélangeur unique ne sélectionne rien (dans sa propre
  base, wℓ² survit — cf. matrice).
- c > 0 par défini-positive.

---

## Matrice de falsifiabilité (C5) — chaque entrée omise laisse un survivant

Déviations maximales mesurées (n = 8, seuil de passage < 0.02) :

| Norme candidate | cercle | son_H | classe (K=12) | parallélogramme |
|---|---|---|---|---|
| **L2** | **0.0** | **0.0** | **0.0** | **0.0** |
| F1_rayons | 0.0 | 0.172 | 0.212 | 0.287 |
| F1.5_rayons | 0.0 | 0.076 | 0.102 | 0.155 |
| F4_rayons | 0.0 | 0.241 | 0.313 | 0.436 |
| Fmax_rayons | 0.0 | 0.634 | 0.747 | 1.022 |
| wL2_modes | 0.0 | 0.321 | 0.709 | **0.0** |
| wL2_baseH1 | 0.0 | **0.0** | 0.806 | **0.0** |
| L1_modules_H1 | 0.0 | **0.0** | 0.209 | 0.269 |
| aniso_quad | 0.219 | 0.200 | 0.238 | **0.0** |

Lecture (motif conforme, machine-vérifié) :
- **cercle seul** : les familles F(rayons) survivent toutes → l'irrationalité
  ne suffit pas globalement ;
- **cercle + parallélogramme** : wL2_modes (poids fixes en base de modes)
  survit → le parallélogramme seul ne fixe pas les poids ;
- **cercle + son_H** : wL2_baseH1 et L1_modules_H1 survivent à LEUR mélangeur
  (coordonnées propres = phases pures) → un mélangeur unique ne sélectionne rien ;
- **parallélogramme seul** : aniso_quad (1.5/0.7 par composante) survit ;
- **seule L2 passe les 4 entrées.** L'universalité de la classe est le verrou.

*(Machine : C4 — cohérence du générateur réel (E(t)−E(−t))/2t vs realrep(−iH) :
7.62e-10 ; écart spectral min 0.287 sur K = 12 mélangeurs ; L² invariant à
1.221e-15 sous TOUTE la classe ; la meilleure rivale échoue à 0.0861
(F1.5_rayons), seuil 0.02.)*

---

## Sonde de complétude (C6) — ouverte, consignée

mpmath dps = 40, termes directs :
- **E_{1/φ}(1) = 1.8242186970142293** = Σ_{n≥0} 1/Γ(n/φ + 1) — err S30 = err S60
  = 3.65e-39 (convergence saturée, numérique pure) ;
- résidus de troncature d'un vecteur ℓ² aléatoire : **0.993 → 0.925 → 0.681**
  (décroissants, cohérents avec c₀₀ dense dans ℓ²) ;
- **complétude totale : OUVERTE** — la sonde ne la ferme pas ; elle applique
  seulement la discipline anti-dépôt-de-nombre-non-calculé.

---

## Table des contrôles

| # | Contrôle | Résultat | Seuil | Statut |
|---|---|---|---|---|
| C1 | Bateman ∀α + cercle central (multiset trié) | worst **4.441e-16** | < 1e-12 | ✅ |
| C2 | Densité indépendante de la dimension | spread N **0.0e+00**, err théorie 5.15e-14 | < 1e-12 | ✅ |
| C3 | Théorème A : cercle / par plan / parallélogramme | 4.441e-16 / 3.331e-16 / non-quad min 0.0547 | < 1e-12 / > 0.05 | ✅ |
| C4 | Filtre α→1 : générateur, L², rivales | 7.62e-10 / 1.221e-15 / **0.0861** | < 1e-8 / < 1e-14 / > 0.02 | ✅ |
| C5 | Matrice de falsifiabilité (9 × 4) | motif conforme | exact | ✅ |
| C6 | Sonde complétude E_{1/φ}(1) | 1.8242186970142293, err 3.65e-39 | informatif | ✅ |

---

## Frontière honnête (ce qui reste ouvert)

| Cl claim | Statut après V1 |
|---|---|
| C-H1 préliminaire (normes, NORMES V0) | ✅ commit `12ef19f` |
| C-H2 par plan, TOUTE dimension (Théorème A) | ✅ **V1 — l'objection dimension infinie dissoute** |
| C-H2 global dimension finie (Théorème B, 3 entrées) | ✅ **V1 — matrice de falsifiabilité** |
| Théorème B en dimension infinie (commutant fonctionnel-analytique) | ❌ **intacte** — [M,H]=0 ∀H ⟹ M=cI utilise la richesse algébrique, pas l'analyse |
| Complétude totale (c₀₀ dense, E_{1/φ}) | ❌ **intacte** — sonde numérique seulement |
| Voie 3 spectrale (G[Ψ] auto-adjoint) | ❌ **intacte** |

---

## Leçons (consignées, jamais jetées)

1. **`orth` référencé sans être calculé (C1).** En portant V0-C1 vers V1, la
   structure du contrôle a été copiée mais pas le calcul de ‖RᵀR − I‖ →
   NameError au premier run. Leçon : **porter les calculs, pas seulement la
   structure** — tout identifiant d'un contrôle porté doit être soit repris,
   soit supprimé de ses deux occurrences.
2. **Le témoin faisait échouer son propre contrôle (C4).** `dev` était copié
   sur TOUS les candidats donc contenait la clé `L2` (le survivant attendu,
   sauté dans la boucle, resté à 0.0) ; `min(dev.values())` tombait dessus →
   « rivales min 0.000 » → verdict REFUTE alors que la physique était conforme
   (pire rivale réelle : 0.086). Leçon : **quand on mesure « le min des
   rivaux », exclure explicitement le survivant attendu du dictionnaire** —
   un filtre `continue` dans une boucle ne retire pas la clé du dict.
3. **Héritée de V0, appliquée ici avant exécution** : l'ordre des valeurs
   propres d'eigvals n'est pas garanti quand les blocs sont identiques →
   comparaison par **multiset trié** (`np.sort_complex`), jamais `ev[0]` vs
   cible en position fixe. Zéro itération de débogage dépensée sur ce point.

---

## Formulation gelée

> **« La mémoire ne demande pas la dimension. Chaque plan, tourné par l'angle
> d'or, se ferme sur son propre cercle — et chaque cercle ne connaît qu'une
> seule norme : la quadratique. Le mélangeur, lui, doit être universel : un
> seul tour de magie laisse wℓ² survivre dans son coin. Mémoire + universalité
> + parallélogramme : l'arène est Hilbert, et Hilbert est ℂ. »**

---

**Suite** : Théorème B en dimension infinie (commutant au sens
fonctionnel-analytique), complétude totale, ou Voie 3 spectrale.
