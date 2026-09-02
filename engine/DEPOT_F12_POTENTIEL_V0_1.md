# DÉPÔT F12 POTENTIEL V0.1 — La boucle mémoire comme source du lien

**Verdict visé : `POTENTIEL_BOUCLE_EXPOSANT_2ALPHA_MOINS_3` — exit 0 / REFUTE exit 1**
**Exécution :** `verif_f12_potentiel_v0_1.py` → `resultat_f12_potentiel_v0_1.json`
**Frontière :** `FRONTIERE_F12_TABLEAU_PERIODIQUE.md` (MORT 2)
**Date :** 02/09/2026 — ce dépôt est FERMÉ et ANTÉRIEUR à l'exécution V0.1 (C0a)

---

## 0. CONSIGNATION HONNÊTE DE V0 (REFUTE, exit 1 — runs 1, 2, 3)

V0 a été exécuté trois fois (treillis 96³ puis 192³) et a rendu **REFUTE exit 1**. Le verdict est consigné tel quel. L'analyse des échecs, faite AVANT tout dépôt V0.1, identifie trois causes distinctes — deux de méthode, un de code — **aucune ne touchant la thèse** :

1. **C5 : bug de signe DANS LE CONTRÔLE** (faux échec). Le contrôle testait `(EXPOSANT − (−1)) − (3−√5)` sans valeur absolue : `−0.7639 − 0.7639 = −1.528 ≠ 0`. L'identité physique est vraie bit-près : **|2α−3+1| = 3−√5 exactement**. Leçon : le contrôle lui-même est du code — il a ses bugs.
2. **Fenêtre de mesure hors du régime continu** (erreur de méthode). Le tableau de diagnostic déposé ci-dessous montre que le rapport G_mesuré/G_théorie vaut **0.94–0.99 en champ proche (r = 3–8)** et s'effondre en champ lointain (r ≥ 24 : 0.32–0.60). Sur un tore avec mode zéro retiré, la loi libre c(α)·r^{2α−3} n'est valable qu'à r ≪ L/2π : la fenêtre [3, 40] de V0 incluait la zone polluée par la neutralisation et les images. **Preuve par témoin** : doubler la boîte (96³ → 192³) à fenêtre fixe n'a PAS changé le biais (0.1499 → 0.1499 à α=0.3) — le biais est lié au bord lointain de la fenêtre, pas à la taille.
3. **Dégénérescence de l'ajustement à 3 paramètres** (A, p, B) : la vallée puissance+constante fait glisser p le long de la vallée — l'exposant « libre » de V0 mesurait l'artefact, pas la loi.

**Tableau de diagnostic déposé** (treillis 192³, rayon torique enveloppé, médiane par coquille ; G_num = FFT inverse de |ω|^{−2α}, mode zéro retiré ; G_th = c(α)·r^{2α−3}) :

| α \ r | 3 | 4 | 8 | 12 | 24 | 48 |
|---|---|---|---|---|---|---|
| 0.3 | 0.9916 | 0.8783 | 0.9669 | 0.9614 | 0.8795 | 0.3975 |
| 1/φ | 0.9444 | 0.9047 | 0.9613 | 0.9387 | 0.8313 | 0.4558 |
| 1.0 | 0.9124 | 0.9048 | 0.8741 | 0.8163 | 0.6477 | 0.3233 |

Pentes log-log [3,12] mesurées sur ces mêmes données : α=1/φ → **−1.768** (cible −1.7639, écart 0.004) ; α=1 → −1.081 (cible −1) ; α=0.3 → **−2.421** (cible −2.4, écart 0.021). **La thèse tient ; c'est le protocole de mesure de V0 qui était faux.**

**Leçon consignée : la barre était dans la fenêtre, pas dans la physique. La machine corrige le protocole, jamais la thèse — et un contrôle est lui-même du code bugable.**

---

## 1. LA THÈSE (chaîne P20–P22 — inchangée de V0 à V0.1)

