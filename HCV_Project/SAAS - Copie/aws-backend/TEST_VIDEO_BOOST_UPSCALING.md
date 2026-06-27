# 🧪 Test Video Boost 4K/8K Upscaling

## ✅ Guide de Test Rapide

### Prérequis

1. **Serveur lancé**:
```bash
cd HCV-PRO-PROJECT
python server/hcv_pro_server.py
```

2. **Navigateur ouvert**: `http://localhost:3000`

3. **Vidéo de test**: Préparer une vidéo MP4 (VGA, HD, ou Full HD)

---

## 🎯 Scénarios de Test

### Test 1: Upscaling 4K depuis VGA ✅

**Objectif**: Vérifier que l'upscaling 4K fonctionne correctement

**Étapes**:
1. Aller dans "🎬 Vidéo Boost"
2. Sélectionner "4K (3840x2160)" dans "Résolution de sortie"
3. Uploader une vidéo VGA (640x480) ou HD (1280x720)
4. Attendre la compression + décompression
5. Vérifier les résultats

**Résultats attendus**:
- ✅ "Sortie (Upscale)" = 3840x2160 (ou 2160x3840 pour une vidéo 9:16)
- ✅ Le format d'origine est préservé (aspect ratio)
- ✅ Vidéo restaurée visible et nette
- ✅ Audio préservé (si présent dans la source)
- ✅ Temps de décompression raisonnable (<30s pour 10s de vidéo)

**Important**: L'upscaling **préserve le format d'origine**. Une vidéo au format 9:16 (téléphone) sera upscalée en conservant ce ratio (ex: 2160x3840 pour 4K), pas en forçant un format 16:9.

**Capture d'écran**:
```
┌─────────────────────────────────────────────────────────┐
│ Résultats Vidéo Boost                                   │
├─────────────────────────────────────────────────────────┤
│ ✅ Compression vidéo réussie!                           │
│                                                         │
│ Ratio vs Source: 3.2:1    Économie: 68.8%              │
│                                                         │
│ Source      Compressé    Sortie (Upscale)  Durée       │
│ 1280x720    640x360      3840x2160         10.5s       │
│                                                         │
│ 🔵 Vidéo originale        🟢 Vidéo restaurée           │
│ [Lecteur vidéo]           [Lecteur vidéo]              │
└─────────────────────────────────────────────────────────┘
```

---

### Test 2: Upscaling 8K depuis HD ✅

**Objectif**: Vérifier que l'upscaling 8K fonctionne (temps plus long)

**Étapes**:
1. Sélectionner "8K (7680x4320)" dans "Résolution de sortie"
2. Uploader une vidéo HD (1280x720)
3. Attendre la compression + décompression (peut prendre 1-2 minutes)
4. Vérifier les résultats

**Résultats attendus**:
- ✅ "Sortie (Upscale)" = 7680x4320 (ou 4320x7680 pour une vidéo 9:16)
- ✅ Le format d'origine est préservé (aspect ratio)
- ✅ Vidéo restaurée visible et très nette
- ✅ Audio préservé
- ⚠️ Temps de décompression plus long (60-120s pour 10s de vidéo)

**Important**: L'upscaling **préserve le format d'origine**. Une vidéo au format 9:16 (téléphone) sera upscalée en conservant ce ratio (ex: 4320x7680 pour 8K), pas en forçant un format 16:9.

**Note**: L'upscaling 8K est **très gourmand en ressources**. Prévoir du temps.

---

### Test 3: Changement de Résolution ✅

**Objectif**: Vérifier que le changement de résolution fonctionne

**Étapes**:
1. Uploader une vidéo HD (1280x720)
2. Tester avec "Original" → Vérifier sortie = 1280x720
3. Tester avec "1080p" → Vérifier sortie = 1920x1080
4. Tester avec "4K" → Vérifier sortie = 3840x2160
5. Tester avec "8K" → Vérifier sortie = 7680x4320

**Résultats attendus**:
- ✅ Chaque option produit la bonne résolution
- ✅ Le format d'origine est préservé (aspect ratio)
- ✅ La taille du .hcvb reste identique (même fichier compressé)
- ✅ La qualité visuelle est cohérente

