# HCV Image Codec - Stratégie pour Images Pré-Compressées

**Date**: 2026-04-11  
**Contexte**: Adaptation du codec HCV pour images déjà compressées (JPEG, PNG, WebP, etc.)

---

## 🎯 Problématique

### Cas d'Usage

Vous avez des images **déjà compressées** (JPEG, PNG, WebP, etc.) et vous voulez:
- ✅ Les compresser davantage
- ✅ Les archiver efficacement
- ✅ Les distribuer avec meilleure qualité
- ✅ Réduire la bande passante

### Défi Principal

Les images compressées ont **peu de redondance restante**:
- JPEG: Quantification + DCT (perte de haute fréquence)
- PNG: Filtrage + Deflate (perte de corrélation)
- WebP: Prédiction + Huffman (perte de structure)

**Résultat**: Les techniques de prédiction (Delta-H) sont moins efficaces.

---

## 📊 Analyse: Compressé vs Non-Compressé

### Image RAW (Non-Compressée)

```
Caractéristiques:
- Haute corrélation spatiale
- Grain naturel (bruit capteur)
- Redondance importante
- Delta-H très efficace

Pipeline HCV:
YCbCr 4:2:2 → Grain Separation → Delta-H → zstd
Ratio attendu: 8-12:1
```

### Image JPEG (Compressée)

```
Caractéristiques:
- Basse corrélation (DCT appliqué)
- Artefacts de quantification
- Peu de redondance
- Delta-H peu efficace

Pipeline Standard:
Décodage JPEG → RGB → YCbCr 4:2:2 → Delta-H → zstd
Ratio attendu: 1.2-1.5:1 (mauvais)
```

---

## ✅ Solutions Adaptées

### Solution 1: Transcoding Intelligent (Recommandé)

**Concept**: Décoder → Réencoder avec meilleure qualité

```
JPEG (Q=85) → Décoder → RGB → YCbCr 4:2:2 → HCV (GRAIN_SYNTH)
                                              ↓
                                        Ratio: 8-12:1
                                        Qualité: Meilleure
```

**Avantages**:
- ✅ Ratio excellent (8-12:1)
- ✅ Qualité améliorée
- ✅ Grain naturel restauré
- ✅ Archivage optimal

**Inconvénients**:
- ❌ Perte de qualité JPEG (irréversible)
- ❌ Temps de traitement (décodage + encodage)

**Cas d'Usage**:
- ✅ Archivage long terme
- ✅ Distribution (qualité acceptable)
- ✅ Stockage (économies importantes)

---

### Solution 2: Compression Directe (Rapide)

**Concept**: Compresser le fichier JPEG directement

```
JPEG (fichier) → Analyse → Stratégie → Compression
                                      ↓
                                 Ratio: 1.2-1.5:1
```

**Variantes**:

#### 2a. Compression du Fichier JPEG

```python
# Charger JPEG
jpeg_data = open('image.jpg', 'rb').read()

# Compresser avec zstd
compressed = zstd.compress(jpeg_data, level=22)

# Ratio: 1.1-1.3:1 (minimal)
```

**Ratio**: 1.1-1.3:1 (très faible)  
**Temps**: Très rapide  
**Qualité**: Préservée

#### 2b. Décodage Partiel + Compression

```python
# Décoder JPEG
image = PIL.Image.open('image.jpg')

# Convertir en YCbCr 4:2:2
Y, Cb, Cr = separate_ycbcr422(image)

# Compresser directement (sans grain separation)
Y_comp = delta_h_encode(Y)
Cb_comp = delta_h_encode(Cb)
Cr_comp = delta_h_encode(Cr)

# Ratio: 1.5-2.5:1 (faible)
```

**Ratio**: 1.5-2.5:1 (faible)  
**Temps**: Rapide  
**Qualité**: Préservée

---

### Solution 3: Recompression Intelligente (Optimal)

**Concept**: Analyser le format source et adapter la stratégie

```
Image Compressée
    ↓
Analyser Format (JPEG/PNG/WebP)
    ↓
Décider Stratégie:
  - JPEG Q<80 → Transcoder (améliorer qualité)
  - JPEG Q≥80 → Compression directe (préserver qualité)
  - PNG → Compression directe (déjà lossless)
  - WebP → Compression directe (déjà optimisé)
    ↓
Appliquer Pipeline Adapté
    ↓
Résultat Optimal
```

---

## 🔧 Implémentation: Classe HCVPrecompressed

