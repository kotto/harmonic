# 📊 État du Serveur HCV-PRO

## 🟢 Statut Actuel: EN COURS D'EXÉCUTION

**Heure de démarrage**: 17 Avril 2026  
**Processus ID**: 2  
**Port**: 3000  
**Adresse**: http://localhost:3000

---

## 📡 Endpoints Actifs

### ✅ GET /
- **Description**: Interface web principale
- **Réponse**: HTML (Tailwind CSS + Lucide Icons)
- **Statut**: Opérationnel

### ✅ GET /api/health
- **Description**: Vérification de la santé du serveur
- **Réponse**: 
```json
{
  "codec": "HCV PRO v1.0",
  "methods": ["broadcast", "android-boost", "video-boost", "universal-boost"],
  "ok": true
}
```
- **Statut**: Opérationnel

### ✅ POST /api/compress
- **Description**: Compression broadcast (signal RAW/SDI)
- **Paramètres**: frame_data (base64), width, height, bit_depth
- **Réponse**: Fichier compressé .hcvp
- **Statut**: Opérationnel

### ✅ POST /api/demo
- **Description**: Démo broadcast avec signal synthétique
- **Paramètres**: Aucun
- **Réponse**: Fichier compressé .hcvp + statistiques
- **Statut**: Opérationnel

### ✅ POST /api/android-boost
- **Description**: Compression Android Boost (JPEG)
- **Paramètres**: file (multipart/form-data)
- **Réponse**: Fichier compressé .hcvb
- **Statut**: Opérationnel

### ✅ POST /api/video-boost
- **Description**: Compression vidéo (H264 via ffmpeg)
- **Paramètres**: file (multipart/form-data)
- **Réponse**: Fichier compressé .hcvv
- **Statut**: Opérationnel

### ✅ POST /api/precompressed
- **Description**: Compression fichiers précompressés (JPEG/PNG/WebP/GIF)
- **Paramètres**: file (multipart/form-data)
- **Réponse**: Fichier compressé .hcvz
- **Statut**: Opérationnel

### ✅ GET /api/history
- **Description**: Historique des compressions
- **Réponse**: Liste JSON des compressions effectuées
- **Statut**: Opérationnel

---

## 🔧 Configuration du Serveur

### Framework
- **Type**: Flask 2.3.3
- **Mode**: Development (non-production)
- **Debug**: Désactivé
- **Threads**: 1 (OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1)

### Dépendances Chargées
- ✅ Flask 2.3.3
- ✅ numpy 1.24.3
- ✅ opencv-python 4.8.0.74
- ✅ Werkzeug 2.3.7
- ✅ zstandard 0.25.0

### Sécurité
- ✅ Headers de sécurité implémentés
- ✅ CSP (Content-Security-Policy) configurée
- ✅ CORS: À configurer pour production
- ✅ HTTPS: À configurer pour production

---

## 📈 Performance

### Codecs Disponibles

| Codec | Ratio | PSNR | Temps Typique |
|-------|-------|------|---------------|
| Broadcast | 26-33:1 | 42-46 dB | ~100-500ms |
| Android Boost | 3-11:1 | 35-42 dB | ~50-200ms |
| Video Boost | 2.3-7.5:1 | >35 dB | ~500-2000ms |
| Universal Boost | 1.2-345:1 | 33-42 dB | ~50-300ms |

### Ressources Système
- **CPU**: Optimisé (threads limités)
- **Mémoire**: ~200-500 MB (selon les opérations)
- **Disque**: Fichiers temporaires dans `/tmp`

---

## 🌐 Accès Réseau

### Localhost
- http://127.0.0.1:3000
- http://localhost:3000

### Réseau Local
- http://192.168.1.190:3000

### Adresses Écoute
- 0.0.0.0:3000 (toutes les interfaces)

---

## 📝 Logs

### Démarrage
```
HCV PRO — Plateforme de Compression Multimédia
============================================================
Serveur: http://localhost:3000
POST /api/compress        Broadcast (RAW/SDI)
POST /api/demo            Démo broadcast
POST /api/android-boost   Android Boost (JPEG)
POST /api/video-boost     Video Boost (H264)
POST /api/precompressed   Précompressés (JPEG/PNG/WebP/GIF)
GET  /api/history         Historique
============================================================
* Serving Flask app 'hcv_pro_server'
* Debug mode: off
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:3000
* Running on http://192.168.1.190:3000
Press CTRL+C to quit
```

---

## ⚠️ Avertissements

### Développement
- ⚠️ Serveur de développement Flask (non-production)
- ⚠️ Pas de load balancing
- ⚠️ Pas de clustering
- ⚠️ Pas de cache distribué

### Production
Pour la production, utiliser:
- Gunicorn ou uWSGI comme serveur WSGI
- Nginx comme reverse proxy
- SSL/TLS pour HTTPS
- Monitoring et logging structurés
- Rate limiting et throttling

---

## 🔄 Commandes Utiles

### Arrêter le serveur
```bash
Ctrl+C
```

### Redémarrer le serveur
```bash
# Arrêter (Ctrl+C)
# Puis relancer
python server/hcv_pro_server.py
```

### Vérifier la santé
```bash
curl http://localhost:3000/api/health
```

### Voir l'historique
```bash
curl http://localhost:3000/api/history
```

---

## 📞 Support

Pour plus d'informations:
- Consultez `START.md` pour le démarrage
- Consultez `VERIFICATION_REPORT.md` pour la vérification
- Consultez `README.md` pour la documentation générale
- Consultez `docs/DOCUMENT_FINAL_HCV_PRO.md` pour la documentation technique

---

**Dernière mise à jour**: 17 Avril 2026  
**Statut**: ✅ Opérationnel