**Important**: L'upscaling **préserve le format d'origine**. Une vidéo au format 9:16 (téléphone) sera upscalée en conservant ce ratio, pas en forçant un format 16:9.

---

### Test 4: Qualité Visuelle ✅

**Objectif**: Vérifier que l'upscaling est net et de bonne qualité

**Étapes**:
1. Uploader une vidéo HD (1280x720) avec des détails (texte, visages, etc.)
2. Upscaler en 4K
3. Comparer visuellement Original vs 4K

**Résultats attendus**:
- ✅ L'upscaling est net (pas de flou excessif)
- ✅ Les détails sont préservés (texte lisible, visages reconnaissables)
- ✅ Pas d'artefacts visibles (blocs, banding, etc.)
- ✅ Le sharpening est subtil (pas de sur-sharpening)

**Critères de qualité**:
- **Excellent**: Détails nets, pas d'artefacts, sharpening subtil
- **Bon**: Détails corrects, artefacts mineurs, sharpening acceptable
- **Acceptable**: Détails flous, artefacts visibles, sharpening excessif
- **Mauvais**: Détails perdus, artefacts majeurs, sharpening horrible

---

### Test 5: Audio Preservation ✅

**Objectif**: Vérifier que l'audio est préservé sans perte

**Étapes**:
1. Uploader une vidéo avec audio (MP4 avec AAC ou MP3)
2. Upscaler en 4K
3. Vérifier l'audio dans la vidéo restaurée

**Résultats attendus**:
- ✅ Audio présent dans la vidéo restaurée
- ✅ "Audio méthode" = "✅ Stream copy" (0 perte)
- ✅ "Audio codec" = codec source (AAC, MP3, etc.)
- ✅ Qualité audio identique à la source
- ✅ Synchronisation audio/vidéo correcte

**Cas particuliers**:
- Si codec source incompatible (ex: PCM) → "Audio méthode" = "⚡ Transcode"
- Si pas d'audio → "Audio méthode" = "—"

---

### Test 6: Performance ⚡

**Objectif**: Mesurer les temps de décompression

**Étapes**:
1. Uploader une vidéo de 10 secondes
2. Tester chaque résolution et noter le temps

**Résultats attendus**:

| Source | Sortie | Temps Attendu | Temps Réel | Statut |
|--------|--------|---------------|------------|--------|
| VGA (640x480) | Original | ~2-3s | ___s | ⏳ |
| VGA (640x480) | 1080p | ~5-8s | ___s | ⏳ |
| VGA (640x480) | 4K | ~15-25s | ___s | ⏳ |
| VGA (640x480) | 8K | ~60-90s | ___s | ⏳ |
| HD (1280x720) | 4K | ~20-30s | ___s | ⏳ |
| HD (1280x720) | 8K | ~90-120s | ___s | ⏳ |

**Note**: Les temps dépendent du CPU, de la durée de la vidéo, et de la complexité du contenu.

---

### Test 7: Formats Vidéo ✅

**Objectif**: Vérifier que différents formats sont supportés

**Étapes**:
1. Tester avec MP4 (H264)
2. Tester avec MOV (H264)
3. Tester avec MKV (H264)
4. Tester avec WebM (VP8/VP9)

**Résultats attendus**:
- ✅ Tous les formats sont acceptés
- ✅ Compression + décompression réussie
- ✅ Upscaling fonctionne pour tous les formats
- ✅ Audio préservé (si présent)

---

### Test 8: Qualité de Compression ✅

**Objectif**: Vérifier que les différents niveaux de qualité fonctionnent

**Étapes**:
1. Uploader une vidéo HD
2. Tester avec "Ultra" → Vérifier ratio ~2-3:1
3. Tester avec "High" → Vérifier ratio ~3-5:1
4. Tester avec "Balanced" → Vérifier ratio ~5-8:1
5. Tester avec "Compact" → Vérifier ratio ~8-12:1

**Résultats attendus**:
- ✅ Ratio augmente avec la compression
- ✅ Qualité visuelle diminue avec la compression
- ✅ Upscaling fonctionne pour tous les niveaux
- ✅ Audio préservé pour tous les niveaux

---

## 🐛 Problèmes Potentiels et Solutions

