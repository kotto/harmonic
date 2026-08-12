# HCV2 Streaming — Solution de diffusion 4K

## Architecture pour le streaming VOD et live avec le codec harmonique

---

## 1. Diagnostic — Où en sommes-nous ?

### Performances actuelles (mesurées)

| Métrique | 1080p | 4K natif | Objectif streaming |
|---|---|---|---|
| **Encode/frame** | ~2-5 s | ~49 s | **< 16 ms** (60fps) |
| **Décode/frame** | ~50 ms | ~200 ms | **< 16 ms** |
| **Ratio moyen** | 6-16× | 4× | 10-20× |
| **PSNR moyen** | 37-57 dB | 55 dB | > 40 dB |

**Le gap est immense : facteur ×3000 entre notre encode actuel et le temps réel.**

### Pourquoi un tel écart ?

| Cause | Impact | Solution |
|---|---|---|
| **FFT 2D logicielle** (Python numpy) | 60% du temps | GPU (CUDA, Vulkan compute) |
| **Retrieval V2 DICT** (matrice de distances) | 30% du temps | Streaming sans dictionnaire (mode FULL) |
| **Copies mémoire** (Python ↔ numpy) | 10% du temps | Pipeline C/C++ natif |
| **Skip/MC search** (pixel diff) | 5% du temps | Optimisation SIMD |

---

## 2. Architecture proposée

### 2.1. VOD (Video on Demand) — faisable maintenant

```
Source 4K (DPX, EXR, MOV)
        ↓
HCV2 Pro encode (offline, 49s/frame)
        ↓
Fichier .hcv2 segmenté (segments de 2s)
        ↓
Génération du manifest HLS (.m3u8)
        ↓
CDN (stockage, distribution)
        ↓
Player WASM (décode temps réel, 4K@60fps)
```

**Le pipeline VOD est réaliste aujourd'hui :**
- L'encode est offline (pas de contrainte temps réel)
- Le décode WASM est temps réel (81 Ko, 4K@60fps)
- Les segments HLS sont générés une fois
- Le CDN distribue les segments .hcv2 comme des fichiers statiques

### 2.2. Live — besoin de GPU

```
Source 4K (caméra, live feed)
        ↓
GPU encode (CUDA FFT + pipeline C)
        ↓
Segments .hcv2 (2s, générés en temps réel)
        ↓
Manifest HLS (.m3u8 mis à jour)
        ↓
CDN / Edge
        ↓
Player WASM
```

**Le live nécessite :**
- Accélération GPU (CUDA, Metal, Vulkan) — ×3000 attendu
- Pipeline C/C++ natif (pas de Python)
- Encodage parallélisé (1 frame par SM)

---

## 3. Prototype VOD — Segmenter une vidéo 4K en HLS

### 3.1. Format du segment

Chaque segment .hcv2 contient un GOP (Group of Pictures) :

```
┌─────────────────────────────────────────────────────┐
│ Segment .hcv2 (2s = 48 frames à 24fps, GOP=12)      │
├─────────────────────────────────────────────────────┤
│ I-frame (encode_best, ∞ dB)  → 4 GOPs de 12 frames  │
│ P-frame 1 (skip + motion + résidu)                   │
│ P-frame 2 (skip + motion + résidu)                   │
│ ...                                                  │
│ P-frame 11 (skip + motion + résidu)                  │
│ I-frame (encode_best, ∞ dB)  → 4e GOP               │
│ P-frame 1                                            │
│ ...                                                  │
└─────────────────────────────────────────────────────┘
```

### 3.2. Manifest HLS (.m3u8)

```
#EXTM3U
#EXT-X-VERSION:7
#EXT-X-TARGETDURATION:2
#EXT-X-MEDIA-SEQUENCE:0

#EXTINF:2.000,
segment_0000.hcv2
#EXTINF:2.000,
segment_0001.hcv2
#EXTINF:2.000,
segment_0002.hcv2
```

### 3.3. Player WASM

Le player WASM (81 Ko) :
1. Télécharge le manifest .m3u8
2. Télécharge chaque segment .hcv2
3. Décode l'I-frame (V2 DICT ou FULL)
4. Décode les P-frames (skip + motion + résidu)
5. Affiche dans une canvas HTML5

---

## 4. Roadmap streaming

