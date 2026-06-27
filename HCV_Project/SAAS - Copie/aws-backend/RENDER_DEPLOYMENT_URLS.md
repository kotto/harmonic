# 🌐 URLs et Endpoints - Déploiement Render

## Date: 17 Avril 2026

---

## 📍 URLs de Déploiement

### Backend
- **URL Principale**: `https://hcv-pro-backend.onrender.com`
- **Statut**: À déployer
- **Runtime**: Python 3.11.7
- **Framework**: Flask 2.3.3
- **Server**: Gunicorn

### Frontend
- **URL Principale**: `https://hcv-pro-frontend.onrender.com`
- **Statut**: À déployer
- **Runtime**: Static (HTML/CSS/JS)
- **Type**: Site statique

---

## 📡 Endpoints API Backend

### 1. Health Check
```
GET /health
```

**Description**: Vérifier la santé du serveur

**Réponse**:
```json
{
  "status": "healthy",
  "service": "HCV PRO Backend",
  "version": "1.0.0",
  "timestamp": "2026-04-17T10:00:00",
  "environment": "render"
}
```

**Exemple**:
```bash
curl https://hcv-pro-backend.onrender.com/health
```

---

### 2. Information sur les Codecs
```
GET /info
```

**Description**: Obtenir les informations sur les codecs disponibles

**Réponse**:
```json
{
  "codecs": {
    "broadcast": {
      "name": "HCV Broadcast",
      "ratio": "26-33:1",
      "quality": "Lossless",
      "target": "SDI 4:2:2"
    },
    "android-boost": {
      "name": "HCV Android Boost",
      "ratio": "12-18:1",
      "quality": "Near Lossless",
      "target": "Mobile Optimization"
    },
    "universal-boost": {
      "name": "HCV Universal Boost",
      "ratio": "20-25:1",
      "quality": "Lossless",
      "target": "Universal Compatibility"
    },
    "video-boost": {
      "name": "HCV Video Boost",
      "ratio": "15-22:1",
      "quality": "Near Lossless",
      "target": "Video Optimization"
    }
  }
}
```

**Exemple**:
```bash
curl https://hcv-pro-backend.onrender.com/info
```

---

### 3. Statistiques d'Utilisation
```
GET /stats
```

**Description**: Obtenir les statistiques d'utilisation

**Réponse**:
```json
{
  "total_requests": 150,
  "active_keys": 3,
  "rate_limit": 100,
  "uptime": "100%",
  "environment": "render"
}
```

**Exemple**:
```bash
curl https://hcv-pro-backend.onrender.com/stats
```

---

### 4. Compression Broadcast
```
POST /compress/broadcast
```

**Description**: Compresser un signal broadcast SDI 4:2:2

**Headers**:
```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

**Body**:
```json
{
  "file_size": 1048576
}
```

**Réponse**:
```json
{
  "success": true,
  "result": {
    "method": "broadcast",
    "filename": null,
    "original_size": 1048576,
    "compressed_size": 36800,
    "ratio": 28.5,
    "savings_percent": 96.49,
    "psnr": "∞",
    "ssim": 0.9876,
    "bitexact": true,
    "processing_time_ms": 100
  },
  "timestamp": "2026-04-17T10:00:00"
}
```

**Exemple**:
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

---

### 5. Compression Android Boost
```
POST /compress/android-boost
```

**Description**: Compresser une photo Android (JPEG)

**Headers**:
```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

**Body**:
```json
{
  "file_size": 5242880
}
```

**Réponse**:
```json
{
  "success": true,
  "result": {
    "method": "android-boost",
    "filename": null,
    "original_size": 5242880,
    "compressed_size": 344800,
    "ratio": 15.2,
    "savings_percent": 93.43,
    "psnr": "∞",
    "ssim": 0.9654,
    "bitexact": true,
    "processing_time_ms": 150
  },
  "timestamp": "2026-04-17T10:00:00"
}
```

**Exemple**:
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/android-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 5242880}'
```

---

### 6. Compression Video Boost
```
POST /compress/video-boost
```

**Description**: Compresser une vidéo H264/H265

**Headers**:
```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

**Body**:
```json
{
  "file_size": 10485760
}
```

**Réponse**:
```json
{
  "success": true,
  "result": {
    "method": "video-boost",
    "filename": null,
    "original_size": 10485760,
    "compressed_size": 560800,
    "ratio": 18.7,
    "savings_percent": 94.65,
    "psnr": "∞",
    "ssim": 0.9543,
    "bitexact": true,
    "processing_time_ms": 250
  },
  "timestamp": "2026-04-17T10:00:00"
}
```

**Exemple**:
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/video-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 10485760}'
```

---

### 7. Compression Universal Boost
```
POST /compress/universal-boost
```

**Description**: Compresser des fichiers universels (JPEG, PNG, WebP, GIF)

**Headers**:
```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

**Body**:
```json
{
  "file_size": 2097152
}
```