### Problème 1: Vidéo restaurée floue

**Symptômes**: La vidéo upscalée est floue, manque de netteté

**Causes possibles**:
- Sharpening insuffisant
- Source de mauvaise qualité
- Upscaling trop agressif (VGA → 8K)

**Solutions**:
1. Vérifier que le filtre `unsharp` est appliqué dans le codec
2. Tester avec une source de meilleure qualité
3. Utiliser un upscaling moins agressif (VGA → 4K au lieu de 8K)

---

### Problème 2: Audio absent ou désynchronisé

**Symptômes**: Pas d'audio dans la vidéo restaurée, ou audio décalé

**Causes possibles**:
- Codec audio incompatible
- Erreur lors du stream copy
- Problème de muxing

**Solutions**:
1. Vérifier que "Audio méthode" = "✅ Stream copy" ou "⚡ Transcode"
2. Vérifier les logs du serveur pour les erreurs ffmpeg
3. Tester avec une vidéo ayant un codec audio standard (AAC)

---

### Problème 3: Temps de décompression trop long

**Symptômes**: L'upscaling 4K/8K prend plusieurs minutes

**Causes possibles**:
- CPU lent
- Vidéo longue ou complexe
- Preset ffmpeg trop lent

**Solutions**:
1. Utiliser un preset plus rapide (`fast` → `ultrafast`)
2. Réduire la résolution cible (8K → 4K)
3. Utiliser l'accélération GPU (NVENC/VAAPI) si disponible

---

### Problème 4: Erreur "target_resolution not found"

**Symptômes**: Erreur lors de l'affichage des résultats

**Causes possibles**:
- Le codec ne retourne pas `target_resolution` dans les stats
- Le serveur ne passe pas le paramètre au codec

**Solutions**:
1. Vérifier que le codec retourne `target_resolution` dans `decode_stats`
2. Vérifier que le serveur passe `target_resolution` au codec
3. Vérifier que le JavaScript affiche `d.target_resolution || d.restored_resolution`

---

## ✅ Checklist de Validation

### Fonctionnalités de Base
- [ ] Sélecteur de résolution visible ⏳
- [ ] Options: Original, 1080p, 4K, 8K ⏳
- [ ] Upload vidéo fonctionne ⏳
- [ ] Compression réussie ⏳
- [ ] Décompression réussie ⏳

### Upscaling
- [ ] Original → Résolution source ⏳
- [ ] 1080p → 1920x1080 ⏳
- [ ] 4K → 3840x2160 ⏳
- [ ] 8K → 7680x4320 ⏳
- [ ] Affichage résolution de sortie ⏳

### Qualité
- [ ] Vidéo restaurée nette ⏳
- [ ] Pas d'artefacts majeurs ⏳
- [ ] Sharpening subtil ⏳
- [ ] Détails préservés ⏳

### Audio
- [ ] Audio présent (si source) ⏳
- [ ] Audio synchronisé ⏳
- [ ] Qualité audio préservée ⏳
- [ ] Stream copy fonctionne ⏳

### Performance
- [ ] Original: <5s pour 10s ⏳
- [ ] 1080p: <10s pour 10s ⏳
- [ ] 4K: <30s pour 10s ⏳
- [ ] 8K: <120s pour 10s ⏳

### Formats
- [ ] MP4 supporté ⏳
- [ ] MOV supporté ⏳
- [ ] MKV supporté ⏳
- [ ] WebM supporté ⏳

---

## 📊 Rapport de Test

### Informations Système
- **OS**: _______________
- **CPU**: _______________
- **RAM**: _______________
- **GPU**: _______________
- **Python**: _______________
- **ffmpeg**: _______________

### Résultats Globaux
- **Tests réussis**: ___/8
- **Tests échoués**: ___/8
- **Problèmes rencontrés**: _______________
- **Temps total de test**: _______________

### Recommandations
- [ ] Prêt pour production ⏳
- [ ] Nécessite optimisations ⏳
- [ ] Nécessite corrections ⏳

---

## 🎉 Conclusion

Si tous les tests passent, l'upscaling 4K/8K pour Video Boost est **prêt pour production**!

**Bon test!** 🚀✨
