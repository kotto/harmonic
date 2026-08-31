# DEPOT COHÉRENCE HORS AXE KMS THU V1 — Où la mémoire laisse sa trace

**Question testée :** la mémoire D^(1/φ) préserve la thermicité (axe KMS : `DEPOT_KMS_DPHI_THU_V0.md` C2+C4). Où laisse-t-elle une trace **mesurable** — et cette trace peut-elle porter les candidats matière noire « effet de cohérence » ?
**Méthode :** chaque nombre déposé est calculé par machine (`verif_coherence_kms_thu_v1.py`, leçon FORCE V1.2).
**Sortie :** exit **0** — 6/6 contrôles conformes aux signatures attendues (`resultat_coherence_kms_thu_v1.json`).

---

## 1. LES RÉCLAMATIONS TESTÉES

Modèle machine : G(τ) = Σ_n p_n(β)·e^{iω_n τ}, poids thermiques **réels positifs** ; branche à mémoire : facteur d'influence e^{iθ} uniforme, θ = πα/2 (Feynman-Vernon, `DEPOT_HAMILTONIEN_ABC_THU_V0.md` C5).

| ID | Réclamation | Signature attendue | Résultat machine |
|----|-------------|--------------------|------------------|
| C1 | **Axe KMS insensible** : Ḟ_mem(ω)/Ḟ_mem(−ω) = e^{−βω} — la phase e^{iθ} apparaît aux deux membres et s'annule dans le rapport | < 1e-12 | ✅ **1.11e-16** (3 β × 3 ω) |
| C2 | **Réalité brisée** : sans mémoire G(0) est réelle (p_n réels, bain stationnaire) ; avec mémoire Im G_mem(0)/\|G_mem(0)\| = **sin(πα/2) = 0.825341** — une partie imaginaire là où il n'y en avait aucune | < 1e-12 | ✅ Im G(0) = **0.0e+00** ; trace = **0.825341 = sin θ** |
| C3 | **Rotation, pas amortissement** : arg G_mem(τ) − arg G(τ) = θ exactement et \|G_mem\| = \|G\| — la trace décale, elle n'amortit pas | < 1e-12 ; < 1e-12 | ✅ phase **1.11e-16** ; module **1.11e-16** |
| C4 | **Double discrimination T** : le décalage de phase est identique à toute température (β ∈ {0.5, 2π, 10}) ; le module suit e^{−βω} | < 1e-12 | ✅ **1.11e-16** |
| C5 | **Réversibilité** : G_mem(τ)·e^{−iθ} = G(τ) exact — la trace est une phase pure, aucune déperdition thermique | < 1e-14 | ✅ **1.24e-16** |
| C6 | **Mesurabilité de α** : θ(α) = πα/2 monotone strict — mesurer le décalage = mesurer α | 90/φ = 55.6231° ; monotone | ✅ 45.0000° / **55.6231°** / 81.0000° (α = 0.5 / 1/φ / 0.9) |

---

## 2. VERDICT : `COHERENCE_KMS_V1_TRACE_PHASE_MESURABLE`

### 2.1 La cartographie complète (module = thermicité, argument = cohérence)

1. **L'axe KMS est aveugle à la mémoire** (C1, 1.11e-16) — c'était le réflexe V0 (balance détaillée préservée). **La cohérence hors axe ne l'est pas** : G(τ) acquiert une rotation **globale et exacte** de πα/2 (C3, 1.11e-16 sur 5 points de temps), sans aucun amortissement (module identique à l'ulp).
2. **La signature la plus directe est C2** : pour un bain stationnaire à poids réels, la cohérence au temps nul est **réelle** — c'est un théorème élémentaire. La mémoire y injecte une **partie imaginaire proportionnelle à sin(πα/2) = 0.825341**. Toute mesure de ⟨A²⟩-type (variance, bruit) sur un système à mémoire voit cette composante : c'est le point d'entrée expérimental le moins exigeant (pas besoin d'interférométrie).
3. **Le split est propre** (C4+C5) : phase indépendante de T, module purement boltzmannien, et la mémoire se retire **intégralement** par rotation inverse (1.24e-16). La trace est **réversible** — la mémoire n'ayant pas d'énergie propre bornée (HAMILTONIEN V0 C3, degré fantôme), elle ne peut pas dissiper : elle ne peut que déphase. Tout est cohérent.

### 2.2 Le payoff : l'axiome α = 1/φ devient falsifiable (C6)

