# Guide d'intégration — Support H264, H265, SDI 4:2:2

## 🎯 Objectif

Ajouter le support des formats vidéo professionnels (H264, H265, SDI 4:2:2, YUV) à l'application web HCV Pro existante.

## 📋 Étapes d'intégration

### Étape 1: Copier les fichiers

```bash
# Copier le décodeur vidéo
cp api/video_decoders.py <votre-projet>/api/

# Copier l'interface web
cp COMPRESSION-SOLUTIONS/upload_pro.html <votre-projet>/public/

# Copier la documentation
cp COMPRESSION-SOLUTIONS/H264_SDI_SUPPORT.md <votre-projet>/docs/
cp COMPRESSION-SOLUTIONS/DEPLOYMENT_H264_SDI.md <votre-projet>/docs/
cp COMPRESSION-SOLUTIONS/README_H264_SDI_IMPLEMENTATION.md <votre-projet>/docs/
```

### Étape 2: Mettre à jour `api/upload.js`

**Avant:**
```javascript
const ALLOWED_EXT = new Set(['.mxf', '.mov', '.ts', '.mp4', '.hcv16', '.avi']);
```

**Après:**
```javascript
const ALLOWED_EXT = new Set([
    '.mxf', '.mov', '.ts', '.mp4', '.hcv16', '.avi',
    '.h264', '.h265', '.hevc', '.sdi', '.yuv'
]);
```

### Étape 3: Mettre à jour `api/hcv_engine.py`

Remplacer la section "Lecture du fichier source" (lignes ~60-120) par:

```python
ext = os.path.splitext(input_path)[1].lower()

# ── Lecture du fichier source ──────────────────────────────────────────
frames = []
audio_samples = None
audio_sr      = None
width = height = 0

if ext == '.hcv16':
    # Re-encode depuis un .hcv16 existant
    try:
        rdr = HCV16Reader(input_path).open()
        frames = rdr.decode_all()
        audio_samples, audio_sr = rdr.decode_audio()
        height, width = frames[0].shape[:2]
        fps_num = rdr.fps_num
        fps_den = rdr.fps_den
    except Exception as e:
        _err(f"Lecture .hcv16 échouée : {e}")

elif ext in ('.h264', '.h265', '.hevc'):
    # H264/H265 via video_decoders
    try:
        from video_decoders import H264Decoder
        frames, fps_num, fps_den, width, height = H264Decoder.decode(input_path)
    except Exception as e:
        _err(f"Décodage H264/H265 échoué : {e}\n{traceback.format_exc()}")

elif ext == '.sdi':
    # SDI 4:2:2 raw format
    try:
        from video_decoders import SDI422Decoder
        width = 1920
        height = 1080
        fps = 25
        bit_depth = 10
        frames, fps_num, fps_den, width, height = SDI422Decoder.decode_raw_sdi(
            input_path, width, height, fps, bit_depth
        )
    except Exception as e:
        _err(f"Décodage SDI 4:2:2 échoué : {e}\n{traceback.format_exc()}")

elif ext == '.yuv':
    # YUV raw format (I420)
    try:
        from video_decoders import YUVDecoder
        width = 1920
        height = 1080
        fps = 25
        frames, fps_num, fps_den, width, height = YUVDecoder.decode_i420(
            input_path, width, height, fps
        )
    except Exception as e:
        _err(f"Décodage YUV échoué : {e}\n{traceback.format_exc()}")

elif ext in ('.mp4', '.mov', '.avi', '.ts', '.mxf'):
    # Lecture vidéo via OpenCV (code existant)
    try:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            _err(f"Impossible d'ouvrir la vidéo : {input_path}")

        fps_src = cap.get(cv2.CAP_PROP_FPS) or 25.0
        fps_num = round(fps_src * 1000)
        fps_den = 1000
        width   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            f16 = frame.astype(np.uint16) << 4
            frames.append(f16)
        cap.release()

        if not frames:
            _err("Aucune frame lue depuis la vidéo")

        # Audio via ffmpeg si disponible (optionnel)
        try:
            import subprocess, tempfile
            wav_tmp = input_path + '_audio.wav'
            r = subprocess.run(
                ['ffmpeg', '-y', '-i', input_path,
                 '-vn', '-acodec', 'pcm_s16le', '-ar', '48000', '-ac', '2',
                 wav_tmp],
                capture_output=True, timeout=60
            )
            if r.returncode == 0 and os.path.exists(wav_tmp):
                import wave
                with wave.open(wav_tmp, 'rb') as wf:
                    raw_audio = wf.readframes(wf.getnframes())
                    audio_samples = np.frombuffer(raw_audio, np.int16).reshape(-1, 2)
                    audio_sr = wf.getframerate()
                os.remove(wav_tmp)
        except Exception:
            pass  # Audio optionnel

    except Exception as e:
        _err(f"Lecture vidéo échouée : {e}")
else:
    _err(f"Format non supporté : {ext}. Formats acceptés : .h264, .h265, .hevc, .sdi, .yuv, .mp4, .mov, .avi, .ts, .mxf, .hcv16")
```