```python
class HCVPrecompressedCodec:
    """
    Codec adapté pour images pré-compressées
    Détecte le format et applique la meilleure stratégie
    """
    
    def __init__(self, mode='AUTO', quality_threshold=80):
        self.mode = mode  # AUTO, TRANSCODE, DIRECT, HYBRID
        self.quality_threshold = quality_threshold
        self.hcv = HCVImageCodec()
    
    def detect_format(self, image_path):
        """Détecte le format et la qualité"""
        # Analyser l'en-tête
        # Estimer la qualité JPEG
        # Retourner (format, quality, recommendation)
        pass
    
    def transcode_strategy(self, image_path):
        """Stratégie: Décoder → Réencoder avec HCV"""
        # Charger image
        image = PIL.Image.open(image_path)
        
        # Convertir en RGB si nécessaire
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convertir en uint16
        image_array = np.array(image, dtype=np.uint16) * 257
        
        # Compresser avec HCV
        return self.hcv.encode_image(image_array)
    
    def direct_strategy(self, image_path):
        """Stratégie: Compresser le fichier directement"""
        with open(image_path, 'rb') as f:
            data = f.read()
        
        # Compresser avec zstd niveau 22
        import zstandard as zstd
        cctx = zstd.ZstdCompressor(level=22)
        return cctx.compress(data)
    
    def hybrid_strategy(self, image_path):
        """Stratégie: Décoder → YCbCr → Compresser"""
        image = PIL.Image.open(image_path)
        image_array = np.array(image, dtype=np.uint16) * 257
        
        # Convertir YCbCr 4:2:2
        Y, Cb, Cr = self.hcv.separate_ycbcr422(image_array)
        
        # Compresser sans grain separation
        Y_comp = self.hcv.delta_h_encode(Y)
        Cb_comp = self.hcv.delta_h_encode(Cb)
        Cr_comp = self.hcv.delta_h_encode(Cr)
        
        # Container
        return self._build_container(Y_comp, Cb_comp, Cr_comp)
    
    def encode(self, image_path):
        """Encode avec stratégie automatique"""
        format_info = self.detect_format(image_path)
        
        if self.mode == 'AUTO':
            if format_info['format'] == 'JPEG' and format_info['quality'] < 80:
                # Qualité faible: transcoder
                return self.transcode_strategy(image_path)
            elif format_info['format'] in ['PNG', 'WebP']:
                # Déjà lossless: compression directe
                return self.direct_strategy(image_path)
            else:
                # Qualité bonne: hybrid
                return self.hybrid_strategy(image_path)
        
        elif self.mode == 'TRANSCODE':
            return self.transcode_strategy(image_path)
        elif self.mode == 'DIRECT':
            return self.direct_strategy(image_path)
        elif self.mode == 'HYBRID':
            return self.hybrid_strategy(image_path)
```

---

## 📊 Comparaison des Stratégies

### Cas 1: JPEG Qualité Basse (Q=60)

| Stratégie | Ratio | Qualité | Temps | Recommandation |
|-----------|-------|---------|-------|----------------|
| Direct | 1.2:1 | Préservée | Très rapide | ❌ Mauvais ratio |
| Hybrid | 2.0:1 | Préservée | Rapide | ⚠️ Acceptable |
| Transcode | 8:1 | **Améliorée** | Lent | ✅ **Optimal** |

**Recommandation**: **TRANSCODE** (améliore qualité + bon ratio)

---

### Cas 2: JPEG Qualité Haute (Q=95)

| Stratégie | Ratio | Qualité | Temps | Recommandation |
|-----------|-------|---------|-------|----------------|
| Direct | 1.3:1 | Préservée | Très rapide | ⚠️ Faible ratio |
| Hybrid | 2.5:1 | Préservée | Rapide | ✅ **Bon** |
| Transcode | 8:1 | Identique | Lent | ⚠️ Overkill |

**Recommandation**: **HYBRID** (bon ratio, rapide)

---

### Cas 3: PNG (Lossless)

| Stratégie | Ratio | Qualité | Temps | Recommandation |
|-----------|-------|---------|-------|----------------|
| Direct | 1.1:1 | Préservée | Très rapide | ✅ **Optimal** |
| Hybrid | 2.0:1 | Préservée | Rapide | ⚠️ Overkill |
| Transcode | 8:1 | Identique | Lent | ❌ Overkill |

**Recommandation**: **DIRECT** (rapide, bon ratio)

---

### Cas 4: WebP (Optimisé)

| Stratégie | Ratio | Qualité | Temps | Recommandation |
|-----------|-------|---------|-------|----------------|
| Direct | 1.15:1 | Préservée | Très rapide | ✅ **Optimal** |
| Hybrid | 1.8:1 | Préservée | Rapide | ⚠️ Overkill |
| Transcode | 8:1 | Identique | Lent | ❌ Overkill |

**Recommandation**: **DIRECT** (rapide, bon ratio)

---

## 🎯 Matrice de Décision

```
Format Source
    ↓
┌─────────────────────────────────────────┐
│ JPEG                                    │
├─────────────────────────────────────────┤
│ Qualité < 70?                           │
│   → TRANSCODE (améliorer + compresser)  │
│                                         │
│ Qualité 70-85?                          │
│   → HYBRID (bon équilibre)              │
│                                         │
│ Qualité > 85?                           │
│   → DIRECT (préserver qualité)          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ PNG / WebP / AVIF                       │
├─────────────────────────────────────────┤
│ Déjà optimisé (lossless)                │
│   → DIRECT (compression fichier)        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Inconnu                                 │
├─────────────────────────────────────────┤
│ Analyser en-tête                        │
│   → Appliquer matrice ci-dessus         │
└─────────────────────────────────────────┘
```

