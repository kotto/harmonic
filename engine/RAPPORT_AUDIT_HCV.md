# 📋 RAPPORT_AUDIT_HCV — L'état réel de l'écosystème HCV dans le workspace

**Audit complet du projet de compression « harmonique » — ce qui est réel, ce qui est enrobage, ce qui est fiction**
**Date** : 11/08/2026 — **Auteur** : Univers-Holistique (Kotto Alain)
**Statut** : Audit factuel — chaque affirmation cite un fichier et une ligne — la méthode : nommer ce qui est, déclarer ce qui reste
**Corrigé le 11/08/2026** : la conclusion « lossless parfait contredit » était trop large — le mode LOSSLESS bit-à-bit de la base SDI est réel et mesuré (15,17×, PSNR ∞, cf. §6). La fiction n'est pas le mode, mais son association aux ratios 200-423:1 et au grain synthétique régénéré.

---

> *« Le projet HCV est un écosystème réel de 34 Mo avec des codecs exécutables — et un écart documenté entre ce qu'il fait (compression d'image classique : downscale, JPEG, zstd, ffmpeg) et ce qu'il raconte (codec harmonique, 30×, lossless parfait, format HCV16). Cet audit publie l'écart — comme X1 et X4 ont publié le leur. »*

---

## TABLE DES MATIÈRES

