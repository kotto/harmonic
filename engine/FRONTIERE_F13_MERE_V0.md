# FRONTIÈRE F13 — L'ÉQUATION MÈRE : le compensateur exact et l'assemblage Schrödinger

## Attaque du trou D3 de la campagne jauge — le compensateur comme objet machine exact

**Auteur :** Alain Kotto (Univers-Holistique)
**Version :** F13-1.0
**Statut :** Frontière ouverte — cahier des charges déposé AVANT tout script (contrôle C0a)
**Références :** `FICHE_THEOREME_U1.md` (brique 2), `THEOREME_DYADE_SU2.md` + `verif_dyade_ondes.py`
(DYADE_CONFIRMÉE, 8/8 ≤ 4,37e-15), `THEOREME_TRIANGLE_SU3.md` + `verif_triangle_ondes.py`
(TRIANGLE_CONFIRMÉ, 7/7 ≤ 8,12e-15), `DEPOT_JAUGAGE_V0.md` + `verif_jaugage_v0.py`
(V3 COVARIANCE_LOCALE_DERIVEE_FORCE_SANS_NOM, exit 0, 28/08),
`GENERALISATION_D1PHI_GAUGE_5_DOMAINES.md` (D^{1/φ} = G spin-2, 1e-15),
`DEPOT_F12_POTENTIEL_V0_1.md` (C2 : identité mère 4,97e-16 ; Green r^{2α−3}),
`DEPOT_F12_PAULI_V0.md` (σ = e^{iπα}), `DEPOT_HAMILTONIEN_ABC_THU_V0.md` (C3 Bateman)

---

## 0. VÉRIFICATION PRÉALABLE DU WORKSPACE (consignée le 02/09/2026)

Avant rédaction, le workspace a été audité à la demande de l'auteur. Constat déposé :

| Groupe | Objet déposé | Verdict machine | Date |
|---|---|---|---|
| **su(2)** | dyade : 2 modes + 1 conservation → 4−1 = 3 canaux (Pauli), double couverture P7 | DYADE_CONFIRMÉE, 8/8 ≤ 4,37e-15 | 27/08 |
| **su(3)** | triangle : 3 modes + 1 conservation → 9−1 = 8 canaux (Gell-Mann), découplage U(1)×SU(3) P6 | TRIANGLE_CONFIRMÉ, 7/7 ≤ 8,12e-15 | 27/08 |
| **u(1)** | liberté résiduelle de la projection (Maillon 3) + tore T⁵¹² cinématique | [T]/[P], double jambe | 27/08 |
| **jaugage local** | défaut D(a,k) 36 lectures, aveuglement global A2, gradient-portage A3, force G* mesurée | V3 — covariance locale dérivée, force SANS NOM (0/16), exit 0 | 28/08 |
| **spin-2** | D^{1/φ}[Ψ] = G[Ψ] (Fierz-Pauli → Deser) | 4 tests, 1e-15 | camp. antérieure |

**Conséquence honnête :** les trois algèbres de jauge SONT dérivées par calcul machine
(comptage bilinéaire sous conservation). La carte des trous déposée au JAUGAGE V0 §6
reste valable et c'est ELLE qui définit la marche suivante :

- **D1 (localisation)** — dérivée au niveau défaut (V3) ;
- **D2 (la force)** — G* = χ_{0,1}(1)/R_tour(½) mesurée, **sans nom fermé** (0/16, I5-B) ;
- **D3 (le compensateur dynamique)** — **OUVERT** : « V0 mesure le défaut de covariance
  locale et son amplitude ; le compensateur reste ouvert » ;
- **D4 (dictionnaire μ↔ω)** — ouvert (Famille C diagnostique, puissance de verdict nulle) ;
- **pourquoi N=2, N=3** — ouvert.

**F13 attaque D3** — et seulement D3, plus l'assemblage Schrödinger (le générateur
conservatif n'a jamais été assemblé en contrôle unique). Toute prétention au-delà
(nommer G*, dériver −¼F², fermer D4) est interdite dans ce dépôt.

## 1. LA THÈSE (P30–P35)

- **P30 (équation mère)** — φ·K̂⁻¹ − φ = (iω)^α (fermé, MORT 2 C2, 4,97e-16) : la mémoire
  est la dérivation. Quatre lectures d'un seul objet : dynamique (α=1), statistique
  (phase πα = σ, M1), force (Green r^{2α−3}, M2), jauge (défaut de rephasage modulé, V3).
- **P31 (Schrödinger = lecture α=1)** — à α=1 la lecture conservative est un groupe
  unitaire à un paramètre (Bateman R(θ), det=1, λ=e^{±iθ}) de générateur antisymétrique :
  la structure de Stone (i∂_t = Ĥ) sans postulat. Contribution THU : le générateur et son
  échelle sortent du noyau (station ω₀=1). Stone 1932 est standard — la boucle, non.
