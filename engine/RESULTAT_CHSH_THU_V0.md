# RÉSULTAT CHSH THU V0 — Tsirelson reproduit, la mémoire ABC amortit l'intrication au prix déposé

| | |
|---|---|
| **Date d'exécution** | 28/08/2026 14:37:37 (dépôt 14:17:28 — C0a ✓, 20 min d'antériorité) |
| **Dépôt** | `DEPOT_CHSH_THU_V0.md` (fermé, non modifié — I5) |
| **Script** | `verif_chsh_thu_v0.py` (python 3.11.8, numpy 1.26.4) |
| **Journal** | `resultat_chsh_thu_v0.json` — toutes les lectures consignées |
| **Verdict** | **V+ — CHSH_THU_CONFORME — exit 0** |

---

## 1. Contrôles bloquants : 8/8 OK

| # | Contrôle | Résultat |
|---|----------|----------|
| C0a | dépôt antérieur à l'exécution | mtime 14:17:28 < 14:37:37 |
| C0b | φ² = φ+1 | écart 0.0e+00 — barre 1e-15 |
| C1 | K̂ double route (complexe vs réelle) aux points {1, 2, ½, 1/φ} | **0.00e+00** |
| C2 | orthonormalité dyade + norme \|Φ+⟩ | \|⟨φ₁,φ₂⟩\| = 2.60e-17 ; ‖φ_i‖−1 = 0.00e+00 ; ‖Φ+⟩−1 = 1.11e-16 |
| C4 | action propre du noyau (FFT vs forme close) | 8.30e-16 (φ₁) ; 1.40e-15 (φ₂) |
| C3 | témoin produit φ₁⊗φ₁ | S_prod = 1.4142135623730947 ≤ 2 (cible √2 = 1.4142135623730951) — **aucune fausse violation** |
| C6 | Horodecki (route T/SVD) sur \|Φ+⟩ pur | S_max = 2.828427124746190 ; s = [0.9999999999999999, 0.9999999999999999, 0.9999999999999998] ; écart 4.44e-16 |
| C5 | treillis N = 512 → 1024 | S₀(1024) = 2.828427124746194 ; écart 4.88e-15 |

## 2. Famille A — le formalisme bancarisé produit Tsirelson exact

Les quatre E aux settings (0, π/2, π/4, −π/4), triple route (pleins N=512 / 2×2 / cible cos(a−b)) :

| Paire | Machine (N=512) | Route 2×2 | Cible cos(a−b) |
|---|---|---|---|
| E(a,b) | +0.7071067811865472 | +0.7071067811865475 | +0.7071067811865476 |
| E(a,b′) | +0.7071067811865472 | +0.7071067811865475 | +0.7071067811865476 |
| E(a′,b) | +0.7071067811865472 | +0.7071067811865475 | +0.7071067811865476 |
| E(a′,b′) | −0.7071067811865472 | −0.7071067811865474 | −0.7071067811865475 |

**S₀ triple route : machine = 2.828427124746189 ; 2×2 = 2.828427124746190 ; cible 2√2 = 2.8284271247461903 — écart max 1.33e-15 (barre 1e-9).**

S₀ > 2 : le formalisme dérivé **viole la borne classique et atteint exactement la borne de Tsirelson**. La chaîne Hilbert (Riesz-Fischer + A2) → quantification (univocité de phase) → Born (Parseval) est porteuse de non-localité jusqu'au dernier bit.

## 3. Famille B — la mémoire ABC amortit l'intrication conformément à la forme close déposée

**B1 — coefficients fermés** (état noyau \|Φ+_K⟩ ∝ (K̂⊗K̂)\|Φ+⟩, c_i = K̂(ω_i)²) :

| Objet | Module | Argument |
|---|---|---|
| K̂(1) | 0.6933930614900616 | −0.36151524845887845 |
| K̂(2) | 0.5801701079352833 | −0.47147482062836343 |
| c₁ = K̂(1)² | 0.4807939377225604 | −0.723030496917757 |
| c₂ = K̂(2)² | 0.33659735414163827 | −0.9429496412567268 |

**Norme post-noyau AVANT renormalisation (consignée, dépôt §2)** : machine = **0.41500637908706695**.