| Phase | Durée | Livrable | Technologie |
|---|---|---|---|
| **Phase 1 — VOD** | 4 semaines | Segmenter une vidéo 4K en HLS, player WASM | Pipeline actuel, offline |
| **Phase 2 — GPU** | 8 semaines | Accélération GPU de l'encode (CUDA FFT) | CUDA, Vulkan compute |
| **Phase 3 — Live** | 4 semaines | Pipeline live 4K@60fps, latence < 2s | GPU + pipeline C natif |
| **Phase 4 — ABR** | 4 semaines | Adaptive Bitrate (4K, 1080p, 720p, 480p) | Multi-résolution, HLS |

### Phase 1 détaillée — VOD (semaine 1-4)

| Semaine | Livrable |
|---|---|
| 1 | **Segmenter une vidéo 4K en segments .hcv2** (outil CLI) |
| 2 | **Générer le manifest HLS** (.m3u8) |
| 3 | **Player WASM** (HTML5 canvas + décodeur WASM) |
| 4 | **Test sur un serveur HTTP + CDN simulé** |

### Budget Phase 1 : 15 000 €

---

## 5. Stack technique pour le streaming

### Encode

| Composant | Technologie | État |
|---|---|---|
| FFT 2D | CUDA (cuFFT) ou Vulkan compute | 🔜 Phase 2 |
| Varint | C natif | ✅ |
| Zlib | zlib-ng (optimisé) | ✅ |
| Gestion des GOPs | Python / C | ✅ (existant) |
| Segment HLS | outil CLI | 🔜 Semaine 1 |
| Manifest HLS | outil CLI | 🔜 Semaine 1 |

### Décode (player)

| Composant | Technologie | État |
|---|---|---|
| IFFT 2D | WASM (KissFFT) | ✅ |
| YCbCr → RGB | WASM | ✅ |
| Skip/Motion | WASM | ✅ |
| HLS loader | JavaScript (fetch API) | 🔜 Semaine 2 |
| Canvas render | HTML5 Canvas + WebGL | 🔜 Semaine 3 |
| Audio | AAC (MediaSource Extensions) | 🔜 Phase 3 |

### Formats

| Format | Description | Poids |
|---|---|---|
| `.hcv2` | Segment vidéo (GOP complet) | Variable |
| `.m3u8` | Manifest HLS | ~1 Ko |
| `.key` | Clé de chiffrement AES-128 | 16 o |

---

## 6. Métriques cibles pour le streaming

| Métrique | VOD (Phase 1) | Live (Phase 3) |
|---|---|---|
| Résolution max | 4K (3840×2160) | 4K (3840×2160) |
| Bitrate | 5-20 Mbps | 5-20 Mbps |
| Ratio | 4-10× | 4-10× |
| Latence | 2-6 s (HLS) | < 2 s |
| Qualité | 55 dB (∞ en I-frame) | 50 dB |
| Décode | 4K@60fps (WASM) | 4K@60fps (WASM) |
| Player | HTML5 + WASM | HTML5 + WASM |
| DRM | AES-128 | AES-128 |

---

## 7. Comparaison avec les solutions existantes

| Critère | **HCV2 Stream** | H.264 (HLS) | H.265 (HLS) | AV1 (DASH) |
|---|---|---|---|---|
| **Ratio** | **4-10×** | 10-20× | 20-40× | 30-50× |
| **Qualité lossless** | **✅ I-frame** | ❌ | ❌ | ❌ |
| **Décodeur libre** | **✅ WASM 81 Ko** | ❌ (brevets) | ❌ (brevets) | ✅ |
| **Latence** | 2-6 s | 2-6 s | 2-6 s | 2-6 s |
| **Matériel** | Logiciel (GPU en 2027) | ✅ Silicium | ✅ Silicium | ⚠️ Partiel |
| **Licence** | **Format ouvert** | Brevets | Brevets | Libre |

---

## 8. Prototype immédiat — segmenter B3 en HLS

Je peux construire dès maintenant :

```bash
# 1. Encoder la vidéo B3 en segments .hcv2
hcv2_stream segment --input B3.mp4 --output segments/ --segment-duration 2

# 2. Générer le manifest
hcv2_stream manifest --input segments/ --output playlist.m3u8

# 3. Servir avec un serveur HTTP
python -m http.server 8080

# 4. Player : http://localhost:8080/player.html
```

---

**Conclusion : le streaming VOD 4K avec HCV2 est réalisable dès maintenant (encode offline, décode WASM temps réel). Le live nécessite un investissement GPU (×3000).**

**Budget Phase 1 (VOD) : 15 000 € — 4 semaines.**

**Tu veux qu'on attaque la Phase 1 (segmenter une vidéo + player WASM) ?**