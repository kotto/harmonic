# RÉSULTAT — OYIBO / CONSERVATION — V0 : **V4 — REFUTE (exit 1)**

**Date :** 2026-09-02 · **Dépôt :** `DEPOT_OYIBO_CONSERVATION_V0.md` (fermé ex ante, C0a ✓)
**Script :** `verif_oyibo_conservation_v0.py` · **Sortie :** `resultat_oyibo_conservation_v0.json` (annexé tel quel, I5)
**Verdict machine :** `V4 REFUTE` — échecs : `famille_C:C3a_C3b_C4` (précisément C3a et C3b ; C4 passe) — **exit 1, aucun sauvetage.**

---

## §1. Deux exécutions, toutes consignées (I3)

| Run | État du script | Verdict | Rôle |
|---|---|---|---|
| EXEC1 | bogué (2 défauts d'implémentation) | V4 | consigné dans `resultat_oyibo_conservation_v0_EXEC1.json` — preuve d'honnêteté |
| EXEC2 | fidèle au dépôt V0 | **V4** | **exécution definitive** — `resultat_oyibo_conservation_v0.json` |

Défauts EXEC1 (corrigés **avant** EXEC2, dépôt V0 jamais touché) :
1. `mp.dps` fixé **après** la construction des constantes : le registre O6 était rationalisé
   à 15 chiffres ⟹ fractions continues terminales ⟹ ν = 0 sur 7 candidats (lecture fausse).
2. Forme réelle \|K̂(ω)\|² évaluée avec `ω^α` signé sur base négative (branche complexe
   principale mpmath) au lieu de \|ω\|^α — la forme réelle est **paire** (dév 0.272 à ω=−0.1).

## §2. Le paysage V0 : 13 des 15 unités de verdict passent

Tout le **contenu physique/mathématique de la chaîne de l'exposant** est confirmé machine :

| Maillon | Lecture | Résultat |
|---|---|---|
| CH-G1 (Noether) | A1 oscillateur, A2 pendule, A3 Kepler e=0.6 — drifts ≤ 1e-9 | ✓ |
| CH-G2 (échelle⟺puissance) | B1 : 48 lectures exactes ≤ 1e-12 ; B2 : témoin e^{−x} dévie > 0,1 | ✓ |
| CH-G5 (convergence) | B3 : r(λ,t) vs δ_pred = ρ₂(λ^{−α}−1)t^{−α}, ≤ 10 % rel + décroissance, λ∈{2,φ} | ✓ 4/4 |
| CH-G5 (taux) | B4 : pente log-log **−0.618984** vs −1/φ = −0.618034 (écart 9,5e-4 ≤ 5e-3) | ✓ |
| CH-G5/G6 (boucle) | D1 λ=φ ; D2 c_k = 1/Γ(k/φ+1) ; D3 couplage [P] consigné | ✓ |
| Contrôles | C0a, C1 (φ²=φ+1), C2 (K̂ double route, 12 lectures), C5, C6 (ML↔Wiman ≤ 1e-12) | ✓ tous |
| C4 (unicité) | max non-dorés = 0.292893 < 1/√5 − 1e-3 | ✓ |

## §3. Les deux échecs : la preuve au bit près que c'est la sonde, pas Hurwitz

| Contrôle | Barre | Mesuré V0 | Valeur mesurée ν₅₀ | Identité exacte |
|---|---|---|---|---|
| C3a \|ν₅₀(1/φ) − 1/√5\| | 1e-6 | 0.06524758 | 0.38196601125010515 | **= 1/φ² au bit près** (convergent c₁ = 1/1 : \|1/φ − 1\|) |
| C3b \|ν₅₀(1/√2) − 1/(2√2)\| | 1e-6 | 0.06066017 | 0.2928932188134525 | **= 1 − 1/√2 au bit près** (même transitoire c₁) |

**Racine :** la sonde V0 « νₙ := min sur les n premiers convergents » lit la **tête** de la
suite des convergents ; la constante de Markov/Hurwitz est une propriété de **queue**
(liminf n→∞). Pour la classe dorée, les convergents oscillent autour de 1/√5 avec une
amplitude ~φ^{−2n} (0.382, 0.472, 0.438, 0.451, 0.446, 0.4477, …) : le transitoire c₁
n'est jamais battu, la sonde est structurellement aveugle à la constante. C'est
exactement le cas prévu par le dépôt V0 §3 : *« Hurwitz est un théorème — son échec
machine est un bug, pas une découverte. »*

## §4. Règlage de protocole

- **C2 (EXEC1)** : défaut d'**implémentation** (le script ne calculait pas la formule O2
  du dépôt) → corrigé avant l'exécution definitive ; le dépôt V0 n'a jamais été modifié.
- **C3a/C3b (EXEC2)** : script **fidèle** au dépôt, dépôt mathématiquement défectueux sur
  sa sonde finie → **irréparable en V0** (I5 : aucun remaniement après exécution). V0
  tombe donc honnêtement à V4, et le remède est une **nouvelle version gelée** : le dépôt
  `DEPOT_OYIBO_CONSERVATION_V1.md` (changement unique : sonde de queue n₀ = N/2 = 25),
  exécuté dans `RESULTAT_OYIBO_CONSERVATION_V1.md`.

## §5. Leçons consignées (V0 → V1)

1. **Le liminf est une propriété de queue** : toute sonde finie d'un théorème asymptotique
   doit échantillonner la queue de la fenêtre, jamais sa tête (le transitoire c₁ = 1/1
   domine le min-tête pour toute la classe dorée et la classe √2).
2. **Précision avant constantes** : `mp.dps` doit précéder la construction des objets
   (sinon rationalisation silencieuse du registre ⟹ ν = 0).
3. **Parité de la forme réelle** : \|K̂(ω)\|² s'écrit avec \|ω\|^α ; un exposant
   fractionnaire sur base négative bascule dans la branche complexe principale.

## §6. Ce que V0 établit malgré V4

La chaîne **Noether → échelle → puissance → noyau ABC** (CH-G1, CH-G2, CH-G5) est
entièrement confirmée machine, y compris le **taux déposé** δ_pred en forme close et la
pente −1/φ à 9,5e-4. Seul le discriminateur CH-G4 tombe — sur un défaut de sonde
identifié, corrigé et re-gelé en V1. Le maillon Oyibo CH-G3 reste **[P] consigné, non
sauvé** ; I4 interdit toute lecture au-delà.
