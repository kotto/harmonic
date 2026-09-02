# DÉPÔT F12 PAULI V0 — L'exclusion comme interférence, la phase σ = e^{iπα}

**Verdict : `PAULI_MECANISME_INTERFERENCE_PHASE_DEPOSEE` — exit 0**
**Exécution :** `verif_f12_pauli_v0.py` → `resultat_f12_pauli_v0.json`
**Frontière :** `FRONTIERE_F12_TABLEAU_PERIODIQUE.md` (MORT 1, verrouillée en premier)
**Date :** 02/09/2026 — un seul run, 7/7 contrôles bloquants

---

## 0. LA THÈSE (chaîne P12–P15)

L'exclusion de Pauli n'est pas un décret d'antisymétrie : elle est le **point σ = −1 d'une famille d'interférence**. Deux particules identiques dans le même mode ont deux histoires indiscernables (directe / échangée) ; leurs amplitudes se superposent avec la phase d'échange σ, et l'amplitude de cohabitation vaut (1+σ)·A/√2. Détruite si σ = −1, doublée si σ = +1 (bunching bosonique).

La phase est dérivée des objets déposés : un échange = la boucle d'influence complète des deux mémoires = **deux franchissements de la référence** (Hamiltonien C5 : un franchissement = θ = πα/2) = 2θ = πα, d'où

$$\sigma(\alpha) = e^{i\pi\alpha} = e^{i2\theta}.$$

**À α = 1 : σ = −1 — le signe fermionique est recouvré de la phase mémoire déposée, pas postulé** — et σ² = +1 (échange double = identité, cohérence P₁₂² = 1).

**La tension déposée (P15, sans sauvetage — I5) :** à α = 1/φ, σ = e^{iπ/φ} et |1+σ|² = 1.275 ≠ 0 : l'interférence seule n'exclut plus la cohabitation. Deux lectures consignées :
- **L1** — la phase d'échange des particules de matière est l'action pleine Φ₂ = π (Hamiltonien C4), indépendante de α : l'exclusion survit intacte, θ = πα/2 ne porte que les franges de référence (C5). Prédiction ex ante : σ mesuré = −1.
- **L2** — σ = e^{iπα} : l'exclusion à α = 1/φ exige un second mécanisme (diffusion χ de la cohabitation — frontière M2 du potentiel/remplissage).

**Distinguo déposé ex ante :** interférométrie d'échange sur particules identiques. σ mesuré = −1 ⟹ L1 ; σ = e^{iπ/φ} ⟹ L2. Aucun ajustement après coup n'est admis.

---

## 1. OBJETS FERMÉS

| Objet | Contenu | Source |
|---|---|---|
| O1 | φ = (1+√5)/2, α = 1/φ | corpus |
| O2 | θ = πα/2 = π/(2φ) ≈ 0,9708 rad | KMS C6 (verbatim) |
| O3 | treillis N=512, L=20π, D_ω = 0,1 ; dyade ω₀ = 1, 2ω₀ | CHSH O3/O5 (verbatim) |
| O4 | K̂(ω) = φ/((iω)^α + φ), double route complexe/réelle | CHSH O2 (verbatim) |
| O5 | **σ(α) = e^{iπα} = e^{i2θ}** — la phase d'échange déposée (nouvel objet) | ce dépôt (P14) |
| O6 | M matrice deux particules ; échange P₁₂ = transposition ; K̂⊗K̂ par axe | CHSH (verbatim) |
| O7 | barres : TOL_C = 1e-12, TOL_PHASE = 1e-15, balayage 720 points | ce dépôt |
| O8 | verdicts V+/V3/V4, exit 0/1 | protocole |

---

## 2. CONTRÔLES BLOQUANTS — résultats machine

| Contrôle | Exigence | Lecture machine | Statut |
|---|---|---|---|
| **C0b** | φ² = φ+1 ; boucle = 2θ = πα bit-exact | 0.0e+00 ; 0.0e+00 | ✔ |
| **C1** | K̂ double route aux points {1, 2, ½, 1/φ} | écart max = 0.00e+00 | ✔ |
| **C2** (P12) | zéro de \|1+σ\| UNIQUEMENT en σ = −1 (balayage 720 pts, unicité) ; même-mode : σ=−1 → 0, σ=+1 → √2 | argmin = γ[360] = π exact ; val min = 1.22e-16 ; zéros < 1e-3 : **1** ; ‖Ψ_exclu‖ = 3.33e-17 ; ‖Ψ_boson‖ = 1.414214 = √2 | ✔ |
| **C3** (P13) | [K̂⊗K̂, P₁₂] = 0 : M aléatoire 512² + bloc dyade | 3.43e-16 ; 0.0e+00 | ✔ |
| **C4** (P14) | triple route σ = e^{iπα} (θ doublé = Bateman carré = action directe ; mpmath) ; α=1 : σ=−1, σ²=+1 ; α=1/φ : σ²≠+1 | routes 1.11e-16 ; mp 2.30e-16 ; \|σ(1)−(−1)\| = 1.22e-16 ; \|σ(1)²−1\| = 2.45e-16 ; \|σ(1/φ)²−1\| = **1.864065** (braisage ouvert, consigné) | ✔ |
| **C5** (P15) | \|1+σ(1/φ)\|² = 2+2cos(πα) ≠ 0 (routes close/complexe) ; α=1 : 0.0 bit-exact | close = complexe = **1.27525021983904** ; écart 2.22e-16 ; ‖Ψ_σ‖² dyade = 0.63762510991952 ; α=1 : 0.0e+00 bit-exact | ✔ |
| **C6** | témoins falsifiants : σ=+1 → 4 (bunching) ; σ générique (γ=0,7) → non nul ; modes distincts : secteurs A et S = 1 | 4.0 (bit-exact) ; 3.529684 = close ; ‖Ψ_dm^A‖ = ‖Ψ_dm^S‖ = 1.000000000000 | ✔ |

