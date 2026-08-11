# 🌊 COMPRESSION_HARMONIQUE_V2 — Les six pistes, l'état et la route

**La nouvelle compression harmonique fondée sur la THU V2 — synthèse des pistes, des mesures et des domaines**
**Date** : 11/08/2026 — **Branche** : `memory-first-hybride` — **Auteur** : Univers-Holistique (Kotto Alain)
**Statut** : Document de synthèse — chaque mesure est une commande reproductible, chaque statut est classé (✅ · 🔬 · 📋 · ❌)
**Références** : `RAPPORT_AUDIT_HCV.md` · `benchmark_hcv2_modal.py` · `exploration_piste3_video_memoire.py` · `exploration_piste6_frft.py`

---

> *« L'ancienne compression harmonique se vendait comme harmonique et était classique (OpenCV, JPEG, zstd). La nouvelle est le contraire : chaque brique est un théorème de la THU V2 — le seuil, la chaîne, la distribution, le noyau, l'ordre — et chaque mesure est publiée, y compris les échecs. »*

---

## TABLE DES MATIÈRES

1. [Le point de départ — la base SDI et son audit](#1-le-point-de-départ)
2. [Les six pistes — l'état des lieux](#2-les-six-pistes)
2bis. [La compression par dictionnaire — trouvée dans le git, réparée, mesurée](#2bis-la-compression-par-dictionnaire)
3. [La découverte commune — la séparation des domaines](#3-la-découverte-commune)
4. [Le pipeline complet — le but](#4-le-pipeline-complet)
5. [Le protocole honnête](#5-le-protocole-honnête)
6. [La feuille de route](#6-la-feuille-de-route)
7. [En une phrase](#7-en-une-phrase)

---

## 1. Le point de départ — la base SDI et son audit

La base (projet HCV du workspace) a été **testée** — la vérité mesurée :

| Mesure de la base | Valeur | Statut |
|---|---|---|
| **Lossless bit-à-bit** (mode LOSSLESS) | PSNR ∞ · SSIM 1,0 — confirmé | ✅ réel |
| **Contenu broadcast optimisé** | **15,17×** (128 % de l'objectif) | ✅ réel sur son terrain |
| **B3 (contenu réel, 10 frames)** | **8,51× @ 51,22 dB** | ✅ la seule mesure sur contenu réel |
| **Signal réaliste** | 0,88× — **expansion** (fichiers plus gros) | ❌ contenu-dépendance |
| **« 30× », HCV16, WASM, lossless parfait** | jamais mesurés / jamais codés | ❌ fiction |

L'audit (`RAPPORT_AUDIT_HCV.md`) a publié l'écart : les codecs réels sont OpenCV+JPEG+zstd (classiques), le format HCV16 n'a jamais été codé, le WASM est un placeholder. **La nouvelle compression part des théorèmes, pas des étiquettes.**

## 2. Les six pistes — l'état des lieux

| Piste | Brique THU | Statut | Mesures |
|---|---|---|---|
| **P1 · Codec modal** | Troncature dorée 1/(φ·m) + chaîne cₙ = 1/Γ(n/φ+1) (T3) | ✅ **implémenté** | 2,25-48,8× (vs fichier) · 154-239× (vs RAW) · PSNR 19,1-24,2 dB · SSIM 0,95-0,98 · masse Parseval 99,5-99,9 % · 2 bugs réels attrapés (quantification inversée, normalisation de la chaîne) |
| **P2 · Compression holographique** | HolographicMemory — superposition, crosstalk ~1/√dim contrôlé par la troncature dorée | 📋 à explorer | les briques existent (wave_lang) — N items dans un vecteur |
| **P3 · Vidéo à mémoire** | Noyau doré K(t) = B·E_{1/φ}(−φ·t^{1/φ}) (T2) — prédiction non-markovienne | 🔬 probe | **contenu à mémoire (scène lente + bruit) : GOLDEN +2,2 dB** (28,35 vs 26,19 vs Markov) · B3 rapide : Markov gagne (31,2 vs 21,4) — la séparation des domaines |
| **P4 · Grain princié** | La mémoire oublie le transitoire à t^{−0,618} — le signal persiste, le grain est oublié | 📋 | le principe du Zeno t^{1,236} mesuré en P3 |
| **P5 · Entropie dorée** | La distribution thermique dorée pₙ = (1−1/φ)(1/φ)ⁿ (E3, vérifiée 1,1×10⁻¹⁶) | 📋 | remplace zlib par un codeur arithmétique à la distribution dérivée |
| **P6 · Transformée dorée** | L'ordre α = 1/φ (T1) — F^a = p(F), la puissance fractionnaire du groupe de la DFT | 🔬 **chantier fermé** | **unitarité ✅ · additivité 9,4×10⁻¹⁶** · le bruit 1/f^{1/φ} compacté **+9 à +11 points** dans le domaine doré (3 méthodes indépendantes : 0,875 · 0,8805 · 0,8700 vs 0,769-0,776) |

## 2bis. La compression par dictionnaire — trouvée dans le git, réparée, mesurée

**Demande** : « Explore aussi le workspace ou gits pour la compression par dictionnaire. »

**Découverte** : la compression par dictionnaire EXISTE dans le dépôt — `engine/multimodal/` (commit `4e3830d` « KA PHONE v3.2 — Storage Optimizer, HarmonicCodec »), **dans toutes les branches, jamais documentée** : `harmonic_codec.py` (1512 l) + `harmonic_database.py` (1657 l, shards + KD-tree + signatures DFT) + `build_dict.py` (223 l) + CLI `hc.py`. C'est la « version avec dictionnaire » qui avait donné des résultats intéressants.

**Elle était cassée depuis l'origine — 3 bugs réels réparés (méthode X1/X4)** :
1. `harmonic_codec.py` importe `multimodal.hcv_bridge` qui n'a **jamais existé** (ni dans 4e3830d ni ailleurs) → `ModuleNotFoundError` à l'import. Réparé : `hcv_bridge.py` créé — pont honnête (le moteur « HCV PRO » externe n'existe pas, audit §5 ; le Delta-H+zstd est natif au codec).
2. `harmonic_database.ingest()` (chemin legacy) omet `signature` requis par le dataclass `HarmonicPatch` → crash à l'ingestion. Réparé : signature passée à l'appel (comme les 2 autres instanciations).
3. **Persistance cassée** : `build_dictionary` sauvegarde les shards dans `<dict>.shards/` mais `HarmonicDatabase.load()` ne les découvrait jamais → un dict rechargé avait 0 shards et le codec retombait en FULL. Réparé : `load()` découvre le dossier voisin (CLI vérifiée de bout en bout : build-dict → compress BEST 76,5:1 → decompress HHD2).

**Les résultats mesurés (bases honnêtes : ratio vs RAW, quality=100, dict sur patches 16×16, images jamais vues)** :

| Mesure | Valeur |
|---|---|
| **Moyenne leave-one-out (8 images réelles SDI, jamais vues) — mode bit-exact** | **44,4× @ PSNR ∞ — 8/8 images lossless exact (bit-à-bit)** |
| vs mode autonome Delta-H+zstd (FULL) | 4,7× en moyenne → **gain ×9,4 du dictionnaire** |
| Meilleures | texture 76,7× · macro 76,5× · portrait 76,3× · pattern géométrique 45,7× · paysage 43,5× |
| La frontière | `architecture_photo` (contenu unique riche) : dict < FULL — le sélecteur BEST la récupère en FULL exact |
| Vidéo V3 (motion+dict+skip, B3 réel) | 3,2× @ 39,5 dB — **lossy par conception** (le skip_threshold omet les patches quasi-inchangés, pas la DCT) ; la référence SDI (8,51× @ 51,22 dB) reste meilleure |

**Le bit-exact (étape b)** : à quality ≥ 92, le résidu V2 est encodé en **Delta-H int32 + zstd exact** (mode 0x01) au lieu de la DCT float64→int16 arrondie (mode 0x00, lossy ~1 LSB) — `multimodal/harmonic_codec.py` `_compress_residual`/`_decompress_residual`. **Double gain mesuré : 8/8 images à ∞ ET la moyenne monte 42,7 → 44,4×** (le Delta-H comprime mieux que le DCT+RLE sur les résidus, ex. geometric_pattern 15,2 → 45,7×).

**L'échelle (étape c — patch_size et seuil, mesurés en LOO)** :

| Réglage | Moyenne LOO (8 images SDI) | Note |
|---|---|---|
| ps=16, thr=0,3 (référence) | 44,4× @ ∞ (8/8) | le point de départ |
| ps=32, thr 0,3-1,0 | **213,2× @ ∞ (8/8)** | **×4,8 — le patch_size est le levier** (moins d'overhead par patch : un patch 32×32 exact = 8 o pour 3072 o) |
| **Généralisation externe** (images jamais vues hors SDI, dict sur 7 images SDI) | **2,5× @ ∞** | la frontière honnête : le 213× mesure la redondance d'une collection homogène (même style/capteur) ; sur contenu inconnu, V2 (1,0-2,6×) < FULL (1,2-4,6×) — **le sélecteur BEST garde le meilleur (zéro perte)** |

**Deux constats structurels publiés** :
1. **Le `match_threshold` est inerte** : le meilleur match est presque toujours sous 0,3 (match ~94-100 % même sur les externes — les signatures normalisées sont proches) ; 0,3 = 0,6 = 1,0 strictement identiques sur toutes les mesures. Le « match » n'est pas un filtrage : le gain vient du résidu exact + Delta-H, pas du choix match/pas-match.
2. **Le dictionnaire est la mémoire du codec** : il compresse ce qu'il connaît (collection homogène : galerie d'un appareil, frames d'une vidéo, lots scannés — 213×) et se tait sur l'inconnu (2,5×, jamais moins que FULL grâce à BEST) — la même loi que le noyau memory-first : « la mémoire certifie, le codec formule ». Le patch_size par défaut passe à **32** (CLI `hc.py`).

**Le transfert doré au résidu (étape d) — ÉCHEC PUBLIÉ, comme P5** : la troncature dorée 1/(φ·m) (P1) a été intégrée au résidu du dictionnaire (mode 0x02, `multimodal/harmonic_codec.py` — diffract + seuil doré + float16 + varint, réutilisant `hcv2_modal_codec`). Mesuré en LOO ps=32 (quality=70) : **GOLDEN 212,0× @ 54-100 dB vs DCT 226,7× @ 54,8-100 dB — inférieur en ratio ET en qualité** : la troncature casse l'exactitude là où le DCT reste ∞ (les résidus du dict sont nuls ou bruités — la masse Parseval du bruit est étalée, le seuil doré jette ~13 % d'énergie → 54-68 dB, et l'overhead du format modal est payé par patch). 1 bug réel attrapé par la mesure (division par zéro sur résidu nul → NaN) et corrigé (chunk vide). **Le théorème ne se transfère pas au résidu** — son terrain reste le codec modal sur images entières (P1, masse 0,8745 vérifiée). Le champion reste le bit-exact (0x01) : 213,2× @ ∞.

**La vidéo (étape e — I-frame par `encode_best`), et 2 bugs réels attrapés par la mesure** :
1. **Grille floor des encodeurs** (`(H-ps)//st+1`) : les ~7 % de pixels des bords (dimensions non multiples de ps) n'étaient pas encodés ni mesurés — corrigé en ceil `(H+st-1)//st` dans `encode`/`encode_full`/`encode_v2` (les décodeurs lisent la grille du header — compatibles). *Erreur méthodologique publiée* : mes « bit-exact 8/8 » portaient sur la zone couverte — pour les images SDI (1024×768, multiples de 32) la couverture était déjà totale, les 213,2× restent valides ; le biais ne touchait que les dimensions arbitraires.
2. **Grille floor de `build_dict.py`** : les patches de bord (paddés) étaient absents du dictionnaire → ~2 Ko/patch au lieu de 10 o → 96 % du bitstream vidéo. Corrigé (padding zéro identique à l'encode).

**Résultat vidéo mesuré (10 frames réelles B3, dict ps=32 sur les 5 premières)** : **I-frame seule : 246× en V2_DICT, bit-exacte** (vs ~8× en DCT brut — ×30) ; **séquence complète : 4,9× @ 43,4 dB** (vs 3,2× @ 39,5 dB avant — +53 % de ratio, +3,9 dB). Frontière : les P-frames (skip/motion vs frame 0) restent le goulot — la référence SDI (8,51× @ 51,22 dB) reste devant sur la vidéo.

**Les P-frames (étape e — comparaison à la frame précédente)** : **4,9 → 8,4× (+71 %)** — le mouvement cumulé vs frame 0 écrasait le ratio. Deux découvertes publiées :
1. **Pas de divergence encode/décode possible** : le codec est bit-exact → la référence reconstruite (encode-décode) est identique à l'originale → l'accumulation apparente venait du skip, pas d'une divergence de référence.
2. **Le `skip_threshold` est le curseur ratio/qualité** (scan mesuré, même B3) : 1,0 → 2,8× @ 49,6 dB · 2,0 → 4,1× @ 43,5 dB · 3,5 → 6,2× @ 40,2 dB · 5,0 → 8,4× @ 38,9 dB (défaut) · 8,0 → 16,9× @ 36,5 dB.

**Le MC avec résidu (étape f — MC_RESIDUAL, flag 0x04)** : les patches dont la compensation est bonne sans être parfaite (threshold ≤ diff < 2·threshold) sont encodés patch déplacé + résidu exact — **le plancher d'erreur du MC-SKIP est relevé** : à skip=5, min PSNR **22,5 → 26,2 dB** (moyen 38,9 → 39,4 dB) au prix de −23 % de ratio (8,4 → 6,5× — le dict matche mieux que le MC sur les différences moyennes ; plage 1,5× mesurée : 6,9× @ 38,2 dB, min 24,8 — le 2× est le meilleur compromis qualité). 2 bugs réels corrigés dans le décodage 0x04 (dx/dy inversés, clamp absent — le bloc 0x02 clamp, le mien non). Nouveau curseur skip : 2,8× @ 48,7 → 13,8× @ 37,5 dB.

**L'I-frame vidéo MODAL (étape h) — ÉCHEC PUBLIÉ, contre-productif** : `encode_video(iframe_min_psnr=...)` autorise le MODAL sur l'I-frame (`_reconstruct_frame` aligné sur le même sélecteur — cohérence encodeur/décodeur garantie). Mesuré (B3, 10 frames, skip=5, MC_RES 2×) : **I-frame exacte 6,5× @ 39,4 dB (min 26,2) · I-frame MODAL 20-25 dB → 2,5× @ 39,2** — le ratio CHUTE : la référence lossy (25-35 dB) dégrade la prédiction des P-frames (plus de patches « modifiés » vs la référence bruitée) et noie le gain de l'I-frame (~1 Ko sur ~1000 Ko). **La vidéo exige une référence exacte — le lossy appartient aux P-frames (skip/motion), pas à l'I-frame.** `iframe_min_psnr` reste disponible (défaut None = exact, le comportement retenu).

**Le GOP (étape i — vidéo native) — la dérive est bornée** : `encode_video(gop_size=...)` réinsère une I-frame (exacte, ~246×) tous les `gop_size` frames. **B3 NATIF (478×850, 10 frames, dict ps=32, skip=5, MC_RES 2×)** :

| gop | Ratio | PSNR moyen | min | dernière frame |
|---|---|---|---|---|
| 0 (1 I-frame) | 7,4× | 39,1 dB | 26,1 | 29,4 (dérive) |
| **4** | **6,0×** | **56,9 dB** | 28,6 | 41,6 |
| 8 | 5,5× | 47,3 dB | 26,1 | 41,6 |

**gop=4 est le réglage de référence** : −19 % de ratio pour **+17,8 dB de PSNR moyen** — la référence se rafraîchit, la dérive des frames lointaines est bornée. **4K native (test_4k_video.mp4, 3840×2160, 8 frames, dict sur 4, gop=4) : 4× @ 55,1 dB** (min 34,8 ; 190 Mo → 49,7 Mo) — premier test 4K du projet.

**Le retrieval par blocs (étape j)** : les matrices de distances (M, N) complètes du V2 (`s @ q.T` + `dists`) explosaient en mémoire (640 Mo par shard en 4K) — `encode_v2` requête désormais par blocs de 1024 requêtes ((M, 1024) ≈ 160 Mo, borné quelle que soit la résolution). **Équivalence vérifiée** (B3 natif : 6,0× @ 56,9 dB identique) ; **4K : 49 s/frame (vs 57)** — le goulot était le calcul (produits matriciels), pas les allocations ; le crash mémoire des grandes résolutions est éliminé.

**Le sélecteur 3 modes (étape g — le codec modal P1 comme 3e candidat)** : `encode_select(image, min_psnr)` — V2 DICT / FULL (bit-exact) + **MODAL** (troncature dorée, `hcv2_modal_codec`, magic `HCVM`) candidat **seulement si son PSNR mesuré ≥ min_psnr** — le plus petit gagne. `decode_select` route par magic. **Frontière mesurée (LOO ps=32, 8 images SDI)** :

| min_psnr | Ratio moyen | PSNR moyen | Exactes |
|---|---|---|---|
| None (BEST exact) | 213,2× | 100,0 dB | 8/8 |
| 15-20 | **372,9×** | 64,1 dB | 4/8 |
| 25 | 279,8× | 73,9 dB | 5/8 |
| 30 | 259,2× | 91,9 dB | 7/8 |

Chaque +5 dB de contrainte retire ~50-90× et rend une image exacte — le curseur fonctionne. **Sur les externes** (dict SDI, images jamais vues) : 2,5× → **72,3× moyenne @ 25,8-33,7 dB** (JWST 22,2× · 02_original 193,1×) — le modal récupère le terrain inconnu — **et le critère protège** : `evolution_gen` (incompressible) reste FULL exact 1,6×. Le MODAL à 22-36 dB est du lossy fort assumé : le curseur min_psnr est le contrat (CLI `--min-psnr`, défaut None = exact).

**Ce que cela signifie pour le protocole HCV2** : le dictionnaire est la **Piste 7** — implémentée (héritée de 4e3830d), réparée (3 bugs), et maintenant mesurée. **Le sélecteur optimal `encode_best` + le résidu bit-exact sont en place** (`multimodal/harmonic_codec.py`, CLI `hc.py`) : pour chaque image, le plus petit de V2 DICT / FULL est choisi, le décodeur détecte le format par magic — **44,4× moyenne LOO, 8/8 images bit-exact (PSNR ∞)**. Prochaines étapes : le match_threshold et le patch_size (l'échelle du gain dépend du seuil), puis les briques THU dans le résidu (troncature dorée, chaîne cₙ) au lieu du Delta-H/zstd.

**Ce qui n'existe toujours pas** (les autres candidats éliminés) : `COMPRESSION-SOLUTIONS/HCV_BINARY_LOSSLESS_CODEC/` — les 4 « stratégies » dont DICTIONARY_BASED appellent toutes le même zstd (sorties identiques mesurées, 2 bugs corrigés au passage, 10/10 tests) ; SDI METHOD_2 = zlib par zones ; `COMPRESSION-ORDINAIRE/harmonic_codec_v12_new.py` = Delta-H + zstd + grain (le « Delta-H » existe bien en code) ; git `1cf4c69` « Dictionnaire v2 » = dictionnaire sémantique ondulatoire.

## 3. La découverte commune — la séparation des domaines

Les trois pistes mesurées convergent vers la même loi :

```
Chaque contenu a son domaine :
  · le contenu ORDINAIRE (images, mouvement rapide)  → Fourier, Markov
  · le contenu À MÉMOIRE (bruit 1/f^{1/φ}, scènes     → le DOMAINE DORÉ
    lentes persistantes, le grain capteur)             (FrFT 1/φ, noyau K(t))
```

| Contenu | Fourier/Markov | Domaine doré |
|---|---|---|
| Bruit doré 1/f^{1/φ} (P6) | 0,769-0,776 | **0,870-0,881** (+9-11 points) |
| Scène lente + bruit (P3) | 26,19 dB (Markov) | **28,35 dB** (+2,2 dB) |
| B3 rapide / image ordinaire | **31,2 dB / 0,993** | 21,4 dB / 0,885 |

**La règle** : le domaine doré n'est pas un remplaçant de Fourier — c'est le domaine du contenu **à mémoire**, et l'ordre 1/φ est dérivé (T1), pas choisi. C'est le terrain que la THU seule possède.

## 4. Le pipeline complet — le but

```
VIDÉO (frames)
   │  prédiction dorée K(t) (P3 — la mémoire, T2)
   ▼
résidu (le grain oublié)
   │  codec modal (P1 — troncature dorée + chaîne cₙ, T3)
   ▼
coefficients → entropie dorée (P5 — la distribution pₙ, E3)
   ▼
fichier .hcv2
```

Le pipeline assemble les briques vérifiées : **la prédiction (P3) + le résidu (P1) + l'entropie (P5)** — chaque étage un théorème, zéro paramètre ajusté.

## 5. Le protocole honnête

1. **Mesures sur de vraies images et vidéos** (architecture, paysage, macro, B3) — PSNR/SSIM systématiques (la base a publié des JSON avec PSNR=None : ne pas répéter) ;
2. **Les deux bases de ratio** : vs fichier ET vs RAW — jamais l'une sans l'autre ;
3. **Zéro paramètre ajusté** : chaque constante est un théorème (φ, la chaîne, la distribution, le seuil, le noyau, l'ordre) ;
4. **Les échecs publiés** : la quantification inversée, la normalisation de la chaîne, l'additivité de la première FrFT — trois erreurs attrapées par la mesure, toutes publiées ;
5. **Les frontières déclarées** : la relation de la FrFT discrète à la continue d'Ozaktas, l'avantage de la dorée sur la moyenne en P3, les pistes P2/P4/P5 non encore implémentées.

## 6. La feuille de route

| # | Étape | Livrable |
|---|---|---|
| 1 | ✅ **La synthèse** (ce document) | le dossier complet |
| 2 | 🔄 **Le pipeline complet P1+P3** | le codec vidéo HCV2 — prédiction dorée + résidu modal — benchmark sur B3 vs la base |
| 3 | 📋 La qualité P1 : phases float32, chroma princié | PSNR 19-24 dB → viser 30+ dB |
| 4 | 📋 L'entropie dorée (P5) | le codeur arithmétique à la distribution pₙ |
| 5 | 📋 P2 (holographique) · P4 (grain princié) | les pistes restantes |
| 6 | 🔬 P6 : la vidéo à mémoire dans le domaine doré | le test naturel suivant |
| 7 | ✅ **P7 : le dictionnaire partagé — complet** : trouvé (4e3830d), réparé (3 bugs), BEST + bit-exact + ps=32 : **213,2× LOO, 8/8 bit-exact (∞)** ; seuil inerte ; transfert doré = échec publié ; vidéo : **MC_RESIDUAL · GOP 6,0× @ 56,9 dB (B3 natif) · 4K 4× @ 55,1 dB · I-frame MODAL = échec publié** ; **sélecteur 3 modes : 372,9× @ 64,1 dB (min=20), 72,3× externes** ; retrieval par blocs (mémoire bornée) ; 2 bugs de grille corrigés | le chantier P7 est clos — les suites possibles : le MC search optimisé (le temps 4K restant), le codec modal sur les P-frames à la résolution native, ou le chantier HHD3 (entropie) |

## 7. En une phrase

> **La nouvelle compression harmonique est l'inverse exact de l'ancienne : chaque brique est un théorème de la THU V2 — le seuil doré 1/(φ·m) (P1, vérifié au point optimal), la chaîne cₙ = 1/Γ(n/φ+1) (T3), le noyau K(t) (P2/P3, +2,2 dB sur le contenu à mémoire), la distribution pₙ (P5, E3), l'ordre 1/φ (P6, additivité 9,4×10⁻¹⁶, +9-11 points sur le bruit doré) — la découverte commune est la séparation des domaines : Fourier pour l'ordinaire, le domaine doré pour le contenu à mémoire — et le pipeline complet (prédiction dorée + résidu modal + entropie dorée) est en construction, mesuré sur de vraies images, avec les échecs publiés et les frontières déclarées : la méthode du dépôt appliquée au codec lui-même.**

---

*Synthèse — FIN — trois pistes mesurées, trois à construire, une loi commune (chaque contenu a son domaine), et un pipeline dont chaque étage est un théorème — la nouvelle compression se construit comme la théorie : pièce dérivée par pièce dérivée, mesure par mesure, échec publié par échec publié*