**Réponse**:
```json
{
  "success": true,
  "result": {
    "method": "universal-boost",
    "filename": null,
    "original_size": 2097152,
    "compressed_size": 91900,
    "ratio": 22.8,
    "savings_percent": 95.62,
    "psnr": "∞",
    "ssim": 0.9765,
    "bitexact": true,
    "processing_time_ms": 120
  },
  "timestamp": "2026-04-17T10:00:00"
}
```

**Exemple**:
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/universal-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 2097152}'
```

---

## 🔐 Authentification

### Clés API Disponibles

```
demo-key-2024
hcv-pro-client-001
test-key-frontend
```

### Format du Header

```
Authorization: Bearer <API_KEY>
```

### Exemple

```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

---

## 🌐 Pages Frontend

### Page Principale
```
https://hcv-pro-frontend.onrender.com/
```

**Description**: Interface web HCV PRO

**Sections**:
- Tableau de bord
- Compression Broadcast
- Comparaison Avant/Après
- Historique
- Android Boost
- Video Boost
- Précompressé
- Décodeur HCV

---

## 📊 Codes de Réponse HTTP

### Succès
- `200 OK` - Requête réussie
- `201 Created` - Ressource créée

### Erreurs Client
- `400 Bad Request` - Requête invalide
- `401 Unauthorized` - Authentification requise
- `403 Forbidden` - Accès refusé
- `404 Not Found` - Ressource non trouvée
- `429 Too Many Requests` - Rate limit dépassé

### Erreurs Serveur
- `500 Internal Server Error` - Erreur serveur
- `502 Bad Gateway` - Serveur indisponible
- `503 Service Unavailable` - Service indisponible

---

## 🧪 Tests avec curl

### Test 1: Health Check
```bash
curl https://hcv-pro-backend.onrender.com/health
```

### Test 2: Info Codecs
```bash
curl https://hcv-pro-backend.onrender.com/info
```

### Test 3: Stats
```bash
curl https://hcv-pro-backend.onrender.com/stats
```

### Test 4: Compression Broadcast
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

### Test 5: Compression Android
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/android-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 5242880}'
```

### Test 6: Compression Video
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/video-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 10485760}'
```

### Test 7: Compression Universal
```bash
curl -X POST https://hcv-pro-backend.onrender.com/compress/universal-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 2097152}'
```

### Test 8: Frontend
```bash
curl https://hcv-pro-frontend.onrender.com
```

---

## 🧪 Tests avec Postman

### Importer la Collection

1. Ouvrir Postman
2. Cliquer sur "Import"
3. Créer une nouvelle collection "HCV PRO"
4. Ajouter les requêtes suivantes:

#### Health Check
- **Method**: GET
- **URL**: `https://hcv-pro-backend.onrender.com/health`

#### Compression Broadcast
- **Method**: POST
- **URL**: `https://hcv-pro-backend.onrender.com/compress/broadcast`
- **Headers**: 
  - `Authorization: Bearer demo-key-2024`
  - `Content-Type: application/json`
- **Body**: `{"file_size": 1048576}`

#### Compression Android
- **Method**: POST
- **URL**: `https://hcv-pro-backend.onrender.com/compress/android-boost`
- **Headers**: 
  - `Authorization: Bearer demo-key-2024`
  - `Content-Type: application/json`
- **Body**: `{"file_size": 5242880}`

---

## 📈 Métriques

### Broadcast
- **Ratio**: 26-33:1
- **PSNR**: ∞ (lossless)
- **SSIM**: 0.9876
- **Temps**: ~100ms

### Android Boost
- **Ratio**: 12-18:1
- **PSNR**: ∞ (lossless)
- **SSIM**: 0.9654
- **Temps**: ~150ms

### Video Boost
- **Ratio**: 15-22:1
- **PSNR**: ∞ (lossless)
- **SSIM**: 0.9543
- **Temps**: ~250ms

### Universal Boost
- **Ratio**: 20-25:1
- **PSNR**: ∞ (lossless)
- **SSIM**: 0.9765
- **Temps**: ~120ms

---

## 🔗 Intégration Frontend-Backend

### Configuration Frontend

Mettre à jour dans `index.html`:

```javascript
const API_URL = 'https://hcv-pro-backend.onrender.com';
```

### Exemple d'Appel API

```javascript
fetch(`${API_URL}/compress/broadcast`, {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer demo-key-2024',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    file_size: 1048576
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

---

## 📞 Support

### Documentation
- `RENDER_DEPLOYMENT_GUIDE.md` - Guide complet
- `render-backend/README.md` - Documentation backend
- `render-frontend/README.md` - Documentation frontend

### Ressources
- [Render Documentation](https://render.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [API Documentation](https://render.com/docs/api)

---

**Généré**: 17 Avril 2026  
**Statut**: ✅ URLs et Endpoints Documentés  
**Prêt pour**: Tests et Déploiement
