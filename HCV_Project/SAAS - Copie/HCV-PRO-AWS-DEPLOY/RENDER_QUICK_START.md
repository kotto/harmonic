# ⚡ Démarrage Rapide - Déploiement Render

## 🎯 En 5 Minutes

### ✅ Statut
- Configuration Render: ✅ Corrigée
- Dépendances: ✅ Complètes
- Fichiers: ✅ Créés
- Documentation: ✅ Complète

### 🚀 Déployer Maintenant

#### Étape 1: Préparer (2 min)
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

#### Étape 2: Créer Backend (2 min)
1. Aller sur [render.com/dashboard](https://render.com/dashboard)
2. Cliquer "New +" → "Web Service"
3. Sélectionner `render-backend`
4. Configurer:
   - Name: `hcv-pro-backend`
   - Build: `pip install --upgrade pip setuptools wheel && pip install -r requirements.txt`
   - Start: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
5. Ajouter variables d'env:
   - `HCV_PRO_SECRET=your-secret-key`
   - `HCV_PRO_API_KEY_REQUIRED=true`
   - `HCV_PRO_RATE_LIMIT=100`
   - `FLASK_ENV=production`
   - `FLASK_DEBUG=false`
6. Cliquer "Create Web Service"

#### Étape 3: Créer Frontend (1 min)
1. Cliquer "New +" → "Static Site"
2. Sélectionner `render-frontend`
3. Configurer:
   - Name: `hcv-pro-frontend`
   - Build: `echo 'Static build - no build required'`
   - Publish: `.`
4. Cliquer "Create Static Site"

### 🧪 Tester (1 min)

```bash
# Backend
curl https://hcv-pro-backend.onrender.com/health

# Frontend
curl https://hcv-pro-frontend.onrender.com

# Compression
curl -X POST https://hcv-pro-backend.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

---

## 📚 Documentation Complète

| Document | Utilité | Durée |
|----------|---------|-------|
| [RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md) | Guide complet | 30 min |
| [RENDER_DEPLOYMENT_CHECKLIST.md](RENDER_DEPLOYMENT_CHECKLIST.md) | Checklist | À utiliser |
| [RENDER_DEPLOYMENT_URLS.md](RENDER_DEPLOYMENT_URLS.md) | Endpoints | 10 min |
| [RENDER_INDEX.md](RENDER_INDEX.md) | Index complet | 5 min |

---

## 🎉 C'est Tout!

**Temps total**: ~10 minutes  
**Prêt pour**: Production

---

**Besoin d'aide?** Consulter [RENDER_INDEX.md](RENDER_INDEX.md)
