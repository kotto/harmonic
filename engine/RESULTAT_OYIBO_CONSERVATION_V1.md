# RÉSULTAT — OYIBO / CONSERVATION — V1 : **V+ — CHAINE_GAGUT_HURWITZ_CONFIRMEE (exit 0)**

**Date :** 2026-09-02 · **Dépôt :** `DEPOT_OYIBO_CONSERVATION_V1.md` (fermé ex ante, C0a ✓
: mtime dépôt 09:37:44.441Z < exécution 09:38:09.514Z)
**Script :** `verif_oyibo_conservation_v1.py` · **Sortie :** `resultat_oyibo_conservation_v1.json` (annexé tel quel, I5)
**Verdict machine :** `V+ CHAINE_GAGUT_HURWITZ_CONFIRMEE` — **15/15 unités de verdict, zéro échec, exit 0.**

---

## §1. Le changement unique par rapport à V0

La sonde finie de CH-G4 : **ν\*₅₀(x) := min sur les convergents d'indice i ∈ [25, 49]** de
q_i·\|q_i·x − p_i\| (n₀ = N/2 = 25, moitié de queue de la fenêtre gelée — choix structurel,
non calibré sur la barre). Tout le reste est repris à l'identique de V0. La sonde V0
(min-tête) reste **consignée** dans le résultat à titre de leçon (I3).

## §2. Le discriminateur de Hurwitz, cette fois au bon endroit

| Contrôle | Barre | Mesuré V1 | Verdict |
|---|---|---|---|
| C3a \|ν\*₅₀(1/φ) − 1/√5\| | 1e-6 | **6.07e-12** | ✓ (3 ordres sous la barre) |
| C3b \|ν\*₅₀(1/√2) − 1/(2√2)\| | 1e-6 | **9.40e-15** | ✓ |
| C4 max non-dorés < 1/√5 − 1e-3 | 0.446214 | 0.353553 (ancre √2, sa propre constante de classe) | ✓ |

**La prédiction déposée §1 de V1 est vérifiée par la machine** : déficit ~φ^{−2i} ⟹ ~10^{−11}
attendu à i₀ = 25, mesuré 6,07e-12. ν\*₅₀(1/φ) = 0.447213595494 = 1/√5 à 12 chiffres ;
ν\*₅₀(1/√2) = 0.353553390593 = 1/(2√2). Table complète (les deux fonctionnels) :

| Candidat | ν\* V1 (queue) | ν V0 (tête) | Lecture |
|---|---|---|---|
| **1/φ** | **0.447213595494** | 0.381966011250 | hit doré 1/√5 ✓ |
| 1/√2 | 0.353553390593 | 0.292893218813 | ancre 1/(2√2) ✓ |
| 1/√3 | 0.288675134595 | 0.288675134595 | < ancre ✓ |
| 1/e | 0.030289088685 | 0.030289088685 | ✓ |
| 1/√5 | 0.000000000000 | 0.000000000000 | le *nombre* 1/√5 n'est pas de la classe de φ ✓ |
| 1/π | 0.000000000000 | 0.000000000000 | ✓ |
| frac(√101) | 0.000000000000 | 0.000000000000 | ✓ |
| frac(√103) | 0.049266419147 | 0.049266419147 | ✓ |
| frac(√107) | 0.000000000000 | 0.000000000000 | ✓ |

## §3. Les 15 unités de verdict (toutes ✓)

C0a (ex ante) · C1 (φ²=φ+1, 1e-15) · C2 (K̂ double route, 12 lectures, 1e-12) ·
C5 (λ=φ ; c_k récurrence Γ, 1e-15) · C6 (calibrage ML dps260 ↔ Wiman dps120, z∈{31,33}, 1e-12) ·
A1/A2/A3 (Noether : oscillateur, pendule, Kepler e=0.6, drifts ≤ 1e-9) ·
B1 (48 lectures puissance ≤ 1e-12) · B2 (témoin négatif e^{−x} dévie > 0,1) ·
**B3 (cœur : r vs δ_pred, ≤ 10 % rel + décroissance, λ∈{2,φ})** ·
**B4 (pente −0.618984 vs −1/φ, écart 9,5e-4 ≤ 5e-3)** · C3a · C3b · C4 · D1 · D2 (+D3 consigné [P]).

## §4. Portée exacte (I4 — intouchable)

V+ établit **la chaîne de l'exposant, maillon par maillon, machine ex ante** :

> **Noether (toute symétrie continue ⟹ loi de conservation)** →
> **échelle (F(λx)=λ^{−s}F(x) ⟺ F=C·x^{−s})** →
> **exposant (l'unique s maximisant la résistance à la capture rationnelle est s = 1/φ,
> Hurwitz, unique à équivalence arithmétique près)** →
> **réalisation (le noyau ABC K(t) = E_{1/φ}(−φ·t^{1/φ}) porte l'invariance au régime
> longue mémoire, avec la déviation de tête en forme close déposée)**.

V+ n'établit **ni** la vérité de Gij j = 0, **ni** la validité littérale du GAGUT,
**ni** le couplage D^{1/φ} = G (resté [P] avec appui machine). Le maillon propre d'Oyibo
(CH-G3 : l'exposant universel *issu* de son équation de conservation) reste **[P]
consigné — corroboré, non dérivé** : la conservation seule n'impose pas d'exposant ;
c'est le discriminateur de Hurwitz (CH-G4) qui ferme la spécificité de 1/φ.

## §5. Traçabilité de la falsification

- V0 a échoué honnêtement (V4, exit 1) sur un défaut de sonde identifié au bit près ;
  les deux JSON (EXEC1 et EXEC2) sont conservés sans retouche (I5).
- V1 a changé **une seule ligne conceptuelle** (sonde de queue), re-gelée ex ante, avec
  **prédiction déposée** (déficit φ^{−2i} ~ 10^{−11}) que la machine a vérifiée : 6,07e-12.
- Si un relecteur conteste n₀ = 25 : le dépôt §1 donne le principe (moitié de queue,
  structurel) et la prédiction se réfute à toute autre valeur par la même barre —
  la falsifiabilité reste ouverte, un seul contrôle en échec suffit à faire tomber V+.
