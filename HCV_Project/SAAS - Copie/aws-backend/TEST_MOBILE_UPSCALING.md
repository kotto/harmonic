# Plan de Test - Upscaling Mobile (Android Boost)

## 🎯 Objectif
Vérifier que l'upscaling 4K/8K fonctionne correctement pour les images mobiles (Android Boost).

## 📋 Prérequis

1. Serveur HCV PRO lancé:
   ```bash
   cd HCV-PRO-PROJECT
   python server/hcv_pro_server.py
   ```

2. Navigateur ouvert sur: `http://localhost:3000`

## ✅ Tests à Effectuer

### Test 1: Upscaling Original (Défaut)
**Objectif**: Vérifier que la résolution originale est préservée par défaut

1. Aller dans la section "📱 Android Boost"
2. Vérifier que le sélecteur "Résolution de sortie" est sur "Original"
3. Cliquer sur "Demo VGA" (640x480)
4. Attendre les résultats
5. **Vérifier**:
   - ✅ "Résolution orig." = 640x480
   - ✅ "Downscaled" = résolution réduite (ex: 480x360)
   - ✅ "Sortie (Upscale)" = 640x480 (même que original)
   - ✅ Images avant/après affichées correctement

### Test 2: Upscaling 4K depuis VGA
**Objectif**: Vérifier l'upscaling vers 4K

