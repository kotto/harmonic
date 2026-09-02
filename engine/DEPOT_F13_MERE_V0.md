# DÉPOT F13 MÈRE V0 — le compensateur exact du défaut de covariance locale (trou D3)

**Date** : 2026-09-02 · **Script** : `verif_f13_mere_v0.py` · **JSON** : `resultat_f13_mere_v0.json`
**Cahier des charges** : `FRONTIERE_F13_MERE_V0.md` (déposé AVANT exécution, contrôle C0a)

```
VERDICT : F13_MERE_COMPENSATEUR_EXACT   exit 0
23 lectures, 0 échec — python 3.11.8 / numpy — durée 25,9 s
```

---

## 0. POSITION (rappel du périmètre gelé)

L'audit workspace du 02/09 a confirmé que les **trois algèbres de jauge sont déjà
dérivées par calcul machine** (campagne 27–28/08) : dyade su(2) (DYADE_CONFIRMEE,
8/8 ≤ 4,37e−15), triangle su(3) (TRIANGLE_CONFIRME, 7/7 ≤ 8,12e−15), théorème U(1)
(cinématique [T] + ontologique [P]), jaugage local V0 (V3,
COVARIANCE_LOCALE_DERIVEE_FORCE_SANS_NOM). F13 n'attaque donc **que** le trou D3 du
registre JAUGAGE : *le compensateur dynamique du défaut de covariance locale* — plus
l'assemblage Schrödinger (P31) et le spectre du connecteur (P35). Tout le reste est
interdit par le §5 de la FRONTIÈRE (pas de nom G*, pas de −¼F², pas de D4, etc.).

## 1. THÈSE DÉPOSÉE — ce que exit 0 établit

- **P30 (identité mère)** — φ·K̂⁻¹ − φ = (iω)^α. La mémoire est une dérivation.
- **P31 (Schrödinger assemblé)** — la lecture α=1 de la boucle est un groupe unitaire
  à un paramètre (rotation de Bateman, dét=1, générateur antisymétrique) : la
  structure de Stone de l'équation de Schrödinger sort de la boucle. Contribution
  THU : l'échelle (station ω₀=1).
