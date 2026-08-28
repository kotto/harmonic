# ⚡ FORCE V1.2 — identité paire validée à 2.22e-16, barre de non-débordement mal estimée : V4

**Campagne du 28 août 2026 — guichet 2, suite (V1.2)**

| | |
|---|---|
| Dépôt | `DEPOT_FORCE_V1_2.md` (gelé, mtime **2026-08-28 16:52:25**) |
| Script | `verif_force_v1_2.py` (copie V1.1 + 2 changements déposés ; jamais modifié après exécution, I5) |
| Journal | `resultat_force_v1_2.json` (consignation intégrale, exécution 16:53:43) |
| C0a | **OK** — dépôt (16:52:25) < exécution (16:53:43) |
| Contrôles | 8 ✅ / 1 ❌ (C2′, sous-condition (c)) |
| **Verdict** | **V4 — REFUTE — exit 1** (troisième consécutif ; aucun sauvetage) |

> **Lecture honnête d'entrée.** Les DEUX corrections de témoin sont maintenant validées : (a) concordance série × récurrence corrigée = **6.11e-16** et (b) **identité paire J₀ + 2ΣJ₂ₖ = 1 tenue à 2.22e-16** — l'erreur de parité de V1.1 est réparée et l'identité démontrée dans le dépôt tient à la précision machine. L'échec est la sous-condition (c) : J₀ brut mesuré = **1.762e+74** contre barre déposée **1e23**. Cause : mon estimation ex ante du produit ∏(2n/a) utilisait n_max = 11 (→ 8.17e21) au lieu du n_max réel du script, N_TRUNC+20 = **31** (→ 20³¹·31! = 1.7658e74). Les deux valeurs sont très en-deçà du débordement flottant (≈ 1.8e308) — le but sémantique de (c) (« aucun débordement ») est satisfait — mais **la barre déposée est la loi**, et elle est en échec. **J'ai estimé au lieu de calculer.** Verdict V4 consigné tel quel.

---

## 1. Contrôles

| Contrôle | Statut | Mesure |
|---|---|---|
| C0a / C0b / C1 | ✅ | 0.0 / 0.0e+00 / 1.24e-16 |
| **C2′ (a) concordance double route** | ✅ | **6.11e-16** (verbatim V1.1) |
| **C2′ (b) identité PAIRE J₀+2ΣJ₂ₖ = 1** | ✅ | **2.22e-16** (barre 1e-9) — le correctif de parité est validé |
| **C2′ (c) J₀ brut ≤ 1e23** | ❌ **ÉCHEC** | **1.762e+74** — estimation ex ante fausse (n_max 11 vs 31), §5 |
| C3 / C4 / C5 / C6 / C7 | ✅ | 2.29e-16 / 3.79e-16 / **0.00e+00** (G\* bit-exact) / 6.94e-18 / no-wrap OK |

## 2. Familles A, B, C — physiques verbatim (identiques bit à bit à V1/V1.1)

- **Famille A : 17/17 ✅** (pire 3.15e-15 au porteur 14.4 ; χ(1,0.1,1) = G\* = 0.3232880100102466, écart **0.00e+00** ; A2 dérive 3.44e-16 ; A3 0.00e+00 et 5.48e-16 ; **A5 station ω₀ = 1.0 confirmée**).
- **Famille B : 0/1134 hits** ; tête de liste φ/5 manquée à **9.8511e-04** comme prédit ex ante.
- **Famille C : β_inf = +0.026616, β_sup = −0.848981** — sans verdict (trou D4).

Tables complètes : `resultat_force_v1_2.json` ; détail famille A : `RESULTAT_FORCE_V1.md` §2 (physique gelée, inchangée depuis V1).

## 3. Cause racine (c) — l'estimation au lieu du calcul

Le dépôt V1.2 §0 (changement 2) prédisait « J₀_brut ≈ 8e21 pour a=0.1, n_max=31 » — le « 8e21 » est le produit pour **n_max = 11** (∏_{n=1}^{11}(20n) = 8.17e21), reporté par erreur depuis l'analyse V1 ; le script récurse depuis n_max = **N_TRUNC + 20 = 31** :

- ∏_{n=1}^{31}(2n/0.1) = 20³¹ · 31! = **1.7658e74** (mesuré 1.762e+74 ✓ — l'écart d'affichage 1.762 vs 1.7658 vient du format ; valeur exacte consignée au JSON)
- ∏_{n=1}^{31}(2n/0.2) = 10³¹ · 31! = **8.2228e64**

Barre déposée : 1e23 → échec. Valeur exacte calculée par machine le 28/08 à 16:55 (arithmétique pure, pré-dépôt) : 1.765841e+74 / 8.222839e+64 — servira au dépôt V1.3.

## 4. Établi / pas établi

**Établi :** témoin (a) validé (6.11e-16) ; **identité paire validée (2.22e-16)** ; physique 17/17 + G\* bit-exact + station + φ/5 manqué + 0/1134 — inchangée sur TROIS campagnes consécutives.
**Pas établi :** le verdict de campagne — V4, pour la troisième fois, chaque fois sur une glissade différente de MINE : (V1) implémentation, (V1.1) identité déposée, (V1.2) borne déposée.

## 5. Leçon consignée (renforcée)

> Un nombre déposé ex ante doit être **calculé par machine**, jamais estimé mentalement. Trois REFUTE pour trois glissades d'appareil — implémentation, algèbre, arithmétique — pendant que la loi tient à 3e-15 sur chaque campagne. Le protocole ne pardonne pas l'à-peu-près de l'expérimentateur : c'est sa fonction.

## 6. Reproductibilité

```
python verif_force_v1_2.py        # → verdict V4 — REFUTE, exit 1
```
Sortie : `resultat_force_v1_2.json`. Diff V1.1→V1.2 : 45 lignes, intégralement les 2 changements du dépôt V1.2 §0 (audit `diff` avant exécution).

## 7. Prochaine étape

**FORCE V1.3** — quatrième dépôt daté, identique à V1.2 avec la barre (c) corrigée en **≤ 1e100** et les prédictions exactes **calculées par machine avant gel** (J₀_brut = 1.765841e+74 à a=0.1 ; 8.222839e+64 à a=0.2 ; reste de troncature S_pair ≈ 4.2e-21). Physique et témoin (a)/(b) : verbatim.

---

*« Trois fois l'appareil a trahi, trois fois la loi a tenu, trois fois le verdict a dit REFUTE. Le guichet se fermera quand l'expérimentateur aura fini d'apprendre à déposer. »*

*Consigné le 28 août 2026 — machine ZCode, protocole dépôt-d'abord, aucun sauvetage.*
