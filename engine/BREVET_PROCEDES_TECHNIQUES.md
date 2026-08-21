# DEMANDE DE BREVET D'INVENTION — PROCÉDÉS TECHNIQUES (VERSION SÉPARÉE)

## OFFICE : INSTITUT NATIONAL DE LA PROPRIÉTÉ INDUSTRIELLE (INPI) — FRANCE
## DEMANDE INTERNATIONALE (PCT) — TOUS ÉTATS DÉSIGNÉS

---

## AVERTISSEMENT DE PORTÉE

Ce document est **strictement restreint aux applications techniques** mises en œuvre par la Théorie Harmonique. Il exclut volontairement toute revendication portant sur :

- la théorie elle-même (équation mère, mémoire d'or, chaîne cₙ) ;
- les lois de la nature, les méthodes mathématiques en tant que telles ;
- les constantes physiques et leur « dérivation ».

**Ces éléments font l'objet d'un mémoire scientifique séparé** (`MEMOIRE_SCIENTIFIQUE_THU.md`), conformément à l'exclusion des « découvertes, théories scientifiques et méthodes mathématiques » de la brevetabilité (art. 52 CBE et équivalents).

---

## 1. DOMAINE TECHNIQUE

L'invention concerne des **procédés de traitement de signal, de compression de données, de calcul et de mesure**, mettant en œuvre un formalisme à base de représentation spectrale et de paramètres dérivés de constantes mathématiques irréductibles.

| Code CIB | Domaine |
|----------|---------|
| H04N 19/00 | Compression d'images/vidéo |
| G10L 19/00 | Compression de la parole/audio |
| G06F 17/10 | Traitement numérique |
| G06F 7/00 | Calcul |
| G01K 7/00 | Mesure de température |
| A61B 5/00 | Mesure/diagnostic médical |

---

## 2. ÉTAT DE LA TECHNIQUE

| Technique | Limites |
|-----------|---------|
| Codecs classiques (JPEG, H.264, AV1, Opus...) | Nécessitent des dictionnaires/paramètres appris ou standardisés ; ratio borné |
| Compression entropique (zstd, gzip) | Inefficace sur contenu déjà compressé (~1,0007×) |
| Thermo-mesure classique | Pas de température privilégiée dérivée d'un principe |

Le **point technique distinctif** revendiqué n'est PAS la théorie, mais la mise en œuvre particulière de procédés exploitant :
1. une **troncature spectrale à seuil dérivé** (1/(φ·m)) ;
2. une **séparation signal/grain à régénération déterministe** ;
3. une **garantie mathématique de non-expansion** ;
4. un **sélecteur multi-mode à critère de qualité mesurée**.

---

## 3. DESCRIPTION DES PROCÉDÉS

### Procédé A — Compression modale à troncature dorée

1. Décomposer le signal (image/audio) en composantes modales.
2. Conserver les composantes dont la masse dépasse un **seuil dérivé 1/(φ·m)** — φ nombre d'or, m nombre de modes.
3. Encoder le résidu par codage différentiel (Delta-H) + codage entropique (zstd).
4. Au décodage, régénérer les composantes tronquées par une règle déterministe (aucune transmission du grain).

**Caractéristique technique** : le seuil de troncature est une fonction fixe d'un paramètre mathématique φ, choisie pour coïncider avec la troncature optimale (vérifié : 87,45 % de masse pour ~54 % des amplitudes), sans paramètre appris.

### Procédé B — Séparateur signal/grain à régénération déterministe

1. Séparer le signal (partie bit-exacte) du grain capteur (partie statistique).
2. Transmettre **uniquement** le signal bit-exact + une statistique compacte du grain (~32 octets).
3. Régénérer le grain au décodage par graine dérivée (0 octet transmis), garantissant `decode(data) == decode(data)` bit à bit.

**Caractéristique technique** : compatible avec le standard AV1 Film Grain Synthesis (H.274) ; propriété d'idempotence du décodage démontrée.

### Procédé C — Garantie mathématique de non-expansion

1. Tenter la compression mode BOOST (downscale + ré-encodage + zstd).
2. Si le résultat est ≥ taille source, appliquer zstd direct.
3. Si encore ≥ source, dégrader progressivement la qualité (qualité JPEG + downscale) jusqu'à ce que `compressed < source`.
4. Terminer : la cascade **garantit mathématiquement** que le résultat n'excède jamais la source.

**Caractéristique technique** : garantie formelle de non-expansion sur tout fichier, y compris déjà compressé (mesuré : ZIP/GZIP ≈ 1,0007× sur B3.mp4, HCV BOOST 1,5–4×).

### Procédé D — Sélecteur multi-mode à critère de qualité mesurée

1. Produire plusieurs candidats de compression (DICT / FULL bit-exact / MODAL lossy).
2. Mesurer le PSNR de chaque candidat.
3. Sélectionner le **plus petit** dont le PSNR ≥ seuil contractuel (`min_psnr`).
4. Router le décodeur par en-tête magique (HCVM / HHD2 / HHDC...).

**Caractéristique technique** : le curseur `min_psnr` est le contrat qualité — chaque +5 dB retire ~50–90× de ratio et restaure l'exactitude ; sur contenu incompressible, retombe automatiquement en FULL bit-exact.

### Procédé E — Prédiction de température par résonance

1. Pour un système physique de gap énergétique ΔE mesuré, calculer T* = ΔE/(k_B·ln φ).
2. Annoncer T* comme température de mesure d'un effet donné (facteur d'occupation = 1/φ).
3. Mesurer ; la prédiction est **falsifiable** (elle peut être refusée par la mesure).