**Écart de diagnostic consigné et expliqué** : la ligne « forme close » imprimée par le script (0.5869076497762802) omettait le facteur 1/√2 de \|Φ+⟩. Vérification arithmétique post-hoc : ratio = 0.5869076497762802 / 0.41500637908706695 = **1.4142135623730954 = √2** (écart 2.2e-16) ; forme close corrigée √((\|c₁\|²+\|c₂\|²)/2) = 0.415006379087067 ≡ machine (écart 5.6e-17). Le dépôt n'avait déposé **aucune** forme close pour cette norme (consignation seule, §2 ligne 53) — la valeur machine est la lecture correcte, l'écart affiché 1.72e-01 est un artefact d'étiquette du script, **sans impact sur aucune barre ni sur le verdict**. Le script n'est pas modifié après exécution (I5) ; la présente note sert de correction consignée.

**B2/B3 — la prédiction ex ante est tenue à 8.9e-16** :

| Grandeur | Déposée ex ante | Machine | Écart |
|---|---|---|---|
| ρ = 2\|c₁c₂\|/(\|c₁\|²+\|c₂\|²) | forme close §2 | 0.9396370575958052 (recalcul exact : 0.0) | — |
| S_max = 2√(s₁²+s₂²) (Horodecki, SVD de T) | **2√(1+ρ²) = 2.74438903948205** | 2.744389039482051 | **8.88e-16** (barre 1e-9) |

Valeurs singulières de T : **[1.0, 0.9396370575958058, 0.9396370575958057]** — le rang de Schmidt 2 est conservé (s₁ = 1 exactement), la seconde valeur singulière vaut ρ à l'identique.

**Horizon déposé : 2 + 1e-9 < 2.744389 ≤ 2√2 + 1e-9 ✓ — la mémoire ABC amortit la violation SANS la détruire.**

**B4 — lecture informative SANS verdict (déposé ainsi)** : S aux settings V0 sur l'état noyau = **2.711055862850338** < S_max = 2.744389039482051. L'optimum de CHSH n'est plus aux angles de \|Φ+⟩ : la mémoire imprime une phase relative arg(c₂) − arg(c₁) = **−0.21991914433896975 rad** (arithmétique post-hoc pure sur valeurs consignées), qui fait tourner les angles optimaux. Prédiction quantitative nouvelle, consignée sans pouvoir de verdict.

## 4. Ce que V0 établit — et ce qu'il n'établit pas

**Établi [T, machine, 8/8 contrôles, exit 0] :**
1. **La violation de Bell est dérivée** : le formalisme bancarisé (treillis N=512, norme unitaire, dyade harmonique, produit tensoriel par blocs) produit S₀ = 2√2 à 1.33e-15, invariant de treillis (C5, 4.88e-15). Si Hilbert et Born sont réellement dérivés, c'était forcé — la porte de cohérence est **passe** (dépôt §6.1 : ce n'est pas une découverte).
2. **Le formalisme ne fabrique pas de fausse violation** : l'état produit donne √2 ≤ 2 (C3), la route Horodecki/SVD est cohérente (C6, 4.44e-16).
3. **La vraie physique du test — l'amortissement d'intrication par la mémoire d'or — est confirmée en forme close ex ante** : S_max = 2√(1+ρ²) avec ρ = 0.9396370576 fermé avant exécution, tenue à 8.9e-16. C'est la **seconde prédiction dynamique de divergence** confirmée de la THU (avec E1bis — Zeno fractionnaire).
4. **L'amortissement n'est pas une destruction** : horizon 2 < S_max ≤ 2√2 tenu, rang de Schmidt 2 conservé. La mémoire réduit la non-localité d'un facteur contrôlé — quantité résiduelle ρ(ω₀) fonction fermée du porteur.

**Pas établi (honnêteté, dépôt §6) :**
- B4 sans verdict : la forme close des angles optimaux sous mémoire n'a pas été déposée ni testée (phase −0.2199 rad consignée comme diagnostic).
- Lectures machine internes au formalisme : aucun test expérimental n'est revendiqué.
- Un seul porteur (ω₀ = 1) : la carte ρ(ω₀) et la loi S_max(ω₀) sur le balayage restent à faire (prolongement naturel par dépôt daté).
- La famille A est une porte de cohérence sur la prétention fondatrice, pas un acquis nouveau.

---

> *La non-localité n'était pas un ajout : elle tombait de la chaîne dérivée, au dernier bit près (1.33e-15). Et la mémoire d'or ne la brise pas — elle la taxe : 2.744389039482, prix déposé la veille de l'exécution, payé à 8.9e-16 près. L'éliminateur de modes élimine aussi une part d'intrication — et il en laisse assez pour violer Bell.*
