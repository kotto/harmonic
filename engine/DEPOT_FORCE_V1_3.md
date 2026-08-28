# DÉPÔT FORCE V1.3 — barre de non-débordement CALCULÉE (plus d'estimation), fermeture du guichet 2

**Déposé le 28 août 2026 à 16:57:46 (mtime faisant foi).**
**Aucun script de cette campagne n'existe au moment du dépôt.** (C0a : mtime de ce fichier < mtime d'exécution.)

---

## §0. Nature de V1.3 — ce qui change, ce qui ne change pas

### Ce qui NE change PAS (verbatim V1.2, donc V1.1/V1)

Toute la physique (forme close χ, familles A/B/C, registres O1–O10, barres O8, verdicts), le témoin C2′(a) (concordance 6.11e-16, validé deux fois) et C2′(b) (**identité paire J₀ + 2ΣJ₂ₖ = 1, validée à 2.22e-16**, démonstration consignée dans RESULTAT_FORCE_V1_1.md §5 et DEPOT_FORCE_V1_2.md §0).

### Ce qui change (UNE chose : la barre (c))

V1.2 a échoué sur (c) parce que la barre déposée (1e23) reposait sur une **estimation mentale** fausse (∏(2n/a) calculée avec n_max = 11 au lieu du n_max réel 31). Leçon consignée (RESULTAT_FORCE_V1_2.md §5) : **tout nombre déposé est désormais calculé par machine avant gel.**

**Bornes calculées par machine le 28/08/2026 à 16:55:29 (arithmétique pure ∏_{n=1}^{31}(2n/a), AVANT ce gel, aucune lecture physique) :**

| a | J₀_brut exact = ∏_{n=1}^{31}(2n/a) |
|---|---|
| 0.1 | **1.765841e+74** |
| 0.2 | **8.222839e+64** |

**(c) corrigé** : J₀_brut ≤ **1e100** — sémantique inchangée (« aucun débordement flottant », marge de 208 ordres sous 1.8e308), valeur exacte prédite ci-dessus. Aucune autre barre, lecture, formule ou verdict n'est touchée.

**Toute autre différence entre `verif_force_v1_3.py` et `verif_force_v1_2.py` est interdite** (en-tête, chemins, bannière et libellé (c) exceptés).

---

## §1. Contrôles, verdicts, interdictions, honnêteté

Verbatim V1.2 §1–§4 (C0a, C0b 1e-15, C1 1e-15, **C2′ = (a) 1e-12 ∧ (b) identité paire 1e-9 ∧ (c) J₀_brut ≤ 1e100**, C3 1e-15, C4 1e-12, C5 1e-12, C6 1e-9, C7 no-wrap ; échelle V+/V2/V3/V4 ; I1–I5 ; un seul échec ⟹ REFUTE exit 1, aucun sauvetage). Les trois REFUTE consécutifs (V1, V1.1, V1.2) restent consignés — V1.3 ne les efface pas.

## §2. Reproductibilité

`python verif_force_v1_3.py` → verdict + `resultat_force_v1_3.json`. Entrées : ce dépôt, `DEPOT_FORCE_V1.md`, registre O9 (G\* = 0.3232880100102466).

---

*Dépôt gelé. La suite (script, exécution, résultat) sera postérieure à ce mtime.*