**Caractéristique technique** : procédé de calibration thermométrique utilisant une constante mathématique comme référence de rapport d'occupation.

---

## 4. REVENDICATIONS (procédés uniquement)

**1.** Procédé de compression de signal caractérisé en ce qu'il comprend :
- une décomposition du signal en composantes modales ;
- une troncature selon un seuil fonction d'une constante mathématique φ (nombre d'or) ;
- un encodage du résidu par codage différentiel et entropique.

**2.** Procédé selon la revendication 1, dans lequel le seuil de troncature est 1/(φ·m), où m est le nombre de modes, la troncature coïncidant avec la troncature optimale sans paramètre appris.

**3.** Procédé de compression caractérisé par une séparation signal/grain, dans lequel :
- le signal est encodé bit-exact ;
- le grain n'est pas transmis, seule sa statistique compacte l'est ;
- le grain est régénéré de façon **déterministe** au décodage par graine dérivée, garantissant l'idempotence bit-à-bit.

**4.** Procédé de compression caractérisé par une garantie formelle de non-expansion, comprenant une cascade de modes (ré-encodage → entropique direct → dégradation forcée) telle que la sortie est mathématiquement toujours inférieure ou égale à la source.

**5.** Procédé de sélection de mode de compression, dans lequel une pluralité de candidats est produite, la qualité de chacun est mesurée (PSNR), et le plus petit candidat dont la qualité ≥ un seuil contractuel est retenu, avec routage du décodeur par identifiant de format.

**6.** Procédé de mesure de température, dans lequel une température de référence T* = ΔE/(k_B·ln φ) est calculée pour un système de gap ΔE donné, et utilisée comme calibration d'un rapport d'occupation de 1/φ.

**7.** (Dépendante) Système mettant en œuvre l'un quelconque des procédés 1 à 6, comprenant un codeur, un décodeur, et un module de sélection à critère de qualité.

---

## 5. RÉSULTATS MESURÉS (avec leur statut de validation)

> **Règle :** aucun chiffre n'est déclaré « validé » sans mesure tierce. Les chiffres ci-dessous sont des **mesures internes** ; leur statut est indiqué.

| Résultat | Valeur interne | Statut |
|----------|----------------|--------|
| Compression lossless DICT (leave-one-out, 8 images) | 44,4× @ PSNR ∞ (8/8 bit-exact) | ⚠️ interne, à valider par labour indépendant |
| Compression collection homogène | 213,2× LOO | ⚠️ mesure la redondance de collection, PAS une universalité |
| Sélecteur 3 modes (min_psnr=20) | 372,9× @ 64,1 dB | ⚠️ interne, lossy fort |
| Externes (images jamais vues) | 2,5× → 72,3× @ 25,8–33,7 dB | ⚠️ interne |
| Non-expansion sur déjà-compressé | 1,5–4× (BOOST) vs ZIP 1,0007× | ⚠️ interne |
| Codec de raisonnement GSM8K | 88,4 % | ⚠️ moteur sans paramètre, mais pipeline T5 appris |

**Programme de validation tierce (obligatoire avant commercialisation)** :
1. Comparatif indépendant vs AV1 FGS, VVC/H.266, V-Nova LCEVC sur corpus standard (SVT/JVET, Netflix).
2. Métriques par laboratoire indépendant : PSNR, SSIM, VMAF, ΔMOS (pas seulement internes).

---

## 6. ABRÉGÉ

Procédés de traitement de signal mettant en œuvre une représentation modale avec troncature à seuil dérivé d'une constante mathématique (nombre d'or), une séparation signal/grain à régénération déterministe bit-exacte, une garantie formelle de non-expansion sur tout fichier, un sélecteur multi-mode à critère de qualité mesurée, et un procédé de calibration thermométrique à température de référence dérivée. Application : compression audio/vidéo, recyclage de flux déjà compressés, calibration de mesure.

---

## 7. SIGNATURE

| Champ | Valeur |
|-------|--------|
| Demandeur / Inventeur | Alain Kotto |
| Nationalité | Française (FR) |
| Priorité | à fixer (dépôt initial) |
| États désignés (PCT) | Tous |

> **Note de dépôt :** ce brevet de procédé est déposé **indépendamment** du mémoire scientifique. Il ne revendique aucune loi de la nature ni méthode mathématique en tant que telle, mais uniquement leur **application technique** (effet technique concret : réduction de la taille de données, garantie de non-expansion, calibration de mesure).
