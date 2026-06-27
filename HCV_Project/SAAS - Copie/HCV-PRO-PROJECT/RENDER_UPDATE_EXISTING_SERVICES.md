# 🔄 Mise à Jour des Services Render Existants

## Date: 17 Avril 2026

---

## 📋 Services Existants à Mettre à Jour

### Frontend
- **Nom**: `hcv-pro-render-frontend`
- **Type**: Static Site
- **URL**: À déterminer

### Backend
- **Nom**: `hcv-pro-render-backend-3`
- **Type**: Web Service
- **URL**: À déterminer

---

## 🔧 Mise à Jour du Backend (hcv-pro-render-backend-3)

### Étape 1: Vérifier la Configuration Actuelle

1. Aller sur [render.com/dashboard](https://render.com/dashboard)
2. Sélectionner `hcv-pro-render-backend-3`
3. Aller à Settings
4. Vérifier:
   - Build Command
   - Start Command
   - Environment Variables

### Étape 2: Mettre à Jour le Start Command

**Aller à**: Settings → Build & Deploy

**Changer**:
```
De: python app.py
À: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

**Cliquer**: Save

### Étape 3: Mettre à Jour les Variables d'Environnement

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

### Étape 4: Vérifier les Dépendances

**Aller à**: Settings → Build & Deploy

**Vérifier Build Command**:
```
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

### Étape 5: Redéployer

**Option 1: Redémarrage Simple**
1. Aller à Settings
2. Cliquer "Restart"
3. Attendre que le service redémarre

**Option 2: Redéploiement Complet**
1. Aller à Deployments
2. Cliquer "Trigger Deploy"
3. Attendre que le déploiement se termine

### Étape 6: Vérifier le Déploiement

```bash
# Vérifier la santé
curl https://hcv-pro-render-backend-3.onrender.com/health

# Réponse attendue:
# {
#   "status": "healthy",
#   "service": "HCV PRO Backend",
#   "version": "1.0.0",
#   "timestamp": "...",
#   "environment": "render"
# }
```

---

## 🌐 Mise à Jour du Frontend (hcv-pro-render-frontend)

### Étape 1: Vérifier la Configuration Actuelle

1. Aller sur [render.com/dashboard](https://render.com/dashboard)
2. Sélectionner `hcv-pro-render-frontend`
3. Aller à Settings
4. Vérifier:
   - Build Command
   - Publish Directory
   - Headers

### Étape 2: Vérifier le Build Command

**Aller à**: Settings → Build & Deploy

**Vérifier**:
```
echo 'Static build - no build required'
```

**Vérifier Publish Directory**:
```
.
```

### Étape 3: Vérifier les Headers

**Aller à**: Settings → Headers

**Vérifier que les headers de sécurité sont présents**:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: geolocation=(), microphone=(), camera=()

### Étape 4: Redéployer

**Option 1: Redémarrage Simple**
1. Aller à Settings
2. Cliquer "Restart"
3. Attendre que le service redémarre

**Option 2: Redéploiement Complet**
1. Aller à Deployments
2. Cliquer "Trigger Deploy"
3. Attendre que le déploiement se termine

### Étape 5: Vérifier le Déploiement

```bash
# Vérifier que le site se charge
curl https://hcv-pro-render-frontend.onrender.com

# Vérifier les headers
curl -I https://hcv-pro-render-frontend.onrender.com
```

---

## 📝 Mise à Jour du Code

### Étape 1: Pousser les Changements vers GitHub

```bash
# Backend
cd render-backend
git add .
git commit -m "Update Render deployment configuration"
git push origin main

# Frontend
cd render-frontend
git add .
git commit -m "Update Render deployment configuration"
git push origin main
```

### Étape 2: Déclencher le Redéploiement

**Option 1: Auto-Deploy (Recommandé)**
- Si auto-deploy est activé, Render va automatiquement redéployer
- Attendre 2-5 minutes

**Option 2: Redéploiement Manuel**
1. Aller à Render Dashboard
2. Sélectionner le service
3. Aller à Deployments
4. Cliquer "Trigger Deploy"

### Étape 3: Vérifier les Logs

**Backend**:
1. Aller à `hcv-pro-render-backend-3`
2. Aller à Logs
3. Vérifier qu'il n'y a pas d'erreurs

**Frontend**:
1. Aller à `hcv-pro-render-frontend`
2. Aller à Logs
3. Vérifier qu'il n'y a pas d'erreurs

---

## 🧪 Tests Post-Mise à Jour

### Test 1: Health Check Backend

```bash
curl https://hcv-pro-render-backend-3.onrender.com/health
```

**Réponse attendue**: 200 OK avec JSON

### Test 2: Info Codecs

```bash
curl https://hcv-pro-render-backend-3.onrender.com/info
```

**Réponse attendue**: 200 OK avec liste des codecs

### Test 3: Compression Broadcast

```bash
curl -X POST https://hcv-pro-render-backend-3.onrender.com/compress/broadcast \
  -H "Authorization: Bearer demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"file_size": 1048576}'
```

**Réponse attendue**: 200 OK avec résultats

### Test 4: Frontend Charge

```bash
curl https://hcv-pro-render-frontend.onrender.com
```

**Réponse attendue**: HTML valide

### Test 5: Intégration Frontend-Backend

1. Ouvrir https://hcv-pro-render-frontend.onrender.com
2. Cliquer sur "Demo Broadcast VGA"
3. Vérifier que la compression fonctionne
4. Vérifier que les résultats s'affichent

---

## 📊 Checklist de Mise à Jour

### Backend (hcv-pro-render-backend-3)
- [ ] Vérifier la configuration actuelle
- [ ] Mettre à jour le Start Command
- [ ] Mettre à jour les variables d'environnement
- [ ] Vérifier les dépendances
- [ ] Redéployer
- [ ] Vérifier le health check
- [ ] Vérifier les logs
- [ ] Tester les endpoints

### Frontend (hcv-pro-render-frontend)
- [ ] Vérifier la configuration actuelle
- [ ] Vérifier le Build Command
- [ ] Vérifier les headers
- [ ] Redéployer
- [ ] Vérifier que le site se charge
- [ ] Vérifier les logs
- [ ] Tester l'intégration

### Code
- [ ] Pousser les changements vers GitHub
- [ ] Vérifier que les fichiers sont à jour
- [ ] Vérifier que les dépendances sont à jour

---

## 🔍 Dépannage

### Le backend ne démarre pas

**Symptôme**: Statut "Failed"

**Solutions**:
1. Vérifier les logs Render
2. Vérifier que le Start Command est correct
3. Vérifier que les dépendances sont installées
4. Vérifier que `app.py` n'a pas d'erreurs

```bash
# Tester localement
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Le frontend ne se charge pas

**Symptôme**: Erreur 404 ou page blanche

**Solutions**:
1. Vérifier les logs Render
2. Vérifier que `index.html` existe
3. Vérifier que le Build Command est correct
4. Vérifier que le Publish Directory est correct

### API ne répond pas

**Symptôme**: Erreur 502 Bad Gateway

**Solutions**:
1. Vérifier que le backend est "Live"
2. Vérifier que le health check passe
3. Vérifier les logs du backend
4. Vérifier que Gunicorn démarre correctement

### CORS Error

**Symptôme**: Erreur CORS dans la console du navigateur

**Solutions**:
1. Vérifier que CORS est activé dans `app.py`
2. Vérifier que l'URL du backend est correcte
3. Vérifier que les headers sont corrects

---

## 📈 Vérification des Performances

### Métriques Backend
1. Aller à `hcv-pro-render-backend-3` → Metrics
2. Vérifier:
   - CPU Usage: < 50%
   - Memory Usage: < 500MB
   - Requests/sec: Normal
   - Response Time: < 1s

### Métriques Frontend
1. Aller à `hcv-pro-render-frontend` → Metrics
2. Vérifier:
   - CPU Usage: < 10%
   - Memory Usage: < 100MB
   - Requests/sec: Normal
   - Response Time: < 100ms

---

## 🎯 Résumé des Changements

### Backend
- ✅ Start Command: Changé en Gunicorn
- ✅ Variables d'env: Mises à jour
- ✅ Dépendances: Vérifiées
- ✅ Configuration: Optimisée

### Frontend
- ✅ Build Command: Vérifié
- ✅ Headers: Vérifiés
- ✅ Configuration: Optimisée

---

## 📞 Support

### Documentation
- [RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md) - Guide complet
- [RENDER_DEPLOYMENT_URLS.md](RENDER_DEPLOYMENT_URLS.md) - URLs et endpoints
- [render-backend/README.md](render-backend/README.md) - Documentation backend
- [render-frontend/README.md](render-frontend/README.md) - Documentation frontend

### Ressources
- [Render Documentation](https://render.com/docs)
- [Render Dashboard](https://render.com/dashboard)

---

## 🚀 Prochaines Étapes

1. ✅ Mettre à jour le backend
2. ✅ Mettre à jour le frontend
3. ✅ Tester les endpoints
4. ✅ Vérifier les performances
5. ✅ Monitorer les logs

---

**Généré**: 17 Avril 2026  
**Statut**: ✅ Guide de Mise à Jour  
**Prêt pour**: Mise à Jour Immédiate
