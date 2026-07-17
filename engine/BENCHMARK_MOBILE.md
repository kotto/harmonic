# 📊 BENCHMARK MOBILE — Harmonic Dictionary Mobile SDK

**Date** : 13 Juillet 2026  
**Auteur** : Alain Kotto  
**Version** : Mobile 1.0

---

## Résumé

Le Harmonic Dictionary est maintenant déployable sur mobile. Le dictionnaire est compressé de **1.5 GB → 977 MB** (RGB565) avec un décodeur minimal de **~200 lignes** (numpy + zstandard uniquement, pas de scipy).

---

## 1. Dictionnaire — Tailles

| Composant | Format | Taille |
|-----------|--------|:------:|
| Signatures | int16 (64B/patch) | **72 MB** |
| Pixels | RGB565 (800B/patch) | **905 MB** |
| Métadonnées | json | ~10 MB |
| **Total** | | **977 MB** |

### Formats de pixels

| Format | Taille pixels | PSNR | Usage |
|--------|:------------:|:----:|-------|
| **Raw uint8** | 1 357 MB | 100 dB | Référence lossless |
| **RGB565** | 905 MB | ~37 dB | Mobile standard |
| JPEG Q85 | ~200 MB | ~45 dB | Mobile compact |
| JPEG Q70 | ~120 MB | ~40 dB | Mobile très compact |

---

## 2. Décodeur mobile

### Code

- `mobile_decoder.py` : ~200 lignes
- Dépendances : `numpy` + `zstandard` (pas scipy, pas PIL pour le décodeur)
- API : `decoder = MobileDecoder(path); image = decoder.decode(bitstream)`

### Roundtrip

```
Encode (serveur)  →  bitstream HHD2 (3 KB pour 400×400, 119.5×)
Decode (mobile)   →  image reconstruite
```

| Métrique | Valeur |
|----------|:------:|
| Ratio (exact match) | **119.5×** |
| PSNR (RGB565 dict) | **37.1 dB** |
| PSNR (JPEG Q85 dict) | ~45 dB |
| PSNR (raw dict) | **100 dB** |

---

## 3. Utilisation

```python
from multimodal.mobile_decoder import MobileDecoder

# Charger le dictionnaire compact
decoder = MobileDecoder('/sdcard/HCV/mobile_dict.hhdm')

# Recevoir un bitstream du serveur
bitstream = receive_from_server()

# Décoder
image = decoder.decode(bitstream)
# → (H, W, 3) uint8 numpy array
```

---

## 4. Prochaine étape : production mobile

1. **Compression native** — C/Rust pour iOS/Android (pas de Python)
2. **Streaming** — décode progressif pour vidéo
3. **Dictionnaire 100 MB** — JPEG Q85 + zstd global
4. **Intégration APK/IPA** — packaging dans l'app
