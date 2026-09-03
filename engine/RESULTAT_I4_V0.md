# RÉSULTAT I4 V0 — la montée vers −¼F² est FERMÉE : le facteur ¼ sort des identités de Bessel, jamais écrit à la main

```
══════════════════════════════════════════════════════════════════════════════
  VERDICT : V+ I4_MONTEE_QUART_FERMEE          exit 0
  12/12 contrôles OK — D1(a–c) OK — D2a OK — D3a OK
  FRONTIÈRE_I4_V0.md commit 459b5ba (gelée AVANT tout script, C0a)
  Exécution : 03/09/2026 11:46:29 — antériorité frontière 2 515 s
══════════════════════════════════════════════════════════════════════════════
```

**Auteur :** Alain Kotto (Univers-Holistique)
**Statut :** Résultat — campagne I4 V0 exécutée sous barres gelées (aucun sauvetage, aucun chiffre calculé à la main)
**Autorité :** `FRONTIERE_I4_V0.md` (commit 459b5ba, 03/09 11:04:33) — thèse Q1–Q5, barres C0a–C10 / D1a–c / D2a–b / D3a–b

---

## 1. LE VERDICT

**La dette nommée trois fois est payée.** INTERACTION D3 V0 (§5) — *le terme continu est une campagne
séparée* ; D3 DYNAMIQUE (frontière §6.2) — *−¼F² reste campagne séparée (I4)* ; F13 §5 — *pas de
−¼F² dérivé*. La campagne I4 ferme la montée au niveau visé (frontière §0) :

> **Le facteur ¼ du terme continu est une identité de Bessel exacte de la graine déposée —
> S₂(a) = Σₘ m(m+2)·J_{m+2}(a)·J_m(a) = a²/4 — et le couplage de la famille paire j=2 prend,
> à la tranche α=1 du poids unique, la forme close exacte**
>
> **I₁₂ = −(a²k²/4N)·[4ω₁ω₂ + k²(a²+3)]**  (famille adiabatique ω₂ = ω₁+2k)
>
> **vérifiée chiffres à chiffres par la machine, sans qu'aucun ¼ ne soit écrit dans la route.**

Le critère de réfutation (OUVERTURE §6.2, verbatim frontière §0-bis) — *si le terme doit être écrit
à la main, consigner non-émérgé → REFUTE* — **n'est pas déclenché** : le formulaire n'existe dans le
code QUE comme prédiction falsifiée ; les sommes S₂, A₂, V₂, W₂ sont mesurées (C3), et leur accord
aux formes closes (1.67e-16) est un contrôle séparé de la route de couplage.

## 2. CONTRÔLES BLOQUANTS — 12/12 (barres gelées, frontière §3)

| # | Contrôle | Valeur mesurée | Barre | Statut |
|---|---|---|---|---|
| C0a | antériorité frontière (mtime 11:04:33 < exec 11:46:29) | 2 515 s | — | OK |
| C0b | φ² = φ+1 | 0.0 | 1e-15 | OK |
| C1 | K̂ double route (complexe/réelle + branche) | 3.3e-16 | 1e-12 | OK |
| C2 | Bessel double route (série×récurrence / identité paire) | 1.1e-16 / 0.0 | 1e-12 / 1e-9 | OK |
| C3 | **identités Q1** (S₂=a²/4, A₂=−a²/4, V₂=a²/4, W₂=(a⁴−a²)/4, S₁=S₃=W₁=0, 5×a) | 1.67e-16 | 1e-15 | OK |
| C4 | Z₂^zj vs forme (sommes MESURÉES), 48 lignes | 2.0e-15 | 1e-12 | OK |
| C5 | réseau = −forme/N, 48 lignes | 2.7e-15 | 1e-12 | OK |
| C6 | silence impaire j=1,3 (8 lignes) | 6.6e-20 | 1e-15 | OK |
| C7 | ratio adiabatique noyau (6 lignes) | pire \|r−1\| = 1.17e-2 | [0.95, 1.05] | OK |
| C8 | ratio boucle α=1/φ (6 lignes) | pire \|r−1\| = 8.9e-3 | [0.95, 1.05] | OK |
| C9 | no-wrap \|ω±nk\| ≤ 25.6 | 24.0 | ≤ 25.6 | OK |
| C10 | filiation λ_loop = λ_kernel² (grille + scalaires, α=1/φ et α=1) | bit-exact | 0 | OK |

## 3. CONSÉQUENCES FALSIFIABLES — toutes dans les barres (frontière §4)

