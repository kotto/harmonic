# 🌐 URLs Render - HCV-PRO-PROJECT

## Configuration Render

### Backend
- **Nom**: hcv-pro-render-backend-3
- **URL**: https://hcv-pro-render-backend-3.onrender.com
- **Health Check**: https://hcv-pro-render-backend-3.onrender.com/health
- **API Base**: https://hcv-pro-render-backend-3.onrender.com/api

### Frontend
- **Nom**: hcv-pro-render-frontend
- **URL**: https://hcv-pro-render-frontend.onrender.com
- **Type**: Static Site

---

## 📡 Endpoints API

### Health Check
```bash
curl https://hcv-pro-render-backend-3.onrender.com/health
```

### Information
```bash
curl https://hcv-pro-render-backend-3.onrender.com/info
```

### Compression Broadcast
```bash
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

### Compression Android Boost
```bash
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/android-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

### Compression Video Boost
```bash
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/video-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

### Compression Universal Boost
```bash
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/universal-boost \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

---

## 🔐 Clés API

Clés API disponibles:
- `demo-key-2024`
- `hcv-pro-client-001`
- `test-key-frontend`

---

## 🧪 Tests Rapides

### Vérifier le Backend
```bash
curl https://hcv-pro-render-backend-3.onrender.com/health
```

### Vérifier le Frontend
```bash
curl https://hcv-pro-render-frontend.onrender.com
```

### Tester la Compression
```bash
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}' | jq
```

---

## 📝 Configuration Frontend

Mettre à jour l'URL du backend dans le code frontend:

```javascript
const API_URL = 'https://hcv-pro-render-backend-3.onrender.com';
```

---

## 🔄 Mise à Jour des URLs

Si vous devez mettre à jour les URLs:

1. Mettre à jour les fichiers de configuration
2. Mettre à jour le code frontend
3. Faire un git push
4. Render redéploiera automatiquement

---

**Dernière mise à jour**: 17 Avril 2026  
**Statut**: ✅ URLs Configurées
