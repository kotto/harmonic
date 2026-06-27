# 🚀 Démarrage Rapide - HCV-PRO-PROJECT

## Installation (Première fois)

```bash
# 1. Installer les dépendances Python
pip install -r requirements.txt

# 2. Lancer le serveur
python server/hcv_pro_server.py
```

## Accès à l'Application

Une fois le serveur lancé, ouvrez votre navigateur:

- **Interface Web**: http://localhost:3000
- **API Health Check**: http://localhost:3000/api/health

## Endpoints API Disponibles

### Compression Broadcast (Signal SDI)
```bash
POST /api/compress
Content-Type: application/json

{
  "frame_data": "base64_encoded_raw_frame",
  "width": 640,
  "height": 480,
  "bit_depth": 12
}
```

### Démo Broadcast (Synthétique)
```bash
POST /api/demo
```

### Compression Android Boost (JPEG)
```bash
POST /api/android-boost
Content-Type: multipart/form-data

file: <image.jpg>
```

### Compression Vidéo (H264)
```bash
POST /api/video-boost
Content-Type: multipart/form-data

file: <video.mp4>
```

### Compression Fichiers Précompressés
```bash
POST /api/precompressed
Content-Type: multipart/form-data

file: <image.png|.jpg|.webp|.gif>
```

### Historique des Compressions
```bash
GET /api/history
```

### Santé du Serveur
```bash
GET /api/health
```

## Arrêt du Serveur

Appuyez sur `Ctrl+C` dans le terminal où le serveur est en cours d'exécution.

## Dépannage

### Le serveur ne démarre pas
- Vérifiez que Python 3.8+ est installé: `python --version`
- Vérifiez que les dépendances sont installées: `pip list | grep Flask`
- Vérifiez que le port 3000 n'est pas utilisé: `netstat -ano | findstr :3000`

### Erreur "Module not found"
- Réinstallez les dépendances: `pip install -r requirements.txt --force-reinstall`

### Erreur de connexion
- Vérifiez que le serveur est en cours d'exécution
- Essayez http://127.0.0.1:3000 au lieu de localhost

## Structure des Fichiers

```
HCV-PRO-PROJECT/
├── server/hcv_pro_server.py      ← Serveur Flask
├── codecs/                        ← Moteurs de compression
├── web/templates/                 ← Interface web
├── api/                           ← Routes API
├── requirements.txt               ← Dépendances Python
└── START.md                       ← Ce fichier
```

## Performance

- **Broadcast**: 26-33:1 ratio, 42-46 dB PSNR
- **Android Boost**: 3-11:1 ratio, 35-42 dB PSNR
- **Video Boost**: 2.3-7.5:1 ratio, >35 dB PSNR
- **Universal Boost**: 1.2-345:1 ratio, 33-42 dB PSNR

## Support

Pour plus d'informations, consultez:
- `README.md` - Documentation générale
- `VERIFICATION_REPORT.md` - Rapport de vérification
- `docs/DOCUMENT_FINAL_HCV_PRO.md` - Documentation technique complète