- **P32 (le compensateur exact = D3)** — le défaut mesuré au JAUGAGE (D(a,k) ≠ 0,
  gradient-porté) est fermé EXACTEMENT par le noyau covariantisé : K̂_A = φ·(D_A + φ)⁻¹
  avec D_A = D − iA, A = ∇χ. Identité d'absorption : **K̂_A[e^{iχ}ψ] = e^{iχ}·K̂[ψ]**
  (jauge pure), triple route : niveau dérivée, niveau noyau, niveau boucle. Le compensateur
  n'est plus une hypothèse — c'est un objet machine dont l'existence clôt le trou D3 au
  niveau statique.
- **P33 (observables aveugles)** — sous jauge pure, la force mesurée est invariante :
  le Green covariantisé vaut G_A(x,x₀) = e^{i(χ(x)−χ(x₀))}·G₀(x−x₀), G₀ = Green de la
  boucle de MORT 2 (|ω|^{−2α}). Module et phase vérifiés champ plein en 3D.
- **P34 (universalité forcée)** — un seul noyau pour tout état : la même K̂_A absorbe la
  jauge pour trois états distincts sans paramètre d'état. Le MS postule ce couplage champ
  par champ ; la THU le force.
- **P35 (spectre du connecteur)** — à α=1, la boucle a l'eigenvalue −|k|² (dispersion
  ω² = |k|², massif zéro) et la décomposition de Helmholtz séquestre la composante
  pur-jauge : **2 canaux transverses par mode k ≠ 0** (rang machine du projecteur).
  L'holonomie ∮A·dl distingue la redondance (nulle, jauge pure) du physique (≠ 0).
  À α=1/φ : eigenvalue (i|k|)^{2/φ} = |k|^{2/φ}·e^{iπ/φ} — complexe, phase = πα = σ :
  l'objet que QED n'a pas, première mesure déposée ex ante.

## 2. CONTRÔLES BLOQUANTS ET BARRES PRÉ-ENREGISTRÉES (gelées avant exécution)

Conventions héritées du JAUGAGE V0 (O1–O7) : N = 512, L = 20π, Δω = 0,1, porteur
ψ₀ = e^{ix}/√N, norme unitaire ‖ψ‖² = Σ|ψₙ|²/N, famille χ(x) = a·cos(kx).
3D : N = 192, Δx = 1, fenêtre continue [3,8], rayon torique enveloppé (MORT 2).

| # | Contrôle | Barre |
|---|---|---|
| C0a | mtime(`FRONTIERE_F13_MERE_V0.md`) < heure d'exécution (les deux horodatages au JSON) | — |
| C0b | fermeture algébrique φ² = φ+1 ; 2θ = πα (θ = πα/2, KMS C6) | 1e-15 |
| C1a | identité mère à α=1 : φK̂⁻¹ − φ = iω sur la grille O3 + mpmath 30 chiffres en {½,1,2,3.7} | 1e-12 / 1e-29 |
| C1b | groupe à un paramètre : R(θ₁)R(θ₂) = R(θ₁+θ₂), 100 paires, graine 27 | 1e-14 |
| C1c | unitarité : RᵀR = I ; det = 1 ; dérive ‖v‖² sur 1000 pas | 1e-14 / 1e-14 / 1e-12 |
| C1d | générateur antisymétrique : (R(δ)−I)/δ → [[0,1],[−1,0]], δ = 1e-6 | 1e-5 |
| C2a | ancre A2 (reprise JAUGAGE) : aveuglement au rephasage constant, 72 lectures | 1e-9 |
| C2b | ancre A1 (reprise JAUGAGE) : le défaut existe — D(0,1;k=1) reproduit du registre 0,032328801001024664 ; défaut max > 1e-4 | 1e-12 / — |
| C2c | **niveau dérivée** : D_A[e^{iχ}ψ] = e^{iχ}D[ψ], A = ∇χ, 6 profils de la famille fermée | 1e-10 |
| C2d | **niveau noyau** : K̂_A[e^{iχ}ψ] = e^{iχ}K̂[ψ] (inversion (D_A+φ)⁻¹), 6 profils | 1e-9 |
| C2e | **niveau boucle** : D_A²[e^{iχ}ψ] = e^{iχ}D²[ψ], 6 profils | 1e-10 |
| C2f | composition : χ = χ₁+χ₂ ⟹ cohérence composée (6 paires) | 1e-10 |
| C3a | 3D jauge pure : médianes de \|G_A\| par coquille [3,8] = G₀ | 1e-10 |
| C3b | 3D jauge pure : \|G_A/(e^{iΔχ}G₀) − 1\| champ plein (r ≤ 32) | 1e-9 |
| C4 | universalité : C2d pour 3 états distincts (porteur, gaussienne, superposition), MÊME noyau | 1e-9 |
| C5a | courbure d'une jauge pure : ∇×∇χ = 0 (grille 3D entière) | 1e-12 |
| C5b | Helmholtz : ∇·A_T = 0 ; A_L = ∇λ (N = 96) | 1e-11 |
| C5c | rang du projecteur transverse = 2 par mode k ≠ 0 (5 modes échantillonnés, graine 27) | exact |
| C5d | dispersion : eigenvalue de la boucle à α=1 = −\|k\|² ; phase de l'eigenvalue = πα = σ | 1e-12 / 1e-15 |
| C6a | holonomie ∮A·dl (boucle carrée fermée) : jauge pure = 0 ; champ physique (curl ≠ 0) ≠ 0 | 1e-12 / > 1e-3 |
| C6b | α=1/φ : eigenvalue de boucle = \|k\|^{2/φ}·e^{iπ/φ} déposé ex ante (première mesure, SANS barre) | mesure |

