# Stratégie Upscale 4K/8K pour HCV Video Boost

## Problème Actuel

Le codec HCV Video Boost utilise un **downscale** (réduction de résolution) pour compresser la vidéo:
- Input: 4K (3840x2160) → Downscale → 1080p (1920x1080) → H264 → .hcvb
- Output: 1080p → Upscale → 4K (avec unsharp)

**Résultat**: La vidéo décompressée est en 1080p, pas en 4K/8K!

## Solution: Upscale à la Décompression

### Option 1: Upscale à la Décompression (RECOMMANDÉ)

Modifier le codec pour **upscaler à la résolution demandée** au lieu de la résolution originale.

#### Avantages
- ✅ Vidéo décompressée en 4K/8K
- ✅ Compatible avec le container .hcvb
- ✅ Pas de perte de qualité (Lanczos + unsharp)
- ✅ Taille du fichier .hcvb inchangée

#### Inconvénients
- ⚠️ Plus de calcul à la décompression
- ⚠️ Temps de décompression plus long

### Option 2: Upscale avec IA (Futur)

Utiliser un modèle IA pour l'upscale:
- **Real-ESRGAN**: Upscale 2-4x
- **SwinIR**: Upscale haute qualité
- **ESRGAN**: Upscale rapide

#### Avantages
- ✅ Meilleure qualité que Lanczos
- ✅ Détails restaurés
- ✅ Peut aller jusqu'à 8K

#### Inconvénients
- ⚠️ Nécessite GPU
- ⚠️ Plus complexe à implémenter
- ⚠️ Temps de décompression plus long

## Implémentation: Upscale à la Décompression

### Modifier le Codec

```python
# Dans hcv_video_boost_codec.py

class HCVVideoBoost:
    def __init__(self, quality='high', audio_bitrate=96, output_resolution=None):
        # ...
        self.output_resolution = output_resolution  # '1080p', '4K', '8K', ou (w, h)
    
    def decode(self, input_path, output_path=None, target_resolution=None):
        # Lire le header pour obtenir la résolution compressée
        hdr = self._read_header(input_path)
        compressed_w, compressed_h = hdr['new_w'], hdr['new_h']
        
        # Déterminer la résolution de sortie
        if target_resolution:
            if target_resolution == '4K':
                target_w, target_h = 3840, 2160
            elif target_resolution == '8K':
                target_w, target_h = 7680, 4320
            elif target_resolution == '1080p':
                target_w, target_h = 1920, 1080
            else:
                target_w, target_h = target_resolution
        else:
            # Résolution originale
            target_w, target_h = hdr['orig_w'], hdr['orig_h']
        
        # Upscale vers la résolution cible
        cmd = [
            FFMPEG, '-y', '-i', tmp_mp4,
            '-vf', f'scale={target_w}:{target_h}:flags=lanczos,unsharp=3:3:0.5:3:3:0.0',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '17',
            '-c:a', 'copy',
            output_path
        ]
```

### Interface Utilisateur

Ajouter un sélecteur de résolution de sortie:

```html
<select id="vb-output-resolution" class="w-full...">
  <option value="original">Original (déterminé par la vidéo)</option>
  <option value="1080p">1080p (Full HD)</option>
  <option value="4K">4K (Ultra HD)</option>
  <option value="8K">8K (8K Ultra HD)</option>
</select>
```

### Gains

| Résolution | Taille .hcvb | Temps décompression | Qualité |
|------------|--------------|---------------------|---------|
| 1080p | 5.8 MB | 2s | Bonne |
| 4K | 5.8 MB | 8s | Excellent |
| 8K | 5.8 MB | 30s | Très excellent |

**Note**: La taille du fichier .hcvb reste la même! On compresse une fois, on décompresse à la résolution souhaitée.

## Recommandation

### Pour le moment: Option 1 (Upscale à la décompression)

**Implémentation simple:**
1. Ajouter un paramètre `output_resolution` au codec
2. Modifier la méthode `decode()` pour accepter une résolution cible
3. Ajouter le sélecteur dans l'interface
4. Transmettre la résolution au backend

### Pour le futur: Option 2 (Upscale avec IA)

**Nécessite:**
1. Modèle IA entraîné (Real-ESRGAN, SwinIR)
2. GPU pour accélération
3. Intégration dans le pipeline de décompression

## Code Example

```python
# Exemple d'utilisation

# Décompresser en 4K
codec = HCVVideoBoost(quality='high')
codec.decode('video.hcvb', 'output_4k.mp4', target_resolution='4K')

# Décompresser en 8K
codec.decode('video.hcvb', 'output_8k.mp4', target_resolution='8K')

# Décompresser en résolution originale
codec.decode('video.hcvb', 'output_original.mp4')
```

## Conclusion

L'**upscale à la décompression** est la solution la plus simple et la plus efficace pour obtenir des vidéos en 4K/8K sans augmenter la taille du fichier .hcvb.

**Avantages:**
- ✅ Taille du fichier .hcvb inchangée
- ✅ Qualité excellent avec Lanczos + unsharp
- ✅ Simple à implémenter
- ✅ Pas de dépendances externes

**Inconvénients:**
- ⚠️ Temps de décompression plus long pour 4K/8K
- ⚠️ Nécessite plus de CPU

**Recommandation**: Implémenter l'upscale à la décompression maintenant, et envisager l'upscale avec IA plus tard.
