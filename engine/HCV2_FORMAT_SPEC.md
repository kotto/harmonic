# HCV2 Format Specification v1.0
## Format de compression harmonique .hcv2

---

## 1. Aperçu

Le format `.hcv2` est un format de compression d'image et vidéo basé sur la Théorie Harmonique Universelle (THU). Il supporte 4 modes de compression, du lossless (∞ dB) au très compressé (527×).

## 2. Structure du fichier

```
┌────────────────────────────────────────────────────────────┐
│ Header (12 o)  │  Payload (variable)                       │
├────────────────────────────────────────────────────────────┤
│ Magic + Meta   │  Mode-specific data + zlib                │
└────────────────────────────────────────────────────────────┘
```

## 3. Header (12 octets)

| Offset | Taille | Champ | Description |
|---|---|---|---|
| 0 | 4 | `height` | Hauteur de l'image en pixels (uint32 LE) |
| 4 | 4 | `width` | Largeur de l'image en pixels (uint32 LE) |
| 8 | 1 | `version` | Version du format : `0x01` |
| 9 | 1 | `precision` | Précision des coefficients : `0x00` = float16, `0x01` = float32 |
| 10 | 1 | `bit_depth` | Profondeur de bits : `8` (SDR), `10`, `12`, `16` (HDR) |
| 11 | 1 | `reserved` | Réservé (0x00) |

**Contraintes** : `height` ≤ 65535, `width` ≤ 65535, `version` = 0x01.

## 4. Modes de compression (magic 4 octets)

Le payload commence par un magic de 4 octets qui identifie le mode :

| Magic | Mode | Description | Ratio typique | Qualité |
|---|---|---|---|---|
| `HCVM` | **MODAL** | Troncature dorée (FFT + Parseval + varint + zlib) | 527× | 29 dB |
| `HCVH` | **HYBRID** | MODAL + corrections FULL sélectives | 3-22× | 40-47 dB |
| `HHD2` | **DICT V2** | Dictionnaire partagé + résidu Delta-H exact | 213× | ∞ (lossless) |
| `HHDC` | **FULL** | Delta-H + zstd, autonome, sans dictionnaire | 2,9× | ∞ (lossless) |

### 4.1. Mode HCVM (MODAL)

```
┌─────────────────────────────────────────────────┐
│ Magic 'HCVM' (4 o)  │  Zlib data (variable)     │
└─────────────────────────────────────────────────┘
```

Le zlib data contient 3 canaux (Y, Cb, Cr) dans l'ordre :

| Canal | Résolution | Description |
|---|---|---|
| Y (Luminance) | `height` × `width` | Pleine résolution |
| Cb (Chrominance) | `ceil(height/2)` × `ceil(width/2)` | Sous-échantillonné 2× |
| Cr (Chrominance) | `ceil(height/2)` × `ceil(width/2)` | Sous-échantillonné 2× |

Chaque canal contient :

| Champ | Taille | Description |
|---|---|---|
| `mask` | `(H*W+7)/8` o | Bitmap des coefficients FFT gardés (seuil doré 1/(φ·N)) |
| `varint_deltas` | variable | Deltas des indices des coefficients (varint uint32) |
| `mags` | `n_keep × 2/4` o | Amplitudes normalisées (float16 ou float32) |
| `phases` | `n_keep × 2/4` o | Phases (float16 ou float32) |
| `max_mag` | 8 o | Facteur de normalisation (float64) |

### 4.2. Mode HHD2 (DICT V2)

```
┌─────────────────────────────────────────────────────────────┐
│ Magic 'HHD2' (4 o)  │  Version (1 o)  │  ps (2 o)  │  ...  │
└─────────────────────────────────────────────────────────────┘
```

Format complet : voir `COMPRESSION_HARMONIQUE_V2_PISTES.md` §2bis.

### 4.3. Mode HCVH (HYBRID)

```
┌──────────────────────────────────────────────────────────────┐
│ Magic 'HCVH' (4 o)  │  modal_len (4 o)  │  n_corr (4 o)     │
├──────────────────────────────────────────────────────────────┤
│ Modal blob (modal_len o)                                     │
├──────────────────────────────────────────────────────────────┤
│ Correction 0 :  yi (2 o)  │  xi (2 o)  │  len (4 o)  │  ... │
│ Correction 1 :  ...                                         │
│ ...                                                          │
└──────────────────────────────────────────────────────────────┘
```

### 4.4. Mode HHDC (FULL)

```
┌──────────────────────────────────────────────────────────────┐
│ Magic 'HHDC' (4 o)  │  Version (1 o)  │  ps (2 o)  │  ...  │
└──────────────────────────────────────────────────────────────┘
```

## 5. Varint (entier variable)

Le varint est un encodage uint32 en 1-5 octets, little-endian par groupe de 7 bits :

```
Octet 1 : [b7=1] [b6-b0 = bits 0-6]
Octet 2 : [b7=1] [b6-b0 = bits 7-13]
...
Dernier : [b7=0] [b6-b0 = bits 28-34]
```

## 6. float16 (IEEE 754 half-precision)

Le format float16 est encodé selon IEEE 754 :

| Bits | Signe | Exposant | Mantisse |
|---|---|---|---|
| 16 | 1 (b15) | 5 (b14-b10) | 10 (b9-b0) |

Conversion float16 ↔ float32 : voir `hcv2_decoder.c` fonction `half_to_float()`.

## 7. Rétrocompatibilité

| Version | Compatibilité |
|---|---|
| 0x00 (pre-v1) | Header sans version : `precision_flag` en byte 8. Décodeur v1 lit byte 8 comme version (0x00 ou 0x01) → si 0x00, precision = byte 8 (qui est 0 ou 64 pour les anciens blobs). |
| 0x01 (v1) | Header standard : byte 8 = 0x01, byte 9 = precision. |

## 8. Tests de robustesse

Un fichier .hcv2 valide DOIT satisfaire :

1. Header : 12 premiers octets lisibles, `height` > 0, `width` > 0, `version` ∈ {0x00, 0x01}
2. Magic : 4 octets suivants ∈ {`HCVM`, `HCVH`, `HHD2`, `HHDC`}
3. Zlib : décompressible (intégrité CRC32)
4. Dimensions : hauteur et largeur ≤ 65535
5. Pixels : RGB, 3 canaux, 8 bits par canal
6. Checksum : SHA-256 du payload (optionnel, recommandé pour l'archivage)

## 9. Extension .hcv2

- Extension recommandée : `.hcv2`
- MIME type : `application/x-hcv2`
- Magic bytes : `HCVM` / `HCVH` / `HHD2` / `HHDC` (offset 12)

## 10. Licence

Le format .hcv2 est ouvert. La spécification est publique.
Le décodeur WASM (81 Ko) est libre.
L'encodeur professionnel fait partie de la suite HCV2 Pro (licence commerciale).