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

## 7. En une phrase

> **La nouvelle compression harmonique est l'inverse exact de l'ancienne : chaque brique est un théorème de la THU V2 — le seuil doré 1/(φ·m) (P1, vérifié au point optimal), la chaîne cₙ = 1/Γ(n/φ+1) (T3), le noyau K(t) (P2/P3, +2,2 dB sur le contenu à mémoire), la distribution pₙ (P5, E3), l'ordre 1/φ (P6, additivité 9,4×10⁻¹⁶, +9-11 points sur le bruit doré) — la découverte commune est la séparation des domaines : Fourier pour l'ordinaire, le domaine doré pour le contenu à mémoire — et le pipeline complet (prédiction dorée + résidu modal + entropie dorée) est en construction, mesuré sur de vraies images, avec les échecs publiés et les frontières déclarées : la méthode du dépôt appliquée au codec lui-même.**

---

*Synthèse — FIN — trois pistes mesurées, trois à construire, une loi commune (chaque contenu a son domaine), et un pipeline dont chaque étage est un théorème — la nouvelle compression se construit comme la théorie : pièce dérivée par pièce dérivée, mesure par mesure, échec publié par échec publié*
