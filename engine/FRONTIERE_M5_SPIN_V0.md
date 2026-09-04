# FRONTIÈRE — M5 : LE SPIN COMME OBJET DEMI-ANGLE DU LIEN V0

## Le facteur 2 de la capacité 2(2l+1) et la signature fermionique — revêtement carré noyau→boucle

**Verdict visé : `M5_SPIN_DEMI_ANGLE_FERME` — exit 0 / REFUTE exit 1**
**Exécution :** `verif_m5_spin_v0.py` → `resultat_m5_spin_v0.json`
**Frontières mères :** `DEPOT_F12_PAULI_V0.md` (M1, d0f714a : « le spin n'est pas
dérivé » — le facteur 2 de la capacité 2(2l+1) y est POSTULÉ) ;
`FRONTIERE_D3_DYNAMIQUE_V0.md` (db00e3b : C10 — un seul poids spectral, la boucle
est son carré, site unique) ; a73c116 (M4 : le rang 4 localisé au degré interne
j spin-orbite, pièce toujours absente).
**Date :** 04/09/2026 — ce dépôt est ANTÉRIEUR à l'exécution (C0a).
**Sondes pré-gel :** `sonde_m5_spin_v0.py` → `sonde_m5_spin_v0_output.txt` (tous
les nombres ci-dessous calculés par machine avant gel, leçon FORCE V1.2).

---

## 0. CONSIGNATION DES SONDES (pré-gel — ce qu'elles ont établi)

