# FRONTIÈRE F12 — M4 : LES NOMBRES MAGIQUES NUCLÉAIRES V0

## La tranche {2,8,20} et la consignation du rang 4 — critère C-P6 par table

**Verdict visé : `M4_NUCLEAIRE_TRANCHES_CONSIGNÉES` — exit 0 / REFUTE exit 1**
**Exécution :** `verif_f12_m4_nucleaire_v0.py` → `resultat_f12_m4_nucleaire_v0.json`
**Frontière mère :** `FRONTIERE_F12_TABLEAU_PERIODIQUE.md` (MORT 3, critère C-P6 :
« les deux tables de nombres magiques sortent du même couple, ou l'échec est
consigné par table »). Table atomique : fermée (M3 V0.1, a1048a1). La présente
frontière tranche la table nucléaire {2, 8, 20, 28, 50, 82, 126}.
**Date :** 03/09/2026 — ce dépôt est ANTÉRIEUR à l'exécution (C0a).
**Sondes pré-gel :** `sonde_m4_nucleaire_v0.py`, `sonde_m4_bars_v0.py` (tous les
nombres ci-dessous calculés par machine avant gel, leçon FORCE V1.2).

---

## 0. CONSIGNATION DES SONDES (pré-gel — ce qu'elles ont établi)

Le lien déposé M2 (boucle D^α∘D^α, exposant 2α−3, b249526) est LONG-RANGE pour
tout α : il ne produit jamais de régime nucléaire. Le SEUL objet déposé qui
porte une échelle de longueur est le noyau mémoire K̂(ω) = φ/((iω)^α + φ) —
pôle ω^α = φ. À α = 1 sa forme réelle est l'exponentielle e^{−φr} : le régime
À PORTÉE FINIE du lien est le lien M2 × l'échelle du noyau.

La sonde a balayé 4 familles centrales × 5 β × 4 μ × 3 seuils θ (222 configs
θ exécutées = 74/80 paires ; 6 paires skippées < 6 états liés, livre en C3)
+ la famille puissance pure (21 configs, complétude M2), toutes remplies avec
LE MÊME couple gelé que M3 :
capacité 2(2l+1) de M1 (d0f714a), ordre par énergie, fermetures par trous
d'énergie relatifs. Résultats machine déposés (sonde_m4_bars, 10.1 s) :

```
C1 contrôle Coulomb l≤6 : err rel max = 0.00047870493489649 ;
   écart dégénérescence-l max = 1.9297619706759583e-05
C2 normalisation u = v/√(r·dτ) : 1.0000000000000002 (écart 2.220446049250313e-16)
N_T1  (3 premières fermetures == [2,8,20]) : 49
N_28  (4e fermeture == 28 après [2,8,20])  : 0   (POW : 0 aussi)
28 apparaît quelque part (jamais en rang 4) : 77
meilleur préfixe : 3/7 — EXP β=20.0 μ=0.5 θ=0.1 → [2, 8, 20, 26, 52, 76, 124]
témoin capacité (YUK1 β=100 μ=1) : double=False [1,4,5,8,13,14]
                                   double=True  [2,8,10,16,26,28]
Coulomb β=1 : [2, 10, 28, 60, 110, 182, 280]          (hydrogénique Σ2n²)
GAUSS β=100 μ=0.5 : [2, 8, 20, 40, 70, 112, 168, 210] (harmonique)
YUKPHI β=200 μ=0.5 : [2, 8, 18, 32, 50, 52, 58, 68]   (hydrogénique par n)
convergence N=800 vs N=1600 (12 premières sous-couches, témoin) : 0.00044683194970739445
```

Témoin gelé EXP β=20 μ=0.5 (les 12 premières sous-couches, énergies machine) :
```
 1  1s Z=  2  E=-12.361853911474865      7  3s Z= 42  E=-5.011714775602838
 2  2p Z=  8  E=-9.502016008249676       8  4d Z= 52  E=-4.613926449951774
 3  2s Z= 10  E=-7.896570023407332       9  5g Z= 70  E=-3.9665175490208586
 4  3d Z= 20  E=-7.274633752315349      10  4p Z= 76  E=-3.7997658918069526
 5  3p Z= 26  E=-6.11937352055374       11  5f Z= 90  E=-3.3443109436814504
 6  4f Z= 40  E=-5.464658408113621      12  4s Z= 92  E=-3.0234478331815207
```