### D1 — le facteur ¼ émerge (montée vers −¼F², famille j=2)

| # | Conséquence | Valeur | Barre | Statut |
|---|---|---|---|---|
| D1a | montée exacte : I₁₂/(−𝔽₁𝔽₂/N) = 1 + k²(a²+3)/(4ω₁ω₂), 8 lignes | pire rel = **2.4e-15** | 1e-12 | OK |
| D1b | forme famille : I₁₂ = −(a²k²/4N)[4ω₁ω₂ + k²(a²+3)] | pire rel = **2.4e-15** | 1e-12 | OK |
| D1c | limite adiabatique : ratio ∈ [0.95, 1.10] à k ≤ 0.2 | pire \|r−1\| = 8.9e-2 (r max 1.0889) | [0.95, 1.10] | OK |

Lignes D1a (le ratio machine ÉGALITE la forme close, 𝔽_i = a·k·ω_i) :

| (a, k, ω₁) | ratio mesuré | prédiction 1 + k²(a²+3)/(4ω₁ω₂) | rel |
|---|---|---|---|
| (0.1, 0.1, 0.5) | 1.021500000000 | 1.021500000000 | 1.8e-15 |
| (0.1, 0.2, 0.5) | 1.066888888889 | 1.066888888889 | 1.0e-15 |
| (1.0, 0.1, 0.5) | 1.028571428571 | 1.028571428571 | 1.6e-15 |
| (1.0, 0.2, 0.5) | 1.088888888889 | 1.088888888889 | **0.0** |
| (1.0, 0.2, 1.0) | 1.028571428571 | 1.028571428571 | 2.0e-15 |

### D2 — structure quadratique (le −¼F² est pair)

| # | Conséquence | Valeur | Statut |
|---|---|---|---|
| D2a | familles impaires (j=1,3) EXACTEMENT muettes à α=1 — couplage purement quadratique (signature −¼F², pas −F) | 6.6e-20 (8 lignes) | OK |
| D2b | canal orthogonal Im⟨δ₁,δ₂⟩ = −sin(πj/2)·Re Z_j/N ≠ 0 — non-observable I₁₂ | rel ≤ 1.6e-12 (8 lignes) | [OBS] |

### D3 — hors α=1 : montée générique, pas de fermeture

| # | Conséquence | Valeur | Statut |
|---|---|---|---|
| D3a | noyau + boucle α=1/φ : le lead conjugué Re[conj W′(ω₁)]W′(ω₂) tient (ratios 0.988–1.009) | pire \|r−1\| = 1.17e-2 | OK |
| D3b | pas de formulaire polynomial hors α=1 (écart croît avec k : 1.2e-2 à k=0.3) — la fermeture est la tranche α=1 | — | [OBS] |

**Registres fermés traversés** : C3 identités à a=1.0 : S₂ mesuré 0.25000000000000006 vs 0.25 ;
A₂ −0.24999999999999994 vs −0.25 ; W₂(1.0) = 0 (identité (a⁴−a²)/4) ; S₁ = S₃ = W₁ = 0 — le ¼
apparait à la 16ᵉ décimale près comme identité, sur les cinq valeurs de a.

## 4. HISTOIRE DES RUNS (défauts d'estimateur consignés avant verdict — leçon V1.2)

- **Run 1 → faux V4_REFUTE (exit 1), 4 échecs, TOUS défauts d'estimateur du script, physique
  intacte, barres gelées inchangées :**
  1. **C7/C8 — pont /N manquant** (leçon V1.2, 4ᵉ occurrence) : le lead adiabatique prédit Z₂ au
     niveau amplitude, le réseau mesure I₁₂ = Re⟨δ₁,δ₂⟩ au niveau norme ; pire \|r−1\| = 0.998 ≈
     1 − 1/512 trahissait exactement le facteur N. Correction : lead/N.
  2. **D1c — mauvaise bande** : le code appliquait la bande C7/C8 [0.95, 1.05] au lieu de la bande
     gelée D1c [0.95, 1.10] (frontière §4) ; le ratio 1.0889 était DANS la barre.
  3. **D3a** héritait du défaut C7/C8.
  4. **D2b [OBS] — signe impair** : prédiction −Re Z_j/N uniforme au lieu de
     Im⟨δ₁,δ₂⟩ = −sin(πj/2)·Re Z_j/N (j=3 → +Re Z₃/N) ; confirmé à rel ≤ 1.6e-12 après correction.
