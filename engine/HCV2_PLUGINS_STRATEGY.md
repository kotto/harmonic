# HCV2 Pro — Stratégie Plugins

## Comment débloquer l'intégration dans les logiciels professionnels

---

## 1. Le problème

| Logiciel | Statut | Impact |
|---|---|---|
| **FFmpeg** | ❌ Aucun | Bloque tout le pipeline pro |
| **DaVinci Resolve** | ❌ Aucun | Bloque post-production |
| **Premiere Pro** | ❌ Aucun | Bloque montage |
| **Avid Media Composer** | ❌ Aucun | Bloque broadcast |

**Sans plugins, HCV2 Pro ne peut pas être adopté en production.**

---

## 2. La stratégie : FFmpeg d'abord, tout le reste via FFmpeg

### 2.1. Pourquoi FFmpeg en premier ?

FFmpeg est le **standard de facto** de l'industrie audiovisuelle :
- DaVinci Resolve l'utilise en interne
- Adobe Media Encoder peut l'appeler
- Avid peut importer ses sorties
- VLC, MPV, GStreamer l'utilisent

**Un plugin FFmpeg = 80% de l'intégration faite.**

### 2.2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FFmpeg                            │
│  ┌─────────────────────────────────────────────┐    │
│  │  libavcodec / libavformat                    │    │
│  │  ┌───────────────────────────────────────┐  │    │
│  │  │  ff_hcv2dec (plugin .so/.dll)         │  │    │
│  │  │  - decode : .hcv2 → RGB               │  │    │
│  │  │  - probe  : détection du format        │  │    │
│  │  └───────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
   DaVinci Resolve  Premiere Pro    Avid MC
   (via FFmpeg)    (via FFmpeg)    (via FFmpeg)
```

---

## 3. Plan de développement (12 semaines)

| Semaine | Plugin | Technologie | Complexité |
|---|---|---|---|
| **1-2** | **FFmpeg decoder** (standalone C) | `ff_hcv2dec.c` — 250 lignes | ✅ Faible |
| **3-4** | **FFmpeg libavfilter** (intégration native) | API FFmpeg `AVCodec` | 🟡 Moyenne |
| **5-6** | **DaVinci Resolve** (script + OpenFX) | Python + OpenFX SDK | 🟡 Moyenne |
| **7-8** | **Premiere Pro** (CEP extension) | JS + CEP SDK | 🟡 Moyenne |
| **9-10** | **Avid MC** (AAX plugin) | C++ + Avid SDK | 🔴 Complexe |
| **11-12** | **Tests + certification** | SMPTE, EBU, tests métier | 🟡 Moyenne |

### Budget total : 25 000 €

---

## 4. Détail par plugin

### 4.1. FFmpeg standalone (semaine 1-2) — ✅ Livré

Fichier : `plugins/ff_hcv2dec.c`

```bash
# Compilation
gcc -O2 -DBUILD_CLI -o ff_hcv2dec ff_hcv2dec.c -lz -lm

# Utilisation
./ff_hcv2dec input.hcv2 output.ppm

# Pipeline FFmpeg
ffmpeg -i input.hcv2 output.png
```

### 4.2. FFmpeg libavfilter (semaine 3-4)

```c
// Exemple d'intégration dans FFmpeg via AVCodec
AVCodec ff_hcv2_decoder = {
    .name = "hcv2",
    .long_name = "HCV2 Harmonique Codec",
    .type = AVMEDIA_TYPE_VIDEO,
    .id = AV_CODEC_ID_HCV2,  // à enregistrer
    .init = hcv2_init,
    .decode = hcv2_decode_frame,
    .close = hcv2_close,
};
```

### 4.3. DaVinci Resolve (semaine 5-6)

```python
# resolve_hcv2.py — Appelé depuis Resolve
import subprocess, sys, os
def decode_hcv2(input_path, output_path):
    subprocess.run(['ff_hcv2dec', input_path, output_path])

# Installation : Copier dans /Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/
```

### 4.4. Premiere Pro (semaine 7-8)

```javascript
// hcv2-cep.js — Extension CEP pour Premiere
const hcv2 = require('./ff_hcv2dec');
hcv2.decode(inputFile, outputFile);
```

### 4.5. Avid Media Composer (semaine 9-10)

```cpp
// hcv2_aax.cpp — Plugin AAX pour Avid
class HCV2Decoder : public AAxDecoder {
    bool DecodeFrame(const uint8_t* input, int inputSize,
                     uint8_t* output, int* outputSize) override {
        return hcv2_decode(input, inputSize, output, &w, &h) == 0;
    }
};
```

---

## 5. Tests et validation

### 5.1. Tests unitaires

```bash
# 1. Fichier valide
./ff_hcv2dec test.hcv2 test.ppm && echo "✅"

# 2. Fichier corrompu (doit échouer proprement)
./ff_hcv2dec /dev/urandom out.ppm 2>/dev/null || echo "✅"

# 3. Pipeline 100 cycles (encode → décode → vérification)
for i in $(seq 100); do
    python -c "
    import hcv2_pro as h
    h.cmd_encode(h.parse_args(['encode', 'test.png', '-o', 'test.hcv2']))
    h.cmd_decode(h.parse_args(['decode', 'test.hcv2', '-o', 'test_restored.png']))
    "
    diff test.png test_restored.png || exit 1
done
echo "✅ 100 cycles sans perte"
```

### 5.2. Certification SMPTE (à venir)

- **SMPTE ST 2067-21** : IMF Application
- **SMPTE ST 2094-1** : Dynamic Metadata
- **SMPTE ST 2036-1** : Ultra High Definition TV

---

## 6. Roadmap d'intégration

| Date | Étape | KPI |
|---|---|---|
| **Semaine 2** | Plugin FFmpeg standalone | `ff_hcv2dec` compile, testé sur 3 OS |
| **Semaine 4** | FFmpeg libavfilter | `ffmpeg -i input.hcv2` fonctionne |
| **Semaine 6** | DaVinci Resolve | Script import/export .hcv2 |
| **Semaine 8** | Premiere Pro | Extension CEP .hcv2 |
| **Semaine 10** | Avid MC | Plugin AAX .hcv2 |
| **Semaine 12** | Certification | Jeu de test SMPTE ✅ |

---

## 7. Conclusion

**La stratégie FFmpeg first est la solution la plus rapide et la plus impactante :**

| Approche | Temps | Couverture | Coût |
|---|---|---|---|
| **FFmpeg d'abord** | 4 semaines | 80% des workflows | 5 000 € |
| Plugins natifs ensuite | 8 semaines | 100% des workflows | 20 000 € |
| **Total** | **12 semaines** | **100%** | **25 000 €** |

Le plugin FFmpeg standalone est déjà livré (`plugins/ff_hcv2dec.c`). Il permet dès maintenant d'intégrer HCV2 dans n'importe quel pipeline via la CLI.