Défauts estimateur de la campagne de sondes (consignés, leçon V1.2 — corrigés
AVANT tout gel) : KeyError (n,l) — ensemble() demandait n≤14 avec N_KEEP=12 ;
normalisation u fausse au premier essai (44.53 — la convention est u = v/√(r·dτ),
celle du verif M3 a1048a1) ; boucle de convergence lisant le nom au lieu de la
clé. Trois bugs de SONDE, aucun touchant la route.

---

## 1. LES QUESTIONS FALSIFIABLES

- **T1 (tranche basse)** : sous le MÊME couple que la table atomique —
  capacité 2(2l+1) de M1 (d0f714a), minimisation d'énergie, niveaux du lien —
  pris cette fois dans le régime À PORTÉE FINIE du noyau déposé (famille
  e^{−μr} — la forme réelle du noyau K̂ à α = 1 est le membre μ = φ de cette
  famille), les TROIS PREMIÈRES fermetures valent [2, 8, 20] sur une large
  région de portées. Témoin gelé : EXP β=20 μ=0.5, θ=0.10
  → [2, 8, 20, 26, 52, 76, 124]. La grille en compte 49 réalisations.
- **T2 (la consignation C-P6)** : la QUATRIÈME fermeture n'est JAMAIS 28 :
  N_28 = 0 sur toute la grille gelée (familles déposées + famille puissance de
  complétude). Le rang 4 de la table nucléaire n'émerge pas du couple à un
  corps central — le degré interne j (brisure spin-orbite 1f₇/₂), consigné
  ABSENT depuis M1 (« le spin n'est pas dérivé », DEPOT_F12_PAULI_V0 §4),
  est la pièce manquante localisée. La consignation est le résultat.
- **T3 (séparation des régimes)** : les trois régimes du lien déposé donnent
  trois séquences distinctes — long-range [2,10,28,60,110,182,280] ;
  puits lisse profond [2,8,20,40,70,112,168] ; lien α=1/φ profond
  [2,8,18,32,50,72,98] — AUCUNE ne continue en [28,50,82,126].
- **T4 (capacité structurelle)** : sans le facteur 2 de M1, les fermetures
  changent ([1,4,5,8,13,14] vs [2,8,10,16,26,28]) — la capacité est
  structurante, pas décorative.
- **T5 (témoin solveur)** : E_{n,l} = −1/(2n²) à α=1 jusqu'à l=6 — le solveur
  est le même que M3 (a1048a1), généralisé à V(r) quelconque.

**Honnêteté T1 (déposée, pas dissimulée) : [2,8,20] est la tranche harmonique
connue — tout puits lisse profond la donne (GAUSS : [2,8,20,40,70,112]). Le
contenu THU n'est pas que [2,8,20] sort (la MQ standard le produit aussi) :
c'est que le régime du noyau déposé — SANS ajustement, μ = φ étant l'échelle
déjà fermée du noyau K̂ — y tombe, et que la MÊME machinerie qui fermait la
table atomique y fonctionne à l'identique. Précision machine consignée : à
μ = φ exactement, la séquence est [2,8,10,20,26,28,42] (D5) — la tranche
[2,8,20] sort des portées plus douces de la MÊME famille e^{−μr} (49
réalisations, témoin μ=0.5) : la chute est celle de la famille déposée
entière, sans aucun réglage sur la cible. La frontière est le rang 4.**

## 2. CONTRÔLES (gelés avant exécution)

| # | Contrôle | Barre gelée |
|---|---|---|
| C0a | antériorité : getmtime(FRONTIERE_F12_M4_NUCLEAIRE_V0.md) < début d'exécution | strict |
| C1 | solveur Coulomb α=1, n≤6, l≤6 : E = −1/(2n²) ; dégénérescence-l | err rel ≤ 5e-4 ; dégén ≤ 1e-4 |
| C2 | normalisation ∫u²dr = 1 (blocs l≤6, témoin EXP) | écart ≤ 1e-8 |
| C3 | livre de la grille : 4 familles × 5 β × 4 μ × 3 θ, skip < 6 liés consigné ; comptages == déposés (222 configs θ exécutées = 74/80 paires ; 6 paires skippées : EXP (20,3.0) et (50,3.0) ; YUK1 (20,3.0) ; GAUSS (20,3.0), (50,3.0) et (100,3.0)=5 liés ; YUKPHI 0 skip ; POW 21/21 exécutées) | égalité exacte des comptages |
| C4 | anti-rétro-ingénierie : la route ne lit JAMAIS la cible — ré-exécution avec cible perturbée (×3) → fermetures bit-identiques ; motifs interdits absents de la source de la route | bit-près / absent |
| C5 | contrôle négatif (doit tenir) : Coulomb β=1 ≠ table nucléaire dès la 2e fermeture ([2,10,…] vs [2,8,…]) | inégalité stricte |
| C6 | convergence N=800 vs N=1600 (12 premières sous-couches du témoin) | écart rel max ≤ 1e-3 |
| C7 | témoin capacité : double=False donne des fermetures ≠ double=True (séquences déposées) | différence stricte |
| C8 | témoin EXP β=20 μ=0.5 : ordre des 12 premières sous-couches et fermetures θ=0.02/0.05/0.10 BIT-IDENTIQUES au dépôt §0 | bit-près |

## 3. CONSÉQUENCES (falsifiables, gelées)

- **D1** : N_T1 == 49 ET le témoin gelé ∈ T1 avec séquence [2,8,20,26,52,76,124]
  — la tranche [2,8,20] sort du même couple que la table atomique.
- **D2** : N_28 == 0 ET N_28_POW == 0 — le rang 4 n'émerge pas du couple à un
  corps central : consignation C-P6 côté nucléaire, localisée au degré interne j.
- **D3 [OBS]** : 28 apparaît quelque part dans 77 configs (jamais en rang 4) —
  consigné sans pouvoir de verdict.
- **D4** : les trois séquences de régime == déposées (Coulomb / GAUSS / YUKPHI,
  bit à bit) — la séparation des régimes est machine.
- **D5 [OBS]** : à l'échelle déposée μ = φ — hors grille gelée, mesurée par la
  sonde S3 et re-mesurée au verif — EXP β=50 μ=φ donne aux θ=0.02 et θ=0.05
  [2,8,10,20,26,28,42] : 28 apparaît en 6e position, pas en 4e. Consigné sans
  pouvoir de verdict.

## 4. ÉCHELLE DE VERDICT (gelée)

- **V+ `M4_NUCLEAIRE_TRANCHES_CONSIGNÉES`** : C0a–C8 tous OK **ET** D1 **ET**
  D2 **ET** D4 — la tranche basse est fermée ET l'échec du rang 4 est consigné
  machine (C-P6 satisfait pour la table nucléaire : succès et échec tous deux
  chiffrés, aucun sauvetage).
- **V2_PARTIEL** : un de D1/D2/D4 en échec partiel (tranche ou séquences déviantes).
- **V3_INCOMPLET** : contrôles OK, conséquence invérifiable.
- **V4_REFUTE** : UN SEUL contrôle en échec ⟹ exit 1, aucun sauvetage.

## 5. GRILLE GELÉE + HONNÊTETÉ

```
N_GRID=800 ; r∈[1e-4,400] log ; L_MAX=6 ; N_KEEP=16 ; N_MAX=14
Familles : EXP e^{-μr} · YUK1 βe^{-μr}/r · YUKPHI β r^{√5-4} e^{-μr} · GAUSS βe^{-r²/2μ²}
BETAS=(20,50,100,200,400) ; MUS=(0.5,1.0,1/φ,3.0) ; THETAS=(0.02,0.05,0.10)
POW_BETAS=(1.0,1.2,1.4,4−√5,1.9,2.2,2.5) ; capacité 2(2l+1) ; skip si < 6 liés
```

- **Un corps central uniquement** — pas de champ nucléaire auto-cohérent (V1) ;
  la portée est celle du dépôt : un corps.
- **Le degré interne j n'est PAS introduit** — la consignation du rang 4 EST la
  localisation de la pièce manquante (spin, frontière ouverte depuis M1).
  Aucune brisure ajoutée pour « faire sortir » 28 : ce serait le sauvetage interdit.
- **Espèces proton/neutron non modélisées** — la capacité s'applique par espèce ;
  la table visée est la table par espèce (isotones).
- **La tranche [2,8,20] est la tranche harmonique connue** (§1, honnêteté T1) —
  la valeur ajoutée est la chute SANS ajustement du régime du noyau déposé dans
  ce régime, pas la nouveauté de la tranche.
- **Aucun chiffre calculé à la main** — tout est diagonalisé (sondes §0) ; le
  script verif n'existe pas encore au moment du dépôt.

---

*Conformément à la discipline de la THU : frontière déposée avant tout script
(C0a) ; sondes pré-gel consignées avec leurs défauts ; un seul échec de contrôle
⟹ REFUTE sans sauvetage ; la consignation d'un échec localisé EST un résultat.*