1. Rester dans "📱 Android Boost"
2. Sélectionner "4K (3840x2160)" dans "Résolution de sortie"
3. Cliquer sur "Demo VGA" (640x480)
4. Attendre les résultats
5. **Vérifier**:
   - ✅ "Résolution orig." = 640x480
   - ✅ "Downscaled" = résolution réduite
   - ✅ "Sortie (Upscale)" = 3840x2160 (4K)
   - ✅ Ratio de compression maintenu
   - ✅ Images affichées (l'image "après" devrait être upscalée)

### Test 3: Upscaling 8K depuis 1MP
**Objectif**: Vérifier l'upscaling vers 8K

1. Rester dans "📱 Android Boost"
2. Sélectionner "8K (7680x4320)" dans "Résolution de sortie"
3. Cliquer sur "Demo 1MP" (1200x800)
4. Attendre les résultats (peut prendre 20-30s pour 8K)
5. **Vérifier**:
   - ✅ "Résolution orig." = 1200x800
   - ✅ "Downscaled" = résolution réduite
   - ✅ "Sortie (Upscale)" = 7680x4320 (8K)
   - ✅ Temps de décompression plus long (normal pour 8K)
   - ✅ Images affichées

### Test 4: Upload Photo Réelle avec 4K
**Objectif**: Tester avec une vraie photo JPEG

1. Préparer une photo JPEG (n'importe quelle résolution)
2. Sélectionner "4K (3840x2160)" dans "Résolution de sortie"
3. Uploader la photo via la zone de drop
4. Attendre les résultats
5. **Vérifier**:
   - ✅ "Résolution orig." = résolution de la photo uploadée
   - ✅ "Downscaled" = résolution réduite selon qualité
   - ✅ "Sortie (Upscale)" = 3840x2160 (4K)
   - ✅ Ratio de compression affiché (ex: 4:1)
   - ✅ PSNR et SSIM affichés
   - ✅ Images avant/après visibles

### Test 5: Changement de Résolution entre Tests
**Objectif**: Vérifier que le changement de résolution fonctionne

1. Sélectionner "Original" → Cliquer "Demo VGA" → Noter la résolution de sortie
2. Sélectionner "4K" → Cliquer "Demo VGA" → Noter la résolution de sortie
3. Sélectionner "8K" → Cliquer "Demo VGA" → Noter la résolution de sortie
4. **Vérifier**:
   - ✅ Chaque test affiche la bonne résolution de sortie
   - ✅ Le ratio de compression reste le même (taille .hcab identique)
   - ✅ Seul le temps de décompression change

### Test 6: Qualité + Upscaling
**Objectif**: Vérifier que qualité et upscaling fonctionnent ensemble

1. Sélectionner "Ultra" (qualité) + "4K" (résolution)
2. Cliquer "Demo 1MP"
3. Noter les résultats
4. Sélectionner "Compact" (qualité) + "4K" (résolution)
5. Cliquer "Demo 1MP"
6. **Vérifier**:
   - ✅ "Ultra" donne un meilleur PSNR/SSIM que "Compact"
   - ✅ Les deux produisent une sortie 4K
   - ✅ "Ultra" a un fichier .hcab plus gros que "Compact"

## 🐛 Problèmes Potentiels

### Problème 1: Résolution de sortie ne change pas
**Symptôme**: La résolution de sortie reste toujours "Original"

**Cause possible**: Le paramètre `target_resolution` n'est pas envoyé au serveur

**Solution**:
1. Ouvrir la console du navigateur (F12)
2. Aller dans l'onglet "Network"
3. Faire un test avec "4K" sélectionné
4. Cliquer sur la requête `/api/android-boost`
5. Vérifier que `target_resolution=4K` est dans les paramètres

### Problème 2: Erreur 500 lors de l'upscaling
**Symptôme**: Erreur serveur lors de la décompression

**Cause possible**: Problème dans le codec ou manque de mémoire

**Solution**:
1. Vérifier les logs du serveur dans le terminal
2. Chercher le traceback Python
3. Vérifier que OpenCV et numpy sont installés
4. Essayer avec une résolution plus petite (Original au lieu de 8K)

### Problème 3: Images ne s'affichent pas
**Symptôme**: Les images avant/après sont vides

**Cause possible**: Problème d'encodage base64 ou format d'image

**Solution**:
1. Ouvrir la console du navigateur
2. Chercher des erreurs JavaScript
3. Vérifier que `d.img_before` et `d.img_after` existent dans la réponse
4. Vérifier que `d.img_format` est 'jpeg'

### Problème 4: Temps de décompression très long
**Symptôme**: L'upscaling 8K prend plus de 1 minute

**Cause**: Normal pour 8K (33 mégapixels)

**Solution**:
- C'est normal! L'upscaling 8K nécessite beaucoup de calculs
- Utiliser "4K" pour un bon compromis qualité/vitesse
- Utiliser "Original" pour la vitesse maximale

## 📊 Résultats Attendus

### Temps de Décompression Typiques

| Résolution Source | Résolution Sortie | Temps Décompression |
|-------------------|-------------------|---------------------|
| VGA (640x480) | Original (640x480) | ~0.5s |
| VGA (640x480) | 4K (3840x2160) | ~3-5s |
| VGA (640x480) | 8K (7680x4320) | ~15-20s |
| 1MP (1200x800) | Original (1200x800) | ~1s |
| 1MP (1200x800) | 4K (3840x2160) | ~5-8s |
| 1MP (1200x800) | 8K (7680x4320) | ~20-30s |

### Qualité Visuelle Attendue

| Résolution Sortie | PSNR | SSIM | Qualité Visuelle |
|-------------------|------|------|------------------|
| Original | >35 dB | >0.997 | Excellente |
| 4K (upscale) | >30 dB | >0.95 | Très bonne |
| 8K (upscale) | >28 dB | >0.93 | Bonne |

**Note**: Les métriques PSNR/SSIM sont calculées par rapport à l'image source, pas à l'image upscalée.

## ✅ Checklist Finale

Avant de considérer le test comme réussi, vérifier:

- [ ] Le sélecteur "Résolution de sortie" est visible dans l'interface
- [ ] Les 3 options (Original, 4K, 8K) sont disponibles
- [ ] Le texte d'aide "💡 L'upscale Lanczos..." est affiché
- [ ] La colonne "Sortie (Upscale)" apparaît dans les résultats
- [ ] La résolution de sortie change selon l'option sélectionnée
- [ ] Le ratio de compression reste le même (taille .hcab identique)
- [ ] Les images avant/après s'affichent correctement
- [ ] Pas d'erreur dans la console du navigateur
- [ ] Pas d'erreur dans les logs du serveur

## 🎉 Succès!

Si tous les tests passent, l'upscaling mobile est **100% fonctionnel**!

Vous pouvez maintenant:
- Compresser des photos Android en `.hcab`
- Décompresser à la résolution souhaitée (Original, 4K, 8K)
- Profiter d'un ratio de compression 3-10:1
- Obtenir une qualité visuelle excellente avec Lanczos + sharpening

## 📝 Notes

- L'upscaling ne crée pas de détails magiques, il interpole intelligemment
- Lanczos4 est le meilleur algorithme d'interpolation disponible
- Le sharpening adaptatif compense la légère perte de netteté
- Pour une qualité encore meilleure, envisager Real-ESRGAN (IA) dans le futur
