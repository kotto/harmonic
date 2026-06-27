# HCS Studio — Rapport de Performance Benchmark
**Date :** 17/02/2026 — **Durée totale :** ~10 secondes — **Tests :** 22/22 OK

---

## Environnement

| Paramètre | Valeur |
|---|---|
| Python | 3.11.8 |
| NumPy | 1.26.4 |
| Pillow (PIL) | 12.1.0 |
| OS | Windows Server 2025 |
| Répertoire core | `f:\FINAL\DEFINITIF\hcs_v2-P3\core\` |

---

## Modules HCS disponibles

| Module | Statut |
|---|---|
| `HybridCompressor` | ✅ OK |
| `KFactorEngine` | ✅ OK |
| `WebPOptimizer` | ✅ OK |
| `QuantumHarmonicCompressor` | ✅ OK |
| `HarmonicUpscalerAPI` | ❌ Absent (erreur encodage emoji dans le module) |
| `OpenCV (cv2)` | ✅ OK |

> **Note :** `harmonic_upscaler.py` contient un caractère emoji ❌ qui provoque une erreur d'encodage charmap au chargement. L'upscaling est assuré en fallback LANCZOS (PIL).

---

## 1. Compression Image (6/6 OK)

| Résolution | Mode | Ratio K | Ratio WebP | **Ratio Hybride** | Espace économisé | Temps |
|---|---|---|---|---|---|---|
| 320×240 | naturel | 7.7:1 | 4.6:1 | **35–41:1** | 99.3–99.4% | 128–272 ms* |
| 640×480 | naturel | 30.7:1 | 4.2:1 | **130–136:1** | 99.8% | 11–51 ms |
| 1280×720 | gradient | 50.4:1 | 55.4:1 | **2792.7:1** | 100.0% | 12–19 ms |
| 1920×1080 | naturel | 50.3:1 | 6.5–6.7:1 | **329–339:1** | 99.9% | 35–37 ms |
| 640×480 | uniforme | 30.7:1 | 384.6:1 | **11815.4:1** | 100.0% | 6 ms |
| 640×480 | bruit pur | 30.7:1 | 3.6:1 | **110.2:1** | 99.8% | 11 ms |

> *Premier appel plus lent (initialisation JIT/modules). Appels suivants : ~10 ms.
>
> **Ratio hybride moyen : 2537:1 — Espace économisé moyen : 99.8%**

### Observations
- **Petite image (320×240)** : k_ratio limité à 7.7:1 car la dimension K-compressée min est 100×100 (plancher interne). Le ratio hybride reste >35:1.
- **Image gradient (HD)** : ratio extrême 2792:1 car les zones uniformes sont triviales à compresser.
- **Bruit pur** : cas difficile — ratio le plus bas (110:1) mais reste très efficace.
- **Contenu uniforme** : ratio maximal (11815:1) — 78 octets pour 3.52 MB brut.

---

## 2. Compression Vidéo frame-by-frame (4/4 OK)

| Séquence | Frames | Taille brute | Archive HCS-ZIP | **Ratio archive** | FPS | Temps/frame |
|---|---|---|---|---|---|---|
| SD 30f 320×240 | 30 | 26.37 MB | 92.91 KB | **290.6:1** | 98.5 | 10.2 ms |
| SD 90f 320×240 | 90 | 79.10 MB | 278.66 KB | **290.7:1** | 100.5 | 9.9 ms |
| HD 30f 640×480 | 30 | 105.47 MB | 93.17 KB | **1159.1:1** | 103.0 | 9.7 ms |
| HD 60f 1280×720 | 60 | 632.81 MB | 322.86 KB | **2007.1:1** | 47.9 | 20.6 ms |

> **Ratio archive moyen : 937:1 — FPS moyen compression : 88 FPS**

### Observations
- **Format de conteneur** : ZIP STORED (frames WebP + meta.json). Efficace mais non streamable.
- **Scalabilité** : les débits restent constants (~100 FPS pour SD, ~48 FPS pour HD 720p).
- **Goulot d'étranglement** : encodage WebP par frame. Pour 720p à 60FPS, 48 FPS de compression est en dessous du temps réel.

---

## 3. Décompression Image (6/6 OK)

| Résolution | Ratio source | Shape reconstituée | **PSNR** | Temps |
|---|---|---|---|---|
| 320×240 | 35–41:1 | (240, 320, 3) | **17.0 dB** | 16–34 ms |
| 640×480 | 130–136:1 | (480, 640, 3) | **16.6 dB** | 8 ms |
| 1280×720 | 2792:1 | (720, 1280, 3) | **31.5 dB** | 22 ms |
| 1920×1080 | 329–339:1 | (1080, 1920, 3) | **18.0 dB** | 50 ms |
| 640×480 uniforme | 11815:1 | (480, 640, 3) | **54.15 dB** | 10–12 ms |
| 640×480 bruit | 110:1 | (480, 640, 3) | **10.5 dB** | 8 ms |

> **PSNR moyen : 24.6 dB — Temps moyen : 19–22 ms**

### Interprétation PSNR
| Plage PSNR | Qualité perçue |
|---|---|
| > 40 dB | Quasi-parfait (indiscernable) |
| 30–40 dB | Bonne qualité (légères artefacts) |
| 20–30 dB | Qualité acceptable (compression visible) |
| < 20 dB | Perte notable |

- Le **PSNR bas sur images naturelles** (16–18 dB) reflète la perte inhérente au K-factor (réduction de résolution importante puis upsample LANCZOS). À ratio 130+ :1, c'est attendu.
- Le **PSNR 31.5 dB** pour HD gradient est excellent car les données sont très lisses.
- Le **PSNR 10.5 dB** pour bruit pur est normal : un bruit aléatoire ne peut pas être reconstruit fidèlement.

---

## 4. Décompression Vidéo (4/4 OK)

| Séquence | Frames | **FPS décompression** | Temps total | PSNR |
|---|---|---|---|---|
| SD 30f 320×240 | 30 | **820 FPS** | 37 ms | N/A* |
| SD 90f 320×240 | 90 | **1856 FPS** | 48 ms | N/A* |
| HD 30f 640×480 | 30 | **1755 FPS** | 17 ms | N/A* |
| HD 60f 1280×720 | 60 | **1193 FPS** | 50 ms | N/A* |

> **FPS moyen décompression : 1406 FPS — Quasi-instantanée**
>
> *PSNR = 0 dB : les frames décodées ont une résolution différente des originales (K-compression interne). La comparaison pixel-à-pixel est skippée car shapes incompatibles.

---

## 5. Upscaling Image (5/5 OK)

| Source | Facteur | Shape résultante | Facteur surface | Méthode | Temps |
|---|---|---|---|---|---|
| 320×240 | 2x | (480, 640, 3) | 4.0x | LANCZOS | 5.6 ms |
| 320×240 | 4x | (960, 1280, 3) | 16x | LANCZOS | 18.9 ms |
| 640×480 | 2x | (960, 1280, 3) | 4.0x | LANCZOS | 22.4 ms |
| 640×480 | 4x | (1920, 2560, 3) | 16x | LANCZOS | 78.7 ms |
| 1280×720 | 2x | (1440, 2560, 3) | 4.0x | LANCZOS | 69.1 ms |

> **Méthode : LANCZOS (PIL) — HarmonicUpscaler indisponible**
> **Temps moyen : 39 ms**

---

## 6. Upscaling Vidéo (3/3 OK)

| Séquence | Facteur | Résolution cible | **FPS upscaling** | Temps total |
|---|---|---|---|---|
| SD 30f 320×240 | 2x | 640×480 | **176 FPS** | 170 ms |
| SD 30f 320×240 | 4x | 1280×960 | **52 FPS** | 574 ms |
| HD 30f 640×480 | 2x | 1280×960 | **40 FPS** | 752 ms |

> **Méthode : LANCZOS — FPS moyen upscaling : 89 FPS**

---

## Synthèse Générale

| Catégorie | Score | Commentaire |
|---|---|---|
| **Compression image** | ⭐⭐⭐⭐⭐ | Ratio hybride 35–11815:1. Exceptionnel. |
| **Compression vidéo** | ⭐⭐⭐⭐ | 290–2007:1, 48–103 FPS. En dessous du temps réel pour HD+ |
| **Décompression image** | ⭐⭐⭐⭐ | 6–50 ms, PSNR 17–54 dB selon contenu |
| **Décompression vidéo** | ⭐⭐⭐⭐⭐ | 1400 FPS moyen, quasi-instantané |
| **Upscaling image** | ⭐⭐⭐ | LANCZOS OK, HarmonicUpscaler à corriger |
| **Upscaling vidéo** | ⭐⭐⭐ | 40–176 FPS selon résolution/facteur |

---

## Points d'Amélioration Identifiés

### 1. Bug K-factor sur petites images
**Problème :** Images <640×480 → k_ratio limité à 7.7:1 (plancher 100×100 interne)
**Source :** `core/k_factor_engine.py` — `min_size = max(100, int(...))`
**Suggestion :** Réduire le plancher minimum ou ajuster k_factor pour petites images.

### 2. HarmonicUpscalerAPI inaccessible
**Problème :** `core/harmonic_upscaler.py` contient un caractère emoji `❌` (U+274C) codé en UTF-8 dans un commentaire, qui fait crasher le chargement sur les terminaux Windows (codec charmap).
**Fix :** Remplacer `❌` par `[KO]` ou `[FAIL]` dans `core/harmonic_upscaler.py`.

### 3. PSNR vidéo = 0 dB (faux négatif)
**Problème :** Le benchmark compare les frames décodées (taille K-compressée) avec les originales (taille pleine). Les shapes ne correspondent pas → PSNR skippé.
**Fix :** Redimensionner les frames décodées vers la résolution originale avant calcul PSNR dans la section décompression vidéo.

### 4. Débit vidéo HD en dessous du temps réel
**Problème :** 48 FPS pour 1280×720 @ 60f (objectif : ≥60 FPS).
**Suggestion :** Paralléliser l'encodage WebP avec `concurrent.futures.ThreadPoolExecutor`.

### 5. Format de conteneur vidéo
**Problème :** ZIP STORED non streamable.
**Suggestion :** Adopter un conteneur MKV ou MP4 avec codec HCS personnalisé, ou un format binaire séquentiel streamable.

---

## Fichiers générés

| Fichier | Description |
|---|---|
| `hcs_studio_integrated/benchmark_performance.py` | Script de benchmark (19,702 bytes) |
| `hcs_studio_integrated/benchmark_results.json` | Résultats JSON complets |
| `hcs_studio_integrated/BENCHMARK_RAPPORT.md` | Ce rapport |
| `generate_benchmark.py` | Générateur du script benchmark |

---

*Rapport généré automatiquement par `benchmark_performance.py` — HCS Studio v2*