La thèse candidate (EXPLORATION_SPIN_M5.md) : le spin est l'objet demi-angle du
lien — le poids mère λ(ω) = (iω)^α est un revêtement DOUBLE de la boucle
λ_loop = λ² (l'application carrée z↦z², deck z↦−z), et à α=1 la fibre est
{+i|ω|, −i|ω|} : deux valeurs, rapport −1 — le signe fermionique déposé.
Sorties machine (sonde unique, 0.0 s, déterministe, aucune graine) :

```
S0a LG1 == −ω² (forme close du carré, grille entière)  : écart max 8.025845262892095e-14  (barre 1e-12)
S0b LG1(w) == LG1(−w) à α=1 (boucle aveugle au signe)  : écart max 1.5926531622911327e-13 (barre 1e-12)
S0c LG(w) − LG(−w) à α=1/φ (grille appariée)           : écart max 102.1034208285483 ;
     à |ω|≈1 : 1.8640648476264556  (fermé 2·sin(πα) = 1.8640648476264554, écart 2.2e-16)
S1  fibre du carré à α=1, r∈{0.5,1,2,3,25.6} :
     |λ(−r)+λ(r)|      ≤ 3.1350958058172244e-15  (fibre {λ,−λ} — deck z↦−z)
     |λ(−r)²−λ(r)²|    ≤ 1.605169052578419e-13   (même point de boucle)
     rapport feuillets λ(+r)/λ(−r) = −1+1.2246467991473532e-16j (|ratio+1| = 1.22e-16)
S1  contraste α=1/φ à r=1 : |λ(−1)+λ(+1)| = 1.1292697728351009 = 2cos(πα/2) ≠ 0
     (les feuillets réels ne partagent PAS une même fibre du carré à α=1/φ)
S2  saut de branche à travers ω=0 — noyau : πα, boucle : 2πα
     α=1   : saut noyau = π (écart 0.0) ; saut boucle mod 2π = 0.0 — holonomie TRIVIALE
     α=1/φ : saut noyau = 1.9416110387254664 (π/φ = 1.94161103872546636495144412038) ;
             saut boucle = 3.8832220774509327 (2π/φ = 3.88322207745093272990288824076,
             écart 0.0) — NON trivial, ≠ π, ≠ 2π
     C0b verbatim (M1) : 2θ − πα = 0.0 — bit-exact
S3  LA VALEUR PROPRE BATEMAN EST LA PHASE DE FEUILLET :
     eig(R(θ)) = phase de feuillet λ(1)/|λ(1)| : écart 0.00e+00 (les deux branches)
     quadruple coïncidence du rapport de feuillets avec σ(α) déposé (M1 C4) :
       θ doublé 1.24e-16 ; Bateman² 2.29e-16 ; directe 1.24e-16 ; mpmath dps40 0.00e+00
     mpmath : σ(1/φ) = −0.362374890080479905574151189285 + 0.932032423813227706155259966181·i
     α=1 : eig(R(π/2)) = {−i, +i} (écart 6.12e-17) — la fibre elle-même
S4  balayage σ 720 pts (M1 C2/C4/C5 verbatim) :
     argmin γ[360] = 3.141592653589793 ; val min 1.2246467991473532e-16 ; zéros <1e-3 : 1
     σ(α=1) = −1 (écart 1.22e-16) — le signe fermionique ; σ(α=1)² = +1 (2.45e-16) — spinor
     σ(1/φ)² = −0.7373688780783203−0.6754902942615233·i ; angle +2π = 3.8832220774509323
       (fermé 2π/φ = 3.8832220774509327) ; |σ²−1| = 1.864065 ; |σ²+1| = 0.724750 — ni +1 ni −1 : anyon
     tension |1+σ(1/φ)|² = 1.27525021983904 (close) / 1.2752502198390399 (complexe) ;
       α=1 : 0.0 bit-exact (exclusion recouvrée)
S5  demi-vitesse : |arg(boucle) − 2·arg(noyau)| max sur grille = 0.0 (α=1) ; 0.0 (α=1/φ)
     traversée de l'axe : noyau accumule π (le demi-tour), boucle accumule 2π (invisible,
     tour complet) — ratio d'avance noyau:boucle = 1:2, θ/(2θ) = 0.5 bit-exact
S6  fibres à 2 valeurs distinctes non nulles : 5/5 aux DEUX α ;
     split sectoriel M1 C2b verbatim : ‖Ψ_exclu(σ=−1)‖ = 3.328925487086585e-17 (mort au
     zéro d'interférence) ; ‖Ψ_boson(σ=+1)‖ = 1.4142135623730951 = √2 exactement
M   ROUTE MORTE consignée avant gel — la monodromie de (iω)^α autour de ω=0 :
     α=1   : e^{2πi} = 1 (écart 2.45e-16) — TRIVIALE, aucune signature spinorielle
     α=1/φ : e^{2πi/φ} angle 3.8832 rad ; |·−(−1)| = 0.724750 — non spinorielle
     e^{2πiα} = −1 ⟺ α = 1/2 : hors points déposés (|1/2 − 1/φ| = 0.11803398874989479,
     |1/2 − 1| = 0.5). Les seuls points déposés : α = 1/φ (axiomatique O1) et α = 1
     (tranché M2/D3D). Route MORTE avant gel — consignée, jamais gelée.
```

Défaut estimateur de la sonde (consigné, leçon V1.2 — corrigé AVANT tout gel) :
un défaut d'AFFICHAGE — bord du wrap (saut α=1 affiché « écart 6.3e+00 » contre
la forme close π ; angles mod 2π non ramenés aux formes closes 2π/φ). Corrigé
et re-exécuté avant gel ; aucun défaut ne touche la route.

---

## 1. LES QUESTIONS FALSIFIABLES

- **T1 (fibre du carré à α=1)** : la paire de feuillets réels ±r du poids mère
  forme la fibre de l'application carrée z↦z² : λ(−r) = −λ(r) et
  λ(−r)² = λ(r)² — le noyau est un revêtement double de la boucle, de groupe
  deck z↦−z, sur les r ∈ {0.5, 1, 2, 3, 25.6}.
- **T2 (le rapport des feuillets est σ)** : λ(+r)/λ(−r) = σ(α) = e^{iπα} — le
  rapport d'échange déposé (M1 C4, quadruple route) EST le deck du revêtement
  carré. À α=1 : −1 exactement, fibre {+i|ω|, −i|ω|} purement imaginaire —
  le monde fermionique est le point α=1 du revêtement.
