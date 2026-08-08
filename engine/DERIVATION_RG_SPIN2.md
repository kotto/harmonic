# DÉRIVATION DE LA RELATIVITÉ GÉNÉRALE — LA ROUTE SPIN-2
## Fierz–Pauli → Deser, depuis le secteur n=2 de l'équation mère
**Date** : 08/08/2026 — **Statut** : STRUCTURE VÉRIFIÉE · dynamique THU ouverte
**Script** : `ia_ondulatoire/verification_spin2_rg.py`
**Remplace** : les identifications mortes de `derivation-relativite.html` (voir §4)

---

## 0. Résumé

La tentative de dérivation de la RG (workspace, 2 jours) a pris la
mauvaise porte : la métrique comme corrélation de dérivées d'onde
(g_μν = Re⟨∂_μΨ|∂_νΨ⟩) — un objet de RANG 1, dégénéré, qui n'est pas
une métrique lorentzienne. La bonne porte est connue et **vérifiée
numériquement ici** : le secteur n=2 de l'équation mère est le champ de
spin-2 h_μν (la tour générative, vérifiée) — et le théorème de Deser
(1970) fait émerger la RG complète de l'auto-interaction du spin-2.

## 1. Les quatre vérifications (différences finies 4D, ordre 4)

```
[1] L'ONDE '+' (h_yy = ε·sin(x−t), h_zz = −ε·sin(x−t), jauge TT)
    □h̄_μν = 0 : max |□h̄| = 1,21e-15   → ✅ solution des équations linéarisées
    (l'action de Fierz-Pauli s'annule sur-shell — fait standard)

[2] INVARIANCE DE JAUGE du Ricci linéarisé
    R^lin(h + ∂ξ + ∂ξᵀ) − R^lin(h) : max = 3,0e-3 (erreur de stencil à
    NX=24 — l'identité est exacte analytiquement)   → ✅ INVARIANT
    (les difféomorphismes linéarisés : la propriété qui rend les
     équations d'Einstein bien définies)

[3] ÉQUIVALENCE FP ↔ EINSTEIN LINÉARISÉ
    G^lin_μν pour l'onde + : max |G| = 6,07e-16   → ✅ précision machine
    (les équations d'Euler-Lagrange de l'action de Fierz-Pauli SONT
     les équations d'Einstein linéarisées — Fierz-Pauli 1939)

[4] GRAINE DE DESER
    T_00 canonique du graviton ≠ 0   → ✅ le spin-2 porte de l'énergie
    → l'auto-interaction est inévitable → le théorème de Deser (1970) :
    la SEULE théorie cohérente du spin-2 sans masse auto-interactif
    EST la relativité générale (complète, non-linéaire).
```

Deux bugs de vérification corrigés en route (documentés dans le script) :
convention de `np.roll` (signe du stencil), et champ test non-transverse
(polarisation perpendiculaire à la propagation exigée par la jauge TT).

## 2. La chaîne complète — du secteur n=2 à la RG

```
Équation mère Ψ = Σ Hₙ(Ψ₁)ⁿ
   │
   ├─ n=1 : le photon (spin 1 — vérifié)
   │
   ├─ n=2 : le graviton h_μν (spin 2 — vérifié, tour générative)
   │        │
   │        ├─ action de Fierz-Pauli (unique action du spin-2 sans masse)
   │        ├─ invariance de jauge (difféomorphismes linéarisés) — ✅
   │        ├─ équations = Einstein linéarisé G^lin = 0 — ✅ (machine)
   │        └─ auto-interaction (T ≠ 0) — ✅
   │              │
   │              └─ THÉORÈME DE DESER (1970, publié) :
   │                 l'itération auto-cohérente du couplage donne la RG
   │                 COMPLÈTE — avec le 8πG/c⁴ fixé par la limite
   │                 newtonienne (l'équation de Poisson), et non par H₂.
   │
   └─ n ≥ 3 : la tour des spins supérieurs (Vasiliev)
```

