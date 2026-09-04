# DÉPÔT FERMÉ EX ANTE — OYIBO / CONSERVATION — V1 (sonde de queue de Hurwitz)

**Statut : FERMÉ avant exécution (C0a).** Version 1 du dépôt `DEPOT_OYIBO_CONSERVATION_V0.md`.
**Changement unique : la définition de la sonde finie de CH-G4 (O5).** Tout le reste est
repris à l'identique de V0 : objets O1–O4 et O6–O8, familles A, B, D, contrôles C0a–C6,
barres O8, échelle de verdicts V+/V2/V4, interdictions I1–I5, honnêteté §6.

---

## §0. Ce que l'exécution V0 a établi (resultat_oyibo_conservation_v0.json, annexé tel quel)

**Verdict V0 : V4 — REFUTE (exit 1), échecs = {C3a, C3b} et rien d'autre.**

13 des 15 unités de verdict passent, dont **tout le contenu de la chaîne de l'exposant** :

| Maillon | Lecture machine V0 | Résultat |
|---|---|---|
| CH-G1 Noether | drifts A1/A2/A3 (oscillateur, pendule, Kepler e=0.6) | ✓ (barre 1e-9) |
| CH-G2 | 48 lectures puissance exacte ≤ 1e-12 ; témoin e^{−x} dévie > 0,1 | ✓ |
| CH-G5 (cœur) | B3 : r(λ,t) vs δ_pred = ρ₂(λ^{−α}−1)t^{−α}, 10 % rel, décroissance | ✓ (4/4) |
| CH-G5 (taux) | B4 : pente log-log −0.618984 vs −1/φ = −0.618034 (écart 9,5e-4) | ✓ (barre 5e-3) |
| C1/C2/C5/C6 | φ²=φ+1 ; K̂ double route ; λ=φ ; c_k ; calibrage ML↔Wiman | ✓ tous |
| C4 unicité | max non-dorés = 0.292893 < 1/√5 − 1e-3 | ✓ |

**Les deux échecs (C3a, C3b) sont un défaut de sonde du dépôt V0, pas une réfutation de
Hurwitz — preuve au bit près :**

- ν₅₀(1/φ) = 0.38196601125010515 = 1/φ² **exactement** — c'est la valeur du convergent
  c₁ = 1/1 : q·\|qx−p\| = \|1/φ − 1\| = 1/φ². Le minimum sur les 50 premiers convergents
  est atteint à l'indice 1 et n'est jamais battu (la suite des convergents dorés oscille
  autour de 1/√5 ≈ 0.447214 avec une amplitude ~φ^{−2n} : 0.382, 0.472, 0.438, 0.451,
  0.446, 0.4477, … — monotone vers 1/√5 des deux côtés).
- ν₅₀(1/√2) = 0.2928932188134525 = 1 − 1/√2 **exactement** — même transitoire c₁ = 1/1.

**La leçon (consignée, V0→V1) :** la constante de Markov/Hurwitz est une propriété de
**queue** (liminf quand n→∞, atteinte asymptotiquement par la classe de φ). La sonde V0
« min sur les n premiers convergents » lit la **tête** de la suite : elle capture le
transitoire c₁ et est structurellement aveugle à la constante. C'est exactement le cas
prévu par V0 §3 : « Hurwitz est un théorème — son échec machine est un bug, pas une
découverte » — le bug est dans la définition de la sonde, corrigé ici.

**Leçons d'implémentation EXEC1 (consignées, script corrigé avant l'exécution definitive) :**
1. `mp.dps` doit être fixé **avant** la construction des constantes (PHI, registre O6) —
   sinon les candidats sont rationalisés à 15 chiffres et leur fraction continue termine
   (ν = 0, lecture fausse).
2. La forme réelle \|K̂(ω)\|² est **paire** : \|ω\|^α, pas ω^α signé (le choix de branche
   mpmath sur base négative retourne le complexe principal, dév 0.27 à ω=−0.1).

---

## §1. Le changement unique : O5-V1, sonde de queue

**V0 (défaut)** : νₙ(x) := min sur les n premiers convergents de q_n·\|q_n·x − p_n\|.

**V1 (corrigé)** : ν*ₙ(x) := min sur les convergents d'**indice i ∈ [n₀, n−1]** de
q_i·\|q_i·x − p_i\|, avec **n₀ = n/2 = 25** (indices 0-based sur les N = 50 convergents
gelés O7).

- **Principe du choix n₀ = N/2** : la seconde moitié de la fenêtre gelée — un choix
  structurel (la moitié de queue), **non calibré sur la barre**. La barre 1e-6 de C3a/C3b
  est inchangée.
- **Prédiction déposée (vérifiée par la machine, pas postulée)** : le déficit
  \|ν*(1/φ) − 1/√5\| décroît en ~φ^{−2i} ; à i₀ = 25 il est ~10^{−11}, donc sous la barre
  1e-6 avec trois ordres de marge. Si la machine mesurait un déficit > 1e-6, V4 tomberait
  à nouveau — **aucun sauvetage**.
- **I3 conservé** : la table Famille C consigne les **deux** fonctionnels, ν₅₀ (V0,
  transitoire) et ν*₅₀ (V1, queue) — la leçon reste lisible dans le résultat.
- C3a/C3b/C4 sont réévalués avec ν* ; C4 devient : max des ν* sur les 8 non-dorés
  < 1/√5 − 1e-3 (les constantes de queue des rivaux sont ≤ 1/(2√2) < 0.446, marge ≥ 0.09).

---

## §2. Contrôles bloquants et échelle (inchangés)

C0a (mtime de CE dépôt < exécution), C1, C2, C5, C6, C3a, C3b, C4, TN — un seul échec
⟹ V4, exit 1, aucun sauvetage. Verdicts : V+ CHAINE_GAGUT_HURWITZ_CONFIRMEE /
V2 CHAINE_CONFIRMEE_SANS_LA_REALISATION / V4 REFUTE.

## §3. Interdictions (reprises de V0)

I1–I5 de V0 s'appliquent tel quels ; I5 s'étend à V1 après exécution (le présent dépôt et
le registre ne sont plus modifiables). I4 : V+ n'établit NI Gij j = 0, NI le GAGUT
littéral, NI le couplage D^{1/φ} = G — uniquement la chaîne de l'exposant, maillon par
maillon, avec le maillon Oyibo consigné [P].

## §4. Honnêteté (reprise de V0 §6, complétée)

Tout V0 §6 tient. En plus : la réussite éventuelle de C3a/C3b en V1 valide la **sonde de
queue** (le théorème de Hurwitz lu correctement), pas une prédiction physique nouvelle ;
elle referme le discriminateur CH-G4 tel que V0 l'a déposé. La portée reste celle de I4.