1. [La synthèse — trois niveaux de réalité](#1-la-synthèse)
2. [L'inventaire des projets](#2-linventaire-des-projets)
3. [Les algorithmes réels — trois pipelines](#3-les-algorithmes-réels)
4. [Le format HCV16 — une spec jamais codée](#4-le-format-hcv16)
5. [Le WASM — un placeholder](#5-le-wasm)
6. [Les mesures réelles vs les revendications](#6-les-mesures-vs-les-revendications)
7. [Les revendications commerciales](#7-les-revendications-commerciales)
8. [Le verdict — ce qui marche, ce qui enrobe, ce qui est fiction](#8-le-verdict)
9. [Les recommandations](#9-les-recommandations)
10. [En une phrase](#10-en-une-phrase)

---

## 1. La synthèse — trois niveaux de réalité

| Niveau | Contenu | Verdict |
|---|---|---|
| **RÉEL — exécutable** | 3 pipelines de compression standards (OpenCV + zstd + ffmpeg), API Flask/Express, déploiement AWS/Render, intégration mobile (bridge, file_watcher, KA Mobile) | ✅ **ça fonctionne** |
| **ENROBAGE — vocabulaire** | « H264 Intra » = JPEG réétiqueté · « séparation grain harmonique » = medianBlur · « Delta-H » = différences horizontales · « 30× » = downscale | ⚠️ **le nom dépasse la chose** |
| **FICTION — documentaire** | Format HCV16 (spec complète, jamais codée) · binaire WASM (placeholder) · « lossless parfait » associé aux ratios 200-423:1 (gradients + base RAW gonflée — le mode LOSSLESS bit-à-bit, lui, est réel et mesuré : 15,17× PSNR ∞, cf. §6) · ratios 30×/423:1 sur images synthétiques vendus comme réels | ❌ **jamais implémenté ni mesuré** — sauf le mode LOSSLESS, réel et mesuré |

## 2. L'inventaire des projets

| Projet | Contenu | État |
|---|---|---|
| **HCV-Compression-Engine** (34 Mo) | Le cœur : `codecs/` (6 codecs Python), `api/` (Express), `mobile/` (bridge WebSocket, file_watcher), `wasm/`, `aws-deploy/` (déploiement complet), `docs/` | ✅ réel — **aucun tests/ ni benchmarks/** |
| **HCV-PROJECT · HCV-PRO-PRO-PROJECT** | Dossiers **vides** | ❌ |
| **HCV-PRO-AWS · HCV-PRO-AWS-DEPLOY** | Squelettes de déploiement — le DEPLOY a `codecs/` **vide** | ⚠️ squelettes |
| **HCV-PRO-PROJECT** | Docs + copies des codecs (identiques) | ⚠️ redondant |
| **HCV_Project** | **Copie imbriquée de l'arborescence parente** | ❌ parasite |
| **QWEN35_MOE_HCV_HARMONIC** | Compression de **modèles IA** (quantification vectorielle de poids) — pas un codec image | ℹ️ autre domaine |

## 3. Les algorithmes réels — trois pipelines

| Codec | Pipeline réel (fichier:ligne) | Ce que « harmonique » veut dire ici |
|---|---|---|
| `hcv_android_boost_codec.py` | downscale Lanczos adaptatif → **JPEG** (`cv2.imencode('.jpg')` l.141) → **zstd L19** | « H264 Intra » (l.119-129) = **un JPEG réétiqueté** ; ratios commentés 3-12:1, jamais mesurés ; les images de test sont **synthétiques** (l.559) |
| `hcv_pro_codec.py` | `cv2.medianBlur` (le « signal ») + **Delta-H** = différences horizontales int32 (l.100-104) → zstd L11 + grain régénéré déterministe (l.149-194) | Le seul vrai élément « delta » de l'écosystème — l'étage entropique est **zstd**, pas un codec maison |
| `hcv_video_boost_codec.py` | **ffmpeg** : `scale=lanczos` + `libx264 -crf` (l.347-353) | « HCVB » = header 32 o + **MP4 standard** |

**La vérité sur « Delta-H »** : il existe en code (différences horizontales int16/int32 + zstd — `hcv_pro_codec.py` l.100-109, `COMPRESSION-CAMERA/METHOD_2_SDI_LIKE_IMAGE_COMPRESSION/hcv_image_codec.py` l.136-194, et `COMPRESSION-ORDINAIRE/harmonic_codec_v12_new.py` `_dh_enc`/`_dh_dec`) — **et il existe un VRAI codec à dictionnaire dans le dépôt** : `engine/multimodal/` (commit `4e3830d`, toutes les branches, jamais documenté) — `harmonic_codec.py` (formats HHDC/HHD2 : retrieval de patches 16×16 par signatures DFT dans des shards KD-tree, IDs 8 o par patch exact, résidus DCT 2D + zigzag + RLE + zstd, vidéo motion+dict+skip). Il était cassé depuis l'origine (import `hcv_bridge` inexistant + dataclass `HarmonicPatch` mal appelé) — réparé et mesuré le 11/08/2026 : **41,9× moyenne leave-one-out @ PSNR 64-100 dB sur images jamais vues** (vs 4,7× pour le Delta-H+zstd autonome — cf. `COMPRESSION_HARMONIQUE_V2_PISTES.md` §2bis). Le reste de l'écosystème (HCV-Compression-Engine, SDI) : l'étage entropique est zstandard, et OpenCV/ffmpeg font le gros du travail.

## 4. Le format HCV16 — une spec jamais codée

`HCV16_Format_Specification.md` décrit un **conteneur binaire cohérent et théorique** : header 256 o (magic 'HCV1', CRC32, modèle de grain, index frames…). **Aucun code de l'écosystème n'implémente ce conteneur** : les codecs réels utilisent d'autres magics (HCVP, HCAB, HCVB, HCI1) avec des headers de 14-32 octets. La spec est un **cahier des charges sans implémentation**.

## 5. Le WASM — un placeholder

`wasm/delta_h.js` est un loader réel (`WebAssembly.instantiate`) mais `delta_h.wasm` (557 o) commence par `// Placeholder for Delta-H WASM module` — **aucun binaire** : l'instantiation échouerait. Les seuls fichiers C (`hcv_decoder.c/.h`) ne sont référencés nulle part.

## 6. Les mesures réelles vs les revendications

| Mesure | Réalité (fichier) | Revendication |
|---|---|---|
| **Ratio réel sur données réelles** | **8,51×** sur B3.mp4 (H.264, 10 frames, QP=3) — `HCV_SDI_validation_report.md` — la **seule mesure réelle** de l'écosystème | « 30× » — jamais mesuré, présent seulement dans les documents de papier (`PAPER_HCV_PRO.md`, `DOUBLE_FENTE_POUR_TOUS.md`) |
| **Ratios sur images synthétiques** | 200-423:1 sur **gradients** (calculés vs taille RAW — une PNG de 34 Ko comptée à 15,7 Mo !) — `sdi_image_metrics_*.json` | vendus comme ratios réels |
| **Qualité** | **PSNR/SSIM = None partout** dans les JSON de mesure — la qualité n'a jamais été mesurée sur ces ratios | « sans perte visible » |
| **Lossless** | **Mode LOSSLESS implémenté et mesuré** : 15,17× bit-à-bit, PSNR ∞ (référence du chantier HCV2 — `benchmark_hcv2_modal.py` l.41, reprise dans `COMPRESSION_HARMONIQUE_V2_PISTES.md` §1 : « PSNR ∞ · SSIM 1,0 — confirmé »). Les JSON anciens (`sdi_image_metrics_lossless.json`) n'ont ni PSNR ni SSIM et leurs ratios 200× viennent de la base RAW gonflée (PNG 34 Ko comptée à 15,7 Mo) ; la mention « Bit-exact not yet implemented » (`HCV_IMAGE_CODEC_TEST_REPORT.md` l.163) date d'avant l'implémentation | « lossless parfait » (`HCV16_Commercial_Document.md` l.49-51) — la fiction n'est pas le mode (réel, PSNR ∞) mais son **association aux ratios 200-423:1** et au grain synthétique : le mode GRAIN_SYNTH régénère un grain ≠ original (PSNR ~50-55 dB — c'est sa définition, pas un bug) |
| **PSNR réel** | 51,22 dB (B3, 10 frames) — la seule mesure de qualité réelle | — |

## 7. Les revendications commerciales

`HCV16_Commercial_Document.md` : « 9.56× à 16.19× », « lossless parfait (PSNR ∞, SSIM=1.0) », projections marché 1,25 M€ à 90 M€ — **contredites par le code et les mesures** : le grain régénéré n'est pas bit-exact, les ratios viennent de gradients, la qualité n'a pas été mesurée. `SUMMARY.txt` (17/04/2026) revendique « Broadcast 26-33:1 » et « Universal 1.2-345:1 » avec **aucun artefact de test joint**.

## 8. Le verdict — ce qui marche, ce qui enrobe, ce qui est fiction

```
✅ MARCHE (réel, exécutable) :
   - 3 pipelines de compression (downscale+JPEG+zstd · delta+zstd+grain ·
     ffmpeg/H.264) — une compression d'image STANDARD, fonctionnelle
   - L'intégration complète : API Express, déploiement AWS/Render,
     mobile (bridge, file_watcher), KA Mobile (optimiseur, .hcv, X-Codec),
     le pont agentique memory-first (hcv_compress)
   - La seule mesure honnête : 8,51× @ 51,22 dB (B3, 10 frames)

⚠️ ENROBE (le nom dépasse la chose) :
   - « H264 Intra » = JPEG · « grain harmonique » = medianBlur ·
     « Delta-H » = différences horizontales · « 30× » = downscale
   - Le PSNR est mesuré pour surveiller, pas pour garantir

❌ FICTION (jamais implémenté ni mesuré) :
   - Le format HCV16 (spec complète, zéro code)
   - Le binaire WASM (placeholder) — et l'algorithme qu'il décrit
   - Le « lossless parfait » associé aux ratios 200-423:1 et au grain synthétique régénéré — le mode LOSSLESS bit-à-bit, lui, est réel et mesuré (15,17×, PSNR ∞) ; le grain régénéré n'est pas bit-exact car c'est le mode GRAIN_SYNTH (PSNR ~50-55 dB, par définition)
   - Les ratios 30×/345×/423× (jamais mesurés sur données réelles)
```

## 9. Les recommandations

1. **Déclasser et renommer** : « HCV v1 = compression d'image par downscale + JPEG/delta + zstd, avec surveillance PSNR » — aligner le marketing sur les mesures réelles (8,51× @ 51,22 dB est une vraie performance, honnête et vérifiable) ;
2. **Mesurer sur de vraies images** : un benchmark public sur un corpus réel (photos/vidéos réelles, PSNR/SSIM systématiques) — les JSON actuels avec PSNR=None doivent être refaits ;
3. **Déclarer les frontières** : le format HCV16, le WASM et le codec entropique « harmonique » deviennent des **frontières de recherche** (comme E1b/E1c) — pas des fonctionnalités ;
4. **Décider du vrai Delta-H** : écrire le codec entropique maison (les briques existent dans le dépôt THU : la chaîne dérivée, le langage ondulatoire) — ou le déclarer ouvert ;
5. **Nettoyer le workspace** : les projets vides (HCV-PROJECT, HCV-PRO-PRO-PROJECT), la copie imbriquée (HCV_Project) et les squelettes sans codec doivent être archivés ou supprimés.

## 10. En une phrase

> **Le projet HCV est réel — trois pipelines de compression standards exécutables (downscale + JPEG/delta + zstd + ffmpeg), une intégration complète (API, déploiement, mobile, agentique) et une seule mesure honnête (8,51× @ 51,22 dB) — mais l'écosystème vend comme « harmonique » ce qui est une compression d'image classique : « H264 Intra » est un JPEG réétiqueté, « Delta-H » est des différences horizontales avec zstd, le format HCV16 n'a jamais été codé, le binaire WASM est un placeholder, et les ratios 30×/345× sont des documents de papier mesurés sur des gradients avec PSNR=None — l'audit publie l'écart (comme X1 et X4 ont publié le leur) et la recommandation est simple : renommer ce qui marche (une vraie compression, mesurable), déclarer ce qui reste (le codec harmonique, une frontière), et mesurer avant de vendre.**

---

*Rapport d'audit — FIN — chaque affirmation cite un fichier et une ligne ; la méthode du projet appliquée au projet lui-même : ce qui est vérifié est nommé, ce qui est affirmé est déclaré, ce qui est fiction est publié*
