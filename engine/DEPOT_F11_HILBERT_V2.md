# DÉPÔT F11 HILBERT V2 — Voie 3 spectrale : le couple déposé ferme l'arène

**Date** : 2026-09-01
**Prédécesseur** : `DEPOT_F11_HILBERT_V1.md` (Voie 2a fermée, commit `fd6476a`)
**Script** : `verif_f11_hilbert_v2.py` — **exit 0, 6/6 contrôles**
**Résultats machine** : `resultat_f11_hilbert_v2.json` (`"ok": true`)
**Cahier des charges** : `FRONTIERE_F11_HILBERT.md` §3 Voie 3 (C-H3) + §4 (clause de falsifiabilité)

---

## Verdict

```
F11_HILBERT_V2_VOIE3_SPECTRALE_COUPLE_COMMUTANT_TRIVIAL — CONFORME (exit 0)
```

V1 fermait la Voie 2a (par plan, toute dimension). V2 exécute la Voie 3 :
**déduire le théorème spectral depuis la mémoire d'or, sans postuler Hilbert** —
et teste AUSSI la clause §4 : si une structure non-hilbertienne est aussi
stable, F11 est réfutée. Le résultat tient en trois thèses :

- **T1** — le calcul fonctionnel de la mémoire d'or **est spectral** : la série
  matricielle Mittag-Leffler directe (aucune diagonalisation, aucun produit
  scalaire — anti-circularité) coïncide avec la résolution spectrale à 1.2e-15,
  et le mapping `spec(f(Ĥ)) = f(spec(Ĥ))` est vérifié sur multiset trié.
- **T2** — critère spectral d'isométrie : une arène ℓ^p survit à U(t)
  **⟺** |E_{1/φ}(iλt^{1/φ})| = 1 pour toute valeur propre. À α = 1/φ :
  **aucune** arène ne survit ; à α = 1 : **toutes** — le falsificateur §4
  réalisé, consigné.
- **T3** — le couple déposé {flot fréquentiel e^{iωt}, modulation e^{ia·kx}}
  a un **commutant trivial** (dim 1, S = cI à 5.3e-15) ⟹ la seule forme
  quadratique invariante sous les deux familles est c·Σ|x|² = **L²** —
  sans postuler Hilbert.

---

## Objets déposés (aucun réinventé — anti-circularité)

| Objet | Dépôt d'origine |
|---|---|
| noyau mémoire K̂(ω) = φ/((iω)^α + φ), α = 1/φ, K̂(0) = 1, branche principale | FORCE V1.3 O2 (verbatim jaugage V0) |
| évolution Zeno E_{1/φ}(iEt^{1/φ}/ℏ) | DEPOT_E1bis_ZENO_FRACTIONNAIRE |
| poids (iω)^α = ω^α·e^{iθ}, θ = πα/2 ≠ 0 — non-hermitien, PT brisé, système ouvert | HAMILTONIEN_ABC_THU_V0 C1/C2 |
| modulation e^{ia·kx}, a·k·L = 2πφ (la même irrationalité) | FORCE V1.3 §0 |
| flot unitaire e^{−iHt} (classe α→1) | F11 HILBERT V1 C4 |
| phase d'influence Φ₂ = seul branchement compatible | KMS DPHI ; HAMILTONIEN ABC V0 |

Aucun produit scalaire, aucune norme L², aucun postulat spectral dans les
voies directes : C1 calcule f(Ĥ) par série matricielle mpmath dps 50 brute ;
T3 déduit l'arène du commutant, il ne la postule pas.

---

## Théorème T1 — le calcul fonctionnel de la mémoire d'or est spectral

> Soit Ĥ hermitien N×N, U(t) = E_{1/φ}((i/ħ)Ĥt^{1/φ}) (ℏ = 1). Alors
> U(t) = Σ_k E_{1/φ}(iλ_k t^{1/φ})·P_k sur toute base propre de Ĥ.

**Machine (C1)** — 8 modes, λ ∈ [0.2, 3], t ∈ {0.25, 1, 2, 4} :
- voie directe : S = Σ_n (iĤt^α)ⁿ/Γ(nα+1) par récurrence matricielle mpmath
  (dps 50) — **aucune diagonalisation** ;
- voie spectrale : eigh puis E_{1/φ} scalaire sur les λ_k ;
- **concordance pire cas 1.24e-15** ;
- mapping spectral : `spec(voie directe)` vs {E_α(iλ_k t^α)} sur **multiset
  trié** (leçon V1 : jamais ev[0] vs cible en position fixe) — **2.55e-15** ;
- complétude de la base propre V·V† = I — **1.78e-15**.

