# HCV PRO Backend - Render Deployment

## 📋 Description

Backend Flask pour HCV PRO - Plateforme de compression multimédia avec support des codecs broadcast, Android Boost, Video Boost et Universal Boost.

## 🚀 Déploiement sur Render

### Configuration Render
- **Runtime**: Python 3.11.7
- **Framework**: Flask 2.3.3
- **Server**: Gunicorn 21.2.0
- **Plan**: Free (gratuit)

### Variables d'Environnement Requises

```env
HCV_PRO_SECRET=your-secret-key-here
HCV_PRO_API_KEY_REQUIRED=true
HCV_PRO_RATE_LIMIT=100
FLASK_ENV=production
FLASK_DEBUG=false
```

### Démarrage Local

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer le serveur
python app.py
```

Le serveur sera accessible sur `http://localhost:5000`

### Démarrage Production (Render)

```bash
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

## 📡 Endpoints API

### Health Check
```bash
GET /health
```

### Information sur les Codecs
```bash
GET /info
```

### Statistiques d'Utilisation
```bash
GET /stats
```

### Compression Broadcast
```bash
POST /compress/broadcast
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "file_size": 1048576
}
```

### Compression Android Boost
```bash
POST /compress/android-boost
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "file_size": 1048576
}
```

### Compression Video Boost
```bash
POST /compress/video-boost
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "file_size": 1048576
}
```

### Compression Universal Boost
```bash
POST /compress/universal-boost
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "file_size": 1048576
}
```

## 🔐 Authentification

Les endpoints de compression nécessitent une clé API valide dans le header `Authorization`:

```bash
Authorization: Bearer demo-key-2024
```

Clés API disponibles:
- `demo-key-2024`
- `hcv-pro-client-001`
- `test-key-frontend`

## 📊 Dépendances

- Flask 2.3.3 - Framework web
- Flask-CORS 4.0.0 - Support CORS
- NumPy 1.24.3 - Calculs numériques
- OpenCV 4.8.0.74 - Traitement d'images
- zstandard 0.21.0+ - Compression
- Gunicorn 21.2.0 - Serveur WSGI
- python-dotenv 1.0.0 - Variables d'environnement

## 🧪 Tests

### Vérifier la Santé
```bash
curl https://hcv-pro-backend.onrender.com/health
```

### Tester la Compression
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

## 📝 Fichiers Importants

- `app.py` - Application Flask principale
- `requirements.txt` - Dépendances Python
- `runtime.txt` - Version Python (3.11.4)
- `Procfile` - Configuration de processus Render
- `.env.example` - Variables d'environnement exemple
- `render.yaml` - Configuration Render

## 🔧 Configuration

### Gunicorn
- Workers: 4
- Bind: 0.0.0.0:$PORT
- Timeout: 120s (par défaut)

### Flask
- Debug: false (production)
- CORS: Activé pour tous les domaines

### Rate Limiting
- Limite: 100 requêtes par heure par clé API
- Stockage: En mémoire (réinitialisation au redémarrage)

## 📚 Documentation

Pour plus d'informations, consultez:
- [Render Documentation](https://render.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://gunicorn.org/)

## 🎯 Prochaines Étapes

1. Configurer les variables d'environnement sur Render
2. Déployer le backend
3. Tester les endpoints
4. Configurer le frontend pour pointer vers le backend

## 📞 Support

Pour les problèmes de déploiement, consultez:
- Les logs Render
- La documentation Render
- Les fichiers de configuration

---

**Dernière mise à jour**: 17 Avril 2026  
**Statut**: ✅ Prêt pour le déploiement
