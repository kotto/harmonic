# DÉPÔT FORCE V1.1 — témoin Bessel corrigé, physique gelée à l'identique

**Déposé le 28 août 2026 à 16:31:24 (mtime faisant foi).**
**Aucun script de cette campagne n'existe au moment du dépôt.** (C0a : mtime de ce fichier < mtime d'exécution.)

---

## §0. Nature de V1.1 — ce qui change, ce qui ne change pas

### Ce qui NE change PAS (physique gelée, verbatim V1)

La totalité de la physique est celle de `DEPOT_FORCE_V1.md` (28 août 2026, 15:53:10), qui reste l'autorité. Rappel non contractuel de l'unique objet déposé :

**χ(ω₀, a, k) = √( Σ_{n≥1} Jₙ(a)² · ( |K̂(ω₀+nk) − K̂(ω₀)|² + |K̂(ω₀−nk) − K̂(ω₀)|² ) ) / ( a·|K̂(ω₀)| )**

— Jacobi–Anger × action propre diagonale du noyau, fréquences signées, troncature |n| ≤ 11. Barres, registres O4/O9 (G\* = 0.3232880100102466, 17ᵉ objet), porteurs {0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.3, 2.0, 2.1, 3.4, 5.5, 8.9, 10.0, 14.4}, familles A (17 lectures), B (1134 lectures composées, [OBS] sans pouvoir de verdict), C (β sans verdict, trou D4) : **verbatim V1, zéro re-tarage, zéro paramètre libre ajouté.**

### Ce qui change (UNE chose : le témoin C2 → C2′)

La campagne V1 (verdict consigné **V4 — REFUTE, exit 1**, `RESULTAT_FORCE_V1.md`) a échoué sur son seul contrôle bloquant C2 : le témoin de double route Bessel. Cause racine diagnostiquée (consignée dans RESULTAT_FORCE_V1.md §5, hors protocole) : **bug d'ordre de normalisation** dans `bessel_table_recurrence` — la boucle `J[n] *= j0_series / J[0]` mute `J[0]` à l'itération n=0, si bien que le facteur vaut ensuite 1.0 et que J₁..J₁₁ gardent leurs valeurs brutes de récurrence (~1e-226, amorce 1e-300). J₀ « exact » était un artefact de cette mutation.

**C2′ (témoin corrigé, déposé ex ante) :**

1. **Route récurrence corrigée** : Miller descendant `J[n−1] = (2n/a)J[n] − J[n+1]`, amorce d'ordre 1 (`J[N]=0, J[N−1]=1`, N = 31), **facteur de normalisation `bessel_J(0,a)/J_rec[0]` figé AVANT toute mutation** de la table.
2. **Double concordance déposée** :
   - (a) écart relatif max |récurrence − série| ≤ **1e-12** sur tous les Jₙ, n ≤ 11, |Jₙ| ≥ 1e-10, a ∈ {0.1, 0.2} ;
   - (b) identité de normalisation sur la route récurrence : S = J₀ + 2Σ_{n=1}^{11} Jₙ = 1 à **1e-9** près (reste de troncature prédit ex ante : < 1e-20 pour a ≤ 0.2, forme Jₙ ≈ (a/2)ⁿ/n! — consigné comme prédiction).
3. **Contrôle de non-débordement** : J_rec[0] brut = ∏_{n=1}^{11}(2n/a) ≤ 1e23 pour a ≥ 0.1 — aucun débordement flottant possible.

**Toute autre différence entre `verif_force_v1.py` et le script V1.1 est interdite** (noms de fichiers, en-têtes et étiquettes de verdict exceptés). Toute divergence constatée au-delà de C2′ devra être consignée comme telle.

---

## §1. Objets et registres (fermés, verbatim V1)

O1–O8 : identiques au dépôt V1. **O9** : G\* = 0.3232880100102466 (17ᵉ objet, mesuré au jaugage V0). O10 : a ∈ {0.1, 0.2}, k ∈ {0.5, 1.0, 2.0}.

---

## §2. Familles (verbatim V1)

- **Famille A** — 17 lectures de la forme close (14 porteurs à a=0.1, k=1 ; A2 a=0.2 ; A3 k ∈ {0.5, 2.0} ; A4 G\* ; A5 station argmax = ω₀ = 1.0). Barre 1e-9.
- **Famille B** — 18 sources × 3 formes (G\*·c, G\*/c, c/G\*) × 21 cibles (registre ∪ {√2, π, e}) = **1134 lectures**, barre 1e-4 (2.355e-7 pour √2/π/e), hits = [OBS] uniquement ; tête de liste φ/5, manqué prédit ≈ 9.86e-4.
- **Famille C** — β_inf / β_sup, consignés SANS pouvoir de verdict (trou D4).

---

## §3. Contrôles

C0a (mtime), C0b (φ² = φ+1 à 1e-15), C1 (K̂ double route, 1e-15), **C2′ (ci-dessus, DEPOT §0)**, C3 (Jacobi–Anger ponctuel, 1e-15), C4 (action propre {0.1, 1.0, 14.4}, 1e-12), C5 (χ_machine(1,0.1,1) = G\* registre, écart relatif 0 exigé au niveau machine — barre 1e-12), C6 (U(1) spot, 1e-9), C7 (no-wrap ≤ 25.6).

**Un seul échec ⟹ REFUTE, exit 1 — aucun sauvetage.** Le verdict V4 de V1 reste l'histoire ; V1.1 est une campagne NOUVELLE (le script V1 n'est pas modifié, I5).

---

## §4. Échelle de verdicts (gelée ex ante, identique V1)

| Verdict | Condition | Exit |
|---|---|---|
| **V+ FORCE_FORME_FERMEE** | tous contrôles ✅ ET 17/17 lectures A dans la barre ET G\* reproduit ET station confirmée | 0 |
| V2 FORCE_FORME_PARTIELLE | forme tenue mais G\* hors barre ou station non confirmée | 0 |
| V3 REFUTE_FORCE_SANS_FORME | ≥ 1 lecture A hors barre | 1 |
| **V4 REFUTE** | tout contrôle bloquant en échec (dont C2′) | 1 |

---

## §5. Interdictions (I1–I5, verbatim V1)

I1 aucun paramètre libre ; I2 registres fermés ; I3 verdicts gelés ex ante ; I4 toutes les lectures consignées, y compris les quasi-échecs ; I5 script non modifiable après exécution.

## §6. Honnêteté (points déposés)

1. V1 est un REFUTE consigné ; V1.1 ne l'efface pas — il teste la même physique avec un appareil réparé.
2. La cause racine C2 est un diagnostic post-exécution : elle guide le dépôt, elle ne justifie rien a posteriori.
3. Le témoignage C2′ reste un témoin : s'il échoue à nouveau, REFUTE — même si la physique tient.
4. Famille B reste [OBS] sans pouvoir de verdict, y compris φ/5.
5. Famille C reste sans verdict (trou D4).
6. Aucune lecture ne sera retirée du consigné, y compris un éventuel échec C2′.

## §7. Reproductibilité

`python verif_force_v1_1.py` → verdict + `resultat_force_v1_1.json` (consignation intégrale). Entrées : ce dépôt, `DEPOT_FORCE_V1.md` (physique), registre O9.

---

*Dépôt gelé. La suite (script, exécution, résultat) sera postérieure à ce mtime.*