### Étape 4: Installer les dépendances

```bash
# Système
sudo apt-get install -y ffmpeg libopencv-dev python3-opencv libzstd-dev

# Python
pip install numpy opencv-python zstandard
```

### Étape 5: Tester l'intégration

```bash
# Exécuter les tests
python3 test_h264_sdi_support.py

# Tester manuellement
python3 api/hcv_engine.py \
    --input test.h264 \
    --output test.hcv16 \
    --mode GRAIN_SYNTH
```

### Étape 6: Déployer l'interface web

```bash
# Copier l'interface web dans le répertoire public
cp COMPRESSION-SOLUTIONS/upload_pro.html <votre-projet>/public/

# Accéder via: http://localhost:3000/upload_pro.html
```

## 🔄 Flux de travail complet

```
Utilisateur
    ↓
Interface web (upload_pro.html)
    ↓
POST /api/upload (multipart/form-data)
    ↓
Node.js (api/upload.js)
    ├─ Valide l'extension
    ├─ Sauvegarde le fichier temporaire
    └─ Lance: python3 api/hcv_engine.py
        ↓
    Python (api/hcv_engine.py)
    ├─ Détecte le format
    ├─ Importe le décodeur approprié
    │   ├─ H264Decoder
    │   ├─ SDI422Decoder
    │   ├─ YUVDecoder
    │   └─ OpenCV (MP4/MOV/AVI/TS/MXF)
    ├─ Décode les frames
    ├─ Encode en HCV16
    └─ Retourne JSON avec résultats
        ↓
    Node.js (api/upload.js)
    ├─ Parse la réponse JSON
    ├─ Sauvegarde le fichier .hcv16
    └─ Retourne les métadonnées
        ↓
    Interface web
    ├─ Affiche les résultats
    ├─ Permet le téléchargement
    └─ Affiche les métriques
```

## 📊 Exemple de réponse API

```json
{
  "ok": true,
  "mode": "GRAIN_SYNTH",
  "ratio": "10.25×",
  "psnr": "~46-55 dB",
  "fileSize": 204800000,
  "frames": 750,
  "width": 1920,
  "height": 1080,
  "fps": "25/1",
  "hasAudio": false,
  "sigmaInfo": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2],
  "headerBytes": 256
}
```

## 🔧 Configuration avancée

### Paramètres SDI personnalisés

Pour permettre à l'utilisateur de configurer les paramètres SDI via l'interface web:

**1. Modifier `upload_pro.html`:**
```html
<form id="uploadForm">
    <input type="hidden" id="sdiWidth" value="1920">
    <input type="hidden" id="sdiHeight" value="1080">
    <input type="hidden" id="sdiFps" value="25">
    <input type="hidden" id="sdiBits" value="10">
</form>
```

**2. Modifier `api/upload.js`:**
```javascript
bb.on('field', (name, val) => {
    if (name === 'mode' && ['fast', 'sdi', 'arch'].includes(val)) mode = val;
    if (name === 'sdi_width') sdi_width = parseInt(val);
    if (name === 'sdi_height') sdi_height = parseInt(val);
    if (name === 'sdi_fps') sdi_fps = parseFloat(val);
    if (name === 'sdi_bits') sdi_bits = parseInt(val);
});

// Passer les paramètres à hcv_engine.py
const args = [
    '--input', inputPath,
    '--output', outputPath,
    '--mode', modeMap[mode],
    '--sdi-width', sdi_width,
    '--sdi-height', sdi_height,
    '--sdi-fps', sdi_fps,
    '--sdi-bits', sdi_bits
];
```

