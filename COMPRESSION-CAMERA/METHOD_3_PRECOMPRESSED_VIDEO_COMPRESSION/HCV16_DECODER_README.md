# Décodeur HCV16

## Description

Le décodeur HCV16 permet de lire et décompresser les fichiers vidéo au format HCV16 créés par le compresseur de vidéo précompressée.

## Fonctionnalités

- **Lecture de fichiers HCV16** : Extraction des métadonnées et structure du fichier
- **Décompression de frames** : Reconstruction des frames individuelles
- **Affichage de la première frame** : Prévisualisation rapide de la vidéo
- **Conversion en MP4** : Décompression complète en fichier vidéo MP4

## Structure du fichier HCV16

```
En-tête (32 bytes):
- Magic number: "HCV6" (4 bytes)
- Version (1 byte)
- Mode (1 byte): 0x01=LOSSLESS, 0x02=GRAIN_SYNTH, 0x03=SIGNAL_ONLY
- Colorspace (1 byte)
- Bit depth (1 byte)
- Width (4 bytes)
- Height (4 bytes)
- Frame count (4 bytes)
- FPS (4 bytes, en millisecondes)
- Sequence ID (4 bytes)
- Number of streams (2 bytes)
- Sigma curve (32 bytes)

Index des frames:
- Offset de chaque frame (8 bytes par frame)

Données des frames:
- Frame data (taille variable)

CRC32 (4 bytes)
```

## Utilisation

### En ligne de commande

```bash
# Afficher les informations d'un fichier HCV16
python hcv16_decoder.py video.hcv16

# Cela va afficher:
# - Les métadonnées de la vidéo
# - Extraire et sauvegarder la première frame en PNG
```

### Dans une application Python

```python
from hcv16_decoder import HCV16Decoder

# Créer un décodeur
decoder = HCV16Decoder()

# Lire un fichier HCV16
info = decoder.get_video_info('video.hcv16')
print(f"Résolution: {info['info']['width']}x{info['info']['height']}")
print(f"Frames: {info['info']['frame_count']}")
print(f"FPS: {info['info']['fps']}")

# Extraire la première frame
frame = decoder.get_first_frame_image('video.hcv16')
if frame['success']:
    # frame['image_data'] contient l'image en base64
    # Utilisable directement dans une balise <img src="...">
    pass

# Décompresser en MP4
result = decoder.decompress_to_mp4('video.hcv16', 'output.mp4')
if result['success']:
    print(f"Vidéo créée: {result['output_path']}")
```

### Via l'API Web

L'application web expose plusieurs endpoints:

#### GET /decompress_video/<session_id>
Décompresse et retourne la première frame d'une vidéo HCV16.

**Réponse:**
```json
{
  "success": true,
  "image_data": "data:image/png;base64,...",
  "width": 1920,
  "height": 1080,
  "frame_number": 0,
  "total_frames": 150,
  "fps": 30.0,
  "bit_depth": 8
}
```

#### GET /get_hcv16_info/<session_id>
Retourne les informations détaillées d'un fichier HCV16.

**Réponse:**
```json
{
  "success": true,
  "hcv16_info": {
    "format": "HCV16",
    "version": 1,
    "mode": "GRAIN_SYNTH",
    "width": 1920,
    "height": 1080,
    "frame_count": 150,
    "fps": 30.0,
    "duration": 5.0,
    "bit_depth": 8,
    "colorspace": "BT.709",
    "file_size": 1234567
  }
}
```

#### GET /decompress_to_mp4/<session_id>
Décompresse complètement un fichier HCV16 en MP4.

**Réponse:**
```json
{
  "success": true,
  "message": "Vidéo décompressée avec succès",
  "output_file": "decompressed_<session_id>.mp4",
  "frame_count": 150,
  "fps": 30.0,
  "width": 1920,
  "height": 1080
}
```

## Algorithme de décompression

1. **Lecture de l'en-tête** : Extraction des métadonnées vidéo
2. **Lecture de l'index** : Récupération des offsets de chaque frame
3. **Pour chaque frame** :
   - Lecture des données delta harmoniques
   - Lecture des données de grain
   - Reconstruction de la frame YUV
   - Application de la courbe sigma
   - Conversion YUV → RGB

## Notes techniques

- Le décodeur utilise OpenCV pour la conversion YUV/RGB
- Les images sont encodées en PNG pour l'affichage web
- La décompression complète en MP4 nécessite OpenCV avec support VideoWriter
- La qualité de reconstruction dépend du mode de compression utilisé

## Dépendances

- Python 3.7+
- NumPy
- Pillow (PIL)
- OpenCV (cv2)

## Installation des dépendances

```bash
pip install numpy pillow opencv-python
```