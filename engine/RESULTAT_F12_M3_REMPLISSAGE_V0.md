# RÉSULTAT F12 — MORT 3 : LE REMPLISSAGE — V0

**Date : 2026-09-03. Verdict machine : `V4_REFUTE` — exit 1. Aucun sauvetage.**

Exécution de `verif_f12_m3_remplissage_v0.py` sur la frontière gelée
`FRONTIERE_F12_M3_REMPLISSAGE_V0.md` (commit **71d92e4**, antériorité mtime
contrôlée par le script lui-même — C0a OK : frontière 13:52:02 < exécution 18:30:52).
Sortie : `resultat_f12_m3_remplissage_v0.json` (154.0 s, graine 1234, grille gelée
N=800, r∈[1e-4,400] log, L_MAX=2, N_KEEP=10, IT_FREEZE=60, MAX_ITER=400, MIX=0.3).

---

## 1. LE VERDICT

**V4_REFUTE — un contrôle en échec (C4), et la règle gelée est : un seul contrôle
en échec ⟹ REFUTE exit 1, sans sauvetage.**

| Contrôle | Résultat | Valeur machine |
|---|---|---|
| C0a antériorité frontière | **OK** | mtime 13:52:02 < 18:30:52 |
| C1 solveur Coulomb −1/(2n²) + dégén. l | **OK** | err rel max 4.732e-04 (barre 5e-4) ; dégén. 1.930e-05 (barre 1e-4) |
| C2 normalisation ∫u²dr = 1 | **OK** | 3.33e-15 |
| C3 charge ∫ρ d³r = N_e | **OK** | 1.42e-14 |
| **C4 témoin He ∈ [−2.88, −2.83]** | **ÉCHEC** | **E(He) = −1.942099** ; conv=True, stable=True |
| C5 one-body négatif (7 β × 3 θ) | **OK** | aucun β ne produit [2,10,18] |
| C6 anti-rétro-ingénierie (graine 1234) | **OK** | 0 système sensible ; motifs interdits : aucun |
| C7 convergence (tout Z sauf Z=5) | **OK** | Z=5 conv=False comme consigné d'avance ; ions tous convergés |
| C8 stabilité refill == config | **OK** | aucun Z instable |

## 2. CE QUE LA MACHINE A QUAND MÊME ÉTABLI (D1–D3 tous passés)

La **thèse physique T1–T3 est confirmée par la machine** — mais le verdict V0 est
porté par l'échelle gelée, qui exige C1–C8 ET D1–D3 :

- **D1 OK — 20/20 configurations fondamentales == aufbau réel** : 1s¹ → 1s² →
  2s¹…2s² → 2p¹ (bore) … 2p⁶ (néon) → 3s¹…3s² → 3p¹…3p⁶ (argon) → **4s¹ (K) →
  4s² (Ca)**. La règle (n+l,n) n'existe nulle part dans la route (C6 : inspection
  de source + permutation d'étiquettes graine 1234 sans effet).
- **D2 OK — fermetures == {3, 11, 19} exactement** : ratios I(Z)/I(Z−1) = 0.172,
  0.253, 0.289 (< 0.4) ; aucun autre Z sous le seuil (suivant : 0.516 à Z=13).
- **D3 OK — inversion ε(4s)−ε(3d) des deux côtés** : Δ(10) = +2.17e-06 (> 0),
  Δ(19) = −8.97e-03 (< 0), Δ(20) = −2.26e-02 (< 0). Le champ donne les DEUX côtés.
- **T4/C5 OK** : la route one-body reste morte sur la grille gelée (Coulomb
  {2,10,28,46…} ; β=4−√5 → [2,4,6,12] ; aucun triplet).
- **T5a OK** : E(H) un corps = −0.4998135932 (|E+0.5| = 1.864e-04 ≤ 5e-4).
- [OBS] D5 consigné : à β=4−√5, états liés s:5, p:3, d:0, E(1s)=−401.3 — la
  tranche mémoire ne ferme pas la table à un corps. D6 (nucléaire) et D7
  (anomalies) hors portée, comme gelé.

## 3. L'ÉCHEC C4 — DIAGNOSTIC (défaut estimateur n°10, consigné sans sauvetage)

E(He) machine = **−1.942099**, hors de la fenêtre gelée [−2.88, −2.83] (écart
≈ +0.89 à +1.06 Hartree). Quantification machine de la cause :

- La fenêtre gelée est le témoin **Hartree sans auto-interaction** (−2.86, exact
  −2.9037) — la valeur produite par la convention « champs par sous-couche »
  **que la frontière §5.2 a elle-même rejetée** (défaut n°8 : non variationnelle,
  sur-corrige I(Z)<0 à Z=6-10).
- Sous la convention **brute mandatée** (auto-interaction incluse — §5.2, qui
  connaît E(H)=−0.243), la machine donne E(He) = −1.9421. La correction J mesurée
  sur grille (J = ∫u²·V_H[u²]d³r = **0.791169**) donne E−J = **−2.7333**, encore
  hors fenêtre : la convention brute délocalise l'orbitale auto-cohérente
  elle-même — la fenêtre n'est atteignable par aucune correction à posteriori.
- **La barre C4 est donc inconsistante avec la convention que la même frontière
  mandate** — défaut de frontière (pas de code) : §0 cite E(He)=−2.8539 depuis la
  convention rejetée, et §5.1 dit « barres sur ORDRES et RATIOS jamais énergies
  absolues », mais C4 gèle une énergie absolue à deux corps.
- Le protocole ne sauve pas : la frontière est gelée, le verdict est **V4_REFUTE**.
  La thèse physique (D1–D3) reste machine-confirmée ; c'est le **témoin** qui est
  cassé, et il le restera dans le registre V0.

## 4. DÉFAUTS ESTIMATEUR (leçon V1.2 — registre continué)

- **n°9** (code, deux runs avortés avant le run de verdict) : clé `'config'`
  lue dans le dict SCF brut au lieu de la table — KeyError lignes 277 puis 382 ;
  affichage seul, aucune physique ; corrigé avant le run de verdict.
- **n°10** (frontière, §3 ci-dessus) : barre C4 gelée depuis la convention
  rejetée — inconsistante avec la convention brute mandatée ; E−J = −2.7333
  machine-quantifié, fenêtre inaccessible sous la convention mandatée.

## 5. PORTÉE (inchangée — frontière §6)

La V0 est REFUTÉE sur son échelle gelée. Le contenu qui survit est consigné :
l'ordre de remplissage Z≤20 sort du champ auto-cohérent du lien (D1/D2/D3) —
mais la V0 ne peut pas porter le titre de théorème : son témoin He est mort par
construction. Toute poursuite passe par une frontière **V0.1 déposée avant
exécution** (précédent M2 : protocole changé, thèse intacte, barres re-gelées
explicitement) — jamais par un relâchement a posteriori de V0.
