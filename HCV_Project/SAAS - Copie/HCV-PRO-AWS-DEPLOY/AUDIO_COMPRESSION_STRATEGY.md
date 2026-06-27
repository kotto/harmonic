# Stratégie de Compression Audio pour HCV Video Boost

## Problème Actuel
- Audio actuellement: **AAC 192 kbps** ou stream copy (bitrate original)
- Pour une vidéo 1h: audio = ~86 MB (192 kbps)
- Objectif: réduire sans perte perceptible de qualité

## Options de Compression Audio

### Option 1: Opus (RECOMMANDÉ) ⭐
**Codec**: Opus (RFC 6716)
- **Bitrate**: 64 kbps (stéréo) = 28.8 MB/h
- **Qualité**: Transparente pour la parole, très bonne pour la musique
- **Avantages**:
  - Meilleure compression que AAC à même bitrate
  - Optimisé pour la parole ET la musique
  - Royalty-free, open-source
  - Support navigateur: Chrome, Firefox, Edge (pas Safari)
- **Inconvénients**: Pas compatible MP4 natif (nécessite Matroska/WebM)
- **Réduction**: 64 vs 192 kbps = **66% de réduction**

### Option 2: AAC-LC Optimisé
**Codec**: AAC-LC (Advanced Audio Coding)
- **Bitrate**: 96 kbps (stéréo) = 43.2 MB/h
- **Qualité**: Très bonne, standard industrie
- **Avantages**:
  - Compatible MP4 natif
  - Support universel (tous navigateurs)
  - Décodage matériel sur mobiles
- **Inconvénients**: Moins efficace que Opus
- **Réduction**: 96 vs 192 kbps = **50% de réduction**

### Option 3: Opus dans Matroska (.mkv)
**Codec**: Opus + Matroska container
- **Bitrate**: 64 kbps
- **Qualité**: Transparente
- **Avantages**:
  - Meilleure compression (Opus)
  - Support métadonnées riche
  - Flexible pour futurs codecs
- **Inconvénients**: Pas de support natif navigateur (nécessite transcode)
- **Réduction**: 64 vs 192 kbps = **66% de réduction**

### Option 4: Hybrid Strategy (MEILLEUR COMPROMIS)
**Stratégie**: Détection intelligente du contenu audio
```
Si audio = parole (podcast, conférence):
  → Opus 48 kbps (très efficace pour parole)
  → Réduction: 75%

Si audio = musique:
  → Opus 96 kbps (qualité CD)
  → Réduction: 50%

Si audio = silence/bruit:
  → Opus 32 kbps
  → Réduction: 83%
```

## Implémentation Recommandée

### Approche 1: AAC-LC 96 kbps (Rapide, Compatible)
**Pros**: Facile à implémenter, compatible MP4, support universel
**Cons**: Moins efficace que Opus
**Réduction**: 50%

```python
# Dans encode():
'-c:a', 'aac',
'-b:a', '96k',  # au lieu de 192k
'-ar', '48000'
```

### Approche 2: Opus + Remux MP4 (Optimal)
**Pros**: Meilleure compression, qualité transparente
**Cons**: Nécessite remux MP4 après
**Réduction**: 66%

```python
# Étape 1: Encoder vidéo + audio Opus
cmd_encode = [
    FFMPEG, '-y', '-i', input_path,
    '-vf', f'scale={new_w}:{new_h}:flags=lanczos',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf),
    '-c:a', 'libopus', '-b:a', '64k',
    '-f', 'matroska',  # Opus nécessite Matroska
    tmp_mkv
]

# Étape 2: Remux en MP4 (audio Opus → MP4 via AAC transcode)
# OU garder en Matroska et décoder en MP4 à la lecture
```

### Approche 3: Détection Audio Intelligente
```python
def detect_audio_type(audio_info):
    """Détecte si audio = parole, musique, silence"""
    # Analyse spectrale simple
    if audio_info['sample_rate'] <= 16000:
        return 'speech'  # Parole
    if audio_info['channels'] == 1:
        return 'mono'    # Mono = souvent parole
    return 'music'       # Stéréo = musique

def get_audio_bitrate(audio_type):
    """Retourne bitrate optimal selon type"""
    return {
        'speech': 48,    # Parole: 48 kbps Opus
        'mono': 64,      # Mono: 64 kbps
        'music': 96,     # Musique: 96 kbps Opus
    }.get(audio_type, 96)
```

## Recommandation Finale

**Implémenter Option 2: AAC-LC 96 kbps**

Raisons:
1. ✅ Facile à implémenter (1 ligne de code)
2. ✅ Compatible MP4 natif (pas de remux)
3. ✅ Support universel (tous navigateurs)
4. ✅ Réduction 50% (86 MB → 43 MB/h)
5. ✅ Qualité imperceptible (96 kbps AAC ≈ 128 kbps MP3)

**Gains Globaux** (exemple vidéo 1h):
- Vidéo H264 (CRF 23): ~500 MB
- Audio AAC 96k: ~43 MB
- **Total: ~543 MB** (vs 586 MB actuellement)
- **Réduction: 7% du fichier total**

## Implémentation dans le Code

Modifier `hcv_video_boost_codec.py`:

```python
# Dans _audio_args():
def _audio_args(has_audio: bool, copy_safe: bool, bitrate: int = 96) -> list:
    if not has_audio:
        return ['-an']
    if copy_safe:
        return ['-c:a', 'copy']
    return ['-c:a', 'aac', '-b:a', f'{bitrate}k', '-ar', '48000']

# Dans encode():
audio_flags = _audio_args(info['has_audio'], info['audio_copy_safe'], bitrate=96)
```

## Prochaines Étapes (Optionnel)

1. **Phase 2**: Ajouter Opus support (Matroska container)
2. **Phase 3**: Détection audio intelligente
3. **Phase 4**: Compression audio lossless (FLAC) pour archivage