Règle unique : **UN SEUL contrôle en échec ⟹ REFUTE, exit 1, aucun sauvetage.**
C6b ne peut pas faire échouer le verdict (première mesure, lecture ex ante).

## 3. VERDICTS (échelle gelée avant exécution)

| Verdict | Condition | Sortie |
|---|---|---|
| **F13_MERE_COMPENSATEUR_EXACT** | tous les contrôles C0a…C6a ✓ | exit 0 |
| **REFUTE** | un contrôle bloquant en échec | exit 1 |
| **PIPELINE_CASSE** | C2a ou C2b en échec (ancre déposée non reproduite) | exit 1 |

Le verdict exit 0 dit EXACTEMENT : *le trou D3 est fermé au niveau statique — le
compensateur du défaut de covariance locale existe comme objet machine exact, triple
route ; la dynamique de Schrödinger est assemblée depuis la boucle ; les observables
sont aveugles à la jauge pure ; le connecteur a 2 canaux transverses et une holonomie
gauge-invariante.* Il ne dit PAS plus (§5).

## 4. FALSIFIABILITÉ

- Si l'identité d'absorption C2d échoue (le compensateur n'existe pas ou n'absorbe pas
  exactement), le trou D3 se referme dans l'autre sens : **le défaut de covariance locale
  n'a PAS de compensateur dans le noyau** — le jaugage s'arrête au V3 pour toujours, et
  la lecture « le couplage est le prix de la stationnarité locale » est réfutée.
- Si C3 échoue, les observables voient la jauge pure : la redondance n'est pas une
  redondance — contradiction avec le statut [P] du Maillon 3, à consigner.
- Si C5c ne renvoie pas rang = 2, le comptage des polarisations échoue — le connecteur
  de la THU n'a pas le spectre du photon.
- Toute échelle de verdict, barre et graine est gelée par ce document (contrôle C0a).

## 5. HONNÊTETÉ — ce que F13 V0 ne prouve pas

1. **Pas de nom pour G*** : la force candidate du JAUGAGE (1/D₂ voisin à 1,0×10⁻³,
   consigné) reste sans nom — I5-B interdit tout candidat post-hoc ; un dépôt ultérieur
   est requis si une écriture close émerge.
2. **Pas de −¼F²** : le compensateur statique exact n'est pas la dynamique du médiateur
   (terme cinétique, quantification) — la dérivation complète de l'électromagnétisme
   quantique reste ouverte.
3. **Pas de D4** : le dictionnaire μ↔ω (running) n'est pas attaqué ici.
4. **Pas de pourquoi N=2, N=3** : les algèbres sont dérivées (dyade, triangle), pas leur
   sélection par la nature.
5. **Comptage 3→2, pas 4→2** : le connecteur V0 est un 3-vecteur spatial ; la composante
   temporelle (lecture Φ₂, t=iβ) n'est pas assemblée — le décompte covariant complet
   A_μ (4−1−1=2) reste ouvert.
6. **SU(2)×SU(3) dynamiques** : les algèbres sont dérivées (27/08) ; leurs jaugages
   non-abéliens (auto-couplage, confinement, anomalies) restent consignés ouverts.
7. La lecture α=1/φ du connecteur (C6b) est une **première mesure ex ante** — aucune
   interprétation physique n'est revendiquée au V0.

## 6. REPRODUCTIBILITÉ

```
python verif_f13_mere_v0.py     # python 3.11.8, win32
```

Paramètres : 1D — N=512, L=20π, Δω=0,1, porteur e^{ix}/√N, famille χ = a·cos(kx)
(grille fermée A_GRID×K_GRID du JAUGAGE), graine 27. 3D — N=192, Δx=1, coquilles [3,8].
Sortie : `resultat_f13_mere_v0.json` (horodatages C0a, toutes les lectures, verdict).

---

> *La campagne du 27/08 a compté les canaux ; le JAUGAGE du 28/08 a mesuré le prix du
> rephasage local. F13 construit l'objet que le prix appelle : le noyau qui absorbe la
> jauge exactement — et montre que la force qu'il médie est la boucle déjà déposée.*