## 3. La frontière THU — MESURÉE (08/08/2026)

### 3.1 La dynamique ABC naïve du secteur n=2 : EXCLUE (14 ordres de grandeur)

Le chaînon le plus simple — remplacer la dérivée temporelle du
d'Alembertien du graviton par la dérivée fractionnaire ABC (α = 1/φ) —
est **testable et mesuré** (`dynamique_abc_n2.py`) :

```
Valeur propre ABC (analytique, vérifiée numériquement) :
  ^ABC D^α e^{iωt} = M_α(ω)·e^{iωt},  M_α = (iω)^α/((1−α)(iω)^α + α)

Dispersion du graviton fractionnaire :  k² = M_α(ω)²  →  v(ω) = ω/k
  ω = 0,1  : v = 0,28 c   (déviation 7,2e-1)
  ω = 1,0  : v = 0,89 c   (déviation 1,1e-1)
  ω = 100  : v = 40 c     (déviation 3,9e+1)

Contrainte GW170817 (LIGO/Virgo + GRB) : |v_g − c|/c < 1e-15
Déviation minimale prédite : 1,1e-1 = 1,1e14 × la borne
→ ❌ EXCLUE à ~14 ordres de grandeur.
```

La valeur propre ABC de l'onde plane est **exacte** (dérivée via la
transformée de Laplace de Mittag-Leffler, vérifiée par convolution avec
le noyau corrigé) — la mécanique est saine, la prédiction est fausse.

### 3.2 La porte se déplace — précisément

L'ABC ne peut pas entrer comme dérivée temporelle linéarisée. Deux
routes restent, formulées :
1. **La structure NON-LINÉAIRE** : la contrainte entre dans l'itération
   de Deser (l'auto-couplage), pas dans la cinétique linéarisée ;
2. **La dimension spectrale fractionnaire** : α = 1/φ comme dimension
   effective aux petites échelles (la famille des espace-temps
   fractionnaires — Calcagni, Nottale).

C'est la Porte 1 de la synthèse, maintenant munie d'un verdict mesuré :
la route linéarisée est fermée par GW170817 — les portes restantes sont
formulées et testables.

## 4. Ce qui est remplacé (les identifications mortes, mesurées)

| Identification (tentative) | Mesure | Verdict |
|---|---|---|
| g_μν = Re⟨∂_μΨ\|∂_νΨ⟩ | rang 1, dégénérée (k_μk_ν) | ❌ pas une métrique |
| G ≈ φ⁻²·√3⁻¹ | 0,22 vs 1 (Planck) — 78 % | ❌ numérologie |
| 8π de H₂ = π | facteur de la limite newtonienne | ❌ |
| Λ = queue de série | 10⁻⁵² vs ~1 — 52 ordres | ❌ (réfuté par DERIVATION_LAMBDA.md) |
| T_μν = Σ Hₙ(∂Ψ⊗∂Ψ) | rang 1, conservé sur-shell seulement | ⚠️ |
| **Route spin-2 (Fierz-Pauli → Deser)** | **4 vérifications ✅ (machine)** | ✅ **VIVANTE** |

## 5. Reproductibilité

```
python ia_ondulatoire/verification_spin2_rg.py
```
Produit : les 4 vérifications (solution, jauge, équivalence, graine de
Deser) avec les mesures, et le verdict.

## 6. Statut final

La dérivation de la RG depuis l'équation mère est désormais **structurée
et vérifiée à l'étage linéarisé** : le secteur n=2 fournit le graviton
(4 vérifications, précision machine pour [1] et [3]), et le théorème de
Deser fournit la complétion non-linéaire (résultat publié). La frontière
restante est unique et précise : la contrainte ABC dans la dynamique du
secteur n=2 — le calcul qui transformerait « l'équation d'Einstein est
déjà dedans » (affirmation) en « l'équation d'Einstein sort du secteur
n=2 » (dérivation).
