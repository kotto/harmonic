# DÉPÔT FORCE V1.2 — identité de normalisation paire (démontrée), fermeture du guichet 2

**Déposé le 28 août 2026 à 16:51:52 (mtime faisant foi).**
**Aucun script de cette campagne n'existe au moment du dépôt.** (C0a : mtime de ce fichier < mtime d'exécution.)

---

## §0. Nature de V1.2 — ce qui change, ce qui ne change pas

### Ce qui NE change PAS (physique + témoin (a) gelés, verbatim V1/V1.1)

La physique est celle de `DEPOT_FORCE_V1.md` (autorité) : forme close χ(ω₀,a,k), familles A (17 lectures @1e-9), B (1134 @1e-4/2.355e-7), C (sans verdict), registres O1–O10, barres O8, verdicts §4. Le témoin C2′(a) — récurrence de Miller corrigée (facteur figé avant mutation, amorce d'ordre 1) vs série, barre 1e-12 — est **verbatim V1.1** (validé à 6.11e-16 le 28/08, RESULTAT_FORCE_V1_1.md §1).

### Ce qui change (DEUX choses, et elles seules)

**Changement 1 — sous-condition (b) : identité paire.** L'identité déposée en V1.1 §0.2(b) (« J₀ + 2Σ_{n≥1}Jₙ = 1 ») est **fausse** : elle omet la parité J₋ₙ = (−1)ⁿJₙ. Démonstration consignée dans le dépôt (RESULTAT_FORCE_V1_1.md §5, reproduite ici) :

> De e^{(a/2)(t−1/t)} = Σ_{n=−∞}^{+∞} Jₙ(a)tⁿ, en t = 1 : Σ_{n=−∞}^{+∞} Jₙ(a) = 1 ; avec J₋ₙ = (−1)ⁿJₙ, Jₙ + J₋ₙ = Jₙ(1+(−1)ⁿ) = 2Jₙ (n pair) ou 0 (n impair). **Donc J₀(a) + 2Σ_{k≥1} J₂ₖ(a) = 1 — ordres pairs uniquement.**

**(b) corrigé** : S_pair = J₀ + 2Σ_{k=1}^{5} J₂ₖ = 1 à **1e-9** près (a ∈ {0.1, 0.2}, n ≤ 11 ⇒ k ≤ 5 ; reste de troncature : J₁₂(0.2) ≈ 2e-17, invisible à la barre — prédiction ex ante).

**Changement 2 — sous-condition (c) : étiquette corrigée.** V1.1 enregistrait la valeur **post-normalisation** (9.975e-01), étiquetée à tort « brut ». La fonction de récurrence retourne désormais un couple **(table, J₀_brut)** où J₀_brut = ∏_{n=1}^{n_max}(2n/a) avant normalisation ; le contrôle (c) porte sur ce brut, barre **≤ 1e23** (aucun débordement flottant ; valeur attendue ≈ 8e21 pour a=0.1, n_max=31 — prédiction ex ante).

**Toute autre différence entre `verif_force_v1_2.py` et `verif_force_v1_1.py` est interdite** (en-tête, chemins et bannière exceptés).

---

## §1–§2. Objets, registres, familles, contrôles

Verbatim V1.1 (donc V1), sous réserve des deux changements ci-dessus : C0a (mtime), C0b (1e-15), C1 (1e-15), **C2′ = (a) 1e-12 ∧ (b) identité paire 1e-9 ∧ (c) J₀_brut ≤ 1e23**, C3 (1e-15), C4 (1e-12), C5 (G\* registre, 1e-12), C6 (1e-9), C7 (no-wrap). **Un seul échec ⟹ REFUTE, exit 1 — aucun sauvetage.**

## §3. Échelle de verdicts (gelée ex ante, verbatim V1)

V+ FORCE_FORME_FERMEE (exit 0) / V2 FORCE_FORME_PARTIELLE (exit 0) / V3 REFUTE_FORCE_SANS_FORME (exit 1) / V4 REFUTE (exit 1).

## §4. Interdictions (I1–I5) et honnêteté

Verbatim V1.1 §5–§6, plus : V1 et V1.1 restent consignés comme deux REFUTE — V1.2 ne les efface pas ; il ferme (ou non) le guichet avec l'appareil enfin droit.

## §5. Reproductibilité

`python verif_force_v1_2.py` → verdict + `resultat_force_v1_2.json`. Entrées : ce dépôt, `DEPOT_FORCE_V1.md`, registre O9 (G\* = 0.3232880100102466).

---

*Dépôt gelé. La suite (script, exécution, résultat) sera postérieure à ce mtime.*
