# 📜 DÉPÔT DATÉ — ASSAUT VERTEX SUR α (PISTE 1 : DENSITÉ SPECTRALE DU NOYAU DORÉ)

**Date de dépôt** : 2026-08-27
**Statut** : PRÉ-ENREGISTREMENT — ce dépôt précède toute exécution de `verif_alpha_vertex.py`
**Script** : `verif_alpha_vertex.py` (à exécuter APRÈS dépôt, verdict bloquant, exit 1 si réfuté)
**Principe** : registre fermé de lectures, critères figés, **zéro paramètre libre** — le mémorandum anti-rétro-fit appliqué à la piste la plus prometteuse de la dérivation de α.

---

## 0. L'invariant contraignant (ancrage corpus)

- `thu/documents/MAILLON3_PROJECTION.md` §7 : la stationnarité (U3) interdit toute
  phase absolue stationnaire ; la liberté résiduelle de la projection **est** la jauge U(1).
- Conséquence : une constante de couplage ne peut pas être un nombre posé — c'est un
  **rapport de normes**, l'unique forme invariante de jauge :

```
α ≡ ‖V̂_temps(Ψ₁ ↔ Ψ_{1/2})‖² / ‖V̂_espace(Ψ₁ ↔ Ψ_{1/2})‖²
```

- Seules pièces machine-vérifiées du corpus disponibles pour les deux pattes :
  **K̂** (noyau doré de mémoire — temps — porte φ) et **T4** (géométrie 4D — espace — porte π).

## 1. Lecture physique du vertex

Vertex QED `e → e + γ` relu par la THU : le photon est le mode n=1 de la tour ;
l'électron est l'état fractal (Ψ₁)^{1/2} (dyade, `THEOREME_DYADE_SU2.md`).
Fréquence de Bohr de la transition : ω = ω₀ − ω₀/2 = **ω₀/2**.
En unités de tour (ω₀ = 1), la patte temps répond à **ω = 1/2**.

## 2. REGISTRE FERMÉ des lectures (pré-enregistré — aucune autre admise)

### Patte temps (3 lectures)

| # | Lecture | Amplitude | Ancrage corpus |
|---|---------|-----------|----------------|
| (a) | Noyau de relaxation de Mittag-Leffler, B = 1 | \|K̃(1/2)\|², K̃(ω) = (iω)^{1/φ−1}/((iω)^{1/φ}+φ) | R3/Maillon-1, complète monotonie → ML [T] (Prabhakar–Mainardi). Le corpus ne fixe aucune normalisation B ⇒ B = 1, zéro paramètre libre |
| (b) | Coefficients de l'équation mère cₙ = 1/Γ(n/φ+1) | \|c_{1/2}/c₁\|² | `DETAIL_COEFFICIENTS_Cn.md` — solution unique de D^{1/φ}[Ψ] = G[Ψ], vérifiée FFT à 2,22×10⁻¹⁶ |
| (c) | Transparence du mode ½ | 1 | Le spectre de tour prolongé au mode ½ donne φ + φ⁻¹ = √5 ⇒ réponse normalisée 1 (identité algébrique [T], contrôlée en C1) |

### Patte espace (5 lectures — normes géométriques, α⁻¹ = norme/‖temps‖²)

| # | Norme | Ancrage corpus |
|---|-------|----------------|
| (i) | (2π)⁴ | Mesure de boucle 4D QED (`LAGRANGIEN_SYNTHESE_PHYSICIENS.md`) |
| (ii) | π⁴ | Normalisation gaussienne 4D du théorème T4 (`DERIVATION_ALPHA_EM_UNIFIEE.md`, table Π→π^{+4}) |
| (iii) | 8π | Densité d'états 4D sans masse : ∫d⁴k/(2π)³ δ(k²)θ(k₀) = 1/(8π) |
| (iv) | 30 = (√2·√3·√5)² | Filtre géométrique 3D au carré (`DERIVATION_SQRT2_SQRT3.md`, A1–A4) |
| (v) | (2π)³ | Convention 2πδ du crochet de normalisation |

**Total : 15 lectures.** Aucune combinaison hors registre ne sera testée par ce dépôt.

*Exclusion assumée* : e⁻⁴ (enveloppe exponentielle du propagateur) est écartée comme
norme physique — l'audit du 27/08 a établi que le propagateur du photon est sans masse
et ne porte aucune décroissance exponentielle (voir `ASSAUT_E1B_MASSE_COURBURE.md`, mur des défaites).

## 3. Critères de verdict (figés avant exécution)

- Cible : α⁻¹(CODATA-2022) = 137,035999177 — référence secondaire CODATA-2018 = 137,035999084.
- **[T+]** : exactement une lecture à écart relatif ≤ 2,355×10⁻⁷ (bat la formule 5-facteurs).
- **[T]** : exactement une lecture à écart relatif ≤ 1×10⁻⁴.
- **[F]** : zéro ou ≥2 lectures à 1×10⁻⁴ ⇒ **la piste est morte sous cette forme**.
  Toute variante exige un NOUVEAU dépôt daté où les pattes sont forcées par la
  grammaire, jamais par la cible.

Contrôles internes bloquants (un seul échec ⇒ réfuté) :
- C1 : identité φ + φ⁻¹ = √5 (tol 1e-12) ;
- C2 : c₂ = 1/Γ(2/φ+1) = 0,889630375 (valeur publiée `DETAIL_COEFFICIENTS_Cn.md`, tol 1e-9) ;
- C3 : transformée de Laplace formelle s^{α−1}/(s^α+φ) vs intégration temporelle directe
  de E_{1/φ}(−φ·t^{1/φ}) en σ ∈ {1, 2} (tol 1e-6) ;
- C3b : cohérence des deux formes de \|K̃(ω)\|² (complexe vs réelle développée, tol 1e-12) ;
- C5 : unicité du hit (0 ou ≥2 à 1e-4 ⇒ réfuté).

Frères comme juges (annexe non bloquante) : la lecture (c·iv) prédit
α_W = (√2·√3·√5)⁻² = **1/30 exactement** — premier test croisé de la règle ;
α_S = 1/(2φ³) imprimé pour mémoire.

## 4. Divulgation de conception (honnêteté)

Des estimations d'ordre de grandeur des pattes ont circulé pendant la conception.
**Aucune lecture du registre n'a été ajoutée, retirée ni modifiée sur la base de sa
proximité avec 137,036** — chacune des 15 lectures tient sur une ancre de corpus citée.
Significativité : la fenêtre ±1e-4 autour de 137,036 a une largeur relative ~2×10⁻⁴ ;
15 tirages "au hasard" y entreraient avec une probabilité ~0,3 %. Un hit unique reste
donc un événement ; un non-hit tue la forme, pas l'invariant.

## 5. Engagements de la machine

1. B = 1 ; aucune tolérance ajustée après coup ; aucune lecture ajoutée après coup.
2. Le script exige la présence de ce dépôt (contrôle C0, horodatage comparé).
3. Sortie JSON horodatée `resultat_alpha_vertex.json` ; verdict lisible :
   `ALPHA_VERTEX_CONFIRME` ([T]/[T+]) ou `ALPHA_VERTEX_REFUTE` (exit 1).
4. En cas de [F] : diagnostic obligatoire — norme d'espace requise pour chaque patte
   temps, voisinage Fibonacci/Lucas de ces normes, facteur d'écart de la meilleure lecture.

---

> *Le sens d'un contrôle n'est pas dans sa formule mais dans ce qu'il peut falsifier.*
> Ce dépôt peut être falsifié par un simple nombre : s'il sort, la piste vertex v1 est morte.