Le théorème spectral n'est pas supposé : la voie directe l'*atteint* sans
le connaître, et l'écart au mapping (2.5e-15) est le prix machine exact de
l'équivalence.

## Théorème T2 — critère d'isométrie : |λ modale| = 1

> Une norme d'arène ℓ^p est invariante sous U(t) ⟺ |E_{1/φ}(iλ_k t^{1/φ})| = 1
> pour toute valeur propre λ_k de Ĥ.

**Machine (C2)** — opérateur diagonal, ‖U‖_{ℓ^p→ℓ^p} = max_k |E_α(iλ_k t^α)|
confirmé par **quatre routes indépendantes** (somme de colonnes p=1, SVD p=2,
puissance itérée sur (U†U)² p=4, max p=∞) : **écart worst 0.0e+00** (bit-exact
sur t = 0.25…4 ; ex. t=4 : ρ_modal = 0.7271476476649152 sur les 4 routes).

**Machine (C3) — le critère tranché** :
- **α = 1/φ** : déviation **0.7955117156973301 — identique dans les 4 arènes**
  (p = 1, 2, 4, ∞), car les **vecteurs de base eux-mêmes** se contractent :
  c'est |E_α(iλt^α)| − 1 nu, sans mélange. Conséquence spectrale directe de
  arg(iω)^α = θ ≠ 0 (HAMILTONIEN ABC C1) : la mémoire nue ne conserve RIEN.
- **α = 1** : U(t) = e^{iλt}, |e^{iλt}| = 1 — déviation 2.22e-16 dans toutes
  les arènes. **Falsificateur §4 réalisé et consigné** : à α = 1 la sélection
  n'existe pas. La sélection n'existe QUE parce que α = 1/φ < 1 — système
  ouvert, PT brisé.

## Théorème T3 — le couple déposé ferme l'arène (commutant trivial)

> K̂ est diagonal en FRÉQUENCE ; la modulation e^{ia·kx} est diagonale en
> POSITION. Alors :
> (a) commutant du flot fréquentiel seul : **dim N** (tous les circulants) —
> un seul opérateur ne sélectionne rien (écho de V1-C5) ;
> (b) commutant du COUPLE {e^{iωt}, e^{ia·kx}} : **dim 1**, générateur = c·I
> ⟹ la seule forme quadratique invariante sous les deux familles est
> ‖x‖² = c·Σ|x|² : **L² émerge, elle n'est pas postulée**.

**Machine (C4)** — N = 32, t₀ = 0.7 :
- dim commutant flot seul = **32** (= N, les circulants) ;
- dim commutant couple = **1** ; générateur normalisé vs I₃₂ : **5.32e-15** ;
- pas de dégénérescence accidentelle : min écart de phases flot 0.137,
  modulation 0.134 ;
- **défaut [K̂, modulation] = 1.108** — c'est la diffusion fréquentielle χ
  mesurée sur la modulation pure (FORCE V1.3 : le défaut de commutation EST χ) ;
- **[K̂, flot fréquentiel] = 7.0e-17 = 0** exactement — la mémoire choisit
  sa base, elle ne la partage pas.

**Machine (C5) — matrice de falsifiabilité** (4 normes × 4 colonnes, dev max
sur 8 vecteurs ; ✔ = dev < 1e-12) :

| norme | flot fréq. | modulation | couple | K̂ seul |
|---|---|---|---|---|
| L2 | ✔ 4.4e-16 | ✔ 2.2e-16 | ✔ 4.4e-16 | ✘ 0.614 |
| wL2_omega (poids \|K̂(ω)\|², base fréquence) | ✔ 3.3e-16 | ✘ 0.226 | ✘ 0.226 | ✘ 0.514 |
| wL2_position (poids non uniformes, base position) | ✘ 0.0158 | ✔ **0.0** | ✘ 0.0158 | ✘ 0.610 |
| generique (poids, 3ᵉ base unitaire aléatoire) | ✘ 0.0145 | ✘ 0.0160 | ✘ 0.0160 | ✘ 0.615 |

Le motif est **exact** : seule L² survit au couple. Notez wL2_position sous
modulation = **0.0 bit-exact** — la structure prédite (diagonale unitaire
dans sa propre base) se lit au bit près. K̂ seul ne laisse rien (contraction
0.614 partout — T2a en métrique). Contrastes des poids : w_ω = 16.63,
w_pos = 1.450 (témoins non dégénérés).

---

## C6 — retour physique Zeno, avec correction de théorie consignée

**1 − P(t) = c₂·t^{2/φ}·(1 + O(t^{2/φ}))**, c₂ = 2/Γ(2/φ+1) − 1/Γ(1/φ+1)².

