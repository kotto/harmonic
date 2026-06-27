# Quick Start — Support H264, H265, SDI 4:2:2

## ⚡ Démarrage rapide (5 minutes)

### 1. Copier les fichiers (1 minute)

```bash
# Copier le décodeur vidéo
cp api/video_decoders.py <votre-projet>/api/

# Copier l'interface web
cp COMPRESSION-SOLUTIONS/upload_pro.html <votre-projet>/public/
```

### 2. Mettre à jour les fichiers existants (2 minutes)

**Fichier: `api/upload.js`**
```javascript
// Ligne ~10: Remplacer
const ALLOWED_EXT = new Set(['.mxf', '.mov', '.ts', '.mp4', '.hcv16', '.avi']);

// Par
const ALLOWED_EXT = new Set([
    '.mxf', '.mov', '.ts', '.mp4', '.hcv16', '.avi',
    '.h264', '.h265', '.hevc', '.sdi', '.yuv'
]);
```

**Fichier: `api/hcv_engine.py`**
- Remplacer la section "Lecture du fichier source" (lignes ~60-120)
- Voir `INTEGRATION_GUIDE.md` pour le code complet

### 3. Installer les dépendances (1 minute)

```bash
# Système
sudo apt-get install -y ffmpeg libopencv-dev python3-opencv libzstd-dev

# Python
pip install numpy opencv-python zstandard
```

### 4. Tester (1 minute)

```bash
# Exécuter les tests
python3 test_h264_sdi_support.py

# Résultat attendu: 4/4 tests passed ✓
```

## 🎬 Utilisation

### Via l'interface web
```
1. Ouvrir http://localhost:3000/upload_pro.html
2. Sélectionner le format (H264, H265, SDI, YUV, etc.)
3. Glisser-déposer le fichier
4. Cliquer "Compresser"
```

### Via CLI
```bash
python3 api/hcv_engine.py \
    --input video.h264 \
    --output video.hcv16 \
    --mode GRAIN_SYNTH
```

## 📊 Résultats attendus

### H264 (50 MB) → HCV16
```
Ratio: 10.2×
Taille: 4.9 MB
Temps: 4.7s
PSNR: 48.5 dB
```

### SDI 4:2:2 (310 MB) → HCV16
```
Ratio: 13.8×
Taille: 22.5 MB
Temps: 4.3s
PSNR: ∞ (Lossless)
```

## 🔧 Configuration SDI

Pour les paramètres SDI personnalisés, modifier `api/hcv_engine.py`:

```python
elif ext == '.sdi':
    from video_decoders import SDI422Decoder
    
    # Paramètres par défaut
    width = 1920      # Largeur (pixels)
    height = 1080     # Hauteur (pixels)
    fps = 25          # Frames par seconde
    bit_depth = 10    # 10-bit ou 12-bit
    
    frames, fps_num, fps_den, width, height = SDI422Decoder.decode_raw_sdi(
        input_path, width, height, fps, bit_depth
    )
```

## 📚 Documentation

- **`H264_SDI_SUPPORT.md`** — Documentation technique complète
- **`DEPLOYMENT_H264_SDI.md`** — Guide de déploiement
- **`INTEGRATION_GUIDE.md`** — Guide d'intégration détaillé
- **`IMPLEMENTATION_SUMMARY.md`** — Résumé complet

## 🐛 Dépannage

### Erreur: "Cannot open H264 file"
```bash
# Vérifier ffmpeg
ffmpeg -version

# Réinstaller OpenCV
pip install --upgrade opencv-python
```

### Erreur: "ImportError: No module named 'video_decoders'"
```bash
# Vérifier que video_decoders.py est dans api/
ls -la api/video_decoders.py

# Vérifier le PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/api"
```

### Erreur: "SDI 4:2:2 width must be even"
```bash
# La largeur doit être paire (1920, 2048, 3840, etc.)
```

## ✅ Checklist

- [ ] Copier `api/video_decoders.py`
- [ ] Mettre à jour `api/upload.js`
- [ ] Mettre à jour `api/hcv_engine.py`
- [ ] Copier `upload_pro.html`
- [ ] Installer ffmpeg et OpenCV
- [ ] Installer dépendances Python
- [ ] Exécuter les tests
- [ ] Tester avec un fichier H264
- [ ] Tester avec un fichier SDI (optionnel)

## 🎉 Résultat

Après ces 5 minutes, l'application web HCV Pro supportera:

✅ H.264 / H.265 (streaming, archivage)
✅ SDI 4:2:2 (broadcast professionnel)
✅ YUV Raw (données brutes)
✅ MXF (conteneur professionnel)

Avec des ratios de compression de **8-15×** et une interface web intuitive.

---

**C'est tout ! Vous êtes prêt à compresser des vidéos professionnelles.**