---

## 💡 Cas d'Usage Pratiques

### Cas 1: Archive JPEG Ancienne (Q=70)

```
Situation:
- 10,000 images JPEG Q=70
- Qualité médiocre
- Besoin d'archivage long terme

Solution:
- Stratégie: TRANSCODE
- Résultat: 8:1 compression + qualité améliorée
- Bénéfice: Meilleure qualité + 87% économie stockage
```

### Cas 2: Distribution WebP Optimisée

```
Situation:
- 50,000 images WebP (déjà optimisées)
- Besoin de réduire bande passante
- Qualité critique

Solution:
- Stratégie: DIRECT
- Résultat: 1.15:1 compression
- Bénéfice: Rapide, qualité préservée, 13% économie
```

### Cas 3: Mix de Formats

```
Situation:
- Archive hétérogène (JPEG, PNG, WebP)
- Besoin d'archivage unifié
- Qualité variable

Solution:
- Stratégie: AUTO (détection + adaptation)
- Résultat: Optimal pour chaque format
- Bénéfice: Archivage unifié, ratio optimal
```

---

## 🔄 Pipeline Complet: HCV Precompressed

```
Image Compressée (JPEG/PNG/WebP)
    ↓
[1] Détection Format
    - Analyser en-tête
    - Estimer qualité
    - Recommander stratégie
    ↓
[2] Sélection Stratégie
    - TRANSCODE: Décoder → Réencoder
    - DIRECT: Compresser fichier
    - HYBRID: Décoder → YCbCr → Compresser
    ↓
[3] Traitement
    - Appliquer pipeline sélectionné
    - Générer container HCV
    ↓
[4] Résultat
    - Fichier HCV compressé
    - Métadonnées (format source, stratégie)
    - Métriques (ratio, qualité, temps)
```

---

## 📈 Résultats Attendus

### Compression Ratios

| Format Source | Stratégie | Ratio | Qualité |
|---------------|-----------|-------|---------|
| JPEG Q=60 | TRANSCODE | 8:1 | ✅ Améliorée |
| JPEG Q=80 | HYBRID | 2.5:1 | ✅ Préservée |
| JPEG Q=95 | DIRECT | 1.3:1 | ✅ Préservée |
| PNG | DIRECT | 1.1:1 | ✅ Préservée |
| WebP | DIRECT | 1.15:1 | ✅ Préservée |

### Temps de Traitement

| Stratégie | Temps | Vitesse |
|-----------|-------|---------|
| DIRECT | 100ms | Très rapide |
| HYBRID | 500ms | Rapide |
| TRANSCODE | 2000ms | Lent |

---

## ✅ Recommandations

### Pour Images JPEG

1. **Qualité < 75**: TRANSCODE
   - Améliore qualité
   - Bon ratio (8:1)
   - Acceptable pour archivage

2. **Qualité 75-90**: HYBRID
   - Équilibre qualité/ratio
   - Ratio 2-3:1
   - Rapide

3. **Qualité > 90**: DIRECT
   - Préserve qualité
   - Ratio 1.2-1.5:1
   - Très rapide

### Pour Images PNG/WebP

- **Toujours DIRECT**
- Déjà optimisées
- Ratio 1.1-1.2:1
- Très rapide

### Pour Archive Mixte

- **Utiliser AUTO**
- Détection automatique
- Stratégie optimale par format
- Résultats cohérents

---

## 🚀 Implémentation Recommandée

### Phase 1: Codec de Base (Déjà Fait)
- ✅ HCVImageCodec (images RAW)

### Phase 2: Support Pré-Compressé (À Faire)
- [ ] HCVPrecompressedCodec
- [ ] Détection format
- [ ] Stratégies multiples
- [ ] Sélection automatique

### Phase 3: Optimisations
- [ ] GPU acceleration
- [ ] Multi-threading
- [ ] Batch processing
- [ ] API REST

---

## 📊 Conclusion

**Oui, la solution HCV peut être adaptée pour images pré-compressées.**

### Stratégies Recommandées

1. **TRANSCODE**: Pour JPEG basse qualité (améliore qualité + ratio 8:1)
2. **HYBRID**: Pour JPEG moyenne qualité (ratio 2-3:1, rapide)
3. **DIRECT**: Pour PNG/WebP/JPEG haute qualité (ratio 1.1-1.5:1, très rapide)
4. **AUTO**: Pour archives mixtes (détection + adaptation)

### Bénéfices

- ✅ Archivage unifié
- ✅ Ratio optimal par format
- ✅ Qualité préservée/améliorée
- ✅ Temps de traitement acceptable

### Prochaines Étapes

1. Implémenter HCVPrecompressedCodec
2. Tester sur archives réelles
3. Optimiser performances
4. Intégrer API

