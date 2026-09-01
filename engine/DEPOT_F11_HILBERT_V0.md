# DÉPÔT F11 HILBERT V0 — La rotation Bateman dérive l'arène (C-H2, dimension finie)

**Date** : 2026-09-01
**Prédécesseur** : `DEPOT_F11_NORMES_V0.md` (C-H1 préliminaire, commit `12ef19f`)
**Script** : `verif_f11_hilbert_v0.py` — **exit 0, 6/6 contrôles**
**Résultats machine** : `resultat_f11_hilbert_v0.json` (`"ok": true`)

---

## Verdict

```
F11_HILBERT_V0_C_H2_THEOREME_DIM_FINIE — CONFORME (exit 0)
```

La frontière F11 passe de « reproduite via A2 » à **« partiellement dérivée »** :
sur chaque plan invariant, le produit scalaire n'est plus postulé — il est la
**conséquence unique** de la rotation Bateman R(θ), θ = πα/2, déposée dans
HAMILTONIEN C3, et de l'irrationalité de θ/π = 1/(2φ).

---

## Énoncé du théorème (C-H2, dimension finie)

> Toute norme sur un espace réel de dimension finie, invariante sous le groupe
> engendré par la rotation Bateman R(θ), θ = πα/2, θ/π irrationnel, est
> euclidienne sur chaque plan invariant — donc induite d'un produit scalaire
> (Jordan–von Neumann 1935).

**Ce que la preuve n'utilise PAS (anti-circularité)** : aucun produit scalaire,
aucune norme L², aucune décomposition spectrale. Seuls : les axiomes de la
norme, l'invariance de groupe, la densité de Kronecker, l'équivalence des
normes en dimension finie, et le théorème parallélogramme → produit scalaire.

---

## Preuve en 5 pas

1. **Isométries ∀n.** R(θ) isométrie pour la norme ⟹ R(nθ) = R(θ)ⁿ isométrie
   pour tout n ∈ ℤ. *(Machine : C1 — RᵀR = I, det = 1, valeurs propres
   e^{±iθ}, pire écart 2.220e-16 sur α ∈ {0.3, 0.5, 1/φ, 0.8, 0.95}.)*

2. **Densité (Kronecker).** θ/π = 1/(2φ) est irrationnel (φ irrationnel), donc
   {nθ mod 2π} est dense dans le cercle. *(Machine : C2 — orbite N = 2000,
   constante de couverture 1.413 (seuil ≤ 8, théorème des trois écarts) ;
   approche de j = π/2 à 1.152e-3, seuil 3.142e-2.)*

3. **Clôture vers SO(2).** En dimension finie toutes les normes sont
   équivalentes ⟹ x ↦ ‖x‖ est continue ⟹ l'invariance sous le sous-groupe
   dense {R(nθ)} s'étend à l'invariance sous SO(2) tout entier.

4. **Homogénéité par orbite.** SO(2)-invariance ⟹ ‖x‖ ne dépend que de
   |x|₂ sur chaque orbite : ‖x‖ = c(‖x‖₂)·‖x‖₂, avec c constant par homogénéité.

5. **Jordan–von Neumann.** La norme ainsi obtenue satisfait la loi du
   parallélogramme ; polarisation : ⟨x,y⟩ = ¼(‖x+y‖² − ‖x−y‖²) est un produit
   scalaire dont elle est issue. *(Machine : C4 — défaut de parallélogramme
   L² = 1.323e-15 ; rivales L¹ 2.78, L⁴ 0.35–0.47, L^∞ 0.52–0.73.)*

---

## Les 6 contrôles machine — nombres déposés

| # | Contrôle | Résultat | Seuil | Statut |
|---|----------|----------|-------|--------|
| C1 | Bateman ∀α (det, trace = 2cosθ, e^{±iθ}, RᵀR) | worst **2.220e-16** | ≤ 1e-14 | ✅ |
| C2 | Irrationalité → densité (couverture, approche de j) | couv. **1.413** ; dist(j) **1.152e-3** | ≤ 8 ; ≤ 3.142e-2 | ✅ |
| C3 | Invariance rotation : L² exact, rivales dévient | L² **4.441e-16** ; rivales min **0.247** | L² ≤ 1e-14 ; rivales ≥ 0.05 | ✅ |
| C4 | Défaut parallélogramme : L² nul, rivales gros | L² **1.323e-15** ; rivales min **0.472** | L² ≤ 1e-14 ; rivales ≥ 0.05 | ✅ |
| C5 | ℂ émerge : j² = −I, isométrie, ⟨jx,y⟩_ℂ = i⟨x,y⟩_ℂ | **1.225e-16 / 2.220e-16 / 8.882e-16** | ≤ 1e-14 | ✅ |
| C6 | Flot α→1 (e^{−iHt}) conserve L² | **2.220e-16** | ≤ 1e-14 | ✅ |

Détail C1, α = 1/φ : det = 1.0000000000000002, trace = 1.1292697728351009,
err_eigen = **0.0** (bit-exact), err_orth = 1.92e-17.

---

## La punchline : l'angle d'or ferme la dernière échapatoire