- **T3 (demi-angle)** : arg(boucle) = 2·arg(noyau) bit-exact sur la grille aux
  deux α (ratio d'avance 1:2) ; la traversée de l'axe donne au noyau πα de
  phase (à α=1 : π, le demi-tour) et à la boucle 2πα (à α=1 : 2π ≡ 0, le tour
  complet invisible) — le noyau tourne à demi-vitesse de la boucle.
- **T4 (le 2:1 n'existe qu'à α=1)** : la boucle est aveugle au signe à α=1
  (LG1(w) = LG1(−w)) ; à α=1/φ la boucle elle-même distingue les feuillets
  (écart 2·sin(πα) = 1.864 à |ω|=1) — le revêtement double n'est une base bien
  définie QU'AU point α=1 ; le braisage ouvert (σ²(1/φ) ni +1 ni −1) est
  consigné, pas sauvé.
- **T5 (le facteur 2)** : la dimension de fibre = 2 (machine, 5/5 sur RS aux
  deux α) fournit le facteur 2 de la capacité 2(2l+1) postulée à M1 —
  [MAPPING : (2l+1), dégénérescence des modes de boucle, n'est PAS dérivée ici,
  consignée] ; témoin sectoriel M1 C2b verbatim : le secteur antisymétrique de
  la paire de feuillets meurt au zéro d'interférence (σ=−1), le symétrique
  survit (√2, bunching).

**Honnêteté T (déposée, pas dissimulée) : ce sont des TÉMOINS de structure —
pas SU(2), pas l'équation de Dirac, pas g=2 (le moment magnétique reste hors
portée). Ce qui est visé : le FACTEUR 2 de la capacité (postulé M1 → dimension
de fibre machine) et la SIGNATURE fermionique (deck du revêtement au point
α=1 tranché). Le degré interne j (pièce M4) reste ouvert — ce dépôt ne le
ferme pas ; il en ferme le socle (le facteur 2 de la capacité).**

## 2. CONTRÔLES (gelés avant exécution)

| # | Contrôle | Barre gelée |
|---|---|---|
| C0a | antériorité : getmtime(FRONTIERE_M5_SPIN_V0.md) < début d'exécution | strict |
| C1 | filiation C10 : LG ≡ WG·WG (multiplication, site unique) et forme close −ω² à α=1 sur la grille entière | écart ≤ 1e-12 (mesuré 8.03e-14) |
| C2 | fibre du carré à α=1 sur RS={0.5,1,2,3,25.6} : \|λ(−r)+λ(r)\| ≤ 1e-14 ; \|λ(−r)²−λ(r)²\| ≤ 1e-12 ; rapport des feuillets = −1 à ≤ 1e-15 | barres (mesurés 3.14e-15 / 1.61e-13 / 1.22e-16) |
| C3 | coïncidence Bateman : \|eig(R(θ)) − phase de feuillet\| ≤ 1e-15 (deux branches) ; quadruple σ (θ doublé, Bateman², directe, mpmath dps40) ≤ 1e-15 | barres (mesurés 0.0 / 2.29e-16) |
| C4 | demi-angle : \|arg(boucle) − 2·arg(noyau)\| ≤ 1e-14 sur la grille aux DEUX α ; 2θ − πα == 0.0 bit-exact ; ratio de traversée == 0.5 bit-exact | barres (mesurés 0.0 / 0.0 / bit) |
| C5 | contraste α=1/φ (doit tenir) : \|LG(w)−LG(−w)\| max > 1 sur grille ; à \|ω\|≈1 == 2·sin(πα) à ≤ 1e-15 ; σ²(1/φ) : \|σ²−1\| > 1 ET \|σ²+1\| > 0.5 ; tension \|1+σ(1/φ)\|² > 1 | inégalités strictes (mesurés 102.1 / 2.2e-16 / 1.864065 / 0.724750 / 1.2753) |
| C6 | zéro d'interférence et secteurs : balayage 720 argmin == 360 ET val ≤ 1e-15 ET 1 zéro ; σ(1) = −1 ≤ 1e-15 ; σ(1)² = +1 ≤ 1e-15 ; tension α=1 == 0.0 bit-exact ; split sectoriel ‖Ψ_exclu‖ ≤ 1e-15 ET ‖Ψ_boson‖ = √2 à ≤ 1e-12 | barres (mesurés 1.22e-16 / 1.22e-16 / 2.45e-16 / 0.0 / 3.33e-17 / 2.8e-16) |
| C7 | consignation route morte : \|e^{2πi}−1\| ≤ 1e-15 ET \|e^{2πi/φ}+1\| > 0.5 ET \|1/2 − 1/φ\| > 0.1 (α=1/2 hors points déposés) | barres |