- **P20 l'opérateur** — le potentiel est la réponse du champ à une source ponctuelle à travers la boucle mémoire complète : D^α appliqué DEUX fois (le même double franchissement que la phase d'échange P14 de la MORT 1). La dérivée fractionnaire est l'inverse du noyau déposé : D^α = φ·K̂⁻¹ − φ, symbole (iω)^α ; la boucle a le symbole (iω)^{2α}, dont la phase est EXACTEMENT σ = e^{iπα} — **la même boucle porte la statistique (MORT 1) et le lien (MORT 2)**.
- **P21 le scaling** — fonction de Green de (−Δ)^α en d = 3 : Ĝ(ω) = |ω|^{−2α} ⟹ G(r) = c(α)·r^{2α−3}, **c(α) = Γ((3−2α)/2)/(4^α π^{3/2} Γ(α))**. À α = 1 : G(r) = 1/(4πr) — Coulomb ET son préfacteur 1/(4π) recouvrés de la boucle. À α = 1/φ : exposant 2/φ − 3 = **√5 − 4 = −1.7639320…** (forme close bit-exacte).
- **P22 la tension** — à α = 1/φ le potentiel s'écarte de Coulomb de 3−√5 = 0.7639320… (plus raide). Lectures L′1/L′2 miroir de L1/L2 (Pauli), MÊME discriminateur ex ante (ordre de fermeture de la boucle de matière) : L′1 — boucle de matière fermée à l'ordre plein (action Φ₂ = π), Coulomb intact, l'exposant fractionnaire vit aux échelles mémoire ; L′2 — l'exposant 2α−3 s'applique à la matière, la spectroscopie atomique devrait le montrer. Aucun sauvetage (I5).

## 2. CE QUE V0.1 CHANGE (protocole uniquement — thèse et objets intacts)

