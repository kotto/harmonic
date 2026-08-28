# ⚡ FORCE V1.1 — témoin Bessel corrigé, physique gelée : le témoin passe, l'identité déposée non

**Campagne du 28 août 2026 — guichet 2, suite (V1.1)**

| | |
|---|---|
| Dépôt | `DEPOT_FORCE_V1_1.md` (gelé, mtime **2026-08-28 16:32:41**) |
| Script | `verif_force_v1_1.py` (copie V1 + diff déposé unique C2′ ; jamais modifié après exécution, I5) |
| Journal | `resultat_force_v1_1.json` (consignation intégrale, exécution 16:33:49) |
| C0a | **OK** — dépôt (16:32:41) < exécution (16:33:49) |
| Contrôles | 8 ✅ / 1 ❌ (C2′, sous-condition (b)) |
| **Verdict** | **V4 — REFUTE — exit 1** (aucun sauvetage, dépôt §3/§5) |

> **Lecture honnête d'entrée.** Le correctif du témoin V1 **fonctionne** : la concordance série × récurrence descendante corrigée donne **6.11e-16** (sous-condition (a), barre 1e-12) — le bug d'ordre de normalisation de V1 est réparé et validé. Mais la campagne échoue sur la sous-condition **(b) que MOI-MÊME j'ai déposée** : j'ai écrit l'identité de normalisation **sans la parité**. L'identité correcte est **J₀ + 2Σₖ J₂ₖ(a) = 1** (ordres pairs uniquement, car J₋ₙ = (−1)ⁿJₙ fait s'annuler les termes impairs) ; j'ai déposé J₀ + 2Σ_{n≥1}Jₙ = 1, qui vaut 1.0999 (a=0.1) et 1.1994 (a=0.2). Le mesuré max|S−1| = **1.99e-01** est exactement la signature de cette erreur (≈ 2Σ impairs à a=0.2). Verdict **V4 consigné tel quel** ; le script n'est pas modifié (I5) ; une correction exigerait un nouveau dépôt daté (V1.2).

---

## 1. Contrôles (dépôt V1.1 §3)

| Contrôle | Statut | Mesure |
|---|---|---|
| C0a dépôt antérieur à l'exécution | ✅ | mtime dépôt 16:32:41 < exécution 16:33:49 |
| C0b fermeture algébrique φ² = φ+1 | ✅ | écart 0.0e+00 |
| C1 K̂ : route complexe vs forme réelle | ✅ | écart max **1.24e-16** |
| **C2′ (a) concordance série × récurrence corrigée** | ✅ | écart max **6.11e-16** (barre 1e-12) — **le correctif V1 est validé** |
| **C2′ (b) identité J₀ + 2ΣJₙ = 1** | ❌ **ÉCHEC** | **max\|S−1\| = 1.99e-01** (barre 1e-9) — identité déposée FAUSSE, §5 |
| C2′ (c) non-débordement | ✅* | J_rec[0] max = 9.975e-01 ≤ 1e23 (*étiquette imprécise : valeur post-normalisation, voir §5-bis) |
| C3 Jacobi–Anger ponctuel (4 couples, 512 pts) | ✅ | écart max **2.29e-16** |
| C4 action propre du noyau {0.1, 1.0, 14.4} | ✅ | max **3.79e-16** |
| C5 reproduction voie V0 : χ(1,0.1,1) = G\* | ✅ | **0.00e+00** (bit-exact) |
| C6 U(1) aveuglement spot | ✅ | dérive max **6.94e-18** |
| C7 no-wrap | ✅ | max 25,4 ≤ 25,6 — aucun mode wrapé |

---

## 2. Famille A — la forme close (physique verbatim V1, 17 lectures, barre 1e-9)

**17/17 ✅ — résultats identiques bit à bit à V1** (physique gelée, consignation complète dans `resultat_force_v1_1.json` ; table détaillée dans `RESULTAT_FORCE_V1.md` §2) :

| Lecture clé | χ_machine | écart |
|---|---|---|
| χ(1, 0.1, 1) = **G\*** | 0.3232880100102466 | **0.00e+00** |
| A2 χ(1, 0.2, 1) — la « dérive 5 % » V0 | 0.3225067397099395 | 3.44e-16 |
| A3 χ(1, 0.1, 0.5) / χ(1, 0.1, 2) | 0.1013641298985957 / 0.3849844383150536 | 5.48e-16 / **0.00e+00** |
| pire lecture (χ(14.4, 0.1, 1)) | 0.0253115414684661 | **3.15e-15** |

**A4** : G\* = 0.3232880100102466 reproduit par la forme close, écart **0.00e+00**. **A5** : station argmax = **ω₀ = 1.0** confirmée.

## 3. Famille B — 1134 lectures composées ([OBS])

**0 hit** (barres 1e-4 / 2.355e-7). Tête de liste φ/5 : écart **9.8511e-04**, manqué confirmé comme prédit ex ante (≈ 9.86e-4) — l'association G\* ≈ φ/5 reste **[OBS] non candidate**.

## 4. Famille C — diagnostics β (sans verdict, trou D4)

β_inf = **+0.026616** (5 porteurs ω₀ < 1), β_sup = **−0.848981** (8 porteurs ω₀ > 1) — identiques à V1, consignés sans pouvoir de verdict.

---

## 5. Cause racine de l'échec C2′(b) — mon erreur d'algèbre DANS le dépôt

### L'identité correcte (démontrée ici, POST-exécution — ne modifie rien)

De la fonction génératrice e^{(a/2)(t − 1/t)} = Σ_{n=−∞}^{+∞} Jₙ(a) tⁿ, en t = 1 :

Σ_{n=−∞}^{+∞} Jₙ(a) = 1, avec **J₋ₙ = (−1)ⁿ Jₙ** ⇒ Jₙ + J₋ₙ = Jₙ(1 + (−1)ⁿ) = 2Jₙ si n **pair**, **0** si n **impair**.

**Donc : J₀(a) + 2Σ_{k≥1} J₂ₖ(a) = 1 — ordres pairs uniquement.**

### Ce que j'avais déposé

DEPOT_FORCE_V1_1.md §0.2(b) : « S = J₀ + 2Σ_{n=1}^{11} Jₙ = 1 à 1e-9 près » — **sans la restriction de parité**. La somme sur tous les ordres vaut S = 1 + 2Σ_{k≥1}J₂ₖ₊₁ = 1 + 2(J₁ + J₃ + …) :

- a = 0.1 : S ≈ 1 + 2(0.0499376 + 0.0000156) ≈ **1.09991** → |S−1| ≈ 0.0999
- a = 0.2 : S ≈ 1 + 2(0.0995008 + 0.0001663) ≈ **1.19933** → |S−1| ≈ 0.1993

**Mesuré : max|S−1| = 1.99e-01** — exactement la déviation prédite par cette analyse (a=0.2 est le max des deux). L'échec n'est pas un accident numérique : c'est la signature arithmétique de l'identité fausse déposée. Une erreur déposée est un contrôle en échec, point — le dépôt fait partie de l'expérience.

### 5-bis. Réserve honnête sur l'étiquette (c)

Le contrôle (c) « J_rec[0] brut ≤ 1e23 » a en réalité enregistré la valeur **après** normalisation (la fonction retourne la table normalisée) : 9.975e-01. La borne ex ante ∏(2n/a) ≤ 1e23 reste arithmétiquement vraie (et le vrai brut ≈ 8.2e21 pour a=0.1, n_max=31 — aucun débordement), mais la quantité enregistrée est triviale. Consigné comme étiquette imprécise, sans impact sur les barres (la sous-condition porteuse est (a)).

---

## 6. Établi / pas établi

**Établi :**

1. **Le correctif du témoin V1 est validé** : concordance série × récurrence descendante corrigée à **6.11e-16** (C2′(a)) — le bug d'ordre de normalisation était bien la cause V1, et lui seul.
2. La physique gelée tient **encore** : 17/17 (pire 3.15e-15), G\* bit-exact (0.00e+00), station ω₀=1, φ/5 manqué comme prédit, 0/1134 hits.
3. Le protocole détecte une erreur d'algèbre déposée à 1e-9 près : max|S−1| = 0.199 contre barre 1e-9.

**Pas établi :**

1. **Le verdict de campagne : V4 — REFUTE** (deuxième consécutif) — à cause de MOI, pas de la physique : V1 = bug d'implémentation du témoin ; V1.1 = identité fausse dans le dépôt.
2. β_inf/β_sup : toujours sans verdict (trou D4).

## 7. Leçon de protocole (consignée)

Deux REFUTE consécutifs, deux fois sur l'appareil expérimental (implémentation puis dépôt), zéro fois sur la loi. C'est le protocole qui fonctionne : **il refuse que l'expérimentateur corrige sa copie après coup** — une identité fausse déposée est un contrôle en échec, exactement comme un bug d'implémentation. Le prix de cette rigueur : trois dépôts au lieu d'un. Le bénéfice : quand le V+ viendra, il ne devra rien à l'indulgence de la machine envers elle-même.

## 8. Reproductibilité

```
python verif_force_v1_1.py        # → verdict V4 — REFUTE, exit 1
```
Sortie : `resultat_force_v1_1.json`. Physique : `DEPOT_FORCE_V1.md` (autorité). Diff V1→V1.1 : 42 lignes, intégralement celui du dépôt V1.1 §0 (audit `diff` consigné avant exécution).

## 9. Prochaine étape proposée (non contraignante)

- **FORCE V1.2** (troisième dépôt daté) : identique à V1.1 avec la sous-condition (b) corrigée en **J₀ + 2ΣₖJ₂ₖ = 1** (ordres pairs), l'identité étant démontrée DANS le dépôt (fonction génératrice, parité) — la physique reste verbatim V1.
- **D3 — le compensateur −¼F²** : conformément à la séquence choisie (« V1.1 puis D3 »), passer à la dérivation de la loi d'interaction à partir du noyau.

---

*« Le témoin a été réparé, puis c'est le dépôt qui a témoigné contre son auteur. L'éliminateur élimine aussi les identités bâclées — surtout les siennes. »*

*Consigné le 28 août 2026 — machine ZCode, protocole dépôt-d'abord, aucun sauvetage.*
