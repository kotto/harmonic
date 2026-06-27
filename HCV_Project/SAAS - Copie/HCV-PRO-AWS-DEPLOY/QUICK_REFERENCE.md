# ⚡ Référence Rapide - HCV-PRO-PROJECT

## 🚀 Démarrage Rapide

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
bash start.sh
```

### Manuel
```bash
python server/hcv_pro_server.py
```

---

## 🌐 Accès à l'Application

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Interface web principale |
| http://127.0.0.1:3000 | Localhost |
| http://192.168.1.190:3000 | Réseau local |

---

## 📡 Endpoints API

### Santé du Serveur
```bash
curl http://localhost:3000/api/health
```

### Historique des Compressions
```bash
curl http://localhost:3000/api/history
```

### Compression Broadcast (Démo)
```bash
curl -X POST http://localhost:3000/api/demo
```

### Compression Android Boost
```bash
curl -X POST -F "file=@image.jpg" http://localhost:3000/api/android-boost
```

### Compression Vidéo
```bash
curl -X POST -F "file=@video.mp4" http://localhost:3000/api/video-boost
```

### Compression Fichiers Précompressés
```bash
curl -X POST -F "file=@image.png" http://localhost:3000/api/precompressed
```

---

## 📊 Méthodes de Compression

| Méthode | Ratio | PSNR | Cible |
|---------|-------|------|-------|
| Broadcast | 26-33:1 | 42-46 dB | Signal SDI |
| Android Boost | 3-11:1 | 35-42 dB | JPEG |
| Video Boost | 2.3-7.5:1 | >35 dB | H264/H265 |
| Universal Boost | 1.2-345:1 | 33-42 dB | JPEG/PNG/WebP |

---

## 🔧 Installation des Dépendances

```bash
pip install -r requirements.txt
```

---

## 📁 Structure du Projet

```
HCV-PRO-PROJECT/
├── server/hcv_pro_server.py      ← Serveur Flask
├── codecs/                        ← Moteurs de compression
├── web/templates/                 ← Interface web
├── api/                           ← Routes API
├── requirements.txt               ← Dépendances Python
├── start.bat                      ← Script Windows
├── start.sh                       ← Script Linux/Mac
└── docs/                          ← Documentation
```

---

## 🛑 Arrêter le Serveur

```bash
Ctrl+C
```

---

## 🔍 Vérification

### Vérifier Python
```bash
python --version
```

### Vérifier les Dépendances
```bash
pip list | grep Flask
pip list | grep numpy
pip list | grep opencv
pip list | grep zstandard
```

### Vérifier le Port 3000
```bash
# Windows
netstat -ano | findstr :3000

# Linux/Mac
lsof -i :3000
```

---

## 📚 Documentation

| Fichier | Description |
|---------|-------------|
| START.md | Guide de démarrage |
| VERIFICATION_REPORT.md | Rapport de vérification |
| SERVER_STATUS.md | État du serveur |
| LAUNCH_SUMMARY.md | Résumé du lancement |
| TESTS_PERFORMED.md | Tests effectués |
| README.md | Documentation générale |

---

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier Python
python --version

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall

# Vérifier le port
netstat -ano | findstr :3000
```

### Erreur "Module not found"
```bash
pip install -r requirements.txt --force-reinstall
```

### Erreur de connexion
```bash
# Vérifier que le serveur est en cours d'exécution
curl http://localhost:3000/api/health

# Essayer une autre adresse
curl http://127.0.0.1:3000/api/health
```

---

## 💡 Conseils

1. **Toujours vérifier la santé du serveur**
   ```bash
   curl http://localhost:3000/api/health
   ```

2. **Consulter l'historique des compressions**
   ```bash
   curl http://localhost:3000/api/history
   ```

3. **Utiliser les scripts de démarrage**
   - Windows: `start.bat`
   - Linux/Mac: `bash start.sh`

4. **Lire la documentation**
   - START.md pour le démarrage
   - VERIFICATION_REPORT.md pour la vérification
   - README.md pour la documentation générale

---

## 🎯 Cas d'Usage Courants

### Tester la Compression Broadcast
```bash
curl -X POST http://localhost:3000/api/demo
```

### Compresser une Image JPEG
```bash
curl -X POST -F "file=@photo.jpg" http://localhost:3000/api/android-boost
```

### Compresser une Vidéo
```bash
curl -X POST -F "file=@video.mp4" http://localhost:3000/api/video-boost
```

### Voir l'Historique
```bash
curl http://localhost:3000/api/history
```

---

## 📞 Support

Pour plus d'informations:
- Consultez `START.md`
- Consultez `VERIFICATION_REPORT.md`
- Consultez `README.md`
- Consultez `docs/DOCUMENT_FINAL_HCV_PRO.md`

---

**Dernière mise à jour**: 17 Avril 2026  
**Statut**: ✅ Opérationnel