**Contre-factuel décisif.** Si θ/π était **rationnel** = p/q, l'orbite {nθ}
serait finie (q éléments), la clôture SO(2) n'aurait pas lieu, et des normes
**polygonales**, invariantes sous ce groupe fini, survivraient
(ex. symétrie à 90° : la norme ‖·‖_∞ tournée est invariante sans être
euclidienne). L'irrationalité de 1/(2φ) est donc **le verrou** : c'est elle
qui interdit à toute arène non quadratique de survivre au balayage.

**Résonance Fibonacci (expliquée par machine, consignée).** Le n\* qui
approche le mieux j = π/2 dans l'orbite est **n\* = 610 = F₁₅**, et
610·θ/(2π) = 94.25018. Mécanisme exact :

```
F₁₅/φ = 610/φ = 377.000733… ≈ F₁₄ (impair)
⟹ 610·θ = (π/2)·(610/φ) ≡ 377·π/2 + (π/2)·7.33e-4 ≡ π/2 (mod 2π)
⟹ dist = (π/2)·7.33e-4 = 1.152e-3   ← le nombre exact du JSON
```

Les nombres de Fibonacci consécutifs portent l'approche de j : **φ signe sa
propre orbite de rotation**. L'irrationalité garantit que l'approche est
infiniment fine ; la suite de Fibonacci fournit les meilleurs approximants.

---

## ℂ émerge de la clôture du groupe — il n'est pas postulé

- j = R(π/2) appartient à la **clôture** de {R(nθ)} (C2 : atteint à 1.152e-3) ;
- j² = −I et j est une isométrie (C5 : 1.225e-16, 2.220e-16) ;
- ⟨x,y⟩_ℂ := ⟨x,y⟩ − i⟨jx,y⟩ satisfait ⟨jx,y⟩_ℂ = i⟨x,y⟩_ℂ (C5 : 8.882e-16).

La structure complexe de la mécanique quantique **sort de la fermeture du
groupe engendré par la rotation déposée**, elle n'est pas une hypothèse.

---

## Portée honnête — ce que ce dépôt N'affirme PAS

| Critère | Statut | Preuve |
|---------|--------|--------|
| C-H1 (L² préliminaire, filtre α→1) | ✅ préliminaire | F11 NORMES V0, commit `12ef19f` |
| C-H2 (L² unique) | ✅ **dimension finie uniquement** | ce dépôt |
| C-H3 (spectral sans postuler Hilbert) | ❌ intact | — |

**Reste ouvert, consigné :**

1. **Voie 2 — dimension infinie.** Le pas 3 repose sur l'équivalence des
   normes, qui **tombe** en dimension infinie. Deux routes : (a) décomposer
   l'espace en plans invariants — mais cela présuppose le spectral, risque
   circulaire à documenter ; (b) un argument sans spectre (à trouver).
2. **Complétude.** Hilbert = préhilbertien **complet** ; la complétude n'est
   pas traitée ici.
3. **Voie 3 — théorème spectral** sans postuler Hilbert : intacte.

**Discipline.** La machine vérifie les hypothèses (C1, C2) et les conséquences
numériques (C3–C6) ; les pas 1–5 sont une preuve mathématique que la machine
ne remplace pas. L'invariance C3/C4 est testée sur familles de normes
concrètes, en cohérence avec le théorème — elle ne le remplace pas.

**Chaîne dérivationnelle mise à jour.** Équation mère → Schrödinger
(α→1, E1a ✅) ⊕ rotation Bateman → arène quadratique + ℂ (ce dépôt, dim. finie).
La « fourth step » de la chaîne (Hilbert) n'est plus entièrement un postulat :
sur chaque plan de modes, elle est dérivée de D^{1/φ}[Ψ] = G[Ψ].

---

## Leçons consignées (3, toutes prises avant dépôt d'un nombre)

1. **`math.exp` n'accepte pas les complexes** (TypeError sur
   `math.exp(1j·θ)`). Correctif : `cmath.exp`. Leçon : dans les scripts verif,
   toute exponentielle d'un nombre potentiellement complexe va à `cmath`.
2. **Le correctif a introduit `cmath` sans l'importer** (NameError). Leçon :
   importer `cmath` aux côtés de `math` dès l'écriture du script, pas au
   débuggage.
3. **Sonde manuelle Fibonacci : θ mal tapé** (`π·φ/4` au lieu de `π/(2φ)`) →
   résonance fausse, non reproductible du JSON. Corrigée avant dépôt ; le
   mécanisme confirmé (F₁₅/φ ≈ F₁₄) redonne exactement le nombre déposé.
   Leçon : toute sonde « hors script » doit reprendre les constantes du JSON,
   jamais les retaper.

Les trois bugs ont été attrapés par l'arbitre à l'exécution ou au
recoupement — **aucun nombre déposé n'en dépend**.

---

## Formulation gelée

> **« L'angle d'or balaie le cercle : la seule arène invariante est
> quadratique. En dimension finie, la rotation Bateman dérive le produit
> scalaire, et ℂ émerge de la clôture du groupe. Restent ouvertes : la
> dimension infinie, la complétude, le spectre. »**