## 3. CONSÉQUENCES (falsifiables, gelées)

- **D1** : dimension de fibre == 2 aux DEUX α (5/5 sur RS) — le facteur 2 est
  une dimension de fibre, machine, pas un postulat.
- **D2** : le rapport des feuillets == σ(α) aux deux α (route fibre) ; à α=1
  le deck vaut −1 : le deck du revêtement carré EST le signe fermionique
  déposé ; à α=1/φ le deck n'appartient pas à Z₂ (braisage ouvert, consigné).
- **D3 [MAPPING]** : 2(2l+1) pour l=0..6 == [2,6,10,14,18,22,26] avec facteur
  2 = dimension de fibre (machine) et (2l+1) consigné NON dérivé — le mapping
  est déposé tel quel, sans pouvoir de verdict sur (2l+1).

## 4. ÉCHELLE DE VERDICT (gelée)

- **V+ `M5_SPIN_DEMI_ANGLE_FERME`** : C0a–C7 tous OK **ET** D1 **ET** D2 **ET**
  D3 conforme — le facteur 2 et la signature fermionique sont fermés au niveau
  visé (dimension de fibre + deck), la route morte est consignée.
- **V2_PARTIEL** : un de D1/D2 en échec partiel (fibre ou deck déviants).
- **V3_INCOMPLET** : contrôles OK, conséquence invérifiable.
- **V4_REFUTE** : UN SEUL contrôle en échec ⟹ exit 1, aucun sauvetage.

## 5. GRILLE GELÉE + HONNÊTETÉ

```
N=512 ; L=20π ; D_OMEGA=0.1 ; W0=1.0 ; GRID=720 ; RS=(0.5,1.0,2.0,3.0,25.6)
TOL_C=1e-12 ; TOL_PHASE=1e-15 ; mp.dps=40
poids mère λ(ω)=(iω)^α verbatim D3D (branche principale, phase ±πα/2)
boucle = MULTIPLICATION du poids mère (site unique C10, jamais (iω)^{2α})
Bateman R(θ) verbatim M1 C3 ; σ verbatim M1 C4 (θ doublé, Bateman², directe, mpmath)
dyade e^{iω₀x}, e^{2iω₀x} et convention O6 verbatim M1
```

- **Témoins de structure** — pas SU(2), pas Dirac, pas g=2 ; le degré interne
  j (pièce M4, brisure spin-orbite) reste ouvert : ce dépôt en ferme le socle
  (facteur 2 + signature), pas l'opérateur spin complet.
- **(2l+1) non dérivé** — la dégénérescence des modes de boucle est consignée
  [MAPPING] ; seule la dimension de fibre est machine.
- **S0c est une DÉCOUVERTE de sonde pré-gel** : la boucle elle-même distingue
  les feuillets à α=1/φ (LG(w) ≠ LG(−w)) — le revêtement double n'est une base
  bien définie qu'à α=1. Entrée dans T4 telle quelle, sans retouche.
- **Route monodromie MORTE avant gel** (α=1/2 requis, jamais déposé) —
  consignation C7 ; jamais rouverte sans nouveau dépôt ex ante.
- **Aucun chiffre calculé à la main** — tout est machine (sonde §0) ; le
  script verif n'existe pas encore au moment du dépôt.
- **Déterministe** — aucune graine, aucun aléa.

---

*Conformément à la discipline de la THU : frontière déposée avant tout script
(C0a) ; sondes pré-gel consignées avec leurs défauts ; un seul échec de contrôle
⟹ REFUTE sans sauvetage ; le braisage ouvert et la route morte sont consignés,
pas sauvés.*
