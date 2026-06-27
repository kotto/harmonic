# ⚡ Mise à Jour Rapide - Services Render Existants

## 🎯 En 10 Minutes

### Services à Mettre à Jour
- **Backend**: `hcv-pro-render-backend-3`
- **Frontend**: `hcv-pro-render-frontend`

---

## 🔄 Mise à Jour du Backend

### Étape 1: Aller au Dashboard (1 min)
1. Ouvrir [render.com/dashboard](https://render.com/dashboard)
2. Sélectionner `hcv-pro-render-backend-3`
3. Aller à Settings → Build & Deploy

### Étape 2: Mettre à Jour le Start Command (2 min)
**Changer**:
```
De: python app.py
À: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```
**Cliquer**: Save

### Étape 3: Mettre à Jour les Variables d'Env (2 min)
**Aller à**: Settings → Environment

**Ajouter/Mettre à jour**:
```
HCV_PRO_SECRET=your-secret-key-here
HCV_PRO_API_KEY_REQUIRED=true
HCV_PRO_RATE_LIMIT=100
FLASK_ENV=production
FLASK_DEBUG=false
```
**Cliquer**: Save

### Étape 4: Redéployer (3 min)
1. Aller à Deployments
2. Cliquer "Trigger Deploy"
3. Attendre que le déploiement se termine

### Étape 5: Vérifier (2 min)
```bash
curl https://hcv-pro-render-backend-3.onrender.com/health
```

---

## 🌐 Mise à Jour du Frontend

### Étape 1: Aller au Dashboard (1 min)
1. Ouvrir [render.com/dashboard](https://render.com/dashboard)
2. Sélectionner `hcv-pro-render-frontend`
3. Aller à Settings

### Étape 2: Vérifier la Configuration (2 min)
**Vérifier**:
- Build Command: `echo 'Static build - no build required'`
- Publish Directory: `.`
- Headers: Présents

### Étape 3: Redéployer (3 min)
1. Aller à Deployments
2. Cliquer "Trigger Deploy"
3. Attendre que le déploiement se termine

### Étape 4: Vérifier (2 min)
```bash
curl https://hcv-pro-render-frontend.onrender.com
```

---

## 🧪 Tests Rapides

```bash
# Backend Health
curl https://hcv-pro-render-backend-3.onrender.com/health

# Frontend
curl https://hcv-pro-render-frontend.onrender.com

# Compression
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

---

## ✅ Checklist Rapide

- [ ] Backend Start Command mis à jour
- [ ] Backend Variables d'env mises à jour
- [ ] Backend redéployé
- [ ] Backend health check OK
- [ ] Frontend redéployé
- [ ] Frontend se charge
- [ ] Tests réussis

---

## 📞 Besoin d'Aide?

Consulter: [RENDER_UPDATE_EXISTING_SERVICES.md](RENDER_UPDATE_EXISTING_SERVICES.md)

---

**Temps total**: ~10 minutes  
**Prêt pour**: Production