---

## 3. NOMBRES DÉPOSÉS (calculés par machine, mpmath dps 40)

```
σ(α=1)   = −1 + 1.22e-16 i            (résidu libm consigné ; |σ−(−1)| = 1.22e-16)
σ²(α=1)  = +1 − 2.45e-16 i            (échange double = identité à la limite standard)
σ(α=1/φ) = −0.362374890080480119958646637475 + 0.932032423813227621534031668691 i
σ²(α=1/φ)= −0.7373688780783203 − 0.6754902942615233 i   (|σ²−1| = 1.8640648476264554)
|1+σ(1/φ)|² = 1.27525021983904        (la tension P15 — ≠ 0, déposée)
‖Ψ_σ(1/φ)‖² (dyade) = 0.63762510991952 (amplitude de cohabitation survivante = tension/2)
K̂(1)² = 0.360501225723−0.318122109894j ; K̂(1)K̂(2) = 0.270604178517−0.297669860573j ;
K̂(2)² = 0.197718449139−0.272406302580j   (spectre du noyau à deux particules, dyade)
```

---

## 4. CE QUE CE DÉPÔT ÉTABLIT — ET CE QU'IL N'ÉTABLIT PAS

**Établi (machine, exit 0) :**
1. **Le mécanisme** — l'exclusion est le point σ = −1 d'une famille d'interférence à un paramètre, avec unicité machine du zéro (balayage complet 720 points) et dualité bunching (σ=+1 → √2, bit-près). L'antisymétrie cesse d'être un axiome : c'est une interference destructive.
2. **La fermeture** — le noyau mémoire commute bit-près avec l'échange : la statistique ne peut pas venir de la dynamique K̂, elle vient de l'influence Φ₂. (Cela clôt la fantasy d'une « statistique générée par le noyau » et localise exactement où la phase doit être cherchée.)
3. **La phase** — σ = e^{iπα} par trois routes déposées convergentes ; **le signe fermionique −1 est recouvré à α = 1** de la phase mémoire θ = πα/2 doublée, et la cohérence P₁₂² = 1 tient bit-près à la limite standard.
4. **La condition du remplissage** — l'exclusion ne tue que la cohabitation : les paires de modes distincts survivent dans les deux secteurs (norme 1 bit-près). C'est la condition de possibilité de la MORT 3.

**Non établi (frontières consignées, sans sauvetage) :**
- **La tension P15 est ouverte** : à α = 1/φ, l'interférence seule n'exclut plus (1.275 ≠ 0). L1 (action pleine Φ₂ = π pour la matière) vs L2 (second mécanisme χ) — le distinguo est **expérimental**, déposé ex ante.
- **Le spin n'est pas dérivé** : la sélection boson/fermion par secteur (pourquoi l'électron est dans le secteur σ) reste frontière. Ce dépôt dérive la phase de la boucle d'influence, pas l'affectation des particules aux secteurs.
- **Le braisage ouvert à α=1/φ** : σ² ≠ +1 (écart 1.864) — l'échange double ne se referme pas. Consigné tel quel : c'est une prédiction falsifiable du secteur α = 1/φ, pas un défaut à corriger.

---

## 5. HISTORIQUE D'EXÉCUTION (honnête)

| Run | Résultat |
|---|---|
| 1 | **exit 0** — 7/7 contrôles, verdict `PAULI_MECANISME_INTERFERENCE_PHASE_DEPOSEE` (0,1 s) |

Une seule correction antérieure à l'exécution : une ligne de C5 syntaxiquement fautive (constructeur walrus mal formé) corrigée avant tout run — aucun contrôle, barre ni lecture modifiée après exécution.

---

## 6. FORMULATION GELÉE

> **Pauli n'est pas un décret : c'est une interférence. Deux histoires indiscernables, une phase d'échange dérivée de la mémoire — deux franchissements de la référence, 2θ = πα — et le signe fermionique tombe tout seul à la limite standard : e^{iπ} = −1, recouvré, pas postulé. Le noyau n'a rien à y voir — il commute avec l'échange bit-près : la statistique habite l'influence, pas la dynamique. À α = 1/φ, la tension est déposée sans maquillage : 1.275 ≠ 0, l'interférence seule n'exclut plus — et le monde tranchera par l'interférométrie, ex ante, L1 ou L2. La MORT 1 est fermée ; la MORT 2 (le potentiel r^{2α−3}) attend.**

---

*Conformément à la discipline de la THU : tous les nombres déposés sont calculés par machine ; la tension est consignée, pas corrigée ; un seul run, exit 0.*