- **Run 2 → V+_I4_MONTEE_QUART_FERMEE exit 0** (le présent verdict) — aucun changement de barre,
  aucune valeur close ajoutée aux routes : corrections d'estimateur uniquement.

## 5. ÉTABLI / NON-ÉTABLI (honnêteté — frontière §6)

**Établi (machine, sous barres gelées) :**
1. Le facteur ¼ de la famille paire j=2 est une **identité de Bessel exacte** (C3 : 1.67e-16) — il
   n'est écrit nulle part dans la route de couplage ; il sort des sommes mesurées.
2. À α=1, le couplage des porteurs jaugés prend la **forme close exacte pour tout k**
   (I₁₂ = −(a²k²/4N)[4ω₁ω₂ + k²(a²+3)] sur la famille adiabatique) — conséquence du polynôme exact
   Δₙ^loop = −2ωnk − (nk)² (filiation P36, aucun reste de Taylor).
3. La **montée** I₁₂/(−𝔽₁𝔽₂/N) = 1 + k²(a²+3)/(4ω₁ω₂) est exacte (2.4e-15) — le couplage tend vers
   −𝔽₁𝔽₂/N dans la limite adiabatique, avec le ¼ sorti de l'identité.
4. Le couplage est **purement quadratique** à α=1 (impaire muette 6.6e-20) — signature F², pas F.
5. Hors α=1 (noyau, boucle α=1/φ), seule la **structure adiabatique générique** tient (lead
   conjugué, ratios 0.988–1.009 à k ≤ 0.3) — pas de formulaire polynomial : le discriminant
   Maxwell/mémoire se relit dans le couplage.

**Non établi (consigné, hors périmètre) :**
1. **Pas de lagrangien continu dérivé** : I4 ferme la structure du couplage discret en limite
   adiabatique — pas la dérivation de −¼F² d'une fonctionnelle sur un champ A(x) continu, pas le
   système 3+1D covariant avec sources (D4/JAUGAGE maintenus).
2. **La lecture « Maxwell » reste une analogie de forme** (quadraticité, facteur ¼, limite
   adiabatique, 𝔽 = a·k·ω défini à la frontière Q4) — déposée comme telle, pas une identification
   d'équations.
3. **Le régime mémoire α=1/φ ne ferme pas** en formulaire (D3b [OBS]) — consigné, pas réfuté.
4. **Ancres internes** (a, k, ω de la famille fermée) — auto-cohérence, pas mesure de laboratoire.

## 6. REPRODUCTIBILITÉ

- Script : `verif_i4_v0.py` (autonome, sections O1–O7 verbatim + sections I4), sortie
  `resultat_i4_v0.json`. Durée : 1.11 s. Python 3.x + NumPy (horodatés au JSON).
- Aucune graine aléatoire — FFT, séries de Bessel et sommes déterministes.
- Ordre C0a : frontière commitée **459b5ba** (11:04:33) AVANT création du script (exec 11:46:29,
  antériorité 2 515 s au JSON).
- Chaîne : OUVERTURE_D3_DYNAMIQUE_V0.md (§6.2) → DEPOT_INTERACTION_D3_V0.md (§5) →
  FRONTIERE_I4_V0.md (459b5ba) → verif_i4_v0.py → resultat_i4_v0.json → RESULTAT_I4_V0.md (ce doc).

## 7. CE QUE FERME LE VERDICT

La chaîne de l'identité mère est désormais **continue de bout en bout au niveau du couplage** :
noyau K̂ = φ/((iω)^α+φ) → boucle λ_loop = λ_kernel² (C10 bit-exact) → propagation coulée à α=1
(D3 DYNAMIQUE, V+) → **couplage quadratique entre porteurs jaugés avec le facteur correct émergeant
des identités de Bessel** (I4, V+). L'objection « Maxwell mis à la main quelque part » perd son
dernier point d'attache au niveau discret : le ¼ vit dans S₂ = a²/4, la quadraticité dans la parité
de la structure de jauge, la limite continue dans le polynôme exact du poids.

Le trou suivant est consigné sans détour (§5) : entre cette loi de couplage sur treillis et
l'équation de Maxwell 3+1D covariante avec sources, il reste le lagrangien continu (fonctionnelle),
le dictionnaire μ↔ω (D4) et la quantification — chacun nommé, chacun hors périmètre I4.

---

*Le facteur ¼ a sorti des identités — il n'y est jamais entré. La montée est fermée au niveau visé.*