**3. Modifier `api/hcv_engine.py`:**
```python
parser.add_argument('--sdi-width', type=int, default=1920)
parser.add_argument('--sdi-height', type=int, default=1080)
parser.add_argument('--sdi-fps', type=float, default=25)
parser.add_argument('--sdi-bits', type=int, default=10)

# Utiliser les paramètres
frames, fps_num, fps_den, width, height = SDI422Decoder.decode_raw_sdi(
    input_path, args.sdi_width, args.sdi_height, args.sdi_fps, args.sdi_bits
)
```

### Support de formats supplémentaires

Pour ajouter un nouveau format (ex: ProRes):

**1. Créer un décodeur dans `api/video_decoders.py`:**
```python
class ProResDecoder:
    @staticmethod
    def decode(input_path):
        # Implémentation
        pass
```

**2. Ajouter dans `api/hcv_engine.py`:**
```python
elif ext == '.prores':
    from video_decoders import ProResDecoder
    frames, fps_num, fps_den, width, height = ProResDecoder.decode(input_path)
```

**3. Ajouter l'extension dans `api/upload.js`:**
```javascript
const ALLOWED_EXT = new Set([..., '.prores']);
```

## 📈 Optimisations possibles

### 1. Traitement par chunks (pour fichiers volumineux)

```python
def frame_generator(input_path):
    """Générateur de frames pour économiser la mémoire"""
    cap = cv2.VideoCapture(input_path)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yield frame.astype(np.uint16) << 4
    cap.release()

# Utilisation
for frame in frame_generator(input_path):
    wtr.add_frame(frame, frame_idx)
```

### 2. Parallélisation du décodage

```python
from concurrent.futures import ThreadPoolExecutor

def decode_frames_parallel(input_path, num_workers=4):
    """Décode les frames en parallèle"""
    cap = cv2.VideoCapture(input_path)
    frames = []
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            future = executor.submit(
                lambda f: f.astype(np.uint16) << 4,
                frame
            )
            futures.append(future)
        
        frames = [f.result() for f in futures]
    
    cap.release()
    return frames
```

### 3. Caching des frames décodées

```python
import hashlib

def get_cached_frames(input_path):
    """Retourne les frames en cache ou les décode"""
    file_hash = hashlib.md5(open(input_path, 'rb').read()).hexdigest()
    cache_path = f'/tmp/hcv-cache-{file_hash}.pkl'
    
    if os.path.exists(cache_path):
        import pickle
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    
    # Décoder et mettre en cache
    frames = H264Decoder.decode(input_path)
    with open(cache_path, 'wb') as f:
        pickle.dump(frames, f)
    
    return frames
```

## 🐛 Dépannage

### Problème: "Cannot open H264 file"
```bash
# Vérifier ffmpeg
ffmpeg -version

# Vérifier OpenCV
python3 -c "import cv2; print(cv2.__version__)"

# Réinstaller
pip install --upgrade opencv-python
```

### Problème: "ImportError: No module named 'video_decoders'"
```bash
# Vérifier que video_decoders.py est dans api/
ls -la api/video_decoders.py

# Vérifier le PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/api"
```

### Problème: "Out of memory"
```bash
# Utiliser le traitement par chunks
# Voir "Optimisations possibles" ci-dessus
```

## ✅ Checklist finale

- [ ] Copier `api/video_decoders.py`
- [ ] Mettre à jour `api/upload.js`
- [ ] Mettre à jour `api/hcv_engine.py`
- [ ] Copier `upload_pro.html`
- [ ] Installer ffmpeg et OpenCV
- [ ] Installer dépendances Python
- [ ] Exécuter les tests
- [ ] Tester avec fichiers H264/H265/SDI
- [ ] Vérifier les logs
- [ ] Déployer en production

## 📚 Ressources

- `H264_SDI_SUPPORT.md` — Documentation technique
- `DEPLOYMENT_H264_SDI.md` — Guide de déploiement
- `README_H264_SDI_IMPLEMENTATION.md` — Résumé de l'implémentation
- `test_h264_sdi_support.py` — Suite de tests

## 🎉 Résultat

Après l'intégration, l'application web HCV Pro supportera:

✅ H.264 / H.265 (streaming, archivage)
✅ SDI 4:2:2 (broadcast professionnel)
✅ YUV Raw (données brutes)
✅ MXF (conteneur professionnel)
✅ MP4, MOV, AVI, TS (formats existants)

Avec des ratios de compression de **8-15×** et une interface web intuitive.