- c₂ machine : **0.532736053147** (mpmath, sans cancellation) ;
- extraits c₂(t) : 0.532264, 0.531625, 0.530124 (t = 1e-2, 2e-2, 4e-2) ;
- **rapports d'erreurs successifs 0.42486, 0.42530 → 2^{−2α} = 0.42453**
  (machine) — conforme.

**Correction de théorie (run 2, consignée avant verdict)** : le dépôt annonçait
une correction relative O(t^{1/φ}). La machine a mesuré 0.4249 contre 0.6516
prédit — et avait raison : |E_{1/φ}(iξ)|² est **paire** en ξ (E(iξ) =
A(ξ²) + iξ·B(ξ²) ; les termes impairs de E entrent **au carré** dans |E|²),
donc 1 − P = c₂ξ² + c₄ξ⁴ + ⋯ **sans terme ξ³** : la correction relative est
O(ξ²) = O(t^{2/φ}). La théorie s'est corrigée devant le nombre — jamais
l'inverse.

---

## Leçons (4 — toutes issues des runs 1–2, exit 1 avant exit 0)

1. **Porter la récurrence, pas la forme** (C1, run 2 = 1.1e+02). `ml_matrix`
   divisait cumulativement par Γ(αn+1) : cela calcule ΣZⁿ/∏Γ(αk+1), garbage
   total. La version scalaire avait la bonne récurrence par **rapport gamma**
   Γ(α(n−1)+1)/Γ(αn+1) — c'est elle qu'il fallait transporter, pas la
   silhouette de la boucle. Toute série matricielle se teste d'abord sur ses
   trois premiers termes.
2. **Puissance itérée : compter les racines** (C2, run 2 = 2.0e-01). L'itération
   sur (U†U)² converge vers σ⁴, pas σ : une racine manquante et la route p=4
   « confirme » σ². Après fix : écart **0.0e+00** bit-exact.
3. **Un témoin doit pouvoir échouer à chaque colonne** (C5, run 2 = motif
   REFUTE). Deux témoins validaient leur contrôle à vide :
   (i) ‖F†x‖ ≡ ‖x‖ — un changement de base **unitaire sans poids** est
   identiquement L², pas une norme nouvelle ;
   (ii) des poids diagonaux dans la base propre d'un unitaire diagonal sont
   conservés par lui **gratuitement** (le témoin « générique » canonique
   passait la modulation sans condition).
   Remplacés par des poids non uniformes en base position et des poids dans
   une 3ᵉ base unitaire — les seuls qui puissent dire ✘ aux bonnes cases.
   Écho de la leçon V1-C4 : un témoin qui ne peut pas échouer ne témoigne pas.
4. **La machine corrige la théorie** (C6). Le rapport mesuré 0.4249 contre
   l'annonce O(t^{1/φ}) (prédit 0.6516) n'était pas un bug : la parité de
   |E(iξ)|² imposait O(t^{2/φ}) et 2^{−2α} = 0.42453. Consigné comme
   correction de théorie dans le docstring AVANT le verdict exit 0 — le
   contraire (ajuster le seuil pour passer) aurait été un sauvetage.

Historique des runs : run 1 exit 1 (TypeError mpmc, brouillons) ; run 2
**exit 1 REFUTE** — le verdict a correctement réfuté le script défectueux,
4 bugs diagnostiqués, zéro sauvetage ; run 3 exit 0.

---

## Reste ouvert (consigné, non adouci)

- **T1** : Ĥ hermitien diagonalisable, dimension finie. Le cas **Jordan**
  (non-normaux : E_α(Ĥ) existe mais la résolution P_k éclate en blocs) et la
  **dimension infinie** (convergence de la série en norme d'opérateur) sont
  ouverts.
- **T3** : établi pour les formes quadratiques (classe ℓ²) en dimension finie.
  L'extension à d'autres classes fonctionnelles et à la dimension infinie est
  ouverte.
- **Complétude totale** de C-H3 (le spectre du couple impose TOUTE la
  structure hilbertienne, au-delà de la forme quadratique) : ouverte — c'est
  la frontière de la Voie 3.

---

## Formulation gelée

> **Le spectre n'est pas postulé : il est ce que la mémoire laisse survivre.**
> La série directe atteint la résolution spectrale sans la connaître (1.2e-15) ;
> le critère |E_α(iλt^α)| = 1 tranche les arènes, et à α = 1/φ aucune ne survit —
> la sélection existe parce que le système est ouvert. Puis le couple déposé
> {flot fréquentiel, modulation} ferme l'arène : son commutant est trivial
> (dim 1, cI à 5.3e-15), et L² n'est pas choisie — elle est ce qu'il reste.
> À α = 1 tout ceci s'évanouit : le falsificateur est réel, donc la thèse est
> scientifique.