- **P32 (compensateur exact — l'objet D3)** — K̂_A = φ·(D_A+φ)⁻¹, D_A = D − iA,
  A = ∇χ, absorbe EXACTEMENT la jauge : **K̂_A[e^{iχ}ψ] = e^{iχ}K̂[ψ]**, vérifié à
  trois niveaux (dérivée, noyau, boucle) + cohérence de composition.
- **P33 (observables aveugles)** — sous jauge pure, G_A(x,x₀) = e^{i(χ(x)−χ(x₀))}·G₀ :
  module et phase vérifiés champ plein en 3D.
- **P34 (universalité forcée)** — le MÊME noyau absorbe la jauge pour 3 états
  distincts, aucun paramètre d'état.
- **P35 (spectre du connecteur)** — courbure de jauge pure nulle ; décomposition de
  Helmholtz séquestre la composante pur-jauge ; **rang du projecteur transverse = 2
  par mode k≠0** ; eigenvalue de boucle à α=1 = −|k|² (massif zéro), phase = πα = π.
  Holonomie : ∮∇χ·dl = 0 (redondance), ∮A_phys·dl ≠ 0 (physique).

## 2. LECTURES MACHINE (run 3, t_exec=1788376632.8)

| # | Contrôle | Barre gelée | Mesuré | Statut |
|---|---|---|---|---|
| C0a | dépôt antérieur à l'exécution | — | depot=1788364282.154 < exec=1788376632.801 | ✅ |
| C0b | fermeture φ²=φ+1 ; 2θ=πα | 1e−15 | 0.00e+00 | ✅ |
| C1a | identité mère α=1, grille 512 + mpmath 40 dps en {½,1,2,3.7} | 1e−12 / 1e−29 | 7.136584e−15 / 5.74e−42 | ✅ |
| C1b | groupe 1-param R(θ₁)R(θ₂)=R(θ₁+θ₂), 100 paires, graine 27 | 1e−14 | 9.436896e−16 | ✅ |
| C1c | unitarité : orth / det / dérive 1000 pas | 1e−14 / 1e−14 / 1e−12 | 2.2e−16 / 2.2e−16 / 1.5e−14 | ✅ |
| C1d | générateur (R(δ)−I)/δ → [[0,1],[−1,0]], δ=1e−6 | 1e−5 | 5.000445e−07 | ✅ |
| C2a | ancre A2 (aveuglement global), 72 lectures | 1e−9 | 6.938894e−17 | ✅ |
| C2b | ancre A1 : registre D(0.1,k=1)=0.032328801001024664 reproduit ; défaut max>1e−4 | 1e−12 / — | écart 6.938894e−18 ; défaut max 0.2986760 | ✅ |
| C2c | niveau dérivée D_A[e^{iχ}ψ]=e^{iχ}Dψ, 6 profils | 1e−10 | 4.738821e−13 | ✅ |
| C2d | **niveau noyau K̂_A[e^{iχ}ψ]=e^{iχ}K̂[ψ]** (inversion dense 512²) + sous-route | 1e−9 / 1e−13 | 2.442492e−14 / 3.3e−14 | ✅ |
| C2e | niveau boucle D_A²[e^{iχ}ψ]=e^{iχ}D²ψ | 1e−10 | 1.085203e−11 | ✅ |
| C2f | composition χ=χ₁+χ₂, 6 paires × 2 routes | 1e−10 | 3.276104e−14 | ✅ |
| C3a | 3D : route étendue −Δ_A + médianes \|G_A\| coquilles [3,8] = G₀ | 1e−10 / 1e−10 | 1.894352e−14 / 6.94e−18 | ✅ |
| C3b | 3D champ plein r≤32 : \|G_A/(e^{iΔχ}G₀)−1\|, n=137 065, 0 dénom. nul | 1e−9 | 3.679211e−15 | ✅ |
| C4 | universalité : même noyau, 3 états × 6 profils | 1e−9 | 2.442492e−14 | ✅ |
| C5a | courbure jauge pure max\|∇×∇χ\|, grille 192³ (reconstruction indép. de C3) | 1e−12 | 9.431717e−17 | ✅ |
| C5b | Helmholtz N=96 : max\|∇·A_T\| / max\|∇×A_L\|, graine 27 | 1e−11 / 1e−11 | 3.380576e−20 / 5.44e−21 | ✅ |
| C5c | rang projecteur transverse = 2, 5/5 modes k≠0 (critère exact, graine 27) ; P²−P | exact / — | 2/2/2/2/2 ; 1.665335e−16 | ✅ |
| C5d | dispersion λ=(iω)²=−ω² (route opérateur dense) ; phase λ = πα = π (σ) | 1e−12 / 1e−15 | 9.726305e−14 / 0.00e+00 | ✅ |
| C6a | holonomie jauge pure ∮∇χ·dl (boucle 24×24, 2²¹ pts/arête) ; téléscopage | 1e−12 / — | 2.808088e−17 ; 0.0e+00 | ✅ |
| C6a' | holonomie champ physique (vortex C=0.5, σ²=32) ; max\|curl\|=1.0000 ≠ 0 | >1e−3 | 5.332022e+00 | ✅ |
| C6b | **mesure ex ante α=1/φ** : λ=(iω)^{2/φ} aux 5 fréquences | SANS barre | voir §4 | lecture |

Dépôts mpmath 30 chiffres :
- `identite_mere_alpha1_w1p3` : (0.0 + 0.0j) — identité mère EXACTE à 30 chiffres en ω=1,3.
- `c6b_lambda_i_2surphi` : (−0.362374890080480119958646637475 + 0.932032423813227621534031668691j) = i^{2/φ}.

## 3. HISTOIRE DES RUNS — consignée sans embellissement

Leçon réappliquée : **tout estimateur est bugable** ; trois exécutions, deux bugs
d'estimateur corrigés AVANT le verdict (barres gelées inchangées, physique inchangée) :

| Run | t_exec | Issue | Diagnostic |
|---|---|---|---|
| 1 | 1788376413.3 | crash NameError `iχ` (f-string C2d : accolades non échappées) | bug de code, aucun verdict (C0a–C2c passés avant crash) |
| 2 | 1788376444.6 | **C5d ECHEC 1.199982** puis crash NameError `ok_a` (C5a) | bug de l'estimateur : phase comparée à πα(α=1/φ)=π/φ au lieu de πα(α=1)=π gelé — 1.199982 = π − π/φ exactement. Physique non réfutée ; estimateur aligné sur la spec gelée |
| 3 | 1788376632.8 | **F13_MERE_COMPENSATEUR_EXACT, exit 0, 21/21 contrôles** | run final, JSON déposé |

## 4. LA MESURE EX ANTE C6b — l'objet que QED n'a pas

Première mesure déposée (aucune interprétation revendiquée au V0, FRONTIÈRE §5.7) :

| ω | Re λ=(iω)^{2/φ} | Im λ | \|λ\| | arg λ / π |
|---|---|---|---|---|
| 0,1 | −0.021042150 | +0.054120655 | 0.058067352 | 0.618033988750 |
| 0,2 | −0.049565975 | +0.127484264 | 0.136780933 | 0.618033988750 |
| 0,3 | −0.081817164 | +0.210434696 | 0.225780446 | 0.618033988750 |
| 0,4 | −0.116755459 | +0.300296395 | 0.322195224 | 0.618033988750 |
| 0,5 | −0.153838331 | +0.395673972 | 0.424528120 | 0.618033988750 |

arg λ / π = **0.6180339887498948 = 1/φ** aux cinq fréquences (branche principale,
consignée [OBS] pour ω<0) : la phase de l'eigenvalue de boucle à α=1/φ vaut πα = σ,
indépendante de ω. Le module suit |ω|^{2/φ} exactement (colonne module_theorique
identique bit-à-bit au JSON). À α=1 la même boucle donne λ=−ω² (phase π) : **la phase
de la statistique est une fonction continue de α** — lecture déposée, non exploitée.

## 5. ÉTABLI / NON ÉTABLI (répète la FRONTIÈRE, n'ajoute rien)

**Établi au V0 (exit 0)** : le trou D3 est fermé au niveau statique — le compensateur
K̂_A=φ·(D_A+φ)⁻¹ existe comme objet machine exact, triple route (dérivée 4.7e−13 /
noyau 2.4e−14 / boucle 1.1e−11), avec composition cohérente ; Schrödinger assemblé
depuis la boucle (P31, 4 contrôles) ; observables aveugles à la jauge pure champ
plein (P33, 1.9e−14/3.7e−15) ; universalité forcée (P34, 2.4e−14) ; connecteur à
2 canaux transverses par mode k≠0 (P35, rang exact) ; holonomie distingue
redondance (2.8e−17) et physique (5.33).

**Non établi (hérité + nouveau)** :
1. Pas de nom pour G* (dynamique du compensateur — le jaugage s'arrête au V3 si C2d
   avait échoué ; il a passé, mais le nom reste ouvert).
2. Pas de terme −¼F² dérivé ; pas de dictionnaire μ↔ω (D4).
3. Pas de « pourquoi N=2, N=3 » pour les groupes.
4. Comptage 3→2 canaux : établi comme rang machine du projecteur (C5c), pas comme
   la discharge 4→2 du photon massif.
5. SU(2)×SU(3) : dynamiques de jauge non construites — seules les algèbres existent
   (campagne 27–28/08).
6. C6b : mesure ex ante, **aucune interprétation physique revendiquée**.
7. Mur d'aliasing : Green de test à bande limitée COUPURE=π/4 (fraction de bande
   0,0082 du cube 192³) ; χ modes (2,3,5) → produit ≤ π/4+0,35 < π [OBS].

## 6. REPRODUCTIBILITÉ

```
python verif_f13_mere_v0.py     # python 3.11.8, numpy, win32 ; 25,9 s ; exit 0
```
Graine 27 (C5b/C5c). Grille 1D : N=512, L=20π, Δω=0,1 (O1–O3) ; 3D : N=192³, Δx=1,
rayon torique enveloppé, fenêtre continue [3,8] ; noyau K̂=φ/((iω)^α+φ) (O2) ;
porteur e^{ix}/√N ; norme ‖ψ‖²=Σ|ψₙ|²/N (O7) ; registre D_REG=0.032328801001024664.
Inversions denses 512×512 (C2d/C2f/C4) : 26 factorisations, cohérence matricielle↔
spectrale 3,3e−14.