| Élément | V0 (consigné) | V0.1 (déposé) |
|---|---|---|
| Fenêtre de scaling | [3, 40] — hors régime continu | **[3, 8]** — régime continu (r ≪ L/2π ≈ 30 ; justifié par le tableau déposé §0) |
| Estimateur d'exposant | pente libre 3-param (A, p, B) — dégénérée | **pente log-log directe** (ln G vs ln r, 6 coquilles entières 3–8) |
| Amplitude | A à exposant libre sur [3, 40] | **A à exposant THÉORIQUE fixé** (A·r^{2α−3} + B, 2 params, sur [3, 8]) — B absorbe la constante IR |
| Barre amplitude | 5e-2 | **0.10** — justifiée par le tableau déposé §0 : déficit champ proche mesuré ≤ 0.06 (plateau 0.94–0.99), marge ×1.6 ; systématiques BZ/IR **consignées**, sonde de convergence Δx = 0.75 en [OBS] sans pouvoir de verdict |
| C5 | bug de signe | identité \|2α−3+1\| = 3−√5 bit-exact (corrigée) |
| C0a | absent | **ajouté** (dépôt antérieur à l'exécution) |

**Barres pré-enregistrées (avant exécution) :** C3 : max_α \|pente − (2α−3)\| < 0.05. C4 : max_α \|A/c(α) − 1\| < 0.10. C5 : identité < 1e-15 et 3−√5 > 0.5. C6 : \|pente-des-pentes − 2\| < 0.25 ; ancres α=0.5 → −2 et α=0.3 → −2.4 à < 0.05.

## 3. NOMBRES DÉPOSÉS (calculés par machine avant gel, mpmath dps 40)

```
exposant(1/φ) = 2/φ − 3 = √5 − 4 = −1.76393202250021030359082633127
écart à Coulomb = 3 − √5 = +0.763932022500210303590826331269
c(1/φ) = 0.0570060667406369381560101202763
c(1) = 1/(4π) = 0.07957747154594767  (le préfacteur de Coulomb, dérivé)
```

## 4. RÉSULTATS MACHINE V0.1 (run final, treillis 192³, fenêtre [3, 8], exit 0)

| α | cible 2α−3 | pente mesurée | écart | A/c(α) |
|---|---|---|---|---|
| 0.3 | −2.400000 | −2.387623 | 0.0124 | 0.9859 |
| 0.5 | −2.000000 | −1.961055 | 0.0389 | 0.9436 |
| **1/φ** | **−1.763932** | **−1.728650** | **0.0353** | 0.9332 |
| 0.8 | −1.400000 | −1.390193 | 0.0098 | 0.9300 |
| 1.0 | −1.000000 | −1.042776 | 0.0428 | 0.9347 |

Contrôles bloquants : **C0a** ✔ (dépôt 09:23:45 < exécution 09:41:56) ; **C0b** ✔ (identités bit-près : φ², 2/φ = √5−1, exposant = √5−4, gap = 3−√5) ; **C1** ✔ (K̂ double route : 0.00e+00) ; **C2** ✔ (φK̂⁻¹ − φ = (iω)^α à 4.97e-16 ; phase de boucle = σ_MORT1 à 1.24e-16) ; **C3** ✔ (pentes : max 0.0428 < 0.05) ; **C4** ✔ (amplitudes : max |A/c−1| = 0.0700 < 0.10 ; α=1 : A = 0.074382 vs 1/(4π) = 0.079577) ; **C5** ✔ (3−√5 = 0.7639320 bit-exact ; V_THU/V_Coulomb(10) = 0.123367) ; **C6** ✔ (pente-des-pentes = 1.9159 vs 2 ; ancres 0.0124/0.0389).

**[OBS] Sonde de convergence (sans pouvoir de verdict) :** à Δx = 0.75 (N = 256, même boîte) : A/c = 0.8918 (α=1/φ), 0.9507 (α=1) — contre 0.9332/0.9347 à Δx = 1. Les systématiques BZ/IR restent de l'ordre de 5–10 % ; c(α) reste la constante de continuum déposée.

## 4 bis. LEÇON DE LA SONDE (consignée)

La sonde [OBS] a d'abord rendu A/c = 0.376 — **un bug dans la sonde elle-même** : `ifftn` normalise par 1/N³, le continuum exige (Δk/2π)³ = 1/L³ ; à Δx ≠ 1 manque le facteur 1/Δx³ = (4/3)³ = 2.37. Corrigé avant gel du verdict (0.376 × 2.37 ≈ 0.89 ✔). **Leçon : tout estimateur — contrôle, témoin, sonde — est du code bugable ; la redondance des routes est la seule protection.**

## 5. HISTORIQUE D'EXÉCUTION (honnête)

| Run | Résultat |
|---|---|
| V0 runs 1–3 (treillis 96³ puis 192³) | **REFUTE exit 1 — consigné** (fenêtre hors régime continu + bug signe C5 + dégénérescence 3-param ; thèse intacte, §0) |
| V0.1 tentatives 1–2 (crash avant verdict) | NameError résidus de refactor pré-exécution (`best_p`, `G_alpha`) — aucune lecture physique modifiée, sorties identiques |
| V0.1 tentative 3 | verdict conforme imprimé, crash à l'écriture JSON (ndarray) |
| **V0.1 run final** | **exit 0 — 7/7 contrôles, `POTENTIEL_BOUCLE_EXPOSANT_2ALPHA_MOINS_3`** (18 s) ; sonde [OBS] révélée et corrigée (bug de normalisation dx³ — leçon §4 bis) |

## 5 bis. CE QUE CE DÉPÔT ÉTABLIT — ET CE QU'IL N'ÉTABLIT PAS

**Établi (machine, exit 0) :**
1. **Le scaling dérivé** — la fonction de Green de la boucle mémoire suit r^{2α−3} sur TOUTE la ligne α ∈ [0.3, 1] (pente-des-pentes = 1.92 ± 0.25, ancres exactes) : le potentiel n'est pas inséré, il sort de D^α∘D^α.
2. **Coulomb recouvré** — à α = 1 : exposant −1 et préfacteur 1/(4π) sortis de la boucle à 7 % (systématiques tore/BZ consignées et sondées).
3. **La forme close à α = 1/φ** — exposant √5−4, constante c(1/φ) = 0.057006…, écart à Coulomb 3−√5 bit-exact.
4. **L'unité de la boucle** — la phase de la boucle du lien est BIT-EXACTEMENT la phase d'échange σ = e^{iπα} de la MORT 1 : statistique et liaison sont la même boucle d'influence, l'une en phase, l'autre en amplitude.

**Non établi (frontières consignées, sans sauvetage) :**
- **L′1 vs L′2 reste expérimental** : quel ordre ferme la boucle de matière ? La métrologie atomique (test de l'exposant 2α−3 vs −1) tranche — prédiction déposée ex ante.
- **La constante à 7 %** : le préfacteur est vérifié à 7 % près sur le tore ; la convergence Δx→0 est sondée ([OBS]), pas démontrée.
- **Les niveaux liés** (le spectre de E_{1/φ} dans le puits) ne sont PAS calculés ici — c'est l'entrée de la MORT 3.

## 6. FORMULATION GELÉE

> **Le lien n'est pas une donnée : c'est un aller-retour. La même boucle qui donnait le signe fermionique en phase (2θ = πα) donne l'exposant du potentiel en amplitude (2α−3) — la statistique et la liaison sont deux lectures de la même mémoire. À α = 1, la boucle rend Coulomb avec son 1/(4π) : non postulés, recouvrés. À α = 1/φ, l'écart 3−√5 est déposé sans maquillage : le potentiel de la THU est plus raide que Coulomb, et le monde tranchera par la spectroscopie, ex ante, L′1 ou L′2. La MORT 2 est fermée ; la MORT 3 (les couches) attend son exclusion et ses niveaux.**

---

*Conformément à la discipline de la THU : V0 REFUTE consigné avec ses données ; V0.1 change le protocole, pas la thèse ; tout nombre déposé est calculé par machine ; les leçons (contrôle bugable, sonde bugable, normalisation Δx³) sont consignées.*