4. Trois non-sélections ont établi qu'**aucun argument théorique ne dérive α** (noyau, KMS, conservation — consignées dans les dépôts V0). Le C6 retourne la situation : θ(α) = πα/2 est **monotone et mesurable** — 45° (α=0.5), **55.6231° (α=1/φ)**, 81° (α=0.9). Un décalage de cohérence mesuré ≠ 55.6231° **réfuterait l'ordre doré**. Pour la première fois, l'axiome de Hurwitz a un **critère expérimental direct** — la théorie sort du pur axiomatique.

### 2.3 Lien matière noire (hypothèse de travail, non prouvée)

5. Les dépôts précédents ont requalifié la matière noire THU en **effet de cohérence** (pas thermique — KMS V0 C4/C5). Ce dépôt donne à cette hypothèse sa **forme testable** : un secteur matière noire à mémoire doit présenter (i) une cohérence à réalité brisée (Im ≠ 0, C2) et (ii) une phase **indépendante de la température** (C4) — deux signatures qu'un fluide thermique ordinaire ne peut pas produire. La mesure (courbes de rotation à haute résolution, lentillage, 21 cm) doit chercher une **structure de phase**, pas un excès de masse thermique. ⚠️ **Borne honnête** : c'est une prédiction de signature, pas une dérivation de l'abondance Ω_DM — l'écart de 76 % des candidats « niveaux de la tour » (H1, réfuté) n'est pas résolu ici.

---

## 3. CE QUE CE DÉPÔT ACHÈTE

- ✅ **La chaîne est fermée de bout en bout** : noyau ❌ → opérateur spectral ❌ → hamiltonien fermé ❌ → **phase d'influence ✅** (HAMILTONIEN V0) → **et la phase laisse une trace mesurable, réversible, indépendante de T** (ici). Chaque maillon est machine-vérifié.
- ✅ **Trois signatures expérimentales déposées** : partie imaginaire sin(πα/2) = 0.825341 à temps nul (C2), décalage de franges 55.6231° (C3, déjà V0 C5), indépendance de T (C4).
- ✅ **α passe du statut axiomatique au statut falsifiable** (C6) — première mesure possible de l'ordre de la mémoire.
- 🔬 **V2 naturelle** : la fonction à deux temps **hors de la ligne KMS complexe complète** G(τ₁, τ₂) = ⟨A(τ₁)A(τ₂)⟩ avec les DEUX jambes à mémoire (facteur e^{2iθ} — tester s'il apparaît une structure de battement entre θ et 2θ), et l'application au terme mémoire des courbes de rotation (`matiere_noire_thu.py`) comme phase et non comme masse.

---

## 4. BORNES HONNÊTES

| Item | Statut |
|---|---|
| C1 (axe KMS insensible) | ✅ réécriture du réflexe V0 côté cohérence — cohérence vérifiée, pas un fait nouveau |
| C2 (réalité brisée, sin θ = 0.825341) | ✅ **signature nouvelle déposée** — conséquence directe mais non consignée avant ce dépôt |
| C3/C5 (rotation globale, réversibilité) | ✅ structurelle (facteur uniforme) — la **non-dissipation** comme conséquence du degré fantôme est le point nouveau |
| C4 (indépendance de T) | ✅ extension du split V0 à la fonction à deux temps |
| C6 (mesurabilité de α) | ✅ **retournement méthodologique nouveau** : axiomatique → falsifiable |
| Modèle | ⚠️ bain discret à 5 modes, facteur d'influence uniforme e^{iθ} (Feynman-Vernon à noyau constant) — la généralisation à noyau ABC complet (K(t) décroissant) est V2 |
| Matière noire | ⚠️ signature de cohérence déposée ; **abondance Ω_DM non dérivée** (H1 réfuté à 76 %, inchangé) |
| Leçon de débogage | C1 premier run : dénominateur du taux de désexcitation écrit e^{+βω} au lieu de O(1) → 2.00e+01 = βω ; attrapé par la signature, pas par inspection |

---

## 5. FICHIERS

- `verif_coherence_kms_thu_v1.py` — les 6 contrôles, verdict par code de sortie (0 = conforme).
- `resultat_coherence_kms_thu_v1.json` — nombres bruts machine (6/6, exit 0).
- Contexte amont : `DEPOT_HAMILTONIEN_ABC_THU_V0.md` (mémoire ouverte, franges), `DEPOT_KMS_DPHI_THU_V0.md` (Boltzmann = phase), `DEPOT_JACOBSON_THU_V0.md` (8π = 2π×4), `COSMOLOGIE_MATIERE_NOIRE_ENERGIE_SOMBRE.md` (H1 réfuté, Ω observés).
